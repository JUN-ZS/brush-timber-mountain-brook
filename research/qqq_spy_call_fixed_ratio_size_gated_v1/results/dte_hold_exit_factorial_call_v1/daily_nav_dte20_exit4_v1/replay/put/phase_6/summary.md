# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 266.63 / USD 1,541.17; mean absolute mismatch USD 1,274.54; mean match score 17.17%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 182/196 | 154/28/0 | 84.62% (78.66–89.14%) | USD 141.47 | USD 814.40 | USD 25,746.80 | USD -20,986.10 | 14 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD -87.41 | USD 307.98 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 182 | 84.62% | USD 220.57 | USD 40,143.00 | USD -20,907.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 182 | 84.62% | USD 211.47 | USD 38,486.80 | USD -20,916.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 182 | 84.62% | USD 185.57 | USD 33,773.00 | USD -20,942.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 182 | 84.62% | USD 176.47 | USD 32,116.80 | USD -20,951.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 182 | 84.62% | USD 150.57 | USD 27,403.00 | USD -20,977.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 182 | 84.62% | USD 141.47 | USD 25,746.80 | USD -20,986.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 182 | 83.52% | USD 80.57 | USD 14,663.00 | USD -21,047.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 182 | 83.52% | USD 71.47 | USD 13,006.80 | USD -21,056.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 182/196 (14) | 24.73% (19.02–31.47%) | USD -58.68 | USD -10,680.20 | USD -2,456.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 182/196 (14) | 84.62% (78.66–89.14%) | USD 141.47 | USD 25,746.80 | USD -20,986.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 182/196 (14) | 17.58% (12.74–23.77%) | USD -552.24 | USD -100,508.20 | USD -4,259.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 182/196 (14) | 24.73% (19.02–31.47%) | USD -293.41 | USD -53,401.00 | USD -12,283.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -208,873.76 | USD -341,657.55 |
| -75% | 0/196 | 0.00% | USD -154,767.12 | USD -253,921.55 |
| -50% | 0/196 | 0.00% | USD -100,660.48 | USD -166,591.05 |
| -40% | 0/196 | 0.00% | USD -79,017.82 | USD -131,705.35 |
| -30% | 0/196 | 0.00% | USD -57,375.16 | USD -96,819.65 |
| -25% | 0/196 | 0.00% | USD -46,553.84 | USD -79,376.80 |
| -20% | 0/196 | 0.00% | USD -35,732.51 | USD -61,933.95 |
| -15% | 1/196 | 0.51% | USD -24,922.33 | USD -44,491.10 |
| -10% | 3/196 | 1.53% | USD -14,189.01 | USD -27,048.25 |
| -5% | 36/196 | 18.37% | USD -3,687.73 | USD -10,572.90 |
| 0% | 196/196 | 100.00% | USD 1,235.60 | USD 221.45 |
| 5% | 196/196 | 100.00% | USD 1,234.99 | USD 221.45 |
| 10% | 196/196 | 100.00% | USD 1,234.99 | USD 221.45 |
| 20% | 196/196 | 100.00% | USD 1,234.99 | USD 221.45 |

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