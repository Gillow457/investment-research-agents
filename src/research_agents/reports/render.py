from __future__ import annotations

from research_agents.reports.models import ResearchReport


def render_markdown(report: ResearchReport) -> str:
    fundamentals = _render_fundamentals(report)
    market_context = _render_market_context(report)
    position_sizing = _render_position_sizing(report)
    signals = "\n".join(
        f"- **{signal.name}**: `{signal.value}` ({signal.score:+.2f}) - {signal.rationale}"
        for signal in report.signals
    )
    risks = "\n".join(
        f"- **{risk.level.upper()} / {risk.category}**: {risk.detail}" for risk in report.risks
    )
    debate = "\n".join(
        f"- **{opinion.role.upper()}** ({opinion.confidence:.0%}): {opinion.thesis} "
        f"Key points: {'; '.join(opinion.key_points)}"
        for opinion in report.debate_opinions
    )
    trace = "\n".join(f"- `{item.agent}`: {item.message}" for item in report.agent_trace)
    return (
        f"# Investment Research Report: {report.ticker}\n\n"
        f"- Analysis date: `{report.analysis_date.isoformat()}`\n"
        f"- Decision: **{report.decision}**\n"
        f"- Confidence: **{report.confidence:.0%}**\n\n"
        "## Summary\n\n"
        f"{report.summary}\n\n"
        "## Fundamentals\n\n"
        f"{fundamentals}\n\n"
        "## Market Context\n\n"
        f"{market_context}\n\n"
        "## Position Sizing\n\n"
        f"{position_sizing}\n\n"
        "## Signals\n\n"
        f"{signals}\n\n"
        "## Risks\n\n"
        f"{risks}\n\n"
        "## Debate\n\n"
        f"{debate or '- No debate opinions recorded.'}\n\n"
        "## Agent Trace\n\n"
        f"{trace}\n"
    )


def _render_fundamentals(report: ResearchReport) -> str:
    if report.fundamentals is None:
        return "- No fundamental metrics recorded."
    metrics = report.fundamentals
    rows = [
        ("Market cap", _format_large(metrics.market_cap)),
        ("Trailing PE", _format_ratio(metrics.trailing_pe)),
        ("Forward PE", _format_ratio(metrics.forward_pe)),
        ("Price/book", _format_ratio(metrics.price_to_book)),
        ("Revenue growth", _format_pct(metrics.revenue_growth)),
        ("Gross margin", _format_pct(metrics.gross_margin)),
        ("Operating margin", _format_pct(metrics.operating_margin)),
        ("Profit margin", _format_pct(metrics.profit_margin)),
        ("Free cash flow", _format_large(metrics.free_cash_flow)),
        ("Debt/equity", _format_ratio(metrics.debt_to_equity)),
    ]
    return "\n".join(f"- **{label}**: {value}" for label, value in rows)


def _render_position_sizing(report: ResearchReport) -> str:
    if report.position_sizing is None:
        return "- No portfolio context provided; no trade sizing plan generated."
    sizing = report.position_sizing
    rows = [
        ("Action", sizing.action),
        ("Current weight", _format_pct(sizing.current_weight)),
        ("Target weight", _format_pct(sizing.target_weight)),
        ("Trade value", _format_large(sizing.trade_value)),
        ("Trade shares", "n/a" if sizing.trade_shares is None else f"{sizing.trade_shares:.4f}"),
        ("Rationale", sizing.rationale),
        ("Constraints", "; ".join(sizing.constraints) if sizing.constraints else "None"),
    ]
    return "\n".join(f"- **{label}**: {value}" for label, value in rows)


def _render_market_context(report: ResearchReport) -> str:
    if report.market_context is None:
        return "- No market benchmark context recorded."
    context = report.market_context
    rows = [
        ("Benchmark", context.benchmark_ticker),
        ("Ticker return", _format_pct(context.ticker_return)),
        ("Benchmark return", _format_pct(context.benchmark_return)),
        ("Relative return", _format_pct(context.relative_return)),
        ("Lookback price points", str(context.lookback_days)),
    ]
    return "\n".join(f"- **{label}**: {value}" for label, value in rows)


def _format_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def _format_ratio(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _format_large(value: float | None) -> str:
    if value is None:
        return "n/a"
    absolute = abs(value)
    if absolute >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    return f"{value:.2f}"
