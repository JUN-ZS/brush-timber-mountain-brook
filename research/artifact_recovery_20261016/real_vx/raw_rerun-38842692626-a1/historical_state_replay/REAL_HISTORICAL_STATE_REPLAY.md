# REAL HISTORICAL STATE REPLAY

Status: **OBSERVED_REPLAY** — direct replay using observed external M1/M2. Not reconstruction. Not P&L replay.

## Data contract
- M1/M2/VIX rows: **1540**
- Coverage: **2016-03-01 → 2022-04-08**
- Archived QQQ/VXX overlap: **1059** rows
- Inputs: observed M1/M2/VIX + aligned archived QQQ/VXX spot series
- Policy: recovered archive state/action functions in engine.js

## Direct term structure
- Mean TS: **6.62%**
- Mean ΔTS: **0.00%**
- Backwardation rows (TS < 0): **232 / 1540 (15.06%)**
- Contango/non-negative rows: **1308 / 1540 (84.94%)**
- Backwardation episodes: **44**
- Longest backwardation run: **52 rows**

## Archive state replay

| State | Rows | Share |
|---|---:|---:|
| Decay-Optimal | 1230 | 79.87% |
| Normal | 174 | 11.30% |
| Shock | 136 | 8.83% |

## Archive action replay

| Action | All rows | Overlap rows |
|---|---:|---:|
| PAIR | 1265 | 803 |
| QQQ_CC_ONLY | 275 | 256 |

## VXX carry
- Carry ON among QQQ/VXX overlap: **803**
- Carry OFF among QQQ/VXX overlap: **256**
- Carry episodes in overlap: **74**
- Longest carry run: **74 rows**

## Change-of-state signal
- Archive state transitions on overlap: **218**
- Archive action transitions on overlap: **146**

## Forensic interpretation
1. **Observed M1/M2 is sufficient to replay the term-dependent archive gate directly.** No VIX→M2 proxy is needed for this historical window.
2. The replay gives exact historical dates for the recovered policy's Shock / High-Spread / Decay-Optimal / Normal classifications and the VXX carry gate.
3. This does **not** prove the historical 12.5% CAGR. Full P&L parity still requires the original option contract identities, expiries, entry/exit prices, roll logic, execution and friction contract.
4. The next simulation, if pursued, must be a separate **EMPIRICAL_TS_SIM_V1** and must remain explicitly DERIVED/HYPOTHETICAL.

Output CSV: research/data/real_historical_state_replay_2018_2022.csv
