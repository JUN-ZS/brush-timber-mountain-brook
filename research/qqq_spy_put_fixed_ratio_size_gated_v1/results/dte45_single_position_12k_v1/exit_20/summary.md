# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 89 checks; 89 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 422.84 / USD 2,489.60; mean absolute mismatch USD 2,066.75; mean match score 16.86%.
- Actual selected contract ratios: {'1:6': 89}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 89; entered cohorts: 89; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_SESSIONS | 86/89 | 68/18/0 | 79.07% (69.32–86.33%) | USD 256.12 | USD 1,288.40 | USD 22,026.40 | USD -25,585.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_SESSIONS | USD -79.27 | USD 414.49 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_SESSIONS | 0.000 | 0.00 | 86 | 79.07% | USD 335.22 | USD 28,829.00 | USD -25,506.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 86 | 79.07% | USD 326.12 | USD 28,046.40 | USD -25,515.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 86 | 79.07% | USD 300.22 | USD 25,819.00 | USD -25,541.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 86 | 79.07% | USD 291.12 | USD 25,036.40 | USD -25,550.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 86 | 79.07% | USD 265.22 | USD 22,809.00 | USD -25,576.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 86 | 79.07% | USD 256.12 | USD 22,026.40 | USD -25,585.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 86 | 79.07% | USD 195.22 | USD 16,789.00 | USD -25,646.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 86 | 79.07% | USD 186.12 | USD 16,006.40 | USD -25,655.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_SESSIONS | 1 : 1 | 86/89 (3) | 39.53% (29.86–50.10%) | USD -32.79 | USD -2,819.60 | USD -2,293.60 |
| HOLD_20_SESSIONS | 1 : 6 | 86/89 (3) | 79.07% (69.32–86.33%) | USD 256.12 | USD 22,026.40 | USD -25,585.10 |
| HOLD_20_SESSIONS | 6 : 1 | 86/89 (3) | 19.77% (12.72–29.40%) | USD -485.62 | USD -41,763.60 | USD -3,719.10 |
| HOLD_20_SESSIONS | 5 : 5 | 86/89 (3) | 39.53% (29.86–50.10%) | USD -163.93 | USD -14,098.00 | USD -11,468.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/89 | 0.00% | USD -204,511.81 | USD -334,060.55 |
| -75% | 0/89 | 0.00% | USD -150,615.93 | USD -247,449.30 |
| -50% | 0/89 | 0.00% | USD -96,720.06 | USD -160,838.05 |
| -40% | 0/89 | 0.00% | USD -75,161.71 | USD -126,193.55 |
| -30% | 0/89 | 0.00% | USD -53,603.36 | USD -91,549.05 |
| -25% | 0/89 | 0.00% | USD -42,824.19 | USD -74,226.80 |
| -20% | 0/89 | 0.00% | USD -32,045.01 | USD -56,904.55 |
| -15% | 1/89 | 1.12% | USD -21,266.90 | USD -39,582.30 |
| -10% | 3/89 | 3.37% | USD -10,583.63 | USD -22,260.05 |
| -5% | 42/89 | 47.19% | USD -570.82 | USD -7,107.25 |
| 0% | 89/89 | 100.00% | USD 2,027.20 | USD 635.45 |
| 5% | 89/89 | 100.00% | USD 2,027.20 | USD 635.45 |
| 10% | 89/89 | 100.00% | USD 2,027.20 | USD 635.45 |
| 20% | 89/89 | 100.00% | USD 2,027.20 | USD 635.45 |

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