import pytest

from research_agents.config import Settings
from research_agents.rate_limit import LocalRateLimiter, create_rate_limiter


def test_local_rate_limiter_allows_zero_limit_without_sleep() -> None:
    limiter = LocalRateLimiter({"test": 0})

    limiter.wait("test")


def test_rate_limiter_rejects_invalid_mode() -> None:
    settings = Settings(None, "https://api.openai.com/v1", "test", rate_limit_mode="bad")

    with pytest.raises(ValueError, match="RATE_LIMIT_MODE"):
        create_rate_limiter(settings)
