# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 282.45 / USD 1,646.26; mean absolute mismatch USD 1,363.81; mean match score 17.12%.
- Actual selected contract ratios: {'1:6': 194}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 194; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 177/194 | 147/30/0 | 83.05% (76.84–87.86%) | USD 326.88 | USD 749.90 | USD 57,857.30 | USD -13,215.10 | 17 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD -100.97 | USD 506.95 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 177 | 83.62% | USD 405.98 | USD 71,858.00 | USD -13,136.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 177 | 83.62% | USD 396.88 | USD 70,247.30 | USD -13,145.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 177 | 83.05% | USD 370.98 | USD 65,663.00 | USD -13,171.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 177 | 83.05% | USD 361.88 | USD 64,052.30 | USD -13,180.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 177 | 83.05% | USD 335.98 | USD 59,468.00 | USD -13,206.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 177 | 83.05% | USD 326.88 | USD 57,857.30 | USD -13,215.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 177 | 83.05% | USD 265.98 | USD 47,078.00 | USD -13,276.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 177 | 83.05% | USD 256.88 | USD 45,467.30 | USD -13,285.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 177/194 (17) | 27.68% (21.62–34.70%) | USD -39.08 | USD -6,917.20 | USD -1,186.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 177/194 (17) | 83.05% (76.84–87.86%) | USD 326.88 | USD 57,857.30 | USD -13,215.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 177/194 (17) | 16.95% (12.14–23.16%) | USD -600.44 | USD -106,277.70 | USD -4,458.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 177/194 (17) | 27.68% (21.62–34.70%) | USD -195.40 | USD -34,586.00 | USD -5,933.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/194 | 0.00% | USD -208,345.93 | USD -337,313.55 |
| -75% | 0/194 | 0.00% | USD -154,416.87 | USD -250,702.30 |
| -50% | 0/194 | 0.00% | USD -100,487.82 | USD -164,091.05 |
| -40% | 0/194 | 0.00% | USD -78,916.20 | USD -129,446.55 |
| -30% | 0/194 | 0.00% | USD -57,344.58 | USD -94,802.05 |
| -25% | 0/194 | 0.00% | USD -46,558.77 | USD -77,479.80 |
| -20% | 0/194 | 0.00% | USD -35,772.96 | USD -60,157.55 |
| -15% | 1/194 | 0.52% | USD -25,007.23 | USD -42,835.30 |
| -10% | 2/194 | 1.03% | USD -14,279.94 | USD -26,227.85 |
| -5% | 34/194 | 17.53% | USD -3,699.01 | USD -11,765.55 |
| 0% | 194/194 | 100.00% | USD 1,317.29 | USD 182.45 |
| 5% | 194/194 | 100.00% | USD 1,324.26 | USD 182.45 |
| 10% | 194/194 | 100.00% | USD 1,324.26 | USD 182.45 |
| 20% | 194/194 | 100.00% | USD 1,324.26 | USD 182.45 |

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