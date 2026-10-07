import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

assert.ok(typeof E.memoryFromJournal==="function");
assert.ok(Array.isArray(E.JOURNAL_MEMORY_MAP));
assert.ok(E.JOURNAL_MEMORY_MAP.length>=17);

// ---------------------------------------------------------------------------
// 1) Happy path — 1:1 map from current_position + current_option_legs VALUE wrappers
// ---------------------------------------------------------------------------
const readyLeg={
  qty:{status:"VALUE",value:2},
  shortStrike:{status:"VALUE",value:820},
  longStrike:{status:"VALUE",value:830},
  expiry:{status:"VALUE",value:"2026-11-20"},
  dte:{status:"VALUE",value:44},
  delta:{status:"VALUE",value:0.10},
  entryCredit:{status:"VALUE",value:0.76},
  status:"READY",
  rollReady:true
};
const flatVxx={
  qty:{status:"VALUE",value:0},
  shortStrike:{status:"EMPTY",value:null},
  longStrike:{status:"EMPTY",value:null},
  expiry:{status:"EMPTY",value:null},
  dte:{status:"EMPTY",value:null},
  delta:{status:"EMPTY",value:null},
  entryCredit:{status:"EMPTY",value:null},
  status:"FLAT",
  rollReady:false
};
const row={
  event_id:"QHV3-TEST-14",
  current_position:{nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:0},
  current_option_legs:{qqq:readyLeg,vxx:flatVxx},
  // Candidate MUST NOT leak into Memory Current Leg fields
  candidates:{
    qqq:{shortStrike:999,longStrike:1005,dte:45,delta:0.12,credit:1.0},
    vxx:{shortStrike:40,longStrike:45,dte:45,delta:0.15,credit:0.5}
  }
};
const mapped=E.memoryFromJournal(row);
assert.strictEqual(mapped.sourceEventId,"QHV3-TEST-14");
assert.strictEqual(mapped.fields.nav,"100000");
assert.strictEqual(mapped.fields.qqqShares,"50");
assert.strictEqual(mapped.fields.vxxPct,"10");
assert.strictEqual(mapped.fields.qqqCalls,"2");
assert.strictEqual(mapped.fields.vxxCalls,"0","explicit journal 0 kept as VALUE(0)");
assert.strictEqual(mapped.fields.qqqShortStrike,"820");
assert.strictEqual(mapped.fields.qqqLongStrike,"830");
assert.strictEqual(mapped.fields.qqqExpiry,"2026-11-20");
assert.strictEqual(mapped.fields.qqqDte,"44");
assert.strictEqual(mapped.fields.qqqDelta,"0.1");
assert.strictEqual(mapped.fields.qqqEntryCredit,"0.76");
// VXX strikes EMPTY → null skip (not 0, not candidate 40/45)
assert.strictEqual(mapped.fields.vxxShortStrike,null);
assert.strictEqual(mapped.fields.vxxLongStrike,null);
assert.strictEqual(mapped.fields.vxxExpiry,null);
assert.ok(!mapped.skipped.includes("qqqCalls"));
assert.ok(mapped.skipped.includes("vxxShortStrike"));
assert.ok(mapped.warnings.some(w=>/candidates/i.test(w)),"warn that candidates ignored");
assert.notStrictEqual(mapped.fields.qqqShortStrike,"999","no candidate leak into qqqShortStrike");
assert.notStrictEqual(mapped.fields.vxxShortStrike,"40","no candidate leak into vxxShortStrike");

const preview=E.memoryMapPreview(mapped);
assert.ok(preview.some(l=>l.includes("current_position.qqqCalls → Memory qqqCalls = 2")));
assert.ok(preview.some(l=>l.includes("current_option_legs.qqq.shortStrike → Memory qqqShortStrike = 820")));
assert.ok(!preview.some(l=>l.includes("999")),"preview must not show candidate strikes");

// ---------------------------------------------------------------------------
// 2) Blank / missing → null (never write 0). No nav key → nav null.
// ---------------------------------------------------------------------------
const blankRow={
  event_id:"QHV3-BLANK",
  current_position:{qqqShares:1}, // vxxPct/qqqCalls/vxxCalls/nav missing
  current_option_legs:{
    qqq:{
      qty:{status:"VALUE",value:1},
      shortStrike:{status:"EMPTY",value:null},
      longStrike:{status:"EMPTY",value:null},
      expiry:{status:"EMPTY",value:null},
      dte:{status:"EMPTY",value:null},
      delta:{status:"EMPTY",value:null},
      entryCredit:{status:"EMPTY",value:null},
      status:"INCOMPLETE"
    }
  }
};
const blank=E.memoryFromJournal(blankRow);
assert.strictEqual(blank.fields.nav,null,"missing nav → leave EMPTY");
assert.strictEqual(blank.fields.qqqShares,"1");
assert.strictEqual(blank.fields.vxxPct,null);
assert.strictEqual(blank.fields.qqqCalls,null,"missing qqqCalls → null, not 0");
assert.strictEqual(blank.fields.vxxCalls,null);
assert.strictEqual(blank.fields.qqqShortStrike,null,"EMPTY shortStrike → null, not 0");
assert.strictEqual(blank.fields.qqqDte,null);

// ---------------------------------------------------------------------------
// 3) Explicit 0 kept for counts and DTE
// ---------------------------------------------------------------------------
const zeros={
  event_id:"QHV3-ZEROS",
  current_position:{nav:0,qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},
  current_option_legs:{
    qqq:{
      shortStrike:{status:"VALUE",value:0}, // unusual but VALUE(0) for number fields with allowZero
      dte:{status:"VALUE",value:0},
      delta:{status:"VALUE",value:0},
      entryCredit:{status:"VALUE",value:0},
      longStrike:{status:"EMPTY",value:null},
      expiry:{status:"EMPTY",value:null}
    },
    vxx:{}
  }
};
const z=E.memoryFromJournal(zeros);
assert.strictEqual(z.fields.nav,"0");
assert.strictEqual(z.fields.qqqShares,"0");
assert.strictEqual(z.fields.vxxPct,"0");
assert.strictEqual(z.fields.qqqCalls,"0");
assert.strictEqual(z.fields.vxxCalls,"0");
assert.strictEqual(z.fields.qqqDte,"0");
assert.strictEqual(z.fields.qqqDelta,"0");
assert.strictEqual(z.fields.qqqEntryCredit,"0");
assert.strictEqual(z.fields.qqqShortStrike,"0","VALUE(0) shortStrike kept");

// ---------------------------------------------------------------------------
// 4) Raw (non-wrapper) option leg scalars also map
// ---------------------------------------------------------------------------
const rawLegs={
  event_id:"QHV3-RAW",
  current_position:{qqqCalls:3,vxxCalls:1},
  current_option_legs:{
    qqq:{shortStrike:480,longStrike:490,expiry:"2026-12-18",dte:72,delta:0.11,entryCredit:1.25},
    vxx:{shortStrike:25,longStrike:30,expiry:"2026-12-18",dte:72,delta:0.18,entryCredit:0.55}
  }
};
const raw=E.memoryFromJournal(rawLegs);
assert.strictEqual(raw.fields.qqqCalls,"3");
assert.strictEqual(raw.fields.qqqShortStrike,"480");
assert.strictEqual(raw.fields.qqqLongStrike,"490");
assert.strictEqual(raw.fields.qqqExpiry,"2026-12-18");
assert.strictEqual(raw.fields.vxxShortStrike,"25");
assert.strictEqual(raw.fields.vxxEntryCredit,"0.55");

// ---------------------------------------------------------------------------
// 5) Round-trip via journalRecord — legs passed through; candidates not in current_position
// ---------------------------------------------------------------------------
const base={qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:8,termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"};
const buyE=E.derive(base);
const cur={nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:0};
const cand={shortStrike:999,longStrike:1005,dte:45,delta:0.12,credit:1,sizingAvailable:true,source:"LEAK_TEST"};
const book=E.targetLedger(base,buyE,cur,{qqq:cand});
const legs=E.currentOptionLegs({
  qqq:{qty:2,shortStrike:820,longStrike:830,expiry:"2026-11-20",dte:44,delta:0.10,entryCredit:0.76},
  vxx:{qty:0}
});
const rec=E.journalRecord({
  engine:buyE,
  book:{...book,current:{...book.current,nav:cur.nav}},
  candidates:{qqq:cand},
  currentOptionLegs:legs,
  optionsStatus:"LIVE"
});
assert.strictEqual(rec.current_position.nav,100000);
assert.ok(!("shortStrike" in rec.current_position));
const fromRec=E.memoryFromJournal({event_id:"QHV3-RT",...rec,candidates:{qqq:cand}});
assert.strictEqual(fromRec.fields.qqqCalls,"2");
assert.strictEqual(fromRec.fields.qqqShortStrike,"820");
assert.notStrictEqual(fromRec.fields.qqqShortStrike,"999");
assert.strictEqual(fromRec.fields.vxxCalls,"0");
assert.strictEqual(fromRec.fields.vxxShortStrike,null,"FLAT VXX EMPTY strikes → null");

console.log(JSON.stringify({
  cell:"14_JOURNAL_MEMORY",
  mapSize:E.JOURNAL_MEMORY_MAP.length,
  happy:{qqqCalls:mapped.fields.qqqCalls,qqqShortStrike:mapped.fields.qqqShortStrike,vxxCalls:mapped.fields.vxxCalls,vxxShortStrike:mapped.fields.vxxShortStrike},
  blankNeZero:{qqqCalls:blank.fields.qqqCalls,qqqShortStrike:blank.fields.qqqShortStrike},
  explicitZero:{qqqCalls:z.fields.qqqCalls,qqqDte:z.fields.qqqDte},
  noCandidateLeak:true,
  previewSample:preview.filter(l=>l.includes("qqqCalls")||l.includes("qqqShortStrike")),
  PASS:true
}));
