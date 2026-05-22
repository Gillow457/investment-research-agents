from __future__ import annotations

import asyncio
import json
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from research_agents.config import Settings
from research_agents.date_resolver import resolve_analysis_date
from research_agents.reports.models import ResearchReport
from research_agents.storage import BatchItemRecord, BatchRecord, ReportRecord, ReportStore, create_report_store
from research_agents.task_queue import QueueClient, create_queue_client


class CreateReportRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    analysis_date: date | None = None
    data_source: Literal["mock", "yfinance", "yfinance_gdelt", "yfinance_gdelt_sec"] = "yfinance_gdelt_sec"


class ReportSummaryResponse(BaseModel):
    id: int
    ticker: str
    analysis_date: date
    data_source: str
    status: str
    attempts: int
    max_attempts: int
    decision: str | None
    confidence: float | None
    error: str | None
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None


class ReportDetailResponse(ReportSummaryResponse):
    report: ResearchReport | None
    markdown: str | None


class BatchCreateRequest(BaseModel):
    tickers: list[str] = Field(min_length=1, max_length=100)
    analysis_date: date | None = None
    data_source: Literal["mock", "yfinance", "yfinance_gdelt", "yfinance_gdelt_sec"] = "yfinance_gdelt_sec"
    concurrency: int = Field(default=3, ge=1, le=5)


class BatchSummaryResponse(BaseModel):
    id: int
    batch_id: int
    status: str
    total: int
    queued: int
    running: int
    completed: int
    failed: int
    data_source: str
    requested_analysis_date: date | None
    concurrency: int
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None


class BatchItemResponse(BaseModel):
    id: int
    ticker: str
    status: str
    analysis_date: date | None
    report_id: int | None
    decision: str | None
    confidence: float | None
    error: str | None


class BatchDetailResponse(BatchSummaryResponse):
    items: list[BatchItemResponse]


def create_app(store: ReportStore | None = None, queue_client: QueueClient | None = None) -> FastAPI:
    app = FastAPI(title="Investment Research Agents API", version="0.1.0")
    settings = Settings.from_env()
    report_store = store or create_report_store(settings.database_url)
    task_queue = queue_client or create_queue_client(settings, report_store)
    report_store.recover_stale_running()

    def get_store() -> ReportStore:
        return report_store

    def get_queue() -> QueueClient:
        return task_queue

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/reports", response_model=ReportSummaryResponse, status_code=202)
    def create_report(
        request: CreateReportRequest,
        store: ReportStore = Depends(get_store),
        queue: QueueClient = Depends(get_queue),
    ) -> ReportSummaryResponse:
        store.recover_stale_running()
        try:
            resolved_date = resolve_analysis_date(request.ticker, request.analysis_date, request.data_source)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        queued = store.create_queued(
            ticker=request.ticker.upper(),
            analysis_date=resolved_date.isoformat(),
            data_source=request.data_source,
        )
        queue.enqueue_report(queued.id)
        return _summary_response(queued)

    @app.post("/report-batches", response_model=BatchSummaryResponse, status_code=202)
    def create_report_batch(
        request: BatchCreateRequest,
        store: ReportStore = Depends(get_store),
        queue: QueueClient = Depends(get_queue),
    ) -> BatchSummaryResponse:
        store.recover_stale_running()
        batch = store.create_batch(
            tickers=request.tickers,
            requested_analysis_date=request.analysis_date.isoformat() if request.analysis_date else None,
            data_source=request.data_source,
            concurrency=request.concurrency,
        )
        queue.enqueue_batch(batch.id)
        return _batch_summary_response(batch)

    @app.post("/report-batches/{batch_id}/retry-failed", response_model=BatchSummaryResponse, status_code=202)
    def retry_failed_report_batch_items(
        batch_id: int,
        store: ReportStore = Depends(get_store),
        queue: QueueClient = Depends(get_queue),
    ) -> BatchSummaryResponse:
        try:
            batch = store.retry_failed_batch_items(batch_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        queue.enqueue_batch(batch.id)
        return _batch_summary_response(batch)

    @app.get("/report-batches/{batch_id}/events")
    async def stream_report_batch_events(
        batch_id: int,
        store: ReportStore = Depends(get_store),
    ) -> StreamingResponse:
        if store.get_batch(batch_id) is None:
            raise HTTPException(status_code=404, detail="Report batch not found.")

        async def event_generator():
            terminal_statuses = {"completed", "completed_with_errors", "failed"}
            while True:
                snapshot = _batch_snapshot(store, batch_id)
                yield f"event: batch_update\ndata: {json.dumps(snapshot)}\n\n"
                if snapshot["status"] in terminal_statuses:
                    break
                await asyncio.sleep(1)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/report-batches/{batch_id}", response_model=BatchDetailResponse)
    def get_report_batch(batch_id: int, store: ReportStore = Depends(get_store)) -> BatchDetailResponse:
        batch = store.get_batch(batch_id)
        if batch is None:
            raise HTTPException(status_code=404, detail="Report batch not found.")
        return _batch_detail_response(batch, store.list_batch_items(batch_id))

    @app.post("/reports/{report_id}/retry", response_model=ReportSummaryResponse, status_code=202)
    def retry_report(
        report_id: int,
        store: ReportStore = Depends(get_store),
        queue: QueueClient = Depends(get_queue),
    ) -> ReportSummaryResponse:
        store.recover_stale_running()
        record = store.get(report_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        try:
            queued = store.retry(report_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        queue.enqueue_report(queued.id)
        return _summary_response(queued)

    @app.get("/reports/{report_id}", response_model=ReportDetailResponse)
    def get_report(report_id: int, store: ReportStore = Depends(get_store)) -> ReportDetailResponse:
        record = store.get(report_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        return _detail_response(record)

    @app.get("/reports", response_model=list[ReportSummaryResponse])
    def list_reports(
        limit: int = Query(default=20, ge=1, le=100),
        store: ReportStore = Depends(get_store),
    ) -> list[ReportSummaryResponse]:
        return [_summary_response(record) for record in store.list_recent(limit=limit)]

    return app


app = create_app()


def _summary_response(record: ReportRecord) -> ReportSummaryResponse:
    return ReportSummaryResponse(
        id=record.id,
        ticker=record.ticker,
        analysis_date=date.fromisoformat(record.analysis_date),
        data_source=record.data_source,
        status=record.status,
        attempts=record.attempts,
        max_attempts=record.max_attempts,
        decision=record.decision,
        confidence=record.confidence,
        error=record.last_error or record.error,
        created_at=record.created_at,
        updated_at=record.updated_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
    )


def _detail_response(record: ReportRecord) -> ReportDetailResponse:
    summary = _summary_response(record)
    return ReportDetailResponse(
        **summary.model_dump(),
        report=record.report(),
        markdown=record.markdown,
    )


def _batch_summary_response(record: BatchRecord) -> BatchSummaryResponse:
    return BatchSummaryResponse(
        id=record.id,
        batch_id=record.id,
        status=record.status,
        total=record.total,
        queued=record.queued,
        running=record.running,
        completed=record.completed,
        failed=record.failed,
        data_source=record.data_source,
        requested_analysis_date=(
            date.fromisoformat(record.requested_analysis_date) if record.requested_analysis_date else None
        ),
        concurrency=record.concurrency,
        created_at=record.created_at,
        updated_at=record.updated_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
    )


def _batch_item_response(record: BatchItemRecord) -> BatchItemResponse:
    return BatchItemResponse(
        id=record.id,
        ticker=record.ticker,
        status=record.status,
        analysis_date=date.fromisoformat(record.analysis_date) if record.analysis_date else None,
        report_id=record.report_id,
        decision=record.decision,
        confidence=record.confidence,
        error=record.error,
    )


def _batch_detail_response(batch: BatchRecord, items: list[BatchItemRecord]) -> BatchDetailResponse:
    summary = _batch_summary_response(batch)
    return BatchDetailResponse(
        **summary.model_dump(),
        items=[_batch_item_response(item) for item in items],
    )


def _batch_snapshot(store: ReportStore, batch_id: int) -> dict:
    batch = store.get_batch(batch_id)
    if batch is None:
        return {"batch_id": batch_id, "status": "missing", "items": []}
    detail = _batch_detail_response(batch, store.list_batch_items(batch_id))
    return detail.model_dump(mode="json")
