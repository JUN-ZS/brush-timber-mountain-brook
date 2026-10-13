const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(require.resolve("../hub_research_pack.js"), "utf8"), sandbox, { filename: "hub_research_pack.js" });
const H = sandbox.module.exports;

function ratioBase(overrides = {}) {
  return {
    mode: "ratio-dynamic-v2",
    nav: 100000,
    budgetUsd: 500,
    spot: 100,
    atmStrike: 100, atmAsk: 6,
    shortStrike: 110, shortBid: 2,
    wingStrike: 120, wingAsk: 0.8,
    requestedN: 2,
    maxN: 4,
    currentN: 0,
    currentShorts: 0,
    currentWings: 0,
    currentShortDelta: 0.20,
    packagePnlUsd: 0,
    ...overrides
  };
}

// The 1xNxN ratio's risk is evaluated from the package terminal payoff,
// not the received premium alone.
{
  const legs = [
    { name: "ATM long call", right: "call", side: "BUY", qty: 1, strike: 100, price: 6 },
    { name: "OTM short calls", right: "call", side: "SELL", qty: 2, strike: 110, price: 2 },
    { name: "Far OTM long wings", right: "call", side: "BUY", qty: 2, strike: 120, price: 0.8 }
  ];
  const x = H.terminalMaxLoss(legs, 100);
  assert.equal(x.ready, true);
  assert.equal(x.debitUsd, 360);
  assert.equal(x.riskUsd, 360);
  assert.equal(x.source, "ENTRY_BID_ASK_TERMINAL_PAYOFF_PROXY");
}

// Dynamic-N entry chooses the largest N in its permitted set that fits the
// entry terminal max-loss budget; N=3 already exceeds this $500 fixture.
{
  const r = H.calculateRatioCall(ratioBase());
  assert.equal(r.ready, true);
  assert.equal(r.maxAffordableN, 2);
  assert.equal(r.entryN, 2);
  assert.equal(r.riskUsd, 360);
  assert.equal(r.action, "NEW ENTRY ELIGIBLE / REVIEW");
  assert.equal(r.targetShorts, 0);
}

// HARVEST50 must not infer that a pair is profitable when current exit quotes
// are absent; price fields are not silently defaulted to zero.
{
  const r = H.calculateRatioCall(ratioBase({
    mode: "ratio-harvest50",
    requestedN: 2,
    currentN: 2, currentShorts: 2, currentWings: 2,
    approachTouched: true, nextDayReversal: true
  }));
  assert.equal(r.ready, true);
  assert.equal(r.harvestedPairs, 0);
  assert.equal(r.action, "HOLD / WAIT FOR HARVEST TRIGGER");
}

// Dynamic-N V2 follows the frozen +0.15-delta reduction step.
{
  const r = H.calculateRatioCall(ratioBase({
    budgetUsd: 500,
    currentN: 2, currentShorts: 2, currentWings: 2,
    currentShortDelta: 0.50
  }));
  assert.equal(r.entryN, 2);
  assert.equal(r.targetPairs, 0);
  assert.equal(r.targetShorts, 0);
  assert.equal(r.targetWings, 0);
  assert.equal(r.action, "REDUCE SHORT+WING PAIRS");
}

// Fresh-Pair V7 needs its frozen N=2 base campaign and checks the risk of
// the next pair before adding it.
{
  const r = H.calculateRatioCall(ratioBase({
    mode: "ratio-fresh-v7",
    budgetUsd: 1300,
    currentN: 2, currentShorts: 2, currentWings: 2,
    currentShortDelta: 0.10,
    lowDeltaStreak: 2,
    sessionsSinceChange: 5
  }));
  assert.equal(r.entryN, 2);
  assert.equal(r.targetPairs, 3);
  assert.equal(r.targetShorts, 3);
  assert.equal(r.targetWings, 3);
  assert.equal(r.action, "ADD ONE FRESH SHORT+WING PAIR");
}

// State-Adaptive geometry preserves +1/-2/+2 calls plus +1/-1 put spread.
// Fixture risk is an entry-terminal-loss proxy from all five observed legs.
{
  const r = H.calculateStateAdaptive({
    spot: 100,
    atmStrike: 100, atmAsk: 6,
    shortStrike: 110, shortBid: 2,
    wingStrike: 120, wingAsk: 0.8,
    longPutStrike: 95, longPutAsk: 3,
    shortPutStrike: 90, shortPutBid: 1.2,
    budgetUsd: 1200,
    wave: 0, prevClose: 111, anchorClose: 100, atr20: 10
  });
  assert.equal(r.ready, true);
  assert.equal(r.riskUsd, 540);
  assert.equal(r.maxPackages, 2);
  assert.equal(r.waveTrigger, true);
  assert.equal(r.nextWave, 1);
  assert.equal(r.nextCallShortDelta, 0.30);
  assert.equal(r.nextPutShortAbsDelta, 0.05);
}

// Staggered Stack uses the same frozen per-vintage structure, but separately
// budgets only 1/2/4 concurrent vintages.
{
  const r = H.calculateStaggered({
    spot: 100,
    atmStrike: 100, atmAsk: 6,
    shortStrike: 110, shortBid: 2,
    wingStrike: 120, wingAsk: 0.8,
    longPutStrike: 95, longPutAsk: 3,
    shortPutStrike: 90, shortPutBid: 1.2,
    budgetUsd: 1200, layerCap: 4, currentLayers: 0
  });
  assert.equal(r.ready, true);
  assert.equal(r.riskUsd, 540);
  assert.equal(r.targetLayers, 2);
  assert.equal(r.reserveAtTargetUsd, 1080);
  assert.equal(r.remainingRiskUsd, 120);
}

// SHOCK-GATED debit vertical only enters after the frozen shock trigger.
// Net credit is rejected because the selected Hub node is a debit spread.
{
  const base = {
    spot: 100,
    longPutStrike: 95, longPutAsk: 3,
    shortPutStrike: 90, shortPutBid: 1.2,
    budgetUsd: 1000
  };
  const waiting = H.calculateShockGatedPut({ ...base, drawdown252Pct: -2, return5dPct: -1 });
  assert.equal(waiting.ready, true);
  assert.equal(waiting.riskUsd, 180);
  assert.equal(waiting.targetContracts, 0);
  assert.equal(waiting.status, "WAITING_FOR_SHOCK_GATE");

  const trigger = H.calculateShockGatedPut({ ...base, drawdown252Pct: -8, return5dPct: 0 });
  assert.equal(trigger.triggered, true);
  assert.equal(trigger.maxContracts, 5);
  assert.equal(trigger.targetContracts, 5);
  assert.equal(trigger.status, "SHOCK_GATE_PASS");

  const credit = H.calculateShockGatedPut({ ...base, longPutAsk: 1, shortPutBid: 2, drawdown252Pct: -10 });
  assert.equal(credit.ready, false);
  assert.match(credit.error, /must be positive/);
}

// Risk-WIN Bank keeps risk rights separate from deployable cash/collateral;
// ISOLATED later wins do not replenish the seed.
{
  const blocked = H.calculateRiskBank({
    mode: "isolated", seedWinUsd: 750, laterLossesUsd: 400,
    laterNetPnlUsd: 10000, candidateRiskUsd: 400
  });
  assert.equal(blocked.availableRiskRightsUsd, 350);
  assert.equal(blocked.eligible, false);
  assert.equal(blocked.isCash, false);
  assert.equal(blocked.isCollateral, false);

  const pass = H.calculateRiskBank({
    mode: "isolated", seedWinUsd: 750, laterLossesUsd: 400,
    laterNetPnlUsd: 10000, candidateRiskUsd: 300
  });
  assert.equal(pass.availableRiskRightsUsd, 350);
  assert.equal(pass.eligible, true);

  const comparator = H.calculateRiskBank({
    mode: "replenish-comparator", seedWinUsd: 750, laterLossesUsd: 400,
    laterNetPnlUsd: 200, candidateRiskUsd: 500
  });
  assert.equal(comparator.availableRiskRightsUsd, 950);
  assert.equal(comparator.mode, "REPLENISH_COMPARATOR");
}

// Chain leg selector builds the researched five-leg geometry and correctly
// marks when it used provider Delta rather than a BS estimate.
{
  const chain = {
    expiry: "2026-11-20",
    calls: [
      { strike: 100, bid: 5.9, ask: 6, delta: 0.50 },
      { strike: 110, bid: 2, ask: 2.1, delta: 0.20 },
      { strike: 120, bid: 0.7, ask: 0.8, delta: 0.08 }
    ],
    puts: [
      { strike: 95, bid: 2.8, ask: 3, delta: -0.25 },
      { strike: 90, bid: 1.1, ask: 1.2, delta: -0.10 }
    ]
  };
  const c = H.chooseChainLegs(chain, 100, "2026-10-09", 45);
  assert.equal(c.ready, true);
  assert.equal(c.expiry, "2026-11-20");
  assert.equal(c.atm.strike, 100);
  assert.equal(c.short.strike, 110);
  assert.equal(c.wing.strike, 120);
  assert.equal(c.longPut.strike, 95);
  assert.equal(c.shortPut.strike, 90);
  assert.equal(c.deltaSource, "PROVIDER_DELTA");
}


// Main desk → Hub bridge: copy capital once, estimate Hybrid reservation conservatively,
// and fail closed when the plan or any held option-risk unit is unknown.
{
  const Bridge = require("../hub_context_bridge.js");
  const now = Date.parse("2026-10-13T10:00:00Z");
  const plan = {
    generatedAt: new Date(now).toISOString(),
    input: {
      nav: 100000, cashPool: 80000,
      sizing: { cashReservePct: 10, totalOptionRiskPct: 3.2 },
      market: { qqq: 500, spot_asof: "2026-10-13", term_asof: "2026-10-13", term_source: "V3_READ_ONLY" }
    },
    result: {
      ok: true,
      market: { status: "FRESH", state: "CARRY", blocked: false },
      rows: [
        { key: "qqqCallSpreads", current: 1, target: 1, riskPerUnit: 973 },
        { key: "vxxCallSpreads", current: 2, target: 3, riskPerUnit: 276 }
      ]
    }
  };
  const packet = Bridge.contextFromPrimaryPlan(plan);
  assert.equal(packet.schema, "QQQ_HYBRID_PRIMARY_CONTEXT_V1");
  assert.equal(packet.riskReservationReady, true);
  assert.equal(packet.baseRiskReservedUsd, 1801, "reservation uses max(current,target) per primary leg");
  assert.equal(packet.market.qqqSpot, 500);
  const valid = Bridge.validate(packet, now);
  assert.equal(valid.ok, true);
  assert.equal(valid.context.capital.nav, 100000);
  assert.equal(valid.context.baseRiskReservedUsd, 1801);
  assert.equal(valid.context.riskReservationBasis, "MAX_CURRENT_OR_TARGET_QTY_X_CURRENT_CANDIDATE_MAX_LOSS; ESTIMATE_NOT_CONFIRMED_FILL");

  const heldRiskUnknown = Bridge.contextFromPrimaryPlan({
    ...plan,
    result: { ...plan.result, rows: [
      { key: "qqqCallSpreads", current: 1, target: 1, riskPerUnit: null },
      { key: "vxxCallSpreads", current: 0, target: 0, riskPerUnit: null }
    ]}
  });
  assert.equal(heldRiskUnknown.riskReservationReady, false);
  assert.equal(heldRiskUnknown.baseRiskReservedUsd, null);
  assert.equal(Bridge.validate(heldRiskUnknown, now).ok, true, "unknown source context may carry capital but must preserve a null risk reservation");

  const blockedPlan = Bridge.contextFromPrimaryPlan({
    ...plan,
    result: { ...plan.result, ok: false, market: { status: "STALE", state: "DATA STALE", blocked: true } }
  });
  assert.equal(blockedPlan.primarySizingReady, false);
  assert.equal(blockedPlan.riskReservationReady, false);
  assert.equal(blockedPlan.baseRiskReservedUsd, null);

  assert.equal(Bridge.validate({ ...packet, generatedAt: "2026-10-13T10:00:00" }, now).ok, false, "context timestamp must include timezone");
  assert.equal(Bridge.validate({ ...packet, generatedAt: new Date(now - Bridge.MAX_AGE_MS - 1).toISOString() }, now).ok, false, "stale context cannot be imported");
  assert.equal(Bridge.validate({ ...packet, capital: { ...packet.capital, totalOptionRiskPct: 101 } }, now).ok, false);
  assert.equal(Bridge.validate({ ...packet, riskReservationReady: false, baseRiskReservedUsd: 0 }, now).ok, false, "unknown risk reservation must never be represented as zero");

  const mainHtml = fs.readFileSync(require("path").join(__dirname, "../index.html"), "utf8");
  const mainApp = fs.readFileSync(require("path").join(__dirname, "../app.js"), "utf8");
  const hubHtml = fs.readFileSync(require("path").join(__dirname, "../hub_research_pack.html"), "utf8");
  const hubUi = fs.readFileSync(require("path").join(__dirname, "../hub_research_pack_ui.js"), "utf8");
  assert.ok(mainHtml.includes('id="syncHubBtn"'));
  assert.ok(mainHtml.indexOf('src="hub_context_bridge.js"') < mainHtml.indexOf('src="app.js"'), "main bridge script must load before app.js");
  assert.ok(mainApp.includes("contextFromPrimaryPlan(lastPlan)"));
  assert.ok(mainApp.includes("localStorage.setItem(bridge.STORAGE_KEY"));
  assert.ok(hubHtml.includes('id="importPrimaryContextBtn"'));
  assert.ok(hubHtml.includes('id="baseRiskReservedUsd"') && !/id="baseRiskReservedUsd"[^>]*value="0"/.test(hubHtml), "unknown Hybrid reservation must not default to zero");
  assert.ok(hubHtml.indexOf('src="hub_context_bridge.js"') < hubHtml.indexOf('src="hub_research_pack_ui.js"'), "Hub bridge script must load before the UI");
  assert.ok(hubUi.includes("function importPrimaryContext()"));
  assert.ok(hubUi.includes("budget.remainingPool === null"), "unknown base reservation must block Hub calculations");
}

console.log("HUB RESEARCH OPTION PACK: 11 TEST GROUPS PASS");
