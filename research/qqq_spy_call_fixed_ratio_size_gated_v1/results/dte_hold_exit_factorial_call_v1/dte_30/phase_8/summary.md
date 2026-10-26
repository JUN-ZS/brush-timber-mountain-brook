# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 199.81 / USD 1,110.56; mean absolute mismatch USD 910.74; mean match score 18.35%.
- Actual selected contract ratios: {'1:6': 194}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 194; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/194 | 108/86/0 | 55.67% (48.64–62.48%) | USD -162.22 | USD 80.40 | USD -31,471.40 | USD -4,489.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 194/194 | 108/86/0 | 55.67% (48.64–62.48%) | USD -162.22 | USD 80.40 | USD -31,471.40 | USD -4,489.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 194/194 | 108/86/0 | 55.67% (48.64–62.48%) | USD -162.22 | USD 80.40 | USD -31,471.40 | USD -4,489.10 | 0 |
| HOLD_10_SESSIONS | 189/194 | 113/76/0 | 59.79% (52.67–66.52%) | USD -209.39 | USD 172.90 | USD -39,573.90 | USD -8,477.10 | 5 |
| HOLD_10_OR_DTE_LE_7 | 189/194 | 113/76/0 | 59.79% (52.67–66.52%) | USD -209.39 | USD 172.90 | USD -39,573.90 | USD -8,477.10 | 5 |
| HOLD_10_OR_DTE_LE_14 | 189/194 | 110/79/0 | 58.20% (51.07–65.00%) | USD -218.30 | USD 164.90 | USD -41,258.90 | USD -8,477.10 | 5 |
| HOLD_15_SESSIONS | 163/194 | 98/65/0 | 60.12% (52.46–67.32%) | USD -360.28 | USD 265.90 | USD -58,726.30 | USD -9,118.10 | 31 |
| HOLD_15_OR_DTE_LE_7 | 170/194 | 109/61/0 | 64.12% (56.67–70.94%) | USD -318.62 | USD 256.40 | USD -54,166.00 | USD -9,118.10 | 24 |
| HOLD_15_OR_DTE_LE_14 | 187/194 | 107/80/0 | 57.22% (50.05–64.09%) | USD -267.87 | USD 163.90 | USD -50,091.70 | USD -12,153.10 | 7 |
| HOLD_20_SESSIONS | 32/194 | 14/18/0 | 43.75% (28.17–60.67%) | USD -1,384.04 | USD -491.60 | USD -44,289.20 | USD -8,788.10 | 162 |
| HOLD_20_OR_DTE_LE_7 | 163/194 | 105/58/0 | 64.42% (56.81–71.36%) | USD -341.54 | USD 221.90 | USD -55,671.30 | USD -10,340.10 | 31 |
| HOLD_20_OR_DTE_LE_14 | 187/194 | 107/80/0 | 57.22% (50.05–64.09%) | USD -267.87 | USD 163.90 | USD -50,091.70 | USD -12,153.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 13.09 | USD -96.22 |
| HOLD_5_OR_DTE_LE_7 | USD 13.09 | USD -96.22 |
| HOLD_5_OR_DTE_LE_14 | USD 13.09 | USD -96.22 |
| HOLD_10_SESSIONS | USD 36.83 | USD -167.11 |
| HOLD_10_OR_DTE_LE_7 | USD 36.83 | USD -167.11 |
| HOLD_10_OR_DTE_LE_14 | USD 35.47 | USD -174.67 |
| HOLD_15_SESSIONS | USD 55.07 | USD -336.26 |
| HOLD_15_OR_DTE_LE_7 | USD 43.18 | USD -282.71 |
| HOLD_15_OR_DTE_LE_14 | USD 37.59 | USD -226.36 |
| HOLD_20_SESSIONS | USD 174.25 | USD -1,479.19 |
| HOLD_20_OR_DTE_LE_7 | USD 44.11 | USD -306.55 |
| HOLD_20_OR_DTE_LE_14 | USD 37.59 | USD -226.36 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 61.34% | USD -83.12 | USD -16,126.00 | USD -4,410.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 60.31% | USD -92.22 | USD -17,891.40 | USD -4,419.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 59.28% | USD -118.12 | USD -22,916.00 | USD -4,445.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 58.76% | USD -127.22 | USD -24,681.40 | USD -4,454.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 56.19% | USD -153.12 | USD -29,706.00 | USD -4,480.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 55.67% | USD -162.22 | USD -31,471.40 | USD -4,489.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 52.06% | USD -223.12 | USD -43,286.00 | USD -4,550.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 51.55% | USD -232.22 | USD -45,051.40 | USD -4,559.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 61.34% | USD -83.12 | USD -16,126.00 | USD -4,410.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 60.31% | USD -92.22 | USD -17,891.40 | USD -4,419.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 59.28% | USD -118.12 | USD -22,916.00 | USD -4,445.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 58.76% | USD -127.22 | USD -24,681.40 | USD -4,454.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 56.19% | USD -153.12 | USD -29,706.00 | USD -4,480.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 55.67% | USD -162.22 | USD -31,471.40 | USD -4,489.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 52.06% | USD -223.12 | USD -43,286.00 | USD -4,550.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 51.55% | USD -232.22 | USD -45,051.40 | USD -4,559.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 61.34% | USD -83.12 | USD -16,126.00 | USD -4,410.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 60.31% | USD -92.22 | USD -17,891.40 | USD -4,419.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 59.28% | USD -118.12 | USD -22,916.00 | USD -4,445.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 58.76% | USD -127.22 | USD -24,681.40 | USD -4,454.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 56.19% | USD -153.12 | USD -29,706.00 | USD -4,480.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 55.67% | USD -162.22 | USD -31,471.40 | USD -4,489.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 52.06% | USD -223.12 | USD -43,286.00 | USD -4,550.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 51.55% | USD -232.22 | USD -45,051.40 | USD -4,559.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 189 | 62.43% | USD -130.29 | USD -24,624.00 | USD -8,398.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 189 | 62.43% | USD -139.39 | USD -26,343.90 | USD -8,407.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 189 | 61.38% | USD -165.29 | USD -31,239.00 | USD -8,433.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 189 | 60.32% | USD -174.39 | USD -32,958.90 | USD -8,442.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 189 | 59.79% | USD -200.29 | USD -37,854.00 | USD -8,468.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 189 | 59.79% | USD -209.39 | USD -39,573.90 | USD -8,477.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 189 | 53.44% | USD -270.29 | USD -51,084.00 | USD -8,538.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 189 | 52.91% | USD -279.39 | USD -52,803.90 | USD -8,547.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 189 | 62.43% | USD -130.29 | USD -24,624.00 | USD -8,398.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 189 | 62.43% | USD -139.39 | USD -26,343.90 | USD -8,407.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 189 | 61.38% | USD -165.29 | USD -31,239.00 | USD -8,433.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 189 | 60.32% | USD -174.39 | USD -32,958.90 | USD -8,442.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 189 | 59.79% | USD -200.29 | USD -37,854.00 | USD -8,468.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 189 | 59.79% | USD -209.39 | USD -39,573.90 | USD -8,477.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 189 | 53.44% | USD -270.29 | USD -51,084.00 | USD -8,538.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 189 | 52.91% | USD -279.39 | USD -52,803.90 | USD -8,547.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 189 | 61.38% | USD -139.20 | USD -26,309.00 | USD -8,398.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 189 | 60.85% | USD -148.30 | USD -28,028.90 | USD -8,407.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 189 | 59.79% | USD -174.20 | USD -32,924.00 | USD -8,433.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 189 | 59.26% | USD -183.30 | USD -34,643.90 | USD -8,442.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 189 | 58.20% | USD -209.20 | USD -39,539.00 | USD -8,468.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 189 | 58.20% | USD -218.30 | USD -41,258.90 | USD -8,477.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 189 | 52.91% | USD -279.20 | USD -52,769.00 | USD -8,538.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 189 | 51.85% | USD -288.30 | USD -54,488.90 | USD -8,547.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 163 | 61.35% | USD -281.18 | USD -45,833.00 | USD -9,039.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 163 | 61.35% | USD -290.28 | USD -47,316.30 | USD -9,048.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 163 | 60.74% | USD -316.18 | USD -51,538.00 | USD -9,074.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 163 | 60.74% | USD -325.28 | USD -53,021.30 | USD -9,083.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 163 | 60.12% | USD -351.18 | USD -57,243.00 | USD -9,109.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 163 | 60.12% | USD -360.28 | USD -58,726.30 | USD -9,118.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 163 | 58.28% | USD -421.18 | USD -68,653.00 | USD -9,179.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 163 | 57.67% | USD -430.28 | USD -70,136.30 | USD -9,188.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 65.88% | USD -239.52 | USD -40,719.00 | USD -9,039.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 65.29% | USD -248.62 | USD -42,266.00 | USD -9,048.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 64.71% | USD -274.52 | USD -46,669.00 | USD -9,074.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 64.71% | USD -283.62 | USD -48,216.00 | USD -9,083.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 64.12% | USD -309.52 | USD -52,619.00 | USD -9,109.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 64.12% | USD -318.62 | USD -54,166.00 | USD -9,118.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 61.76% | USD -379.52 | USD -64,519.00 | USD -9,179.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 61.76% | USD -388.62 | USD -66,066.00 | USD -9,188.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 187 | 61.50% | USD -188.77 | USD -35,300.00 | USD -12,074.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 187 | 60.96% | USD -197.87 | USD -37,001.70 | USD -12,083.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 187 | 59.89% | USD -223.77 | USD -41,845.00 | USD -12,109.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 187 | 59.36% | USD -232.87 | USD -43,546.70 | USD -12,118.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 187 | 58.29% | USD -258.77 | USD -48,390.00 | USD -12,144.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 187 | 57.22% | USD -267.87 | USD -50,091.70 | USD -12,153.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 187 | 53.48% | USD -328.77 | USD -61,480.00 | USD -12,214.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 187 | 52.94% | USD -337.87 | USD -63,181.70 | USD -12,223.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 32 | 43.75% | USD -1,304.94 | USD -41,758.00 | USD -8,709.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 32 | 43.75% | USD -1,314.04 | USD -42,049.20 | USD -8,718.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 32 | 43.75% | USD -1,339.94 | USD -42,878.00 | USD -8,744.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 32 | 43.75% | USD -1,349.04 | USD -43,169.20 | USD -8,753.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 32 | 43.75% | USD -1,374.94 | USD -43,998.00 | USD -8,779.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 32 | 43.75% | USD -1,384.04 | USD -44,289.20 | USD -8,788.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 32 | 43.75% | USD -1,444.94 | USD -46,238.00 | USD -8,849.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 32 | 40.62% | USD -1,454.04 | USD -46,529.20 | USD -8,858.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 163 | 65.64% | USD -262.44 | USD -42,778.00 | USD -10,261.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 163 | 65.03% | USD -271.54 | USD -44,261.30 | USD -10,270.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 163 | 64.42% | USD -297.44 | USD -48,483.00 | USD -10,296.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 163 | 64.42% | USD -306.54 | USD -49,966.30 | USD -10,305.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 163 | 64.42% | USD -332.44 | USD -54,188.00 | USD -10,331.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 163 | 64.42% | USD -341.54 | USD -55,671.30 | USD -10,340.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 163 | 61.96% | USD -402.44 | USD -65,598.00 | USD -10,401.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 163 | 61.96% | USD -411.54 | USD -67,081.30 | USD -10,410.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 187 | 61.50% | USD -188.77 | USD -35,300.00 | USD -12,074.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 187 | 60.96% | USD -197.87 | USD -37,001.70 | USD -12,083.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 187 | 59.89% | USD -223.77 | USD -41,845.00 | USD -12,109.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 187 | 59.36% | USD -232.87 | USD -43,546.70 | USD -12,118.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 187 | 58.29% | USD -258.77 | USD -48,390.00 | USD -12,144.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 187 | 57.22% | USD -267.87 | USD -50,091.70 | USD -12,153.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 187 | 53.48% | USD -328.77 | USD -61,480.00 | USD -12,214.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 187 | 52.94% | USD -337.87 | USD -63,181.70 | USD -12,223.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/194 (0) | 29.90% (23.90–36.68%) | USD -25.54 | USD -4,955.40 | USD -429.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/194 (0) | 55.67% (48.64–62.48%) | USD -162.22 | USD -31,471.40 | USD -4,489.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/194 (0) | 35.05% (28.69–42.00%) | USD -16.58 | USD -3,216.40 | USD -2,164.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/194 (0) | 29.90% (23.90–36.68%) | USD -127.72 | USD -24,777.00 | USD -2,148.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/194 (0) | 29.90% (23.90–36.68%) | USD -25.54 | USD -4,955.40 | USD -429.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/194 (0) | 55.67% (48.64–62.48%) | USD -162.22 | USD -31,471.40 | USD -4,489.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/194 (0) | 35.05% (28.69–42.00%) | USD -16.58 | USD -3,216.40 | USD -2,164.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/194 (0) | 29.90% (23.90–36.68%) | USD -127.72 | USD -24,777.00 | USD -2,148.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 29.90% (23.90–36.68%) | USD -25.54 | USD -4,955.40 | USD -429.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 55.67% (48.64–62.48%) | USD -162.22 | USD -31,471.40 | USD -4,489.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 35.05% (28.69–42.00%) | USD -16.58 | USD -3,216.40 | USD -2,164.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 29.90% (23.90–36.68%) | USD -127.72 | USD -24,777.00 | USD -2,148.00 |
| HOLD_10_SESSIONS | 1 : 1 | 189/194 (5) | 27.51% (21.64–34.28%) | USD -13.63 | USD -2,575.40 | USD -1,030.60 |
| HOLD_10_SESSIONS | 1 : 6 | 189/194 (5) | 59.79% (52.67–66.52%) | USD -209.39 | USD -39,573.90 | USD -8,477.10 |
| HOLD_10_SESSIONS | 6 : 1 | 189/194 (5) | 35.98% (29.48–43.04%) | USD 114.00 | USD 21,546.10 | USD -2,602.10 |
| HOLD_10_SESSIONS | 5 : 5 | 189/194 (5) | 27.51% (21.64–34.28%) | USD -68.13 | USD -12,877.00 | USD -5,153.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 189/194 (5) | 27.51% (21.64–34.28%) | USD -13.63 | USD -2,575.40 | USD -1,030.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 189/194 (5) | 59.79% (52.67–66.52%) | USD -209.39 | USD -39,573.90 | USD -8,477.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 189/194 (5) | 35.98% (29.48–43.04%) | USD 114.00 | USD 21,546.10 | USD -2,602.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 189/194 (5) | 27.51% (21.64–34.28%) | USD -68.13 | USD -12,877.00 | USD -5,153.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 189/194 (5) | 26.45% (20.68–33.17%) | USD -16.25 | USD -3,070.40 | USD -1,030.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 189/194 (5) | 58.20% (51.07–65.00%) | USD -218.30 | USD -41,258.90 | USD -8,477.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 189/194 (5) | 35.45% (28.98–42.50%) | USD 104.58 | USD 19,766.10 | USD -2,551.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 189/194 (5) | 26.45% (20.68–33.17%) | USD -81.23 | USD -15,352.00 | USD -5,153.00 |
| HOLD_15_SESSIONS | 1 : 1 | 163/194 (31) | 31.29% (24.67–38.77%) | USD -23.57 | USD -3,841.80 | USD -724.60 |
| HOLD_15_SESSIONS | 1 : 6 | 163/194 (31) | 60.12% (52.46–67.32%) | USD -360.28 | USD -58,726.30 | USD -9,118.10 |
| HOLD_15_SESSIONS | 6 : 1 | 163/194 (31) | 35.58% (28.64–43.19%) | USD 195.30 | USD 31,833.70 | USD -2,810.10 |
| HOLD_15_SESSIONS | 5 : 5 | 163/194 (31) | 31.29% (24.67–38.77%) | USD -117.85 | USD -19,209.00 | USD -3,623.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 170/194 (24) | 30.59% (24.15–37.88%) | USD -26.54 | USD -4,511.00 | USD -724.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 170/194 (24) | 64.12% (56.67–70.94%) | USD -318.62 | USD -54,166.00 | USD -9,118.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 170/194 (24) | 34.12% (27.41–41.52%) | USD 132.88 | USD 22,589.00 | USD -2,810.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 170/194 (24) | 30.59% (24.15–37.88%) | USD -132.68 | USD -22,555.00 | USD -3,623.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 187/194 (7) | 24.60% (18.98–31.24%) | USD -22.73 | USD -4,251.20 | USD -1,148.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 187/194 (7) | 57.22% (50.05–64.09%) | USD -267.87 | USD -50,091.70 | USD -12,153.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 187/194 (7) | 35.29% (28.80–42.38%) | USD 108.73 | USD 20,333.30 | USD -2,551.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 187/194 (7) | 24.60% (18.98–31.24%) | USD -113.67 | USD -21,256.00 | USD -5,743.00 |
| HOLD_20_SESSIONS | 1 : 1 | 32/194 (162) | 40.62% (25.52–57.74%) | USD -94.88 | USD -3,036.20 | USD -1,042.60 |
| HOLD_20_SESSIONS | 1 : 6 | 32/194 (162) | 43.75% (28.17–60.67%) | USD -1,384.04 | USD -44,289.20 | USD -8,788.10 |
| HOLD_20_SESSIONS | 6 : 1 | 32/194 (162) | 62.50% (45.25–77.07%) | USD 719.87 | USD 23,035.80 | USD -3,077.10 |
| HOLD_20_SESSIONS | 5 : 5 | 32/194 (162) | 40.62% (25.52–57.74%) | USD -474.41 | USD -15,181.00 | USD -5,213.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 163/194 (31) | 31.90% (25.23–39.40%) | USD -29.58 | USD -4,821.80 | USD -690.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 163/194 (31) | 64.42% (56.81–71.36%) | USD -341.54 | USD -55,671.30 | USD -10,340.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 163/194 (31) | 34.97% (28.07–42.56%) | USD 134.47 | USD 21,918.70 | USD -2,810.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 163/194 (31) | 31.90% (25.23–39.40%) | USD -147.91 | USD -24,109.00 | USD -3,453.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 187/194 (7) | 24.60% (18.98–31.24%) | USD -22.73 | USD -4,251.20 | USD -1,148.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 187/194 (7) | 57.22% (50.05–64.09%) | USD -267.87 | USD -50,091.70 | USD -12,153.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 187/194 (7) | 35.29% (28.80–42.38%) | USD 108.73 | USD 20,333.30 | USD -2,551.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 187/194 (7) | 24.60% (18.98–31.24%) | USD -113.67 | USD -21,256.00 | USD -5,743.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -75% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -50% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -40% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -30% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -25% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -20% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -15% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -10% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| -5% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| 0% | 194/194 | 100.00% | USD 871.19 | USD 104.45 |
| 5% | 35/194 | 18.04% | USD -3,253.31 | USD -9,531.35 |
| 10% | 0/194 | 0.00% | USD -13,745.49 | USD -25,059.15 |
| 20% | 0/194 | 0.00% | USD -35,325.37 | USD -58,369.55 |

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