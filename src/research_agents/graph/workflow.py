from __future__ import annotations

import re
from datetime import date

from langgraph.graph import END, START, StateGraph

from research_agents.agents import (
    MarketDataAgent,
    DebateAgent,
    FundamentalAnalystAgent,
    MarketContextAgent,
    NewsSentimentAgent,
    PortfolioManagerAgent,
    RiskManagerAgent,
    TechnicalAnalystAgent,
)
from research_agents.config import Settings
from research_agents.data import (
    CachedMarketDataProvider,
    CachedNewsProvider,
    CompositeMarketDataProvider,
    MockMarketDataProvider,
    MockNewsProvider,
    GDELTNewsProvider,
    YFinanceMarketDataProvider,
    YFinanceNewsProvider,
)
from research_agents.graph.state import ResearchState
from research_agents.llm.client import LLMClient, create_llm_client
from research_agents.reports.models import PortfolioContext, ResearchReport
from research_agents.agents.position_sizing import PositionSizingAgent

_TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.:-]{0,15}$")


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not _TICKER_PATTERN.fullmatch(normalized):
        raise ValueError("Ticker must be 1-16 uppercase letters, digits, dots, colons, or hyphens.")
    return normalized


def build_research_graph(llm: LLMClient | None = None, data_source: str = "mock"):
    if data_source == "mock":
        market_data = MockMarketDataProvider()
        news = MockNewsProvider()
    elif data_source == "yfinance":
        market_data = YFinanceMarketDataProvider()
        news = YFinanceNewsProvider()
    elif data_source == "yfinance_gdelt":
        market_data = YFinanceMarketDataProvider()
        news = GDELTNewsProvider()
    elif data_source == "yfinance_gdelt_sec":
        market_data = CompositeMarketDataProvider(YFinanceMarketDataProvider())
        news = GDELTNewsProvider()
    else:
        raise ValueError("Data source must be 'mock', 'yfinance', 'yfinance_gdelt', or 'yfinance_gdelt_sec'.")

    if data_source != "mock":
        market_data = CachedMarketDataProvider(market_data, data_source)
        news = CachedNewsProvider(news, data_source)

    llm_client = llm or create_llm_client(Settings.from_env())

    market_agent = MarketDataAgent(market_data)
    news_agent = NewsSentimentAgent(news, llm_client)
    technical_agent = TechnicalAnalystAgent()
    fundamental_agent = FundamentalAnalystAgent()
    market_context_agent = MarketContextAgent()
    risk_agent = RiskManagerAgent()
    bull_agent = DebateAgent("bull", llm_client)
    bear_agent = DebateAgent("bear", llm_client)
    debate_risk_agent = DebateAgent("risk", llm_client)
    portfolio_agent = PortfolioManagerAgent(llm_client)

    def load_market_data(state: ResearchState) -> dict:
        return market_agent.run(state["ticker"], state["analysis_date"])

    def analyze_news(state: ResearchState) -> dict:
        return news_agent.run(state["ticker"], state["analysis_date"])

    def analyze_technicals(state: ResearchState) -> dict:
        return technical_agent.run(state["price_history"])

    def analyze_fundamentals(state: ResearchState) -> dict:
        return fundamental_agent.run(state["fundamentals"])

    def analyze_market_context(state: ResearchState) -> dict:
        return market_context_agent.run(state["market_context"])

    def assess_risk(state: ResearchState) -> dict:
        return risk_agent.run(
            state["price_history"],
            state.get("signals", []),
            state.get("fundamentals"),
            state.get("market_context"),
        )

    def debate_bull(state: ResearchState) -> dict:
        return bull_agent.run(
            state["ticker"],
            state["analysis_date"],
            state.get("signals", []),
            state.get("risks", []),
            state.get("fundamentals"),
            state.get("market_context"),
        )

    def debate_bear(state: ResearchState) -> dict:
        return bear_agent.run(
            state["ticker"],
            state["analysis_date"],
            state.get("signals", []),
            state.get("risks", []),
            state.get("fundamentals"),
            state.get("market_context"),
        )

    def debate_risk(state: ResearchState) -> dict:
        return debate_risk_agent.run(
            state["ticker"],
            state["analysis_date"],
            state.get("signals", []),
            state.get("risks", []),
            state.get("fundamentals"),
            state.get("market_context"),
        )

    def decide_portfolio(state: ResearchState) -> dict:
        return portfolio_agent.run(
            ticker=state["ticker"],
            analysis_date=state["analysis_date"],
            signals=state.get("signals", []),
            risks=state.get("risks", []),
            debate_opinions=state.get("debate_opinions", []),
            fundamentals=state.get("fundamentals"),
            market_context=state.get("market_context"),
            trace=state.get("agent_trace", []),
        )

    graph = StateGraph(ResearchState)
    graph.add_node("market_data", load_market_data)
    graph.add_node("news_sentiment", analyze_news)
    graph.add_node("technical_analysis", analyze_technicals)
    graph.add_node("fundamental_analysis", analyze_fundamentals)
    graph.add_node("market_context_analysis", analyze_market_context)
    graph.add_node("risk_management", assess_risk)
    graph.add_node("bull_debate", debate_bull)
    graph.add_node("bear_debate", debate_bear)
    graph.add_node("risk_debate", debate_risk)
    graph.add_node("portfolio_management", decide_portfolio)

    graph.add_edge(START, "market_data")
    graph.add_edge("market_data", "news_sentiment")
    graph.add_edge("news_sentiment", "technical_analysis")
    graph.add_edge("technical_analysis", "fundamental_analysis")
    graph.add_edge("fundamental_analysis", "market_context_analysis")
    graph.add_edge("market_context_analysis", "risk_management")
    graph.add_edge("risk_management", "bull_debate")
    graph.add_edge("bull_debate", "bear_debate")
    graph.add_edge("bear_debate", "risk_debate")
    graph.add_edge("risk_debate", "portfolio_management")
    graph.add_edge("portfolio_management", END)
    return graph.compile()


def run_research(ticker: str, analysis_date: date, data_source: str = "mock") -> ResearchReport:
    normalized = _normalize_ticker(ticker)
    result = build_research_graph(data_source=data_source).invoke(
        {
            "ticker": normalized,
            "analysis_date": analysis_date,
            "signals": [],
            "risks": [],
            "debate_opinions": [],
            "agent_trace": [],
        }
    )
    report = result["report"]
    if not isinstance(report, ResearchReport):
        raise TypeError("Research graph completed without a valid ResearchReport.")
    return report


def run_research_with_portfolio(
    ticker: str,
    analysis_date: date,
    portfolio_context: PortfolioContext | dict,
    data_source: str = "mock",
) -> ResearchReport:
    context = (
        portfolio_context
        if isinstance(portfolio_context, PortfolioContext)
        else PortfolioContext.model_validate(portfolio_context)
    )
    report = run_research(ticker, analysis_date, data_source=data_source)
    return PositionSizingAgent().run(report, context)
