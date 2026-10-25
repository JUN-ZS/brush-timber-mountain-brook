# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 98 checks; 98 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 453.93 / USD 2,658.43; mean absolute mismatch USD 2,204.50; mean match score 16.93%.
- Actual selected contract ratios: {'1:6': 98}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 98; entered cohorts: 98; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 96/98 | 80/16/0 | 83.33% (74.63–89.47%) | USD 658.74 | USD 1,402.90 | USD 63,239.40 | USD -44,015.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -183.72 | USD 921.56 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 96 | 84.38% | USD 737.84 | USD 70,833.00 | USD -43,936.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 96 | 84.38% | USD 728.74 | USD 69,959.40 | USD -43,945.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 96 | 84.38% | USD 702.84 | USD 67,473.00 | USD -43,971.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 96 | 84.38% | USD 693.74 | USD 66,599.40 | USD -43,980.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 96 | 83.33% | USD 667.84 | USD 64,113.00 | USD -44,006.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 96 | 83.33% | USD 658.74 | USD 63,239.40 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 96 | 82.29% | USD 597.84 | USD 57,393.00 | USD -44,076.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 96 | 82.29% | USD 588.74 | USD 56,519.40 | USD -44,085.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 96/98 (2) | 35.42% (26.58–45.38%) | USD -52.73 | USD -5,061.60 | USD -4,413.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 96/98 (2) | 83.33% (74.63–89.47%) | USD 658.74 | USD 63,239.40 | USD -44,015.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 96/98 (2) | 15.62% (9.70–24.19%) | USD -1,027.82 | USD -98,670.60 | USD -7,350.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 96/98 (2) | 35.42% (26.58–45.38%) | USD -263.62 | USD -25,308.00 | USD -22,068.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/98 | 0.00% | USD -206,000.87 | USD -337,225.55 |
| -75% | 0/98 | 0.00% | USD -151,828.32 | USD -249,489.55 |
| -50% | 0/98 | 0.00% | USD -97,655.78 | USD -161,753.55 |
| -40% | 0/98 | 0.00% | USD -75,986.76 | USD -126,659.15 |
| -30% | 0/98 | 0.00% | USD -54,317.74 | USD -91,564.75 |
| -25% | 0/98 | 0.00% | USD -43,483.24 | USD -74,017.55 |
| -20% | 0/98 | 0.00% | USD -32,648.73 | USD -56,470.35 |
| -15% | 0/98 | 0.00% | USD -21,814.22 | USD -38,923.15 |
| -10% | 4/98 | 4.08% | USD -10,982.43 | USD -22,266.35 |
| -5% | 40/98 | 40.82% | USD -907.30 | USD -7,526.90 |
| 0% | 98/98 | 100.00% | USD 2,164.95 | USD 683.45 |
| 5% | 98/98 | 100.00% | USD 2,164.95 | USD 683.45 |
| 10% | 98/98 | 100.00% | USD 2,164.95 | USD 683.45 |
| 20% | 98/98 | 100.00% | USD 2,164.95 | USD 683.45 |

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