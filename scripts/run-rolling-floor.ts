import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  FLOOR_HORIZON_MONTHS,
  couple,
  monthlyize,
  qqqMonthly,
  quantile,
  recommendForScale,
  replayOne,
  replayFundingPlan,
  summarizeReplays,
  type FundingReplayResult,
  summarizeStatePath,
  TRAP_SCALES_YEARS,
  type ChannelScaleSignal,
  type Channel,
  type MonthlyPoint,
} from "../src/lib/pulse/rolling-floor.ts";

type ChannelId = "QQQ" | "NDX" | "NASDAQCOM";
type Mode = "full" | "shard" | "bridge";

type ShardPayload = {
  version: "rolling-floor.shard.v3";
  kind: "CHANNEL_SHARD";
  channel: ChannelId;
  layer: Channel["layer"];
  targetDates: string[];
  qqq: MonthlyPoint[];
  points: MonthlyPoint[];
  qqqHash: string;
  data: {
    source: string;
    sha256_16: string;
    first: string | null;
    last: string | null;
    months: number;
  };
  signals: ChannelScaleSignal[];
};

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DEFAULT_OUT = join(ROOT, "research", "rolling_10y_floor");
const DEFAULT_INPUT = join(ROOT, "inputs", "rolling_floor_shards");
const END_DATE = qqqMonthly().at(-1)?.date ?? "2026-09-04";

function parseArgs() {
  const argv = process.argv.slice(2);
  const get = (name: string, fallback: string | null = null) => {
    const i = argv.indexOf(name);
    return i >= 0 ? argv[i + 1] ?? fallback : fallback;
  };
  const mode = (get("--mode", "full") ?? "full") as Mode;
  const channel = get("--channel") as ChannelId | null;
  const outDir = resolve(ROOT, get("--out-dir", DEFAULT_OUT) ?? DEFAULT_OUT);
  const inputDir = resolve(ROOT, get("--input-dir", DEFAULT_INPUT) ?? DEFAULT_INPUT);
  if (!["full", "shard", "bridge"].includes(mode)) {
    throw new Error("Unknown mode: " + mode);
  }
  if (mode === "shard" && !channel) throw new Error("--channel is required in shard mode");
  if (channel && !["QQQ", "NDX", "NASDAQCOM"].includes(channel)) {
    throw new Error("Unknown channel: " + channel);
  }
  return { mode, channel, outDir, inputDir };
}

function hashPoints(points: MonthlyPoint[]) {
  return createHash("sha256").update(JSON.stringify(points)).digest("hex").slice(0, 16);
}

function indexAtOrBefore(points: MonthlyPoint[], date: string) {
  let lo = 0;
  let hi = points.length - 1;
  let best = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (points[mid].date <= date) {
      best = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return best;
}

async function fetchFred(id: string, start: string) {
  const url =
    "https://fred.stlouisfed.org/graph/fredgraph.csv?" +
    new URLSearchParams({ id, cosd: start, coed: END_DATE });
  const res = await fetch(url, {
    headers: { "User-Agent": "rolling-10y-floor-research/2.0" },
  });
  if (!res.ok) throw new Error("FRED " + id + " HTTP " + res.status);
  const raw = await res.text();
  const sha256_16 = createHash("sha256").update(raw).digest("hex").slice(0, 16);
  const lines = raw.split(/\r?\n/).filter(Boolean);
  const points: { date: string; value: number }[] = [];
  for (let i = 1; i < lines.length; i++) {
    const comma = lines[i].indexOf(",");
    if (comma < 0) continue;
    const date = lines[i].slice(0, comma).trim();
    const value = Number(lines[i].slice(comma + 1).trim());
    if (/^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(value) && value > 0) {
      points.push({ date, value });
    }
  }
  const monthly = monthlyize(points);
  return { points: monthly, sha256_16, source: url };
}

function channelLayer(channel: ChannelId): Channel["layer"] {
  return channel === "QQQ" ? "OBSERVED" : "PROXY_PRICE";
}

async function makeShard(channel: ChannelId): Promise<ShardPayload> {
  const qqq = qqqMonthly();
  let points: MonthlyPoint[];
  let source = "repo:src/data/universe.json";
  let sha256_16 = hashPoints(qqq);

  if (channel === "QQQ") {
    points = qqq;
  } else if (channel === "NDX") {
    const x = await fetchFred("NASDAQ100", "1986-01-02");
    points = x.points;
    source = x.source;
    sha256_16 = x.sha256_16;
  } else {
    const x = await fetchFred("NASDAQCOM", "1971-02-05");
    points = x.points;
    source = x.source;
    sha256_16 = x.sha256_16;
  }

  const signals: ChannelScaleSignal[] = [];
  for (const asof of qqq) {
    const idx = indexAtOrBefore(points, asof.date);
    if (idx < 0) continue;
    for (const scaleYears of TRAP_SCALES_YEARS) {
      const signal = recommendForScale(points, qqq, idx, scaleYears);
      signal.channel = channel;
      signal.layer = channelLayer(channel);
      signals.push(signal);
    }
  }

  return {
    version: "rolling-floor.shard.v3",
    kind: "CHANNEL_SHARD",
    channel,
    layer: channelLayer(channel),
    targetDates: qqq.map((x) => x.date),
    qqq,
    points,
    qqqHash: hashPoints(qqq),
    data: {
      source,
      sha256_16,
      first: points[0]?.date ?? null,
      last: points.at(-1)?.date ?? null,
      months: points.length,
    },
    signals,
  };
}

function clockReplay(q: MonthlyPoint[], startIndex: number) {
  const h = 120;
  if (startIndex + h >= q.length) return null;
  let cash = 1;
  const lots: { amount: number; entry: number }[] = [];
  const curve: number[] = [1];
  let peak = 1;
  let maxDd = 0;

  for (let j = 0; j < h; j++) {
    const amount = cash / (h - j);
    const px = q[startIndex + j].value;
    lots.push({ amount, entry: px });
    cash -= amount;

    const e =
      cash +
      lots.reduce((s, lot) => s + lot.amount * (px / lot.entry), 0);
    curve.push(e);
    peak = Math.max(peak, e);
    maxDd = Math.min(maxDd, e / peak - 1);
  }

  const finalPx = q[startIndex + h].value;
  const terminal =
    cash +
    lots.reduce((s, lot) => s + lot.amount * (finalPx / lot.entry), 0);
  curve.push(terminal);
  peak = Math.max(peak, terminal);
  maxDd = Math.min(maxDd, terminal / peak - 1);

  return {
    terminalWealth: terminal,
    maxDrawdown: maxDd,
  };
}

function lumpReplay(q: MonthlyPoint[], startIndex: number) {
  const h = 120;
  if (startIndex + h >= q.length) return null;
  const startPx = q[startIndex].value;
  let peak = 1;
  let maxDd = 0;
  for (let j = 0; j <= h; j++) {
    const e = q[startIndex + j].value / startPx;
    peak = Math.max(peak, e);
    maxDd = Math.min(maxDd, e / peak - 1);
  }
  return {
    terminalWealth: q[startIndex + h].value / startPx,
    maxDrawdown: maxDd,
  };
}

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(path, "utf8")) as T;
}

function groupSignals(shards: ShardPayload[]) {
  const byDate = new Map<string, ChannelScaleSignal[]>();
  for (const shard of shards) {
    for (const signal of shard.signals) {
      const xs = byDate.get(signal.asof) ?? [];
      xs.push(signal);
      byDate.set(signal.asof, xs);
    }
  }
  return byDate;
}

function validateShards(shards: ShardPayload[], qqq: MonthlyPoint[]) {
  const ids = shards.map((x) => x.channel).sort();
  const expected = ["NASDAQCOM", "NDX", "QQQ"];
  if (ids.join(",") !== expected.join(",")) {
    throw new Error(
      "Bridge requires exactly QQQ + NDX + NASDAQCOM; got " + ids.join(","),
    );
  }
  const qqqHash = hashPoints(qqq);
  for (const shard of shards) {
    if (shard.version !== "rolling-floor.shard.v3" || shard.kind !== "CHANNEL_SHARD") {
      throw new Error("Invalid shard: " + shard.channel);
    }
    if (shard.qqqHash !== qqqHash) {
      throw new Error(
        "QQQ snapshot hash mismatch in " +
          shard.channel +
          ": " +
          shard.qqqHash +
          " != " +
          qqqHash,
      );
    }
    if (shard.targetDates.length !== qqq.length) {
      throw new Error("Target date count mismatch in " + shard.channel);
    }
    if (shard.signals.length === 0) {
      throw new Error("Empty signal shard: " + shard.channel);
    }
  }
}

function buildBridgePanel(qqq: MonthlyPoint[], shards: ShardPayload[]) {
  const byDate = groupSignals(shards);
  const panel = new Map<string, ReturnType<typeof couple>>();
  for (const p of qqq) {
    panel.set(p.date, couple(p.date, 0, byDate.get(p.date) ?? []));
  }
  return { panel, byDate };
}

function runReplay(
  qqq: MonthlyPoint[],
  panel: Map<string, ReturnType<typeof couple>>,
) {
  const replays = [];
  const adaptiveCredit = [];
  const clock = [];
  const lump = [];
  const adaptiveFunding = [];
  const clockFunding = [];

  for (let start = 0; start + 120 < qqq.length; start++) {
    const coupled = replayOne(qqq, panel, start, "COUPLED");
    const credit = replayOne(qqq, panel, start, "ADAPTIVE_CREDIT_ONLY");
    const adaptiveFund = replayFundingPlan(
      qqq,
      panel,
      start,
      120,
      "ADAPTIVE_FUNDED",
    );
    const clockFund = replayFundingPlan(
      qqq,
      panel,
      start,
      120,
      "CLOCK_FUNDED",
    );
    if (!coupled || !credit || !adaptiveFund || !clockFund) continue;
    replays.push(coupled);
    adaptiveCredit.push(credit);
    adaptiveFunding.push(adaptiveFund);
    clockFunding.push(clockFund);
    clock.push(clockReplay(qqq, start));
    lump.push(lumpReplay(qqq, start));
  }

  return {
    replays,
    adaptiveCredit,
    adaptiveFunding,
    clockFunding,
    clock: clock.filter(Boolean),
    lump: lump.filter(Boolean),
  };
}

function summarizeFunding(results: FundingReplayResult[]) {
  const terminals = results.map((r) => r.terminalWealth);
  const contributions = results.map((r) => r.totalContributed);
  const principals = [...new Set(results.map((r) => r.plannedPrincipal))];
  if (principals.length > 1) {
    throw new Error("Funding comparison mixes different planned principal B values");
  }
  const plannedPrincipal = principals[0] ?? 1;
  const contributedRatios = contributions.map((x) => x / plannedPrincipal);
  const terminalRatios = terminals.map((x) => x / plannedPrincipal);
  return {
    nReplays: results.length,
    plannedPrincipal,
    principalFailureRate:
      terminalRatios.filter((x) => x < 1).length / Math.max(1, terminalRatios.length),
    q05Terminal: quantile(terminalRatios, 0.05) ?? 0,
    medianTerminal: quantile(terminalRatios, 0.50) ?? 0,
    worstTerminal: terminalRatios.length ? Math.min(...terminalRatios) : 0,
    meanTotalContributedRatio: mean(contributedRatios),
    medianTotalContributedRatio: quantile(contributedRatios, 0.50) ?? 0,
    q05TotalContributedRatio: quantile(contributedRatios, 0.05) ?? 0,
    meanContributionReduction: 1 - mean(contributedRatios),
  };
}

function mean(xs: number[]) {
  return xs.reduce((sum, x) => sum + x, 0) / Math.max(1, xs.length);
}

function checkpointMetrics(
  result: FundingReplayResult,
  months: 36 | 60 | 120,
) {
  const row = result.path[months - 1];
  if (!row) return null;
  const navToContributed =
    row.cumulativeContributed > 1e-12
      ? row.nav / row.cumulativeContributed
      : null;
  return {
    contributedRatio: row.cumulativeContributed,
    navToContributed,
    navToB: row.nav,
  };
}

function summarizeFundingCheckpointDifference(
  adaptive: FundingReplayResult[],
  clock: FundingReplayResult[],
  months: 36 | 60 | 120,
) {
  const n = Math.min(adaptive.length, clock.length);
  const deltaContributed: number[] = [];
  const deltaNavToContributed: number[] = [];
  const deltaNavToB: number[] = [];

  for (let i = 0; i < n; i++) {
    const a = adaptive[i];
    const c = clock[i];
    if (!a || !c || a.startDate !== c.startDate || a.endDate !== c.endDate) {
      throw new Error(
        "Checkpoint comparison requires identical rolling starts at index " + i,
      );
    }
    const am = checkpointMetrics(a, months);
    const cm = checkpointMetrics(c, months);
    if (!am || !cm || am.navToContributed == null || cm.navToContributed == null) {
      continue;
    }
    // All deltas are CLOCK - ADAPTIVE on the exact same rolling start.
    deltaContributed.push(cm.contributedRatio - am.contributedRatio);
    deltaNavToContributed.push(cm.navToContributed - am.navToContributed);
    deltaNavToB.push(cm.navToB - am.navToB);
  }

  return {
    months,
    label: months === 36 ? "3Y" : months === 60 ? "5Y" : "10Y",
    pairedObservations: deltaContributed.length,
    dependence: "OVERLAPPING_ROLLING_PATHS; DIAGNOSTIC",
    clockMinusAdaptive: {
      contributedRatio: mean(deltaContributed),
      navToContributed: mean(deltaNavToContributed),
      navToB: mean(deltaNavToB),
    },
  };
}

function baselineSummary(
  rows: Array<{ terminalWealth: number; maxDrawdown: number }>,
) {
  const ws = rows.map((r) => r.terminalWealth);
  const q05 = quantile(ws, 0.05) ?? 0;
  const a = [...ws].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return {
    n: rows.length,
    nonLossRate:
      ws.filter((x) => x >= 1).length / Math.max(1, ws.length),
    medianTerminal:
      a.length === 0 ? 0 : a.length % 2 ? a[m] : ((a[m - 1] ?? 0) + a[m]) / 2,
    q05Terminal: q05,
    principalFailureRate: 1 - ws.filter((x) => x >= 1).length / Math.max(1, ws.length),
    worstTerminal: a.length ? a[0] : 0,
    meanMaxDd:
      rows.reduce((s, x) => s + x.maxDrawdown, 0) /
      Math.max(1, rows.length),
    worstMaxDd: rows.length ? Math.min(...rows.map((x) => x.maxDrawdown)) : 0,
  };
}

function writeOutputs(
  outDir: string,
  qqq: MonthlyPoint[],
  shards: ShardPayload[],
  replay: ReturnType<typeof runReplay>,
) {
  mkdirSync(outDir, { recursive: true });
  const latestDate = qqq.at(-1)?.date ?? END_DATE;
  const { panel, byDate } = buildBridgePanel(qqq, shards);
  const current =
    panel.get(latestDate) ??
    couple(latestDate, 0, byDate.get(latestDate) ?? []);

  const payload = {
    version: "rolling-floor.v4-adaptive-funding",
    evidenceClass: "RESEARCH_ONLY",
    topology: {
      workers: [
        {
          lane: "windows",
          channel: "QQQ",
          runner: 'windows-latest',
          role: "AUDIT_ONLY",
        },
        {
          lane: "linux",
          channel: "NDX",
          runner: '["ubuntu-latest"]',
        },
        {
          lane: "hub-web",
          channel: "NASDAQCOM",
          runner: '["ubuntu-latest"]',
        },
      ],
      bridge: "ubuntu-latest",
      windowsAudit: "NONBLOCKING",
    },
    target: {
      asset: "QQQ",
      horizonYears: 10,
      decisionCadence: "monthly",
      dataAsOf: latestDate,
    },
    trap: {
      scalesYears: [...TRAP_SCALES_YEARS],
      rule:
        "10Y is terminal horizon; 20/30/50Y are parallel historical context scales. An analog is admitted only after its following QQQ 10Y path is fully mature.",
      signalObjective:
        "For each scale, target is the nearest-rank 95% fraction of front-loaded capital required for the analog paths to reach terminal principal under the fixed 10Y deployment ladder. This is a floor requirement, not a terminal-return maximizer.",
      divergence:
        "Scale disagreement is a first-class state; CONVERGENT permits forward pull, TENSION halves it, DIVERGENT/THIN return authority to the deadline clock.",
    },
    data: shards.map((s) => ({
      channel: s.channel,
      layer: s.layer,
      first: s.data.first,
      last: s.data.last,
      months: s.data.months,
      sha256_16: s.data.sha256_16,
      source: s.data.source,
    })),
    current: {
      asOf: latestDate,
      clockFirstMonthTarget: 1 / 120,
      robustTargetAtPhaseZero: current.robustTarget,
      agreementAtPhaseZero: current.agreement,
      divergenceStateAtPhaseZero: current.divergenceState,
      coupledTargetAtPhaseZero: current.coupledTarget,
      firstInjectionFraction: Math.max(1 / 120, current.coupledTarget),
      signalCount: current.signals.length,
      perScale: current.perScale,
      mutualChase: current.mutualChase,
    },
    replay: {
      n: replay.replays.length,
      coupled: summarizeReplays(replay.replays),
      adaptiveCreditOnly: summarizeReplays(replay.adaptiveCredit),
      adaptiveFunding: summarizeFunding(replay.adaptiveFunding),
      clockFunding: summarizeFunding(replay.clockFunding),
      clockOnly: baselineSummary(replay.clock),
      lumpNow: baselineSummary(replay.lump),
    },
    evaluation: {
      rolling10Y: {
        observations: replay.replays.length,
        dependence: "OVERLAPPING_ROLLING_WINDOWS; DIAGNOSTIC_ONLY",
      },
      checkpointDiffs: [
        summarizeFundingCheckpointDifference(replay.adaptiveFunding, replay.clockFunding, 36),
        summarizeFundingCheckpointDifference(replay.adaptiveFunding, replay.clockFunding, 60),
        summarizeFundingCheckpointDifference(replay.adaptiveFunding, replay.clockFunding, 120),
      ],
      rule: "3Y/5Y are interim checkpoints inside the fixed 10Y objective; 10Y remains the terminal floor test. Each row is a paired CLOCK - ADAPTIVE comparison from the same rolling start. Rolling starts overlap, so paired observations are diagnostic, not independent samples.",
    },
    statePath: summarizeStatePath(replay.replays),
    mutualChasePath: summarizeStatePath(replay.replays, "mutualChaseState"),
    provenance: {
      runner: "scripts/run-rolling-floor.ts",
      mode: "BRIDGE",
      qqqHash: hashPoints(qqq),
      sourceCommit: process.env.GITHUB_SHA ?? "LOCAL",
      externalRerun: "Use the portable bundle. No npm install and no network are required for bridge replay.",
    },
  };

  writeFileSync(
    join(outDir, "rolling_floor_result.json"),
    JSON.stringify(payload, null, 2),
  );
  writeFileSync(
    join(outDir, "rolling_floor_replays.jsonl"),
    replay.replays.map((r) => JSON.stringify(r)).join("\n") + "\n",
  );
  writeFileSync(
    join(outDir, "rolling_floor_adaptive_credit_replays.jsonl"),
    replay.adaptiveCredit.map((r) => JSON.stringify(r)).join("\n") + "\n",
  );
  writeFileSync(
    join(outDir, "rolling_floor_adaptive_funding_replays.jsonl"),
    replay.adaptiveFunding.map((r) => JSON.stringify(r)).join("\n") + "\n",
  );
  writeFileSync(
    join(outDir, "rolling_floor_state_path.json"),
    JSON.stringify(summarizeStatePath(replay.replays), null, 2),
  );

  const report = [
    "# Rolling 10Y Capital-Floor Research — Adaptive Funding Plan",
    "",
    "Data end: " + latestDate,
    "",
    "## Execution topology",
    "",
    "- One workflow launches three parallel machine workers.",
    "- Windows (windows-latest) computes a non-blocking QQQ audit shard; Bridge uses the repo QQQ snapshot as canonical target input.",
    "- Linux hosted computes NASDAQ-100 proxy state signals.",
    "- HUB-Web (ubuntu-latest) computes NASDAQ Composite proxy state signals.",
    "- A separate Bridge collector on ubuntu-latest joins the required immutable NDX/NASDAQCOM shards with the canonical QQQ snapshot, applies the coupling state machine, and performs the QQQ replay.",
    "",
    "## Offline rerun",
    "",
    "- The portable bundle contains the exact runner source, QQQ source snapshot, required proxy shards, and the prior output.",
    "- RUN.cmd / RUN.sh invoke Node 22 directly; npm and FRED network access are not required for bridge replay.",
    "",
    "## State-conditioned capital path",
    "",
    "The state analysis is descriptive: it compares cumulative deployed capital with the hard clock target without changing any controller rule.",
    "",
    ...payload.statePath.map((s) =>
      [
        "- " + s.state +
          ": observations=" + s.observations +
          ", share=" + (s.shareOfObservedMonths * 100).toFixed(1) + "%" +
          ", mean ahead-of-clock=" + (s.meanAheadOfClock * 100).toFixed(2) + "%" +
          ", q05/q95 ahead=" + (s.q05AheadOfClock * 100).toFixed(2) +
          "%/" + (s.q95AheadOfClock * 100).toFixed(2) + "%" +
          ", episodes=" + s.episodes +
          ", mean episode=" + s.meanEpisodeMonths.toFixed(1) + "m" +
          ", max episode=" + s.maxEpisodeMonths + "m",
      ].join("")
    ),
    "",
    "Interpretation: CONVERGENT records where scale consensus is permitted to pull capital ahead of the deadline; TENSION records partial authority; DIVERGENT removes historical pull and returns to the clock; THIN means insufficient scale evidence.",
    "",
    "## Mutual-chase topology",
    "",
    ...payload.mutualChasePath.map((s) =>
      [
        "- " + s.state +
          ": observations=" + s.observations +
          ", share=" + (s.shareOfObservedMonths * 100).toFixed(1) + "%" +
          ", mean ahead-of-clock=" + (s.meanAheadOfClock * 100).toFixed(2) + "%" +
          ", episodes=" + s.episodes +
          ", mean episode=" + s.meanEpisodeMonths.toFixed(1) + "m",
      ].join("")
    ),
    "",
    "Mutual-chase state is diagnostic only; it does not alter the replay action.",
    "",
    "## Replay",
    "",
    "Signal objective: 95% terminal-principal floor front-load requirement, not maximum terminal wealth.",
    "",
    "The adaptive-credit replay is a historical-credit diagnostic. The new adaptive-funded replay is the actual funding-plan experiment: external principal starts outside the account and enters dynamically over 10 years.",
    "",
    "Coupled replays: " + replay.replays.length,
    "Coupled non-loss rate: " +
      (payload.replay.coupled.nonLossRate * 100).toFixed(1) +
      "%",
    "Coupled 5% terminal quantile: " +
      payload.replay.coupled.q05Terminal.toFixed(4),
    "Coupled worst terminal: " +
      payload.replay.coupled.worstTerminal.toFixed(4),
    "Coupled worst MaxDD: " +
      (payload.replay.coupled.worstMaxDd * 100).toFixed(1) +
      "%",
    "",
    "Adaptive-credit-only principal failure rate: " +
      ((1 - payload.replay.adaptiveCreditOnly.nonLossRate) * 100).toFixed(1) +
      "%",
    "Adaptive-credit-only 5% terminal quantile: " +
      payload.replay.adaptiveCreditOnly.q05Terminal.toFixed(4),
    "Adaptive-credit mean total deployed: " +
      (payload.replay.adaptiveCreditOnly.meanTotalInvested * 100).toFixed(2) +
      "%",
    "Adaptive-credit mean undeployed at end: " +
      (payload.replay.adaptiveCreditOnly.meanUndeployedAtEnd * 100).toFixed(2) +
      "%",
    "Clock-only principal failure rate: " +
      ((1 - payload.replay.clockOnly.nonLossRate) * 100).toFixed(1) +
      "%",
    "Clock-only 5% terminal quantile: " +
      payload.replay.clockOnly.q05Terminal.toFixed(4),
    "Lump-now principal failure rate: " +
      ((1 - payload.replay.lumpNow.nonLossRate) * 100).toFixed(1) +
      "%",
    "Lump-now 5% terminal quantile: " +
      payload.replay.lumpNow.q05Terminal.toFixed(4),
    "",
    "## External funding plan",
    "",
    "This layer starts with zero account cash. Planned principal B=1 remains outside the account and is contributed month-by-month. Contributions are invested when funded; adaptive funding reduces only future external contributions using reversible NAV surplus credit.",
    "",
    "Adaptive-funded principal failure rate: " +
      (payload.replay.adaptiveFunding.principalFailureRate * 100).toFixed(1) + "%",
    "Adaptive-funded 5% terminal quantile: " +
      payload.replay.adaptiveFunding.q05Terminal.toFixed(4),
    "Adaptive-funded mean total contributed / B: " +
      (payload.replay.adaptiveFunding.meanTotalContributedRatio * 100).toFixed(2) + "%",
    "Adaptive-funded mean contribution reduction: " +
      (payload.replay.adaptiveFunding.meanContributionReduction * 100).toFixed(2) + "%",
    "Clock-funded principal failure rate: " +
      (payload.replay.clockFunding.principalFailureRate * 100).toFixed(1) + "%",
    "Clock-funded 5% terminal quantile / B: " +
      payload.replay.clockFunding.q05Terminal.toFixed(4),
    "",
    "## Paired checkpoint differential (CLOCK - ADAPTIVE)",
    "",
    "| Checkpoint | Delta contributed / B | Delta NAV / contributed | Delta NAV / B |",
    "|---|---:|---:|---:|",
    ...payload.evaluation.checkpointDiffs.map((x) =>
      "| " + x.label +
      " | " + (x.clockMinusAdaptive.contributedRatio * 100).toFixed(2) + "%" +
      " | " + x.clockMinusAdaptive.navToContributed.toFixed(4) +
      " | " + x.clockMinusAdaptive.navToB.toFixed(4) +
      " |"
    ),
    "",
    "Positive numbers mean CLOCK is higher than ADAPTIVE for that same rolling start. NAV / contributed is measured against capital already externally contributed at the checkpoint; NAV / B uses the full planned principal B=1 as denominator.",
    "",
    "## Current",
    "",
    "Robust target at phase 0: " +
      (current.robustTarget == null
        ? "MISSING"
        : (current.robustTarget * 100).toFixed(1) + "%"),
    "Cross-scale state authority: " +
      (current.agreement * 100).toFixed(1) +
      "%",
    "Divergence state: " + current.divergenceState,
    "Coupled phase-0 target: " +
      (current.coupledTarget * 100).toFixed(2) +
      "%",
    "",
    "## Limitation",
    "",
    "QQQ is the observed outcome target. NDX and NASDAQ Composite are price-index proxy channels used only for state analog selection. Rolling starts overlap heavily, so replay count is not an independent-sample count.",
    "",
  ].join("\n");

  writeFileSync(join(outDir, "rolling_floor_report.md"), report);
}

async function main() {
  const { mode, channel, outDir, inputDir } = parseArgs();

  if (mode === "shard") {
    const shard = await makeShard(channel as ChannelId);
    mkdirSync(outDir, { recursive: true });
    writeFileSync(
      join(outDir, shard.channel + ".json"),
      JSON.stringify(shard, null, 2),
    );
    console.log(
      "SHARD PASS " +
        shard.channel +
        ": signals=" +
        shard.signals.length +
        ", points=" +
        shard.points.length,
    );
    return;
  }

  let shards: ShardPayload[];
  if (mode === "bridge") {
    const canonicalQqq = await makeShard("QQQ");
    const proxyShards = (["NDX", "NASDAQCOM"] as ChannelId[]).map((id) =>
      readJson<ShardPayload>(join(inputDir, id + ".json")),
    );
    shards = [canonicalQqq, ...proxyShards];
  } else {
    shards = await Promise.all(
      (["QQQ", "NDX", "NASDAQCOM"] as ChannelId[]).map(makeShard),
    );
  }

  const qqq = qqqMonthly();
  validateShards(shards, qqq);
  const replay = runReplay(qqq, buildBridgePanel(qqq, shards).panel);
  writeOutputs(outDir, qqq, shards, replay);
  console.log(readFileSync(join(outDir, "rolling_floor_report.md"), "utf8"));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
