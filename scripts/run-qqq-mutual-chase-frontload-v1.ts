import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type Data = { asof: string; dates: string[]; c: { QQQ?: Array<number | null> } };
type MP = { date: string; close: number };
type Metrics = {
  targetMonth1: number;
  terminalEconomicWealth: number;
  terminalEconomicCagr: number;
  rawMaxDd: number;
  economicMaxDd: number;
  externalContribution: number;
  harvestToReserve: number;
  reserveBuyUsed: number;
  buyEvents: number;
  sellEvents: number;
  grossBuy: number;
  grossSell: number;
  avgGrossTurnover: number;
  avgNetExternalContribution: number;
  terminalPlannedReserve: number;
  terminalHarvestReserve: number;
  principalBreach: boolean;
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H = 120;
const B = 1;
const FRONTLOADS = Array.from({ length: 11 }, (_, i) => i / 10);

function monthly(data: Data): MP[] {
  const out = new Map<string, MP>();
  for (let i = 0; i < Math.min(data.dates.length, (data.c.QQQ ?? []).length); i++) {
    const date = data.dates[i];
    const close = Number((data.c.QQQ ?? [])[i]);
    if (!Number.isFinite(close) || close <= 0 || !/^\\d{4}-\\d{2}-\\d{2}$/.test(date)) continue;
    const key = date.slice(0, 7);
    const prior = out.get(key);
    if (!prior || date > prior.date) out.set(key, { date, close });
  }
  return [...out.values()].sort((a, b) => a.date.localeCompare(b.date));
}

function maxDd(xs: number[]): number {
  let peak = 0;
  let out = 0;
  for (const x of xs) {
    peak = Math.max(peak, x);
    if (peak > 1e-12) out = Math.min(out, x / peak - 1);
  }
  return out;
}

function summarize(xs: number[]) {
  const s = [...xs].sort((a, b) => a - b);
  const mean = xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length);
  const q = (p: number) => {
    if (!s.length) return 0;
    const z = (s.length - 1) * p;
    const lo = Math.floor(z), hi = Math.ceil(z);
    return s[lo] + (s[hi] - s[lo]) * (z - lo);
  };
  return {
    n: xs.length, mean, median: q(0.5),
    q05: q(0.05), q25: q(0.25), q75: q(0.75), q95: q(0.95),
    positiveRate: xs.filter((x) => x > 0).length / Math.max(1, xs.length),
  };
}

function target(F: number, t: number): number {
  return F * B + (1 - F) * B * (t / H);
}

function simulate(prices: number[], F: number): Metrics {
  let shares = 0;
  let plannedReserve = B;
  let harvestReserve = 0;
  let externalContribution = 0;
  let harvestToReserve = 0;
  let reserveBuyUsed = 0;
  let buyEvents = 0;
  let sellEvents = 0;
  let grossBuy = 0;
  let grossSell = 0;
  const raw = [0];
  const economic = [B];

  for (let t = 1; t <= H; t++) {
    const targetT = target(F, t);
    const prevPrice = prices[t - 1];
    const prevNav = shares * prevPrice;

    if (prevNav > targetT + 1e-12) {
      const sellAmountPrev = prevNav - targetT;
      const sellShares = Math.min(shares, sellAmountPrev / Math.max(prevPrice, 1e-12));
      const proceeds = sellShares * prices[t];
      if (sellShares > 0) {
        shares -= sellShares;
        harvestReserve += proceeds;
        harvestToReserve += proceeds;
        grossSell += proceeds;
        sellEvents++;
      }
    } else if (prevNav < targetT - 1e-12) {
      let need = targetT - prevNav;

      const fromHarvest = Math.min(harvestReserve, need);
      harvestReserve -= fromHarvest;
      need -= fromHarvest;
      reserveBuyUsed += fromHarvest;

      const fromPlanned = Math.min(plannedReserve, need);
      plannedReserve -= fromPlanned;
      need -= fromPlanned;
      externalContribution += fromPlanned;

      const used = fromHarvest + fromPlanned;
      if (used > 0) {
        shares += used / prices[t];
        grossBuy += used;
        buyEvents++;
      }
    }

    const nav = shares * prices[t];
    raw.push(nav);
    economic.push(nav + plannedReserve + harvestReserve);
  }

  const ew = economic[H];
  return {
    targetMonth1: target(F, 1),
    terminalEconomicWealth: ew,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, ew / B), 1 / 10) - 1,
    rawMaxDd: maxDd(raw.slice(1)),
    economicMaxDd: maxDd(economic),
    externalContribution,
    harvestToReserve,
    reserveBuyUsed,
    buyEvents,
    sellEvents,
    grossBuy,
    grossSell,
    avgGrossTurnover: (grossBuy + grossSell) / H,
    avgNetExternalContribution: externalContribution / H,
    terminalPlannedReserve: plannedReserve,
    terminalHarvestReserve: harvestReserve,
    principalBreach: ew < B - 1e-10,
  };
}

type Row = { start: string; end: string; byF: Record<string, Metrics> };

function compare(rows: Row[], F: number) {
  const key = F.toFixed(1);
  const base = "0.0";
  const terminal = rows.map((r) => r.byF[key].terminalEconomicWealth - r.byF[base].terminalEconomicWealth);
  const rawDd = rows.map((r) => (r.byF[key].rawMaxDd - r.byF[base].rawMaxDd) * 100);
  const ecoDd = rows.map((r) => (r.byF[key].economicMaxDd - r.byF[base].economicMaxDd) * 100);
  const cagr = rows.map((r) => (r.byF[key].terminalEconomicCagr - r.byF[base].terminalEconomicCagr) * 100);
  return {
    terminalDelta: summarize(terminal),
    rawMaxDdDeltaPp: summarize(rawDd),
    economicMaxDdDeltaPp: summarize(ecoDd),
    cagrDeltaPp: summarize(cagr),
    higherTerminalWindows: terminal.filter((x) => x > 0).length,
    lowerEconomicDdWindows: ecoDd.filter((x) => x < 0).length,
    lowerRawDdWindows: rawDd.filter((x) < 0).length,
  };
}

function run() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as Data;
  const months = monthly(data);
  if (months.length < H + 1) throw new Error("NOT_ENOUGH_MONTHLY_DATA");

  const rows: Row[] = [];
  for (let s = 0; s + H < months.length; s++) {
    const prices = months.slice(s, s + H + 1).map((x) => x.close);
    const byF: Record<string, Metrics> = {};
    for (const F of FRONTLOADS) byF[F.toFixed(1)] = simulate(prices, F);
    if (Math.abs(target(0, 1) - B / H) > 1e-12) throw new Error("CLOCK_TARGET_MISMATCH");
    if (Math.abs(target(1, 120) - B) > 1e-12) throw new Error("FULL_FRONTLOAD_ENDPOINT_MISMATCH");
    rows.push({ start: months[s].date, end: months[s + H].date, byF });
  }

  const failures: string[] = [];
  for (const row of rows) {
    for (const F of FRONTLOADS) {
      const m = row.byF[F.toFixed(1)];
      if (m.externalContribution > B + 1e-8) failures.push(row.start + " F=" + F + " budget");
      if (m.terminalPlannedReserve < -1e-8 || m.terminalHarvestReserve < -1e-8) failures.push(row.start + " F=" + F + " reserve");
      if (!Number.isFinite(m.terminalEconomicWealth)) failures.push(row.start + " F=" + F + " nonfinite");
    }
  }
  if (failures.length) throw new Error("FRONTLOAD_INVARIANT_FAIL " + failures.slice(0, 20).join(" | "));

  const summary = FRONTLOADS.map((F) => {
    const xs = rows.map((r) => r.byF[F.toFixed(1)]);
    return {
      frontload: F,
      targetMonth1: target(F, 1),
      terminalEconomicWealth: summarize(xs.map((x) => x.terminalEconomicWealth)),
      terminalCagrPct: summarize(xs.map((x) => x.terminalEconomicCagr * 100)),
      rawMaxDdPct: summarize(xs.map((x) => x.rawMaxDd * 100)),
      economicMaxDdPct: summarize(xs.map((x) => x.economicMaxDd * 100)),
      externalContributionPct: summarize(xs.map((x) => x.externalContribution * 100)),
      harvestPct: summarize(xs.map((x) => x.harvestToReserve * 100)),
      reserveBuyUsedPct: summarize(xs.map((x) => x.reserveBuyUsed * 100)),
      buyEvents: summarize(xs.map((x) => x.buyEvents)),
      sellEvents: summarize(xs.map((x) => x.sellEvents)),
      avgGrossTurnoverPctBPerMonth: summarize(xs.map((x) => x.avgGrossTurnover * 100)),
      terminalPlannedReservePct: summarize(xs.map((x) => x.terminalPlannedReserve * 100)),
      terminalHarvestReservePct: summarize(xs.map((x) => x.terminalHarvestReserve * 100)),
      principalBreachWindows: xs.filter((x) => x.principalBreach).length,
    };
  });

  const comparisons = Object.fromEntries(FRONTLOADS.map((F) => [F.toFixed(1), compare(rows, F)]));

  const report = {
    researchId: "QQQ_MUTUAL_CHASE_FRONTLOAD_V1",
    status: "RESEARCH_ONLY",
    provenance: {
      source: "src/data/universe.json",
      sourceAsOf: data.asof,
      monthlyPoints: months.length,
      completeRollingWindows: rows.length,
      overlappingWindows: true,
    },
    fixedRules: {
      totalBudget: "B=1",
      horizon: H,
      targetCurve: "C_t(F)=F*B+(1-F)*B*t/120",
      frontloadGrid: FRONTLOADS,
      decisionTiming: "BUY/SELL dollar amount uses only prior month-end NAV versus current target.",
      execution: "t month-end close",
      externalBudgetCap: B,
      borrowing: false,
      futurePriceRead: false,
      parameterSearch: false,
      targetReset: false,
    },
    summary,
    comparisonsVsClock: comparisons,
    windows: rows,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_frontload_v1.json"), JSON.stringify(report, null, 2));

  const md = [
    "# QQQ_MUTUAL_CHASE_FRONTLOAD_V1",
    "",
    "> RESEARCH_ONLY / DIAGNOSTIC_ONLY.",
    "",
    "C_t(F) = F*B + (1-F)*B*t/120. F=0 is CLOCK; F=1 targets full B from month 1.",
    "",
    "| Frontload | Month-1 target %B | Mean terminal EW | Mean CAGR | Mean raw MaxDD | Mean economic MaxDD | Mean external contribution | Mean gross turnover/month |",
    "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...summary.map((r) => "| " + (r.frontload*100).toFixed(0) + "% | " + (r.targetMonth1*100).toFixed(2) + "% | " + r.terminalEconomicWealth.mean.toFixed(6) + " B | " + r.terminalCagrPct.mean.toFixed(3) + "% | " + r.rawMaxDdPct.mean.toFixed(3) + "% | " + r.economicMaxDdPct.mean.toFixed(3) + "% | " + r.externalContributionPct.mean.toFixed(3) + "%B | " + r.avgGrossTurnoverPctBPerMonth.mean.toFixed(3) + "%B |"),
    "",
    "| Frontload | Mean terminal ΔB vs CLOCK | Mean CAGR Δ pp | Mean raw MaxDD Δ pp | Mean economic MaxDD Δ pp | Higher terminal | Lower economic MaxDD |",
    "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...FRONTLOADS.map((F) => {
      const r = comparisons[F.toFixed(1)];
      return "| " + (F*100).toFixed(0) + "% | " + r.terminalDelta.mean.toFixed(6) + " | " + r.cagrDeltaPp.mean.toFixed(3) + " | " + r.rawMaxDdDeltaPp.mean.toFixed(3) + " | " + r.economicMaxDdDeltaPp.mean.toFixed(3) + " | " + r.higherTerminalWindows + "/" + rows.length + " | " + r.lowerEconomicDdWindows + "/" + rows.length + " |";
    }),
    "",
    "Interpretation: this measures budget-curve timing plus endogenous BUY/SELL recycling. It is not an entry-timing prediction and no front-load level is promoted automatically.",
  ].join("\\n");
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_frontload_v1.md"), md);

  const header = [
    "start","end","frontload","targetMonth1","terminalEW","terminalCagr","rawMaxDd","economicMaxDd",
    "externalContribution","harvestToReserve","reserveBuyUsed","buyEvents","sellEvents","grossBuy","grossSell",
    "avgGrossTurnover","avgNetExternalContribution","terminalPlannedReserve","terminalHarvestReserve","principalBreach",
  ].join(",");
  const lines = [header];
  for (const row of rows) for (const F of FRONTLOADS) {
    const m = row.byF[F.toFixed(1)];
    lines.push([
      row.start,row.end,F,m.targetMonth1,m.terminalEconomicWealth,m.terminalEconomicCagr,m.rawMaxDd,m.economicMaxDd,
      m.externalContribution,m.harvestToReserve,m.reserveBuyUsed,m.buyEvents,m.sellEvents,m.grossBuy,m.grossSell,
      m.avgGrossTurnover,m.avgNetExternalContribution,m.terminalPlannedReserve,m.terminalHarvestReserve,m.principalBreach,
    ].map((x) => JSON.stringify(x)).join(","));
  }
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_frontload_v1.csv"), lines.join("\\n") + "\\n");
  console.log(JSON.stringify({ provenance: report.provenance, summary: report.summary, comparisonsVsClock: report.comparisonsVsClock }, null, 2));
}

run();
