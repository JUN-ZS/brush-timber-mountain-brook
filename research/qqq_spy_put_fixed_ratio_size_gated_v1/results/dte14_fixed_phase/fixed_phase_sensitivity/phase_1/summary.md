# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 227.23 / USD 653.27; mean absolute mismatch USD 426.03; mean match score 35.04%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 384/392 | 294/90/0 | 76.56% (72.08–80.52%) | USD -13.22 | USD 176.30 | USD -5,076.80 | USD -8,918.20 | 8 |
| HOLD_10_SESSIONS | 12/392 | 8/4/0 | 66.67% (39.06–86.19%) | USD -41.28 | USD 217.80 | USD -495.40 | USD -1,875.20 | 380 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| EXIT_AT_DTE_LE_7 | 391/392 | 293/98/0 | 74.94% (70.41–78.97%) | USD -9.89 | USD 148.80 | USD -3,866.20 | USD -8,918.20 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -45.22 | USD 77.20 |
| HOLD_10_SESSIONS | USD 24.67 | USD -20.75 |
| HOLD_20_SESSIONS | — | — |
| EXIT_AT_DTE_LE_7 | USD -48.88 | USD 84.19 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 384 | 79.69% | USD 31.98 | USD 12,280.00 | USD -8,873.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 384 | 79.69% | USD 26.78 | USD 10,283.20 | USD -8,878.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 384 | 79.17% | USD 11.98 | USD 4,600.00 | USD -8,893.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 384 | 78.91% | USD 6.78 | USD 2,603.20 | USD -8,898.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 384 | 77.08% | USD -8.02 | USD -3,080.00 | USD -8,913.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 384 | 76.56% | USD -13.22 | USD -5,076.80 | USD -8,918.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 384 | 74.22% | USD -48.02 | USD -18,440.00 | USD -8,953.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 384 | 73.96% | USD -53.22 | USD -20,436.80 | USD -8,958.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 12 | 66.67% | USD 3.92 | USD 47.00 | USD -1,830.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 12 | 66.67% | USD -1.28 | USD -15.40 | USD -1,835.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 12 | 66.67% | USD -16.08 | USD -193.00 | USD -1,850.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 12 | 66.67% | USD -21.28 | USD -255.40 | USD -1,855.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 12 | 66.67% | USD -36.08 | USD -433.00 | USD -1,870.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 12 | 66.67% | USD -41.28 | USD -495.40 | USD -1,875.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 12 | 66.67% | USD -76.08 | USD -913.00 | USD -1,910.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 12 | 66.67% | USD -81.28 | USD -975.40 | USD -1,915.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 76.98% | USD 35.31 | USD 13,807.00 | USD -8,873.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 76.98% | USD 30.11 | USD 11,773.80 | USD -8,878.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 76.21% | USD 15.31 | USD 5,987.00 | USD -8,893.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 75.70% | USD 10.11 | USD 3,953.80 | USD -8,898.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 75.19% | USD -4.69 | USD -1,833.00 | USD -8,913.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 74.94% | USD -9.89 | USD -3,866.20 | USD -8,918.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 71.87% | USD -44.69 | USD -17,473.00 | USD -8,953.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 71.36% | USD -49.89 | USD -19,506.20 | USD -8,958.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 384/392 (8) | 26.56% (22.39–31.20%) | USD -42.08 | USD -16,160.40 | USD -1,611.60 |
| HOLD_5_SESSIONS | 1 : 6 | 384/392 (8) | 78.65% (74.27–82.45%) | USD 30.07 | USD 11,548.60 | USD -19,878.10 |
| HOLD_5_SESSIONS | 6 : 1 | 384/392 (8) | 19.53% (15.88–23.79%) | USD -324.67 | USD -124,671.40 | USD -5,900.10 |
| HOLD_5_SESSIONS | 4 : 5 | 384/392 (8) | 45.83% (40.92–50.83%) | USD -153.91 | USD -59,099.80 | USD -10,099.70 |
| HOLD_10_SESSIONS | 1 : 1 | 12/392 (380) | 16.67% (4.70–44.80%) | USD -4.85 | USD -58.20 | USD -262.60 |
| HOLD_10_SESSIONS | 1 : 6 | 12/392 (380) | 66.67% (39.06–86.19%) | USD -95.93 | USD -1,151.20 | USD -4,294.10 |
| HOLD_10_SESSIONS | 6 : 1 | 12/392 (380) | 33.33% (13.81–60.94%) | USD 61.98 | USD 743.80 | USD -1,715.10 |
| HOLD_10_SESSIONS | 4 : 5 | 12/392 (380) | 33.33% (13.81–60.94%) | USD -37.62 | USD -451.40 | USD -1,856.70 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 4 : 5 | 0/392 (392) | — | — | — | — |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 25.06% (21.02–29.59%) | USD -43.42 | USD -16,975.60 | USD -1,611.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 75.70% (71.22–79.69%) | USD 40.40 | USD 15,797.90 | USD -19,878.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 20.46% (16.76–24.74%) | USD -344.31 | USD -134,627.10 | USD -7,193.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 391/392 (1) | 45.01% (40.15–49.97%) | USD -156.90 | USD -61,347.70 | USD -10,099.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -89,076.46 | USD -140,742.60 |
| -75% | 0/392 | 0.00% | USD -66,201.11 | USD -104,951.10 |
| -50% | 0/392 | 0.00% | USD -43,325.77 | USD -69,159.60 |
| -40% | 0/392 | 0.00% | USD -34,175.63 | USD -54,843.00 |
| -30% | 0/392 | 0.00% | USD -25,025.49 | USD -40,572.60 |
| -25% | 0/392 | 0.00% | USD -20,450.43 | USD -33,440.60 |
| -20% | 0/392 | 0.00% | USD -15,875.36 | USD -26,308.60 |
| -15% | 1/392 | 0.26% | USD -11,306.23 | USD -19,176.60 |
| -10% | 2/392 | 0.51% | USD -6,735.75 | USD -12,044.60 |
| -5% | 37/392 | 9.44% | USD -2,200.31 | USD -5,561.45 |
| 0% | 392/392 | 100.00% | USD 392.46 | USD 33.40 |
| 5% | 392/392 | 100.00% | USD 403.43 | USD 33.40 |
| 10% | 392/392 | 100.00% | USD 403.43 | USD 33.40 |
| 20% | 392/392 | 100.00% | USD 403.43 | USD 33.40 |

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