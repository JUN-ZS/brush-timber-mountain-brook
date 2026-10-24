# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 1164 checks; 199 qualified; 965 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 921.21 / USD 1,814.44; mean absolute mismatch USD 893.23; mean match score 50.29%.
- Actual selected contract ratios: {'2:4': 198}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 199; entered cohorts: 198; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 197/198 | 127/70/0 | 64.47% (57.57–70.82%) | USD -0.22 | USD 128.20 | USD -42.60 | USD -3,709.80 | 1 |
| HOLD_10_SESSIONS | 195/198 | 141/54/0 | 72.31% (65.64–78.11%) | USD 57.71 | USD 258.20 | USD 11,253.00 | USD -4,617.80 | 3 |
| HOLD_20_SESSIONS | 192/198 | 154/38/0 | 80.21% (74.00–85.23%) | USD 261.38 | USD 512.20 | USD 50,184.40 | USD -5,427.80 | 6 |
| EXIT_AT_DTE_LE_7 | 172/198 | 140/32/0 | 81.40% (74.92–86.50%) | USD 248.60 | USD 599.20 | USD 42,758.40 | USD -9,633.80 | 26 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -136.34 | USD 203.92 |
| HOLD_10_SESSIONS | USD -219.46 | USD 344.96 |
| HOLD_20_SESSIONS | USD -384.43 | USD 713.60 |
| EXIT_AT_DTE_LE_7 | USD -396.40 | USD 712.79 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 197 | 67.51% | USD 67.58 | USD 13,314.00 | USD -3,642.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 197 | 67.51% | USD 59.78 | USD 11,777.40 | USD -3,649.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 197 | 66.50% | USD 37.58 | USD 7,404.00 | USD -3,672.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 197 | 65.99% | USD 29.78 | USD 5,867.40 | USD -3,679.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 197 | 64.97% | USD 7.58 | USD 1,494.00 | USD -3,702.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 197 | 64.47% | USD -0.22 | USD -42.60 | USD -3,709.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 197 | 58.38% | USD -52.42 | USD -10,326.00 | USD -3,762.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 197 | 57.87% | USD -60.22 | USD -11,862.60 | USD -3,769.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 75.38% | USD 125.51 | USD 24,474.00 | USD -4,550.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 75.38% | USD 117.71 | USD 22,953.00 | USD -4,557.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 74.36% | USD 95.51 | USD 18,624.00 | USD -4,580.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 74.36% | USD 87.71 | USD 17,103.00 | USD -4,587.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 72.82% | USD 65.51 | USD 12,774.00 | USD -4,610.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 72.31% | USD 57.71 | USD 11,253.00 | USD -4,617.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 67.69% | USD 5.51 | USD 1,074.00 | USD -4,670.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 67.69% | USD -2.29 | USD -447.00 | USD -4,677.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 192 | 81.77% | USD 329.18 | USD 63,202.00 | USD -5,360.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 192 | 81.25% | USD 321.38 | USD 61,704.40 | USD -5,367.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 192 | 81.25% | USD 299.18 | USD 57,442.00 | USD -5,390.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 192 | 81.25% | USD 291.38 | USD 55,944.40 | USD -5,397.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 192 | 80.73% | USD 269.18 | USD 51,682.00 | USD -5,420.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 192 | 80.21% | USD 261.38 | USD 50,184.40 | USD -5,427.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 192 | 79.69% | USD 209.18 | USD 40,162.00 | USD -5,480.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 192 | 79.69% | USD 201.38 | USD 38,664.40 | USD -5,487.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 172 | 81.98% | USD 316.40 | USD 54,420.00 | USD -9,566.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 172 | 81.98% | USD 308.60 | USD 53,078.40 | USD -9,573.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 172 | 81.98% | USD 286.40 | USD 49,260.00 | USD -9,596.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 172 | 81.98% | USD 278.60 | USD 47,918.40 | USD -9,603.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 172 | 81.98% | USD 256.40 | USD 44,100.00 | USD -9,626.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 172 | 81.40% | USD 248.60 | USD 42,758.40 | USD -9,633.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 172 | 80.81% | USD 196.40 | USD 33,780.00 | USD -9,686.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 172 | 80.81% | USD 188.60 | USD 32,438.40 | USD -9,693.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 197/198 (1) | 31.47% (25.39–38.26%) | USD -39.79 | USD -7,838.20 | USD -544.60 |
| HOLD_5_SESSIONS | 1 : 6 | 197/198 (1) | 64.97% (58.08–71.29%) | USD 158.61 | USD 31,246.30 | USD -7,267.10 |
| HOLD_5_SESSIONS | 6 : 1 | 197/198 (1) | 28.93% (23.05–35.62%) | USD -437.13 | USD -86,113.70 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 197/198 (1) | 50.76% (43.83–57.66%) | USD -119.47 | USD -23,535.90 | USD -3,488.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/198 (3) | 30.26% (24.24–37.03%) | USD -46.09 | USD -8,987.00 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/198 (3) | 75.38% (68.89–80.90%) | USD 328.62 | USD 64,080.50 | USD -10,501.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/198 (3) | 20.51% (15.44–26.72%) | USD -651.23 | USD -126,989.50 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/198 (3) | 54.36% (47.35–61.20%) | USD -109.41 | USD -21,334.50 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 192/198 (6) | 39.58% (32.94–46.64%) | USD -36.41 | USD -6,991.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 192/198 (6) | 80.73% (74.57–85.68%) | USD 799.09 | USD 153,425.80 | USD -11,587.10 |
| HOLD_20_SESSIONS | 6 : 1 | 192/198 (6) | 16.15% (11.61–22.01%) | USD -1,053.98 | USD -202,364.20 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 192/198 (6) | 70.31% (63.50–76.33%) | USD 21.45 | USD 4,118.60 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 172/198 (26) | 37.79% (30.89–45.23%) | USD -42.60 | USD -7,327.20 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 172/198 (26) | 81.40% (74.92–86.50%) | USD 791.89 | USD 136,204.80 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 172/198 (26) | 18.02% (13.00–24.45%) | USD -1,090.09 | USD -187,495.20 | USD -5,483.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 172/198 (26) | 72.67% (65.57–78.78%) | USD -3.50 | USD -602.40 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/198 | 0.00% | USD -96,222.65 | USD -144,865.90 |
| -75% | 0/198 | 0.00% | USD -71,067.54 | USD -107,716.90 |
| -50% | 0/198 | 0.00% | USD -45,912.44 | USD -70,567.90 |
| -40% | 0/198 | 0.00% | USD -35,850.40 | USD -55,738.70 |
| -30% | 0/198 | 0.00% | USD -25,788.36 | USD -40,917.50 |
| -25% | 0/198 | 0.00% | USD -20,757.34 | USD -33,506.90 |
| -20% | 0/198 | 0.00% | USD -15,726.32 | USD -26,096.30 |
| -15% | 0/198 | 0.00% | USD -10,695.30 | USD -18,685.70 |
| -10% | 2/198 | 1.01% | USD -5,663.64 | USD -11,275.10 |
| -5% | 82/198 | 41.41% | USD -685.57 | USD -4,261.00 |
| 0% | 198/198 | 100.00% | USD 860.97 | USD 216.10 |
| 5% | 198/198 | 100.00% | USD 859.33 | USD 216.10 |
| 10% | 198/198 | 100.00% | USD 859.33 | USD 216.10 |
| 20% | 198/198 | 100.00% | USD 859.33 | USD 216.10 |

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