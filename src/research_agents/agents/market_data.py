from __future__ import annotations

from datetime import date

from research_agents.data.providers import MarketDataProvider
from research_agents.graph.state import AgentTrace


class MarketDataAgent:
    name = "MarketDataAgent"

    def __init__(self, market_data: MarketDataProvider) -> None:
        self._market_data = market_data

    def run(self, ticker: str, analysis_date: date) -> dict:
        profile = self._market_data.get_company_profile(ticker)
        prices = self._market_data.get_price_history(ticker, analysis_date)
        fundamentals = self._market_data.get_fundamentals(ticker)
        market_context = self._market_data.get_market_context(ticker, analysis_date, prices)
        trace = AgentTrace(
            agent=self.name,
            message=(
                f"Loaded profile for {profile.name}, {len(prices)} daily prices, "
                f"fundamentals, and {market_context.benchmark_ticker} benchmark context."
            ),
        )
        return {
            "company_profile": profile,
            "price_history": prices,
            "fundamentals": fundamentals,
            "market_context": market_context,
            "agent_trace": [trace],
        }
