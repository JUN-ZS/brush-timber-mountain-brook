# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 449.28 / USD 2,675.51; mean absolute mismatch USD 2,226.23; mean match score 16.67%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 193/196 | 160/33/0 | 82.90% (76.96–87.56%) | USD 623.14 | USD 1,400.90 | USD 120,266.70 | USD -29,813.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -171.86 | USD 874.10 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 83.42% | USD 702.24 | USD 135,533.00 | USD -29,734.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 83.42% | USD 693.14 | USD 133,776.70 | USD -29,743.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 82.90% | USD 667.24 | USD 128,778.00 | USD -29,769.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 82.90% | USD 658.14 | USD 127,021.70 | USD -29,778.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 82.90% | USD 632.24 | USD 122,023.00 | USD -29,804.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 82.90% | USD 623.14 | USD 120,266.70 | USD -29,813.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 82.90% | USD 562.24 | USD 108,513.00 | USD -29,874.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 82.90% | USD 553.14 | USD 106,756.70 | USD -29,883.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 193/196 (3) | 43.52% (36.72–50.58%) | USD -48.78 | USD -9,413.80 | USD -2,926.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 193/196 (3) | 82.90% (76.96–87.56%) | USD 623.14 | USD 120,266.70 | USD -29,813.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 193/196 (3) | 15.54% (11.11–21.32%) | USD -964.58 | USD -186,163.30 | USD -7,645.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 193/196 (3) | 43.52% (36.72–50.58%) | USD -243.88 | USD -47,069.00 | USD -14,633.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -205,191.03 | USD -333,646.55 |
| -75% | 0/196 | 0.00% | USD -151,284.21 | USD -246,651.05 |
| -50% | 0/196 | 0.00% | USD -97,377.39 | USD -159,655.55 |
| -40% | 0/196 | 0.00% | USD -75,814.66 | USD -124,857.35 |
| -30% | 0/196 | 0.00% | USD -54,251.93 | USD -90,195.25 |
| -25% | 0/196 | 0.00% | USD -43,470.57 | USD -73,230.05 |
| -20% | 0/196 | 0.00% | USD -32,689.20 | USD -56,324.75 |
| -15% | 1/196 | 0.51% | USD -21,921.61 | USD -39,423.05 |
| -10% | 4/196 | 2.04% | USD -11,179.04 | USD -23,000.55 |
| -5% | 79/196 | 40.31% | USD -880.85 | USD -8,108.00 |
| 0% | 196/196 | 100.00% | USD 2,187.03 | USD 573.45 |
| 5% | 196/196 | 100.00% | USD 2,186.68 | USD 573.45 |
| 10% | 196/196 | 100.00% | USD 2,186.68 | USD 573.45 |
| 20% | 196/196 | 100.00% | USD 2,186.68 | USD 573.45 |

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