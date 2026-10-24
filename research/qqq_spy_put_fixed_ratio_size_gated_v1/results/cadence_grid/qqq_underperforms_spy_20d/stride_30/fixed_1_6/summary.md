# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 518 checks; 50 qualified; 468 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 454.88 / USD 2,628.60; mean absolute mismatch USD 2,173.72; mean match score 17.05%.
- Actual selected contract ratios: {'1:6': 50}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 50; entered cohorts: 50; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 50/50 | 25/25/0 | 50.00% (36.64–63.36%) | USD -372.36 | USD 22.90 | USD -18,618.00 | USD -5,175.10 | 0 |
| HOLD_10_SESSIONS | 50/50 | 35/15/0 | 70.00% (56.25–80.90%) | USD -19.04 | USD 617.40 | USD -952.00 | USD -7,969.10 | 0 |
| HOLD_20_SESSIONS | 49/50 | 39/10/0 | 79.59% (66.36–88.52%) | USD 636.10 | USD 1,394.90 | USD 31,169.10 | USD -9,449.10 | 1 |
| EXIT_AT_DTE_LE_7 | 47/50 | 41/6/0 | 87.23% (74.83–94.02%) | USD 491.22 | USD 1,649.90 | USD 23,087.30 | USD -20,318.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 39.14 | USD -332.40 |
| HOLD_10_SESSIONS | USD -67.14 | USD 127.20 |
| HOLD_20_SESSIONS | USD -210.76 | USD 925.96 |
| EXIT_AT_DTE_LE_7 | USD -200.62 | USD 770.94 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 50 | 54.00% | USD -293.26 | USD -14,663.00 | USD -5,096.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 50 | 54.00% | USD -302.36 | USD -15,118.00 | USD -5,105.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 50 | 54.00% | USD -328.26 | USD -16,413.00 | USD -5,131.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 50 | 52.00% | USD -337.36 | USD -16,868.00 | USD -5,140.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 50 | 50.00% | USD -363.26 | USD -18,163.00 | USD -5,166.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 50 | 50.00% | USD -372.36 | USD -18,618.00 | USD -5,175.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 50 | 50.00% | USD -433.26 | USD -21,663.00 | USD -5,236.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 50 | 48.00% | USD -442.36 | USD -22,118.00 | USD -5,245.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 50 | 72.00% | USD 60.06 | USD 3,003.00 | USD -7,890.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 50 | 72.00% | USD 50.96 | USD 2,548.00 | USD -7,899.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 50 | 72.00% | USD 25.06 | USD 1,253.00 | USD -7,925.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 50 | 72.00% | USD 15.96 | USD 798.00 | USD -7,934.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 50 | 70.00% | USD -9.94 | USD -497.00 | USD -7,960.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 50 | 70.00% | USD -19.04 | USD -952.00 | USD -7,969.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 50 | 70.00% | USD -79.94 | USD -3,997.00 | USD -8,030.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 50 | 70.00% | USD -89.04 | USD -4,452.00 | USD -8,039.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 49 | 79.59% | USD 715.20 | USD 35,045.00 | USD -9,370.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 49 | 79.59% | USD 706.10 | USD 34,599.10 | USD -9,379.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 49 | 79.59% | USD 680.20 | USD 33,330.00 | USD -9,405.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 49 | 79.59% | USD 671.10 | USD 32,884.10 | USD -9,414.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 49 | 79.59% | USD 645.20 | USD 31,615.00 | USD -9,440.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 49 | 79.59% | USD 636.10 | USD 31,169.10 | USD -9,449.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 49 | 79.59% | USD 575.20 | USD 28,185.00 | USD -9,510.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 49 | 79.59% | USD 566.10 | USD 27,739.10 | USD -9,519.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 47 | 87.23% | USD 570.32 | USD 26,805.00 | USD -20,239.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 47 | 87.23% | USD 561.22 | USD 26,377.30 | USD -20,248.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 47 | 87.23% | USD 535.32 | USD 25,160.00 | USD -20,274.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 47 | 87.23% | USD 526.22 | USD 24,732.30 | USD -20,283.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 47 | 87.23% | USD 500.32 | USD 23,515.00 | USD -20,309.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 47 | 87.23% | USD 491.22 | USD 23,087.30 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 47 | 87.23% | USD 430.32 | USD 20,225.00 | USD -20,379.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 47 | 87.23% | USD 421.22 | USD 19,797.30 | USD -20,388.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 50/50 (0) | 36.00% (24.14–49.86%) | USD -38.86 | USD -1,943.00 | USD -433.60 |
| HOLD_5_SESSIONS | 1 : 6 | 50/50 (0) | 50.00% (36.64–63.36%) | USD -372.36 | USD -18,618.00 | USD -5,175.10 |
| HOLD_5_SESSIONS | 6 : 1 | 50/50 (0) | 34.00% (22.44–47.85%) | USD 100.34 | USD 5,017.00 | USD -2,020.10 |
| HOLD_5_SESSIONS | 4 : 5 | 50/50 (0) | 42.00% (29.38–55.77%) | USD -222.14 | USD -11,107.00 | USD -2,682.70 |
| HOLD_10_SESSIONS | 1 : 1 | 50/50 (0) | 28.00% (17.47–41.67%) | USD -68.54 | USD -3,427.00 | USD -595.60 |
| HOLD_10_SESSIONS | 1 : 6 | 50/50 (0) | 70.00% (56.25–80.90%) | USD -19.04 | USD -952.00 | USD -7,969.10 |
| HOLD_10_SESSIONS | 6 : 1 | 50/50 (0) | 26.00% (15.87–39.55%) | USD -460.74 | USD -23,037.00 | USD -3,228.10 |
| HOLD_10_SESSIONS | 4 : 5 | 50/50 (0) | 44.00% (31.16–57.69%) | USD -264.26 | USD -13,213.00 | USD -3,618.70 |
| HOLD_20_SESSIONS | 1 : 1 | 49/50 (1) | 24.49% (14.60–38.09%) | USD -79.03 | USD -3,872.40 | USD -590.60 |
| HOLD_20_SESSIONS | 1 : 6 | 49/50 (1) | 79.59% (66.36–88.52%) | USD 636.10 | USD 31,169.10 | USD -9,449.10 |
| HOLD_20_SESSIONS | 6 : 1 | 49/50 (1) | 16.33% (8.51–29.04%) | USD -1,189.30 | USD -58,275.90 | USD -3,733.10 |
| HOLD_20_SESSIONS | 4 : 5 | 49/50 (1) | 69.39% (55.47–80.48%) | USD -173.09 | USD -8,481.30 | USD -3,856.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 47/50 (3) | 29.79% (18.65–43.98%) | USD -94.73 | USD -4,452.20 | USD -1,279.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 47/50 (3) | 87.23% (74.83–94.02%) | USD 491.22 | USD 23,087.30 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 47/50 (3) | 10.64% (4.63–22.59%) | USD -1,154.31 | USD -54,252.70 | USD -3,792.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 47/50 (3) | 76.60% (62.78–86.40%) | USD -261.72 | USD -12,300.90 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/50 | 0.00% | USD -208,136.27 | USD -326,323.55 |
| -75% | 0/50 | 0.00% | USD -153,343.49 | USD -240,755.55 |
| -50% | 0/50 | 0.00% | USD -98,550.72 | USD -155,187.55 |
| -40% | 0/50 | 0.00% | USD -76,633.61 | USD -120,960.35 |
| -30% | 0/50 | 0.00% | USD -54,716.50 | USD -87,872.95 |
| -25% | 0/50 | 0.00% | USD -43,757.94 | USD -71,336.05 |
| -20% | 0/50 | 0.00% | USD -32,799.39 | USD -54,799.15 |
| -15% | 0/50 | 0.00% | USD -21,840.83 | USD -38,262.25 |
| -10% | 2/50 | 4.00% | USD -10,890.60 | USD -23,103.25 |
| -5% | 22/50 | 44.00% | USD -866.63 | USD -8,803.90 |
| 0% | 50/50 | 100.00% | USD 2,134.17 | USD 722.45 |
| 5% | 50/50 | 100.00% | USD 2,134.17 | USD 722.45 |
| 10% | 50/50 | 100.00% | USD 2,134.17 | USD 722.45 |
| 20% | 50/50 | 100.00% | USD 2,134.17 | USD 722.45 |

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