import { stateAt, type MonthlyPoint, type StateVector } from "./rolling-floor.ts";

export type LongScaleProvenance =
  | "OBSERVED_QQQ"
  | "SYNTHETIC_HISTORY"
  | "SYNTHETIC_FUTURE";

export type LongScalePoint = {
  date: string;
  value: number;
  provenance: LongScaleProvenance;
};

export type LongScaleFutureProfile = {
  months: number[];
  median: number[];
  q05: number[];
  q95: number[];
  analogCount: number;
  nearestDistance: number | null;
  horizonYears: number;
};

export type LongScaleProfile = {
  scaleYears: 50;
  asOf: string;
  observedStartDate: string | null;
  observedEndDate: string;
  syntheticHistoryStartDate: string | null;
  syntheticHistoryMonths: number;
  syntheticFutureMonths: number;
  points: LongScalePoint[];
  future: LongScaleFutureProfile | null;
  calibration: {
    proxySource: "NASDAQ100 + NASDAQCOM";
    proxyOverlapMonths: number;
    proxyBeta: number | null;
    qqqOverlapMonths: number;
    qqqBeta: number | null;
  };
};

function monthKey(date: string) {
  return date.slice(0, 7);
}

function addYears(date: string, years: number) {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCFullYear(d.getUTCFullYear() + years);
  return d.toISOString().slice(0, 10);
}

function median(xs: number[]) {
  if (!xs.length) return null;
  const a = [...xs].sort((x, y) => x - y);
  const i = Math.floor(a.length / 2);
  return a.length % 2 ? a[i] ?? null : ((a[i - 1] ?? 0) + (a[i] ?? 0)) / 2;
}

function quantile(xs: number[], p: number) {
  if (!xs.length) return null;
  const a = [...xs].sort((x, y) => x - y);
  const pos = Math.max(0, Math.min(a.length - 1, (a.length - 1) * p));
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  const t = pos - lo;
  return (a[lo] ?? 0) + ((a[hi] ?? a[lo] ?? 0) - (a[lo] ?? 0)) * t;
}

function logCalibration(source: MonthlyPoint[], target: MonthlyPoint[]) {
  const targetByMonth = new Map(target.map((p) => [monthKey(p.date), p.value]));
  const pairs = source
    .map((p) => {
      const t = targetByMonth.get(monthKey(p.date));
      return t != null && p.value > 0 && t > 0
        ? { x: Math.log(p.value), y: Math.log(t) }
        : null;
    })
    .filter((x): x is { x: number; y: number } => x != null);

  if (pairs.length < 24) {
    return { alpha: null, beta: null, overlapMonths: pairs.length };
  }

  const mx = pairs.reduce((s, p) => s + p.x, 0) / pairs.length;
  const my = pairs.reduce((s, p) => s + p.y, 0) / pairs.length;
  const variance = pairs.reduce((s, p) => s + (p.x - mx) ** 2, 0);
  const beta = variance > 1e-12
    ? pairs.reduce((s, p) => s + (p.x - mx) * (p.y - my), 0) / variance
    : 1;
  const alpha = median(pairs.map((p) => p.y - beta * p.x));
  return { alpha, beta, overlapMonths: pairs.length };
}

function calibrateValue(value: number, calibration: { alpha: number | null; beta: number | null }) {
  if (calibration.alpha == null || calibration.beta == null || !Number.isFinite(value) || value <= 0) {
    return null;
  }
  const result = Math.exp(calibration.alpha + calibration.beta * Math.log(value));
  return Number.isFinite(result) && result > 0 ? result : null;
}

function buildContinuousProxy(ndx: MonthlyPoint[], composite: MonthlyPoint[], startDate: string, asOf: string) {
  const ndxByMonth = new Map(ndx.map((p) => [monthKey(p.date), p.value]));
  const calibration = logCalibration(composite, ndx);
  const dates = new Set<string>();

  for (const p of composite) {
    if (p.date >= startDate && p.date <= asOf) dates.add(monthKey(p.date));
  }
  for (const p of ndx) {
    if (p.date >= startDate && p.date <= asOf) dates.add(monthKey(p.date));
  }

  return [...dates]
    .sort()
    .map((month) => {
      const compositeValue = composite.find((p) => monthKey(p.date) === month)?.value ?? null;
      const ndxValue = ndxByMonth.get(month) ?? null;
      if (ndxValue != null) {
        return { date: month + "-01", value: ndxValue };
      }
      const reconstructed = compositeValue == null ? null : calibrateValue(compositeValue, calibration);
      return reconstructed == null ? null : { date: month + "-01", value: reconstructed };
    })
    .filter((x): x is MonthlyPoint => x != null);
}

function distance(a: StateVector, b: StateVector) {
  const scales = [0.15, 0.30, 0.30, 0.20, 24];
  return Math.sqrt(
    [
      (a.dd12 - b.dd12) / scales[0],
      (a.dd36 - b.dd36) / scales[1],
      (a.mom12 - b.mom12) / scales[2],
      (a.vol6 - b.vol6) / scales[3],
      (a.ddDurationMonths - b.ddDurationMonths) / scales[4],
    ].reduce((sum, x) => sum + x * x, 0),
  );
}

function normalizedPath(points: MonthlyPoint[], index: number, horizonMonths: number) {
  const base = points[index]?.value;
  if (base == null || base <= 0 || index + horizonMonths >= points.length) return null;
  const out: number[] = [];
  for (let i = 0; i <= horizonMonths; i++) {
    const value = points[index + i]?.value;
    if (value == null || value <= 0) return null;
    out.push(value / base);
  }
  return out;
}

function buildFutureProfile(points: MonthlyPoint[], asOfIndex: number, horizonYears: number) {
  const horizonMonths = horizonYears * 12;
  const current = stateAt(points, asOfIndex);
  if (!current) return null;

  const minIndex = Math.max(36, asOfIndex - 50 * 12);
  const maxIndex = asOfIndex - horizonMonths;
  if (maxIndex <= minIndex) return null;

  const candidates: Array<{ distance: number; path: number[] }> = [];
  for (let i = minIndex; i <= maxIndex; i += 3) {
    const state = stateAt(points, i);
    const path = state ? normalizedPath(points, i, horizonMonths) : null;
    if (!state || !path) continue;
    const d = distance(current, state);
    candidates.push({ distance: d, path });
  }

  candidates.sort((a, b) => a.distance - b.distance);
  const usable = candidates
    .slice(0, 24)
    .filter((x) => Math.exp(-0.5 * x.distance * x.distance) > 0.001);

  if (!usable.length) return null;

  const months = Array.from({ length: horizonMonths + 1 }, (_, i) => i);
  return {
    months,
    median: months.map((i) => median(usable.map((x) => x.path[i] ?? 1)) ?? 1),
    q05: months.map((i) => quantile(usable.map((x) => x.path[i] ?? 1), 0.05) ?? 1),
    q95: months.map((i) => quantile(usable.map((x) => x.path[i] ?? 1), 0.95) ?? 1),
    analogCount: usable.length,
    nearestDistance: usable[0]?.distance ?? null,
    horizonYears,
  };
}

export function buildSyntheticLongScale(
  qqq: MonthlyPoint[],
  ndx: MonthlyPoint[],
  composite: MonthlyPoint[],
  asOf: string,
  historyYears = 50,
  futureYears = 20,
): LongScaleProfile | null {
  const qqqObserved = qqq
    .filter((p) => p.date <= asOf)
    .sort((a, b) => a.date.localeCompare(b.date));
  if (!qqqObserved.length || !ndx.length || !composite.length) return null;

  const observedStartDate = qqqObserved[0]?.date ?? null;
  const historyStartDate = addYears(asOf, -historyYears);
  const proxy = buildContinuousProxy(ndx, composite, historyStartDate, asOf);
  if (proxy.length < 36) return null;

  const proxyCalibration = logCalibration(composite, ndx);
  const qqqCalibration = logCalibration(proxy, qqqObserved);
  if (qqqCalibration.alpha == null || qqqCalibration.beta == null) return null;

  const observedByMonth = new Map(qqqObserved.map((p) => [monthKey(p.date), p.value]));
  const points: LongScalePoint[] = [];

  for (const p of proxy) {
    const observed = observedByMonth.get(monthKey(p.date));
    if (observed != null) {
      points.push({ date: p.date, value: observed, provenance: "OBSERVED_QQQ" });
      continue;
    }
    const synthetic = calibrateValue(p.value, qqqCalibration);
    if (synthetic != null) {
      points.push({ date: p.date, value: synthetic, provenance: "SYNTHETIC_HISTORY" });
    }
  }

  for (const p of qqqObserved) {
    if (!points.some((x) => monthKey(x.date) === monthKey(p.date))) {
      points.push({ date: p.date, value: p.value, provenance: "OBSERVED_QQQ" });
    }
  }

  points.sort((a, b) => a.date.localeCompare(b.date));

  const proxyAsOfIndex = proxy.reduce(
    (best, p, i) => (p.date <= asOf && p.date > (proxy[best]?.date ?? "") ? i : best),
    0,
  );
  const future = buildFutureProfile(proxy, proxyAsOfIndex, futureYears);

  const syntheticHistory = points.filter((p) => p.provenance === "SYNTHETIC_HISTORY");
  const futureMonths = future?.horizonYears != null ? future.horizonYears * 12 : 0;

  return {
    scaleYears: 50,
    asOf,
    observedStartDate,
    observedEndDate: qqqObserved.at(-1)?.date ?? asOf,
    syntheticHistoryStartDate: syntheticHistory[0]?.date ?? null,
    syntheticHistoryMonths: syntheticHistory.length,
    syntheticFutureMonths: futureMonths,
    points,
    future,
    calibration: {
      proxySource: "NASDAQ100 + NASDAQCOM",
      proxyOverlapMonths: proxyCalibration.overlapMonths,
      proxyBeta: proxyCalibration.beta,
      qqqOverlapMonths: qqqCalibration.overlapMonths,
      qqqBeta: qqqCalibration.beta,
    },
  };
}
