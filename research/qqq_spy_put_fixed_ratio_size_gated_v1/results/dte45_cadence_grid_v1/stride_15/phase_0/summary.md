# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 131 checks; 131 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 453.24 / USD 2,695.69; mean absolute mismatch USD 2,242.45; mean match score 16.60%.
- Actual selected contract ratios: {'1:6': 131}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 131; entered cohorts: 131; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 129/131 | 109/20/0 | 84.50% (77.26–89.73%) | USD 531.64 | USD 1,400.90 | USD 68,582.10 | USD -51,851.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -167.12 | USD 777.86 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 129 | 85.27% | USD 610.74 | USD 78,786.00 | USD -51,772.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 129 | 85.27% | USD 601.64 | USD 77,612.10 | USD -51,781.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 129 | 84.50% | USD 575.74 | USD 74,271.00 | USD -51,807.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 129 | 84.50% | USD 566.64 | USD 73,097.10 | USD -51,816.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 129 | 84.50% | USD 540.74 | USD 69,756.00 | USD -51,842.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 129 | 84.50% | USD 531.64 | USD 68,582.10 | USD -51,851.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 129 | 84.50% | USD 470.74 | USD 60,726.00 | USD -51,912.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 129 | 84.50% | USD 461.64 | USD 59,552.10 | USD -51,921.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 129/131 (2) | 40.31% (32.24–48.94%) | USD -60.07 | USD -7,749.40 | USD -4,269.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 129/131 (2) | 84.50% (77.26–89.73%) | USD 531.64 | USD 68,582.10 | USD -51,851.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 129/131 (2) | 16.28% (10.90–23.61%) | USD -952.15 | USD -122,827.90 | USD -7,649.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 129/131 (2) | 40.31% (32.24–48.94%) | USD -300.36 | USD -38,747.00 | USD -21,348.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/131 | 0.00% | USD -204,859.01 | USD -333,646.55 |
| -75% | 0/131 | 0.00% | USD -151,006.36 | USD -246,651.05 |
| -50% | 0/131 | 0.00% | USD -97,153.70 | USD -159,655.55 |
| -40% | 0/131 | 0.00% | USD -75,612.64 | USD -124,857.35 |
| -30% | 0/131 | 0.00% | USD -54,071.58 | USD -90,059.15 |
| -25% | 0/131 | 0.00% | USD -43,301.05 | USD -72,660.05 |
| -20% | 0/131 | 0.00% | USD -32,530.52 | USD -55,260.95 |
| -15% | 1/131 | 0.76% | USD -21,759.99 | USD -37,900.05 |
| -10% | 3/131 | 2.29% | USD -11,020.60 | USD -21,632.55 |
| -5% | 54/131 | 41.22% | USD -862.03 | USD -6,851.20 |
| 0% | 131/131 | 100.00% | USD 2,203.42 | USD 696.45 |
| 5% | 131/131 | 100.00% | USD 2,202.90 | USD 696.45 |
| 10% | 131/131 | 100.00% | USD 2,202.90 | USD 696.45 |
| 20% | 131/131 | 100.00% | USD 2,202.90 | USD 696.45 |

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