# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 288.19 / USD 1,541.67; mean absolute mismatch USD 1,253.48; mean match score 18.76%.
- Actual selected contract ratios: {'1:6': 109}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 109; entered cohorts: 109; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 109/109 | 58/51/0 | 53.21% (43.89–62.31%) | USD -197.42 | USD 19.90 | USD -21,518.90 | USD -4,319.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 109/109 | 58/51/0 | 53.21% (43.89–62.31%) | USD -197.42 | USD 19.90 | USD -21,518.90 | USD -4,319.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 109/109 | 58/51/0 | 53.21% (43.89–62.31%) | USD -197.42 | USD 19.90 | USD -21,518.90 | USD -4,319.10 | 0 |
| HOLD_10_SESSIONS | 109/109 | 54/55/0 | 49.54% (40.33–58.78%) | USD -205.11 | USD -10.10 | USD -22,356.90 | USD -5,982.10 | 0 |
| HOLD_10_OR_DTE_LE_7 | 109/109 | 54/55/0 | 49.54% (40.33–58.78%) | USD -205.11 | USD -10.10 | USD -22,356.90 | USD -5,982.10 | 0 |
| HOLD_10_OR_DTE_LE_14 | 109/109 | 54/55/0 | 49.54% (40.33–58.78%) | USD -205.11 | USD -10.10 | USD -22,356.90 | USD -5,982.10 | 0 |
| HOLD_15_SESSIONS | 108/109 | 55/53/0 | 50.93% (41.63–60.16%) | USD -470.34 | USD 52.40 | USD -50,796.80 | USD -9,233.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 108/109 | 55/53/0 | 50.93% (41.63–60.16%) | USD -470.34 | USD 52.40 | USD -50,796.80 | USD -9,233.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 108/109 | 55/53/0 | 50.93% (41.63–60.16%) | USD -470.34 | USD 52.40 | USD -50,796.80 | USD -9,233.10 | 1 |
| HOLD_20_SESSIONS | 107/109 | 59/48/0 | 55.14% (45.70–64.22%) | USD -357.00 | USD 160.90 | USD -38,198.70 | USD -8,416.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 107/109 | 59/48/0 | 55.14% (45.70–64.22%) | USD -357.00 | USD 160.90 | USD -38,198.70 | USD -8,416.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 107/109 | 59/48/0 | 55.14% (45.70–64.22%) | USD -357.00 | USD 160.90 | USD -38,198.70 | USD -8,416.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 13.90 | USD -132.22 |
| HOLD_5_OR_DTE_LE_7 | USD 13.90 | USD -132.22 |
| HOLD_5_OR_DTE_LE_14 | USD 13.90 | USD -132.22 |
| HOLD_10_SESSIONS | USD 24.16 | USD -150.17 |
| HOLD_10_OR_DTE_LE_7 | USD 24.16 | USD -150.17 |
| HOLD_10_OR_DTE_LE_14 | USD 24.16 | USD -150.17 |
| HOLD_15_SESSIONS | USD 74.54 | USD -465.78 |
| HOLD_15_OR_DTE_LE_7 | USD 74.54 | USD -465.78 |
| HOLD_15_OR_DTE_LE_14 | USD 74.54 | USD -465.78 |
| HOLD_20_SESSIONS | USD 33.21 | USD -311.10 |
| HOLD_20_OR_DTE_LE_7 | USD 33.21 | USD -311.10 |
| HOLD_20_OR_DTE_LE_14 | USD 33.21 | USD -311.10 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 109 | 55.96% | USD -118.32 | USD -12,897.00 | USD -4,240.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 109 | 55.96% | USD -127.42 | USD -13,888.90 | USD -4,249.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 109 | 55.96% | USD -153.32 | USD -16,712.00 | USD -4,275.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 109 | 55.96% | USD -162.42 | USD -17,703.90 | USD -4,284.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 109 | 53.21% | USD -188.32 | USD -20,527.00 | USD -4,310.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 109 | 53.21% | USD -197.42 | USD -21,518.90 | USD -4,319.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 109 | 43.12% | USD -258.32 | USD -28,157.00 | USD -4,380.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 109 | 43.12% | USD -267.42 | USD -29,148.90 | USD -4,389.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 109 | 55.96% | USD -118.32 | USD -12,897.00 | USD -4,240.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 109 | 55.96% | USD -127.42 | USD -13,888.90 | USD -4,249.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 109 | 55.96% | USD -153.32 | USD -16,712.00 | USD -4,275.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 109 | 55.96% | USD -162.42 | USD -17,703.90 | USD -4,284.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 109 | 53.21% | USD -188.32 | USD -20,527.00 | USD -4,310.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 109 | 53.21% | USD -197.42 | USD -21,518.90 | USD -4,319.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 109 | 43.12% | USD -258.32 | USD -28,157.00 | USD -4,380.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 109 | 43.12% | USD -267.42 | USD -29,148.90 | USD -4,389.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 109 | 55.96% | USD -118.32 | USD -12,897.00 | USD -4,240.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 109 | 55.96% | USD -127.42 | USD -13,888.90 | USD -4,249.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 109 | 55.96% | USD -153.32 | USD -16,712.00 | USD -4,275.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 109 | 55.96% | USD -162.42 | USD -17,703.90 | USD -4,284.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 109 | 53.21% | USD -188.32 | USD -20,527.00 | USD -4,310.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 109 | 53.21% | USD -197.42 | USD -21,518.90 | USD -4,319.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 109 | 43.12% | USD -258.32 | USD -28,157.00 | USD -4,380.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 109 | 43.12% | USD -267.42 | USD -29,148.90 | USD -4,389.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 109 | 54.13% | USD -126.01 | USD -13,735.00 | USD -5,903.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 109 | 53.21% | USD -135.11 | USD -14,726.90 | USD -5,912.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 109 | 51.38% | USD -161.01 | USD -17,550.00 | USD -5,938.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 109 | 50.46% | USD -170.11 | USD -18,541.90 | USD -5,947.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 109 | 49.54% | USD -196.01 | USD -21,365.00 | USD -5,973.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 109 | 49.54% | USD -205.11 | USD -22,356.90 | USD -5,982.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 109 | 47.71% | USD -266.01 | USD -28,995.00 | USD -6,043.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 109 | 47.71% | USD -275.11 | USD -29,986.90 | USD -6,052.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 109 | 54.13% | USD -126.01 | USD -13,735.00 | USD -5,903.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 109 | 53.21% | USD -135.11 | USD -14,726.90 | USD -5,912.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 109 | 51.38% | USD -161.01 | USD -17,550.00 | USD -5,938.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 109 | 50.46% | USD -170.11 | USD -18,541.90 | USD -5,947.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 109 | 49.54% | USD -196.01 | USD -21,365.00 | USD -5,973.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 109 | 49.54% | USD -205.11 | USD -22,356.90 | USD -5,982.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 109 | 47.71% | USD -266.01 | USD -28,995.00 | USD -6,043.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 109 | 47.71% | USD -275.11 | USD -29,986.90 | USD -6,052.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 109 | 54.13% | USD -126.01 | USD -13,735.00 | USD -5,903.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 109 | 53.21% | USD -135.11 | USD -14,726.90 | USD -5,912.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 109 | 51.38% | USD -161.01 | USD -17,550.00 | USD -5,938.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 109 | 50.46% | USD -170.11 | USD -18,541.90 | USD -5,947.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 109 | 49.54% | USD -196.01 | USD -21,365.00 | USD -5,973.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 109 | 49.54% | USD -205.11 | USD -22,356.90 | USD -5,982.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 109 | 47.71% | USD -266.01 | USD -28,995.00 | USD -6,043.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 109 | 47.71% | USD -275.11 | USD -29,986.90 | USD -6,052.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 108 | 53.70% | USD -391.24 | USD -42,254.00 | USD -9,154.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 108 | 53.70% | USD -400.34 | USD -43,236.80 | USD -9,163.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 108 | 51.85% | USD -426.24 | USD -46,034.00 | USD -9,189.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 108 | 50.93% | USD -435.34 | USD -47,016.80 | USD -9,198.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 108 | 50.93% | USD -461.24 | USD -49,814.00 | USD -9,224.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 108 | 50.93% | USD -470.34 | USD -50,796.80 | USD -9,233.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 108 | 50.00% | USD -531.24 | USD -57,374.00 | USD -9,294.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 108 | 49.07% | USD -540.34 | USD -58,356.80 | USD -9,303.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 108 | 53.70% | USD -391.24 | USD -42,254.00 | USD -9,154.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 108 | 53.70% | USD -400.34 | USD -43,236.80 | USD -9,163.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 108 | 51.85% | USD -426.24 | USD -46,034.00 | USD -9,189.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 108 | 50.93% | USD -435.34 | USD -47,016.80 | USD -9,198.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 108 | 50.93% | USD -461.24 | USD -49,814.00 | USD -9,224.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 108 | 50.93% | USD -470.34 | USD -50,796.80 | USD -9,233.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 108 | 50.00% | USD -531.24 | USD -57,374.00 | USD -9,294.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 108 | 49.07% | USD -540.34 | USD -58,356.80 | USD -9,303.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 108 | 53.70% | USD -391.24 | USD -42,254.00 | USD -9,154.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 108 | 53.70% | USD -400.34 | USD -43,236.80 | USD -9,163.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 108 | 51.85% | USD -426.24 | USD -46,034.00 | USD -9,189.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 108 | 50.93% | USD -435.34 | USD -47,016.80 | USD -9,198.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 108 | 50.93% | USD -461.24 | USD -49,814.00 | USD -9,224.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 108 | 50.93% | USD -470.34 | USD -50,796.80 | USD -9,233.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 108 | 50.00% | USD -531.24 | USD -57,374.00 | USD -9,294.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 108 | 49.07% | USD -540.34 | USD -58,356.80 | USD -9,303.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 107 | 55.14% | USD -277.90 | USD -29,735.00 | USD -8,337.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 107 | 55.14% | USD -287.00 | USD -30,708.70 | USD -8,346.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 107 | 55.14% | USD -312.90 | USD -33,480.00 | USD -8,372.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 107 | 55.14% | USD -322.00 | USD -34,453.70 | USD -8,381.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 107 | 55.14% | USD -347.90 | USD -37,225.00 | USD -8,407.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 107 | 55.14% | USD -357.00 | USD -38,198.70 | USD -8,416.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 107 | 52.34% | USD -417.90 | USD -44,715.00 | USD -8,477.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 107 | 52.34% | USD -427.00 | USD -45,688.70 | USD -8,486.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 107 | 55.14% | USD -277.90 | USD -29,735.00 | USD -8,337.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 107 | 55.14% | USD -287.00 | USD -30,708.70 | USD -8,346.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 107 | 55.14% | USD -312.90 | USD -33,480.00 | USD -8,372.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 107 | 55.14% | USD -322.00 | USD -34,453.70 | USD -8,381.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 107 | 55.14% | USD -347.90 | USD -37,225.00 | USD -8,407.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 107 | 55.14% | USD -357.00 | USD -38,198.70 | USD -8,416.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 107 | 52.34% | USD -417.90 | USD -44,715.00 | USD -8,477.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 107 | 52.34% | USD -427.00 | USD -45,688.70 | USD -8,486.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 107 | 55.14% | USD -277.90 | USD -29,735.00 | USD -8,337.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 107 | 55.14% | USD -287.00 | USD -30,708.70 | USD -8,346.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 107 | 55.14% | USD -312.90 | USD -33,480.00 | USD -8,372.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 107 | 55.14% | USD -322.00 | USD -34,453.70 | USD -8,381.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 107 | 55.14% | USD -347.90 | USD -37,225.00 | USD -8,407.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 107 | 55.14% | USD -357.00 | USD -38,198.70 | USD -8,416.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 107 | 52.34% | USD -417.90 | USD -44,715.00 | USD -8,477.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 107 | 52.34% | USD -427.00 | USD -45,688.70 | USD -8,486.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 109/109 (0) | 26.61% (19.21–35.59%) | USD -30.74 | USD -3,350.40 | USD -361.60 |
| HOLD_5_SESSIONS | 1 : 6 | 109/109 (0) | 53.21% (43.89–62.31%) | USD -197.42 | USD -21,518.90 | USD -4,319.10 |
| HOLD_5_SESSIONS | 6 : 1 | 109/109 (0) | 39.45% (30.78–48.83%) | USD -17.74 | USD -1,933.90 | USD -2,278.10 |
| HOLD_5_SESSIONS | 5 : 5 | 109/109 (0) | 26.61% (19.21–35.59%) | USD -153.69 | USD -16,752.00 | USD -1,808.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 109/109 (0) | 26.61% (19.21–35.59%) | USD -30.74 | USD -3,350.40 | USD -361.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 109/109 (0) | 53.21% (43.89–62.31%) | USD -197.42 | USD -21,518.90 | USD -4,319.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 109/109 (0) | 39.45% (30.78–48.83%) | USD -17.74 | USD -1,933.90 | USD -2,278.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 109/109 (0) | 26.61% (19.21–35.59%) | USD -153.69 | USD -16,752.00 | USD -1,808.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 109/109 (0) | 26.61% (19.21–35.59%) | USD -30.74 | USD -3,350.40 | USD -361.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 109/109 (0) | 53.21% (43.89–62.31%) | USD -197.42 | USD -21,518.90 | USD -4,319.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 109/109 (0) | 39.45% (30.78–48.83%) | USD -17.74 | USD -1,933.90 | USD -2,278.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 109/109 (0) | 26.61% (19.21–35.59%) | USD -153.69 | USD -16,752.00 | USD -1,808.00 |
| HOLD_10_SESSIONS | 1 : 1 | 109/109 (0) | 30.28% (22.44–39.45%) | USD -23.47 | USD -2,558.40 | USD -549.60 |
| HOLD_10_SESSIONS | 1 : 6 | 109/109 (0) | 49.54% (40.33–58.78%) | USD -205.11 | USD -22,356.90 | USD -5,982.10 |
| HOLD_10_SESSIONS | 6 : 1 | 109/109 (0) | 36.70% (28.25–46.05%) | USD 40.81 | USD 4,448.10 | USD -2,500.10 |
| HOLD_10_SESSIONS | 5 : 5 | 109/109 (0) | 30.28% (22.44–39.45%) | USD -117.36 | USD -12,792.00 | USD -2,748.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 109/109 (0) | 30.28% (22.44–39.45%) | USD -23.47 | USD -2,558.40 | USD -549.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 109/109 (0) | 49.54% (40.33–58.78%) | USD -205.11 | USD -22,356.90 | USD -5,982.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 109/109 (0) | 36.70% (28.25–46.05%) | USD 40.81 | USD 4,448.10 | USD -2,500.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 109/109 (0) | 30.28% (22.44–39.45%) | USD -117.36 | USD -12,792.00 | USD -2,748.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 109/109 (0) | 30.28% (22.44–39.45%) | USD -23.47 | USD -2,558.40 | USD -549.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 109/109 (0) | 49.54% (40.33–58.78%) | USD -205.11 | USD -22,356.90 | USD -5,982.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 109/109 (0) | 36.70% (28.25–46.05%) | USD 40.81 | USD 4,448.10 | USD -2,500.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 109/109 (0) | 30.28% (22.44–39.45%) | USD -117.36 | USD -12,792.00 | USD -2,748.00 |
| HOLD_15_SESSIONS | 1 : 1 | 108/109 (1) | 29.63% (21.84–38.82%) | USD -25.69 | USD -2,774.80 | USD -461.60 |
| HOLD_15_SESSIONS | 1 : 6 | 108/109 (1) | 50.93% (41.63–60.16%) | USD -470.34 | USD -50,796.80 | USD -9,233.10 |
| HOLD_15_SESSIONS | 6 : 1 | 108/109 (1) | 39.81% (31.09–49.24%) | USD 290.49 | USD 31,373.20 | USD -3,025.10 |
| HOLD_15_SESSIONS | 5 : 5 | 108/109 (1) | 29.63% (21.84–38.82%) | USD -128.46 | USD -13,874.00 | USD -2,308.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 108/109 (1) | 29.63% (21.84–38.82%) | USD -25.69 | USD -2,774.80 | USD -461.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 108/109 (1) | 50.93% (41.63–60.16%) | USD -470.34 | USD -50,796.80 | USD -9,233.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 108/109 (1) | 39.81% (31.09–49.24%) | USD 290.49 | USD 31,373.20 | USD -3,025.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 108/109 (1) | 29.63% (21.84–38.82%) | USD -128.46 | USD -13,874.00 | USD -2,308.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 108/109 (1) | 29.63% (21.84–38.82%) | USD -25.69 | USD -2,774.80 | USD -461.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 108/109 (1) | 50.93% (41.63–60.16%) | USD -470.34 | USD -50,796.80 | USD -9,233.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 108/109 (1) | 39.81% (31.09–49.24%) | USD 290.49 | USD 31,373.20 | USD -3,025.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 108/109 (1) | 29.63% (21.84–38.82%) | USD -128.46 | USD -13,874.00 | USD -2,308.00 |
| HOLD_20_SESSIONS | 1 : 1 | 107/109 (2) | 28.04% (20.40–37.20%) | USD -41.24 | USD -4,413.20 | USD -502.60 |
| HOLD_20_SESSIONS | 1 : 6 | 107/109 (2) | 55.14% (45.70–64.22%) | USD -357.00 | USD -38,198.70 | USD -8,416.10 |
| HOLD_20_SESSIONS | 6 : 1 | 107/109 (2) | 34.58% (26.24–43.98%) | USD 68.28 | USD 7,306.30 | USD -2,875.10 |
| HOLD_20_SESSIONS | 5 : 5 | 107/109 (2) | 28.04% (20.40–37.20%) | USD -206.22 | USD -22,066.00 | USD -2,513.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 107/109 (2) | 28.04% (20.40–37.20%) | USD -41.24 | USD -4,413.20 | USD -502.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 107/109 (2) | 55.14% (45.70–64.22%) | USD -357.00 | USD -38,198.70 | USD -8,416.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 107/109 (2) | 34.58% (26.24–43.98%) | USD 68.28 | USD 7,306.30 | USD -2,875.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 107/109 (2) | 28.04% (20.40–37.20%) | USD -206.22 | USD -22,066.00 | USD -2,513.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 107/109 (2) | 28.04% (20.40–37.20%) | USD -41.24 | USD -4,413.20 | USD -502.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 107/109 (2) | 55.14% (45.70–64.22%) | USD -357.00 | USD -38,198.70 | USD -8,416.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 107/109 (2) | 34.58% (26.24–43.98%) | USD 68.28 | USD 7,306.30 | USD -2,875.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 107/109 (2) | 28.04% (20.40–37.20%) | USD -206.22 | USD -22,066.00 | USD -2,513.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -75% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -50% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -40% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -30% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -25% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -20% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -15% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -10% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| -5% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| 0% | 109/109 | 100.00% | USD 1,213.93 | USD 303.45 |
| 5% | 64/109 | 58.72% | USD -55.71 | USD -3,898.25 |
| 10% | 3/109 | 2.75% | USD -10,064.98 | USD -18,713.25 |
| 20% | 1/109 | 0.92% | USD -32,028.35 | USD -52,670.55 |

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