# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.61 / USD 1,325.85; mean absolute mismatch USD 878.24; mean match score 33.37%.
- Actual selected contract ratios: {'1:3': 390}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 390; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 389/390 | 258/131/0 | 66.32% (61.49–70.84%) | USD 18.43 | USD 150.80 | USD 7,168.20 | USD -7,423.20 | 1 |
| HOLD_10_SESSIONS | 388/390 | 293/95/0 | 75.52% (71.00–79.53%) | USD 72.90 | USD 313.30 | USD 28,283.40 | USD -10,501.20 | 2 |
| HOLD_20_SESSIONS | 386/390 | 316/70/0 | 81.87% (77.71–85.39%) | USD 178.65 | USD 531.30 | USD 68,957.80 | USD -21,325.20 | 4 |
| EXIT_AT_DTE_LE_7 | 343/390 | 288/55/0 | 83.97% (79.71–87.47%) | USD 198.52 | USD 638.80 | USD 68,093.40 | USD -19,363.20 | 47 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -50.26 | USD 113.89 |
| HOLD_10_SESSIONS | USD -84.64 | USD 202.74 |
| HOLD_20_SESSIONS | USD -154.97 | USD 378.82 |
| EXIT_AT_DTE_LE_7 | USD -188.69 | USD 432.41 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 389 | 70.69% | USD 63.63 | USD 24,751.00 | USD -7,378.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 389 | 70.18% | USD 58.43 | USD 22,728.20 | USD -7,383.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 389 | 69.15% | USD 43.63 | USD 16,971.00 | USD -7,398.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 389 | 68.12% | USD 38.43 | USD 14,948.20 | USD -7,403.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 389 | 66.58% | USD 23.63 | USD 9,191.00 | USD -7,418.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 389 | 66.32% | USD 18.43 | USD 7,168.20 | USD -7,423.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 389 | 63.75% | USD -16.37 | USD -6,369.00 | USD -7,458.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 389 | 63.24% | USD -21.57 | USD -8,391.80 | USD -7,463.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 388 | 76.80% | USD 118.10 | USD 45,821.00 | USD -10,456.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 388 | 76.55% | USD 112.90 | USD 43,803.40 | USD -10,461.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 388 | 76.03% | USD 98.10 | USD 38,061.00 | USD -10,476.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 388 | 75.77% | USD 92.90 | USD 36,043.40 | USD -10,481.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 388 | 75.52% | USD 78.10 | USD 30,301.00 | USD -10,496.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 388 | 75.52% | USD 72.90 | USD 28,283.40 | USD -10,501.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 388 | 73.45% | USD 38.10 | USD 14,781.00 | USD -10,536.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 388 | 73.20% | USD 32.90 | USD 12,763.40 | USD -10,541.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 386 | 82.38% | USD 223.85 | USD 86,405.00 | USD -21,280.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 386 | 82.12% | USD 218.65 | USD 84,397.80 | USD -21,285.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 386 | 82.12% | USD 203.85 | USD 78,685.00 | USD -21,300.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 386 | 82.12% | USD 198.65 | USD 76,677.80 | USD -21,305.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 386 | 81.87% | USD 183.85 | USD 70,965.00 | USD -21,320.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 386 | 81.87% | USD 178.65 | USD 68,957.80 | USD -21,325.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 386 | 81.35% | USD 143.85 | USD 55,525.00 | USD -21,360.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 386 | 81.35% | USD 138.65 | USD 53,517.80 | USD -21,365.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 343 | 84.26% | USD 243.72 | USD 83,597.00 | USD -19,318.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 343 | 84.26% | USD 238.52 | USD 81,813.40 | USD -19,323.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 343 | 84.26% | USD 223.72 | USD 76,737.00 | USD -19,338.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 343 | 83.97% | USD 218.52 | USD 74,953.40 | USD -19,343.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 343 | 83.97% | USD 203.72 | USD 69,877.00 | USD -19,358.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 343 | 83.97% | USD 198.52 | USD 68,093.40 | USD -19,363.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 343 | 83.97% | USD 163.72 | USD 56,157.00 | USD -19,398.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 343 | 83.67% | USD 158.52 | USD 54,373.40 | USD -19,403.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 389/390 (1) | 34.45% (29.90–39.30%) | USD -34.90 | USD -13,576.40 | USD -813.60 |
| HOLD_5_SESSIONS | 1 : 6 | 389/390 (1) | 68.38% (63.60–72.80%) | USD 98.42 | USD 38,285.10 | USD -17,582.10 |
| HOLD_5_SESSIONS | 6 : 1 | 389/390 (1) | 26.22% (22.10–30.81%) | USD -342.72 | USD -133,319.90 | USD -7,478.10 |
| HOLD_5_SESSIONS | 4 : 5 | 389/390 (1) | 46.79% (41.88–51.75%) | USD -112.94 | USD -43,933.30 | USD -5,988.70 |
| HOLD_10_SESSIONS | 1 : 1 | 388/390 (2) | 32.73% (28.25–37.55%) | USD -39.66 | USD -15,389.80 | USD -2,062.60 |
| HOLD_10_SESSIONS | 1 : 6 | 388/390 (2) | 76.55% (72.08–80.49%) | USD 241.74 | USD 93,793.20 | USD -23,159.10 |
| HOLD_10_SESSIONS | 6 : 1 | 388/390 (2) | 23.71% (19.75–28.19%) | USD -519.39 | USD -201,521.80 | USD -7,189.10 |
| HOLD_10_SESSIONS | 4 : 5 | 388/390 (2) | 57.73% (52.76–62.55%) | USD -102.38 | USD -39,722.60 | USD -12,469.70 |
| HOLD_20_SESSIONS | 1 : 1 | 386/390 (4) | 35.75% (31.13–40.65%) | USD -51.30 | USD -19,800.60 | USD -4,028.60 |
| HOLD_20_SESSIONS | 1 : 6 | 386/390 (4) | 80.83% (76.61–84.44%) | USD 523.56 | USD 202,095.40 | USD -47,270.10 |
| HOLD_20_SESSIONS | 6 : 1 | 386/390 (4) | 15.80% (12.50–19.78%) | USD -882.64 | USD -340,699.60 | USD -10,258.10 |
| HOLD_20_SESSIONS | 4 : 5 | 386/390 (4) | 70.47% (65.73–74.80%) | USD -90.22 | USD -34,823.20 | USD -24,762.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 343/390 (47) | 32.94% (28.18–38.08%) | USD -67.15 | USD -23,032.80 | USD -3,886.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 343/390 (47) | 83.38% (79.08–86.95%) | USD 597.03 | USD 204,782.70 | USD -42,814.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 343/390 (47) | 14.58% (11.24–18.70%) | USD -1,067.09 | USD -366,012.30 | USD -10,358.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 343/390 (47) | 72.59% (67.64–77.05%) | USD -135.77 | USD -46,568.10 | USD -23,284.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/390 | 0.00% | USD -87,099.02 | USD -138,393.60 |
| -75% | 0/390 | 0.00% | USD -64,253.39 | USD -102,965.85 |
| -50% | 0/390 | 0.00% | USD -41,407.77 | USD -67,538.10 |
| -40% | 0/390 | 0.00% | USD -32,269.52 | USD -53,367.00 |
| -30% | 0/390 | 0.00% | USD -23,131.27 | USD -39,195.90 |
| -25% | 0/390 | 0.00% | USD -18,562.15 | USD -32,110.35 |
| -20% | 2/390 | 0.51% | USD -13,993.02 | USD -25,024.80 |
| -15% | 3/390 | 0.77% | USD -9,439.55 | USD -17,939.25 |
| -10% | 10/390 | 2.56% | USD -4,893.44 | USD -10,853.70 |
| -5% | 159/390 | 40.77% | USD -543.11 | USD -3,922.85 |
| 0% | 390/390 | 100.00% | USD 854.73 | USD 221.40 |
| 5% | 390/390 | 100.00% | USD 855.64 | USD 221.40 |
| 10% | 390/390 | 100.00% | USD 855.64 | USD 221.40 |
| 20% | 390/390 | 100.00% | USD 855.64 | USD 221.40 |

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