import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { buildConditionalPriceLadder, type PricePathSample } from "../src/lib/floor/yahoo-live.ts";
import {
  activePaperOrders,
  fillPaperOrder,
  paperEconomicWealth,
  seedOrderMachine,
  syncOrderMachine,
} from "../src/lib/floor/order-machine.ts";
import { dynamicTradeIntent, frontLoadedTarget } from "../src/lib/floor/deployment.ts";

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

function runMachine(start: number, end: number, startDate: string, frontload: number) {
  let state = seedOrderMachine({
    now: dates[start] + "T00:00:00.000Z",
    marketDate: dates[start],
    qqqPrice: prices[start],
    nav: 0,
    capital: B,
    contributed: 0,
  });
  let parentIntentDays = 0;
  let buyIntents = 0;
  let sellIntents = 0;
  let armedOrders = 0;
  let fills = 0;
  let buyFills = 0;
  let sellFills = 0;
  let touched = 0;
  let maxActiveOrders = 0;
  let parentNotional = 0;
  let childNotional = 0;
  let filledNotional = 0;

  for (let i = start; i <= end; i += 1) {
    const date = dates[i];
    const target = frontLoadedTarget(B, frontload, cycleMonthFor(startDate, date), date);
    const intent = dynamicTradeIntent({
      id: "DEV_VITE_DYNAMIC_" + date + "_M" + String(cycleMonthFor(startDate, date)),
      now: date + "T23:59:59.000Z",
      cycleMonth: cycleMonthFor(startDate, date),
      nav: state.positionNav,
      target,
      remainingCapital: Math.max(0, B),
    });
    if (intent) {
      parentIntentDays += 1;
      parentNotional += intent.notional;
      if (intent.side === "BUY") buyIntents += 1;
      else sellIntents += 1;
    }

    const ladder = ladders[i];
    const beforeActive = activePaperOrders(state);
    const beforeIds = new Set(beforeActive.map((order) => order.id));
    state = syncOrderMachine({
      state,
      now: date + "T23:59:59.000Z",
      marketDate: date,
      currentPrice: prices[i],
      ladder,
      intent,
    });
    const newlyArmed = activePaperOrders(state).filter((order) => !beforeIds.has(order.id));
    armedOrders += newlyArmed.length;
    childNotional += newlyArmed.reduce((sum, order) => sum + order.suggestedAmount, 0);

    for (const order of newlyArmed) {
      const rung = order.rung === "NEAR" ? 0.5 : order.rung === "MID" ? 0.3 : 0.2;
      const expected = (order.parentIntentNotional ?? 0) * rung;
      if (Math.abs(order.suggestedAmount - expected) > 1e-8) {
        throw new Error("parent-intent sizing invariant failed for " + order.id);
      }
      if (order.parentIntentId !== intent?.id) {
        throw new Error("parent-intent identity invariant failed for " + order.id);
      }
    }

    maxActiveOrders = Math.max(maxActiveOrders, activePaperOrders(state).length);
    if (maxActiveOrders > 1) {
      throw new Error("execution layer created more than one active parent order");
    }

    const touchedOrder = activePaperOrders(state).find((order) => order.status === "TOUCHED");
    if (touchedOrder) {
      touched += 1;
      const before = touchedOrder.side;
      const beforeWealth = paperEconomicWealth(state);
      state = fillPaperOrder(state, touchedOrder.id, prices[i], date + "T23:59:59.500Z");
      if (state.orders.find((x) => x.id === touchedOrder.id)?.status !== "FILLED") {
        throw new Error("touched order did not reach FILLED");
      }
      fills += 1;
      filledNotional += state.orders.find((x) => x.id === touchedOrder.id)?.filledAmount ?? 0;
      if (paperEconomicWealth(state) > beforeWealth + 1e-8) {
        throw new Error("paper wealth conservation invariant failed");
      }
      if (before === "BUY") buyFills += 1;
      else sellFills += 1;

      state = syncOrderMachine({
        state,
        now: date + "T23:59:59.900Z",
        marketDate: date,
        currentPrice: prices[i],
        ladder,
        intent: dynamicTradeIntent({
          id: "DEV_VITE_DYNAMIC_" + date + "_M" + String(cycleMonthFor(startDate, date)),
          now: date + "T23:59:59.900Z",
          cycleMonth: cycleMonthFor(startDate, date),
          nav: state.positionNav,
          target,
          remainingCapital: Math.max(0, B),
        }),
      });
    }
  }
  return {
    parentIntentDays,
    buyIntents,
    sellIntents,
    armedOrders,
    fills,
    buyFills,
    sellFills,
    touched,
    maxActiveOrders,
    parentNotional,
    childNotional,
    filledNotional,
    terminalEconomicWealth: paperEconomicWealth(state),
  };
}

function summarize(frontload: number) {
  const results = windows.map((w) => ({
    ...w,
    machine: runMachine(w.start, w.end, w.startDate, frontload),
  }));
  const mean = (xs: number[]) => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;
  return {
    frontload,
    windows: results.length,
    meanParentIntentDays: mean(results.map((x) => x.machine.parentIntentDays)),
    meanBuyIntentDays: mean(results.map((x) => x.machine.buyIntents)),
    meanSellIntentDays: mean(results.map((x) => x.machine.sellIntents)),
    meanArmedOrders: mean(results.map((x) => x.machine.armedOrders)),
    meanFills: mean(results.map((x) => x.machine.fills)),
    meanBuyFills: mean(results.map((x) => x.machine.buyFills)),
    meanSellFills: mean(results.map((x) => x.machine.sellFills)),
    meanTouched: mean(results.map((x) => x.machine.touched)),
    maxObservedActiveOrders: Math.max(...results.map((x) => x.machine.maxActiveOrders)),
    meanParentNotional: mean(results.map((x) => x.machine.parentNotional)),
    meanChildNotional: mean(results.map((x) => x.machine.childNotional)),
    meanFilledNotional: mean(results.map((x) => x.machine.filledNotional)),
    firstWindows: results.slice(0, 3).map((x) => ({
      start: x.startDate,
      end: x.endDate,
      parentIntentDays: x.machine.parentIntentDays,
      armedOrders: x.machine.armedOrders,
      fills: x.machine.fills,
      buyFills: x.machine.buyFills,
      sellFills: x.machine.sellFills,
    })),
  };
}

const output = {
  schema: "qqq-order-machine-replay-v2-contract",
  generatedAt: new Date().toISOString(),
  dataAsOf: universe.asof,
  source: "src/data/universe.json / c.QQQ / Yahoo adjclose",
  windows: windows.length,
  frontloads: FRONTLOADS,
  assumptions: {
    purpose: "execution-contract/invariant replay only; NOT a strategy alpha or CAGR comparison",
    parent: "DEV/Vite dynamicTradeIntent from deploymentGap is the only BUY/SELL source",
    execution: "ladder chooses child rung/limit; child notional = parent intent notional × rung weight 50/30/20",
    fill: "daily-close touch only; manual paper fill confirmation; no fees/slippage",
    orderValidity: "persistent across market dates; new day marks ARMED as STALE; no automatic cancel",
    matching: "causal DAY/WEEK/MONTH volatility percentiles + causal 5D signed-return percentile; max distance 0.32; top 25 matches",
    rungs: "NEAR 1D/70%, MID 5D/50%, DEEP 21D/30%; weights 50/30/20",
  },
  results: FRONTLOADS.map((f) => summarize(f)),
};

const outDir = process.argv[2] ?? "./replay-out";
mkdirSync(outDir, { recursive: true });
writeFileSync(outDir + "/RESULTS_ORDER_MACHINE_REPLAY.json", JSON.stringify(output, null, 2));
const csvRows = ["frontload,windows,meanParentIntentDays,meanBuyIntentDays,meanSellIntentDays,meanArmedOrders,meanFills,meanBuyFills,meanSellFills,meanTouched,maxObservedActiveOrders,meanParentNotional,meanChildNotional,meanFilledNotional"];
for (const row of output.results) {
  csvRows.push([
    row.frontload,row.windows,row.meanParentIntentDays,row.meanBuyIntentDays,row.meanSellIntentDays,
    row.meanArmedOrders,row.meanFills,row.meanBuyFills,row.meanSellFills,row.meanTouched,
    row.maxObservedActiveOrders,row.meanParentNotional,row.meanChildNotional,row.meanFilledNotional,
  ].join(","));
}
writeFileSync(outDir + "/RESULTS_ORDER_MACHINE_REPLAY.csv", csvRows.join("\n") + "\n");
console.log(JSON.stringify(output, null, 2));
