# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 131 checks; 131 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 453.24 / USD 1,347.85; mean absolute mismatch USD 894.60; mean match score 33.19%.
- Actual selected contract ratios: {'1:3': 131}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 131; entered cohorts: 131; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 131/131 | 95/36/0 | 72.52% (64.32–79.44%) | USD 39.59 | USD 219.80 | USD 5,185.80 | USD -7,101.20 | 0 |
| HOLD_10_SESSIONS | 129/131 | 97/32/0 | 75.19% (67.08–81.85%) | USD 65.40 | USD 339.80 | USD 8,436.20 | USD -7,366.20 | 2 |
| HOLD_20_SESSIONS | 129/131 | 110/19/0 | 85.27% (78.14–90.36%) | USD 176.56 | USD 535.80 | USD 22,776.20 | USD -23,302.20 | 2 |
| EXIT_AT_DTE_LE_7 | 114/131 | 95/19/0 | 83.33% (75.43–89.06%) | USD 17.04 | USD 641.30 | USD 1,942.20 | USD -17,039.20 | 17 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -69.18 | USD 153.96 |
| HOLD_10_SESSIONS | USD -96.61 | USD 207.21 |
| HOLD_20_SESSIONS | USD -167.10 | USD 388.86 |
| EXIT_AT_DTE_LE_7 | USD -121.71 | USD 183.95 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 131 | 74.05% | USD 84.79 | USD 11,107.00 | USD -7,056.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 131 | 74.05% | USD 79.59 | USD 10,425.80 | USD -7,061.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 131 | 74.05% | USD 64.79 | USD 8,487.00 | USD -7,076.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 131 | 72.52% | USD 59.59 | USD 7,805.80 | USD -7,081.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 131 | 72.52% | USD 44.79 | USD 5,867.00 | USD -7,096.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 131 | 72.52% | USD 39.59 | USD 5,185.80 | USD -7,101.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 131 | 69.47% | USD 4.79 | USD 627.00 | USD -7,136.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 131 | 69.47% | USD -0.41 | USD -54.20 | USD -7,141.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 129 | 76.74% | USD 110.60 | USD 14,267.00 | USD -7,321.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 129 | 76.74% | USD 105.40 | USD 13,596.20 | USD -7,326.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 129 | 75.97% | USD 90.60 | USD 11,687.00 | USD -7,341.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 129 | 75.97% | USD 85.40 | USD 11,016.20 | USD -7,346.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 129 | 75.19% | USD 70.60 | USD 9,107.00 | USD -7,361.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 129 | 75.19% | USD 65.40 | USD 8,436.20 | USD -7,366.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 129 | 74.42% | USD 30.60 | USD 3,947.00 | USD -7,401.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 129 | 73.64% | USD 25.40 | USD 3,276.20 | USD -7,406.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 129 | 85.27% | USD 221.76 | USD 28,607.00 | USD -23,257.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 129 | 85.27% | USD 216.56 | USD 27,936.20 | USD -23,262.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 129 | 85.27% | USD 201.76 | USD 26,027.00 | USD -23,277.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 129 | 85.27% | USD 196.56 | USD 25,356.20 | USD -23,282.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 129 | 85.27% | USD 181.76 | USD 23,447.00 | USD -23,297.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 129 | 85.27% | USD 176.56 | USD 22,776.20 | USD -23,302.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 129 | 84.50% | USD 141.76 | USD 18,287.00 | USD -23,337.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 129 | 84.50% | USD 136.56 | USD 17,616.20 | USD -23,342.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 114 | 84.21% | USD 62.24 | USD 7,095.00 | USD -16,994.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 114 | 84.21% | USD 57.04 | USD 6,502.20 | USD -16,999.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 114 | 84.21% | USD 42.24 | USD 4,815.00 | USD -17,014.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 114 | 84.21% | USD 37.04 | USD 4,222.20 | USD -17,019.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 114 | 83.33% | USD 22.24 | USD 2,535.00 | USD -17,034.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 114 | 83.33% | USD 17.04 | USD 1,942.20 | USD -17,039.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 114 | 83.33% | USD -17.76 | USD -2,025.00 | USD -17,074.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 114 | 83.33% | USD -22.96 | USD -2,617.80 | USD -17,079.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 131/131 (0) | 35.11% (27.47–43.61%) | USD -40.45 | USD -5,299.60 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 131/131 (0) | 72.52% (64.32–79.44%) | USD 159.65 | USD 20,913.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 131/131 (0) | 22.90% (16.54–30.81%) | USD -442.83 | USD -58,011.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 131/131 (0) | 50.38% (41.93–58.81%) | USD -121.80 | USD -15,955.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 129/131 (2) | 36.43% (28.63–45.02%) | USD -50.14 | USD -6,468.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 129/131 (2) | 74.42% (66.26–81.17%) | USD 238.71 | USD 30,793.10 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 129/131 (2) | 19.38% (13.49–27.05%) | USD -589.70 | USD -76,071.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 129/131 (2) | 58.91% (50.29–67.03%) | USD -142.80 | USD -18,421.30 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 129/131 (2) | 40.31% (32.24–48.94%) | USD -60.08 | USD -7,750.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 129/131 (2) | 84.50% (77.26–89.73%) | USD 531.52 | USD 68,566.10 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 129/131 (2) | 16.28% (10.90–23.61%) | USD -952.08 | USD -122,818.90 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 129/131 (2) | 78.29% (70.42–84.53%) | USD -122.00 | USD -15,738.30 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 114/131 (17) | 42.11% (33.44–51.28%) | USD -82.99 | USD -9,461.40 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 114/131 (17) | 85.09% (77.41–90.48%) | USD 167.08 | USD 19,047.60 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 114/131 (17) | 17.54% (11.65–25.55%) | USD -748.05 | USD -85,277.40 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 114/131 (17) | 74.56% (65.86–81.66%) | USD -281.96 | USD -32,143.80 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/131 | 0.00% | USD -86,998.30 | USD -137,444.60 |
| -75% | 0/131 | 0.00% | USD -64,189.20 | USD -101,740.85 |
| -50% | 0/131 | 0.00% | USD -41,380.10 | USD -66,037.10 |
| -40% | 0/131 | 0.00% | USD -32,256.46 | USD -51,755.60 |
| -30% | 0/131 | 0.00% | USD -23,132.82 | USD -37,474.10 |
| -25% | 0/131 | 0.00% | USD -18,571.00 | USD -30,333.35 |
| -20% | 0/131 | 0.00% | USD -14,009.18 | USD -23,192.60 |
| -15% | 1/131 | 0.76% | USD -9,447.36 | USD -16,051.85 |
| -10% | 3/131 | 2.29% | USD -4,896.89 | USD -9,451.60 |
| -5% | 49/131 | 37.40% | USD -532.50 | USD -3,167.65 |
| 0% | 131/131 | 100.00% | USD 872.52 | USD 275.40 |
| 5% | 131/131 | 100.00% | USD 872.00 | USD 275.40 |
| 10% | 131/131 | 100.00% | USD 872.00 | USD 275.40 |
| 20% | 131/131 | 100.00% | USD 872.00 | USD 275.40 |

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