(function (root) {
  "use strict";

  const SCHEMA = "QQQ_HYBRID_POSITION_REGISTER_V1";
  const STORAGE_KEY = "qqqHybridPositionRegisterV1";
  const TEMPLATES = {
    QQQ_CORE: { label: "QQQ core shares", kind: "STOCK", symbol: "QQQ", side: "LONG", unit: "shares", strategyKey: "qqqShares", multiplier: 1 },
    VXX_SHORT_STOCK: { label: "VXX short stock", kind: "STOCK", symbol: "VXX", side: "SHORT", unit: "shares", strategyKey: "vxxShortShares", multiplier: 1 },
    QQQ_CALL_CREDIT: { label: "QQQ far call-credit spread", kind: "CREDIT_VERTICAL", symbol: "QQQ", strategyKey: "qqqCallSpreads", unit: "spreads", multiplier: 100 },
    VXX_CALL_CREDIT: { label: "VXX call-credit spread", kind: "CREDIT_VERTICAL", symbol: "VXX", strategyKey: "vxxCallSpreads", unit: "spreads", multiplier: 100 }
  };
  const ENTRY_EVIDENCE = new Set(["BROKER_FILL", "BROKER_STATEMENT", "MANUAL_ESTIMATE", "UNKNOWN"]);
  const MARK_SOURCE = new Set(["BROKER_LIVE", "PUBLIC_DELAYED", "EOD_MARK", "MODEL_ESTIMATE", "UNKNOWN"]);

  function numberOrNull(value) {
    if (value === null || value === undefined || value === "") return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function validDate(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const parsed = new Date(value + "T00:00:00Z");
    return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
  }

  function idFor(index = 0) {
    return "position-" + Date.now().toString(36) + "-" + Number(index).toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }

  function normalizeRecord(raw, index = 0) {
    const x = raw && typeof raw === "object" ? raw : {};
    const template = TEMPLATES[x.template] ? x.template : "UNKNOWN_TEMPLATE";
    return {
      id: String(x.id || idFor(index)),
      template,
      qty: numberOrNull(x.qty),
      entryDate: String(x.entryDate || ""),
      entryPrice: numberOrNull(x.entryPrice),
      markPrice: numberOrNull(x.markPrice),
      markAsOf: String(x.markAsOf || ""),
      markSourceType: MARK_SOURCE.has(x.markSourceType) ? x.markSourceType : "UNKNOWN",
      markSourceNote: String(x.markSourceNote || "").slice(0, 500),
      entryEvidence: ENTRY_EVIDENCE.has(x.entryEvidence) ? x.entryEvidence : "UNKNOWN",
      entrySourceNote: String(x.entrySourceNote || "").slice(0, 500),
      expiry: String(x.expiry || ""),
      shortStrike: numberOrNull(x.shortStrike),
      longStrike: numberOrNull(x.longStrike),
      shortSymbol: String(x.shortSymbol || "").trim().slice(0, 100),
      longSymbol: String(x.longSymbol || "").trim().slice(0, 100),
      multiplier: numberOrNull(x.multiplier) ?? TEMPLATES[template]?.multiplier ?? 100,
      termsVerified: x.termsVerified === true,
      deliverableNote: String(x.deliverableNote || "").slice(0, 500),
      createdAt: String(x.createdAt || new Date().toISOString()),
      updatedAt: String(x.updatedAt || new Date().toISOString())
    };
  }

  function validateRecord(record) {
    const x = record && record.template ? normalizeRecord(record) : normalizeRecord(record || {});
    const errors = [];
    const t = TEMPLATES[x.template];
    if (!t) errors.push("Choose a supported position template.");
    if (!Number.isFinite(x.qty) || x.qty <= 0 || !Number.isInteger(x.qty)) errors.push("Quantity must be a positive whole number.");
    if (x.entryPrice !== null && (x.entryPrice < 0 || !Number.isFinite(x.entryPrice))) errors.push("Entry price must be blank or a non-negative number.");
    if (x.markPrice !== null && (x.markPrice < 0 || !Number.isFinite(x.markPrice))) errors.push("Current mark / close cost must be blank or a non-negative number.");
    if (t && t.kind === "STOCK" && x.entryPrice !== null && x.entryPrice <= 0) errors.push("A recorded stock entry price must be greater than zero.");
    if (t && t.kind === "STOCK" && x.markPrice !== null && x.markPrice <= 0) errors.push("A recorded stock mark must be greater than zero.");
    if (x.entryDate && !validDate(x.entryDate)) errors.push("Entry date must be a valid YYYY-MM-DD date.");
    if (x.expiry && !validDate(x.expiry)) errors.push("Option expiry must be a valid YYYY-MM-DD date.");
    if (t && t.kind === "CREDIT_VERTICAL") {
      if (x.multiplier <= 0 || !Number.isFinite(x.multiplier)) errors.push("Option multiplier must be greater than zero.");
      if (x.shortStrike !== null && x.shortStrike <= 0) errors.push("Short strike must be positive.");
      if (x.longStrike !== null && x.longStrike <= 0) errors.push("Protective-wing strike must be positive.");
      if (x.entryPrice !== null && x.entryPrice <= 0) errors.push("Entry net credit must be greater than zero.");
    }
    return { ok: errors.length === 0, errors, record: x };
  }

  function normalizeList(rawRows) {
    if (!Array.isArray(rawRows)) return { ok: false, errors: ["Position register must contain a positions array."], positions: [] };
    if (rawRows.length > 200) return { ok: false, errors: ["Position register is limited to 200 records per snapshot."], positions: [] };
    const normalized = rawRows.map((r, i) => normalizeRecord(r, i));
    const errors = [];
    normalized.forEach((r, i) => {
      const verdict = validateRecord(r);
      if (!verdict.ok) errors.push("Row " + (i + 1) + ": " + verdict.errors.join(" "));
    });
    const ids = new Set();
    normalized.forEach((r, i) => {
      if (ids.has(r.id)) errors.push("Duplicate record ID on row " + (i + 1) + ".");
      ids.add(r.id);
    });
    return { ok: errors.length === 0, errors, positions: errors.length ? [] : normalized };
  }

  function isAdjustedVxxSymbol(value) {
    const symbol = String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    return /^(?:VXX[12]|1VXX[12])\d{6}[CP]\d{8}$/.test(symbol);
  }

  function markFreshness(row, nowMs) {
    if (!row.markPriceIsKnown) return { label: "NO MARK", stale: true, ageMinutes: null };
    if (!row.markAsOfMs) return { label: "AS-OF MISSING", stale: true, ageMinutes: null };
    const ageMinutes = (nowMs - row.markAsOfMs) / 60000;
    if (ageMinutes < -5) return { label: "FUTURE TIMESTAMP", stale: true, ageMinutes };
    if (row.markSourceType === "BROKER_LIVE") {
      return { label: ageMinutes <= 15 ? "LIVE ≤15M" : "STALE LIVE", stale: ageMinutes > 15, ageMinutes };
    }
    if (row.markSourceType === "PUBLIC_DELAYED") {
      return { label: ageMinutes <= 72 * 60 ? "DELAYED ≤72H" : "OLD DELAYED", stale: ageMinutes > 72 * 60, ageMinutes };
    }
    if (row.markSourceType === "EOD_MARK") {
      return { label: ageMinutes <= 96 * 60 ? "EOD ≤96H" : "OLD EOD", stale: ageMinutes > 96 * 60, ageMinutes };
    }
    if (row.markSourceType === "MODEL_ESTIMATE") return { label: "MODEL ESTIMATE", stale: true, ageMinutes };
    return { label: "SOURCE UNKNOWN", stale: true, ageMinutes };
  }

  function summarize(positions, market = {}, nowMs = Date.now()) {
    const normalized = normalizeList(Array.isArray(positions) ? positions : []);
    const records = normalized.ok ? normalized.positions : [];
    const holdings = { qqqShares: 0, vxxShortShares: 0, qqqCallSpreads: 0, vxxCallSpreads: 0 };
    const blockedKeys = new Set();
    const rows = records.map((record, index) => {
      const template = TEMPLATES[record.template];
      const option = template.kind === "CREDIT_VERTICAL";
      const marketSpot = template.symbol === "QQQ" ? numberOrNull(market.qqq) : numberOrNull(market.vxx);
      let markPrice = record.markPrice;
      let markAsOf = record.markAsOf;
      let markSourceType = record.markSourceType;
      let markSourceNote = record.markSourceNote;
      let markDerivedFromSnapshot = false;
      if (markPrice === null && !option && marketSpot > 0) {
        markPrice = marketSpot;
        markAsOf = String(template.symbol === "QQQ" ? market.spot_asof || "" : market.spot_asof || "");
        markSourceType = "UNKNOWN";
        markSourceNote = "Derived from APP spot snapshot; source class not preserved in position register; not stored in the position record.";
        markDerivedFromSnapshot = true;
      }

      const width = option && record.shortStrike !== null && record.longStrike !== null
        ? Math.abs(record.shortStrike - record.longStrike) : null;
      const entryKnown = record.entryPrice !== null && Number.isFinite(record.entryPrice);
      const markKnown = markPrice !== null && Number.isFinite(markPrice);
      let pnl = null, pnlStatus = "P&L INCOMPLETE";
      if (entryKnown && markKnown && template.kind === "STOCK") {
        pnl = template.side === "SHORT"
          ? (record.entryPrice - markPrice) * record.qty
          : (markPrice - record.entryPrice) * record.qty;
        pnlStatus = record.entryEvidence === "UNKNOWN" || markSourceType === "UNKNOWN" || markSourceType === "MODEL_ESTIMATE"
          ? "INDICATIVE · SOURCE UNVERIFIED" : "GROSS UNREALIZED P&L";
      } else if (entryKnown && markKnown && option && record.multiplier > 0) {
        pnl = (record.entryPrice - markPrice) * record.qty * record.multiplier;
        pnlStatus = record.termsVerified && record.entryEvidence !== "UNKNOWN" &&
          markSourceType !== "UNKNOWN" && markSourceType !== "MODEL_ESTIMATE"
          ? "GROSS UNREALIZED P&L · BEFORE FEES" : "INDICATIVE · TERMS/SOURCE UNVERIFIED";
      }

      const markForFreshness = {
        markPriceIsKnown: markKnown,
        markAsOfMs: markAsOf ? Date.parse(markAsOf) : null,
        markSourceType
      };
      const freshness = markFreshness(markForFreshness, nowMs);
      const identityComplete = !option || (
        validDate(record.expiry) && record.shortStrike !== null && record.longStrike !== null &&
        record.shortStrike > 0 && record.longStrike > 0 && record.shortStrike !== record.longStrike &&
        Boolean(record.shortSymbol) && Boolean(record.longSymbol)
      );
      const adjustedDetected = template.symbol === "VXX" &&
        (isAdjustedVxxSymbol(record.shortSymbol) || isAdjustedVxxSymbol(record.longSymbol));
      // An adjusted VXX root needs an explicit deliverable note as well as the
      // operator's broker-verification check before it can count toward sizing.
      const termsComplete = !option || (
        identityComplete && record.termsVerified && record.multiplier > 0 &&
        (!adjustedDetected || Boolean(record.deliverableNote.trim()))
      );
      if (option && !termsComplete) blockedKeys.add(template.strategyKey);

      let maxLossPerPackage = null;
      if (option && width !== null && entryKnown && record.entryPrice > 0 && width > record.entryPrice && record.multiplier > 0) {
        maxLossPerPackage = (width - record.entryPrice) * record.multiplier;
      }
      return {
        ...record, index, label: template.label, kind: template.kind, symbol: template.symbol, side: template.side || "CREDIT",
        unit: template.unit, strategyKey: template.strategyKey, markPrice,
        markAsOf, markSourceType, markSourceNote, markDerivedFromSnapshot,
        entryKnown, markPriceIsKnown: markKnown, width, unrealizedPnl: pnl, pnlStatus,
        pnlComplete: pnl !== null, markFreshness: freshness.label, staleMark: freshness.stale,
        identityComplete, termsComplete, adjustedDetected, maxLossPerPackage
      };
    });

    for (const row of rows) {
      if (row.strategyKey in holdings) holdings[row.strategyKey] += row.qty;
    }
    const knownRows = rows.filter(row => row.pnlComplete);
    const knownPnlSubtotal = knownRows.reduce((sum, row) => sum + row.unrealizedPnl, 0);
    const staleMarkCount = rows.filter(row => row.staleMark).length;
    const incompletePnlCount = rows.filter(row => !row.pnlComplete).length;
    const termBlockedCount = rows.filter(row => row.kind === "CREDIT_VERTICAL" && !row.termsComplete).length;
    return {
      schema: SCHEMA,
      storageKey: STORAGE_KEY,
      count: rows.length,
      holdings,
      rows,
      blockingKeys: [...blockedKeys],
      knownPnlSubtotal,
      knownPnlRows: knownRows.length,
      incompletePnlCount,
      staleMarkCount,
      termBlockedCount,
      error: normalized.ok ? null : normalized.errors.join(" "),
      importErrors: normalized.errors,
      timezone: (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || "UNKNOWN"; } catch (_) { return "UNKNOWN"; } })(),
      note: "Gross unrealized mark-to-entry estimate only. Excludes commissions, slippage, dividends, borrow costs, assignment/exercise, taxes and cash-flow timing."
    };
  }

  function exportEnvelope(positions, exportedAt = new Date().toISOString()) {
    return { schema: SCHEMA, exportedAt, timezone: (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || "UNKNOWN"; } catch (_) { return "UNKNOWN"; } })(), positions: normalizeList(positions).positions };
  }

  function parseEnvelope(raw) {
    let data;
    try { data = typeof raw === "string" ? JSON.parse(raw) : raw; }
    catch (_) { return { ok: false, errors: ["File is not valid JSON."], positions: [] }; }
    if (!data || data.schema !== SCHEMA || !Array.isArray(data.positions)) {
      return { ok: false, errors: ["The file is not a QQQ Hybrid Position Register V1 export."], positions: [] };
    }
    return normalizeList(data.positions);
  }

  const api = { SCHEMA, STORAGE_KEY, TEMPLATES, normalizeRecord, validateRecord, normalizeList, summarize, exportEnvelope, parseEnvelope, isAdjustedVxxSymbol };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.PositionLedgerV1 = api;
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this));
