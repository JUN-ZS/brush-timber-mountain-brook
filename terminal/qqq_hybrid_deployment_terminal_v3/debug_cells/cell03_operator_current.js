import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const e=E.derive({
  qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:8,
  termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"
});

const current={nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:3};

const ready=E.targetLedger({qqq:750},e,current,{});
assert.strictEqual(ready.target.qqqCalls,2);
assert.strictEqual(ready.target.vxxCalls,3);

const incomplete=E.targetLedger({qqq:750},e,{
  ...current,
  qqqCalls:null,
  inputStatus:{status:"INCOMPLETE",empty:["qqqCalls"],invalid:[],fields:{}}
},{});
assert.strictEqual(incomplete.inputBlocked,true);
assert.strictEqual(incomplete.deltas.qqqCalls,0);

console.log(JSON.stringify({
  cell:"03_OPERATOR_CURRENT",
  readyCurrent:ready.current,
  readyTarget:ready.target,
  incompleteStatus:incomplete.inputStatus.status,
  PASS:true
}));
