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
    let reservation = 0;
    let riskReservationReady = primarySizingReady;
    const riskReservationRows = [];
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
        riskReservationRows.push({ key, status: "CURRENT_OR_TARGET_UNKNOWN", current, target, riskPerUnit: finite(row.riskPerUnit), reservedUsd: null });
        continue;
      }
      const quantity = Math.max(current, target);
      const riskPerUnit = finite(row.riskPerUnit);
      if (quantity > 0 && (riskPerUnit === null || riskPerUnit < 0)) {
        riskReservationReady = false;
        riskReservationRows.push({ key, status: "RISK_PER_UNIT_UNKNOWN", current, target, quantity, riskPerUnit, reservedUsd: null });
        continue;
      }
      const reservedUsd = quantity * (quantity === 0 ? 0 : riskPerUnit);
      reservation += reservedUsd;
      riskReservationRows.push({ key, status: "ESTIMATED", current, target, quantity, riskPerUnit, reservedUsd });
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
      riskReservationBasis: "MAX_CURRENT_OR_TARGET_QTY_X_CURRENT_CANDIDATE_MAX_LOSS; ESTIMATE_NOT_CONFIRMED_FILL",
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
