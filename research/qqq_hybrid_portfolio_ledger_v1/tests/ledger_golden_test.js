const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(path.join(__dirname, "..", "ledger_engine.js"), "utf8");
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(source, ctx);
const L = ctx.window.PortfolioLedgerV1;

function eq(actual, expected, label) {
  if (actual !== expected) throw new Error(label + ": expected " + expected + ", got " + actual);
}
function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) throw new Error(label + ": expected " + expected + ", got " + actual);
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
near(snap.cash, 100000 - 100*700-10 - 50*720-5 + 80*730-8 + 2*12*100-4, 1e-9, "cash");
eq(snap.positions.length, 2, "position count");

const qqq = snap.positions.find((x) => x.symbol === "QQQ");
near(qqq.quantity, 70, 1e-12, "QQQ quantity");
near(qqq.realizedPnl, 80*(730-700), 1e-9, "QQQ FIFO realized");
near(qqq.unrealizedPnl, 20*(740-700) + 50*(740-720), 1e-9, "QQQ unrealized");

const short = snap.positions.find((x) => x.symbol === "QQQ261218C00750000");
near(short.quantity, -2, 1e-12, "option short quantity");
near(short.unrealizedPnl, (12-8)*2*100, 1e-9, "option short unrealized");

near(snap.totalFees, 27, 1e-9, "fees");
near(snap.realizedPnl, 2400, 1e-9, "total realized");
near(snap.unrealizedPnl, 3000, 1e-9, "total unrealized");
near(snap.netPnl, 5400 - 27, 1e-9, "net pnl");

const period = L.periodMetrics(
  events,
  "2026-10-01T09:00:00Z",
  "2026-10-03T23:00:00Z",
  { QQQ: 700, QQQ261218C00750000: 0 },
  { QQQ: 740, QQQ261218C00750000: 8 }
);
ok(period.complete, "period complete");
near(period.periodExternalCashFlow, 0, 1e-9, "period external CF");
near(period.pnl, period.endEquity - period.startEquity, 1e-9, "period pnl");

const flowEvents = events.concat([
  { type:"CASHFLOW", id:"cf2", timestamp:"2026-10-02T12:00:00Z", amount:10000 }
]);
const period2 = L.periodMetrics(
  flowEvents,
  "2026-10-01T09:00:00Z",
  "2026-10-03T23:00:00Z",
  { QQQ: 700, QQQ261218C00750000: 0 },
  { QQQ: 740, QQQ261218C00750000: 8 }
);
near(period2.periodExternalCashFlow, 10000, 1e-9, "period flow");
near(period2.pnl, period2.endEquity - period2.startEquity - 10000, 1e-9, "flow-adjusted pnl");

console.log("LEDGER GOLDEN TEST: PASS");
