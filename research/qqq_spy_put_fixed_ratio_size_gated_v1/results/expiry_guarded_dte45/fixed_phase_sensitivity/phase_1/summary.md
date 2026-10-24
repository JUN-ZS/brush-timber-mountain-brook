# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 438.18 / USD 1,290.00; mean absolute mismatch USD 851.82; mean match score 33.68%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 389/392 | 291/98/0 | 74.81% (70.26–78.86%) | USD 25.95 | USD 304.80 | USD 10,094.20 | USD -12,630.20 | 3 |
| HOLD_20_OR_DTE_LE_7 | 384/392 | 315/69/0 | 82.03% (77.88–85.55%) | USD 148.41 | USD 526.30 | USD 56,991.20 | USD -25,266.20 | 8 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -76.62 | USD 147.77 |
| HOLD_20_OR_DTE_LE_7 | USD -149.89 | USD 343.50 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 389 | 76.86% | USD 71.15 | USD 27,677.00 | USD -12,585.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 389 | 76.86% | USD 65.95 | USD 25,654.20 | USD -12,590.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 389 | 76.61% | USD 51.15 | USD 19,897.00 | USD -12,605.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 389 | 76.35% | USD 45.95 | USD 17,874.20 | USD -12,610.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 389 | 75.58% | USD 31.15 | USD 12,117.00 | USD -12,625.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 389 | 74.81% | USD 25.95 | USD 10,094.20 | USD -12,630.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 389 | 72.75% | USD -8.85 | USD -3,443.00 | USD -12,665.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 389 | 72.24% | USD -14.05 | USD -5,465.80 | USD -12,670.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 384 | 82.29% | USD 193.61 | USD 74,348.00 | USD -25,221.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 384 | 82.29% | USD 188.41 | USD 72,351.20 | USD -25,226.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 384 | 82.03% | USD 173.61 | USD 66,668.00 | USD -25,241.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 384 | 82.03% | USD 168.41 | USD 64,671.20 | USD -25,246.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 384 | 82.03% | USD 153.61 | USD 58,988.00 | USD -25,261.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 384 | 82.03% | USD 148.41 | USD 56,991.20 | USD -25,266.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 384 | 81.77% | USD 113.61 | USD 43,628.00 | USD -25,301.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 384 | 81.77% | USD 108.41 | USD 41,631.20 | USD -25,306.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 389/392 (3) | 30.59% (26.22–35.34%) | USD -49.97 | USD -19,436.40 | USD -3,033.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 389/392 (3) | 75.58% (71.07–79.58%) | USD 139.82 | USD 54,390.10 | USD -27,025.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 389/392 (3) | 21.08% (17.32–25.41%) | USD -489.58 | USD -190,444.90 | USD -7,310.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 389/392 (3) | 53.98% (49.02–58.87%) | USD -161.90 | USD -62,980.30 | USD -16,932.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 384/392 (8) | 36.46% (31.80–41.38%) | USD -57.99 | USD -22,266.40 | USD -5,223.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 384/392 (8) | 82.29% (78.16–85.78%) | USD 458.01 | USD 175,877.60 | USD -55,330.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 384/392 (8) | 17.45% (13.98–21.56%) | USD -863.91 | USD -331,742.40 | USD -7,350.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 384/392 (8) | 70.31% (65.56–74.66%) | USD -128.74 | USD -49,436.80 | USD -30,915.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -87,174.67 | USD -138,872.60 |
| -75% | 0/392 | 0.00% | USD -64,295.03 | USD -102,824.35 |
| -50% | 0/392 | 0.00% | USD -41,415.38 | USD -66,776.10 |
| -40% | 0/392 | 0.00% | USD -32,263.53 | USD -52,356.80 |
| -30% | 0/392 | 0.00% | USD -23,111.67 | USD -37,937.50 |
| -25% | 0/392 | 0.00% | USD -18,535.74 | USD -30,727.85 |
| -20% | 1/392 | 0.26% | USD -13,960.16 | USD -23,543.60 |
| -15% | 2/392 | 0.51% | USD -9,396.94 | USD -16,607.60 |
| -10% | 10/392 | 2.55% | USD -4,842.65 | USD -9,849.30 |
| -5% | 162/392 | 41.33% | USD -489.64 | USD -3,637.45 |
| 0% | 392/392 | 100.00% | USD 829.22 | USD 189.40 |
| 5% | 392/392 | 100.00% | USD 829.22 | USD 189.40 |
| 10% | 392/392 | 100.00% | USD 829.22 | USD 189.40 |
| 20% | 392/392 | 100.00% | USD 829.22 | USD 189.40 |

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
