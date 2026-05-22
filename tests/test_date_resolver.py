from datetime import date
from types import SimpleNamespace

import pytest

from research_agents.date_resolver import resolve_analysis_date


class FakeHistory:
    empty = False

    def tail(self, count: int):
        return self

    @property
    def index(self):
        return [SimpleNamespace(date=lambda: date(2026, 5, 19))]


class EmptyHistory(FakeHistory):
    empty = True


class FakeTicker:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker

    def history(self, **kwargs):
        return FakeHistory()


def test_resolve_analysis_date_uses_requested_date() -> None:
    requested = date(2026, 5, 17)

    resolved = resolve_analysis_date("AAPL", requested, "yfinance")

    assert resolved == requested


def test_resolve_analysis_date_uses_today_for_mock(monkeypatch) -> None:
    class FakeDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 5, 20)

    monkeypatch.setattr("research_agents.date_resolver.date", FakeDate)

    resolved = resolve_analysis_date("AAPL", None, "mock")

    assert resolved == date(2026, 5, 20)


def test_resolve_analysis_date_uses_latest_yfinance_date(monkeypatch) -> None:
    monkeypatch.setattr("research_agents.date_resolver.yf.Ticker", FakeTicker)

    resolved = resolve_analysis_date("1810.HK", None, "yfinance_gdelt_sec")

    assert resolved == date(2026, 5, 19)


def test_resolve_analysis_date_fails_when_no_recent_data(monkeypatch) -> None:
    class EmptyTicker(FakeTicker):
        def history(self, **kwargs):
            return EmptyHistory()

    monkeypatch.setattr("research_agents.date_resolver.yf.Ticker", EmptyTicker)

    with pytest.raises(ValueError, match="no recent price data"):
        resolve_analysis_date("BAD", None, "yfinance")
