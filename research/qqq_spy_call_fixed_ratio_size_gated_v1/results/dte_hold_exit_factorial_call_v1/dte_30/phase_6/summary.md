# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 213.55 / USD 1,154.30; mean absolute mismatch USD 940.74; mean match score 18.75%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 195/196 | 106/89/0 | 54.36% (47.35–61.20%) | USD -225.68 | USD 51.90 | USD -44,008.50 | USD -6,973.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 195/196 | 106/89/0 | 54.36% (47.35–61.20%) | USD -225.68 | USD 51.90 | USD -44,008.50 | USD -6,973.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 195/196 | 106/89/0 | 54.36% (47.35–61.20%) | USD -225.68 | USD 51.90 | USD -44,008.50 | USD -6,973.10 | 1 |
| HOLD_10_SESSIONS | 191/196 | 113/78/0 | 59.16% (52.08–65.89%) | USD -160.07 | USD 191.90 | USD -30,574.10 | USD -7,641.10 | 5 |
| HOLD_10_OR_DTE_LE_7 | 191/196 | 113/78/0 | 59.16% (52.08–65.89%) | USD -160.07 | USD 191.90 | USD -30,574.10 | USD -7,641.10 | 5 |
| HOLD_10_OR_DTE_LE_14 | 191/196 | 109/82/0 | 57.07% (49.98–63.88%) | USD -166.32 | USD 188.90 | USD -31,767.10 | USD -7,641.10 | 5 |
| HOLD_15_SESSIONS | 166/196 | 98/68/0 | 59.04% (51.43–66.23%) | USD -501.46 | USD 285.40 | USD -83,242.60 | USD -10,982.10 | 30 |
| HOLD_15_OR_DTE_LE_7 | 170/196 | 100/70/0 | 58.82% (51.31–65.95%) | USD -456.11 | USD 278.40 | USD -77,539.00 | USD -10,982.10 | 26 |
| HOLD_15_OR_DTE_LE_14 | 190/196 | 118/72/0 | 62.11% (55.03–68.70%) | USD -180.47 | USD 236.40 | USD -34,290.00 | USD -9,431.10 | 6 |
| HOLD_20_SESSIONS | 48/196 | 26/22/0 | 54.17% (40.29–67.42%) | USD -902.73 | USD 184.40 | USD -43,330.80 | USD -10,707.10 | 148 |
| HOLD_20_OR_DTE_LE_7 | 160/196 | 91/69/0 | 56.88% (49.13–64.30%) | USD -523.56 | USD 304.90 | USD -83,769.00 | USD -10,973.10 | 36 |
| HOLD_20_OR_DTE_LE_14 | 190/196 | 118/72/0 | 62.11% (55.03–68.70%) | USD -180.47 | USD 236.40 | USD -34,290.00 | USD -9,431.10 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 20.43 | USD -167.02 |
| HOLD_5_OR_DTE_LE_7 | USD 20.43 | USD -167.02 |
| HOLD_5_OR_DTE_LE_14 | USD 20.43 | USD -167.02 |
| HOLD_10_SESSIONS | USD 17.04 | USD -98.01 |
| HOLD_10_OR_DTE_LE_7 | USD 17.04 | USD -98.01 |
| HOLD_10_OR_DTE_LE_14 | USD 20.69 | USD -107.91 |
| HOLD_15_SESSIONS | USD 82.51 | USD -504.87 |
| HOLD_15_OR_DTE_LE_7 | USD 70.87 | USD -447.88 |
| HOLD_15_OR_DTE_LE_14 | USD 48.75 | USD -150.13 |
| HOLD_20_SESSIONS | USD 234.50 | USD -1,058.12 |
| HOLD_20_OR_DTE_LE_7 | USD 83.28 | USD -527.74 |
| HOLD_20_OR_DTE_LE_14 | USD 48.75 | USD -150.13 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 195 | 58.46% | USD -146.58 | USD -28,584.00 | USD -6,894.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 195 | 56.92% | USD -155.68 | USD -30,358.50 | USD -6,903.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 195 | 55.90% | USD -181.58 | USD -35,409.00 | USD -6,929.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 195 | 55.90% | USD -190.68 | USD -37,183.50 | USD -6,938.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 195 | 54.87% | USD -216.58 | USD -42,234.00 | USD -6,964.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 195 | 54.36% | USD -225.68 | USD -44,008.50 | USD -6,973.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 195 | 49.74% | USD -286.58 | USD -55,884.00 | USD -7,034.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 195 | 49.74% | USD -295.68 | USD -57,658.50 | USD -7,043.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 195 | 58.46% | USD -146.58 | USD -28,584.00 | USD -6,894.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 195 | 56.92% | USD -155.68 | USD -30,358.50 | USD -6,903.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 195 | 55.90% | USD -181.58 | USD -35,409.00 | USD -6,929.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 195 | 55.90% | USD -190.68 | USD -37,183.50 | USD -6,938.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 195 | 54.87% | USD -216.58 | USD -42,234.00 | USD -6,964.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 195 | 54.36% | USD -225.68 | USD -44,008.50 | USD -6,973.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 195 | 49.74% | USD -286.58 | USD -55,884.00 | USD -7,034.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 195 | 49.74% | USD -295.68 | USD -57,658.50 | USD -7,043.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 58.46% | USD -146.58 | USD -28,584.00 | USD -6,894.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 56.92% | USD -155.68 | USD -30,358.50 | USD -6,903.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 55.90% | USD -181.58 | USD -35,409.00 | USD -6,929.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 55.90% | USD -190.68 | USD -37,183.50 | USD -6,938.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 54.87% | USD -216.58 | USD -42,234.00 | USD -6,964.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 54.36% | USD -225.68 | USD -44,008.50 | USD -6,973.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 49.74% | USD -286.58 | USD -55,884.00 | USD -7,034.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 49.74% | USD -295.68 | USD -57,658.50 | USD -7,043.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 191 | 62.30% | USD -80.97 | USD -15,466.00 | USD -7,562.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 191 | 61.78% | USD -90.07 | USD -17,204.10 | USD -7,571.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 191 | 60.73% | USD -115.97 | USD -22,151.00 | USD -7,597.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 191 | 60.21% | USD -125.07 | USD -23,889.10 | USD -7,606.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 191 | 59.69% | USD -150.97 | USD -28,836.00 | USD -7,632.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 191 | 59.16% | USD -160.07 | USD -30,574.10 | USD -7,641.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 191 | 56.54% | USD -220.97 | USD -42,206.00 | USD -7,702.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 191 | 56.02% | USD -230.07 | USD -43,944.10 | USD -7,711.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 62.30% | USD -80.97 | USD -15,466.00 | USD -7,562.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 61.78% | USD -90.07 | USD -17,204.10 | USD -7,571.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 60.73% | USD -115.97 | USD -22,151.00 | USD -7,597.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 60.21% | USD -125.07 | USD -23,889.10 | USD -7,606.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 59.69% | USD -150.97 | USD -28,836.00 | USD -7,632.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 59.16% | USD -160.07 | USD -30,574.10 | USD -7,641.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 56.54% | USD -220.97 | USD -42,206.00 | USD -7,702.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 56.02% | USD -230.07 | USD -43,944.10 | USD -7,711.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 191 | 60.21% | USD -87.22 | USD -16,659.00 | USD -7,562.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 191 | 59.69% | USD -96.32 | USD -18,397.10 | USD -7,571.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 191 | 58.64% | USD -122.22 | USD -23,344.00 | USD -7,597.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 191 | 58.12% | USD -131.32 | USD -25,082.10 | USD -7,606.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 191 | 57.59% | USD -157.22 | USD -30,029.00 | USD -7,632.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 191 | 57.07% | USD -166.32 | USD -31,767.10 | USD -7,641.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 191 | 54.97% | USD -227.22 | USD -43,399.00 | USD -7,702.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 191 | 54.45% | USD -236.32 | USD -45,137.10 | USD -7,711.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 166 | 60.84% | USD -422.36 | USD -70,112.00 | USD -10,903.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 166 | 60.84% | USD -431.46 | USD -71,622.60 | USD -10,912.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 166 | 60.24% | USD -457.36 | USD -75,922.00 | USD -10,938.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 166 | 59.64% | USD -466.46 | USD -77,432.60 | USD -10,947.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 166 | 59.04% | USD -492.36 | USD -81,732.00 | USD -10,973.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 166 | 59.04% | USD -501.46 | USD -83,242.60 | USD -10,982.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 166 | 57.83% | USD -562.36 | USD -93,352.00 | USD -11,043.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 166 | 57.83% | USD -571.46 | USD -94,862.60 | USD -11,052.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 61.76% | USD -377.01 | USD -64,092.00 | USD -10,903.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 61.76% | USD -386.11 | USD -65,639.00 | USD -10,912.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 61.18% | USD -412.01 | USD -70,042.00 | USD -10,938.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 60.00% | USD -421.11 | USD -71,589.00 | USD -10,947.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 58.82% | USD -447.01 | USD -75,992.00 | USD -10,973.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 58.82% | USD -456.11 | USD -77,539.00 | USD -10,982.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 57.06% | USD -517.01 | USD -87,892.00 | USD -11,043.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 57.06% | USD -526.11 | USD -89,439.00 | USD -11,052.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 190 | 64.74% | USD -101.37 | USD -19,261.00 | USD -9,352.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 190 | 64.21% | USD -110.47 | USD -20,990.00 | USD -9,361.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 190 | 63.16% | USD -136.37 | USD -25,911.00 | USD -9,387.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 190 | 63.16% | USD -145.47 | USD -27,640.00 | USD -9,396.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 190 | 62.63% | USD -171.37 | USD -32,561.00 | USD -9,422.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 190 | 62.11% | USD -180.47 | USD -34,290.00 | USD -9,431.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 190 | 59.47% | USD -241.37 | USD -45,861.00 | USD -9,492.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 190 | 58.42% | USD -250.47 | USD -47,590.00 | USD -9,501.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 48 | 54.17% | USD -823.62 | USD -39,534.00 | USD -10,628.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 48 | 54.17% | USD -832.73 | USD -39,970.80 | USD -10,637.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 48 | 54.17% | USD -858.62 | USD -41,214.00 | USD -10,663.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 48 | 54.17% | USD -867.73 | USD -41,650.80 | USD -10,672.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 48 | 54.17% | USD -893.62 | USD -42,894.00 | USD -10,698.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 48 | 54.17% | USD -902.73 | USD -43,330.80 | USD -10,707.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 48 | 54.17% | USD -963.62 | USD -46,254.00 | USD -10,768.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 48 | 54.17% | USD -972.73 | USD -46,690.80 | USD -10,777.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 160 | 59.38% | USD -444.46 | USD -71,113.00 | USD -10,894.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 160 | 59.38% | USD -453.56 | USD -72,569.00 | USD -10,903.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 160 | 59.38% | USD -479.46 | USD -76,713.00 | USD -10,929.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 160 | 58.12% | USD -488.56 | USD -78,169.00 | USD -10,938.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 160 | 56.88% | USD -514.46 | USD -82,313.00 | USD -10,964.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 160 | 56.88% | USD -523.56 | USD -83,769.00 | USD -10,973.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 160 | 55.62% | USD -584.46 | USD -93,513.00 | USD -11,034.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 160 | 55.62% | USD -593.56 | USD -94,969.00 | USD -11,043.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 190 | 64.74% | USD -101.37 | USD -19,261.00 | USD -9,352.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 190 | 64.21% | USD -110.47 | USD -20,990.00 | USD -9,361.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 190 | 63.16% | USD -136.37 | USD -25,911.00 | USD -9,387.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 190 | 63.16% | USD -145.47 | USD -27,640.00 | USD -9,396.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 190 | 62.63% | USD -171.37 | USD -32,561.00 | USD -9,422.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 190 | 62.11% | USD -180.47 | USD -34,290.00 | USD -9,431.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 190 | 59.47% | USD -241.37 | USD -45,861.00 | USD -9,492.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 190 | 58.42% | USD -250.47 | USD -47,590.00 | USD -9,501.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 195/196 (1) | 27.18% (21.42–33.82%) | USD -30.01 | USD -5,851.00 | USD -404.60 |
| HOLD_5_SESSIONS | 1 : 6 | 195/196 (1) | 54.36% (47.35–61.20%) | USD -225.68 | USD -44,008.50 | USD -6,973.10 |
| HOLD_5_SESSIONS | 6 : 1 | 195/196 (1) | 36.41% (29.98–43.37%) | USD 15.65 | USD 3,051.50 | USD -7,261.10 |
| HOLD_5_SESSIONS | 5 : 5 | 195/196 (1) | 27.18% (21.42–33.82%) | USD -150.03 | USD -29,255.00 | USD -2,023.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 195/196 (1) | 27.18% (21.42–33.82%) | USD -30.01 | USD -5,851.00 | USD -404.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 195/196 (1) | 54.36% (47.35–61.20%) | USD -225.68 | USD -44,008.50 | USD -6,973.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 195/196 (1) | 36.41% (29.98–43.37%) | USD 15.65 | USD 3,051.50 | USD -7,261.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 195/196 (1) | 27.18% (21.42–33.82%) | USD -150.03 | USD -29,255.00 | USD -2,023.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 27.18% (21.42–33.82%) | USD -30.01 | USD -5,851.00 | USD -404.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 54.36% (47.35–61.20%) | USD -225.68 | USD -44,008.50 | USD -6,973.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 36.41% (29.98–43.37%) | USD 15.65 | USD 3,051.50 | USD -7,261.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 27.18% (21.42–33.82%) | USD -150.03 | USD -29,255.00 | USD -2,023.00 |
| HOLD_10_SESSIONS | 1 : 1 | 191/196 (5) | 32.46% (26.22–39.39%) | USD -21.90 | USD -4,182.60 | USD -715.60 |
| HOLD_10_SESSIONS | 1 : 6 | 191/196 (5) | 59.16% (52.08–65.89%) | USD -160.07 | USD -30,574.10 | USD -7,641.10 |
| HOLD_10_SESSIONS | 6 : 1 | 191/196 (5) | 32.46% (26.22–39.39%) | USD 6.78 | USD 1,295.90 | USD -3,028.10 |
| HOLD_10_SESSIONS | 5 : 5 | 191/196 (5) | 32.46% (26.22–39.39%) | USD -109.49 | USD -20,913.00 | USD -3,578.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 191/196 (5) | 32.46% (26.22–39.39%) | USD -21.90 | USD -4,182.60 | USD -715.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 191/196 (5) | 59.16% (52.08–65.89%) | USD -160.07 | USD -30,574.10 | USD -7,641.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 191/196 (5) | 32.46% (26.22–39.39%) | USD 6.78 | USD 1,295.90 | USD -3,028.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 191/196 (5) | 32.46% (26.22–39.39%) | USD -109.49 | USD -20,913.00 | USD -3,578.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 191/196 (5) | 33.51% (27.20–40.47%) | USD -19.90 | USD -3,800.60 | USD -446.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 191/196 (5) | 57.07% (49.98–63.88%) | USD -166.32 | USD -31,767.10 | USD -7,641.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 191/196 (5) | 31.94% (25.74–38.85%) | USD 27.03 | USD 5,162.90 | USD -3,028.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 191/196 (5) | 33.51% (27.20–40.47%) | USD -99.49 | USD -19,003.00 | USD -2,233.00 |
| HOLD_15_SESSIONS | 1 : 1 | 166/196 (30) | 27.71% (21.46–34.97%) | USD -24.24 | USD -4,023.60 | USD -659.60 |
| HOLD_15_SESSIONS | 1 : 6 | 166/196 (30) | 59.04% (51.43–66.23%) | USD -501.46 | USD -83,242.60 | USD -10,982.10 |
| HOLD_15_SESSIONS | 6 : 1 | 166/196 (30) | 36.14% (29.23–43.69%) | USD 331.79 | USD 55,077.40 | USD -3,175.10 |
| HOLD_15_SESSIONS | 5 : 5 | 166/196 (30) | 27.71% (21.46–34.97%) | USD -121.19 | USD -20,118.00 | USD -3,298.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 170/196 (26) | 28.24% (22.01–35.42%) | USD -26.38 | USD -4,484.00 | USD -1,406.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 170/196 (26) | 58.82% (51.31–65.95%) | USD -456.11 | USD -77,539.00 | USD -10,982.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 170/196 (26) | 35.88% (29.06–43.33%) | USD 271.48 | USD 46,151.00 | USD -3,175.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 170/196 (26) | 28.24% (22.01–35.42%) | USD -131.88 | USD -22,420.00 | USD -7,033.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 190/196 (6) | 33.16% (26.86–40.13%) | USD 1.13 | USD 215.00 | USD -446.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 190/196 (6) | 62.11% (55.03–68.70%) | USD -180.47 | USD -34,290.00 | USD -9,431.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 190/196 (6) | 30.53% (24.42–37.41%) | USD 188.39 | USD 35,795.00 | USD -3,153.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 190/196 (6) | 33.16% (26.86–40.13%) | USD 5.66 | USD 1,075.00 | USD -2,233.00 |
| HOLD_20_SESSIONS | 1 : 1 | 48/196 (148) | 43.75% (30.70–57.73%) | USD 35.55 | USD 1,706.20 | USD -601.60 |
| HOLD_20_SESSIONS | 1 : 6 | 48/196 (148) | 54.17% (40.29–67.42%) | USD -902.73 | USD -43,330.80 | USD -10,707.10 |
| HOLD_20_SESSIONS | 6 : 1 | 48/196 (148) | 50.00% (36.39–63.61%) | USD 1,151.55 | USD 55,274.20 | USD -2,945.10 |
| HOLD_20_SESSIONS | 5 : 5 | 48/196 (148) | 43.75% (30.70–57.73%) | USD 177.73 | USD 8,531.00 | USD -3,008.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 160/196 (36) | 31.25% (24.58–38.80%) | USD -27.27 | USD -4,364.00 | USD -1,406.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 160/196 (36) | 56.88% (49.13–64.30%) | USD -523.56 | USD -83,769.00 | USD -10,973.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 160/196 (36) | 36.25% (29.20–43.94%) | USD 332.63 | USD 53,221.00 | USD -2,596.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 160/196 (36) | 31.25% (24.58–38.80%) | USD -136.38 | USD -21,820.00 | USD -7,033.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 190/196 (6) | 33.16% (26.86–40.13%) | USD 1.13 | USD 215.00 | USD -446.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 190/196 (6) | 62.11% (55.03–68.70%) | USD -180.47 | USD -34,290.00 | USD -9,431.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 190/196 (6) | 30.53% (24.42–37.41%) | USD 188.39 | USD 35,795.00 | USD -3,153.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 190/196 (6) | 33.16% (26.86–40.13%) | USD 5.66 | USD 1,075.00 | USD -2,233.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -75% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -50% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -40% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -30% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -25% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -20% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -15% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -10% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| -5% | 196/196 | 100.00% | USD 901.19 | USD 18.45 |
| 0% | 196/196 | 100.00% | USD 883.99 | USD 18.45 |
| 5% | 33/196 | 16.84% | USD -3,248.67 | USD -9,417.15 |
| 10% | 2/196 | 1.02% | USD -13,824.67 | USD -26,440.95 |
| 20% | 0/196 | 0.00% | USD -35,396.93 | USD -61,535.35 |

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