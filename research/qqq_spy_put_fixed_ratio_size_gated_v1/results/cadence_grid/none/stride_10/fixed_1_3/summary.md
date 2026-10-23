# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 449.28 / USD 1,337.76; mean absolute mismatch USD 888.48; mean match score 33.35%.
- Actual selected contract ratios: {'1:3': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 132/64/0 | 67.35% (60.50–73.52%) | USD 55.07 | USD 181.80 | USD 10,792.80 | USD -2,268.20 | 0 |
| HOLD_10_SESSIONS | 195/196 | 149/46/0 | 76.41% (69.98–81.82%) | USD 102.68 | USD 322.80 | USD 20,023.00 | USD -5,233.20 | 1 |
| HOLD_20_SESSIONS | 193/196 | 159/34/0 | 82.38% (76.39–87.11%) | USD 216.67 | USD 552.80 | USD 41,817.40 | USD -13,681.20 | 3 |
| EXIT_AT_DTE_LE_7 | 178/196 | 147/31/0 | 82.58% (76.34–87.45%) | USD 130.69 | USD 643.80 | USD 23,262.40 | USD -20,630.20 | 18 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -73.99 | USD 174.26 |
| HOLD_10_SESSIONS | USD -102.50 | USD 250.38 |
| HOLD_20_SESSIONS | USD -171.31 | USD 433.18 |
| EXIT_AT_DTE_LE_7 | USD -166.82 | USD 342.71 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 69.39% | USD 100.27 | USD 19,652.00 | USD -2,223.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 69.39% | USD 95.07 | USD 18,632.80 | USD -2,228.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 69.39% | USD 80.27 | USD 15,732.00 | USD -2,243.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 67.86% | USD 75.07 | USD 14,712.80 | USD -2,248.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 67.35% | USD 60.27 | USD 11,812.00 | USD -2,263.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 67.35% | USD 55.07 | USD 10,792.80 | USD -2,268.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 63.78% | USD 20.27 | USD 3,972.00 | USD -2,303.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 63.27% | USD 15.07 | USD 2,952.80 | USD -2,308.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 76.92% | USD 147.88 | USD 28,837.00 | USD -5,188.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 76.92% | USD 142.68 | USD 27,823.00 | USD -5,193.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 76.92% | USD 127.88 | USD 24,937.00 | USD -5,208.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 76.92% | USD 122.68 | USD 23,923.00 | USD -5,213.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 76.41% | USD 107.88 | USD 21,037.00 | USD -5,228.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 76.41% | USD 102.68 | USD 20,023.00 | USD -5,233.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 73.85% | USD 67.88 | USD 13,237.00 | USD -5,268.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 73.33% | USD 62.68 | USD 12,223.00 | USD -5,273.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 193 | 82.38% | USD 261.87 | USD 50,541.00 | USD -13,636.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 193 | 82.38% | USD 256.67 | USD 49,537.40 | USD -13,641.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 193 | 82.38% | USD 241.87 | USD 46,681.00 | USD -13,656.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 193 | 82.38% | USD 236.67 | USD 45,677.40 | USD -13,661.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 193 | 82.38% | USD 221.87 | USD 42,821.00 | USD -13,676.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 193 | 82.38% | USD 216.67 | USD 41,817.40 | USD -13,681.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 193 | 82.38% | USD 181.87 | USD 35,101.00 | USD -13,716.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 193 | 82.38% | USD 176.67 | USD 34,097.40 | USD -13,721.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 178 | 83.15% | USD 175.89 | USD 31,308.00 | USD -20,585.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 178 | 83.15% | USD 170.69 | USD 30,382.40 | USD -20,590.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 178 | 82.58% | USD 155.89 | USD 27,748.00 | USD -20,605.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 178 | 82.58% | USD 150.69 | USD 26,822.40 | USD -20,610.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 178 | 82.58% | USD 135.89 | USD 24,188.00 | USD -20,625.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 178 | 82.58% | USD 130.69 | USD 23,262.40 | USD -20,630.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 178 | 82.58% | USD 95.89 | USD 17,068.00 | USD -20,665.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 178 | 82.58% | USD 90.69 | USD 16,142.40 | USD -20,670.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 29.08% (23.17–35.79%) | USD -38.51 | USD -7,547.60 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 68.88% (62.09–74.94%) | USD 195.43 | USD 38,303.40 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 22.96% (17.62–29.33%) | USD -464.98 | USD -91,136.60 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 196/196 (0) | 49.49% (42.57–56.43%) | USD -107.25 | USD -21,020.20 | USD -2,903.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/196 (1) | 39.49% (32.89–46.49%) | USD -41.64 | USD -8,120.00 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/196 (1) | 75.90% (69.43–81.36%) | USD 319.17 | USD 62,237.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/196 (1) | 21.03% (15.89–27.28%) | USD -610.65 | USD -119,077.50 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/196 (1) | 62.56% (55.59–69.05%) | USD -94.40 | USD -18,408.50 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 193/196 (3) | 43.52% (36.72–50.58%) | USD -49.52 | USD -9,556.80 | USD -2,926.60 |
| HOLD_20_SESSIONS | 1 : 6 | 193/196 (3) | 82.90% (76.96–87.56%) | USD 615.95 | USD 118,878.70 | USD -29,813.10 |
| HOLD_20_SESSIONS | 6 : 1 | 193/196 (3) | 15.54% (11.11–21.32%) | USD -962.57 | USD -185,776.30 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 193/196 (3) | 72.54% (65.85–78.35%) | USD -64.97 | USD -12,540.10 | USD -17,083.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 178/196 (18) | 43.82% (36.74–51.16%) | USD -75.18 | USD -13,382.80 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 178/196 (18) | 84.27% (78.20–88.89%) | USD 439.50 | USD 78,230.20 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 178/196 (18) | 17.42% (12.55–23.66%) | USD -965.79 | USD -171,909.80 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 178/196 (18) | 72.47% (65.49–78.51%) | USD -197.80 | USD -35,208.60 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -87,148.57 | USD -137,444.60 |
| -75% | 0/196 | 0.00% | USD -64,317.30 | USD -101,740.85 |
| -50% | 0/196 | 0.00% | USD -41,486.03 | USD -66,037.10 |
| -40% | 0/196 | 0.00% | USD -32,353.53 | USD -51,755.60 |
| -30% | 0/196 | 0.00% | USD -23,221.02 | USD -37,474.10 |
| -25% | 0/196 | 0.00% | USD -18,654.77 | USD -30,474.35 |
| -20% | 0/196 | 0.00% | USD -14,088.51 | USD -23,529.40 |
| -15% | 1/196 | 0.51% | USD -9,528.35 | USD -16,743.95 |
| -10% | 4/196 | 2.04% | USD -4,978.79 | USD -9,958.50 |
| -5% | 74/196 | 37.76% | USD -547.46 | USD -3,699.35 |
| 0% | 196/196 | 100.00% | USD 866.23 | USD 215.40 |
| 5% | 196/196 | 100.00% | USD 865.88 | USD 215.40 |
| 10% | 196/196 | 100.00% | USD 865.88 | USD 215.40 |
| 20% | 196/196 | 100.00% | USD 865.88 | USD 215.40 |

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