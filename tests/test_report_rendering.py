from datetime import date

from research_agents.graph.state import AgentTrace, FundamentalMetrics, MarketContext, RiskNote, Signal
from research_agents.reports.models import PositionSizingRecommendation
from research_agents.reports.models import ResearchReport
from research_agents.reports.render import render_markdown


def test_report_rendering_contains_key_sections() -> None:
    report = ResearchReport(
        ticker="AAPL",
        analysis_date=date(2026, 5, 17),
        decision="HOLD",
        confidence=0.58,
        summary="Summary text.",
        fundamentals=FundamentalMetrics(trailing_pe=31.5, revenue_growth=0.08, profit_margin=0.18),
        market_context=MarketContext(
            benchmark_ticker="SPY",
            ticker_return=0.03,
            benchmark_return=0.01,
            relative_return=0.02,
            lookback_days=7,
        ),
        position_sizing=PositionSizingRecommendation(
            action="BUY",
            current_weight=0.0,
            target_weight=0.05,
            trade_value=5000,
            trade_shares=25,
            rationale="Sizing test.",
            constraints=["Research planning only."],
        ),
        signals=[Signal(name="technical_trend", value="sideways", score=0.0, rationale="Flat.")],
        risks=[RiskNote(level="medium", category="volatility", detail="Moderate moves.")],
        agent_trace=[AgentTrace(agent="TechnicalAnalystAgent", message="Detected sideways.")],
    )

    markdown = render_markdown(report)

    assert "AAPL" in markdown
    assert "2026-05-17" in markdown
    assert "HOLD" in markdown
    assert "## Fundamentals" in markdown
    assert "Trailing PE" in markdown
    assert "## Market Context" in markdown
    assert "SPY" in markdown
    assert "## Position Sizing" in markdown
    assert "Trade value" in markdown
    assert "## Risks" in markdown
    assert "## Agent Trace" in markdown
