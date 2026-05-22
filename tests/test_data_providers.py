from datetime import date

import pytest

from research_agents.data import MockMarketDataProvider, MockNewsProvider


def test_mock_market_data_is_stable() -> None:
    provider = MockMarketDataProvider()

    profile = provider.get_company_profile("AAPL")
    prices = provider.get_price_history("AAPL", date(2026, 5, 17))
    fundamentals = provider.get_fundamentals("AAPL")
    market_context = provider.get_market_context("AAPL", date(2026, 5, 17), prices)

    assert profile.name == "Apple Inc."
    assert len(prices) == 7
    assert prices[-1].date == date(2026, 5, 17)
    assert fundamentals.trailing_pe == 31.5
    assert fundamentals.free_cash_flow is not None
    assert market_context.benchmark_ticker == "SPY"
    assert market_context.lookback_days == len(prices)


def test_mock_news_rejects_unknown_ticker() -> None:
    provider = MockNewsProvider()

    with pytest.raises(ValueError, match="Unsupported mock ticker"):
        provider.get_news("UNKNOWN", date(2026, 5, 17))
