import { universe } from "./bars.ts";

export type Regime = "CALM" | "UNSTABLE" | "TAIL" | "RECOVERY";
export type StrategyId = "QQQ" | "QQQ_VXX" | "COVERED_PROXY" | "PROTECTED_PROXY" | "CONVEX_PROXY";

export const PROXY_STRATEGIES: StrategyId[] = ["COVERED_PROXY", "PROTECTED_PROXY", "CONVEX_PROXY"];

export type Policy = {
  baseRisk: number;
  unstableRisk: number;
  tailRisk: number;
  recoveryRisk: number;
  vxxHedge: number;
  ddBrake: number;
};

export type Metrics = {
  cagr: number;
  maxDd: number;
  sharpe: number;
  sortino: number;
  totalReturn: number;
  volatility: number;
  calmar: number;
  worstDay: number;
  es: number;
  turnover: number;
  nDays: number;
};

export type CurvePoint = {
  i: number;
  date: string;
  equity: number;
  drawdown: number;
  regime: Regime;
  risk: number;
  qqq: number | null;
  vxx: number | null;
  strategyReturn: number;
};

export type BacktestResult = {
  strategy: StrategyId;
  policy: Policy;
  metrics: Metrics;
  curve: CurvePoint[];
  split: { train: Metrics; validation: Metrics; oos: Metrics };
  score: number;
  proxy: boolean;
  oosLeakage: false;
};

const DAYS = 252;
const WARMUP = 60;

function ret(sym: string, i: number) {
  const a = universe.c[sym]?.[i - 1];
  const b = universe.c[sym]?.[i];
  if (a == null || b == null || a <= 0 || b <= 0) return null;
  return b / a - 1;
}

function close(sym: string, i: number) {
  const v = universe.c[sym]?.[i];
  return v == null || v <= 0 ? null : v;
}

function mean(xs: number[]) {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;
}

function stdev(xs: number[]) {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(mean(xs.map((x) => (x - m) ** 2)));
}

function quantile(xs: number[], q: number) {
  if (!xs.length) return 0;
  const a = [...xs].sort((x, y) => x - y);
  const p = (a.length - 1) * q;
  const lo = Math.floor(p);
  const hi = Math.ceil(p);
  return a[lo] + (a[hi] - a[lo]) * (p - lo);
}

function expectedShortfall(rs: number[], q = 0.05) {
  if (!rs.length) return 0;
  const cut = quantile(rs, q);
  const tail = rs.filter((r) => r <= cut);
  return tail.length ? mean(tail) : cut;
}

export function emptyMetrics(): Metrics {
  return {
    cagr: 0,
    maxDd: 0,
    sharpe: 0,
    sortino: 0,
    totalReturn: 0,
    volatility: 0,
    calmar: 0,
    worstDay: 0,
    es: 0,
    turnover: 0,
    nDays: 0,
  };
}

export function metrics(rs: number[], turnover = 0): Metrics {
  if (!rs.length) return emptyMetrics();
  let eq = 1;
  let peak = 1;
  let maxDd = 0;
  for (const r of rs) {
    eq *= 1 + r;
    peak = Math.max(peak, eq);
    maxDd = Math.min(maxDd, eq / peak - 1);
  }
  const vol = stdev(rs) * Math.sqrt(DAYS);
  const down = stdev(rs.filter((r) => r < 0)) * Math.sqrt(DAYS);
  const cagr = Math.pow(eq, DAYS / rs.length) - 1;
  return {
    cagr,
    maxDd,
    sharpe: vol ? (mean(rs) * DAYS) / vol : 0,
    sortino: down ? (mean(rs) * DAYS) / down : 0,
    totalReturn: eq - 1,
    volatility: vol,
    calmar: maxDd < 0 ? cagr / -maxDd : 0,
    worstDay: Math.min(...rs),
    es: expectedShortfall(rs, 0.05),
    turnover,
    nDays: rs.length,
  };
}

export function coverage() {
  const v = universe.c.VXX ?? [];
  let first = -1;
  let last = -1;
  let n = 0;
  for (let i = 0; i < v.length; i++) {
    if (v[i] != null && v[i] > 0) {
      n += 1;
      if (first < 0) first = i;
      last = i;
    }
  }
  return {
    vxxBars: n,
    vxxStartIndex: first,
    vxxEndIndex: last,
    vxxStart: first >= 0 ? universe.dates[first] : null,
    vxxEnd: last >= 0 ? universe.dates[last] : null,
    vxxFirstClose: first >= 0 ? v[first] : null,
    missingVxxAsZeroReturn: true,
    windowNotSilentlyShrunk: true,
    note: "Missing VXX bars are treated as 0 return in QQQ_VXX, so pre-2018 QQQ_VXX ≈ QQQ. The official window is NOT silently shrunk to the VXX era.",
  };
}

export function state(i: number): {
  regime: Regime;
  building: boolean;
  vol: number;
  vol5: number;
  vix: number | null;
  vixAccel: number | null;
  dd20: number;
  mom60: number;
  mom5: number;
} {
  const q = universe.c.QQQ ?? [];
  const p = q[i] ?? 0;
  const r20: number[] = [];
  const r5: number[] = [];
  for (let j = Math.max(1, i - 19); j <= i; j++) {
    const r = ret("QQQ", j);
    if (r != null) {
      r20.push(r);
      if (j >= i - 4) r5.push(r);
    }
  }
  const vol = stdev(r20) * Math.sqrt(DAYS);
  const vol5 = stdev(r5) * Math.sqrt(DAYS);
  const p20 = i >= 20 && q[i - 20] ? p / q[i - 20] - 1 : 0;
  const p60 = i >= 60 && q[i - 60] ? p / q[i - 60] - 1 : 0;
  const mom5 = i >= 5 && q[i - 5] ? p / q[i - 5] - 1 : 0;
  const vix = close("VIX", i);
  const vixPrev = i >= 5 ? close("VIX", i - 5) : null;
  const vixAccel = vix != null && vixPrev != null ? vix - vixPrev : null;
  const tail = (vix != null && vix >= 30) || vol >= 0.38 || p20 <= -0.08;
  const unstable = (vix != null && vix >= 20) || vol >= 0.25 || p20 < 0;
  const recovery = p20 > 0 && p60 < 0;
  const regime: Regime = tail ? "TAIL" : recovery ? "RECOVERY" : unstable ? "UNSTABLE" : "CALM";
  // Lead: danger forming, not yet TAIL. t-1 when called as state(i-1).
  const building =
    !tail &&
    vix != null &&
    vix >= 18 &&
    mom5 < 0 &&
    ((vol5 > vol * 1.15 && vol5 >= 0.18) || (vixAccel != null && vixAccel >= 2) || vol5 >= 0.28);
  return { regime, building, vol, vol5, vix, vixAccel, dd20: p20, mom60: p60, mom5 };
}

export function rawReturn(strategy: StrategyId, i: number, policy: Policy): number | null {
  const q = ret("QQQ", i);
  if (q == null) return null;
  const v = ret("VXX", i) ?? 0;
  if (strategy === "QQQ") return q;
  if (strategy === "QQQ_VXX") return q - policy.vxxHedge * v;
  if (strategy === "COVERED_PROXY") return Math.min(q, 0.006) + 0.0002;
  if (strategy === "PROTECTED_PROXY") return q + Math.max(-q - 0.015, 0) - 0.00025;
  return Math.abs(q) > 0.015 ? Math.abs(q) - 0.00055 : -0.00055;
}

function riskFor(s: ReturnType<typeof state>, dd: number, p: Policy) {
  let r =
    s.regime === "TAIL"
      ? p.tailRisk
      : s.regime === "UNSTABLE"
        ? p.unstableRisk
        : s.regime === "RECOVERY"
          ? p.recoveryRisk
          : p.baseRisk;
  if (dd <= -p.ddBrake) r *= 0.5;
  if (dd <= -Math.min(0.045, p.ddBrake * 1.8)) r *= 0.25;
  return Math.max(0, Math.min(1, r));
}

export function sampleWindow() {
  const end = universe.dates.length - 1;
  const start = WARMUP;
  const n = end - start + 1;
  const trainEnd = start + Math.floor(n * 0.6) - 1;
  const valEnd = start + Math.floor(n * 0.8) - 1;
  const cov = coverage();
  return {
    start,
    end,
    trainEnd,
    valEnd,
    oosStart: valEnd + 1,
    trainDate: universe.dates[start],
    trainEndDate: universe.dates[trainEnd],
    valEndDate: universe.dates[valEnd],
    oosStartDate: universe.dates[valEnd + 1],
    endDate: universe.dates[end],
    nBars: universe.dates.length,
    vxxStart: cov.vxxStart,
    vxxStartIndex: cov.vxxStartIndex,
    trainHasVxx: cov.vxxStartIndex >= 0 && cov.vxxStartIndex <= trainEnd,
    validationHasVxx: cov.vxxStartIndex >= 0 && cov.vxxStartIndex <= valEnd,
    oosHasVxx: cov.vxxStartIndex >= 0 && cov.vxxStartIndex <= end,
  };
}

export function validationScore(m: Metrics) {
  return (
    m.cagr * 100 -
    Math.max(0, -m.maxDd) * 160 -
    Math.max(0, -m.es) * 80 +
    m.sharpe * 6 +
    m.sortino * 3 -
    m.turnover * 8
  );
}

export function runBacktest(
  strategy: StrategyId,
  policy: Policy,
  start = WARMUP,
  end = universe.dates.length - 1,
  keepCurve = true,
  constantRisk?: number,
): BacktestResult {
  const w = sampleWindow();
  const rs: number[] = [];
  const trainRs: number[] = [];
  const valRs: number[] = [];
  const oosRs: number[] = [];
  const curve: CurvePoint[] = [];
  let equity = 1;
  let peak = 1;
  let prevRisk = 0;
  let turns = 0;
  for (let i = Math.max(WARMUP, start); i <= end; i++) {
    const s = state(i - 1);
    const dd = equity / peak - 1;
    const risk = constantRisk != null ? Math.max(0, Math.min(1, constantRisk)) : riskFor(s, dd, policy);
    const r = rawReturn(strategy, i, policy);
    if (r == null) continue;
    if (Math.abs(risk - prevRisk) > 1e-6) turns += 1;
    prevRisk = risk;
    const realized = risk * r;
    equity *= 1 + realized;
    peak = Math.max(peak, equity);
    rs.push(realized);
    if (i <= w.trainEnd) trainRs.push(realized);
    else if (i <= w.valEnd) valRs.push(realized);
    else oosRs.push(realized);
    if (keepCurve) {
      curve.push({
        i,
        date: universe.dates[i],
        equity,
        drawdown: equity / peak - 1,
        regime: s.regime,
        risk,
        qqq: ret("QQQ", i),
        vxx: ret("VXX", i),
        strategyReturn: realized,
      });
    }
  }
  const turnover = rs.length ? turns / rs.length : 0;
  const validation = metrics(valRs, turnover);
  return {
    strategy,
    policy,
    metrics: metrics(rs, turnover),
    curve,
    split: {
      train: metrics(trainRs, turnover),
      validation,
      oos: metrics(oosRs, turnover),
    },
    score: validationScore(validation),
    proxy: PROXY_STRATEGIES.includes(strategy),
    oosLeakage: false,
  };
}

export const DEFAULT_POLICY: Policy = {
  baseRisk: 1,
  unstableRisk: 0.5,
  tailRisk: 0.05,
  recoveryRisk: 0.7,
  vxxHedge: 0.1,
  ddBrake: 0.025,
};

export const BUY_HOLD_QQQ_POLICY: Policy = {
  baseRisk: 1,
  unstableRisk: 1,
  tailRisk: 1,
  recoveryRisk: 1,
  vxxHedge: 0,
  ddBrake: 1,
};

export const STRATEGIES: StrategyId[] = [
  "QQQ",
  "QQQ_VXX",
  "COVERED_PROXY",
  "PROTECTED_PROXY",
  "CONVEX_PROXY",
];

export function policyGrid(): Policy[] {
  const out: Policy[] = [];
  for (const unstableRisk of [0.35, 0.5, 0.65]) {
    for (const tailRisk of [0.02, 0.05, 0.1]) {
      for (const ddBrake of [0.015, 0.025, 0.035]) {
        for (const vxxHedge of [0, 0.08, 0.12, 0.18]) {
          out.push({
            baseRisk: 1,
            unstableRisk,
            tailRisk,
            recoveryRisk: 0.7,
            vxxHedge,
            ddBrake,
          });
        }
      }
    }
  }
  return out;
}

/** TRAIN+VALIDATION only. OOS never enters ranking. Curves omitted to keep search cheap. */
export function searchPolicies(strategy: StrategyId): BacktestResult[] {
  const w = sampleWindow();
  const results = policyGrid().map((p) => runBacktest(strategy, p, w.start, w.valEnd, false));
  return results.sort((a, b) => b.score - a.score);
}

export function freezeChampion(candidates: BacktestResult[]): BacktestResult {
  const best = candidates[0];
  if (!best) {
    return runBacktest("QQQ", DEFAULT_POLICY);
  }
  const w = sampleWindow();
  return runBacktest(best.strategy, best.policy, w.start, w.end, true);
}

export function competeAll(): { candidates: BacktestResult[]; champion: BacktestResult } {
  const w = sampleWindow();
  const candidates: BacktestResult[] = [];
  for (const s of STRATEGIES) {
    for (const p of policyGrid()) {
      candidates.push(runBacktest(s, p, w.start, w.valEnd, false));
    }
  }
  candidates.sort((a, b) => b.score - a.score);
  const champion = freezeChampion(candidates);
  return { candidates, champion };
}

export function buyHoldQQQ(): BacktestResult {
  const w = sampleWindow();
  // Overlay none: 100% QQQ every bar. The 4.5% hard second brake is a state-risk
  // overlay artifact and must not leak into the Observed buy-and-hold path.
  return runBacktest("QQQ", BUY_HOLD_QQQ_POLICY, w.start, w.end, false, 1);
}

export function freezeSpotChampion(): BacktestResult {
  const w = sampleWindow();
  const candidates: BacktestResult[] = [];
  for (const s of ["QQQ", "QQQ_VXX"] as StrategyId[]) {
    for (const p of policyGrid()) {
      candidates.push(runBacktest(s, p, w.start, w.valEnd, false));
    }
  }
  candidates.sort((a, b) => b.score - a.score);
  return freezeChampion(candidates);
}

export function pareto(results: BacktestResult[]) {
  return results.filter(
    (a) =>
      !results.some(
        (b) =>
          b !== a &&
          b.split.validation.cagr >= a.split.validation.cagr &&
          b.split.validation.maxDd >= a.split.validation.maxDd &&
          (b.split.validation.cagr > a.split.validation.cagr ||
            b.split.validation.maxDd > a.split.validation.maxDd),
      ),
  );
}

export function targetGate(r: Metrics, cagrTarget = 0.12, ddTarget = -0.05) {
  return {
    cagrPass: r.cagr >= cagrTarget,
    ddPass: r.maxDd >= ddTarget,
    pass: r.cagr >= cagrTarget && r.maxDd >= ddTarget,
    cagrTarget,
    ddTarget,
  };
}

export function historicalBenchmark() {
  return {
    label: "historical benchmark (not V2 result)",
    cagr: 0.1252,
    maxDd: -0.2351,
    winRate: 0.562,
    profitFactor: 1.74,
    sharpe: 0.88,
    sortino: 1.26,
    trades: 104,
  };
}

/** Guard: QQQ_VXX must actually move when vxxHedge changes on a VXX-present bar. */
export function assertVxxHedgeIsLive(): { ok: true; sampleDate: string; r0: number; r18: number } {
  const cov = coverage();
  if (cov.vxxStartIndex < 0) throw new Error("VXX_HEDGE_GUARD: no VXX bars");
  let i = -1;
  for (let k = cov.vxxStartIndex + 2; k < universe.dates.length; k++) {
    const v = ret("VXX", k);
    if (v != null && Math.abs(v) > 0.01) {
      i = k;
      break;
    }
  }
  if (i < 0) throw new Error("VXX_HEDGE_GUARD: no VXX move to test");
  const z: Policy = { ...DEFAULT_POLICY, vxxHedge: 0 };
  const h: Policy = { ...DEFAULT_POLICY, vxxHedge: 0.18 };
  const r0 = rawReturn("QQQ_VXX", i, z);
  const r18 = rawReturn("QQQ_VXX", i, h);
  if (r0 == null || r18 == null) throw new Error("VXX_HEDGE_GUARD: null returns");
  if (Math.abs(r0 - r18) < 1e-12) {
    throw new Error(`VXX_HEDGE_GUARD: vxxHedge unused on ${universe.dates[i]} (r0=${r0} r18=${r18})`);
  }
  return { ok: true, sampleDate: universe.dates[i], r0, r18 };
}
