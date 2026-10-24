# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,794.92 / USD 2,216.54; mean absolute mismatch USD 455.57; mean match score 78.96%.
- Actual selected contract ratios: {'4:5': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 192/199/0 | 49.10% (44.18–54.04%) | USD -127.57 | USD -6.70 | USD -49,879.70 | USD -7,766.70 | 1 |
| HOLD_10_SESSIONS | 389/392 | 227/162/0 | 58.35% (53.40–63.15%) | USD -124.43 | USD 66.30 | USD -48,403.30 | USD -20,070.70 | 3 |
| HOLD_20_SESSIONS | 384/392 | 276/108/0 | 71.88% (67.18–76.14%) | USD -106.13 | USD 203.80 | USD -40,752.80 | USD -26,594.70 | 8 |
| EXIT_AT_DTE_LE_7 | 342/392 | 246/96/0 | 71.93% (66.94–76.43%) | USD -202.67 | USD 230.30 | USD -69,313.40 | USD -26,385.70 | 50 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -296.57 | USD 270.70 |
| HOLD_10_SESSIONS | USD -415.10 | USD 392.37 |
| HOLD_20_SESSIONS | USD -700.00 | USD 695.57 |
| EXIT_AT_DTE_LE_7 | USD -735.71 | USD 634.74 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 59.34% | USD -25.87 | USD -10,115.00 | USD -7,665.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 58.82% | USD -37.57 | USD -14,689.70 | USD -7,676.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 55.50% | USD -70.87 | USD -27,710.00 | USD -7,710.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 54.99% | USD -82.57 | USD -32,284.70 | USD -7,721.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 50.90% | USD -115.87 | USD -45,305.00 | USD -7,755.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 49.10% | USD -127.57 | USD -49,879.70 | USD -7,766.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 38.36% | USD -205.87 | USD -80,495.00 | USD -7,845.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 37.08% | USD -217.57 | USD -85,069.70 | USD -7,856.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 389 | 66.84% | USD -22.73 | USD -8,842.00 | USD -19,969.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 389 | 66.07% | USD -34.43 | USD -13,393.30 | USD -19,980.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 389 | 63.75% | USD -67.73 | USD -26,347.00 | USD -20,014.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 389 | 62.72% | USD -79.43 | USD -30,898.30 | USD -20,025.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 389 | 58.87% | USD -112.73 | USD -43,852.00 | USD -20,059.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 389 | 58.35% | USD -124.43 | USD -48,403.30 | USD -20,070.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 389 | 48.07% | USD -202.73 | USD -78,862.00 | USD -20,149.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 389 | 46.79% | USD -214.43 | USD -83,413.30 | USD -20,160.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 384 | 77.86% | USD -4.43 | USD -1,700.00 | USD -26,493.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 384 | 77.60% | USD -16.13 | USD -6,192.80 | USD -26,504.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 384 | 75.26% | USD -49.43 | USD -18,980.00 | USD -26,538.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 384 | 75.00% | USD -61.13 | USD -23,472.80 | USD -26,549.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 384 | 72.14% | USD -94.43 | USD -36,260.00 | USD -26,583.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 384 | 71.88% | USD -106.13 | USD -40,752.80 | USD -26,594.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 384 | 63.28% | USD -184.43 | USD -70,820.00 | USD -26,673.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 384 | 62.50% | USD -196.13 | USD -75,312.80 | USD -26,684.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 342 | 79.24% | USD -100.97 | USD -34,532.00 | USD -26,284.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 342 | 78.36% | USD -112.67 | USD -38,533.40 | USD -26,295.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 342 | 76.32% | USD -145.97 | USD -49,922.00 | USD -26,329.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 342 | 75.44% | USD -157.67 | USD -53,923.40 | USD -26,340.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 342 | 73.39% | USD -190.97 | USD -65,312.00 | USD -26,374.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 342 | 71.93% | USD -202.67 | USD -69,313.40 | USD -26,385.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 342 | 65.50% | USD -280.97 | USD -96,092.00 | USD -26,464.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 342 | 63.74% | USD -292.67 | USD -100,093.40 | USD -26,475.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 32.48% (28.03–37.27%) | USD -42.60 | USD -16,657.60 | USD -1,278.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 69.57% (64.83–73.92%) | USD 171.60 | USD 67,095.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 24.30% (20.31–28.78%) | USD -469.82 | USD -183,699.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 391/392 (1) | 49.10% (44.18–54.04%) | USD -127.57 | USD -49,879.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 389/392 (3) | 37.28% (32.62–42.18%) | USD -47.90 | USD -18,633.40 | USD -3,518.60 |
| HOLD_10_SESSIONS | 1 : 6 | 389/392 (3) | 75.84% (71.34–79.82%) | USD 287.96 | USD 112,018.10 | USD -33,500.10 |
| HOLD_10_SESSIONS | 6 : 1 | 389/392 (3) | 21.08% (17.32–25.41%) | USD -623.27 | USD -242,451.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 389/392 (3) | 58.35% (53.40–63.15%) | USD -124.43 | USD -48,403.30 | USD -20,070.70 |
| HOLD_20_SESSIONS | 1 : 1 | 384/392 (8) | 41.67% (36.84–46.66%) | USD -58.49 | USD -22,458.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 384/392 (8) | 83.59% (79.56–86.96%) | USD 580.59 | USD 222,945.60 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 384/392 (8) | 15.36% (12.10–19.31%) | USD -989.99 | USD -380,154.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 384/392 (8) | 71.88% (67.18–76.14%) | USD -106.13 | USD -40,752.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 342/392 (50) | 38.89% (33.87–44.15%) | USD -79.58 | USD -27,216.20 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 342/392 (50) | 83.92% (79.65–87.43%) | USD 498.66 | USD 170,540.80 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 342/392 (50) | 16.08% (12.57–20.35%) | USD -1,055.71 | USD -361,054.20 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 342/392 (50) | 71.93% (66.94–76.43%) | USD -202.67 | USD -69,313.40 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -73,115.94 | USD -94,413.85 |
| -75% | 0/392 | 0.00% | USD -54,295.50 | USD -70,612.10 |
| -50% | 0/392 | 0.00% | USD -35,475.06 | USD -46,810.35 |
| -40% | 0/392 | 0.00% | USD -27,946.89 | USD -37,334.65 |
| -30% | 0/392 | 0.00% | USD -20,418.71 | USD -28,023.95 |
| -25% | 0/392 | 0.00% | USD -16,654.62 | USD -23,368.60 |
| -20% | 1/392 | 0.26% | USD -12,890.54 | USD -18,713.25 |
| -15% | 3/392 | 0.77% | USD -9,129.67 | USD -14,122.35 |
| -10% | 10/392 | 2.55% | USD -5,388.09 | USD -9,710.85 |
| -5% | 117/392 | 29.85% | USD -1,399.98 | USD -5,363.35 |
| 0% | 352/392 | 89.80% | USD 371.47 | USD -1,944.85 |
| 5% | 352/392 | 89.80% | USD 370.77 | USD -1,944.85 |
| 10% | 352/392 | 89.80% | USD 370.77 | USD -1,944.85 |
| 20% | 352/392 | 89.80% | USD 370.77 | USD -1,944.85 |

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