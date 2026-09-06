import assert from "node:assert/strict";
import test from "node:test";
import {
  emptyQuote,
  previewConnection,
  runScenarios,
  selectLiveStructure,
  eodSpot,
  derivedState,
  suggestedRisk,
} from "./live.ts";

test("preview cannot claim LIVE OpenD", () => {
  const c = previewConnection();
  assert.equal(c.status, "WAITING_FOR_LOCAL_DIAGNOSTIC");
  assert.equal(c.issueClass, "ENVIRONMENT");
});

test("empty quote is UNAVAILABLE not zero live", () => {
  const q = emptyQuote("US.QQQ", "no opend");
  assert.equal(q.source, "UNAVAILABLE");
  assert.equal(q.last, null);
});

test("selector refuses non-live contracts", () => {
  const out = selectLiveStructure(
    [
      {
        code: "SYNTH",
        strike: 500,
        dte: 30,
        right: "PUT",
        bid: 8,
        ask: 8.2,
        last: 8.1,
        mid: 8.1,
        iv: 0.2,
        delta: -0.25,
        gamma: null,
        theta: null,
        vega: null,
        oi: null,
        spreadPct: 0.02,
        source: "SYNTHETIC",
      },
    ],
    520,
    "UNSTABLE",
  );
  assert.equal(out.status, "NOT_AVAILABLE");
  assert.equal(out.source, "UNAVAILABLE");
});

test("selector refuses without live spot", () => {
  const out = selectLiveStructure([], null, "CALM");
  assert.equal(out.status, "NOT_AVAILABLE");
});

test("scenario shocked options are DERIVED", () => {
  const rows = runScenarios({ spot: 500, iv: 0.18, spotSource: "DERIVED", ivSource: "DERIVED" });
  assert.ok(rows.length > 0);
  assert.ok(rows.filter((r) => r.structure !== "QQQ_ONLY").every((r) => r.shockedOptionSource === "DERIVED"));
  const qqqOnly = rows.find((r) => r.structure === "QQQ_ONLY" && r.shock === -0.05);
  const otm = rows.find((r) => r.structure === "OTM5_PUT" && r.shock === -0.05);
  assert.ok(qqqOnly && otm);
  assert.ok(otm.totalPnl > qqqOnly.totalPnl);
});

test("eod spot is labelled DERIVED", () => {
  const s = eodSpot();
  assert.equal(s.source, "DERIVED");
  assert.ok(s.qqq == null || s.qqq > 0);
});

test("derived state uses V2.2 rules", () => {
  const s = derivedState();
  assert.ok(["CALM", "UNSTABLE", "TAIL", "RECOVERY"].includes(s.regime));
  const r = suggestedRisk(s.regime, s.building);
  assert.equal(r.qqqExposure, 1);
  if (s.building) assert.ok(r.putHedge >= 0.75);
});
