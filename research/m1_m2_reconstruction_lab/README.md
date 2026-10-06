# M1/M2 Masked Reconstruction Lab V1

## Purpose

This app performs the forensic experiment:

REAL M1/M2 (evaluation truth)
→ MASK M1/M2
→ historical reconstruction method
→ synthetic M1/M2
→ compare at four layers

1. M1/M2 numerical error
2. S_t = (M2-M1)/M1 error
3. regime agreement
4. action agreement

The app is deliberately separate from the Live Deployment Terminal. It does not invent official Cboe provenance and it does not transmit broker orders.

## Current data

Input:
research/data/vx_m1_m2_external_2016_2022.csv

Coverage currently expected:
2016-03-01 → 2022-04-08
1,540 rows

Data status:
EXTERNAL_OBSERVED / UNVALIDATED_AGAINST_OFFICIAL_SOURCE

## Reconstruction method

Current method: ARCHIVE_V4_PROXY

Recovered historical clue:

lift = 0.10 * tanh((VIX_MA20 - VIX) / 6.0)
m2 = m1 * (1.0 + lift)

The archive also contains a VXX reconstruction equation, but that is a VXX path reconstruction, not M1/M2, so it is not used here.

Because the exact historical contract that produced the reported 12.5% result has not yet been recovered, this proxy is explicitly marked UNVALIDATED. The app must never label its outputs as a proof of the Original Hybrid result.

For the current proxy:
- m1_reconstructed = VIX (proxy assumption; not an observed VX contract)
- m2_reconstructed = m1_reconstructed * (1 + lift)

## Action layer

Action comparison uses the current terminal's deterministic baseline policy:
- SHOCK: VIX >= 28 and S <= 0 -> REDUCE
- PRE-SHOCK: S <= 0 or VIX >= 28 -> REDUCE
- WEAKENING: 0 < S <= 5% -> HOLD
- CARRY: S > 5% and VIX < 28 -> BUY

This is a POLICY_BASELINE comparison, not a recovered exact 12.5% forensic replay.

## No leakage contract

Reconstruction for row t receives only:
- VIX_t
- VIX values from rows <= t
- fixed method constants

Truth M1/M2 are retained only in an evaluation-side object. A leakage test mutates future truth rows and requires all prior reconstructed rows to remain identical.

## Run

From Windows CMD:

    RUN.cmd

Then open http://127.0.0.1:8790

No third-party package is required.

FINAL SINGLE-RUN MARKER: 2026-10-07T00:xx+08:00
