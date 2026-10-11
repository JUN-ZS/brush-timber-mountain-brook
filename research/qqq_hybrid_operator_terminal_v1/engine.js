(function (root) {
  "use strict";

  const REFERENCE_PROFILE = Object.freeze({
    name: "V3 policy reference — preview only",
    cashReservePct: 10,
    vxxShortMarginMultiple: 1.5,
    qqqCorePct: 42,
    vxxNormalPct: 18,
    vxxHighPct: 10,
    qqqCallRiskPct: 1.2,
    vxxCallRiskPct: 2,
    qqqBullPutRiskPct: 0,
    totalOptionRiskPct: 3.2,
    vixHigh: 28,
    termSafe: 5,
    maxTermAgeDays: 4
  });

  // Strategies discussed across Hybrid, Live Hedge and Hub. Research-only legs
  // are present for comparison, but never authorize entries by their presence.
  const OPTION_STRATEGIES = Object.freeze([
    { key: "qqqCallSpreads", id: "QQQ_CALL_CREDIT", label: "QQQ FAR CALL / CALL-CREDIT", family: "hybrid", kind: "creditVertical", candidateKey: "qqqCall", riskPctField: "qqqCallRiskPct", defaultRiskPct: 1.2, seller: true, baseline: true, mainBudgetEligible: true, priority: 1 },
    { key: "vxxCallSpreads", id: "VXX_CALL_CREDIT", label: "VXX CALL-CREDIT", family: "hybrid", kind: "creditVertical", candidateKey: "vxxCall", riskPctField: "vxxCallRiskPct", defaultRiskPct: 2, seller: true, baseline: true, mainBudgetEligible: true, priority: 2 },
    { key: "vxxPutSpreads", id: "VXX_PUT_CREDIT", label: "VXX PUT-CREDIT (RESEARCH ONLY)", family: "research", kind: "creditVertical", candidateKey: "vxxPut", riskPctField: "vxxPutRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 3 },
    { key: "qqqBullPutSpreads", id: "QQQ_BULL_PUT", label: "QQQ BULL-PUT CREDIT", family: "research", kind: "creditVertical", candidateKey: "qqqPut", riskPctField: "qqqBullPutRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 4 },
    { key: "qqqBearCallSpreads", id: "QQQ_BEAR_CALL", label: "QQQ BEAR-CALL CREDIT", family: "research", kind: "creditVertical", candidateKey: "qqqBearCall", riskPctField: "qqqBearCallRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 5 },
    { key: "coveredCalls", id: "COVERED_CALL", label: "COVERED CALL", family: "research", kind: "coveredCall", candidateKey: "qqqCoveredCall", riskPctField: "coveredCallRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 6 },
    { key: "protectivePuts", id: "QQQ_PROTECTIVE_PUT", label: "QQQ PROTECTIVE PUT", family: "research", kind: "debit", candidateKey: "qqqProtectivePut", riskPctField: "protectivePutRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 7 },
    { key: "longCalls", id: "LONG_CALL", label: "LONG CALL", family: "research", kind: "debit", candidateKey: "qqqLongCall", riskPctField: "longCallRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 8 },
    { key: "longPuts", id: "LONG_PUT", label: "LONG PUT", family: "research", kind: "debit", candidateKey: "qqqLongPut", riskPctField: "longPutRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 9 },
    { key: "longStraddles", id: "LONG_STRADDLE", label: "LONG STRADDLE", family: "research", kind: "manualDebit", candidateKey: null, riskPctField: "longStraddleRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 10 },
    { key: "ironFlies", id: "IRON_FLY", label: "IRON FLY", family: "research", kind: "manualRisk", candidateKey: null, riskPctField: "ironFlyRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 11 },
    { key: "ironCondors", id: "IRON_CONDOR", label: "IRON CONDOR", family: "research", kind: "manualRisk", candidateKey: null, riskPctField: "ironCondorRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 12 },
    { key: "brokenWings", id: "BROKEN_WING", label: "BROKEN-WING BUTTERFLY", family: "research", kind: "manualRisk", candidateKey: null, riskPctField: "brokenWingRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 13 },
    { key: "calendars", id: "CALENDAR", label: "CALENDAR SPREAD", family: "research", kind: "manualDebit", candidateKey: null, riskPctField: "calendarRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 14 },
    { key: "ratioCalls", id: "HUB_RATIO_CALL_HARVEST", label: "HUB RATIO-CALL HARVEST / DYNAMIC-N", family: "research", kind: "hubDefinedRisk", candidateKey: "hubRatioCall", riskPctField: "ratioCallRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 15 },
    { key: "hubStateAdaptive", id: "HUB_STATE_ADAPTIVE_STACK", label: "HUB STATE-ADAPTIVE / STAGGERED PACKAGE", family: "research", kind: "hubDefinedRisk", candidateKey: "hubStateAdaptive", riskPctField: "hubStateAdaptiveRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 16 },
    { key: "hubShockPuts", id: "HUB_SHOCK_GATED_PUT", label: "HUB SHOCK-GATED PUT DEBIT SPREAD", family: "research", kind: "hubDefinedRisk", candidateKey: "hubShockPut", riskPctField: "hubShockPutRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 17 },
    { key: "ratioPuts", id: "PUT_RATIO_1_N_1", label: "PUT RATIO (STRESS-ONLY)", family: "research", kind: "stressOnly", candidateKey: null, riskPctField: "ratioPutRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 18 }
  ]);

  function num(value, fallback = null) {
    if (value === null || value === undefined || value === "") return fallback;
    const parsed = Number(String(value).replace(/,/g, ""));
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function whole(value, fallback = 0) {
    const v = num(value, fallback);
    return Number.isFinite(v) ? Math.max(0, Math.floor(v)) : fallback;
  }

  function termSlope(m1, m2) {
    return Number.isFinite(m1) && Number.isFinite(m2) && m1 > 0 ? ((m2 - m1) / m1) * 100 : null;
  }

  function daysBetween(a, b) {
    if (!a || !b) return null;
    const x = Date.parse(String(a).slice(0, 10) + "T00:00:00Z");
    const y = Date.parse(String(b).slice(0, 10) + "T00:00:00Z");
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    return Math.abs(y - x) / 86400000;
  }

  function assessMarket(snapshot, settings = {}) {
    const s = snapshot || {};
    const qqq = num(s.qqq), vxx = num(s.vxx), vix = num(s.vix);
    const m1 = num(s.m1), m2 = num(s.m2);
    const slopeProvided = num(s.term_slope);
    const slope = slopeProvided !== null ? slopeProvided : termSlope(m1, m2);
    const today = s.today || new Date().toISOString().slice(0, 10);
    const termAsOf = s.term_asof || null;
    const spotAsOf = s.spot_asof || null;
    const maxAge = num(settings.maxTermAgeDays, REFERENCE_PROFILE.maxTermAgeDays);
    const hasAll = [qqq, vxx, vix, m1, m2, slope].every(Number.isFinite) &&
      qqq > 0 && vxx > 0 && vix >= 0 && m1 > 0 && m2 > 0;
    if (!hasAll || s.term_source === "BLOCKED") {
      return { blocked: true, status: "BLOCKED", state: "DATA BLOCKED", action: "HOLD", allowNew: false, riskOff: true, qqq, vxx, vix, m1, m2, slope, reason: "Missing/invalid spot or VX M1/M2. No target may be inferred from absent data." };
    }
    const age = termAsOf ? daysBetween(termAsOf, today) : null;
    const asofGap = spotAsOf && termAsOf ? daysBetween(spotAsOf, termAsOf) : 0;
    if (age === null || age > maxAge) {
      return { blocked: true, status: "STALE", state: "DATA STALE", action: "HOLD", allowNew: false, riskOff: true, qqq, vxx, vix, m1, m2, slope, age, reason: "VX term as-of is missing or older than the permitted cadence. Freeze sizing changes until refreshed." };
    }
    if (asofGap !== null && asofGap > 2) {
      return { blocked: true, status: "MIXED", state: "AS-OF MIXED", action: "HOLD", allowNew: false, riskOff: true, qqq, vxx, vix, m1, m2, slope, age, reason: "Spot and VX term timestamps differ by more than two days." };
    }
    const high = vix >= num(settings.vixHigh, REFERENCE_PROFILE.vixHigh);
    const backwardation = slope <= 0;
    const thin = slope <= num(settings.termSafe, REFERENCE_PROFILE.termSafe);
    let state, action, reason;
    if (high && backwardation) {
      state = "SHOCK"; action = "REDUCE"; reason = "VIX high + VX backwardation: cut volatility-seller exposure first; preserve QQQ core capacity.";
    } else if (backwardation) {
      state = "PRE-SHOCK"; action = "REDUCE"; reason = "VX backwardation: no new short-vol exposure; reduce seller legs toward the policy target.";
    } else if (high) {
      state = "PRE-SHOCK"; action = "REDUCE"; reason = "VIX high: cap VXX short notional and stop adding short-vol options.";
    } else if (thin) {
      state = "WEAKENING"; action = "HOLD"; reason = "Positive but thin contango: no new carry entries; over-cap positions may still be trimmed.";
    } else {
      state = "CARRY"; action = "BUY"; reason = "Healthy contango and VIX below the high line: eligible legs may build toward capacity.";
    }
    return { blocked: false, status: "FRESH", state, action, allowNew: state === "CARRY", riskOff: state === "SHOCK" || state === "PRE-SHOCK", high, backwardation, thin, qqq, vxx, vix, m1, m2, slope, age, termAsOf, spotAsOf, reason };
  }

  function candidateRisk(strategy, candidate, manualRiskUnit) {
    const manual = num(manualRiskUnit);
    if (strategy.kind === "creditVertical") {
      if (candidate && candidate.contractTermsStatus === "ADJUSTED_DELIVERABLE_BLOCKED") {
        return { riskPerUnit: null, capitalPerUnitUsd: null, source: "ADJUSTED_CONTRACT_BLOCKED", ready: false, reason: "Adjusted VXX option root detected (" + (candidate.adjustedContractSymbols || []).join(", ") + "). The primary budget is blocked until the exact multiplier and deliverable are verified; do not size at 100 by assumption." };
      }
      if (candidate && [candidate.width, candidate.credit].every(v => Number.isFinite(num(v))) &&
          num(candidate.width) > 0 && num(candidate.credit) > 0 && num(candidate.credit) < num(candidate.width)) {
        const riskPerUnit = (num(candidate.width) - num(candidate.credit)) * 100;
        return { riskPerUnit, capitalPerUnitUsd: riskPerUnit, debitPerUnitUsd: -num(candidate.credit) * 100, source: candidate.source || "OBSERVED_CHAIN", ready: true, reason: "Defined-risk vertical: (width − net credit) × 100." };
      }
      return { riskPerUnit: null, source: "MISSING_CHAIN", ready: false, reason: "Need a valid same-expiry vertical and positive observable net credit; no sizing invented." };
    }
    if (strategy.kind === "debit") {
      if (candidate && num(candidate.ask) > 0) return { riskPerUnit: num(candidate.ask) * 100, capitalPerUnitUsd: num(candidate.ask) * 100, debitPerUnitUsd: num(candidate.ask) * 100, source: candidate.source || "OBSERVED_CHAIN", ready: true, reason: "Long option risk is the debit paid (ask × multiplier)." };
      return { riskPerUnit: null, source: "MISSING_CHAIN", ready: false, reason: "Need a positive observed option ask. No premium floor is fabricated." };
    }
    if (strategy.kind === "coveredCall") {
      if (candidate && (num(candidate.shortBid) > 0 || (candidate.type === "coveredCall" && num(candidate.credit) > 0))) return { riskPerUnit: null, source: candidate.source || "OBSERVED_CHAIN", ready: true, reason: "Contract target is bounded by QQQ shares / 100; confirm the actual covered-call short bid before use." };
      return { riskPerUnit: null, source: "MISSING_CHAIN", ready: false, reason: "Need a positive short-call bid minus long-hedge ask / covered-call candidate." };
    }
    if (strategy.kind === "manualDebit") {
      if (manual > 0) return { riskPerUnit: manual, capitalPerUnitUsd: manual, debitPerUnitUsd: manual, source: "MANUAL_DEBIT_INPUT", ready: true, reason: "Manual debit / max loss per spread; verify the actual chain before use." };
      return { riskPerUnit: null, source: "PENDING_MANUAL_DEBIT", ready: false, reason: "Enter total debit per spread × multiplier; otherwise PENDING." };
    }
    if (strategy.kind === "manualRisk") {
      if (manual > 0) return { riskPerUnit: manual, capitalPerUnitUsd: manual, source: "MANUAL_DEFINED_RISK_INPUT", ready: true, reason: "Manual max loss per spread; verify strike geometry and net credit." };
      return { riskPerUnit: null, source: "PENDING_MANUAL_RISK", ready: false, reason: "Enter the verified maximum loss per spread; otherwise PENDING." };
    }
    if (strategy.kind === "hubDefinedRisk") {
      const risk = num(candidate && (candidate.riskPerUnit ?? candidate.riskUsd));
      if (candidate && candidate.ready !== false && risk !== null && risk > 0) {
        const debit = num(candidate.debitUsd, 0);
        return { riskPerUnit: Math.max(risk, Math.max(0, debit)), capitalPerUnitUsd: Math.max(risk, Math.max(0, debit)), debitPerUnitUsd: debit, source: candidate.source || "HUB_RESEARCH_ENTRY_PAYOFF_PROXY", ready: true, reason: candidate.reason || "Hub-researched package risk; one package is counted in the shared portfolio risk pool." };
      }
      return { riskPerUnit: null, capitalPerUnitUsd: null, source: "HUB_RESEARCH_CANDIDATE_PENDING", ready: false, reason: candidate?.error || "Run the Hub research-chain candidate lookup; missing prices do not create a capacity." };
    }
    if (strategy.kind === "stressOnly") {
      if (manual > 0) return { riskPerUnit: manual, capitalPerUnitUsd: manual, source: "MANUAL_STRESS_ESTIMATE", ready: true, reason: "Stress-loss estimate only. Ratio tails remain unbounded; this is NOT a hard loss cap." };
      return { riskPerUnit: null, source: "UNBOUNDED_TAIL", ready: false, reason: "No finite hard max-loss figure is available for this ratio structure. Sizing remains PENDING." };
    }
    return { riskPerUnit: null, source: "UNSUPPORTED", ready: false, reason: "Unsupported sizing type." };
  }

  function actionFor(current, cap, canAdd) {
    if (cap === null || cap === undefined) return { target: current, action: "PENDING", delta: 0 };
    if (current > cap) return { target: cap, action: "REDUCE", delta: cap - current };
    if (canAdd && current < cap) return { target: cap, action: "ADD", delta: cap - current };
    return { target: current, action: "HOLD", delta: 0 };
  }

  function calculatePortfolio(input) {
    const d = input || {};
    const market = assessMarket(d.market, d.gates);
    const nav = num(d.nav, 0);
    const cashPool = num(d.cashPool, 0);
    const sizing = d.sizing || {};
    const holdings = d.holdings || {};
    const candidates = d.candidates || {};
    const permissions = d.permissions || {};
    const optionRiskPct = num(sizing.totalOptionRiskPct, REFERENCE_PROFILE.totalOptionRiskPct);
    const cashReservePct = num(sizing.cashReservePct, REFERENCE_PROFILE.cashReservePct);
    const vxxShortMarginMultiple = num(sizing.vxxShortMarginMultiple, REFERENCE_PROFILE.vxxShortMarginMultiple);
    const percentInputs = [
      ["cashReservePct", cashReservePct],
      ["qqqCorePct", num(sizing.qqqCorePct, REFERENCE_PROFILE.qqqCorePct)],
      ["vxxNormalPct", num(sizing.vxxNormalPct, REFERENCE_PROFILE.vxxNormalPct)],
      ["vxxHighPct", num(sizing.vxxHighPct, REFERENCE_PROFILE.vxxHighPct)],
      ["totalOptionRiskPct", optionRiskPct],
      ...OPTION_STRATEGIES.filter(strategy => strategy.mainBudgetEligible).map(strategy => [strategy.riskPctField, num(sizing[strategy.riskPctField], strategy.defaultRiskPct)])
    ];
    const invalidPercent = percentInputs.find(([key, value]) => !Number.isFinite(value) || value < 0 || value > 100);
    const invalidMarginMultiple = !Number.isFinite(vxxShortMarginMultiple) || vxxShortMarginMultiple <= 0 || vxxShortMarginMultiple > 10;
    const cashReserveUsd = Math.max(0, Math.min(cashPool, cashPool * cashReservePct / 100));
    const availableAfterReserve = Math.max(0, cashPool - cashReserveUsd);
    const totalOptionRiskPool = Math.max(0, Math.min(nav * Math.max(0, optionRiskPct) / 100, availableAfterReserve));
    const stockCapitalPool = Math.max(0, availableAfterReserve - totalOptionRiskPool);
    const results = [];
    if (market.blocked || !(nav > 0) || cashPool < 0 || invalidPercent || invalidMarginMultiple) {
      for (const row of [{ key: "qqqShares", label: "QQQ CORE SHARES", current: whole(holdings.qqqShares) }, { key: "vxxShortShares", label: "VXX SHORT SHARES", current: whole(holdings.vxxShortShares) }]) {
        results.push({ ...row, capacity: null, target: row.current, delta: 0, action: "BLOCKED", status: market.blocked ? market.status : invalidPercent ? "INVALID_PERCENT" : invalidMarginMultiple ? "INVALID_MARGIN_MULTIPLE" : "INVALID_NAV_OR_CASH", reason: market.blocked ? market.reason : invalidPercent ? (invalidPercent[0] + " must be between 0 and 100; no sizing changes are produced.") : invalidMarginMultiple ? "VXX short margin reserve multiple must be > 0 and <= 10; no sizing changes are produced." : "NAV must be positive and cash pool cannot be negative." });
      }
      for (const strategy of OPTION_STRATEGIES) {
        const current = whole(holdings[strategy.key]);
        results.push({ key: strategy.key, id: strategy.id, label: strategy.label, family: strategy.family, current, capacity: null, target: current, delta: 0, action: "BLOCKED", status: market.blocked ? market.status : invalidPercent ? "INVALID_PERCENT" : invalidMarginMultiple ? "INVALID_MARGIN_MULTIPLE" : "INVALID_NAV_OR_CASH", reason: market.blocked ? market.reason : invalidPercent ? (invalidPercent[0] + " must be between 0 and 100; no sizing changes are produced.") : invalidMarginMultiple ? "VXX short margin reserve multiple must be > 0 and <= 10; no sizing changes are produced." : "NAV must be positive and cash pool cannot be negative." });
      }
      return { ok: false, market, nav, cashPool, cashReservePct, cashReserveUsd, availableAfterReserve, totalOptionRiskPool, stockCapitalPool, vxxShortMarginMultiple, qqqAdditionalCapitalUsd: 0, vxxAdditionalMarginUsd: 0, qqqTargetNotionalUsd: null, vxxTargetMarginUsd: null, vxxTargetNotionalUsd: null, optionRiskReservedAtTargets: null, plannedCapitalRequiredUsd: null, remainingUnallocatedCashUsd: null, rows: results, ratioCampaign: calculateRatioCampaign(d.ratioCampaign || {}, market), boundary: { brokerOrders: false, automaticMutation: false } };
    }

    // cashPool = uncommitted capital available for this plan. Reserve cash and
    // the shared option-risk envelope first; then fund incremental QQQ buys and
    // estimated VXX short-margin collateral. Existing holdings are not re-counted
    // as fresh purchases; only positive ADD deltas consume this cash pool.
    const qqqCorePct = num(sizing.qqqCorePct, REFERENCE_PROFILE.qqqCorePct);
    const rawCoreCapacity = qqqCorePct >= 0 ? Math.floor(nav * qqqCorePct / 100 / market.qqq) : null;
    const currentQqq = whole(holdings.qqqShares);
    const cashLimitedCoreCapacity = rawCoreCapacity === null ? null : currentQqq + Math.floor(stockCapitalPool / market.qqq);
    const coreCapacity = rawCoreCapacity === null ? null : Math.min(rawCoreCapacity, cashLimitedCoreCapacity);
    let coreTarget, coreAction;
    if (coreCapacity === null) {
      coreTarget = currentQqq; coreAction = "PENDING";
    } else if (currentQqq > rawCoreCapacity) {
      coreTarget = rawCoreCapacity; coreAction = "REDUCE";
    } else if (market.allowNew) {
      coreTarget = Math.min(rawCoreCapacity, currentQqq + Math.floor(stockCapitalPool / market.qqq));
      coreAction = coreTarget > currentQqq ? "ADD" : "HOLD";
    } else {
      coreTarget = currentQqq; coreAction = "HOLD";
    }
    const qqqAdditionalCapitalUsd = Math.max(0, coreTarget - currentQqq) * market.qqq;
    const qqqTargetNotionalUsd = Math.max(0, coreTarget) * market.qqq;
    const cashAfterCore = Math.max(0, stockCapitalPool - qqqAdditionalCapitalUsd);
    results.push({
      key: "qqqShares", id: "QQQ_CORE", label: "QQQ CORE SHARES", family: "hybrid",
      current: currentQqq, capacity: coreCapacity, target: coreTarget, delta: coreTarget - currentQqq,
      action: coreAction, status: "READY",
      unitPrice: market.qqq, incrementalCapitalUsd: qqqAdditionalCapitalUsd, targetNotionalUsd: qqqTargetNotionalUsd,
      capacityNotionalUsd: coreCapacity === null ? null : coreCapacity * market.qqq,
      reason: "Maximum shares are capped by NAV allocation and cash left after the cash reserve + shared option-risk envelope. Adds require CARRY; over-cap reductions remain visible."
    });

    const vxxBasePct = market.backwardation ? 0 : (market.high ? num(sizing.vxxHighPct, REFERENCE_PROFILE.vxxHighPct) : num(sizing.vxxNormalPct, REFERENCE_PROFILE.vxxNormalPct));
    const rawVxxCapacity = vxxBasePct >= 0 ? Math.floor(nav * vxxBasePct / 100 / market.vxx) : null;
    const currentVxx = whole(holdings.vxxShortShares);
    const vxxMarginPerShare = market.vxx * vxxShortMarginMultiple;
    const cashLimitedVxxCapacity = rawVxxCapacity === null ? null : currentVxx + Math.floor(cashAfterCore / vxxMarginPerShare);
    const vxxCapacity = market.backwardation ? 0 : (rawVxxCapacity === null ? null : Math.min(rawVxxCapacity, cashLimitedVxxCapacity));
    let vxxTarget, vxxAction;
    if (market.backwardation) {
      vxxTarget = 0; vxxAction = currentVxx > 0 ? "REDUCE" : "HOLD";
    } else if (vxxCapacity === null) {
      vxxTarget = currentVxx; vxxAction = "PENDING";
    } else if (currentVxx > rawVxxCapacity) {
      vxxTarget = rawVxxCapacity; vxxAction = "REDUCE";
    } else if (market.allowNew) {
      vxxTarget = Math.min(rawVxxCapacity, currentVxx + Math.floor(cashAfterCore / vxxMarginPerShare));
      vxxAction = vxxTarget > currentVxx ? "ADD" : "HOLD";
    } else {
      vxxTarget = currentVxx; vxxAction = "HOLD";
    }
    const vxxAdditionalMarginUsd = Math.max(0, vxxTarget - currentVxx) * vxxMarginPerShare;
    const vxxTargetMarginUsd = Math.max(0, vxxTarget) * vxxMarginPerShare;
    const vxxTargetNotionalUsd = Math.max(0, vxxTarget) * market.vxx;
    results.push({
      key: "vxxShortShares", id: "VXX_SHORT_STOCK", label: "VXX SHORT SHARES", family: "hybrid",
      current: currentVxx, capacity: vxxCapacity, target: vxxTarget, delta: vxxTarget - currentVxx,
      action: vxxAction, status: "READY",
      unitPrice: market.vxx, marginMultiple: vxxShortMarginMultiple,
      incrementalCapitalUsd: vxxAdditionalMarginUsd, targetMarginUsd: vxxTargetMarginUsd, targetNotionalUsd: vxxTargetNotionalUsd,
      capacityNotionalUsd: vxxCapacity === null ? null : vxxCapacity * market.vxx,
      reason: market.backwardation
        ? "Backwardation policy target is zero. VXX short stock still has unbounded upside risk."
        : "Notional cap uses the VIX regime; incremental capacity also reserves the entered VXX short-margin multiple. Confirm this estimate with your broker. It is not a hard loss cap."
    });
    const working = [];
    for (const strategy of OPTION_STRATEGIES) {
      const current = whole(holdings[strategy.key]);
      const mainBudgetEligible = strategy.mainBudgetEligible === true;
      const budgetPct = mainBudgetEligible ? Math.max(0, num(sizing[strategy.riskPctField], strategy.defaultRiskPct)) : 0;
      const enabled = mainBudgetEligible && (strategy.baseline || permissions[strategy.key] === true);
      const candidate = strategy.candidateKey ? candidates[strategy.candidateKey] : null;
      const risk = candidateRisk(strategy, candidate, d.manualRiskPerUnit && d.manualRiskPerUnit[strategy.key]);
      const sellerBlocked = strategy.seller && (market.backwardation || market.high);
      let rawCapacity = null;
      let status = "OUTSIDE_MAIN_BUDGET";
      let reason = "Research-only structure is deliberately excluded from the primary portfolio budget. It must not reserve the main option-risk pool or create a main-plan capacity.";

      if (mainBudgetEligible) {
        rawCapacity = 0;
        status = "OFF";
        reason = risk.reason;
        if (risk.source === "ADJUSTED_CONTRACT_BLOCKED") {
          rawCapacity = null;
          status = "BLOCKED_CONTRACT";
          reason = risk.reason;
        } else if (budgetPct <= 0) {
          rawCapacity = 0;
          status = "OFF";
          reason = "Risk budget is 0%: no new capacity is allocated to this primary seller leg.";
        } else if (!enabled) {
          rawCapacity = 0;
          status = "NOT_ENABLED";
          reason = "This primary add-on is not enabled for capacity.";
        } else if (sellerBlocked) {
          rawCapacity = 0;
          status = "RISK_OFF";
          reason = "High VIX or VX backwardation disables this volatility-seller leg.";
        } else if (!risk.ready) {
          rawCapacity = null;
          status = "PENDING";
        } else if (strategy.kind === "coveredCall") {
          rawCapacity = Math.floor(Math.max(0, coreTarget) / 100);
          status = "READY";
          reason = "Covered call capacity is capped at floor(QQQ shares / 100); never sell more calls than covered shares.";
        } else {
          rawCapacity = Math.floor((nav * budgetPct / 100) / risk.riskPerUnit);
          status = risk.source === "MANUAL_STRESS_ESTIMATE" ? "STRESS_ONLY" : (risk.source.startsWith("MANUAL") ? "MANUAL_RISK_INPUT" : "READY");
        }
        if (strategy.kind === "hubDefinedRisk" && candidate && candidate.gatePass === false) {
          rawCapacity = 0;
          status = "WAITING_FOR_GATE";
          reason = candidate.reason || "The Hub research structure's entry gate has not fired.";
        } else if (strategy.kind === "hubDefinedRisk" && candidate && Number.isFinite(num(candidate.maxUnits))) {
          rawCapacity = Math.min(rawCapacity === null ? num(candidate.maxUnits) : rawCapacity, Math.max(0, whole(candidate.maxUnits)));
        }
      }

      working.push({
        strategy, current, mainBudgetEligible, budgetPct, enabled, candidate, risk, rawCapacity, status, reason, sellerBlocked,
        requestedRiskBudgetUsd: mainBudgetEligible ? Math.max(0, nav * budgetPct / 100) : 0,
        allocatedRiskBudgetUsd: 0, capacity: rawCapacity
      });
    }

    // Shared pool uses proportional allocation, not a priority queue. Each
    // enabled/quoted strategy receives its share of the common risk pool based
    // on its editable NAV percentage. If requested weights exceed the pool,
    // every eligible strategy scales down by the same factor before integer
    // contract rounding. Unquoted, disabled and gated-off legs reserve nothing.
    const eligible = working.filter(item =>
      item.mainBudgetEligible && item.enabled && item.budgetPct > 0 && item.rawCapacity !== null &&
      item.risk.ready && Number.isFinite(item.risk.riskPerUnit) && item.risk.riskPerUnit > 0 &&
      item.strategy.kind !== "coveredCall" && !item.sellerBlocked
    );
    const totalRequestedRiskBudgetsUsd = eligible.reduce((sum, item) => sum + item.requestedRiskBudgetUsd, 0);
    const riskScaleFactor = totalRequestedRiskBudgetsUsd > totalOptionRiskPool && totalRequestedRiskBudgetsUsd > 0
      ? totalOptionRiskPool / totalRequestedRiskBudgetsUsd : 1;
    for (const item of eligible) {
      item.allocatedRiskBudgetUsd = item.requestedRiskBudgetUsd * riskScaleFactor;
      item.capacity = Math.min(item.rawCapacity, Math.floor((item.allocatedRiskBudgetUsd + 1e-9) / item.risk.riskPerUnit));
    }

    let remainingRiskPool = totalOptionRiskPool;
    for (const item of working.sort((a, b) => a.strategy.priority - b.strategy.priority)) {
      const { strategy, current, budgetPct, risk, sellerBlocked } = item;
      let capacity = item.capacity;
      if (capacity !== null && capacity > 0 && risk.riskPerUnit > 0 && strategy.kind !== "coveredCall") {
        const actualRiskLimit = eligible.includes(item) ? item.allocatedRiskBudgetUsd : item.requestedRiskBudgetUsd;
        capacity = Math.min(capacity, Math.floor((actualRiskLimit + 1e-9) / risk.riskPerUnit));
        item.capacity = capacity;
        remainingRiskPool = Math.max(0, remainingRiskPool - capacity * risk.riskPerUnit);
      }
      let target, action, delta;
      const policyExit = item.mainBudgetEligible && strategy.seller && (market.backwardation || market.high);
      if (market.blocked) {
        target = current; action = "BLOCKED"; delta = 0;
      } else if (item.mainBudgetEligible && risk.source === "ADJUSTED_CONTRACT_BLOCKED") {
        target = current; action = "BLOCKED"; delta = 0;
      } else if (!item.mainBudgetEligible) {
        target = current; action = "OUTSIDE_BUDGET"; delta = 0;
      } else if (policyExit) {
        target = 0; action = current > 0 ? "REDUCE" : "HOLD"; delta = target - current;
      } else if (capacity === null) {
        target = current; action = "PENDING"; delta = 0;
      } else {
        let canAdd = market.allowNew && item.enabled && budgetPct > 0 && !sellerBlocked;
        if (!strategy.baseline && strategy.kind === "debit" && permissions.allowProtectionBuys === true && market.status === "FRESH") canAdd = budgetPct > 0;
        const actionResult = actionFor(current, capacity, canAdd);
        target = actionResult.target; action = actionResult.action; delta = actionResult.delta;
      }
      if (item.mainBudgetEligible && strategy.kind === "coveredCall" && target > Math.floor(Math.max(0, coreTarget) / 100)) {
        target = Math.floor(Math.max(0, coreTarget) / 100);
        delta = target - current;
        action = delta < 0 ? "REDUCE" : delta > 0 ? "ADD" : "HOLD";
      }
      if (item.mainBudgetEligible && strategy.kind === "stressOnly" && item.status !== "OFF" && item.status !== "NOT_ENABLED" && item.status !== "PENDING") {
        item.status = "STRESS_ONLY";
        item.reason = "Target is based on a user-entered stress-loss estimate only; ratio tails are NOT hard-capped.";
      }
      results.push({
        key: strategy.key, id: strategy.id, label: strategy.label, family: strategy.family,
        current, capacity: capacity === null ? null : Math.max(0, capacity),
        target, delta, action,
        status: item.status,
        mainBudgetEligible: item.mainBudgetEligible,
        riskBudgetUsd: item.requestedRiskBudgetUsd,
        allocatedRiskBudgetUsd: item.mainBudgetEligible ? item.allocatedRiskBudgetUsd : 0,
        riskPerUnit: risk.riskPerUnit,
        capitalPerUnitUsd: risk.capitalPerUnitUsd ?? risk.riskPerUnit,
        targetRiskReserveUsd: item.mainBudgetEligible && risk.riskPerUnit && target > 0 && strategy.kind !== "coveredCall" ? risk.riskPerUnit * target : 0,
        riskSource: risk.source,
        candidateSource: item.candidate?.source || null,
        reason: sellerBlocked && !policyExit ? "No new seller entries in this market state; over-cap trimming remains allowed." : item.reason,
        maxLossIsHardCap: !["stressOnly", "coveredCall"].includes(strategy.kind),
        strategyKind: strategy.kind
      });
    }

    // If detailed held-option terms are incomplete, block only the affected strategy
    // row. A count is not enough to claim a reliable target for an unknown deliverable.
    const positionRegister = d.positionRegister || {};
    if (positionRegister.useForSizing === true && Array.isArray(positionRegister.blockingKeys)) {
      for (const key of positionRegister.blockingKeys) {
        const row = results.find(item => item.key === key && item.mainBudgetEligible);
        if (!row) continue;
        row.capacity = null;
        row.target = row.current;
        row.delta = 0;
        row.action = "BLOCKED";
        row.status = "BLOCKED_POSITION_TERMS";
        row.allocatedRiskBudgetUsd = 0;
        row.riskPerUnit = null;
        row.targetRiskReserveUsd = null;
        row.riskSource = "POSITION_REGISTER_TERMS_UNVERIFIED";
        row.reason = "The current position register has an option package with unverified expiry / leg identity / deliverable or multiplier. Verify the held contract terms before sizing changes for this strategy.";
      }
    }

    return {
      ok: true,
      market, nav, cashPool, cashReservePct, cashReserveUsd, availableAfterReserve,
      totalOptionRiskPool, stockCapitalPool, vxxShortMarginMultiple,
      totalRequestedRiskBudgetsUsd, riskScaleFactor, remainingRiskPool,
      qqqAdditionalCapitalUsd, qqqTargetNotionalUsd, vxxAdditionalMarginUsd,
      vxxTargetMarginUsd, vxxTargetNotionalUsd,
      optionRiskReservedAtTargets: results.filter(r => r.mainBudgetEligible && r.riskPerUnit && r.target > 0 && r.strategyKind !== "coveredCall").reduce((sum, r) => sum + r.riskPerUnit * r.target, 0),
      plannedCapitalRequiredUsd: cashReserveUsd + totalOptionRiskPool + qqqAdditionalCapitalUsd + vxxAdditionalMarginUsd,
      remainingUnallocatedCashUsd: Math.max(0, cashPool - cashReserveUsd - totalOptionRiskPool - qqqAdditionalCapitalUsd - vxxAdditionalMarginUsd),
      rows: results,
      ratioCampaign: calculateRatioCampaign(d.ratioCampaign || {}, market),
      boundary: {
        brokerOrders: false,
        automaticMutation: false,
        source: "V3_READ_ONLY_MARKET_STATE + OPERATOR_INPUTS",
        missingCandidateNeverFabricated: true
      }
    };
  }

  function calculateRatioCampaign(input, market) {
    const d = input || {};
    const enabled = d.enabled === true;
    const currentFar = whole(d.currentFarShort);
    const currentNear = whole(d.currentNearLong);
    const nShort = Math.min(100, Math.max(1, whole(d.nShort, 10) || 10));
    const farDeltaAbs = Math.min(1, Math.max(0.01, Math.abs(num(d.farDelta, 0.08))));
    const nearDeltaAbs = Math.min(1, Math.max(0.01, Math.abs(num(d.nearDelta, 0.5))));
    const coverage = Math.min(5, Math.max(0, num(d.coverageMult, 1.5)));
    const maxStack = Math.min(20, Math.max(1, whole(d.maxStack, 5) || 5));
    const distancePct = Math.min(100, Math.max(0, num(d.farDistancePct, 10)));
    const gammaRel = Math.min(100, Math.max(0, num(d.gammaRel, 1)));
    const deltaJump = Math.min(1, Math.max(0, num(d.deltaJump, 0)));
    // Preserves the legacy Live Hedge risk-state scoring: delta, distance,
    // relative gamma and delta-jump affect the number of near-long contracts.
    const dScore = farDeltaAbs < 0.04 ? 1 : farDeltaAbs < 0.06 ? 2 : farDeltaAbs < 0.08 ? 3 : farDeltaAbs < 0.10 ? 4 : 5;
    const distance = distancePct / 100;
    const xScore = distance > 0.10 ? 1 : distance > 0.07 ? 2 : distance > 0.04 ? 3 : distance > 0.02 ? 4 : 5;
    const gScore = gammaRel < 1.20 && deltaJump < 0.01 ? 1 : gammaRel < 1.50 && deltaJump < 0.02 ? 2 : 3;
    const riskScore = 0.50 * dScore + 0.30 * xScore + 0.20 * gScore;
    const baseNearTarget = Math.max(1, Math.min(maxStack, Math.ceil((coverage * nShort * farDeltaAbs) / nearDeltaAbs)));
    const stackAdjustment = riskScore >= 4.2 ? 2 : riskScore >= 3.2 ? 1 : 0;
    const riskAdjustedNearTarget = Math.max(1, Math.min(maxStack, baseNearTarget + stackAdjustment));
    const riskMeta = { farDeltaAbs, nearDeltaAbs, distancePct, gammaRel, deltaJump, dScore, xScore, gScore, riskScore, baseNearTarget, stackAdjustment };
    const targetFar = !enabled ? 0 : nShort;
    const targetNear = !enabled ? 0 : riskAdjustedNearTarget;
    if (market.blocked) return { enabled, currentFar, currentNear, targetFar: currentFar, targetNear: currentNear, farDelta: 0, nearDelta: 0, actionFar: "BLOCKED", actionNear: "BLOCKED", noHardLossCap: true, status: "BLOCKED", ...riskMeta };
    if (market.riskOff) return { enabled, currentFar, currentNear, targetFar: 0, targetNear: 0, farDelta: -currentFar, nearDelta: -currentNear, actionFar: currentFar ? "REDUCE" : "HOLD", actionNear: currentNear ? "REDUCE" : "HOLD", noHardLossCap: true, status: "RISK_OFF_EXIT_REVIEW", ...riskMeta };
    if (!enabled) return { enabled, currentFar, currentNear, targetFar: 0, targetNear: 0, farDelta: -currentFar, nearDelta: -currentNear, actionFar: currentFar ? "REDUCE" : "HOLD", actionNear: currentNear ? "REDUCE" : "HOLD", noHardLossCap: true, status: "DISABLED_MANUAL_REVIEW", ...riskMeta };
    const nearAction = actionFor(currentNear, targetNear, market.allowNew);
    const farAction = actionFor(currentFar, targetFar, market.allowNew);
    return { enabled, nShort, currentFar, currentNear, targetFar, targetNear, farDelta: farAction.delta, nearDelta: nearAction.delta, actionFar: farAction.action, actionNear: nearAction.action, noHardLossCap: true, status: "LEGACY_N_X_NO_HARD_LOSS_CAP", note: "Per campaign only. The legacy 10:near-long rule is a management profile, not a portfolio-wide capacity or max-loss guarantee.", ...riskMeta };
  }
  function normalizeOptionChain(payload, right) {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload[right === "put" ? "puts" : "calls"])) return payload[right === "put" ? "puts" : "calls"];
    const result = payload?.optionChain?.result?.[0], opts = result?.options?.[0];
    const rows = opts?.[right === "put" ? "puts" : "calls"];
    return Array.isArray(rows) ? rows : [];
  }

  function expiryMs(v) {
    if (typeof v === "number" && Number.isFinite(v)) return v < 1e12 ? v * 1000 : v;
    if (typeof v === "string" && /^\s*\d+(?:\.\d+)?\s*$/.test(v)) {
      const n = Number(v); return n < 1e12 ? n * 1000 : n;
    }
    if (typeof v === "string" && v.trim()) { const p = Date.parse(v); return Number.isFinite(p) ? p : null; }
    return null;
  }

  function normalCdf(x) {
    const sign = x < 0 ? -1 : 1, ax = Math.abs(x);
    const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911;
    const t=1/(1+p*ax);
    const erf=sign*(1-(((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*Math.exp(-ax*ax));
    return 0.5*(1+erf);
  }


  function isAdjustedVxxContractSymbol(value) {
    const symbol = String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    // Standard VXX symbols use root VXX + six expiry digits. Adjusted VXX1/VXX2
    // roots add a root digit before that six-digit expiry; 1VXX2-style roots also exist.
    return /^(?:VXX[12]|1VXX[12])\d{6}[CP]\d{8}$/.test(symbol);
  }

  // Quote width / midpoint is a descriptive execution-quality triage metric.
  // It does not establish live executability or approve a strategy.
  function quoteQuality(row) {
    const bid = num(row && row.bid), ask = num(row && row.ask);
    if (bid === null || ask === null || bid <= 0 || ask < bid) {
      return { bid, ask, width: null, midpoint: null, widthPctMid: null, quality: "UNKNOWN" };
    }
    const width = ask - bid;
    const midpoint = (ask + bid) / 2;
    const widthPctMid = midpoint > 0 ? width / midpoint * 100 : null;
    const quality = widthPctMid === null ? "UNKNOWN" :
      widthPctMid <= 10 ? "TIGHT" : widthPctMid <= 25 ? "WATCH" : "WIDE";
    return { bid, ask, width, midpoint, widthPctMid, quality };
  }

  function estimateDelta(spot, strike, dte, iv, right) {
    if (![spot, strike, dte, iv].every(Number.isFinite) || spot <= 0 || strike <= 0 || dte <= 0 || iv <= 0) return null;
    const t = dte / 365, sigma = iv, d1 = (Math.log(spot/strike)+(0.03+0.5*sigma*sigma)*t)/(sigma*Math.sqrt(t));
    const call = normalCdf(d1);
    return right === "put" ? call - 1 : call;
  }

  function findCreditVertical(payload, spot, right, targetDte = 45, targetAbsDelta = 0.16, asOf = null) {
    if (!Number.isFinite(spot) || spot <= 0 || !["call","put"].includes(right)) return null;
    const nowMs = asOf ? Date.parse(String(asOf) + "T00:00:00Z") : Date.now();
    const rows = normalizeOptionChain(payload, right).map(x => {
      const exp = expiryMs(x.expiration ?? x.expiry ?? x.expirationDate);
      const dte = num(x.days, Number.isFinite(exp) ? (exp-nowMs)/86400000 : null);
      const strike = num(x.strike), bid = num(x.bid), ask = num(x.ask), iv = num(x.impliedVolatility);
      const rawDelta = num(x.delta);
      const delta = rawDelta !== null ? rawDelta : estimateDelta(spot, strike, dte, iv, right);
      return { ...x, expiryMs: exp, expiry: Number.isFinite(exp) ? new Date(exp).toISOString().slice(0,10) : null, dte, strike, bid, ask, iv, delta, deltaSource: rawDelta !== null ? "PROVIDER_DELTA" : "BS_ESTIMATE" };
    }).filter(x => Number.isFinite(x.expiryMs) && Number.isFinite(x.dte) && x.dte >= 14 && x.dte <= 120 &&
      Number.isFinite(x.strike) && x.strike > 0 && Number.isFinite(x.bid) && Number.isFinite(x.ask) &&
      x.bid > 0 && x.ask >= x.bid && Number.isFinite(x.delta) &&
      (right === "call" ? x.strike > spot && x.delta > 0 && x.delta <= 0.30 : x.strike < spot && x.delta < 0 && x.delta >= -0.30));
    if (!rows.length) return null;
    const expiries = [...new Set(rows.map(x => x.expiryMs))].sort((a,b) => Math.abs((a-nowMs)/86400000-targetDte) - Math.abs((b-nowMs)/86400000-targetDte));
    const expiry = expiries[0], pool = rows.filter(x => x.expiryMs === expiry);
    pool.sort((a,b) => Math.abs(Math.abs(a.delta)-targetAbsDelta)-Math.abs(Math.abs(b.delta)-targetAbsDelta));
    const short = pool[0];
    const wingRows = pool.filter(x => right === "call" ? x.strike > short.strike : x.strike < short.strike);
    wingRows.sort((a,b) => {
      const da = Math.abs(a.strike - short.strike * (right === "call" ? 1.015 : 0.985));
      const db = Math.abs(b.strike - short.strike * (right === "call" ? 1.015 : 0.985));
      return da-db;
    });
    if (!wingRows.length) return null;
    const wing = wingRows[0];
    const credit = short.bid - wing.ask;
    const width = Math.abs(wing.strike - short.strike);
    if (!(credit > 0 && width > credit)) return null;
    const shortQuote = quoteQuality(short), longQuote = quoteQuality(wing);
    const isVxxChain = String(payload && payload.symbol || "").toUpperCase() === "VXX";
    const adjustedSymbols = [short.contractSymbol || short.symbol, wing.contractSymbol || wing.symbol]
      .filter(isAdjustedVxxContractSymbol);
    const adjustedVxxTerms = isVxxChain && adjustedSymbols.length > 0;
    return {
      right, expiry: short.expiry, dte: short.dte,
      shortStrike: short.strike, longStrike: wing.strike,
      shortContractSymbol: short.contractSymbol || short.symbol || null,
      longContractSymbol: wing.contractSymbol || wing.symbol || null,
      shortDelta: short.delta, longDelta: wing.delta,
      deltaSource: short.deltaSource,
      shortBid: short.bid, shortAsk: short.ask,
      longBid: wing.bid, longAsk: wing.ask,
      shortQuoteWidth: shortQuote.width, shortQuoteMid: shortQuote.midpoint,
      shortQuoteWidthPctMid: shortQuote.widthPctMid, shortQuoteQuality: shortQuote.quality,
      longQuoteWidth: longQuote.width, longQuoteMid: longQuote.midpoint,
      longQuoteWidthPctMid: longQuote.widthPctMid, longQuoteQuality: longQuote.quality,
      credit, width,
      multiplierAssumption: 100, multiplierVerified: false,
      contractTermsStatus: adjustedVxxTerms ? "ADJUSTED_DELIVERABLE_BLOCKED" : "UNVERIFIED_NOT_BROKER_CONFIRMED",
      adjustedContractSymbols: adjustedSymbols,
      maxLossPerSpread: (width-credit)*100,
      source: "YAHOO_OPTION_CHAIN_DELAYED_OR_ESTIMATED",
      quoteTimestampStatus: "NOT_VERIFIED_BY_PROVIDER",
      candidateStatus: adjustedVxxTerms ? "ADJUSTED_CONTRACT_BLOCKED" : "REVIEW_BEFORE_USE"
    };
  }

  function findShortCall(payload, spot, targetDte = 45, targetAbsDelta = 0.16, asOf = null) {
    if (!Number.isFinite(spot) || spot <= 0) return null;
    const nowMs = asOf ? Date.parse(String(asOf) + "T00:00:00Z") : Date.now();
    const rows = normalizeOptionChain(payload, "call").map(x => {
      const exp = expiryMs(x.expiration ?? x.expiry ?? x.expirationDate);
      const dte = num(x.days, Number.isFinite(exp) ? (exp-nowMs)/86400000 : null);
      const strike = num(x.strike), bid = num(x.bid), ask = num(x.ask), iv = num(x.impliedVolatility), rawDelta = num(x.delta);
      const delta = rawDelta !== null ? rawDelta : estimateDelta(spot, strike, dte, iv, "call");
      return { ...x, expiryMs: exp, expiry: Number.isFinite(exp) ? new Date(exp).toISOString().slice(0,10) : null, dte, strike, bid, ask, iv, delta, deltaSource: rawDelta !== null ? "PROVIDER_DELTA" : "BS_ESTIMATE" };
    }).filter(x => Number.isFinite(x.expiryMs) && Number.isFinite(x.dte) && x.dte >= 14 && x.dte <= 120 &&
      Number.isFinite(x.strike) && x.strike >= spot && Number.isFinite(x.bid) && x.bid > 0 &&
      Number.isFinite(x.ask) && x.ask >= x.bid && Number.isFinite(x.delta) && x.delta > 0 && x.delta <= 0.35);
    if (!rows.length) return null;
    rows.sort((a,b) => Math.abs(a.dte-targetDte)-Math.abs(b.dte-targetDte) ||
      Math.abs(Math.abs(a.delta)-targetAbsDelta)-Math.abs(Math.abs(b.delta)-targetAbsDelta) || a.strike-b.strike);
    const x = rows[0];
    const shortQuote = quoteQuality(x);
    return {
      type: "coveredCall", right: "call", expiry: x.expiry, dte: x.dte,
      strike: x.strike, contractSymbol: x.contractSymbol || x.symbol || null,
      shortBid: x.bid, shortAsk: x.ask, ask: x.ask, delta: x.delta,
      shortQuoteWidth: shortQuote.width, shortQuoteMid: shortQuote.midpoint,
      shortQuoteWidthPctMid: shortQuote.widthPctMid, shortQuoteQuality: shortQuote.quality,
      deltaSource: x.deltaSource, source: "YAHOO_OPTION_CHAIN_DELAYED_OR_ESTIMATED",
      quoteTimestampStatus: "NOT_VERIFIED_BY_PROVIDER",
      candidateStatus: "REVIEW_BEFORE_USE"
    };
  }

  function findLongOption(payload, spot, right, targetDte = 45, targetAbsDelta = 0.25, asOf = null) {
    if (!Number.isFinite(spot) || spot <= 0 || !["call","put"].includes(right)) return null;
    const nowMs = asOf ? Date.parse(String(asOf) + "T00:00:00Z") : Date.now();
    const rows = normalizeOptionChain(payload, right).map(x => {
      const exp = expiryMs(x.expiration ?? x.expiry ?? x.expirationDate);
      const dte = num(x.days, Number.isFinite(exp) ? (exp-nowMs)/86400000 : null);
      const strike = num(x.strike), ask = num(x.ask), iv = num(x.impliedVolatility), rawDelta = num(x.delta);
      const delta = rawDelta !== null ? rawDelta : estimateDelta(spot, strike, dte, iv, right);
      return { ...x, expiryMs: exp, expiry: Number.isFinite(exp) ? new Date(exp).toISOString().slice(0,10) : null, dte, strike, ask, iv, delta, deltaSource: rawDelta !== null ? "PROVIDER_DELTA" : "BS_ESTIMATE" };
    }).filter(x => Number.isFinite(x.expiryMs) && Number.isFinite(x.dte) && x.dte >= 14 && x.dte <= 120 && Number.isFinite(x.strike) && x.strike > 0 && Number.isFinite(x.ask) && x.ask > 0 && Number.isFinite(x.delta) &&
      (right === "call" ? x.delta > 0 && x.strike >= spot : x.delta < 0 && x.strike <= spot));
    if (!rows.length) return null;
    rows.sort((a,b) => Math.abs(a.dte-targetDte)-Math.abs(b.dte-targetDte) || Math.abs(Math.abs(a.delta)-targetAbsDelta)-Math.abs(Math.abs(b.delta)-targetAbsDelta));
    const x = rows[0];
    return { right, expiry: x.expiry, dte: x.dte, strike: x.strike, ask: x.ask, delta: x.delta, deltaSource: x.deltaSource, source: "YAHOO_OPTION_CHAIN_DELAYED_OR_ESTIMATED", candidateStatus: "REVIEW_BEFORE_USE" };
  }

  const Engine = { REFERENCE_PROFILE, OPTION_STRATEGIES, num, termSlope, assessMarket, quoteQuality, isAdjustedVxxContractSymbol, candidateRisk, calculatePortfolio, calculateRatioCampaign, findCreditVertical, findLongOption, findShortCall };
  root.HybridOperatorEngineV1 = Engine;
  if (typeof module !== "undefined" && module.exports) module.exports = Engine;
})(typeof globalThis !== "undefined" ? globalThis : this);
