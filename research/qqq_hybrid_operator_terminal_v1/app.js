(() => {
  "use strict";
  const E = window.HybridOperatorEngineV1;
  const $ = (id) => document.getElementById(id);
  const candidates = {};
  let lastPlan = null;
  let marketSource = "BLOCKED";
  let marketMeta = "";
  let marketTouched = false;
  let hubChainCandidates = null;
  let hubChainMeta = null;

  const TOP_BUDGETS = {
    qqqCallSpreads: "qqqCallRiskPct",
    vxxCallSpreads: "vxxCallRiskPct"
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
      const enableCell = !s.mainBudgetEligible
        ? '<span class="tag">RESEARCH ONLY</span>'
        : s.baseline
          ? '<span class="tag active">PRIMARY</span>'
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
        '<td>' + (s.mainBudgetEligible
          ? '<input id="budget-' + s.key + '" type="number" min="0" max="100" step="0.1" value="' + budget + '" aria-label="' + esc(s.label) + ' requested risk weight percent of NAV">'
          : '<span class="tag">OUTSIDE MAIN BUDGET</span>') + '</td>' +
        '<td id="allocated-' + s.key + '">—</td>' +
        '<td>' + riskCell + '</td>' +
        '<td>' + enableCell + '</td>' +
        '<td id="capacity-' + s.key + '">—</td><td id="target-' + s.key + '">—</td><td id="reserved-' + s.key + '">—</td><td id="action-' + s.key + '">—</td>' +
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
      cashReservePct: inputNumber("cashReservePct", 10),
      vxxShortMarginMultiple: inputNumber("vxxShortMarginMultiple", 1.5),
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
      sizing[s.riskPctField] = s.mainBudgetEligible ? inputNumber("budget-" + s.key, s.defaultRiskPct) : 0;
      holdings[s.key] = inputNumber("current-" + s.key, 0);
      if (s.mainBudgetEligible && !s.baseline) permissions[s.key] = $("enabled-" + s.key)?.checked === true;
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
    if (candidate.hubPackage === true) {
      return "HUB QQQ package · " + (candidate.expiry || "expiry pending") +
        " · max-loss/risk " + usd(candidate.riskPerUnit) +
        " · debit " + usd(candidate.debitUsd) +
        (candidate.n ? " · Ratio N=" + candidate.n : "") +
        (candidate.maxUnits ? " · cap " + fmt(candidate.maxUnits) + " packages" : "") +
        " · " + (candidate.gatePass === false ? "ENTRY GATE OFF" : "risk candidate ready");
    }
    if (candidate.maxLossPerSpread !== undefined) {
      return candidate.right.toUpperCase() + " vertical · " + candidate.expiry + " · " +
        fmt(candidate.dte) + " DTE · " + fmt(candidate.shortStrike, 2) + "/" + fmt(candidate.longStrike, 2) +
        " · credit " + usd(candidate.credit) + " · max loss " + usd(candidate.maxLossPerSpread) +
        " · " + candidate.source;
    }
    return candidate.right.toUpperCase() + " long · " + candidate.expiry + " · " + fmt(candidate.dte) +
      " DTE · K " + fmt(candidate.strike, 2) + " · ask " + usd(candidate.ask) + " · " + candidate.source;
  }

  function syncHubResearchCandidates() {
    if (!hubChainCandidates) {
      delete candidates.hubRatioCall;
      delete candidates.hubStateAdaptive;
      delete candidates.hubShockPut;
      return;
    }
    const H = window.HubOptionPackV1;
    const c = hubChainCandidates;
    const spot = E.num($("mQqq").value);
    if (!H || !(spot > 0)) return;
    if (Math.abs(spot - c.spotAtLoad) / c.spotAtLoad > 0.025) {
      const stale = { ready: false, hubPackage: true, source: "HUB_CHAIN_STALE_SPOT", expiry: c.expiry,
        riskPerUnit: null, debitUsd: null, error: "QQQ spot moved more than 2.5% since candidate lookup; reload the chain before sizing." };
      candidates.hubRatioCall = { ...stale };
      candidates.hubStateAdaptive = { ...stale };
      candidates.hubShockPut = { ...stale };
      return;
    }

    const common = {
      spot,
      atmStrike: c.atm.strike, atmAsk: c.atm.ask,
      shortStrike: c.short.strike, shortBid: c.short.bid,
      wingStrike: c.wing.strike, wingAsk: c.wing.ask,
      longPutStrike: c.longPut.strike, longPutAsk: c.longPut.ask,
      shortPutStrike: c.shortPut.strike, shortPutBid: c.shortPut.bid
    };
    const quoteSource = "HUB_QQQ_CHAIN_" + (c.deltaSource || "DELTA_UNKNOWN");
    const n = Math.max(1, Math.min(4, inputNumber("hubRatioN", 2)));
    const ratioRisk = H.terminalMaxLoss(H.ratioCallLegs(common, n), spot);
    candidates.hubRatioCall = ratioRisk.ready ? {
      hubPackage: true, ready: true, right: "call", expiry: c.expiry, n,
      riskPerUnit: Math.max(ratioRisk.riskUsd, Math.max(0, ratioRisk.debitUsd)),
      debitUsd: ratioRisk.debitUsd, maxUnits: 100, gatePass: true,
      source: quoteSource,
      reason: "Hub Ratio-Call package +1 ATM Call − N OTM Short Calls + N farther-OTM Wings; entry risk is shared with all other option rows."
    } : {
      hubPackage: true, ready: false, right: "call", expiry: c.expiry,
      source: quoteSource, error: ratioRisk.error || "Ratio-call package risk could not be established."
    };

    const state = H.calculateStateAdaptive({
      ...common, budgetUsd: 1e12, wave: 0, prevClose: null, anchorClose: null, atr20: null
    });
    const layerCap = [1,2,4].includes(Number($("hubStateLayerCap").value)) ? Number($("hubStateLayerCap").value) : 1;
    candidates.hubStateAdaptive = state.ready ? {
      hubPackage: true, ready: true, right: "call", expiry: c.expiry,
      riskPerUnit: Math.max(state.riskUsd, Math.max(0, state.debitUsd)),
      debitUsd: state.debitUsd, maxUnits: layerCap, gatePass: true,
      source: quoteSource,
      reason: "Hub State-Adaptive five-leg package; the selected 1/2/4 vintage cap applies, and all active vintages share the same pool."
    } : {
      hubPackage: true, ready: false, right: "call", expiry: c.expiry,
      source: quoteSource, error: state.error || "State-Adaptive package risk could not be established."
    };

    const shock = H.calculateShockGatedPut({
      ...common, budgetUsd: 1e12,
      drawdown252Pct: inputNumber("hubDrawdown252Pct", 0),
      return5dPct: inputNumber("hubReturn5dPct", 0)
    });
    candidates.hubShockPut = shock.ready ? {
      hubPackage: true, ready: true, right: "put", expiry: c.expiry,
      riskPerUnit: Math.max(shock.riskUsd, Math.max(0, shock.debitUsd)),
      debitUsd: shock.debitUsd, maxUnits: 100, gatePass: shock.triggered,
      source: quoteSource,
      reason: shock.reason
    } : {
      hubPackage: true, ready: false, right: "put", expiry: c.expiry,
      source: quoteSource, error: shock.error || "Shock-gated put spread risk could not be established."
    };
  }

  async function findHubResearchCandidates() {
    const button = $("findHubResearchBtn");
    const status = $("journalStatus");
    const spot = E.num($("mQqq").value);
    if (!(spot > 0)) {
      status.textContent = "Hub candidates need a verified QQQ spot. Refresh V3 first, or enter QQQ spot manually.";
      return;
    }
    const targetDte = Math.max(14, Math.min(120, inputNumber("targetDte", 45)));
    button.disabled = true;
    button.textContent = "Finding Hub packages…";
    try {
      const response = await fetch("/api/options?symbol=QQQ&right=both&targetDte=" + encodeURIComponent(targetDte), { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error || "QQQ chain unavailable");
      const result = window.HubOptionPackV1.chooseChainLegs(payload, spot, $("mToday").value || new Date().toISOString().slice(0, 10), targetDte);
      if (!result.ready) throw new Error(result.error || "Could not form the researched five-leg QQQ package.");
      hubChainCandidates = { ...result, spotAtLoad: spot };
      hubChainMeta = { retrievedAt: payload.retrieved_at, source: payload.source, expiry: result.expiry };
      syncHubResearchCandidates();
      $("candidateRows").innerHTML = ["hubRatioCall","hubStateAdaptive","hubShockPut"].map(key =>
        '<div class="candidate-row"><b>' + esc(key) + '</b><span>' + esc(currentCandidateText(candidates[key])) + '</span></div>'
      ).join("");
      status.textContent = "Hub QQQ candidates loaded for expiry " + result.expiry +
        " (" + (result.deltaSource || "Delta source unknown") + "). Public quotes may be delayed/incomplete; enable rows and set their % NAV risk weights to use the common risk pool.";
      renderPlan();
    } catch (error) {
      hubChainCandidates = null;
      hubChainMeta = null;
      syncHubResearchCandidates();
      status.textContent = "Hub research candidates are PENDING: " + (error instanceof Error ? error.message : String(error)) + ". No substitute leg or price was fabricated.";
      $("candidateRows").innerHTML = '<div class="empty">Hub candidates PENDING · ' + esc(error instanceof Error ? error.message : String(error)) + '</div>';
      renderPlan();
    } finally {
      button.disabled = false;
      button.textContent = "Find Hub Research Packages";
    }
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
      const targetAbsDelta = E.num(button.dataset.targetDelta, right === "put" ? 0.25 : 0.16);
      const candidate = button.dataset.kind === "vertical"
        ? E.findCreditVertical(payload, spot, right, targetDte, targetAbsDelta, $("mToday").value)
        : button.dataset.kind === "short"
          ? E.findShortCall(payload, spot, targetDte, targetAbsDelta, $("mToday").value)
          : E.findLongOption(payload, spot, right, targetDte, targetAbsDelta, $("mToday").value);
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
        qqqCall: "Find QQQ Far Call-Credit", qqqBearCall: "Find QQQ Bear-Call Vertical",
        vxxCall: "Find VXX Call Vertical", vxxPut: "Find VXX Put Vertical", qqqPut: "Find QQQ Put Vertical",
        qqqLongCall: "Find QQQ Long Call", qqqLongPut: "Find QQQ Long Put",
        qqqProtectivePut: "Find QQQ Protective Put", qqqCoveredCall: "Find Covered Call"
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

  function renderProDashboard(result, input) {
    const rows = result.rows || [];
    const getRow = (key) => rows.find((r) => r.key === key) || {};
    const nav = E.num(result.nav, 0);
    const cash = E.num(result.cashPool, 0);
    const qqq = getRow("qqqShares");
    const vxx = getRow("vxxShortShares");
    const qCall = getRow("qqqCallSpreads");
    const vCall = getRow("vxxCallSpreads");
    const inputCandidates = input.candidates || {};
    const qCandidate = inputCandidates.qqqCall || null;
    const vCandidate = inputCandidates.vxxCall || null;
    const exactUsd = (value) => Number.isFinite(Number(value)) ? "$" + Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—";
    const pct = (value) => Number.isFinite(Number(value)) ? Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + "%" : "—";
    const ratioPct = (value, base) => Number.isFinite(Number(value)) && Number(base) > 0 ? Number(value) / Number(base) * 100 : null;
    const displayQty = (row, unit) => row.capacity === null || row.capacity === undefined || result.market.blocked
      ? "PENDING" : fmt(row.capacity) + " " + unit;
    const capacity = (row) => row.capacity === null || row.capacity === undefined || result.market.blocked ? null : Math.max(0, Number(row.capacity));
    const card = (label, number, unit, meta, state = "ready") =>
      '<article class="pro-capacity-card ' + state + '"><small>' + esc(label) + '</small><b>' + esc(number) + '</b><span>' + esc(unit) + '</span><div class="pro-card-meta">' +
      meta.map((line) => '<span>' + line + '</span>').join("") + '</div></article>';
    const qtyQ = capacity(qqq), qtyV = capacity(vxx), qtyQc = capacity(qCall), qtyVc = capacity(vCall);
    const capQNotional = qtyQ !== null && Number.isFinite(Number(qqq.unitPrice)) ? qtyQ * Number(qqq.unitPrice) : null;
    const capVNotional = qtyV !== null && Number.isFinite(Number(vxx.unitPrice)) ? qtyV * Number(vxx.unitPrice) : null;
    const vxxMarginMultiple = E.num(input.sizing.vxxShortMarginMultiple, 1.5);
    const capVMargin = capVNotional !== null ? capVNotional * vxxMarginMultiple : null;
    const qRiskPerSpread = E.num(qCall.riskPerUnit);
    const vRiskPerSpread = E.num(vCall.riskPerUnit);
    const qMaxLoss = qtyQc !== null && qRiskPerSpread !== null ? qtyQc * qRiskPerSpread : null;
    const vMaxLoss = qtyVc !== null && vRiskPerSpread !== null ? qtyVc * vRiskPerSpread : null;
    const knownOptionRisk = (qMaxLoss === null ? 0 : qMaxLoss) + (vMaxLoss === null ? 0 : vMaxLoss);
    const knownOptionLegs = [qMaxLoss, vMaxLoss].filter((v) => v !== null).length;
    const pool = Number.isFinite(Number(result.totalOptionRiskPool)) ? Number(result.totalOptionRiskPool) : null;
    const usedPct = pool > 0 ? Math.min(100, knownOptionRisk / pool * 100) : 0;
    const stockNotional = capQNotional !== null && capVNotional !== null ? capQNotional + capVNotional : null;
    const capitalRequired = E.num(result.plannedCapitalRequiredUsd);
    const freeCash = E.num(result.remainingUnallocatedCashUsd);
    const currentTargetRisk = E.num(result.optionRiskReservedAtTargets);
    const calcStatus = $("proCalcStatus");
    calcStatus.textContent = result.market.blocked ? "BLOCKED · REFRESH / VERIFY DATA" :
      result.market.state + (result.market.allowNew ? " · ADDS PERMITTED BY GATE" : " · HOLD / REDUCE RULES");
    calcStatus.className = "pro-status " + (result.market.blocked ? "bad" : result.market.state === "CARRY" ? "good" : "warn");

    $("proKpis").innerHTML = [
      ["PORTFOLIO NAV", usd(nav), "NAV basis for all allocation percentages"],
      ["MAX STOCK NOTIONAL", stockNotional === null ? "PENDING" : exactUsd(stockNotional), stockNotional === null ? "Await valid market prices" : pct(ratioPct(stockNotional, nav)) + " of NAV · QQQ + VXX short"],
      ["MAX OPTION LOSS", qMaxLoss === null && vMaxLoss === null ? "PENDING" : usd(knownOptionRisk), pool !== null ? pct(ratioPct(knownOptionRisk, nav)) + " NAV · " + pct(usedPct) + " of shared pool" : "Waiting for risk pool"],
      ["FREE CASH AFTER PLAN", freeCash === null ? "PENDING" : exactUsd(freeCash), freeCash === null ? "Blocked until market data is fresh" : pct(ratioPct(freeCash, cash)) + " of uncommitted cash"]
    ].map(([label, value, sub]) => '<article class="pro-kpi"><small>' + esc(label) + '</small><b>' + esc(value) + '</b><span>' + esc(sub) + '</span></article>').join("");

    const components = [
      { key: "reserve", label: "Cash reserve", value: E.num(result.cashReserveUsd), color: "reserve" },
      { key: "risk", label: "Full option-risk envelope", value: E.num(result.totalOptionRiskPool), color: "risk" },
      { key: "qqq", label: "Incremental QQQ purchase", value: E.num(result.qqqAdditionalCapitalUsd), color: "qqq" },
      { key: "vxx", label: "Incremental VXX margin", value: E.num(result.vxxAdditionalMarginUsd), color: "vxx" },
      { key: "free", label: "Unallocated cash", value: freeCash, color: "free" }
    ];
    if (!result.ok || !(cash > 0)) {
      $("proCashUtilization").textContent = "PENDING";
      $("proCapitalChart").innerHTML = '<div class="pro-empty">Capital chart is blocked until NAV, cash and the V3 / manually verified market snapshot pass the freshness gate.</div>';
      $("proCapitalLegend").innerHTML = "";
    } else {
      $("proCashUtilization").textContent = pct(ratioPct(capitalRequired, cash)) + " USED";
      $("proCapitalChart").innerHTML =
        '<div class="pro-stack-track" aria-label="Cash plan allocation">' +
        components.map((c) => {
          const value = Number.isFinite(c.value) ? Math.max(0, c.value) : 0;
          const width = Math.max(0, Math.min(100, value / cash * 100));
          return '<div class="pro-stack-segment ' + c.color + '" title="' + esc(c.label + ": " + exactUsd(value)) + '" style="width:' + width.toFixed(4) + '%"></div>';
        }).join("") + '</div><div class="pro-stack-scale"><span>$0</span><span>' + esc(exactUsd(cash)) + ' available</span></div>';
      $("proCapitalLegend").innerHTML = components.map((c) => {
        const value = Number.isFinite(c.value) ? Math.max(0, c.value) : null;
        return '<div class="pro-legend-item"><i class="pro-legend-dot ' + c.color + '"></i><span class="pro-legend-label">' + esc(c.label) + '</span><b class="pro-legend-value">' + esc(value === null ? "PENDING" : exactUsd(value)) + '</b></div>';
      }).join("");
    }

    $("proOptionPoolLabel").textContent = pool === null ? "PENDING" : exactUsd(pool) + " · " + pct(ratioPct(pool, nav)) + " NAV";
    $("proRiskDonut").style.setProperty("--used", Number.isFinite(usedPct) ? usedPct.toFixed(2) : "0");
    $("proRiskUsedPct").textContent = (qMaxLoss === null || vMaxLoss === null) ? "PARTIAL" : pct(usedPct);
    const riskLegMarkup = [
      { label: "QQQ Call-Credit", amount: qMaxLoss, max: pool, cls: "" },
      { label: "VXX Call-Credit", amount: vMaxLoss, max: pool, cls: "vxx" },
      { label: "Unused after rounding", amount: pool === null ? null : Math.max(0, pool - knownOptionRisk), max: pool, cls: "" }
    ].map((item) => {
      const barPct = Number.isFinite(item.amount) && Number(item.max) > 0 ? Math.min(100, item.amount / item.max * 100) : 0;
      return '<div class="pro-risk-leg"><div class="pro-risk-leg-head"><span>' + esc(item.label) + '</span><b>' + esc(item.amount === null ? "PENDING" : exactUsd(item.amount)) + '</b></div><div class="pro-risk-track"><div class="pro-risk-fill ' + item.cls + '" style="width:' + barPct.toFixed(3) + '%"></div></div></div>';
    }).join("");
    $("proRiskBreakdown").innerHTML = riskLegMarkup;
    $("proRiskFoot").textContent = (knownOptionLegs === 2
      ? "Maximum spread risk at current contract capacity. "
      : "Partial quote coverage: missing legs are not assumed to have zero risk. ") +
      (currentTargetRisk === null ? "Current target risk is blocked/pending." : "Current policy target reserves " + exactUsd(currentTargetRisk) + ".") +
      " VXX put is excluded.";

    const qCreditPerSpread = E.num(qCandidate && qCandidate.credit);
    const vCreditPerSpread = E.num(vCandidate && vCandidate.credit);
    const qTotalCredit = qtyQc !== null && qCreditPerSpread !== null ? qCreditPerSpread * 100 * qtyQc : null;
    const vTotalCredit = qtyVc !== null && vCreditPerSpread !== null ? vCreditPerSpread * 100 * qtyVc : null;
    const qStrikes = qCandidate ? fmt(qCandidate.shortStrike, 2) + "C / " + fmt(qCandidate.longStrike, 2) + "C" : "Quote pending";
    const vStrikes = vCandidate ? fmt(vCandidate.shortStrike, 2) + "C / " + fmt(vCandidate.longStrike, 2) + "C" : "Quote pending";
    const expiryQ = qCandidate && qCandidate.expiry ? qCandidate.expiry : "same-expiry quote needed";
    const expiryV = vCandidate && vCandidate.expiry ? vCandidate.expiry : "same-expiry quote needed";
    const statusOf = (row, quantity, priceKnown) => result.market.blocked ? "BLOCKED" : quantity === null || !priceKnown ? "QUOTE / DATA PENDING" :
      row.action === "ADD" || row.action === "HOLD" ? esc(row.action) + " · REVIEW" : esc(row.action) + " · REVIEW";
    const statusClass = (text) => /PENDING|BLOCKED/.test(text) ? "pro-warn" : /ADD|READY|REVIEW/.test(text) ? "pro-good" : "pro-muted";
    const tableRows = [
      {
        name: "QQQ Core Shares", sub: "Equity allocation cap",
        price: result.market.blocked ? "PENDING" : exactUsd(result.market.qqq) + " / share",
        qty: displayQty(qqq, "shares"),
        exposure: capQNotional === null ? "PENDING" : exactUsd(capQNotional) + " notional",
        credit: "—", loss: "—",
        navPct: capQNotional === null ? "PENDING" : pct(ratioPct(capQNotional, nav)),
        status: statusOf(qqq, qtyQ, capQNotional !== null)
      },
      {
        name: "VXX Short Stock", sub: "Notional limit · short stock has uncapped upside risk",
        price: result.market.blocked ? "PENDING" : exactUsd(result.market.vxx) + " / share",
        qty: displayQty(vxx, "short shares"),
        exposure: capVNotional === null || capVMargin === null ? "PENDING" : exactUsd(capVNotional) + " notional · " + exactUsd(capVMargin) + " margin",
        credit: "—", loss: "Unbounded",
        navPct: capVNotional === null || capVMargin === null ? "PENDING" : pct(ratioPct(capVNotional, nav)) + " notional / " + pct(ratioPct(capVMargin, nav)) + " margin",
        status: statusOf(vxx, qtyV, capVMargin !== null)
      },
      {
        name: "QQQ Call-Credit", sub: "Short call + long wing · " + expiryQ,
        price: qCandidate ? qStrikes : "Quote pending",
        qty: qtyQc === null ? "PENDING" : fmt(qtyQc) + " spreads",
        exposure: qMaxLoss === null ? "PENDING" : exactUsd(qMaxLoss) + " max-loss exposure",
        credit: qTotalCredit === null ? "PENDING" : exactUsd(qTotalCredit),
        loss: qMaxLoss === null ? "PENDING" : exactUsd(qMaxLoss),
        navPct: qMaxLoss === null ? "PENDING" : pct(ratioPct(qMaxLoss, nav)),
        status: statusOf(qCall, qtyQc, qMaxLoss !== null)
      },
      {
        name: "VXX Call-Credit", sub: "Short call + long wing · " + expiryV,
        price: vCandidate ? vStrikes : "Quote pending",
        qty: qtyVc === null ? "PENDING" : fmt(qtyVc) + " spreads",
        exposure: vMaxLoss === null ? "PENDING" : exactUsd(vMaxLoss) + " max-loss exposure",
        credit: vTotalCredit === null ? "PENDING" : exactUsd(vTotalCredit),
        loss: vMaxLoss === null ? "PENDING" : exactUsd(vMaxLoss),
        navPct: vMaxLoss === null ? "PENDING" : pct(ratioPct(vMaxLoss, nav)),
        status: statusOf(vCall, qtyVc, vMaxLoss !== null)
      }
    ];
    $("proAllocationRows").innerHTML = tableRows.map((row) => {
      const c = statusClass(row.status);
      return '<tr><td>' + esc(row.name) + '<small>' + esc(row.sub) + '</small></td>' +
        '<td class="pro-number">' + esc(row.price) + '</td><td class="pro-number">' + esc(row.qty) + '</td>' +
        '<td class="pro-number">' + esc(row.exposure) + '</td><td class="pro-number">' + esc(row.credit) + '</td>' +
        '<td class="pro-number">' + esc(row.loss) + '</td><td class="pro-number">' + esc(row.navPct) + '</td>' +
        '<td class="' + c + '">' + esc(row.status.replace(/<[^>]*>/g, "")) + '</td></tr>';
    }).join("");

    $("proCapacityGrid").innerHTML =
      card("QQQ CORE SHARES", qtyQ === null ? "PENDING" : fmt(qtyQ), "shares · max capacity",
        ['<b>' + esc(capQNotional === null ? "—" : exactUsd(capQNotional)) + '</b> notional', esc(pct(ratioPct(capQNotional, nav))) + ' NAV'],
        qtyQ === null ? "pending" : "ready") +
      card("VXX SHORT STOCK", qtyV === null ? "PENDING" : fmt(qtyV), "shares short · max capacity",
        ['<b>' + esc(capVNotional === null ? "—" : exactUsd(capVNotional)) + '</b> notional', '<b>' + esc(capVMargin === null ? "—" : exactUsd(capVMargin)) + '</b> estimated margin'],
        qtyV === null ? "pending" : "ready") +
      card("QQQ CALL-CREDIT", qtyQc === null ? "PENDING" : fmt(qtyQc), "spreads · max capacity",
        ['<b>' + esc(qMaxLoss === null ? "—" : exactUsd(qMaxLoss)) + '</b> max loss', '<b>' + esc(qTotalCredit === null ? "—" : exactUsd(qTotalCredit)) + '</b> estimated credit', esc(qCandidate ? qStrikes + " · " + expiryQ : "Load QQQ call quote")],
        qtyQc === null ? "pending" : "ready") +
      card("VXX CALL-CREDIT", qtyVc === null ? "PENDING" : fmt(qtyVc), "spreads · max capacity",
        ['<b>' + esc(vMaxLoss === null ? "—" : exactUsd(vMaxLoss)) + '</b> max loss', '<b>' + esc(vTotalCredit === null ? "—" : exactUsd(vTotalCredit)) + '</b> estimated credit', esc(vCandidate ? vStrikes + " · " + expiryV : "Load VXX call quote")],
        qtyVc === null ? "pending" : "ready");

    const totalStockText = stockNotional === null ? "PENDING" : exactUsd(stockNotional);
    const totalRiskText = qMaxLoss === null && vMaxLoss === null ? "PENDING" : exactUsd(knownOptionRisk);
    $("proTotalsRow").innerHTML =
      '<span>MAX STOCK NOTIONAL<b>' + esc(totalStockText) + '</b></span>' +
      '<span>OPTION MAX LOSS @ CAPACITY<b>' + esc(totalRiskText) + '</b></span>' +
      '<span>PLANNED CAPITAL REQUIRED<b>' + esc(capitalRequired === null ? "PENDING" : exactUsd(capitalRequired)) + '</b></span>' +
      '<span>UNALLOCATED CASH<b>' + esc(freeCash === null ? "PENDING" : exactUsd(freeCash)) + '</b></span>';
  }

  function renderPlan() {
    updateSlopeDisplay();
    syncHubResearchCandidates();
    const input = readInput();
    // Manual edits make the source explicit rather than silently preserving a stale V3 provenance tag.
    if (marketTouched) input.market.term_source = "MANUAL_OPERATOR_INPUT";
    const result = E.calculatePortfolio(input);
    lastPlan = { generatedAt: new Date().toISOString(), input, result, candidates };
    renderProDashboard(result, input);
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
      const exposureEl = $("exposure-" + r.key);
      if (exposureEl) exposureEl.textContent = usd(r.targetNotionalUsd);
      const capitalEl = $("capital-" + r.key);
      if (capitalEl) capitalEl.textContent = usd(r.incrementalCapitalUsd);
    }

    for (const r of result.rows.filter(row => E.OPTION_STRATEGIES.some(s => s.key === row.key))) {
      $("capacity-" + r.key).textContent = r.status === "OUTSIDE_MAIN_BUDGET" ? "EXCLUDED" : r.capacity === null || r.capacity === undefined ? "PENDING" : fmt(r.capacity);
      $("target-" + r.key).textContent = r.status === "OUTSIDE_MAIN_BUDGET" ? "—" : r.target === null || r.target === undefined ? "PENDING" : fmt(r.target);
      $("action-" + r.key).textContent = r.status === "OUTSIDE_MAIN_BUDGET" ? "OUTSIDE MAIN BUDGET" : r.action + (r.delta ? " " + signed(r.delta) : "");
      $("action-" + r.key).className = "action-cell " + String(r.action || "").toLowerCase();
      $("reason-" + r.key).textContent = r.reason || "";
      $("reason-" + r.key).title = r.reason || "";
      const riskEl = $("risk-" + r.key);
      if (riskEl && riskEl.tagName !== "INPUT") {
        riskEl.textContent = r.riskPerUnit === null || r.riskPerUnit === undefined ? "—" : usd(r.riskPerUnit);
      }
      const sourceEl = $("source-" + r.key);
      if (sourceEl) sourceEl.textContent = r.candidateSource || r.riskSource || r.status;
      const allocatedEl = $("allocated-" + r.key);
      if (allocatedEl) allocatedEl.textContent = r.status === "OUTSIDE_MAIN_BUDGET" ? "EXCLUDED" : r.allocatedRiskBudgetUsd > 0 ? usd(r.allocatedRiskBudgetUsd) : (r.status === "PENDING" ? "PENDING" : "$0");
      const reservedEl = $("reserved-" + r.key);
      if (reservedEl) reservedEl.textContent = r.status === "OUTSIDE_MAIN_BUDGET" ? "EXCLUDED" : r.strategyKind === "coveredCall" || r.riskPerUnit === null || r.riskPerUnit === undefined || r.target === null ? "N/A / PENDING" : usd(r.riskPerUnit * r.target);
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
      ["NAV / uncommitted cash", usd(result.nav) + " / " + usd(result.cashPool)],
      ["Cash reserve", usd(result.cashReserveUsd)],
      ["Shared option-risk envelope", usd(result.totalOptionRiskPool)],
      ["Quoted primary short-option requests", usd(result.totalRequestedRiskBudgetsUsd)],
      ["Common proportional scale factor", Number.isFinite(result.riskScaleFactor) ? fmt(result.riskScaleFactor, 3) + "×" : "—"],
      ["Risk still unused after integer sizing", usd(result.remainingRiskPool)],
      ["QQQ target notional", usd(result.qqqTargetNotionalUsd)],
      ["VXX target short notional", usd(result.vxxTargetNotionalUsd)],
      ["VXX target margin estimate", usd(result.vxxTargetMarginUsd)],
      ["Known option loss at targets", result.optionRiskReservedAtTargets == null ? "PENDING / BLOCKED" : usd(optionRiskAtTargets)],
      ["Capital required for planned adds + reserves", usd(result.plannedCapitalRequiredUsd)],
      ["Unallocated cash after plan", usd(result.remainingUnallocatedCashUsd)],
      ["Sizing status", result.ok ? "CALCULATED / REVIEW" : "BLOCKED"]
    ].map(([k,v]) => '<div><small>' + esc(k) + '</small><b>' + esc(v) + '</b></div>').join("");
    $("summaryReasons").innerHTML = '<p><b>Why:</b> ' + esc(m.reason) + '</p>' +
      '<p><b>Main budget scope:</b> QQQ core shares + VXX short-stock margin + QQQ call-credit + VXX call-credit only. VXX put and all other catalogue structures are excluded from the primary plan.</p>' +
      '<p><b>Capital accounting:</b> planned cash = reserve + shared primary seller-option risk envelope + incremental QQQ purchases + estimated margin for incremental VXX short shares. Existing shares are not counted as fresh purchases.</p>' +
      '<p><b>Risk boundary:</b> VXX margin is a user-entered estimate, not a loss cap. VXX put and other research rows receive no primary capacity or risk reservation.</p>';
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
      cashReservePct:p.cashReservePct, vxxShortMarginMultiple:p.vxxShortMarginMultiple,
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
    $("findHubResearchBtn").addEventListener("click", findHubResearchCandidates);
    document.querySelectorAll("[data-find]").forEach(btn => {
      btn.dataset.label = btn.textContent;
      btn.addEventListener("click", () => findCandidate(btn));
    });
    document.querySelectorAll("input,select").forEach(el => {
      if (el.id.startsWith("current-") || el.id.startsWith("budget-") || el.id.startsWith("risk-") || el.id.startsWith("enabled-") ||
          ["mQqq","mVxx","mVix","mM1","mM2","mSpotAsOf","mTermAsOf","mToday","nav","cashPool","cashReservePct","vxxShortMarginMultiple","qqqCorePct","vxxNormalPct","vxxHighPct","totalOptionRiskPct","vixHigh","termSafe","maxTermAgeDays","nxEnabled","nxCurrentFar","nxCurrentNear","nxFarDelta","nxNearDelta","nxCoverage","nxMaxStack","nxNShort","nxFarDistancePct","nxGammaRel","nxDeltaJump","allowProtectionBuys","targetDte","hubRatioN","hubStateLayerCap","hubDrawdown252Pct","hubReturn5dPct"].includes(el.id)) {
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
