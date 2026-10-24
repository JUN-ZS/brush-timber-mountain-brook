# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 450.08 / USD 1,333.19; mean absolute mismatch USD 883.12; mean match score 33.45%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 389/392 | 296/93/0 | 76.09% (71.61–80.06%) | USD 93.96 | USD 325.80 | USD 36,550.20 | USD -13,211.20 | 3 |
| HOLD_20_OR_DTE_LE_7 | 384/392 | 320/64/0 | 83.33% (79.28–86.73%) | USD 199.30 | USD 539.80 | USD 76,532.20 | USD -23,302.20 | 8 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -105.54 | USD 244.70 |
| HOLD_20_OR_DTE_LE_7 | USD -172.70 | USD 417.20 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 389 | 77.12% | USD 139.16 | USD 54,133.00 | USD -13,166.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 389 | 77.12% | USD 133.96 | USD 52,110.20 | USD -13,171.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 389 | 76.86% | USD 119.16 | USD 46,353.00 | USD -13,186.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 389 | 76.86% | USD 113.96 | USD 44,330.20 | USD -13,191.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 389 | 76.09% | USD 99.16 | USD 38,573.00 | USD -13,206.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 389 | 76.09% | USD 93.96 | USD 36,550.20 | USD -13,211.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 389 | 73.78% | USD 59.16 | USD 23,013.00 | USD -13,246.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 389 | 73.52% | USD 53.96 | USD 20,990.20 | USD -13,251.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 384 | 83.59% | USD 244.50 | USD 93,889.00 | USD -23,257.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 384 | 83.59% | USD 239.30 | USD 91,892.20 | USD -23,262.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 384 | 83.59% | USD 224.50 | USD 86,209.00 | USD -23,277.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 384 | 83.59% | USD 219.30 | USD 84,212.20 | USD -23,282.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 384 | 83.33% | USD 204.50 | USD 78,529.00 | USD -23,297.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 384 | 83.33% | USD 199.30 | USD 76,532.20 | USD -23,302.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 384 | 82.55% | USD 164.50 | USD 63,169.00 | USD -23,337.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 384 | 82.55% | USD 159.30 | USD 61,172.20 | USD -23,342.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 389/392 (3) | 37.28% (32.62–42.18%) | USD -46.58 | USD -18,118.40 | USD -2,810.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 389/392 (3) | 75.84% (71.34–79.82%) | USD 304.76 | USD 118,553.10 | USD -28,812.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 389/392 (3) | 21.08% (17.32–25.41%) | USD -630.80 | USD -245,381.90 | USD -7,173.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 389/392 (3) | 58.35% (53.40–63.15%) | USD -116.04 | USD -45,139.30 | USD -16,442.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 384/392 (8) | 41.67% (36.84–46.66%) | USD -56.23 | USD -21,593.40 | USD -4,269.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 384/392 (8) | 83.33% (79.28–86.73%) | USD 582.61 | USD 223,720.60 | USD -51,851.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 384/392 (8) | 15.62% (12.34–19.60%) | USD -976.24 | USD -374,874.40 | USD -7,649.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 384/392 (8) | 71.61% (66.91–75.89%) | USD -97.16 | USD -37,310.80 | USD -26,594.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -87,154.91 | USD -138,122.60 |
| -75% | 0/392 | 0.00% | USD -64,312.95 | USD -102,416.10 |
| -50% | 0/392 | 0.00% | USD -41,470.98 | USD -66,709.60 |
| -40% | 0/392 | 0.00% | USD -32,334.20 | USD -52,427.00 |
| -30% | 0/392 | 0.00% | USD -23,197.41 | USD -38,144.40 |
| -25% | 0/392 | 0.00% | USD -18,629.02 | USD -31,003.10 |
| -20% | 0/392 | 0.00% | USD -14,060.63 | USD -24,166.40 |
| -15% | 3/392 | 0.77% | USD -9,495.28 | USD -17,390.45 |
| -10% | 10/392 | 2.55% | USD -4,949.27 | USD -10,614.50 |
| -5% | 154/392 | 39.29% | USD -546.22 | USD -3,940.10 |
| 0% | 392/392 | 100.00% | USD 860.69 | USD 215.40 |
| 5% | 392/392 | 100.00% | USD 860.52 | USD 215.40 |
| 10% | 392/392 | 100.00% | USD 860.52 | USD 215.40 |
| 20% | 392/392 | 100.00% | USD 860.52 | USD 215.40 |

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
