import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_PROTECTED, assertPutCushionsDownDay, firstWaveGrid, putOpeningLedgerEntry, runProtected } from "./protected.ts";
import { buyHoldQQQ, sampleWindow } from "./backtest.ts";

test("first-wave grid is finite and PROTECTED-only", () => {
  const g = firstWaveGrid();
  assert.equal(g.length, 3 * 3 * 2 * 2 * 3 * 3 * 2);
  assert.ok(g.length <= 700);
});

test("zero put overlay tracks QQQ 100% (Observed path)", () => {
  const w = sampleWindow();
  const zero = runProtected(
    {
      ...DEFAULT_PROTECTED,
      calmPut: 0,
      unstablePut: 0,
      tailPut: 0,
      recoveryPut: 0,
      buildingPut: 0,
    },
    w.start,
    w.trainEnd,
    false,
  );
  const hold = buyHoldQQQ();
  assert.ok(Math.abs(zero.split.train.cagr - hold.split.train.cagr) < 0.002);
  assert.ok(Math.abs(zero.split.train.maxDd - hold.split.train.maxDd) < 0.01);
});

test("put overlay cushions a historical -8% QQQ day", () => {
  const g = assertPutCushionsDownDay();
  assert.equal(g.ok, true);
  assert.ok(g.overlay > g.qqq);
});


test("PUT opening records the asset mark separately from the ask cash outlay", () => {
  const opened = putOpeningLedgerEntry(1, 10, 0.1);
  assert.equal(opened.assetMarkValue, 10);
  assert.ok(Math.abs(opened.cashPaid - 11) < 1e-12);
  assert.ok(Math.abs(opened.assetMarkValue - opened.cashPaid - (-1)) < 1e-12);
});

test("PUT open-mid and subsequent marks produce correct ask-to-bid P&L", () => {
  const contracts = 1;
  const opened = putOpeningLedgerEntry(contracts, 10, 0.1);
  let putPnl = opened.assetMarkValue;
  putPnl += contracts * (12 - 10);   // mark-up while held
  putPnl += contracts * (10.8 - 12); // closing at bid
  const netPnl = putPnl - opened.cashPaid;
  assert.ok(Math.abs(netPnl - (-0.2)) < 1e-12);
});

test("a worthless expiry loses the ask paid exactly once", () => {
  const contracts = 2;
  const opened = putOpeningLedgerEntry(contracts, 10, 0.1);
  const terminalIntrinsic = 0;
  const putPnl = opened.assetMarkValue + contracts * (terminalIntrinsic - 10);
  const netPnl = putPnl - opened.cashPaid;
  assert.ok(Math.abs(netPnl - (-22)) < 1e-12);
  assert.ok(Math.abs(netPnl - (-opened.cashPaid)) < 1e-12);
});

test("PUT opening ledger rejects invalid market inputs", () => {
  assert.throws(() => putOpeningLedgerEntry(1, 10, -0.1), RangeError);
  assert.throws(() => putOpeningLedgerEntry(1, Number.NaN, 0.1), RangeError);
});
