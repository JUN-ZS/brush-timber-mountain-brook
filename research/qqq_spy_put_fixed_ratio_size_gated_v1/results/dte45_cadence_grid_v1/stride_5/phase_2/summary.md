# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 460.54 / USD 2,717.34; mean absolute mismatch USD 2,256.80; mean match score 16.82%.
- Actual selected contract ratios: {'1:6': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 384/391 | 317/67/0 | 82.55% (78.44–86.02%) | USD 501.53 | USD 1,380.90 | USD 192,588.60 | USD -51,761.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -159.18 | USD 739.81 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 384 | 83.07% | USD 580.63 | USD 222,963.00 | USD -51,682.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 384 | 83.07% | USD 571.53 | USD 219,468.60 | USD -51,691.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 384 | 83.07% | USD 545.63 | USD 209,523.00 | USD -51,717.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 384 | 83.07% | USD 536.53 | USD 206,028.60 | USD -51,726.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 384 | 82.55% | USD 510.63 | USD 196,083.00 | USD -51,752.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 384 | 82.55% | USD 501.53 | USD 192,588.60 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 384 | 82.29% | USD 440.63 | USD 169,203.00 | USD -51,822.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 384 | 82.29% | USD 431.53 | USD 165,708.60 | USD -51,831.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 384/391 (7) | 38.28% (33.56–43.24%) | USD -58.48 | USD -22,455.40 | USD -4,434.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 384/391 (7) | 82.55% (78.44–86.02%) | USD 501.53 | USD 192,588.60 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 384/391 (7) | 15.36% (12.10–19.31%) | USD -910.88 | USD -349,776.40 | USD -8,979.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 384/391 (7) | 38.28% (33.56–43.24%) | USD -292.39 | USD -112,277.00 | USD -22,173.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -205,687.86 | USD -337,943.55 |
| -75% | 0/391 | 0.00% | USD -151,651.83 | USD -251,020.05 |
| -50% | 0/391 | 0.00% | USD -97,615.81 | USD -164,096.55 |
| -40% | 0/391 | 0.00% | USD -76,001.40 | USD -129,327.15 |
| -30% | 0/391 | 0.00% | USD -54,386.99 | USD -94,557.75 |
| -25% | 0/391 | 0.00% | USD -43,579.78 | USD -77,173.05 |
| -20% | 0/391 | 0.00% | USD -32,772.58 | USD -59,788.35 |
| -15% | 2/391 | 0.51% | USD -21,966.66 | USD -42,403.65 |
| -10% | 8/391 | 2.05% | USD -11,201.80 | USD -25,018.95 |
| -5% | 164/391 | 41.94% | USD -941.43 | USD -8,775.95 |
| 0% | 391/391 | 100.00% | USD 2,208.11 | USD 677.45 |
| 5% | 391/391 | 100.00% | USD 2,217.25 | USD 677.45 |
| 10% | 391/391 | 100.00% | USD 2,217.25 | USD 677.45 |
| 20% | 391/391 | 100.00% | USD 2,217.25 | USD 677.45 |

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