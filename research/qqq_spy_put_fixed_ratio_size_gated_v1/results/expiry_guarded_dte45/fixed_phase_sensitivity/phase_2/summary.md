# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 460.95 / USD 1,359.01; mean absolute mismatch USD 898.06; mean match score 33.66%.
- Actual selected contract ratios: {'1:3': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 388/391 | 286/102/0 | 73.71% (69.11–77.84%) | USD 50.85 | USD 280.80 | USD 19,730.40 | USD -8,412.20 | 3 |
| HOLD_20_OR_DTE_LE_7 | 384/391 | 316/68/0 | 82.29% (78.16–85.78%) | USD 179.30 | USD 520.80 | USD 68,851.20 | USD -18,370.20 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -86.66 | USD 182.71 |
| HOLD_20_OR_DTE_LE_7 | USD -162.52 | USD 387.02 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 388 | 75.00% | USD 96.05 | USD 37,268.00 | USD -8,367.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 388 | 75.00% | USD 90.85 | USD 35,250.40 | USD -8,372.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 388 | 74.48% | USD 76.05 | USD 29,508.00 | USD -8,387.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 388 | 74.23% | USD 70.85 | USD 27,490.40 | USD -8,392.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 388 | 73.97% | USD 56.05 | USD 21,748.00 | USD -8,407.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 388 | 73.71% | USD 50.85 | USD 19,730.40 | USD -8,412.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 388 | 71.91% | USD 16.05 | USD 6,228.00 | USD -8,447.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 388 | 71.91% | USD 10.85 | USD 4,210.40 | USD -8,452.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 384 | 82.81% | USD 224.50 | USD 86,208.00 | USD -18,325.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 384 | 82.81% | USD 219.30 | USD 84,211.20 | USD -18,330.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 384 | 82.55% | USD 204.50 | USD 78,528.00 | USD -18,345.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 384 | 82.55% | USD 199.30 | USD 76,531.20 | USD -18,350.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 384 | 82.29% | USD 184.50 | USD 70,848.00 | USD -18,365.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 384 | 82.29% | USD 179.30 | USD 68,851.20 | USD -18,370.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 384 | 81.51% | USD 144.50 | USD 55,488.00 | USD -18,405.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 384 | 81.51% | USD 139.30 | USD 53,491.20 | USD -18,410.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 388/391 (3) | 34.79% (30.22–39.66%) | USD -48.36 | USD -18,762.80 | USD -1,623.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 388/391 (3) | 73.71% (69.11–77.84%) | USD 199.67 | USD 77,470.20 | USD -19,798.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 388/391 (3) | 22.94% (19.03–27.37%) | USD -538.17 | USD -208,809.80 | USD -6,942.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 388/391 (3) | 54.90% (49.92–59.78%) | USD -143.83 | USD -55,804.60 | USD -9,192.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 384/391 (7) | 38.02% (33.31–42.97%) | USD -56.11 | USD -21,546.40 | USD -4,193.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 384/391 (7) | 82.81% (78.72–86.26%) | USD 532.42 | USD 204,447.60 | USD -40,143.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 384/391 (7) | 15.36% (12.10–19.31%) | USD -925.19 | USD -355,272.40 | USD -8,979.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 384/391 (7) | 65.62% (60.74–70.20%) | USD -106.74 | USD -40,986.80 | USD -23,862.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -87,352.29 | USD -139,425.60 |
| -75% | 0/391 | 0.00% | USD -64,467.56 | USD -103,634.10 |
| -50% | 0/391 | 0.00% | USD -41,582.84 | USD -67,842.60 |
| -40% | 0/391 | 0.00% | USD -32,428.95 | USD -53,526.00 |
| -30% | 0/391 | 0.00% | USD -23,275.06 | USD -39,209.40 |
| -25% | 0/391 | 0.00% | USD -18,698.11 | USD -32,051.10 |
| -20% | 0/391 | 0.00% | USD -14,121.17 | USD -24,892.80 |
| -15% | 2/391 | 0.51% | USD -9,544.64 | USD -17,734.50 |
| -10% | 9/391 | 2.30% | USD -4,982.44 | USD -10,576.20 |
| -5% | 144/391 | 36.83% | USD -572.57 | USD -4,050.05 |
| 0% | 391/391 | 100.00% | USD 871.91 | USD 262.40 |
| 5% | 391/391 | 100.00% | USD 875.46 | USD 262.40 |
| 10% | 391/391 | 100.00% | USD 875.46 | USD 262.40 |
| 20% | 391/391 | 100.00% | USD 875.46 | USD 262.40 |

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
