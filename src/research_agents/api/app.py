from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from research_agents.config import Settings
from research_agents.jobs import run_report_job
from research_agents.reports.models import ResearchReport
from research_agents.storage import ReportRecord, ReportStore


class CreateReportRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    analysis_date: date
    data_source: Literal["mock", "yfinance", "yfinance_gdelt"] = "mock"


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


def create_app(store: ReportStore | None = None) -> FastAPI:
    app = FastAPI(title="Investment Research Agents API", version="0.1.0")
    report_store = store or ReportStore(Settings.from_env().database_path)
    report_store.recover_stale_running()

    def get_store() -> ReportStore:
        return report_store

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/reports", response_model=ReportSummaryResponse, status_code=202)
    def create_report(
        request: CreateReportRequest,
        background_tasks: BackgroundTasks,
        store: ReportStore = Depends(get_store),
    ) -> ReportSummaryResponse:
        store.recover_stale_running()
        queued = store.create_queued(
            ticker=request.ticker.upper(),
            analysis_date=request.analysis_date.isoformat(),
            data_source=request.data_source,
        )
        background_tasks.add_task(run_report_job, queued.id, store)
        return _summary_response(queued)

    @app.post("/reports/{report_id}/retry", response_model=ReportSummaryResponse, status_code=202)
    def retry_report(
        report_id: int,
        background_tasks: BackgroundTasks,
        store: ReportStore = Depends(get_store),
    ) -> ReportSummaryResponse:
        store.recover_stale_running()
        record = store.get(report_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        try:
            queued = store.retry(report_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        background_tasks.add_task(run_report_job, queued.id, store)
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
