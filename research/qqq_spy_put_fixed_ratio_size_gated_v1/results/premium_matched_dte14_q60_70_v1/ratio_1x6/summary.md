# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 916.12 / USD 1,399.79; mean absolute mismatch USD 507.41; mean match score 69.29%.
- Actual selected contract ratios: {'1:6': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 390/392 | 303/87/0 | 77.69% (73.30–81.54%) | USD 144.98 | USD 326.40 | USD 56,542.00 | USD -17,659.10 | 2 |
| HOLD_10_SESSIONS | 49/392 | 40/9/0 | 81.63% (68.64–90.02%) | USD -1,131.02 | USD 427.90 | USD -55,419.90 | USD -32,965.10 | 343 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| HOLD_20_OR_DTE_LE_7 | 391/392 | 295/96/0 | 75.45% (70.95–79.45%) | USD -42.89 | USD 286.90 | USD -16,768.10 | USD -26,768.10 | 1 |
| EXIT_AT_DTE_LE_7 | 391/392 | 295/96/0 | 75.45% (70.95–79.45%) | USD -42.89 | USD 286.90 | USD -16,768.10 | USD -26,768.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -180.40 | USD 404.48 |
| HOLD_10_SESSIONS | USD 45.22 | USD -1,097.14 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -117.48 | USD 153.70 |
| EXIT_AT_DTE_LE_7 | USD -117.48 | USD 153.70 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 390 | 83.08% | USD 224.08 | USD 87,391.00 | USD -17,580.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 390 | 82.82% | USD 214.98 | USD 83,842.00 | USD -17,589.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 390 | 81.54% | USD 189.08 | USD 73,741.00 | USD -17,615.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 390 | 80.77% | USD 179.98 | USD 70,192.00 | USD -17,624.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 390 | 78.46% | USD 154.08 | USD 60,091.00 | USD -17,650.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 390 | 77.69% | USD 144.98 | USD 56,542.00 | USD -17,659.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 390 | 73.33% | USD 84.08 | USD 32,791.00 | USD -17,720.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 390 | 72.82% | USD 74.98 | USD 29,242.00 | USD -17,729.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 49 | 81.63% | USD -1,051.92 | USD -51,544.00 | USD -32,886.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 49 | 81.63% | USD -1,061.02 | USD -51,989.90 | USD -32,895.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 49 | 81.63% | USD -1,086.92 | USD -53,259.00 | USD -32,921.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 49 | 81.63% | USD -1,096.02 | USD -53,704.90 | USD -32,930.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 49 | 81.63% | USD -1,121.92 | USD -54,974.00 | USD -32,956.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 49 | 81.63% | USD -1,131.02 | USD -55,419.90 | USD -32,965.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 49 | 81.63% | USD -1,191.92 | USD -58,404.00 | USD -33,026.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 49 | 81.63% | USD -1,201.02 | USD -58,849.90 | USD -33,035.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 391 | 80.56% | USD 36.21 | USD 14,160.00 | USD -26,689.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 391 | 80.31% | USD 27.11 | USD 10,601.90 | USD -26,698.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 391 | 78.77% | USD 1.21 | USD 475.00 | USD -26,724.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 391 | 78.77% | USD -7.89 | USD -3,083.10 | USD -26,733.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 391 | 76.98% | USD -33.79 | USD -13,210.00 | USD -26,759.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 391 | 75.45% | USD -42.89 | USD -16,768.10 | USD -26,768.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 391 | 70.08% | USD -103.79 | USD -40,580.00 | USD -26,829.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 391 | 69.31% | USD -112.89 | USD -44,138.10 | USD -26,838.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 80.56% | USD 36.21 | USD 14,160.00 | USD -26,689.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 80.31% | USD 27.11 | USD 10,601.90 | USD -26,698.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 78.77% | USD 1.21 | USD 475.00 | USD -26,724.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 78.77% | USD -7.89 | USD -3,083.10 | USD -26,733.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 76.98% | USD -33.79 | USD -13,210.00 | USD -26,759.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 75.45% | USD -42.89 | USD -16,768.10 | USD -26,768.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 70.08% | USD -103.79 | USD -40,580.00 | USD -26,829.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 69.31% | USD -112.89 | USD -44,138.10 | USD -26,838.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 390/392 (2) | 33.33% (28.84–38.15%) | USD -135.58 | USD -52,878.00 | USD -1,512.60 |
| HOLD_5_SESSIONS | 1 : 6 | 390/392 (2) | 77.69% (73.30–81.54%) | USD 144.98 | USD 56,542.00 | USD -17,659.10 |
| HOLD_5_SESSIONS | 6 : 1 | 390/392 (2) | 31.03% (26.64–35.78%) | USD -1,094.07 | USD -426,688.00 | USD -14,970.10 |
| HOLD_5_SESSIONS | 5 : 5 | 390/392 (2) | 33.33% (28.84–38.15%) | USD -677.92 | USD -264,390.00 | USD -7,563.00 |
| HOLD_10_SESSIONS | 1 : 1 | 49/392 (343) | 30.61% (19.52–44.53%) | USD -160.23 | USD -7,851.40 | USD -2,398.60 |
| HOLD_10_SESSIONS | 1 : 6 | 49/392 (343) | 81.63% (68.64–90.02%) | USD -1,131.02 | USD -55,419.90 | USD -32,965.10 |
| HOLD_10_SESSIONS | 6 : 1 | 49/392 (343) | 38.78% (26.43–52.75%) | USD 9.39 | USD 460.10 | USD -10,574.10 |
| HOLD_10_SESSIONS | 5 : 5 | 49/392 (343) | 30.61% (19.52–44.53%) | USD -801.16 | USD -39,257.00 | USD -11,993.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/392 (392) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 391/392 (1) | 31.71% (27.30–36.49%) | USD -114.47 | USD -44,756.60 | USD -1,706.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 391/392 (1) | 75.45% (70.95–79.45%) | USD -42.89 | USD -16,768.10 | USD -26,768.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 391/392 (1) | 31.20% (26.81–35.96%) | USD -758.38 | USD -296,528.10 | USD -16,429.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 391/392 (1) | 31.71% (27.30–36.49%) | USD -572.34 | USD -223,783.00 | USD -8,533.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 31.71% (27.30–36.49%) | USD -114.47 | USD -44,756.60 | USD -1,706.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 75.45% (70.95–79.45%) | USD -42.89 | USD -16,768.10 | USD -26,768.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 31.20% (26.81–35.96%) | USD -758.38 | USD -296,528.10 | USD -16,429.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 391/392 (1) | 31.71% (27.30–36.49%) | USD -572.34 | USD -223,783.00 | USD -8,533.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -208,966.97 | USD -340,798.55 |
| -75% | 0/392 | 0.00% | USD -155,034.91 | USD -253,562.55 |
| -50% | 0/392 | 0.00% | USD -101,102.84 | USD -166,326.55 |
| -40% | 0/392 | 0.00% | USD -79,530.01 | USD -131,432.15 |
| -30% | 0/392 | 0.00% | USD -57,957.18 | USD -97,098.25 |
| -25% | 0/392 | 0.00% | USD -47,170.77 | USD -79,937.30 |
| -20% | 0/392 | 0.00% | USD -36,384.36 | USD -62,776.35 |
| -15% | 1/392 | 0.26% | USD -25,597.94 | USD -45,615.40 |
| -10% | 3/392 | 0.77% | USD -14,827.66 | USD -28,454.45 |
| -5% | 44/392 | 11.22% | USD -4,200.36 | USD -11,699.60 |
| 0% | 388/392 | 98.98% | USD 1,099.31 | USD -60.55 |
| 5% | 332/392 | 84.69% | USD 469.03 | USD -285.55 |
| 10% | 332/392 | 84.69% | USD 447.17 | USD -285.55 |
| 20% | 332/392 | 84.69% | USD 444.12 | USD -285.55 |

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