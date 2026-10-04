import test from "node:test";
import assert from "node:assert/strict";
import { FRONTLOAD_GRID, dailyDeploymentRecord, dailyProgress, deploymentGap, dynamicTradeIntent, frontLoadedFraction } from "./deployment.ts";

test("frontload endpoints are fixed", () => {
  assert.equal(frontLoadedFraction(0, 0), 0);
  assert.equal(frontLoadedFraction(1, 0), 1);
  assert.equal(frontLoadedFraction(0, 1), 1);
  assert.equal(frontLoadedFraction(0.4, 1), 1);
  assert.deepEqual(FRONTLOAD_GRID, [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]);
});

test("daily progress stays inside the horizon", () => {
  assert.equal(dailyProgress(1, "2026-01-01"), 0);
  assert(dailyProgress(60, "2026-06-15") > 0);
  assert.equal(dailyProgress(120, "2035-12-31"), 1);
});

test("deployment gap is capped by remaining budget", () => {
  assert.deepEqual(deploymentGap(400, 1500, 500), { buyAvailable: 500, sellExcess: 0, signedGap: 1100, status: "BUY_AVAILABLE" });
  assert.deepEqual(deploymentGap(1800, 1500, 500), { buyAvailable: 0, sellExcess: 300, signedGap: -300, status: "SELL_EXCESS" });
});

test("record carries daily market context", () => {
  const row = dailyDeploymentRecord({
    recordedAt: "2026-10-04T00:00:00.000Z", marketDate: "2026-10-04", cycleMonth: 2,
    capital: 100000, frontload: 0.4, nav: 30000, contributed: 25000, qqqPrice: 600, marketState: "REGULAR",
    dayRatio: 1.1, weekRatio: 1.3, monthRatio: 0.9, dayLevel: "ELEVATED", weekLevel: "HIGH", monthLevel: "NORMAL"
  });
  assert.equal(row.source, "YAHOO_FINANCE_CHART");
  assert.equal(row.status, "BUY_AVAILABLE");
  assert.equal(row.buyAvailable, Math.min(75000, row.target - 30000));
});


test("dynamic trade intent exposes the existing deployment gap without inventing a side", () => {
  const buy = dynamicTradeIntent({
    id: "dev-vite-2026-10-04-m3",
    now: "2026-10-04T00:00:00Z",
    cycleMonth: 3,
    nav: 30_000,
    target: 50_000,
    remainingCapital: 80_000,
  });
  assert.equal(buy?.side, "BUY");
  assert.equal(buy?.notional, 20_000);
  assert.equal(buy?.signedGap, 20_000);

  const sell = dynamicTradeIntent({
    id: "dev-vite-2026-10-05-m3",
    now: "2026-10-05T00:00:00Z",
    cycleMonth: 3,
    nav: 70_000,
    target: 50_000,
    remainingCapital: 80_000,
  });
  assert.equal(sell?.side, "SELL");
  assert.equal(sell?.notional, 20_000);
  assert.equal(sell?.signedGap, -20_000);

  const none = dynamicTradeIntent({
    id: "dev-vite-2026-10-06-m3",
    now: "2026-10-06T00:00:00Z",
    cycleMonth: 3,
    nav: 50_000,
    target: 50_000,
    remainingCapital: 50_000,
  });
  assert.equal(none, null);
});

test("frontload changes deployment target, never funding accounting", () => {
  const target20 = dailyDeploymentRecord({
    recordedAt: "2026-10-04T00:00:00.000Z", marketDate: "2026-10-04", cycleMonth: 1,
    capital: 100_000, frontload: 0.2, nav: 20_000, contributed: 0, startingDeployed: 20_000,
    qqqPrice: 100, marketState: "REGULAR",
    dayRatio: 1, weekRatio: 1, monthRatio: 1, dayLevel: "NORMAL", weekLevel: "NORMAL", monthLevel: "NORMAL",
  });
  const target40 = dailyDeploymentRecord({
    recordedAt: "2026-10-04T00:00:00.000Z", marketDate: "2026-10-04", cycleMonth: 1,
    capital: 100_000, frontload: 0.4, nav: 20_000, contributed: 0, startingDeployed: 20_000,
    qqqPrice: 100, marketState: "REGULAR",
    dayRatio: 1, weekRatio: 1, monthRatio: 1, dayLevel: "NORMAL", weekLevel: "NORMAL", monthLevel: "NORMAL",
  });

  assert.equal(target20.target, 20_000);
  assert.equal(target20.buyAvailable, 0);
  assert.equal(target20.contributed, 0);
  assert.equal(target20.remainingCapital, 80_000);

  assert.equal(target40.target, 40_000);
  assert.equal(target40.buyAvailable, 20_000);
  assert.equal(target40.contributed, 0);
  assert.equal(target40.remainingCapital, 80_000);
});
