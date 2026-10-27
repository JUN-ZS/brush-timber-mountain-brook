# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 285.75 / USD 1,699.29; mean absolute mismatch USD 1,413.54; mean match score 16.90%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 177/196 | 143/34/0 | 80.79% (74.36–85.92%) | USD 179.26 | USD 833.90 | USD 31,729.30 | USD -26,488.10 | 19 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD -87.03 | USD 345.39 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 177 | 81.36% | USD 258.36 | USD 45,730.00 | USD -26,409.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 177 | 81.36% | USD 249.26 | USD 44,119.30 | USD -26,418.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 177 | 81.36% | USD 223.36 | USD 39,535.00 | USD -26,444.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 177 | 81.36% | USD 214.26 | USD 37,924.30 | USD -26,453.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 177 | 80.79% | USD 188.36 | USD 33,340.00 | USD -26,479.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 177 | 80.79% | USD 179.26 | USD 31,729.30 | USD -26,488.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 177 | 80.23% | USD 118.36 | USD 20,950.00 | USD -26,549.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 177 | 80.23% | USD 109.26 | USD 19,339.30 | USD -26,558.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 177/196 (19) | 32.20% (25.76–39.40%) | USD -52.06 | USD -9,215.20 | USD -2,761.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 177/196 (19) | 80.79% (74.36–85.92%) | USD 179.26 | USD 31,729.30 | USD -26,488.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 177/196 (19) | 18.64% (13.59–25.03%) | USD -543.70 | USD -96,235.70 | USD -5,939.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 177/196 (19) | 32.20% (25.76–39.40%) | USD -260.32 | USD -46,076.00 | USD -13,808.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -208,677.77 | USD -337,894.55 |
| -75% | 0/196 | 0.00% | USD -154,770.06 | USD -250,973.80 |
| -50% | 0/196 | 0.00% | USD -100,862.36 | USD -165,169.05 |
| -40% | 0/196 | 0.00% | USD -79,299.28 | USD -130,847.15 |
| -30% | 0/196 | 0.00% | USD -57,736.19 | USD -96,525.25 |
| -25% | 0/196 | 0.00% | USD -46,954.65 | USD -79,364.30 |
| -20% | 0/196 | 0.00% | USD -36,173.11 | USD -62,203.35 |
| -15% | 1/196 | 0.51% | USD -25,391.63 | USD -45,042.40 |
| -10% | 1/196 | 0.51% | USD -14,645.63 | USD -27,881.45 |
| -5% | 21/196 | 10.71% | USD -3,973.56 | USD -11,079.05 |
| 0% | 196/196 | 100.00% | USD 1,364.21 | USD 275.45 |
| 5% | 196/196 | 100.00% | USD 1,373.99 | USD 275.45 |
| 10% | 196/196 | 100.00% | USD 1,373.99 | USD 275.45 |
| 20% | 196/196 | 100.00% | USD 1,373.99 | USD 275.45 |

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