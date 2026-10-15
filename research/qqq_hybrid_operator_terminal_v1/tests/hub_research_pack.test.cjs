const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(require.resolve("../hub_research_pack.js"), "utf8"), sandbox, { filename: "hub_research_pack.js" });
const H = sandbox.module.exports;

{
  const oneMillion = H.calculateNavExitReferences(1000000);
  assert.equal(oneMillion.ready, true);
  assert.equal(oneMillion.targets[0].percentNav, 0.5);
  assert.equal(oneMillion.targets[0].usd, 5000);
  assert.equal(oneMillion.targets[1].percentNav, 1);
  assert.equal(oneMillion.targets[1].usd, 10000);
  assert.equal(oneMillion.targets[2].percentNav, 2);
  assert.equal(oneMillion.targets[2].usd, 20000);
  const historicalReference = H.calculateNavExitReferences(100000);
  assert.deepEqual(
    JSON.parse(JSON.stringify(historicalReference.targets.map(x => x.usd))),
    [500, 1000, 2000],
    "historical Run #7 targets must map to .5% / 1% / 2% of the $100k reference NAV"
  );
  assert.equal(H.calculateNavExitReferences(0).ready, false);
  assert.equal(H.calculateNavExitReferences(null).ready, false);
}

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

// The selected ratio direction must change the put legs, not only the label.
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
  const shortHeavy = H.chooseChainLegs(chain, 100, "2026-10-09", 45, "short-heavy");
  assert.equal(shortHeavy.ready, true);
  assert.equal(shortHeavy.expiry, "2026-11-20");
  assert.equal(shortHeavy.atm.strike, 100);
  assert.equal(shortHeavy.short.strike, 110);
  assert.equal(shortHeavy.wing.strike, 120);
  assert.equal(shortHeavy.longPut.strike, 95);
  assert.equal(shortHeavy.shortPut.strike, 90);
  assert.equal(shortHeavy.deltaSource, "PROVIDER_DELTA");

  const longHeavy = H.chooseChainLegs(chain, 100, "2026-10-09", 45, "long-heavy");
  assert.equal(longHeavy.ready, true);
  assert.equal(longHeavy.longPut.strike, 90);
  assert.equal(longHeavy.shortPut.strike, 95);
}


// Main desk → Hub bridge: copy capital once, estimate Hybrid reservation conservatively,
// and fail closed when the plan or any held option-risk unit is unknown.
{
  const bridgeSandbox = { module: { exports: {} } };
  vm.runInNewContext(fs.readFileSync(require.resolve("../hub_context_bridge.js"), "utf8"), bridgeSandbox, { filename: "hub_context_bridge.js" });
  const Bridge = bridgeSandbox.module.exports;
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
        { key: "qqqCallSpreads", current: 0, target: 1, riskPerUnit: 973 },
        { key: "vxxCallSpreads", current: 0, target: 3, riskPerUnit: 276 }
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
  assert.equal(valid.context.riskReservationBasis, "CONFIRMED_REGISTER_HELD_MAX_LOSS_PLUS_INCREMENTAL_TARGET_QTY_X_CURRENT_CANDIDATE_MAX_LOSS");

  const matchedHeldRegister = Bridge.contextFromPrimaryPlan({
    ...plan,
    input: {
      ...plan.input,
      holdings: { qqqCallSpreads: 1, vxxCallSpreads: 2 },
      positionRegister: {
        useForSizing: true,
        completeConfirmed: true,
        records: [{ id: "q-held" }, { id: "v-held" }],
        summary: { rows: [
          { strategyKey: "qqqCallSpreads", qty: 1, termsComplete: true, identityComplete: true, adjustedDetected: false, maxLossPerPackage: 900 },
          { strategyKey: "vxxCallSpreads", qty: 2, termsComplete: true, identityComplete: true, adjustedDetected: false, maxLossPerPackage: 250 }
        ]}
      }
    },
    result: { ...plan.result, rows: [
      { key: "qqqCallSpreads", current: 1, target: 1, riskPerUnit: 973 },
      { key: "vxxCallSpreads", current: 2, target: 3, riskPerUnit: 276 }
    ]}
  });
  assert.equal(matchedHeldRegister.riskReservationReady, true);
  assert.equal(matchedHeldRegister.baseRiskReservedUsd, 1676, "held risk comes from reconciled positions; candidate risk prices only incremental target adds");

  const stockOnlyRegister = Bridge.contextFromPrimaryPlan({
    ...plan,
    input: {
      ...plan.input,
      positionRegister: {
        useForSizing: false,
        completeConfirmed: false,
        records: [{ template: "QQQ_CORE", qty: 50 }, { template: "VXX_SHORT_STOCK", qty: 10 }]
      }
    }
  });
  assert.equal(stockOnlyRegister.riskReservationReady, true, "stock-only ledger rows do not reserve option risk or falsely block a zero-current option scenario");

  const unregisteredHeldRisk = Bridge.contextFromPrimaryPlan({
    ...plan,
    result: { ...plan.result, rows: [
      { key: "qqqCallSpreads", current: 1, target: 1, riskPerUnit: 973 },
      { key: "vxxCallSpreads", current: 0, target: 0, riskPerUnit: null }
    ]}
  });
  assert.equal(unregisteredHeldRisk.riskReservationReady, false, "held option quantities without a complete position register must block reservation");
  assert.equal(unregisteredHeldRisk.baseRiskReservedUsd, null);

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

// Both N:1 directions are distinct. Expiry and quote/contract evidence gates
// are explicit; a net credit is valid and never substitutes for downside risk.
{
  const futureExpiry = new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10);
  const shortHeavyBase = {
    spot: 100, longPutStrike: 95, longPutAsk: 3,
    shortPutStrike: 90, shortPutBid: 1.2, putRatioN: 2,
    putRatioDirection: "short-heavy", putRatioExpiry: futureExpiry,
    putRatioQuoteConfirmed: true, putRatioStandardContractConfirmed: true,
    budgetUsd: 10000
  };
  const r = H.calculatePutRatio(shortHeavyBase);
  assert.equal(r.ready, true);
  assert.equal(r.status, "RISK_GATE_PASS");
  assert.equal(r.orientation, "N SHORT : 1 LONG");
  assert.equal(r.debitUsd, 60);
  assert.equal(r.riskUsd, 8560);
  assert.equal(r.zeroSpotPnlUsd, -8560);
  assert.equal(r.maxPackages, 1);
  assert.equal(r.longPutContracts, 1);
  assert.equal(r.shortPutContracts, 2);
  assert.equal(r.longPutQtyPerPackage, 1);
  assert.equal(r.shortPutQtyPerPackage, 2);
  assert.equal(r.legs[0].qty, 1);
  assert.equal(r.legs[1].qty, 2);

  const longHeavy = H.calculatePutRatio({
    ...shortHeavyBase, putRatioDirection: "long-heavy",
    longPutStrike: 90, longPutAsk: 1.2, shortPutStrike: 95, shortPutBid: 3,
    budgetUsd: 1000
  });
  assert.equal(longHeavy.ready, true);
  assert.equal(longHeavy.status, "RISK_GATE_PASS");
  assert.equal(longHeavy.orientation, "N LONG : 1 SHORT");
  assert.equal(longHeavy.debitUsd, -60);
  assert.equal(longHeavy.riskUsd, 440);
  assert.equal(longHeavy.zeroSpotPnlUsd, 8560);
  assert.equal(longHeavy.maxPackages, 2);
  assert.equal(longHeavy.longPutContracts, 4);
  assert.equal(longHeavy.shortPutContracts, 2);
  assert.equal(longHeavy.legs[0].qty, 2);
  assert.equal(longHeavy.legs[1].qty, 1);

  const shortHeavyCredit = H.calculatePutRatio({ ...shortHeavyBase, shortPutBid: 2, budgetUsd: 10000 });
  assert.equal(shortHeavyCredit.ready, true);
  assert.equal(shortHeavyCredit.debitUsd, -100);
  assert.equal(shortHeavyCredit.riskUsd, 8400);

  const nOne = H.calculatePutRatio({ ...shortHeavyBase, putRatioN: 1, budgetUsd: 1000 });
  assert.equal(nOne.ready, true);
  assert.equal(nOne.debitUsd, 180);
  assert.equal(nOne.riskUsd, 180);

  const tooSmall = H.calculatePutRatio({ ...shortHeavyBase, budgetUsd: 400 });
  assert.equal(tooSmall.ready, true);
  assert.equal(tooSmall.maxPackages, 0);
  assert.equal(tooSmall.status, "RISK_GATE_BLOCK");

  const invalidRatio = H.calculatePutRatio({ ...shortHeavyBase, putRatioN: 2.5 });
  assert.equal(invalidRatio.ready, false);
  assert.equal(invalidRatio.status, "PENDING");
  assert.match(invalidRatio.error, /whole number from 1 to 6/);

  const invalidGeometry = H.calculatePutRatio({ ...shortHeavyBase, longPutStrike: 90, shortPutStrike: 95 });
  assert.equal(invalidGeometry.ready, false);
  assert.equal(invalidGeometry.status, "PENDING");

  const missingExpiry = H.calculatePutRatio({ ...shortHeavyBase, putRatioExpiry: "" });
  assert.equal(missingExpiry.ready, false);
  assert.equal(missingExpiry.status, "PENDING");

  const noQuoteConfirmation = H.calculatePutRatio({ ...shortHeavyBase, putRatioQuoteConfirmed: false });
  assert.equal(noQuoteConfirmation.ready, false);
  assert.equal(noQuoteConfirmation.status, "PENDING");

  const noContractConfirmation = H.calculatePutRatio({ ...shortHeavyBase, putRatioStandardContractConfirmed: false });
  assert.equal(noContractConfirmation.ready, false);
  assert.equal(noContractConfirmation.status, "PENDING");

  const unknownBudget = H.calculatePutRatio({ ...shortHeavyBase, budgetUsd: null });
  assert.equal(unknownBudget.ready, false);
  assert.equal(unknownBudget.status, "PENDING");

  const expired = H.calculatePutRatio({ ...shortHeavyBase, putRatioExpiry: "2020-01-01" });
  assert.equal(expired.ready, false);
  assert.equal(expired.status, "PENDING");
}

// Both orientations remain research-only; neither enters the main call-credit pool.
// The new N:1 put ratio is visible in the dedicated Hub selector and never
// replaces the main terminal's two-leg CALL risk-pool whitelist.
{
  const hubHtml = fs.readFileSync(require("node:path").join(__dirname, "../hub_research_pack.html"), "utf8");
  const hubUi = fs.readFileSync(require("node:path").join(__dirname, "../hub_research_pack_ui.js"), "utf8");
  const mainHtml = fs.readFileSync(require("node:path").join(__dirname, "../index.html"), "utf8");
  assert.ok(hubHtml.includes('<option value="put-ratio">Hub QQQ Put Ratio · N SHORT : 1 LONG / N LONG : 1 SHORT</option>'));
  assert.ok(hubHtml.includes('id="putRatioN"'));
  assert.ok(hubHtml.includes('id="putRatioDirection"'));
  assert.ok(hubHtml.includes('id="putRatioExpiry"'));
  assert.ok(hubHtml.includes('id="putRatioQuoteConfirmed"'));
  assert.ok(hubHtml.includes('id="putRatioStandardContractConfirmed"'));
  assert.ok(hubHtml.includes('id="putRatioExitReference"'), "N:1 pane must show historical exit/risk references");
  assert.ok(hubHtml.includes('id="putRatioExitDirectionNotice"'), "the historical exit card must warn when the selected ratio orientation differs");
  assert.ok(hubUi.includes('if the selected direction is long-heavy, historical SHORT-heavy results are not treated as its evidence') || hubUi.includes('不可當成目前 LONG-heavy N LONG : 1 SHORT 的績效或退出證據'), "LONG-heavy must never inherit SHORT-heavy exit results");
  assert.ok(hubHtml.includes('id="putRatioExit05Usd"') && hubHtml.includes('id="putRatioExit10Usd"') && hubHtml.includes('id="putRatioExit20Usd"'));
  assert.ok(hubUi.includes('E.calculateNavExitReferences(n("nav", null))'), "threshold dollar values must derive from the current NAV input");
  assert.ok(hubHtml.includes("首 5 個持倉交易日"), "fast-exit small-sample warning must remain visible");
  assert.ok(hubHtml.includes("10.64% / 21.47%"), "short-heavy historical terminal tail-risk reference must remain visible"); 
  const exitReference = fs.readFileSync(require("node:path").join(__dirname, "../QQQ_PUT_RATIO_1M_EXIT_REFERENCE_V1.md"), "utf8");
  assert.ok(exitReference.includes("Worked $1m model scenario — not an observed option chain"), "modelled N-sweep example must be explicitly labelled hypothetical");
  assert.ok(exitReference.includes("N=2–6 all exceed a 2% NAV tail budget"), "tail-budget gate must remain explicit");
  assert.ok(exitReference.includes("does not model path-dependent margin calls or forced liquidation"), "terminal-payoff caveat must not disappear");
  assert.ok(hubHtml.includes("QQQ_PUT_RATIO_1M_EXIT_REFERENCE_V1.md"), "full reference report must be linked from Hub");
  assert.ok(hubHtml.includes("BUY TO OPEN"));
  assert.ok(hubUi.includes("E.calculatePutRatio"));
  assert.ok(hubUi.includes("SELL TO OPEN"));
  assert.ok(mainHtml.includes("QQQ Put Ratio (N SHORT : 1 LONG / N LONG : 1 SHORT)"));
  assert.ok(mainHtml.includes('id="preservedResearchTracks"'), "main terminal must keep Put research discoverable above the long dashboard");
  assert.ok(mainHtml.includes('href="option_chain_lab.html?chain=QQQ_PUT"'), "QQQ LONG PUT chain entry must have a direct route");
  assert.ok(mainHtml.includes('href="hub_research_pack.html?strategyMode=put-ratio&amp;putRatioDirection=long-heavy"'), "N LONG PUT : 1 SHORT PUT must have a direction-specific direct route");
  assert.ok(mainHtml.includes('href="hub_research_pack.html?strategyMode=put-ratio&amp;putRatioDirection=short-heavy"'), "N SHORT PUT : 1 LONG PUT must have a direction-specific direct route");
  assert.ok(hubUi.includes('get("putRatioDirection")'), "Hub must restore the requested ratio orientation from the route");
  assert.ok(hubUi.includes('$("putRatioDirection").value = requestedPutRatioDirection'), "a direct link must not fall back to the opposite default ratio orientation");
  assert.ok(mainHtml.includes('href="hub_research_pack.html?strategyMode=shock-put"'), "shock-gated put-debit lane must have a one-click route");
  assert.ok(hubUi.includes('get("strategyMode")'), "Hub must honor the main-desk direct route");
  const primaryUi = fs.readFileSync(require("node:path").join(__dirname, "../app.js"), "utf8");
  assert.ok(primaryUi.includes("function syncCapitalContextToHub(openHub = true)"), "direct Hub links must sync the live primary context");
  assert.ok(primaryUi.includes("syncCapitalContextToHub(false)"), "direct Hub routes must sync without spawning a duplicate window");
  assert.ok(primaryUi.includes('target.searchParams.set("fromPrimary", "1")'), "Hub direct routes must import current NAV/cash/risk context");
  assert.ok(primaryUi.includes("event.preventDefault()"), "failed primary-context sync must not silently open Hub with stale defaults");
  assert.ok(mainHtml.includes("N=10／20 lower-strike SHORT PUTs"), "legacy N10/N20 study must remain discoverable without being conflated with Hub N1-6");
  assert.ok(mainHtml.includes("1 LONG higher-strike : 5 SHORT lower-strike"), "legacy 1x5 exit study must remain discoverable");
  const preservationRegister = fs.readFileSync(require("node:path").join(__dirname, "../STRATEGY_PRESERVATION_REGISTER.md"), "utf8");
  assert.ok(preservationRegister.includes("QQQ_PUT_RATIO_N1_LONG_HEAVY"), "preservation register must explicitly retain N LONG PUT : 1 SHORT PUT");
  assert.ok(preservationRegister.includes("QQQ_PUT_RATIO_N1_SHORT_HEAVY"), "preservation register must explicitly retain N SHORT PUT : 1 LONG PUT");
  assert.ok(preservationRegister.includes("QQQ_PUT_RATIO_EXIT_1_LONG_5_SHORT"), "preservation register must retain the distinct historical 1-long/5-short exit study");
  assert.ok(preservationRegister.includes("QQQ_PUT_ATM_N10_N20_SHORT_HEAVY"), "preservation register must retain the distinct historical N10/N20 ATM-long study");
  assert.ok(preservationRegister.includes("QQQ_LONG_PUT"), "preservation register must explicitly retain the standalone QQQ LONG PUT chain");
  assert.ok(!hubHtml.includes("由 Hybrid + 所有啟用的 Hub 結構共用同一個總風險池按比例分配"), "Hub must not claim a multi-structure allocator that is not wired");
  assert.ok(mainHtml.includes('Only those two defined-risk credit verticals share the option max-loss pool'));
}

console.log("HUB RESEARCH OPTION PACK: directional put-ratio regression PASS");
