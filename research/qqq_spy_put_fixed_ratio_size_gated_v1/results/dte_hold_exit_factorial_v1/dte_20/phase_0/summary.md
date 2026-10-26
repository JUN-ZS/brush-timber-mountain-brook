# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 285.75 / USD 1,699.29; mean absolute mismatch USD 1,413.54; mean match score 16.90%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 145/51/0 | 73.98% (67.42–79.62%) | USD 271.30 | USD 529.40 | USD 53,174.40 | USD -6,472.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 196/196 | 145/51/0 | 73.98% (67.42–79.62%) | USD 271.30 | USD 529.40 | USD 53,174.40 | USD -6,472.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 196/196 | 140/56/0 | 71.43% (64.74–77.29%) | USD -15.01 | USD 403.90 | USD -2,941.60 | USD -18,851.10 | 0 |
| HOLD_10_SESSIONS | 168/196 | 135/33/0 | 80.36% (73.70–85.66%) | USD 183.19 | USD 810.40 | USD 30,775.20 | USD -16,984.10 | 28 |
| HOLD_10_OR_DTE_LE_7 | 194/196 | 158/36/0 | 81.44% (75.38–86.28%) | USD 391.58 | USD 792.40 | USD 75,965.60 | USD -13,873.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 196/196 | 140/56/0 | 71.43% (64.74–77.29%) | USD -64.76 | USD 403.90 | USD -12,692.60 | USD -18,851.10 | 0 |
| HOLD_15_SESSIONS | 4/196 | 1/3/0 | 25.00% (4.56–69.94%) | USD -11,890.85 | USD -8,388.60 | USD -47,563.40 | USD -32,684.10 | 192 |
| HOLD_15_OR_DTE_LE_7 | 193/196 | 158/35/0 | 81.87% (75.83–86.66%) | USD 300.28 | USD 790.90 | USD 57,953.70 | USD -26,488.10 | 3 |
| HOLD_15_OR_DTE_LE_14 | 196/196 | 140/56/0 | 71.43% (64.74–77.29%) | USD -64.76 | USD 403.90 | USD -12,692.60 | USD -18,851.10 | 0 |
| HOLD_20_SESSIONS | 0/196 | 0/0/0 | — | — | — | — | — | 196 |
| HOLD_20_OR_DTE_LE_7 | 193/196 | 158/35/0 | 81.87% (75.83–86.66%) | USD 300.28 | USD 790.90 | USD 57,953.70 | USD -26,488.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 196/196 | 140/56/0 | 71.43% (64.74–77.29%) | USD -64.76 | USD 403.90 | USD -12,692.60 | USD -18,851.10 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -87.08 | USD 437.48 |
| HOLD_5_OR_DTE_LE_7 | USD -87.08 | USD 437.48 |
| HOLD_5_OR_DTE_LE_14 | USD -31.33 | USD 95.42 |
| HOLD_10_SESSIONS | USD -97.82 | USD 360.11 |
| HOLD_10_OR_DTE_LE_7 | USD -109.96 | USD 580.64 |
| HOLD_10_OR_DTE_LE_14 | USD -25.06 | USD 39.40 |
| HOLD_15_SESSIONS | USD 794.25 | USD -12,606.00 |
| HOLD_15_OR_DTE_LE_7 | USD -99.41 | USD 478.79 |
| HOLD_15_OR_DTE_LE_14 | USD -25.06 | USD 39.40 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -99.41 | USD 478.79 |
| HOLD_20_OR_DTE_LE_14 | USD -25.06 | USD 39.40 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 77.55% | USD 350.40 | USD 68,678.00 | USD -6,393.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 77.04% | USD 341.30 | USD 66,894.40 | USD -6,402.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 75.51% | USD 315.40 | USD 61,818.00 | USD -6,428.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 75.00% | USD 306.30 | USD 60,034.40 | USD -6,437.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 73.98% | USD 280.40 | USD 54,958.00 | USD -6,463.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 73.98% | USD 271.30 | USD 53,174.40 | USD -6,472.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 72.96% | USD 210.40 | USD 41,238.00 | USD -6,533.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 72.45% | USD 201.30 | USD 39,454.40 | USD -6,542.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 196 | 77.55% | USD 350.40 | USD 68,678.00 | USD -6,393.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 196 | 77.04% | USD 341.30 | USD 66,894.40 | USD -6,402.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 196 | 75.51% | USD 315.40 | USD 61,818.00 | USD -6,428.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 196 | 75.00% | USD 306.30 | USD 60,034.40 | USD -6,437.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 196 | 73.98% | USD 280.40 | USD 54,958.00 | USD -6,463.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 196 | 73.98% | USD 271.30 | USD 53,174.40 | USD -6,472.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 196 | 72.96% | USD 210.40 | USD 41,238.00 | USD -6,533.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 196 | 72.45% | USD 201.30 | USD 39,454.40 | USD -6,542.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 196 | 73.47% | USD 64.09 | USD 12,562.00 | USD -18,772.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 196 | 73.47% | USD 54.99 | USD 10,778.40 | USD -18,781.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 196 | 72.45% | USD 29.09 | USD 5,702.00 | USD -18,807.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 196 | 72.45% | USD 19.99 | USD 3,918.40 | USD -18,816.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 196 | 71.43% | USD -5.91 | USD -1,158.00 | USD -18,842.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 196 | 71.43% | USD -15.01 | USD -2,941.60 | USD -18,851.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 196 | 68.88% | USD -75.91 | USD -14,878.00 | USD -18,912.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 196 | 67.86% | USD -85.01 | USD -16,661.60 | USD -18,921.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 168 | 80.95% | USD 262.29 | USD 44,064.00 | USD -16,905.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 168 | 80.95% | USD 253.19 | USD 42,535.20 | USD -16,914.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 168 | 80.95% | USD 227.29 | USD 38,184.00 | USD -16,940.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 168 | 80.95% | USD 218.19 | USD 36,655.20 | USD -16,949.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 168 | 80.36% | USD 192.29 | USD 32,304.00 | USD -16,975.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 168 | 80.36% | USD 183.19 | USD 30,775.20 | USD -16,984.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 168 | 79.17% | USD 122.29 | USD 20,544.00 | USD -17,045.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 168 | 79.17% | USD 113.19 | USD 19,015.20 | USD -17,054.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 81.44% | USD 470.68 | USD 91,311.00 | USD -13,794.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 81.44% | USD 461.58 | USD 89,545.60 | USD -13,803.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 81.44% | USD 435.68 | USD 84,521.00 | USD -13,829.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 81.44% | USD 426.58 | USD 82,755.60 | USD -13,838.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 81.44% | USD 400.68 | USD 77,731.00 | USD -13,864.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 81.44% | USD 391.58 | USD 75,965.60 | USD -13,873.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 80.41% | USD 330.68 | USD 64,151.00 | USD -13,934.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 80.41% | USD 321.58 | USD 62,385.60 | USD -13,943.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 196 | 72.96% | USD 14.34 | USD 2,811.00 | USD -18,772.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 196 | 72.96% | USD 5.24 | USD 1,027.40 | USD -18,781.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 196 | 72.45% | USD -20.66 | USD -4,049.00 | USD -18,807.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 196 | 72.45% | USD -29.76 | USD -5,832.60 | USD -18,816.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 196 | 71.43% | USD -55.66 | USD -10,909.00 | USD -18,842.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 196 | 71.43% | USD -64.76 | USD -12,692.60 | USD -18,851.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 196 | 68.88% | USD -125.66 | USD -24,629.00 | USD -18,912.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 196 | 67.86% | USD -134.76 | USD -26,412.60 | USD -18,921.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 4 | 25.00% | USD -11,811.75 | USD -47,247.00 | USD -32,605.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 4 | 25.00% | USD -11,820.85 | USD -47,283.40 | USD -32,614.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 4 | 25.00% | USD -11,846.75 | USD -47,387.00 | USD -32,640.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 4 | 25.00% | USD -11,855.85 | USD -47,423.40 | USD -32,649.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 4 | 25.00% | USD -11,881.75 | USD -47,527.00 | USD -32,675.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 4 | 25.00% | USD -11,890.85 | USD -47,563.40 | USD -32,684.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 4 | 25.00% | USD -11,951.75 | USD -47,807.00 | USD -32,745.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 4 | 25.00% | USD -11,960.85 | USD -47,843.40 | USD -32,754.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.87% | USD 379.38 | USD 73,220.00 | USD -26,409.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.87% | USD 370.28 | USD 71,463.70 | USD -26,418.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 81.87% | USD 344.38 | USD 66,465.00 | USD -26,444.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 81.87% | USD 335.28 | USD 64,708.70 | USD -26,453.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 81.87% | USD 309.38 | USD 59,710.00 | USD -26,479.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 81.87% | USD 300.28 | USD 57,953.70 | USD -26,488.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 80.83% | USD 239.38 | USD 46,200.00 | USD -26,549.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 80.83% | USD 230.28 | USD 44,443.70 | USD -26,558.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 196 | 72.96% | USD 14.34 | USD 2,811.00 | USD -18,772.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 196 | 72.96% | USD 5.24 | USD 1,027.40 | USD -18,781.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 196 | 72.45% | USD -20.66 | USD -4,049.00 | USD -18,807.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 196 | 72.45% | USD -29.76 | USD -5,832.60 | USD -18,816.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 196 | 71.43% | USD -55.66 | USD -10,909.00 | USD -18,842.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 196 | 71.43% | USD -64.76 | USD -12,692.60 | USD -18,851.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 196 | 68.88% | USD -125.66 | USD -24,629.00 | USD -18,912.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 196 | 67.86% | USD -134.76 | USD -26,412.60 | USD -18,921.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.87% | USD 379.38 | USD 73,220.00 | USD -26,409.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.87% | USD 370.28 | USD 71,463.70 | USD -26,418.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 81.87% | USD 344.38 | USD 66,465.00 | USD -26,444.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 81.87% | USD 335.28 | USD 64,708.70 | USD -26,453.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 81.87% | USD 309.38 | USD 59,710.00 | USD -26,479.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 81.87% | USD 300.28 | USD 57,953.70 | USD -26,488.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 80.83% | USD 239.38 | USD 46,200.00 | USD -26,549.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 80.83% | USD 230.28 | USD 44,443.70 | USD -26,558.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 196 | 72.96% | USD 14.34 | USD 2,811.00 | USD -18,772.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 196 | 72.96% | USD 5.24 | USD 1,027.40 | USD -18,781.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 196 | 72.45% | USD -20.66 | USD -4,049.00 | USD -18,807.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 196 | 72.45% | USD -29.76 | USD -5,832.60 | USD -18,816.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 196 | 71.43% | USD -55.66 | USD -10,909.00 | USD -18,842.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 196 | 71.43% | USD -64.76 | USD -12,692.60 | USD -18,851.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 196 | 68.88% | USD -125.66 | USD -24,629.00 | USD -18,912.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 196 | 67.86% | USD -134.76 | USD -26,412.60 | USD -18,921.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -36.77 | USD -7,206.60 | USD -633.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 73.98% (67.42–79.62%) | USD 271.30 | USD 53,174.40 | USD -6,472.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 17.35% (12.69–23.26%) | USD -528.68 | USD -103,620.60 | USD -4,298.10 |
| HOLD_5_SESSIONS | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -183.84 | USD -36,033.00 | USD -3,168.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -36.77 | USD -7,206.60 | USD -633.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 196/196 (0) | 73.98% (67.42–79.62%) | USD 271.30 | USD 53,174.40 | USD -6,472.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 196/196 (0) | 17.35% (12.69–23.26%) | USD -528.68 | USD -103,620.60 | USD -4,298.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -183.84 | USD -36,033.00 | USD -3,168.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 196/196 (0) | 27.55% (21.77–34.19%) | USD -38.02 | USD -7,452.60 | USD -959.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 196/196 (0) | 71.43% (64.74–77.29%) | USD -15.01 | USD -2,941.60 | USD -18,851.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 196/196 (0) | 22.96% (17.62–29.33%) | USD -251.16 | USD -49,226.60 | USD -3,478.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 196/196 (0) | 27.55% (21.77–34.19%) | USD -190.12 | USD -37,263.00 | USD -4,798.00 |
| HOLD_10_SESSIONS | 1 : 1 | 168/196 (28) | 33.33% (26.65–40.76%) | USD -60.40 | USD -10,147.80 | USD -1,458.60 |
| HOLD_10_SESSIONS | 1 : 6 | 168/196 (28) | 80.36% (73.70–85.66%) | USD 183.19 | USD 30,775.20 | USD -16,984.10 |
| HOLD_10_SESSIONS | 6 : 1 | 168/196 (28) | 17.86% (12.80–24.35%) | USD -606.01 | USD -101,809.80 | USD -4,974.10 |
| HOLD_10_SESSIONS | 5 : 5 | 168/196 (28) | 33.33% (26.65–40.76%) | USD -302.02 | USD -50,739.00 | USD -7,293.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 194/196 (2) | 34.54% (28.20–41.47%) | USD -35.79 | USD -6,943.40 | USD -1,458.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 194/196 (2) | 81.44% (75.38–86.28%) | USD 391.58 | USD 75,965.60 | USD -13,873.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 194/196 (2) | 15.98% (11.49–21.79%) | USD -642.11 | USD -124,569.40 | USD -4,620.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 194/196 (2) | 34.54% (28.20–41.47%) | USD -178.95 | USD -34,717.00 | USD -7,293.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -41.09 | USD -8,053.60 | USD -959.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 196/196 (0) | 71.43% (64.74–77.29%) | USD -64.76 | USD -12,692.60 | USD -18,851.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 196/196 (0) | 23.98% (18.54–30.42%) | USD -222.87 | USD -43,682.60 | USD -3,478.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -205.45 | USD -40,268.00 | USD -4,798.00 |
| HOLD_15_SESSIONS | 1 : 1 | 4/196 (192) | 0.00% (0.00–48.99%) | USD -1,329.35 | USD -5,317.40 | USD -3,452.60 |
| HOLD_15_SESSIONS | 1 : 6 | 4/196 (192) | 25.00% (4.56–69.94%) | USD -11,890.85 | USD -47,563.40 | USD -32,684.10 |
| HOLD_15_SESSIONS | 6 : 1 | 4/196 (192) | 50.00% (15.00–85.00%) | USD 2,585.40 | USD 10,341.60 | USD -2,252.10 |
| HOLD_15_SESSIONS | 5 : 5 | 4/196 (192) | 0.00% (0.00–48.99%) | USD -6,646.75 | USD -26,587.00 | USD -17,263.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 193/196 (3) | 34.72% (28.36–41.67%) | USD -42.21 | USD -8,146.80 | USD -2,761.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 193/196 (3) | 81.87% (75.83–86.66%) | USD 300.28 | USD 57,953.70 | USD -26,488.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 193/196 (3) | 17.10% (12.44–23.04%) | USD -595.76 | USD -114,981.30 | USD -4,620.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 193/196 (3) | 34.72% (28.36–41.67%) | USD -211.06 | USD -40,734.00 | USD -13,808.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -41.09 | USD -8,053.60 | USD -959.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 196/196 (0) | 71.43% (64.74–77.29%) | USD -64.76 | USD -12,692.60 | USD -18,851.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 196/196 (0) | 23.98% (18.54–30.42%) | USD -222.87 | USD -43,682.60 | USD -3,478.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -205.45 | USD -40,268.00 | USD -4,798.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/196 (196) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 193/196 (3) | 34.72% (28.36–41.67%) | USD -42.21 | USD -8,146.80 | USD -2,761.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 193/196 (3) | 81.87% (75.83–86.66%) | USD 300.28 | USD 57,953.70 | USD -26,488.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 193/196 (3) | 17.10% (12.44–23.04%) | USD -595.76 | USD -114,981.30 | USD -4,620.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 193/196 (3) | 34.72% (28.36–41.67%) | USD -211.06 | USD -40,734.00 | USD -13,808.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -41.09 | USD -8,053.60 | USD -959.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 196/196 (0) | 71.43% (64.74–77.29%) | USD -64.76 | USD -12,692.60 | USD -18,851.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 196/196 (0) | 23.98% (18.54–30.42%) | USD -222.87 | USD -43,682.60 | USD -3,478.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -205.45 | USD -40,268.00 | USD -4,798.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -208,677.77 | USD -337,894.55 |
| -75% | 0/196 | 0.00% | USD -154,770.06 | USD -250,973.80 |
| -50% | 0/196 | 0.00% | USD -100,862.36 | USD -165,169.05 |
| -40% | 0/196 | 0.00% | USD -79,299.28 | USD -130,847.15 |
| -30% | 0/196 | 0.00% | USD -57,736.19 | USD -96,525.25 |
| -25% | 0/196 | 0.00% | USD -46,954.65 | USD -79,364.30 |
| -20% | 0/196 | 0.00% | USD -36,173.11 | USD -62,203.35 |
| -15% | 1/196 | 0.51% | USD -25,391.63 | USD -45,042.40 |
| -10% | 1/196 | 0.51% | USD -14,645.63 | USD -27,881.45 |
| -5% | 21/196 | 10.71% | USD -3,973.56 | USD -11,079.05 |
| 0% | 196/196 | 100.00% | USD 1,364.21 | USD 275.45 |
| 5% | 196/196 | 100.00% | USD 1,373.99 | USD 275.45 |
| 10% | 196/196 | 100.00% | USD 1,373.99 | USD 275.45 |
| 20% | 196/196 | 100.00% | USD 1,373.99 | USD 275.45 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short put can dominate downside even when QQQ long put appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.