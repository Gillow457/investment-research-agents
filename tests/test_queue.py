from datetime import date

import pytest

from research_agents.config import Settings
from research_agents.task_queue import RQQueueClient, create_queue_client
from research_agents.storage import ReportStore


class FakeRQQueue:
    def __init__(self) -> None:
        self.jobs = []

    def enqueue(self, func, *args):
        self.jobs.append((func, args))


def test_inline_queue_executes_report_immediately(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    queued = store.create_queued("AAPL", date(2026, 5, 17).isoformat(), "mock")
    settings = Settings(None, "https://api.openai.com/v1", "test", queue_mode="inline")

    queue = create_queue_client(settings, store)
    queue.enqueue_report(queued.id)

    completed = store.get(queued.id)
    assert completed is not None
    assert completed.status == "completed"


def test_rq_queue_enqueues_without_running_job() -> None:
    fake_queue = FakeRQQueue()
    settings = Settings(None, "https://api.openai.com/v1", "test", queue_mode="rq")
    store = ReportStore(":memory:")

    queue = RQQueueClient(settings, store, queue=fake_queue)  # type: ignore[arg-type]
    queue.enqueue_report(123)

    assert fake_queue.jobs[0][1] == (123,)
    assert fake_queue.jobs[0][0].__name__ == "run_report_job_from_env"


def test_rq_queue_enqueues_batch_items_up_to_batch_concurrency(tmp_path) -> None:
    fake_queue = FakeRQQueue()
    settings = Settings(None, "https://api.openai.com/v1", "test", queue_mode="rq")
    store = ReportStore(tmp_path / "reports.sqlite3")
    batch = store.create_batch(["AAPL", "NVDA", "AAPL"], "2026-05-17", "mock", concurrency=2)

    queue = RQQueueClient(settings, store, queue=fake_queue)  # type: ignore[arg-type]
    queue.enqueue_batch(batch.id)

    assert len(fake_queue.jobs) == 2
    assert all(job[0].__name__ == "run_report_batch_item_job_from_env" for job in fake_queue.jobs)
    assert store.get_batch(batch.id).status == "running"


def test_queue_rejects_invalid_mode(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    settings = Settings(None, "https://api.openai.com/v1", "test", queue_mode="bad")

    with pytest.raises(ValueError, match="QUEUE_MODE"):
        create_queue_client(settings, store)


def test_settings_reads_queue_environment(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://example:6379/3")
    monkeypatch.setenv("RESEARCH_AGENTS_QUEUE_MODE", "rq")
    monkeypatch.setenv("RESEARCH_AGENTS_QUEUE_NAME", "custom")
    monkeypatch.setenv("RESEARCH_AGENTS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
    monkeypatch.setenv("RESEARCH_AGENTS_CACHE_MODE", "redis")
    monkeypatch.setenv("RESEARCH_AGENTS_RATE_LIMIT_MODE", "redis")

    settings = Settings.from_env()

    assert settings.redis_url == "redis://example:6379/3"
    assert settings.queue_mode == "rq"
    assert settings.queue_name == "custom"
    assert settings.database_url == "postgresql+psycopg://user:pass@localhost/db"
    assert settings.cache_mode == "redis"
    assert settings.rate_limit_mode == "redis"
