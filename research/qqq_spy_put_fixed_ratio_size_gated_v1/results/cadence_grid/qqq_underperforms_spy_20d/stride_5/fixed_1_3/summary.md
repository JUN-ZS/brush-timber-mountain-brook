# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 1164 checks; 199 qualified; 965 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 460.90 / USD 1,356.79; mean absolute mismatch USD 895.89; mean match score 33.61%.
- Actual selected contract ratios: {'1:3': 198}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 199; entered cohorts: 198; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 197/198 | 125/72/0 | 63.45% (56.53–69.86%) | USD 25.02 | USD 167.80 | USD 4,928.60 | USD -3,165.20 | 1 |
| HOLD_10_SESSIONS | 195/198 | 144/51/0 | 73.85% (67.26–79.51%) | USD 96.39 | USD 294.80 | USD 18,797.00 | USD -4,203.20 | 3 |
| HOLD_20_SESSIONS | 192/198 | 155/37/0 | 80.73% (74.57–85.68%) | USD 301.64 | USD 525.80 | USD 57,915.60 | USD -4,932.20 | 6 |
| EXIT_AT_DTE_LE_7 | 172/198 | 141/31/0 | 81.98% (75.55–87.00%) | USD 288.38 | USD 648.80 | USD 49,601.60 | USD -8,692.20 | 26 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -63.55 | USD 133.77 |
| HOLD_10_SESSIONS | USD -108.36 | USD 249.95 |
| HOLD_20_SESSIONS | USD -193.78 | USD 540.62 |
| EXIT_AT_DTE_LE_7 | USD -198.99 | USD 532.57 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 197 | 65.99% | USD 70.22 | USD 13,833.00 | USD -3,120.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 197 | 65.99% | USD 65.02 | USD 12,808.60 | USD -3,125.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 197 | 63.96% | USD 50.22 | USD 9,893.00 | USD -3,140.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 197 | 63.96% | USD 45.02 | USD 8,868.60 | USD -3,145.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 197 | 63.45% | USD 30.22 | USD 5,953.00 | USD -3,160.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 197 | 63.45% | USD 25.02 | USD 4,928.60 | USD -3,165.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 197 | 61.42% | USD -9.78 | USD -1,927.00 | USD -3,200.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 197 | 60.41% | USD -14.98 | USD -2,951.40 | USD -3,205.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 75.90% | USD 141.59 | USD 27,611.00 | USD -4,158.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 75.90% | USD 136.39 | USD 26,597.00 | USD -4,163.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 75.90% | USD 121.59 | USD 23,711.00 | USD -4,178.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 75.90% | USD 116.39 | USD 22,697.00 | USD -4,183.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 74.36% | USD 101.59 | USD 19,811.00 | USD -4,198.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 73.85% | USD 96.39 | USD 18,797.00 | USD -4,203.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 71.28% | USD 61.59 | USD 12,011.00 | USD -4,238.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 70.26% | USD 56.39 | USD 10,997.00 | USD -4,243.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 192 | 81.25% | USD 346.84 | USD 66,594.00 | USD -4,887.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 192 | 81.25% | USD 341.64 | USD 65,595.60 | USD -4,892.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 192 | 81.25% | USD 326.84 | USD 62,754.00 | USD -4,907.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 192 | 81.25% | USD 321.64 | USD 61,755.60 | USD -4,912.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 192 | 81.25% | USD 306.84 | USD 58,914.00 | USD -4,927.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 192 | 80.73% | USD 301.64 | USD 57,915.60 | USD -4,932.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 192 | 80.73% | USD 266.84 | USD 51,234.00 | USD -4,967.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 192 | 80.73% | USD 261.64 | USD 50,235.60 | USD -4,972.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 172 | 81.98% | USD 333.58 | USD 57,376.00 | USD -8,647.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 172 | 81.98% | USD 328.38 | USD 56,481.60 | USD -8,652.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 172 | 81.98% | USD 313.58 | USD 53,936.00 | USD -8,667.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 172 | 81.98% | USD 308.38 | USD 53,041.60 | USD -8,672.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 172 | 81.98% | USD 293.58 | USD 50,496.00 | USD -8,687.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 172 | 81.98% | USD 288.38 | USD 49,601.60 | USD -8,692.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 172 | 81.40% | USD 253.58 | USD 43,616.00 | USD -8,727.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 172 | 81.40% | USD 248.38 | USD 42,721.60 | USD -8,732.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 197/198 (1) | 31.47% (25.39–38.26%) | USD -41.56 | USD -8,187.20 | USD -544.60 |
| HOLD_5_SESSIONS | 1 : 6 | 197/198 (1) | 64.47% (57.57–70.82%) | USD 124.88 | USD 24,602.30 | USD -7,267.10 |
| HOLD_5_SESSIONS | 6 : 1 | 197/198 (1) | 29.95% (23.99–36.68%) | USD -415.80 | USD -81,912.70 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 197/198 (1) | 49.75% (42.84–56.67%) | USD -132.95 | USD -26,190.90 | USD -3,488.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/198 (3) | 30.26% (24.24–37.03%) | USD -47.64 | USD -9,290.00 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/198 (3) | 74.87% (68.34–80.44%) | USD 312.45 | USD 60,927.50 | USD -10,453.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/198 (3) | 20.51% (15.44–26.72%) | USD -645.94 | USD -125,957.50 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/198 (3) | 53.85% (46.84–60.70%) | USD -118.55 | USD -23,116.50 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 192/198 (6) | 39.58% (32.94–46.64%) | USD -36.17 | USD -6,945.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 192/198 (6) | 80.73% (74.57–85.68%) | USD 808.37 | USD 155,206.80 | USD -11,587.10 |
| HOLD_20_SESSIONS | 6 : 1 | 192/198 (6) | 16.15% (11.61–22.01%) | USD -1,061.58 | USD -203,823.20 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 192/198 (6) | 70.31% (63.50–76.33%) | USD 24.22 | USD 4,649.60 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 172/198 (26) | 37.79% (30.89–45.23%) | USD -44.07 | USD -7,579.20 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 172/198 (26) | 81.40% (74.92–86.50%) | USD 787.05 | USD 135,372.80 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 172/198 (26) | 18.02% (13.00–24.45%) | USD -1,095.51 | USD -188,427.20 | USD -5,483.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 172/198 (26) | 72.67% (65.57–78.78%) | USD -10.04 | USD -1,726.40 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/198 | 0.00% | USD -87,474.27 | USD -138,284.60 |
| -75% | 0/198 | 0.00% | USD -64,506.51 | USD -102,619.35 |
| -50% | 0/198 | 0.00% | USD -41,538.76 | USD -66,954.10 |
| -40% | 0/198 | 0.00% | USD -32,351.66 | USD -52,688.00 |
| -30% | 0/198 | 0.00% | USD -23,164.56 | USD -38,421.90 |
| -25% | 0/198 | 0.00% | USD -18,571.01 | USD -31,288.85 |
| -20% | 0/198 | 0.00% | USD -13,977.45 | USD -24,155.80 |
| -15% | 0/198 | 0.00% | USD -9,383.90 | USD -17,022.75 |
| -10% | 2/198 | 1.01% | USD -4,790.64 | USD -9,889.70 |
| -5% | 90/198 | 45.45% | USD -374.62 | USD -3,803.15 |
| 0% | 198/198 | 100.00% | USD 874.11 | USD 228.40 |
| 5% | 198/198 | 100.00% | USD 873.29 | USD 228.40 |
| 10% | 198/198 | 100.00% | USD 873.29 | USD 228.40 |
| 20% | 198/198 | 100.00% | USD 873.29 | USD 228.40 |

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