import { universe } from "./bars.ts";

export const FLOOR_HORIZON_YEARS = 10;
export const FLOOR_HORIZON_MONTHS = FLOOR_HORIZON_YEARS * 12;
// The controller knows only the hard 100% principal plan. This default keeps
// the original monthly clock behavior, while callers may explicitly choose a
// larger initial funding fraction such as 10% or 20%.
export const DEFAULT_INITIAL_FUNDING_FRACTION =
  1 / FLOOR_HORIZON_MONTHS;
export const TRAP_SCALES_YEARS = [20, 30, 50] as const;

export type TrapScale = (typeof TRAP_SCALES_YEARS)[number];

export type SeriesPoint = {
  date: string;
  value: number;
};

export type MonthlyPoint = SeriesPoint;

export type StateVector = {
  dd12: number;
  dd36: number;
  mom12: number;
  vol6: number;
  ddDurationMonths: number;
};

export type Analog = {
  date: string;
  distance: number;
  weight: number;
  terminal: number;
  path: number[];
};

export type Channel = {
  id: string;
  layer: "OBSERVED" | "PROXY_PRICE";
  points: MonthlyPoint[];
};

export type FloorProfile = {
  probabilities: number[];
  requiredFrontLoad: number[];
  meanRequiredFrontLoad: number;
  maxRequiredFrontLoad: number;
};

export type DeploymentResponseProfile = {
  deploymentFractions: number[];
  q05Terminal: number[];
  pNonLoss: number[];
  meanTerminal: number[];
};

export type RiskBaselineProfile = {
  deploymentFractions: number[];
  garMedian: number[];
  garQ05: number[];
  garQ95: number[];
  maxDdMedian: number[];
  maxDdQ05: number[];
  maxDdQ95: number[];
};

export type ForwardPathProfile = {
  months: number[];
  median: number[];
  q05: number[];
  q95: number[];
};

export type MutualChaseTopology = {
  state: DivergenceState;
  localDirections: Array<"FORWARD" | "BACKWARD" | "FLAT" | "MIXED">;
  leaderScaleBySegment: Array<TrapScale | null>;
  leaderChanges: number;
  pairwiseCurveCrossings: number;
};

export type ChannelScaleSignal = {
  channel: string;
  layer: Channel["layer"];
  scaleYears: TrapScale;
  asof: string;
  target: number | null;
  floorProfile: FloorProfile | null;
  responseProfile: DeploymentResponseProfile | null;
  riskBaselineProfile: RiskBaselineProfile | null;
  forwardPathProfile: ForwardPathProfile | null;
  nearestAnalogDistance: number | null;
  q05: number | null;
  pNonLoss: number | null;
  mean: number | null;
  nAnalogs: number;
  effectiveN: number;
  status: "OK" | "INSUFFICIENT_HISTORY";
  // Raw per-analog 10Y MaxDD samples for empirical surplus-survival credit.
  // This is not a GAR/MaxDD weighted score.
  creditMaxDrawdowns: number[] | null;
};

export type DivergenceState = "CONVERGENT" | "TENSION" | "DIVERGENT" | "THIN";

export type CoupledSignal = {

  asof: string;
  clockTarget: number;
  divergenceState: DivergenceState;
  signals: ChannelScaleSignal[];
  perScale: Array<{
    scaleYears: TrapScale;
    target: number | null;
    agreement: number;
    nSignals: number;
    responseProfile: DeploymentResponseProfile | null;
    riskBaselineProfile: RiskBaselineProfile | null;
    forwardPathProfile: ForwardPathProfile | null;
    nearestAnalogDistance: number | null;
  }>;
  robustTarget: number | null;
  agreement: number;
  coupledTarget: number;
  mutualChase: Array<{
    channel: string;
    topology: MutualChaseTopology;
  }>;
};

export type ReplayTrade = {
  date: string;
  action: number;
  deployed: number;
  cash: number;
  coupledTarget: number;
  clockTarget: number;
  agreement: number;
  divergenceState: DivergenceState;
  mutualChaseState: DivergenceState;
  mutualLeaderChanges: number;
  mutualCurveCrossings: number;
  creditAmount: number;
  creditConfidence: number;
  effectiveTarget: number;
};

export type ReplayPathPoint = {
  date: string;
  action: number;
  deployed: number;
  cash: number;
  coupledTarget: number;
  clockTarget: number;
  agreement: number;
  divergenceState: DivergenceState;
  mutualChaseState: DivergenceState;
  mutualLeaderChanges: number;
  mutualCurveCrossings: number;
  creditAmount: number;
  creditConfidence: number;
  effectiveTarget: number;
};

export type FundingPlanMode = "CLOCK_FUNDED" | "ADAPTIVE_FUNDED";

export type ProfitWithdrawalMode =
  | "NONE"
  | "SCHEDULED"
  | "SWEEP_ELIGIBLE_SURPLUS";

export type FundingPathPoint = {
  date: string;
  contribution: number;
  cumulativeContributed: number;
  remainingExternalCapital: number;
  plannedPrincipal: number;
  initialFundingFraction: number;
  invested: number;
  accountCash: number;
  navBeforeWithdrawal: number;
  nav: number;
  surplus: number;
  fundingCredit: number;
  creditConfidence: number;
  fundingTarget: number;
  clockTarget: number;
  withdrawalEligibleSurplus: number;
  withdrawalRequested: number;
  withdrawalExecuted: number;
  cumulativeWithdrawn: number;
  nextDecisionCreditBeforeWithdrawal: number;
  nextDecisionCreditAfterWithdrawal: number;
  creditCancelledByWithdrawal: number;
  divergenceState: DivergenceState;
};

export type FundingReplayResult = {
  startDate: string;
  endDate: string;
  horizonMonths: number;
  plannedPrincipal: number;
  initialFundingFraction: number;
  terminalWealth: number;
  maxDrawdown: number;
  totalContributed: number;
  totalWithdrawn: number;
  maxContributionReduction: number;
  totalContributionReduction: number;
  netEconomicWealth: number;
  path: FundingPathPoint[];
};

export type ReplayMode = "COUPLED" | "ADAPTIVE_CREDIT_ONLY";

export type ReplayResult = {
  startDate: string;
  endDate: string;
  terminalWealth: number;
  terminalReturn: number;
  maxDrawdown: number;
  minEquity: number;
  deployedAtHalfway: number;
  deployedAtYear8: number;
  forcedCatchUpMonths: number;
  totalInvested: number;
  trades: ReplayTrade[];
  path: ReplayPathPoint[];
};

const MIN_ANALOGS = 8;
const MAX_ANALOGS = 24;
const ANALOG_STRIDE_MONTHS = 3;
const FLOOR_PROFILE_PROBABILITIES = [0.50, 0.75, 0.90, 0.95, 0.99, 1.00];
const AGREEMENT_MAD_SCALE = 0.15;
const TENSION_AGREEMENT = 0.80;
const DIVERGENT_AGREEMENT = 0.50;

// A fixed majority gate: less than half of the empirical analog paths
// supporting surplus survival means no credit and full clock authority.
export const CREDIT_MIN_SURVIVAL = 0.50;

function clamp(x: number, lo = 0, hi = 1) {
  return Math.max(lo, Math.min(hi, x));
}

export function median(xs: number[]) {
  if (!xs.length) return null;
  const a = [...xs].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

export function mad(xs: number[], center?: number) {
  if (!xs.length) return 0;
  const c = center ?? median(xs) ?? 0;
  return median(xs.map((x) => Math.abs(x - c))) ?? 0;
}

export function quantile(xs: number[], q: number) {
  if (!xs.length) return null;
  const a = [...xs].sort((x, y) => x - y);
  const p = (a.length - 1) * q;
  const lo = Math.floor(p);
  const hi = Math.ceil(p);
  return a[lo] + (a[hi] - a[lo]) * (p - lo);
}

export function addYears(date: string, years: number) {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCFullYear(d.getUTCFullYear() + years);
  return d.toISOString().slice(0, 10);
}

export function monthKey(date: string) {
  return date.slice(0, 7);
}

export function monthsBetween(a: string, b: string) {
  const da = new Date(`${a.slice(0, 7)}-01T00:00:00Z`);
  const db = new Date(`${b.slice(0, 7)}-01T00:00:00Z`);
  return (
    (db.getUTCFullYear() - da.getUTCFullYear()) * 12 +
    db.getUTCMonth() -
    da.getUTCMonth()
  );
}

export function monthlyize(points: SeriesPoint[]): MonthlyPoint[] {
  const lastByMonth = new Map<string, SeriesPoint>();
  for (const p of points) {
    if (!Number.isFinite(p.value) || p.value <= 0) continue;
    const key = monthKey(p.date);
    const prev = lastByMonth.get(key);
    if (!prev || p.date > prev.date) lastByMonth.set(key, p);
  }
  return [...lastByMonth.values()].sort((a, b) => a.date.localeCompare(b.date));
}

export function qqqMonthly(): MonthlyPoint[] {
  const q = universe.c.QQQ ?? [];
  const out: SeriesPoint[] = [];
  for (let i = 0; i < universe.dates.length; i++) {
    const v = q[i];
    if (v != null && v > 0) out.push({ date: universe.dates[i], value: v });
  }
  return monthlyize(out);
}

export function stateAt(points: MonthlyPoint[], index: number): StateVector | null {
  if (index < 36) return null;
  const px = points[index]?.value;
  if (px == null || px <= 0) return null;

  const p12 = points[index - 12]?.value;
  const p36 = points[index - 36]?.value;
  if (p12 == null || p36 == null || p12 <= 0 || p36 <= 0) return null;

  const r6: number[] = [];
  for (let i = Math.max(1, index - 5); i <= index; i++) {
    const a = points[i - 1]?.value;
    const b = points[i]?.value;
    if (a != null && b != null && a > 0 && b > 0) r6.push(b / a - 1);
  }
  const m6 = r6.length ? r6.reduce((a, b) => a + b, 0) / r6.length : 0;
  const variance =
    r6.length > 1
      ? r6.reduce((s, x) => s + (x - m6) ** 2, 0) / r6.length
      : 0;

  let peak = points[index - 12]?.value ?? px;
  for (let i = index - 12; i <= index; i++) peak = Math.max(peak, points[i]?.value ?? peak);
  const dd12 = px / peak - 1;

  peak = points[index - 36]?.value ?? px;
  for (let i = index - 36; i <= index; i++) peak = Math.max(peak, points[i]?.value ?? peak);
  const dd36 = px / peak - 1;

  let duration = 0;
  for (let i = index; i > 0; i--) {
    if ((points[i]?.value ?? 0) < (points[i - 1]?.value ?? 0)) duration++;
    else break;
  }

  return {
    dd12,
    dd36,
    mom12: px / p12 - 1,
    vol6: Math.sqrt(variance) * Math.sqrt(12),
    ddDurationMonths: duration,
  };
}

function featureDistance(a: StateVector, b: StateVector) {
  const scales = [0.15, 0.30, 0.30, 0.20, 24];
  const xs = [
    (a.dd12 - b.dd12) / scales[0],
    (a.dd36 - b.dd36) / scales[1],
    (a.mom12 - b.mom12) / scales[2],
    (a.vol6 - b.vol6) / scales[3],
    (a.ddDurationMonths - b.ddDurationMonths) / scales[4],
  ];
  return Math.sqrt(xs.reduce((s, x) => s + x * x, 0));
}

function pathFrom(points: MonthlyPoint[], index: number): number[] | null {
  if (index + FLOOR_HORIZON_MONTHS >= points.length) return null;
  const base = points[index]?.value;
  if (base == null || base <= 0) return null;
  const out: number[] = [];
  for (let j = 0; j <= FLOOR_HORIZON_MONTHS; j++) {
    const v = points[index + j]?.value;
    if (v == null || v <= 0) return null;
    out.push(v / base);
  }
  return out;
}

function outcomeIndexByMonth(points: MonthlyPoint[], date: string) {
  const key = monthKey(date);
  const exact = points.findIndex((p) => monthKey(p.date) === key);
  if (exact >= 0) return exact;
  return indexAtOrBefore(points, date);
}

function terminalForDeployment(a: number, path: number[]) {
  const h = FLOOR_HORIZON_MONTHS;
  const terminalGrowth = path[h];
  let ladder = 0;
  for (let k = 1; k <= h; k++) {
    const fromKToEnd = terminalGrowth / path[k];
    ladder += fromKToEnd;
  }
  return a * terminalGrowth + ((1 - a) / h) * ladder;
}

function terminalAtZeroAndOne(path: number[]) {
  return {
    zero: terminalForDeployment(0, path),
    one: terminalForDeployment(1, path),
  };
}

function equityCurveForDeployment(a: number, path: number[]) {
  const h = FLOOR_HORIZON_MONTHS;
  if (path.length <= h || h <= 0) return [1];

  const initial = clamp(a);
  const monthlyRemainder = (1 - initial) / h;
  const curve = [1];

  for (let j = 1; j <= h; j++) {
    const px = path[j];
    if (!Number.isFinite(px) || px <= 0) return curve;
    const cash = Math.max(0, (1 - initial) - monthlyRemainder * j);
    let equity = initial * px + cash;
    for (let k = 1; k <= j; k++) {
      const entry = path[k];
      if (!Number.isFinite(entry) || entry <= 0) return curve;
      equity += monthlyRemainder * (px / entry);
    }
    curve.push(equity);
  }

  return curve;
}

function garFromTerminal(terminal: number) {
  return Math.pow(Math.max(1e-12, terminal), 1 / FLOOR_HORIZON_YEARS) - 1;
}

function riskMetricsForDeployment(a: number, path: number[]) {
  const terminal = terminalForDeployment(a, path);
  const maxDd = equityStats(equityCurveForDeployment(a, path)).maxDd;
  return {
    gar: garFromTerminal(terminal),
    maxDd,
  };
}

export function buildRiskBaselineProfile(paths: number[][]): RiskBaselineProfile {
  const deploymentFractions = Array.from({ length: 21 }, (_, i) => i / 20);
  const rows = deploymentFractions.map((a) => {
    const metrics = paths.map((path) => riskMetricsForDeployment(a, path));
    return {
      gar: {
        median: median(metrics.map((x) => x.gar)) ?? 0,
        q05: quantile(metrics.map((x) => x.gar), 0.05) ?? 0,
        q95: quantile(metrics.map((x) => x.gar), 0.95) ?? 0,
      },
      maxDd: {
        median: median(metrics.map((x) => x.maxDd)) ?? 0,
        q05: quantile(metrics.map((x) => x.maxDd), 0.05) ?? 0,
        q95: quantile(metrics.map((x) => x.maxDd), 0.95) ?? 0,
      },
    };
  });

  return {
    deploymentFractions,
    garMedian: rows.map((x) => x.gar.median),
    garQ05: rows.map((x) => x.gar.q05),
    garQ95: rows.map((x) => x.gar.q95),
    maxDdMedian: rows.map((x) => x.maxDd.median),
    maxDdQ05: rows.map((x) => x.maxDd.q05),
    maxDdQ95: rows.map((x) => x.maxDd.q95),
  };
}

export function buildForwardPathProfile(paths: number[][]): ForwardPathProfile {
  const months = Array.from({ length: FLOOR_HORIZON_MONTHS + 1 }, (_, i) => i);
  return {
    months,
    median: months.map((i) => median(paths.map((p) => p[i] ?? 1)) ?? 1),
    q05: months.map((i) => quantile(paths.map((p) => p[i] ?? 1), 0.05) ?? 1),
    q95: months.map((i) => quantile(paths.map((p) => p[i] ?? 1), 0.95) ?? 1),
  };
}

export function requiredFrontLoadFraction(path: number[], floor = 1) {
  const { zero, one } = terminalAtZeroAndOne(path);
  if (zero >= floor) return 0;
  if (one < floor) return 1;

  const slope = one - zero;
  if (slope <= 0) return 1;
  return clamp((floor - zero) / slope);
}

function objective(paths: number[][], a: number) {
  const ws = paths.map((p) => terminalForDeployment(a, p));
  const q05 = quantile(ws, 0.05) ?? 0;
  const pNonLoss = ws.filter((w) => w >= 1).length / ws.length;
  const mean = ws.reduce((x, y) => x + y, 0) / ws.length;
  return { q05, pNonLoss, mean };
}

export function deploymentResponseProfile(paths: number[][]): DeploymentResponseProfile {
  const deploymentFractions = Array.from({ length: 21 }, (_, i) => i / 20);
  const rows = deploymentFractions.map((a) => objective(paths, a));
  return {
    deploymentFractions,
    q05Terminal: rows.map((x) => x.q05),
    pNonLoss: rows.map((x) => x.pNonLoss),
    meanTerminal: rows.map((x) => x.mean),
  };
}

export function floorProfile(paths: number[][]): FloorProfile {
  const required = paths.map((path) => requiredFrontLoadFraction(path, 1));
  const ordered = [...required].sort((a, b) => a - b);
  const requiredFrontLoad = FLOOR_PROFILE_PROBABILITIES.map((p) => {
    const index = Math.max(0, Math.ceil(p * ordered.length) - 1);
    return ordered[index] ?? 1;
  });

  return {
    probabilities: [...FLOOR_PROFILE_PROBABILITIES],
    requiredFrontLoad,
    meanRequiredFrontLoad:
      required.reduce((sum, x) => sum + x, 0) / Math.max(1, required.length),
    maxRequiredFrontLoad: ordered.at(-1) ?? 1,
  };
}

function floorTarget(paths: number[][]) {
  const profile = floorProfile(paths);
  const index = FLOOR_PROFILE_PROBABILITIES.indexOf(0.95);
  // Keep the established scalar 95% floor controller unchanged. The extra
  // profile is preserved for structural cross-scale analysis.
  return profile.requiredFrontLoad[index] ?? 1;
}

function buildAnalogs(
  statePoints: MonthlyPoint[],
  outcomePoints: MonthlyPoint[],
  asofIndex: number,
  scaleYears: TrapScale,
): Analog[] {
  const current = stateAt(statePoints, asofIndex);
  if (!current) return [];

  const asofDate = statePoints[asofIndex].date;
  const minDate = addYears(asofDate, -scaleYears);
  const matureCutoff = addYears(asofDate, -FLOOR_HORIZON_YEARS);
  const maxIndex = statePoints.findIndex((p) => p.date > matureCutoff);
  const upperExclusive = maxIndex < 0 ? statePoints.length : maxIndex;

  const candidates: Analog[] = [];
  for (let i = 36; i < upperExclusive; i += ANALOG_STRIDE_MONTHS) {
    const p = statePoints[i];
    if (p.date < minDate || p.date >= matureCutoff) continue;
    const state = stateAt(statePoints, i);
    const outcomeIndex = outcomeIndexByMonth(outcomePoints, p.date);
    const path = outcomeIndex >= 0 ? pathFrom(outcomePoints, outcomeIndex) : null;
    if (!state || !path) continue;
    const distance = featureDistance(current, state);
    const weight = Math.exp(-0.5 * distance * distance);
    candidates.push({ date: p.date, distance, weight, terminal: path[path.length - 1], path });
  }

  candidates.sort((a, b) => a.distance - b.distance);
  return candidates.slice(0, MAX_ANALOGS);
}

export function recommendForScale(
  statePoints: MonthlyPoint[],
  outcomePoints: MonthlyPoint[],
  asofIndex: number,
  scaleYears: TrapScale,
): ChannelScaleSignal {
  const asof = statePoints[asofIndex]?.date ?? "";
  const analogs = buildAnalogs(statePoints, outcomePoints, asofIndex, scaleYears);
  const usable = analogs.filter((a) => a.weight > 0.001);
  const effectiveN = usable.length / 4;
  if (usable.length < MIN_ANALOGS) {
    return {
      channel: "",
      layer: "OBSERVED",
      scaleYears,
      asof,
      target: null,
      floorProfile: null,
      responseProfile: null,
      riskBaselineProfile: null,
      forwardPathProfile: null,
      nearestAnalogDistance: null,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: usable.length,
      effectiveN,
      status: "INSUFFICIENT_HISTORY",
      creditMaxDrawdowns: null,
    };
  }

  const paths = usable.map((x) => x.path);
  const profile = floorProfile(paths);
  const responseProfile = deploymentResponseProfile(paths);
  const riskBaselineProfile = buildRiskBaselineProfile(paths);
  const forwardPathProfile = buildForwardPathProfile(paths);
  const target = floorTarget(paths);
  const scored = objective(paths, target);

  return {
    channel: "",
    layer: "OBSERVED",
    scaleYears,
    asof,
    target,
    floorProfile: profile,
    responseProfile,
    riskBaselineProfile,
    forwardPathProfile,
    nearestAnalogDistance: usable[0]?.distance ?? null,
    q05: scored.q05,
    pNonLoss: scored.pNonLoss,
    mean: scored.mean,
    nAnalogs: usable.length,
    effectiveN,
    status: "OK",
    creditMaxDrawdowns: paths.map((path) => equityStats(path).maxDd),
  };
}

function responseSlope(profile: DeploymentResponseProfile, i: number) {
  const a = profile.q05Terminal[i];
  const b = profile.q05Terminal[i + 1];
  const da = profile.deploymentFractions[i];
  const db = profile.deploymentFractions[i + 1];
  const width = db - da;
  return width > 0 ? (b - a) / width : 0;
}

export function overallMutualChaseState(topologies: MutualChaseTopology[]): DivergenceState {
  const usable = topologies.filter((x) => x.state !== "THIN");
  if (usable.length === 0) return "THIN";
  if (usable.some((x) => x.state === "DIVERGENT")) return "DIVERGENT";
  if (usable.some((x) => x.state === "TENSION")) return "TENSION";
  return "CONVERGENT";
}

export function mutualChaseTopology(
  profiles: Array<{ scaleYears: TrapScale; profile: DeploymentResponseProfile }>,
): MutualChaseTopology {
  if (profiles.length < 2) {
    return {
      state: "THIN",
      localDirections: [],
      leaderScaleBySegment: [],
      leaderChanges: 0,
      pairwiseCurveCrossings: 0,
    };
  }

  const segments = Math.min(
    ...profiles.map((x) => x.profile.q05Terminal.length - 1),
  );
  const leaderScaleBySegment: Array<TrapScale | null> = [];
  const localDirections: Array<"FORWARD" | "BACKWARD" | "FLAT" | "MIXED"> = [];

  for (let i = 0; i < segments; i++) {
    const slopes = profiles.map((x) => ({
      scaleYears: x.scaleYears,
      slope: responseSlope(x.profile, i),
    }));
    const positive = slopes.some((x) => x.slope > 1e-12);
    const negative = slopes.some((x) => x.slope < -1e-12);

    if (positive && negative) localDirections.push("MIXED");
    else if (positive) localDirections.push("FORWARD");
    else if (negative) localDirections.push("BACKWARD");
    else localDirections.push("FLAT");

    const leader = slopes
      .filter((x) => Math.abs(x.slope) > 1e-12)
      .sort((a, b) => Math.abs(b.slope) - Math.abs(a.slope))[0];
    leaderScaleBySegment.push(leader?.scaleYears ?? null);
  }

  let leaderChanges = 0;
  for (let i = 1; i < leaderScaleBySegment.length; i++) {
    const a = leaderScaleBySegment[i - 1];
    const b = leaderScaleBySegment[i];
    if (a != null && b != null && a !== b) leaderChanges++;
  }

  let pairwiseCurveCrossings = 0;
  for (let a = 0; a < profiles.length; a++) {
    for (let b = a + 1; b < profiles.length; b++) {
      const left = profiles[a].profile.q05Terminal;
      const right = profiles[b].profile.q05Terminal;
      let lastSign = 0;
      for (let i = 0; i < Math.min(left.length, right.length); i++) {
        const d = left[i] - right[i];
        const sign = d > 1e-10 ? 1 : d < -1e-10 ? -1 : 0;
        if (sign !== 0 && lastSign !== 0 && sign !== lastSign) pairwiseCurveCrossings++;
        if (sign !== 0) lastSign = sign;
      }
    }
  }

  const hasMixedDirection = localDirections.includes("MIXED");
  const hasDirectionalDisagreement = leaderChanges > 0 || pairwiseCurveCrossings > 0;
  const state = hasMixedDirection
    ? "DIVERGENT"
    : hasDirectionalDisagreement
      ? "TENSION"
      : "CONVERGENT";

  return {
    state,
    localDirections,
    leaderScaleBySegment,
    leaderChanges,
    pairwiseCurveCrossings,
  };
}

function robustConsensus(targets: number[]) {
  if (!targets.length) return { center: null, agreement: 0 };
  const center = median(targets) ?? 0;
  // MAD is 0 when a majority sits on the median, so one far scale is invisible.
  // Cross-scale authority uses the farthest scale: an outlier must not pull.
  const dispersion = Math.max(mad(targets, center), ...targets.map((x) => Math.abs(x - center)));
  const agreement = 1 - clamp(dispersion / AGREEMENT_MAD_SCALE);
  return { center, agreement };
}

export function divergenceState(scaleCount: number, agreement: number): DivergenceState {
  if (scaleCount < 2) return "THIN";
  if (agreement >= TENSION_AGREEMENT) return "CONVERGENT";
  if (agreement >= DIVERGENT_AGREEMENT) return "TENSION";
  return "DIVERGENT";
}

function stateAuthority(state: DivergenceState, agreement: number) {
  if (state === "CONVERGENT") return agreement;
  if (state === "TENSION") return agreement * 0.5;
  return 0;
}

export function couple(
  asof: string,
  elapsedMonths: number,
  signals: ChannelScaleSignal[],
): CoupledSignal {
  const clockTarget = clamp(elapsedMonths / FLOOR_HORIZON_MONTHS);
  const perScale = TRAP_SCALES_YEARS.map((scaleYears) => {
    const scaleSignals = signals.filter(
      (s) => s.scaleYears === scaleYears && s.status === "OK" && s.target != null,
    );
    const xs = scaleSignals.map((s) => s.target as number);
    const c = robustConsensus(xs);
    const responseProfiles = scaleSignals
      .map((s) => s.responseProfile)
      .filter(Boolean) as DeploymentResponseProfile[];
    const responseProfile =
      responseProfiles.length > 0
        ? {
            deploymentFractions: responseProfiles[0].deploymentFractions,
            q05Terminal: responseProfiles[0].deploymentFractions.map((_, i) =>
              median(responseProfiles.map((p) => p.q05Terminal[i])) ?? 0
            ),
            pNonLoss: responseProfiles[0].deploymentFractions.map((_, i) =>
              median(responseProfiles.map((p) => p.pNonLoss[i])) ?? 0
            ),
            meanTerminal: responseProfiles[0].deploymentFractions.map((_, i) =>
              median(responseProfiles.map((p) => p.meanTerminal[i])) ?? 0
            ),
          }
        : null;

    const riskProfiles = scaleSignals
      .map((s) => s.riskBaselineProfile)
      .filter(Boolean) as RiskBaselineProfile[];
    const riskBaselineProfile =
      riskProfiles.length > 0
        ? {
            deploymentFractions: riskProfiles[0].deploymentFractions,
            garMedian: riskProfiles[0].deploymentFractions.map((_, i) =>
              median(riskProfiles.map((p) => p.garMedian[i])) ?? 0
            ),
            garQ05: riskProfiles[0].deploymentFractions.map((_, i) =>
              median(riskProfiles.map((p) => p.garQ05[i])) ?? 0
            ),
            garQ95: riskProfiles[0].deploymentFractions.map((_, i) =>
              median(riskProfiles.map((p) => p.garQ95[i])) ?? 0
            ),
            maxDdMedian: riskProfiles[0].deploymentFractions.map((_, i) =>
              median(riskProfiles.map((p) => p.maxDdMedian[i])) ?? 0
            ),
            maxDdQ05: riskProfiles[0].deploymentFractions.map((_, i) =>
              median(riskProfiles.map((p) => p.maxDdQ05[i])) ?? 0
            ),
            maxDdQ95: riskProfiles[0].deploymentFractions.map((_, i) =>
              median(riskProfiles.map((p) => p.maxDdQ95[i])) ?? 0
            ),
          }
        : null;

    const forwardProfiles = scaleSignals
      .map((s) => s.forwardPathProfile)
      .filter(Boolean) as ForwardPathProfile[];
    const forwardPathProfile =
      forwardProfiles.length > 0
        ? {
            months: forwardProfiles[0].months,
            median: forwardProfiles[0].months.map((_, i) =>
              median(forwardProfiles.map((p) => p.median[i])) ?? 1
            ),
            q05: forwardProfiles[0].months.map((_, i) =>
              median(forwardProfiles.map((p) => p.q05[i])) ?? 1
            ),
            q95: forwardProfiles[0].months.map((_, i) =>
              median(forwardProfiles.map((p) => p.q95[i])) ?? 1
            ),
          }
        : null;

    const nearestDistances = scaleSignals
      .map((s) => s.nearestAnalogDistance)
      .filter((x): x is number => Number.isFinite(x));
    return {
      scaleYears,
      target: c.center,
      agreement: c.agreement,
      nSignals: xs.length,
      responseProfile,
      riskBaselineProfile,
      forwardPathProfile,
      nearestAnalogDistance: nearestDistances.length ? median(nearestDistances) : null,
    };
  }).filter((x) => x.nSignals > 0);

  const scaleTargets = perScale
    .filter((x) => x.target != null)
    .map((x) => x.target as number);
  const finalConsensus = robustConsensus(scaleTargets);

  // The trap is only allowed to pull capital forward when at least two
  // independent historical scales agree. One available scale is descriptive,
  // not a consensus signal, so authority returns to the clock.
  const divergence = divergenceState(scaleTargets.length, finalConsensus.agreement);
  const signalAuthority = stateAuthority(divergence, finalConsensus.agreement);
  const coupledTarget =
    finalConsensus.center == null
      ? clockTarget
      : clamp(clockTarget + signalAuthority * (finalConsensus.center - clockTarget));

  // QQQ is the canonical observed outcome/audit channel. Mutual-chase
  // shared state is driven only by independent proxy-price channels.
  const mutualChase = [...new Set(
    signals.filter((s) => s.layer === "PROXY_PRICE").map((s) => s.channel)
  )].map((channel) => {
    const profiles = TRAP_SCALES_YEARS
      .map((scaleYears) => {
        const signal = signals.find(
          (s) =>
            s.channel === channel &&
            s.scaleYears === scaleYears &&
            s.status === "OK" &&
            s.responseProfile != null,
        );
        return signal?.responseProfile
          ? { scaleYears, profile: signal.responseProfile }
          : null;
      })
      .filter(Boolean) as Array<{
        scaleYears: TrapScale;
        profile: DeploymentResponseProfile;
      }>;

    return {
      channel,
      topology: mutualChaseTopology(profiles),
    };
  });

  return {
    asof,
    clockTarget,
    divergenceState: divergence,
    signals,
    perScale,
    robustTarget: finalConsensus.center,
    agreement: signalAuthority,
    coupledTarget,
    mutualChase,
  };
}

function equityStats(curve: number[]) {
  let peak = 1;
  let maxDd = 0;
  let minEquity = Infinity;
  for (const e of curve) {
    peak = Math.max(peak, e);
    minEquity = Math.min(minEquity, e);
    maxDd = Math.min(maxDd, e / peak - 1);
  }
  return { maxDd, minEquity };
}

function indexAtOrBefore(points: MonthlyPoint[], date: string) {
  let lo = 0;
  let hi = points.length - 1;
  let best = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (points[mid].date <= date) {
      best = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return best;
}

export function buildSignalPanel(channels: Channel[], targetDates: string[]) {
  const panel = new Map<string, CoupledSignal>();

  for (const asof of targetDates) {
    const signals: ChannelScaleSignal[] = [];

    for (const channel of channels) {
      const idx = indexAtOrBefore(channel.points, asof);
      if (idx < 0) continue;
      for (const scaleYears of TRAP_SCALES_YEARS) {
        const outcomePoints =
          channels.find((candidate) => candidate.id === "QQQ")?.points ?? channel.points;
        const s = recommendForScale(channel.points, outcomePoints, idx, scaleYears);
        s.channel = channel.id;
        s.layer = channel.layer;
        signals.push(s);
      }
    }

    panel.set(asof, couple(asof, 0, signals));
  }

  return panel;
}

export function adaptiveCreditConfidence(
  signal: CoupledSignal | undefined,
  deployed: number,
  surplus: number,
): number {
  if (!signal || deployed <= 1e-12 || surplus <= 1e-12) return 0;

  if (
    signal.divergenceState === "DIVERGENT" ||
    signal.divergenceState === "THIN"
  ) {
    return 0;
  }

  // Current surplus is the loss budget available to the currently deployed
  // QQQ exposure. A historical path survives when its observed 10Y MaxDD
  // would not consume that entire surplus budget.
  const tolerablePortfolioDrawdown = surplus / deployed;
  const scaleSurvival: number[] = [];

  for (const scaleYears of TRAP_SCALES_YEARS) {
    const channelSignals = signal.signals.filter(
      (x) =>
        x.scaleYears === scaleYears &&
        x.status === "OK" &&
        Array.isArray(x.creditMaxDrawdowns) &&
        x.creditMaxDrawdowns.length >= MIN_ANALOGS,
    );

    const channelRates = channelSignals
      .map((x) => {
        const samples = x.creditMaxDrawdowns ?? [];
        const survived = samples.filter(
          (drawdown) => drawdown >= -tolerablePortfolioDrawdown,
        ).length;
        return samples.length ? survived / samples.length : null;
      })
      .filter((x): x is number => x != null);

    if (channelRates.length) {
      // Median across alternate channel views prevents repeated QQQ outcomes
      // from being counted as independent evidence.
      scaleSurvival.push(median(channelRates) ?? 0);
    }
  }

  // Require at least two historical scales before credit can have authority.
  if (scaleSurvival.length < 2) return 0;

  const q = median(scaleSurvival) ?? 0;
  return q >= CREDIT_MIN_SURVIVAL ? q : 0;
}

export function replayFundingPlan(
  qqq: MonthlyPoint[],
  panel: Map<string, CoupledSignal>,
  startIndex: number,
  horizonMonths = FLOOR_HORIZON_MONTHS,
  mode: FundingPlanMode = "ADAPTIVE_FUNDED",
  plannedPrincipal = 1,
  initialFundingFraction = DEFAULT_INITIAL_FUNDING_FRACTION,
  withdrawalMode: ProfitWithdrawalMode = "NONE",
  withdrawalSchedule: Map<string, number> = new Map(),
): FundingReplayResult | null {
  const endIndex = startIndex + horizonMonths;
  if (endIndex >= qqq.length) return null;
  if (!(plannedPrincipal > 0) || !Number.isFinite(plannedPrincipal)) {
    throw new Error("plannedPrincipal must be a positive finite number");
  }
  if (
    !(initialFundingFraction > 0) ||
    initialFundingFraction > 1 ||
    !Number.isFinite(initialFundingFraction)
  ) {
    throw new Error("initialFundingFraction must be in (0, 1]");
  }

  let externalRemaining = plannedPrincipal;
  let cumulativeContributed = 0;
  let accountCash = 0;
  const lots: { amount: number; entry: number }[] = [];
  const path: FundingPathPoint[] = [];
  const curve: number[] = [0];
  let nav = 0;
  let cumulativeWithdrawn = 0;

  if (
    withdrawalMode === "SCHEDULED" &&
    [...withdrawalSchedule.values()].some(
      (x) => !Number.isFinite(x) || x < 0,
    )
  ) {
    throw new Error("scheduled withdrawals must be finite and non-negative");
  }

  for (let j = 0; j < horizonMonths; j++) {
    const i = startIndex + j;
    const date = qqq[i].date;
    const sig = panel.get(date);

    // Funding decision timing: month j may only use the prior month's close.
    // Month 0 has no prior observation, so it starts with zero account NAV.
    const decisionPx = j === 0 ? null : qqq[i - 1].value;
    nav =
      decisionPx == null
        ? accountCash
        : accountCash +
          lots.reduce(
            (sum, lot) => sum + lot.amount * (decisionPx / lot.entry),
            0,
          );

    const investedBefore = cumulativeContributed;
    const surplus = Math.max(0, nav - cumulativeContributed);
    const creditConfidence =
      mode === "ADAPTIVE_FUNDED"
        ? adaptiveCreditConfidence(sig, investedBefore, surplus)
        : 0;

    // Credit substitutes for future external contributions. It never becomes
    // cash inside the account and is recalculated every month, so it can vanish.
    const fundingCredit =
      mode === "ADAPTIVE_FUNDED"
        ? Math.min(surplus, externalRemaining) * creditConfidence
        : 0;
    const clockTargetFraction =
      horizonMonths <= 1
        ? 1
        : initialFundingFraction +
          ((1 - initialFundingFraction) * j) / (horizonMonths - 1);
    const clockTarget = clamp(clockTargetFraction);
    const clockTargetAmount = plannedPrincipal * clockTarget;
    const fundingTarget =
      mode === "ADAPTIVE_FUNDED"
        ? Math.max(0, clockTargetAmount - fundingCredit)
        : clockTargetAmount;

    const contribution = Math.min(
      externalRemaining,
      Math.max(0, fundingTarget - cumulativeContributed),
    );

    if (contribution > 1e-12) {
      lots.push({ amount: contribution, entry: qqq[i].value });
      cumulativeContributed += contribution;
      externalRemaining -= contribution;
    }

    nav =
      accountCash +
      lots.reduce((sum, lot) => sum + lot.amount * (qqq[i].value / lot.entry), 0);

    const navBeforeWithdrawal = nav;
    const withdrawalEligibleSurplus = Math.max(
      0,
      navBeforeWithdrawal - cumulativeContributed,
    );
    const scheduledWithdrawal = withdrawalSchedule.get(date) ?? 0;
    const withdrawalRequested =
      withdrawalMode === "SWEEP_ELIGIBLE_SURPLUS"
        ? withdrawalEligibleSurplus
        : withdrawalMode === "SCHEDULED"
          ? scheduledWithdrawal
          : 0;
    const withdrawalExecuted = Math.min(
      withdrawalEligibleSurplus,
      Math.max(0, withdrawalRequested),
    );

    if (withdrawalExecuted > 1e-12 && navBeforeWithdrawal > 1e-12) {
      const cashWithdrawal = Math.min(accountCash, withdrawalExecuted);
      accountCash -= cashWithdrawal;
      const remaining = withdrawalExecuted - cashWithdrawal;
      if (remaining > 1e-12) {
        const scale = Math.max(
          0,
          (navBeforeWithdrawal - withdrawalExecuted) /
            Math.max(1e-12, navBeforeWithdrawal - cashWithdrawal),
        );
        for (const lot of lots) lot.amount *= scale;
      }
      nav = accountCash +
        lots.reduce(
          (sum, lot) => sum + lot.amount * (qqq[i].value / lot.entry),
          0,
        );
      cumulativeWithdrawn += withdrawalExecuted;
    }

    const postWithdrawalSurplus = Math.max(
      0,
      nav - cumulativeContributed,
    );
    const closeCreditConfidence =
      mode === "ADAPTIVE_FUNDED"
        ? adaptiveCreditConfidence(
            sig,
            cumulativeContributed,
            postWithdrawalSurplus,
          )
        : 0;
    const nextDecisionCreditBeforeWithdrawal =
      mode === "ADAPTIVE_FUNDED"
        ? Math.min(
            withdrawalEligibleSurplus,
            externalRemaining,
          ) * closeCreditConfidence
        : 0;
    const nextDecisionCreditAfterWithdrawal =
      mode === "ADAPTIVE_FUNDED"
        ? Math.min(postWithdrawalSurplus, externalRemaining) *
          closeCreditConfidence
        : 0;

    path.push({
      date,
      contribution,
      cumulativeContributed,
      remainingExternalCapital: externalRemaining,
      plannedPrincipal,
      initialFundingFraction,
      invested: lots.reduce((sum, lot) => sum + lot.amount, 0),
      accountCash,
      navBeforeWithdrawal,
      nav,
      surplus: postWithdrawalSurplus,
      fundingCredit,
      creditConfidence,
      fundingTarget,
      clockTarget,
      withdrawalEligibleSurplus,
      withdrawalRequested,
      withdrawalExecuted,
      cumulativeWithdrawn,
      nextDecisionCreditBeforeWithdrawal,
      nextDecisionCreditAfterWithdrawal,
      creditCancelledByWithdrawal: Math.max(
        0,
        nextDecisionCreditBeforeWithdrawal -
          nextDecisionCreditAfterWithdrawal,
      ),
      divergenceState: sig?.divergenceState ?? "THIN",
    });

    curve.push(nav);
  }

  const finalPx = qqq[endIndex].value;
  nav =
    accountCash +
    lots.reduce((sum, lot) => sum + lot.amount * (finalPx / lot.entry), 0);
  curve.push(nav);

  return {
    startDate: qqq[startIndex].date,
    endDate: qqq[endIndex].date,
    horizonMonths,
    terminalWealth: nav,
    maxDrawdown: equityStats(curve).maxDd,
    totalContributed: cumulativeContributed,
    totalWithdrawn: cumulativeWithdrawn,
    plannedPrincipal,
    initialFundingFraction,
    maxContributionReduction: Math.max(
      0,
      ...path.map(
        (point) =>
          plannedPrincipal * point.clockTarget - point.cumulativeContributed,
      ),
    ),
    totalContributionReduction: plannedPrincipal - cumulativeContributed,
    netEconomicWealth:
      nav + cumulativeWithdrawn - cumulativeContributed,
    path,
  };
}

export function replayOne(
  qqq: MonthlyPoint[],
  panel: Map<string, CoupledSignal>,
  startIndex: number,
  mode: ReplayMode = "COUPLED",
): ReplayResult | null {
  const endIndex = startIndex + FLOOR_HORIZON_MONTHS;
  if (endIndex >= qqq.length) return null;

  let cash = 1;
  let equity = 1;
  let peak = 1;
  let totalInvested = 0;
  let forcedCatchUpMonths = 0;
  const lots: { amount: number; entry: number }[] = [];
  const trades: ReplayTrade[] = [];
  const path: ReplayPathPoint[] = [];
  const curve: number[] = [1];

  for (let j = 0; j < FLOOR_HORIZON_MONTHS; j++) {
    const i = startIndex + j;
    const date = qqq[i].date;
    const sig = panel.get(date);
    const monthsLeft = FLOOR_HORIZON_MONTHS - j;
    const mandatoryAdd = monthsLeft > 0 ? cash / monthsLeft : cash;
    const clockTarget = clamp((j + 1) / FLOOR_HORIZON_MONTHS);

    // Missing/insufficient history never disables the deadline clock.
    const robustTarget = sig?.robustTarget ?? null;
    const signalAgreement = sig?.agreement ?? 0;
    const divergence = sig?.divergenceState ?? "THIN";
    const topologies = sig?.mutualChase.map((x) => x.topology) ?? [];
    const mutualState = overallMutualChaseState(topologies);
    const mutualLeaderChanges = topologies.reduce((sum, x) => sum + x.leaderChanges, 0);
    const mutualCurveCrossings = topologies.reduce((sum, x) => sum + x.pairwiseCurveCrossings, 0);
    const lagTarget =
      robustTarget == null
        ? clockTarget
        : clamp(clockTarget + signalAgreement * (robustTarget - clockTarget));

    const deployedBefore = 1 - cash;
    // B=1 in the normalized research account, so NAV-1 equals only the
    // mark-to-market gain on the already deployed lots.
    const surplus = Math.max(0, equity - 1);

    // ADAPTIVE_CREDIT_ONLY is intentionally separate from the coupled timing
    // controller: it never moves money ahead because of a signal target.
    const creditConfidence =
      mode === "ADAPTIVE_CREDIT_ONLY"
        ? adaptiveCreditConfidence(sig, deployedBefore, surplus)
        : 0;
    const creditCapacity = Math.max(0, cash);
    const creditAmount =
      mode === "ADAPTIVE_CREDIT_ONLY"
        ? Math.min(surplus, creditCapacity) * creditConfidence
        : 0;

    // Credit is a reversible reduction in cumulative deployment need.
    // If NAV falls back, credit falls back too and the clock automatically
    // catches up; no previously-deployed amount is undone.
    const effectiveTarget =
      mode === "ADAPTIVE_CREDIT_ONLY"
        ? Math.max(0, clockTarget - creditAmount)
        : lagTarget;

    const effectiveMandatoryAdd =
      mode === "ADAPTIVE_CREDIT_ONLY"
        ? Math.max(0, effectiveTarget - deployedBefore)
        : mandatoryAdd;
    const desiredAdd =
      mode === "ADAPTIVE_CREDIT_ONLY"
        ? effectiveMandatoryAdd
        : Math.max(0, lagTarget - deployedBefore);
    const action =
      mode === "ADAPTIVE_CREDIT_ONLY"
        ? Math.min(cash, effectiveMandatoryAdd)
        : Math.min(cash, Math.max(mandatoryAdd, desiredAdd));

    if (action > 1e-12) {
      if (action <= mandatoryAdd + 1e-9 && desiredAdd < mandatoryAdd - 1e-9) {
        forcedCatchUpMonths++;
      }

      const entry = qqq[i].value;
      lots.push({ amount: action, entry });
      cash -= action;
      totalInvested += action;

      trades.push({
        date,
        action,
        deployed: 1 - cash,
        cash,
        coupledTarget: lagTarget,
        clockTarget,
        agreement: signalAgreement,
        divergenceState: divergence,
        mutualChaseState: mutualState,
        mutualLeaderChanges,
        mutualCurveCrossings,
        creditAmount,
        creditConfidence,
        effectiveTarget,
      });
    }

    const currentPx = qqq[i].value;
    equity =
      cash +
      lots.reduce((s, lot) => s + lot.amount * (currentPx / lot.entry), 0);
    peak = Math.max(peak, equity);
    curve.push(equity);

    path.push({
      date,
      action,
      deployed: 1 - cash,
      cash,
      coupledTarget: lagTarget,
      clockTarget,
      agreement: signalAgreement,
      divergenceState: divergence,
      mutualChaseState: mutualState,
      mutualLeaderChanges,
      mutualCurveCrossings,
      creditAmount,
      creditConfidence,
      effectiveTarget,
    });
  }

  const finalPx = qqq[endIndex].value;
  equity =
    cash +
    lots.reduce((s, lot) => s + lot.amount * (finalPx / lot.entry), 0);
  peak = Math.max(peak, equity);
  curve.push(equity);
  const stats = equityStats(curve);

  const halfwayTarget = FLOOR_HORIZON_MONTHS / 2;
  const year8Target = FLOOR_HORIZON_MONTHS * 0.8;
  const deployedAtHalfway =
    trades.filter((t) => monthsBetween(qqq[startIndex].date, t.date) <= halfwayTarget).at(-1)?.deployed ?? 0;
  const deployedAtYear8 =
    trades.filter((t) => monthsBetween(qqq[startIndex].date, t.date) <= year8Target).at(-1)?.deployed ?? 0;

  return {
    startDate: qqq[startIndex].date,
    endDate: qqq[endIndex].date,
    terminalWealth: equity,
    terminalReturn: equity - 1,
    maxDrawdown: stats.maxDd,
    minEquity: stats.minEquity,
    deployedAtHalfway,
    deployedAtYear8,
    forcedCatchUpMonths,
    totalInvested,
    trades,
    path,
  };
}


export type StatePathSummary = {
  state: DivergenceState;
  observations: number;
  shareOfObservedMonths: number;
  meanDeployed: number;
  medianDeployed: number;
  meanClockTarget: number;
  meanAheadOfClock: number;
  medianAheadOfClock: number;
  q05AheadOfClock: number;
  q95AheadOfClock: number;
  meanAbsoluteAhead: number;
  meanCoupledTargetDelta: number;
  episodes: number;
  meanEpisodeMonths: number;
  medianEpisodeMonths: number;
  maxEpisodeMonths: number;
  meanEpisodePeakAhead: number;
  meanEpisodeEndAhead: number;
};

type StateEpisode = {
  state: DivergenceState;
  months: number;
  peakAhead: number;
  endAhead: number;
};

function episodesFromReplay(
  result: ReplayResult,
  stateField: "divergenceState" | "mutualChaseState" = "divergenceState",
): StateEpisode[] {
  const episodes: StateEpisode[] = [];
  let currentState: DivergenceState | null = null;
  let months = 0;
  let peakAhead = 0;
  let endAhead = 0;

  for (const point of result.path) {
    const ahead = point.deployed - point.clockTarget;
    const state = point[stateField];

    if (currentState !== state) {
      if (currentState != null) {
        episodes.push({
          state: currentState,
          months,
          peakAhead,
          endAhead,
        });
      }
      currentState = state;
      months = 0;
      peakAhead = ahead;
      endAhead = ahead;
    }

    months++;
    peakAhead = Math.max(peakAhead, ahead);
    endAhead = ahead;
  }

  if (currentState != null) {
    episodes.push({
      state: currentState,
      months,
      peakAhead,
      endAhead,
    });
  }

  return episodes;
}

export function summarizeStatePath(
  results: ReplayResult[],
  stateField: "divergenceState" | "mutualChaseState" = "divergenceState",
) {
  const rows: Record<DivergenceState, {
    ahead: number[];
    deployed: number[];
    clock: number[];
    coupledDelta: number[];
    episodes: StateEpisode[];
  }> = {
    CONVERGENT: { ahead: [], deployed: [], clock: [], coupledDelta: [], episodes: [] },
    TENSION: { ahead: [], deployed: [], clock: [], coupledDelta: [], episodes: [] },
    DIVERGENT: { ahead: [], deployed: [], clock: [], coupledDelta: [], episodes: [] },
    THIN: { ahead: [], deployed: [], clock: [], coupledDelta: [], episodes: [] },
  };

  for (const result of results) {
    for (const point of result.path) {
      const row = rows[point[stateField]];
      const ahead = point.deployed - point.clockTarget;
      row.ahead.push(ahead);
      row.deployed.push(point.deployed);
      row.clock.push(point.clockTarget);
      row.coupledDelta.push(point.coupledTarget - point.clockTarget);
    }
    for (const ep of episodesFromReplay(result, stateField)) rows[ep.state].episodes.push(ep);
  }

  const total = Object.values(rows).reduce((n, row) => n + row.ahead.length, 0);

  return (Object.keys(rows) as DivergenceState[]).map((state): StatePathSummary => {
    const row = rows[state];
    const episodes = row.episodes;
    const episodeMonths = episodes.map((x) => x.months);
    const peakAhead = episodes.map((x) => x.peakAhead);
    const endAhead = episodes.map((x) => x.endAhead);
    return {
      state,
      observations: row.ahead.length,
      shareOfObservedMonths: row.ahead.length / Math.max(1, total),
      meanDeployed: row.deployed.reduce((a, b) => a + b, 0) / Math.max(1, row.deployed.length),
      medianDeployed: median(row.deployed) ?? 0,
      meanClockTarget: row.clock.reduce((a, b) => a + b, 0) / Math.max(1, row.clock.length),
      meanAheadOfClock: row.ahead.reduce((a, b) => a + b, 0) / Math.max(1, row.ahead.length),
      medianAheadOfClock: median(row.ahead) ?? 0,
      q05AheadOfClock: quantile(row.ahead, 0.05) ?? 0,
      q95AheadOfClock: quantile(row.ahead, 0.95) ?? 0,
      meanAbsoluteAhead: row.ahead.reduce((a, b) => a + Math.abs(b), 0) / Math.max(1, row.ahead.length),
      meanCoupledTargetDelta: row.coupledDelta.reduce((a, b) => a + b, 0) / Math.max(1, row.coupledDelta.length),
      episodes: episodes.length,
      meanEpisodeMonths: episodeMonths.reduce((a, b) => a + b, 0) / Math.max(1, episodeMonths.length),
      medianEpisodeMonths: median(episodeMonths) ?? 0,
      maxEpisodeMonths: episodeMonths.length ? Math.max(...episodeMonths) : 0,
      meanEpisodePeakAhead: peakAhead.reduce((a, b) => a + b, 0) / Math.max(1, peakAhead.length),
      meanEpisodeEndAhead: endAhead.reduce((a, b) => a + b, 0) / Math.max(1, endAhead.length),
    };
  });
}

export function summarizeReplays(results: ReplayResult[]) {
  const ws = results.map((r) => r.terminalWealth);
  const nonLoss = ws.filter((x) => x >= 1).length / Math.max(1, ws.length);
  const worst = Math.min(...ws);
  const q05 = quantile(ws, 0.05) ?? 0;
  const q10 = quantile(ws, 0.10) ?? 0;
  const medianWealth = median(ws) ?? 0;
  const meanWealth = ws.reduce((a, b) => a + b, 0) / Math.max(1, ws.length);
  return {
    nReplays: results.length,
    nonLossRate: nonLoss,
    q05Terminal: q05,
    q10Terminal: q10,
    medianTerminal: medianWealth,
    meanTerminal: meanWealth,
    worstTerminal: worst,
    meanMaxDd: results.reduce((a, b) => a + b.maxDrawdown, 0) / Math.max(1, results.length),
    worstMaxDd: Math.min(...results.map((r) => r.maxDrawdown)),
    meanForcedCatchUpMonths:
      results.reduce((a, b) => a + b.forcedCatchUpMonths, 0) / Math.max(1, results.length),
    meanDeployedAtHalfway:
      results.reduce((a, b) => a + b.deployedAtHalfway, 0) / Math.max(1, results.length),
    meanDeployedAtYear8:
      results.reduce((a, b) => a + b.deployedAtYear8, 0) / Math.max(1, results.length),
    meanTotalInvested:
      results.reduce((a, b) => a + b.totalInvested, 0) / Math.max(1, results.length),
    medianTotalInvested: median(results.map((r) => r.totalInvested)) ?? 0,
    q05TotalInvested: quantile(results.map((r) => r.totalInvested), 0.05) ?? 0,
    meanUndeployedAtEnd:
      results.reduce((a, b) => a + (1 - b.totalInvested), 0) / Math.max(1, results.length),
  };
}
