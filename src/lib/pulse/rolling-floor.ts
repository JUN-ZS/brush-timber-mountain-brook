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

export type ChannelScaleSignal = {
  channel: string;
  layer: Channel["layer"];
  scaleYears: TrapScale;
  asof: string;
  target: number | null;
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
};

const ACTION_GRID = Array.from({ length: 21 }, (_, i) => i / 20);
const MIN_ANALOGS = 8;
const MAX_ANALOGS = 24;
const ANALOG_STRIDE_MONTHS = 3;
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

function objective(paths: number[], a: number) {
  const ws = paths.map((p) => terminalForDeployment(a, p));
  const q05 = quantile(ws, 0.05) ?? 0;
  const pNonLoss = ws.filter((w) => w >= 1).length / ws.length;
  const mean = ws.reduce((x, y) => x + y, 0) / ws.length;
  // Terminal floor dominates. P(non-loss) and mean break ties only.
  return { q05, pNonLoss, mean };
}

function buildAnalogs(
  points: MonthlyPoint[],
  asofIndex: number,
  scaleYears: TrapScale,
): Analog[] {
  const current = stateAt(points, asofIndex);
  if (!current) return [];

  const asofDate = points[asofIndex].date;
  const minDate = addYears(asofDate, -scaleYears);
  const matureCutoff = addYears(asofDate, -FLOOR_HORIZON_YEARS);
  const maxIndex = points.findIndex((p) => p.date > matureCutoff);
  const upperExclusive = maxIndex < 0 ? points.length : maxIndex;

  const candidates: Analog[] = [];
  for (let i = 36; i < upperExclusive; i += ANALOG_STRIDE_MONTHS) {
    const p = points[i];
    if (p.date < minDate || p.date >= matureCutoff) continue;
    const state = stateAt(points, i);
    const path = pathFrom(points, i);
    if (!state || !path) continue;
    const distance = featureDistance(current, state);
    const weight = Math.exp(-0.5 * distance * distance);
    candidates.push({ date: p.date, distance, weight, terminal: path[path.length - 1], path });
  }

  candidates.sort((a, b) => a.distance - b.distance);
  return candidates.slice(0, MAX_ANALOGS);
}

export function recommendForScale(
  points: MonthlyPoint[],
  asofIndex: number,
  scaleYears: TrapScale,
): ChannelScaleSignal {
  const asof = points[asofIndex]?.date ?? "";
  const analogs = buildAnalogs(points, asofIndex, scaleYears);
  const usable = analogs.filter((a) => a.weight > 0.001);
  const effectiveN = usable.length / 4;
  if (usable.length < MIN_ANALOGS) {
    return {
      channel: "",
      layer: "OBSERVED",
      scaleYears,
      asof,
      target: null,
      q05: null,
      pNonLoss: null,
      mean: null,
      nAnalogs: usable.length,
      effectiveN,
      status: "INSUFFICIENT_HISTORY",
    };
  }

  const scored = ACTION_GRID.map((a) => ({
    a,
    ...objective(usable.map((x) => x.path), a),
  }));

  scored.sort(
    (x, y) =>
      y.q05 - x.q05 ||
      y.pNonLoss - x.pNonLoss ||
      y.mean - x.mean ||
      x.a - y.a,
  );

  const best = scored[0];
  return {
    channel: "",
    layer: "OBSERVED",
    scaleYears,
    asof,
    target: best.a,
    q05: best.q05,
    pNonLoss: best.pNonLoss,
    mean: best.mean,
    nAnalogs: usable.length,
    effectiveN,
    status: "OK",
  };
}

function robustConsensus(targets: number[]) {
  if (!targets.length) return { center: null, agreement: 0 };
  const center = median(targets) ?? 0;
  const dispersion = mad(targets, center);
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
    const xs = signals
      .filter((s) => s.scaleYears === scaleYears && s.status === "OK" && s.target != null)
      .map((s) => s.target as number);
    const c = robustConsensus(xs);
    return {
      scaleYears,
      target: c.center,
      agreement: c.agreement,
      nSignals: xs.length,
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
        const s = recommendForScale(channel.points, idx, scaleYears);
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
  const curve: number[] = [1];

  for (let j = 0; j < FLOOR_HORIZON_MONTHS; j++) {
    const i = startIndex + j;
    const date = qqq[i].date;
    const sig = panel.get(date);
    if (!sig) continue;

    const monthsLeft = FLOOR_HORIZON_MONTHS - j;
    const mandatoryAdd = monthsLeft > 0 ? cash / monthsLeft : cash;
    const clockTarget = clamp((j + 1) / FLOOR_HORIZON_MONTHS);
    const lagTarget =
      sig.robustTarget == null
        ? clockTarget
        : clamp(clockTarget + sig.agreement * (sig.robustTarget - clockTarget));
    const desiredAdd = Math.max(0, lagTarget - (1 - cash));
    const action = Math.min(cash, Math.max(mandatoryAdd, desiredAdd));

    if (action <= 1e-12) continue;

    if (action <= mandatoryAdd + 1e-9 && desiredAdd < mandatoryAdd - 1e-9) {
      forcedCatchUpMonths++;
    }

    const entry = qqq[i].value;
    lots.push({ amount: action, entry });
    cash -= action;
    totalInvested += action;

    const currentPx = qqq[i].value;
    equity =
      cash +
      lots.reduce((s, lot) => s + lot.amount * (currentPx / lot.entry), 0);
    peak = Math.max(peak, equity);
    curve.push(equity);

    trades.push({
      date,
      action,
      deployed: 1 - cash,
      cash,
      coupledTarget: lagTarget,
      clockTarget,
      agreement: sig.agreement,
    });
  }

  const finalPx = qqq[endIndex].value;
  equity =
    cash +
    lots.reduce((s, lot) => s + lot.amount * (finalPx / lot.entry), 0);
  curve.push(equity);
  const stats = equityStats(curve);

  const half = trades.find((t) => monthsBetween(qqq[startIndex].date, t.date) >= 60);
  const year8 = trades.find((t) => monthsBetween(qqq[startIndex].date, t.date) >= 96);

  return {
    startDate: qqq[startIndex].date,
    endDate: qqq[endIndex].date,
    terminalWealth: equity,
    terminalReturn: equity - 1,
    maxDrawdown: stats.maxDd,
    minEquity: stats.minEquity,
    deployedAtHalfway: half?.deployed ?? 0,
    deployedAtYear8: year8?.deployed ?? 0,
    forcedCatchUpMonths,
    totalInvested,
    trades,
  };
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
