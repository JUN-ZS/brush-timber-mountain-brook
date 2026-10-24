# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 834 checks; 81 qualified; 753 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 457.25 / USD 1,315.00; mean absolute mismatch USD 857.75; mean match score 34.46%.
- Actual selected contract ratios: {'1:3': 81}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 81; entered cohorts: 81; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 80/81 | 44/36/0 | 55.00% (44.12–65.42%) | USD -74.71 | USD 90.30 | USD -5,977.00 | USD -1,914.20 | 1 |
| HOLD_10_SESSIONS | 80/81 | 59/21/0 | 73.75% (63.18–82.14%) | USD -92.79 | USD 267.80 | USD -7,423.00 | USD -8,076.20 | 1 |
| HOLD_20_SESSIONS | 78/81 | 64/14/0 | 82.05% (72.10–89.00%) | USD 174.40 | USD 535.30 | USD 13,603.40 | USD -5,230.20 | 3 |
| EXIT_AT_DTE_LE_7 | 71/81 | 58/13/0 | 81.69% (71.15–88.98%) | USD 66.00 | USD 639.80 | USD 4,685.80 | USD -9,106.20 | 10 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 5.47 | USD -34.99 |
| HOLD_10_SESSIONS | USD -50.14 | USD 2.55 |
| HOLD_20_SESSIONS | USD -112.09 | USD 331.69 |
| EXIT_AT_DTE_LE_7 | USD -101.80 | USD 213.00 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 80 | 58.75% | USD -29.51 | USD -2,361.00 | USD -1,869.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 80 | 58.75% | USD -34.71 | USD -2,777.00 | USD -1,874.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 80 | 56.25% | USD -49.51 | USD -3,961.00 | USD -1,889.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 80 | 55.00% | USD -54.71 | USD -4,377.00 | USD -1,894.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 80 | 55.00% | USD -69.51 | USD -5,561.00 | USD -1,909.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 80 | 55.00% | USD -74.71 | USD -5,977.00 | USD -1,914.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 80 | 52.50% | USD -109.51 | USD -8,761.00 | USD -1,949.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 80 | 51.25% | USD -114.71 | USD -9,177.00 | USD -1,954.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 80 | 73.75% | USD -47.59 | USD -3,807.00 | USD -8,031.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 80 | 73.75% | USD -52.79 | USD -4,223.00 | USD -8,036.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 80 | 73.75% | USD -67.59 | USD -5,407.00 | USD -8,051.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 80 | 73.75% | USD -72.79 | USD -5,823.00 | USD -8,056.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 80 | 73.75% | USD -87.59 | USD -7,007.00 | USD -8,071.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 80 | 73.75% | USD -92.79 | USD -7,423.00 | USD -8,076.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 80 | 72.50% | USD -127.59 | USD -10,207.00 | USD -8,111.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 80 | 72.50% | USD -132.79 | USD -10,623.00 | USD -8,116.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 78 | 82.05% | USD 219.60 | USD 17,129.00 | USD -5,185.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 78 | 82.05% | USD 214.40 | USD 16,723.40 | USD -5,190.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 78 | 82.05% | USD 199.60 | USD 15,569.00 | USD -5,205.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 78 | 82.05% | USD 194.40 | USD 15,163.40 | USD -5,210.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 78 | 82.05% | USD 179.60 | USD 14,009.00 | USD -5,225.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 78 | 82.05% | USD 174.40 | USD 13,603.40 | USD -5,230.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 78 | 82.05% | USD 139.60 | USD 10,889.00 | USD -5,265.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 78 | 82.05% | USD 134.40 | USD 10,483.40 | USD -5,270.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 71 | 81.69% | USD 111.20 | USD 7,895.00 | USD -9,061.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 71 | 81.69% | USD 106.00 | USD 7,525.80 | USD -9,066.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 71 | 81.69% | USD 91.20 | USD 6,475.00 | USD -9,081.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 71 | 81.69% | USD 86.00 | USD 6,105.80 | USD -9,086.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 71 | 81.69% | USD 71.20 | USD 5,055.00 | USD -9,101.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 71 | 81.69% | USD 66.00 | USD 4,685.80 | USD -9,106.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 71 | 81.69% | USD 31.20 | USD 2,215.00 | USD -9,141.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 71 | 81.69% | USD 26.00 | USD 1,845.80 | USD -9,146.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 80/81 (1) | 32.50% (23.24–43.36%) | USD -28.79 | USD -2,303.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 80/81 (1) | 56.25% (45.34–66.59%) | USD -143.60 | USD -11,488.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 80/81 (1) | 31.25% (22.15–42.07%) | USD -57.91 | USD -4,633.00 | USD -3,885.10 |
| HOLD_5_SESSIONS | 4 : 5 | 80/81 (1) | 45.00% (34.58–55.88%) | USD -138.11 | USD -11,049.00 | USD -2,180.70 |
| HOLD_10_SESSIONS | 1 : 1 | 80/81 (1) | 30.00% (21.06–40.77%) | USD -71.89 | USD -5,751.00 | USD -1,001.60 |
| HOLD_10_SESSIONS | 1 : 6 | 80/81 (1) | 72.50% (61.86–81.08%) | USD -124.14 | USD -9,931.00 | USD -18,784.10 |
| HOLD_10_SESSIONS | 6 : 1 | 80/81 (1) | 22.50% (14.73–32.79%) | USD -379.07 | USD -30,326.00 | USD -3,854.10 |
| HOLD_10_SESSIONS | 4 : 5 | 80/81 (1) | 48.75% (38.11–59.51%) | USD -298.00 | USD -23,840.00 | USD -7,319.70 |
| HOLD_20_SESSIONS | 1 : 1 | 78/81 (3) | 32.05% (22.75–43.04%) | USD -24.13 | USD -1,881.80 | USD -612.60 |
| HOLD_20_SESSIONS | 1 : 6 | 78/81 (3) | 79.49% (69.25–86.96%) | USD 472.19 | USD 36,831.20 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 78/81 (3) | 19.23% (12.02–29.33%) | USD -641.07 | USD -50,003.80 | USD -4,716.10 |
| HOLD_20_SESSIONS | 4 : 5 | 78/81 (3) | 70.51% (59.62–79.48%) | USD 2.76 | USD 215.40 | USD -3,888.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 71/81 (10) | 32.39% (22.66–43.94%) | USD -53.40 | USD -3,791.60 | USD -1,422.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 71/81 (10) | 83.10% (72.74–90.06%) | USD 245.10 | USD 17,401.90 | USD -23,852.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 71/81 (10) | 12.68% (6.81–22.37%) | USD -618.92 | USD -43,943.10 | USD -4,207.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 71/81 (10) | 70.42% (58.98–79.77%) | USD -153.91 | USD -10,927.70 | USD -8,108.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/81 | 0.00% | USD -88,165.66 | USD -138,284.60 |
| -75% | 0/81 | 0.00% | USD -65,032.87 | USD -102,619.35 |
| -50% | 0/81 | 0.00% | USD -41,900.08 | USD -66,954.10 |
| -40% | 0/81 | 0.00% | USD -32,646.96 | USD -52,688.00 |
| -30% | 0/81 | 0.00% | USD -23,393.84 | USD -38,421.90 |
| -25% | 0/81 | 0.00% | USD -18,767.28 | USD -31,288.85 |
| -20% | 0/81 | 0.00% | USD -14,140.72 | USD -24,155.80 |
| -15% | 0/81 | 0.00% | USD -9,514.16 | USD -17,022.75 |
| -10% | 1/81 | 1.23% | USD -4,888.33 | USD -9,889.70 |
| -5% | 36/81 | 44.44% | USD -480.40 | USD -3,798.85 |
| 0% | 81/81 | 100.00% | USD 835.15 | USD 283.40 |
| 5% | 81/81 | 100.00% | USD 835.15 | USD 283.40 |
| 10% | 81/81 | 100.00% | USD 835.15 | USD 283.40 |
| 20% | 81/81 | 100.00% | USD 835.15 | USD 283.40 |

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