# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 296.22 / USD 1,727.63; mean absolute mismatch USD 1,431.41; mean match score 17.25%.
- Actual selected contract ratios: {'1:6': 194}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 194; entered cohorts: 194; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 193/194 | 148/45/0 | 76.68% (70.23–82.09%) | USD 119.49 | USD 484.90 | USD 23,060.70 | USD -19,371.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 193/194 | 148/45/0 | 76.68% (70.23–82.09%) | USD 119.49 | USD 484.90 | USD 23,060.70 | USD -19,371.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 193/194 | 143/50/0 | 74.09% (67.48–79.76%) | USD 175.79 | USD 373.90 | USD 33,927.70 | USD -11,599.10 | 1 |
| HOLD_10_SESSIONS | 161/194 | 132/29/0 | 81.99% (75.33–87.16%) | USD -117.24 | USD 807.90 | USD -18,875.10 | USD -26,010.10 | 33 |
| HOLD_10_OR_DTE_LE_7 | 192/194 | 160/32/0 | 83.33% (77.42–87.94%) | USD 146.56 | USD 765.40 | USD 28,139.80 | USD -23,526.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 193/194 | 142/51/0 | 73.58% (66.94–79.29%) | USD 188.69 | USD 373.90 | USD 36,416.70 | USD -11,599.10 | 1 |
| HOLD_15_SESSIONS | 2/194 | 1/1/0 | 50.00% (9.45–90.55%) | USD -1,909.60 | USD -1,909.60 | USD -3,819.20 | USD -4,904.10 | 192 |
| HOLD_15_OR_DTE_LE_7 | 191/194 | 160/31/0 | 83.77% (77.88–88.32%) | USD 132.20 | USD 761.90 | USD 25,250.90 | USD -23,526.10 | 3 |
| HOLD_15_OR_DTE_LE_14 | 193/194 | 142/51/0 | 73.58% (66.94–79.29%) | USD 188.69 | USD 373.90 | USD 36,416.70 | USD -11,599.10 | 1 |
| HOLD_20_SESSIONS | 0/194 | 0/0/0 | — | — | — | — | — | 194 |
| HOLD_20_OR_DTE_LE_7 | 191/194 | 160/31/0 | 83.77% (77.88–88.32%) | USD 132.20 | USD 761.90 | USD 25,250.90 | USD -23,526.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 193/194 | 142/51/0 | 73.58% (66.94–79.29%) | USD 188.69 | USD 373.90 | USD 36,416.70 | USD -11,599.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -68.77 | USD 267.36 |
| HOLD_5_OR_DTE_LE_7 | USD -68.77 | USD 267.36 |
| HOLD_5_OR_DTE_LE_14 | USD -59.88 | USD 314.77 |
| HOLD_10_SESSIONS | USD -46.48 | USD 8.35 |
| HOLD_10_OR_DTE_LE_7 | USD -83.28 | USD 308.94 |
| HOLD_10_OR_DTE_LE_14 | USD -62.77 | USD 330.56 |
| HOLD_15_SESSIONS | USD 719.50 | USD -2,550.00 |
| HOLD_15_OR_DTE_LE_7 | USD -80.12 | USD 291.42 |
| HOLD_15_OR_DTE_LE_14 | USD -62.77 | USD 330.56 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -80.12 | USD 291.42 |
| HOLD_20_OR_DTE_LE_14 | USD -62.77 | USD 330.56 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 193 | 77.20% | USD 198.59 | USD 38,327.00 | USD -19,292.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 193 | 77.20% | USD 189.49 | USD 36,570.70 | USD -19,301.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 193 | 77.20% | USD 163.59 | USD 31,572.00 | USD -19,327.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 193 | 77.20% | USD 154.49 | USD 29,815.70 | USD -19,336.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 193 | 77.20% | USD 128.59 | USD 24,817.00 | USD -19,362.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 193 | 76.68% | USD 119.49 | USD 23,060.70 | USD -19,371.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 193 | 73.06% | USD 58.59 | USD 11,307.00 | USD -19,432.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 193 | 73.06% | USD 49.49 | USD 9,550.70 | USD -19,441.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 77.20% | USD 198.59 | USD 38,327.00 | USD -19,292.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 77.20% | USD 189.49 | USD 36,570.70 | USD -19,301.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 77.20% | USD 163.59 | USD 31,572.00 | USD -19,327.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 77.20% | USD 154.49 | USD 29,815.70 | USD -19,336.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 77.20% | USD 128.59 | USD 24,817.00 | USD -19,362.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 76.68% | USD 119.49 | USD 23,060.70 | USD -19,371.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 73.06% | USD 58.59 | USD 11,307.00 | USD -19,432.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 73.06% | USD 49.49 | USD 9,550.70 | USD -19,441.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 75.65% | USD 254.89 | USD 49,194.00 | USD -11,520.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 75.65% | USD 245.79 | USD 47,437.70 | USD -11,529.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 75.65% | USD 219.89 | USD 42,439.00 | USD -11,555.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 75.65% | USD 210.79 | USD 40,682.70 | USD -11,564.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 75.13% | USD 184.89 | USD 35,684.00 | USD -11,590.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 74.09% | USD 175.79 | USD 33,927.70 | USD -11,599.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 69.95% | USD 114.89 | USD 22,174.00 | USD -11,660.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 69.95% | USD 105.79 | USD 20,417.70 | USD -11,669.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 161 | 81.99% | USD -38.14 | USD -6,140.00 | USD -25,931.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 161 | 81.99% | USD -47.24 | USD -7,605.10 | USD -25,940.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 161 | 81.99% | USD -73.14 | USD -11,775.00 | USD -25,966.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 161 | 81.99% | USD -82.24 | USD -13,240.10 | USD -25,975.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 161 | 81.99% | USD -108.14 | USD -17,410.00 | USD -26,001.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 161 | 81.99% | USD -117.24 | USD -18,875.10 | USD -26,010.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 161 | 81.99% | USD -178.14 | USD -28,680.00 | USD -26,071.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 161 | 81.99% | USD -187.24 | USD -30,145.10 | USD -26,080.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 84.90% | USD 225.66 | USD 43,327.00 | USD -23,447.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 84.90% | USD 216.56 | USD 41,579.80 | USD -23,456.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 83.85% | USD 190.66 | USD 36,607.00 | USD -23,482.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 83.85% | USD 181.56 | USD 34,859.80 | USD -23,491.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 83.33% | USD 155.66 | USD 29,887.00 | USD -23,517.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 83.33% | USD 146.56 | USD 28,139.80 | USD -23,526.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 82.81% | USD 85.66 | USD 16,447.00 | USD -23,587.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 82.81% | USD 76.56 | USD 14,699.80 | USD -23,596.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 75.13% | USD 267.79 | USD 51,683.00 | USD -11,520.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 75.13% | USD 258.69 | USD 49,926.70 | USD -11,529.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 75.13% | USD 232.79 | USD 44,928.00 | USD -11,555.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 75.13% | USD 223.69 | USD 43,171.70 | USD -11,564.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 74.61% | USD 197.79 | USD 38,173.00 | USD -11,590.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 73.58% | USD 188.69 | USD 36,416.70 | USD -11,599.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 69.95% | USD 127.79 | USD 24,663.00 | USD -11,660.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 69.95% | USD 118.69 | USD 22,906.70 | USD -11,669.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 2 | 50.00% | USD -1,830.50 | USD -3,661.00 | USD -4,825.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 2 | 50.00% | USD -1,839.60 | USD -3,679.20 | USD -4,834.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 2 | 50.00% | USD -1,865.50 | USD -3,731.00 | USD -4,860.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 2 | 50.00% | USD -1,874.60 | USD -3,749.20 | USD -4,869.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 2 | 50.00% | USD -1,900.50 | USD -3,801.00 | USD -4,895.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 2 | 50.00% | USD -1,909.60 | USD -3,819.20 | USD -4,904.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 2 | 50.00% | USD -1,970.50 | USD -3,941.00 | USD -4,965.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 2 | 50.00% | USD -1,979.60 | USD -3,959.20 | USD -4,974.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 85.34% | USD 211.30 | USD 40,359.00 | USD -23,447.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 85.34% | USD 202.20 | USD 38,620.90 | USD -23,456.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 84.29% | USD 176.30 | USD 33,674.00 | USD -23,482.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 84.29% | USD 167.20 | USD 31,935.90 | USD -23,491.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 83.77% | USD 141.30 | USD 26,989.00 | USD -23,517.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 83.77% | USD 132.20 | USD 25,250.90 | USD -23,526.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 83.25% | USD 71.30 | USD 13,619.00 | USD -23,587.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 83.25% | USD 62.20 | USD 11,880.90 | USD -23,596.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 75.13% | USD 267.79 | USD 51,683.00 | USD -11,520.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 75.13% | USD 258.69 | USD 49,926.70 | USD -11,529.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 75.13% | USD 232.79 | USD 44,928.00 | USD -11,555.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 75.13% | USD 223.69 | USD 43,171.70 | USD -11,564.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 74.61% | USD 197.79 | USD 38,173.00 | USD -11,590.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 73.58% | USD 188.69 | USD 36,416.70 | USD -11,599.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 69.95% | USD 127.79 | USD 24,663.00 | USD -11,660.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 69.95% | USD 118.69 | USD 22,906.70 | USD -11,669.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 85.34% | USD 211.30 | USD 40,359.00 | USD -23,447.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 85.34% | USD 202.20 | USD 38,620.90 | USD -23,456.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 84.29% | USD 176.30 | USD 33,674.00 | USD -23,482.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 84.29% | USD 167.20 | USD 31,935.90 | USD -23,491.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 83.77% | USD 141.30 | USD 26,989.00 | USD -23,517.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 83.77% | USD 132.20 | USD 25,250.90 | USD -23,526.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 83.25% | USD 71.30 | USD 13,619.00 | USD -23,587.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 83.25% | USD 62.20 | USD 11,880.90 | USD -23,596.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 193 | 75.13% | USD 267.79 | USD 51,683.00 | USD -11,520.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 193 | 75.13% | USD 258.69 | USD 49,926.70 | USD -11,529.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 193 | 75.13% | USD 232.79 | USD 44,928.00 | USD -11,555.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 193 | 75.13% | USD 223.69 | USD 43,171.70 | USD -11,564.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 193 | 74.61% | USD 197.79 | USD 38,173.00 | USD -11,590.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 193 | 73.58% | USD 188.69 | USD 36,416.70 | USD -11,599.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 193 | 69.95% | USD 127.79 | USD 24,663.00 | USD -11,660.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 193 | 69.95% | USD 118.69 | USD 22,906.70 | USD -11,669.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 193/194 (1) | 28.50% (22.60–35.24%) | USD -46.81 | USD -9,034.80 | USD -1,699.60 |
| HOLD_5_SESSIONS | 1 : 6 | 193/194 (1) | 76.68% (70.23–82.09%) | USD 119.49 | USD 23,060.70 | USD -19,371.10 |
| HOLD_5_SESSIONS | 6 : 1 | 193/194 (1) | 20.21% (15.15–26.43%) | USD -447.17 | USD -86,304.30 | USD -3,512.10 |
| HOLD_5_SESSIONS | 5 : 5 | 193/194 (1) | 28.50% (22.60–35.24%) | USD -234.06 | USD -45,174.00 | USD -8,498.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 193/194 (1) | 28.50% (22.60–35.24%) | USD -46.81 | USD -9,034.80 | USD -1,699.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 193/194 (1) | 76.68% (70.23–82.09%) | USD 119.49 | USD 23,060.70 | USD -19,371.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 193/194 (1) | 20.21% (15.15–26.43%) | USD -447.17 | USD -86,304.30 | USD -3,512.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 193/194 (1) | 28.50% (22.60–35.24%) | USD -234.06 | USD -45,174.00 | USD -8,498.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -30.01 | USD -5,792.80 | USD -698.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 74.09% (67.48–79.76%) | USD 175.79 | USD 33,927.70 | USD -11,599.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 23.83% (18.37–30.32%) | USD -385.89 | USD -74,477.30 | USD -4,181.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -150.07 | USD -28,964.00 | USD -3,493.00 |
| HOLD_10_SESSIONS | 1 : 1 | 161/194 (33) | 27.33% (21.03–34.68%) | USD -67.69 | USD -10,898.60 | USD -2,591.60 |
| HOLD_10_SESSIONS | 1 : 6 | 161/194 (33) | 81.99% (75.33–87.16%) | USD -117.24 | USD -18,875.10 | USD -26,010.10 |
| HOLD_10_SESSIONS | 6 : 1 | 161/194 (33) | 18.01% (12.84–24.67%) | USD -356.62 | USD -57,415.10 | USD -6,265.10 |
| HOLD_10_SESSIONS | 5 : 5 | 161/194 (33) | 27.33% (21.03–34.68%) | USD -338.47 | USD -54,493.00 | USD -12,958.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 192/194 (2) | 25.52% (19.88–32.13%) | USD -54.39 | USD -10,442.20 | USD -2,379.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 192/194 (2) | 83.33% (77.42–87.94%) | USD 146.56 | USD 28,139.80 | USD -23,526.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 192/194 (2) | 16.15% (11.61–22.01%) | USD -527.27 | USD -101,235.20 | USD -6,166.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 192/194 (2) | 25.52% (19.88–32.13%) | USD -271.93 | USD -52,211.00 | USD -11,898.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -30.28 | USD -5,843.80 | USD -698.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 73.58% (66.94–79.29%) | USD 188.69 | USD 36,416.70 | USD -11,599.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 22.80% (17.44–29.21%) | USD -400.64 | USD -77,323.30 | USD -4,181.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -151.39 | USD -29,219.00 | USD -3,493.00 |
| HOLD_15_SESSIONS | 1 : 1 | 2/194 (192) | 100.00% (34.24–100.00%) | USD 271.90 | USD 543.80 | USD 177.40 |
| HOLD_15_SESSIONS | 1 : 6 | 2/194 (192) | 50.00% (9.45–90.55%) | USD -1,909.60 | USD -3,819.20 | USD -4,904.10 |
| HOLD_15_SESSIONS | 6 : 1 | 2/194 (192) | 100.00% (34.24–100.00%) | USD 3,812.90 | USD 7,625.80 | USD 1,479.90 |
| HOLD_15_SESSIONS | 5 : 5 | 2/194 (192) | 100.00% (34.24–100.00%) | USD 1,359.50 | USD 2,719.00 | USD 887.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 191/194 (3) | 26.70% (20.93–33.39%) | USD -54.15 | USD -10,342.60 | USD -2,379.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 191/194 (3) | 83.77% (77.88–88.32%) | USD 132.20 | USD 25,250.90 | USD -23,526.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 191/194 (3) | 15.71% (11.23–21.54%) | USD -511.25 | USD -97,649.10 | USD -6,166.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 191/194 (3) | 26.70% (20.93–33.39%) | USD -270.75 | USD -51,713.00 | USD -11,898.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -30.28 | USD -5,843.80 | USD -698.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 73.58% (66.94–79.29%) | USD 188.69 | USD 36,416.70 | USD -11,599.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 22.80% (17.44–29.21%) | USD -400.64 | USD -77,323.30 | USD -4,181.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -151.39 | USD -29,219.00 | USD -3,493.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/194 (194) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 191/194 (3) | 26.70% (20.93–33.39%) | USD -54.15 | USD -10,342.60 | USD -2,379.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 191/194 (3) | 83.77% (77.88–88.32%) | USD 132.20 | USD 25,250.90 | USD -23,526.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 191/194 (3) | 15.71% (11.23–21.54%) | USD -511.25 | USD -97,649.10 | USD -6,166.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 191/194 (3) | 26.70% (20.93–33.39%) | USD -270.75 | USD -51,713.00 | USD -11,898.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -30.28 | USD -5,843.80 | USD -698.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 193/194 (1) | 73.58% (66.94–79.29%) | USD 188.69 | USD 36,416.70 | USD -11,599.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 193/194 (1) | 22.80% (17.44–29.21%) | USD -400.64 | USD -77,323.30 | USD -4,181.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 193/194 (1) | 29.02% (23.07–35.78%) | USD -151.39 | USD -29,219.00 | USD -3,493.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/194 | 0.00% | USD -208,888.78 | USD -338,833.55 |
| -75% | 0/194 | 0.00% | USD -154,868.69 | USD -252,003.80 |
| -50% | 0/194 | 0.00% | USD -100,848.59 | USD -165,174.05 |
| -40% | 0/194 | 0.00% | USD -79,240.55 | USD -130,442.15 |
| -30% | 0/194 | 0.00% | USD -57,632.51 | USD -95,710.25 |
| -25% | 0/194 | 0.00% | USD -46,828.50 | USD -78,344.30 |
| -20% | 0/194 | 0.00% | USD -36,024.48 | USD -60,978.35 |
| -15% | 0/194 | 0.00% | USD -25,220.46 | USD -43,612.40 |
| -10% | 2/194 | 1.03% | USD -14,416.44 | USD -26,710.55 |
| -5% | 25/194 | 12.89% | USD -3,811.97 | USD -11,182.05 |
| 0% | 194/194 | 100.00% | USD 1,383.73 | USD 315.45 |
| 5% | 194/194 | 100.00% | USD 1,391.86 | USD 315.45 |
| 10% | 194/194 | 100.00% | USD 1,391.86 | USD 315.45 |
| 20% | 194/194 | 100.00% | USD 1,391.86 | USD 315.45 |

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