# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 550.81 / USD 3,269.17; mean absolute mismatch USD 2,718.37; mean match score 16.55%.
- Actual selected contract ratios: {'1:6': 109}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 109; entered cohorts: 109; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 109/109 | 71/38/0 | 65.14% (55.81–73.43%) | USD 3.84 | USD 371.90 | USD 419.10 | USD -8,501.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 109/109 | 71/38/0 | 65.14% (55.81–73.43%) | USD 3.84 | USD 371.90 | USD 419.10 | USD -8,501.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 109/109 | 71/38/0 | 65.14% (55.81–73.43%) | USD 3.84 | USD 371.90 | USD 419.10 | USD -8,501.10 | 0 |
| HOLD_10_SESSIONS | 108/109 | 84/24/0 | 77.78% (69.06–84.59%) | USD 302.86 | USD 787.40 | USD 32,709.20 | USD -15,403.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 108/109 | 84/24/0 | 77.78% (69.06–84.59%) | USD 302.86 | USD 787.40 | USD 32,709.20 | USD -15,403.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 108/109 | 84/24/0 | 77.78% (69.06–84.59%) | USD 302.86 | USD 787.40 | USD 32,709.20 | USD -15,403.10 | 1 |
| HOLD_15_SESSIONS | 107/109 | 82/25/0 | 76.64% (67.78–83.64%) | USD 317.19 | USD 1,158.90 | USD 33,939.30 | USD -40,775.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 107/109 | 82/25/0 | 76.64% (67.78–83.64%) | USD 317.19 | USD 1,158.90 | USD 33,939.30 | USD -40,775.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 107/109 | 82/25/0 | 76.64% (67.78–83.64%) | USD 317.19 | USD 1,158.90 | USD 33,939.30 | USD -40,775.10 | 2 |
| HOLD_20_SESSIONS | 107/109 | 87/20/0 | 81.31% (72.89–87.56%) | USD 362.01 | USD 1,473.90 | USD 38,735.30 | USD -39,349.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 107/109 | 87/20/0 | 81.31% (72.89–87.56%) | USD 362.01 | USD 1,473.90 | USD 38,735.30 | USD -39,349.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 107/109 | 87/20/0 | 81.31% (72.89–87.56%) | USD 362.01 | USD 1,473.90 | USD 38,735.30 | USD -39,349.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -38.65 | USD 121.60 |
| HOLD_5_OR_DTE_LE_7 | USD -38.65 | USD 121.60 |
| HOLD_5_OR_DTE_LE_14 | USD -38.65 | USD 121.60 |
| HOLD_10_SESSIONS | USD -95.04 | USD 477.00 |
| HOLD_10_OR_DTE_LE_7 | USD -95.04 | USD 477.00 |
| HOLD_10_OR_DTE_LE_14 | USD -95.04 | USD 477.00 |
| HOLD_15_SESSIONS | USD -123.07 | USD 519.36 |
| HOLD_15_OR_DTE_LE_7 | USD -123.07 | USD 519.36 |
| HOLD_15_OR_DTE_LE_14 | USD -123.07 | USD 519.36 |
| HOLD_20_SESSIONS | USD -156.70 | USD 597.81 |
| HOLD_20_OR_DTE_LE_7 | USD -156.70 | USD 597.81 |
| HOLD_20_OR_DTE_LE_14 | USD -156.70 | USD 597.81 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 109 | 67.89% | USD 82.94 | USD 9,041.00 | USD -8,422.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 109 | 67.89% | USD 73.84 | USD 8,049.10 | USD -8,431.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 109 | 66.97% | USD 47.94 | USD 5,226.00 | USD -8,457.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 109 | 66.97% | USD 38.84 | USD 4,234.10 | USD -8,466.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 109 | 66.06% | USD 12.94 | USD 1,411.00 | USD -8,492.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 109 | 65.14% | USD 3.84 | USD 419.10 | USD -8,501.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 109 | 63.30% | USD -57.06 | USD -6,219.00 | USD -8,562.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 109 | 62.39% | USD -66.16 | USD -7,210.90 | USD -8,571.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 109 | 67.89% | USD 82.94 | USD 9,041.00 | USD -8,422.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 109 | 67.89% | USD 73.84 | USD 8,049.10 | USD -8,431.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 109 | 66.97% | USD 47.94 | USD 5,226.00 | USD -8,457.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 109 | 66.97% | USD 38.84 | USD 4,234.10 | USD -8,466.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 109 | 66.06% | USD 12.94 | USD 1,411.00 | USD -8,492.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 109 | 65.14% | USD 3.84 | USD 419.10 | USD -8,501.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 109 | 63.30% | USD -57.06 | USD -6,219.00 | USD -8,562.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 109 | 62.39% | USD -66.16 | USD -7,210.90 | USD -8,571.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 109 | 67.89% | USD 82.94 | USD 9,041.00 | USD -8,422.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 109 | 67.89% | USD 73.84 | USD 8,049.10 | USD -8,431.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 109 | 66.97% | USD 47.94 | USD 5,226.00 | USD -8,457.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 109 | 66.97% | USD 38.84 | USD 4,234.10 | USD -8,466.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 109 | 66.06% | USD 12.94 | USD 1,411.00 | USD -8,492.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 109 | 65.14% | USD 3.84 | USD 419.10 | USD -8,501.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 109 | 63.30% | USD -57.06 | USD -6,219.00 | USD -8,562.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 109 | 62.39% | USD -66.16 | USD -7,210.90 | USD -8,571.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 108 | 77.78% | USD 381.96 | USD 41,252.00 | USD -15,324.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 108 | 77.78% | USD 372.86 | USD 40,269.20 | USD -15,333.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 108 | 77.78% | USD 346.96 | USD 37,472.00 | USD -15,359.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 108 | 77.78% | USD 337.86 | USD 36,489.20 | USD -15,368.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 108 | 77.78% | USD 311.96 | USD 33,692.00 | USD -15,394.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 108 | 77.78% | USD 302.86 | USD 32,709.20 | USD -15,403.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 108 | 76.85% | USD 241.96 | USD 26,132.00 | USD -15,464.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 108 | 76.85% | USD 232.86 | USD 25,149.20 | USD -15,473.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 108 | 77.78% | USD 381.96 | USD 41,252.00 | USD -15,324.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 108 | 77.78% | USD 372.86 | USD 40,269.20 | USD -15,333.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 108 | 77.78% | USD 346.96 | USD 37,472.00 | USD -15,359.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 108 | 77.78% | USD 337.86 | USD 36,489.20 | USD -15,368.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 108 | 77.78% | USD 311.96 | USD 33,692.00 | USD -15,394.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 108 | 77.78% | USD 302.86 | USD 32,709.20 | USD -15,403.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 108 | 76.85% | USD 241.96 | USD 26,132.00 | USD -15,464.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 108 | 76.85% | USD 232.86 | USD 25,149.20 | USD -15,473.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 108 | 77.78% | USD 381.96 | USD 41,252.00 | USD -15,324.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 108 | 77.78% | USD 372.86 | USD 40,269.20 | USD -15,333.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 108 | 77.78% | USD 346.96 | USD 37,472.00 | USD -15,359.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 108 | 77.78% | USD 337.86 | USD 36,489.20 | USD -15,368.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 108 | 77.78% | USD 311.96 | USD 33,692.00 | USD -15,394.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 108 | 77.78% | USD 302.86 | USD 32,709.20 | USD -15,403.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 108 | 76.85% | USD 241.96 | USD 26,132.00 | USD -15,464.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 108 | 76.85% | USD 232.86 | USD 25,149.20 | USD -15,473.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 107 | 78.50% | USD 396.29 | USD 42,403.00 | USD -40,696.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 107 | 77.57% | USD 387.19 | USD 41,429.30 | USD -40,705.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 107 | 77.57% | USD 361.29 | USD 38,658.00 | USD -40,731.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 107 | 77.57% | USD 352.19 | USD 37,684.30 | USD -40,740.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 107 | 77.57% | USD 326.29 | USD 34,913.00 | USD -40,766.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 107 | 76.64% | USD 317.19 | USD 33,939.30 | USD -40,775.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 107 | 75.70% | USD 256.29 | USD 27,423.00 | USD -40,836.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 107 | 75.70% | USD 247.19 | USD 26,449.30 | USD -40,845.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 107 | 78.50% | USD 396.29 | USD 42,403.00 | USD -40,696.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 107 | 77.57% | USD 387.19 | USD 41,429.30 | USD -40,705.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 107 | 77.57% | USD 361.29 | USD 38,658.00 | USD -40,731.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 107 | 77.57% | USD 352.19 | USD 37,684.30 | USD -40,740.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 107 | 77.57% | USD 326.29 | USD 34,913.00 | USD -40,766.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 107 | 76.64% | USD 317.19 | USD 33,939.30 | USD -40,775.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 107 | 75.70% | USD 256.29 | USD 27,423.00 | USD -40,836.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 107 | 75.70% | USD 247.19 | USD 26,449.30 | USD -40,845.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 107 | 78.50% | USD 396.29 | USD 42,403.00 | USD -40,696.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 107 | 77.57% | USD 387.19 | USD 41,429.30 | USD -40,705.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 107 | 77.57% | USD 361.29 | USD 38,658.00 | USD -40,731.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 107 | 77.57% | USD 352.19 | USD 37,684.30 | USD -40,740.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 107 | 77.57% | USD 326.29 | USD 34,913.00 | USD -40,766.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 107 | 76.64% | USD 317.19 | USD 33,939.30 | USD -40,775.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 107 | 75.70% | USD 256.29 | USD 27,423.00 | USD -40,836.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 107 | 75.70% | USD 247.19 | USD 26,449.30 | USD -40,845.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 107 | 82.24% | USD 441.11 | USD 47,199.00 | USD -39,270.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 107 | 82.24% | USD 432.01 | USD 46,225.30 | USD -39,279.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 107 | 82.24% | USD 406.11 | USD 43,454.00 | USD -39,305.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 107 | 82.24% | USD 397.01 | USD 42,480.30 | USD -39,314.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 107 | 81.31% | USD 371.11 | USD 39,709.00 | USD -39,340.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 107 | 81.31% | USD 362.01 | USD 38,735.30 | USD -39,349.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 107 | 81.31% | USD 301.11 | USD 32,219.00 | USD -39,410.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 107 | 81.31% | USD 292.01 | USD 31,245.30 | USD -39,419.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 107 | 82.24% | USD 441.11 | USD 47,199.00 | USD -39,270.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 107 | 82.24% | USD 432.01 | USD 46,225.30 | USD -39,279.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 107 | 82.24% | USD 406.11 | USD 43,454.00 | USD -39,305.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 107 | 82.24% | USD 397.01 | USD 42,480.30 | USD -39,314.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 107 | 81.31% | USD 371.11 | USD 39,709.00 | USD -39,340.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 107 | 81.31% | USD 362.01 | USD 38,735.30 | USD -39,349.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 107 | 81.31% | USD 301.11 | USD 32,219.00 | USD -39,410.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 107 | 81.31% | USD 292.01 | USD 31,245.30 | USD -39,419.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 107 | 82.24% | USD 441.11 | USD 47,199.00 | USD -39,270.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 107 | 82.24% | USD 432.01 | USD 46,225.30 | USD -39,279.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 107 | 82.24% | USD 406.11 | USD 43,454.00 | USD -39,305.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 107 | 82.24% | USD 397.01 | USD 42,480.30 | USD -39,314.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 107 | 81.31% | USD 371.11 | USD 39,709.00 | USD -39,340.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 107 | 81.31% | USD 362.01 | USD 38,735.30 | USD -39,349.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 107 | 81.31% | USD 301.11 | USD 32,219.00 | USD -39,410.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 107 | 81.31% | USD 292.01 | USD 31,245.30 | USD -39,419.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 109/109 (0) | 27.52% (20.01–36.56%) | USD -40.99 | USD -4,467.40 | USD -790.60 |
| HOLD_5_SESSIONS | 1 : 6 | 109/109 (0) | 65.14% (55.81–73.43%) | USD 3.84 | USD 419.10 | USD -8,501.10 |
| HOLD_5_SESSIONS | 6 : 1 | 109/109 (0) | 29.36% (21.63–38.49%) | USD -290.74 | USD -31,690.90 | USD -4,456.10 |
| HOLD_5_SESSIONS | 5 : 5 | 109/109 (0) | 27.52% (20.01–36.56%) | USD -204.93 | USD -22,337.00 | USD -3,953.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 109/109 (0) | 27.52% (20.01–36.56%) | USD -40.99 | USD -4,467.40 | USD -790.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 109/109 (0) | 65.14% (55.81–73.43%) | USD 3.84 | USD 419.10 | USD -8,501.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 109/109 (0) | 29.36% (21.63–38.49%) | USD -290.74 | USD -31,690.90 | USD -4,456.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 109/109 (0) | 27.52% (20.01–36.56%) | USD -204.93 | USD -22,337.00 | USD -3,953.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 109/109 (0) | 27.52% (20.01–36.56%) | USD -40.99 | USD -4,467.40 | USD -790.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 109/109 (0) | 65.14% (55.81–73.43%) | USD 3.84 | USD 419.10 | USD -8,501.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 109/109 (0) | 29.36% (21.63–38.49%) | USD -290.74 | USD -31,690.90 | USD -4,456.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 109/109 (0) | 27.52% (20.01–36.56%) | USD -204.93 | USD -22,337.00 | USD -3,953.00 |
| HOLD_10_SESSIONS | 1 : 1 | 108/109 (1) | 33.33% (25.15–42.66%) | USD -38.14 | USD -4,118.80 | USD -1,511.60 |
| HOLD_10_SESSIONS | 1 : 6 | 108/109 (1) | 77.78% (69.06–84.59%) | USD 302.86 | USD 32,709.20 | USD -15,403.10 |
| HOLD_10_SESSIONS | 6 : 1 | 108/109 (1) | 24.07% (16.99–32.94%) | USD -569.82 | USD -61,540.80 | USD -5,156.10 |
| HOLD_10_SESSIONS | 5 : 5 | 108/109 (1) | 33.33% (25.15–42.66%) | USD -190.69 | USD -20,594.00 | USD -7,558.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 108/109 (1) | 33.33% (25.15–42.66%) | USD -38.14 | USD -4,118.80 | USD -1,511.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 108/109 (1) | 77.78% (69.06–84.59%) | USD 302.86 | USD 32,709.20 | USD -15,403.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 108/109 (1) | 24.07% (16.99–32.94%) | USD -569.82 | USD -61,540.80 | USD -5,156.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 108/109 (1) | 33.33% (25.15–42.66%) | USD -190.69 | USD -20,594.00 | USD -7,558.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 108/109 (1) | 33.33% (25.15–42.66%) | USD -38.14 | USD -4,118.80 | USD -1,511.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 108/109 (1) | 77.78% (69.06–84.59%) | USD 302.86 | USD 32,709.20 | USD -15,403.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 108/109 (1) | 24.07% (16.99–32.94%) | USD -569.82 | USD -61,540.80 | USD -5,156.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 108/109 (1) | 33.33% (25.15–42.66%) | USD -190.69 | USD -20,594.00 | USD -7,558.00 |
| HOLD_15_SESSIONS | 1 : 1 | 107/109 (2) | 36.45% (27.95–45.89%) | USD -59.11 | USD -6,325.20 | USD -3,598.60 |
| HOLD_15_SESSIONS | 1 : 6 | 107/109 (2) | 76.64% (67.78–83.64%) | USD 317.19 | USD 33,939.30 | USD -40,775.10 |
| HOLD_15_SESSIONS | 6 : 1 | 107/109 (2) | 24.30% (17.16–33.22%) | USD -730.99 | USD -78,215.70 | USD -4,889.10 |
| HOLD_15_SESSIONS | 5 : 5 | 107/109 (2) | 36.45% (27.95–45.89%) | USD -295.57 | USD -31,626.00 | USD -17,993.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 107/109 (2) | 36.45% (27.95–45.89%) | USD -59.11 | USD -6,325.20 | USD -3,598.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 107/109 (2) | 76.64% (67.78–83.64%) | USD 317.19 | USD 33,939.30 | USD -40,775.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 107/109 (2) | 24.30% (17.16–33.22%) | USD -730.99 | USD -78,215.70 | USD -4,889.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 107/109 (2) | 36.45% (27.95–45.89%) | USD -295.57 | USD -31,626.00 | USD -17,993.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 107/109 (2) | 36.45% (27.95–45.89%) | USD -59.11 | USD -6,325.20 | USD -3,598.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 107/109 (2) | 76.64% (67.78–83.64%) | USD 317.19 | USD 33,939.30 | USD -40,775.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 107/109 (2) | 24.30% (17.16–33.22%) | USD -730.99 | USD -78,215.70 | USD -4,889.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 107/109 (2) | 36.45% (27.95–45.89%) | USD -295.57 | USD -31,626.00 | USD -17,993.00 |
| HOLD_20_SESSIONS | 1 : 1 | 107/109 (2) | 38.32% (29.66–47.78%) | USD -79.67 | USD -8,524.20 | USD -4,012.60 |
| HOLD_20_SESSIONS | 1 : 6 | 107/109 (2) | 81.31% (72.89–87.56%) | USD 362.01 | USD 38,735.30 | USD -39,349.10 |
| HOLD_20_SESSIONS | 6 : 1 | 107/109 (2) | 20.56% (13.99–29.17%) | USD -919.67 | USD -98,404.70 | USD -4,804.10 |
| HOLD_20_SESSIONS | 5 : 5 | 107/109 (2) | 38.32% (29.66–47.78%) | USD -398.33 | USD -42,621.00 | USD -20,063.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 107/109 (2) | 38.32% (29.66–47.78%) | USD -79.67 | USD -8,524.20 | USD -4,012.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 107/109 (2) | 81.31% (72.89–87.56%) | USD 362.01 | USD 38,735.30 | USD -39,349.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 107/109 (2) | 20.56% (13.99–29.17%) | USD -919.67 | USD -98,404.70 | USD -4,804.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 107/109 (2) | 38.32% (29.66–47.78%) | USD -398.33 | USD -42,621.00 | USD -20,063.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 107/109 (2) | 38.32% (29.66–47.78%) | USD -79.67 | USD -8,524.20 | USD -4,012.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 107/109 (2) | 81.31% (72.89–87.56%) | USD 362.01 | USD 38,735.30 | USD -39,349.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 107/109 (2) | 20.56% (13.99–29.17%) | USD -919.67 | USD -98,404.70 | USD -4,804.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 107/109 (2) | 38.32% (29.66–47.78%) | USD -398.33 | USD -42,621.00 | USD -20,063.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/109 | 0.00% | USD -207,371.02 | USD -331,436.55 |
| -75% | 0/109 | 0.00% | USD -152,248.66 | USD -244,222.30 |
| -50% | 0/109 | 0.00% | USD -97,126.29 | USD -157,008.05 |
| -40% | 0/109 | 0.00% | USD -75,077.35 | USD -122,122.35 |
| -30% | 0/109 | 0.00% | USD -53,028.40 | USD -87,236.65 |
| -25% | 0/109 | 0.00% | USD -42,003.93 | USD -69,793.80 |
| -20% | 0/109 | 0.00% | USD -30,979.46 | USD -52,350.95 |
| -15% | 1/109 | 0.92% | USD -19,954.99 | USD -35,397.25 |
| -10% | 7/109 | 6.42% | USD -8,938.16 | USD -19,938.25 |
| -5% | 67/109 | 61.47% | USD 842.03 | USD -6,321.90 |
| 0% | 109/109 | 100.00% | USD 2,677.10 | USD 1,022.45 |
| 5% | 109/109 | 100.00% | USD 2,678.82 | USD 1,022.45 |
| 10% | 109/109 | 100.00% | USD 2,678.82 | USD 1,022.45 |
| 20% | 109/109 | 100.00% | USD 2,678.82 | USD 1,022.45 |

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