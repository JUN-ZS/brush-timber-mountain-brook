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
  qqq:750,vxx:20,vix:16,m1:16.2,m2:17.2,s:((17.2-16.2)/16.2)*100,
  termAsOf:"2026-10-07",spotAsOf:"2026-10-07",today:"2026-10-07"
};

const carry=E.derive(base);
const thin=E.derive({...base,s:3});
const back=E.derive({...base,s:-1});
const shock=E.derive({...base,vix:32,s:-4});

assert.strictEqual(carry.action,"BUY");
assert.strictEqual(carry.gate,"OPEN");
assert.strictEqual(thin.action,"HOLD");
assert.strictEqual(thin.gate,"WATCH");
assert.strictEqual(back.action,"REDUCE");
assert.strictEqual(shock.state,"SHOCK");

console.log(JSON.stringify({
  cell:"02_DECISION",
  results:[
    {name:"CARRY",state:carry.state,action:carry.action,gate:carry.gate},
    {name:"THIN",state:thin.state,action:thin.action,gate:thin.gate},
    {name:"BACKWARDATION",state:back.state,action:back.action,gate:back.gate},
    {name:"SHOCK",state:shock.state,action:shock.action,gate:shock.gate}
  ],
  PASS:true
}));
