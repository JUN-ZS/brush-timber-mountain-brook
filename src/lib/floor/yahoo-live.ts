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
};

export function buildLiveHistoryMatch(series: YahooSeries): LiveHistoryMatch | null {
  const closes = series.bars.map((b) => b.close).filter((x) => Number.isFinite(x) && x > 0);
  const current = finitePositive(series.price) ?? closes.at(-1) ?? null;
  if (current == null || closes.length < 80) return null;

  const day = liveScale(current, closes, 1, 756);
  const week = liveScale(current, closes, 5, 180);
  const month = liveScale(current, closes, 21, 48);
  const priceDir = signedDir(current, closes.at(-6) ?? null);
  const volLevel = week.level;

  type Candidate = { date: string; d1: number; d5: number; d21: number };
  const candidates: Candidate[] = [];
  const target = [
    day.percentile,
    week.percentile,
    month.percentile,
  ];
  for (let i = 25; i < closes.length - 21; i += 1) {
    const d = historicalPercentile(closes[i], closes, 1, 756, i);
    const w = historicalPercentile(closes[i], closes, 5, 180, i);
    const m = historicalPercentile(closes[i], closes, 21, 48, i);
    if (target.some((x) => x == null) || d == null || w == null || m == null) continue;
    const distance =
      Math.abs(d - (target[0] ?? 0)) +
      Math.abs(w - (target[1] ?? 0)) +
      Math.abs(m - (target[2] ?? 0));
    if (distance > 0.24) continue;
    const d1 = signedForward(closes, i, 1);
    const d5 = signedForward(closes, i, 5);
    const d21 = signedForward(closes, i, 21);
    if (d1 == null || d5 == null || d21 == null) continue;
    candidates.push({ date: series.bars[i]?.date ?? "", d1, d5, d21 });
  }

  candidates.sort(
    (a, b) =>
      featureDistance(closes, a.date, target) -
      featureDistance(closes, b.date, target),
  );
  const selected = candidates.slice(0, 25);
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
  };

  function featureDistance(xs: number[], date: string, t: (number | null)[]) {
    const i = series.bars.findIndex((b) => b.date === date);
    if (i < 25) return Infinity;
    const d = historicalPercentile(xs[i], xs, 1, 756, i);
    const w = historicalPercentile(xs[i], xs, 5, 180, i);
    const m = historicalPercentile(xs[i], xs, 21, 48, i);
    if (d == null || w == null || m == null) return Infinity;
    return Math.abs(d - (t[0] ?? d)) + Math.abs(w - (t[1] ?? w)) + Math.abs(m - (t[2] ?? m));
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


export type SellTimingObservation = {
  price: number;
  trailing12mHigh: number;
  drawdownFrom12mHigh: number;
  return6m: number | null;
  return12m: number | null;
  near12mHigh: boolean;
  at12mHigh: boolean;
  strongAndHigh: boolean;
  postRunup: boolean;
  navAboveClock: boolean;
};

export function buildSellTimingObservation(
  series: YahooSeries,
  accountNav: number,
  clockTargetAmount: number,
): SellTimingObservation | null {
  const bars = series.bars
    .filter((bar) => Number.isFinite(bar.close) && bar.close > 0)
    .sort((a, b) => a.date.localeCompare(b.date));
  const price = finitePositive(series.price) ?? bars.at(-1)?.close ?? null;
  if (price == null || bars.length < 13) return null;

  const end = bars.length - 1;
  const start12 = Math.max(0, end - 251);
  const start6 = Math.max(0, end - 126);
  const trailing12mHigh = Math.max(...bars.slice(start12, end + 1).map((bar) => bar.close));
  const price6mAgo = bars[start6]?.close ?? null;
  const price12mAgo = bars[start12]?.close ?? null;
  const return6m = price6mAgo && price6mAgo > 0 ? price / price6mAgo - 1 : null;
  const return12m = price12mAgo && price12mAgo > 0 ? price / price12mAgo - 1 : null;
  const drawdownFrom12mHigh = price / trailing12mHigh - 1;
  const near12mHigh = price >= trailing12mHigh * 0.95 - 1e-12;
  const at12mHigh = price >= trailing12mHigh - 1e-12;

  return {
    price,
    trailing12mHigh,
    drawdownFrom12mHigh,
    return6m,
    return12m,
    near12mHigh,
    at12mHigh,
    strongAndHigh: return12m != null && return12m >= 0 && near12mHigh,
    postRunup: return6m != null && return6m >= 0.15 && near12mHigh,
    navAboveClock: Number.isFinite(accountNav) && accountNav > Math.max(0, clockTargetAmount) + 0.005,
  };
}


export type SellTimingObservation = {
  price: number;
  trailing12mHigh: number;
  drawdownFrom12mHigh: number;
  return6m: number | null;
  return12m: number | null;
  near12mHigh: boolean;
  at12mHigh: boolean;
  strongAndHigh: boolean;
  postRunup: boolean;
  navAboveClock: boolean;
};

export function buildSellTimingObservation(
  series: YahooSeries,
  accountNav: number,
  clockTargetAmount: number,
): SellTimingObservation | null {
  const bars = series.bars
    .filter((bar) => Number.isFinite(bar.close) && bar.close > 0)
    .sort((a, b) => a.date.localeCompare(b.date));
  const price = finitePositive(series.price) ?? bars.at(-1)?.close ?? null;
  if (price == null || bars.length < 260) return null;

  const end = bars.length - 1;
  const start12 = end - 251;
  const start6 = end - 126;
  const trailing12mHigh = Math.max(...bars.slice(start12, end + 1).map((bar) => bar.close));
  const price6mAgo = bars[start6]?.close ?? null;
  const price12mAgo = bars[start12]?.close ?? null;
  const return6m = price6mAgo && price6mAgo > 0 ? price / price6mAgo - 1 : null;
  const return12m = price12mAgo && price12mAgo > 0 ? price / price12mAgo - 1 : null;
  const drawdownFrom12mHigh = price / trailing12mHigh - 1;
  const near12mHigh = price >= trailing12mHigh * 0.95 - 1e-12;
  const at12mHigh = price >= trailing12mHigh - 1e-12;
  return {
    price,
    trailing12mHigh,
    drawdownFrom12mHigh,
    return6m,
    return12m,
    near12mHigh,
    at12mHigh,
    strongAndHigh: return12m != null && return12m >= 0 && near12mHigh,
    postRunup: return6m != null && return6m >= 0.15 && near12mHigh,
    navAboveClock: Number.isFinite(accountNav) && accountNav > Math.max(0, clockTargetAmount) + 0.005,
  };
}
