import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert";

globalThis.window = {};
vm.runInThisContext(fs.readFileSync(new URL("../engine.js", import.meta.url), "utf8"));
const E = globalThis.window.M1M2Lab;

const rows = [
  {Date:"2022-01-03",VIX:"20",M1:"22",M2:"24"},
  {Date:"2022-01-04",VIX:"22",M1:"23",M2:"25"},
  {Date:"2022-01-05",VIX:"24",M1:"26",M2:"25"},
  {Date:"2022-01-06",VIX:"18",M1:"20",M2:"22"}
];

const masked = E.buildMaskedInput(rows);
const a = E.reconstructSeries(masked);
const b = E.reconstructSeries(masked);
assert.deepStrictEqual(a, b, "determinism");

const expectedLift = 0.10 * Math.tanh((20 - 20) / 6);
assert.strictEqual(a[0].m1, 20, "row0 m1 proxy");
assert.strictEqual(a[0].m2, 20 * (1 + expectedLift), "row0 m2 proxy");

const comp = E.compare(rows, a);
assert.strictEqual(comp.metrics.n, rows.length, "row count");

const audit = E.leakageAudit(rows);
assert.strictEqual(audit.pass, true, "future truth must not affect prior reconstruction");

const test = E.action(E.term(24, 25), 20);
assert.strictEqual(test, "BUY", "positive contango > 5%");

const shock = E.action(E.term(28, 27), 32);
assert.strictEqual(shock, "REDUCE", "high VIX + backwardation");
console.log("M1/M2 reconstruction lab golden tests PASS");
