# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 741 checks; 65 qualified; 676 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 443.47 / USD 1,273.08; mean absolute mismatch USD 829.61; mean match score 34.37%.
- Actual selected contract ratios: {'1:3': 64}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 65; entered cohorts: 64; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 64/64 | 37/27/0 | 57.81% (45.61–69.13%) | USD -74.92 | USD 116.80 | USD -4,794.80 | USD -2,117.20 | 0 |
| HOLD_10_SESSIONS | 64/64 | 48/16/0 | 75.00% (63.18–83.99%) | USD -38.15 | USD 282.80 | USD -2,441.80 | USD -4,203.20 | 0 |
| HOLD_20_SESSIONS | 62/64 | 50/12/0 | 80.65% (69.15–88.57%) | USD 330.90 | USD 572.80 | USD 20,515.60 | USD -3,960.20 | 2 |
| EXIT_AT_DTE_LE_7 | 55/64 | 44/11/0 | 80.00% (67.64–88.45%) | USD 174.91 | USD 627.80 | USD 9,620.00 | USD -8,692.20 | 9 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -23.30 | USD -6.42 |
| HOLD_10_SESSIONS | USD -43.58 | USD 50.62 |
| HOLD_20_SESSIONS | USD -205.95 | USD 582.05 |
| EXIT_AT_DTE_LE_7 | USD -107.93 | USD 328.04 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 64 | 60.94% | USD -29.72 | USD -1,902.00 | USD -2,072.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 64 | 60.94% | USD -34.92 | USD -2,234.80 | USD -2,077.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 64 | 57.81% | USD -49.72 | USD -3,182.00 | USD -2,092.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 64 | 57.81% | USD -54.92 | USD -3,514.80 | USD -2,097.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 64 | 57.81% | USD -69.72 | USD -4,462.00 | USD -2,112.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 64 | 57.81% | USD -74.92 | USD -4,794.80 | USD -2,117.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 64 | 56.25% | USD -109.72 | USD -7,022.00 | USD -2,152.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 64 | 56.25% | USD -114.92 | USD -7,354.80 | USD -2,157.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 64 | 75.00% | USD 7.05 | USD 451.00 | USD -4,158.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 64 | 75.00% | USD 1.85 | USD 118.20 | USD -4,163.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 64 | 75.00% | USD -12.95 | USD -829.00 | USD -4,178.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 64 | 75.00% | USD -18.15 | USD -1,161.80 | USD -4,183.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 64 | 75.00% | USD -32.95 | USD -2,109.00 | USD -4,198.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 64 | 75.00% | USD -38.15 | USD -2,441.80 | USD -4,203.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 64 | 75.00% | USD -72.95 | USD -4,669.00 | USD -4,238.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 64 | 73.44% | USD -78.15 | USD -5,001.80 | USD -4,243.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 62 | 82.26% | USD 376.10 | USD 23,318.00 | USD -3,915.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 62 | 82.26% | USD 370.90 | USD 22,995.60 | USD -3,920.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 62 | 82.26% | USD 356.10 | USD 22,078.00 | USD -3,935.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 62 | 82.26% | USD 350.90 | USD 21,755.60 | USD -3,940.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 62 | 82.26% | USD 336.10 | USD 20,838.00 | USD -3,955.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 62 | 80.65% | USD 330.90 | USD 20,515.60 | USD -3,960.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 62 | 80.65% | USD 296.10 | USD 18,358.00 | USD -3,995.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 62 | 80.65% | USD 290.90 | USD 18,035.60 | USD -4,000.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 55 | 80.00% | USD 220.11 | USD 12,106.00 | USD -8,647.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 55 | 80.00% | USD 214.91 | USD 11,820.00 | USD -8,652.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 55 | 80.00% | USD 200.11 | USD 11,006.00 | USD -8,667.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 55 | 80.00% | USD 194.91 | USD 10,720.00 | USD -8,672.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 55 | 80.00% | USD 180.11 | USD 9,906.00 | USD -8,687.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 55 | 80.00% | USD 174.91 | USD 9,620.00 | USD -8,692.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 55 | 80.00% | USD 140.11 | USD 7,706.00 | USD -8,727.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 55 | 80.00% | USD 134.91 | USD 7,420.00 | USD -8,732.20 |

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
| -100% | 0/64 | 0.00% | USD -87,089.43 | USD -134,816.60 |
| -75% | 0/64 | 0.00% | USD -64,231.32 | USD -99,643.35 |
| -50% | 0/64 | 0.00% | USD -41,373.21 | USD -64,470.10 |
| -40% | 0/64 | 0.00% | USD -32,229.97 | USD -50,400.80 |
| -30% | 0/64 | 0.00% | USD -23,086.72 | USD -36,331.50 |
| -25% | 0/64 | 0.00% | USD -18,515.10 | USD -29,296.85 |
| -20% | 0/64 | 0.00% | USD -13,943.48 | USD -22,604.60 |
| -15% | 0/64 | 0.00% | USD -9,371.86 | USD -15,913.35 |
| -10% | 1/64 | 1.56% | USD -4,800.51 | USD -9,744.10 |
| -5% | 27/64 | 42.19% | USD -428.23 | USD -3,798.85 |
| 0% | 64/64 | 100.00% | USD 807.01 | USD 228.40 |
| 5% | 64/64 | 100.00% | USD 807.01 | USD 228.40 |
| 10% | 64/64 | 100.00% | USD 807.01 | USD 228.40 |
| 20% | 64/64 | 100.00% | USD 807.01 | USD 228.40 |

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