import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

// Cell 18 — Web beginner input (single responsibility: holdings input → NAV → ledger input status).
// Expected values are hand-computed literals; this cell never calls derive/targetLedger to build expectations.
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..");
globalThis.window = {};
vm.runInThisContext(fs.readFileSync(path.join(root, "engine.js"), "utf8"));
const E = globalThis.window.HybridEngineV3;
const out = {};

// A) NAV = cash + QQQ shares × QQQ price (hand: 100,000 + 100 × 750 = 175,000)
{
  const n = E.beginnerNav({ cash: "100,000", qqqShares: "100", qqqPrice: 750, navOverride: "" });
  assert.strictEqual(n.status, "VALUE"); assert.strictEqual(n.value, 175000); assert.strictEqual(n.source, "AUTO");
  const cashOnly = E.beginnerNav({ cash: "50000", qqqShares: "0", qqqPrice: null });
  assert.deepStrictEqual([cashOnly.status, cashOnly.value], ["VALUE", 50000]); // 0 shares → price not needed
  const noPrice = E.beginnerNav({ cash: "100000", qqqShares: "100", qqqPrice: null });
  assert.deepStrictEqual([noPrice.status, noPrice.value], ["EMPTY", null]); // 未能計, never 0
  const blankCash = E.beginnerNav({ cash: "", qqqShares: "100", qqqPrice: 750 });
  assert.deepStrictEqual([blankCash.status, blankCash.value], ["EMPTY", null]);
  const blankShares = E.beginnerNav({ cash: "100000", qqqShares: " ", qqqPrice: 750 });
  assert.deepStrictEqual([blankShares.status, blankShares.value], ["EMPTY", null]);
  for (const bad of ["abc", "-1", "0x10", "1,5", "1e3"]) {
    const r = E.beginnerNav({ cash: bad, qqqShares: "100", qqqPrice: 750 });
    assert.deepStrictEqual([r.status, r.value], ["INVALID", null], "cash " + bad);
  }
  const zeroNav = E.beginnerNav({ cash: "0", qqqShares: "0", qqqPrice: 750 });
  assert.deepStrictEqual([zeroNav.status, zeroNav.value], ["INVALID", null]); // NAV 0 never sizes
  const manual = E.beginnerNav({ cash: "", qqqShares: "", qqqPrice: null, navOverride: "200,000" });
  assert.deepStrictEqual([manual.status, manual.value, manual.source], ["VALUE", 200000, "MANUAL"]);
  const manualWins = E.beginnerNav({ cash: "100000", qqqShares: "100", qqqPrice: 750, navOverride: "180000" });
  assert.deepStrictEqual([manualWins.value, manualWins.source], [180000, "MANUAL"]);
  const badOverride = E.beginnerNav({ cash: "100000", qqqShares: "100", qqqPrice: 750, navOverride: "abc" });
  assert.deepStrictEqual([badOverride.status, badOverride.source], ["INVALID", "MANUAL"]); // never silently falls back
  const zeroOverride = E.beginnerNav({ cash: "100000", qqqShares: "100", qqqPrice: 750, navOverride: "0" });
  assert.strictEqual(zeroOverride.status, "INVALID");
  out.nav = { auto: n.value, cashOnly: cashOnly.value, noPrice: noPrice.status, manual: manual.value };
}

// B) VXX shares → % NAV (hand: 1,575 × 20 / 175,000 × 100 = 18)
{
  const c = E.vxxSharesToPct({ vxxShares: "1,575", vxxPrice: 20, nav: 175000 });
  assert.deepStrictEqual([c.status, c.value], ["VALUE", 18]);
  assert.deepStrictEqual(E.vxxSharesToPct({ vxxShares: "0", vxxPrice: null, nav: null }).value, 0);
  assert.strictEqual(E.vxxSharesToPct({ vxxShares: "", vxxPrice: 20, nav: 175000 }).status, "EMPTY");
  assert.strictEqual(E.vxxSharesToPct({ vxxShares: "1575", vxxPrice: null, nav: 175000 }).status, "EMPTY");
  assert.strictEqual(E.vxxSharesToPct({ vxxShares: "1575", vxxPrice: 20, nav: null }).status, "EMPTY");
  assert.strictEqual(E.vxxSharesToPct({ vxxShares: "-5", vxxPrice: 20, nav: 175000 }).status, "INVALID");
  out.vxxConversion = c.value;
}

// C) Ledger input status: blank ≠ 0, invalid ≠ 0, explicit 0 is valid
const px = { qqqPrice: 750, vxxPrice: 20 };
{
  const allBlank = E.beginnerLedger({}, px);
  assert.strictEqual(allBlank.inputStatus.status, "INCOMPLETE");
  assert.deepStrictEqual(allBlank.inputStatus.empty, ["nav", "qqqShares", "vxxPct", "qqqCalls", "vxxCalls"]);
  assert.deepStrictEqual([allBlank.nav, allBlank.qqqShares, allBlank.vxxPct], [null, null, null]);
  const invalid = E.beginnerLedger({ cash: "100000", qqqShares: "100", vxxPct: "abc", qqqCalls: "0", vxxCalls: "0" }, px);
  assert.strictEqual(invalid.inputStatus.status, "INVALID");
  assert.deepStrictEqual(invalid.inputStatus.invalid, ["vxxPct"]);
  assert.strictEqual(invalid.vxxPct, null);
  const zeros = E.beginnerLedger({ cash: "100,000", qqqShares: "0", vxxPct: "0", qqqCalls: "0", vxxCalls: "0" }, px);
  assert.strictEqual(zeros.inputStatus.status, "READY");
  assert.deepStrictEqual([zeros.nav, zeros.qqqShares, zeros.vxxPct, zeros.qqqCalls, zeros.vxxCalls], [100000, 0, 0, 0, 0]);
  const viaShares = E.beginnerLedger({ cash: "100000", qqqShares: "100", vxxShortShares: "1575", qqqCalls: "0", vxxCalls: "0" }, px);
  assert.strictEqual(viaShares.inputStatus.status, "READY");
  assert.deepStrictEqual([viaShares.nav, viaShares.vxxPct, viaShares.vxxInfo.source], [175000, 18, "SHARES"]);
  const pctWins = E.beginnerLedger({ cash: "100000", qqqShares: "100", vxxPct: "10", vxxShortShares: "1575", qqqCalls: "0", vxxCalls: "0" }, px);
  assert.deepStrictEqual([pctWins.vxxPct, pctWins.vxxInfo.source, typeof pctWins.vxxInfo.warning], [10, "PCT", "string"]);
  out.ledger = { allBlank: allBlank.inputStatus.status, invalid: invalid.inputStatus.status, zeros: zeros.inputStatus.status, viaSharesPct: viaShares.vxxPct };
}

// D) Decision layer shows NEEDS INPUT for a blank book (never BUILD from 0); READY book proceeds.
{
  const d = { qqq: 750, vxx: 20, vix: 16, m1: 16.2, m2: 17.2, s: ((17.2 - 16.2) / 16.2) * 100, termAsOf: "2026-10-08", spotAsOf: "2026-10-08", today: "2026-10-08" };
  const e = E.derive(d);
  const blankBook = E.targetLedger(d, e, E.beginnerLedger({}, px), {});
  assert.strictEqual(blankBook.inputBlocked, true);
  assert.deepStrictEqual(blankBook.deltas, { qqqShares: 0, vxxPct: 0, qqqCalls: 0, vxxCalls: 0 });
  const b = E.strategyActionBridge({ d, e, book: blankBook, funding: {} });
  assert.strictEqual(b.actionClass, "NEEDS_INPUT");
  assert.strictEqual(b.noBrokerOrder, true);
  assert.ok(b.operatorInstruction.includes("留空唔等於 0"));
  const s = E.operatorSummary(d, e, blankBook, {}, {});
  assert.strictEqual(s.mode, "NEEDS INPUT");
  assert.ok(!s.plan.some(x => /^(QQQ core|VXX short|QQQ far|VXX call) \+/.test(x)), "no add lines while NEEDS INPUT");
  assert.ok(s.plan[0].startsWith("第一步"));
  // Demo through the web path: hand math NAV 175,000 → QQQ floor(175000×42%/750)=98, VXX 18% → REBALANCE
  const demo = E.beginnerLedger({ cash: "100,000", qqqShares: "100", vxxPct: "0", qqqCalls: "0", vxxCalls: "0" }, px);
  const demoBook = E.targetLedger(d, e, demo, {});
  assert.strictEqual(demoBook.inputBlocked, false);
  assert.deepStrictEqual(demoBook.target, { qqqShares: 98, vxxPct: 18, qqqCalls: 0, vxxCalls: 0 });
  assert.strictEqual(E.strategyActionBridge({ d, e, book: demoBook, funding: {} }).actionClass, "REBALANCE");
  // Data PAUSE outranks NEEDS INPUT
  const dBlocked = { ...d, m1: null, m2: null, s: null };
  const eB = E.derive(dBlocked);
  assert.strictEqual(E.strategyActionBridge({ d: dBlocked, e: eB, book: E.targetLedger(dBlocked, eB, E.beginnerLedger({}, px), {}), funding: {} }).actionClass, "PAUSE");
  out.decision = { blank: b.actionClass, blankMode: s.mode, demoTarget: demoBook.target };
}

// E) Static web contract: blank defaults, text+decimal inputs, step-1 block, escaped plan, app syntax.
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
{
  assert.ok(html.includes("第一步：輸入你而家持有乜"));
  assert.ok(!/type="number"/.test(html), "no type=number inputs (they turn 'abc' into silent blank)");
  for (const id of ["cash", "qqqShares", "vxxPct", "vxxShortShares", "qqqCalls", "vxxCalls", "nav", "strategyPool", "newCapital"]) {
    const m = html.match(new RegExp('<input id="' + id + '"[^>]*>'));
    assert.ok(m, "input " + id);
    assert.ok(/type="text"/.test(m[0]) && /inputmode="decimal"/.test(m[0]), id + " text+decimal");
    assert.ok(/value=""/.test(m[0]) || !/value=/.test(m[0]), id + " starts blank");
  }
  assert.ok(!/value="(?!")[^"]*\d[^"]*"/.test(html), "no prefilled numeric default anywhere");
  assert.ok(html.includes('id="navInUse"'));
  assert.ok(app.includes("E.beginnerLedger("), "app ledger() uses the tested pure helper");
  assert.ok(app.includes("s.plan.map(x=>\"<div class='operator-line'>\"+escapeHtml(x)"), "operatorPlan escaped");
  const chk = spawnSync(process.execPath, ["--check", path.join(root, "app.js")], { encoding: "utf8" });
  assert.strictEqual(chk.status, 0, chk.stderr);
}

// F) Real app.js wiring in a minimal fake DOM (ids parsed from index.html; fetch stubbed; no network).
{
  const ids = [...html.matchAll(/id="([^"]+)"/g)].map(m => m[1]);
  const els = {};
  const mk = id => ({ id, value: "", textContent: "", innerHTML: "", className: "", checked: false, disabled: false, style: {},
    classList: { add() {}, remove() {} }, addEventListener(t, f) { (this._l ||= []).push(f); }, closest() { return null } });
  for (const id of ids) els[id] = mk(id);
  const snapshot = { qqq: 750, vxx: 20, vix: 16, m1: 16.2, m2: 17.2, term_slope: ((17.2 - 16.2) / 16.2) * 100,
    term_asof: new Date().toISOString().slice(0, 10), spot_asof: new Date().toISOString().slice(0, 10), term_source: "OPEND_VX_LIVE", provenance: {}, source_chain: [] };
  const ctx = vm.createContext({
    HybridEngineV3: E, console, setTimeout, Date, JSON, Number, String, Object, Array, Math, Set, Promise,
    document: { getElementById: id => els[id] || null },
    localStorage: { getItem: () => null, setItem() {} },
    fetch: async url => ({ ok: true, json: async () => (String(url).startsWith("/api/snapshot") ? snapshot : { rows: [] }) }),
  });
  vm.runInContext(app, ctx);
  await new Promise(r => setTimeout(r, 50)); // let refresh() resolve
  // Blank page → NEEDS INPUT everywhere, NAV 未能計, nothing built from 0
  assert.ok(els.navInUse.textContent.startsWith("NAV：未能計"), els.navInUse.textContent);
  assert.strictEqual(els.bridgeAction.textContent, "NEEDS_INPUT");
  assert.strictEqual(els.operatorMode.textContent, "NEEDS INPUT");
  assert.ok(els.queue.innerHTML.includes("NEEDS INPUT"));
  const blankUi = { nav: els.navInUse.textContent, bridge: els.bridgeAction.textContent, mode: els.operatorMode.textContent };
  // Type the beginner demo and fire input events
  const type = (id, v) => { els[id].value = v; for (const f of els[id]._l || []) f(); };
  type("cash", "100,000"); type("qqqShares", "100"); type("vxxPct", "0"); type("qqqCalls", "0"); type("vxxCalls", "0");
  assert.ok(els.navInUse.textContent.includes("AUTO") && els.navInUse.textContent.includes("175,000"), els.navInUse.textContent);
  assert.strictEqual(els.bridgeAction.textContent, "REBALANCE");
  assert.ok(els.bridgeTarget.textContent.includes("QQQ 98.00 shares"), els.bridgeTarget.textContent);
  assert.ok(els.ledgerRows.innerHTML.includes("REDUCE -2.00 shares") && els.ledgerRows.innerHTML.includes("ADD +18.00 % NAV"));
  // Manual override is labelled
  type("nav", "200000");
  assert.ok(els.navInUse.textContent.includes("MANUAL override"), els.navInUse.textContent);
  type("nav", "");
  // VXX by shares (③ blank) converts with live VXX price
  type("vxxPct", ""); type("vxxShortShares", "1,575");
  assert.ok(els.vxxConvertMeta.textContent.includes("= 18.00% NAV"), els.vxxConvertMeta.textContent);
  // Invalid entry is INVALID, not blank
  type("qqqCalls", "abc");
  assert.ok(els.inputStatusMeta.textContent.includes("無效"), els.inputStatusMeta.textContent);
  assert.strictEqual(els.bridgeAction.textContent, "NEEDS_INPUT");
  out.ui = { blank: blankUi, demoBridge: "REBALANCE", conversion: els.vxxConvertMeta.textContent };
}

console.log(JSON.stringify({ cell: "18_WEB_BEGINNER_INPUT", ...out, PASS: true }));
