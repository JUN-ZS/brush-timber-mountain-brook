# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 66 checks; 66 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 902.15 / USD 1,794.18; mean absolute mismatch USD 892.03; mean match score 49.93%.
- Actual selected contract ratios: {'2:4': 66}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 66; entered cohorts: 66; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 66/66 | 45/21/0 | 68.18% (56.21–78.15%) | USD -17.13 | USD 174.20 | USD -1,130.80 | USD -3,483.80 | 0 |
| HOLD_10_SESSIONS | 65/66 | 48/17/0 | 73.85% (62.05–82.98%) | USD 79.80 | USD 328.20 | USD 5,187.00 | USD -5,637.80 | 1 |
| HOLD_20_SESSIONS | 65/66 | 55/10/0 | 84.62% (73.94–91.42%) | USD 271.98 | USD 534.20 | USD 17,679.00 | USD -5,581.80 | 1 |
| EXIT_AT_DTE_LE_7 | 62/66 | 53/9/0 | 85.48% (74.66–92.17%) | USD 82.39 | USD 624.20 | USD 5,108.40 | USD -20,497.80 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -191.27 | USD 241.94 |
| HOLD_10_SESSIONS | USD -257.57 | USD 405.17 |
| HOLD_20_SESSIONS | USD -356.71 | USD 696.49 |
| EXIT_AT_DTE_LE_7 | USD -276.45 | USD 426.65 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 66 | 71.21% | USD 50.67 | USD 3,344.00 | USD -3,416.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 66 | 69.70% | USD 42.87 | USD 2,829.20 | USD -3,423.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 66 | 69.70% | USD 20.67 | USD 1,364.00 | USD -3,446.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 66 | 69.70% | USD 12.87 | USD 849.20 | USD -3,453.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 66 | 68.18% | USD -9.33 | USD -616.00 | USD -3,476.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 66 | 68.18% | USD -17.13 | USD -1,130.80 | USD -3,483.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 66 | 65.15% | USD -69.33 | USD -4,576.00 | USD -3,536.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 66 | 65.15% | USD -77.13 | USD -5,090.80 | USD -3,543.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 65 | 75.38% | USD 147.60 | USD 9,594.00 | USD -5,570.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 65 | 75.38% | USD 139.80 | USD 9,087.00 | USD -5,577.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 65 | 75.38% | USD 117.60 | USD 7,644.00 | USD -5,600.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 65 | 75.38% | USD 109.80 | USD 7,137.00 | USD -5,607.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 65 | 73.85% | USD 87.60 | USD 5,694.00 | USD -5,630.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 65 | 73.85% | USD 79.80 | USD 5,187.00 | USD -5,637.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 65 | 73.85% | USD 27.60 | USD 1,794.00 | USD -5,690.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 65 | 73.85% | USD 19.80 | USD 1,287.00 | USD -5,697.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 65 | 84.62% | USD 339.78 | USD 22,086.00 | USD -5,514.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 65 | 84.62% | USD 331.98 | USD 21,579.00 | USD -5,521.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 65 | 84.62% | USD 309.78 | USD 20,136.00 | USD -5,544.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 65 | 84.62% | USD 301.98 | USD 19,629.00 | USD -5,551.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 65 | 84.62% | USD 279.78 | USD 18,186.00 | USD -5,574.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 65 | 84.62% | USD 271.98 | USD 17,679.00 | USD -5,581.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 65 | 84.62% | USD 219.78 | USD 14,286.00 | USD -5,634.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 65 | 84.62% | USD 211.98 | USD 13,779.00 | USD -5,641.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 62 | 85.48% | USD 150.19 | USD 9,312.00 | USD -20,430.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 62 | 85.48% | USD 142.39 | USD 8,828.40 | USD -20,437.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 62 | 85.48% | USD 120.19 | USD 7,452.00 | USD -20,460.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 62 | 85.48% | USD 112.39 | USD 6,968.40 | USD -20,467.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 62 | 85.48% | USD 90.19 | USD 5,592.00 | USD -20,490.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 62 | 85.48% | USD 82.39 | USD 5,108.40 | USD -20,497.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 62 | 85.48% | USD 30.19 | USD 1,872.00 | USD -20,550.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 62 | 85.48% | USD 22.39 | USD 1,388.40 | USD -20,557.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 66/66 (0) | 27.27% (18.00–39.04%) | USD -57.75 | USD -3,811.60 | USD -983.60 |
| HOLD_5_SESSIONS | 1 : 6 | 66/66 (0) | 72.73% (60.96–82.00%) | USD 188.17 | USD 12,419.40 | USD -4,775.10 |
| HOLD_5_SESSIONS | 6 : 1 | 66/66 (0) | 19.70% (11.89–30.84%) | USD -592.43 | USD -39,100.60 | USD -3,001.10 |
| HOLD_5_SESSIONS | 4 : 5 | 66/66 (0) | 50.00% (38.27–61.73%) | USD -181.82 | USD -12,000.20 | USD -4,692.70 |
| HOLD_10_SESSIONS | 1 : 1 | 65/66 (1) | 36.92% (26.23–49.08%) | USD -50.09 | USD -3,256.00 | USD -746.60 |
| HOLD_10_SESSIONS | 1 : 6 | 65/66 (1) | 75.38% (63.69–84.24%) | USD 399.87 | USD 25,991.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 65/66 (1) | 15.38% (8.58–26.06%) | USD -750.52 | USD -48,783.50 | USD -3,797.10 |
| HOLD_10_SESSIONS | 4 : 5 | 65/66 (1) | 64.62% (52.48–75.12%) | USD -110.38 | USD -7,174.50 | USD -5,058.70 |
| HOLD_20_SESSIONS | 1 : 1 | 65/66 (1) | 40.00% (28.97–52.14%) | USD -26.83 | USD -1,744.00 | USD -975.60 |
| HOLD_20_SESSIONS | 1 : 6 | 65/66 (1) | 84.62% (73.94–91.42%) | USD 787.28 | USD 51,173.50 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 65/66 (1) | 16.92% (9.72–27.82%) | USD -975.10 | USD -63,381.50 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 65/66 (1) | 80.00% (68.73–87.92%) | USD 55.50 | USD 3,607.50 | USD -5,571.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 62/66 (4) | 48.39% (36.41–60.55%) | USD -54.16 | USD -3,358.20 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 62/66 (4) | 87.10% (76.55–93.31%) | USD 422.64 | USD 26,203.80 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 62/66 (4) | 19.35% (11.43–30.85%) | USD -801.79 | USD -49,711.20 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 62/66 (4) | 77.42% (65.59–86.04%) | USD -121.30 | USD -7,520.40 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/66 | 0.00% | USD -95,802.11 | USD -144,087.90 |
| -75% | 0/66 | 0.00% | USD -70,794.58 | USD -106,874.90 |
| -50% | 0/66 | 0.00% | USD -45,787.05 | USD -69,661.90 |
| -40% | 0/66 | 0.00% | USD -35,784.04 | USD -54,776.70 |
| -30% | 0/66 | 0.00% | USD -25,781.03 | USD -39,891.50 |
| -25% | 0/66 | 0.00% | USD -20,779.52 | USD -32,448.90 |
| -20% | 0/66 | 0.00% | USD -15,778.02 | USD -25,006.30 |
| -15% | 0/66 | 0.00% | USD -10,776.51 | USD -17,582.80 |
| -10% | 2/66 | 3.03% | USD -5,773.62 | USD -10,808.50 |
| -5% | 24/66 | 36.36% | USD -831.80 | USD -4,034.20 |
| 0% | 66/66 | 100.00% | USD 860.19 | USD 356.10 |
| 5% | 66/66 | 100.00% | USD 858.13 | USD 356.10 |
| 10% | 66/66 | 100.00% | USD 858.13 | USD 356.10 |
| 20% | 66/66 | 100.00% | USD 858.13 | USD 356.10 |

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