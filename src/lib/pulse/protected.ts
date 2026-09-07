import { bsPrice, roundStrike } from "./black-scholes.ts";
import { universe, calendarIndexOf } from "./bars.ts";
import {
  type Regime,
  type Metrics,
  metrics,
  sampleWindow,
  state,
  buyHoldQQQ,
  type BacktestResult,
} from "./backtest.ts";

/**
 * V2.2 persistent put overlay.
 *
 * Observed: QQQ close, VIX close.
 * Derived: Black-Scholes put marked with VIX as IV (SPX 30d IV, flat term
 *          structure — NOT QQQ option IV, NOT this DTE).
 * Estimated: 10% of mid as bid/ask haircut on open and early close.
 * Hypothetical: none in this path. The V2.1 daily -1.5% floor is a different toy.
 *
 * No OPRA chain. This is not a historical option-fill backtest.
 */

const DAYS = 252;
const WARMUP = 60;
const ADD_STEP = 0.24;

export type ProtectedSpec = {
  putDistance: number;
  dte: number;
  rollDays: number;
  calmPut: number;
  unstablePut: number;
  tailPut: number;
  recoveryPut: number;
  buildingPut: number;
  qqqCalm: number;
  qqqUnstable: number;
  qqqTail: number;
  qqqRecovery: number;
  emergencyDd: number | null;
  spread: number;
};

export const DEFAULT_PROTECTED: ProtectedSpec = {
  putDistance: 0.03,
  dte: 30,
  rollDays: 7,
  calmPut: 0,
  unstablePut: 0.5,
  tailPut: 1,
  recoveryPut: 0.25,
  buildingPut: 0.75,
  qqqCalm: 1,
  qqqUnstable: 1,
  qqqTail: 1,
  qqqRecovery: 1,
  emergencyDd: null,
  spread: 0.1,
};

/** Full grid the user specified. Not searched in first wave. */
export const INTENDED_PROTECTED_GRID = {
  putDistance: [0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05],
  dte: [7, 14, 21, 30, 45, 60, 90],
  rollDays: [7, 14, 21, 30],
  putSize: [0.25, 0.5, 0.75, 1, 1.5],
  note: "First wave searches a subset so the freeze protocol can actually run. Intended grid is recorded, not silently treated as searched.",
};

export type ProtectedCurvePoint = {
  i: number;
  date: string;
  equity: number;
  drawdown: number;
  regime: Regime;
  building: boolean;
  qqqExp: number;
  putSize: number;
  putMark: number;
  premium: number;
  strategyReturn: number;
  vix: number | null;
};

export type ProtectedResult = {
  spec: ProtectedSpec;
  metrics: Metrics;
  split: { train: Metrics; validation: Metrics; oos: Metrics };
  extras: {
    full: ProtectedExtras;
    train: ProtectedExtras;
    validation: ProtectedExtras;
    oos: ProtectedExtras;
  };
  score: number;
  curve: ProtectedCurvePoint[];
  oosLeakage: false;
  layer: "Derived";
  disclaimer: string;
};

export type ProtectedExtras = {
  premiumDrag: number;
  premiumSum: number;
  nRolls: number;
  nAddOns: number;
  nOpens: number;
  protectionEfficiency: number;
  avgPutSize: number;
  daysWithPut: number;
};

type Lot = {
  strike: number;
  expiryI: number;
  contracts: number;
  lastMark: number;
  openedI: number;
};

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

function addCalendarDays(iso: string, n: number) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

function expiryIndex(fromI: number, dte: number) {
  const target = addCalendarDays(universe.dates[fromI], dte);
  let j = calendarIndexOf(target);
  if (j <= fromI) j = fromI + 1;
  if (j >= universe.dates.length) j = universe.dates.length - 1;
  return j;
}

function remainingCalendarDays(i: number, expiryI: number) {
  const a = Date.parse(`${universe.dates[i]}T00:00:00Z`);
  const b = Date.parse(`${universe.dates[expiryI]}T00:00:00Z`);
  return (b - a) / 86400000;
}

function ivFromVix(i: number) {
  const v = close("VIX", i) ?? close("VIX", i - 1);
  if (v == null || v <= 0) return 0.2;
  return v > 3 ? v / 100 : v;
}

function markPut(S: number, K: number, i: number, expiryI: number, iv: number) {
  const days = remainingCalendarDays(i, expiryI);
  if (days <= 0.4) return Math.max(K - S, 0);
  return bsPrice({ spot: S, strike: K, tYears: days / 365, iv, right: "PUT" });
}

export function qqqExposure(s: ReturnType<typeof state>, spec: ProtectedSpec, dd: number) {
  let q =
    s.regime === "TAIL"
      ? spec.qqqTail
      : s.regime === "UNSTABLE"
        ? spec.qqqUnstable
        : s.regime === "RECOVERY"
          ? spec.qqqRecovery
          : spec.qqqCalm;
  if (spec.emergencyDd != null && dd <= -spec.emergencyDd) q *= 0.5;
  return Math.max(0, Math.min(1.5, q));
}

export function putTarget(s: ReturnType<typeof state>, spec: ProtectedSpec) {
  let z =
    s.regime === "TAIL"
      ? spec.tailPut
      : s.regime === "UNSTABLE"
        ? spec.unstablePut
        : s.regime === "RECOVERY"
          ? spec.recoveryPut
          : spec.calmPut;
  if (s.building) z = Math.max(z, spec.buildingPut);
  return Math.max(0, Math.min(1.5, z));
}

function emptyExtras(): ProtectedExtras {
  return {
    premiumDrag: 0,
    premiumSum: 0,
    nRolls: 0,
    nAddOns: 0,
    nOpens: 0,
    protectionEfficiency: 0,
    avgPutSize: 0,
    daysWithPut: 0,
  };
}

function extrasFrom(
  premiumSum: number,
  nDays: number,
  nRolls: number,
  nAddOns: number,
  nOpens: number,
  putSizeSum: number,
  daysWithPut: number,
  protectedDd: number,
  nakedDd: number,
): ProtectedExtras {
  const premiumDrag = nDays ? premiumSum * (DAYS / nDays) : 0;
  const ddReduction = Math.max(0, -nakedDd - -protectedDd);
  return {
    premiumDrag,
    premiumSum,
    nRolls,
    nAddOns,
    nOpens,
    protectionEfficiency: premiumDrag > 1e-6 ? ddReduction / premiumDrag : 0,
    avgPutSize: nDays ? putSizeSum / nDays : 0,
    daysWithPut,
  };
}

export function protectedScore(m: Metrics, extra: ProtectedExtras) {
  return (
    m.cagr * 100 -
    Math.max(0, -m.maxDd) * 160 -
    Math.max(0, -m.es) * 80 +
    m.sharpe * 6 +
    m.sortino * 3 -
    m.turnover * 8 +
    extra.protectionEfficiency * 8 -
    extra.premiumDrag * 40
  );
}

const DISCLAIMER =
  "Derived BS put overlay using VIX as IV. Estimated 10% spread haircut. NOT an OPRA fill backtest.";

let nakedCache: BacktestResult | null = null;
function nakedQQQ() {
  if (!nakedCache) nakedCache = buyHoldQQQ();
  return nakedCache;
}

export function runProtected(
  spec: ProtectedSpec,
  start = WARMUP,
  end = universe.dates.length - 1,
  keepCurve = true,
): ProtectedResult {
  const w = sampleWindow();
  const naked = nakedQQQ();
  const rs: number[] = [];
  const trainRs: number[] = [];
  const valRs: number[] = [];
  const oosRs: number[] = [];
  const curve: ProtectedCurvePoint[] = [];
  const lots: Lot[] = [];
  let equity = 1;
  let peak = 1;
  let prevPut = 0;
  let turns = 0;
  const acc = {
    full: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
    train: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
    val: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
    oos: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
  };

  const bump = (which: "full" | "train" | "val" | "oos", k: "prem" | "rolls" | "add" | "opens" | "putSum" | "withPut", x: number) => {
    acc.full[k] += x;
    acc[which][k] += x;
  };

  for (let i = Math.max(WARMUP, start); i <= end; i++) {
    const qRet = ret("QQQ", i);
    const S = close("QQQ", i);
    if (qRet == null || S == null) continue;
    const s = state(i - 1);
    const dd = equity / peak - 1;
    const qqqExp = qqqExposure(s, spec, dd);
    const target = putTarget(s, spec);
    const iv = ivFromVix(i);
    const which = i <= w.trainEnd ? "train" : i <= w.valEnd ? "val" : "oos";

    let putPnl = 0;
    let premium = 0;

    for (let k = lots.length - 1; k >= 0; k--) {
      const lot = lots[k];
      const mid = markPut(S, lot.strike, i, lot.expiryI, iv);
      putPnl += lot.contracts * (mid - lot.lastMark);
      lot.lastMark = mid;
      if (i >= lot.expiryI) {
        lots.splice(k, 1);
      }
    }

    const minExpiry = lots.reduce((m, lot) => Math.min(m, lot.expiryI), Infinity);
    const dueRoll = lots.length > 0 && remainingCalendarDays(i, minExpiry) <= spec.rollDays;
    if (dueRoll) {
      for (const lot of lots) {
        const hair = lot.lastMark * (1 - spec.spread);
        putPnl += lot.contracts * (hair - lot.lastMark);
        lot.lastMark = hair;
      }
      lots.length = 0;
      bump(which, "rolls", 1);
    }

    const currentSize = equity > 0 ? lots.reduce((a, lot) => a + (lot.contracts * S) / equity, 0) : 0;
    const needOpen = lots.length === 0 && target > 0.02;
    const needAdd = lots.length > 0 && target > currentSize + ADD_STEP;
    if ((needOpen || needAdd) && equity > 0) {
      const addSize = needOpen ? target : target - currentSize;
      const contracts = (addSize * equity) / S;
      const strike = roundStrike(S * (1 - spec.putDistance), S);
      const expiryI = expiryIndex(i, spec.dte);
      const mid = markPut(S, strike, i, expiryI, iv);
      const pay = mid * (1 + spec.spread);
      premium += contracts * pay;
      lots.push({ strike, expiryI, contracts, lastMark: mid, openedI: i });
      bump(which, "opens", 1);
      if (needAdd) bump(which, "add", 1);
    }

    if (Math.abs(target - prevPut) > 1e-6) turns += 1;
    prevPut = target;

    const rPut = equity > 0 ? (putPnl - premium) / equity : 0;
    const realized = qqqExp * qRet + rPut;
    equity *= 1 + realized;
    if (equity <= 1e-8) equity = 1e-8;
    peak = Math.max(peak, equity);
    rs.push(realized);
    if (i <= w.trainEnd) trainRs.push(realized);
    else if (i <= w.valEnd) valRs.push(realized);
    else oosRs.push(realized);

    const sizeNow = equity > 0 ? lots.reduce((a, lot) => a + (lot.contracts * S) / equity, 0) : 0;
    bump(which, "prem", equity > 0 ? premium / (equity / (1 + realized) || 1) : 0);
    bump(which, "putSum", sizeNow);
    if (sizeNow > 0.02) bump(which, "withPut", 1);

    if (keepCurve) {
      curve.push({
        i,
        date: universe.dates[i],
        equity,
        drawdown: equity / peak - 1,
        regime: s.regime,
        building: s.building,
        qqqExp,
        putSize: sizeNow,
        putMark: lots.reduce((a, lot) => a + lot.contracts * lot.lastMark, 0),
        premium,
        strategyReturn: realized,
        vix: close("VIX", i),
      });
    }
  }

  const turnover = rs.length ? turns / rs.length : 0;
  const m = metrics(rs, turnover);
  const train = metrics(trainRs, turnover);
  const validation = metrics(valRs, turnover);
  const oos = metrics(oosRs, turnover);
  const pack = (mSplit: Metrics, a: typeof acc.full, n: number, nakedDd: number): ProtectedExtras =>
    extrasFrom(a.prem, n, a.rolls, a.add, a.opens, a.putSum, a.withPut, mSplit.maxDd, nakedDd);

  const extras = {
    full: pack(m, acc.full, rs.length, naked.metrics.maxDd),
    train: pack(train, acc.train, trainRs.length, naked.split.train.maxDd),
    validation: pack(validation, acc.val, valRs.length, naked.split.validation.maxDd),
    oos: pack(oos, acc.oos, oosRs.length, naked.split.oos.maxDd),
  };

  return {
    spec,
    metrics: m,
    split: { train, validation, oos },
    extras,
    score: protectedScore(validation, extras.validation),
    curve,
    oosLeakage: false,
    layer: "Derived",
    disclaimer: DISCLAIMER,
  };
}

export function firstWaveGrid(): ProtectedSpec[] {
  const out: ProtectedSpec[] = [];
  for (const putDistance of [0.02, 0.03, 0.05]) {
    for (const dte of [21, 30, 45]) {
      for (const rollDays of [7, 14]) {
        for (const calmPut of [0, 0.25]) {
          for (const unstablePut of [0.25, 0.5, 0.75]) {
            for (const tailPut of [0.75, 1, 1.5]) {
              for (const recoveryPut of [0.25, 0.5]) {
                out.push({
                  ...DEFAULT_PROTECTED,
                  putDistance,
                  dte,
                  rollDays,
                  calmPut,
                  unstablePut,
                  tailPut,
                  recoveryPut,
                });
              }
            }
          }
        }
      }
    }
  }
  return out;
}

/** TRAIN+VALIDATION only. */
export function searchProtected(): ProtectedResult[] {
  const w = sampleWindow();
  const grid = firstWaveGrid();
  const results = grid.map((spec) => runProtected(spec, w.start, w.valEnd, false));
  return results.sort((a, b) => b.score - a.score);
}

export function freezeProtected(candidates: ProtectedResult[]): ProtectedResult {
  const best = candidates[0] ?? runProtected(DEFAULT_PROTECTED);
  const w = sampleWindow();
  return runProtected(best.spec, w.start, w.end, true);
}

export function paretoProtected(results: ProtectedResult[]) {
  return results.filter(
    (a) =>
      !results.some(
        (b) =>
          b !== a &&
          b.split.validation.cagr >= a.split.validation.cagr &&
          b.split.validation.maxDd >= a.split.validation.maxDd &&
          b.extras.validation.premiumDrag <= a.extras.validation.premiumDrag &&
          (b.split.validation.cagr > a.split.validation.cagr ||
            b.split.validation.maxDd > a.split.validation.maxDd ||
            b.extras.validation.premiumDrag < a.extras.validation.premiumDrag),
      ),
  );
}


/** Custom windows for re-fit CPCV / walk-forward. Selection must not use test bars. */
export type ProtectedWindow = {
  simStart: number;
  simEnd: number;
  /** Inclusive score ranges; bars outside still simulate for path continuity when within sim range. */
  trainFrom: number;
  trainTo: number;
  valFrom: number;
  valTo: number;
  testFrom?: number;
  testTo?: number;
};

export type ProtectedWindowResult = {
  spec: ProtectedSpec;
  score: number;
  train: Metrics;
  validation: Metrics;
  test: Metrics | null;
  extras: { train: ProtectedExtras; validation: ProtectedExtras; test: ProtectedExtras | null };
  layer: "Derived";
  disclaimer: string;
  oosLeakage: false;
};

/**
 * Simulate [simStart, simEnd] and score train/val/test slices independently of sampleWindow().
 * Use for re-fit CPCV: search with simEnd=valTo (test omitted); evaluate champion with test range set.
 */
export function runProtectedWindow(
  spec: ProtectedSpec,
  win: ProtectedWindow,
  keepCurve = false,
): ProtectedWindowResult {
  const naked = nakedQQQ();
  const trainRs: number[] = [];
  const valRs: number[] = [];
  const testRs: number[] = [];
  const lots: Lot[] = [];
  let equity = 1;
  let peak = 1;
  let prevPut = 0;
  let turns = 0;
  let nAll = 0;
  const acc = {
    train: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
    val: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
    test: { prem: 0, rolls: 0, add: 0, opens: 0, putSum: 0, withPut: 0 },
  };

  const bump = (which: "train" | "val" | "test" | null, k: "prem" | "rolls" | "add" | "opens" | "putSum" | "withPut", x: number) => {
    if (!which) return;
    acc[which][k] += x;
  };

  const bucket = (i: number): "train" | "val" | "test" | null => {
    if (i >= win.trainFrom && i <= win.trainTo) return "train";
    if (i >= win.valFrom && i <= win.valTo) return "val";
    if (win.testFrom != null && win.testTo != null && i >= win.testFrom && i <= win.testTo) return "test";
    return null;
  };

  for (let i = Math.max(WARMUP, win.simStart); i <= win.simEnd; i++) {
    const qRet = ret("QQQ", i);
    const S = close("QQQ", i);
    if (qRet == null || S == null) continue;
    const s = state(i - 1);
    const dd = equity / peak - 1;
    const qqqExp = qqqExposure(s, spec, dd);
    const target = putTarget(s, spec);
    const iv = ivFromVix(i);
    const which = bucket(i);

    let putPnl = 0;
    let premium = 0;

    for (let k = lots.length - 1; k >= 0; k--) {
      const lot = lots[k];
      const mid = markPut(S, lot.strike, i, lot.expiryI, iv);
      putPnl += lot.contracts * (mid - lot.lastMark);
      lot.lastMark = mid;
      if (i >= lot.expiryI) lots.splice(k, 1);
    }

    const minExpiry = lots.reduce((m, lot) => Math.min(m, lot.expiryI), Infinity);
    const dueRoll = lots.length > 0 && remainingCalendarDays(i, minExpiry) <= spec.rollDays;
    if (dueRoll) {
      for (const lot of lots) {
        const hair = lot.lastMark * (1 - spec.spread);
        putPnl += lot.contracts * (hair - lot.lastMark);
        lot.lastMark = hair;
      }
      lots.length = 0;
      bump(which, "rolls", 1);
    }

    const currentSize = equity > 0 ? lots.reduce((a, lot) => a + (lot.contracts * S) / equity, 0) : 0;
    const needOpen = lots.length === 0 && target > 0.02;
    const needAdd = lots.length > 0 && target > currentSize + ADD_STEP;
    if ((needOpen || needAdd) && equity > 0) {
      const addSize = needOpen ? target : target - currentSize;
      const contracts = (addSize * equity) / S;
      const strike = roundStrike(S * (1 - spec.putDistance), S);
      const expiryI = expiryIndex(i, spec.dte);
      const mid = markPut(S, strike, i, expiryI, iv);
      const pay = mid * (1 + spec.spread);
      premium += contracts * pay;
      lots.push({ strike, expiryI, contracts, lastMark: mid, openedI: i });
      bump(which, "opens", 1);
      if (needAdd) bump(which, "add", 1);
    }

    if (Math.abs(target - prevPut) > 1e-6) turns += 1;
    prevPut = target;

    const rPut = equity > 0 ? (putPnl - premium) / equity : 0;
    const realized = qqqExp * qRet + rPut;
    equity *= 1 + realized;
    if (equity <= 1e-8) equity = 1e-8;
    peak = Math.max(peak, equity);
    nAll += 1;
    if (which === "train") trainRs.push(realized);
    else if (which === "val") valRs.push(realized);
    else if (which === "test") testRs.push(realized);

    const sizeNow = equity > 0 ? lots.reduce((a, lot) => a + (lot.contracts * S) / equity, 0) : 0;
    bump(which, "prem", equity > 0 ? premium / (equity / (1 + realized) || 1) : 0);
    bump(which, "putSum", sizeNow);
    if (sizeNow > 0.02) bump(which, "withPut", 1);
    void keepCurve;
  }

  const turnover = nAll ? turns / nAll : 0;
  const train = metrics(trainRs, turnover);
  const validation = metrics(valRs, turnover);
  const test = testRs.length ? metrics(testRs, turnover) : null;
  const pack = (mSplit: Metrics, a: typeof acc.train, n: number, nakedDd: number): ProtectedExtras =>
    extrasFrom(a.prem, n, a.rolls, a.add, a.opens, a.putSum, a.withPut, mSplit.maxDd, nakedDd);

  return {
    spec,
    score: protectedScore(validation, pack(validation, acc.val, valRs.length, naked.metrics.maxDd)),
    train,
    validation,
    test,
    extras: {
      train: pack(train, acc.train, trainRs.length, naked.metrics.maxDd),
      validation: pack(validation, acc.val, valRs.length, naked.metrics.maxDd),
      test: test ? pack(test, acc.test, testRs.length, naked.metrics.maxDd) : null,
    },
    layer: "Derived",
    disclaimer: DISCLAIMER,
    oosLeakage: false,
  };
}

/** Search first-wave grid using only train/val windows (sim ends at valTo). */
export function searchProtectedWindow(win: ProtectedWindow): ProtectedWindowResult[] {
  const selectWin: ProtectedWindow = { ...win, simEnd: win.valTo, testFrom: undefined, testTo: undefined };
  return firstWaveGrid()
    .map((spec) => runProtectedWindow(spec, selectWin, false))
    .sort((a, b) => b.score - a.score);
}

export function evaluateProtectedWindow(spec: ProtectedSpec, win: ProtectedWindow): ProtectedWindowResult {
  return runProtectedWindow(spec, { ...win, simEnd: win.testTo ?? win.valTo }, false);
}


export function assertPutCushionsDownDay(): { ok: true; date: string; qqq: number; overlay: number } {
  const q = universe.c.QQQ ?? [];
  let i = -1;
  for (let k = WARMUP + 5; k < q.length; k++) {
    const r = ret("QQQ", k);
    if (r != null && r <= -0.08) {
      i = k;
      break;
    }
  }
  if (i < 0) throw new Error("PUT_GUARD: no -8% QQQ day");
  const spec: ProtectedSpec = {
    ...DEFAULT_PROTECTED,
    calmPut: 1,
    unstablePut: 1,
    tailPut: 1,
    recoveryPut: 1,
    buildingPut: 1,
    putDistance: 0.02,
    dte: 30,
    rollDays: 7,
  };
  const one = runProtected(spec, i - 8, i, true);
  const last = one.curve[one.curve.length - 1];
  const qqq = ret("QQQ", i);
  if (!last || qqq == null) throw new Error("PUT_GUARD: missing bar");
  if (last.strategyReturn <= qqq + 0.002) {
    throw new Error(
      `PUT_GUARD: overlay did not cushion ${universe.dates[i]} qqq=${qqq} overlay=${last.strategyReturn}`,
    );
  }
  return { ok: true, date: universe.dates[i], qqq, overlay: last.strategyReturn };
}
