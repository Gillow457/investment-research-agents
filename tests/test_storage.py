from datetime import date
from datetime import UTC, datetime, timedelta
import sqlite3

from research_agents import run_research
from research_agents.reports.render import render_markdown
from research_agents.storage import ReportStore


def test_report_store_persists_completed_report(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    queued = store.create_queued("AAPL", "2026-05-17", "mock")
    running = store.mark_running(queued.id)
    report = run_research("AAPL", date(2026, 5, 17))
    markdown = render_markdown(report)

    completed = store.mark_completed(running.id, report, markdown)
    loaded = store.get(completed.id)

    assert loaded is not None
    assert loaded.status == "completed"
    assert loaded.attempts == 1
    assert loaded.report() == report
    assert "Investment Research Report: AAPL" in loaded.markdown


def test_report_store_state_transitions(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    queued = store.create_queued("AAPL", "2026-05-17", "mock")

    running = store.mark_running(queued.id)
    failed = store.mark_failed(running.id, "temporary failure")
    retried = store.retry(failed.id)
    running_again = store.mark_running(retried.id)

    assert queued.status == "queued"
    assert running.status == "running"
    assert failed.status == "failed"
    assert retried.status == "queued"
    assert running_again.status == "running"
    assert running_again.attempts == 2


def test_report_store_recovers_stale_running(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    queued = store.create_queued("AAPL", "2026-05-17", "mock")
    running = store.mark_running(queued.id)
    stale_started_at = (datetime.now(tz=UTC) - timedelta(minutes=60)).isoformat()

    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            "UPDATE reports SET started_at = ? WHERE id = ?",
            (stale_started_at, running.id),
        )

    recovered = store.recover_stale_running(timeout_minutes=30)
    loaded = store.get(running.id)

    assert recovered == 1
    assert loaded is not None
    assert loaded.status == "failed"
    assert loaded.last_error == "Task timed out or server stopped during execution."


def test_report_store_migrates_old_table(tmp_path) -> None:
    database_path = tmp_path / "reports.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                data_source TEXT NOT NULL,
                status TEXT NOT NULL,
                decision TEXT,
                confidence REAL,
                report_json TEXT,
                markdown TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    store = ReportStore(database_path)
    queued = store.create_queued("AAPL", "2026-05-17", "mock")

    assert queued.status == "queued"
    assert queued.attempts == 0
    assert queued.max_attempts == 3


def test_report_store_batch_item_state_and_counts(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    batch = store.create_batch(["AAPL", "NVDA"], None, "mock", concurrency=2)
    items = store.list_batch_items(batch.id)

    running_batch = store.mark_batch_running(batch.id)
    running_item = store.mark_batch_item_running(items[0].id, "2026-05-17")
    report = run_research("AAPL", date(2026, 5, 17))
    report_record = store.create_queued("AAPL", "2026-05-17", "mock", batch_id=batch.id)
    completed_report = store.mark_completed(report_record.id, report, render_markdown(report))
    completed_item = store.mark_batch_item_completed(running_item.id, completed_report)
    failed_item = store.mark_batch_item_failed(items[1].id, "bad ticker")
    final_batch = store.finalize_batch(batch.id)

    assert running_batch.status == "running"
    assert completed_item.status == "completed"
    assert completed_item.report_id == completed_report.id
    assert completed_item.decision == report.decision
    assert failed_item.status == "failed"
    assert final_batch.status == "completed_with_errors"
    assert final_batch.completed == 1
    assert final_batch.failed == 1


def test_report_store_retries_failed_batch_items(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    batch = store.create_batch(["AAPL", "BAD"], None, "mock", concurrency=1)
    items = store.list_batch_items(batch.id)

    store.mark_batch_running(batch.id)
    store.mark_batch_item_completed(
        items[0].id,
        store.mark_completed(
            store.create_queued("AAPL", "2026-05-17", "mock", batch_id=batch.id).id,
            run_research("AAPL", date(2026, 5, 17)),
            "ok",
        ),
    )
    store.mark_batch_item_failed(items[1].id, "bad ticker")
    store.finalize_batch(batch.id)

    retried = store.retry_failed_batch_items(batch.id)
    retried_items = store.list_batch_items(batch.id)

    assert retried.status == "queued"
    assert retried.queued == 1
    assert retried.completed == 1
    assert [item.status for item in retried_items] == ["completed", "queued"]
    assert retried_items[1].report_id is None
