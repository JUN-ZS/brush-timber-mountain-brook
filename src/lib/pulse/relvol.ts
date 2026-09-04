import { denseCloses, vixAt, calendar, type ClosePt } from "./bars.ts";
import { assignSplit } from "./splits.ts";
import { cohortOf, INDEX, TRADED, type Cohort, type SymbolId } from "./universe.ts";
import { median, stdev, timeDecay } from "./stats.ts";

export type Scale = "DAY" | "WEEK" | "MONTH";
export type RelLevel = "NORMAL_LOW" | "NORMAL" | "ELEVATED" | "HIGH" | "EXTREME" | "SUPER_EXTREME";
export type VolDir = "CONTRACTING" | "NORMAL" | "EXPANDING" | "EXTREME";
export type PriceDir = "STRONG_UP" | "MOD_UP" | "FLAT" | "MOD_DOWN" | "STRONG_DOWN";

export type ScaleState = {
  scale: Scale;
  current: number;
  mean: number | null;
  median: number | null;
  std: number | null;
  percentile: number | null;
  ratio: number | null;
  z: number | null;
  level: RelLevel | "UNKNOWN";
  durationAboveMean: number;
  durationAbove90: number;
  durationAbove95: number;
  nextMean: number | null;
  nextWarn: number | null;
  nextExtreme: number | null;
  gapToWarn: number | null;
  p90: number | null;
};

export type Persistence = {
  p1: number | null;
  p2: number | null;
  p3: number | null;
  n: number;
  score: "HIGH" | "LOW" | "UNKNOWN";
  oosP1: number | null;
  oosN: number;
};

export type MoveDist = {
  p1: number | null;
  p2: number | null;
  p3: number | null;
  p5: number | null;
  p8: number | null;
  p10: number | null;
  median: number | null;
  n: number;
};

export type DurationStat = {
  duration: number;
  n: number;
  pContinue: number | null;
  pRevert: number | null;
  pExtreme: number | null;
};

export type MatrixCell = {
  price: PriceDir;
  vol: VolDir;
  n: number;
  medianNext: number | null;
  pUp: number | null;
};

export type RelCard = {
  symbol: SymbolId;
  date: string;
  cal: number;
  spot: number;
  cohort: Cohort;
  nBars: number;
  confidence: "thin" | "low" | "moderate";
  day: ScaleState;
  week: ScaleState;
  month: ScaleState;
  persistence: Persistence;
  continuation: number | null;
  reversion: number | null;
  volMomentum: "RISING" | "FALLING" | "FLAT" | "UNKNOWN";
  weekTimeline: { d: string; pct: number | null }[];
  priceDir: PriceDir;
  volDir: VolDir;
  expectedMove: { d1: MoveDist; d5: MoveDist; d21: MoveDist };
  impliedWeek: number | null;
  modelWeek: number | null;
  volEdge: number | null;
  rv21: number | null;
  split: ReturnType<typeof assignSplit>;
  alert: "READY" | "PRE_BREAKOUT" | "EARLY" | "WAIT";
  durationCond: DurationStat | null;
  missing: string[];
};

const HIST_DAY = 756;
const HIST_WEEK = 180;
const HIST_MONTH = 48;

export const LEVEL_THRESHOLDS = [0.8, 0.9, 1, 1.1, 1.2, 1.25, 1.5, 1.75, 2, 2.5, 3];

export function levelOf(ratio: number | null): RelLevel | "UNKNOWN" {
  if (ratio == null) return "UNKNOWN";
  if (ratio < 0.8) return "NORMAL_LOW";
  if (ratio < 1) return "NORMAL";
  if (ratio < 1.25) return "ELEVATED";
  if (ratio < 1.5) return "HIGH";
  if (ratio < 2) return "EXTREME";
  return "SUPER_EXTREME";
}

function absMove(c: number[], i: number, win: number) {
  const a = c[i - win];
  const b = c[i];
  if (!(a > 0) || !(b > 0) || i - win < 0) return null;
  return Math.abs(b / a - 1);
}

function signedMove(c: number[], i: number, win: number) {
  const a = c[i - win];
  const b = c[i];
  if (!(a > 0) || !(b > 0) || i - win < 0) return null;
  return b / a - 1;
}

function durationBack(pcts: (number | null)[], i: number, thresh: number, step: number) {
  let n = 0;
  for (let k = i; k >= 0; k -= step) {
    const p = pcts[k];
    if (p == null || p < thresh) break;
    n += 1;
  }
  return n;
}

export function priceDirOf(r: number | null): PriceDir {
  if (r == null) return "FLAT";
  if (r > 0.03) return "STRONG_UP";
  if (r > 0.008) return "MOD_UP";
  if (r < -0.03) return "STRONG_DOWN";
  if (r < -0.008) return "MOD_DOWN";
  return "FLAT";
}

export function volDirOf(level: RelLevel | "UNKNOWN"): VolDir {
  if (level === "NORMAL_LOW") return "CONTRACTING";
  if (level === "NORMAL" || level === "UNKNOWN") return "NORMAL";
  if (level === "ELEVATED" || level === "HIGH") return "EXPANDING";
  return "EXTREME";
}

function distOf(xs: number[]): MoveDist {
  if (!xs.length) return { p1: null, p2: null, p3: null, p5: null, p8: null, p10: null, median: null, n: 0 };
  const hit = (t: number) => xs.filter((x) => x > t).length / xs.length;
  return {
    p1: hit(0.01),
    p2: hit(0.02),
    p3: hit(0.03),
    p5: hit(0.05),
    p8: hit(0.08),
    p10: hit(0.1),
    median: median(xs),
    n: xs.length,
  };
}

type Built = {
  dates: string[];
  cal: number[];
  closes: number[];
  day: (number | null)[];
  week: (number | null)[];
  month: (number | null)[];
  dayPct: (number | null)[];
  weekPct: (number | null)[];
  monthPct: (number | null)[];
  dayMean: (number | null)[];
  weekMean: (number | null)[];
  monthMean: (number | null)[];
  weekP90: (number | null)[];
};

function p90of(h: number[]) {
  if (h.length < 40) return null;
  const a = [...h].sort((x, y) => x - y);
  return a[Math.floor(0.9 * (a.length - 1))];
}

/** Fixed-bin histogram so percentile is O(1) per bar, not O(window). */
class MoveHist {
  q: number[] = [];
  bins = new Int32Array(48);
  n = 0;
  sum = 0;
  cap: number;
  constructor(cap: number) {
    this.cap = cap;
  }
  add(x: number) {
    this.q.push(x);
    this.bins[binOf(x)] += 1;
    this.n += 1;
    this.sum += x;
    if (this.q.length > this.cap) {
      const old = this.q.shift()!;
      this.bins[binOf(old)] -= 1;
      this.n -= 1;
      this.sum -= old;
    }
  }
  mean() {
    return this.n ? this.sum / this.n : null;
  }
  pct(x: number) {
    if (this.n < 40) return null;
    const b = binOf(x);
    let c = 0;
    for (let i = 0; i <= b; i++) c += this.bins[i];
    return c / this.n;
  }
  p90() {
    if (this.n < 40) return null;
    const target = Math.floor(0.9 * this.n);
    let c = 0;
    for (let i = 0; i < this.bins.length; i++) {
      c += this.bins[i];
      if (c >= target) return (i + 0.5) * 0.006;
    }
    return 0.25;
  }
}

function binOf(x: number) {
  if (x <= 0) return 0;
  return Math.min(47, Math.floor(x / 0.006));
}

function buildSeries(sym: string): Built {
  const pts: ClosePt[] = denseCloses(sym);
  const n = pts.length;
  const dates = pts.map((p) => p.d);
  const cal = pts.map((p) => p.cal);
  const closes = pts.map((p) => p.c);
  const day = new Array<number | null>(n).fill(null);
  const week = new Array<number | null>(n).fill(null);
  const month = new Array<number | null>(n).fill(null);
  const dayPct = new Array<number | null>(n).fill(null);
  const weekPct = new Array<number | null>(n).fill(null);
  const monthPct = new Array<number | null>(n).fill(null);
  const dayMean = new Array<number | null>(n).fill(null);
  const weekMean = new Array<number | null>(n).fill(null);
  const monthMean = new Array<number | null>(n).fill(null);
  const weekP90 = new Array<number | null>(n).fill(null);
  const hDay = new MoveHist(HIST_DAY);
  const hWeek = new MoveHist(HIST_WEEK);
  const hMonth = new MoveHist(HIST_MONTH);
  for (let i = 0; i < n; i++) {
    const d = absMove(closes, i, 1);
    const w = absMove(closes, i, 5);
    const m = absMove(closes, i, 21);
    day[i] = d;
    week[i] = w;
    month[i] = m;
    dayMean[i] = hDay.mean();
    weekMean[i] = hWeek.mean();
    monthMean[i] = hMonth.mean();
    weekP90[i] = hWeek.p90();
    if (d != null) dayPct[i] = hDay.pct(d);
    if (w != null) weekPct[i] = hWeek.pct(w);
    if (m != null) monthPct[i] = hMonth.pct(m);
    if (d != null) hDay.add(d);
    if (w != null) hWeek.add(w);
    if (m != null) hMonth.add(m);
  }
  return {
    dates,
    cal,
    closes,
    day,
    week,
    month,
    dayPct,
    weekPct,
    monthPct,
    dayMean,
    weekMean,
    monthMean,
    weekP90,
  };
}

const cache = new Map<string, Built>();
function seriesOf(sym: string) {
  let s = cache.get(sym);
  if (!s) {
    s = buildSeries(sym);
    cache.set(sym, s);
  }
  return s;
}

function idxAt(s: Built, calCursor: number) {
  let i = s.cal.length - 1;
  while (i >= 0 && s.cal[i] > calCursor) i -= 1;
  return i;
}

function scaleState(s: Built, i: number, scale: Scale): ScaleState {
  const cur = scale === "DAY" ? s.day[i] : scale === "WEEK" ? s.week[i] : s.month[i];
  const mn = scale === "DAY" ? s.dayMean[i] : scale === "WEEK" ? s.weekMean[i] : s.monthMean[i];
  const pct = scale === "DAY" ? s.dayPct[i] : scale === "WEEK" ? s.weekPct[i] : s.monthPct[i];
  const step = scale === "DAY" ? 1 : scale === "WEEK" ? 5 : 21;
  const hist: number[] = [];
  const cap = scale === "DAY" ? HIST_DAY : scale === "WEEK" ? HIST_WEEK : HIST_MONTH;
  for (let k = i - step; k >= Math.max(0, i - cap * step); k -= step) {
    const v = scale === "DAY" ? s.day[k] : scale === "WEEK" ? s.week[k] : s.month[k];
    if (v != null) hist.push(v);
  }
  const ratio = cur != null && mn ? cur / mn : null;
  const sd = stdev(hist);
  const z = cur != null && mn != null && sd ? (cur - mn) / sd : null;
  const pcts = scale === "DAY" ? s.dayPct : scale === "WEEK" ? s.weekPct : s.monthPct;
  const p90 = scale === "WEEK" ? s.weekP90[i] : hist.length >= 40 ? p90of(hist) : null;
  const warn = p90 ?? (mn != null ? mn * 1.5 : null);
  const extreme = mn != null ? mn * 2 : null;
  return {
    scale,
    current: cur ?? 0,
    mean: mn,
    median: median(hist),
    std: sd,
    percentile: pct,
    ratio,
    z,
    level: levelOf(ratio),
    durationAboveMean: durationBack(pcts, i, 0.5, step),
    durationAbove90: durationBack(pcts, i, 0.9, step),
    durationAbove95: durationBack(pcts, i, 0.95, step),
    nextMean: mn,
    nextWarn: warn,
    nextExtreme: extreme,
    gapToWarn: cur != null && warn != null ? warn - cur : null,
    p90,
  };
}

function persistenceWeek(s: Built, i: number): Persistence {
  let stay1 = 0;
  let stay2 = 0;
  let stay3 = 0;
  let n = 0;
  let oosStay = 0;
  let oosN = 0;
  for (let k = 10; k + 15 < i; k += 5) {
    const m = s.weekMean[k];
    const w = s.week[k];
    if (m == null || w == null || w <= m) continue;
    const split = assignSplit(s.dates[k]);
    const w1 = s.week[k + 5];
    const w2 = s.week[k + 10];
    const w3 = s.week[k + 15];
    const m1 = s.weekMean[k + 5] ?? m;
    const m2 = s.weekMean[k + 10] ?? m;
    const m3 = s.weekMean[k + 15] ?? m;
    const wt = timeDecay(i - k);
    if (split === "TRAIN") {
      n += wt;
      if (w1 != null && w1 > m1) stay1 += wt;
      if (w1 != null && w1 > m1 && w2 != null && w2 > m2) stay2 += wt;
      if (w1 != null && w1 > m1 && w2 != null && w2 > m2 && w3 != null && w3 > m3) stay3 += wt;
    } else if (split === "UNPROVEN_OOS" || split === "VALIDATION") {
      oosN += 1;
      if (w1 != null && w1 > m1) oosStay += 1;
    }
  }
  const p1 = n >= 20 ? stay1 / n : null;
  const p2 = n >= 20 ? stay2 / n : null;
  const p3 = n >= 20 ? stay3 / n : null;
  const score: Persistence["score"] = p1 == null ? "UNKNOWN" : p1 >= 0.55 ? "HIGH" : "LOW";
  return { p1, p2, p3, n: Math.round(n), score, oosP1: oosN >= 12 ? oosStay / oosN : null, oosN };
}

function contRev(s: Built, i: number): { continuation: number | null; reversion: number | null } {
  const pct = s.weekPct[i];
  if (pct == null) return { continuation: null, reversion: null };
  let cont = 0;
  let n = 0;
  for (let k = 10; k + 5 < i; k += 5) {
    if (assignSplit(s.dates[k]) !== "TRAIN") continue;
    const p = s.weekPct[k];
    if (p == null || Math.abs(p - pct) > 0.08) continue;
    const nxt = s.weekPct[k + 5];
    if (nxt == null) continue;
    const w = timeDecay(i - k);
    n += w;
    if (nxt >= p - 0.02) cont += w;
  }
  if (n < 12) return { continuation: null, reversion: null };
  const continuation = cont / n;
  return { continuation, reversion: 1 - continuation };
}

function moveDists(s: Built, i: number): RelCard["expectedMove"] {
  const pct = s.weekPct[i];
  const d1: number[] = [];
  const d5: number[] = [];
  const d21: number[] = [];
  if (pct != null) {
    for (let k = 30; k + 21 < i; k += 5) {
      if (assignSplit(s.dates[k]) !== "TRAIN") continue;
      const p = s.weekPct[k];
      if (p == null || Math.abs(p - pct) > 0.1) continue;
      const a = absMove(s.closes, k + 1, 1);
      const b = absMove(s.closes, k + 5, 5);
      const c = absMove(s.closes, k + 21, 21);
      if (a != null) d1.push(a);
      if (b != null) d5.push(b);
      if (c != null) d21.push(c);
    }
  }
  return { d1: distOf(d1), d5: distOf(d5), d21: distOf(d21) };
}

function durationCond(s: Built, i: number, dur: number): DurationStat | null {
  if (dur < 1) return null;
  let n = 0;
  let cont = 0;
  let rev = 0;
  let ext = 0;
  for (let k = 25; k + 5 < i; k += 5) {
    if (assignSplit(s.dates[k]) !== "TRAIN") continue;
    const d = durationBack(s.weekPct, k, 0.9, 5);
    if (d !== dur) continue;
    n += 1;
    const nxt = s.weekPct[k + 5];
    if (nxt != null && nxt >= 0.9) cont += 1;
    if (nxt != null && nxt < 0.5) rev += 1;
    if (nxt != null && nxt >= 0.95) ext += 1;
  }
  if (n < 8) return { duration: dur, n, pContinue: null, pRevert: null, pExtreme: null };
  return { duration: dur, n, pContinue: cont / n, pRevert: rev / n, pExtreme: ext / n };
}

function rv21(closes: number[], i: number) {
  if (i < 22) return null;
  const xs: number[] = [];
  for (let k = i - 20; k <= i; k++) {
    const r = signedMove(closes, k, 1);
    if (r != null) xs.push(r);
  }
  const sd = stdev(xs);
  return sd == null ? null : sd * Math.sqrt(252);
}

export function cardAt(sym: SymbolId, calCursor: number): RelCard | null {
  const s = seriesOf(sym);
  const i = idxAt(s, calCursor);
  if (i < 40) return null;
  const day = scaleState(s, i, "DAY");
  const week = scaleState(s, i, "WEEK");
  const month = scaleState(s, i, "MONTH");
  const persist = persistenceWeek(s, i);
  const cr = contRev(s, i);
  const tl: RelCard["weekTimeline"] = [];
  for (let k = Math.max(5, i - 5 * 16); k <= i; k += 5) {
    tl.push({ d: s.dates[k], pct: s.weekPct[k] });
  }
  const a = tl[tl.length - 1]?.pct;
  const b = tl[tl.length - 4]?.pct;
  const slope = a != null && b != null ? a - b : 0;
  const volMom: RelCard["volMomentum"] =
    a == null || b == null ? "UNKNOWN" : slope > 0.06 ? "RISING" : slope < -0.06 ? "FALLING" : "FLAT";
  const r5 = signedMove(s.closes, i, 5);
  const rv = rv21(s.closes, i);
  const vix = vixAt(s.cal[i]);
  const implied = INDEX.has(sym) && vix != null ? vix / 100 / Math.sqrt(52) : rv != null ? (rv / Math.sqrt(52)) * 1.15 : week.mean;
  const modelWeek = moveDists(s, i).d5.median;
  const dur = durationCond(s, i, week.durationAbove90);
  let alert: RelCard["alert"] = "WAIT";
  const wp = week.percentile ?? 0;
  if (wp >= 0.9 && week.durationAboveMean >= 2) alert = "READY";
  else if (wp >= 0.8 && wp < 0.9 && volMom === "RISING") alert = "PRE_BREAKOUT";
  else if (wp >= 0.7 && volMom === "RISING" && week.durationAboveMean >= 3) alert = "EARLY";
  const missing = ["OPTIONS", "IV_SURFACE", "BID_ASK"];
  if (s.dates.length < 800) missing.push("SHORT_HISTORY");
  let life = 0;
  let ln = 0;
  for (let k = 5; k <= i; k += 5) {
    const w = s.week[k];
    if (w != null) {
      life += w;
      ln += 1;
    }
  }
  return {
    symbol: sym,
    date: s.dates[i],
    cal: s.cal[i],
    spot: s.closes[i],
    cohort: cohortOf(s.dates.length, ln ? life / ln : week.mean),
    nBars: s.dates.length,
    confidence: s.dates.length < 800 ? "thin" : week.percentile == null ? "low" : "moderate",
    day,
    week,
    month,
    persistence: persist,
    continuation: cr.continuation,
    reversion: cr.reversion,
    volMomentum: volMom,
    weekTimeline: tl,
    priceDir: priceDirOf(r5),
    volDir: volDirOf(week.level),
    expectedMove: moveDists(s, i),
    impliedWeek: implied ?? null,
    modelWeek,
    volEdge: modelWeek != null && implied != null ? modelWeek - implied : null,
    rv21: rv,
    split: assignSplit(s.dates[i]),
    alert,
    durationCond: dur,
    missing,
  };
}

export function ranking(calCursor: number) {
  return TRADED.map((sym) => cardAt(sym, calCursor)).filter((c): c is RelCard => c != null);
}

export function similarFwd(sym: SymbolId, calCursor: number, horizon = 5): { r: number; w: number }[] {
  const s = seriesOf(sym);
  const i = idxAt(s, calCursor);
  const pct = s.weekPct[i];
  const out: { r: number; w: number }[] = [];
  if (pct == null || i < 40) return out;
  for (let k = 30; k + horizon < i; k += 5) {
    if (assignSplit(s.dates[k]) !== "TRAIN") continue;
    const p = s.weekPct[k];
    if (p == null || Math.abs(p - pct) > 0.1) continue;
    const r = signedMove(s.closes, k + horizon, horizon);
    if (r != null) out.push({ r, w: timeDecay(i - k) });
  }
  return out;
}

export function thresholdProbe(sym: SymbolId, calCursor: number) {
  const s = seriesOf(sym);
  const i = idxAt(s, calCursor);
  return LEVEL_THRESHOLDS.map((thr) => {
    let n = 0;
    let stay = 0;
    for (let k = 20; k + 5 < i; k += 5) {
      if (assignSplit(s.dates[k]) !== "TRAIN") continue;
      const m = s.weekMean[k];
      const w = s.week[k];
      if (m == null || w == null || w / m < thr) continue;
      n += 1;
      const w1 = s.week[k + 5];
      const m1 = s.weekMean[k + 5] ?? m;
      if (w1 != null && m1 && w1 / m1 >= thr) stay += 1;
    }
    return { thr, n, p1: n >= 12 ? stay / n : null };
  });
}

export function stateMatrix(sym: SymbolId, calCursor: number): MatrixCell[] {
  const s = seriesOf(sym);
  const i = idxAt(s, calCursor);
  const prices: PriceDir[] = ["STRONG_UP", "MOD_UP", "FLAT", "MOD_DOWN", "STRONG_DOWN"];
  const vols: VolDir[] = ["CONTRACTING", "NORMAL", "EXPANDING", "EXTREME"];
  const buckets = new Map<string, number[]>();
  for (const p of prices) for (const v of vols) buckets.set(`${p}|${v}`, []);
  for (let k = 30; k + 5 < i; k += 5) {
    if (assignSplit(s.dates[k]) !== "TRAIN") continue;
    const r5 = signedMove(s.closes, k, 5);
    const ratio = s.week[k] != null && s.weekMean[k] ? s.week[k]! / s.weekMean[k]! : null;
    const pd = priceDirOf(r5);
    const vd = volDirOf(levelOf(ratio));
    const nxt = signedMove(s.closes, k + 5, 5);
    if (nxt == null) continue;
    buckets.get(`${pd}|${vd}`)?.push(nxt);
  }
  const cells: MatrixCell[] = [];
  for (const p of prices) {
    for (const v of vols) {
      const xs = buckets.get(`${p}|${v}`) ?? [];
      cells.push({
        price: p,
        vol: v,
        n: xs.length,
        medianNext: median(xs),
        pUp: xs.length ? xs.filter((x) => x > 0).length / xs.length : null,
      });
    }
  }
  return cells;
}

export function causalOk(sym: SymbolId, calCursor: number) {
  const s = seriesOf(sym);
  const i = idxAt(s, calCursor);
  if (i < 50) return false;
  const later = s.weekMean[s.weekMean.length - 1];
  const now = s.weekMean[i];
  return now != null && later != null;
}

export { calendar };
