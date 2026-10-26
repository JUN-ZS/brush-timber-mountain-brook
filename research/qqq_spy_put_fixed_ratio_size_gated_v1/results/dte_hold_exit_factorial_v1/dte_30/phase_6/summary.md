# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 344.31 / USD 2,011.04; mean absolute mismatch USD 1,666.73; mean match score 17.15%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 195/196 | 140/55/0 | 71.79% (65.11–77.64%) | USD -54.83 | USD 434.90 | USD -10,691.50 | USD -18,183.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 195/196 | 140/55/0 | 71.79% (65.11–77.64%) | USD -54.83 | USD 434.90 | USD -10,691.50 | USD -18,183.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 195/196 | 140/55/0 | 71.79% (65.11–77.64%) | USD -54.83 | USD 434.90 | USD -10,691.50 | USD -18,183.10 | 1 |
| HOLD_10_SESSIONS | 194/196 | 150/44/0 | 77.32% (70.93–82.65%) | USD 123.61 | USD 779.90 | USD 23,979.60 | USD -29,537.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 194/196 | 150/44/0 | 77.32% (70.93–82.65%) | USD 123.61 | USD 779.90 | USD 23,979.60 | USD -29,537.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 194/196 | 150/44/0 | 77.32% (70.93–82.65%) | USD 118.43 | USD 759.90 | USD 22,974.60 | USD -29,537.10 | 2 |
| HOLD_15_SESSIONS | 181/196 | 141/40/0 | 77.90% (71.31–83.33%) | USD 176.85 | USD 1,102.90 | USD 32,009.90 | USD -45,081.10 | 15 |
| HOLD_15_OR_DTE_LE_7 | 187/196 | 148/39/0 | 79.14% (72.76–84.35%) | USD 197.93 | USD 1,079.90 | USD 37,013.30 | USD -45,081.10 | 9 |
| HOLD_15_OR_DTE_LE_14 | 193/196 | 150/43/0 | 77.72% (71.34–83.02%) | USD 227.27 | USD 800.90 | USD 43,862.70 | USD -29,537.10 | 3 |
| HOLD_20_SESSIONS | 34/196 | 28/6/0 | 82.35% (66.49–91.65%) | USD 809.99 | USD 1,820.40 | USD 27,539.60 | USD -16,772.10 | 162 |
| HOLD_20_OR_DTE_LE_7 | 183/196 | 155/28/0 | 84.70% (78.78–89.20%) | USD 349.12 | USD 1,100.90 | USD 63,889.70 | USD -45,081.10 | 13 |
| HOLD_20_OR_DTE_LE_14 | 193/196 | 150/43/0 | 77.72% (71.34–83.02%) | USD 227.27 | USD 800.90 | USD 43,862.70 | USD -29,537.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -31.88 | USD 56.15 |
| HOLD_5_OR_DTE_LE_7 | USD -31.88 | USD 56.15 |
| HOLD_5_OR_DTE_LE_14 | USD -31.88 | USD 56.15 |
| HOLD_10_SESSIONS | USD -82.23 | USD 284.94 |
| HOLD_10_OR_DTE_LE_7 | USD -82.23 | USD 284.94 |
| HOLD_10_OR_DTE_LE_14 | USD -82.62 | USD 280.14 |
| HOLD_15_SESSIONS | USD -86.41 | USD 342.36 |
| HOLD_15_OR_DTE_LE_7 | USD -84.48 | USD 361.51 |
| HOLD_15_OR_DTE_LE_14 | USD -93.58 | USD 399.95 |
| HOLD_20_SESSIONS | USD -226.21 | USD 1,115.29 |
| HOLD_20_OR_DTE_LE_7 | USD -106.99 | USD 535.21 |
| HOLD_20_OR_DTE_LE_14 | USD -93.58 | USD 399.95 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 195 | 73.85% | USD 24.27 | USD 4,733.00 | USD -18,104.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 195 | 73.85% | USD 15.17 | USD 2,958.50 | USD -18,113.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 195 | 73.33% | USD -10.73 | USD -2,092.00 | USD -18,139.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 195 | 72.82% | USD -19.83 | USD -3,866.50 | USD -18,148.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 195 | 72.31% | USD -45.73 | USD -8,917.00 | USD -18,174.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 195 | 71.79% | USD -54.83 | USD -10,691.50 | USD -18,183.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 195 | 69.23% | USD -115.73 | USD -22,567.00 | USD -18,244.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 195 | 69.23% | USD -124.83 | USD -24,341.50 | USD -18,253.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 195 | 73.85% | USD 24.27 | USD 4,733.00 | USD -18,104.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 195 | 73.85% | USD 15.17 | USD 2,958.50 | USD -18,113.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 195 | 73.33% | USD -10.73 | USD -2,092.00 | USD -18,139.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 195 | 72.82% | USD -19.83 | USD -3,866.50 | USD -18,148.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 195 | 72.31% | USD -45.73 | USD -8,917.00 | USD -18,174.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 195 | 71.79% | USD -54.83 | USD -10,691.50 | USD -18,183.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 195 | 69.23% | USD -115.73 | USD -22,567.00 | USD -18,244.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 195 | 69.23% | USD -124.83 | USD -24,341.50 | USD -18,253.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 73.85% | USD 24.27 | USD 4,733.00 | USD -18,104.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 73.85% | USD 15.17 | USD 2,958.50 | USD -18,113.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 73.33% | USD -10.73 | USD -2,092.00 | USD -18,139.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 72.82% | USD -19.83 | USD -3,866.50 | USD -18,148.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 72.31% | USD -45.73 | USD -8,917.00 | USD -18,174.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 71.79% | USD -54.83 | USD -10,691.50 | USD -18,183.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 69.23% | USD -115.73 | USD -22,567.00 | USD -18,244.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 69.23% | USD -124.83 | USD -24,341.50 | USD -18,253.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 194 | 78.35% | USD 202.71 | USD 39,325.00 | USD -29,458.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 194 | 78.35% | USD 193.61 | USD 37,559.60 | USD -29,467.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 194 | 78.35% | USD 167.71 | USD 32,535.00 | USD -29,493.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 194 | 78.35% | USD 158.61 | USD 30,769.60 | USD -29,502.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 194 | 77.84% | USD 132.71 | USD 25,745.00 | USD -29,528.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 194 | 77.32% | USD 123.61 | USD 23,979.60 | USD -29,537.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 194 | 76.80% | USD 62.71 | USD 12,165.00 | USD -29,598.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 194 | 76.80% | USD 53.61 | USD 10,399.60 | USD -29,607.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 78.35% | USD 202.71 | USD 39,325.00 | USD -29,458.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 78.35% | USD 193.61 | USD 37,559.60 | USD -29,467.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 78.35% | USD 167.71 | USD 32,535.00 | USD -29,493.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 78.35% | USD 158.61 | USD 30,769.60 | USD -29,502.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 77.84% | USD 132.71 | USD 25,745.00 | USD -29,528.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 77.32% | USD 123.61 | USD 23,979.60 | USD -29,537.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 76.80% | USD 62.71 | USD 12,165.00 | USD -29,598.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 76.80% | USD 53.61 | USD 10,399.60 | USD -29,607.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 78.87% | USD 197.53 | USD 38,320.00 | USD -29,458.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 78.87% | USD 188.43 | USD 36,554.60 | USD -29,467.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 78.35% | USD 162.53 | USD 31,530.00 | USD -29,493.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 78.35% | USD 153.43 | USD 29,764.60 | USD -29,502.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 77.84% | USD 127.53 | USD 24,740.00 | USD -29,528.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 77.32% | USD 118.43 | USD 22,974.60 | USD -29,537.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 76.80% | USD 57.53 | USD 11,160.00 | USD -29,598.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 76.80% | USD 48.43 | USD 9,394.60 | USD -29,607.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 181 | 79.01% | USD 255.95 | USD 46,327.00 | USD -45,002.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 181 | 79.01% | USD 246.85 | USD 44,679.90 | USD -45,011.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 181 | 79.01% | USD 220.95 | USD 39,992.00 | USD -45,037.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 181 | 78.45% | USD 211.85 | USD 38,344.90 | USD -45,046.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 181 | 78.45% | USD 185.95 | USD 33,657.00 | USD -45,072.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 181 | 77.90% | USD 176.85 | USD 32,009.90 | USD -45,081.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 181 | 77.35% | USD 115.95 | USD 20,987.00 | USD -45,142.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 181 | 77.35% | USD 106.85 | USD 19,339.90 | USD -45,151.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 187 | 80.21% | USD 277.03 | USD 51,805.00 | USD -45,002.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 187 | 80.21% | USD 267.93 | USD 50,103.30 | USD -45,011.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 187 | 80.21% | USD 242.03 | USD 45,260.00 | USD -45,037.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 187 | 79.68% | USD 232.93 | USD 43,558.30 | USD -45,046.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 187 | 79.68% | USD 207.03 | USD 38,715.00 | USD -45,072.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 187 | 79.14% | USD 197.93 | USD 37,013.30 | USD -45,081.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 187 | 78.61% | USD 137.03 | USD 25,625.00 | USD -45,142.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 187 | 78.61% | USD 127.93 | USD 23,923.30 | USD -45,151.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 78.76% | USD 306.37 | USD 59,129.00 | USD -29,458.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 78.76% | USD 297.27 | USD 57,372.70 | USD -29,467.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 78.24% | USD 271.37 | USD 52,374.00 | USD -29,493.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 78.24% | USD 262.27 | USD 50,617.70 | USD -29,502.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 78.24% | USD 236.37 | USD 45,619.00 | USD -29,528.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 77.72% | USD 227.27 | USD 43,862.70 | USD -29,537.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 77.72% | USD 166.37 | USD 32,109.00 | USD -29,598.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 77.72% | USD 157.27 | USD 30,352.70 | USD -29,607.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 34 | 82.35% | USD 889.09 | USD 30,229.00 | USD -16,693.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 34 | 82.35% | USD 879.99 | USD 29,919.60 | USD -16,702.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 34 | 82.35% | USD 854.09 | USD 29,039.00 | USD -16,728.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 34 | 82.35% | USD 844.99 | USD 28,729.60 | USD -16,737.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 34 | 82.35% | USD 819.09 | USD 27,849.00 | USD -16,763.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 34 | 82.35% | USD 809.99 | USD 27,539.60 | USD -16,772.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 34 | 82.35% | USD 749.09 | USD 25,469.00 | USD -16,833.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 34 | 82.35% | USD 739.99 | USD 25,159.60 | USD -16,842.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 183 | 84.70% | USD 428.22 | USD 78,365.00 | USD -45,002.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 183 | 84.70% | USD 419.12 | USD 76,699.70 | USD -45,011.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 183 | 84.70% | USD 393.22 | USD 71,960.00 | USD -45,037.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 183 | 84.70% | USD 384.12 | USD 70,294.70 | USD -45,046.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 183 | 84.70% | USD 358.22 | USD 65,555.00 | USD -45,072.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 183 | 84.70% | USD 349.12 | USD 63,889.70 | USD -45,081.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 183 | 83.61% | USD 288.22 | USD 52,745.00 | USD -45,142.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 183 | 83.61% | USD 279.12 | USD 51,079.70 | USD -45,151.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 78.76% | USD 306.37 | USD 59,129.00 | USD -29,458.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 78.76% | USD 297.27 | USD 57,372.70 | USD -29,467.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 78.24% | USD 271.37 | USD 52,374.00 | USD -29,493.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 78.24% | USD 262.27 | USD 50,617.70 | USD -29,502.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 78.24% | USD 236.37 | USD 45,619.00 | USD -29,528.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 77.72% | USD 227.27 | USD 43,862.70 | USD -29,537.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 77.72% | USD 166.37 | USD 32,109.00 | USD -29,598.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 77.72% | USD 157.27 | USD 30,352.70 | USD -29,607.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 195/196 (1) | 26.67% (20.95–33.28%) | USD -45.12 | USD -8,799.00 | USD -1,461.60 |
| HOLD_5_SESSIONS | 1 : 6 | 195/196 (1) | 71.79% (65.11–77.64%) | USD -54.83 | USD -10,691.50 | USD -18,183.10 |
| HOLD_5_SESSIONS | 6 : 1 | 195/196 (1) | 26.15% (20.49–32.74%) | USD -261.03 | USD -50,901.50 | USD -3,893.10 |
| HOLD_5_SESSIONS | 5 : 5 | 195/196 (1) | 26.67% (20.95–33.28%) | USD -225.62 | USD -43,995.00 | USD -7,308.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 195/196 (1) | 26.67% (20.95–33.28%) | USD -45.12 | USD -8,799.00 | USD -1,461.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 195/196 (1) | 71.79% (65.11–77.64%) | USD -54.83 | USD -10,691.50 | USD -18,183.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 195/196 (1) | 26.15% (20.49–32.74%) | USD -261.03 | USD -50,901.50 | USD -3,893.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 195/196 (1) | 26.67% (20.95–33.28%) | USD -225.62 | USD -43,995.00 | USD -7,308.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 26.67% (20.95–33.28%) | USD -45.12 | USD -8,799.00 | USD -1,461.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 71.79% (65.11–77.64%) | USD -54.83 | USD -10,691.50 | USD -18,183.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 26.15% (20.49–32.74%) | USD -261.03 | USD -50,901.50 | USD -3,893.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 26.67% (20.95–33.28%) | USD -225.62 | USD -43,995.00 | USD -7,308.00 |
| HOLD_10_SESSIONS | 1 : 1 | 194/196 (2) | 30.41% (24.37–37.21%) | USD -57.34 | USD -11,124.40 | USD -3,415.60 |
| HOLD_10_SESSIONS | 1 : 6 | 194/196 (2) | 77.32% (70.93–82.65%) | USD 123.61 | USD 23,979.60 | USD -29,537.10 |
| HOLD_10_SESSIONS | 6 : 1 | 194/196 (2) | 19.59% (14.62–25.74%) | USD -525.00 | USD -101,850.40 | USD -4,216.10 |
| HOLD_10_SESSIONS | 5 : 5 | 194/196 (2) | 30.41% (24.37–37.21%) | USD -286.71 | USD -55,622.00 | USD -17,078.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 194/196 (2) | 30.41% (24.37–37.21%) | USD -57.34 | USD -11,124.40 | USD -3,415.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 194/196 (2) | 77.32% (70.93–82.65%) | USD 123.61 | USD 23,979.60 | USD -29,537.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 194/196 (2) | 19.59% (14.62–25.74%) | USD -525.00 | USD -101,850.40 | USD -4,216.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 194/196 (2) | 30.41% (24.37–37.21%) | USD -286.71 | USD -55,622.00 | USD -17,078.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/196 (2) | 28.35% (22.48–35.07%) | USD -58.53 | USD -11,354.40 | USD -3,415.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/196 (2) | 77.32% (70.93–82.65%) | USD 118.43 | USD 22,974.60 | USD -29,537.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/196 (2) | 20.10% (15.07–26.30%) | USD -528.12 | USD -102,455.40 | USD -4,205.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/196 (2) | 28.35% (22.48–35.07%) | USD -292.64 | USD -56,772.00 | USD -17,078.00 |
| HOLD_15_SESSIONS | 1 : 1 | 181/196 (15) | 30.39% (24.15–37.44%) | USD -51.95 | USD -9,403.60 | USD -3,549.60 |
| HOLD_15_SESSIONS | 1 : 6 | 181/196 (15) | 77.90% (71.31–83.33%) | USD 176.85 | USD 32,009.90 | USD -45,081.10 |
| HOLD_15_SESSIONS | 6 : 1 | 181/196 (15) | 17.68% (12.81–23.89%) | USD -540.53 | USD -97,835.10 | USD -4,828.10 |
| HOLD_15_SESSIONS | 5 : 5 | 181/196 (15) | 30.39% (24.15–37.44%) | USD -259.77 | USD -47,018.00 | USD -17,748.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 187/196 (9) | 32.09% (25.81–39.08%) | USD -46.82 | USD -8,756.20 | USD -3,549.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 187/196 (9) | 79.14% (72.76–84.35%) | USD 197.93 | USD 37,013.30 | USD -45,081.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 187/196 (9) | 19.25% (14.24–25.50%) | USD -525.70 | USD -98,306.70 | USD -4,785.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 187/196 (9) | 32.09% (25.81–39.08%) | USD -234.12 | USD -43,781.00 | USD -17,748.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 193/196 (3) | 30.57% (24.50–37.40%) | USD -49.52 | USD -9,557.80 | USD -3,415.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 193/196 (3) | 77.72% (71.34–83.02%) | USD 227.27 | USD 43,862.70 | USD -29,537.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 193/196 (3) | 20.21% (15.15–26.43%) | USD -573.92 | USD -110,767.30 | USD -4,205.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 193/196 (3) | 30.57% (24.50–37.40%) | USD -247.61 | USD -47,789.00 | USD -17,078.00 |
| HOLD_20_SESSIONS | 1 : 1 | 34/196 (162) | 23.53% (12.44–40.00%) | USD -62.92 | USD -2,139.40 | USD -876.60 |
| HOLD_20_SESSIONS | 1 : 6 | 34/196 (162) | 82.35% (66.49–91.65%) | USD 809.99 | USD 27,539.60 | USD -16,772.10 |
| HOLD_20_SESSIONS | 6 : 1 | 34/196 (162) | 14.71% (6.45–30.13%) | USD -1,250.45 | USD -42,515.40 | USD -4,145.10 |
| HOLD_20_SESSIONS | 5 : 5 | 34/196 (162) | 23.53% (12.44–40.00%) | USD -314.62 | USD -10,697.00 | USD -4,383.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 183/196 (13) | 31.69% (25.39–38.75%) | USD -40.39 | USD -7,390.80 | USD -3,549.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 183/196 (13) | 84.70% (78.78–89.20%) | USD 349.12 | USD 63,889.70 | USD -45,081.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 183/196 (13) | 16.94% (12.20–23.04%) | USD -631.83 | USD -115,625.30 | USD -4,785.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 183/196 (13) | 31.69% (25.39–38.75%) | USD -201.93 | USD -36,954.00 | USD -17,748.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 193/196 (3) | 30.57% (24.50–37.40%) | USD -49.52 | USD -9,557.80 | USD -3,415.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 193/196 (3) | 77.72% (71.34–83.02%) | USD 227.27 | USD 43,862.70 | USD -29,537.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 193/196 (3) | 20.21% (15.15–26.43%) | USD -573.92 | USD -110,767.30 | USD -4,205.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 193/196 (3) | 30.57% (24.50–37.40%) | USD -247.61 | USD -47,789.00 | USD -17,078.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -207,175.34 | USD -339,101.55 |
| -75% | 0/196 | 0.00% | USD -153,083.54 | USD -251,365.55 |
| -50% | 0/196 | 0.00% | USD -98,991.75 | USD -163,629.55 |
| -40% | 0/196 | 0.00% | USD -77,355.04 | USD -128,535.15 |
| -30% | 0/196 | 0.00% | USD -55,718.32 | USD -93,603.65 |
| -25% | 0/196 | 0.00% | USD -44,899.96 | USD -76,160.80 |
| -20% | 0/196 | 0.00% | USD -34,081.61 | USD -58,717.95 |
| -15% | 1/196 | 0.51% | USD -23,289.71 | USD -41,299.55 |
| -10% | 3/196 | 1.53% | USD -12,546.91 | USD -24,063.25 |
| -5% | 58/196 | 29.59% | USD -2,243.12 | USD -9,809.90 |
| 0% | 196/196 | 100.00% | USD 1,627.18 | USD 56.45 |
| 5% | 196/196 | 100.00% | USD 1,627.18 | USD 56.45 |
| 10% | 196/196 | 100.00% | USD 1,627.18 | USD 56.45 |
| 20% | 196/196 | 100.00% | USD 1,627.18 | USD 56.45 |

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