# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 278 checks; 278 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 460.46 / USD 2,755.83; mean absolute mismatch USD 2,295.37; mean match score 16.70%.
- Actual selected contract ratios: {'1:6': 278}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 278; entered cohorts: 278; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 273/278 | 229/44/0 | 83.88% (79.06–87.77%) | USD 532.07 | USD 1,417.90 | USD 145,255.70 | USD -44,015.10 | 5 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -169.58 | USD 780.75 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 273 | 84.25% | USD 611.17 | USD 166,850.00 | USD -43,936.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 273 | 84.25% | USD 602.07 | USD 164,365.70 | USD -43,945.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 273 | 84.25% | USD 576.17 | USD 157,295.00 | USD -43,971.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 273 | 84.25% | USD 567.07 | USD 154,810.70 | USD -43,980.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 273 | 84.25% | USD 541.17 | USD 147,740.00 | USD -44,006.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 273 | 83.88% | USD 532.07 | USD 145,255.70 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 273 | 83.15% | USD 471.17 | USD 128,630.00 | USD -44,076.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 273 | 83.15% | USD 462.07 | USD 126,145.70 | USD -44,085.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 273/278 (5) | 41.03% (35.35–46.95%) | USD -62.05 | USD -16,939.80 | USD -4,413.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 273/278 (5) | 83.88% (79.06–87.77%) | USD 532.07 | USD 145,255.70 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 273/278 (5) | 14.65% (10.95–19.34%) | USD -966.43 | USD -263,834.30 | USD -7,645.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 273/278 (5) | 41.03% (35.35–46.95%) | USD -310.25 | USD -84,699.00 | USD -22,068.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/278 | 0.00% | USD -205,497.87 | USD -336,601.55 |
| -75% | 0/278 | 0.00% | USD -151,550.25 | USD -249,385.05 |
| -50% | 0/278 | 0.00% | USD -97,602.63 | USD -162,168.55 |
| -40% | 0/278 | 0.00% | USD -76,023.58 | USD -127,281.95 |
| -30% | 0/278 | 0.00% | USD -54,444.53 | USD -92,395.35 |
| -25% | 0/278 | 0.00% | USD -43,655.01 | USD -74,952.05 |
| -20% | 0/278 | 0.00% | USD -32,865.48 | USD -57,508.75 |
| -15% | 0/278 | 0.00% | USD -22,075.96 | USD -40,096.80 |
| -10% | 5/278 | 1.80% | USD -11,288.36 | USD -24,397.65 |
| -5% | 116/278 | 41.73% | USD -891.49 | USD -8,987.60 |
| 0% | 278/278 | 100.00% | USD 2,256.07 | USD 569.45 |
| 5% | 278/278 | 100.00% | USD 2,255.82 | USD 569.45 |
| 10% | 278/278 | 100.00% | USD 2,255.82 | USD 569.45 |
| 20% | 278/278 | 100.00% | USD 2,255.82 | USD 569.45 |

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