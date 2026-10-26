# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 448.11 / USD 2,625.44; mean absolute mismatch USD 2,177.34; mean match score 16.85%.
- Actual selected contract ratios: {'1:6': 176}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 177; entered cohorts: 176; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 176/176 | 119/57/0 | 67.61% (60.39–74.09%) | USD 1.63 | USD 386.40 | USD 287.40 | USD -17,582.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 176/176 | 119/57/0 | 67.61% (60.39–74.09%) | USD 1.63 | USD 386.40 | USD 287.40 | USD -17,582.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 176/176 | 119/57/0 | 67.61% (60.39–74.09%) | USD 1.63 | USD 386.40 | USD 287.40 | USD -17,582.10 | 0 |
| HOLD_10_SESSIONS | 175/176 | 136/39/0 | 77.71% (70.99–83.25%) | USD 357.76 | USD 837.90 | USD 62,608.50 | USD -15,575.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 175/176 | 136/39/0 | 77.71% (70.99–83.25%) | USD 357.76 | USD 837.90 | USD 62,608.50 | USD -15,575.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 175/176 | 136/39/0 | 77.71% (70.99–83.25%) | USD 357.76 | USD 837.90 | USD 62,608.50 | USD -15,575.10 | 1 |
| HOLD_15_SESSIONS | 175/176 | 137/38/0 | 78.29% (71.61–83.75%) | USD 299.11 | USD 1,086.90 | USD 52,344.50 | USD -34,139.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 175/176 | 137/38/0 | 78.29% (71.61–83.75%) | USD 299.11 | USD 1,086.90 | USD 52,344.50 | USD -34,139.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 175/176 | 137/38/0 | 78.29% (71.61–83.75%) | USD 299.11 | USD 1,086.90 | USD 52,344.50 | USD -34,139.10 | 1 |
| HOLD_20_SESSIONS | 174/176 | 144/30/0 | 82.76% (76.45–87.65%) | USD 671.49 | USD 1,464.90 | USD 116,838.60 | USD -39,445.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 174/176 | 144/30/0 | 82.76% (76.45–87.65%) | USD 671.49 | USD 1,464.90 | USD 116,838.60 | USD -39,445.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 174/176 | 145/29/0 | 83.33% (77.09–88.14%) | USD 699.77 | USD 1,405.40 | USD 121,760.60 | USD -32,410.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -30.40 | USD 111.14 |
| HOLD_5_OR_DTE_LE_7 | USD -30.40 | USD 111.14 |
| HOLD_5_OR_DTE_LE_14 | USD -30.40 | USD 111.14 |
| HOLD_10_SESSIONS | USD -98.17 | USD 535.03 |
| HOLD_10_OR_DTE_LE_7 | USD -98.17 | USD 535.03 |
| HOLD_10_OR_DTE_LE_14 | USD -98.17 | USD 535.03 |
| HOLD_15_SESSIONS | USD -104.60 | USD 482.81 |
| HOLD_15_OR_DTE_LE_7 | USD -104.60 | USD 482.81 |
| HOLD_15_OR_DTE_LE_14 | USD -104.60 | USD 482.81 |
| HOLD_20_SESSIONS | USD -171.83 | USD 922.41 |
| HOLD_20_OR_DTE_LE_7 | USD -171.83 | USD 922.41 |
| HOLD_20_OR_DTE_LE_14 | USD -168.82 | USD 947.69 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 176 | 68.75% | USD 80.73 | USD 14,209.00 | USD -17,503.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 176 | 68.18% | USD 71.63 | USD 12,607.40 | USD -17,512.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 176 | 68.18% | USD 45.73 | USD 8,049.00 | USD -17,538.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 176 | 68.18% | USD 36.63 | USD 6,447.40 | USD -17,547.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 176 | 67.61% | USD 10.73 | USD 1,889.00 | USD -17,573.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 176 | 67.61% | USD 1.63 | USD 287.40 | USD -17,582.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 176 | 66.48% | USD -59.27 | USD -10,431.00 | USD -17,643.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 176 | 65.91% | USD -68.37 | USD -12,032.60 | USD -17,652.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 176 | 68.75% | USD 80.73 | USD 14,209.00 | USD -17,503.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 176 | 68.18% | USD 71.63 | USD 12,607.40 | USD -17,512.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 176 | 68.18% | USD 45.73 | USD 8,049.00 | USD -17,538.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 176 | 68.18% | USD 36.63 | USD 6,447.40 | USD -17,547.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 176 | 67.61% | USD 10.73 | USD 1,889.00 | USD -17,573.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 176 | 67.61% | USD 1.63 | USD 287.40 | USD -17,582.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 176 | 66.48% | USD -59.27 | USD -10,431.00 | USD -17,643.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 176 | 65.91% | USD -68.37 | USD -12,032.60 | USD -17,652.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 176 | 68.75% | USD 80.73 | USD 14,209.00 | USD -17,503.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 176 | 68.18% | USD 71.63 | USD 12,607.40 | USD -17,512.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 176 | 68.18% | USD 45.73 | USD 8,049.00 | USD -17,538.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 176 | 68.18% | USD 36.63 | USD 6,447.40 | USD -17,547.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 176 | 67.61% | USD 10.73 | USD 1,889.00 | USD -17,573.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 176 | 67.61% | USD 1.63 | USD 287.40 | USD -17,582.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 176 | 66.48% | USD -59.27 | USD -10,431.00 | USD -17,643.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 176 | 65.91% | USD -68.37 | USD -12,032.60 | USD -17,652.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 175 | 79.43% | USD 436.86 | USD 76,451.00 | USD -15,496.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 175 | 79.43% | USD 427.76 | USD 74,858.50 | USD -15,505.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 175 | 78.29% | USD 401.86 | USD 70,326.00 | USD -15,531.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 175 | 77.71% | USD 392.76 | USD 68,733.50 | USD -15,540.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 175 | 77.71% | USD 366.86 | USD 64,201.00 | USD -15,566.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 175 | 77.71% | USD 357.76 | USD 62,608.50 | USD -15,575.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 175 | 77.14% | USD 296.86 | USD 51,951.00 | USD -15,636.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 175 | 77.14% | USD 287.76 | USD 50,358.50 | USD -15,645.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 175 | 79.43% | USD 436.86 | USD 76,451.00 | USD -15,496.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 175 | 79.43% | USD 427.76 | USD 74,858.50 | USD -15,505.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 175 | 78.29% | USD 401.86 | USD 70,326.00 | USD -15,531.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 175 | 77.71% | USD 392.76 | USD 68,733.50 | USD -15,540.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 175 | 77.71% | USD 366.86 | USD 64,201.00 | USD -15,566.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 175 | 77.71% | USD 357.76 | USD 62,608.50 | USD -15,575.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 175 | 77.14% | USD 296.86 | USD 51,951.00 | USD -15,636.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 175 | 77.14% | USD 287.76 | USD 50,358.50 | USD -15,645.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 175 | 79.43% | USD 436.86 | USD 76,451.00 | USD -15,496.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 175 | 79.43% | USD 427.76 | USD 74,858.50 | USD -15,505.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 175 | 78.29% | USD 401.86 | USD 70,326.00 | USD -15,531.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 175 | 77.71% | USD 392.76 | USD 68,733.50 | USD -15,540.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 175 | 77.71% | USD 366.86 | USD 64,201.00 | USD -15,566.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 175 | 77.71% | USD 357.76 | USD 62,608.50 | USD -15,575.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 175 | 77.14% | USD 296.86 | USD 51,951.00 | USD -15,636.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 175 | 77.14% | USD 287.76 | USD 50,358.50 | USD -15,645.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 175 | 78.29% | USD 378.21 | USD 66,187.00 | USD -34,060.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 175 | 78.29% | USD 369.11 | USD 64,594.50 | USD -34,069.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 175 | 78.29% | USD 343.21 | USD 60,062.00 | USD -34,095.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 175 | 78.29% | USD 334.11 | USD 58,469.50 | USD -34,104.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 175 | 78.29% | USD 308.21 | USD 53,937.00 | USD -34,130.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 175 | 78.29% | USD 299.11 | USD 52,344.50 | USD -34,139.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 175 | 77.71% | USD 238.21 | USD 41,687.00 | USD -34,200.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 175 | 77.71% | USD 229.11 | USD 40,094.50 | USD -34,209.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 175 | 78.29% | USD 378.21 | USD 66,187.00 | USD -34,060.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 175 | 78.29% | USD 369.11 | USD 64,594.50 | USD -34,069.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 175 | 78.29% | USD 343.21 | USD 60,062.00 | USD -34,095.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 175 | 78.29% | USD 334.11 | USD 58,469.50 | USD -34,104.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 175 | 78.29% | USD 308.21 | USD 53,937.00 | USD -34,130.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 175 | 78.29% | USD 299.11 | USD 52,344.50 | USD -34,139.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 175 | 77.71% | USD 238.21 | USD 41,687.00 | USD -34,200.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 175 | 77.71% | USD 229.11 | USD 40,094.50 | USD -34,209.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 175 | 78.29% | USD 378.21 | USD 66,187.00 | USD -34,060.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 175 | 78.29% | USD 369.11 | USD 64,594.50 | USD -34,069.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 175 | 78.29% | USD 343.21 | USD 60,062.00 | USD -34,095.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 175 | 78.29% | USD 334.11 | USD 58,469.50 | USD -34,104.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 175 | 78.29% | USD 308.21 | USD 53,937.00 | USD -34,130.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 175 | 78.29% | USD 299.11 | USD 52,344.50 | USD -34,139.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 175 | 77.71% | USD 238.21 | USD 41,687.00 | USD -34,200.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 175 | 77.71% | USD 229.11 | USD 40,094.50 | USD -34,209.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 174 | 82.76% | USD 750.59 | USD 130,602.00 | USD -39,366.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 174 | 82.76% | USD 741.49 | USD 129,018.60 | USD -39,375.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 174 | 82.76% | USD 715.59 | USD 124,512.00 | USD -39,401.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 174 | 82.76% | USD 706.49 | USD 122,928.60 | USD -39,410.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 174 | 82.76% | USD 680.59 | USD 118,422.00 | USD -39,436.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 174 | 82.76% | USD 671.49 | USD 116,838.60 | USD -39,445.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 174 | 82.76% | USD 610.59 | USD 106,242.00 | USD -39,506.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 174 | 82.76% | USD 601.49 | USD 104,658.60 | USD -39,515.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 174 | 82.76% | USD 750.59 | USD 130,602.00 | USD -39,366.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 174 | 82.76% | USD 741.49 | USD 129,018.60 | USD -39,375.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 174 | 82.76% | USD 715.59 | USD 124,512.00 | USD -39,401.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 174 | 82.76% | USD 706.49 | USD 122,928.60 | USD -39,410.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 174 | 82.76% | USD 680.59 | USD 118,422.00 | USD -39,436.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 174 | 82.76% | USD 671.49 | USD 116,838.60 | USD -39,445.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 174 | 82.76% | USD 610.59 | USD 106,242.00 | USD -39,506.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 174 | 82.76% | USD 601.49 | USD 104,658.60 | USD -39,515.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 174 | 83.33% | USD 778.87 | USD 135,524.00 | USD -32,331.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 174 | 83.33% | USD 769.77 | USD 133,940.60 | USD -32,340.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 174 | 83.33% | USD 743.87 | USD 129,434.00 | USD -32,366.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 174 | 83.33% | USD 734.77 | USD 127,850.60 | USD -32,375.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 174 | 83.33% | USD 708.87 | USD 123,344.00 | USD -32,401.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 174 | 83.33% | USD 699.77 | USD 121,760.60 | USD -32,410.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 174 | 83.33% | USD 638.87 | USD 111,164.00 | USD -32,471.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 174 | 83.33% | USD 629.77 | USD 109,580.60 | USD -32,480.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 176/176 (0) | 30.68% (24.34–37.85%) | USD -34.48 | USD -6,068.60 | USD -793.60 |
| HOLD_5_SESSIONS | 1 : 6 | 176/176 (0) | 67.61% (60.39–74.09%) | USD 1.63 | USD 287.40 | USD -17,582.10 |
| HOLD_5_SESSIONS | 6 : 1 | 176/176 (0) | 26.70% (20.72–33.69%) | USD -243.00 | USD -42,767.60 | USD -4,306.10 |
| HOLD_5_SESSIONS | 5 : 5 | 176/176 (0) | 30.68% (24.34–37.85%) | USD -172.40 | USD -30,343.00 | USD -3,968.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 176/176 (0) | 30.68% (24.34–37.85%) | USD -34.48 | USD -6,068.60 | USD -793.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 176/176 (0) | 67.61% (60.39–74.09%) | USD 1.63 | USD 287.40 | USD -17,582.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 176/176 (0) | 26.70% (20.72–33.69%) | USD -243.00 | USD -42,767.60 | USD -4,306.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 176/176 (0) | 30.68% (24.34–37.85%) | USD -172.40 | USD -30,343.00 | USD -3,968.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 176/176 (0) | 30.68% (24.34–37.85%) | USD -34.48 | USD -6,068.60 | USD -793.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 176/176 (0) | 67.61% (60.39–74.09%) | USD 1.63 | USD 287.40 | USD -17,582.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 176/176 (0) | 26.70% (20.72–33.69%) | USD -243.00 | USD -42,767.60 | USD -4,306.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 176/176 (0) | 30.68% (24.34–37.85%) | USD -172.40 | USD -30,343.00 | USD -3,968.00 |
| HOLD_10_SESSIONS | 1 : 1 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -31.59 | USD -5,529.00 | USD -1,623.60 |
| HOLD_10_SESSIONS | 1 : 6 | 175/176 (1) | 77.71% (70.99–83.25%) | USD 357.76 | USD 62,608.50 | USD -15,575.10 |
| HOLD_10_SESSIONS | 6 : 1 | 175/176 (1) | 23.43% (17.77–30.23%) | USD -578.92 | USD -101,311.50 | USD -3,854.10 |
| HOLD_10_SESSIONS | 5 : 5 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -157.97 | USD -27,645.00 | USD -8,118.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -31.59 | USD -5,529.00 | USD -1,623.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 175/176 (1) | 77.71% (70.99–83.25%) | USD 357.76 | USD 62,608.50 | USD -15,575.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 175/176 (1) | 23.43% (17.77–30.23%) | USD -578.92 | USD -101,311.50 | USD -3,854.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -157.97 | USD -27,645.00 | USD -8,118.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -31.59 | USD -5,529.00 | USD -1,623.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 175/176 (1) | 77.71% (70.99–83.25%) | USD 357.76 | USD 62,608.50 | USD -15,575.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 175/176 (1) | 23.43% (17.77–30.23%) | USD -578.92 | USD -101,311.50 | USD -3,854.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -157.97 | USD -27,645.00 | USD -8,118.00 |
| HOLD_15_SESSIONS | 1 : 1 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -46.73 | USD -8,178.00 | USD -3,397.60 |
| HOLD_15_SESSIONS | 1 : 6 | 175/176 (1) | 78.29% (71.61–83.75%) | USD 299.11 | USD 52,344.50 | USD -34,139.10 |
| HOLD_15_SESSIONS | 6 : 1 | 175/176 (1) | 21.14% (15.75–27.78%) | USD -626.23 | USD -109,590.50 | USD -5,076.10 |
| HOLD_15_SESSIONS | 5 : 5 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -233.66 | USD -40,890.00 | USD -16,988.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -46.73 | USD -8,178.00 | USD -3,397.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 175/176 (1) | 78.29% (71.61–83.75%) | USD 299.11 | USD 52,344.50 | USD -34,139.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 175/176 (1) | 21.14% (15.75–27.78%) | USD -626.23 | USD -109,590.50 | USD -5,076.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -233.66 | USD -40,890.00 | USD -16,988.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -46.73 | USD -8,178.00 | USD -3,397.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 175/176 (1) | 78.29% (71.61–83.75%) | USD 299.11 | USD 52,344.50 | USD -34,139.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 175/176 (1) | 21.14% (15.75–27.78%) | USD -626.23 | USD -109,590.50 | USD -5,076.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 175/176 (1) | 34.86% (28.19–42.17%) | USD -233.66 | USD -40,890.00 | USD -16,988.00 |
| HOLD_20_SESSIONS | 1 : 1 | 174/176 (2) | 35.63% (28.90–42.99%) | USD -40.69 | USD -7,080.40 | USD -3,333.60 |
| HOLD_20_SESSIONS | 1 : 6 | 174/176 (2) | 82.76% (76.45–87.65%) | USD 671.49 | USD 116,838.60 | USD -39,445.10 |
| HOLD_20_SESSIONS | 6 : 1 | 174/176 (2) | 13.79% (9.45–19.70%) | USD -956.33 | USD -166,401.40 | USD -5,301.10 |
| HOLD_20_SESSIONS | 5 : 5 | 174/176 (2) | 35.63% (28.90–42.99%) | USD -203.46 | USD -35,402.00 | USD -16,668.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 174/176 (2) | 35.63% (28.90–42.99%) | USD -40.69 | USD -7,080.40 | USD -3,333.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 174/176 (2) | 82.76% (76.45–87.65%) | USD 671.49 | USD 116,838.60 | USD -39,445.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 174/176 (2) | 13.79% (9.45–19.70%) | USD -956.33 | USD -166,401.40 | USD -5,301.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 174/176 (2) | 35.63% (28.90–42.99%) | USD -203.46 | USD -35,402.00 | USD -16,668.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 174/176 (2) | 37.36% (30.51–44.74%) | USD -33.47 | USD -5,823.40 | USD -3,733.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 174/176 (2) | 83.33% (77.09–88.14%) | USD 699.77 | USD 121,760.60 | USD -32,410.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 174/176 (2) | 13.79% (9.45–19.70%) | USD -934.05 | USD -162,524.40 | USD -5,086.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 174/176 (2) | 37.36% (30.51–44.74%) | USD -167.34 | USD -29,117.00 | USD -18,668.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/176 | 0.00% | USD -206,077.68 | USD -337,580.55 |
| -75% | 0/176 | 0.00% | USD -151,824.68 | USD -250,998.30 |
| -50% | 0/176 | 0.00% | USD -97,571.67 | USD -164,416.05 |
| -40% | 0/176 | 0.00% | USD -75,870.47 | USD -129,783.15 |
| -30% | 0/176 | 0.00% | USD -54,169.27 | USD -95,150.25 |
| -25% | 0/176 | 0.00% | USD -43,318.67 | USD -77,833.80 |
| -20% | 1/176 | 0.57% | USD -32,468.07 | USD -60,517.35 |
| -15% | 2/176 | 1.14% | USD -21,655.48 | USD -43,200.90 |
| -10% | 4/176 | 2.27% | USD -10,884.51 | USD -25,884.45 |
| -5% | 83/176 | 47.16% | USD -773.64 | USD -8,568.00 |
| 0% | 176/176 | 100.00% | USD 2,137.79 | USD 585.45 |
| 5% | 176/176 | 100.00% | USD 2,137.79 | USD 585.45 |
| 10% | 176/176 | 100.00% | USD 2,137.79 | USD 585.45 |
| 20% | 176/176 | 100.00% | USD 2,137.79 | USD 585.45 |

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