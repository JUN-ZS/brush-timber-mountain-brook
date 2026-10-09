(function (root) {
  "use strict";

  const REFERENCE_PROFILE = Object.freeze({
    name: "V3 policy reference — preview only",
    qqqCorePct: 42,
    vxxNormalPct: 18,
    vxxHighPct: 10,
    qqqCallRiskPct: 1.2,
    vxxCallRiskPct: 2,
    vxxPutRiskPct: 0,
    qqqBullPutRiskPct: 0,
    totalOptionRiskPct: 3.2,
    vixHigh: 28,
    termSafe: 5,
    maxTermAgeDays: 4
  });

  // Strategies discussed across Hybrid, Live Hedge and Hub. Research-only legs
  // are present for comparison, but never authorize entries by their presence.
  const OPTION_STRATEGIES = Object.freeze([
    { key: "qqqCallSpreads", id: "QQQ_CALL_CREDIT", label: "QQQ FAR CALL / CALL-CREDIT", family: "hybrid", kind: "creditVertical", candidateKey: "qqqCall", riskPctField: "qqqCallRiskPct", defaultRiskPct: 1.2, seller: true, baseline: true, priority: 1 },
    { key: "vxxCallSpreads", id: "VXX_CALL_CREDIT", label: "VXX CALL-CREDIT", family: "hybrid", kind: "creditVertical", candidateKey: "vxxCall", riskPctField: "vxxCallRiskPct", defaultRiskPct: 2, seller: true, baseline: true, priority: 2 },
    { key: "vxxPutSpreads", id: "VXX_PUT_CREDIT", label: "VXX PUT-CREDIT", family: "research", kind: "creditVertical", candidateKey: "vxxPut", riskPctField: "vxxPutRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 3 },
    { key: "qqqBullPutSpreads", id: "QQQ_BULL_PUT", label: "QQQ BULL-PUT CREDIT", family: "research", kind: "creditVertical", candidateKey: "qqqPut", riskPctField: "qqqBullPutRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 4 },
    { key: "qqqBearCallSpreads", id: "QQQ_BEAR_CALL", label: "QQQ BEAR-CALL CREDIT", family: "research", kind: "creditVertical", candidateKey: "qqqCall", riskPctField: "qqqBearCallRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 5 },
    { key: "coveredCalls", id: "COVERED_CALL", label: "COVERED CALL", family: "research", kind: "coveredCall", candidateKey: "qqqCall", riskPctField: "coveredCallRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 6 },
    { key: "protectivePuts", id: "QQQ_PROTECTIVE_PUT", label: "QQQ PROTECTIVE PUT", family: "research", kind: "debit", candidateKey: "qqqLongPut", riskPctField: "protectivePutRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 7 },
    { key: "longCalls", id: "LONG_CALL", label: "LONG CALL", family: "research", kind: "debit", candidateKey: "qqqLongCall", riskPctField: "longCallRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 8 },
    { key: "longPuts", id: "LONG_PUT", label: "LONG PUT", family: "research", kind: "debit", candidateKey: "qqqLongPut", riskPctField: "longPutRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 9 },
    { key: "longStraddles", id: "LONG_STRADDLE", label: "LONG STRADDLE", family: "research", kind: "manualDebit", candidateKey: null, riskPctField: "longStraddleRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 10 },
    { key: "ironFlies", id: "IRON_FLY", label: "IRON FLY", family: "research", kind: "manualRisk", candidateKey: null, riskPctField: "ironFlyRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 11 },
    { key: "ironCondors", id: "IRON_CONDOR", label: "IRON CONDOR", family: "research", kind: "manualRisk", candidateKey: null, riskPctField: "ironCondorRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 12 },
    { key: "brokenWings", id: "BROKEN_WING", label: "BROKEN-WING BUTTERFLY", family: "research", kind: "manualRisk", candidateKey: null, riskPctField: "brokenWingRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 13 },
    { key: "calendars", id: "CALENDAR", label: "CALENDAR SPREAD", family: "research", kind: "manualDebit", candidateKey: null, riskPctField: "calendarRiskPct", defaultRiskPct: 0, seller: false, baseline: false, priority: 14 },
    { key: "ratioCalls", id: "CALL_RATIO_1_N_1", label: "CALL RATIO 1:N:1", family: "research", kind: "stressOnly", candidateKey: null, riskPctField: "ratioCallRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 15 },
    { key: "ratioPuts", id: "PUT_RATIO_1_N_1", label: "PUT RATIO 1:N:1", family: "research", kind: "stressOnly", candidateKey: null, riskPctField: "ratioPutRiskPct", defaultRiskPct: 0, seller: true, baseline: false, priority: 16 }
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
      if (candidate && [candidate.width, candidate.credit].every(v => Number.isFinite(num(v))) &&
          num(candidate.width) > 0 && num(candidate.credit) > 0 && num(candidate.credit) < num(candidate.width)) {
        return { riskPerUnit: (num(candidate.width) - num(candidate.credit)) * 100, source: candidate.source || "OBSERVED_CHAIN", ready: true, reason: "Defined-risk vertical: (width − net credit) × 100." };
      }
      return { riskPerUnit: null, source: "MISSING_CHAIN", ready: false, reason: "Need a valid same-expiry vertical and positive observable net credit; no sizing invented." };
    }
    if (strategy.kind === "debit") {
      if (candidate && num(candidate.ask) > 0) return { riskPerUnit: num(candidate.ask) * 100, source: candidate.source || "OBSERVED_CHAIN", ready: true, reason: "Long option risk is the debit paid (ask × multiplier)." };
      return { riskPerUnit: null, source: "MISSING_CHAIN", ready: false, reason: "Need a positive observed option ask. No premium floor is fabricated." };
    }
    if (strategy.kind === "coveredCall") {
      if (candidate && (num(candidate.shortBid) > 0 || (candidate.type === "coveredCall" && num(candidate.credit) > 0))) return { riskPerUnit: null, source: candidate.source || "OBSERVED_CHAIN", ready: true, reason: "Contract target is bounded by QQQ shares / 100; confirm the actual covered-call short bid before use." };
      return { riskPerUnit: null, source: "MISSING_CHAIN", ready: false, reason: "Need a positive short-call bid minus long-hedge ask / covered-call candidate." };
    }
    if (strategy.kind === "manualDebit") {
      if (manual > 0) return { riskPerUnit: manual, source: "MANUAL_DEBIT_INPUT", ready: true, reason: "Manual debit / max loss per spread; verify the actual chain before use." };
      return { riskPerUnit: null, source: "PENDING_MANUAL_DEBIT", ready: false, reason: "Enter total debit per spread × multiplier; otherwise PENDING." };
    }
    if (strategy.kind === "manualRisk") {
      if (manual > 0) return { riskPerUnit: manual, source: "MANUAL_DEFINED_RISK_INPUT", ready: true, reason: "Manual max loss per spread; verify strike geometry and net credit." };
      return { riskPerUnit: null, source: "PENDING_MANUAL_RISK", ready: false, reason: "Enter the verified maximum loss per spread; otherwise PENDING." };
    }
    if (strategy.kind === "stressOnly") {
      if (manual > 0) return { riskPerUnit: manual, source: "MANUAL_STRESS_ESTIMATE", ready: true, reason: "Stress-loss estimate only. Ratio tails remain unbounded; this is NOT a hard loss cap." };
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
    const percentInputs = [
      ["qqqCorePct", num(sizing.qqqCorePct, REFERENCE_PROFILE.qqqCorePct)],
      ["vxxNormalPct", num(sizing.vxxNormalPct, REFERENCE_PROFILE.vxxNormalPct)],
      ["vxxHighPct", num(sizing.vxxHighPct, REFERENCE_PROFILE.vxxHighPct)],
      ["totalOptionRiskPct", optionRiskPct],
      ...OPTION_STRATEGIES.map(strategy => [strategy.riskPctField, num(sizing[strategy.riskPctField], strategy.defaultRiskPct)])
    ];
    const invalidPercent = percentInputs.find(([key, value]) => !Number.isFinite(value) || value < 0 || value > 100);
    const totalOptionRiskPool = Math.max(0, Math.min(nav * Math.max(0, optionRiskPct) / 100, Math.max(0, cashPool)));
    const results = [];
    if (market.blocked || !(nav > 0) || cashPool < 0 || invalidPercent) {
      for (const row of [{ key: "qqqShares", label: "QQQ CORE SHARES", current: whole(holdings.qqqShares) }, { key: "vxxShortShares", label: "VXX SHORT SHARES", current: whole(holdings.vxxShortShares) }]) {
        results.push({ ...row, capacity: null, target: row.current, delta: 0, action: "BLOCKED", status: market.blocked ? market.status : invalidPercent ? "INVALID_PERCENT" : "INVALID_NAV_OR_CASH", reason: market.blocked ? market.reason : invalidPercent ? (invalidPercent[0] + " must be between 0 and 100; no sizing changes are produced.") : "NAV must be positive and cash pool cannot be negative." });
      }
      for (const strategy of OPTION_STRATEGIES) {
        const current = whole(holdings[strategy.key]);
        results.push({ key: strategy.key, id: strategy.id, label: strategy.label, family: strategy.family, current, capacity: null, target: current, delta: 0, action: "BLOCKED", status: market.blocked ? market.status : invalidPercent ? "INVALID_PERCENT" : "INVALID_NAV_OR_CASH", reason: market.blocked ? market.reason : invalidPercent ? (invalidPercent[0] + " must be between 0 and 100; no sizing changes are produced.") : "NAV must be positive and cash pool cannot be negative." });
      }
      return { ok: false, market, nav, cashPool, totalOptionRiskPool, rows: results, ratioCampaign: calculateRatioCampaign(d.ratioCampaign || {}, market), boundary: { brokerOrders: false, automaticMutation: false } };
    }

    const qqqCorePct = num(sizing.qqqCorePct, REFERENCE_PROFILE.qqqCorePct);
    const coreCapacity = qqqCorePct >= 0 ? Math.floor(nav * qqqCorePct / 100 / market.qqq) : null;
    const currentQqq = whole(holdings.qqqShares);
    let coreTarget, coreAction;
    if (coreCapacity === null) {
      coreTarget = currentQqq; coreAction = "PENDING";
    } else if (currentQqq > coreCapacity) {
      coreTarget = coreCapacity; coreAction = "REDUCE";
    } else if (market.allowNew) {
      const cashLimited = currentQqq + Math.floor(Math.max(0, cashPool) / market.qqq);
      coreTarget = Math.min(coreCapacity, cashLimited);
      coreAction = coreTarget > currentQqq ? "ADD" : "HOLD";
    } else {
      coreTarget = currentQqq; coreAction = "HOLD";
    }
    results.push({ key: "qqqShares", id: "QQQ_CORE", label: "QQQ CORE SHARES", family: "hybrid", current: currentQqq, capacity: coreCapacity, target: coreTarget, delta: coreTarget - currentQqq, action: coreAction, status: "READY", reason: "Capacity is NAV × core allocation / QQQ price. Adds require CARRY; over-cap reduction remains visible in HOLD states." });

    const vxxBasePct = market.backwardation ? 0 : (market.high ? num(sizing.vxxHighPct, REFERENCE_PROFILE.vxxHighPct) : num(sizing.vxxNormalPct, REFERENCE_PROFILE.vxxNormalPct));
    const vxxCapacity = vxxBasePct >= 0 ? Math.floor(nav * vxxBasePct / 100 / market.vxx) : null;
    const currentVxx = whole(holdings.vxxShortShares);
    let vxxTarget, vxxAction;
    if (market.backwardation) {
      vxxTarget = 0; vxxAction = currentVxx > 0 ? "REDUCE" : "HOLD";
    } else if (vxxCapacity === null) {
      vxxTarget = currentVxx; vxxAction = "PENDING";
    } else if (currentVxx > vxxCapacity) {
      vxxTarget = vxxCapacity; vxxAction = "REDUCE";
    } else if (market.allowNew) {
      vxxTarget = vxxCapacity; vxxAction = vxxTarget > currentVxx ? "ADD" : "HOLD";
    } else {
      vxxTarget = currentVxx; vxxAction = "HOLD";
    }
    results.push({ key: "vxxShortShares", id: "VXX_SHORT_STOCK", label: "VXX SHORT SHARES", family: "hybrid", current: currentVxx, capacity: vxxCapacity, target: vxxTarget, delta: vxxTarget - currentVxx, action: vxxAction, status: "READY", reason: market.backwardation ? "Backwardation policy target is zero. VXX short stock still has unbounded upside risk." : "Notional cap uses VIX regime (normal/high). This is a sizing ceiling, not a hard loss cap." });

    const working = [];
    for (const strategy of OPTION_STRATEGIES) {
      const current = whole(holdings[strategy.key]);
      const budgetPct = Math.max(0, num(sizing[strategy.riskPctField], strategy.defaultRiskPct));
      const enabled = strategy.baseline || permissions[strategy.key] === true;
      const candidate = strategy.candidateKey ? candidates[strategy.candidateKey] : null;
      const risk = candidateRisk(strategy, candidate, d.manualRiskPerUnit && d.manualRiskPerUnit[strategy.key]);
      const sellerBlocked = strategy.seller && (market.backwardation || market.high);
      let rawCapacity = 0;
      let status = "OFF";
      let reason = risk.reason;
      if (budgetPct <= 0) {
        rawCapacity = 0;
        status = "OFF";
        reason = "Risk budget is 0%: strategy is disabled for new capacity; any recorded overage is visible for reduction.";
      } else if (!enabled) {
        rawCapacity = 0;
        status = "NOT_ENABLED";
        reason = "Research/add-on entry permission is not explicitly enabled.";
      } else if (sellerBlocked) {
        rawCapacity = 0;
        status = "RISK_OFF";
        reason = "High VIX or VX backwardation disables this volatility-seller leg.";
      } else if (!risk.ready) {
        rawCapacity = null;
        status = "PENDING";
      } else if (strategy.kind === "coveredCall") {
        rawCapacity = Math.floor(currentQqq / 100);
        status = "READY";
        reason = "Covered call capacity is capped at floor(QQQ shares / 100); never sell more calls than covered shares.";
      } else {
        rawCapacity = Math.floor((nav * budgetPct / 100) / risk.riskPerUnit);
        status = risk.source === "MANUAL_STRESS_ESTIMATE" ? "STRESS_ONLY" : (risk.source.startsWith("MANUAL") ? "MANUAL_RISK_INPUT" : "READY");
      }
      working.push({ strategy, current, budgetPct, enabled, candidate, risk, rawCapacity, status, reason, sellerBlocked });
    }

    let remainingRiskPool = totalOptionRiskPool;
    for (const item of working.sort((a, b) => a.strategy.priority - b.strategy.priority)) {
      const { strategy, current, budgetPct, risk, sellerBlocked } = item;
      let capacity = item.rawCapacity;
      if (capacity !== null && capacity > 0 && risk.riskPerUnit > 0 && strategy.kind !== "coveredCall") {
        const globalCap = Math.floor((remainingRiskPool + 1e-9) / risk.riskPerUnit);
        capacity = Math.min(capacity, globalCap);
        remainingRiskPool = Math.max(0, remainingRiskPool - capacity * risk.riskPerUnit);
      }
      let target, action, delta;
      const policyExit = (strategy.seller && (market.backwardation || market.high)) || (!strategy.baseline && !item.enabled);
      if (market.blocked) {
        target = current; action = "BLOCKED"; delta = 0;
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
      if (strategy.kind === "coveredCall" && target > Math.floor(currentQqq / 100)) {
        target = Math.floor(currentQqq / 100);
        delta = target - current;
        action = delta < 0 ? "REDUCE" : delta > 0 ? "ADD" : "HOLD";
      }
      if (strategy.kind === "stressOnly" && item.status !== "OFF" && item.status !== "NOT_ENABLED" && item.status !== "PENDING") {
        item.status = "STRESS_ONLY";
        item.reason = "Target is based on a user-entered stress-loss estimate only; ratio tails are NOT hard-capped.";
      }
      results.push({
        key: strategy.key, id: strategy.id, label: strategy.label, family: strategy.family,
        current, capacity: capacity === null ? null : Math.max(0, capacity),
        target, delta, action,
        status: item.status,
        riskBudgetUsd: nav * budgetPct / 100,
        riskPerUnit: risk.riskPerUnit,
        riskSource: risk.source,
        candidateSource: item.candidate?.source || null,
        reason: sellerBlocked && !policyExit ? "No new seller entries in this market state; over-cap trimming remains allowed." : item.reason,
        maxLossIsHardCap: strategy.kind !== "stressOnly",
        strategyKind: strategy.kind
      });
    }

    return {
      ok: true,
      market, nav, cashPool, totalOptionRiskPool,
      optionRiskReservedAtTargets: results.filter(r => r.riskPerUnit && r.target > 0 && r.strategyKind !== "coveredCall").reduce((sum, r) => sum + r.riskPerUnit * r.target, 0),
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
    const nShort = Math.max(1, whole(d.nShort, 10) || 10);
    const farDelta = Math.abs(num(d.farDelta, 0.08));
    const nearDelta = Math.max(0.01, Math.abs(num(d.nearDelta, 0.5)));
    const coverage = Math.max(0, num(d.coverageMult, 1.5));
    const maxStack = Math.max(1, whole(d.maxStack, 5) || 5);
    const proposedNear = Math.max(1, Math.min(maxStack, Math.ceil((coverage * nShort * farDelta) / nearDelta)));
    const targetFar = !enabled ? 0 : nShort;
    const targetNear = !enabled ? 0 : proposedNear;
    if (market.blocked) return { enabled, currentFar, currentNear, targetFar: currentFar, targetNear: currentNear, farDelta: targetFar-currentFar, nearDelta: targetNear-currentNear, actionFar: "BLOCKED", actionNear: "BLOCKED", noHardLossCap: true, status: "BLOCKED" };
    if (market.riskOff) return { enabled, currentFar, currentNear, targetFar: 0, targetNear: 0, farDelta: -currentFar, nearDelta: -currentNear, actionFar: currentFar ? "REDUCE" : "HOLD", actionNear: currentNear ? "REDUCE" : "HOLD", noHardLossCap: true, status: "RISK_OFF_EXIT_REVIEW" };
    if (!enabled) return { enabled, currentFar, currentNear, targetFar: 0, targetNear: 0, farDelta: -currentFar, nearDelta: -currentNear, actionFar: currentFar ? "REDUCE" : "HOLD", actionNear: currentNear ? "REDUCE" : "HOLD", noHardLossCap: true, status: "DISABLED_MANUAL_REVIEW" };
    const nearAction = actionFor(currentNear, targetNear, market.allowNew);
    const farAction = actionFor(currentFar, targetFar, market.allowNew);
    return { enabled, nShort, currentFar, currentNear, targetFar, targetNear, farDelta: farAction.delta, nearDelta: nearAction.delta, actionFar: farAction.action, actionNear: nearAction.action, noHardLossCap: true, status: "LEGACY_N_X_NO_HARD_LOSS_CAP", note: "Per campaign only. The 10:near-long rule is a legacy management profile, not a portfolio-wide capacity or max-loss guarantee." };
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
    return {
      right, expiry: short.expiry, dte: short.dte,
      shortStrike: short.strike, longStrike: wing.strike,
      shortDelta: short.delta, deltaSource: short.deltaSource,
      shortBid: short.bid, longAsk: wing.ask, credit, width,
      maxLossPerSpread: (width-credit)*100,
      source: "YAHOO_OPTION_CHAIN_DELAYED_OR_ESTIMATED",
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

  const Engine = { REFERENCE_PROFILE, OPTION_STRATEGIES, num, termSlope, assessMarket, candidateRisk, calculatePortfolio, calculateRatioCampaign, findCreditVertical, findLongOption };
  root.HybridOperatorEngineV1 = Engine;
  if (typeof module !== "undefined" && module.exports) module.exports = Engine;
})(typeof globalThis !== "undefined" ? globalThis : this);
