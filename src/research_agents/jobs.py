from __future__ import annotations

from datetime import date

from research_agents.graph.workflow import run_research
from research_agents.reports.render import render_markdown
from research_agents.storage import ReportStore


def run_report_job(report_id: int, store: ReportStore) -> None:
    record = store.mark_running(report_id)
    try:
        report = run_research(
            ticker=record.ticker,
            analysis_date=date.fromisoformat(record.analysis_date),
            data_source=record.data_source,
        )
        markdown = render_markdown(report)
        store.mark_completed(report_id, report, markdown)
    except Exception as exc:
        store.mark_failed(report_id, str(exc))
