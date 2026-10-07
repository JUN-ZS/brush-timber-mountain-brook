import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const d={qqq:750,vxx:20,vix:20,m1:16,m2:17,s:6,termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"};
const ready=x=>({...x,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}});
const candidate={
  qqq:{shortStrike:850,longStrike:865,dte:45,delta:0.10,credit:1,sizingAvailable:true,source:"FIXTURE"},
  vxx:{shortStrike:30,longStrike:31,dte:45,delta:0.10,credit:0.5,sizingAvailable:true,source:"FIXTURE"}
};

const market=E.derive(d);
const empty=ready({nav:100000,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0});
const build=E.targetLedger(d,market,empty,candidate);
const a=E.operatorSummary(d,market,build,candidate,{qqqDte:"",qqqDelta:"",vxxDte:"",vxxDelta:""});
assert.strictEqual(a.mode,"BUILD / REBALANCE");
assert.ok(a.plan.some(x=>x.includes("QQQ core")));
assert.ok(a.plan.some(x=>x.includes("VXX short")));
assert.ok(a.plan.some(x=>x.includes("QQQ far")));
assert.strictEqual(a.thresholds[0].id,"S_5");

const holdData={...d,s:3};
const hold=E.derive(holdData);
const held=ready({nav:100000,qqqShares:56,vxxPct:18,qqqCalls:2,vxxCalls:3});
const holdBook=E.targetLedger(holdData,hold,held,{});
const h=E.operatorSummary(holdData,hold,holdBook,{},{qqqDte:"",qqqDelta:"",vxxDte:"",vxxDelta:""});
assert.strictEqual(h.mode,"WATCH");
assert.ok(h.plan[0].includes("不新增"));
assert.strictEqual(h.rolls.qqq.status,"NEEDS_DATA");
assert.strictEqual(h.rolls.vxx.status,"NEEDS_DATA");
assert.strictEqual(h.thresholds[0].id,"S_0");
assert.strictEqual(h.thresholds[0].text,"3 pp");

const dRoll={...holdData,s:8};
const eRoll=E.derive(dRoll);
const bRoll=E.targetLedger(dRoll,eRoll,ready({nav:100000,qqqShares:56,vxxPct:18,qqqCalls:2,vxxCalls:0}),candidate);
const roll=E.operatorSummary(dRoll,eRoll,bRoll,candidate,{qqqDte:20,qqqDelta:0.12,vxxDte:"",vxxDelta:""});
assert.strictEqual(roll.rolls.qqq.status,"WATCH");
assert.ok(roll.rolls.qqq.text.includes("DTE 6"));
assert.ok(roll.rolls.qqq.text.includes("Δ 0.04"));
assert.strictEqual(roll.rolls.vxx.status,"OFF");

console.log(JSON.stringify({
  cell:"07_OPERATOR_SUMMARY",
  buildMode:a.mode,
  holdMode:h.mode,
  nearestHoldChange:h.thresholds[0].label+" · "+h.thresholds[0].text,
  qqqRollDistance:roll.rolls.qqq.text,
  vxxRoll:roll.rolls.vxx.text,
  PASS:true
}));
