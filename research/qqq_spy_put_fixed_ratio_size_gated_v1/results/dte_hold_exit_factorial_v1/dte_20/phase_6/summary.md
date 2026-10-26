# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 266.63 / USD 1,541.17; mean absolute mismatch USD 1,274.54; mean match score 17.17%.
- Actual selected contract ratios: {'1:6': 196}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 196; entered cohorts: 196; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 195/196 | 147/48/0 | 75.38% (68.89–80.90%) | USD -69.65 | USD 462.90 | USD -13,581.50 | USD -18,773.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 195/196 | 147/48/0 | 75.38% (68.89–80.90%) | USD -69.65 | USD 462.90 | USD -13,581.50 | USD -18,773.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 195/196 | 143/52/0 | 73.33% (66.72–79.05%) | USD -48.09 | USD 352.90 | USD -9,378.50 | USD -18,773.10 | 1 |
| HOLD_10_SESSIONS | 161/196 | 134/27/0 | 83.23% (76.70–88.21%) | USD -22.76 | USD 829.90 | USD -3,664.10 | USD -30,517.10 | 35 |
| HOLD_10_OR_DTE_LE_7 | 193/196 | 157/36/0 | 81.35% (75.26–86.21%) | USD -128.26 | USD 744.90 | USD -24,753.30 | USD -30,517.10 | 3 |
| HOLD_10_OR_DTE_LE_14 | 195/196 | 143/52/0 | 73.33% (66.72–79.05%) | USD -26.33 | USD 352.90 | USD -5,133.50 | USD -18,773.10 | 1 |
| HOLD_15_SESSIONS | 4/196 | 3/1/0 | 75.00% (30.06–95.44%) | USD 602.65 | USD 723.90 | USD 2,410.60 | USD -1,061.10 | 192 |
| HOLD_15_OR_DTE_LE_7 | 192/196 | 156/36/0 | 81.25% (75.14–86.14%) | USD -145.15 | USD 728.90 | USD -27,868.20 | USD -30,517.10 | 4 |
| HOLD_15_OR_DTE_LE_14 | 195/196 | 143/52/0 | 73.33% (66.72–79.05%) | USD -26.33 | USD 352.90 | USD -5,133.50 | USD -18,773.10 | 1 |
| HOLD_20_SESSIONS | 0/196 | 0/0/0 | — | — | — | — | — | 196 |
| HOLD_20_OR_DTE_LE_7 | 192/196 | 156/36/0 | 81.25% (75.14–86.14%) | USD -145.15 | USD 728.90 | USD -27,868.20 | USD -30,517.10 | 4 |
| HOLD_20_OR_DTE_LE_14 | 195/196 | 143/52/0 | 73.33% (66.72–79.05%) | USD -26.33 | USD 352.90 | USD -5,133.50 | USD -18,773.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -27.23 | USD 36.68 |
| HOLD_5_OR_DTE_LE_7 | USD -27.23 | USD 36.68 |
| HOLD_5_OR_DTE_LE_14 | USD -32.66 | USD 63.66 |
| HOLD_10_SESSIONS | USD -64.93 | USD 121.27 |
| HOLD_10_OR_DTE_LE_7 | USD -28.54 | USD -20.61 |
| HOLD_10_OR_DTE_LE_14 | USD -37.26 | USD 90.03 |
| HOLD_15_SESSIONS | USD -111.75 | USD 793.50 |
| HOLD_15_OR_DTE_LE_7 | USD -21.86 | USD -44.19 |
| HOLD_15_OR_DTE_LE_14 | USD -37.26 | USD 90.03 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -21.86 | USD -44.19 |
| HOLD_20_OR_DTE_LE_14 | USD -37.26 | USD 90.03 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 195 | 76.41% | USD 9.45 | USD 1,843.00 | USD -18,694.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 195 | 76.41% | USD 0.35 | USD 68.50 | USD -18,703.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 195 | 76.41% | USD -25.55 | USD -4,982.00 | USD -18,729.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 195 | 75.90% | USD -34.65 | USD -6,756.50 | USD -18,738.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 195 | 75.38% | USD -60.55 | USD -11,807.00 | USD -18,764.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 195 | 75.38% | USD -69.65 | USD -13,581.50 | USD -18,773.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 195 | 73.33% | USD -130.55 | USD -25,457.00 | USD -18,834.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 195 | 72.82% | USD -139.65 | USD -27,231.50 | USD -18,843.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 195 | 76.41% | USD 9.45 | USD 1,843.00 | USD -18,694.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 195 | 76.41% | USD 0.35 | USD 68.50 | USD -18,703.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 195 | 76.41% | USD -25.55 | USD -4,982.00 | USD -18,729.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 195 | 75.90% | USD -34.65 | USD -6,756.50 | USD -18,738.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 195 | 75.38% | USD -60.55 | USD -11,807.00 | USD -18,764.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 195 | 75.38% | USD -69.65 | USD -13,581.50 | USD -18,773.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 195 | 73.33% | USD -130.55 | USD -25,457.00 | USD -18,834.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 195 | 72.82% | USD -139.65 | USD -27,231.50 | USD -18,843.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 75.90% | USD 31.01 | USD 6,046.00 | USD -18,694.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 74.87% | USD 21.91 | USD 4,271.50 | USD -18,703.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 74.36% | USD -3.99 | USD -779.00 | USD -18,729.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 74.36% | USD -13.09 | USD -2,553.50 | USD -18,738.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 73.85% | USD -38.99 | USD -7,604.00 | USD -18,764.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 73.33% | USD -48.09 | USD -9,378.50 | USD -18,773.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 67.69% | USD -108.99 | USD -21,254.00 | USD -18,834.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 67.18% | USD -118.09 | USD -23,028.50 | USD -18,843.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 161 | 83.23% | USD 56.34 | USD 9,071.00 | USD -30,438.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 161 | 83.23% | USD 47.24 | USD 7,605.90 | USD -30,447.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 161 | 83.23% | USD 21.34 | USD 3,436.00 | USD -30,473.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 161 | 83.23% | USD 12.24 | USD 1,970.90 | USD -30,482.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 161 | 83.23% | USD -13.66 | USD -2,199.00 | USD -30,508.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 161 | 83.23% | USD -22.76 | USD -3,664.10 | USD -30,517.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 161 | 83.23% | USD -83.66 | USD -13,469.00 | USD -30,578.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 161 | 83.23% | USD -92.76 | USD -14,934.10 | USD -30,587.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.87% | USD -49.16 | USD -9,487.00 | USD -30,438.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.87% | USD -58.26 | USD -11,243.30 | USD -30,447.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 81.87% | USD -84.16 | USD -16,242.00 | USD -30,473.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 81.35% | USD -93.26 | USD -17,998.30 | USD -30,482.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 81.35% | USD -119.16 | USD -22,997.00 | USD -30,508.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 81.35% | USD -128.26 | USD -24,753.30 | USD -30,517.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 80.83% | USD -189.16 | USD -36,507.00 | USD -30,578.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 80.83% | USD -198.26 | USD -38,263.30 | USD -30,587.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 76.41% | USD 52.77 | USD 10,291.00 | USD -18,694.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 75.38% | USD 43.67 | USD 8,516.50 | USD -18,703.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 74.36% | USD 17.77 | USD 3,466.00 | USD -18,729.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 74.36% | USD 8.67 | USD 1,691.50 | USD -18,738.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 73.85% | USD -17.23 | USD -3,359.00 | USD -18,764.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 73.33% | USD -26.33 | USD -5,133.50 | USD -18,773.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 68.21% | USD -87.23 | USD -17,009.00 | USD -18,834.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 67.69% | USD -96.33 | USD -18,783.50 | USD -18,843.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 4 | 75.00% | USD 681.75 | USD 2,727.00 | USD -982.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 4 | 75.00% | USD 672.65 | USD 2,690.60 | USD -991.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 4 | 75.00% | USD 646.75 | USD 2,587.00 | USD -1,017.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 4 | 75.00% | USD 637.65 | USD 2,550.60 | USD -1,026.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 4 | 75.00% | USD 611.75 | USD 2,447.00 | USD -1,052.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 4 | 75.00% | USD 602.65 | USD 2,410.60 | USD -1,061.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 4 | 75.00% | USD 541.75 | USD 2,167.00 | USD -1,122.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 4 | 75.00% | USD 532.65 | USD 2,130.60 | USD -1,131.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 81.77% | USD -66.05 | USD -12,681.00 | USD -30,438.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 81.77% | USD -75.15 | USD -14,428.20 | USD -30,447.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 81.77% | USD -101.05 | USD -19,401.00 | USD -30,473.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 81.25% | USD -110.15 | USD -21,148.20 | USD -30,482.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 81.25% | USD -136.05 | USD -26,121.00 | USD -30,508.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 81.25% | USD -145.15 | USD -27,868.20 | USD -30,517.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 80.73% | USD -206.05 | USD -39,561.00 | USD -30,578.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 80.73% | USD -215.15 | USD -41,308.20 | USD -30,587.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 76.41% | USD 52.77 | USD 10,291.00 | USD -18,694.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 75.38% | USD 43.67 | USD 8,516.50 | USD -18,703.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 74.36% | USD 17.77 | USD 3,466.00 | USD -18,729.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 74.36% | USD 8.67 | USD 1,691.50 | USD -18,738.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 73.85% | USD -17.23 | USD -3,359.00 | USD -18,764.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 73.33% | USD -26.33 | USD -5,133.50 | USD -18,773.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 68.21% | USD -87.23 | USD -17,009.00 | USD -18,834.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 67.69% | USD -96.33 | USD -18,783.50 | USD -18,843.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 192 | 81.77% | USD -66.05 | USD -12,681.00 | USD -30,438.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 192 | 81.77% | USD -75.15 | USD -14,428.20 | USD -30,447.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 192 | 81.77% | USD -101.05 | USD -19,401.00 | USD -30,473.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 192 | 81.25% | USD -110.15 | USD -21,148.20 | USD -30,482.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 192 | 81.25% | USD -136.05 | USD -26,121.00 | USD -30,508.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 192 | 81.25% | USD -145.15 | USD -27,868.20 | USD -30,517.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 192 | 80.73% | USD -206.05 | USD -39,561.00 | USD -30,578.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 192 | 80.73% | USD -215.15 | USD -41,308.20 | USD -30,587.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 195 | 76.41% | USD 52.77 | USD 10,291.00 | USD -18,694.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 195 | 75.38% | USD 43.67 | USD 8,516.50 | USD -18,703.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 195 | 74.36% | USD 17.77 | USD 3,466.00 | USD -18,729.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 195 | 74.36% | USD 8.67 | USD 1,691.50 | USD -18,738.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 195 | 73.85% | USD -17.23 | USD -3,359.00 | USD -18,764.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 195 | 73.33% | USD -26.33 | USD -5,133.50 | USD -18,773.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 195 | 68.21% | USD -87.23 | USD -17,009.00 | USD -18,834.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 195 | 67.69% | USD -96.33 | USD -18,783.50 | USD -18,843.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 195/196 (1) | 25.64% (20.02–32.20%) | USD -43.71 | USD -8,524.00 | USD -1,536.60 |
| HOLD_5_SESSIONS | 1 : 6 | 195/196 (1) | 75.38% (68.89–80.90%) | USD -69.65 | USD -13,581.50 | USD -18,773.10 |
| HOLD_5_SESSIONS | 6 : 1 | 195/196 (1) | 21.54% (16.35–27.83%) | USD -236.34 | USD -46,086.50 | USD -4,106.10 |
| HOLD_5_SESSIONS | 5 : 5 | 195/196 (1) | 25.64% (20.02–32.20%) | USD -218.56 | USD -42,620.00 | USD -7,683.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 195/196 (1) | 25.64% (20.02–32.20%) | USD -43.71 | USD -8,524.00 | USD -1,536.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 195/196 (1) | 75.38% (68.89–80.90%) | USD -69.65 | USD -13,581.50 | USD -18,773.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 195/196 (1) | 21.54% (16.35–27.83%) | USD -236.34 | USD -46,086.50 | USD -4,106.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 195/196 (1) | 25.64% (20.02–32.20%) | USD -218.56 | USD -42,620.00 | USD -7,683.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -44.65 | USD -8,706.00 | USD -1,536.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 73.33% (66.72–79.05%) | USD -48.09 | USD -9,378.50 | USD -18,773.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 24.62% (19.10–31.11%) | USD -264.43 | USD -51,563.50 | USD -3,188.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -223.23 | USD -43,530.00 | USD -7,683.00 |
| HOLD_10_SESSIONS | 1 : 1 | 161/196 (35) | 25.47% (19.36–32.71%) | USD -67.31 | USD -10,837.60 | USD -3,365.60 |
| HOLD_10_SESSIONS | 1 : 6 | 161/196 (35) | 83.23% (76.70–88.21%) | USD -22.76 | USD -3,664.10 | USD -30,517.10 |
| HOLD_10_SESSIONS | 6 : 1 | 161/196 (35) | 17.39% (12.32–23.99%) | USD -448.44 | USD -72,199.10 | USD -4,275.10 |
| HOLD_10_SESSIONS | 5 : 5 | 161/196 (35) | 25.47% (19.36–32.71%) | USD -336.57 | USD -54,188.00 | USD -16,828.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 193/196 (3) | 25.39% (19.77–31.97%) | USD -54.58 | USD -10,533.80 | USD -3,365.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 193/196 (3) | 81.35% (75.26–86.21%) | USD -128.26 | USD -24,753.30 | USD -30,517.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 193/196 (3) | 17.10% (12.44–23.04%) | USD -253.80 | USD -48,983.30 | USD -4,258.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 193/196 (3) | 25.39% (19.77–31.97%) | USD -272.90 | USD -52,669.00 | USD -16,828.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -44.85 | USD -8,746.00 | USD -1,536.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 73.33% (66.72–79.05%) | USD -26.33 | USD -5,133.50 | USD -18,773.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 25.13% (19.56–31.66%) | USD -287.63 | USD -56,088.50 | USD -3,188.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -224.26 | USD -43,730.00 | USD -7,683.00 |
| HOLD_15_SESSIONS | 1 : 1 | 4/196 (192) | 25.00% (4.56–69.94%) | USD -2.10 | USD -8.40 | USD -189.60 |
| HOLD_15_SESSIONS | 1 : 6 | 4/196 (192) | 75.00% (30.06–95.44%) | USD 602.65 | USD 2,410.60 | USD -1,061.10 |
| HOLD_15_SESSIONS | 6 : 1 | 4/196 (192) | 25.00% (4.56–69.94%) | USD -617.35 | USD -2,469.40 | USD -1,677.10 |
| HOLD_15_SESSIONS | 5 : 5 | 4/196 (192) | 25.00% (4.56–69.94%) | USD -10.50 | USD -42.00 | USD -948.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 192/196 (4) | 25.52% (19.88–32.13%) | USD -51.82 | USD -9,950.20 | USD -3,365.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 192/196 (4) | 81.25% (75.14–86.14%) | USD -145.15 | USD -27,868.20 | USD -30,517.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 192/196 (4) | 17.19% (12.51–23.15%) | USD -217.62 | USD -41,783.20 | USD -4,258.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 192/196 (4) | 25.52% (19.88–32.13%) | USD -259.12 | USD -49,751.00 | USD -16,828.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -44.85 | USD -8,746.00 | USD -1,536.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 73.33% (66.72–79.05%) | USD -26.33 | USD -5,133.50 | USD -18,773.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 25.13% (19.56–31.66%) | USD -287.63 | USD -56,088.50 | USD -3,188.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -224.26 | USD -43,730.00 | USD -7,683.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/196 (196) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/196 (196) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 192/196 (4) | 25.52% (19.88–32.13%) | USD -51.82 | USD -9,950.20 | USD -3,365.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 192/196 (4) | 81.25% (75.14–86.14%) | USD -145.15 | USD -27,868.20 | USD -30,517.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 192/196 (4) | 17.19% (12.51–23.15%) | USD -217.62 | USD -41,783.20 | USD -4,258.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 192/196 (4) | 25.52% (19.88–32.13%) | USD -259.12 | USD -49,751.00 | USD -16,828.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -44.85 | USD -8,746.00 | USD -1,536.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 195/196 (1) | 73.33% (66.72–79.05%) | USD -26.33 | USD -5,133.50 | USD -18,773.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 195/196 (1) | 25.13% (19.56–31.66%) | USD -287.63 | USD -56,088.50 | USD -3,188.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 195/196 (1) | 28.72% (22.83–35.43%) | USD -224.26 | USD -43,730.00 | USD -7,683.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/196 | 0.00% | USD -208,873.76 | USD -341,657.55 |
| -75% | 0/196 | 0.00% | USD -154,767.12 | USD -253,921.55 |
| -50% | 0/196 | 0.00% | USD -100,660.48 | USD -166,591.05 |
| -40% | 0/196 | 0.00% | USD -79,017.82 | USD -131,705.35 |
| -30% | 0/196 | 0.00% | USD -57,375.16 | USD -96,819.65 |
| -25% | 0/196 | 0.00% | USD -46,553.84 | USD -79,376.80 |
| -20% | 0/196 | 0.00% | USD -35,732.51 | USD -61,933.95 |
| -15% | 1/196 | 0.51% | USD -24,922.33 | USD -44,491.10 |
| -10% | 3/196 | 1.53% | USD -14,189.01 | USD -27,048.25 |
| -5% | 36/196 | 18.37% | USD -3,687.73 | USD -10,572.90 |
| 0% | 196/196 | 100.00% | USD 1,235.60 | USD 221.45 |
| 5% | 196/196 | 100.00% | USD 1,234.99 | USD 221.45 |
| 10% | 196/196 | 100.00% | USD 1,234.99 | USD 221.45 |
| 20% | 196/196 | 100.00% | USD 1,234.99 | USD 221.45 |

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