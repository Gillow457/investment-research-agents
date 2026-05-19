from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from research_agents.reports.models import ResearchReport


@dataclass(frozen=True)
class ReportRecord:
    id: int
    ticker: str
    analysis_date: str
    data_source: str
    status: str
    attempts: int
    max_attempts: int
    decision: str | None
    confidence: float | None
    report_json: str | None
    markdown: str | None
    error: str | None
    last_error: str | None
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None

    def report(self) -> ResearchReport | None:
        if self.report_json is None:
            return None
        return ResearchReport.model_validate_json(self.report_json)


class ReportStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    data_source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    decision TEXT,
                    confidence REAL,
                    report_json TEXT,
                    markdown TEXT,
                    error TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT
                )
                """
            )
            self._migrate(connection)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reports_ticker_date ON reports(ticker, analysis_date)"
            )

    def create_queued(
        self,
        ticker: str,
        analysis_date: str,
        data_source: str,
        max_attempts: int = 3,
    ) -> ReportRecord:
        now = _now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reports (
                    ticker, analysis_date, data_source, status, attempts, max_attempts, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ticker, analysis_date, data_source, "queued", 0, max_attempts, now, now),
            )
            report_id = int(cursor.lastrowid)
        record = self.get(report_id)
        if record is None:
            raise RuntimeError("Created report row could not be loaded.")
        return record

    def create_pending(self, ticker: str, analysis_date: str, data_source: str) -> ReportRecord:
        return self.create_queued(ticker, analysis_date, data_source)

    def mark_running(self, report_id: int) -> ReportRecord:
        now = _now()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
            if row is None:
                raise ValueError(f"Report {report_id} not found.")
            if row["status"] != "queued":
                raise ValueError(f"Report {report_id} is not queued.")
            if int(row["attempts"]) >= int(row["max_attempts"]):
                raise ValueError(f"Report {report_id} has reached max attempts.")
            connection.execute(
                """
                UPDATE reports
                SET status = ?, attempts = attempts + 1, started_at = ?, finished_at = NULL,
                    error = NULL, last_error = NULL, updated_at = ?
                WHERE id = ?
                """,
                ("running", now, now, report_id),
            )
        record = self.get(report_id)
        if record is None:
            raise RuntimeError("Running report row could not be loaded.")
        return record

    def mark_completed(self, report_id: int, report: ResearchReport, markdown: str) -> ReportRecord:
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE reports
                SET status = ?, decision = ?, confidence = ?, report_json = ?, markdown = ?,
                    error = NULL, last_error = NULL, finished_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    report.decision,
                    report.confidence,
                    report.model_dump_json(),
                    markdown,
                    now,
                    now,
                    report_id,
                ),
            )
        record = self.get(report_id)
        if record is None:
            raise RuntimeError("Completed report row could not be loaded.")
        return record

    def mark_failed(self, report_id: int, error: str) -> ReportRecord:
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE reports
                SET status = ?, error = ?, last_error = ?, finished_at = ?, updated_at = ?
                WHERE id = ?
                """,
                ("failed", error, error, now, now, report_id),
            )
        record = self.get(report_id)
        if record is None:
            raise RuntimeError("Failed report row could not be loaded.")
        return record

    def retry(self, report_id: int) -> ReportRecord:
        now = _now()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
            if row is None:
                raise ValueError(f"Report {report_id} not found.")
            if row["status"] not in {"failed"}:
                raise ValueError(f"Report {report_id} cannot be retried from status {row['status']}.")
            if int(row["attempts"]) >= int(row["max_attempts"]):
                raise ValueError(f"Report {report_id} has reached max attempts.")
            connection.execute(
                """
                UPDATE reports
                SET status = ?, decision = NULL, confidence = NULL, report_json = NULL, markdown = NULL,
                    error = NULL, last_error = NULL, started_at = NULL, finished_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                ("queued", now, report_id),
            )
        record = self.get(report_id)
        if record is None:
            raise RuntimeError("Retried report row could not be loaded.")
        return record

    def recover_stale_running(self, timeout_minutes: int = 30) -> int:
        cutoff = datetime.now(tz=UTC) - timedelta(minutes=timeout_minutes)
        now = _now()
        message = "Task timed out or server stopped during execution."
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE reports
                SET status = ?, error = ?, last_error = ?, finished_at = ?, updated_at = ?
                WHERE status = ?
                  AND started_at IS NOT NULL
                  AND started_at < ?
                """,
                ("failed", message, message, now, now, "running", cutoff.isoformat()),
            )
            return int(cursor.rowcount)

    def get(self, report_id: int) -> ReportRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        return _record_from_row(row) if row is not None else None

    def list_recent(self, limit: int = 20) -> list[ReportRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reports ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _migrate(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(reports)").fetchall()
        }
        migrations = {
            "attempts": "ALTER TABLE reports ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0",
            "max_attempts": "ALTER TABLE reports ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 3",
            "last_error": "ALTER TABLE reports ADD COLUMN last_error TEXT",
            "started_at": "ALTER TABLE reports ADD COLUMN started_at TEXT",
            "finished_at": "ALTER TABLE reports ADD COLUMN finished_at TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(statement)


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _record_from_row(row: sqlite3.Row) -> ReportRecord:
    return ReportRecord(
        id=int(row["id"]),
        ticker=str(row["ticker"]),
        analysis_date=str(row["analysis_date"]),
        data_source=str(row["data_source"]),
        status=str(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        decision=row["decision"],
        confidence=row["confidence"],
        report_json=row["report_json"],
        markdown=row["markdown"],
        error=row["error"],
        last_error=row["last_error"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )
