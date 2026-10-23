# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 452.90 / USD 1,336.53; mean absolute mismatch USD 883.63; mean match score 33.72%.
- Actual selected contract ratios: {'1:3': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 390/391 | 267/123/0 | 68.46% (63.69–72.87%) | USD 39.98 | USD 166.80 | USD 15,594.00 | USD -7,101.20 | 1 |
| HOLD_10_SESSIONS | 388/391 | 293/95/0 | 75.52% (71.00–79.53%) | USD 84.45 | USD 314.80 | USD 32,767.40 | USD -13,211.20 | 3 |
| HOLD_20_SESSIONS | 383/391 | 318/65/0 | 83.03% (78.95–86.46%) | USD 195.70 | USD 540.80 | USD 74,953.40 | USD -23,302.20 | 8 |
| EXIT_AT_DTE_LE_7 | 346/391 | 285/61/0 | 82.37% (78.01–86.02%) | USD 153.52 | USD 637.80 | USD 53,118.80 | USD -20,630.20 | 45 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -73.71 | USD 158.89 |
| HOLD_10_SESSIONS | USD -105.04 | USD 234.70 |
| HOLD_20_SESSIONS | USD -173.30 | USD 414.20 |
| EXIT_AT_DTE_LE_7 | USD -178.69 | USD 377.41 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 390 | 71.54% | USD 85.18 | USD 33,222.00 | USD -7,056.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 390 | 71.03% | USD 79.98 | USD 31,194.00 | USD -7,061.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 390 | 70.77% | USD 65.18 | USD 25,422.00 | USD -7,076.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 390 | 70.00% | USD 59.98 | USD 23,394.00 | USD -7,081.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 390 | 69.23% | USD 45.18 | USD 17,622.00 | USD -7,096.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 390 | 68.46% | USD 39.98 | USD 15,594.00 | USD -7,101.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 390 | 65.38% | USD 5.18 | USD 2,022.00 | USD -7,136.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 390 | 64.62% | USD -0.02 | USD -6.00 | USD -7,141.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 388 | 76.29% | USD 129.65 | USD 50,305.00 | USD -13,166.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 388 | 76.29% | USD 124.45 | USD 48,287.40 | USD -13,171.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 388 | 76.29% | USD 109.65 | USD 42,545.00 | USD -13,186.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 388 | 76.29% | USD 104.45 | USD 40,527.40 | USD -13,191.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 388 | 75.52% | USD 89.65 | USD 34,785.00 | USD -13,206.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 388 | 75.52% | USD 84.45 | USD 32,767.40 | USD -13,211.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 388 | 73.45% | USD 49.65 | USD 19,265.00 | USD -13,246.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 388 | 73.20% | USD 44.45 | USD 17,247.40 | USD -13,251.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 383 | 83.55% | USD 240.90 | USD 92,265.00 | USD -23,257.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 383 | 83.55% | USD 235.70 | USD 90,273.40 | USD -23,262.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 383 | 83.29% | USD 220.90 | USD 84,605.00 | USD -23,277.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 383 | 83.29% | USD 215.70 | USD 82,613.40 | USD -23,282.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 383 | 83.03% | USD 200.90 | USD 76,945.00 | USD -23,297.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 383 | 83.03% | USD 195.70 | USD 74,953.40 | USD -23,302.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 383 | 82.25% | USD 160.90 | USD 61,625.00 | USD -23,337.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 383 | 82.25% | USD 155.70 | USD 59,633.40 | USD -23,342.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 346 | 83.24% | USD 198.72 | USD 68,758.00 | USD -20,585.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 346 | 83.24% | USD 193.52 | USD 66,958.80 | USD -20,590.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 346 | 82.95% | USD 178.72 | USD 61,838.00 | USD -20,605.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 346 | 82.66% | USD 173.52 | USD 60,038.80 | USD -20,610.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 346 | 82.37% | USD 158.72 | USD 54,918.00 | USD -20,625.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 346 | 82.37% | USD 153.52 | USD 53,118.80 | USD -20,630.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 346 | 82.08% | USD 118.72 | USD 41,078.00 | USD -20,665.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 346 | 82.08% | USD 113.52 | USD 39,278.80 | USD -20,670.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 390/391 (1) | 31.54% (27.13–36.31%) | USD -43.34 | USD -16,904.00 | USD -1,278.60 |
| HOLD_5_SESSIONS | 1 : 6 | 390/391 (1) | 69.74% (65.01–74.09%) | USD 164.98 | USD 64,341.00 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 390/391 (1) | 24.10% (20.12–28.59%) | USD -468.38 | USD -182,669.00 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 390/391 (1) | 47.95% (43.03–52.90%) | USD -131.71 | USD -51,367.00 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 388/391 (3) | 36.34% (31.71–41.24%) | USD -49.41 | USD -19,171.80 | USD -2,810.60 |
| HOLD_10_SESSIONS | 1 : 6 | 388/391 (3) | 75.26% (70.73–79.29%) | USD 285.25 | USD 110,676.20 | USD -28,812.10 |
| HOLD_10_SESSIONS | 6 : 1 | 388/391 (3) | 21.13% (17.36–25.47%) | USD -631.13 | USD -244,878.80 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 388/391 (3) | 57.73% (52.76–62.55%) | USD -130.72 | USD -50,717.60 | USD -16,442.70 |
| HOLD_20_SESSIONS | 1 : 1 | 383/391 (8) | 39.95% (35.17–44.93%) | USD -57.83 | USD -22,148.80 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 383/391 (8) | 83.03% (78.95–86.46%) | USD 576.00 | USD 220,606.70 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 383/391 (8) | 16.19% (12.84–20.21%) | USD -980.80 | USD -375,648.30 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 383/391 (8) | 69.97% (65.20–74.35%) | USD -104.55 | USD -40,044.10 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 346/391 (45) | 36.71% (31.80–41.90%) | USD -75.48 | USD -26,117.60 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 346/391 (45) | 84.10% (79.88–87.58%) | USD 497.03 | USD 171,973.40 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 346/391 (45) | 15.61% (12.16–19.81%) | USD -1,025.42 | USD -354,796.60 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 346/391 (45) | 71.68% (66.71–76.17%) | USD -187.43 | USD -64,852.20 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -87,231.16 | USD -138,122.60 |
| -75% | 0/391 | 0.00% | USD -64,370.17 | USD -102,416.10 |
| -50% | 0/391 | 0.00% | USD -41,509.18 | USD -66,709.60 |
| -40% | 0/391 | 0.00% | USD -32,364.78 | USD -52,427.00 |
| -30% | 0/391 | 0.00% | USD -23,220.39 | USD -38,144.40 |
| -25% | 0/391 | 0.00% | USD -18,648.19 | USD -31,003.10 |
| -20% | 0/391 | 0.00% | USD -14,075.99 | USD -24,166.40 |
| -15% | 3/391 | 0.77% | USD -9,506.85 | USD -17,390.45 |
| -10% | 10/391 | 2.56% | USD -4,957.08 | USD -10,614.50 |
| -5% | 152/391 | 38.87% | USD -552.11 | USD -3,940.10 |
| 0% | 391/391 | 100.00% | USD 861.21 | USD 208.40 |
| 5% | 391/391 | 100.00% | USD 861.03 | USD 208.40 |
| 10% | 391/391 | 100.00% | USD 861.03 | USD 208.40 |
| 20% | 391/391 | 100.00% | USD 861.03 | USD 208.40 |

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