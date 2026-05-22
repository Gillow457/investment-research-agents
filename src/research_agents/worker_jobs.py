from __future__ import annotations

from research_agents.config import Settings
from redis import Redis
from rq import Queue

from research_agents.jobs import run_report_batch_item_job, run_report_batch_job, run_report_job
from research_agents.storage import create_report_store


def run_report_job_from_env(report_id: int) -> None:
    settings = Settings.from_env()
    run_report_job(report_id, create_report_store(settings.database_url))


def run_report_batch_job_from_env(batch_id: int) -> None:
    settings = Settings.from_env()
    run_report_batch_job(batch_id, create_report_store(settings.database_url))


def run_report_batch_item_job_from_env(item_id: int) -> None:
    settings = Settings.from_env()
    store = create_report_store(settings.database_url)
    item = store.get_batch_item(item_id)
    if item is None:
        raise ValueError(f"Batch item {item_id} not found.")
    run_report_batch_item_job(item_id, store)
    _enqueue_next_batch_items(settings, store, item.batch_id)


def _enqueue_next_batch_items(settings: Settings, store: ReportStore, batch_id: int) -> None:
    batch = store.get_batch(batch_id)
    if batch is None or batch.status not in {"queued", "running"}:
        return
    queued_items = store.list_queued_batch_items(batch_id)
    if not queued_items:
        store.finalize_batch(batch_id)
        return
    slots = max(0, min(batch.concurrency - batch.running, len(queued_items)))
    if slots <= 0:
        return
    queue = Queue(settings.queue_name, connection=Redis.from_url(settings.redis_url))
    for item in queued_items[:slots]:
        queue.enqueue(run_report_batch_item_job_from_env, item.id)
