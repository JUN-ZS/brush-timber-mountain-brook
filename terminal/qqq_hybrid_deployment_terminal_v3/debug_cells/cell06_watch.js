import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const d={
  qqq:750,vxx:20,vix:16,m1:16.2,m2:16.2,s:0.1,
  termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"
};
const hold=E.derive({...d,s:3});
const rowsNoPosition=E.triggers(d,hold,{hasQQQCall:false,hasVXXCall:false});
const q=rowsNoPosition.find(x=>x.id==="QQQ_ROLL");
const v=rowsNoPosition.find(x=>x.id==="VXX_ROLL");
const thin=rowsNoPosition.find(x=>x.id==="S_SAFE");

assert.strictEqual(q.fire,false);
assert.strictEqual(q.mode,"NO_POSITION");
assert.strictEqual(v.fire,false);
assert.strictEqual(v.mode,"NO_POSITION");
assert.strictEqual(thin.fire,false);
assert.strictEqual(thin.mode,"WATCH");

const incomplete=E.triggers(d,hold,{hasQQQCall:true,hasVXXCall:true,qqqDte:"",qqqDelta:"",vxxDte:"",vxxDelta:""});
assert.strictEqual(incomplete.find(x=>x.id==="QQQ_ROLL").mode,"NEEDS_POSITION_DATA");
assert.strictEqual(incomplete.find(x=>x.id==="VXX_ROLL").mode,"NEEDS_POSITION_DATA");

const armed=E.triggers(d,hold,{hasQQQCall:true,hasVXXCall:true,qqqDte:10,qqqDelta:0.12,vxxDte:30,vxxDelta:0.12});
assert.strictEqual(armed.find(x=>x.id==="QQQ_ROLL").fire,true);
assert.strictEqual(armed.find(x=>x.id==="VXX_ROLL").fire,false);

console.log(JSON.stringify({
  cell:"06_WATCH",
  noPosition:{qqq:q.mode,vxx:v.mode,thin:thin.mode},
  incomplete:{
    qqq:incomplete.find(x=>x.id==="QQQ_ROLL").mode,
    vxx:incomplete.find(x=>x.id==="VXX_ROLL").mode
  },
  armed:{
    qqq:armed.find(x=>x.id==="QQQ_ROLL").fire,
    vxx:armed.find(x=>x.id==="VXX_ROLL").fire
  },
  PASS:true
}));
