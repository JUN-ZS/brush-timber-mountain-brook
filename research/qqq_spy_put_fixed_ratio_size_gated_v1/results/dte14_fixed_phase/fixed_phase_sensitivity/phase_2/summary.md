# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 250.27 / USD 713.80; mean absolute mismatch USD 464.08; mean match score 35.56%.
- Actual selected contract ratios: {'1:3': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 382/391 | 291/91/0 | 76.18% (71.66–80.18%) | USD 7.51 | USD 176.30 | USD 2,868.60 | USD -9,303.20 | 9 |
| HOLD_10_SESSIONS | 12/391 | 8/4/0 | 66.67% (39.06–86.19%) | USD -21.28 | USD 240.80 | USD -255.40 | USD -1,797.20 | 379 |
| HOLD_20_SESSIONS | 0/391 | 0/0/0 | — | — | — | — | — | 391 |
| EXIT_AT_DTE_LE_7 | 388/391 | 284/104/0 | 73.20% (68.58–77.36%) | USD -14.37 | USD 153.30 | USD -5,574.60 | USD -5,449.20 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -54.95 | USD 107.66 |
| HOLD_10_SESSIONS | USD -62.08 | USD 86.00 |
| HOLD_20_SESSIONS | — | — |
| EXIT_AT_DTE_LE_7 | USD -49.11 | USD 79.94 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 382 | 78.01% | USD 52.71 | USD 20,135.00 | USD -9,258.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 382 | 78.01% | USD 47.51 | USD 18,148.60 | USD -9,263.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 382 | 77.23% | USD 32.71 | USD 12,495.00 | USD -9,278.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 382 | 76.70% | USD 27.51 | USD 10,508.60 | USD -9,283.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 382 | 76.18% | USD 12.71 | USD 4,855.00 | USD -9,298.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 382 | 76.18% | USD 7.51 | USD 2,868.60 | USD -9,303.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 382 | 73.82% | USD -27.29 | USD -10,425.00 | USD -9,338.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 382 | 73.56% | USD -32.49 | USD -12,411.40 | USD -9,343.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 12 | 66.67% | USD 23.92 | USD 287.00 | USD -1,752.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 12 | 66.67% | USD 18.72 | USD 224.60 | USD -1,757.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 12 | 66.67% | USD 3.92 | USD 47.00 | USD -1,772.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 12 | 66.67% | USD -1.28 | USD -15.40 | USD -1,777.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 12 | 66.67% | USD -16.08 | USD -193.00 | USD -1,792.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 12 | 66.67% | USD -21.28 | USD -255.40 | USD -1,797.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 12 | 66.67% | USD -56.08 | USD -673.00 | USD -1,832.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 12 | 66.67% | USD -61.28 | USD -735.40 | USD -1,837.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 388 | 76.29% | USD 30.83 | USD 11,963.00 | USD -5,404.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 388 | 76.03% | USD 25.63 | USD 9,945.40 | USD -5,409.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 388 | 74.74% | USD 10.83 | USD 4,203.00 | USD -5,424.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 388 | 74.48% | USD 5.63 | USD 2,185.40 | USD -5,429.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 388 | 73.20% | USD -9.17 | USD -3,557.00 | USD -5,444.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 388 | 73.20% | USD -14.37 | USD -5,574.60 | USD -5,449.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 388 | 70.62% | USD -49.17 | USD -19,077.00 | USD -5,484.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 388 | 70.62% | USD -54.37 | USD -21,094.60 | USD -5,489.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 382/391 (9) | 28.53% (24.24–33.26%) | USD -41.67 | USD -15,916.20 | USD -1,074.60 |
| HOLD_5_SESSIONS | 1 : 6 | 382/391 (9) | 77.23% (72.76–81.15%) | USD 81.27 | USD 31,045.80 | USD -23,449.10 |
| HOLD_5_SESSIONS | 6 : 1 | 382/391 (9) | 17.80% (14.29–21.95%) | USD -372.93 | USD -142,459.20 | USD -5,895.10 |
| HOLD_5_SESSIONS | 4 : 5 | 382/391 (9) | 46.60% (41.65–51.61%) | USD -142.07 | USD -54,272.40 | USD -6,023.70 |
| HOLD_10_SESSIONS | 1 : 1 | 12/391 (379) | 41.67% (19.33–68.05%) | USD -56.02 | USD -672.20 | USD -422.60 |
| HOLD_10_SESSIONS | 1 : 6 | 12/391 (379) | 66.67% (39.06–86.19%) | USD 30.82 | USD 369.80 | USD -3,859.10 |
| HOLD_10_SESSIONS | 6 : 1 | 12/391 (379) | 16.67% (4.70–44.80%) | USD -422.93 | USD -5,075.20 | USD -1,104.10 |
| HOLD_10_SESSIONS | 4 : 5 | 12/391 (379) | 50.00% (25.38–74.62%) | USD -206.70 | USD -2,480.40 | USD -2,377.70 |
| HOLD_20_SESSIONS | 1 : 1 | 0/391 (391) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/391 (391) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/391 (391) | — | — | — | — |
| HOLD_20_SESSIONS | 4 : 5 | 0/391 (391) | — | — | — | — |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 388/391 (3) | 28.61% (24.34–33.30%) | USD -45.06 | USD -17,483.80 | USD -1,264.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 388/391 (3) | 74.48% (69.92–78.57%) | USD 31.67 | USD 12,289.20 | USD -12,146.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 388/391 (3) | 20.10% (16.42–24.38%) | USD -347.10 | USD -134,675.80 | USD -5,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 388/391 (3) | 45.36% (40.48–50.34%) | USD -164.90 | USD -63,980.60 | USD -6,170.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -89,275.04 | USD -141,478.60 |
| -75% | 0/391 | 0.00% | USD -66,390.53 | USD -105,687.10 |
| -50% | 0/391 | 0.00% | USD -43,506.02 | USD -69,895.60 |
| -40% | 0/391 | 0.00% | USD -34,352.21 | USD -55,579.00 |
| -30% | 0/391 | 0.00% | USD -25,198.40 | USD -41,262.40 |
| -25% | 0/391 | 0.00% | USD -20,621.50 | USD -34,104.10 |
| -20% | 0/391 | 0.00% | USD -16,044.60 | USD -26,945.80 |
| -15% | 0/391 | 0.00% | USD -11,467.70 | USD -19,794.40 |
| -10% | 3/391 | 0.77% | USD -6,896.21 | USD -12,755.80 |
| -5% | 27/391 | 6.91% | USD -2,360.12 | USD -5,814.05 |
| 0% | 389/391 | 99.49% | USD 420.24 | USD -130.60 |
| 5% | 389/391 | 99.49% | USD 440.99 | USD -130.60 |
| 10% | 389/391 | 99.49% | USD 440.93 | USD -130.60 |
| 20% | 389/391 | 99.49% | USD 440.93 | USD -130.60 |

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