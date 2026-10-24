# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 450.08 / USD 1,333.19; mean absolute mismatch USD 883.12; mean match score 33.45%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 269/122/0 | 68.80% (64.04–73.19%) | USD 47.92 | USD 174.80 | USD 18,734.80 | USD -7,101.20 | 1 |
| HOLD_10_SESSIONS | 389/392 | 296/93/0 | 76.09% (71.61–80.06%) | USD 93.96 | USD 325.80 | USD 36,550.20 | USD -13,211.20 | 3 |
| HOLD_20_SESSIONS | 384/392 | 320/64/0 | 83.33% (79.28–86.73%) | USD 198.95 | USD 536.80 | USD 76,396.20 | USD -23,302.20 | 8 |
| EXIT_AT_DTE_LE_7 | 347/392 | 287/60/0 | 82.71% (78.38–86.32%) | USD 154.56 | USD 637.80 | USD 53,630.60 | USD -20,630.20 | 45 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -75.23 | USD 168.35 |
| HOLD_10_SESSIONS | USD -105.54 | USD 244.70 |
| HOLD_20_SESSIONS | USD -173.08 | USD 417.23 |
| EXIT_AT_DTE_LE_7 | USD -177.92 | USD 377.67 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 71.36% | USD 93.12 | USD 36,408.00 | USD -7,056.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 71.10% | USD 87.92 | USD 34,374.80 | USD -7,061.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 70.84% | USD 73.12 | USD 28,588.00 | USD -7,076.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 69.82% | USD 67.92 | USD 26,554.80 | USD -7,081.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 69.31% | USD 53.12 | USD 20,768.00 | USD -7,096.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 68.80% | USD 47.92 | USD 18,734.80 | USD -7,101.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 65.73% | USD 13.12 | USD 5,128.00 | USD -7,136.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 65.22% | USD 7.92 | USD 3,094.80 | USD -7,141.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 389 | 77.12% | USD 139.16 | USD 54,133.00 | USD -13,166.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 389 | 77.12% | USD 133.96 | USD 52,110.20 | USD -13,171.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 389 | 76.86% | USD 119.16 | USD 46,353.00 | USD -13,186.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 389 | 76.86% | USD 113.96 | USD 44,330.20 | USD -13,191.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 389 | 76.09% | USD 99.16 | USD 38,573.00 | USD -13,206.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 389 | 76.09% | USD 93.96 | USD 36,550.20 | USD -13,211.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 389 | 73.78% | USD 59.16 | USD 23,013.00 | USD -13,246.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 389 | 73.52% | USD 53.96 | USD 20,990.20 | USD -13,251.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 384 | 83.59% | USD 244.15 | USD 93,753.00 | USD -23,257.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 384 | 83.59% | USD 238.95 | USD 91,756.20 | USD -23,262.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 384 | 83.59% | USD 224.15 | USD 86,073.00 | USD -23,277.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 384 | 83.59% | USD 218.95 | USD 84,076.20 | USD -23,282.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 384 | 83.33% | USD 204.15 | USD 78,393.00 | USD -23,297.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 384 | 83.33% | USD 198.95 | USD 76,396.20 | USD -23,302.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 384 | 82.55% | USD 164.15 | USD 63,033.00 | USD -23,337.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 384 | 82.55% | USD 158.95 | USD 61,036.20 | USD -23,342.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 347 | 83.57% | USD 199.76 | USD 69,315.00 | USD -20,585.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 347 | 83.57% | USD 194.56 | USD 67,510.60 | USD -20,590.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 347 | 83.29% | USD 179.76 | USD 62,375.00 | USD -20,605.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 347 | 83.00% | USD 174.56 | USD 60,570.60 | USD -20,610.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 347 | 82.71% | USD 159.76 | USD 55,435.00 | USD -20,625.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 347 | 82.71% | USD 154.56 | USD 53,630.60 | USD -20,630.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 347 | 82.42% | USD 119.76 | USD 41,555.00 | USD -20,665.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 347 | 82.42% | USD 114.56 | USD 39,750.60 | USD -20,670.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 32.23% (27.79–37.01%) | USD -41.72 | USD -16,310.60 | USD -1,278.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 69.57% (64.83–73.92%) | USD 182.36 | USD 71,302.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 24.04% (20.07–28.52%) | USD -474.37 | USD -185,477.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 391/392 (1) | 49.10% (44.18–54.04%) | USD -122.05 | USD -47,719.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 389/392 (3) | 37.28% (32.62–42.18%) | USD -46.58 | USD -18,118.40 | USD -2,810.60 |
| HOLD_10_SESSIONS | 1 : 6 | 389/392 (3) | 75.84% (71.34–79.82%) | USD 304.76 | USD 118,553.10 | USD -28,812.10 |
| HOLD_10_SESSIONS | 6 : 1 | 389/392 (3) | 21.08% (17.32–25.41%) | USD -630.80 | USD -245,381.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 389/392 (3) | 58.35% (53.40–63.15%) | USD -116.04 | USD -45,139.30 | USD -16,442.70 |
| HOLD_20_SESSIONS | 1 : 1 | 384/392 (8) | 41.41% (36.59–46.39%) | USD -56.60 | USD -21,735.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 384/392 (8) | 83.33% (79.28–86.73%) | USD 582.27 | USD 223,593.60 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 384/392 (8) | 15.62% (12.34–19.60%) | USD -978.49 | USD -375,741.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 384/392 (8) | 71.61% (66.91–75.89%) | USD -98.63 | USD -37,875.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 347/392 (45) | 39.19% (34.20–44.42%) | USD -74.63 | USD -25,895.20 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 347/392 (45) | 84.15% (79.94–87.62%) | USD 498.33 | USD 172,919.30 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 347/392 (45) | 16.14% (12.64–20.38%) | USD -1,020.71 | USD -354,185.70 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 347/392 (45) | 72.05% (67.10–76.51%) | USD -183.91 | USD -63,817.90 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -87,154.91 | USD -138,122.60 |
| -75% | 0/392 | 0.00% | USD -64,312.95 | USD -102,416.10 |
| -50% | 0/392 | 0.00% | USD -41,470.98 | USD -66,709.60 |
| -40% | 0/392 | 0.00% | USD -32,334.20 | USD -52,427.00 |
| -30% | 0/392 | 0.00% | USD -23,197.41 | USD -38,144.40 |
| -25% | 0/392 | 0.00% | USD -18,629.02 | USD -31,003.10 |
| -20% | 0/392 | 0.00% | USD -14,060.63 | USD -24,166.40 |
| -15% | 3/392 | 0.77% | USD -9,495.28 | USD -17,390.45 |
| -10% | 10/392 | 2.55% | USD -4,949.27 | USD -10,614.50 |
| -5% | 154/392 | 39.29% | USD -546.22 | USD -3,940.10 |
| 0% | 392/392 | 100.00% | USD 860.69 | USD 215.40 |
| 5% | 392/392 | 100.00% | USD 860.52 | USD 215.40 |
| 10% | 392/392 | 100.00% | USD 860.52 | USD 215.40 |
| 20% | 392/392 | 100.00% | USD 860.52 | USD 215.40 |

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