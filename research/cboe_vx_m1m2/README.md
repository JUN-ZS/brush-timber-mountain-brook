# CBOE VX M1/M2 — 2018-2026 reconstruction gate

Status: research-only; data acquisition + validation.

Execution is intentionally isolated from main strategy policy. A temporary PR QA
bridge may execute this collector for PR #83; the collector itself never places
orders and never changes P&L logic.

## Goal

Obtain contract-level daily VX observations across the full Original-Hybrid
window (2018-03-01 through 2026-09-04) from the Cboe public daily settlement
CSV endpoint, then validate the M1/M2 selection against the already archived
observed 2016-03-01 through 2022-04-08 dataset.

This stage does not modify strategy parameters, policy logic, or P&L.

## Selection contract

For each trade date:

- keep standard monthly VX contracts (symbol starts with VX/);
- exclude weekly VXNN contracts and VXT/VXM products;
- require expiration strictly after the trade date;
- sort by expiration;
- earliest = M1;
- second-earliest = M2;
- compute S = (M2-M1)/M1.

## Gate

Before any full replay, the merged history must pass:

research/data/vx_m1_m2_external_2016_2022.csv

The validator requires at least 900 common dates, at least 99% of compared
M1/M2 pairs within $0.10, no more than 1% term-sign mismatch, and zero
expiration-order violations.

A failed gate is STOP. Do not smooth, proxy, reinterpret, or retune.

## Evidence classes

- OBSERVED: price/contract row returned directly by Cboe.
- DERIVED: M1/M2 chosen deterministically from the observed contract rows.
- HYPOTHETICAL: not used in this stage.

The resulting file is research data, not a live-data entitlement.
