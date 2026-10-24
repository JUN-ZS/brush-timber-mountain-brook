# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 449.28 / USD 2,675.51; mean absolute mismatch USD 2,226.23; mean match score 16.67%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 136/60/0 | 69.39% (62.61–75.42%) | USD 199.01 | USD 468.90 | USD 39,005.40 | USD -4,912.10 | 0 |
| HOLD_10_SESSIONS | 195/196 | 148/47/0 | 75.90% (69.43–81.36%) | USD 324.61 | USD 843.90 | USD 63,298.50 | USD -11,108.10 | 1 |
| HOLD_20_SESSIONS | 193/196 | 160/33/0 | 82.90% (76.96–87.56%) | USD 622.46 | USD 1,400.90 | USD 120,135.70 | USD -29,813.10 | 3 |
| EXIT_AT_DTE_LE_7 | 178/196 | 150/28/0 | 84.27% (78.20–88.89%) | USD 463.68 | USD 1,705.90 | USD 82,534.20 | USD -44,688.10 | 18 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -74.45 | USD 352.56 |
| HOLD_10_SESSIONS | USD -103.55 | USD 507.26 |
| HOLD_20_SESSIONS | USD -171.82 | USD 873.39 |
| EXIT_AT_DTE_LE_7 | USD -169.94 | USD 712.72 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 70.41% | USD 278.11 | USD 54,509.00 | USD -4,833.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 70.41% | USD 269.01 | USD 52,725.40 | USD -4,842.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 70.41% | USD 243.11 | USD 47,649.00 | USD -4,868.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 70.41% | USD 234.01 | USD 45,865.40 | USD -4,877.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 69.90% | USD 208.11 | USD 40,789.00 | USD -4,903.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 69.39% | USD 199.01 | USD 39,005.40 | USD -4,912.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 67.86% | USD 138.11 | USD 27,069.00 | USD -4,973.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 67.35% | USD 129.01 | USD 25,285.40 | USD -4,982.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 76.41% | USD 403.71 | USD 78,723.00 | USD -11,029.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 76.41% | USD 394.61 | USD 76,948.50 | USD -11,038.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 75.90% | USD 368.71 | USD 71,898.00 | USD -11,064.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 75.90% | USD 359.61 | USD 70,123.50 | USD -11,073.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 75.90% | USD 333.71 | USD 65,073.00 | USD -11,099.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 75.90% | USD 324.61 | USD 63,298.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 74.87% | USD 263.71 | USD 51,423.00 | USD -11,169.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 74.87% | USD 254.61 | USD 49,648.50 | USD -11,178.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 193 | 83.42% | USD 701.56 | USD 135,402.00 | USD -29,734.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 193 | 83.42% | USD 692.46 | USD 133,645.70 | USD -29,743.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 193 | 82.90% | USD 666.56 | USD 128,647.00 | USD -29,769.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 193 | 82.90% | USD 657.46 | USD 126,890.70 | USD -29,778.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 193 | 82.90% | USD 631.56 | USD 121,892.00 | USD -29,804.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 193 | 82.90% | USD 622.46 | USD 120,135.70 | USD -29,813.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 193 | 82.90% | USD 561.56 | USD 108,382.00 | USD -29,874.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 193 | 82.90% | USD 552.46 | USD 106,625.70 | USD -29,883.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 178 | 84.83% | USD 542.78 | USD 96,614.00 | USD -44,609.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 178 | 84.83% | USD 533.68 | USD 94,994.20 | USD -44,618.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 178 | 84.27% | USD 507.78 | USD 90,384.00 | USD -44,644.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 178 | 84.27% | USD 498.68 | USD 88,764.20 | USD -44,653.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 178 | 84.27% | USD 472.78 | USD 84,154.00 | USD -44,679.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 178 | 84.27% | USD 463.68 | USD 82,534.20 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 178 | 83.71% | USD 402.78 | USD 71,694.00 | USD -44,749.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 178 | 83.71% | USD 393.68 | USD 70,074.20 | USD -44,758.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 29.08% (23.17–35.79%) | USD -38.29 | USD -7,505.60 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 69.39% (62.61–75.42%) | USD 199.01 | USD 39,005.40 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 22.96% (17.62–29.33%) | USD -467.06 | USD -91,544.60 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 196/196 (0) | 50.00% (43.07–56.93%) | USD -105.72 | USD -20,720.20 | USD -2,903.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/196 (1) | 39.49% (32.89–46.49%) | USD -41.61 | USD -8,114.00 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/196 (1) | 75.90% (69.43–81.36%) | USD 324.61 | USD 63,298.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/196 (1) | 21.03% (15.89–27.28%) | USD -615.88 | USD -120,096.50 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/196 (1) | 62.56% (55.59–69.05%) | USD -93.20 | USD -18,173.50 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 193/196 (3) | 43.52% (36.72–50.58%) | USD -48.86 | USD -9,429.80 | USD -2,926.60 |
| HOLD_20_SESSIONS | 1 : 6 | 193/196 (3) | 82.90% (76.96–87.56%) | USD 622.46 | USD 120,135.70 | USD -29,813.10 |
| HOLD_20_SESSIONS | 6 : 1 | 193/196 (3) | 15.54% (11.11–21.32%) | USD -964.48 | USD -186,144.30 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 193/196 (3) | 72.54% (65.85–78.35%) | USD -61.17 | USD -11,806.10 | USD -17,083.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 178/196 (18) | 43.82% (36.74–51.16%) | USD -73.76 | USD -13,128.80 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 178/196 (18) | 84.27% (78.20–88.89%) | USD 463.68 | USD 82,534.20 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 178/196 (18) | 17.42% (12.55–23.66%) | USD -979.98 | USD -174,435.80 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 178/196 (18) | 71.91% (64.90–78.00%) | USD -187.54 | USD -33,382.60 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -205,191.03 | USD -333,646.55 |
| -75% | 0/196 | 0.00% | USD -151,284.21 | USD -246,651.05 |
| -50% | 0/196 | 0.00% | USD -97,377.39 | USD -159,655.55 |
| -40% | 0/196 | 0.00% | USD -75,814.66 | USD -124,857.35 |
| -30% | 0/196 | 0.00% | USD -54,251.93 | USD -90,195.25 |
| -25% | 0/196 | 0.00% | USD -43,470.57 | USD -73,230.05 |
| -20% | 0/196 | 0.00% | USD -32,689.20 | USD -56,324.75 |
| -15% | 1/196 | 0.51% | USD -21,921.61 | USD -39,423.05 |
| -10% | 4/196 | 2.04% | USD -11,179.04 | USD -23,000.55 |
| -5% | 79/196 | 40.31% | USD -880.85 | USD -8,108.00 |
| 0% | 196/196 | 100.00% | USD 2,187.03 | USD 573.45 |
| 5% | 196/196 | 100.00% | USD 2,186.68 | USD 573.45 |
| 10% | 196/196 | 100.00% | USD 2,186.68 | USD 573.45 |
| 20% | 196/196 | 100.00% | USD 2,186.68 | USD 573.45 |

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