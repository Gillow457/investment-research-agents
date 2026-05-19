# Investment Research Agents

`investment-research-agents` is a first-version backend framework for a multi-agent investment research report system. It is not an automated trading system and does not place orders. The goal is to produce a traceable research report from a ticker and analysis date.

## What It Does

The current workflow uses mock market and news data so the architecture is runnable and testable before integrating real data vendors.

Agents:

- `MarketDataAgent`: loads company profile and price history.
- `NewsSentimentAgent`: summarizes mock news sentiment.
- `TechnicalAnalystAgent`: derives simple trend signals from price history.
- `RiskManagerAgent`: creates a risk level and risk notes.
- `BullDebateAgent`: argues the upside case using structured LLM output.
- `BearDebateAgent`: argues the downside case using structured LLM output.
- `RiskDebateAgent`: argues the risk-control case using structured LLM output.
- `PortfolioManagerAgent`: resolves the debate into a `BUY`, `HOLD`, or `SELL` research stance with confidence.

The workflow is orchestrated with LangGraph and returns a structured `ResearchReport` that can be rendered as Markdown. When `OPENAI_API_KEY` is set, the debate agents and portfolio manager request JSON output from the OpenAI-compatible endpoint and validate it with Pydantic schemas. Without a key, the project uses deterministic structured stub outputs for stable tests and demos.

## Install

```bash
uv sync
```

Optional model configuration:

```bash
cp .env.example .env
```

If `OPENAI_API_KEY` is not set, the system uses a deterministic stub LLM so tests and demos remain stable.

## Run

```bash
uv run research-agents analyze --ticker AAPL --date 2026-05-17
```

Use Yahoo Finance for real company profile, price history, and best-effort news:

```bash
uv run research-agents analyze --ticker AAPL --date 2026-05-17 --data-source yfinance
```

Use Yahoo Finance for market/fundamental data and GDELT for broader news coverage:

```bash
uv run research-agents analyze --ticker 1810.HK --date 2026-05-19 --data-source yfinance_gdelt
```

Save a report:

```bash
uv run research-agents analyze --ticker AAPL --date 2026-05-17 --output reports/AAPL_2026-05-17.md
```

## API Server

Start the FastAPI server:

```bash
uv run uvicorn research_agents.api.app:app --reload
```

Create and persist a report:

```bash
curl -X POST http://127.0.0.1:8000/reports \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"AAPL","analysis_date":"2026-05-17","data_source":"mock"}'
```

The create endpoint returns `202 Accepted` with a queued task id. The report is generated in a background task.

Read reports:

```bash
curl http://127.0.0.1:8000/reports/1
curl http://127.0.0.1:8000/reports
```

Retry a failed report:

```bash
curl -X POST http://127.0.0.1:8000/reports/1/retry
```

Reports are stored in SQLite at `data/research_reports.sqlite3` by default. Override with `RESEARCH_AGENTS_DB`.

## Python API

```python
from datetime import date
from research_agents import run_research

report = run_research("AAPL", date(2026, 5, 17), data_source="mock")
print(report.decision)
```

## Roadmap

- Replace mock providers with real market, filing, and news providers.
- Add bullish and bearish researcher debate rounds.
- Add backtesting and model/prompt evaluation sets.
- Add scheduled jobs and a web dashboard.
