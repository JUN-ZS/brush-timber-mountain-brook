import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { buildConditionalPriceLadder, type PricePathSample } from "../src/lib/floor/yahoo-live.ts";
import {
  activePaperOrders,
  fillPaperOrder,
  seedOrderMachine,
  syncOrderMachine,
} from "../src/lib/floor/order-machine.ts";
import { frontLoadedTarget } from "../src/lib/floor/deployment.ts";

const universe = JSON.parse(
  readFileSync(new URL("../src/data/universe.json", import.meta.url), "utf8"),
) as { dates: string[]; c: { QQQ: Array<number | null> }; asof: string };

const points = universe.dates
  .map((date, i) => ({ date, price: Number(universe.c.QQQ[i]) }))
  .filter((x) => Number.isFinite(x.price) && x.price > 0);
const dates = points.map((x) => x.date);
const prices = points.map((x) => x.price);
const n = prices.length;
const B = 100_000;
const FRONTLOADS = [0, 0.4, 1];

function historicalPercentile(valueAtI: number, step: number, cap: number, i: number, signed = false) {
  if (!(valueAtI > 0) || i < step + 40) return null;
  const anchor = prices[i - step];
  if (!(anchor > 0)) return null;
  const move = signed ? valueAtI / anchor - 1 : Math.abs(valueAtI / anchor - 1);
  const first = Math.max(step, i - cap * step);
  let total = 0;
  let le = 0;
  for (let k = first; k < i; k += step) {
    const a = prices[k - step];
    const b = prices[k];
    if (a > 0 && b > 0) {
      total += 1;
      const x = signed ? b / a - 1 : Math.abs(b / a - 1);
      if (x <= move) le += 1;
    }
  }
  return total >= 40 ? le / total : null;
}

const dayP: Array<number | null> = new Array(n);
const weekP: Array<number | null> = new Array(n);
const monthP: Array<number | null> = new Array(n);
const dirP: Array<number | null> = new Array(n);
for (let i = 0; i < n; i += 1) {
  dayP[i] = historicalPercentile(prices[i], 1, 756, i);
  weekP[i] = historicalPercentile(prices[i], 5, 180, i);
  monthP[i] = historicalPercentile(prices[i], 21, 48, i);
  dirP[i] = historicalPercentile(prices[i], 5, 180, i, true);
}

const lows: Array<Partial<PricePathSample>> = new Array(n);
const highs: Array<Partial<PricePathSample>> = new Array(n);
for (let i = 0; i < n; i += 1) {
  if (i + 1 < n) lows[i] = { low1: prices[i + 1], high1: prices[i + 1] };
  if (i + 5 < n) {
    let lo = Infinity;
    let hi = -Infinity;
    for (let k = i + 1; k <= i + 5; k += 1) { lo = Math.min(lo, prices[k]); hi = Math.max(hi, prices[k]); }
    lows[i].low5 = lo; highs[i] = { ...(highs[i] ?? {}), high5: hi };
  }
  if (i + 21 < n) {
    let lo = Infinity;
    let hi = -Infinity;
    for (let k = i + 1; k <= i + 21; k += 1) { lo = Math.min(lo, prices[k]); hi = Math.max(hi, prices[k]); }
    lows[i].low21 = lo; highs[i] = { ...(highs[i] ?? {}), high21: hi };
  }
  if (i + 1 < n) highs[i] = { ...(highs[i] ?? {}), high1: prices[i + 1] };
}

function buildDailyLadder(i: number) {
  if (dayP[i] == null || weekP[i] == null || monthP[i] == null || dirP[i] == null || i < 61) return null;
  const target = [dayP[i], weekP[i], monthP[i], dirP[i]];
  const best: Array<{ i: number; distance: number }> = [];
  for (let k = 61; k <= i - 21; k += 1) {
    if (dayP[k] == null || weekP[k] == null || monthP[k] == null || dirP[k] == null) continue;
    const distance =
      Math.abs(dayP[k]! - target[0]!) +
      Math.abs(weekP[k]! - target[1]!) +
      Math.abs(monthP[k]! - target[2]!) +
      Math.abs(dirP[k]! - target[3]!);
    if (distance > 0.32) continue;
    if (best.length < 25) {
      best.push({ i: k, distance });
      best.sort((a, b) => a.distance - b.distance);
    } else if (distance < best[best.length - 1].distance) {
      best.pop();
      best.push({ i: k, distance });
      best.sort((a, b) => a.distance - b.distance);
    }
  }
  const samples: PricePathSample[] = [];
  for (const row of best) {
    const base = prices[row.i];
    if (!(base > 0)) continue;
    samples.push({
      entryPrice: base,
      low1: lows[row.i].low1 ?? base,
      low5: lows[row.i].low5 ?? base,
      low21: lows[row.i].low21 ?? base,
      high1: highs[row.i].high1 ?? base,
      high5: highs[row.i].high5 ?? base,
      high21: highs[row.i].high21 ?? base,
    });
  }
  return buildConditionalPriceLadder(prices[i], samples);
}

const ladders = new Array(n);
for (let i = 0; i < n; i += 1) ladders[i] = buildDailyLadder(i);

const monthFirst: number[] = [];
const monthLast: number[] = [];
let previousMonth = "";
for (let i = 0; i < n; i += 1) {
  const month = dates[i].slice(0, 7);
  if (month !== previousMonth) {
    monthFirst.push(i);
    if (previousMonth) monthLast.push(i - 1);
    previousMonth = month;
  }
}
monthLast.push(n - 1);

const windows = [];
for (let s = 0; s + 120 < monthFirst.length; s += 1) {
  windows.push({
    start: monthFirst[s],
    end: monthLast[s + 120],
    startDate: dates[monthFirst[s]],
    endDate: dates[monthLast[s + 120]],
  });
}

function runClock(start: number, end: number, startDate: string, frontload: number) {
  let shares = 0;
  let reserve = B;
  let peak = 0;
  let maxDd = 0;
  for (let i = start; i <= end; i += 1) {
    const target = frontLoadedTarget(B, frontload, cycleMonthFor(startDate, dates[i]), dates[i]);
    const nav = shares * prices[i];
    if (nav < target) {
      const buy = Math.min(reserve, target - nav);
      if (buy > 0) { shares += buy / prices[i]; reserve -= buy; }
    } else if (nav > target && shares > 0) {
      const sell = Math.min(nav - target, nav);
      shares -= sell / prices[i];
      reserve += sell;
    }
    const wealth = shares * prices[i] + reserve;
    peak = Math.max(peak, wealth);
    maxDd = Math.min(maxDd, wealth / peak - 1);
  }
  return { wealth: shares * prices[end] + reserve, maxDd };
}

function cycleMonthFor(startDate: string, date: string) {
  const s = new Date(startDate + "T00:00:00Z");
  const d = new Date(date + "T00:00:00Z");
  return Math.max(
    1,
    Math.min(120, (d.getUTCFullYear() - s.getUTCFullYear()) * 12 + (d.getUTCMonth() - s.getUTCMonth()) + 1),
  );
}

function runMachine(start: number, end: number, startDate: string, frontload: number, twoSided: boolean) {
  let state = seedOrderMachine({
    now: dates[start] + "T00:00:00.000Z",
    marketDate: dates[start],
    qqqPrice: prices[start],
    nav: 0,
    capital: B,
    contributed: 0,
  });
  let peak = 0;
  let maxDd = 0;
  let buyFills = 0;
  let sellFills = 0;
  let touched = 0;
  for (let i = start; i <= end; i += 1) {
    const date = dates[i];
    const target = frontLoadedTarget(B, frontload, cycleMonthFor(startDate, date), date);
    const full = ladders[i];
    const ladder = twoSided ? full : full ? { ...full, reduce: [] } : null;
    state = syncOrderMachine({
      state,
      now: date + "T23:59:59.000Z",
      marketDate: date,
      currentPrice: prices[i],
      ladder,
      target,
    });
    const touchedOrder = activePaperOrders(state).find((order) => order.status === "TOUCHED");
    if (touchedOrder) {
      touched += 1;
      const before = touchedOrder.side;
      state = fillPaperOrder(state, touchedOrder.id, prices[i], date + "T23:59:59.500Z");
      if (before === "BUY") buyFills += 1;
      else sellFills += 1;
      // Mimic the UI: after a confirmed fill, rebuild the next rung without a second fill at this observation.
      state = syncOrderMachine({
        state,
        now: date + "T23:59:59.900Z",
        marketDate: date,
        currentPrice: prices[i],
        ladder,
        target,
      });
    }
    const wealth = state.positionNav + state.deploymentReserve + state.harvestReserve;
    peak = Math.max(peak, wealth);
    maxDd = Math.min(maxDd, peak > 0 ? wealth / peak - 1 : 0);
  }
  return {
    wealth: state.positionNav + state.deploymentReserve + state.harvestReserve,
    maxDd,
    buyFills,
    sellFills,
    touched,
    harvestReserve: state.harvestReserve,
    deploymentReserve: state.deploymentReserve,
  };
}

function summarize(frontload: number, mode: "BUY_ONLY" | "TWO_SIDED") {
  const results = windows.map((w) => {
    const clock = runClock(w.start, w.end, w.startDate, frontload);
    const machine = runMachine(w.start, w.end, w.startDate, frontload, mode === "TWO_SIDED");
    const years = (new Date(w.endDate).getTime() - new Date(w.startDate).getTime()) / (365.25 * 24 * 3600 * 1000);
    return {
      ...w,
      clock,
      machine,
      delta: machine.wealth - clock.wealth,
      cagrClock: Math.pow(clock.wealth / B, 1 / years) - 1,
      cagrMachine: Math.pow(machine.wealth / B, 1 / years) - 1,
    };
  });
  const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
  const median = (xs: number[]) => {
    const z = [...xs].sort((a, b) => a - b);
    const p = (z.length - 1) / 2;
    return (z[Math.floor(p)] + z[Math.ceil(p)]) / 2;
  };
  return {
    frontload,
    mode,
    windows: results.length,
    meanTerminalClock: mean(results.map((x) => x.clock.wealth)),
    meanTerminalMachine: mean(results.map((x) => x.machine.wealth)),
    meanTerminalDelta: mean(results.map((x) => x.delta)),
    medianTerminalDelta: median(results.map((x) => x.delta)),
    terminalWinRate: results.filter((x) => x.delta > 0).length / results.length,
    meanCAGRClock: mean(results.map((x) => x.cagrClock)),
    meanCAGRMachine: mean(results.map((x) => x.cagrMachine)),
    meanCAGRDelta: mean(results.map((x) => x.cagrMachine - x.cagrClock)),
    meanMaxDDClock: mean(results.map((x) => x.clock.maxDd)),
    meanMaxDDMachine: mean(results.map((x) => x.machine.maxDd)),
    meanMaxDDDelta: mean(results.map((x) => x.machine.maxDd - x.clock.maxDd)),
    maxDDBetterRate: results.filter((x) => x.machine.maxDd > x.clock.maxDd).length / results.length,
    avgBuyFills: mean(results.map((x) => x.machine.buyFills)),
    avgSellFills: mean(results.map((x) => x.machine.sellFills)),
    avgTouched: mean(results.map((x) => x.machine.touched)),
    avgHarvestReserveEnd: mean(results.map((x) => x.machine.harvestReserve)),
    avgDeploymentReserveEnd: mean(results.map((x) => x.machine.deploymentReserve)),
    firstWindows: results.slice(0, 3).map((x) => ({
      start: x.startDate,
      end: x.endDate,
      clock: x.clock.wealth,
      machine: x.machine.wealth,
      delta: x.delta,
      machineMaxDD: x.machine.maxDd,
      buyFills: x.machine.buyFills,
      sellFills: x.machine.sellFills,
    })),
  };
}

const output = {
  schema: "qqq-order-machine-replay-v1",
  generatedAt: new Date().toISOString(),
  dataAsOf: universe.asof,
  source: "src/data/universe.json / c.QQQ / Yahoo adjclose",
  windows: windows.length,
  frontloads: FRONTLOADS,
  assumptions: {
    execution: "daily-close touch only; fill at resting limit; one confirmed fill per side per daily observation; no fees/slippage",
    orderValidity: "persistent across market dates; new day marks ARMED as STALE; no automatic cancel",
    matching: "causal DAY/WEEK/MONTH volatility percentiles + causal 5D signed-return percentile; max distance 0.32; top 25 matches",
    rungs: "NEAR 1D/70%, MID 5D/50%, DEEP 21D/30%; weights 50/30/20",
    capital: "B=100000 fully available as deployment reserve at window start; frontload changes target curve, not cash availability",
    baseline: "daily close target tracker against the same front-loaded target curve",
  },
  results: FRONTLOADS.flatMap((f) => [summarize(f, "BUY_ONLY"), summarize(f, "TWO_SIDED")]),
};

const outDir = process.argv[2] ?? "./replay-out";
mkdirSync(outDir, { recursive: true });
writeFileSync(outDir + "/RESULTS_ORDER_MACHINE_REPLAY.json", JSON.stringify(output, null, 2));
const csvRows = ["frontload,mode,meanTerminalDelta,medianTerminalDelta,terminalWinRate,meanCAGRDelta,meanMaxDDDelta,maxDDBetterRate,avgBuyFills,avgSellFills,avgTouched,avgHarvestReserveEnd,avgDeploymentReserveEnd"];
for (const row of output.results) {
  csvRows.push([
    row.frontload,row.mode,row.meanTerminalDelta,row.medianTerminalDelta,row.terminalWinRate,
    row.meanCAGRDelta,row.meanMaxDDDelta,row.maxDDBetterRate,row.avgBuyFills,row.avgSellFills,
    row.avgTouched,row.avgHarvestReserveEnd,row.avgDeploymentReserveEnd,
  ].join(","));
}
writeFileSync(outDir + "/RESULTS_ORDER_MACHINE_REPLAY.csv", csvRows.join("\n") + "\n");
console.log(JSON.stringify(output, null, 2));
