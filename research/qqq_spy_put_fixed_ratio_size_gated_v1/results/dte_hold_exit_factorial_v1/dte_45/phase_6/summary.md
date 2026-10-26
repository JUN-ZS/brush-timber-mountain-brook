# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 427.52 / USD 2,530.22; mean absolute mismatch USD 2,102.70; mean match score 16.73%.
- Actual selected contract ratios: {'1:6': 172}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 172; entered cohorts: 172; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 171/172 | 123/48/0 | 71.93% (64.77–78.13%) | USD 18.87 | USD 445.90 | USD 3,226.90 | USD -17,756.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 171/172 | 123/48/0 | 71.93% (64.77–78.13%) | USD 18.87 | USD 445.90 | USD 3,226.90 | USD -17,756.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 171/172 | 123/48/0 | 71.93% (64.77–78.13%) | USD 18.87 | USD 445.90 | USD 3,226.90 | USD -17,756.10 | 1 |
| HOLD_10_SESSIONS | 170/172 | 132/38/0 | 77.65% (70.81–83.26%) | USD 205.75 | USD 729.40 | USD 34,977.00 | USD -27,025.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 170/172 | 132/38/0 | 77.65% (70.81–83.26%) | USD 205.75 | USD 729.40 | USD 34,977.00 | USD -27,025.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 170/172 | 132/38/0 | 77.65% (70.81–83.26%) | USD 205.75 | USD 729.40 | USD 34,977.00 | USD -27,025.10 | 2 |
| HOLD_15_SESSIONS | 170/172 | 129/41/0 | 75.88% (68.93–81.70%) | USD 288.25 | USD 959.40 | USD 49,002.00 | USD -45,670.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 170/172 | 129/41/0 | 75.88% (68.93–81.70%) | USD 288.25 | USD 959.40 | USD 49,002.00 | USD -45,670.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 170/172 | 129/41/0 | 75.88% (68.93–81.70%) | USD 288.25 | USD 959.40 | USD 49,002.00 | USD -45,670.10 | 2 |
| HOLD_20_SESSIONS | 169/172 | 139/30/0 | 82.25% (75.79–87.27%) | USD 403.07 | USD 1,315.90 | USD 68,118.10 | USD -44,015.10 | 3 |
| HOLD_20_OR_DTE_LE_7 | 169/172 | 139/30/0 | 82.25% (75.79–87.27%) | USD 403.07 | USD 1,315.90 | USD 68,118.10 | USD -44,015.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 170/172 | 138/32/0 | 81.18% (74.64–86.34%) | USD 311.72 | USD 1,263.40 | USD 52,993.00 | USD -44,015.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -41.82 | USD 139.79 |
| HOLD_5_OR_DTE_LE_7 | USD -41.82 | USD 139.79 |
| HOLD_5_OR_DTE_LE_14 | USD -41.82 | USD 139.79 |
| HOLD_10_SESSIONS | USD -93.89 | USD 378.74 |
| HOLD_10_OR_DTE_LE_7 | USD -93.89 | USD 378.74 |
| HOLD_10_OR_DTE_LE_14 | USD -93.89 | USD 378.74 |
| HOLD_15_SESSIONS | USD -103.51 | USD 470.86 |
| HOLD_15_OR_DTE_LE_7 | USD -103.51 | USD 470.86 |
| HOLD_15_OR_DTE_LE_14 | USD -103.51 | USD 470.86 |
| HOLD_20_SESSIONS | USD -143.96 | USD 626.13 |
| HOLD_20_OR_DTE_LE_7 | USD -143.96 | USD 626.13 |
| HOLD_20_OR_DTE_LE_14 | USD -126.62 | USD 517.45 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 171 | 74.85% | USD 97.97 | USD 16,753.00 | USD -17,677.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 171 | 74.85% | USD 88.87 | USD 15,196.90 | USD -17,686.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 171 | 74.27% | USD 62.97 | USD 10,768.00 | USD -17,712.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 171 | 74.27% | USD 53.87 | USD 9,211.90 | USD -17,721.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 171 | 72.51% | USD 27.97 | USD 4,783.00 | USD -17,747.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 171 | 71.93% | USD 18.87 | USD 3,226.90 | USD -17,756.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 171 | 69.59% | USD -42.03 | USD -7,187.00 | USD -17,817.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 171 | 69.01% | USD -51.13 | USD -8,743.10 | USD -17,826.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 171 | 74.85% | USD 97.97 | USD 16,753.00 | USD -17,677.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 171 | 74.85% | USD 88.87 | USD 15,196.90 | USD -17,686.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 171 | 74.27% | USD 62.97 | USD 10,768.00 | USD -17,712.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 171 | 74.27% | USD 53.87 | USD 9,211.90 | USD -17,721.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 171 | 72.51% | USD 27.97 | USD 4,783.00 | USD -17,747.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 171 | 71.93% | USD 18.87 | USD 3,226.90 | USD -17,756.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 171 | 69.59% | USD -42.03 | USD -7,187.00 | USD -17,817.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 171 | 69.01% | USD -51.13 | USD -8,743.10 | USD -17,826.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 171 | 74.85% | USD 97.97 | USD 16,753.00 | USD -17,677.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 171 | 74.85% | USD 88.87 | USD 15,196.90 | USD -17,686.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 171 | 74.27% | USD 62.97 | USD 10,768.00 | USD -17,712.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 171 | 74.27% | USD 53.87 | USD 9,211.90 | USD -17,721.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 171 | 72.51% | USD 27.97 | USD 4,783.00 | USD -17,747.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 171 | 71.93% | USD 18.87 | USD 3,226.90 | USD -17,756.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 171 | 69.59% | USD -42.03 | USD -7,187.00 | USD -17,817.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 171 | 69.01% | USD -51.13 | USD -8,743.10 | USD -17,826.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 170 | 79.41% | USD 284.85 | USD 48,424.00 | USD -26,946.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 170 | 79.41% | USD 275.75 | USD 46,877.00 | USD -26,955.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 170 | 77.65% | USD 249.85 | USD 42,474.00 | USD -26,981.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 170 | 77.65% | USD 240.75 | USD 40,927.00 | USD -26,990.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 170 | 77.65% | USD 214.85 | USD 36,524.00 | USD -27,016.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 170 | 77.65% | USD 205.75 | USD 34,977.00 | USD -27,025.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 170 | 77.06% | USD 144.85 | USD 24,624.00 | USD -27,086.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 170 | 76.47% | USD 135.75 | USD 23,077.00 | USD -27,095.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 79.41% | USD 284.85 | USD 48,424.00 | USD -26,946.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 79.41% | USD 275.75 | USD 46,877.00 | USD -26,955.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 77.65% | USD 249.85 | USD 42,474.00 | USD -26,981.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 77.65% | USD 240.75 | USD 40,927.00 | USD -26,990.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 77.65% | USD 214.85 | USD 36,524.00 | USD -27,016.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 77.65% | USD 205.75 | USD 34,977.00 | USD -27,025.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 77.06% | USD 144.85 | USD 24,624.00 | USD -27,086.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 76.47% | USD 135.75 | USD 23,077.00 | USD -27,095.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 170 | 79.41% | USD 284.85 | USD 48,424.00 | USD -26,946.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 170 | 79.41% | USD 275.75 | USD 46,877.00 | USD -26,955.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 170 | 77.65% | USD 249.85 | USD 42,474.00 | USD -26,981.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 170 | 77.65% | USD 240.75 | USD 40,927.00 | USD -26,990.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 170 | 77.65% | USD 214.85 | USD 36,524.00 | USD -27,016.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 170 | 77.65% | USD 205.75 | USD 34,977.00 | USD -27,025.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 170 | 77.06% | USD 144.85 | USD 24,624.00 | USD -27,086.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 170 | 76.47% | USD 135.75 | USD 23,077.00 | USD -27,095.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 170 | 76.47% | USD 367.35 | USD 62,449.00 | USD -45,591.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 170 | 75.88% | USD 358.25 | USD 60,902.00 | USD -45,600.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 170 | 75.88% | USD 332.35 | USD 56,499.00 | USD -45,626.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 170 | 75.88% | USD 323.25 | USD 54,952.00 | USD -45,635.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 170 | 75.88% | USD 297.35 | USD 50,549.00 | USD -45,661.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 170 | 75.88% | USD 288.25 | USD 49,002.00 | USD -45,670.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 170 | 75.88% | USD 227.35 | USD 38,649.00 | USD -45,731.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 170 | 75.88% | USD 218.25 | USD 37,102.00 | USD -45,740.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 76.47% | USD 367.35 | USD 62,449.00 | USD -45,591.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 75.88% | USD 358.25 | USD 60,902.00 | USD -45,600.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 75.88% | USD 332.35 | USD 56,499.00 | USD -45,626.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 75.88% | USD 323.25 | USD 54,952.00 | USD -45,635.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 75.88% | USD 297.35 | USD 50,549.00 | USD -45,661.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 75.88% | USD 288.25 | USD 49,002.00 | USD -45,670.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 75.88% | USD 227.35 | USD 38,649.00 | USD -45,731.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 75.88% | USD 218.25 | USD 37,102.00 | USD -45,740.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 170 | 76.47% | USD 367.35 | USD 62,449.00 | USD -45,591.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 170 | 75.88% | USD 358.25 | USD 60,902.00 | USD -45,600.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 170 | 75.88% | USD 332.35 | USD 56,499.00 | USD -45,626.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 170 | 75.88% | USD 323.25 | USD 54,952.00 | USD -45,635.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 170 | 75.88% | USD 297.35 | USD 50,549.00 | USD -45,661.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 170 | 75.88% | USD 288.25 | USD 49,002.00 | USD -45,670.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 170 | 75.88% | USD 227.35 | USD 38,649.00 | USD -45,731.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 170 | 75.88% | USD 218.25 | USD 37,102.00 | USD -45,740.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 169 | 82.84% | USD 482.17 | USD 81,486.00 | USD -43,936.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 169 | 82.84% | USD 473.07 | USD 79,948.10 | USD -43,945.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 169 | 82.84% | USD 447.17 | USD 75,571.00 | USD -43,971.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 169 | 82.84% | USD 438.07 | USD 74,033.10 | USD -43,980.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 169 | 82.25% | USD 412.17 | USD 69,656.00 | USD -44,006.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 169 | 82.25% | USD 403.07 | USD 68,118.10 | USD -44,015.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 169 | 81.66% | USD 342.17 | USD 57,826.00 | USD -44,076.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 169 | 81.66% | USD 333.07 | USD 56,288.10 | USD -44,085.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 169 | 82.84% | USD 482.17 | USD 81,486.00 | USD -43,936.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 169 | 82.84% | USD 473.07 | USD 79,948.10 | USD -43,945.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 169 | 82.84% | USD 447.17 | USD 75,571.00 | USD -43,971.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 169 | 82.84% | USD 438.07 | USD 74,033.10 | USD -43,980.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 169 | 82.25% | USD 412.17 | USD 69,656.00 | USD -44,006.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 169 | 82.25% | USD 403.07 | USD 68,118.10 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 169 | 81.66% | USD 342.17 | USD 57,826.00 | USD -44,076.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 169 | 81.66% | USD 333.07 | USD 56,288.10 | USD -44,085.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 170 | 81.18% | USD 390.82 | USD 66,440.00 | USD -43,936.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 170 | 81.18% | USD 381.72 | USD 64,893.00 | USD -43,945.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 170 | 81.18% | USD 355.82 | USD 60,490.00 | USD -43,971.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 170 | 81.18% | USD 346.72 | USD 58,943.00 | USD -43,980.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 170 | 81.18% | USD 320.82 | USD 54,540.00 | USD -44,006.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 170 | 81.18% | USD 311.72 | USD 52,993.00 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 170 | 81.18% | USD 250.82 | USD 42,640.00 | USD -44,076.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 170 | 81.18% | USD 241.72 | USD 41,093.00 | USD -44,085.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 171/172 (1) | 31.58% (25.08–38.89%) | USD -41.12 | USD -7,031.60 | USD -1,394.60 |
| HOLD_5_SESSIONS | 1 : 6 | 171/172 (1) | 71.93% (64.77–78.13%) | USD 18.87 | USD 3,226.90 | USD -17,756.10 |
| HOLD_5_SESSIONS | 6 : 1 | 171/172 (1) | 23.98% (18.19–30.90%) | USD -306.71 | USD -52,448.10 | USD -6,451.10 |
| HOLD_5_SESSIONS | 5 : 5 | 171/172 (1) | 31.58% (25.08–38.89%) | USD -205.60 | USD -35,158.00 | USD -6,973.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 171/172 (1) | 31.58% (25.08–38.89%) | USD -41.12 | USD -7,031.60 | USD -1,394.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 171/172 (1) | 71.93% (64.77–78.13%) | USD 18.87 | USD 3,226.90 | USD -17,756.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 171/172 (1) | 23.98% (18.19–30.90%) | USD -306.71 | USD -52,448.10 | USD -6,451.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 171/172 (1) | 31.58% (25.08–38.89%) | USD -205.60 | USD -35,158.00 | USD -6,973.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 171/172 (1) | 31.58% (25.08–38.89%) | USD -41.12 | USD -7,031.60 | USD -1,394.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 171/172 (1) | 71.93% (64.77–78.13%) | USD 18.87 | USD 3,226.90 | USD -17,756.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 171/172 (1) | 23.98% (18.19–30.90%) | USD -306.71 | USD -52,448.10 | USD -6,451.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 171/172 (1) | 31.58% (25.08–38.89%) | USD -205.60 | USD -35,158.00 | USD -6,973.00 |
| HOLD_10_SESSIONS | 1 : 1 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -53.37 | USD -9,073.00 | USD -3,033.60 |
| HOLD_10_SESSIONS | 1 : 6 | 170/172 (2) | 77.65% (70.81–83.26%) | USD 205.75 | USD 34,977.00 | USD -27,025.10 |
| HOLD_10_SESSIONS | 6 : 1 | 170/172 (2) | 19.41% (14.17–26.01%) | USD -579.34 | USD -98,488.00 | USD -7,310.10 |
| HOLD_10_SESSIONS | 5 : 5 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -266.85 | USD -45,365.00 | USD -15,168.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -53.37 | USD -9,073.00 | USD -3,033.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 170/172 (2) | 77.65% (70.81–83.26%) | USD 205.75 | USD 34,977.00 | USD -27,025.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 170/172 (2) | 19.41% (14.17–26.01%) | USD -579.34 | USD -98,488.00 | USD -7,310.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -266.85 | USD -45,365.00 | USD -15,168.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -53.37 | USD -9,073.00 | USD -3,033.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 170/172 (2) | 77.65% (70.81–83.26%) | USD 205.75 | USD 34,977.00 | USD -27,025.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 170/172 (2) | 19.41% (14.17–26.01%) | USD -579.34 | USD -98,488.00 | USD -7,310.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -266.85 | USD -45,365.00 | USD -15,168.00 |
| HOLD_15_SESSIONS | 1 : 1 | 170/172 (2) | 32.35% (25.78–39.71%) | USD -47.64 | USD -8,098.00 | USD -3,973.60 |
| HOLD_15_SESSIONS | 1 : 6 | 170/172 (2) | 75.88% (68.93–81.70%) | USD 288.25 | USD 49,002.00 | USD -45,670.10 |
| HOLD_15_SESSIONS | 6 : 1 | 170/172 (2) | 21.18% (15.71–27.92%) | USD -621.69 | USD -105,688.00 | USD -7,390.10 |
| HOLD_15_SESSIONS | 5 : 5 | 170/172 (2) | 32.35% (25.78–39.71%) | USD -238.18 | USD -40,490.00 | USD -19,868.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 170/172 (2) | 32.35% (25.78–39.71%) | USD -47.64 | USD -8,098.00 | USD -3,973.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 170/172 (2) | 75.88% (68.93–81.70%) | USD 288.25 | USD 49,002.00 | USD -45,670.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 170/172 (2) | 21.18% (15.71–27.92%) | USD -621.69 | USD -105,688.00 | USD -7,390.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 170/172 (2) | 32.35% (25.78–39.71%) | USD -238.18 | USD -40,490.00 | USD -19,868.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 170/172 (2) | 32.35% (25.78–39.71%) | USD -47.64 | USD -8,098.00 | USD -3,973.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 170/172 (2) | 75.88% (68.93–81.70%) | USD 288.25 | USD 49,002.00 | USD -45,670.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 170/172 (2) | 21.18% (15.71–27.92%) | USD -621.69 | USD -105,688.00 | USD -7,390.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 170/172 (2) | 32.35% (25.78–39.71%) | USD -238.18 | USD -40,490.00 | USD -19,868.00 |
| HOLD_20_SESSIONS | 1 : 1 | 169/172 (3) | 36.69% (29.79–44.17%) | USD -62.21 | USD -10,513.40 | USD -4,413.60 |
| HOLD_20_SESSIONS | 1 : 6 | 169/172 (3) | 82.25% (75.79–87.27%) | USD 403.07 | USD 68,118.10 | USD -44,015.10 |
| HOLD_20_SESSIONS | 6 : 1 | 169/172 (3) | 17.75% (12.73–24.21%) | USD -838.53 | USD -141,711.90 | USD -7,350.10 |
| HOLD_20_SESSIONS | 5 : 5 | 169/172 (3) | 36.69% (29.79–44.17%) | USD -311.05 | USD -52,567.00 | USD -22,068.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 169/172 (3) | 36.69% (29.79–44.17%) | USD -62.21 | USD -10,513.40 | USD -4,413.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 169/172 (3) | 82.25% (75.79–87.27%) | USD 403.07 | USD 68,118.10 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 169/172 (3) | 17.75% (12.73–24.21%) | USD -838.53 | USD -141,711.90 | USD -7,350.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 169/172 (3) | 36.69% (29.79–44.17%) | USD -311.05 | USD -52,567.00 | USD -22,068.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 170/172 (2) | 38.82% (31.82–46.32%) | USD -62.98 | USD -10,707.00 | USD -4,413.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 170/172 (2) | 81.18% (74.64–86.34%) | USD 311.72 | USD 52,993.00 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 170/172 (2) | 18.82% (13.66–25.36%) | USD -752.60 | USD -127,942.00 | USD -7,309.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 170/172 (2) | 38.82% (31.82–46.32%) | USD -314.91 | USD -53,535.00 | USD -22,068.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/172 | 0.00% | USD -202,891.76 | USD -337,225.55 |
| -75% | 0/172 | 0.00% | USD -149,454.02 | USD -249,489.55 |
| -50% | 0/172 | 0.00% | USD -96,016.28 | USD -161,753.55 |
| -40% | 0/172 | 0.00% | USD -74,641.18 | USD -126,659.15 |
| -30% | 0/172 | 0.00% | USD -53,266.09 | USD -91,564.75 |
| -25% | 0/172 | 0.00% | USD -42,578.54 | USD -74,017.55 |
| -20% | 0/172 | 0.00% | USD -31,890.99 | USD -56,470.35 |
| -15% | 1/172 | 0.58% | USD -21,230.69 | USD -38,923.15 |
| -10% | 8/172 | 4.65% | USD -10,628.00 | USD -22,266.35 |
| -5% | 74/172 | 43.02% | USD -756.86 | USD -7,526.90 |
| 0% | 172/172 | 100.00% | USD 2,063.15 | USD 610.45 |
| 5% | 172/172 | 100.00% | USD 2,063.15 | USD 610.45 |
| 10% | 172/172 | 100.00% | USD 2,063.15 | USD 610.45 |
| 20% | 172/172 | 100.00% | USD 2,063.15 | USD 610.45 |

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