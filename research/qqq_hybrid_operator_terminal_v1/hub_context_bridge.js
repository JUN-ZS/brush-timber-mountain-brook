(function (root) {
  "use strict";
  const SCHEMA = "QQQ_HYBRID_PRIMARY_CONTEXT_V1";
  const STORAGE_KEY = SCHEMA;
  const MAX_AGE_MS = 24 * 60 * 60 * 1000;
  const PRIMARY_OPTION_KEYS = ["qqqCallSpreads", "vxxCallSpreads"];
  function finite(value) {
    if (value === null || value === undefined || value === "") return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  function hasTimezone(value) {
    return typeof value === "string" && /(?:Z|[+-][0-9]{2}:[0-9]{2})$/i.test(value.trim());
  }
  function contextFromPrimaryPlan(plan, generatedAt) {
    const input = plan && plan.input || {};
    const result = plan && plan.result || {};
    const marketInput = input.market || {};
    const marketResult = result.market || {};
    const sizing = input.sizing || {};
    const primarySizingReady = result.ok === true && marketResult.blocked !== true;
    const rows = Array.isArray(result.rows) ? result.rows : [];
    const positionRegister = input.positionRegister || {};
    const registerRows = positionRegister.summary && Array.isArray(positionRegister.summary.rows)
      ? positionRegister.summary.rows : [];
    const registerUsable = positionRegister.useForSizing === true &&
      positionRegister.completeConfirmed === true;
    const recordedPositions = Array.isArray(positionRegister.records) ? positionRegister.records : [];
    const recordedOptionPositions = recordedPositions.filter(item => item &&
      (item.template === "QQQ_CALL_CREDIT" || item.template === "VXX_CALL_CREDIT") && finite(item.qty) > 0);
    let reservation = 0;
    let riskReservationReady = primarySizingReady;
    const riskReservationRows = [];
    if (recordedOptionPositions.length > 0 && !registerUsable) riskReservationReady = false;
    for (const key of PRIMARY_OPTION_KEYS) {
      const row = rows.find(item => item && item.key === key);
      if (!row) {
        riskReservationReady = false;
        riskReservationRows.push({ key, status: "MISSING_PRIMARY_ROW", current: null, target: null, riskPerUnit: null, reservedUsd: null });
        continue;
      }
      const current = finite(row.current);
      const target = finite(row.target);
      if (current === null || target === null || current < 0 || target < 0) {
        riskReservationReady = false;
        riskReservationRows.push({ key, status: "CURRENT_OR_TARGET_UNKNOWN", current, target, riskPerUnit: finite(row.riskPerUnit), heldRiskUsd: null, targetAddRiskUsd: null, reservedUsd: null });
        continue;
      }
      let heldRiskUsd = 0;
      if (current > 0) {
        if (!registerUsable) {
          riskReservationReady = false;
          riskReservationRows.push({ key, status: "HELD_RISK_REQUIRES_CONFIRMED_POSITION_REGISTER", current, target, riskPerUnit: finite(row.riskPerUnit), heldRiskUsd: null, targetAddRiskUsd: null, reservedUsd: null });
          continue;
        }
        const heldRows = registerRows.filter(item => item && item.strategyKey === key && finite(item.qty) > 0);
        const registeredQty = heldRows.reduce((sum, item) => sum + finite(item.qty), 0);
        if (Math.abs(registeredQty - current) > 1e-9 || heldRows.some(item =>
          item.termsComplete !== true ||
          item.identityComplete !== true ||
          item.adjustedDetected === true ||
          finite(item.maxLossPerPackage) === null ||
          finite(item.maxLossPerPackage) < 0
        )) {
          riskReservationReady = false;
          riskReservationRows.push({ key, status: "HELD_CONTRACT_RISK_INCOMPLETE", current, target, registeredQty, riskPerUnit: finite(row.riskPerUnit), heldRiskUsd: null, targetAddRiskUsd: null, reservedUsd: null });
          continue;
        }
        heldRiskUsd = heldRows.reduce((sum, item) => sum + finite(item.qty) * finite(item.maxLossPerPackage), 0);
      }
      const targetAddQty = Math.max(0, target - current);
      const riskPerUnit = finite(row.riskPerUnit);
      if (targetAddQty > 0 && (riskPerUnit === null || riskPerUnit < 0)) {
        riskReservationReady = false;
        riskReservationRows.push({ key, status: "TARGET_ADD_RISK_PER_UNIT_UNKNOWN", current, target, targetAddQty, riskPerUnit, heldRiskUsd, targetAddRiskUsd: null, reservedUsd: null });
        continue;
      }
      const targetAddRiskUsd = targetAddQty * (targetAddQty === 0 ? 0 : riskPerUnit);
      const reservedUsd = heldRiskUsd + targetAddRiskUsd;
      reservation += reservedUsd;
      riskReservationRows.push({
        key,
        status: current > 0 ? "HELD_REGISTER_PLUS_TARGET_ADDS" : "TARGET_ONLY_SCENARIO",
        current, target, targetAddQty, riskPerUnit, heldRiskUsd, targetAddRiskUsd, reservedUsd
      });
    }
    if (!riskReservationReady) reservation = null;
    const qqqSpot = finite(marketInput.qqq);
    return {
      schema: SCHEMA,
      generatedAt: generatedAt || plan && plan.generatedAt || new Date().toISOString(),
      source: "MAIN_OPERATOR_PREVIEW",
      capital: {
        nav: finite(input.nav),
        cashPool: finite(input.cashPool),
        cashReservePct: finite(sizing.cashReservePct),
        totalOptionRiskPct: finite(sizing.totalOptionRiskPct)
      },
      market: {
        qqqSpot: qqqSpot !== null && qqqSpot > 0 ? qqqSpot : null,
        spotAsOf: marketInput.spot_asof || null,
        termAsOf: marketInput.term_asof || null,
        status: String(marketResult.status || "UNKNOWN"),
        state: String(marketResult.state || "UNKNOWN"),
        termSource: String(marketInput.term_source || "UNKNOWN")
      },
      primarySizingReady,
      riskReservationReady,
      baseRiskReservedUsd: riskReservationReady ? reservation : null,
      riskReservationBasis: "CONFIRMED_REGISTER_HELD_MAX_LOSS_PLUS_INCREMENTAL_TARGET_QTY_X_CURRENT_CANDIDATE_MAX_LOSS",
      riskReservationRows,
      boundary: { brokerOrders: false, actualFillsAuthenticated: false, purpose: "Capital/risk context only; manual review required." }
    };
  }
  function validate(raw, nowMs, maxAgeMs) {
    let packet = raw;
    if (typeof packet === "string") {
      try { packet = JSON.parse(packet); }
      catch (_) { return { ok: false, error: "Saved primary context is not valid JSON." }; }
    }
    if (!packet || typeof packet !== "object" || packet.schema !== SCHEMA) return { ok: false, error: "No compatible primary capital-context snapshot was found." };
    if (!hasTimezone(packet.generatedAt) || !Number.isFinite(Date.parse(packet.generatedAt))) return { ok: false, error: "Primary context timestamp is invalid or has no explicit timezone." };
    const now = Number.isFinite(nowMs) ? nowMs : Date.now();
    const age = now - Date.parse(packet.generatedAt);
    const maxAge = Number.isFinite(maxAgeMs) && maxAgeMs > 0 ? maxAgeMs : MAX_AGE_MS;
    if (age < -5 * 60 * 1000) return { ok: false, error: "Primary context timestamp is in the future; re-sync from the main desk." };
    if (age > maxAge) return { ok: false, error: "Primary context is over 24 hours old; re-sync from the main desk before using it." };
    const capital = packet.capital || {};
    const nav = finite(capital.nav);
    const cashPool = finite(capital.cashPool);
    const cashReservePct = finite(capital.cashReservePct);
    const totalOptionRiskPct = finite(capital.totalOptionRiskPct);
    if (!(nav > 0)) return { ok: false, error: "Primary context NAV must be positive." };
    if (cashPool === null || cashPool < 0) return { ok: false, error: "Primary context uncommitted cash must be zero or positive." };
    if (cashReservePct === null || cashReservePct < 0 || cashReservePct > 100) return { ok: false, error: "Primary context cash reserve percentage must be between 0 and 100." };
    if (totalOptionRiskPct === null || totalOptionRiskPct < 0 || totalOptionRiskPct > 100) return { ok: false, error: "Primary context option-risk pool percentage must be between 0 and 100." };
    const market = packet.market || {};
    const spot = finite(market.qqqSpot);
    if (spot !== null && !(spot > 0)) return { ok: false, error: "Primary context QQQ spot is invalid." };
    const primarySizingReady = packet.primarySizingReady === true;
    const riskReservationReady = packet.riskReservationReady === true;
    const reserved = finite(packet.baseRiskReservedUsd);
    if (riskReservationReady && (!primarySizingReady || reserved === null || reserved < 0)) return { ok: false, error: "Primary context risk-reservation readiness does not match its data." };
    if (!riskReservationReady && packet.baseRiskReservedUsd !== null) return { ok: false, error: "Unknown risk reservation must remain null, not zero." };
    if (!Array.isArray(packet.riskReservationRows)) return { ok: false, error: "Primary context is missing the risk-reservation audit rows." };
    return {
      ok: true,
      context: {
        schema: SCHEMA, generatedAt: packet.generatedAt,
        capital: { nav, cashPool, cashReservePct, totalOptionRiskPct },
        market: {
          qqqSpot: spot,
          spotAsOf: market.spotAsOf == null ? null : String(market.spotAsOf),
          termAsOf: market.termAsOf == null ? null : String(market.termAsOf),
          status: String(market.status || "UNKNOWN"),
          state: String(market.state || "UNKNOWN"),
          termSource: String(market.termSource || "UNKNOWN")
        },
        primarySizingReady, riskReservationReady,
        baseRiskReservedUsd: riskReservationReady ? reserved : null,
        riskReservationBasis: String(packet.riskReservationBasis || "UNKNOWN"),
        riskReservationRows: packet.riskReservationRows
      },
      ageMs: Math.max(0, age)
    };
  }
  const API = { SCHEMA, STORAGE_KEY, MAX_AGE_MS, contextFromPrimaryPlan, validate };
  root.HubContextBridgeV1 = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
