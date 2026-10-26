# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 190.47 / USD 1,037.69; mean absolute mismatch USD 847.23; mean match score 18.54%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/195 | 92/102/0 | 47.42% (40.51–54.43%) | USD -263.65 | USD -24.60 | USD -51,148.40 | USD -5,433.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 194/195 | 92/102/0 | 47.42% (40.51–54.43%) | USD -263.65 | USD -24.60 | USD -51,148.40 | USD -5,433.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 92/102/0 | 47.42% (40.51–54.43%) | USD -263.65 | USD -24.60 | USD -51,148.40 | USD -5,433.10 | 1 |
| HOLD_10_SESSIONS | 190/195 | 115/75/0 | 60.53% (53.43–67.20%) | USD -246.93 | USD 142.40 | USD -46,917.00 | USD -5,571.10 | 5 |
| HOLD_10_OR_DTE_LE_7 | 190/195 | 115/75/0 | 60.53% (53.43–67.20%) | USD -246.93 | USD 142.40 | USD -46,917.00 | USD -5,571.10 | 5 |
| HOLD_10_OR_DTE_LE_14 | 192/195 | 114/78/0 | 59.38% (52.31–66.07%) | USD -219.84 | USD 144.40 | USD -42,209.20 | USD -5,571.10 | 3 |
| HOLD_15_SESSIONS | 159/195 | 95/64/0 | 59.75% (51.98–67.05%) | USD -443.57 | USD 190.90 | USD -70,526.90 | USD -15,128.10 | 36 |
| HOLD_15_OR_DTE_LE_7 | 164/195 | 97/67/0 | 59.15% (51.50–66.38%) | USD -400.08 | USD 198.40 | USD -65,612.40 | USD -15,128.10 | 31 |
| HOLD_15_OR_DTE_LE_14 | 188/195 | 114/74/0 | 60.64% (53.51–67.34%) | USD -251.37 | USD 152.90 | USD -47,256.80 | USD -13,580.10 | 7 |
| HOLD_20_SESSIONS | 28/195 | 11/17/0 | 39.29% (23.57–57.59%) | USD -1,734.96 | USD -949.60 | USD -48,578.80 | USD -12,564.10 | 167 |
| HOLD_20_OR_DTE_LE_7 | 159/195 | 96/63/0 | 60.38% (52.62–67.65%) | USD -453.89 | USD 231.90 | USD -72,167.90 | USD -18,669.10 | 36 |
| HOLD_20_OR_DTE_LE_14 | 188/195 | 114/74/0 | 60.64% (53.51–67.34%) | USD -251.37 | USD 152.90 | USD -47,256.80 | USD -13,580.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 30.86 | USD -215.41 |
| HOLD_5_OR_DTE_LE_7 | USD 30.86 | USD -215.41 |
| HOLD_5_OR_DTE_LE_14 | USD 30.86 | USD -215.41 |
| HOLD_10_SESSIONS | USD 27.96 | USD -195.79 |
| HOLD_10_OR_DTE_LE_7 | USD 27.96 | USD -195.79 |
| HOLD_10_OR_DTE_LE_14 | USD 27.23 | USD -167.97 |
| HOLD_15_SESSIONS | USD 104.63 | USD -469.09 |
| HOLD_15_OR_DTE_LE_7 | USD 94.78 | USD -415.76 |
| HOLD_15_OR_DTE_LE_14 | USD 34.67 | USD -206.94 |
| HOLD_20_SESSIONS | USD 431.07 | USD -2,086.93 |
| HOLD_20_OR_DTE_LE_7 | USD 105.14 | USD -479.92 |
| HOLD_20_OR_DTE_LE_14 | USD 34.67 | USD -206.94 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 53.61% | USD -184.55 | USD -35,803.00 | USD -5,354.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 52.58% | USD -193.65 | USD -37,568.40 | USD -5,363.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 51.03% | USD -219.55 | USD -42,593.00 | USD -5,389.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 51.03% | USD -228.65 | USD -44,358.40 | USD -5,398.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 48.45% | USD -254.55 | USD -49,383.00 | USD -5,424.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 47.42% | USD -263.65 | USD -51,148.40 | USD -5,433.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 43.30% | USD -324.55 | USD -62,963.00 | USD -5,494.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 42.27% | USD -333.65 | USD -64,728.40 | USD -5,503.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 53.61% | USD -184.55 | USD -35,803.00 | USD -5,354.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 52.58% | USD -193.65 | USD -37,568.40 | USD -5,363.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 51.03% | USD -219.55 | USD -42,593.00 | USD -5,389.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 51.03% | USD -228.65 | USD -44,358.40 | USD -5,398.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 48.45% | USD -254.55 | USD -49,383.00 | USD -5,424.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 47.42% | USD -263.65 | USD -51,148.40 | USD -5,433.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 43.30% | USD -324.55 | USD -62,963.00 | USD -5,494.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 42.27% | USD -333.65 | USD -64,728.40 | USD -5,503.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 53.61% | USD -184.55 | USD -35,803.00 | USD -5,354.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 52.58% | USD -193.65 | USD -37,568.40 | USD -5,363.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 51.03% | USD -219.55 | USD -42,593.00 | USD -5,389.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 51.03% | USD -228.65 | USD -44,358.40 | USD -5,398.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 48.45% | USD -254.55 | USD -49,383.00 | USD -5,424.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 47.42% | USD -263.65 | USD -51,148.40 | USD -5,433.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 43.30% | USD -324.55 | USD -62,963.00 | USD -5,494.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 42.27% | USD -333.65 | USD -64,728.40 | USD -5,503.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 190 | 62.11% | USD -167.83 | USD -31,888.00 | USD -5,492.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 190 | 61.58% | USD -176.93 | USD -33,617.00 | USD -5,501.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 190 | 61.58% | USD -202.83 | USD -38,538.00 | USD -5,527.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 190 | 61.05% | USD -211.93 | USD -40,267.00 | USD -5,536.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 190 | 60.53% | USD -237.83 | USD -45,188.00 | USD -5,562.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 190 | 60.53% | USD -246.93 | USD -46,917.00 | USD -5,571.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 190 | 56.32% | USD -307.83 | USD -58,488.00 | USD -5,632.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 190 | 55.79% | USD -316.93 | USD -60,217.00 | USD -5,641.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 190 | 62.11% | USD -167.83 | USD -31,888.00 | USD -5,492.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 190 | 61.58% | USD -176.93 | USD -33,617.00 | USD -5,501.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 190 | 61.58% | USD -202.83 | USD -38,538.00 | USD -5,527.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 190 | 61.05% | USD -211.93 | USD -40,267.00 | USD -5,536.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 190 | 60.53% | USD -237.83 | USD -45,188.00 | USD -5,562.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 190 | 60.53% | USD -246.93 | USD -46,917.00 | USD -5,571.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 190 | 56.32% | USD -307.83 | USD -58,488.00 | USD -5,632.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 190 | 55.79% | USD -316.93 | USD -60,217.00 | USD -5,641.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 192 | 62.50% | USD -140.74 | USD -27,022.00 | USD -5,492.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 192 | 61.46% | USD -149.84 | USD -28,769.20 | USD -5,501.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 192 | 60.94% | USD -175.74 | USD -33,742.00 | USD -5,527.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 192 | 60.42% | USD -184.84 | USD -35,489.20 | USD -5,536.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 192 | 59.38% | USD -210.74 | USD -40,462.00 | USD -5,562.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 192 | 59.38% | USD -219.84 | USD -42,209.20 | USD -5,571.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 192 | 56.25% | USD -280.74 | USD -53,902.00 | USD -5,632.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 192 | 55.73% | USD -289.84 | USD -55,649.20 | USD -5,641.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 159 | 61.01% | USD -364.47 | USD -57,950.00 | USD -15,049.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 159 | 61.01% | USD -373.57 | USD -59,396.90 | USD -15,058.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 159 | 61.01% | USD -399.47 | USD -63,515.00 | USD -15,084.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 159 | 60.38% | USD -408.57 | USD -64,961.90 | USD -15,093.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 159 | 59.75% | USD -434.47 | USD -69,080.00 | USD -15,119.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 159 | 59.75% | USD -443.57 | USD -70,526.90 | USD -15,128.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 159 | 56.60% | USD -504.47 | USD -80,210.00 | USD -15,189.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 159 | 56.60% | USD -513.57 | USD -81,656.90 | USD -15,198.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 164 | 60.37% | USD -320.98 | USD -52,640.00 | USD -15,049.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 164 | 60.37% | USD -330.08 | USD -54,132.40 | USD -15,058.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 164 | 60.37% | USD -355.98 | USD -58,380.00 | USD -15,084.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 164 | 59.15% | USD -365.08 | USD -59,872.40 | USD -15,093.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 164 | 59.15% | USD -390.98 | USD -64,120.00 | USD -15,119.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 164 | 59.15% | USD -400.08 | USD -65,612.40 | USD -15,128.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 164 | 56.10% | USD -460.98 | USD -75,600.00 | USD -15,189.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 164 | 56.10% | USD -470.08 | USD -77,092.40 | USD -15,198.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 188 | 62.77% | USD -172.27 | USD -32,386.00 | USD -13,501.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 188 | 62.23% | USD -181.37 | USD -34,096.80 | USD -13,510.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 188 | 61.17% | USD -207.27 | USD -38,966.00 | USD -13,536.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 188 | 61.17% | USD -216.37 | USD -40,676.80 | USD -13,545.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 188 | 60.64% | USD -242.27 | USD -45,546.00 | USD -13,571.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 188 | 60.64% | USD -251.37 | USD -47,256.80 | USD -13,580.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 188 | 56.91% | USD -312.27 | USD -58,706.00 | USD -13,641.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 188 | 55.85% | USD -321.37 | USD -60,416.80 | USD -13,650.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 28 | 39.29% | USD -1,655.86 | USD -46,364.00 | USD -12,485.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 28 | 39.29% | USD -1,664.96 | USD -46,618.80 | USD -12,494.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 28 | 39.29% | USD -1,690.86 | USD -47,344.00 | USD -12,520.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 28 | 39.29% | USD -1,699.96 | USD -47,598.80 | USD -12,529.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 28 | 39.29% | USD -1,725.86 | USD -48,324.00 | USD -12,555.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 28 | 39.29% | USD -1,734.96 | USD -48,578.80 | USD -12,564.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 28 | 32.14% | USD -1,795.86 | USD -50,284.00 | USD -12,625.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 28 | 32.14% | USD -1,804.96 | USD -50,538.80 | USD -12,634.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 159 | 62.26% | USD -374.79 | USD -59,591.00 | USD -18,590.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 159 | 61.64% | USD -383.89 | USD -61,037.90 | USD -18,599.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 159 | 61.64% | USD -409.79 | USD -65,156.00 | USD -18,625.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 159 | 60.38% | USD -418.89 | USD -66,602.90 | USD -18,634.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 159 | 60.38% | USD -444.79 | USD -70,721.00 | USD -18,660.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 159 | 60.38% | USD -453.89 | USD -72,167.90 | USD -18,669.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 159 | 57.86% | USD -514.79 | USD -81,851.00 | USD -18,730.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 159 | 57.86% | USD -523.89 | USD -83,297.90 | USD -18,739.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 188 | 62.77% | USD -172.27 | USD -32,386.00 | USD -13,501.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 188 | 62.23% | USD -181.37 | USD -34,096.80 | USD -13,510.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 188 | 61.17% | USD -207.27 | USD -38,966.00 | USD -13,536.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 188 | 61.17% | USD -216.37 | USD -40,676.80 | USD -13,545.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 188 | 60.64% | USD -242.27 | USD -45,546.00 | USD -13,571.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 188 | 60.64% | USD -251.37 | USD -47,256.80 | USD -13,580.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 188 | 56.91% | USD -312.27 | USD -58,706.00 | USD -13,641.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 188 | 55.85% | USD -321.37 | USD -60,416.80 | USD -13,650.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/195 (1) | 27.32% (21.54–33.98%) | USD -27.64 | USD -5,362.40 | USD -555.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/195 (1) | 47.42% (40.51–54.43%) | USD -263.65 | USD -51,148.40 | USD -5,433.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/195 (1) | 38.14% (31.60–45.15%) | USD 70.16 | USD 13,611.60 | USD -3,082.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/195 (1) | 27.32% (21.54–33.98%) | USD -138.21 | USD -26,812.00 | USD -2,778.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/195 (1) | 27.32% (21.54–33.98%) | USD -27.64 | USD -5,362.40 | USD -555.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/195 (1) | 47.42% (40.51–54.43%) | USD -263.65 | USD -51,148.40 | USD -5,433.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/195 (1) | 38.14% (31.60–45.15%) | USD 70.16 | USD 13,611.60 | USD -3,082.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/195 (1) | 27.32% (21.54–33.98%) | USD -138.21 | USD -26,812.00 | USD -2,778.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 27.32% (21.54–33.98%) | USD -27.64 | USD -5,362.40 | USD -555.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 47.42% (40.51–54.43%) | USD -263.65 | USD -51,148.40 | USD -5,433.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 38.14% (31.60–45.15%) | USD 70.16 | USD 13,611.60 | USD -3,082.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 27.32% (21.54–33.98%) | USD -138.21 | USD -26,812.00 | USD -2,778.00 |
| HOLD_10_SESSIONS | 1 : 1 | 190/195 (5) | 31.05% (24.90–37.95%) | USD -27.27 | USD -5,182.00 | USD -533.60 |
| HOLD_10_SESSIONS | 1 : 6 | 190/195 (5) | 60.53% (53.43–67.20%) | USD -246.93 | USD -46,917.00 | USD -5,571.10 |
| HOLD_10_SESSIONS | 6 : 1 | 190/195 (5) | 35.79% (29.32–42.83%) | USD 56.02 | USD 10,643.00 | USD -3,093.10 |
| HOLD_10_SESSIONS | 5 : 5 | 190/195 (5) | 31.05% (24.90–37.95%) | USD -136.37 | USD -25,910.00 | USD -2,668.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 190/195 (5) | 31.05% (24.90–37.95%) | USD -27.27 | USD -5,182.00 | USD -533.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 190/195 (5) | 60.53% (53.43–67.20%) | USD -246.93 | USD -46,917.00 | USD -5,571.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 190/195 (5) | 35.79% (29.32–42.83%) | USD 56.02 | USD 10,643.00 | USD -3,093.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 190/195 (5) | 31.05% (24.90–37.95%) | USD -136.37 | USD -25,910.00 | USD -2,668.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 192/195 (3) | 30.73% (24.63–37.58%) | USD -23.37 | USD -4,486.20 | USD -533.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 192/195 (3) | 59.38% (52.31–66.07%) | USD -219.84 | USD -42,209.20 | USD -5,571.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 192/195 (3) | 34.38% (28.02–41.34%) | USD 56.28 | USD 10,805.80 | USD -3,053.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 192/195 (3) | 30.73% (24.63–37.58%) | USD -116.83 | USD -22,431.00 | USD -2,668.00 |
| HOLD_15_SESSIONS | 1 : 1 | 159/195 (36) | 35.22% (28.22–42.91%) | USD 3.85 | USD 611.60 | USD -1,588.60 |
| HOLD_15_SESSIONS | 1 : 6 | 159/195 (36) | 59.75% (51.98–67.05%) | USD -443.57 | USD -70,526.90 | USD -15,128.10 |
| HOLD_15_SESSIONS | 6 : 1 | 159/195 (36) | 34.59% (27.64–42.27%) | USD 470.49 | USD 74,808.10 | USD -3,520.10 |
| HOLD_15_SESSIONS | 5 : 5 | 159/195 (36) | 35.22% (28.22–42.91%) | USD 19.23 | USD 3,058.00 | USD -7,943.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 164/195 (31) | 34.15% (27.33–41.69%) | USD 2.89 | USD 473.60 | USD -1,588.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 164/195 (31) | 59.15% (51.50–66.38%) | USD -400.08 | USD -65,612.40 | USD -15,128.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 164/195 (31) | 33.54% (26.76–41.07%) | USD 420.29 | USD 68,927.60 | USD -3,468.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 164/195 (31) | 34.15% (27.33–41.69%) | USD 14.44 | USD 2,368.00 | USD -7,943.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 188/195 (7) | 30.85% (24.69–37.78%) | USD -22.42 | USD -4,214.80 | USD -509.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 188/195 (7) | 60.64% (53.51–67.34%) | USD -251.37 | USD -47,256.80 | USD -13,580.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 188/195 (7) | 33.51% (27.15–40.53%) | USD 94.43 | USD 17,753.20 | USD -3,053.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 188/195 (7) | 30.85% (24.69–37.78%) | USD -112.10 | USD -21,074.00 | USD -2,548.00 |
| HOLD_20_SESSIONS | 1 : 1 | 28/195 (167) | 46.43% (29.53–64.19%) | USD 60.65 | USD 1,698.20 | USD -405.60 |
| HOLD_20_SESSIONS | 1 : 6 | 28/195 (167) | 39.29% (23.57–57.59%) | USD -1,734.96 | USD -48,578.80 | USD -12,564.10 |
| HOLD_20_SESSIONS | 6 : 1 | 28/195 (167) | 67.86% (49.34–82.07%) | USD 2,159.51 | USD 60,466.20 | USD -1,443.10 |
| HOLD_20_SESSIONS | 5 : 5 | 28/195 (167) | 46.43% (29.53–64.19%) | USD 303.25 | USD 8,491.00 | USD -2,028.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 159/195 (36) | 35.85% (28.81–43.56%) | USD 2.55 | USD 405.60 | USD -1,588.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 159/195 (36) | 60.38% (52.62–67.65%) | USD -453.89 | USD -72,167.90 | USD -18,669.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 159/195 (36) | 35.22% (28.22–42.91%) | USD 471.74 | USD 75,007.10 | USD -3,468.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 159/195 (36) | 35.85% (28.81–43.56%) | USD 12.75 | USD 2,028.00 | USD -7,943.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 188/195 (7) | 30.85% (24.69–37.78%) | USD -22.42 | USD -4,214.80 | USD -509.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 188/195 (7) | 60.64% (53.51–67.34%) | USD -251.37 | USD -47,256.80 | USD -13,580.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 188/195 (7) | 33.51% (27.15–40.53%) | USD 94.43 | USD 17,753.20 | USD -3,053.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 188/195 (7) | 30.85% (24.69–37.78%) | USD -112.10 | USD -21,074.00 | USD -2,548.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -75% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -50% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -40% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -30% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -25% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -20% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -15% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -10% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| -5% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| 0% | 195/195 | 100.00% | USD 807.68 | USD 58.45 |
| 5% | 42/195 | 21.54% | USD -3,122.03 | USD -9,429.45 |
| 10% | 3/195 | 1.54% | USD -13,544.87 | USD -26,635.05 |
| 20% | 1/195 | 0.51% | USD -35,076.46 | USD -61,468.55 |

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