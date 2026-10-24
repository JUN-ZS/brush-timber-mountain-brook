# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 44 checks; 44 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 873.09 / USD 1,725.09; mean absolute mismatch USD 852.00; mean match score 49.20%.
- Actual selected contract ratios: {'2:4': 44}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 44; entered cohorts: 44; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 32/12/0 | 72.73% (58.15–83.65%) | USD -155.25 | USD 168.20 | USD -6,831.20 | USD -8,305.80 | 0 |
| HOLD_10_SESSIONS | 44/44 | 32/12/0 | 72.73% (58.15–83.65%) | USD -222.44 | USD 310.20 | USD -9,787.20 | USD -8,717.80 | 0 |
| HOLD_20_SESSIONS | 44/44 | 34/10/0 | 77.27% (63.01–87.16%) | USD -476.94 | USD 570.20 | USD -20,985.20 | USD -27,571.80 | 0 |
| EXIT_AT_DTE_LE_7 | 36/44 | 28/8/0 | 77.78% (61.92–88.28%) | USD -693.24 | USD 684.20 | USD -24,956.80 | USD -20,219.80 | 8 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 0.00 | USD -87.45 |
| HOLD_10_SESSIONS | USD -13.36 | USD -141.27 |
| HOLD_20_SESSIONS | USD -76.77 | USD -332.36 |
| EXIT_AT_DTE_LE_7 | USD 34.11 | USD -659.56 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 44 | 75.00% | USD -87.45 | USD -3,848.00 | USD -8,238.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 44 | 75.00% | USD -95.25 | USD -4,191.20 | USD -8,245.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 44 | 75.00% | USD -117.45 | USD -5,168.00 | USD -8,268.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 44 | 72.73% | USD -125.25 | USD -5,511.20 | USD -8,275.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 44 | 72.73% | USD -147.45 | USD -6,488.00 | USD -8,298.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 44 | 72.73% | USD -155.25 | USD -6,831.20 | USD -8,305.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 44 | 68.18% | USD -207.45 | USD -9,128.00 | USD -8,358.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 44 | 68.18% | USD -215.25 | USD -9,471.20 | USD -8,365.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 44 | 72.73% | USD -154.64 | USD -6,804.00 | USD -8,650.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 44 | 72.73% | USD -162.44 | USD -7,147.20 | USD -8,657.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 44 | 72.73% | USD -184.64 | USD -8,124.00 | USD -8,680.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 44 | 72.73% | USD -192.44 | USD -8,467.20 | USD -8,687.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 44 | 72.73% | USD -214.64 | USD -9,444.00 | USD -8,710.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 44 | 72.73% | USD -222.44 | USD -9,787.20 | USD -8,717.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 44 | 70.45% | USD -274.64 | USD -12,084.00 | USD -8,770.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 44 | 70.45% | USD -282.44 | USD -12,427.20 | USD -8,777.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 44 | 77.27% | USD -409.14 | USD -18,002.00 | USD -27,504.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 44 | 77.27% | USD -416.94 | USD -18,345.20 | USD -27,511.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 44 | 77.27% | USD -439.14 | USD -19,322.00 | USD -27,534.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 44 | 77.27% | USD -446.94 | USD -19,665.20 | USD -27,541.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 44 | 77.27% | USD -469.14 | USD -20,642.00 | USD -27,564.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 44 | 77.27% | USD -476.94 | USD -20,985.20 | USD -27,571.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 44 | 77.27% | USD -529.14 | USD -23,282.00 | USD -27,624.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 44 | 77.27% | USD -536.94 | USD -23,625.20 | USD -27,631.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 36 | 77.78% | USD -625.44 | USD -22,516.00 | USD -20,152.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 36 | 77.78% | USD -633.24 | USD -22,796.80 | USD -20,159.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 36 | 77.78% | USD -655.44 | USD -23,596.00 | USD -20,182.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 36 | 77.78% | USD -663.24 | USD -23,876.80 | USD -20,189.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 36 | 77.78% | USD -685.44 | USD -24,676.00 | USD -20,212.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 36 | 77.78% | USD -693.24 | USD -24,956.80 | USD -20,219.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 36 | 77.78% | USD -745.44 | USD -26,836.00 | USD -20,272.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 36 | 77.78% | USD -753.24 | USD -27,116.80 | USD -20,279.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 44/44 (0) | 38.64% (25.72–53.38%) | USD -44.46 | USD -1,956.40 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -210.28 | USD -9,252.40 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 44/44 (0) | 22.73% (12.84–36.99%) | USD -100.96 | USD -4,442.40 | USD -2,665.10 |
| HOLD_5_SESSIONS | 4 : 5 | 44/44 (0) | 56.82% (42.22–70.32%) | USD -211.02 | USD -9,284.80 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 44/44 (0) | 45.45% (31.71–59.93%) | USD -64.60 | USD -2,842.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -297.69 | USD -13,098.40 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 44/44 (0) | 20.45% (11.15–34.50%) | USD -154.51 | USD -6,798.40 | USD -2,949.10 |
| HOLD_10_SESSIONS | 4 : 5 | 44/44 (0) | 61.36% (46.62–74.28%) | USD -305.02 | USD -13,420.80 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 44/44 (0) | 40.91% (27.69–55.59%) | USD -144.08 | USD -6,339.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 44/44 (0) | 79.55% (65.50–88.85%) | USD -616.03 | USD -27,105.40 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 44/44 (0) | 18.18% (9.51–31.96%) | USD -392.51 | USD -17,270.40 | USD -4,371.10 |
| HOLD_20_SESSIONS | 4 : 5 | 44/44 (0) | 70.45% (55.78–81.84%) | USD -670.70 | USD -29,510.80 | USD -26,594.70 |
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
| -100% | 0/44 | 0.00% | USD -95,436.17 | USD -143,109.90 |
| -75% | 0/44 | 0.00% | USD -70,496.30 | USD -105,888.40 |
| -50% | 0/44 | 0.00% | USD -45,556.42 | USD -68,666.90 |
| -40% | 0/44 | 0.00% | USD -35,580.47 | USD -53,778.30 |
| -30% | 0/44 | 0.00% | USD -25,604.52 | USD -38,889.70 |
| -25% | 0/44 | 0.00% | USD -20,616.55 | USD -31,517.40 |
| -20% | 0/44 | 0.00% | USD -15,628.57 | USD -24,315.90 |
| -15% | 0/44 | 0.00% | USD -10,640.60 | USD -17,114.40 |
| -10% | 2/44 | 4.55% | USD -5,626.83 | USD -10,189.50 |
| -5% | 18/44 | 40.91% | USD -785.19 | USD -3,879.60 |
| 0% | 44/44 | 100.00% | USD 818.10 | USD 270.10 |
| 5% | 44/44 | 100.00% | USD 818.10 | USD 270.10 |
| 10% | 44/44 | 100.00% | USD 818.10 | USD 270.10 |
| 20% | 44/44 | 100.00% | USD 818.10 | USD 270.10 |

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