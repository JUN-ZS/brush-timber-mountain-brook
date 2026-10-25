# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 129 checks; 129 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 475.78 / USD 2,786.88; mean absolute mismatch USD 2,311.11; mean match score 17.16%.
- Actual selected contract ratios: {'1:6': 129}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 129; entered cohorts: 129; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 127/129 | 106/21/0 | 83.46% (76.04–88.92%) | USD 667.14 | USD 1,412.90 | USD 84,726.30 | USD -51,761.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -199.64 | USD 945.87 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 127 | 83.46% | USD 746.24 | USD 94,772.00 | USD -51,682.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 127 | 83.46% | USD 737.14 | USD 93,616.30 | USD -51,691.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 127 | 83.46% | USD 711.24 | USD 90,327.00 | USD -51,717.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 127 | 83.46% | USD 702.14 | USD 89,171.30 | USD -51,726.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 127 | 83.46% | USD 676.24 | USD 85,882.00 | USD -51,752.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 127 | 83.46% | USD 667.14 | USD 84,726.30 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 127 | 82.68% | USD 606.24 | USD 76,992.00 | USD -51,822.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 127 | 82.68% | USD 597.14 | USD 75,836.30 | USD -51,831.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 127/129 (2) | 35.43% (27.65–44.07%) | USD -64.59 | USD -8,203.20 | USD -4,434.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 127/129 (2) | 83.46% (76.04–88.92%) | USD 667.14 | USD 84,726.30 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 127/129 (2) | 14.17% (9.16–21.29%) | USD -1,119.28 | USD -142,148.70 | USD -8,979.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 127/129 (2) | 35.43% (27.65–44.07%) | USD -322.96 | USD -41,016.00 | USD -22,173.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/129 | 0.00% | USD -205,680.33 | USD -333,892.55 |
| -75% | 0/129 | 0.00% | USD -151,642.85 | USD -246,865.30 |
| -50% | 0/129 | 0.00% | USD -97,605.38 | USD -159,838.05 |
| -40% | 0/129 | 0.00% | USD -75,990.38 | USD -125,027.15 |
| -30% | 0/129 | 0.00% | USD -54,375.39 | USD -90,221.65 |
| -25% | 0/129 | 0.00% | USD -43,567.90 | USD -73,447.80 |
| -20% | 0/129 | 0.00% | USD -32,760.40 | USD -56,673.95 |
| -15% | 1/129 | 0.78% | USD -21,952.34 | USD -39,900.10 |
| -10% | 2/129 | 1.55% | USD -11,178.80 | USD -24,273.35 |
| -5% | 54/129 | 41.86% | USD -907.53 | USD -8,775.95 |
| 0% | 129/129 | 100.00% | USD 2,240.97 | USD 726.45 |
| 5% | 129/129 | 100.00% | USD 2,271.56 | USD 726.45 |
| 10% | 129/129 | 100.00% | USD 2,271.56 | USD 726.45 |
| 20% | 129/129 | 100.00% | USD 2,271.56 | USD 726.45 |

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