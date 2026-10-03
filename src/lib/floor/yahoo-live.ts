export type YahooBar = {
  date: string;
  close: number;
};

export type YahooSeries = {
  symbol: string;
  price: number | null;
  previousClose: number | null;
  regularMarketTime: string | null;
  marketState: string | null;
  currency: string | null;
  bars: YahooBar[];
};

export type LiveScaleSignal = {
  scale: "DAY" | "WEEK" | "MONTH";
  currentMove: number | null;
  meanMove: number | null;
  percentile: number | null;
  ratio: number | null;
  level: "NORMAL_LOW" | "NORMAL" | "ELEVATED" | "HIGH" | "EXTREME" | "SUPER_EXTREME" | "UNKNOWN";
};

export type PriceHorizon = 1 | 5 | 21;

export type PriceActionLevel = {
  side: "ADD" | "REDUCE";
  horizon: PriceHorizon;
  touchProbability: number;
  price: number | null;
  distancePct: number | null;
  samples: number;
};

export type PricePathSample = {
  entryPrice: number;
  low1: number;
  low5: number;
  low21: number;
  high1: number;
  high5: number;
  high21: number;
};

export type LivePriceLadder = {
  add: PriceActionLevel[];
  reduce: PriceActionLevel[];
  samples: number;
  quality: "THIN" | "DESCRIPTIVE";
};

export type LiveHistoryMatch = {
  symbol: string;
  currentPrice: number | null;
  priceDir: "STRONG_UP" | "MOD_UP" | "FLAT" | "MOD_DOWN" | "STRONG_DOWN";
  volLevel: LiveScaleSignal["level"];
  day: LiveScaleSignal;
  week: LiveScaleSignal;
  month: LiveScaleSignal;
  matches: number;
  median1d: number | null;
  median5d: number | null;
  median21d: number | null;
  pUp5d: number | null;
  referenceDates: string[];
  priceLadder: LivePriceLadder | null;
};

export function buildLiveHistoryMatch(series: YahooSeries): LiveHistoryMatch | null {
  const closes = series.bars.map((b) => b.close).filter((x) => Number.isFinite(x) && x > 0);
  const current = finitePositive(series.price) ?? closes.at(-1) ?? null;
  if (current == null || closes.length < 80) return null;

  const day = liveScale(current, closes, 1, 756);
  const week = liveScale(current, closes, 5, 180);
  const month = liveScale(current, closes, 21, 48);
  const priceDir = signedDir(current, closes.at(-6) ?? null);
  const directionPercentile = historicalSignedPercentile(current, closes, 5, 180, closes.length - 1);
  const volLevel = week.level;

  type Candidate = {
    date: string;
    base: number;
    directionPercentile: number;
    d1: number;
    d5: number;
    d21: number;
    low1: number;
    low5: number;
    low21: number;
    high1: number;
    high5: number;
    high21: number;
  };
  const candidates: Candidate[] = [];
  const target = [
    day.percentile,
    week.percentile,
    month.percentile,
    directionPercentile,
  ];
  for (let i = 25; i < closes.length - 21; i += 1) {
    const d = historicalPercentile(closes[i], closes, 1, 756, i);
    const w = historicalPercentile(closes[i], closes, 5, 180, i);
    const m = historicalPercentile(closes[i], closes, 21, 48, i);
    const direction = historicalSignedPercentile(closes[i], closes, 5, 180, i);
    if (
      target.some((x) => x == null) ||
      d == null || w == null || m == null || direction == null
    ) continue;
    const distance =
      Math.abs(d - (target[0] ?? 0)) +
      Math.abs(w - (target[1] ?? 0)) +
      Math.abs(m - (target[2] ?? 0)) +
      Math.abs(direction - (target[3] ?? 0));
    // Keep the original ~0.08 average feature-distance threshold after adding direction.
    if (distance > 0.32) continue;
    const d1 = signedForward(closes, i, 1);
    const d5 = signedForward(closes, i, 5);
    const d21 = signedForward(closes, i, 21);
    const low1 = forwardExtreme(closes, i, 1, "LOW");
    const low5 = forwardExtreme(closes, i, 5, "LOW");
    const low21 = forwardExtreme(closes, i, 21, "LOW");
    const high1 = forwardExtreme(closes, i, 1, "HIGH");
    const high5 = forwardExtreme(closes, i, 5, "HIGH");
    const high21 = forwardExtreme(closes, i, 21, "HIGH");
    if (
      d1 == null || d5 == null || d21 == null ||
      low1 == null || low5 == null || low21 == null ||
      high1 == null || high5 == null || high21 == null
    ) continue;
    candidates.push({
      date: series.bars[i]?.date ?? "",
      base: closes[i] ?? 0,
      directionPercentile: direction,
      d1, d5, d21,
      low1, low5, low21,
      high1, high5, high21,
    });
  }

  candidates.sort(
    (a, b) =>
      featureDistance(closes, a.date, target) -
      featureDistance(closes, b.date, target),
  );
  const selected = candidates.slice(0, 25);
  const priceLadder = current == null
    ? null
    : buildConditionalPriceLadder(
        current,
        selected.map((x) => ({
          entryPrice: x.base,
          low1: x.low1,
          low5: x.low5,
          low21: x.low21,
          high1: x.high1,
          high5: x.high5,
          high21: x.high21,
        })),
      );
  return {
    symbol: series.symbol,
    currentPrice: current,
    priceDir,
    volLevel,
    day,
    week,
    month,
    matches: selected.length,
    median1d: median(selected.map((x) => x.d1)),
    median5d: median(selected.map((x) => x.d5)),
    median21d: median(selected.map((x) => x.d21)),
    pUp5d: selected.length ? selected.filter((x) => x.d5 > 0).length / selected.length : null,
    referenceDates: selected.slice(0, 8).map((x) => x.date).filter(Boolean),
    priceLadder,
  };

  function featureDistance(xs: number[], date: string, t: (number | null)[]) {
    const i = series.bars.findIndex((b) => b.date === date);
    if (i < 25) return Infinity;
    const d = historicalPercentile(xs[i], xs, 1, 756, i);
    const w = historicalPercentile(xs[i], xs, 5, 180, i);
    const m = historicalPercentile(xs[i], xs, 21, 48, i);
    const direction = historicalSignedPercentile(xs[i], xs, 5, 180, i);
    if (d == null || w == null || m == null || direction == null) return Infinity;
    return (
      Math.abs(d - (t[0] ?? d)) +
      Math.abs(w - (t[1] ?? w)) +
      Math.abs(m - (t[2] ?? m)) +
      Math.abs(direction - (t[3] ?? direction))
    );
  }
}

function liveScale(current: number, closes: number[], step: number, cap: number): LiveScaleSignal {
  const move = Math.abs(current / (closes.at(-(step + 1)) ?? 0) - 1);
  if (!Number.isFinite(move) || move < 0) {
    return { scale: step === 1 ? "DAY" : step === 5 ? "WEEK" : "MONTH", currentMove: null, meanMove: null, percentile: null, ratio: null, level: "UNKNOWN" };
  }
  const sample: number[] = [];
  const end = closes.length - 1;
  for (let i = end - cap * step; i < end; i += step) {
    if (i < step) continue;
    const a = closes[i - step];
    const b = closes[i];
    if (a > 0 && b > 0) sample.push(Math.abs(b / a - 1));
  }
  const meanMove = mean(sample);
  const percentile = sample.length ? sample.filter((x) => x <= move).length / sample.length : null;
  const ratio = meanMove && meanMove > 0 ? move / meanMove : null;
  return {
    scale: step === 1 ? "DAY" : step === 5 ? "WEEK" : "MONTH",
    currentMove: move,
    meanMove,
    percentile,
    ratio,
    level: levelOf(ratio),
  };
}

function historicalPercentile(valueAtI: number, closes: number[], step: number, cap: number, i: number) {
  if (!(valueAtI > 0) || i < step + 40) return null;
  const move = Math.abs(valueAtI / closes[i - step] - 1);
  const sample: number[] = [];
  const first = Math.max(step, i - cap * step);
  for (let k = first; k < i; k += step) {
    const a = closes[k - step];
    const b = closes[k];
    if (a > 0 && b > 0) sample.push(Math.abs(b / a - 1));
  }
  return sample.length >= 40 ? sample.filter((x) => x <= move).length / sample.length : null;
}

function signedForward(closes: number[], i: number, horizon: number) {
  const a = closes[i];
  const b = closes[i + horizon];
  return a > 0 && b > 0 ? b / a - 1 : null;
}

function historicalSignedPercentile(valueAtI: number, closes: number[], step: number, cap: number, i: number) {
  if (!(valueAtI > 0) || i < step + 40) return null;
  const move = valueAtI / closes[i - step] - 1;
  const sample: number[] = [];
  const first = Math.max(step, i - cap * step);
  for (let k = first; k < i; k += step) {
    const a = closes[k - step];
    const b = closes[k];
    if (a > 0 && b > 0) sample.push(b / a - 1);
  }
  return sample.length >= 40 ? sample.filter((x) => x <= move).length / sample.length : null;
}

function forwardExtreme(
  closes: number[],
  i: number,
  horizon: number,
  side: "LOW" | "HIGH",
) {
  const path = closes.slice(i, i + horizon + 1);
  if (path.length !== horizon + 1 || !path.every((x) => x > 0)) return null;
  return side === "LOW" ? Math.min(...path) : Math.max(...path);
}

function quantile(xs: number[], q: number) {
  if (!xs.length) return null;
  const sorted = [...xs].sort((a, b) => a - b);
  const position = (sorted.length - 1) * Math.max(0, Math.min(1, q));
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower] ?? null;
  const weight = position - lower;
  return (sorted[lower] ?? 0) * (1 - weight) + (sorted[upper] ?? 0) * weight;
}

export function buildConditionalPriceLadder(
  current: number,
  selected: PricePathSample[],
): LivePriceLadder {
  const touchProbabilities = [0.7, 0.5, 0.3] as const;
  const horizons = [1, 5, 21] as const;
  const add: PriceActionLevel[] = [];
  const reduce: PriceActionLevel[] = [];
  const valid = selected.filter(
    (x) =>
      Number.isFinite(x.entryPrice) &&
      x.entryPrice > 0 &&
      [x.low1, x.low5, x.low21, x.high1, x.high5, x.high21].every(
        (value) => Number.isFinite(value) && value > 0,
      ),
  );

  const rawLevels = horizons.map((horizon) => {
    const lows = valid.map(
      (x) =>
        (horizon === 1 ? x.low1 : horizon === 5 ? x.low5 : x.low21) /
        x.entryPrice,
    );
    const highs = valid.map(
      (x) =>
        (horizon === 1 ? x.high1 : horizon === 5 ? x.high5 : x.high21) /
        x.entryPrice,
    );
    return { horizon, lows, highs };
  });

  for (const { horizon, lows, highs } of rawLevels) {
    for (const touchProbability of touchProbabilities) {
      const lowRatio = quantile(lows, touchProbability);
      const highRatio = quantile(highs, 1 - touchProbability);
      const addPrice = lowRatio == null ? null : current * lowRatio;
      const reducePrice = highRatio == null ? null : current * highRatio;
      add.push({
        side: "ADD",
        horizon,
        touchProbability,
        price: addPrice != null && addPrice < current ? addPrice : null,
        distancePct: addPrice != null && addPrice < current ? addPrice / current - 1 : null,
        samples: valid.length,
      });
      reduce.push({
        side: "REDUCE",
        horizon,
        touchProbability,
        price: reducePrice != null && reducePrice > current ? reducePrice : null,
        distancePct: reducePrice != null && reducePrice > current ? reducePrice / current - 1 : null,
        samples: valid.length,
      });
    }
  }

  return {
    add,
    reduce,
    samples: valid.length,
    quality: valid.length < 12 ? "THIN" : "DESCRIPTIVE",
  };
}

function signedDir(current: number, prior: number | null) {
  const r = prior && prior > 0 ? current / prior - 1 : 0;
  if (r > 0.03) return "STRONG_UP" as const;
  if (r > 0.008) return "MOD_UP" as const;
  if (r < -0.03) return "STRONG_DOWN" as const;
  if (r < -0.008) return "MOD_DOWN" as const;
  return "FLAT" as const;
}

function levelOf(ratio: number | null): LiveScaleSignal["level"] {
  if (ratio == null) return "UNKNOWN";
  if (ratio < 0.8) return "NORMAL_LOW";
  if (ratio < 1) return "NORMAL";
  if (ratio < 1.25) return "ELEVATED";
  if (ratio < 1.5) return "HIGH";
  if (ratio < 2) return "EXTREME";
  return "SUPER_EXTREME";
}

function finitePositive(x: unknown): number | null {
  const n = Number(x);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function mean(xs: number[]) {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
}

function median(xs: number[]) {
  if (!xs.length) return null;
  const a = [...xs].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}
