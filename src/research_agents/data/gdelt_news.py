from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen

from research_agents.graph.state import NewsItem
from research_agents.rate_limit import rate_limit


class GDELTNewsProvider:
    endpoint = "https://api.gdeltproject.org/api/v2/doc/doc"
    _positive_terms = {"beat", "growth", "upgrade", "strong", "record", "surge", "profit", "demand"}
    _negative_terms = {"risk", "miss", "downgrade", "weak", "drop", "lawsuit", "pressure", "concern"}

    def get_news(self, ticker: str, analysis_date: date) -> list[NewsItem]:
        rate_limit("gdelt")
        query = _company_query(ticker)
        start = analysis_date - timedelta(days=7)
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": "10",
            "sort": "HybridRel",
            "startdatetime": start.strftime("%Y%m%d000000"),
            "enddatetime": analysis_date.strftime("%Y%m%d235959"),
        }
        url = f"{self.endpoint}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return [
                NewsItem(
                    date=analysis_date,
                    title=f"GDELT news lookup failed for {ticker.upper()}: {exc}",
                    source="GDELT",
                    sentiment=0.0,
                )
            ]

        articles = payload.get("articles") or []
        items: list[NewsItem] = []
        for article in articles[:5]:
            title = str(article.get("title") or "").strip()
            if not title:
                continue
            published_at = _parse_gdelt_date(str(article.get("seendate") or "")) or analysis_date
            if published_at > analysis_date:
                continue
            items.append(
                NewsItem(
                    date=published_at,
                    title=title,
                    source=str(article.get("domain") or "GDELT"),
                    sentiment=_heuristic_sentiment(title),
                )
            )

        if items:
            return items
        return [
            NewsItem(
                date=analysis_date,
                title=f"No recent GDELT news returned for {ticker.upper()}",
                source="GDELT",
                sentiment=0.0,
            )
        ]


def _company_query(ticker: str) -> str:
    normalized = ticker.upper()
    aliases = {
        "1810.HK": '"Xiaomi" OR "Xiaomi Corporation"',
        "AAPL": '"Apple" OR "Apple Inc"',
        "NVDA": '"NVIDIA" OR "Nvidia Corporation"',
        "MSFT": '"Microsoft" OR "Microsoft Corporation"',
        "TSLA": '"Tesla" OR "Tesla Inc"',
    }
    return aliases.get(normalized, f'"{normalized}"')


def _parse_gdelt_date(value: str) -> date | None:
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _heuristic_sentiment(title: str) -> float:
    normalized = title.lower()
    positive_hits = sum(term in normalized for term in GDELTNewsProvider._positive_terms)
    negative_hits = sum(term in normalized for term in GDELTNewsProvider._negative_terms)
    score = (positive_hits - negative_hits) * 0.2
    return max(-1.0, min(1.0, score))
