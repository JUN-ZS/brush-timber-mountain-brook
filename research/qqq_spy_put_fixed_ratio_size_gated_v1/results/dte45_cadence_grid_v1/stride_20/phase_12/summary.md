# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 98 checks; 98 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 454.34 / USD 2,707.71; mean absolute mismatch USD 2,253.38; mean match score 16.62%.
- Actual selected contract ratios: {'1:6': 98}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 98; entered cohorts: 98; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 96/98 | 84/12/0 | 87.50% (79.41–92.70%) | USD 335.54 | USD 1,264.90 | USD 32,211.40 | USD -51,761.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -151.11 | USD 565.75 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 96 | 87.50% | USD 414.64 | USD 39,805.00 | USD -51,682.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 96 | 87.50% | USD 405.54 | USD 38,931.40 | USD -51,691.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 96 | 87.50% | USD 379.64 | USD 36,445.00 | USD -51,717.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 96 | 87.50% | USD 370.54 | USD 35,571.40 | USD -51,726.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 96 | 87.50% | USD 344.64 | USD 33,085.00 | USD -51,752.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 96 | 87.50% | USD 335.54 | USD 32,211.40 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 96 | 87.50% | USD 274.64 | USD 26,365.00 | USD -51,822.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 96 | 87.50% | USD 265.54 | USD 25,491.40 | USD -51,831.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 96/98 (2) | 38.54% (29.43–48.54%) | USD -79.42 | USD -7,624.60 | USD -4,434.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 96/98 (2) | 87.50% (79.41–92.70%) | USD 335.54 | USD 32,211.40 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 96/98 (2) | 13.54% (8.09–21.80%) | USD -891.50 | USD -85,583.60 | USD -8,618.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 96/98 (2) | 38.54% (29.43–48.54%) | USD -397.11 | USD -38,123.00 | USD -22,173.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/98 | 0.00% | USD -206,088.38 | USD -336,601.55 |
| -75% | 0/98 | 0.00% | USD -151,967.58 | USD -249,385.05 |
| -50% | 0/98 | 0.00% | USD -97,846.77 | USD -162,168.55 |
| -40% | 0/98 | 0.00% | USD -76,198.45 | USD -127,281.95 |
| -30% | 0/98 | 0.00% | USD -54,550.13 | USD -92,395.35 |
| -25% | 0/98 | 0.00% | USD -43,725.97 | USD -74,952.05 |
| -20% | 0/98 | 0.00% | USD -32,901.81 | USD -57,508.75 |
| -15% | 0/98 | 0.00% | USD -22,077.65 | USD -40,065.45 |
| -10% | 2/98 | 2.04% | USD -11,274.61 | USD -22,622.15 |
| -5% | 39/98 | 39.80% | USD -949.10 | USD -7,103.95 |
| 0% | 98/98 | 100.00% | USD 2,217.60 | USD 722.45 |
| 5% | 98/98 | 100.00% | USD 2,213.83 | USD 722.45 |
| 10% | 98/98 | 100.00% | USD 2,213.83 | USD 722.45 |
| 20% | 98/98 | 100.00% | USD 2,213.83 | USD 722.45 |

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