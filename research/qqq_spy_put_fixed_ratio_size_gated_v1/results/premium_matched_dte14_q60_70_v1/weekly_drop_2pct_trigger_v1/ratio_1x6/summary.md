# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_2pct_corr60_pos — SPY rolling 5-session return crosses from above -2% to <= -2%, with positive Pearson correlation over the prior 60 daily returns; entry no earlier than next observed common session.
- Filter evaluation: 1952 checks; 99 qualified; 1853 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,082.97 / USD 1,708.06; mean absolute mismatch USD 656.91; mean match score 68.72%.
- Actual selected contract ratios: {'1:6': 99}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 99; entered cohorts: 99; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/99 | 76/22/0 | 77.55% (68.34–84.68%) | USD 373.68 | USD 448.40 | USD 36,620.20 | USD -8,260.10 | 1 |
| HOLD_10_SESSIONS | 5/99 | 5/0/0 | 100.00% (56.55–100.00%) | USD 1,335.50 | USD 1,501.90 | USD 6,677.50 | USD 600.90 | 94 |
| HOLD_20_SESSIONS | 0/99 | 0/0/0 | — | — | — | — | — | 99 |
| HOLD_20_OR_DTE_LE_7 | 99/99 | 70/29/0 | 70.71% (61.10–78.76%) | USD -23.66 | USD 246.90 | USD -2,341.90 | USD -21,700.10 | 0 |
| EXIT_AT_DTE_LE_7 | 99/99 | 70/29/0 | 70.71% (61.10–78.76%) | USD -23.66 | USD 246.90 | USD -2,341.90 | USD -21,700.10 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -207.16 | USD 659.94 |
| HOLD_10_SESSIONS | USD -408.20 | USD 1,822.80 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -134.07 | USD 189.52 |
| EXIT_AT_DTE_LE_7 | USD -134.07 | USD 189.52 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 81.63% | USD 452.78 | USD 44,372.00 | USD -8,181.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 81.63% | USD 443.68 | USD 43,480.20 | USD -8,190.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 79.59% | USD 417.78 | USD 40,942.00 | USD -8,216.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 77.55% | USD 408.68 | USD 40,050.20 | USD -8,225.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 77.55% | USD 382.78 | USD 37,512.00 | USD -8,251.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 77.55% | USD 373.68 | USD 36,620.20 | USD -8,260.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 73.47% | USD 312.78 | USD 30,652.00 | USD -8,321.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 72.45% | USD 303.68 | USD 29,760.20 | USD -8,330.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 5 | 100.00% | USD 1,414.60 | USD 7,073.00 | USD 680.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 5 | 100.00% | USD 1,405.50 | USD 7,027.50 | USD 670.90 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 5 | 100.00% | USD 1,379.60 | USD 6,898.00 | USD 645.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 5 | 100.00% | USD 1,370.50 | USD 6,852.50 | USD 635.90 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 5 | 100.00% | USD 1,344.60 | USD 6,723.00 | USD 610.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 5 | 100.00% | USD 1,335.50 | USD 6,677.50 | USD 600.90 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 5 | 100.00% | USD 1,274.60 | USD 6,373.00 | USD 540.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 5 | 100.00% | USD 1,265.50 | USD 6,327.50 | USD 530.90 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 99 | 75.76% | USD 55.44 | USD 5,489.00 | USD -21,621.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 99 | 74.75% | USD 46.34 | USD 4,588.10 | USD -21,630.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 99 | 73.74% | USD 20.44 | USD 2,024.00 | USD -21,656.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 99 | 73.74% | USD 11.34 | USD 1,123.10 | USD -21,665.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 99 | 70.71% | USD -14.56 | USD -1,441.00 | USD -21,691.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 99 | 70.71% | USD -23.66 | USD -2,341.90 | USD -21,700.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 99 | 66.67% | USD -84.56 | USD -8,371.00 | USD -21,761.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 99 | 63.64% | USD -93.66 | USD -9,271.90 | USD -21,770.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 99 | 75.76% | USD 55.44 | USD 5,489.00 | USD -21,621.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 99 | 74.75% | USD 46.34 | USD 4,588.10 | USD -21,630.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 99 | 73.74% | USD 20.44 | USD 2,024.00 | USD -21,656.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 99 | 73.74% | USD 11.34 | USD 1,123.10 | USD -21,665.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 99 | 70.71% | USD -14.56 | USD -1,441.00 | USD -21,691.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 99 | 70.71% | USD -23.66 | USD -2,341.90 | USD -21,700.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 99 | 66.67% | USD -84.56 | USD -8,371.00 | USD -21,761.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 99 | 63.64% | USD -93.66 | USD -9,271.90 | USD -21,770.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/99 (1) | 38.78% (29.73–48.67%) | USD -119.77 | USD -11,737.80 | USD -1,519.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/99 (1) | 77.55% (68.34–84.68%) | USD 373.68 | USD 36,620.20 | USD -8,260.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/99 (1) | 34.69% (26.01–44.53%) | USD -1,212.09 | USD -118,784.80 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 98/99 (1) | 38.78% (29.73–48.67%) | USD -598.87 | USD -58,689.00 | USD -7,598.00 |
| HOLD_10_SESSIONS | 1 : 1 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -127.00 | USD -635.00 | USD -640.60 |
| HOLD_10_SESSIONS | 1 : 6 | 5/99 (94) | 100.00% (56.55–100.00%) | USD 1,335.50 | USD 6,677.50 | USD 600.90 |
| HOLD_10_SESSIONS | 6 : 1 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -2,224.50 | USD -11,122.50 | USD -6,197.10 |
| HOLD_10_SESSIONS | 5 : 5 | 5/99 (94) | 40.00% (11.76–76.93%) | USD -635.00 | USD -3,175.00 | USD -3,203.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/99 (99) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -125.08 | USD -12,383.40 | USD -1,312.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 99/99 (0) | 70.71% (61.10–78.76%) | USD -23.66 | USD -2,341.90 | USD -21,700.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -851.94 | USD -84,341.90 | USD -16,269.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -625.42 | USD -61,917.00 | USD -6,563.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -125.08 | USD -12,383.40 | USD -1,312.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 99/99 (0) | 70.71% (61.10–78.76%) | USD -23.66 | USD -2,341.90 | USD -21,700.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 99/99 (0) | 34.34% (25.73–44.12%) | USD -851.94 | USD -84,341.90 | USD -16,269.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 99/99 (0) | 35.35% (26.64–45.16%) | USD -625.42 | USD -61,917.00 | USD -6,563.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/99 | 0.00% | USD -202,083.15 | USD -327,173.55 |
| -75% | 0/99 | 0.00% | USD -149,224.11 | USD -243,069.30 |
| -50% | 0/99 | 0.00% | USD -96,365.07 | USD -158,965.05 |
| -40% | 0/99 | 0.00% | USD -75,221.45 | USD -125,323.35 |
| -30% | 0/99 | 0.00% | USD -54,077.83 | USD -91,681.65 |
| -25% | 0/99 | 0.00% | USD -43,506.02 | USD -74,860.80 |
| -20% | 0/99 | 0.00% | USD -32,934.22 | USD -58,039.95 |
| -15% | 0/99 | 0.00% | USD -22,362.41 | USD -41,219.10 |
| -10% | 2/99 | 2.02% | USD -11,830.47 | USD -24,398.25 |
| -5% | 29/99 | 29.29% | USD -1,703.50 | USD -8,144.35 |
| 0% | 93/99 | 93.94% | USD 1,271.53 | USD -219.55 |
| 5% | 81/99 | 81.82% | USD 635.20 | USD -297.55 |
| 10% | 81/99 | 81.82% | USD 585.60 | USD -297.55 |
| 20% | 81/99 | 81.82% | USD 585.54 | USD -297.55 |

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