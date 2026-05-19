from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from research_agents.graph.state import AgentTrace, DebateOpinion, FundamentalMetrics, RiskNote, Signal
from research_agents.llm.client import LLMClient
from research_agents.prompts import EVIDENCE_RULES, JSON_RULES, PORTFOLIO_PROMPT
from research_agents.reports.models import ResearchReport


class PortfolioDecisionOutput(BaseModel):
    decision: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str


class PortfolioManagerAgent:
    name = "PortfolioManagerAgent"

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(
        self,
        ticker: str,
        analysis_date: date,
        signals: list[Signal],
        risks: list[RiskNote],
        debate_opinions: list[DebateOpinion],
        fundamentals: FundamentalMetrics | None,
        trace: list[AgentTrace],
    ) -> dict:
        score = sum(signal.score for signal in signals)
        has_high_risk = any(risk.level == "high" for risk in risks)

        if score >= 0.35 and not has_high_risk:
            decision = "BUY"
            confidence = 0.68
        elif score <= -0.25 or has_high_risk:
            decision = "SELL" if score < -0.35 else "HOLD"
            confidence = 0.61
        else:
            decision = "HOLD"
            confidence = 0.58

        prompt = PORTFOLIO_PROMPT.format(
            ticker=ticker,
            analysis_date=analysis_date.isoformat(),
            evidence_rules=EVIDENCE_RULES,
            json_rules=JSON_RULES,
            baseline_decision=decision,
            baseline_confidence=confidence,
            aggregate_signal_score=score,
            high_risk=has_high_risk,
            signals=[signal.model_dump() for signal in signals],
            risks=[risk.model_dump() for risk in risks],
            debate_opinions=[opinion.model_dump() for opinion in debate_opinions],
            fundamentals=fundamentals.model_dump() if fundamentals else None,
        )
        output = self._llm.complete(prompt, response_schema=PortfolioDecisionOutput)
        if not isinstance(output, PortfolioDecisionOutput):
            raise TypeError("PortfolioManagerAgent did not return PortfolioDecisionOutput.")

        manager_trace = AgentTrace(
            agent=self.name,
            message=(
                f"Resolved debate into {output.decision} with confidence {output.confidence:.2f} "
                f"from aggregate score {score:.2f}."
            ),
        )
        report = ResearchReport(
            ticker=ticker,
            analysis_date=analysis_date,
            decision=output.decision,
            confidence=output.confidence,
            summary=output.summary,
            fundamentals=fundamentals,
            signals=signals,
            risks=risks,
            debate_opinions=debate_opinions,
            agent_trace=[*trace, manager_trace],
        )
        return {"report": report, "agent_trace": [manager_trace]}
