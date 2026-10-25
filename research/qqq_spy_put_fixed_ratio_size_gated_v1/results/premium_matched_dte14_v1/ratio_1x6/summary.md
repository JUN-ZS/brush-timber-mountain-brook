# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,396.76 / USD 1,402.76; mean absolute mismatch USD 346.32; mean match score 80.13%.
- Actual selected contract ratios: {'1:6': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 265/126/0 | 67.77% (62.99–72.21%) | USD 110.56 | USD 265.90 | USD 43,228.90 | USD -17,572.10 | 1 |
| HOLD_10_SESSIONS | 63/392 | 50/13/0 | 79.37% (67.83–87.52%) | USD -818.81 | USD 310.90 | USD -51,585.30 | USD -32,887.10 | 329 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| HOLD_20_OR_DTE_LE_7 | 391/392 | 260/131/0 | 66.50% (61.68–70.99%) | USD -92.58 | USD 192.90 | USD -36,197.10 | USD -26,657.10 | 1 |
| EXIT_AT_DTE_LE_7 | 391/392 | 260/131/0 | 66.50% (61.68–70.99%) | USD -92.58 | USD 192.90 | USD -36,197.10 | USD -26,657.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -219.15 | USD 408.81 |
| HOLD_10_SESSIONS | USD -106.57 | USD -633.14 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -152.27 | USD 138.80 |
| EXIT_AT_DTE_LE_7 | USD -152.27 | USD 138.80 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 74.42% | USD 189.66 | USD 74,157.00 | USD -17,493.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 74.17% | USD 180.56 | USD 70,598.90 | USD -17,502.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 72.12% | USD 154.66 | USD 60,472.00 | USD -17,528.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 71.61% | USD 145.56 | USD 56,913.90 | USD -17,537.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 69.31% | USD 119.66 | USD 46,787.00 | USD -17,563.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 67.77% | USD 110.56 | USD 43,228.90 | USD -17,572.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 64.45% | USD 49.66 | USD 19,417.00 | USD -17,633.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 63.68% | USD 40.56 | USD 15,858.90 | USD -17,642.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 63 | 85.71% | USD -739.71 | USD -46,602.00 | USD -32,808.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 63 | 85.71% | USD -748.81 | USD -47,175.30 | USD -32,817.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 63 | 82.54% | USD -774.71 | USD -48,807.00 | USD -32,843.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 63 | 82.54% | USD -783.81 | USD -49,380.30 | USD -32,852.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 63 | 79.37% | USD -809.71 | USD -51,012.00 | USD -32,878.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 63 | 79.37% | USD -818.81 | USD -51,585.30 | USD -32,887.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 63 | 79.37% | USD -879.71 | USD -55,422.00 | USD -32,948.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 63 | 77.78% | USD -888.81 | USD -55,995.30 | USD -32,957.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 391 | 72.89% | USD -13.48 | USD -5,269.00 | USD -26,578.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 391 | 72.38% | USD -22.58 | USD -8,827.10 | USD -26,587.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 391 | 71.36% | USD -48.48 | USD -18,954.00 | USD -26,613.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 391 | 70.59% | USD -57.58 | USD -22,512.10 | USD -26,622.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 391 | 67.77% | USD -83.48 | USD -32,639.00 | USD -26,648.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 391 | 66.50% | USD -92.58 | USD -36,197.10 | USD -26,657.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 391 | 60.36% | USD -153.48 | USD -60,009.00 | USD -26,718.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 391 | 60.36% | USD -162.58 | USD -63,567.10 | USD -26,727.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 72.89% | USD -13.48 | USD -5,269.00 | USD -26,578.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 72.38% | USD -22.58 | USD -8,827.10 | USD -26,587.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 71.36% | USD -48.48 | USD -18,954.00 | USD -26,613.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 70.59% | USD -57.58 | USD -22,512.10 | USD -26,622.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 67.77% | USD -83.48 | USD -32,639.00 | USD -26,648.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 66.50% | USD -92.58 | USD -36,197.10 | USD -26,657.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 60.36% | USD -153.48 | USD -60,009.00 | USD -26,718.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 60.36% | USD -162.58 | USD -63,567.10 | USD -26,727.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 35.04% (30.48–39.89%) | USD -173.62 | USD -67,884.60 | USD -2,398.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 67.77% (62.99–72.21%) | USD 110.56 | USD 43,228.90 | USD -17,572.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 33.50% (29.01–38.32%) | USD -1,325.89 | USD -518,421.10 | USD -16,560.10 |
| HOLD_5_SESSIONS | 5 : 5 | 391/392 (1) | 35.04% (30.48–39.89%) | USD -868.09 | USD -339,423.00 | USD -11,993.00 |
| HOLD_10_SESSIONS | 1 : 1 | 63/392 (329) | 33.33% (22.95–45.63%) | USD -234.70 | USD -14,785.80 | USD -2,320.60 |
| HOLD_10_SESSIONS | 1 : 6 | 63/392 (329) | 79.37% (67.83–87.52%) | USD -818.81 | USD -51,585.30 | USD -32,887.10 |
| HOLD_10_SESSIONS | 6 : 1 | 63/392 (329) | 34.92% (24.33–47.25%) | USD -824.05 | USD -51,915.30 | USD -12,137.10 |
| HOLD_10_SESSIONS | 5 : 5 | 63/392 (329) | 33.33% (22.95–45.63%) | USD -1,173.48 | USD -73,929.00 | USD -11,603.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/392 (392) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 391/392 (1) | 36.32% (31.70–41.20%) | USD -151.74 | USD -59,330.60 | USD -2,199.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 391/392 (1) | 66.50% (61.68–70.99%) | USD -92.58 | USD -36,197.10 | USD -26,657.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 391/392 (1) | 34.53% (29.99–39.37%) | USD -969.61 | USD -379,117.10 | USD -19,207.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 391/392 (1) | 36.32% (31.70–41.20%) | USD -758.70 | USD -296,653.00 | USD -10,998.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 36.32% (31.70–41.20%) | USD -151.74 | USD -59,330.60 | USD -2,199.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 66.50% (61.68–70.99%) | USD -92.58 | USD -36,197.10 | USD -26,657.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 34.53% (29.99–39.37%) | USD -969.61 | USD -379,117.10 | USD -19,207.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 391/392 (1) | 36.32% (31.70–41.20%) | USD -758.70 | USD -296,653.00 | USD -10,998.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -208,843.30 | USD -340,594.55 |
| -75% | 0/392 | 0.00% | USD -154,911.94 | USD -253,358.55 |
| -50% | 0/392 | 0.00% | USD -100,980.59 | USD -166,122.55 |
| -40% | 0/392 | 0.00% | USD -79,408.04 | USD -131,337.15 |
| -30% | 0/392 | 0.00% | USD -57,835.50 | USD -97,015.25 |
| -25% | 0/392 | 0.00% | USD -47,049.23 | USD -79,854.30 |
| -20% | 0/392 | 0.00% | USD -36,262.96 | USD -62,693.35 |
| -15% | 1/392 | 0.26% | USD -25,476.69 | USD -45,532.40 |
| -10% | 3/392 | 0.77% | USD -14,706.55 | USD -28,371.45 |
| -5% | 49/392 | 12.50% | USD -4,074.79 | USD -11,684.60 |
| 0% | 391/392 | 99.74% | USD 1,229.05 | USD -28.55 |
| 5% | 144/392 | 36.73% | USD 150.02 | USD -942.55 |
| 10% | 118/392 | 30.10% | USD -0.82 | USD -942.55 |
| 20% | 115/392 | 29.34% | USD -27.93 | USD -942.55 |

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