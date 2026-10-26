# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 277.56 / USD 1,487.89; mean absolute mismatch USD 1,210.34; mean match score 18.71%.
- Actual selected contract ratios: {'1:6': 113}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 113; entered cohorts: 113; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 113/113 | 57/56/0 | 50.44% (41.36–59.49%) | USD -166.63 | USD 33.90 | USD -18,829.30 | USD -3,262.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 113/113 | 57/56/0 | 50.44% (41.36–59.49%) | USD -166.63 | USD 33.90 | USD -18,829.30 | USD -3,262.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 113/113 | 57/56/0 | 50.44% (41.36–59.49%) | USD -166.63 | USD 33.90 | USD -18,829.30 | USD -3,262.10 | 0 |
| HOLD_10_SESSIONS | 112/113 | 53/59/0 | 47.32% (38.32–56.50%) | USD -297.33 | USD -57.10 | USD -33,301.20 | USD -5,888.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 112/113 | 53/59/0 | 47.32% (38.32–56.50%) | USD -297.33 | USD -57.10 | USD -33,301.20 | USD -5,888.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 112/113 | 53/59/0 | 47.32% (38.32–56.50%) | USD -297.33 | USD -57.10 | USD -33,301.20 | USD -5,888.10 | 1 |
| HOLD_15_SESSIONS | 112/113 | 60/52/0 | 53.57% (44.37–62.54%) | USD -294.23 | USD 122.40 | USD -32,954.20 | USD -5,854.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 112/113 | 60/52/0 | 53.57% (44.37–62.54%) | USD -294.23 | USD 122.40 | USD -32,954.20 | USD -5,854.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 112/113 | 60/52/0 | 53.57% (44.37–62.54%) | USD -294.23 | USD 122.40 | USD -32,954.20 | USD -5,854.10 | 1 |
| HOLD_20_SESSIONS | 111/113 | 65/46/0 | 58.56% (49.26–67.29%) | USD -269.67 | USD 185.90 | USD -29,933.10 | USD -10,263.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 111/113 | 65/46/0 | 58.56% (49.26–67.29%) | USD -269.67 | USD 185.90 | USD -29,933.10 | USD -10,263.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 111/113 | 65/46/0 | 58.56% (49.26–67.29%) | USD -269.67 | USD 185.90 | USD -29,933.10 | USD -10,263.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -5.87 | USD -81.66 |
| HOLD_5_OR_DTE_LE_7 | USD -5.87 | USD -81.66 |
| HOLD_5_OR_DTE_LE_14 | USD -5.87 | USD -81.66 |
| HOLD_10_SESSIONS | USD 21.29 | USD -239.52 |
| HOLD_10_OR_DTE_LE_7 | USD 21.29 | USD -239.52 |
| HOLD_10_OR_DTE_LE_14 | USD 21.29 | USD -239.52 |
| HOLD_15_SESSIONS | USD 12.22 | USD -227.36 |
| HOLD_15_OR_DTE_LE_7 | USD 12.22 | USD -227.36 |
| HOLD_15_OR_DTE_LE_14 | USD 12.22 | USD -227.36 |
| HOLD_20_SESSIONS | USD 4.46 | USD -195.03 |
| HOLD_20_OR_DTE_LE_7 | USD 4.46 | USD -195.03 |
| HOLD_20_OR_DTE_LE_14 | USD 4.46 | USD -195.03 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 113 | 57.52% | USD -87.53 | USD -9,891.00 | USD -3,183.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 113 | 57.52% | USD -96.63 | USD -10,919.30 | USD -3,192.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 113 | 56.64% | USD -122.53 | USD -13,846.00 | USD -3,218.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 113 | 55.75% | USD -131.63 | USD -14,874.30 | USD -3,227.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 113 | 53.10% | USD -157.53 | USD -17,801.00 | USD -3,253.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 113 | 50.44% | USD -166.63 | USD -18,829.30 | USD -3,262.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 113 | 47.79% | USD -227.53 | USD -25,711.00 | USD -3,323.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 113 | 47.79% | USD -236.63 | USD -26,739.30 | USD -3,332.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 57.52% | USD -87.53 | USD -9,891.00 | USD -3,183.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 57.52% | USD -96.63 | USD -10,919.30 | USD -3,192.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 56.64% | USD -122.53 | USD -13,846.00 | USD -3,218.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 55.75% | USD -131.63 | USD -14,874.30 | USD -3,227.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 53.10% | USD -157.53 | USD -17,801.00 | USD -3,253.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 50.44% | USD -166.63 | USD -18,829.30 | USD -3,262.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 47.79% | USD -227.53 | USD -25,711.00 | USD -3,323.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 47.79% | USD -236.63 | USD -26,739.30 | USD -3,332.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 57.52% | USD -87.53 | USD -9,891.00 | USD -3,183.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 57.52% | USD -96.63 | USD -10,919.30 | USD -3,192.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 56.64% | USD -122.53 | USD -13,846.00 | USD -3,218.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 55.75% | USD -131.63 | USD -14,874.30 | USD -3,227.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 53.10% | USD -157.53 | USD -17,801.00 | USD -3,253.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 50.44% | USD -166.63 | USD -18,829.30 | USD -3,262.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 47.79% | USD -227.53 | USD -25,711.00 | USD -3,323.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 47.79% | USD -236.63 | USD -26,739.30 | USD -3,332.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 112 | 50.89% | USD -218.23 | USD -24,442.00 | USD -5,809.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 112 | 50.89% | USD -227.33 | USD -25,461.20 | USD -5,818.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 112 | 48.21% | USD -253.23 | USD -28,362.00 | USD -5,844.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 112 | 47.32% | USD -262.33 | USD -29,381.20 | USD -5,853.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 112 | 47.32% | USD -288.23 | USD -32,282.00 | USD -5,879.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 112 | 47.32% | USD -297.33 | USD -33,301.20 | USD -5,888.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 112 | 45.54% | USD -358.23 | USD -40,122.00 | USD -5,949.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 112 | 44.64% | USD -367.33 | USD -41,141.20 | USD -5,958.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 50.89% | USD -218.23 | USD -24,442.00 | USD -5,809.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 50.89% | USD -227.33 | USD -25,461.20 | USD -5,818.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 48.21% | USD -253.23 | USD -28,362.00 | USD -5,844.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 47.32% | USD -262.33 | USD -29,381.20 | USD -5,853.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 47.32% | USD -288.23 | USD -32,282.00 | USD -5,879.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 47.32% | USD -297.33 | USD -33,301.20 | USD -5,888.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 45.54% | USD -358.23 | USD -40,122.00 | USD -5,949.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 44.64% | USD -367.33 | USD -41,141.20 | USD -5,958.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 50.89% | USD -218.23 | USD -24,442.00 | USD -5,809.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 50.89% | USD -227.33 | USD -25,461.20 | USD -5,818.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 48.21% | USD -253.23 | USD -28,362.00 | USD -5,844.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 47.32% | USD -262.33 | USD -29,381.20 | USD -5,853.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 47.32% | USD -288.23 | USD -32,282.00 | USD -5,879.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 47.32% | USD -297.33 | USD -33,301.20 | USD -5,888.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 45.54% | USD -358.23 | USD -40,122.00 | USD -5,949.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 44.64% | USD -367.33 | USD -41,141.20 | USD -5,958.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 112 | 54.46% | USD -215.13 | USD -24,095.00 | USD -5,775.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 112 | 53.57% | USD -224.23 | USD -25,114.20 | USD -5,784.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 112 | 53.57% | USD -250.13 | USD -28,015.00 | USD -5,810.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 112 | 53.57% | USD -259.23 | USD -29,034.20 | USD -5,819.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 112 | 53.57% | USD -285.13 | USD -31,935.00 | USD -5,845.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 112 | 53.57% | USD -294.23 | USD -32,954.20 | USD -5,854.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 112 | 51.79% | USD -355.13 | USD -39,775.00 | USD -5,915.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 112 | 51.79% | USD -364.23 | USD -40,794.20 | USD -5,924.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 54.46% | USD -215.13 | USD -24,095.00 | USD -5,775.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 53.57% | USD -224.23 | USD -25,114.20 | USD -5,784.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 53.57% | USD -250.13 | USD -28,015.00 | USD -5,810.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 53.57% | USD -259.23 | USD -29,034.20 | USD -5,819.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 53.57% | USD -285.13 | USD -31,935.00 | USD -5,845.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 53.57% | USD -294.23 | USD -32,954.20 | USD -5,854.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 51.79% | USD -355.13 | USD -39,775.00 | USD -5,915.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 51.79% | USD -364.23 | USD -40,794.20 | USD -5,924.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 54.46% | USD -215.13 | USD -24,095.00 | USD -5,775.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 53.57% | USD -224.23 | USD -25,114.20 | USD -5,784.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 53.57% | USD -250.13 | USD -28,015.00 | USD -5,810.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 53.57% | USD -259.23 | USD -29,034.20 | USD -5,819.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 53.57% | USD -285.13 | USD -31,935.00 | USD -5,845.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 53.57% | USD -294.23 | USD -32,954.20 | USD -5,854.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 51.79% | USD -355.13 | USD -39,775.00 | USD -5,915.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 51.79% | USD -364.23 | USD -40,794.20 | USD -5,924.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 111 | 60.36% | USD -190.57 | USD -21,153.00 | USD -10,184.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 111 | 59.46% | USD -199.67 | USD -22,163.10 | USD -10,193.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 111 | 59.46% | USD -225.57 | USD -25,038.00 | USD -10,219.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 111 | 59.46% | USD -234.67 | USD -26,048.10 | USD -10,228.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 111 | 58.56% | USD -260.57 | USD -28,923.00 | USD -10,254.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 111 | 58.56% | USD -269.67 | USD -29,933.10 | USD -10,263.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 111 | 56.76% | USD -330.57 | USD -36,693.00 | USD -10,324.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 111 | 55.86% | USD -339.67 | USD -37,703.10 | USD -10,333.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 111 | 60.36% | USD -190.57 | USD -21,153.00 | USD -10,184.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 111 | 59.46% | USD -199.67 | USD -22,163.10 | USD -10,193.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 111 | 59.46% | USD -225.57 | USD -25,038.00 | USD -10,219.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 111 | 59.46% | USD -234.67 | USD -26,048.10 | USD -10,228.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 111 | 58.56% | USD -260.57 | USD -28,923.00 | USD -10,254.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 111 | 58.56% | USD -269.67 | USD -29,933.10 | USD -10,263.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 111 | 56.76% | USD -330.57 | USD -36,693.00 | USD -10,324.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 111 | 55.86% | USD -339.67 | USD -37,703.10 | USD -10,333.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 111 | 60.36% | USD -190.57 | USD -21,153.00 | USD -10,184.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 111 | 59.46% | USD -199.67 | USD -22,163.10 | USD -10,193.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 111 | 59.46% | USD -225.57 | USD -25,038.00 | USD -10,219.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 111 | 59.46% | USD -234.67 | USD -26,048.10 | USD -10,228.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 111 | 58.56% | USD -260.57 | USD -28,923.00 | USD -10,254.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 111 | 58.56% | USD -269.67 | USD -29,933.10 | USD -10,263.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 111 | 56.76% | USD -330.57 | USD -36,693.00 | USD -10,324.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 111 | 55.86% | USD -339.67 | USD -37,703.10 | USD -10,333.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 113/113 (0) | 23.89% (16.97–32.53%) | USD -42.08 | USD -4,754.80 | USD -426.60 |
| HOLD_5_SESSIONS | 1 : 6 | 113/113 (0) | 50.44% (41.36–59.49%) | USD -166.63 | USD -18,829.30 | USD -3,262.10 |
| HOLD_5_SESSIONS | 6 : 1 | 113/113 (0) | 34.51% (26.39–43.66%) | USD -127.91 | USD -14,454.30 | USD -1,895.10 |
| HOLD_5_SESSIONS | 5 : 5 | 113/113 (0) | 23.89% (16.97–32.53%) | USD -210.39 | USD -23,774.00 | USD -2,133.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 113/113 (0) | 23.89% (16.97–32.53%) | USD -42.08 | USD -4,754.80 | USD -426.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 113/113 (0) | 50.44% (41.36–59.49%) | USD -166.63 | USD -18,829.30 | USD -3,262.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 113/113 (0) | 34.51% (26.39–43.66%) | USD -127.91 | USD -14,454.30 | USD -1,895.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 113/113 (0) | 23.89% (16.97–32.53%) | USD -210.39 | USD -23,774.00 | USD -2,133.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 113/113 (0) | 23.89% (16.97–32.53%) | USD -42.08 | USD -4,754.80 | USD -426.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 113/113 (0) | 50.44% (41.36–59.49%) | USD -166.63 | USD -18,829.30 | USD -3,262.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 113/113 (0) | 34.51% (26.39–43.66%) | USD -127.91 | USD -14,454.30 | USD -1,895.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 113/113 (0) | 23.89% (16.97–32.53%) | USD -210.39 | USD -23,774.00 | USD -2,133.00 |
| HOLD_10_SESSIONS | 1 : 1 | 112/113 (1) | 27.68% (20.24–36.60%) | USD -41.23 | USD -4,618.20 | USD -696.60 |
| HOLD_10_SESSIONS | 1 : 6 | 112/113 (1) | 47.32% (38.32–56.50%) | USD -297.33 | USD -33,301.20 | USD -5,888.10 |
| HOLD_10_SESSIONS | 6 : 1 | 112/113 (1) | 39.29% (30.74–48.54%) | USD 8.69 | USD 973.80 | USD -2,108.10 |
| HOLD_10_SESSIONS | 5 : 5 | 112/113 (1) | 27.68% (20.24–36.60%) | USD -206.17 | USD -23,091.00 | USD -3,483.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 112/113 (1) | 27.68% (20.24–36.60%) | USD -41.23 | USD -4,618.20 | USD -696.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 112/113 (1) | 47.32% (38.32–56.50%) | USD -297.33 | USD -33,301.20 | USD -5,888.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 112/113 (1) | 39.29% (30.74–48.54%) | USD 8.69 | USD 973.80 | USD -2,108.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 112/113 (1) | 27.68% (20.24–36.60%) | USD -206.17 | USD -23,091.00 | USD -3,483.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 112/113 (1) | 27.68% (20.24–36.60%) | USD -41.23 | USD -4,618.20 | USD -696.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 112/113 (1) | 47.32% (38.32–56.50%) | USD -297.33 | USD -33,301.20 | USD -5,888.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 112/113 (1) | 39.29% (30.74–48.54%) | USD 8.69 | USD 973.80 | USD -2,108.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 112/113 (1) | 27.68% (20.24–36.60%) | USD -206.17 | USD -23,091.00 | USD -3,483.00 |
| HOLD_15_SESSIONS | 1 : 1 | 112/113 (1) | 29.46% (21.82–38.47%) | USD -48.27 | USD -5,406.20 | USD -552.60 |
| HOLD_15_SESSIONS | 1 : 6 | 112/113 (1) | 53.57% (44.37–62.54%) | USD -294.23 | USD -32,954.20 | USD -5,854.10 |
| HOLD_15_SESSIONS | 6 : 1 | 112/113 (1) | 31.25% (23.41–40.34%) | USD -43.65 | USD -4,889.20 | USD -2,201.10 |
| HOLD_15_SESSIONS | 5 : 5 | 112/113 (1) | 29.46% (21.82–38.47%) | USD -241.35 | USD -27,031.00 | USD -2,763.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 112/113 (1) | 29.46% (21.82–38.47%) | USD -48.27 | USD -5,406.20 | USD -552.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 112/113 (1) | 53.57% (44.37–62.54%) | USD -294.23 | USD -32,954.20 | USD -5,854.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 112/113 (1) | 31.25% (23.41–40.34%) | USD -43.65 | USD -4,889.20 | USD -2,201.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 112/113 (1) | 29.46% (21.82–38.47%) | USD -241.35 | USD -27,031.00 | USD -2,763.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 112/113 (1) | 29.46% (21.82–38.47%) | USD -48.27 | USD -5,406.20 | USD -552.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 112/113 (1) | 53.57% (44.37–62.54%) | USD -294.23 | USD -32,954.20 | USD -5,854.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 112/113 (1) | 31.25% (23.41–40.34%) | USD -43.65 | USD -4,889.20 | USD -2,201.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 112/113 (1) | 29.46% (21.82–38.47%) | USD -241.35 | USD -27,031.00 | USD -2,763.00 |
| HOLD_20_SESSIONS | 1 : 1 | 111/113 (2) | 32.43% (24.44–41.60%) | USD -50.65 | USD -5,621.60 | USD -764.60 |
| HOLD_20_SESSIONS | 1 : 6 | 111/113 (2) | 58.56% (49.26–67.29%) | USD -269.67 | USD -29,933.10 | USD -10,263.10 |
| HOLD_20_SESSIONS | 6 : 1 | 111/113 (2) | 35.14% (26.89–44.38%) | USD -84.85 | USD -9,418.10 | USD -2,390.10 |
| HOLD_20_SESSIONS | 5 : 5 | 111/113 (2) | 32.43% (24.44–41.60%) | USD -253.23 | USD -28,108.00 | USD -3,823.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 111/113 (2) | 32.43% (24.44–41.60%) | USD -50.65 | USD -5,621.60 | USD -764.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 111/113 (2) | 58.56% (49.26–67.29%) | USD -269.67 | USD -29,933.10 | USD -10,263.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 111/113 (2) | 35.14% (26.89–44.38%) | USD -84.85 | USD -9,418.10 | USD -2,390.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 111/113 (2) | 32.43% (24.44–41.60%) | USD -253.23 | USD -28,108.00 | USD -3,823.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 111/113 (2) | 32.43% (24.44–41.60%) | USD -50.65 | USD -5,621.60 | USD -764.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 111/113 (2) | 58.56% (49.26–67.29%) | USD -269.67 | USD -29,933.10 | USD -10,263.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 111/113 (2) | 35.14% (26.89–44.38%) | USD -84.85 | USD -9,418.10 | USD -2,390.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 111/113 (2) | 32.43% (24.44–41.60%) | USD -253.23 | USD -28,108.00 | USD -3,823.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -75% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -50% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -40% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -30% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -25% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -20% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -15% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -10% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| -5% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| 0% | 113/113 | 100.00% | USD 1,170.79 | USD 273.45 |
| 5% | 70/113 | 61.95% | USD 44.50 | USD -4,079.35 |
| 10% | 4/113 | 3.54% | USD -9,873.45 | USD -18,674.55 |
| 20% | 1/113 | 0.89% | USD -31,728.40 | USD -52,737.95 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short call can dominate downside even when QQQ long call appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.