import { universe } from "./bars.ts";

export const FLOOR_HORIZON_YEARS = 10;
export const FLOOR_HORIZON_MONTHS = FLOOR_HORIZON_YEARS * 12;
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

export type ChannelScaleSignal = {
  channel: string;
  layer: Channel["layer"];
  scaleYears: TrapScale;
  asof: string;
  target: number | null;
  floorProfile: FloorProfile | null;
  q05: number | null;
  pNonLoss: number | null;
  mean: number | null;
  nAnalogs: number;
  effectiveN: number;
  status: "OK" | "INSUFFICIENT_HISTORY";
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
  }>;
  robustTarget: number | null;
  agreement: number;
  coupledTarget: number;
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
};

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

export function requiredFrontLoadFraction(path: number[], floor = 1) {
  const { zero, one } = terminalAtZeroAndOne(path);
  if (zero >= floor) return 0;
  if (one < floor) return 1;

  const slope = one - zero;
  if (slope <= 0) return 1;
  return clamp((floor - zero) / slope);
}

function objective(paths: number[], a: number) {
  const ws = paths.map((p) => terminalForDeployment(a, p));
  const q05 = quantile(ws, 0.05) ?? 0;
  const pNonLoss = ws.filter((w) => w >= 1).length / ws.length;
  const mean = ws.reduce((x, y) => x + y, 0) / ws.length;
  return { q05, pNonLoss, mean };
}

export function floorProfile(paths: number[]): FloorProfile {
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

function floorTarget(paths: number[]) {
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
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: usable.length,
      effectiveN,
      status: "INSUFFICIENT_HISTORY",
    };
  }

  const paths = usable.map((x) => x.path);
  const profile = floorProfile(paths);
  const target = floorTarget(paths);
  const scored = objective(paths, target);

  return {
    channel: "",
    layer: "OBSERVED",
    scaleYears,
    asof,
    target,
    floorProfile: profile,
    q05: scored.q05,
    pNonLoss: scored.pNonLoss,
    mean: scored.mean,
    nAnalogs: usable.length,
    effectiveN,
    status: "OK",
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
    const profiles = scaleSignals.map((s) => s.floorProfile).filter(Boolean) as FloorProfile[];
    const profile =
      profiles.length > 0
        ? {
            probabilities: profiles[0].probabilities,
            requiredFrontLoad: profiles[0].probabilities.map((_, i) =>
              median(profiles.map((p) => p.requiredFrontLoad[i])) ?? 0
            ),
            meanRequiredFrontLoad:
              profiles.reduce((sum, p) => sum + p.meanRequiredFrontLoad, 0) / profiles.length,
            maxRequiredFrontLoad: Math.max(...profiles.map((p) => p.maxRequiredFrontLoad)),
          }
        : null;
    return {
      scaleYears,
      target: c.center,
      agreement: c.agreement,
      nSignals: xs.length,
      profile,
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

  return {
    asof,
    clockTarget,
    divergenceState: divergence,
    signals,
    perScale,
    robustTarget: finalConsensus.center,
    agreement: signalAuthority,
    coupledTarget,
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

export function replayOne(
  qqq: MonthlyPoint[],
  panel: Map<string, CoupledSignal>,
  startIndex: number,
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
    const lagTarget =
      robustTarget == null
        ? clockTarget
        : clamp(clockTarget + signalAgreement * (robustTarget - clockTarget));
    const desiredAdd = Math.max(0, lagTarget - (1 - cash));
    const action = Math.min(cash, Math.max(mandatoryAdd, desiredAdd));

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

function episodesFromReplay(result: ReplayResult): StateEpisode[] {
  const episodes: StateEpisode[] = [];
  let currentState: DivergenceState | null = null;
  let months = 0;
  let peakAhead = 0;
  let endAhead = 0;

  for (const point of result.path) {
    const ahead = point.deployed - point.clockTarget;

    if (currentState !== point.divergenceState) {
      if (currentState != null) {
        episodes.push({
          state: currentState,
          months,
          peakAhead,
          endAhead,
        });
      }
      currentState = point.divergenceState;
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

export function summarizeStatePath(results: ReplayResult[]) {
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
      const row = rows[point.divergenceState];
      const ahead = point.deployed - point.clockTarget;
      row.ahead.push(ahead);
      row.deployed.push(point.deployed);
      row.clock.push(point.clockTarget);
      row.coupledDelta.push(point.coupledTarget - point.clockTarget);
    }
    for (const ep of episodesFromReplay(result)) rows[ep.state].episodes.push(ep);
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
  };
}
