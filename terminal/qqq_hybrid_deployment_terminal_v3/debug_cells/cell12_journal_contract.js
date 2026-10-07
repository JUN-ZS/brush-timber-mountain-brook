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
const thin={...base,s:3}; // HOLD / WATCH
const current={nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:3};
const candidate={shortStrike:850,longStrike:865,dte:45,delta:0.10,credit:1,sizingAvailable:true,source:"DEBUG_FIXTURE"};

// 1) HOLD + no candidate + current calls 2/3 → option deltas 0; conflict NONE
const holdE=E.derive(thin);
assert.strictEqual(holdE.action,"HOLD");
const holdBook=E.targetLedger(thin,holdE,current,{});
const holdRec=E.journalRecord({engine:holdE,book:holdBook,candidates:{},optionsStatus:null});
assert.strictEqual(holdRec.deltas.qqqCalls,0);
assert.strictEqual(holdRec.deltas.vxxCalls,0);
assert.strictEqual(holdRec.conflict,"NONE");
assert.strictEqual(holdRec.deltas_guarded,false);
assert.strictEqual(holdRec.candidate_present.qqq,false);
assert.strictEqual(holdRec.candidate_present.vxx,false);

// 2) BUY + SOURCE_DOWN + calls 2 → option deltas 0
const buyE=E.derive(base);
assert.strictEqual(buyE.action,"BUY");
const buyCur={nav:100000,qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:2};
const buyBook=E.targetLedger(base,buyE,buyCur,{});
const buyRec=E.journalRecord({
  engine:buyE,book:buyBook,candidates:{},optionsStatus:"OPTIONS_SOURCE_DOWN"
});
assert.strictEqual(buyRec.deltas.qqqCalls,0);
assert.strictEqual(buyRec.deltas.vxxCalls,0);
assert.strictEqual(buyRec.options_status,"OPTIONS_SOURCE_DOWN");
assert.strictEqual(buyRec.conflict,"NONE");

// 3) human REDUCE vs engine HOLD → CONFLICT
const conflictRec=E.journalRecord({
  engine:holdE,book:holdBook,humanAction:"REDUCE",candidates:{},optionsStatus:null
});
assert.strictEqual(conflictRec.conflict,"CONFLICT");
assert.strictEqual(conflictRec.human_action,"REDUCE");
assert.strictEqual(conflictRec.engine_action,"HOLD");

// 4) synthetic bad book (HOLD + delta qqqCalls -2) → DELTA_ACTION_MISMATCH + guarded zeros
const badBook={
  current:{qqqShares:50,vxxPct:10,qqqCalls:2,vxxCalls:3},
  target:{qqqShares:50,vxxPct:10,qqqCalls:0,vxxCalls:3},
  deltas:{qqqShares:0,vxxPct:0,qqqCalls:-2,vxxCalls:0}
};
const mismatchRec=E.journalRecord({
  engine:holdE,book:badBook,candidates:{},optionsStatus:"OPTIONS_SOURCE_DOWN"
});
assert.strictEqual(mismatchRec.conflict,"DELTA_ACTION_MISMATCH");
assert.strictEqual(mismatchRec.deltas.qqqCalls,0);
assert.strictEqual(mismatchRec.target_position.qqqCalls,2);
assert.strictEqual(mismatchRec.deltas_guarded,true);

// Also: HOLD + negative delta without candidate (null status) → mismatch
const mismatchNoStatus=E.journalRecord({
  engine:holdE,book:badBook,candidates:{}
});
assert.strictEqual(mismatchNoStatus.conflict,"DELTA_ACTION_MISMATCH");
assert.strictEqual(mismatchNoStatus.deltas.qqqCalls,0);

// 5) record has no candidate strikes under current_position
const withCand=E.journalRecord({
  engine:buyE,
  book:E.targetLedger(base,buyE,buyCur,{qqq:candidate}),
  candidates:{qqq:candidate},
  optionsStatus:"LIVE"
});
assert.ok(!("shortStrike" in withCand.current_position));
assert.ok(!("longStrike" in withCand.current_position));
assert.ok(!("expiry" in withCand.current_position));
assert.strictEqual(withCand.current_position.qqqCalls,2);
assert.ok(!("current_option_legs" in withCand)); // not passed → not invented from candidate

// Explicit identity only when passed
const legs=E.currentOptionLegs({
  qqq:{qty:2,shortStrike:480,longStrike:490,expiry:"2026-11-20",dte:44,delta:0.10},
  vxx:{qty:0}
});
const withLegs=E.journalRecord({
  engine:holdE,book:holdBook,candidates:{qqq:candidate},currentOptionLegs:legs
});
assert.ok(withLegs.current_option_legs);
assert.strictEqual(withLegs.current_option_legs.qqq.status,"READY");
assert.strictEqual(withLegs.current_option_legs.qqq.shortStrike.value,480);
// Candidate strikes must not overwrite current_position
assert.notStrictEqual(withLegs.current_position.qqqCalls,candidate.shortStrike);
assert.ok(!("shortStrike" in withLegs.current_position));

// Human CONFLICT takes precedence over delta mismatch
const both=E.journalRecord({
  engine:holdE,book:badBook,humanAction:"REDUCE",candidates:{},optionsStatus:"OPTIONS_SOURCE_DOWN"
});
assert.strictEqual(both.conflict,"CONFLICT");
assert.strictEqual(both.deltas.qqqCalls,0);
assert.strictEqual(both.deltas_guarded,true);

// 6) HOLD trim is a valid operator action, not a false delta/action mismatch.
{
  const trimCur={nav:100000,qqqShares:50,vxxPct:25,qqqCalls:2,vxxCalls:3};
  const trimBook=E.targetLedger(thin,holdE,trimCur,{});
  const bridge=E.strategyActionBridge({d:thin,e:holdE,book:trimBook,funding:{}});
  const rec=E.journalRecord({engine:holdE,book:trimBook,candidates:{},optionsStatus:"OPTIONS_SOURCE_DOWN",actionBridge:bridge});
  assert.strictEqual(rec.engine_action,"HOLD");
  assert.strictEqual(rec.conflict,"NONE");
  assert.strictEqual(rec.deltas.vxxPct,-7);
  assert.strictEqual(rec.target_position.vxxPct,18);
  assert.strictEqual(rec.action_bridge.action_class,"TRIM");
  const humanTrim=E.journalRecord({engine:holdE,book:trimBook,humanAction:"trim",candidates:{},actionBridge:bridge});
  assert.strictEqual(humanTrim.conflict,"NONE");
  const humanBuy=E.journalRecord({engine:holdE,book:trimBook,humanAction:"BUY",candidates:{},actionBridge:bridge});
  assert.strictEqual(humanBuy.conflict,"CONFLICT");
}

console.log(JSON.stringify({
  cell:"12_JOURNAL_CONTRACT",
  hold:{conflict:holdRec.conflict,deltas:holdRec.deltas},
  buySourceDown:{conflict:buyRec.conflict,deltas:buyRec.deltas,options_status:buyRec.options_status},
  humanConflict:conflictRec.conflict,
  deltaMismatch:{conflict:mismatchRec.conflict,deltas:mismatchRec.deltas,deltas_guarded:mismatchRec.deltas_guarded},
  noCandidateStrikesInCurrent:true,
  PASS:true
}));
