# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 98 checks; 98 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 869.96 / USD 1,738.82; mean absolute mismatch USD 868.86; mean match score 49.73%.
- Actual selected contract ratios: {'2:4': 98}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 98; entered cohorts: 98; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/98 | 67/31/0 | 68.37% (58.62–76.73%) | USD 29.87 | USD 178.20 | USD 2,927.60 | USD -2,773.80 | 0 |
| HOLD_10_SESSIONS | 98/98 | 79/19/0 | 80.61% (71.69–87.22%) | USD 92.34 | USD 319.20 | USD 9,049.60 | USD -6,635.80 | 0 |
| HOLD_20_SESSIONS | 97/98 | 77/20/0 | 79.38% (70.29–86.24%) | USD 187.19 | USD 556.20 | USD 18,157.40 | USD -9,717.80 | 1 |
| EXIT_AT_DTE_LE_7 | 92/98 | 79/13/0 | 85.87% (77.31–91.55%) | USD 0.85 | USD 637.20 | USD 78.40 | USD -20,497.80 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -206.86 | USD 304.53 |
| HOLD_10_SESSIONS | USD -272.43 | USD 432.57 |
| HOLD_20_SESSIONS | USD -333.96 | USD 588.95 |
| EXIT_AT_DTE_LE_7 | USD -388.78 | USD 457.43 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 74.49% | USD 97.67 | USD 9,572.00 | USD -2,706.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 74.49% | USD 89.87 | USD 8,807.60 | USD -2,713.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 71.43% | USD 67.67 | USD 6,632.00 | USD -2,736.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 71.43% | USD 59.87 | USD 5,867.60 | USD -2,743.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 68.37% | USD 37.67 | USD 3,692.00 | USD -2,766.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 68.37% | USD 29.87 | USD 2,927.60 | USD -2,773.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 63.27% | USD -22.33 | USD -2,188.00 | USD -2,826.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 63.27% | USD -30.13 | USD -2,952.40 | USD -2,833.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 98 | 81.63% | USD 160.14 | USD 15,694.00 | USD -6,568.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 98 | 81.63% | USD 152.34 | USD 14,929.60 | USD -6,575.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 98 | 81.63% | USD 130.14 | USD 12,754.00 | USD -6,598.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 98 | 81.63% | USD 122.34 | USD 11,989.60 | USD -6,605.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 98 | 80.61% | USD 100.14 | USD 9,814.00 | USD -6,628.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 98 | 80.61% | USD 92.34 | USD 9,049.60 | USD -6,635.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 98 | 75.51% | USD 40.14 | USD 3,934.00 | USD -6,688.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 98 | 75.51% | USD 32.34 | USD 3,169.60 | USD -6,695.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 97 | 80.41% | USD 254.99 | USD 24,734.00 | USD -9,650.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 97 | 80.41% | USD 247.19 | USD 23,977.40 | USD -9,657.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 97 | 80.41% | USD 224.99 | USD 21,824.00 | USD -9,680.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 97 | 80.41% | USD 217.19 | USD 21,067.40 | USD -9,687.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 97 | 80.41% | USD 194.99 | USD 18,914.00 | USD -9,710.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 97 | 79.38% | USD 187.19 | USD 18,157.40 | USD -9,717.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 97 | 79.38% | USD 134.99 | USD 13,094.00 | USD -9,770.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 97 | 79.38% | USD 127.19 | USD 12,337.40 | USD -9,777.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 92 | 85.87% | USD 68.65 | USD 6,316.00 | USD -20,430.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 92 | 85.87% | USD 60.85 | USD 5,598.40 | USD -20,437.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 92 | 85.87% | USD 38.65 | USD 3,556.00 | USD -20,460.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 92 | 85.87% | USD 30.85 | USD 2,838.40 | USD -20,467.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 92 | 85.87% | USD 8.65 | USD 796.00 | USD -20,490.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 92 | 85.87% | USD 0.85 | USD 78.40 | USD -20,497.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 92 | 85.87% | USD -51.35 | USD -4,724.00 | USD -20,550.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 92 | 85.87% | USD -59.15 | USD -5,441.60 | USD -20,557.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/98 (0) | 27.55% (19.68–37.12%) | USD -49.90 | USD -4,889.80 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/98 (0) | 74.49% (65.05–82.08%) | USD 274.27 | USD 26,878.20 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -623.54 | USD -61,106.80 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 98/98 (0) | 48.98% (39.31–58.73%) | USD -134.75 | USD -13,205.60 | USD -2,903.70 |
| HOLD_10_SESSIONS | 1 : 1 | 98/98 (0) | 40.82% (31.61–50.71%) | USD -50.67 | USD -4,965.80 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 98/98 (0) | 80.61% (71.69–87.22%) | USD 433.54 | USD 42,487.20 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -788.24 | USD -77,247.80 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 98/98 (0) | 64.29% (54.43–73.07%) | USD -105.84 | USD -10,372.60 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 97/98 (1) | 44.33% (34.85–54.24%) | USD -42.34 | USD -4,107.20 | USD -1,890.60 |
| HOLD_20_SESSIONS | 1 : 6 | 97/98 (1) | 80.41% (71.42–87.09%) | USD 637.34 | USD 61,822.30 | USD -16,732.10 |
| HOLD_20_SESSIONS | 6 : 1 | 97/98 (1) | 15.46% (9.60–23.96%) | USD -933.74 | USD -90,572.70 | USD -4,180.10 |
| HOLD_20_SESSIONS | 4 : 5 | 97/98 (1) | 71.13% (61.45–79.21%) | USD -33.43 | USD -3,242.90 | USD -10,530.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 92/98 (6) | 43.48% (33.81–53.67%) | USD -102.63 | USD -9,442.20 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 92/98 (6) | 84.78% (76.06–90.71%) | USD 412.66 | USD 37,964.80 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 92/98 (6) | 14.13% (8.45–22.69%) | USD -1,131.09 | USD -104,060.20 | USD -4,912.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 92/98 (6) | 71.74% (61.81–79.92%) | USD -307.47 | USD -28,287.40 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/98 | 0.00% | USD -95,293.49 | USD -141,677.90 |
| -75% | 0/98 | 0.00% | USD -70,404.58 | USD -105,266.90 |
| -50% | 0/98 | 0.00% | USD -45,515.67 | USD -68,855.90 |
| -40% | 0/98 | 0.00% | USD -35,560.10 | USD -54,291.50 |
| -30% | 0/98 | 0.00% | USD -25,604.53 | USD -39,807.10 |
| -25% | 0/98 | 0.00% | USD -20,626.75 | USD -32,660.90 |
| -20% | 0/98 | 0.00% | USD -15,648.97 | USD -25,514.70 |
| -15% | 1/98 | 1.02% | USD -10,685.32 | USD -18,368.50 |
| -10% | 2/98 | 2.04% | USD -5,739.20 | USD -11,222.30 |
| -5% | 37/98 | 37.76% | USD -817.56 | USD -4,076.10 |
| 0% | 98/98 | 100.00% | USD 834.96 | USD 192.10 |
| 5% | 98/98 | 100.00% | USD 834.96 | USD 192.10 |
| 10% | 98/98 | 100.00% | USD 834.96 | USD 192.10 |
| 20% | 98/98 | 100.00% | USD 834.96 | USD 192.10 |

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