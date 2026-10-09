import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type Strategy = "CLOCK" | "DIP_10_12M_ONE_SLICE" | "ORACLE_2X_CEILING";

type QqqData = { source: string; asof: string; dates: string[]; c: { QQQ?: Array<number | null> } };
type MonthlyPoint = { date: string; close: number };

type WindowResult = {
  startDate: string;
  endDate: string;
  clockTerminal: number;
  dipTerminal: number;
  oracleTerminal: number;
  dipDeltaTerminal: number;
  oracleDeltaTerminal: number;
  clockMaxDd: number;
  dipMaxDd: number;
  oracleMaxDd: number;
  dipDeltaMaxDd: number;
  scheduleMoves: number;
  schedulePeakFraction: number;
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H = 120;
const TRIGGER_DD = -0.10;

function finitePositive(x: unknown): number | null {
  const n = Number(x);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function monthlyQqq(data: QqqData): MonthlyPoint[] {
  const dates = data.dates ?? [];
  const closes = data.c.QQQ ?? [];
  const byMonth = new Map<string, MonthlyPoint>();
  for (let i = 0; i < Math.min(dates.length, closes.length); i++) {
    const close = finitePositive(closes[i]);
    const date = dates[i];
    if (close == null || !/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;
    const key = date.slice(0, 7);
    const prev = byMonth.get(key);
    if (!prev || date > prev.date) byMonth.set(key, { date, close });
  }
  return [...byMonth.values()].sort((a, b) => a.date.localeCompare(b.date));
}

function dd12(prices: number[], i: number): number {
  const lo = Math.max(0, i - 11);
  const peak = Math.max(...prices.slice(lo, i + 1));
  return prices[i] / peak - 1;
}

function clockSchedule(): number[] {
  return [0, ...Array.from({ length: H }, () => 1 / H)];
}

function dipSchedule(prices: number[]): { schedule: number[]; moves: number } {
  const schedule = clockSchedule();
  let moves = 0;
  for (let i = 12; i <= H; i++) {
    if (dd12(prices, i) > TRIGGER_DD) continue;
    let donor = -1;
    for (let j = H; j > i; j--) {
      if (schedule[j] > 1e-12) { donor = j; break; }
    }
    if (donor > i) {
      schedule[i] += schedule[donor];
      schedule[donor] = 0;
      moves += 1;
    }
  }
  return { schedule, moves };
}

function oracle2xSchedule(prices: number[]): number[] {
  const schedule = Array.from({ length: H + 1 }, () => 0);
  const rows = prices
    .slice(1, H + 1)
    .map((price, j) => ({ month: j + 1, terminalMultiplier: prices[H] / price }))
    .sort((a, b) => b.terminalMultiplier - a.terminalMultiplier);
  let remaining = 1;
  for (const row of rows) {
    const add = Math.min(2 / H, remaining);
    schedule[row.month] = add;
    remaining -= add;
    if (remaining <= 1e-12) break;
  }
  if (Math.abs(remaining) > 1e-10) throw new Error("oracle schedule did not allocate all capital");
  return schedule;
}

function equityFromSchedule(prices: number[], schedule: number[]): number[] {
  let investedShares = 0;
  let cumulativeInvested = 0;
  const curve = [1];
  for (let i = 1; i < prices.length; i++) {
    investedShares += schedule[i] / prices[i];
    cumulativeInvested += schedule[i];
    const cash = Math.max(0, 1 - cumulativeInvested);
    curve.push(cash + investedShares * prices[i]);
  }
  return curve;
}

function terminal(prices: number[], schedule: number[]): number {
  const end = prices[H];
  return schedule.slice(1, H + 1).reduce((sum, weight, i) => sum + weight * (end / prices[i + 1]), 0);
}

function maxDd(curve: number[]): number {
  let peak = -Infinity;
  let out = 0;
  for (const x of curve) {
    peak = Math.max(peak, x);
    out = Math.min(out, x / Math.max(1e-12, peak) - 1);
  }
  return out;
}

function selectCompleteWindows(months: MonthlyPoint[]) {
  const out: Array<{ start: number; end: number }> = [];
  for (let start = 0; start + H < months.length; start++) out.push({ start, end: start + H });
  return out;
}

function shockPrices(base: number[], month: number, shock: number): number[] {
  if (month < 1 || month > H) throw new Error("shock month out of range");
  return base.map((x, i) => (i >= month ? x * (1 + shock) : x));
}

function runWindow(basePrices: number[], mode: Strategy) {
  const schedule =
    mode === "CLOCK"
      ? clockSchedule()
      : mode === "DIP_10_12M_ONE_SLICE"
        ? dipSchedule(basePrices).schedule
        : oracle2xSchedule(basePrices);
  const equity = equityFromSchedule(basePrices, schedule);
  return { schedule, terminal: equity.at(-1) ?? 1, maxDd: maxDd(equity) };
}

function summarize(xs: number[]) {
  const sorted = [...xs].sort((a, b) => a - b);
  const mean = xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length);
  const q = (p: number) => {
    if (!sorted.length) return null;
    const x = (sorted.length - 1) * p;
    const lo = Math.floor(x);
    const hi = Math.ceil(x);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (x - lo);
  };
  return {
    n: xs.length,
    mean,
    median: q(0.5),
    q05: q(0.05),
    q25: q(0.25),
    q75: q(0.75),
    q95: q(0.95),
    positiveRate: xs.length ? xs.filter((x) => x > 0).length / xs.length : 0,
  };
}

function curvature(wealths: number[]) {
  const [w0, w10, w20] = wealths;
  if (![w0, w10, w20].every(Number.isFinite)) return NaN;
  return (w20 ?? NaN) - 2 * (w10 ?? NaN) + (w0 ?? NaN);
}

function main() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as QqqData;
  const months = monthlyQqq(data);
  const windows = selectCompleteWindows(months);
  const results: WindowResult[] = [];

  for (const { start, end } of windows) {
    const prices = months.slice(start, end + 1).map((x) => x.close);
    const clock = runWindow(prices, "CLOCK");
    const dipState = dipSchedule(prices);
    const dip = runWindow(prices, "DIP_10_12M_ONE_SLICE");
    const oracle = runWindow(prices, "ORACLE_2X_CEILING");
    results.push({
      startDate: months[start].date,
      endDate: months[end].date,
      clockTerminal: clock.terminal,
      dipTerminal: dip.terminal,
      oracleTerminal: oracle.terminal,
      dipDeltaTerminal: dip.terminal - clock.terminal,
      oracleDeltaTerminal: oracle.terminal - clock.terminal,
      clockMaxDd: clock.maxDd,
      dipMaxDd: dip.maxDd,
      oracleMaxDd: oracle.maxDd,
      dipDeltaMaxDd: dip.maxDd - clock.maxDd,
      scheduleMoves: dipState.moves,
      schedulePeakFraction: Math.max(...dipState.schedule),
    });
  }

  const shockMonths = [24, 60, 96];
  const shocks = [0, -0.10, -0.20, -0.30];
  const curvatureRows: Array<Record<string, number | string>> = [];
  for (const { start, end } of windows.slice(0, Math.min(80, windows.length))) {
    const base = months.slice(start, end + 1).map((x) => x.close);
    for (const mode of ["CLOCK", "DIP_10_12M_ONE_SLICE"] as const) {
      const frozen = runWindow(base, mode).schedule;
      for (const month of shockMonths) {
        const frozenWealths = shocks.map((s) => terminal(shockPrices(base, month, s), frozen));
        const pathAwareWealths = shocks.map((s) => runWindow(shockPrices(base, month, s), mode).terminal);
        curvatureRows.push({
          startDate: months[start].date,
          endDate: months[end].date,
          mode,
          shockMonth: month,
          frozenCurvature_0_10_20: curvature(frozenWealths),
          pathAwareCurvature_0_10_20: curvature(pathAwareWealths),
        });
      }
    }
  }

  const invariantFailures: string[] = [];
  for (const row of results) {
    const prices = months
      .slice(months.findIndex((x) => x.date === row.startDate), months.findIndex((x) => x.date === row.endDate) + 1)
      .map((x) => x.close);
    for (const mode of ["CLOCK", "DIP_10_12M_ONE_SLICE", "ORACLE_2X_CEILING"] as const) {
      const schedule = runWindow(prices, mode).schedule;
      const total = schedule.reduce((a, b) => a + b, 0);
      if (Math.abs(total - 1) > 1e-10) invariantFailures.push(row.startDate + " " + mode + " total=" + total);
      if (schedule.some((x) => x < -1e-12)) invariantFailures.push(row.startDate + " " + mode + " negative allocation");
    }
    if (row.schedulePeakFraction > 2 / H + 1e-10) {
      invariantFailures.push(row.startDate + " DIP peak>2x monthly slice");
    }
    if (row.clockMaxDd <= -0.999999999) {
      invariantFailures.push(row.startDate + " clock equity collapsed to zero; cash accounting broken");
    }
  }
  const frozenCurvatureMax = Math.max(
    0,
    ...curvatureRows
      .map((x) => Math.abs(Number(x.frozenCurvature_0_10_20)))
      .filter(Number.isFinite),
  );
  if (frozenCurvatureMax > 1e-8) {
    invariantFailures.push("frozen schedule curvature exceeds tolerance: " + frozenCurvatureMax);
  }
  if (invariantFailures.length) throw new Error("RESEARCH_INVARIANT_FAIL " + invariantFailures.slice(0, 8).join(" | "));

  const report = {
    researchId: "QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1",
    status: "RESEARCH_ONLY",
    data: { source: "src/data/universe.json", sourceAsOf: data.asof, monthlyPoints: months.length, completeRollingWindows: windows.length, overlap: true },
    fixedRules: {
      trigger: "trailing_12M_drawdown <= -10%",
      action: "move exactly one future 1/120 slice into current month; donor is latest month with undistributed slice",
      oracle: "hindsight 2x/month deployment ceiling, diagnostic ceiling only",
    },
    terminal: {
      dipVsClock: summarize(results.map((x) => x.dipDeltaTerminal)),
      oracleVsClock: summarize(results.map((x) => x.oracleDeltaTerminal)),
    },
    maxDd: { dipVsClock: summarize(results.map((x) => x.dipDeltaMaxDd)) },
    deployment: {
      dipMoves: summarize(results.map((x) => x.scheduleMoves)),
      dipPeakMonthlyFraction: summarize(results.map((x) => x.schedulePeakFraction)),
    },
    convexity: {
      frozenSchedule: summarize(curvatureRows.map((x) => Number(x.frozenCurvature_0_10_20)).filter(Number.isFinite)),
      pathAwareDip: summarize(curvatureRows.filter((x) => x.mode === "DIP_10_12M_ONE_SLICE").map((x) => Number(x.pathAwareCurvature_0_10_20)).filter(Number.isFinite)),
      interpretation: "Frozen schedule is the mechanical payoff test. Path-aware curvature can only come from the deployment policy changing exposure after the shock.",
      shockSet: shocks,
      shockMonths,
    },
    windows: results,
    curvatureRows,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_hybrid_downside_convexity_v1.json"), JSON.stringify(report, null, 2));

  const csvHeader = ["startDate","endDate","clockTerminal","dipTerminal","oracleTerminal","dipDeltaTerminal","oracleDeltaTerminal","clockMaxDd","dipMaxDd","oracleMaxDd","dipDeltaMaxDd","scheduleMoves","schedulePeakFraction"];
  const csvRows = results.map((x) => csvHeader.map((h) => JSON.stringify((x as Record<string, unknown>)[h])).join(","));
  writeFileSync(resolve(OUT_DIR, "qqq_hybrid_downside_convexity_v1.csv"), csvHeader.join(",") + "\n" + csvRows.join("\n") + "\n");

  const md = [
    "# QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1",
    "",
    "> RESEARCH_ONLY. No product authority. No funding instruction.",
    "",
    "## Historical deployment value",
    "",
    "DIP terminal delta vs CLOCK:",
    JSON.stringify(report.terminal.dipVsClock),
    "",
    "Oracle 2x ceiling delta vs CLOCK:",
    JSON.stringify(report.terminal.oracleVsClock),
    "",
    "DIP MaxDD delta vs CLOCK:",
    JSON.stringify(report.maxDd.dipVsClock),
    "",
    "## Convexity",
    "",
    "Frozen-schedule curvature (0/-10/-20 shock):",
    JSON.stringify(report.convexity.frozenSchedule),
    "",
    "Path-aware DIP curvature:",
    JSON.stringify(report.convexity.pathAwareDip),
    "",
    "Frozen curvature is the mechanical payoff test. A pure long/cash timing schedule should be affine in a permanent level shock; non-zero curvature beyond numerical tolerance must be audited.",
    "",
    "## Limitation",
    "",
    "The ORACLE uses hindsight by definition and is never an executable candidate. All rolling windows overlap. This V1 does not claim an option-like convex payoff from deployment timing. A true non-linear hedge must be tested separately against its premium and fill/data assumptions.",
    "",
  ].join("\n");
  writeFileSync(resolve(OUT_DIR, "qqq_hybrid_downside_convexity_v1.md"), md);
  console.log(md);
}

main();