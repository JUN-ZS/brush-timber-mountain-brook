import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData = { source: string; asof: string; dates: string[]; c: { QQQ?: Array<number | null> } };
type MonthlyPoint = { date: string; close: number };
type SellState = "NORMAL" | "EXTENDED_CANDIDATE" | "ARMED" | "COOLDOWN";
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

type PathResult = {
  startDate: string;
  endDate: string;
  clock: Metrics;
  staticPostRunup: Metrics;
  stateMachine: Metrics;
  stateMachineSellEvents: number;
  stateMachineStateChanges: number;
  stateMachineExtensionEpisodes: number;
};

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DATA_PATH = resolve(ROOT, "src/data/universe.json");
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H = 120;
const B = 1;

// Fixed action size chosen before this state-machine result is inspected.
// This is the previously observed low-drag region, not a tuned winner inside this experiment.
const SELL = 0.10;

// Fixed extension condition inherited verbatim from POST_RUNUP timing research.
// No threshold search is performed here.
function monthlyQqq(data: QqqData): MonthlyPoint[] {
  const dates = data.dates ?? [];
  const closes = data.c.QQQ ?? [];
  const byMonth = new Map<string, MonthlyPoint>();
  for (let i = 0; i < Math.min(dates.length, closes.length); i++) {
    const close = Number(closes[i]);
    const date = dates[i];
    if (!Number.isFinite(close) || close <= 0 || !/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;
    const key = date.slice(0, 7);
    const prev = byMonth.get(key);
    if (!prev || date > prev.date) byMonth.set(key, { date, close });
  }
  return [...byMonth.values()].sort((a, b) => a.date.localeCompare(b.date));
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
    median: q(0.5),
    q05: q(0.05),
    q25: q(0.25),
    q75: q(0.75),
    q95: q(0.95),
    positiveRate: xs.length ? xs.filter((x) => x > 0).length / xs.length : 0,
  };
}

function isExtended(pr: number[], i: number): boolean {
  if (i < 12 || i < 6) return false;
  const p = pr[i];
  const h12 = Math.max(...pr.slice(Math.max(0, i - 11), i + 1));
  const near12mHigh = p >= 0.95 * h12 - 1e-12;
  const runup6m = p / pr[i - 6] - 1;
  return near12mHigh && runup6m >= 0.15;
}

function clock(pr: number[]): Metrics {
  let shares = 0;
  let plannedReserve = B;
  const raw = [0];
  const eco = [B];

  for (let t = 1; t <= H; t++) {
    const c = Math.min(plannedReserve, B / H);
    plannedReserve -= c;
    shares += c / pr[t];
    const nav = shares * pr[t];
    raw.push(nav);
    eco.push(nav + plannedReserve);
  }

  const ew = eco[H];
  return {
    totalExternalContribution: B,
    contributionEvents: H,
    totalHarvestToReserve: 0,
    harvestEvents: 0,
    terminalNav: raw[H],
    terminalEconomicWealth: ew,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, ew), 0.1) - 1,
    rawAccountMaxDd: maxDd(raw.slice(1)),
    economicMaxDd: maxDd(eco),
    principalBreach: ew < B - 1e-10,
  };
}

function simulateStaticPostRunup(pr: number[]): Metrics {
  let shares = 0;
  let plannedReserve = B;
  let harvestReserve = 0;
  let totalExternalContribution = 0;
  let contributionEvents = 0;
  let totalHarvestToReserve = 0;
  let harvestEvents = 0;
  const raw = [0];
  const eco = [B];

  for (let t = 1; t <= H; t++) {
    const target = (t / H) * B;
    const i = t - 1;
    const prevNav = shares * pr[i];

    if (prevNav > target + 1e-12 && isExtended(pr, i)) {
      const sellAmountAtPrevClose = SELL * (prevNav - target);
      const sellShares = Math.min(shares, sellAmountAtPrevClose / Math.max(pr[i], 1e-12));
      const proceedsAtCurrentClose = sellShares * pr[t];
      if (sellShares > 0) {
        shares -= sellShares;
        harvestReserve += proceedsAtCurrentClose;
        totalHarvestToReserve += proceedsAtCurrentClose;
        harvestEvents++;
      }
    } else if (prevNav < target - 1e-12) {
      let need = target - prevNav;
      const fromHarvest = Math.min(harvestReserve, need);
      harvestReserve -= fromHarvest;
      need -= fromHarvest;
      const fromPlanned = Math.min(plannedReserve, need);
      plannedReserve -= fromPlanned;
      totalExternalContribution += fromPlanned;
      if (fromPlanned > 1e-12) contributionEvents++;
      const used = fromHarvest + fromPlanned;
      if (used > 0) shares += used / pr[t];
    }

    const nav = shares * pr[t];
    raw.push(nav);
    eco.push(nav + plannedReserve + harvestReserve);
  }

  const ew = eco[H];
  return {
    totalExternalContribution,
    contributionEvents,
    totalHarvestToReserve,
    harvestEvents,
    terminalNav: raw[H],
    terminalEconomicWealth: ew,
    terminalEconomicCagr: Math.pow(Math.max(1e-12, ew), 0.1) - 1,
    rawAccountMaxDd: maxDd(raw.slice(1)),
    economicMaxDd: maxDd(eco),
    principalBreach: ew < B - 1e-10,
  };
}

/**
 * SELL STATE MACHINE
 *
 * NORMAL
 *   -> EXTENDED_CANDIDATE when prior month-end is objectively extended.
 *
 * EXTENDED_CANDIDATE
 *   -> ARMED when the extension condition persists for a second consecutive
 *      prior month-end observation.
 *   -> NORMAL when extension disappears.
 *
 * ARMED
 *   -> SELL one fixed 10% slice of prior-close surplus, then COOLDOWN.
 *
 * COOLDOWN
 *   -> remains closed to SELL even while extension persists.
 *   -> NORMAL only after the extension condition breaks.
 *
 * This creates hysteresis:
 * - confirmation prevents one-month extension from causing a harvest;
 * - cooldown prevents repeated monthly selling inside one persistent run-up;
 * - a new harvest requires a fresh extension episode.
 *
 * Causality:
 * - state transition and SELL amount use only t-1 month-end information;
 * - execution occurs at t month-end close;
 * - no future price is read.
 */
function simulateStateMachine(pr: number[]): { metrics: Metrics; sellEvents: number; stateChanges: number; extensionEpisodes: number } {
  let shares = 0;
  let plannedReserve = B;
  let harvestReserve = 0;
  let totalExternalContribution = 0;
  let contributionEvents = 0;
  let totalHarvestToReserve = 0;
  let harvestEvents = 0;
  let state: SellState = "NORMAL";
  let sellEvents = 0;
  let stateChanges = 0;
  let extensionEpisodes = 0;
  let soldInCurrentEpisode = false;

  const raw = [0];
  const eco = [B];

  for (let t = 1; t <= H; t++) {
    const target = (t / H) * B;
    const i = t - 1;
    const prevPrice = pr[i];
    const prevNav = shares * prevPrice;
    const extended = isExtended(pr, i);

    const prevState = state;
    if (state === "NORMAL") {
      if (extended) {
        state = "EXTENDED_CANDIDATE";
        extensionEpisodes++;
        soldInCurrentEpisode = false;
      }
    } else if (state === "EXTENDED_CANDIDATE") {
      if (extended) state = "ARMED";
      else state = "NORMAL";
    } else if (state === "ARMED") {
      if (extended && prevNav > target + 1e-12) {
        const sellAmountAtPrevClose = SELL * (prevNav - target);
        const sellShares = Math.min(shares, sellAmountAtPrevClose / Math.max(prevPrice, 1e-12));
        if (sellShares > 0) {
          if (soldInCurrentEpisode) throw new Error("SELL_STATE_MACHINE_DUPLICATE_EPISODE_SELL");
          const proceedsAtCurrentClose = sellShares * pr[t];
          shares -= sellShares;
          harvestReserve += proceedsAtCurrentClose;
          totalHarvestToReserve += proceedsAtCurrentClose;
          harvestEvents++;
          sellEvents++;
          soldInCurrentEpisode = true;
          state = "COOLDOWN";
        }
      } else if (!extended) {
        state = "NORMAL";
      }
    } else if (state === "COOLDOWN") {
      if (!extended) state = "NORMAL";
    }

    if (state !== prevState) stateChanges++;

    // BUY side remains the same full-shortfall chase as the existing mutual-chase research.
    // A SELL and BUY cannot happen on the same decision because the surplus/shortfall conditions are mutually exclusive.
    if (prevNav < target - 1e-12) {
      let need = target - prevNav;
      const fromHarvest = Math.min(harvestReserve, need);
      harvestReserve -= fromHarvest;
      need -= fromHarvest;

      const fromPlanned = Math.min(plannedReserve, need);
      plannedReserve -= fromPlanned;
      totalExternalContribution += fromPlanned;
      if (fromPlanned > 1e-12) contributionEvents++;

      const used = fromHarvest + fromPlanned;
      if (used > 0) shares += used / pr[t];
    }

    const nav = shares * pr[t];
    raw.push(nav);
    eco.push(nav + plannedReserve + harvestReserve);

    // Structural invariant: at most one SELL may occur inside each continuous extension episode.
    if (sellEvents > extensionEpisodes) {
      throw new Error("SELL_STATE_MACHINE_EPISODE_SELL_COUNT_FAIL");
    }
  }

  const ew = eco[H];
  return {
    metrics: {
      totalExternalContribution,
      contributionEvents,
      totalHarvestToReserve,
      harvestEvents,
      terminalNav: raw[H],
      terminalEconomicWealth: ew,
      terminalEconomicCagr: Math.pow(Math.max(1e-12, ew), 0.1) - 1,
      rawAccountMaxDd: maxDd(raw.slice(1)),
      economicMaxDd: maxDd(eco),
      principalBreach: ew < B - 1e-10,
    },
    sellEvents,
    stateChanges,
    extensionEpisodes,
  };
}

function run() {
  const data = JSON.parse(readFileSync(DATA_PATH, "utf8")) as QqqData;
  const months = monthlyQqq(data);
  const windows: PathResult[] = [];

  for (let start = 0; start + H < months.length; start++) {
    const pr = months.slice(start, start + H + 1).map((x) => x.close);
    const c = clock(pr);
    const s = simulateStaticPostRunup(pr);
    const sm = simulateStateMachine(pr);
    windows.push({
      startDate: months[start].date,
      endDate: months[start + H].date,
      clock: c,
      staticPostRunup: s,
      stateMachine: sm.metrics,
      stateMachineSellEvents: sm.sellEvents,
      stateMachineStateChanges: sm.stateChanges,
      stateMachineExtensionEpisodes: sm.extensionEpisodes,
    });
  }

  const failures: string[] = [];
  for (const p of windows) {
    for (const [name, m] of [["CLOCK", p.clock], ["STATIC_POST_RUNUP", p.staticPostRunup], ["STATE_MACHINE", p.stateMachine]] as const) {
      if (m.totalExternalContribution > B + 1e-8) failures.push(p.startDate + " " + name + " external budget");
      if (m.terminalEconomicWealth < B - 1e-8) failures.push(p.startDate + " " + name + " economic wealth below principal");
      if (!Number.isFinite(m.terminalEconomicWealth)) failures.push(p.startDate + " " + name + " non-finite");
    }
    if (p.stateMachineSellEvents > p.stateMachineExtensionEpisodes) failures.push(p.startDate + " more SELLs than extension episodes");
    if (p.stateMachineStateChanges < p.stateMachineSellEvents) failures.push(p.startDate + " SELL transition accounting");
  }
  if (failures.length) throw new Error("SELL_STATE_MACHINE_INVARIANT_FAIL " + failures.slice(0, 20).join(" | "));

  const compare = (key: "staticPostRunup" | "stateMachine") => {
    const rows = windows.map((p) => {
      const m = p[key];
      return {
        deltaTerminal: m.terminalEconomicWealth - p.clock.terminalEconomicWealth,
        deltaRawDd: m.rawAccountMaxDd - p.clock.rawAccountMaxDd,
        deltaEconomicDd: m.economicMaxDd - p.clock.economicMaxDd,
        deltaCagrPp: (m.terminalEconomicCagr - p.clock.terminalEconomicCagr) * 100,
        externalContribution: m.totalExternalContribution,
        harvest: m.totalHarvestToReserve,
        sells: m.harvestEvents,
      };
    });
    return {
      terminalDelta: summarize(rows.map((x) => x.deltaTerminal)),
      rawMaxDdDeltaPp: summarize(rows.map((x) => x.deltaRawDd * 100)),
      economicMaxDdDeltaPp: summarize(rows.map((x) => x.deltaEconomicDd * 100)),
      cagrDeltaPp: summarize(rows.map((x) => x.deltaCagrPp)),
      externalContributionPercent: summarize(rows.map((x) => x.externalContribution * 100)),
      harvestToReservePercent: summarize(rows.map((x) => x.harvest * 100)),
      sellEvents: summarize(rows.map((x) => x.sells)),
      positiveTerminalVsClock: rows.filter((x) => x.deltaTerminal > 0).length,
    };
  };

  const stateMachineVsStatic = windows.map((p) => ({
    deltaTerminal: p.stateMachine.terminalEconomicWealth - p.staticPostRunup.terminalEconomicWealth,
    deltaRawDd: p.stateMachine.rawAccountMaxDd - p.staticPostRunup.rawAccountMaxDd,
    deltaEconomicDd: p.stateMachine.economicMaxDd - p.staticPostRunup.economicMaxDd,
    deltaCagrPp: (p.stateMachine.terminalEconomicCagr - p.staticPostRunup.terminalEconomicCagr) * 100,
  }));

  const report = {
    researchId: "QQQ_MUTUAL_CHASE_SELL_STATE_MACHINE_V1",
    status: "RESEARCH_ONLY",
    question: "Does a fixed SELL state machine add value beyond simply reducing SELL frequency under the same POST_RUNUP eligibility?",
    provenance: {
      source: "src/data/universe.json",
      sourceAsOf: data.asof,
      monthlyPoints: months.length,
      completeRollingWindows: windows.length,
      overlappingWindows: true,
    },
    fixedRule: {
      target: "C_t = B*t/120",
      buy: "Full shortfall below target; reuse harvested reserve first, then planned reserve.",
      sellFraction: SELL,
      eligibility: "POST_RUNUP = prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.",
      stateMachine: {
        NORMAL: "No SELL eligibility.",
        EXTENDED_CANDIDATE: "First consecutive month-end with POST_RUNUP true.",
        ARMED: "Second consecutive month-end with POST_RUNUP true.",
        COOLDOWN: "Entered immediately after one SELL; no further SELL until POST_RUNUP breaks.",
      },
      confirmation: "Two consecutive qualifying prior month-ends before the first SELL in an episode.",
      cooldown: "One SELL maximum per continuous POST_RUNUP episode.",
      decisionData: "t-1 month-end only.",
      execution: "t month-end close.",
      futurePriceRead: false,
      parameterSearch: false,
      winnerSelection: false,
    },
    fairComparisons: {
      CLOCK: "B/120 each month; no tactical SELL.",
      STATIC_POST_RUNUP: "Same POST_RUNUP condition and same fixed 10% SELL fraction, but no confirmation/cooldown state machine.",
      STATE_MACHINE: "Same condition and same 10% SELL fraction, with fixed confirmation + cooldown hysteresis.",
    },
    comparisonVsClock: {
      staticPostRunup: compare("staticPostRunup"),
      stateMachine: compare("stateMachine"),
    },
    stateMachineVsStaticPostRunup: {
      terminalDelta: summarize(stateMachineVsStatic.map((x) => x.deltaTerminal)),
      rawMaxDdDeltaPp: summarize(stateMachineVsStatic.map((x) => x.deltaRawDd * 100)),
      economicMaxDdDeltaPp: summarize(stateMachineVsStatic.map((x) => x.deltaEconomicDd * 100)),
      cagrDeltaPp: summarize(stateMachineVsStatic.map((x) => x.deltaCagrPp)),
      betterTerminalWindows: stateMachineVsStatic.filter((x) => x.deltaTerminal > 0).length,
      lowerRawDdWindows: stateMachineVsStatic.filter((x) => x.deltaRawDd < 0).length,
      lowerEconomicDdWindows: stateMachineVsStatic.filter((x) => x.deltaEconomicDd < 0).length,
      higherCagrWindows: stateMachineVsStatic.filter((x) => x.deltaCagrPp > 0).length,
    },
    windows,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_sell_state_machine_v1.json"), JSON.stringify(report, null, 2));

  const md = [
    "# QQQ_MUTUAL_CHASE_SELL_STATE_MACHINE_V1",
    "",
    "> RESEARCH_ONLY / DIAGNOSTIC_ONLY. No formal 10Y Floor authority and no broker execution authority.",
    "",
    "## Fixed state machine",
    "",
    "| State | Transition | SELL action |",
    "| --- | --- | --- |",
    "| NORMAL | POST_RUNUP becomes true | none |",
    "| EXTENDED_CANDIDATE | POST_RUNUP remains true for one more month-end | none |",
    "| ARMED | second consecutive qualifying observation | one 10% SELL of prior-close surplus |",
    "| COOLDOWN | immediately after SELL | no SELL until POST_RUNUP breaks |",
    "",
    "POST_RUNUP is fixed as prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.",
    "",
    "The purpose is hysteresis, not threshold optimization: confirm the state before harvesting, then block repeated harvesting during the same persistent extension episode.",
    "",
    "## Fair isolation test",
    "",
    "The state machine is compared against a static rule with the exact same POST_RUNUP condition and exact same 10% SELL fraction. Therefore any improvement over STATIC_POST_RUNUP is attributable to confirmation/cooldown structure rather than simply selling less aggressively by construction.",
    "",
    "## Causality",
    "",
    "- Decision amount and state transition use only t-1 month-end information.",
    "- Execution occurs at t month-end close.",
    "- No future price is read.",
    "- No parameter search.",
    "",
    "## Aggregated comparison vs CLOCK",
    "",
    "| Variant | Mean terminal ΔB | Mean raw MaxDD Δ | Mean economic MaxDD Δ | Mean CAGR Δ pp | Mean SELL events | Positive terminal windows |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...(["staticPostRunup", "stateMachine"] as const).map((k) => {
      const row = k === "staticPostRunup" ? report.comparisonVsClock.staticPostRunup : report.comparisonVsClock.stateMachine;
      return "| " + (k === "staticPostRunup" ? "STATIC_POST_RUNUP" : "STATE_MACHINE") + " | " +
        row.terminalDelta.mean.toFixed(6) + " | " +
        row.rawMaxDdDeltaPp.mean.toFixed(3) + " pp | " +
        row.economicMaxDdDeltaPp.mean.toFixed(3) + " pp | " +
        row.cagrDeltaPp.mean.toFixed(3) + " pp | " +
        row.sellEvents.mean.toFixed(2) + " | " +
        row.positiveTerminalVsClock + "/" + windows.length + " |";
    }),
    "",
    "## State-machine incremental effect vs STATIC_POST_RUNUP",
    "",
    "Mean terminal ΔB: " + report.stateMachineVsStaticPostRunup.terminalDelta.mean.toFixed(6),
    "",
    "Mean raw MaxDD Δ: " + report.stateMachineVsStaticPostRunup.rawMaxDdDeltaPp.mean.toFixed(3) + " pp",
    "",
    "Mean economic MaxDD Δ: " + report.stateMachineVsStaticPostRunup.economicMaxDdDeltaPp.mean.toFixed(3) + " pp",
    "",
    "Mean CAGR Δ: " + report.stateMachineVsStaticPostRunup.cagrDeltaPp.mean.toFixed(3) + " pp",
    "",
    "Better terminal windows: " + report.stateMachineVsStaticPostRunup.betterTerminalWindows + "/" + windows.length,
    "",
    "Lower raw MaxDD windows: " + report.stateMachineVsStaticPostRunup.lowerRawDdWindows + "/" + windows.length,
    "",
    "Lower economic MaxDD windows: " + report.stateMachineVsStaticPostRunup.lowerEconomicDdWindows + "/" + windows.length,
    "",
    "Higher CAGR windows: " + report.stateMachineVsStaticPostRunup.higherCagrWindows + "/" + windows.length,
    "",
    "## Promotion gate",
    "",
    "The state machine remains RESEARCH_ONLY. It is not promoted merely because it improves a metric. Promotion requires incremental value versus STATIC_POST_RUNUP plus preservation of economic-wealth accounting and causal invariants.",
    "",
  ].join("\n");
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_sell_state_machine_v1.md"), md);

  const csvHeader = [
    "startDate","endDate",
    "clockTerminalEconomicWealth","staticPostRunupTerminalEconomicWealth","stateMachineTerminalEconomicWealth",
    "staticDeltaTerminal","stateMachineDeltaTerminal","stateMachineVsStaticTerminalDelta",
    "clockRawAccountMaxDd","staticRawAccountMaxDd","stateMachineRawAccountMaxDd",
    "clockEconomicMaxDd","staticEconomicMaxDd","stateMachineEconomicMaxDd",
    "staticCagrDeltaPp","stateMachineCagrDeltaPp","stateMachineVsStaticCagrDeltaPp",
    "staticSellEvents","stateMachineSellEvents","stateMachineStateChanges","stateMachineExtensionEpisodes",
    "staticExternalContribution","stateMachineExternalContribution",
    "staticHarvestToReserve","stateMachineHarvestToReserve"
  ];
  const lines = [csvHeader.join(",")];
  for (const p of windows) {
    lines.push([
      p.startDate,p.endDate,
      p.clock.terminalEconomicWealth,p.staticPostRunup.terminalEconomicWealth,p.stateMachine.terminalEconomicWealth,
      p.staticPostRunup.terminalEconomicWealth-p.clock.terminalEconomicWealth,
      p.stateMachine.terminalEconomicWealth-p.clock.terminalEconomicWealth,
      p.stateMachine.terminalEconomicWealth-p.staticPostRunup.terminalEconomicWealth,
      p.clock.rawAccountMaxDd,p.staticPostRunup.rawAccountMaxDd,p.stateMachine.rawAccountMaxDd,
      p.clock.economicMaxDd,p.staticPostRunup.economicMaxDd,p.stateMachine.economicMaxDd,
      (p.staticPostRunup.terminalEconomicCagr-p.clock.terminalEconomicCagr)*100,
      (p.stateMachine.terminalEconomicCagr-p.clock.terminalEconomicCagr)*100,
      (p.stateMachine.terminalEconomicCagr-p.staticPostRunup.terminalEconomicCagr)*100,
      p.staticPostRunup.harvestEvents,p.stateMachine.harvestEvents,p.stateMachineStateChanges,p.stateMachineExtensionEpisodes,
      p.staticPostRunup.totalExternalContribution,p.stateMachine.totalExternalContribution,
      p.staticPostRunup.totalHarvestToReserve,p.stateMachine.totalHarvestToReserve,
    ].map((x) => JSON.stringify(x)).join(","));
  }
  writeFileSync(resolve(OUT_DIR, "qqq_mutual_chase_sell_state_machine_v1.csv"), lines.join("\n") + "\n");

  console.log(md);
}

run();
