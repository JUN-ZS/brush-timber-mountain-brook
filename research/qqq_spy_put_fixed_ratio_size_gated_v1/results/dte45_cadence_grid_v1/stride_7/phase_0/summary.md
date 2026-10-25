# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 280 checks; 280 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 436.37 / USD 2,566.22; mean absolute mismatch USD 2,129.85; mean match score 16.72%.
- Actual selected contract ratios: {'1:6': 280}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 280; entered cohorts: 280; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 276/280 | 226/50/0 | 81.88% (76.91–85.98%) | USD 524.02 | USD 1,384.40 | USD 144,630.40 | USD -39,635.10 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -158.53 | USD 761.65 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 276 | 81.88% | USD 603.12 | USD 166,462.00 | USD -39,556.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 276 | 81.88% | USD 594.02 | USD 163,950.40 | USD -39,565.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 276 | 81.88% | USD 568.12 | USD 156,802.00 | USD -39,591.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 276 | 81.88% | USD 559.02 | USD 154,290.40 | USD -39,600.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 276 | 81.88% | USD 533.12 | USD 147,142.00 | USD -39,626.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 276 | 81.88% | USD 524.02 | USD 144,630.40 | USD -39,635.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 276 | 81.16% | USD 463.12 | USD 127,822.00 | USD -39,696.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 276 | 81.16% | USD 454.02 | USD 125,310.40 | USD -39,705.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 276/280 (4) | 36.59% (31.13–42.42%) | USD -54.19 | USD -14,955.60 | USD -4,193.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 276/280 (4) | 81.88% (76.91–85.98%) | USD 524.02 | USD 144,630.40 | USD -39,635.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 276/280 (4) | 17.39% (13.38–22.30%) | USD -903.33 | USD -249,319.60 | USD -7,649.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 276/280 (4) | 36.59% (31.13–42.42%) | USD -270.93 | USD -74,778.00 | USD -20,968.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/280 | 0.00% | USD -204,827.33 | USD -336,022.55 |
| -75% | 0/280 | 0.00% | USD -150,921.46 | USD -248,902.05 |
| -50% | 0/280 | 0.00% | USD -97,015.59 | USD -161,964.55 |
| -40% | 0/280 | 0.00% | USD -75,453.24 | USD -127,189.55 |
| -30% | 0/280 | 0.00% | USD -53,890.89 | USD -92,414.55 |
| -25% | 0/280 | 0.00% | USD -43,109.72 | USD -75,027.05 |
| -20% | 2/280 | 0.71% | USD -32,329.52 | USD -57,639.55 |
| -15% | 3/280 | 1.07% | USD -21,599.51 | USD -40,252.05 |
| -10% | 9/280 | 3.21% | USD -10,900.86 | USD -23,103.25 |
| -5% | 116/280 | 41.43% | USD -814.97 | USD -8,803.90 |
| 0% | 280/280 | 100.00% | USD 2,090.30 | USD 610.45 |
| 5% | 280/280 | 100.00% | USD 2,090.30 | USD 610.45 |
| 10% | 280/280 | 100.00% | USD 2,090.30 | USD 610.45 |
| 20% | 280/280 | 100.00% | USD 2,090.30 | USD 610.45 |

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