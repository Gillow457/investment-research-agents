from __future__ import annotations

from research_agents.graph.state import AgentTrace, FundamentalMetrics, Signal


class FundamentalAnalystAgent:
    name = "FundamentalAnalystAgent"

    def run(self, fundamentals: FundamentalMetrics) -> dict:
        score = 0.0
        reasons: list[str] = []

        if fundamentals.revenue_growth is not None:
            if fundamentals.revenue_growth >= 0.10:
                score += 0.2
                reasons.append(f"revenue growth is healthy at {fundamentals.revenue_growth:.1%}")
            elif fundamentals.revenue_growth < 0:
                score -= 0.25
                reasons.append(f"revenue is contracting at {fundamentals.revenue_growth:.1%}")

        if fundamentals.gross_margin is not None and fundamentals.gross_margin >= 0.40:
            score += 0.15
            reasons.append(f"gross margin is strong at {fundamentals.gross_margin:.1%}")

        if fundamentals.profit_margin is not None:
            if fundamentals.profit_margin >= 0.15:
                score += 0.15
                reasons.append(f"profit margin is resilient at {fundamentals.profit_margin:.1%}")
            elif fundamentals.profit_margin < 0:
                score -= 0.25
                reasons.append(f"profit margin is negative at {fundamentals.profit_margin:.1%}")

        if fundamentals.free_cash_flow is not None:
            if fundamentals.free_cash_flow > 0:
                score += 0.15
                reasons.append("free cash flow is positive")
            else:
                score -= 0.25
                reasons.append("free cash flow is negative")

        valuation_penalty = 0.0
        if fundamentals.trailing_pe is not None and fundamentals.trailing_pe > 45:
            valuation_penalty += 0.15
        if fundamentals.price_to_book is not None and fundamentals.price_to_book > 20:
            valuation_penalty += 0.1
        if valuation_penalty:
            score -= valuation_penalty
            reasons.append("valuation multiples are elevated")

        if fundamentals.debt_to_equity is not None and fundamentals.debt_to_equity > 2:
            score -= 0.15
            reasons.append("leverage is elevated")

        bounded_score = max(-1.0, min(1.0, round(score, 2)))
        if bounded_score >= 0.25:
            view = "strong"
        elif bounded_score <= -0.2:
            view = "weak"
        else:
            view = "mixed"

        rationale = "; ".join(reasons) if reasons else "Fundamental data is limited or neutral."
        signal = Signal(
            name="fundamental_quality",
            value=view,
            score=bounded_score,
            rationale=rationale,
        )
        trace = AgentTrace(
            agent=self.name,
            message=f"Scored fundamentals as {view} with score {bounded_score:+.2f}.",
        )
        return {"signals": [signal], "agent_trace": [trace]}
