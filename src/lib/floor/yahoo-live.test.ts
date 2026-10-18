import test from "node:test";
import assert from "node:assert/strict";
import { buildConditionalPriceLadder, type PricePathSample } from "./yahoo-live.ts";

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

test("conditional ladder projects normalized historical extremes onto current QQQ", () => {
  const samples = [
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
  ];
  const ladder = buildConditionalPriceLadder(200, samples);
  assert.equal(ladder.samples, 12);
  assert.equal(ladder.quality, "DESCRIPTIVE");

  const add5d70 = ladder.add.find((x) => x.horizon === 5 && x.touchProbability === 0.7);
  const reduce5d50 = ladder.reduce.find((x) => x.horizon === 5 && x.touchProbability === 0.5);
  assert(add5d70?.price != null && add5d70.price < 200);
  assert(reduce5d50?.price != null && reduce5d50.price > 200);
  assert.equal(add5d70?.side, "ADD");
  assert.equal(reduce5d50?.side, "REDUCE");
});

test("thin samples are marked but remain visible as descriptive levels", () => {
  const ladder = buildConditionalPriceLadder(200, [
    sample(100, 0.05, 0.04),
    { ...sample(100, 0.05, 0.04), entryPrice: 0 },
  ]);
  assert.equal(ladder.samples, 1);
  assert.equal(ladder.quality, "THIN");
  const add5d = ladder.add.find((x) => x.horizon === 5 && x.touchProbability === 0.5);
  const reduce5d = ladder.reduce.find((x) => x.horizon === 5 && x.touchProbability === 0.5);
  assert(add5d?.price != null && add5d.price < 200);
  assert(reduce5d?.price != null && reduce5d.price > 200);
});
