# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 374.08 / USD 2,187.94; mean absolute mismatch USD 1,813.86; mean match score 16.93%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/195 | 137/57/0 | 70.62% (63.86–76.58%) | USD 162.64 | USD 444.40 | USD 31,551.60 | USD -10,535.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 194/195 | 137/57/0 | 70.62% (63.86–76.58%) | USD 162.64 | USD 444.40 | USD 31,551.60 | USD -10,535.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 137/57/0 | 70.62% (63.86–76.58%) | USD 162.64 | USD 444.40 | USD 31,551.60 | USD -10,535.10 | 1 |
| HOLD_10_SESSIONS | 194/195 | 150/44/0 | 77.32% (70.93–82.65%) | USD 57.50 | USD 759.40 | USD 11,154.60 | USD -20,317.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 194/195 | 150/44/0 | 77.32% (70.93–82.65%) | USD 57.50 | USD 759.40 | USD 11,154.60 | USD -20,317.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 194/195 | 151/43/0 | 77.84% (71.48–83.11%) | USD 21.96 | USD 755.90 | USD 4,259.60 | USD -20,317.10 | 1 |
| HOLD_15_SESSIONS | 181/195 | 150/31/0 | 82.87% (76.72–87.66%) | USD 414.45 | USD 1,110.90 | USD 75,015.90 | USD -21,205.10 | 14 |
| HOLD_15_OR_DTE_LE_7 | 188/195 | 157/31/0 | 83.51% (77.55–88.13%) | USD 327.24 | USD 1,093.90 | USD 61,520.20 | USD -28,877.10 | 7 |
| HOLD_15_OR_DTE_LE_14 | 194/195 | 156/38/0 | 80.41% (74.26–85.38%) | USD 74.14 | USD 838.90 | USD 14,383.60 | USD -20,317.10 | 1 |
| HOLD_20_SESSIONS | 38/195 | 28/10/0 | 73.68% (57.99–85.03%) | USD -381.07 | USD 1,015.90 | USD -14,480.80 | USD -24,600.10 | 157 |
| HOLD_20_OR_DTE_LE_7 | 187/195 | 158/29/0 | 84.49% (78.62–88.98%) | USD 429.71 | USD 1,152.90 | USD 80,355.30 | USD -28,877.10 | 8 |
| HOLD_20_OR_DTE_LE_14 | 194/195 | 156/38/0 | 80.41% (74.26–85.38%) | USD 74.14 | USD 838.90 | USD 14,383.60 | USD -20,317.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -67.29 | USD 309.03 |
| HOLD_5_OR_DTE_LE_7 | USD -67.29 | USD 309.03 |
| HOLD_5_OR_DTE_LE_14 | USD -67.29 | USD 309.03 |
| HOLD_10_SESSIONS | USD -67.43 | USD 204.03 |
| HOLD_10_OR_DTE_LE_7 | USD -67.43 | USD 204.03 |
| HOLD_10_OR_DTE_LE_14 | USD -60.42 | USD 161.47 |
| HOLD_15_SESSIONS | USD -139.03 | USD 632.59 |
| HOLD_15_OR_DTE_LE_7 | USD -131.18 | USD 537.51 |
| HOLD_15_OR_DTE_LE_14 | USD -69.13 | USD 222.37 |
| HOLD_20_SESSIONS | USD 45.24 | USD -347.21 |
| HOLD_20_OR_DTE_LE_7 | USD -149.43 | USD 658.24 |
| HOLD_20_OR_DTE_LE_14 | USD -69.13 | USD 222.37 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 73.20% | USD 241.74 | USD 46,897.00 | USD -10,456.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 72.68% | USD 232.64 | USD 45,131.60 | USD -10,465.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 72.16% | USD 206.74 | USD 40,107.00 | USD -10,491.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 72.16% | USD 197.64 | USD 38,341.60 | USD -10,500.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 70.62% | USD 171.74 | USD 33,317.00 | USD -10,526.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 70.62% | USD 162.64 | USD 31,551.60 | USD -10,535.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 70.10% | USD 101.74 | USD 19,737.00 | USD -10,596.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 70.10% | USD 92.64 | USD 17,971.60 | USD -10,605.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 73.20% | USD 241.74 | USD 46,897.00 | USD -10,456.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 72.68% | USD 232.64 | USD 45,131.60 | USD -10,465.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 72.16% | USD 206.74 | USD 40,107.00 | USD -10,491.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 72.16% | USD 197.64 | USD 38,341.60 | USD -10,500.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 70.62% | USD 171.74 | USD 33,317.00 | USD -10,526.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 70.62% | USD 162.64 | USD 31,551.60 | USD -10,535.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 70.10% | USD 101.74 | USD 19,737.00 | USD -10,596.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 70.10% | USD 92.64 | USD 17,971.60 | USD -10,605.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 73.20% | USD 241.74 | USD 46,897.00 | USD -10,456.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 72.68% | USD 232.64 | USD 45,131.60 | USD -10,465.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 72.16% | USD 206.74 | USD 40,107.00 | USD -10,491.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 72.16% | USD 197.64 | USD 38,341.60 | USD -10,500.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 70.62% | USD 171.74 | USD 33,317.00 | USD -10,526.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 70.62% | USD 162.64 | USD 31,551.60 | USD -10,535.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 70.10% | USD 101.74 | USD 19,737.00 | USD -10,596.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.10% | USD 92.64 | USD 17,971.60 | USD -10,605.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 194 | 77.84% | USD 136.60 | USD 26,500.00 | USD -20,238.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 194 | 77.84% | USD 127.50 | USD 24,734.60 | USD -20,247.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 194 | 77.32% | USD 101.60 | USD 19,710.00 | USD -20,273.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 194 | 77.32% | USD 92.50 | USD 17,944.60 | USD -20,282.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 194 | 77.32% | USD 66.60 | USD 12,920.00 | USD -20,308.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 194 | 77.32% | USD 57.50 | USD 11,154.60 | USD -20,317.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 194 | 76.29% | USD -3.40 | USD -660.00 | USD -20,378.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 194 | 76.29% | USD -12.50 | USD -2,425.40 | USD -20,387.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 77.84% | USD 136.60 | USD 26,500.00 | USD -20,238.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 77.84% | USD 127.50 | USD 24,734.60 | USD -20,247.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 77.32% | USD 101.60 | USD 19,710.00 | USD -20,273.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 77.32% | USD 92.50 | USD 17,944.60 | USD -20,282.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 77.32% | USD 66.60 | USD 12,920.00 | USD -20,308.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 77.32% | USD 57.50 | USD 11,154.60 | USD -20,317.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 76.29% | USD -3.40 | USD -660.00 | USD -20,378.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 76.29% | USD -12.50 | USD -2,425.40 | USD -20,387.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 78.35% | USD 101.06 | USD 19,605.00 | USD -20,238.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 78.35% | USD 91.96 | USD 17,839.60 | USD -20,247.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 77.84% | USD 66.06 | USD 12,815.00 | USD -20,273.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 77.84% | USD 56.96 | USD 11,049.60 | USD -20,282.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 77.84% | USD 31.06 | USD 6,025.00 | USD -20,308.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 77.84% | USD 21.96 | USD 4,259.60 | USD -20,317.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 76.80% | USD -38.94 | USD -7,555.00 | USD -20,378.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 76.80% | USD -48.04 | USD -9,320.40 | USD -20,387.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 181 | 83.43% | USD 493.55 | USD 89,333.00 | USD -21,126.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 181 | 82.87% | USD 484.45 | USD 87,685.90 | USD -21,135.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 181 | 82.87% | USD 458.55 | USD 82,998.00 | USD -21,161.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 181 | 82.87% | USD 449.45 | USD 81,350.90 | USD -21,170.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 181 | 82.87% | USD 423.55 | USD 76,663.00 | USD -21,196.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 181 | 82.87% | USD 414.45 | USD 75,015.90 | USD -21,205.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 181 | 82.32% | USD 353.55 | USD 63,993.00 | USD -21,266.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 181 | 82.32% | USD 344.45 | USD 62,345.90 | USD -21,275.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 188 | 84.04% | USD 406.34 | USD 76,391.00 | USD -28,798.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 188 | 83.51% | USD 397.24 | USD 74,680.20 | USD -28,807.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 188 | 83.51% | USD 371.34 | USD 69,811.00 | USD -28,833.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 188 | 83.51% | USD 362.24 | USD 68,100.20 | USD -28,842.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 188 | 83.51% | USD 336.34 | USD 63,231.00 | USD -28,868.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 188 | 83.51% | USD 327.24 | USD 61,520.20 | USD -28,877.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 188 | 82.98% | USD 266.34 | USD 50,071.00 | USD -28,938.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 188 | 82.98% | USD 257.24 | USD 48,360.20 | USD -28,947.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 81.44% | USD 153.24 | USD 29,729.00 | USD -20,238.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 81.44% | USD 144.14 | USD 27,963.60 | USD -20,247.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 80.93% | USD 118.24 | USD 22,939.00 | USD -20,273.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 80.41% | USD 109.14 | USD 21,173.60 | USD -20,282.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 80.41% | USD 83.24 | USD 16,149.00 | USD -20,308.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 80.41% | USD 74.14 | USD 14,383.60 | USD -20,317.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 79.90% | USD 13.24 | USD 2,569.00 | USD -20,378.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 79.90% | USD 4.14 | USD 803.60 | USD -20,387.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 38 | 73.68% | USD -301.97 | USD -11,475.00 | USD -24,521.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 38 | 73.68% | USD -311.07 | USD -11,820.80 | USD -24,530.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 38 | 73.68% | USD -336.97 | USD -12,805.00 | USD -24,556.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 38 | 73.68% | USD -346.07 | USD -13,150.80 | USD -24,565.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 38 | 73.68% | USD -371.97 | USD -14,135.00 | USD -24,591.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 38 | 73.68% | USD -381.07 | USD -14,480.80 | USD -24,600.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 38 | 73.68% | USD -441.97 | USD -16,795.00 | USD -24,661.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 38 | 73.68% | USD -451.07 | USD -17,140.80 | USD -24,670.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 187 | 85.03% | USD 508.81 | USD 95,147.00 | USD -28,798.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 187 | 84.49% | USD 499.71 | USD 93,445.30 | USD -28,807.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 187 | 84.49% | USD 473.81 | USD 88,602.00 | USD -28,833.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 187 | 84.49% | USD 464.71 | USD 86,900.30 | USD -28,842.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 187 | 84.49% | USD 438.81 | USD 82,057.00 | USD -28,868.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 187 | 84.49% | USD 429.71 | USD 80,355.30 | USD -28,877.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 187 | 83.96% | USD 368.81 | USD 68,967.00 | USD -28,938.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 187 | 83.96% | USD 359.71 | USD 67,265.30 | USD -28,947.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 81.44% | USD 153.24 | USD 29,729.00 | USD -20,238.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 81.44% | USD 144.14 | USD 27,963.60 | USD -20,247.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 80.93% | USD 118.24 | USD 22,939.00 | USD -20,273.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 80.41% | USD 109.14 | USD 21,173.60 | USD -20,282.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 80.41% | USD 83.24 | USD 16,149.00 | USD -20,308.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 80.41% | USD 74.14 | USD 14,383.60 | USD -20,317.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 79.90% | USD 13.24 | USD 2,569.00 | USD -20,378.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 79.90% | USD 4.14 | USD 803.60 | USD -20,387.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -38.39 | USD -7,447.40 | USD -512.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/195 (1) | 70.62% (63.86–76.58%) | USD 162.64 | USD 31,551.60 | USD -10,535.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/195 (1) | 23.20% (17.81–29.62%) | USD -431.36 | USD -83,683.40 | USD -6,107.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -191.94 | USD -37,237.00 | USD -2,563.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -38.39 | USD -7,447.40 | USD -512.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/195 (1) | 70.62% (63.86–76.58%) | USD 162.64 | USD 31,551.60 | USD -10,535.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/195 (1) | 23.20% (17.81–29.62%) | USD -431.36 | USD -83,683.40 | USD -6,107.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -191.94 | USD -37,237.00 | USD -2,563.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -38.39 | USD -7,447.40 | USD -512.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 70.62% (63.86–76.58%) | USD 162.64 | USD 31,551.60 | USD -10,535.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 23.20% (17.81–29.62%) | USD -431.36 | USD -83,683.40 | USD -6,107.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -191.94 | USD -37,237.00 | USD -2,563.00 |
| HOLD_10_SESSIONS | 1 : 1 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -56.03 | USD -10,869.40 | USD -1,312.60 |
| HOLD_10_SESSIONS | 1 : 6 | 194/195 (1) | 77.32% (70.93–82.65%) | USD 57.50 | USD 11,154.60 | USD -20,317.10 |
| HOLD_10_SESSIONS | 6 : 1 | 194/195 (1) | 20.62% (15.52–26.86%) | USD -449.69 | USD -87,240.40 | USD -6,888.10 |
| HOLD_10_SESSIONS | 5 : 5 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -280.14 | USD -54,347.00 | USD -6,563.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -56.03 | USD -10,869.40 | USD -1,312.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 194/195 (1) | 77.32% (70.93–82.65%) | USD 57.50 | USD 11,154.60 | USD -20,317.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 194/195 (1) | 20.62% (15.52–26.86%) | USD -449.69 | USD -87,240.40 | USD -6,888.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -280.14 | USD -54,347.00 | USD -6,563.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 33.51% (27.24–40.41%) | USD -56.11 | USD -10,884.40 | USD -1,510.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 77.84% (71.48–83.11%) | USD 21.96 | USD 4,259.60 | USD -20,317.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 20.10% (15.07–26.30%) | USD -414.69 | USD -80,450.40 | USD -6,744.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 33.51% (27.24–40.41%) | USD -280.53 | USD -54,422.00 | USD -7,553.00 |
| HOLD_15_SESSIONS | 1 : 1 | 181/195 (14) | 33.70% (27.22–40.86%) | USD -56.20 | USD -10,172.60 | USD -2,232.60 |
| HOLD_15_SESSIONS | 1 : 6 | 181/195 (14) | 82.87% (76.72–87.66%) | USD 414.45 | USD 75,015.90 | USD -21,205.10 |
| HOLD_15_SESSIONS | 6 : 1 | 181/195 (14) | 15.47% (10.93–21.45%) | USD -807.87 | USD -146,224.10 | USD -8,701.10 |
| HOLD_15_SESSIONS | 5 : 5 | 181/195 (14) | 33.70% (27.22–40.86%) | USD -281.01 | USD -50,863.00 | USD -11,163.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 188/195 (7) | 34.04% (27.65–41.08%) | USD -64.19 | USD -12,067.80 | USD -3,255.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 188/195 (7) | 83.51% (77.55–88.13%) | USD 327.24 | USD 61,520.20 | USD -28,877.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 188/195 (7) | 15.43% (10.96–21.28%) | USD -776.57 | USD -145,994.80 | USD -8,701.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 188/195 (7) | 34.04% (27.65–41.08%) | USD -320.95 | USD -60,339.00 | USD -16,278.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -54.67 | USD -10,605.40 | USD -1,510.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 80.41% (74.26–85.38%) | USD 74.14 | USD 14,383.60 | USD -20,317.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 20.62% (15.52–26.86%) | USD -456.81 | USD -88,621.40 | USD -6,744.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -273.34 | USD -53,027.00 | USD -7,553.00 |
| HOLD_20_SESSIONS | 1 : 1 | 38/195 (157) | 31.58% (19.08–47.46%) | USD -35.23 | USD -1,338.80 | USD -453.60 |
| HOLD_20_SESSIONS | 1 : 6 | 38/195 (157) | 73.68% (57.99–85.03%) | USD -381.07 | USD -14,480.80 | USD -24,600.10 |
| HOLD_20_SESSIONS | 6 : 1 | 38/195 (157) | 23.68% (12.99–39.21%) | USD 134.45 | USD 5,109.20 | USD -4,309.10 |
| HOLD_20_SESSIONS | 5 : 5 | 38/195 (157) | 31.58% (19.08–47.46%) | USD -176.16 | USD -6,694.00 | USD -2,268.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 187/195 (8) | 34.76% (28.30–41.83%) | USD -62.32 | USD -11,654.20 | USD -3,255.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 187/195 (8) | 84.49% (78.62–88.98%) | USD 429.71 | USD 80,355.30 | USD -28,877.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 187/195 (8) | 16.04% (11.47–21.98%) | USD -865.96 | USD -161,934.70 | USD -8,701.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 187/195 (8) | 34.76% (28.30–41.83%) | USD -311.61 | USD -58,271.00 | USD -16,278.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -54.67 | USD -10,605.40 | USD -1,510.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 80.41% (74.26–85.38%) | USD 74.14 | USD 14,383.60 | USD -20,317.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 20.62% (15.52–26.86%) | USD -456.81 | USD -88,621.40 | USD -6,744.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 32.99% (26.76–39.88%) | USD -273.34 | USD -53,027.00 | USD -7,553.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/195 | 0.00% | USD -207,406.29 | USD -337,570.55 |
| -75% | 0/195 | 0.00% | USD -153,395.70 | USD -250,354.05 |
| -50% | 0/195 | 0.00% | USD -99,385.11 | USD -163,137.55 |
| -40% | 0/195 | 0.00% | USD -77,780.88 | USD -128,250.95 |
| -30% | 0/195 | 0.00% | USD -56,176.64 | USD -93,364.35 |
| -25% | 0/195 | 0.00% | USD -45,374.52 | USD -75,921.05 |
| -20% | 0/195 | 0.00% | USD -34,572.41 | USD -58,506.95 |
| -15% | 1/195 | 0.51% | USD -23,770.29 | USD -41,733.10 |
| -10% | 3/195 | 1.54% | USD -13,006.47 | USD -24,959.25 |
| -5% | 44/195 | 22.56% | USD -2,436.40 | USD -9,693.25 |
| 0% | 195/195 | 100.00% | USD 1,742.17 | USD 485.45 |
| 5% | 195/195 | 100.00% | USD 1,774.31 | USD 485.45 |
| 10% | 195/195 | 100.00% | USD 1,774.31 | USD 485.45 |
| 20% | 195/195 | 100.00% | USD 1,774.31 | USD 485.45 |

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