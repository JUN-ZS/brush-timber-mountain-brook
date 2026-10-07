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
  "2026-10-02T23:00:00Z",
  "2026-10-03T23:00:00Z",
  {},
  { QQQ: 740, QQQ261218C00750000: 8 }
);
ok(!incomplete.complete && incomplete.pnl === null, "incomplete held-position period is blocked");

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
near(crossSnap.equity, 1030, 1e-9, "crossed equity");
near(crossSnap.netPnl, 30, 1e-9, "crossed net pnl");



// DATA-INTEGRITY V2: explicit timezone, stable id, multiplier/fee validation, non-negative marks
let caught = false;
try { L.normalizeEvent({ type:"FILL", timestamp:"2026-10-07T10:00:00", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:1, price:100 }); }
catch (err) { caught = /event id is required/.test(String(err)); }
ok(caught, "missing event id blocked before timestamp ambiguity");

caught = false;
try { L.normalizeEvent({ id:"naive-ts", type:"FILL", timestamp:"2026-10-07T10:00:00", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:1, price:100 }); }
catch (err) { caught = /timestamp is invalid/.test(String(err)); }
ok(caught, "timezone-less timestamp blocked");

caught = false;
try { L.normalizeEvent({ id:"bad-mult", type:"FILL", timestamp:"2026-10-07T10:00:00Z", symbol:"QQQ-OPT", assetType:"OPTION", side:"BUY", quantity:1, price:2, multiplier:0 }); }
catch (err) { caught = /multiplier must be > 0/.test(String(err)); }
ok(caught, "invalid multiplier blocked");

caught = false;
try { L.normalizeEvent({ id:"bad-fee", type:"FILL", timestamp:"2026-10-07T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:1, price:100, fees:"oops" }); }
catch (err) { caught = /fees must be >= 0/.test(String(err)); }
ok(caught, "invalid fees blocked");

caught = false;
try { L.parseMarksObject({ QQQ: -1 }, "manual marks"); }
catch (err) { caught = /finite non-negative number/.test(String(err)); }
ok(caught, "negative manual mark blocked");

const negativeSnap = L.snapshot([
  { type:"CASHFLOW", id:"pcf", timestamp:"2026-10-01T09:00:00Z", amount:1000 },
  { id:"peq", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:1, price:100 }
], { QQQ: -1 });
ok(negativeSnap.positions[0].mark === null, "negative live mark treated as unusable");
ok(!negativeSnap.coverage.allMarksPresent, "negative mark cannot complete valuation");

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


// BLOCKER B: ledger snapshot must not coerce null/blank mark to 0
const nullSnap = L.snapshot([
  { type:"CASHFLOW", id:"ncf", timestamp:"2026-10-01T09:00:00Z", amount:100000 },
  { id:"neq", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:1, price:100, fees:0 }
], { QQQ: null });
ok(nullSnap.positions[0].mark === null, "ledger null mark stays null");
ok(!nullSnap.coverage.allMarksPresent, "ledger null mark incomplete coverage");

let parseNullCaught = false;
try { L.parseMarksObject({ QQQ: null }, "manual marks"); }
catch (err) { parseNullCaught = /missing \(null\/blank\)/.test(String(err)); }
ok(parseNullCaught, "parseMarksObject rejects null");

let parseBlankCaught = false;
try { L.parseMarksObject({ QQQ: "" }, "manual marks"); }
catch (err) { parseBlankCaught = /missing \(null\/blank\)/.test(String(err)); }
ok(parseBlankCaught, "parseMarksObject rejects blank");

const parsed = L.parseMarksObject({ qqq: "742.5" }, "manual marks");
near(parsed.QQQ, 742.5, 1e-12, "parseMarksObject uppercases and parses");

// BLOCKER C: historical end without endMarks fails closed; must not silently use live marks
const histCash = { type:"CASHFLOW", id:"hc1", timestamp:"2026-09-01T09:00:00Z", amount:100000 };
const histBuy = { id:"hq1", timestamp:"2026-09-01T10:00:00Z", symbol:"QQQ", assetType:"EQUITY", side:"BUY", quantity:10, price:100, fees:0 };
const startAt = "2026-09-01T12:00:00Z";
const histEndAt = "2026-09-15T12:00:00Z";
const startMarks = { QQQ: 100 };
const liveToday = { QQQ: 999 };
const resolvedHist = L.resolvePeriodEndMarks(histEndAt, {}, liveToday, Date.parse("2026-10-07T00:00:00Z"));
ok(!resolvedHist.usedLiveEnd, "historical end does not use live marks");
ok(Object.keys(resolvedHist.endMarks).length === 0, "historical empty endMarks stays empty");
const histIncomplete = L.periodMetrics([histCash, histBuy], startAt, histEndAt, startMarks, resolvedHist.endMarks);
ok(!histIncomplete.complete && histIncomplete.pnl === null, "historical period without end marks is incomplete");

const resolvedLive = L.resolvePeriodEndMarks(
  new Date(Date.parse("2026-10-07T00:00:00Z")).toISOString(),
  {},
  liveToday,
  Date.parse("2026-10-07T00:00:30Z")
);
ok(resolvedLive.usedLiveEnd, "end≈now may use live marks");
near(resolvedLive.endMarks.QQQ, 999, 1e-12, "live end marks passthrough");

const explicitEnd = L.resolvePeriodEndMarks(histEndAt, { QQQ: 110 }, liveToday, Date.parse("2026-10-07T00:00:00Z"));
ok(!explicitEnd.usedLiveEnd, "explicit end marks preferred over live");
const histComplete = L.periodMetrics([histCash, histBuy], startAt, histEndAt, startMarks, explicitEnd.endMarks);
ok(histComplete.complete, "historical period with explicit end marks complete");
near(histComplete.pnl, 100, 1e-9, "historical period pnl uses end marks not live");

console.log("LEDGER GOLDEN TEST: PASS");
