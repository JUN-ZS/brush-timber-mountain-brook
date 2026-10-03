import test from "node:test";
import assert from "node:assert/strict";
import { FRONTLOAD_GRID, dailyDeploymentRecord, dailyProgress, deploymentGap, frontLoadedFraction } from "./deployment.ts";

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
