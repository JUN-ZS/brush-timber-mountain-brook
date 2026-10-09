const assert = require("node:assert/strict");
const H = require("../hub_research_pack.js");

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
  const legs = H.ratioCallLegs(ratioBase(), 2);
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

console.log("HUB RESEARCH OPTION PACK: 9 TEST GROUPS PASS");
