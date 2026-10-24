# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 44 checks; 44 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,746.18 / USD 2,156.36; mean absolute mismatch USD 433.91; mean match score 77.76%.
- Actual selected contract ratios: {'4:5': 44}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 44; entered cohorts: 44; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 25/19/0 | 56.82% (42.22–70.32%) | USD -206.63 | USD 46.80 | USD -9,091.80 | USD -7,766.70 | 0 |
| HOLD_10_SESSIONS | 44/44 | 27/17/0 | 61.36% (46.62–74.28%) | USD -305.02 | USD 139.80 | USD -13,420.80 | USD -8,413.70 | 0 |
| HOLD_20_SESSIONS | 44/44 | 31/13/0 | 70.45% (55.78–81.84%) | USD -672.20 | USD 209.30 | USD -29,576.80 | USD -26,594.70 | 0 |
| EXIT_AT_DTE_LE_7 | 36/44 | 28/8/0 | 77.78% (61.92–88.28%) | USD -857.92 | USD 218.30 | USD -30,885.20 | USD -20,239.70 | 8 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -3.45 | USD -101.48 |
| HOLD_10_SESSIONS | USD -26.73 | USD -176.59 |
| HOLD_20_SESSIONS | USD -157.55 | USD -412.95 |
| EXIT_AT_DTE_LE_7 | USD 68.22 | USD -824.44 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 44 | 65.91% | USD -104.93 | USD -4,617.00 | USD -7,665.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 44 | 65.91% | USD -116.63 | USD -5,131.80 | USD -7,676.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 44 | 61.36% | USD -149.93 | USD -6,597.00 | USD -7,710.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 44 | 61.36% | USD -161.63 | USD -7,111.80 | USD -7,721.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 44 | 56.82% | USD -194.93 | USD -8,577.00 | USD -7,755.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 44 | 56.82% | USD -206.63 | USD -9,091.80 | USD -7,766.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 44 | 40.91% | USD -284.93 | USD -12,537.00 | USD -7,845.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 44 | 40.91% | USD -296.63 | USD -13,051.80 | USD -7,856.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 44 | 65.91% | USD -203.32 | USD -8,946.00 | USD -8,312.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 44 | 65.91% | USD -215.02 | USD -9,460.80 | USD -8,323.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 44 | 65.91% | USD -248.32 | USD -10,926.00 | USD -8,357.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 44 | 65.91% | USD -260.02 | USD -11,440.80 | USD -8,368.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 44 | 61.36% | USD -293.32 | USD -12,906.00 | USD -8,402.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 44 | 61.36% | USD -305.02 | USD -13,420.80 | USD -8,413.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 44 | 54.55% | USD -383.32 | USD -16,866.00 | USD -8,492.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 44 | 54.55% | USD -395.02 | USD -17,380.80 | USD -8,503.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 44 | 75.00% | USD -570.50 | USD -25,102.00 | USD -26,493.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 44 | 75.00% | USD -582.20 | USD -25,616.80 | USD -26,504.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 44 | 72.73% | USD -615.50 | USD -27,082.00 | USD -26,538.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 44 | 72.73% | USD -627.20 | USD -27,596.80 | USD -26,549.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 44 | 70.45% | USD -660.50 | USD -29,062.00 | USD -26,583.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 44 | 70.45% | USD -672.20 | USD -29,576.80 | USD -26,594.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 44 | 61.36% | USD -750.50 | USD -33,022.00 | USD -26,673.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 44 | 61.36% | USD -762.20 | USD -33,536.80 | USD -26,684.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 36 | 80.56% | USD -756.22 | USD -27,224.00 | USD -20,138.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 36 | 80.56% | USD -767.92 | USD -27,645.20 | USD -20,149.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 36 | 77.78% | USD -801.22 | USD -28,844.00 | USD -20,183.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 36 | 77.78% | USD -812.92 | USD -29,265.20 | USD -20,194.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 36 | 77.78% | USD -846.22 | USD -30,464.00 | USD -20,228.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 36 | 77.78% | USD -857.92 | USD -30,885.20 | USD -20,239.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 36 | 66.67% | USD -936.22 | USD -33,704.00 | USD -20,318.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 36 | 66.67% | USD -947.92 | USD -34,125.20 | USD -20,329.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 44/44 (0) | 38.64% (25.72–53.38%) | USD -43.76 | USD -1,925.40 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -201.74 | USD -8,876.40 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 44/44 (0) | 22.73% (12.84–36.99%) | USD -104.58 | USD -4,601.40 | USD -2,665.10 |
| HOLD_5_SESSIONS | 4 : 5 | 44/44 (0) | 56.82% (42.22–70.32%) | USD -206.63 | USD -9,091.80 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 44/44 (0) | 45.45% (31.71–59.93%) | USD -64.60 | USD -2,842.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -297.69 | USD -13,098.40 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 44/44 (0) | 20.45% (11.15–34.50%) | USD -154.51 | USD -6,798.40 | USD -2,949.10 |
| HOLD_10_SESSIONS | 4 : 5 | 44/44 (0) | 61.36% (46.62–74.28%) | USD -305.02 | USD -13,420.80 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 44/44 (0) | 40.91% (27.69–55.59%) | USD -144.58 | USD -6,361.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 44/44 (0) | 79.55% (65.50–88.85%) | USD -614.03 | USD -27,017.40 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 44/44 (0) | 18.18% (9.51–31.96%) | USD -398.01 | USD -17,512.40 | USD -4,371.10 |
| HOLD_20_SESSIONS | 4 : 5 | 44/44 (0) | 70.45% (55.78–81.84%) | USD -672.20 | USD -29,576.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 36/44 (8) | 41.67% (27.14–57.80%) | USD -170.43 | USD -6,135.60 | USD -3,376.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 36/44 (8) | 77.78% (61.92–88.28%) | USD -1,051.38 | USD -37,849.60 | USD -37,043.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 36/44 (8) | 25.00% (13.75–41.07%) | USD -141.66 | USD -5,099.60 | USD -4,415.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 36/44 (8) | 77.78% (61.92–88.28%) | USD -857.92 | USD -30,885.20 | USD -20,239.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/44 | 0.00% | USD -73,124.21 | USD -91,946.85 |
| -75% | 0/44 | 0.00% | USD -54,295.11 | USD -68,706.60 |
| -50% | 0/44 | 0.00% | USD -35,466.01 | USD -45,466.35 |
| -40% | 0/44 | 0.00% | USD -27,934.37 | USD -36,170.25 |
| -30% | 0/44 | 0.00% | USD -20,402.73 | USD -26,874.15 |
| -25% | 0/44 | 0.00% | USD -16,636.91 | USD -22,226.10 |
| -20% | 0/44 | 0.00% | USD -12,871.09 | USD -17,578.05 |
| -15% | 0/44 | 0.00% | USD -9,105.27 | USD -12,930.00 |
| -10% | 1/44 | 2.27% | USD -5,287.85 | USD -8,485.35 |
| -5% | 16/44 | 36.36% | USD -1,284.38 | USD -4,145.45 |
| 0% | 40/44 | 90.91% | USD 359.33 | USD -408.85 |
| 5% | 40/44 | 90.91% | USD 359.33 | USD -408.85 |
| 10% | 40/44 | 90.91% | USD 359.33 | USD -408.85 |
| 20% | 40/44 | 90.91% | USD 359.33 | USD -408.85 |

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