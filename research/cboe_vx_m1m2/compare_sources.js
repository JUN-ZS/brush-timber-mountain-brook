#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

function arg(name, fallback=null) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}
function csv(text) {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  if (!lines.length || !lines[0]) return [];
  const head = lines.shift().split(",");
  return lines.filter(Boolean).map(line => {
    const cells = line.split(",");
    return Object.fromEntries(head.map((h,i)=>[h, cells[i] ?? ""]));
  });
}
function num(x) {
  const v = Number(x);
  return Number.isFinite(v) ? v : null;
}
function key(x) { return String(x ?? "").slice(0,10); }
function pct(x) { return Number.isFinite(x) ? (x*100).toFixed(3)+"%" : "NA"; }
function read(p) { return fs.readFileSync(p,"utf8"); }
function loadEngine(p) {
  globalThis.window = {};
  vm.runInThisContext(read(p), {filename:p});
  return globalThis.window.M1M2Lab;
}
function writeJson(p, x) {
  fs.mkdirSync(path.dirname(p), {recursive:true});
  fs.writeFileSync(p, JSON.stringify(x,null,2)+"\n","utf8");
}
function esc(v) {
  const s = v == null ? "" : String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g,'""') + '"' : s;
}

const realPath = arg("--real");
const externalPath = arg("--external");
const spotsPath = arg("--spots");
const enginePath = arg("--engine", "research/m1_m2_reconstruction_lab/engine.js");
const outDir = arg("--out-dir", "artifacts/real-vx/source-swap");
if (!realPath || !externalPath || !spotsPath) throw new Error("Missing --real/--external/--spots");

const E = loadEngine(enginePath);
const real = csv(read(realPath)).map(r=>({
  date:key(r.trade_date),
  m1:num(r.m1_settlement),
  m2:num(r.m2_settlement),
  s:num(r.term_slope)
})).filter(r=>r.date && Number.isFinite(r.m1) && Number.isFinite(r.m2));

const external = csv(read(externalPath)).map(r=>({
  date:key(r.Date),
  vix:num(r.VIX),
  m1:num(r.M1),
  m2:num(r.M2)
})).filter(r=>r.date && Number.isFinite(r.m1) && Number.isFinite(r.m2));

const spots = new Map();
for (const r of csv(read(spotsPath))) {
  spots.set(key(r.Date), {
    date:key(r.Date), qqq:num(r.QQQ), vxx:num(r.VXX), vix:num(r.VIX), prevDate:key(r.PrevDate)
  });
}

const byReal = new Map(real.map(r=>[r.date,r]));
const byExt = new Map(external.map(r=>[r.date,r]));
const dates = [...byReal.keys()].filter(d=>byExt.has(d)).sort();

const rows = [];
let termSign=0, archiveState=0, archiveAction=0, carry=0;
for (const date of dates) {
  const a = byExt.get(date);
  const b = byReal.get(date);
  const spot = spots.get(date);
  if (!spot || !Number.isFinite(spot.vix)) continue;
  const prev = spot.prevDate ? spots.get(spot.prevDate) : null;
  const rQ = prev && Number.isFinite(spot.qqq) && Number.isFinite(prev.qqq) && prev.qqq !== 0 ? spot.qqq / prev.qqq - 1 : null;
  const rV = prev && Number.isFinite(spot.vxx) && Number.isFinite(prev.vxx) && prev.vxx !== 0 ? spot.vxx / prev.vxx - 1 : null;
  const sOld = E.term(a.m1,a.m2);
  const sReal = E.term(b.m1,b.m2);
  const oldState = E.archiveState(spot.vix,rQ,rV,sOld);
  const realState = E.archiveState(spot.vix,rQ,rV,sReal);
  const oldAction = E.archiveAction(spot.vix,rQ,rV,sOld);
  const realAction = E.archiveAction(spot.vix,rQ,rV,sReal);
  const oldCarry = E.archiveCarry(spot.vix,rQ,rV,sOld);
  const realCarry = E.archiveCarry(spot.vix,rQ,rV,sReal);
  const signMatch = (sOld > 0) === (sReal > 0);
  const stateMatch = oldState === realState;
  const actionMatch = oldAction === realAction;
  const carryMatch = oldCarry === realCarry;
  if (signMatch) termSign++;
  if (stateMatch) archiveState++;
  if (actionMatch) archiveAction++;
  if (carryMatch) carry++;
  rows.push({
    date, vix:spot.vix,
    old:{m1:a.m1,m2:a.m2,s:sOld,state:oldState,action:oldAction,carry:oldCarry},
    real:{m1:b.m1,m2:b.m2,s:sReal,state:realState,action:realAction,carry:realCarry},
    delta:{m1:b.m1-a.m1,m2:b.m2-a.m2,s:sReal-sOld},
    rQ,rV,matches:{termSign:signMatch,state:stateMatch,action:actionMatch,carry:carryMatch}
  });
}

const metrics = {
  overlapRows: rows.length,
  termSignAgreementPct: rows.length ? 100*termSign/rows.length : null,
  archiveStateAgreementPct: rows.length ? 100*archiveState/rows.length : null,
  archiveActionAgreementPct: rows.length ? 100*archiveAction/rows.length : null,
  archiveVxxCarryAgreementPct: rows.length ? 100*carry/rows.length : null,
  actionMismatchRows: rows.filter(r=>!r.matches.action).length,
  stateMismatchRows: rows.filter(r=>!r.matches.state).length,
  termSignMismatchRows: rows.filter(r=>!r.matches.termSign).length,
  carryMismatchRows: rows.filter(r=>!r.matches.carry).length,
  sampleMismatches: rows.filter(r=>!r.matches.action || !r.matches.state || !r.matches.termSign).slice(0,20),
  oldSource:"EXTERNAL_OBSERVED / UNVALIDATED",
  realSource:"CBOE per-expiry VX historical daily settlement"
};

const header = ["date","vix","old_m1","real_m1","delta_m1","old_m2","real_m2","delta_m2","old_s","real_s","delta_s","old_state","real_state","state_match","old_action","real_action","action_match","old_carry","real_carry","carry_match","rQ","rV","term_sign_match"];
const lines=[header.join(",")];
for(const r of rows){
  lines.push([
    r.date,r.vix,r.old.m1,r.real.m1,r.delta.m1,r.old.m2,r.real.m2,r.delta.m2,r.old.s,r.real.s,r.delta.s,
    r.old.state,r.real.state,r.matches.state,r.old.action,r.real.action,r.matches.action,r.old.carry,r.real.carry,r.matches.carry,r.rQ,r.rV,r.matches.termSign
  ].map(esc).join(","));
}
fs.mkdirSync(outDir,{recursive:true});
fs.writeFileSync(path.join(outDir,"source_swap_rows.csv"),lines.join("\n")+"\n","utf8");
writeJson(path.join(outDir,"source_swap_metrics.json"),metrics);

const report = [
  "# VX SOURCE-SWAP PARITY — OLD EXTERNAL vs REAL CBOE",
  "",
  "Status: DIAGNOSTIC / SOURCE-SWAP",
  "",
  "Same spot inputs; only the M1/M2 source changes.",
  "",
  "| Metric | Result |",
  "|---|---:|",
  "| Overlap rows | **"+rows.length+"** |",
  "| Term-sign agreement | **"+pct(metrics.termSignAgreementPct/100)+"** |",
  "| Archive-state agreement | **"+pct(metrics.archiveStateAgreementPct/100)+"** |",
  "| Archive-action agreement | **"+pct(metrics.archiveActionAgreementPct/100)+"** |",
  "| VXX-carry agreement | **"+pct(metrics.archiveVxxCarryAgreementPct/100)+"** |",
  "| Term-sign mismatches | **"+metrics.termSignMismatchRows+"** |",
  "| State mismatches | **"+metrics.stateMismatchRows+"** |",
  "| Action mismatches | **"+metrics.actionMismatchRows+"** |",
  "",
  "Interpretation:",
  "1. Only M1/M2 source is changed.",
  "2. High agreement means this recovered policy is relatively insensitive to the exact M1/M2 point values over the measured overlap.",
  "3. This is not a CAGR proof.",
  "4. No parameter search or threshold tuning is performed.",
  "",
  "Outputs: source_swap_metrics.json, source_swap_rows.csv"
].join("\n");
fs.writeFileSync(path.join(outDir,"SOURCE_SWAP_PARITY.md"),report+"\n","utf8");
console.log(JSON.stringify(metrics,null,2));
