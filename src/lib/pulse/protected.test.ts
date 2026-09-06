import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_PROTECTED, assertPutCushionsDownDay, firstWaveGrid, runProtected } from "./protected.ts";
import { buyHoldQQQ, sampleWindow } from "./backtest.ts";

test("first-wave grid is finite and PROTECTED-only", () => {
  const g = firstWaveGrid();
  assert.equal(g.length, 3 * 3 * 2 * 2 * 3 * 3 * 2);
  assert.ok(g.length <= 700);
});

test("zero put overlay tracks QQQ 100% (Observed path)", () => {
  const w = sampleWindow();
  const zero = runProtected(
    {
      ...DEFAULT_PROTECTED,
      calmPut: 0,
      unstablePut: 0,
      tailPut: 0,
      recoveryPut: 0,
      buildingPut: 0,
    },
    w.start,
    w.trainEnd,
    false,
  );
  const hold = buyHoldQQQ();
  assert.ok(Math.abs(zero.split.train.cagr - hold.split.train.cagr) < 0.002);
  assert.ok(Math.abs(zero.split.train.maxDd - hold.split.train.maxDd) < 0.01);
});

test("put overlay cushions a historical -8% QQQ day", () => {
  const g = assertPutCushionsDownDay();
  assert.equal(g.ok, true);
  assert.ok(g.overlay > g.qqq);
});
