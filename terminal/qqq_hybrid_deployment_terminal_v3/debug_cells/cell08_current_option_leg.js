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

// --- ROLL prefers Current Leg identity (operatorSummary) ---
const today="2026-10-07";
const readyLedger=x=>({...x,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}});
const dRoll={qqq:750,vxx:20,vix:20,m1:16,m2:17,s:8,termAsOf:today,spotAsOf:today,today};
const eRoll=E.derive(dRoll);
const bookHeld=E.targetLedger(dRoll,eRoll,readyLedger({nav:100000,qqqShares:56,vxxPct:18,qqqCalls:2,vxxCalls:0}),{});

// expiry-only READY → computed DTE feeds roll distance (blank dte ≠ 0)
assert.strictEqual(E.dteFromExpiry("2026-11-20",today),44);
assert.strictEqual(E.dteFromExpiry("2026-10-01",today),0); // past → 0
assert.strictEqual(E.dteFromExpiry("","2026-10-07"),null);
const expiryOnlyLegs=E.currentOptionLegs({
  qqq:{qty:2,shortStrike:480,longStrike:490,expiry:"2026-11-20",dte:"",delta:"",entryCredit:""},
  vxx:{qty:0}
});
assert.strictEqual(expiryOnlyLegs.qqq.status,"READY");
assert.strictEqual(expiryOnlyLegs.qqq.dte.status,"EMPTY");
assert.strictEqual(expiryOnlyLegs.qqq.dte.value,null);
const rollExpiry=E.operatorSummary(dRoll,eRoll,bookHeld,{},{currentOptionLegs:expiryOnlyLegs,today});
assert.strictEqual(rollExpiry.rolls.qqq.status,"WATCH");
assert.ok(rollExpiry.rolls.qqq.text.includes("DTE 30"),"expected DTE 30d (44-14), got "+rollExpiry.rolls.qqq.text);
assert.strictEqual(rollExpiry.rolls.vxx.status,"OFF");
assert.strictEqual(rollExpiry.rolls.vxx.text,"NO POSITION");

// blank dte + blank expiry with qty>0 → INCOMPLETE / not ROLL_NOW
const incompleteLegs=E.currentOptionLegs({
  qqq:{qty:2,shortStrike:"",longStrike:"",expiry:"",dte:"",delta:""},
  vxx:{qty:0}
});
assert.strictEqual(incompleteLegs.qqq.status,"INCOMPLETE");
const rollInc=E.operatorSummary(dRoll,eRoll,bookHeld,{},{currentOptionLegs:incompleteLegs,today,qqqDte:"",qqqDelta:""});
assert.strictEqual(rollInc.rolls.qqq.status,"NEEDS_DATA");
assert.ok(rollInc.rolls.qqq.text.includes("NEEDS_POSITION_DATA"));
assert.notStrictEqual(rollInc.rolls.qqq.status,"ROLL_NOW");

// FLAT → NO POSITION
const flatLegs=E.currentOptionLegs({qqq:{qty:0},vxx:{qty:0}});
assert.strictEqual(flatLegs.qqq.status,"FLAT");
const bookFlat=E.targetLedger(dRoll,eRoll,readyLedger({nav:100000,qqqShares:56,vxxPct:18,qqqCalls:0,vxxCalls:0}),{});
const rollFlat=E.operatorSummary(dRoll,eRoll,bookFlat,{},{currentOptionLegs:flatLegs,today});
assert.strictEqual(rollFlat.rolls.qqq.status,"OFF");
assert.strictEqual(rollFlat.rolls.qqq.text,"NO POSITION");

console.log(JSON.stringify({
  cell:"08_CURRENT_OPTION_LEG",
  flat:{qty0:flatQty0.status,allEmpty:flatEmpty.status,blankDteIsEmpty:flatEmpty.dte},
  ready:{status:ready.status,rollReady:ready.rollReady,width:ready.width,entryCredit:ready.entryCredit.value},
  readyNoGreeks:{status:readyNoGreeks.status,rollReady:readyNoGreeks.rollReady,dte:readyNoGreeks.dte},
  incomplete:{status:incomplete.status,shortStrike:incomplete.shortStrike.status},
  invalid:{status:invalid.status,shortStrike:invalid.shortStrike.status},
  debitCredit:debit.entryCredit.value,
  aggregate:{qqq:both.qqq.status,vxx:both.vxx.status},
  roll:{
    expiryOnlyDte:rollExpiry.rolls.qqq.text,
    expiryOnlyStatus:rollExpiry.rolls.qqq.status,
    incomplete:rollInc.rolls.qqq.status,
    flat:rollFlat.rolls.qqq.text,
    dteFromExpiry:E.dteFromExpiry("2026-11-20",today)
  },
  PASS:true
}));
