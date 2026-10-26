# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 562.09 / USD 3,345.34; mean absolute mismatch USD 2,783.25; mean match score 16.50%.
- Actual selected contract ratios: {'1:6': 115}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 115; entered cohorts: 115; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 115/115 | 78/37/0 | 67.83% (58.83–75.67%) | USD 54.29 | USD 381.90 | USD 6,243.50 | USD -17,184.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 115/115 | 78/37/0 | 67.83% (58.83–75.67%) | USD 54.29 | USD 381.90 | USD 6,243.50 | USD -17,184.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 115/115 | 78/37/0 | 67.83% (58.83–75.67%) | USD 54.29 | USD 381.90 | USD 6,243.50 | USD -17,184.10 | 0 |
| HOLD_10_SESSIONS | 113/115 | 91/22/0 | 80.53% (72.28–86.78%) | USD 724.24 | USD 1,013.90 | USD 81,838.70 | USD -4,605.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 113/115 | 91/22/0 | 80.53% (72.28–86.78%) | USD 724.24 | USD 1,013.90 | USD 81,838.70 | USD -4,605.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 113/115 | 91/22/0 | 80.53% (72.28–86.78%) | USD 724.24 | USD 1,013.90 | USD 81,838.70 | USD -4,605.10 | 2 |
| HOLD_15_SESSIONS | 113/115 | 91/22/0 | 80.53% (72.28–86.78%) | USD 731.19 | USD 1,375.90 | USD 82,624.70 | USD -11,681.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 113/115 | 91/22/0 | 80.53% (72.28–86.78%) | USD 731.19 | USD 1,375.90 | USD 82,624.70 | USD -11,681.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 113/115 | 91/22/0 | 80.53% (72.28–86.78%) | USD 731.19 | USD 1,375.90 | USD 82,624.70 | USD -11,681.10 | 2 |
| HOLD_20_SESSIONS | 112/115 | 92/20/0 | 82.14% (74.02–88.13%) | USD 1,093.01 | USD 1,538.90 | USD 122,416.80 | USD -8,931.10 | 3 |
| HOLD_20_OR_DTE_LE_7 | 112/115 | 92/20/0 | 82.14% (74.02–88.13%) | USD 1,093.01 | USD 1,538.90 | USD 122,416.80 | USD -8,931.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 112/115 | 92/20/0 | 82.14% (74.02–88.13%) | USD 1,093.01 | USD 1,538.90 | USD 122,416.80 | USD -8,931.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -54.54 | USD 187.93 |
| HOLD_5_OR_DTE_LE_7 | USD -54.54 | USD 187.93 |
| HOLD_5_OR_DTE_LE_14 | USD -54.54 | USD 187.93 |
| HOLD_10_SESSIONS | USD -141.48 | USD 944.81 |
| HOLD_10_OR_DTE_LE_7 | USD -141.48 | USD 944.81 |
| HOLD_10_OR_DTE_LE_14 | USD -141.48 | USD 944.81 |
| HOLD_15_SESSIONS | USD -163.25 | USD 973.54 |
| HOLD_15_OR_DTE_LE_7 | USD -163.25 | USD 973.54 |
| HOLD_15_OR_DTE_LE_14 | USD -163.25 | USD 973.54 |
| HOLD_20_SESSIONS | USD -239.88 | USD 1,411.98 |
| HOLD_20_OR_DTE_LE_7 | USD -239.88 | USD 1,411.98 |
| HOLD_20_OR_DTE_LE_14 | USD -239.88 | USD 1,411.98 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 115 | 70.43% | USD 133.39 | USD 15,340.00 | USD -17,105.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 115 | 69.57% | USD 124.29 | USD 14,293.50 | USD -17,114.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 115 | 69.57% | USD 98.39 | USD 11,315.00 | USD -17,140.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 115 | 68.70% | USD 89.29 | USD 10,268.50 | USD -17,149.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 115 | 67.83% | USD 63.39 | USD 7,290.00 | USD -17,175.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 115 | 67.83% | USD 54.29 | USD 6,243.50 | USD -17,184.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 115 | 65.22% | USD -6.61 | USD -760.00 | USD -17,245.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 115 | 65.22% | USD -15.71 | USD -1,806.50 | USD -17,254.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 115 | 70.43% | USD 133.39 | USD 15,340.00 | USD -17,105.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 115 | 69.57% | USD 124.29 | USD 14,293.50 | USD -17,114.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 115 | 69.57% | USD 98.39 | USD 11,315.00 | USD -17,140.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 115 | 68.70% | USD 89.29 | USD 10,268.50 | USD -17,149.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 115 | 67.83% | USD 63.39 | USD 7,290.00 | USD -17,175.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 115 | 67.83% | USD 54.29 | USD 6,243.50 | USD -17,184.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 115 | 65.22% | USD -6.61 | USD -760.00 | USD -17,245.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 115 | 65.22% | USD -15.71 | USD -1,806.50 | USD -17,254.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 115 | 70.43% | USD 133.39 | USD 15,340.00 | USD -17,105.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 115 | 69.57% | USD 124.29 | USD 14,293.50 | USD -17,114.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 115 | 69.57% | USD 98.39 | USD 11,315.00 | USD -17,140.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 115 | 68.70% | USD 89.29 | USD 10,268.50 | USD -17,149.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 115 | 67.83% | USD 63.39 | USD 7,290.00 | USD -17,175.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 115 | 67.83% | USD 54.29 | USD 6,243.50 | USD -17,184.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 115 | 65.22% | USD -6.61 | USD -760.00 | USD -17,245.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 115 | 65.22% | USD -15.71 | USD -1,806.50 | USD -17,254.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 113 | 81.42% | USD 803.34 | USD 90,777.00 | USD -4,526.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 113 | 81.42% | USD 794.24 | USD 89,748.70 | USD -4,535.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 113 | 80.53% | USD 768.34 | USD 86,822.00 | USD -4,561.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 113 | 80.53% | USD 759.24 | USD 85,793.70 | USD -4,570.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 113 | 80.53% | USD 733.34 | USD 82,867.00 | USD -4,596.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 113 | 80.53% | USD 724.24 | USD 81,838.70 | USD -4,605.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 113 | 78.76% | USD 663.34 | USD 74,957.00 | USD -4,666.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 113 | 78.76% | USD 654.24 | USD 73,928.70 | USD -4,675.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 81.42% | USD 803.34 | USD 90,777.00 | USD -4,526.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 81.42% | USD 794.24 | USD 89,748.70 | USD -4,535.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 80.53% | USD 768.34 | USD 86,822.00 | USD -4,561.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 80.53% | USD 759.24 | USD 85,793.70 | USD -4,570.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 80.53% | USD 733.34 | USD 82,867.00 | USD -4,596.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 80.53% | USD 724.24 | USD 81,838.70 | USD -4,605.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 78.76% | USD 663.34 | USD 74,957.00 | USD -4,666.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 78.76% | USD 654.24 | USD 73,928.70 | USD -4,675.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 81.42% | USD 803.34 | USD 90,777.00 | USD -4,526.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 81.42% | USD 794.24 | USD 89,748.70 | USD -4,535.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 80.53% | USD 768.34 | USD 86,822.00 | USD -4,561.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 80.53% | USD 759.24 | USD 85,793.70 | USD -4,570.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 80.53% | USD 733.34 | USD 82,867.00 | USD -4,596.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 80.53% | USD 724.24 | USD 81,838.70 | USD -4,605.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 78.76% | USD 663.34 | USD 74,957.00 | USD -4,666.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 78.76% | USD 654.24 | USD 73,928.70 | USD -4,675.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 113 | 81.42% | USD 810.29 | USD 91,563.00 | USD -11,602.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 113 | 81.42% | USD 801.19 | USD 90,534.70 | USD -11,611.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 113 | 81.42% | USD 775.29 | USD 87,608.00 | USD -11,637.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 113 | 81.42% | USD 766.19 | USD 86,579.70 | USD -11,646.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 113 | 80.53% | USD 740.29 | USD 83,653.00 | USD -11,672.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 113 | 80.53% | USD 731.19 | USD 82,624.70 | USD -11,681.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 113 | 79.65% | USD 670.29 | USD 75,743.00 | USD -11,742.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 113 | 79.65% | USD 661.19 | USD 74,714.70 | USD -11,751.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 81.42% | USD 810.29 | USD 91,563.00 | USD -11,602.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 81.42% | USD 801.19 | USD 90,534.70 | USD -11,611.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 81.42% | USD 775.29 | USD 87,608.00 | USD -11,637.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 81.42% | USD 766.19 | USD 86,579.70 | USD -11,646.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 80.53% | USD 740.29 | USD 83,653.00 | USD -11,672.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 80.53% | USD 731.19 | USD 82,624.70 | USD -11,681.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 79.65% | USD 670.29 | USD 75,743.00 | USD -11,742.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 79.65% | USD 661.19 | USD 74,714.70 | USD -11,751.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 81.42% | USD 810.29 | USD 91,563.00 | USD -11,602.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 81.42% | USD 801.19 | USD 90,534.70 | USD -11,611.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 81.42% | USD 775.29 | USD 87,608.00 | USD -11,637.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 81.42% | USD 766.19 | USD 86,579.70 | USD -11,646.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 80.53% | USD 740.29 | USD 83,653.00 | USD -11,672.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 80.53% | USD 731.19 | USD 82,624.70 | USD -11,681.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 79.65% | USD 670.29 | USD 75,743.00 | USD -11,742.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 79.65% | USD 661.19 | USD 74,714.70 | USD -11,751.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 112 | 83.04% | USD 1,172.11 | USD 131,276.00 | USD -8,852.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 112 | 83.04% | USD 1,163.01 | USD 130,256.80 | USD -8,861.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 112 | 83.04% | USD 1,137.11 | USD 127,356.00 | USD -8,887.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 112 | 83.04% | USD 1,128.01 | USD 126,336.80 | USD -8,896.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 112 | 82.14% | USD 1,102.11 | USD 123,436.00 | USD -8,922.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 112 | 82.14% | USD 1,093.01 | USD 122,416.80 | USD -8,931.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 112 | 82.14% | USD 1,032.11 | USD 115,596.00 | USD -8,992.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 112 | 82.14% | USD 1,023.01 | USD 114,576.80 | USD -9,001.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 83.04% | USD 1,172.11 | USD 131,276.00 | USD -8,852.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 83.04% | USD 1,163.01 | USD 130,256.80 | USD -8,861.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 83.04% | USD 1,137.11 | USD 127,356.00 | USD -8,887.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 83.04% | USD 1,128.01 | USD 126,336.80 | USD -8,896.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 82.14% | USD 1,102.11 | USD 123,436.00 | USD -8,922.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 82.14% | USD 1,093.01 | USD 122,416.80 | USD -8,931.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 82.14% | USD 1,032.11 | USD 115,596.00 | USD -8,992.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 82.14% | USD 1,023.01 | USD 114,576.80 | USD -9,001.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 83.04% | USD 1,172.11 | USD 131,276.00 | USD -8,852.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 83.04% | USD 1,163.01 | USD 130,256.80 | USD -8,861.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 83.04% | USD 1,137.11 | USD 127,356.00 | USD -8,887.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 83.04% | USD 1,128.01 | USD 126,336.80 | USD -8,896.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 82.14% | USD 1,102.11 | USD 123,436.00 | USD -8,922.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 82.14% | USD 1,093.01 | USD 122,416.80 | USD -8,931.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 82.14% | USD 1,032.11 | USD 115,596.00 | USD -8,992.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 82.14% | USD 1,023.01 | USD 114,576.80 | USD -9,001.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 115/115 (0) | 31.30% (23.55–40.27%) | USD -45.82 | USD -5,269.00 | USD -917.60 |
| HOLD_5_SESSIONS | 1 : 6 | 115/115 (0) | 67.83% (58.83–75.67%) | USD 54.29 | USD 6,243.50 | USD -17,184.10 |
| HOLD_5_SESSIONS | 6 : 1 | 115/115 (0) | 25.22% (18.17–33.87%) | USD -375.01 | USD -43,126.50 | USD -4,586.10 |
| HOLD_5_SESSIONS | 5 : 5 | 115/115 (0) | 31.30% (23.55–40.27%) | USD -229.09 | USD -26,345.00 | USD -4,588.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 115/115 (0) | 31.30% (23.55–40.27%) | USD -45.82 | USD -5,269.00 | USD -917.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 115/115 (0) | 67.83% (58.83–75.67%) | USD 54.29 | USD 6,243.50 | USD -17,184.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 115/115 (0) | 25.22% (18.17–33.87%) | USD -375.01 | USD -43,126.50 | USD -4,586.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 115/115 (0) | 31.30% (23.55–40.27%) | USD -229.09 | USD -26,345.00 | USD -4,588.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 115/115 (0) | 31.30% (23.55–40.27%) | USD -45.82 | USD -5,269.00 | USD -917.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 115/115 (0) | 67.83% (58.83–75.67%) | USD 54.29 | USD 6,243.50 | USD -17,184.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 115/115 (0) | 25.22% (18.17–33.87%) | USD -375.01 | USD -43,126.50 | USD -4,586.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 115/115 (0) | 31.30% (23.55–40.27%) | USD -229.09 | USD -26,345.00 | USD -4,588.00 |
| HOLD_10_SESSIONS | 1 : 1 | 113/115 (2) | 44.25% (35.43–53.44%) | USD -6.61 | USD -746.80 | USD -358.60 |
| HOLD_10_SESSIONS | 1 : 6 | 113/115 (2) | 80.53% (72.28–86.78%) | USD 724.24 | USD 81,838.70 | USD -4,605.10 |
| HOLD_10_SESSIONS | 6 : 1 | 113/115 (2) | 23.01% (16.21–31.58%) | USD -770.50 | USD -87,066.30 | USD -4,218.10 |
| HOLD_10_SESSIONS | 5 : 5 | 113/115 (2) | 44.25% (35.43–53.44%) | USD -33.04 | USD -3,734.00 | USD -1,793.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 44.25% (35.43–53.44%) | USD -6.61 | USD -746.80 | USD -358.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 80.53% (72.28–86.78%) | USD 724.24 | USD 81,838.70 | USD -4,605.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 23.01% (16.21–31.58%) | USD -770.50 | USD -87,066.30 | USD -4,218.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 44.25% (35.43–53.44%) | USD -33.04 | USD -3,734.00 | USD -1,793.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 44.25% (35.43–53.44%) | USD -6.61 | USD -746.80 | USD -358.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 80.53% (72.28–86.78%) | USD 724.24 | USD 81,838.70 | USD -4,605.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 23.01% (16.21–31.58%) | USD -770.50 | USD -87,066.30 | USD -4,218.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 44.25% (35.43–53.44%) | USD -33.04 | USD -3,734.00 | USD -1,793.00 |
| HOLD_15_SESSIONS | 1 : 1 | 113/115 (2) | 38.94% (30.45–48.15%) | USD -23.59 | USD -2,665.80 | USD -591.60 |
| HOLD_15_SESSIONS | 1 : 6 | 113/115 (2) | 80.53% (72.28–86.78%) | USD 731.19 | USD 82,624.70 | USD -11,681.10 |
| HOLD_15_SESSIONS | 6 : 1 | 113/115 (2) | 19.47% (13.22–27.72%) | USD -896.33 | USD -101,285.30 | USD -4,599.10 |
| HOLD_15_SESSIONS | 5 : 5 | 113/115 (2) | 38.94% (30.45–48.15%) | USD -117.96 | USD -13,329.00 | USD -2,958.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 38.94% (30.45–48.15%) | USD -23.59 | USD -2,665.80 | USD -591.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 80.53% (72.28–86.78%) | USD 731.19 | USD 82,624.70 | USD -11,681.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 19.47% (13.22–27.72%) | USD -896.33 | USD -101,285.30 | USD -4,599.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 38.94% (30.45–48.15%) | USD -117.96 | USD -13,329.00 | USD -2,958.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 38.94% (30.45–48.15%) | USD -23.59 | USD -2,665.80 | USD -591.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 80.53% (72.28–86.78%) | USD 731.19 | USD 82,624.70 | USD -11,681.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 19.47% (13.22–27.72%) | USD -896.33 | USD -101,285.30 | USD -4,599.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 38.94% (30.45–48.15%) | USD -117.96 | USD -13,329.00 | USD -2,958.00 |
| HOLD_20_SESSIONS | 1 : 1 | 112/115 (3) | 43.75% (34.92–52.99%) | USD -27.14 | USD -3,040.20 | USD -665.60 |
| HOLD_20_SESSIONS | 1 : 6 | 112/115 (3) | 82.14% (74.02–88.13%) | USD 1,093.01 | USD 122,416.80 | USD -8,931.10 |
| HOLD_20_SESSIONS | 6 : 1 | 112/115 (3) | 13.39% (8.29–20.93%) | USD -1,283.02 | USD -143,698.20 | USD -5,407.10 |
| HOLD_20_SESSIONS | 5 : 5 | 112/115 (3) | 43.75% (34.92–52.99%) | USD -135.72 | USD -15,201.00 | USD -3,328.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 112/115 (3) | 43.75% (34.92–52.99%) | USD -27.14 | USD -3,040.20 | USD -665.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 112/115 (3) | 82.14% (74.02–88.13%) | USD 1,093.01 | USD 122,416.80 | USD -8,931.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 112/115 (3) | 13.39% (8.29–20.93%) | USD -1,283.02 | USD -143,698.20 | USD -5,407.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 112/115 (3) | 43.75% (34.92–52.99%) | USD -135.72 | USD -15,201.00 | USD -3,328.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 112/115 (3) | 43.75% (34.92–52.99%) | USD -27.14 | USD -3,040.20 | USD -665.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 112/115 (3) | 82.14% (74.02–88.13%) | USD 1,093.01 | USD 122,416.80 | USD -8,931.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 112/115 (3) | 13.39% (8.29–20.93%) | USD -1,283.02 | USD -143,698.20 | USD -5,407.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 112/115 (3) | 43.75% (34.92–52.99%) | USD -135.72 | USD -15,201.00 | USD -3,328.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/115 | 0.00% | USD -209,772.04 | USD -330,767.55 |
| -75% | 0/115 | 0.00% | USD -154,110.80 | USD -244,156.30 |
| -50% | 0/115 | 0.00% | USD -98,449.55 | USD -157,545.05 |
| -40% | 0/115 | 0.00% | USD -76,185.06 | USD -122,900.55 |
| -30% | 0/115 | 0.00% | USD -53,920.56 | USD -88,256.05 |
| -25% | 0/115 | 0.00% | USD -42,788.31 | USD -70,933.80 |
| -20% | 0/115 | 0.00% | USD -31,656.06 | USD -53,611.55 |
| -15% | 0/115 | 0.00% | USD -20,523.82 | USD -36,289.30 |
| -10% | 6/115 | 5.22% | USD -9,411.49 | USD -21,263.55 |
| -5% | 72/115 | 62.61% | USD 621.29 | USD -7,343.55 |
| 0% | 115/115 | 100.00% | USD 2,743.70 | USD 865.45 |
| 5% | 115/115 | 100.00% | USD 2,743.70 | USD 865.45 |
| 10% | 115/115 | 100.00% | USD 2,743.70 | USD 865.45 |
| 20% | 115/115 | 100.00% | USD 2,743.70 | USD 865.45 |

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