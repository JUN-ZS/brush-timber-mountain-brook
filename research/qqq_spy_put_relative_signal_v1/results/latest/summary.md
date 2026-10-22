# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 399 checks; 36 qualified; 363 rejected (includes insufficient lookback).
- Position sizing: match LONG QQQ PUT premium debit to SHORT SPY PUT premium credit per cohort; whole-contract ratio varies by entry; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean premium debit/credit: USD 1,777.83 / USD 1,776.75; mean absolute mismatch USD 71.42; mean match score 95.60%.
- Actual selected contract ratios: {'1:1': 1, '3:3': 7, '3:4': 1, '3:5': 1, '4:3': 3, '4:4': 12, '4:5': 6, '5:4': 5}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 36; entered cohorts: 36; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 36/36 | 9/27/0 | 25.00% (13.75–41.07%) | USD -179.29 | USD -180.40 | USD -6,454.50 | USD -1,009.40 | 0 |
| HOLD_10_SESSIONS | 36/36 | 7/29/0 | 19.44% (9.75–35.03%) | USD -126.88 | USD -165.20 | USD -4,567.50 | USD -514.40 | 0 |
| HOLD_20_SESSIONS | 34/36 | 10/24/0 | 29.41% (16.83–46.17%) | USD -52.43 | USD -94.25 | USD -1,782.50 | USD -1,147.80 | 2 |
| EXIT_AT_DTE_LE_7 | 30/36 | 8/22/0 | 26.67% (14.18–44.45%) | USD -93.03 | USD -90.40 | USD -2,790.90 | USD -2,287.80 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -432.19 | USD 339.22 |
| HOLD_10_SESSIONS | USD -639.31 | USD 598.75 |
| HOLD_20_SESSIONS | USD -1,249.15 | USD 1,284.79 |
| EXIT_AT_DTE_LE_7 | USD -705.97 | USD 700.70 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 36 | 30.56% | USD -92.97 | USD -3,347.00 | USD -919.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 36 | 27.78% | USD -102.90 | USD -3,704.50 | USD -929.40 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 36 | 27.78% | USD -131.17 | USD -4,722.00 | USD -959.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 36 | 27.78% | USD -141.10 | USD -5,079.50 | USD -969.40 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 36 | 25.00% | USD -169.36 | USD -6,097.00 | USD -999.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 36 | 25.00% | USD -179.29 | USD -6,454.50 | USD -1,009.40 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 36 | 13.89% | USD -245.75 | USD -8,847.00 | USD -1,079.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 36 | 13.89% | USD -255.68 | USD -9,204.50 | USD -1,089.40 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 36 | 25.00% | USD -40.56 | USD -1,460.00 | USD -424.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 36 | 22.22% | USD -50.49 | USD -1,817.50 | USD -434.40 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 36 | 22.22% | USD -78.75 | USD -2,835.00 | USD -464.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 36 | 19.44% | USD -88.68 | USD -3,192.50 | USD -474.40 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 36 | 19.44% | USD -116.94 | USD -4,210.00 | USD -504.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 36 | 19.44% | USD -126.88 | USD -4,567.50 | USD -514.40 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 36 | 8.33% | USD -193.33 | USD -6,960.00 | USD -584.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 36 | 8.33% | USD -203.26 | USD -7,317.50 | USD -594.40 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 34 | 47.06% | USD 35.65 | USD 1,212.00 | USD -1,080.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 34 | 44.12% | USD 25.51 | USD 867.50 | USD -1,087.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 34 | 38.24% | USD -3.32 | USD -113.00 | USD -1,110.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 34 | 32.35% | USD -13.46 | USD -457.50 | USD -1,117.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 34 | 29.41% | USD -42.29 | USD -1,438.00 | USD -1,140.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 34 | 29.41% | USD -52.43 | USD -1,782.50 | USD -1,147.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 34 | 20.59% | USD -120.24 | USD -4,088.00 | USD -1,200.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 34 | 20.59% | USD -130.37 | USD -4,432.50 | USD -1,207.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 30 | 50.00% | USD -5.27 | USD -158.00 | USD -2,220.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 30 | 40.00% | USD -15.36 | USD -460.90 | USD -2,227.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 30 | 33.33% | USD -44.10 | USD -1,323.00 | USD -2,250.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 30 | 33.33% | USD -54.20 | USD -1,625.90 | USD -2,257.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 30 | 26.67% | USD -82.93 | USD -2,488.00 | USD -2,280.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 30 | 26.67% | USD -93.03 | USD -2,790.90 | USD -2,287.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 30 | 16.67% | USD -160.60 | USD -4,818.00 | USD -2,340.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 30 | 16.67% | USD -170.70 | USD -5,120.90 | USD -2,347.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 36/36 (0) | 33.33% (20.21–49.67%) | USD -25.46 | USD -916.60 | USD -152.60 |
| HOLD_5_SESSIONS | 1 : 6 | 36/36 (0) | 69.44% (53.14–82.00%) | USD 397.07 | USD 14,294.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -575.29 | USD -20,710.60 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 36/36 (0) | 55.56% (39.58–70.46%) | USD -17.34 | USD -624.20 | USD -787.70 |
| HOLD_10_SESSIONS | 1 : 1 | 36/36 (0) | 36.11% (22.48–52.42%) | USD -14.46 | USD -520.60 | USD -166.60 |
| HOLD_10_SESSIONS | 1 : 6 | 36/36 (0) | 80.56% (64.97–90.25%) | USD 770.29 | USD 27,730.40 | USD -3,830.10 |
| HOLD_10_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -871.52 | USD -31,374.60 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 36/36 (0) | 61.11% (44.86–75.22%) | USD 99.11 | USD 3,567.80 | USD -1,007.70 |
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
| -100% | 1/36 | 2.78% | USD -37,997.02 | USD -131,965.20 |
| -75% | 1/36 | 2.78% | USD -28,425.32 | USD -98,480.45 |
| -50% | 1/36 | 2.78% | USD -18,853.62 | USD -64,995.70 |
| -40% | 1/36 | 2.78% | USD -15,024.94 | USD -51,601.80 |
| -30% | 0/36 | 0.00% | USD -11,196.26 | USD -38,207.90 |
| -25% | 0/36 | 0.00% | USD -9,281.92 | USD -31,510.95 |
| -20% | 0/36 | 0.00% | USD -7,367.58 | USD -24,814.00 |
| -15% | 0/36 | 0.00% | USD -5,453.24 | USD -18,117.05 |
| -10% | 0/36 | 0.00% | USD -3,522.45 | USD -11,420.10 |
| -5% | 3/36 | 8.33% | USD -1,229.48 | USD -4,723.15 |
| 0% | 11/36 | 30.56% | USD -44.24 | USD -245.20 |
| 5% | 11/36 | 30.56% | USD -44.24 | USD -245.20 |
| 10% | 11/36 | 30.56% | USD -44.24 | USD -245.20 |
| 20% | 11/36 | 30.56% | USD -44.24 | USD -245.20 |

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