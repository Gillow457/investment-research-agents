from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from redis import Redis
from rq import Queue

from research_agents.config import Settings
from research_agents.jobs import run_report_batch_job, run_report_job
from research_agents.storage import ReportStore
from research_agents.worker_jobs import run_report_batch_item_job_from_env, run_report_job_from_env


class QueueClient(Protocol):
    def enqueue_report(self, report_id: int) -> None:
        ...

    def enqueue_batch(self, batch_id: int) -> None:
        ...


@dataclass(frozen=True)
class InlineQueueClient:
    store: ReportStore

    def enqueue_report(self, report_id: int) -> None:
        run_report_job(report_id, self.store)

    def enqueue_batch(self, batch_id: int) -> None:
        run_report_batch_job(batch_id, self.store)


class RQQueueClient:
    def __init__(self, settings: Settings, store: ReportStore, queue: Queue | None = None) -> None:
        self._settings = settings
        self._store = store
        self._queue = queue or Queue(settings.queue_name, connection=Redis.from_url(settings.redis_url))

    def enqueue_report(self, report_id: int) -> None:
        self._queue.enqueue(run_report_job_from_env, report_id)

    def enqueue_batch(self, batch_id: int) -> None:
        batch = self._store.mark_batch_running(batch_id)
        queued_items = self._store.list_queued_batch_items(batch_id)
        slots = min(batch.concurrency, len(queued_items))
        for item in queued_items[:slots]:
            self._queue.enqueue(run_report_batch_item_job_from_env, item.id)


def create_queue_client(settings: Settings, store: ReportStore) -> QueueClient:
    mode = settings.queue_mode.lower()
    if mode == "inline":
        return InlineQueueClient(store)
    if mode == "rq":
        return RQQueueClient(settings, store)
    raise ValueError("RESEARCH_AGENTS_QUEUE_MODE must be 'inline' or 'rq'.")
