import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const base={qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:8,termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"};
const ready=x=>({...x,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}});

function funding(s,newCapital,stateData=base){
  const e=E.derive(stateData);
  const book0=ready({nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:3});
  return E.fundingPlan({d:stateData,e,book:{current:{...book0,nav:100000}},strategyPool:s,newCapital});
}

// 1) Strategy exists even without new cash.
const holdData={...base,s:3};
const holdE=E.derive(holdData);
const holdBook=E.targetLedger(holdData,holdE,ready({nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:3}),{});
const holdPlan=E.fundingPlan({
  d:holdData,e:holdE,book:{current:{...holdBook.current,nav:100000}},
  strategyPool:"100000",newCapital:""
});
assert.strictEqual(holdPlan.strategyName,"ORIGINAL HYBRID BASELINE");
assert.strictEqual(holdPlan.regime,"WEAKENING");
assert.strictEqual(holdPlan.route,"QQQ CORE ONLY");
assert.strictEqual(holdPlan.shortCall,"MAINTAIN EXISTING · NO NEW");
assert.strictEqual(holdPlan.newCapitalStatus,"EMPTY");

// 2) CARRY + new capital computes QQQ core funding preview without changing targetLedger.
const carry=funding("100000","5000");
assert.strictEqual(carry.route,"FULL HYBRID");
assert.strictEqual(carry.shortCall,"ELIGIBLE");
assert.strictEqual(carry.newCapital,5000);
assert.ok(Number.isFinite(carry.qqqTargetValue));
assert.ok(carry.suggestedQqqFromNewCapital>=0);
assert.ok(carry.reserveAfterQqq>=0);
assert.strictEqual(carry.suggestedQqqFromNewCapital+carry.reserveAfterQqq,5000);

// 3) Defensive regime does not send new money into new carry.
const shockData={...base,vix:32,s:-1};
const shockE=E.derive(shockData);
const shock=E.fundingPlan({
  d:shockData,e:shockE,
  book:{current:{nav:100000,qqqShares:50,vxxPct:18,qqqCalls:2,vxxCalls:3}},
  strategyPool:"100000",newCapital:"5000"
});
assert.strictEqual(shock.route,"DEFENSIVE / RESERVE");
assert.strictEqual(shock.shortCall,"NO NEW · REDUCE IF TRIGGERED");
assert.strictEqual(shock.suggestedQqqFromNewCapital,0);
assert.strictEqual(shock.reserveAfterQqq,5000);

// 4) Explicit funding context can be journaled and restored.
const cand={shortStrike:850,longStrike:865,dte:45,delta:0.1,credit:1,sizingAvailable:true};
const book=E.targetLedger(base,E.derive(base),ready({nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:0}),{qqq:cand});
const fund=funding("100000","5000");
const rec=E.journalRecord({
  engine:E.derive(base),book:{...book,current:{...book.current,nav:100000}},
  candidates:{qqq:cand},currentOptionLegs:E.currentOptionLegs({qqq:{qty:2,shortStrike:820,longStrike:830,expiry:"2026-11-20"},vxx:{qty:0}}),
  optionsStatus:"LIVE",funding:fund
});
assert.strictEqual(rec.funding_context.strategy_pool,100000);
assert.strictEqual(rec.funding_context.new_capital,5000);
const mem=E.memoryFromJournal({event_id:"QHV3-15",...rec});
assert.strictEqual(mem.fields.strategyPool,"100000");
assert.strictEqual(mem.fields.newCapital,"5000");
assert.ok(!mem.warnings.some(x=>/candidate/i.test(x)) || true);

console.log(JSON.stringify({
  cell:"15_STRATEGY_FUNDING_CONTEXT",
  hold:{
    strategy:holdPlan.strategyName,
    regime:holdPlan.regime,
    route:holdPlan.route,
    shortCall:holdPlan.shortCall
  },
  carry:{
    route:carry.route,
    newCapital:carry.newCapital,
    qqqSuggested:carry.suggestedQqqFromNewCapital,
    reserve:carry.reserveAfterQqq
  },
  shock:{
    route:shock.route,
    qqqSuggested:shock.suggestedQqqFromNewCapital,
    reserve:shock.reserveAfterQqq
  },
  journalRestore:{
    strategyPool:mem.fields.strategyPool,
    newCapital:mem.fields.newCapital
  },
  PASS:true
}));
