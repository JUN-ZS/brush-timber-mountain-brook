# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 896.58 / USD 1,780.22; mean absolute mismatch USD 883.64; mean match score 50.01%.
- Actual selected contract ratios: {'2:4': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 126/70/0 | 64.29% (57.36–70.66%) | USD 7.93 | USD 155.20 | USD 1,555.20 | USD -3,483.80 | 0 |
| HOLD_10_SESSIONS | 195/196 | 145/50/0 | 74.36% (67.80–79.98%) | USD 61.15 | USD 318.20 | USD 11,925.00 | USD -6,635.80 | 1 |
| HOLD_20_SESSIONS | 193/196 | 157/36/0 | 81.35% (75.26–86.21%) | USD 140.57 | USD 538.20 | USD 27,130.60 | USD -23,029.80 | 3 |
| EXIT_AT_DTE_LE_7 | 177/196 | 146/31/0 | 82.49% (76.21–87.38%) | USD 57.80 | USD 600.20 | USD 10,231.40 | USD -25,221.80 | 19 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -149.22 | USD 224.96 |
| HOLD_10_SESSIONS | USD -202.12 | USD 331.08 |
| HOLD_20_SESSIONS | USD -323.71 | USD 532.08 |
| EXIT_AT_DTE_LE_7 | USD -337.47 | USD 463.07 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 68.88% | USD 75.73 | USD 14,844.00 | USD -3,416.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 68.37% | USD 67.93 | USD 13,315.20 | USD -3,423.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 66.84% | USD 45.73 | USD 8,964.00 | USD -3,446.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 66.84% | USD 37.93 | USD 7,435.20 | USD -3,453.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 64.29% | USD 15.73 | USD 3,084.00 | USD -3,476.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 64.29% | USD 7.93 | USD 1,555.20 | USD -3,483.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 59.18% | USD -44.27 | USD -8,676.00 | USD -3,536.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 58.67% | USD -52.07 | USD -10,204.80 | USD -3,543.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 76.92% | USD 128.95 | USD 25,146.00 | USD -6,568.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 76.92% | USD 121.15 | USD 23,625.00 | USD -6,575.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 76.92% | USD 98.95 | USD 19,296.00 | USD -6,598.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 76.92% | USD 91.15 | USD 17,775.00 | USD -6,605.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 74.36% | USD 68.95 | USD 13,446.00 | USD -6,628.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 74.36% | USD 61.15 | USD 11,925.00 | USD -6,635.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 71.28% | USD 8.95 | USD 1,746.00 | USD -6,688.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 71.28% | USD 1.15 | USD 225.00 | USD -6,695.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 193 | 81.87% | USD 208.37 | USD 40,216.00 | USD -22,962.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 193 | 81.87% | USD 200.57 | USD 38,710.60 | USD -22,969.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 193 | 81.87% | USD 178.37 | USD 34,426.00 | USD -22,992.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 193 | 81.87% | USD 170.57 | USD 32,920.60 | USD -22,999.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 193 | 81.87% | USD 148.37 | USD 28,636.00 | USD -23,022.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 193 | 81.35% | USD 140.57 | USD 27,130.60 | USD -23,029.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 193 | 80.83% | USD 88.37 | USD 17,056.00 | USD -23,082.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 193 | 80.83% | USD 80.57 | USD 15,550.60 | USD -23,089.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 177 | 82.49% | USD 125.60 | USD 22,232.00 | USD -25,154.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 177 | 82.49% | USD 117.80 | USD 20,851.40 | USD -25,161.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 177 | 82.49% | USD 95.60 | USD 16,922.00 | USD -25,184.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 177 | 82.49% | USD 87.80 | USD 15,541.40 | USD -25,191.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 177 | 82.49% | USD 65.60 | USD 11,612.00 | USD -25,214.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 177 | 82.49% | USD 57.80 | USD 10,231.40 | USD -25,221.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 177 | 82.49% | USD 5.60 | USD 992.00 | USD -25,274.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 177 | 82.49% | USD -2.20 | USD -388.60 | USD -25,281.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 29.08% (23.17–35.79%) | USD -40.97 | USD -8,030.60 | USD -983.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 68.88% (62.09–74.94%) | USD 183.73 | USD 36,010.40 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 22.96% (17.62–29.33%) | USD -470.53 | USD -92,224.60 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 196/196 (0) | 49.49% (42.57–56.43%) | USD -118.95 | USD -23,314.20 | USD -4,692.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/196 (1) | 39.49% (32.89–46.49%) | USD -40.89 | USD -7,974.00 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/196 (1) | 75.90% (69.43–81.36%) | USD 316.45 | USD 61,708.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/196 (1) | 21.03% (15.89–27.28%) | USD -602.70 | USD -117,526.50 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/196 (1) | 62.56% (55.59–69.05%) | USD -92.10 | USD -17,959.50 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 193/196 (3) | 44.04% (37.22–51.09%) | USD -51.43 | USD -9,926.80 | USD -3,488.60 |
| HOLD_20_SESSIONS | 1 : 6 | 193/196 (3) | 82.90% (76.96–87.56%) | USD 557.17 | USD 107,533.70 | USD -43,620.10 |
| HOLD_20_SESSIONS | 6 : 1 | 193/196 (3) | 15.54% (11.11–21.32%) | USD -917.21 | USD -177,021.30 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 193/196 (3) | 73.06% (66.39–78.82%) | USD -84.02 | USD -16,215.10 | USD -21,980.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 177/196 (19) | 43.50% (36.41–50.87%) | USD -75.57 | USD -13,375.20 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 177/196 (19) | 84.18% (78.09–88.82%) | USD 446.78 | USD 79,079.30 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 177/196 (19) | 17.51% (12.62–23.79%) | USD -975.74 | USD -172,705.70 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 177/196 (19) | 72.32% (65.30–78.38%) | USD -197.80 | USD -35,009.90 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -95,603.64 | USD -144,087.90 |
| -75% | 0/196 | 0.00% | USD -70,657.24 | USD -106,874.90 |
| -50% | 0/196 | 0.00% | USD -45,710.84 | USD -69,661.90 |
| -40% | 0/196 | 0.00% | USD -35,732.28 | USD -54,776.70 |
| -30% | 0/196 | 0.00% | USD -25,753.72 | USD -39,891.50 |
| -25% | 0/196 | 0.00% | USD -20,764.44 | USD -32,660.90 |
| -20% | 0/196 | 0.00% | USD -15,775.16 | USD -25,514.70 |
| -15% | 1/196 | 0.51% | USD -10,792.94 | USD -18,368.50 |
| -10% | 5/196 | 2.55% | USD -5,822.31 | USD -11,222.30 |
| -5% | 71/196 | 36.22% | USD -870.72 | USD -4,459.60 |
| 0% | 196/196 | 100.00% | USD 850.44 | USD 192.10 |
| 5% | 196/196 | 100.00% | USD 849.74 | USD 192.10 |
| 10% | 196/196 | 100.00% | USD 849.74 | USD 192.10 |
| 20% | 196/196 | 100.00% | USD 849.74 | USD 192.10 |

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