# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 468.80 / USD 2,769.47; mean absolute mismatch USD 2,300.67; mean match score 16.84%.
- Actual selected contract ratios: {'1:6': 180}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 180; entered cohorts: 180; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 179/180 | 125/54/0 | 69.83% (62.75–76.08%) | USD 114.64 | USD 464.90 | USD 20,521.10 | USD -18,671.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 179/180 | 125/54/0 | 69.83% (62.75–76.08%) | USD 114.64 | USD 464.90 | USD 20,521.10 | USD -18,671.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 179/180 | 125/54/0 | 69.83% (62.75–76.08%) | USD 114.64 | USD 464.90 | USD 20,521.10 | USD -18,671.10 | 1 |
| HOLD_10_SESSIONS | 179/180 | 138/41/0 | 77.09% (70.41–82.64%) | USD 265.58 | USD 849.90 | USD 47,538.10 | USD -20,978.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 179/180 | 138/41/0 | 77.09% (70.41–82.64%) | USD 265.58 | USD 849.90 | USD 47,538.10 | USD -20,978.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 179/180 | 138/41/0 | 77.09% (70.41–82.64%) | USD 265.58 | USD 849.90 | USD 47,538.10 | USD -20,978.10 | 1 |
| HOLD_15_SESSIONS | 178/180 | 140/38/0 | 78.65% (72.06–84.03%) | USD 515.61 | USD 1,230.40 | USD 91,779.20 | USD -41,949.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 178/180 | 140/38/0 | 78.65% (72.06–84.03%) | USD 515.61 | USD 1,230.40 | USD 91,779.20 | USD -41,949.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 178/180 | 140/38/0 | 78.65% (72.06–84.03%) | USD 515.61 | USD 1,230.40 | USD 91,779.20 | USD -41,949.10 | 2 |
| HOLD_20_SESSIONS | 177/180 | 140/37/0 | 79.10% (72.52–84.44%) | USD 543.67 | USD 1,450.90 | USD 96,229.30 | USD -46,365.10 | 3 |
| HOLD_20_OR_DTE_LE_7 | 177/180 | 140/37/0 | 79.10% (72.52–84.44%) | USD 543.67 | USD 1,450.90 | USD 96,229.30 | USD -46,365.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 178/180 | 142/36/0 | 79.78% (73.27–85.02%) | USD 583.47 | USD 1,396.90 | USD 103,858.20 | USD -46,365.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -70.42 | USD 264.17 |
| HOLD_5_OR_DTE_LE_7 | USD -70.42 | USD 264.17 |
| HOLD_5_OR_DTE_LE_14 | USD -70.42 | USD 264.17 |
| HOLD_10_SESSIONS | USD -102.51 | USD 447.18 |
| HOLD_10_OR_DTE_LE_7 | USD -102.51 | USD 447.18 |
| HOLD_10_OR_DTE_LE_14 | USD -102.51 | USD 447.18 |
| HOLD_15_SESSIONS | USD -149.42 | USD 744.13 |
| HOLD_15_OR_DTE_LE_7 | USD -149.42 | USD 744.13 |
| HOLD_15_OR_DTE_LE_14 | USD -149.42 | USD 744.13 |
| HOLD_20_SESSIONS | USD -163.44 | USD 786.20 |
| HOLD_20_OR_DTE_LE_7 | USD -163.44 | USD 786.20 |
| HOLD_20_OR_DTE_LE_14 | USD -164.15 | USD 826.72 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 179 | 74.86% | USD 193.74 | USD 34,680.00 | USD -18,592.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 179 | 74.30% | USD 184.64 | USD 33,051.10 | USD -18,601.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 179 | 73.18% | USD 158.74 | USD 28,415.00 | USD -18,627.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 179 | 73.18% | USD 149.64 | USD 26,786.10 | USD -18,636.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 179 | 71.51% | USD 123.74 | USD 22,150.00 | USD -18,662.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 179 | 69.83% | USD 114.64 | USD 20,521.10 | USD -18,671.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 179 | 67.60% | USD 53.74 | USD 9,620.00 | USD -18,732.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 179 | 67.60% | USD 44.64 | USD 7,991.10 | USD -18,741.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 179 | 74.86% | USD 193.74 | USD 34,680.00 | USD -18,592.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 179 | 74.30% | USD 184.64 | USD 33,051.10 | USD -18,601.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 179 | 73.18% | USD 158.74 | USD 28,415.00 | USD -18,627.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 179 | 73.18% | USD 149.64 | USD 26,786.10 | USD -18,636.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 179 | 71.51% | USD 123.74 | USD 22,150.00 | USD -18,662.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 179 | 69.83% | USD 114.64 | USD 20,521.10 | USD -18,671.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 179 | 67.60% | USD 53.74 | USD 9,620.00 | USD -18,732.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 179 | 67.60% | USD 44.64 | USD 7,991.10 | USD -18,741.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 179 | 74.86% | USD 193.74 | USD 34,680.00 | USD -18,592.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 179 | 74.30% | USD 184.64 | USD 33,051.10 | USD -18,601.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 179 | 73.18% | USD 158.74 | USD 28,415.00 | USD -18,627.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 179 | 73.18% | USD 149.64 | USD 26,786.10 | USD -18,636.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 179 | 71.51% | USD 123.74 | USD 22,150.00 | USD -18,662.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 179 | 69.83% | USD 114.64 | USD 20,521.10 | USD -18,671.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 179 | 67.60% | USD 53.74 | USD 9,620.00 | USD -18,732.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 179 | 67.60% | USD 44.64 | USD 7,991.10 | USD -18,741.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 179 | 77.65% | USD 344.68 | USD 61,697.00 | USD -20,899.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 179 | 77.65% | USD 335.58 | USD 60,068.10 | USD -20,908.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 179 | 77.65% | USD 309.68 | USD 55,432.00 | USD -20,934.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 179 | 77.65% | USD 300.58 | USD 53,803.10 | USD -20,943.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 179 | 77.09% | USD 274.68 | USD 49,167.00 | USD -20,969.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 179 | 77.09% | USD 265.58 | USD 47,538.10 | USD -20,978.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 179 | 76.54% | USD 204.68 | USD 36,637.00 | USD -21,039.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 179 | 76.54% | USD 195.58 | USD 35,008.10 | USD -21,048.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 179 | 77.65% | USD 344.68 | USD 61,697.00 | USD -20,899.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 179 | 77.65% | USD 335.58 | USD 60,068.10 | USD -20,908.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 179 | 77.65% | USD 309.68 | USD 55,432.00 | USD -20,934.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 179 | 77.65% | USD 300.58 | USD 53,803.10 | USD -20,943.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 179 | 77.09% | USD 274.68 | USD 49,167.00 | USD -20,969.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 179 | 77.09% | USD 265.58 | USD 47,538.10 | USD -20,978.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 179 | 76.54% | USD 204.68 | USD 36,637.00 | USD -21,039.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 179 | 76.54% | USD 195.58 | USD 35,008.10 | USD -21,048.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 179 | 77.65% | USD 344.68 | USD 61,697.00 | USD -20,899.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 179 | 77.65% | USD 335.58 | USD 60,068.10 | USD -20,908.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 179 | 77.65% | USD 309.68 | USD 55,432.00 | USD -20,934.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 179 | 77.65% | USD 300.58 | USD 53,803.10 | USD -20,943.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 179 | 77.09% | USD 274.68 | USD 49,167.00 | USD -20,969.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 179 | 77.09% | USD 265.58 | USD 47,538.10 | USD -20,978.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 179 | 76.54% | USD 204.68 | USD 36,637.00 | USD -21,039.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 179 | 76.54% | USD 195.58 | USD 35,008.10 | USD -21,048.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 178 | 79.78% | USD 594.71 | USD 105,859.00 | USD -41,870.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 178 | 79.78% | USD 585.61 | USD 104,239.20 | USD -41,879.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 178 | 79.78% | USD 559.71 | USD 99,629.00 | USD -41,905.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 178 | 79.78% | USD 550.61 | USD 98,009.20 | USD -41,914.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 178 | 79.21% | USD 524.71 | USD 93,399.00 | USD -41,940.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 178 | 78.65% | USD 515.61 | USD 91,779.20 | USD -41,949.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 178 | 78.09% | USD 454.71 | USD 80,939.00 | USD -42,010.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 178 | 78.09% | USD 445.61 | USD 79,319.20 | USD -42,019.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 178 | 79.78% | USD 594.71 | USD 105,859.00 | USD -41,870.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 178 | 79.78% | USD 585.61 | USD 104,239.20 | USD -41,879.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 178 | 79.78% | USD 559.71 | USD 99,629.00 | USD -41,905.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 178 | 79.78% | USD 550.61 | USD 98,009.20 | USD -41,914.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 178 | 79.21% | USD 524.71 | USD 93,399.00 | USD -41,940.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 178 | 78.65% | USD 515.61 | USD 91,779.20 | USD -41,949.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 178 | 78.09% | USD 454.71 | USD 80,939.00 | USD -42,010.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 178 | 78.09% | USD 445.61 | USD 79,319.20 | USD -42,019.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 178 | 79.78% | USD 594.71 | USD 105,859.00 | USD -41,870.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 178 | 79.78% | USD 585.61 | USD 104,239.20 | USD -41,879.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 178 | 79.78% | USD 559.71 | USD 99,629.00 | USD -41,905.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 178 | 79.78% | USD 550.61 | USD 98,009.20 | USD -41,914.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 178 | 79.21% | USD 524.71 | USD 93,399.00 | USD -41,940.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 178 | 78.65% | USD 515.61 | USD 91,779.20 | USD -41,949.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 178 | 78.09% | USD 454.71 | USD 80,939.00 | USD -42,010.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 178 | 78.09% | USD 445.61 | USD 79,319.20 | USD -42,019.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 177 | 79.10% | USD 622.77 | USD 110,230.00 | USD -46,286.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 177 | 79.10% | USD 613.67 | USD 108,619.30 | USD -46,295.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 177 | 79.10% | USD 587.77 | USD 104,035.00 | USD -46,321.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 177 | 79.10% | USD 578.67 | USD 102,424.30 | USD -46,330.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 177 | 79.10% | USD 552.77 | USD 97,840.00 | USD -46,356.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 177 | 79.10% | USD 543.67 | USD 96,229.30 | USD -46,365.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 177 | 79.10% | USD 482.77 | USD 85,450.00 | USD -46,426.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 177 | 79.10% | USD 473.67 | USD 83,839.30 | USD -46,435.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 177 | 79.10% | USD 622.77 | USD 110,230.00 | USD -46,286.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 177 | 79.10% | USD 613.67 | USD 108,619.30 | USD -46,295.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 177 | 79.10% | USD 587.77 | USD 104,035.00 | USD -46,321.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 177 | 79.10% | USD 578.67 | USD 102,424.30 | USD -46,330.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 177 | 79.10% | USD 552.77 | USD 97,840.00 | USD -46,356.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 177 | 79.10% | USD 543.67 | USD 96,229.30 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 177 | 79.10% | USD 482.77 | USD 85,450.00 | USD -46,426.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 177 | 79.10% | USD 473.67 | USD 83,839.30 | USD -46,435.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 178 | 80.34% | USD 662.57 | USD 117,938.00 | USD -46,286.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 178 | 80.34% | USD 653.47 | USD 116,318.20 | USD -46,295.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 178 | 79.78% | USD 627.57 | USD 111,708.00 | USD -46,321.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 178 | 79.78% | USD 618.47 | USD 110,088.20 | USD -46,330.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 178 | 79.78% | USD 592.57 | USD 105,478.00 | USD -46,356.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 178 | 79.78% | USD 583.47 | USD 103,858.20 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 178 | 79.78% | USD 522.57 | USD 93,018.00 | USD -46,426.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 178 | 79.78% | USD 513.47 | USD 91,398.20 | USD -46,435.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -49.00 | USD -8,770.40 | USD -1,564.60 |
| HOLD_5_SESSIONS | 1 : 6 | 179/180 (1) | 69.83% (62.75–76.08%) | USD 114.64 | USD 20,521.10 | USD -18,671.10 |
| HOLD_5_SESSIONS | 6 : 1 | 179/180 (1) | 25.14% (19.35–31.97%) | USD -457.62 | USD -81,913.90 | USD -4,497.10 |
| HOLD_5_SESSIONS | 5 : 5 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -244.98 | USD -43,852.00 | USD -7,823.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -49.00 | USD -8,770.40 | USD -1,564.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 179/180 (1) | 69.83% (62.75–76.08%) | USD 114.64 | USD 20,521.10 | USD -18,671.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 179/180 (1) | 25.14% (19.35–31.97%) | USD -457.62 | USD -81,913.90 | USD -4,497.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -244.98 | USD -43,852.00 | USD -7,823.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -49.00 | USD -8,770.40 | USD -1,564.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 179/180 (1) | 69.83% (62.75–76.08%) | USD 114.64 | USD 20,521.10 | USD -18,671.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 179/180 (1) | 25.14% (19.35–31.97%) | USD -457.62 | USD -81,913.90 | USD -4,497.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -244.98 | USD -43,852.00 | USD -7,823.00 |
| HOLD_10_SESSIONS | 1 : 1 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -50.58 | USD -9,053.40 | USD -1,981.60 |
| HOLD_10_SESSIONS | 1 : 6 | 179/180 (1) | 77.09% (70.41–82.64%) | USD 265.58 | USD 47,538.10 | USD -20,978.10 |
| HOLD_10_SESSIONS | 6 : 1 | 179/180 (1) | 19.55% (14.41–25.98%) | USD -619.62 | USD -110,911.90 | USD -6,005.10 |
| HOLD_10_SESSIONS | 5 : 5 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -252.89 | USD -45,267.00 | USD -9,908.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -50.58 | USD -9,053.40 | USD -1,981.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 179/180 (1) | 77.09% (70.41–82.64%) | USD 265.58 | USD 47,538.10 | USD -20,978.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 179/180 (1) | 19.55% (14.41–25.98%) | USD -619.62 | USD -110,911.90 | USD -6,005.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -252.89 | USD -45,267.00 | USD -9,908.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -50.58 | USD -9,053.40 | USD -1,981.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 179/180 (1) | 77.09% (70.41–82.64%) | USD 265.58 | USD 47,538.10 | USD -20,978.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 179/180 (1) | 19.55% (14.41–25.98%) | USD -619.62 | USD -110,911.90 | USD -6,005.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 179/180 (1) | 32.40% (25.98–39.57%) | USD -252.89 | USD -45,267.00 | USD -9,908.00 |
| HOLD_15_SESSIONS | 1 : 1 | 178/180 (2) | 37.08% (30.33–44.38%) | USD -48.00 | USD -8,543.80 | USD -3,252.60 |
| HOLD_15_SESSIONS | 1 : 6 | 178/180 (2) | 78.65% (72.06–84.03%) | USD 515.61 | USD 91,779.20 | USD -41,949.10 |
| HOLD_15_SESSIONS | 6 : 1 | 178/180 (2) | 20.22% (14.98–26.73%) | USD -851.61 | USD -151,585.80 | USD -5,236.10 |
| HOLD_15_SESSIONS | 5 : 5 | 178/180 (2) | 37.08% (30.33–44.38%) | USD -239.99 | USD -42,719.00 | USD -16,263.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 178/180 (2) | 37.08% (30.33–44.38%) | USD -48.00 | USD -8,543.80 | USD -3,252.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 178/180 (2) | 78.65% (72.06–84.03%) | USD 515.61 | USD 91,779.20 | USD -41,949.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 178/180 (2) | 20.22% (14.98–26.73%) | USD -851.61 | USD -151,585.80 | USD -5,236.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 178/180 (2) | 37.08% (30.33–44.38%) | USD -239.99 | USD -42,719.00 | USD -16,263.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 178/180 (2) | 37.08% (30.33–44.38%) | USD -48.00 | USD -8,543.80 | USD -3,252.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 178/180 (2) | 78.65% (72.06–84.03%) | USD 515.61 | USD 91,779.20 | USD -41,949.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 178/180 (2) | 20.22% (14.98–26.73%) | USD -851.61 | USD -151,585.80 | USD -5,236.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 178/180 (2) | 37.08% (30.33–44.38%) | USD -239.99 | USD -42,719.00 | USD -16,263.00 |
| HOLD_20_SESSIONS | 1 : 1 | 177/180 (3) | 41.81% (34.79–49.17%) | USD -55.00 | USD -9,735.20 | USD -4,038.60 |
| HOLD_20_SESSIONS | 1 : 6 | 177/180 (3) | 79.10% (72.52–84.44%) | USD 543.67 | USD 96,229.30 | USD -46,365.10 |
| HOLD_20_SESSIONS | 6 : 1 | 177/180 (3) | 18.08% (13.11–24.41%) | USD -928.68 | USD -164,375.70 | USD -5,296.10 |
| HOLD_20_SESSIONS | 5 : 5 | 177/180 (3) | 41.81% (34.79–49.17%) | USD -275.01 | USD -48,676.00 | USD -20,193.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 177/180 (3) | 41.81% (34.79–49.17%) | USD -55.00 | USD -9,735.20 | USD -4,038.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 177/180 (3) | 79.10% (72.52–84.44%) | USD 543.67 | USD 96,229.30 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 177/180 (3) | 18.08% (13.11–24.41%) | USD -928.68 | USD -164,375.70 | USD -5,296.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 177/180 (3) | 41.81% (34.79–49.17%) | USD -275.01 | USD -48,676.00 | USD -20,193.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 178/180 (2) | 41.57% (34.59–48.92%) | USD -48.96 | USD -8,714.80 | USD -4,038.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 178/180 (2) | 79.78% (73.27–85.02%) | USD 583.47 | USD 103,858.20 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 178/180 (2) | 16.85% (12.07–23.04%) | USD -926.19 | USD -164,861.80 | USD -5,296.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 178/180 (2) | 41.57% (34.59–48.92%) | USD -244.80 | USD -43,574.00 | USD -20,193.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/180 | 0.00% | USD -208,183.23 | USD -333,656.55 |
| -75% | 0/180 | 0.00% | USD -153,442.64 | USD -246,826.80 |
| -50% | 0/180 | 0.00% | USD -98,702.06 | USD -159,997.05 |
| -40% | 0/180 | 0.00% | USD -76,805.83 | USD -125,265.15 |
| -30% | 0/180 | 0.00% | USD -54,909.59 | USD -90,533.25 |
| -25% | 0/180 | 0.00% | USD -43,961.48 | USD -74,073.55 |
| -20% | 0/180 | 0.00% | USD -33,013.36 | USD -58,191.35 |
| -15% | 0/180 | 0.00% | USD -22,065.24 | USD -42,309.15 |
| -10% | 7/180 | 3.89% | USD -11,126.82 | USD -26,426.95 |
| -5% | 76/180 | 42.22% | USD -850.87 | USD -10,544.75 |
| 0% | 180/180 | 100.00% | USD 2,257.47 | USD 569.45 |
| 5% | 180/180 | 100.00% | USD 2,261.12 | USD 569.45 |
| 10% | 180/180 | 100.00% | USD 2,261.12 | USD 569.45 |
| 20% | 180/180 | 100.00% | USD 2,261.12 | USD 569.45 |

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