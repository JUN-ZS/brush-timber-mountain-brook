# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 449.73 / USD 2,664.70; mean absolute mismatch USD 2,214.97; mean match score 16.72%.
- Actual selected contract ratios: {'1:6': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 273/118/0 | 69.82% (65.10–74.16%) | USD 184.28 | USD 469.90 | USD 72,051.90 | USD -15,946.10 | 1 |
| HOLD_10_SESSIONS | 389/392 | 295/94/0 | 75.84% (71.34–79.82%) | USD 306.14 | USD 852.90 | USD 119,090.10 | USD -28,812.10 | 3 |
| HOLD_20_SESSIONS | 384/392 | 320/64/0 | 83.33% (79.28–86.73%) | USD 589.39 | USD 1,390.90 | USD 226,326.60 | USD -51,851.10 | 8 |
| EXIT_AT_DTE_LE_7 | 347/392 | 292/55/0 | 84.15% (79.94–87.62%) | USD 510.29 | USD 1,632.90 | USD 177,072.30 | USD -44,688.10 | 45 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -75.91 | USD 339.28 |
| HOLD_10_SESSIONS | USD -105.69 | USD 490.94 |
| HOLD_20_SESSIONS | USD -174.87 | USD 843.36 |
| EXIT_AT_DTE_LE_7 | USD -179.31 | USD 768.71 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 72.12% | USD 263.38 | USD 102,980.00 | USD -15,867.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 72.12% | USD 254.28 | USD 99,421.90 | USD -15,876.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 71.87% | USD 228.38 | USD 89,295.00 | USD -15,902.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 71.36% | USD 219.28 | USD 85,736.90 | USD -15,911.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 70.59% | USD 193.38 | USD 75,610.00 | USD -15,937.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 69.82% | USD 184.28 | USD 72,051.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 68.03% | USD 123.38 | USD 48,240.00 | USD -16,007.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 67.52% | USD 114.28 | USD 44,681.90 | USD -16,016.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 389 | 76.61% | USD 385.24 | USD 149,860.00 | USD -28,733.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 389 | 76.61% | USD 376.14 | USD 146,320.10 | USD -28,742.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 389 | 76.09% | USD 350.24 | USD 136,245.00 | USD -28,768.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 389 | 76.09% | USD 341.14 | USD 132,705.10 | USD -28,777.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 389 | 76.09% | USD 315.24 | USD 122,630.00 | USD -28,803.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 389 | 75.84% | USD 306.14 | USD 119,090.10 | USD -28,812.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 389 | 75.06% | USD 245.24 | USD 95,400.00 | USD -28,873.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 389 | 75.06% | USD 236.14 | USD 91,860.10 | USD -28,882.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 384 | 83.85% | USD 668.49 | USD 256,701.00 | USD -51,772.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 384 | 83.85% | USD 659.39 | USD 253,206.60 | USD -51,781.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 384 | 83.59% | USD 633.49 | USD 243,261.00 | USD -51,807.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 384 | 83.59% | USD 624.39 | USD 239,766.60 | USD -51,816.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 384 | 83.33% | USD 598.49 | USD 229,821.00 | USD -51,842.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 384 | 83.33% | USD 589.39 | USD 226,326.60 | USD -51,851.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 384 | 83.33% | USD 528.49 | USD 202,941.00 | USD -51,912.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 384 | 83.33% | USD 519.39 | USD 199,446.60 | USD -51,921.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 347 | 84.44% | USD 589.39 | USD 204,520.00 | USD -44,609.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 347 | 84.44% | USD 580.29 | USD 201,362.30 | USD -44,618.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 347 | 84.15% | USD 554.39 | USD 192,375.00 | USD -44,644.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 347 | 84.15% | USD 545.29 | USD 189,217.30 | USD -44,653.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 347 | 84.15% | USD 519.39 | USD 180,230.00 | USD -44,679.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 347 | 84.15% | USD 510.29 | USD 177,072.30 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 347 | 83.86% | USD 449.39 | USD 155,940.00 | USD -44,749.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 347 | 83.86% | USD 440.29 | USD 152,782.30 | USD -44,758.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 32.23% (27.79–37.01%) | USD -41.96 | USD -16,406.60 | USD -1,278.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 69.82% (65.10–74.16%) | USD 184.28 | USD 72,051.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 24.30% (20.31–28.78%) | USD -478.00 | USD -186,898.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 391/392 (1) | 49.36% (44.44–54.30%) | USD -122.60 | USD -47,934.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 389/392 (3) | 37.28% (32.62–42.18%) | USD -46.47 | USD -18,076.40 | USD -2,810.60 |
| HOLD_10_SESSIONS | 1 : 6 | 389/392 (3) | 75.84% (71.34–79.82%) | USD 306.14 | USD 119,090.10 | USD -28,812.10 |
| HOLD_10_SESSIONS | 6 : 1 | 389/392 (3) | 21.08% (17.32–25.41%) | USD -631.43 | USD -245,624.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 389/392 (3) | 58.35% (53.40–63.15%) | USD -115.35 | USD -44,872.30 | USD -16,442.70 |
| HOLD_20_SESSIONS | 1 : 1 | 384/392 (8) | 41.15% (36.34–46.13%) | USD -56.91 | USD -21,852.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 384/392 (8) | 83.33% (79.28–86.73%) | USD 589.39 | USD 226,326.60 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 384/392 (8) | 15.36% (12.10–19.31%) | USD -987.74 | USD -379,293.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 384/392 (8) | 71.61% (66.91–75.89%) | USD -98.37 | USD -37,773.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 347/392 (45) | 39.19% (34.20–44.42%) | USD -73.80 | USD -25,607.20 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 347/392 (45) | 84.15% (79.94–87.62%) | USD 510.29 | USD 177,072.30 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 347/392 (45) | 16.14% (12.64–20.38%) | USD -1,026.87 | USD -356,322.70 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 347/392 (45) | 71.76% (66.80–76.24%) | USD -178.37 | USD -61,892.90 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -205,229.29 | USD -336,022.55 |
| -75% | 0/392 | 0.00% | USD -151,294.08 | USD -248,786.55 |
| -50% | 0/392 | 0.00% | USD -97,358.87 | USD -161,550.55 |
| -40% | 0/392 | 0.00% | USD -75,784.78 | USD -126,656.15 |
| -30% | 0/392 | 0.00% | USD -54,210.70 | USD -91,761.75 |
| -25% | 0/392 | 0.00% | USD -43,423.66 | USD -74,395.55 |
| -20% | 0/392 | 0.00% | USD -32,636.61 | USD -58,015.55 |
| -15% | 3/392 | 0.77% | USD -21,856.46 | USD -41,635.55 |
| -10% | 10/392 | 2.55% | USD -11,120.51 | USD -25,255.55 |
| -5% | 166/392 | 42.35% | USD -876.67 | USD -8,987.60 |
| 0% | 392/392 | 100.00% | USD 2,175.59 | USD 573.45 |
| 5% | 392/392 | 100.00% | USD 2,175.42 | USD 573.45 |
| 10% | 392/392 | 100.00% | USD 2,175.42 | USD 573.45 |
| 20% | 392/392 | 100.00% | USD 2,175.42 | USD 573.45 |

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