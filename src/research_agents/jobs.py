from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from research_agents.date_resolver import resolve_analysis_date
from research_agents.graph.workflow import run_research, run_research_with_portfolio
from research_agents.reports.models import PortfolioContext
from research_agents.reports.render import render_markdown
from research_agents.storage import BatchItemRecord, ReportRecord, ReportStore


def run_report_job(report_id: int, store: ReportStore) -> ReportRecord:
    record = store.mark_running(report_id)
    try:
        context = _portfolio_context(record.portfolio_context_json)
        if context is None:
            report = run_research(
                ticker=record.ticker,
                analysis_date=date.fromisoformat(record.analysis_date),
                data_source=record.data_source,
            )
        else:
            report = run_research_with_portfolio(
                ticker=record.ticker,
                analysis_date=date.fromisoformat(record.analysis_date),
                portfolio_context=context,
                data_source=record.data_source,
            )
        markdown = render_markdown(report)
        return store.mark_completed(report_id, report, markdown)
    except Exception as exc:
        return store.mark_failed(report_id, str(exc))


def run_report_batch_job(batch_id: int, store: ReportStore) -> None:
    batch = store.mark_batch_running(batch_id)
    items = store.list_queued_batch_items(batch_id)
    max_workers = max(1, min(batch.concurrency, 5))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_batch_item, item, batch.data_source, batch.requested_analysis_date, store) for item in items]
        for future in as_completed(futures):
            future.result()

    store.finalize_batch(batch_id)


def run_report_batch_item_job(item_id: int, store: ReportStore) -> None:
    item = store.get_batch_item(item_id)
    if item is None:
        raise ValueError(f"Batch item {item_id} not found.")
    batch = store.get_batch(item.batch_id)
    if batch is None:
        raise ValueError(f"Batch {item.batch_id} not found.")
    store.mark_batch_running(batch.id)
    _run_batch_item(item, batch.data_source, batch.requested_analysis_date, store)
    store.finalize_batch(batch.id)


def _run_batch_item(
    item: BatchItemRecord,
    data_source: str,
    requested_analysis_date: str | None,
    store: ReportStore,
) -> None:
    try:
        parsed_requested_date = date.fromisoformat(requested_analysis_date) if requested_analysis_date else None
        resolved_date = resolve_analysis_date(item.ticker, parsed_requested_date, data_source)
        running_item = store.mark_batch_item_running(item.id, resolved_date.isoformat())
        report_record = store.create_queued(
            ticker=running_item.ticker,
            analysis_date=resolved_date.isoformat(),
            data_source=data_source,
            batch_id=running_item.batch_id,
            portfolio_context_json=store.get_batch(running_item.batch_id).portfolio_context_json,
        )
        completed_report = run_report_job(report_record.id, store)
        if completed_report.status == "completed":
            store.mark_batch_item_completed(running_item.id, completed_report)
        else:
            store.mark_batch_item_failed(
                running_item.id,
                completed_report.last_error or completed_report.error or "Report failed.",
                report_id=completed_report.id,
            )
    except Exception as exc:
        store.mark_batch_item_failed(item.id, str(exc))


def _portfolio_context(payload: str | None) -> PortfolioContext | None:
    if payload is None:
        return None
    return PortfolioContext.model_validate_json(payload)
