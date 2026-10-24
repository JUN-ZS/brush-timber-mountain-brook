# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 66 checks; 66 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 451.08 / USD 2,691.27; mean absolute mismatch USD 2,240.20; mean match score 16.64%.
- Actual selected contract ratios: {'1:6': 66}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 66; entered cohorts: 66; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 66/66 | 49/17/0 | 74.24% (62.57–83.25%) | USD 236.90 | USD 594.40 | USD 15,635.40 | USD -3,956.10 | 0 |
| HOLD_10_SESSIONS | 65/66 | 49/16/0 | 75.38% (63.69–84.24%) | USD 399.87 | USD 852.90 | USD 25,991.50 | USD -11,108.10 | 1 |
| HOLD_20_SESSIONS | 65/66 | 55/10/0 | 84.62% (73.94–91.42%) | USD 770.18 | USD 1,343.90 | USD 50,061.50 | USD -12,548.10 | 1 |
| EXIT_AT_DTE_LE_7 | 62/66 | 54/8/0 | 87.10% (76.55–93.31%) | USD 490.93 | USD 1,634.90 | USD 30,437.80 | USD -33,176.10 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -95.36 | USD 411.36 |
| HOLD_10_SESSIONS | USD -128.78 | USD 607.75 |
| HOLD_20_SESSIONS | USD -174.14 | USD 1,023.42 |
| EXIT_AT_DTE_LE_7 | USD -148.90 | USD 718.94 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 66 | 74.24% | USD 316.00 | USD 20,856.00 | USD -3,877.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 66 | 74.24% | USD 306.90 | USD 20,255.40 | USD -3,886.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 66 | 74.24% | USD 281.00 | USD 18,546.00 | USD -3,912.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 66 | 74.24% | USD 271.90 | USD 17,945.40 | USD -3,921.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 66 | 74.24% | USD 246.00 | USD 16,236.00 | USD -3,947.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 66 | 74.24% | USD 236.90 | USD 15,635.40 | USD -3,956.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 66 | 72.73% | USD 176.00 | USD 11,616.00 | USD -4,017.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 66 | 72.73% | USD 166.90 | USD 11,015.40 | USD -4,026.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 65 | 76.92% | USD 478.97 | USD 31,133.00 | USD -11,029.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 65 | 76.92% | USD 469.87 | USD 30,541.50 | USD -11,038.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 65 | 75.38% | USD 443.97 | USD 28,858.00 | USD -11,064.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 65 | 75.38% | USD 434.87 | USD 28,266.50 | USD -11,073.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 65 | 75.38% | USD 408.97 | USD 26,583.00 | USD -11,099.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 65 | 75.38% | USD 399.87 | USD 25,991.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 65 | 75.38% | USD 338.97 | USD 22,033.00 | USD -11,169.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 65 | 75.38% | USD 329.87 | USD 21,441.50 | USD -11,178.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 65 | 86.15% | USD 849.28 | USD 55,203.00 | USD -12,469.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 65 | 86.15% | USD 840.18 | USD 54,611.50 | USD -12,478.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 65 | 84.62% | USD 814.28 | USD 52,928.00 | USD -12,504.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 65 | 84.62% | USD 805.18 | USD 52,336.50 | USD -12,513.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 65 | 84.62% | USD 779.28 | USD 50,653.00 | USD -12,539.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 65 | 84.62% | USD 770.18 | USD 50,061.50 | USD -12,548.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 65 | 84.62% | USD 709.28 | USD 46,103.00 | USD -12,609.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 65 | 84.62% | USD 700.18 | USD 45,511.50 | USD -12,618.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 62 | 87.10% | USD 570.03 | USD 35,342.00 | USD -33,097.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 62 | 87.10% | USD 560.93 | USD 34,777.80 | USD -33,106.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 62 | 87.10% | USD 535.03 | USD 33,172.00 | USD -33,132.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 62 | 87.10% | USD 525.93 | USD 32,607.80 | USD -33,141.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 62 | 87.10% | USD 500.03 | USD 31,002.00 | USD -33,167.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 62 | 87.10% | USD 490.93 | USD 30,437.80 | USD -33,176.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 62 | 87.10% | USD 430.03 | USD 26,662.00 | USD -33,237.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 62 | 87.10% | USD 420.93 | USD 26,097.80 | USD -33,246.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 66/66 (0) | 27.27% (18.00–39.04%) | USD -49.40 | USD -3,260.60 | USD -480.60 |
| HOLD_5_SESSIONS | 1 : 6 | 66/66 (0) | 74.24% (62.57–83.25%) | USD 236.90 | USD 15,635.40 | USD -3,956.10 |
| HOLD_5_SESSIONS | 6 : 1 | 66/66 (0) | 19.70% (11.89–30.84%) | USD -582.72 | USD -38,459.60 | USD -3,001.10 |
| HOLD_5_SESSIONS | 4 : 5 | 66/66 (0) | 51.52% (39.71–63.15%) | USD -140.35 | USD -9,263.20 | USD -2,272.70 |
| HOLD_10_SESSIONS | 1 : 1 | 65/66 (1) | 36.92% (26.23–49.08%) | USD -50.09 | USD -3,256.00 | USD -746.60 |
| HOLD_10_SESSIONS | 1 : 6 | 65/66 (1) | 75.38% (63.69–84.24%) | USD 399.87 | USD 25,991.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 65/66 (1) | 15.38% (8.58–26.06%) | USD -750.52 | USD -48,783.50 | USD -3,797.10 |
| HOLD_10_SESSIONS | 4 : 5 | 65/66 (1) | 64.62% (52.48–75.12%) | USD -110.38 | USD -7,174.50 | USD -5,058.70 |
| HOLD_20_SESSIONS | 1 : 1 | 65/66 (1) | 40.00% (28.97–52.14%) | USD -26.17 | USD -1,701.00 | USD -975.60 |
| HOLD_20_SESSIONS | 1 : 6 | 65/66 (1) | 84.62% (73.94–91.42%) | USD 770.18 | USD 50,061.50 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 65/66 (1) | 16.92% (9.72–27.82%) | USD -953.36 | USD -61,968.50 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 65/66 (1) | 80.00% (68.73–87.92%) | USD 54.59 | USD 3,548.50 | USD -5,571.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 62/66 (4) | 48.39% (36.41–60.55%) | USD -51.68 | USD -3,204.20 | USD -3,304.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 62/66 (4) | 87.10% (76.55–93.31%) | USD 490.93 | USD 30,437.80 | USD -33,176.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 62/66 (4) | 19.35% (11.43–30.85%) | USD -852.70 | USD -52,867.20 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 62/66 (4) | 77.42% (65.59–86.04%) | USD -98.20 | USD -6,088.40 | USD -19,192.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/66 | 0.00% | USD -205,687.05 | USD -333,646.55 |
| -75% | 0/66 | 0.00% | USD -151,637.56 | USD -246,651.05 |
| -50% | 0/66 | 0.00% | USD -97,588.07 | USD -159,655.55 |
| -40% | 0/66 | 0.00% | USD -75,968.27 | USD -124,857.35 |
| -30% | 0/66 | 0.00% | USD -54,348.47 | USD -90,059.15 |
| -25% | 0/66 | 0.00% | USD -43,538.57 | USD -72,660.05 |
| -20% | 0/66 | 0.00% | USD -32,728.67 | USD -55,260.95 |
| -15% | 0/66 | 0.00% | USD -21,918.78 | USD -37,900.05 |
| -10% | 1/66 | 1.52% | USD -11,108.19 | USD -21,632.55 |
| -5% | 27/66 | 40.91% | USD -858.00 | USD -6,851.20 |
| 0% | 66/66 | 100.00% | USD 2,201.68 | USD 843.45 |
| 5% | 66/66 | 100.00% | USD 2,200.65 | USD 843.45 |
| 10% | 66/66 | 100.00% | USD 2,200.65 | USD 843.45 |
| 20% | 66/66 | 100.00% | USD 2,200.65 | USD 843.45 |

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