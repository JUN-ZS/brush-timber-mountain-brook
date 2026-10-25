# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_2pct_corr60_pos — SPY rolling 5-session return crosses from above -2% to <= -2%, with positive Pearson correlation over the prior 60 daily returns; entry no earlier than next observed common session.
- Filter evaluation: 1950 checks; 99 qualified; 1851 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 2,152.42 / USD 1,685.27; mean absolute mismatch USD 663.64; mean match score 69.94%.
- Actual selected contract ratios: {'2:6': 99}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 99; entered cohorts: 99; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/99 | 47/51/0 | 47.96% (38.33–57.74%) | USD 138.44 | USD -112.40 | USD 13,566.80 | USD -6,402.40 | 1 |
| HOLD_10_SESSIONS | 5/99 | 4/1/0 | 80.00% (37.55–96.38%) | USD 916.00 | USD 741.60 | USD 4,580.00 | USD -0.40 | 94 |
| HOLD_20_SESSIONS | 0/99 | 0/0/0 | — | — | — | — | — | 99 |
| HOLD_20_OR_DTE_LE_7 | 99/99 | 44/55/0 | 44.44% (35.05–54.26%) | USD -179.71 | USD -100.40 | USD -17,791.60 | USD -16,710.40 | 0 |
| EXIT_AT_DTE_LE_7 | 99/99 | 44/55/0 | 44.44% (35.05–54.26%) | USD -179.71 | USD -100.40 | USD -17,791.60 | USD -16,710.40 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -390.82 | USD 619.65 |
| HOLD_10_SESSIONS | USD -816.40 | USD 1,822.80 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -256.22 | USD 166.91 |
| EXIT_AT_DTE_LE_7 | USD -256.22 | USD 166.91 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 48.98% | USD 228.84 | USD 22,426.00 | USD -6,312.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 48.98% | USD 218.44 | USD 21,406.80 | USD -6,322.40 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 47.96% | USD 188.84 | USD 18,506.00 | USD -6,352.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 47.96% | USD 178.44 | USD 17,486.80 | USD -6,362.40 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 47.96% | USD 148.84 | USD 14,586.00 | USD -6,392.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 47.96% | USD 138.44 | USD 13,566.80 | USD -6,402.40 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 45.92% | USD 68.84 | USD 6,746.00 | USD -6,472.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 45.92% | USD 58.44 | USD 5,726.80 | USD -6,482.40 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 5 | 100.00% | USD 1,006.40 | USD 5,032.00 | USD 90.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 5 | 100.00% | USD 996.00 | USD 4,980.00 | USD 79.60 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 5 | 100.00% | USD 966.40 | USD 4,832.00 | USD 50.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 5 | 100.00% | USD 956.00 | USD 4,780.00 | USD 39.60 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 5 | 100.00% | USD 926.40 | USD 4,632.00 | USD 10.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 5 | 80.00% | USD 916.00 | USD 4,580.00 | USD -0.40 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 5 | 80.00% | USD 846.40 | USD 4,232.00 | USD -70.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 5 | 80.00% | USD 836.00 | USD 4,180.00 | USD -80.40 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 99 | 49.49% | USD -89.31 | USD -8,842.00 | USD -16,620.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 99 | 47.47% | USD -99.71 | USD -9,871.60 | USD -16,630.40 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 99 | 47.47% | USD -129.31 | USD -12,802.00 | USD -16,660.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 99 | 46.46% | USD -139.71 | USD -13,831.60 | USD -16,670.40 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 99 | 45.45% | USD -169.31 | USD -16,762.00 | USD -16,700.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 99 | 44.44% | USD -179.71 | USD -17,791.60 | USD -16,710.40 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 99 | 41.41% | USD -249.31 | USD -24,682.00 | USD -16,780.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 99 | 40.40% | USD -259.71 | USD -25,711.60 | USD -16,790.40 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 99 | 49.49% | USD -89.31 | USD -8,842.00 | USD -16,620.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 99 | 47.47% | USD -99.71 | USD -9,871.60 | USD -16,630.40 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 99 | 47.47% | USD -129.31 | USD -12,802.00 | USD -16,660.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 99 | 46.46% | USD -139.71 | USD -13,831.60 | USD -16,670.40 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 99 | 45.45% | USD -169.31 | USD -16,762.00 | USD -16,700.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 99 | 44.44% | USD -179.71 | USD -17,791.60 | USD -16,710.40 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 99 | 41.41% | USD -249.31 | USD -24,682.00 | USD -16,780.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 99 | 40.40% | USD -259.71 | USD -25,711.60 | USD -16,790.40 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/99 (1) | 38.78% (29.73–48.67%) | USD -114.73 | USD -11,243.80 | USD -1,519.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/99 (1) | 78.57% (69.45–85.54%) | USD 345.14 | USD 33,824.20 | USD -8,260.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/99 (1) | 35.71% (26.93–45.57%) | USD -1,148.27 | USD -112,530.80 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 98/99 (1) | 38.78% (29.73–48.67%) | USD -573.66 | USD -56,219.00 | USD -7,598.00 |
| HOLD_10_SESSIONS | 1 : 1 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -127.00 | USD -635.00 | USD -640.60 |
| HOLD_10_SESSIONS | 1 : 6 | 5/99 (94) | 100.00% (56.55–100.00%) | USD 1,335.50 | USD 6,677.50 | USD 600.90 |
| HOLD_10_SESSIONS | 6 : 1 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -2,224.50 | USD -11,122.50 | USD -6,197.10 |
| HOLD_10_SESSIONS | 5 : 5 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -635.00 | USD -3,175.00 | USD -3,203.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/99 (99) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -122.89 | USD -12,166.40 | USD -1,312.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 99/99 (0) | 69.70% (60.05–77.87%) | USD -40.30 | USD -3,989.90 | USD -21,700.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -819.95 | USD -81,174.90 | USD -16,269.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -614.46 | USD -60,832.00 | USD -6,563.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -122.89 | USD -12,166.40 | USD -1,312.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 99/99 (0) | 69.70% (60.05–77.87%) | USD -40.30 | USD -3,989.90 | USD -21,700.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -819.95 | USD -81,174.90 | USD -16,269.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -614.46 | USD -60,832.00 | USD -6,563.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/99 | 0.00% | USD -170,386.09 | USD -268,111.20 |
| -75% | 0/99 | 0.00% | USD -125,523.05 | USD -198,914.70 |
| -50% | 0/99 | 0.00% | USD -80,660.02 | USD -129,718.20 |
| -40% | 0/99 | 0.00% | USD -62,714.80 | USD -102,039.60 |
| -30% | 0/99 | 0.00% | USD -44,769.59 | USD -74,361.00 |
| -25% | 0/99 | 0.00% | USD -35,796.98 | USD -60,521.70 |
| -20% | 0/99 | 0.00% | USD -26,824.38 | USD -46,682.40 |
| -15% | 1/99 | 1.01% | USD -17,851.77 | USD -32,843.10 |
| -10% | 3/99 | 3.03% | USD -8,919.03 | USD -19,003.80 |
| -5% | 47/99 | 47.47% | USD -391.26 | USD -6,371.60 |
| 0% | 78/99 | 78.79% | USD 928.66 | USD -873.20 |
| 5% | 14/99 | 14.14% | USD -413.03 | USD -1,979.20 |
| 10% | 11/99 | 11.11% | USD -512.22 | USD -2,099.20 |
| 20% | 11/99 | 11.11% | USD -512.35 | USD -2,099.20 |

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