# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 282.45 / USD 1,646.26; mean absolute mismatch USD 1,363.81; mean match score 17.12%.
- Actual selected contract ratios: {'1:6': 194}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 194; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/194 | 138/56/0 | 71.13% (64.40–77.05%) | USD 18.53 | USD 430.40 | USD 3,595.60 | USD -19,508.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 194/194 | 138/56/0 | 71.13% (64.40–77.05%) | USD 18.53 | USD 430.40 | USD 3,595.60 | USD -19,508.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 194/194 | 141/53/0 | 72.68% (66.02–78.46%) | USD 6.07 | USD 381.90 | USD 1,177.60 | USD -19,508.10 | 0 |
| HOLD_10_SESSIONS | 161/194 | 129/32/0 | 80.12% (73.29–85.55%) | USD 131.89 | USD 763.90 | USD 21,234.90 | USD -30,254.10 | 33 |
| HOLD_10_OR_DTE_LE_7 | 193/194 | 157/36/0 | 81.35% (75.26–86.21%) | USD 300.62 | USD 721.90 | USD 58,019.70 | USD -16,588.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 194/194 | 145/49/0 | 74.74% (68.19–80.34%) | USD 57.69 | USD 406.40 | USD 11,192.60 | USD -19,508.10 | 0 |
| HOLD_15_SESSIONS | 5/194 | 3/2/0 | 60.00% (23.07–88.24%) | USD -1,401.50 | USD 45.90 | USD -7,007.50 | USD -4,603.10 | 189 |
| HOLD_15_OR_DTE_LE_7 | 193/194 | 158/35/0 | 81.87% (75.83–86.66%) | USD 299.91 | USD 742.90 | USD 57,882.70 | USD -16,588.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 194/194 | 145/49/0 | 74.74% (68.19–80.34%) | USD 57.69 | USD 406.40 | USD 11,192.60 | USD -19,508.10 | 0 |
| HOLD_20_SESSIONS | 0/194 | 0/0/0 | — | — | — | — | — | 194 |
| HOLD_20_OR_DTE_LE_7 | 193/194 | 158/35/0 | 81.87% (75.83–86.66%) | USD 299.91 | USD 742.90 | USD 57,882.70 | USD -16,588.10 | 1 |
| HOLD_20_OR_DTE_LE_14 | 194/194 | 145/49/0 | 74.74% (68.19–80.34%) | USD 57.69 | USD 406.40 | USD 11,192.60 | USD -19,508.10 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -35.91 | USD 133.55 |
| HOLD_5_OR_DTE_LE_7 | USD -35.91 | USD 133.55 |
| HOLD_5_OR_DTE_LE_14 | USD -42.78 | USD 127.95 |
| HOLD_10_SESSIONS | USD -71.30 | USD 282.30 |
| HOLD_10_OR_DTE_LE_7 | USD -89.62 | USD 469.34 |
| HOLD_10_OR_DTE_LE_14 | USD -51.49 | USD 188.29 |
| HOLD_15_SESSIONS | USD 54.00 | USD -1,376.40 |
| HOLD_15_OR_DTE_LE_7 | USD -88.49 | USD 467.50 |
| HOLD_15_OR_DTE_LE_14 | USD -51.49 | USD 188.29 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -88.49 | USD 467.50 |
| HOLD_20_OR_DTE_LE_14 | USD -51.49 | USD 188.29 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 72.68% | USD 97.63 | USD 18,941.00 | USD -19,429.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 72.68% | USD 88.53 | USD 17,175.60 | USD -19,438.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 72.68% | USD 62.63 | USD 12,151.00 | USD -19,464.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 72.68% | USD 53.53 | USD 10,385.60 | USD -19,473.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 71.13% | USD 27.63 | USD 5,361.00 | USD -19,499.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 71.13% | USD 18.53 | USD 3,595.60 | USD -19,508.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 68.56% | USD -42.37 | USD -8,219.00 | USD -19,569.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 68.56% | USD -51.47 | USD -9,984.40 | USD -19,578.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 72.68% | USD 97.63 | USD 18,941.00 | USD -19,429.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 72.68% | USD 88.53 | USD 17,175.60 | USD -19,438.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 72.68% | USD 62.63 | USD 12,151.00 | USD -19,464.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 72.68% | USD 53.53 | USD 10,385.60 | USD -19,473.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 71.13% | USD 27.63 | USD 5,361.00 | USD -19,499.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 71.13% | USD 18.53 | USD 3,595.60 | USD -19,508.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 68.56% | USD -42.37 | USD -8,219.00 | USD -19,569.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 68.56% | USD -51.47 | USD -9,984.40 | USD -19,578.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 74.74% | USD 85.17 | USD 16,523.00 | USD -19,429.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 74.74% | USD 76.07 | USD 14,757.60 | USD -19,438.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 74.23% | USD 50.17 | USD 9,733.00 | USD -19,464.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 74.23% | USD 41.07 | USD 7,967.60 | USD -19,473.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 72.68% | USD 15.17 | USD 2,943.00 | USD -19,499.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 72.68% | USD 6.07 | USD 1,177.60 | USD -19,508.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 69.07% | USD -54.83 | USD -10,637.00 | USD -19,569.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 68.56% | USD -63.93 | USD -12,402.40 | USD -19,578.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 161 | 80.75% | USD 210.99 | USD 33,970.00 | USD -30,175.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 161 | 80.75% | USD 201.89 | USD 32,504.90 | USD -30,184.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 161 | 80.12% | USD 175.99 | USD 28,335.00 | USD -30,210.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 161 | 80.12% | USD 166.89 | USD 26,869.90 | USD -30,219.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 161 | 80.12% | USD 140.99 | USD 22,700.00 | USD -30,245.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 161 | 80.12% | USD 131.89 | USD 21,234.90 | USD -30,254.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 161 | 79.50% | USD 70.99 | USD 11,430.00 | USD -30,315.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 161 | 79.50% | USD 61.89 | USD 9,964.90 | USD -30,324.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.35% | USD 379.72 | USD 73,286.00 | USD -16,509.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.35% | USD 370.62 | USD 71,529.70 | USD -16,518.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 81.35% | USD 344.72 | USD 66,531.00 | USD -16,544.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 81.35% | USD 335.62 | USD 64,774.70 | USD -16,553.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 81.35% | USD 309.72 | USD 59,776.00 | USD -16,579.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 81.35% | USD 300.62 | USD 58,019.70 | USD -16,588.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 81.35% | USD 239.72 | USD 46,266.00 | USD -16,649.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 81.35% | USD 230.62 | USD 44,509.70 | USD -16,658.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 76.29% | USD 136.79 | USD 26,538.00 | USD -19,429.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 76.29% | USD 127.69 | USD 24,772.60 | USD -19,438.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 75.77% | USD 101.79 | USD 19,748.00 | USD -19,464.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 75.77% | USD 92.69 | USD 17,982.60 | USD -19,473.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 74.74% | USD 66.79 | USD 12,958.00 | USD -19,499.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 74.74% | USD 57.69 | USD 11,192.60 | USD -19,508.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 71.13% | USD -3.21 | USD -622.00 | USD -19,569.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.10% | USD -12.31 | USD -2,387.40 | USD -19,578.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 5 | 60.00% | USD -1,322.40 | USD -6,612.00 | USD -4,524.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 5 | 60.00% | USD -1,331.50 | USD -6,657.50 | USD -4,533.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 5 | 60.00% | USD -1,357.40 | USD -6,787.00 | USD -4,559.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 5 | 60.00% | USD -1,366.50 | USD -6,832.50 | USD -4,568.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 5 | 60.00% | USD -1,392.40 | USD -6,962.00 | USD -4,594.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 5 | 60.00% | USD -1,401.50 | USD -7,007.50 | USD -4,603.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 5 | 40.00% | USD -1,462.40 | USD -7,312.00 | USD -4,664.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 5 | 40.00% | USD -1,471.50 | USD -7,357.50 | USD -4,673.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.87% | USD 379.01 | USD 73,149.00 | USD -16,509.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.87% | USD 369.91 | USD 71,392.70 | USD -16,518.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 81.87% | USD 344.01 | USD 66,394.00 | USD -16,544.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 81.87% | USD 334.91 | USD 64,637.70 | USD -16,553.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 81.87% | USD 309.01 | USD 59,639.00 | USD -16,579.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 81.87% | USD 299.91 | USD 57,882.70 | USD -16,588.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 81.87% | USD 239.01 | USD 46,129.00 | USD -16,649.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 81.87% | USD 229.91 | USD 44,372.70 | USD -16,658.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 76.29% | USD 136.79 | USD 26,538.00 | USD -19,429.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 76.29% | USD 127.69 | USD 24,772.60 | USD -19,438.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 75.77% | USD 101.79 | USD 19,748.00 | USD -19,464.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 75.77% | USD 92.69 | USD 17,982.60 | USD -19,473.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 74.74% | USD 66.79 | USD 12,958.00 | USD -19,499.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 74.74% | USD 57.69 | USD 11,192.60 | USD -19,508.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 71.13% | USD -3.21 | USD -622.00 | USD -19,569.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.10% | USD -12.31 | USD -2,387.40 | USD -19,578.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 193 | 81.87% | USD 379.01 | USD 73,149.00 | USD -16,509.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 193 | 81.87% | USD 369.91 | USD 71,392.70 | USD -16,518.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 193 | 81.87% | USD 344.01 | USD 66,394.00 | USD -16,544.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 193 | 81.87% | USD 334.91 | USD 64,637.70 | USD -16,553.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 193 | 81.87% | USD 309.01 | USD 59,639.00 | USD -16,579.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 193 | 81.87% | USD 299.91 | USD 57,882.70 | USD -16,588.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 193 | 81.87% | USD 239.01 | USD 46,129.00 | USD -16,649.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 193 | 81.87% | USD 229.91 | USD 44,372.70 | USD -16,658.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 76.29% | USD 136.79 | USD 26,538.00 | USD -19,429.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 76.29% | USD 127.69 | USD 24,772.60 | USD -19,438.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 75.77% | USD 101.79 | USD 19,748.00 | USD -19,464.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 75.77% | USD 92.69 | USD 17,982.60 | USD -19,473.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 74.74% | USD 66.79 | USD 12,958.00 | USD -19,499.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 74.74% | USD 57.69 | USD 11,192.60 | USD -19,508.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 71.13% | USD -3.21 | USD -622.00 | USD -19,569.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 70.10% | USD -12.31 | USD -2,387.40 | USD -19,578.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/194 (0) | 25.26% (19.66–31.81%) | USD -36.25 | USD -7,033.40 | USD -959.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/194 (0) | 71.13% (64.40–77.05%) | USD 18.53 | USD 3,595.60 | USD -19,508.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/194 (0) | 21.65% (16.43–27.97%) | USD -272.32 | USD -52,829.40 | USD -4,298.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/194 (0) | 25.26% (19.66–31.81%) | USD -181.27 | USD -35,167.00 | USD -4,798.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/194 (0) | 25.26% (19.66–31.81%) | USD -36.25 | USD -7,033.40 | USD -959.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/194 (0) | 71.13% (64.40–77.05%) | USD 18.53 | USD 3,595.60 | USD -19,508.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/194 (0) | 21.65% (16.43–27.97%) | USD -272.32 | USD -52,829.40 | USD -4,298.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/194 (0) | 25.26% (19.66–31.81%) | USD -181.27 | USD -35,167.00 | USD -4,798.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 24.74% (19.20–31.27%) | USD -44.05 | USD -8,546.40 | USD -959.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 72.68% (66.02–78.46%) | USD 6.07 | USD 1,177.60 | USD -19,508.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 22.68% (17.35–29.07%) | USD -314.45 | USD -61,002.40 | USD -4,298.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 24.74% (19.20–31.27%) | USD -220.27 | USD -42,732.00 | USD -4,798.00 |
| HOLD_10_SESSIONS | 1 : 1 | 161/194 (33) | 29.81% (23.29–37.28%) | USD -46.85 | USD -7,543.60 | USD -2,637.60 |
| HOLD_10_SESSIONS | 1 : 6 | 161/194 (33) | 80.12% (73.29–85.55%) | USD 131.89 | USD 21,234.90 | USD -30,254.10 |
| HOLD_10_SESSIONS | 6 : 1 | 161/194 (33) | 18.63% (13.38–25.35%) | USD -459.88 | USD -74,040.10 | USD -4,276.10 |
| HOLD_10_SESSIONS | 5 : 5 | 161/194 (33) | 29.81% (23.29–37.28%) | USD -234.27 | USD -37,718.00 | USD -13,188.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 193/194 (1) | 27.98% (22.12–34.69%) | USD -33.99 | USD -6,560.80 | USD -1,606.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 193/194 (1) | 81.35% (75.26–86.21%) | USD 300.62 | USD 58,019.70 | USD -16,588.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 193/194 (1) | 18.65% (13.79–24.74%) | USD -538.58 | USD -103,945.30 | USD -4,183.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 193/194 (1) | 27.98% (22.12–34.69%) | USD -169.97 | USD -32,804.00 | USD -8,033.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 24.23% (18.74–30.72%) | USD -42.71 | USD -8,286.40 | USD -959.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 74.74% (68.19–80.34%) | USD 57.69 | USD 11,192.60 | USD -19,508.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 22.68% (17.35–29.07%) | USD -356.69 | USD -69,197.40 | USD -4,358.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 24.23% (18.74–30.72%) | USD -213.57 | USD -41,432.00 | USD -4,798.00 |
| HOLD_15_SESSIONS | 1 : 1 | 5/194 (189) | 20.00% (3.62–62.45%) | USD -198.00 | USD -990.00 | USD -707.60 |
| HOLD_15_SESSIONS | 1 : 6 | 5/194 (189) | 60.00% (23.07–88.24%) | USD -1,401.50 | USD -7,007.50 | USD -4,603.10 |
| HOLD_15_SESSIONS | 6 : 1 | 5/194 (189) | 40.00% (11.76–76.93%) | USD 15.50 | USD 77.50 | USD -1,865.10 |
| HOLD_15_SESSIONS | 5 : 5 | 5/194 (189) | 20.00% (3.62–62.45%) | USD -990.00 | USD -4,950.00 | USD -3,538.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 193/194 (1) | 27.98% (22.12–34.69%) | USD -33.18 | USD -6,402.80 | USD -1,606.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 193/194 (1) | 81.87% (75.83–86.66%) | USD 299.91 | USD 57,882.70 | USD -16,588.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 193/194 (1) | 18.65% (13.79–24.74%) | USD -532.14 | USD -102,702.30 | USD -4,401.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 193/194 (1) | 27.98% (22.12–34.69%) | USD -165.88 | USD -32,014.00 | USD -8,033.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 24.23% (18.74–30.72%) | USD -42.71 | USD -8,286.40 | USD -959.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 74.74% (68.19–80.34%) | USD 57.69 | USD 11,192.60 | USD -19,508.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 22.68% (17.35–29.07%) | USD -356.69 | USD -69,197.40 | USD -4,358.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 24.23% (18.74–30.72%) | USD -213.57 | USD -41,432.00 | USD -4,798.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/194 (194) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 193/194 (1) | 27.98% (22.12–34.69%) | USD -33.18 | USD -6,402.80 | USD -1,606.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 193/194 (1) | 81.87% (75.83–86.66%) | USD 299.91 | USD 57,882.70 | USD -16,588.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 193/194 (1) | 18.65% (13.79–24.74%) | USD -532.14 | USD -102,702.30 | USD -4,401.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 193/194 (1) | 27.98% (22.12–34.69%) | USD -165.88 | USD -32,014.00 | USD -8,033.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 24.23% (18.74–30.72%) | USD -42.71 | USD -8,286.40 | USD -959.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 74.74% (68.19–80.34%) | USD 57.69 | USD 11,192.60 | USD -19,508.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 22.68% (17.35–29.07%) | USD -356.69 | USD -69,197.40 | USD -4,358.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 24.23% (18.74–30.72%) | USD -213.57 | USD -41,432.00 | USD -4,798.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/194 | 0.00% | USD -208,345.93 | USD -337,313.55 |
| -75% | 0/194 | 0.00% | USD -154,416.87 | USD -250,702.30 |
| -50% | 0/194 | 0.00% | USD -100,487.82 | USD -164,091.05 |
| -40% | 0/194 | 0.00% | USD -78,916.20 | USD -129,446.55 |
| -30% | 0/194 | 0.00% | USD -57,344.58 | USD -94,802.05 |
| -25% | 0/194 | 0.00% | USD -46,558.77 | USD -77,479.80 |
| -20% | 0/194 | 0.00% | USD -35,772.96 | USD -60,157.55 |
| -15% | 1/194 | 0.52% | USD -25,007.23 | USD -42,835.30 |
| -10% | 2/194 | 1.03% | USD -14,279.94 | USD -26,227.85 |
| -5% | 34/194 | 17.53% | USD -3,699.01 | USD -11,765.55 |
| 0% | 194/194 | 100.00% | USD 1,317.29 | USD 182.45 |
| 5% | 194/194 | 100.00% | USD 1,324.26 | USD 182.45 |
| 10% | 194/194 | 100.00% | USD 1,324.26 | USD 182.45 |
| 20% | 194/194 | 100.00% | USD 1,324.26 | USD 182.45 |

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