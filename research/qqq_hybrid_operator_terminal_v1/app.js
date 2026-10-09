(() => {
  "use strict";
  const E = window.HybridOperatorEngineV1;
  const $ = (id) => document.getElementById(id);
  const candidates = {};
  let lastPlan = null;
  let marketSource = "BLOCKED";
  let marketMeta = "";
  let marketTouched = false;

  const TOP_BUDGETS = {
    qqqCallSpreads: "qqqCallRiskPct",
    vxxCallSpreads: "vxxCallRiskPct",
    vxxPutSpreads: "vxxPutRiskPct",
    qqqBullPutSpreads: "qqqBullPutRiskPct"
  };
  const STOCK_KEYS = ["qqqShares", "vxxShortShares"];

  const fmt = (v, digits = 0) => Number.isFinite(Number(v)) ? Number(v).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }) : "—";
  const usd = (v) => Number.isFinite(Number(v)) ? "$" + Number(v).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) : "—";
  const signed = (v) => Number.isFinite(Number(v)) ? (v > 0 ? "+" : "") + fmt(v, 0) : "—";
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const inputNumber = (id, fallback = 0) => E.num($(id)?.value, fallback);

  function buildOptionRows() {
    const body = $("optionRows");
    body.innerHTML = E.OPTION_STRATEGIES.map((s) => {
      const mainBudgetId = TOP_BUDGETS[s.key];
      const budget = mainBudgetId ? inputNumber(mainBudgetId, s.defaultRiskPct) : s.defaultRiskPct;
      const manualKind = ["manualDebit", "manualRisk", "stressOnly"].includes(s.kind);
      const enableCell = s.baseline
        ? '<span class="tag active">BASELINE</span>'
        : '<label class="toggle small-toggle"><input id="enabled-' + s.key + '" type="checkbox"> enabled</label>';
      const riskCell = manualKind
        ? '<input id="risk-' + s.key + '" type="number" min="0" step="1" placeholder="' + (s.kind === "stressOnly" ? "stress loss" : s.kind === "manualDebit" ? "debit max loss" : "verified max loss") + '">'
        : '<span id="risk-' + s.key + '" class="risk-value">—</span>';
      const sourceCell = s.candidateKey
        ? '<small id="source-' + s.key + '" class="muted">candidate pending</small>'
        : '<small id="source-' + s.key + '" class="muted">' + (s.kind === "stressOnly" ? "UNBOUNDED TAIL" : "manual risk input") + '</small>';
      return '<tr data-key="' + s.key + '">' +
        '<td class="strategy-cell"><b>' + esc(s.label) + '</b>' + sourceCell + '<small id="reason-' + s.key + '" class="row-reason">Not sized yet</small></td>' +
        '<td><input id="current-' + s.key + '" type="number" min="0" step="1" value="0" aria-label="' + esc(s.label) + ' current contracts"></td>' +
        '<td><input id="budget-' + s.key + '" type="number" min="0" max="100" step="0.1" value="' + budget + '" aria-label="' + esc(s.label) + ' risk budget percent"></td>' +
        '<td>' + riskCell + '</td>' +
        '<td>' + enableCell + '</td>' +
        '<td id="capacity-' + s.key + '">—</td><td id="target-' + s.key + '">—</td><td id="action-' + s.key + '">—</td>' +
      '</tr>';
    }).join("");
    for (const [key, id] of Object.entries(TOP_BUDGETS)) {
      $("budget-" + key).value = inputNumber(id, 0);
      $(id).addEventListener("input", () => { $("budget-" + key).value = $(id).value; renderPlan(); });
      $("budget-" + key).addEventListener("input", () => { $(id).value = $("budget-" + key).value; renderPlan(); });
    }
  }

  function syncBudgetInputsFromProfile() {
    for (const [key, id] of Object.entries(TOP_BUDGETS)) $("budget-" + key).value = $(id).value;
    renderPlan();
  }

  function readMarket() {
    const today = $("mToday").value || new Date().toISOString().slice(0, 10);
    return {
      qqq: E.num($("mQqq").value),
      vxx: E.num($("mVxx").value),
      vix: E.num($("mVix").value),
      m1: E.num($("mM1").value),
      m2: E.num($("mM2").value),
      term_asof: $("mTermAsOf").value || null,
      spot_asof: $("mSpotAsOf").value || null,
      today,
      term_source: marketSource
    };
  }

  function readInput() {
    const sizing = {
      qqqCorePct: inputNumber("qqqCorePct", 42),
      vxxNormalPct: inputNumber("vxxNormalPct", 18),
      vxxHighPct: inputNumber("vxxHighPct", 10),
      totalOptionRiskPct: inputNumber("totalOptionRiskPct", 3.2),
      vixHigh: inputNumber("vixHigh", 28),
      termSafe: inputNumber("termSafe", 5),
      maxTermAgeDays: inputNumber("maxTermAgeDays", 4)
    };
    const holdings = {
      qqqShares: inputNumber("current-qqqShares", 0),
      vxxShortShares: inputNumber("current-vxxShortShares", 0)
    };
    const permissions = { allowProtectionBuys: $("allowProtectionBuys")?.checked === true };
    const manualRiskPerUnit = {};
    for (const s of E.OPTION_STRATEGIES) {
      sizing[s.riskPctField] = inputNumber("budget-" + s.key, s.defaultRiskPct);
      holdings[s.key] = inputNumber("current-" + s.key, 0);
      if (!s.baseline) permissions[s.key] = $("enabled-" + s.key)?.checked === true;
      if (["manualDebit", "manualRisk", "stressOnly"].includes(s.kind)) manualRiskPerUnit[s.key] = inputNumber("risk-" + s.key, null);
    }
    return {
      market: readMarket(),
      nav: inputNumber("nav", 0),
      cashPool: inputNumber("cashPool", 0),
      sizing, holdings, candidates, permissions, manualRiskPerUnit,
      ratioCampaign: {
        enabled: $("nxEnabled").checked,
        currentFarShort: inputNumber("nxCurrentFar", 0),
        currentNearLong: inputNumber("nxCurrentNear", 0),
        nShort: inputNumber("nxNShort", 10),
        farDelta: inputNumber("nxFarDelta", 0.08),
        nearDelta: inputNumber("nxNearDelta", 0.5),
        coverageMult: inputNumber("nxCoverage", 1.5),
        maxStack: inputNumber("nxMaxStack", 5),
        farDistancePct: inputNumber("nxFarDistancePct", 10),
        gammaRel: inputNumber("nxGammaRel", 1),
        deltaJump: inputNumber("nxDeltaJump", 0)
      }
    };
  }

  function setInput(id, value) {
    const el = $(id);
    if (!el) return;
    el.value = value === null || value === undefined ? "" : value;
  }

  function setMarket(snapshot, meta = "") {
    marketTouched = false;
    marketSource = snapshot?.term_source || "BLOCKED";
    setInput("mQqq", snapshot?.qqq);
    setInput("mVxx", snapshot?.vxx);
    setInput("mVix", snapshot?.vix);
    setInput("mM1", snapshot?.m1);
    setInput("mM2", snapshot?.m2);
    setInput("mSpotAsOf", snapshot?.spot_asof);
    setInput("mTermAsOf", snapshot?.term_asof);
    setInput("mToday", snapshot?.today || new Date().toISOString().slice(0, 10));
    marketMeta = meta || [
      snapshot?.bridge_source || snapshot?.source_chain?.join(" → ") || "V3 snapshot",
      snapshot?.provenance ? JSON.stringify(snapshot.provenance) : "",
      snapshot?.bridge_retrieved_at || snapshot?.captured_at || ""
    ].filter(Boolean).join(" · ");
    renderPlan();
  }

  function currentCandidateText(candidate) {
    if (!candidate) return "PENDING · no usable chain candidate";
    if (candidate.maxLossPerSpread !== undefined) {
      return candidate.right.toUpperCase() + " vertical · " + candidate.expiry + " · " +
        fmt(candidate.dte) + " DTE · " + fmt(candidate.shortStrike, 2) + "/" + fmt(candidate.longStrike, 2) +
        " · credit " + usd(candidate.credit) + " · max loss " + usd(candidate.maxLossPerSpread) +
        " · " + candidate.source;
    }
    return candidate.right.toUpperCase() + " long · " + candidate.expiry + " · " + fmt(candidate.dte) +
      " DTE · K " + fmt(candidate.strike, 2) + " · ask " + usd(candidate.ask) + " · " + candidate.source;
  }

  async function refreshMarket() {
    $("marketReason").textContent = "Reading V3's local read-only snapshot…";
    try {
      const response = await fetch("/api/snapshot", { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok || payload.ok === false || payload.term_source === "BLOCKED") {
        throw new Error(payload.message || payload.error || "V3 snapshot is blocked");
      }
      setMarket(payload);
      $("marketReason").textContent = "V3 market bridge loaded. Review provenance and as-of timestamps before using any target.";
    } catch (error) {
      marketSource = "BLOCKED";
      marketMeta = "V3 bridge unavailable: " + (error instanceof Error ? error.message : String(error));
      $("marketMeta").textContent = marketMeta;
      $("marketReason").textContent = "Enter an explicitly verified snapshot into the market fields. Missing prices/M1/M2 are never filled with invented values.";
      renderPlan();
    }
  }

  async function findCandidate(button) {
    const key = button.dataset.find, symbol = button.dataset.symbol, right = button.dataset.right;
    const targetDte = Math.max(14, Math.min(120, inputNumber("targetDte", 45)));
    button.disabled = true;
    button.textContent = "Finding…";
    try {
      const response = await fetch("/api/options?symbol=" + encodeURIComponent(symbol) + "&targetDte=" + targetDte + "&right=both", { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error || "option chain unavailable");
      const spot = E.num($(symbol === "QQQ" ? "mQqq" : "mVxx").value);
      if (!(spot > 0)) throw new Error("spot missing; refresh V3 or enter a verified spot first");
      const candidate = button.dataset.kind === "vertical"
        ? E.findCreditVertical(payload, spot, right, targetDte, 0.16, $("mToday").value)
        : button.dataset.kind === "short"
          ? E.findShortCall(payload, spot, targetDte, 0.16, $("mToday").value)
          : E.findLongOption(payload, spot, right, targetDte, right === "put" ? 0.25 : 0.16, $("mToday").value);
      if (!candidate) throw new Error("No candidate with valid strikes, expiry and positive bid/ask credit/debit. No substitute price was invented.");
      candidate.chainRetrievedAt = payload.retrieved_at;
      candidates[key] = candidate;
      $("candidateRows").innerHTML = Object.keys(candidates).filter(k => candidates[k]).map(k =>
        '<div class="candidate-row"><b>' + esc(k) + '</b><span>' + esc(currentCandidateText(candidates[k])) + '</span></div>'
      ).join("");
      $("journalStatus").textContent = payload.warning || "Candidate loaded. Public chain data is indicative only.";
      renderPlan();
    } catch (error) {
      candidates[key] = null;
      $("candidateRows").innerHTML = Object.keys(candidates).filter(k => candidates[k]).map(k =>
        '<div class="candidate-row"><b>' + esc(k) + '</b><span>' + esc(currentCandidateText(candidates[k])) + '</span></div>'
      ).join("") || '<div class="empty">No usable candidates. A missing candidate stays PENDING.</div>';
      $("journalStatus").textContent = key + ": " + (error instanceof Error ? error.message : String(error));
      renderPlan();
    } finally {
      button.disabled = false;
      button.textContent = button.dataset.label || ({
        qqqCall: "Find QQQ Call Vertical", vxxCall: "Find VXX Call Vertical",
        vxxPut: "Find VXX Put Vertical", qqqPut: "Find QQQ Put Vertical",
        qqqLongCall: "Find QQQ Long Call", qqqLongPut: "Find QQQ Long Put", qqqCoveredCall: "Find Covered Call"
      }[key] || "Find Candidate");
    }
  }

  function renderActionCell(row, idPrefix) {
    const targetEl = $(idPrefix + "-target");
    const actionEl = $(idPrefix + "-action");
    const capacityEl = $(idPrefix + "-capacity");
    if (capacityEl) capacityEl.textContent = row.capacity === null || row.capacity === undefined ? "PENDING" : fmt(row.capacity);
    if (targetEl) targetEl.textContent = row.target === null || row.target === undefined ? "PENDING" : fmt(row.target);
    if (actionEl) {
      actionEl.textContent = row.action + (row.delta ? " " + signed(row.delta) : "");
      actionEl.className = "action-cell " + String(row.action || "").toLowerCase();
      actionEl.title = row.reason || "";
    }
  }

  function renderPlan() {
    updateSlopeDisplay();
    const input = readInput();
    // Manual edits make the source explicit rather than silently preserving a stale V3 provenance tag.
    if (marketTouched) input.market.term_source = "MANUAL_OPERATOR_INPUT";
    const result = E.calculatePortfolio(input);
    lastPlan = { generatedAt: new Date().toISOString(), input, result, candidates };
    const m = result.market;
    $("marketBadge").textContent = m.status + (m.blocked ? " · NO SIZING" : "");
    $("marketBadge").className = "tag " + (m.blocked ? "danger" : m.state === "CARRY" ? "active" : "warn");
    $("marketMeta").textContent = marketMeta || (marketTouched ? "MANUAL_OPERATOR_INPUT — confirm source and dates." : "No source metadata.");
    $("marketReason").textContent = m.reason;
    $("stateName").textContent = m.state;
    $("stateAction").textContent = m.action + (m.allowNew ? " · NEW ENTRIES ALLOWED" : " · NO NEW CARRY ADDS");
    $("gData").textContent = m.status;
    $("gVix").textContent = Number.isFinite(m.vix) ? fmt(m.vix, 2) + (m.high ? " · HIGH" : "") : "—";
    $("gTerm").textContent = Number.isFinite(m.slope) ? fmt(m.slope, 2) + "%" + (m.backwardation ? " · BACK" : m.thin ? " · THIN" : " · OK") : "—";
    $("gAdds").textContent = m.blocked ? "BLOCKED" : m.allowNew ? "CARRY" : "HOLD / CUT";
    $("mSlope").value = Number.isFinite(m.slope) ? fmt(m.slope, 2) + "%" : "—";

    for (const r of result.rows.filter(row => ["qqqShares","vxxShortShares"].includes(row.key))) {
      $("capacity-" + r.key).textContent = r.capacity === null || r.capacity === undefined ? "PENDING" : fmt(r.capacity);
      $("target-" + r.key).textContent = r.target === null || r.target === undefined ? "PENDING" : fmt(r.target);
      $("action-" + r.key).textContent = r.action + (r.delta ? " " + signed(r.delta) : "") + " shares";
      $("action-" + r.key).className = "action-cell " + String(r.action || "").toLowerCase();
      $("action-" + r.key).title = r.reason || "";
    }

    for (const r of result.rows.filter(row => E.OPTION_STRATEGIES.some(s => s.key === row.key))) {
      $("capacity-" + r.key).textContent = r.capacity === null || r.capacity === undefined ? "PENDING" : fmt(r.capacity);
      $("target-" + r.key).textContent = r.target === null || r.target === undefined ? "PENDING" : fmt(r.target);
      $("action-" + r.key).textContent = r.action + (r.delta ? " " + signed(r.delta) : "");
      $("action-" + r.key).className = "action-cell " + String(r.action || "").toLowerCase();
      $("reason-" + r.key).textContent = r.reason || "";
      $("reason-" + r.key).title = r.reason || "";
      const riskEl = $("risk-" + r.key);
      if (riskEl && riskEl.tagName !== "INPUT") {
        riskEl.textContent = r.riskPerUnit === null || r.riskPerUnit === undefined ? "—" : usd(r.riskPerUnit);
      }
      const sourceEl = $("source-" + r.key);
      if (sourceEl) sourceEl.textContent = r.candidateSource || r.riskSource || r.status;
    }

    const ratio = result.ratioCampaign;
    $("nxResult").innerHTML =
      '<div class="nx-grid"><div><small>FAR SHORT</small><b>' + fmt(ratio.currentFar) + ' → ' + fmt(ratio.targetFar) + '</b><span class="' + String(ratio.actionFar).toLowerCase() + '">' + esc(ratio.actionFar) + ' ' + signed(ratio.farDelta) + '</span></div>' +
      '<div><small>NEAR LONG</small><b>' + fmt(ratio.currentNear) + ' → ' + fmt(ratio.targetNear) + '</b><span class="' + String(ratio.actionNear).toLowerCase() + '">' + esc(ratio.actionNear) + ' ' + signed(ratio.nearDelta) + '</span></div></div>' +
      '<p>Risk score ' + fmt(ratio.riskScore, 2) + ' = delta ' + ratio.dScore + ' × 0.50 + distance ' + ratio.xScore + ' × 0.30 + gamma/jump ' + ratio.gScore + ' × 0.20. Base near target ' + fmt(ratio.baseNearTarget) + ', stack adjustment +' + fmt(ratio.stackAdjustment) + '.</p>' +
      '<p>' + esc(ratio.note || "Disabled or risk gate active; this is a per-campaign reference only.") + '</p>' +
      '<b class="danger-text">Risk boundary: no hard max-loss cap.</b>';

    const riskRows = result.rows.filter(r => r.family !== "hybrid" && r.riskPerUnit && r.target > 0 && r.strategyKind !== "coveredCall");
    const optionRiskAtTargets = result.optionRiskReservedAtTargets || 0;
    $("summaryMetrics").innerHTML = [
      ["Market gate", m.state],
      ["NAV / cash pool", usd(result.nav) + " / " + usd(result.cashPool)],
      ["Max option-risk pool", usd(result.totalOptionRiskPool)],
      ["Option risk reserved", usd(optionRiskAtTargets)],
      ["Sizing status", result.ok ? "CALCULATED / REVIEW" : "BLOCKED"]
    ].map(([k,v]) => '<div><small>' + esc(k) + '</small><b>' + esc(v) + '</b></div>').join("");
    $("summaryReasons").innerHTML = '<p><b>Why:</b> ' + esc(m.reason) + '</p>' +
      '<p><b>Safety:</b> target capacities are derived from current inputs; excess is shown as REDUCE even when additions are blocked. Missing chain candidates stay PENDING.</p>' +
      '<p><b>Ratio boundary:</b> stress-loss inputs do not turn an uncapped ratio tail into a hard loss limit.</p>';
    updateTestResult(result);
  }

  function updateSlopeDisplay() {
    const slope = E.termSlope(E.num($("mM1").value), E.num($("mM2").value));
    $("mSlope").value = slope === null ? "—" : fmt(slope, 2) + "%";
  }

  function updateTestResult(result) {
    const key = $("testLeg").value;
    const row = result.rows.find(r => r.key === key);
    if (!row) {
      $("testResult").textContent = "No result for selected leg.";
      return;
    }
    if (row.capacity === null) {
      $("testResult").innerHTML = '<b>PENDING:</b> ' + esc(row.reason || "A current candidate/risk input is missing.") + '<br>Current quantity is retained; no fabricated target.';
    } else if (row.delta < 0) {
      $("testResult").innerHTML = '<b>REDUCE:</b> current ' + fmt(row.current) + ' → target ' + fmt(row.target) + '; reduce by ' + fmt(Math.abs(row.delta)) + ' units.<br>' + esc(row.reason || "");
    } else if (row.delta > 0) {
      $("testResult").innerHTML = '<b>ADD PREVIEW:</b> current ' + fmt(row.current) + ' → target ' + fmt(row.target) + '; potential add ' + fmt(row.delta) + ' units.<br>Manual review only; no order is sent.';
    } else {
      $("testResult").innerHTML = '<b>' + esc(row.action) + ':</b> current ' + fmt(row.current) + ', target ' + (row.target === null ? "PENDING" : fmt(row.target)) + '.<br>' + esc(row.reason || "");
    }
  }

  function setTest1000() {
    const key = $("testLeg").value;
    const input = $("current-" + key);
    if (input) input.value = 1000;
    renderPlan();
    $("journalStatus").textContent = "SIMULATION ONLY: current quantity set to 1000 for " + key + ". No actual position was changed.";
  }

  function serializePlan() {
    if (!lastPlan) renderPlan();
    return JSON.stringify({
      schema: "QQQ_HYBRID_OPERATOR_TERMINAL_V1",
      generatedAt: lastPlan.generatedAt,
      input: lastPlan.input,
      result: lastPlan.result,
      candidates,
      boundary: { brokerOrders: false, automaticMutation: false, historicalSizingPromotedToLive: false }
    }, null, 2);
  }

  function exportPlan() {
    const blob = new Blob([serializePlan()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "qqq-hybrid-operator-plan.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function appendJournal() {
    const payload = {
      record_type: "MANUAL_PREVIEW",
      input: lastPlan?.input || readInput(),
      result: lastPlan?.result || null,
      candidates,
      boundary: { brokerOrders: false, automaticMutation: false }
    };
    try {
      const response = await fetch("/api/journal", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "journal endpoint unavailable");
      $("journalStatus").textContent = "Preview journal appended at " + result.journaled_at + ". No broker action occurred.";
    } catch (error) {
      $("journalStatus").textContent = "Journal service unavailable: " + (error instanceof Error ? error.message : String(error)) + ". Export JSON to save this preview.";
    }
  }

  function loadReferenceProfile() {
    const p = E.REFERENCE_PROFILE;
    for (const [k,v] of Object.entries({
      qqqCorePct:p.qqqCorePct, vxxNormalPct:p.vxxNormalPct, vxxHighPct:p.vxxHighPct,
      qqqCallRiskPct:p.qqqCallRiskPct, vxxCallRiskPct:p.vxxCallRiskPct,
      vxxPutRiskPct:p.vxxPutRiskPct, qqqBullPutRiskPct:p.qqqBullPutRiskPct,
      totalOptionRiskPct:p.totalOptionRiskPct, vixHigh:p.vixHigh, termSafe:p.termSafe, maxTermAgeDays:p.maxTermAgeDays
    })) $(k).value = v;
    syncBudgetInputsFromProfile();
    $("journalStatus").textContent = "Loaded V3 reference parameters for a what-if preview. This does not change any live policy or broker position.";
  }

  function wire() {
    buildOptionRows();
    $("mToday").value = new Date().toISOString().slice(0,10);
    $("refreshBtn").addEventListener("click", refreshMarket);
    $("v3ProfileBtn").addEventListener("click", loadReferenceProfile);
    $("test1000Btn").addEventListener("click", setTest1000);
    $("testLeg").addEventListener("change", () => { window.hybridTestOverrides = {}; renderPlan(); });
    $("exportBtn").addEventListener("click", exportPlan);
    $("journalBtn").addEventListener("click", appendJournal);
    document.querySelectorAll("[data-find]").forEach(btn => {
      btn.dataset.label = btn.textContent;
      btn.addEventListener("click", () => findCandidate(btn));
    });
    document.querySelectorAll("input,select").forEach(el => {
      if (el.id.startsWith("current-") || el.id.startsWith("budget-") || el.id.startsWith("risk-") || el.id.startsWith("enabled-") ||
          ["mQqq","mVxx","mVix","mM1","mM2","mSpotAsOf","mTermAsOf","mToday","nav","cashPool","qqqCorePct","vxxNormalPct","vxxHighPct","totalOptionRiskPct","vixHigh","termSafe","maxTermAgeDays","nxEnabled","nxCurrentFar","nxCurrentNear","nxFarDelta","nxNearDelta","nxCoverage","nxMaxStack","nxNShort","nxFarDistancePct","nxGammaRel","nxDeltaJump","allowProtectionBuys","targetDte"].includes(el.id)) {
        el.addEventListener("input", () => {
          if (["mQqq","mVxx","mVix","mM1","mM2","mSpotAsOf","mTermAsOf","mToday"].includes(el.id)) {
            marketTouched = true;
            if (marketSource === "BLOCKED") marketSource = "MANUAL_OPERATOR_INPUT";
            marketMeta = "MANUAL_OPERATOR_INPUT — market prices and expiry state must be verified by the operator.";
          }
          // Keep the top-level mirrors and option rows synchronized.
          const budgetKey = Object.entries(TOP_BUDGETS).find(([,id]) => id === el.id)?.[0];
          if (budgetKey) $("budget-" + budgetKey).value = el.value;
          renderPlan();
        });
      }
    });
    // Restore the first test model after initial render.
    renderPlan();
    refreshMarket();
  }

  wire();
})();
