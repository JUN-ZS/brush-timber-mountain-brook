# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 741 checks; 65 qualified; 676 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 890.38 / USD 1,708.94; mean absolute mismatch USD 818.56; mean match score 51.45%.
- Actual selected contract ratios: {'2:4': 64}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 65; entered cohorts: 64; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 64/64 | 39/25/0 | 60.94% (48.69–71.94%) | USD -110.61 | USD 102.20 | USD -7,079.20 | USD -2,511.80 | 0 |
| HOLD_10_SESSIONS | 64/64 | 47/17/0 | 73.44% (61.52–82.70%) | USD -77.67 | USD 261.20 | USD -4,971.20 | USD -4,617.80 | 0 |
| HOLD_20_SESSIONS | 62/64 | 51/11/0 | 82.26% (70.96–89.79%) | USD 298.97 | USD 531.20 | USD 18,536.40 | USD -4,309.80 | 2 |
| EXIT_AT_DTE_LE_7 | 55/64 | 44/11/0 | 80.00% (67.64–88.45%) | USD 153.73 | USD 580.20 | USD 8,455.00 | USD -9,633.80 | 9 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -46.94 | USD 4.12 |
| HOLD_10_SESSIONS | USD -91.81 | USD 81.94 |
| HOLD_20_SESSIONS | USD -410.39 | USD 777.16 |
| EXIT_AT_DTE_LE_7 | USD -214.98 | USD 436.51 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 64 | 64.06% | USD -42.81 | USD -2,740.00 | USD -2,444.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 64 | 64.06% | USD -50.61 | USD -3,239.20 | USD -2,451.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 64 | 64.06% | USD -72.81 | USD -4,660.00 | USD -2,474.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 64 | 64.06% | USD -80.61 | USD -5,159.20 | USD -2,481.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 64 | 62.50% | USD -102.81 | USD -6,580.00 | USD -2,504.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 64 | 60.94% | USD -110.61 | USD -7,079.20 | USD -2,511.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 64 | 56.25% | USD -162.81 | USD -10,420.00 | USD -2,564.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 64 | 56.25% | USD -170.61 | USD -10,919.20 | USD -2,571.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 64 | 73.44% | USD -9.88 | USD -632.00 | USD -4,550.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 64 | 73.44% | USD -17.68 | USD -1,131.20 | USD -4,557.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 64 | 73.44% | USD -39.88 | USD -2,552.00 | USD -4,580.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 64 | 73.44% | USD -47.67 | USD -3,051.20 | USD -4,587.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 64 | 73.44% | USD -69.88 | USD -4,472.00 | USD -4,610.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 64 | 73.44% | USD -77.67 | USD -4,971.20 | USD -4,617.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 64 | 70.31% | USD -129.88 | USD -8,312.00 | USD -4,670.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 64 | 70.31% | USD -137.68 | USD -8,811.20 | USD -4,677.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 62 | 83.87% | USD 366.77 | USD 22,740.00 | USD -4,242.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 62 | 82.26% | USD 358.97 | USD 22,256.40 | USD -4,249.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 62 | 82.26% | USD 336.77 | USD 20,880.00 | USD -4,272.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 62 | 82.26% | USD 328.97 | USD 20,396.40 | USD -4,279.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 62 | 82.26% | USD 306.77 | USD 19,020.00 | USD -4,302.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 62 | 82.26% | USD 298.97 | USD 18,536.40 | USD -4,309.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 62 | 82.26% | USD 246.77 | USD 15,300.00 | USD -4,362.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 62 | 82.26% | USD 238.97 | USD 14,816.40 | USD -4,369.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 55 | 80.00% | USD 221.53 | USD 12,184.00 | USD -9,566.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 55 | 80.00% | USD 213.73 | USD 11,755.00 | USD -9,573.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 55 | 80.00% | USD 191.53 | USD 10,534.00 | USD -9,596.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 55 | 80.00% | USD 183.73 | USD 10,105.00 | USD -9,603.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 55 | 80.00% | USD 161.53 | USD 8,884.00 | USD -9,626.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 55 | 80.00% | USD 153.73 | USD 8,455.00 | USD -9,633.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 55 | 80.00% | USD 101.53 | USD 5,584.00 | USD -9,686.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 55 | 80.00% | USD 93.73 | USD 5,155.00 | USD -9,693.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -45.04 | USD -2,882.40 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 64/64 (0) | 57.81% (45.61–69.13%) | USD -96.38 | USD -6,168.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -218.88 | USD -14,008.40 | USD -3,078.10 |
| HOLD_5_SESSIONS | 4 : 5 | 64/64 (0) | 50.00% (38.10–61.90%) | USD -190.42 | USD -12,186.80 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 64/64 (0) | 32.81% (22.57–45.00%) | USD -48.02 | USD -3,073.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 64/64 (0) | 73.44% (61.52–82.70%) | USD -2.10 | USD -134.40 | USD -10,501.10 |
| HOLD_10_SESSIONS | 6 : 1 | 64/64 (0) | 23.44% (14.75–35.13%) | USD -334.05 | USD -21,379.40 | USD -4,023.10 |
| HOLD_10_SESSIONS | 4 : 5 | 64/64 (0) | 54.69% (42.57–66.27%) | USD -182.90 | USD -11,705.80 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 62/64 (2) | 37.10% (26.16–49.54%) | USD -33.50 | USD -2,077.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 62/64 (2) | 82.26% (70.96–89.79%) | USD 881.45 | USD 54,649.80 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 62/64 (2) | 14.52% (7.83–25.34%) | USD -1,115.97 | USD -69,190.20 | USD -3,964.10 |
| HOLD_20_SESSIONS | 4 : 5 | 62/64 (2) | 70.97% (58.71–80.78%) | USD 48.98 | USD 3,036.60 | USD -4,305.70 |
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
| -100% | 0/64 | 0.00% | USD -95,736.34 | USD -141,445.90 |
| -75% | 0/64 | 0.00% | USD -70,716.02 | USD -105,061.90 |
| -50% | 0/64 | 0.00% | USD -45,695.70 | USD -68,677.90 |
| -40% | 0/64 | 0.00% | USD -35,687.57 | USD -54,124.30 |
| -30% | 0/64 | 0.00% | USD -25,679.44 | USD -39,570.70 |
| -25% | 0/64 | 0.00% | USD -20,675.38 | USD -32,293.90 |
| -20% | 0/64 | 0.00% | USD -15,671.31 | USD -25,017.10 |
| -15% | 0/64 | 0.00% | USD -10,667.25 | USD -17,740.30 |
| -10% | 1/64 | 1.56% | USD -5,660.01 | USD -10,582.10 |
| -5% | 24/64 | 37.50% | USD -757.68 | USD -4,261.00 |
| 0% | 64/64 | 100.00% | USD 784.66 | USD 216.10 |
| 5% | 64/64 | 100.00% | USD 784.66 | USD 216.10 |
| 10% | 64/64 | 100.00% | USD 784.66 | USD 216.10 |
| 20% | 64/64 | 100.00% | USD 784.66 | USD 216.10 |

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