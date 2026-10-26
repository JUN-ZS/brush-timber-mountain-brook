# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 452.23 / USD 2,692.12; mean absolute mismatch USD 2,239.89; mean match score 16.59%.
- Actual selected contract ratios: {'1:6': 169}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 169; entered cohorts: 169; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 168/169 | 116/52/0 | 69.05% (61.70–75.55%) | USD 109.26 | USD 398.40 | USD 18,355.20 | USD -15,672.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 168/169 | 116/52/0 | 69.05% (61.70–75.55%) | USD 109.26 | USD 398.40 | USD 18,355.20 | USD -15,672.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 168/169 | 116/52/0 | 69.05% (61.70–75.55%) | USD 109.26 | USD 398.40 | USD 18,355.20 | USD -15,672.10 | 1 |
| HOLD_10_SESSIONS | 168/169 | 124/44/0 | 73.81% (66.68–79.87%) | USD 5.78 | USD 764.40 | USD 970.20 | USD -18,603.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 168/169 | 124/44/0 | 73.81% (66.68–79.87%) | USD 5.78 | USD 764.40 | USD 970.20 | USD -18,603.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 168/169 | 124/44/0 | 73.81% (66.68–79.87%) | USD 5.78 | USD 764.40 | USD 970.20 | USD -18,603.10 | 1 |
| HOLD_15_SESSIONS | 166/169 | 135/31/0 | 81.33% (74.71–86.52%) | USD 346.77 | USD 1,056.90 | USD 57,564.40 | USD -31,171.10 | 3 |
| HOLD_15_OR_DTE_LE_7 | 166/169 | 135/31/0 | 81.33% (74.71–86.52%) | USD 346.77 | USD 1,056.90 | USD 57,564.40 | USD -31,171.10 | 3 |
| HOLD_15_OR_DTE_LE_14 | 166/169 | 135/31/0 | 81.33% (74.71–86.52%) | USD 346.77 | USD 1,056.90 | USD 57,564.40 | USD -31,171.10 | 3 |
| HOLD_20_SESSIONS | 166/169 | 138/28/0 | 83.13% (76.70–88.06%) | USD 323.94 | USD 1,309.90 | USD 53,774.40 | USD -51,761.10 | 3 |
| HOLD_20_OR_DTE_LE_7 | 166/169 | 138/28/0 | 83.13% (76.70–88.06%) | USD 323.94 | USD 1,309.90 | USD 53,774.40 | USD -51,761.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 166/169 | 138/28/0 | 83.13% (76.70–88.06%) | USD 389.18 | USD 1,250.40 | USD 64,603.40 | USD -46,879.10 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -62.39 | USD 250.75 |
| HOLD_5_OR_DTE_LE_7 | USD -62.39 | USD 250.75 |
| HOLD_5_OR_DTE_LE_14 | USD -62.39 | USD 250.75 |
| HOLD_10_SESSIONS | USD -59.95 | USD 144.82 |
| HOLD_10_OR_DTE_LE_7 | USD -59.95 | USD 144.82 |
| HOLD_10_OR_DTE_LE_14 | USD -59.95 | USD 144.82 |
| HOLD_15_SESSIONS | USD -117.23 | USD 543.11 |
| HOLD_15_OR_DTE_LE_7 | USD -117.23 | USD 543.11 |
| HOLD_15_OR_DTE_LE_14 | USD -117.23 | USD 543.11 |
| HOLD_20_SESSIONS | USD -136.56 | USD 539.60 |
| HOLD_20_OR_DTE_LE_7 | USD -136.56 | USD 539.60 |
| HOLD_20_OR_DTE_LE_14 | USD -138.77 | USD 607.05 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 168 | 70.83% | USD 188.36 | USD 31,644.00 | USD -15,593.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 168 | 70.24% | USD 179.26 | USD 30,115.20 | USD -15,602.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 168 | 69.64% | USD 153.36 | USD 25,764.00 | USD -15,628.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 168 | 69.64% | USD 144.26 | USD 24,235.20 | USD -15,637.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 168 | 69.64% | USD 118.36 | USD 19,884.00 | USD -15,663.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 168 | 69.05% | USD 109.26 | USD 18,355.20 | USD -15,672.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 168 | 67.26% | USD 48.36 | USD 8,124.00 | USD -15,733.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 168 | 66.67% | USD 39.26 | USD 6,595.20 | USD -15,742.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 168 | 70.83% | USD 188.36 | USD 31,644.00 | USD -15,593.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 168 | 70.24% | USD 179.26 | USD 30,115.20 | USD -15,602.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 168 | 69.64% | USD 153.36 | USD 25,764.00 | USD -15,628.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 168 | 69.64% | USD 144.26 | USD 24,235.20 | USD -15,637.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 168 | 69.64% | USD 118.36 | USD 19,884.00 | USD -15,663.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 168 | 69.05% | USD 109.26 | USD 18,355.20 | USD -15,672.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 168 | 67.26% | USD 48.36 | USD 8,124.00 | USD -15,733.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 168 | 66.67% | USD 39.26 | USD 6,595.20 | USD -15,742.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 168 | 70.83% | USD 188.36 | USD 31,644.00 | USD -15,593.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 168 | 70.24% | USD 179.26 | USD 30,115.20 | USD -15,602.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 168 | 69.64% | USD 153.36 | USD 25,764.00 | USD -15,628.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 168 | 69.64% | USD 144.26 | USD 24,235.20 | USD -15,637.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 168 | 69.64% | USD 118.36 | USD 19,884.00 | USD -15,663.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 168 | 69.05% | USD 109.26 | USD 18,355.20 | USD -15,672.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 168 | 67.26% | USD 48.36 | USD 8,124.00 | USD -15,733.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 168 | 66.67% | USD 39.26 | USD 6,595.20 | USD -15,742.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 168 | 75.60% | USD 84.88 | USD 14,259.00 | USD -18,524.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 168 | 75.00% | USD 75.78 | USD 12,730.20 | USD -18,533.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 168 | 75.00% | USD 49.88 | USD 8,379.00 | USD -18,559.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 168 | 75.00% | USD 40.77 | USD 6,850.20 | USD -18,568.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 168 | 73.81% | USD 14.88 | USD 2,499.00 | USD -18,594.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 168 | 73.81% | USD 5.78 | USD 970.20 | USD -18,603.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 168 | 72.62% | USD -55.12 | USD -9,261.00 | USD -18,664.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 168 | 72.62% | USD -64.22 | USD -10,789.80 | USD -18,673.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 168 | 75.60% | USD 84.88 | USD 14,259.00 | USD -18,524.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 168 | 75.00% | USD 75.78 | USD 12,730.20 | USD -18,533.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 168 | 75.00% | USD 49.88 | USD 8,379.00 | USD -18,559.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 168 | 75.00% | USD 40.77 | USD 6,850.20 | USD -18,568.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 168 | 73.81% | USD 14.88 | USD 2,499.00 | USD -18,594.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 168 | 73.81% | USD 5.78 | USD 970.20 | USD -18,603.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 168 | 72.62% | USD -55.12 | USD -9,261.00 | USD -18,664.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 168 | 72.62% | USD -64.22 | USD -10,789.80 | USD -18,673.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 168 | 75.60% | USD 84.88 | USD 14,259.00 | USD -18,524.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 168 | 75.00% | USD 75.78 | USD 12,730.20 | USD -18,533.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 168 | 75.00% | USD 49.88 | USD 8,379.00 | USD -18,559.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 168 | 75.00% | USD 40.77 | USD 6,850.20 | USD -18,568.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 168 | 73.81% | USD 14.88 | USD 2,499.00 | USD -18,594.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 168 | 73.81% | USD 5.78 | USD 970.20 | USD -18,603.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 168 | 72.62% | USD -55.12 | USD -9,261.00 | USD -18,664.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 168 | 72.62% | USD -64.22 | USD -10,789.80 | USD -18,673.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 166 | 81.33% | USD 425.87 | USD 70,695.00 | USD -31,092.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 166 | 81.33% | USD 416.77 | USD 69,184.40 | USD -31,101.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 166 | 81.33% | USD 390.87 | USD 64,885.00 | USD -31,127.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 166 | 81.33% | USD 381.77 | USD 63,374.40 | USD -31,136.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 166 | 81.33% | USD 355.87 | USD 59,075.00 | USD -31,162.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 166 | 81.33% | USD 346.77 | USD 57,564.40 | USD -31,171.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 166 | 78.92% | USD 285.87 | USD 47,455.00 | USD -31,232.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 166 | 78.92% | USD 276.77 | USD 45,944.40 | USD -31,241.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 166 | 81.33% | USD 425.87 | USD 70,695.00 | USD -31,092.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 166 | 81.33% | USD 416.77 | USD 69,184.40 | USD -31,101.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 166 | 81.33% | USD 390.87 | USD 64,885.00 | USD -31,127.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 166 | 81.33% | USD 381.77 | USD 63,374.40 | USD -31,136.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 166 | 81.33% | USD 355.87 | USD 59,075.00 | USD -31,162.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 166 | 81.33% | USD 346.77 | USD 57,564.40 | USD -31,171.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 166 | 78.92% | USD 285.87 | USD 47,455.00 | USD -31,232.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 166 | 78.92% | USD 276.77 | USD 45,944.40 | USD -31,241.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 166 | 81.33% | USD 425.87 | USD 70,695.00 | USD -31,092.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 166 | 81.33% | USD 416.77 | USD 69,184.40 | USD -31,101.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 166 | 81.33% | USD 390.87 | USD 64,885.00 | USD -31,127.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 166 | 81.33% | USD 381.77 | USD 63,374.40 | USD -31,136.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 166 | 81.33% | USD 355.87 | USD 59,075.00 | USD -31,162.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 166 | 81.33% | USD 346.77 | USD 57,564.40 | USD -31,171.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 166 | 78.92% | USD 285.87 | USD 47,455.00 | USD -31,232.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 166 | 78.92% | USD 276.77 | USD 45,944.40 | USD -31,241.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 166 | 83.13% | USD 403.04 | USD 66,905.00 | USD -51,682.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 166 | 83.13% | USD 393.94 | USD 65,394.40 | USD -51,691.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 166 | 83.13% | USD 368.04 | USD 61,095.00 | USD -51,717.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 166 | 83.13% | USD 358.94 | USD 59,584.40 | USD -51,726.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 166 | 83.13% | USD 333.04 | USD 55,285.00 | USD -51,752.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 166 | 83.13% | USD 323.94 | USD 53,774.40 | USD -51,761.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 166 | 82.53% | USD 263.04 | USD 43,665.00 | USD -51,822.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 166 | 82.53% | USD 253.94 | USD 42,154.40 | USD -51,831.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 166 | 83.13% | USD 403.04 | USD 66,905.00 | USD -51,682.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 166 | 83.13% | USD 393.94 | USD 65,394.40 | USD -51,691.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 166 | 83.13% | USD 368.04 | USD 61,095.00 | USD -51,717.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 166 | 83.13% | USD 358.94 | USD 59,584.40 | USD -51,726.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 166 | 83.13% | USD 333.04 | USD 55,285.00 | USD -51,752.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 166 | 83.13% | USD 323.94 | USD 53,774.40 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 166 | 82.53% | USD 263.04 | USD 43,665.00 | USD -51,822.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 166 | 82.53% | USD 253.94 | USD 42,154.40 | USD -51,831.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 166 | 83.13% | USD 468.28 | USD 77,734.00 | USD -46,800.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 166 | 83.13% | USD 459.18 | USD 76,223.40 | USD -46,809.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 166 | 83.13% | USD 433.28 | USD 71,924.00 | USD -46,835.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 166 | 83.13% | USD 424.18 | USD 70,413.40 | USD -46,844.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 166 | 83.13% | USD 398.28 | USD 66,114.00 | USD -46,870.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 166 | 83.13% | USD 389.18 | USD 64,603.40 | USD -46,879.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 166 | 82.53% | USD 328.28 | USD 54,494.00 | USD -46,940.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 166 | 82.53% | USD 319.18 | USD 52,983.40 | USD -46,949.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 168/169 (1) | 30.95% (24.45–38.30%) | USD -43.20 | USD -7,257.80 | USD -1,290.60 |
| HOLD_5_SESSIONS | 1 : 6 | 168/169 (1) | 69.05% (61.70–75.55%) | USD 109.26 | USD 18,355.20 | USD -15,672.10 |
| HOLD_5_SESSIONS | 6 : 1 | 168/169 (1) | 24.40% (18.53–31.42%) | USD -411.67 | USD -69,159.80 | USD -6,090.10 |
| HOLD_5_SESSIONS | 5 : 5 | 168/169 (1) | 30.95% (24.45–38.30%) | USD -216.01 | USD -36,289.00 | USD -6,453.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 168/169 (1) | 30.95% (24.45–38.30%) | USD -43.20 | USD -7,257.80 | USD -1,290.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 168/169 (1) | 69.05% (61.70–75.55%) | USD 109.26 | USD 18,355.20 | USD -15,672.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 168/169 (1) | 24.40% (18.53–31.42%) | USD -411.67 | USD -69,159.80 | USD -6,090.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 168/169 (1) | 30.95% (24.45–38.30%) | USD -216.01 | USD -36,289.00 | USD -6,453.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 168/169 (1) | 30.95% (24.45–38.30%) | USD -43.20 | USD -7,257.80 | USD -1,290.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 168/169 (1) | 69.05% (61.70–75.55%) | USD 109.26 | USD 18,355.20 | USD -15,672.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 168/169 (1) | 24.40% (18.53–31.42%) | USD -411.67 | USD -69,159.80 | USD -6,090.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 168/169 (1) | 30.95% (24.45–38.30%) | USD -216.01 | USD -36,289.00 | USD -6,453.00 |
| HOLD_10_SESSIONS | 1 : 1 | 168/169 (1) | 35.12% (28.31–42.60%) | USD -58.41 | USD -9,812.80 | USD -1,415.60 |
| HOLD_10_SESSIONS | 1 : 6 | 168/169 (1) | 73.81% (66.68–79.87%) | USD 5.78 | USD 970.20 | USD -18,603.10 |
| HOLD_10_SESSIONS | 6 : 1 | 168/169 (1) | 23.81% (18.00–30.79%) | USD -414.64 | USD -69,659.80 | USD -6,843.10 |
| HOLD_10_SESSIONS | 5 : 5 | 168/169 (1) | 35.12% (28.31–42.60%) | USD -292.05 | USD -49,064.00 | USD -7,078.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 168/169 (1) | 35.12% (28.31–42.60%) | USD -58.41 | USD -9,812.80 | USD -1,415.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 168/169 (1) | 73.81% (66.68–79.87%) | USD 5.78 | USD 970.20 | USD -18,603.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 168/169 (1) | 23.81% (18.00–30.79%) | USD -414.64 | USD -69,659.80 | USD -6,843.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 168/169 (1) | 35.12% (28.31–42.60%) | USD -292.05 | USD -49,064.00 | USD -7,078.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 168/169 (1) | 35.12% (28.31–42.60%) | USD -58.41 | USD -9,812.80 | USD -1,415.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 168/169 (1) | 73.81% (66.68–79.87%) | USD 5.78 | USD 970.20 | USD -18,603.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 168/169 (1) | 23.81% (18.00–30.79%) | USD -414.64 | USD -69,659.80 | USD -6,843.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 168/169 (1) | 35.12% (28.31–42.60%) | USD -292.05 | USD -49,064.00 | USD -7,078.00 |
| HOLD_15_SESSIONS | 1 : 1 | 166/169 (3) | 34.94% (28.10–42.46%) | USD -49.32 | USD -8,186.60 | USD -3,009.60 |
| HOLD_15_SESSIONS | 1 : 6 | 166/169 (3) | 81.33% (74.71–86.52%) | USD 346.77 | USD 57,564.40 | USD -31,171.10 |
| HOLD_15_SESSIONS | 6 : 1 | 166/169 (3) | 20.48% (15.04–27.26%) | USD -691.99 | USD -114,870.60 | USD -8,004.10 |
| HOLD_15_SESSIONS | 5 : 5 | 166/169 (3) | 34.94% (28.10–42.46%) | USD -246.58 | USD -40,933.00 | USD -15,048.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 166/169 (3) | 34.94% (28.10–42.46%) | USD -49.32 | USD -8,186.60 | USD -3,009.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 166/169 (3) | 81.33% (74.71–86.52%) | USD 346.77 | USD 57,564.40 | USD -31,171.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 166/169 (3) | 20.48% (15.04–27.26%) | USD -691.99 | USD -114,870.60 | USD -8,004.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 166/169 (3) | 34.94% (28.10–42.46%) | USD -246.58 | USD -40,933.00 | USD -15,048.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 166/169 (3) | 34.94% (28.10–42.46%) | USD -49.32 | USD -8,186.60 | USD -3,009.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 166/169 (3) | 81.33% (74.71–86.52%) | USD 346.77 | USD 57,564.40 | USD -31,171.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 166/169 (3) | 20.48% (15.04–27.26%) | USD -691.99 | USD -114,870.60 | USD -8,004.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 166/169 (3) | 34.94% (28.10–42.46%) | USD -246.58 | USD -40,933.00 | USD -15,048.00 |
| HOLD_20_SESSIONS | 1 : 1 | 166/169 (3) | 40.36% (33.20–47.96%) | USD -69.23 | USD -11,491.60 | USD -4,434.60 |
| HOLD_20_SESSIONS | 1 : 6 | 166/169 (3) | 83.13% (76.70–88.06%) | USD 323.94 | USD 53,774.40 | USD -51,761.10 |
| HOLD_20_SESSIONS | 6 : 1 | 166/169 (3) | 15.66% (10.92–21.96%) | USD -808.53 | USD -134,215.60 | USD -8,979.10 |
| HOLD_20_SESSIONS | 5 : 5 | 166/169 (3) | 40.36% (33.20–47.96%) | USD -346.13 | USD -57,458.00 | USD -22,173.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 166/169 (3) | 40.36% (33.20–47.96%) | USD -69.23 | USD -11,491.60 | USD -4,434.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 166/169 (3) | 83.13% (76.70–88.06%) | USD 323.94 | USD 53,774.40 | USD -51,761.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 166/169 (3) | 15.66% (10.92–21.96%) | USD -808.53 | USD -134,215.60 | USD -8,979.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 166/169 (3) | 40.36% (33.20–47.96%) | USD -346.13 | USD -57,458.00 | USD -22,173.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 166/169 (3) | 39.16% (32.06–46.75%) | USD -60.20 | USD -9,992.60 | USD -4,032.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 166/169 (3) | 83.13% (76.70–88.06%) | USD 389.18 | USD 64,603.40 | USD -46,879.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 166/169 (3) | 16.27% (11.43–22.63%) | USD -810.55 | USD -134,551.60 | USD -8,979.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 166/169 (3) | 39.16% (32.06–46.75%) | USD -300.98 | USD -49,963.00 | USD -20,163.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/169 | 0.00% | USD -201,911.85 | USD -336,601.55 |
| -75% | 0/169 | 0.00% | USD -148,809.77 | USD -249,385.05 |
| -50% | 0/169 | 0.00% | USD -95,707.68 | USD -162,168.55 |
| -40% | 0/169 | 0.00% | USD -74,466.85 | USD -127,281.95 |
| -30% | 0/169 | 0.00% | USD -53,226.02 | USD -92,395.35 |
| -25% | 0/169 | 0.00% | USD -42,605.60 | USD -74,952.05 |
| -20% | 0/169 | 0.00% | USD -31,985.18 | USD -57,508.75 |
| -15% | 1/169 | 0.59% | USD -21,364.33 | USD -40,065.45 |
| -10% | 4/169 | 2.37% | USD -10,805.64 | USD -22,622.15 |
| -5% | 73/169 | 43.20% | USD -684.14 | USD -8,014.25 |
| 0% | 169/169 | 100.00% | USD 2,179.18 | USD 713.45 |
| 5% | 169/169 | 100.00% | USD 2,200.34 | USD 713.45 |
| 10% | 169/169 | 100.00% | USD 2,200.34 | USD 713.45 |
| 20% | 169/169 | 100.00% | USD 2,200.34 | USD 713.45 |

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