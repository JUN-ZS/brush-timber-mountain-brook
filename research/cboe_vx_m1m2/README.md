# CBOE VX M1/M2 — contract archive reconstruction

The first daily-settlement collector was intentionally rejected after it proved
that the public daily endpoint only supplied a recent rolling window in this
runtime (the merge produced 216 rows from 2025-10-27 to 2026-09-04).

This version uses Cboe's historical per-contract VX CSV archives instead:
CFE_F18_VX.csv, CFE_G18_VX.csv, ... with one monthly contract per file.

Process:
1. Download every standard monthly VX contract from 2018 through 2026-09.
2. Parse Trade Date + Settle from each contract file.
3. On each date, select the two earliest monthly contracts that actually have
   a settlement row on that date; no weekly VX contracts are eligible.
4. Compute S = (M2-M1)/M1.
5. Validate the resulting series against the already observed 2016-2022
   M1/M2 archive before any P&L replay.

Evidence:
- contract settlement values are OBSERVED from Cboe-hosted historical CSV files;
- the M1/M2 mapping is DERIVED deterministically from observed contract rows;
- no synthetic term proxy is used;
- a failed overlap gate is STOP.

The historical Cboe archive exposes individual VX month files such as
CFE_F13_VX.csv and the historical-data page states VX price/volume detail is
available for selected futures from 2013 to current.
