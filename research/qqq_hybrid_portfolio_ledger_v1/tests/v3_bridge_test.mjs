import assert from "node:assert/strict";
import { bridge, normalizeSnapshot } from "../v3_bridge.js";

const carryFixture = {
  captured_at: "2026-10-07T00:00:00Z",
  qqq: 742,
  vxx: 30,
  vix: 16,
  m1: 17,
  m2: 18,
  term_asof: "2026-10-07",
  spot_asof: "2026-10-07",
  today: "2026-10-07",
  term_source: "FIXTURE",
};

const normalized = normalizeSnapshot(carryFixture);
assert.equal(normalized.s, ((18 - 17) / 17) * 100);

const result = await bridge({ fixture: carryFixture });
if (result.available) {
  assert.equal(result.connected, true);
  assert.equal(result.policy_owner, "V3");
  assert.equal(result.action, "BUY");
  assert.equal(result.state, "CARRY");
  assert.ok(result.engine_version);
  assert.ok(result.policy_version);
} else {
  assert.equal(result.connected, false);
}

const shockFixture = {
  ...carryFixture,
  vix: 31,
  m1: 20,
  m2: 19,
  term_source: "FIXTURE",
};
const shock = await bridge({ fixture: shockFixture });
if (shock.available) {
  assert.equal(shock.action, "REDUCE");
  assert.equal(shock.state, "SHOCK");
}

console.log("V3 BRIDGE CONTRACT TEST: PASS");
