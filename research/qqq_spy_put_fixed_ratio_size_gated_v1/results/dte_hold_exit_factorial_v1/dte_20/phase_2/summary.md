# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 302.45 / USD 1,766.83; mean absolute mismatch USD 1,464.38; mean match score 17.11%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/195 | 146/48/0 | 75.26% (68.73–80.80%) | USD 166.85 | USD 464.90 | USD 32,368.60 | USD -12,394.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 194/195 | 146/48/0 | 75.26% (68.73–80.80%) | USD 166.85 | USD 464.90 | USD 32,368.60 | USD -12,394.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 139/55/0 | 71.65% (64.93–77.52%) | USD 77.87 | USD 283.40 | USD 15,106.60 | USD -6,450.10 | 1 |
| HOLD_10_SESSIONS | 166/195 | 134/32/0 | 80.72% (74.05–86.00%) | USD -25.64 | USD 762.90 | USD -4,256.60 | USD -20,563.10 | 29 |
| HOLD_10_OR_DTE_LE_7 | 192/195 | 153/39/0 | 79.69% (73.44–84.77%) | USD 59.24 | USD 745.90 | USD 11,374.80 | USD -20,563.10 | 3 |
| HOLD_10_OR_DTE_LE_14 | 194/195 | 142/52/0 | 73.20% (66.56–78.93%) | USD 93.04 | USD 330.90 | USD 18,049.60 | USD -6,450.10 | 1 |
| HOLD_15_SESSIONS | 4/195 | 1/3/0 | 25.00% (4.56–69.94%) | USD -5,695.10 | USD -3,363.60 | USD -22,780.40 | USD -17,436.10 | 191 |
| HOLD_15_OR_DTE_LE_7 | 192/195 | 153/39/0 | 79.69% (73.44–84.77%) | USD 75.57 | USD 759.40 | USD 14,509.80 | USD -19,685.10 | 3 |
| HOLD_15_OR_DTE_LE_14 | 194/195 | 142/52/0 | 73.20% (66.56–78.93%) | USD 93.04 | USD 330.90 | USD 18,049.60 | USD -6,450.10 | 1 |
| HOLD_20_SESSIONS | 0/195 | 0/0/0 | — | — | — | — | — | 195 |
| HOLD_20_OR_DTE_LE_7 | 192/195 | 153/39/0 | 79.69% (73.44–84.77%) | USD 75.57 | USD 759.40 | USD 14,509.80 | USD -19,685.10 | 3 |
| HOLD_20_OR_DTE_LE_14 | 194/195 | 142/52/0 | 73.20% (66.56–78.93%) | USD 93.04 | USD 330.90 | USD 18,049.60 | USD -6,450.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -70.07 | USD 316.02 |
| HOLD_5_OR_DTE_LE_7 | USD -70.07 | USD 316.02 |
| HOLD_5_OR_DTE_LE_14 | USD -59.25 | USD 216.22 |
| HOLD_10_SESSIONS | USD -61.08 | USD 114.54 |
| HOLD_10_OR_DTE_LE_7 | USD -62.94 | USD 201.28 |
| HOLD_10_OR_DTE_LE_14 | USD -59.76 | USD 231.90 |
| HOLD_15_SESSIONS | USD 922.50 | USD -6,538.50 |
| HOLD_15_OR_DTE_LE_7 | USD -68.36 | USD 223.03 |
| HOLD_15_OR_DTE_LE_14 | USD -59.76 | USD 231.90 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -68.36 | USD 223.03 |
| HOLD_20_OR_DTE_LE_14 | USD -59.76 | USD 231.90 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 76.29% | USD 245.95 | USD 47,714.00 | USD -12,315.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 76.29% | USD 236.85 | USD 45,948.60 | USD -12,324.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 76.29% | USD 210.95 | USD 40,924.00 | USD -12,350.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 76.29% | USD 201.85 | USD 39,158.60 | USD -12,359.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 75.77% | USD 175.95 | USD 34,134.00 | USD -12,385.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 75.26% | USD 166.85 | USD 32,368.60 | USD -12,394.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 72.68% | USD 105.95 | USD 20,554.00 | USD -12,455.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 72.68% | USD 96.85 | USD 18,788.60 | USD -12,464.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 76.29% | USD 245.95 | USD 47,714.00 | USD -12,315.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 76.29% | USD 236.85 | USD 45,948.60 | USD -12,324.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 76.29% | USD 210.95 | USD 40,924.00 | USD -12,350.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 76.29% | USD 201.85 | USD 39,158.60 | USD -12,359.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 75.77% | USD 175.95 | USD 34,134.00 | USD -12,385.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 75.26% | USD 166.85 | USD 32,368.60 | USD -12,394.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 72.68% | USD 105.95 | USD 20,554.00 | USD -12,455.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 72.68% | USD 96.85 | USD 18,788.60 | USD -12,464.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 74.23% | USD 156.97 | USD 30,452.00 | USD -6,371.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 74.23% | USD 147.87 | USD 28,686.60 | USD -6,380.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 73.71% | USD 121.97 | USD 23,662.00 | USD -6,406.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 72.68% | USD 112.87 | USD 21,896.60 | USD -6,415.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 71.65% | USD 86.97 | USD 16,872.00 | USD -6,441.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 71.65% | USD 77.87 | USD 15,106.60 | USD -6,450.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 69.07% | USD 16.97 | USD 3,292.00 | USD -6,511.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 69.07% | USD 7.87 | USD 1,526.60 | USD -6,520.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 166 | 81.33% | USD 53.46 | USD 8,874.00 | USD -20,484.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 166 | 80.72% | USD 44.36 | USD 7,363.40 | USD -20,493.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 166 | 80.72% | USD 18.46 | USD 3,064.00 | USD -20,519.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 166 | 80.72% | USD 9.36 | USD 1,553.40 | USD -20,528.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 166 | 80.72% | USD -16.54 | USD -2,746.00 | USD -20,554.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 166 | 80.72% | USD -25.64 | USD -4,256.60 | USD -20,563.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 166 | 78.92% | USD -86.54 | USD -14,366.00 | USD -20,624.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 166 | 78.31% | USD -95.64 | USD -15,876.60 | USD -20,633.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 80.21% | USD 138.34 | USD 26,562.00 | USD -20,484.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 80.21% | USD 129.24 | USD 24,814.80 | USD -20,493.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 79.69% | USD 103.34 | USD 19,842.00 | USD -20,519.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 79.69% | USD 94.24 | USD 18,094.80 | USD -20,528.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 79.69% | USD 68.34 | USD 13,122.00 | USD -20,554.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 79.69% | USD 59.24 | USD 11,374.80 | USD -20,563.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 78.65% | USD -1.66 | USD -318.00 | USD -20,624.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 78.65% | USD -10.76 | USD -2,065.20 | USD -20,633.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 75.77% | USD 172.14 | USD 33,395.00 | USD -6,371.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 75.77% | USD 163.04 | USD 31,629.60 | USD -6,380.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 75.26% | USD 137.14 | USD 26,605.00 | USD -6,406.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 74.23% | USD 128.04 | USD 24,839.60 | USD -6,415.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 73.20% | USD 102.14 | USD 19,815.00 | USD -6,441.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 73.20% | USD 93.04 | USD 18,049.60 | USD -6,450.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 70.62% | USD 32.14 | USD 6,235.00 | USD -6,511.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.62% | USD 23.04 | USD 4,469.60 | USD -6,520.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 4 | 25.00% | USD -5,616.00 | USD -22,464.00 | USD -17,357.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 4 | 25.00% | USD -5,625.10 | USD -22,500.40 | USD -17,366.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 4 | 25.00% | USD -5,651.00 | USD -22,604.00 | USD -17,392.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 4 | 25.00% | USD -5,660.10 | USD -22,640.40 | USD -17,401.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 4 | 25.00% | USD -5,686.00 | USD -22,744.00 | USD -17,427.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 4 | 25.00% | USD -5,695.10 | USD -22,780.40 | USD -17,436.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 4 | 25.00% | USD -5,756.00 | USD -23,024.00 | USD -17,497.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 4 | 25.00% | USD -5,765.10 | USD -23,060.40 | USD -17,506.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 80.21% | USD 154.67 | USD 29,697.00 | USD -19,606.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 80.21% | USD 145.57 | USD 27,949.80 | USD -19,615.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 79.69% | USD 119.67 | USD 22,977.00 | USD -19,641.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 79.69% | USD 110.57 | USD 21,229.80 | USD -19,650.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 79.69% | USD 84.67 | USD 16,257.00 | USD -19,676.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 79.69% | USD 75.57 | USD 14,509.80 | USD -19,685.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 79.69% | USD 14.67 | USD 2,817.00 | USD -19,746.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 79.69% | USD 5.57 | USD 1,069.80 | USD -19,755.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 75.77% | USD 172.14 | USD 33,395.00 | USD -6,371.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 75.77% | USD 163.04 | USD 31,629.60 | USD -6,380.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 75.26% | USD 137.14 | USD 26,605.00 | USD -6,406.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 74.23% | USD 128.04 | USD 24,839.60 | USD -6,415.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 73.20% | USD 102.14 | USD 19,815.00 | USD -6,441.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 73.20% | USD 93.04 | USD 18,049.60 | USD -6,450.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 70.62% | USD 32.14 | USD 6,235.00 | USD -6,511.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.62% | USD 23.04 | USD 4,469.60 | USD -6,520.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 80.21% | USD 154.67 | USD 29,697.00 | USD -19,606.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 80.21% | USD 145.57 | USD 27,949.80 | USD -19,615.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 79.69% | USD 119.67 | USD 22,977.00 | USD -19,641.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 79.69% | USD 110.57 | USD 21,229.80 | USD -19,650.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 79.69% | USD 84.67 | USD 16,257.00 | USD -19,676.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 79.69% | USD 75.57 | USD 14,509.80 | USD -19,685.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 79.69% | USD 14.67 | USD 2,817.00 | USD -19,746.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 79.69% | USD 5.57 | USD 1,069.80 | USD -19,755.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 75.77% | USD 172.14 | USD 33,395.00 | USD -6,371.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 75.77% | USD 163.04 | USD 31,629.60 | USD -6,380.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 75.26% | USD 137.14 | USD 26,605.00 | USD -6,406.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 74.23% | USD 128.04 | USD 24,839.60 | USD -6,415.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 73.20% | USD 102.14 | USD 19,815.00 | USD -6,441.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 73.20% | USD 93.04 | USD 18,049.60 | USD -6,450.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 70.62% | USD 32.14 | USD 6,235.00 | USD -6,511.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.62% | USD 23.04 | USD 4,469.60 | USD -6,520.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/195 (1) | 29.38% (23.42–36.14%) | USD -40.00 | USD -7,760.40 | USD -721.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/195 (1) | 75.26% (68.73–80.80%) | USD 166.85 | USD 32,368.60 | USD -12,394.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/195 (1) | 20.10% (15.07–26.30%) | USD -446.86 | USD -86,691.40 | USD -5,670.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/195 (1) | 29.38% (23.42–36.14%) | USD -200.01 | USD -38,802.00 | USD -3,608.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/195 (1) | 29.38% (23.42–36.14%) | USD -40.00 | USD -7,760.40 | USD -721.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/195 (1) | 75.26% (68.73–80.80%) | USD 166.85 | USD 32,368.60 | USD -12,394.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/195 (1) | 20.10% (15.07–26.30%) | USD -446.86 | USD -86,691.40 | USD -5,670.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/195 (1) | 29.38% (23.42–36.14%) | USD -200.01 | USD -38,802.00 | USD -3,608.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -45.81 | USD -8,887.40 | USD -1,159.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 71.65% (64.93–77.52%) | USD 77.87 | USD 15,106.60 | USD -6,450.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 21.13% (15.98–27.41%) | USD -398.55 | USD -77,318.40 | USD -5,670.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -229.06 | USD -44,437.00 | USD -5,798.00 |
| HOLD_10_SESSIONS | 1 : 1 | 166/195 (29) | 29.52% (23.11–36.86%) | USD -64.59 | USD -10,722.60 | USD -1,421.60 |
| HOLD_10_SESSIONS | 1 : 6 | 166/195 (29) | 80.72% (74.05–86.00%) | USD -25.64 | USD -4,256.60 | USD -20,563.10 |
| HOLD_10_SESSIONS | 6 : 1 | 166/195 (29) | 18.67% (13.48–25.29%) | USD -426.52 | USD -70,801.60 | USD -7,232.10 |
| HOLD_10_SESSIONS | 5 : 5 | 166/195 (29) | 29.52% (23.11–36.86%) | USD -322.97 | USD -53,613.00 | USD -7,108.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 192/195 (3) | 32.29% (26.08–39.20%) | USD -51.99 | USD -9,982.20 | USD -1,524.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 192/195 (3) | 79.69% (73.44–84.77%) | USD 59.24 | USD 11,374.80 | USD -20,563.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 192/195 (3) | 19.27% (14.32–25.43%) | USD -423.18 | USD -81,250.20 | USD -7,021.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 192/195 (3) | 32.29% (26.08–39.20%) | USD -259.95 | USD -49,911.00 | USD -7,623.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -43.71 | USD -8,479.40 | USD -1,159.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 73.20% (66.56–78.93%) | USD 93.04 | USD 18,049.60 | USD -6,450.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 21.13% (15.98–27.41%) | USD -399.00 | USD -77,405.40 | USD -5,670.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -218.54 | USD -42,397.00 | USD -5,798.00 |
| HOLD_15_SESSIONS | 1 : 1 | 4/195 (191) | 25.00% (4.56–69.94%) | USD -189.85 | USD -759.40 | USD -843.60 |
| HOLD_15_SESSIONS | 1 : 6 | 4/195 (191) | 25.00% (4.56–69.94%) | USD -5,695.10 | USD -22,780.40 | USD -17,436.10 |
| HOLD_15_SESSIONS | 6 : 1 | 4/195 (191) | 50.00% (15.00–85.00%) | USD 4,366.15 | USD 17,464.60 | USD -3,067.10 |
| HOLD_15_SESSIONS | 5 : 5 | 4/195 (191) | 25.00% (4.56–69.94%) | USD -949.25 | USD -3,797.00 | USD -4,218.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 192/195 (3) | 32.29% (26.08–39.20%) | USD -53.79 | USD -10,327.20 | USD -1,524.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 192/195 (3) | 79.69% (73.44–84.77%) | USD 75.57 | USD 14,509.80 | USD -19,685.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 192/195 (3) | 18.75% (13.86–24.86%) | USD -452.08 | USD -86,800.20 | USD -7,021.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 192/195 (3) | 32.29% (26.08–39.20%) | USD -268.94 | USD -51,636.00 | USD -7,623.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -43.71 | USD -8,479.40 | USD -1,159.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 73.20% (66.56–78.93%) | USD 93.04 | USD 18,049.60 | USD -6,450.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 21.13% (15.98–27.41%) | USD -399.00 | USD -77,405.40 | USD -5,670.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -218.54 | USD -42,397.00 | USD -5,798.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/195 (195) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/195 (195) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 192/195 (3) | 32.29% (26.08–39.20%) | USD -53.79 | USD -10,327.20 | USD -1,524.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 192/195 (3) | 79.69% (73.44–84.77%) | USD 75.57 | USD 14,509.80 | USD -19,685.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 192/195 (3) | 18.75% (13.86–24.86%) | USD -452.08 | USD -86,800.20 | USD -7,021.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 192/195 (3) | 32.29% (26.08–39.20%) | USD -268.94 | USD -51,636.00 | USD -7,623.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -43.71 | USD -8,479.40 | USD -1,159.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 73.20% (66.56–78.93%) | USD 93.04 | USD 18,049.60 | USD -6,450.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 21.13% (15.98–27.41%) | USD -399.00 | USD -77,405.40 | USD -5,670.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -218.54 | USD -42,397.00 | USD -5,798.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/195 | 0.00% | USD -209,016.68 | USD -338,781.55 |
| -75% | 0/195 | 0.00% | USD -155,002.58 | USD -251,565.05 |
| -50% | 0/195 | 0.00% | USD -100,988.49 | USD -164,348.55 |
| -40% | 0/195 | 0.00% | USD -79,382.85 | USD -129,461.95 |
| -30% | 0/195 | 0.00% | USD -57,777.21 | USD -94,575.35 |
| -25% | 0/195 | 0.00% | USD -46,974.39 | USD -77,192.30 |
| -20% | 0/195 | 0.00% | USD -36,171.57 | USD -60,141.35 |
| -15% | 0/195 | 0.00% | USD -25,368.76 | USD -43,090.40 |
| -10% | 2/195 | 1.03% | USD -14,593.74 | USD -26,039.45 |
| -5% | 21/195 | 10.77% | USD -3,964.36 | USD -11,443.25 |
| 0% | 195/195 | 100.00% | USD 1,374.31 | USD 304.45 |
| 5% | 195/195 | 100.00% | USD 1,424.83 | USD 304.45 |
| 10% | 195/195 | 100.00% | USD 1,424.83 | USD 304.45 |
| 20% | 195/195 | 100.00% | USD 1,424.83 | USD 304.45 |

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