"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(require.resolve("../position_ledger.js"), "utf8"), sandbox, { filename: "position_ledger.js" });
const P = sandbox.module.exports;

function near(actual, expected, tolerance = 1e-8) { assert.ok(Math.abs(actual - expected) < tolerance, "expected " + expected + ", got " + actual); }

function base(overrides = {}) {
  return {
    id: "row-1", template: "QQQ_CORE", qty: 10,
    entryDate: "2026-09-01", entryPrice: 100, markPrice: 110,
    markAsOf: "2026-10-11T10:00", markSourceType: "BROKER_LIVE",
    entryEvidence: "BROKER_FILL", entrySourceNote: "fill record",
    markSourceNote: "broker quote", multiplier: 1,
    ...overrides
  };
}

// Stock long and short P&L use the correct sign and a clear share count.
{
  const qqq = P.summarize([base()], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(qqq.holdings.qqqShares, 10);
  assert.equal(qqq.rows[0].unrealizedPnl, 100);
  assert.equal(qqq.rows[0].pnlStatus, "GROSS UNREALIZED P&L");
  assert.equal(qqq.rows[0].markFreshness, "LIVE ≤15M");
  assert.equal(qqq.qualifiedPnlSubtotal, 100);
  assert.equal(qqq.qualifiedPnlRows, 1);
  assert.equal(qqq.indicativePnlRows, 0);
  const vxx = P.summarize([base({ template: "VXX_SHORT_STOCK", qty: 20, entryPrice: 20, markPrice: 18, multiplier: 1 })], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(vxx.holdings.vxxShortShares, 20);
  assert.equal(vxx.rows[0].unrealizedPnl, 40);
  assert.equal(vxx.qualifiedPnlSubtotal, 40);

  // A manual estimate remains arithmetically useful, but is separated from the evidence-qualified subtotal.
  const estimatedEntry = P.summarize([base({ entryEvidence: "MANUAL_ESTIMATE" })], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(estimatedEntry.rows[0].unrealizedPnl, 100);
  assert.equal(estimatedEntry.rows[0].pnlStatus, "INDICATIVE · ENTRY UNVERIFIED");
  assert.equal(estimatedEntry.qualifiedPnlRows, 0);
  assert.equal(estimatedEntry.qualifiedPnlSubtotal, 0);
  assert.equal(estimatedEntry.indicativePnlRows, 1);
  assert.equal(estimatedEntry.indicativePnlSubtotal, 100);

  // Invalid/old non-empty timestamps fail closed and cannot enter the qualified subtotal.
  const invalidAsOf = P.summarize([base({ markAsOf: "not-a-date" })], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(invalidAsOf.rows[0].markFreshness, "AS-OF INVALID");
  assert.equal(invalidAsOf.rows[0].pnlStatus, "INDICATIVE · MARK STALE/INVALID");
  assert.equal(invalidAsOf.rows[0].staleMark, true);
  assert.equal(invalidAsOf.staleMarkCount, 1);
  assert.equal(invalidAsOf.qualifiedPnlRows, 0);
  const staleLive = P.summarize([base({ markAsOf: "2026-10-11T09:30" })], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(staleLive.rows[0].markFreshness, "STALE LIVE");
  assert.equal(staleLive.rows[0].pnlStatus, "INDICATIVE · MARK STALE/INVALID");
  assert.equal(staleLive.qualifiedPnlRows, 0);
  assert.equal(staleLive.indicativePnlRows, 1);
}

// Credit-spread package P&L uses entry credit minus exit debit, then verified/assumed multiplier.
{
  const row = base({
    template: "QQQ_CALL_CREDIT", qty: 3, entryPrice: 0.8, markPrice: 1.3,
    expiry: "2026-11-20", shortStrike: 800, longStrike: 810,
    shortSymbol: "QQQ261120C00800000", longSymbol: "QQQ261120C00810000",
    multiplier: 100, termsVerified: true
  });
  const s = P.summarize([row], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(s.holdings.qqqCallSpreads, 3);
  near(s.rows[0].unrealizedPnl, -150);
  near(s.rows[0].maxLossPerPackage, 920);
  assert.equal(s.blockingKeys.length, 0);

  const estimatedEntry = P.summarize([{ ...row, id: "manual-entry", entryEvidence: "MANUAL_ESTIMATE" }], {}, Date.parse("2026-10-11T10:05"));
  near(estimatedEntry.rows[0].unrealizedPnl, -150);
  assert.equal(estimatedEntry.rows[0].pnlStatus, "INDICATIVE · ENTRY UNVERIFIED");
}

// Unknown option identity/deliverable blocks sizing only for that strategy.
{
  const s = P.summarize([base({ template: "VXX_CALL_CREDIT", qty: 2, entryPrice: 0.3, markPrice: 0.2 })], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(s.holdings.vxxCallSpreads, 2);
  assert.deepEqual(JSON.parse(JSON.stringify(s.blockingKeys)), ["vxxCallSpreads"]);
  assert.equal(s.termBlockedCount, 1);
  assert.match(s.rows[0].pnlStatus, /CONTRACT IDENTITY UNVERIFIED/);
}

// Adjusted roots are identified and surfaced even if the record owner has not verified terms.
{
  assert.equal(P.isAdjustedVxxSymbol("VXX2261120C00021000"), true);
  assert.equal(P.isAdjustedVxxSymbol("VXX1261120C00021000"), true);
  assert.equal(P.isAdjustedVxxSymbol("VXX261120C00021000"), false);
  const s = P.summarize([base({
    template: "VXX_CALL_CREDIT", qty: 1,
    expiry: "2026-11-20", shortStrike: 21, longStrike: 24,
    shortSymbol: "VXX2261120C00021000", longSymbol: "VXX2261120C00024000",
    multiplier: 100, termsVerified: false
  })], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(s.rows[0].adjustedDetected, true);
  assert.ok(s.blockingKeys.includes("vxxCallSpreads"));

  const adjustedRecord = base({
    id: "adjusted-position", template: "VXX_CALL_CREDIT", qty: 1,
    entryPrice: 0.3, markPrice: 0.2, expiry: "2026-11-20",
    shortStrike: 21, longStrike: 24,
    shortSymbol: "VXX2261120C00021000", longSymbol: "VXX2261120C00024000",
    multiplier: 100, termsVerified: true, deliverableNote: ""
  });
  const noDeliverableNote = P.summarize([adjustedRecord], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(noDeliverableNote.rows[0].termsComplete, false);
  assert.ok(noDeliverableNote.blockingKeys.includes("vxxCallSpreads"));
  const withDeliverableNote = P.summarize([{ ...adjustedRecord, deliverableNote: "Broker contract details verified; deliverable manually transcribed." }], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(withDeliverableNote.rows[0].termsComplete, true);
  assert.equal(withDeliverableNote.blockingKeys.length, 0);
}

// Missing option marks remain missing; missing stock marks may use the explicitly labelled APP snapshot.
{
  const s = P.summarize([
    base({ template: "QQQ_CORE", qty: 2, entryPrice: 100, markPrice: null, markAsOf: "", markSourceType: "UNKNOWN", multiplier: 1 }),
    base({ id: "row-2", template: "QQQ_CALL_CREDIT", qty: 1, entryPrice: 0.7, markPrice: null, markAsOf: "", expiry: "2026-11-20", shortStrike: 110, longStrike: 115, shortSymbol: "QQQ261120C00110000", longSymbol: "QQQ261120C00115000", multiplier: 100, termsVerified: true })
  ], { qqq: 120, vxx: 20, spot_asof: "2026-10-11" }, Date.parse("2026-10-11T10:05"));
  assert.equal(s.rows[0].markPrice, 120);
  assert.equal(s.rows[0].unrealizedPnl, 40);
  assert.equal(s.rows[0].markDerivedFromSnapshot, true);
  assert.equal(s.rows[0].markSourceType, "UNKNOWN", "snapshot-derived mark source must not be falsely labelled EOD/live");
  assert.match(s.rows[0].pnlStatus, /SOURCE UNVERIFIED/);
  assert.equal(s.rows[1].unrealizedPnl, null);
  assert.equal(s.incompletePnlCount, 1);
}

// Old live quotes and model marks must not be labelled fresh.
{
  const s = P.summarize([
    base({ markAsOf: "2026-10-11T08:00", markSourceType: "BROKER_LIVE" }),
    base({ id: "row-2", markAsOf: "2026-10-11T10:00", markSourceType: "MODEL_ESTIMATE" })
  ], {}, Date.parse("2026-10-11T10:05"));
  assert.equal(s.rows[0].markFreshness, "STALE LIVE");
  assert.equal(s.rows[1].markFreshness, "MODEL ESTIMATE");
  assert.equal(s.staleMarkCount, 2);
}

// Imports are versioned, bounded, and all-or-nothing.
{
  const envelope = P.exportEnvelope([base()], "2026-10-11T10:00:00Z");
  assert.equal(envelope.schema, "QQQ_HYBRID_POSITION_REGISTER_V1");
  assert.equal(P.parseEnvelope(JSON.stringify(envelope)).ok, true);
  assert.equal(P.parseEnvelope(JSON.stringify({ schema: "wrong", positions: [] })).ok, false);
  assert.equal(P.normalizeList([base(), base({ id: "row-1" })]).ok, false);
  assert.equal(P.validateRecord(base({ qty: 1.5 })).ok, false);
  assert.equal(P.validateRecord(base({ markPrice: -1 })).ok, false);
}


// Exact OCC symbols must agree with expiry, right and strike inputs; reversed call-credit legs are rejected.
{
  const good = base({
    id: "verified-call", template: "QQQ_CALL_CREDIT", qty: 1,
    entryPrice: 0.5, markPrice: 0.4,
    expiry: "2026-11-20", shortStrike: 800, longStrike: 810,
    shortSymbol: "QQQ261120C00800000", longSymbol: "QQQ261120C00810000",
    multiplier: 100, termsVerified: true, deliverableNote: "Standard 100 QQQ shares"
  });
  assert.equal(P.parseOccOptionSymbol(good.shortSymbol).strike, 800);
  assert.equal(P.parseOccOptionSymbol(good.shortSymbol).expiry, "2026-11-20");
  assert.equal(P.validateRecord(good).ok, true);
  const wrongExpiry = P.summarize([{ ...good, id: "wrong-expiry", shortSymbol: "QQQ261218C00800000" }], {}, Date.parse("2026-10-11T10:05"));
  assert.ok(wrongExpiry.blockingKeys.includes("qqqCallSpreads"));
  assert.equal(wrongExpiry.rows[0].identityComplete, false);
  const wrongStrike = P.summarize([{ ...good, id: "wrong-strike", longSymbol: "QQQ261120C00805000" }], {}, Date.parse("2026-10-11T10:05"));
  assert.ok(wrongStrike.blockingKeys.includes("qqqCallSpreads"));
  const wrongRoot = P.summarize([{ ...good, id: "wrong-root", shortSymbol: "SPY261120C00800000" }], {}, Date.parse("2026-10-11T10:05"));
  assert.ok(wrongRoot.blockingKeys.includes("qqqCallSpreads"));
  assert.equal(P.validateRecord({ ...good, shortStrike: 810, longStrike: 800 }).ok, false);
}

console.log("QQQ HYBRID POSITION REGISTER: 8 TEST GROUPS PASS");
