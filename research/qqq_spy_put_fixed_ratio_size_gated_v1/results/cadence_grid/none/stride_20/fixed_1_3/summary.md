# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 98 checks; 98 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 436.95 / USD 1,309.29; mean absolute mismatch USD 872.34; mean match score 33.17%.
- Actual selected contract ratios: {'1:3': 98}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 98; entered cohorts: 98; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/98 | 70/28/0 | 71.43% (61.81–79.43%) | USD 78.63 | USD 192.80 | USD 7,705.40 | USD -2,268.20 | 0 |
| HOLD_10_SESSIONS | 98/98 | 79/19/0 | 80.61% (71.69–87.22%) | USD 144.28 | USD 337.30 | USD 14,139.40 | USD -5,233.20 | 0 |
| HOLD_20_SESSIONS | 97/98 | 77/20/0 | 79.38% (70.29–86.24%) | USD 222.47 | USD 552.80 | USD 21,579.60 | USD -7,827.20 | 1 |
| EXIT_AT_DTE_LE_7 | 92/98 | 78/14/0 | 84.78% (76.06–90.71%) | USD 96.05 | USD 706.80 | USD 8,836.60 | USD -17,039.20 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -103.16 | USD 226.99 |
| HOLD_10_SESSIONS | USD -139.08 | USD 328.56 |
| HOLD_20_SESSIONS | USD -166.96 | USD 434.63 |
| EXIT_AT_DTE_LE_7 | USD -190.90 | USD 332.15 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 75.51% | USD 123.83 | USD 12,135.00 | USD -2,223.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 75.51% | USD 118.63 | USD 11,625.40 | USD -2,228.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 75.51% | USD 103.83 | USD 10,175.00 | USD -2,243.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 72.45% | USD 98.63 | USD 9,665.40 | USD -2,248.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 71.43% | USD 83.83 | USD 8,215.00 | USD -2,263.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 71.43% | USD 78.63 | USD 7,705.40 | USD -2,268.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 67.35% | USD 43.83 | USD 4,295.00 | USD -2,303.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 66.33% | USD 38.63 | USD 3,785.40 | USD -2,308.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 98 | 81.63% | USD 189.48 | USD 18,569.00 | USD -5,188.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 98 | 81.63% | USD 184.28 | USD 18,059.40 | USD -5,193.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 98 | 81.63% | USD 169.48 | USD 16,609.00 | USD -5,208.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 98 | 81.63% | USD 164.28 | USD 16,099.40 | USD -5,213.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 98 | 80.61% | USD 149.48 | USD 14,649.00 | USD -5,228.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 98 | 80.61% | USD 144.28 | USD 14,139.40 | USD -5,233.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 98 | 77.55% | USD 109.48 | USD 10,729.00 | USD -5,268.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 98 | 77.55% | USD 104.28 | USD 10,219.40 | USD -5,273.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 97 | 79.38% | USD 267.67 | USD 25,964.00 | USD -7,782.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 97 | 79.38% | USD 262.47 | USD 25,459.60 | USD -7,787.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 97 | 79.38% | USD 247.67 | USD 24,024.00 | USD -7,802.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 97 | 79.38% | USD 242.47 | USD 23,519.60 | USD -7,807.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 97 | 79.38% | USD 227.67 | USD 22,084.00 | USD -7,822.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 97 | 79.38% | USD 222.47 | USD 21,579.60 | USD -7,827.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 97 | 79.38% | USD 187.67 | USD 18,204.00 | USD -7,862.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 97 | 79.38% | USD 182.47 | USD 17,699.60 | USD -7,867.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 92 | 84.78% | USD 141.25 | USD 12,995.00 | USD -16,994.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 92 | 84.78% | USD 136.05 | USD 12,516.60 | USD -16,999.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 92 | 84.78% | USD 121.25 | USD 11,155.00 | USD -17,014.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 92 | 84.78% | USD 116.05 | USD 10,676.60 | USD -17,019.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 92 | 84.78% | USD 101.25 | USD 9,315.00 | USD -17,034.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 92 | 84.78% | USD 96.05 | USD 8,836.60 | USD -17,039.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 92 | 84.78% | USD 61.25 | USD 5,635.00 | USD -17,074.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 92 | 84.78% | USD 56.05 | USD 5,156.60 | USD -17,079.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/98 (0) | 27.55% (19.68–37.12%) | USD -50.10 | USD -4,909.80 | USD -505.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/98 (0) | 74.49% (65.05–82.08%) | USD 271.72 | USD 26,628.20 | USD -4,912.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -622.42 | USD -60,996.80 | USD -4,240.10 |
| HOLD_5_SESSIONS | 4 : 5 | 98/98 (0) | 48.98% (39.31–58.73%) | USD -136.04 | USD -13,331.60 | USD -2,903.70 |
| HOLD_10_SESSIONS | 1 : 1 | 98/98 (0) | 40.82% (31.61–50.71%) | USD -52.16 | USD -5,111.80 | USD -1,402.60 |
| HOLD_10_SESSIONS | 1 : 6 | 98/98 (0) | 80.61% (71.69–87.22%) | USD 438.94 | USD 43,016.20 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 98/98 (0) | 17.35% (11.12–26.04%) | USD -804.07 | USD -78,798.80 | USD -5,364.10 |
| HOLD_10_SESSIONS | 4 : 5 | 98/98 (0) | 64.29% (54.43–73.07%) | USD -110.42 | USD -10,821.60 | USD -7,525.70 |
| HOLD_20_SESSIONS | 1 : 1 | 97/98 (1) | 43.30% (33.88–53.23%) | USD -44.68 | USD -4,334.20 | USD -1,890.60 |
| HOLD_20_SESSIONS | 1 : 6 | 97/98 (1) | 80.41% (71.42–87.09%) | USD 623.20 | USD 60,450.30 | USD -16,732.10 |
| HOLD_20_SESSIONS | 6 : 1 | 97/98 (1) | 15.46% (9.60–23.96%) | USD -935.98 | USD -90,789.70 | USD -4,180.10 |
| HOLD_20_SESSIONS | 4 : 5 | 97/98 (1) | 70.10% (60.37–78.31%) | USD -45.15 | USD -4,379.90 | USD -10,530.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 92/98 (6) | 43.48% (33.81–53.67%) | USD -102.78 | USD -9,456.20 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 92/98 (6) | 84.78% (76.06–90.71%) | USD 394.30 | USD 36,275.80 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 92/98 (6) | 14.13% (8.45–22.69%) | USD -1,113.80 | USD -102,469.20 | USD -4,912.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 92/98 (6) | 71.74% (61.81–79.92%) | USD -311.72 | USD -28,678.40 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/98 | 0.00% | USD -86,804.79 | USD -135,029.60 |
| -75% | 0/98 | 0.00% | USD -64,041.18 | USD -100,045.85 |
| -50% | 0/98 | 0.00% | USD -41,277.56 | USD -65,260.10 |
| -40% | 0/98 | 0.00% | USD -32,172.11 | USD -51,345.80 |
| -30% | 0/98 | 0.00% | USD -23,066.67 | USD -37,431.50 |
| -25% | 0/98 | 0.00% | USD -18,513.94 | USD -30,474.35 |
| -20% | 0/98 | 0.00% | USD -13,961.22 | USD -23,529.40 |
| -15% | 1/98 | 1.02% | USD -9,420.68 | USD -16,743.95 |
| -10% | 2/98 | 2.04% | USD -4,897.12 | USD -9,958.50 |
| -5% | 38/98 | 38.78% | USD -500.12 | USD -3,173.05 |
| 0% | 98/98 | 100.00% | USD 849.74 | USD 215.40 |
| 5% | 98/98 | 100.00% | USD 849.74 | USD 215.40 |
| 10% | 98/98 | 100.00% | USD 849.74 | USD 215.40 |
| 20% | 98/98 | 100.00% | USD 849.74 | USD 215.40 |

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