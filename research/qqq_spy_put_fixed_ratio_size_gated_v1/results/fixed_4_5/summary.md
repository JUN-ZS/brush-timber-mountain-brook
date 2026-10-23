# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 399 checks; 36 qualified; 363 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,946.22 / USD 2,361.81; mean absolute mismatch USD 475.25; mean match score 79.71%.
- Actual selected contract ratios: {'4:5': 36}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 36; entered cohorts: 36; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 36/36 | 21/15/0 | 58.33% (42.20–72.86%) | USD 5.27 | USD 22.80 | USD 189.80 | USD -787.70 | 0 |
| HOLD_10_SESSIONS | 36/36 | 23/13/0 | 63.89% (47.58–77.52%) | USD 113.63 | USD 96.80 | USD 4,090.80 | USD -1,007.70 | 0 |
| HOLD_20_SESSIONS | 34/36 | 25/9/0 | 73.53% (56.88–85.40%) | USD 241.62 | USD 230.30 | USD 8,215.20 | USD -1,894.70 | 2 |
| EXIT_AT_DTE_LE_7 | 30/36 | 21/9/0 | 70.00% (52.12–83.34%) | USD -6.20 | USD 169.80 | USD -186.00 | USD -4,303.70 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -441.78 | USD 548.75 |
| HOLD_10_SESSIONS | USD -659.67 | USD 875.00 |
| HOLD_20_SESSIONS | USD -1,245.06 | USD 1,588.38 |
| EXIT_AT_DTE_LE_7 | USD -682.00 | USD 777.50 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 36 | 61.11% | USD 106.97 | USD 3,851.00 | USD -686.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 36 | 61.11% | USD 95.27 | USD 3,429.80 | USD -697.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 36 | 61.11% | USD 61.97 | USD 2,231.00 | USD -731.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 36 | 61.11% | USD 50.27 | USD 1,809.80 | USD -742.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 36 | 61.11% | USD 16.97 | USD 611.00 | USD -776.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 36 | 58.33% | USD 5.27 | USD 189.80 | USD -787.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 36 | 41.67% | USD -73.03 | USD -2,629.00 | USD -866.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 36 | 41.67% | USD -84.73 | USD -3,050.20 | USD -877.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 36 | 66.67% | USD 215.33 | USD 7,752.00 | USD -906.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 36 | 66.67% | USD 203.63 | USD 7,330.80 | USD -917.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 36 | 66.67% | USD 170.33 | USD 6,132.00 | USD -951.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 36 | 63.89% | USD 158.63 | USD 5,710.80 | USD -962.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 36 | 63.89% | USD 125.33 | USD 4,512.00 | USD -996.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 36 | 63.89% | USD 113.63 | USD 4,090.80 | USD -1,007.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 36 | 55.56% | USD 35.33 | USD 1,272.00 | USD -1,086.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 36 | 50.00% | USD 23.63 | USD 850.80 | USD -1,097.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 34 | 76.47% | USD 343.32 | USD 11,673.00 | USD -1,793.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 34 | 76.47% | USD 331.62 | USD 11,275.20 | USD -1,804.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 34 | 76.47% | USD 298.32 | USD 10,143.00 | USD -1,838.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 34 | 76.47% | USD 286.62 | USD 9,745.20 | USD -1,849.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 34 | 73.53% | USD 253.32 | USD 8,613.00 | USD -1,883.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 34 | 73.53% | USD 241.62 | USD 8,215.20 | USD -1,894.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 34 | 67.65% | USD 163.32 | USD 5,553.00 | USD -1,973.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 34 | 67.65% | USD 151.62 | USD 5,155.20 | USD -1,984.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 30 | 76.67% | USD 95.50 | USD 2,865.00 | USD -4,202.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 30 | 76.67% | USD 83.80 | USD 2,514.00 | USD -4,213.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 30 | 73.33% | USD 50.50 | USD 1,515.00 | USD -4,247.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 30 | 73.33% | USD 38.80 | USD 1,164.00 | USD -4,258.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 30 | 70.00% | USD 5.50 | USD 165.00 | USD -4,292.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 30 | 70.00% | USD -6.20 | USD -186.00 | USD -4,303.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 30 | 60.00% | USD -84.50 | USD -2,535.00 | USD -4,382.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 30 | 60.00% | USD -96.20 | USD -2,886.00 | USD -4,393.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 36/36 (0) | 33.33% (20.21–49.67%) | USD -23.29 | USD -838.60 | USD -152.60 |
| HOLD_5_SESSIONS | 1 : 6 | 36/36 (0) | 69.44% (53.14–82.00%) | USD 468.96 | USD 16,882.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -632.02 | USD -22,752.60 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 36/36 (0) | 58.33% (42.20–72.86%) | USD 5.27 | USD 189.80 | USD -787.70 |
| HOLD_10_SESSIONS | 1 : 1 | 36/36 (0) | 36.11% (22.48–52.42%) | USD -12.52 | USD -450.60 | USD -143.60 |
| HOLD_10_SESSIONS | 1 : 6 | 36/36 (0) | 80.56% (64.97–90.25%) | USD 805.98 | USD 29,015.40 | USD -3,830.10 |
| HOLD_10_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -893.60 | USD -32,169.60 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 36/36 (0) | 63.89% (47.58–77.52%) | USD 113.63 | USD 4,090.80 | USD -1,007.70 |
| HOLD_20_SESSIONS | 1 : 1 | 34/36 (2) | 38.24% (23.90–54.96%) | USD -16.19 | USD -550.40 | USD -382.60 |
| HOLD_20_SESSIONS | 1 : 6 | 34/36 (2) | 88.24% (73.38–95.33%) | USD 1,515.69 | USD 51,533.60 | USD -2,204.10 |
| HOLD_20_SESSIONS | 6 : 1 | 34/36 (2) | 5.88% (1.63–19.09%) | USD -1,629.01 | USD -55,386.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 34/36 (2) | 73.53% (56.88–85.40%) | USD 241.62 | USD 8,215.20 | USD -1,894.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 30/36 (6) | 36.67% (21.87–54.49%) | USD -37.60 | USD -1,128.00 | USD -762.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 30/36 (6) | 80.00% (62.69–90.49%) | USD 683.40 | USD 20,502.00 | USD -8,997.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 30/36 (6) | 16.67% (7.34–33.56%) | USD -946.60 | USD -28,398.00 | USD -4,765.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 30/36 (6) | 70.00% (52.12–83.34%) | USD -6.20 | USD -186.00 | USD -4,303.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/36 | 0.00% | USD -73,440.82 | USD -94,322.85 |
| -75% | 0/36 | 0.00% | USD -54,495.92 | USD -70,290.60 |
| -50% | 0/36 | 0.00% | USD -35,551.02 | USD -46,287.35 |
| -40% | 0/36 | 0.00% | USD -27,973.06 | USD -37,150.25 |
| -30% | 0/36 | 0.00% | USD -20,395.09 | USD -28,013.15 |
| -25% | 0/36 | 0.00% | USD -16,606.11 | USD -23,444.60 |
| -20% | 0/36 | 0.00% | USD -12,817.13 | USD -18,876.05 |
| -15% | 0/36 | 0.00% | USD -9,028.15 | USD -14,307.50 |
| -10% | 1/36 | 2.78% | USD -5,229.33 | USD -9,738.95 |
| -5% | 12/36 | 33.33% | USD -1,255.79 | USD -5,170.40 |
| 0% | 31/36 | 86.11% | USD 364.73 | USD -990.85 |
| 5% | 31/36 | 86.11% | USD 364.73 | USD -990.85 |
| 10% | 31/36 | 86.11% | USD 364.73 | USD -990.85 |
| 20% | 31/36 | 86.11% | USD 364.73 | USD -990.85 |

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