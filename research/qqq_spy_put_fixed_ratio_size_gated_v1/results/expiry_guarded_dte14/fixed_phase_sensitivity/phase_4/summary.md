# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 389 checks; 389 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 233.96 / USD 671.50; mean absolute mismatch USD 437.57; mean match score 35.36%.
- Actual selected contract ratios: {'1:3': 388}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 388; entered cohorts: 388; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 386/388 | 300/86/0 | 77.72% (73.31–81.59%) | USD -22.07 | USD 159.30 | USD -8,517.20 | USD -9,622.20 | 2 |
| HOLD_20_OR_DTE_LE_7 | 386/388 | 300/86/0 | 77.72% (73.31–81.59%) | USD -22.07 | USD 159.30 | USD -8,517.20 | USD -9,622.20 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -48.54 | USD 71.67 |
| HOLD_20_OR_DTE_LE_7 | USD -48.54 | USD 71.67 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 386 | 79.79% | USD 23.13 | USD 8,930.00 | USD -9,577.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 386 | 79.79% | USD 17.93 | USD 6,922.80 | USD -9,582.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 386 | 79.53% | USD 3.13 | USD 1,210.00 | USD -9,597.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 386 | 79.27% | USD -2.07 | USD -797.20 | USD -9,602.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 386 | 78.24% | USD -16.87 | USD -6,510.00 | USD -9,617.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 386 | 77.72% | USD -22.07 | USD -8,517.20 | USD -9,622.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 386 | 74.09% | USD -56.87 | USD -21,950.00 | USD -9,657.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 386 | 73.83% | USD -62.07 | USD -23,957.20 | USD -9,662.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 386 | 79.79% | USD 23.13 | USD 8,930.00 | USD -9,577.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 386 | 79.79% | USD 17.93 | USD 6,922.80 | USD -9,582.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 386 | 79.53% | USD 3.13 | USD 1,210.00 | USD -9,597.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 386 | 79.27% | USD -2.07 | USD -797.20 | USD -9,602.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 386 | 78.24% | USD -16.87 | USD -6,510.00 | USD -9,617.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 386 | 77.72% | USD -22.07 | USD -8,517.20 | USD -9,622.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 386 | 74.09% | USD -56.87 | USD -21,950.00 | USD -9,657.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 386 | 73.83% | USD -62.07 | USD -23,957.20 | USD -9,662.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 386/388 (2) | 25.91% (21.79–30.50%) | USD -47.25 | USD -18,237.60 | USD -2,229.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 386/388 (2) | 79.27% (74.95–83.02%) | USD 15.71 | USD 6,063.40 | USD -21,485.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 386/388 (2) | 19.43% (15.79–23.67%) | USD -346.44 | USD -133,726.60 | USD -4,928.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 386/388 (2) | 48.96% (44.01–53.94%) | USD -176.40 | USD -68,090.20 | USD -12,463.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 386/388 (2) | 25.91% (21.79–30.50%) | USD -47.25 | USD -18,237.60 | USD -2,229.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 386/388 (2) | 79.27% (74.95–83.02%) | USD 15.71 | USD 6,063.40 | USD -21,485.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 386/388 (2) | 19.43% (15.79–23.67%) | USD -346.44 | USD -133,726.60 | USD -4,928.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 386/388 (2) | 48.96% (44.01–53.94%) | USD -176.40 | USD -68,090.20 | USD -12,463.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/388 | 0.00% | USD -89,178.36 | USD -139,407.60 |
| -75% | 0/388 | 0.00% | USD -66,292.79 | USD -103,805.85 |
| -50% | 0/388 | 0.00% | USD -43,407.22 | USD -68,204.10 |
| -40% | 0/388 | 0.00% | USD -34,253.00 | USD -53,963.40 |
| -30% | 0/388 | 0.00% | USD -25,098.77 | USD -39,748.80 |
| -25% | 0/388 | 0.00% | USD -20,521.66 | USD -32,659.10 |
| -20% | 0/388 | 0.00% | USD -15,944.54 | USD -25,776.60 |
| -15% | 0/388 | 0.00% | USD -11,367.43 | USD -18,952.85 |
| -10% | 3/388 | 0.77% | USD -6,790.40 | USD -12,129.10 |
| -5% | 28/388 | 7.22% | USD -2,243.25 | USD -5,483.00 |
| 0% | 387/388 | 99.74% | USD 414.75 | USD -29.60 |
| 5% | 387/388 | 99.74% | USD 414.94 | USD -29.60 |
| 10% | 387/388 | 99.74% | USD 414.94 | USD -29.60 |
| 20% | 387/388 | 99.74% | USD 414.94 | USD -29.60 |

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

## Expiry-guarded exit contract

- Exit signal: planned 10/20 common-session holding limit OR remaining calendar DTE <= 7, whichever occurs first.
- A trigger is not a guaranteed fill. The replay still requires exact selected contracts, valid quotes and sufficient displayed exit-side size; failed closes defer and can remain unresolved at expiry/source end.
- Base engine SHA-256: 2037a21cb3c6b13a2965e08e516e3688f785dfa18d988a5640303b531f6ee40d; patched engine SHA-256: c689e002bb43440f0d7e5a2ad8208e16169984f124435875cd1d5dc4be63e2b6; runner SHA-256: 1ecebff5bb001c5c4441e447247aa99696055611c3634a514d0c5a4fabbe6e73.
