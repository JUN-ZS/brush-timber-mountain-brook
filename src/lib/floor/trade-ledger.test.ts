import test from "node:test";
import assert from "node:assert/strict";
import { activeTradeNotional, createTradeEntry } from "./trade-ledger.ts";

test("trade entries record notional, price, and derived shares", () => {
  const entry = createTradeEntry({
    side: "SELL",
    amount: 12_000,
    price: 750,
    cycleMonth: 7,
    recordedAt: "2026-10-04T00:00:00Z",
    note: "manual execution",
  });

  assert.equal(entry.side, "SELL");
  assert.equal(entry.amount, 12_000);
  assert.equal(entry.price, 750);
  assert.equal(entry.shares, 16);
  assert.equal(entry.source, "MANUAL");
  assert.equal(entry.voidedAt, null);
});

test("voided trades stay auditable but leave active trade totals", () => {
  const buy = createTradeEntry({
    side: "BUY",
    amount: 10_000,
    price: 500,
    cycleMonth: 1,
    recordedAt: "2026-10-04T00:00:00Z",
  });
  const sell = createTradeEntry({
    side: "SELL",
    amount: 3_000,
    price: 600,
    cycleMonth: 2,
    recordedAt: "2026-10-04T00:01:00Z",
  });
  const voidedSell = { ...sell, id: "voided-sell", voidedAt: "2026-10-04T00:02:00Z" };

  assert.equal(activeTradeNotional([buy], "BUY"), 10_000);
  assert.equal(activeTradeNotional([sell, voidedSell], "SELL"), 3_000);
});