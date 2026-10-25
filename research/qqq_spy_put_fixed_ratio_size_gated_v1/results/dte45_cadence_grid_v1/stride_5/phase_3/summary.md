# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.61 / USD 2,651.82; mean absolute mismatch USD 2,204.20; mean match score 16.69%.
- Actual selected contract ratios: {'1:6': 390}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 390; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 386/390 | 312/74/0 | 80.83% (76.61–84.44%) | USD 475.12 | USD 1,414.90 | USD 183,397.40 | USD -52,171.10 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -149.27 | USD 703.49 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 386 | 81.61% | USD 554.22 | USD 213,930.00 | USD -52,092.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 386 | 81.35% | USD 545.12 | USD 210,417.40 | USD -52,101.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 386 | 80.83% | USD 519.22 | USD 200,420.00 | USD -52,127.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 386 | 80.83% | USD 510.12 | USD 196,907.40 | USD -52,136.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 386 | 80.83% | USD 484.22 | USD 186,910.00 | USD -52,162.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 386 | 80.83% | USD 475.12 | USD 183,397.40 | USD -52,171.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 386 | 80.57% | USD 414.22 | USD 159,890.00 | USD -52,232.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 386 | 80.57% | USD 405.12 | USD 156,377.40 | USD -52,241.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 386/390 (4) | 35.75% (31.13–40.65%) | USD -54.62 | USD -21,083.60 | USD -4,434.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 386/390 (4) | 80.83% (76.61–84.44%) | USD 475.12 | USD 183,397.40 | USD -52,171.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 386/390 (4) | 15.80% (12.50–19.78%) | USD -857.47 | USD -330,982.60 | USD -10,258.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 386/390 (4) | 35.75% (31.13–40.65%) | USD -273.10 | USD -105,418.00 | USD -22,173.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/390 | 0.00% | USD -205,080.00 | USD -337,580.55 |
| -75% | 0/390 | 0.00% | USD -151,138.88 | USD -250,998.30 |
| -50% | 0/390 | 0.00% | USD -97,197.77 | USD -164,416.05 |
| -40% | 0/390 | 0.00% | USD -75,621.32 | USD -129,783.15 |
| -30% | 0/390 | 0.00% | USD -54,044.87 | USD -95,150.25 |
| -25% | 0/390 | 0.00% | USD -43,256.65 | USD -77,833.80 |
| -20% | 2/390 | 0.51% | USD -32,468.42 | USD -60,517.35 |
| -15% | 3/390 | 0.77% | USD -21,712.55 | USD -43,200.90 |
| -10% | 10/390 | 2.56% | USD -10,980.14 | USD -25,884.45 |
| -5% | 168/390 | 43.08% | USD -879.11 | USD -8,881.55 |
| 0% | 390/390 | 100.00% | USD 2,162.42 | USD 585.45 |
| 5% | 390/390 | 100.00% | USD 2,164.65 | USD 585.45 |
| 10% | 390/390 | 100.00% | USD 2,164.65 | USD 585.45 |
| 20% | 390/390 | 100.00% | USD 2,164.65 | USD 585.45 |

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