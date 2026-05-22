from datetime import date

from research_agents.storage import ReportStore
from research_agents.worker_jobs import run_report_batch_item_job_from_env, run_report_batch_job_from_env, run_report_job_from_env


def test_worker_report_job_runs_from_environment(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "reports.sqlite3"
    monkeypatch.setenv("RESEARCH_AGENTS_DB", str(database_path))
    store = ReportStore(database_path)
    queued = store.create_queued("AAPL", date(2026, 5, 17).isoformat(), "mock")

    run_report_job_from_env(queued.id)

    completed = store.get(queued.id)
    assert completed is not None
    assert completed.status == "completed"


def test_worker_batch_job_runs_from_environment(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "reports.sqlite3"
    monkeypatch.setenv("RESEARCH_AGENTS_DB", str(database_path))
    store = ReportStore(database_path)
    batch = store.create_batch(["AAPL", "NVDA"], "2026-05-17", "mock", concurrency=2)

    run_report_batch_job_from_env(batch.id)

    completed = store.get_batch(batch.id)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.completed == 2


def test_worker_batch_item_job_runs_from_environment(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "reports.sqlite3"
    monkeypatch.setenv("RESEARCH_AGENTS_DB", str(database_path))
    store = ReportStore(database_path)
    batch = store.create_batch(["AAPL"], "2026-05-17", "mock", concurrency=1)
    item = store.list_batch_items(batch.id)[0]

    run_report_batch_item_job_from_env(item.id)

    completed = store.get_batch(batch.id)
    items = store.list_batch_items(batch.id)
    assert completed is not None
    assert completed.status == "completed"
    assert items[0].status == "completed"
    assert items[0].report_id is not None
