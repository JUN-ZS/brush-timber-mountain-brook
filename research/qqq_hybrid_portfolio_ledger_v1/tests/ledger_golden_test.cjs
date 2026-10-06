const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(path.join(__dirname, "..", "ledger_engine.js"), "utf8");
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(source, ctx);
const L = ctx.window.PortfolioLedgerV1;

function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) {
    throw new Error(label + ": expected " + expected + ", got " + actual);
  }
}
function ok(value, label) {
  if (!value) throw new Error(label + ": expected truthy");
}

const events = [
  { type:"CASHFLOW", id:"cf1", timestamp:"2026-10-01T09:00:00Z", amount:100000 },
  { id:"b1", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:100, price:700, fees:10 },
  { id:"b2", timestamp:"2026-10-02T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:50, price:720, fees:5 },
  { id:"s1", timestamp:"2026-10-03T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"SELL", quantity:80, price:730, fees:8 },
  { id:"opt1", timestamp:"2026-10-03T11:00:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"SELL", quantity:2, price:12, multiplier:100, fees:4 },
];

const snap = L.snapshot(events, { QQQ: 740, QQQ261218C00750000: 8 });
console.log("DEBUG SNAP", JSON.stringify(snap));
near(snap.cash, 54773, 1e-9, "cash");
near(snap.equity, 104973, 1e-9, "equity");
near(snap.realizedPnl, 2400, 1e-9, "realized pnl");
near(snap.unrealizedPnl, 2600, 1e-9, "unrealized pnl");
near(snap.netPnl, 4973, 1e-9, "net pnl");
near(snap.totalFees, 27, 1e-9, "fees");

const qqq = snap.positions.find((x) => x.symbol === "QQQ");
near(qqq.quantity, 70, 1e-12, "QQQ quantity");
near(qqq.realizedPnl, 2400, 1e-9, "QQQ FIFO realized");
near(qqq.unrealizedPnl, 1800, 1e-9, "QQQ unrealized");

const short = snap.positions.find((x) => x.symbol === "QQQ261218C00750000");
near(short.quantity, -2, 1e-12, "option short quantity");
near(short.unrealizedPnl, 800, 1e-9, "option short unrealized");

const period = L.periodMetrics(
  events,
  "2026-10-01T09:00:00Z",
  "2026-10-03T23:00:00Z",
  { QQQ: 700, QQQ261218C00750000: 12 },
  { QQQ: 740, QQQ261218C00750000: 8 }
);
ok(period.complete, "period complete");
near(period.periodExternalCashFlow, 0, 1e-9, "period external CF");
near(period.pnl, 4973, 1e-9, "period pnl");
near(period.returnPct, 4.973, 1e-9, "period return");

const flowEvents = events.concat([
  { type:"CASHFLOW", id:"cf2", timestamp:"2026-10-02T12:00:00Z", amount:10000 }
]);
const period2 = L.periodMetrics(
  flowEvents,
  "2026-10-01T09:00:00Z",
  "2026-10-03T23:00:00Z",
  { QQQ: 700, QQQ261218C00750000: 12 },
  { QQQ: 740, QQQ261218C00750000: 8 }
);
near(period2.periodExternalCashFlow, 10000, 1e-9, "period flow");
near(period2.pnl, 4973, 1e-9, "flow-adjusted pnl");

const incomplete = L.periodMetrics(
  events,
  "2026-10-01T09:00:00Z",
  "2026-10-03T23:00:00Z",
  {},
  { QQQ: 740, QQQ261218C00750000: 8 }
);
ok(!incomplete.complete && incomplete.pnl === null, "incomplete period is blocked");

const crossing = [
  { type:"CASHFLOW", id:"cfx", timestamp:"2026-10-01T09:00:00Z", amount:1000 },
  { id:"bx", timestamp:"2026-10-01T10:00:00Z", symbol:"TEST", assetType:"EQUITY", side:"BUY", quantity:10, price:10 },
  { id:"sx", timestamp:"2026-10-02T10:00:00Z", symbol:"TEST", assetType:"EQUITY", side:"SELL", quantity:15, price:12 },
];
const crossSnap = L.snapshot(crossing, { TEST:10 });
const crossPos = crossSnap.positions.find((x) => x.symbol === "TEST");
near(crossPos.quantity, -5, 1e-12, "crossed short quantity");
near(crossPos.realizedPnl, 20, 1e-9, "crossed realized pnl");
near(crossPos.unrealizedPnl, 10, 1e-9, "crossed unrealized pnl");
near(crossSnap.equity, 30, 1e-9, "crossed equity");

const defaultOption = L.normalizeEvent({
  id:"opt-default", timestamp:"2026-10-04T10:00:00Z", symbol:"QQQ-OPT",
  assetType:"OPTION", side:"SELL", quantity:1, price:5
});
near(defaultOption.multiplier, 100, 1e-12, "option default multiplier");
if (Object.prototype.hasOwnProperty.call(defaultOption, "pnl")) {
  throw new Error("fill must not accept stored P&L as truth");
}

let mismatchCaught = false;
try {
  L.snapshot([
    { id:"m1", timestamp:"2026-10-01T10:00:00Z", symbol:"M", assetType:"EQUITY", side:"BUY", quantity:1, price:10 },
    { id:"m2", timestamp:"2026-10-02T10:00:00Z", symbol:"M", assetType:"OPTION", side:"SELL", quantity:1, price:1 },
  ], { M: 10 });
} catch (err) {
  mismatchCaught = /asset type mismatch/.test(String(err));
}
ok(mismatchCaught, "asset mismatch blocked");

console.log("LEDGER GOLDEN TEST: PASS");
