# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 131 checks; 131 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 437.73 / USD 2,600.11; mean absolute mismatch USD 2,162.37; mean match score 16.81%.
- Actual selected contract ratios: {'1:6': 131}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 131; entered cohorts: 131; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 128/131 | 104/24/0 | 81.25% (73.62–87.06%) | USD 452.13 | USD 1,283.90 | USD 57,873.20 | USD -25,585.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -128.06 | USD 659.30 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 128 | 82.03% | USD 531.23 | USD 67,998.00 | USD -25,506.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 128 | 82.03% | USD 522.13 | USD 66,833.20 | USD -25,515.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 128 | 82.03% | USD 496.23 | USD 63,518.00 | USD -25,541.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 128 | 82.03% | USD 487.13 | USD 62,353.20 | USD -25,550.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 128 | 81.25% | USD 461.23 | USD 59,038.00 | USD -25,576.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 128 | 81.25% | USD 452.13 | USD 57,873.20 | USD -25,585.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 128 | 80.47% | USD 391.23 | USD 50,078.00 | USD -25,646.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 128 | 80.47% | USD 382.13 | USD 48,913.20 | USD -25,655.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 128/131 (3) | 39.06% (31.05–47.72%) | USD -40.78 | USD -5,219.80 | USD -2,293.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 128/131 (3) | 81.25% (73.62–87.06%) | USD 452.13 | USD 57,873.20 | USD -25,585.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 128/131 (3) | 17.19% (11.63–24.65%) | USD -737.59 | USD -94,411.80 | USD -6,391.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 128/131 (3) | 39.06% (31.05–47.72%) | USD -203.90 | USD -26,099.00 | USD -11,468.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/131 | 0.00% | USD -205,873.15 | USD -337,225.55 |
| -75% | 0/131 | 0.00% | USD -151,785.75 | USD -249,489.55 |
| -50% | 0/131 | 0.00% | USD -97,698.36 | USD -161,753.55 |
| -40% | 0/131 | 0.00% | USD -76,063.40 | USD -126,659.15 |
| -30% | 0/131 | 0.00% | USD -54,428.44 | USD -91,564.75 |
| -25% | 0/131 | 0.00% | USD -43,610.96 | USD -74,017.55 |
| -20% | 0/131 | 0.00% | USD -32,793.48 | USD -56,470.35 |
| -15% | 0/131 | 0.00% | USD -21,976.00 | USD -38,923.15 |
| -10% | 4/131 | 3.05% | USD -11,158.39 | USD -21,727.45 |
| -5% | 57/131 | 43.51% | USD -903.10 | USD -8,232.95 |
| 0% | 131/131 | 100.00% | USD 2,122.82 | USD 635.45 |
| 5% | 131/131 | 100.00% | USD 2,122.82 | USD 635.45 |
| 10% | 131/131 | 100.00% | USD 2,122.82 | USD 635.45 |
| 20% | 131/131 | 100.00% | USD 2,122.82 | USD 635.45 |

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