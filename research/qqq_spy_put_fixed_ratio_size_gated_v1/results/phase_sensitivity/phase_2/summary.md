# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.72 / USD 1,325.84; mean absolute mismatch USD 878.12; mean match score 33.51%.
- Actual selected contract ratios: {'1:3': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 390/391 | 258/132/0 | 66.15% (61.32–70.67%) | USD 25.21 | USD 151.30 | USD 9,830.00 | USD -3,633.20 | 1 |
| HOLD_10_SESSIONS | 389/391 | 289/100/0 | 74.29% (69.73–78.38%) | USD 82.60 | USD 298.80 | USD 32,131.20 | USD -7,020.20 | 2 |
| HOLD_20_SESSIONS | 386/391 | 313/73/0 | 81.09% (76.88–84.68%) | USD 189.94 | USD 536.80 | USD 73,317.80 | USD -18,370.20 | 5 |
| EXIT_AT_DTE_LE_7 | 350/391 | 296/54/0 | 84.57% (80.41–87.98%) | USD 192.10 | USD 653.30 | USD 67,234.00 | USD -19,463.20 | 41 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -63.03 | USD 133.43 |
| HOLD_10_SESSIONS | USD -97.16 | USD 224.96 |
| HOLD_20_SESSIONS | USD -163.90 | USD 399.05 |
| EXIT_AT_DTE_LE_7 | USD -194.67 | USD 431.97 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 390 | 68.97% | USD 70.41 | USD 27,458.00 | USD -3,588.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 390 | 68.21% | USD 65.21 | USD 25,430.00 | USD -3,593.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 390 | 66.92% | USD 50.41 | USD 19,658.00 | USD -3,608.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 390 | 66.92% | USD 45.21 | USD 17,630.00 | USD -3,613.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 390 | 66.41% | USD 30.41 | USD 11,858.00 | USD -3,628.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 390 | 66.15% | USD 25.21 | USD 9,830.00 | USD -3,633.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 390 | 63.08% | USD -9.59 | USD -3,742.00 | USD -3,668.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 390 | 62.56% | USD -14.79 | USD -5,770.00 | USD -3,673.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 389 | 75.58% | USD 127.80 | USD 49,714.00 | USD -6,975.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 389 | 75.58% | USD 122.60 | USD 47,691.20 | USD -6,980.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 389 | 75.32% | USD 107.80 | USD 41,934.00 | USD -6,995.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 389 | 75.06% | USD 102.60 | USD 39,911.20 | USD -7,000.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 389 | 74.29% | USD 87.80 | USD 34,154.00 | USD -7,015.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 389 | 74.29% | USD 82.60 | USD 32,131.20 | USD -7,020.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 389 | 71.21% | USD 47.80 | USD 18,594.00 | USD -7,055.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 389 | 71.21% | USD 42.60 | USD 16,571.20 | USD -7,060.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 386 | 81.61% | USD 235.14 | USD 90,765.00 | USD -18,325.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 386 | 81.61% | USD 229.94 | USD 88,757.80 | USD -18,330.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 386 | 81.35% | USD 215.14 | USD 83,045.00 | USD -18,345.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 386 | 81.35% | USD 209.94 | USD 81,037.80 | USD -18,350.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 386 | 81.09% | USD 195.14 | USD 75,325.00 | USD -18,365.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 386 | 81.09% | USD 189.94 | USD 73,317.80 | USD -18,370.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 386 | 80.31% | USD 155.14 | USD 59,885.00 | USD -18,405.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 386 | 80.31% | USD 149.94 | USD 57,877.80 | USD -18,410.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 350 | 84.86% | USD 237.30 | USD 83,054.00 | USD -19,418.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 350 | 84.86% | USD 232.10 | USD 81,234.00 | USD -19,423.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 350 | 84.86% | USD 217.30 | USD 76,054.00 | USD -19,438.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 350 | 84.86% | USD 212.10 | USD 74,234.00 | USD -19,443.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 350 | 84.57% | USD 197.30 | USD 69,054.00 | USD -19,458.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 350 | 84.57% | USD 192.10 | USD 67,234.00 | USD -19,463.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 350 | 84.29% | USD 157.30 | USD 55,054.00 | USD -19,498.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 350 | 84.29% | USD 152.10 | USD 53,234.00 | USD -19,503.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 390/391 (1) | 29.74% (25.42–34.46%) | USD -41.15 | USD -16,048.00 | USD -830.60 |
| HOLD_5_SESSIONS | 1 : 6 | 390/391 (1) | 68.21% (63.42–72.63%) | USD 124.74 | USD 48,647.00 | USD -7,837.10 |
| HOLD_5_SESSIONS | 6 : 1 | 390/391 (1) | 25.90% (21.80–30.47%) | USD -412.78 | USD -160,983.00 | USD -5,743.10 |
| HOLD_5_SESSIONS | 4 : 5 | 390/391 (1) | 43.59% (38.75–48.55%) | USD -131.42 | USD -51,253.00 | USD -4,723.70 |
| HOLD_10_SESSIONS | 1 : 1 | 389/391 (2) | 33.42% (28.91–38.25%) | USD -44.77 | USD -17,417.40 | USD -1,623.60 |
| HOLD_10_SESSIONS | 1 : 6 | 389/391 (2) | 74.81% (70.26–78.86%) | USD 273.66 | USD 106,454.10 | USD -15,115.10 |
| HOLD_10_SESSIONS | 6 : 1 | 389/391 (2) | 22.11% (18.27–26.49%) | USD -587.08 | USD -228,375.90 | USD -6,816.10 |
| HOLD_10_SESSIONS | 4 : 5 | 389/391 (2) | 56.56% (51.59–61.39%) | USD -115.41 | USD -44,895.30 | USD -9,192.70 |
| HOLD_20_SESSIONS | 1 : 1 | 386/391 (5) | 37.05% (32.38–41.97%) | USD -53.49 | USD -20,646.60 | USD -4,193.60 |
| HOLD_20_SESSIONS | 1 : 6 | 386/391 (5) | 81.09% (76.88–84.68%) | USD 555.09 | USD 214,264.40 | USD -40,143.10 |
| HOLD_20_SESSIONS | 6 : 1 | 386/391 (5) | 15.54% (12.27–19.50%) | USD -929.51 | USD -358,790.60 | USD -8,618.10 |
| HOLD_20_SESSIONS | 4 : 5 | 386/391 (5) | 69.95% (65.20–74.31%) | USD -92.24 | USD -35,604.20 | USD -23,862.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 350/391 (41) | 32.86% (28.15–37.94%) | USD -73.28 | USD -25,648.00 | USD -3,885.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 350/391 (41) | 84.29% (80.10–87.72%) | USD 590.16 | USD 206,557.00 | USD -43,254.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 350/391 (41) | 14.29% (11.01–18.34%) | USD -1,103.12 | USD -386,093.00 | USD -8,654.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 350/391 (41) | 73.43% (68.56–77.78%) | USD -160.43 | USD -56,151.00 | USD -23,215.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -87,211.91 | USD -137,346.60 |
| -75% | 0/391 | 0.00% | USD -64,354.98 | USD -101,744.85 |
| -50% | 0/391 | 0.00% | USD -41,498.05 | USD -66,143.10 |
| -40% | 0/391 | 0.00% | USD -32,355.28 | USD -51,902.40 |
| -30% | 0/391 | 0.00% | USD -23,212.51 | USD -37,661.70 |
| -25% | 0/391 | 0.00% | USD -18,641.12 | USD -30,739.60 |
| -20% | 0/391 | 0.00% | USD -14,069.73 | USD -24,183.20 |
| -15% | 2/391 | 0.51% | USD -9,498.77 | USD -17,626.80 |
| -10% | 8/391 | 2.05% | USD -4,946.32 | USD -11,070.40 |
| -5% | 145/391 | 37.08% | USD -572.31 | USD -4,514.00 |
| 0% | 391/391 | 100.00% | USD 855.77 | USD 262.40 |
| 5% | 391/391 | 100.00% | USD 855.52 | USD 262.40 |
| 10% | 391/391 | 100.00% | USD 855.52 | USD 262.40 |
| 20% | 391/391 | 100.00% | USD 855.52 | USD 262.40 |

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