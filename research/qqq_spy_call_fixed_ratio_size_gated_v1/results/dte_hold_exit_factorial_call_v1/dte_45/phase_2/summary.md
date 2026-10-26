# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 238.88 / USD 1,229.47; mean absolute mismatch USD 990.59; mean match score 19.37%.
- Actual selected contract ratios: {'1:6': 169}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 169; entered cohorts: 169; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 168/169 | 84/84/0 | 50.00% (42.52–57.48%) | USD -186.52 | USD -0.10 | USD -31,334.80 | USD -4,167.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 168/169 | 84/84/0 | 50.00% (42.52–57.48%) | USD -186.52 | USD -0.10 | USD -31,334.80 | USD -4,167.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 168/169 | 84/84/0 | 50.00% (42.52–57.48%) | USD -186.52 | USD -0.10 | USD -31,334.80 | USD -4,167.10 | 1 |
| HOLD_10_SESSIONS | 168/169 | 90/78/0 | 53.57% (46.03–60.95%) | USD -318.33 | USD 22.90 | USD -53,479.80 | USD -5,841.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 168/169 | 90/78/0 | 53.57% (46.03–60.95%) | USD -318.33 | USD 22.90 | USD -53,479.80 | USD -5,841.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 168/169 | 90/78/0 | 53.57% (46.03–60.95%) | USD -318.33 | USD 22.90 | USD -53,479.80 | USD -5,841.10 | 1 |
| HOLD_15_SESSIONS | 164/169 | 94/70/0 | 57.32% (49.66–64.63%) | USD -279.65 | USD 155.40 | USD -45,863.40 | USD -9,382.10 | 5 |
| HOLD_15_OR_DTE_LE_7 | 164/169 | 94/70/0 | 57.32% (49.66–64.63%) | USD -279.65 | USD 155.40 | USD -45,863.40 | USD -9,382.10 | 5 |
| HOLD_15_OR_DTE_LE_14 | 164/169 | 94/70/0 | 57.32% (49.66–64.63%) | USD -279.65 | USD 155.40 | USD -45,863.40 | USD -9,382.10 | 5 |
| HOLD_20_SESSIONS | 158/169 | 96/62/0 | 60.76% (52.98–68.03%) | USD -456.83 | USD 208.90 | USD -72,179.80 | USD -13,560.10 | 11 |
| HOLD_20_OR_DTE_LE_7 | 158/169 | 96/62/0 | 60.76% (52.98–68.03%) | USD -456.83 | USD 208.90 | USD -72,179.80 | USD -13,560.10 | 11 |
| HOLD_20_OR_DTE_LE_14 | 162/169 | 101/61/0 | 62.35% (54.68–69.44%) | USD -379.36 | USD 250.40 | USD -61,456.20 | USD -13,560.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 18.76 | USD -126.18 |
| HOLD_5_OR_DTE_LE_7 | USD 18.76 | USD -126.18 |
| HOLD_5_OR_DTE_LE_14 | USD 18.76 | USD -126.18 |
| HOLD_10_SESSIONS | USD 49.59 | USD -288.82 |
| HOLD_10_OR_DTE_LE_7 | USD 49.59 | USD -288.82 |
| HOLD_10_OR_DTE_LE_14 | USD 49.59 | USD -288.82 |
| HOLD_15_SESSIONS | USD 57.37 | USD -257.93 |
| HOLD_15_OR_DTE_LE_7 | USD 57.37 | USD -257.93 |
| HOLD_15_OR_DTE_LE_14 | USD 57.37 | USD -257.93 |
| HOLD_20_SESSIONS | USD 100.97 | USD -478.71 |
| HOLD_20_OR_DTE_LE_7 | USD 100.97 | USD -478.71 |
| HOLD_20_OR_DTE_LE_14 | USD 82.19 | USD -382.44 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 168 | 54.76% | USD -107.42 | USD -18,046.00 | USD -4,088.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 168 | 54.17% | USD -116.52 | USD -19,574.80 | USD -4,097.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 168 | 52.98% | USD -142.42 | USD -23,926.00 | USD -4,123.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 168 | 52.38% | USD -151.52 | USD -25,454.80 | USD -4,132.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 168 | 50.60% | USD -177.42 | USD -29,806.00 | USD -4,158.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 168 | 50.00% | USD -186.52 | USD -31,334.80 | USD -4,167.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 168 | 45.24% | USD -247.42 | USD -41,566.00 | USD -4,228.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 168 | 45.24% | USD -256.52 | USD -43,094.80 | USD -4,237.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 168 | 54.76% | USD -107.42 | USD -18,046.00 | USD -4,088.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 168 | 54.17% | USD -116.52 | USD -19,574.80 | USD -4,097.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 168 | 52.98% | USD -142.42 | USD -23,926.00 | USD -4,123.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 168 | 52.38% | USD -151.52 | USD -25,454.80 | USD -4,132.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 168 | 50.60% | USD -177.42 | USD -29,806.00 | USD -4,158.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 168 | 50.00% | USD -186.52 | USD -31,334.80 | USD -4,167.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 168 | 45.24% | USD -247.42 | USD -41,566.00 | USD -4,228.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 168 | 45.24% | USD -256.52 | USD -43,094.80 | USD -4,237.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 168 | 54.76% | USD -107.42 | USD -18,046.00 | USD -4,088.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 168 | 54.17% | USD -116.52 | USD -19,574.80 | USD -4,097.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 168 | 52.98% | USD -142.42 | USD -23,926.00 | USD -4,123.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 168 | 52.38% | USD -151.52 | USD -25,454.80 | USD -4,132.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 168 | 50.60% | USD -177.42 | USD -29,806.00 | USD -4,158.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 168 | 50.00% | USD -186.52 | USD -31,334.80 | USD -4,167.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 168 | 45.24% | USD -247.42 | USD -41,566.00 | USD -4,228.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 168 | 45.24% | USD -256.52 | USD -43,094.80 | USD -4,237.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 168 | 56.55% | USD -239.23 | USD -40,191.00 | USD -5,762.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 168 | 55.95% | USD -248.33 | USD -41,719.80 | USD -5,771.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 168 | 55.36% | USD -274.23 | USD -46,071.00 | USD -5,797.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 168 | 55.36% | USD -283.33 | USD -47,599.80 | USD -5,806.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 168 | 54.17% | USD -309.23 | USD -51,951.00 | USD -5,832.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 168 | 53.57% | USD -318.33 | USD -53,479.80 | USD -5,841.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 168 | 49.40% | USD -379.23 | USD -63,711.00 | USD -5,902.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 168 | 49.40% | USD -388.33 | USD -65,239.80 | USD -5,911.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 168 | 56.55% | USD -239.23 | USD -40,191.00 | USD -5,762.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 168 | 55.95% | USD -248.33 | USD -41,719.80 | USD -5,771.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 168 | 55.36% | USD -274.23 | USD -46,071.00 | USD -5,797.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 168 | 55.36% | USD -283.33 | USD -47,599.80 | USD -5,806.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 168 | 54.17% | USD -309.23 | USD -51,951.00 | USD -5,832.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 168 | 53.57% | USD -318.33 | USD -53,479.80 | USD -5,841.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 168 | 49.40% | USD -379.23 | USD -63,711.00 | USD -5,902.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 168 | 49.40% | USD -388.33 | USD -65,239.80 | USD -5,911.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 168 | 56.55% | USD -239.23 | USD -40,191.00 | USD -5,762.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 168 | 55.95% | USD -248.33 | USD -41,719.80 | USD -5,771.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 168 | 55.36% | USD -274.23 | USD -46,071.00 | USD -5,797.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 168 | 55.36% | USD -283.33 | USD -47,599.80 | USD -5,806.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 168 | 54.17% | USD -309.23 | USD -51,951.00 | USD -5,832.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 168 | 53.57% | USD -318.33 | USD -53,479.80 | USD -5,841.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 168 | 49.40% | USD -379.23 | USD -63,711.00 | USD -5,902.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 168 | 49.40% | USD -388.33 | USD -65,239.80 | USD -5,911.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 164 | 59.15% | USD -200.55 | USD -32,891.00 | USD -9,303.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 164 | 59.15% | USD -209.65 | USD -34,383.40 | USD -9,312.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 164 | 59.15% | USD -235.55 | USD -38,631.00 | USD -9,338.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 164 | 57.93% | USD -244.65 | USD -40,123.40 | USD -9,347.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 164 | 57.32% | USD -270.55 | USD -44,371.00 | USD -9,373.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 164 | 57.32% | USD -279.65 | USD -45,863.40 | USD -9,382.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 164 | 54.27% | USD -340.55 | USD -55,851.00 | USD -9,443.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 164 | 54.27% | USD -349.65 | USD -57,343.40 | USD -9,452.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 164 | 59.15% | USD -200.55 | USD -32,891.00 | USD -9,303.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 164 | 59.15% | USD -209.65 | USD -34,383.40 | USD -9,312.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 164 | 59.15% | USD -235.55 | USD -38,631.00 | USD -9,338.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 164 | 57.93% | USD -244.65 | USD -40,123.40 | USD -9,347.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 164 | 57.32% | USD -270.55 | USD -44,371.00 | USD -9,373.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 164 | 57.32% | USD -279.65 | USD -45,863.40 | USD -9,382.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 164 | 54.27% | USD -340.55 | USD -55,851.00 | USD -9,443.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 164 | 54.27% | USD -349.65 | USD -57,343.40 | USD -9,452.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 164 | 59.15% | USD -200.55 | USD -32,891.00 | USD -9,303.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 164 | 59.15% | USD -209.65 | USD -34,383.40 | USD -9,312.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 164 | 59.15% | USD -235.55 | USD -38,631.00 | USD -9,338.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 164 | 57.93% | USD -244.65 | USD -40,123.40 | USD -9,347.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 164 | 57.32% | USD -270.55 | USD -44,371.00 | USD -9,373.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 164 | 57.32% | USD -279.65 | USD -45,863.40 | USD -9,382.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 164 | 54.27% | USD -340.55 | USD -55,851.00 | USD -9,443.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 164 | 54.27% | USD -349.65 | USD -57,343.40 | USD -9,452.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 158 | 62.03% | USD -377.73 | USD -59,682.00 | USD -13,481.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 158 | 62.03% | USD -386.83 | USD -61,119.80 | USD -13,490.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 158 | 60.76% | USD -412.73 | USD -65,212.00 | USD -13,516.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 158 | 60.76% | USD -421.83 | USD -66,649.80 | USD -13,525.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 158 | 60.76% | USD -447.73 | USD -70,742.00 | USD -13,551.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 158 | 60.76% | USD -456.83 | USD -72,179.80 | USD -13,560.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 158 | 58.23% | USD -517.73 | USD -81,802.00 | USD -13,621.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 158 | 56.96% | USD -526.83 | USD -83,239.80 | USD -13,630.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 158 | 62.03% | USD -377.73 | USD -59,682.00 | USD -13,481.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 158 | 62.03% | USD -386.83 | USD -61,119.80 | USD -13,490.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 158 | 60.76% | USD -412.73 | USD -65,212.00 | USD -13,516.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 158 | 60.76% | USD -421.83 | USD -66,649.80 | USD -13,525.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 158 | 60.76% | USD -447.73 | USD -70,742.00 | USD -13,551.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 158 | 60.76% | USD -456.83 | USD -72,179.80 | USD -13,560.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 158 | 58.23% | USD -517.73 | USD -81,802.00 | USD -13,621.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 158 | 56.96% | USD -526.83 | USD -83,239.80 | USD -13,630.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 162 | 63.58% | USD -300.26 | USD -48,642.00 | USD -13,481.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 162 | 63.58% | USD -309.36 | USD -50,116.20 | USD -13,490.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 162 | 62.96% | USD -335.26 | USD -54,312.00 | USD -13,516.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 162 | 62.96% | USD -344.36 | USD -55,786.20 | USD -13,525.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 162 | 62.35% | USD -370.26 | USD -59,982.00 | USD -13,551.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 162 | 62.35% | USD -379.36 | USD -61,456.20 | USD -13,560.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 162 | 58.02% | USD -440.26 | USD -71,322.00 | USD -13,621.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 162 | 57.41% | USD -449.36 | USD -72,796.20 | USD -13,630.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 168/169 (1) | 32.14% (25.55–39.54%) | USD -24.87 | USD -4,177.80 | USD -590.60 |
| HOLD_5_SESSIONS | 1 : 6 | 168/169 (1) | 50.00% (42.52–57.48%) | USD -186.52 | USD -31,334.80 | USD -4,167.10 |
| HOLD_5_SESSIONS | 6 : 1 | 168/169 (1) | 38.10% (31.10–45.63%) | USD 12.44 | USD 2,090.20 | USD -1,908.10 |
| HOLD_5_SESSIONS | 5 : 5 | 168/169 (1) | 32.14% (25.55–39.54%) | USD -124.34 | USD -20,889.00 | USD -2,953.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 168/169 (1) | 32.14% (25.55–39.54%) | USD -24.87 | USD -4,177.80 | USD -590.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 168/169 (1) | 50.00% (42.52–57.48%) | USD -186.52 | USD -31,334.80 | USD -4,167.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 168/169 (1) | 38.10% (31.10–45.63%) | USD 12.44 | USD 2,090.20 | USD -1,908.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 168/169 (1) | 32.14% (25.55–39.54%) | USD -124.34 | USD -20,889.00 | USD -2,953.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 168/169 (1) | 32.14% (25.55–39.54%) | USD -24.87 | USD -4,177.80 | USD -590.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 168/169 (1) | 50.00% (42.52–57.48%) | USD -186.52 | USD -31,334.80 | USD -4,167.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 168/169 (1) | 38.10% (31.10–45.63%) | USD 12.44 | USD 2,090.20 | USD -1,908.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 168/169 (1) | 32.14% (25.55–39.54%) | USD -124.34 | USD -20,889.00 | USD -2,953.00 |
| HOLD_10_SESSIONS | 1 : 1 | 168/169 (1) | 32.74% (26.10–40.15%) | USD -21.15 | USD -3,552.80 | USD -929.60 |
| HOLD_10_SESSIONS | 1 : 6 | 168/169 (1) | 53.57% (46.03–60.95%) | USD -318.33 | USD -53,479.80 | USD -5,841.10 |
| HOLD_10_SESSIONS | 6 : 1 | 168/169 (1) | 36.31% (29.42–43.81%) | USD 170.30 | USD 28,610.20 | USD -2,402.10 |
| HOLD_10_SESSIONS | 5 : 5 | 168/169 (1) | 32.74% (26.10–40.15%) | USD -105.74 | USD -17,764.00 | USD -4,648.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 168/169 (1) | 32.74% (26.10–40.15%) | USD -21.15 | USD -3,552.80 | USD -929.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 168/169 (1) | 53.57% (46.03–60.95%) | USD -318.33 | USD -53,479.80 | USD -5,841.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 168/169 (1) | 36.31% (29.42–43.81%) | USD 170.30 | USD 28,610.20 | USD -2,402.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 168/169 (1) | 32.74% (26.10–40.15%) | USD -105.74 | USD -17,764.00 | USD -4,648.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 168/169 (1) | 32.74% (26.10–40.15%) | USD -21.15 | USD -3,552.80 | USD -929.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 168/169 (1) | 53.57% (46.03–60.95%) | USD -318.33 | USD -53,479.80 | USD -5,841.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 168/169 (1) | 36.31% (29.42–43.81%) | USD 170.30 | USD 28,610.20 | USD -2,402.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 168/169 (1) | 32.74% (26.10–40.15%) | USD -105.74 | USD -17,764.00 | USD -4,648.00 |
| HOLD_15_SESSIONS | 1 : 1 | 164/169 (5) | 34.15% (27.33–41.69%) | USD -8.22 | USD -1,347.40 | USD -586.60 |
| HOLD_15_SESSIONS | 1 : 6 | 164/169 (5) | 57.32% (49.66–64.63%) | USD -279.65 | USD -45,863.40 | USD -9,382.10 |
| HOLD_15_SESSIONS | 6 : 1 | 164/169 (5) | 35.37% (28.46–42.94%) | USD 222.14 | USD 36,431.60 | USD -2,795.10 |
| HOLD_15_SESSIONS | 5 : 5 | 164/169 (5) | 34.15% (27.33–41.69%) | USD -41.08 | USD -6,737.00 | USD -2,933.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 164/169 (5) | 34.15% (27.33–41.69%) | USD -8.22 | USD -1,347.40 | USD -586.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 164/169 (5) | 57.32% (49.66–64.63%) | USD -279.65 | USD -45,863.40 | USD -9,382.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 164/169 (5) | 35.37% (28.46–42.94%) | USD 222.14 | USD 36,431.60 | USD -2,795.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 164/169 (5) | 34.15% (27.33–41.69%) | USD -41.08 | USD -6,737.00 | USD -2,933.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 164/169 (5) | 34.15% (27.33–41.69%) | USD -8.22 | USD -1,347.40 | USD -586.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 164/169 (5) | 57.32% (49.66–64.63%) | USD -279.65 | USD -45,863.40 | USD -9,382.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 164/169 (5) | 35.37% (28.46–42.94%) | USD 222.14 | USD 36,431.60 | USD -2,795.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 164/169 (5) | 34.15% (27.33–41.69%) | USD -41.08 | USD -6,737.00 | USD -2,933.00 |
| HOLD_20_SESSIONS | 1 : 1 | 158/169 (11) | 31.65% (24.90–39.26%) | USD -1.41 | USD -222.80 | USD -798.60 |
| HOLD_20_SESSIONS | 1 : 6 | 158/169 (11) | 60.76% (52.98–68.03%) | USD -456.83 | USD -72,179.80 | USD -13,560.10 |
| HOLD_20_SESSIONS | 6 : 1 | 158/169 (11) | 39.87% (32.57–47.66%) | USD 446.96 | USD 70,620.20 | USD -2,377.10 |
| HOLD_20_SESSIONS | 5 : 5 | 158/169 (11) | 31.65% (24.90–39.26%) | USD -7.05 | USD -1,114.00 | USD -3,993.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 158/169 (11) | 31.65% (24.90–39.26%) | USD -1.41 | USD -222.80 | USD -798.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 158/169 (11) | 60.76% (52.98–68.03%) | USD -456.83 | USD -72,179.80 | USD -13,560.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 158/169 (11) | 39.87% (32.57–47.66%) | USD 446.96 | USD 70,620.20 | USD -2,377.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 158/169 (11) | 31.65% (24.90–39.26%) | USD -7.05 | USD -1,114.00 | USD -3,993.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 162/169 (7) | 32.10% (25.40–39.63%) | USD -4.16 | USD -673.20 | USD -798.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 162/169 (7) | 62.35% (54.68–69.44%) | USD -379.36 | USD -61,456.20 | USD -13,560.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 162/169 (7) | 38.27% (31.14–45.95%) | USD 350.27 | USD 56,743.80 | USD -2,568.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 162/169 (7) | 32.10% (25.40–39.63%) | USD -20.78 | USD -3,366.00 | USD -3,993.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -75% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -50% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -40% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -30% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -25% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -20% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -15% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -10% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| -5% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| 0% | 169/169 | 100.00% | USD 951.04 | USD 159.45 |
| 5% | 55/169 | 32.54% | USD -1,711.31 | USD -7,410.05 |
| 10% | 3/169 | 1.78% | USD -11,546.64 | USD -24,218.55 |
| 20% | 1/169 | 0.59% | USD -32,743.56 | USD -57,835.55 |

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