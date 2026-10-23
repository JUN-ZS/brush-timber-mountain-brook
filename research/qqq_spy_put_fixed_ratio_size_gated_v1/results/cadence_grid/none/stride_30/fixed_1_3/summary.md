# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 66 checks; 66 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 451.08 / USD 1,345.64; mean absolute mismatch USD 894.56; mean match score 33.29%.
- Actual selected contract ratios: {'1:3': 66}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 66; entered cohorts: 66; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 66/66 | 47/19/0 | 71.21% (59.36–80.73%) | USD 60.60 | USD 223.30 | USD 3,999.80 | USD -1,778.20 | 0 |
| HOLD_10_SESSIONS | 65/66 | 50/15/0 | 76.92% (65.36–85.49%) | USD 129.89 | USD 340.80 | USD 8,443.00 | USD -4,891.20 | 1 |
| HOLD_20_SESSIONS | 65/66 | 55/10/0 | 84.62% (73.94–91.42%) | USD 292.37 | USD 534.80 | USD 19,004.00 | USD -5,230.20 | 1 |
| EXIT_AT_DTE_LE_7 | 62/66 | 53/9/0 | 85.48% (74.66–92.17%) | USD 136.56 | USD 662.80 | USD 8,466.60 | USD -17,039.20 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -94.20 | USD 200.00 |
| HOLD_10_SESSIONS | USD -128.78 | USD 303.88 |
| HOLD_20_SESSIONS | USD -174.14 | USD 511.71 |
| EXIT_AT_DTE_LE_7 | USD -138.23 | USD 319.98 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 66 | 72.73% | USD 105.80 | USD 6,983.00 | USD -1,733.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 66 | 72.73% | USD 100.60 | USD 6,639.80 | USD -1,738.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 66 | 72.73% | USD 85.80 | USD 5,663.00 | USD -1,753.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 66 | 71.21% | USD 80.60 | USD 5,319.80 | USD -1,758.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 66 | 71.21% | USD 65.80 | USD 4,343.00 | USD -1,773.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 66 | 71.21% | USD 60.60 | USD 3,999.80 | USD -1,778.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 66 | 68.18% | USD 25.80 | USD 1,703.00 | USD -1,813.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 66 | 68.18% | USD 20.60 | USD 1,359.80 | USD -1,818.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 65 | 76.92% | USD 175.09 | USD 11,381.00 | USD -4,846.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 65 | 76.92% | USD 169.89 | USD 11,043.00 | USD -4,851.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 65 | 76.92% | USD 155.09 | USD 10,081.00 | USD -4,866.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 65 | 76.92% | USD 149.89 | USD 9,743.00 | USD -4,871.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 65 | 76.92% | USD 135.09 | USD 8,781.00 | USD -4,886.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 65 | 76.92% | USD 129.89 | USD 8,443.00 | USD -4,891.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 65 | 75.38% | USD 95.09 | USD 6,181.00 | USD -4,926.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 65 | 73.85% | USD 89.89 | USD 5,843.00 | USD -4,931.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 65 | 84.62% | USD 337.57 | USD 21,942.00 | USD -5,185.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 65 | 84.62% | USD 332.37 | USD 21,604.00 | USD -5,190.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 65 | 84.62% | USD 317.57 | USD 20,642.00 | USD -5,205.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 65 | 84.62% | USD 312.37 | USD 20,304.00 | USD -5,210.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 65 | 84.62% | USD 297.57 | USD 19,342.00 | USD -5,225.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 65 | 84.62% | USD 292.37 | USD 19,004.00 | USD -5,230.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 65 | 84.62% | USD 257.57 | USD 16,742.00 | USD -5,265.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 65 | 84.62% | USD 252.37 | USD 16,404.00 | USD -5,270.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 62 | 85.48% | USD 181.76 | USD 11,269.00 | USD -16,994.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 62 | 85.48% | USD 176.56 | USD 10,946.60 | USD -16,999.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 62 | 85.48% | USD 161.76 | USD 10,029.00 | USD -17,014.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 62 | 85.48% | USD 156.56 | USD 9,706.60 | USD -17,019.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 62 | 85.48% | USD 141.76 | USD 8,789.00 | USD -17,034.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 62 | 85.48% | USD 136.56 | USD 8,466.60 | USD -17,039.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 62 | 85.48% | USD 101.76 | USD 6,309.00 | USD -17,074.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 62 | 85.48% | USD 96.56 | USD 5,986.60 | USD -17,079.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 66/66 (0) | 27.27% (18.00–39.04%) | USD -50.13 | USD -3,308.60 | USD -480.60 |
| HOLD_5_SESSIONS | 1 : 6 | 66/66 (0) | 72.73% (60.96–82.00%) | USD 226.70 | USD 14,962.40 | USD -3,956.10 |
| HOLD_5_SESSIONS | 6 : 1 | 66/66 (0) | 19.70% (11.89–30.84%) | USD -577.62 | USD -38,122.60 | USD -3,001.10 |
| HOLD_5_SESSIONS | 4 : 5 | 66/66 (0) | 50.00% (38.27–61.73%) | USD -145.15 | USD -9,580.20 | USD -2,272.70 |
| HOLD_10_SESSIONS | 1 : 1 | 65/66 (1) | 36.92% (26.23–49.08%) | USD -50.09 | USD -3,256.00 | USD -746.60 |
| HOLD_10_SESSIONS | 1 : 6 | 65/66 (1) | 75.38% (63.69–84.24%) | USD 399.87 | USD 25,991.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 65/66 (1) | 15.38% (8.58–26.06%) | USD -750.52 | USD -48,783.50 | USD -3,797.10 |
| HOLD_10_SESSIONS | 4 : 5 | 65/66 (1) | 64.62% (52.48–75.12%) | USD -110.38 | USD -7,174.50 | USD -5,058.70 |
| HOLD_20_SESSIONS | 1 : 1 | 65/66 (1) | 40.00% (28.97–52.14%) | USD -26.17 | USD -1,701.00 | USD -975.60 |
| HOLD_20_SESSIONS | 1 : 6 | 65/66 (1) | 84.62% (73.94–91.42%) | USD 770.18 | USD 50,061.50 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 65/66 (1) | 16.92% (9.72–27.82%) | USD -953.36 | USD -61,968.50 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 65/66 (1) | 80.00% (68.73–87.92%) | USD 54.59 | USD 3,548.50 | USD -5,571.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 62/66 (4) | 48.39% (36.41–60.55%) | USD -54.16 | USD -3,358.20 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 62/66 (4) | 87.10% (76.55–93.31%) | USD 422.64 | USD 26,203.80 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 62/66 (4) | 19.35% (11.43–30.85%) | USD -801.79 | USD -49,711.20 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 62/66 (4) | 77.42% (65.59–86.04%) | USD -121.30 | USD -7,520.40 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/66 | 0.00% | USD -87,347.55 | USD -137,444.60 |
| -75% | 0/66 | 0.00% | USD -64,457.36 | USD -101,740.85 |
| -50% | 0/66 | 0.00% | USD -41,567.16 | USD -66,037.10 |
| -40% | 0/66 | 0.00% | USD -32,411.08 | USD -51,755.60 |
| -30% | 0/66 | 0.00% | USD -23,255.00 | USD -37,474.10 |
| -25% | 0/66 | 0.00% | USD -18,676.96 | USD -30,333.35 |
| -20% | 0/66 | 0.00% | USD -14,098.92 | USD -23,192.60 |
| -15% | 0/66 | 0.00% | USD -9,520.88 | USD -16,051.85 |
| -10% | 1/66 | 1.52% | USD -4,942.15 | USD -9,451.60 |
| -5% | 24/66 | 36.36% | USD -526.42 | USD -3,167.65 |
| 0% | 66/66 | 100.00% | USD 872.99 | USD 344.40 |
| 5% | 66/66 | 100.00% | USD 871.96 | USD 344.40 |
| 10% | 66/66 | 100.00% | USD 871.96 | USD 344.40 |
| 20% | 66/66 | 100.00% | USD 871.96 | USD 344.40 |

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