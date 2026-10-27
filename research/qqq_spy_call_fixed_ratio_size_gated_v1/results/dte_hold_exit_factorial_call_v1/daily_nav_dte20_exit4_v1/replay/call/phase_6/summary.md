# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 182.18 / USD 985.19; mean absolute mismatch USD 803.01; mean match score 18.98%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 156/196 | 92/64/0 | 58.97% (51.13–66.39%) | USD -268.72 | USD 189.40 | USD -41,919.60 | USD -8,794.10 | 40 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD 48.50 | USD -238.12 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 156 | 61.54% | USD -189.62 | USD -29,580.00 | USD -8,715.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 156 | 61.54% | USD -198.72 | USD -30,999.60 | USD -8,724.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 156 | 60.26% | USD -224.62 | USD -35,040.00 | USD -8,750.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 156 | 60.26% | USD -233.72 | USD -36,459.60 | USD -8,759.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 156 | 58.97% | USD -259.62 | USD -40,500.00 | USD -8,785.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 156 | 58.97% | USD -268.72 | USD -41,919.60 | USD -8,794.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 156 | 57.69% | USD -329.62 | USD -51,420.00 | USD -8,855.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 156 | 57.69% | USD -338.72 | USD -52,839.60 | USD -8,864.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 156/196 (40) | 32.05% (25.24–39.73%) | USD -13.79 | USD -2,150.60 | USD -573.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 156/196 (40) | 58.97% (51.13–66.39%) | USD -268.72 | USD -41,919.60 | USD -8,794.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 156/196 (40) | 33.33% (26.41–41.05%) | USD 172.21 | USD 26,865.40 | USD -2,609.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 156/196 (40) | 32.05% (25.24–39.73%) | USD -68.93 | USD -10,753.00 | USD -2,868.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -75% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -50% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -40% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -30% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -25% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -20% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -15% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -10% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -5% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| 0% | 196/196 | 100.00% | USD 736.56 | USD 86.45 |
| 5% | 18/196 | 9.18% | USD -4,752.51 | USD -11,328.75 |
| 10% | 2/196 | 1.02% | USD -15,434.34 | USD -28,875.95 |
| 20% | 0/196 | 0.00% | USD -37,020.44 | USD -63,970.35 |

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