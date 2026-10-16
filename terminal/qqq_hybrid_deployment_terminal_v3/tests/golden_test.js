
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

function check(name,input,expected){
  const a=E.derive(input),b=E.derive(input);
  assert.deepStrictEqual(a,b,name+" deterministic");
  for(const [k,v] of Object.entries(expected)) assert.strictEqual(a[k],v,name+" "+k);
}

const base={qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:((17.2-16.2)/16.2)*100,termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"};
check("CARRY",base,{state:"CARRY",action:"BUY",blocked:false,gate:"OPEN"});
check("THIN",{...base,s:3},{state:"WEAKENING",action:"HOLD",blocked:false,gate:"WATCH"});
check("BACKWARDATION",{...base,s:-1},{state:"PRE-SHOCK",action:"REDUCE",blocked:false,gate:"CUT"});
check("SHOCK",{...base,vix:32,s:-4},{state:"SHOCK",action:"REDUCE",blocked:false,gate:"CUT"});
check("BLOCK",{...base,m1:null,m2:null,s:null},{state:"DATA BLOCKED",action:"HOLD",blocked:true,gate:"BLOCKED"});
check("STALE",{...base,termAsOf:"2026-10-01",today:"2026-10-07"},{state:"DATA STALE",action:"HOLD",blocked:true,gate:"STALE"});

// F1 — missing, invalid, or future timestamps must never default to FRESH.
const missingTermTime=E.derive({...base,termAsOf:null});
assert.strictEqual(missingTermTime.health.status,"PENDING");
assert.strictEqual(missingTermTime.gate,"PENDING");
assert.strictEqual(missingTermTime.blocked,true);
assert.strictEqual(E.derive({...base,spotAsOf:undefined}).health.status,"PENDING");
assert.strictEqual(E.derive({...base,today:"not-a-date"}).health.status,"PENDING");
assert.strictEqual(E.derive({...base,termAsOf:"2026-10-08"}).health.status,"PENDING");
assert.strictEqual(E.derive({...base,termAsOf:"2026-10-03"}).health.status,"FRESH"); // inclusive max age = 4 days
assert.strictEqual(E.derive({...base,termAsOf:"2026-10-02"}).health.status,"STALE"); // 5 days
assert.strictEqual(E.derive({...base,spotAsOf:"2026-10-04"}).health.status,"MIXED");

const book=E.targetLedger({...base,qqq:750},{...E.derive(base),blocked:false,targets:{qqqCorePct:42,vxxPct:18,vxxCallBudgetPct:2,qqqCallBudgetPct:1.2}},{nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0});
assert.ok(book.deltas.qqqShares>0);
assert.ok(book.deltas.vxxPct>0);

// F2/F4 — require same-expiry, identified contracts with valid quote sides and size.
const chain=[
  {contractSymbol:"QQQ261120C00850000",expiration:"2026-11-20",strike:850,bid:2.00,ask:2.10,bidSize:10,askSize:10,impliedVolatility:0.28},
  {contractSymbol:"QQQ261120C00865000",expiration:"2026-11-20",strike:865,bid:0.90,ask:1.00,bidSize:12,askSize:11,impliedVolatility:0.28},
  {contractSymbol:"QQQ261218C00850000",expiration:"2026-12-18",strike:850,bid:3.00,ask:3.10,bidSize:9,askSize:9,impliedVolatility:0.28},
  {contractSymbol:"QQQ261218C00865000",expiration:"2026-12-18",strike:865,bid:1.60,ask:1.70,bidSize:8,askSize:8,impliedVolatility:0.28}
];
const quoteMeta={retrievedAt:"2026-10-07T15:00:00Z",source:"TEST_FIXTURE",symbol:"QQQ"};
const cand=E.candidateFromChain(chain,750,0.10,45,"2026-10-07",quoteMeta);
assert.ok(cand,"candidate selected only from a fully validated chain");
assert.strictEqual(cand.shortStrike,850);
assert.strictEqual(cand.longStrike,865);
assert.strictEqual(cand.expiration,"2026-11-20");
assert.strictEqual(cand.credit,1);
assert.strictEqual(cand.maxLossPerSpread,1400);
assert.strictEqual(cand.shortBidSize,10);
assert.strictEqual(cand.longAskSize,11);
assert.strictEqual(cand.contractIdentityValidated,true);
assert.strictEqual(cand.quoteValidated,true);
assert.strictEqual(E.candidateFromChain(chain,750,0.10,45,"2026-10-07"),null); // no quote timestamp/source/root
assert.strictEqual(E.candidateFromChain(chain,750,0.10,45,"2026-10-07",{...quoteMeta,retrievedAt:"2026-10-05T15:00:00Z"}),null); // stale quote
assert.strictEqual(E.candidateFromChain(chain,750,0.10,45,"2026-10-07",{...quoteMeta,symbol:"SPY"}),null); // wrong root
assert.strictEqual(E.candidateFromChain(chain.map(x=>({...x,contractSymbol:undefined})),750,0.10,45,"2026-10-07",quoteMeta),null); // missing identity on all candidate legs
assert.strictEqual(E.candidateFromChain(chain.map(x=>({...x,bidSize:undefined})),750,0.10,45,"2026-10-07",quoteMeta),null); // missing size on all candidate legs
assert.strictEqual(E.candidateFromChain(chain.map(x=>({...x,bid:x.ask+0.1})),750,0.10,45,"2026-10-07",quoteMeta),null); // crossed quotes on all candidate legs

// F3/F7 — credit budget is distinct from max-expiry-loss budget.
const noSizingConstraints=E.targetLedger(
  {...base,qqq:750},
  E.derive(base),
  {nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},
  {qqq:cand,vxx:null}
);
assert.strictEqual(noSizingConstraints.sizing.qqqCalls.status,"PENDING_RISK_BUDGET");
assert.strictEqual(noSizingConstraints.sizing.qqqCalls.legacyFormulaSemantics,"PREMIUM_CREDIT_CAP_ONLY");
assert.strictEqual(noSizingConstraints.sizing.qqqCalls.creditBudgetAmount,1200);
assert.strictEqual(noSizingConstraints.sizing.qqqCalls.creditBudgetQuantity,12);
assert.strictEqual(noSizingConstraints.sizing.qqqCalls.maxLossPerSpread,1400);
assert.strictEqual(noSizingConstraints.sizing.qqqCalls.maxLossBudgetAmount,null);
assert.strictEqual(noSizingConstraints.target.qqqCalls,0); // do not turn a credit-only calculation into a deployable target

const verifiedConstraints={budgetSemantics:"MAX_EXPIRY_LOSS",maxLossBudgetPct:2,interimStressBudgetPct:3,interimStressLossPerSpread:2000,interimStressVerified:true,cashMaxQty:10,brokerMarginMaxQty:3,marginVerified:true,assignmentVerified:true,quoteExecutionVerified:true};
const verified=E.targetLedger(
  {...base,qqq:750},
  E.derive(base),
  {nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},
  {qqq:cand,vxx:null},
  {qqq:verifiedConstraints}
);
assert.strictEqual(verified.sizing.qqqCalls.status,"READY");
assert.strictEqual(verified.sizing.qqqCalls.maxLossBudgetAmount,2000);
assert.strictEqual(verified.sizing.qqqCalls.maxLossBudgetQuantity,1);
assert.strictEqual(verified.sizing.qqqCalls.interimStressQuantity,1);
assert.strictEqual(verified.sizing.qqqCalls.quantity,1);
assert.strictEqual(verified.target.qqqCalls,1);
assert.strictEqual(verified.executionAllowed,false); // no broker/order permission

// F2 — absent candidate while existing options are held must preserve current quantity.
const weak=E.derive({...base,s:3});
const held=E.targetLedger(
  {...base,s:3},
  weak,
  {nav:100000,qqqShares:10,vxxPct:4,qqqCalls:3,vxxCalls:2},
  {qqq:null,vxx:null}
);
assert.strictEqual(held.target.qqqCalls,3);
assert.strictEqual(held.target.vxxCalls,2);
assert.strictEqual(held.sizing.qqqCalls.status,"PENDING_CANDIDATE");
assert.strictEqual(held.deltas.qqqCalls,0);
assert.strictEqual(held.deltas.vxxCalls,0);

// F5 — BLOCK preserves positions but explicitly marks current risk unresolved.
const blockedInput={...base,m1:null,m2:null,s:null};
const blockedDecision=E.derive(blockedInput);
const blockedLedger=E.targetLedger(
  blockedInput,
  blockedDecision,
  {nav:100000,qqqShares:40,vxxPct:18,qqqCalls:2,vxxCalls:1}
);
assert.deepStrictEqual(blockedLedger.target,blockedLedger.current);
assert.strictEqual(blockedLedger.riskStatus,"UNRESOLVED_CURRENT_EXPOSURE");
assert.ok(blockedLedger.unresolvedRisk.some(x=>x.leg==="VXX UNDERLYING SHORT"));
assert.strictEqual(blockedLedger.executionAllowed,false);

// F6 — missing margin, cash, interim stress, or assignment checks must block capacity.
const missingMargin=E.targetLedger(
  {...base,qqq:750},
  E.derive(base),
  {nav:100000,qqqShares:0,vxxPct:0,qqqCalls:2,vxxCalls:0},
  {qqq:cand,vxx:null},
  {qqq:{...verifiedConstraints,brokerMarginMaxQty:undefined,marginVerified:false}}
);
assert.strictEqual(missingMargin.sizing.qqqCalls.status,"BLOCKED_MARGIN_UNKNOWN");
assert.strictEqual(missingMargin.sizing.qqqCalls.recommendedQuantity,null);
assert.strictEqual(missingMargin.target.qqqCalls,2);
const missingCash=E.targetLedger(
  {...base,qqq:750},
  E.derive(base),
  {nav:100000,qqqShares:0,vxxPct:0,qqqCalls:2,vxxCalls:0},
  {qqq:cand,vxx:null},
  {qqq:{...verifiedConstraints,cashMaxQty:undefined}}
);
assert.strictEqual(missingCash.sizing.qqqCalls.status,"BLOCKED_CASH_CAP");
assert.strictEqual(missingCash.target.qqqCalls,2);
const missingStress=E.targetLedger(
  {...base,qqq:750},
  E.derive(base),
  {nav:100000,qqqShares:0,vxxPct:0,qqqCalls:2,vxxCalls:0},
  {qqq:cand,vxx:null},
  {qqq:{...verifiedConstraints,interimStressVerified:false}}
);
assert.strictEqual(missingStress.sizing.qqqCalls.status,"PENDING_INTERIM_STRESS");
assert.strictEqual(missingStress.target.qqqCalls,2);
const missingAssignment=E.targetLedger(
  {...base,qqq:750},
  E.derive(base),
  {nav:100000,qqqShares:0,vxxPct:0,qqqCalls:2,vxxCalls:0},
  {qqq:cand,vxx:null},
  {qqq:{...verifiedConstraints,assignmentVerified:false}}
);
assert.strictEqual(missingAssignment.sizing.qqqCalls.status,"BLOCKED_ASSIGNMENT_UNKNOWN");
assert.strictEqual(missingAssignment.target.qqqCalls,2);

console.log("V3 golden engine PASS — F1-F7 contract gates");

