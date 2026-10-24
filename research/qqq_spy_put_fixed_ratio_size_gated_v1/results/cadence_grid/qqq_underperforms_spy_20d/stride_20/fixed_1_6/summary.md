# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 741 checks; 65 qualified; 676 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 443.47 / USD 2,546.16; mean absolute mismatch USD 2,102.69; mean match score 17.18%.
- Actual selected contract ratios: {'1:6': 64}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 65; entered cohorts: 64; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 64/64 | 37/27/0 | 57.81% (45.61–69.13%) | USD -115.24 | USD 329.90 | USD -7,375.40 | USD -4,827.10 | 0 |
| HOLD_10_SESSIONS | 64/64 | 47/17/0 | 73.44% (61.52–82.70%) | USD -21.43 | USD 764.40 | USD -1,371.40 | USD -10,453.10 | 0 |
| HOLD_20_SESSIONS | 62/64 | 51/11/0 | 82.26% (70.96–89.79%) | USD 879.05 | USD 1,502.90 | USD 54,500.80 | USD -9,376.10 | 2 |
| EXIT_AT_DTE_LE_7 | 55/64 | 45/10/0 | 81.82% (69.67–89.81%) | USD 469.05 | USD 1,647.90 | USD 25,797.50 | USD -20,318.10 | 9 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -23.30 | USD -12.84 |
| HOLD_10_SESSIONS | USD -43.58 | USD 101.25 |
| HOLD_20_SESSIONS | USD -205.95 | USD 1,164.10 |
| EXIT_AT_DTE_LE_7 | USD -107.93 | USD 656.07 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 64 | 60.94% | USD -36.14 | USD -2,313.00 | USD -4,748.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 64 | 60.94% | USD -45.24 | USD -2,895.40 | USD -4,757.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 64 | 60.94% | USD -71.14 | USD -4,553.00 | USD -4,783.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 64 | 59.38% | USD -80.24 | USD -5,135.40 | USD -4,792.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 64 | 59.38% | USD -106.14 | USD -6,793.00 | USD -4,818.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 64 | 57.81% | USD -115.24 | USD -7,375.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 64 | 57.81% | USD -176.14 | USD -11,273.00 | USD -4,888.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 64 | 56.25% | USD -185.24 | USD -11,855.40 | USD -4,897.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 64 | 76.56% | USD 57.67 | USD 3,691.00 | USD -10,374.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 64 | 76.56% | USD 48.57 | USD 3,108.60 | USD -10,383.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 64 | 76.56% | USD 22.67 | USD 1,451.00 | USD -10,409.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 64 | 76.56% | USD 13.57 | USD 868.60 | USD -10,418.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 64 | 73.44% | USD -12.33 | USD -789.00 | USD -10,444.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 64 | 73.44% | USD -21.43 | USD -1,371.40 | USD -10,453.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 64 | 73.44% | USD -82.33 | USD -5,269.00 | USD -10,514.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 64 | 73.44% | USD -91.43 | USD -5,851.40 | USD -10,523.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 62 | 83.87% | USD 958.15 | USD 59,405.00 | USD -9,297.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 62 | 83.87% | USD 949.05 | USD 58,840.80 | USD -9,306.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 62 | 83.87% | USD 923.15 | USD 57,235.00 | USD -9,332.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 62 | 83.87% | USD 914.05 | USD 56,670.80 | USD -9,341.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 62 | 83.87% | USD 888.15 | USD 55,065.00 | USD -9,367.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 62 | 82.26% | USD 879.05 | USD 54,500.80 | USD -9,376.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 62 | 82.26% | USD 818.15 | USD 50,725.00 | USD -9,437.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 62 | 82.26% | USD 809.05 | USD 50,160.80 | USD -9,446.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 55 | 81.82% | USD 548.15 | USD 30,148.00 | USD -20,239.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 55 | 81.82% | USD 539.05 | USD 29,647.50 | USD -20,248.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 55 | 81.82% | USD 513.15 | USD 28,223.00 | USD -20,274.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 55 | 81.82% | USD 504.05 | USD 27,722.50 | USD -20,283.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 55 | 81.82% | USD 478.15 | USD 26,298.00 | USD -20,309.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 55 | 81.82% | USD 469.05 | USD 25,797.50 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 55 | 81.82% | USD 408.15 | USD 22,448.00 | USD -20,379.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 55 | 81.82% | USD 399.05 | USD 21,947.50 | USD -20,388.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 64/64 (0) | 31.25% (21.23–43.39%) | USD -48.04 | USD -3,074.40 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 64/64 (0) | 57.81% (45.61–69.13%) | USD -115.24 | USD -7,375.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -221.02 | USD -14,145.40 | USD -3,078.10 |
| HOLD_5_SESSIONS | 4 : 5 | 64/64 (0) | 48.44% (36.63–60.42%) | USD -205.59 | USD -13,157.80 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -49.30 | USD -3,155.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 64/64 (0) | 73.44% (61.52–82.70%) | USD -21.43 | USD -1,371.40 | USD -10,453.10 |
| HOLD_10_SESSIONS | 6 : 1 | 64/64 (0) | 23.44% (14.75–35.13%) | USD -323.69 | USD -20,716.40 | USD -3,685.10 |
| HOLD_10_SESSIONS | 4 : 5 | 64/64 (0) | 53.12% (41.07–64.82%) | USD -191.64 | USD -12,264.80 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 62/64 (2) | 37.10% (26.16–49.54%) | USD -34.54 | USD -2,141.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 62/64 (2) | 82.26% (70.96–89.79%) | USD 879.05 | USD 54,500.80 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 62/64 (2) | 14.52% (7.83–25.34%) | USD -1,120.79 | USD -69,489.20 | USD -3,964.10 |
| HOLD_20_SESSIONS | 4 : 5 | 62/64 (2) | 70.97% (58.71–80.78%) | USD 44.57 | USD 2,763.60 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 55/64 (9) | 36.36% (24.93–49.58%) | USD -21.18 | USD -1,165.00 | USD -941.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 55/64 (9) | 81.82% (69.67–89.81%) | USD 469.05 | USD 25,797.50 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 55/64 (9) | 18.18% (10.19–30.33%) | USD -617.32 | USD -33,952.50 | USD -3,980.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 55/64 (9) | 70.91% (57.86–81.23%) | USD 13.32 | USD 732.50 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/64 | 0.00% | USD -204,741.11 | USD -326,323.55 |
| -75% | 0/64 | 0.00% | USD -150,848.48 | USD -240,755.55 |
| -50% | 0/64 | 0.00% | USD -96,955.85 | USD -155,187.55 |
| -40% | 0/64 | 0.00% | USD -75,398.80 | USD -120,960.35 |
| -30% | 0/64 | 0.00% | USD -53,841.75 | USD -86,733.15 |
| -25% | 0/64 | 0.00% | USD -43,063.23 | USD -70,306.30 |
| -20% | 0/64 | 0.00% | USD -32,284.70 | USD -54,098.75 |
| -15% | 0/64 | 0.00% | USD -21,506.17 | USD -37,891.20 |
| -10% | 1/64 | 1.56% | USD -10,733.50 | USD -23,103.25 |
| -5% | 29/64 | 45.31% | USD -615.79 | USD -8,803.90 |
| 0% | 64/64 | 100.00% | USD 2,063.14 | USD 589.45 |
| 5% | 64/64 | 100.00% | USD 2,063.14 | USD 589.45 |
| 10% | 64/64 | 100.00% | USD 2,063.14 | USD 589.45 |
| 20% | 64/64 | 100.00% | USD 2,063.14 | USD 589.45 |

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