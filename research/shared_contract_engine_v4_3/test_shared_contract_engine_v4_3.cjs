"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const E = require("./shared_contract_engine_v4_3.js");

const ENTRY = "2030-06-03T20:00:00Z";
const EXIT = "2030-06-10T20:00:00Z";
const EXPIRY = "2030-06-21";
const LONG = "QQQ300621P00500000";
const SHORT = "QQQ300621P00480000";
const HASH = "a".repeat(64);

function quote(contractId, strike, asOf, bid, ask, bidSize = 20, askSize = 20, overrides = {}) {
  return {
    sourceId: "TEST_ONLY_NOT_MARKET_DATA", sourceFileHash: HASH, contractId,
    underlying: "QQQ", expiry: EXPIRY, right: "P", strike, asOf, bid, ask, bidSize, askSize, multiplier: 100,
    contractIdentityState: "OCC_TERMS_MATCH", adjustedContract: false,
    evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD",
    ...overrides
  };
}
function replayStore(overrides = {}) {
  const store = E.createEmptySourceStore();
  store.status = "RAW_ROWS_IMPORTED_SOURCE_AUTHENTICATION_PENDING";
  store.sources = [{ sourceId: "TEST_ONLY_NOT_MARKET_DATA", sourceName: "TEST_ONLY", rawFileHash: HASH, importedRowCount: 4, evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD" }];
  store.quotes = [
    quote(LONG, 500, ENTRY, 3.1, 3.2), quote(SHORT, 480, ENTRY, 1.05, 1.12),
    quote(LONG, 500, EXIT, 7.0, 7.4), quote(SHORT, 480, EXIT, 4.0, 4.2),
    ...(overrides.quotes || [])
  ];
  return store;
}
function zeroLedger(overrides = {}) {
  return {
    cashBalance: 1000, qqqShares: 0, vxxShortQty: 0, qqqCallQty: 0, vxxCallQty: 0,
    qqqSpot: null, qqqEntryPrice: null, vxxSpot: null, vxxEntryPrice: null,
    qqqCallEntryCredit: null, qqqCallCurrentMark: null, qqqCallWidth: null, qqqCallMultiplier: null,
    vxxCallEntryCredit: null, vxxCallCurrentMark: null, vxxCallWidth: null, vxxCallMultiplier: null,
    ...overrides
  };
}
async function deterministicEvaluate(state) {
  return {
    ledgerStatus: state.inputs.ledgerStatus || "DERIVED_ONLY",
    nav: Number(state.inputs.cashBalance || 0) + Number(state.inputs.qqqShares || 0) * Number(state.inputs.qqqSpot || 0),
    barRisk: state.barParams.barRiskPct,
    probabilityFilter: state.probParams.probRegimeFilter,
    floorBase: state.floorAndDveParams.inpFloorBaseB,
    sourceQuoteCount: state.sourceStore.quotes.length
  };
}

test("01 strict parser distinguishes empty, zero and invalid", () => {
  assert.deepEqual(E.parseStrictNumber("  "), { state: "EMPTY", value: null });
  assert.deepEqual(E.parseStrictNumber("0"), { state: "VALID", value: 0 });
  assert.deepEqual(E.parseStrictNumber(0), { state: "VALID", value: 0 });
  assert.equal(E.parseStrictNumber("12USD").state, "INVALID");
  assert.equal(E.parseStrictNumber("0x10").state, "INVALID");
});
test("02 strict parser rejects booleans, arrays, objects, NaN and infinities", () => {
  for (const value of [true, false, [], {}, Infinity, NaN]) assert.equal(E.parseStrictNumber(value).state, "INVALID");
});
test("03 canonical hashes are invariant to object key order", async () => {
  assert.equal(await E.sha256Hex({ b: 2, a: 1 }), await E.sha256Hex({ a: 1, b: 2 }));
});
test("04 CSV parser handles CRLF and a quoted comma", () => {
  const rows = E.parseCSV('contractId,note\r\nQQQ300621P00500000,"test, fixture"\r\n');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].note, "test, fixture");
});
test("05 CSV parser rejects malformed quotes and inconsistent column counts", () => {
  assert.throws(() => E.parseCSV('a,b\n1,"bad'), /INVALID_CSV/);
  assert.throws(() => E.parseCSV("a,b\n1,2,3"), /INVALID_CSV/);
});
test("06 empty source store does not ship any synthetic episode or raw quote", () => {
  const empty = E.createEmptySourceStore();
  assert.equal(empty.status, "REPO_SUMMARY_REFERENCE_ONLY (UNVERIFIED_RAW_CHAIN)");
  assert.equal(empty.quotes.length, 0);
  assert.equal(empty.episodes.length, 0);
});
test("07 quote CSV import requires source identity and stores raw-file SHA-256", async () => {
  const csv = "contractId,underlying,expiry,right,strike,asOf,bid,ask,bidSize,askSize,multiplier\nQQQ300621P00500000,QQQ,2030-06-21,P,500,2030-06-03T20:00:00Z,3.1,3.2,20,20,100";
  await assert.rejects(() => E.importQuotesCSV(csv, {}, E.createEmptySourceStore()), /SOURCE_ID_REQUIRED/);
  const store = await E.importQuotesCSV(csv, { sourceId: "test-source", sourceName: "TEST_ONLY" }, E.createEmptySourceStore());
  assert.equal(store.quotes.length, 1);
  assert.match(store.quotes[0].sourceFileHash, /^[a-f0-9]{64}$/);
  assert.equal(store.quotes[0].sourceAuthentication, "UNAUTHENTICATED_UPLOAD");
});
test("08 quote importer rejects missing values rather than defaulting to zero", async () => {
  const csv = "contractId,underlying,expiry,right,strike,asOf,bid,ask,bidSize,askSize,multiplier\nQQQ300621P00500000,QQQ,2030-06-21,P,500,2030-06-03T20:00:00Z,,3.2,20,20,100";
  await assert.rejects(() => E.importQuotesCSV(csv, { sourceId: "test-source" }, E.createEmptySourceStore()), /MISSING_REQUIRED_VALUE/);
});
test("09 quote importer rejects timezone-less timestamps and crossed markets", async () => {
  const header = "contractId,underlying,expiry,right,strike,asOf,bid,ask,bidSize,askSize,multiplier\n";
  await assert.rejects(() => E.importQuotesCSV(header + "QQQ300621P00500000,QQQ,2030-06-21,P,500,2030-06-03T20:00:00,3.1,3.2,20,20,100", { sourceId: "t" }), /INVALID_QUOTE/);
  await assert.rejects(() => E.importQuotesCSV(header + "QQQ300621P00500000,QQQ,2030-06-21,P,500,2030-06-03T20:00:00Z,3.3,3.2,20,20,100", { sourceId: "t" }), /INVALID_QUOTE/);
});
test("10 quote importer rejects negative and fractional liquidity size", async () => {
  const header = "contractId,underlying,expiry,right,strike,asOf,bid,ask,bidSize,askSize,multiplier\n";
  await assert.rejects(() => E.importQuotesCSV(header + "QQQ300621P00500000,QQQ,2030-06-21,P,500,2030-06-03T20:00:00Z,3.1,3.2,-1,20,100", { sourceId: "t" }), /OUT_OF_RANGE/);
  await assert.rejects(() => E.importQuotesCSV(header + "QQQ300621P00500000,QQQ,2030-06-21,P,500,2030-06-03T20:00:00Z,3.1,3.2,1.5,20,100", { sourceId: "t" }), /INVALID_INTEGER/);
});
test("11 OCC symbol terms must agree with expiry, right and strike", async () => {
  const csv = "contractId,underlying,expiry,right,strike,asOf,bid,ask,bidSize,askSize,multiplier\nQQQ300621P00500000,QQQ,2030-06-19,P,500,2030-06-03T20:00:00Z,3.1,3.2,20,20,100";
  await assert.rejects(() => E.importQuotesCSV(csv, { sourceId: "t" }), /CONTRACT_IDENTITY_MISMATCH/);
});
test("12 coverage never substitutes spot-only history for option-chain coverage", () => {
  const store = replayStore();
  store.coverageExpectation.expectedTradingDates = ["2030-06-03", "2030-06-04", "2030-06-10"];
  store.marketRows = [{
    sourceId: "spot-source", sourceFileHash: HASH, symbol: "QQQ", date: "2030-06-04", close: 500,
    adjustmentBasis: "ADJUSTED", evidenceClass: "OBSERVED_UPLOAD_VALUES", sourceAuthentication: "UNAUTHENTICATED_UPLOAD"
  }];
  const report = E.coverageReport(store);
  assert.equal(report.expectedTradingDays, 3);
  assert.equal(report.optionChainCoveredDays, 2);
  assert.deepEqual(report.missingOptionChainDates, ["2030-06-04"]);
  assert.equal(report.qqqPriceCoveredDays, 1);
  assert.match(report.evidenceNote, /never count as option-chain observations/i);
});
test("13 duplicate exact quotes are rejected as ambiguous source rows", () => {
  const store = replayStore();
  store.quotes.push({ ...store.quotes[0] });
  assert.throws(() => E.validateSourceStore(store), /DUPLICATE_QUOTE/);
});
test("14 price-path drop statistics are not called option-strategy win rate", () => {
  const rows = [
    { symbol: "QQQ", adjustmentBasis: "ADJUSTED", date: "2030-01-02", close: 100 },
    { symbol: "QQQ", adjustmentBasis: "ADJUSTED", date: "2030-01-03", close: 94 },
    { symbol: "QQQ", adjustmentBasis: "ADJUSTED", date: "2030-01-04", close: 91 },
    { symbol: "QQQ", adjustmentBasis: "ADJUSTED", date: "2030-01-07", close: 97 }
  ];
  const out = E.deriveHistoricalPriceDropStats(rows, { horizonTradingObservations: 1, thresholdsPct: [5, 8], adjustmentBasis: "ADJUSTED" });
  assert.equal(out.denominator, 3);
  assert.equal(out.thresholds[0].events, 1);
  assert.match(out.measure, /NOT_OPTION_STRATEGY_WIN_RATE/);
});
test("15 market importer requires price adjustment basis", async () => {
  const good = "sourceId,symbol,date,close,adjustmentBasis\nmarket-source,QQQ,2030-01-02,100,ADJUSTED";
  const store = await E.importMarketCSV(good, { sourceId: "market-source" }, E.createEmptySourceStore());
  assert.equal(store.marketRows.length, 1);
  const bad = "sourceId,symbol,date,close\nmarket-source,QQQ,2030-01-02,100";
  await assert.rejects(() => E.importMarketCSV(bad, { sourceId: "market-source" }), /INVALID_MARKET_ROW/);
});
test("16 exact 1xN replay uses conservative quote sides and no confirmed-fill claim", () => {
  const out = E.replayPutRatioEpisode(replayStore(), {
    episodeId: "TEST_ONLY_EPISODE", longContractId: LONG, shortContractId: SHORT, nShort: 5, entryAsOf: ENTRY, exitAsOf: EXIT
  }, { slippageUsdPerContractPerSide: 0, commissionUsdPerContractPerSide: 0 });
  assert.equal(out.grossPnlUsd, (7 - 3.2 + 5 * (1.05 - 4.2)) * 100);
  assert.equal(out.frictionCostUsd, 0);
  assert.ok(Math.abs(out.netPnlUsd + 1195) < 1e-8, "floating-point cents remain within tolerance");
  assert.equal(out.confirmedFill, false);
  assert.equal(out.executionEvidence, "EOD_QUOTE_SIDE_REPLAY");
});
test("17 replay requires sufficient side-specific displayed depth", () => {
  const store = replayStore();
  store.quotes[3] = { ...store.quotes[3], askSize: 4 };
  assert.throws(() => E.replayPutRatioEpisode(store, {
    episodeId: "TEST_ONLY_DEPTH", longContractId: LONG, shortContractId: SHORT, nShort: 5, entryAsOf: ENTRY, exitAsOf: EXIT
  }, { slippageUsdPerContractPerSide: 0, commissionUsdPerContractPerSide: 0 }), /BLOCKED_INSUFFICIENT_QUOTE_DEPTH/);
});
test("18 replay refuses missing exact quotes instead of forward-filling", () => {
  const store = replayStore();
  store.quotes = store.quotes.filter(row => !(row.contractId === SHORT && row.asOf === EXIT));
  assert.throws(() => E.replayPutRatioEpisode(store, {
    episodeId: "TEST_ONLY_MISSING", longContractId: LONG, shortContractId: SHORT, nShort: 5, entryAsOf: ENTRY, exitAsOf: EXIT
  }, { slippageUsdPerContractPerSide: 0, commissionUsdPerContractPerSide: 0 }), /MISSING_EXACT_QUOTE/);
});
test("19 zero slippage and zero commission remain zero", () => {
  assert.deepEqual(E.computeDynamicCostStrict(3, "0", "0"), {
    valid: true, status: "COST_INPUTS_VALID", slippageUsdPerContractPerSide: 0, commissionUsdPerContractPerSide: 0, costUsd: 0
  });
});
test("20 missing or negative costs block without default substitution", () => {
  assert.equal(E.computeDynamicCostStrict(3, "", 0.65).valid, false);
  assert.equal(E.computeDynamicCostStrict(3, -0.01, 0.65).valid, false);
  assert.equal(E.computeDynamicCostStrict(-1, 0, 0).valid, false);
});
test("21 positive QQQ holding requires its entry basis and current spot", () => {
  const out = E.evaluateLedger(zeroLedger({ qqqShares: 10 }));
  assert.equal(out.status, "BLOCKED_MISSING_POSITION_BASIS");
  assert.ok(out.missingFields.some(field => /qqqSpot/.test(field)));
  assert.ok(out.missingFields.some(field => /qqqEntryPrice/.test(field)));
});
test("22 positive VXX short holding requires its own entry price", () => {
  const out = E.evaluateLedger(zeroLedger({ vxxShortQty: 10, vxxSpot: 20 }));
  assert.equal(out.status, "BLOCKED_MISSING_POSITION_BASIS");
  assert.ok(out.missingFields.some(field => /vxxEntryPrice/.test(field)));
});
test("23 positive option quantity requires entry credit and current mark", () => {
  const out = E.evaluateLedger(zeroLedger({ qqqCallQty: 1, qqqCallEntryCredit: 0.5, qqqCallWidth: 5, qqqCallMultiplier: 100 }));
  assert.equal(out.status, "BLOCKED_MISSING_POSITION_BASIS");
  assert.ok(out.missingFields.some(field => /qqqCallCurrentMark/.test(field)));
});
test("24 external statement NAV mismatch blocks reconciled NAV", () => {
  const out = E.evaluateLedger(zeroLedger({ statementNav: 1200, statementSourceId: "TEST_ONLY_STATEMENT", statementAsOf: "2030-01-02T20:00:00Z", statementFileSha256: HASH }));
  assert.equal(out.status, "BLOCKED_STATEMENT_RECONCILIATION_MISMATCH");
  assert.equal(out.totalNav, null);
  assert.equal(out.conservationDelta, 200);
});
test("25 manual NAV override is not treated as an independent statement", () => {
  const out = E.evaluateLedger(zeroLedger({ navOverride: 1000 }));
  assert.equal(out.status, "UNRECONCILED_NO_STATEMENT");
  assert.equal(out.reconciledWithStatement, false);
  assert.equal(out.manualNavOverride, 1000);
  assert.equal(out.conservationDelta, null);
});
test("26 ledger does not add short-sale proceeds a second time", () => {
  const out = E.evaluateLedger(zeroLedger({
    cashBalance: 1000, qqqShares: 2, qqqEntryPrice: 100, qqqSpot: 110,
    vxxShortQty: 10, vxxEntryPrice: 25, vxxSpot: 20, statementNav: 1020,
    statementSourceId: "TEST_ONLY_STATEMENT", statementAsOf: "2030-01-02T20:00:00Z", statementFileSha256: HASH
  }));
  assert.equal(out.status, "RECONCILED_TO_SOURCE_TAGGED_STATEMENT_NOT_AUTHENTICATED");
  assert.equal(out.totalAssets, 1220);
  assert.equal(out.totalLiabilities, 200);
  assert.equal(out.totalNav, 1020);
  assert.equal(out.vxxUnrealizedPnl, 50);
});
test("36 statement NAV without source identity/hash is not treated as externally reconciled", () => {
  const out = E.evaluateLedger(zeroLedger({ statementNav: 1000 }));
  assert.equal(out.status, "UNRECONCILED_STATEMENT_PROVENANCE_MISSING");
  assert.equal(out.reconciledWithStatement, false);
  assert.equal(out.conservationDelta, null);
  assert.equal(out.totalNav, 1000);
});
test("37 malformed or zero statement NAV is blocked, not relabeled as absent", () => {
  assert.equal(E.evaluateLedger(zeroLedger({ statementNav: "n/a" })).status, "BLOCKED_INVALID_STATEMENT_NAV");
  assert.equal(E.evaluateLedger(zeroLedger({ statementNav: 0 })).status, "BLOCKED_INVALID_STATEMENT_NAV");
});
test("27 invalid option candidate blocks joint stress without fixed $420 fallback", () => {
  const ledger = E.evaluateLedger(zeroLedger({ vxxCallQty: 1, vxxCallEntryCredit: 0.5, vxxCallCurrentMark: 0.4, vxxCallWidth: 5, vxxCallMultiplier: 100 }));
  const out = E.deriveJointStressFromHoldingsStrict(ledger, { qqqCoreShockLossUsd: 0, vxxShortShockLossUsd: 0 }, { vxxCall: { valid: false } });
  assert.equal(out.valid, false);
  assert.equal(out.totalLossUsd, null);
  assert.match(out.status, /BLOCKED_CANDIDATE_LOSS_UNKNOWN/);
});
test("28 state bundle hashes full source, all parameter groups and engine output", async () => {
  const state = {
    inputs: { cashBalance: 1000, qqqShares: 2, qqqSpot: 110 },
    barParams: { barRiskPct: "5", slippage: "0", commission: "0", holdingDay: "DTE7" },
    probParams: { probRegimeFilter: "ALL", probMaxVixInput: "28" },
    floorAndDveParams: { inpFloorBaseB: "100000", dveGainPerUnit: "0" },
    sourceStore: replayStore()
  };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  assert.equal(bundle.schema, E.STATE_SCHEMA);
  for (const key of ["sourceHash", "scenarioHash", "engineOutputHash"]) assert.match(bundle.hashes[key], /^[a-f0-9]{64}$/);
  const staged = await E.verifyAndStageFullStateBundle(JSON.stringify(bundle), { evaluate: deterministicEvaluate });
  assert.equal(staged.ok, true);
  assert.deepEqual(staged.stagedState.barParams, state.barParams);
  assert.deepEqual(staged.stagedState.probParams, state.probParams);
  assert.deepEqual(staged.stagedState.floorAndDveParams, state.floorAndDveParams);
});
test("29 source row alteration without sourceHash update is rejected", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: replayStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  bundle.sourceStore.quotes[0].bid = 3.15;
  await assert.rejects(() => E.verifyAndStageFullStateBundle(bundle, { evaluate: deterministicEvaluate }), /HASH_INTEGRITY_MISMATCH/);
});
test("30 parameter alteration without scenarioHash update is rejected", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: E.createEmptySourceStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  bundle.barParams.risk = 99;
  await assert.rejects(() => E.verifyAndStageFullStateBundle(bundle, { evaluate: deterministicEvaluate }), /HASH_INTEGRITY_MISMATCH/);
});
test("31 embedded engine output alteration without matching hash is rejected", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: E.createEmptySourceStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  bundle.engineOutput.nav = -1;
  await assert.rejects(() => E.verifyAndStageFullStateBundle(bundle, { evaluate: deterministicEvaluate }), /HASH_INTEGRITY_MISMATCH/);
});
test("32 engine output is independently recomputed, not merely re-hashed", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: E.createEmptySourceStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  await assert.rejects(() => E.verifyAndStageFullStateBundle(bundle, {
    evaluate: async s => ({ ...await deterministicEvaluate(s), forged: true })
  }), /OUTPUT_REPRODUCIBILITY_MISMATCH/);
});
test("33 schema and no-broker boundary are checked before state restore", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: E.createEmptySourceStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  await assert.rejects(() => E.verifyAndStageFullStateBundle({ ...bundle, schema: "wrong" }, { evaluate: deterministicEvaluate }), /REJECTED_SCHEMA_MISMATCH/);
  await assert.rejects(() => E.verifyAndStageFullStateBundle({ ...bundle, brokerOrdersAllowed: true }, { evaluate: deterministicEvaluate }), /REJECTED_BROKER_BOUNDARY/);
});
test("34 failed verification does not commit; successful restore commits a staged state", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: E.createEmptySourceStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state);
  let current = { sentinel: "original" }, commits = 0;
  const adapter = { snapshotState: () => current, commitStagedState: staged => { current = staged; commits += 1; }, restorePreviousState: prior => { current = prior; } };
  await assert.rejects(() => E.restoreFullStateBundle({ ...bundle, barParams: { risk: 100 } }, adapter, { evaluate: deterministicEvaluate }), /HASH_INTEGRITY_MISMATCH/);
  assert.equal(commits, 0);
  assert.equal(current.sentinel, "original");
  await E.restoreFullStateBundle(bundle, adapter, { evaluate: deterministicEvaluate });
  assert.equal(commits, 1);
  assert.equal(current.barParams.risk, 3);
  assert.equal(current.brokerOrdersAllowed, undefined);
});
test("35 failed commit restores previous state when adapter supports rollback", async () => {
  const state = { inputs: { cashBalance: 1000 }, barParams: { risk: 3 }, probParams: { filter: "ALL" }, floorAndDveParams: { floor: 100 }, sourceStore: E.createEmptySourceStore() };
  state.engineOutput = await deterministicEvaluate(state);
  const bundle = await E.buildFullStateBundle(state), previous = { sentinel: "original" };
  let current = previous, restored = false;
  await assert.rejects(() => E.restoreFullStateBundle(bundle, {
    snapshotState: () => current,
    commitStagedState: () => { current = { sentinel: "partially changed" }; throw new Error("simulated commit failure"); },
    restorePreviousState: old => { current = old; restored = true; }
  }, { evaluate: deterministicEvaluate }), /simulated commit failure/);
  assert.equal(restored, true);
  assert.equal(current.sentinel, "original");
});
