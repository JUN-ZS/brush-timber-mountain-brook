"use strict";
// Full-use scenario matrix. Prices are plausible deterministic what-if fixtures,
// not current market data, not live quotes, and not evidence of executable fills.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadUmd(relPath) {
  const sandbox = { module: { exports: {} } };
  vm.runInNewContext(
    fs.readFileSync(require.resolve(relPath), "utf8"),
    sandbox,
    { filename: path.basename(relPath) }
  );
  return sandbox.module.exports;
}

// Repo package.json is "type":"module", so plain require of these browser UMDs
// returns an empty Module namespace. Load them the same way sibling *.test.cjs files do.
const E = loadUmd("../engine.js");
const P = loadUmd("../position_ledger.js");
const D = loadUmd("../decision_value_engine.js");
const R = loadUmd("../deployment_roadmap.js");
const Lab = loadUmd("../option_chain_lab.js");
assert.ok(E && typeof E.assessMarket === "function", "engine UMD must export assessMarket");
assert.ok(Lab && Lab.SAMPLE && Lab.SAMPLE.chains, "Lab SAMPLE fixture must load via UMD sandbox");

const now = Date.now();
const today = new Date(now).toISOString().slice(0, 10); // deterministic ISO market-date fixture; not an engine API dependency
assert.ok(today, "test clock must resolve an operational market date");
const expiry = new Date(Date.parse(today + "T00:00:00Z") + 45 * 86400000).toISOString().slice(0, 10);
const recent = new Date(now - 5 * 60000).toISOString();
const stale = new Date(now - 20 * 60000).toISOString();
let passed = 0;
function scenario(name, fn) {
  fn();
  passed += 1;
  console.log("PASS · " + name);
}
function near(actual, expected, epsilon = 0.01) {
  assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= epsilon,
    "expected " + expected + " ± " + epsilon + ", got " + actual);
}
function row(plan, key) {
  const r = plan.rows.find(x => x.key === key);
  assert.ok(r, "missing planner row: " + key);
  return r;
}
function snap(overrides = {}) {
  return {
    qqq: 748, vxx: 17.23, vix: 18, m1: 18, m2: 19,
    term_asof: today, spot_asof: today, today, term_source: "SCENARIO_FIXTURE",
    ...overrides
  };
}
function planBase(overrides = {}) {
  return {
    market: snap(), nav: 100000, cashPool: 100000,
    sizing: {
      cashReservePct: 10, qqqCorePct: 42, vxxNormalPct: 18, vxxHighPct: 10,
      vxxShortMarginMultiple: 1.5, totalOptionRiskPct: 3.2,
      qqqCallRiskPct: 1.2, vxxCallRiskPct: 2.0,
      vixHigh: 28, termSafe: 5, maxTermAgeDays: 4
    },
    holdings: {}, candidates: {}, permissions: {}, manualRiskPerUnit: {},
    positionRegister: {}, ratioCampaign: {},
    ...overrides
  };
}
function makeCandidate(chainKey, root, pairKey) {
  const rows = Lab.SAMPLE.chains[chainKey];
  const calculated = Lab.calculateVerticals(chainKey, rows, 100, 3200);
  const picked = calculated.candidates.find(x => x.key === pairKey);
  assert.ok(picked, "sample fixture should contain " + pairKey);
  const meta = {
    sourceType: "USER_SCREENSHOT_TRANSCRIPTION",
    sourceName: "Repository regression fixture; not authenticated market evidence",
    sourceUrl: "",
    observedAt: recent,
    timezone: "UTC",
    contractSymbol: root,
    contractStatus: "STANDARD_TERMS_RECORDED",
    deliverableNote: "100 shares",
    contractEvidenceUrl: "https://www.theocc.com/"
  };
  const handoff = Lab.buildPrimaryPlannerHandoff(
    meta, expiry, chainKey, picked, 100, rows.length, false, true, now
  );
  assert.equal(handoff.ok, true, handoff.reason || "Lab handoff must be structurally valid");
  assert.equal(handoff.candidate.dataAuthentication, "NOT_INDEPENDENTLY_VERIFIED");
  assert.equal(handoff.candidate.ordersAuthorized, false);
  return handoff.candidate;
}
const qqqCandidate = makeCandidate("QQQ_CALL", "QQQ", "799C/810C");
const vxxCandidate = makeCandidate("VXX_CALL", "VXX", "21C/24C");
const fullInput = planBase({ candidates: { qqqCall: qqqCandidate, vxxCall: vxxCandidate } });
const carry = E.assessMarket(snap());
const shock = E.assessMarket(snap({ vix: 38, m1: 22, m2: 20 }));
const weakening = E.assessMarket(snap({ m1: 20, m2: 20.5 }));

scenario("market-state classifier covers carry / weakening / pre-shock / shock / blocked", () => {
  assert.equal(carry.state, "CARRY");
  assert.equal(weakening.state, "WEAKENING");
  assert.equal(E.assessMarket(snap({ vix: 31 })).state, "PRE-SHOCK");
  assert.equal(shock.state, "SHOCK");
  assert.equal(E.assessMarket(snap({ m1: null })).blocked, true);
});

scenario("capital-first four-leg plan reproduces a credible $100k scenario", () => {
  const r = E.calculatePortfolio(fullInput);
  assert.equal(r.ok, true);
  assert.equal(r.market.state, "CARRY");
  assert.equal(row(r, "qqqShares").capacity, 56);
  assert.equal(row(r, "vxxShortShares").capacity, 1044);
  assert.equal(row(r, "qqqCallSpreads").riskPerUnit, 973);
  assert.equal(row(r, "qqqCallSpreads").capacity, 1);
  assert.equal(row(r, "vxxCallSpreads").riskPerUnit, 276);
  assert.equal(row(r, "vxxCallSpreads").capacity, 7);
  near(r.optionRiskReservedAtTargets, 2905);
  near(r.remainingUnallocatedCashUsd, 17929.82);
  assert.ok(r.optionRiskReservedAtTargets <= r.totalOptionRiskPool);
  assert.ok(r.plannedCapitalRequiredUsd <= r.cashPool);
  assert.equal(r.boundary.brokerOrders, false);
  assert.equal(r.boundary.automaticMutation, false);
});

scenario("over-cap positions trim while market is weakening and new carry stays disabled", () => {
  const r = E.calculatePortfolio(planBase({
    market: snap({ m1: 20, m2: 20.5 }),
    holdings: { qqqShares: 100, vxxShortShares: 1100, qqqCallSpreads: 1, vxxCallSpreads: 2 },
    candidates: { qqqCall: qqqCandidate, vxxCall: vxxCandidate }
  }));
  assert.equal(r.market.state, "WEAKENING");
  assert.equal(row(r, "qqqShares").action, "REDUCE");
  assert.equal(row(r, "qqqShares").target, 56);
  assert.equal(row(r, "vxxShortShares").action, "REDUCE");
  assert.equal(row(r, "vxxShortShares").target, 1044);
  assert.equal(row(r, "qqqCallSpreads").target, 1);
  assert.equal(row(r, "qqqCallSpreads").action, "HOLD");
  assert.equal(row(r, "vxxCallSpreads").target, 2);
});

scenario("shock/backwardation blocks seller adds and cuts VXX short target to zero", () => {
  const r = E.calculatePortfolio(planBase({
    market: snap({ vix: 38, m1: 22, m2: 20 }),
    holdings: { qqqShares: 10, vxxShortShares: 250, qqqCallSpreads: 1, vxxCallSpreads: 2 },
    candidates: { qqqCall: qqqCandidate, vxxCall: vxxCandidate }
  }));
  assert.equal(r.market.state, "SHOCK");
  assert.equal(row(r, "vxxShortShares").target, 0);
  assert.equal(row(r, "vxxShortShares").action, "REDUCE");
  assert.equal(row(r, "qqqCallSpreads").target, 0);
  assert.equal(row(r, "vxxCallSpreads").target, 0);
});

scenario("missing, stale, future and invalid market inputs fail closed", () => {
  const missing = E.calculatePortfolio(planBase({ market: snap({ qqq: null }) }));
  assert.equal(missing.ok, false);
  assert.equal(row(missing, "qqqShares").action, "BLOCKED");
  const staleDate = new Date(Date.parse(today + "T00:00:00Z") - 10 * 86400000).toISOString().slice(0, 10);
  const stalePlan = E.calculatePortfolio(planBase({
    market: snap({ term_asof: staleDate }), holdings: { qqqShares: 21 }
  }));
  assert.equal(stalePlan.market.state, "DATA STALE");
  assert.equal(row(stalePlan, "qqqShares").target, 21);
  const futurePlan = E.calculatePortfolio(planBase({
    market: snap({ term_asof: "2099-01-01", spot_asof: "2099-01-01" })
  }));
  assert.equal(futurePlan.market.state, "AS-OF FUTURE");
  const invalidBudget = E.calculatePortfolio(planBase({ sizing: { ...planBase().sizing, cashReservePct: 101 } }));
  assert.equal(invalidBudget.ok, false);
  assert.equal(row(invalidBudget, "qqqShares").status, "INVALID_PERCENT");
});

scenario("limited free cash constrains capacity without exceeding the shared cash pool", () => {
  const r = E.calculatePortfolio(planBase({ cashPool: 500, candidates: { qqqCall: qqqCandidate } }));
  assert.equal(r.totalOptionRiskPool, 450);
  assert.equal(row(r, "qqqCallSpreads").capacity, 0);
  assert.equal(row(r, "qqqShares").capacity, 0);
  assert.ok(r.plannedCapitalRequiredUsd <= 500);
  assert.ok(r.remainingUnallocatedCashUsd >= 0);
});

scenario("QQQ/VXX option-chain arithmetic plus adverse slippage matches fixture", () => {
  const q = Lab.calculateVerticals("QQQ_CALL", Lab.SAMPLE.chains.QQQ_CALL, 100, 3200).candidates.find(x => x.key === "799C/810C");
  const v = Lab.calculateVerticals("VXX_CALL", Lab.SAMPLE.chains.VXX_CALL, 100, 3200).candidates.find(x => x.key === "21C/24C");
  near(q.credit, 1.27, 1e-8); near(q.maxLoss, 973, 1e-8);
  near(q.executionStress[1].creditPerShare, 1.22, 1e-8);
  near(q.executionStress[1].maxLoss, 978, 1e-8);
  near(v.credit, 0.24, 1e-8); near(v.maxLoss, 276, 1e-8);
  near(v.executionStress[1].creditPerShare, 0.19, 1e-8);
  near(v.executionStress[1].maxLoss, 281, 1e-8);
  assert.equal(Lab.SAMPLE.observationTimeVerified, false);
  // Clone out of the UMD vm realm so deepEqual does not fail on cross-context arrays.
  assert.deepEqual(JSON.parse(JSON.stringify(Lab.SAMPLE.chains.QQQ_PUT)), []);
  assert.deepEqual(JSON.parse(JSON.stringify(Lab.SAMPLE.chains.VXX_PUT)), []);
});

scenario("wide/missing quotes and adjusted contract terms do not masquerade as usable capacity", () => {
  const missing = Lab.calculateVerticals("QQQ_CALL", [
    {strike: 799, bid: 3.16, ask: 3.18},
    {strike: 810, bid: null, ask: 1.89}
  ], 100, 3200);
  assert.equal(missing.candidates.length, 0);
  assert.ok(Lab.calculateVerticals("QQQ_CALL", Lab.SAMPLE.chains.QQQ_CALL, null, 3200).error);
  assert.ok(Lab.calculateVerticals("QQQ_CALL", Lab.SAMPLE.chains.QQQ_CALL, 100, -1).error);
  const adjusted = Lab.calculateVerticals("VXX_CALL", Lab.SAMPLE.chains.VXX_CALL, 100, 3200, "ADJUSTED_TERMS_RECORDED");
  assert.equal(adjusted.candidates.length, 0);
  const staleCandidate = { ...qqqCandidate, quoteObservedAt: stale };
  const stalePlan = E.calculatePortfolio({ ...fullInput, candidates: { qqqCall: staleCandidate, vxxCall: vxxCandidate } });
  assert.equal(row(stalePlan, "qqqCallSpreads").capacity, null);
  assert.equal(row(stalePlan, "qqqCallSpreads").action, "PENDING");
  assert.equal(row(stalePlan, "vxxCallSpreads").capacity, 7);
});

function stockPosition(template, qty, entryPrice, markPrice, extra = {}) {
  return {
    id: template + "-fixture", template, qty, entryDate: today, entryPrice, markPrice,
    riskBudgetUsd: 2000, stopMarkPrice: template === "VXX_SHORT_STOCK" ? entryPrice + 2 : entryPrice - 20,
    targetMarkPrice: template === "VXX_SHORT_STOCK" ? entryPrice - 2 : entryPrice + 40,
    maxHoldDays: 120, markAsOf: recent, markSourceType: "EOD_MARK",
    markSourceNote: "SCENARIO FIXTURE ONLY; not a broker statement",
    entryEvidence: "BROKER_STATEMENT", entrySourceNote: "SYNTHETIC TEST LABEL; not a real fill",
    multiplier: 1, ...extra
  };
}
function optionPosition(termsVerified = true, extra = {}) {
  const ymd = expiry.slice(2,4) + expiry.slice(5,7) + expiry.slice(8,10);
  const occ = (strike) => "QQQ" + ymd + "C" + String(Math.round(strike * 1000)).padStart(8,"0");
  return {
    id: "qqq-call-fixture", template: "QQQ_CALL_CREDIT", qty: 1,
    entryDate: today, entryPrice: 1.27, markPrice: 0.80,
    riskBudgetUsd: 973, stopMarkPrice: 2.10, targetMarkPrice: 0.40,
    maxHoldDays: 45, expiryReviewDte: 14, markAsOf: recent, markSourceType: "EOD_MARK",
    markSourceNote: "SCENARIO FIXTURE ONLY; closing debit is not executable evidence",
    entryEvidence: "BROKER_STATEMENT", entrySourceNote: "SYNTHETIC TEST LABEL; not a real fill",
    expiry, shortStrike: 799, longStrike: 810, shortSymbol: occ(799), longSymbol: occ(810),
    multiplier: 100, termsVerified, deliverableNote: "100 shares; test fixture only", ...extra
  };
}

scenario("position ledger P&L signs, metadata buckets and import/export round-trip work together", () => {
  const positions = [
    stockPosition("QQQ_CORE", 10, 740, 748),
    stockPosition("VXX_SHORT_STOCK", 100, 18, 17.23),
    optionPosition(true)
  ];
  const summary = P.summarize(positions, {qqq: 748, vxx: 17.23, spot_asof: today}, now);
  assert.equal(summary.holdings.qqqShares, 10);
  assert.equal(summary.holdings.vxxShortShares, 100);
  assert.equal(summary.holdings.qqqCallSpreads, 1);
  near(summary.rows[0].unrealizedPnl, 80);
  near(summary.rows[1].unrealizedPnl, 77);
  near(summary.rows[2].unrealizedPnl, 47);
  assert.equal(summary.termBlockedCount, 0);
  assert.equal(summary.metadataCompletePnlRows, 3);
  const envelope = P.exportEnvelope(positions, new Date(now).toISOString());
  const imported = P.parseEnvelope(JSON.stringify(envelope));
  assert.equal(imported.ok, true);
  assert.equal(imported.positions.length, 3);
  assert.equal(P.parseEnvelope("{ invalid JSON").ok, false);
});

scenario("unverified held option terms block only the affected sizing leg; stale marks lose qualified status", () => {
  const badTerms = P.summarize([optionPosition(false)], {}, now);
  assert.ok(badTerms.blockingKeys.includes("qqqCallSpreads"));
  const blockedPlan = E.calculatePortfolio({
    ...fullInput,
    holdings: { qqqCallSpreads: 1 },
    positionRegister: { useForSizing: true, blockingKeys: badTerms.blockingKeys }
  });
  assert.equal(row(blockedPlan, "qqqCallSpreads").riskPerUnit, null);
  assert.equal(row(blockedPlan, "qqqCallSpreads").capacity, null);
  assert.equal(row(blockedPlan, "vxxCallSpreads").capacity, 7);
  const staleLedger = P.summarize([
    stockPosition("QQQ_CORE", 10, 740, 748, { markAsOf: new Date(now - 30 * 60000).toISOString(), markSourceType: "BROKER_LIVE" })
  ], {}, now);
  assert.equal(staleLedger.rows[0].staleMark, true);
  assert.equal(staleLedger.metadataCompletePnlRows, 0);
  assert.equal(staleLedger.indicativePnlRows, 1);
});

function generalityDossier() {
  return {
    auditorVersion:"QQQ_HYBRID_GENERALITY_AUDITOR_V1", auditStatus:"PASS_OPERATOR_ATTESTED",
    evidenceClass:"OBSERVED", outcomeClass:"REAL_EXECUTION", sourceAuthenticated:true,
    canCountAsRealExecutionProbability:true,
    inputIntegrity:{observationsSha256:"a".repeat(64),calendarSha256:"b".repeat(64),specSha256:"c".repeat(64)},
    dataQuality:{sourceRowCount:1500,expectedObservationCoveragePct:100,missingExpectedDates:[]},
    baselineId:"SCENARIO_BASELINE",candidateId:"SCENARIO_CANDIDATE",sourceRef:"synthetic scenario fixture",
    trainStart:"2018-01-02",trainEnd:"2019-12-31",validationStart:"2020-01-02",validationEnd:"2023-12-29",
    finalStart:"2024-01-02",finalEnd:"2024-12-31",
    finalUntouched:true,finalEvaluatedOnce:true,designFrozenBeforeFinal:true,noLookahead:true,trialLedgerComplete:true,
    finalCoveragePct:100,finalObservationCount:252,
    regimeObservations:{CARRY:300,WEAKENING:150,"PRE-SHOCK":120,SHOCK_BACKWARDATION:110},
    rollingWindows:[
      {id:"W1",start:"2020-01-02",end:"2020-12-31",observations:252,coveragePct:100,missingDatesReviewed:true,sameCapitalAndCosts:true,lookaheadFree:true,costStressPass:true,catastrophicFailure:false,effectDeltaPct:0.4},
      {id:"W2",start:"2021-01-04",end:"2021-12-31",observations:252,coveragePct:100,missingDatesReviewed:true,sameCapitalAndCosts:true,lookaheadFree:true,costStressPass:true,catastrophicFailure:false,effectDeltaPct:0.2},
      {id:"W3",start:"2022-01-03",end:"2022-12-30",observations:252,coveragePct:100,missingDatesReviewed:true,sameCapitalAndCosts:true,lookaheadFree:true,costStressPass:true,catastrophicFailure:false,effectDeltaPct:0.3},
      {id:"W4",start:"2023-01-03",end:"2023-06-30",observations:124,coveragePct:99.2,missingDatesReviewed:true,sameCapitalAndCosts:true,lookaheadFree:true,costStressPass:true,catastrophicFailure:false,effectDeltaPct:0.1},
      {id:"W5",start:"2023-07-03",end:"2023-12-29",observations:125,coveragePct:99.2,missingDatesReviewed:true,sameCapitalAndCosts:true,lookaheadFree:true,costStressPass:true,catastrophicFailure:false,effectDeltaPct:0.15}
    ]
  };
}
function stress() {
  return {
    scenarioName:"Illustrative QQQ drawdown + volatility expansion",
    sourceNote:"Synthetic loss-only stress assumptions; not VaR or a verified portfolio mark",
    reconciled:true,
    legs:{
      qqqCore:{state:"ACTIVE",stressLossUsd:900},
      vxxShort:{state:"ZERO"},
      qqqCallCredit:{state:"ACTIVE",stressLossUsd:500},
      vxxCallCredit:{state:"ACTIVE",stressLossUsd:300}
    }
  };
}
scenario("Decision Value engine refuses forged execution evidence while retaining useful EV diagnostics", () => {
  const dossier = generalityDossier();
  const review = D.evaluateGenerality(dossier);
  assert.equal(review.status, "PASS_OPERATOR_ATTESTED");
  assert.equal(review.canCountAsRealExecutionProbability, false);
  const common = {
    candidateKey:"qqqShares", lens:"ADD", quantity:10, horizonDays:30, nav:100000,
    rewardUsd:100, lossUsd:50, costUsd:5, costStressUsd:10, riskNature:"DEFINED",
    probabilityMethod:"EMPIRICAL", wins:40, trials:50, probabilityBasis:"INDEPENDENT_OOS",
    accuracy:"PASS", generality:"PASS", integration:"PASS",
    evidenceNote:"synthetic report; no source authentication",
    alternativeEVTotalUsd:0, alternativeLabel:"WAIT direct-P&L sensitivity only",
    candidateCapitalBasisUsd:100000, alternativeCapitalBasisUsd:100000,
    candidateRiskBudgetUsd:1700, alternativeRiskBudgetUsd:1700,
    alternativeHorizonDays:30, alternativeCostsIncluded:true,
    generalityDossierJson:dossier, portfolioStress:stress(),
    market:{blocked:false,allowNew:true,action:"BUY",state:"CARRY"},
    mainRow:{key:"qqqShares",current:10,target:30,capacity:100,action:"ADD",status:"READY",reason:"synthetic scenario"}
  };
  const r = D.evaluate(common);
  assert.equal(r.status, "EVIDENCE_INCOMPLETE");
  assert.equal(r.independentEvidenceOk, false);
  assert.equal(r.generalityReview.canCountAsRealExecutionProbability, false);
  assert.ok(r.expectedValueBaseUsd > 0, "the scenario arithmetic can remain visible");
  assert.ok(r.expectedValueAdverseUsd > 0, "the adverse scenario is positive under these invented inputs");
  assert.equal(r.brokerOrders, false);
  const noAlt = D.evaluate({...common, alternativeEVTotalUsd:null, alternativeLabel:""});
  assert.equal(noAlt.status, "ALTERNATIVE_VALUE_PENDING");
  const blockedMarket = D.evaluate({...common, market:{blocked:true,allowNew:false,state:"DATA BLOCKED"}});
  assert.equal(blockedMarket.status, "MARKET_BLOCKED");
  const hypothetical = D.evaluate({...common, probabilityBasis:"HYPOTHESIS"});
  assert.equal(hypothetical.status, "HYPOTHESIS_ONLY");
});

scenario("CLOCK Floor, future contributions and market gates do not auto-invest or auto-sell", () => {
  const carryStart = (Number(today.slice(0,4))-9) + today.slice(4);
  const floorStart = (Number(today.slice(0,4))-10) + today.slice(4);
  const carryRoadmap = R.evaluate({
    baseCapitalUsd:100000,startDate:carryStart,horizonMonths:120,monthlyContributionUsd:500,
    currentNavUsd:105000,currentCashUsd:50000,today,market:carry
  });
  assert.equal(carryRoadmap.status, "CARRY_HUMAN_REVIEW");
  near(carryRoadmap.floorUsd, 90000);
  assert.equal(carryRoadmap.plannedFutureContributionsUsd, 6000);
  assert.equal(carryRoadmap.contributionsCountedInCurrentCash, false);
  assert.equal(carryRoadmap.forecastedCagr, null);
  assert.equal(carryRoadmap.brokerOrders, false);
  const floorBreach = R.evaluate({...{
    baseCapitalUsd:100000,startDate:floorStart,horizonMonths:120,monthlyContributionUsd:500,
    currentNavUsd:90000,currentCashUsd:50000,today,market:carry
  }});
  assert.equal(floorBreach.status, "FLOOR_BREACH");
  assert.match(floorBreach.nextAction, /不會自動 SELL/);
  const riskOff = R.evaluate({
    baseCapitalUsd:100000,startDate:carryStart,horizonMonths:120,monthlyContributionUsd:0,
    currentNavUsd:100000,currentCashUsd:100000,today,market:shock
  });
  assert.equal(riskOff.status, "DEFENSIVE_REVIEW");
  const noData = R.evaluate({
    baseCapitalUsd:100000,startDate:carryStart,horizonMonths:120,monthlyContributionUsd:0,
    currentNavUsd:100000,currentCashUsd:100000,today,market:{blocked:true,allowNew:false,state:"UNKNOWN",action:"HOLD"}
  });
  assert.equal(noData.status, "WAIT_FOR_DATA");
});

scenario("HTML load order and broker boundary are wired as expected", () => {
  const root = path.join(__dirname, "..");
  const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
  const scripts = [...html.matchAll(/<script[^>]+src=["']([^"']+)["']/g)].map(m => m[1]);
  for (const asset of scripts) {
    if (/^(https?:)?\/\//.test(asset)) continue;
    assert.ok(fs.existsSync(path.join(root, asset)), "missing local script " + asset);
  }
  assert.ok(scripts.indexOf("decision_value_engine.js") >= 0);
  assert.ok(scripts.indexOf("app.js") > scripts.indexOf("decision_value_engine.js"));
  assert.ok(scripts.indexOf("position_ledger.js") >= 0);
  assert.ok(scripts.indexOf("deployment_roadmap.js") >= 0);
  assert.ok(fs.readFileSync(path.join(root, "server.py"), "utf8").includes("/api/journal"));
  assert.equal(E.calculatePortfolio(fullInput).boundary.brokerOrders, false);
});

console.log("QQQ HYBRID FULL-USE SCENARIO MATRIX: " + passed + " scenarios PASS (deterministic what-if inputs; not live evidence)");
