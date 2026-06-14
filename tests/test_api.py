from fastapi.testclient import TestClient

from research_agents.api import create_app
from research_agents.storage import ReportStore


class RecordingQueue:
    def __init__(self) -> None:
        self.report_ids = []
        self.batch_ids = []

    def enqueue_report(self, report_id: int) -> None:
        self.report_ids.append(report_id)

    def enqueue_batch(self, batch_id: int) -> None:
        self.batch_ids.append(batch_id)


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


def test_api_serves_minimal_web_console(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Investment Research Agents" in response.text
    assert 'id="report-form"' in response.text
    assert 'fetch("/reports"' in response.text


def test_api_can_enqueue_report_without_executing_inline(tmp_path) -> None:
    queue = RecordingQueue()
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"), queue_client=queue)
    client = TestClient(app)

    response = client.post(
        "/reports",
        json={"ticker": "AAPL", "analysis_date": "2026-05-17", "data_source": "mock"},
    )

    assert response.status_code == 202
    assert queue.report_ids == [response.json()["id"]]
    detail = client.get(f"/reports/{response.json()['id']}").json()
    assert detail["status"] == "queued"


def test_api_creates_report_with_only_ticker(tmp_path, monkeypatch) -> None:
    from datetime import date

    monkeypatch.setattr(
        "research_agents.api.app.resolve_analysis_date",
        lambda ticker, requested_date, data_source: date(2026, 5, 17),
    )
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post("/reports", json={"ticker": "AAPL", "data_source": "mock"})

    assert response.status_code == 202
    assert response.json()["analysis_date"] == "2026-05-17"


def test_api_creates_report_with_portfolio_context(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/reports",
        json={
            "ticker": "AAPL",
            "analysis_date": "2026-05-17",
            "data_source": "mock",
            "portfolio_context": {
                "portfolio_value": 100000,
                "cash": 30000,
                "positions": [],
                "risk_profile": "moderate",
                "max_position_pct": 0.1,
                "max_new_buy_pct": 0.05,
                "min_trade_value": 500,
            },
        },
    )

    assert response.status_code == 202
    detail = client.get(f"/reports/{response.json()['id']}").json()
    assert detail["status"] == "completed"
    assert detail["report"]["position_sizing"]["action"] == "BUY"
    assert "## Position Sizing" in detail["markdown"]


def test_api_rejects_when_date_resolution_fails(tmp_path, monkeypatch) -> None:
    def fail_resolve(ticker, requested_date, data_source):
        raise ValueError("no recent price data")

    monkeypatch.setattr("research_agents.api.app.resolve_analysis_date", fail_resolve)
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post("/reports", json={"ticker": "BAD"})

    assert response.status_code == 400
    assert response.json()["detail"] == "no recent price data"


def test_api_accepts_yfinance_gdelt_sec_source(tmp_path, monkeypatch) -> None:
    from research_agents.reports.models import ResearchReport
    from research_agents.graph.state import AgentTrace, RiskNote, Signal
    from datetime import date

    def fake_run_research(ticker: str, analysis_date: date, data_source: str) -> ResearchReport:
        assert data_source == "yfinance_gdelt_sec"
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
        json={"ticker": "1810.HK", "analysis_date": "2026-05-19", "data_source": "yfinance_gdelt_sec"},
    )

    assert response.status_code == 202
    detail = client.get(f"/reports/{response.json()['id']}").json()
    assert detail["status"] == "completed"


def test_api_lists_reports(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    client.post("/reports", json={"ticker": "AAPL", "analysis_date": "2026-05-17", "data_source": "mock"})
    response = client.get("/reports")

    assert response.status_code == 200
    assert response.json()[0]["ticker"] == "AAPL"


def test_api_records_failed_background_report(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/reports",
        json={"ticker": "UNKNOWN", "analysis_date": "2026-05-17", "data_source": "mock"},
    )

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


def test_api_creates_and_reads_completed_report_batch(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/report-batches",
        json={"tickers": ["AAPL", "NVDA"], "analysis_date": "2026-05-17", "data_source": "mock", "concurrency": 2},
    )

    assert response.status_code == 202
    created = response.json()
    assert created["batch_id"] == created["id"]
    assert created["total"] == 2

    detail = client.get(f"/report-batches/{created['id']}").json()
    assert detail["status"] == "completed"
    assert detail["completed"] == 2
    assert detail["failed"] == 0
    assert {item["ticker"] for item in detail["items"]} == {"AAPL", "NVDA"}
    assert all(item["report_id"] for item in detail["items"])
    assert all(item["decision"] in {"BUY", "HOLD", "SELL"} for item in detail["items"])


def test_api_batch_report_uses_portfolio_context(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/report-batches",
        json={
            "tickers": ["AAPL"],
            "analysis_date": "2026-05-17",
            "data_source": "mock",
            "portfolio_context": {"portfolio_value": 100000, "cash": 30000, "positions": []},
        },
    )

    assert response.status_code == 202
    batch_detail = client.get(f"/report-batches/{response.json()['id']}").json()
    report_id = batch_detail["items"][0]["report_id"]
    report_detail = client.get(f"/reports/{report_id}").json()
    assert report_detail["report"]["position_sizing"]["action"] == "BUY"


def test_api_can_enqueue_batch_without_executing_inline(tmp_path) -> None:
    queue = RecordingQueue()
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"), queue_client=queue)
    client = TestClient(app)

    response = client.post(
        "/report-batches",
        json={"tickers": ["AAPL", "NVDA"], "analysis_date": "2026-05-17", "data_source": "mock"},
    )

    assert response.status_code == 202
    assert queue.batch_ids == [response.json()["id"]]
    detail = client.get(f"/report-batches/{response.json()['id']}").json()
    assert detail["status"] == "queued"
    assert detail["queued"] == 2


def test_api_report_batch_allows_partial_failure(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    response = client.post(
        "/report-batches",
        json={"tickers": ["AAPL", "UNKNOWN"], "analysis_date": "2026-05-17", "data_source": "mock"},
    )

    assert response.status_code == 202
    detail = client.get(f"/report-batches/{response.json()['id']}").json()
    assert detail["status"] == "completed_with_errors"
    assert detail["completed"] == 1
    assert detail["failed"] == 1
    failed_items = [item for item in detail["items"] if item["status"] == "failed"]
    assert "Unsupported mock ticker" in failed_items[0]["error"]


def test_api_streams_report_batch_events(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    created = client.post(
        "/report-batches",
        json={"tickers": ["AAPL"], "analysis_date": "2026-05-17", "data_source": "mock"},
    ).json()

    response = client.get(f"/report-batches/{created['id']}/events")

    assert response.status_code == 200
    assert "event: batch_update" in response.text
    assert '"status": "completed"' in response.text
    assert '"ticker": "AAPL"' in response.text


def test_api_retries_failed_report_batch_items(tmp_path) -> None:
    app = create_app(ReportStore(tmp_path / "reports.sqlite3"))
    client = TestClient(app)

    created = client.post(
        "/report-batches",
        json={"tickers": ["UNKNOWN"], "analysis_date": "2026-05-17", "data_source": "mock"},
    ).json()
    first_detail = client.get(f"/report-batches/{created['id']}").json()
    first_report_id = first_detail["items"][0]["report_id"]

    response = client.post(f"/report-batches/{created['id']}/retry-failed")

    assert response.status_code == 202
    second_detail = client.get(f"/report-batches/{created['id']}").json()
    assert second_detail["status"] == "failed"
    assert second_detail["items"][0]["status"] == "failed"
    assert second_detail["items"][0]["report_id"] != first_report_id
