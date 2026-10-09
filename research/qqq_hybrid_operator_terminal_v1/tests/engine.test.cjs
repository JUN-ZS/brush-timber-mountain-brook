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
  assert.equal(r.totalOptionRiskPool, 500);
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

// Research ratio strategies do not get a fake hard max-loss capacity.
{
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, ratioCallRiskPct: 1 },
    holdings: { ratioCalls: 3 },
    permissions: { ratioCalls: true }
  }));
  const x = row(r, "ratioCalls");
  assert.equal(x.capacity, null);
  assert.equal(x.target, 3);
  assert.equal(x.status, "PENDING");
  assert.equal(x.riskSource, "UNBOUNDED_TAIL");
  assert.equal(x.maxLossIsHardCap, false);
}

// A manually entered stress-loss estimate is marked stress-only, not a guaranteed hard cap.
{
  const r = E.calculatePortfolio(base({
    sizing: { ...base().sizing, ratioCallRiskPct: 1 },
    manualRiskPerUnit: { ratioCalls: 500 },
    permissions: { ratioCalls: true }
  }));
  const x = row(r, "ratioCalls");
  assert.equal(x.capacity, 2); // floor($1,000 / $500)
  assert.equal(x.status, "STRESS_ONLY");
  assert.equal(x.maxLossIsHardCap, false);
}

// Long options use debit × 100; covered calls cannot exceed QQQ shares / 100.
{
  const r = E.calculatePortfolio(base({
    holdings: { qqqShares: 450, coveredCalls: 10 },
    sizing: { ...base().sizing, longCallRiskPct: 1, coveredCallRiskPct: 1 },
    candidates: {
      qqqLongCall: { ask: 2.5, source: "FIXTURE" },
      qqqCall: { shortBid: 0.5, credit: 0.2, source: "FIXTURE" }
    },
    permissions: { longCalls: true, coveredCalls: true }
  }));
  assert.equal(row(r, "longCalls").riskPerUnit, 250);
  assert.equal(row(r, "longCalls").capacity, 4);
  assert.equal(row(r, "coveredCalls").capacity, 4);
  assert.equal(row(r, "coveredCalls").target, 4);
  assert.equal(row(r, "coveredCalls").action, "REDUCE");
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
    { expiration: expiry, days: 42, strike: 105, bid: 2.0, ask: 2.1, delta: 0.16 },
    { expiration: expiry, days: 42, strike: 107, bid: 1.2, ask: 1.4, delta: 0.10 },
    { expiration: expiry, days: 42, strike: 110, bid: 0.4, ask: 0.6, delta: 0.05 }
  ];
  const call = E.findCreditVertical({ calls }, 100, "call", 45, 0.16, "2026-10-09");
  assert.equal(call.shortStrike, 105);
  assert.equal(call.longStrike, 107);
  assert.equal(call.credit, 0.6);
  assert.equal(call.maxLossPerSpread, 140);
  assert.equal(call.expiry, "2026-11-20");

  const puts = [
    { expiration: expiry, days: 42, strike: 95, bid: 2.0, ask: 2.2, delta: -0.16 },
    { expiration: expiry, days: 42, strike: 92.5, bid: 1.1, ask: 1.3, delta: -0.10 },
    { expiration: expiry, days: 42, strike: 90, bid: 0.5, ask: 0.7, delta: -0.05 }
  ];
  const put = E.findCreditVertical({ puts }, 100, "put", 45, 0.16, "2026-10-09");
  assert.equal(put.shortStrike, 95);
  assert.equal(put.longStrike, 92.5);
  assert.equal(put.credit, 0.7);
  assert.equal(put.maxLossPerSpread, 180);
  assert.equal(put.expiry, "2026-11-20");
}

console.log("QQQ HYBRID OPERATOR TERMINAL ENGINE: 16 TEST GROUPS PASS");
