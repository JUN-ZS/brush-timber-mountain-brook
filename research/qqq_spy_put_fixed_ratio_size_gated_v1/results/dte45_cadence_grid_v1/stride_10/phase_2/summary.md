# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 457.29 / USD 2,706.71; mean absolute mismatch USD 2,249.42; mean match score 16.71%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 192/195 | 159/33/0 | 82.81% (76.85–87.49%) | USD 346.66 | USD 1,288.90 | USD 66,558.80 | USD -51,761.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -135.15 | USD 560.91 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 82.81% | USD 425.76 | USD 81,746.00 | USD -51,682.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 82.81% | USD 416.66 | USD 79,998.80 | USD -51,691.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 82.81% | USD 390.76 | USD 75,026.00 | USD -51,717.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 82.81% | USD 381.66 | USD 73,278.80 | USD -51,726.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 82.81% | USD 355.76 | USD 68,306.00 | USD -51,752.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 82.81% | USD 346.66 | USD 66,558.80 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 82.29% | USD 285.76 | USD 54,866.00 | USD -51,822.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 82.29% | USD 276.66 | USD 53,118.80 | USD -51,831.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 192/195 (3) | 38.54% (31.95–45.59%) | USD -64.26 | USD -12,338.20 | USD -4,434.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 192/195 (3) | 82.81% (76.85–87.49%) | USD 346.66 | USD 66,558.80 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 192/195 (3) | 16.67% (12.06–22.58%) | USD -796.49 | USD -152,926.20 | USD -8,979.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 192/195 (3) | 38.54% (31.95–45.59%) | USD -321.31 | USD -61,691.00 | USD -22,173.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/195 | 0.00% | USD -205,582.23 | USD -336,601.55 |
| -75% | 0/195 | 0.00% | USD -151,565.15 | USD -249,385.05 |
| -50% | 0/195 | 0.00% | USD -97,548.07 | USD -162,168.55 |
| -40% | 0/195 | 0.00% | USD -75,941.24 | USD -127,281.95 |
| -30% | 0/195 | 0.00% | USD -54,334.40 | USD -92,395.35 |
| -25% | 0/195 | 0.00% | USD -43,530.99 | USD -74,952.05 |
| -20% | 0/195 | 0.00% | USD -32,727.57 | USD -57,508.75 |
| -15% | 1/195 | 0.51% | USD -21,923.78 | USD -40,065.45 |
| -10% | 4/195 | 2.05% | USD -11,173.85 | USD -23,126.25 |
| -5% | 80/195 | 41.03% | USD -863.00 | USD -8,014.25 |
| 0% | 195/195 | 100.00% | USD 2,191.53 | USD 713.45 |
| 5% | 195/195 | 100.00% | USD 2,209.87 | USD 713.45 |
| 10% | 195/195 | 100.00% | USD 2,209.87 | USD 713.45 |
| 20% | 195/195 | 100.00% | USD 2,209.87 | USD 713.45 |

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