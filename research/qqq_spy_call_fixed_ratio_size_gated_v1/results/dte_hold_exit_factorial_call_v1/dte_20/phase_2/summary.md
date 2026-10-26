# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 161.74 / USD 869.75; mean absolute mismatch USD 708.01; mean match score 19.62%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 193/195 | 115/78/0 | 59.59% (52.54–66.26%) | USD -153.08 | USD 111.90 | USD -29,545.30 | USD -4,802.10 | 2 |
| HOLD_5_OR_DTE_LE_7 | 193/195 | 115/78/0 | 59.59% (52.54–66.26%) | USD -153.08 | USD 111.90 | USD -29,545.30 | USD -4,802.10 | 2 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 111/83/0 | 57.22% (50.18–63.97%) | USD -147.41 | USD 99.90 | USD -28,598.40 | USD -4,126.10 | 1 |
| HOLD_10_SESSIONS | 138/195 | 83/55/0 | 60.14% (51.81–67.93%) | USD -449.09 | USD 168.40 | USD -61,974.80 | USD -5,664.10 | 57 |
| HOLD_10_OR_DTE_LE_7 | 174/195 | 108/66/0 | 62.07% (54.67–68.94%) | USD -329.97 | USD 178.90 | USD -57,415.40 | USD -6,681.10 | 21 |
| HOLD_10_OR_DTE_LE_14 | 194/195 | 112/82/0 | 57.73% (50.70–64.47%) | USD -143.68 | USD 104.40 | USD -27,874.40 | USD -4,126.10 | 1 |
| HOLD_15_SESSIONS | 5/195 | 2/3/0 | 40.00% (11.76–76.93%) | USD -1,913.10 | USD -2,901.10 | USD -9,565.50 | USD -5,550.10 | 190 |
| HOLD_15_OR_DTE_LE_7 | 171/195 | 104/67/0 | 60.82% (53.34–67.82%) | USD -356.99 | USD 159.90 | USD -61,045.10 | USD -6,681.10 | 24 |
| HOLD_15_OR_DTE_LE_14 | 194/195 | 112/82/0 | 57.73% (50.70–64.47%) | USD -143.68 | USD 104.40 | USD -27,874.40 | USD -4,126.10 | 1 |
| HOLD_20_SESSIONS | 0/195 | 0/0/0 | — | — | — | — | — | 195 |
| HOLD_20_OR_DTE_LE_7 | 171/195 | 104/67/0 | 60.82% (53.34–67.82%) | USD -356.99 | USD 159.90 | USD -61,045.10 | USD -6,681.10 | 24 |
| HOLD_20_OR_DTE_LE_14 | 194/195 | 112/82/0 | 57.73% (50.70–64.47%) | USD -143.68 | USD 104.40 | USD -27,874.40 | USD -4,126.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 4.85 | USD -78.84 |
| HOLD_5_OR_DTE_LE_7 | USD 4.85 | USD -78.84 |
| HOLD_5_OR_DTE_LE_14 | USD 7.06 | USD -75.37 |
| HOLD_10_SESSIONS | USD 72.49 | USD -442.48 |
| HOLD_10_OR_DTE_LE_7 | USD 37.13 | USD -288.00 |
| HOLD_10_OR_DTE_LE_14 | USD 12.06 | USD -76.64 |
| HOLD_15_SESSIONS | USD 796.40 | USD -2,630.40 |
| HOLD_15_OR_DTE_LE_7 | USD 45.23 | USD -323.12 |
| HOLD_15_OR_DTE_LE_14 | USD 12.06 | USD -76.64 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD 45.23 | USD -323.12 |
| HOLD_20_OR_DTE_LE_14 | USD 12.06 | USD -76.64 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 193 | 62.18% | USD -73.98 | USD -14,279.00 | USD -4,723.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 193 | 61.14% | USD -83.08 | USD -16,035.30 | USD -4,732.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 193 | 60.10% | USD -108.98 | USD -21,034.00 | USD -4,758.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 193 | 60.10% | USD -118.08 | USD -22,790.30 | USD -4,767.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 193 | 59.59% | USD -143.98 | USD -27,789.00 | USD -4,793.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 193 | 59.59% | USD -153.08 | USD -29,545.30 | USD -4,802.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 193 | 54.92% | USD -213.98 | USD -41,299.00 | USD -4,863.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 193 | 53.37% | USD -223.08 | USD -43,055.30 | USD -4,872.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 62.18% | USD -73.98 | USD -14,279.00 | USD -4,723.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 61.14% | USD -83.08 | USD -16,035.30 | USD -4,732.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 60.10% | USD -108.98 | USD -21,034.00 | USD -4,758.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 60.10% | USD -118.08 | USD -22,790.30 | USD -4,767.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 59.59% | USD -143.98 | USD -27,789.00 | USD -4,793.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 59.59% | USD -153.08 | USD -29,545.30 | USD -4,802.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 54.92% | USD -213.98 | USD -41,299.00 | USD -4,863.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 53.37% | USD -223.08 | USD -43,055.30 | USD -4,872.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 61.34% | USD -68.31 | USD -13,253.00 | USD -4,047.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 60.82% | USD -77.41 | USD -15,018.40 | USD -4,056.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 59.79% | USD -103.31 | USD -20,043.00 | USD -4,082.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 59.79% | USD -112.41 | USD -21,808.40 | USD -4,091.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 57.22% | USD -138.31 | USD -26,833.00 | USD -4,117.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 57.22% | USD -147.41 | USD -28,598.40 | USD -4,126.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 54.12% | USD -208.31 | USD -40,413.00 | USD -4,187.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 53.61% | USD -217.41 | USD -42,178.40 | USD -4,196.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 138 | 60.87% | USD -369.99 | USD -51,059.00 | USD -5,585.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 138 | 60.87% | USD -379.09 | USD -52,314.80 | USD -5,594.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 138 | 60.87% | USD -404.99 | USD -55,889.00 | USD -5,620.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 138 | 60.14% | USD -414.09 | USD -57,144.80 | USD -5,629.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 138 | 60.14% | USD -439.99 | USD -60,719.00 | USD -5,655.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 138 | 60.14% | USD -449.09 | USD -61,974.80 | USD -5,664.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 138 | 55.80% | USD -509.99 | USD -70,379.00 | USD -5,725.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 138 | 55.80% | USD -519.09 | USD -71,634.80 | USD -5,734.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 174 | 64.37% | USD -250.87 | USD -43,652.00 | USD -6,602.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 174 | 64.37% | USD -259.97 | USD -45,235.40 | USD -6,611.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 174 | 63.79% | USD -285.87 | USD -49,742.00 | USD -6,637.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 174 | 63.22% | USD -294.97 | USD -51,325.40 | USD -6,646.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 174 | 63.22% | USD -320.87 | USD -55,832.00 | USD -6,672.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 174 | 62.07% | USD -329.97 | USD -57,415.40 | USD -6,681.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 174 | 58.62% | USD -390.87 | USD -68,012.00 | USD -6,742.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 174 | 58.05% | USD -399.97 | USD -69,595.40 | USD -6,751.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 61.86% | USD -64.58 | USD -12,529.00 | USD -4,047.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 61.34% | USD -73.68 | USD -14,294.40 | USD -4,056.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 60.31% | USD -99.58 | USD -19,319.00 | USD -4,082.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 60.31% | USD -108.68 | USD -21,084.40 | USD -4,091.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 57.73% | USD -134.58 | USD -26,109.00 | USD -4,117.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 57.73% | USD -143.68 | USD -27,874.40 | USD -4,126.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 54.64% | USD -204.58 | USD -39,689.00 | USD -4,187.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 54.12% | USD -213.68 | USD -41,454.40 | USD -4,196.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 5 | 40.00% | USD -1,834.00 | USD -9,170.00 | USD -5,471.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 5 | 40.00% | USD -1,843.10 | USD -9,215.50 | USD -5,480.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 5 | 40.00% | USD -1,869.00 | USD -9,345.00 | USD -5,506.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 5 | 40.00% | USD -1,878.10 | USD -9,390.50 | USD -5,515.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 5 | 40.00% | USD -1,904.00 | USD -9,520.00 | USD -5,541.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 5 | 40.00% | USD -1,913.10 | USD -9,565.50 | USD -5,550.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 5 | 20.00% | USD -1,974.00 | USD -9,870.00 | USD -5,611.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 5 | 20.00% | USD -1,983.10 | USD -9,915.50 | USD -5,620.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 171 | 63.16% | USD -277.89 | USD -47,519.00 | USD -6,602.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 171 | 63.16% | USD -286.99 | USD -49,075.10 | USD -6,611.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 171 | 62.57% | USD -312.89 | USD -53,504.00 | USD -6,637.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 171 | 61.99% | USD -321.99 | USD -55,060.10 | USD -6,646.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 171 | 61.99% | USD -347.89 | USD -59,489.00 | USD -6,672.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 171 | 60.82% | USD -356.99 | USD -61,045.10 | USD -6,681.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 171 | 57.31% | USD -417.89 | USD -71,459.00 | USD -6,742.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 171 | 56.73% | USD -426.99 | USD -73,015.10 | USD -6,751.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 61.86% | USD -64.58 | USD -12,529.00 | USD -4,047.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 61.34% | USD -73.68 | USD -14,294.40 | USD -4,056.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 60.31% | USD -99.58 | USD -19,319.00 | USD -4,082.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 60.31% | USD -108.68 | USD -21,084.40 | USD -4,091.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 57.73% | USD -134.58 | USD -26,109.00 | USD -4,117.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 57.73% | USD -143.68 | USD -27,874.40 | USD -4,126.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 54.64% | USD -204.58 | USD -39,689.00 | USD -4,187.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 54.12% | USD -213.68 | USD -41,454.40 | USD -4,196.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 171 | 63.16% | USD -277.89 | USD -47,519.00 | USD -6,602.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 171 | 63.16% | USD -286.99 | USD -49,075.10 | USD -6,611.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 171 | 62.57% | USD -312.89 | USD -53,504.00 | USD -6,637.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 171 | 61.99% | USD -321.99 | USD -55,060.10 | USD -6,646.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 171 | 61.99% | USD -347.89 | USD -59,489.00 | USD -6,672.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 171 | 60.82% | USD -356.99 | USD -61,045.10 | USD -6,681.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 171 | 57.31% | USD -417.89 | USD -71,459.00 | USD -6,742.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 171 | 56.73% | USD -426.99 | USD -73,015.10 | USD -6,751.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 61.86% | USD -64.58 | USD -12,529.00 | USD -4,047.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 61.34% | USD -73.68 | USD -14,294.40 | USD -4,056.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 60.31% | USD -99.58 | USD -19,319.00 | USD -4,082.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 60.31% | USD -108.68 | USD -21,084.40 | USD -4,091.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 57.73% | USD -134.58 | USD -26,109.00 | USD -4,117.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 57.73% | USD -143.68 | USD -27,874.40 | USD -4,126.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 54.64% | USD -204.58 | USD -39,689.00 | USD -4,187.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 54.12% | USD -213.68 | USD -41,454.40 | USD -4,196.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 193/195 (2) | 27.98% (22.12–34.69%) | USD -30.88 | USD -5,960.80 | USD -625.60 |
| HOLD_5_SESSIONS | 1 : 6 | 193/195 (2) | 59.59% (52.54–66.26%) | USD -153.08 | USD -29,545.30 | USD -4,802.10 |
| HOLD_5_SESSIONS | 6 : 1 | 193/195 (2) | 30.05% (24.02–36.86%) | USD -63.11 | USD -12,180.30 | USD -1,742.10 |
| HOLD_5_SESSIONS | 5 : 5 | 193/195 (2) | 27.98% (22.12–34.69%) | USD -154.42 | USD -29,804.00 | USD -3,128.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 193/195 (2) | 27.98% (22.12–34.69%) | USD -30.88 | USD -5,960.80 | USD -625.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 193/195 (2) | 59.59% (52.54–66.26%) | USD -153.08 | USD -29,545.30 | USD -4,802.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 193/195 (2) | 30.05% (24.02–36.86%) | USD -63.11 | USD -12,180.30 | USD -1,742.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 193/195 (2) | 27.98% (22.12–34.69%) | USD -154.42 | USD -29,804.00 | USD -3,128.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -28.11 | USD -5,452.40 | USD -625.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 57.22% (50.18–63.97%) | USD -147.41 | USD -28,598.40 | USD -4,126.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 30.93% (24.85–37.75%) | USD -49.32 | USD -9,568.40 | USD -1,966.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -140.53 | USD -27,262.00 | USD -3,128.00 |
| HOLD_10_SESSIONS | 1 : 1 | 138/195 (57) | 31.16% (24.03–39.31%) | USD -23.86 | USD -3,292.80 | USD -967.60 |
| HOLD_10_SESSIONS | 1 : 6 | 138/195 (57) | 60.14% (51.81–67.93%) | USD -449.09 | USD -61,974.80 | USD -5,664.10 |
| HOLD_10_SESSIONS | 6 : 1 | 138/195 (57) | 33.33% (26.01–41.56%) | USD 282.07 | USD 38,925.20 | USD -2,486.10 |
| HOLD_10_SESSIONS | 5 : 5 | 138/195 (57) | 31.16% (24.03–39.31%) | USD -119.30 | USD -16,464.00 | USD -4,838.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 174/195 (21) | 22.41% (16.85–29.17%) | USD -33.47 | USD -5,824.40 | USD -1,099.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 174/195 (21) | 62.07% (54.67–68.94%) | USD -329.97 | USD -57,415.40 | USD -6,681.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 174/195 (21) | 31.03% (24.63–38.26%) | USD 95.66 | USD 16,644.60 | USD -2,130.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 174/195 (21) | 22.41% (16.85–29.17%) | USD -167.37 | USD -29,122.00 | USD -5,498.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -23.32 | USD -4,523.40 | USD -625.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 57.73% (50.70–64.47%) | USD -143.68 | USD -27,874.40 | USD -4,126.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 31.96% (25.80–38.82%) | USD -19.53 | USD -3,789.40 | USD -1,966.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -116.58 | USD -22,617.00 | USD -3,128.00 |
| HOLD_15_SESSIONS | 1 : 1 | 5/195 (190) | 60.00% (23.07–88.24%) | USD 335.40 | USD 1,677.00 | USD -212.60 |
| HOLD_15_SESSIONS | 1 : 6 | 5/195 (190) | 40.00% (11.76–76.93%) | USD -1,913.10 | USD -9,565.50 | USD -5,550.10 |
| HOLD_15_SESSIONS | 6 : 1 | 5/195 (190) | 80.00% (37.55–96.38%) | USD 4,260.90 | USD 21,304.50 | USD -181.10 |
| HOLD_15_SESSIONS | 5 : 5 | 5/195 (190) | 60.00% (23.07–88.24%) | USD 1,677.00 | USD 8,385.00 | USD -1,063.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 171/195 (24) | 23.98% (18.19–30.90%) | USD -31.22 | USD -5,338.60 | USD -1,099.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 171/195 (24) | 60.82% (53.34–67.82%) | USD -356.99 | USD -61,045.10 | USD -6,681.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 171/195 (24) | 32.16% (25.62–39.49%) | USD 138.45 | USD 23,674.90 | USD -2,130.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 171/195 (24) | 23.98% (18.19–30.90%) | USD -156.10 | USD -26,693.00 | USD -5,498.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -23.32 | USD -4,523.40 | USD -625.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 57.73% (50.70–64.47%) | USD -143.68 | USD -27,874.40 | USD -4,126.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 31.96% (25.80–38.82%) | USD -19.53 | USD -3,789.40 | USD -1,966.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -116.58 | USD -22,617.00 | USD -3,128.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/195 (195) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 171/195 (24) | 23.98% (18.19–30.90%) | USD -31.22 | USD -5,338.60 | USD -1,099.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 171/195 (24) | 60.82% (53.34–67.82%) | USD -356.99 | USD -61,045.10 | USD -6,681.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 171/195 (24) | 32.16% (25.62–39.49%) | USD 138.45 | USD 23,674.90 | USD -2,130.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 171/195 (24) | 23.98% (18.19–30.90%) | USD -156.10 | USD -26,693.00 | USD -5,498.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -23.32 | USD -4,523.40 | USD -625.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 57.73% (50.70–64.47%) | USD -143.68 | USD -27,874.40 | USD -4,126.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 31.96% (25.80–38.82%) | USD -19.53 | USD -3,789.40 | USD -1,966.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 25.26% (19.66–31.81%) | USD -116.58 | USD -22,617.00 | USD -3,128.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -75% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -50% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -40% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -30% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -25% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -20% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -15% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -10% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| -5% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| 0% | 195/195 | 100.00% | USD 668.46 | USD 33.45 |
| 5% | 29/195 | 14.87% | USD -4,437.86 | USD -12,415.05 |
| 10% | 1/195 | 0.51% | USD -15,038.47 | USD -29,223.55 |
| 20% | 1/195 | 0.51% | USD -36,587.85 | USD -62,840.55 |

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