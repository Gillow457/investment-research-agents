from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from research_agents.graph.state import AgentTrace, DebateOpinion, FundamentalMetrics, MarketContext, RiskNote, Signal


class ResearchReport(BaseModel):
    ticker: str
    analysis_date: date
    decision: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    fundamentals: FundamentalMetrics | None = None
    market_context: MarketContext | None = None
    signals: list[Signal]
    risks: list[RiskNote]
    debate_opinions: list[DebateOpinion] = Field(default_factory=list)
    agent_trace: list[AgentTrace]
