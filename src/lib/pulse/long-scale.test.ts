import test from "node:test";
import assert from "node:assert/strict";
import { buildSyntheticLongScale } from "./long-scale.ts";

function series(startYear, months, base, monthlyGrowth = 0.01) {
  return Array.from({ length: months }, (_, i) => {
    const d = new Date(Date.UTC(startYear, i, 1));
    return {
      date: d.toISOString().slice(0, 10),
      value: base * Math.pow(1 + monthlyGrowth, i),
    };
  });
}

test("buildSyntheticLongScale preserves observed QQQ and creates historical/future layers", () => {
  const composite = series(1971, 660, 100, 0.004);
  const ndx = composite
    .filter((_, i) => i >= 180)
    .map((p) => ({ ...p, value: p.value * 1.7 }));
  const qqq = series(2004, 275, 30, 0.005);
  const profile = buildSyntheticLongScale(
    qqq,
    ndx,
    composite,
    "2026-11-01",
    50,
    10,
  );

  assert.ok(profile);
  assert.equal(profile.scaleYears, 50);
  assert.ok(profile.points.some((p) => p.provenance === "SYNTHETIC_HISTORY"));
  assert.ok(profile.points.some((p) => p.provenance === "OBSERVED_QQQ"));
  assert.equal(profile.future?.months.length, 121);
  assert.equal(profile.future?.months.at(-1), 120);

  const observedLast = profile.points.filter((p) => p.provenance === "OBSERVED_QQQ").at(-1);
  assert.equal(observedLast?.value, qqq.at(-1)?.value);
  assert.equal(profile.future?.median[0], 1);
});

test("future horizon can extend beyond the immediate 10Y simulation", () => {
  const composite = series(1971, 840, 100, 0.003);
  const ndx = composite
    .filter((_, i) => i >= 180)
    .map((p) => ({ ...p, value: p.value * 1.4 }));
  const qqq = series(2004, 275, 30, 0.005);
  const profile = buildSyntheticLongScale(
    qqq,
    ndx,
    composite,
    "2026-11-01",
    50,
    20,
  );
  assert.ok(profile);
  assert.equal(profile.future?.months.length, 241);
  assert.equal(profile.syntheticFutureMonths, 240);
});
