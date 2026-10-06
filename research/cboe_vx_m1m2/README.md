# CBOE VX M1/M2 — contract archive reconstruction

RESEARCH RUN TRIGGER MARKER: 2026-10-07T00:14+08:00

The previous daily-settlement collector was rejected because the public daily endpoint supplied only a recent rolling window in the runtime. This version uses Cboe-hosted historical per-contract VX CSV archives such as CFE_F18_VX.csv, CFE_G18_VX.csv, and later monthly contracts.

Process:
1. Download every standard monthly VX contract from 2018 through 2026-09.
2. Parse Trade Date + Settle from each contract file.
3. On each date, select the two earliest monthly contracts that actually have a settlement row on that date; weekly VX instruments are not eligible.
4. Compute S = (M2-M1)/M1.
5. Validate the resulting series against the archived observed 2016-2022 M1/M2 dataset before any P&L replay.

No strategy parameters or P&L logic are changed here. A failed overlap gate is STOP.

Evidence classes: OBSERVED contract settlement values; DERIVED deterministic M1/M2 selection; HYPOTHETICAL none.

Cboe's historical pages expose VX price/volume detail and the historical archive contains individual VX month files.