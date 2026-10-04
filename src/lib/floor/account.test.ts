import test from "node:test";
import assert from "node:assert/strict";
import {
  actualContributed,
  actualWithdrawn,
  clockTarget,
  createEntry,
  defaultFloorAccount,
  fundingDelta,
  fundingStatus,
} from "./account.ts";

test("month zero has a zero Floor clock target", () => {
  assert.equal(clockTarget(100_000, 0), 0);
  assert.equal(fundingStatus(fundingDelta(100_000, 0, [])), "ON_CLOCK");
});

test("funding status uses Actual contributed minus CLOCK only", () => {
  const entries = [
    createEntry("CONTRIBUTION", 36_000, 48, "2026-10-04T00:00:00Z"),
    createEntry("WITHDRAWAL", 5_000, 48, "2026-10-04T00:01:00Z"),
  ];

  assert.equal(clockTarget(100_000, 48), 40_000);
  assert.equal(actualContributed(entries), 36_000);
  assert.equal(actualWithdrawn(entries), 5_000);
  assert.equal(fundingDelta(100_000, 48, entries), -4_000);
  assert.equal(fundingStatus(-4_000), "BEHIND");
});

test("NAV never participates in funding status", () => {
  const entries = [createEntry("CONTRIBUTION", 50_000, 60, "2026-10-04T00:00:00Z")];
  const lowNav = defaultFloorAccount();
  const highNav = { ...lowNav, nav: 1_000_000 };

  assert.equal(fundingDelta(highNav.plannedPrincipal, 60, entries), 0);
  assert.equal(fundingDelta(lowNav.plannedPrincipal, 60, entries), 0);
  assert.equal(fundingStatus(fundingDelta(highNav.plannedPrincipal, 60, entries)), "ON_CLOCK");
});

test("CLOCK endpoints remain exactly 0% and 100% of B", () => {
  assert.equal(clockTarget(100_000, 0), 0);
  assert.equal(clockTarget(100_000, 120), 100_000);
});

test("withdrawal never changes Actual contributed", () => {
  const entries = [
    createEntry("CONTRIBUTION", 70_000, 84, "2026-10-04T00:00:00Z"),
    createEntry("WITHDRAWAL", 20_000, 84, "2026-10-04T00:02:00Z"),
  ];

  assert.equal(actualContributed(entries), 70_000);
  assert.equal(actualWithdrawn(entries), 20_000);
});


test("voided funding entries are retained but excluded from formal totals", () => {
  const contribution = createEntry("CONTRIBUTION", 50_000, 60, "2026-10-04T00:00:00Z");
  const withdrawal = createEntry("WITHDRAWAL", 7_000, 60, "2026-10-04T00:01:00Z");
  const entries = [
    contribution,
    { ...withdrawal, voidedAt: "2026-10-04T00:02:00Z" },
    { ...contribution, id: "voided-contribution", voidedAt: "2026-10-04T00:03:00Z" },
  ];
  assert.equal(actualContributed(entries), 50_000);
  assert.equal(actualWithdrawn(entries), 0);
});
