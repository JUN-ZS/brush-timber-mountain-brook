
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

const book=E.targetLedger({...base,qqq:750},{...E.derive(base),blocked:false,targets:{qqqCorePct:42,vxxPct:18,vxxCallBudgetPct:2,qqqCallBudgetPct:1.2}},{nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0});
assert.ok(book.deltas.qqqShares>0);
assert.ok(book.deltas.vxxPct>0);\n\nconst chain=[{expiration:"2026-11-20",strike:850,bid:2.00,ask:2.10,impliedVolatility:0.28},{expiration:"2026-11-20",strike:865,bid:0.90,ask:1.00,impliedVolatility:0.28},{expiration:"2026-12-18",strike:850,bid:3.00,ask:3.10,impliedVolatility:0.28},{expiration:"2026-12-18",strike:865,bid:1.60,ask:1.70,impliedVolatility:0.28}];\nconst cand=E.candidateFromChain(chain,750,0.10,45,"2026-10-07");\nassert.ok(cand,"candidate selected");\nassert.strictEqual(cand.shortStrike,850);\nassert.strictEqual(cand.longStrike,865);\nassert.strictEqual(cand.credit,1);\nassert.strictEqual(cand.sizingAvailable,true);\nconst sized=E.targetLedger({...base,qqq:750},{...E.derive(base),blocked:false,targets:{qqqCorePct:42,vxxPct:18,vxxCallBudgetPct:2,qqqCallBudgetPct:1.2}},{nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},{qqq:cand,vxx:null});\nassert.strictEqual(sized.target.qqqCalls,12);\nconst pending=E.targetLedger(base,E.derive(base),{nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0});\nassert.strictEqual(pending.target.qqqCalls,0);\nassert.strictEqual(pending.sizing.qqqCalls.status,"PENDING_CANDIDATE");
console.log("V3 golden engine PASS");
