# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 131 checks; 131 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 905.89 / USD 1,796.46; mean absolute mismatch USD 890.56; mean match score 49.78%.
- Actual selected contract ratios: {'2:4': 131}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 131; entered cohorts: 131; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 131/131 | 91/40/0 | 69.47% (61.12–76.70%) | USD -18.29 | USD 170.20 | USD -2,395.80 | USD -8,305.80 | 0 |
| HOLD_10_SESSIONS | 129/131 | 94/35/0 | 72.87% (64.62–79.80%) | USD 15.47 | USD 328.20 | USD 1,995.80 | USD -8,717.80 | 2 |
| HOLD_20_SESSIONS | 129/131 | 110/19/0 | 85.27% (78.14–90.36%) | USD 119.36 | USD 538.20 | USD 15,397.80 | USD -27,571.80 | 2 |
| EXIT_AT_DTE_LE_7 | 113/131 | 93/20/0 | 82.30% (74.24–88.24%) | USD -70.31 | USD 598.20 | USD -7,945.40 | USD -20,497.80 | 18 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -133.11 | USD 182.63 |
| HOLD_10_SESSIONS | USD -192.45 | USD 275.72 |
| HOLD_20_SESSIONS | USD -335.60 | USD 522.76 |
| EXIT_AT_DTE_LE_7 | USD -242.48 | USD 239.96 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 131 | 74.05% | USD 49.51 | USD 6,486.00 | USD -8,238.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 131 | 73.28% | USD 41.71 | USD 5,464.20 | USD -8,245.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 131 | 72.52% | USD 19.51 | USD 2,556.00 | USD -8,268.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 131 | 70.99% | USD 11.71 | USD 1,534.20 | USD -8,275.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 131 | 69.47% | USD -10.49 | USD -1,374.00 | USD -8,298.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 131 | 69.47% | USD -18.29 | USD -2,395.80 | USD -8,305.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 131 | 64.89% | USD -70.49 | USD -9,234.00 | USD -8,358.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 131 | 64.89% | USD -78.29 | USD -10,255.80 | USD -8,365.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 129 | 75.19% | USD 83.27 | USD 10,742.00 | USD -8,650.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 129 | 75.19% | USD 75.47 | USD 9,735.80 | USD -8,657.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 129 | 74.42% | USD 53.27 | USD 6,872.00 | USD -8,680.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 129 | 73.64% | USD 45.47 | USD 5,865.80 | USD -8,687.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 129 | 72.87% | USD 23.27 | USD 3,002.00 | USD -8,710.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 129 | 72.87% | USD 15.47 | USD 1,995.80 | USD -8,717.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 129 | 72.09% | USD -36.73 | USD -4,738.00 | USD -8,770.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 129 | 72.09% | USD -44.53 | USD -5,744.20 | USD -8,777.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 129 | 85.27% | USD 187.16 | USD 24,144.00 | USD -27,504.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 129 | 85.27% | USD 179.36 | USD 23,137.80 | USD -27,511.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 129 | 85.27% | USD 157.16 | USD 20,274.00 | USD -27,534.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 129 | 85.27% | USD 149.36 | USD 19,267.80 | USD -27,541.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 129 | 85.27% | USD 127.16 | USD 16,404.00 | USD -27,564.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 129 | 85.27% | USD 119.36 | USD 15,397.80 | USD -27,571.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 129 | 85.27% | USD 67.16 | USD 8,664.00 | USD -27,624.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 129 | 85.27% | USD 59.36 | USD 7,657.80 | USD -27,631.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 113 | 83.19% | USD -2.51 | USD -284.00 | USD -20,430.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 113 | 83.19% | USD -10.31 | USD -1,165.40 | USD -20,437.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 113 | 83.19% | USD -32.51 | USD -3,674.00 | USD -20,460.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 113 | 83.19% | USD -40.31 | USD -4,555.40 | USD -20,467.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 113 | 83.19% | USD -62.51 | USD -7,064.00 | USD -20,490.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 113 | 82.30% | USD -70.31 | USD -7,945.40 | USD -20,497.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 113 | 82.30% | USD -122.51 | USD -13,844.00 | USD -20,550.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 113 | 82.30% | USD -130.31 | USD -14,725.40 | USD -20,557.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 131/131 (0) | 35.88% (28.17–44.39%) | USD -43.50 | USD -5,698.60 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 131/131 (0) | 72.52% (64.32–79.44%) | USD 128.28 | USD 16,804.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 131/131 (0) | 22.90% (16.54–30.81%) | USD -432.79 | USD -56,695.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 131/131 (0) | 50.38% (41.93–58.81%) | USD -139.65 | USD -18,293.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 129/131 (2) | 36.43% (28.63–45.02%) | USD -49.89 | USD -6,436.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 129/131 (2) | 74.42% (66.26–81.17%) | USD 238.26 | USD 30,735.10 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 129/131 (2) | 19.38% (13.49–27.05%) | USD -587.52 | USD -75,789.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 129/131 (2) | 58.91% (50.29–67.03%) | USD -141.95 | USD -18,311.30 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 129/131 (2) | 40.31% (32.24–48.94%) | USD -59.71 | USD -7,702.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 129/131 (2) | 84.50% (77.26–89.73%) | USD 537.24 | USD 69,304.10 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 129/131 (2) | 16.28% (10.90–23.61%) | USD -955.20 | USD -123,220.90 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 129/131 (2) | 78.29% (70.42–84.53%) | USD -119.44 | USD -15,408.30 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 113/131 (18) | 41.59% (32.93–50.81%) | USD -83.85 | USD -9,474.80 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 113/131 (18) | 84.96% (77.22–90.39%) | USD 159.61 | USD 18,035.70 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 113/131 (18) | 17.70% (11.76–25.76%) | USD -746.54 | USD -84,359.30 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 113/131 (18) | 74.34% (65.58–81.50%) | USD -286.70 | USD -32,397.10 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/131 | 0.00% | USD -95,422.88 | USD -144,087.90 |
| -75% | 0/131 | 0.00% | USD -70,500.57 | USD -106,874.90 |
| -50% | 0/131 | 0.00% | USD -45,578.27 | USD -69,661.90 |
| -40% | 0/131 | 0.00% | USD -35,609.34 | USD -54,776.70 |
| -30% | 0/131 | 0.00% | USD -25,640.42 | USD -39,891.50 |
| -25% | 0/131 | 0.00% | USD -20,655.96 | USD -32,448.90 |
| -20% | 0/131 | 0.00% | USD -15,671.50 | USD -25,006.30 |
| -15% | 1/131 | 0.76% | USD -10,687.04 | USD -17,582.80 |
| -10% | 4/131 | 3.05% | USD -5,712.06 | USD -10,808.50 |
| -5% | 48/131 | 36.64% | USD -846.35 | USD -4,034.20 |
| 0% | 131/131 | 100.00% | USD 857.70 | USD 270.10 |
| 5% | 131/131 | 100.00% | USD 856.66 | USD 270.10 |
| 10% | 131/131 | 100.00% | USD 856.66 | USD 270.10 |
| 20% | 131/131 | 100.00% | USD 856.66 | USD 270.10 |

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