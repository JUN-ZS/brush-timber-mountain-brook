# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 1164 checks; 199 qualified; 965 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 460.38 / USD 2,713.21; mean absolute mismatch USD 2,252.83; mean match score 16.79%.
- Actual selected contract ratios: {'1:6': 198}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 199; entered cohorts: 198; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 197/198 | 127/70/0 | 64.47% (57.57–70.82%) | USD 125.64 | USD 401.90 | USD 24,751.30 | USD -7,267.10 | 1 |
| HOLD_10_SESSIONS | 195/198 | 146/49/0 | 74.87% (68.34–80.44%) | USD 313.08 | USD 809.90 | USD 61,051.50 | USD -10,453.10 | 3 |
| HOLD_20_SESSIONS | 192/198 | 155/37/0 | 80.73% (74.57–85.68%) | USD 798.50 | USD 1,352.40 | USD 153,311.80 | USD -11,587.10 | 6 |
| EXIT_AT_DTE_LE_7 | 172/198 | 140/32/0 | 81.40% (74.92–86.50%) | USD 772.34 | USD 1,675.90 | USD 132,841.80 | USD -20,318.10 | 26 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -63.01 | USD 267.75 |
| HOLD_10_SESSIONS | USD -108.09 | USD 500.28 |
| HOLD_20_SESSIONS | USD -191.03 | USD 1,068.62 |
| EXIT_AT_DTE_LE_7 | USD -194.76 | USD 1,046.20 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 197 | 66.50% | USD 204.74 | USD 40,334.00 | USD -7,188.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 197 | 66.50% | USD 195.64 | USD 38,541.30 | USD -7,197.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 197 | 66.50% | USD 169.74 | USD 33,439.00 | USD -7,223.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 197 | 65.99% | USD 160.64 | USD 31,646.30 | USD -7,232.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 197 | 65.48% | USD 134.74 | USD 26,544.00 | USD -7,258.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 197 | 64.47% | USD 125.64 | USD 24,751.30 | USD -7,267.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 197 | 63.96% | USD 64.74 | USD 12,754.00 | USD -7,328.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 197 | 62.94% | USD 55.64 | USD 10,961.30 | USD -7,337.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 76.92% | USD 392.18 | USD 76,476.00 | USD -10,374.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 76.92% | USD 383.08 | USD 74,701.50 | USD -10,383.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 76.41% | USD 357.18 | USD 69,651.00 | USD -10,409.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 76.41% | USD 348.08 | USD 67,876.50 | USD -10,418.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 74.87% | USD 322.18 | USD 62,826.00 | USD -10,444.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 74.87% | USD 313.08 | USD 61,051.50 | USD -10,453.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 73.85% | USD 252.18 | USD 49,176.00 | USD -10,514.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 73.33% | USD 243.08 | USD 47,401.50 | USD -10,523.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 192 | 81.77% | USD 877.60 | USD 168,499.00 | USD -11,508.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 192 | 81.77% | USD 868.50 | USD 166,751.80 | USD -11,517.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 192 | 81.25% | USD 842.60 | USD 161,779.00 | USD -11,543.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 192 | 81.25% | USD 833.50 | USD 160,031.80 | USD -11,552.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 192 | 81.25% | USD 807.60 | USD 155,059.00 | USD -11,578.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 192 | 80.73% | USD 798.50 | USD 153,311.80 | USD -11,587.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 192 | 80.21% | USD 737.60 | USD 141,619.00 | USD -11,648.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 192 | 80.21% | USD 728.50 | USD 139,871.80 | USD -11,657.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 172 | 81.98% | USD 851.44 | USD 146,447.00 | USD -20,239.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 172 | 81.98% | USD 842.34 | USD 144,881.80 | USD -20,248.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 172 | 81.40% | USD 816.44 | USD 140,427.00 | USD -20,274.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 172 | 81.40% | USD 807.34 | USD 138,861.80 | USD -20,283.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 172 | 81.40% | USD 781.44 | USD 134,407.00 | USD -20,309.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 172 | 81.40% | USD 772.34 | USD 132,841.80 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 172 | 81.40% | USD 711.44 | USD 122,367.00 | USD -20,379.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 172 | 81.40% | USD 702.34 | USD 120,801.80 | USD -20,388.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 197/198 (1) | 31.98% (25.86–38.78%) | USD -40.98 | USD -8,073.20 | USD -544.60 |
| HOLD_5_SESSIONS | 1 : 6 | 197/198 (1) | 64.47% (57.57–70.82%) | USD 125.64 | USD 24,751.30 | USD -7,267.10 |
| HOLD_5_SESSIONS | 6 : 1 | 197/198 (1) | 29.44% (23.52–36.15%) | USD -412.51 | USD -81,263.70 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 197/198 (1) | 50.25% (43.33–57.16%) | USD -130.60 | USD -25,727.90 | USD -3,488.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/198 (3) | 30.26% (24.24–37.03%) | USD -47.31 | USD -9,226.00 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/198 (3) | 74.87% (68.34–80.44%) | USD 313.08 | USD 61,051.50 | USD -10,453.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/198 (3) | 20.51% (15.44–26.72%) | USD -644.27 | USD -125,633.50 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/198 (3) | 53.85% (46.84–60.70%) | USD -117.17 | USD -22,848.50 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 192/198 (6) | 40.10% (33.43–47.17%) | USD -35.52 | USD -6,820.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 192/198 (6) | 80.73% (74.57–85.68%) | USD 798.50 | USD 153,311.80 | USD -11,587.10 |
| HOLD_20_SESSIONS | 6 : 1 | 192/198 (6) | 16.15% (11.61–22.01%) | USD -1,047.15 | USD -201,053.20 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 192/198 (6) | 70.31% (63.50–76.33%) | USD 24.72 | USD 4,745.60 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 172/198 (26) | 37.79% (30.89–45.23%) | USD -43.00 | USD -7,395.20 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 172/198 (26) | 81.40% (74.92–86.50%) | USD 772.34 | USD 132,841.80 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 172/198 (26) | 18.02% (13.00–24.45%) | USD -1,073.30 | USD -184,608.20 | USD -5,483.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 172/198 (26) | 72.67% (65.57–78.78%) | USD -8.92 | USD -1,533.40 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/198 | 0.00% | USD -205,553.97 | USD -335,839.55 |
| -75% | 0/198 | 0.00% | USD -151,419.78 | USD -248,902.05 |
| -50% | 0/198 | 0.00% | USD -97,285.59 | USD -161,964.55 |
| -40% | 0/198 | 0.00% | USD -75,631.91 | USD -127,189.55 |
| -30% | 0/198 | 0.00% | USD -53,978.23 | USD -92,414.55 |
| -25% | 0/198 | 0.00% | USD -43,151.39 | USD -75,027.05 |
| -20% | 0/198 | 0.00% | USD -32,324.56 | USD -57,639.55 |
| -15% | 0/198 | 0.00% | USD -21,497.72 | USD -40,252.05 |
| -10% | 2/198 | 1.01% | USD -10,672.97 | USD -23,103.25 |
| -5% | 96/198 | 48.48% | USD -479.34 | USD -8,881.55 |
| 0% | 198/198 | 100.00% | USD 2,214.10 | USD 589.45 |
| 5% | 198/198 | 100.00% | USD 2,213.28 | USD 589.45 |
| 10% | 198/198 | 100.00% | USD 2,213.28 | USD 589.45 |
| 20% | 198/198 | 100.00% | USD 2,213.28 | USD 589.45 |

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