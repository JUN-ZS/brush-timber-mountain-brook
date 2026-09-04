import assert from "node:assert/strict";
import test from "node:test";
import { lastBar } from "./bars.ts";
import { cardAt } from "./relvol.ts";
import { compete, capacityPlan, ironFlyPnl, shortRatioOf } from "./structures.ts";

test("iron fly payoff: inside short, between, past wing", () => {
  assert.ok(Math.abs(ironFlyPnl(0.005, 0.02, 0.05, 0.007) - 0.007) < 1e-9);
  const mid = ironFlyPnl(0.03, 0.02, 0.05, 0.007);
  assert.ok(mid < 0.007 && mid > -0.03);
  const wing = ironFlyPnl(0.2, 0.02, 0.05, 0.007);
  assert.ok(Math.abs(wing - (0.007 - 0.03)) < 1e-9);
});

test("structures compete and may pick NO_TRADE", () => {
  const q = cardAt("QQQ", lastBar);
  assert.ok(q);
  const dep = compete(q, lastBar);
  assert.ok(dep.some((d) => d.id === "NO_TRADE"));
  assert.ok(dep.every((d) => d.tag === "HYPOTHETICAL"));
  assert.ok(dep.every((d) => d.chain === "OPTIONS_MISSING"));
  assert.ok(dep.some((d) => d.id === "IRON_FLY"));
  assert.ok(dep.some((d) => d.id === "BROKEN_WING"));
  assert.ok(dep.some((d) => d.id === "CALL_RATIO"));
  assert.ok(dep.some((d) => d.id === "COVERED_CALL"));
  assert.ok(dep.some((d) => d.id === "BUY_UNDERLYING"));
});

test("short ratio is state-dependent not frozen at 5", () => {
  const q = cardAt("QQQ", lastBar);
  assert.ok(q);
  const n = shortRatioOf(q);
  assert.ok(n >= 2 && n <= 5);
});

test("breach budget has ES and consecutive cluster", () => {
  const q = cardAt("NVDA", lastBar);
  assert.ok(q);
  const dep = compete(q, lastBar);
  const fly = dep.find((d) => d.id === "IRON_FLY");
  assert.ok(fly);
  assert.ok(fly.breach.n >= 0);
  assert.ok(fly.breach.consecutive3 >= 0);
  assert.ok(fly.breach.es95 <= 0 || fly.breach.n === 0);
});

test("capacity shrinks when consecutive budget is tight", () => {
  const q = cardAt("QQQ", lastBar);
  assert.ok(q);
  const dep = compete(q, lastBar).find((d) => d.id !== "NO_TRADE");
  assert.ok(dep);
  const wide = capacityPlan(dep, q.spot, { maxConsec: 8, maxDd: 50_000 });
  const tight = capacityPlan(dep, q.spot, { maxConsec: 1, maxDd: 200 });
  assert.ok(tight.lots <= wide.lots);
});

test("NO_TRADE capacity is rejected", () => {
  const q = cardAt("QQQ", lastBar);
  assert.ok(q);
  const none = compete(q, lastBar).find((d) => d.id === "NO_TRADE");
  assert.ok(none);
  const plan = capacityPlan(none, q.spot, { maxConsec: 3, maxDd: 2000 });
  assert.equal(plan.rejected, true);
  assert.equal(plan.lots, 0);
});
