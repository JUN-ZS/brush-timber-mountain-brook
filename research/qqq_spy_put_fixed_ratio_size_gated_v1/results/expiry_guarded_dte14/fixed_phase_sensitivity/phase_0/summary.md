# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 235.82 / USD 701.09; mean absolute mismatch USD 465.27; mean match score 34.35%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 390/392 | 300/90/0 | 76.92% (72.49–80.83%) | USD -28.70 | USD 182.80 | USD -11,194.00 | USD -11,506.20 | 2 |
| HOLD_20_OR_DTE_LE_7 | 390/392 | 300/90/0 | 76.92% (72.49–80.83%) | USD -28.70 | USD 182.80 | USD -11,194.00 | USD -11,506.20 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -47.84 | USD 64.34 |
| HOLD_20_OR_DTE_LE_7 | USD -47.84 | USD 64.34 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 390 | 78.21% | USD 16.50 | USD 6,434.00 | USD -11,461.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 390 | 78.21% | USD 11.30 | USD 4,406.00 | USD -11,466.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 390 | 77.69% | USD -3.50 | USD -1,366.00 | USD -11,481.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 390 | 77.44% | USD -8.70 | USD -3,394.00 | USD -11,486.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 390 | 76.92% | USD -23.50 | USD -9,166.00 | USD -11,501.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 390 | 76.92% | USD -28.70 | USD -11,194.00 | USD -11,506.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 390 | 73.85% | USD -63.50 | USD -24,766.00 | USD -11,541.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 390 | 73.33% | USD -68.70 | USD -26,794.00 | USD -11,546.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 390 | 78.21% | USD 16.50 | USD 6,434.00 | USD -11,461.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 390 | 78.21% | USD 11.30 | USD 4,406.00 | USD -11,466.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 390 | 77.69% | USD -3.50 | USD -1,366.00 | USD -11,481.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 390 | 77.44% | USD -8.70 | USD -3,394.00 | USD -11,486.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 390 | 76.92% | USD -23.50 | USD -9,166.00 | USD -11,501.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 390 | 76.92% | USD -28.70 | USD -11,194.00 | USD -11,506.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 390 | 73.85% | USD -63.50 | USD -24,766.00 | USD -11,541.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 390 | 73.33% | USD -68.70 | USD -26,794.00 | USD -11,546.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 390/392 (2) | 32.05% (27.61–36.84%) | USD -48.99 | USD -19,108.00 | USD -2,075.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 390/392 (2) | 77.44% (73.03–81.31%) | USD 1.74 | USD 677.00 | USD -25,652.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 390/392 (2) | 19.49% (15.86–23.71%) | USD -344.70 | USD -134,433.00 | USD -4,465.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 390/392 (2) | 52.05% (47.10–56.97%) | USD -185.83 | USD -72,475.00 | USD -13,017.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 390/392 (2) | 32.05% (27.61–36.84%) | USD -48.99 | USD -19,108.00 | USD -2,075.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 390/392 (2) | 77.44% (73.03–81.31%) | USD 1.74 | USD 677.00 | USD -25,652.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 390/392 (2) | 19.49% (15.86–23.71%) | USD -344.70 | USD -134,433.00 | USD -4,465.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 390/392 (2) | 52.05% (47.10–56.97%) | USD -185.83 | USD -72,475.00 | USD -13,017.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -89,074.36 | USD -140,501.60 |
| -75% | 0/392 | 0.00% | USD -66,232.66 | USD -104,795.10 |
| -50% | 0/392 | 0.00% | USD -43,390.97 | USD -69,088.60 |
| -40% | 0/392 | 0.00% | USD -34,254.29 | USD -54,806.00 |
| -30% | 0/392 | 0.00% | USD -25,117.62 | USD -40,523.40 |
| -25% | 0/392 | 0.00% | USD -20,549.28 | USD -33,424.35 |
| -20% | 0/392 | 0.00% | USD -15,980.94 | USD -26,392.00 |
| -15% | 1/392 | 0.26% | USD -11,412.60 | USD -19,359.65 |
| -10% | 3/392 | 0.77% | USD -6,850.39 | USD -12,327.30 |
| -5% | 25/392 | 6.38% | USD -2,321.38 | USD -5,442.05 |
| 0% | 392/392 | 100.00% | USD 436.66 | USD 59.40 |
| 5% | 392/392 | 100.00% | USD 442.67 | USD 59.40 |
| 10% | 392/392 | 100.00% | USD 442.67 | USD 59.40 |
| 20% | 392/392 | 100.00% | USD 442.67 | USD 59.40 |

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
