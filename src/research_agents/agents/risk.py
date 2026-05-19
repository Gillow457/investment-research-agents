from __future__ import annotations

from research_agents.graph.state import AgentTrace, FundamentalMetrics, PricePoint, RiskNote, Signal


class RiskManagerAgent:
    name = "RiskManagerAgent"

    def run(
        self,
        price_history: list[PricePoint],
        signals: list[Signal],
        fundamentals: FundamentalMetrics | None = None,
    ) -> dict:
        closes = [point.close for point in price_history]
        daily_moves = [
            abs((closes[index] - closes[index - 1]) / closes[index - 1])
            for index in range(1, len(closes))
        ]
        average_move = sum(daily_moves) / len(daily_moves)
        sentiment = next((signal for signal in signals if signal.name == "news_sentiment"), None)

        risks: list[RiskNote] = []
        if average_move > 0.025:
            risks.append(
                RiskNote(
                    level="high",
                    category="volatility",
                    detail=f"Average absolute daily move is {average_move:.2%}.",
                )
            )
        else:
            risks.append(
                RiskNote(
                    level="medium",
                    category="volatility",
                    detail=f"Average absolute daily move is {average_move:.2%}.",
                )
            )

        if sentiment and sentiment.score < 0:
            risks.append(
                RiskNote(
                    level="medium",
                    category="sentiment",
                    detail="News sentiment is below neutral and may pressure near-term performance.",
                )
            )

        fundamental = next((signal for signal in signals if signal.name == "fundamental_quality"), None)
        if fundamental and fundamental.score < 0:
            risks.append(
                RiskNote(
                    level="medium",
                    category="fundamentals",
                    detail=f"Fundamental quality signal is {fundamental.value}: {fundamental.rationale}",
                )
            )
        if fundamentals and fundamentals.debt_to_equity is not None and fundamentals.debt_to_equity > 2:
            risks.append(
                RiskNote(
                    level="medium",
                    category="balance_sheet",
                    detail=f"Debt/equity is elevated at {fundamentals.debt_to_equity:.2f}.",
                )
            )
        if fundamentals and fundamentals.trailing_pe is not None and fundamentals.trailing_pe > 60:
            risks.append(
                RiskNote(
                    level="medium",
                    category="valuation",
                    detail=f"Trailing PE is elevated at {fundamentals.trailing_pe:.2f}.",
                )
            )

        overall = "high" if any(risk.level == "high" for risk in risks) else "medium"
        trace = AgentTrace(agent=self.name, message=f"Assigned overall risk level: {overall}.")
        return {"risks": risks, "agent_trace": [trace]}
