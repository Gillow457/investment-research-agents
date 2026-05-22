from __future__ import annotations

from datetime import date

from research_agents.data.providers import MarketDataProvider
from research_agents.data.sec_companyfacts import SECCompanyFactsProvider
from research_agents.graph.state import CompanyProfile, FundamentalMetrics, MarketContext, PricePoint


class CompositeMarketDataProvider:
    def __init__(
        self,
        primary: MarketDataProvider,
        sec_facts: SECCompanyFactsProvider | None = None,
    ) -> None:
        self._primary = primary
        self._sec_facts = sec_facts or SECCompanyFactsProvider()

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        return self._primary.get_company_profile(ticker)

    def get_price_history(self, ticker: str, analysis_date: date) -> list[PricePoint]:
        return self._primary.get_price_history(ticker, analysis_date)

    def get_market_context(
        self,
        ticker: str,
        analysis_date: date,
        price_history: list[PricePoint],
    ) -> MarketContext:
        return self._primary.get_market_context(ticker, analysis_date, price_history)

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        yfinance_metrics = self._primary.get_fundamentals(ticker)
        if "." in ticker:
            return yfinance_metrics
        try:
            sec_metrics = self._sec_facts.get_fundamentals(ticker)
        except ValueError:
            return yfinance_metrics
        return _merge_fundamentals(sec_metrics, yfinance_metrics)


def _merge_fundamentals(authoritative: FundamentalMetrics, fallback: FundamentalMetrics) -> FundamentalMetrics:
    data = fallback.model_dump()
    for key, value in authoritative.model_dump().items():
        if value is not None:
            data[key] = value
    data["source"] = authoritative.source
    return FundamentalMetrics.model_validate(data)
