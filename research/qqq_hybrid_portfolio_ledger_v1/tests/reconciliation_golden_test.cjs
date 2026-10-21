const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(path.join(__dirname, "..", "reconciliation.js"), "utf8");
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(source, ctx);
const R = ctx.window.PortfolioReconciliationV1;

function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) throw new Error(label + ": expected " + expected + ", got " + actual);
}
function eq(actual, expected, label) {
  if (actual !== expected) throw new Error(label + ": expected " + expected + ", got " + actual);
}

const snap = {
  equity: 100000,
  positions: [
    { symbol:"QQQ", marketValue:40000 },
    { symbol:"VXX", marketValue:-15000 },
  ],
};

const ready = R.reconcile(snap, {
  available:true,
  connected:true,
  targets:{qqqCorePct:42, vxxPct:18},
});
eq(ready.status, "READY", "status");
near(ready.rows[0].actual, 40, 1e-12, "QQQ actual");
near(ready.rows[0].target, 42, 1e-12, "QQQ target");
near(ready.rows[0].gap, -2, 1e-12, "QQQ gap");
eq(ready.rows[0].action, "UNDERWEIGHT", "QQQ action");
near(ready.rows[1].actual, 15, 1e-12, "VXX short actual");
near(ready.rows[1].gap, -3, 1e-12, "VXX gap");
eq(ready.rows[1].action, "UNDERWEIGHT", "VXX action");
eq(ready.summary.comparable, 2, "comparable");
eq(ready.summary.unmapped, 2, "unmapped");

const aligned = R.reconcile(
  { equity:100000, positions:[
    {symbol:"QQQ", marketValue:42000},
    {symbol:"VXX", marketValue:-18000},
  ]},
  {available:true, connected:true, targets:{qqqCorePct:42, vxxPct:18}}
);
eq(aligned.rows[0].action, "ALIGNED", "QQQ aligned");
eq(aligned.rows[1].action, "ALIGNED", "VXX aligned");

const offline = R.reconcile(snap, {available:false, connected:false});
eq(offline.status, "UNAVAILABLE", "offline status");
eq(offline.summary.comparable, 0, "offline comparable");

console.log("RECONCILIATION GOLDEN TEST: PASS");
