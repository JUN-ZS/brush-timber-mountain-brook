# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 518 checks; 50 qualified; 468 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 910.36 / USD 1,760.56; mean absolute mismatch USD 850.20; mean match score 51.02%.
- Actual selected contract ratios: {'2:4': 50}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 50; entered cohorts: 50; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 50/50 | 25/25/0 | 50.00% (36.64–63.36%) | USD -191.92 | USD 17.20 | USD -9,596.00 | USD -2,763.80 | 0 |
| HOLD_10_SESSIONS | 50/50 | 32/18/0 | 64.00% (50.14–75.86%) | USD -107.60 | USD 153.20 | USD -5,380.00 | USD -3,663.80 | 0 |
| HOLD_20_SESSIONS | 49/50 | 40/9/0 | 81.63% (68.64–90.02%) | USD 125.87 | USD 512.20 | USD 6,167.80 | USD -4,607.80 | 1 |
| EXIT_AT_DTE_LE_7 | 47/50 | 41/6/0 | 87.23% (74.83–94.02%) | USD 41.99 | USD 590.20 | USD 1,973.40 | USD -9,633.80 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 60.36 | USD -184.48 |
| HOLD_10_SESSIONS | USD -137.24 | USD 97.44 |
| HOLD_20_SESSIONS | USD -419.39 | USD 613.06 |
| EXIT_AT_DTE_LE_7 | USD -396.17 | USD 505.96 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 50 | 52.00% | USD -124.12 | USD -6,206.00 | USD -2,696.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 50 | 52.00% | USD -131.92 | USD -6,596.00 | USD -2,703.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 50 | 52.00% | USD -154.12 | USD -7,706.00 | USD -2,726.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 50 | 52.00% | USD -161.92 | USD -8,096.00 | USD -2,733.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 50 | 50.00% | USD -184.12 | USD -9,206.00 | USD -2,756.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 50 | 50.00% | USD -191.92 | USD -9,596.00 | USD -2,763.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 50 | 50.00% | USD -244.12 | USD -12,206.00 | USD -2,816.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 50 | 50.00% | USD -251.92 | USD -12,596.00 | USD -2,823.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 50 | 68.00% | USD -39.80 | USD -1,990.00 | USD -3,596.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 50 | 68.00% | USD -47.60 | USD -2,380.00 | USD -3,603.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 50 | 66.00% | USD -69.80 | USD -3,490.00 | USD -3,626.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 50 | 66.00% | USD -77.60 | USD -3,880.00 | USD -3,633.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 50 | 64.00% | USD -99.80 | USD -4,990.00 | USD -3,656.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 50 | 64.00% | USD -107.60 | USD -5,380.00 | USD -3,663.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 50 | 62.00% | USD -159.80 | USD -7,990.00 | USD -3,716.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 50 | 62.00% | USD -167.60 | USD -8,380.00 | USD -3,723.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 49 | 81.63% | USD 193.67 | USD 9,490.00 | USD -4,540.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 49 | 81.63% | USD 185.87 | USD 9,107.80 | USD -4,547.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 49 | 81.63% | USD 163.67 | USD 8,020.00 | USD -4,570.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 49 | 81.63% | USD 155.87 | USD 7,637.80 | USD -4,577.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 49 | 81.63% | USD 133.67 | USD 6,550.00 | USD -4,600.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 49 | 81.63% | USD 125.87 | USD 6,167.80 | USD -4,607.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 49 | 81.63% | USD 73.67 | USD 3,610.00 | USD -4,660.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 49 | 81.63% | USD 65.87 | USD 3,227.80 | USD -4,667.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 47 | 87.23% | USD 109.79 | USD 5,160.00 | USD -9,566.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 47 | 87.23% | USD 101.99 | USD 4,793.40 | USD -9,573.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 47 | 87.23% | USD 79.79 | USD 3,750.00 | USD -9,596.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 47 | 87.23% | USD 71.99 | USD 3,383.40 | USD -9,603.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 47 | 87.23% | USD 49.79 | USD 2,340.00 | USD -9,626.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 47 | 87.23% | USD 41.99 | USD 1,973.40 | USD -9,633.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 47 | 87.23% | USD -10.21 | USD -480.00 | USD -9,686.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 47 | 87.23% | USD -18.01 | USD -846.60 | USD -9,693.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 50/50 (0) | 36.00% (24.14–49.86%) | USD -38.54 | USD -1,927.00 | USD -433.60 |
| HOLD_5_SESSIONS | 1 : 6 | 50/50 (0) | 50.00% (36.64–63.36%) | USD -325.64 | USD -16,282.00 | USD -5,175.10 |
| HOLD_5_SESSIONS | 6 : 1 | 50/50 (0) | 34.00% (22.44–47.85%) | USD 55.86 | USD 2,793.00 | USD -2,966.10 |
| HOLD_5_SESSIONS | 4 : 5 | 50/50 (0) | 44.00% (31.16–57.69%) | USD -211.58 | USD -10,579.00 | USD -2,682.70 |
| HOLD_10_SESSIONS | 1 : 1 | 50/50 (0) | 28.00% (17.47–41.67%) | USD -66.86 | USD -3,343.00 | USD -595.60 |
| HOLD_10_SESSIONS | 1 : 6 | 50/50 (0) | 70.00% (56.25–80.90%) | USD -1.56 | USD -78.00 | USD -7,969.10 |
| HOLD_10_SESSIONS | 6 : 1 | 50/50 (0) | 26.00% (15.87–39.55%) | USD -466.46 | USD -23,323.00 | USD -4,023.10 |
| HOLD_10_SESSIONS | 4 : 5 | 50/50 (0) | 46.00% (32.97–59.60%) | USD -254.38 | USD -12,719.00 | USD -3,618.70 |
| HOLD_20_SESSIONS | 1 : 1 | 49/50 (1) | 24.49% (14.60–38.09%) | USD -79.03 | USD -3,872.40 | USD -590.60 |
| HOLD_20_SESSIONS | 1 : 6 | 49/50 (1) | 79.59% (66.36–88.52%) | USD 630.80 | USD 30,909.10 | USD -9,449.10 |
| HOLD_20_SESSIONS | 6 : 1 | 49/50 (1) | 16.33% (8.51–29.04%) | USD -1,184.00 | USD -58,015.90 | USD -3,733.10 |
| HOLD_20_SESSIONS | 4 : 5 | 49/50 (1) | 69.39% (55.47–80.48%) | USD -174.15 | USD -8,533.30 | USD -3,856.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 47/50 (3) | 29.79% (18.65–43.98%) | USD -94.20 | USD -4,427.20 | USD -1,279.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 47/50 (3) | 87.23% (74.83–94.02%) | USD 481.75 | USD 22,642.30 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 47/50 (3) | 10.64% (4.63–22.59%) | USD -1,141.12 | USD -53,632.70 | USD -3,792.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 47/50 (3) | 76.60% (62.78–86.40%) | USD -261.59 | USD -12,294.90 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/50 | 0.00% | USD -96,916.58 | USD -141,445.90 |
| -75% | 0/50 | 0.00% | USD -71,575.18 | USD -105,061.90 |
| -50% | 0/50 | 0.00% | USD -46,233.78 | USD -68,677.90 |
| -40% | 0/50 | 0.00% | USD -36,097.22 | USD -54,124.30 |
| -30% | 0/50 | 0.00% | USD -25,960.66 | USD -39,570.70 |
| -25% | 0/50 | 0.00% | USD -20,892.38 | USD -32,346.90 |
| -20% | 0/50 | 0.00% | USD -15,824.10 | USD -25,162.70 |
| -15% | 0/50 | 0.00% | USD -10,755.82 | USD -18,093.00 |
| -10% | 2/50 | 4.00% | USD -5,685.14 | USD -11,173.30 |
| -5% | 17/50 | 34.00% | USD -903.44 | USD -4,261.00 |
| 0% | 50/50 | 100.00% | USD 816.30 | USD 274.10 |
| 5% | 50/50 | 100.00% | USD 816.30 | USD 274.10 |
| 10% | 50/50 | 100.00% | USD 816.30 | USD 274.10 |
| 20% | 50/50 | 100.00% | USD 816.30 | USD 274.10 |

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