# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d_and_spy_nonpositive_20d — Require QQQ trailing 20-session return below SPY AND SPY trailing return <= 0%; signal at close, entry no earlier than next common session.
- Filter evaluation: 928 checks; 24 qualified; 904 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 490.50 / USD 2,901.25; mean absolute mismatch USD 2,410.75; mean match score 16.42%.
- Actual selected contract ratios: {'1:6': 24}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 24; entered cohorts: 24; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 24/24 | 14/10/0 | 58.33% (38.83–75.53%) | USD -52.39 | USD 597.90 | USD -1,257.40 | USD -4,744.10 | 0 |
| HOLD_10_SESSIONS | 24/24 | 14/10/0 | 58.33% (38.83–75.53%) | USD -505.35 | USD 734.90 | USD -12,128.40 | USD -18,603.10 | 0 |
| HOLD_20_SESSIONS | 23/24 | 18/5/0 | 78.26% (58.10–90.34%) | USD 299.33 | USD 1,740.90 | USD 6,884.70 | USD -13,583.10 | 1 |
| EXIT_AT_DTE_LE_7 | 22/24 | 19/3/0 | 86.36% (66.67–95.25%) | USD 1,002.35 | USD 1,920.40 | USD 22,051.80 | USD -6,964.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -13.79 | USD 40.50 |
| HOLD_10_SESSIONS | USD -28.00 | USD -398.25 |
| HOLD_20_SESSIONS | USD -148.00 | USD 526.43 |
| EXIT_AT_DTE_LE_7 | USD -220.27 | USD 1,301.73 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 24 | 58.33% | USD 26.71 | USD 641.00 | USD -4,665.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 24 | 58.33% | USD 17.61 | USD 422.60 | USD -4,674.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 24 | 58.33% | USD -8.29 | USD -199.00 | USD -4,700.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 24 | 58.33% | USD -17.39 | USD -417.40 | USD -4,709.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 24 | 58.33% | USD -43.29 | USD -1,039.00 | USD -4,735.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 24 | 58.33% | USD -52.39 | USD -1,257.40 | USD -4,744.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 24 | 58.33% | USD -113.29 | USD -2,719.00 | USD -4,805.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 24 | 58.33% | USD -122.39 | USD -2,937.40 | USD -4,814.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 24 | 62.50% | USD -426.25 | USD -10,230.00 | USD -18,524.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 24 | 62.50% | USD -435.35 | USD -10,448.40 | USD -18,533.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 24 | 62.50% | USD -461.25 | USD -11,070.00 | USD -18,559.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 24 | 62.50% | USD -470.35 | USD -11,288.40 | USD -18,568.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 24 | 58.33% | USD -496.25 | USD -11,910.00 | USD -18,594.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 24 | 58.33% | USD -505.35 | USD -12,128.40 | USD -18,603.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 24 | 58.33% | USD -566.25 | USD -13,590.00 | USD -18,664.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 24 | 58.33% | USD -575.35 | USD -13,808.40 | USD -18,673.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 23 | 78.26% | USD 378.43 | USD 8,704.00 | USD -13,504.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 23 | 78.26% | USD 369.33 | USD 8,494.70 | USD -13,513.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 23 | 78.26% | USD 343.43 | USD 7,899.00 | USD -13,539.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 23 | 78.26% | USD 334.33 | USD 7,689.70 | USD -13,548.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 23 | 78.26% | USD 308.43 | USD 7,094.00 | USD -13,574.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 23 | 78.26% | USD 299.33 | USD 6,884.70 | USD -13,583.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 23 | 78.26% | USD 238.43 | USD 5,484.00 | USD -13,644.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 23 | 78.26% | USD 229.33 | USD 5,274.70 | USD -13,653.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 22 | 86.36% | USD 1,081.45 | USD 23,792.00 | USD -6,885.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 22 | 86.36% | USD 1,072.35 | USD 23,591.80 | USD -6,894.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 22 | 86.36% | USD 1,046.45 | USD 23,022.00 | USD -6,920.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 22 | 86.36% | USD 1,037.35 | USD 22,821.80 | USD -6,929.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 22 | 86.36% | USD 1,011.45 | USD 22,252.00 | USD -6,955.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 22 | 86.36% | USD 1,002.35 | USD 22,051.80 | USD -6,964.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 22 | 86.36% | USD 941.45 | USD 20,712.00 | USD -7,025.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 22 | 86.36% | USD 932.35 | USD 20,511.80 | USD -7,034.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 24/24 (0) | 37.50% (21.16–57.29%) | USD -29.64 | USD -711.40 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 24/24 (0) | 58.33% (38.83–75.53%) | USD -52.39 | USD -1,257.40 | USD -4,744.10 |
| HOLD_5_SESSIONS | 6 : 1 | 24/24 (0) | 37.50% (21.16–57.29%) | USD -155.10 | USD -3,722.40 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 24/24 (0) | 54.17% (35.07–72.11%) | USD -123.12 | USD -2,954.80 | USD -2,180.70 |
| HOLD_10_SESSIONS | 1 : 1 | 24/24 (0) | 29.17% (14.91–49.17%) | USD -116.97 | USD -2,807.40 | USD -951.60 |
| HOLD_10_SESSIONS | 1 : 6 | 24/24 (0) | 58.33% (38.83–75.53%) | USD -505.35 | USD -12,128.40 | USD -18,603.10 |
| HOLD_10_SESSIONS | 6 : 1 | 24/24 (0) | 33.33% (17.97–53.29%) | USD -313.48 | USD -7,523.40 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 24/24 (0) | 54.17% (35.07–72.11%) | USD -545.58 | USD -13,093.80 | USD -7,336.70 |
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
| -100% | 0/24 | 0.00% | USD -202,551.72 | USD -320,328.55 |
| -75% | 0/24 | 0.00% | USD -149,066.29 | USD -236,224.30 |
| -50% | 0/24 | 0.00% | USD -95,580.86 | USD -152,120.05 |
| -40% | 0/24 | 0.00% | USD -74,186.69 | USD -118,478.35 |
| -30% | 0/24 | 0.00% | USD -52,792.52 | USD -84,836.65 |
| -25% | 0/24 | 0.00% | USD -42,095.44 | USD -68,015.80 |
| -20% | 0/24 | 0.00% | USD -31,398.35 | USD -51,194.95 |
| -15% | 0/24 | 0.00% | USD -20,701.26 | USD -34,374.10 |
| -10% | 0/24 | 0.00% | USD -10,004.18 | USD -18,612.45 |
| -5% | 12/24 | 50.00% | USD 97.01 | USD -4,751.50 |
| 0% | 24/24 | 100.00% | USD 2,371.20 | USD 858.45 |
| 5% | 24/24 | 100.00% | USD 2,371.20 | USD 858.45 |
| 10% | 24/24 | 100.00% | USD 2,371.20 | USD 858.45 |
| 20% | 24/24 | 100.00% | USD 2,371.20 | USD 858.45 |

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