# Investment Research Agents

`investment-research-agents` is a first-version backend framework for a multi-agent investment research report system. It is not an automated trading system and does not place orders. The goal is to produce a traceable research report from a ticker and analysis date.

## What It Does

The current workflow can run fully offline with mock data, or use real market, news, and filing-derived fundamentals through `yfinance_gdelt_sec`.

Agents:

- `MarketDataAgent`: loads company profile, price history, fundamentals, and benchmark context.
- `NewsSentimentAgent`: summarizes news sentiment from mock, Yahoo Finance, or GDELT data.
- `TechnicalAnalystAgent`: derives simple trend signals from price history.
- `FundamentalAnalystAgent`: scores valuation, profitability, growth, and cash-flow quality.
- `MarketContextAgent`: compares the ticker return against a market benchmark such as `SPY`, `^HSI`, `^TWII`, or `000001.SS`.
- `RiskManagerAgent`: creates a risk level and risk notes.
- `BullDebateAgent`: argues the upside case using structured LLM output.
- `BearDebateAgent`: argues the downside case using structured LLM output.
- `RiskDebateAgent`: argues the risk-control case using structured LLM output.
- `PortfolioManagerAgent`: resolves the debate into a `BUY`, `HOLD`, or `SELL` research stance with confidence.
- `PositionSizingAgent`: optionally converts a research stance into a rule-based position sizing plan when portfolio context is supplied.

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

Run autonomous analysis with only a ticker. The system resolves the latest available trading day and uses `yfinance_gdelt_sec` by default:

```bash
uv run research-agents analyze --ticker 1810.HK
```

Use Yahoo Finance for real company profile, price history, and best-effort news:

```bash
uv run research-agents analyze --ticker AAPL --date 2026-05-17 --data-source yfinance
```

Use Yahoo Finance for market/fundamental data and GDELT for broader news coverage:

```bash
uv run research-agents analyze --ticker 1810.HK --date 2026-05-19 --data-source yfinance_gdelt
```

Use Yahoo Finance plus GDELT plus SEC Company Facts for authoritative US fundamentals. For non-US exchange-suffixed tickers such as `1810.HK`, SEC lookup is skipped and the system falls back to Yahoo Finance fundamentals:

```bash
uv run research-agents analyze --ticker AAPL --data-source yfinance_gdelt_sec
```

Set `SEC_USER_AGENT` in `.env` if you want to identify your app/contact for SEC requests:

```bash
SEC_USER_AGENT="investment-research-agents/0.1 your-email@example.com"
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

Open the minimal web console:

```text
http://127.0.0.1:8000/
```

The console lets you submit a ticker, optionally choose an analysis date and data source, poll the asynchronous report task, and read the generated Markdown report in the browser.

For high-concurrency runs, start Redis and an RQ worker in a separate terminal:

```bash
redis-server
RESEARCH_AGENTS_QUEUE_MODE=rq uv run research-agents-worker
RESEARCH_AGENTS_QUEUE_MODE=rq uv run uvicorn research_agents.api.app:app --reload
```

Without Redis, keep `RESEARCH_AGENTS_QUEUE_MODE=inline`. Inline mode executes jobs in-process and is useful for local demos and tests.

In `rq` mode, a batch is split into per-ticker jobs. The API initially enqueues up to the batch `concurrency` value, and each completed ticker schedules the next queued ticker. Run more workers to increase total throughput while keeping each batch bounded:

```bash
RESEARCH_AGENTS_QUEUE_MODE=rq uv run research-agents-worker
RESEARCH_AGENTS_QUEUE_MODE=rq uv run research-agents-worker
RESEARCH_AGENTS_QUEUE_MODE=rq uv run research-agents-worker
```

Use PostgreSQL for multi-worker state storage:

```bash
export RESEARCH_AGENTS_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/research_agents"
RESEARCH_AGENTS_QUEUE_MODE=rq uv run uvicorn research_agents.api.app:app --reload
```

Use Redis-backed cache and global rate limiting when running multiple workers:

```bash
export RESEARCH_AGENTS_CACHE_MODE=redis
export RESEARCH_AGENTS_RATE_LIMIT_MODE=redis
export YFINANCE_RATE_LIMIT_PER_MINUTE=120
export GDELT_RATE_LIMIT_PER_MINUTE=60
export SEC_RATE_LIMIT_PER_MINUTE=60
export LLM_RATE_LIMIT_PER_MINUTE=60
```

Create and persist a report:

```bash
curl -X POST http://127.0.0.1:8000/reports \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"AAPL"}'
```

The create endpoint returns `202 Accepted` with a queued task id. In `rq` mode the report is generated by the worker; in `inline` mode it runs immediately in the API process.

Create a report with portfolio-aware position sizing:

```bash
curl -X POST http://127.0.0.1:8000/reports \
  -H 'Content-Type: application/json' \
  -d '{
    "ticker":"AAPL",
    "portfolio_context":{
      "portfolio_value":100000,
      "cash":30000,
      "positions":[{"ticker":"MSFT","shares":10,"market_value":4500}],
      "risk_profile":"moderate",
      "max_position_pct":0.10,
      "max_new_buy_pct":0.05,
      "min_trade_value":500
    }
  }'
```

Position sizing is deterministic and constraint-based. The system will not invent trade size when portfolio context is missing, and generated plans are research planning outputs, not trading instructions.

Read reports:

```bash
curl http://127.0.0.1:8000/reports/1
curl http://127.0.0.1:8000/reports
```

Retry a failed report:

```bash
curl -X POST http://127.0.0.1:8000/reports/1/retry
```

Create a batch report job for many tickers:

```bash
curl -X POST http://127.0.0.1:8000/report-batches \
  -H 'Content-Type: application/json' \
  -d '{"tickers":["AAPL","NVDA","2357.TW"],"concurrency":3}'
```

Read batch progress and item results:

```bash
curl http://127.0.0.1:8000/report-batches/1
```

Stream batch progress with Server-Sent Events:

```bash
curl -N http://127.0.0.1:8000/report-batches/1/events
```

Retry only failed tickers in a batch:

```bash
curl -X POST http://127.0.0.1:8000/report-batches/1/retry-failed
```

Batch jobs default to small concurrency (`3`, max `5`) to reduce external data and LLM rate-limit failures. A failed ticker does not stop the rest of the batch.

Reports are stored in SQLite at `data/research_reports.sqlite3` by default. Override with `RESEARCH_AGENTS_DB` for another SQLite path or `RESEARCH_AGENTS_DATABASE_URL` for PostgreSQL.

## Python API

```python
from datetime import date
from research_agents import run_research

report = run_research("AAPL", date(2026, 5, 17), data_source="mock")
print(report.decision)
```

Portfolio-aware sizing:

```python
from datetime import date
from research_agents import PortfolioContext, run_research_with_portfolio

context = PortfolioContext(portfolio_value=100_000, cash=30_000, positions=[])
report = run_research_with_portfolio("AAPL", date(2026, 5, 17), context, data_source="mock")
print(report.position_sizing)
```

## Roadmap

- Add more primary data providers such as company IR filings, macro rates, sector ETFs, and analyst estimates.
- Add evaluation datasets to compare report stances against forward returns and risk-adjusted outcomes.
- Add backtesting and model/prompt evaluation sets.
- Add scheduled jobs and a web dashboard.
