from datetime import date

from research_agents import PortfolioContext, Position, run_research, run_research_with_portfolio
from research_agents.agents.position_sizing import PositionSizingAgent


def test_run_research_with_portfolio_generates_buy_plan() -> None:
    context = PortfolioContext(
        portfolio_value=100_000,
        cash=30_000,
        positions=[],
        risk_profile="moderate",
        max_position_pct=0.10,
        max_new_buy_pct=0.05,
        min_trade_value=500,
    )

    report = run_research_with_portfolio("AAPL", date(2026, 5, 17), context)

    assert report.position_sizing is not None
    assert report.position_sizing.action == "BUY"
    assert report.position_sizing.trade_value == 5000
    assert report.position_sizing.trade_shares is not None
    assert report.position_sizing.trade_shares > 0


def test_position_sizing_returns_no_trade_plan_without_context() -> None:
    report = run_research("AAPL", date(2026, 5, 17))

    sized = PositionSizingAgent().run(report, None)

    assert sized.position_sizing is not None
    assert sized.position_sizing.action == "NO_TRADE_PLAN"


def test_position_sizing_trims_when_current_position_exceeds_target() -> None:
    context = PortfolioContext(
        portfolio_value=100_000,
        cash=10_000,
        positions=[Position(ticker="AAPL", shares=100, market_value=20_000)],
        min_trade_value=500,
    )

    report = run_research_with_portfolio("AAPL", date(2026, 5, 17), context)

    assert report.position_sizing is not None
    assert report.position_sizing.action == "TRIM"
    assert report.position_sizing.trade_value is not None
    assert report.position_sizing.trade_value < 0


def test_position_sizing_holds_when_trade_is_below_minimum() -> None:
    context = PortfolioContext(
        portfolio_value=100_000,
        cash=30_000,
        positions=[],
        min_trade_value=10_000,
    )

    report = run_research_with_portfolio("AAPL", date(2026, 5, 17), context)

    assert report.position_sizing is not None
    assert report.position_sizing.action == "HOLD"
    assert "Minimum trade value" in "; ".join(report.position_sizing.constraints)
