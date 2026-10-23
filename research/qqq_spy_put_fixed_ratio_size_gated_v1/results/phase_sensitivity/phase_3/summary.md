# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 442.69 / USD 1,313.06; mean absolute mismatch USD 870.37; mean match score 33.36%.
- Actual selected contract ratios: {'1:3': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 390/391 | 261/129/0 | 66.92% (62.11–71.41%) | USD 27.32 | USD 171.80 | USD 10,656.00 | USD -4,770.20 | 1 |
| HOLD_10_SESSIONS | 389/391 | 293/96/0 | 75.32% (70.80–79.34%) | USD 81.60 | USD 310.80 | USD 31,744.20 | USD -10,501.20 | 2 |
| HOLD_20_SESSIONS | 386/391 | 311/75/0 | 80.57% (76.33–84.21%) | USD 180.38 | USD 533.80 | USD 69,627.80 | USD -21,325.20 | 5 |
| EXIT_AT_DTE_LE_7 | 345/391 | 289/56/0 | 83.77% (79.51–87.28%) | USD 171.68 | USD 647.80 | USD 59,229.00 | USD -19,363.20 | 46 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -57.96 | USD 130.48 |
| HOLD_10_SESSIONS | USD -91.65 | USD 218.45 |
| HOLD_20_SESSIONS | USD -156.42 | USD 382.00 |
| EXIT_AT_DTE_LE_7 | USD -186.63 | USD 403.51 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 390 | 69.74% | USD 72.52 | USD 28,284.00 | USD -4,725.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 390 | 68.97% | USD 67.32 | USD 26,256.00 | USD -4,730.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 390 | 67.95% | USD 52.52 | USD 20,484.00 | USD -4,745.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 390 | 67.69% | USD 47.32 | USD 18,456.00 | USD -4,750.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 390 | 67.18% | USD 32.52 | USD 12,684.00 | USD -4,765.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 390 | 66.92% | USD 27.32 | USD 10,656.00 | USD -4,770.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 390 | 64.62% | USD -7.48 | USD -2,916.00 | USD -4,805.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 390 | 64.62% | USD -12.68 | USD -4,944.00 | USD -4,810.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 389 | 76.61% | USD 126.80 | USD 49,327.00 | USD -10,456.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 389 | 76.35% | USD 121.60 | USD 47,304.20 | USD -10,461.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 389 | 75.84% | USD 106.80 | USD 41,547.00 | USD -10,476.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 389 | 75.84% | USD 101.60 | USD 39,524.20 | USD -10,481.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 389 | 75.32% | USD 86.80 | USD 33,767.00 | USD -10,496.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 389 | 75.32% | USD 81.60 | USD 31,744.20 | USD -10,501.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 389 | 72.49% | USD 46.80 | USD 18,207.00 | USD -10,536.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 389 | 72.49% | USD 41.60 | USD 16,184.20 | USD -10,541.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 386 | 81.09% | USD 225.58 | USD 87,075.00 | USD -21,280.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 386 | 80.83% | USD 220.38 | USD 85,067.80 | USD -21,285.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 386 | 80.83% | USD 205.58 | USD 79,355.00 | USD -21,300.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 386 | 80.83% | USD 200.38 | USD 77,347.80 | USD -21,305.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 386 | 80.57% | USD 185.58 | USD 71,635.00 | USD -21,320.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 386 | 80.57% | USD 180.38 | USD 69,627.80 | USD -21,325.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 386 | 80.05% | USD 145.58 | USD 56,195.00 | USD -21,360.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 386 | 80.05% | USD 140.38 | USD 54,187.80 | USD -21,365.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 345 | 84.35% | USD 216.88 | USD 74,823.00 | USD -19,318.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 345 | 84.35% | USD 211.68 | USD 73,029.00 | USD -19,323.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 345 | 84.35% | USD 196.88 | USD 67,923.00 | USD -19,338.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 345 | 84.06% | USD 191.68 | USD 66,129.00 | USD -19,343.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 345 | 83.77% | USD 176.88 | USD 61,023.00 | USD -19,358.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 345 | 83.77% | USD 171.68 | USD 59,229.00 | USD -19,363.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 345 | 83.77% | USD 136.88 | USD 47,223.00 | USD -19,398.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 345 | 83.77% | USD 131.68 | USD 45,429.00 | USD -19,403.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 390/391 (1) | 33.59% (29.08–38.42%) | USD -37.07 | USD -14,456.00 | USD -813.60 |
| HOLD_5_SESSIONS | 1 : 6 | 390/391 (1) | 68.46% (63.69–72.87%) | USD 123.91 | USD 48,324.00 | USD -10,735.10 |
| HOLD_5_SESSIONS | 6 : 1 | 390/391 (1) | 25.64% (21.56–30.20%) | USD -383.37 | USD -149,516.00 | USD -4,497.10 |
| HOLD_5_SESSIONS | 4 : 5 | 390/391 (1) | 46.41% (41.52–51.37%) | USD -116.07 | USD -45,268.00 | USD -5,162.70 |
| HOLD_10_SESSIONS | 1 : 1 | 389/391 (2) | 33.42% (28.91–38.25%) | USD -41.43 | USD -16,116.40 | USD -2,062.60 |
| HOLD_10_SESSIONS | 1 : 6 | 389/391 (2) | 75.84% (71.34–79.82%) | USD 266.16 | USD 103,535.10 | USD -23,159.10 |
| HOLD_10_SESSIONS | 6 : 1 | 389/391 (2) | 22.36% (18.51–26.76%) | USD -556.17 | USD -216,349.90 | USD -6,005.10 |
| HOLD_10_SESSIONS | 4 : 5 | 389/391 (2) | 57.07% (52.11–61.90%) | USD -104.20 | USD -40,535.30 | USD -12,469.70 |
| HOLD_20_SESSIONS | 1 : 1 | 386/391 (5) | 36.79% (32.13–41.71%) | USD -51.69 | USD -19,950.60 | USD -4,028.60 |
| HOLD_20_SESSIONS | 1 : 6 | 386/391 (5) | 80.05% (75.78–83.73%) | USD 528.49 | USD 203,995.40 | USD -47,270.10 |
| HOLD_20_SESSIONS | 6 : 1 | 386/391 (5) | 15.29% (12.04–19.22%) | USD -890.28 | USD -343,649.60 | USD -5,355.10 |
| HOLD_20_SESSIONS | 4 : 5 | 386/391 (5) | 69.43% (64.66–73.82%) | USD -90.71 | USD -35,013.20 | USD -24,762.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 345/391 (46) | 33.62% (28.84–38.76%) | USD -74.73 | USD -25,782.00 | USD -3,886.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 345/391 (46) | 83.77% (79.51–87.28%) | USD 541.29 | USD 186,745.50 | USD -42,814.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 345/391 (46) | 14.49% (11.17–18.60%) | USD -1,064.40 | USD -367,219.50 | USD -6,897.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 345/391 (46) | 71.88% (66.92–76.37%) | USD -175.72 | USD -60,622.50 | USD -23,284.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -87,187.44 | USD -137,346.60 |
| -75% | 0/391 | 0.00% | USD -64,329.21 | USD -101,744.85 |
| -50% | 0/391 | 0.00% | USD -41,470.98 | USD -66,143.10 |
| -40% | 0/391 | 0.00% | USD -32,327.69 | USD -51,902.40 |
| -30% | 0/391 | 0.00% | USD -23,184.39 | USD -37,661.70 |
| -25% | 0/391 | 0.00% | USD -18,612.75 | USD -30,739.60 |
| -20% | 2/391 | 0.51% | USD -14,041.10 | USD -24,183.20 |
| -15% | 3/391 | 0.77% | USD -9,485.07 | USD -17,626.80 |
| -10% | 8/391 | 2.05% | USD -4,938.89 | USD -11,070.40 |
| -5% | 155/391 | 39.64% | USD -565.33 | USD -4,514.00 |
| 0% | 391/391 | 100.00% | USD 847.07 | USD 221.40 |
| 5% | 391/391 | 100.00% | USD 847.77 | USD 221.40 |
| 10% | 391/391 | 100.00% | USD 847.77 | USD 221.40 |
| 20% | 391/391 | 100.00% | USD 847.77 | USD 221.40 |

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