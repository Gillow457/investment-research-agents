from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import yfinance as yf

from research_agents.graph.state import CompanyProfile, FundamentalMetrics, MarketContext, NewsItem, PricePoint
from research_agents.rate_limit import rate_limit


class YFinanceMarketDataProvider:
    def get_company_profile(self, ticker: str) -> CompanyProfile:
        rate_limit("yfinance")
        symbol = ticker.upper()
        info = yf.Ticker(symbol).get_info()
        if not info or info.get("quoteType") in {None, "NONE"}:
            raise ValueError(f"Could not load Yahoo Finance profile for ticker: {symbol}.")

        return CompanyProfile(
            ticker=symbol,
            name=info.get("longName") or info.get("shortName") or symbol,
            sector=info.get("sector") or "Unknown",
            description=info.get("longBusinessSummary") or "No company description returned by Yahoo Finance.",
        )

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        rate_limit("yfinance")
        symbol = ticker.upper()
        info = yf.Ticker(symbol).get_info()
        if not info or info.get("quoteType") in {None, "NONE"}:
            raise ValueError(f"Could not load Yahoo Finance fundamentals for ticker: {symbol}.")
        return FundamentalMetrics(
            source="yfinance",
            market_cap=_optional_float(info.get("marketCap")),
            trailing_pe=_optional_float(info.get("trailingPE")),
            forward_pe=_optional_float(info.get("forwardPE")),
            price_to_book=_optional_float(info.get("priceToBook")),
            revenue_growth=_optional_float(info.get("revenueGrowth")),
            gross_margin=_optional_float(info.get("grossMargins")),
            operating_margin=_optional_float(info.get("operatingMargins")),
            profit_margin=_optional_float(info.get("profitMargins")),
            free_cash_flow=_optional_float(info.get("freeCashflow")),
            debt_to_equity=_optional_float(info.get("debtToEquity")),
        )

    def get_price_history(self, ticker: str, analysis_date: date) -> list[PricePoint]:
        rate_limit("yfinance")
        symbol = ticker.upper()
        start = analysis_date - timedelta(days=14)
        end = analysis_date + timedelta(days=1)
        history = yf.Ticker(symbol).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
        if history.empty:
            raise ValueError(f"Could not load Yahoo Finance price history for ticker: {symbol}.")

        points: list[PricePoint] = []
        for index, row in history.tail(10).iterrows():
            points.append(
                PricePoint(
                    date=index.date(),
                    open=_required_float(row, "Open"),
                    high=_required_float(row, "High"),
                    low=_required_float(row, "Low"),
                    close=_required_float(row, "Close"),
                    volume=int(row.get("Volume") or 0),
                )
            )
        return points

    def get_market_context(
        self,
        ticker: str,
        analysis_date: date,
        price_history: list[PricePoint],
    ) -> MarketContext:
        rate_limit("yfinance")
        benchmark = _benchmark_for_ticker(ticker)
        start = analysis_date - timedelta(days=14)
        end = analysis_date + timedelta(days=1)
        history = yf.Ticker(benchmark).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
        if history.empty:
            raise ValueError(f"Could not load Yahoo Finance benchmark history for ticker: {benchmark}.")
        benchmark_points = [
            PricePoint(
                date=index.date(),
                open=_required_float(row, "Open"),
                high=_required_float(row, "High"),
                low=_required_float(row, "Low"),
                close=_required_float(row, "Close"),
                volume=int(row.get("Volume") or 0),
            )
            for index, row in history.tail(len(price_history)).iterrows()
        ]
        ticker_return = _return(price_history)
        benchmark_return = _return(benchmark_points)
        return MarketContext(
            benchmark_ticker=benchmark,
            ticker_return=round(ticker_return, 4),
            benchmark_return=round(benchmark_return, 4),
            relative_return=round(ticker_return - benchmark_return, 4),
            lookback_days=min(len(price_history), len(benchmark_points)),
        )


class YFinanceNewsProvider:
    _positive_terms = {"beat", "growth", "upgrade", "strong", "record", "surge", "profit", "demand"}
    _negative_terms = {"risk", "miss", "downgrade", "weak", "drop", "lawsuit", "pressure", "concern"}

    def get_news(self, ticker: str, analysis_date: date) -> list[NewsItem]:
        rate_limit("yfinance")
        symbol = ticker.upper()
        raw_news = yf.Ticker(symbol).news or []
        items: list[NewsItem] = []

        for item in raw_news[:5]:
            title = _news_title(item)
            if not title:
                continue
            published_at = _news_date(item) or analysis_date
            if published_at > analysis_date:
                published_at = analysis_date
            items.append(
                NewsItem(
                    date=published_at,
                    title=title,
                    source=_news_source(item),
                    sentiment=_heuristic_sentiment(title),
                )
            )

        if items:
            return items

        return [
            NewsItem(
                date=analysis_date,
                title=f"No recent Yahoo Finance news returned for {symbol}",
                source="Yahoo Finance",
                sentiment=0.0,
            )
        ]


def _required_float(row: Any, key: str) -> float:
    value = row.get(key)
    if value is None:
        raise ValueError(f"Yahoo Finance price row is missing {key}.")
    return round(float(value), 2)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _news_title(item: dict[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, dict):
        title = content.get("title")
        if title:
            return str(title)
    return str(item.get("title") or "")


def _news_source(item: dict[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, dict):
        provider = content.get("provider")
        if isinstance(provider, dict) and provider.get("displayName"):
            return str(provider["displayName"])
    return str(item.get("publisher") or "Yahoo Finance")


def _news_date(item: dict[str, Any]) -> date | None:
    content = item.get("content")
    if isinstance(content, dict) and content.get("pubDate"):
        try:
            return datetime.fromisoformat(str(content["pubDate"]).replace("Z", "+00:00")).date()
        except ValueError:
            return None

    timestamp = item.get("providerPublishTime")
    if isinstance(timestamp, int | float):
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
    return None


def _heuristic_sentiment(title: str) -> float:
    normalized = title.lower()
    positive_hits = sum(term in normalized for term in YFinanceNewsProvider._positive_terms)
    negative_hits = sum(term in normalized for term in YFinanceNewsProvider._negative_terms)
    score = (positive_hits - negative_hits) * 0.2
    return max(-1.0, min(1.0, score))


def _benchmark_for_ticker(ticker: str) -> str:
    normalized = ticker.upper()
    if normalized.endswith(".HK"):
        return "^HSI"
    if normalized.endswith(".TW") or normalized.endswith(".TWO"):
        return "^TWII"
    if normalized.endswith(".SS") or normalized.endswith(".SZ"):
        return "000001.SS"
    return "SPY"


def _return(points: list[PricePoint]) -> float:
    if len(points) < 2 or points[0].close == 0:
        return 0.0
    return (points[-1].close - points[0].close) / points[0].close
