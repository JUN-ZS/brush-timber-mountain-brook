import test from "node:test";
import assert from "node:assert/strict";
import { median, couple, deploymentResponseProfile, divergenceState, floorProfile, requiredFrontLoadFraction, buildRiskBaselineProfile, summarizeStatePath, type ReplayResult } from "./rolling-floor.ts";

test("median", () => assert.equal(median([0.1, 0.2, 0.25, 0.9]), 0.225));

test("scale divergence becomes an explicit fourth state", () => {
  assert.equal(divergenceState(3, 0.95), "CONVERGENT");
  assert.equal(divergenceState(3, 0.65), "TENSION");
  assert.equal(divergenceState(3, 0.20), "DIVERGENT");
  assert.equal(divergenceState(1, 0.95), "THIN");
});

test("divergence removes forward-pull authority instead of disabling the clock", () => {
  const mk = (s: 20 | 30 | 50, t: number) => ({
    channel: "S",
    layer: "OBSERVED" as const,
    scaleYears: s,
    asof: "2026-01-01",
    target: t,
    floorProfile: null,
    responseProfile: null,
    riskBaselineProfile: null,
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
  assert.equal(c.divergenceState, "DIVERGENT");
  assert.equal(c.agreement, 0);
  assert.equal(c.coupledTarget, c.clockTarget);
});

test("single available scale is THIN, not evidence of convergence", () => {
  const c = couple("2026-01-01", 60, [{
    channel: "S",
    layer: "OBSERVED" as const,
    scaleYears: 20,
    asof: "2026-01-01",
    target: 0.95,
    floorProfile: null,
    responseProfile: null,
    riskBaselineProfile: null,
    q05: 1,
    pNonLoss: 0.5,
    mean: 1.1,
    nAnalogs: 20,
    effectiveN: 5,
    status: "OK" as const,
  }]);
  assert.equal(c.divergenceState, "THIN");
  assert.equal(c.agreement, 0);
  assert.equal(c.coupledTarget, c.clockTarget);
});


test("state-conditioned path summary observes displacement from the clock", () => {
  const result: ReplayResult = {
    startDate: "2010-01-01",
    endDate: "2020-01-01",
    terminalWealth: 1,
    terminalReturn: 0,
    maxDrawdown: 0,
    minEquity: 1,
    deployedAtHalfway: 0.75,
    deployedAtYear8: 1,
    forcedCatchUpMonths: 1,
    totalInvested: 1,
    trades: [
      {
        date: "2010-01-01",
        action: 0.50,
        deployed: 0.50,
        cash: 0.50,
        coupledTarget: 0.50,
        clockTarget: 0.25,
        agreement: 1,
        divergenceState: "CONVERGENT",
        mutualChaseState: "CONVERGENT",
        mutualLeaderChanges: 0,
        mutualCurveCrossings: 0,
      },
      {
        date: "2010-02-01",
        action: 0.25,
        deployed: 0.75,
        cash: 0.25,
        coupledTarget: 0.50,
        clockTarget: 0.50,
        agreement: 1,
        divergenceState: "CONVERGENT",
        mutualChaseState: "CONVERGENT",
        mutualLeaderChanges: 0,
        mutualCurveCrossings: 0,
      },
      {
        date: "2010-03-01",
        action: 0.05,
        deployed: 0.80,
        cash: 0.20,
        coupledTarget: 0.75,
        clockTarget: 0.75,
        agreement: 0.65,
        divergenceState: "TENSION",
        mutualChaseState: "CONVERGENT",
        mutualLeaderChanges: 0,
        mutualCurveCrossings: 0,
      },
      {
        date: "2010-04-01",
        action: 0.20,
        deployed: 1,
        cash: 0,
        coupledTarget: 1,
        clockTarget: 1,
        agreement: 0,
        divergenceState: "DIVERGENT",
        mutualChaseState: "CONVERGENT",
        mutualLeaderChanges: 0,
        mutualCurveCrossings: 0,
      },
    ],
    path: [{ date: "2010-01-01", action: 0.5, deployed: 0.5, cash: 0.5, coupledTarget: 0.5, clockTarget: 0.25, agreement: 1, divergenceState: "CONVERGENT" }, { date: "2010-02-01", action: 0.25, deployed: 0.75, cash: 0.25, coupledTarget: 0.5, clockTarget: 0.5, agreement: 1, divergenceState: "CONVERGENT" }, { date: "2010-03-01", action: 0.05, deployed: 0.8, cash: 0.19999999999999996, coupledTarget: 0.75, clockTarget: 0.75, agreement: 0.65, divergenceState: "TENSION" }, { date: "2010-04-01", action: 0.2, deployed: 1, cash: 0, coupledTarget: 1, clockTarget: 1, agreement: 0, divergenceState: "DIVERGENT" }],
  };

  const summary = summarizeStatePath([result]);
  const convergent = summary.find((x) => x.state === "CONVERGENT")!;
  const tension = summary.find((x) => x.state === "TENSION")!;
  const divergent = summary.find((x) => x.state === "DIVERGENT")!;

  assert.equal(convergent.observations, 2);
  assert.equal(Number(convergent.meanAheadOfClock.toFixed(4)), 0.25);
  assert.equal(Number(tension.meanAheadOfClock.toFixed(4)), 0.05);
  assert.equal(Number(divergent.meanAheadOfClock.toFixed(4)), 0);
  assert.equal(convergent.episodes, 1);
  assert.equal(convergent.maxEpisodeMonths, 2);
});


test("capital-floor target asks for required front-load, not maximum terminal wealth", () => {
  const flat = Array.from({ length: 121 }, () => 1);
  assert.equal(requiredFrontLoadFraction(flat), 0);

  const path = Array.from({ length: 121 }, (_, i) => (i === 120 ? 1.2 : 2));
  const required = requiredFrontLoadFraction(path);
  assert.ok(required > 0.66 && required < 0.68);

  const unrecoverable = Array.from({ length: 121 }, (_, i) => (i === 120 ? 0.8 : 2));
  assert.equal(requiredFrontLoadFraction(unrecoverable), 1);
});


test("full floor-response profile preserves tail shape beyond the 95% scalar target", () => {
  const paths = [
    Array.from({ length: 121 }, (_, i) => (i === 120 ? 0.8 : 2)),
    Array.from({ length: 121 }, (_, i) => (i === 120 ? 1.2 : 2)),
    Array.from({ length: 121 }, (_, i) => (i === 120 ? 1.3 : 2)),
  ];
  const profile = floorProfile(paths);
  assert.deepEqual(profile.probabilities, [0.5, 0.75, 0.9, 0.95, 0.99, 1]);
  assert.ok(profile.requiredFrontLoad[0] > 0.6 && profile.requiredFrontLoad[0] < 0.7);
  assert.equal(profile.requiredFrontLoad[1], 1);
  assert.equal(profile.requiredFrontLoad[3], 1);
  assert.equal(profile.requiredFrontLoad.at(-1), 1);
});


test("deployment response profile keeps the conservative terminal-floor curve", () => {
  const flat = Array.from({ length: 121 }, () => 1);
  const profile = deploymentResponseProfile([flat]);
  assert.deepEqual(profile.deploymentFractions.slice(0, 3), [0, 0.05, 0.1]);
  assert.equal(profile.deploymentFractions.at(-1), 1);
  assert.equal(profile.q05Terminal.length, 21);
  assert.equal(profile.pNonLoss[0], 1);
  assert.equal(profile.pNonLoss.at(-1), 1);
});


test("GAR / MaxDD baseline profile is diagnostic and aligned to the existing deployment-response grid", () => {
  const rising = Array.from({ length: 121 }, (_, i) => 1 + i / 60);
  const falling = Array.from({ length: 121 }, (_, i) => Math.max(0.5, 1 - i / 240));
  const profile = buildRiskBaselineProfile([rising, falling]);

  assert.deepEqual(profile.deploymentFractions.slice(0, 3), [0, 0.05, 0.1]);
  assert.equal(profile.deploymentFractions.at(-1), 1);
  assert.equal(profile.garMedian.length, 21);
  assert.equal(profile.garQ05.length, 21);
  assert.equal(profile.garQ95.length, 21);
  assert.equal(profile.maxDdMedian.length, 21);
  assert.equal(profile.maxDdQ05.length, 21);
  assert.equal(profile.maxDdQ95.length, 21);

  for (const x of profile.garMedian.concat(profile.garQ05, profile.garQ95, profile.maxDdMedian, profile.maxDdQ05, profile.maxDdQ95)) {
    assert.ok(Number.isFinite(x));
  }

  assert.ok(profile.garQ05[20] <= profile.garMedian[20]);
  assert.ok(profile.garMedian[20] <= profile.garQ95[20]);
  assert.ok(profile.maxDdQ05[20] <= profile.maxDdMedian[20]);
  assert.ok(profile.maxDdMedian[20] <= profile.maxDdQ95[20]);
});
