"use strict";
const assert=require("node:assert/strict");
const X=require("../put_ratio_exit_sensitivity.js");
const now=Date.parse("2026-10-15T08:00:00Z");
function valid(overrides={}){return{nav:1000000,thresholdPct:1,orientation:"short-heavy",ratioN:5,packages:1,longStrike:705,shortStrike:665,longEntryPrice:11.11,shortEntryPrice:2.67,currentLongBid:12.50,currentShortAsk:1.50,commissionPerContractSide:0.65,closeSlippagePerShare:0.05,dte:45,heldSessions:3,spot:728.92,quoteAsOf:"2026-10-15T07:58:00Z",...overrides}}
function near(a,b,e=0.011){assert.ok(Math.abs(a-b)<=e,"expected "+b+" ± "+e+", got "+a)}
{
 const r=X.evaluate(valid(),now);assert.equal(r.ready,true);
 near(r.thresholds[0].usd,5000);near(r.thresholds[1].usd,10000);near(r.thresholds[2].usd,20000);
 near(r.oneThousandPct,0.1);near(r.targetUsd,10000);near(r.fullClosePnlUsd,686.2);near(r.pnlPctNav,0.06862,0.0001);
 assert.equal(r.thresholdState,"WITHIN_CANDIDATE_BAND");assert.equal(r.baselineDteActive,false);assert.equal(r.timing.first3,true);assert.equal(r.timing.first5,true);assert.equal(r.quoteQuality.status,"TIME_WITHIN_15M_UNAUTHENTICATED");
}
{
 const r=X.evaluate(valid(),now);near(r.trimShort.realizedPnlOnTrimmedShortsAfterCostsUsd,442.8);near(r.trimShort.residualOpenPnlAfterCostsReservedUsd,243.4);
 near(r.trimShort.combinedPnlWithResidualExitCostReservedUsd,r.fullClosePnlUsd);assert.equal(r.trimShort.shortContractsToClose,4);
 assert.equal(r.trimShort.remainingLongQty,1);assert.equal(r.trimShort.remainingShortQty,1);assert.equal(r.trimShort.remainingContracts,2);assert.ok(r.trimShort.residualWorstExpiryLossFromCurrentMarkUsd>=0);
}
{
 const r=X.evaluate(valid({dte:7,heldSessions:5,thresholdPct:0.5,packages:10}),now);
 assert.equal(r.baselineDteActive,true);assert.equal(r.timing.first5,true);assert.equal(r.thresholdHit,true);assert.equal(r.status,"PROFIT_TARGET_REACHED");assert.equal(r.trimShort.shortContractsToClose,40);
}
{
 const r=X.evaluate(valid({orientation:"long-heavy",ratioN:2,longStrike:665,shortStrike:705,longEntryPrice:2.72,shortEntryPrice:11,currentLongBid:1.80,currentShortAsk:12,dte:7}),now);
 assert.equal(r.ready,true);assert.equal(r.longQty,2);assert.equal(r.shortQty,1);assert.equal(r.trimShort.shortContractsToClose,1);
 assert.equal(r.trimShort.remainingLongQty,2);assert.equal(r.trimShort.remainingShortQty,0);
 near(r.trimShort.combinedPnlWithResidualExitCostReservedUsd,r.fullClosePnlUsd);assert.notEqual(r.trimShort.riskProfile,X.evaluate(valid(),now).trimShort.riskProfile);
}
{
 const geom=X.evaluate(valid({longStrike:650,shortStrike:665}),now);assert.equal(geom.ready,false);assert.match(geom.error,/geometry/i);
 const missing=X.evaluate(valid({currentLongBid:null}),now);assert.equal(missing.ready,false);assert.match(missing.error,/Missing marks stay PENDING/i);
 const stale=X.evaluate(valid({quoteAsOf:"2026-10-15T07:40:00Z"}),now);assert.equal(stale.ready,true);assert.equal(stale.quoteQuality.status,"STALE_OVER_15M");assert.equal(stale.displayStatus,"SCENARIO_ONLY_TIMESTAMP_GATE_NOT_MET");
 const future=X.evaluate(valid({quoteAsOf:"2026-10-15T09:00:00Z"}),now);assert.equal(future.quoteQuality.status,"FUTURE_TIMESTAMP");
}
console.log("QQQ PUT RATIO EXIT SENSITIVITY: NAV bar, fees, full-close/short-trim reconciliation, DTE≤7 and stale-mark gates PASS");
