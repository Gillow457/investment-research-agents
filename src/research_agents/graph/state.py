from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field


def append_items[T](left: list[T] | None, right: list[T] | None) -> list[T]:
    return [*(left or []), *(right or [])]


class CompanyProfile(BaseModel):
    ticker: str
    name: str
    sector: str
    description: str


class PricePoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class NewsItem(BaseModel):
    date: date
    title: str
    source: str
    sentiment: float = Field(ge=-1.0, le=1.0)


class FundamentalMetrics(BaseModel):
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    revenue_growth: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    profit_margin: float | None = None
    free_cash_flow: float | None = None
    debt_to_equity: float | None = None


class Signal(BaseModel):
    name: str
    value: str
    score: float = Field(ge=-1.0, le=1.0)
    rationale: str


class RiskNote(BaseModel):
    level: Literal["low", "medium", "high"]
    category: str
    detail: str


class AgentTrace(BaseModel):
    agent: str
    message: str


class DebateOpinion(BaseModel):
    role: Literal["bull", "bear", "risk"]
    thesis: str
    key_points: list[str] = Field(min_length=1, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchState(TypedDict, total=False):
    ticker: str
    analysis_date: date
    company_profile: CompanyProfile
    price_history: list[PricePoint]
    news_items: list[NewsItem]
    fundamentals: FundamentalMetrics
    signals: Annotated[list[Signal], append_items]
    risks: Annotated[list[RiskNote], append_items]
    debate_opinions: Annotated[list[DebateOpinion], append_items]
    agent_trace: Annotated[list[AgentTrace], append_items]
    report: object
