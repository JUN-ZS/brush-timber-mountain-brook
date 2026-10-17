
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { spawnSync } from "node:child_process";
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
assert.ok(book.deltas.vxxPct>0);

const chain=[{expiration:"2026-11-20",strike:850,bid:2.00,ask:2.10,impliedVolatility:0.28},{expiration:"2026-11-20",strike:865,bid:0.90,ask:1.00,impliedVolatility:0.28},{expiration:"2026-12-18",strike:850,bid:3.00,ask:3.10,impliedVolatility:0.28},{expiration:"2026-12-18",strike:865,bid:1.60,ask:1.70,impliedVolatility:0.28}];
const cand=E.candidateFromChain(chain,750,0.10,45,"2026-10-07");
assert.ok(cand,"candidate selected");
assert.strictEqual(cand.shortStrike,850);
assert.strictEqual(cand.longStrike,865);
assert.strictEqual(cand.credit,1);
assert.strictEqual(cand.sizingAvailable,true);
const sized=E.targetLedger({...base,qqq:750},{...E.derive(base),blocked:false,targets:{qqqCorePct:42,vxxPct:18,vxxCallBudgetPct:2,qqqCallBudgetPct:1.2}},{nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},{qqq:cand,vxx:null});
assert.strictEqual(sized.target.qqqCalls,12);
const pending=E.targetLedger(base,E.derive(base),{nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0});
assert.strictEqual(pending.target.qqqCalls,0);
assert.strictEqual(pending.sizing.qqqCalls.status,"PENDING_CANDIDATE");
console.log("V3 golden engine PASS");

// Cell 14 coverage via golden step (OAuth token lacks `workflow` scope to edit cells YAML).
const cell14=spawnSync(process.execPath,[path.join(here,"..","debug_cells","cell14_journal_memory.js")],{encoding:"utf8"});
assert.strictEqual(cell14.status,0,"cell14_journal_memory must PASS\n"+cell14.stdout+"\n"+cell14.stderr);
assert.ok(String(cell14.stdout).includes('"PASS":true'),"cell14 PASS marker");
const cell15=spawnSync(process.execPath,[path.join(here,"..","debug_cells","cell15_strategy_funding_context.js")],{encoding:"utf8"});
assert.strictEqual(cell15.status,0,"cell15_strategy_funding_context must PASS\n"+cell15.stdout+"\n"+cell15.stderr);
assert.ok(String(cell15.stdout).includes('"PASS":true'),"cell15 PASS marker");
const cell16=spawnSync(process.execPath,[path.join(here,"..","debug_cells","cell16_strategy_action_bridge.js")],{encoding:"utf8"});
assert.strictEqual(cell16.status,0,"cell16_strategy_action_bridge must PASS\n"+cell16.stdout+"\n"+cell16.stderr);
assert.ok(String(cell16.stdout).includes('"PASS":true'),"cell16 PASS marker");
console.log("V3 golden + Cell 14/15/16 operator loop PASS");
