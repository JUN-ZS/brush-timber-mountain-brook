"use strict";
const assert=require("node:assert/strict");
const D=require("../decision_value_engine.js");
function fixture(overrides={}){return {candidateKey:"qqqShares",lens:"ADD",quantity:10,horizonDays:10,nav:100000,rewardUsd:200,lossUsd:100,costUsd:5,costStressUsd:10,riskNature:"DEFINED",probabilityMethod:"EMPIRICAL",wins:40,trials:50,probabilityBasis:"INDEPENDENT_OOS",accuracy:"PASS",generality:"PASS",integration:"PASS",evidenceNote:"source hash + chronological OOS report",market:{blocked:false,allowNew:true,action:"BUY",state:"CARRY"},mainRow:{key:"qqqShares",current:10,target:30,capacity:100,delta:20,action:"ADD",status:"READY",reason:"eligible"},...overrides};}
{
 const r=D.evaluate(fixture());assert.equal(r.status,"ELIGIBLE_FOR_HUMAN_REVIEW");assert.equal(r.probabilityBasePct,80);
 assert.ok(r.probabilityLowPct<80&&r.probabilityHighPct>80);assert.equal(r.breakEvenProbabilityPct,35);
 assert.equal(r.expectedValueBaseUsd,0.8*200-0.2*100-5);assert.equal(r.expectedValueAdverseUsd,r.probabilityLowPct/100*200-(1-r.probabilityLowPct/100)*100-15);
 assert.equal(r.expectedValueBaseTotalUsd,r.expectedValueBaseUsd*10);assert.equal(r.expectedValuePerCalendarDayUsd,r.expectedValueBaseTotalUsd/10);
}
{const r=D.evaluate(fixture({probabilityBasis:"HYPOTHESIS",probabilityMethod:"MANUAL",probabilityLowPct:60,probabilityBasePct:70,probabilityHighPct:80}));assert.equal(r.status,"HYPOTHESIS_ONLY");}
{const r=D.evaluate(fixture({probabilityBasis:"MODEL_REPLAY",candidateKey:"vxxCallSpreads",wins:41,trials:49,mainRow:{current:0,target:10,capacity:10,delta:10,action:"ADD",status:"READY",reason:"route"}}));assert.equal(r.probabilityBasePct,41/49*100);assert.equal(r.status,"MODEL_ONLY");assert.equal(r.axes.accuracy,"BLOCKED · MODEL_ONLY / NOT OPRA");}
{const r=D.evaluate(fixture({candidateKey:"qqqFarCallOverlay"}));assert.equal(r.status,"QQQ_OVERLAY_LOCKBOX");assert.equal(r.axes.integration,"FAILS CURRENT BASE SCREEN");}
{const r=D.evaluate(fixture({market:{blocked:true,allowNew:false,action:"HOLD",state:"DATA BLOCKED"}}));assert.equal(r.status,"MARKET_BLOCKED");}
{const r=D.evaluate(fixture({mainRow:{current:10,target:15,capacity:100,delta:5,action:"ADD",status:"READY",reason:"route"},quantity:6}));assert.equal(r.status,"QTY_OVER_TARGET");assert.equal(r.quantityOverTarget,true);}
{const r=D.evaluate(fixture({lens:"HOLD",mainRow:{current:10,target:5,capacity:100,delta:-5,action:"REDUCE",status:"READY",reason:"reduce"}}));assert.equal(r.status,"HOLD_CONFLICTS_WITH_REDUCE");}
{const r=D.evaluate(fixture({candidateKey:"vxxShortShares",riskNature:"DEFINED"}));assert.equal(r.riskNature,"UNBOUNDED");assert.equal(r.status,"UNBOUNDED_TAIL");}
{const r=D.evaluate(fixture({probabilityBasis:"INDEPENDENT_OOS",probabilityMethod:"MANUAL",probabilityLowPct:60,probabilityBasePct:70,probabilityHighPct:80}));assert.equal(r.status,"EVIDENCE_INCOMPLETE");}
{assert.equal(D.wilson95(1,0),null);assert.equal(D.wilson95(4,3),null);assert.ok(D.wilson95(41,49).lowPct<D.wilson95(41,49).basePct);const r=D.evaluate(fixture({probabilityMethod:"MANUAL",probabilityBasis:"HYPOTHESIS",probabilityLowPct:80,probabilityBasePct:70,probabilityHighPct:90}));assert.equal(r.status,"INVALID_RANGE");}
console.log("QQQ HYBRID DECISION VALUE ENGINE: 10 test groups PASS");
