# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 741 checks; 65 qualified; 676 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,780.75 / USD 2,136.17; mean absolute mismatch USD 407.14; mean match score 80.47%.
- Actual selected contract ratios: {'4:5': 64}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 65; entered cohorts: 64; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 64/64 | 32/32/0 | 50.00% (38.10–61.90%) | USD -183.12 | USD -6.70 | USD -11,719.80 | USD -2,439.70 | 0 |
| HOLD_10_SESSIONS | 64/64 | 35/29/0 | 54.69% (42.57–66.27%) | USD -182.90 | USD 52.80 | USD -11,705.80 | USD -4,602.70 | 0 |
| HOLD_20_SESSIONS | 62/64 | 44/18/0 | 70.97% (58.71–80.78%) | USD 44.65 | USD 198.30 | USD 2,768.60 | USD -4,305.70 | 2 |
| EXIT_AT_DTE_LE_7 | 55/64 | 39/16/0 | 70.91% (57.86–81.23%) | USD 13.97 | USD 264.30 | USD 768.50 | USD -7,641.70 | 9 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -101.19 | USD 19.77 |
| HOLD_10_SESSIONS | USD -183.62 | USD 102.42 |
| HOLD_20_SESSIONS | USD -838.32 | USD 984.68 |
| EXIT_AT_DTE_LE_7 | USD -429.96 | USD 545.64 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 64 | 53.12% | USD -81.42 | USD -5,211.00 | USD -2,338.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 64 | 53.12% | USD -93.12 | USD -5,959.80 | USD -2,349.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 64 | 53.12% | USD -126.42 | USD -8,091.00 | USD -2,383.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 64 | 51.56% | USD -138.12 | USD -8,839.80 | USD -2,394.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 64 | 50.00% | USD -171.42 | USD -10,971.00 | USD -2,428.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 64 | 50.00% | USD -183.12 | USD -11,719.80 | USD -2,439.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 64 | 42.19% | USD -261.42 | USD -16,731.00 | USD -2,518.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 64 | 40.62% | USD -273.12 | USD -17,479.80 | USD -2,529.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 64 | 64.06% | USD -81.20 | USD -5,197.00 | USD -4,501.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 64 | 64.06% | USD -92.90 | USD -5,945.80 | USD -4,512.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 64 | 59.38% | USD -126.20 | USD -8,077.00 | USD -4,546.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 64 | 57.81% | USD -137.90 | USD -8,825.80 | USD -4,557.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 64 | 56.25% | USD -171.20 | USD -10,957.00 | USD -4,591.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 64 | 54.69% | USD -182.90 | USD -11,705.80 | USD -4,602.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 64 | 43.75% | USD -261.20 | USD -16,717.00 | USD -4,681.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 64 | 42.19% | USD -272.90 | USD -17,465.80 | USD -4,692.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 62 | 77.42% | USD 146.35 | USD 9,074.00 | USD -4,204.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 62 | 77.42% | USD 134.65 | USD 8,348.60 | USD -4,215.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 62 | 77.42% | USD 101.35 | USD 6,284.00 | USD -4,249.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 62 | 74.19% | USD 89.65 | USD 5,558.60 | USD -4,260.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 62 | 74.19% | USD 56.35 | USD 3,494.00 | USD -4,294.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 62 | 70.97% | USD 44.65 | USD 2,768.60 | USD -4,305.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 62 | 62.90% | USD -33.65 | USD -2,086.00 | USD -4,384.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 62 | 62.90% | USD -45.35 | USD -2,811.40 | USD -4,395.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 55 | 78.18% | USD 115.67 | USD 6,362.00 | USD -7,540.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 55 | 78.18% | USD 103.97 | USD 5,718.50 | USD -7,551.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 55 | 76.36% | USD 70.67 | USD 3,887.00 | USD -7,585.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 55 | 76.36% | USD 58.97 | USD 3,243.50 | USD -7,596.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 55 | 70.91% | USD 25.67 | USD 1,412.00 | USD -7,630.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 55 | 70.91% | USD 13.97 | USD 768.50 | USD -7,641.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 55 | 63.64% | USD -64.33 | USD -3,538.00 | USD -7,720.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 55 | 63.64% | USD -76.03 | USD -4,181.50 | USD -7,731.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 64/64 (0) | 34.38% (23.92–46.60%) | USD -43.94 | USD -2,812.40 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 64/64 (0) | 57.81% (45.61–69.13%) | USD -80.68 | USD -5,163.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -226.93 | USD -14,523.40 | USD -3,078.10 |
| HOLD_5_SESSIONS | 4 : 5 | 64/64 (0) | 50.00% (38.10–61.90%) | USD -183.12 | USD -11,719.80 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -48.02 | USD -3,073.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 64/64 (0) | 73.44% (61.52–82.70%) | USD -2.10 | USD -134.40 | USD -10,501.10 |
| HOLD_10_SESSIONS | 6 : 1 | 64/64 (0) | 23.44% (14.75–35.13%) | USD -334.05 | USD -21,379.40 | USD -4,023.10 |
| HOLD_10_SESSIONS | 4 : 5 | 64/64 (0) | 54.69% (42.57–66.27%) | USD -182.90 | USD -11,705.80 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 62/64 (2) | 35.48% (24.74–47.92%) | USD -35.25 | USD -2,185.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 62/64 (2) | 82.26% (70.96–89.79%) | USD 892.93 | USD 55,361.80 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 62/64 (2) | 14.52% (7.83–25.34%) | USD -1,139.65 | USD -70,658.20 | USD -3,964.10 |
| HOLD_20_SESSIONS | 4 : 5 | 62/64 (2) | 70.97% (58.71–80.78%) | USD 44.65 | USD 2,768.60 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 55/64 (9) | 36.36% (24.93–49.58%) | USD -20.96 | USD -1,153.00 | USD -941.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 55/64 (9) | 81.82% (69.67–89.81%) | USD 468.17 | USD 25,749.50 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 55/64 (9) | 18.18% (10.19–30.33%) | USD -614.92 | USD -33,820.50 | USD -3,980.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 55/64 (9) | 70.91% (57.86–81.23%) | USD 13.97 | USD 768.50 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/64 | 0.00% | USD -73,829.62 | USD -94,322.85 |
| -75% | 0/64 | 0.00% | USD -54,816.51 | USD -70,290.60 |
| -50% | 0/64 | 0.00% | USD -35,803.40 | USD -46,476.35 |
| -40% | 0/64 | 0.00% | USD -28,198.16 | USD -37,150.25 |
| -30% | 0/64 | 0.00% | USD -20,592.92 | USD -28,013.15 |
| -25% | 0/64 | 0.00% | USD -16,790.30 | USD -23,444.60 |
| -20% | 0/64 | 0.00% | USD -12,987.68 | USD -18,876.05 |
| -15% | 0/64 | 0.00% | USD -9,185.06 | USD -14,307.50 |
| -10% | 1/64 | 1.56% | USD -5,370.51 | USD -9,738.95 |
| -5% | 22/64 | 34.38% | USD -1,309.88 | USD -5,170.40 |
| 0% | 55/64 | 85.94% | USD 304.57 | USD -990.85 |
| 5% | 55/64 | 85.94% | USD 304.57 | USD -990.85 |
| 10% | 55/64 | 85.94% | USD 304.57 | USD -990.85 |
| 20% | 55/64 | 85.94% | USD 304.57 | USD -990.85 |

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