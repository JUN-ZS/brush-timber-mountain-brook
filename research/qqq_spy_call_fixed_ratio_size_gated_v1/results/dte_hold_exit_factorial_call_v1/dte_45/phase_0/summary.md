# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 232.61 / USD 1,259.80; mean absolute mismatch USD 1,027.19; mean match score 18.72%.
- Actual selected contract ratios: {'1:6': 180}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 180; entered cohorts: 180; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 180/180 | 99/81/0 | 55.00% (47.70–62.09%) | USD -117.61 | USD 49.90 | USD -21,169.00 | USD -3,533.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 180/180 | 99/81/0 | 55.00% (47.70–62.09%) | USD -117.61 | USD 49.90 | USD -21,169.00 | USD -3,533.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 180/180 | 99/81/0 | 55.00% (47.70–62.09%) | USD -117.61 | USD 49.90 | USD -21,169.00 | USD -3,533.10 | 0 |
| HOLD_10_SESSIONS | 179/180 | 101/78/0 | 56.42% (49.10–63.48%) | USD -136.24 | USD 94.90 | USD -24,386.90 | USD -6,646.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 179/180 | 101/78/0 | 56.42% (49.10–63.48%) | USD -136.24 | USD 94.90 | USD -24,386.90 | USD -6,646.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 179/180 | 101/78/0 | 56.42% (49.10–63.48%) | USD -136.24 | USD 94.90 | USD -24,386.90 | USD -6,646.10 | 1 |
| HOLD_15_SESSIONS | 176/180 | 99/77/0 | 56.25% (48.87–63.37%) | USD -226.90 | USD 220.90 | USD -39,933.60 | USD -6,424.10 | 4 |
| HOLD_15_OR_DTE_LE_7 | 176/180 | 99/77/0 | 56.25% (48.87–63.37%) | USD -226.90 | USD 220.90 | USD -39,933.60 | USD -6,424.10 | 4 |
| HOLD_15_OR_DTE_LE_14 | 176/180 | 99/77/0 | 56.25% (48.87–63.37%) | USD -226.90 | USD 220.90 | USD -39,933.60 | USD -6,424.10 | 4 |
| HOLD_20_SESSIONS | 172/180 | 106/66/0 | 61.63% (54.18–68.57%) | USD -265.58 | USD 268.90 | USD -45,679.20 | USD -11,658.10 | 8 |
| HOLD_20_OR_DTE_LE_7 | 172/180 | 106/66/0 | 61.63% (54.18–68.57%) | USD -265.58 | USD 268.90 | USD -45,679.20 | USD -11,658.10 | 8 |
| HOLD_20_OR_DTE_LE_14 | 172/180 | 102/70/0 | 59.30% (51.84–66.36%) | USD -315.61 | USD 314.90 | USD -54,285.20 | USD -11,658.10 | 8 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 4.23 | USD -42.73 |
| HOLD_5_OR_DTE_LE_7 | USD 4.23 | USD -42.73 |
| HOLD_5_OR_DTE_LE_14 | USD 4.23 | USD -42.73 |
| HOLD_10_SESSIONS | USD 17.01 | USD -74.15 |
| HOLD_10_OR_DTE_LE_7 | USD 17.01 | USD -74.15 |
| HOLD_10_OR_DTE_LE_14 | USD 17.01 | USD -74.15 |
| HOLD_15_SESSIONS | USD 36.02 | USD -183.82 |
| HOLD_15_OR_DTE_LE_7 | USD 36.02 | USD -183.82 |
| HOLD_15_OR_DTE_LE_14 | USD 36.02 | USD -183.82 |
| HOLD_20_SESSIONS | USD 60.08 | USD -246.56 |
| HOLD_20_OR_DTE_LE_7 | USD 60.08 | USD -246.56 |
| HOLD_20_OR_DTE_LE_14 | USD 63.94 | USD -300.45 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 180 | 59.44% | USD -38.51 | USD -6,931.00 | USD -3,454.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 180 | 58.89% | USD -47.61 | USD -8,569.00 | USD -3,463.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 180 | 58.33% | USD -73.51 | USD -13,231.00 | USD -3,489.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 180 | 58.33% | USD -82.61 | USD -14,869.00 | USD -3,498.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 180 | 55.56% | USD -108.51 | USD -19,531.00 | USD -3,524.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 180 | 55.00% | USD -117.61 | USD -21,169.00 | USD -3,533.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 180 | 48.89% | USD -178.51 | USD -32,131.00 | USD -3,594.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 180 | 48.33% | USD -187.61 | USD -33,769.00 | USD -3,603.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 180 | 59.44% | USD -38.51 | USD -6,931.00 | USD -3,454.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 180 | 58.89% | USD -47.61 | USD -8,569.00 | USD -3,463.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 180 | 58.33% | USD -73.51 | USD -13,231.00 | USD -3,489.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 180 | 58.33% | USD -82.61 | USD -14,869.00 | USD -3,498.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 180 | 55.56% | USD -108.51 | USD -19,531.00 | USD -3,524.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 180 | 55.00% | USD -117.61 | USD -21,169.00 | USD -3,533.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 180 | 48.89% | USD -178.51 | USD -32,131.00 | USD -3,594.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 180 | 48.33% | USD -187.61 | USD -33,769.00 | USD -3,603.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 180 | 59.44% | USD -38.51 | USD -6,931.00 | USD -3,454.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 180 | 58.89% | USD -47.61 | USD -8,569.00 | USD -3,463.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 180 | 58.33% | USD -73.51 | USD -13,231.00 | USD -3,489.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 180 | 58.33% | USD -82.61 | USD -14,869.00 | USD -3,498.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 180 | 55.56% | USD -108.51 | USD -19,531.00 | USD -3,524.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 180 | 55.00% | USD -117.61 | USD -21,169.00 | USD -3,533.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 180 | 48.89% | USD -178.51 | USD -32,131.00 | USD -3,594.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 180 | 48.33% | USD -187.61 | USD -33,769.00 | USD -3,603.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 179 | 59.22% | USD -57.14 | USD -10,228.00 | USD -6,567.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 179 | 58.66% | USD -66.24 | USD -11,856.90 | USD -6,576.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 179 | 58.10% | USD -92.14 | USD -16,493.00 | USD -6,602.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 179 | 58.10% | USD -101.24 | USD -18,121.90 | USD -6,611.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 179 | 57.54% | USD -127.14 | USD -22,758.00 | USD -6,637.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 179 | 56.42% | USD -136.24 | USD -24,386.90 | USD -6,646.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 179 | 52.51% | USD -197.14 | USD -35,288.00 | USD -6,707.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 179 | 52.51% | USD -206.24 | USD -36,916.90 | USD -6,716.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 179 | 59.22% | USD -57.14 | USD -10,228.00 | USD -6,567.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 179 | 58.66% | USD -66.24 | USD -11,856.90 | USD -6,576.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 179 | 58.10% | USD -92.14 | USD -16,493.00 | USD -6,602.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 179 | 58.10% | USD -101.24 | USD -18,121.90 | USD -6,611.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 179 | 57.54% | USD -127.14 | USD -22,758.00 | USD -6,637.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 179 | 56.42% | USD -136.24 | USD -24,386.90 | USD -6,646.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 179 | 52.51% | USD -197.14 | USD -35,288.00 | USD -6,707.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 179 | 52.51% | USD -206.24 | USD -36,916.90 | USD -6,716.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 179 | 59.22% | USD -57.14 | USD -10,228.00 | USD -6,567.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 179 | 58.66% | USD -66.24 | USD -11,856.90 | USD -6,576.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 179 | 58.10% | USD -92.14 | USD -16,493.00 | USD -6,602.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 179 | 58.10% | USD -101.24 | USD -18,121.90 | USD -6,611.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 179 | 57.54% | USD -127.14 | USD -22,758.00 | USD -6,637.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 179 | 56.42% | USD -136.24 | USD -24,386.90 | USD -6,646.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 179 | 52.51% | USD -197.14 | USD -35,288.00 | USD -6,707.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 179 | 52.51% | USD -206.24 | USD -36,916.90 | USD -6,716.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 176 | 59.09% | USD -147.80 | USD -26,012.00 | USD -6,345.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 176 | 59.09% | USD -156.90 | USD -27,613.60 | USD -6,354.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 176 | 57.95% | USD -182.80 | USD -32,172.00 | USD -6,380.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 176 | 57.39% | USD -191.90 | USD -33,773.60 | USD -6,389.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 176 | 56.82% | USD -217.80 | USD -38,332.00 | USD -6,415.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 176 | 56.25% | USD -226.90 | USD -39,933.60 | USD -6,424.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 176 | 54.55% | USD -287.80 | USD -50,652.00 | USD -6,485.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 176 | 54.55% | USD -296.90 | USD -52,253.60 | USD -6,494.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 176 | 59.09% | USD -147.80 | USD -26,012.00 | USD -6,345.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 176 | 59.09% | USD -156.90 | USD -27,613.60 | USD -6,354.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 176 | 57.95% | USD -182.80 | USD -32,172.00 | USD -6,380.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 176 | 57.39% | USD -191.90 | USD -33,773.60 | USD -6,389.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 176 | 56.82% | USD -217.80 | USD -38,332.00 | USD -6,415.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 176 | 56.25% | USD -226.90 | USD -39,933.60 | USD -6,424.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 176 | 54.55% | USD -287.80 | USD -50,652.00 | USD -6,485.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 176 | 54.55% | USD -296.90 | USD -52,253.60 | USD -6,494.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 176 | 59.09% | USD -147.80 | USD -26,012.00 | USD -6,345.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 176 | 59.09% | USD -156.90 | USD -27,613.60 | USD -6,354.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 176 | 57.95% | USD -182.80 | USD -32,172.00 | USD -6,380.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 176 | 57.39% | USD -191.90 | USD -33,773.60 | USD -6,389.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 176 | 56.82% | USD -217.80 | USD -38,332.00 | USD -6,415.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 176 | 56.25% | USD -226.90 | USD -39,933.60 | USD -6,424.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 176 | 54.55% | USD -287.80 | USD -50,652.00 | USD -6,485.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 176 | 54.55% | USD -296.90 | USD -52,253.60 | USD -6,494.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 172 | 62.79% | USD -186.48 | USD -32,074.00 | USD -11,579.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 172 | 62.21% | USD -195.58 | USD -33,639.20 | USD -11,588.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 172 | 62.21% | USD -221.48 | USD -38,094.00 | USD -11,614.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 172 | 62.21% | USD -230.58 | USD -39,659.20 | USD -11,623.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 172 | 61.63% | USD -256.48 | USD -44,114.00 | USD -11,649.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 172 | 61.63% | USD -265.58 | USD -45,679.20 | USD -11,658.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 172 | 59.88% | USD -326.48 | USD -56,154.00 | USD -11,719.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 172 | 59.88% | USD -335.58 | USD -57,719.20 | USD -11,728.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 172 | 62.79% | USD -186.48 | USD -32,074.00 | USD -11,579.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 172 | 62.21% | USD -195.58 | USD -33,639.20 | USD -11,588.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 172 | 62.21% | USD -221.48 | USD -38,094.00 | USD -11,614.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 172 | 62.21% | USD -230.58 | USD -39,659.20 | USD -11,623.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 172 | 61.63% | USD -256.48 | USD -44,114.00 | USD -11,649.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 172 | 61.63% | USD -265.58 | USD -45,679.20 | USD -11,658.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 172 | 59.88% | USD -326.48 | USD -56,154.00 | USD -11,719.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 172 | 59.88% | USD -335.58 | USD -57,719.20 | USD -11,728.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 172 | 60.47% | USD -236.51 | USD -40,680.00 | USD -11,579.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 172 | 60.47% | USD -245.61 | USD -42,245.20 | USD -11,588.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 172 | 59.30% | USD -271.51 | USD -46,700.00 | USD -11,614.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 172 | 59.30% | USD -280.61 | USD -48,265.20 | USD -11,623.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 172 | 59.30% | USD -306.51 | USD -52,720.00 | USD -11,649.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 172 | 59.30% | USD -315.61 | USD -54,285.20 | USD -11,658.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 172 | 58.72% | USD -376.51 | USD -64,760.00 | USD -11,719.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 172 | 58.14% | USD -385.61 | USD -66,325.20 | USD -11,728.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 180/180 (0) | 28.89% (22.76–35.90%) | USD -25.49 | USD -4,589.00 | USD -294.60 |
| HOLD_5_SESSIONS | 1 : 6 | 180/180 (0) | 55.00% (47.70–62.09%) | USD -117.61 | USD -21,169.00 | USD -3,533.10 |
| HOLD_5_SESSIONS | 6 : 1 | 180/180 (0) | 34.44% (27.89–41.65%) | USD -60.86 | USD -10,954.00 | USD -2,649.10 |
| HOLD_5_SESSIONS | 5 : 5 | 180/180 (0) | 28.89% (22.76–35.90%) | USD -127.47 | USD -22,945.00 | USD -1,473.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 180/180 (0) | 28.89% (22.76–35.90%) | USD -25.49 | USD -4,589.00 | USD -294.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 180/180 (0) | 55.00% (47.70–62.09%) | USD -117.61 | USD -21,169.00 | USD -3,533.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 180/180 (0) | 34.44% (27.89–41.65%) | USD -60.86 | USD -10,954.00 | USD -2,649.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 180/180 (0) | 28.89% (22.76–35.90%) | USD -127.47 | USD -22,945.00 | USD -1,473.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 180/180 (0) | 28.89% (22.76–35.90%) | USD -25.49 | USD -4,589.00 | USD -294.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 180/180 (0) | 55.00% (47.70–62.09%) | USD -117.61 | USD -21,169.00 | USD -3,533.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 180/180 (0) | 34.44% (27.89–41.65%) | USD -60.86 | USD -10,954.00 | USD -2,649.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 180/180 (0) | 28.89% (22.76–35.90%) | USD -127.47 | USD -22,945.00 | USD -1,473.00 |
| HOLD_10_SESSIONS | 1 : 1 | 179/180 (1) | 31.28% (24.95–38.41%) | USD -17.95 | USD -3,213.40 | USD -814.60 |
| HOLD_10_SESSIONS | 1 : 6 | 179/180 (1) | 56.42% (49.10–63.48%) | USD -136.24 | USD -24,386.90 | USD -6,646.10 |
| HOLD_10_SESSIONS | 6 : 1 | 179/180 (1) | 40.22% (33.32–47.54%) | USD 10.58 | USD 1,893.10 | USD -2,900.10 |
| HOLD_10_SESSIONS | 5 : 5 | 179/180 (1) | 31.28% (24.95–38.41%) | USD -89.76 | USD -16,067.00 | USD -4,073.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 179/180 (1) | 31.28% (24.95–38.41%) | USD -17.95 | USD -3,213.40 | USD -814.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 179/180 (1) | 56.42% (49.10–63.48%) | USD -136.24 | USD -24,386.90 | USD -6,646.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 179/180 (1) | 40.22% (33.32–47.54%) | USD 10.58 | USD 1,893.10 | USD -2,900.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 179/180 (1) | 31.28% (24.95–38.41%) | USD -89.76 | USD -16,067.00 | USD -4,073.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 179/180 (1) | 31.28% (24.95–38.41%) | USD -17.95 | USD -3,213.40 | USD -814.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 179/180 (1) | 56.42% (49.10–63.48%) | USD -136.24 | USD -24,386.90 | USD -6,646.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 179/180 (1) | 40.22% (33.32–47.54%) | USD 10.58 | USD 1,893.10 | USD -2,900.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 179/180 (1) | 31.28% (24.95–38.41%) | USD -89.76 | USD -16,067.00 | USD -4,073.00 |
| HOLD_15_SESSIONS | 1 : 1 | 176/180 (4) | 32.39% (25.91–39.61%) | USD -17.21 | USD -3,029.60 | USD -558.60 |
| HOLD_15_SESSIONS | 1 : 6 | 176/180 (4) | 56.25% (48.87–63.37%) | USD -226.90 | USD -39,933.60 | USD -6,424.10 |
| HOLD_15_SESSIONS | 6 : 1 | 176/180 (4) | 34.66% (28.02–41.95%) | USD 106.40 | USD 18,726.40 | USD -2,631.10 |
| HOLD_15_SESSIONS | 5 : 5 | 176/180 (4) | 32.39% (25.91–39.61%) | USD -86.07 | USD -15,148.00 | USD -2,793.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 176/180 (4) | 32.39% (25.91–39.61%) | USD -17.21 | USD -3,029.60 | USD -558.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 176/180 (4) | 56.25% (48.87–63.37%) | USD -226.90 | USD -39,933.60 | USD -6,424.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 176/180 (4) | 34.66% (28.02–41.95%) | USD 106.40 | USD 18,726.40 | USD -2,631.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 176/180 (4) | 32.39% (25.91–39.61%) | USD -86.07 | USD -15,148.00 | USD -2,793.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 176/180 (4) | 32.39% (25.91–39.61%) | USD -17.21 | USD -3,029.60 | USD -558.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 176/180 (4) | 56.25% (48.87–63.37%) | USD -226.90 | USD -39,933.60 | USD -6,424.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 176/180 (4) | 34.66% (28.02–41.95%) | USD 106.40 | USD 18,726.40 | USD -2,631.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 176/180 (4) | 32.39% (25.91–39.61%) | USD -86.07 | USD -15,148.00 | USD -2,793.00 |
| HOLD_20_SESSIONS | 1 : 1 | 172/180 (8) | 35.47% (28.70–42.86%) | USD -3.61 | USD -621.20 | USD -834.60 |
| HOLD_20_SESSIONS | 1 : 6 | 172/180 (8) | 61.63% (54.18–68.57%) | USD -265.58 | USD -45,679.20 | USD -11,658.10 |
| HOLD_20_SESSIONS | 6 : 1 | 172/180 (8) | 34.88% (28.16–42.27%) | USD 240.30 | USD 41,330.80 | USD -2,520.10 |
| HOLD_20_SESSIONS | 5 : 5 | 172/180 (8) | 35.47% (28.70–42.86%) | USD -18.06 | USD -3,106.00 | USD -4,173.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 172/180 (8) | 35.47% (28.70–42.86%) | USD -3.61 | USD -621.20 | USD -834.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 172/180 (8) | 61.63% (54.18–68.57%) | USD -265.58 | USD -45,679.20 | USD -11,658.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 172/180 (8) | 34.88% (28.16–42.27%) | USD 240.30 | USD 41,330.80 | USD -2,520.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 172/180 (8) | 35.47% (28.70–42.86%) | USD -18.06 | USD -3,106.00 | USD -4,173.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 172/180 (8) | 34.30% (27.62–41.67%) | USD -8.73 | USD -1,502.20 | USD -1,102.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 172/180 (8) | 59.30% (51.84–66.36%) | USD -315.61 | USD -54,285.20 | USD -11,658.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 172/180 (8) | 36.05% (29.25–43.45%) | USD 254.48 | USD 43,769.80 | USD -2,627.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 172/180 (8) | 34.30% (27.62–41.67%) | USD -43.67 | USD -7,511.00 | USD -5,513.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -75% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -50% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -40% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -30% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -25% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -20% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -15% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -10% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| -5% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| 0% | 180/180 | 100.00% | USD 987.64 | USD 105.45 |
| 5% | 65/180 | 36.11% | USD -1,552.99 | USD -8,333.40 |
| 10% | 3/180 | 1.67% | USD -11,831.98 | USD -24,040.25 |
| 20% | 1/180 | 0.56% | USD -33,419.64 | USD -55,596.95 |

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