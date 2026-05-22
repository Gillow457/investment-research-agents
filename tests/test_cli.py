from typer.testing import CliRunner

from research_agents.cli import app


def test_cli_analyze_outputs_markdown() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--ticker", "AAPL", "--date", "2026-05-17", "--data-source", "mock"])

    assert result.exit_code == 0
    assert "Investment Research Report: AAPL" in result.output
    assert "Agent Trace" in result.output


def test_cli_analyze_accepts_only_ticker(monkeypatch) -> None:
    from datetime import date

    monkeypatch.setattr(
        "research_agents.cli.resolve_analysis_date",
        lambda ticker, requested_date, data_source: date(2026, 5, 17),
    )

    result = CliRunner().invoke(app, ["analyze", "--ticker", "AAPL", "--data-source", "mock"])

    assert result.exit_code == 0
    assert "Investment Research Report: AAPL" in result.output


def test_cli_rejects_unknown_ticker() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--ticker", "UNKNOWN", "--date", "2026-05-17", "--data-source", "mock"])

    assert result.exit_code != 0
    assert "Unsupported mock ticker" in result.output
