# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 278 checks; 278 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 17–23 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,115.81 / USD 1,691.31; mean absolute mismatch USD 593.06; mean match score 67.67%.
- Actual selected contract ratios: {'1:6': 277}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 277; entered cohorts: 277; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 276/277 | 203/73/0 | 73.55% (68.05–78.41%) | USD 14.46 | USD 295.90 | USD 3,990.40 | USD -18,649.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -149.36 | USD 242.91 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 276 | 76.45% | USD 93.56 | USD 25,822.00 | USD -18,570.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 276 | 76.09% | USD 84.46 | USD 23,310.40 | USD -18,579.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 276 | 74.64% | USD 58.56 | USD 16,162.00 | USD -18,605.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 276 | 74.64% | USD 49.46 | USD 13,650.40 | USD -18,614.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 276 | 73.91% | USD 23.56 | USD 6,502.00 | USD -18,640.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 276 | 73.55% | USD 14.46 | USD 3,990.40 | USD -18,649.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 276 | 71.01% | USD -46.44 | USD -12,818.00 | USD -18,710.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 276 | 69.93% | USD -55.54 | USD -15,329.60 | USD -18,719.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 276/277 (1) | 33.33% (28.03–39.09%) | USD -131.47 | USD -36,285.60 | USD -2,067.60 |
| HOLD_5_SESSIONS | 1 : 6 | 276/277 (1) | 73.55% (68.05–78.41%) | USD 14.46 | USD 3,990.40 | USD -18,649.10 |
| HOLD_5_SESSIONS | 6 : 1 | 276/277 (1) | 32.25% (27.01–37.97%) | USD -934.74 | USD -257,989.60 | USD -16,619.10 |
| HOLD_5_SESSIONS | 5 : 5 | 276/277 (1) | 33.33% (28.03–39.09%) | USD -657.35 | USD -181,428.00 | USD -10,338.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/277 | 0.00% | USD -207,688.68 | USD -339,376.55 |
| -75% | 0/277 | 0.00% | USD -153,685.19 | USD -252,162.30 |
| -50% | 0/277 | 0.00% | USD -99,681.70 | USD -164,948.05 |
| -40% | 0/277 | 0.00% | USD -78,080.30 | USD -130,062.35 |
| -30% | 0/277 | 0.00% | USD -56,478.91 | USD -95,176.65 |
| -25% | 0/277 | 0.00% | USD -45,678.21 | USD -77,733.80 |
| -20% | 0/277 | 0.00% | USD -34,877.51 | USD -60,290.95 |
| -15% | 0/277 | 0.00% | USD -24,076.81 | USD -42,848.10 |
| -10% | 4/277 | 1.44% | USD -13,283.00 | USD -25,405.25 |
| -5% | 62/277 | 22.38% | USD -2,700.11 | USD -9,600.20 |
| 0% | 276/277 | 99.64% | USD 1,363.99 | USD -84.55 |
| 5% | 255/277 | 92.06% | USD 581.14 | USD -364.55 |
| 10% | 255/277 | 92.06% | USD 538.29 | USD -364.55 |
| 20% | 255/277 | 92.06% | USD 535.95 | USD -364.55 |

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