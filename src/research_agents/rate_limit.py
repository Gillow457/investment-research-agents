from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

from redis import Redis

from research_agents.config import Settings


@dataclass
class LocalRateLimiter:
    limits: dict[str, int]
    _hits: dict[str, list[float]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def wait(self, bucket: str) -> None:
        limit = self.limits.get(bucket, 0)
        if limit <= 0:
            return
        while True:
            now = time.monotonic()
            with self._lock:
                hits = [hit for hit in self._hits.get(bucket, []) if now - hit < 60]
                if len(hits) < limit:
                    hits.append(now)
                    self._hits[bucket] = hits
                    return
                sleep_for = max(0.01, 60 - (now - hits[0]))
                self._hits[bucket] = hits
            time.sleep(min(sleep_for, 1.0))


class RedisRateLimiter:
    def __init__(self, redis_url: str, limits: dict[str, int]) -> None:
        self._redis = Redis.from_url(redis_url)
        self._limits = limits

    def wait(self, bucket: str) -> None:
        limit = self._limits.get(bucket, 0)
        if limit <= 0:
            return
        while True:
            window = int(time.time() // 60)
            key = f"research_agents:rate:{bucket}:{window}"
            count = int(self._redis.incr(key))
            if count == 1:
                self._redis.expire(key, 70)
            if count <= limit:
                return
            time.sleep(1.0)


class NoopRateLimiter:
    def wait(self, bucket: str) -> None:
        return


def create_rate_limiter(settings: Settings):
    limits = {
        "yfinance": settings.yfinance_rate_limit_per_minute,
        "gdelt": settings.gdelt_rate_limit_per_minute,
        "sec": settings.sec_rate_limit_per_minute,
        "llm": settings.llm_rate_limit_per_minute,
    }
    mode = settings.rate_limit_mode.lower()
    if mode == "none":
        return NoopRateLimiter()
    if mode == "redis":
        return RedisRateLimiter(settings.redis_url, limits)
    if mode == "local":
        return LocalRateLimiter(limits)
    raise ValueError("RESEARCH_AGENTS_RATE_LIMIT_MODE must be 'none', 'local', or 'redis'.")


_rate_limiter = None


def get_rate_limiter():
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = create_rate_limiter(Settings.from_env())
    return _rate_limiter


def rate_limit(bucket: str) -> None:
    get_rate_limiter().wait(bucket)
