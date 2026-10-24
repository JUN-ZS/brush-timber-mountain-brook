# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 98 checks; 98 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,733.31 / USD 2,167.09; mean absolute mismatch USD 451.99; mean match score 78.60%.
- Actual selected contract ratios: {'4:5': 98}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 98; entered cohorts: 98; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/98 | 48/50/0 | 48.98% (39.31–58.73%) | USD -135.44 | USD -5.70 | USD -13,273.60 | USD -2,903.70 | 0 |
| HOLD_10_SESSIONS | 98/98 | 63/35/0 | 64.29% (54.43–73.07%) | USD -105.91 | USD 64.80 | USD -10,379.60 | USD -7,525.70 | 0 |
| HOLD_20_SESSIONS | 97/98 | 69/28/0 | 71.13% (61.45–79.21%) | USD -52.55 | USD 218.30 | USD -5,096.90 | USD -10,530.70 | 1 |
| EXIT_AT_DTE_LE_7 | 91/98 | 66/25/0 | 72.53% (62.59–80.64%) | USD -294.58 | USD 283.30 | USD -26,806.70 | USD -20,624.70 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -411.35 | USD 377.60 |
| HOLD_10_SESSIONS | USD -539.88 | USD 535.66 |
| HOLD_20_SESSIONS | USD -756.82 | USD 805.98 |
| EXIT_AT_DTE_LE_7 | USD -779.69 | USD 586.81 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 61.22% | USD -33.74 | USD -3,307.00 | USD -2,802.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 61.22% | USD -45.44 | USD -4,453.60 | USD -2,813.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 54.08% | USD -78.74 | USD -7,717.00 | USD -2,847.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 54.08% | USD -90.44 | USD -8,863.60 | USD -2,858.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 51.02% | USD -123.74 | USD -12,127.00 | USD -2,892.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 48.98% | USD -135.44 | USD -13,273.60 | USD -2,903.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 37.76% | USD -213.74 | USD -20,947.00 | USD -2,982.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 36.73% | USD -225.44 | USD -22,093.60 | USD -2,993.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 98 | 66.33% | USD -4.21 | USD -413.00 | USD -7,424.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 98 | 65.31% | USD -15.91 | USD -1,559.60 | USD -7,435.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 98 | 64.29% | USD -49.21 | USD -4,823.00 | USD -7,469.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 98 | 64.29% | USD -60.91 | USD -5,969.60 | USD -7,480.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 98 | 64.29% | USD -94.21 | USD -9,233.00 | USD -7,514.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 98 | 64.29% | USD -105.91 | USD -10,379.60 | USD -7,525.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 98 | 48.98% | USD -184.21 | USD -18,053.00 | USD -7,604.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 98 | 48.98% | USD -195.91 | USD -19,199.60 | USD -7,615.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 97 | 77.32% | USD 49.15 | USD 4,768.00 | USD -10,429.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 97 | 77.32% | USD 37.45 | USD 3,633.10 | USD -10,440.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 97 | 74.23% | USD 4.15 | USD 403.00 | USD -10,474.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 97 | 73.20% | USD -7.55 | USD -731.90 | USD -10,485.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 97 | 71.13% | USD -40.85 | USD -3,962.00 | USD -10,519.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 97 | 71.13% | USD -52.55 | USD -5,096.90 | USD -10,530.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 97 | 62.89% | USD -130.85 | USD -12,692.00 | USD -10,609.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 97 | 61.86% | USD -142.55 | USD -13,826.90 | USD -10,620.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 91 | 81.32% | USD -192.88 | USD -17,552.00 | USD -20,523.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 91 | 81.32% | USD -204.58 | USD -18,616.70 | USD -20,534.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 91 | 80.22% | USD -237.88 | USD -21,647.00 | USD -20,568.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 91 | 78.02% | USD -249.58 | USD -22,711.70 | USD -20,579.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 91 | 73.63% | USD -282.88 | USD -25,742.00 | USD -20,613.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 91 | 72.53% | USD -294.58 | USD -26,806.70 | USD -20,624.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 91 | 67.03% | USD -372.88 | USD -33,932.00 | USD -20,703.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 91 | 65.93% | USD -384.58 | USD -34,996.70 | USD -20,714.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/98 (0) | 27.55% (19.68–37.12%) | USD -49.92 | USD -4,891.80 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/98 (0) | 74.49% (65.05–82.08%) | USD 271.19 | USD 26,576.20 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -620.60 | USD -60,818.80 | USD -3,952.10 |
| HOLD_5_SESSIONS | 4 : 5 | 98/98 (0) | 48.98% (39.31–58.73%) | USD -135.44 | USD -13,273.60 | USD -2,903.70 |
| HOLD_10_SESSIONS | 1 : 1 | 98/98 (0) | 40.82% (31.61–50.71%) | USD -50.44 | USD -4,942.80 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 98/98 (0) | 80.61% (71.69–87.22%) | USD 428.73 | USD 42,015.20 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -781.78 | USD -76,614.80 | USD -4,731.10 |
| HOLD_10_SESSIONS | 4 : 5 | 98/98 (0) | 64.29% (54.43–73.07%) | USD -105.91 | USD -10,379.60 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 97/98 (1) | 44.33% (34.85–54.24%) | USD -50.61 | USD -4,909.20 | USD -1,890.60 |
| HOLD_20_SESSIONS | 1 : 6 | 97/98 (1) | 81.44% (72.56–87.93%) | USD 698.87 | USD 67,790.30 | USD -16,732.10 |
| HOLD_20_SESSIONS | 6 : 1 | 97/98 (1) | 14.43% (8.80–22.78%) | USD -1,053.14 | USD -102,154.70 | USD -4,180.10 |
| HOLD_20_SESSIONS | 4 : 5 | 97/98 (1) | 71.13% (61.45–79.21%) | USD -52.55 | USD -5,096.90 | USD -10,530.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 91/98 (7) | 43.96% (34.21–54.19%) | USD -100.16 | USD -9,114.60 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 91/98 (7) | 84.62% (75.82–90.61%) | USD 430.15 | USD 39,143.90 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 91/98 (7) | 14.29% (8.54–22.92%) | USD -1,131.28 | USD -102,946.10 | USD -4,912.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 91/98 (7) | 72.53% (62.59–80.64%) | USD -294.58 | USD -26,806.70 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/98 | 0.00% | USD -73,103.04 | USD -94,413.85 |
| -75% | 0/98 | 0.00% | USD -54,289.90 | USD -70,612.10 |
| -50% | 0/98 | 0.00% | USD -35,476.75 | USD -46,810.35 |
| -40% | 0/98 | 0.00% | USD -27,951.49 | USD -37,334.65 |
| -30% | 0/98 | 0.00% | USD -20,426.24 | USD -28,023.95 |
| -25% | 0/98 | 0.00% | USD -16,663.61 | USD -23,368.60 |
| -20% | 0/98 | 0.00% | USD -12,900.98 | USD -18,713.25 |
| -15% | 1/98 | 1.02% | USD -9,151.25 | USD -14,122.35 |
| -10% | 2/98 | 2.04% | USD -5,411.97 | USD -9,611.85 |
| -5% | 30/98 | 30.61% | USD -1,378.65 | USD -4,892.90 |
| 0% | 88/98 | 89.80% | USD 382.94 | USD -305.85 |
| 5% | 88/98 | 89.80% | USD 382.94 | USD -305.85 |
| 10% | 88/98 | 89.80% | USD 382.94 | USD -305.85 |
| 20% | 88/98 | 89.80% | USD 382.94 | USD -305.85 |

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