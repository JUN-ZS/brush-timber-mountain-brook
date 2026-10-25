# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_1pct — SPY rolling 5-session close return crosses from above -1% to <= -1%; no correlation gate; entry next observed common session.
- Filter evaluation: 1953 checks; 138 qualified; 1815 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,022.12 / USD 821.28; mean absolute mismatch USD 291.25; mean match score 73.58%.
- Actual selected contract ratios: {'1:3': 138}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 138; entered cohorts: 138; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 138/138 | 54/84/0 | 39.13% (31.39–47.46%) | USD -103.40 | USD -70.20 | USD -14,268.60 | USD -7,933.20 | 0 |
| HOLD_10_SESSIONS | 15/138 | 8/7/0 | 53.33% (30.12–75.19%) | USD 181.07 | USD 124.80 | USD 2,716.00 | USD -405.20 | 123 |
| HOLD_20_SESSIONS | 0/138 | 0/0/0 | — | — | — | — | — | 138 |
| HOLD_20_OR_DTE_LE_7 | 138/138 | 57/81/0 | 41.30% (33.43–49.65%) | USD -97.50 | USD -47.70 | USD -13,455.60 | USD -5,962.20 | 0 |
| EXIT_AT_DTE_LE_7 | 138/138 | 57/81/0 | 41.30% (33.43–49.65%) | USD -97.50 | USD -47.70 | USD -13,455.60 | USD -5,962.20 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -138.43 | USD 80.24 |
| HOLD_10_SESSIONS | USD -508.53 | USD 734.80 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -182.37 | USD 130.07 |
| EXIT_AT_DTE_LE_7 | USD -182.37 | USD 130.07 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 138 | 47.10% | USD -58.20 | USD -8,031.00 | USD -7,888.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 138 | 44.93% | USD -63.40 | USD -8,748.60 | USD -7,893.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 138 | 44.20% | USD -78.20 | USD -10,791.00 | USD -7,908.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 138 | 42.03% | USD -83.40 | USD -11,508.60 | USD -7,913.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 138 | 41.30% | USD -98.20 | USD -13,551.00 | USD -7,928.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 138 | 39.13% | USD -103.40 | USD -14,268.60 | USD -7,933.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 138 | 36.23% | USD -138.20 | USD -19,071.00 | USD -7,968.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 138 | 36.23% | USD -143.40 | USD -19,788.60 | USD -7,973.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 15 | 66.67% | USD 226.27 | USD 3,394.00 | USD -360.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 15 | 66.67% | USD 221.07 | USD 3,316.00 | USD -365.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 15 | 60.00% | USD 206.27 | USD 3,094.00 | USD -380.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 15 | 60.00% | USD 201.07 | USD 3,016.00 | USD -385.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 15 | 60.00% | USD 186.27 | USD 2,794.00 | USD -400.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 15 | 53.33% | USD 181.07 | USD 2,716.00 | USD -405.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 15 | 53.33% | USD 146.27 | USD 2,194.00 | USD -440.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 15 | 53.33% | USD 141.07 | USD 2,116.00 | USD -445.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 138 | 49.28% | USD -52.30 | USD -7,218.00 | USD -5,917.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 138 | 46.38% | USD -57.50 | USD -7,935.60 | USD -5,922.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 138 | 43.48% | USD -72.30 | USD -9,978.00 | USD -5,937.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 138 | 42.03% | USD -77.50 | USD -10,695.60 | USD -5,942.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 138 | 41.30% | USD -92.30 | USD -12,738.00 | USD -5,957.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 138 | 41.30% | USD -97.50 | USD -13,455.60 | USD -5,962.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 138 | 38.41% | USD -132.30 | USD -18,258.00 | USD -5,997.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 138 | 36.96% | USD -137.50 | USD -18,975.60 | USD -6,002.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 138 | 49.28% | USD -52.30 | USD -7,218.00 | USD -5,917.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 138 | 46.38% | USD -57.50 | USD -7,935.60 | USD -5,922.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 138 | 43.48% | USD -72.30 | USD -9,978.00 | USD -5,937.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 138 | 42.03% | USD -77.50 | USD -10,695.60 | USD -5,942.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 138 | 41.30% | USD -92.30 | USD -12,738.00 | USD -5,957.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 138 | 41.30% | USD -97.50 | USD -13,455.60 | USD -5,962.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 138 | 38.41% | USD -132.30 | USD -18,258.00 | USD -5,997.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 138 | 36.96% | USD -137.50 | USD -18,975.60 | USD -6,002.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 138/138 (0) | 33.33% (26.01–41.56%) | USD -134.29 | USD -18,531.80 | USD -1,519.60 |
| HOLD_5_SESSIONS | 1 : 6 | 138/138 (0) | 73.19% (65.24–79.88%) | USD -57.06 | USD -7,873.80 | USD -20,393.10 |
| HOLD_5_SESSIONS | 6 : 1 | 138/138 (0) | 33.33% (26.01–41.56%) | USD -882.96 | USD -121,848.80 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 138/138 (0) | 33.33% (26.01–41.56%) | USD -671.44 | USD -92,659.00 | USD -7,598.00 |
| HOLD_10_SESSIONS | 1 : 1 | 15/138 (123) | 26.67% (10.90–51.95%) | USD -286.20 | USD -4,293.00 | USD -987.60 |
| HOLD_10_SESSIONS | 1 : 6 | 15/138 (123) | 100.00% (79.61–100.00%) | USD 881.97 | USD 13,229.50 | USD 64.90 |
| HOLD_10_SESSIONS | 6 : 1 | 15/138 (123) | 20.00% (7.05–45.19%) | USD -2,885.37 | USD -43,280.50 | USD -10,574.10 |
| HOLD_10_SESSIONS | 5 : 5 | 15/138 (123) | 26.67% (10.90–51.95%) | USD -1,431.00 | USD -21,465.00 | USD -4,938.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/138 (138) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -161.61 | USD -22,302.80 | USD -1,312.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 138/138 (0) | 76.81% (69.10–83.07%) | USD -1.34 | USD -184.80 | USD -15,422.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 138/138 (0) | 31.88% (24.69–40.06%) | USD -1,129.96 | USD -155,934.80 | USD -16,269.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -808.07 | USD -111,514.00 | USD -6,563.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -161.61 | USD -22,302.80 | USD -1,312.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 138/138 (0) | 76.81% (69.10–83.07%) | USD -1.34 | USD -184.80 | USD -15,422.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 138/138 (0) | 31.88% (24.69–40.06%) | USD -1,129.96 | USD -155,934.80 | USD -16,269.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -808.07 | USD -111,514.00 | USD -6,563.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/138 | 0.00% | USD -85,799.88 | USD -135,729.60 |
| -75% | 0/138 | 0.00% | USD -63,394.71 | USD -100,493.10 |
| -50% | 0/138 | 0.00% | USD -40,989.55 | USD -65,256.60 |
| -40% | 0/138 | 0.00% | USD -32,027.48 | USD -51,162.00 |
| -30% | 0/138 | 0.00% | USD -23,065.41 | USD -37,180.50 |
| -25% | 0/138 | 0.00% | USD -18,584.38 | USD -30,260.85 |
| -20% | 0/138 | 0.00% | USD -14,103.34 | USD -23,341.20 |
| -15% | 1/138 | 0.72% | USD -9,622.31 | USD -16,499.15 |
| -10% | 2/138 | 1.45% | USD -5,155.58 | USD -9,782.30 |
| -5% | 42/138 | 30.43% | USD -796.35 | USD -3,321.15 |
| 0% | 120/138 | 86.96% | USD 502.86 | USD -265.60 |
| 5% | 23/138 | 16.67% | USD -173.48 | USD -939.60 |
| 10% | 20/138 | 14.49% | USD -223.39 | USD -1,049.60 |
| 20% | 20/138 | 14.49% | USD -223.43 | USD -1,049.60 |

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