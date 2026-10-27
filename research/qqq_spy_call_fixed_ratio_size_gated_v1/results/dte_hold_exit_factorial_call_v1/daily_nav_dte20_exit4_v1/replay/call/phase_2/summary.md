# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 161.74 / USD 869.75; mean absolute mismatch USD 708.01; mean match score 19.62%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 144/195 | 84/60/0 | 58.33% (50.17–66.07%) | USD -470.26 | USD 149.40 | USD -67,717.40 | USD -6,172.10 | 51 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD 69.51 | USD -460.67 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 144 | 61.81% | USD -391.16 | USD -56,327.00 | USD -6,093.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 144 | 61.81% | USD -400.26 | USD -57,637.40 | USD -6,102.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 144 | 61.11% | USD -426.16 | USD -61,367.00 | USD -6,128.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 144 | 59.03% | USD -435.26 | USD -62,677.40 | USD -6,137.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 144 | 59.03% | USD -461.16 | USD -66,407.00 | USD -6,163.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 144 | 58.33% | USD -470.26 | USD -67,717.40 | USD -6,172.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 144 | 55.56% | USD -531.16 | USD -76,487.00 | USD -6,233.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 144 | 54.86% | USD -540.26 | USD -77,797.40 | USD -6,242.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 144/195 (51) | 29.17% (22.36–37.05%) | USD -29.87 | USD -4,301.40 | USD -967.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 144/195 (51) | 58.33% (50.17–66.07%) | USD -470.26 | USD -67,717.40 | USD -6,172.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 144/195 (51) | 35.42% (28.08–43.51%) | USD 261.16 | USD 37,607.60 | USD -1,966.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 144/195 (51) | 29.17% (22.36–37.05%) | USD -149.35 | USD -21,507.00 | USD -4,838.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -75% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -50% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -40% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -30% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -25% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -20% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -15% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -10% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -5% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| 0% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| 5% | 29/195 | 14.87% | USD -4,437.86 | USD -12,415.05 |
| 10% | 1/195 | 0.51% | USD -15,038.47 | USD -29,223.55 |
| 20% | 1/195 | 0.51% | USD -36,587.85 | USD -62,840.55 |

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