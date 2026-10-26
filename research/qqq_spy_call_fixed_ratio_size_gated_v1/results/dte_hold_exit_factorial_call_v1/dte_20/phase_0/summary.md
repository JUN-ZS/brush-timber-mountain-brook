# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 155.70 / USD 845.57; mean absolute mismatch USD 689.87; mean match score 19.24%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 195/196 | 115/80/0 | 58.97% (51.96–65.64%) | USD -88.67 | USD 91.90 | USD -17,290.50 | USD -4,688.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 195/196 | 115/80/0 | 58.97% (51.96–65.64%) | USD -89.09 | USD 91.90 | USD -17,372.50 | USD -4,688.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 195/196 | 113/82/0 | 57.95% (50.93–64.66%) | USD -76.79 | USD 61.90 | USD -14,973.50 | USD -4,688.10 | 1 |
| HOLD_10_SESSIONS | 148/196 | 90/58/0 | 60.81% (52.77–68.31%) | USD -322.46 | USD 206.90 | USD -47,724.80 | USD -7,125.10 | 48 |
| HOLD_10_OR_DTE_LE_7 | 178/196 | 110/68/0 | 61.80% (54.48–68.61%) | USD -164.48 | USD 203.40 | USD -29,276.80 | USD -8,023.10 | 18 |
| HOLD_10_OR_DTE_LE_14 | 195/196 | 114/81/0 | 58.46% (51.45–65.15%) | USD -65.80 | USD 74.90 | USD -12,831.50 | USD -4,688.10 | 1 |
| HOLD_15_SESSIONS | 2/196 | 0/2/0 | 0.00% (0.00–65.76%) | USD -1,550.60 | USD -1,550.60 | USD -3,101.20 | USD -1,801.10 | 194 |
| HOLD_15_OR_DTE_LE_7 | 177/196 | 110/67/0 | 62.15% (54.82–68.96%) | USD -183.30 | USD 178.90 | USD -32,443.70 | USD -8,023.10 | 19 |
| HOLD_15_OR_DTE_LE_14 | 195/196 | 114/81/0 | 58.46% (51.45–65.15%) | USD -65.80 | USD 74.90 | USD -12,831.50 | USD -4,688.10 | 1 |
| HOLD_20_SESSIONS | 0/196 | 0/0/0 | — | — | — | — | — | 196 |
| HOLD_20_OR_DTE_LE_7 | 177/196 | 110/67/0 | 62.15% (54.82–68.96%) | USD -183.30 | USD 178.90 | USD -32,443.70 | USD -8,023.10 | 19 |
| HOLD_20_OR_DTE_LE_14 | 195/196 | 114/81/0 | 58.46% (51.45–65.15%) | USD -65.80 | USD 74.90 | USD -12,831.50 | USD -4,688.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 0.74 | USD -10.31 |
| HOLD_5_OR_DTE_LE_7 | USD 0.93 | USD -10.92 |
| HOLD_5_OR_DTE_LE_14 | USD -0.79 | USD 3.11 |
| HOLD_10_SESSIONS | USD 56.11 | USD -299.47 |
| HOLD_10_OR_DTE_LE_7 | USD 24.04 | USD -109.42 |
| HOLD_10_OR_DTE_LE_14 | USD -1.41 | USD 14.71 |
| HOLD_15_SESSIONS | USD 214.50 | USD -1,686.00 |
| HOLD_15_OR_DTE_LE_7 | USD 29.06 | USD -133.25 |
| HOLD_15_OR_DTE_LE_14 | USD -1.41 | USD 14.71 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD 29.06 | USD -133.25 |
| HOLD_20_OR_DTE_LE_14 | USD -1.41 | USD 14.71 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 195 | 64.62% | USD -9.57 | USD -1,866.00 | USD -4,609.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 195 | 64.10% | USD -18.67 | USD -3,640.50 | USD -4,618.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 195 | 61.03% | USD -44.57 | USD -8,691.00 | USD -4,644.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 195 | 61.03% | USD -53.67 | USD -10,465.50 | USD -4,653.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 195 | 58.97% | USD -79.57 | USD -15,516.00 | USD -4,679.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 195 | 58.97% | USD -88.67 | USD -17,290.50 | USD -4,688.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 195 | 53.33% | USD -149.57 | USD -29,166.00 | USD -4,749.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 195 | 51.28% | USD -158.67 | USD -30,940.50 | USD -4,758.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 195 | 64.62% | USD -9.99 | USD -1,948.00 | USD -4,609.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 195 | 64.10% | USD -19.09 | USD -3,722.50 | USD -4,618.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 195 | 61.03% | USD -44.99 | USD -8,773.00 | USD -4,644.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 195 | 61.03% | USD -54.09 | USD -10,547.50 | USD -4,653.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 195 | 58.97% | USD -79.99 | USD -15,598.00 | USD -4,679.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 195 | 58.97% | USD -89.09 | USD -17,372.50 | USD -4,688.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 195 | 53.33% | USD -149.99 | USD -29,248.00 | USD -4,749.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 195 | 51.28% | USD -159.09 | USD -31,022.50 | USD -4,758.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 62.56% | USD 2.31 | USD 451.00 | USD -4,609.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 62.05% | USD -6.79 | USD -1,323.50 | USD -4,618.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 59.49% | USD -32.69 | USD -6,374.00 | USD -4,644.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 58.97% | USD -41.79 | USD -8,148.50 | USD -4,653.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 57.95% | USD -67.69 | USD -13,199.00 | USD -4,679.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 57.95% | USD -76.79 | USD -14,973.50 | USD -4,688.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 50.26% | USD -137.69 | USD -26,849.00 | USD -4,749.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 49.23% | USD -146.79 | USD -28,623.50 | USD -4,758.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 148 | 62.84% | USD -243.36 | USD -36,018.00 | USD -7,046.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 148 | 62.84% | USD -252.46 | USD -37,364.80 | USD -7,055.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 148 | 61.49% | USD -278.36 | USD -41,198.00 | USD -7,081.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 148 | 61.49% | USD -287.46 | USD -42,544.80 | USD -7,090.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 148 | 60.81% | USD -313.36 | USD -46,378.00 | USD -7,116.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 148 | 60.81% | USD -322.46 | USD -47,724.80 | USD -7,125.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 148 | 59.46% | USD -383.36 | USD -56,738.00 | USD -7,186.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 148 | 58.78% | USD -392.46 | USD -58,084.80 | USD -7,195.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 178 | 65.73% | USD -85.38 | USD -15,197.00 | USD -7,944.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 178 | 65.73% | USD -94.48 | USD -16,816.80 | USD -7,953.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 178 | 64.61% | USD -120.38 | USD -21,427.00 | USD -7,979.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 178 | 64.04% | USD -129.48 | USD -23,046.80 | USD -7,988.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 178 | 62.36% | USD -155.38 | USD -27,657.00 | USD -8,014.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 178 | 61.80% | USD -164.48 | USD -29,276.80 | USD -8,023.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 178 | 59.55% | USD -225.38 | USD -40,117.00 | USD -8,084.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 178 | 59.55% | USD -234.48 | USD -41,736.80 | USD -8,093.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 62.56% | USD 13.30 | USD 2,593.00 | USD -4,609.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 62.05% | USD 4.20 | USD 818.50 | USD -4,618.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 60.00% | USD -21.70 | USD -4,232.00 | USD -4,644.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 59.49% | USD -30.80 | USD -6,006.50 | USD -4,653.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 58.46% | USD -56.70 | USD -11,057.00 | USD -4,679.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 58.46% | USD -65.80 | USD -12,831.50 | USD -4,688.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 50.77% | USD -126.70 | USD -24,707.00 | USD -4,749.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 50.26% | USD -135.80 | USD -26,481.50 | USD -4,758.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 2 | 0.00% | USD -1,471.50 | USD -2,943.00 | USD -1,722.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 2 | 0.00% | USD -1,480.60 | USD -2,961.20 | USD -1,731.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 2 | 0.00% | USD -1,506.50 | USD -3,013.00 | USD -1,757.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 2 | 0.00% | USD -1,515.60 | USD -3,031.20 | USD -1,766.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 2 | 0.00% | USD -1,541.50 | USD -3,083.00 | USD -1,792.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 2 | 0.00% | USD -1,550.60 | USD -3,101.20 | USD -1,801.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 2 | 0.00% | USD -1,611.50 | USD -3,223.00 | USD -1,862.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 2 | 0.00% | USD -1,620.60 | USD -3,241.20 | USD -1,871.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 177 | 66.10% | USD -104.20 | USD -18,443.00 | USD -7,944.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 177 | 66.10% | USD -113.30 | USD -20,053.70 | USD -7,953.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 177 | 64.97% | USD -139.20 | USD -24,638.00 | USD -7,979.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 177 | 64.41% | USD -148.30 | USD -26,248.70 | USD -7,988.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 177 | 62.71% | USD -174.20 | USD -30,833.00 | USD -8,014.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 177 | 62.15% | USD -183.30 | USD -32,443.70 | USD -8,023.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 177 | 59.32% | USD -244.20 | USD -43,223.00 | USD -8,084.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 177 | 59.32% | USD -253.30 | USD -44,833.70 | USD -8,093.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 62.56% | USD 13.30 | USD 2,593.00 | USD -4,609.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 62.05% | USD 4.20 | USD 818.50 | USD -4,618.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 60.00% | USD -21.70 | USD -4,232.00 | USD -4,644.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 59.49% | USD -30.80 | USD -6,006.50 | USD -4,653.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 58.46% | USD -56.70 | USD -11,057.00 | USD -4,679.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 58.46% | USD -65.80 | USD -12,831.50 | USD -4,688.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 50.77% | USD -126.70 | USD -24,707.00 | USD -4,749.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 50.26% | USD -135.80 | USD -26,481.50 | USD -4,758.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 177 | 66.10% | USD -104.20 | USD -18,443.00 | USD -7,944.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 177 | 66.10% | USD -113.30 | USD -20,053.70 | USD -7,953.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 177 | 64.97% | USD -139.20 | USD -24,638.00 | USD -7,979.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 177 | 64.41% | USD -148.30 | USD -26,248.70 | USD -7,988.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 177 | 62.71% | USD -174.20 | USD -30,833.00 | USD -8,014.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 177 | 62.15% | USD -183.30 | USD -32,443.70 | USD -8,023.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 177 | 59.32% | USD -244.20 | USD -43,223.00 | USD -8,084.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 177 | 59.32% | USD -253.30 | USD -44,833.70 | USD -8,093.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 62.56% | USD 13.30 | USD 2,593.00 | USD -4,609.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 62.05% | USD 4.20 | USD 818.50 | USD -4,618.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 60.00% | USD -21.70 | USD -4,232.00 | USD -4,644.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 59.49% | USD -30.80 | USD -6,006.50 | USD -4,653.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 58.46% | USD -56.70 | USD -11,057.00 | USD -4,679.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 58.46% | USD -65.80 | USD -12,831.50 | USD -4,688.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 50.77% | USD -126.70 | USD -24,707.00 | USD -4,749.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 50.26% | USD -135.80 | USD -26,481.50 | USD -4,758.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 195/196 (1) | 28.21% (22.36–34.90%) | USD -23.58 | USD -4,598.00 | USD -303.60 |
| HOLD_5_SESSIONS | 1 : 6 | 195/196 (1) | 58.97% (51.96–65.64%) | USD -88.67 | USD -17,290.50 | USD -4,688.10 |
| HOLD_5_SESSIONS | 6 : 1 | 195/196 (1) | 31.28% (25.19–38.10%) | USD -76.39 | USD -14,895.50 | USD -1,978.10 |
| HOLD_5_SESSIONS | 5 : 5 | 195/196 (1) | 28.21% (22.36–34.90%) | USD -117.90 | USD -22,990.00 | USD -1,518.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 195/196 (1) | 28.21% (22.36–34.90%) | USD -23.49 | USD -4,580.00 | USD -303.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 195/196 (1) | 58.97% (51.96–65.64%) | USD -89.09 | USD -17,372.50 | USD -4,688.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 195/196 (1) | 31.28% (25.19–38.10%) | USD -75.32 | USD -14,687.50 | USD -1,978.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 195/196 (1) | 28.21% (22.36–34.90%) | USD -117.44 | USD -22,900.00 | USD -1,518.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.21% (22.36–34.90%) | USD -22.88 | USD -4,461.00 | USD -262.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 57.95% (50.93–64.66%) | USD -76.79 | USD -14,973.50 | USD -4,688.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 31.28% (25.19–38.10%) | USD -83.35 | USD -16,253.50 | USD -1,978.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.21% (22.36–34.90%) | USD -114.38 | USD -22,305.00 | USD -1,313.00 |
| HOLD_10_SESSIONS | 1 : 1 | 148/196 (48) | 33.11% (26.04–41.03%) | USD -16.40 | USD -2,427.80 | USD -918.60 |
| HOLD_10_SESSIONS | 1 : 6 | 148/196 (48) | 60.81% (52.77–68.31%) | USD -322.46 | USD -47,724.80 | USD -7,125.10 |
| HOLD_10_SESSIONS | 6 : 1 | 148/196 (48) | 29.73% (22.95–37.53%) | USD 207.64 | USD 30,730.20 | USD -1,786.10 |
| HOLD_10_SESSIONS | 5 : 5 | 148/196 (48) | 33.11% (26.04–41.03%) | USD -82.02 | USD -12,139.00 | USD -4,593.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 178/196 (18) | 26.40% (20.48–33.33%) | USD -16.80 | USD -2,989.80 | USD -1,191.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 178/196 (18) | 61.80% (54.48–68.61%) | USD -164.48 | USD -29,276.80 | USD -8,023.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 178/196 (18) | 31.46% (25.09–38.61%) | USD 46.90 | USD 8,348.20 | USD -1,908.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 178/196 (18) | 26.40% (20.48–33.33%) | USD -83.98 | USD -14,949.00 | USD -5,958.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -21.56 | USD -4,204.00 | USD -262.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 58.46% (51.45–65.15%) | USD -65.80 | USD -12,831.50 | USD -4,688.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 30.77% (24.71–37.57%) | USD -85.11 | USD -16,596.50 | USD -1,696.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -107.79 | USD -21,020.00 | USD -1,313.00 |
| HOLD_15_SESSIONS | 1 : 1 | 2/196 (194) | 50.00% (9.45–90.55%) | USD -89.10 | USD -178.20 | USD -179.60 |
| HOLD_15_SESSIONS | 1 : 6 | 2/196 (194) | 0.00% (0.00–65.76%) | USD -1,550.60 | USD -3,101.20 | USD -1,801.10 |
| HOLD_15_SESSIONS | 6 : 1 | 2/196 (194) | 100.00% (34.24–100.00%) | USD 926.90 | USD 1,853.80 | USD 543.90 |
| HOLD_15_SESSIONS | 5 : 5 | 2/196 (194) | 50.00% (9.45–90.55%) | USD -445.50 | USD -891.00 | USD -898.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 177/196 (19) | 26.55% (20.60–33.51%) | USD -15.75 | USD -2,788.20 | USD -1,191.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 177/196 (19) | 62.15% (54.82–68.96%) | USD -183.30 | USD -32,443.70 | USD -8,023.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 177/196 (19) | 32.20% (25.76–39.40%) | USD 73.03 | USD 12,926.30 | USD -1,908.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 177/196 (19) | 26.55% (20.60–33.51%) | USD -78.76 | USD -13,941.00 | USD -5,958.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -21.56 | USD -4,204.00 | USD -262.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 58.46% (51.45–65.15%) | USD -65.80 | USD -12,831.50 | USD -4,688.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 30.77% (24.71–37.57%) | USD -85.11 | USD -16,596.50 | USD -1,696.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -107.79 | USD -21,020.00 | USD -1,313.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/196 (196) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 177/196 (19) | 26.55% (20.60–33.51%) | USD -15.75 | USD -2,788.20 | USD -1,191.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 177/196 (19) | 62.15% (54.82–68.96%) | USD -183.30 | USD -32,443.70 | USD -8,023.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 177/196 (19) | 32.20% (25.76–39.40%) | USD 73.03 | USD 12,926.30 | USD -1,908.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 177/196 (19) | 26.55% (20.60–33.51%) | USD -78.76 | USD -13,941.00 | USD -5,958.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -21.56 | USD -4,204.00 | USD -262.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 58.46% (51.45–65.15%) | USD -65.80 | USD -12,831.50 | USD -4,688.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 30.77% (24.71–37.57%) | USD -85.11 | USD -16,596.50 | USD -1,696.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -107.79 | USD -21,020.00 | USD -1,313.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -75% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -50% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -40% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -30% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -25% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -20% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -15% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -10% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -5% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| 0% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| 5% | 20/196 | 10.20% | USD -4,449.82 | USD -10,235.90 |
| 10% | 1/196 | 0.51% | USD -15,087.69 | USD -27,294.75 |
| 20% | 0/196 | 0.00% | USD -36,586.91 | USD -62,092.95 |

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