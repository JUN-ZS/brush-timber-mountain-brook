# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 244.70 / USD 1,292.20; mean absolute mismatch USD 1,047.50; mean match score 19.40%.
- Actual selected contract ratios: {'1:6': 180}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 180; entered cohorts: 180; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 179/180 | 83/96/0 | 46.37% (39.22–53.67%) | USD -278.31 | USD -90.10 | USD -49,816.90 | USD -7,899.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 179/180 | 83/96/0 | 46.37% (39.22–53.67%) | USD -278.31 | USD -90.10 | USD -49,816.90 | USD -7,899.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 179/180 | 83/96/0 | 46.37% (39.22–53.67%) | USD -278.31 | USD -90.10 | USD -49,816.90 | USD -7,899.10 | 1 |
| HOLD_10_SESSIONS | 179/180 | 100/79/0 | 55.87% (48.54–62.94%) | USD -261.45 | USD 65.90 | USD -46,798.90 | USD -5,360.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 179/180 | 100/79/0 | 55.87% (48.54–62.94%) | USD -261.45 | USD 65.90 | USD -46,798.90 | USD -5,360.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 179/180 | 100/79/0 | 55.87% (48.54–62.94%) | USD -261.45 | USD 65.90 | USD -46,798.90 | USD -5,360.10 | 1 |
| HOLD_15_SESSIONS | 176/180 | 100/76/0 | 56.82% (49.43–63.91%) | USD -374.86 | USD 101.90 | USD -65,974.60 | USD -14,156.10 | 4 |
| HOLD_15_OR_DTE_LE_7 | 176/180 | 100/76/0 | 56.82% (49.43–63.91%) | USD -374.86 | USD 101.90 | USD -65,974.60 | USD -14,156.10 | 4 |
| HOLD_15_OR_DTE_LE_14 | 176/180 | 100/76/0 | 56.82% (49.43–63.91%) | USD -374.86 | USD 101.90 | USD -65,974.60 | USD -14,156.10 | 4 |
| HOLD_20_SESSIONS | 168/180 | 98/70/0 | 58.33% (50.77–65.52%) | USD -372.29 | USD 247.40 | USD -62,544.80 | USD -11,242.10 | 12 |
| HOLD_20_OR_DTE_LE_7 | 168/180 | 98/70/0 | 58.33% (50.77–65.52%) | USD -372.29 | USD 247.40 | USD -62,544.80 | USD -11,242.10 | 12 |
| HOLD_20_OR_DTE_LE_14 | 171/180 | 99/72/0 | 57.89% (50.40–65.04%) | USD -378.95 | USD 261.90 | USD -64,800.10 | USD -17,258.10 | 9 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 36.84 | USD -236.04 |
| HOLD_5_OR_DTE_LE_7 | USD 36.84 | USD -236.04 |
| HOLD_5_OR_DTE_LE_14 | USD 36.84 | USD -236.04 |
| HOLD_10_SESSIONS | USD 33.35 | USD -215.70 |
| HOLD_10_OR_DTE_LE_7 | USD 33.35 | USD -215.70 |
| HOLD_10_OR_DTE_LE_14 | USD 33.35 | USD -215.70 |
| HOLD_15_SESSIONS | USD 72.36 | USD -368.11 |
| HOLD_15_OR_DTE_LE_7 | USD 72.36 | USD -368.11 |
| HOLD_15_OR_DTE_LE_14 | USD 72.36 | USD -368.11 |
| HOLD_20_SESSIONS | USD 83.77 | USD -376.96 |
| HOLD_20_OR_DTE_LE_7 | USD 83.77 | USD -376.96 |
| HOLD_20_OR_DTE_LE_14 | USD 84.08 | USD -383.93 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 179 | 49.72% | USD -199.21 | USD -35,658.00 | USD -7,820.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 179 | 48.60% | USD -208.31 | USD -37,286.90 | USD -7,829.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 179 | 48.60% | USD -234.21 | USD -41,923.00 | USD -7,855.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 179 | 48.04% | USD -243.31 | USD -43,551.90 | USD -7,864.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 179 | 46.37% | USD -269.21 | USD -48,188.00 | USD -7,890.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 179 | 46.37% | USD -278.31 | USD -49,816.90 | USD -7,899.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 179 | 42.46% | USD -339.21 | USD -60,718.00 | USD -7,960.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 179 | 42.46% | USD -348.31 | USD -62,346.90 | USD -7,969.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 179 | 49.72% | USD -199.21 | USD -35,658.00 | USD -7,820.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 179 | 48.60% | USD -208.31 | USD -37,286.90 | USD -7,829.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 179 | 48.60% | USD -234.21 | USD -41,923.00 | USD -7,855.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 179 | 48.04% | USD -243.31 | USD -43,551.90 | USD -7,864.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 179 | 46.37% | USD -269.21 | USD -48,188.00 | USD -7,890.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 179 | 46.37% | USD -278.31 | USD -49,816.90 | USD -7,899.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 179 | 42.46% | USD -339.21 | USD -60,718.00 | USD -7,960.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 179 | 42.46% | USD -348.31 | USD -62,346.90 | USD -7,969.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 179 | 49.72% | USD -199.21 | USD -35,658.00 | USD -7,820.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 179 | 48.60% | USD -208.31 | USD -37,286.90 | USD -7,829.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 179 | 48.60% | USD -234.21 | USD -41,923.00 | USD -7,855.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 179 | 48.04% | USD -243.31 | USD -43,551.90 | USD -7,864.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 179 | 46.37% | USD -269.21 | USD -48,188.00 | USD -7,890.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 179 | 46.37% | USD -278.31 | USD -49,816.90 | USD -7,899.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 179 | 42.46% | USD -339.21 | USD -60,718.00 | USD -7,960.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 179 | 42.46% | USD -348.31 | USD -62,346.90 | USD -7,969.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 179 | 60.34% | USD -182.35 | USD -32,640.00 | USD -5,281.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 179 | 60.34% | USD -191.45 | USD -34,268.90 | USD -5,290.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 179 | 58.66% | USD -217.35 | USD -38,905.00 | USD -5,316.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 179 | 58.66% | USD -226.45 | USD -40,533.90 | USD -5,325.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 179 | 55.87% | USD -252.35 | USD -45,170.00 | USD -5,351.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 179 | 55.87% | USD -261.45 | USD -46,798.90 | USD -5,360.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 179 | 50.28% | USD -322.35 | USD -57,700.00 | USD -5,421.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 179 | 49.72% | USD -331.45 | USD -59,328.90 | USD -5,430.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 179 | 60.34% | USD -182.35 | USD -32,640.00 | USD -5,281.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 179 | 60.34% | USD -191.45 | USD -34,268.90 | USD -5,290.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 179 | 58.66% | USD -217.35 | USD -38,905.00 | USD -5,316.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 179 | 58.66% | USD -226.45 | USD -40,533.90 | USD -5,325.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 179 | 55.87% | USD -252.35 | USD -45,170.00 | USD -5,351.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 179 | 55.87% | USD -261.45 | USD -46,798.90 | USD -5,360.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 179 | 50.28% | USD -322.35 | USD -57,700.00 | USD -5,421.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 179 | 49.72% | USD -331.45 | USD -59,328.90 | USD -5,430.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 179 | 60.34% | USD -182.35 | USD -32,640.00 | USD -5,281.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 179 | 60.34% | USD -191.45 | USD -34,268.90 | USD -5,290.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 179 | 58.66% | USD -217.35 | USD -38,905.00 | USD -5,316.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 179 | 58.66% | USD -226.45 | USD -40,533.90 | USD -5,325.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 179 | 55.87% | USD -252.35 | USD -45,170.00 | USD -5,351.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 179 | 55.87% | USD -261.45 | USD -46,798.90 | USD -5,360.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 179 | 50.28% | USD -322.35 | USD -57,700.00 | USD -5,421.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 179 | 49.72% | USD -331.45 | USD -59,328.90 | USD -5,430.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 176 | 58.52% | USD -295.76 | USD -52,053.00 | USD -14,077.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 176 | 58.52% | USD -304.86 | USD -53,654.60 | USD -14,086.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 176 | 57.39% | USD -330.76 | USD -58,213.00 | USD -14,112.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 176 | 57.39% | USD -339.86 | USD -59,814.60 | USD -14,121.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 176 | 56.82% | USD -365.76 | USD -64,373.00 | USD -14,147.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 176 | 56.82% | USD -374.86 | USD -65,974.60 | USD -14,156.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 176 | 52.27% | USD -435.76 | USD -76,693.00 | USD -14,217.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 176 | 51.14% | USD -444.86 | USD -78,294.60 | USD -14,226.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 176 | 58.52% | USD -295.76 | USD -52,053.00 | USD -14,077.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 176 | 58.52% | USD -304.86 | USD -53,654.60 | USD -14,086.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 176 | 57.39% | USD -330.76 | USD -58,213.00 | USD -14,112.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 176 | 57.39% | USD -339.86 | USD -59,814.60 | USD -14,121.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 176 | 56.82% | USD -365.76 | USD -64,373.00 | USD -14,147.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 176 | 56.82% | USD -374.86 | USD -65,974.60 | USD -14,156.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 176 | 52.27% | USD -435.76 | USD -76,693.00 | USD -14,217.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 176 | 51.14% | USD -444.86 | USD -78,294.60 | USD -14,226.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 176 | 58.52% | USD -295.76 | USD -52,053.00 | USD -14,077.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 176 | 58.52% | USD -304.86 | USD -53,654.60 | USD -14,086.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 176 | 57.39% | USD -330.76 | USD -58,213.00 | USD -14,112.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 176 | 57.39% | USD -339.86 | USD -59,814.60 | USD -14,121.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 176 | 56.82% | USD -365.76 | USD -64,373.00 | USD -14,147.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 176 | 56.82% | USD -374.86 | USD -65,974.60 | USD -14,156.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 176 | 52.27% | USD -435.76 | USD -76,693.00 | USD -14,217.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 176 | 51.14% | USD -444.86 | USD -78,294.60 | USD -14,226.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 168 | 63.10% | USD -293.19 | USD -49,256.00 | USD -11,163.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 168 | 62.50% | USD -302.29 | USD -50,784.80 | USD -11,172.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 168 | 60.71% | USD -328.19 | USD -55,136.00 | USD -11,198.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 168 | 59.52% | USD -337.29 | USD -56,664.80 | USD -11,207.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 168 | 58.33% | USD -363.19 | USD -61,016.00 | USD -11,233.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 168 | 58.33% | USD -372.29 | USD -62,544.80 | USD -11,242.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 168 | 55.36% | USD -433.19 | USD -72,776.00 | USD -11,303.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 168 | 55.36% | USD -442.29 | USD -74,304.80 | USD -11,312.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 168 | 63.10% | USD -293.19 | USD -49,256.00 | USD -11,163.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 168 | 62.50% | USD -302.29 | USD -50,784.80 | USD -11,172.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 168 | 60.71% | USD -328.19 | USD -55,136.00 | USD -11,198.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 168 | 59.52% | USD -337.29 | USD -56,664.80 | USD -11,207.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 168 | 58.33% | USD -363.19 | USD -61,016.00 | USD -11,233.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 168 | 58.33% | USD -372.29 | USD -62,544.80 | USD -11,242.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 168 | 55.36% | USD -433.19 | USD -72,776.00 | USD -11,303.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 168 | 55.36% | USD -442.29 | USD -74,304.80 | USD -11,312.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 171 | 61.40% | USD -299.85 | USD -51,274.00 | USD -17,179.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 171 | 60.82% | USD -308.95 | USD -52,830.10 | USD -17,188.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 171 | 59.06% | USD -334.85 | USD -57,259.00 | USD -17,214.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 171 | 58.48% | USD -343.95 | USD -58,815.10 | USD -17,223.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 171 | 57.89% | USD -369.85 | USD -63,244.00 | USD -17,249.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 171 | 57.89% | USD -378.95 | USD -64,800.10 | USD -17,258.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 171 | 56.73% | USD -439.85 | USD -75,214.00 | USD -17,319.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 171 | 56.73% | USD -448.95 | USD -76,770.10 | USD -17,328.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 179/180 (1) | 30.17% (23.92–37.25%) | USD -25.10 | USD -4,493.40 | USD -494.60 |
| HOLD_5_SESSIONS | 1 : 6 | 179/180 (1) | 46.37% (39.22–53.67%) | USD -278.31 | USD -49,816.90 | USD -7,899.10 |
| HOLD_5_SESSIONS | 6 : 1 | 179/180 (1) | 40.22% (33.32–47.54%) | USD 102.59 | USD 18,363.10 | USD -2,892.10 |
| HOLD_5_SESSIONS | 5 : 5 | 179/180 (1) | 30.17% (23.92–37.25%) | USD -125.51 | USD -22,467.00 | USD -2,473.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 179/180 (1) | 30.17% (23.92–37.25%) | USD -25.10 | USD -4,493.40 | USD -494.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 179/180 (1) | 46.37% (39.22–53.67%) | USD -278.31 | USD -49,816.90 | USD -7,899.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 179/180 (1) | 40.22% (33.32–47.54%) | USD 102.59 | USD 18,363.10 | USD -2,892.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 179/180 (1) | 30.17% (23.92–37.25%) | USD -125.51 | USD -22,467.00 | USD -2,473.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 179/180 (1) | 30.17% (23.92–37.25%) | USD -25.10 | USD -4,493.40 | USD -494.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 179/180 (1) | 46.37% (39.22–53.67%) | USD -278.31 | USD -49,816.90 | USD -7,899.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 179/180 (1) | 40.22% (33.32–47.54%) | USD 102.59 | USD 18,363.10 | USD -2,892.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 179/180 (1) | 30.17% (23.92–37.25%) | USD -125.51 | USD -22,467.00 | USD -2,473.00 |
| HOLD_10_SESSIONS | 1 : 1 | 179/180 (1) | 36.31% (29.62–43.58%) | USD -25.20 | USD -4,510.40 | USD -482.60 |
| HOLD_10_SESSIONS | 1 : 6 | 179/180 (1) | 55.87% (48.54–62.94%) | USD -261.45 | USD -46,798.90 | USD -5,360.10 |
| HOLD_10_SESSIONS | 6 : 1 | 179/180 (1) | 37.99% (31.20–45.28%) | USD 85.06 | USD 15,226.10 | USD -3,131.10 |
| HOLD_10_SESSIONS | 5 : 5 | 179/180 (1) | 36.31% (29.62–43.58%) | USD -125.99 | USD -22,552.00 | USD -2,413.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 179/180 (1) | 36.31% (29.62–43.58%) | USD -25.20 | USD -4,510.40 | USD -482.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 179/180 (1) | 55.87% (48.54–62.94%) | USD -261.45 | USD -46,798.90 | USD -5,360.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 179/180 (1) | 37.99% (31.20–45.28%) | USD 85.06 | USD 15,226.10 | USD -3,131.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 179/180 (1) | 36.31% (29.62–43.58%) | USD -125.99 | USD -22,552.00 | USD -2,413.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 179/180 (1) | 36.31% (29.62–43.58%) | USD -25.20 | USD -4,510.40 | USD -482.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 179/180 (1) | 55.87% (48.54–62.94%) | USD -261.45 | USD -46,798.90 | USD -5,360.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 179/180 (1) | 37.99% (31.20–45.28%) | USD 85.06 | USD 15,226.10 | USD -3,131.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 179/180 (1) | 36.31% (29.62–43.58%) | USD -125.99 | USD -22,552.00 | USD -2,413.00 |
| HOLD_15_SESSIONS | 1 : 1 | 176/180 (4) | 35.80% (29.09–43.11%) | USD -11.59 | USD -2,040.60 | USD -1,463.60 |
| HOLD_15_SESSIONS | 1 : 6 | 176/180 (4) | 56.82% (49.43–63.91%) | USD -374.86 | USD -65,974.60 | USD -14,156.10 |
| HOLD_15_SESSIONS | 6 : 1 | 176/180 (4) | 35.80% (29.09–43.11%) | USD 293.70 | USD 51,690.40 | USD -3,447.10 |
| HOLD_15_SESSIONS | 5 : 5 | 176/180 (4) | 35.80% (29.09–43.11%) | USD -57.97 | USD -10,203.00 | USD -7,318.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 176/180 (4) | 35.80% (29.09–43.11%) | USD -11.59 | USD -2,040.60 | USD -1,463.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 176/180 (4) | 56.82% (49.43–63.91%) | USD -374.86 | USD -65,974.60 | USD -14,156.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 176/180 (4) | 35.80% (29.09–43.11%) | USD 293.70 | USD 51,690.40 | USD -3,447.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 176/180 (4) | 35.80% (29.09–43.11%) | USD -57.97 | USD -10,203.00 | USD -7,318.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 176/180 (4) | 35.80% (29.09–43.11%) | USD -11.59 | USD -2,040.60 | USD -1,463.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 176/180 (4) | 56.82% (49.43–63.91%) | USD -374.86 | USD -65,974.60 | USD -14,156.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 176/180 (4) | 35.80% (29.09–43.11%) | USD 293.70 | USD 51,690.40 | USD -3,447.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 176/180 (4) | 35.80% (29.09–43.11%) | USD -57.97 | USD -10,203.00 | USD -7,318.00 |
| HOLD_20_SESSIONS | 1 : 1 | 168/180 (12) | 34.52% (27.75–41.99%) | USD -1.65 | USD -277.80 | USD -539.60 |
| HOLD_20_SESSIONS | 1 : 6 | 168/180 (12) | 58.33% (50.77–65.52%) | USD -372.29 | USD -62,544.80 | USD -11,242.10 |
| HOLD_20_SESSIONS | 6 : 1 | 168/180 (12) | 35.71% (28.86–43.20%) | USD 360.72 | USD 60,600.20 | USD -3,769.10 |
| HOLD_20_SESSIONS | 5 : 5 | 168/180 (12) | 34.52% (27.75–41.99%) | USD -8.27 | USD -1,389.00 | USD -2,698.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 168/180 (12) | 34.52% (27.75–41.99%) | USD -1.65 | USD -277.80 | USD -539.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 168/180 (12) | 58.33% (50.77–65.52%) | USD -372.29 | USD -62,544.80 | USD -11,242.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 168/180 (12) | 35.71% (28.86–43.20%) | USD 360.72 | USD 60,600.20 | USD -3,769.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 168/180 (12) | 34.52% (27.75–41.99%) | USD -8.27 | USD -1,389.00 | USD -2,698.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 171/180 (9) | 34.50% (27.79–41.90%) | USD -2.51 | USD -428.60 | USD -539.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 171/180 (9) | 57.89% (50.40–65.04%) | USD -378.95 | USD -64,800.10 | USD -17,258.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 171/180 (9) | 34.50% (27.79–41.90%) | USD 361.40 | USD 61,799.90 | USD -3,787.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 171/180 (9) | 34.50% (27.79–41.90%) | USD -12.53 | USD -2,143.00 | USD -2,698.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -75% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -50% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -40% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -30% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -25% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -20% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -15% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -10% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| -5% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| 0% | 180/180 | 100.00% | USD 1,007.95 | USD 75.45 |
| 5% | 68/180 | 37.78% | USD -1,536.60 | USD -6,914.05 |
| 10% | 6/180 | 3.33% | USD -11,845.95 | USD -23,425.35 |
| 20% | 1/180 | 0.56% | USD -33,648.96 | USD -57,989.55 |

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