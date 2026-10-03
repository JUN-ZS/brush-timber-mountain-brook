import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData = {
  source?: string;
  asof: string;
  dates: string[];
  c: { QQQ?: Array<number | null> };
};
type MP = { date: string; close: number };
type SellState = "NORMAL" | "EXTENDED_CANDIDATE" | "ARMED" | "COOLDOWN";
type ReserveMode = "CURRENT_REUSE" | "ONE_SHOT_DD_RELEASE" | "RESERVE_STATE";
type ReserveState = "LOCKED" | "WEAKNESS_CANDIDATE" | "RESERVE_DEPLOYABLE" | "RECOVERY";

type Metrics = {
  terminalEconomicWealth: number;
  terminalCagr: number;
  rawMaxDd: number;
  economicMaxDd: number;
  externalContribution: number;
  sellEvents: number;
  harvestToReserve: number;
  releaseEvents: number;
  relockEvents: number;
  reserveUsedForBuy: number;
  terminalLockedReserve: number;
  terminalAvailableReserve: number;
  deployableMonths: number;
  principalBreach: boolean;
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(
  ROOT,
  process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1",
);

const H = 120;
const B = 1;
const SELL = 0.10;
const DD_TRIGGER = -0.10;
const CONFIRM_MONTHS = 2;
const RECOVERY_MONTHS = 2;

function monthly(data: QqqData): MP[] {
  const out = new Map<string, MP>();
  const ds = data.dates ?? [];
  const cs = data.c.QQQ ?? [];

  for (let i = 0; i < Math.min(ds.length, cs.length); i++) {
    const date = ds[i];
    const close = Number(cs[i]);
    if (
      !Number.isFinite(close) ||
      close <= 0 ||
      typeof date !== "string" ||
      !/^\d{4}-\d{2}-\d{2}$/.test(date)
    ) {
      continue;
    }
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
    const lo = Math.floor(z);
    const hi = Math.ceil(z);
    return s[lo] + (s[hi] - s[lo]) * (z - lo);
  };
  return {
    n: xs.length,
    mean,
    median: q(0.50),
    q05: q(0.05),
    q25: q(0.25),
    q75: q(0.75),
    q95: q(0.95),
    positiveRate: xs.filter((x) => x > 0).length / Math.max(1, xs.length),
  };
}

function dd12(pr: number[], i: number): number {
  if (i < 12) return 0;
  const high = Math.max(...pr.slice(i - 11, i + 1));
  return pr[i] / high - 1;
}

function extension(pr: number[], i: number): boolean {
  if (i < 12) return false;
  const p = pr[i];
  const high = Math.max(...pr.slice(i - 11, i + 1));
  return p >= 0.95 * high - 1e-12 && p / pr[i - 6] - 1 >= 0.15;
}

function clock(pr: number[]): Metrics {
  let shares = 0;
  let planned = B;
  const raw = [0];
  const economic = [B];

  for (let t = 1; t <= H; t++) {
    const contribution = Math.min(planned, B / H);
    planned -= contribution;
    shares += contribution / pr[t];
    const nav = shares * pr[t];
    raw.push(nav);
    economic.push(nav + planned);
  }

  const ew = economic[H];
  return {
    terminalEconomicWealth: ew,
    terminalCagr: Math.pow(Math.max(1e-12, ew), 0.1) - 1,
    rawMaxDd: maxDd(raw.slice(1)),
    economicMaxDd: maxDd(economic),
    externalContribution: B - planned,
    sellEvents: 0,
    harvestToReserve: 0,
    releaseEvents: 0,
    relockEvents: 0,
    reserveUsedForBuy: 0,
    terminalLockedReserve: 0,
    terminalAvailableReserve: planned,
    deployableMonths: 0,
    principalBreach: ew < B - 1e-10,
  };
}

function simulate(pr: number[], mode: ReserveMode): Metrics {
  let shares = 0;
  let planned = B;
  let lockedReserve = 0;
  let availableReserve = 0;

  let sellEvents = 0;
  let harvestToReserve = 0;
  let releaseEvents = 0;
  let relockEvents = 0;
  let reserveUsedForBuy = 0;
  let deployableMonths = 0;
  let oneShotReleased = false;

  let sellState: SellState = "NORMAL";
  let soldInEpisode = false;

  let reserveState: ReserveState = mode === "CURRENT_REUSE"
    ? "RESERVE_DEPLOYABLE"
    : "LOCKED";
  let weaknessCount = 0;
  let recoveryCount = 0;

  const raw = [0];
  const economic = [B];

  for (let t = 1; t <= H; t++) {
    const i = t - 1;
    const pricePrev = pr[i];
    const prevNav = shares * pricePrev;
    const target = (t / H) * B;
    const isExtended = extension(pr, i);
    const weakness = dd12(pr, i) <= DD_TRIGGER + 1e-12;
    const recovered = dd12(pr, i) > DD_TRIGGER + 1e-12;

    // Fixed SELL state machine; identical across all reserve modes.
    if (sellState === "NORMAL") {
      if (isExtended) {
        sellState = "EXTENDED_CANDIDATE";
        soldInEpisode = false;
      }
    } else if (sellState === "EXTENDED_CANDIDATE") {
      sellState = isExtended ? "ARMED" : "NORMAL";
    } else if (sellState === "ARMED") {
      if (isExtended && prevNav > target + 1e-12) {
        const sellAmountPrev = SELL * (prevNav - target);
        const sellShares = Math.min(
          shares,
          sellAmountPrev / Math.max(pricePrev, 1e-12),
        );
        if (sellShares > 0) {
          if (soldInEpisode) throw new Error("SELL_EPISODE_DUPLICATE");
          const proceeds = sellShares * pr[t];
          shares -= sellShares;
          sellEvents++;
          harvestToReserve += proceeds;

          if (mode === "CURRENT_REUSE") {
            availableReserve += proceeds;
          } else {
            lockedReserve += proceeds;
          }

          soldInEpisode = true;
          sellState = "COOLDOWN";
        }
      } else if (!isExtended) {
        sellState = "NORMAL";
      }
    } else if (sellState === "COOLDOWN" && !isExtended) {
      sellState = "NORMAL";
    }

    // Reserve eligibility uses only t-1 information.
    if (mode === "ONE_SHOT_DD_RELEASE") {
      if (!oneShotReleased && lockedReserve > 1e-12 && weakness) {
        availableReserve += lockedReserve;
        lockedReserve = 0;
        oneShotReleased = true;
        releaseEvents++;
      }
    } else if (mode === "RESERVE_STATE") {
      if (reserveState === "LOCKED") {
        if (weakness) {
          reserveState = "WEAKNESS_CANDIDATE";
          weaknessCount = 1;
          recoveryCount = 0;
        }
      } else if (reserveState === "WEAKNESS_CANDIDATE") {
        if (weakness) {
          weaknessCount++;
          if (weaknessCount >= CONFIRM_MONTHS) {
            reserveState = "RESERVE_DEPLOYABLE";
            weaknessCount = 0;
            recoveryCount = 0;
            if (lockedReserve > 1e-12) {
              availableReserve += lockedReserve;
              lockedReserve = 0;
              releaseEvents++;
            }
          }
        } else {
          reserveState = "LOCKED";
          weaknessCount = 0;
          recoveryCount = 0;
        }
      } else if (reserveState === "RESERVE_DEPLOYABLE") {
        if (recovered) {
          reserveState = "RECOVERY";
          recoveryCount = 1;
        } else {
          recoveryCount = 0;
        }
      } else if (reserveState === "RECOVERY") {
        if (weakness) {
          reserveState = "RESERVE_DEPLOYABLE";
          recoveryCount = 0;
        } else if (recovered) {
          recoveryCount++;
          if (recoveryCount >= RECOVERY_MONTHS) {
            reserveState = "LOCKED";
            recoveryCount = 0;
            if (availableReserve > 1e-12) {
              lockedReserve += availableReserve;
              availableReserve = 0;
              relockEvents++;
            }
          }
        }
      }
    }

    const canUseReserve =
      mode === "CURRENT_REUSE" ||
      mode === "ONE_SHOT_DD_RELEASE" ||
      reserveState === "RESERVE_DEPLOYABLE";

    if (canUseReserve) deployableMonths++;

    // BUY remains the same full-shortfall chase toward unchanged CLOCK target.
    if (prevNav < target - 1e-12) {
      let need = target - prevNav;

      const fromReserve = canUseReserve
        ? Math.min(availableReserve, need)
        : 0;
      availableReserve -= fromReserve;
      need -= fromReserve;
      reserveUsedForBuy += fromReserve;

      const fromPlanned = Math.min(planned, need);
      planned -= fromPlanned;
      need -= fromPlanned;

      if (need > 1e-9) throw new Error("BUY_SHORTFALL_UNFUNDED");

      const used = fromReserve + fromPlanned;
      if (used > 0) shares += used / pr[t];
    }

    const nav = shares * pr[t];
    raw.push(nav);
    economic.push(nav + planned + lockedReserve + availableReserve);
  }

  const ew = economic[H];
  return {
    terminalEconomicWealth: ew,
    terminalCagr: Math.pow(Math.max(1e-12, ew), 0.1) - 1,
    rawMaxDd: maxDd(raw.slice(1)),
    economicMaxDd: maxDd(economic),
    externalContribution: B - planned,
    sellEvents,
    harvestToReserve,
    releaseEvents,
    relockEvents,
    reserveUsedForBuy,
    terminalLockedReserve: lockedReserve,
    terminalAvailableReserve: availableReserve,
    deployableMonths,
    principalBreach: ew < B - 1e-10,
  };
}

type Window = {
  start: string;
  end: string;
  clock: Metrics;
  current: Metrics;
  oneShot: Metrics;
  state: Metrics;
};

function compare(
  rows: Window[],
  left: keyof Pick<Window, "current" | "oneShot" | "state">,
  right: keyof Pick<Window, "clock" | "current" | "oneShot" | "state">,
) {
  const terminal = rows.map(
    (r) => r[left].terminalEconomicWealth - r[right].terminalEconomicWealth,
  );
  const rawDd = rows.map(
    (r) => (r[left].rawMaxDd - r[right].rawMaxDd) * 100,
  );
  const ecoDd = rows.map(
    (r) => (r[left].economicMaxDd - r[right].economicMaxDd) * 100,
  );
  const cagr = rows.map(
    (r) => (r[left].terminalCagr - r[right].terminalCagr) * 100,
  );

  return {
    terminalDelta: summarize(terminal),
    rawMaxDdDeltaPp: summarize(rawDd),
    economicMaxDdDeltaPp: summarize(ecoDd),
    cagrDeltaPp: summarize(cagr),
    higherTerminalWindows: terminal.filter((x) => x > 0).length,
    lowerRawDdWindows: rawDd.filter((x) => x < 0).length,
    lowerEconomicDdWindows: ecoDd.filter((x) => x < 0).length,
    higherCagrWindows: cagr.filter((x) => x > 0).length,
  };
}

function run() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as QqqData;
  const months = monthly(data);
  const rows: Window[] = [];

  if (months.length < H + 1) throw new Error("NOT_ENOUGH_MONTHLY_DATA");

  for (let start = 0; start + H < months.length; start++) {
    const pr = months.slice(start, start + H + 1).map((x) => x.close);
    rows.push({
      start: months[start].date,
      end: months[start + H].date,
      clock: clock(pr),
      current: simulate(pr, "CURRENT_REUSE"),
      oneShot: simulate(pr, "ONE_SHOT_DD_RELEASE"),
      state: simulate(pr, "RESERVE_STATE"),
    });
  }

  const failures: string[] = [];
  for (const row of rows) {
    for (const item of [
      ["CLOCK", row.clock],
      ["CURRENT_REUSE", row.current],
      ["ONE_SHOT_DD_RELEASE", row.oneShot],
      ["RESERVE_STATE", row.state],
    ] as const) {
      const label = item[0];
      const m = item[1];
      if (m.externalContribution > B + 1e-8) failures.push(row.start + " " + label + " external budget");
      if (m.terminalEconomicWealth < B - 1e-8) failures.push(row.start + " " + label + " principal breach");
      if (!Number.isFinite(m.terminalEconomicWealth)) failures.push(row.start + " " + label + " non-finite");
      if (m.terminalLockedReserve < -1e-10 || m.terminalAvailableReserve < -1e-10) failures.push(row.start + " " + label + " negative reserve");
    }
  }

  if (failures.length) throw new Error("RESERVE_STATE_INVARIANT_FAIL " + failures.slice(0, 20).join(" | "));

  const report = {
    researchId: "QQQ_MUTUAL_CHASE_RESERVE_STATE_V1",
    status: "RESEARCH_ONLY",
    provenance: {
      source: "src/data/universe.json",
      sourceAsOf: data.asof,
      monthlyPoints: months.length,
      completeRollingWindows: rows.length,
      overlappingWindows: true,
    },
    fixedRules: {
      target: "C_t = B*t/120; unchanged across all variants",
      sell: {
        fraction: SELL,
        eligibility: "POST_RUNUP = prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high",
        confirmation: "two consecutive qualifying prior month-ends",
        cooldown: "one SELL maximum per continuous POST_RUNUP episode",
      },
      reserveEligibility: {
        weaknessSignal: "prior QQQ trailing 12M drawdown <= -10%",
        confirmMonths: CONFIRM_MONTHS,
        recoverySignal: "prior QQQ trailing 12M drawdown > -10%",
        recoveryMonths: RECOVERY_MONTHS,
        action: "state machine gates reserve reuse only; it does not change target or add extra BUY exposure",
        decision: "t-1 month-end",
        execution: "t month-end close",
        futurePriceRead: false,
        parameterSearch: false,
        winnerSelection: false,
      },
    },
    variants: {
      CURRENT_REUSE: "Harvested reserve is immediately reusable against any future CLOCK shortfall.",
      ONE_SHOT_DD_RELEASE: "Harvested reserve remains locked until the fixed 12M DD <= -10% trigger occurs once; then it remains reusable thereafter.",
      RESERVE_STATE: "Harvested reserve remains locked; the same DD <= -10% weakness must persist for two consecutive month-ends before release. After two consecutive months above -10% DD, any unused reserve is re-locked.",
    },
    comparisons: {
      currentVsClock: compare(rows, "current", "clock"),
      oneShotVsClock: compare(rows, "oneShot", "clock"),
      stateVsClock: compare(rows, "state", "clock"),
      stateVsCurrent: compare(rows, "state", "current"),
      stateVsOneShot: compare(rows, "state", "oneShot"),
    },
    windows: rows,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(
    resolve(OUT_DIR, "qqq_mutual_chase_reserve_state_v1.json"),
    JSON.stringify(report, null, 2),
  );

  const summaryRows = [
    ["CURRENT_REUSE vs CLOCK", report.comparisons.currentVsClock],
    ["ONE_SHOT_DD_RELEASE vs CLOCK", report.comparisons.oneShotVsClock],
    ["RESERVE_STATE vs CLOCK", report.comparisons.stateVsClock],
    ["RESERVE_STATE vs CURRENT_REUSE", report.comparisons.stateVsCurrent],
    ["RESERVE_STATE vs ONE_SHOT_DD_RELEASE", report.comparisons.stateVsOneShot],
  ] as const;

  const md = [
    "# QQQ_MUTUAL_CHASE_RESERVE_STATE_V1",
    "",
    "> RESEARCH_ONLY / DIAGNOSTIC_ONLY. No formal 10Y Floor authority and no broker execution authority.",
    "",
    "## Research question",
    "",
    "Does stateful reserve eligibility add incremental deployment value over immediate reserve reuse, while leaving the CLOCK target unchanged?",
    "",
    "## Fixed reserve state",
    "",
    "| State | Condition | Reserve action |",
    "| --- | --- | --- |",
    "| LOCKED | default / post-recovery | reserve cannot fund BUY |",
    "| WEAKNESS_CANDIDATE | first month with QQQ 12M DD <= -10% | still locked |",
    "| RESERVE_DEPLOYABLE | second consecutive month with DD <= -10% | release locked reserve; it may fund future CLOCK shortfalls |",
    "| RECOVERY | first month with DD > -10% after deployability | reserve remains deployable while recovery is confirmed |",
    "| LOCKED | second consecutive recovery month | re-lock any unused reserve |",
    "",
    "The reserve state is an eligibility gate only. It never changes C_t = B*t/120 and never forces an extra BUY.",
    "",
    "## Fair controls",
    "",
    "- CURRENT_REUSE: harvested reserve is immediately reusable.",
    "- ONE_SHOT_DD_RELEASE: same -10% trigger, but release occurs once and never re-locks.",
    "- RESERVE_STATE: same trigger, with two-month confirmation and two-month recovery hysteresis.",
    "",
    "The SELL mechanism is identical across all three modes: 10% of prior-close surplus, POST_RUNUP eligibility, two-observation confirmation, one SELL per continuous episode.",
    "",
    "## Runtime summary",
    "",
    "| Comparison | Mean terminal Δ | Mean raw MaxDD Δ | Mean economic MaxDD Δ | Mean CAGR Δ pp | Higher terminal | Lower economic MaxDD |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...summaryRows.map(([name, r]) =>
      "| " + name + " | " +
      r.terminalDelta.mean.toFixed(6) + " B | " +
      r.rawMaxDdDeltaPp.mean.toFixed(3) + " pp | " +
      r.economicMaxDdDeltaPp.mean.toFixed(3) + " pp | " +
      r.cagrDeltaPp.mean.toFixed(3) + " pp | " +
      r.higherTerminalWindows + "/" + rows.length + " | " +
      r.lowerEconomicDdWindows + "/" + rows.length + " |"
    ),
    "",
    "## Gate",
    "",
    "The decisive evidence is the incremental result RESERVE_STATE vs CURRENT_REUSE and the isolation result RESERVE_STATE vs ONE_SHOT_DD_RELEASE. No variant is promoted automatically.",
  ].join("\\n");

  writeFileSync(
    resolve(OUT_DIR, "qqq_mutual_chase_reserve_state_v1.md"),
    md,
  );

  const csv = [
    [
      "start","end",
      "clock_ew","current_ew","oneShot_ew","state_ew",
      "state_minus_current_ew","state_minus_oneShot_ew",
      "clock_raw_dd","current_raw_dd","oneShot_raw_dd","state_raw_dd",
      "clock_eco_dd","current_eco_dd","oneShot_eco_dd","state_eco_dd",
      "state_minus_current_eco_dd_pp","state_minus_oneShot_eco_dd_pp",
      "current_cagr_pct","oneShot_cagr_pct","state_cagr_pct",
      "state_minus_current_cagr_pp","state_minus_oneShot_cagr_pp",
      "current_sells","oneShot_sells","state_sells",
      "current_release","oneShot_release","state_release",
      "state_relock","state_reserve_used"
    ].join(","),
    ...rows.map((r) => [
      r.start,r.end,
      r.clock.terminalEconomicWealth,r.current.terminalEconomicWealth,r.oneShot.terminalEconomicWealth,r.state.terminalEconomicWealth,
      r.state.terminalEconomicWealth-r.current.terminalEconomicWealth,
      r.state.terminalEconomicWealth-r.oneShot.terminalEconomicWealth,
      r.clock.rawMaxDd,r.current.rawMaxDd,r.oneShot.rawMaxDd,r.state.rawMaxDd,
      r.clock.economicMaxDd,r.current.economicMaxDd,r.oneShot.economicMaxDd,r.state.economicMaxDd,
      (r.state.economicMaxDd-r.current.economicMaxDd)*100,
      (r.state.economicMaxDd-r.oneShot.economicMaxDd)*100,
      r.current.terminalCagr*100,r.oneShot.terminalCagr*100,r.state.terminalCagr*100,
      (r.state.terminalCagr-r.current.terminalCagr)*100,
      (r.state.terminalCagr-r.oneShot.terminalCagr)*100,
      r.current.sellEvents,r.oneShot.sellEvents,r.state.sellEvents,
      r.current.releaseEvents,r.oneShot.releaseEvents,r.state.releaseEvents,
      r.state.relockEvents,r.state.reserveUsedForBuy,
    ].map((x) => JSON.stringify(x)).join(",")),
  ].join("\\n") + "\\n";

  writeFileSync(
    resolve(OUT_DIR, "qqq_mutual_chase_reserve_state_v1.csv"),
    csv,
  );

  console.log(JSON.stringify({
    provenance: report.provenance,
    comparisons: report.comparisons,
  }, null, 2));
}

run();
