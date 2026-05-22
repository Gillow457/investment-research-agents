from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from threading import Lock

from redis import Redis

from research_agents.config import Settings


@dataclass
class MemoryCache:
    ttl_seconds: int
    _values: dict[str, tuple[float, str]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def get(self, key: str) -> str | None:
        with self._lock:
            value = self._values.get(key)
            if value is None:
                return None
            expires_at, payload = value
            if expires_at < time.time():
                self._values.pop(key, None)
                return None
            return payload

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._values[key] = (time.time() + self.ttl_seconds, value)


class RedisCache:
    def __init__(self, redis_url: str, ttl_seconds: int) -> None:
        self._redis = Redis.from_url(redis_url)
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> str | None:
        value = self._redis.get(key)
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)

    def set(self, key: str, value: str) -> None:
        self._redis.setex(key, self._ttl_seconds, value)


class NoopCache:
    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str) -> None:
        return None


def create_cache(settings: Settings):
    mode = settings.cache_mode.lower()
    if mode == "none":
        return NoopCache()
    if mode == "redis":
        return RedisCache(settings.redis_url, settings.cache_ttl_seconds)
    if mode == "memory":
        return MemoryCache(settings.cache_ttl_seconds)
    raise ValueError("RESEARCH_AGENTS_CACHE_MODE must be 'none', 'memory', or 'redis'.")


_cache = None


def get_cache():
    global _cache
    if _cache is None:
        _cache = create_cache(Settings.from_env())
    return _cache


def cache_get_json(key: str):
    payload = get_cache().get(key)
    return None if payload is None else json.loads(payload)


def cache_set_json(key: str, value) -> None:
    get_cache().set(key, json.dumps(value, ensure_ascii=True))
