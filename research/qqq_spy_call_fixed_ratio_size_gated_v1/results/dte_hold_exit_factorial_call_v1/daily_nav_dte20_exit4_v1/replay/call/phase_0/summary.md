# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 155.70 / USD 845.57; mean absolute mismatch USD 689.87; mean match score 19.24%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 152/196 | 93/59/0 | 61.18% (53.25–68.56%) | USD -318.51 | USD 207.40 | USD -48,413.20 | USD -7,125.10 | 44 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD 60.28 | USD -299.68 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 152 | 65.13% | USD -239.41 | USD -36,390.00 | USD -7,046.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 152 | 64.47% | USD -248.51 | USD -37,773.20 | USD -7,055.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 152 | 62.50% | USD -274.41 | USD -41,710.00 | USD -7,081.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 152 | 62.50% | USD -283.51 | USD -43,093.20 | USD -7,090.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 152 | 61.18% | USD -309.41 | USD -47,030.00 | USD -7,116.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 152 | 61.18% | USD -318.51 | USD -48,413.20 | USD -7,125.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 152 | 56.58% | USD -379.41 | USD -57,670.00 | USD -7,186.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 152 | 56.58% | USD -388.51 | USD -59,053.20 | USD -7,195.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 152/196 (44) | 29.61% (22.92–37.29%) | USD -12.27 | USD -1,865.20 | USD -918.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 152/196 (44) | 61.18% (53.25–68.56%) | USD -318.51 | USD -48,413.20 | USD -7,125.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 152/196 (44) | 32.89% (25.93–40.70%) | USD 232.61 | USD 35,356.80 | USD -1,786.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 152/196 (44) | 29.61% (22.92–37.29%) | USD -61.36 | USD -9,326.00 | USD -4,593.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -75% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -50% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -40% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -30% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -25% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -20% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -15% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -10% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| -5% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| 0% | 196/196 | 100.00% | USD 650.32 | USD 38.45 |
| 5% | 20/196 | 10.20% | USD -4,449.82 | USD -10,235.90 |
| 10% | 1/196 | 0.51% | USD -15,087.69 | USD -27,294.75 |
| 20% | 0/196 | 0.00% | USD -36,586.91 | USD -62,092.95 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short call can dominate downside even when QQQ long call appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.