# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 391 checks; 391 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 460.95 / USD 1,359.01; mean absolute mismatch USD 898.06; mean match score 33.66%.
- Actual selected contract ratios: {'1:3': 391}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 391; entered cohorts: 391; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 389/391 | 256/133/0 | 65.81% (60.96–70.35%) | USD 5.36 | USD 138.80 | USD 2,085.20 | USD -8,482.20 | 2 |
| HOLD_10_SESSIONS | 388/391 | 286/102/0 | 73.71% (69.11–77.84%) | USD 50.85 | USD 280.80 | USD 19,730.40 | USD -8,412.20 | 3 |
| HOLD_20_SESSIONS | 383/391 | 315/68/0 | 82.25% (78.10–85.75%) | USD 176.77 | USD 520.80 | USD 67,701.40 | USD -18,370.20 | 8 |
| EXIT_AT_DTE_LE_7 | 348/391 | 292/56/0 | 83.91% (79.68–87.40%) | USD 200.11 | USD 638.30 | USD 69,639.40 | USD -19,463.20 | 43 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -57.92 | USD 108.48 |
| HOLD_10_SESSIONS | USD -86.66 | USD 182.71 |
| HOLD_20_SESSIONS | USD -161.45 | USD 383.42 |
| EXIT_AT_DTE_LE_7 | USD -200.11 | USD 445.42 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 389 | 68.64% | USD 50.56 | USD 19,668.00 | USD -8,437.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 389 | 68.12% | USD 45.36 | USD 17,645.20 | USD -8,442.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 389 | 66.58% | USD 30.56 | USD 11,888.00 | USD -8,457.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 389 | 66.58% | USD 25.36 | USD 9,865.20 | USD -8,462.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 389 | 66.07% | USD 10.56 | USD 4,108.00 | USD -8,477.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 389 | 65.81% | USD 5.36 | USD 2,085.20 | USD -8,482.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 389 | 62.21% | USD -29.44 | USD -11,452.00 | USD -8,517.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 389 | 61.44% | USD -34.64 | USD -13,474.80 | USD -8,522.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 388 | 75.00% | USD 96.05 | USD 37,268.00 | USD -8,367.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 388 | 75.00% | USD 90.85 | USD 35,250.40 | USD -8,372.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 388 | 74.48% | USD 76.05 | USD 29,508.00 | USD -8,387.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 388 | 74.23% | USD 70.85 | USD 27,490.40 | USD -8,392.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 388 | 73.97% | USD 56.05 | USD 21,748.00 | USD -8,407.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 388 | 73.71% | USD 50.85 | USD 19,730.40 | USD -8,412.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 388 | 71.91% | USD 16.05 | USD 6,228.00 | USD -8,447.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 388 | 71.91% | USD 10.85 | USD 4,210.40 | USD -8,452.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 383 | 82.77% | USD 221.97 | USD 85,013.00 | USD -18,325.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 383 | 82.77% | USD 216.77 | USD 83,021.40 | USD -18,330.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 383 | 82.51% | USD 201.97 | USD 77,353.00 | USD -18,345.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 383 | 82.51% | USD 196.77 | USD 75,361.40 | USD -18,350.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 383 | 82.25% | USD 181.97 | USD 69,693.00 | USD -18,365.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 383 | 82.25% | USD 176.77 | USD 67,701.40 | USD -18,370.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 383 | 81.46% | USD 141.97 | USD 54,373.00 | USD -18,405.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 383 | 81.46% | USD 136.77 | USD 52,381.40 | USD -18,410.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 348 | 84.20% | USD 245.31 | USD 85,369.00 | USD -19,418.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 348 | 84.20% | USD 240.11 | USD 83,559.40 | USD -19,423.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 348 | 84.20% | USD 225.31 | USD 78,409.00 | USD -19,438.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 348 | 84.20% | USD 220.11 | USD 76,599.40 | USD -19,443.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 348 | 83.91% | USD 205.31 | USD 71,449.00 | USD -19,458.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 348 | 83.91% | USD 200.11 | USD 69,639.40 | USD -19,463.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 348 | 83.62% | USD 165.31 | USD 57,529.00 | USD -19,498.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 348 | 83.62% | USD 160.11 | USD 55,719.40 | USD -19,503.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 389/391 (2) | 29.05% (24.76–33.75%) | USD -44.36 | USD -17,255.40 | USD -830.60 |
| HOLD_5_SESSIONS | 1 : 6 | 389/391 (2) | 67.10% (62.28–71.58%) | USD 79.94 | USD 31,096.10 | USD -19,982.10 |
| HOLD_5_SESSIONS | 6 : 1 | 389/391 (2) | 26.99% (22.82–31.61%) | USD -390.45 | USD -151,883.90 | USD -6,090.10 |
| HOLD_5_SESSIONS | 4 : 5 | 389/391 (2) | 45.76% (40.87–50.73%) | USD -152.57 | USD -59,351.30 | USD -7,095.70 |
| HOLD_10_SESSIONS | 1 : 1 | 388/391 (3) | 34.79% (30.22–39.66%) | USD -48.36 | USD -18,762.80 | USD -1,623.60 |
| HOLD_10_SESSIONS | 1 : 6 | 388/391 (3) | 73.71% (69.11–77.84%) | USD 199.67 | USD 77,470.20 | USD -19,798.10 |
| HOLD_10_SESSIONS | 6 : 1 | 388/391 (3) | 22.94% (19.03–27.37%) | USD -538.17 | USD -208,809.80 | USD -6,942.10 |
| HOLD_10_SESSIONS | 4 : 5 | 388/391 (3) | 54.90% (49.92–59.78%) | USD -143.83 | USD -55,804.60 | USD -9,192.70 |
| HOLD_20_SESSIONS | 1 : 1 | 383/391 (8) | 37.86% (33.14–42.81%) | USD -56.25 | USD -21,542.80 | USD -4,193.60 |
| HOLD_20_SESSIONS | 1 : 6 | 383/391 (8) | 82.77% (78.66–86.22%) | USD 526.29 | USD 201,567.70 | USD -40,143.10 |
| HOLD_20_SESSIONS | 6 : 1 | 383/391 (8) | 15.40% (12.13–19.36%) | USD -920.02 | USD -352,367.30 | USD -8,979.10 |
| HOLD_20_SESSIONS | 4 : 5 | 383/391 (8) | 65.54% (60.64–70.12%) | USD -108.48 | USD -41,549.10 | USD -23,862.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 348/391 (43) | 33.05% (28.31–38.15%) | USD -74.24 | USD -25,833.80 | USD -3,885.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 348/391 (43) | 83.33% (79.06–86.88%) | USD 611.64 | USD 212,849.20 | USD -43,254.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 348/391 (43) | 14.37% (11.07–18.44%) | USD -1,131.28 | USD -393,685.80 | USD -9,512.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 348/391 (43) | 70.69% (65.70–75.23%) | USD -159.77 | USD -55,598.60 | USD -23,215.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/391 | 0.00% | USD -87,352.29 | USD -139,425.60 |
| -75% | 0/391 | 0.00% | USD -64,467.56 | USD -103,634.10 |
| -50% | 0/391 | 0.00% | USD -41,582.84 | USD -67,842.60 |
| -40% | 0/391 | 0.00% | USD -32,428.95 | USD -53,526.00 |
| -30% | 0/391 | 0.00% | USD -23,275.06 | USD -39,209.40 |
| -25% | 0/391 | 0.00% | USD -18,698.11 | USD -32,051.10 |
| -20% | 0/391 | 0.00% | USD -14,121.17 | USD -24,892.80 |
| -15% | 2/391 | 0.51% | USD -9,544.64 | USD -17,734.50 |
| -10% | 9/391 | 2.30% | USD -4,982.44 | USD -10,576.20 |
| -5% | 144/391 | 36.83% | USD -572.57 | USD -4,050.05 |
| 0% | 391/391 | 100.00% | USD 871.91 | USD 262.40 |
| 5% | 391/391 | 100.00% | USD 875.46 | USD 262.40 |
| 10% | 391/391 | 100.00% | USD 875.46 | USD 262.40 |
| 20% | 391/391 | 100.00% | USD 875.46 | USD 262.40 |

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