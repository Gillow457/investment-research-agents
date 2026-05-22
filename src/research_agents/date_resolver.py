from __future__ import annotations

from datetime import date

import yfinance as yf


def resolve_analysis_date(ticker: str, requested_date: date | None, data_source: str) -> date:
    if requested_date is not None:
        return requested_date
    if data_source == "mock":
        return date.today()
    if data_source in {"yfinance", "yfinance_gdelt", "yfinance_gdelt_sec"}:
        return _latest_yfinance_trading_date(ticker)
    raise ValueError("Data source must be 'mock', 'yfinance', 'yfinance_gdelt', or 'yfinance_gdelt_sec'.")


def _latest_yfinance_trading_date(ticker: str) -> date:
    try:
        history = yf.Ticker(ticker.upper()).history(period="10d", interval="1d", auto_adjust=False)
    except Exception as exc:
        raise ValueError(f"Could not resolve latest trading date for {ticker}: {exc}") from exc
    if history.empty:
        raise ValueError(f"Could not resolve latest trading date for {ticker}: no recent price data returned.")
    latest_index = history.tail(1).index[0]
    return latest_index.date()
