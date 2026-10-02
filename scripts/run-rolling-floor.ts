import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  buildSignalPanel,
  qqqMonthly,
  replayOne,
  summarizeReplays,
  monthlyize,
  type Channel,
  type MonthlyPoint,
} from "../src/lib/pulse/rolling-floor.ts";

const ROOT = process.cwd();
const RESEARCH = join(ROOT, "research", "rolling_10y_floor");
const END_DATE = qqqMonthly().at(-1)?.date ?? "2026-09-04";

async function fetchFred(id: string, start: string) {
  const url =
    "https://fred.stlouisfed.org/graph/fredgraph.csv?" +
    new URLSearchParams({ id, cosd: start, coed: END_DATE });
  const res = await fetch(url, {
    headers: { "User-Agent": "rolling-10y-floor-research/1.0" },
  });
  if (!res.ok) throw new Error(`FRED ${id} HTTP ${res.status}`);
  const text = await res.text();
  const hash = createHash("sha256").update(text).digest("hex").slice(0, 16);
  const lines = text.split(/\\r?\\n/).filter(Boolean);
  const points = [];
  for (let i = 1; i < lines.length; i++) {
    const comma = lines[i].indexOf(",");
    if (comma < 0) continue;
    const date = lines[i].slice(0, comma).trim();
    const raw = lines[i].slice(comma + 1).trim();
    const value = Number(raw);
    if (/^\\d{4}-\\d{2}-\\d{2}$/.test(date) && Number.isFinite(value) && value > 0) {
      points.push({ date, value });
    }
  }
  return { points: monthlyize(points), hash, url };
}

function clockReplay(q: MonthlyPoint[], startIndex: number) {
  const h = 120;
  if (startIndex + h >= q.length) return null;
  let cash = 1;
  const lots: { amount: number; entry: number }[] = [];
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
    peak = Math.max(peak, e);
    maxDd = Math.min(maxDd, e / peak - 1);
  }
  const endPx = q[startIndex + h].value;
  const end =
    cash + lots.reduce((s, lot) => s + lot.amount * (endPx / lot.entry), 0);
  return { terminalWealth: end, maxDrawdown: maxDd };
}

function lumpReplay(q: MonthlyPoint[], startIndex: number) {
  const h = 120;
  if (startIndex + h >= q.length) return null;
  const startPx = q[startIndex].value;
  const endPx = q[startIndex + h].value;
  let peak = 1;
  let maxDd = 0;
  for (let j = 0; j <= h; j++) {
    const e = q[startIndex + j].value / startPx;
    peak = Math.max(peak, e);
    maxDd = Math.min(maxDd, e / peak - 1);
  }
  return { terminalWealth: endPx / startPx, maxDrawdown: maxDd };
}

async function main() {
  mkdirSync(RESEARCH, { recursive: true });
  const qqq = qqqMonthly();
  const ndx = await fetchFred("NASDAQ100", "1986-01-02");
  const comp = await fetchFred("NASDAQCOM", "1971-02-05");

  const channels: Channel[] = [
    { id: "QQQ", layer: "OBSERVED", points: qqq },
    { id: "NDX", layer: "PROXY_PRICE", points: ndx.points },
    { id: "NASDAQCOM", layer: "PROXY_PRICE", points: comp.points },
  ];

  const panel = buildSignalPanel(channels, qqq.map((x) => x.date));
  const replays = [];
  const clock = [];
  const lump = [];

  for (let start = 0; start + 120 < qqq.length; start++) {
    const r = replayOne(qqq, panel, start);
    if (r) {
      replays.push(r);
      clock.push(clockReplay(qqq, start));
      lump.push(lumpReplay(qqq, start));
    }
  }

  const cleanClock = clock.filter(Boolean);
  const cleanLump = lump.filter(Boolean);
  const avg = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length);
  const nonLoss = (xs: number[]) => xs.filter((x) => x >= 1).length / Math.max(1, xs.length);

  const latestDate = qqq.at(-1)?.date ?? END_DATE;
  const latest = panel.get(latestDate);
  const currentSignals = latest?.signals ?? [];

  const payload = {
    version: "rolling-floor.v1",
    evidenceClass: "RESEARCH_ONLY",
    target: {
      asset: "QQQ",
      horizonYears: 10,
      decisionCadence: "monthly",
      dataAsOf: latestDate,
    },
    trap: {
      scalesYears: [20, 30, 50],
      rule: "Each scale sees only past analog anchors whose full 10Y path was already known at the as-of date. No future anchor is eligible.",
      balance: "Robust median across available channels/scales; MAD disagreement reduces signal authority and returns control to the clock.",
    },
    data: {
      QQQ: { layer: "OBSERVED", first: qqq[0]?.date, last: qqq.at(-1)?.date, months: qqq.length },
      NASDAQ100: { layer: "PROXY_PRICE", first: ndx.points[0]?.date, last: ndx.points.at(-1)?.date, months: ndx.points.length, sha256_16: ndx.hash, source: ndx.url },
      NASDAQCOM: { layer: "PROXY_PRICE", first: comp.points[0]?.date, last: comp.points.at(-1)?.date, months: comp.points.length, sha256_16: comp.hash, source: comp.url },
    },
    current: {
      asOf: latestDate,
      clockFirstMonthTarget: 1 / 120,
      robustTargetAtPhaseZero: latest?.robustTarget ?? null,
      agreementAtPhaseZero: latest?.agreement ?? 0,
      divergenceStateAtPhaseZero: latest?.divergenceState ?? "THIN",
      firstInjectionFraction: latest?.robustTarget == null
        ? 1 / 120
        : Math.max(1 / 120, (latest.robustTarget ?? 0) * (latest.agreement ?? 0)),
      signals: currentSignals,
      perScale: latest?.perScale ?? [],
    },
    replay: {
      n: replays.length,
      coupled: summarizeReplays(replays),
      clockOnly: {
        n: cleanClock.length,
        nonLossRate: nonLoss(cleanClock.map((x) => x!.terminalWealth)),
        meanTerminal: avg(cleanClock.map((x) => x!.terminalWealth)),
        worstTerminal: Math.min(...cleanClock.map((x) => x!.terminalWealth)),
      },
      lumpNow: {
        n: cleanLump.length,
        nonLossRate: nonLoss(cleanLump.map((x) => x!.terminalWealth)),
        meanTerminal: avg(cleanLump.map((x) => x!.terminalWealth)),
        worstTerminal: Math.min(...cleanLump.map((x) => x!.terminalWealth)),
      },
    },
    starts: replays.map((r) => ({
      startDate: r.startDate,
      endDate: r.endDate,
      terminalWealth: r.terminalWealth,
      maxDrawdown: r.maxDrawdown,
      deployedAtHalfway: r.deployedAtHalfway,
      deployedAtYear8: r.deployedAtYear8,
      forcedCatchUpMonths: r.forcedCatchUpMonths,
      divergenceStateByDate: r.trades.map((t) => ({ date: t.date, state: t.divergenceState })),
    })),
  };

  writeFileSync(join(RESEARCH, "rolling_floor_result.json"), JSON.stringify(payload, null, 2));
  writeFileSync(
    join(RESEARCH, "rolling_floor_replays.jsonl"),
    replays.map((r) => JSON.stringify(r)).join("\n") + "\n",
  );

  const report = [
    "# Rolling 10Y Capital-Floor Controller",
    "",
    `Data end: **${latestDate}**`,
    "",
    "## Architecture",
    "",
    "- 10Y = fixed terminal horizon.",
    "- 20/30/50Y = parallel historical-context trap scales; 10Y is only the terminal target horizon.",
    "- Analog futures are admitted only after their own 10Y future has matured.",
    "- Scale disagreement is preserved; it reduces signal authority instead of being averaged away.",
    "- Clock is the hard backstop: remaining cash is forced into equal catch-up slices as the deadline approaches.",
    "- QQQ outcome is the observed target path. NDX and NASDAQ Composite are price-only context proxies.",
    "",
    "## Replay",
    "",
    `Coupled replays: **${payload.replay.n}**`,
    `Coupled non-loss rate: **${(payload.replay.coupled.nonLossRate * 100).toFixed(1)}%**`,
    `Coupled 5% terminal quantile: **${payload.replay.coupled.q05Terminal.toFixed(4)}**`,
    `Coupled worst terminal: **${payload.replay.coupled.worstTerminal.toFixed(4)}**`,
    `Coupled worst MaxDD: **${(payload.replay.coupled.worstMaxDd * 100).toFixed(1)}%**`,
    "",
    `Clock-only non-loss: **${(payload.replay.clockOnly.nonLossRate * 100).toFixed(1)}%**`,
    `Lump-now non-loss: **${(payload.replay.lumpNow.nonLossRate * 100).toFixed(1)}%**`,
    "",
    "## Current (repo data as-of)",
    "",
    `Robust signal target at phase 0: **${payload.current.robustTargetAtPhaseZero == null ? "MISSING" : (payload.current.robustTargetAtPhaseZero * 100).toFixed(1) + "%"}**`,
    `Cross-scale agreement: **${(payload.current.agreementAtPhaseZero * 100).toFixed(1)}%**`,
    `Divergence state: **${payload.current.divergenceStateAtPhaseZero}**`,
    `First-month minimum by clock: **${(100 / 120).toFixed(3)}%**`,
    `First injection from coupled rule: **${(payload.current.firstInjectionFraction * 100).toFixed(2)}%**`,
    "",
    "## Important limitation",
    "",
    "This is a research controller, not a guarantee. NDX/NASDAQ Composite proxy channels are price-index histories, while the scored target is the observed QQQ path. The current repo's QQQ data begins in 2004, so the number of independent 10Y start regimes is limited.",
    "",
  ].join("\n");

  writeFileSync(join(RESEARCH, "rolling_floor_report.md"), report);
  console.log(report);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
