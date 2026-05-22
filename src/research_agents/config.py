from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    database_path: str = "data/research_reports.sqlite3"
    database_url: str = "data/research_reports.sqlite3"
    redis_url: str = "redis://localhost:6379/0"
    queue_mode: str = "inline"
    queue_name: str = "research-agents"
    cache_mode: str = "memory"
    cache_ttl_seconds: int = 900
    rate_limit_mode: str = "local"
    yfinance_rate_limit_per_minute: int = 120
    gdelt_rate_limit_per_minute: int = 60
    sec_rate_limit_per_minute: int = 60
    llm_rate_limit_per_minute: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY") or None
        database_url = os.getenv("RESEARCH_AGENTS_DATABASE_URL") or os.getenv(
            "RESEARCH_AGENTS_DB", "data/research_reports.sqlite3"
        )
        return cls(
            openai_api_key=api_key,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            database_path=database_url,
            database_url=database_url,
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            queue_mode=os.getenv("RESEARCH_AGENTS_QUEUE_MODE", "inline"),
            queue_name=os.getenv("RESEARCH_AGENTS_QUEUE_NAME", "research-agents"),
            cache_mode=os.getenv("RESEARCH_AGENTS_CACHE_MODE", "memory"),
            cache_ttl_seconds=int(os.getenv("RESEARCH_AGENTS_CACHE_TTL_SECONDS", "900")),
            rate_limit_mode=os.getenv("RESEARCH_AGENTS_RATE_LIMIT_MODE", "local"),
            yfinance_rate_limit_per_minute=int(os.getenv("YFINANCE_RATE_LIMIT_PER_MINUTE", "120")),
            gdelt_rate_limit_per_minute=int(os.getenv("GDELT_RATE_LIMIT_PER_MINUTE", "60")),
            sec_rate_limit_per_minute=int(os.getenv("SEC_RATE_LIMIT_PER_MINUTE", "60")),
            llm_rate_limit_per_minute=int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "60")),
        )
