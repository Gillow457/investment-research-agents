from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from research_agents.date_resolver import resolve_analysis_date
from research_agents.graph.workflow import run_research
from research_agents.reports.render import render_markdown

app = typer.Typer(help="Generate multi-agent investment research reports.")
console = Console()


@app.callback()
def main() -> None:
    """Generate multi-agent investment research reports."""


@app.command()
def analyze(
    ticker: Annotated[str, typer.Option("--ticker", "-t", help="Ticker symbol, such as AAPL.")],
    analysis_date: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Analysis date in YYYY-MM-DD format."),
    ] = None,
    data_source: Annotated[
        str,
        typer.Option("--data-source", help="Data source: mock, yfinance, yfinance_gdelt, or yfinance_gdelt_sec."),
    ] = "yfinance_gdelt_sec",
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Optional Markdown output path.")] = None,
) -> None:
    try:
        parsed_date = date.fromisoformat(analysis_date) if analysis_date else None
    except ValueError as exc:
        raise typer.BadParameter("Date must use YYYY-MM-DD format.") from exc

    try:
        resolved_date = resolve_analysis_date(ticker, parsed_date, data_source)
        report = run_research(ticker, resolved_date, data_source=data_source)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    markdown = render_markdown(report)
    console.print(markdown)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        console.print(f"\nSaved report to {output}")
