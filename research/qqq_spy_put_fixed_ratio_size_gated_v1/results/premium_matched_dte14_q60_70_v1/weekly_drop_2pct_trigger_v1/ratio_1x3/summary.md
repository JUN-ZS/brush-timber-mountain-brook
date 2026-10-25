# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_2pct_corr60_pos — SPY rolling 5-session return crosses from above -2% to <= -2%, with positive Pearson correlation over the prior 60 daily returns; entry no earlier than next observed common session.
- Filter evaluation: 1954 checks; 99 qualified; 1855 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,082.72 / USD 853.85; mean absolute mismatch USD 327.11; mean match score 70.60%.
- Actual selected contract ratios: {'1:3': 99}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 99; entered cohorts: 99; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 99/99 | 47/52/0 | 47.47% (37.92–57.22%) | USD 65.40 | USD -59.20 | USD 6,474.20 | USD -3,201.20 | 0 |
| HOLD_10_SESSIONS | 5/99 | 4/1/0 | 80.00% (37.55–96.38%) | USD 458.00 | USD 370.80 | USD 2,290.00 | USD -0.20 | 94 |
| HOLD_20_SESSIONS | 0/99 | 0/0/0 | — | — | — | — | — | 99 |
| HOLD_20_OR_DTE_LE_7 | 99/99 | 44/55/0 | 44.44% (35.05–54.26%) | USD -84.44 | USD -50.20 | USD -8,359.80 | USD -8,355.20 | 0 |
| EXIT_AT_DTE_LE_7 | 99/99 | 44/55/0 | 44.44% (35.05–54.26%) | USD -84.44 | USD -50.20 | USD -8,359.80 | USD -8,355.20 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -202.04 | USD 312.64 |
| HOLD_10_SESSIONS | USD -408.20 | USD 911.40 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -133.82 | USD 94.58 |
| EXIT_AT_DTE_LE_7 | USD -133.82 | USD 94.58 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 99 | 48.48% | USD 110.60 | USD 10,949.00 | USD -3,156.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 99 | 48.48% | USD 105.40 | USD 10,434.20 | USD -3,161.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 99 | 47.47% | USD 90.60 | USD 8,969.00 | USD -3,176.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 99 | 47.47% | USD 85.40 | USD 8,454.20 | USD -3,181.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 99 | 47.47% | USD 70.60 | USD 6,989.00 | USD -3,196.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 99 | 47.47% | USD 65.40 | USD 6,474.20 | USD -3,201.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 99 | 44.44% | USD 30.60 | USD 3,029.00 | USD -3,236.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 99 | 44.44% | USD 25.40 | USD 2,514.20 | USD -3,241.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 5 | 100.00% | USD 503.20 | USD 2,516.00 | USD 45.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 5 | 100.00% | USD 498.00 | USD 2,490.00 | USD 39.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 5 | 100.00% | USD 483.20 | USD 2,416.00 | USD 25.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 5 | 100.00% | USD 478.00 | USD 2,390.00 | USD 19.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 5 | 100.00% | USD 463.20 | USD 2,316.00 | USD 5.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 5 | 80.00% | USD 458.00 | USD 2,290.00 | USD -0.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 5 | 80.00% | USD 423.20 | USD 2,116.00 | USD -35.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 5 | 80.00% | USD 418.00 | USD 2,090.00 | USD -40.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 99 | 49.49% | USD -39.24 | USD -3,885.00 | USD -8,310.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 99 | 47.47% | USD -44.44 | USD -4,399.80 | USD -8,315.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 99 | 47.47% | USD -59.24 | USD -5,865.00 | USD -8,330.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 99 | 46.46% | USD -64.44 | USD -6,379.80 | USD -8,335.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 99 | 45.45% | USD -79.24 | USD -7,845.00 | USD -8,350.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 99 | 44.44% | USD -84.44 | USD -8,359.80 | USD -8,355.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 99 | 41.41% | USD -119.24 | USD -11,805.00 | USD -8,390.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 99 | 39.39% | USD -124.44 | USD -12,319.80 | USD -8,395.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 99 | 49.49% | USD -39.24 | USD -3,885.00 | USD -8,310.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 99 | 47.47% | USD -44.44 | USD -4,399.80 | USD -8,315.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 99 | 47.47% | USD -59.24 | USD -5,865.00 | USD -8,330.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 99 | 46.46% | USD -64.44 | USD -6,379.80 | USD -8,335.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 99 | 45.45% | USD -79.24 | USD -7,845.00 | USD -8,350.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 99 | 44.44% | USD -84.44 | USD -8,359.80 | USD -8,355.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 99 | 41.41% | USD -119.24 | USD -11,805.00 | USD -8,390.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 99 | 39.39% | USD -124.44 | USD -12,319.80 | USD -8,395.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 99/99 (0) | 37.37% (28.48–47.21%) | USD -120.43 | USD -11,922.40 | USD -1,519.60 |
| HOLD_5_SESSIONS | 1 : 6 | 99/99 (0) | 76.77% (67.54–83.99%) | USD 344.13 | USD 34,069.10 | USD -8,260.10 |
| HOLD_5_SESSIONS | 6 : 1 | 99/99 (0) | 33.33% (24.82–43.09%) | USD -1,187.13 | USD -117,525.90 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 99/99 (0) | 37.37% (28.48–47.21%) | USD -602.14 | USD -59,612.00 | USD -7,598.00 |
| HOLD_10_SESSIONS | 1 : 1 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -127.00 | USD -635.00 | USD -640.60 |
| HOLD_10_SESSIONS | 1 : 6 | 5/99 (94) | 100.00% (56.55–100.00%) | USD 1,335.50 | USD 6,677.50 | USD 600.90 |
| HOLD_10_SESSIONS | 6 : 1 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -2,224.50 | USD -11,122.50 | USD -6,197.10 |
| HOLD_10_SESSIONS | 5 : 5 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -635.00 | USD -3,175.00 | USD -3,203.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/99 (99) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -124.89 | USD -12,364.40 | USD -1,312.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 99/99 (0) | 70.71% (61.10–78.76%) | USD -23.77 | USD -2,352.90 | USD -21,700.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 99/99 (0) | 33.33% (24.82–43.09%) | USD -850.48 | USD -84,197.90 | USD -16,269.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -624.46 | USD -61,822.00 | USD -6,563.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -124.89 | USD -12,364.40 | USD -1,312.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 99/99 (0) | 70.71% (61.10–78.76%) | USD -23.77 | USD -2,352.90 | USD -21,700.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 99/99 (0) | 33.33% (24.82–43.09%) | USD -850.48 | USD -84,197.90 | USD -16,269.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -624.46 | USD -61,822.00 | USD -6,563.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/99 | 0.00% | USD -85,188.34 | USD -134,055.60 |
| -75% | 0/99 | 0.00% | USD -62,763.36 | USD -99,457.35 |
| -50% | 0/99 | 0.00% | USD -40,338.37 | USD -64,859.10 |
| -40% | 0/99 | 0.00% | USD -31,368.38 | USD -51,019.80 |
| -30% | 0/99 | 0.00% | USD -22,398.39 | USD -37,180.50 |
| -25% | 0/99 | 0.00% | USD -17,913.39 | USD -30,260.85 |
| -20% | 0/99 | 0.00% | USD -13,428.39 | USD -23,341.20 |
| -15% | 1/99 | 1.01% | USD -8,943.40 | USD -16,421.55 |
| -10% | 3/99 | 3.03% | USD -4,478.33 | USD -9,501.90 |
| -5% | 47/99 | 47.47% | USD -210.57 | USD -3,185.80 |
| 0% | 79/99 | 79.80% | USD 479.27 | USD -436.60 |
| 5% | 14/99 | 14.14% | USD -201.81 | USD -929.60 |
| 10% | 11/99 | 11.11% | USD -251.41 | USD -1,049.60 |
| 20% | 11/99 | 11.11% | USD -251.47 | USD -1,049.60 |

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