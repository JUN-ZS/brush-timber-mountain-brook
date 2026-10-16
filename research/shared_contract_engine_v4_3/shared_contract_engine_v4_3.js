const SharedContractEngineV43 = (function (factory) {
  "use strict";
  return factory();
})(function () {
  "use strict";
  const SOURCE_SCHEMA = "qqq-hybrid.verified-source-store.v1";
  const STATE_SCHEMA = "qqq-hybrid.shared-contract.v4.3";
  const QUOTE_SCHEMA = "qqq-historical-option-chain.v1";
  const DECIMAL = /^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$/;
  const ISO_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;
  const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;
  const OCC = /^([A-Z0-9.]{1,6})(\d{6})([CP])(\d{8})$/;

  function fail(code, message) {
    const error = new Error(code + ": " + message);
    error.code = code;
    throw error;
  }
  function parseStrictNumber(value) {
    if (value === null || value === undefined) return { state: "EMPTY", value: null };
    if (typeof value === "string") {
      const raw = value.trim();
      if (!raw) return { state: "EMPTY", value: null };
      if (!DECIMAL.test(raw)) return { state: "INVALID", value: null };
      const parsed = Number(raw);
      return Number.isFinite(parsed) ? { state: "VALID", value: parsed } : { state: "INVALID", value: null };
    }
    if (typeof value === "number" && Number.isFinite(value)) return { state: "VALID", value };
    return { state: "INVALID", value: null };
  }
  function strictNumber(value, label, options) {
    const parsed = parseStrictNumber(value);
    if (parsed.state !== "VALID") fail(parsed.state === "EMPTY" ? "MISSING_REQUIRED_VALUE" : "INVALID_NUMBER", label + " must be an explicit finite decimal number.");
    if (options && options.min !== undefined && parsed.value < options.min) fail("OUT_OF_RANGE", label + " must be >= " + options.min + ".");
    if (options && options.max !== undefined && parsed.value > options.max) fail("OUT_OF_RANGE", label + " must be <= " + options.max + ".");
    if (options && options.integer && !Number.isInteger(parsed.value)) fail("INVALID_INTEGER", label + " must be an integer.");
    return parsed.value;
  }
  function optionalNumber(value) {
    const parsed = parseStrictNumber(value);
    return parsed.state === "VALID" ? parsed.value : null;
  }
  function validDate(value) {
    if (typeof value !== "string" || !DATE_ONLY.test(value)) return false;
    const date = new Date(value + "T00:00:00Z");
    return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
  }
  function validInstant(value) {
    return typeof value === "string" && ISO_INSTANT.test(value) && Number.isFinite(Date.parse(value));
  }
  function textValue(value) { return typeof value === "string" ? value.trim() : ""; }

  function canonicalize(value, seen) {
    if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
    if (typeof value === "number") {
      if (!Number.isFinite(value)) fail("NON_CANONICAL_VALUE", "Non-finite numbers cannot be hashed.");
      return JSON.stringify(value);
    }
    if (typeof value === "undefined" || typeof value === "function" || typeof value === "symbol" || typeof value === "bigint") {
      fail("NON_CANONICAL_VALUE", "Undefined, functions, symbols and bigints cannot be hashed.");
    }
    const visited = seen || new Set();
    if (visited.has(value)) fail("NON_CANONICAL_VALUE", "Circular data cannot be hashed.");
    visited.add(value);
    let result;
    if (Array.isArray(value)) {
      result = "[" + value.map(item => canonicalize(item, visited)).join(",") + "]";
    } else {
      const keys = Object.keys(value).sort();
      result = "{" + keys.map(key => JSON.stringify(key) + ":" + canonicalize(value[key], visited)).join(",") + "}";
    }
    visited.delete(value);
    return result;
  }
  async function sha256Hex(value) {
    const text = typeof value === "string" ? value : canonicalize(value);
    if (typeof require === "function") {
      try { return require("node:crypto").createHash("sha256").update(text, "utf8").digest("hex"); }
      catch (_) { /* Web Crypto fallback. */ }
    }
    const cryptoApi = typeof globalThis !== "undefined" ? globalThis.crypto : null;
    if (!cryptoApi || !cryptoApi.subtle || typeof TextEncoder === "undefined") fail("HASH_API_UNAVAILABLE", "SHA-256 requires Node crypto or Web Crypto.");
    const digest = await cryptoApi.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(digest)).map(byte => byte.toString(16).padStart(2, "0")).join("");
  }

  function parseCSV(text) {
    if (typeof text !== "string" || !text.trim()) fail("EMPTY_IMPORT", "CSV file is empty.");
    const input = text.charCodeAt(0) === 0xFEFF ? text.slice(1) : text;
    const rows = [];
    let row = [], cell = "", quoted = false;
    for (let i = 0; i < input.length; i += 1) {
      const ch = input[i];
      if (quoted) {
        if (ch === '"') {
          if (input[i + 1] === '"') { cell += '"'; i += 1; }
          else quoted = false;
        } else cell += ch;
      } else if (ch === '"' && cell.length === 0) quoted = true;
      else if (ch === ",") { row.push(cell); cell = ""; }
      else if (ch === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; }
      else if (ch !== "\r") cell += ch;
    }
    if (quoted) fail("INVALID_CSV", "CSV contains an unterminated quoted field.");
    if (cell.length || row.length) { row.push(cell); rows.push(row); }
    while (rows.length && rows[rows.length - 1].every(value => String(value).trim() === "")) rows.pop();
    if (rows.length < 2) fail("INVALID_CSV", "CSV needs a header and at least one data row.");
    const headers = rows.shift().map(value => String(value).trim());
    if (headers.some(value => !value)) fail("INVALID_CSV", "CSV header contains a blank column name.");
    if (new Set(headers).size !== headers.length) fail("INVALID_CSV", "CSV header contains duplicate column names.");
    return rows.map((values, index) => {
      if (values.length !== headers.length) fail("INVALID_CSV", "Row " + (index + 2) + " has " + values.length + " values; expected " + headers.length + ".");
      const out = {};
      headers.forEach((header, column) => { out[header] = values[column]; });
      out.__rowNumber = index + 2;
      return out;
    });
  }
  function parseOcc(contractId) {
    const symbol = textValue(contractId).toUpperCase().replace(/\s+/g, "");
    const match = symbol.match(OCC);
    if (!match) return null;
    const expiry = "20" + match[2].slice(0, 2) + "-" + match[2].slice(2, 4) + "-" + match[2].slice(4, 6);
    if (!validDate(expiry)) return null;
    return { symbol, root: match[1], expiry, right: match[3], strike: Number(match[4]) / 1000 };
  }

  function normalizeQuote(raw, sourceId, rawFileHash) {
    const contractId = textValue(raw.contractId || raw.symbol);
    if (!contractId) fail("INVALID_QUOTE", "contractId is required.");
    const sid = textValue(raw.sourceId || sourceId);
    if (!sid) fail("INVALID_QUOTE", "sourceId is required.");
    const underlying = textValue(raw.underlying).toUpperCase();
    if (!["QQQ", "VXX"].includes(underlying)) fail("INVALID_QUOTE", "underlying must be QQQ or VXX.");
    const expiry = textValue(raw.expiry);
    if (!validDate(expiry)) fail("INVALID_QUOTE", "expiry must be a valid YYYY-MM-DD date.");
    const right = textValue(raw.right).toUpperCase();
    if (!["C", "P"].includes(right)) fail("INVALID_QUOTE", "right must be C or P.");
    const strike = strictNumber(raw.strike, "strike", { min: 0.000001 });
    const asOf = textValue(raw.asOf);
    if (!validInstant(asOf)) fail("INVALID_QUOTE", "asOf must be an ISO-8601 timestamp with an explicit timezone.");
    const bid = strictNumber(raw.bid, "bid", { min: 0 });
    const ask = strictNumber(raw.ask, "ask", { min: 0 });
    if (ask < bid) fail("INVALID_QUOTE", "ask must be >= bid; crossed markets are rejected.");
    const bidSize = strictNumber(raw.bidSize, "bidSize", { min: 0, integer: true });
    const askSize = strictNumber(raw.askSize, "askSize", { min: 0, integer: true });
    const multiplier = strictNumber(raw.multiplier, "multiplier", { min: 1, integer: true });
    const sourceFileHash = String(rawFileHash || raw.sourceFileHash || "").toLowerCase();
    if (!/^[a-f0-9]{64}$/.test(sourceFileHash)) fail("INVALID_QUOTE", "Quote must retain a SHA-256 hash of its imported raw file.");
    const occ = parseOcc(contractId);
    let contractIdentityState = "UNVERIFIED_CONTRACT_ID", adjustedContract = false;
    if (occ) {
      if (occ.expiry !== expiry || occ.right !== right || Math.abs(occ.strike - strike) > 0.000001) {
        fail("CONTRACT_IDENTITY_MISMATCH", "OCC terms conflict with expiry/right/strike for " + contractId + ".");
      }
      if (underlying === "QQQ" && occ.root !== "QQQ") fail("CONTRACT_IDENTITY_MISMATCH", "QQQ symbol root is not QQQ.");
      if (underlying === "VXX" && !occ.root.startsWith("VXX")) fail("CONTRACT_IDENTITY_MISMATCH", "VXX symbol root does not start with VXX.");
      adjustedContract = underlying === "VXX" && occ.root !== "VXX";
      contractIdentityState = adjustedContract ? "ADJUSTED_DELIVERABLE_UNSUPPORTED" : "OCC_TERMS_MATCH";
    }
    return {
      sourceId: sid, sourceFileHash, contractId, underlying, expiry, right, strike, asOf, bid, ask, bidSize, askSize, multiplier,
      contractIdentityState, adjustedContract, evidenceClass: "OBSERVED_UPLOAD_VALUES",
      sourceAuthentication: "UNAUTHENTICATED_UPLOAD"
    };
  }

  function normalizeEpisode(raw) {
    const episodeId = textValue(raw.episodeId);
    const longContractId = textValue(raw.longContractId);
    const shortContractId = textValue(raw.shortContractId);
    const nShort = strictNumber(raw.nShort, "nShort", { min: 1, integer: true });
    const entryAsOf = textValue(raw.entryAsOf), exitAsOf = textValue(raw.exitAsOf);
    if (!episodeId || !longContractId || !shortContractId) fail("INVALID_EPISODE", "episodeId and both contract IDs are required.");
    if (longContractId === shortContractId) fail("INVALID_EPISODE", "Long and short contract IDs must differ.");
    if (!validInstant(entryAsOf) || !validInstant(exitAsOf)) fail("INVALID_EPISODE", "Entry and exit timestamps must include a timezone.");
    if (Date.parse(exitAsOf) <= Date.parse(entryAsOf)) fail("INVALID_EPISODE", "Exit timestamp must be later than entry timestamp.");
    return { episodeId, longContractId, shortContractId, nShort, entryAsOf, exitAsOf, evidenceClass: "USER_DEFINED_EPISODE_SPEC" };
  }

  function normalizeMarketRow(raw, sourceId, rawFileHash) {
    const sid = textValue(raw.sourceId || sourceId);
    if (!sid) fail("INVALID_MARKET_ROW", "sourceId is required.");
    const symbol = textValue(raw.symbol).toUpperCase();
    if (!["QQQ", "VXX", "VIX", "VXN"].includes(symbol)) fail("INVALID_MARKET_ROW", "Unsupported symbol.");
    const date = textValue(raw.date);
    if (!validDate(date)) fail("INVALID_MARKET_ROW", "date must be YYYY-MM-DD.");
    const close = strictNumber(raw.close, "close", { min: 0.000001 });
    const adjustmentBasis = textValue(raw.adjustmentBasis).toUpperCase();
    if (!["RAW", "ADJUSTED", "INDEX_LEVEL"].includes(adjustmentBasis)) fail("INVALID_MARKET_ROW", "adjustmentBasis must be explicit.");
    const sourceFileHash = String(rawFileHash || raw.sourceFileHash || "").toLowerCase();
    if (!/^[a-f0-9]{64}$/.test(sourceFileHash)) fail("INVALID_MARKET_ROW", "Price row must retain a raw-file SHA-256.");
    return { sourceId: sid, sourceFileHash, symbol, date, close, adjustmentBasis, evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD" };
  }

  function createEmptySourceStore() {
    return {
      schema: SOURCE_SCHEMA,
      status: "REPO_SUMMARY_REFERENCE_ONLY (UNVERIFIED_RAW_CHAIN)",
      sources: [], quotes: [], marketRows: [], episodes: [],
      coverageExpectation: { expectedTradingDates: [] },
      evidenceNote: "No raw quote chain or underlying history is included. Summary statistics are not raw observations."
    };
  }
  function assertSourceStoreShape(store) {
    if (!store || store.schema !== SOURCE_SCHEMA) fail("SOURCE_SCHEMA_MISMATCH", "Unsupported source-store schema.");
    for (const key of ["sources", "quotes", "marketRows", "episodes"]) if (!Array.isArray(store[key])) fail("INVALID_SOURCE_STORE", key + " must be an array.");
    if (!store.coverageExpectation || !Array.isArray(store.coverageExpectation.expectedTradingDates)) fail("INVALID_SOURCE_STORE", "Expected trading dates must be an array.");
  }
  function validateSourceStore(store) {
    assertSourceStoreShape(store);
    const quoteKeys = new Set();
    for (const quote of store.quotes) {
      const normalized = normalizeQuote(quote, quote.sourceId, quote.sourceFileHash);
      if (quote.contractIdentityState !== normalized.contractIdentityState || quote.adjustedContract !== normalized.adjustedContract) {
        fail("INVALID_SOURCE_STORE", "Contract identity flags do not match the contract terms for " + quote.contractId + ".");
      }
      const key = normalized.contractId + "|" + normalized.asOf + "|" + normalized.sourceId;
      if (quoteKeys.has(key)) fail("DUPLICATE_QUOTE", "Duplicate contract/asOf/source row: " + key);
      quoteKeys.add(key);
      if (quote.sourceAuthentication !== "UNAUTHENTICATED_UPLOAD") fail("INVALID_SOURCE_STORE", "Source authenticity cannot be self-attested inside a portable bundle.");
    }
    const marketKeys = new Set();
    for (const row of store.marketRows) {
      const normalized = normalizeMarketRow(row, row.sourceId, row.sourceFileHash);
      const key = normalized.symbol + "|" + normalized.date + "|" + normalized.adjustmentBasis + "|" + normalized.sourceId;
      if (marketKeys.has(key)) fail("DUPLICATE_MARKET_ROW", "Duplicate price row: " + key);
      marketKeys.add(key);
      if (row.sourceAuthentication !== "UNAUTHENTICATED_UPLOAD") fail("INVALID_SOURCE_STORE", "Source authenticity cannot be self-attested inside a portable bundle.");
    }
    const episodeIds = new Set();
    for (const episode of store.episodes) {
      const normalized = normalizeEpisode(episode);
      if (episodeIds.has(normalized.episodeId)) fail("DUPLICATE_EPISODE", "Duplicate episodeId: " + normalized.episodeId);
      episodeIds.add(normalized.episodeId);
    }
    for (const date of store.coverageExpectation.expectedTradingDates) if (!validDate(date)) fail("INVALID_SOURCE_STORE", "Expected coverage contains an invalid date.");
    return true;
  }

  function mergeRows(store, property, rows, sourceEntry) {
    const next = JSON.parse(JSON.stringify(store));
    next[property] = next[property].concat(rows);
    next.sources.push(sourceEntry);
    if (next.quotes.length) next.status = "RAW_ROWS_IMPORTED_SOURCE_AUTHENTICATION_PENDING";
    validateSourceStore(next);
    return next;
  }
  async function importQuotesCSV(text, metadata, currentStore) {
    const meta = metadata || {}, sourceId = textValue(meta.sourceId);
    if (!sourceId) fail("SOURCE_ID_REQUIRED", "A stable sourceId is required.");
    const rawFileHash = await sha256Hex(text), rows = parseCSV(text);
    const quotes = rows.map(row => {
      try { return normalizeQuote(row, sourceId, rawFileHash); }
      catch (error) { fail(error.code || "INVALID_QUOTE", "CSV row " + row.__rowNumber + ": " + error.message); }
    });
    return mergeRows(currentStore || createEmptySourceStore(), "quotes", quotes, {
      sourceId, sourceName: textValue(meta.sourceName) || "UNNAMED_UPLOAD",
      sourceUrl: textValue(meta.sourceUrl) || null, rawFileHash, importedRowCount: quotes.length,
      evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD"
    });
  }
  async function importQuotesJSON(text, metadata, currentStore) {
    const meta = metadata || {}, sourceId = textValue(meta.sourceId);
    if (!sourceId) fail("SOURCE_ID_REQUIRED", "A stable sourceId is required.");
    let parsed;
    try { parsed = JSON.parse(text); } catch (_) { fail("INVALID_JSON", "Quote JSON cannot be parsed."); }
    const rows = Array.isArray(parsed) ? parsed : parsed && parsed.schema === "qqq-historical-option-chain.v1" && Array.isArray(parsed.records) ? parsed.records : null;
    if (!rows || !rows.length) fail("INVALID_JSON", "Expected a non-empty array or qqq-historical-option-chain.v1 records object.");
    const rawFileHash = await sha256Hex(text);
    const quotes = rows.map((row, index) => {
      try { return normalizeQuote(row, sourceId, rawFileHash); }
      catch (error) { fail(error.code || "INVALID_QUOTE", "JSON record " + (index + 1) + ": " + error.message); }
    });
    return mergeRows(currentStore || createEmptySourceStore(), "quotes", quotes, {
      sourceId, sourceName: textValue(meta.sourceName) || "UNNAMED_UPLOAD", sourceUrl: textValue(meta.sourceUrl) || null,
      rawFileHash, importedRowCount: quotes.length, evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD"
    });
  }
  async function importEpisodesCSV(text, metadata, currentStore) {
    const meta = metadata || {}, sourceId = textValue(meta.sourceId);
    if (!sourceId) fail("SOURCE_ID_REQUIRED", "A stable sourceId is required.");
    const rawFileHash = await sha256Hex(text), rows = parseCSV(text);
    const episodes = rows.map(row => {
      try { return normalizeEpisode(row); }
      catch (error) { fail(error.code || "INVALID_EPISODE", "CSV row " + row.__rowNumber + ": " + error.message); }
    });
    return mergeRows(currentStore || createEmptySourceStore(), "episodes", episodes, {
      sourceId, sourceName: textValue(meta.sourceName) || "UNNAMED_EPISODE_SPEC", sourceUrl: textValue(meta.sourceUrl) || null,
      rawFileHash, importedRowCount: episodes.length, evidenceClass: "USER_DEFINED_EPISODE_SPEC", sourceAuthentication: "UNAUTHENTICATED_UPLOAD"
    });
  }
  async function importMarketCSV(text, metadata, currentStore) {
    const meta = metadata || {}, sourceId = textValue(meta.sourceId);
    if (!sourceId) fail("SOURCE_ID_REQUIRED", "A stable sourceId is required.");
    const rawFileHash = await sha256Hex(text), rows = parseCSV(text);
    const marketRows = rows.map(row => {
      try { return normalizeMarketRow(row, sourceId, rawFileHash); }
      catch (error) { fail(error.code || "INVALID_MARKET_ROW", "CSV row " + row.__rowNumber + ": " + error.message); }
    });
    return mergeRows(currentStore || createEmptySourceStore(), "marketRows", marketRows, {
      sourceId, sourceName: textValue(meta.sourceName) || "UNNAMED_PRICE_HISTORY", sourceUrl: textValue(meta.sourceUrl) || null,
      rawFileHash, importedRowCount: marketRows.length, evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD"
    });
  }

  function coverageReport(store, expectedTradingDates) {
    validateSourceStore(store);
    const expected = Array.from(new Set((expectedTradingDates || store.coverageExpectation.expectedTradingDates || []).slice().sort()));
    const optionDates = new Set(store.quotes.map(row => row.asOf.slice(0, 10)));
    const qqqPriceDates = new Set(store.marketRows.filter(row => row.symbol === "QQQ").map(row => row.date));
    return {
      expectedTradingDays: expected.length,
      optionChainCoveredDays: expected.filter(date => optionDates.has(date)).length,
      missingOptionChainDates: expected.filter(date => !optionDates.has(date)),
      qqqPriceCoveredDays: expected.filter(date => qqqPriceDates.has(date)).length,
      missingQqqPriceDates: expected.filter(date => !qqqPriceDates.has(date)),
      evidenceNote: "Option-chain coverage and underlying-price coverage are separate. Underlying-only dates never count as option-chain observations."
    };
  }
  function deriveHistoricalPriceDropStats(marketRows, options) {
    const opts = options || {};
    const horizon = strictNumber(opts.horizonTradingObservations, "horizonTradingObservations", { min: 1, integer: true });
    if (!Array.isArray(opts.thresholdsPct) || !opts.thresholdsPct.length) fail("INVALID_STATISTICS_INPUT", "thresholdsPct must be a non-empty array.");
    const basis = textValue(opts.adjustmentBasis).toUpperCase();
    if (!["RAW", "ADJUSTED"].includes(basis)) fail("INVALID_STATISTICS_INPUT", "Choose RAW or ADJUSTED price basis explicitly.");
    const rows = marketRows.filter(row => row.symbol === "QQQ" && row.adjustmentBasis === basis).slice().sort((a, b) => a.date.localeCompare(b.date));
    const dates = new Set();
    for (const row of rows) {
      if (dates.has(row.date)) fail("AMBIGUOUS_PRICE_HISTORY", "Multiple QQQ " + basis + " values exist on " + row.date + ".");
      dates.add(row.date);
    }
    if (rows.length <= horizon) return {
      status: "INSUFFICIENT_OBSERVATIONS", evidenceClass: "DERIVED",
      measure: "QQQ_PRICE_PATH_DROP_FREQUENCY_NOT_OPTION_STRATEGY_WIN_RATE",
      adjustmentBasis: basis, horizonTradingObservations: horizon, denominator: 0, thresholds: []
    };
    const valid = [];
    for (let i = 0; i + horizon < rows.length; i += 1) valid.push({
      startDate: rows[i].date, endDate: rows[i + horizon].date,
      returnPct: (rows[i + horizon].close / rows[i].close - 1) * 100
    });
    return {
      status: "DESCRIPTIVE_HISTORICAL_PROXY", evidenceClass: "DERIVED",
      measure: "QQQ_PRICE_PATH_DROP_FREQUENCY_NOT_OPTION_STRATEGY_WIN_RATE",
      adjustmentBasis: basis, horizonTradingObservations: horizon,
      denominator: valid.length, sampleStart: rows[0].date, sampleEnd: rows[rows.length - 1].date,
      calendarNote: "Horizon counts imported observations. Missing sessions can distort interpretation; supply a complete expected trading calendar before calling this consecutive-session frequency.",
      thresholds: opts.thresholdsPct.map(raw => {
        const threshold = strictNumber(raw, "thresholdPct", { min: 0.000001 });
        const events = valid.filter(item => item.returnPct <= -threshold).length;
        return { thresholdDropPct: threshold, events, denominator: valid.length, frequencyPct: events / valid.length * 100 };
      })
    };
  }

  function uniqueQuote(store, contractId, asOf) {
    const matches = store.quotes.filter(row => row.contractId === contractId && row.asOf === asOf);
    if (!matches.length) fail("MISSING_EXACT_QUOTE", "No exact quote for " + contractId + " at " + asOf + ".");
    if (matches.length > 1) fail("AMBIGUOUS_EXACT_QUOTE", "More than one quote matches " + contractId + " at " + asOf + ".");
    return matches[0];
  }
  function replayPutRatioEpisode(store, episodeInput, costInput) {
    validateSourceStore(store);
    const episode = normalizeEpisode(episodeInput), costs = costInput || {};
    const slippage = strictNumber(costs.slippageUsdPerContractPerSide, "slippageUsdPerContractPerSide", { min: 0 });
    const commission = strictNumber(costs.commissionUsdPerContractPerSide, "commissionUsdPerContractPerSide", { min: 0 });
    const le = uniqueQuote(store, episode.longContractId, episode.entryAsOf);
    const se = uniqueQuote(store, episode.shortContractId, episode.entryAsOf);
    const lx = uniqueQuote(store, episode.longContractId, episode.exitAsOf);
    const sx = uniqueQuote(store, episode.shortContractId, episode.exitAsOf);
    const legs = [le, se, lx, sx];
    if (legs.some(row => row.contractIdentityState !== "OCC_TERMS_MATCH")) fail("BLOCKED_CONTRACT_IDENTITY", "Replay requires matching standard OCC identity; adjusted or unidentified terms are unsupported.");
    if (legs.some(row => row.adjustedContract)) fail("BLOCKED_ADJUSTED_DELIVERABLE", "Adjusted option deliverables are not modeled.");
    if (le.underlying !== "QQQ" || se.underlying !== "QQQ" || le.right !== "P" || se.right !== "P") fail("INVALID_RATIO_STRUCTURE", "This replay is specifically for QQQ put-ratio structures.");
    if (le.expiry !== se.expiry || le.expiry !== lx.expiry || le.expiry !== sx.expiry) fail("INVALID_RATIO_STRUCTURE", "Both legs must use the same expiry.");
    if (le.strike <= se.strike) fail("INVALID_RATIO_STRUCTURE", "Long put strike must exceed short put strike.");
    if (le.multiplier !== se.multiplier || le.multiplier !== lx.multiplier || le.multiplier !== sx.multiplier) fail("INVALID_RATIO_STRUCTURE", "Leg multipliers differ.");
    if (le.askSize < 1 || se.bidSize < episode.nShort || lx.bidSize < 1 || sx.askSize < episode.nShort) fail("BLOCKED_INSUFFICIENT_QUOTE_DEPTH", "Observed-side sizes do not cover all requested contracts on all four legs.");
    const multiplier = le.multiplier;
    const grossPnl = (lx.bid - le.ask + episode.nShort * (se.bid - sx.ask)) * multiplier;
    const frictionCostUsd = 2 * (1 + episode.nShort) * (slippage + commission);
    return {
      episodeId: episode.episodeId, entryAsOf: episode.entryAsOf, exitAsOf: episode.exitAsOf,
      longContractId: episode.longContractId, shortContractId: episode.shortContractId,
      nLong: 1, nShort: episode.nShort, grossPnlUsd: grossPnl, frictionCostUsd, netPnlUsd: grossPnl - frictionCostUsd,
      costInputs: { slippageUsdPerContractPerSide: slippage, commissionUsdPerContractPerSide: commission },
      evidenceClass: "DERIVED", executionEvidence: "EOD_QUOTE_SIDE_REPLAY", confirmedFill: false,
      note: "Exact uploaded timestamps; buy-at-ask/sell-at-bid with side-specific sizes. Not a confirmed fill or future win probability."
    };
  }
  function summarizeEpisodeReplays(results) {
    const resolved = results.filter(row => row && Number.isFinite(row.netPnlUsd));
    const wins = resolved.filter(row => row.netPnlUsd > 0).length;
    return {
      resolvedEpisodes: resolved.length, wins, nonPositiveEpisodes: resolved.length - wins,
      winRatePct: resolved.length ? wins / resolved.length * 100 : null,
      totalNetPnlUsd: resolved.reduce((sum, row) => sum + row.netPnlUsd, 0),
      evidenceClass: "DERIVED",
      statisticMeaning: "Descriptive resolved-episode quote-side replay ratio only; not a forecast and not independently authenticated market data."
    };
  }

  function evaluateLedger(input) {
    const x = input || {}, missing = [], values = {};
    for (const key of ["cashBalance", "qqqShares", "vxxShortQty", "qqqCallQty", "vxxCallQty"]) {
      const parsed = parseStrictNumber(x[key]);
      if (parsed.state !== "VALID") missing.push(key + (parsed.state === "EMPTY" ? " (missing)" : " (invalid number)"));
      else values[key] = parsed.value;
    }
    if (missing.length) return { ledgerComplete: false, reconciledWithStatement: false, status: "BLOCKED_MISSING_POSITION_BASIS", missingFields: missing, totalNav: null, conservationDelta: null };
    for (const key of ["qqqShares", "vxxShortQty", "qqqCallQty", "vxxCallQty"]) {
      if (!Number.isInteger(values[key]) || values[key] < 0) fail("INVALID_POSITION_QUANTITY", key + " must be a non-negative whole number.");
    }
    const qqqShares = values.qqqShares, vxxShortQty = values.vxxShortQty;
    const qqqCallQty = values.qqqCallQty, vxxCallQty = values.vxxCallQty, cashBalance = values.cashBalance;
    const parsed = {}, conditionalFields = [];
    function readIfHeld(key, held, options) {
      const result = parseStrictNumber(x[key]);
      if (held && result.state !== "VALID") conditionalFields.push(key + (result.state === "EMPTY" ? " (required for an open position)" : " (invalid number)"));
      else if (held) {
        const n = result.value;
        if (options && options.min !== undefined && n < options.min) conditionalFields.push(key + " (must be >= " + options.min + ")");
        else parsed[key] = n;
      } else parsed[key] = result.state === "VALID" ? result.value : 0;
    }
    readIfHeld("qqqSpot", qqqShares > 0, { min: 0.000001 });
    readIfHeld("qqqEntryPrice", qqqShares > 0, { min: 0.000001 });
    readIfHeld("vxxSpot", vxxShortQty > 0, { min: 0.000001 });
    readIfHeld("vxxEntryPrice", vxxShortQty > 0, { min: 0.000001 });
    for (const [prefix, qty] of [["qqqCall", qqqCallQty], ["vxxCall", vxxCallQty]]) {
      if (qty > 0) {
        for (const suffix of ["EntryCredit", "CurrentMark", "Width", "Multiplier"]) {
          const key = prefix + suffix, result = parseStrictNumber(x[key]);
          if (result.state !== "VALID") conditionalFields.push(key + (result.state === "EMPTY" ? " (required for an open position)" : " (invalid number)"));
          else parsed[key] = result.value;
        }
        if (parsed[prefix + "EntryCredit"] !== undefined && parsed[prefix + "EntryCredit"] <= 0) conditionalFields.push(prefix + "EntryCredit (must be > 0)");
        if (parsed[prefix + "CurrentMark"] !== undefined && parsed[prefix + "CurrentMark"] < 0) conditionalFields.push(prefix + "CurrentMark (must be >= 0)");
        if (parsed[prefix + "Width"] !== undefined && parsed[prefix + "Width"] <= 0) conditionalFields.push(prefix + "Width (must be > 0)");
        if (parsed[prefix + "Multiplier"] !== undefined && (!Number.isInteger(parsed[prefix + "Multiplier"]) || parsed[prefix + "Multiplier"] <= 0)) conditionalFields.push(prefix + "Multiplier (must be a positive whole number)");
        if (parsed[prefix + "Width"] !== undefined && parsed[prefix + "EntryCredit"] !== undefined && parsed[prefix + "Width"] <= parsed[prefix + "EntryCredit"]) conditionalFields.push(prefix + "Width (must exceed entry credit to compute finite defined-risk max loss)");
      } else for (const suffix of ["EntryCredit", "CurrentMark", "Width", "Multiplier"]) parsed[prefix + suffix] = 0;
    }
    if (conditionalFields.length) return { ledgerComplete: false, reconciledWithStatement: false, status: "BLOCKED_MISSING_POSITION_BASIS", missingFields: conditionalFields, totalNav: null, conservationDelta: null };

    const qqqSpot = qqqShares > 0 ? parsed.qqqSpot : optionalNumber(x.qqqSpot);
    const vxxSpot = vxxShortQty > 0 ? parsed.vxxSpot : optionalNumber(x.vxxSpot);
    const qqqMarketValue = qqqShares * (qqqSpot || 0);
    const vxxShortLiability = vxxShortQty * (vxxSpot || 0);
    const qqqCallLiability = qqqCallQty * parsed.qqqCallCurrentMark * parsed.qqqCallMultiplier;
    const vxxCallLiability = vxxCallQty * parsed.vxxCallCurrentMark * parsed.vxxCallMultiplier;
    // cashBalance means account/broker cash and already includes posted short-sale proceeds and option credits.
    const totalAssets = cashBalance + qqqMarketValue;
    const totalLiabilities = vxxShortLiability + qqqCallLiability + vxxCallLiability;
    const derivedNav = totalAssets - totalLiabilities;
    const qqqUnrealizedPnl = qqqShares * ((qqqSpot || 0) - (parsed.qqqEntryPrice || 0));
    const vxxUnrealizedPnl = vxxShortQty * ((parsed.vxxEntryPrice || 0) - (vxxSpot || 0));
    const qqqCallUnrealizedPnl = qqqCallQty * (parsed.qqqCallEntryCredit - parsed.qqqCallCurrentMark) * parsed.qqqCallMultiplier;
    const vxxCallUnrealizedPnl = vxxCallQty * (parsed.vxxCallEntryCredit - parsed.vxxCallCurrentMark) * parsed.vxxCallMultiplier;
    const qqqCallMaxExpiryLoss = qqqCallQty * Math.max(0, parsed.qqqCallWidth - parsed.qqqCallEntryCredit) * parsed.qqqCallMultiplier;
    const vxxCallMaxExpiryLoss = vxxCallQty * Math.max(0, parsed.vxxCallWidth - parsed.vxxCallEntryCredit) * parsed.vxxCallMultiplier;
    const baseResult = {
      ledgerComplete: true, reconciledWithStatement: false, status: "UNRECONCILED_NO_STATEMENT",
      missingFields: [], cashBalance, qqqShares, qqqMarketValue, qqqUnrealizedPnl,
      vxxShortQty, vxxShortLiability, vxxUnrealizedPnl,
      qqqCallQty, qqqCallLiability, qqqCallUnrealizedPnl, qqqCallMaxExpiryLoss,
      vxxCallQty, vxxCallLiability, vxxCallUnrealizedPnl, vxxCallMaxExpiryLoss,
      totalAssets, totalLiabilities, ledgerDerivedNav: derivedNav, totalNav: derivedNav,
      conservationDelta: null, statementNav: null,
      manualNavOverride: optionalNumber(x.navOverride),
      accountingAssumption: "Cash balance includes posted short-sale proceeds and option premiums; they are not added a second time."
    };
    const statementParsed = parseStrictNumber(x.statementNav);
    if (statementParsed.state === "EMPTY") return baseResult;
    if (statementParsed.state !== "VALID" || statementParsed.value <= 0) {
      return {
        ...baseResult, ledgerComplete: false, status: "BLOCKED_INVALID_STATEMENT_NAV", totalNav: null,
        missingFields: ["statementNav must be a positive finite value when provided."]
      };
    }
    const statementEvidence = {
      sourceId: textValue(x.statementSourceId),
      asOf: textValue(x.statementAsOf),
      fileSha256: textValue(x.statementFileSha256).toLowerCase()
    };
    const statementProvenanceMissing = [];
    if (!statementEvidence.sourceId) statementProvenanceMissing.push("statementSourceId");
    if (!validInstant(statementEvidence.asOf)) statementProvenanceMissing.push("statementAsOf (ISO timestamp with timezone)");
    if (!/^[a-f0-9]{64}$/.test(statementEvidence.fileSha256)) statementProvenanceMissing.push("statementFileSha256 (SHA-256 of the source file)");
    if (statementProvenanceMissing.length) {
      return {
        ...baseResult, status: "UNRECONCILED_STATEMENT_PROVENANCE_MISSING",
        missingFields: statementProvenanceMissing,
        statementNavCandidate: statementParsed.value
      };
    }
    const conservationDelta = Math.abs(derivedNav - statementParsed.value);
    if (conservationDelta > 0.01) {
      return {
        ...baseResult, ledgerComplete: false, status: "BLOCKED_STATEMENT_RECONCILIATION_MISMATCH",
        missingFields: ["Source-tagged statement NAV differs from ledger-derived NAV by $" + conservationDelta.toFixed(2) + " (tolerance $0.01)."],
        totalNav: null, conservationDelta, statementNavCandidate: statementParsed.value,
        statementEvidence
      };
    }
    return {
      ...baseResult, reconciledWithStatement: true,
      status: "RECONCILED_TO_SOURCE_TAGGED_STATEMENT_NOT_AUTHENTICATED",
      missingFields: [], conservationDelta, statementNav: statementParsed.value, statementEvidence,
      note: "The statement file hash and source metadata are recorded, but source authenticity still requires independent verification."
    };
  }

  function computeDynamicCostStrict(units, slippageRaw, commissionRaw) {
    let n;
    try { n = strictNumber(units, "units", { min: 0, integer: true }); }
    catch (error) { return { valid: false, status: error.code || "INVALID_UNITS", costUsd: null }; }
    const slip = parseStrictNumber(slippageRaw), comm = parseStrictNumber(commissionRaw);
    if (slip.state !== "VALID" || comm.state !== "VALID" || slip.value < 0 || comm.value < 0) return { valid: false, status: "BLOCKED_COST_INPUT_MISSING_OR_INVALID", costUsd: null };
    return {
      valid: true, status: "COST_INPUTS_VALID",
      slippageUsdPerContractPerSide: slip.value, commissionUsdPerContractPerSide: comm.value,
      costUsd: 2 * n * (slip.value + comm.value)
    };
  }

  function deriveJointStressFromHoldingsStrict(ledger, stressInput, candidates) {
    if (!ledger || ledger.ledgerComplete !== true) return { valid: false, status: "BLOCKED_LEDGER_INCOMPLETE", totalLossUsd: null };
    const stress = stressInput || {}, optionCandidates = candidates || {}, losses = {};
    function stockLoss(key, active) {
      if (!active) { losses[key] = 0; return; }
      const parsed = parseStrictNumber(stress[key]);
      if (parsed.state !== "VALID" || parsed.value < 0) fail("BLOCKED_STRESS_LOSS_UNKNOWN", key + " must be an explicit non-negative scenario loss.");
      losses[key] = parsed.value;
    }
    try {
      stockLoss("qqqCoreShockLossUsd", ledger.qqqShares > 0);
      stockLoss("vxxShortShockLossUsd", ledger.vxxShortQty > 0);
      for (const [key, qtyKey] of [["qqqCall", "qqqCallQty"], ["vxxCall", "vxxCallQty"]]) {
        const qty = ledger[qtyKey] || 0;
        if (qty === 0) { losses[key + "MaxExpiryLossUsd"] = 0; continue; }
        const candidate = optionCandidates[key], maxLoss = parseStrictNumber(candidate && candidate.maxExpirationLossPerSpread);
        if (!candidate || candidate.valid !== true || maxLoss.state !== "VALID" || maxLoss.value < 0) fail("BLOCKED_CANDIDATE_LOSS_UNKNOWN", key + " contract is invalid or maximum expiry loss is unknown; no fixed fallback is allowed.");
        losses[key + "MaxExpiryLossUsd"] = qty * maxLoss.value;
      }
    } catch (error) {
      return { valid: false, status: error.code || "BLOCKED_CANDIDATE_LOSS_UNKNOWN", totalLossUsd: null, reason: error.message };
    }
    return {
      valid: true, status: "HYPOTHETICAL_STRESS_WITH_EXPLICIT_INPUTS",
      totalLossUsd: Object.values(losses).reduce((sum, value) => sum + value, 0),
      componentLossesUsd: losses, evidenceClass: "HYPOTHETICAL",
      note: "Scenario sum only; not VaR, a forecast, broker margin or proof of executable liquidation."
    };
  }

  async function buildFullStateBundle(state) {
    const x = state || {};
    if (!x.inputs || !x.barParams || !x.probParams || !x.floorAndDveParams || !x.engineOutput) fail("INCOMPLETE_STATE", "inputs, barParams, probParams, floorAndDveParams and engineOutput are required.");

    // Hash the exact JSON-compatible snapshot that is exported, not the pre-serialization
    // object. JSON omits undefined object properties; hashing the original object would
    // create a hash for data that is not actually present in the bundle.
    function jsonSnapshot(value, label) {
      let encoded;
      try { encoded = JSON.stringify(value); }
      catch (error) { fail("STATE_NOT_JSON_SERIALIZABLE", label + " cannot be serialized: " + error.message); }
      if (encoded === undefined) fail("STATE_NOT_JSON_SERIALIZABLE", label + " did not produce a JSON value.");
      try { return JSON.parse(encoded); }
      catch (_) { fail("STATE_NOT_JSON_SERIALIZABLE", label + " did not produce valid JSON."); }
    }
    const sourceStore = jsonSnapshot(x.sourceStore || createEmptySourceStore(), "sourceStore");
    const inputs = jsonSnapshot(x.inputs, "inputs");
    const barParams = jsonSnapshot(x.barParams, "barParams");
    const probParams = jsonSnapshot(x.probParams, "probParams");
    const floorAndDveParams = jsonSnapshot(x.floorAndDveParams, "floorAndDveParams");
    const engineOutput = jsonSnapshot(x.engineOutput, "engineOutput");
    validateSourceStore(sourceStore);
    const scenario = { inputs, barParams, probParams, floorAndDveParams };
    return {
      schema: STATE_SCHEMA, brokerOrdersAllowed: false, exportedAt: textValue(x.exportedAt) || null,
      sourceStore, inputs, barParams, probParams, floorAndDveParams, engineOutput,
      hashes: {
        sourceHash: await sha256Hex(sourceStore),
        scenarioHash: await sha256Hex(scenario),
        engineOutputHash: await sha256Hex(engineOutput)
      },
      integrityNote: "Hashes cover the exact embedded JSON snapshot and detect inconsistency relative to the bundle; they are not a digital signature or source-authentication proof."
    };
  }

  async function verifyAndStageFullStateBundle(rawBundle, policy) {
    const opts = policy || {};
    let bundle = rawBundle;
    if (typeof rawBundle === "string") {
      try { bundle = JSON.parse(rawBundle); } catch (_) { fail("INVALID_JSON", "State bundle is not valid JSON."); }
    }
    if (!bundle || bundle.schema !== STATE_SCHEMA) fail("REJECTED_SCHEMA_MISMATCH", "Expected " + STATE_SCHEMA + ".");
    if (bundle.brokerOrdersAllowed !== false) fail("REJECTED_BROKER_BOUNDARY", "brokerOrdersAllowed must be false.");
    for (const key of ["sourceStore", "inputs", "barParams", "probParams", "floorAndDveParams", "engineOutput", "hashes"]) {
      if (!Object.prototype.hasOwnProperty.call(bundle, key) || bundle[key] === null || bundle[key] === undefined) fail("REJECTED_INCOMPLETE_BUNDLE", "Missing " + key + ".");
    }
    for (const key of ["sourceHash", "scenarioHash", "engineOutputHash"]) {
      if (typeof bundle.hashes[key] !== "string" || !/^[a-f0-9]{64}$/i.test(bundle.hashes[key])) fail("REJECTED_INCOMPLETE_BUNDLE", "Missing/invalid SHA-256 " + key + ".");
    }
    validateSourceStore(bundle.sourceStore);
    const actualSourceHash = await sha256Hex(bundle.sourceStore);
    if (actualSourceHash !== bundle.hashes.sourceHash) fail("HASH_INTEGRITY_MISMATCH", "sourceHash does not match the entire embedded source store.");
    if (opts.expectedSourceHash && actualSourceHash !== opts.expectedSourceHash) fail("SOURCE_HASH_NOT_TRUSTED", "Source store differs from externally pinned source hash.");
    const scenario = { inputs: bundle.inputs, barParams: bundle.barParams, probParams: bundle.probParams, floorAndDveParams: bundle.floorAndDveParams };
    if (await sha256Hex(scenario) !== bundle.hashes.scenarioHash) fail("HASH_INTEGRITY_MISMATCH", "scenarioHash does not match all inputs and parameter groups.");
    if (await sha256Hex(bundle.engineOutput) !== bundle.hashes.engineOutputHash) fail("HASH_INTEGRITY_MISMATCH", "engineOutputHash does not match the embedded output.");
    if (typeof opts.evaluate !== "function") fail("RECOMPUTE_REQUIRED", "An independent deterministic evaluator is required before restore.");
    const derivedOutput = await opts.evaluate({
      inputs: JSON.parse(JSON.stringify(bundle.inputs)), barParams: JSON.parse(JSON.stringify(bundle.barParams)),
      probParams: JSON.parse(JSON.stringify(bundle.probParams)), floorAndDveParams: JSON.parse(JSON.stringify(bundle.floorAndDveParams)),
      sourceStore: JSON.parse(JSON.stringify(bundle.sourceStore))
    });
    if (await sha256Hex(derivedOutput) !== bundle.hashes.engineOutputHash) fail("OUTPUT_REPRODUCIBILITY_MISMATCH", "Recomputed engine output does not match engineOutputHash.");
    return {
      ok: true,
      stagedState: {
        inputs: JSON.parse(JSON.stringify(bundle.inputs)), barParams: JSON.parse(JSON.stringify(bundle.barParams)),
        probParams: JSON.parse(JSON.stringify(bundle.probParams)), floorAndDveParams: JSON.parse(JSON.stringify(bundle.floorAndDveParams)),
        sourceStore: JSON.parse(JSON.stringify(bundle.sourceStore)), engineOutput: JSON.parse(JSON.stringify(derivedOutput)),
        hashes: Object.assign({}, bundle.hashes)
      },
      commitAllowed: true, brokerOrdersAllowed: false
    };
  }

  async function restoreFullStateBundle(rawBundle, adapter, policy) {
    if (!adapter || typeof adapter.commitStagedState !== "function") fail("RESTORE_ADAPTER_REQUIRED", "Provide an atomic commitStagedState adapter.");
    const verified = await verifyAndStageFullStateBundle(rawBundle, policy);
    const previous = typeof adapter.snapshotState === "function" ? await adapter.snapshotState() : undefined;
    try {
      await adapter.commitStagedState(verified.stagedState);
    } catch (error) {
      if (typeof adapter.restorePreviousState === "function" && previous !== undefined) await adapter.restorePreviousState(previous);
      throw error;
    }
    return { ok: true, restored: true, brokerOrdersAllowed: false, hashes: verified.stagedState.hashes };
  }

  return Object.freeze({
    SOURCE_SCHEMA, STATE_SCHEMA, QUOTE_SCHEMA,
    parseStrictNumber, strictNumber, canonicalize, sha256Hex, parseCSV, parseOcc,
    createEmptySourceStore, validateSourceStore, importQuotesCSV, importQuotesJSON, importEpisodesCSV, importMarketCSV,
    coverageReport, deriveHistoricalPriceDropStats, replayPutRatioEpisode, summarizeEpisodeReplays,
    evaluateLedger, computeDynamicCostStrict, deriveJointStressFromHoldingsStrict,
    buildFullStateBundle, verifyAndStageFullStateBundle, restoreFullStateBundle
  });
});
if (typeof globalThis !== "undefined") globalThis.SharedContractEngineV43 = SharedContractEngineV43;
export const SOURCE_SCHEMA = SharedContractEngineV43.SOURCE_SCHEMA;
export const STATE_SCHEMA = SharedContractEngineV43.STATE_SCHEMA;
export const QUOTE_SCHEMA = SharedContractEngineV43.QUOTE_SCHEMA;
export const parseStrictNumber = SharedContractEngineV43.parseStrictNumber;
export const strictNumber = SharedContractEngineV43.strictNumber;
export const canonicalize = SharedContractEngineV43.canonicalize;
export const sha256Hex = SharedContractEngineV43.sha256Hex;
export const parseCSV = SharedContractEngineV43.parseCSV;
export const parseOcc = SharedContractEngineV43.parseOcc;
export const createEmptySourceStore = SharedContractEngineV43.createEmptySourceStore;
export const validateSourceStore = SharedContractEngineV43.validateSourceStore;
export const importQuotesCSV = SharedContractEngineV43.importQuotesCSV;
export const importQuotesJSON = SharedContractEngineV43.importQuotesJSON;
export const importEpisodesCSV = SharedContractEngineV43.importEpisodesCSV;
export const importMarketCSV = SharedContractEngineV43.importMarketCSV;
export const coverageReport = SharedContractEngineV43.coverageReport;
export const deriveHistoricalPriceDropStats = SharedContractEngineV43.deriveHistoricalPriceDropStats;
export const replayPutRatioEpisode = SharedContractEngineV43.replayPutRatioEpisode;
export const summarizeEpisodeReplays = SharedContractEngineV43.summarizeEpisodeReplays;
export const evaluateLedger = SharedContractEngineV43.evaluateLedger;
export const computeDynamicCostStrict = SharedContractEngineV43.computeDynamicCostStrict;
export const deriveJointStressFromHoldingsStrict = SharedContractEngineV43.deriveJointStressFromHoldingsStrict;
export const buildFullStateBundle = SharedContractEngineV43.buildFullStateBundle;
export const verifyAndStageFullStateBundle = SharedContractEngineV43.verifyAndStageFullStateBundle;
export const restoreFullStateBundle = SharedContractEngineV43.restoreFullStateBundle;
export default SharedContractEngineV43;
