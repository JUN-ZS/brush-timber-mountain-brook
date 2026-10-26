# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 182.18 / USD 985.19; mean absolute mismatch USD 803.01; mean match score 18.98%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 191/196 | 107/84/0 | 56.02% (48.93–62.87%) | USD -213.72 | USD 98.90 | USD -40,820.10 | USD -7,102.10 | 5 |
| HOLD_5_OR_DTE_LE_7 | 191/196 | 107/84/0 | 56.02% (48.93–62.87%) | USD -213.72 | USD 98.90 | USD -40,820.10 | USD -7,102.10 | 5 |
| HOLD_5_OR_DTE_LE_14 | 194/196 | 101/93/0 | 52.06% (45.06–58.98%) | USD -265.78 | USD 33.90 | USD -51,561.40 | USD -7,102.10 | 2 |
| HOLD_10_SESSIONS | 145/196 | 91/54/0 | 62.76% (54.66–70.20%) | USD -244.27 | USD 204.90 | USD -35,418.50 | USD -8,992.10 | 51 |
| HOLD_10_OR_DTE_LE_7 | 173/196 | 105/68/0 | 60.69% (53.26–67.66%) | USD -164.33 | USD 189.90 | USD -28,429.30 | USD -9,131.10 | 23 |
| HOLD_10_OR_DTE_LE_14 | 194/196 | 104/90/0 | 53.61% (46.59–60.49%) | USD -259.88 | USD 54.40 | USD -50,417.40 | USD -7,102.10 | 2 |
| HOLD_15_SESSIONS | 4/196 | 1/3/0 | 25.00% (4.56–69.94%) | USD -4,163.10 | USD -2,293.60 | USD -16,652.40 | USD -12,865.10 | 192 |
| HOLD_15_OR_DTE_LE_7 | 173/196 | 104/69/0 | 60.12% (52.68–67.12%) | USD -233.81 | USD 188.90 | USD -40,449.30 | USD -9,131.10 | 23 |
| HOLD_15_OR_DTE_LE_14 | 194/196 | 104/90/0 | 53.61% (46.59–60.49%) | USD -259.88 | USD 54.40 | USD -50,417.40 | USD -7,102.10 | 2 |
| HOLD_20_SESSIONS | 0/196 | 0/0/0 | — | — | — | — | — | 196 |
| HOLD_20_OR_DTE_LE_7 | 173/196 | 104/69/0 | 60.12% (52.68–67.12%) | USD -233.81 | USD 188.90 | USD -40,449.30 | USD -9,131.10 | 23 |
| HOLD_20_OR_DTE_LE_14 | 194/196 | 104/90/0 | 53.61% (46.59–60.49%) | USD -259.88 | USD 54.40 | USD -50,417.40 | USD -7,102.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 16.17 | USD -150.79 |
| HOLD_5_OR_DTE_LE_7 | USD 16.17 | USD -150.79 |
| HOLD_5_OR_DTE_LE_14 | USD 17.26 | USD -203.94 |
| HOLD_10_SESSIONS | USD 36.85 | USD -202.01 |
| HOLD_10_OR_DTE_LE_7 | USD 22.91 | USD -108.14 |
| HOLD_10_OR_DTE_LE_14 | USD 16.94 | USD -197.72 |
| HOLD_15_SESSIONS | USD 897.50 | USD -4,981.50 |
| HOLD_15_OR_DTE_LE_7 | USD 37.57 | USD -192.28 |
| HOLD_15_OR_DTE_LE_14 | USD 16.94 | USD -197.72 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD 37.57 | USD -192.28 |
| HOLD_20_OR_DTE_LE_14 | USD 16.94 | USD -197.72 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 191 | 58.64% | USD -134.62 | USD -25,712.00 | USD -7,023.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 191 | 58.64% | USD -143.72 | USD -27,450.10 | USD -7,032.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 191 | 57.07% | USD -169.62 | USD -32,397.00 | USD -7,058.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 191 | 56.54% | USD -178.72 | USD -34,135.10 | USD -7,067.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 191 | 56.02% | USD -204.62 | USD -39,082.00 | USD -7,093.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 191 | 56.02% | USD -213.72 | USD -40,820.10 | USD -7,102.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 191 | 53.93% | USD -274.62 | USD -52,452.00 | USD -7,163.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 191 | 53.40% | USD -283.72 | USD -54,190.10 | USD -7,172.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 58.64% | USD -134.62 | USD -25,712.00 | USD -7,023.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 58.64% | USD -143.72 | USD -27,450.10 | USD -7,032.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 57.07% | USD -169.62 | USD -32,397.00 | USD -7,058.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 56.54% | USD -178.72 | USD -34,135.10 | USD -7,067.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 56.02% | USD -204.62 | USD -39,082.00 | USD -7,093.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 56.02% | USD -213.72 | USD -40,820.10 | USD -7,102.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 53.93% | USD -274.62 | USD -52,452.00 | USD -7,163.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 53.40% | USD -283.72 | USD -54,190.10 | USD -7,172.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 58.25% | USD -186.68 | USD -36,216.00 | USD -7,023.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 57.73% | USD -195.78 | USD -37,981.40 | USD -7,032.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 54.64% | USD -221.68 | USD -43,006.00 | USD -7,058.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 53.61% | USD -230.78 | USD -44,771.40 | USD -7,067.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 52.58% | USD -256.68 | USD -49,796.00 | USD -7,093.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 52.06% | USD -265.78 | USD -51,561.40 | USD -7,102.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 48.45% | USD -326.68 | USD -63,376.00 | USD -7,163.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 47.94% | USD -335.78 | USD -65,141.40 | USD -7,172.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 145 | 65.52% | USD -165.17 | USD -23,949.00 | USD -8,913.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 145 | 65.52% | USD -174.27 | USD -25,268.50 | USD -8,922.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 145 | 64.83% | USD -200.17 | USD -29,024.00 | USD -8,948.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 145 | 64.14% | USD -209.27 | USD -30,343.50 | USD -8,957.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 145 | 62.76% | USD -235.17 | USD -34,099.00 | USD -8,983.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 145 | 62.76% | USD -244.27 | USD -35,418.50 | USD -8,992.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 145 | 60.00% | USD -305.17 | USD -44,249.00 | USD -9,053.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 145 | 59.31% | USD -314.27 | USD -45,568.50 | USD -9,062.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 173 | 65.90% | USD -85.23 | USD -14,745.00 | USD -9,052.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 173 | 65.90% | USD -94.33 | USD -16,319.30 | USD -9,061.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 173 | 64.74% | USD -120.23 | USD -20,800.00 | USD -9,087.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 173 | 64.16% | USD -129.33 | USD -22,374.30 | USD -9,096.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 173 | 61.85% | USD -155.23 | USD -26,855.00 | USD -9,122.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 173 | 60.69% | USD -164.33 | USD -28,429.30 | USD -9,131.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 173 | 57.80% | USD -225.23 | USD -38,965.00 | USD -9,192.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 173 | 56.65% | USD -234.33 | USD -40,539.30 | USD -9,201.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -180.78 | USD -35,072.00 | USD -7,023.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 58.76% | USD -189.88 | USD -36,837.40 | USD -7,032.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 55.67% | USD -215.78 | USD -41,862.00 | USD -7,058.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 55.15% | USD -224.88 | USD -43,627.40 | USD -7,067.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 54.12% | USD -250.78 | USD -48,652.00 | USD -7,093.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.61% | USD -259.88 | USD -50,417.40 | USD -7,102.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 49.48% | USD -320.78 | USD -62,232.00 | USD -7,163.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 48.97% | USD -329.88 | USD -63,997.40 | USD -7,172.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 4 | 25.00% | USD -4,084.00 | USD -16,336.00 | USD -12,786.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 4 | 25.00% | USD -4,093.10 | USD -16,372.40 | USD -12,795.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 4 | 25.00% | USD -4,119.00 | USD -16,476.00 | USD -12,821.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 4 | 25.00% | USD -4,128.10 | USD -16,512.40 | USD -12,830.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 4 | 25.00% | USD -4,154.00 | USD -16,616.00 | USD -12,856.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 4 | 25.00% | USD -4,163.10 | USD -16,652.40 | USD -12,865.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 4 | 25.00% | USD -4,224.00 | USD -16,896.00 | USD -12,926.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 4 | 25.00% | USD -4,233.10 | USD -16,932.40 | USD -12,935.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 173 | 64.74% | USD -154.71 | USD -26,765.00 | USD -9,052.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 173 | 64.74% | USD -163.81 | USD -28,339.30 | USD -9,061.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 173 | 63.58% | USD -189.71 | USD -32,820.00 | USD -9,087.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 173 | 63.58% | USD -198.81 | USD -34,394.30 | USD -9,096.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 173 | 61.27% | USD -224.71 | USD -38,875.00 | USD -9,122.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 173 | 60.12% | USD -233.81 | USD -40,449.30 | USD -9,131.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 173 | 57.23% | USD -294.71 | USD -50,985.00 | USD -9,192.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 173 | 56.07% | USD -303.81 | USD -52,559.30 | USD -9,201.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -180.78 | USD -35,072.00 | USD -7,023.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 58.76% | USD -189.88 | USD -36,837.40 | USD -7,032.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 55.67% | USD -215.78 | USD -41,862.00 | USD -7,058.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 55.15% | USD -224.88 | USD -43,627.40 | USD -7,067.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 54.12% | USD -250.78 | USD -48,652.00 | USD -7,093.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.61% | USD -259.88 | USD -50,417.40 | USD -7,102.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 49.48% | USD -320.78 | USD -62,232.00 | USD -7,163.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 48.97% | USD -329.88 | USD -63,997.40 | USD -7,172.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 173 | 64.74% | USD -154.71 | USD -26,765.00 | USD -9,052.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 173 | 64.74% | USD -163.81 | USD -28,339.30 | USD -9,061.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 173 | 63.58% | USD -189.71 | USD -32,820.00 | USD -9,087.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 173 | 63.58% | USD -198.81 | USD -34,394.30 | USD -9,096.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 173 | 61.27% | USD -224.71 | USD -38,875.00 | USD -9,122.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 173 | 60.12% | USD -233.81 | USD -40,449.30 | USD -9,131.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 173 | 57.23% | USD -294.71 | USD -50,985.00 | USD -9,192.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 173 | 56.07% | USD -303.81 | USD -52,559.30 | USD -9,201.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -180.78 | USD -35,072.00 | USD -7,023.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 58.76% | USD -189.88 | USD -36,837.40 | USD -7,032.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 55.67% | USD -215.78 | USD -41,862.00 | USD -7,058.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 55.15% | USD -224.88 | USD -43,627.40 | USD -7,067.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 54.12% | USD -250.78 | USD -48,652.00 | USD -7,093.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.61% | USD -259.88 | USD -50,417.40 | USD -7,102.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 49.48% | USD -320.78 | USD -62,232.00 | USD -7,163.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 48.97% | USD -329.88 | USD -63,997.40 | USD -7,172.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 191/196 (5) | 23.56% (18.10–30.06%) | USD -31.56 | USD -6,028.60 | USD -533.60 |
| HOLD_5_SESSIONS | 1 : 6 | 191/196 (5) | 56.02% (48.93–62.87%) | USD -213.72 | USD -40,820.10 | USD -7,102.10 |
| HOLD_5_SESSIONS | 6 : 1 | 191/196 (5) | 32.46% (26.22–39.39%) | USD -7.23 | USD -1,380.10 | USD -9,295.10 |
| HOLD_5_SESSIONS | 5 : 5 | 191/196 (5) | 23.56% (18.10–30.06%) | USD -157.82 | USD -30,143.00 | USD -2,668.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 191/196 (5) | 23.56% (18.10–30.06%) | USD -31.56 | USD -6,028.60 | USD -533.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 191/196 (5) | 56.02% (48.93–62.87%) | USD -213.72 | USD -40,820.10 | USD -7,102.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 191/196 (5) | 32.46% (26.22–39.39%) | USD -7.23 | USD -1,380.10 | USD -9,295.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 191/196 (5) | 23.56% (18.10–30.06%) | USD -157.82 | USD -30,143.00 | USD -2,668.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -39.33 | USD -7,630.40 | USD -569.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/196 (2) | 52.06% (45.06–58.98%) | USD -265.78 | USD -51,561.40 | USD -7,102.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/196 (2) | 32.47% (26.28–39.35%) | USD -9.54 | USD -1,851.40 | USD -9,295.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -196.66 | USD -38,152.00 | USD -2,848.00 |
| HOLD_10_SESSIONS | 1 : 1 | 145/196 (51) | 32.41% (25.33–40.40%) | USD -19.42 | USD -2,816.00 | USD -835.60 |
| HOLD_10_SESSIONS | 1 : 6 | 145/196 (51) | 62.76% (54.66–70.20%) | USD -244.27 | USD -35,418.50 | USD -8,992.10 |
| HOLD_10_SESSIONS | 6 : 1 | 145/196 (51) | 34.48% (27.24–42.53%) | USD 108.32 | USD 15,706.50 | USD -4,176.10 |
| HOLD_10_SESSIONS | 5 : 5 | 145/196 (51) | 32.41% (25.33–40.40%) | USD -97.10 | USD -14,080.00 | USD -4,178.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 173/196 (23) | 30.64% (24.25–37.86%) | USD -17.72 | USD -3,064.80 | USD -481.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 173/196 (23) | 60.69% (53.26–67.66%) | USD -164.33 | USD -28,429.30 | USD -9,131.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 173/196 (23) | 30.06% (23.72–37.26%) | USD 40.32 | USD 6,975.70 | USD -4,176.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 173/196 (23) | 30.64% (24.25–37.86%) | USD -88.58 | USD -15,324.00 | USD -2,408.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -38.62 | USD -7,491.40 | USD -626.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/196 (2) | 53.61% (46.59–60.49%) | USD -259.88 | USD -50,417.40 | USD -7,102.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/196 (2) | 32.47% (26.28–39.35%) | USD -10.42 | USD -2,022.40 | USD -9,295.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -193.08 | USD -37,457.00 | USD -3,133.00 |
| HOLD_15_SESSIONS | 1 : 1 | 4/196 (192) | 50.00% (15.00–85.00%) | USD 44.65 | USD 178.60 | USD -363.60 |
| HOLD_15_SESSIONS | 1 : 6 | 4/196 (192) | 25.00% (4.56–69.94%) | USD -4,163.10 | USD -16,652.40 | USD -12,865.10 |
| HOLD_15_SESSIONS | 6 : 1 | 4/196 (192) | 75.00% (30.06–95.44%) | USD 4,475.65 | USD 17,902.60 | USD -782.10 |
| HOLD_15_SESSIONS | 5 : 5 | 4/196 (192) | 50.00% (15.00–85.00%) | USD 223.25 | USD 893.00 | USD -1,818.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 173/196 (23) | 30.64% (24.25–37.86%) | USD -17.08 | USD -2,954.80 | USD -481.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 173/196 (23) | 60.12% (52.68–67.12%) | USD -233.81 | USD -40,449.30 | USD -9,131.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 173/196 (23) | 30.06% (23.72–37.26%) | USD 114.25 | USD 19,765.70 | USD -4,176.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 173/196 (23) | 30.64% (24.25–37.86%) | USD -85.40 | USD -14,774.00 | USD -2,408.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -38.62 | USD -7,491.40 | USD -626.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/196 (2) | 53.61% (46.59–60.49%) | USD -259.88 | USD -50,417.40 | USD -7,102.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/196 (2) | 32.47% (26.28–39.35%) | USD -10.42 | USD -2,022.40 | USD -9,295.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -193.08 | USD -37,457.00 | USD -3,133.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/196 (196) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 173/196 (23) | 30.64% (24.25–37.86%) | USD -17.08 | USD -2,954.80 | USD -481.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 173/196 (23) | 60.12% (52.68–67.12%) | USD -233.81 | USD -40,449.30 | USD -9,131.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 173/196 (23) | 30.06% (23.72–37.26%) | USD 114.25 | USD 19,765.70 | USD -4,176.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 173/196 (23) | 30.64% (24.25–37.86%) | USD -85.40 | USD -14,774.00 | USD -2,408.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -38.62 | USD -7,491.40 | USD -626.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/196 (2) | 53.61% (46.59–60.49%) | USD -259.88 | USD -50,417.40 | USD -7,102.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/196 (2) | 32.47% (26.28–39.35%) | USD -10.42 | USD -2,022.40 | USD -9,295.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/196 (2) | 22.68% (17.35–29.07%) | USD -193.08 | USD -37,457.00 | USD -3,133.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -75% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -50% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -40% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -30% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -25% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -20% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -15% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -10% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| -5% | 196/196 | 100.00% | USD 763.46 | USD 86.45 |
| 0% | 196/196 | 100.00% | USD 736.56 | USD 86.45 |
| 5% | 18/196 | 9.18% | USD -4,752.51 | USD -11,328.75 |
| 10% | 2/196 | 1.02% | USD -15,434.34 | USD -28,875.95 |
| 20% | 0/196 | 0.00% | USD -37,020.44 | USD -63,970.35 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short call can dominate downside even when QQQ long call appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.