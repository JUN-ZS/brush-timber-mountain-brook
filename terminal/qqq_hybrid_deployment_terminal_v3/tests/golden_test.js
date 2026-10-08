
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
// F4 HOLD trim: never add; VXX above frozen 18% target is trimmed to target.
{
  const thin={...base,vix:20,s:3};
  const eH=E.derive(thin);
  for(const [vxx,wantVxx,wantClass] of [[25,18,"TRIM"],[10,10,"MAINTAIN"],[18,18,"MAINTAIN"]]){
    const bk=E.targetLedger(thin,eH,{nav:100000,qqqShares:100,vxxPct:vxx,qqqCalls:2,vxxCalls:1});
    assert.deepStrictEqual(bk.target,{qqqShares:100,vxxPct:wantVxx,qqqCalls:2,vxxCalls:1},"HOLD target VXX "+vxx);
    const br=E.strategyActionBridge({d:thin,e:eH,book:bk,funding:{}});
    assert.strictEqual(br.actionClass,wantClass,"HOLD class VXX "+vxx);
    assert.strictEqual(br.noBrokerOrder,true);
  }
}

const exactFive={...base,m1:16,m2:16.8,s:((16.8-16)/16)*100};
assert.strictEqual(E.normalizeTermSlope(exactFive.s),5,"S=5 exact boundary normalization");
assert.strictEqual(E.derive(exactFive).state,"WEAKENING","S=5 exact boundary must remain HOLD");
assert.strictEqual(E.derive({...exactFive,s:5.000001}).state,"CARRY","S just above 5 must remain CARRY");
assert.strictEqual(E.derive({...base,termAsOf:"2026-10-09",spotAsOf:"2026-10-08",today:"2026-10-08"}).health.code,"TERM_DATE_FUTURE");
assert.strictEqual(E.derive({...base,termAsOf:"2026-10-08",spotAsOf:"2026-10-09",today:"2026-10-08"}).health.code,"SPOT_DATE_FUTURE");
{
  const permCarryData={...base,s:8};
  const permCarryE=E.derive(permCarryData),permCand={credit:1,sizingAvailable:true};
  const permCarryBook=E.targetLedger(permCarryData,permCarryE,{nav:100000,qqqShares:40,vxxPct:10,qqqCalls:2,vxxCalls:3,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}},{qqq:permCand,vxx:permCand});
  const pc=E.permissionLedger(permCarryData,permCarryE,permCarryBook,{qqq:permCand,vxx:permCand},100000);
  assert.strictEqual(pc.status,"CARRY / BUILD TOWARD FULL"); assert.strictEqual(pc.rows[0].maxBuy,16); assert.strictEqual(pc.rows[1].maxBuy,8);
  assert.strictEqual(pc.rows[2].maxBuy,10); assert.strictEqual(pc.rows[3].maxBuy,17);

  const permHoldData={...base,s:3},permHoldE=E.derive(permHoldData);
  const permHoldBook=E.targetLedger(permHoldData,permHoldE,{nav:100000,qqqShares:100,vxxPct:25,qqqCalls:2,vxxCalls:1,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}},{});
  const ph=E.permissionLedger(permHoldData,permHoldE,permHoldBook,{},100000);
  assert.strictEqual(ph.status,"HOLD / NO NEW CARRY"); assert.strictEqual(ph.rows[0].maxBuy,0); assert.strictEqual(ph.rows[1].nowMax,18); assert.strictEqual(ph.rows[1].maxSell,7); assert.strictEqual(ph.rows[2].maxBuy,0); assert.strictEqual(ph.rows[3].maxBuy,0);
  const overCapHoldBook=E.targetLedger(permHoldData,permHoldE,{nav:100000,qqqShares:100,vxxPct:25,qqqCalls:1000,vxxCalls:1000,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}},{qqq:permCand,vxx:permCand});
  assert.strictEqual(overCapHoldBook.target.qqqCalls,12,"HOLD trims QQQ far-call to frozen capacity");
  assert.strictEqual(overCapHoldBook.target.vxxCalls,20,"HOLD trims VXX call to frozen capacity");
  assert.strictEqual(overCapHoldBook.deltas.qqqCalls,-988); assert.strictEqual(overCapHoldBook.deltas.vxxCalls,-980);
  const phOverCap=E.permissionLedger(permHoldData,permHoldE,overCapHoldBook,{qqq:permCand,vxx:permCand},100000);
  assert.strictEqual(phOverCap.rows[2].nowMax,12); assert.strictEqual(phOverCap.rows[2].maxBuy,0); assert.strictEqual(phOverCap.rows[2].maxSell,988);
  assert.strictEqual(phOverCap.rows[3].nowMax,20); assert.strictEqual(phOverCap.rows[3].maxBuy,0); assert.strictEqual(phOverCap.rows[3].maxSell,980);

  const permReduceData={...base,vix:32,s:-4},permReduceE=E.derive(permReduceData);
  const permReduceBook=E.targetLedger(permReduceData,permReduceE,{nav:100000,qqqShares:100,vxxPct:18,qqqCalls:21,vxxCalls:4,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}},{});
  const pr=E.permissionLedger(permReduceData,permReduceE,permReduceBook,{},100000);
  assert.strictEqual(pr.status,"SHOCK / CUT"); assert.strictEqual(pr.rows[0].maxSell,0); assert.strictEqual(pr.rows[1].nowMax,0); assert.strictEqual(pr.rows[1].maxSell,18); assert.strictEqual(pr.rows[2].maxSell,21); assert.strictEqual(pr.rows[3].maxSell,4);

  const permBlockedData={...base,m1:null,m2:null,s:null},permBlockedE=E.derive(permBlockedData);
  const permBlockedBook=E.targetLedger(permBlockedData,permBlockedE,{nav:100000,qqqShares:100,vxxPct:18,qqqCalls:21,vxxCalls:4,inputStatus:{status:"READY",invalid:[],empty:[],fields:{}}},{});
  const pb=E.permissionLedger(permBlockedData,permBlockedE,permBlockedBook,{},100000);
  assert.strictEqual(pb.status,"BLOCKED / NO TRADE"); assert.ok(pb.rows.every(r=>r.maxBuy===0&&r.maxSell===0));
  assert.ok(pb.note.includes("資料未通過"),"blocked permission must use blocked note");
  assert.ok(!pb.note.includes("可留"),"blocked permission must not use HOLD wording");

  // UI contract regression: QQQ FULL is presented as frozen 42% NAV plus approximate share count.
  const appSource=fs.readFileSync(path.join(here,"..","app.js"),"utf8");
  assert.ok(appSource.includes('"42% NAV (≈"+fmt(r.full,0)+" shares)"'),"QQQ FULL display contract");
}

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
const cell17=spawnSync(process.execPath,[path.join(here,"..","debug_cells","cell17_beginner_guided_input.js"),"--self-test"],{encoding:"utf8"});
assert.strictEqual(cell17.status,0,"cell17_beginner_guided_input --self-test must PASS\n"+cell17.stdout+"\n"+cell17.stderr);
assert.ok(String(cell17.stdout).includes('"PASS":true'),"cell17 PASS marker");
console.log("V3 golden + Cell 14/15/16 operator loop PASS");
