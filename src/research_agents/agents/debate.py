from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from research_agents.graph.state import AgentTrace, DebateOpinion, FundamentalMetrics, MarketContext, RiskNote, Signal
from research_agents.llm.client import LLMClient
from research_agents.prompts import DEBATE_PROMPT, EVIDENCE_RULES, JSON_RULES


class DebateOpinionOutput(BaseModel):
    thesis: str
    key_points: list[str] = Field(min_length=1, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)


class DebateAgent:
    def __init__(self, role: Literal["bull", "bear", "risk"], llm: LLMClient) -> None:
        self.role = role
        self.name = f"{role.title()}DebateAgent"
        self._llm = llm

    def run(
        self,
        ticker: str,
        analysis_date: date,
        signals: list[Signal],
        risks: list[RiskNote],
        fundamentals: FundamentalMetrics | None,
        market_context: MarketContext | None,
    ) -> dict:
        prompt = DEBATE_PROMPT.format(
            role=self.role,
            ticker=ticker,
            analysis_date=analysis_date.isoformat(),
            evidence_rules=EVIDENCE_RULES,
            json_rules=JSON_RULES,
            signals=[signal.model_dump() for signal in signals],
            risks=[risk.model_dump() for risk in risks],
            fundamentals=fundamentals.model_dump() if fundamentals else None,
            market_context=market_context.model_dump() if market_context else None,
        )
        output = self._llm.complete(prompt, response_schema=DebateOpinionOutput)
        if not isinstance(output, DebateOpinionOutput):
            raise TypeError(f"{self.name} did not return DebateOpinionOutput.")

        opinion = DebateOpinion(
            role=self.role,
            thesis=output.thesis,
            key_points=output.key_points,
            confidence=output.confidence,
        )
        trace = AgentTrace(
            agent=self.name,
            message=f"Produced {self.role} thesis with confidence {output.confidence:.2f}.",
        )
        return {"debate_opinions": [opinion], "agent_trace": [trace]}
