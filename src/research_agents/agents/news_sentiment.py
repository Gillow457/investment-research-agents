from __future__ import annotations

from datetime import date

from research_agents.data.providers import NewsProvider
from research_agents.graph.state import AgentTrace, Signal
from research_agents.llm.client import LLMClient
from research_agents.prompts import EVIDENCE_RULES, NEWS_SENTIMENT_PROMPT


class NewsSentimentAgent:
    name = "NewsSentimentAgent"

    def __init__(self, news: NewsProvider, llm: LLMClient) -> None:
        self._news = news
        self._llm = llm

    def run(self, ticker: str, analysis_date: date) -> dict:
        news_items = self._news.get_news(ticker, analysis_date)
        average_sentiment = sum(item.sentiment for item in news_items) / len(news_items)
        label = "positive" if average_sentiment > 0.15 else "negative" if average_sentiment < -0.15 else "mixed"
        prompt = NEWS_SENTIMENT_PROMPT.format(
            ticker=ticker,
            average_sentiment=average_sentiment,
            label=label,
            news_titles=[item.title for item in news_items],
            evidence_rules=EVIDENCE_RULES,
        )
        summary = self._llm.complete(prompt)
        signal = Signal(
            name="news_sentiment",
            value=label,
            score=round(average_sentiment, 2),
            rationale=summary,
        )
        trace = AgentTrace(
            agent=self.name,
            message=f"Processed {len(news_items)} news items; sentiment is {label}.",
        )
        return {"news_items": news_items, "signals": [signal], "agent_trace": [trace]}
