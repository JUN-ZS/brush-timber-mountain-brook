# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 98 checks; 98 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 436.95 / USD 2,618.57; mean absolute mismatch USD 2,181.62; mean match score 16.58%.
- Actual selected contract ratios: {'1:6': 98}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 98; entered cohorts: 98; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/98 | 74/24/0 | 75.51% (66.14–82.95%) | USD 278.88 | USD 557.90 | USD 27,330.20 | USD -4,912.10 | 0 |
| HOLD_10_SESSIONS | 98/98 | 79/19/0 | 80.61% (71.69–87.22%) | USD 438.94 | USD 912.90 | USD 43,016.20 | USD -11,108.10 | 0 |
| HOLD_20_SESSIONS | 97/98 | 78/19/0 | 80.41% (71.42–87.09%) | USD 623.20 | USD 1,409.90 | USD 60,450.30 | USD -16,732.10 | 1 |
| EXIT_AT_DTE_LE_7 | 92/98 | 78/14/0 | 84.78% (76.06–90.71%) | USD 473.18 | USD 1,784.90 | USD 43,532.80 | USD -33,176.10 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -104.08 | USD 462.06 |
| HOLD_10_SESSIONS | USD -139.08 | USD 657.12 |
| HOLD_20_SESSIONS | USD -166.96 | USD 869.26 |
| EXIT_AT_DTE_LE_7 | USD -202.87 | USD 755.15 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 76.53% | USD 357.98 | USD 35,082.00 | USD -4,833.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 76.53% | USD 348.88 | USD 34,190.20 | USD -4,842.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 76.53% | USD 322.98 | USD 31,652.00 | USD -4,868.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 76.53% | USD 313.88 | USD 30,760.20 | USD -4,877.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 75.51% | USD 287.98 | USD 28,222.00 | USD -4,903.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 75.51% | USD 278.88 | USD 27,330.20 | USD -4,912.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 72.45% | USD 217.98 | USD 21,362.00 | USD -4,973.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 72.45% | USD 208.88 | USD 20,470.20 | USD -4,982.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 98 | 81.63% | USD 518.04 | USD 50,768.00 | USD -11,029.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 98 | 81.63% | USD 508.94 | USD 49,876.20 | USD -11,038.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 98 | 80.61% | USD 483.04 | USD 47,338.00 | USD -11,064.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 98 | 80.61% | USD 473.94 | USD 46,446.20 | USD -11,073.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 98 | 80.61% | USD 448.04 | USD 43,908.00 | USD -11,099.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 98 | 80.61% | USD 438.94 | USD 43,016.20 | USD -11,108.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 98 | 78.57% | USD 378.04 | USD 37,048.00 | USD -11,169.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 98 | 78.57% | USD 368.94 | USD 36,156.20 | USD -11,178.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 97 | 81.44% | USD 702.30 | USD 68,123.00 | USD -16,653.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 97 | 81.44% | USD 693.20 | USD 67,240.30 | USD -16,662.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 97 | 80.41% | USD 667.30 | USD 64,728.00 | USD -16,688.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 97 | 80.41% | USD 658.20 | USD 63,845.30 | USD -16,697.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 97 | 80.41% | USD 632.30 | USD 61,333.00 | USD -16,723.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 97 | 80.41% | USD 623.20 | USD 60,450.30 | USD -16,732.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 97 | 80.41% | USD 562.30 | USD 54,543.00 | USD -16,793.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 97 | 80.41% | USD 553.20 | USD 53,660.30 | USD -16,802.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 92 | 85.87% | USD 552.28 | USD 50,810.00 | USD -33,097.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 92 | 85.87% | USD 543.18 | USD 49,972.80 | USD -33,106.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 92 | 84.78% | USD 517.28 | USD 47,590.00 | USD -33,132.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 92 | 84.78% | USD 508.18 | USD 46,752.80 | USD -33,141.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 92 | 84.78% | USD 482.28 | USD 44,370.00 | USD -33,167.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 92 | 84.78% | USD 473.18 | USD 43,532.80 | USD -33,176.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 92 | 84.78% | USD 412.28 | USD 37,930.00 | USD -33,237.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 92 | 84.78% | USD 403.18 | USD 37,092.80 | USD -33,246.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/98 (0) | 27.55% (19.68–37.12%) | USD -49.67 | USD -4,867.80 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/98 (0) | 75.51% (66.14–82.95%) | USD 278.88 | USD 27,330.20 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -626.58 | USD -61,404.80 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 98/98 (0) | 50.00% (40.29–59.71%) | USD -132.98 | USD -13,031.60 | USD -2,903.70 |
| HOLD_10_SESSIONS | 1 : 1 | 98/98 (0) | 40.82% (31.61–50.71%) | USD -52.16 | USD -5,111.80 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 98/98 (0) | 80.61% (71.69–87.22%) | USD 438.94 | USD 43,016.20 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -804.07 | USD -78,798.80 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 98/98 (0) | 64.29% (54.43–73.07%) | USD -110.42 | USD -10,821.60 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 97/98 (1) | 43.30% (33.88–53.23%) | USD -44.68 | USD -4,334.20 | USD -1,890.60 |
| HOLD_20_SESSIONS | 1 : 6 | 97/98 (1) | 80.41% (71.42–87.09%) | USD 623.20 | USD 60,450.30 | USD -16,732.10 |
| HOLD_20_SESSIONS | 6 : 1 | 97/98 (1) | 15.46% (9.60–23.96%) | USD -935.98 | USD -90,789.70 | USD -4,180.10 |
| HOLD_20_SESSIONS | 4 : 5 | 97/98 (1) | 70.10% (60.37–78.31%) | USD -45.15 | USD -4,379.90 | USD -10,530.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 92/98 (6) | 43.48% (33.81–53.67%) | USD -99.61 | USD -9,164.20 | USD -3,304.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 92/98 (6) | 84.78% (76.06–90.71%) | USD 473.18 | USD 43,532.80 | USD -33,176.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 92/98 (6) | 14.13% (8.45–22.69%) | USD -1,170.46 | USD -107,682.20 | USD -4,912.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 92/98 (6) | 71.74% (61.81–79.92%) | USD -283.88 | USD -26,117.40 | USD -19,192.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/98 | 0.00% | USD -204,283.38 | USD -328,030.55 |
| -75% | 0/98 | 0.00% | USD -150,559.57 | USD -242,621.55 |
| -50% | 0/98 | 0.00% | USD -96,835.76 | USD -157,756.55 |
| -40% | 0/98 | 0.00% | USD -75,346.24 | USD -123,945.95 |
| -30% | 0/98 | 0.00% | USD -53,856.71 | USD -90,135.35 |
| -25% | 0/98 | 0.00% | USD -43,111.95 | USD -73,230.05 |
| -20% | 0/98 | 0.00% | USD -32,367.19 | USD -56,324.75 |
| -15% | 1/98 | 1.02% | USD -21,649.98 | USD -39,423.05 |
| -10% | 2/98 | 2.04% | USD -10,974.36 | USD -23,000.55 |
| -5% | 42/98 | 42.86% | USD -768.28 | USD -6,578.05 |
| 0% | 98/98 | 100.00% | USD 2,142.07 | USD 573.45 |
| 5% | 98/98 | 100.00% | USD 2,142.07 | USD 573.45 |
| 10% | 98/98 | 100.00% | USD 2,142.07 | USD 573.45 |
| 20% | 98/98 | 100.00% | USD 2,142.07 | USD 573.45 |

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