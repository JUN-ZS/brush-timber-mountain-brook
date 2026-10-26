# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 547.01 / USD 3,334.67; mean absolute mismatch USD 2,787.66; mean match score 16.20%.
- Actual selected contract ratios: {'1:6': 113}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 113; entered cohorts: 113; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 113/113 | 74/39/0 | 65.49% (56.34–73.61%) | USD 118.71 | USD 447.90 | USD 13,414.70 | USD -7,642.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 113/113 | 74/39/0 | 65.49% (56.34–73.61%) | USD 118.71 | USD 447.90 | USD 13,414.70 | USD -7,642.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 113/113 | 74/39/0 | 65.49% (56.34–73.61%) | USD 118.71 | USD 447.90 | USD 13,414.70 | USD -7,642.10 | 0 |
| HOLD_10_SESSIONS | 112/113 | 86/26/0 | 76.79% (68.16–83.64%) | USD 460.18 | USD 958.90 | USD 51,539.80 | USD -13,685.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 112/113 | 86/26/0 | 76.79% (68.16–83.64%) | USD 460.18 | USD 958.90 | USD 51,539.80 | USD -13,685.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 112/113 | 86/26/0 | 76.79% (68.16–83.64%) | USD 460.18 | USD 958.90 | USD 51,539.80 | USD -13,685.10 | 1 |
| HOLD_15_SESSIONS | 112/113 | 95/17/0 | 84.82% (77.03–90.30%) | USD 712.92 | USD 1,196.40 | USD 79,846.80 | USD -14,243.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 112/113 | 95/17/0 | 84.82% (77.03–90.30%) | USD 712.92 | USD 1,196.40 | USD 79,846.80 | USD -14,243.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 112/113 | 95/17/0 | 84.82% (77.03–90.30%) | USD 712.92 | USD 1,196.40 | USD 79,846.80 | USD -14,243.10 | 1 |
| HOLD_20_SESSIONS | 111/113 | 89/22/0 | 80.18% (71.81–86.53%) | USD 544.90 | USD 1,391.90 | USD 60,483.90 | USD -28,539.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 111/113 | 89/22/0 | 80.18% (71.81–86.53%) | USD 544.90 | USD 1,391.90 | USD 60,483.90 | USD -28,539.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 111/113 | 89/22/0 | 80.18% (71.81–86.53%) | USD 544.90 | USD 1,391.90 | USD 60,483.90 | USD -28,539.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -65.07 | USD 262.88 |
| HOLD_5_OR_DTE_LE_7 | USD -65.07 | USD 262.88 |
| HOLD_5_OR_DTE_LE_14 | USD -65.07 | USD 262.88 |
| HOLD_10_SESSIONS | USD -121.63 | USD 660.91 |
| HOLD_10_OR_DTE_LE_7 | USD -121.63 | USD 660.91 |
| HOLD_10_OR_DTE_LE_14 | USD -121.63 | USD 660.91 |
| HOLD_15_SESSIONS | USD -171.95 | USD 963.96 |
| HOLD_15_OR_DTE_LE_7 | USD -171.95 | USD 963.96 |
| HOLD_15_OR_DTE_LE_14 | USD -171.95 | USD 963.96 |
| HOLD_20_SESSIONS | USD -175.89 | USD 799.89 |
| HOLD_20_OR_DTE_LE_7 | USD -175.89 | USD 799.89 |
| HOLD_20_OR_DTE_LE_14 | USD -175.89 | USD 799.89 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 113 | 67.26% | USD 197.81 | USD 22,353.00 | USD -7,563.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 113 | 67.26% | USD 188.71 | USD 21,324.70 | USD -7,572.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 113 | 65.49% | USD 162.81 | USD 18,398.00 | USD -7,598.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 113 | 65.49% | USD 153.71 | USD 17,369.70 | USD -7,607.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 113 | 65.49% | USD 127.81 | USD 14,443.00 | USD -7,633.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 113 | 65.49% | USD 118.71 | USD 13,414.70 | USD -7,642.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 113 | 63.72% | USD 57.81 | USD 6,533.00 | USD -7,703.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 113 | 62.83% | USD 48.71 | USD 5,504.70 | USD -7,712.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 67.26% | USD 197.81 | USD 22,353.00 | USD -7,563.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 67.26% | USD 188.71 | USD 21,324.70 | USD -7,572.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 65.49% | USD 162.81 | USD 18,398.00 | USD -7,598.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 65.49% | USD 153.71 | USD 17,369.70 | USD -7,607.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 65.49% | USD 127.81 | USD 14,443.00 | USD -7,633.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 65.49% | USD 118.71 | USD 13,414.70 | USD -7,642.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 63.72% | USD 57.81 | USD 6,533.00 | USD -7,703.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 62.83% | USD 48.71 | USD 5,504.70 | USD -7,712.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 67.26% | USD 197.81 | USD 22,353.00 | USD -7,563.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 67.26% | USD 188.71 | USD 21,324.70 | USD -7,572.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 65.49% | USD 162.81 | USD 18,398.00 | USD -7,598.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 65.49% | USD 153.71 | USD 17,369.70 | USD -7,607.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 65.49% | USD 127.81 | USD 14,443.00 | USD -7,633.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 65.49% | USD 118.71 | USD 13,414.70 | USD -7,642.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 63.72% | USD 57.81 | USD 6,533.00 | USD -7,703.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 62.83% | USD 48.71 | USD 5,504.70 | USD -7,712.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 112 | 77.68% | USD 539.28 | USD 60,399.00 | USD -13,606.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 112 | 76.79% | USD 530.18 | USD 59,379.80 | USD -13,615.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 112 | 76.79% | USD 504.28 | USD 56,479.00 | USD -13,641.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 112 | 76.79% | USD 495.18 | USD 55,459.80 | USD -13,650.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 112 | 76.79% | USD 469.28 | USD 52,559.00 | USD -13,676.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 112 | 76.79% | USD 460.18 | USD 51,539.80 | USD -13,685.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 112 | 75.00% | USD 399.28 | USD 44,719.00 | USD -13,746.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 112 | 75.00% | USD 390.18 | USD 43,699.80 | USD -13,755.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 77.68% | USD 539.28 | USD 60,399.00 | USD -13,606.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 76.79% | USD 530.18 | USD 59,379.80 | USD -13,615.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 76.79% | USD 504.28 | USD 56,479.00 | USD -13,641.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 76.79% | USD 495.18 | USD 55,459.80 | USD -13,650.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 76.79% | USD 469.28 | USD 52,559.00 | USD -13,676.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 76.79% | USD 460.18 | USD 51,539.80 | USD -13,685.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 75.00% | USD 399.28 | USD 44,719.00 | USD -13,746.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 75.00% | USD 390.18 | USD 43,699.80 | USD -13,755.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 77.68% | USD 539.28 | USD 60,399.00 | USD -13,606.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 76.79% | USD 530.18 | USD 59,379.80 | USD -13,615.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 76.79% | USD 504.28 | USD 56,479.00 | USD -13,641.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 76.79% | USD 495.18 | USD 55,459.80 | USD -13,650.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 76.79% | USD 469.28 | USD 52,559.00 | USD -13,676.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 76.79% | USD 460.18 | USD 51,539.80 | USD -13,685.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 75.00% | USD 399.28 | USD 44,719.00 | USD -13,746.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 75.00% | USD 390.18 | USD 43,699.80 | USD -13,755.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 112 | 84.82% | USD 792.02 | USD 88,706.00 | USD -14,164.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 112 | 84.82% | USD 782.92 | USD 87,686.80 | USD -14,173.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 112 | 84.82% | USD 757.02 | USD 84,786.00 | USD -14,199.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 112 | 84.82% | USD 747.92 | USD 83,766.80 | USD -14,208.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 112 | 84.82% | USD 722.02 | USD 80,866.00 | USD -14,234.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 112 | 84.82% | USD 712.92 | USD 79,846.80 | USD -14,243.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 112 | 83.93% | USD 652.02 | USD 73,026.00 | USD -14,304.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 112 | 83.93% | USD 642.92 | USD 72,006.80 | USD -14,313.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 112 | 84.82% | USD 792.02 | USD 88,706.00 | USD -14,164.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 112 | 84.82% | USD 782.92 | USD 87,686.80 | USD -14,173.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 112 | 84.82% | USD 757.02 | USD 84,786.00 | USD -14,199.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 112 | 84.82% | USD 747.92 | USD 83,766.80 | USD -14,208.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 112 | 84.82% | USD 722.02 | USD 80,866.00 | USD -14,234.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 112 | 84.82% | USD 712.92 | USD 79,846.80 | USD -14,243.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 112 | 83.93% | USD 652.02 | USD 73,026.00 | USD -14,304.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 112 | 83.93% | USD 642.92 | USD 72,006.80 | USD -14,313.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 112 | 84.82% | USD 792.02 | USD 88,706.00 | USD -14,164.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 112 | 84.82% | USD 782.92 | USD 87,686.80 | USD -14,173.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 112 | 84.82% | USD 757.02 | USD 84,786.00 | USD -14,199.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 112 | 84.82% | USD 747.92 | USD 83,766.80 | USD -14,208.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 112 | 84.82% | USD 722.02 | USD 80,866.00 | USD -14,234.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 112 | 84.82% | USD 712.92 | USD 79,846.80 | USD -14,243.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 112 | 83.93% | USD 652.02 | USD 73,026.00 | USD -14,304.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 112 | 83.93% | USD 642.92 | USD 72,006.80 | USD -14,313.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 111 | 80.18% | USD 624.00 | USD 69,264.00 | USD -28,460.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 111 | 80.18% | USD 614.90 | USD 68,253.90 | USD -28,469.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 111 | 80.18% | USD 589.00 | USD 65,379.00 | USD -28,495.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 111 | 80.18% | USD 579.90 | USD 64,368.90 | USD -28,504.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 111 | 80.18% | USD 554.00 | USD 61,494.00 | USD -28,530.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 111 | 80.18% | USD 544.90 | USD 60,483.90 | USD -28,539.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 111 | 80.18% | USD 484.00 | USD 53,724.00 | USD -28,600.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 111 | 80.18% | USD 474.90 | USD 52,713.90 | USD -28,609.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 111 | 80.18% | USD 624.00 | USD 69,264.00 | USD -28,460.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 111 | 80.18% | USD 614.90 | USD 68,253.90 | USD -28,469.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 111 | 80.18% | USD 589.00 | USD 65,379.00 | USD -28,495.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 111 | 80.18% | USD 579.90 | USD 64,368.90 | USD -28,504.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 111 | 80.18% | USD 554.00 | USD 61,494.00 | USD -28,530.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 111 | 80.18% | USD 544.90 | USD 60,483.90 | USD -28,539.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 111 | 80.18% | USD 484.00 | USD 53,724.00 | USD -28,600.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 111 | 80.18% | USD 474.90 | USD 52,713.90 | USD -28,609.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 111 | 80.18% | USD 624.00 | USD 69,264.00 | USD -28,460.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 111 | 80.18% | USD 614.90 | USD 68,253.90 | USD -28,469.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 111 | 80.18% | USD 589.00 | USD 65,379.00 | USD -28,495.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 111 | 80.18% | USD 579.90 | USD 64,368.90 | USD -28,504.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 111 | 80.18% | USD 554.00 | USD 61,494.00 | USD -28,530.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 111 | 80.18% | USD 544.90 | USD 60,483.90 | USD -28,539.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 111 | 80.18% | USD 484.00 | USD 53,724.00 | USD -28,600.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 111 | 80.18% | USD 474.90 | USD 52,713.90 | USD -28,609.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 113/113 (0) | 28.32% (20.83–37.23%) | USD -43.86 | USD -4,955.80 | USD -558.60 |
| HOLD_5_SESSIONS | 1 : 6 | 113/113 (0) | 65.49% (56.34–73.61%) | USD 118.71 | USD 13,414.70 | USD -7,642.10 |
| HOLD_5_SESSIONS | 6 : 1 | 113/113 (0) | 26.55% (19.28–35.36%) | USD -425.71 | USD -48,105.30 | USD -4,004.10 |
| HOLD_5_SESSIONS | 5 : 5 | 113/113 (0) | 28.32% (20.83–37.23%) | USD -219.28 | USD -24,779.00 | USD -2,793.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 113/113 (0) | 28.32% (20.83–37.23%) | USD -43.86 | USD -4,955.80 | USD -558.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 113/113 (0) | 65.49% (56.34–73.61%) | USD 118.71 | USD 13,414.70 | USD -7,642.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 113/113 (0) | 26.55% (19.28–35.36%) | USD -425.71 | USD -48,105.30 | USD -4,004.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 113/113 (0) | 28.32% (20.83–37.23%) | USD -219.28 | USD -24,779.00 | USD -2,793.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 113/113 (0) | 28.32% (20.83–37.23%) | USD -43.86 | USD -4,955.80 | USD -558.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 113/113 (0) | 65.49% (56.34–73.61%) | USD 118.71 | USD 13,414.70 | USD -7,642.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 113/113 (0) | 26.55% (19.28–35.36%) | USD -425.71 | USD -48,105.30 | USD -4,004.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 113/113 (0) | 28.32% (20.83–37.23%) | USD -219.28 | USD -24,779.00 | USD -2,793.00 |
| HOLD_10_SESSIONS | 1 : 1 | 112/113 (1) | 42.86% (34.08–52.11%) | USD -34.08 | USD -3,817.20 | USD -1,113.60 |
| HOLD_10_SESSIONS | 1 : 6 | 112/113 (1) | 76.79% (68.16–83.64%) | USD 460.18 | USD 51,539.80 | USD -13,685.10 |
| HOLD_10_SESSIONS | 6 : 1 | 112/113 (1) | 21.43% (14.84–29.91%) | USD -698.75 | USD -78,260.20 | USD -5,123.10 |
| HOLD_10_SESSIONS | 5 : 5 | 112/113 (1) | 42.86% (34.08–52.11%) | USD -170.41 | USD -19,086.00 | USD -5,568.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 112/113 (1) | 42.86% (34.08–52.11%) | USD -34.08 | USD -3,817.20 | USD -1,113.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 112/113 (1) | 76.79% (68.16–83.64%) | USD 460.18 | USD 51,539.80 | USD -13,685.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 112/113 (1) | 21.43% (14.84–29.91%) | USD -698.75 | USD -78,260.20 | USD -5,123.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 112/113 (1) | 42.86% (34.08–52.11%) | USD -170.41 | USD -19,086.00 | USD -5,568.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 112/113 (1) | 42.86% (34.08–52.11%) | USD -34.08 | USD -3,817.20 | USD -1,113.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 112/113 (1) | 76.79% (68.16–83.64%) | USD 460.18 | USD 51,539.80 | USD -13,685.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 112/113 (1) | 21.43% (14.84–29.91%) | USD -698.75 | USD -78,260.20 | USD -5,123.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 112/113 (1) | 42.86% (34.08–52.11%) | USD -170.41 | USD -19,086.00 | USD -5,568.00 |
| HOLD_15_SESSIONS | 1 : 1 | 112/113 (1) | 45.54% (36.61–54.75%) | USD -33.89 | USD -3,795.20 | USD -1,121.60 |
| HOLD_15_SESSIONS | 1 : 6 | 112/113 (1) | 84.82% (77.03–90.30%) | USD 712.92 | USD 79,846.80 | USD -14,243.10 |
| HOLD_15_SESSIONS | 6 : 1 | 112/113 (1) | 16.96% (11.14–24.98%) | USD -950.12 | USD -106,413.20 | USD -5,899.10 |
| HOLD_15_SESSIONS | 5 : 5 | 112/113 (1) | 45.54% (36.61–54.75%) | USD -169.43 | USD -18,976.00 | USD -5,608.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 112/113 (1) | 45.54% (36.61–54.75%) | USD -33.89 | USD -3,795.20 | USD -1,121.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 112/113 (1) | 84.82% (77.03–90.30%) | USD 712.92 | USD 79,846.80 | USD -14,243.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 112/113 (1) | 16.96% (11.14–24.98%) | USD -950.12 | USD -106,413.20 | USD -5,899.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 112/113 (1) | 45.54% (36.61–54.75%) | USD -169.43 | USD -18,976.00 | USD -5,608.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 112/113 (1) | 45.54% (36.61–54.75%) | USD -33.89 | USD -3,795.20 | USD -1,121.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 112/113 (1) | 84.82% (77.03–90.30%) | USD 712.92 | USD 79,846.80 | USD -14,243.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 112/113 (1) | 16.96% (11.14–24.98%) | USD -950.12 | USD -106,413.20 | USD -5,899.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 112/113 (1) | 45.54% (36.61–54.75%) | USD -169.43 | USD -18,976.00 | USD -5,608.00 |
| HOLD_20_SESSIONS | 1 : 1 | 111/113 (2) | 46.85% (37.83–56.08%) | USD -65.18 | USD -7,234.60 | USD -2,732.60 |
| HOLD_20_SESSIONS | 1 : 6 | 111/113 (2) | 80.18% (71.81–86.53%) | USD 544.90 | USD 60,483.90 | USD -28,539.10 |
| HOLD_20_SESSIONS | 6 : 1 | 111/113 (2) | 18.92% (12.72–27.20%) | USD -1,001.14 | USD -111,126.10 | USD -6,981.10 |
| HOLD_20_SESSIONS | 5 : 5 | 111/113 (2) | 46.85% (37.83–56.08%) | USD -325.88 | USD -36,173.00 | USD -13,663.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 111/113 (2) | 46.85% (37.83–56.08%) | USD -65.18 | USD -7,234.60 | USD -2,732.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 111/113 (2) | 80.18% (71.81–86.53%) | USD 544.90 | USD 60,483.90 | USD -28,539.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 111/113 (2) | 18.92% (12.72–27.20%) | USD -1,001.14 | USD -111,126.10 | USD -6,981.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 111/113 (2) | 46.85% (37.83–56.08%) | USD -325.88 | USD -36,173.00 | USD -13,663.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 111/113 (2) | 46.85% (37.83–56.08%) | USD -65.18 | USD -7,234.60 | USD -2,732.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 111/113 (2) | 80.18% (71.81–86.53%) | USD 544.90 | USD 60,483.90 | USD -28,539.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 111/113 (2) | 18.92% (12.72–27.20%) | USD -1,001.14 | USD -111,126.10 | USD -6,981.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 111/113 (2) | 46.85% (37.83–56.08%) | USD -325.88 | USD -36,173.00 | USD -13,663.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/113 | 0.00% | USD -206,773.80 | USD -330,579.55 |
| -75% | 0/113 | 0.00% | USD -151,895.11 | USD -243,584.05 |
| -50% | 0/113 | 0.00% | USD -97,016.43 | USD -156,748.05 |
| -40% | 0/113 | 0.00% | USD -75,064.96 | USD -122,426.15 |
| -30% | 0/113 | 0.00% | USD -53,113.48 | USD -88,104.25 |
| -25% | 0/113 | 0.00% | USD -42,137.75 | USD -70,943.30 |
| -20% | 0/113 | 0.00% | USD -31,162.01 | USD -54,207.55 |
| -15% | 0/113 | 0.00% | USD -20,186.27 | USD -37,785.05 |
| -10% | 6/113 | 5.31% | USD -9,220.03 | USD -21,362.55 |
| -5% | 68/113 | 60.18% | USD 716.83 | USD -6,224.00 |
| 0% | 113/113 | 100.00% | USD 2,748.11 | USD 879.45 |
| 5% | 113/113 | 100.00% | USD 2,748.11 | USD 879.45 |
| 10% | 113/113 | 100.00% | USD 2,748.11 | USD 879.45 |
| 20% | 113/113 | 100.00% | USD 2,748.11 | USD 879.45 |

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