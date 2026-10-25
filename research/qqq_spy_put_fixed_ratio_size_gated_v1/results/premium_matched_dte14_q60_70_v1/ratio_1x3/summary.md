# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 914.54 / USD 698.76; mean absolute mismatch USD 284.39; mean match score 71.25%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 203/188/0 | 51.92% (46.97–56.83%) | USD -25.83 | USD 11.80 | USD -10,099.20 | USD -7,533.20 | 1 |
| HOLD_10_SESSIONS | 49/392 | 26/23/0 | 53.06% (39.38–66.30%) | USD -548.55 | USD 74.80 | USD -26,878.80 | USD -14,625.20 | 343 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| HOLD_20_OR_DTE_LE_7 | 391/392 | 192/199/0 | 49.10% (44.18–54.04%) | USD -85.59 | USD -10.20 | USD -33,466.20 | USD -10,629.20 | 1 |
| EXIT_AT_DTE_LE_7 | 391/392 | 192/199/0 | 49.10% (44.18–54.04%) | USD -85.59 | USD -10.20 | USD -33,466.20 | USD -10,629.20 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -177.41 | USD 196.78 |
| HOLD_10_SESSIONS | USD 45.22 | USD -548.57 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -113.87 | USD 73.48 |
| EXIT_AT_DTE_LE_7 | USD -113.87 | USD 73.48 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 58.06% | USD 19.37 | USD 7,574.00 | USD -7,488.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 57.54% | USD 14.17 | USD 5,540.80 | USD -7,493.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 55.24% | USD -0.63 | USD -246.00 | USD -7,508.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 54.73% | USD -5.83 | USD -2,279.20 | USD -7,513.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 53.20% | USD -20.63 | USD -8,066.00 | USD -7,528.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 51.92% | USD -25.83 | USD -10,099.20 | USD -7,533.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 46.29% | USD -60.63 | USD -23,706.00 | USD -7,568.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 45.52% | USD -65.83 | USD -25,739.20 | USD -7,573.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 49 | 63.27% | USD -503.35 | USD -24,664.00 | USD -14,580.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 49 | 63.27% | USD -508.55 | USD -24,918.80 | USD -14,585.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 49 | 61.22% | USD -523.35 | USD -25,644.00 | USD -14,600.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 49 | 59.18% | USD -528.55 | USD -25,898.80 | USD -14,605.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 49 | 53.06% | USD -543.35 | USD -26,624.00 | USD -14,620.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 49 | 53.06% | USD -548.55 | USD -26,878.80 | USD -14,625.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 49 | 51.02% | USD -583.35 | USD -28,584.00 | USD -14,660.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 49 | 51.02% | USD -588.55 | USD -28,838.80 | USD -14,665.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 391 | 56.52% | USD -40.39 | USD -15,793.00 | USD -10,584.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 391 | 55.24% | USD -45.59 | USD -17,826.20 | USD -10,589.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 391 | 53.45% | USD -60.39 | USD -23,613.00 | USD -10,604.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 391 | 52.17% | USD -65.59 | USD -25,646.20 | USD -10,609.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 391 | 49.87% | USD -80.39 | USD -31,433.00 | USD -10,624.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 391 | 49.10% | USD -85.59 | USD -33,466.20 | USD -10,629.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 391 | 44.25% | USD -120.39 | USD -47,073.00 | USD -10,664.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 391 | 43.48% | USD -125.59 | USD -49,106.20 | USD -10,669.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 56.52% | USD -40.39 | USD -15,793.00 | USD -10,584.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 55.24% | USD -45.59 | USD -17,826.20 | USD -10,589.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 53.45% | USD -60.39 | USD -23,613.00 | USD -10,604.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 52.17% | USD -65.59 | USD -25,646.20 | USD -10,609.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 49.87% | USD -80.39 | USD -31,433.00 | USD -10,624.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 49.10% | USD -85.59 | USD -33,466.20 | USD -10,629.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 44.25% | USD -120.39 | USD -47,073.00 | USD -10,664.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 43.48% | USD -125.59 | USD -49,106.20 | USD -10,669.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 33.50% (29.01–38.32%) | USD -134.42 | USD -52,556.60 | USD -1,512.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 77.75% (73.37–81.59%) | USD 137.05 | USD 53,586.90 | USD -17,659.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 30.95% (26.57–35.70%) | USD -1,077.96 | USD -421,483.10 | USD -14,970.10 |
| HOLD_5_SESSIONS | 5 : 5 | 391/392 (1) | 33.50% (29.01–38.32%) | USD -672.08 | USD -262,783.00 | USD -7,563.00 |
| HOLD_10_SESSIONS | 1 : 1 | 49/392 (343) | 30.61% (19.52–44.53%) | USD -160.23 | USD -7,851.40 | USD -2,398.60 |
| HOLD_10_SESSIONS | 1 : 6 | 49/392 (343) | 81.63% (68.64–90.02%) | USD -1,131.02 | USD -55,419.90 | USD -32,965.10 |
| HOLD_10_SESSIONS | 6 : 1 | 49/392 (343) | 38.78% (26.43–52.75%) | USD 9.39 | USD 460.10 | USD -10,574.10 |
| HOLD_10_SESSIONS | 5 : 5 | 49/392 (343) | 30.61% (19.52–44.53%) | USD -801.16 | USD -39,257.00 | USD -11,993.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/392 (392) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 391/392 (1) | 31.97% (27.54–36.75%) | USD -111.98 | USD -43,783.60 | USD -1,452.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 391/392 (1) | 75.19% (70.68–79.21%) | USD -46.01 | USD -17,990.10 | USD -24,775.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 391/392 (1) | 31.46% (27.05–36.22%) | USD -737.84 | USD -288,495.10 | USD -16,429.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 391/392 (1) | 31.97% (27.54–36.75%) | USD -559.89 | USD -218,918.00 | USD -7,263.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 31.97% (27.54–36.75%) | USD -111.98 | USD -43,783.60 | USD -1,452.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 75.19% (70.68–79.21%) | USD -46.01 | USD -17,990.10 | USD -24,775.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 31.46% (27.05–36.22%) | USD -737.84 | USD -288,495.10 | USD -16,429.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 391/392 (1) | 31.97% (27.54–36.75%) | USD -559.89 | USD -218,918.00 | USD -7,263.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -88,111.99 | USD -139,115.60 |
| -75% | 0/392 | 0.00% | USD -65,270.01 | USD -103,409.10 |
| -50% | 0/392 | 0.00% | USD -42,428.03 | USD -67,702.60 |
| -40% | 0/392 | 0.00% | USD -33,291.24 | USD -53,515.40 |
| -30% | 0/392 | 0.00% | USD -24,154.45 | USD -39,450.70 |
| -25% | 0/392 | 0.00% | USD -19,586.06 | USD -32,418.35 |
| -20% | 0/392 | 0.00% | USD -15,017.66 | USD -25,386.00 |
| -15% | 2/392 | 0.51% | USD -10,449.27 | USD -18,353.65 |
| -10% | 5/392 | 1.28% | USD -5,888.94 | USD -11,321.30 |
| -5% | 68/392 | 17.35% | USD -1,400.09 | USD -4,576.10 |
| 0% | 336/392 | 85.71% | USD 423.71 | USD -331.60 |
| 5% | 54/392 | 13.78% | USD -213.48 | USD -990.60 |
| 10% | 48/392 | 12.24% | USD -235.34 | USD -990.60 |
| 20% | 48/392 | 12.24% | USD -238.39 | USD -990.60 |

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