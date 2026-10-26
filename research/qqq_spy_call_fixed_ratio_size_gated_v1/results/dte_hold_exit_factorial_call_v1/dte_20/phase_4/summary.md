# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 160.66 / USD 871.69; mean absolute mismatch USD 711.04; mean match score 19.28%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 191/195 | 102/89/0 | 53.40% (46.33–60.34%) | USD -287.42 | USD 26.90 | USD -54,898.10 | USD -9,788.10 | 4 |
| HOLD_5_OR_DTE_LE_7 | 191/195 | 102/89/0 | 53.40% (46.33–60.34%) | USD -287.42 | USD 26.90 | USD -54,898.10 | USD -9,788.10 | 4 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 103/91/0 | 53.09% (46.08–59.99%) | USD -214.53 | USD 30.90 | USD -41,618.40 | USD -4,344.10 | 1 |
| HOLD_10_SESSIONS | 140/195 | 80/60/0 | 57.14% (48.86–65.04%) | USD -437.66 | USD 164.40 | USD -61,273.00 | USD -6,507.10 | 55 |
| HOLD_10_OR_DTE_LE_7 | 173/195 | 98/75/0 | 56.65% (49.20–63.81%) | USD -338.64 | USD 132.90 | USD -58,584.30 | USD -7,542.10 | 22 |
| HOLD_10_OR_DTE_LE_14 | 194/195 | 104/90/0 | 53.61% (46.59–60.49%) | USD -217.84 | USD 40.90 | USD -42,260.40 | USD -4,344.10 | 1 |
| HOLD_15_SESSIONS | 4/195 | 3/1/0 | 75.00% (30.06–95.44%) | USD 277.40 | USD 219.90 | USD 1,109.60 | USD -375.10 | 191 |
| HOLD_15_OR_DTE_LE_7 | 172/195 | 98/74/0 | 56.98% (49.50–64.14%) | USD -323.32 | USD 130.90 | USD -55,611.20 | USD -7,542.10 | 23 |
| HOLD_15_OR_DTE_LE_14 | 194/195 | 104/90/0 | 53.61% (46.59–60.49%) | USD -217.84 | USD 40.90 | USD -42,260.40 | USD -4,344.10 | 1 |
| HOLD_20_SESSIONS | 0/195 | 0/0/0 | — | — | — | — | — | 195 |
| HOLD_20_OR_DTE_LE_7 | 172/195 | 98/74/0 | 56.98% (49.50–64.14%) | USD -323.32 | USD 130.90 | USD -55,611.20 | USD -7,542.10 | 23 |
| HOLD_20_OR_DTE_LE_14 | 194/195 | 104/90/0 | 53.61% (46.59–60.49%) | USD -217.84 | USD 40.90 | USD -42,260.40 | USD -4,344.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 32.87 | USD -241.19 |
| HOLD_5_OR_DTE_LE_7 | USD 32.87 | USD -241.19 |
| HOLD_5_OR_DTE_LE_14 | USD 21.84 | USD -157.27 |
| HOLD_10_SESSIONS | USD 69.92 | USD -428.49 |
| HOLD_10_OR_DTE_LE_7 | USD 36.27 | USD -295.80 |
| HOLD_10_OR_DTE_LE_14 | USD 20.94 | USD -159.68 |
| HOLD_15_SESSIONS | USD -62.00 | USD 418.50 |
| HOLD_15_OR_DTE_LE_7 | USD 37.36 | USD -281.58 |
| HOLD_15_OR_DTE_LE_14 | USD 20.94 | USD -159.68 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD 37.36 | USD -281.58 |
| HOLD_20_OR_DTE_LE_14 | USD 20.94 | USD -159.68 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 191 | 58.12% | USD -208.32 | USD -39,790.00 | USD -9,709.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 191 | 57.07% | USD -217.42 | USD -41,528.10 | USD -9,718.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 191 | 56.02% | USD -243.32 | USD -46,475.00 | USD -9,744.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 191 | 54.97% | USD -252.42 | USD -48,213.10 | USD -9,753.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 191 | 53.93% | USD -278.32 | USD -53,160.00 | USD -9,779.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 191 | 53.40% | USD -287.42 | USD -54,898.10 | USD -9,788.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 191 | 46.60% | USD -348.32 | USD -66,530.00 | USD -9,849.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 191 | 45.03% | USD -357.42 | USD -68,268.10 | USD -9,858.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 58.12% | USD -208.32 | USD -39,790.00 | USD -9,709.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 57.07% | USD -217.42 | USD -41,528.10 | USD -9,718.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 56.02% | USD -243.32 | USD -46,475.00 | USD -9,744.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 54.97% | USD -252.42 | USD -48,213.10 | USD -9,753.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 53.93% | USD -278.32 | USD -53,160.00 | USD -9,779.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 53.40% | USD -287.42 | USD -54,898.10 | USD -9,788.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 46.60% | USD -348.32 | USD -66,530.00 | USD -9,849.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 45.03% | USD -357.42 | USD -68,268.10 | USD -9,858.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 58.25% | USD -135.43 | USD -26,273.00 | USD -4,265.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 57.22% | USD -144.53 | USD -28,038.40 | USD -4,274.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 54.64% | USD -170.43 | USD -33,063.00 | USD -4,300.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 54.64% | USD -179.53 | USD -34,828.40 | USD -4,309.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 53.09% | USD -205.43 | USD -39,853.00 | USD -4,335.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.09% | USD -214.53 | USD -41,618.40 | USD -4,344.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 46.91% | USD -275.43 | USD -53,433.00 | USD -4,405.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.39% | USD -284.53 | USD -55,198.40 | USD -4,414.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 140 | 61.43% | USD -358.56 | USD -50,199.00 | USD -6,428.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 140 | 61.43% | USD -367.66 | USD -51,473.00 | USD -6,437.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 140 | 60.71% | USD -393.56 | USD -55,099.00 | USD -6,463.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 140 | 60.71% | USD -402.66 | USD -56,373.00 | USD -6,472.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 140 | 59.29% | USD -428.56 | USD -59,999.00 | USD -6,498.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 140 | 57.14% | USD -437.66 | USD -61,273.00 | USD -6,507.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 140 | 55.71% | USD -498.56 | USD -69,799.00 | USD -6,568.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 140 | 55.00% | USD -507.66 | USD -71,073.00 | USD -6,577.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 173 | 61.27% | USD -259.54 | USD -44,900.00 | USD -7,463.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 173 | 60.69% | USD -268.64 | USD -46,474.30 | USD -7,472.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 173 | 58.96% | USD -294.54 | USD -50,955.00 | USD -7,498.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 173 | 58.38% | USD -303.64 | USD -52,529.30 | USD -7,507.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 173 | 57.80% | USD -329.54 | USD -57,010.00 | USD -7,533.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 173 | 56.65% | USD -338.64 | USD -58,584.30 | USD -7,542.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 173 | 52.60% | USD -399.54 | USD -69,120.00 | USD -7,603.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 173 | 52.60% | USD -408.64 | USD -70,694.30 | USD -7,612.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -138.74 | USD -26,915.00 | USD -4,265.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 58.25% | USD -147.84 | USD -28,680.40 | USD -4,274.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 55.67% | USD -173.74 | USD -33,705.00 | USD -4,300.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 55.67% | USD -182.84 | USD -35,470.40 | USD -4,309.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 53.61% | USD -208.74 | USD -40,495.00 | USD -4,335.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.61% | USD -217.84 | USD -42,260.40 | USD -4,344.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 47.42% | USD -278.74 | USD -54,075.00 | USD -4,405.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.39% | USD -287.84 | USD -55,840.40 | USD -4,414.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 4 | 75.00% | USD 356.50 | USD 1,426.00 | USD -296.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 4 | 75.00% | USD 347.40 | USD 1,389.60 | USD -305.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 4 | 75.00% | USD 321.50 | USD 1,286.00 | USD -331.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 4 | 75.00% | USD 312.40 | USD 1,249.60 | USD -340.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 4 | 75.00% | USD 286.50 | USD 1,146.00 | USD -366.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 4 | 75.00% | USD 277.40 | USD 1,109.60 | USD -375.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 4 | 75.00% | USD 216.50 | USD 866.00 | USD -436.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 4 | 75.00% | USD 207.40 | USD 829.60 | USD -445.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 172 | 62.21% | USD -244.22 | USD -42,006.00 | USD -7,463.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 172 | 61.63% | USD -253.32 | USD -43,571.20 | USD -7,472.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 172 | 59.30% | USD -279.22 | USD -48,026.00 | USD -7,498.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 172 | 58.72% | USD -288.32 | USD -49,591.20 | USD -7,507.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 172 | 58.14% | USD -314.22 | USD -54,046.00 | USD -7,533.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 172 | 56.98% | USD -323.32 | USD -55,611.20 | USD -7,542.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 172 | 52.91% | USD -384.22 | USD -66,086.00 | USD -7,603.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 172 | 52.91% | USD -393.32 | USD -67,651.20 | USD -7,612.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -138.74 | USD -26,915.00 | USD -4,265.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 58.25% | USD -147.84 | USD -28,680.40 | USD -4,274.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 55.67% | USD -173.74 | USD -33,705.00 | USD -4,300.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 55.67% | USD -182.84 | USD -35,470.40 | USD -4,309.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 53.61% | USD -208.74 | USD -40,495.00 | USD -4,335.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.61% | USD -217.84 | USD -42,260.40 | USD -4,344.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 47.42% | USD -278.74 | USD -54,075.00 | USD -4,405.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.39% | USD -287.84 | USD -55,840.40 | USD -4,414.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 172 | 62.21% | USD -244.22 | USD -42,006.00 | USD -7,463.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 172 | 61.63% | USD -253.32 | USD -43,571.20 | USD -7,472.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 172 | 59.30% | USD -279.22 | USD -48,026.00 | USD -7,498.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 172 | 58.72% | USD -288.32 | USD -49,591.20 | USD -7,507.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 172 | 58.14% | USD -314.22 | USD -54,046.00 | USD -7,533.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 172 | 56.98% | USD -323.32 | USD -55,611.20 | USD -7,542.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 172 | 52.91% | USD -384.22 | USD -66,086.00 | USD -7,603.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 172 | 52.91% | USD -393.32 | USD -67,651.20 | USD -7,612.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -138.74 | USD -26,915.00 | USD -4,265.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 58.25% | USD -147.84 | USD -28,680.40 | USD -4,274.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 55.67% | USD -173.74 | USD -33,705.00 | USD -4,300.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 55.67% | USD -182.84 | USD -35,470.40 | USD -4,309.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 53.61% | USD -208.74 | USD -40,495.00 | USD -4,335.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 53.61% | USD -217.84 | USD -42,260.40 | USD -4,344.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 47.42% | USD -278.74 | USD -54,075.00 | USD -4,405.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.39% | USD -287.84 | USD -55,840.40 | USD -4,414.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 191/195 (4) | 29.32% (23.32–36.13%) | USD -29.93 | USD -5,716.60 | USD -557.60 |
| HOLD_5_SESSIONS | 1 : 6 | 191/195 (4) | 53.40% (46.33–60.34%) | USD -287.42 | USD -54,898.10 | USD -9,788.10 |
| HOLD_5_SESSIONS | 6 : 1 | 191/195 (4) | 36.65% (30.14–43.68%) | USD 77.92 | USD 14,881.90 | USD -2,687.10 |
| HOLD_5_SESSIONS | 5 : 5 | 191/195 (4) | 29.32% (23.32–36.13%) | USD -149.65 | USD -28,583.00 | USD -2,788.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 191/195 (4) | 29.32% (23.32–36.13%) | USD -29.93 | USD -5,716.60 | USD -557.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 191/195 (4) | 53.40% (46.33–60.34%) | USD -287.42 | USD -54,898.10 | USD -9,788.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 191/195 (4) | 36.65% (30.14–43.68%) | USD 77.92 | USD 14,881.90 | USD -2,687.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 191/195 (4) | 29.32% (23.32–36.13%) | USD -149.65 | USD -28,583.00 | USD -2,788.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 26.29% (20.60–32.90%) | USD -26.97 | USD -5,232.40 | USD -557.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 53.09% (46.08–59.99%) | USD -214.53 | USD -41,618.40 | USD -4,344.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 37.63% (31.11–44.62%) | USD 25.73 | USD 4,991.60 | USD -2,378.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 26.29% (20.60–32.90%) | USD -134.86 | USD -26,162.00 | USD -2,788.00 |
| HOLD_10_SESSIONS | 1 : 1 | 140/195 (55) | 28.57% (21.74–36.55%) | USD -24.09 | USD -3,373.00 | USD -613.60 |
| HOLD_10_SESSIONS | 1 : 6 | 140/195 (55) | 57.14% (48.86–65.04%) | USD -437.66 | USD -61,273.00 | USD -6,507.10 |
| HOLD_10_SESSIONS | 6 : 1 | 140/195 (55) | 37.86% (30.25–46.11%) | USD 269.01 | USD 37,662.00 | USD -2,866.10 |
| HOLD_10_SESSIONS | 5 : 5 | 140/195 (55) | 28.57% (21.74–36.55%) | USD -120.46 | USD -16,865.00 | USD -3,068.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 173/195 (22) | 26.59% (20.57–33.63%) | USD -35.63 | USD -6,164.80 | USD -719.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 173/195 (22) | 56.65% (49.20–63.81%) | USD -338.64 | USD -58,584.30 | USD -7,542.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 173/195 (22) | 31.79% (25.31–39.06%) | USD 89.19 | USD 15,430.70 | USD -2,865.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 173/195 (22) | 26.59% (20.57–33.63%) | USD -178.17 | USD -30,824.00 | USD -3,598.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 26.80% (21.07–33.44%) | USD -28.27 | USD -5,484.40 | USD -557.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 53.61% (46.59–60.49%) | USD -217.84 | USD -42,260.40 | USD -4,344.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 36.60% (30.14–43.58%) | USD 19.95 | USD 3,869.60 | USD -2,378.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 26.80% (21.07–33.44%) | USD -141.35 | USD -27,422.00 | USD -2,788.00 |
| HOLD_15_SESSIONS | 1 : 1 | 4/195 (191) | 50.00% (15.00–85.00%) | USD -14.85 | USD -59.40 | USD -148.60 |
| HOLD_15_SESSIONS | 1 : 6 | 4/195 (191) | 75.00% (30.06–95.44%) | USD 277.40 | USD 1,109.60 | USD -375.10 |
| HOLD_15_SESSIONS | 6 : 1 | 4/195 (191) | 50.00% (15.00–85.00%) | USD -381.35 | USD -1,525.40 | USD -1,385.10 |
| HOLD_15_SESSIONS | 5 : 5 | 4/195 (191) | 50.00% (15.00–85.00%) | USD -74.25 | USD -297.00 | USD -743.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 172/195 (23) | 26.74% (20.69–33.81%) | USD -32.17 | USD -5,533.20 | USD -719.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 172/195 (23) | 56.98% (49.50–64.14%) | USD -323.32 | USD -55,611.20 | USD -7,542.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 172/195 (23) | 33.14% (26.54–40.48%) | USD 98.13 | USD 16,878.80 | USD -2,892.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 172/195 (23) | 26.74% (20.69–33.81%) | USD -160.85 | USD -27,666.00 | USD -3,598.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 26.80% (21.07–33.44%) | USD -28.27 | USD -5,484.40 | USD -557.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 53.61% (46.59–60.49%) | USD -217.84 | USD -42,260.40 | USD -4,344.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 36.60% (30.14–43.58%) | USD 19.95 | USD 3,869.60 | USD -2,378.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 26.80% (21.07–33.44%) | USD -141.35 | USD -27,422.00 | USD -2,788.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/195 (195) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 172/195 (23) | 26.74% (20.69–33.81%) | USD -32.17 | USD -5,533.20 | USD -719.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 172/195 (23) | 56.98% (49.50–64.14%) | USD -323.32 | USD -55,611.20 | USD -7,542.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 172/195 (23) | 33.14% (26.54–40.48%) | USD 98.13 | USD 16,878.80 | USD -2,892.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 172/195 (23) | 26.74% (20.69–33.81%) | USD -160.85 | USD -27,666.00 | USD -3,598.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 26.80% (21.07–33.44%) | USD -28.27 | USD -5,484.40 | USD -557.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 53.61% (46.59–60.49%) | USD -217.84 | USD -42,260.40 | USD -4,344.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 36.60% (30.14–43.58%) | USD 19.95 | USD 3,869.60 | USD -2,378.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 26.80% (21.07–33.44%) | USD -141.35 | USD -27,422.00 | USD -2,788.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -75% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -50% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -40% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -30% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -25% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -20% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -15% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -10% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -5% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| 0% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| 5% | 26/195 | 13.33% | USD -4,370.64 | USD -11,771.30 |
| 10% | 2/195 | 1.03% | USD -14,909.56 | USD -29,188.05 |
| 20% | 0/195 | 0.00% | USD -36,465.36 | USD -64,021.55 |

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