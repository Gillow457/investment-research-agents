from datetime import date

from research_agents.cache import MemoryCache
from research_agents.data.cached import CachedMarketDataProvider, CachedNewsProvider
from research_agents.data.mock import MockMarketDataProvider, MockNewsProvider


class CountingMarketProvider(MockMarketDataProvider):
    def __init__(self) -> None:
        self.profile_calls = 0

    def get_company_profile(self, ticker: str):
        self.profile_calls += 1
        return super().get_company_profile(ticker)


class CountingNewsProvider(MockNewsProvider):
    def __init__(self) -> None:
        self.news_calls = 0

    def get_news(self, ticker: str, analysis_date: date):
        self.news_calls += 1
        return super().get_news(ticker, analysis_date)


def test_cached_market_data_provider_reuses_cached_profile(monkeypatch) -> None:
    monkeypatch.setattr("research_agents.cache._cache", MemoryCache(ttl_seconds=60))
    provider = CountingMarketProvider()
    cached = CachedMarketDataProvider(provider, "test")

    first = cached.get_company_profile("AAPL")
    second = cached.get_company_profile("AAPL")

    assert first == second
    assert provider.profile_calls == 1


def test_cached_news_provider_reuses_cached_news(monkeypatch) -> None:
    monkeypatch.setattr("research_agents.cache._cache", MemoryCache(ttl_seconds=60))
    provider = CountingNewsProvider()
    cached = CachedNewsProvider(provider, "test")

    first = cached.get_news("AAPL", date(2026, 5, 17))
    second = cached.get_news("AAPL", date(2026, 5, 17))

    assert first == second
    assert provider.news_calls == 1
