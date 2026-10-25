# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_1pct — SPY rolling 5-session close return crosses from above -1% to <= -1%; no correlation gate; entry next observed common session.
- Filter evaluation: 1951 checks; 138 qualified; 1813 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,022.41 / USD 1,640.52; mean absolute mismatch USD 639.35; mean match score 66.50%.
- Actual selected contract ratios: {'1:6': 138}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 138; entered cohorts: 138; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 137/138 | 101/36/0 | 73.72% (65.78–80.37%) | USD -0.84 | USD 290.90 | USD -114.70 | USD -20,393.10 | 1 |
| HOLD_10_SESSIONS | 14/138 | 14/0/0 | 100.00% (78.47–100.00%) | USD 916.40 | USD 425.40 | USD 12,829.60 | USD 64.90 | 124 |
| HOLD_20_SESSIONS | 0/138 | 0/0/0 | — | — | — | — | — | 138 |
| HOLD_20_OR_DTE_LE_7 | 138/138 | 107/31/0 | 77.54% (69.88–83.70%) | USD 6.13 | USD 271.40 | USD 846.20 | USD -15,422.10 | 0 |
| EXIT_AT_DTE_LE_7 | 138/138 | 107/31/0 | 77.54% (69.88–83.70%) | USD 6.13 | USD 271.40 | USD 846.20 | USD -15,422.10 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -146.72 | USD 224.98 |
| HOLD_10_SESSIONS | USD -571.36 | USD 1,566.86 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -185.20 | USD 270.43 |
| EXIT_AT_DTE_LE_7 | USD -185.20 | USD 270.43 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 137 | 78.10% | USD 78.26 | USD 10,722.00 | USD -20,314.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 137 | 78.10% | USD 69.16 | USD 9,475.30 | USD -20,323.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 137 | 76.64% | USD 43.26 | USD 5,927.00 | USD -20,349.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 137 | 76.64% | USD 34.16 | USD 4,680.30 | USD -20,358.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 137 | 74.45% | USD 8.26 | USD 1,132.00 | USD -20,384.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 137 | 73.72% | USD -0.84 | USD -114.70 | USD -20,393.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 137 | 70.07% | USD -61.74 | USD -8,458.00 | USD -20,454.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 137 | 69.34% | USD -70.84 | USD -9,704.70 | USD -20,463.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 14 | 100.00% | USD 995.50 | USD 13,937.00 | USD 144.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 14 | 100.00% | USD 986.40 | USD 13,809.60 | USD 134.90 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 14 | 100.00% | USD 960.50 | USD 13,447.00 | USD 109.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 14 | 100.00% | USD 951.40 | USD 13,319.60 | USD 99.90 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 14 | 100.00% | USD 925.50 | USD 12,957.00 | USD 74.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 14 | 100.00% | USD 916.40 | USD 12,829.60 | USD 64.90 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 14 | 100.00% | USD 855.50 | USD 11,977.00 | USD 4.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 14 | 92.86% | USD 846.40 | USD 11,849.60 | USD -5.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 138 | 79.71% | USD 85.23 | USD 11,762.00 | USD -15,343.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 138 | 79.71% | USD 76.13 | USD 10,506.20 | USD -15,352.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 138 | 78.99% | USD 50.23 | USD 6,932.00 | USD -15,378.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 138 | 77.54% | USD 41.13 | USD 5,676.20 | USD -15,387.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 138 | 77.54% | USD 15.23 | USD 2,102.00 | USD -15,413.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 138 | 77.54% | USD 6.13 | USD 846.20 | USD -15,422.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 138 | 74.64% | USD -54.77 | USD -7,558.00 | USD -15,483.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 138 | 72.46% | USD -63.87 | USD -8,813.80 | USD -15,492.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 138 | 79.71% | USD 85.23 | USD 11,762.00 | USD -15,343.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 138 | 79.71% | USD 76.13 | USD 10,506.20 | USD -15,352.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 138 | 78.99% | USD 50.23 | USD 6,932.00 | USD -15,378.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 138 | 77.54% | USD 41.13 | USD 5,676.20 | USD -15,387.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 138 | 77.54% | USD 15.23 | USD 2,102.00 | USD -15,413.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 138 | 77.54% | USD 6.13 | USD 846.20 | USD -15,422.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 138 | 74.64% | USD -54.77 | USD -7,558.00 | USD -15,483.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 138 | 72.46% | USD -63.87 | USD -8,813.80 | USD -15,492.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 137/138 (1) | 33.58% (26.21–41.84%) | USD -131.82 | USD -18,059.20 | USD -1,519.60 |
| HOLD_5_SESSIONS | 1 : 6 | 137/138 (1) | 73.72% (65.78–80.37%) | USD -0.84 | USD -114.70 | USD -20,393.10 |
| HOLD_5_SESSIONS | 6 : 1 | 137/138 (1) | 33.58% (26.21–41.84%) | USD -921.90 | USD -126,299.70 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 137/138 (1) | 33.58% (26.21–41.84%) | USD -659.09 | USD -90,296.00 | USD -7,598.00 |
| HOLD_10_SESSIONS | 1 : 1 | 14/138 (124) | 21.43% (7.57–47.59%) | USD -332.81 | USD -4,659.40 | USD -987.60 |
| HOLD_10_SESSIONS | 1 : 6 | 14/138 (124) | 100.00% (78.47–100.00%) | USD 916.40 | USD 12,829.60 | USD 64.90 |
| HOLD_10_SESSIONS | 6 : 1 | 14/138 (124) | 14.29% (4.01–39.94%) | USD -3,246.10 | USD -45,445.40 | USD -10,574.10 |
| HOLD_10_SESSIONS | 5 : 5 | 14/138 (124) | 21.43% (7.57–47.59%) | USD -1,664.07 | USD -23,297.00 | USD -4,938.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/138 (138) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -162.73 | USD -22,456.80 | USD -1,312.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 138/138 (0) | 77.54% (69.88–83.70%) | USD 6.13 | USD 846.20 | USD -15,422.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 138/138 (0) | 31.88% (24.69–40.06%) | USD -1,145.24 | USD -158,043.80 | USD -16,269.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -813.65 | USD -112,284.00 | USD -6,563.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -162.73 | USD -22,456.80 | USD -1,312.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 138/138 (0) | 77.54% (69.88–83.70%) | USD 6.13 | USD 846.20 | USD -15,422.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 138/138 (0) | 31.88% (24.69–40.06%) | USD -1,145.24 | USD -158,043.80 | USD -16,269.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -813.65 | USD -112,284.00 | USD -6,563.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/138 | 0.00% | USD -203,312.01 | USD -333,053.55 |
| -75% | 0/138 | 0.00% | USD -150,504.82 | USD -246,998.55 |
| -50% | 0/138 | 0.00% | USD -97,697.63 | USD -160,943.55 |
| -40% | 0/138 | 0.00% | USD -76,574.75 | USD -126,521.55 |
| -30% | 0/138 | 0.00% | USD -55,451.87 | USD -92,099.55 |
| -25% | 0/138 | 0.00% | USD -44,890.43 | USD -74,888.55 |
| -20% | 0/138 | 0.00% | USD -34,328.99 | USD -58,039.95 |
| -15% | 0/138 | 0.00% | USD -23,767.55 | USD -41,219.10 |
| -10% | 2/138 | 1.45% | USD -13,234.72 | USD -24,833.75 |
| -5% | 25/138 | 18.12% | USD -2,916.89 | USD -8,583.65 |
| 0% | 137/138 | 99.28% | USD 1,271.99 | USD -122.55 |
| 5% | 123/138 | 89.13% | USD 628.52 | USD -412.55 |
| 10% | 123/138 | 89.13% | USD 578.61 | USD -412.55 |
| 20% | 123/138 | 89.13% | USD 578.57 | USD -412.55 |

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