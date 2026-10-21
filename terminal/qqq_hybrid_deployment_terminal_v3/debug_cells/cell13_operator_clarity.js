import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const today="2026-10-07";
const ready=x=>({...x,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}});

// ---------------------------------------------------------------------------
// A) Data cadence / MIXED-SOURCE (pain #7)
// Same-calendar-day delayed settlement term + live last spot → FRESH + badges,
// NOT blocked. Date-gap MIXED (>2d) still blocks.
// ---------------------------------------------------------------------------
const mixedSameDay={
  qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:((17.2-16.2)/16.2)*100,
  termAsOf:today,spotAsOf:today,today,
  term_source:"CBOE_PUBLIC_DELAYED_VX",
  provenance:{qqq:"YAHOO",vxx:"YAHOO",vix:"OPEND",m1:"CBOE_PUBLIC_DELAYED_VX",m2:"CBOE_PUBLIC_DELAYED_VX"}
};
const hA=E.dataHealth(mixedSameDay);
assert.strictEqual(hA.status,"FRESH");
assert.strictEqual(hA.termCadence,"DELAYED_SETTLEMENT");
assert.strictEqual(hA.spotCadence,"LAST");
assert.strictEqual(hA.sourceMix,"MIXED_SOURCE");
assert.ok(hA.label.includes("MIXED-SOURCE"));
assert.ok(hA.badges.includes("MIXED-SOURCE"));
assert.ok(hA.badges.some(b=>b.includes("DELAYED SETTLEMENT")&&b.includes("LAST")));
assert.strictEqual(hA.warnOnly,true);
const dA=E.derive(mixedSameDay);
assert.strictEqual(dA.blocked,false,"MIXED_SOURCE same-day must not block trading");
assert.strictEqual(dA.action,"BUY");

const cadenceOnly=E.sourceCadence(mixedSameDay);
assert.strictEqual(cadenceOnly.sourceMix,"MIXED_SOURCE");

// Date-gap MIXED (>2d) still blocks
// age=3 (<= maxTermAgeDays 4) but asofGap=3 (>2) → AS-OF MIXED blocks; not STALE
const dateMixed={...mixedSameDay,spotAsOf:"2026-10-07",termAsOf:"2026-10-04",today:"2026-10-07"};
const hGap=E.dataHealth(dateMixed);
assert.strictEqual(hGap.status,"MIXED");
assert.strictEqual(hGap.label,"AS-OF MIXED");
const dGap=E.derive(dateMixed);
assert.strictEqual(dGap.blocked,true);

// Plain FRESH (aligned live term + last spot) — no MIXED-SOURCE
const aligned={
  ...mixedSameDay,
  term_source:"OPEND_VX_LIVE",
  provenance:{qqq:"OPEND",vxx:"OPEND",vix:"OPEND",m1:"OPEND_VX",m2:"OPEND_VX"}
};
const hAligned=E.dataHealth(aligned);
assert.strictEqual(hAligned.status,"FRESH");
assert.notStrictEqual(hAligned.sourceMix,"MIXED_SOURCE");
assert.ok(!String(hAligned.label).includes("MIXED-SOURCE"));

// ---------------------------------------------------------------------------
// B) VXX naming (pain #6)
// ---------------------------------------------------------------------------
const labels=E.exposureLabels();
assert.strictEqual(labels.vxxShort,"VXX short exposure (% NAV)");
assert.strictEqual(labels.vxxShortUnit,"% NAV");
assert.strictEqual(labels.vxxCallSpreads,"VXX call credit spreads");
assert.strictEqual(labels.vxxCallUnit,"contracts");
const shares=E.impliedVxxShares(100000,10,20);
assert.ok(Number.isFinite(shares));
assert.strictEqual(Math.round(shares),500); // 100000*0.10/20
assert.strictEqual(E.impliedVxxShares(100000,10,null),null);
assert.strictEqual(E.impliedVxxShares(100000,10,0),null);
assert.strictEqual(E.impliedVxxShares("","",20),null);

// ---------------------------------------------------------------------------
// C) Flat-book silence (pain #8)
// ---------------------------------------------------------------------------
const silenceZero=E.flatBookSilence({qqqCalls:0,vxxCalls:0});
assert.strictEqual(silenceZero.silent,true);
assert.strictEqual(silenceZero.reason,"CALLS_ZERO");

const silenceForce=E.flatBookSilence({qqqCalls:2,vxxCalls:3,forceFlat:true});
assert.strictEqual(silenceForce.silent,true);
assert.strictEqual(silenceForce.reason,"FORCE_FLAT");

const flatLegs=E.currentOptionLegs({qqq:{qty:0},vxx:{qty:0}});
const silenceLegs=E.flatBookSilence({qqqCalls:2,vxxCalls:3,currentOptionLegs:flatLegs});
assert.strictEqual(silenceLegs.silent,true);
assert.strictEqual(silenceLegs.reason,"LEGS_FLAT");

const hold=E.derive({qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3,termAsOf:today,spotAsOf:today,today});
// Blank DTE with calls=0 must not fire ROLL / must be NO_POSITION
const trigFlat=E.triggers(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3},
  hold,
  {qqqCalls:0,vxxCalls:0,qqqDte:"",qqqDelta:"",vxxDte:"",vxxDelta:""}
);
const qRoll=trigFlat.find(x=>x.id==="QQQ_ROLL");
const vRoll=trigFlat.find(x=>x.id==="VXX_ROLL");
assert.strictEqual(qRoll.fire,false);
assert.strictEqual(qRoll.mode,"NO_POSITION");
assert.strictEqual(vRoll.fire,false);
assert.strictEqual(vRoll.mode,"NO_POSITION");

// forceFlat suppresses even when hasQQQCall:true would otherwise arm
const trigForce=E.triggers(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3},
  hold,
  {hasQQQCall:true,hasVXXCall:true,qqqDte:10,qqqDelta:0.20,vxxDte:10,vxxDelta:0.25,forceFlat:true}
);
assert.strictEqual(trigForce.find(x=>x.id==="QQQ_ROLL").fire,false);
assert.strictEqual(trigForce.find(x=>x.id==="QQQ_ROLL").mode,"NO_POSITION");
assert.strictEqual(trigForce.find(x=>x.id==="VXX_ROLL").fire,false);

// operatorSummary rolls OFF under forceFlat / zero calls (never ROLL_NOW from blank)
const bookFlat=E.targetLedger(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3,termAsOf:today,spotAsOf:today,today},
  hold,
  ready({nav:100000,qqqShares:56,vxxPct:18,qqqCalls:0,vxxCalls:0}),
  {}
);
const sumFlat=E.operatorSummary(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3,today},
  hold,bookFlat,{},
  {qqqDte:"",qqqDelta:"",vxxDte:"",vxxDelta:"",forceFlat:false,currentOptionLegs:flatLegs,today}
);
assert.strictEqual(sumFlat.rolls.qqq.status,"OFF");
assert.strictEqual(sumFlat.rolls.qqq.text,"NO POSITION");
assert.strictEqual(sumFlat.rolls.vxx.status,"OFF");
assert.notStrictEqual(sumFlat.rolls.qqq.status,"ROLL_NOW");

const bookHeld=E.targetLedger(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3,termAsOf:today,spotAsOf:today,today},
  hold,
  ready({nav:100000,qqqShares:56,vxxPct:18,qqqCalls:2,vxxCalls:3}),
  {}
);
const sumForce=E.operatorSummary(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3,today},
  hold,bookHeld,{},
  {qqqDte:10,qqqDelta:0.20,vxxDte:10,vxxDelta:0.25,forceFlat:true,today}
);
assert.strictEqual(sumForce.rolls.qqq.status,"OFF");
assert.strictEqual(sumForce.rolls.vxx.status,"OFF");
assert.strictEqual(sumForce.flatBookSilence.reason,"FORCE_FLAT");

// Armed path still works when legs present and not flat
const trigArmed=E.triggers(
  {qqq:750,vxx:20,vix:16,m1:16,m2:16.5,s:3},
  hold,
  {qqqCalls:2,vxxCalls:3,qqqDte:10,qqqDelta:0.12,vxxDte:30,vxxDelta:0.12}
);
assert.strictEqual(trigArmed.find(x=>x.id==="QQQ_ROLL").fire,true);
assert.strictEqual(trigArmed.find(x=>x.id==="VXX_ROLL").fire,false);

console.log(JSON.stringify({
  cell:"13_OPERATOR_CLARITY",
  A:{
    sameDayMixed:{status:hA.status,label:hA.label,termCadence:hA.termCadence,spotCadence:hA.spotCadence,sourceMix:hA.sourceMix,blocked:dA.blocked},
    dateGapMixed:{status:hGap.status,blocked:dGap.blocked},
    aligned:{status:hAligned.status,sourceMix:hAligned.sourceMix}
  },
  B:{
    vxxShort:labels.vxxShort,
    vxxCallSpreads:labels.vxxCallSpreads,
    impliedShares:shares
  },
  C:{
    callsZero:silenceZero.reason,
    forceFlat:silenceForce.reason,
    legsFlat:silenceLegs.reason,
    triggerFlat:{qqq:qRoll.mode,vxx:vRoll.mode,fire:qRoll.fire||vRoll.fire},
    summaryForce:{qqq:sumForce.rolls.qqq.status,vxx:sumForce.rolls.vxx.status},
    armedQqqFire:trigArmed.find(x=>x.id==="QQQ_ROLL").fire
  },
  PASS:true
}));
