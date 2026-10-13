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
      multiplier: numberOrNull(x.multiplier) ?? (TEMPLATES[template]?.kind === "STOCK" ? 1 : null),
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
      if (x.multiplier === null || x.multiplier <= 0 || !Number.isFinite(x.multiplier)) errors.push("Option multiplier must be explicitly entered and greater than zero.");
      if (x.shortStrike !== null && x.shortStrike <= 0) errors.push("Short strike must be positive.");
      if (x.longStrike !== null && x.longStrike <= 0) errors.push("Protective-wing strike must be positive.");
      if (x.shortStrike !== null && x.longStrike !== null && x.shortStrike >= x.longStrike) errors.push("For supported call-credit verticals, short strike must be below the protective-wing strike.");
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

  function parseOccOptionSymbol(value) {
    const symbol = String(value || "").toUpperCase().replace(/\s+/g, "");
    const match = symbol.match(/^([A-Z0-9.]{1,6})(\d{6})([CP])(\d{8})$/);
    if (!match) return null;
    const expiryDigits = match[2];
    const expiry = "20" + expiryDigits.slice(0, 2) + "-" + expiryDigits.slice(2, 4) + "-" + expiryDigits.slice(4, 6);
    if (!validDate(expiry)) return null;
    return {
      symbol,
      root: match[1],
      expiry,
      right: match[3],
      strike: Number(match[4]) / 1000
    };
  }

  function optionSymbolMatches(value, expectedRoot, expiry, strike) {
    const parsed = parseOccOptionSymbol(value);
    if (!parsed || !expectedRoot || !validDate(expiry) || strike === null || strike === undefined) return false;
    return parsed.root.startsWith(expectedRoot) &&
      parsed.expiry === expiry &&
      parsed.right === "C" &&
      Math.abs(parsed.strike - Number(strike)) < 0.000001;
  }

  function isAdjustedVxxSymbol(value) {
    const symbol = String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    return /^(?:VXX[12]|1VXX[12])\d{6}[CP]\d{8}$/.test(symbol);
  }

  function hasExplicitTimezone(value) {
    const stamp = typeof value === "string" ? value.trim() : "";
    return /(?:Z|[+-][0-9]{2}:[0-9]{2})$/i.test(stamp);
  }

  function markFreshness(row, nowMs) {
    if (!row.markPriceIsKnown) return { label: "NO MARK", stale: true, ageMinutes: null };
    if (typeof row.markAsOf !== "string" || !row.markAsOf.trim()) {
      return { label: "AS-OF MISSING", stale: true, ageMinutes: null };
    }
    if (!Number.isFinite(row.markAsOfMs)) return { label: "AS-OF INVALID", stale: true, ageMinutes: null };
    if (!hasExplicitTimezone(row.markAsOf)) return { label: "AS-OF TIMEZONE UNKNOWN", stale: true, ageMinutes: null };
    const ageMinutes = (nowMs - row.markAsOfMs) / 60000;
    if (ageMinutes < 0) return { label: "FUTURE TIMESTAMP", stale: true, ageMinutes };
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
      const entryEvidenceTypeDeclared = record.entryEvidence === "BROKER_FILL" || record.entryEvidence === "BROKER_STATEMENT";
      const entryEvidenceDeclared = entryEvidenceTypeDeclared && Boolean(record.entrySourceNote.trim());
      const markKnown = markPrice !== null && Number.isFinite(markPrice);
      let pnl = null, pnlStatus = "P&L INCOMPLETE";
      if (entryKnown && markKnown && template.kind === "STOCK") {
        pnl = template.side === "SHORT"
          ? (record.entryPrice - markPrice) * record.qty
          : (markPrice - record.entryPrice) * record.qty;
      } else if (entryKnown && markKnown && option && record.multiplier > 0) {
        pnl = (record.entryPrice - markPrice) * record.qty * record.multiplier;
      }

      const markForFreshness = {
        markPriceIsKnown: markKnown,
        markAsOf,
        markAsOfMs: markAsOf ? Date.parse(markAsOf) : null,
        markSourceType
      };
      const freshness = markFreshness(markForFreshness, nowMs);
      const shortContract = option ? parseOccOptionSymbol(record.shortSymbol) : null;
      const longContract = option ? parseOccOptionSymbol(record.longSymbol) : null;
      const shortIdentityMatches = option && optionSymbolMatches(record.shortSymbol, template.symbol, record.expiry, record.shortStrike);
      const longIdentityMatches = option && optionSymbolMatches(record.longSymbol, template.symbol, record.expiry, record.longStrike);
      const identityComplete = !option || (
        validDate(record.expiry) && record.shortStrike !== null && record.longStrike !== null &&
        record.shortStrike > 0 && record.longStrike > record.shortStrike &&
        shortIdentityMatches && longIdentityMatches &&
        Boolean(record.shortSymbol) && Boolean(record.longSymbol)
      );
      const adjustedDetected = option && (
        (shortContract && shortContract.root !== template.symbol) ||
        (longContract && longContract.root !== template.symbol) ||
        (template.symbol === "VXX" && (isAdjustedVxxSymbol(record.shortSymbol) || isAdjustedVxxSymbol(record.longSymbol)))
      );
      // Adjusted VXX roots can be recorded for audit and premium P&L attribution only.
      // Until the non-standard exercise payoff is implemented, notes/attestation cannot enable sizing.
      const termsComplete = !option || (
        !adjustedDetected && identityComplete && record.termsVerified && record.multiplier > 0
      );
      if (option && !termsComplete) blockedKeys.add(template.strategyKey);

      // "Metadata-complete" means the operator-entered source declarations, required contract fields,
      // and mark freshness pass internal checks. The app does not fetch or authenticate referenced documents.
      if (pnl !== null) {
        const confidenceIssues = [];
        if (!entryEvidenceDeclared) confidenceIssues.push("ENTRY UNVERIFIED");
        if (markSourceType === "UNKNOWN" || markSourceType === "MODEL_ESTIMATE" || !markSourceNote.trim()) {
          confidenceIssues.push("MARK SOURCE UNVERIFIED");
        }
        if (freshness.label === "AS-OF TIMEZONE UNKNOWN") {
          confidenceIssues.push("MARK TIMEZONE UNKNOWN");
        } else if (freshness.stale && freshness.label !== "NO MARK") {
          confidenceIssues.push("MARK STALE/INVALID");
        } else if (freshness.label === "NO MARK") {
          confidenceIssues.push("MARK MISSING");
        }
        if (option && !identityComplete) confidenceIssues.push("CONTRACT IDENTITY UNVERIFIED");
        if (option && adjustedDetected) confidenceIssues.push("ADJUSTED PAYOFF MODEL UNSUPPORTED");
        else if (option && !termsComplete) confidenceIssues.push("CONTRACT TERMS UNVERIFIED");
        pnlStatus = confidenceIssues.length
          ? "INDICATIVE · " + confidenceIssues.join(" / ")
          : option ? "GROSS UNREALIZED P&L · BEFORE FEES · METADATA COMPLETE" : "GROSS UNREALIZED P&L · METADATA COMPLETE";
      }

      let maxLossPerPackage = null;
      if (option && !adjustedDetected && width !== null && entryKnown && record.entryPrice > 0 && width > record.entryPrice && record.multiplier > 0) {
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
    const metadataCompletePnlRows = knownRows.filter(row => row.pnlStatus.startsWith("GROSS UNREALIZED P&L"));
    const indicativePnlRows = knownRows.filter(row => row.pnlStatus.startsWith("INDICATIVE"));
    const metadataCompletePnlSubtotal = metadataCompletePnlRows.reduce((sum, row) => sum + row.unrealizedPnl, 0);
    const indicativePnlSubtotal = indicativePnlRows.reduce((sum, row) => sum + row.unrealizedPnl, 0);
    const staleMarkCount = rows.filter(row => row.staleMark).length;
    // Separate missing/stale/unsupported mark status from source metadata gaps. These counters may overlap.
    const markSourceMetadataIncompleteCount = rows.filter(row =>
      row.markPriceIsKnown && (
        row.markSourceType === "UNKNOWN" ||
        row.markSourceType === "MODEL_ESTIMATE" ||
        !String(row.markSourceNote || "").trim()
      )
    ).length;
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
      metadataCompletePnlSubtotal,
      metadataCompletePnlRows: metadataCompletePnlRows.length,
      indicativePnlSubtotal,
      indicativePnlRows: indicativePnlRows.length,
      incompletePnlCount,
      staleMarkCount,
      markSourceMetadataIncompleteCount,
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

  const api = { SCHEMA, STORAGE_KEY, TEMPLATES, normalizeRecord, validateRecord, normalizeList, summarize, exportEnvelope, parseEnvelope, isAdjustedVxxSymbol, parseOccOptionSymbol, optionSymbolMatches };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.PositionLedgerV1 = api;
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this));
