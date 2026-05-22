from __future__ import annotations

from datetime import date

from pydantic import TypeAdapter

from research_agents.cache import cache_get_json, cache_set_json
from research_agents.data.providers import MarketDataProvider, NewsProvider
from research_agents.graph.state import CompanyProfile, FundamentalMetrics, MarketContext, NewsItem, PricePoint

_PRICE_POINTS = TypeAdapter(list[PricePoint])
_NEWS_ITEMS = TypeAdapter(list[NewsItem])


class CachedMarketDataProvider:
    def __init__(self, provider: MarketDataProvider, namespace: str) -> None:
        self._provider = provider
        self._namespace = namespace

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        key = _key(self._namespace, "profile", ticker.upper())
        cached = cache_get_json(key)
        if cached is not None:
            return CompanyProfile.model_validate(cached)
        value = self._provider.get_company_profile(ticker)
        cache_set_json(key, value.model_dump(mode="json"))
        return value

    def get_price_history(self, ticker: str, analysis_date: date) -> list[PricePoint]:
        key = _key(self._namespace, "prices", ticker.upper(), analysis_date.isoformat())
        cached = cache_get_json(key)
        if cached is not None:
            return _PRICE_POINTS.validate_python(cached)
        value = self._provider.get_price_history(ticker, analysis_date)
        cache_set_json(key, [point.model_dump(mode="json") for point in value])
        return value

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        key = _key(self._namespace, "fundamentals", ticker.upper())
        cached = cache_get_json(key)
        if cached is not None:
            return FundamentalMetrics.model_validate(cached)
        value = self._provider.get_fundamentals(ticker)
        cache_set_json(key, value.model_dump(mode="json"))
        return value

    def get_market_context(
        self,
        ticker: str,
        analysis_date: date,
        price_history: list[PricePoint],
    ) -> MarketContext:
        key = _key(self._namespace, "market_context", ticker.upper(), analysis_date.isoformat())
        cached = cache_get_json(key)
        if cached is not None:
            return MarketContext.model_validate(cached)
        value = self._provider.get_market_context(ticker, analysis_date, price_history)
        cache_set_json(key, value.model_dump(mode="json"))
        return value


class CachedNewsProvider:
    def __init__(self, provider: NewsProvider, namespace: str) -> None:
        self._provider = provider
        self._namespace = namespace

    def get_news(self, ticker: str, analysis_date: date) -> list[NewsItem]:
        key = _key(self._namespace, "news", ticker.upper(), analysis_date.isoformat())
        cached = cache_get_json(key)
        if cached is not None:
            return _NEWS_ITEMS.validate_python(cached)
        value = self._provider.get_news(ticker, analysis_date)
        cache_set_json(key, [item.model_dump(mode="json") for item in value])
        return value


def _key(*parts: str) -> str:
    return "research_agents:cache:" + ":".join(parts)
