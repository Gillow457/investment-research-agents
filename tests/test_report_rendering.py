from datetime import date

from research_agents.graph.state import AgentTrace, FundamentalMetrics, RiskNote, Signal
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
    assert "## Risks" in markdown
    assert "## Agent Trace" in markdown
