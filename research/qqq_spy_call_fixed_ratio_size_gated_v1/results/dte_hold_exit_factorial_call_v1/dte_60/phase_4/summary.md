# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 279.38 / USD 1,512.05; mean absolute mismatch USD 1,232.67; mean match score 18.36%.
- Actual selected contract ratios: {'1:6': 120}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 120; entered cohorts: 120; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 120/120 | 57/63/0 | 47.50% (38.78–56.37%) | USD -232.62 | USD -79.10 | USD -27,914.00 | USD -4,487.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 120/120 | 57/63/0 | 47.50% (38.78–56.37%) | USD -232.62 | USD -79.10 | USD -27,914.00 | USD -4,487.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 120/120 | 57/63/0 | 47.50% (38.78–56.37%) | USD -232.62 | USD -79.10 | USD -27,914.00 | USD -4,487.10 | 0 |
| HOLD_10_SESSIONS | 120/120 | 62/58/0 | 51.67% (42.81–60.42%) | USD -221.95 | USD 15.90 | USD -26,634.00 | USD -4,975.10 | 0 |
| HOLD_10_OR_DTE_LE_7 | 120/120 | 62/58/0 | 51.67% (42.81–60.42%) | USD -221.95 | USD 15.90 | USD -26,634.00 | USD -4,975.10 | 0 |
| HOLD_10_OR_DTE_LE_14 | 120/120 | 62/58/0 | 51.67% (42.81–60.42%) | USD -221.95 | USD 15.90 | USD -26,634.00 | USD -4,975.10 | 0 |
| HOLD_15_SESSIONS | 119/120 | 66/53/0 | 55.46% (46.50–64.08%) | USD -379.78 | USD 173.90 | USD -45,193.90 | USD -14,487.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 119/120 | 66/53/0 | 55.46% (46.50–64.08%) | USD -379.78 | USD 173.90 | USD -45,193.90 | USD -14,487.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 119/120 | 66/53/0 | 55.46% (46.50–64.08%) | USD -379.78 | USD 173.90 | USD -45,193.90 | USD -14,487.10 | 1 |
| HOLD_20_SESSIONS | 119/120 | 65/54/0 | 54.62% (45.67–63.28%) | USD -334.10 | USD 140.90 | USD -39,757.90 | USD -9,216.10 | 1 |
| HOLD_20_OR_DTE_LE_7 | 119/120 | 65/54/0 | 54.62% (45.67–63.28%) | USD -334.10 | USD 140.90 | USD -39,757.90 | USD -9,216.10 | 1 |
| HOLD_20_OR_DTE_LE_14 | 119/120 | 65/54/0 | 54.62% (45.67–63.28%) | USD -334.10 | USD 140.90 | USD -39,757.90 | USD -9,216.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 35.83 | USD -189.35 |
| HOLD_5_OR_DTE_LE_7 | USD 35.83 | USD -189.35 |
| HOLD_5_OR_DTE_LE_14 | USD 35.83 | USD -189.35 |
| HOLD_10_SESSIONS | USD 31.70 | USD -174.55 |
| HOLD_10_OR_DTE_LE_7 | USD 31.70 | USD -174.55 |
| HOLD_10_OR_DTE_LE_14 | USD 31.70 | USD -174.55 |
| HOLD_15_SESSIONS | USD 91.99 | USD -392.67 |
| HOLD_15_OR_DTE_LE_7 | USD 91.99 | USD -392.67 |
| HOLD_15_OR_DTE_LE_14 | USD 91.99 | USD -392.67 |
| HOLD_20_SESSIONS | USD 85.49 | USD -340.49 |
| HOLD_20_OR_DTE_LE_7 | USD 85.49 | USD -340.49 |
| HOLD_20_OR_DTE_LE_14 | USD 85.49 | USD -340.49 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 120 | 49.17% | USD -153.52 | USD -18,422.00 | USD -4,408.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 120 | 49.17% | USD -162.62 | USD -19,514.00 | USD -4,417.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 120 | 48.33% | USD -188.52 | USD -22,622.00 | USD -4,443.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 120 | 48.33% | USD -197.62 | USD -23,714.00 | USD -4,452.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 120 | 48.33% | USD -223.52 | USD -26,822.00 | USD -4,478.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 120 | 47.50% | USD -232.62 | USD -27,914.00 | USD -4,487.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 120 | 45.00% | USD -293.52 | USD -35,222.00 | USD -4,548.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 120 | 44.17% | USD -302.62 | USD -36,314.00 | USD -4,557.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 120 | 49.17% | USD -153.52 | USD -18,422.00 | USD -4,408.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 120 | 49.17% | USD -162.62 | USD -19,514.00 | USD -4,417.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 120 | 48.33% | USD -188.52 | USD -22,622.00 | USD -4,443.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 120 | 48.33% | USD -197.62 | USD -23,714.00 | USD -4,452.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 120 | 48.33% | USD -223.52 | USD -26,822.00 | USD -4,478.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 120 | 47.50% | USD -232.62 | USD -27,914.00 | USD -4,487.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 120 | 45.00% | USD -293.52 | USD -35,222.00 | USD -4,548.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 120 | 44.17% | USD -302.62 | USD -36,314.00 | USD -4,557.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 120 | 49.17% | USD -153.52 | USD -18,422.00 | USD -4,408.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 120 | 49.17% | USD -162.62 | USD -19,514.00 | USD -4,417.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 120 | 48.33% | USD -188.52 | USD -22,622.00 | USD -4,443.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 120 | 48.33% | USD -197.62 | USD -23,714.00 | USD -4,452.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 120 | 48.33% | USD -223.52 | USD -26,822.00 | USD -4,478.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 120 | 47.50% | USD -232.62 | USD -27,914.00 | USD -4,487.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 120 | 45.00% | USD -293.52 | USD -35,222.00 | USD -4,548.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 120 | 44.17% | USD -302.62 | USD -36,314.00 | USD -4,557.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 120 | 56.67% | USD -142.85 | USD -17,142.00 | USD -4,896.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 120 | 55.00% | USD -151.95 | USD -18,234.00 | USD -4,905.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 120 | 55.00% | USD -177.85 | USD -21,342.00 | USD -4,931.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 120 | 54.17% | USD -186.95 | USD -22,434.00 | USD -4,940.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 120 | 52.50% | USD -212.85 | USD -25,542.00 | USD -4,966.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 120 | 51.67% | USD -221.95 | USD -26,634.00 | USD -4,975.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 120 | 48.33% | USD -282.85 | USD -33,942.00 | USD -5,036.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 120 | 48.33% | USD -291.95 | USD -35,034.00 | USD -5,045.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 120 | 56.67% | USD -142.85 | USD -17,142.00 | USD -4,896.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 120 | 55.00% | USD -151.95 | USD -18,234.00 | USD -4,905.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 120 | 55.00% | USD -177.85 | USD -21,342.00 | USD -4,931.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 120 | 54.17% | USD -186.95 | USD -22,434.00 | USD -4,940.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 120 | 52.50% | USD -212.85 | USD -25,542.00 | USD -4,966.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 120 | 51.67% | USD -221.95 | USD -26,634.00 | USD -4,975.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 120 | 48.33% | USD -282.85 | USD -33,942.00 | USD -5,036.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 120 | 48.33% | USD -291.95 | USD -35,034.00 | USD -5,045.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 120 | 56.67% | USD -142.85 | USD -17,142.00 | USD -4,896.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 120 | 55.00% | USD -151.95 | USD -18,234.00 | USD -4,905.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 120 | 55.00% | USD -177.85 | USD -21,342.00 | USD -4,931.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 120 | 54.17% | USD -186.95 | USD -22,434.00 | USD -4,940.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 120 | 52.50% | USD -212.85 | USD -25,542.00 | USD -4,966.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 120 | 51.67% | USD -221.95 | USD -26,634.00 | USD -4,975.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 120 | 48.33% | USD -282.85 | USD -33,942.00 | USD -5,036.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 120 | 48.33% | USD -291.95 | USD -35,034.00 | USD -5,045.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 119 | 59.66% | USD -300.68 | USD -35,781.00 | USD -14,408.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 119 | 58.82% | USD -309.78 | USD -36,863.90 | USD -14,417.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 119 | 57.14% | USD -335.68 | USD -39,946.00 | USD -14,443.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 119 | 56.30% | USD -344.78 | USD -41,028.90 | USD -14,452.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 119 | 55.46% | USD -370.68 | USD -44,111.00 | USD -14,478.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 119 | 55.46% | USD -379.78 | USD -45,193.90 | USD -14,487.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 119 | 53.78% | USD -440.68 | USD -52,441.00 | USD -14,548.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 119 | 53.78% | USD -449.78 | USD -53,523.90 | USD -14,557.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 119 | 59.66% | USD -300.68 | USD -35,781.00 | USD -14,408.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 119 | 58.82% | USD -309.78 | USD -36,863.90 | USD -14,417.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 119 | 57.14% | USD -335.68 | USD -39,946.00 | USD -14,443.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 119 | 56.30% | USD -344.78 | USD -41,028.90 | USD -14,452.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 119 | 55.46% | USD -370.68 | USD -44,111.00 | USD -14,478.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 119 | 55.46% | USD -379.78 | USD -45,193.90 | USD -14,487.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 119 | 53.78% | USD -440.68 | USD -52,441.00 | USD -14,548.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 119 | 53.78% | USD -449.78 | USD -53,523.90 | USD -14,557.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 119 | 59.66% | USD -300.68 | USD -35,781.00 | USD -14,408.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 119 | 58.82% | USD -309.78 | USD -36,863.90 | USD -14,417.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 119 | 57.14% | USD -335.68 | USD -39,946.00 | USD -14,443.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 119 | 56.30% | USD -344.78 | USD -41,028.90 | USD -14,452.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 119 | 55.46% | USD -370.68 | USD -44,111.00 | USD -14,478.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 119 | 55.46% | USD -379.78 | USD -45,193.90 | USD -14,487.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 119 | 53.78% | USD -440.68 | USD -52,441.00 | USD -14,548.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 119 | 53.78% | USD -449.78 | USD -53,523.90 | USD -14,557.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 119 | 59.66% | USD -255.00 | USD -30,345.00 | USD -9,137.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 119 | 59.66% | USD -264.10 | USD -31,427.90 | USD -9,146.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 119 | 57.14% | USD -290.00 | USD -34,510.00 | USD -9,172.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 119 | 57.14% | USD -299.10 | USD -35,592.90 | USD -9,181.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 119 | 54.62% | USD -325.00 | USD -38,675.00 | USD -9,207.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 119 | 54.62% | USD -334.10 | USD -39,757.90 | USD -9,216.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 119 | 52.94% | USD -395.00 | USD -47,005.00 | USD -9,277.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 119 | 52.94% | USD -404.10 | USD -48,087.90 | USD -9,286.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 119 | 59.66% | USD -255.00 | USD -30,345.00 | USD -9,137.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 119 | 59.66% | USD -264.10 | USD -31,427.90 | USD -9,146.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 119 | 57.14% | USD -290.00 | USD -34,510.00 | USD -9,172.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 119 | 57.14% | USD -299.10 | USD -35,592.90 | USD -9,181.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 119 | 54.62% | USD -325.00 | USD -38,675.00 | USD -9,207.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 119 | 54.62% | USD -334.10 | USD -39,757.90 | USD -9,216.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 119 | 52.94% | USD -395.00 | USD -47,005.00 | USD -9,277.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 119 | 52.94% | USD -404.10 | USD -48,087.90 | USD -9,286.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 119 | 59.66% | USD -255.00 | USD -30,345.00 | USD -9,137.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 119 | 59.66% | USD -264.10 | USD -31,427.90 | USD -9,146.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 119 | 57.14% | USD -290.00 | USD -34,510.00 | USD -9,172.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 119 | 57.14% | USD -299.10 | USD -35,592.90 | USD -9,181.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 119 | 54.62% | USD -325.00 | USD -38,675.00 | USD -9,207.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 119 | 54.62% | USD -334.10 | USD -39,757.90 | USD -9,216.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 119 | 52.94% | USD -395.00 | USD -47,005.00 | USD -9,277.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 119 | 52.94% | USD -404.10 | USD -48,087.90 | USD -9,286.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 120/120 (0) | 32.50% (24.78–41.31%) | USD -18.32 | USD -2,199.00 | USD -300.60 |
| HOLD_5_SESSIONS | 1 : 6 | 120/120 (0) | 47.50% (38.78–56.37%) | USD -232.62 | USD -27,914.00 | USD -4,487.10 |
| HOLD_5_SESSIONS | 6 : 1 | 120/120 (0) | 48.33% (39.58–57.19%) | USD 104.34 | USD 12,521.00 | USD -2,852.10 |
| HOLD_5_SESSIONS | 5 : 5 | 120/120 (0) | 32.50% (24.78–41.31%) | USD -91.62 | USD -10,995.00 | USD -1,503.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 120/120 (0) | 32.50% (24.78–41.31%) | USD -18.32 | USD -2,199.00 | USD -300.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 120/120 (0) | 47.50% (38.78–56.37%) | USD -232.62 | USD -27,914.00 | USD -4,487.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 120/120 (0) | 48.33% (39.58–57.19%) | USD 104.34 | USD 12,521.00 | USD -2,852.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 120/120 (0) | 32.50% (24.78–41.31%) | USD -91.62 | USD -10,995.00 | USD -1,503.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 120/120 (0) | 32.50% (24.78–41.31%) | USD -18.32 | USD -2,199.00 | USD -300.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 120/120 (0) | 47.50% (38.78–56.37%) | USD -232.62 | USD -27,914.00 | USD -4,487.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 120/120 (0) | 48.33% (39.58–57.19%) | USD 104.34 | USD 12,521.00 | USD -2,852.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 120/120 (0) | 32.50% (24.78–41.31%) | USD -91.62 | USD -10,995.00 | USD -1,503.00 |
| HOLD_10_SESSIONS | 1 : 1 | 120/120 (0) | 35.83% (27.82–44.73%) | USD -19.99 | USD -2,399.00 | USD -447.60 |
| HOLD_10_SESSIONS | 1 : 6 | 120/120 (0) | 51.67% (42.81–60.42%) | USD -221.95 | USD -26,634.00 | USD -4,975.10 |
| HOLD_10_SESSIONS | 6 : 1 | 120/120 (0) | 43.33% (34.81–52.27%) | USD 82.01 | USD 9,841.00 | USD -2,843.10 |
| HOLD_10_SESSIONS | 5 : 5 | 120/120 (0) | 35.83% (27.82–44.73%) | USD -99.96 | USD -11,995.00 | USD -2,238.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 120/120 (0) | 35.83% (27.82–44.73%) | USD -19.99 | USD -2,399.00 | USD -447.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 120/120 (0) | 51.67% (42.81–60.42%) | USD -221.95 | USD -26,634.00 | USD -4,975.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 120/120 (0) | 43.33% (34.81–52.27%) | USD 82.01 | USD 9,841.00 | USD -2,843.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 120/120 (0) | 35.83% (27.82–44.73%) | USD -99.96 | USD -11,995.00 | USD -2,238.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 120/120 (0) | 35.83% (27.82–44.73%) | USD -19.99 | USD -2,399.00 | USD -447.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 120/120 (0) | 51.67% (42.81–60.42%) | USD -221.95 | USD -26,634.00 | USD -4,975.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 120/120 (0) | 43.33% (34.81–52.27%) | USD 82.01 | USD 9,841.00 | USD -2,843.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 120/120 (0) | 35.83% (27.82–44.73%) | USD -99.96 | USD -11,995.00 | USD -2,238.00 |
| HOLD_15_SESSIONS | 1 : 1 | 119/120 (1) | 35.29% (27.29–44.22%) | USD 3.95 | USD 469.60 | USD -1,281.60 |
| HOLD_15_SESSIONS | 1 : 6 | 119/120 (1) | 55.46% (46.50–64.08%) | USD -379.78 | USD -45,193.90 | USD -14,487.10 |
| HOLD_15_SESSIONS | 6 : 1 | 119/120 (1) | 43.70% (35.12–52.67%) | USD 407.40 | USD 48,481.10 | USD -3,808.10 |
| HOLD_15_SESSIONS | 5 : 5 | 119/120 (1) | 35.29% (27.29–44.22%) | USD 19.73 | USD 2,348.00 | USD -6,408.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 119/120 (1) | 35.29% (27.29–44.22%) | USD 3.95 | USD 469.60 | USD -1,281.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 119/120 (1) | 55.46% (46.50–64.08%) | USD -379.78 | USD -45,193.90 | USD -14,487.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 119/120 (1) | 43.70% (35.12–52.67%) | USD 407.40 | USD 48,481.10 | USD -3,808.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 119/120 (1) | 35.29% (27.29–44.22%) | USD 19.73 | USD 2,348.00 | USD -6,408.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 119/120 (1) | 35.29% (27.29–44.22%) | USD 3.95 | USD 469.60 | USD -1,281.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 119/120 (1) | 55.46% (46.50–64.08%) | USD -379.78 | USD -45,193.90 | USD -14,487.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 119/120 (1) | 43.70% (35.12–52.67%) | USD 407.40 | USD 48,481.10 | USD -3,808.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 119/120 (1) | 35.29% (27.29–44.22%) | USD 19.73 | USD 2,348.00 | USD -6,408.00 |
| HOLD_20_SESSIONS | 1 : 1 | 119/120 (1) | 31.93% (24.23–40.76%) | USD 6.14 | USD 730.60 | USD -437.60 |
| HOLD_20_SESSIONS | 1 : 6 | 119/120 (1) | 54.62% (45.67–63.28%) | USD -334.10 | USD -39,757.90 | USD -9,216.10 |
| HOLD_20_SESSIONS | 6 : 1 | 119/120 (1) | 40.34% (31.96–49.32%) | USD 377.08 | USD 44,872.10 | USD -3,984.10 |
| HOLD_20_SESSIONS | 5 : 5 | 119/120 (1) | 31.93% (24.23–40.76%) | USD 30.70 | USD 3,653.00 | USD -2,188.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 119/120 (1) | 31.93% (24.23–40.76%) | USD 6.14 | USD 730.60 | USD -437.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 119/120 (1) | 54.62% (45.67–63.28%) | USD -334.10 | USD -39,757.90 | USD -9,216.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 119/120 (1) | 40.34% (31.96–49.32%) | USD 377.08 | USD 44,872.10 | USD -3,984.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 119/120 (1) | 31.93% (24.23–40.76%) | USD 30.70 | USD 3,653.00 | USD -2,188.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 119/120 (1) | 31.93% (24.23–40.76%) | USD 6.14 | USD 730.60 | USD -437.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 119/120 (1) | 54.62% (45.67–63.28%) | USD -334.10 | USD -39,757.90 | USD -9,216.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 119/120 (1) | 40.34% (31.96–49.32%) | USD 377.08 | USD 44,872.10 | USD -3,984.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 119/120 (1) | 31.93% (24.23–40.76%) | USD 30.70 | USD 3,653.00 | USD -2,188.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -75% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -50% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -40% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -30% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -25% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -20% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -15% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -10% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| -5% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| 0% | 120/120 | 100.00% | USD 1,193.12 | USD 236.45 |
| 5% | 72/120 | 60.00% | USD -102.06 | USD -3,813.10 |
| 10% | 8/120 | 6.67% | USD -9,861.58 | USD -21,215.05 |
| 20% | 1/120 | 0.83% | USD -31,951.02 | USD -56,048.55 |

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