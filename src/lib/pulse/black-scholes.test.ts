import assert from "node:assert/strict";
import test from "node:test";
import { bsPrice, bsGreeks, strikeForDelta } from "./black-scholes.ts";

test("ATM call is positive and put-call parity-ish", () => {
  const call = bsPrice({ spot: 100, strike: 100, tYears: 30 / 365, iv: 0.25, right: "CALL" });
  const put = bsPrice({ spot: 100, strike: 100, tYears: 30 / 365, iv: 0.25, right: "PUT" });
  assert.ok(call > 0 && put > 0);
  assert.ok(Math.abs(call - put) < 1.5);
});

test("delta of ATM call near 0.5", () => {
  const g = bsGreeks({ spot: 100, strike: 100, tYears: 30 / 365, iv: 0.2, right: "CALL" });
  assert.ok(g.delta > 0.45 && g.delta < 0.6);
});

test("OTM strike for 16-delta is above spot", () => {
  const k = strikeForDelta({ spot: 100, tYears: 30 / 365, iv: 0.25, targetAbsDelta: 0.16, right: "CALL" });
  assert.ok(k > 100);
});
