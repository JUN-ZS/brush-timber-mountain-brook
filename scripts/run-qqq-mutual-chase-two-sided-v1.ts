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
  terminalEconomicReturn: number;
  terminalEconomicCagr: number;
  rawAccountMaxDd: number;
  economicMaxDd: number;
  postRebalanceMaxDd: number;
  principalBreach: boolean;
  minEconomicWealth: number;
  finalPlannedReserve: number;
  finalHarvestReserve: number;
};

type PathResult = {
  startDate: string;
  endDate: string;
  clock: Metrics;
  twoSided: Metrics;
  delta: {
    terminalEconomicWealth: number;
    economicMaxDd: number;
    rawAccountMaxDd: number;
    externalContribution: number;
    harvestToReserve: number;
  };
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H = 120;
const B = 1;
// V1 execution convention: month-end close is both the mark and the rebalance price; no next-month information is used.

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

function emptyMetrics(): Metrics {
  return {
    totalExternalContribution: 0,
    contributionEvents: 0,
    totalHarvestToReserve: 0,
    harvestEvents: 0,
    terminalNav: 0,
    terminalEconomicWealth: B,
    terminalEconomicReturn: 0,
    terminalEconomicCagr: 0,
    rawAccountMaxDd: 0,
    economicMaxDd: 0,
    postRebalanceMaxDd: 0,
    principalBreach: false,
    minEconomicWealth: B,
    finalPlannedReserve: B,
    finalHarvestReserve: 0,
  };
}

function simulateClock(prices: number[]): Metrics {
  let shares = 0;
  let plannedReserve = B;
  const harvestReserve = 0;
  let totalExternalContribution = 0;
  const rawNavCurve = [0];
  const economicCurve = [B];
  const postRebalanceCurve = [0];

  for (let t = 1; t <= H; t++) {
    const c = Math.min(plannedReserve, B / H);
    plannedReserve -= c;
    totalExternalContribution += c;
    shares += c / prices[t];

    const nav = shares * prices[t];
    const economic = nav + plannedReserve + harvestReserve;
    rawNavCurve.push(nav);
    economicCurve.push(economic);
    postRebalanceCurve.push(nav);
  }

  const terminalNav = rawNavCurve[H];
  const terminalEconomicWealth = economicCurve[H];
  return {
    ...emptyMetrics(),
    totalExternalContribution,
    contributionEvents: H,
    terminalNav,
    terminalEconomicWealth,
    terminalEconomicReturn: terminalEconomicWealth - B,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, terminalEconomicWealth / B), 1 / 10) - 1,
    rawAccountMaxDd: maxDd(rawNavCurve.slice(1)),
    economicMaxDd: maxDd(economicCurve),
    postRebalanceMaxDd: maxDd(postRebalanceCurve.slice(1)),
    principalBreach: terminalEconomicWealth < B - 1e-10,
    minEconomicWealth: Math.min(...economicCurve),
    finalPlannedReserve: plannedReserve,
    finalHarvestReserve: harvestReserve,
  };
}

/**
 * TWO-SIDED MUTUAL CHASE:
 * - target account capital C_t = B*t/120.
 * - At each month-end, first mark current holdings at that month's close.
 * - If raw NAV > C_t, SELL the excess at the same close and move proceeds into harvest reserve.
 * - If raw NAV < C_t, buy the shortfall at the same close.
 *   Harvest reserve is reused first; planned reserve is used second and is counted as external contribution.
 * - Planned reserve can move at most B in total; no borrowing.
 * - All decisions use only current/past data. No future price is read.
 *
 * The post-rebalance account NAV is intentionally the target whenever economic wealth allows it.
 * Therefore post-rebalance account MaxDD is not an informative risk metric; raw pre-rebalance
 * market NAV MaxDD and whole-economic-wealth MaxDD are the meaningful diagnostics.
 */
function simulateTwoSided(prices: number[]): Metrics {
  let shares = 0;
  let plannedReserve = B;
  let harvestReserve = 0;
  let totalExternalContribution = 0;
  let contributionEvents = 0;
  let totalHarvestToReserve = 0;
  let harvestEvents = 0;

  const rawNavCurve = [0];
  const economicCurve = [B];
  const postRebalanceCurve = [0];

  for (let t = 1; t <= H; t++) {
    const target = (t / H) * B;

    // Strict causal rule:
    // the dollar amount of this month's BUY/SELL is fixed using only t-1 close NAV.
    // The actual transfer executes at t close. No t-close information is used to set the amount.
    const prevPrice = prices[t - 1];
    const prevNav = shares * prevPrice;

    if (prevNav > target + 1e-12) {
      // Lock only the prior-close excess. Price slippage/market movement until t close is intentionally retained.
      const sellAmountAtPrevClose = prevNav - target;
      const sellShares = Math.min(shares, sellAmountAtPrevClose / Math.max(prevPrice, 1e-12));
      const proceedsAtCurrentClose = sellShares * prices[t];
      shares -= sellShares;
      harvestReserve += proceedsAtCurrentClose;
      totalHarvestToReserve += proceedsAtCurrentClose;
      if (proceedsAtCurrentClose > 1e-12) harvestEvents += 1;
    } else if (prevNav < target - 1e-12) {
      let need = target - prevNav;

      // Recycle previously harvested gains first.
      const fromHarvest = Math.min(harvestReserve, need);
      harvestReserve -= fromHarvest;
      need -= fromHarvest;

      // Then consume the remaining planned B budget.
      const fromPlanned = Math.min(plannedReserve, need);
      plannedReserve -= fromPlanned;
      totalExternalContribution += fromPlanned;
      if (fromPlanned > 1e-12) contributionEvents += 1;

      const used = fromHarvest + fromPlanned;
      if (used > 0) shares += used / prices[t];
      // Any residual need is deliberately left unfunded: no borrowing and no extra B.
    }

    const preRebalanceNav = shares * prices[t];
    const economic = preRebalanceNav + plannedReserve + harvestReserve;
    rawNavCurve.push(preRebalanceNav);
    economicCurve.push(economic);
    postRebalanceCurve.push(preRebalanceNav);
  }

  const terminalNav = postRebalanceCurve[H];
  const terminalEconomicWealth = economicCurve[H];

  return {
    ...emptyMetrics(),
    totalExternalContribution,
    contributionEvents,
    totalHarvestToReserve,
    harvestEvents,
    terminalNav,
    terminalEconomicWealth,
    terminalEconomicReturn: terminalEconomicWealth - B,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, terminalEconomicWealth / B), 1 / 10) - 1,
    rawAccountMaxDd: maxDd(rawNavCurve.slice(1)),
    economicMaxDd: maxDd(economicCurve),
    postRebalanceMaxDd: maxDd(postRebalanceCurve.slice(1)),
    principalBreach: terminalEconomicWealth < B - 1e-10,
    minEconomicWealth: Math.min(...economicCurve),
    finalPlannedReserve: plannedReserve,
    finalHarvestReserve: harvestReserve,
  };
}

function run() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as QqqData;
  const months = monthlyQqq(data);
  const windows: Array<{ start: number; end: number }> = [];
  for (let start = 0; start + H < months.length; start++) windows.push({ start, end: start + H });

  const results: PathResult[] = [];

  for (const { start, end } of windows) {
    const prices = months.slice(start, end + 1).map((x) => x.close);
    const clock = simulateClock(prices);
    const twoSided = simulateTwoSided(prices);
    results.push({
      startDate: months[start].date,
      endDate: months[end].date,
      clock,
      twoSided,
      delta: {
        terminalEconomicWealth: twoSided.terminalEconomicWealth - clock.terminalEconomicWealth,
        economicMaxDd: twoSided.economicMaxDd - clock.economicMaxDd,
        rawAccountMaxDd: twoSided.rawAccountMaxDd - clock.rawAccountMaxDd,
        externalContribution: twoSided.totalExternalContribution - clock.totalExternalContribution,
        harvestToReserve: twoSided.totalHarvestToReserve,
      },
    });
  }

  const failures: string[] = [];
  for (const r of results) {
    if (r.clock.totalExternalContribution > B + 1e-8) failures.push(r.startDate + " CLOCK budget violation");
    if (r.twoSided.totalExternalContribution > B + 1e-8) failures.push(r.startDate + " two-sided external budget violation");
    if (r.twoSided.finalPlannedReserve < -1e-8 || r.twoSided.finalHarvestReserve < -1e-8) failures.push(r.startDate + " negative reserve");
    if (!Number.isFinite(r.twoSided.terminalEconomicWealth)) failures.push(r.startDate + " non-finite economic wealth");
  }
  if (failures.length) throw new Error("TWO_SIDED_MUTUAL_CHASE_INVARIANT_FAIL " + failures.slice(0, 10).join(" | "));

  const deltaTerminal = results.map((r) => r.delta.terminalEconomicWealth);
  const deltaEconomicDd = results.map((r) => r.delta.economicMaxDd);
  const deltaRawDd = results.map((r) => r.delta.rawAccountMaxDd);
  const extContribution = results.map((r) => r.twoSided.totalExternalContribution);
  const harvest = results.map((r) => r.twoSided.totalHarvestToReserve);
  const breach = results.filter((r) => r.twoSided.principalBreach).length;

  const report = {
    researchId: "QQQ_MUTUAL_CHASE_TWO_SIDED_V1",
    status: "RESEARCH_ONLY",
    question: "Does two-sided NAV chasing—buying below the rising capital target and selling above it—improve capital preservation versus CLOCK?",
    data: {
      source: "src/data/universe.json",
      sourceAsOf: data.asof,
      monthlyPoints: months.length,
      completeRollingWindows: windows.length,
      overlap: true,
    },
    fixedRule: {
      target: "C_t = B * t / 120",
      trigger: "Every month-end; compare current marked NAV with C_t.",
      belowTarget: "Buy exactly the shortfall; reuse harvested reserve first, then planned reserve.",
      aboveTarget: "SELL exactly the excess and move proceeds to harvest reserve.",
      externalBudget: "Planned reserve starts at B and cannot be replenished by external capital beyond B.",
      borrowing: false,
      parameterSearch: false,
      futurePriceRead: false,
      note: "Post-rebalance NAV is mechanically near C_t; post-rebalance account MaxDD is therefore not an informative primary risk measure.",
    },
    comparison: {
      against: "CLOCK = B/120 each month, no tactical sell.",
      primaryRisk: "raw account MaxDD before month-end rebalance and whole-economic-wealth MaxDD.",
    },
    twoSidedVsClock: {
      terminalEconomicWealthDelta: summarize(deltaTerminal),
      economicMaxDdDelta: summarize(deltaEconomicDd),
      rawAccountMaxDdDelta: summarize(deltaRawDd),
      externalContributionFraction: summarize(extContribution),
      harvestToReserveFraction: summarize(harvest),
      principalBreachWindows: breach,
      principalBreachRate: breach / Math.max(1, results.length),
      contributionEvents: summarize(results.map((r) => r.twoSided.contributionEvents)),
      harvestEvents: summarize(results.map((r) => r.twoSided.harvestEvents)),
    },
    windows: results,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_two_sided_v1.json"), JSON.stringify(report, null, 2));

  const md = [
    "# QQQ_MUTUAL_CHASE_TWO_SIDED_V1",
    "",
    "> RESEARCH_ONLY. No formal 10Y Floor authority. No BUY/SELL execution authority.",
    "",
    "## Fixed two-sided rule",
    "",
    "At each month-end, define C_t = B*t/120 and compare current marked account NAV with C_t.",
    "",
    "- NAV below C_t: BUY the shortfall, using harvested reserve first and planned reserve second.",
    "- NAV above C_t: SELL the excess and place proceeds in harvest reserve.",
    "- Planned reserve begins at B; external capital cannot exceed B in total; no borrowing.",
    "",
    "This is deliberately symmetric: gains can become reserve, and later losses can pull that reserve back into QQQ.",
    "",
    "## Results",
    "",
    "Two-sided terminal economic wealth delta vs CLOCK:",
    JSON.stringify(report.twoSidedVsClock.terminalEconomicWealthDelta),
    "",
    "Two-sided economic-wealth MaxDD delta vs CLOCK:",
    JSON.stringify(report.twoSidedVsClock.economicMaxDdDelta),
    "",
    "Two-sided raw pre-rebalance account MaxDD delta vs CLOCK:",
    JSON.stringify(report.twoSidedVsClock.rawAccountMaxDdDelta),
    "",
    "External contribution fraction:",
    JSON.stringify(report.twoSidedVsClock.externalContributionFraction),
    "",
    "Harvest-to-reserve fraction:",
    JSON.stringify(report.twoSidedVsClock.harvestToReserveFraction),
    "",
    "Principal-breach windows:",
    report.twoSidedVsClock.principalBreachWindows + " / " + windows.length,
    "",
    "## Interpretation guardrail",
    "",
    "The strategy is a two-sided capital-recycling rule, not an option hedge. Selling gains can reduce later exposure and therefore may reduce drawdown at the cost of upside. Results must be judged on whole economic wealth because sales and buys are internal transfers between account and reserve.",
    "",
  ].join("\n");
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_two_sided_v1.md"), md);

  const csvHeader = [
    "startDate","endDate",
    "clockTerminalEconomicWealth","twoSidedTerminalEconomicWealth","deltaTerminalEconomicWealth",
    "clockRawAccountMaxDd","twoSidedRawAccountMaxDd","deltaRawAccountMaxDd",
    "clockEconomicMaxDd","twoSidedEconomicMaxDd","deltaEconomicMaxDd",
    "twoSidedExternalContribution","twoSidedHarvestToReserve",
    "twoSidedContributionEvents","twoSidedHarvestEvents","twoSidedPrincipalBreach"
  ];
  const csvRows = results.map((r) => [
    r.startDate,r.endDate,
    r.clock.terminalEconomicWealth,r.twoSided.terminalEconomicWealth,r.delta.terminalEconomicWealth,
    r.clock.rawAccountMaxDd,r.twoSided.rawAccountMaxDd,r.delta.rawAccountMaxDd,
    r.clock.economicMaxDd,r.twoSided.economicMaxDd,r.delta.economicMaxDd,
    r.twoSided.totalExternalContribution,r.twoSided.totalHarvestToReserve,
    r.twoSided.contributionEvents,r.twoSided.harvestEvents,r.twoSided.principalBreach
  ].map((x) => JSON.stringify(x)).join(","));
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_two_sided_v1.csv"), csvHeader.join(",") + "\n" + csvRows.join("\n") + "\n");

  console.log(md);
}

run();
