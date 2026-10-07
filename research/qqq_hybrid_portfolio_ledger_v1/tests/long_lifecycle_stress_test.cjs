const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const ctx = { window: {} };
vm.createContext(ctx);
for (const file of ["ledger_engine.js", "position_identity.js", "spread_pnl.js"]) {
  vm.runInContext(fs.readFileSync(path.join(root, file), "utf8"), ctx);
}
const L = ctx.window.PortfolioLedgerV1;
const I = ctx.window.PortfolioPositionIdentityV1;
const S = ctx.window.PortfolioSpreadPnlV1;

const events = [];
const baseMs = Date.parse("2026-01-01T00:00:00Z");
let seq = 0;
function add(symbol, side, price, legRole, timestampMs, fees = 1) {
  seq += 1;
  events.push({
    id: "STRESS-" + String(seq).padStart(6, "0"),
    timestamp: new Date(timestampMs).toISOString(),
    symbol,
    assetType: "OPTION",
    side,
    quantity: 1,
    price,
    fees,
    positionIdentity: {
      campaignId: "STRESS-C1",
      spreadId: "STRESS-S1",
      legRole,
      strategyRole: "QQQ_CALL_CREDIT_SPREAD"
    }
  });
}

add("LONG-0000", "BUY", 2, "LONG", baseMs);
add("SHORT-0000", "SELL", 8, "SHORT", baseMs + 1);

const ROLLS = 2500;
for (let i = 1; i <= ROLLS; i++) {
  const t = baseMs + i * 100000;
  const old = String(i - 1).padStart(4, "0");
  const next = String(i).padStart(4, "0");

  // Roll opens the next pair first (temporary MULTI_CONTRACT), then closes the old pair.
  add("LONG-" + next, "BUY", 2 + i, "LONG", t);
  add("SHORT-" + next, "SELL", 8 + i, "SHORT", t + 1);
  add("LONG-" + old, "SELL", 3 + (i - 1), "LONG", t + 2);
  add("SHORT-" + old, "BUY", 7 + (i - 1), "SHORT", t + 3);
}

const marks = {
  ["LONG-" + String(ROLLS).padStart(4, "0")]: 2 + ROLLS,
  ["SHORT-" + String(ROLLS).padStart(4, "0")]: 8 + ROLLS
};
const result = S.attribute(events, marks);
if (result.summary.paired !== 1 || result.rows[0].status !== "PAIRED") {
  throw new Error("long lifecycle did not finish PAIRED");
}
const row = result.rows[0];
const expectedRealized = ROLLS * 200;
const expectedFees = events.length;
const expectedTotal = expectedRealized - expectedFees;
if (Math.abs(row.realizedPnl - expectedRealized) > 1e-9) {
  throw new Error("realized drift: expected " + expectedRealized + ", got " + row.realizedPnl);
}
if (Math.abs(row.fees - expectedFees) > 1e-9) {
  throw new Error("fee drift: expected " + expectedFees + ", got " + row.fees);
}
if (Math.abs(row.unrealizedPnl) > 1e-9 || Math.abs(row.totalPnl - expectedTotal) > 1e-9) {
  throw new Error("final P&L mismatch: expected " + expectedTotal + ", got " + row.totalPnl);
}

// Reordered import must be exactly equivalent after deterministic sortEvents().
const shuffled = events.slice().sort((a, b) => {
  const ha = (a.id.charCodeAt(7) * 31 + a.id.length * 17) % 997;
  const hb = (b.id.charCodeAt(7) * 31 + b.id.length * 17) % 997;
  return hb - ha || b.id.localeCompare(a.id);
});
const shuffledRow = S.attribute(shuffled, marks).rows[0];
if (JSON.stringify({
  status: shuffledRow.status,
  realizedPnl: shuffledRow.realizedPnl,
  unrealizedPnl: shuffledRow.unrealizedPnl,
  fees: shuffledRow.fees,
  totalPnl: shuffledRow.totalPnl,
  units: shuffledRow.units
}) !== JSON.stringify({
  status: row.status,
  realizedPnl: row.realizedPnl,
  unrealizedPnl: row.unrealizedPnl,
  fees: row.fees,
  totalPnl: row.totalPnl,
  units: row.units
})) {
  throw new Error("unordered import changed lifecycle attribution");
}

// Stress FIFO with many independent lots.
const FIFO_LOTS = 10000;
const fifoEvents = [];
for (let i = 0; i < FIFO_LOTS; i++) {
  fifoEvents.push({
    id: "FIFO-B-" + String(i).padStart(5, "0"),
    timestamp: new Date(baseMs + i * 10).toISOString(),
    symbol: "FIFO-QQQ",
    assetType: "EQUITY",
    side: "BUY",
    quantity: 1,
    price: 100 + (i % 17)
  });
}
for (let i = 0; i < FIFO_LOTS; i++) {
  fifoEvents.push({
    id: "FIFO-S-" + String(i).padStart(5, "0"),
    timestamp: new Date(baseMs + 200000 + i * 10).toISOString(),
    symbol: "FIFO-QQQ",
    assetType: "EQUITY",
    side: "SELL",
    quantity: 1,
    price: 110
  });
}
const fifo = L.snapshot(fifoEvents, {});
const fifoPos = fifo.positions.length ? fifo.positions[0] : null;
const expectedFifoRealized = fifoEvents.slice(0, FIFO_LOTS)
  .reduce((sum, e) => sum + (110 - e.price), 0);
if (!fifoPos || fifoPos.quantity !== 0 || Math.abs(fifo.realizedPnl - expectedFifoRealized) > 1e-9) {
  throw new Error("FIFO stress mismatch");
}

console.log("LONG LIFECYCLE STRESS: PASS");
console.log("ROLLS=" + ROLLS + " EVENTS=" + events.length + " EXPECTED_TOTAL_PNL=" + expectedTotal);
console.log("FIFO_LOTS=" + FIFO_LOTS + " REALIZED=" + expectedFifoRealized);
