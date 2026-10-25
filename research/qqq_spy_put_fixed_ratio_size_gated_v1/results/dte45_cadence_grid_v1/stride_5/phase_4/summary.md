# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 389 checks; 389 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.86 / USD 2,646.82; mean absolute mismatch USD 2,198.96; mean match score 16.79%.
- Actual selected contract ratios: {'1:6': 389}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 389; entered cohorts: 389; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 383/389 | 306/77/0 | 79.90% (75.59–83.60%) | USD 560.88 | USD 1,367.90 | USD 214,816.70 | USD -46,365.10 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -163.58 | USD 803.56 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 383 | 80.68% | USD 639.98 | USD 245,112.00 | USD -46,286.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 383 | 80.68% | USD 630.88 | USD 241,626.70 | USD -46,295.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 383 | 80.42% | USD 604.98 | USD 231,707.00 | USD -46,321.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 383 | 80.42% | USD 595.88 | USD 228,221.70 | USD -46,330.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 383 | 80.16% | USD 569.98 | USD 218,302.00 | USD -46,356.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 383 | 79.90% | USD 560.88 | USD 214,816.70 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 383 | 79.90% | USD 499.98 | USD 191,492.00 | USD -46,426.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 383 | 79.90% | USD 490.88 | USD 188,006.70 | USD -46,435.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 383/389 (6) | 38.38% (33.65–43.34%) | USD -52.26 | USD -20,013.80 | USD -4,038.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 383/389 (6) | 79.90% (75.59–83.60%) | USD 560.88 | USD 214,816.70 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 383/389 (6) | 17.23% (13.78–21.34%) | USD -926.67 | USD -354,913.30 | USD -5,355.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 383/389 (6) | 38.38% (33.65–43.34%) | USD -261.28 | USD -100,069.00 | USD -20,193.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/389 | 0.00% | USD -205,647.70 | USD -333,656.55 |
| -75% | 0/389 | 0.00% | USD -151,595.00 | USD -246,826.80 |
| -50% | 0/389 | 0.00% | USD -97,542.29 | USD -159,997.05 |
| -40% | 0/389 | 0.00% | USD -75,921.21 | USD -125,265.15 |
| -30% | 0/389 | 0.00% | USD -54,300.13 | USD -90,533.25 |
| -25% | 0/389 | 0.00% | USD -43,489.59 | USD -74,073.55 |
| -20% | 0/389 | 0.00% | USD -32,679.05 | USD -58,191.35 |
| -15% | 1/389 | 0.26% | USD -21,868.51 | USD -42,309.15 |
| -10% | 11/389 | 2.83% | USD -11,083.34 | USD -26,426.95 |
| -5% | 159/389 | 40.87% | USD -878.26 | USD -10,544.75 |
| 0% | 389/389 | 100.00% | USD 2,157.72 | USD 569.45 |
| 5% | 389/389 | 100.00% | USD 2,159.41 | USD 569.45 |
| 10% | 389/389 | 100.00% | USD 2,159.41 | USD 569.45 |
| 20% | 389/389 | 100.00% | USD 2,159.41 | USD 569.45 |

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