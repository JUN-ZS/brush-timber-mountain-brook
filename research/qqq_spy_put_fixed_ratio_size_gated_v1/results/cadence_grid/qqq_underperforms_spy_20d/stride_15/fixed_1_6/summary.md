# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 834 checks; 81 qualified; 753 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 457.25 / USD 2,630.00; mean absolute mismatch USD 2,172.75; mean match score 17.23%.
- Actual selected contract ratios: {'1:6': 81}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 81; entered cohorts: 81; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 80/81 | 45/35/0 | 56.25% (45.34–66.59%) | USD -143.24 | USD 297.90 | USD -11,459.00 | USD -4,827.10 | 1 |
| HOLD_10_SESSIONS | 80/81 | 58/22/0 | 72.50% (61.86–81.08%) | USD -124.14 | USD 707.40 | USD -9,931.00 | USD -18,784.10 | 1 |
| HOLD_20_SESSIONS | 78/81 | 62/16/0 | 79.49% (69.25–86.96%) | USD 472.19 | USD 1,440.40 | USD 36,831.20 | USD -12,548.10 | 3 |
| EXIT_AT_DTE_LE_7 | 71/81 | 59/12/0 | 83.10% (72.74–90.06%) | USD 245.10 | USD 1,645.90 | USD 17,401.90 | USD -23,852.10 | 10 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 5.31 | USD -69.45 |
| HOLD_10_SESSIONS | USD -50.14 | USD 5.10 |
| HOLD_20_SESSIONS | USD -112.09 | USD 663.38 |
| EXIT_AT_DTE_LE_7 | USD -101.80 | USD 426.00 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 80 | 58.75% | USD -64.14 | USD -5,131.00 | USD -4,748.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 80 | 58.75% | USD -73.24 | USD -5,859.00 | USD -4,757.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 80 | 58.75% | USD -99.14 | USD -7,931.00 | USD -4,783.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 80 | 57.50% | USD -108.24 | USD -8,659.00 | USD -4,792.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 80 | 57.50% | USD -134.14 | USD -10,731.00 | USD -4,818.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 80 | 56.25% | USD -143.24 | USD -11,459.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 80 | 56.25% | USD -204.14 | USD -16,331.00 | USD -4,888.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 80 | 55.00% | USD -213.24 | USD -17,059.00 | USD -4,897.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 80 | 76.25% | USD -45.04 | USD -3,603.00 | USD -18,705.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 80 | 76.25% | USD -54.14 | USD -4,331.00 | USD -18,714.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 80 | 75.00% | USD -80.04 | USD -6,403.00 | USD -18,740.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 80 | 75.00% | USD -89.14 | USD -7,131.00 | USD -18,749.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 80 | 72.50% | USD -115.04 | USD -9,203.00 | USD -18,775.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 80 | 72.50% | USD -124.14 | USD -9,931.00 | USD -18,784.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 80 | 72.50% | USD -185.04 | USD -14,803.00 | USD -18,845.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 80 | 72.50% | USD -194.14 | USD -15,531.00 | USD -18,854.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 78 | 80.77% | USD 551.29 | USD 43,001.00 | USD -12,469.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 78 | 80.77% | USD 542.19 | USD 42,291.20 | USD -12,478.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 78 | 80.77% | USD 516.29 | USD 40,271.00 | USD -12,504.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 78 | 80.77% | USD 507.19 | USD 39,561.20 | USD -12,513.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 78 | 80.77% | USD 481.29 | USD 37,541.00 | USD -12,539.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 78 | 79.49% | USD 472.19 | USD 36,831.20 | USD -12,548.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 78 | 79.49% | USD 411.29 | USD 32,081.00 | USD -12,609.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 78 | 79.49% | USD 402.19 | USD 31,371.20 | USD -12,618.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 71 | 83.10% | USD 324.20 | USD 23,018.00 | USD -23,773.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 71 | 83.10% | USD 315.10 | USD 22,371.90 | USD -23,782.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 71 | 83.10% | USD 289.20 | USD 20,533.00 | USD -23,808.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 71 | 83.10% | USD 280.10 | USD 19,886.90 | USD -23,817.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 71 | 83.10% | USD 254.20 | USD 18,048.00 | USD -23,843.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 71 | 83.10% | USD 245.10 | USD 17,401.90 | USD -23,852.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 71 | 83.10% | USD 184.20 | USD 13,078.00 | USD -23,913.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 71 | 83.10% | USD 175.10 | USD 12,431.90 | USD -23,922.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 80/81 (1) | 32.50% (23.24–43.36%) | USD -28.86 | USD -2,309.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 80/81 (1) | 56.25% (45.34–66.59%) | USD -143.24 | USD -11,459.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 80/81 (1) | 31.25% (22.15–42.07%) | USD -58.80 | USD -4,704.00 | USD -3,885.10 |
| HOLD_5_SESSIONS | 4 : 5 | 80/81 (1) | 45.00% (34.58–55.88%) | USD -138.32 | USD -11,066.00 | USD -2,180.70 |
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
| -100% | 0/81 | 0.00% | USD -207,500.95 | USD -335,839.55 |
| -75% | 0/81 | 0.00% | USD -152,905.84 | USD -248,902.05 |
| -50% | 0/81 | 0.00% | USD -98,310.73 | USD -161,964.55 |
| -40% | 0/81 | 0.00% | USD -76,472.69 | USD -127,189.55 |
| -30% | 0/81 | 0.00% | USD -54,634.64 | USD -92,414.55 |
| -25% | 0/81 | 0.00% | USD -43,715.62 | USD -75,027.05 |
| -20% | 0/81 | 0.00% | USD -32,796.60 | USD -57,639.55 |
| -15% | 0/81 | 0.00% | USD -21,877.58 | USD -40,252.05 |
| -10% | 1/81 | 1.23% | USD -10,963.69 | USD -23,103.25 |
| -5% | 37/81 | 45.68% | USD -729.88 | USD -8,803.90 |
| 0% | 81/81 | 100.00% | USD 2,133.20 | USD 722.45 |
| 5% | 81/81 | 100.00% | USD 2,133.20 | USD 722.45 |
| 10% | 81/81 | 100.00% | USD 2,133.20 | USD 722.45 |
| 20% | 81/81 | 100.00% | USD 2,133.20 | USD 722.45 |

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