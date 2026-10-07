import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

// FLAT — qty 0
const flatQty0=E.parseOptionLeg({qty:0});
assert.strictEqual(flatQty0.status,"FLAT");
assert.strictEqual(flatQty0.qty.status,"VALUE");
assert.strictEqual(flatQty0.qty.value,0);
assert.strictEqual(flatQty0.rollReady,false);

// FLAT — all empty
const flatEmpty=E.parseOptionLeg({});
assert.strictEqual(flatEmpty.status,"FLAT");
assert.strictEqual(flatEmpty.qty.status,"EMPTY");
assert.strictEqual(flatEmpty.shortStrike.status,"EMPTY");
assert.strictEqual(flatEmpty.dte.status,"EMPTY");
assert.strictEqual(flatEmpty.dte.value,null); // blank DTE ≠ 0

// READY — full identity (dte/delta present → rollReady)
const ready=E.parseOptionLeg({
  qty:2,
  shortStrike:480,
  longStrike:490,
  expiry:"2026-11-20",
  dte:44,
  delta:0.10,
  entryCredit:1.25
});
assert.strictEqual(ready.status,"READY");
assert.strictEqual(ready.rollReady,true);
assert.strictEqual(ready.width,10);
assert.strictEqual(ready.entryCredit.value,1.25);

// READY without dte/delta — identity ok, not roll-ready
const readyNoGreeks=E.parseOptionLeg({
  qty:1,
  shortStrike:20,
  longStrike:22,
  expiry:"2026-12-18",
  dte:"",
  delta:"",
  entryCredit:""
});
assert.strictEqual(readyNoGreeks.status,"READY");
assert.strictEqual(readyNoGreeks.rollReady,false);
assert.strictEqual(readyNoGreeks.dte.status,"EMPTY");
assert.strictEqual(readyNoGreeks.dte.value,null); // blank ≠ 0

// INCOMPLETE — qty 2, blank strikes
const incomplete=E.parseOptionLeg({qty:2,shortStrike:"",longStrike:"",expiry:""});
assert.strictEqual(incomplete.status,"INCOMPLETE");
assert.strictEqual(incomplete.shortStrike.status,"EMPTY");
assert.strictEqual(incomplete.rollReady,false);

// INVALID — bad strike
const invalid=E.parseOptionLeg({qty:1,shortStrike:"abc",longStrike:490,expiry:"2026-11-20"});
assert.strictEqual(invalid.status,"INVALID");
assert.strictEqual(invalid.shortStrike.status,"INVALID");

// entryCredit may be negative (debit)
const debit=E.parseOptionLeg({
  qty:1,shortStrike:100,longStrike:105,expiry:"2026-11-20",entryCredit:-0.35
});
assert.strictEqual(debit.status,"READY");
assert.strictEqual(debit.entryCredit.status,"VALUE");
assert.strictEqual(debit.entryCredit.value,-0.35);

// Aggregate QQQ + VXX
const both=E.currentOptionLegs({
  qqq:{qty:2,shortStrike:480,longStrike:490,expiry:"2026-11-20",dte:44,delta:0.10,entryCredit:1.25},
  vxx:{qty:0}
});
assert.strictEqual(both.qqq.status,"READY");
assert.strictEqual(both.vxx.status,"FLAT");

console.log(JSON.stringify({
  cell:"08_CURRENT_OPTION_LEG",
  flat:{qty0:flatQty0.status,allEmpty:flatEmpty.status,blankDteIsEmpty:flatEmpty.dte},
  ready:{status:ready.status,rollReady:ready.rollReady,width:ready.width,entryCredit:ready.entryCredit.value},
  readyNoGreeks:{status:readyNoGreeks.status,rollReady:readyNoGreeks.rollReady,dte:readyNoGreeks.dte},
  incomplete:{status:incomplete.status,shortStrike:incomplete.shortStrike.status},
  invalid:{status:invalid.status,shortStrike:invalid.shortStrike.status},
  debitCredit:debit.entryCredit.value,
  aggregate:{qqq:both.qqq.status,vxx:both.vxx.status},
  PASS:true
}));
