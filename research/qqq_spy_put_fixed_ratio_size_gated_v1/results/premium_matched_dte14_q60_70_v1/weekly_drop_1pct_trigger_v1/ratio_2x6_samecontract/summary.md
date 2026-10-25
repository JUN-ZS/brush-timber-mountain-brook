# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_1pct — SPY rolling 5-session close return crosses from above -1% to <= -1%; no correlation gate; entry next observed common session.
- Filter evaluation: 1945 checks; 138 qualified; 1807 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 2,021.45 / USD 1,607.09; mean absolute mismatch USD 589.87; mean match score 73.20%.
- Actual selected contract ratios: {'2:6': 138}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 138; entered cohorts: 138; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 136/138 | 53/83/0 | 38.97% (31.18–47.36%) | USD -139.16 | USD -133.40 | USD -18,926.40 | USD -15,866.40 | 2 |
| HOLD_10_SESSIONS | 14/138 | 7/7/0 | 50.00% (26.80–73.20%) | USD 333.74 | USD 124.60 | USD 4,672.40 | USD -810.40 | 124 |
| HOLD_20_SESSIONS | 0/138 | 0/0/0 | — | — | — | — | — | 138 |
| HOLD_20_OR_DTE_LE_7 | 138/138 | 57/81/0 | 41.30% (33.43–49.65%) | USD -185.76 | USD -95.40 | USD -25,635.20 | USD -11,924.40 | 0 |
| EXIT_AT_DTE_LE_7 | 138/138 | 57/81/0 | 41.30% (33.43–49.65%) | USD -185.76 | USD -95.40 | USD -25,635.20 | USD -11,924.40 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -288.54 | USD 239.78 |
| HOLD_10_SESSIONS | USD -1,142.71 | USD 1,566.86 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -361.14 | USD 265.78 |
| EXIT_AT_DTE_LE_7 | USD -361.14 | USD 265.78 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 136 | 47.79% | USD -48.76 | USD -6,632.00 | USD -15,776.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 136 | 45.59% | USD -59.16 | USD -8,046.40 | USD -15,786.40 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 136 | 44.12% | USD -88.76 | USD -12,072.00 | USD -15,816.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 136 | 41.91% | USD -99.16 | USD -13,486.40 | USD -15,826.40 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 136 | 41.18% | USD -128.76 | USD -17,512.00 | USD -15,856.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 136 | 38.97% | USD -139.16 | USD -18,926.40 | USD -15,866.40 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 136 | 36.76% | USD -208.76 | USD -28,392.00 | USD -15,936.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 136 | 36.76% | USD -219.16 | USD -29,806.40 | USD -15,946.40 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 14 | 64.29% | USD 424.14 | USD 5,938.00 | USD -720.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 14 | 64.29% | USD 413.74 | USD 5,792.40 | USD -730.40 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 14 | 57.14% | USD 384.14 | USD 5,378.00 | USD -760.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 14 | 57.14% | USD 373.74 | USD 5,232.40 | USD -770.40 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 14 | 57.14% | USD 344.14 | USD 4,818.00 | USD -800.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 14 | 50.00% | USD 333.74 | USD 4,672.40 | USD -810.40 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 14 | 50.00% | USD 264.14 | USD 3,698.00 | USD -880.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 14 | 50.00% | USD 253.74 | USD 3,552.40 | USD -890.40 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 138 | 49.28% | USD -95.36 | USD -13,160.00 | USD -11,834.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 138 | 46.38% | USD -105.76 | USD -14,595.20 | USD -11,844.40 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 138 | 43.48% | USD -135.36 | USD -18,680.00 | USD -11,874.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 138 | 42.03% | USD -145.76 | USD -20,115.20 | USD -11,884.40 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 138 | 41.30% | USD -175.36 | USD -24,200.00 | USD -11,914.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 138 | 41.30% | USD -185.76 | USD -25,635.20 | USD -11,924.40 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 138 | 39.13% | USD -255.36 | USD -35,240.00 | USD -11,994.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 138 | 38.41% | USD -265.76 | USD -36,675.20 | USD -12,004.40 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 138 | 49.28% | USD -95.36 | USD -13,160.00 | USD -11,834.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 138 | 46.38% | USD -105.76 | USD -14,595.20 | USD -11,844.40 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 138 | 43.48% | USD -135.36 | USD -18,680.00 | USD -11,874.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 138 | 42.03% | USD -145.76 | USD -20,115.20 | USD -11,884.40 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 138 | 41.30% | USD -175.36 | USD -24,200.00 | USD -11,914.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 138 | 41.30% | USD -185.76 | USD -25,635.20 | USD -11,924.40 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 138 | 39.13% | USD -255.36 | USD -35,240.00 | USD -11,994.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 138 | 38.41% | USD -265.76 | USD -36,675.20 | USD -12,004.40 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 136/138 (2) | 33.82% (26.41–42.12%) | USD -126.91 | USD -17,259.60 | USD -1,519.60 |
| HOLD_5_SESSIONS | 1 : 6 | 136/138 (2) | 73.53% (65.54–80.22%) | USD 16.41 | USD 2,231.40 | USD -20,393.10 |
| HOLD_5_SESSIONS | 6 : 1 | 136/138 (2) | 33.82% (26.41–42.12%) | USD -904.77 | USD -123,048.60 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 136/138 (2) | 33.82% (26.41–42.12%) | USD -634.54 | USD -86,298.00 | USD -7,598.00 |
| HOLD_10_SESSIONS | 1 : 1 | 14/138 (124) | 21.43% (7.57–47.59%) | USD -332.81 | USD -4,659.40 | USD -987.60 |
| HOLD_10_SESSIONS | 1 : 6 | 14/138 (124) | 100.00% (78.47–100.00%) | USD 916.40 | USD 12,829.60 | USD 64.90 |
| HOLD_10_SESSIONS | 6 : 1 | 14/138 (124) | 14.29% (4.01–39.94%) | USD -3,246.10 | USD -45,445.40 | USD -10,574.10 |
| HOLD_10_SESSIONS | 5 : 5 | 14/138 (124) | 21.43% (7.57–47.59%) | USD -1,664.07 | USD -23,297.00 | USD -4,938.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/138 (138) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -158.88 | USD -21,924.80 | USD -1,312.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 138/138 (0) | 76.09% (68.33–82.44%) | USD 6.11 | USD 843.20 | USD -15,422.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 138/138 (0) | 31.88% (24.69–40.06%) | USD -1,118.24 | USD -154,316.80 | USD -16,269.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -794.38 | USD -109,624.00 | USD -6,563.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -158.88 | USD -21,924.80 | USD -1,312.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 138/138 (0) | 76.09% (68.33–82.44%) | USD 6.11 | USD 843.20 | USD -15,422.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 138/138 (0) | 31.88% (24.69–40.06%) | USD -1,118.24 | USD -154,316.80 | USD -16,269.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 138/138 (0) | 29.71% (22.72–37.80%) | USD -794.38 | USD -109,624.00 | USD -6,563.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/138 | 0.00% | USD -171,612.46 | USD -272,691.20 |
| -75% | 0/138 | 0.00% | USD -126,786.46 | USD -202,532.70 |
| -50% | 0/138 | 0.00% | USD -81,960.46 | USD -132,374.20 |
| -40% | 0/138 | 0.00% | USD -64,030.06 | USD -104,310.80 |
| -30% | 0/138 | 0.00% | USD -46,099.66 | USD -76,247.40 |
| -25% | 0/138 | 0.00% | USD -37,134.46 | USD -62,215.70 |
| -20% | 0/138 | 0.00% | USD -28,169.26 | USD -48,184.00 |
| -15% | 1/138 | 0.72% | USD -19,204.06 | USD -34,152.30 |
| -10% | 2/138 | 1.45% | USD -10,267.46 | USD -20,120.60 |
| -5% | 43/138 | 31.16% | USD -1,545.87 | USD -6,642.30 |
| 0% | 120/138 | 86.96% | USD 971.96 | USD -637.20 |
| 5% | 22/138 | 15.94% | USD -363.26 | USD -2,691.20 |
| 10% | 19/138 | 13.77% | USD -459.47 | USD -2,691.20 |
| 20% | 19/138 | 13.77% | USD -459.56 | USD -2,691.20 |

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