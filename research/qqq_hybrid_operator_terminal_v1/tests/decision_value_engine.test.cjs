"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const sandbox={module:{exports:{}}};
vm.runInNewContext(fs.readFileSync(require.resolve("../decision_value_engine.js"),"utf8"),sandbox,{filename:"decision_value_engine.js"});
const D=sandbox.module.exports;
function fixture(overrides={}){return {candidateKey:"qqqShares",lens:"ADD",quantity:10,horizonDays:10,nav:100000,rewardUsd:200,lossUsd:100,costUsd:5,costStressUsd:10,riskNature:"DEFINED",probabilityMethod:"EMPIRICAL",wins:40,trials:50,probabilityBasis:"INDEPENDENT_OOS",accuracy:"PASS",generality:"PASS",integration:"PASS",alternativeEVTotalUsd:0,alternativeLabel:"Explicit $0 direct-P&L WAIT baseline",evidenceNote:"source hash + chronological OOS report",market:{blocked:false,allowNew:true,action:"BUY",state:"CARRY"},mainRow:{key:"qqqShares",current:10,target:30,capacity:100,delta:20,action:"ADD",status:"READY",reason:"eligible"},...overrides};}
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

{
 const missing=D.evaluate(fixture({alternativeEVTotalUsd:null,alternativeLabel:""}));
 assert.equal(missing.status,"ALTERNATIVE_VALUE_PENDING");
 assert.equal(missing.incrementalValueBaseUsd,null);
 const inferior=D.evaluate(fixture({alternativeEVTotalUsd:2000,alternativeLabel:"Cash + current portfolio comparator"}));
 assert.equal(inferior.status,"NEGATIVE_INCREMENTAL_VALUE");
 assert.ok(inferior.incrementalValueBaseUsd<0);
 const fragile=D.evaluate(fixture({costStressUsd:300,alternativeEVTotalUsd:0,alternativeLabel:"Explicit $0 direct-P&L WAIT baseline"}));
 assert.equal(fragile.status,"FRAGILE_EXPECTED_VALUE");
 const floor=D.evaluate(fixture({deploymentRoadmap:{status:"FLOOR_BREACH",floorGapUsd:-500},market:{blocked:false,allowNew:true,action:"BUY",state:"CARRY"}}));
 assert.equal(floor.status,"CLOCK_FLOOR_BREACH");
 const noCarry=D.evaluate(fixture({candidateKey:"qqqShares",market:{blocked:false,allowNew:false,action:"HOLD",state:"THIN"}}));
 assert.equal(noCarry.status,"ADD_NOT_ALLOWED","QQQ Core ADD must not bypass the current regime gate");
 const missingRoute=D.evaluate(fixture({mainRow:{current:null,target:null,capacity:null,action:"ADD",status:"PENDING",reason:"unknown current/target"}}));
 assert.equal(missingRoute.mainRoute.maxAllowedAdd,null);
 assert.equal(missingRoute.status,"ADD_NOT_ALLOWED","unknown capacity cannot be coerced to an add gap");
 const heldReview=D.evaluate(fixture({lens:"HOLD",positionManagementRows:[{template:"QQQ_CORE",label:"QQQ core",action:"STOP MARK BREACHED · HUMAN REVIEW",pnlR:-1.2,pnl:-120}]}));
 assert.equal(heldReview.status,"POSITION_REVIEW_PRIORITY");
}
{
 // Full-use scenario matrix: missing data must be PENDING, not disguised as an invalid probability.
 const missingManual=D.evaluate(fixture({probabilityMethod:"MANUAL",probabilityLowPct:null,probabilityBasePct:null,probabilityHighPct:null}));
 assert.equal(missingManual.status,"NEEDS_PROBABILITY");
 assert.equal(missingManual.expectedValueBaseUsd,null);
 const missingEmpirical=D.evaluate(fixture({wins:null,trials:50}));
 assert.equal(missingEmpirical.status,"NEEDS_PROBABILITY");
 assert.equal(missingEmpirical.sampleSize,null);
}
{
 // A mathematically impossible sample is invalid, unlike a blank sample.
 const impossible=D.evaluate(fixture({wins:31,trials:30}));
 assert.equal(impossible.status,"INVALID_RANGE");
}
{
 // The evidence floor is enforced at 29, then accepts a 30-observation example only for review.
 const below=D.evaluate(fixture({wins:23,trials:29}));
 assert.equal(below.status,"EVIDENCE_INCOMPLETE");
 assert.ok(below.warnings.some(x=>x.includes("30-trade")));
 const atFloor=D.evaluate(fixture({wins:24,trials:30}));
 assert.equal(atFloor.status,"ELIGIBLE_FOR_HUMAN_REVIEW");
 assert.ok(atFloor.incrementalValueAdverseUsd>0);
 assert.equal(atFloor.scenarioRiskPctNav,1);
}
{
 // A low observed win rate does not get rescued by a positive headline or comparator.
 const negative=D.evaluate(fixture({wins:10,trials:50}));
 assert.equal(negative.status,"NEGATIVE_EXPECTED_VALUE");
 assert.ok(negative.expectedValueBaseUsd<0);
}
{
 // The same candidate loses to a better-priced comparator even when its own EV is positive.
 const beaten=D.evaluate(fixture({alternativeEVTotalUsd:1400,alternativeLabel:"Same-capital alternative with priced expected EV"}));
 assert.equal(beaten.status,"NEGATIVE_INCREMENTAL_VALUE");
 assert.ok(beaten.expectedValueBaseTotalUsd>0);
 assert.ok(beaten.incrementalValueBaseUsd<0);
}
{
 // Severe extra costs make the base case look attractive but break the adverse case.
 const stressed=D.evaluate(fixture({costStressUsd:300}));
 assert.equal(stressed.status,"FRAGILE_EXPECTED_VALUE");
 assert.ok(stressed.expectedValueBaseUsd>0);
 assert.ok(stressed.expectedValueAdverseUsd<0);
}
{
 // Material risk is disclosed as a warning rather than silently changing the selected scenario.
 const largeRisk=D.evaluate(fixture({lossUsd:600}));
 assert.ok(largeRisk.scenarioRiskPctNav>5);
 assert.ok(largeRisk.warnings.some(x=>x.includes("exceeds 5% of NAV")));
}
{
 // Main sizing BLOCK/PENDING state cannot be overridden by a positive EV.
 const blockedRoute=D.evaluate(fixture({mainRow:{current:10,target:30,capacity:100,action:"BLOCKED",status:"BLOCKED",reason:"invalid/stale market"}}));
 assert.equal(blockedRoute.status,"ADD_NOT_ALLOWED");
 assert.equal(blockedRoute.mainRoute.maxAllowedAdd,null);
}
{
 // HOLD cannot be priced on an empty position, even with otherwise good forward EV.
 const emptyHold=D.evaluate(fixture({lens:"HOLD",mainRow:{current:0,target:30,capacity:100,action:"ADD",status:"READY",reason:"capacity"}}));
 assert.equal(emptyHold.status,"ADD_NOT_ALLOWED");
}
{
 // Partial low/base/high data are pending, not a fabricated zero or an adverse pass.
 const noRange=D.evaluate(fixture({probabilityMethod:"MANUAL",probabilityLowPct:null,probabilityBasePct:80,probabilityHighPct:null}));
 assert.equal(noRange.status,"NEEDS_PROBABILITY");
 assert.equal(noRange.robustPositive,false);
}
{
 const badManual=D.evaluate(fixture({probabilityMethod:"MANUAL",probabilityLowPct:60,probabilityBasePct:101,probabilityHighPct:110}));
 assert.equal(badManual.status,"INVALID_RANGE");
}
{
 // A breached long-horizon floor blocks new ADD, but an existing HOLD stays a review scenario.
 const holdFloor=D.evaluate(fixture({lens:"HOLD",deploymentRoadmap:{status:"FLOOR_BREACH",floorGapUsd:-500},mainRow:{current:10,target:10,capacity:100,action:"HOLD",status:"READY",reason:"no sizing change"}}));
 assert.equal(holdFloor.status,"ELIGIBLE_FOR_HUMAN_REVIEW");
 assert.ok(holdFloor.warnings.some(x=>x.includes("CLOCK Floor is breached")));
}
{
 // Custom research cannot obtain portfolio sizing just by supplying positive hypothetical EV.
 const custom=D.evaluate(fixture({candidateKey:"custom",mainRow:null}));
 assert.equal(custom.status,"NO_SIZING_ROUTE");
}
{
 const missingPayoff=D.evaluate(fixture({rewardUsd:null}));
 assert.equal(missingPayoff.status,"NEEDS_PAYOFF");
}
{
 const noComparator=D.evaluate(fixture({alternativeEVTotalUsd:null,alternativeLabel:""}));
 assert.equal(noComparator.status,"ALTERNATIVE_VALUE_PENDING");
 assert.equal(noComparator.waitReferenceExpectedValueUsd,null,"unknown WAIT value must not be serialized as $0");
}
console.log("QQQ HYBRID DECISION VALUE ENGINE: 17 base + 15 full-use scenario checks PASS");
