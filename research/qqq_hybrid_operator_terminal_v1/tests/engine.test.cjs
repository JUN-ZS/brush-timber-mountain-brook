const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(require.resolve("../engine.js"), "utf8"), sandbox, { filename: "engine.js" });
const E = sandbox.module.exports;

function snap(overrides = {}) {
  return {
    qqq: 100,
    vxx: 20,
    vix: 15,
    m1: 20,
    m2: 22,
    term_asof: "2026-10-09",
    spot_asof: "2026-10-09",
    today: "2026-10-09",
    term_source: "FIXTURE",
    ...overrides
  };
}

function base(overrides = {}) {
  return {
    market: snap(),
    nav: 100000,
    cashPool: 100000,
    sizing: {
      qqqCorePct: 42,
      vxxNormalPct: 18,
      vxxHighPct: 10,
      totalOptionRiskPct: 3.2,
      qqqCallRiskPct: 1.2,
      vxxCallRiskPct: 2,
      vxxPutRiskPct: 0,
      qqqBullPutRiskPct: 0,
      vixHigh: 28,
      termSafe: 5,
      maxTermAgeDays: 4
    },
    holdings: {},
    candidates: {},
    permissions: {},
    manualRiskPerUnit: {},
    ratioCampaign: {},
    ...overrides
  };
}

function row(result, key) {
  const value = result.rows.find(x => x.key === key);
  assert.ok(value, "missing result row " + key);
  return value;
}

// Reverse sizing of 1,000 QQQ shares: 42% × $100,000 / $100 = 420 shares.
{
  const r = E.calculatePortfolio(base({ holdings: { qqqShares: 1000 } }));
  const x = row(r, "qqqShares");
  assert.equal(r.market.state, "CARRY");
  assert.equal(x.capacity, 420);
  assert.equal(x.target, 420);
  assert.equal(x.delta, -580);
  assert.equal(x.action, "REDUCE");
}

// VXX short-share cap in normal carry: 18% NAV / $20 = 900 shares.
{
  const r = E.calculatePortfolio(base({ holdings: { vxxShortShares: 1000 } }));
  const x = row(r, "vxxShortShares");
  assert.equal(x.capacity, 900);
  assert.equal(x.target, 900);
  assert.equal(x.delta, -100);
  assert.equal(x.action, "REDUCE");
}

// High VIX but contango: cap VXX short stock at 10% NAV and disable seller options.
{
  const r = E.calculatePortfolio(base({
    market: snap({ vix: 31 }),
    holdings: { vxxShortShares: 1000, vxxCallSpreads: 4 },
    candidates: { vxxCall: { width: 5, credit: 0.8, shortBid: 1, source: "FIXTURE" } }
  }));
  assert.equal(r.market.state, "PRE-SHOCK");
  assert.equal(row(r, "vxxShortShares").capacity, 500);
  assert.equal(row(r, "vxxShortShares").target, 500);
  assert.equal(row(r, "vxxCallSpreads").target, 0);
  assert.equal(row(r, "vxxCallSpreads").action, "REDUCE");
}

// Backwardation sets VXX short stock target to zero.
{
  const r = E.calculatePortfolio(base({
    market: snap({ m1: 22, m2: 20 }),
    holdings: { vxxShortShares: 1000 }
  }));
  assert.equal(r.market.state, "PRE-SHOCK");
  assert.equal(row(r, "vxxShortShares").capacity, 0);
  assert.equal(row(r, "vxxShortShares").target, 0);
  assert.equal(row(r, "vxxShortShares").delta, -1000);
}

// Defined-risk credit vertical uses width minus credit, never credit by itself.
{
  const r = E.calculatePortfolio(base({
    candidates: { qqqCall: { width: 5, credit: 0.8, shortBid: 1.1, source: "FIXTURE" } }
  }));
  const x = row(r, "qqqCallSpreads");
  assert.equal(x.riskPerUnit, 420);
  assert.equal(x.capacity, 2); // floor($1,200 / $420)
  assert.equal(x.target, 2);
  assert.equal(x.maxLossIsHardCap, true);
  assert.ok(r.optionRiskReservedAtTargets <= r.totalOptionRiskPool);
}

// Global option risk pool limits a contract count even when the leg budget is larger.
{
  const r = E.calculatePortfolio(base({
    cashPool: 500,
    candidates: { qqqCall: { width: 5, credit: 0.8, source: "FIXTURE" } }
  }));
  assert.equal(r.totalOptionRiskPool, 450);
  assert.equal(row(r, "qqqCallSpreads").capacity, 1);
}

// A missing current chain candidate leaves an existing position PENDING, never invented as zero.
{
  const r = E.calculatePortfolio(base({ holdings: { qqqCallSpreads: 7 } }));
  const x = row(r, "qqqCallSpreads");
  assert.equal(x.capacity, null);
  assert.equal(x.target, 7);
  assert.equal(x.action, "PENDING");
  assert.equal(x.status, "PENDING");
}

// In HOLD/weakening, excess still trims; undersized positions do not get new entries.
{
  const r = E.calculatePortfolio(base({
    market: snap({ m1: 20, m2: 20.5 }),
    holdings: { qqqShares: 1000, vxxCallSpreads: 1 },
    candidates: { vxxCall: { width: 5, credit: 0.8, shortBid: 1, source: "FIXTURE" } }
  }));
  assert.equal(r.market.state, "WEAKENING");
  assert.equal(row(r, "qqqShares").target, 420);
  assert.equal(row(r, "qqqShares").action, "REDUCE");
  assert.equal(row(r, "vxxCallSpreads").target, 1);
  assert.equal(row(r, "vxxCallSpreads").action, "HOLD");
}

// Missing/stale market data blocks sizing changes instead of producing a made-up target.
{
  const r = E.calculatePortfolio(base({
    market: snap({ term_asof: "2026-09-01" }),
    holdings: { qqqShares: 1000, qqqCallSpreads: 4 }
  }));
  assert.equal(r.ok, false);
  assert.equal(r.market.blocked, true);
  assert.equal(row(r, "qqqShares").target, 1000);
  assert.equal(row(r, "qqqCallSpreads").target, 4);
  assert.equal(row(r, "qqqCallSpreads").action, "BLOCKED");
}

// Generic Ratio Put remains stress-only: no fake hard max-loss capacity is allowed.
{
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, ratioPutRiskPct: 1 },
    holdings: { ratioPuts: 3 },
    permissions: { ratioPuts: true }
  }));
  const x = row(r, "ratioPuts");
  assert.equal(x.capacity, null);
  assert.equal(x.target, 3);
  assert.equal(x.status, "OUTSIDE_MAIN_BUDGET");
  assert.equal(x.riskSource, "UNBOUNDED_TAIL");
  assert.equal(x.action, "OUTSIDE_BUDGET");
  assert.equal(x.maxLossIsHardCap, false);
}

// A manually entered ratio-put stress estimate is marked stress-only, not a hard cap.
{
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, ratioPutRiskPct: 1 },
    manualRiskPerUnit: { ratioPuts: 500 },
    permissions: { ratioPuts: true }
  }));
  const x = row(r, "ratioPuts");
  assert.equal(x.capacity, null);
  assert.equal(x.status, "OUTSIDE_MAIN_BUDGET");
  assert.equal(x.riskPerUnit, 500);
  assert.equal(x.riskSource, "MANUAL_STRESS_ESTIMATE");
  assert.equal(x.action, "OUTSIDE_BUDGET");
  assert.equal(x.maxLossIsHardCap, false);
}

// Long options and covered calls remain inspection-only; even a valid quote cannot change the main plan.
{
  const r = E.calculatePortfolio(base({
    holdings: { qqqShares: 450, coveredCalls: 10, longCalls: 3 },
    sizing: { ...base().sizing, longCallRiskPct: 1, coveredCallRiskPct: 1 },
    candidates: {
      qqqLongCall: { ask: 2.5, source: "FIXTURE" },
      qqqCoveredCall: { type: "coveredCall", shortBid: 0.5, source: "FIXTURE" }
    },
    permissions: { longCalls: true, coveredCalls: true }
  }));
  assert.equal(row(r, "longCalls").riskPerUnit, 250);
  assert.equal(row(r, "longCalls").capacity, null);
  assert.equal(row(r, "longCalls").target, 3);
  assert.equal(row(r, "longCalls").status, "OUTSIDE_MAIN_BUDGET");
  assert.equal(row(r, "coveredCalls").capacity, null);
  assert.equal(row(r, "coveredCalls").target, 10);
  assert.equal(row(r, "coveredCalls").action, "OUTSIDE_BUDGET");
}

// Legacy 10:N hedge is per campaign and explicitly does not claim a hard loss cap.
{
  const r = E.calculatePortfolio(base({
    ratioCampaign: {
      enabled: true, currentFarShort: 1000, currentNearLong: 1000,
      nShort: 10, farDelta: 0.08, nearDelta: 0.5, coverageMult: 1.5, maxStack: 5
    }
  }));
  assert.equal(r.ratioCampaign.targetFar, 10);
  assert.equal(r.ratioCampaign.farDelta, -990);
  assert.equal(r.ratioCampaign.targetNear, 3);
  assert.equal(r.ratioCampaign.nearDelta, -997);
  assert.equal(r.ratioCampaign.noHardLossCap, true);
}

// The read-only policy boundary is explicit.
{
  const r = E.calculatePortfolio(base());
  assert.equal(r.boundary.brokerOrders, false);
  assert.equal(r.boundary.automaticMutation, false);
  assert.equal(r.boundary.missingCandidateNeverFabricated, true);
}

// Invalid allocation percentages must block resizing and preserve current positions.
{
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, qqqCorePct: 101 },
    holdings: { qqqShares: 1000, vxxShortShares: 1000 }
  }));
  assert.equal(r.ok, false);
  assert.equal(row(r, "qqqShares").target, 1000);
  assert.equal(row(r, "qqqShares").status, "INVALID_PERCENT");
  assert.match(row(r, "qqqShares").reason, /between 0 and 100/);
}

// Quote-backed call and put vertical candidates keep exact expiry/wing direction and defined max loss.
{
  const expiry = Date.parse("2026-11-20T00:00:00Z") / 1000;
  const calls = [
    { expiration: expiry, days: 42, strike: 105, bid: 2.0, ask: 2.1, delta: 0.16, contractSymbol: "QQQ_TEST_SHORT" },
    { expiration: expiry, days: 42, strike: 107, bid: 1.2, ask: 1.4, delta: 0.10, contractSymbol: "QQQ_TEST_WING" },
    { expiration: expiry, days: 42, strike: 110, bid: 0.4, ask: 0.6, delta: 0.05, contractSymbol: "QQQ_TEST_FAR_WING" }
  ];
  const call = E.findCreditVertical({ calls }, 100, "call", 45, 0.16, "2026-10-09");
  assert.equal(call.shortStrike, 105);
  assert.equal(call.longStrike, 107);
  assert.ok(Math.abs(call.credit - 0.6) < 1e-9);
  assert.ok(Math.abs(call.maxLossPerSpread - 140) < 1e-9);
  assert.equal(call.expiry, "2026-11-20");
  assert.equal(call.shortContractSymbol, "QQQ_TEST_SHORT");
  assert.equal(call.longContractSymbol, "QQQ_TEST_WING");
  assert.equal(call.shortBid, 2.0);
  assert.equal(call.shortAsk, 2.1);
  assert.equal(call.longBid, 1.2);
  assert.equal(call.longAsk, 1.4);
  assert.equal(call.multiplierAssumption, 100);
  assert.equal(call.multiplierVerified, false);
  assert.equal(call.shortQuoteQuality, "TIGHT");
  assert.equal(call.longQuoteQuality, "WATCH");
  assert.ok(Math.abs(call.shortQuoteWidthPctMid - (0.1 / 2.05 * 100)) < 1e-9);
  assert.ok(Math.abs(call.longQuoteWidthPctMid - (0.2 / 1.3 * 100)) < 1e-9);
  assert.equal(E.quoteQuality({bid: 1, ask: 1.5}).quality, "WIDE");
  assert.equal(E.quoteQuality({bid: 1, ask: null}).quality, "UNKNOWN");

  const puts = [
    { expiration: expiry, days: 42, strike: 95, bid: 2.0, ask: 2.2, delta: -0.16 },
    { expiration: expiry, days: 42, strike: 92.5, bid: 1.1, ask: 1.3, delta: -0.10 },
    { expiration: expiry, days: 42, strike: 90, bid: 0.5, ask: 0.7, delta: -0.05 }
  ];
  const put = E.findCreditVertical({ puts }, 100, "put", 45, 0.16, "2026-10-09");
  assert.equal(put.shortStrike, 95);
  assert.equal(put.longStrike, 92.5);
  assert.ok(Math.abs(put.credit - 0.7) < 1e-9);
  assert.ok(Math.abs(put.maxLossPerSpread - 180) < 1e-9);
  assert.equal(put.expiry, "2026-11-20");
}

// Legacy hedge raises near-long coverage when delta/distance/gamma risk score breaches thresholds.
{
  const r = E.calculatePortfolio(base({
    ratioCampaign: {
      enabled: true, currentFarShort: 10, currentNearLong: 1,
      nShort: 10, farDelta: 0.12, nearDelta: 0.5, coverageMult: 1.5, maxStack: 5,
      farDistancePct: 3, gammaRel: 1.6, deltaJump: 0.025
    }
  }));
  assert.equal(r.ratioCampaign.dScore, 5);
  assert.equal(r.ratioCampaign.xScore, 4);
  assert.equal(r.ratioCampaign.gScore, 3);
  assert.ok(Math.abs(r.ratioCampaign.riskScore - 4.3) < 1e-9);
  assert.equal(r.ratioCampaign.stackAdjustment, 2);
  assert.equal(r.ratioCampaign.targetNear, 5);
  assert.equal(r.ratioCampaign.noHardLossCap, true);
}

// Covered-call candidate detection remains testable, but covered calls are outside the primary budget.
{
  const expiry = Date.parse("2026-11-20T00:00:00Z") / 1000;
  const calls = [
    { expiration: expiry, days: 42, strike: 105, bid: 2.0, ask: 2.1, delta: 0.16 },
    { expiration: expiry, days: 42, strike: 107, bid: 1.2, ask: 1.4, delta: 0.10 }
  ];
  const candidate = E.findShortCall({ calls }, 100, 45, 0.16, "2026-10-09");
  assert.equal(candidate.type, "coveredCall");
  assert.equal(candidate.shortBid, 2.0);
  assert.equal(candidate.strike, 105);
  const r = E.calculatePortfolio(base({
    holdings: { qqqShares: 450, coveredCalls: 10 },
    sizing: { ...base().sizing, coveredCallRiskPct: 1 },
    candidates: { qqqCoveredCall: candidate },
    permissions: { coveredCalls: true }
  }));
  assert.equal(row(r, "coveredCalls").capacity, null);
  assert.equal(row(r, "coveredCalls").target, 10);
  assert.equal(row(r, "coveredCalls").delta, 0);
  assert.equal(row(r, "coveredCalls").action, "OUTSIDE_BUDGET");
  assert.equal(row(r, "coveredCalls").maxLossIsHardCap, false);
}

// Fresh $100,000 capital plan conserves cash across reserve, shares, margin and option risk.
{
  const r = E.calculatePortfolio(base());
  assert.equal(r.cashReserveUsd, 10000);
  assert.equal(r.totalOptionRiskPool, 3200);
  assert.equal(row(r, "qqqShares").target, 420);
  assert.equal(r.qqqAdditionalCapitalUsd, 42000);
  assert.equal(row(r, "vxxShortShares").target, 900);
  assert.equal(r.vxxAdditionalMarginUsd, 27000);
  assert.equal(r.plannedCapitalRequiredUsd, 82200);
  assert.equal(r.remainingUnallocatedCashUsd, 17800);
  assert.ok(r.plannedCapitalRequiredUsd <= r.cashPool);
}

// A constrained $50,000 cash pool must not spend the same dollar twice.
{
  const r = E.calculatePortfolio(base({ cashPool: 50000 }));
  assert.equal(r.cashReserveUsd, 5000);
  assert.equal(r.totalOptionRiskPool, 3200);
  assert.equal(row(r, "qqqShares").target, 418);
  assert.equal(r.qqqAdditionalCapitalUsd, 41800);
  assert.equal(row(r, "vxxShortShares").target, 0);
  assert.equal(r.vxxAdditionalMarginUsd, 0);
  assert.equal(r.plannedCapitalRequiredUsd, 50000);
  assert.equal(r.remainingUnallocatedCashUsd, 0);
}

// Existing QQQ holdings use only incremental cash for a new target.
{
  const r = E.calculatePortfolio(base({ cashPool: 60000, holdings: { qqqShares: 200 } }));
  assert.equal(row(r, "qqqShares").target, 420);
  assert.equal(r.qqqAdditionalCapitalUsd, 22000);
  assert.ok(r.plannedCapitalRequiredUsd <= 60000);
}


// The option budgets are weights against one pool, not independent full-NAV entitlements.
// 3% + 3% requested weights are proportionally reduced to fit the $3,200 total pool.
{
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, totalOptionRiskPct: 3.2, qqqCallRiskPct: 3, vxxCallRiskPct: 3 },
    candidates: {
      qqqCall: { width: 5, credit: 4, source: "FIXTURE" }, // $100 max loss per spread
      vxxCall: { width: 10, credit: 8, source: "FIXTURE" } // $200 max loss per spread
    }
  }));
  assert.ok(Math.abs(r.riskScaleFactor - (3200 / 6000)) < 1e-9);
  assert.ok(Math.abs(row(r, "qqqCallSpreads").allocatedRiskBudgetUsd - 1600) < 1e-9);
  assert.ok(Math.abs(row(r, "vxxCallSpreads").allocatedRiskBudgetUsd - 1600) < 1e-9);
  assert.equal(row(r, "qqqCallSpreads").capacity, 16);
  assert.equal(row(r, "vxxCallSpreads").capacity, 8);
  assert.equal(r.optionRiskReservedAtTargets, 3200);
}

// User-uploaded 2026-11-20 screenshot chain sizes the two call-credit legs; VXX put is intentionally excluded from the primary plan.
{
  const fixture = JSON.parse(fs.readFileSync(require.resolve("./fixtures/user_uploaded_option_chain_2026-11-20.json"), "utf8"));
  assert.equal(fixture.source, "USER_UPLOADED_SCREENSHOT");
  assert.equal(fixture.expiration, "2026-11-20");
  assert.equal(fixture.instruments.VXX.right, "call");
  assert.equal(fixture.unavailable.vxxPuts.present, false);

  const qqqQuotes = fixture.instruments.QQQ.quotes;
  const qqqShort = qqqQuotes.find(q => q.strike === 799);
  const qqqWing = qqqQuotes.find(q => q.strike === 810);
  const vxxQuotes = fixture.instruments.VXX.quotes;
  const vxxShort = vxxQuotes.find(q => q.strike === 21);
  const vxxWing = vxxQuotes.find(q => q.strike === 24);
  const qqqCandidate = {
    width: Math.abs(qqqWing.strike - qqqShort.strike),
    credit: qqqShort.bid - qqqWing.ask,
    shortBid: qqqShort.bid, longAsk: qqqWing.ask,
    shortStrike: qqqShort.strike, longStrike: qqqWing.strike,
    expiry: fixture.expiration, source: fixture.source + ":QQQ_CALLS"
  };
  const vxxCandidate = {
    width: Math.abs(vxxWing.strike - vxxShort.strike),
    credit: vxxShort.bid - vxxWing.ask,
    shortBid: vxxShort.bid, longAsk: vxxWing.ask,
    shortStrike: vxxShort.strike, longStrike: vxxWing.strike,
    expiry: fixture.expiration, source: fixture.source + ":VXX_CALLS"
  };
  const r = E.calculatePortfolio(base({
    market: snap({
      qqq: fixture.exampleMarketInputsFromConversation.qqqSpot,
      vxx: fixture.exampleMarketInputsFromConversation.vxxSpot,
      vix: fixture.exampleMarketInputsFromConversation.vix
    }),
    sizing: {
      ...base().sizing, totalOptionRiskPct: 3.2,
      qqqCallRiskPct: 1.2, vxxCallRiskPct: 2, vxxPutRiskPct: 1
    },
    candidates: { qqqCall: qqqCandidate, vxxCall: vxxCandidate },
    permissions: { vxxPutSpreads: true }
  }));
  assert.ok(Math.abs(qqqCandidate.credit - 1.27) < 1e-9);
  assert.equal(row(r, "qqqCallSpreads").riskPerUnit, 973);
  assert.equal(row(r, "qqqCallSpreads").capacity, 1);
  assert.equal(row(r, "qqqCallSpreads").candidateSource, fixture.source + ":QQQ_CALLS");
  assert.ok(Math.abs(vxxCandidate.credit - 0.24) < 1e-9);
  assert.equal(row(r, "vxxCallSpreads").riskPerUnit, 276);
  assert.equal(row(r, "vxxCallSpreads").capacity, 7);
  assert.equal(row(r, "vxxCallSpreads").candidateSource, fixture.source + ":VXX_CALLS");
  assert.equal(r.totalOptionRiskPool, 3200);
  assert.equal(r.totalRequestedRiskBudgetsUsd, 3200); // Only QQQ/VXX call-credit requests share the primary pool.
  assert.equal(r.riskScaleFactor, 1);
  assert.equal(r.optionRiskReservedAtTargets, 2905);
  assert.equal(r.remainingRiskPool, 295);

  // Keep exposure allocation separate from estimated opening credit and express both on the same $100k NAV basis.
  // These are quote-side scenario estimates from the user-uploaded screenshot fixture, not confirmed fills or realized P&L.
  const qqqCapacityCreditUsd = qqqCandidate.credit * 100 * row(r, "qqqCallSpreads").capacity;
  const vxxCapacityCreditUsd = vxxCandidate.credit * 100 * row(r, "vxxCallSpreads").capacity;
  assert.ok(Math.abs(qqqCapacityCreditUsd - 127) < 1e-9);
  assert.ok(Math.abs(vxxCapacityCreditUsd - 168) < 1e-9);
  assert.ok(Math.abs(qqqCapacityCreditUsd / r.nav * 100 - 0.127) < 1e-9);
  assert.ok(Math.abs(vxxCapacityCreditUsd / r.nav * 100 - 0.168) < 1e-9);
  assert.ok(Math.abs(r.optionRiskReservedAtTargets / r.nav * 100 - 2.905) < 1e-9);
  assert.ok(Math.abs(r.totalOptionRiskPool / r.nav * 100 - 3.2) < 1e-9);
  assert.ok(Math.abs(r.optionRiskReservedAtTargets / r.totalOptionRiskPool * 100 - 90.78125) < 1e-9);

  assert.equal(row(r, "vxxPutSpreads").status, "OUTSIDE_MAIN_BUDGET");
  assert.equal(row(r, "vxxPutSpreads").capacity, null);
  assert.equal(row(r, "vxxPutSpreads").action, "OUTSIDE_BUDGET");
  assert.equal(row(r, "vxxPutSpreads").allocatedRiskBudgetUsd, 0);
  assert.equal(row(r, "vxxPutSpreads").targetRiskReserveUsd, 0);
}

// Hub/debit/research structures remain visible but never join or alter the main seller-option budget.
{
  const r = E.calculatePortfolio(base({
    sizing: {
      ...base().sizing, totalOptionRiskPct: 3.2,
      qqqCallRiskPct: 1.2, vxxCallRiskPct: 2,
      ratioCallRiskPct: 2, hubShockPutRiskPct: 1,
      longCallRiskPct: 1, ratioPutRiskPct: 1
    },
    holdings: { ratioCalls: 2, hubShockPuts: 1, longCalls: 3, ratioPuts: 2 },
    candidates: {
      qqqCall: { width: 5, credit: 4, source: "FIXTURE" },
      vxxCall: { width: 10, credit: 8, source: "FIXTURE" },
      hubRatioCall: { hubPackage: true, ready: true, riskPerUnit: 600, debitUsd: 200, maxUnits: 10, gatePass: true, source: "HUB_FIXTURE" },
      hubShockPut: { hubPackage: true, ready: true, riskPerUnit: 200, debitUsd: 200, maxUnits: 100, gatePass: false, source: "HUB_FIXTURE" },
      qqqLongCall: { ask: 2.5, source: "FIXTURE" }
    },
    permissions: { ratioCalls: true, hubShockPuts: true, longCalls: true, ratioPuts: true },
    manualRiskPerUnit: { ratioPuts: 500 }
  }));
  assert.equal(r.totalRequestedRiskBudgetsUsd, 3200);
  assert.equal(r.riskScaleFactor, 1);
  assert.equal(r.optionRiskReservedAtTargets, 3200);
  for (const key of ["ratioCalls", "hubShockPuts", "longCalls", "ratioPuts"]) {
    assert.equal(row(r, key).status, "OUTSIDE_MAIN_BUDGET");
    assert.equal(row(r, key).capacity, null);
    assert.equal(row(r, key).action, "OUTSIDE_BUDGET");
    assert.equal(row(r, key).target, row(r, key).current);
    assert.equal(row(r, key).allocatedRiskBudgetUsd, 0);
    assert.equal(row(r, key).targetRiskReserveUsd, 0);
  }
}

// Similar strategy labels have independent candidate keys so budgets do not duplicate one quote.
{
  const bearCall = E.OPTION_STRATEGIES.find(s => s.key === "qqqBearCallSpreads");
  const farCall = E.OPTION_STRATEGIES.find(s => s.key === "qqqCallSpreads");
  const protectivePut = E.OPTION_STRATEGIES.find(s => s.key === "protectivePuts");
  const longPut = E.OPTION_STRATEGIES.find(s => s.key === "longPuts");
  assert.equal(farCall.candidateKey, "qqqCall");
  assert.equal(bearCall.candidateKey, "qqqBearCall");
  assert.notEqual(farCall.candidateKey, bearCall.candidateKey);
  assert.equal(protectivePut.candidateKey, "qqqProtectivePut");
  assert.equal(longPut.candidateKey, "qqqLongPut");
  assert.notEqual(protectivePut.candidateKey, longPut.candidateKey);
}



// Adjusted VXX roots must block main-budget capacity instead of assuming a standard 100-unit deliverable.
{
  const expiry = Date.parse("2026-11-20T00:00:00Z") / 1000;
  const vxx = {
    symbol: "VXX",
    calls: [
      { expiration: expiry, days: 42, strike: 21, bid: 0.58, ask: 0.72, delta: 0.16, contractSymbol: "VXX2261120C00021000" },
      { expiration: expiry, days: 42, strike: 24, bid: 0.24, ask: 0.34, delta: 0.08, contractSymbol: "VXX2261120C00024000" },
      { expiration: expiry, days: 42, strike: 26, bid: 0.12, ask: 0.18, delta: 0.04, contractSymbol: "VXX2261120C00026000" }
    ]
  };
  assert.equal(E.isAdjustedVxxContractSymbol("VXX2261120C00021000"), true);
  assert.equal(E.isAdjustedVxxContractSymbol("VXX1261120C00021000"), true);
  assert.equal(E.isAdjustedVxxContractSymbol("VXX261120C00021000"), false);
  const candidate = E.findCreditVertical(vxx, 20, "call", 45, 0.16, "2026-10-09");
  assert.ok(candidate);
  assert.equal(candidate.contractTermsStatus, "ADJUSTED_DELIVERABLE_BLOCKED");
  assert.equal(candidate.candidateStatus, "ADJUSTED_CONTRACT_BLOCKED");
  const r = E.calculatePortfolio(base({ candidates: { vxxCall: candidate } }));
  const x = row(r, "vxxCallSpreads");
  assert.equal(x.capacity, null);
  assert.equal(x.action, "BLOCKED");
  assert.equal(x.status, "BLOCKED_CONTRACT");
  assert.match(x.reason, /does not model the contract's non-standard exercise payoff/);

  const riskOff = E.calculatePortfolio(base({
    market: snap({ vix: 31 }),
    holdings: { vxxCallSpreads: 1 },
    candidates: { vxxCall: candidate }
  }));
  const riskOffRow = row(riskOff, "vxxCallSpreads");
  assert.equal(riskOffRow.capacity, null);
  assert.equal(riskOffRow.action, "BLOCKED");
  assert.equal(riskOffRow.target, 1, "do not claim a computable reduction quantity when contract terms are unknown");
}


// Position register hard gate: held option terms unknown means current quantity is known,
// but a safe strategy target / risk reserve is not asserted.
{
  const candidate = { width: 5, credit: 0.8, shortBid: 1.1, source: "FIXTURE" };
  const r = E.calculatePortfolio(base({
    holdings: { qqqCallSpreads: 3 },
    candidates: { qqqCall: candidate },
    positionRegister: { useForSizing: true, blockingKeys: ["qqqCallSpreads"] }
  }));
  const x = row(r, "qqqCallSpreads");
  assert.equal(x.capacity, null);
  assert.equal(x.target, 3);
  assert.equal(x.delta, 0);
  assert.equal(x.action, "BLOCKED");
  assert.equal(x.status, "BLOCKED_POSITION_TERMS");
  assert.equal(x.riskPerUnit, null);
  assert.match(x.reason, /unverified/);
}

// A held-position terms block must be excluded before proportional shared-risk allocation.
{
  const candidate = { width: 5, credit: 0.8, shortBid: 1.1, source: "FIXTURE" };
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, totalOptionRiskPct: 3.2, qqqCallRiskPct: 2, vxxCallRiskPct: 2 },
    holdings: { qqqCallSpreads: 3 },
    candidates: { qqqCall: candidate, vxxCall: candidate },
    positionRegister: { useForSizing: true, blockingKeys: ["qqqCallSpreads"] }
  }));
  const qqq = row(r, "qqqCallSpreads");
  const vxx = row(r, "vxxCallSpreads");
  assert.equal(qqq.capacity, null);
  assert.equal(qqq.target, 3);
  assert.equal(qqq.action, "BLOCKED");
  assert.equal(qqq.status, "BLOCKED_POSITION_TERMS");
  assert.equal(r.totalRequestedRiskBudgetsUsd, 2000, "blocked QQQ request must not enter the shared risk allocator");
  assert.equal(r.riskScaleFactor, 1, "the eligible VXX budget must not be diluted by a blocked QQQ row");
  assert.equal(vxx.capacity, 4);
  assert.equal(vxx.target, 4);
  assert.equal(vxx.allocatedRiskBudgetUsd, 2000);
  assert.equal(r.remainingRiskPool, 1520);
  assert.equal(r.optionRiskReservedAtTargets, 1680);
}

console.log("QQQ HYBRID OPERATOR ENGINE: 29 TEST GROUPS PASS");

