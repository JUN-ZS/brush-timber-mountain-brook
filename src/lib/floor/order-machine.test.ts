import test from "node:test";
import assert from "node:assert/strict";
import { buildConditionalPriceLadder, type PricePathSample } from "./yahoo-live.ts";
import {
  activePaperOrders,
  cancelPaperOrder,
  canFillOrder,
  fillPaperOrder,
  nextRungLabel,
  paperEconomicWealth,
  repricePaperOrder,
  seedOrderMachine,
  syncOrderMachine,
} from "./order-machine.ts";

function sample(entryPrice: number, low: number, high: number): PricePathSample {
  return {
    entryPrice,
    low1: entryPrice * (1 - low),
    low5: entryPrice * (1 - low * 1.4),
    low21: entryPrice * (1 - low * 2),
    high1: entryPrice * (1 + high),
    high5: entryPrice * (1 + high * 1.4),
    high21: entryPrice * (1 + high * 2),
  };
}

function ladder() {
  return buildConditionalPriceLadder(100, [
    sample(100, 0.05, 0.04),
    sample(110, 0.06, 0.05),
    sample(90, 0.07, 0.06),
    sample(120, 0.08, 0.07),
    sample(130, 0.09, 0.08),
    sample(80, 0.10, 0.09),
    sample(140, 0.06, 0.05),
    sample(150, 0.07, 0.06),
    sample(160, 0.08, 0.07),
    sample(170, 0.09, 0.08),
    sample(180, 0.10, 0.09),
    sample(190, 0.05, 0.04),
  ]);
}

function money(value: number) {
  return Math.round(value * 100) / 100;
}

test("order machine arms one next BUY and advances after fill", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const synced = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    target: 60_000,
  });
  const buys = activePaperOrders(synced).filter((x) => x.side === "BUY");
  assert.equal(buys.length, 1);
  assert.equal(buys[0]?.rung, "NEAR");

  const touched = syncOrderMachine({
    state: synced,
    now: "2026-10-05T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: buys[0]!.limitPrice,
    ladder: ladder(),
    target: 60_000,
  });
  const touchedOrder = touched.orders.find((x) => x.id === buys[0]!.id);
  assert.equal(touchedOrder?.status, "TOUCHED");
  assert.equal(canFillOrder(touched, buys[0]!.id, buys[0]!.limitPrice), true);
  assert.equal(canFillOrder(touched, buys[0]!.id, buys[0]!.limitPrice + 3), true);

  const filled = fillPaperOrder(touched, buys[0]!.id, buys[0]!.limitPrice, "2026-10-04T01:00:00.000Z");
  assert.equal(filled.nextBuyRung, 1);
  assert.equal(filled.harvestReserve, 0);
  assert(filled.deploymentReserve < synced.deploymentReserve);
  assert.equal(paperEconomicWealth(filled), paperEconomicWealth(touched));
  assert.equal(nextRungLabel("BUY", filled.nextBuyRung), "BUY MID");

  const next = syncOrderMachine({
    state: filled,
    now: "2026-10-04T02:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: buys[0]!.limitPrice,
    ladder: ladder(),
    target: 60_000,
  });
  assert.equal(activePaperOrders(next).filter((x) => x.side === "BUY")[0]?.rung, "MID");
});

test("SELL fill moves proceeds into harvest reserve and next SELL rises", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 100_000,
    capital: 100_000,
    contributed: 100_000,
  });
  const synced = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    target: 80_000,
  });
  const sell = activePaperOrders(synced).find((x) => x.side === "SELL");
  assert(sell);
  const touched = syncOrderMachine({
    state: synced,
    now: "2026-10-04T01:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: sell.limitPrice,
    ladder: ladder(),
    target: 80_000,
  });
  const filled = fillPaperOrder(touched, sell.id, sell.limitPrice, "2026-10-04T02:00:00.000Z");
  assert(filled.harvestReserve > 0);
  assert(filled.positionNav < synced.positionNav);
  assert.equal(filled.nextSellRung, 1);
  assert.equal(money(paperEconomicWealth(filled)), money(paperEconomicWealth(touched)));
});

test("a new market session marks open orders STALE without cancelling them", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const day1 = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    target: 60_000,
  });
  const oldBuy = activePaperOrders(day1).find((x) => x.side === "BUY");
  assert(oldBuy);
  const day2 = syncOrderMachine({
    state: day1,
    now: "2026-10-05T00:00:00.000Z",
    marketDate: "2026-10-05",
    currentPrice: 101,
    ladder: ladder(),
    target: 60_000,
  });
  assert.equal(day2.orders.find((x) => x.id === oldBuy.id)?.status, "STALE");
  assert.equal(day2.nextBuyRung, 0);
  assert.equal(activePaperOrders(day2).find((x) => x.side === "BUY")?.id, oldBuy.id);
});

test("repricing preserves the same rung index and supersedes the old ticket", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const day1 = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    target: 60_000,
  });
  const oldBuy = activePaperOrders(day1).find((x) => x.side === "BUY");
  assert(oldBuy);
  const stale = syncOrderMachine({
    state: day1,
    now: "2026-10-05T00:00:00.000Z",
    marketDate: "2026-10-05",
    currentPrice: 101,
    ladder: ladder(),
    target: 60_000,
  });
  const repriced = repricePaperOrder(stale, oldBuy.id, "2026-10-05T01:00:00.000Z", "2026-10-05", ladder(), 60_000);
  assert.equal(repriced.nextBuyRung, 0);
  assert.equal(repriced.orders.find((x) => x.id === oldBuy.id)?.status, "REPLACED");
  assert.equal(activePaperOrders(repriced).find((x) => x.side === "BUY")?.rung, "NEAR");
});

test("cancellation skips the rung instead of silently re-arming it", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const synced = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    target: 60_000,
  });
  const buy = activePaperOrders(synced).find((x) => x.side === "BUY");
  assert(buy);
  const cancelled = cancelPaperOrder(synced, buy.id, "2026-10-04T01:00:00.000Z");
  assert.equal(cancelled.orders.find((x) => x.id === buy.id)?.status, "CANCELLED");
  assert.equal(cancelled.nextBuyRung, 1);
  assert.equal(activePaperOrders(cancelled).filter((x) => x.side === "BUY").length, 0);
  assert.equal(nextRungLabel("BUY", cancelled.nextBuyRung), "BUY MID");

  const resumed = syncOrderMachine({
    state: cancelled,
    now: "2026-10-04T02:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    target: 60_000,
  });
  assert.equal(resumed.nextBuyRung, 1);
  assert.equal(activePaperOrders(resumed).find((x) => x.side === "BUY")?.rung, "MID");
});
