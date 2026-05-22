from __future__ import annotations

from redis import Redis
from rq import Queue, Worker

from research_agents.config import Settings


def main() -> None:
    settings = Settings.from_env()
    connection = Redis.from_url(settings.redis_url)
    queue = Queue(settings.queue_name, connection=connection)
    worker = Worker([queue], connection=connection)
    worker.work()
