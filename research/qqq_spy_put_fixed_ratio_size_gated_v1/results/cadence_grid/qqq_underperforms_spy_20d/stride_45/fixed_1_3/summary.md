# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 399 checks; 36 qualified; 363 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 482.83 / USD 1,400.75; mean absolute mismatch USD 917.92; mean match score 34.06%.
- Actual selected contract ratios: {'1:3': 36}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 36; entered cohorts: 36; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 36/36 | 23/13/0 | 63.89% (47.58–77.52%) | USD 140.91 | USD 194.30 | USD 5,072.80 | USD -1,718.20 | 0 |
| HOLD_10_SESSIONS | 36/36 | 29/7/0 | 80.56% (64.97–90.25%) | USD 299.44 | USD 350.80 | USD 10,779.80 | USD -1,570.20 | 0 |
| HOLD_20_SESSIONS | 34/36 | 30/4/0 | 88.24% (73.38–95.33%) | USD 584.62 | USD 502.80 | USD 19,877.20 | USD -1,111.20 | 2 |
| EXIT_AT_DTE_LE_7 | 30/36 | 25/5/0 | 83.33% (66.44–92.66%) | USD 247.60 | USD 550.30 | USD 7,428.00 | USD -3,572.20 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -97.72 | USD 283.83 |
| HOLD_10_SESSIONS | USD -160.11 | USD 504.75 |
| HOLD_20_SESSIONS | USD -299.65 | USD 929.47 |
| EXIT_AT_DTE_LE_7 | USD -169.40 | USD 462.20 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 36 | 72.22% | USD 186.11 | USD 6,700.00 | USD -1,673.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 36 | 72.22% | USD 180.91 | USD 6,512.80 | USD -1,678.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 36 | 66.67% | USD 166.11 | USD 5,980.00 | USD -1,693.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 36 | 63.89% | USD 160.91 | USD 5,792.80 | USD -1,698.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 36 | 63.89% | USD 146.11 | USD 5,260.00 | USD -1,713.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 36 | 63.89% | USD 140.91 | USD 5,072.80 | USD -1,718.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 36 | 63.89% | USD 106.11 | USD 3,820.00 | USD -1,753.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 36 | 63.89% | USD 100.91 | USD 3,632.80 | USD -1,758.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 36 | 83.33% | USD 344.64 | USD 12,407.00 | USD -1,525.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 36 | 83.33% | USD 339.44 | USD 12,219.80 | USD -1,530.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 36 | 83.33% | USD 324.64 | USD 11,687.00 | USD -1,545.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 36 | 83.33% | USD 319.44 | USD 11,499.80 | USD -1,550.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 36 | 83.33% | USD 304.64 | USD 10,967.00 | USD -1,565.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 36 | 80.56% | USD 299.44 | USD 10,779.80 | USD -1,570.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 36 | 80.56% | USD 264.64 | USD 9,527.00 | USD -1,605.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 36 | 77.78% | USD 259.44 | USD 9,339.80 | USD -1,610.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 34 | 88.24% | USD 629.82 | USD 21,414.00 | USD -1,066.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 34 | 88.24% | USD 624.62 | USD 21,237.20 | USD -1,071.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 34 | 88.24% | USD 609.82 | USD 20,734.00 | USD -1,086.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 34 | 88.24% | USD 604.62 | USD 20,557.20 | USD -1,091.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 34 | 88.24% | USD 589.82 | USD 20,054.00 | USD -1,106.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 34 | 88.24% | USD 584.62 | USD 19,877.20 | USD -1,111.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 34 | 88.24% | USD 549.82 | USD 18,694.00 | USD -1,146.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 34 | 88.24% | USD 544.62 | USD 18,517.20 | USD -1,151.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 30 | 83.33% | USD 292.80 | USD 8,784.00 | USD -3,527.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 30 | 83.33% | USD 287.60 | USD 8,628.00 | USD -3,532.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 30 | 83.33% | USD 272.80 | USD 8,184.00 | USD -3,547.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 30 | 83.33% | USD 267.60 | USD 8,028.00 | USD -3,552.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 30 | 83.33% | USD 252.80 | USD 7,584.00 | USD -3,567.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 30 | 83.33% | USD 247.60 | USD 7,428.00 | USD -3,572.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 30 | 83.33% | USD 212.80 | USD 6,384.00 | USD -3,607.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 30 | 83.33% | USD 207.60 | USD 6,228.00 | USD -3,612.20 |

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
| -100% | 0/36 | 0.00% | USD -87,303.29 | USD -134,816.60 |
| -75% | 0/36 | 0.00% | USD -64,360.77 | USD -99,643.35 |
| -50% | 0/36 | 0.00% | USD -41,418.25 | USD -64,470.10 |
| -40% | 0/36 | 0.00% | USD -32,241.24 | USD -50,400.80 |
| -30% | 0/36 | 0.00% | USD -23,064.24 | USD -36,331.50 |
| -25% | 0/36 | 0.00% | USD -18,475.73 | USD -29,296.85 |
| -20% | 0/36 | 0.00% | USD -13,887.23 | USD -22,604.60 |
| -15% | 0/36 | 0.00% | USD -9,298.72 | USD -15,913.35 |
| -10% | 1/36 | 2.78% | USD -4,713.54 | USD -9,744.10 |
| -5% | 18/36 | 50.00% | USD -350.09 | USD -3,798.85 |
| 0% | 36/36 | 100.00% | USD 895.32 | USD 347.40 |
| 5% | 36/36 | 100.00% | USD 895.32 | USD 347.40 |
| 10% | 36/36 | 100.00% | USD 895.32 | USD 347.40 |
| 20% | 36/36 | 100.00% | USD 895.32 | USD 347.40 |

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