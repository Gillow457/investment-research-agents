from datetime import date

from research_agents.data.composite import CompositeMarketDataProvider
from research_agents.graph.state import CompanyProfile, FundamentalMetrics, MarketContext, PricePoint


class FakePrimaryProvider:
    def get_company_profile(self, ticker: str) -> CompanyProfile:
        return CompanyProfile(ticker=ticker.upper(), name="Apple Inc.", sector="Technology", description="Test")

    def get_price_history(self, ticker: str, analysis_date: date) -> list[PricePoint]:
        return []

    def get_market_context(
        self,
        ticker: str,
        analysis_date: date,
        price_history: list[PricePoint],
    ) -> MarketContext:
        return MarketContext(
            benchmark_ticker="SPY",
            ticker_return=0.02,
            benchmark_return=0.01,
            relative_return=0.01,
            lookback_days=2,
        )

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        return FundamentalMetrics(source="yfinance", trailing_pe=31.5, revenue=100.0, profit_margin=0.1)


class FakeSECProvider:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        if self.should_fail:
            raise ValueError("not found")
        return FundamentalMetrics(source="sec_companyfacts", revenue=120.0, net_income=30.0)


def test_composite_provider_prefers_sec_facts_and_preserves_yfinance_ratios() -> None:
    provider = CompositeMarketDataProvider(FakePrimaryProvider(), FakeSECProvider())

    fundamentals = provider.get_fundamentals("AAPL")

    assert fundamentals.source == "sec_companyfacts"
    assert fundamentals.revenue == 120.0
    assert fundamentals.net_income == 30.0
    assert fundamentals.trailing_pe == 31.5
    assert fundamentals.profit_margin == 0.1


def test_composite_provider_falls_back_when_sec_is_unavailable() -> None:
    provider = CompositeMarketDataProvider(FakePrimaryProvider(), FakeSECProvider(should_fail=True))

    fundamentals = provider.get_fundamentals("AAPL")

    assert fundamentals.source == "yfinance"
    assert fundamentals.revenue == 100.0


def test_composite_provider_skips_sec_for_exchange_suffixed_tickers() -> None:
    sec = FakeSECProvider()
    provider = CompositeMarketDataProvider(FakePrimaryProvider(), sec)

    fundamentals = provider.get_fundamentals("1810.HK")

    assert fundamentals.source == "yfinance"
    assert fundamentals.revenue == 100.0
