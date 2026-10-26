# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 349.93 / USD 2,052.77; mean absolute mismatch USD 1,702.84; mean match score 16.94%.
- Actual selected contract ratios: {'1:6': 194}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 194; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/194 | 132/62/0 | 68.04% (61.18–74.20%) | USD -34.70 | USD 404.90 | USD -6,731.40 | USD -18,989.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 194/194 | 132/62/0 | 68.04% (61.18–74.20%) | USD -34.70 | USD 404.90 | USD -6,731.40 | USD -18,989.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 194/194 | 132/62/0 | 68.04% (61.18–74.20%) | USD -34.70 | USD 404.90 | USD -6,731.40 | USD -18,989.10 | 0 |
| HOLD_10_SESSIONS | 193/194 | 153/40/0 | 79.27% (73.01–84.39%) | USD 330.50 | USD 830.90 | USD 63,785.70 | USD -15,730.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 193/194 | 153/40/0 | 79.27% (73.01–84.39%) | USD 330.50 | USD 830.90 | USD 63,785.70 | USD -15,730.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 193/194 | 150/43/0 | 77.72% (71.34–83.02%) | USD 339.21 | USD 801.90 | USD 65,467.70 | USD -15,730.10 | 1 |
| HOLD_15_SESSIONS | 186/194 | 148/38/0 | 79.57% (73.20–84.74%) | USD 168.33 | USD 1,099.40 | USD 31,309.40 | USD -34,120.10 | 8 |
| HOLD_15_OR_DTE_LE_7 | 190/194 | 152/38/0 | 80.00% (73.74–85.07%) | USD 196.42 | USD 1,090.90 | USD 37,319.00 | USD -34,120.10 | 4 |
| HOLD_15_OR_DTE_LE_14 | 193/194 | 149/44/0 | 77.20% (70.79–82.56%) | USD 277.11 | USD 860.90 | USD 53,482.70 | USD -34,120.10 | 1 |
| HOLD_20_SESSIONS | 20/194 | 11/9/0 | 55.00% (34.21–74.18%) | USD -1,628.50 | USD 545.90 | USD -32,570.00 | USD -29,606.10 | 174 |
| HOLD_20_OR_DTE_LE_7 | 183/194 | 149/34/0 | 81.42% (75.16–86.39%) | USD 225.01 | USD 1,121.90 | USD 41,177.70 | USD -32,761.10 | 11 |
| HOLD_20_OR_DTE_LE_14 | 193/194 | 149/44/0 | 77.20% (70.79–82.56%) | USD 277.11 | USD 860.90 | USD 53,482.70 | USD -34,120.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -32.33 | USD 76.73 |
| HOLD_5_OR_DTE_LE_7 | USD -32.33 | USD 76.73 |
| HOLD_5_OR_DTE_LE_14 | USD -32.33 | USD 76.73 |
| HOLD_10_SESSIONS | USD -98.63 | USD 508.23 |
| HOLD_10_OR_DTE_LE_7 | USD -98.63 | USD 508.23 |
| HOLD_10_OR_DTE_LE_14 | USD -90.45 | USD 508.76 |
| HOLD_15_SESSIONS | USD -85.92 | USD 333.35 |
| HOLD_15_OR_DTE_LE_7 | USD -87.36 | USD 362.87 |
| HOLD_15_OR_DTE_LE_14 | USD -88.91 | USD 445.12 |
| HOLD_20_SESSIONS | USD 182.50 | USD -1,731.90 |
| HOLD_20_OR_DTE_LE_7 | USD -95.69 | USD 399.80 |
| HOLD_20_OR_DTE_LE_14 | USD -88.91 | USD 445.12 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 68.56% | USD 44.40 | USD 8,614.00 | USD -18,910.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 68.56% | USD 35.30 | USD 6,848.60 | USD -18,919.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 68.04% | USD 9.40 | USD 1,824.00 | USD -18,945.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 68.04% | USD 0.30 | USD 58.60 | USD -18,954.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 68.04% | USD -25.60 | USD -4,966.00 | USD -18,980.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 68.04% | USD -34.70 | USD -6,731.40 | USD -18,989.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 67.01% | USD -95.60 | USD -18,546.00 | USD -19,050.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 66.49% | USD -104.70 | USD -20,311.40 | USD -19,059.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 68.56% | USD 44.40 | USD 8,614.00 | USD -18,910.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 68.56% | USD 35.30 | USD 6,848.60 | USD -18,919.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 68.04% | USD 9.40 | USD 1,824.00 | USD -18,945.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 68.04% | USD 0.30 | USD 58.60 | USD -18,954.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 68.04% | USD -25.60 | USD -4,966.00 | USD -18,980.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 68.04% | USD -34.70 | USD -6,731.40 | USD -18,989.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 67.01% | USD -95.60 | USD -18,546.00 | USD -19,050.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 66.49% | USD -104.70 | USD -20,311.40 | USD -19,059.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 68.56% | USD 44.40 | USD 8,614.00 | USD -18,910.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 68.56% | USD 35.30 | USD 6,848.60 | USD -18,919.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 68.04% | USD 9.40 | USD 1,824.00 | USD -18,945.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 68.04% | USD 0.30 | USD 58.60 | USD -18,954.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 68.04% | USD -25.60 | USD -4,966.00 | USD -18,980.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 68.04% | USD -34.70 | USD -6,731.40 | USD -18,989.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 67.01% | USD -95.60 | USD -18,546.00 | USD -19,050.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 66.49% | USD -104.70 | USD -20,311.40 | USD -19,059.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 193 | 79.79% | USD 409.60 | USD 79,052.00 | USD -15,651.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 193 | 79.79% | USD 400.50 | USD 77,295.70 | USD -15,660.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 193 | 79.27% | USD 374.60 | USD 72,297.00 | USD -15,686.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 193 | 79.27% | USD 365.50 | USD 70,540.70 | USD -15,695.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 193 | 79.27% | USD 339.60 | USD 65,542.00 | USD -15,721.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 193 | 79.27% | USD 330.50 | USD 63,785.70 | USD -15,730.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 193 | 79.27% | USD 269.60 | USD 52,032.00 | USD -15,791.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 193 | 78.76% | USD 260.50 | USD 50,275.70 | USD -15,800.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 79.79% | USD 409.60 | USD 79,052.00 | USD -15,651.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 79.79% | USD 400.50 | USD 77,295.70 | USD -15,660.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 79.27% | USD 374.60 | USD 72,297.00 | USD -15,686.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 79.27% | USD 365.50 | USD 70,540.70 | USD -15,695.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 79.27% | USD 339.60 | USD 65,542.00 | USD -15,721.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 79.27% | USD 330.50 | USD 63,785.70 | USD -15,730.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 79.27% | USD 269.60 | USD 52,032.00 | USD -15,791.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 78.76% | USD 260.50 | USD 50,275.70 | USD -15,800.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 78.24% | USD 418.31 | USD 80,734.00 | USD -15,651.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 78.24% | USD 409.21 | USD 78,977.70 | USD -15,660.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 77.72% | USD 383.31 | USD 73,979.00 | USD -15,686.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 77.72% | USD 374.21 | USD 72,222.70 | USD -15,695.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 77.72% | USD 348.31 | USD 67,224.00 | USD -15,721.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 77.72% | USD 339.21 | USD 65,467.70 | USD -15,730.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 77.72% | USD 278.31 | USD 53,714.00 | USD -15,791.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 77.20% | USD 269.21 | USD 51,957.70 | USD -15,800.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 186 | 79.57% | USD 247.43 | USD 46,022.00 | USD -34,041.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 186 | 79.57% | USD 238.33 | USD 44,329.40 | USD -34,050.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 186 | 79.57% | USD 212.43 | USD 39,512.00 | USD -34,076.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 186 | 79.57% | USD 203.33 | USD 37,819.40 | USD -34,085.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 186 | 79.57% | USD 177.43 | USD 33,002.00 | USD -34,111.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 186 | 79.57% | USD 168.33 | USD 31,309.40 | USD -34,120.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 186 | 79.57% | USD 107.43 | USD 19,982.00 | USD -34,181.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 186 | 79.57% | USD 98.33 | USD 18,289.40 | USD -34,190.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 190 | 80.00% | USD 275.52 | USD 52,348.00 | USD -34,041.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 190 | 80.00% | USD 266.42 | USD 50,619.00 | USD -34,050.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 190 | 80.00% | USD 240.52 | USD 45,698.00 | USD -34,076.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 190 | 80.00% | USD 231.42 | USD 43,969.00 | USD -34,085.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 190 | 80.00% | USD 205.52 | USD 39,048.00 | USD -34,111.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 190 | 80.00% | USD 196.42 | USD 37,319.00 | USD -34,120.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 190 | 80.00% | USD 135.52 | USD 25,748.00 | USD -34,181.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 190 | 80.00% | USD 126.42 | USD 24,019.00 | USD -34,190.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 79.79% | USD 356.21 | USD 68,749.00 | USD -34,041.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 79.27% | USD 347.11 | USD 66,992.70 | USD -34,050.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 78.24% | USD 321.21 | USD 61,994.00 | USD -34,076.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 77.72% | USD 312.11 | USD 60,237.70 | USD -34,085.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 77.72% | USD 286.21 | USD 55,239.00 | USD -34,111.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 77.20% | USD 277.11 | USD 53,482.70 | USD -34,120.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 76.68% | USD 216.21 | USD 41,729.00 | USD -34,181.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 76.17% | USD 207.11 | USD 39,972.70 | USD -34,190.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 20 | 55.00% | USD -1,549.40 | USD -30,988.00 | USD -29,527.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 20 | 55.00% | USD -1,558.50 | USD -31,170.00 | USD -29,536.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 20 | 55.00% | USD -1,584.40 | USD -31,688.00 | USD -29,562.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 20 | 55.00% | USD -1,593.50 | USD -31,870.00 | USD -29,571.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 20 | 55.00% | USD -1,619.40 | USD -32,388.00 | USD -29,597.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 20 | 55.00% | USD -1,628.50 | USD -32,570.00 | USD -29,606.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 20 | 55.00% | USD -1,689.40 | USD -33,788.00 | USD -29,667.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 20 | 55.00% | USD -1,698.50 | USD -33,970.00 | USD -29,676.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 183 | 81.97% | USD 304.11 | USD 55,653.00 | USD -32,682.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 183 | 81.97% | USD 295.01 | USD 53,987.70 | USD -32,691.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 183 | 81.97% | USD 269.11 | USD 49,248.00 | USD -32,717.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 183 | 81.97% | USD 260.01 | USD 47,582.70 | USD -32,726.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 183 | 81.42% | USD 234.11 | USD 42,843.00 | USD -32,752.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 183 | 81.42% | USD 225.01 | USD 41,177.70 | USD -32,761.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 183 | 81.42% | USD 164.11 | USD 30,033.00 | USD -32,822.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 183 | 81.42% | USD 155.01 | USD 28,367.70 | USD -32,831.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 79.79% | USD 356.21 | USD 68,749.00 | USD -34,041.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 79.27% | USD 347.11 | USD 66,992.70 | USD -34,050.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 78.24% | USD 321.21 | USD 61,994.00 | USD -34,076.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 77.72% | USD 312.11 | USD 60,237.70 | USD -34,085.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 77.72% | USD 286.21 | USD 55,239.00 | USD -34,111.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 77.20% | USD 277.11 | USD 53,482.70 | USD -34,120.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 76.68% | USD 216.21 | USD 41,729.00 | USD -34,181.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 76.17% | USD 207.11 | USD 39,972.70 | USD -34,190.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/194 (0) | 27.84% (22.01–34.53%) | USD -42.14 | USD -8,175.40 | USD -1,019.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/194 (0) | 68.04% (61.18–74.20%) | USD -34.70 | USD -6,731.40 | USD -18,989.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/194 (0) | 25.77% (20.13–32.36%) | USD -260.29 | USD -50,496.40 | USD -4,225.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/194 (0) | 27.84% (22.01–34.53%) | USD -210.71 | USD -40,877.00 | USD -5,098.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/194 (0) | 27.84% (22.01–34.53%) | USD -42.14 | USD -8,175.40 | USD -1,019.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/194 (0) | 68.04% (61.18–74.20%) | USD -34.70 | USD -6,731.40 | USD -18,989.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/194 (0) | 25.77% (20.13–32.36%) | USD -260.29 | USD -50,496.40 | USD -4,225.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/194 (0) | 27.84% (22.01–34.53%) | USD -210.71 | USD -40,877.00 | USD -5,098.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 27.84% (22.01–34.53%) | USD -42.14 | USD -8,175.40 | USD -1,019.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 68.04% (61.18–74.20%) | USD -34.70 | USD -6,731.40 | USD -18,989.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 25.77% (20.13–32.36%) | USD -260.29 | USD -50,496.40 | USD -4,225.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 27.84% (22.01–34.53%) | USD -210.71 | USD -40,877.00 | USD -5,098.00 |
| HOLD_10_SESSIONS | 1 : 1 | 193/194 (1) | 32.64% (26.42–39.54%) | USD -36.53 | USD -7,049.80 | USD -1,653.60 |
| HOLD_10_SESSIONS | 1 : 6 | 193/194 (1) | 79.27% (73.01–84.39%) | USD 330.50 | USD 63,785.70 | USD -15,730.10 |
| HOLD_10_SESSIONS | 6 : 1 | 193/194 (1) | 19.69% (14.69–25.87%) | USD -586.19 | USD -113,134.30 | USD -3,807.10 |
| HOLD_10_SESSIONS | 5 : 5 | 193/194 (1) | 32.64% (26.42–39.54%) | USD -182.64 | USD -35,249.00 | USD -8,268.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 193/194 (1) | 32.64% (26.42–39.54%) | USD -36.53 | USD -7,049.80 | USD -1,653.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 193/194 (1) | 79.27% (73.01–84.39%) | USD 330.50 | USD 63,785.70 | USD -15,730.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 193/194 (1) | 19.69% (14.69–25.87%) | USD -586.19 | USD -113,134.30 | USD -3,807.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 193/194 (1) | 32.64% (26.42–39.54%) | USD -182.64 | USD -35,249.00 | USD -8,268.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 32.64% (26.42–39.54%) | USD -28.25 | USD -5,452.80 | USD -1,653.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 77.72% (71.34–83.02%) | USD 339.21 | USD 65,467.70 | USD -15,730.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 22.28% (16.98–28.66%) | USD -536.98 | USD -103,637.30 | USD -3,807.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 32.64% (26.42–39.54%) | USD -141.26 | USD -27,264.00 | USD -8,268.00 |
| HOLD_15_SESSIONS | 1 : 1 | 186/194 (8) | 29.57% (23.48–36.49%) | USD -52.97 | USD -9,851.60 | USD -3,328.60 |
| HOLD_15_SESSIONS | 1 : 6 | 186/194 (8) | 79.57% (73.20–84.74%) | USD 168.33 | USD 31,309.40 | USD -34,120.10 |
| HOLD_15_SESSIONS | 6 : 1 | 186/194 (8) | 15.59% (11.08–21.49%) | USD -539.09 | USD -100,270.60 | USD -4,682.10 |
| HOLD_15_SESSIONS | 5 : 5 | 186/194 (8) | 29.57% (23.48–36.49%) | USD -264.83 | USD -49,258.00 | USD -16,643.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 190/194 (4) | 30.53% (24.42–37.41%) | USD -49.48 | USD -9,401.00 | USD -3,328.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 190/194 (4) | 80.00% (73.74–85.07%) | USD 196.42 | USD 37,319.00 | USD -34,120.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 190/194 (4) | 16.32% (11.74–22.23%) | USD -542.77 | USD -103,126.00 | USD -4,682.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 190/194 (4) | 30.53% (24.42–37.41%) | USD -247.39 | USD -47,005.00 | USD -16,643.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 34.72% (28.36–41.67%) | USD -37.32 | USD -7,202.80 | USD -3,328.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 77.20% (70.79–82.56%) | USD 277.11 | USD 53,482.70 | USD -34,120.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 22.28% (16.98–28.66%) | USD -538.35 | USD -103,902.30 | USD -4,182.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 34.72% (28.36–41.67%) | USD -186.60 | USD -36,014.00 | USD -16,643.00 |
| HOLD_20_SESSIONS | 1 : 1 | 20/194 (174) | 50.00% (29.93–70.07%) | USD -128.75 | USD -2,575.00 | USD -3,124.60 |
| HOLD_20_SESSIONS | 1 : 6 | 20/194 (174) | 55.00% (34.21–74.18%) | USD -1,628.50 | USD -32,570.00 | USD -29,606.10 |
| HOLD_20_SESSIONS | 6 : 1 | 20/194 (174) | 45.00% (25.82–65.79%) | USD 727.25 | USD 14,545.00 | USD -5,671.10 |
| HOLD_20_SESSIONS | 5 : 5 | 20/194 (174) | 50.00% (29.93–70.07%) | USD -643.75 | USD -12,875.00 | USD -15,623.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 183/194 (11) | 29.51% (23.38–36.48%) | USD -51.65 | USD -9,452.80 | USD -3,739.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 183/194 (11) | 81.42% (75.16–86.39%) | USD 225.01 | USD 41,177.70 | USD -32,761.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 183/194 (11) | 15.30% (10.80–21.22%) | USD -586.60 | USD -107,347.30 | USD -5,630.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 183/194 (11) | 29.51% (23.38–36.48%) | USD -258.27 | USD -47,264.00 | USD -18,698.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 34.72% (28.36–41.67%) | USD -37.32 | USD -7,202.80 | USD -3,328.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 77.20% (70.79–82.56%) | USD 277.11 | USD 53,482.70 | USD -34,120.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 22.28% (16.98–28.66%) | USD -538.35 | USD -103,902.30 | USD -4,182.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 34.72% (28.36–41.67%) | USD -186.60 | USD -36,014.00 | USD -16,643.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/194 | 0.00% | USD -206,775.19 | USD -336,635.55 |
| -75% | 0/194 | 0.00% | USD -152,843.94 | USD -250,024.30 |
| -50% | 0/194 | 0.00% | USD -98,912.69 | USD -163,413.05 |
| -40% | 0/194 | 0.00% | USD -77,340.19 | USD -128,768.55 |
| -30% | 0/194 | 0.00% | USD -55,767.69 | USD -94,124.05 |
| -25% | 0/194 | 0.00% | USD -44,981.44 | USD -76,801.80 |
| -20% | 0/194 | 0.00% | USD -34,195.19 | USD -59,479.55 |
| -15% | 1/194 | 0.52% | USD -23,427.99 | USD -42,157.30 |
| -10% | 4/194 | 2.06% | USD -12,698.47 | USD -24,835.05 |
| -5% | 51/194 | 26.29% | USD -2,316.21 | USD -10,016.55 |
| 0% | 194/194 | 100.00% | USD 1,664.13 | USD 388.45 |
| 5% | 194/194 | 100.00% | USD 1,663.29 | USD 388.45 |
| 10% | 194/194 | 100.00% | USD 1,663.29 | USD 388.45 |
| 20% | 194/194 | 100.00% | USD 1,663.29 | USD 388.45 |

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