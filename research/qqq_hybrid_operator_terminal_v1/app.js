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
  const OPTION_HANDOFF_PREFIX = "QQQ_HYBRID_PRIMARY_OPTION_CANDIDATE_V1:";
  const OPTION_HANDOFF_SLOTS = Object.freeze({ QQQ_CALL: "qqqCall", VXX_CALL: "vxxCall" });
  const STOCK_KEYS = ["qqqShares", "vxxShortShares"];
  const PositionLedger = window.PositionLedgerV1;
  const PositionManagement = window.PositionManagementV1;
  const DeploymentRoadmap = window.DeploymentRoadmapV1;
  const DecisionValueEngine = window.DecisionValueEngineV1;
  const DECISION_VALUE_STORAGE_KEY = "QQQ_HYBRID_DECISION_VALUE_V1";
  const DEPLOYMENT_STORAGE_KEY = "QQQ_HYBRID_DEPLOYMENT_ROADMAP_V1";
  let positionRecords = [];
  let positionRegisterSummary = null;
  let manualHoldingsBeforeRegister = null;
  let positionStorageNotice = "";

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
          ? '<span id="budget-display-' + s.key + '" class="muted budget-display">' + fmt(budget, 1) + '% NAV · configured above</span>'
          : '<span class="tag">OUTSIDE MAIN BUDGET</span>') + '</td>' +
        '<td id="allocated-' + s.key + '">—</td>' +
        '<td>' + riskCell + '</td>' +
        '<td>' + enableCell + '</td>' +
        '<td id="capacity-' + s.key + '">—</td><td id="target-' + s.key + '">—</td><td id="reserved-' + s.key + '">—</td><td id="action-' + s.key + '">—</td>' +
      '</tr>';
    }).join("");
    for (const [key, id] of Object.entries(TOP_BUDGETS)) {
      const display = $("budget-display-" + key);
      const updateDisplay = () => {
        if (display) display.textContent = fmt(inputNumber(id, 0), 1) + "% NAV · configured above";
      };
      updateDisplay();
      $(id).addEventListener("input", () => { updateDisplay(); renderPlan(); });
    }
  }

  function syncBudgetInputsFromProfile() {
    for (const [key, id] of Object.entries(TOP_BUDGETS)) {
      const display = $("budget-display-" + key);
      if (display) display.textContent = fmt(inputNumber(id, 0), 1) + "% NAV · configured above";
    }
    renderPlan();
  }

  function toggleResearchRows() {
    const wrap = $("optionTableWrap");
    const button = $("toggleResearchRows");
    if (!wrap || !button) return;
    const shown = wrap.classList.toggle("show-research-rows");
    const count = E.OPTION_STRATEGIES.filter(s => !s.mainBudgetEligible).length;
    button.setAttribute("aria-expanded", String(shown));
    button.textContent = shown ? "Hide " + count + " research-only rows" : "Show " + count + " research-only rows";
  }


  function loadPositionRecords() {
    if (!PositionLedger) {
      positionStorageNotice = "Position register module failed to load. Manual current-quantity inputs remain active.";
      return;
    }
    try {
      const raw = localStorage.getItem(PositionLedger.STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      const list = Array.isArray(parsed) ? parsed : parsed && parsed.schema === PositionLedger.SCHEMA ? parsed.positions : null;
      const normalized = PositionLedger.normalizeList(list);
      if (!normalized.ok) {
        positionStorageNotice = "Saved register could not be loaded safely: " + normalized.errors.join(" ");
        positionRecords = [];
        return;
      }
      positionRecords = normalized.positions;
      positionStorageNotice = "Loaded " + positionRecords.length + " saved position record(s) from this browser.";
    } catch (error) {
      positionStorageNotice = "Saved register unavailable or invalid; no rows were guessed. " + (error instanceof Error ? error.message : String(error));
    }
  }

  function savePositionRecords() {
    try {
      localStorage.setItem(PositionLedger.STORAGE_KEY, JSON.stringify(PositionLedger.exportEnvelope(positionRecords)));
      positionStorageNotice = "Saved " + positionRecords.length + " position record(s) in this browser. Export JSON for a portable backup.";
      return true;
    } catch (error) {
      positionStorageNotice = "Browser storage failed; export the register JSON to preserve this snapshot. " + (error instanceof Error ? error.message : String(error));
      return false;
    }
  }

  const positionMoney = (value, signedValue = false) => {
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return "UNKNOWN";
    const n = Number(value);
    const sign = n < 0 ? "−" : signedValue && n > 0 ? "+" : "";
    return sign + "$" + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  function positionTemplate() {
    return PositionLedger.TEMPLATES[$("posTemplate").value] || PositionLedger.TEMPLATES.QQQ_CORE;
  }

  function updatePositionFormMode() {
    const template = positionTemplate();
    const isOption = template.kind === "CREDIT_VERTICAL";
    $("positionOptionFields").hidden = !isOption;
    $("positionOptionFields").querySelectorAll("input,select").forEach(el => { el.disabled = !isOption; });
    $("posMultiplier").value = isOption ? (Number($("posMultiplier").value) > 1 ? $("posMultiplier").value : template.multiplier) : 1;
    $("posMultiplier").readOnly = !isOption;
    $("posEntryPriceLabel").textContent = isOption ? "Entry net credit ($ / underlying share)" : "Average entry price ($ / share)";
    $("posMarkPriceLabel").textContent = isOption ? "Current estimated close debit ($ / underlying share)" : "Current mark ($ / share)";
    $("posMarkPrice").placeholder = isOption ? "Net exit debit; blank stays unknown" : "Blank uses the APP spot snapshot for attribution";
    $("posStopMarkLabel").textContent = isOption ? "Stop close debit ($ / share)" : "Stop mark ($ / share)";
    $("posTargetMarkLabel").textContent = isOption ? "Target close debit ($ / share)" : "Target mark ($ / share)";
    $("posStopMarkPrice").placeholder = template === "QQQ_CORE" ? "Below entry" : "Above entry / credit";
    $("posTargetMarkPrice").placeholder = template === "QQQ_CORE" ? "Above entry" : "Below entry / credit";
    $("positionSaveBtn").textContent = $("positionEditId").value ? "Save position changes" : "Add position record";
  }

  function readPositionDraft() {
    const template = $("posTemplate").value;
    const options = PositionLedger.TEMPLATES[template]?.kind === "CREDIT_VERTICAL";
    const rawNumber = id => $(id).value === "" ? null : Number($(id).value);
    return PositionLedger.normalizeRecord({
      id: $("positionEditId").value || undefined,
      template,
      qty: rawNumber("posQty"),
      entryDate: $("posEntryDate").value,
      entryPrice: rawNumber("posEntryPrice"),
      markPrice: rawNumber("posMarkPrice"),
      riskBudgetUsd: rawNumber("posRiskBudgetUsd"),
      stopMarkPrice: rawNumber("posStopMarkPrice"),
      targetMarkPrice: rawNumber("posTargetMarkPrice"),
      profitTargetR: rawNumber("posProfitTargetR"),
      maxHoldDays: rawNumber("posMaxHoldDays"),
      expiryReviewDte: rawNumber("posExpiryReviewDte"),
      markAsOf: $("posMarkAsOf").value,
      markSourceType: $("posMarkSourceType").value,
      markSourceNote: $("posMarkSourceNote").value.trim(),
      entryEvidence: $("posEntryEvidence").value,
      entrySourceNote: $("posEntrySourceNote").value.trim(),
      expiry: options ? $("posExpiry").value : "",
      shortStrike: options ? rawNumber("posShortStrike") : null,
      longStrike: options ? rawNumber("posLongStrike") : null,
      shortSymbol: options ? $("posShortSymbol").value.trim() : "",
      longSymbol: options ? $("posLongSymbol").value.trim() : "",
      multiplier: options ? rawNumber("posMultiplier") : 1,
      termsVerified: options && $("posTermsVerified").checked,
      deliverableNote: options ? $("posDeliverableNote").value.trim() : ""
    });
  }

  function resetPositionForm() {
    $("positionForm").reset();
    $("positionEditId").value = "";
    $("posQty").value = 1;
    $("posRiskBudgetUsd").value = "";
    $("posStopMarkPrice").value = "";
    $("posTargetMarkPrice").value = "";
    $("posProfitTargetR").value = "";
    $("posMaxHoldDays").value = "";
    $("posExpiryReviewDte").value = "";
    $("posMarkSourceType").value = "UNKNOWN";
    $("posEntryEvidence").value = "UNKNOWN";
    $("posTermsVerified").checked = false;
    $("positionCancelEditBtn").hidden = true;
    updatePositionFormMode();
    $("positionFormStatus").textContent = "Form reset. Existing registered position records remain unchanged.";
  }

  function fillPositionForm(record) {
    const set = (id, value) => { if ($(id)) $(id).value = value === null || value === undefined ? "" : String(value); };
    set("positionEditId", record.id);
    set("posTemplate", record.template);
    updatePositionFormMode();
    set("posQty", record.qty);
    set("posEntryDate", record.entryDate);
    set("posEntryPrice", record.entryPrice);
    set("posMarkPrice", record.markPrice);
    set("posRiskBudgetUsd", record.riskBudgetUsd);
    set("posStopMarkPrice", record.stopMarkPrice);
    set("posTargetMarkPrice", record.targetMarkPrice);
    set("posProfitTargetR", record.profitTargetR);
    set("posMaxHoldDays", record.maxHoldDays);
    set("posExpiryReviewDte", record.expiryReviewDte);
    set("posMarkAsOf", record.markAsOf);
    set("posMarkSourceType", record.markSourceType);
    set("posMarkSourceNote", record.markSourceNote);
    set("posEntryEvidence", record.entryEvidence);
    set("posEntrySourceNote", record.entrySourceNote);
    set("posExpiry", record.expiry);
    set("posShortStrike", record.shortStrike);
    set("posLongStrike", record.longStrike);
    set("posShortSymbol", record.shortSymbol);
    set("posLongSymbol", record.longSymbol);
    set("posMultiplier", record.multiplier);
    set("posDeliverableNote", record.deliverableNote);
    $("posTermsVerified").checked = record.termsVerified === true;
    $("positionCancelEditBtn").hidden = false;
    $("positionSaveBtn").textContent = "Save position changes";
    $("positionRegisterPanel").open = true;
    $("positionFormStatus").textContent = "Editing " + (PositionLedger.TEMPLATES[record.template]?.label || record.template) + ". Saving updates this browser record; it does not send orders.";
  }

  function managementContext(market, nav) {
    const state = E.assessMarket(market, {
      vixHigh: inputNumber("vixHigh", 28),
      termSafe: inputNumber("termSafe", 5),
      maxTermAgeDays: inputNumber("maxTermAgeDays", 4)
    });
    return { nav, today: market.today, marketState: state };
  }

  function measureRegisteredPositions(summary, market, nav) {
    if (!PositionManagement || !summary || !Array.isArray(summary.rows)) return [];
    const context = managementContext(market, nav);
    return summary.rows.map(row => ({
      id: row.id, label: row.label, template: row.template, qty: row.qty,
      pnl: row.unrealizedPnl, pnlStatus: row.pnlStatus, markFreshness: row.markFreshness,
      ...PositionManagement.evaluate(row, context)
    }));
  }

  function renderPositionLedger() {
    if (!PositionLedger) return;
    const market = readMarket();
    positionRegisterSummary = PositionLedger.summarize(positionRecords, market);
    const summary = positionRegisterSummary;
    const measuredRows = measureRegisteredPositions(summary, market, inputNumber("nav", 0));
    const managementById = new Map(measuredRows.map(row => [row.id, row]));
    const managementReviews = measuredRows.filter(row => !String(row.action || "").startsWith("MONITOR ")).length;
    $("positionLedgerHeadline").innerHTML =
      '<div><small>METADATA-COMPLETE P&amp;L SUBTOTAL</small><b>' + (summary.metadataCompletePnlRows ? esc(positionMoney(summary.metadataCompletePnlSubtotal, true)) : "—") + '</b><span>' + summary.metadataCompletePnlRows + ' metadata-complete row(s); indicative subtotal ' + esc(positionMoney(summary.indicativePnlSubtotal, true)) + ' across ' + summary.indicativePnlRows + ' row(s), excluded from metadata-complete total</span></div>' +
      '<div><small>INCOMPLETE P&amp;L ROWS</small><b>' + fmt(summary.incompletePnlCount) + '</b><span>Missing entry or mark; not assumed to be zero</span></div>' +
      '<div><small>MARK STATUS / SOURCE GAPS</small><b>' + fmt(summary.staleMarkCount) + ' flags · ' + fmt(summary.markSourceMetadataIncompleteCount) + ' gaps</b><span>Flags include missing/stale/invalid marks or unsupported source. Gaps mean UNKNOWN/MODEL_ESTIMATE or no reference on a known mark; counts may overlap.</span></div>' +
      '<div><small>HELD OPTION SIZING BLOCKS</small><b>' + fmt(summary.termBlockedCount) + '</b><span>Includes incomplete terms or adjusted payoffs the app cannot model</span></div>' +
      '<div><small>MANAGEMENT REVIEWS / INCOMPLETE PLANS</small><b>' + fmt(managementReviews) + '</b><span>Stop, loss budget, profit, regime, holding-time and expiry checks; no automatic orders</span></div>';

    $("positionLedgerTotals").innerHTML = [
      ["REGISTERED UNITS", fmt(summary.count)],
      ["QQQ SHARES", fmt(summary.holdings.qqqShares)],
      ["VXX SHORT SHARES", fmt(summary.holdings.vxxShortShares)],
      ["QQQ CALL-CREDIT", fmt(summary.holdings.qqqCallSpreads) + " spreads"],
      ["VXX CALL-CREDIT", fmt(summary.holdings.vxxCallSpreads) + " spreads"]
    ].map(([name, value]) => '<div><small>' + esc(name) + '</small><b>' + esc(value) + '</b></div>').join("");

    $("positionLedgerRows").innerHTML = summary.rows.length ? summary.rows.map(row => {
      const option = row.kind === "CREDIT_VERTICAL";
      const contractLine = option
        ? 'Exp ' + esc(row.expiry || "UNKNOWN") + ' · SHORT ' + esc(row.shortSymbol || ("K " + (row.shortStrike ?? "?"))) +
          ' / LONG ' + esc(row.longSymbol || ("K " + (row.longStrike ?? "?")))
        : esc(row.side + " · " + row.unit);
      const terms = option
        ? (row.adjustedDetected
            ? "BLOCKED · ADJUSTED PAYOFF UNSUPPORTED"
            : row.termsComplete ? "OPERATOR-ATTESTED TERMS" : "BLOCKED · TERMS INCOMPLETE")
          + (row.adjustedDetected ? " · ADJUSTED ROOT" : "")
        : esc(row.entryEvidence || "UNKNOWN ENTRY");
      const riskNote = option
        ? (row.adjustedDetected
            ? "Max loss UNKNOWN · adjusted deliverable payoff is not modeled"
            : row.maxLossPerPackage === null ? "Per-package max loss UNKNOWN" : "Entry max loss/package (assumed terms): " + positionMoney(row.maxLossPerPackage))
        : "";
      const pnlClass = row.unrealizedPnl === null ? "position-pnl-unknown" : row.unrealizedPnl < 0 ? "position-pnl-negative" : "position-pnl-positive";
      const meter = managementById.get(row.id) || {};
      const signedR = meter.pnlR === null || meter.pnlR === undefined ? "—" : (meter.pnlR > 0 ? "+" : "") + fmt(meter.pnlR, 2) + "R";
      const signedRDay = meter.rPerCalendarDay === null || meter.rPerCalendarDay === undefined ? "—" : (meter.rPerCalendarDay > 0 ? "+" : "") + fmt(meter.rPerCalendarDay, 3) + "R/day";
      const pnlDay = meter.pnlPerCalendarDay === null || meter.pnlPerCalendarDay === undefined ? "—" : positionMoney(meter.pnlPerCalendarDay, true) + " / calendar day";
      const pnlNav = meter.pnlPctNav === null || meter.pnlPctNav === undefined ? "—" : fmt(meter.pnlPctNav, 2) + "% NAV";
      const riskRate = meter.riskBudgetPctNav === null || meter.riskBudgetPctNav === undefined ? "UNKNOWN" : fmt(meter.riskBudgetPctNav, 2) + "% NAV";
      const lossToStop = meter.riskToStopUsd === null || meter.riskToStopUsd === undefined ? "—" : positionMoney(meter.riskToStopUsd);
      const rewardLeft = meter.targetRewardUsd === null || meter.targetRewardUsd === undefined ? "—" : positionMoney(meter.targetRewardUsd);
      const rr = meter.rewardRiskRatio === null || meter.rewardRiskRatio === undefined ? "—" : fmt(meter.rewardRiskRatio, 2) + ":1";
      const age = meter.elapsedCalendarDays === null || meter.elapsedCalendarDays === undefined ? "UNKNOWN AGE" :
        fmt(meter.elapsedCalendarDays) + (meter.maxHoldDays === null || meter.maxHoldDays === undefined ? " calendar days held" : " / " + fmt(meter.maxHoldDays) + " calendar days");
      const dteText = meter.dte === null || meter.dte === undefined ? "" : " · " + fmt(meter.dte) + " DTE";
      const managementHtml =
        '<small>P&amp;L pace: ' + esc(pnlDay) + ' · ' + esc(signedRDay) + ' · ' + esc(pnlNav) + '</small>' +
        '<small>P&amp;L / risk unit: ' + esc(signedR) + ' · risk budget ' + esc(riskRate) + ' (' + esc(meter.riskBudgetSource || "UNKNOWN") + ')</small>' +
        '<small>From current mark: loss-to-stop ' + esc(lossToStop) + ' · target reward left ' + esc(rewardLeft) + ' · reward/risk ' + esc(rr) + '</small>' +
        '<small>Time: ' + esc(age) + esc(dteText) + '</small>' +
        '<b class="position-management-action">' + esc(meter.action || "PENDING · MANAGEMENT METER UNAVAILABLE") + '</b>' +
        '<small>' + esc(meter.reason || "Required measurement is unavailable.") + '</small>';
      return '<tr>' +
        '<td><b>' + esc(row.label) + '</b><small>' + contractLine + '</small></td>' +
        '<td>' + esc(row.entryDate || "UNKNOWN") + '</td>' +
        '<td class="pro-number">' + esc(fmt(row.qty)) + ' ' + esc(row.unit) + '</td>' +
        '<td class="pro-number">' + esc(row.entryPrice === null ? "UNKNOWN" : positionMoney(row.entryPrice)) + '</td>' +
        '<td class="pro-number">' + esc(row.markPrice === null ? "UNKNOWN" : positionMoney(row.markPrice)) + (row.markDerivedFromSnapshot ? '<small>APP spot snapshot</small>' : '') + '</td>' +
        '<td class="' + pnlClass + '">' + esc(positionMoney(row.unrealizedPnl, true)) + '<small>' + esc(row.pnlStatus) + '</small>' + managementHtml + '</td>' +
        '<td>' + esc(row.markFreshness) + '<small>' + esc(row.markAsOf || "as-of missing") + '</small></td>' +
        '<td>' + esc(terms) + '<small>' + esc(riskNote) + '</small><small>Entry: ' + esc(row.entryEvidence || "UNKNOWN") + (row.entrySourceNote ? ' · ' + esc(row.entrySourceNote) : '') + '</small><small>Mark: ' + esc(row.markSourceType || "UNKNOWN") + (row.markSourceNote ? ' · ' + esc(row.markSourceNote) : '') + '</small></td>' +
        '<td><button type="button" data-position-action="edit" data-position-id="' + esc(row.id) + '">Edit</button> <button type="button" data-position-action="delete" data-position-id="' + esc(row.id) + '">Remove</button></td>' +
      '</tr>';
    }).join("") : '<tr><td colspan="9" class="pro-empty-cell">No position records yet. Manual Current Quantity inputs remain available.</td></tr>';

    if (summary.error) positionStorageNotice = "Register validation issue: " + summary.error;
    const active = $("positionUseRegister").checked && $("positionRegisterCompleteConfirmed").checked;
    $("positionRegisterModeStatus").textContent = (active
      ? "ACTIVE: registered quantities are the Current inputs for QQQ core, VXX short stock, QQQ call-credit and VXX call-credit. Any term block freezes only the affected option strategy."
      : "ATTRIBUTION ONLY: current quantities remain manual inputs until you enable register mode.") +
      (positionStorageNotice ? " · " + positionStorageNotice : "") +
      " · " + summary.note;
    const quantityFields = {
      qqqShares: "current-qqqShares", vxxShortShares: "current-vxxShortShares",
      qqqCallSpreads: "current-qqqCallSpreads", vxxCallSpreads: "current-vxxCallSpreads"
    };
    for (const [key, id] of Object.entries(quantityFields)) {
      const el = $(id);
      if (!el) continue;
      el.disabled = active;
      if (active) el.value = summary.holdings[key] || 0;
    }
  }

  function savePositionFromForm() {
    const draft = readPositionDraft();
    const verdict = PositionLedger.validateRecord(draft);
    if (!verdict.ok) {
      $("positionFormStatus").textContent = "Not saved: " + verdict.errors.join(" ");
      return;
    }
    const index = positionRecords.findIndex(row => row.id === draft.id);
    invalidatePositionRegisterCoverage("The position register changed.");
    draft.updatedAt = new Date().toISOString();
    if (index >= 0) positionRecords[index] = draft;
    else {
      draft.createdAt = new Date().toISOString();
      positionRecords.push(draft);
    }
    savePositionRecords();
    $("positionFormStatus").textContent = (index >= 0 ? "Position record updated. " : "Position record added. ") + positionStorageNotice;
    resetPositionForm();
    renderPlan();
  }


  function restoreManualPositionInputs() {
    if (!manualHoldingsBeforeRegister) return;
    for (const [id, value] of Object.entries(manualHoldingsBeforeRegister)) $(id).value = value;
    manualHoldingsBeforeRegister = null;
  }

  function invalidatePositionRegisterCoverage(reason) {
    $("positionRegisterCompleteConfirmed").checked = false;
    if ($("positionUseRegister").checked) {
      $("positionUseRegister").checked = false;
      restoreManualPositionInputs();
    } else {
      manualHoldingsBeforeRegister = null;
    }
    $("positionRegisterModeStatus").textContent = reason +
      " Register completeness confirmation has been cleared; re-check all four categories before switching it back into sizing.";
  }

  function handlePositionRegisterMode() {
    const use = $("positionUseRegister").checked;
    if (use && !$("positionRegisterCompleteConfirmed").checked) {
      $("positionUseRegister").checked = false;
      $("positionRegisterModeStatus").textContent = "Cannot use register for sizing until you confirm that all four primary position categories have been reviewed; omitted categories will be interpreted as zero.";
      return;
    }
    if (use && positionRecords.length === 0) {
      $("positionUseRegister").checked = false;
      $("positionRegisterModeStatus").textContent = "Cannot switch to register mode: add at least one verified-identity position record first. Use explicit manual inputs for a verified zero-holdings account.";
      return;
    }
    const ids = ["current-qqqShares", "current-vxxShortShares", "current-qqqCallSpreads", "current-vxxCallSpreads"];
    if (use) {
      manualHoldingsBeforeRegister = {};
      for (const id of ids) manualHoldingsBeforeRegister[id] = $(id).value;
    } else {
      restoreManualPositionInputs();
    }
    renderPlan();
  }

  function exportPositionRegister() {
    const payload = PositionLedger.exportEnvelope(positionRecords);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "qqq-hybrid-position-register-" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    $("positionFormStatus").textContent = "Position register exported. Keep this file as a portable backup; browser storage is device/browser-specific.";
  }

  async function importPositionRegister(file) {
    try {
      if (!file) return;
      if (positionRecords.length && !window.confirm("Replace the current browser position register with the imported records? Export a backup first if needed.")) return;
      const result = PositionLedger.parseEnvelope(await file.text());
      if (!result.ok) {
        $("positionFormStatus").textContent = "Import rejected without changing existing rows: " + result.errors.join(" ");
        return;
      }
      invalidatePositionRegisterCoverage("An imported register replaced the previous snapshot.");
      positionRecords = result.positions;
      const saved = savePositionRecords();
      $("positionFormStatus").textContent = "Imported " + positionRecords.length + " record(s). " + (saved ? "Saved locally." : "Local save failed; export a backup.");
      renderPlan();
    } catch (error) {
      $("positionFormStatus").textContent = "Import failed without changing existing rows: " + (error instanceof Error ? error.message : String(error));
    } finally {
      $("positionImportFile").value = "";
    }
  }

  function exportPositionRegisterJson() {
    if (!PositionLedger) throw new Error("Position register module unavailable.");
    exportPositionRegister();
  }

  function readMarket() {
    // This is an operational desk, not a historical replay UI. Never let a
    // snapshot or manually edited date make old quotes look fresh.
    const today = E.currentMarketDate(Date.now()) || "";
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
      vxxShortBorrowAprPct: E.num($("vxxShortBorrowAprPct")?.value, null),
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
      sizing[s.riskPctField] = s.mainBudgetEligible ? inputNumber(TOP_BUDGETS[s.key], s.defaultRiskPct) : 0;
      holdings[s.key] = inputNumber("current-" + s.key, 0);
      if (s.mainBudgetEligible && !s.baseline) permissions[s.key] = $("enabled-" + s.key)?.checked === true;
      if (["manualDebit", "manualRisk", "stressOnly"].includes(s.kind)) manualRiskPerUnit[s.key] = inputNumber("risk-" + s.key, null);
    }
    const currentMarket = readMarket();
    const positionSummary = PositionLedger ? PositionLedger.summarize(positionRecords, currentMarket) : null;
    const managementRows = measureRegisteredPositions(positionSummary, currentMarket, inputNumber("nav", 0));
    const usePositionRegister = $("positionUseRegister")?.checked === true && $("positionRegisterCompleteConfirmed")?.checked === true && positionRecords.length > 0 && positionSummary && !positionSummary.error;
    if (usePositionRegister) Object.assign(holdings, positionSummary.holdings);
    return {
      market: readMarket(),
      nav: inputNumber("nav", 0),
      cashPool: inputNumber("cashPool", 0),
      sizing, holdings, candidates, permissions, manualRiskPerUnit,
      positionRegister: positionSummary ? {
        useForSizing: usePositionRegister,
        completeConfirmed: $("positionRegisterCompleteConfirmed")?.checked === true,
        records: positionRecords,
        summary: positionSummary,
        managementRows,
        blockingKeys: usePositionRegister ? positionSummary.blockingKeys : []
      } : { useForSizing: false, records: [], blockingKeys: [] },
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
    setInput("mToday", E.currentMarketDate(Date.now()) || "");
    marketMeta = meta || [
      snapshot?.bridge_source || snapshot?.source_chain?.join(" → ") || "V3 snapshot",
      snapshot?.provenance ? JSON.stringify(snapshot.provenance) : "",
      snapshot?.bridge_retrieved_at || snapshot?.captured_at || ""
    ].filter(Boolean).join(" · ");
    renderPlan();
  }

  const premium = (value) => Number.isFinite(Number(value))
    ? "$" + Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : "—";
  function quoteWidthLabel(value, quality) {
    return Number.isFinite(Number(value)) ? Number(value).toFixed(1) + "% mid " + (quality || "UNKNOWN") : "UNKNOWN width";
  }

  function currentCandidateText(candidate) {
    if (!candidate) return "PENDING · no usable chain candidate";
    if (candidate.handoffSchema === "QQQ_HYBRID_PRIMARY_OPTION_CANDIDATE_V1") {
      const gate = E.validatePrimaryOptionHandoff(candidate);
      return candidate.contractRoot + " CALL-CREDIT · " + candidate.shortContractSymbol + " / " + candidate.longContractSymbol +
        " · expiry " + candidate.expiry + " · credit/share " + candidate.credit.toFixed(2) +
        " · max loss/spread $" + candidate.maxLossPerSpread.toFixed(2) +
        " · short spread/mid " + candidate.shortQuoteWidthPctMid.toFixed(1) + "% (" + candidate.shortQuoteQuality + ")" +
        " · wing spread/mid " + candidate.longQuoteWidthPctMid.toFixed(1) + "% (" + candidate.longQuoteQuality + ")" +
        " · operator observation " + candidate.quoteObservedAt + " (source timestamp not authenticated)" +
        " · HUMAN REVIEW ONLY · " + (gate.ok ? "MANUAL RISK INPUT" : "PENDING · " + gate.reason) + " · NO ORDERS";
    }
    if (candidate.hubPackage === true) {
      return "HUB QQQ package · " + (candidate.expiry || "expiry pending") +
        " · max-loss/risk " + usd(candidate.riskPerUnit) +
        " · debit " + usd(candidate.debitUsd) +
        (candidate.n ? " · Ratio N=" + candidate.n : "") +
        (candidate.maxUnits ? " · cap " + fmt(candidate.maxUnits) + " packages" : "") +
        " · " + (candidate.gatePass === false ? "ENTRY GATE OFF" : "risk candidate ready");
    }
    if (candidate.maxLossPerSpread !== undefined) {
      const shortLabel = candidate.shortContractSymbol || ("K " + fmt(candidate.shortStrike, 2));
      const longLabel = candidate.longContractSymbol || ("K " + fmt(candidate.longStrike, 2));
      const fetched = candidate.chainRetrievedAt
        ? " · chain fetched " + candidate.chainRetrievedAt + " (quote timestamp not verified)"
        : " · quote timestamp not verified";
      const termsWarning = candidate.contractTermsStatus === "ADJUSTED_DELIVERABLE_BLOCKED"
        ? " · ADJUSTED VXX ROOT DETECTED — CAPACITY BLOCKED"
        : " · deliverable/multiplier not broker-verified";
      const sizingWarning = candidate.sizingEvidence === "PUBLIC_CHAIN_SCENARIO_ONLY"
        ? " · SCENARIO ONLY — MAIN CAPACITY PENDING MANUAL SOURCE/TERMS REVIEW"
        : "";
      return candidate.right.toUpperCase() + " vertical · expiry " + candidate.expiry + " · " +
        fmt(candidate.dte) + " DTE · SHORT " + shortLabel + " Bid/Ask " +
        premium(candidate.shortBid) + "/" + premium(candidate.shortAsk) + " · width " +
        quoteWidthLabel(candidate.shortQuoteWidthPctMid, candidate.shortQuoteQuality) +
        " · WING " + longLabel + " Bid/Ask " + premium(candidate.longBid) + "/" + premium(candidate.longAsk) +
        " · width " + quoteWidthLabel(candidate.longQuoteWidthPctMid, candidate.longQuoteQuality) +
        " · credit/share " + premium(candidate.credit) + " · max loss/spread " + usd(candidate.maxLossPerSpread) +
        " (multiplier " + (candidate.multiplierAssumption || 100) + " assumed; not verified)" +
        fetched + termsWarning + sizingWarning + " · " + (candidate.chainSource || candidate.source || "source unknown");
    }
    return candidate.right.toUpperCase() + " long · " + candidate.expiry + " · " + fmt(candidate.dte) +
      " DTE · K " + fmt(candidate.strike, 2) + " · ask " + premium(candidate.ask) +
      " · width " + quoteWidthLabel(candidate.shortQuoteWidthPctMid, candidate.shortQuoteQuality) +
      " · " + (candidate.chainRetrievedAt ? "chain fetched " + candidate.chainRetrievedAt + " (quote time unverified)" : "quote time unverified") +
      " · " + (candidate.chainSource || candidate.source || "source unknown");
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

  function renderCandidateRows() {
    const present = Object.keys(candidates).filter(k => candidates[k]);
    $("candidateRows").innerHTML = present.map(k =>
      '<div class="candidate-row"><b>' + esc(k) + '</b><span>' + esc(currentCandidateText(candidates[k])) + '</span></div>'
    ).join("") || '<div class="empty">No usable candidates. Public/unverified chains remain scenario-only; missing evidence stays PENDING.</div>';
  }

  function restoreOptionCandidatesFromLocalStorage() {
    for (const chainKey of Object.keys(OPTION_HANDOFF_SLOTS)) {
      try {
        const raw = window.localStorage.getItem(OPTION_HANDOFF_PREFIX + chainKey);
        if (!raw) continue;
        const packet = JSON.parse(raw), gate = E.validatePrimaryOptionHandoff(packet);
        if (gate.ok && packet.chainKey === chainKey) candidates[OPTION_HANDOFF_SLOTS[chainKey]] = packet;
        else { candidates[OPTION_HANDOFF_SLOTS[chainKey]] = null; $("journalStatus").textContent = "Stored "+chainKey+" handoff is PENDING/BLOCKED: "+(gate.reason||"chain key mismatch"); }
      } catch (error) { candidates[OPTION_HANDOFF_SLOTS[chainKey]] = null; $("journalStatus").textContent = "Stored "+chainKey+" handoff could not be read; capacity remains PENDING."; }
    }
    renderCandidateRows();
  }

  function acceptOptionCandidatePacket(packet, expectedChainKey) {
    const chainKey = expectedChainKey || (packet && packet.chainKey), slot = OPTION_HANDOFF_SLOTS[chainKey];
    if (!slot) return;
    const gate = E.validatePrimaryOptionHandoff(packet);
    if (!gate.ok || packet.chainKey !== chainKey) {
      candidates[slot] = null;
      $("journalStatus").textContent = "Option Chain Lab handoff BLOCKED: " + (gate.reason || "chain key mismatch");
    } else {
      candidates[slot] = packet;
      $("journalStatus").textContent = "Loaded operator-attested "+chainKey+" candidate. HUMAN REVIEW ONLY; source authenticity and fills are not independently verified. No broker order was sent.";
    }
    renderCandidateRows();
    renderPlan();
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
      candidate.chainRetrievedAt = payload.retrieved_at || null;
      candidate.chainSource = payload.source || candidate.source || "SOURCE_UNSPECIFIED";
      candidate.quoteTimestampStatus = "UNVERIFIED — API fetch time is not an exchange quote timestamp";
      candidate.sizingEvidence = "PUBLIC_CHAIN_SCENARIO_ONLY";
      if (candidate.maxLossPerSpread !== undefined) {
        candidate.multiplierAssumption = 100;
        candidate.multiplierVerified = false;
      }
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
    const exactUsd = (value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) ? "$" + Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—";
    const pct = (value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) ? Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + "%" : "—";
    const ratioPct = (value, base) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) && Number(base) > 0 ? Number(value) / Number(base) * 100 : null;
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
    const borrowAprInput = E.num(input.sizing && input.sizing.vxxShortBorrowAprPct);
    const borrowApr = borrowAprInput !== null && borrowAprInput >= 0 && borrowAprInput <= 100 ? borrowAprInput : null;
    const vxxBorrowAnnualAtCapacity = borrowApr !== null && capVNotional !== null ? capVNotional * borrowApr / 100 : null;
    const vxxBorrowAnnualStressAtCapacity = vxxBorrowAnnualAtCapacity === null ? null : vxxBorrowAnnualAtCapacity * 1.5;
    const qRiskPerSpread = E.num(qCall.riskPerUnit);
    const vRiskPerSpread = E.num(vCall.riskPerUnit);
    const qMaxLoss = qtyQc !== null && qRiskPerSpread !== null ? qtyQc * qRiskPerSpread : null;
    const vMaxLoss = qtyVc !== null && vRiskPerSpread !== null ? qtyVc * vRiskPerSpread : null;
    const knownOptionRisk = (qMaxLoss === null ? 0 : qMaxLoss) + (vMaxLoss === null ? 0 : vMaxLoss);
    const knownOptionLegs = [qMaxLoss, vMaxLoss].filter((v) => v !== null).length;
    const pool = Number.isFinite(Number(result.totalOptionRiskPool)) ? Number(result.totalOptionRiskPool) : null;
    const usedPct = pool > 0 ? Math.min(100, knownOptionRisk / pool * 100) : 0;
    const optionRiskKpiValue = knownOptionLegs === 2
      ? usd(knownOptionRisk)
      : knownOptionLegs === 1 ? "PARTIAL · " + usd(knownOptionRisk) : "PENDING";
    const optionRiskKpiDetail = knownOptionLegs === 2
      ? (pool !== null ? pct(ratioPct(knownOptionRisk, nav)) + " NAV · " + pct(usedPct) + " of shared pool" : "Waiting for risk pool")
      : knownOptionLegs === 1
        ? "Known leg only · other call-credit leg PENDING; no combined total"
        : "Waiting for two valid call-credit quotes";
    const stockNotional = capQNotional !== null && capVNotional !== null ? capQNotional + capVNotional : null;
    const capitalRequired = E.num(result.plannedCapitalRequiredUsd);
    const freeCash = E.num(result.remainingUnallocatedCashUsd);
    const currentTargetRisk = E.num(result.optionRiskReservedAtTargets);
    const calcStatus = $("proCalcStatus");
    calcStatus.textContent = result.market.blocked ? "BLOCKED · REFRESH / VERIFY DATA" :
      result.market.state + (result.market.allowNew ? " · MARKET GATE PASSED — HUMAN REVIEW ONLY" : " · HOLD / REDUCE RULES");
    calcStatus.className = "pro-status " + (result.market.blocked ? "bad" : result.market.state === "CARRY" ? "good" : "warn");

    $("proKpis").innerHTML = [
      ["PORTFOLIO NAV", usd(nav), "NAV basis for all allocation percentages"],
      ["MAX STOCK NOTIONAL", stockNotional === null ? "PENDING" : exactUsd(stockNotional), stockNotional === null ? "Await valid market prices" : pct(ratioPct(stockNotional, nav)) + " of NAV · QQQ + VXX short"],
      ["MAX OPTION LOSS", optionRiskKpiValue, optionRiskKpiDetail],
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
      { label: "Unused after rounding", amount: knownOptionLegs === 2 && pool !== null ? Math.max(0, pool - knownOptionRisk) : null, max: pool, cls: "" }
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
    const qRewardRiskPct = qCandidate && Number.isFinite(Number(qCandidate.maxLossPerSpread)) && Number(qCandidate.maxLossPerSpread) > 0 && qCreditPerSpread !== null
      ? qCreditPerSpread * 100 / Number(qCandidate.maxLossPerSpread) * 100 : null;
    const vRewardRiskPct = vCandidate && Number.isFinite(Number(vCandidate.maxLossPerSpread)) && Number(vCandidate.maxLossPerSpread) > 0 && vCreditPerSpread !== null
      ? vCreditPerSpread * 100 / Number(vCandidate.maxLossPerSpread) * 100 : null;
    const qBreakEven = qCandidate && E.num(qCandidate.shortStrike) !== null && qCreditPerSpread !== null ? E.num(qCandidate.shortStrike) + qCreditPerSpread : null;
    const vBreakEven = vCandidate && E.num(vCandidate.shortStrike) !== null && vCreditPerSpread !== null ? E.num(vCandidate.shortStrike) + vCreditPerSpread : null;
    const qStrikes = qCandidate ? fmt(qCandidate.shortStrike, 2) + "C / " + fmt(qCandidate.longStrike, 2) + "C" : "Quote pending";
    const vStrikes = vCandidate ? fmt(vCandidate.shortStrike, 2) + "C / " + fmt(vCandidate.longStrike, 2) + "C" : "Quote pending";
    const expiryQ = qCandidate && qCandidate.expiry ? qCandidate.expiry : "same-expiry quote needed";
    const expiryV = vCandidate && vCandidate.expiry ? vCandidate.expiry : "same-expiry quote needed";
    const statusOf = (row, quantity, priceKnown) => {
      if (result.market.blocked) return "BLOCKED · MARKET DATA";
      if (row.action === "BLOCKED" || String(row.status || "").startsWith("BLOCKED")) return "BLOCKED · SEE REASON";
      if (quantity === null || !priceKnown) return "QUOTE / DATA PENDING";
      return esc(row.action) + " · REVIEW";
    };
    const statusClass = (text) => /PENDING|BLOCKED/.test(text) ? "pro-warn" : /ADD|READY|REVIEW/.test(text) ? "pro-good" : "pro-muted";
    const tableRows = [
      {
        name: "QQQ Core Shares", sub: "Equity allocation cap",
        price: result.market.blocked ? "PENDING" : exactUsd(result.market.qqq) + " / share",
        qty: displayQty(qqq, "shares"),
        exposure: capQNotional === null ? "PENDING" : exactUsd(capQNotional) + " notional",
        credit: "—", creditDetail: "", loss: "—",
        navPct: capQNotional === null ? "PENDING" : pct(ratioPct(capQNotional, nav)),
        status: statusOf(qqq, qtyQ, capQNotional !== null)
      },
      {
        name: "VXX Short Stock", sub: "Notional limit · short stock has uncapped upside risk",
        price: result.market.blocked ? "PENDING" : exactUsd(result.market.vxx) + " / share",
        qty: displayQty(vxx, "short shares"),
        exposure: capVNotional === null || capVMargin === null ? "PENDING" : exactUsd(capVNotional) + " notional · " + exactUsd(capVMargin) + " margin",
        credit: "—", creditDetail: "", loss: "Unbounded",
        navPct: capVNotional === null || capVMargin === null ? "PENDING" : pct(ratioPct(capVNotional, nav)) + " notional / " + pct(ratioPct(capVMargin, nav)) + " margin",
        status: statusOf(vxx, qtyV, capVMargin !== null)
      },
      {
        name: "QQQ Call-Credit", sub: "Short call + long wing · " + expiryQ,
        price: qCandidate ? qStrikes : "Quote pending",
        qty: qtyQc === null ? "PENDING" : fmt(qtyQc) + " spreads",
        exposure: qMaxLoss === null ? "PENDING" : exactUsd(qMaxLoss) + " max-loss exposure",
        credit: qTotalCredit === null ? "PENDING" : exactUsd(qTotalCredit),
        creditDetail: qTotalCredit === null ? "Quote / capacity pending" : pct(ratioPct(qTotalCredit, nav)) + " of NAV · max-capacity estimate; max profit / max loss " + pct(qRewardRiskPct) + "; expiry breakeven " + (qBreakEven === null ? "PENDING" : exactUsd(qBreakEven) + "/share") + " before fees",
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
        creditDetail: vTotalCredit === null ? "Quote / capacity pending" : pct(ratioPct(vTotalCredit, nav)) + " of NAV · max-capacity estimate; max profit / max loss " + pct(vRewardRiskPct) + "; expiry breakeven " + (vBreakEven === null ? "PENDING" : exactUsd(vBreakEven) + "/share") + " before fees",
        loss: vMaxLoss === null ? "PENDING" : exactUsd(vMaxLoss),
        navPct: vMaxLoss === null ? "PENDING" : pct(ratioPct(vMaxLoss, nav)),
        status: statusOf(vCall, qtyVc, vMaxLoss !== null)
      }
    ];
    $("proAllocationRows").innerHTML = tableRows.map((row) => {
      const c = statusClass(row.status);
      return '<tr><td>' + esc(row.name) + '<small>' + esc(row.sub) + '</small></td>' +
        '<td class="pro-number">' + esc(row.price) + '</td><td class="pro-number">' + esc(row.qty) + '</td>' +
        '<td class="pro-number">' + esc(row.exposure) + '</td><td class="pro-number">' + esc(row.credit) + (row.creditDetail ? '<small>' + esc(row.creditDetail) + '</small>' : '') + '</td>' +
        '<td class="pro-number">' + esc(row.loss) + '</td><td class="pro-number">' + esc(row.navPct) + '</td>' +
        '<td class="' + c + '">' + esc(row.status.replace(/<[^>]*>/g, "")) + '</td></tr>';
    }).join("");

    $("proCapacityGrid").innerHTML =
      card("QQQ CORE SHARES", qtyQ === null ? "PENDING" : fmt(qtyQ), "shares · max capacity",
        ['<b>' + esc(capQNotional === null ? "—" : exactUsd(capQNotional)) + '</b> notional', esc(pct(ratioPct(capQNotional, nav))) + ' NAV'],
        qtyQ === null ? "pending" : "ready") +
      card("VXX SHORT STOCK", qtyV === null ? "PENDING" : fmt(qtyV), "shares short · max capacity",
        ['<b>' + esc(capVNotional === null ? "—" : exactUsd(capVNotional)) + '</b> notional', '<b>' + esc(capVMargin === null ? "—" : exactUsd(capVMargin)) + '</b> estimated margin',
          vxxBorrowAnnualAtCapacity === null
            ? "Annual borrow cost PENDING · valid APR required"
            : "Borrow est. " + exactUsd(vxxBorrowAnnualAtCapacity) + "/year at " + pct(borrowApr) + " APR · 1.5× stress " + exactUsd(vxxBorrowAnnualStressAtCapacity)],
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


  function localCalendarDate() {
    const d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0");
  }
  function optionalNumber(id) {
    const raw = String($(id)?.value ?? "").trim();
    if (!raw) return null;
    const value = Number(raw);
    return Number.isFinite(value) ? value : null;
  }
  function readRoadmapSettings() {
    return { baseCapitalUsd: optionalNumber("planBaseCapital"), startDate: String($("planStartDate")?.value || ""),
      horizonMonths: optionalNumber("planHorizonMonths"), monthlyContributionUsd: optionalNumber("planMonthlyContribution") };
  }
  function persistRoadmapSettings() {
    try { window.localStorage.setItem(DEPLOYMENT_STORAGE_KEY, JSON.stringify(readRoadmapSettings())); }
    catch (_) { const status=$("deploymentRoadmapStatus"); if(status){status.textContent="LOCAL SAVE UNAVAILABLE";status.className="tag warn";} }
  }
  function restoreRoadmapSettings() {
    try {
      const raw=window.localStorage.getItem(DEPLOYMENT_STORAGE_KEY); if(!raw)return;
      const saved=JSON.parse(raw); if(!saved||typeof saved!=="object"||Array.isArray(saved))return;
      if(saved.baseCapitalUsd!==undefined&&saved.baseCapitalUsd!==null)$("planBaseCapital").value=String(saved.baseCapitalUsd);
      if(typeof saved.startDate==="string")$("planStartDate").value=saved.startDate;
      if(saved.horizonMonths!==undefined&&saved.horizonMonths!==null)$("planHorizonMonths").value=String(saved.horizonMonths);
      if(saved.monthlyContributionUsd!==undefined&&saved.monthlyContributionUsd!==null)$("planMonthlyContribution").value=String(saved.monthlyContributionUsd);
    } catch (_) { const status=$("deploymentRoadmapStatus"); if(status){status.textContent="SAVED PLAN INVALID · REVIEW INPUTS";status.className="tag warn";} }
  }
  function renderDeploymentRoadmap(result) {
    if(!DeploymentRoadmap||typeof DeploymentRoadmap.evaluate!=="function")return null;
    const settings=readRoadmapSettings();
    const output=DeploymentRoadmap.evaluate({...settings,currentNavUsd:optionalNumber("nav"),currentCashUsd:optionalNumber("cashPool"),today:localCalendarDate(),market:result.market});
    const usdOrPending=v=>typeof v==="number"&&Number.isFinite(v)?"$"+v.toLocaleString("en-US",{minimumFractionDigits:0,maximumFractionDigits:0}):"PENDING";
    const percentOrPending=v=>typeof v==="number"&&Number.isFinite(v)?v.toLocaleString("en-US",{minimumFractionDigits:1,maximumFractionDigits:1})+"%":"PENDING";
    const labels={BASELINE_PENDING:"PENDING · NEED INPUT",NEEDS_PAYOFF:"PENDING · PAYOFF / COST / TIME MISSING",NEEDS_PROBABILITY:"PENDING · PROBABILITY / SAMPLE MISSING",INVALID_RANGE:"BLOCK · PROBABILITY RANGE INVALID",MARKET_BLOCKED:"BLOCK · MARKET DATA GATE",CLOCK_FLOOR_BREACH:"BLOCK · CLOCK FLOOR BREACH",ADD_NOT_ALLOWED:"BLOCK · CURRENT APP TARGET / MARKET GATE",QTY_OVER_TARGET:"BLOCK · PROPOSED UNITS EXCEED ADD GAP",PORTFOLIO_STRESS_PENDING:"PENDING · COMMON PORTFOLIO STRESS",PORTFOLIO_STRESS_INVALID:"BLOCK · COMMON STRESS INPUT INVALID",PORTFOLIO_TAIL_REVIEW:"HUMAN REVIEW · VXX SHORT TAIL",PORTFOLIO_STRESS_REVIEW:"HUMAN REVIEW · STRESS > 5% NAV",COMPARATOR_CONTRACT_PENDING:"PENDING · COMPARATOR BASIS",ALTERNATIVE_NOT_COMPARABLE:"BLOCK · ALTERNATIVE NOT COMPARABLE",GENERALITY_PENDING:"PENDING · GENERALITY DOSSIER",POSITION_REVIEW_PRIORITY:"HOLD REVIEW · POSITION-SPECIFIC GATE FIRST",HOLD_CONFLICTS_WITH_REDUCE:"FOLLOW REDUCE ROUTE · HOLD EV CANNOT OVERRIDE",QQQ_OVERLAY_LOCKBOX:"RESEARCH BLOCK · FAR CALL OVERLAY FAILED CURRENT SCREEN",MODEL_ONLY:"MODEL ONLY · NOT TRADE-READY",HYPOTHESIS_ONLY:"SCENARIO ONLY · PROBABILITY NOT EVIDENCED",EVIDENCE_INCOMPLETE:"PENDING · ACCURACY / GENERALITY / INTEGRATION",ALTERNATIVE_VALUE_PENDING:"PENDING · ALTERNATIVE NOT PRICED",NEGATIVE_INCREMENTAL_VALUE:"WAIT / ALTERNATIVE WINS · NON-POSITIVE DELTA",NEGATIVE_EXPECTED_VALUE:"WAIT / NO ADD · BASE EV NON-POSITIVE",FRAGILE_EXPECTED_VALUE:"FRAGILE · ADVERSE EV NON-POSITIVE",UNBOUNDED_TAIL:"SCENARIO ONLY · UNBOUNDED / STRESS RISK",NO_SIZING_ROUTE:"SCENARIO ONLY · NO PRIMARY CAPACITY ROUTE",ELIGIBLE_FOR_HUMAN_REVIEW:"ELIGIBLE FOR HUMAN REVIEW · NO ORDER"};
    const status=$("deploymentRoadmapStatus");
    if(status){status.textContent=labels[output.status]||"PENDING";status.className=output.status==="CARRY_HUMAN_REVIEW"?"tag active":["FLOOR_BREACH","DEFENSIVE_REVIEW"].includes(output.status)?"tag danger":"tag warn";}
    $("deploymentRoadmapHeadline").textContent=output.nextAction||"路線圖待確認。";
    const monthText=output.elapsedMonths===null||output.elapsedMonths===undefined?"PENDING":output.elapsedMonths+" / "+output.horizonMonths+" months";
    const remainingText=output.remainingMonths===null||output.remainingMonths===undefined?"PENDING":output.remainingMonths+" months · "+percentOrPending(output.completionPct)+" complete";
    const floorText=output.floorUsd===null||output.floorUsd===undefined?"PENDING":usdOrPending(output.currentNavUsd)+" / "+usdOrPending(output.floorUsd);
    const gapText=output.floorGapUsd===null||output.floorGapUsd===undefined?"Need confirmed baseline":(output.floorGapUsd>=0?"+":"−")+usdOrPending(Math.abs(output.floorGapUsd))+" vs floor";
    const contribText=output.plannedFutureContributionsUsd===null||output.plannedFutureContributionsUsd===undefined?"PENDING":usdOrPending(output.plannedFutureContributionsUsd);
    $("deploymentRoadmapMetrics").innerHTML=[
      ["STARTING CAPITAL B",usdOrPending(output.baseCapitalUsd),output.startDate?"Since "+output.startDate:"Original baseline date required"],
      ["CURRENT NAV / CLOCK FLOOR",floorText,gapText],
      ["HORIZON REMAINING",remainingText,"Progress "+monthText],
      ["PLANNED FUTURE CONTRIBUTIONS",contribText,"Not spendable today; confirm when settled"]
    ].map(([label,value,detail])=>'<div class="roadmap-metric"><small>'+esc(label)+'</small><b>'+esc(value)+'</b><span>'+esc(detail)+'</span></div>').join("");
    return {schema:"QQQ_HYBRID_DEPLOYMENT_ROADMAP_V1",...output,settings,currentNavUsd:optionalNumber("nav"),currentCashUsd:optionalNumber("cashPool"),
      generatedAt:new Date().toISOString(),brokerOrders:false,forecastedCagr:null,forecastedMaxDrawdown:null};
  }
  function lockRoadmapBaseline() {
    const nav=optionalNumber("nav");
    if(nav===null||nav<=0){$("deploymentRoadmapHeadline").textContent="無法鎖定：請先在 Principal / Capital 區輸入已核實且大於 $0 的 NAV。";return;}
    $("planBaseCapital").value=String(nav);$("planStartDate").value=localCalendarDate();persistRoadmapSettings();renderPlan();
    $("journalStatus").textContent="已把目前輸入 NAV 與今天鎖為本機長期路線圖基準；這是人工確認的規劃基準，並非券商核實。";
  }
  function clearRoadmapBaseline() {
    $("planBaseCapital").value="";$("planStartDate").value="";persistRoadmapSettings();renderPlan();
    $("journalStatus").textContent="長期基準已清除；路線圖回到 PENDING，不會改動 NAV、倉位或策略規則。";
  }


  const DECISION_INPUT_IDS=["dvCandidate","dvLens","dvQuantity","dvHorizonDays","dvRewardUsd","dvLossUsd","dvCostUsd","dvCostStressUsd","dvRiskNature","dvAlternativeEVTotalUsd","dvAlternativeLabel","dvCandidateCapitalUsd","dvAlternativeCapitalUsd","dvCandidateRiskBudgetUsd","dvAlternativeRiskBudgetUsd","dvAlternativeHorizonDays","dvAlternativeCostsIncluded","dvProbabilityMethod","dvProbLowPct","dvProbBasePct","dvProbHighPct","dvWins","dvTrials","dvProbabilityBasis","dvAccuracy","dvGenerality","dvIntegration","dvEvidenceNote","dvGeneralityDossierJson","dvStressScenarioName","dvStressSourceNote","dvStressQqqCoreState","dvStressQqqCoreLoss","dvStressVxxShortState","dvStressVxxShortLoss","dvStressQqqCallState","dvStressQqqCallLoss","dvStressVxxCallState","dvStressVxxCallLoss","dvStressReconciled"];
  function readDecisionValueInputs(){
    const n=id=>{const raw=String($(id)?.value??"").trim();if(!raw)return null;const v=Number(raw);return Number.isFinite(v)?v:null;};
    const portfolioStress={scenarioName:String($("dvStressScenarioName").value||"").trim(),sourceNote:String($("dvStressSourceNote").value||"").trim(),reconciled:$("dvStressReconciled").checked,legs:{qqqCore:{state:$("dvStressQqqCoreState").value,stressLossUsd:n("dvStressQqqCoreLoss")},vxxShort:{state:$("dvStressVxxShortState").value,stressLossUsd:n("dvStressVxxShortLoss")},qqqCallCredit:{state:$("dvStressQqqCallState").value,stressLossUsd:n("dvStressQqqCallLoss")},vxxCallCredit:{state:$("dvStressVxxCallState").value,stressLossUsd:n("dvStressVxxCallLoss")}}};
    return {candidateKey:$("dvCandidate").value,lens:$("dvLens").value,quantity:n("dvQuantity"),horizonDays:n("dvHorizonDays"),rewardUsd:n("dvRewardUsd"),lossUsd:n("dvLossUsd"),costUsd:n("dvCostUsd"),costStressUsd:n("dvCostStressUsd"),riskNature:$("dvRiskNature").value,alternativeEVTotalUsd:n("dvAlternativeEVTotalUsd"),alternativeLabel:String($("dvAlternativeLabel").value||"").trim(),candidateCapitalBasisUsd:n("dvCandidateCapitalUsd"),alternativeCapitalBasisUsd:n("dvAlternativeCapitalUsd"),candidateRiskBudgetUsd:n("dvCandidateRiskBudgetUsd"),alternativeRiskBudgetUsd:n("dvAlternativeRiskBudgetUsd"),alternativeHorizonDays:n("dvAlternativeHorizonDays"),alternativeCostsIncluded:$("dvAlternativeCostsIncluded").value==="YES",portfolioStress,generalityDossierJson:String($("dvGeneralityDossierJson").value||"").trim(),stressScenarioName:portfolioStress.scenarioName,stressSourceNote:portfolioStress.sourceNote,stressReconciled:portfolioStress.reconciled,stressQqqCoreState:portfolioStress.legs.qqqCore.state,stressQqqCoreLoss:portfolioStress.legs.qqqCore.stressLossUsd,stressVxxShortState:portfolioStress.legs.vxxShort.state,stressVxxShortLoss:portfolioStress.legs.vxxShort.stressLossUsd,stressQqqCallState:portfolioStress.legs.qqqCallCredit.state,stressQqqCallLoss:portfolioStress.legs.qqqCallCredit.stressLossUsd,stressVxxCallState:portfolioStress.legs.vxxCallCredit.state,stressVxxCallLoss:portfolioStress.legs.vxxCallCredit.stressLossUsd,stressReconciled:portfolioStress.reconciled,probabilityMethod:$("dvProbabilityMethod").value,probabilityLowPct:n("dvProbLowPct"),probabilityBasePct:n("dvProbBasePct"),probabilityHighPct:n("dvProbHighPct"),wins:n("dvWins"),trials:n("dvTrials"),probabilityBasis:$("dvProbabilityBasis").value,accuracy:$("dvAccuracy").value,generality:$("dvGenerality").value,integration:$("dvIntegration").value,evidenceNote:String($("dvEvidenceNote").value||"").trim()};
  }
  function persistDecisionValueInputs(){try{window.localStorage.setItem(DECISION_VALUE_STORAGE_KEY,JSON.stringify(readDecisionValueInputs()));}catch(_){if($("dvVerdictBadge"))$("dvVerdictBadge").textContent="LOCAL SAVE UNAVAILABLE";}}
  function restoreDecisionValueInputs(){
    try{const raw=window.localStorage.getItem(DECISION_VALUE_STORAGE_KEY);if(!raw)return;const p=JSON.parse(raw);if(!p||typeof p!=="object"||Array.isArray(p))return;
      const map={candidateKey:"dvCandidate",lens:"dvLens",quantity:"dvQuantity",horizonDays:"dvHorizonDays",rewardUsd:"dvRewardUsd",lossUsd:"dvLossUsd",costUsd:"dvCostUsd",costStressUsd:"dvCostStressUsd",riskNature:"dvRiskNature",alternativeEVTotalUsd:"dvAlternativeEVTotalUsd",alternativeLabel:"dvAlternativeLabel",candidateCapitalBasisUsd:"dvCandidateCapitalUsd",alternativeCapitalBasisUsd:"dvAlternativeCapitalUsd",candidateRiskBudgetUsd:"dvCandidateRiskBudgetUsd",alternativeRiskBudgetUsd:"dvAlternativeRiskBudgetUsd",alternativeHorizonDays:"dvAlternativeHorizonDays",alternativeCostsIncluded:"dvAlternativeCostsIncluded",generalityDossierJson:"dvGeneralityDossierJson",stressScenarioName:"dvStressScenarioName",stressSourceNote:"dvStressSourceNote",stressQqqCoreState:"dvStressQqqCoreState",stressQqqCoreLoss:"dvStressQqqCoreLoss",stressVxxShortState:"dvStressVxxShortState",stressVxxShortLoss:"dvStressVxxShortLoss",stressQqqCallState:"dvStressQqqCallState",stressQqqCallLoss:"dvStressQqqCallLoss",stressVxxCallState:"dvStressVxxCallState",stressVxxCallLoss:"dvStressVxxCallLoss",probabilityMethod:"dvProbabilityMethod",probabilityLowPct:"dvProbLowPct",probabilityBasePct:"dvProbBasePct",probabilityHighPct:"dvProbHighPct",wins:"dvWins",trials:"dvTrials",probabilityBasis:"dvProbabilityBasis",accuracy:"dvAccuracy",generality:"dvGenerality",integration:"dvIntegration",evidenceNote:"dvEvidenceNote"};
      for(const[k,id]of Object.entries(map))if(p[k]!==undefined&&p[k]!==null&&$(id))$(id).value=String(p[k]);
      if($("dvStressReconciled"))$("dvStressReconciled").checked=p.stressReconciled===true;
    }catch(_){if($("dvVerdictBadge"))$("dvVerdictBadge").textContent="SAVED SCENARIO INVALID";}
  }
  function renderDecisionValueDesk(result, deploymentRoadmap, positionRegister){
    if(!DecisionValueEngine||typeof DecisionValueEngine.evaluate!=="function")return null;
    const inputs=readDecisionValueInputs(),row=Array.isArray(result.rows)?result.rows.find(x=>x.key===inputs.candidateKey)||null:null;
    const out=DecisionValueEngine.evaluate({...inputs,nav:result.nav,market:result.market,mainRow:row,deploymentRoadmap,positionManagementRows:positionRegister?.managementRows||[]});
    const comparatorStatus=$("dvComparatorStatus");
    if(comparatorStatus)comparatorStatus.textContent="Fair comparator: "+out.comparatorContract.status+" — "+out.comparatorContract.reason;
    const generalityStatus=$("dvGeneralityStatus");
    if(generalityStatus)generalityStatus.textContent="Generality dossier: "+out.generalityReview.status+" · rolling windows "+(out.generalityReview.rollingWindowCount??"UNKNOWN")+" · positive "+(out.generalityReview.positiveEffectWindows??"UNKNOWN")+" · source authenticated by app: NO. "+(out.generalityReview.issues||[]).join(" ");
    const stress=out.portfolioStress,stressStatus=$("dvPortfolioRiskResult");
    if(stressStatus)stressStatus.textContent="Common stress: "+stress.status+" · event "+(stress.scenarioName||"UNKNOWN")+" · loss sum "+(typeof stress.totalLossUsd==="number"?money(stress.totalLossUsd):"UNKNOWN")+" · NAV "+(typeof stress.riskPctNav==="number"?pct(stress.riskPctNav):"UNKNOWN")+" · active categories "+(stress.activeLegs||[]).length+"/4 · unbounded tail "+(stress.unboundedTail?"YES":"not flagged")+" · "+[...(stress.missingLegs||[]),...(stress.invalid||[])].join("; ");
    const money=v=>typeof v==="number"&&Number.isFinite(v)?(v<0?"−$":"$")+Math.abs(v).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):"—";
    const pct=v=>typeof v==="number"&&Number.isFinite(v)?v.toLocaleString("en-US",{minimumFractionDigits:1,maximumFractionDigits:1})+"%":"—";
    const prob=v=>typeof v==="number"&&Number.isFinite(v)?pct(v):"UNKNOWN";
    $("dvManualProbabilityFields").hidden=inputs.probabilityMethod!=="MANUAL";$("dvEmpiricalProbabilityFields").hidden=inputs.probabilityMethod!=="EMPIRICAL";
    const route=out.mainRoute;
    const moneySigned=v=>typeof v==="number"&&Number.isFinite(v)?(v<0?"−$":v>0?"+$":"$")+Math.abs(v).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):"UNKNOWN";
    const heldText=!out.heldPositions.length
      ? "No matching registered position. Current size may still come from the manual sizing input; do not treat the absent register as zero holdings."
      : out.heldPositions.map(x=>String(x.label||x.template)+" · "+String(x.action||"PENDING")+" · P&L "+moneySigned(x.pnl)+" · "+(typeof x.pnlR==="number"?fmt(x.pnlR,2)+"R":"R UNKNOWN")+" · "+(typeof x.pnlPerCalendarDay==="number"?moneySigned(x.pnlPerCalendarDay)+"/calendar day":"P&L pace UNKNOWN")+" · reward:stop "+(typeof x.rewardRiskRatio==="number"?fmt(x.rewardRiskRatio,2)+":1":"UNKNOWN")+" · DTE "+(x.dte===null||x.dte===undefined?"N/A":fmt(x.dte))).join("\\n");
    $("dvHeldMeasurement").textContent=heldText;
    $("dvEngineRoute").innerHTML=!route?"<b>Primary sizing row:</b> NOT MAPPED — scenario only; the desk does not invent capacity.":
      "<b>Current engine route:</b> "+esc(route.action||"PENDING")+" · current "+esc(route.current===null?"UNKNOWN":fmt(route.current))+" → target "+esc(route.target===null?"UNKNOWN":fmt(route.target))+" · capacity "+esc(route.capacity===null?"UNKNOWN":fmt(route.capacity))+
      "<br>Maximum add gap: <b>"+esc(route.maxAllowedAdd===null?"UNKNOWN":fmt(route.maxAllowedAdd))+"</b> · trim gap: <b>"+esc(route.maxAllowedTrim===null?"UNKNOWN":fmt(route.maxAllowedTrim))+"</b><br>"+esc(route.reason||"No source reason returned.");
    const labels={BASELINE_PENDING:"PENDING · NEED INPUT",NEEDS_PAYOFF:"PENDING · PAYOFF / COST / TIME MISSING",NEEDS_PROBABILITY:"PENDING · PROBABILITY / SAMPLE MISSING",INVALID_RANGE:"BLOCK · PROBABILITY RANGE INVALID",MARKET_BLOCKED:"BLOCK · MARKET DATA GATE",CLOCK_FLOOR_BREACH:"BLOCK · CLOCK FLOOR BREACH",ADD_NOT_ALLOWED:"BLOCK · CURRENT APP TARGET / MARKET GATE",QTY_OVER_TARGET:"BLOCK · PROPOSED UNITS EXCEED ADD GAP",POSITION_REVIEW_PRIORITY:"HOLD REVIEW · POSITION-SPECIFIC GATE FIRST",HOLD_CONFLICTS_WITH_REDUCE:"FOLLOW REDUCE ROUTE · HOLD EV CANNOT OVERRIDE",QQQ_OVERLAY_LOCKBOX:"RESEARCH BLOCK · FAR CALL OVERLAY FAILED CURRENT SCREEN",MODEL_ONLY:"MODEL ONLY · NOT TRADE-READY",HYPOTHESIS_ONLY:"SCENARIO ONLY · PROBABILITY NOT EVIDENCED",EVIDENCE_INCOMPLETE:"PENDING · ACCURACY / GENERALITY / INTEGRATION",ALTERNATIVE_VALUE_PENDING:"PENDING · ALTERNATIVE NOT PRICED",NEGATIVE_INCREMENTAL_VALUE:"WAIT / ALTERNATIVE WINS · NON-POSITIVE DELTA",NEGATIVE_EXPECTED_VALUE:"WAIT / NO ADD · BASE EV NON-POSITIVE",FRAGILE_EXPECTED_VALUE:"FRAGILE · ADVERSE EV NON-POSITIVE",UNBOUNDED_TAIL:"SCENARIO ONLY · UNBOUNDED / STRESS RISK",NO_SIZING_ROUTE:"SCENARIO ONLY · NO PRIMARY CAPACITY ROUTE",ELIGIBLE_FOR_HUMAN_REVIEW:"ELIGIBLE FOR HUMAN REVIEW · NO ORDER"};
    $("dvVerdictBadge").textContent=labels[out.status]||out.status;$("dvVerdictBadge").className=["QQQ_OVERLAY_LOCKBOX","MARKET_BLOCKED","CLOCK_FLOOR_BREACH","ADD_NOT_ALLOWED","QTY_OVER_TARGET","POSITION_REVIEW_PRIORITY","HOLD_CONFLICTS_WITH_REDUCE","UNBOUNDED_TAIL","PORTFOLIO_STRESS_INVALID","PORTFOLIO_TAIL_REVIEW","PORTFOLIO_STRESS_REVIEW","ALTERNATIVE_NOT_COMPARABLE","NEGATIVE_EXPECTED_VALUE","NEGATIVE_INCREMENTAL_VALUE"].includes(out.status)?"tag danger":out.status==="ELIGIBLE_FOR_HUMAN_REVIEW"?"tag active":"tag warn";
    $("dvVerdictHeadline").textContent=out.nextAction||"Decision value pending.";
    const metrics=[["BREAK-EVEN P*",pct(out.breakEvenProbabilityPct),"Probability needed to cover loss + base costs"],["BASE EXPECTED VALUE",money(out.expectedValueBaseUsd),out.expectedValueBasePerRisk===null?"EV / entered loss UNKNOWN":fmt(out.expectedValueBasePerRisk,2)+" × entered loss unit"],["ADVERSE EXPECTED VALUE",money(out.expectedValueAdverseUsd),out.adverseProbabilityPct===null?"Low-probability / stress-cost unavailable":prob(out.adverseProbabilityPct)+" · stress costs included"],["EV PER CALENDAR DAY",money(out.expectedValuePerCalendarDayUsd),"Candidate total EV / time"],["INCREMENTAL EV vs ALTERNATIVE",money(out.incrementalValueBaseUsd),out.alternativeComplete?"Base delta after comparator: "+esc(out.alternativeLabel):"PENDING · alternative not priced"]];
    $("dvMetrics").innerHTML=metrics.map(([t,v,d])=>'<div class="decision-metric"><small>'+esc(t)+'</small><b>'+esc(v)+'</b><span>'+esc(d)+'</span></div>').join("");
    const cr=(name,p,cost,ev,total,delta)=>'<tr><td>'+esc(name)+'</td><td>'+esc(prob(p))+'</td><td>'+esc(money(cost))+'</td><td>'+esc(money(ev))+'</td><td>'+esc(money(total))+'</td><td>'+esc(money(delta))+'</td></tr>';
    $("dvSensitivityRows").innerHTML=out.expectedValueBaseUsd===null?'<tr><td colspan="6" class="pro-empty-cell">Complete positive gain/loss, costs, quantity, horizon and probability.</td></tr>':cr("LOW / ADVERSE",out.probabilityLowPct,out.totalCostAdverseUsd,out.expectedValueAdverseUsd,out.expectedValueAdverseTotalUsd,out.incrementalValueAdverseUsd)+cr("BASE",out.probabilityBasePct,out.totalCostBaseUsd,out.expectedValueBaseUsd,out.expectedValueBaseTotalUsd,out.incrementalValueBaseUsd)+cr("HIGH / FAVOURABLE",out.probabilityHighPct,out.totalCostBaseUsd,out.expectedValueHighUsd,out.expectedValueHighTotalUsd,out.incrementalValueHighUsd);
    const reasons=["<p><strong>Fair comparator:</strong> "+esc(out.comparatorContract.status)+" · "+esc(out.comparatorContract.reason)+".</p>","<p><strong>Cross-strategy stress:</strong> "+esc(out.portfolioStress.status)+" · event "+esc(out.portfolioStress.scenarioName||"UNKNOWN")+" · loss sum "+esc(money(out.portfolioStress.totalLossUsd))+" · NAV "+esc(pct(out.portfolioStress.riskPctNav))+" · source authentication: NO. "+esc((out.portfolioStress.warnings||[]).join(" "))+"</p>","<p><strong>Generality dossier:</strong> "+esc(out.generalityReview.status)+" · windows "+esc(out.generalityReview.rollingWindowCount??"UNKNOWN")+" · positive "+esc(out.generalityReview.positiveEffectWindows??"UNKNOWN")+"/"+esc(out.generalityReview.rollingWindowCount??"UNKNOWN")+" · source authenticated: NO. "+esc((out.generalityReview.issues||[]).join(" "))+"</p>","<p><strong>Probability:</strong> "+esc(out.probabilityMethodLabel)+" · "+esc(out.probabilityBasisLabel)+" · sample "+esc(out.sampleSize===null?"UNKNOWN":fmt(out.sampleSize))+".</p>","<p><strong>Risk measurement:</strong> "+esc(out.riskNatureLabel)+"; entered scenario loss at quantity "+esc(money(out.scenarioLossTotalUsd))+" ("+esc(pct(out.scenarioRiskPctNav))+" NAV). Not a guarantee or VaR estimate.</p>","<p><strong>Risk / reward:</strong> "+esc(out.rewardRiskRatio===null?"UNKNOWN":fmt(out.rewardRiskRatio,2)+":1")+" · probability margin over break-even "+esc(out.probabilityMarginPct===null?"UNKNOWN":(out.probabilityMarginPct>=0?"+":"")+pct(out.probabilityMarginPct))+" · base EV as % NAV "+esc(pct(out.expectedValuePctNav))+".</p>","<p><strong>Alternative benchmark:</strong> "+(out.alternativeComplete?esc(out.alternativeLabel)+" · total EV "+esc(money(out.alternativeEVTotalUsd))+" · base incremental EV "+esc(money(out.incrementalValueBaseUsd))+" · adverse incremental EV "+esc(money(out.incrementalValueAdverseUsd)):"PENDING — enter a named, same-capital and same-horizon alternative. $0 direct P&amp;L is not automatically the economic cost of waiting.")+".</p>","<p><strong>Deployment roadmap:</strong> "+esc(out.deploymentRoadmap?.status||"BASELINE PENDING")+" · CLOCK gap "+esc(moneySigned(out.deploymentRoadmap?.floorGapUsd))+"; floor breach blocks new deployment. Missing baseline is not converted to zero.</p>","<p><strong>Three axes:</strong> Accuracy "+esc(out.axes.accuracy)+" · Generality "+esc(out.axes.generality)+" · Integration "+esc(out.axes.integration)+". PASS settings are operator-attested.</p>"];
    if(out.warnings.length)reasons.push("<p><strong>Limits:</strong> "+esc(out.warnings.join(" "))+"</p>");$("dvDecisionReasons").innerHTML=reasons.join("");
    return {schema:"QQQ_HYBRID_DECISION_VALUE_V1",...out,input:inputs,currentRow:row?{key:row.key,current:row.current,target:row.target,capacity:row.capacity,delta:row.delta,action:row.action,status:row.status,reason:row.reason}:null,generatedAt:new Date().toISOString(),brokerOrders:false,automaticPositionMutation:false};
  }
  function loadVxxModelReplayProbability(){$("dvCandidate").value="vxxCallSpreads";$("dvProbabilityMethod").value="EMPIRICAL";$("dvWins").value="41";$("dvTrials").value="49";$("dvProbabilityBasis").value="MODEL_REPLAY";$("dvEvidenceNote").value="Repo historical attribution: 41/49 closed wins, 2018-03-01 to 2026-09-04; DERIVED_BS_VIX, NOT OPRA; descriptive model-only reference.";persistDecisionValueInputs();renderPlan();}
  function renderPlan() {
    updateSlopeDisplay();
    syncHubResearchCandidates();
    renderPositionLedger();
    const input = readInput();
    // Manual edits make the source explicit rather than silently preserving a stale V3 provenance tag.
    if (marketTouched) input.market.term_source = "MANUAL_OPERATOR_INPUT";
    const result = E.calculatePortfolio(input);
    const deploymentRoadmap = renderDeploymentRoadmap(result);
    const decisionValue = renderDecisionValueDesk(result, deploymentRoadmap, input.positionRegister);
    lastPlan = { generatedAt: new Date().toISOString(), input, result, candidates, deploymentRoadmap, decisionValue };
    renderProDashboard(result, input);
    const m = result.market;
    $("marketBadge").textContent = m.status + (m.blocked ? " · NO SIZING" : "");
    $("marketBadge").className = "tag " + (m.blocked ? "danger" : m.state === "CARRY" ? "active" : "warn");
    $("marketMeta").textContent = marketMeta || (marketTouched ? "MANUAL_OPERATOR_INPUT — confirm source and dates." : "No source metadata.");
    $("marketReason").textContent = m.reason;
    $("stateName").textContent = m.state;
    $("stateAction").textContent = m.blocked
      ? "BLOCK · WAIT FOR VERIFIED DATA"
      : m.allowNew
        ? "CARRY · ELIGIBLE FOR HUMAN REVIEW ONLY"
        : m.action === "REDUCE"
          ? "RISK-OFF · REVIEW SELLER-LEG REDUCTIONS"
          : "HOLD · NO NEW CARRY ADDS";
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
      deploymentRoadmap: lastPlan.deploymentRoadmap || null,
      decisionValue: lastPlan.decisionValue || null,
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



  function syncCapitalContextToHub() {
    const status = $("hubContextSyncStatus");
    const link = $("openHubFromContextLink");
    const bridge = window.HubContextBridgeV1;
    if (!bridge || typeof bridge.contextFromPrimaryPlan !== "function") {
      if (status) status.textContent = "Hub context bridge unavailable; refresh the local app files before syncing.";
      return;
    }
    try {
      renderPlan();
      const packet = bridge.contextFromPrimaryPlan(lastPlan);
      const checked = bridge.validate(packet, Date.now());
      if (!checked.ok) throw new Error(checked.error || "Primary context validation failed.");
      window.localStorage.setItem(bridge.STORAGE_KEY, JSON.stringify(packet));
      if (link) link.hidden = false;
      if (status) {
        status.textContent = packet.riskReservationReady
          ? "已保存本次主台情境。原 Hybrid 風險額度 = $" + packet.baseRiskReservedUsd.toFixed(2) +
            "（按 primary current/target 數量 × 目前候選每組風險估算；不是已成交持倉證明）。"
          : "已保存 NAV／現金設定，但主台 sizing 或現有風險估算未通過；Hub 的預留風險保持未知，不會自動當成 $0。";
      }
      try { window.open("hub_research_pack.html?fromPrimary=1", "_blank", "noopener,noreferrer"); } catch (_) {}
    } catch (error) {
      if (status) status.textContent = "未能同步到 Hub：" + (error instanceof Error ? error.message : String(error)) + "。主台輸入沒有改動。";
    }
  }

  function exportAiReviewPack() {
    const helper = window.AiHandoffV1;
    if (!helper || typeof helper.serialize !== "function") {
      const status = $("aiHandoffStatus");
      if (status) status.textContent = "AI handoff helper unavailable. Refresh the local app files before exporting.";
      return;
    }
    if (!lastPlan) renderPlan();
    const content = helper.serialize(lastPlan, candidates, marketMeta);
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const day = String(lastPlan?.generatedAt || new Date().toISOString()).slice(0, 10);
    a.href = url;
    a.download = "qqq-hybrid-ai-review-" + day + ".md";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    const status = $("aiHandoffStatus");
    if (status) status.textContent = "AI review packet exported. Attach it to ChatGPT with a fresh broker option-chain screenshot/CSV. No order was sent.";
    $("journalStatus").textContent = "AI review packet exported for manual review. It does not authorize an order or mutate a position.";
  }

  async function appendJournal() {
    const payload = {
      record_type: "MANUAL_PREVIEW",
      input: lastPlan?.input || readInput(),
      result: lastPlan?.result || null,
      candidates,
      deploymentRoadmap: lastPlan?.deploymentRoadmap || null,
      decisionValue: lastPlan?.decisionValue || null,
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
      totalOptionRiskPct:p.totalOptionRiskPct, vixHigh:p.vixHigh, termSafe:p.termSafe, maxTermAgeDays:p.maxTermAgeDays
    })) $(k).value = v;
    syncBudgetInputsFromProfile();
    $("journalStatus").textContent = "Loaded V3 reference parameters for a what-if preview. This does not change any live policy or broker position.";
  }

  function wire() {
    buildOptionRows();
    loadPositionRecords();
    updatePositionFormMode();
    $("positionSaveBtn").addEventListener("click", savePositionFromForm);
    $("positionCancelEditBtn").addEventListener("click", resetPositionForm);
    $("posTemplate").addEventListener("change", updatePositionFormMode);
    $("positionUseRegister").addEventListener("change", handlePositionRegisterMode);
    $("positionRegisterCompleteConfirmed").addEventListener("change", () => {
      if (!$("positionRegisterCompleteConfirmed").checked && $("positionUseRegister").checked) {
        $("positionUseRegister").checked = false;
        restoreManualPositionInputs();
      }
      renderPlan();
    });
    $("positionExportBtn").addEventListener("click", exportPositionRegisterJson);
    $("positionImportBtn").addEventListener("click", () => $("positionImportFile").click());
    $("positionImportFile").addEventListener("change", event => importPositionRegister(event.target.files && event.target.files[0]));
    $("positionLedgerRows").addEventListener("click", event => {
      const button = event.target.closest("[data-position-action]");
      if (!button) return;
      const id = button.dataset.positionId;
      const index = positionRecords.findIndex(row => row.id === id);
      if (index < 0) return;
      if (button.dataset.positionAction === "edit") {
        fillPositionForm(positionRecords[index]);
      } else if (button.dataset.positionAction === "delete" &&
        window.confirm("Remove this local position record? No broker position will be changed.")) {
        invalidatePositionRegisterCoverage("A position record was removed.");
        positionRecords.splice(index, 1);
        savePositionRecords();
        renderPlan();
      }
    });
    restoreRoadmapSettings();
    restoreDecisionValueInputs();
    $("dvLoadVxxReplayBtn").addEventListener("click", loadVxxModelReplayProbability);
    $("dvStressReconciled").addEventListener("change", () => { persistDecisionValueInputs(); renderPlan(); });
    $("setRoadmapBaselineBtn").addEventListener("click", lockRoadmapBaseline);
    $("clearRoadmapBaselineBtn").addEventListener("click", clearRoadmapBaseline);
    $("mToday").value = new Date().toISOString().slice(0,10);
    $("refreshBtn").addEventListener("click", refreshMarket);
    $("v3ProfileBtn").addEventListener("click", loadReferenceProfile);
    $("test1000Btn").addEventListener("click", setTest1000);
    $("testLeg").addEventListener("change", () => { window.hybridTestOverrides = {}; renderPlan(); });
    $("exportBtn").addEventListener("click", exportPlan);
    $("toggleResearchRows").addEventListener("click", toggleResearchRows);
    $("aiHandoffBtn").addEventListener("click", exportAiReviewPack);
    $("syncHubBtn").addEventListener("click", syncCapitalContextToHub);
    $("journalBtn").addEventListener("click", appendJournal);
    window.addEventListener("storage", event => {
      if (!event.key || !event.key.startsWith(OPTION_HANDOFF_PREFIX)) return;
      const chainKey = event.key.slice(OPTION_HANDOFF_PREFIX.length), slot = OPTION_HANDOFF_SLOTS[chainKey];
      if (!slot) return;
      if (event.newValue === null) {
        candidates[slot] = null; renderCandidateRows();
        $("journalStatus").textContent = "Removed "+chainKey+" handoff; primary option capacity is PENDING.";
        renderPlan(); return;
      }
      try { acceptOptionCandidatePacket(JSON.parse(event.newValue), chainKey); }
      catch (error) { candidates[slot] = null; renderCandidateRows(); $("journalStatus").textContent = "Invalid "+chainKey+" handoff JSON; capacity remains PENDING."; renderPlan(); }
    });
    $("findHubResearchBtn").addEventListener("click", findHubResearchCandidates);
    document.querySelectorAll("[data-find]").forEach(btn => {
      btn.dataset.label = btn.textContent;
      btn.addEventListener("click", () => findCandidate(btn));
    });
    document.querySelectorAll("input,select,textarea").forEach(el => {
      if (el.id.startsWith("current-") || el.id.startsWith("budget-") || el.id.startsWith("risk-") || el.id.startsWith("enabled-") ||
          ["mQqq","mVxx","mVix","mM1","mM2","mSpotAsOf","mTermAsOf","mToday","nav","cashPool","cashReservePct","vxxShortMarginMultiple","vxxShortBorrowAprPct","qqqCorePct","vxxNormalPct","vxxHighPct","totalOptionRiskPct","vixHigh","termSafe","maxTermAgeDays","nxEnabled","nxCurrentFar","nxCurrentNear","nxFarDelta","nxNearDelta","nxCoverage","nxMaxStack","nxNShort","nxFarDistancePct","nxGammaRel","nxDeltaJump","allowProtectionBuys","targetDte","hubRatioN","hubStateLayerCap","hubDrawdown252Pct","hubReturn5dPct","planBaseCapital","planStartDate","planHorizonMonths","planMonthlyContribution",...DECISION_INPUT_IDS].includes(el.id)) {
        el.addEventListener("input", () => {
          if (["mQqq","mVxx","mVix","mM1","mM2","mSpotAsOf","mTermAsOf","mToday"].includes(el.id)) {
            marketTouched = true;
            if (marketSource === "BLOCKED") marketSource = "MANUAL_OPERATOR_INPUT";
            marketMeta = "MANUAL_OPERATOR_INPUT — market prices and expiry state must be verified by the operator.";
          }
          if (["planBaseCapital","planStartDate","planHorizonMonths","planMonthlyContribution"].includes(el.id)) persistRoadmapSettings();
          if (DECISION_INPUT_IDS.includes(el.id)) persistDecisionValueInputs();
          // Keep the top-level mirrors and option rows synchronized.
          const budgetKey = Object.entries(TOP_BUDGETS).find(([,id]) => id === el.id)?.[0];
          if (budgetKey) $("budget-" + budgetKey).value = el.value;
          renderPlan();
        });
      }
    });
    // Restore the first test model after initial render.
    restoreOptionCandidatesFromLocalStorage();
    renderPlan();
    // Age out operator-recorded quotes even if the page is otherwise idle.
    window.setInterval(() => {
      if (candidates.qqqCall || candidates.vxxCall) { renderCandidateRows(); renderPlan(); }
    }, 60000);
    refreshMarket();
  }

  wire();
})();
