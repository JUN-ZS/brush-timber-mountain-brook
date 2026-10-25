# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 704.62 / USD 1,399.94; mean absolute mismatch USD 695.34; mean match score 54.33%.
- Actual selected contract ratios: {'1:6': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 389/392 | 322/67/0 | 82.78% (78.71–86.20%) | USD 170.62 | USD 408.90 | USD 66,372.10 | USD -17,691.10 | 3 |
| HOLD_10_SESSIONS | 46/392 | 37/9/0 | 80.43% (66.83–89.35%) | USD -1,246.01 | USD 484.90 | USD -57,316.60 | USD -33,073.10 | 346 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| HOLD_20_OR_DTE_LE_7 | 391/392 | 312/79/0 | 79.80% (75.53–83.48%) | USD -18.40 | USD 360.90 | USD -7,195.10 | USD -26,841.10 | 1 |
| EXIT_AT_DTE_LE_7 | 391/392 | 312/79/0 | 79.80% (75.53–83.48%) | USD -18.40 | USD 360.90 | USD -7,195.10 | USD -26,841.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -158.05 | USD 407.77 |
| HOLD_10_SESSIONS | USD 55.26 | USD -1,222.17 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -104.72 | USD 165.42 |
| EXIT_AT_DTE_LE_7 | USD -104.72 | USD 165.42 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 389 | 84.58% | USD 249.72 | USD 97,142.00 | USD -17,612.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 389 | 84.58% | USD 240.62 | USD 93,602.10 | USD -17,621.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 389 | 83.29% | USD 214.72 | USD 83,527.00 | USD -17,647.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 389 | 83.29% | USD 205.62 | USD 79,987.10 | USD -17,656.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 389 | 83.03% | USD 179.72 | USD 69,912.00 | USD -17,682.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 389 | 82.78% | USD 170.62 | USD 66,372.10 | USD -17,691.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 389 | 79.43% | USD 109.72 | USD 42,682.00 | USD -17,752.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 389 | 78.66% | USD 100.62 | USD 39,142.10 | USD -17,761.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 46 | 80.43% | USD -1,166.91 | USD -53,678.00 | USD -32,994.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 46 | 80.43% | USD -1,176.01 | USD -54,096.60 | USD -33,003.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 46 | 80.43% | USD -1,201.91 | USD -55,288.00 | USD -33,029.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 46 | 80.43% | USD -1,211.01 | USD -55,706.60 | USD -33,038.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 46 | 80.43% | USD -1,236.91 | USD -56,898.00 | USD -33,064.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 46 | 80.43% | USD -1,246.01 | USD -57,316.60 | USD -33,073.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 46 | 80.43% | USD -1,306.91 | USD -60,118.00 | USD -33,134.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 46 | 80.43% | USD -1,316.01 | USD -60,536.60 | USD -33,143.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 391 | 81.07% | USD 60.70 | USD 23,733.00 | USD -26,762.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 391 | 80.56% | USD 51.60 | USD 20,174.90 | USD -26,771.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 391 | 80.31% | USD 25.70 | USD 10,048.00 | USD -26,797.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 391 | 80.31% | USD 16.60 | USD 6,489.90 | USD -26,806.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 391 | 79.80% | USD -9.30 | USD -3,637.00 | USD -26,832.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 391 | 79.80% | USD -18.40 | USD -7,195.10 | USD -26,841.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 391 | 75.70% | USD -79.30 | USD -31,007.00 | USD -26,902.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 391 | 75.19% | USD -88.40 | USD -34,565.10 | USD -26,911.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 81.07% | USD 60.70 | USD 23,733.00 | USD -26,762.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 80.56% | USD 51.60 | USD 20,174.90 | USD -26,771.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 80.31% | USD 25.70 | USD 10,048.00 | USD -26,797.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 80.31% | USD 16.60 | USD 6,489.90 | USD -26,806.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 79.80% | USD -9.30 | USD -3,637.00 | USD -26,832.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 79.80% | USD -18.40 | USD -7,195.10 | USD -26,841.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 75.70% | USD -79.30 | USD -31,007.00 | USD -26,902.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 75.19% | USD -88.40 | USD -34,565.10 | USD -26,911.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 389/392 (3) | 28.79% (24.52–33.48%) | USD -112.68 | USD -43,834.40 | USD -1,335.60 |
| HOLD_5_SESSIONS | 1 : 6 | 389/392 (3) | 82.78% (78.71–86.20%) | USD 170.62 | USD 66,372.10 | USD -17,691.10 |
| HOLD_5_SESSIONS | 6 : 1 | 389/392 (3) | 27.76% (23.55–32.41%) | USD -959.42 | USD -373,212.90 | USD -13,332.10 |
| HOLD_5_SESSIONS | 5 : 5 | 389/392 (3) | 28.79% (24.52–33.48%) | USD -563.42 | USD -219,172.00 | USD -6,678.00 |
| HOLD_10_SESSIONS | 1 : 1 | 46/392 (346) | 30.43% (19.08–44.81%) | USD -171.03 | USD -7,867.60 | USD -2,506.60 |
| HOLD_10_SESSIONS | 1 : 6 | 46/392 (346) | 80.43% (66.83–89.35%) | USD -1,246.01 | USD -57,316.60 | USD -33,073.10 |
| HOLD_10_SESSIONS | 6 : 1 | 46/392 (346) | 36.96% (24.52–51.40%) | USD 48.77 | USD 2,243.40 | USD -10,106.10 |
| HOLD_10_SESSIONS | 5 : 5 | 46/392 (346) | 30.43% (19.08–44.81%) | USD -855.17 | USD -39,338.00 | USD -12,533.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/392 (392) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 391/392 (1) | 29.41% (25.11–34.11%) | USD -99.75 | USD -39,003.60 | USD -1,779.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 391/392 (1) | 79.80% (75.53–83.48%) | USD -18.40 | USD -7,195.10 | USD -26,841.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 391/392 (1) | 30.43% (26.08–35.17%) | USD -679.87 | USD -265,830.10 | USD -14,167.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 391/392 (1) | 29.41% (25.11–34.11%) | USD -498.77 | USD -195,018.00 | USD -8,898.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 29.41% (25.11–34.11%) | USD -99.75 | USD -39,003.60 | USD -1,779.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 79.80% (75.53–83.48%) | USD -18.40 | USD -7,195.10 | USD -26,841.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 30.43% (26.08–35.17%) | USD -679.87 | USD -265,830.10 | USD -14,167.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 391/392 (1) | 29.41% (25.11–34.11%) | USD -498.77 | USD -195,018.00 | USD -8,898.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -209,096.14 | USD -341,082.55 |
| -75% | 0/392 | 0.00% | USD -155,165.14 | USD -253,846.55 |
| -50% | 0/392 | 0.00% | USD -101,234.13 | USD -166,610.55 |
| -40% | 0/392 | 0.00% | USD -79,661.72 | USD -131,716.15 |
| -30% | 0/392 | 0.00% | USD -58,089.32 | USD -97,144.25 |
| -25% | 0/392 | 0.00% | USD -47,303.12 | USD -79,983.30 |
| -20% | 0/392 | 0.00% | USD -36,516.92 | USD -62,822.35 |
| -15% | 1/392 | 0.26% | USD -25,730.72 | USD -45,661.40 |
| -10% | 3/392 | 0.77% | USD -14,960.65 | USD -28,500.45 |
| -5% | 37/392 | 9.44% | USD -4,333.55 | USD -11,743.60 |
| 0% | 392/392 | 100.00% | USD 1,008.21 | USD 36.45 |
| 5% | 389/392 | 99.23% | USD 663.14 | USD -43.55 |
| 10% | 389/392 | 99.23% | USD 657.54 | USD -43.55 |
| 20% | 389/392 | 99.23% | USD 655.77 | USD -43.55 |

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