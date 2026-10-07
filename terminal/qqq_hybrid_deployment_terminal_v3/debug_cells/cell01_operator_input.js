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

// F6: plain decimals only. Thousands separators are explicit; ambiguous text is INVALID, never re-read.
const strict={
  comma:E.operatorNumber("100,000",{min:0}),
  commaDecimal:E.operatorNumber("1,234.5",{min:0}),
  padded:E.operatorNumber(" 5 ",{min:0}),
  leadingDot:E.operatorNumber(".5",{min:0}),
  hex:E.operatorNumber("0x10",{min:0}),
  euroDecimal:E.operatorNumber("1,5",{min:0}),
  badGroups:E.operatorNumber("1,2,3",{min:0}),
  exponent:E.operatorNumber("1e3",{min:0}),
  trailingText:E.operatorNumber("5abc",{min:0}),
  infinity:E.operatorNumber("Infinity",{min:0}),
  dotOnly:E.operatorNumber(".",{min:0}),
  numberType:E.operatorNumber(0.12,{min:0}),
  tinyNumberType:E.operatorNumber(1e-7,{min:0}),
  debit:E.operatorNumber("-0.35",{min:Number.NEGATIVE_INFINITY})
};
assert.deepStrictEqual(strict.comma,{status:"VALUE",value:100000});
assert.deepStrictEqual(strict.commaDecimal,{status:"VALUE",value:1234.5});
assert.deepStrictEqual(strict.padded,{status:"VALUE",value:5});
assert.deepStrictEqual(strict.leadingDot,{status:"VALUE",value:0.5});
for(const k of ["hex","euroDecimal","badGroups","exponent","trailingText","infinity","dotOnly"]){
  assert.deepStrictEqual(strict[k],{status:"INVALID",value:null},k);
}
assert.deepStrictEqual(strict.numberType,{status:"VALUE",value:0.12});
assert.deepStrictEqual(strict.tinyNumberType,{status:"VALUE",value:1e-7});
assert.deepStrictEqual(strict.debit,{status:"VALUE",value:-0.35});

console.log(JSON.stringify({
  cell:"01_OPERATOR_INPUT",
  zero,
  empty,
  invalid,
  negative,
  value,
  PASS:true
}));
