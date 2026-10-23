# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 131 checks; 131 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,811.79 / USD 2,245.57; mean absolute mismatch USD 444.76; mean match score 79.20%.
- Actual selected contract ratios: {'4:5': 131}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 131; entered cohorts: 131; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 131/131 | 66/65/0 | 50.38% (41.93–58.81%) | USD -138.17 | USD 0.30 | USD -18,100.70 | USD -7,766.70 | 0 |
| HOLD_10_SESSIONS | 129/131 | 76/53/0 | 58.91% (50.29–67.03%) | USD -141.95 | USD 71.30 | USD -18,311.30 | USD -8,413.70 | 2 |
| HOLD_20_SESSIONS | 129/131 | 101/28/0 | 78.29% (70.42–84.53%) | USD -119.92 | USD 207.30 | USD -15,469.30 | USD -26,594.70 | 2 |
| EXIT_AT_DTE_LE_7 | 113/131 | 84/29/0 | 74.34% (65.58–81.50%) | USD -301.71 | USD 204.30 | USD -34,093.10 | USD -20,624.70 | 18 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -267.39 | USD 230.92 |
| HOLD_10_SESSIONS | USD -384.90 | USD 344.65 |
| HOLD_20_SESSIONS | USD -672.71 | USD 654.50 |
| EXIT_AT_DTE_LE_7 | USD -515.01 | USD 315.00 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 131 | 61.07% | USD -36.47 | USD -4,778.00 | USD -7,665.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 131 | 60.31% | USD -48.17 | USD -6,310.70 | USD -7,676.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 131 | 56.49% | USD -81.47 | USD -10,673.00 | USD -7,710.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 131 | 55.73% | USD -93.17 | USD -12,205.70 | USD -7,721.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 131 | 51.15% | USD -126.47 | USD -16,568.00 | USD -7,755.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 131 | 50.38% | USD -138.17 | USD -18,100.70 | USD -7,766.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 131 | 41.22% | USD -216.47 | USD -28,358.00 | USD -7,845.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 131 | 39.69% | USD -228.17 | USD -29,890.70 | USD -7,856.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 129 | 67.44% | USD -40.25 | USD -5,192.00 | USD -8,312.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 129 | 67.44% | USD -51.95 | USD -6,701.30 | USD -8,323.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 129 | 65.89% | USD -85.25 | USD -10,997.00 | USD -8,357.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 129 | 65.12% | USD -96.95 | USD -12,506.30 | USD -8,368.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 129 | 59.69% | USD -130.25 | USD -16,802.00 | USD -8,402.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 129 | 58.91% | USD -141.95 | USD -18,311.30 | USD -8,413.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 129 | 49.61% | USD -220.25 | USD -28,412.00 | USD -8,492.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 129 | 48.06% | USD -231.95 | USD -29,921.30 | USD -8,503.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 129 | 81.40% | USD -18.22 | USD -2,350.00 | USD -26,493.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 129 | 80.62% | USD -29.92 | USD -3,859.30 | USD -26,504.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 129 | 79.84% | USD -63.22 | USD -8,155.00 | USD -26,538.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 129 | 79.84% | USD -74.92 | USD -9,664.30 | USD -26,549.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 129 | 78.29% | USD -108.22 | USD -13,960.00 | USD -26,583.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 129 | 78.29% | USD -119.92 | USD -15,469.30 | USD -26,594.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 129 | 67.44% | USD -198.22 | USD -25,570.00 | USD -26,673.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 129 | 67.44% | USD -209.92 | USD -27,079.30 | USD -26,684.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 113 | 82.30% | USD -200.01 | USD -22,601.00 | USD -20,523.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 113 | 80.53% | USD -211.71 | USD -23,923.10 | USD -20,534.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 113 | 76.99% | USD -245.01 | USD -27,686.00 | USD -20,568.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 113 | 75.22% | USD -256.71 | USD -29,008.10 | USD -20,579.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 113 | 74.34% | USD -290.01 | USD -32,771.00 | USD -20,613.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 113 | 74.34% | USD -301.71 | USD -34,093.10 | USD -20,624.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 113 | 67.26% | USD -380.01 | USD -42,941.00 | USD -20,703.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 113 | 65.49% | USD -391.71 | USD -44,263.10 | USD -20,714.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 131/131 (0) | 35.88% (28.17–44.39%) | USD -43.26 | USD -5,667.60 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 131/131 (0) | 72.52% (64.32–79.44%) | USD 131.15 | USD 17,180.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 131/131 (0) | 22.90% (16.54–30.81%) | USD -434.00 | USD -56,854.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 131/131 (0) | 50.38% (41.93–58.81%) | USD -138.17 | USD -18,100.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 129/131 (2) | 36.43% (28.63–45.02%) | USD -49.89 | USD -6,436.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 129/131 (2) | 74.42% (66.26–81.17%) | USD 238.26 | USD 30,735.10 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 129/131 (2) | 19.38% (13.49–27.05%) | USD -587.52 | USD -75,789.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 129/131 (2) | 58.91% (50.29–67.03%) | USD -141.95 | USD -18,311.30 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 129/131 (2) | 40.31% (32.24–48.94%) | USD -59.88 | USD -7,724.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 129/131 (2) | 84.50% (77.26–89.73%) | USD 538.12 | USD 69,417.10 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 129/131 (2) | 16.28% (10.90–23.61%) | USD -957.27 | USD -123,487.90 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 129/131 (2) | 78.29% (70.42–84.53%) | USD -119.92 | USD -15,469.30 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 113/131 (18) | 41.59% (32.93–50.81%) | USD -88.35 | USD -9,983.80 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 113/131 (18) | 84.96% (77.22–90.39%) | USD 170.15 | USD 19,226.70 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 113/131 (18) | 17.70% (11.76–25.76%) | USD -788.61 | USD -89,113.30 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 113/131 (18) | 74.34% (65.58–81.50%) | USD -301.71 | USD -34,093.10 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/131 | 0.00% | USD -72,984.54 | USD -94,322.85 |
| -75% | 0/131 | 0.00% | USD -54,183.65 | USD -70,290.60 |
| -50% | 0/131 | 0.00% | USD -35,382.76 | USD -46,258.35 |
| -40% | 0/131 | 0.00% | USD -27,862.41 | USD -36,967.25 |
| -30% | 0/131 | 0.00% | USD -20,342.05 | USD -27,803.15 |
| -25% | 0/131 | 0.00% | USD -16,581.87 | USD -23,221.10 |
| -20% | 0/131 | 0.00% | USD -12,821.69 | USD -18,639.05 |
| -15% | 1/131 | 0.76% | USD -9,061.51 | USD -14,057.00 |
| -10% | 3/131 | 2.29% | USD -5,300.50 | USD -9,474.95 |
| -5% | 42/131 | 32.06% | USD -1,363.31 | USD -4,944.20 |
| 0% | 118/131 | 90.08% | USD 385.01 | USD -408.85 |
| 5% | 118/131 | 90.08% | USD 382.94 | USD -408.85 |
| 10% | 118/131 | 90.08% | USD 382.94 | USD -408.85 |
| 20% | 118/131 | 90.08% | USD 382.94 | USD -408.85 |

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