# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.45 / USD 2,669.10; mean absolute mismatch USD 2,221.65; mean match score 16.64%.
- Actual selected contract ratios: {'1:6': 180}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 180; entered cohorts: 180; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 180/180 | 124/56/0 | 68.89% (61.79–75.20%) | USD 149.35 | USD 465.90 | USD 26,883.00 | USD -4,912.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 180/180 | 124/56/0 | 68.89% (61.79–75.20%) | USD 149.35 | USD 465.90 | USD 26,883.00 | USD -4,912.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 180/180 | 124/56/0 | 68.89% (61.79–75.20%) | USD 149.35 | USD 465.90 | USD 26,883.00 | USD -4,912.10 | 0 |
| HOLD_10_SESSIONS | 179/180 | 133/46/0 | 74.30% (67.44–80.15%) | USD 221.17 | USD 807.90 | USD 39,590.10 | USD -11,108.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 179/180 | 133/46/0 | 74.30% (67.44–80.15%) | USD 221.17 | USD 807.90 | USD 39,590.10 | USD -11,108.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 179/180 | 133/46/0 | 74.30% (67.44–80.15%) | USD 221.17 | USD 807.90 | USD 39,590.10 | USD -11,108.10 | 1 |
| HOLD_15_SESSIONS | 178/180 | 140/38/0 | 78.65% (72.06–84.03%) | USD 312.32 | USD 1,093.90 | USD 55,592.20 | USD -29,402.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 178/180 | 140/38/0 | 78.65% (72.06–84.03%) | USD 312.32 | USD 1,093.90 | USD 55,592.20 | USD -29,402.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 178/180 | 140/38/0 | 78.65% (72.06–84.03%) | USD 312.32 | USD 1,093.90 | USD 55,592.20 | USD -29,402.10 | 2 |
| HOLD_20_SESSIONS | 177/180 | 147/30/0 | 83.05% (76.84–87.86%) | USD 593.84 | USD 1,360.90 | USD 105,110.30 | USD -29,813.10 | 3 |
| HOLD_20_OR_DTE_LE_7 | 177/180 | 147/30/0 | 83.05% (76.84–87.86%) | USD 593.84 | USD 1,360.90 | USD 105,110.30 | USD -29,813.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 177/180 | 149/28/0 | 84.18% (78.09–88.82%) | USD 589.71 | USD 1,337.90 | USD 104,378.30 | USD -29,813.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -66.88 | USD 295.33 |
| HOLD_5_OR_DTE_LE_7 | USD -66.88 | USD 295.33 |
| HOLD_5_OR_DTE_LE_14 | USD -66.88 | USD 295.33 |
| HOLD_10_SESSIONS | USD -87.75 | USD 388.02 |
| HOLD_10_OR_DTE_LE_7 | USD -87.75 | USD 388.02 |
| HOLD_10_OR_DTE_LE_14 | USD -87.75 | USD 388.02 |
| HOLD_15_SESSIONS | USD -116.63 | USD 508.04 |
| HOLD_15_OR_DTE_LE_7 | USD -116.63 | USD 508.04 |
| HOLD_15_OR_DTE_LE_14 | USD -116.63 | USD 508.04 |
| HOLD_20_SESSIONS | USD -166.89 | USD 839.83 |
| HOLD_20_OR_DTE_LE_7 | USD -166.89 | USD 839.83 |
| HOLD_20_OR_DTE_LE_14 | USD -164.38 | USD 833.19 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 180 | 69.44% | USD 228.45 | USD 41,121.00 | USD -4,833.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 180 | 69.44% | USD 219.35 | USD 39,483.00 | USD -4,842.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 180 | 69.44% | USD 193.45 | USD 34,821.00 | USD -4,868.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 180 | 69.44% | USD 184.35 | USD 33,183.00 | USD -4,877.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 180 | 69.44% | USD 158.45 | USD 28,521.00 | USD -4,903.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 180 | 68.89% | USD 149.35 | USD 26,883.00 | USD -4,912.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 180 | 67.22% | USD 88.45 | USD 15,921.00 | USD -4,973.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 180 | 66.67% | USD 79.35 | USD 14,283.00 | USD -4,982.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 180 | 69.44% | USD 228.45 | USD 41,121.00 | USD -4,833.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 180 | 69.44% | USD 219.35 | USD 39,483.00 | USD -4,842.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 180 | 69.44% | USD 193.45 | USD 34,821.00 | USD -4,868.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 180 | 69.44% | USD 184.35 | USD 33,183.00 | USD -4,877.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 180 | 69.44% | USD 158.45 | USD 28,521.00 | USD -4,903.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 180 | 68.89% | USD 149.35 | USD 26,883.00 | USD -4,912.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 180 | 67.22% | USD 88.45 | USD 15,921.00 | USD -4,973.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 180 | 66.67% | USD 79.35 | USD 14,283.00 | USD -4,982.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 180 | 69.44% | USD 228.45 | USD 41,121.00 | USD -4,833.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 180 | 69.44% | USD 219.35 | USD 39,483.00 | USD -4,842.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 180 | 69.44% | USD 193.45 | USD 34,821.00 | USD -4,868.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 180 | 69.44% | USD 184.35 | USD 33,183.00 | USD -4,877.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 180 | 69.44% | USD 158.45 | USD 28,521.00 | USD -4,903.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 180 | 68.89% | USD 149.35 | USD 26,883.00 | USD -4,912.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 180 | 67.22% | USD 88.45 | USD 15,921.00 | USD -4,973.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 180 | 66.67% | USD 79.35 | USD 14,283.00 | USD -4,982.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 179 | 74.86% | USD 300.27 | USD 53,749.00 | USD -11,029.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 179 | 74.86% | USD 291.17 | USD 52,120.10 | USD -11,038.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 179 | 74.30% | USD 265.27 | USD 47,484.00 | USD -11,064.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 179 | 74.30% | USD 256.17 | USD 45,855.10 | USD -11,073.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 179 | 74.30% | USD 230.27 | USD 41,219.00 | USD -11,099.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 179 | 74.30% | USD 221.17 | USD 39,590.10 | USD -11,108.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 179 | 73.18% | USD 160.27 | USD 28,689.00 | USD -11,169.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 179 | 73.18% | USD 151.17 | USD 27,060.10 | USD -11,178.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 179 | 74.86% | USD 300.27 | USD 53,749.00 | USD -11,029.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 179 | 74.86% | USD 291.17 | USD 52,120.10 | USD -11,038.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 179 | 74.30% | USD 265.27 | USD 47,484.00 | USD -11,064.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 179 | 74.30% | USD 256.17 | USD 45,855.10 | USD -11,073.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 179 | 74.30% | USD 230.27 | USD 41,219.00 | USD -11,099.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 179 | 74.30% | USD 221.17 | USD 39,590.10 | USD -11,108.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 179 | 73.18% | USD 160.27 | USD 28,689.00 | USD -11,169.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 179 | 73.18% | USD 151.17 | USD 27,060.10 | USD -11,178.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 179 | 74.86% | USD 300.27 | USD 53,749.00 | USD -11,029.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 179 | 74.86% | USD 291.17 | USD 52,120.10 | USD -11,038.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 179 | 74.30% | USD 265.27 | USD 47,484.00 | USD -11,064.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 179 | 74.30% | USD 256.17 | USD 45,855.10 | USD -11,073.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 179 | 74.30% | USD 230.27 | USD 41,219.00 | USD -11,099.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 179 | 74.30% | USD 221.17 | USD 39,590.10 | USD -11,108.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 179 | 73.18% | USD 160.27 | USD 28,689.00 | USD -11,169.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 179 | 73.18% | USD 151.17 | USD 27,060.10 | USD -11,178.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 178 | 79.78% | USD 391.42 | USD 69,672.00 | USD -29,323.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 178 | 79.78% | USD 382.32 | USD 68,052.20 | USD -29,332.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 178 | 79.21% | USD 356.42 | USD 63,442.00 | USD -29,358.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 178 | 79.21% | USD 347.32 | USD 61,822.20 | USD -29,367.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 178 | 78.65% | USD 321.42 | USD 57,212.00 | USD -29,393.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 178 | 78.65% | USD 312.32 | USD 55,592.20 | USD -29,402.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 178 | 78.65% | USD 251.42 | USD 44,752.00 | USD -29,463.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 178 | 78.09% | USD 242.32 | USD 43,132.20 | USD -29,472.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 178 | 79.78% | USD 391.42 | USD 69,672.00 | USD -29,323.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 178 | 79.78% | USD 382.32 | USD 68,052.20 | USD -29,332.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 178 | 79.21% | USD 356.42 | USD 63,442.00 | USD -29,358.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 178 | 79.21% | USD 347.32 | USD 61,822.20 | USD -29,367.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 178 | 78.65% | USD 321.42 | USD 57,212.00 | USD -29,393.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 178 | 78.65% | USD 312.32 | USD 55,592.20 | USD -29,402.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 178 | 78.65% | USD 251.42 | USD 44,752.00 | USD -29,463.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 178 | 78.09% | USD 242.32 | USD 43,132.20 | USD -29,472.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 178 | 79.78% | USD 391.42 | USD 69,672.00 | USD -29,323.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 178 | 79.78% | USD 382.32 | USD 68,052.20 | USD -29,332.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 178 | 79.21% | USD 356.42 | USD 63,442.00 | USD -29,358.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 178 | 79.21% | USD 347.32 | USD 61,822.20 | USD -29,367.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 178 | 78.65% | USD 321.42 | USD 57,212.00 | USD -29,393.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 178 | 78.65% | USD 312.32 | USD 55,592.20 | USD -29,402.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 178 | 78.65% | USD 251.42 | USD 44,752.00 | USD -29,463.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 178 | 78.09% | USD 242.32 | USD 43,132.20 | USD -29,472.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 177 | 83.62% | USD 672.94 | USD 119,111.00 | USD -29,734.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 177 | 83.62% | USD 663.84 | USD 117,500.30 | USD -29,743.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 177 | 83.05% | USD 637.94 | USD 112,916.00 | USD -29,769.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 177 | 83.05% | USD 628.84 | USD 111,305.30 | USD -29,778.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 177 | 83.05% | USD 602.94 | USD 106,721.00 | USD -29,804.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 177 | 83.05% | USD 593.84 | USD 105,110.30 | USD -29,813.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 177 | 83.05% | USD 532.94 | USD 94,331.00 | USD -29,874.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 177 | 83.05% | USD 523.84 | USD 92,720.30 | USD -29,883.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 177 | 83.62% | USD 672.94 | USD 119,111.00 | USD -29,734.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 177 | 83.62% | USD 663.84 | USD 117,500.30 | USD -29,743.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 177 | 83.05% | USD 637.94 | USD 112,916.00 | USD -29,769.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 177 | 83.05% | USD 628.84 | USD 111,305.30 | USD -29,778.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 177 | 83.05% | USD 602.94 | USD 106,721.00 | USD -29,804.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 177 | 83.05% | USD 593.84 | USD 105,110.30 | USD -29,813.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 177 | 83.05% | USD 532.94 | USD 94,331.00 | USD -29,874.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 177 | 83.05% | USD 523.84 | USD 92,720.30 | USD -29,883.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 177 | 84.18% | USD 668.81 | USD 118,379.00 | USD -29,734.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 177 | 84.18% | USD 659.71 | USD 116,768.30 | USD -29,743.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 177 | 84.18% | USD 633.81 | USD 112,184.00 | USD -29,769.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 177 | 84.18% | USD 624.71 | USD 110,573.30 | USD -29,778.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 177 | 84.18% | USD 598.81 | USD 105,989.00 | USD -29,804.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 177 | 84.18% | USD 589.71 | USD 104,378.30 | USD -29,813.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 177 | 84.18% | USD 528.81 | USD 93,599.00 | USD -29,874.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 177 | 84.18% | USD 519.71 | USD 91,988.30 | USD -29,883.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 180/180 (0) | 28.33% (22.26–35.32%) | USD -40.26 | USD -7,247.00 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 180/180 (0) | 68.89% (61.79–75.20%) | USD 149.35 | USD 26,883.00 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 180/180 (0) | 23.89% (18.25–30.62%) | USD -431.18 | USD -77,612.00 | USD -4,240.10 |
| HOLD_5_SESSIONS | 5 : 5 | 180/180 (0) | 28.33% (22.26–35.32%) | USD -201.31 | USD -36,235.00 | USD -2,528.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 180/180 (0) | 28.33% (22.26–35.32%) | USD -40.26 | USD -7,247.00 | USD -505.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 180/180 (0) | 68.89% (61.79–75.20%) | USD 149.35 | USD 26,883.00 | USD -4,912.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 180/180 (0) | 23.89% (18.25–30.62%) | USD -431.18 | USD -77,612.00 | USD -4,240.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 180/180 (0) | 28.33% (22.26–35.32%) | USD -201.31 | USD -36,235.00 | USD -2,528.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 180/180 (0) | 28.33% (22.26–35.32%) | USD -40.26 | USD -7,247.00 | USD -505.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 180/180 (0) | 68.89% (61.79–75.20%) | USD 149.35 | USD 26,883.00 | USD -4,912.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 180/180 (0) | 23.89% (18.25–30.62%) | USD -431.18 | USD -77,612.00 | USD -4,240.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 180/180 (0) | 28.33% (22.26–35.32%) | USD -201.31 | USD -36,235.00 | USD -2,528.00 |
| HOLD_10_SESSIONS | 1 : 1 | 179/180 (1) | 39.11% (32.26–46.41%) | USD -45.68 | USD -8,176.40 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 179/180 (1) | 74.30% (67.44–80.15%) | USD 221.17 | USD 39,590.10 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 179/180 (1) | 21.79% (16.37–28.39%) | USD -540.92 | USD -96,824.90 | USD -5,364.10 |
| HOLD_10_SESSIONS | 5 : 5 | 179/180 (1) | 39.11% (32.26–46.41%) | USD -228.39 | USD -40,882.00 | USD -7,013.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 179/180 (1) | 39.11% (32.26–46.41%) | USD -45.68 | USD -8,176.40 | USD -1,402.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 179/180 (1) | 74.30% (67.44–80.15%) | USD 221.17 | USD 39,590.10 | USD -11,108.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 179/180 (1) | 21.79% (16.37–28.39%) | USD -540.92 | USD -96,824.90 | USD -5,364.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 179/180 (1) | 39.11% (32.26–46.41%) | USD -228.39 | USD -40,882.00 | USD -7,013.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 179/180 (1) | 39.11% (32.26–46.41%) | USD -45.68 | USD -8,176.40 | USD -1,402.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 179/180 (1) | 74.30% (67.44–80.15%) | USD 221.17 | USD 39,590.10 | USD -11,108.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 179/180 (1) | 21.79% (16.37–28.39%) | USD -540.92 | USD -96,824.90 | USD -5,364.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 179/180 (1) | 39.11% (32.26–46.41%) | USD -228.39 | USD -40,882.00 | USD -7,013.00 |
| HOLD_15_SESSIONS | 1 : 1 | 178/180 (2) | 38.76% (31.92–46.09%) | USD -54.56 | USD -9,710.80 | USD -3,020.60 |
| HOLD_15_SESSIONS | 1 : 6 | 178/180 (2) | 78.65% (72.06–84.03%) | USD 312.32 | USD 55,592.20 | USD -29,402.10 |
| HOLD_15_SESSIONS | 6 : 1 | 178/180 (2) | 17.42% (12.55–23.66%) | USD -694.20 | USD -123,567.80 | USD -6,027.10 |
| HOLD_15_SESSIONS | 5 : 5 | 178/180 (2) | 38.76% (31.92–46.09%) | USD -272.78 | USD -48,554.00 | USD -15,103.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 178/180 (2) | 38.76% (31.92–46.09%) | USD -54.56 | USD -9,710.80 | USD -3,020.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 178/180 (2) | 78.65% (72.06–84.03%) | USD 312.32 | USD 55,592.20 | USD -29,402.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 178/180 (2) | 17.42% (12.55–23.66%) | USD -694.20 | USD -123,567.80 | USD -6,027.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 178/180 (2) | 38.76% (31.92–46.09%) | USD -272.78 | USD -48,554.00 | USD -15,103.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 178/180 (2) | 38.76% (31.92–46.09%) | USD -54.56 | USD -9,710.80 | USD -3,020.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 178/180 (2) | 78.65% (72.06–84.03%) | USD 312.32 | USD 55,592.20 | USD -29,402.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 178/180 (2) | 17.42% (12.55–23.66%) | USD -694.20 | USD -123,567.80 | USD -6,027.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 178/180 (2) | 38.76% (31.92–46.09%) | USD -272.78 | USD -48,554.00 | USD -15,103.00 |
| HOLD_20_SESSIONS | 1 : 1 | 177/180 (3) | 44.07% (36.96–51.43%) | USD -49.52 | USD -8,764.20 | USD -2,926.60 |
| HOLD_20_SESSIONS | 1 : 6 | 177/180 (3) | 83.05% (76.84–87.86%) | USD 593.84 | USD 105,110.30 | USD -29,813.10 |
| HOLD_20_SESSIONS | 6 : 1 | 177/180 (3) | 15.25% (10.70–21.28%) | USD -940.45 | USD -166,459.70 | USD -7,645.10 |
| HOLD_20_SESSIONS | 5 : 5 | 177/180 (3) | 44.07% (36.96–51.43%) | USD -247.58 | USD -43,821.00 | USD -14,633.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 177/180 (3) | 44.07% (36.96–51.43%) | USD -49.52 | USD -8,764.20 | USD -2,926.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 177/180 (3) | 83.05% (76.84–87.86%) | USD 593.84 | USD 105,110.30 | USD -29,813.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 177/180 (3) | 15.25% (10.70–21.28%) | USD -940.45 | USD -166,459.70 | USD -7,645.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 177/180 (3) | 44.07% (36.96–51.43%) | USD -247.58 | USD -43,821.00 | USD -14,633.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 177/180 (3) | 45.20% (38.05–52.55%) | USD -48.11 | USD -8,516.20 | USD -2,926.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 177/180 (3) | 84.18% (78.09–88.82%) | USD 589.71 | USD 104,378.30 | USD -29,813.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 177/180 (3) | 14.69% (10.23–20.65%) | USD -926.51 | USD -163,991.70 | USD -7,645.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 177/180 (3) | 45.20% (38.05–52.55%) | USD -240.57 | USD -42,581.00 | USD -14,633.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/180 | 0.00% | USD -206,055.86 | USD -333,646.55 |
| -75% | 0/180 | 0.00% | USD -151,930.78 | USD -246,651.05 |
| -50% | 0/180 | 0.00% | USD -97,805.70 | USD -159,655.55 |
| -40% | 0/180 | 0.00% | USD -76,155.67 | USD -124,857.35 |
| -30% | 0/180 | 0.00% | USD -54,505.63 | USD -90,195.25 |
| -25% | 0/180 | 0.00% | USD -43,680.62 | USD -73,230.05 |
| -20% | 0/180 | 0.00% | USD -32,855.60 | USD -56,324.75 |
| -15% | 1/180 | 0.56% | USD -22,045.59 | USD -39,423.05 |
| -10% | 4/180 | 2.22% | USD -11,262.82 | USD -23,000.55 |
| -5% | 71/180 | 39.44% | USD -928.77 | USD -8,108.00 |
| 0% | 180/180 | 100.00% | USD 2,182.48 | USD 679.45 |
| 5% | 180/180 | 100.00% | USD 2,182.10 | USD 679.45 |
| 10% | 180/180 | 100.00% | USD 2,182.10 | USD 679.45 |
| 20% | 180/180 | 100.00% | USD 2,182.10 | USD 679.45 |

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