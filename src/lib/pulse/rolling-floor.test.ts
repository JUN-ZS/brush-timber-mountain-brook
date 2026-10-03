import test from "node:test";
import assert from "node:assert/strict";
import {
  median,
  couple,
  deploymentResponseProfile,
  divergenceState,
  floorProfile,
  requiredFrontLoadFraction,
  buildRiskBaselineProfile,
  buildForwardPathProfile,
  summarizeStatePath,
  adaptiveCreditConfidence,
  replayOne,
  replayFundingPlan,
  type ReplayResult,
} from "./rolling-floor.ts";

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
    forwardPathProfile: null,
    nearestAnalogDistance: 0.1,
    q05: 1,
    pNonLoss: 0.5,
    mean: 1.1,
    nAnalogs: 20,
    effectiveN: 5,
    status: "OK" as const,
    creditMaxDrawdowns: null,
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
    forwardPathProfile: null,
    nearestAnalogDistance: 0.1,
    q05: 1,
    pNonLoss: 0.5,
    mean: 1.1,
    nAnalogs: 20,
    effectiveN: 5,
    status: "OK" as const,
    creditMaxDrawdowns: null,
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
        creditAmount: 0,
        creditConfidence: 0,
        effectiveTarget: 0.50,
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
        creditAmount: 0,
        creditConfidence: 0,
        effectiveTarget: 0.50,
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
        creditAmount: 0,
        creditConfidence: 0,
        effectiveTarget: 0.75,
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
        creditAmount: 0,
        creditConfidence: 0,
        effectiveTarget: 1,
      },
    ],
    path: [
    { date: "2010-01-01", action: 0.5, deployed: 0.5, cash: 0.5, coupledTarget: 0.5, clockTarget: 0.25, agreement: 1, divergenceState: "CONVERGENT", mutualChaseState: "CONVERGENT", mutualLeaderChanges: 0, mutualCurveCrossings: 0, creditAmount: 0, creditConfidence: 0, effectiveTarget: 0.5 },
    { date: "2010-02-01", action: 0.25, deployed: 0.75, cash: 0.25, coupledTarget: 0.5, clockTarget: 0.5, agreement: 1, divergenceState: "CONVERGENT", mutualChaseState: "CONVERGENT", mutualLeaderChanges: 0, mutualCurveCrossings: 0, creditAmount: 0, creditConfidence: 0, effectiveTarget: 0.5 },
    { date: "2010-03-01", action: 0.05, deployed: 0.8, cash: 0.19999999999999996, coupledTarget: 0.75, clockTarget: 0.75, agreement: 0.65, divergenceState: "TENSION", mutualChaseState: "CONVERGENT", mutualLeaderChanges: 0, mutualCurveCrossings: 0, creditAmount: 0, creditConfidence: 0, effectiveTarget: 0.75 },
    { date: "2010-04-01", action: 0.2, deployed: 1, cash: 0, coupledTarget: 1, clockTarget: 1, agreement: 0, divergenceState: "DIVERGENT", mutualChaseState: "CONVERGENT", mutualLeaderChanges: 0, mutualCurveCrossings: 0, creditAmount: 0, creditConfidence: 0, effectiveTarget: 1 },
  ],
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


test("funding clock can start at 10% or 20% and still targets 100% B", () => {
  const qqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: 1,
  }));
  const signal = {
    asof: qqq[0].date,
    clockTarget: 0,
    divergenceState: "THIN" as const,
    signals: [],
    perScale: [],
    robustTarget: null,
    agreement: 0,
    coupledTarget: 0,
    mutualChase: [],
  };
  const panel = new Map(qqq.map((p) => [p.date, signal]));

  for (const initial of [0.10, 0.20]) {
    const result = replayFundingPlan(
      qqq,
      panel,
      0,
      120,
      "CLOCK_FUNDED",
      1,
      initial,
    )!;
    assert.equal(result.initialFundingFraction, initial);
    assert.equal(Number(result.path[0].contribution.toFixed(6)), initial);
    assert.equal(Number(result.path.at(-1)!.cumulativeContributed.toFixed(6)), 1);
    assert.equal(Number(result.totalContributed.toFixed(6)), 1);
    assert.equal(Number(result.path.at(-1)!.clockTarget.toFixed(6)), 1);
  }
});

test("funding plan keeps principal outside until monthly funding is actually needed", () => {
  const qqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: i === 0 ? 1 : i === 1 ? 1.30 : 1.30,
  }));

  const signalFor = (date: string) => ({
    asof: date,
    clockTarget: 0,
    divergenceState: "CONVERGENT" as const,
    signals: [20, 30, 50].map((scaleYears) => ({
      channel: "S",
      layer: "OBSERVED" as const,
      scaleYears: scaleYears as 20 | 30 | 50,
      asof: date,
      target: null,
      floorProfile: null,
      responseProfile: null,
      riskBaselineProfile: null,
      forwardPathProfile: null,
      nearestAnalogDistance: 0,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: 8,
      effectiveN: 2,
      status: "OK" as const,
      creditMaxDrawdowns: Array(8).fill(0),
    })),
    perScale: [],
    robustTarget: null,
    agreement: 0,
    coupledTarget: 0,
    mutualChase: [],
  });

  const panel = new Map(
    qqq.map((p) => [p.date, signalFor(p.date)]),
  );

  const clock = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "CLOCK_FUNDED",
  )!;
  const adaptive = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
  )!;

  // Month 1 receives only the clock amount; the rest of the planned capital
  // remains outside the account.
  assert.equal(Number(clock.path[0].contribution.toFixed(6)), Number((1 / 120).toFixed(6)));
  assert.ok(clock.path[0].remainingExternalCapital > 0.99);

  // The current month's close cannot fund the same month's decision.
  assert.equal(adaptive.path[1].fundingCredit, 0);

  // Month 3 can use the prior month's closed gain and reduces new external funding.
  assert.ok(adaptive.path[2].fundingCredit > 0);
  assert.ok(
    adaptive.path[2].contribution < clock.path[2].contribution,
  );

  // Under a sustained gain, the reduced external funding is not required to
  // catch back up; the earned surplus itself remains inside the account.
  assert.ok(adaptive.totalContributed < 1);
  assert.equal(adaptive.path[0].accountCash, 0);

  // B is an immutable plan ceiling, not a recursive output. Scaling B must
  // preserve every funding ratio and NAV/B ratio.
  const scaled = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
    100,
  )!;
  assert.equal(scaled.plannedPrincipal, 100);
  assert.equal(
    Number((scaled.totalContributed / scaled.plannedPrincipal).toFixed(6)),
    Number(adaptive.totalContributed.toFixed(6)),
  );
  assert.equal(
    Number(
      (
        scaled.path[2].nav / scaled.plannedPrincipal
      ).toFixed(6),
    ),
    Number(adaptive.path[2].nav.toFixed(6)),
  );

  const reversalQqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: i === 0 ? 1 : i === 1 ? 1.30 : 0.80,
  }));
  const reversalPanel = new Map(
    reversalQqq.map((p) => [p.date, signalFor(p.date)]),
  );
  const reversal = replayFundingPlan(
    reversalQqq,
    reversalPanel,
    0,
    120,
    "ADAPTIVE_FUNDED",
  )!;

  // The month-3 decision can still use the month-2 gain.
  assert.ok(reversal.path[2].fundingCredit > 0);

  // After the month-3 loss is closed, credit vanishes and future contributions resume.
  assert.equal(reversal.path[3].fundingCredit, 0);
  assert.ok(reversal.path[3].contribution >= clock.path[3].contribution);
  assert.equal(Number(reversal.totalContributed.toFixed(6)), 1);
  assert.equal(
    Number(
      (
        reversal.totalContributed +
        reversal.path.at(-1)!.remainingExternalCapital
      ).toFixed(6),
    ),
    1,
  );
});

test("adaptive credit is a majority survival probability, not a GAR/MaxDD score", () => {
  const mk = (scaleYears: 20 | 30 | 50, samples: number[]) => ({
    channel: "S",
    layer: "OBSERVED" as const,
    scaleYears,
    asof: "2026-01-01",
    target: 0,
    floorProfile: null,
    responseProfile: null,
    riskBaselineProfile: null,
    forwardPathProfile: null,
    nearestAnalogDistance: 0.1,
    q05: 1,
    pNonLoss: 1,
    mean: 1,
    nAnalogs: samples.length,
    effectiveN: samples.length / 4,
    status: "OK" as const,
    creditMaxDrawdowns: samples,
  });

  const signal = {
    asof: "2026-01-01",
    clockTarget: 0.5,
    divergenceState: "CONVERGENT" as const,
    signals: [
      mk(20, Array(8).fill(0)),
      mk(30, Array(8).fill(0)),
      mk(50, Array(8).fill(0)),
    ],
    perScale: [],
    robustTarget: null,
    agreement: 1,
    coupledTarget: 0.5,
    mutualChase: [],
  };

  assert.equal(adaptiveCreditConfidence(signal, 0.10, 0.01), 1);

  const weak = {
    ...signal,
    signals: [
      mk(20, [0, 0, 0, 0, -0.20, -0.20, -0.20, -0.20]),
      mk(30, [0, 0, 0, 0, -0.20, -0.20, -0.20, -0.20]),
      mk(50, [0, 0, 0, 0, -0.20, -0.20, -0.20, -0.20]),
    ],
  };
  // 0.01 surplus on 10% deployed = 10% tolerable drawdown; only 50% survive,
  // so the fixed majority gate admits q=0.5.
  assert.equal(adaptiveCreditConfidence(weak, 0.10, 0.01), 0.5);

  const rejected = {
    ...signal,
    signals: [
      mk(20, [0, 0, 0, -0.20, -0.20, -0.20, -0.20, -0.20]),
      mk(30, [0, 0, 0, -0.20, -0.20, -0.20, -0.20, -0.20]),
      mk(50, [0, 0, 0, -0.20, -0.20, -0.20, -0.20, -0.20]),
    ],
  };
  assert.equal(adaptiveCreditConfidence(rejected, 0.10, 0.01), 0);
});

test("adaptive credit reduces future buy and is revoked by a later floor breach", () => {
  const qqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: i === 0 ? 1 : i === 1 ? 1.2 : 0.8,
  }));

  const signalFor = (date: string) => ({
    asof: date,
    clockTarget: 0,
    divergenceState: "CONVERGENT" as const,
    signals: [20, 30, 50].map((scaleYears) => ({
      channel: "S",
      layer: "OBSERVED" as const,
      scaleYears: scaleYears as 20 | 30 | 50,
      asof: date,
      target: null,
      floorProfile: null,
      responseProfile: null,
      riskBaselineProfile: null,
      forwardPathProfile: null,
      nearestAnalogDistance: 0,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: 8,
      effectiveN: 2,
      status: "OK" as const,
      creditMaxDrawdowns: Array(8).fill(0),
    })),
    perScale: [],
    robustTarget: null,
    agreement: 0,
    coupledTarget: 0,
    mutualChase: [],
  });

  const panel = new Map(qqq.map((p) => [p.date, signalFor(p.date)]));
  const result = replayOne(qqq, panel, 0, "ADAPTIVE_CREDIT_ONLY")!;
  // Month 1 closes with the gain; month 2 is the first decision that can
  // legitimately use that closed surplus.
  assert.ok(result.path[2].creditAmount > 0);
  assert.ok(result.path[2].effectiveTarget < result.path[2].clockTarget);
  // The later 20% QQQ drop removes the surplus at the next decision point.
  assert.equal(result.path[3].creditAmount, 0);
  assert.ok(result.path[3].action > 1 / 120);
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



test("GAR / MaxDD risk curve remains fully invested at the terminal point", () => {
  const path = Array.from({ length: 121 }, (_, i) => 1 + i / 60);
  const profile = buildRiskBaselineProfile([path]);
  const flat = Array.from({ length: 121 }, () => 1);
  const flatProfile = buildRiskBaselineProfile([flat]);
  assert.ok(profile.garMedian.at(-1)! > 0);
  assert.equal(flatProfile.maxDdMedian.at(-1), 0);
  assert.equal(flatProfile.garMedian.at(-1), 0);
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


test("forward path profile preserves the fixed 10Y path geometry", () => {
  const flat = Array.from({ length: 121 }, () => 1);
  const rising = Array.from({ length: 121 }, (_, i) => 1 + i / 120);
  const profile = buildForwardPathProfile([flat, rising]);

  assert.equal(profile.months.length, 121);
  assert.equal(profile.months[0], 0);
  assert.equal(profile.months.at(-1), 120);
  assert.equal(profile.median[0], 1);
  assert.equal(profile.median.at(-1), 1.5);
  assert.equal(profile.q05.at(-1), 1.05);
  assert.equal(profile.q95.at(-1), 1.95);
});

test("partial B-floor withdrawal uses fixed alpha and preserves the B floor at execution", () => {
  const qqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: i === 0 ? 1 : 3,
  }));
  const signal = {
    asof: qqq[0].date,
    clockTarget: 0,
    divergenceState: "CONVERGENT" as const,
    signals: [20, 30, 50].map((scaleYears) => ({
      channel: "S",
      layer: "OBSERVED" as const,
      scaleYears: scaleYears as 20 | 30 | 50,
      asof: qqq[0].date,
      target: null,
      floorProfile: null,
      responseProfile: null,
      riskBaselineProfile: null,
      forwardPathProfile: null,
      nearestAnalogDistance: 0,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: 8,
      effectiveN: 2,
      status: "OK" as const,
      creditMaxDrawdowns: Array(8).fill(0),
    })),
    perScale: [],
    robustTarget: null,
    agreement: 0,
    coupledTarget: 0,
    mutualChase: [],
  };
  const panel = new Map(qqq.map((p) => [p.date, signal]));
  const alpha = 0.50;

  const result = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
    1,
    0.10,
    "PARTIAL_ABOVE_PLANNED_PRINCIPAL",
    new Map(),
    alpha,
  )!;

  const point = result.path[1];
  assert.equal(result.withdrawalAlpha, alpha);
  assert.equal(point.withdrawalAlpha, alpha);
  assert.ok(point.navBeforeWithdrawal > result.plannedPrincipal);
  assert.equal(
    Number(point.withdrawalExecuted.toFixed(10)),
    Number(
      ((point.navBeforeWithdrawal - result.plannedPrincipal) * alpha).toFixed(10),
    ),
  );
  assert.ok(point.nav + 1e-12 >= result.plannedPrincipal);
  assert.ok(point.nav < point.navBeforeWithdrawal);
});

test("B-floor withdrawal stays zero below B and never takes NAV below immutable planned principal", () => {
  const qqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: i === 0 ? 1 : 20,
  }));
  const signal = {
    asof: qqq[0].date,
    clockTarget: 0,
    divergenceState: "CONVERGENT" as const,
    signals: [20, 30, 50].map((scaleYears) => ({
      channel: "S",
      layer: "OBSERVED" as const,
      scaleYears: scaleYears as 20 | 30 | 50,
      asof: qqq[0].date,
      target: null,
      floorProfile: null,
      responseProfile: null,
      riskBaselineProfile: null,
      forwardPathProfile: null,
      nearestAnalogDistance: 0,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: 8,
      effectiveN: 2,
      status: "OK" as const,
      creditMaxDrawdowns: Array(8).fill(0),
    })),
    perScale: [],
    robustTarget: null,
    agreement: 0,
    coupledTarget: 0,
    mutualChase: [],
  };
  const panel = new Map(qqq.map((p) => [p.date, signal]));

  const date = qqq[1].date;
  // Month 0 is explicitly requested but NAV is only 10% of B, so eligibility
  // must stay at zero. Month 1 jumps above B and may withdraw only NAV-B.
  const requested = new Map([
    [qqq[0].date, 10],
    [date, 10],
  ]);
  const result = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
    1,
    0.10,
    "SCHEDULED",
    requested,
  )!;

  const early = result.path[0];
  assert.equal(early.withdrawalRequested, 10);
  assert.equal(early.withdrawalEligibleSurplus, 0);
  assert.equal(early.withdrawalExecuted, 0);
  assert.ok(early.nav < 1);

  const point = result.path[1];
  assert.ok(point.navBeforeWithdrawal > 1);
  assert.ok(point.withdrawalEligibleSurplus > 0);
  assert.equal(
    Number(point.withdrawalEligibleSurplus.toFixed(10)),
    Number((point.navBeforeWithdrawal - result.plannedPrincipal).toFixed(10)),
  );
  assert.equal(
    Number(point.withdrawalExecuted.toFixed(10)),
    Number(point.withdrawalEligibleSurplus.toFixed(10)),
  );
  assert.equal(Number(point.nav.toFixed(10)), 1);
  assert.ok(point.nav + 1e-12 >= result.plannedPrincipal);
  assert.equal(result.totalContributed <= 1, true);
  assert.ok(result.totalWithdrawn > 0);

  const scaled = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
    100,
    0.10,
    "SCHEDULED",
    new Map([
      [qqq[0].date, 1000],
      [qqq[1].date, 1000],
    ]),
  )!;
  assert.equal(scaled.plannedPrincipal, 100);
  assert.equal(Number(scaled.path[0].withdrawalExecuted.toFixed(10)), 0);
  assert.equal(Number(scaled.path[1].nav.toFixed(10)), 100);
  assert.equal(
    Number(
      (scaled.path[1].withdrawalExecuted / scaled.plannedPrincipal).toFixed(10),
    ),
    Number(
      (point.withdrawalExecuted / point.plannedPrincipal).toFixed(10),
    ),
  );

  assert.throws(
    () =>
      replayFundingPlan(
        qqq,
        panel,
        0,
        120,
        "ADAPTIVE_FUNDED",
        1,
        0.10,
        "SCHEDULED",
        new Map([[qqq[1].date, -0.01]]),
      ),
    /finite and non-negative/,
  );
});

test("profit sweep and adaptive credit are mutually exclusive uses of the same surplus", () => {
  const qqq = Array.from({ length: 121 }, (_, i) => ({
    date: new Date(Date.UTC(2010, i, 1)).toISOString().slice(0, 10),
    value: 1 + i * 0.05,
  }));
  const signalFor = (date: string) => ({
    asof: date,
    clockTarget: 0,
    divergenceState: "CONVERGENT" as const,
    signals: [20, 30, 50].map((scaleYears) => ({
      channel: "S",
      layer: "OBSERVED" as const,
      scaleYears: scaleYears as 20 | 30 | 50,
      asof: date,
      target: null,
      floorProfile: null,
      responseProfile: null,
      riskBaselineProfile: null,
      forwardPathProfile: null,
      nearestAnalogDistance: 0,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: 8,
      effectiveN: 2,
      status: "OK" as const,
      creditMaxDrawdowns: Array(8).fill(0),
    })),
    perScale: [],
    robustTarget: null,
    agreement: 0,
    coupledTarget: 0,
    mutualChase: [],
  });
  const panel = new Map(qqq.map((p) => [p.date, signalFor(p.date)]));

  const noWithdrawal = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
    1,
    0.10,
    "NONE",
  )!;
  const sweep = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "ADAPTIVE_FUNDED",
    1,
    0.10,
    "SWEEP_ELIGIBLE_SURPLUS",
  )!;
  const clock = replayFundingPlan(
    qqq,
    panel,
    0,
    120,
    "CLOCK_FUNDED",
    1,
    0.10,
    "SWEEP_ELIGIBLE_SURPLUS",
  )!;

  const creditPoint = noWithdrawal.path.find(
    (point) => point.nextDecisionCreditBeforeWithdrawal > 1e-12,
  )!;
  const sweepPoint = sweep.path.find(
    (point) => point.nextDecisionCreditBeforeWithdrawal > 1e-12,
  )!;

  assert.ok(creditPoint);
  assert.ok(sweepPoint);
  assert.ok(noWithdrawal.totalContributed < 1);
  assert.equal(Number(sweep.totalContributed.toFixed(8)), 1);
  assert.equal(Number(clock.totalContributed.toFixed(8)), 1);
  assert.ok(sweep.totalWithdrawn > 0);

  // The same close has surplus before extraction, but after extraction there
  // is no remaining surplus to support a future credit.
  assert.ok(sweepPoint.nextDecisionCreditBeforeWithdrawal > 0);
  assert.equal(Number(sweepPoint.nextDecisionCreditAfterWithdrawal.toFixed(10)), 0);
  assert.equal(
    Number(
      sweepPoint.creditCancelledByWithdrawal.toFixed(10),
    ),
    Number(sweepPoint.nextDecisionCreditBeforeWithdrawal.toFixed(10)),
  );

  // Once the surplus is swept, adaptive funding follows the hard clock rather
  // than retaining both the cash withdrawal and the deferred contribution.
  assert.equal(
    Number(sweep.totalContributed.toFixed(8)),
    Number(clock.totalContributed.toFixed(8)),
  );
  assert.equal(
    Number(
      (
        sweep.terminalWealth +
        sweep.totalWithdrawn -
        sweep.totalContributed
      ).toFixed(10),
    ),
    Number(sweep.netEconomicWealth.toFixed(10)),
  );
});

