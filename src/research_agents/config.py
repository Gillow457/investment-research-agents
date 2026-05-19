from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    database_path: str = "data/research_reports.sqlite3"

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY") or None
        return cls(
            openai_api_key=api_key,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            database_path=os.getenv("RESEARCH_AGENTS_DB", "data/research_reports.sqlite3"),
        )
