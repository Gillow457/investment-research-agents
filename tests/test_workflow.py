from datetime import date

import pytest

from research_agents import ResearchReport, run_research


def test_run_research_completes_with_mock_data() -> None:
    report = run_research("AAPL", date(2026, 5, 17))

    assert isinstance(report, ResearchReport)
    assert report.ticker == "AAPL"
    assert report.analysis_date == date(2026, 5, 17)
    assert report.decision in {"BUY", "HOLD", "SELL"}
    assert report.fundamentals is not None
    assert report.fundamentals.trailing_pe is not None
    assert report.signals
    assert any(signal.name == "fundamental_quality" for signal in report.signals)
    assert report.risks
    assert [opinion.role for opinion in report.debate_opinions] == ["bull", "bear", "risk"]
    assert [trace.agent for trace in report.agent_trace] == [
        "MarketDataAgent",
        "NewsSentimentAgent",
        "TechnicalAnalystAgent",
        "FundamentalAnalystAgent",
        "RiskManagerAgent",
        "BullDebateAgent",
        "BearDebateAgent",
        "RiskDebateAgent",
        "PortfolioManagerAgent",
    ]


def test_run_research_rejects_invalid_ticker() -> None:
    with pytest.raises(ValueError, match="Ticker must"):
        run_research("../AAPL", date(2026, 5, 17))
