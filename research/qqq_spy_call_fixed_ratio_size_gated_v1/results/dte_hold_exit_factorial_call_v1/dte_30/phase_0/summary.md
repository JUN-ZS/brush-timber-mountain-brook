# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 190.08 / USD 1,009.71; mean absolute mismatch USD 819.63; mean match score 19.35%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 196/196 | 105/91/0 | 53.57% (46.59–60.42%) | USD -131.03 | USD 50.90 | USD -25,681.60 | USD -4,164.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 196/196 | 105/91/0 | 53.57% (46.59–60.42%) | USD -131.03 | USD 50.90 | USD -25,681.60 | USD -4,164.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 196/196 | 105/91/0 | 53.57% (46.59–60.42%) | USD -131.03 | USD 50.90 | USD -25,681.60 | USD -4,164.10 | 0 |
| HOLD_10_SESSIONS | 189/196 | 113/76/0 | 59.79% (52.67–66.52%) | USD -230.29 | USD 143.90 | USD -43,523.90 | USD -6,660.10 | 7 |
| HOLD_10_OR_DTE_LE_7 | 189/196 | 113/76/0 | 59.79% (52.67–66.52%) | USD -230.29 | USD 143.90 | USD -43,523.90 | USD -6,660.10 | 7 |
| HOLD_10_OR_DTE_LE_14 | 190/196 | 111/79/0 | 58.42% (51.31–65.19%) | USD -248.63 | USD 132.90 | USD -47,240.00 | USD -7,379.10 | 6 |
| HOLD_15_SESSIONS | 166/196 | 96/70/0 | 57.83% (50.23–65.08%) | USD -327.28 | USD 188.40 | USD -54,328.60 | USD -7,599.10 | 30 |
| HOLD_15_OR_DTE_LE_7 | 170/196 | 97/73/0 | 57.06% (49.54–64.26%) | USD -225.68 | USD 138.40 | USD -38,365.00 | USD -7,599.10 | 26 |
| HOLD_15_OR_DTE_LE_14 | 189/196 | 108/81/0 | 57.14% (50.01–63.99%) | USD -259.70 | USD 127.90 | USD -49,083.90 | USD -7,379.10 | 7 |
| HOLD_20_SESSIONS | 32/196 | 13/19/0 | 40.62% (25.52–57.74%) | USD -1,850.19 | USD -562.60 | USD -59,206.20 | USD -8,412.10 | 164 |
| HOLD_20_OR_DTE_LE_7 | 161/196 | 90/71/0 | 55.90% (48.18–63.34%) | USD -302.37 | USD 142.90 | USD -48,682.10 | USD -9,258.10 | 35 |
| HOLD_20_OR_DTE_LE_14 | 189/196 | 108/81/0 | 57.14% (50.01–63.99%) | USD -259.70 | USD 127.90 | USD -49,083.90 | USD -7,379.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 4.15 | USD -56.08 |
| HOLD_5_OR_DTE_LE_7 | USD 4.15 | USD -56.08 |
| HOLD_5_OR_DTE_LE_14 | USD 4.15 | USD -56.08 |
| HOLD_10_SESSIONS | USD 25.86 | USD -177.05 |
| HOLD_10_OR_DTE_LE_7 | USD 25.86 | USD -177.05 |
| HOLD_10_OR_DTE_LE_14 | USD 22.72 | USD -192.25 |
| HOLD_15_SESSIONS | USD 50.59 | USD -298.77 |
| HOLD_15_OR_DTE_LE_7 | USD 31.69 | USD -178.27 |
| HOLD_15_OR_DTE_LE_14 | USD 23.68 | USD -204.29 |
| HOLD_20_SESSIONS | USD 397.91 | USD -2,169.00 |
| HOLD_20_OR_DTE_LE_7 | USD 70.99 | USD -294.26 |
| HOLD_20_OR_DTE_LE_14 | USD 23.68 | USD -204.29 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 196 | 59.69% | USD -51.93 | USD -10,178.00 | USD -4,085.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 196 | 58.67% | USD -61.03 | USD -11,961.60 | USD -4,094.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 196 | 57.65% | USD -86.93 | USD -17,038.00 | USD -4,120.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 196 | 57.14% | USD -96.03 | USD -18,821.60 | USD -4,129.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 196 | 54.59% | USD -121.93 | USD -23,898.00 | USD -4,155.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 196 | 53.57% | USD -131.03 | USD -25,681.60 | USD -4,164.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 196 | 48.98% | USD -191.93 | USD -37,618.00 | USD -4,225.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 196 | 47.45% | USD -201.03 | USD -39,401.60 | USD -4,234.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 196 | 59.69% | USD -51.93 | USD -10,178.00 | USD -4,085.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 196 | 58.67% | USD -61.03 | USD -11,961.60 | USD -4,094.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 196 | 57.65% | USD -86.93 | USD -17,038.00 | USD -4,120.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 196 | 57.14% | USD -96.03 | USD -18,821.60 | USD -4,129.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 196 | 54.59% | USD -121.93 | USD -23,898.00 | USD -4,155.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 196 | 53.57% | USD -131.03 | USD -25,681.60 | USD -4,164.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 196 | 48.98% | USD -191.93 | USD -37,618.00 | USD -4,225.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 196 | 47.45% | USD -201.03 | USD -39,401.60 | USD -4,234.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 196 | 59.69% | USD -51.93 | USD -10,178.00 | USD -4,085.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 196 | 58.67% | USD -61.03 | USD -11,961.60 | USD -4,094.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 196 | 57.65% | USD -86.93 | USD -17,038.00 | USD -4,120.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 196 | 57.14% | USD -96.03 | USD -18,821.60 | USD -4,129.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 196 | 54.59% | USD -121.93 | USD -23,898.00 | USD -4,155.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 196 | 53.57% | USD -131.03 | USD -25,681.60 | USD -4,164.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 196 | 48.98% | USD -191.93 | USD -37,618.00 | USD -4,225.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 196 | 47.45% | USD -201.03 | USD -39,401.60 | USD -4,234.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 189 | 62.43% | USD -151.19 | USD -28,574.00 | USD -6,581.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 189 | 61.90% | USD -160.29 | USD -30,293.90 | USD -6,590.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 189 | 61.38% | USD -186.19 | USD -35,189.00 | USD -6,616.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 189 | 61.38% | USD -195.29 | USD -36,908.90 | USD -6,625.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 189 | 60.85% | USD -221.19 | USD -41,804.00 | USD -6,651.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 189 | 59.79% | USD -230.29 | USD -43,523.90 | USD -6,660.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 189 | 55.56% | USD -291.19 | USD -55,034.00 | USD -6,721.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 189 | 55.56% | USD -300.29 | USD -56,753.90 | USD -6,730.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 189 | 62.43% | USD -151.19 | USD -28,574.00 | USD -6,581.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 189 | 61.90% | USD -160.29 | USD -30,293.90 | USD -6,590.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 189 | 61.38% | USD -186.19 | USD -35,189.00 | USD -6,616.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 189 | 61.38% | USD -195.29 | USD -36,908.90 | USD -6,625.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 189 | 60.85% | USD -221.19 | USD -41,804.00 | USD -6,651.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 189 | 59.79% | USD -230.29 | USD -43,523.90 | USD -6,660.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 189 | 55.56% | USD -291.19 | USD -55,034.00 | USD -6,721.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 189 | 55.56% | USD -300.29 | USD -56,753.90 | USD -6,730.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 190 | 61.05% | USD -169.53 | USD -32,211.00 | USD -7,300.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 190 | 60.53% | USD -178.63 | USD -33,940.00 | USD -7,309.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 190 | 60.00% | USD -204.53 | USD -38,861.00 | USD -7,335.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 190 | 59.47% | USD -213.63 | USD -40,590.00 | USD -7,344.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 190 | 59.47% | USD -239.53 | USD -45,511.00 | USD -7,370.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 190 | 58.42% | USD -248.63 | USD -47,240.00 | USD -7,379.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 190 | 54.21% | USD -309.53 | USD -58,811.00 | USD -7,440.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 190 | 53.68% | USD -318.63 | USD -60,540.00 | USD -7,449.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 166 | 60.24% | USD -248.18 | USD -41,198.00 | USD -7,520.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 166 | 60.24% | USD -257.28 | USD -42,708.60 | USD -7,529.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 166 | 59.64% | USD -283.18 | USD -47,008.00 | USD -7,555.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 166 | 59.04% | USD -292.28 | USD -48,518.60 | USD -7,564.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 166 | 57.83% | USD -318.18 | USD -52,818.00 | USD -7,590.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 166 | 57.83% | USD -327.28 | USD -54,328.60 | USD -7,599.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 166 | 57.23% | USD -388.18 | USD -64,438.00 | USD -7,660.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 166 | 57.23% | USD -397.28 | USD -65,948.60 | USD -7,669.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 58.82% | USD -146.58 | USD -24,918.00 | USD -7,520.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 58.82% | USD -155.68 | USD -26,465.00 | USD -7,529.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 58.24% | USD -181.58 | USD -30,868.00 | USD -7,555.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 58.24% | USD -190.68 | USD -32,415.00 | USD -7,564.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 57.06% | USD -216.58 | USD -36,818.00 | USD -7,590.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 57.06% | USD -225.68 | USD -38,365.00 | USD -7,599.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 56.47% | USD -286.58 | USD -48,718.00 | USD -7,660.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 56.47% | USD -295.68 | USD -50,265.00 | USD -7,669.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 189 | 60.85% | USD -180.60 | USD -34,134.00 | USD -7,300.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 189 | 59.79% | USD -189.70 | USD -35,853.90 | USD -7,309.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 189 | 58.20% | USD -215.60 | USD -40,749.00 | USD -7,335.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 189 | 57.67% | USD -224.70 | USD -42,468.90 | USD -7,344.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 189 | 57.67% | USD -250.60 | USD -47,364.00 | USD -7,370.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 189 | 57.14% | USD -259.70 | USD -49,083.90 | USD -7,379.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 189 | 54.50% | USD -320.60 | USD -60,594.00 | USD -7,440.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 189 | 53.97% | USD -329.70 | USD -62,313.90 | USD -7,449.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 32 | 43.75% | USD -1,771.09 | USD -56,675.00 | USD -8,333.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 32 | 43.75% | USD -1,780.19 | USD -56,966.20 | USD -8,342.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 32 | 43.75% | USD -1,806.09 | USD -57,795.00 | USD -8,368.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 32 | 40.62% | USD -1,815.19 | USD -58,086.20 | USD -8,377.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 32 | 40.62% | USD -1,841.09 | USD -58,915.00 | USD -8,403.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 32 | 40.62% | USD -1,850.19 | USD -59,206.20 | USD -8,412.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 32 | 40.62% | USD -1,911.09 | USD -61,155.00 | USD -8,473.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 32 | 40.62% | USD -1,920.19 | USD -61,446.20 | USD -8,482.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 161 | 59.01% | USD -223.27 | USD -35,947.00 | USD -9,179.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 161 | 59.01% | USD -232.37 | USD -37,412.10 | USD -9,188.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 161 | 58.39% | USD -258.27 | USD -41,582.00 | USD -9,214.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 161 | 58.39% | USD -267.37 | USD -43,047.10 | USD -9,223.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 161 | 55.90% | USD -293.27 | USD -47,217.00 | USD -9,249.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 161 | 55.90% | USD -302.37 | USD -48,682.10 | USD -9,258.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 161 | 55.28% | USD -363.27 | USD -58,487.00 | USD -9,319.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 161 | 55.28% | USD -372.37 | USD -59,952.10 | USD -9,328.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 189 | 60.85% | USD -180.60 | USD -34,134.00 | USD -7,300.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 189 | 59.79% | USD -189.70 | USD -35,853.90 | USD -7,309.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 189 | 58.20% | USD -215.60 | USD -40,749.00 | USD -7,335.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 189 | 57.67% | USD -224.70 | USD -42,468.90 | USD -7,344.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 189 | 57.67% | USD -250.60 | USD -47,364.00 | USD -7,370.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 189 | 57.14% | USD -259.70 | USD -49,083.90 | USD -7,379.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 189 | 54.50% | USD -320.60 | USD -60,594.00 | USD -7,440.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 189 | 53.97% | USD -329.70 | USD -62,313.90 | USD -7,449.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -27.79 | USD -5,447.60 | USD -350.60 |
| HOLD_5_SESSIONS | 1 : 6 | 196/196 (0) | 53.57% (46.59–60.42%) | USD -131.03 | USD -25,681.60 | USD -4,164.10 |
| HOLD_5_SESSIONS | 6 : 1 | 196/196 (0) | 33.16% (26.95–40.02%) | USD -63.53 | USD -12,451.60 | USD -2,077.10 |
| HOLD_5_SESSIONS | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -138.97 | USD -27,238.00 | USD -1,753.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -27.79 | USD -5,447.60 | USD -350.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 196/196 (0) | 53.57% (46.59–60.42%) | USD -131.03 | USD -25,681.60 | USD -4,164.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 196/196 (0) | 33.16% (26.95–40.02%) | USD -63.53 | USD -12,451.60 | USD -2,077.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -138.97 | USD -27,238.00 | USD -1,753.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -27.79 | USD -5,447.60 | USD -350.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 196/196 (0) | 53.57% (46.59–60.42%) | USD -131.03 | USD -25,681.60 | USD -4,164.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 196/196 (0) | 33.16% (26.95–40.02%) | USD -63.53 | USD -12,451.60 | USD -2,077.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 196/196 (0) | 28.57% (22.71–35.26%) | USD -138.97 | USD -27,238.00 | USD -1,753.00 |
| HOLD_10_SESSIONS | 1 : 1 | 189/196 (7) | 26.98% (21.16–33.72%) | USD -26.25 | USD -4,960.40 | USD -838.60 |
| HOLD_10_SESSIONS | 1 : 6 | 189/196 (7) | 59.79% (52.67–66.52%) | USD -230.29 | USD -43,523.90 | USD -6,660.10 |
| HOLD_10_SESSIONS | 6 : 1 | 189/196 (7) | 33.86% (27.50–40.87%) | USD 46.57 | USD 8,801.10 | USD -2,338.10 |
| HOLD_10_SESSIONS | 5 : 5 | 189/196 (7) | 26.98% (21.16–33.72%) | USD -131.23 | USD -24,802.00 | USD -4,193.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 189/196 (7) | 26.98% (21.16–33.72%) | USD -26.25 | USD -4,960.40 | USD -838.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 189/196 (7) | 59.79% (52.67–66.52%) | USD -230.29 | USD -43,523.90 | USD -6,660.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 189/196 (7) | 33.86% (27.50–40.87%) | USD 46.57 | USD 8,801.10 | USD -2,338.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 189/196 (7) | 26.98% (21.16–33.72%) | USD -131.23 | USD -24,802.00 | USD -4,193.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 190/196 (6) | 25.79% (20.09–32.45%) | USD -31.92 | USD -6,065.00 | USD -1,072.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 190/196 (6) | 58.42% (51.31–65.19%) | USD -248.63 | USD -47,240.00 | USD -7,379.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 190/196 (6) | 33.68% (27.35–40.67%) | USD 25.18 | USD 4,785.00 | USD -2,338.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 190/196 (6) | 25.79% (20.09–32.45%) | USD -159.61 | USD -30,325.00 | USD -5,363.00 |
| HOLD_15_SESSIONS | 1 : 1 | 166/196 (30) | 30.72% (24.21–38.11%) | USD -21.80 | USD -3,619.60 | USD -733.60 |
| HOLD_15_SESSIONS | 1 : 6 | 166/196 (30) | 57.83% (50.23–65.08%) | USD -327.28 | USD -54,328.60 | USD -7,599.10 |
| HOLD_15_SESSIONS | 6 : 1 | 166/196 (30) | 33.73% (26.98–41.22%) | USD 174.65 | USD 28,991.40 | USD -2,374.10 |
| HOLD_15_SESSIONS | 5 : 5 | 166/196 (30) | 30.72% (24.21–38.11%) | USD -109.02 | USD -18,098.00 | USD -3,668.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 170/196 (26) | 31.18% (24.69–38.49%) | USD -20.62 | USD -3,505.00 | USD -733.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 170/196 (26) | 57.06% (49.54–64.26%) | USD -225.68 | USD -38,365.00 | USD -7,599.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 170/196 (26) | 32.94% (26.32–40.31%) | USD 81.35 | USD 13,830.00 | USD -2,374.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 170/196 (26) | 31.18% (24.69–38.49%) | USD -103.09 | USD -17,525.00 | USD -3,668.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 189/196 (7) | 25.93% (20.20–32.61%) | USD -32.97 | USD -6,230.40 | USD -1,072.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 189/196 (7) | 57.14% (50.01–63.99%) | USD -259.70 | USD -49,083.90 | USD -7,379.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 189/196 (7) | 33.33% (27.00–40.33%) | USD 28.95 | USD 5,471.10 | USD -2,378.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 189/196 (7) | 25.93% (20.20–32.61%) | USD -164.83 | USD -31,152.00 | USD -5,363.00 |
| HOLD_20_SESSIONS | 1 : 1 | 32/196 (164) | 28.12% (15.56–45.37%) | USD 13.81 | USD 441.80 | USD -1,019.60 |
| HOLD_20_SESSIONS | 1 : 6 | 32/196 (164) | 40.62% (25.52–57.74%) | USD -1,850.19 | USD -59,206.20 | USD -8,412.10 |
| HOLD_20_SESSIONS | 6 : 1 | 32/196 (164) | 43.75% (28.17–60.67%) | USD 1,946.84 | USD 62,298.80 | USD -1,896.10 |
| HOLD_20_SESSIONS | 5 : 5 | 32/196 (164) | 28.12% (15.56–45.37%) | USD 69.03 | USD 2,209.00 | USD -5,098.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 161/196 (35) | 32.92% (26.13–40.50%) | USD -0.66 | USD -105.60 | USD -813.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 161/196 (35) | 55.90% (48.18–63.34%) | USD -302.37 | USD -48,682.10 | USD -9,258.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 161/196 (35) | 33.54% (26.71–41.14%) | USD 297.78 | USD 47,942.90 | USD -2,130.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 161/196 (35) | 32.92% (26.13–40.50%) | USD -3.28 | USD -528.00 | USD -4,068.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 189/196 (7) | 25.93% (20.20–32.61%) | USD -32.97 | USD -6,230.40 | USD -1,072.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 189/196 (7) | 57.14% (50.01–63.99%) | USD -259.70 | USD -49,083.90 | USD -7,379.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 189/196 (7) | 33.33% (27.00–40.33%) | USD 28.95 | USD 5,471.10 | USD -2,378.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 189/196 (7) | 25.93% (20.20–32.61%) | USD -164.83 | USD -31,152.00 | USD -5,363.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -75% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -50% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -40% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -30% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -25% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -20% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -15% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -10% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| -5% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| 0% | 196/196 | 100.00% | USD 780.08 | USD 70.45 |
| 5% | 39/196 | 19.90% | USD -3,041.14 | USD -8,636.40 |
| 10% | 2/196 | 1.02% | USD -13,564.64 | USD -25,253.55 |
| 20% | 1/196 | 0.51% | USD -35,066.87 | USD -60,087.55 |

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