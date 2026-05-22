from datetime import date
from types import SimpleNamespace

from research_agents.data.yfinance_provider import YFinanceMarketDataProvider, YFinanceNewsProvider
from research_agents.data.yfinance_provider import _benchmark_for_ticker


class FakeTicker:
    news = [
        {
            "content": {
                "title": "AAPL demand growth remains strong",
                "provider": {"displayName": "FakeNews"},
                "pubDate": "2026-05-16T10:00:00Z",
            }
        }
    ]

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def get_info(self) -> dict:
        return {
            "quoteType": "EQUITY",
            "longName": "Apple Inc.",
            "sector": "Technology",
            "longBusinessSummary": "Consumer technology company.",
            "marketCap": 3100000000000,
            "trailingPE": 31.5,
            "forwardPE": 28.0,
            "priceToBook": 45.0,
            "revenueGrowth": 0.06,
            "grossMargins": 0.46,
            "operatingMargins": 0.31,
            "profitMargins": 0.25,
            "freeCashflow": 100000000000,
            "debtToEquity": 1.5,
        }

    def history(self, **kwargs):
        return FakeHistory()


class FakeHistory:
    empty = False

    def tail(self, count: int):
        return self

    def iterrows(self):
        rows = [
            ("2026-05-15", {"Open": 180.0, "High": 182.0, "Low": 179.0, "Close": 181.0, "Volume": 100}),
            ("2026-05-16", {"Open": 181.0, "High": 183.0, "Low": 180.0, "Close": 182.0, "Volume": 120}),
        ]
        for raw_date, row in rows:
            yield SimpleNamespace(date=lambda raw_date=raw_date: date.fromisoformat(raw_date)), row


def test_yfinance_market_data_provider_maps_profile_and_prices(monkeypatch) -> None:
    monkeypatch.setattr("research_agents.data.yfinance_provider.yf.Ticker", FakeTicker)

    provider = YFinanceMarketDataProvider()
    profile = provider.get_company_profile("aapl")
    prices = provider.get_price_history("aapl", date(2026, 5, 17))
    fundamentals = provider.get_fundamentals("aapl")
    market_context = provider.get_market_context("aapl", date(2026, 5, 17), prices)

    assert profile.ticker == "AAPL"
    assert profile.name == "Apple Inc."
    assert len(prices) == 2
    assert prices[-1].close == 182.0
    assert fundamentals.trailing_pe == 31.5
    assert fundamentals.revenue_growth == 0.06
    assert market_context.benchmark_ticker == "SPY"
    assert market_context.lookback_days == 2


def test_yfinance_news_provider_maps_news(monkeypatch) -> None:
    monkeypatch.setattr("research_agents.data.yfinance_provider.yf.Ticker", FakeTicker)

    news = YFinanceNewsProvider().get_news("AAPL", date(2026, 5, 17))

    assert news[0].source == "FakeNews"
    assert news[0].sentiment > 0


def test_yfinance_benchmark_mapping_supports_taiwan_tickers() -> None:
    assert _benchmark_for_ticker("2357.TW") == "^TWII"
