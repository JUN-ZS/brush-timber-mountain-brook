# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,789.86 / USD 2,222.07; mean absolute mismatch USD 465.73; mean match score 78.75%.
- Actual selected contract ratios: {'4:5': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 97/99/0 | 49.49% (42.57–56.43%) | USD -119.36 | USD -2.70 | USD -23,395.20 | USD -4,692.70 | 0 |
| HOLD_10_SESSIONS | 195/196 | 122/73/0 | 62.56% (55.59–69.05%) | USD -92.14 | USD 95.30 | USD -17,966.50 | USD -7,525.70 | 1 |
| HOLD_20_SESSIONS | 193/196 | 141/52/0 | 73.06% (66.39–78.82%) | USD -80.90 | USD 205.30 | USD -15,614.10 | USD -21,980.70 | 3 |
| EXIT_AT_DTE_LE_7 | 176/196 | 128/48/0 | 72.73% (65.71–78.77%) | USD -200.14 | USD 228.30 | USD -35,225.20 | USD -26,385.70 | 20 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -296.90 | USD 279.23 |
| HOLD_10_SESSIONS | USD -401.74 | USD 411.31 |
| HOLD_20_SESSIONS | USD -706.30 | USD 727.10 |
| EXIT_AT_DTE_LE_7 | USD -694.75 | USD 596.31 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 59.69% | USD -17.66 | USD -3,462.00 | USD -4,591.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 59.18% | USD -29.36 | USD -5,755.20 | USD -4,602.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 55.10% | USD -62.66 | USD -12,282.00 | USD -4,636.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 55.10% | USD -74.36 | USD -14,575.20 | USD -4,647.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 51.02% | USD -107.66 | USD -21,102.00 | USD -4,681.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 49.49% | USD -119.36 | USD -23,395.20 | USD -4,692.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 35.71% | USD -197.66 | USD -38,742.00 | USD -4,771.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 34.18% | USD -209.36 | USD -41,035.20 | USD -4,782.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 67.18% | USD 9.56 | USD 1,865.00 | USD -7,424.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 66.67% | USD -2.14 | USD -416.50 | USD -7,435.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 65.64% | USD -35.44 | USD -6,910.00 | USD -7,469.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 64.62% | USD -47.14 | USD -9,191.50 | USD -7,480.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 62.56% | USD -80.44 | USD -15,685.00 | USD -7,514.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 62.56% | USD -92.14 | USD -17,966.50 | USD -7,525.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 50.77% | USD -170.44 | USD -33,235.00 | USD -7,604.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 50.26% | USD -182.14 | USD -35,516.50 | USD -7,615.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 193 | 77.20% | USD 20.80 | USD 4,014.00 | USD -21,879.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 193 | 76.68% | USD 9.10 | USD 1,755.90 | USD -21,890.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 193 | 75.13% | USD -24.20 | USD -4,671.00 | USD -21,924.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 193 | 74.61% | USD -35.90 | USD -6,929.10 | USD -21,935.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 193 | 73.06% | USD -69.20 | USD -13,356.00 | USD -21,969.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 193 | 73.06% | USD -80.90 | USD -15,614.10 | USD -21,980.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 193 | 64.77% | USD -159.20 | USD -30,726.00 | USD -22,059.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 193 | 64.25% | USD -170.90 | USD -32,984.10 | USD -22,070.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 176 | 79.55% | USD -98.44 | USD -17,326.00 | USD -26,284.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 176 | 78.98% | USD -110.14 | USD -19,385.20 | USD -26,295.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 176 | 77.84% | USD -143.44 | USD -25,246.00 | USD -26,329.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 176 | 76.70% | USD -155.14 | USD -27,305.20 | USD -26,340.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 176 | 73.30% | USD -188.44 | USD -33,166.00 | USD -26,374.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 176 | 72.73% | USD -200.14 | USD -35,225.20 | USD -26,385.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 176 | 68.75% | USD -278.44 | USD -49,006.00 | USD -26,464.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 176 | 66.48% | USD -290.14 | USD -51,065.20 | USD -26,475.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 29.08% (23.17–35.79%) | USD -40.98 | USD -8,031.60 | USD -983.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 68.88% (62.09–74.94%) | USD 181.76 | USD 35,624.40 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 22.96% (17.62–29.33%) | USD -468.60 | USD -91,845.60 | USD -3,952.10 |
| HOLD_5_SESSIONS | 4 : 5 | 196/196 (0) | 49.49% (42.57–56.43%) | USD -119.36 | USD -23,395.20 | USD -4,692.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/196 (1) | 39.49% (32.89–46.49%) | USD -40.77 | USD -7,951.00 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/196 (1) | 75.90% (69.43–81.36%) | USD 314.03 | USD 61,236.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/196 (1) | 21.03% (15.89–27.28%) | USD -599.45 | USD -116,893.50 | USD -5,042.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/196 (1) | 62.56% (55.59–69.05%) | USD -92.14 | USD -17,966.50 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 193/196 (3) | 44.04% (37.22–51.09%) | USD -53.76 | USD -10,374.80 | USD -3,488.60 |
| HOLD_20_SESSIONS | 1 : 6 | 193/196 (3) | 83.42% (77.53–88.00%) | USD 616.84 | USD 119,050.70 | USD -43,620.10 |
| HOLD_20_SESSIONS | 6 : 1 | 193/196 (3) | 15.03% (10.67–20.75%) | USD -993.13 | USD -191,674.30 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 193/196 (3) | 73.06% (66.39–78.82%) | USD -80.90 | USD -15,614.10 | USD -21,980.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 176/196 (20) | 43.75% (36.63–51.13%) | USD -77.03 | USD -13,556.60 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 176/196 (20) | 84.09% (77.97–88.76%) | USD 462.78 | USD 81,449.40 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 176/196 (20) | 17.61% (12.70–23.92%) | USD -1,001.96 | USD -176,345.60 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 176/196 (20) | 72.73% (65.71–78.77%) | USD -200.14 | USD -35,225.20 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -73,162.15 | USD -94,413.85 |
| -75% | 0/196 | 0.00% | USD -54,347.14 | USD -70,612.10 |
| -50% | 0/196 | 0.00% | USD -35,532.14 | USD -46,810.35 |
| -40% | 0/196 | 0.00% | USD -28,006.13 | USD -37,334.65 |
| -30% | 0/196 | 0.00% | USD -20,480.13 | USD -28,023.95 |
| -25% | 0/196 | 0.00% | USD -16,717.13 | USD -23,368.60 |
| -20% | 0/196 | 0.00% | USD -12,954.13 | USD -18,713.25 |
| -15% | 1/196 | 0.51% | USD -9,197.57 | USD -14,122.35 |
| -10% | 5/196 | 2.55% | USD -5,449.77 | USD -9,611.85 |
| -5% | 60/196 | 30.61% | USD -1,413.90 | USD -4,892.90 |
| 0% | 175/196 | 89.29% | USD 382.75 | USD -1,204.85 |
| 5% | 175/196 | 89.29% | USD 381.36 | USD -1,204.85 |
| 10% | 175/196 | 89.29% | USD 381.36 | USD -1,204.85 |
| 20% | 175/196 | 89.29% | USD 381.36 | USD -1,204.85 |

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