import assert from "node:assert/strict";
import test from "node:test";
import { assignSplit } from "./splits.ts";
import { calendarIndexOf, lastBar, universe } from "./bars.ts";
import { cardAt, ranking, levelOf, causalOk, thresholdProbe, similarFwd } from "./relvol.ts";
import { compete, capacityPlan, ironFlyPnl, shortRatioOf } from "./structures.ts";

test("split: 2023+ is UNPROVEN_OOS not frozen", () => {
  assert.equal(assignSplit("2024-06-01"), "UNPROVEN_OOS");
  assert.equal(assignSplit("2012-01-01"), "TRAIN");
});

test("relative vol levels", () => {
  assert.equal(levelOf(0.7), "NORMAL_LOW");
  assert.equal(levelOf(1.1), "ELEVATED");
  assert.equal(levelOf(1.8), "EXTREME");
  assert.equal(levelOf(2.4), "SUPER_EXTREME");
  assert.equal(levelOf(null), "UNKNOWN");
});

test("universe is daily, not monthly", () => {
  assert.ok(universe.dates.length > 4000);
  assert.equal(universe.dates[0] < "2005-01-01", true);
  assert.ok(universe.n.NVDA > 4000);
  assert.ok(universe.n.HOOD > 800);
});

test("card is causal: uses own history only", () => {
  const q = cardAt("QQQ", lastBar);
  assert.ok(q);
  assert.equal(q.symbol, "QQQ");
  assert.ok(q.week.percentile == null || (q.week.percentile >= 0 && q.week.percentile <= 1));
  assert.ok(q.day.durationAboveMean >= 0);
  assert.equal(q.split, "UNPROVEN_OOS");
  assert.ok(causalOk("QQQ", calendarIndexOf("2015-06-15")));
});

test("first rolling window stays unknown until enough history", () => {
  const early = cardAt("QQQ", 30);
  assert.equal(early, null);
});

test("percentile does not use future bars", () => {
  const a = cardAt("QQQ", calendarIndexOf("2016-06-01"));
  const b = cardAt("QQQ", lastBar);
  assert.ok(a && b);
  assert.notEqual(a.week.mean, b.week.mean);
});

test("2020 crash week is elevated versus QQQ own history", () => {
  const c = cardAt("QQQ", calendarIndexOf("2020-03-16"));
  assert.ok(c);
  assert.ok((c.week.percentile ?? 0) >= 0.8 || c.week.level === "HIGH" || c.week.level === "EXTREME" || c.week.level === "SUPER_EXTREME");
});

test("ranking keeps three raw dimensions and many names", () => {
  const rows = ranking(lastBar);
  assert.ok(rows.length >= 16);
  for (const r of rows) {
    assert.ok("day" in r && "week" in r && "month" in r);
  }
  assert.ok(rows.some((r) => r.symbol === "NVDA"));
  assert.ok(rows.some((r) => r.symbol === "PLTR"));
});

test("hot names with short history get thin or HOT cohort", () => {
  const h = cardAt("HOOD", lastBar);
  assert.ok(h);
  assert.ok(h.cohort === "HOT" || h.confidence === "thin" || h.nBars < 2000);
});

test("missing bars on VXX do not crash", () => {
  const c = cardAt("VXX", lastBar);
  assert.ok(c === null || c.symbol === "VXX");
});

test("consecutive duration is non-negative and timeline has slope info", () => {
  const q = cardAt("NVDA", lastBar);
  assert.ok(q);
  assert.ok(q.week.durationAboveMean >= 0);
  assert.ok(q.weekTimeline.length >= 4);
  assert.ok(["RISING", "FALLING", "FLAT", "UNKNOWN"].includes(q.volMomentum));
});

test("threshold probe competes instead of freezing 1.25", () => {
  const rows = thresholdProbe("QQQ", lastBar);
  assert.ok(rows.length >= 8);
  assert.ok(rows.some((r) => r.thr === 1.25));
});
