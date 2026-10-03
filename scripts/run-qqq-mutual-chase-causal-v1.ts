import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData = {
  source: string;
  asof: string;
  dates: string[];
  c: { QQQ?: Array<number | null> };
};

type MonthlyPoint = { date: string; close: number };

type PathResult = {
  startDate: string;
  endDate: string;
  clock: Metrics;
  mutualChase: Metrics;
  delta: DeltaMetrics;
};

type Metrics = {
  totalContribution: number;
  contributionCount: number;
  terminalNav: number;
  terminalEconomicWealth: number;
  terminalEconomicReturn: number;
  terminalEconomicCagr: number;
  accountMaxDd: number;
  economicMaxDd: number;
  principalBreach: boolean;
  minEconomicWealth: number;
};

type DeltaMetrics = {
  terminalEconomicWealth: number;
  terminalEconomicReturn: number;
  accountMaxDd: number;
  economicMaxDd: number;
  totalContribution: number;
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H = 120;
const B = 1;

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

function clockContribution(t: number): number {
  return 1 / H;
}

function accountMaxDd(curve: number[]): number {
  let peak = 0;
  let out = 0;
  for (const x of curve) {
    peak = Math.max(peak, x);
    if (peak > 1e-12) out = Math.min(out, x / peak - 1);
  }
  return out;
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

function simulateClock(prices: number[]): Metrics {
  let shares = 0;
  let totalContribution = 0;
  const navCurve = [0];
  const economicCurve = [B];
  let contributionCount = 0;

  for (let t = 1; t <= H; t++) {
    const c = clockContribution(t);
    totalContribution += c;
    contributionCount += 1;
    shares += c / prices[t];
    const nav = shares * prices[t];
    const reserve = Math.max(0, B - totalContribution);
    navCurve.push(nav);
    economicCurve.push(nav + reserve);
  }

  const terminalNav = navCurve[H];
  const terminalEconomicWealth = economicCurve[H];
  return {
    totalContribution,
    contributionCount,
    terminalNav,
    terminalEconomicWealth,
    terminalEconomicReturn: terminalEconomicWealth - B,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, terminalEconomicWealth / B), 1 / 10) - 1,
    accountMaxDd: accountMaxDd(navCurve.slice(1)),
    economicMaxDd: accountMaxDd(economicCurve),
    principalBreach: terminalEconomicWealth < B - 1e-10,
    minEconomicWealth: Math.min(...economicCurve),
  };
}

/**
 * CAUSAL MUTUAL CHASE:
 * - B starts outside the investment account as reserve.
 * - Month t target is C_t = t/H * B.
 * - Contribution decision uses ONLY prior month-end NAV.
 * - Contribution_t = max(0, C_t - NAV_{t-1}), capped by remaining B.
 * - This means prior gains can reduce future contributions, while prior losses can increase them.
 * - No future price is read. No borrowing. No parameter search.
 */
function simulateMutualChase(prices: number[]): Metrics {
  let shares = 0;
  let nav = 0;
  let totalContribution = 0;
  let contributionCount = 0;
  const navCurve = [0];
  const economicCurve = [B];

  for (let t = 1; t <= H; t++) {
    const target = (t / H) * B;
    const remainingBudget = Math.max(0, B - totalContribution);
    const contribution = Math.min(remainingBudget, Math.max(0, target - nav));

    if (contribution > 1e-12) {
      totalContribution += contribution;
      contributionCount += 1;
      shares += contribution / prices[t];
    }

    nav = shares * prices[t];
    const reserve = Math.max(0, B - totalContribution);
    navCurve.push(nav);
    economicCurve.push(nav + reserve);
  }

  const terminalNav = navCurve[H];
  const terminalEconomicWealth = economicCurve[H];
  return {
    totalContribution,
    contributionCount,
    terminalNav,
    terminalEconomicWealth,
    terminalEconomicReturn: terminalEconomicWealth - B,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, terminalEconomicWealth / B), 1 / 10) - 1,
    accountMaxDd: accountMaxDd(navCurve.slice(1)),
    economicMaxDd: accountMaxDd(economicCurve),
    principalBreach: terminalEconomicWealth < B - 1e-10,
    minEconomicWealth: Math.min(...economicCurve),
  };
}

function run() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as QqqData;
  const months = monthlyQqq(data);
  const windows: Array<{ start: number; end: number }> = [];
  for (let start = 0; start + H < months.length; start++) {
    windows.push({ start, end: start + H });
  }

  const results: PathResult[] = [];

  for (const { start, end } of windows) {
    const prices = months.slice(start, end + 1).map((x) => x.close);
    const clock = simulateClock(prices);
    const mutualChase = simulateMutualChase(prices);
    results.push({
      startDate: months[start].date,
      endDate: months[end].date,
      clock,
      mutualChase,
      delta: {
        terminalEconomicWealth: mutualChase.terminalEconomicWealth - clock.terminalEconomicWealth,
        terminalEconomicReturn: mutualChase.terminalEconomicReturn - clock.terminalEconomicReturn,
        accountMaxDd: mutualChase.accountMaxDd - clock.accountMaxDd,
        economicMaxDd: mutualChase.economicMaxDd - clock.economicMaxDd,
        totalContribution: mutualChase.totalContribution - clock.totalContribution,
      },
    });
  }

  // Sanity checks: the strategy may leave B outside the account, but can never contribute > B.
  const failures: string[] = [];
  for (const row of results) {
    if (row.mutualChase.totalContribution < -1e-10 || row.mutualChase.totalContribution > B + 1e-10) {
      failures.push(row.startDate + " contribution budget violation");
    }
    if (!Number.isFinite(row.mutualChase.terminalEconomicWealth)) {
      failures.push(row.startDate + " non-finite terminal wealth");
    }
    if (row.clock.totalContribution !== B) failures.push(row.startDate + " clock did not deploy exactly B");
    if (row.clock.terminalEconomicWealth < -1e-10 || row.mutualChase.terminalEconomicWealth < -1e-10) {
      failures.push(row.startDate + " negative economic wealth");
    }
  }
  if (failures.length) throw new Error("MUTUAL_CHASE_INVARIANT_FAIL " + failures.slice(0, 10).join(" | "));

  const deltaTerminal = results.map((r) => r.delta.terminalEconomicWealth);
  const deltaAccountDd = results.map((r) => r.delta.accountMaxDd);
  const deltaEconomicDd = results.map((r) => r.delta.economicMaxDd);
  const deltaContribution = results.map((r) => r.delta.totalContribution);
  const chaseContribution = results.map((r) => r.mutualChase.totalContribution);
  const chaseBreaches = results.filter((r) => r.mutualChase.principalBreach).length;

  const firstMonthAndEarlyRows = results.filter((r) => r.mutualChase.contributionCount > 0).map((r) => ({
    startDate: r.startDate,
    firstMonthPrice: months.find((m) => m.date === r.startDate)?.close ?? null,
    contribution: r.mutualChase.totalContribution,
    terminalEconomicReturn: r.mutualChase.terminalEconomicReturn,
  }));

  const report = {
    researchId: "QQQ_MUTUAL_CHASE_CAUSAL_V1",
    status: "RESEARCH_ONLY",
    question: "Can prior investment performance causally reduce or increase future external contributions while preserving the original B budget, and does that help terminal economic wealth or drawdown?",
    data: {
      source: "src/data/universe.json",
      sourceAsOf: data.asof,
      monthlyPoints: months.length,
      completeRollingWindows: windows.length,
      overlap: true,
    },
    fixedRule: {
      target: "C_t = B * t / 120",
      decisionTiming: "Month t contribution uses only NAV at month t-1 close.",
      contribution: "max(0, C_t - NAV_{t-1}), capped by remaining external budget B.",
      reserve: "B - cumulative contribution remains outside the investment account and is included in economic wealth.",
      noBorrowing: true,
      noParameterSearch: true,
      noFuturePriceRead: true,
    },
    comparison: {
      against: "CLOCK = exactly B/120 invested each month.",
      note: "Account NAV and whole-economic-wealth drawdown are both reported because reduced contribution leaves capital in reserve.",
    },
    mutualChaseVsClock: {
      terminalEconomicWealthDelta: summarize(deltaTerminal),
      accountMaxDdDelta: summarize(deltaAccountDd),
      economicMaxDdDelta: summarize(deltaEconomicDd),
      contributionDelta: summarize(deltaContribution),
      totalContributionFraction: summarize(chaseContribution),
      principalBreachWindows: chaseBreaches,
      principalBreachRate: chaseBreaches / Math.max(1, results.length),
    },
    windows: results,
    auditSample: firstMonthAndEarlyRows.slice(0, 20),
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_causal_v1.json"), JSON.stringify(report, null, 2));

  const md = [
    "# QQQ_MUTUAL_CHASE_CAUSAL_V1",
    "",
    "> RESEARCH_ONLY. No formal 10Y Floor authority. No BUY/SELL signal.",
    "",
    "## Fixed causal rule",
    "",
    "At month t, target capital is C_t = B·t/120.",
    "The contribution decision uses only the previous month-end NAV:",
    "",
    "Contribution_t = min(B - cumulative contribution, max(0, C_t - NAV_{t-1})).",
    "",
    "So prior gains can suppress future contributions; prior losses can increase them.",
    "Any unspent portion of B stays outside the investment account and is counted in whole-economic wealth.",
    "",
    "## Results",
    "",
    "Mutual-chase vs CLOCK terminal economic wealth delta:",
    JSON.stringify(report.mutualChaseVsClock.terminalEconomicWealthDelta),
    "",
    "Mutual-chase vs CLOCK account MaxDD delta:",
    JSON.stringify(report.mutualChaseVsClock.accountMaxDdDelta),
    "",
    "Mutual-chase vs CLOCK economic-wealth MaxDD delta:",
    JSON.stringify(report.mutualChaseVsClock.economicMaxDdDelta),
    "",
    "Mutual-chase total contribution fraction:",
    JSON.stringify(report.mutualChaseVsClock.totalContributionFraction),
    "",
    "Windows with terminal economic wealth below B:",
    report.mutualChaseVsClock.principalBreachWindows + " / " + windows.length,
    "",
    "## Interpretation guardrail",
    "",
    "This experiment is intentionally not a 'better return by investing less' claim. Economic wealth = account NAV + uninvested reserve, so skipped contributions are still capital owned outside the account.",
    "The only allowed feedback is prior realized path information through NAV_{t-1}; there is no future price read and no parameter search.",
    "",
  ].join("\n");
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_causal_v1.md"), md);

  const csvHeader = [
    "startDate","endDate",
    "clockTerminalEconomicWealth","mutualChaseTerminalEconomicWealth","deltaTerminalEconomicWealth",
    "clockAccountMaxDd","mutualChaseAccountMaxDd","deltaAccountMaxDd",
    "clockEconomicMaxDd","mutualChaseEconomicMaxDd","deltaEconomicMaxDd",
    "clockTotalContribution","mutualChaseTotalContribution","deltaTotalContribution",
    "mutualChaseContributionCount","mutualChasePrincipalBreach"
  ];
  const csvRows = results.map((r) => [
    r.startDate, r.endDate,
    r.clock.terminalEconomicWealth, r.mutualChase.terminalEconomicWealth, r.delta.terminalEconomicWealth,
    r.clock.accountMaxDd, r.mutualChase.accountMaxDd, r.delta.accountMaxDd,
    r.clock.economicMaxDd, r.mutualChase.economicMaxDd, r.delta.economicMaxDd,
    r.clock.totalContribution, r.mutualChase.totalContribution, r.delta.totalContribution,
    r.mutualChase.contributionCount, r.mutualChase.principalBreach
  ].map((x) => JSON.stringify(x)).join(","));
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_causal_v1.csv"), csvHeader.join(",") + "\n" + csvRows.join("\n") + "\n");

  console.log(md);
}

run();
