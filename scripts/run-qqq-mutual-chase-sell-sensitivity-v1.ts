import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData = { source: string; asof: string; dates: string[]; c: { QQQ?: Array<number | null> } };
type MonthlyPoint = { date: string; close: number };

type Metrics = {
  totalExternalContribution: number;
  contributionEvents: number;
  totalHarvestToReserve: number;
  harvestEvents: number;
  terminalNav: number;
  terminalEconomicWealth: number;
  terminalEconomicCagr: number;
  rawAccountMaxDd: number;
  economicMaxDd: number;
  principalBreach: boolean;
};

type SensitivityPath = {
  startDate: string;
  endDate: string;
  clock: Metrics;
  alphas: Record<string, Metrics>;
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H = 120;
const B = 1;

// Pre-registered before result inspection. Do not expand from observed results.
const SELL_FRACTIONS = [0, 0.10, 0.25, 0.50, 0.75, 1.00] as const;

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

function maxDd(curve: number[]): number {
  let peak = 0;
  let out = 0;
  for (const x of curve) {
    peak = Math.max(peak, x);
    if (peak > 1e-12) out = Math.min(out, x / peak - 1);
  }
  return out;
}

function emptyMetrics(): Metrics {
  return {
    totalExternalContribution: 0,
    contributionEvents: 0,
    totalHarvestToReserve: 0,
    harvestEvents: 0,
    terminalNav: 0,
    terminalEconomicWealth: B,
    terminalEconomicCagr: 0,
    rawAccountMaxDd: 0,
    economicMaxDd: 0,
    principalBreach: false,
  };
}

function simulate(prices: number[], sellFraction: number): Metrics {
  let shares = 0;
  let plannedReserve = B;
  let harvestReserve = 0;
  let totalExternalContribution = 0;
  let contributionEvents = 0;
  let totalHarvestToReserve = 0;
  let harvestEvents = 0;

  const rawNavCurve = [0];
  const economicCurve = [B];

  for (let t = 1; t <= H; t++) {
    const target = (t / H) * B;

    // Strict causal decision: t-month transfer size uses only t-1 close NAV.
    const prevPrice = prices[t - 1];
    const prevNav = shares * prevPrice;

    if (prevNav > target + 1e-12 && sellFraction > 0) {
      const excess = prevNav - target;
      const sellAmountAtPrevClose = sellFraction * excess;
      const sellShares = Math.min(shares, sellAmountAtPrevClose / Math.max(prevPrice, 1e-12));
      const proceedsAtCurrentClose = sellShares * prices[t];

      shares -= sellShares;
      harvestReserve += proceedsAtCurrentClose;
      totalHarvestToReserve += proceedsAtCurrentClose;
      if (proceedsAtCurrentClose > 1e-12) harvestEvents += 1;
    } else if (prevNav < target - 1e-12) {
      let need = target - prevNav;

      // Reuse harvested profits first.
      const fromHarvest = Math.min(harvestReserve, need);
      harvestReserve -= fromHarvest;
      need -= fromHarvest;

      // Then use the fixed planned principal budget.
      const fromPlanned = Math.min(plannedReserve, need);
      plannedReserve -= fromPlanned;
      totalExternalContribution += fromPlanned;
      if (fromPlanned > 1e-12) contributionEvents += 1;

      const used = fromHarvest + fromPlanned;
      if (used > 0) shares += used / prices[t];
      // No borrowing when the reserve budget is exhausted.
    }

    const nav = shares * prices[t];
    const economic = nav + plannedReserve + harvestReserve;
    rawNavCurve.push(nav);
    economicCurve.push(economic);
  }

  const terminalNav = rawNavCurve[H];
  const terminalEconomicWealth = economicCurve[H];

  return {
    ...emptyMetrics(),
    totalExternalContribution,
    contributionEvents,
    totalHarvestToReserve,
    harvestEvents,
    terminalNav,
    terminalEconomicWealth,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, terminalEconomicWealth / B), 1 / 10) - 1,
    rawAccountMaxDd: maxDd(rawNavCurve.slice(1)),
    economicMaxDd: maxDd(economicCurve),
    principalBreach: terminalEconomicWealth < B - 1e-10,
  };
}

function summarize(xs: number[]) {
  const sorted = [...xs].sort((a, b) => a - b);
  const mean = xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length);
  const q = (p: number) => {
    if (!sorted.length) return 0;
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

function run() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as QqqData;
  const months = monthlyQqq(data);
  const windows: Array<{ start: number; end: number }> = [];
  for (let start = 0; start + H < months.length; start++) windows.push({ start, end: start + H });

  const paths: SensitivityPath[] = [];

  for (const { start, end } of windows) {
    const prices = months.slice(start, end + 1).map((x) => x.close);
    const clock = simulate(prices, 0);

    const alphas: Record<string, Metrics> = {};
    for (const alpha of SELL_FRACTIONS) {
      alphas[alpha.toFixed(2)] = simulate(prices, alpha);
    }

    paths.push({
      startDate: months[start].date,
      endDate: months[end].date,
      clock,
      alphas,
    });
  }

  const failures: string[] = [];
  for (const path of paths) {
    if (path.clock.totalExternalContribution > B + 1e-8) {
      failures.push(path.startDate + " CLOCK budget violation");
    }
    for (const alpha of SELL_FRACTIONS) {
      const m = path.alphas[alpha.toFixed(2)];
      if (m.totalExternalContribution > B + 1e-8) failures.push(path.startDate + " alpha " + alpha + " external budget violation");
      if (m.principalBreach) failures.push(path.startDate + " alpha " + alpha + " principal breach");
      if (!Number.isFinite(m.terminalEconomicWealth)) failures.push(path.startDate + " alpha " + alpha + " non-finite");
    }
  }
  if (failures.length) throw new Error("SELL_SENSITIVITY_INVARIANT_FAIL " + failures.slice(0, 20).join(" | "));

  const rows = SELL_FRACTIONS.map((alpha) => {
    const key = alpha.toFixed(2);
    const r = paths.map((p) => {
      const m = p.alphas[key];
      return {
        alpha,
        deltaTerminal: m.terminalEconomicWealth - p.clock.terminalEconomicWealth,
        deltaRawDd: m.rawAccountMaxDd - p.clock.rawAccountMaxDd,
        deltaEconomicDd: m.economicMaxDd - p.clock.economicMaxDd,
        cagr: m.terminalEconomicCagr,
        cagrDeltaPp: (m.terminalEconomicCagr - p.clock.terminalEconomicCagr) * 100,
        externalContribution: m.totalExternalContribution,
        harvest: m.totalHarvestToReserve,
        terminal: m.terminalEconomicWealth,
        terminalBelowB: m.terminalEconomicWealth < B,
      };
    });

    const cagrDeltas = r.map((x) => x.cagrDeltaPp);
    const rawDd = r.map((x) => x.deltaRawDd);
    const econDd = r.map((x) => x.deltaEconomicDd);
    const terminal = r.map((x) => x.deltaTerminal);
    const external = r.map((x) => x.externalContribution);
    const harvest = r.map((x) => x.harvest);
    const drag = Math.max(0, -summarize(cagrDeltas).mean);
    const ddImprove = summarize(rawDd).mean * 100;

    return {
      alpha,
      windows: paths.length,
      terminalDelta: summarize(terminal),
      rawMaxDdDelta: summarize(rawDd),
      economicMaxDdDelta: summarize(econDd),
      terminalCagr: summarize(r.map((x) => x.cagr)),
      cagrDeltaPp: summarize(cagrDeltas),
      externalContribution: summarize(external),
      harvestToReserve: summarize(harvest),
      positiveVsClock: r.filter((x) => x.deltaTerminal > 0).length,
      belowB: r.filter((x) => x.terminalBelowB).length,
      drawdownImprovementPerCagrPp: drag > 1e-12 ? ddImprove / drag : null,
    };
  });

  const report = {
    researchId: "QQQ_MUTUAL_CHASE_SELL_SENSITIVITY_V1",
    status: "RESEARCH_ONLY",
    provenance: {
      source: "src/data/universe.json",
      sourceAsOf: data.asof,
      monthlyPoints: months.length,
      completeRollingWindows: windows.length,
      overlappingWindows: true,
    },
    fixedRule: {
      target: "C_t = B*t/120",
      buy: "Full shortfall below target, after harvested reserve reuse.",
      sell: "SELL = alpha * max(0, NAV_(t-1) - C_t).",
      sellFractions: [...SELL_FRACTIONS],
      decisionData: "NAV at t-1 month-end close only.",
      execution: "t month-end close.",
      borrowing: false,
      parameterSearch: false,
      winnerSelection: false,
      note: "Alpha is the only changed research variable; all other mutual-chase mechanics are held fixed."
    },
    comparison: {
      baseline: "CLOCK = B/120 every month, no tactical SELL and no performance-based BUY/SELL.",
      terminalMetric: "whole economic wealth = NAV + planned reserve + harvested reserve.",
      drawdownMetrics: "raw pre-rebalance account MaxDD and whole-economic-wealth MaxDD."
    },
    sensitivity: rows,
    windows: paths
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_sell_sensitivity_v1.json"), JSON.stringify(report, null, 2));

  const md = [
    "# QQQ_MUTUAL_CHASE_SELL_SENSITIVITY_V1",
    "",
    "> RESEARCH_ONLY / DIAGNOSTIC_ONLY. No formal Floor authority.",
    "",
    "Pre-registered SELL fractions:",
    SELL_FRACTIONS.map((x) => (x * 100) + "%").join(", "),
    "",
    "Rule: BUY remains full shortfall-chase; SELL = alpha * max(0, NAV_(t-1) - C_t); C_t = B*t/120.",
    "",
    "No future price read. No parameter search. All 153+ rolling windows are reported as a sensitivity surface, not a winner-selection exercise.",
    "",
    "## Aggregated trade-off",
    "",
    "| SELL alpha | Mean terminal ΔB | Mean raw MaxDD Δ | Mean economic MaxDD Δ | Mean CAGR Δ (pp) | Positive terminal vs CLOCK | Below B terminal | Mean external contribution |",
    "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...rows.map((x) => "| " + (x.alpha * 100).toFixed(0) + "% | " +
      x.terminalDelta.mean.toFixed(6) + " | " +
      (x.rawMaxDdDelta.mean * 100).toFixed(3) + " pp | " +
      (x.economicMaxDdDelta.mean * 100).toFixed(3) + " pp | " +
      x.cagrDeltaPp.mean.toFixed(3) + " pp | " +
      x.positiveVsClock + "/" + paths.length + " | " +
      x.belowB + "/" + paths.length + " | " +
      (x.externalContribution.mean * 100).toFixed(3) + "% |").join("\n"),
    "",
    "## Interpretation",
    "",
    "Positive MaxDD delta means the drawdown is less negative, i.e. an improvement.",
    "",
    "This experiment does not define a universal acceptable CAGR loss. The intended output is the shape of the Pareto trade-off: how much drawdown relief is purchased for each unit of compounding sacrificed.",
    "",
    "No alpha is promoted automatically."
  ].join("\n");

  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_sell_sensitivity_v1.md"), md);

  const csvHeader = [
    "startDate","endDate","alpha",
    "clockTerminalEconomicWealth","terminalEconomicWealth","deltaTerminalEconomicWealth",
    "clockRawAccountMaxDd","rawAccountMaxDd","deltaRawAccountMaxDd",
    "clockEconomicMaxDd","economicMaxDd","deltaEconomicMaxDd",
    "terminalEconomicCagr","cagrDeltaPp",
    "externalContribution","harvestToReserve","principalBreach"
  ];

  const csvLines = [csvHeader.join(",")];
  for (const p of paths) {
    for (const alpha of SELL_FRACTIONS) {
      const m = p.alphas[alpha.toFixed(2)];
      csvLines.push([
        p.startDate,p.endDate,alpha.toFixed(2),
        p.clock.terminalEconomicWealth,m.terminalEconomicWealth,m.terminalEconomicWealth-p.clock.terminalEconomicWealth,
        p.clock.rawAccountMaxDd,m.rawAccountMaxDd,m.rawAccountMaxDd-p.clock.rawAccountMaxDd,
        p.clock.economicMaxDd,m.economicMaxDd,m.economicMaxDd-p.clock.economicMaxDd,
        m.terminalEconomicCagr,(m.terminalEconomicCagr-p.clock.terminalEconomicCagr)*100,
        m.totalExternalContribution,m.totalHarvestToReserve,m.principalBreach
      ].map((x) => JSON.stringify(x)).join(","));
    }
  }

  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_sell_sensitivity_v1.csv"), csvLines.join("\n") + "\n");
  console.log(md);
}

run();

// Fixed sensitivity runner trigger: workflow was preregistered before this commit.
