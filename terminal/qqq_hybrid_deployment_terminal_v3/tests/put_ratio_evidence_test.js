import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,"..");
const apiPath=path.join(root,"put_ratio_evidence.js");
const snapshotPath=path.join(root,"put_ratio_evidence_v1.json");
const moduleBox={exports:{}};
vm.runInNewContext(fs.readFileSync(apiPath,"utf8"),{module:moduleBox,console});
const P=moduleBox.exports;
const evidence=JSON.parse(fs.readFileSync(snapshotPath,"utf8"));

assert.equal(P.validateSnapshot(evidence).ok,true,"source-pinned evidence snapshot should validate");
assert.equal(evidence.metadata.optionEpisodes,62);
assert.equal(evidence.curve.session_dates.length,1960);
assert.equal(Object.keys(evidence.curve.cumulative_pnl_usd_by_policy).length,13);

const baseline=P.evaluate(evidence,{
  nav:80000,direction:"SHORT_HEAVY",n:5,policyId:"BASE_DTE7_CLOSE_SHORT_RISK",
  riskPct:1,profitPct:1,currentPnl:"",age:"",dte:"",rv20:"",horizon:5,combinedReview:false
});
assert.equal(baseline.evidenceStatus,"AVAILABLE_RESEARCH_ONLY");
assert.equal(baseline.history.episodes,62);
assert.equal(baseline.history.resolved,62);
assert.ok(Math.abs(baseline.history.winRatePct-95.1613)<0.001);
assert.equal(baseline.history.netPnlUsd,18067.6);
assert.equal(baseline.tail.worstUsd,214696.9);
assert.equal(baseline.tail.wholeUnits,0,"$80k / 1% terminal-tail budget must not permit one 1:5 unit");
assert.ok(Math.abs(baseline.serialCurve.maxPct-(-8.2796))<0.001);
assert.equal(baseline.serialCurve.maxPeakDate,"2025-04-01");
assert.equal(baseline.serialCurve.maxTroughDate,"2025-04-08");
assert.equal(baseline.serialCurve.missingMarks,11);
const dd3=baseline.serialCurve.levels.find(x=>x.level===3);
assert.equal(dd3.count,4);
assert.equal(dd3.years,4);
assert.equal(dd3.allYears,8);
assert.equal(dd3.yearIncidencePct,50,"four of eight observed calendar years had a >=3% drawdown cycle");
const dd5=baseline.serialCurve.levels.find(x=>x.level===5);
assert.deepEqual(Array.from(dd5.eventYears),["2024","2025"]);
assert.equal(dd5.yearIncidencePct,25,"two of eight observed calendar years had a >=5% drawdown cycle");
assert.equal(baseline.profitTarget.navTargetUsd,800);
assert.equal(baseline.profitTarget.directFixedTargetUsd,800);
assert.equal(baseline.profitTarget.directPolicy.triggerCount,6);

const target800=P.evaluate(evidence,{
  nav:80000,direction:"SHORT_HEAVY",n:5,policyId:"TP_USD_800_CLOSE_SHORT_RISK",
  riskPct:1,profitPct:1,currentPnl:900,age:3,dte:25,rv20:40,horizon:5,combinedReview:true
});
assert.equal(target800.history.winRatePct,95.16);
assert.equal(target800.profitTarget.directPolicy.id,"TP_USD_800_CLOSE_SHORT_RISK");
assert.equal(target800.combinedReview.status,"BLOCK_PUT_RATIO_ADDITION");
assert.ok(target800.alerts.some(x=>x.code==="PROFIT_TARGET_REACHED"));
assert.ok(target800.alerts.some(x=>x.code==="TAIL_BUDGET_ZERO"));
assert.ok(target800.alerts.some(x=>x.code==="VOL_DOWNSIDE_ELEVATED"));
assert.ok(target800.alerts.some(x=>x.code==="VOL_DOWNSIDE_ELEVATED"&&x.text.includes("5 sessions")));
assert.ok(target800.alerts.some(x=>x.code==="TIME_VOL_PRIORITY_REVIEW"),"profit line + elevated volatility should trigger explicit priority review");
assert.equal(target800.combinedReview.primaryHybridActionMutation,false);
assert.equal(target800.combinedReview.primaryHybridTargetMutation,false);
assert.equal(target800.combinedReview.executionEnabled,false);

const target1000=P.evaluate(evidence,{
  nav:100000,direction:"SHORT_HEAVY",n:5,policyId:"TP_USD_1000_CLOSE_SHORT_RISK",
  riskPct:1,profitPct:1,currentPnl:1050,age:22,dte:6,rv20:40,horizon:10,combinedReview:true
});
assert.equal(target1000.profitTarget.navTargetUsd,1000);
assert.equal(target1000.profitTarget.directFixedTargetUsd,1000);
assert.equal(target1000.profitTarget.directPolicy.triggerCount,3);
assert.ok(target1000.alerts.some(x=>x.code==="AGE_20"&&x.text.includes("P&L remains positive")));
assert.ok(target1000.alerts.some(x=>x.code==="DTE_7"));
assert.ok(target1000.alerts.some(x=>x.code==="VOL_DOWNSIDE_ELEVATED"&&x.text.includes("10 sessions")));

const n1=P.evaluate(evidence,{nav:80000,direction:"SHORT_HEAVY",n:1,policyId:"BASE_DTE7_CLOSE_SHORT_RISK",riskPct:1,profitPct:1,combinedReview:true});
assert.equal(n1.history,null,"N=1 must not borrow the N=5 option win rate");
assert.equal(n1.serialCurve,null,"N=1 must not borrow the N=5 strategy MaxDD curve");
assert.equal(n1.tail.wholeUnits,1);

const volOnly=P.evaluate(evidence,{nav:80000,direction:"SHORT_HEAVY",n:5,policyId:"BASE_DTE7_CLOSE_SHORT_RISK",riskPct:1,profitPct:1,currentPnl:0,age:3,dte:25,rv20:40,horizon:5,combinedReview:true});
assert.ok(volOnly.alerts.some(x=>x.code==="VOL_DOWNSIDE_ELEVATED"));
assert.ok(!volOnly.alerts.some(x=>x.code==="TIME_VOL_PRIORITY_REVIEW"),"volatility alone must not masquerade as a conjunctive time/volatility signal");

const longHeavy=P.evaluate(evidence,{nav:80000,direction:"LONG_HEAVY",n:5,policyId:"BASE_DTE7_CLOSE_SHORT_RISK",riskPct:1,profitPct:1,combinedReview:true});
assert.equal(longHeavy.history,null,"reverse direction must not inherit the short-heavy option history");
assert.ok(Math.abs(longHeavy.tail.worstUsd-5074.9)<0.001);

const noExactTarget=P.evaluate(evidence,{nav:60000,direction:"SHORT_HEAVY",n:5,policyId:"BASE_DTE7_CLOSE_SHORT_RISK",riskPct:1,profitPct:1,combinedReview:false});
assert.equal(noExactTarget.profitTarget.navTargetUsd,600);
assert.equal(noExactTarget.profitTarget.directFixedTargetUsd,null,"unreplayed $600 threshold must not interpolate $500/$800 evidence");

const invalid={...evidence,curve:{...evidence.curve,source_option_end:"2026-01-01"}};
assert.equal(P.validateSnapshot(invalid).ok,false,"source-window mismatch must fail closed");
console.log("Put Ratio evidence overlay PASS — pinned source, matched history, NAV tail cap, MaxDD tiers, direct target matching, time × volatility, no Frozen-policy mutation");
