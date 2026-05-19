from typer.testing import CliRunner

from research_agents.cli import app


def test_cli_analyze_outputs_markdown() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--ticker", "AAPL", "--date", "2026-05-17"])

    assert result.exit_code == 0
    assert "Investment Research Report: AAPL" in result.output
    assert "Agent Trace" in result.output


def test_cli_rejects_unknown_ticker() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--ticker", "UNKNOWN", "--date", "2026-05-17"])

    assert result.exit_code != 0
    assert "Unsupported mock ticker" in result.output
