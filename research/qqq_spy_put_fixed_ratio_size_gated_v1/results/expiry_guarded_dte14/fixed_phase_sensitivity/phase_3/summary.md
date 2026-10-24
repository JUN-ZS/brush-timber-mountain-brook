# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 235.28 / USD 691.05; mean absolute mismatch USD 455.77; mean match score 34.76%.
- Actual selected contract ratios: {'1:3': 390}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 390; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 388/390 | 292/96/0 | 75.26% (70.73–79.29%) | USD 20.33 | USD 159.30 | USD 7,888.40 | USD -9,164.20 | 2 |
| HOLD_20_OR_DTE_LE_7 | 388/390 | 292/96/0 | 75.26% (70.73–79.29%) | USD 20.33 | USD 159.30 | USD 7,888.40 | USD -9,164.20 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -49.71 | USD 115.24 |
| HOLD_20_OR_DTE_LE_7 | USD -49.71 | USD 115.24 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 388 | 78.35% | USD 65.53 | USD 25,426.00 | USD -9,119.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 388 | 78.35% | USD 60.33 | USD 23,408.40 | USD -9,124.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 388 | 77.58% | USD 45.53 | USD 17,666.00 | USD -9,139.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 388 | 77.06% | USD 40.33 | USD 15,648.40 | USD -9,144.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 388 | 75.52% | USD 25.53 | USD 9,906.00 | USD -9,159.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 388 | 75.26% | USD 20.33 | USD 7,888.40 | USD -9,164.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 388 | 73.45% | USD -14.47 | USD -5,614.00 | USD -9,199.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 388 | 71.65% | USD -19.67 | USD -7,631.60 | USD -9,204.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 388 | 78.35% | USD 65.53 | USD 25,426.00 | USD -9,119.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 388 | 78.35% | USD 60.33 | USD 23,408.40 | USD -9,124.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 388 | 77.58% | USD 45.53 | USD 17,666.00 | USD -9,139.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 388 | 77.06% | USD 40.33 | USD 15,648.40 | USD -9,144.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 388 | 75.52% | USD 25.53 | USD 9,906.00 | USD -9,159.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 388 | 75.26% | USD 20.33 | USD 7,888.40 | USD -9,164.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 388 | 73.45% | USD -14.47 | USD -5,614.00 | USD -9,199.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 388 | 71.65% | USD -19.67 | USD -7,631.60 | USD -9,204.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 388/390 (2) | 29.38% (25.07–34.10%) | USD -33.90 | USD -13,152.80 | USD -934.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 388/390 (2) | 77.06% (72.63–80.97%) | USD 101.68 | USD 39,450.20 | USD -21,657.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 388/390 (2) | 21.65% (17.84–26.01%) | USD -338.97 | USD -131,519.80 | USD -8,103.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 388/390 (2) | 46.65% (41.74–51.62%) | USD -108.48 | USD -42,090.60 | USD -7,506.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 388/390 (2) | 29.38% (25.07–34.10%) | USD -33.90 | USD -13,152.80 | USD -934.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 388/390 (2) | 77.06% (72.63–80.97%) | USD 101.68 | USD 39,450.20 | USD -21,657.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 388/390 (2) | 21.65% (17.84–26.01%) | USD -338.97 | USD -131,519.80 | USD -8,103.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 388/390 (2) | 46.65% (41.74–51.62%) | USD -108.48 | USD -42,090.60 | USD -7,506.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/390 | 0.00% | USD -89,009.78 | USD -140,218.60 |
| -75% | 0/390 | 0.00% | USD -66,167.18 | USD -104,627.60 |
| -50% | 0/390 | 0.00% | USD -43,324.58 | USD -69,036.60 |
| -40% | 0/390 | 0.00% | USD -34,187.54 | USD -54,800.20 |
| -30% | 0/390 | 0.00% | USD -25,050.50 | USD -40,837.40 |
| -25% | 0/390 | 0.00% | USD -20,481.98 | USD -33,989.60 |
| -20% | 0/390 | 0.00% | USD -15,913.46 | USD -27,141.80 |
| -15% | 2/390 | 0.51% | USD -11,345.22 | USD -20,294.00 |
| -10% | 3/390 | 0.77% | USD -6,794.21 | USD -13,446.20 |
| -5% | 38/390 | 9.74% | USD -2,269.29 | USD -6,598.40 |
| 0% | 390/390 | 100.00% | USD 411.34 | USD 27.40 |
| 5% | 390/390 | 100.00% | USD 433.17 | USD 27.40 |
| 10% | 390/390 | 100.00% | USD 433.17 | USD 27.40 |
| 20% | 390/390 | 100.00% | USD 433.17 | USD 27.40 |

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
