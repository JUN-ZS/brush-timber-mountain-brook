import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
globalThis.window={};
vm.runInThisContext(fs.readFileSync(path.join(here,"..","engine.js"),"utf8"));
const E=globalThis.window.HybridEngineV3;

const chain=[
  {expiration:"2026-11-20",strike:850,bid:2.00,ask:2.10,impliedVolatility:0.28},
  {expiration:"2026-11-20",strike:865,bid:0.90,ask:1.00,impliedVolatility:0.28},
  {expiration:"2026-12-18",strike:850,bid:3.00,ask:3.10,impliedVolatility:0.28},
  {expiration:"2026-12-18",strike:865,bid:1.60,ask:1.70,impliedVolatility:0.28}
];

const cand=E.candidateFromChain(chain,750,0.10,45,"2026-10-07");
assert.ok(cand);
assert.strictEqual(cand.shortStrike,850);
assert.strictEqual(cand.longStrike,865);
assert.strictEqual(cand.credit,1);
assert.strictEqual(cand.sizingAvailable,true);

console.log(JSON.stringify({
  cell:"04_CANDIDATE",
  shortStrike:cand.shortStrike,
  longStrike:cand.longStrike,
  dte:cand.dte,
  delta:cand.delta,
  credit:cand.credit,
  source:cand.source,
  PASS:true
}));
