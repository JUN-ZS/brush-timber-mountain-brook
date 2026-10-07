import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const d={qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:8,termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"};
const e=E.derive(d);
const current={nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:3};

const hold=E.targetLedger({...d,qqq:750},E.derive({...d,s:3}),current,{});
assert.strictEqual(hold.target.qqqCalls,2);
assert.strictEqual(hold.target.vxxCalls,3);
assert.strictEqual(hold.deltas.qqqCalls,0);
assert.strictEqual(hold.deltas.vxxCalls,0);

const candidate={shortStrike:850,longStrike:865,dte:45,delta:0.10,credit:1,sizingAvailable:true,source:"DEBUG_FIXTURE"};
const buy=E.targetLedger(d,e,current,{qqq:candidate,vxx:candidate});
assert.ok(buy.target.qqqCalls>0);
assert.ok(buy.target.vxxCalls>0);

const buyWithoutCandidate=E.targetLedger(d,e,current,{});
assert.strictEqual(buyWithoutCandidate.target.qqqCalls,2);
assert.strictEqual(buyWithoutCandidate.target.vxxCalls,3);

console.log(JSON.stringify({
  cell:"05_BUILD",
  holdTarget:hold.target,
  holdDeltas:hold.deltas,
  buyTarget:buy.target,
  buyWithoutCandidate:buyWithoutCandidate.target,
  PASS:true
}));
