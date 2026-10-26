# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 359.70 / USD 2,143.19; mean absolute mismatch USD 1,783.49; mean match score 16.76%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 139/57/0 | 70.92% (64.21–76.83%) | USD 222.60 | USD 470.40 | USD 43,629.40 | USD -4,759.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 196/196 | 139/57/0 | 70.92% (64.21–76.83%) | USD 222.60 | USD 470.40 | USD 43,629.40 | USD -4,759.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 196/196 | 139/57/0 | 70.92% (64.21–76.83%) | USD 222.60 | USD 470.40 | USD 43,629.40 | USD -4,759.10 | 0 |
| HOLD_10_SESSIONS | 195/196 | 152/43/0 | 77.95% (71.62–83.20%) | USD 320.43 | USD 857.90 | USD 62,484.50 | USD -15,463.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 195/196 | 152/43/0 | 77.95% (71.62–83.20%) | USD 320.43 | USD 857.90 | USD 62,484.50 | USD -15,463.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 195/196 | 149/46/0 | 76.41% (69.98–81.82%) | USD 326.47 | USD 884.90 | USD 63,661.50 | USD -15,463.10 | 1 |
| HOLD_15_SESSIONS | 184/196 | 155/29/0 | 84.24% (78.28–88.80%) | USD 417.12 | USD 1,191.40 | USD 76,749.60 | USD -31,416.10 | 12 |
| HOLD_15_OR_DTE_LE_7 | 192/196 | 161/31/0 | 83.85% (77.99–88.39%) | USD 296.60 | USD 1,153.40 | USD 56,946.80 | USD -31,416.10 | 4 |
| HOLD_15_OR_DTE_LE_14 | 195/196 | 151/44/0 | 77.44% (71.07–82.74%) | USD 198.92 | USD 903.90 | USD 38,788.50 | USD -26,188.10 | 1 |
| HOLD_20_SESSIONS | 31/196 | 25/6/0 | 80.65% (63.72–90.81%) | USD -608.78 | USD 1,754.90 | USD -18,872.10 | USD -29,979.10 | 165 |
| HOLD_20_OR_DTE_LE_7 | 188/196 | 157/31/0 | 83.51% (77.55–88.13%) | USD 269.14 | USD 1,216.40 | USD 50,599.20 | USD -27,758.10 | 8 |
| HOLD_20_OR_DTE_LE_14 | 195/196 | 151/44/0 | 77.44% (71.07–82.74%) | USD 198.92 | USD 903.90 | USD 38,788.50 | USD -26,188.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -79.52 | USD 381.21 |
| HOLD_5_OR_DTE_LE_7 | USD -79.52 | USD 381.21 |
| HOLD_5_OR_DTE_LE_14 | USD -79.52 | USD 381.21 |
| HOLD_10_SESSIONS | USD -108.56 | USD 508.09 |
| HOLD_10_OR_DTE_LE_7 | USD -108.56 | USD 508.09 |
| HOLD_10_OR_DTE_LE_14 | USD -104.92 | USD 510.49 |
| HOLD_15_SESSIONS | USD -142.95 | USD 639.16 |
| HOLD_15_OR_DTE_LE_7 | USD -110.90 | USD 486.59 |
| HOLD_15_OR_DTE_LE_14 | USD -88.26 | USD 366.28 |
| HOLD_20_SESSIONS | USD -162.71 | USD -366.97 |
| HOLD_20_OR_DTE_LE_7 | USD -104.85 | USD 453.10 |
| HOLD_20_OR_DTE_LE_14 | USD -88.26 | USD 366.28 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 71.94% | USD 301.70 | USD 59,133.00 | USD -4,680.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 71.94% | USD 292.60 | USD 57,349.40 | USD -4,689.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 71.94% | USD 266.70 | USD 52,273.00 | USD -4,715.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 71.94% | USD 257.60 | USD 50,489.40 | USD -4,724.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 71.43% | USD 231.70 | USD 45,413.00 | USD -4,750.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 70.92% | USD 222.60 | USD 43,629.40 | USD -4,759.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 68.37% | USD 161.70 | USD 31,693.00 | USD -4,820.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 68.37% | USD 152.60 | USD 29,909.40 | USD -4,829.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 196 | 71.94% | USD 301.70 | USD 59,133.00 | USD -4,680.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 196 | 71.94% | USD 292.60 | USD 57,349.40 | USD -4,689.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 196 | 71.94% | USD 266.70 | USD 52,273.00 | USD -4,715.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 196 | 71.94% | USD 257.60 | USD 50,489.40 | USD -4,724.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 196 | 71.43% | USD 231.70 | USD 45,413.00 | USD -4,750.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 196 | 70.92% | USD 222.60 | USD 43,629.40 | USD -4,759.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 196 | 68.37% | USD 161.70 | USD 31,693.00 | USD -4,820.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 196 | 68.37% | USD 152.60 | USD 29,909.40 | USD -4,829.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 196 | 71.94% | USD 301.70 | USD 59,133.00 | USD -4,680.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 196 | 71.94% | USD 292.60 | USD 57,349.40 | USD -4,689.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 196 | 71.94% | USD 266.70 | USD 52,273.00 | USD -4,715.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 196 | 71.94% | USD 257.60 | USD 50,489.40 | USD -4,724.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 196 | 71.43% | USD 231.70 | USD 45,413.00 | USD -4,750.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 196 | 70.92% | USD 222.60 | USD 43,629.40 | USD -4,759.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 196 | 68.37% | USD 161.70 | USD 31,693.00 | USD -4,820.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 196 | 68.37% | USD 152.60 | USD 29,909.40 | USD -4,829.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 78.97% | USD 399.53 | USD 77,909.00 | USD -15,384.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 78.97% | USD 390.43 | USD 76,134.50 | USD -15,393.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 78.46% | USD 364.53 | USD 71,084.00 | USD -15,419.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 78.46% | USD 355.43 | USD 69,309.50 | USD -15,428.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 77.95% | USD 329.53 | USD 64,259.00 | USD -15,454.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 77.95% | USD 320.43 | USD 62,484.50 | USD -15,463.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 77.44% | USD 259.53 | USD 50,609.00 | USD -15,524.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 76.92% | USD 250.43 | USD 48,834.50 | USD -15,533.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 195 | 78.97% | USD 399.53 | USD 77,909.00 | USD -15,384.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 195 | 78.97% | USD 390.43 | USD 76,134.50 | USD -15,393.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 195 | 78.46% | USD 364.53 | USD 71,084.00 | USD -15,419.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 195 | 78.46% | USD 355.43 | USD 69,309.50 | USD -15,428.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 195 | 77.95% | USD 329.53 | USD 64,259.00 | USD -15,454.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 195 | 77.95% | USD 320.43 | USD 62,484.50 | USD -15,463.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 195 | 77.44% | USD 259.53 | USD 50,609.00 | USD -15,524.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 195 | 76.92% | USD 250.43 | USD 48,834.50 | USD -15,533.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 77.44% | USD 405.57 | USD 79,086.00 | USD -15,384.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 77.44% | USD 396.47 | USD 77,311.50 | USD -15,393.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 76.92% | USD 370.57 | USD 72,261.00 | USD -15,419.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 76.92% | USD 361.47 | USD 70,486.50 | USD -15,428.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 76.41% | USD 335.57 | USD 65,436.00 | USD -15,454.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 76.41% | USD 326.47 | USD 63,661.50 | USD -15,463.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 75.90% | USD 265.57 | USD 51,786.00 | USD -15,524.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 75.90% | USD 256.47 | USD 50,011.50 | USD -15,533.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 184 | 84.24% | USD 496.22 | USD 91,304.00 | USD -31,337.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 184 | 84.24% | USD 487.12 | USD 89,629.60 | USD -31,346.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 184 | 84.24% | USD 461.22 | USD 84,864.00 | USD -31,372.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 184 | 84.24% | USD 452.12 | USD 83,189.60 | USD -31,381.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 184 | 84.24% | USD 426.22 | USD 78,424.00 | USD -31,407.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 184 | 84.24% | USD 417.12 | USD 76,749.60 | USD -31,416.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 184 | 83.70% | USD 356.22 | USD 65,544.00 | USD -31,477.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 184 | 83.15% | USD 347.12 | USD 63,869.60 | USD -31,486.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 83.85% | USD 375.70 | USD 72,134.00 | USD -31,337.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 83.85% | USD 366.60 | USD 70,386.80 | USD -31,346.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 83.85% | USD 340.70 | USD 65,414.00 | USD -31,372.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 83.85% | USD 331.60 | USD 63,666.80 | USD -31,381.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 83.85% | USD 305.70 | USD 58,694.00 | USD -31,407.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 83.85% | USD 296.60 | USD 56,946.80 | USD -31,416.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 82.29% | USD 235.70 | USD 45,254.00 | USD -31,477.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 82.29% | USD 226.60 | USD 43,506.80 | USD -31,486.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 77.95% | USD 278.02 | USD 54,213.00 | USD -26,109.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 77.95% | USD 268.92 | USD 52,438.50 | USD -26,118.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 77.95% | USD 243.02 | USD 47,388.00 | USD -26,144.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 77.95% | USD 233.92 | USD 45,613.50 | USD -26,153.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 77.44% | USD 208.02 | USD 40,563.00 | USD -26,179.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 77.44% | USD 198.92 | USD 38,788.50 | USD -26,188.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 76.92% | USD 138.02 | USD 26,913.00 | USD -26,249.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 76.92% | USD 128.92 | USD 25,138.50 | USD -26,258.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 31 | 80.65% | USD -529.68 | USD -16,420.00 | USD -29,900.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 31 | 80.65% | USD -538.78 | USD -16,702.10 | USD -29,909.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 31 | 80.65% | USD -564.68 | USD -17,505.00 | USD -29,935.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 31 | 80.65% | USD -573.78 | USD -17,787.10 | USD -29,944.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 31 | 80.65% | USD -599.68 | USD -18,590.00 | USD -29,970.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 31 | 80.65% | USD -608.78 | USD -18,872.10 | USD -29,979.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 31 | 80.65% | USD -669.68 | USD -20,760.00 | USD -30,040.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 31 | 80.65% | USD -678.78 | USD -21,042.10 | USD -30,049.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 188 | 84.04% | USD 348.24 | USD 65,470.00 | USD -27,679.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 188 | 83.51% | USD 339.14 | USD 63,759.20 | USD -27,688.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 188 | 83.51% | USD 313.24 | USD 58,890.00 | USD -27,714.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 188 | 83.51% | USD 304.14 | USD 57,179.20 | USD -27,723.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 188 | 83.51% | USD 278.24 | USD 52,310.00 | USD -27,749.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 188 | 83.51% | USD 269.14 | USD 50,599.20 | USD -27,758.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 188 | 82.45% | USD 208.24 | USD 39,150.00 | USD -27,819.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 188 | 82.45% | USD 199.14 | USD 37,439.20 | USD -27,828.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 77.95% | USD 278.02 | USD 54,213.00 | USD -26,109.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 77.95% | USD 268.92 | USD 52,438.50 | USD -26,118.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 77.95% | USD 243.02 | USD 47,388.00 | USD -26,144.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 77.95% | USD 233.92 | USD 45,613.50 | USD -26,153.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 77.44% | USD 208.02 | USD 40,563.00 | USD -26,179.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 77.44% | USD 198.92 | USD 38,788.50 | USD -26,188.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 76.92% | USD 138.02 | USD 26,913.00 | USD -26,249.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 76.92% | USD 128.92 | USD 25,138.50 | USD -26,258.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 30.61% (24.58–37.39%) | USD -38.58 | USD -7,561.60 | USD -558.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 70.92% (64.21–76.83%) | USD 222.60 | USD 43,629.40 | USD -4,759.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 22.45% (17.17–28.79%) | USD -492.66 | USD -96,560.60 | USD -4,333.10 |
| HOLD_5_SESSIONS | 5 : 5 | 196/196 (0) | 30.61% (24.58–37.39%) | USD -192.90 | USD -37,808.00 | USD -2,793.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 196/196 (0) | 30.61% (24.58–37.39%) | USD -38.58 | USD -7,561.60 | USD -558.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 196/196 (0) | 70.92% (64.21–76.83%) | USD 222.60 | USD 43,629.40 | USD -4,759.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 196/196 (0) | 22.45% (17.17–28.79%) | USD -492.66 | USD -96,560.60 | USD -4,333.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 196/196 (0) | 30.61% (24.58–37.39%) | USD -192.90 | USD -37,808.00 | USD -2,793.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 196/196 (0) | 30.61% (24.58–37.39%) | USD -38.58 | USD -7,561.60 | USD -558.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 196/196 (0) | 70.92% (64.21–76.83%) | USD 222.60 | USD 43,629.40 | USD -4,759.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 196/196 (0) | 22.45% (17.17–28.79%) | USD -492.66 | USD -96,560.60 | USD -4,333.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 196/196 (0) | 30.61% (24.58–37.39%) | USD -192.90 | USD -37,808.00 | USD -2,793.00 |
| HOLD_10_SESSIONS | 1 : 1 | 195/196 (1) | 34.87% (28.53–41.79%) | USD -46.48 | USD -9,063.00 | USD -1,444.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/196 (1) | 77.95% (71.62–83.20%) | USD 320.43 | USD 62,484.50 | USD -15,463.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/196 (1) | 18.97% (14.09–25.06%) | USD -645.77 | USD -125,925.50 | USD -5,374.10 |
| HOLD_10_SESSIONS | 5 : 5 | 195/196 (1) | 34.87% (28.53–41.79%) | USD -232.38 | USD -45,315.00 | USD -7,223.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 195/196 (1) | 34.87% (28.53–41.79%) | USD -46.48 | USD -9,063.00 | USD -1,444.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 195/196 (1) | 77.95% (71.62–83.20%) | USD 320.43 | USD 62,484.50 | USD -15,463.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 195/196 (1) | 18.97% (14.09–25.06%) | USD -645.77 | USD -125,925.50 | USD -5,374.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 195/196 (1) | 34.87% (28.53–41.79%) | USD -232.38 | USD -45,315.00 | USD -7,223.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 34.87% (28.53–41.79%) | USD -42.44 | USD -8,276.00 | USD -1,444.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 76.41% (69.98–81.82%) | USD 326.47 | USD 63,661.50 | USD -15,463.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 20.00% (14.99–26.17%) | USD -623.56 | USD -121,593.50 | USD -5,374.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 34.87% (28.53–41.79%) | USD -212.21 | USD -41,380.00 | USD -7,223.00 |
| HOLD_15_SESSIONS | 1 : 1 | 184/196 (12) | 30.98% (24.74–37.99%) | USD -59.02 | USD -10,859.40 | USD -3,209.60 |
| HOLD_15_SESSIONS | 1 : 6 | 184/196 (12) | 84.24% (78.28–88.80%) | USD 417.12 | USD 76,749.60 | USD -31,416.10 |
| HOLD_15_SESSIONS | 6 : 1 | 184/196 (12) | 14.13% (9.83–19.90%) | USD -830.25 | USD -152,765.40 | USD -5,891.10 |
| HOLD_15_SESSIONS | 5 : 5 | 184/196 (12) | 30.98% (24.74–37.99%) | USD -295.09 | USD -54,297.00 | USD -16,048.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 192/196 (4) | 32.29% (26.08–39.20%) | USD -52.40 | USD -10,060.20 | USD -3,209.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 192/196 (4) | 83.85% (77.99–88.39%) | USD 296.60 | USD 56,946.80 | USD -31,416.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 192/196 (4) | 15.10% (10.73–20.85%) | USD -663.38 | USD -127,368.20 | USD -5,891.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 192/196 (4) | 32.29% (26.08–39.20%) | USD -261.98 | USD -50,301.00 | USD -16,048.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 36.92% (30.46–43.89%) | USD -49.82 | USD -9,714.00 | USD -2,706.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 77.44% (71.07–82.74%) | USD 198.92 | USD 38,788.50 | USD -26,188.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 20.51% (15.44–26.72%) | USD -547.62 | USD -106,786.50 | USD -5,552.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 36.92% (30.46–43.89%) | USD -249.08 | USD -48,570.00 | USD -13,533.00 |
| HOLD_20_SESSIONS | 1 : 1 | 31/196 (165) | 29.03% (16.10–46.59%) | USD -246.47 | USD -7,640.60 | USD -2,707.60 |
| HOLD_20_SESSIONS | 1 : 6 | 31/196 (165) | 80.65% (63.72–90.81%) | USD -608.78 | USD -18,872.10 | USD -29,979.10 |
| HOLD_20_SESSIONS | 6 : 1 | 31/196 (165) | 19.35% (9.19–36.28%) | USD -1,116.52 | USD -34,612.10 | USD -6,910.10 |
| HOLD_20_SESSIONS | 5 : 5 | 31/196 (165) | 29.03% (16.10–46.59%) | USD -1,232.35 | USD -38,203.00 | USD -13,538.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 188/196 (8) | 32.45% (26.16–39.43%) | USD -51.94 | USD -9,763.80 | USD -3,110.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 188/196 (8) | 83.51% (77.55–88.13%) | USD 269.14 | USD 50,599.20 | USD -27,758.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 188/196 (8) | 15.43% (10.96–21.28%) | USD -632.69 | USD -118,945.80 | USD -5,891.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 188/196 (8) | 32.45% (26.16–39.43%) | USD -259.68 | USD -48,819.00 | USD -15,553.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 36.92% (30.46–43.89%) | USD -49.82 | USD -9,714.00 | USD -2,706.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 77.44% (71.07–82.74%) | USD 198.92 | USD 38,788.50 | USD -26,188.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 20.51% (15.44–26.72%) | USD -547.62 | USD -106,786.50 | USD -5,552.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 36.92% (30.46–43.89%) | USD -249.08 | USD -48,570.00 | USD -13,533.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -207,034.06 | USD -335,276.55 |
| -75% | 0/196 | 0.00% | USD -153,130.53 | USD -248,281.05 |
| -50% | 0/196 | 0.00% | USD -99,227.01 | USD -162,168.05 |
| -40% | 0/196 | 0.00% | USD -77,665.60 | USD -127,846.15 |
| -30% | 0/196 | 0.00% | USD -56,104.19 | USD -93,524.25 |
| -25% | 0/196 | 0.00% | USD -45,323.48 | USD -76,363.30 |
| -20% | 0/196 | 0.00% | USD -34,542.77 | USD -59,202.35 |
| -15% | 1/196 | 0.51% | USD -23,765.13 | USD -42,041.40 |
| -10% | 2/196 | 1.02% | USD -13,019.51 | USD -25,390.55 |
| -5% | 53/196 | 27.04% | USD -2,427.21 | USD -8,968.05 |
| 0% | 196/196 | 100.00% | USD 1,738.72 | USD 467.45 |
| 5% | 196/196 | 100.00% | USD 1,743.94 | USD 467.45 |
| 10% | 196/196 | 100.00% | USD 1,743.94 | USD 467.45 |
| 20% | 196/196 | 100.00% | USD 1,743.94 | USD 467.45 |

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