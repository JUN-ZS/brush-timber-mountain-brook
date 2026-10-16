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
    markAsOf: "2026-10-11T10:00:00Z", markSourceType: "BROKER_LIVE",
    entryEvidence: "BROKER_FILL", entrySourceNote: "fill record",
    markSourceNote: "broker quote", multiplier: 1,
    ...overrides
  };
}

// Strict number parsing keeps blank distinct from explicit zero and rejects coercive inputs.
{
  const blank = P.normalizeRecord(base({ markPrice: "   " }));
  assert.equal(blank.markPrice, null, "whitespace-only mark is EMPTY, never numeric zero");

  const option = base({
    template: "QQQ_CALL_CREDIT", qty: 1, entryPrice: "0.5", markPrice: "0",
    expiry: "2026-11-20", shortStrike: "800", longStrike: "810",
    shortSymbol: "QQQ261120C00800000", longSymbol: "QQQ261120C00810000",
    multiplier: "100", termsVerified: true
  });
  const explicitZero = P.normalizeRecord(option);
  assert.equal(explicitZero.markPrice, 0, "an explicit numeric zero stays zero");
  assert.equal(P.validateRecord(option).ok, true, "zero is not conflated with an empty field");

  const blankOptionMark = { ...option, id: "blank-option-mark", markPrice: "   " };
  const blankSummary = P.summarize([blankOptionMark], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(blankSummary.rows[0].markPrice, null);
  assert.equal(blankSummary.rows[0].unrealizedPnl, null, "blank option mark remains unknown P&L, not an implied zero-debit close");
  assert.equal(blankSummary.incompletePnlCount, 1);

  for (const invalid of ["12USD", "0x10", true, [], {}, Infinity]) {
    assert.equal(P.validateRecord(base({ markPrice: invalid })).ok, false, "invalid numeric input rejected: " + String(invalid));
    assert.equal(P.normalizeList([base({ markPrice: invalid })]).ok, false, "invalid numeric input must block the whole imported register");
  }
}

// Stock long and short P&L use the correct sign and a clear share count.
{
  const qqq = P.summarize([base()], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(qqq.holdings.qqqShares, 10);
  assert.equal(qqq.rows[0].unrealizedPnl, 100);
  assert.equal(qqq.rows[0].pnlStatus, "GROSS UNREALIZED P&L · METADATA COMPLETE");
  assert.equal(qqq.rows[0].markFreshness, "LIVE ≤15M");
  assert.equal(qqq.metadataCompletePnlSubtotal, 100);
  assert.equal(qqq.metadataCompletePnlRows, 1);
  assert.equal(qqq.indicativePnlRows, 0);
  const vxx = P.summarize([base({ template: "VXX_SHORT_STOCK", qty: 20, entryPrice: 20, markPrice: 18, multiplier: 1 })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(vxx.holdings.vxxShortShares, 20);
  assert.equal(vxx.rows[0].unrealizedPnl, 40);
  assert.equal(vxx.metadataCompletePnlSubtotal, 40);

  // A manual estimate remains arithmetically useful, but is separated from the metadata-complete subtotal.
  const estimatedEntry = P.summarize([base({ entryEvidence: "MANUAL_ESTIMATE" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(estimatedEntry.rows[0].unrealizedPnl, 100);
  assert.equal(estimatedEntry.rows[0].pnlStatus, "INDICATIVE · ENTRY UNVERIFIED");
  assert.equal(estimatedEntry.metadataCompletePnlRows, 0);
  assert.equal(estimatedEntry.metadataCompletePnlSubtotal, 0);
  assert.equal(estimatedEntry.indicativePnlRows, 1);
  assert.equal(estimatedEntry.indicativePnlSubtotal, 100);

  // Invalid/old non-empty timestamps fail closed and cannot enter the qualified subtotal.
  const invalidAsOf = P.summarize([base({ markAsOf: "not-a-date" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(invalidAsOf.rows[0].markFreshness, "AS-OF INVALID");
  assert.equal(invalidAsOf.rows[0].pnlStatus, "INDICATIVE · MARK STALE/INVALID");
  assert.equal(invalidAsOf.rows[0].staleMark, true);
  assert.equal(invalidAsOf.staleMarkCount, 1);
  assert.equal(invalidAsOf.metadataCompletePnlRows, 0);
  const staleLive = P.summarize([base({ markAsOf: "2026-10-11T09:30:00Z" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(staleLive.rows[0].markFreshness, "STALE LIVE");
  assert.equal(staleLive.rows[0].pnlStatus, "INDICATIVE · MARK STALE/INVALID");
  assert.equal(staleLive.metadataCompletePnlRows, 0);
  assert.equal(staleLive.indicativePnlRows, 1);

  // Even a small future timestamp must fail closed; clock skew must not make a future quote look current.
  const futureTimestamp = P.summarize([base({ markAsOf: "2026-10-11T10:06:00Z" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(futureTimestamp.rows[0].markFreshness, "FUTURE TIMESTAMP");
  assert.equal(futureTimestamp.rows[0].pnlStatus, "INDICATIVE · MARK STALE/INVALID");
  assert.equal(futureTimestamp.metadataCompletePnlRows, 0);

  const missingTimezone = P.summarize([base({ markAsOf: "2026-10-11T10:00" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(missingTimezone.rows[0].markFreshness, "AS-OF TIMEZONE UNKNOWN");
  assert.equal(missingTimezone.rows[0].pnlStatus, "INDICATIVE · MARK TIMEZONE UNKNOWN");
  assert.equal(missingTimezone.metadataCompletePnlRows, 0);

  const offsetTimestamp = P.summarize([base({ markAsOf: "2026-10-11T10:00:00+08:00" })], {}, Date.parse("2026-10-11T10:05:00+08:00"));
  assert.equal(offsetTimestamp.rows[0].markFreshness, "LIVE ≤15M");
  assert.equal(offsetTimestamp.metadataCompletePnlRows, 1);

  const missingEntryReference = P.summarize([base({ entrySourceNote: "" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(missingEntryReference.rows[0].pnlStatus, "INDICATIVE · ENTRY UNVERIFIED");
  assert.equal(missingEntryReference.metadataCompletePnlRows, 0);

  const missingMarkReference = P.summarize([base({ markSourceNote: "" })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(missingMarkReference.rows[0].pnlStatus, "INDICATIVE · MARK SOURCE UNVERIFIED");
  assert.equal(missingMarkReference.rows[0].markFreshness, "LIVE ≤15M");
  assert.equal(missingMarkReference.staleMarkCount, 0, "a fresh timestamp must not be called stale just because its source reference is missing");
  assert.equal(missingMarkReference.markSourceMetadataIncompleteCount, 1, "source-reference gaps need a separate counter");
  assert.equal(missingMarkReference.metadataCompletePnlRows, 0);
}

// Credit-spread package P&L uses entry credit minus exit debit, then verified/assumed multiplier.
{
  const row = base({
    template: "QQQ_CALL_CREDIT", qty: 3, entryPrice: 0.8, markPrice: 1.3,
    expiry: "2026-11-20", shortStrike: 800, longStrike: 810,
    shortSymbol: "QQQ261120C00800000", longSymbol: "QQQ261120C00810000",
    multiplier: 100, termsVerified: true
  });
  const s = P.summarize([row], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(s.holdings.qqqCallSpreads, 3);
  near(s.rows[0].unrealizedPnl, -150);
  near(s.rows[0].maxLossPerPackage, 920);
  assert.equal(s.blockingKeys.length, 0);

  const estimatedEntry = P.summarize([{ ...row, id: "manual-entry", entryEvidence: "MANUAL_ESTIMATE" }], {}, Date.parse("2026-10-11T10:05:00Z"));
  near(estimatedEntry.rows[0].unrealizedPnl, -150);
  assert.equal(estimatedEntry.rows[0].pnlStatus, "INDICATIVE · ENTRY UNVERIFIED");
}

// Unknown option identity/deliverable blocks sizing only for that strategy.
{
  const s = P.summarize([base({ template: "VXX_CALL_CREDIT", qty: 2, entryPrice: 0.3, markPrice: 0.2 })], {}, Date.parse("2026-10-11T10:05:00Z"));
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
  })], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(s.rows[0].adjustedDetected, true);
  assert.ok(s.blockingKeys.includes("vxxCallSpreads"));

  const adjustedRecord = base({
    id: "adjusted-position", template: "VXX_CALL_CREDIT", qty: 1,
    entryPrice: 0.3, markPrice: 0.2, expiry: "2026-11-20",
    shortStrike: 21, longStrike: 24,
    shortSymbol: "VXX2261120C00021000", longSymbol: "VXX2261120C00024000",
    multiplier: 100, termsVerified: true, deliverableNote: ""
  });
  const noDeliverableNote = P.summarize([adjustedRecord], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(noDeliverableNote.rows[0].termsComplete, false);
  assert.ok(noDeliverableNote.blockingKeys.includes("vxxCallSpreads"));
  const withDeliverableNote = P.summarize([{ ...adjustedRecord, deliverableNote: "Broker contract details verified; deliverable manually transcribed." }], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(withDeliverableNote.rows[0].termsComplete, false, "operator notes do not make an adjusted payoff model valid for sizing");
  assert.ok(withDeliverableNote.blockingKeys.includes("vxxCallSpreads"), "adjusted VXX holdings remain sizing-blocked even when terms are documented");
  assert.equal(withDeliverableNote.rows[0].maxLossPerPackage, null, "standard width × multiplier must not be shown as max loss for adjusted deliverables");
  assert.match(withDeliverableNote.rows[0].pnlStatus, /ADJUSTED PAYOFF MODEL UNSUPPORTED/);
}

// Missing option marks remain missing; missing stock marks may use the explicitly labelled APP snapshot.
{
  const s = P.summarize([
    base({ template: "QQQ_CORE", qty: 2, entryPrice: 100, markPrice: null, markAsOf: "", markSourceType: "UNKNOWN", multiplier: 1 }),
    base({ id: "row-2", template: "QQQ_CALL_CREDIT", qty: 1, entryPrice: 0.7, markPrice: null, markAsOf: "", expiry: "2026-11-20", shortStrike: 110, longStrike: 115, shortSymbol: "QQQ261120C00110000", longSymbol: "QQQ261120C00115000", multiplier: 100, termsVerified: true })
  ], { qqq: 120, vxx: 20, spot_asof: "2026-10-11" }, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(s.rows[0].markPrice, 120);
  assert.equal(s.rows[0].unrealizedPnl, 40);
  assert.equal(s.rows[0].markDerivedFromSnapshot, true);
  assert.equal(s.rows[0].markSourceType, "UNKNOWN", "snapshot-derived mark source must not be falsely labelled EOD/live");
  assert.equal(s.markSourceMetadataIncompleteCount, 1, "snapshot-derived stock mark must expose its missing source class");
  assert.match(s.rows[0].pnlStatus, /SOURCE UNVERIFIED/);
  assert.equal(s.rows[1].unrealizedPnl, null);
  assert.equal(s.incompletePnlCount, 1);
}

// Old live quotes and model marks must not be labelled fresh.
{
  const s = P.summarize([
    base({ markAsOf: "2026-10-11T08:00:00Z", markSourceType: "BROKER_LIVE" }),
    base({ id: "row-2", markAsOf: "2026-10-11T10:00:00Z", markSourceType: "MODEL_ESTIMATE" })
  ], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(s.rows[0].markFreshness, "STALE LIVE");
  assert.equal(s.rows[1].markFreshness, "MODEL ESTIMATE");
  assert.equal(s.staleMarkCount, 2);
  assert.equal(s.markSourceMetadataIncompleteCount, 1, "the model mark has a source-metadata gap while the live mark does not");
}

// Imports/exports are versioned, bounded, and all-or-nothing.
{
  const envelope = P.exportEnvelope([base()], "2026-10-11T10:00:00Z");
  assert.equal(envelope.schema, "QQQ_HYBRID_POSITION_REGISTER_V1");
  assert.equal(P.parseEnvelope(JSON.stringify(envelope)).ok, true);
  assert.equal(P.parseEnvelope(JSON.stringify({ schema: "wrong", positions: [] })).ok, false);
  assert.equal(P.normalizeList([base(), base({ id: "row-1" })]).ok, false);
  assert.equal(P.validateRecord(base({ qty: 1.5 })).ok, false);
  assert.equal(P.validateRecord(base({ markPrice: -1 })).ok, false);
  assert.throws(() => P.exportEnvelope([base({ qty: "not-a-number" })]), /Cannot export invalid position register/);
  assert.equal(P.exportEnvelope([]).positions.length, 0, "an intentionally empty register remains exportable");
  const whitespaceImport = P.parseEnvelope(JSON.stringify({
    schema: "QQQ_HYBRID_POSITION_REGISTER_V1",
    positions: [base({ template: "QQQ_CALL_CREDIT", qty: 1, entryPrice: 0.5, markPrice: "  ", expiry: "2026-11-20", shortStrike: 800, longStrike: 810, shortSymbol: "QQQ261120C00800000", longSymbol: "QQQ261120C00810000", multiplier: 100, termsVerified: true })]
  }));
  assert.equal(whitespaceImport.ok, true, "blank optional mark is accepted only as unknown, never coerced to 0");
  assert.equal(whitespaceImport.positions[0].markPrice, null);
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
  const wrongExpiry = P.summarize([{ ...good, id: "wrong-expiry", shortSymbol: "QQQ261218C00800000" }], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.ok(wrongExpiry.blockingKeys.includes("qqqCallSpreads"));
  assert.equal(wrongExpiry.rows[0].identityComplete, false);
  const wrongStrike = P.summarize([{ ...good, id: "wrong-strike", longSymbol: "QQQ261120C00805000" }], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.ok(wrongStrike.blockingKeys.includes("qqqCallSpreads"));
  const wrongRoot = P.summarize([{ ...good, id: "wrong-root", shortSymbol: "SPY261120C00800000" }], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.ok(wrongRoot.blockingKeys.includes("qqqCallSpreads"));
  assert.equal(P.validateRecord({ ...good, shortStrike: 810, longStrike: 800 }).ok, false);
}


// A blank option multiplier must not silently normalize to the standard 100-unit assumption.
{
  const goodOption = base({
    id: "blank-multiplier", template: "QQQ_CALL_CREDIT", qty: 1,
    entryPrice: 0.5, markPrice: 0.4,
    expiry: "2026-11-20", shortStrike: 800, longStrike: 810,
    shortSymbol: "QQQ261120C00800000", longSymbol: "QQQ261120C00810000",
    multiplier: 100, termsVerified: true, deliverableNote: "Broker contract details checked by operator"
  });
  const normalizedBlank = P.normalizeRecord({ ...goodOption, multiplier: "" });
  assert.equal(normalizedBlank.multiplier, null, "a blank multiplier must remain unknown");
  const validation = P.validateRecord({ ...goodOption, multiplier: null });
  assert.equal(validation.ok, false, "blank multiplier must fail validation");
  assert.match(validation.errors.join(" "), /explicitly entered and greater than zero/);

  const summary = P.summarize([{ ...goodOption, multiplier: null }], {}, Date.parse("2026-10-11T10:05:00Z"));
  assert.equal(summary.count, 0, "invalid imported rows must not enter the ledger aggregate");
  assert.equal(summary.knownPnlRows, 0, "a missing multiplier must never produce option P&L");
  assert.match(summary.error || "", /multiplier must be explicitly entered and greater than zero/);

  const imported = P.parseEnvelope(JSON.stringify({
    schema: "QQQ_HYBRID_POSITION_REGISTER_V1",
    positions: [{ ...goodOption, multiplier: null }]
  }));
  assert.equal(imported.ok, false, "imports with missing option multiplier must fail closed");
}

// Shared management meter uses the same dimensions and side-aware price semantics.
{
  const meterSandbox = { module: { exports: {} } };
  vm.runInNewContext(fs.readFileSync(require.resolve("../position_management.js"), "utf8"), meterSandbox, { filename: "position_management.js" });
  const M = meterSandbox.module.exports;
  const baseRow = {
    id: "managed-qqq", template: "QQQ_CORE", kind: "STOCK", side: "LONG", qty: 10, multiplier: 1,
    entryDate: "2026-10-01", entryPrice: 100, markPrice: 110, stopMarkPrice: 95, targetMarkPrice: 115,
    riskBudgetUsd: null, profitTargetR: null, maxHoldDays: 10, expiryReviewDte: null,
    unrealizedPnl: 100, markFreshness: "LIVE ≤15M", staleMark: false,
    pnlStatus: "GROSS UNREALIZED P&L · METADATA COMPLETE"
  };
  const gate = { blocked: false, riskOff: false, state: "CARRY" };
  const threeDays = M.evaluate(baseRow, { nav: 100000, today: "2026-10-04", marketState: gate });
  assert.equal(threeDays.elapsedCalendarDays, 3);
  near(threeDays.riskBudgetUsd, 50);
  near(threeDays.pnlR, 2);
  near(threeDays.pnlPctNav, 0.1);
  near(threeDays.pnlPerCalendarDay, 100 / 3);
  near(threeDays.rPerCalendarDay, 2 / 3);
  near(threeDays.riskToStopUsd, 150);
  near(threeDays.targetRewardUsd, 50);
  assert.equal(threeDays.action, "MONITOR · NO RULE TRIGGERED", "fast positive P&L alone must not force a trim");

  const tenDays = M.evaluate({ ...baseRow, unrealizedPnl: 1000, markPrice: 115 }, { nav: 100000, today: "2026-10-11", marketState: gate });
  assert.equal(tenDays.elapsedCalendarDays, 10);
  near(tenDays.pnlPerCalendarDay, 100);
  assert.equal(tenDays.timeLimitReached, true);
  assert.equal(tenDays.action, "TIME LIMIT REACHED · HUMAN REVIEW");

  const targetR = M.evaluate({ ...baseRow, riskBudgetUsd: 1000, profitTargetR: 1, unrealizedPnl: 1000 }, { nav: 100000, today: "2026-10-04", marketState: gate });
  assert.equal(targetR.profitTargetRReached, true);
  assert.equal(targetR.action, "PROFIT REVIEW THRESHOLD REACHED");

  const stopHit = M.evaluate({ ...baseRow, markPrice: 94, unrealizedPnl: -60 }, { nav: 100000, today: "2026-10-04", marketState: gate });
  assert.equal(stopHit.stopBreached, true);
  assert.equal(stopHit.action, "STOP MARK BREACHED · HUMAN REVIEW");

  const staleStop = M.evaluate({ ...baseRow, markFreshness: "STALE LIVE", staleMark: true }, { nav: 100000, today: "2026-10-04", marketState: gate });
  assert.equal(staleStop.stopBreached, false);
  assert.equal(staleStop.action, "PENDING · FRESH VERIFIED MARK REQUIRED");

  const credit = M.evaluate({
    ...baseRow, entryDate: "2026-10-10", maxHoldDays: 30,
    template: "QQQ_CALL_CREDIT", kind: "CREDIT_VERTICAL", side: "CREDIT",
    entryPrice: 0.8, markPrice: 1.2, stopMarkPrice: 1.4, targetMarkPrice: 0.4,
    qty: 2, multiplier: 100, riskBudgetUsd: null, maxLossPerPackage: 420,
    termsComplete: true, expiry: "2026-10-20", expiryReviewDte: 5,
    unrealizedPnl: -80
  }, { nav: 100000, today: "2026-10-14", marketState: gate });
  near(credit.riskBudgetUsd, 120);
  near(credit.pnlR, -80 / 120);
  near(credit.riskToStopUsd, 40);
  near(credit.targetRewardUsd, 160);
  near(credit.rewardRiskRatio, 4);
  assert.equal(credit.dte, 6);
  assert.equal(credit.action, "MONITOR · NO RULE TRIGGERED");

  const vxxShock = M.evaluate({
    ...baseRow, template: "VXX_SHORT_STOCK", kind: "STOCK", side: "SHORT",
    entryPrice: 20, markPrice: 17, stopMarkPrice: 22, targetMarkPrice: 15,
    qty: 100, multiplier: 1, riskBudgetUsd: 200, unrealizedPnl: 300
  }, { nav: 100000, today: "2026-10-04", marketState: { blocked: false, riskOff: true, state: "SHOCK" } });
  assert.equal(vxxShock.action, "REGIME RISK REVIEW · HUMAN REVIEW");

  const incomplete = M.evaluate({ ...baseRow, riskBudgetUsd: 100, stopMarkPrice: null, maxHoldDays: null }, { nav: 100000, today: "2026-10-04", marketState: gate });
  assert.equal(incomplete.action, "PLAN INCOMPLETE · STOP MARK NOT SET");

  assert.equal(P.validateRecord(base({ stopMarkPrice: 110 })).ok, false, "long stock stop above entry is rejected");
  assert.equal(P.validateRecord(base({ riskBudgetUsd: 0 })).ok, false, "zero risk budget is not a valid denominator");
}


// Long-horizon roadmap uses an explicit starting baseline; future deposits never become today's cash.
{
  const roadmapSandbox = { module: { exports: {} } };
  vm.runInNewContext(fs.readFileSync(require.resolve("../deployment_roadmap.js"), "utf8"), roadmapSandbox, { filename: "deployment_roadmap.js" });
  const R = roadmapSandbox.module.exports;
  const marketCarry = { blocked: false, allowNew: true, action: "HOLD", state: "CARRY" };
  const pending = R.evaluate({ baseCapitalUsd:null,startDate:"",horizonMonths:120,monthlyContributionUsd:500,currentNavUsd:100000,currentCashUsd:90000,today:"2026-10-14",market:marketCarry });
  assert.equal(pending.status,"BASELINE_PENDING");
  assert.equal(pending.floorUsd,null);
  const threeMonths = R.evaluate({ baseCapitalUsd:100000,startDate:"2026-07-14",horizonMonths:120,monthlyContributionUsd:500,currentNavUsd:100000,currentCashUsd:90000,today:"2026-10-14",market:marketCarry });
  assert.equal(threeMonths.status,"CARRY_HUMAN_REVIEW");
  assert.equal(threeMonths.elapsedMonths,3);
  near(threeMonths.floorUsd,2500);
  near(threeMonths.floorGapUsd,97500);
  near(threeMonths.plannedFutureContributionsUsd,58500);
  assert.equal(threeMonths.contributionsCountedInCurrentCash,false);
  assert.equal(threeMonths.forecastedCagr,null);
  const floorBreach = R.evaluate({ baseCapitalUsd:100000,startDate:"2016-10-14",horizonMonths:120,monthlyContributionUsd:0,currentNavUsd:95000,currentCashUsd:1000,today:"2026-10-14",market:marketCarry });
  assert.equal(floorBreach.elapsedMonths,120);
  near(floorBreach.floorUsd,100000);
  assert.equal(floorBreach.status,"FLOOR_BREACH");
  assert.match(floorBreach.nextAction,/不會自動 SELL/);
  const blocked=R.evaluate({baseCapitalUsd:100000,startDate:"2026-09-14",horizonMonths:120,monthlyContributionUsd:0,currentNavUsd:100000,currentCashUsd:100000,today:"2026-10-14",market:{blocked:true,allowNew:false,action:"BLOCK",state:"UNKNOWN"}});
  assert.equal(blocked.status,"WAIT_FOR_DATA");
  const shock=R.evaluate({baseCapitalUsd:100000,startDate:"2026-09-14",horizonMonths:120,monthlyContributionUsd:0,currentNavUsd:100000,currentCashUsd:100000,today:"2026-10-14",market:{blocked:false,allowNew:false,action:"REDUCE",state:"SHOCK"}});
  assert.equal(shock.status,"DEFENSIVE_REVIEW");
  const future=R.evaluate({baseCapitalUsd:100000,startDate:"2026-12-01",horizonMonths:120,monthlyContributionUsd:0,currentNavUsd:100000,currentCashUsd:100000,today:"2026-10-14",market:marketCarry});
  assert.equal(future.status,"BASELINE_PENDING");
}
console.log("QQQ HYBRID POSITION REGISTER: shared position + deployment roadmap PASS");

