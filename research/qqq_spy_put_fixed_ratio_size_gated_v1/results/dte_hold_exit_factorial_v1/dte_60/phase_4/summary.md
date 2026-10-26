# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 563.74 / USD 3,375.03; mean absolute mismatch USD 2,811.29; mean match score 16.64%.
- Actual selected contract ratios: {'1:6': 119}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 119; entered cohorts: 119; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 119/119 | 80/39/0 | 67.23% (58.37–75.01%) | USD 157.26 | USD 454.90 | USD 18,714.10 | USD -14,623.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 119/119 | 80/39/0 | 67.23% (58.37–75.01%) | USD 157.26 | USD 454.90 | USD 18,714.10 | USD -14,623.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 119/119 | 80/39/0 | 67.23% (58.37–75.01%) | USD 157.26 | USD 454.90 | USD 18,714.10 | USD -14,623.10 | 0 |
| HOLD_10_SESSIONS | 119/119 | 91/28/0 | 76.47% (68.10–83.19%) | USD 379.02 | USD 786.90 | USD 45,103.10 | USD -14,701.10 | 0 |
| HOLD_10_OR_DTE_LE_7 | 119/119 | 91/28/0 | 76.47% (68.10–83.19%) | USD 379.02 | USD 786.90 | USD 45,103.10 | USD -14,701.10 | 0 |
| HOLD_10_OR_DTE_LE_14 | 119/119 | 91/28/0 | 76.47% (68.10–83.19%) | USD 379.02 | USD 786.90 | USD 45,103.10 | USD -14,701.10 | 0 |
| HOLD_15_SESSIONS | 118/119 | 92/26/0 | 77.97% (69.67–84.50%) | USD 605.71 | USD 1,215.40 | USD 71,473.20 | USD -29,728.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 118/119 | 92/26/0 | 77.97% (69.67–84.50%) | USD 605.71 | USD 1,215.40 | USD 71,473.20 | USD -29,728.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 118/119 | 92/26/0 | 77.97% (69.67–84.50%) | USD 605.71 | USD 1,215.40 | USD 71,473.20 | USD -29,728.10 | 1 |
| HOLD_20_SESSIONS | 117/119 | 91/26/0 | 77.78% (69.43–84.36%) | USD 496.26 | USD 1,464.90 | USD 58,062.30 | USD -50,138.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 117/119 | 91/26/0 | 77.78% (69.43–84.36%) | USD 496.26 | USD 1,464.90 | USD 58,062.30 | USD -50,138.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 117/119 | 91/26/0 | 77.78% (69.43–84.36%) | USD 496.26 | USD 1,464.90 | USD 58,062.30 | USD -50,138.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -72.66 | USD 309.03 |
| HOLD_5_OR_DTE_LE_7 | USD -72.66 | USD 309.03 |
| HOLD_5_OR_DTE_LE_14 | USD -72.66 | USD 309.03 |
| HOLD_10_SESSIONS | USD -112.13 | USD 570.25 |
| HOLD_10_OR_DTE_LE_7 | USD -112.13 | USD 570.25 |
| HOLD_10_OR_DTE_LE_14 | USD -112.13 | USD 570.25 |
| HOLD_15_SESSIONS | USD -167.65 | USD 852.46 |
| HOLD_15_OR_DTE_LE_7 | USD -167.65 | USD 852.46 |
| HOLD_15_OR_DTE_LE_14 | USD -167.65 | USD 852.46 |
| HOLD_20_SESSIONS | USD -159.82 | USD 735.18 |
| HOLD_20_OR_DTE_LE_7 | USD -159.82 | USD 735.18 |
| HOLD_20_OR_DTE_LE_14 | USD -159.82 | USD 735.18 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 119 | 69.75% | USD 236.36 | USD 28,127.00 | USD -14,544.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 119 | 69.75% | USD 227.26 | USD 27,044.10 | USD -14,553.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 119 | 68.91% | USD 201.36 | USD 23,962.00 | USD -14,579.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 119 | 68.07% | USD 192.26 | USD 22,879.10 | USD -14,588.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 119 | 67.23% | USD 166.36 | USD 19,797.00 | USD -14,614.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 119 | 67.23% | USD 157.26 | USD 18,714.10 | USD -14,623.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 119 | 65.55% | USD 96.36 | USD 11,467.00 | USD -14,684.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 119 | 65.55% | USD 87.26 | USD 10,384.10 | USD -14,693.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 119 | 69.75% | USD 236.36 | USD 28,127.00 | USD -14,544.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 119 | 69.75% | USD 227.26 | USD 27,044.10 | USD -14,553.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 119 | 68.91% | USD 201.36 | USD 23,962.00 | USD -14,579.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 119 | 68.07% | USD 192.26 | USD 22,879.10 | USD -14,588.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 119 | 67.23% | USD 166.36 | USD 19,797.00 | USD -14,614.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 119 | 67.23% | USD 157.26 | USD 18,714.10 | USD -14,623.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 119 | 65.55% | USD 96.36 | USD 11,467.00 | USD -14,684.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 119 | 65.55% | USD 87.26 | USD 10,384.10 | USD -14,693.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 119 | 69.75% | USD 236.36 | USD 28,127.00 | USD -14,544.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 119 | 69.75% | USD 227.26 | USD 27,044.10 | USD -14,553.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 119 | 68.91% | USD 201.36 | USD 23,962.00 | USD -14,579.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 119 | 68.07% | USD 192.26 | USD 22,879.10 | USD -14,588.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 119 | 67.23% | USD 166.36 | USD 19,797.00 | USD -14,614.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 119 | 67.23% | USD 157.26 | USD 18,714.10 | USD -14,623.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 119 | 65.55% | USD 96.36 | USD 11,467.00 | USD -14,684.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 119 | 65.55% | USD 87.26 | USD 10,384.10 | USD -14,693.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 119 | 78.15% | USD 458.12 | USD 54,516.00 | USD -14,622.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 119 | 78.15% | USD 449.02 | USD 53,433.10 | USD -14,631.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 119 | 78.15% | USD 423.12 | USD 50,351.00 | USD -14,657.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 119 | 78.15% | USD 414.02 | USD 49,268.10 | USD -14,666.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 119 | 76.47% | USD 388.12 | USD 46,186.00 | USD -14,692.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 119 | 76.47% | USD 379.02 | USD 45,103.10 | USD -14,701.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 119 | 72.27% | USD 318.12 | USD 37,856.00 | USD -14,762.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 119 | 72.27% | USD 309.02 | USD 36,773.10 | USD -14,771.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 119 | 78.15% | USD 458.12 | USD 54,516.00 | USD -14,622.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 119 | 78.15% | USD 449.02 | USD 53,433.10 | USD -14,631.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 119 | 78.15% | USD 423.12 | USD 50,351.00 | USD -14,657.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 119 | 78.15% | USD 414.02 | USD 49,268.10 | USD -14,666.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 119 | 76.47% | USD 388.12 | USD 46,186.00 | USD -14,692.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 119 | 76.47% | USD 379.02 | USD 45,103.10 | USD -14,701.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 119 | 72.27% | USD 318.12 | USD 37,856.00 | USD -14,762.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 119 | 72.27% | USD 309.02 | USD 36,773.10 | USD -14,771.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 119 | 78.15% | USD 458.12 | USD 54,516.00 | USD -14,622.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 119 | 78.15% | USD 449.02 | USD 53,433.10 | USD -14,631.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 119 | 78.15% | USD 423.12 | USD 50,351.00 | USD -14,657.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 119 | 78.15% | USD 414.02 | USD 49,268.10 | USD -14,666.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 119 | 76.47% | USD 388.12 | USD 46,186.00 | USD -14,692.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 119 | 76.47% | USD 379.02 | USD 45,103.10 | USD -14,701.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 119 | 72.27% | USD 318.12 | USD 37,856.00 | USD -14,762.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 119 | 72.27% | USD 309.02 | USD 36,773.10 | USD -14,771.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 118 | 77.97% | USD 684.81 | USD 80,807.00 | USD -29,649.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 118 | 77.97% | USD 675.71 | USD 79,733.20 | USD -29,658.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 118 | 77.97% | USD 649.81 | USD 76,677.00 | USD -29,684.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 118 | 77.97% | USD 640.71 | USD 75,603.20 | USD -29,693.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 118 | 77.97% | USD 614.81 | USD 72,547.00 | USD -29,719.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 118 | 77.97% | USD 605.71 | USD 71,473.20 | USD -29,728.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 118 | 77.97% | USD 544.81 | USD 64,287.00 | USD -29,789.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 118 | 77.97% | USD 535.71 | USD 63,213.20 | USD -29,798.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 118 | 77.97% | USD 684.81 | USD 80,807.00 | USD -29,649.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 118 | 77.97% | USD 675.71 | USD 79,733.20 | USD -29,658.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 118 | 77.97% | USD 649.81 | USD 76,677.00 | USD -29,684.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 118 | 77.97% | USD 640.71 | USD 75,603.20 | USD -29,693.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 118 | 77.97% | USD 614.81 | USD 72,547.00 | USD -29,719.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 118 | 77.97% | USD 605.71 | USD 71,473.20 | USD -29,728.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 118 | 77.97% | USD 544.81 | USD 64,287.00 | USD -29,789.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 118 | 77.97% | USD 535.71 | USD 63,213.20 | USD -29,798.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 118 | 77.97% | USD 684.81 | USD 80,807.00 | USD -29,649.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 118 | 77.97% | USD 675.71 | USD 79,733.20 | USD -29,658.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 118 | 77.97% | USD 649.81 | USD 76,677.00 | USD -29,684.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 118 | 77.97% | USD 640.71 | USD 75,603.20 | USD -29,693.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 118 | 77.97% | USD 614.81 | USD 72,547.00 | USD -29,719.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 118 | 77.97% | USD 605.71 | USD 71,473.20 | USD -29,728.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 118 | 77.97% | USD 544.81 | USD 64,287.00 | USD -29,789.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 118 | 77.97% | USD 535.71 | USD 63,213.20 | USD -29,798.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 117 | 77.78% | USD 575.36 | USD 67,317.00 | USD -50,059.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 117 | 77.78% | USD 566.26 | USD 66,252.30 | USD -50,068.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 117 | 77.78% | USD 540.36 | USD 63,222.00 | USD -50,094.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 117 | 77.78% | USD 531.26 | USD 62,157.30 | USD -50,103.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 117 | 77.78% | USD 505.36 | USD 59,127.00 | USD -50,129.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 117 | 77.78% | USD 496.26 | USD 58,062.30 | USD -50,138.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 117 | 76.92% | USD 435.36 | USD 50,937.00 | USD -50,199.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 117 | 76.92% | USD 426.26 | USD 49,872.30 | USD -50,208.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 117 | 77.78% | USD 575.36 | USD 67,317.00 | USD -50,059.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 117 | 77.78% | USD 566.26 | USD 66,252.30 | USD -50,068.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 117 | 77.78% | USD 540.36 | USD 63,222.00 | USD -50,094.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 117 | 77.78% | USD 531.26 | USD 62,157.30 | USD -50,103.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 117 | 77.78% | USD 505.36 | USD 59,127.00 | USD -50,129.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 117 | 77.78% | USD 496.26 | USD 58,062.30 | USD -50,138.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 117 | 76.92% | USD 435.36 | USD 50,937.00 | USD -50,199.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 117 | 76.92% | USD 426.26 | USD 49,872.30 | USD -50,208.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 117 | 77.78% | USD 575.36 | USD 67,317.00 | USD -50,059.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 117 | 77.78% | USD 566.26 | USD 66,252.30 | USD -50,068.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 117 | 77.78% | USD 540.36 | USD 63,222.00 | USD -50,094.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 117 | 77.78% | USD 531.26 | USD 62,157.30 | USD -50,103.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 117 | 77.78% | USD 505.36 | USD 59,127.00 | USD -50,129.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 117 | 77.78% | USD 496.26 | USD 58,062.30 | USD -50,138.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 117 | 76.92% | USD 435.36 | USD 50,937.00 | USD -50,199.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 117 | 76.92% | USD 426.26 | USD 49,872.30 | USD -50,208.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 119/119 (0) | 31.09% (23.48–39.89%) | USD -43.76 | USD -5,207.40 | USD -1,151.60 |
| HOLD_5_SESSIONS | 1 : 6 | 119/119 (0) | 67.23% (58.37–75.01%) | USD 157.26 | USD 18,714.10 | USD -14,623.10 |
| HOLD_5_SESSIONS | 6 : 1 | 119/119 (0) | 26.89% (19.74–35.49%) | USD -463.58 | USD -55,165.90 | USD -4,493.10 |
| HOLD_5_SESSIONS | 5 : 5 | 119/119 (0) | 31.09% (23.48–39.89%) | USD -218.80 | USD -26,037.00 | USD -5,758.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 119/119 (0) | 31.09% (23.48–39.89%) | USD -43.76 | USD -5,207.40 | USD -1,151.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 119/119 (0) | 67.23% (58.37–75.01%) | USD 157.26 | USD 18,714.10 | USD -14,623.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 119/119 (0) | 26.89% (19.74–35.49%) | USD -463.58 | USD -55,165.90 | USD -4,493.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 119/119 (0) | 31.09% (23.48–39.89%) | USD -218.80 | USD -26,037.00 | USD -5,758.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 119/119 (0) | 31.09% (23.48–39.89%) | USD -43.76 | USD -5,207.40 | USD -1,151.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 119/119 (0) | 67.23% (58.37–75.01%) | USD 157.26 | USD 18,714.10 | USD -14,623.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 119/119 (0) | 26.89% (19.74–35.49%) | USD -463.58 | USD -55,165.90 | USD -4,493.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 119/119 (0) | 31.09% (23.48–39.89%) | USD -218.80 | USD -26,037.00 | USD -5,758.00 |
| HOLD_10_SESSIONS | 1 : 1 | 119/119 (0) | 35.29% (27.29–44.22%) | USD -39.69 | USD -4,723.40 | USD -1,194.60 |
| HOLD_10_SESSIONS | 1 : 6 | 119/119 (0) | 76.47% (68.10–83.19%) | USD 379.02 | USD 45,103.10 | USD -14,701.10 |
| HOLD_10_SESSIONS | 6 : 1 | 119/119 (0) | 21.01% (14.65–29.18%) | USD -656.86 | USD -78,166.90 | USD -6,041.10 |
| HOLD_10_SESSIONS | 5 : 5 | 119/119 (0) | 35.29% (27.29–44.22%) | USD -198.46 | USD -23,617.00 | USD -5,973.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 119/119 (0) | 35.29% (27.29–44.22%) | USD -39.69 | USD -4,723.40 | USD -1,194.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 119/119 (0) | 76.47% (68.10–83.19%) | USD 379.02 | USD 45,103.10 | USD -14,701.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 119/119 (0) | 21.01% (14.65–29.18%) | USD -656.86 | USD -78,166.90 | USD -6,041.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 119/119 (0) | 35.29% (27.29–44.22%) | USD -198.46 | USD -23,617.00 | USD -5,973.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 119/119 (0) | 35.29% (27.29–44.22%) | USD -39.69 | USD -4,723.40 | USD -1,194.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 119/119 (0) | 76.47% (68.10–83.19%) | USD 379.02 | USD 45,103.10 | USD -14,701.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 119/119 (0) | 21.01% (14.65–29.18%) | USD -656.86 | USD -78,166.90 | USD -6,041.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 119/119 (0) | 35.29% (27.29–44.22%) | USD -198.46 | USD -23,617.00 | USD -5,973.00 |
| HOLD_15_SESSIONS | 1 : 1 | 118/119 (1) | 43.22% (34.64–52.23%) | USD -48.18 | USD -5,684.80 | USD -2,731.60 |
| HOLD_15_SESSIONS | 1 : 6 | 118/119 (1) | 77.97% (69.67–84.50%) | USD 605.71 | USD 71,473.20 | USD -29,728.10 |
| HOLD_15_SESSIONS | 6 : 1 | 118/119 (1) | 21.19% (14.78–29.41%) | USD -942.94 | USD -111,266.80 | USD -5,094.10 |
| HOLD_15_SESSIONS | 5 : 5 | 118/119 (1) | 43.22% (34.64–52.23%) | USD -240.88 | USD -28,424.00 | USD -13,658.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 118/119 (1) | 43.22% (34.64–52.23%) | USD -48.18 | USD -5,684.80 | USD -2,731.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 118/119 (1) | 77.97% (69.67–84.50%) | USD 605.71 | USD 71,473.20 | USD -29,728.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 118/119 (1) | 21.19% (14.78–29.41%) | USD -942.94 | USD -111,266.80 | USD -5,094.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 118/119 (1) | 43.22% (34.64–52.23%) | USD -240.88 | USD -28,424.00 | USD -13,658.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 118/119 (1) | 43.22% (34.64–52.23%) | USD -48.18 | USD -5,684.80 | USD -2,731.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 118/119 (1) | 77.97% (69.67–84.50%) | USD 605.71 | USD 71,473.20 | USD -29,728.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 118/119 (1) | 21.19% (14.78–29.41%) | USD -942.94 | USD -111,266.80 | USD -5,094.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 118/119 (1) | 43.22% (34.64–52.23%) | USD -240.88 | USD -28,424.00 | USD -13,658.00 |
| HOLD_20_SESSIONS | 1 : 1 | 117/119 (2) | 41.88% (33.34–50.94%) | USD -59.89 | USD -7,007.20 | USD -4,296.60 |
| HOLD_20_SESSIONS | 1 : 6 | 117/119 (2) | 77.78% (69.43–84.36%) | USD 496.26 | USD 58,062.30 | USD -50,138.10 |
| HOLD_20_SESSIONS | 6 : 1 | 117/119 (2) | 23.08% (16.37–31.49%) | USD -915.49 | USD -107,112.70 | USD -5,258.10 |
| HOLD_20_SESSIONS | 5 : 5 | 117/119 (2) | 41.88% (33.34–50.94%) | USD -299.45 | USD -35,036.00 | USD -21,483.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 117/119 (2) | 41.88% (33.34–50.94%) | USD -59.89 | USD -7,007.20 | USD -4,296.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 117/119 (2) | 77.78% (69.43–84.36%) | USD 496.26 | USD 58,062.30 | USD -50,138.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 117/119 (2) | 23.08% (16.37–31.49%) | USD -915.49 | USD -107,112.70 | USD -5,258.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 117/119 (2) | 41.88% (33.34–50.94%) | USD -299.45 | USD -35,036.00 | USD -21,483.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 117/119 (2) | 41.88% (33.34–50.94%) | USD -59.89 | USD -7,007.20 | USD -4,296.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 117/119 (2) | 77.78% (69.43–84.36%) | USD 496.26 | USD 58,062.30 | USD -50,138.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 117/119 (2) | 23.08% (16.37–31.49%) | USD -915.49 | USD -107,112.70 | USD -5,258.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 117/119 (2) | 41.88% (33.34–50.94%) | USD -299.45 | USD -35,036.00 | USD -21,483.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/119 | 0.00% | USD -209,415.64 | USD -328,523.55 |
| -75% | 0/119 | 0.00% | USD -153,843.65 | USD -241,439.80 |
| -50% | 0/119 | 0.00% | USD -98,271.66 | USD -154,356.05 |
| -40% | 0/119 | 0.00% | USD -76,042.86 | USD -119,522.55 |
| -30% | 0/119 | 0.00% | USD -53,814.07 | USD -85,707.55 |
| -25% | 0/119 | 0.00% | USD -42,699.67 | USD -69,208.05 |
| -20% | 0/119 | 0.00% | USD -31,585.27 | USD -53,246.55 |
| -15% | 1/119 | 0.84% | USD -20,470.87 | USD -37,718.05 |
| -10% | 8/119 | 6.72% | USD -9,351.39 | USD -22,189.55 |
| -5% | 74/119 | 62.18% | USD 564.63 | USD -6,661.05 |
| 0% | 119/119 | 100.00% | USD 2,771.74 | USD 885.45 |
| 5% | 119/119 | 100.00% | USD 2,771.74 | USD 885.45 |
| 10% | 119/119 | 100.00% | USD 2,771.74 | USD 885.45 |
| 20% | 119/119 | 100.00% | USD 2,771.74 | USD 885.45 |

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