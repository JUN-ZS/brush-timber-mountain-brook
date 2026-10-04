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
  restoreCancelledOrder,
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

function buyIntent(notional: number, id = "buy-intent") {
  return {
    id,
    side: "BUY" as const,
    notional,
    target: 0,
    signedGap: notional,
    cycleMonth: 1,
    source: "DEV_VITE_DYNAMIC_DEPLOYMENT_V1" as const,
    createdAt: "2026-10-04T00:00:00.000Z",
  };
}

function sellIntent(notional: number, id = "sell-intent") {
  return {
    id,
    side: "SELL" as const,
    notional,
    target: 0,
    signedGap: -notional,
    cycleMonth: 1,
    source: "DEV_VITE_DYNAMIC_DEPLOYMENT_V1" as const,
    createdAt: "2026-10-04T00:00:00.000Z",
  };
}

test("order amount comes only from the parent dynamic intent", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const parent = buyIntent(60_000, "dynamic-buy-60k");
  const synced = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    intent: parent,
  });
  const buy = activePaperOrders(synced).find((x) => x.side === "BUY");
  assert(buy);
  assert.equal(buy.parentIntentId, "dynamic-buy-60k");
  assert.equal(buy.parentIntentNotional, 60_000);
  assert.equal(buy.suggestedAmount, 30_000);
});

test("order machine v2 requires dynamic parent intent for order creation", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  assert.equal(state.schema, "qqq-order-machine.v2");
  const unchanged = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    intent: null,
  });
  assert.equal(activePaperOrders(unchanged).length, 0);
});


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
    intent: buyIntent(60_000),
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
    intent: buyIntent(60_000),
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
    intent: buyIntent(60_000),
  });
  assert.equal(activePaperOrders(next).filter((x) => x.side === "BUY")[0]?.rung, "MID");
});

test("unavailable current ladder rung advances to the next valid rung", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const full = ladder();
  const sparse = {
    ...full,
    add: full.add.filter((row) => !(row.horizon === 1 && row.touchProbability === 0.7)),
  };
  const synced = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: sparse,
    intent: buyIntent(60_000),
  });
  assert.equal(synced.nextBuyRung, 1);
  assert.equal(activePaperOrders(synced).find((x) => x.side === "BUY")?.rung, "MID");
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
    intent: sellIntent(20_000),
  });
  const sell = activePaperOrders(synced).find((x) => x.side === "SELL");
  assert(sell);
  const touched = syncOrderMachine({
    state: synced,
    now: "2026-10-04T01:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: sell.limitPrice,
    ladder: ladder(),
    intent: sellIntent(20_000),
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
    intent: buyIntent(60_000),
  });
  const oldBuy = activePaperOrders(day1).find((x) => x.side === "BUY");
  assert(oldBuy);
  const day2 = syncOrderMachine({
    state: day1,
    now: "2026-10-05T00:00:00.000Z",
    marketDate: "2026-10-05",
    currentPrice: 101,
    ladder: ladder(),
    intent: buyIntent(60_000),
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
    intent: buyIntent(60_000),
  });
  const oldBuy = activePaperOrders(day1).find((x) => x.side === "BUY");
  assert(oldBuy);
  const stale = syncOrderMachine({
    state: day1,
    now: "2026-10-05T00:00:00.000Z",
    marketDate: "2026-10-05",
    currentPrice: 101,
    ladder: ladder(),
    intent: buyIntent(60_000),
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
    intent: buyIntent(60_000),
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
    intent: buyIntent(60_000),
  });
  assert.equal(resumed.nextBuyRung, 1);
  assert.equal(activePaperOrders(resumed).find((x) => x.side === "BUY")?.rung, "MID");
});

test("cancelled rung can be restored when no later rung has filled", () => {
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
    intent: buyIntent(60_000),
  });
  const buy = activePaperOrders(synced).find((x) => x.side === "BUY");
  assert(buy);

  const cancelled = cancelPaperOrder(synced, buy.id, "2026-10-04T01:00:00.000Z");
  assert.equal(cancelled.orders.find((x) => x.id === buy.id)?.status, "CANCELLED");
  assert.equal(cancelled.nextBuyRung, 1);

  const restored = restoreCancelledOrder(cancelled, buy.id, "2026-10-04T02:00:00.000Z");
  assert.equal(restored.nextBuyRung, 0);
  assert.equal(restored.orders.find((x) => x.id === buy.id)?.status, "ARMED");

  const resynced = syncOrderMachine({
    state: restored,
    now: "2026-10-04T02:01:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    intent: buyIntent(60_000),
  });
  assert.equal(activePaperOrders(resynced).filter((x) => x.side === "BUY").length, 1);
  assert.equal(activePaperOrders(resynced).find((x) => x.side === "BUY")?.rung, "NEAR");
});

test("cancelled rung cannot be restored after a later rung has filled", () => {
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
    intent: buyIntent(60_000),
  });
  const buy = activePaperOrders(synced).find((x) => x.side === "BUY");
  assert(buy);
  const cancelled = cancelPaperOrder(synced, buy.id, "2026-10-04T01:00:00.000Z");
  const mid = syncOrderMachine({
    state: cancelled,
    now: "2026-10-04T02:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    intent: buyIntent(60_000),
  });
  const midOrder = activePaperOrders(mid).find((x) => x.side === "BUY");
  assert.equal(midOrder?.rung, "MID");
  const touched = syncOrderMachine({
    state: mid,
    now: "2026-10-04T03:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: midOrder!.limitPrice,
    ladder: ladder(),
    intent: buyIntent(60_000),
  });
  const filled = fillPaperOrder(touched, midOrder!.id, midOrder!.limitPrice, "2026-10-04T04:00:00.000Z");
  assert.equal(filled.nextBuyRung, 2);
  const restored = restoreCancelledOrder(filled, buy.id, "2026-10-04T05:00:00.000Z");
  assert.equal(restored.orders.find((x) => x.id === buy.id)?.status, "CANCELLED");
  assert.equal(restored.nextBuyRung, 2);
});


test("a changed opposite intent does not create a second side while an order is active", () => {
  const state = seedOrderMachine({
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    qqqPrice: 100,
    nav: 40_000,
    capital: 100_000,
    contributed: 40_000,
  });
  const buy = syncOrderMachine({
    state,
    now: "2026-10-04T00:00:00.000Z",
    marketDate: "2026-10-04",
    currentPrice: 100,
    ladder: ladder(),
    intent: buyIntent(60_000),
  });
  const sell = syncOrderMachine({
    state: buy,
    now: "2026-10-05T00:00:00.000Z",
    marketDate: "2026-10-05",
    currentPrice: 101,
    ladder: ladder(),
    intent: sellIntent(20_000),
  });
  assert.equal(activePaperOrders(sell).length, 1);
  assert.equal(activePaperOrders(sell)[0]?.side, "BUY");
});
