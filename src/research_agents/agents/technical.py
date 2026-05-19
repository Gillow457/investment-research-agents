from __future__ import annotations

from research_agents.graph.state import AgentTrace, PricePoint, Signal


class TechnicalAnalystAgent:
    name = "TechnicalAnalystAgent"

    def run(self, price_history: list[PricePoint]) -> dict:
        if len(price_history) < 2:
            raise ValueError("At least two price points are required for technical analysis.")

        first_close = price_history[0].close
        last_close = price_history[-1].close
        change_pct = ((last_close - first_close) / first_close) * 100

        if change_pct >= 3:
            trend = "uptrend"
            score = 0.35
        elif change_pct <= -3:
            trend = "downtrend"
            score = -0.35
        else:
            trend = "sideways"
            score = 0.0

        signal = Signal(
            name="technical_trend",
            value=trend,
            score=score,
            rationale=f"Close moved {change_pct:.2f}% across the lookback window.",
        )
        trace = AgentTrace(agent=self.name, message=f"Detected {trend} with {change_pct:.2f}% price change.")
        return {"signals": [signal], "agent_trace": [trace]}
