// Cell 19 — Data gate: date validity (F1).
// Single responsibility: the engine data gate must FAIL CLOSED when the dates that
// prove data freshness are missing or unparseable. A null / "abc" / "2026/09/01"
// term date, a broken spot date, or no clock must never become FRESH → CARRY → BUY.
// Read-only. No broker. No POLICY change. Expected values are literal.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
globalThis.window = {};
vm.runInThisContext(fs.readFileSync(path.join(here, "..", "engine.js"), "utf8"));
const E = globalThis.window.HybridEngineV3;

const TODAY = "2026-10-08";
// CARRY-shaped values: VIX 16 < 28, S = (17.2-16.2)/16.2 = 6.17% > 5 → would be CARRY/BUY if the gate opened.
const base = { qqq: 750, vxx: 20, vix: 16, m1: 16.2, m2: 17.2, s: E.term(16.2, 17.2), termAsOf: TODAY, spotAsOf: TODAY, today: TODAY, term_source: "CBOE_PUBLIC_DELAYED_VX", provenance: {} };
const position = { nav: 100000, qqqShares: 10, vxxPct: 5, qqqCalls: 1, vxxCalls: 0, inputStatus: { status: "READY", invalid: [], empty: [], fields: {} } };

const results = [];
let pass = true;
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, ...(ok ? {} : { detail }) });
  if (!ok) pass = false;
}

function run(data) {
  const e = E.derive(data);
  const book = E.targetLedger(data, e, position, {});
  const bridge = E.strategyActionBridge({ d: data, e, book, funding: {}, currentOptionLegs: null, journalRows: [] });
  const summary = E.operatorSummary(data, e, book, {}, {});
  return { e, book, bridge, summary };
}

function expectBlocked(name, patch, code) {
  const data = { ...base, ...patch };
  const r = run(data);
  const h = r.e.health || {};
  const sameAsCurrent = ["qqqShares", "vxxPct", "qqqCalls", "vxxCalls"].every(k => r.book.target[k] === position[k]);
  const ok = r.e.state === "DATA BLOCKED" && r.e.action === "HOLD" && r.e.blocked === true &&
    h.status === "BLOCKED" && h.code === code && String(h.label || "").includes(code.replace(/_/g, " ")) &&
    sameAsCurrent && r.bridge.actionClass === "PAUSE" && r.bridge.noBrokerOrder === true && r.summary.mode === "PAUSED";
  check(name, ok, { state: r.e.state, action: r.e.action, gate: r.e.gate, code: h.code, label: h.label, target: r.book.target, bridge: r.bridge.actionClass, mode: r.summary.mode });
}

function expectState(name, patch, state, extra = () => true) {
  const data = { ...base, ...patch };
  const r = run(data);
  const ok = r.e.state === state && extra(r);
  check(name, ok, { state: r.e.state, action: r.e.action, health: r.e.health && { status: r.e.health.status, code: r.e.health.code, ageDays: r.e.health.ageDays }, bridge: r.bridge.actionClass });
}

// A. Term date (term values present, date missing / unparseable) → BLOCKED TERM DATE INVALID.
expectBlocked("A1 termAsOf null → BLOCKED", { termAsOf: null }, "TERM_DATE_INVALID");
expectBlocked("A2 termAsOf undefined → BLOCKED", { termAsOf: undefined }, "TERM_DATE_INVALID");
expectBlocked("A3 termAsOf '' → BLOCKED", { termAsOf: "" }, "TERM_DATE_INVALID");
expectBlocked("A4 termAsOf 'abc' → BLOCKED", { termAsOf: "abc" }, "TERM_DATE_INVALID");
expectBlocked("A5 termAsOf '2026/09/01' → BLOCKED", { termAsOf: "2026/09/01" }, "TERM_DATE_INVALID");
expectBlocked("A6 termAsOf '2026-02-30' (no such day) → BLOCKED", { termAsOf: "2026-02-30" }, "TERM_DATE_INVALID");
expectBlocked("A7 termAsOf '10/07/2026' → BLOCKED", { termAsOf: "10/07/2026" }, "TERM_DATE_INVALID");
// Providers emit YYYY-MM-DD only (Cboe data_asof is converted to a NY date in Python), so a raw datetime is not accepted.
expectBlocked("A8 termAsOf raw datetime → BLOCKED (providers normalise to NY date first)", { termAsOf: "2026-10-07T17:05:19-05:00" }, "TERM_DATE_INVALID");
expectBlocked("A9 termAsOf number → BLOCKED", { termAsOf: 20261008 }, "TERM_DATE_INVALID");

// B. Spot date → BLOCKED SPOT DATE INVALID.
expectBlocked("B1 spotAsOf 'abc' → BLOCKED", { spotAsOf: "abc" }, "SPOT_DATE_INVALID");
expectBlocked("B2 spotAsOf '2026/10/08' → BLOCKED", { spotAsOf: "2026/10/08" }, "SPOT_DATE_INVALID");
expectBlocked("B3 spotAsOf null → BLOCKED", { spotAsOf: null }, "SPOT_DATE_INVALID");
expectBlocked("B4 spotAsOf '2026-13-01' → BLOCKED", { spotAsOf: "2026-13-01" }, "SPOT_DATE_INVALID");

// C. Clock → BLOCKED NO CLOCK (engine never reads the wall clock itself; app.js always passes today).
expectBlocked("C1 today missing → BLOCKED", { today: undefined }, "NO_CLOCK");
expectBlocked("C2 today null → BLOCKED", { today: null }, "NO_CLOCK");
expectBlocked("C3 today 'abc' → BLOCKED", { today: "abc" }, "NO_CLOCK");

// D. Valid dates keep the existing gate semantics (no change to POLICY.maxTermAgeDays 4 / date-mix 2).
expectState("D1 all valid → CARRY / BUY", {}, "CARRY", r => r.e.action === "BUY" && r.e.health.status === "FRESH" && r.e.health.ageDays === 0);
expectState("D2 term 4d old → still CARRY", { termAsOf: "2026-10-04", spotAsOf: "2026-10-04" }, "CARRY", r => r.e.health.ageDays === 4);
expectState("D3 term 5d old → DATA STALE", { termAsOf: "2026-10-03", spotAsOf: "2026-10-03" }, "DATA STALE", r => r.bridge.actionClass === "PAUSE");
expectState("D4 spot/term gap 3d → AS-OF MIXED", { spotAsOf: "2026-10-05" }, "AS-OF MIXED", r => r.bridge.actionClass === "PAUSE");
expectState("D5 padded ' 2026-10-08 ' accepted", { termAsOf: " 2026-10-08 ", spotAsOf: " 2026-10-08 ", today: " 2026-10-08 " }, "CARRY");
// Missing values still use the original BLOCKED path (precedence: values → clock → term date → spot date → STALE → MIXED).
expectState("D6 m1 missing + bad date → DATA BLOCKED (missing-field reason wins)", { m1: null, termAsOf: "abc" }, "DATA BLOCKED", r => r.e.health.code === "MISSING_FIELD");

// E. Supply side: the live page must never be stuck on NO CLOCK.
{
  const app = fs.readFileSync(path.join(here, "..", "app.js"), "utf8");
  const m = app.match(/function inputRow\(\)\{[\s\S]*?\n\}/);
  const body = m ? m[0] : "";
  const todayAssignments = (body.match(/today:/g) || []).length;
  const allFromClock = (body.match(/today:new Date\(\)\.toISOString\(\)\.slice\(0,10\)/g) || []).length;
  check("E1 app.js inputRow passes a clock 'today' on both live and no-live paths", todayAssignments === 2 && allFromClock === 2, { todayAssignments, allFromClock });
  const server = fs.readFileSync(path.join(here, "..", "server.py"), "utf8");
  check("E2 server.py snapshot carries an ISO 'today'", /"today":\s*datetime\.now\(timezone\.utc\)\.astimezone\(\)\.date\(\)\.isoformat\(\)/.test(server), "today field not found");
}

const failed = results.filter(r => !r.ok);
for (const r of failed) console.log("FAIL", r.name, JSON.stringify(r.detail));
console.log(JSON.stringify({ cell: "19_DATA_GATE_DATES", PASS: pass, checks: results.length, failed: failed.length }));
process.exitCode = pass ? 0 : 1;
