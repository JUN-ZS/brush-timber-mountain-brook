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
  const PositionLedger = window.PositionLedgerV1;
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

  function renderPositionLedger() {
    if (!PositionLedger) return;
    const market = readMarket();
    positionRegisterSummary = PositionLedger.summarize(positionRecords, market);
    const summary = positionRegisterSummary;
    $("positionLedgerHeadline").innerHTML =
      '<div><small>METADATA-COMPLETE P&amp;L SUBTOTAL</small><b>' + (summary.metadataCompletePnlRows ? esc(positionMoney(summary.metadataCompletePnlSubtotal, true)) : "—") + '</b><span>' + summary.metadataCompletePnlRows + ' metadata-complete row(s); indicative subtotal ' + esc(positionMoney(summary.indicativePnlSubtotal, true)) + ' across ' + summary.indicativePnlRows + ' row(s), excluded from metadata-complete total</span></div>' +
      '<div><small>INCOMPLETE P&amp;L ROWS</small><b>' + fmt(summary.incompletePnlCount) + '</b><span>Missing entry or mark; not assumed to be zero</span></div>' +
      '<div><small>STALE / UNVERIFIED MARKS</small><b>' + fmt(summary.staleMarkCount) + '</b><span>Age/source affects confidence, not the arithmetic</span></div>' +
      '<div><small>HELD OPTION TERMS BLOCKS</small><b>' + fmt(summary.termBlockedCount) + '</b><span>Blocks that strategy when register mode is on</span></div>';

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
        ? (row.termsComplete ? "OPERATOR-ATTESTED TERMS" : "BLOCKED · TERMS INCOMPLETE") + (row.adjustedDetected ? " · ADJUSTED ROOT" : "")
        : esc(row.entryEvidence || "UNKNOWN ENTRY");
      const riskNote = option
        ? (row.maxLossPerPackage === null ? "Per-package max loss UNKNOWN" : "Entry max loss/package (assumed terms): " + positionMoney(row.maxLossPerPackage))
        : "";
      const pnlClass = row.unrealizedPnl === null ? "position-pnl-unknown" : row.unrealizedPnl < 0 ? "position-pnl-negative" : "position-pnl-positive";
      return '<tr>' +
        '<td><b>' + esc(row.label) + '</b><small>' + contractLine + '</small></td>' +
        '<td>' + esc(row.entryDate || "UNKNOWN") + '</td>' +
        '<td class="pro-number">' + esc(fmt(row.qty)) + ' ' + esc(row.unit) + '</td>' +
        '<td class="pro-number">' + esc(row.entryPrice === null ? "UNKNOWN" : positionMoney(row.entryPrice)) + '</td>' +
        '<td class="pro-number">' + esc(row.markPrice === null ? "UNKNOWN" : positionMoney(row.markPrice)) + (row.markDerivedFromSnapshot ? '<small>APP spot snapshot</small>' : '') + '</td>' +
        '<td class="' + pnlClass + '">' + esc(positionMoney(row.unrealizedPnl, true)) + '<small>' + esc(row.pnlStatus) + '</small></td>' +
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
      sizing[s.riskPctField] = s.mainBudgetEligible ? inputNumber(TOP_BUDGETS[s.key], s.defaultRiskPct) : 0;
      holdings[s.key] = inputNumber("current-" + s.key, 0);
      if (s.mainBudgetEligible && !s.baseline) permissions[s.key] = $("enabled-" + s.key)?.checked === true;
      if (["manualDebit", "manualRisk", "stressOnly"].includes(s.kind)) manualRiskPerUnit[s.key] = inputNumber("risk-" + s.key, null);
    }
    const positionSummary = PositionLedger ? PositionLedger.summarize(positionRecords, readMarket()) : null;
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
    setInput("mToday", snapshot?.today || new Date().toISOString().slice(0, 10));
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
      return candidate.right.toUpperCase() + " vertical · expiry " + candidate.expiry + " · " +
        fmt(candidate.dte) + " DTE · SHORT " + shortLabel + " Bid/Ask " +
        premium(candidate.shortBid) + "/" + premium(candidate.shortAsk) + " · width " +
        quoteWidthLabel(candidate.shortQuoteWidthPctMid, candidate.shortQuoteQuality) +
        " · WING " + longLabel + " Bid/Ask " + premium(candidate.longBid) + "/" + premium(candidate.longAsk) +
        " · width " + quoteWidthLabel(candidate.longQuoteWidthPctMid, candidate.longQuoteQuality) +
        " · credit/share " + premium(candidate.credit) + " · max loss/spread " + usd(candidate.maxLossPerSpread) +
        " (multiplier " + (candidate.multiplierAssumption || 100) + " assumed; not verified)" +
        fetched + termsWarning + " · " + (candidate.chainSource || candidate.source || "source unknown");
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
        creditDetail: qTotalCredit === null ? "Quote / capacity pending" : pct(ratioPct(qTotalCredit, nav)) + " of NAV · max-capacity estimate",
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
        creditDetail: vTotalCredit === null ? "Quote / capacity pending" : pct(ratioPct(vTotalCredit, nav)) + " of NAV · max-capacity estimate",
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
    renderPositionLedger();
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
    $("mToday").value = new Date().toISOString().slice(0,10);
    $("refreshBtn").addEventListener("click", refreshMarket);
    $("v3ProfileBtn").addEventListener("click", loadReferenceProfile);
    $("test1000Btn").addEventListener("click", setTest1000);
    $("testLeg").addEventListener("change", () => { window.hybridTestOverrides = {}; renderPlan(); });
    $("exportBtn").addEventListener("click", exportPlan);
    $("toggleResearchRows").addEventListener("click", toggleResearchRows);
    $("aiHandoffBtn").addEventListener("click", exportAiReviewPack);
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
