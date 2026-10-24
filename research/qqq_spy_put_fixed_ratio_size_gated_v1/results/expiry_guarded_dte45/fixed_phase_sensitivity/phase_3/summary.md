# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.61 / USD 1,325.85; mean absolute mismatch USD 878.24; mean match score 33.37%.
- Actual selected contract ratios: {'1:3': 390}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 390; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 388/390 | 293/95/0 | 75.52% (71.00–79.53%) | USD 72.90 | USD 313.30 | USD 28,283.40 | USD -10,501.20 | 2 |
| HOLD_20_OR_DTE_LE_7 | 386/390 | 316/70/0 | 81.87% (77.71–85.39%) | USD 178.33 | USD 531.30 | USD 68,834.80 | USD -21,325.20 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -84.64 | USD 202.74 |
| HOLD_20_OR_DTE_LE_7 | USD -154.93 | USD 378.46 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 388 | 76.80% | USD 118.10 | USD 45,821.00 | USD -10,456.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 388 | 76.55% | USD 112.90 | USD 43,803.40 | USD -10,461.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 388 | 76.03% | USD 98.10 | USD 38,061.00 | USD -10,476.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 388 | 75.77% | USD 92.90 | USD 36,043.40 | USD -10,481.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 388 | 75.52% | USD 78.10 | USD 30,301.00 | USD -10,496.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 388 | 75.52% | USD 72.90 | USD 28,283.40 | USD -10,501.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 388 | 73.45% | USD 38.10 | USD 14,781.00 | USD -10,536.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 388 | 73.20% | USD 32.90 | USD 12,763.40 | USD -10,541.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 386 | 82.38% | USD 223.53 | USD 86,282.00 | USD -21,280.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 386 | 82.12% | USD 218.33 | USD 84,274.80 | USD -21,285.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 386 | 82.12% | USD 203.53 | USD 78,562.00 | USD -21,300.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 386 | 82.12% | USD 198.33 | USD 76,554.80 | USD -21,305.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 386 | 81.87% | USD 183.53 | USD 70,842.00 | USD -21,320.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 386 | 81.87% | USD 178.33 | USD 68,834.80 | USD -21,325.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 386 | 81.35% | USD 143.53 | USD 55,402.00 | USD -21,360.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 386 | 81.35% | USD 138.33 | USD 53,394.80 | USD -21,365.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 388/390 (2) | 32.73% (28.25–37.55%) | USD -39.66 | USD -15,389.80 | USD -2,062.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 388/390 (2) | 76.55% (72.08–80.49%) | USD 241.74 | USD 93,793.20 | USD -23,159.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 388/390 (2) | 23.71% (19.75–28.19%) | USD -519.39 | USD -201,521.80 | USD -7,189.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 388/390 (2) | 57.73% (52.76–62.55%) | USD -102.38 | USD -39,722.60 | USD -12,469.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 386/390 (4) | 35.49% (30.88–40.39%) | USD -51.38 | USD -19,831.60 | USD -4,028.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 386/390 (4) | 80.83% (76.61–84.44%) | USD 522.89 | USD 201,834.40 | USD -47,270.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 386/390 (4) | 15.80% (12.50–19.78%) | USD -882.53 | USD -340,655.60 | USD -10,258.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 386/390 (4) | 70.47% (65.73–74.80%) | USD -90.66 | USD -34,993.20 | USD -24,762.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/390 | 0.00% | USD -87,099.02 | USD -138,393.60 |
| -75% | 0/390 | 0.00% | USD -64,253.39 | USD -102,965.85 |
| -50% | 0/390 | 0.00% | USD -41,407.77 | USD -67,538.10 |
| -40% | 0/390 | 0.00% | USD -32,269.52 | USD -53,367.00 |
| -30% | 0/390 | 0.00% | USD -23,131.27 | USD -39,195.90 |
| -25% | 0/390 | 0.00% | USD -18,562.15 | USD -32,110.35 |
| -20% | 2/390 | 0.51% | USD -13,993.02 | USD -25,024.80 |
| -15% | 3/390 | 0.77% | USD -9,439.55 | USD -17,939.25 |
| -10% | 10/390 | 2.56% | USD -4,893.44 | USD -10,853.70 |
| -5% | 159/390 | 40.77% | USD -543.11 | USD -3,922.85 |
| 0% | 390/390 | 100.00% | USD 854.73 | USD 221.40 |
| 5% | 390/390 | 100.00% | USD 855.64 | USD 221.40 |
| 10% | 390/390 | 100.00% | USD 855.64 | USD 221.40 |
| 20% | 390/390 | 100.00% | USD 855.64 | USD 221.40 |

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
