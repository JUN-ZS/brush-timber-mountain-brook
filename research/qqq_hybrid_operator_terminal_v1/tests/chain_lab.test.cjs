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

// VXX CALL values and sizing must follow the same uploaded fixture.
const vcall = Lab.calculateVerticals("VXX_CALL",s.chains.VXX_CALL,100,3200);
const vc = vcall.candidates.find(x=>x.key==="21C/24C");
assert.ok(vc);
near(vc.credit,.24,"VXX 21/24 net credit per share");
near(vc.maxProfit,24,"VXX 21/24 max profit");
near(vc.maxLoss,276,"VXX 21/24 max loss");
near(vc.breakEven,21.24,"VXX 21/24 breakeven");

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
  'VXX,CALL,21,0.58,0.72,0.2698,2026-11-20,PUBLIC_DATA,"Example, feed",https://example.com/data,2026-10-09T15:45,America/New_York,VXX,STANDARD_TERMS_RECORDED,"100 shares",https://example.com/occ\n' +
  'VXX,CALL,24,0.24,0.34,0.1731,2026-11-20,PUBLIC_DATA,"Example, feed",https://example.com/data,2026-10-09T15:45,America/New_York,VXX,STANDARD_TERMS_RECORDED,"100 shares",https://example.com/occ';
const rich = Lab.parseCsv(richCsv);
assert.equal(rich.total,2);
assert.equal(rich.expiration,"2026-11-20");
assert.equal(rich.metadata.sourceType,"PUBLIC_DATA");
assert.equal(rich.metadata.sourceName,"Example, feed");
assert.equal(rich.chainMetadata.VXX_CALL.contractSymbol,"VXX");
assert.equal(rich.chainMetadata.VXX_CALL.deliverableNote,"100 shares");
assert.equal(rich.metadataConflicts.length,0);
assert.equal(Lab.parseCsv('symbol,side,strike,bid,ask,delta\nQQQ,CALL,799,3.16,3.18,0.1456').expiration,"","legacy CSV must not inherit the UI's prior expiry");

const goodMeta={sourceType:"PUBLIC_DATA",sourceName:"Example feed",sourceUrl:"https://example.com/data",observedAt:"2026-10-09T15:45",timezone:"America/New_York",contractSymbol:"VXX",contractStatus:"STANDARD_TERMS_RECORDED",deliverableNote:"100 shares",contractEvidenceUrl:"https://example.com/occ"};
const provGood=Lab.assessProvenance(goodMeta,"2026-11-20",2,false);
assert.equal(provGood.complete,true);
assert.equal(provGood.ordersAuthorized,false,"complete metadata must never authorize orders");
assert.equal(Lab.assessProvenance(goodMeta,"2026-11-20",2,true).status,"MANUAL_EDIT_RECHECK");
assert.equal(Lab.assessProvenance({...goodMeta,sourceType:"MODEL_DERIVED"},"2026-11-20",2,false).status,"MODEL_ONLY");
assert.equal(Lab.assessProvenance({...goodMeta,contractStatus:"UNKNOWN"},"2026-11-20",2,false).complete,false);
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


// Three-axis measurement scorecard is visible on both APP surfaces and keeps
// accounting integrity separate from trade accuracy, generality, and integration.
const measurementReport = fs.readFileSync(require("path").join(__dirname, "../QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN50.md"), "utf8");
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
assert.ok(measurementReport.includes("1,688 / 1,688"), "measurement report must record independent ledger coverage");
assert.ok(measurementReport.includes("FAILS_CURRENT_BASE_SCREEN"), "measurement report must preserve the actual failed baseline screen");
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
assert.ok(handoffHtml.includes('id="positionLedgerCard"'), "position facts/P&L register must be present");
assert.ok(handoffHtml.includes("does not independently authenticate referenced broker documents"), "position register must disclose that source references are not authenticated");
assert.ok(handoffHtml.includes("human attestation, not app-side verification"), "contract checkbox must not imply app-side verification");
assert.ok(handoffApp.includes("METADATA-COMPLETE P&amp;L SUBTOTAL"), "P&L headline must describe metadata completeness, not verified evidence");
assert.ok(handoffApp.includes("OPERATOR-ATTESTED TERMS"), "held-option terms must be described as operator-attested");
assert.ok(handoffApp.includes("MARK STATUS / SOURCE GAPS"), "dashboard must separate mark status flags from source metadata gaps");
assert.ok(handoffApp.includes("markSourceMetadataIncompleteCount"), "dashboard must expose a separate source-gap count");
assert.ok(aiHandoffSource.includes("Mark source-metadata gaps"), "AI handoff must separate source gaps from mark status flags");
assert.ok(aiHandoffSource.includes("source not independently authenticated"), "AI handoff must preserve the evidence-authentication limitation");
assert.ok(positionLedgerSource.includes("metadataCompletePnlSubtotal"), "ledger aggregate must use metadata-complete terminology");
assert.ok(positionLedgerSource.includes("markSourceMetadataIncompleteCount"), "ledger must calculate source metadata gaps separately");
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
assert.ok(positionLedgerTest.includes("8 TEST GROUPS PASS"), "dedicated position ledger tests must exist");
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

console.log("option_chain_lab=PASS; ai_handoff=PASS; compact_ui=PASS; quote_quality=PASS; position_register=PASS; risk_credit_units=PASS; partial_risk_kpi=PASS");
