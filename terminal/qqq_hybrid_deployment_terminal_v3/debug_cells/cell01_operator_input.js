import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const zero=E.operatorNumber("0",{min:0});
const empty=E.operatorNumber("",{min:0});
const invalid=E.operatorNumber("abc",{min:0});
const negative=E.operatorNumber("-1",{min:0});
const value=E.operatorNumber("12.5",{min:0});

assert.deepStrictEqual(zero,{status:"VALUE",value:0});
assert.deepStrictEqual(empty,{status:"EMPTY",value:null});
assert.deepStrictEqual(invalid,{status:"INVALID",value:null});
assert.deepStrictEqual(negative,{status:"INVALID",value:null});
assert.deepStrictEqual(value,{status:"VALUE",value:12.5});

console.log(JSON.stringify({
  cell:"01_OPERATOR_INPUT",
  zero,
  empty,
  invalid,
  negative,
  value,
  PASS:true
}));
