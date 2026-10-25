# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 432.34 / USD 2,549.76; mean absolute mismatch USD 2,117.42; mean match score 16.79%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 191/196 | 158/33/0 | 82.72% (76.73–87.42%) | USD 502.36 | USD 1,407.90 | USD 95,949.90 | USD -44,015.10 | 5 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -159.62 | USD 741.08 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 83.25% | USD 581.46 | USD 111,058.00 | USD -43,936.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 83.25% | USD 572.36 | USD 109,319.90 | USD -43,945.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 83.25% | USD 546.46 | USD 104,373.00 | USD -43,971.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 83.25% | USD 537.36 | USD 102,634.90 | USD -43,980.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 82.72% | USD 511.46 | USD 97,688.00 | USD -44,006.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 82.72% | USD 502.36 | USD 95,949.90 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 81.68% | USD 441.46 | USD 84,318.00 | USD -44,076.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 81.68% | USD 432.36 | USD 82,579.90 | USD -44,085.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 191/196 (5) | 35.08% (28.67–42.08%) | USD -58.71 | USD -11,213.60 | USD -4,413.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 191/196 (5) | 82.72% (76.73–87.42%) | USD 502.36 | USD 95,949.90 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 191/196 (5) | 17.28% (12.58–23.27%) | USD -913.33 | USD -174,445.10 | USD -7,350.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 191/196 (5) | 35.08% (28.67–42.08%) | USD -293.55 | USD -56,068.00 | USD -22,068.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -205,342.25 | USD -337,225.55 |
| -75% | 0/196 | 0.00% | USD -151,257.16 | USD -249,489.55 |
| -50% | 0/196 | 0.00% | USD -97,172.08 | USD -161,753.55 |
| -40% | 0/196 | 0.00% | USD -75,538.04 | USD -126,659.15 |
| -30% | 0/196 | 0.00% | USD -53,904.00 | USD -91,564.75 |
| -25% | 0/196 | 0.00% | USD -43,086.99 | USD -74,017.55 |
| -20% | 0/196 | 0.00% | USD -32,269.97 | USD -56,470.35 |
| -15% | 1/196 | 0.51% | USD -21,476.86 | USD -38,923.15 |
| -10% | 8/196 | 4.08% | USD -10,734.31 | USD -22,266.35 |
| -5% | 84/196 | 42.86% | USD -785.98 | USD -7,783.90 |
| 0% | 196/196 | 100.00% | USD 2,077.87 | USD 610.45 |
| 5% | 196/196 | 100.00% | USD 2,077.87 | USD 610.45 |
| 10% | 196/196 | 100.00% | USD 2,077.87 | USD 610.45 |
| 20% | 196/196 | 100.00% | USD 2,077.87 | USD 610.45 |

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