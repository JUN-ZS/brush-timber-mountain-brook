import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const base={
  qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:8,
  termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"
};
const ready=x=>({...x,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}});

function setup(data=base,position={qqqShares:100,vxxPct:10,qqqCalls:2,vxxCalls:1},funding={strategyPool:"100000",newCapital:"5000"},candidates={}){
  const e=E.derive(data);
  const book=E.targetLedger(data,e,ready({nav:100000,...position}),candidates);
  const f=E.fundingPlan({
    d:data,e,
    book:{current:{...book.current,nav:100000}},
    strategyPool:funding.strategyPool,
    newCapital:funding.newCapital
  });
  return{e,book,f};
}

// 1) CARRY -> REBALANCE when frozen target has both additions and reductions; engine action remains BUY.
{
  const {e,book,f}=setup();
  const b=E.strategyActionBridge({d:base,e,book,funding:f,currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),journalRows:[]});
  assert.strictEqual(b.actionClass,"REBALANCE");
  assert.strictEqual(b.regime,"CARRY");
  assert.strictEqual(b.engineAction,"BUY");
  assert.strictEqual(b.qqqCoreTargetPct,42);
  assert.strictEqual(b.noBrokerOrder,true);
  assert.strictEqual(b.funding.status,"CONTEXT_ONLY");
  assert.strictEqual(b.funding.promotion,"RESEARCH_ONLY_NOT_EXECUTION");
  assert.ok(Array.isArray(b.closedLoop)&&b.closedLoop.length===7);
}

// 2) HOLD/WEAKENING -> MAINTAIN; pool route is displayed but cannot become execution class.
{
  const data={...base,s:3};
  const {e,book,f}=setup(data);
  const b=E.strategyActionBridge({d:data,e,book,funding:f,currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),journalRows:[]});
  assert.strictEqual(b.actionClass,"MAINTAIN");
  assert.strictEqual(b.engineAction,"HOLD");
  assert.strictEqual(b.funding.route,"QQQ CORE ONLY");
  assert.strictEqual(b.actionClass==="QQQ CORE ONLY",false);
}

// 3) SHOCK -> DEFEND and never BUILD.
{
  const data={...base,vix:32,s:-1};
  const {e,book,f}=setup(data);
  const b=E.strategyActionBridge({d:data,e,book,funding:f,currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),journalRows:[]});
  assert.strictEqual(b.actionClass,"DEFEND");
  assert.strictEqual(b.funding.route,"DEFENSIVE / RESERVE");
  assert.ok(!b.actionClass.includes("BUILD"));
}

// 4) BLOCKED -> PAUSE and target is current.
{
  const data={...base,m1:null,m2:null,s:null};
  const {e,book,f}=setup(data);
  const b=E.strategyActionBridge({d:data,e,book,funding:f,currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),journalRows:[]});
  assert.strictEqual(b.actionClass,"PAUSE");
  assert.deepStrictEqual(b.target,b.current);
  assert.strictEqual(b.nextStep,"WATCH_NEXT_TRANSITION");
}

// 5) Journal baseline feeds bridge status, but does not become a decision override.
{
  const {e,book,f}=setup();
  const old={event_id:"QHV3-test",state:"WEAKENING",engine_action:"HOLD",target_position:{qqqShares:1,vxxPct:0,qqqCalls:0,vxxCalls:0},conflict:"NONE"};
  const b=E.strategyActionBridge({d:base,e,book,funding:f,currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),journalRows:[old]});
  assert.strictEqual(b.journal.eventId,"QHV3-test");
  assert.strictEqual(b.journal.changed,true);
  assert.strictEqual(b.actionClass,"REBALANCE");
}

// 6) Journal contract persists only the bridge's operator-facing outcome.
{
  const {e,book,f}=setup();
  const bridge=E.strategyActionBridge({d:base,e,book,funding:f,currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),journalRows:[]});
  const rec=E.journalRecord({
    engine:e,book:{...book,current:{...book.current,nav:100000}},
    humanAction:null,optionsStatus:null,candidates:{},currentOptionLegs:E.currentOptionLegs({qqq:{qty:2},vxx:{qty:1}}),
    funding:f,actionBridge:bridge
  });
  assert.strictEqual(rec.action_bridge.version,"CELL16-V1");
  assert.strictEqual(rec.action_bridge.no_broker_order,true);
  assert.strictEqual(rec.funding_context.route,f.route);
}

console.log(JSON.stringify({
  cell:"16_STRATEGY_ACTION_BRIDGE",
  checks:6,
  cases:["CARRY/REBALANCE","WEAKENING/MAINTAIN","SHOCK/DEFEND","BLOCKED/PAUSE","JOURNAL_BASELINE","JOURNAL_BRIDGE"],
  PASS:true
}));
