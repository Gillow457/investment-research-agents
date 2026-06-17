from __future__ import annotations


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>多智能体投研控制台 | Investment Research Agents</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #687385;
      --paper: #f4f1ea;
      --surface: #fffdf8;
      --surface-strong: #f8f4eb;
      --line: #d7d0c3;
      --line-strong: #b8ad9b;
      --charcoal: #20242a;
      --charcoal-2: #2f3640;
      --teal: #0f766e;
      --teal-dark: #0b5f59;
      --amber: #b7791f;
      --red: #b42318;
      --green: #0f7a45;
      --blue: #2f5f9f;
      --shadow: 0 18px 60px rgba(28, 31, 35, .16);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(90deg, rgba(32, 36, 42, .05) 1px, transparent 1px),
        linear-gradient(180deg, rgba(32, 36, 42, .05) 1px, transparent 1px),
        var(--paper);
      background-size: 28px 28px;
      color: var(--ink);
      font: 14px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    button, input, select, textarea {
      font: inherit;
    }

    button {
      border: 0;
      cursor: pointer;
    }

    button:disabled {
      cursor: not-allowed;
      opacity: .58;
    }

    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    .topbar {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 18px;
      align-items: center;
      padding: 18px 24px;
      background: rgba(255, 253, 248, .92);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 20;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .mark {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      background: var(--charcoal);
      color: #f8f4eb;
      display: grid;
      place-items: center;
      font-weight: 800;
      box-shadow: inset 0 -5px 0 rgba(15, 118, 110, .45);
      flex: 0 0 auto;
    }

    .brand h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.12;
      letter-spacing: 0;
    }

    .brand p {
      margin: 2px 0 0;
      color: var(--muted);
    }

    .top-actions {
      display: grid;
      grid-template-columns: auto auto auto;
      gap: 10px;
      align-items: center;
    }

    .server-pill, .mode-pill {
      min-height: 34px;
      padding: 7px 11px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--muted);
      font-weight: 700;
      white-space: nowrap;
    }

    .server-pill strong {
      color: var(--green);
    }

    .workspace {
      width: min(1440px, calc(100vw - 28px));
      margin: 18px auto 34px;
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr) 310px;
      gap: 16px;
      align-items: start;
    }

    .panel, .workbench, .rail {
      border: 1px solid var(--line);
      background: rgba(255, 253, 248, .95);
      border-radius: 12px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel {
      position: sticky;
      top: 88px;
    }

    .panel-head, .rail-head, .workbench-head {
      padding: 16px;
      border-bottom: 1px solid var(--line);
      background: var(--surface-strong);
    }

    .panel-head h2, .rail-head h2, .workbench-head h2 {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }

    .panel-body {
      padding: 16px;
    }

    .segmented {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px;
      padding: 4px;
      background: #ece5d8;
      border: 1px solid var(--line);
      border-radius: 10px;
    }

    .segment {
      min-height: 36px;
      border-radius: 7px;
      background: transparent;
      color: #4a5361;
      font-weight: 760;
      transition: background .18s ease, color .18s ease, transform .18s ease;
    }

    .segment.active {
      background: var(--charcoal);
      color: #fffdf8;
      transform: translateY(-1px);
    }

    .form-grid {
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }

    .field-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    label {
      display: grid;
      gap: 6px;
      color: #374151;
      font-size: 12px;
      font-weight: 780;
    }

    input, select, textarea {
      width: 100%;
      min-height: 40px;
      border: 1px solid #c8bead;
      border-radius: 8px;
      background: #fffdf8;
      color: var(--ink);
      padding: 9px 10px;
      outline: none;
      transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
    }

    input:focus, select:focus, textarea:focus {
      border-color: var(--teal);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, .16);
      background: #ffffff;
    }

    textarea {
      min-height: 96px;
      resize: vertical;
    }

    .portfolio-box {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: #fbf8f1;
    }

    .toggle-line {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 10px;
    }

    .toggle-line strong {
      font-size: 13px;
    }

    .switch {
      width: 48px;
      height: 26px;
      border-radius: 999px;
      background: #c8bead;
      padding: 3px;
      transition: background .18s ease;
    }

    .switch span {
      display: block;
      width: 20px;
      height: 20px;
      border-radius: 999px;
      background: #fff;
      transition: transform .18s ease;
    }

    .switch.active {
      background: var(--teal);
    }

    .switch.active span {
      transform: translateX(22px);
    }

    .portfolio-fields {
      display: none;
      gap: 10px;
    }

    .portfolio-fields.active {
      display: grid;
    }

    .primary-button {
      min-height: 44px;
      width: 100%;
      border-radius: 9px;
      background: var(--teal);
      color: #fff;
      font-weight: 820;
      transition: transform .18s ease, background .18s ease, box-shadow .18s ease;
      box-shadow: 0 12px 26px rgba(15, 118, 110, .22);
    }

    .primary-button:hover {
      background: var(--teal-dark);
      transform: translateY(-1px);
    }

    .secondary-button {
      min-height: 38px;
      border-radius: 8px;
      background: #ffffff;
      color: var(--charcoal);
      border: 1px solid var(--line);
      font-weight: 760;
    }

    .microcopy {
      color: var(--muted);
      font-size: 12px;
      margin: 0;
    }

    .status-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      border-bottom: 1px solid var(--line);
      background: var(--charcoal);
      color: #f8f4eb;
    }

    .status-cell {
      padding: 14px 16px;
      border-right: 1px solid rgba(255, 255, 255, .12);
      min-width: 0;
    }

    .status-cell:last-child {
      border-right: 0;
    }

    .status-cell span {
      display: block;
      color: #bfc7cf;
      font-size: 12px;
    }

    .status-cell strong {
      display: block;
      margin-top: 4px;
      font-size: 20px;
      line-height: 1.1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .workbench-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      border-radius: 999px;
      padding: 4px 10px;
      background: #ebe3d5;
      color: #4b5563;
      font-size: 12px;
      font-weight: 820;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .pill.completed { background: #dcfce7; color: var(--green); }
    .pill.failed { background: #fee4e2; color: var(--red); }
    .pill.running, .pill.queued { background: #fef3c7; color: #986300; }
    .pill.idle { background: #e8eef7; color: var(--blue); }
    .pill.error { background: #fee4e2; color: var(--red); }

    .canvas-area {
      min-height: 620px;
      padding: 16px;
      background:
        linear-gradient(180deg, rgba(255, 253, 248, .86), rgba(246, 241, 231, .94)),
        #fffdf8;
    }

    .empty-state {
      min-height: 520px;
      display: grid;
      place-items: center;
      text-align: center;
      color: var(--muted);
    }

    .empty-state-inner {
      max-width: 520px;
      display: grid;
      gap: 14px;
      justify-items: center;
    }

    .orbit {
      width: min(360px, 78vw);
      aspect-ratio: 1;
      border: 1px solid var(--line);
      border-radius: 50%;
      position: relative;
      background:
        conic-gradient(from 15deg, rgba(15, 118, 110, .18), rgba(183, 121, 31, .16), rgba(47, 95, 159, .16), rgba(15, 118, 110, .18));
      box-shadow: inset 0 0 0 28px rgba(255, 253, 248, .7);
    }

    .orbit::before, .orbit::after {
      content: "";
      position: absolute;
      inset: 21%;
      border-radius: 50%;
      border: 1px dashed rgba(32, 36, 42, .24);
    }

    .orbit::after {
      inset: 39%;
      background: var(--charcoal);
      border: 0;
      box-shadow: 0 14px 40px rgba(32, 36, 42, .28);
    }

    .node {
      position: absolute;
      width: 78px;
      min-height: 34px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: #fffdf8;
      display: grid;
      place-items: center;
      font-size: 11px;
      font-weight: 820;
      color: var(--charcoal);
      box-shadow: 0 8px 20px rgba(32, 36, 42, .12);
    }

    .node:nth-child(1) { left: 50%; top: 2%; transform: translateX(-50%); }
    .node:nth-child(2) { right: 2%; top: 27%; }
    .node:nth-child(3) { right: 10%; bottom: 13%; }
    .node:nth-child(4) { left: 10%; bottom: 13%; }
    .node:nth-child(5) { left: 2%; top: 27%; }

    .report-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 280px;
      gap: 14px;
      align-items: start;
    }

    .report-paper, .inspector, .batch-table-wrap {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fffdf8;
      overflow: hidden;
    }

    .report-paper {
      padding: 20px 24px 26px;
    }

    .inspector {
      padding: 14px;
      display: grid;
      gap: 12px;
      position: sticky;
      top: 88px;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .metric {
      min-height: 72px;
      border: 1px solid var(--line);
      border-radius: 9px;
      background: #fbf8f1;
      padding: 10px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 5px;
    }

    .metric strong {
      display: block;
      font-size: 20px;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }

    .agent-stack {
      display: grid;
      gap: 8px;
      padding: 14px;
    }

    .agent-item {
      border: 1px solid var(--line);
      border-radius: 9px;
      background: #fffdf8;
      padding: 10px;
      transition: transform .18s ease, border-color .18s ease;
    }

    .agent-item.active {
      border-color: var(--teal);
      transform: translateX(2px);
    }

    .agent-item strong {
      display: block;
      font-size: 12px;
      margin-bottom: 4px;
    }

    .agent-item span {
      color: var(--muted);
      font-size: 12px;
    }

    .markdown h1, .markdown h2, .markdown h3 {
      margin: 22px 0 9px;
      line-height: 1.24;
      letter-spacing: 0;
    }

    .markdown h1 { font-size: 24px; margin-top: 0; }
    .markdown h2 { font-size: 18px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
    .markdown h3 { font-size: 15px; }
    .markdown p { margin: 8px 0; }
    .markdown ul { margin: 9px 0 14px 20px; padding: 0; }
    .markdown li { margin: 4px 0; }
    .markdown code {
      background: #eee6d8;
      border-radius: 5px;
      padding: 1px 5px;
    }

    .rail {
      position: sticky;
      top: 88px;
    }

    .rail-list {
      padding: 12px;
      display: grid;
      gap: 10px;
    }

    .history-item {
      border: 1px solid var(--line);
      background: #fffdf8;
      border-radius: 9px;
      padding: 10px;
      text-align: left;
      color: var(--ink);
      display: grid;
      gap: 4px;
      transition: border-color .18s ease, transform .18s ease;
    }

    .history-item:hover {
      border-color: var(--teal);
      transform: translateY(-1px);
    }

    .history-item strong {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
    }

    .history-item span {
      color: var(--muted);
      font-size: 12px;
    }

    .batch-table-wrap {
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 700px;
    }

    th, td {
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }

    th {
      background: #f8f4eb;
      color: #4b5563;
      font-size: 12px;
      text-transform: uppercase;
    }

    td {
      color: var(--ink);
    }

    .error-box {
      border: 1px solid #f3aaa4;
      background: #fff5f4;
      color: var(--red);
      border-radius: 9px;
      padding: 12px;
      white-space: pre-wrap;
    }

    .hidden { display: none !important; }

    @media (max-width: 1180px) {
      .workspace {
        grid-template-columns: 340px minmax(0, 1fr);
      }
      .rail {
        grid-column: 1 / -1;
        position: static;
      }
      .rail-list {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
    }

    @media (max-width: 860px) {
      .topbar {
        grid-template-columns: 1fr;
        padding: 14px;
      }
      .top-actions {
        grid-template-columns: 1fr 1fr;
      }
      .workspace {
        width: min(100vw - 18px, 720px);
        grid-template-columns: 1fr;
      }
      .panel, .rail, .inspector {
        position: static;
      }
      .status-strip {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .report-grid {
        grid-template-columns: 1fr;
      }
      .rail-list {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 520px) {
      .field-row, .metric-grid {
        grid-template-columns: 1fr;
      }
      .top-actions {
        grid-template-columns: 1fr;
      }
      .canvas-area {
        padding: 10px;
      }
      .report-paper {
        padding: 16px;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: .001ms !important;
        transition-duration: .001ms !important;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="mark">IR</div>
        <div>
          <h1>多智能体投研控制台</h1>
          <p>投研工作流、批量监控与组合仓位规划</p>
        </div>
      </div>
      <div class="top-actions">
        <div id="server-status" class="server-pill"><strong>在线</strong> API</div>
        <div id="active-mode-pill" class="mode-pill">单票报告</div>
        <button id="refresh-history" class="secondary-button" type="button">刷新</button>
      </div>
    </header>

    <main class="workspace">
      <aside class="panel">
        <div class="panel-head">
          <h2>任务控制台</h2>
        </div>
        <div class="panel-body">
          <div class="segmented" role="tablist" aria-label="报告模式">
            <button id="single-mode" class="segment active" type="button">单票</button>
            <button id="batch-mode" class="segment" type="button">批量</button>
          </div>

          <form id="report-form" class="form-grid">
            <label>
              股票代码
              <input id="ticker" name="ticker" value="AAPL" autocomplete="off" required maxlength="16">
            </label>

            <label id="batch-tickers-field" class="hidden">
              股票代码列表
              <textarea id="batch-tickers" spellcheck="false">AAPL
MSFT
NVDA</textarea>
            </label>

            <div class="field-row">
              <label>
                分析日期
                <input id="analysis-date" name="analysis_date" type="date">
              </label>
              <label>
                数据源
                <select id="data-source" name="data_source">
                  <option value="yfinance_gdelt_sec">yfinance_gdelt_sec</option>
                  <option value="yfinance_gdelt">yfinance_gdelt</option>
                  <option value="yfinance">yfinance</option>
                  <option value="mock">mock</option>
                </select>
              </label>
            </div>

            <label id="batch-concurrency-field" class="hidden">
              批量并发数
              <input id="batch-concurrency" type="number" min="1" max="5" value="3">
            </label>

            <div class="portfolio-box">
              <div class="toggle-line">
                <strong>组合仓位规划</strong>
                <button id="portfolio-toggle" class="switch" type="button" aria-pressed="false"><span></span></button>
              </div>
              <div id="portfolio-fields" class="portfolio-fields">
                <div class="field-row">
                  <label>
                    总资产
                    <input id="portfolio-value" type="number" min="0" step="100" value="100000">
                  </label>
                  <label>
                    可用现金
                    <input id="cash" type="number" min="0" step="100" value="30000">
                  </label>
                </div>
                <div class="field-row">
                  <label>
                    风险偏好
                    <select id="risk-profile">
                      <option value="moderate">稳健</option>
                      <option value="conservative">保守</option>
                      <option value="aggressive">进取</option>
                    </select>
                  </label>
                  <label>
                    当前持仓市值
                    <input id="current-position" type="number" min="0" step="100" value="0">
                  </label>
                </div>
              </div>
              <p class="microcopy">仓位计算基于规则约束，仅用于研究规划，不执行交易。</p>
            </div>

            <button id="submit-button" class="primary-button" type="submit">开始分析</button>
          </form>
        </div>
      </aside>

      <section class="workbench">
        <div class="status-strip">
          <div class="status-cell"><span>状态</span><strong id="metric-status">待命</strong></div>
          <div class="status-cell"><span>决策</span><strong id="metric-decision">-</strong></div>
          <div class="status-cell"><span>置信度</span><strong id="metric-confidence">-</strong></div>
          <div class="status-cell"><span>任务</span><strong id="metric-task">-</strong></div>
        </div>
        <div class="workbench-head">
          <h2 id="workspace-title">智能体工作台</h2>
          <span id="status-pill" class="pill idle">待命</span>
        </div>
        <div id="canvas-area" class="canvas-area">
          <div class="empty-state">
            <div class="empty-state-inner">
              <div class="orbit" aria-hidden="true">
                <div class="node">行情</div>
                <div class="node">新闻</div>
                <div class="node">技术</div>
                <div class="node">风险</div>
                <div class="node">组合</div>
              </div>
              <p>提交股票代码或批量任务后，投研工作流会在这里展开。</p>
            </div>
          </div>
        </div>
      </section>

      <aside class="rail">
        <div class="rail-head">
          <h2>最近报告</h2>
        </div>
        <div id="history-list" class="rail-list">
          <div class="history-item"><span>暂无已加载报告。</span></div>
        </div>
      </aside>
    </main>
  </div>

  <script>
    const state = {
      mode: "single",
      pollHandle: null,
      eventSource: null,
      portfolioEnabled: false
    };

    const els = {
      form: document.querySelector("#report-form"),
      singleMode: document.querySelector("#single-mode"),
      batchMode: document.querySelector("#batch-mode"),
      modePill: document.querySelector("#active-mode-pill"),
      ticker: document.querySelector("#ticker"),
      batchTickersField: document.querySelector("#batch-tickers-field"),
      batchTickers: document.querySelector("#batch-tickers"),
      batchConcurrencyField: document.querySelector("#batch-concurrency-field"),
      batchConcurrency: document.querySelector("#batch-concurrency"),
      analysisDate: document.querySelector("#analysis-date"),
      dataSource: document.querySelector("#data-source"),
      portfolioToggle: document.querySelector("#portfolio-toggle"),
      portfolioFields: document.querySelector("#portfolio-fields"),
      portfolioValue: document.querySelector("#portfolio-value"),
      cash: document.querySelector("#cash"),
      riskProfile: document.querySelector("#risk-profile"),
      currentPosition: document.querySelector("#current-position"),
      submitButton: document.querySelector("#submit-button"),
      statusPill: document.querySelector("#status-pill"),
      canvas: document.querySelector("#canvas-area"),
      workspaceTitle: document.querySelector("#workspace-title"),
      metricStatus: document.querySelector("#metric-status"),
      metricDecision: document.querySelector("#metric-decision"),
      metricConfidence: document.querySelector("#metric-confidence"),
      metricTask: document.querySelector("#metric-task"),
      history: document.querySelector("#history-list"),
      refreshHistory: document.querySelector("#refresh-history"),
      serverStatus: document.querySelector("#server-status")
    };

    els.singleMode.addEventListener("click", () => setMode("single"));
    els.batchMode.addEventListener("click", () => setMode("batch"));
    els.portfolioToggle.addEventListener("click", togglePortfolio);
    els.refreshHistory.addEventListener("click", loadHistory);
    els.form.addEventListener("submit", submitCommand);

    loadHistory();
    checkHealth();

    function setMode(mode) {
      state.mode = mode;
      els.singleMode.classList.toggle("active", mode === "single");
      els.batchMode.classList.toggle("active", mode === "batch");
      els.batchTickersField.classList.toggle("hidden", mode !== "batch");
      els.batchConcurrencyField.classList.toggle("hidden", mode !== "batch");
      els.ticker.closest("label").classList.toggle("hidden", mode !== "single");
      els.modePill.textContent = mode === "single" ? "单票报告" : "批量监控";
      els.submitButton.textContent = mode === "single" ? "开始分析" : "启动批量任务";
      resetMetrics();
    }

    function togglePortfolio() {
      state.portfolioEnabled = !state.portfolioEnabled;
      els.portfolioToggle.classList.toggle("active", state.portfolioEnabled);
      els.portfolioToggle.setAttribute("aria-pressed", String(state.portfolioEnabled));
      els.portfolioFields.classList.toggle("active", state.portfolioEnabled);
    }

    async function submitCommand(event) {
      event.preventDefault();
      stopLiveUpdates();
      setBusy(true);
      try {
        if (state.mode === "single") {
          await createReport();
        } else {
          await createBatch();
        }
      } catch (error) {
        renderError(error.message);
        setBusy(false);
      }
    }

    async function createReport() {
      setStatus("queued", "创建报告任务");
      renderLoading("报告任务已入队", "正在等待智能体工作流返回首个状态。");
      const payload = buildSinglePayload();
      const response = await fetch("/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "报告任务创建失败。");
      renderReportShell(body);
      await pollReport(body.id);
    }

    async function createBatch() {
      setStatus("queued", "创建批量任务");
      renderLoading("批量任务已入队", "正在通过事件流同步每只股票的处理进度。");
      const payload = buildBatchPayload();
      const response = await fetch("/report-batches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "批量任务创建失败。");
      renderBatch(body);
      streamBatch(body.id);
    }

    function buildSinglePayload() {
      const payload = {
        ticker: els.ticker.value.trim(),
        data_source: els.dataSource.value
      };
      if (els.analysisDate.value) payload.analysis_date = els.analysisDate.value;
      const portfolio = buildPortfolioContext(payload.ticker);
      if (portfolio) payload.portfolio_context = portfolio;
      return payload;
    }

    function buildBatchPayload() {
      const tickers = els.batchTickers.value
        .split(/[\\n,\\s]+/)
        .map((ticker) => ticker.trim())
        .filter(Boolean);
      const payload = {
        tickers,
        data_source: els.dataSource.value,
        concurrency: Number(els.batchConcurrency.value || 3)
      };
      if (els.analysisDate.value) payload.analysis_date = els.analysisDate.value;
      const portfolio = buildPortfolioContext(tickers[0] || "AAPL");
      if (portfolio) payload.portfolio_context = portfolio;
      return payload;
    }

    function buildPortfolioContext(activeTicker) {
      if (!state.portfolioEnabled) return null;
      const positionValue = Number(els.currentPosition.value || 0);
      const positions = positionValue > 0 ? [{
        ticker: activeTicker,
        shares: 0,
        market_value: positionValue
      }] : [];
      return {
        portfolio_value: Number(els.portfolioValue.value || 0),
        cash: Number(els.cash.value || 0),
        positions,
        risk_profile: els.riskProfile.value,
        max_position_pct: 0.10,
        max_new_buy_pct: 0.05,
        min_trade_value: 500
      };
    }

    async function pollReport(reportId) {
      const terminal = new Set(["completed", "failed"]);
      const load = async () => {
        const response = await fetch(`/reports/${reportId}`);
        const detail = await response.json();
        if (!response.ok) throw new Error(detail.detail || "读取报告失败。");
        renderReportShell(detail);
        if (terminal.has(detail.status)) {
          stopLiveUpdates();
          setBusy(false);
          if (detail.status === "completed") {
            renderReport(detail);
            loadHistory();
          } else {
            renderError(detail.error || "报告生成失败。");
          }
        }
      };
      await load();
      state.pollHandle = window.setInterval(load, 1400);
    }

    function streamBatch(batchId) {
      if (state.eventSource) state.eventSource.close();
      state.eventSource = new EventSource(`/report-batches/${batchId}/events`);
      state.eventSource.addEventListener("batch_update", (event) => {
        const detail = JSON.parse(event.data);
        renderBatch(detail);
        if (["completed", "completed_with_errors", "failed"].includes(detail.status)) {
          stopLiveUpdates();
          setBusy(false);
          loadHistory();
        }
      });
      state.eventSource.onerror = () => {
        stopLiveUpdates();
        setBusy(false);
        renderError("批量任务事件流已断开。");
      };
    }

    function renderReportShell(detail) {
      setStatus(detail.status, detail.ticker || "报告");
      els.workspaceTitle.textContent = `${detail.ticker} 投研报告`;
      els.metricStatus.textContent = humanStatus(detail.status);
      els.metricDecision.textContent = detail.decision || "-";
      els.metricConfidence.textContent = detail.confidence == null ? "-" : `${Math.round(detail.confidence * 100)}%`;
      els.metricTask.textContent = `#${detail.id}`;
    }

    function renderReport(detail) {
      const report = detail.report || {};
      const position = report.position_sizing;
      const trace = report.agent_trace || [];
      const markdown = detail.markdown || "未返回 Markdown 报告。";
      els.canvas.innerHTML = `
        <div class="report-grid">
          <article class="report-paper markdown">${renderMarkdown(markdown)}</article>
          <aside class="inspector">
            <div class="metric-grid">
              <div class="metric"><span>决策</span><strong>${escapeHtml(detail.decision || "-")}</strong></div>
              <div class="metric"><span>置信度</span><strong>${detail.confidence == null ? "-" : Math.round(detail.confidence * 100) + "%"}</strong></div>
              <div class="metric"><span>风险项</span><strong>${(report.risks || []).length}</strong></div>
              <div class="metric"><span>信号数</span><strong>${(report.signals || []).length}</strong></div>
            </div>
            ${position ? renderPosition(position) : ""}
            <div>
              <h2>智能体轨迹</h2>
              <div class="agent-stack">${renderTrace(trace)}</div>
            </div>
          </aside>
        </div>
      `;
    }

    function renderPosition(position) {
      return `
        <div class="metric">
          <span>仓位计划</span>
          <strong>${escapeHtml(position.action || "-")}</strong>
          <p class="microcopy">目标 ${formatPct(position.target_weight)} · 交易金额 ${formatMoney(position.trade_value)}</p>
        </div>
      `;
    }

    function renderTrace(trace) {
      if (!trace.length) return '<div class="agent-item"><span>未返回智能体轨迹。</span></div>';
      return trace.map((item, index) => `
        <div class="agent-item ${index === trace.length - 1 ? "active" : ""}">
          <strong>${escapeHtml(item.agent || "智能体")}</strong>
          <span>${escapeHtml(item.message || "")}</span>
        </div>
      `).join("");
    }

    function renderBatch(detail) {
      setStatus(detail.status, `批量任务 #${detail.id || detail.batch_id}`);
      els.workspaceTitle.textContent = `批量任务 #${detail.id || detail.batch_id}`;
      els.metricStatus.textContent = humanStatus(detail.status);
      els.metricDecision.textContent = `${detail.completed || 0}/${detail.total || 0}`;
      els.metricConfidence.textContent = `${detail.failed || 0} 失败`;
      els.metricTask.textContent = `#${detail.id || detail.batch_id}`;
      const items = detail.items || [];
      els.canvas.innerHTML = `
        <div class="batch-table-wrap">
          <table>
            <thead>
              <tr>
                <th>股票</th>
                <th>状态</th>
                <th>日期</th>
                <th>决策</th>
                <th>置信度</th>
                <th>错误</th>
              </tr>
            </thead>
            <tbody>
              ${items.map(renderBatchRow).join("") || '<tr><td colspan="6">正在等待批量任务明细。</td></tr>'}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderBatchRow(item) {
      return `
        <tr>
          <td><strong>${escapeHtml(item.ticker || "-")}</strong></td>
          <td><span class="pill ${escapeHtml(item.status || "queued")}">${humanStatus(item.status || "queued")}</span></td>
          <td>${escapeHtml(item.analysis_date || "-")}</td>
          <td>${escapeHtml(item.decision || "-")}</td>
          <td>${item.confidence == null ? "-" : Math.round(item.confidence * 100) + "%"}</td>
          <td>${escapeHtml(item.error || "")}</td>
        </tr>
      `;
    }

    async function loadHistory() {
      try {
        const response = await fetch("/reports?limit=8");
        const reports = await response.json();
        if (!response.ok) throw new Error("加载报告列表失败。");
        if (!reports.length) {
          els.history.innerHTML = '<div class="history-item"><span>暂无报告。</span></div>';
          return;
        }
        els.history.innerHTML = reports.map((report) => `
          <button class="history-item" type="button" data-report-id="${report.id}">
            <strong>${escapeHtml(report.ticker)} <span class="pill ${escapeHtml(report.status)}">${humanStatus(report.status)}</span></strong>
            <span>${escapeHtml(report.analysis_date)} · ${escapeHtml(report.decision || "待生成")}</span>
          </button>
        `).join("");
        els.history.querySelectorAll("[data-report-id]").forEach((button) => {
          button.addEventListener("click", () => openReport(button.dataset.reportId));
        });
      } catch (error) {
        els.history.innerHTML = `<div class="history-item"><span>${escapeHtml(error.message)}</span></div>`;
      }
    }

    async function openReport(reportId) {
      stopLiveUpdates();
      setBusy(false);
      const response = await fetch(`/reports/${reportId}`);
      const detail = await response.json();
      if (!response.ok) {
        renderError(detail.detail || "打开报告失败。");
        return;
      }
      renderReportShell(detail);
      if (detail.status === "completed") renderReport(detail);
      if (detail.status === "failed") renderError(detail.error || "报告生成失败。");
    }

    async function checkHealth() {
      try {
        const response = await fetch("/health");
        if (!response.ok) throw new Error("offline");
        els.serverStatus.innerHTML = "<strong>在线</strong> API";
      } catch {
        els.serverStatus.innerHTML = "<strong style='color: var(--red)'>离线</strong> API";
      }
    }

    function renderLoading(title, text) {
      els.canvas.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-inner">
            <div class="orbit" aria-hidden="true">
              <div class="node">行情</div>
              <div class="node">新闻</div>
              <div class="node">技术</div>
              <div class="node">风险</div>
              <div class="node">组合</div>
            </div>
            <p><strong>${escapeHtml(title)}</strong><br>${escapeHtml(text)}</p>
          </div>
        </div>
      `;
    }

    function renderError(message) {
      setStatus("failed", "错误");
      els.metricStatus.textContent = humanStatus("failed");
      els.canvas.innerHTML = `<div class="error-box">${escapeHtml(message)}</div>`;
    }

    function setStatus(status, label) {
      els.statusPill.className = `pill ${status}`;
      els.statusPill.textContent = humanStatus(status);
      els.metricStatus.textContent = humanStatus(status);
      if (label) els.workspaceTitle.textContent = label;
    }

    function resetMetrics() {
      els.metricStatus.textContent = humanStatus("idle");
      els.metricDecision.textContent = "-";
      els.metricConfidence.textContent = "-";
      els.metricTask.textContent = "-";
      els.statusPill.className = "pill idle";
      els.statusPill.textContent = humanStatus("idle");
      els.workspaceTitle.textContent = "智能体工作台";
    }

    function setBusy(isBusy) {
      els.submitButton.disabled = isBusy;
      if (isBusy) {
        els.submitButton.textContent = state.mode === "single" ? "分析中..." : "同步中...";
      } else {
        els.submitButton.textContent = state.mode === "single" ? "开始分析" : "启动批量任务";
      }
    }

    function stopLiveUpdates() {
      if (state.pollHandle) window.clearInterval(state.pollHandle);
      state.pollHandle = null;
      if (state.eventSource) state.eventSource.close();
      state.eventSource = null;
    }

    function renderMarkdown(markdown) {
      const lines = escapeHtml(markdown).split("\\n");
      const html = [];
      let inList = false;
      for (const line of lines) {
        const formatted = formatInline(line);
        if (line.startsWith("### ")) {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<h3>${formatInline(line.slice(4))}</h3>`);
        } else if (line.startsWith("## ")) {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<h2>${formatInline(line.slice(3))}</h2>`);
        } else if (line.startsWith("# ")) {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<h1>${formatInline(line.slice(2))}</h1>`);
        } else if (line.startsWith("- ")) {
          if (!inList) { html.push("<ul>"); inList = true; }
          html.push(`<li>${formatInline(line.slice(2))}</li>`);
        } else if (line.trim() === "") {
          if (inList) { html.push("</ul>"); inList = false; }
        } else {
          if (inList) { html.push("</ul>"); inList = false; }
          html.push(`<p>${formatted}</p>`);
        }
      }
      if (inList) html.push("</ul>");
      return html.join("");
    }

    function formatInline(value) {
      return value
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");
    }

    function formatPct(value) {
      if (value == null) return "-";
      return `${Math.round(Number(value) * 1000) / 10}%`;
    }

    function formatMoney(value) {
      if (value == null) return "-";
      return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
    }

    function humanStatus(status) {
      const labels = {
        idle: "待命",
        queued: "排队中",
        running: "运行中",
        completed: "已完成",
        failed: "失败",
        completed_with_errors: "部分失败",
        missing: "缺失"
      };
      return labels[status] || String(status || "idle").replaceAll("_", " ");
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
