#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const DATA_PATH = path.join(ROOT, "research/data/vx_m1_m2_external_2016_2022.csv");
const SPOT_PATH = path.join(ROOT, "research/data/archive_spots_overlap_2018_2022.csv");
const ENGINE_PATH = path.join(ROOT, "research/m1_m2_reconstruction_lab/engine.js");
const OUT_CSV = path.join(ROOT, "research/data/real_historical_state_replay_2018_2022.csv");
const OUT_MD = path.join(ROOT, "research/m1_m2_reconstruction_lab/REAL_HISTORICAL_STATE_REPLAY.md");

function parseCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  const header = lines.shift().split(",");
  return lines.filter(Boolean).map(line => {
    const cells = line.split(",");
    const row = {};
    header.forEach((h, i) => row[h] = cells[i] ?? "");
    return row;
  });
}
function num(x) {
  const v = Number(x);
  return Number.isFinite(v) ? v : null;
}
function key(x) {
  return String(x ?? "").slice(0, 10);
}
function mean(xs) {
  const a = xs.filter(Number.isFinite);
  return a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
}
function pct(x, digits = 2) {
  return Number.isFinite(x) ? (x * 100).toFixed(digits) + "%" : "NA";
}
function esc(v) {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
function loadEngine() {
  globalThis.window = {};
  vm.runInThisContext(fs.readFileSync(ENGINE_PATH, "utf8"), { filename: ENGINE_PATH });
  return globalThis.window.M1M2Lab;
}

const E = loadEngine();
const termRows = parseCsv(fs.readFileSync(DATA_PATH, "utf8"))
  .map(r => ({ Date:r.Date, VIX:num(r.VIX), M1:num(r.M1), M2:num(r.M2) }))
  .sort((a,b) => a.Date.localeCompare(b.Date));

if (termRows.length !== 1540) throw new Error("Observed M1/M2 dataset row-count contract failed: " + termRows.length);
if (!termRows.every(r => r.Date && Number.isFinite(r.VIX) && Number.isFinite(r.M1) && Number.isFinite(r.M2) && r.M1 > 0 && r.M2 > 0)) {
  throw new Error("Observed M1/M2 dataset contains missing/non-positive VIX/M1/M2");
}
for (let i = 1; i < termRows.length; i++) {
  if (termRows[i-1].Date >= termRows[i].Date) throw new Error("Observed dataset must be strictly ascending after sort");
}

const spots = new Map();
for (const r of parseCsv(fs.readFileSync(SPOT_PATH, "utf8"))) {
  spots.set(key(r.Date), {
    date:key(r.Date), qqq:num(r.QQQ), vxx:num(r.VXX), vix:num(r.VIX), prevDate:key(r.PrevDate)
  });
}

const results = [];
let overlap = 0;
let backwardation = 0;
let contango = 0;
let carryOn = 0;
let carryOff = 0;
let prevOverlapAction = null;
let prevOverlapState = null;
let actionTransitions = 0;
let stateTransitions = 0;

for (let i = 0; i < termRows.length; i++) {
  const r = termRows[i];
  const m1 = num(r.M1);
  const m2 = num(r.M2);
  const ts = E.term(m1, m2);
  const prevTs = i > 0 ? E.term(termRows[i-1].M1, termRows[i-1].M2) : null;
  const prevPrevTs = i > 1 ? E.term(termRows[i-2].M1, termRows[i-2].M2) : null;
  const dTs = Number.isFinite(ts) && Number.isFinite(prevTs) ? ts - prevTs : null;
  const prevDTs = Number.isFinite(prevTs) && Number.isFinite(prevPrevTs) ? prevTs - prevPrevTs : null;
  const d2Ts = Number.isFinite(dTs) && Number.isFinite(prevDTs) ? dTs - prevDTs : null;

  const spot = spots.get(key(r.Date));
  const prevSpot = spot?.prevDate ? spots.get(spot.prevDate) : null;
  const rQ = spot && prevSpot && Number.isFinite(spot.qqq) && Number.isFinite(prevSpot.qqq) && prevSpot.qqq !== 0
    ? spot.qqq / prevSpot.qqq - 1 : null;
  const rV = spot && prevSpot && Number.isFinite(spot.vxx) && Number.isFinite(prevSpot.vxx) && prevSpot.vxx !== 0
    ? spot.vxx / prevSpot.vxx - 1 : null;

  const archiveState = E.archiveState(num(r.VIX), rQ, rV, ts);
  const archiveAction = E.archiveAction(num(r.VIX), rQ, rV, ts);
  const vxxCarry = E.archiveCarry(num(r.VIX), rQ, rV, ts);

  if (spot && prevSpot) overlap++;
  if (Number.isFinite(ts)) {
    if (ts < 0) backwardation++; else contango++;
  }
  if (spot && prevSpot) {
    if (vxxCarry) carryOn++; else carryOff++;
    if (prevOverlapAction !== null && archiveAction !== prevOverlapAction) actionTransitions++;
    if (prevOverlapState !== null && archiveState !== prevOverlapState) stateTransitions++;
    prevOverlapAction = archiveAction;
    prevOverlapState = archiveState;
  }

  results.push({
    date:key(r.Date), vix:num(r.VIX), m1, m2, ts, dTs, d2Ts,
    qqq:spot?.qqq ?? null, vxx:spot?.vxx ?? null, rQ, rV,
    archiveState, archiveAction, vxxCarry,
    source:"OBSERVED_M1_M2 + ARCHIVE_POLICY",
    provenance:"OBSERVED_REPLAY"
  });
}

function countBy(rows, field) {
  const out = {};
  for (const r of rows) out[r[field]] = (out[r[field]] || 0) + 1;
  return out;
}
function episodeStats(rows, predicate) {
  const episodes = [];
  let start = null, end = null, count = 0;
  for (const r of rows) {
    if (predicate(r)) {
      if (start === null) start = r.date;
      end = r.date;
      count++;
    } else if (start !== null) {
      episodes.push({start, end, rows:count});
      start = null; end = null; count = 0;
    }
  }
  if (start !== null) episodes.push({start, end, rows:count});
  return {
    count:episodes.length,
    longest:episodes.reduce((m,e) => Math.max(m,e.rows), 0),
    episodes
  };
}

const stateCounts = countBy(results, "archiveState");
const actionCounts = countBy(results, "archiveAction");
const overlapRows = results.filter(r => Number.isFinite(r.rQ) && Number.isFinite(r.rV));
const overlapActionCounts = countBy(overlapRows, "archiveAction");
const overlapStateCounts = countBy(overlapRows, "archiveState");
const backwardEpisodes = episodeStats(results, r => Number.isFinite(r.ts) && r.ts < 0);
const carryEpisodes = episodeStats(overlapRows, r => r.vxxCarry);
const meanTs = mean(results.map(r => r.ts));
const meanDTs = mean(results.map(r => r.dTs));

const csvHeader = [
  "Date","VIX","M1","M2","TS","dTS","d2TS",
  "QQQ","VXX","rQ","rV","archiveState","archiveAction","vxxCarry",
  "source","provenance"
];
const csv = [csvHeader.join(",")];
for (const r of results) {
  csv.push([
    r.date,r.vix,r.m1,r.m2,r.ts,r.dTs,r.d2Ts,
    r.qqq,r.vxx,r.rQ,r.rV,r.archiveState,r.archiveAction,r.vxxCarry,
    r.source,r.provenance
  ].map(esc).join(","));
}
fs.writeFileSync(OUT_CSV, csv.join("\n") + "\n", "utf8");

function table(counts, total) {
  return Object.entries(counts).map(([k,v]) => "| " + k + " | " + v + " | " + pct(v/total) + " |");
}
function actionTable() {
  const keys = Array.from(new Set([...Object.keys(actionCounts), ...Object.keys(overlapActionCounts)]));
  return keys.map(k => "| " + k + " | " + (actionCounts[k] || 0) + " | " + (overlapActionCounts[k] || 0) + " |");
}
const report = [
  "# REAL HISTORICAL STATE REPLAY",
  "",
  "Status: **OBSERVED_REPLAY** — direct replay using observed external M1/M2. Not reconstruction. Not P&L replay.",
  "",
  "## Data contract",
  "- M1/M2/VIX rows: **" + results.length + "**",
  "- Coverage: **" + results[0].date + " → " + results.at(-1).date + "**",
  "- Archived QQQ/VXX overlap: **" + overlapRows.length + "** rows",
  "- Inputs: observed M1/M2/VIX + aligned archived QQQ/VXX spot series",
  "- Policy: recovered archive state/action functions in engine.js",
  "",
  "## Direct term structure",
  "- Mean TS: **" + pct(meanTs) + "**",
  "- Mean ΔTS: **" + pct(meanDTs) + "**",
  "- Backwardation rows (TS < 0): **" + backwardation + " / " + results.length + " (" + pct(backwardation/results.length) + ")**",
  "- Contango/non-negative rows: **" + contango + " / " + results.length + " (" + pct(contango/results.length) + ")**",
  "- Backwardation episodes: **" + backwardEpisodes.count + "**",
  "- Longest backwardation run: **" + backwardEpisodes.longest + " rows**",
  "",
  "## Archive state replay",
  "",
  "| State | Rows | Share |",
  "|---|---:|---:|",
  ...table(stateCounts, results.length),
  "",
  "## Archive action replay",
  "",
  "| Action | All rows | Overlap rows |",
  "|---|---:|---:|",
  ...actionTable(),
  "",
  "## VXX carry",
  "- Carry ON among QQQ/VXX overlap: **" + carryOn + "**",
  "- Carry OFF among QQQ/VXX overlap: **" + carryOff + "**",
  "- Carry episodes in overlap: **" + carryEpisodes.count + "**",
  "- Longest carry run: **" + carryEpisodes.longest + " rows**",
  "",
  "## Change-of-state signal",
  "- Archive state transitions on overlap: **" + stateTransitions + "**",
  "- Archive action transitions on overlap: **" + actionTransitions + "**",
  "",
  "## Forensic interpretation",
  "1. **Observed M1/M2 is sufficient to replay the term-dependent archive gate directly.** No VIX→M2 proxy is needed for this historical window.",
  "2. The replay gives exact historical dates for the recovered policy's Shock / High-Spread / Decay-Optimal / Normal classifications and the VXX carry gate.",
  "3. This does **not** prove the historical 12.5% CAGR. Full P&L parity still requires the original option contract identities, expiries, entry/exit prices, roll logic, execution and friction contract.",
  "4. The next simulation, if pursued, must be a separate **EMPIRICAL_TS_SIM_V1** and must remain explicitly DERIVED/HYPOTHETICAL.",
  "",
  "Output CSV: research/data/real_historical_state_replay_2018_2022.csv"
].join("\n");
fs.writeFileSync(OUT_MD, report + "\n", "utf8");

console.log(JSON.stringify({
  status:"PASS",
  role:"OBSERVED_REPLAY",
  rows:results.length,
  coverage:[results[0].date, results.at(-1).date],
  overlap:overlapRows.length,
  meanTs,
  backwardationRows:backwardation,
  backwardationEpisodes:backwardEpisodes.count,
  longestBackwardationRun:backwardEpisodes.longest,
  stateCounts,
  actionCounts,
  overlapStateCounts,
  overlapActionCounts,
  carryOn,
  carryOff,
  carryEpisodes:carryEpisodes.count,
  longestCarryRun:carryEpisodes.longest,
  actionTransitions,
  stateTransitions,
  outputs:[
    "research/data/real_historical_state_replay_2018_2022.csv",
    "research/m1_m2_reconstruction_lab/REAL_HISTORICAL_STATE_REPLAY.md"
  ]
}, null, 2));
