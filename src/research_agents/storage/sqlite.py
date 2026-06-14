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
    batch_id: int | None = None
    portfolio_context_json: str | None = None

    def report(self) -> ResearchReport | None:
        if self.report_json is None:
            return None
        return ResearchReport.model_validate_json(self.report_json)


@dataclass(frozen=True)
class BatchRecord:
    id: int
    status: str
    total: int
    queued: int
    running: int
    completed: int
    failed: int
    data_source: str
    requested_analysis_date: str | None
    concurrency: int
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None
    portfolio_context_json: str | None = None


@dataclass(frozen=True)
class BatchItemRecord:
    id: int
    batch_id: int
    ticker: str
    status: str
    analysis_date: str | None
    report_id: int | None
    decision: str | None
    confidence: float | None
    error: str | None
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None


class ReportStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
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
                    finished_at TEXT,
                    batch_id INTEGER,
                    portfolio_context_json TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS report_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    queued INTEGER NOT NULL,
                    running INTEGER NOT NULL,
                    completed INTEGER NOT NULL,
                    failed INTEGER NOT NULL,
                    data_source TEXT NOT NULL,
                    requested_analysis_date TEXT,
                    concurrency INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    portfolio_context_json TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS report_batch_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    status TEXT NOT NULL,
                    analysis_date TEXT,
                    report_id INTEGER,
                    decision TEXT,
                    confidence REAL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    FOREIGN KEY(batch_id) REFERENCES report_batches(id),
                    FOREIGN KEY(report_id) REFERENCES reports(id)
                )
                """
            )
            self._migrate(connection)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reports_ticker_date ON reports(ticker, analysis_date)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_reports_batch_id ON reports(batch_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_batch_items_batch_id ON report_batch_items(batch_id)"
            )

    def create_queued(
        self,
        ticker: str,
        analysis_date: str,
        data_source: str,
        max_attempts: int = 3,
        batch_id: int | None = None,
        portfolio_context_json: str | None = None,
    ) -> ReportRecord:
        now = _now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reports (
                    ticker, analysis_date, data_source, status, attempts, max_attempts,
                    created_at, updated_at, batch_id, portfolio_context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ticker, analysis_date, data_source, "queued", 0, max_attempts, now, now, batch_id, portfolio_context_json),
            )
            report_id = int(cursor.lastrowid)
        record = self.get(report_id)
        if record is None:
            raise RuntimeError("Created report row could not be loaded.")
        return record

    def create_pending(self, ticker: str, analysis_date: str, data_source: str) -> ReportRecord:
        return self.create_queued(ticker, analysis_date, data_source)

    def create_batch(
        self,
        tickers: list[str],
        requested_analysis_date: str | None,
        data_source: str,
        concurrency: int,
        portfolio_context_json: str | None = None,
    ) -> BatchRecord:
        now = _now()
        normalized = [ticker.upper() for ticker in tickers]
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO report_batches (
                    status, total, queued, running, completed, failed, data_source,
                    requested_analysis_date, concurrency, created_at, updated_at, portfolio_context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "queued",
                    len(normalized),
                    len(normalized),
                    0,
                    0,
                    0,
                    data_source,
                    requested_analysis_date,
                    concurrency,
                    now,
                    now,
                    portfolio_context_json,
                ),
            )
            batch_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO report_batch_items (
                    batch_id, ticker, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [(batch_id, ticker, "queued", now, now) for ticker in normalized],
            )
        batch = self.get_batch(batch_id)
        if batch is None:
            raise RuntimeError("Created batch row could not be loaded.")
        return batch

    def mark_batch_running(self, batch_id: int) -> BatchRecord:
        now = _now()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM report_batches WHERE id = ?", (batch_id,)).fetchone()
            if row is None:
                raise ValueError(f"Batch {batch_id} not found.")
            if row["status"] == "running":
                self._refresh_batch_counts(batch_id)
                batch = self.get_batch(batch_id)
                if batch is None:
                    raise RuntimeError("Running batch row could not be loaded.")
                return batch
            if row["status"] not in {"queued", "completed_with_errors", "failed"}:
                raise ValueError(f"Batch {batch_id} cannot be started from status {row['status']}.")
            connection.execute(
                """
                UPDATE report_batches
                SET status = ?, started_at = COALESCE(started_at, ?), finished_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                ("running", now, now, batch_id),
            )
        self._refresh_batch_counts(batch_id)
        batch = self.get_batch(batch_id)
        if batch is None:
            raise RuntimeError("Running batch row could not be loaded.")
        return batch

    def mark_batch_item_running(self, item_id: int, analysis_date: str) -> BatchItemRecord:
        now = _now()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM report_batch_items WHERE id = ?", (item_id,)).fetchone()
            if row is None:
                raise ValueError(f"Batch item {item_id} not found.")
            if row["status"] != "queued":
                raise ValueError(f"Batch item {item_id} is not queued.")
            connection.execute(
                """
                UPDATE report_batch_items
                SET status = ?, analysis_date = ?, error = NULL, started_at = ?, finished_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                ("running", analysis_date, now, now, item_id),
            )
        item = self.get_batch_item(item_id)
        if item is None:
            raise RuntimeError("Running batch item row could not be loaded.")
        self._refresh_batch_counts(item.batch_id)
        return item

    def mark_batch_item_completed(self, item_id: int, report: ReportRecord) -> BatchItemRecord:
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE report_batch_items
                SET status = ?, report_id = ?, decision = ?, confidence = ?, error = NULL,
                    finished_at = ?, updated_at = ?
                WHERE id = ?
                """,
                ("completed", report.id, report.decision, report.confidence, now, now, item_id),
            )
        item = self.get_batch_item(item_id)
        if item is None:
            raise RuntimeError("Completed batch item row could not be loaded.")
        self._refresh_batch_counts(item.batch_id)
        return item

    def mark_batch_item_failed(self, item_id: int, error: str, report_id: int | None = None) -> BatchItemRecord:
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE report_batch_items
                SET status = ?, report_id = COALESCE(?, report_id), error = ?, finished_at = ?, updated_at = ?
                WHERE id = ?
                """,
                ("failed", report_id, error, now, now, item_id),
            )
        item = self.get_batch_item(item_id)
        if item is None:
            raise RuntimeError("Failed batch item row could not be loaded.")
        self._refresh_batch_counts(item.batch_id)
        return item

    def finalize_batch(self, batch_id: int) -> BatchRecord:
        self._refresh_batch_counts(batch_id)
        batch = self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch {batch_id} not found.")
        if batch.running or batch.queued:
            return batch
        if batch.completed == batch.total:
            status = "completed"
        elif batch.failed == batch.total:
            status = "failed"
        else:
            status = "completed_with_errors"
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE report_batches
                SET status = ?, finished_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, now, batch_id),
            )
        finalized = self.get_batch(batch_id)
        if finalized is None:
            raise RuntimeError("Finalized batch row could not be loaded.")
        return finalized

    def retry_failed_batch_items(self, batch_id: int) -> BatchRecord:
        now = _now()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM report_batches WHERE id = ?", (batch_id,)).fetchone()
            if row is None:
                raise ValueError(f"Batch {batch_id} not found.")
            if row["status"] not in {"completed_with_errors", "failed"}:
                raise ValueError(f"Batch {batch_id} cannot retry failed items from status {row['status']}.")
            cursor = connection.execute(
                """
                UPDATE report_batch_items
                SET status = ?, report_id = NULL, decision = NULL, confidence = NULL, error = NULL,
                    started_at = NULL, finished_at = NULL, updated_at = ?
                WHERE batch_id = ? AND status = ?
                """,
                ("queued", now, batch_id, "failed"),
            )
            if int(cursor.rowcount) == 0:
                raise ValueError(f"Batch {batch_id} has no failed items to retry.")
            connection.execute(
                """
                UPDATE report_batches
                SET status = ?, finished_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                ("queued", now, batch_id),
            )
        self._refresh_batch_counts(batch_id)
        batch = self.get_batch(batch_id)
        if batch is None:
            raise RuntimeError("Retried batch row could not be loaded.")
        return batch

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

    def get_batch(self, batch_id: int) -> BatchRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM report_batches WHERE id = ?", (batch_id,)).fetchone()
        return _batch_from_row(row) if row is not None else None

    def get_batch_item(self, item_id: int) -> BatchItemRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM report_batch_items WHERE id = ?", (item_id,)).fetchone()
        return _batch_item_from_row(row) if row is not None else None

    def list_batch_items(self, batch_id: int) -> list[BatchItemRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM report_batch_items WHERE batch_id = ? ORDER BY id",
                (batch_id,),
            ).fetchall()
        return [_batch_item_from_row(row) for row in rows]

    def list_queued_batch_items(self, batch_id: int) -> list[BatchItemRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM report_batch_items WHERE batch_id = ? AND status = ? ORDER BY id",
                (batch_id, "queued"),
            ).fetchall()
        return [_batch_item_from_row(row) for row in rows]

    def list_recent(self, limit: int = 20) -> list[ReportRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reports ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _refresh_batch_counts(self, batch_id: int) -> None:
        now = _now()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM report_batch_items
                WHERE batch_id = ?
                GROUP BY status
                """,
                (batch_id,),
            ).fetchall()
            counts = {str(row["status"]): int(row["count"]) for row in rows}
            connection.execute(
                """
                UPDATE report_batches
                SET queued = ?, running = ?, completed = ?, failed = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    counts.get("queued", 0),
                    counts.get("running", 0),
                    counts.get("completed", 0),
                    counts.get("failed", 0),
                    now,
                    batch_id,
                ),
            )

    @staticmethod
    def _migrate(connection: sqlite3.Connection) -> None:
        report_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(reports)").fetchall()
        }
        report_migrations = {
            "attempts": "ALTER TABLE reports ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0",
            "max_attempts": "ALTER TABLE reports ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 3",
            "last_error": "ALTER TABLE reports ADD COLUMN last_error TEXT",
            "started_at": "ALTER TABLE reports ADD COLUMN started_at TEXT",
            "finished_at": "ALTER TABLE reports ADD COLUMN finished_at TEXT",
            "batch_id": "ALTER TABLE reports ADD COLUMN batch_id INTEGER",
            "portfolio_context_json": "ALTER TABLE reports ADD COLUMN portfolio_context_json TEXT",
        }
        for column, statement in report_migrations.items():
            if column not in report_columns:
                connection.execute(statement)

        batch_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(report_batches)").fetchall()
        }
        batch_migrations = {
            "portfolio_context_json": "ALTER TABLE report_batches ADD COLUMN portfolio_context_json TEXT",
        }
        for column, statement in batch_migrations.items():
            if column not in batch_columns:
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
        batch_id=row["batch_id"],
        portfolio_context_json=row["portfolio_context_json"],
    )


def _batch_from_row(row: sqlite3.Row) -> BatchRecord:
    return BatchRecord(
        id=int(row["id"]),
        status=str(row["status"]),
        total=int(row["total"]),
        queued=int(row["queued"]),
        running=int(row["running"]),
        completed=int(row["completed"]),
        failed=int(row["failed"]),
        data_source=str(row["data_source"]),
        requested_analysis_date=row["requested_analysis_date"],
        concurrency=int(row["concurrency"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        portfolio_context_json=row["portfolio_context_json"],
    )


def _batch_item_from_row(row: sqlite3.Row) -> BatchItemRecord:
    return BatchItemRecord(
        id=int(row["id"]),
        batch_id=int(row["batch_id"]),
        ticker=str(row["ticker"]),
        status=str(row["status"]),
        analysis_date=row["analysis_date"],
        report_id=row["report_id"],
        decision=row["decision"],
        confidence=row["confidence"],
        error=row["error"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )
