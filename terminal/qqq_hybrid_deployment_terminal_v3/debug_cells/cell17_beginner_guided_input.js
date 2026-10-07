import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
globalThis.window = {};
vm.runInThisContext(fs.readFileSync(path.join(here, "..", "engine.js"), "utf8"));
const E = globalThis.window.HybridEngineV3;

// IMPORTANT:
// This is a beginner-facing input translator AND an independent audit harness.
// It deliberately does NOT use E.derive / E.targetLedger to calculate the expected
// result. Frozen baseline constants below are copied as a contract so the guide can
// catch accidental drift in the production engine.
const CONTRACT = Object.freeze({
  corePct: 42,
  vxxNormalPct: 18,
  vxxHighPct: 10,
  qqqCallBudgetPct: 1.2,
  vxxCallBudgetPct: 2,
  vixHigh: 28,
  termSafe: 5,
  maxTermAgeDays: 4,
  mixedDateBlockDays: 2,
});

const TODAY_DEFAULT = new Date().toLocaleDateString("en-CA");

function localDate() {
  return new Date().toLocaleDateString("en-CA");
}

function finiteNumber(v) {
  const n = Number(String(v ?? "").replace(/,/g, "").trim());
  return Number.isFinite(n) ? n : null;
}

function daysBetween(a, b) {
  if (!a || !b) return null;
  const x = Date.parse(a + "T00:00:00Z");
  const y = Date.parse(b + "T00:00:00Z");
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return Math.abs(x - y) / 86400000;
}

function optionCountStatus(v) {
  const n = finiteNumber(v);
  if (n === null || n < 0) return "INVALID";
  return "VALUE";
}

function positionExists(book) {
  return book.qqqShares > 0 || book.vxxPct > 0 || book.qqqCalls > 0 || book.vxxCalls > 0;
}

function independentExpected(data, current) {
  const missingSpot = [data.qqq, data.vxx, data.vix].some(v => !Number.isFinite(v));
  const missingTerm = !Number.isFinite(data.m1) || !Number.isFinite(data.m2) || !Number.isFinite(data.s);
  if (missingSpot || missingTerm) {
    return {
      state: "DATA BLOCKED",
      action: "HOLD",
      gate: "BLOCKED",
      blocked: true,
      reasonClass: "MISSING_REQUIRED_DATA",
      target: { qqqShares: current.qqqShares, vxxPct: current.vxxPct, qqqCalls: current.qqqCalls, vxxCalls: current.vxxCalls },
    };
  }

  const termAge = daysBetween(data.termAsOf, data.today);
  if (termAge !== null && termAge > CONTRACT.maxTermAgeDays) {
    return {
      state: "DATA STALE",
      action: "HOLD",
      gate: "STALE",
      blocked: true,
      reasonClass: "STALE_TERM_DATA",
      target: { qqqShares: current.qqqShares, vxxPct: current.vxxPct, qqqCalls: current.qqqCalls, vxxCalls: current.vxxCalls },
    };
  }

  const asofGap = data.spotAsOf && data.termAsOf ? daysBetween(data.spotAsOf, data.termAsOf) : 0;
  if (asofGap !== null && asofGap > CONTRACT.mixedDateBlockDays) {
    return {
      state: "AS-OF MIXED",
      action: "HOLD",
      gate: "MIXED",
      blocked: true,
      reasonClass: "MATERIAL_DATE_MIX",
      target: { qqqShares: current.qqqShares, vxxPct: current.vxxPct, qqqCalls: current.qqqCalls, vxxCalls: current.vxxCalls },
    };
  }

  const high = data.vix >= CONTRACT.vixHigh;
  const backwardation = data.s <= 0;
  const thin = data.s <= CONTRACT.termSafe;

  let state;
  let action;
  let gate;
  let reasonClass;
  if (high && backwardation) {
    state = "SHOCK";
    action = "REDUCE";
    gate = "CUT";
    reasonClass = "VIX_HIGH_AND_BACKWARDATION";
  } else if (backwardation) {
    state = "PRE-SHOCK";
    action = "REDUCE";
    gate = "CUT";
    reasonClass = "BACKWARDATION";
  } else if (high) {
    state = "PRE-SHOCK";
    action = "REDUCE";
    gate = "CAP";
    reasonClass = "VIX_HIGH";
  } else if (thin) {
    state = "WEAKENING";
    action = "HOLD";
    gate = "WATCH";
    reasonClass = "THIN_CONTANGO";
  } else {
    state = "CARRY";
    action = "BUY";
    gate = "OPEN";
    reasonClass = "HEALTHY_CONTANGO";
  }

  const vxxTarget = backwardation ? 0 : (high ? CONTRACT.vxxHighPct : CONTRACT.vxxNormalPct);
  const qqqCallBudget = backwardation || high ? 0 : CONTRACT.qqqCallBudgetPct;
  const vxxCallBudget = backwardation || high ? 0 : CONTRACT.vxxCallBudgetPct;

  // Keep the independent target shape identical to the production Ledger
  // on every non-blocked path, including HOLD.
  let target = {
    qqqShares: current.qqqShares,
    vxxPct: current.vxxPct,
    qqqCalls: current.qqqCalls,
    vxxCalls: current.vxxCalls,
  };
  if (action === "BUY") {
    const qqqTargetShares = data.qqq > 0
      ? Math.floor((current.nav * CONTRACT.corePct / 100) / data.qqq)
      : current.qqqShares;
    target = {
      qqqShares: qqqTargetShares,
      vxxPct: vxxTarget,
      qqqCalls: current.qqqCalls,
      vxxCalls: current.vxxCalls,
    };
  } else if (action === "REDUCE") {
    // Independent mirror of targetLedger REDUCE: option budgets are zero,
    // so existing seller option legs converge toward zero via min(current, 0).
    target = {
      qqqShares: current.qqqShares,
      vxxPct: Math.min(current.vxxPct, vxxTarget),
      qqqCalls: Math.min(current.qqqCalls, qqqCallBudget > 0 ? current.qqqCalls : 0),
      vxxCalls: Math.min(current.vxxCalls, vxxCallBudget > 0 ? current.vxxCalls : 0),
    };
  }

  return {
    state,
    action,
    gate,
    blocked: false,
    reasonClass,
    target,
    budgets: { qqqCallBudget, vxxCallBudget },
    qqqCoreTargetPct: CONTRACT.corePct,
    vxxTarget,
  };
}

function independentActionClass(engineAction, deltas, hasPosition, blocked) {
  if (blocked) return "PAUSE";
  const adds = Object.values(deltas).some(v => Number.isFinite(v) && v > 1e-9);
  const reductions = Object.values(deltas).some(v => Number.isFinite(v) && v < -1e-9);

  if (engineAction === "REDUCE") return "DEFEND";
  if (engineAction === "BUY") {
    if (adds && reductions) return "REBALANCE";
    if (adds) return "BUILD";
    return hasPosition ? "MAINTAIN" : "READY";
  }
  if (engineAction === "HOLD") return hasPosition ? "MAINTAIN" : "READY";
  return "READY";
}

function compareDeep(label, actual, expected) {
  try {
    assert.deepStrictEqual(actual, expected);
    console.log("  PASS  " + label);
    return true;
  } catch (err) {
    console.log("  FAIL  " + label);
    console.log("        expected:", JSON.stringify(expected));
    console.log("        actual:  ", JSON.stringify(actual));
    return false;
  }
}

function summarizeGuide(data, current, audit) {
  const actualData = E.derive(data);
  const actualBook = E.targetLedger(
    data,
    actualData,
    {
      nav: current.nav,
      qqqShares: current.qqqShares,
      vxxPct: current.vxxPct,
      qqqCalls: current.qqqCalls,
      vxxCalls: current.vxxCalls,
      inputStatus: { status: "READY", invalid: [], empty: [], fields: {} },
    },
    {},
  );
  const funding = E.fundingPlan({
    d: data,
    e: actualData,
    book: { current: { ...actualBook.current, nav: current.nav } },
    strategyPool: "",
    newCapital: "",
  });
  const bridge = E.strategyActionBridge({
    d: data,
    e: actualData,
    book: actualBook,
    funding,
    currentOptionLegs: E.currentOptionLegs({
      qqq: { qty: current.qqqCalls },
      vxx: { qty: current.vxxCalls },
    }),
    journalRows: [],
  });

  const expectedState = audit.expected;
  const expectedDeltas = {
    qqqShares: expectedState.target.qqqShares - current.qqqShares,
    vxxPct: expectedState.target.vxxPct - current.vxxPct,
    qqqCalls: expectedState.target.qqqCalls - current.qqqCalls,
    vxxCalls: expectedState.target.vxxCalls - current.vxxCalls,
  };
  const expectedClass = independentActionClass(
    expectedState.action,
    expectedDeltas,
    positionExists(current),
    expectedState.blocked,
  );

  console.log("");
  console.log("==============================================");
  console.log("小白引導結果");
  console.log("==============================================");
  console.log("你的 NAV（簡化）      : USD " + current.nav.toLocaleString("en-US", { maximumFractionDigits: 2 }));
  console.log("QQQ                   : " + current.qqqShares + " shares");
  console.log("QQQ 市值              : USD " + (current.qqqShares * data.qqq).toLocaleString("en-US", { maximumFractionDigits: 2 }));
  console.log("VXX short              : " + current.vxxPct + "% NAV");
  console.log("QQQ far-call           : " + current.qqqCalls + " spreads");
  console.log("VXX call               : " + current.vxxCalls + " spreads");
  console.log("");
  console.log("市場：QQQ " + data.qqq + " · VXX " + data.vxx + " · VIX " + data.vix);
  console.log("VX：M1 " + data.m1 + " → M2 " + data.m2 + " · S = " + data.s.toFixed(2) + "%");
  console.log("狀態：" + actualData.state + " · Engine Action：" + actualData.action + " · Gate：" + actualData.gate);
  console.log("");
  console.log("CURRENT → TARGET");
  console.log("  QQQ  : " + current.qqqShares + " → " + actualBook.target.qqqShares + " (" + (actualBook.deltas.qqqShares >= 0 ? "+" : "") + actualBook.deltas.qqqShares + ")");
  console.log("  VXX  : " + current.vxxPct + "% → " + actualBook.target.vxxPct + "% (" + (actualBook.deltas.vxxPct >= 0 ? "+" : "") + actualBook.deltas.vxxPct + " pp)");
  console.log("  QQQ far-call: " + current.qqqCalls + " → " + actualBook.target.qqqCalls);
  console.log("  VXX call    : " + current.vxxCalls + " → " + actualBook.target.vxxCalls);
  console.log("");
  console.log("Cell 16 對人說：" + bridge.actionClass);
  console.log("操作提示：" + bridge.operatorInstruction);
  console.log("Funding：" + bridge.funding.route + " · " + bridge.funding.status);
  console.log("下一步：" + bridge.nextStep);
  console.log("Broker：" + (bridge.noBrokerOrder ? "NO AUTO ORDER · 手動執行" : "UNEXPECTED"));

  console.log("");
  console.log("==============================================");
  console.log("反推 Audit：獨立規則 ↔ 正式 Engine");
  console.log("==============================================");
  compareDeep("Decision.state", actualData.state, expectedState.state);
  compareDeep("Decision.action", actualData.action, expectedState.action);
  compareDeep("Decision.gate", actualData.gate, expectedState.gate);
  compareDeep("Decision.blocked", actualData.blocked, expectedState.blocked);
  compareDeep("Target", actualBook.target, expectedState.target);
  compareDeep("Deltas", actualBook.deltas, expectedDeltas);
  compareDeep("Cell16.actionClass", bridge.actionClass, expectedClass);

  const pass =
    actualData.state === expectedState.state &&
    actualData.action === expectedState.action &&
    actualData.gate === expectedState.gate &&
    actualData.blocked === expectedState.blocked &&
    JSON.stringify(actualBook.target) === JSON.stringify(expectedState.target) &&
    JSON.stringify(actualBook.deltas) === JSON.stringify(expectedDeltas) &&
    bridge.actionClass === expectedClass &&
    bridge.noBrokerOrder === true;

  console.log("");
  console.log("AUDIT RESULT: " + (pass ? "PASS" : "FAIL"));
  return { pass, actualData, actualBook, bridge, expectedState, expectedDeltas, expectedClass };
}

function makeData({ qqPrice = 750, vxxPrice = 20, vix = 16, m1 = 16.2, m2 = 17.2, today = TODAY_DEFAULT, termAsOf = today, spotAsOf = today, source = "CBOE_PUBLIC_DELAYED_VX" } = {}) {
  return {
    qqq: qqPrice,
    vxx: vxxPrice,
    vix,
    m1,
    m2,
    s: ((m2 - m1) / m1) * 100,
    termAsOf,
    spotAsOf,
    today,
    term_source: source,
    provenance: source === "CBOE_PUBLIC_DELAYED_VX"
      ? { m1: "CBOE_PUBLIC_DELAYED_VX", m2: "CBOE_PUBLIC_DELAYED_VX", term_slope: "DERIVED_FROM_CBOE_M1_M2", qqq: "OPEND", vxx: "OPEND", vix: "OPEND" }
      : { m1: "OPEND_VX", m2: "OPEND_VX", term_slope: "DERIVED_FROM_OPEND_VX", qqq: "OPEND", vxx: "OPEND", vix: "OPEND" },
  };
}

async function askLine(rl, label, defaultValue = "") {
  const suffix = defaultValue !== "" ? " [" + defaultValue + "]" : "";
  const answer = (await rl.question(label + suffix + ": ")).trim();
  return answer === "" ? String(defaultValue) : answer;
}

async function askNumber(rl, label, { min = 0, allowBlank = false, defaultValue = "" } = {}) {
  while (true) {
    const raw = await askLine(rl, label, defaultValue);
    if (allowBlank && raw === "") return null;
    const n = finiteNumber(raw);
    if (n !== null && n >= min) return n;
    console.log("  請輸入 >= " + min + " 的數字。");
  }
}

async function askChoice(rl, title, options, defaultIndex = 1) {
  console.log("");
  console.log(title);
  options.forEach((x, i) => console.log("  " + (i + 1) + ") " + x));
  while (true) {
    const raw = await askLine(rl, "選", String(defaultIndex));
    const n = Number(raw);
    if (Number.isInteger(n) && n >= 1 && n <= options.length) return n;
    console.log("  請輸入 1-" + options.length + "。");
  }
}

async function interactive() {
  const rl = createInterface({ input, output });
  try {
    console.log("");
    console.log("QQQ HYBRID · BEGINNER GUIDED INPUT");
    console.log("呢個程式只做三件事：問你 → 翻譯成正式輸入 → 反推 Engine 有冇跟對。");
    console.log("唔抓市場、唔下單；VXX short 用 % NAV，call spreads 用 contracts。");
    console.log("");

    const cash = await askNumber(rl, "1/7 現金 USD（例如 100000）", { min: 0 });
    const qqqShares = await askNumber(rl, "2/7 你有幾多 QQQ shares", { min: 0 });
    const qqqPrice = await askNumber(rl, "3/7 現在 QQQ 價格", { min: 0.000001 });
    const vxxPrice = await askNumber(rl, "4/7 現在 VXX 價格（只作 exposure 換算顯示）", { min: 0.000001 });

    const currentNav = cash + qqqShares * qqqPrice;
    console.log("  → 引導器計算簡化 NAV = cash + QQQ 市值 = USD " + currentNav.toLocaleString("en-US", { maximumFractionDigits: 2 }));

    const vxxPct = await askNumber(rl, "5/7 現有 VXX short 是幾多 % NAV（冇就 0）", { min: 0 });
    const qqqCalls = await askNumber(rl, "6/7 現有 QQQ far-call credit spreads 幾張（冇就 0）", { min: 0 });
    const vxxCalls = await askNumber(rl, "7/7 現有 VXX call credit spreads 幾張（冇就 0）", { min: 0 });

    console.log("");
    console.log("而家問市場條件。你唔需要自己計 S；程式會用 M1/M2 計。");
    const vix = await askNumber(rl, "VIX", { min: 0 });
    const m1 = await askNumber(rl, "VX M1", { min: 0.000001 });
    const m2 = await askNumber(rl, "VX M2", { min: 0.000001 });
    const today = await askLine(rl, "今天日期 YYYY-MM-DD", localDate());
    const termAsOf = await askLine(rl, "M1/M2 的資料日期 YYYY-MM-DD", today);
    const spotAsOf = await askLine(rl, "QQQ/VXX/VIX 的資料日期 YYYY-MM-DD", today);
    const sourceChoice = await askChoice(
      rl,
      "VX term source",
      ["Cboe delayed settlement（配 live spot 時會顯示 MIXED-SOURCE warning）", "OpenD / live VX"],
      1,
    );
    const source = sourceChoice === 1 ? "CBOE_PUBLIC_DELAYED_VX" : "OPEND_VX_LIVE";

    const data = makeData({
      qqPrice: qqqPrice,
      vxxPrice,
      vix,
      m1,
      m2,
      today,
      termAsOf,
      spotAsOf,
      source,
    });
    const current = {
      nav: currentNav,
      qqqShares,
      vxxPct,
      qqqCalls,
      vxxCalls,
    };
    const expected = independentExpected(data, current);
    const audit = { expected };
    return summarizeGuide(data, current, audit);
  } finally {
    rl.close();
  }
}

function runSelfTest() {
  const today = "2026-10-08";
  const current = { nav: 175000, qqqShares: 100, vxxPct: 0, qqqCalls: 0, vxxCalls: 0 };
  const cases = [
    { name: "DEMO CARRY", data: makeData({ today, termAsOf: today, spotAsOf: today }) },
    { name: "WEAKENING", data: makeData({ today, m1: 16, m2: 16.48, termAsOf: today, spotAsOf: today }) },
    { name: "PRE-SHOCK BACKWARDATION", data: makeData({ today, m1: 16.2, m2: 16.0, termAsOf: today, spotAsOf: today }) },
    { name: "PRE-SHOCK HIGH VIX", data: makeData({ today, vix: 30, m1: 16.2, m2: 17.2, termAsOf: today, spotAsOf: today }) },
    { name: "SHOCK", data: makeData({ today, vix: 35, m1: 16.2, m2: 15.5, termAsOf: today, spotAsOf: today }) },
    { name: "STALE", data: makeData({ today, termAsOf: "2026-10-01", spotAsOf: today }) },
    { name: "BLOCKED", data: makeData({ today, m1: null, m2: null, termAsOf: today, spotAsOf: today }) },
    { name: "DATE MIX", data: makeData({ today, termAsOf: "2026-10-08", spotAsOf: "2026-10-04" }) },
  ];

  let allPass = true;
  console.log("CELL 17 · BEGINNER GUIDED INPUT · SELF TEST");
  console.log("Independent contract constants:", JSON.stringify(CONTRACT));
  for (const c of cases) {
    const e = independentExpected(c.data, current);
    const actual = E.derive(c.data);
    const book = E.targetLedger(
      c.data,
      actual,
      {
        nav: current.nav,
        qqqShares: current.qqqShares,
        vxxPct: current.vxxPct,
        qqqCalls: current.qqqCalls,
        vxxCalls: current.vxxCalls,
        inputStatus: { status: "READY", invalid: [], empty: [], fields: {} },
      },
      {},
    );
    const f = E.fundingPlan({
      d: c.data,
      e: actual,
      book: { current: { ...book.current, nav: current.nav } },
      strategyPool: "",
      newCapital: "",
    });
    const b = E.strategyActionBridge({
      d: c.data,
      e: actual,
      book,
      funding: f,
      currentOptionLegs: E.currentOptionLegs({ qqq: { qty: current.qqqCalls }, vxx: { qty: current.vxxCalls } }),
      journalRows: [],
    });
    const expectedDeltas = {
      qqqShares: e.target.qqqShares - current.qqqShares,
      vxxPct: e.target.vxxPct - current.vxxPct,
      qqqCalls: e.target.qqqCalls - current.qqqCalls,
      vxxCalls: e.target.vxxCalls - current.vxxCalls,
    };
    const expectedClass = independentActionClass(e.action, expectedDeltas, positionExists(current), e.blocked);
    const pass =
      actual.state === e.state &&
      actual.action === e.action &&
      actual.gate === e.gate &&
      actual.blocked === e.blocked &&
      JSON.stringify(book.target) === JSON.stringify(e.target) &&
      JSON.stringify(book.deltas) === JSON.stringify(expectedDeltas) &&
      b.actionClass === expectedClass &&
      b.noBrokerOrder === true;
    console.log((pass ? "PASS" : "FAIL") + " · " + c.name + " · " + actual.state + "/" + actual.action + " · Cell16=" + b.actionClass);
    if (!pass) {
      console.log("  expected state:", e.state, "actual:", actual.state);
      console.log("  expected action:", e.action, "actual:", actual.action);
      console.log("  expected target:", JSON.stringify(e.target), "actual:", JSON.stringify(book.target));
      console.log("  expected class:", expectedClass, "actual:", b.actionClass);
      allPass = false;
    }
  }

  // HOLD shape regression: independent expected target must contain exactly
  // the four production Ledger fields, never NAV.
  {
    const holdData = makeData({
      today,
      m1: 16,
      m2: 16.48,
      termAsOf: today,
      spotAsOf: today,
    });
    const holdExpected = independentExpected(holdData, current);
    const holdEngine = E.derive(holdData);
    const holdActual = E.targetLedger(
      holdData,
      holdEngine,
      {
        nav: current.nav,
        qqqShares: current.qqqShares,
        vxxPct: current.vxxPct,
        qqqCalls: current.qqqCalls,
        vxxCalls: current.vxxCalls,
        inputStatus: { status: "READY", invalid: [], empty: [], fields: {} },
      },
      {},
    );
    const exactShape = JSON.stringify(holdExpected.target) === JSON.stringify(holdActual.target);
    const noNav = !Object.prototype.hasOwnProperty.call(holdExpected.target, "nav");
    const pass = holdEngine.state === "WEAKENING" && holdEngine.action === "HOLD" && exactShape && noNav;
    console.log((pass ? "PASS" : "FAIL") + " · HOLD TARGET SHAPE · four Ledger fields only");
    if (!pass) {
      console.log("  expected target:", JSON.stringify(holdExpected.target), "actual:", JSON.stringify(holdActual.target));
      allPass = false;
    }
  }

  // Active seller regression: reduction must also test existing option legs,
  // not only a flat book. The production REDUCE budget is zero, so 21/4 -> 0/0.
  {
    const activeSeller = { nav: 100000, qqqShares: 100, vxxPct: 18, qqqCalls: 21, vxxCalls: 4 };
    const shockData = makeData({
      today,
      qqPrice: 750,
      vxxPrice: 20,
      vix: 35,
      m1: 16.2,
      m2: 15.5,
      termAsOf: today,
      spotAsOf: today,
    });
    const e = independentExpected(shockData, activeSeller);
    const actual = E.derive(shockData);
    const book = E.targetLedger(
      shockData,
      actual,
      {
        nav: activeSeller.nav,
        qqqShares: activeSeller.qqqShares,
        vxxPct: activeSeller.vxxPct,
        qqqCalls: activeSeller.qqqCalls,
        vxxCalls: activeSeller.vxxCalls,
        inputStatus: { status: "READY", invalid: [], empty: [], fields: {} },
      },
      {},
    );
    const f = E.fundingPlan({
      d: shockData,
      e: actual,
      book: { current: { ...book.current, nav: activeSeller.nav } },
      strategyPool: "",
      newCapital: "",
    });
    const b = E.strategyActionBridge({
      d: shockData,
      e: actual,
      book,
      funding: f,
      currentOptionLegs: E.currentOptionLegs({
        qqq: { qty: activeSeller.qqqCalls },
        vxx: { qty: activeSeller.vxxCalls },
      }),
      journalRows: [],
    });
    const expectedDeltas = {
      qqqShares: e.target.qqqShares - activeSeller.qqqShares,
      vxxPct: e.target.vxxPct - activeSeller.vxxPct,
      qqqCalls: e.target.qqqCalls - activeSeller.qqqCalls,
      vxxCalls: e.target.vxxCalls - activeSeller.vxxCalls,
    };
    const pass =
      actual.state === "SHOCK" &&
      actual.action === "REDUCE" &&
      book.target.qqqCalls === 0 &&
      book.target.vxxCalls === 0 &&
      e.target.qqqCalls === 0 &&
      e.target.vxxCalls === 0 &&
      JSON.stringify(book.target) === JSON.stringify(e.target) &&
      JSON.stringify(book.deltas) === JSON.stringify(expectedDeltas) &&
      b.actionClass === "DEFEND";
    console.log((pass ? "PASS" : "FAIL") + " · ACTIVE SELLER SHOCK · 21/4 → " + book.target.qqqCalls + "/" + book.target.vxxCalls + " · Cell16=" + b.actionClass);
    if (!pass) {
      console.log("  expected target:", JSON.stringify(e.target), "actual:", JSON.stringify(book.target));
      allPass = false;
    }
  }

  // Explicit small-white demo: 100 QQQ + USD 100,000 cash at QQQ 750.
  const demoData = makeData({ today, termAsOf: today, spotAsOf: today, qqPrice: 750, vxxPrice: 20, vix: 16, m1: 16.2, m2: 17.2 });
  const demo = summarizeGuide(demoData, current, { expected: independentExpected(demoData, current) });
  allPass = allPass && demo.pass;
  console.log("");
  console.log(JSON.stringify({
    cell: "17_BEGINNER_GUIDED_INPUT",
    checks: cases.length + 1,
    contractIsIndependent: true,
    demo: {
      cash: 100000,
      qqqShares: 100,
      qqqPrice: 750,
      expectedNav: 175000,
      expectedState: "CARRY",
      expectedEngineAction: "BUY",
      expectedCell16: "REBALANCE",
    },
    PASS: allPass,
  }));
  if (!allPass) process.exitCode = 1;
}

const args = new Set(process.argv.slice(2));
if (args.has("--self-test")) {
  runSelfTest();
} else if (args.has("--demo")) {
  const demoData = makeData({
    today: "2026-10-08",
    termAsOf: "2026-10-08",
    spotAsOf: "2026-10-08",
    qqPrice: 750,
    vxxPrice: 20,
    vix: 16,
    m1: 16.2,
    m2: 17.2,
  });
  summarizeGuide(
    demoData,
    { nav: 175000, qqqShares: 100, vxxPct: 0, qqqCalls: 0, vxxCalls: 0 },
    { expected: independentExpected(demoData, { nav: 175000, qqqShares: 100, vxxPct: 0, qqqCalls: 0, vxxCalls: 0 }) },
  );
} else {
  interactive().catch(err => {
    console.error("GUIDE ERROR:", err);
    process.exitCode = 1;
  });
}
