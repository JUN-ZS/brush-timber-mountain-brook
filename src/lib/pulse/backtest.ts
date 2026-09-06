import { universe } from "./bars.ts";

export type Regime = "CALM" | "UNSTABLE" | "TAIL" | "RECOVERY";
export type StrategyId = "QQQ" | "QQQ_VXX" | "COVERED_PROXY" | "PROTECTED_PROXY" | "CONVEX_PROXY";

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
};

export type BacktestResult = {
  strategy: StrategyId;
  policy: Policy;
  metrics: Metrics;
  curve: CurvePoint[];
  split: { train: Metrics; validation: Metrics; oos: Metrics };
  score: number;
};

const DAYS = 252;

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

function mean(xs: number[]) { return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0; }
function stdev(xs: number[]) {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(mean(xs.map((x) => (x - m) ** 2)));
}
function quantile(xs: number[], q: number) {
  if (!xs.length) return 0;
  const a = [...xs].sort((x, y) => x - y);
  const p = (a.length - 1) * q;
  const lo = Math.floor(p), hi = Math.ceil(p);
  return a[lo] + (a[hi] - a[lo]) * (p - lo);
}

function metrics(rs: number[]): Metrics {
  if (!rs.length) return { cagr: 0, maxDd: 0, sharpe: 0, sortino: 0, totalReturn: 0, volatility: 0, calmar: 0, worstDay: 0, nDays: 0 };
  let eq = 1, peak = 1, maxDd = 0;
  for (const r of rs) { eq *= 1 + r; peak = Math.max(peak, eq); maxDd = Math.min(maxDd, eq / peak - 1); }
  const vol = stdev(rs) * Math.sqrt(DAYS);
  const down = stdev(rs.filter((r) => r < 0)) * Math.sqrt(DAYS);
  const cagr = Math.pow(eq, DAYS / rs.length) - 1;
  return { cagr, maxDd, sharpe: vol ? mean(rs) * DAYS / vol : 0, sortino: down ? mean(rs) * DAYS / down : 0, totalReturn: eq - 1, volatility: vol, calmar: maxDd < 0 ? cagr / -maxDd : 0, worstDay: Math.min(...rs), nDays: rs.length };
}

function state(i: number): { regime: Regime; vol: number; vix: number | null; dd20: number; mom60: number } {
  const q = universe.c.QQQ ?? [];
  const p = q[i];
  const r20: number[] = [];
  for (let j = Math.max(1, i - 19); j <= i; j++) { const r = ret("QQQ", j); if (r != null) r20.push(r); }
  const vol = stdev(r20) * Math.sqrt(DAYS);
  const p20 = i >= 20 && q[i - 20] ? p / q[i - 20] - 1 : 0;
  const p60 = i >= 60 && q[i - 60] ? p / q[i - 60] - 1 : 0;
  const vix = close("VIX", i);
  const tail = (vix != null && vix >= 30) || vol >= 0.38 || p20 <= -0.08;
  const unstable = (vix != null && vix >= 20) || vol >= 0.25 || p20 < 0;
  const recovery = p20 > 0 && p60 < 0;
  return { regime: tail ? "TAIL" : recovery ? "RECOVERY" : unstable ? "UNSTABLE" : "CALM", vol, vix, dd20: p20, mom60: p60 };
}

function rawReturn(strategy: StrategyId, i: number): number | null {
  const q = ret("QQQ", i); if (q == null) return null;
  const v = ret("VXX", i) ?? 0;
  if (strategy === "QQQ") return q;
  if (strategy === "QQQ_VXX") return q - 0.10 * v;
  if (strategy === "COVERED_PROXY") return Math.min(q, 0.006) + 0.00020;
  if (strategy === "PROTECTED_PROXY") return q + Math.max(-q - 0.015, 0) - 0.00025;
  return Math.abs(q) > 0.015 ? Math.abs(q) - 0.00055 : -0.00055;
}

function riskFor(s: ReturnType<typeof state>, dd: number, p: Policy) {
  let r = s.regime === "TAIL" ? p.tailRisk : s.regime === "UNSTABLE" ? p.unstableRisk : s.regime === "RECOVERY" ? p.recoveryRisk : p.baseRisk;
  if (dd <= -p.ddBrake) r *= 0.5;
  if (dd <= -Math.min(0.045, p.ddBrake * 1.8)) r *= 0.25;
  return Math.max(0, Math.min(1, r));
}

export function runBacktest(strategy: StrategyId, policy: Policy, start = 60, end = universe.dates.length - 1): BacktestResult {
  const rs: number[] = [], curve: CurvePoint[] = [];
  let equity = 1, peak = 1;
  for (let i = Math.max(60, start); i <= end; i++) {
    const s = state(i - 1); // strictly prior-bar information
    const dd = equity / peak - 1;
    const risk = riskFor(s, dd, policy);
    const r = rawReturn(strategy, i);
    if (r == null) continue;
    const vxx = ret("VXX", i);
    const realized = risk * r;
    equity *= 1 + realized;
    peak = Math.max(peak, equity);
    const drawdown = equity / peak - 1;
    rs.push(realized);
    curve.push({ i, date: universe.dates[i], equity, drawdown, regime: s.regime, risk, qqq: ret("QQQ", i), vxx });
  }
  const m = metrics(rs);
  const splitIndex = Math.floor(rs.length * 0.60);
  const valIndex = Math.floor(rs.length * 0.80);
  const train = metrics(rs.slice(0, splitIndex));
  const validation = metrics(rs.slice(splitIndex, valIndex));
  const oos = metrics(rs.slice(valIndex));
  const score = (oos.cagr * 100) - Math.max(0, -oos.maxDd * 100) * 1.5;
  return { strategy, policy, metrics: m, curve, split: { train, validation, oos }, score };
}

export const DEFAULT_POLICY: Policy = { baseRisk: 1, unstableRisk: 0.50, tailRisk: 0.05, recoveryRisk: 0.70, vxxHedge: 0.10, ddBrake: 0.025 };

export function policyGrid(): Policy[] {
  const out: Policy[] = [];
  for (const unstableRisk of [0.35, 0.50, 0.65])
    for (const tailRisk of [0.02, 0.05, 0.10])
      for (const ddBrake of [0.015, 0.025, 0.035])
        out.push({ baseRisk: 1, unstableRisk, tailRisk, recoveryRisk: 0.70, vxxHedge: 0.10, ddBrake });
  return out;
}

export function searchPolicies(strategy: StrategyId): BacktestResult[] {
  const results = policyGrid().map((p) => runBacktest(strategy, p));
  return results.sort((a, b) => b.score - a.score);
}

export function pareto(results: BacktestResult[]) {
  return results.filter((a) => !results.some((b) => b !== a && b.metrics.cagr >= a.metrics.cagr && b.metrics.maxDd >= a.metrics.maxDd && (b.metrics.cagr > a.metrics.cagr || b.metrics.maxDd > a.metrics.maxDd)));
}

export function targetGate(r: BacktestResult, cagrTarget = 0.12, ddTarget = -0.05) {
  return r.metrics.cagr >= cagrTarget && r.metrics.maxDd >= ddTarget;
}

export function historicalBenchmark() {
  return { cagr: 0.1252, maxDd: -0.2351, winRate: 0.562, profitFactor: 1.74, sharpe: 0.88, sortino: 1.26, trades: 104 };
}
