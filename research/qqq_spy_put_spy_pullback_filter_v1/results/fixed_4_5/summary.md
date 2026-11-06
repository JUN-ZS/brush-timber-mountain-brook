# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d_and_spy_nonpositive_20d — Require QQQ trailing 20-session return below SPY AND SPY trailing return <= 0%; signal at close, entry no earlier than next common session.
- Filter evaluation: 928 checks; 24 qualified; 904 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,935.00 / USD 2,391.46; mean absolute mismatch USD 485.63; mean match score 77.73%.
- Actual selected contract ratios: {'4:5': 24}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 24; entered cohorts: 24; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 24/24 | 13/11/0 | 54.17% (35.07–72.11%) | USD -125.95 | USD 22.80 | USD -3,022.80 | USD -2,180.70 | 0 |
| HOLD_10_SESSIONS | 24/24 | 13/11/0 | 54.17% (35.07–72.11%) | USD -545.87 | USD 23.30 | USD -13,100.80 | USD -7,336.70 | 0 |
| HOLD_20_SESSIONS | 23/24 | 16/7/0 | 69.57% (49.13–84.40%) | USD -255.00 | USD 166.30 | USD -5,865.10 | USD -5,762.70 | 1 |
| EXIT_AT_DTE_LE_7 | 22/24 | 16/6/0 | 72.73% (51.85–86.85%) | USD 101.98 | USD 232.30 | USD 2,243.60 | USD -1,575.70 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -45.50 | USD 21.25 |
| HOLD_10_SESSIONS | USD -91.67 | USD -352.50 |
| HOLD_20_SESSIONS | USD -592.00 | USD 438.70 |
| EXIT_AT_DTE_LE_7 | USD -881.09 | USD 1,084.77 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 24 | 62.50% | USD -24.25 | USD -582.00 | USD -2,079.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 24 | 62.50% | USD -35.95 | USD -862.80 | USD -2,090.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 24 | 62.50% | USD -69.25 | USD -1,662.00 | USD -2,124.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 24 | 58.33% | USD -80.95 | USD -1,942.80 | USD -2,135.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 24 | 58.33% | USD -114.25 | USD -2,742.00 | USD -2,169.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 24 | 54.17% | USD -125.95 | USD -3,022.80 | USD -2,180.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 24 | 45.83% | USD -204.25 | USD -4,902.00 | USD -2,259.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 24 | 41.67% | USD -215.95 | USD -5,182.80 | USD -2,270.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 24 | 62.50% | USD -444.17 | USD -10,660.00 | USD -7,235.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 24 | 58.33% | USD -455.87 | USD -10,940.80 | USD -7,246.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 24 | 54.17% | USD -489.17 | USD -11,740.00 | USD -7,280.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 24 | 54.17% | USD -500.87 | USD -12,020.80 | USD -7,291.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 24 | 54.17% | USD -534.17 | USD -12,820.00 | USD -7,325.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 24 | 54.17% | USD -545.87 | USD -13,100.80 | USD -7,336.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 24 | 41.67% | USD -624.17 | USD -14,980.00 | USD -7,415.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 24 | 37.50% | USD -635.87 | USD -15,260.80 | USD -7,426.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 23 | 69.57% | USD -153.30 | USD -3,526.00 | USD -5,661.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 23 | 69.57% | USD -165.00 | USD -3,795.10 | USD -5,672.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 23 | 69.57% | USD -198.30 | USD -4,561.00 | USD -5,706.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 23 | 69.57% | USD -210.00 | USD -4,830.10 | USD -5,717.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 23 | 69.57% | USD -243.30 | USD -5,596.00 | USD -5,751.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 23 | 69.57% | USD -255.00 | USD -5,865.10 | USD -5,762.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 23 | 60.87% | USD -333.30 | USD -7,666.00 | USD -5,841.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 23 | 56.52% | USD -345.00 | USD -7,935.10 | USD -5,852.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 22 | 77.27% | USD 203.68 | USD 4,481.00 | USD -1,474.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 22 | 77.27% | USD 191.98 | USD 4,223.60 | USD -1,485.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 22 | 77.27% | USD 158.68 | USD 3,491.00 | USD -1,519.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 22 | 72.73% | USD 146.98 | USD 3,233.60 | USD -1,530.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 22 | 72.73% | USD 113.68 | USD 2,501.00 | USD -1,564.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 22 | 72.73% | USD 101.98 | USD 2,243.60 | USD -1,575.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 22 | 68.18% | USD 23.68 | USD 521.00 | USD -1,654.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 22 | 68.18% | USD 11.98 | USD 263.60 | USD -1,665.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 24/24 (0) | 37.50% (21.16–57.29%) | USD -29.73 | USD -713.40 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 24/24 (0) | 58.33% (38.83–75.53%) | USD -64.97 | USD -1,559.40 | USD -4,744.10 |
| HOLD_5_SESSIONS | 6 : 1 | 24/24 (0) | 37.50% (21.16–57.29%) | USD -143.10 | USD -3,434.40 | USD -3,952.10 |
| HOLD_5_SESSIONS | 4 : 5 | 24/24 (0) | 54.17% (35.07–72.11%) | USD -125.95 | USD -3,022.80 | USD -2,180.70 |
| HOLD_10_SESSIONS | 1 : 1 | 24/24 (0) | 29.17% (14.91–49.17%) | USD -116.02 | USD -2,784.40 | USD -951.60 |
| HOLD_10_SESSIONS | 1 : 6 | 24/24 (0) | 58.33% (38.83–75.53%) | USD -525.02 | USD -12,600.40 | USD -18,603.10 |
| HOLD_10_SESSIONS | 6 : 1 | 24/24 (0) | 33.33% (17.97–53.29%) | USD -287.10 | USD -6,890.40 | USD -4,731.10 |
| HOLD_10_SESSIONS | 4 : 5 | 24/24 (0) | 54.17% (35.07–72.11%) | USD -545.87 | USD -13,100.80 | USD -7,336.70 |
| HOLD_20_SESSIONS | 1 : 1 | 23/24 (1) | 34.78% (18.81–55.11%) | USD -82.86 | USD -1,905.80 | USD -801.60 |
| HOLD_20_SESSIONS | 1 : 6 | 23/24 (1) | 78.26% (58.10–90.34%) | USD 299.33 | USD 6,884.70 | USD -13,583.10 |
| HOLD_20_SESSIONS | 6 : 1 | 23/24 (1) | 17.39% (6.98–37.14%) | USD -879.36 | USD -20,225.30 | USD -3,962.10 |
| HOLD_20_SESSIONS | 4 : 5 | 23/24 (1) | 69.57% (49.13–84.40%) | USD -255.00 | USD -5,865.10 | USD -5,762.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 22/24 (2) | 36.36% (19.73–57.05%) | USD -25.92 | USD -570.20 | USD -256.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 22/24 (2) | 86.36% (66.67–95.25%) | USD 1,002.35 | USD 22,051.80 | USD -6,964.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 22/24 (2) | 13.64% (4.75–33.34%) | USD -1,183.78 | USD -26,043.20 | USD -3,999.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 22/24 (2) | 72.73% (51.85–86.85%) | USD 101.98 | USD 2,243.60 | USD -1,575.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/24 | 0.00% | USD -74,050.64 | USD -89,907.85 |
| -75% | 0/24 | 0.00% | USD -54,992.69 | USD -67,066.10 |
| -50% | 0/24 | 0.00% | USD -35,934.75 | USD -44,224.35 |
| -40% | 0/24 | 0.00% | USD -28,311.57 | USD -35,087.65 |
| -30% | 0/24 | 0.00% | USD -20,688.39 | USD -25,950.95 |
| -25% | 0/24 | 0.00% | USD -16,876.80 | USD -21,435.60 |
| -20% | 0/24 | 0.00% | USD -13,065.21 | USD -16,982.45 |
| -15% | 0/24 | 0.00% | USD -9,253.62 | USD -12,529.30 |
| -10% | 0/24 | 0.00% | USD -5,442.03 | USD -8,404.05 |
| -5% | 8/24 | 33.33% | USD -1,213.21 | USD -3,623.00 |
| 0% | 23/24 | 95.83% | USD 405.61 | USD -400.85 |
| 5% | 23/24 | 95.83% | USD 405.61 | USD -400.85 |
| 10% | 23/24 | 95.83% | USD 405.61 | USD -400.85 |
| 20% | 23/24 | 95.83% | USD 405.61 | USD -400.85 |

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

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.