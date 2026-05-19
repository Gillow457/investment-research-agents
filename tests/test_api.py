from fastapi.testclient import TestClient

from research_agents.api import create_app
from research_agents.storage import ReportStore


def test_api_creates_and_reads_report(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/reports",
        json={"ticker": "AAPL", "analysis_date": "2026-05-17", "data_source": "mock"},
    )

    assert response.status_code == 202
    created = response.json()
    assert created["status"] == "queued"
    assert created["attempts"] == 0

    fetched = client.get(f"/reports/{created['id']}")
    assert fetched.status_code == 200
    detail = fetched.json()
    assert detail["id"] == created["id"]
    assert detail["status"] == "completed"
    assert detail["attempts"] == 1
    assert detail["report"]["ticker"] == "AAPL"
    assert "## Debate" in detail["markdown"]


def test_api_accepts_yfinance_gdelt_source(tmp_path, monkeypatch) -> None:
    from research_agents.reports.models import ResearchReport
    from research_agents.graph.state import AgentTrace, RiskNote, Signal
    from datetime import date

    def fake_run_research(ticker: str, analysis_date: date, data_source: str) -> ResearchReport:
        assert data_source == "yfinance_gdelt"
        return ResearchReport(
            ticker=ticker,
            analysis_date=analysis_date,
            decision="HOLD",
            confidence=0.5,
            summary="ok",
            signals=[Signal(name="mock", value="mixed", score=0, rationale="test")],
            risks=[RiskNote(level="medium", category="test", detail="test")],
            agent_trace=[AgentTrace(agent="test", message="test")],
        )

    monkeypatch.setattr("research_agents.jobs.run_research", fake_run_research)
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/reports",
        json={"ticker": "1810.HK", "analysis_date": "2026-05-19", "data_source": "yfinance_gdelt"},
    )

    assert response.status_code == 202
    detail = client.get(f"/reports/{response.json()['id']}").json()
    assert detail["status"] == "completed"


def test_api_lists_reports(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    client.post("/reports", json={"ticker": "AAPL", "analysis_date": "2026-05-17"})
    response = client.get("/reports")

    assert response.status_code == 200
    assert response.json()[0]["ticker"] == "AAPL"


def test_api_records_failed_background_report(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post("/reports", json={"ticker": "UNKNOWN", "analysis_date": "2026-05-17"})

    assert response.status_code == 202
    detail = client.get(f"/reports/{response.json()['id']}").json()
    assert detail["status"] == "failed"
    assert "Unsupported mock ticker" in detail["error"]


def test_api_retries_failed_report(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.sqlite3")
    app = create_app(store)
    client = TestClient(app)
    queued = store.create_queued("AAPL", "2026-05-17", "mock")
    store.mark_running(queued.id)
    store.mark_failed(queued.id, "temporary failure")

    response = client.post(f"/reports/{queued.id}/retry")

    assert response.status_code == 202
    detail = client.get(f"/reports/{queued.id}").json()
    assert detail["status"] == "completed"
    assert detail["attempts"] == 2
    assert detail["report"]["ticker"] == "AAPL"
