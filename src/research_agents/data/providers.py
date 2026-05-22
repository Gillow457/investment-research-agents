from __future__ import annotations

from datetime import date
from typing import Protocol

from research_agents.graph.state import CompanyProfile, FundamentalMetrics, MarketContext, NewsItem, PricePoint


class MarketDataProvider(Protocol):
    def get_price_history(self, ticker: str, analysis_date: date) -> list[PricePoint]:
        ...

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        ...

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        ...

    def get_market_context(
        self,
        ticker: str,
        analysis_date: date,
        price_history: list[PricePoint],
    ) -> MarketContext:
        ...


class NewsProvider(Protocol):
    def get_news(self, ticker: str, analysis_date: date) -> list[NewsItem]:
        ...
