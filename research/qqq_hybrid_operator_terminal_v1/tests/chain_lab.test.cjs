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
console.log("option_chain_lab=PASS");
