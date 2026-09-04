import type { RelCard } from "./relvol.ts";
import { similarFwd } from "./relvol.ts";
import { bsPrice } from "./black-scholes.ts";
import { expectedShortfall, quantile } from "./stats.ts";
import type { SymbolId } from "./universe.ts";

export type StructureId =
  | "NO_TRADE"
  | "IRON_FLY"
  | "IRON_CONDOR"
  | "BROKEN_WING"
  | "CALL_RATIO"
  | "PUT_RATIO"
  | "BULL_PUT"
  | "BEAR_CALL"
  | "COVERED_CALL"
  | "PROTECTIVE_PUT"
  | "LONG_STRADDLE"
  | "LONG_CALL"
  | "LONG_PUT"
  | "BUY_UNDERLYING"
  | "CALENDAR";

export type BreachBudget = {
  probability: number;
  avgLoss: number;
  medianLoss: number;
  worst: number;
  es95: number;
  es99: number;
  consecutive3: number;
  consecutive5: number;
  maxConsecutive: number;
  recovery: number;
  n: number;
};

export type Deployment = {
  id: StructureId;
  variant: string;
  label: string;
  legs: string;
  shortRatio: number;
  dte: number;
  shortPct: number;
  wingPct: number;
  credit: number;
  ev: number;
  pop: number;
  breach: BreachBudget;
  valueRisk: number | null;
  persistenceAdj: number;
  score: number;
  why: string[];
  tag: "HYPOTHETICAL";
  chain: "OPTIONS_MISSING";
};

export type CapacityPlan = {
  lots: number;
  notional: number;
  expectedBreachDollar: number;
  es95Dollar: number;
  rejected: boolean;
  reason: string;
};

export type BudgetInput = {
  maxConsec: number;
  maxDd: number;
};

function consecRate(flags: boolean[], k: number) {
  if (flags.length < k) return 0;
  let hits = 0;
  let n = 0;
  for (let i = 0; i + k <= flags.length; i++) {
    n += 1;
    if (flags.slice(i, i + k).every(Boolean)) hits += 1;
  }
  return n ? hits / n : 0;
}

function maxRun(flags: boolean[]) {
  let best = 0;
  let cur = 0;
  for (const f of flags) {
    cur = f ? cur + 1 : 0;
    if (cur > best) best = cur;
  }
  return best;
}

function recoveryRate(pnls: number[]) {
  let rec = 0;
  let n = 0;
  for (let i = 0; i + 1 < pnls.length; i++) {
    if (pnls[i] >= 0) continue;
    n += 1;
    if (pnls[i + 1] > 0) rec += 1;
  }
  return n ? rec / n : 0;
}

export function ironFlyPnl(r: number, short = 0.02, wing = 0.05, credit = 0.007) {
  const x = Math.abs(r);
  if (x <= short) return credit;
  if (x <= wing) return credit - (x - short);
  return credit - (wing - short);
}

function condorPnl(r: number, short = 0.03, wing = 0.07, credit = 0.005) {
  return ironFlyPnl(r, short, wing, credit);
}

function brokenWingPnl(r: number, short = 0.02, upWing = 0.08, dnWing = 0.04, credit = 0.006) {
  if (r >= 0) return ironFlyPnl(r, short, upWing, credit);
  return ironFlyPnl(r, short, dnWing, credit);
}

function ratioPnl(r: number, nShort: number, dir: 1 | -1, otm = 0.03, hedge = 0.1) {
  const x = r * dir;
  const long = Math.max(x, 0);
  const short = Math.max(x - otm, 0) * nShort;
  const tail = Math.max(x - hedge, 0);
  const credit = 0.004 * nShort - 0.012;
  return credit + long - short + tail;
}

function straddlePnl(r: number, debit = 0.025) {
  return Math.abs(r) - debit;
}

function longOptPnl(r: number, dir: 1 | -1, debit = 0.018) {
  return Math.max(r * dir, 0) - debit;
}

function creditSpreadPnl(r: number, dir: 1 | -1, short = 0.02, wing = 0.05, credit = 0.006) {
  const adverse = dir === 1 ? -r : r;
  if (adverse <= short) return credit;
  if (adverse <= wing) return credit - (adverse - short);
  return credit - (wing - short);
}

function coveredCallPnl(r: number, short = 0.03, credit = 0.008) {
  return r - Math.max(r - short, 0) + credit;
}

function protectivePutPnl(r: number, strike = -0.05, debit = 0.012) {
  return r + Math.max(-strike - r, 0) - debit;
}

function calendarPnl(r: number, debit = 0.006) {
  const inner = ironFlyPnl(r, 0.015, 0.04, 0.004);
  return inner - debit;
}

function buyPnl(r: number) {
  return r;
}

function budget(pnls: number[]): BreachBudget {
  const losses = pnls.filter((p) => p < 0);
  const flags = pnls.map((p) => p < 0);
  return {
    probability: pnls.length ? losses.length / pnls.length : 0,
    avgLoss: losses.length ? losses.reduce((s, x) => s + x, 0) / losses.length : 0,
    medianLoss: losses.length ? quantile(losses, 0.5) : 0,
    worst: losses.length ? Math.min(...losses) : 0,
    es95: expectedShortfall(pnls, 0.05),
    es99: expectedShortfall(pnls, 0.01),
    consecutive3: consecRate(flags, 3),
    consecutive5: consecRate(flags, 5),
    maxConsecutive: maxRun(flags),
    recovery: recoveryRate(pnls),
    n: pnls.length,
  };
}

export function theoreticalCredit(card: RelCard, shortPct: number, wingPct: number, dte: number) {
  const iv = card.rv21 ?? 0.28;
  const T = Math.max(dte / 365, 1 / 365);
  const S = card.spot;
  const shortC = bsPrice({ spot: S, strike: S * (1 + shortPct), tYears: T, iv, right: "CALL" });
  const shortP = bsPrice({ spot: S, strike: S * (1 - shortPct), tYears: T, iv, right: "PUT" });
  const longC = bsPrice({ spot: S, strike: S * (1 + wingPct), tYears: T, iv, right: "CALL" });
  const longP = bsPrice({ spot: S, strike: S * (1 - wingPct), tYears: T, iv, right: "PUT" });
  return (shortC + shortP - longC - longP) / S;
}

export function shortRatioOf(card: RelCard) {
  if (card.reversion != null && card.reversion >= 0.6 && (card.week.level === "EXTREME" || card.week.level === "SUPER_EXTREME"))
    return 5;
  if (card.reversion != null && card.reversion >= 0.55) return 4;
  if (card.continuation != null && card.continuation >= 0.6) return 2;
  if (card.week.level === "SUPER_EXTREME") return 3;
  if (card.volMomentum === "RISING" && card.continuation != null && card.continuation >= 0.55) return 2;
  return 3;
}

function scoreOf(ev: number, br: BreachBudget, persist: RelCard["persistence"], edge: number | null, conf: RelCard["confidence"]) {
  const tail = Math.min(-0.002, br.es95);
  const vr = Math.max(-4, Math.min(4, ev / Math.abs(tail)));
  const pAdj = persist.score === "HIGH" ? 1.1 : persist.score === "LOW" ? 0.75 : 0.9;
  const eAdj = edge != null && edge > 0 ? 1.08 : edge != null && edge < 0 ? 0.9 : 1;
  const oos = persist.oosP1 == null ? 0.92 : Math.max(0.7, Math.min(1.08, persist.oosP1 / 0.55));
  const cAdj = conf === "thin" ? 0.7 : conf === "low" ? 0.85 : 1;
  const cluster = 1 - Math.min(0.35, br.consecutive3 * 2);
  return vr * pAdj * eAdj * oos * cAdj * cluster;
}

export function compete(card: RelCard, calCursor: number): Deployment[] {
  const fwd = similarFwd(card.symbol as SymbolId, calCursor, 5);
  const persistAdj = card.persistence.score === "HIGH" ? 1 : card.persistence.score === "LOW" ? 0.7 : 0.85;
  const nShort = shortRatioOf(card);
  const rs = fwd.map((x) => x.r);
  const ws = fwd.map((x) => x.w);
  const wsum = ws.reduce((s, x) => s + x, 0) || 1;

  const mk = (
    id: StructureId,
    variant: string,
    label: string,
    legs: string,
    pnlFn: (r: number) => number,
    why: string[],
    extra?: { shortPct?: number; wingPct?: number; credit?: number; ratio?: number },
  ): Deployment => {
    const pnls = rs.map(pnlFn);
    const ev = pnls.length ? pnls.reduce((s, p, i) => s + p * ws[i], 0) / wsum : 0;
    const pop = pnls.length ? pnls.filter((p) => p > 0).length / pnls.length : 0;
    const br = budget(pnls);
    const vr = br.es95 < 0 ? ev / Math.abs(br.es95) : null;
    const sc = scoreOf(ev, br, card.persistence, card.volEdge, card.confidence);
    return {
      id,
      variant,
      label,
      legs,
      shortRatio: extra?.ratio ?? (id.includes("RATIO") ? nShort : 1),
      dte: 7,
      shortPct: extra?.shortPct ?? 0,
      wingPct: extra?.wingPct ?? 0,
      credit: extra?.credit ?? 0,
      ev,
      pop,
      breach: br,
      valueRisk: vr,
      persistenceAdj: persistAdj,
      score: Math.max(0, Math.min(99, 50 + sc * 12)),
      why,
      tag: "HYPOTHETICAL",
      chain: "OPTIONS_MISSING",
    };
  };

  const flyGrid = [
    [0.01, 0.05],
    [0.015, 0.05],
    [0.02, 0.05],
    [0.02, 0.08],
  ] as const;

  const rows: Deployment[] = [];
  for (const [sh, wg] of flyGrid) {
    const cr = Math.max(0.002, theoreticalCredit(card, sh, wg, 7));
    rows.push(
      mk(
        "IRON_FLY",
        `fly-${sh}-${wg}`,
        `Iron Fly ±${(sh * 100).toFixed(1)}/${(wg * 100).toFixed(0)}`,
        `short ±${(sh * 100).toFixed(1)}% / wings ±${(wg * 100).toFixed(0)}%`,
        (r) => ironFlyPnl(r, sh, wg, cr),
        ["結構競爭，不是預設鐵蝶"],
        { shortPct: sh, wingPct: wg, credit: cr },
      ),
    );
  }
  rows.push(
    mk("IRON_CONDOR", "ic", "Iron Condor ±3/7", "short ±3% / wings ±7%", (r) => condorPnl(r), ["較寬盈利區"]),
    mk("BROKEN_WING", "bw", "Broken Wing", "short ±2% / call +8% / put +4%", (r) => brokenWingPnl(r), ["不對稱翼"]),
    mk(
      "CALL_RATIO",
      `cr-${nShort}`,
      `Call Ratio 1:${nShort}:1`,
      `long ATM + short ${nShort}× +3% + long +10%`,
      (r) => ratioPnl(r, nShort, 1),
      ["Short ratio = f(state)，不是寫死 5"],
      { ratio: nShort },
    ),
    mk(
      "PUT_RATIO",
      `pr-${nShort}`,
      `Put Ratio 1:${nShort}:1`,
      `long ATM put + short ${nShort}× −3% + long −10%`,
      (r) => ratioPnl(r, nShort, -1),
      ["下跌突破才考慮"],
      { ratio: nShort },
    ),
    mk("BULL_PUT", "bp", "Bull Put", "short −2% / long −5%", (r) => creditSpreadPnl(r, 1), ["有限風險收租"]),
    mk("BEAR_CALL", "bc", "Bear Call", "short +2% / long +5%", (r) => creditSpreadPnl(r, -1), ["上行過熱"]),
    mk("COVERED_CALL", "cc", "Covered Call", "long stock + short +3% call", (r) => coveredCallPnl(r), ["固定賣升，大趨勢會被截"]),
    mk("PROTECTIVE_PUT", "pp", "Protective Put", "long stock + long −5% put", (r) => protectivePutPnl(r), ["付保險"]),
    mk("LONG_STRADDLE", "ls", "Long Straddle", "long ATM straddle", (r) => straddlePnl(r), ["買波動"]),
    mk("LONG_CALL", "lc", "Long Call", "long near ATM call", (r) => longOptPnl(r, 1), ["保留凸性"]),
    mk("LONG_PUT", "lp", "Long Put", "long near ATM put", (r) => longOptPnl(r, -1), ["下跌凸性"]),
    mk("CALENDAR", "cal", "Calendar", "short 7D / long 21D ATM", (r) => calendarPnl(r), ["期限結構代理"]),
    mk("BUY_UNDERLYING", "eq", "Buy underlying", "long shares, no option overlay", (r) => buyPnl(r), ["吃 drift，沒有收租"]),
  );

  const noTrade: Deployment = {
    id: "NO_TRADE",
    variant: "none",
    label: "NO_TRADE",
    legs: "none",
    shortRatio: 0,
    dte: 0,
    shortPct: 0,
    wingPct: 0,
    credit: 0,
    ev: 0,
    pop: 0,
    breach: {
      probability: 0,
      avgLoss: 0,
      medianLoss: 0,
      worst: 0,
      es95: 0,
      es99: 0,
      consecutive3: 0,
      consecutive5: 0,
      maxConsecutive: 0,
      recovery: 0,
      n: fwd.length,
    },
    valueRisk: null,
    persistenceAdj: persistAdj,
    score: 52,
    why: ["沒有足夠 edge / persistence 低 / 選擇權鏈 MISSING"],
    tag: "HYPOTHETICAL",
    chain: "OPTIONS_MISSING",
  };

  const tradable = rows.filter((d) => d.id !== "NO_TRADE");
  const best = tradable.reduce((a, b) => (b.score > a.score ? b : a), tradable[0]);
  const shouldWait =
    !best ||
    best.ev <= 0 ||
    card.persistence.score === "LOW" ||
    fwd.length < 25 ||
    card.confidence === "thin" ||
    card.alert === "WAIT";
  if (shouldWait) {
    const mx = Math.max(...rows.map((r) => r.score), 50);
    noTrade.score = Math.min(100, mx + 1);
  }
  rows.push(noTrade);
  return rows.sort((a, b) => b.score - a.score);
}

export function capacityPlan(dep: Deployment, spot: number, budget: BudgetInput): CapacityPlan {
  const unitEs = Math.abs(dep.breach.es95) * 100 * spot;
  const unitWorst = Math.abs(Math.min(dep.breach.worst, dep.breach.es99)) * 100 * spot;
  const unit = Math.max(unitEs, unitWorst * 0.5, 1);
  let lots = Math.floor(budget.maxDd / unit);
  let rejected = false;
  let reason = "within budget";
  if (dep.id === "NO_TRADE") {
    return { lots: 0, notional: 0, expectedBreachDollar: 0, es95Dollar: 0, rejected: true, reason: "NO_TRADE" };
  }
  if (dep.breach.maxConsecutive > budget.maxConsec && dep.breach.consecutive3 > 0.04) {
    lots = Math.floor(lots * 0.4);
    reason = `historical cluster ${dep.breach.maxConsecutive} > budget ${budget.maxConsec}`;
  }
  if (dep.breach.n < 20) {
    lots = Math.min(lots, 1);
    reason = "thin similar-state sample";
  }
  if (lots <= 0) {
    rejected = true;
    reason = "drawdown budget cannot absorb ES95 of 1 lot";
  }
  return {
    lots,
    notional: lots * 100 * spot,
    expectedBreachDollar: lots * Math.abs(dep.breach.avgLoss) * 100 * spot * dep.breach.probability,
    es95Dollar: lots * unitEs,
    rejected,
    reason,
  };
}
