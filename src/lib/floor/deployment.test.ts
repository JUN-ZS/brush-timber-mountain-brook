import test from "node:test";
import assert from "node:assert/strict";
import { clockTarget, fundingDelta } from "./account.ts";
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
    recordedAt: "2026-01-01T00:00:00.000Z", marketDate: "2026-01-01", cycleMonth: 1,
    capital: 100_000, frontload: 0.2, nav: 20_000, contributed: 0, startingDeployed: 20_000,
    qqqPrice: 100, marketState: "REGULAR",
    dayRatio: 1, weekRatio: 1, monthRatio: 1, dayLevel: "NORMAL", weekLevel: "NORMAL", monthLevel: "NORMAL",
  });
  const target40 = dailyDeploymentRecord({
    recordedAt: "2026-01-01T00:00:00.000Z", marketDate: "2026-01-01", cycleMonth: 1,
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

  const ledger = [{
    id: "funding-1", recordedAt: "2026-01-01T00:00:00.000Z", cycleMonth: 1,
    kind: "CONTRIBUTION" as const, amount: 5_000,
  }];
  const funding20 = fundingDelta(100_000, 1, ledger);
  const funding40 = fundingDelta(100_000, 1, ledger);
  assert.equal(funding20, funding40);
  assert.equal(funding20, 5_000 - clockTarget(100_000, 1));
});

test("every frontload grid point maps to the same day-progress formula", () => {
  const capital = 100_000;
  const marketDate = "2026-10-02";
  const cycleMonth = 1;
  const progress = dailyProgress(cycleMonth, marketDate);

  let previousTarget = -1;
  for (const frontload of FRONTLOAD_GRID) {
    const row = dailyDeploymentRecord({
      recordedAt: "2026-10-02T00:00:00.000Z",
      marketDate,
      cycleMonth,
      capital,
      frontload,
      nav: 0,
      contributed: 0,
      startingDeployed: 0,
      qqqPrice: 749.58,
      marketState: "REGULAR",
      dayRatio: null,
      weekRatio: null,
      monthRatio: null,
      dayLevel: "ELEVATED",
      weekLevel: "NORMAL_LOW",
      monthLevel: "HIGH",
    });
    const expectedTarget = capital * (frontload + (1 - frontload) * progress);
    assert(Math.abs(row.target - expectedTarget) < 1e-9);
    assert.equal(row.contributed, 0);
    assert.equal(row.buyAvailable, row.target);
    assert(row.target >= previousTarget);
    previousTarget = row.target;
  }

  const f20 = dailyDeploymentRecord({
    recordedAt: "2026-10-02T00:00:00.000Z",
    marketDate,
    cycleMonth,
    capital,
    frontload: 0.2,
    nav: 0,
    contributed: 0,
    startingDeployed: 0,
    qqqPrice: 749.58,
    marketState: "REGULAR",
    dayRatio: null,
    weekRatio: null,
    monthRatio: null,
    dayLevel: "ELEVATED",
    weekLevel: "NORMAL_LOW",
    monthLevel: "HIGH",
  });
  const f40 = { ...f20, frontload: 0.4 };
  const expected20 = capital * (0.2 + 0.8 * progress);
  const expected40 = capital * (0.4 + 0.6 * progress);
  assert(Math.abs(f20.target - expected20) < 1e-9);
  assert(Math.abs(frontLoadedTarget(capital, f40.frontload, cycleMonth, marketDate) - expected40) < 1e-9);
  assert(Math.abs(f40.frontload - 0.4) < 1e-12);
});


test("daily deployment observation CANCEL keeps history and RESTORE restores it", () => {
  const first = {
    id: "obs-40",
    marketDate: "2026-10-02",
    frontload: 0.4,
    target: 40_016.67,
    nav: 0,
    buyAvailable: 40_016.67,
    sellExcess: 0,
    voidedAt: null as string | null,
  };
  const second = {
    ...first,
    id: "obs-20",
    frontload: 0.2,
    target: 20_022.22,
    buyAvailable: 20_022.22,
  };

  const entries = [first, second];
  const cancelled = toggleDailyDeploymentObservation(entries, "obs-40", "2026-10-05T00:00:00Z");
  assert.equal(cancelled.length, 2);
  assert.equal(cancelled.find((x) => x.id === "obs-40")?.voidedAt, "2026-10-05T00:00:00Z");
  assert.equal(cancelled.find((x) => x.id === "obs-20")?.voidedAt, null);

  const restored = toggleDailyDeploymentObservation(cancelled, "obs-40", "2026-10-05T00:01:00Z");
  assert.equal(restored.length, 2);
  assert.equal(restored.find((x) => x.id === "obs-40")?.voidedAt, null);
});

test("daily deployment RESTORE refuses duplicate active DATE + F", () => {
  const entries = [
    {
      id: "obs-old",
      marketDate: "2026-10-02",
      frontload: 0.4,
      voidedAt: "2026-10-05T00:00:00Z" as string | null,
    },
    {
      id: "obs-new",
      marketDate: "2026-10-02",
      frontload: 0.4,
      voidedAt: null as string | null,
    },
  ];
  const restored = toggleDailyDeploymentObservation(entries, "obs-old", "2026-10-05T00:01:00Z");
  assert.equal(restored, entries);
  assert.equal(restored.find((x) => x.id === "obs-old")?.voidedAt, "2026-10-05T00:00:00Z");
});
