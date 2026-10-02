import test from "node:test";
import assert from "node:assert/strict";
import { median, couple } from "./rolling-floor.ts";

test("median", () => assert.equal(median([0.1, 0.2, 0.25, 0.9]), 0.225));

test("coupling reduces authority when 20/30/50Y scales disagree", () => {
  const mk = (s: 20 | 30 | 50, t: number) => ({
    channel: "S",
    layer: "OBSERVED" as const,
    scaleYears: s,
    asof: "2026-01-01",
    target: t,
    q05: 1,
    pNonLoss: 0.5,
    mean: 1.1,
    nAnalogs: 20,
    effectiveN: 5,
    status: "OK" as const,
  });
  const c = couple("2026-01-01", 60, [
    mk(20, 0.05),
    mk(30, 0.95),
    mk(50, 0.05),
  ]);
  assert.equal(c.clockTarget, 0.5);
  assert.ok(c.agreement >= 0 && c.agreement < 1);
  assert.ok(c.coupledTarget >= 0 && c.coupledTarget <= 1);
});

test("single available scale has no authority", () => {
  const c = couple("2026-01-01", 60, [{
    channel: "S",
    layer: "OBSERVED" as const,
    scaleYears: 20,
    asof: "2026-01-01",
    target: 0.95,
    q05: 1,
    pNonLoss: 0.5,
    mean: 1.1,
    nAnalogs: 20,
    effectiveN: 5,
    status: "OK" as const,
  }]);
  assert.equal(c.agreement, 0);
  assert.equal(c.coupledTarget, c.clockTarget);
});
