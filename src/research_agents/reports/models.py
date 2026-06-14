from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from research_agents.graph.state import AgentTrace, DebateOpinion, FundamentalMetrics, MarketContext, RiskNote, Signal


class Position(BaseModel):
    ticker: str
    shares: float = Field(ge=0.0)
    market_value: float = Field(ge=0.0)
    average_cost: float | None = Field(default=None, ge=0.0)


class PortfolioContext(BaseModel):
    portfolio_value: float = Field(gt=0.0)
    cash: float = Field(ge=0.0)
    positions: list[Position] = Field(default_factory=list)
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"
    max_position_pct: float = Field(default=0.10, gt=0.0, le=1.0)
    max_new_buy_pct: float = Field(default=0.05, gt=0.0, le=1.0)
    min_trade_value: float = Field(default=500.0, ge=0.0)


class PositionSizingRecommendation(BaseModel):
    action: Literal["BUY", "HOLD", "SELL", "TRIM", "NO_TRADE_PLAN"]
    current_weight: float | None = None
    target_weight: float | None = None
    trade_value: float | None = None
    trade_shares: float | None = None
    rationale: str
    constraints: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    ticker: str
    analysis_date: date
    decision: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    fundamentals: FundamentalMetrics | None = None
    market_context: MarketContext | None = None
    position_sizing: PositionSizingRecommendation | None = None
    signals: list[Signal]
    risks: list[RiskNote]
    debate_opinions: list[DebateOpinion] = Field(default_factory=list)
    agent_trace: list[AgentTrace]
