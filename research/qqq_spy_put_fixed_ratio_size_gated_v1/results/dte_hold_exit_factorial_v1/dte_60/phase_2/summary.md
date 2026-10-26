# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 585.25 / USD 3,485.74; mean absolute mismatch USD 2,900.49; mean match score 16.54%.
- Actual selected contract ratios: {'1:6': 115}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 115; entered cohorts: 115; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 113/115 | 75/38/0 | 66.37% (57.25–74.42%) | USD 207.31 | USD 418.90 | USD 23,425.70 | USD -6,911.10 | 2 |
| HOLD_5_OR_DTE_LE_7 | 113/115 | 75/38/0 | 66.37% (57.25–74.42%) | USD 207.31 | USD 418.90 | USD 23,425.70 | USD -6,911.10 | 2 |
| HOLD_5_OR_DTE_LE_14 | 113/115 | 75/38/0 | 66.37% (57.25–74.42%) | USD 207.31 | USD 418.90 | USD 23,425.70 | USD -6,911.10 | 2 |
| HOLD_10_SESSIONS | 113/115 | 80/33/0 | 70.80% (61.84–78.39%) | USD 162.51 | USD 720.90 | USD 18,363.70 | USD -19,080.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 113/115 | 80/33/0 | 70.80% (61.84–78.39%) | USD 162.51 | USD 720.90 | USD 18,363.70 | USD -19,080.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 113/115 | 80/33/0 | 70.80% (61.84–78.39%) | USD 162.51 | USD 720.90 | USD 18,363.70 | USD -19,080.10 | 2 |
| HOLD_15_SESSIONS | 112/115 | 92/20/0 | 82.14% (74.02–88.13%) | USD 671.79 | USD 1,150.40 | USD 75,240.80 | USD -19,568.10 | 3 |
| HOLD_15_OR_DTE_LE_7 | 112/115 | 92/20/0 | 82.14% (74.02–88.13%) | USD 671.79 | USD 1,150.40 | USD 75,240.80 | USD -19,568.10 | 3 |
| HOLD_15_OR_DTE_LE_14 | 112/115 | 92/20/0 | 82.14% (74.02–88.13%) | USD 671.79 | USD 1,150.40 | USD 75,240.80 | USD -19,568.10 | 3 |
| HOLD_20_SESSIONS | 112/115 | 91/21/0 | 81.25% (73.03–87.40%) | USD 481.91 | USD 1,388.40 | USD 53,973.80 | USD -45,010.10 | 3 |
| HOLD_20_OR_DTE_LE_7 | 112/115 | 91/21/0 | 81.25% (73.03–87.40%) | USD 481.91 | USD 1,388.40 | USD 53,973.80 | USD -45,010.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 112/115 | 91/21/0 | 81.25% (73.03–87.40%) | USD 481.91 | USD 1,388.40 | USD 53,973.80 | USD -45,010.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -74.28 | USD 360.69 |
| HOLD_5_OR_DTE_LE_7 | USD -74.28 | USD 360.69 |
| HOLD_5_OR_DTE_LE_14 | USD -74.28 | USD 360.69 |
| HOLD_10_SESSIONS | USD -85.20 | USD 326.81 |
| HOLD_10_OR_DTE_LE_7 | USD -85.20 | USD 326.81 |
| HOLD_10_OR_DTE_LE_14 | USD -85.20 | USD 326.81 |
| HOLD_15_SESSIONS | USD -175.25 | USD 926.14 |
| HOLD_15_OR_DTE_LE_7 | USD -175.25 | USD 926.14 |
| HOLD_15_OR_DTE_LE_14 | USD -175.25 | USD 926.14 |
| HOLD_20_SESSIONS | USD -172.22 | USD 733.23 |
| HOLD_20_OR_DTE_LE_7 | USD -172.22 | USD 733.23 |
| HOLD_20_OR_DTE_LE_14 | USD -172.22 | USD 733.23 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 113 | 69.03% | USD 286.41 | USD 32,364.00 | USD -6,832.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 113 | 69.03% | USD 277.31 | USD 31,335.70 | USD -6,841.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 113 | 69.03% | USD 251.41 | USD 28,409.00 | USD -6,867.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 113 | 68.14% | USD 242.31 | USD 27,380.70 | USD -6,876.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 113 | 68.14% | USD 216.41 | USD 24,454.00 | USD -6,902.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 113 | 66.37% | USD 207.31 | USD 23,425.70 | USD -6,911.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 113 | 65.49% | USD 146.41 | USD 16,544.00 | USD -6,972.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 113 | 64.60% | USD 137.31 | USD 15,515.70 | USD -6,981.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 69.03% | USD 286.41 | USD 32,364.00 | USD -6,832.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 69.03% | USD 277.31 | USD 31,335.70 | USD -6,841.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 69.03% | USD 251.41 | USD 28,409.00 | USD -6,867.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 68.14% | USD 242.31 | USD 27,380.70 | USD -6,876.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 68.14% | USD 216.41 | USD 24,454.00 | USD -6,902.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 66.37% | USD 207.31 | USD 23,425.70 | USD -6,911.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 65.49% | USD 146.41 | USD 16,544.00 | USD -6,972.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 64.60% | USD 137.31 | USD 15,515.70 | USD -6,981.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 69.03% | USD 286.41 | USD 32,364.00 | USD -6,832.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 69.03% | USD 277.31 | USD 31,335.70 | USD -6,841.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 69.03% | USD 251.41 | USD 28,409.00 | USD -6,867.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 68.14% | USD 242.31 | USD 27,380.70 | USD -6,876.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 68.14% | USD 216.41 | USD 24,454.00 | USD -6,902.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 66.37% | USD 207.31 | USD 23,425.70 | USD -6,911.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 65.49% | USD 146.41 | USD 16,544.00 | USD -6,972.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 64.60% | USD 137.31 | USD 15,515.70 | USD -6,981.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 113 | 71.68% | USD 241.61 | USD 27,302.00 | USD -19,001.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 113 | 71.68% | USD 232.51 | USD 26,273.70 | USD -19,010.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 113 | 71.68% | USD 206.61 | USD 23,347.00 | USD -19,036.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 113 | 71.68% | USD 197.51 | USD 22,318.70 | USD -19,045.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 113 | 70.80% | USD 171.61 | USD 19,392.00 | USD -19,071.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 113 | 70.80% | USD 162.51 | USD 18,363.70 | USD -19,080.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 113 | 69.91% | USD 101.61 | USD 11,482.00 | USD -19,141.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 113 | 69.91% | USD 92.51 | USD 10,453.70 | USD -19,150.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 71.68% | USD 241.61 | USD 27,302.00 | USD -19,001.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 71.68% | USD 232.51 | USD 26,273.70 | USD -19,010.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 71.68% | USD 206.61 | USD 23,347.00 | USD -19,036.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 71.68% | USD 197.51 | USD 22,318.70 | USD -19,045.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 70.80% | USD 171.61 | USD 19,392.00 | USD -19,071.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 70.80% | USD 162.51 | USD 18,363.70 | USD -19,080.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 69.91% | USD 101.61 | USD 11,482.00 | USD -19,141.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 69.91% | USD 92.51 | USD 10,453.70 | USD -19,150.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 71.68% | USD 241.61 | USD 27,302.00 | USD -19,001.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 71.68% | USD 232.51 | USD 26,273.70 | USD -19,010.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 71.68% | USD 206.61 | USD 23,347.00 | USD -19,036.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 71.68% | USD 197.51 | USD 22,318.70 | USD -19,045.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 70.80% | USD 171.61 | USD 19,392.00 | USD -19,071.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 70.80% | USD 162.51 | USD 18,363.70 | USD -19,080.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 69.91% | USD 101.61 | USD 11,482.00 | USD -19,141.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 69.91% | USD 92.51 | USD 10,453.70 | USD -19,150.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 112 | 82.14% | USD 750.89 | USD 84,100.00 | USD -19,489.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 112 | 82.14% | USD 741.79 | USD 83,080.80 | USD -19,498.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 112 | 82.14% | USD 715.89 | USD 80,180.00 | USD -19,524.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 112 | 82.14% | USD 706.79 | USD 79,160.80 | USD -19,533.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 112 | 82.14% | USD 680.89 | USD 76,260.00 | USD -19,559.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 112 | 82.14% | USD 671.79 | USD 75,240.80 | USD -19,568.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 112 | 82.14% | USD 610.89 | USD 68,420.00 | USD -19,629.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 112 | 82.14% | USD 601.79 | USD 67,400.80 | USD -19,638.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 82.14% | USD 750.89 | USD 84,100.00 | USD -19,489.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 82.14% | USD 741.79 | USD 83,080.80 | USD -19,498.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 82.14% | USD 715.89 | USD 80,180.00 | USD -19,524.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 82.14% | USD 706.79 | USD 79,160.80 | USD -19,533.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 82.14% | USD 680.89 | USD 76,260.00 | USD -19,559.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 82.14% | USD 671.79 | USD 75,240.80 | USD -19,568.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 82.14% | USD 610.89 | USD 68,420.00 | USD -19,629.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 82.14% | USD 601.79 | USD 67,400.80 | USD -19,638.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 82.14% | USD 750.89 | USD 84,100.00 | USD -19,489.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 82.14% | USD 741.79 | USD 83,080.80 | USD -19,498.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 82.14% | USD 715.89 | USD 80,180.00 | USD -19,524.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 82.14% | USD 706.79 | USD 79,160.80 | USD -19,533.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 82.14% | USD 680.89 | USD 76,260.00 | USD -19,559.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 82.14% | USD 671.79 | USD 75,240.80 | USD -19,568.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 82.14% | USD 610.89 | USD 68,420.00 | USD -19,629.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 82.14% | USD 601.79 | USD 67,400.80 | USD -19,638.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 112 | 81.25% | USD 561.01 | USD 62,833.00 | USD -44,931.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 112 | 81.25% | USD 551.91 | USD 61,813.80 | USD -44,940.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 112 | 81.25% | USD 526.01 | USD 58,913.00 | USD -44,966.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 112 | 81.25% | USD 516.91 | USD 57,893.80 | USD -44,975.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 112 | 81.25% | USD 491.01 | USD 54,993.00 | USD -45,001.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 112 | 81.25% | USD 481.91 | USD 53,973.80 | USD -45,010.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 112 | 80.36% | USD 421.01 | USD 47,153.00 | USD -45,071.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 112 | 80.36% | USD 411.91 | USD 46,133.80 | USD -45,080.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 81.25% | USD 561.01 | USD 62,833.00 | USD -44,931.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 81.25% | USD 551.91 | USD 61,813.80 | USD -44,940.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 81.25% | USD 526.01 | USD 58,913.00 | USD -44,966.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 81.25% | USD 516.91 | USD 57,893.80 | USD -44,975.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 81.25% | USD 491.01 | USD 54,993.00 | USD -45,001.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 81.25% | USD 481.91 | USD 53,973.80 | USD -45,010.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 80.36% | USD 421.01 | USD 47,153.00 | USD -45,071.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 80.36% | USD 411.91 | USD 46,133.80 | USD -45,080.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 81.25% | USD 561.01 | USD 62,833.00 | USD -44,931.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 81.25% | USD 551.91 | USD 61,813.80 | USD -44,940.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 81.25% | USD 526.01 | USD 58,913.00 | USD -44,966.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 81.25% | USD 516.91 | USD 57,893.80 | USD -44,975.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 81.25% | USD 491.01 | USD 54,993.00 | USD -45,001.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 81.25% | USD 481.91 | USD 53,973.80 | USD -45,010.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 80.36% | USD 421.01 | USD 47,153.00 | USD -45,071.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 80.36% | USD 411.91 | USD 46,133.80 | USD -45,080.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -36.77 | USD -4,154.80 | USD -474.60 |
| HOLD_5_SESSIONS | 1 : 6 | 113/115 (2) | 66.37% (57.25–74.42%) | USD 207.31 | USD 23,425.70 | USD -6,911.10 |
| HOLD_5_SESSIONS | 6 : 1 | 113/115 (2) | 30.97% (23.19–40.01%) | USD -464.68 | USD -52,509.30 | USD -5,960.10 |
| HOLD_5_SESSIONS | 5 : 5 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -183.84 | USD -20,774.00 | USD -2,373.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -36.77 | USD -4,154.80 | USD -474.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 66.37% (57.25–74.42%) | USD 207.31 | USD 23,425.70 | USD -6,911.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 30.97% (23.19–40.01%) | USD -464.68 | USD -52,509.30 | USD -5,960.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -183.84 | USD -20,774.00 | USD -2,373.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -36.77 | USD -4,154.80 | USD -474.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 66.37% (57.25–74.42%) | USD 207.31 | USD 23,425.70 | USD -6,911.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 30.97% (23.19–40.01%) | USD -464.68 | USD -52,509.30 | USD -5,960.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -183.84 | USD -20,774.00 | USD -2,373.00 |
| HOLD_10_SESSIONS | 1 : 1 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -53.33 | USD -6,026.80 | USD -1,025.60 |
| HOLD_10_SESSIONS | 1 : 6 | 113/115 (2) | 70.80% (61.84–78.39%) | USD 162.51 | USD 18,363.70 | USD -19,080.10 |
| HOLD_10_SESSIONS | 6 : 1 | 113/115 (2) | 27.43% (20.05–36.30%) | USD -535.85 | USD -60,551.30 | USD -6,742.10 |
| HOLD_10_SESSIONS | 5 : 5 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -266.67 | USD -30,134.00 | USD -5,128.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -53.33 | USD -6,026.80 | USD -1,025.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 70.80% (61.84–78.39%) | USD 162.51 | USD 18,363.70 | USD -19,080.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 27.43% (20.05–36.30%) | USD -535.85 | USD -60,551.30 | USD -6,742.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -266.67 | USD -30,134.00 | USD -5,128.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -53.33 | USD -6,026.80 | USD -1,025.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 70.80% (61.84–78.39%) | USD 162.51 | USD 18,363.70 | USD -19,080.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 27.43% (20.05–36.30%) | USD -535.85 | USD -60,551.30 | USD -6,742.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -266.67 | USD -30,134.00 | USD -5,128.00 |
| HOLD_15_SESSIONS | 1 : 1 | 112/115 (3) | 35.71% (27.45–44.93%) | USD -43.49 | USD -4,871.20 | USD -1,771.60 |
| HOLD_15_SESSIONS | 1 : 6 | 112/115 (3) | 82.14% (74.02–88.13%) | USD 671.79 | USD 75,240.80 | USD -19,568.10 |
| HOLD_15_SESSIONS | 6 : 1 | 112/115 (3) | 21.43% (14.84–29.91%) | USD -976.24 | USD -109,339.20 | USD -7,908.10 |
| HOLD_15_SESSIONS | 5 : 5 | 112/115 (3) | 35.71% (27.45–44.93%) | USD -217.46 | USD -24,356.00 | USD -8,858.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 112/115 (3) | 35.71% (27.45–44.93%) | USD -43.49 | USD -4,871.20 | USD -1,771.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 112/115 (3) | 82.14% (74.02–88.13%) | USD 671.79 | USD 75,240.80 | USD -19,568.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 112/115 (3) | 21.43% (14.84–29.91%) | USD -976.24 | USD -109,339.20 | USD -7,908.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 112/115 (3) | 35.71% (27.45–44.93%) | USD -217.46 | USD -24,356.00 | USD -8,858.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 112/115 (3) | 35.71% (27.45–44.93%) | USD -43.49 | USD -4,871.20 | USD -1,771.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 112/115 (3) | 82.14% (74.02–88.13%) | USD 671.79 | USD 75,240.80 | USD -19,568.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 112/115 (3) | 21.43% (14.84–29.91%) | USD -976.24 | USD -109,339.20 | USD -7,908.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 112/115 (3) | 35.71% (27.45–44.93%) | USD -217.46 | USD -24,356.00 | USD -8,858.00 |
| HOLD_20_SESSIONS | 1 : 1 | 112/115 (3) | 38.39% (29.91–47.64%) | USD -72.62 | USD -8,133.20 | USD -3,883.60 |
| HOLD_20_SESSIONS | 1 : 6 | 112/115 (3) | 81.25% (73.03–87.40%) | USD 481.91 | USD 53,973.80 | USD -45,010.10 |
| HOLD_20_SESSIONS | 6 : 1 | 112/115 (3) | 18.75% (12.60–26.97%) | USD -990.23 | USD -110,906.20 | USD -8,938.10 |
| HOLD_20_SESSIONS | 5 : 5 | 112/115 (3) | 38.39% (29.91–47.64%) | USD -363.09 | USD -40,666.00 | USD -19,418.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 112/115 (3) | 38.39% (29.91–47.64%) | USD -72.62 | USD -8,133.20 | USD -3,883.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 112/115 (3) | 81.25% (73.03–87.40%) | USD 481.91 | USD 53,973.80 | USD -45,010.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 112/115 (3) | 18.75% (12.60–26.97%) | USD -990.23 | USD -110,906.20 | USD -8,938.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 112/115 (3) | 38.39% (29.91–47.64%) | USD -363.09 | USD -40,666.00 | USD -19,418.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 112/115 (3) | 38.39% (29.91–47.64%) | USD -72.62 | USD -8,133.20 | USD -3,883.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 112/115 (3) | 81.25% (73.03–87.40%) | USD 481.91 | USD 53,973.80 | USD -45,010.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 112/115 (3) | 18.75% (12.60–26.97%) | USD -990.23 | USD -110,906.20 | USD -8,938.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 112/115 (3) | 38.39% (29.91–47.64%) | USD -363.09 | USD -40,666.00 | USD -19,418.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/115 | 0.00% | USD -211,144.56 | USD -332,365.55 |
| -75% | 0/115 | 0.00% | USD -155,205.02 | USD -245,149.05 |
| -50% | 0/115 | 0.00% | USD -99,265.48 | USD -157,932.55 |
| -40% | 0/115 | 0.00% | USD -76,889.66 | USD -123,045.95 |
| -30% | 0/115 | 0.00% | USD -54,513.84 | USD -88,159.35 |
| -25% | 0/115 | 0.00% | USD -43,325.93 | USD -70,716.05 |
| -20% | 0/115 | 0.00% | USD -32,138.03 | USD -53,648.35 |
| -15% | 0/115 | 0.00% | USD -20,950.12 | USD -36,597.40 |
| -10% | 5/115 | 4.35% | USD -9,759.87 | USD -20,510.95 |
| -5% | 64/115 | 55.65% | USD 533.88 | USD -6,663.25 |
| 0% | 115/115 | 100.00% | USD 2,835.93 | USD 999.45 |
| 5% | 115/115 | 100.00% | USD 2,860.94 | USD 999.45 |
| 10% | 115/115 | 100.00% | USD 2,860.94 | USD 999.45 |
| 20% | 115/115 | 100.00% | USD 2,860.94 | USD 999.45 |

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