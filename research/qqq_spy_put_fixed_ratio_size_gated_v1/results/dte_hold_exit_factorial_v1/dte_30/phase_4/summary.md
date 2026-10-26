# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 367.88 / USD 2,160.31; mean absolute mismatch USD 1,792.43; mean match score 17.03%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/195 | 144/50/0 | 74.23% (67.64–79.87%) | USD 143.18 | USD 483.90 | USD 27,776.60 | USD -19,044.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 194/195 | 144/50/0 | 74.23% (67.64–79.87%) | USD 143.18 | USD 483.90 | USD 27,776.60 | USD -19,044.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 144/50/0 | 74.23% (67.64–79.87%) | USD 143.18 | USD 483.90 | USD 27,776.60 | USD -19,044.10 | 1 |
| HOLD_10_SESSIONS | 193/195 | 156/37/0 | 80.83% (74.70–85.76%) | USD 158.10 | USD 839.90 | USD 30,512.70 | USD -25,764.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 193/195 | 156/37/0 | 80.83% (74.70–85.76%) | USD 158.10 | USD 839.90 | USD 30,512.70 | USD -25,764.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 194/195 | 155/39/0 | 79.90% (73.70–84.93%) | USD 166.10 | USD 836.90 | USD 32,223.60 | USD -22,302.10 | 1 |
| HOLD_15_SESSIONS | 182/195 | 149/33/0 | 81.87% (75.63–86.79%) | USD 413.88 | USD 1,128.40 | USD 75,325.80 | USD -42,588.10 | 13 |
| HOLD_15_OR_DTE_LE_7 | 189/195 | 157/32/0 | 83.07% (77.08–87.74%) | USD 472.26 | USD 1,124.90 | USD 89,257.10 | USD -42,588.10 | 6 |
| HOLD_15_OR_DTE_LE_14 | 194/195 | 158/36/0 | 81.44% (75.38–86.28%) | USD 76.58 | USD 904.90 | USD 14,856.60 | USD -31,847.10 | 1 |
| HOLD_20_SESSIONS | 23/195 | 11/12/0 | 47.83% (29.24–67.04%) | USD -3,574.88 | USD -484.10 | USD -82,222.30 | USD -47,260.10 | 172 |
| HOLD_20_OR_DTE_LE_7 | 180/195 | 150/30/0 | 83.33% (77.20–88.07%) | USD 445.49 | USD 1,130.40 | USD 80,188.00 | USD -45,908.10 | 15 |
| HOLD_20_OR_DTE_LE_14 | 194/195 | 158/36/0 | 81.44% (75.38–86.28%) | USD 76.58 | USD 904.90 | USD 14,856.60 | USD -31,847.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -70.24 | USD 292.52 |
| HOLD_5_OR_DTE_LE_7 | USD -70.24 | USD 292.52 |
| HOLD_5_OR_DTE_LE_14 | USD -70.24 | USD 292.52 |
| HOLD_10_SESSIONS | USD -80.77 | USD 317.97 |
| HOLD_10_OR_DTE_LE_7 | USD -80.77 | USD 317.97 |
| HOLD_10_OR_DTE_LE_14 | USD -89.44 | USD 334.64 |
| HOLD_15_SESSIONS | USD -138.90 | USD 631.88 |
| HOLD_15_OR_DTE_LE_7 | USD -139.21 | USD 690.57 |
| HOLD_15_OR_DTE_LE_14 | USD -81.75 | USD 237.43 |
| HOLD_20_SESSIONS | USD 537.52 | USD -4,033.30 |
| HOLD_20_OR_DTE_LE_7 | USD -136.74 | USD 661.33 |
| HOLD_20_OR_DTE_LE_14 | USD -81.75 | USD 237.43 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 77.84% | USD 222.28 | USD 43,122.00 | USD -18,965.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 76.80% | USD 213.18 | USD 41,356.60 | USD -18,974.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 76.29% | USD 187.28 | USD 36,332.00 | USD -19,000.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 76.29% | USD 178.18 | USD 34,566.60 | USD -19,009.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 74.74% | USD 152.28 | USD 29,542.00 | USD -19,035.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 74.23% | USD 143.18 | USD 27,776.60 | USD -19,044.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 72.16% | USD 82.28 | USD 15,962.00 | USD -19,105.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 71.13% | USD 73.18 | USD 14,196.60 | USD -19,114.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 77.84% | USD 222.28 | USD 43,122.00 | USD -18,965.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 76.80% | USD 213.18 | USD 41,356.60 | USD -18,974.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 76.29% | USD 187.28 | USD 36,332.00 | USD -19,000.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 76.29% | USD 178.18 | USD 34,566.60 | USD -19,009.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 74.74% | USD 152.28 | USD 29,542.00 | USD -19,035.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 74.23% | USD 143.18 | USD 27,776.60 | USD -19,044.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 72.16% | USD 82.28 | USD 15,962.00 | USD -19,105.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 71.13% | USD 73.18 | USD 14,196.60 | USD -19,114.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 77.84% | USD 222.28 | USD 43,122.00 | USD -18,965.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 76.80% | USD 213.18 | USD 41,356.60 | USD -18,974.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 76.29% | USD 187.28 | USD 36,332.00 | USD -19,000.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 76.29% | USD 178.18 | USD 34,566.60 | USD -19,009.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 74.74% | USD 152.28 | USD 29,542.00 | USD -19,035.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 74.23% | USD 143.18 | USD 27,776.60 | USD -19,044.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 72.16% | USD 82.28 | USD 15,962.00 | USD -19,105.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 71.13% | USD 73.18 | USD 14,196.60 | USD -19,114.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 193 | 81.35% | USD 237.20 | USD 45,779.00 | USD -25,685.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 193 | 81.35% | USD 228.10 | USD 44,022.70 | USD -25,694.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 193 | 80.83% | USD 202.20 | USD 39,024.00 | USD -25,720.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 193 | 80.83% | USD 193.10 | USD 37,267.70 | USD -25,729.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 193 | 80.83% | USD 167.20 | USD 32,269.00 | USD -25,755.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 193 | 80.83% | USD 158.10 | USD 30,512.70 | USD -25,764.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 193 | 78.76% | USD 97.20 | USD 18,759.00 | USD -25,825.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 193 | 78.24% | USD 88.10 | USD 17,002.70 | USD -25,834.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.35% | USD 237.20 | USD 45,779.00 | USD -25,685.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.35% | USD 228.10 | USD 44,022.70 | USD -25,694.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 80.83% | USD 202.20 | USD 39,024.00 | USD -25,720.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 80.83% | USD 193.10 | USD 37,267.70 | USD -25,729.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 80.83% | USD 167.20 | USD 32,269.00 | USD -25,755.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 80.83% | USD 158.10 | USD 30,512.70 | USD -25,764.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 78.76% | USD 97.20 | USD 18,759.00 | USD -25,825.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 78.24% | USD 88.10 | USD 17,002.70 | USD -25,834.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 80.93% | USD 245.20 | USD 47,569.00 | USD -22,223.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 80.93% | USD 236.10 | USD 45,803.60 | USD -22,232.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 80.41% | USD 210.20 | USD 40,779.00 | USD -22,258.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 80.41% | USD 201.10 | USD 39,013.60 | USD -22,267.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 79.90% | USD 175.20 | USD 33,989.00 | USD -22,293.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 79.90% | USD 166.10 | USD 32,223.60 | USD -22,302.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 78.35% | USD 105.20 | USD 20,409.00 | USD -22,363.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 77.84% | USD 96.10 | USD 18,643.60 | USD -22,372.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 182 | 81.87% | USD 492.98 | USD 89,722.00 | USD -42,509.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 182 | 81.87% | USD 483.88 | USD 88,065.80 | USD -42,518.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 182 | 81.87% | USD 457.98 | USD 83,352.00 | USD -42,544.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 182 | 81.87% | USD 448.88 | USD 81,695.80 | USD -42,553.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 182 | 81.87% | USD 422.98 | USD 76,982.00 | USD -42,579.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 182 | 81.87% | USD 413.88 | USD 75,325.80 | USD -42,588.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 182 | 81.87% | USD 352.98 | USD 64,242.00 | USD -42,649.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 182 | 81.32% | USD 343.88 | USD 62,585.80 | USD -42,658.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 189 | 83.07% | USD 551.36 | USD 104,207.00 | USD -42,509.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 189 | 83.07% | USD 542.26 | USD 102,487.10 | USD -42,518.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 189 | 83.07% | USD 516.36 | USD 97,592.00 | USD -42,544.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 189 | 83.07% | USD 507.26 | USD 95,872.10 | USD -42,553.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 189 | 83.07% | USD 481.36 | USD 90,977.00 | USD -42,579.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 189 | 83.07% | USD 472.26 | USD 89,257.10 | USD -42,588.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 189 | 83.07% | USD 411.36 | USD 77,747.00 | USD -42,649.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 189 | 82.54% | USD 402.26 | USD 76,027.10 | USD -42,658.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 81.96% | USD 155.68 | USD 30,202.00 | USD -31,768.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 81.96% | USD 146.58 | USD 28,436.60 | USD -31,777.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 81.96% | USD 120.68 | USD 23,412.00 | USD -31,803.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 81.96% | USD 111.58 | USD 21,646.60 | USD -31,812.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 81.44% | USD 85.68 | USD 16,622.00 | USD -31,838.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 81.44% | USD 76.58 | USD 14,856.60 | USD -31,847.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 80.41% | USD 15.68 | USD 3,042.00 | USD -31,908.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 79.90% | USD 6.58 | USD 1,276.60 | USD -31,917.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 23 | 47.83% | USD -3,495.78 | USD -80,403.00 | USD -47,181.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 23 | 47.83% | USD -3,504.88 | USD -80,612.30 | USD -47,190.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 23 | 47.83% | USD -3,530.78 | USD -81,208.00 | USD -47,216.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 23 | 47.83% | USD -3,539.88 | USD -81,417.30 | USD -47,225.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 23 | 47.83% | USD -3,565.78 | USD -82,013.00 | USD -47,251.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 23 | 47.83% | USD -3,574.88 | USD -82,222.30 | USD -47,260.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 23 | 47.83% | USD -3,635.78 | USD -83,623.00 | USD -47,321.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 23 | 47.83% | USD -3,644.88 | USD -83,832.30 | USD -47,330.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 180 | 83.33% | USD 524.59 | USD 94,426.00 | USD -45,829.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 180 | 83.33% | USD 515.49 | USD 92,788.00 | USD -45,838.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 180 | 83.33% | USD 489.59 | USD 88,126.00 | USD -45,864.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 180 | 83.33% | USD 480.49 | USD 86,488.00 | USD -45,873.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 180 | 83.33% | USD 454.59 | USD 81,826.00 | USD -45,899.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 180 | 83.33% | USD 445.49 | USD 80,188.00 | USD -45,908.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 180 | 83.33% | USD 384.59 | USD 69,226.00 | USD -45,969.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 180 | 83.33% | USD 375.49 | USD 67,588.00 | USD -45,978.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 81.96% | USD 155.68 | USD 30,202.00 | USD -31,768.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 81.96% | USD 146.58 | USD 28,436.60 | USD -31,777.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 81.96% | USD 120.68 | USD 23,412.00 | USD -31,803.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 81.96% | USD 111.58 | USD 21,646.60 | USD -31,812.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 81.44% | USD 85.68 | USD 16,622.00 | USD -31,838.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 81.44% | USD 76.58 | USD 14,856.60 | USD -31,847.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 80.41% | USD 15.68 | USD 3,042.00 | USD -31,908.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 79.90% | USD 6.58 | USD 1,276.60 | USD -31,917.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -44.08 | USD -8,552.40 | USD -1,672.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/195 (1) | 74.23% (67.64–79.87%) | USD 143.18 | USD 27,776.60 | USD -19,044.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/195 (1) | 24.74% (19.20–31.27%) | USD -451.77 | USD -87,643.40 | USD -4,316.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -220.42 | USD -42,762.00 | USD -8,363.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -44.08 | USD -8,552.40 | USD -1,672.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/195 (1) | 74.23% (67.64–79.87%) | USD 143.18 | USD 27,776.60 | USD -19,044.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/195 (1) | 24.74% (19.20–31.27%) | USD -451.77 | USD -87,643.40 | USD -4,316.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -220.42 | USD -42,762.00 | USD -8,363.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -44.08 | USD -8,552.40 | USD -1,672.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 74.23% (67.64–79.87%) | USD 143.18 | USD 27,776.60 | USD -19,044.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 24.74% (19.20–31.27%) | USD -451.77 | USD -87,643.40 | USD -4,316.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -220.42 | USD -42,762.00 | USD -8,363.00 |
| HOLD_10_SESSIONS | 1 : 1 | 193/195 (2) | 33.16% (26.90–40.07%) | USD -50.38 | USD -9,722.80 | USD -2,270.60 |
| HOLD_10_SESSIONS | 1 : 6 | 193/195 (2) | 80.83% (74.70–85.76%) | USD 158.10 | USD 30,512.70 | USD -25,764.10 |
| HOLD_10_SESSIONS | 6 : 1 | 193/195 (2) | 18.65% (13.79–24.74%) | USD -510.74 | USD -98,572.30 | USD -6,407.10 |
| HOLD_10_SESSIONS | 5 : 5 | 193/195 (2) | 33.16% (26.90–40.07%) | USD -251.89 | USD -48,614.00 | USD -11,353.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 193/195 (2) | 33.16% (26.90–40.07%) | USD -50.38 | USD -9,722.80 | USD -2,270.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 193/195 (2) | 80.83% (74.70–85.76%) | USD 158.10 | USD 30,512.70 | USD -25,764.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 193/195 (2) | 18.65% (13.79–24.74%) | USD -510.74 | USD -98,572.30 | USD -6,407.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 193/195 (2) | 33.16% (26.90–40.07%) | USD -251.89 | USD -48,614.00 | USD -11,353.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 32.47% (26.28–39.35%) | USD -56.26 | USD -10,915.40 | USD -2,270.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 79.90% (73.70–84.93%) | USD 166.10 | USD 32,223.60 | USD -22,302.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 17.53% (12.82–23.49%) | USD -559.96 | USD -108,631.40 | USD -6,039.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 32.47% (26.28–39.35%) | USD -281.32 | USD -54,577.00 | USD -11,353.00 |
| HOLD_15_SESSIONS | 1 : 1 | 182/195 (13) | 35.71% (29.11–42.90%) | USD -56.19 | USD -10,226.20 | USD -3,251.60 |
| HOLD_15_SESSIONS | 1 : 6 | 182/195 (13) | 81.87% (75.63–86.79%) | USD 413.88 | USD 75,325.80 | USD -42,588.10 |
| HOLD_15_SESSIONS | 6 : 1 | 182/195 (13) | 16.48% (11.80–22.56%) | USD -807.19 | USD -146,909.20 | USD -5,262.10 |
| HOLD_15_SESSIONS | 5 : 5 | 182/195 (13) | 35.71% (29.11–42.90%) | USD -280.94 | USD -51,131.00 | USD -16,258.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 189/195 (6) | 35.98% (29.48–43.04%) | USD -46.72 | USD -8,829.40 | USD -3,251.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 189/195 (6) | 83.07% (77.08–87.74%) | USD 472.26 | USD 89,257.10 | USD -42,588.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 189/195 (6) | 16.40% (11.80–22.34%) | USD -799.27 | USD -151,062.90 | USD -5,262.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 189/195 (6) | 35.98% (29.48–43.04%) | USD -233.58 | USD -44,147.00 | USD -16,258.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 34.02% (27.72–40.94%) | USD -64.78 | USD -12,567.40 | USD -3,455.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 81.44% (75.38–86.28%) | USD 76.58 | USD 14,856.60 | USD -31,847.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 19.59% (14.62–25.74%) | USD -530.04 | USD -102,828.40 | USD -6,039.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 34.02% (27.72–40.94%) | USD -323.90 | USD -62,837.00 | USD -17,278.00 |
| HOLD_20_SESSIONS | 1 : 1 | 23/195 (172) | 39.13% (22.16–59.21%) | USD -157.30 | USD -3,617.80 | USD -4,038.60 |
| HOLD_20_SESSIONS | 1 : 6 | 23/195 (172) | 47.83% (29.24–67.04%) | USD -3,574.88 | USD -82,222.30 | USD -47,260.10 |
| HOLD_20_SESSIONS | 6 : 1 | 23/195 (172) | 56.52% (36.81–74.37%) | USD 2,473.81 | USD 56,897.70 | USD -3,356.10 |
| HOLD_20_SESSIONS | 5 : 5 | 23/195 (172) | 39.13% (22.16–59.21%) | USD -786.48 | USD -18,089.00 | USD -20,193.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 180/195 (15) | 35.56% (28.93–42.78%) | USD -49.12 | USD -8,842.00 | USD -3,521.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 180/195 (15) | 83.33% (77.20–88.07%) | USD 445.49 | USD 80,188.00 | USD -45,908.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 180/195 (15) | 16.67% (11.93–22.80%) | USD -789.34 | USD -142,082.00 | USD -5,260.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 180/195 (15) | 35.56% (28.93–42.78%) | USD -245.61 | USD -44,210.00 | USD -17,608.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 34.02% (27.72–40.94%) | USD -64.78 | USD -12,567.40 | USD -3,455.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 81.44% (75.38–86.28%) | USD 76.58 | USD 14,856.60 | USD -31,847.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 19.59% (14.62–25.74%) | USD -530.04 | USD -102,828.40 | USD -6,039.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 34.02% (27.72–40.94%) | USD -323.90 | USD -62,837.00 | USD -17,278.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/195 | 0.00% | USD -207,380.93 | USD -335,633.55 |
| -75% | 0/195 | 0.00% | USD -153,351.80 | USD -248,803.80 |
| -50% | 0/195 | 0.00% | USD -99,322.66 | USD -161,974.05 |
| -40% | 0/195 | 0.00% | USD -77,711.01 | USD -127,242.15 |
| -30% | 0/195 | 0.00% | USD -56,099.35 | USD -92,510.25 |
| -25% | 0/195 | 0.00% | USD -45,293.52 | USD -75,144.30 |
| -20% | 0/195 | 0.00% | USD -34,487.70 | USD -58,028.55 |
| -15% | 0/195 | 0.00% | USD -23,681.87 | USD -41,529.05 |
| -10% | 2/195 | 1.03% | USD -12,879.65 | USD -25,677.55 |
| -5% | 48/195 | 24.62% | USD -2,403.55 | USD -10,149.05 |
| 0% | 195/195 | 100.00% | USD 1,747.79 | USD 488.45 |
| 5% | 195/195 | 100.00% | USD 1,752.88 | USD 488.45 |
| 10% | 195/195 | 100.00% | USD 1,752.88 | USD 488.45 |
| 20% | 195/195 | 100.00% | USD 1,752.88 | USD 488.45 |

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