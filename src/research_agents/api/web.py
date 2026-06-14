from __future__ import annotations


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Investment Research Agents</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #697386;
      --line: #d8dee8;
      --accent: #0f766e;
      --accent-dark: #0b5f59;
      --danger: #b42318;
      --ok: #0f7a45;
      --warn: #9a6700;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font: 15px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      background: #17202a;
      color: #fff;
      padding: 22px 28px;
      border-bottom: 4px solid var(--accent);
    }
    header h1 {
      margin: 0 0 4px;
      font-size: 24px;
      font-weight: 720;
      letter-spacing: 0;
    }
    header p { margin: 0; color: #cbd5e1; }
    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 22px auto 40px;
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 18px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .panel { padding: 18px; }
    h2 {
      margin: 0 0 14px;
      font-size: 17px;
      letter-spacing: 0;
    }
    label {
      display: block;
      margin: 12px 0 6px;
      color: #344054;
      font-weight: 650;
      font-size: 13px;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid #c7d0dd;
      border-radius: 6px;
      padding: 10px 11px;
      color: var(--ink);
      background: #fff;
      font: inherit;
    }
    textarea { min-height: 96px; resize: vertical; }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    button {
      width: 100%;
      margin-top: 16px;
      border: 0;
      border-radius: 6px;
      padding: 11px 14px;
      background: var(--accent);
      color: #fff;
      font-weight: 720;
      cursor: pointer;
    }
    button:hover { background: var(--accent-dark); }
    button:disabled { cursor: not-allowed; opacity: .65; }
    .hint {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }
    .status {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
    }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      padding: 3px 10px;
      background: #eef2f7;
      color: #344054;
      font-weight: 700;
      font-size: 12px;
      text-transform: uppercase;
    }
    .pill.completed { background: #dcfce7; color: var(--ok); }
    .pill.failed { background: #fee4e2; color: var(--danger); }
    .pill.running, .pill.queued { background: #fef3c7; color: var(--warn); }
    .report {
      padding: 18px 22px 28px;
      min-height: 560px;
      overflow-wrap: anywhere;
    }
    .empty {
      color: var(--muted);
      padding: 40px 0;
      text-align: center;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fafbfc;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
    }
    .metric strong {
      display: block;
      margin-top: 3px;
      font-size: 18px;
    }
    .markdown h1, .markdown h2, .markdown h3 {
      margin: 22px 0 8px;
      line-height: 1.25;
      letter-spacing: 0;
    }
    .markdown h1 { font-size: 24px; }
    .markdown h2 { font-size: 19px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
    .markdown h3 { font-size: 16px; }
    .markdown p { margin: 8px 0; }
    .markdown ul { margin: 8px 0 12px 21px; padding: 0; }
    .markdown li { margin: 4px 0; }
    .error {
      border: 1px solid #fda29b;
      border-radius: 8px;
      padding: 12px;
      color: var(--danger);
      background: #fff5f5;
      white-space: pre-wrap;
    }
    @media (max-width: 820px) {
      main { grid-template-columns: 1fr; width: min(100vw - 22px, 720px); }
      .summary-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Investment Research Agents</h1>
    <p>Multi-agent research report console</p>
  </header>
  <main>
    <section class="panel">
      <h2>Create Report</h2>
      <form id="report-form">
        <label for="ticker">Ticker</label>
        <input id="ticker" name="ticker" value="AAPL" autocomplete="off" required maxlength="16">

        <div class="row">
          <div>
            <label for="analysis-date">Analysis Date</label>
            <input id="analysis-date" name="analysis_date" type="date">
          </div>
          <div>
            <label for="data-source">Data Source</label>
            <select id="data-source" name="data_source">
              <option value="yfinance_gdelt_sec">yfinance_gdelt_sec</option>
              <option value="yfinance_gdelt">yfinance_gdelt</option>
              <option value="yfinance">yfinance</option>
              <option value="mock">mock</option>
            </select>
          </div>
        </div>

        <label for="portfolio-json">Portfolio Context JSON</label>
        <textarea id="portfolio-json" spellcheck="false" placeholder='{"portfolio_value":100000,"cash":30000,"positions":[]}'></textarea>

        <button id="submit-button" type="submit">Run Analysis</button>
        <p class="hint">Leave the date empty to resolve the latest available trading day. Use mock for fast local demos.</p>
      </form>
    </section>

    <section>
      <div class="status">
        <span id="status-pill" class="pill">idle</span>
        <span id="status-text">No report created yet.</span>
      </div>
      <div id="report" class="report">
        <div class="empty">Submit a ticker to generate a research report.</div>
      </div>
    </section>
  </main>

  <script>
    const form = document.querySelector("#report-form");
    const button = document.querySelector("#submit-button");
    const statusPill = document.querySelector("#status-pill");
    const statusText = document.querySelector("#status-text");
    const reportEl = document.querySelector("#report");
    let pollHandle = null;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearPoll();
      setBusy(true);
      setStatus("queued", "Creating report task...");
      reportEl.innerHTML = '<div class="empty">Waiting for the agent workflow to finish.</div>';

      try {
        const payload = buildPayload();
        const response = await fetch("/reports", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const body = await response.json();
        if (!response.ok) throw new Error(body.detail || "Report creation failed.");
        renderSummary(body);
        await pollReport(body.id);
      } catch (error) {
        setStatus("failed", "Request failed.");
        reportEl.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
        setBusy(false);
      }
    });

    function buildPayload() {
      const ticker = document.querySelector("#ticker").value.trim();
      const analysisDate = document.querySelector("#analysis-date").value;
      const dataSource = document.querySelector("#data-source").value;
      const portfolioText = document.querySelector("#portfolio-json").value.trim();
      const payload = { ticker, data_source: dataSource };
      if (analysisDate) payload.analysis_date = analysisDate;
      if (portfolioText) payload.portfolio_context = JSON.parse(portfolioText);
      return payload;
    }

    async function pollReport(reportId) {
      const terminalStatuses = new Set(["completed", "failed"]);
      const load = async () => {
        const response = await fetch(`/reports/${reportId}`);
        const detail = await response.json();
        if (!response.ok) throw new Error(detail.detail || "Failed to read report.");
        renderSummary(detail);
        if (terminalStatuses.has(detail.status)) {
          clearPoll();
          setBusy(false);
          if (detail.status === "completed") renderReport(detail);
          if (detail.status === "failed") renderError(detail.error || "Report failed.");
        }
      };
      await load();
      pollHandle = window.setInterval(load, 1500);
    }

    function renderSummary(detail) {
      setStatus(detail.status, `${detail.ticker} · ${detail.analysis_date} · ${detail.data_source}`);
      if (detail.status !== "completed") return;
      const confidence = detail.confidence == null ? "N/A" : `${Math.round(detail.confidence * 100)}%`;
      reportEl.innerHTML = `
        <div class="summary-grid">
          <div class="metric"><span>Decision</span><strong>${escapeHtml(detail.decision || "N/A")}</strong></div>
          <div class="metric"><span>Confidence</span><strong>${confidence}</strong></div>
          <div class="metric"><span>Report ID</span><strong>#${detail.id}</strong></div>
        </div>
        <div class="empty">Rendering report...</div>
      `;
    }

    function renderReport(detail) {
      const markdown = detail.markdown || "No Markdown report was returned.";
      const confidence = detail.confidence == null ? "N/A" : `${Math.round(detail.confidence * 100)}%`;
      reportEl.innerHTML = `
        <div class="summary-grid">
          <div class="metric"><span>Decision</span><strong>${escapeHtml(detail.decision || "N/A")}</strong></div>
          <div class="metric"><span>Confidence</span><strong>${confidence}</strong></div>
          <div class="metric"><span>Report ID</span><strong>#${detail.id}</strong></div>
        </div>
        <div class="markdown">${renderMarkdown(markdown)}</div>
      `;
    }

    function renderError(message) {
      reportEl.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
    }

    function setStatus(status, text) {
      statusPill.className = `pill ${status}`;
      statusPill.textContent = status;
      statusText.textContent = text;
    }

    function setBusy(isBusy) {
      button.disabled = isBusy;
      button.textContent = isBusy ? "Running..." : "Run Analysis";
    }

    function clearPoll() {
      if (pollHandle) window.clearInterval(pollHandle);
      pollHandle = null;
    }

    function renderMarkdown(markdown) {
      const lines = escapeHtml(markdown).split("\\n");
      const html = [];
      let inList = false;
      for (const line of lines) {
        if (line.startsWith("### ")) {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<h3>${line.slice(4)}</h3>`);
        } else if (line.startsWith("## ")) {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<h2>${line.slice(3)}</h2>`);
        } else if (line.startsWith("# ")) {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<h1>${line.slice(2)}</h1>`);
        } else if (line.startsWith("- ")) {
          if (!inList) { html.push("<ul>"); inList = true; }
          html.push(`<li>${line.slice(2)}</li>`);
        } else if (line.trim() === "") {
          if (inList) { html.push("</ul>"); inList = false; }
        } else {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<p>${line}</p>`);
        }
      }
      if (inList) html.push("</ul>");
      return html.join("");
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  </script>
</body>
</html>
"""
