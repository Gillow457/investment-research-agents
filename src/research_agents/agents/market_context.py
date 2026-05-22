from __future__ import annotations

from research_agents.graph.state import AgentTrace, MarketContext, Signal


class MarketContextAgent:
    name = "MarketContextAgent"

    def run(self, market_context: MarketContext) -> dict:
        relative = market_context.relative_return
        if relative >= 0.02:
            value = "outperforming"
            score = 0.2
        elif relative <= -0.02:
            value = "underperforming"
            score = -0.2
        else:
            value = "in_line"
            score = 0.0

        signal = Signal(
            name="market_context",
            value=value,
            score=score,
            rationale=(
                f"Ticker return was {market_context.ticker_return:.1%} versus "
                f"{market_context.benchmark_ticker} at {market_context.benchmark_return:.1%} "
                f"over {market_context.lookback_days} price points."
            ),
        )
        trace = AgentTrace(
            agent=self.name,
            message=(
                f"Compared ticker performance against {market_context.benchmark_ticker}; "
                f"relative return {relative:.1%}."
            ),
        )
        return {"signals": [signal], "agent_trace": [trace]}
