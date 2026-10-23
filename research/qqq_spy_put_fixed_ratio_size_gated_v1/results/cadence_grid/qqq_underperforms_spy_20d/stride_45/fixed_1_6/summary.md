# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 399 checks; 36 qualified; 363 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 482.83 / USD 2,801.50; mean absolute mismatch USD 2,318.67; mean match score 17.03%.
- Actual selected contract ratios: {'1:6': 36}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 36; entered cohorts: 36; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 36/36 | 25/11/0 | 69.44% (53.14–82.00%) | USD 390.84 | USD 488.90 | USD 14,070.40 | USD -4,827.10 | 0 |
| HOLD_10_SESSIONS | 36/36 | 29/7/0 | 80.56% (64.97–90.25%) | USD 770.29 | USD 945.90 | USD 27,730.40 | USD -3,830.10 | 0 |
| HOLD_20_SESSIONS | 34/36 | 30/4/0 | 88.24% (73.38–95.33%) | USD 1,480.19 | USD 1,339.90 | USD 50,326.60 | USD -2,204.10 | 2 |
| EXIT_AT_DTE_LE_7 | 30/36 | 24/6/0 | 80.00% (62.69–90.49%) | USD 675.90 | USD 1,456.90 | USD 20,277.00 | USD -8,997.10 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -97.72 | USD 567.67 |
| HOLD_10_SESSIONS | USD -160.11 | USD 1,009.50 |
| HOLD_20_SESSIONS | USD -299.65 | USD 1,858.94 |
| EXIT_AT_DTE_LE_7 | USD -169.40 | USD 924.40 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 36 | 72.22% | USD 469.94 | USD 16,918.00 | USD -4,748.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 36 | 72.22% | USD 460.84 | USD 16,590.40 | USD -4,757.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 36 | 72.22% | USD 434.94 | USD 15,658.00 | USD -4,783.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 36 | 69.44% | USD 425.84 | USD 15,330.40 | USD -4,792.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 36 | 69.44% | USD 399.94 | USD 14,398.00 | USD -4,818.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 36 | 69.44% | USD 390.84 | USD 14,070.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 36 | 69.44% | USD 329.94 | USD 11,878.00 | USD -4,888.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 36 | 66.67% | USD 320.84 | USD 11,550.40 | USD -4,897.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 36 | 86.11% | USD 849.39 | USD 30,578.00 | USD -3,751.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 36 | 86.11% | USD 840.29 | USD 30,250.40 | USD -3,760.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 36 | 86.11% | USD 814.39 | USD 29,318.00 | USD -3,786.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 36 | 86.11% | USD 805.29 | USD 28,990.40 | USD -3,795.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 36 | 80.56% | USD 779.39 | USD 28,058.00 | USD -3,821.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 36 | 80.56% | USD 770.29 | USD 27,730.40 | USD -3,830.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 36 | 80.56% | USD 709.39 | USD 25,538.00 | USD -3,891.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 36 | 80.56% | USD 700.29 | USD 25,210.40 | USD -3,900.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 34 | 91.18% | USD 1,559.29 | USD 53,016.00 | USD -2,125.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 34 | 91.18% | USD 1,550.19 | USD 52,706.60 | USD -2,134.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 34 | 91.18% | USD 1,524.29 | USD 51,826.00 | USD -2,160.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 34 | 91.18% | USD 1,515.19 | USD 51,516.60 | USD -2,169.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 34 | 91.18% | USD 1,489.29 | USD 50,636.00 | USD -2,195.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 34 | 88.24% | USD 1,480.19 | USD 50,326.60 | USD -2,204.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 34 | 88.24% | USD 1,419.29 | USD 48,256.00 | USD -2,265.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 34 | 88.24% | USD 1,410.19 | USD 47,946.60 | USD -2,274.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 30 | 80.00% | USD 755.00 | USD 22,650.00 | USD -8,918.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 30 | 80.00% | USD 745.90 | USD 22,377.00 | USD -8,927.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 30 | 80.00% | USD 720.00 | USD 21,600.00 | USD -8,953.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 30 | 80.00% | USD 710.90 | USD 21,327.00 | USD -8,962.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 30 | 80.00% | USD 685.00 | USD 20,550.00 | USD -8,988.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 30 | 80.00% | USD 675.90 | USD 20,277.00 | USD -8,997.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 30 | 80.00% | USD 615.00 | USD 18,450.00 | USD -9,058.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 30 | 80.00% | USD 605.90 | USD 18,177.00 | USD -9,067.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 36/36 (0) | 33.33% (20.21–49.67%) | USD -25.71 | USD -925.60 | USD -152.60 |
| HOLD_5_SESSIONS | 1 : 6 | 36/36 (0) | 69.44% (53.14–82.00%) | USD 390.84 | USD 14,070.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -570.82 | USD -20,549.60 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 36/36 (0) | 55.56% (39.58–70.46%) | USD -19.53 | USD -703.20 | USD -787.70 |
| HOLD_10_SESSIONS | 1 : 1 | 36/36 (0) | 36.11% (22.48–52.42%) | USD -14.46 | USD -520.60 | USD -166.60 |
| HOLD_10_SESSIONS | 1 : 6 | 36/36 (0) | 80.56% (64.97–90.25%) | USD 770.29 | USD 27,730.40 | USD -3,830.10 |
| HOLD_10_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -871.52 | USD -31,374.60 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 36/36 (0) | 61.11% (44.86–75.22%) | USD 99.11 | USD 3,567.80 | USD -1,007.70 |
| HOLD_20_SESSIONS | 1 : 1 | 34/36 (2) | 41.18% (26.37–57.78%) | USD -12.42 | USD -422.40 | USD -382.60 |
| HOLD_20_SESSIONS | 1 : 6 | 34/36 (2) | 88.24% (73.38–95.33%) | USD 1,480.19 | USD 50,326.60 | USD -2,204.10 |
| HOLD_20_SESSIONS | 6 : 1 | 34/36 (2) | 5.88% (1.63–19.09%) | USD -1,567.16 | USD -53,283.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 34/36 (2) | 73.53% (56.88–85.40%) | USD 248.83 | USD 8,460.20 | USD -1,894.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 30/36 (6) | 36.67% (21.87–54.49%) | USD -37.93 | USD -1,138.00 | USD -762.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 30/36 (6) | 80.00% (62.69–90.49%) | USD 675.90 | USD 20,277.00 | USD -8,997.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 30/36 (6) | 16.67% (7.34–33.56%) | USD -941.43 | USD -28,243.00 | USD -4,765.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 30/36 (6) | 66.67% (48.78–80.77%) | USD -8.97 | USD -269.00 | USD -4,303.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/36 | 0.00% | USD -205,486.16 | USD -326,323.55 |
| -75% | 0/36 | 0.00% | USD -151,335.97 | USD -240,755.55 |
| -50% | 0/36 | 0.00% | USD -97,185.79 | USD -155,187.55 |
| -40% | 0/36 | 0.00% | USD -75,525.71 | USD -120,960.35 |
| -30% | 0/36 | 0.00% | USD -53,865.64 | USD -86,733.15 |
| -25% | 0/36 | 0.00% | USD -43,035.60 | USD -70,306.30 |
| -20% | 0/36 | 0.00% | USD -32,205.56 | USD -54,098.75 |
| -15% | 0/36 | 0.00% | USD -21,375.52 | USD -37,891.20 |
| -10% | 1/36 | 2.78% | USD -10,558.73 | USD -23,103.25 |
| -5% | 19/36 | 52.78% | USD -434.91 | USD -8,803.90 |
| 0% | 36/36 | 100.00% | USD 2,279.12 | USD 858.45 |
| 5% | 36/36 | 100.00% | USD 2,279.12 | USD 858.45 |
| 10% | 36/36 | 100.00% | USD 2,279.12 | USD 858.45 |
| 20% | 36/36 | 100.00% | USD 2,279.12 | USD 858.45 |

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