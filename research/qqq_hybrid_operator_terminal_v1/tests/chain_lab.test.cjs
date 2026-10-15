"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(require.resolve("../option_chain_lab.js"), "utf8"), sandbox, { filename: "option_chain_lab.js" });
const Lab = sandbox.module.exports;
const s = Lab.SAMPLE;
const fixture = JSON.parse(fs.readFileSync(require.resolve("./fixtures/user_uploaded_option_chain_2026-11-20.json"), "utf8"));
function near(a,b,label){assert.ok(Math.abs(a-b)<1e-8,label+": expected "+b+", got "+a);}

// Anti-drift: UI sample must match the canonical upload fixture exactly.
assert.equal(s.expiration, fixture.expiration);
for (const [symbol, key] of [["QQQ","QQQ_CALL"],["VXX","VXX_CALL"]]) {
  const expected = fixture.instruments[symbol].quotes.map(q => ({strike:q.strike,bid:q.bid,ask:q.ask,delta:q.delta}));
  assert.deepEqual(JSON.parse(JSON.stringify(s.chains[key])), expected, key + " must match canonical screenshot fixture");
}
assert.deepEqual(JSON.parse(JSON.stringify(s.chains.QQQ_PUT)), []);
assert.deepEqual(JSON.parse(JSON.stringify(s.chains.VXX_PUT)), []);

// Screenshot sample must match the canonical repository fixture.
// QQQ CALL: 799 bid $3.16; 810 protective wing ask $1.89.
const call = Lab.calculateVerticals("QQQ_CALL",s.chains.QQQ_CALL,100,3200);
const q1=call.candidates.find(x=>x.key==="799C/805C");
const q2=call.candidates.find(x=>x.key==="799C/810C");
assert.ok(q1 && q2);
near(q1.credit,.76,"QQQ 799/805 net credit per share");
near(q1.maxProfit,76,"QQQ 799/805 max profit");
near(q1.maxLoss,524,"QQQ 799/805 max loss");
near(q1.breakEven,799.76,"QQQ 799/805 breakeven");
near(q2.credit,1.27,"QQQ 799/810 net credit per share");
near(q2.maxLoss,973,"QQQ 799/810 max loss");
assert.equal(q2.maxQty,3);
assert.equal(q2.spreadBand,"≤10% MID");
assert.ok(q2.shortSpreadPctMid < 10 && q2.wingSpreadPctMid < 10);
near(q2.executionStress[1].creditPerShare,1.22,"QQQ 799/810 credit after $0.025 extra adverse slippage per leg");
near(q2.executionStress[1].maxLoss,978,"QQQ 799/810 max loss under $0.025 per-leg slippage");
assert.equal(q2.executionStress.length,4);
assert.equal(q2.executionStress[3].maxQty,3);

// Relative spread/mid tiers must expose wide cheap contracts that a fixed dollar floor could hide.
assert.equal(Lab.quoteState({bid:.99,ask:1.01}).band,"TIGHT");
assert.equal(Lab.quoteState({bid:.90,ask:1.10}).band,"MODERATE");
const cheapWide=Lab.quoteState({bid:.01,ask:.11});
assert.equal(cheapWide.band,"WIDE");
assert.ok(cheapWide.spreadPctMid > 25 && cheapWide.wide);

// VXX CALL values and sizing must follow the same uploaded fixture.
const vcall = Lab.calculateVerticals("VXX_CALL",s.chains.VXX_CALL,100,3200);
const vc = vcall.candidates.find(x=>x.key==="21C/24C");
assert.ok(vc);
near(vc.credit,.24,"VXX 21/24 net credit per share");
near(vc.maxProfit,24,"VXX 21/24 max profit");
near(vc.maxLoss,276,"VXX 21/24 max loss");
near(vc.breakEven,21.24,"VXX 21/24 breakeven");
near(vc.executionStress[1].creditPerShare,.19,"VXX 21/24 credit after $0.025 extra adverse slippage per leg");
near(vc.executionStress[1].maxLoss,281,"VXX 21/24 max loss under $0.025 per-leg slippage");
assert.equal(vc.executionStress[3].maxQty,10);

// Do not fabricate puts absent from the screenshot. They remain importable separately.
assert.equal(s.chains.QQQ_PUT.length,0,"screenshot QQQ put chain must remain empty");
assert.equal(s.chains.VXX_PUT.length,0,"screenshot VXX put chain must remain empty");
assert.equal(Lab.calculateVerticals("VXX_PUT",s.chains.VXX_PUT,100,3200).candidates.length,0);

const csv=Lab.parseCsv("symbol,side,strike,bid,ask,delta\nQQQ,CALL,799,3.16,3.18,0.1456\nVXX,PUT,16,0.65,0.77,-0.3264");
assert.equal(csv.total,2);
assert.equal(csv.chains.QQQ_CALL[0].strike,799);
assert.equal(csv.chains.VXX_PUT[0].bid,.65);

// A separately supplied manual put chain still computes correctly; it is not part of the screenshot sample.
const manualPut = Lab.calculateVerticals("VXX_PUT",[
  {strike:15,bid:.30,ask:.37,delta:-.1964},
  {strike:16,bid:.65,ask:.77,delta:-.3264}
],100,3200);
const vp=manualPut.candidates.find(x=>x.key==="16P/15P");
assert.ok(vp);
near(vp.credit,.28,"manual VXX 16/15 put credit");
near(vp.maxProfit,28,"manual VXX put max profit");
near(vp.maxLoss,72,"manual VXX put max loss");
near(vp.breakEven,15.72,"manual VXX put breakeven");
near(Lab.expiryPnl(vp,15,100,1),-72,"manual VXX put max loss at expiry");

const missing=Lab.calculateVerticals("VXX_PUT",[
  {strike:16,bid:null,ask:.77},
  {strike:15,bid:.30,ask:.37}
],100,3200);
assert.equal(missing.candidates.length,0);

// Invalid sizing inputs must BLOCK rather than silently use standard defaults.
assert.ok(Lab.calculateVerticals("QQQ_CALL",s.chains.QQQ_CALL,0,3200).error);
assert.ok(Lab.calculateVerticals("QQQ_CALL",s.chains.QQQ_CALL,null,3200).error);
assert.ok(Lab.calculateVerticals("QQQ_CALL",s.chains.QQQ_CALL,100,null).error);
assert.ok(Lab.calculateVerticals("QQQ_CALL",s.chains.QQQ_CALL,100,-1).error);
assert.equal(Lab.expiryPnl(q2,810,0,1),null);
assert.equal(Lab.expiryPnl(q2,810,100,0),null);
assert.equal(Lab.expiryPnl(q2,810,100,1.5),null);
// CSV with source and contract metadata survives quoted commas and records expiry.
const richCsv = 'symbol,side,strike,bid,ask,delta,expiration,source_type,source_name,source_url,observed_at,timezone,contract_symbol,contract_status,deliverable_note,contract_evidence_url\n' +
  'VXX,CALL,21,0.58,0.72,0.2698,2026-11-20,PUBLIC_DATA,"Example, feed",https://example.com/data,2026-10-09T15:45:00-04:00,America/New_York,VXX,STANDARD_TERMS_RECORDED,"100 shares",https://example.com/occ\n' +
  'VXX,CALL,24,0.24,0.34,0.1731,2026-11-20,PUBLIC_DATA,"Example, feed",https://example.com/data,2026-10-09T15:45:00-04:00,America/New_York,VXX,STANDARD_TERMS_RECORDED,"100 shares",https://example.com/occ';
const rich = Lab.parseCsv(richCsv);
assert.equal(rich.total,2);
assert.equal(rich.expiration,"2026-11-20");
assert.equal(rich.metadata.sourceType,"PUBLIC_DATA");
assert.equal(rich.metadata.sourceName,"Example, feed");
assert.equal(rich.chainMetadata.VXX_CALL.contractSymbol,"VXX");
assert.equal(rich.chainMetadata.VXX_CALL.deliverableNote,"100 shares");
assert.equal(rich.metadataConflicts.length,0);
assert.equal(Lab.parseCsv('symbol,side,strike,bid,ask,delta\nQQQ,CALL,799,3.16,3.18,0.1456').expiration,"","legacy CSV must not inherit the UI's prior expiry");

const goodMeta={sourceType:"PUBLIC_DATA",sourceName:"Example feed",sourceUrl:"https://example.com/data",observedAt:"2026-10-09T15:45:00-04:00",timezone:"America/New_York",contractSymbol:"VXX",contractStatus:"STANDARD_TERMS_RECORDED",deliverableNote:"100 shares",contractEvidenceUrl:"https://example.com/occ"};
const freshNow=Date.parse("2026-10-09T15:50:00-04:00");
const provGood=Lab.assessProvenance(goodMeta,"2026-11-20",2,false,freshNow);
assert.equal(provGood.complete,true);
assert.equal(provGood.ordersAuthorized,false,"complete metadata must never authorize orders");
assert.equal(provGood.freshnessStatus,"AS-OF ≤15M");
assert.equal(Lab.assessProvenance(goodMeta,"2026-11-20",2,true,freshNow).status,"MANUAL_EDIT_RECHECK");
const modelOnly=Lab.assessProvenance({...goodMeta,sourceType:"MODEL_DERIVED"},"2026-11-20",2,false,freshNow);
assert.equal(modelOnly.status,"MODEL_ONLY");
assert.equal(modelOnly.metadataComplete,false,"model-derived quotes cannot pass provenance completeness");
assert.equal(modelOnly.complete,false,"model-derived quotes must not count as metadata/time pass");
assert.equal(Lab.assessProvenance({...goodMeta,contractStatus:"UNKNOWN"},"2026-11-20",2,false,freshNow).complete,false);
const staleProv=Lab.assessProvenance(goodMeta,"2026-11-20",2,false,Date.parse("2026-10-09T16:01:00-04:00"));
assert.equal(staleProv.status,"STALE_QUOTE");assert.equal(staleProv.complete,false);assert.equal(staleProv.freshnessStatus,"STALE >15M");
const unzonedProv=Lab.assessProvenance({...goodMeta,observedAt:"2026-10-09T15:45"},"2026-11-20",2,false,freshNow);
assert.equal(unzonedProv.status,"QUOTE_TIMEZONE_UNKNOWN");assert.equal(unzonedProv.complete,false);
const futureProv=Lab.assessProvenance({...goodMeta,observedAt:"2026-10-09T16:00:00-04:00"},"2026-11-20",2,false,freshNow);
assert.equal(futureProv.status,"FUTURE_QUOTE_TIMESTAMP");assert.equal(futureProv.complete,false);
const futureByOneMinute=Lab.assessProvenance({...goodMeta,observedAt:"2026-10-09T15:51:00-04:00"},"2026-11-20",2,false,freshNow);
assert.equal(futureByOneMinute.status,"FUTURE_QUOTE_TIMESTAMP","a one-minute-future timestamp must be blocked");
assert.equal(futureByOneMinute.complete,false);
assert.equal(futureByOneMinute.freshnessStatus,"FUTURE TIMESTAMP");
const adjustedMeta={...goodMeta,contractStatus:"ADJUSTED_TERMS_RECORDED",contractSymbol:"VXX2"};
const adjustedStatus=Lab.assessProvenance(adjustedMeta,"2026-11-20",2,false);
assert.equal(adjustedStatus.status,"ADJUSTED_CONTRACT_SCENARIO_ONLY");
assert.equal(adjustedStatus.complete,false);
assert.equal(adjustedStatus.ordersAuthorized,false);
const rootMismatch=Lab.assessProvenance({...goodMeta,contractSymbol:"VXX2",contractStatus:"STANDARD_TERMS_RECORDED"},"2026-11-20",2,false);
assert.equal(rootMismatch.status,"CONTRACT_STATUS_CONFLICT");
assert.equal(rootMismatch.complete,false);
const adjustedCapacity=Lab.calculateVerticals("VXX_CALL",s.chains.VXX_CALL,100,3200,"ADJUSTED_TERMS_RECORDED");
assert.equal(adjustedCapacity.candidates.length,0);
assert.ok(adjustedCapacity.error.includes("調整合約"));

const conflicting=Lab.parseCsv(richCsv.replace("2026-11-20,PUBLIC_DATA","2026-12-18,PUBLIC_DATA"));
assert.ok(conflicting.metadataConflicts.length>0,"mixed expiry rows must be rejected");
const partiallyMissingExpiry = Lab.parseCsv(richCsv.replace("2026-11-20,PUBLIC_DATA"," ,PUBLIC_DATA"));
assert.ok(partiallyMissingExpiry.metadataConflicts.some(x=>x.includes("缺少到期日")));
const partiallyMissingSource = Lab.parseCsv(richCsv.replace("PUBLIC_DATA,\"Example, feed\"","PUBLIC_DATA,"));
assert.ok(partiallyMissingSource.metadataConflicts.some(x=>x.includes("source_name")));

assert.equal(Lab.csvCell('Example, "quoted"'),'"Example, ""quoted"""');

// UI integration: the main operator terminal and Option Chain Lab must expose
// the source-backed validation gate, while clearly keeping it read-only.
const mainHtml = fs.readFileSync(require("path").join(__dirname, "../index.html"), "utf8");
const labHtml = fs.readFileSync(require("path").join(__dirname, "../option_chain_lab.html"), "utf8");
assert.ok(mainHtml.includes('id="researchValidation"'), "main terminal must show the research validation lockbox");
assert.ok(mainHtml.includes("1,946 / 1,971 · 98.73%"), "main terminal must disclose paired-session coverage");
assert.ok(mainHtml.includes("−2.72%"), "main terminal must disclose measured spot-basis mismatch");
assert.ok(mainHtml.includes("does not change sizing, entry/exit rules, strategy weights, or broker permissions"), "validation lockbox must remain read-only");
assert.ok(labHtml.includes('id="asof" type="text"'), "quote timestamp must require explicit timezone-bearing ISO string");
assert.ok(labHtml.includes("Spread / mid"), "quote quality table must expose relative spread");
assert.ok(fs.readFileSync(require("node:path").join(__dirname, "../option_chain_lab.js"), "utf8").includes("STALE >15M"), "stale quote gate must be wired in the Lab");
assert.ok(fs.readFileSync(require("node:path").join(__dirname, "../option_chain_lab.js"), "utf8").includes("executionStress"), "slippage sensitivity must be calculated");
assert.ok(mainHtml.includes('id="optionTableWrap"'), "primary/research strategy table must support compact filtering");
assert.ok(mainHtml.includes('id="toggleResearchRows"'), "research-only strategy rows must be explicitly expandable");
assert.ok(mainHtml.includes('id="advancedResearchTools"'), "non-primary option lookups must be collapsed by default");
assert.ok(mainHtml.includes("width / midpoint"), "quote spread quality definition must be visible");
assert.ok(mainHtml.includes("not a verified exchange quote timestamp"), "fetch time must not be presented as quote time");
assert.ok(!mainHtml.includes('id="budget-qqqCallSpreads"'), "primary risk budget must not be duplicated as a second input");
assert.ok(labHtml.includes('id="historicalModelValidation"'), "Option Chain Lab must show model-fit evidence");
assert.ok(labHtml.includes("+$0.181 / share"), "Option Chain Lab must disclose measured proxy credit gap");
assert.ok(labHtml.includes("No missing quote is interpolated or forward-filled"), "Option Chain Lab must disclose the no-fill gap policy");
assert.ok(labHtml.includes("FAILS_CURRENT_BASE_SCREEN"), "Option Chain Lab must not imply Far-Call performance approval");


// Beginner-friendly holding-time / harvest explainer is collapsed by default and sourced.
assert.ok(mainHtml.includes('id="timeHarvestMeasurementGuide"'), "beginner time / harvest guide must be present");
assert.ok(mainHtml.includes("觀察到條件（Signal）不等於成交（Fill）"), "guide must distinguish a trigger from a fill");
assert.ok(mainHtml.includes("每風險暴露等效日損益"), "guide must describe a time/risk normalized comparison carefully");
assert.ok(mainHtml.includes("首次觀察到 +$1,000 共 9 次，但 5 個持倉交易日內為 0 次"), "guide must retain measured fast-win event count");
assert.ok(mainHtml.includes("$106,392"), "guide must surface the ratio structure tail-risk block");
assert.ok(mainHtml.includes("$100,000 只作標準化分母"), "guide must not present a sum across fixed one-unit episodes as portfolio return or CAGR");
assert.ok(mainHtml.includes('href="https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/101"'), "guide must link the isolated exit-measurement study");
assert.ok(mainHtml.includes("入場後第 20 個觀察交易日（入場日記為 age 0）"), "guide must define the day-20 age convention");

// Three-axis measurement scorecard is visible on both APP surfaces and keeps
// accounting integrity separate from trade accuracy, generality, and integration.
const measurementReport = fs.readFileSync(require("path").join(__dirname, "../QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN148.md"), "utf8");
assert.ok(mainHtml.includes('href="QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN148.md"'), "primary dashboard must link the latest measured scorecard snapshot");
assert.ok(labHtml.includes('href="QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN148.md"'), "Option Chain Lab must link the same latest measured scorecard snapshot");
assert.ok(!mainHtml.includes('href="QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN50.md"'), "primary dashboard must not foreground a stale scorecard");
assert.ok(!labHtml.includes('href="QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN50.md"'), "Option Chain Lab must not foreground a stale scorecard");
for (const [html, id] of [[mainHtml, 'id="measurementScorecard"'], [labHtml, 'id="measurementScorecardLab"']]) {
  assert.ok(html.includes(id), "both APP surfaces must expose the measurement scorecard");
  assert.ok(html.includes("ACCURACY"), "accuracy axis must be shown");
  assert.ok(html.includes("GENERALITY"), "generality axis must be shown");
  assert.ok(html.includes("INTEGRATION"), "integration axis must be shown");
  assert.ok(html.includes("FAIL CURRENT BASE SCREEN"), "negative integration gate must not be hidden");
  assert.ok(html.includes("NOT DEMONSTRATED"), "generality must not be implied from QA success");
  assert.ok(html.includes("−$5,646"), "negative closed-trade screen must be displayed");
  assert.ok(html.includes("−$5,552"), "negative paired NAV comparison must be displayed");
  assert.ok(html.includes("at least 2.00"), "pre-registered downside acceptance bar must be visible");
  assert.ok(html.includes("at least 20%"), "pre-registered deployment acceptance bar must be visible");
}
assert.ok(measurementReport.includes("1,688 pass, 0 fail, 0 blocked"), "latest scorecard must record exact independent ledger coverage");
assert.ok(measurementReport.includes("FAILS CURRENT BASE SCREEN"), "latest measured snapshot must preserve the actual failed baseline screen");
assert.ok(measurementReport.includes("No"), "measurement report must retain a no-promotion disposition");



// AI handoff packet contract: the same active APP state must carry its raw JSON,
// separate measurement axes, and fail-closed human action into the downloadable report.
const aiHandoffSource = fs.readFileSync(require("node:path").join(__dirname, "../ai_handoff.js"), "utf8");
const handoffSandbox = { module: { exports: {} }, window: {} };
vm.runInNewContext(aiHandoffSource, handoffSandbox, { filename: "ai_handoff.js" });
const Handoff = handoffSandbox.module.exports;
assert.equal(typeof Handoff.serialize, "function");
assert.equal(typeof handoffSandbox.window.AiHandoffV1.serialize, "function");
const handoff = Handoff.serialize({
  generatedAt: "2026-10-11T06:00:00.000Z",
  input: { nav: 100000, cashPool: 100000, market: { qqq: 700, vxx: 20, vix: 25, m1: 18, m2: 19, spot_asof: "2026-10-11", term_asof: "2026-10-10", today: "2026-10-11" } },
  result: {
    ok: false, nav: 100000, cashPool: 100000, cashReserveUsd: 10000, totalOptionRiskPool: 3200,
    qqqAdditionalCapitalUsd: 0, vxxAdditionalMarginUsd: 0, plannedCapitalRequiredUsd: null, remainingUnallocatedCashUsd: null,
    market: { status: "BLOCKED", state: "DATA BLOCKED", action: "HOLD", slope: 5.55, reason: "Missing market source evidence." },
    rows: [{ key: "qqqShares", label: "QQQ CORE", current: 0, capacity: null, target: 0, delta: 0, action: "BLOCKED", status: "BLOCKED", reason: "market source missing" }]
  }
}, { qqqCall: { source: "YAHOO_OPTIONS_DELAYED_OR_ESTIMATED", expiry: "2026-11-20" } }, "V3_READ_ONLY_LOCAL_SNAPSHOT · retrieved at sample time");
// Missing numeric fields must remain UNKNOWN/PENDING, never coerce null or blank to $0.00.
{
  const incomplete = Handoff.serialize({
    generatedAt: "2026-10-11T06:00:00.000Z",
    input: { nav: 100000, cashPool: 100000, sizing: { vxxShortBorrowAprPct: " " },
      positionRegister: { summary: {
        count: 1, metadataCompletePnlSubtotal: " ", metadataCompletePnlRows: 1,
        indicativePnlSubtotal: " ", indicativePnlRows: 1, knownPnlSubtotal: " ", knownPnlRows: 1,
        incompletePnlCount: 0, staleMarkCount: 0, markSourceMetadataIncompleteCount: 0, termBlockedCount: 0,
        timezone: "UTC", rows: [{ label: "Whitespace P&L", qty: 1, unit: "shares", entryPrice: " ", markPrice: " ",
          unrealizedPnl: " ", pnlStatus: "INDICATIVE", markFreshness: "UNKNOWN", kind: "STOCK" }]
      } } },
    result: { ok: false, nav: 100000, cashPool: 100000, rows: [{ key: "vxxShortShares", targetNotionalUsd: " " }] }
  }, {
    qqqCall: {
      expiry: "2026-11-20", dte: 40, shortStrike: null, longStrike: null,
      shortBid: null, shortAsk: null, longBid: null, longAsk: null,
      shortQuoteWidthPctMid: null, longQuoteWidthPctMid: " ", credit: null,
      width: null, maxLossPerSpread: null, multiplierAssumption: 100,
      source: "INCOMPLETE_FIXTURE"
    },
    vxxCall: null
  }, "INCOMPLETE_FIXTURE");
  assert.ok(incomplete.includes("width/mid UNKNOWN"), "missing quote width must not be shown as 0.0% mid");
  assert.ok(incomplete.includes("max profit/spread UNKNOWN"), "missing credit must not be shown as $0.00 profit");
  assert.ok(incomplete.includes("expiry breakeven UNKNOWN"), "missing strikes/credit must not create a $0.00 breakeven");
  assert.ok(incomplete.includes("max profit/max loss UNKNOWN"), "missing economics must remain unknown");
  assert.ok(incomplete.includes("estimated annual cost at target notional: PENDING"), "blank target notional/APR must stay pending");
  assert.ok(incomplete.toLowerCase().includes("metadata-complete unrealized p&l subtotal (source not independently authenticated): unknown"),
    "blank metadata subtotal must remain UNKNOWN, not zero");
  assert.ok(incomplete.includes("indicative subtotal: UNKNOWN"), "blank indicative subtotal must remain UNKNOWN, not zero");
  assert.ok(incomplete.includes("UNKNOWN (INDICATIVE)"), "blank row P&L must remain UNKNOWN, not $0.00");
  assert.ok(!incomplete.includes("$0.00 (INDICATIVE)"), "blank row P&L must not look like a true zero result");

  const invalidMultiplier = Handoff.serialize({
    generatedAt: "2026-10-11T06:00:00.000Z",
    input: { nav: 100000, cashPool: 100000, sizing: { vxxShortBorrowAprPct: "" } },
    result: { ok: false, nav: 100000, cashPool: 100000, rows: [] }
  }, {
    qqqCall: {
      expiry: "2026-11-20", dte: 40, shortStrike: 800, longStrike: 810,
      shortBid: 1.25, shortAsk: 1.35, longBid: 0.20, longAsk: 0.30,
      shortQuoteWidthPctMid: 8, longQuoteWidthPctMid: 20, credit: 1.0,
      width: 10, maxLossPerSpread: 900, multiplierAssumption: " ", source: "INVALID_MULTIPLIER_FIXTURE"
    },
    vxxCall: null
  }, "INVALID_MULTIPLIER_FIXTURE");
  assert.ok(invalidMultiplier.includes("max loss/spread UNKNOWN at assumed multiplier UNKNOWN"),
    "missing multiplier must not silently turn into a $100-contract assumption");
  assert.ok(invalidMultiplier.includes("max profit/spread UNKNOWN"), "profit must stay unknown without an explicit multiplier");
  assert.ok(invalidMultiplier.includes("max profit/max loss UNKNOWN"), "risk ratio must stay unknown without an explicit multiplier");
}

for (const required of [
  "QQQ Hybrid — Manual AI Review Pack", "DATA BLOCKED", "Current research lockbox",
  "ACCURACY", "GENERALITY", "INTEGRATION", "FAILS_CURRENT_BASE_SCREEN",
  "USD 0.01", "1.5×", "BLOCK or WAIT", "No broker order", "V3_READ_ONLY_LOCAL_SNAPSHOT",
  "qqqCall", "QQQ_HYBRID_AI_REVIEW_PACK_V1", "~~~~json", "plannedCapitalRequiredUsd"
]) assert.ok(handoff.includes(required), "AI review packet must include " + required);

const handoffHtml = fs.readFileSync(require("node:path").join(__dirname, "../index.html"), "utf8");
const handoffApp = fs.readFileSync(require("node:path").join(__dirname, "../app.js"), "utf8");
const handoffEngine = fs.readFileSync(require("node:path").join(__dirname, "../engine.js"), "utf8");
const positionLedgerSource = fs.readFileSync(require("node:path").join(__dirname, "../position_ledger.js"), "utf8");
const positionLedgerTest = fs.readFileSync(require("node:path").join(__dirname, "position_ledger.test.cjs"), "utf8");
const handoffProtocol = fs.readFileSync(require("node:path").join(__dirname, "../AI_MANUAL_COLLABORATION_PROTOCOL_V1.md"), "utf8");
assert.ok(handoffHtml.includes('id="aiHandoffBtn"'), "top-level AI handoff download must be discoverable");
assert.ok(handoffHtml.includes('id="aiHandoffGuide"'), "manual collaboration steps must be visible in APP");
assert.ok(handoffHtml.includes('id="beginnerDecisionChecklist"'), "beginner decision gates must be visible without adding another dashboard");
assert.ok(handoffHtml.includes('id="vxxShortBorrowAprPct"'), "VXX short carry cost must use an explicit editable APR assumption");
assert.ok(handoffHtml.includes("maximum profit = net credit") && handoffHtml.includes("expiry breakeven"), "beginner checklist must explain option payoff measures");
assert.ok(handoffHtml.includes("isolated QQQ Far-Call overlay fails its base integration screen"), "capacity must not be confused with strategy validation");
assert.ok(handoffHtml.includes('id="positionLedgerCard"'), "position facts/P&L register must be present");
assert.ok(handoffHtml.includes("does not independently authenticate referenced broker documents"), "position register must disclose that source references are not authenticated");
assert.ok(handoffHtml.includes("human attestation, not app-side verification"), "contract checkbox must not imply app-side verification");
assert.ok(handoffApp.includes("METADATA-COMPLETE P&amp;L SUBTOTAL"), "P&L headline must describe metadata completeness, not verified evidence");
assert.ok(handoffApp.includes("OPERATOR-ATTESTED TERMS"), "held-option terms must be described as operator-attested");
assert.ok(handoffApp.includes("MARK STATUS / SOURCE GAPS"), "dashboard must separate mark status flags from source metadata gaps");
assert.ok(handoffApp.includes("markSourceMetadataIncompleteCount"), "dashboard must expose a separate source-gap count");
assert.ok(handoffApp.includes("vxxShortBorrowAprPct"), "operator plan must capture the VXX short borrow cost assumption");
assert.ok(handoffApp.includes("vxxBorrowAnnualStressAtCapacity"), "dashboard must show a 1.5x annual borrow-cost stress");
assert.ok(handoffApp.includes("max profit / max loss"), "primary option table must show reward-to-max-loss");
assert.ok(handoffApp.includes("ELIGIBLE FOR HUMAN REVIEW ONLY"), "regime state must not display BUY as an unqualified action");
assert.ok(aiHandoffSource.includes("VXX short borrow APR assumption"), "AI packet must include borrow APR and its limitation");
assert.ok(aiHandoffSource.includes("expiry breakeven"), "AI packet must report option breakeven arithmetic");
assert.ok(aiHandoffSource.includes("Mark source-metadata gaps"), "AI handoff must separate source gaps from mark status flags");
assert.ok(aiHandoffSource.includes("source not independently authenticated"), "AI handoff must preserve the evidence-authentication limitation");
assert.ok(positionLedgerSource.includes("metadataCompletePnlSubtotal"), "ledger aggregate must use metadata-complete terminology");
assert.ok(positionLedgerSource.includes("markSourceMetadataIncompleteCount"), "ledger must calculate source metadata gaps separately");
assert.ok(positionLedgerSource.includes("ADJUSTED PAYOFF MODEL UNSUPPORTED"), "adjusted held VXX payoff must be explicitly marked unsupported");
assert.ok(positionLedgerSource.includes("!adjustedDetected && identityComplete"), "adjusted held VXX must not pass the sizing terms gate");
assert.ok(handoffApp.includes("BLOCKED · ADJUSTED PAYOFF UNSUPPORTED"), "operator UI must display the adjusted-payoff sizing block");
assert.ok(handoffApp.includes("adjusted deliverable payoff is not modeled"), "operator UI must keep adjusted max loss unknown");
assert.ok(positionLedgerTest.includes("fresh timestamp must not be called stale"), "fresh-but-unreferenced marks must be tested separately from stale marks");
assert.ok(handoffHtml.includes('id="positionUseRegister"'), "position register must require explicit use for sizing");
assert.ok(handoffHtml.includes('id="positionRegisterCompleteConfirmed"'), "position register must require all four categories to be reconciled");
assert.ok(handoffApp.includes("Cannot use register for sizing until you confirm"), "unconfirmed completeness must block register mode");
assert.ok(handoffApp.includes("invalidatePositionRegisterCoverage"), "register edits/imports must invalidate stale completeness confirmation");
assert.ok(handoffApp.includes('completeConfirmed: $("positionRegisterCompleteConfirmed")?.checked === true'), "AI packet must retain completeness confirmation");
assert.ok(handoffHtml.includes('id="positionImportFile"'), "position register must support portable JSON import");
assert.ok(handoffHtml.includes('id="posMarkAsOf" type="text"'), "position mark as-of must accept an explicit timezone-bearing timestamp");
assert.ok(handoffHtml.includes("2026-10-09T16:00:00-04:00"), "position form must show an ISO 8601 timezone example");
assert.ok(positionLedgerSource.includes("AS-OF TIMEZONE UNKNOWN"), "timestamps without explicit timezone must fail closed");
assert.ok(handoffHtml.includes('src="position_ledger.js"'), "position ledger module must load in the app");
assert.ok(handoffApp.includes("positionRegister: positionSummary ?"), "current holdings and AI packet must include position register state");
assert.ok(positionLedgerSource.includes("Gross unrealized mark-to-entry"), "position ledger must disclose P&L scope");
assert.ok(positionLedgerTest.includes("QQQ HYBRID POSITION REGISTER:"), "dedicated position ledger test suite must exist regardless of group count");
assert.ok(handoffEngine.includes("BLOCKED_POSITION_TERMS"), "unverified held terms must block affected sizing rows");
assert.ok(handoffHtml.includes('id="aiHandoffStatus"'), "export feedback must be visible");
assert.ok(handoffHtml.includes('src="ai_handoff.js"'), "handoff module must load before app runtime");
assert.ok(handoffApp.includes("function exportAiReviewPack()"), "APP must create a live-state AI packet");
assert.ok(handoffApp.includes("helper.serialize(lastPlan, candidates, marketMeta)"), "packet must use current plan and candidate evidence");
assert.ok(handoffEngine.includes("shortQuoteWidthPctMid"), "candidate metrics must preserve both-leg relative quote width");
assert.ok(handoffEngine.includes("ADJUSTED_DELIVERABLE_BLOCKED"), "adjusted VXX roots must fail closed in the primary budget");
assert.ok(handoffApp.includes("ADJUSTED VXX ROOT DETECTED — CAPACITY BLOCKED"), "adjusted VXX contract blocker must be visible to the operator");
assert.ok(handoffApp.includes("quote timestamp not verified"), "APP must distinguish chain fetch time from quote timestamp");
assert.ok(handoffApp.includes("configured above"), "primary option risk percentage has one authoritative input");
assert.ok(handoffProtocol.includes("Accuracy"), "durable collaboration protocol must define accuracy");
assert.ok(handoffProtocol.includes("Generality"), "durable collaboration protocol must define generality");
assert.ok(handoffProtocol.includes("Integration"), "durable collaboration protocol must define integration");
assert.ok(handoffProtocol.includes("No order is placed"), "durable protocol must preserve the no-order boundary");

assert.ok(mainHtml.includes("QQQ call-credit max-loss allocation (% NAV)"), "primary percentage input must state it allocates maximum loss, not credit");
assert.ok(mainHtml.includes("VXX call-credit max-loss allocation (% NAV)"), "VXX percentage input must state it allocates maximum loss, not credit");
assert.ok(mainHtml.includes("not premium/credit targets"), "UI must distinguish risk budget from estimated opening credit");
assert.ok(mainHtml.includes("Est. Net Credit ($ / % NAV)"), "allocation table must promise both credit units");
assert.ok(handoffApp.includes("pct(ratioPct(qTotalCredit, nav))"), "QQQ estimated credit must be expressed as % NAV");
assert.ok(handoffApp.includes("pct(ratioPct(vTotalCredit, nav))"), "VXX estimated credit must be expressed as % NAV");
assert.ok(handoffApp.includes("knownOptionLegs === 2"), "combined max-loss KPI must require both option legs");
assert.ok(handoffApp.includes('"PARTIAL · " + usd(knownOptionRisk)'), "one known leg must not be shown as total max loss");
assert.ok(handoffApp.includes("Known leg only · other call-credit leg PENDING; no combined total"), "partial max-loss KPI must disclose missing exposure");
assert.ok(handoffApp.includes("Waiting for two valid call-credit quotes"), "missing both option legs must remain pending");
assert.ok(handoffApp.includes('amount: knownOptionLegs === 2 && pool !== null ? Math.max(0, pool - knownOptionRisk) : null'), "unused risk room must remain PENDING until both option legs and the risk pool are valid");
const statusOfBlockIndex = handoffApp.indexOf('if (row.action === "BLOCKED" || String(row.status || "").startsWith("BLOCKED")) return "BLOCKED · SEE REASON";');
const statusOfPendingIndex = handoffApp.indexOf('if (quantity === null || !priceKnown) return "QUOTE / DATA PENDING";', statusOfBlockIndex);
assert.ok(statusOfBlockIndex >= 0 && statusOfPendingIndex > statusOfBlockIndex, "explicit model/contract blocks must not be mislabeled as missing quotes");


// Handoff regression: allow only recent, operator-attested standard CALL contracts.
{
  const fixture=Lab.SAMPLE;
  const quotes=Lab.calculateVerticals("QQQ_CALL",fixture.chains.QQQ_CALL,100,3200);
  const q2=quotes.candidates.find(c=>c.key==="799C/810C");
  const meta={
    sourceType:"USER_SCREENSHOT_TRANSCRIPTION",sourceName:"Broker screenshot, manually transcribed",sourceUrl:"",
    observedAt:"2026-10-13T08:50:00Z",timezone:"UTC",contractSymbol:"QQQ",
    contractStatus:"STANDARD_TERMS_RECORDED",deliverableNote:"100 shares",contractEvidenceUrl:"https://www.theocc.com/"
  };
  const now=Date.parse("2026-10-13T09:00:00Z");
  const h=Lab.buildPrimaryPlannerHandoff(meta,"2026-11-20","QQQ_CALL",q2,100,fixture.chains.QQQ_CALL.length,false,true,now);
  assert.equal(h.ok,true);
  assert.equal(h.candidate.shortContractSymbol,"QQQ261120C00799000");
  assert.equal(h.candidate.longContractSymbol,"QQQ261120C00810000");
  assert.equal(h.candidate.maxLossPerSpread,973);
  assert.equal(h.candidate.candidateStatus,"HUMAN_REVIEW_REQUIRED");
  assert.equal(Lab.buildPrimaryPlannerHandoff(meta,"2026-11-20","QQQ_PUT",q2,100,3,false,true,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff(meta,"2026-11-20","QQQ_CALL",q2,100,3,false,false,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff(meta,"2026-11-20","QQQ_CALL",q2,100,3,true,true,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff({...meta,sourceType:"PUBLIC_DATA"},"2026-11-20","QQQ_CALL",q2,100,3,false,true,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff({...meta,observedAt:"2026-10-13T08:40:00Z"},"2026-11-20","QQQ_CALL",q2,100,3,false,true,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff({...meta,observedAt:"2026-10-13T08:50"},"2026-11-20","QQQ_CALL",q2,100,3,false,true,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff({...meta,contractSymbol:"VXX2"},"2026-11-20","QQQ_CALL",q2,100,3,false,true,now).ok,false);
  assert.equal(Lab.buildPrimaryPlannerHandoff(meta,"2026-11-20","QQQ_CALL",q2,50,3,false,true,now).ok,false);
}
{
  const engineSource=fs.readFileSync(require("path").join(__dirname,"../engine.js"),"utf8");
  const appSource=fs.readFileSync(require("path").join(__dirname,"../app.js"),"utf8");
  const htmlSource=fs.readFileSync(require("path").join(__dirname,"../option_chain_lab.html"),"utf8");
  assert.ok(engineSource.includes("validatePrimaryOptionHandoff"));
  assert.ok(engineSource.includes("PENDING_OPTION_EVIDENCE"));
  assert.ok(appSource.includes("OPTION_HANDOFF_PREFIX"));
  assert.ok(htmlSource.includes('id="sendToMain"'));
  assert.ok(htmlSource.includes('id="attestStandard"'));
}


// Cross-layer integration: the exact Lab-produced handoff must be accepted by the planner,
// and a tampered/stale packet must not create capacity even though its arithmetic still exists.
{
  const engineSandbox = { module: { exports: {} } };
  vm.runInNewContext(fs.readFileSync(require.resolve("../engine.js"), "utf8"), engineSandbox, { filename: "engine.js" });
  const E = engineSandbox.module.exports;
  const now = Date.now();
  const today = new Date(now).toISOString().slice(0, 10);
  const todayMs = Date.parse(today + "T00:00:00Z");
  const expiry = new Date(todayMs + 45 * 86400000).toISOString().slice(0, 10);
  const observedAt = new Date(now - 5 * 60000).toISOString();
  function handoffFor(chainKey, root, rows, pairKey) {
    const values = Lab.calculateVerticals(chainKey, rows, 100, 3200);
    const selected = values.candidates.find(c => c.key === pairKey);
    assert.ok(selected, "integration fixture must contain " + pairKey);
    const meta = {
      sourceType: "USER_SCREENSHOT_TRANSCRIPTION",
      sourceName: "Deterministic fixture, not authenticated evidence",
      sourceUrl: "",
      observedAt,
      timezone: "UTC",
      contractSymbol: root,
      contractStatus: "STANDARD_TERMS_RECORDED",
      deliverableNote: "100 shares",
      contractEvidenceUrl: "https://www.theocc.com/"
    };
    const result = Lab.buildPrimaryPlannerHandoff(meta, expiry, chainKey, selected, 100, rows.length, false, true, now);
    assert.equal(result.ok, true, "Option Chain Lab must produce a structurally valid handoff for " + chainKey);
    return result.candidate;
  }
  const qqqCandidate = handoffFor("QQQ_CALL", "QQQ", s.chains.QQQ_CALL, "799C/810C");
  const vxxCandidate = handoffFor("VXX_CALL", "VXX", s.chains.VXX_CALL, "21C/24C");
  const qqqStrategy = E.OPTION_STRATEGIES.find(x => x.key === "qqqCallSpreads");
  const vxxStrategy = E.OPTION_STRATEGIES.find(x => x.key === "vxxCallSpreads");
  assert.equal(E.validatePrimaryOptionHandoff(qqqCandidate, now).ok, true);
  assert.equal(E.validatePrimaryOptionHandoff(vxxCandidate, now).ok, true);
  assert.equal(E.candidateRisk(qqqStrategy, qqqCandidate, null, now).riskPerUnit, 973);
  assert.equal(E.candidateRisk(vxxStrategy, vxxCandidate, null, now).riskPerUnit, 276);

  const sizingInput = {
    market: { qqq: 748, vxx: 17.23, vix: 18, m1: 18, m2: 19, term_asof: today, spot_asof: today, today, term_source: "FIXTURE" },
    nav: 100000,
    cashPool: 100000,
    sizing: { qqqCorePct: 42, vxxNormalPct: 18, vxxHighPct: 10, totalOptionRiskPct: 3.2, qqqCallRiskPct: 1.2, vxxCallRiskPct: 2, vixHigh: 28, termSafe: 5, maxTermAgeDays: 4 },
    holdings: {},
    candidates: { qqqCall: qqqCandidate, vxxCall: vxxCandidate },
    permissions: {}
  };
  const cleanPlan = E.calculatePortfolio(sizingInput);
  const row = (plan, key) => {
    const found = plan.rows.find(x => x.key === key);
    assert.ok(found, "missing plan row " + key);
    return found;
  };
  assert.equal(row(cleanPlan, "qqqCallSpreads").riskPerUnit, 973);
  assert.equal(row(cleanPlan, "qqqCallSpreads").capacity, 1);
  assert.equal(row(cleanPlan, "vxxCallSpreads").riskPerUnit, 276);
  assert.equal(row(cleanPlan, "vxxCallSpreads").capacity, 7);
  assert.equal(cleanPlan.totalRequestedRiskBudgetsUsd, 3200);

  const tampered = { ...qqqCandidate, credit: qqqCandidate.credit + 0.01 };
  const blockedPlan = E.calculatePortfolio({ ...sizingInput, candidates: { qqqCall: tampered, vxxCall: vxxCandidate } });
  assert.equal(row(blockedPlan, "qqqCallSpreads").riskPerUnit, null);
  assert.equal(row(blockedPlan, "qqqCallSpreads").capacity, null);
  assert.equal(row(blockedPlan, "qqqCallSpreads").action, "PENDING");
  assert.equal(row(blockedPlan, "qqqCallSpreads").riskSource, "PENDING_OPTION_EVIDENCE");
  assert.equal(row(blockedPlan, "vxxCallSpreads").capacity, 7, "a blocked QQQ candidate must not dilute valid VXX allocation");
  assert.equal(blockedPlan.totalRequestedRiskBudgetsUsd, 2000);

  const stale = { ...qqqCandidate, quoteObservedAt: new Date(now - 16 * 60000).toISOString() };
  const stalePlan = E.calculatePortfolio({ ...sizingInput, candidates: { qqqCall: stale, vxxCall: vxxCandidate } });
  assert.equal(row(stalePlan, "qqqCallSpreads").capacity, null);
  assert.equal(row(stalePlan, "qqqCallSpreads").status, "PENDING");
  assert.equal(row(stalePlan, "vxxCallSpreads").capacity, 7);
}


// Prospective journal: quote snapshots and outcome events are append-only, separated, and never authorize orders.
{
  const journalSource = fs.readFileSync(require.resolve("../paper_observation_journal.js"), "utf8");
  const journalSandbox = { module: { exports: {} } };
  vm.runInNewContext(journalSource, journalSandbox, { filename: "paper_observation_journal.js" });
  const J = journalSandbox.module.exports;
  const now = Date.parse("2026-10-13T09:00:00Z");
  const q = J.createQuoteObservation({
    eventId: J.nextEventId("QUOTE", 0, now), recordedAt: new Date(now).toISOString(),
    chainKey: "QQQ_CALL", expiration: "2026-11-20",
    sourceMeta: { sourceType: "BROKER_EXPORT", sourceName: "operator-entered test metadata", sourceUrl: "", observedAt: "2026-10-13T08:55:00Z", timezone: "UTC", contractSymbol: "QQQ", contractStatus: "STANDARD_TERMS_RECORDED", deliverableNote: "100 shares", contractEvidenceUrl: "https://www.theocc.com/" },
    provenanceStatus: "RECORDED_REVIEW_REQUIRED", freshnessStatus: "AS-OF ≤15M", quoteAgeMinutes: 5, provenanceComplete: true,
    manuallyEdited: false, multiplier: 100, riskBudgetUsd: 3200, plannedQuantity: 1, intendedLimitCreditPerShare: 1.2,
    candidate: { key: "799C/810C", shortStrike: 799, longStrike: 810, width: 11, shortBid: 3.16, shortAsk: 3.18, longBid: 1.87, longAsk: 1.89, credit: 1.27, maxLoss: 973, maxProfit: 127, breakEven: 800.27, isCall: true },
    chainRows: [{strike:799,bid:3.16,ask:3.18,delta:0.1456},{strike:810,bid:1.87,ask:1.89,delta:0.0954}], note: "synthetic test only"
  });
  assert.equal(q.ok, true);
  assert.equal(q.event.status, "QUOTE_SNAPSHOT_ONLY_NOT_FILL");
  assert.equal(q.event.ordersAuthorized, false);
  assert.equal(q.event.dataAuthentication, "NOT_INDEPENDENTLY_AUTHENTICATED");
  assert.equal(q.event.candidateContractSymbols.short, "QQQ261120C00799000");
  assert.equal(J.makeStandardOptionSymbol("QQQ","2026-11-20","P",799), "QQQ261120P00799000", "PUT observations must preserve the option right");
  const env0 = J.emptyEnvelope(new Date(now).toISOString());
  const appended = J.appendEvent(env0, q.event);
  assert.equal(appended.ok, true);
  assert.equal(J.summarize(appended.envelope).quoteObservations, 1);
  assert.equal(J.summarize(appended.envelope).metadataAndFreshnessPassAtCapture, 1);
  const invalidStamp = J.createQuoteObservation({ ...q.event, eventId: "bad", recordedAt: "2026-10-13T09:00:00" });
  assert.equal(invalidStamp.ok, false);
  const staleQuote = J.createQuoteObservation({ ...q.event, eventId: "stale", provenanceComplete: false, freshnessStatus: "STALE >15M" });
  assert.equal(staleQuote.ok, true);
  assert.equal(staleQuote.event.provenanceCompleteAtCapture, false);
  const noTzFill = J.createOutcomeEvent({ eventId:"out-no-tz", recordedAt:new Date(now+60000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.24, filledQuantity:1, outcomeAt:"2026-10-13T09:01:00", outcomeReference:"statement row 1" },q.event);
  assert.equal(noTzFill.ok,false);
  const noRefFill = J.createOutcomeEvent({ eventId:"out-no-ref", recordedAt:new Date(now+60000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.24, filledQuantity:1, outcomeAt:"2026-10-13T09:01:00Z", outcomeReference:"" },q.event);
  assert.equal(noRefFill.ok,false);
  const fill = J.createOutcomeEvent({ eventId:"out-fill", recordedAt:new Date(now+60000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.22, filledQuantity:2, outcomeAt:"2026-10-13T09:01:00Z", outcomeReference:"statement row label 1", filledShortSymbol:q.event.candidateContractSymbols.short, filledLongSymbol:q.event.candidateContractSymbols.long },q.event);
  assert.equal(fill.ok,true);
  assert.equal(fill.event.dataAuthentication,"OPERATOR_REPORTED_NOT_AUTHENTICATED");
  const withFill = J.appendEvent(appended.envelope,fill.event);
  assert.equal(withFill.ok,true);
  const forgedOutcomeSchema = JSON.parse(JSON.stringify(withFill.envelope));
  forgedOutcomeSchema.events[1].schemaVersion = 2;
  assert.equal(J.parseEnvelope(forgedOutcomeSchema).ok,false,"unsupported outcome event schema version must be rejected");
  const summary = J.summarize(withFill.envelope);
  assert.equal(summary.operatorReportedFillCount,1);
  assert.equal(summary.eligibleReportedFillComparisons,1);
  assert.equal(summary.meanReportedFillCreditGapPerShare, -0.05);
  assert.equal(summary.meanReportedFillCreditGapPerContractUsd, -5);
  assert.equal(summary.fillComparisons[0].gapTotalUsd,-10);

  assert.equal(summary.nonComparableReportedFillCount,0);
  assert.equal(summary.fillComparisons[0].quoteToFillMinutes,6);
  // Fill records are retained, but exact contract and quote/fill-time alignment gate the measured comparison.
  const boundaryFill = J.createOutcomeEvent({ eventId:"out-boundary", recordedAt:new Date(now+17*60000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.22, filledQuantity:1, outcomeAt:"2026-10-13T09:10:00Z", outcomeReference:"boundary test", filledShortSymbol:q.event.candidateContractSymbols.short, filledLongSymbol:q.event.candidateContractSymbols.long },q.event);
  assert.equal(boundaryFill.ok,true);
  const boundarySummary = J.summarize(J.appendEvent(appended.envelope,boundaryFill.event).envelope);
  assert.equal(boundarySummary.eligibleReportedFillComparisons,1,"exactly 15 minutes is inside the inclusive boundary");
  const lateFill = J.createOutcomeEvent({ eventId:"out-late", recordedAt:new Date(now+13*60000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.22, filledQuantity:1, outcomeAt:"2026-10-13T09:11:00Z", outcomeReference:"late fill test", filledShortSymbol:q.event.candidateContractSymbols.short, filledLongSymbol:q.event.candidateContractSymbols.long },q.event);
  assert.equal(lateFill.ok,true);
  const lateSummary = J.summarize(J.appendEvent(appended.envelope,lateFill.event).envelope);
  assert.equal(lateSummary.operatorReportedFillCount,1);
  assert.equal(lateSummary.eligibleReportedFillComparisons,0);
  assert.equal(lateSummary.nonComparableReportedFillCount,1);
  assert.equal(lateSummary.comparisonExclusionCounts.QUOTE_FILL_GAP_OVER_15M,1);
  const preQuoteFill = J.createOutcomeEvent({ eventId:"out-pre-quote", recordedAt:new Date(now+14*60000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.22, filledQuantity:1, outcomeAt:"2026-10-13T08:54:00Z", outcomeReference:"pre-quote fill test", filledShortSymbol:q.event.candidateContractSymbols.short, filledLongSymbol:q.event.candidateContractSymbols.long },q.event);
  assert.equal(preQuoteFill.ok,true);
  const preQuoteSummary = J.summarize(J.appendEvent(appended.envelope,preQuoteFill.event).envelope);
  assert.equal(preQuoteSummary.eligibleReportedFillComparisons,0);
  assert.equal(preQuoteSummary.comparisonExclusionCounts.FILL_PRECEDES_QUOTE,1);
  const wrongContractFill = J.createOutcomeEvent({ eventId:"out-wrong-contract", recordedAt:new Date(now+120000).toISOString(), outcomeType:"OPERATOR_REPORTED_FILL", fillCreditPerShare:1.22, filledQuantity:1, outcomeAt:"2026-10-13T09:01:00Z", outcomeReference:"wrong contract test", filledShortSymbol:"QQQ261120C00800000", filledLongSymbol:q.event.candidateContractSymbols.long },q.event);
  assert.equal(wrongContractFill.ok,true,"a reported outcome is retained even if it is not comparable");
  const wrongContractSummary = J.summarize(J.appendEvent(appended.envelope,wrongContractFill.event).envelope);
  assert.equal(wrongContractSummary.eligibleReportedFillComparisons,0);
  assert.equal(wrongContractSummary.comparisonExclusionCounts.FILLED_CONTRACT_SYMBOL_MISMATCH,1);
  const forgedSymbols = JSON.parse(JSON.stringify(appended.envelope));
  forgedSymbols.events[0].candidateContractSymbols.short = "QQQ261120C00800000";
  assert.equal(J.parseEnvelope(forgedSymbols).ok,false,"tampered quote OCC symbol derivation must be rejected");

  const forgedMetadata = JSON.parse(JSON.stringify(appended.envelope));
  forgedMetadata.events[0].sourceMeta.sourceName = "";
  assert.equal(J.parseEnvelope(forgedMetadata).ok,false,"metadata-pass flag cannot override missing required source metadata");
  const forgedAge = JSON.parse(JSON.stringify(appended.envelope));
  forgedAge.events[0].quoteAgeMinutes = 16;
  assert.equal(J.parseEnvelope(forgedAge).ok,false,"metadata-pass flag cannot override stale quote age");
  const forgedCandidate = JSON.parse(JSON.stringify(appended.envelope));
  forgedCandidate.events[0].candidate.credit = 2;
  assert.equal(J.parseEnvelope(forgedCandidate).ok,false,"candidate credit must reconcile to captured short Bid minus wing Ask");

  const forgedProvenanceFlag = JSON.parse(JSON.stringify(appended.envelope));
  forgedProvenanceFlag.events[0].provenanceCompleteAtCapture = "true";
  assert.equal(J.parseEnvelope(forgedProvenanceFlag).ok,false,"string provenance flags must not count as metadata/time pass");
  const forgedManualEditFlag = JSON.parse(JSON.stringify(appended.envelope));
  forgedManualEditFlag.events[0].manuallyEdited = "true";
  assert.equal(J.parseEnvelope(forgedManualEditFlag).ok,false,"string manual-edit flags must not bypass manual-edit rejection");
  const forgedQuoteSchema = JSON.parse(JSON.stringify(appended.envelope));
  forgedQuoteSchema.events[0].schemaVersion = 2;
  assert.equal(J.parseEnvelope(forgedQuoteSchema).ok,false,"unsupported quote event schema version must be rejected");

  const forgedModelPass = J.createQuoteObservation({ ...q.event, eventId:"model-claimed-complete", sourceMeta:{...q.event.sourceMeta,sourceType:"MODEL_DERIVED"}, provenanceComplete:true });
  assert.equal(forgedModelPass.ok,false,"model-derived quote cannot claim metadata/time pass");
  const hypothetical = J.createOutcomeEvent({ eventId:"out-paper", recordedAt:new Date(now+120000).toISOString(), outcomeType:"PAPER_ASSUMED_FILL", fillCreditPerShare:1.25, filledQuantity:1, outcomeAt:"", outcomeReference:"", note:"hypothesis only" },q.event);
  assert.equal(hypothetical.ok,true);
  const withHypothesis = J.appendEvent(withFill.envelope,hypothetical.event);
  assert.equal(withHypothesis.ok,true);
  assert.equal(J.summarize(withHypothesis.envelope).eligibleReportedFillComparisons,1,"hypothetical fills never contaminate reported-fill comparison");
  assert.equal(J.summarize(withHypothesis.envelope).hypotheticalFillCount,1);
  assert.equal(J.appendEvent(withHypothesis.envelope,q.event).ok,false,"duplicate IDs are rejected");
  assert.equal(J.parseEnvelope(JSON.stringify(withHypothesis.envelope)).ok,true,"journal JSON round-trips");
  const broken = JSON.parse(JSON.stringify(withHypothesis.envelope));
  broken.events[1].observationId = "missing-parent";
  assert.equal(J.parseEnvelope(broken).ok,false,"dangling outcomes are rejected");
  const merged = J.mergeEnvelopes(withHypothesis.envelope, JSON.stringify(withFill.envelope));
  assert.equal(merged.ok,true);
  assert.equal(merged.duplicates,2);
  assert.equal(merged.envelope.events.length,3);
  assert.equal(J.createOutcomeEvent({eventId:"no-trade",recordedAt:new Date(now+120000).toISOString(),outcomeType:"NO_TRADE"},q.event).ok,true);
  const htmlSource = fs.readFileSync(require.resolve("../option_chain_lab.html"), "utf8");
  const appSource = fs.readFileSync(require.resolve("../option_chain_lab.js"), "utf8");
  assert.ok(htmlSource.includes('id="paperObservationJournal"'));
  assert.ok(htmlSource.includes('id="paperJournalControls"'), "journal controls should be collapsed by default to avoid dashboard bloat");
  assert.ok(htmlSource.includes('id="paperOutcomeShortSymbol"'), "fill comparisons require the reported short-leg contract symbol");
  assert.ok(htmlSource.includes('id="paperOutcomeLongSymbol"'), "fill comparisons require the reported long-leg contract symbol");
  assert.ok(htmlSource.includes('id="recordPaperObservation"'));
  assert.ok(htmlSource.includes('id="importPaperJournal"'));
  assert.ok(htmlSource.includes('src="paper_observation_journal.js"'));
  assert.ok(appSource.includes("PaperJournal.createQuoteObservation"));
  assert.ok(appSource.includes("renderPaperJournal"));
}


// QQQ put ratio backspread: N lower-strike LONG puts for each higher-strike SHORT put.
{
  const ratio = Lab.calculatePutBackspread({
    expiry:"2026-11-20", longPerShort:2, packages:1, multiplier:100, budget:1000,
    contractSymbol:"QQQ", contractStatus:"STANDARD_TERMS_RECORDED",
    longPut:{strike:90,bid:2.00,ask:2.25,delta:-0.12},
    shortPut:{strike:100,bid:5.00,ask:5.20,delta:-0.25}
  });
  assert.equal(ratio.ok,true);
  assert.equal(ratio.ratio,"2:1");
  assert.equal(ratio.longContracts,2);
  assert.equal(ratio.shortContracts,1);
  near(ratio.creditPerShare,.50,"2:1 put backspread net credit/share");
  near(ratio.totalNetOpeningCashUsd,50,"2:1 put backspread opening cash");
  near(ratio.maxLossPerPackageUsd,950,"loss valley at lower long strike");
  near(ratio.totalMaxLossUsd,950,"planned maximum expiry loss");
  near(ratio.pnlAtZeroPerPackageUsd,8050,"expiry P&L at QQQ zero");
  near(ratio.pnlAtLongStrikePerPackageUsd,-950,"expiry P&L at lower long strike");
  near(ratio.pnlAtShortStrikePerPackageUsd,50,"expiry P&L at short strike");
  assert.equal(ratio.budgetCapacityPackages,1);
  assert.deepEqual(JSON.parse(JSON.stringify(ratio.breakevens.map(x=>x.price===undefined?x.label:x.price))),[80.5,99.5]);
  near(ratio.slippageStress[1].creditPerShare,.425,"$0.025 adverse price shift on each quote side for N=2");
  near(ratio.slippageStress[1].maxLossPerPackageUsd,957.5,"stressed maximum expiry loss");
  const three = Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:3,multiplier:100,budget:3200,
    contractSymbol:"QQQ",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  });
  assert.equal(three.longContracts,6);
  assert.equal(three.shortContracts,3);
  near(three.totalMaxLossUsd,2850,"3 packages have 6 long and 3 short contracts");
  const oneToOne = Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:1,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  });
  assert.equal(oneToOne.ratio,"1:1");
  near(oneToOne.pnlAtZeroPerPackageUsd,-725,"1:1 lower tail loss equals the long-strike valley");
  near(oneToOne.pnlAtZeroPerPackageUsd,oneToOne.pnlAtLongStrikePerPackageUsd,"1:1 put vertical has no extra crash convexity below the long strike");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",longPut:{strike:100,bid:2,ask:2.25},shortPut:{strike:90,bid:5,ask:5.2}
  }).ok,false,"put backspread strike direction must not be reversed");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"VXX",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"ratio helper rejects an incorrectly labelled underlying root");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ1",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"QQQ-prefixed adjusted/ambiguous roots must not pass as standard QQQ");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ261120P00090000",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,true,"a complete standard OCC symbol may prove the QQQ root when it matches one selected leg");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ261218P00090000",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"a full OCC symbol with a different expiry must be rejected");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ261120C00090000",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"a full CALL symbol cannot identify a PUT chain");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:1,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",longPut:{strike:90,bid:1,ask:1},shortPut:{strike:100,bid:12,ask:12.5}
  }).ok,false,"net credit greater than spread width is a quote anomaly, not zero risk");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:1,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",longPut:{strike:90,bid:1,ask:1},shortPut:{strike:100,bid:11,ask:11.5}
  }).ok,false,"net credit at the spread-width boundary is blocked as an arbitrage/quote anomaly");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",contractStatus:"ADJUSTED_TERMS_RECORDED",
    longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"adjusted contract terms remain blocked");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"underlying contract root is required");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"2026-11-20",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",longPut:{strike:90,bid:2,ask:null},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"missing long quote fields cannot become a ratio quote");
  assert.equal(Lab.calculatePutBackspread({
    expiry:"bad",longPerShort:2,packages:1,multiplier:100,budget:1000,
    contractSymbol:"QQQ",longPut:{strike:90,bid:2,ask:2.25},shortPut:{strike:100,bid:5,ask:5.2}
  }).ok,false,"invalid expiry is blocked");
}
assert.ok(fs.readFileSync(require.resolve("../option_chain_lab.html"),"utf8").includes('id="qqqPutRatioDetails"'),"put ratio UI must be collapsed by default");
{
  const labSource=fs.readFileSync(require.resolve("../option_chain_lab.js"),"utf8");
  const mainHtml=fs.readFileSync(require.resolve("../index.html"),"utf8");
  assert.ok(mainHtml.includes('href="option_chain_lab.html?chain=QQQ_PUT"'), "main desk must expose a direct QQQ PUT research route");
  assert.ok(labSource.includes('new URLSearchParams(win.location&&win.location.search||"").get("chain")'), "deep link must select a chain without fabricating quotes");
  assert.ok(labSource.includes('if(Object.prototype.hasOwnProperty.call(chains,requestedChain))active=requestedChain'), "requested chain must be validated against known chain keys");
}

console.log("option_chain_lab=PASS; put_ratio_backspread=PASS; ai_handoff=PASS; compact_ui=PASS; quote_quality=PASS; position_register=PASS; risk_credit_units=PASS; partial_risk_kpi=PASS; paper_observation_journal=PASS");
