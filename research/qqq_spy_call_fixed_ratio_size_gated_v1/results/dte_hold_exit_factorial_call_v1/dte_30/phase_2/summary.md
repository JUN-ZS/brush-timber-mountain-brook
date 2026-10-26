# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 24–36 (target 30); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 193.93 / USD 1,034.12; mean absolute mismatch USD 840.19; mean match score 19.46%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 194/195 | 105/89/0 | 54.12% (47.10–60.99%) | USD -186.07 | USD 33.40 | USD -36,098.40 | USD -4,296.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 194/195 | 105/89/0 | 54.12% (47.10–60.99%) | USD -186.07 | USD 33.40 | USD -36,098.40 | USD -4,296.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 194/195 | 105/89/0 | 54.12% (47.10–60.99%) | USD -186.07 | USD 33.40 | USD -36,098.40 | USD -4,296.10 | 1 |
| HOLD_10_SESSIONS | 190/195 | 107/83/0 | 56.32% (49.21–63.17%) | USD -296.29 | USD 86.90 | USD -56,296.00 | USD -6,257.10 | 5 |
| HOLD_10_OR_DTE_LE_7 | 190/195 | 107/83/0 | 56.32% (49.21–63.17%) | USD -296.29 | USD 86.90 | USD -56,296.00 | USD -6,257.10 | 5 |
| HOLD_10_OR_DTE_LE_14 | 190/195 | 107/83/0 | 56.32% (49.21–63.17%) | USD -294.03 | USD 85.90 | USD -55,866.00 | USD -6,257.10 | 5 |
| HOLD_15_SESSIONS | 168/195 | 103/65/0 | 61.31% (53.77–68.34%) | USD -264.84 | USD 258.40 | USD -44,493.80 | USD -10,567.10 | 27 |
| HOLD_15_OR_DTE_LE_7 | 173/195 | 109/64/0 | 63.01% (55.60–69.84%) | USD -242.00 | USD 255.90 | USD -41,866.30 | USD -10,567.10 | 22 |
| HOLD_15_OR_DTE_LE_14 | 189/195 | 102/87/0 | 53.97% (46.85–60.92%) | USD -285.42 | USD 90.90 | USD -53,944.90 | USD -6,257.10 | 6 |
| HOLD_20_SESSIONS | 45/195 | 27/18/0 | 60.00% (45.45–72.98%) | USD -937.88 | USD 254.90 | USD -42,204.50 | USD -7,819.10 | 150 |
| HOLD_20_OR_DTE_LE_7 | 165/195 | 103/62/0 | 62.42% (54.83–69.45%) | USD -300.96 | USD 264.90 | USD -49,658.50 | USD -10,567.10 | 30 |
| HOLD_20_OR_DTE_LE_14 | 189/195 | 102/87/0 | 53.97% (46.85–60.92%) | USD -285.42 | USD 90.90 | USD -53,944.90 | USD -6,257.10 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 13.06 | USD -120.03 |
| HOLD_5_OR_DTE_LE_7 | USD 13.06 | USD -120.03 |
| HOLD_5_OR_DTE_LE_14 | USD 13.06 | USD -120.03 |
| HOLD_10_SESSIONS | USD 37.81 | USD -255.00 |
| HOLD_10_OR_DTE_LE_7 | USD 37.81 | USD -255.00 |
| HOLD_10_OR_DTE_LE_14 | USD 35.96 | USD -250.89 |
| HOLD_15_SESSIONS | USD 49.79 | USD -235.54 |
| HOLD_15_OR_DTE_LE_7 | USD 44.81 | USD -207.71 |
| HOLD_15_OR_DTE_LE_14 | USD 35.87 | USD -242.19 |
| HOLD_20_SESSIONS | USD 99.49 | USD -958.27 |
| HOLD_20_OR_DTE_LE_7 | USD 65.16 | USD -287.02 |
| HOLD_20_OR_DTE_LE_14 | USD 35.87 | USD -242.19 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 194 | 59.28% | USD -106.97 | USD -20,753.00 | USD -4,217.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 194 | 59.28% | USD -116.07 | USD -22,518.40 | USD -4,226.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 194 | 58.25% | USD -141.97 | USD -27,543.00 | USD -4,252.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 194 | 57.73% | USD -151.07 | USD -29,308.40 | USD -4,261.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 194 | 56.70% | USD -176.97 | USD -34,333.00 | USD -4,287.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 194 | 54.12% | USD -186.07 | USD -36,098.40 | USD -4,296.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 194 | 46.39% | USD -246.97 | USD -47,913.00 | USD -4,357.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 194 | 45.36% | USD -256.07 | USD -49,678.40 | USD -4,366.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 194 | 59.28% | USD -106.97 | USD -20,753.00 | USD -4,217.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 194 | 59.28% | USD -116.07 | USD -22,518.40 | USD -4,226.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 194 | 58.25% | USD -141.97 | USD -27,543.00 | USD -4,252.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 194 | 57.73% | USD -151.07 | USD -29,308.40 | USD -4,261.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 194 | 56.70% | USD -176.97 | USD -34,333.00 | USD -4,287.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 194 | 54.12% | USD -186.07 | USD -36,098.40 | USD -4,296.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 194 | 46.39% | USD -246.97 | USD -47,913.00 | USD -4,357.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 194 | 45.36% | USD -256.07 | USD -49,678.40 | USD -4,366.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.28% | USD -106.97 | USD -20,753.00 | USD -4,217.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 59.28% | USD -116.07 | USD -22,518.40 | USD -4,226.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 58.25% | USD -141.97 | USD -27,543.00 | USD -4,252.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 57.73% | USD -151.07 | USD -29,308.40 | USD -4,261.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 56.70% | USD -176.97 | USD -34,333.00 | USD -4,287.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 54.12% | USD -186.07 | USD -36,098.40 | USD -4,296.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 46.39% | USD -246.97 | USD -47,913.00 | USD -4,357.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 45.36% | USD -256.07 | USD -49,678.40 | USD -4,366.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 190 | 61.05% | USD -217.19 | USD -41,267.00 | USD -6,178.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 190 | 60.53% | USD -226.29 | USD -42,996.00 | USD -6,187.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 190 | 60.00% | USD -252.19 | USD -47,917.00 | USD -6,213.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 190 | 60.00% | USD -261.29 | USD -49,646.00 | USD -6,222.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 190 | 58.42% | USD -287.19 | USD -54,567.00 | USD -6,248.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 190 | 56.32% | USD -296.29 | USD -56,296.00 | USD -6,257.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 190 | 53.16% | USD -357.19 | USD -67,867.00 | USD -6,318.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 190 | 52.11% | USD -366.29 | USD -69,596.00 | USD -6,327.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 190 | 61.05% | USD -217.19 | USD -41,267.00 | USD -6,178.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 190 | 60.53% | USD -226.29 | USD -42,996.00 | USD -6,187.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 190 | 60.00% | USD -252.19 | USD -47,917.00 | USD -6,213.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 190 | 60.00% | USD -261.29 | USD -49,646.00 | USD -6,222.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 190 | 58.42% | USD -287.19 | USD -54,567.00 | USD -6,248.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 190 | 56.32% | USD -296.29 | USD -56,296.00 | USD -6,257.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 190 | 53.16% | USD -357.19 | USD -67,867.00 | USD -6,318.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 190 | 52.11% | USD -366.29 | USD -69,596.00 | USD -6,327.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 190 | 60.53% | USD -214.93 | USD -40,837.00 | USD -6,178.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 190 | 60.00% | USD -224.03 | USD -42,566.00 | USD -6,187.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 190 | 59.47% | USD -249.93 | USD -47,487.00 | USD -6,213.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 190 | 59.47% | USD -259.03 | USD -49,216.00 | USD -6,222.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 190 | 57.89% | USD -284.93 | USD -54,137.00 | USD -6,248.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 190 | 56.32% | USD -294.03 | USD -55,866.00 | USD -6,257.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 190 | 52.63% | USD -354.93 | USD -67,437.00 | USD -6,318.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 190 | 52.11% | USD -364.03 | USD -69,166.00 | USD -6,327.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 168 | 63.10% | USD -185.74 | USD -31,205.00 | USD -10,488.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 168 | 63.10% | USD -194.84 | USD -32,733.80 | USD -10,497.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 168 | 62.50% | USD -220.74 | USD -37,085.00 | USD -10,523.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 168 | 62.50% | USD -229.84 | USD -38,613.80 | USD -10,532.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 168 | 61.31% | USD -255.74 | USD -42,965.00 | USD -10,558.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 168 | 61.31% | USD -264.84 | USD -44,493.80 | USD -10,567.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 168 | 57.14% | USD -325.74 | USD -54,725.00 | USD -10,628.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 168 | 57.14% | USD -334.84 | USD -56,253.80 | USD -10,637.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 173 | 66.47% | USD -162.90 | USD -28,182.00 | USD -10,488.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 173 | 66.47% | USD -172.00 | USD -29,756.30 | USD -10,497.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 173 | 65.32% | USD -197.90 | USD -34,237.00 | USD -10,523.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 173 | 65.32% | USD -207.00 | USD -35,811.30 | USD -10,532.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 173 | 63.01% | USD -232.90 | USD -40,292.00 | USD -10,558.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 173 | 63.01% | USD -242.00 | USD -41,866.30 | USD -10,567.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 173 | 60.12% | USD -302.90 | USD -52,402.00 | USD -10,628.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 173 | 60.12% | USD -312.00 | USD -53,976.30 | USD -10,637.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 189 | 57.67% | USD -206.32 | USD -38,995.00 | USD -6,178.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 189 | 56.61% | USD -215.42 | USD -40,714.90 | USD -6,187.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 189 | 56.08% | USD -241.32 | USD -45,610.00 | USD -6,213.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 189 | 55.56% | USD -250.42 | USD -47,329.90 | USD -6,222.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 189 | 54.50% | USD -276.32 | USD -52,225.00 | USD -6,248.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 189 | 53.97% | USD -285.42 | USD -53,944.90 | USD -6,257.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 189 | 52.38% | USD -346.32 | USD -65,455.00 | USD -6,318.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 189 | 52.38% | USD -355.42 | USD -67,174.90 | USD -6,327.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 45 | 60.00% | USD -858.78 | USD -38,645.00 | USD -7,740.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 45 | 60.00% | USD -867.88 | USD -39,054.50 | USD -7,749.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 45 | 60.00% | USD -893.78 | USD -40,220.00 | USD -7,775.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 45 | 60.00% | USD -902.88 | USD -40,629.50 | USD -7,784.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 45 | 60.00% | USD -928.78 | USD -41,795.00 | USD -7,810.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 45 | 60.00% | USD -937.88 | USD -42,204.50 | USD -7,819.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 45 | 57.78% | USD -998.78 | USD -44,945.00 | USD -7,880.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 45 | 57.78% | USD -1,007.88 | USD -45,354.50 | USD -7,889.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 165 | 64.24% | USD -221.86 | USD -36,607.00 | USD -10,488.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 165 | 64.24% | USD -230.96 | USD -38,108.50 | USD -10,497.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 165 | 63.64% | USD -256.86 | USD -42,382.00 | USD -10,523.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 165 | 63.64% | USD -265.96 | USD -43,883.50 | USD -10,532.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 165 | 62.42% | USD -291.86 | USD -48,157.00 | USD -10,558.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 165 | 62.42% | USD -300.96 | USD -49,658.50 | USD -10,567.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 165 | 60.00% | USD -361.86 | USD -59,707.00 | USD -10,628.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 165 | 60.00% | USD -370.96 | USD -61,208.50 | USD -10,637.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 189 | 57.67% | USD -206.32 | USD -38,995.00 | USD -6,178.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 189 | 56.61% | USD -215.42 | USD -40,714.90 | USD -6,187.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 189 | 56.08% | USD -241.32 | USD -45,610.00 | USD -6,213.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 189 | 55.56% | USD -250.42 | USD -47,329.90 | USD -6,222.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 189 | 54.50% | USD -276.32 | USD -52,225.00 | USD -6,248.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 189 | 53.97% | USD -285.42 | USD -53,944.90 | USD -6,257.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 189 | 52.38% | USD -346.32 | USD -65,455.00 | USD -6,318.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 189 | 52.38% | USD -355.42 | USD -67,174.90 | USD -6,327.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -29.55 | USD -5,732.40 | USD -599.60 |
| HOLD_5_SESSIONS | 1 : 6 | 194/195 (1) | 54.12% (47.10–60.99%) | USD -186.07 | USD -36,098.40 | USD -4,296.10 |
| HOLD_5_SESSIONS | 6 : 1 | 194/195 (1) | 35.05% (28.69–42.00%) | USD -20.76 | USD -4,028.40 | USD -1,843.10 |
| HOLD_5_SESSIONS | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -147.74 | USD -28,662.00 | USD -2,998.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -29.55 | USD -5,732.40 | USD -599.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 194/195 (1) | 54.12% (47.10–60.99%) | USD -186.07 | USD -36,098.40 | USD -4,296.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 194/195 (1) | 35.05% (28.69–42.00%) | USD -20.76 | USD -4,028.40 | USD -1,843.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -147.74 | USD -28,662.00 | USD -2,998.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -29.55 | USD -5,732.40 | USD -599.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/195 (1) | 54.12% (47.10–60.99%) | USD -186.07 | USD -36,098.40 | USD -4,296.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/195 (1) | 35.05% (28.69–42.00%) | USD -20.76 | USD -4,028.40 | USD -1,843.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/195 (1) | 28.87% (22.95–35.60%) | USD -147.74 | USD -28,662.00 | USD -2,998.00 |
| HOLD_10_SESSIONS | 1 : 1 | 190/195 (5) | 28.42% (22.48–35.21%) | USD -27.29 | USD -5,186.00 | USD -1,005.60 |
| HOLD_10_SESSIONS | 1 : 6 | 190/195 (5) | 56.32% (49.21–63.17%) | USD -296.29 | USD -56,296.00 | USD -6,257.10 |
| HOLD_10_SESSIONS | 6 : 1 | 190/195 (5) | 34.21% (27.84–41.21%) | USD 105.23 | USD 19,994.00 | USD -1,979.10 |
| HOLD_10_SESSIONS | 5 : 5 | 190/195 (5) | 28.42% (22.48–35.21%) | USD -136.47 | USD -25,930.00 | USD -5,028.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 190/195 (5) | 28.42% (22.48–35.21%) | USD -27.29 | USD -5,186.00 | USD -1,005.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 190/195 (5) | 56.32% (49.21–63.17%) | USD -296.29 | USD -56,296.00 | USD -6,257.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 190/195 (5) | 34.21% (27.84–41.21%) | USD 105.23 | USD 19,994.00 | USD -1,979.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 190/195 (5) | 28.42% (22.48–35.21%) | USD -136.47 | USD -25,930.00 | USD -5,028.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 190/195 (5) | 27.37% (21.52–34.11%) | USD -28.45 | USD -5,406.00 | USD -1,005.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 190/195 (5) | 56.32% (49.21–63.17%) | USD -294.03 | USD -55,866.00 | USD -6,257.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 190/195 (5) | 34.74% (28.33–41.75%) | USD 94.86 | USD 18,024.00 | USD -1,979.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 190/195 (5) | 27.37% (21.52–34.11%) | USD -142.26 | USD -27,030.00 | USD -5,028.00 |
| HOLD_15_SESSIONS | 1 : 1 | 168/195 (27) | 33.33% (26.65–40.76%) | USD -12.06 | USD -2,026.80 | USD -577.60 |
| HOLD_15_SESSIONS | 1 : 6 | 168/195 (27) | 61.31% (53.77–68.34%) | USD -264.84 | USD -44,493.80 | USD -10,567.10 |
| HOLD_15_SESSIONS | 6 : 1 | 168/195 (27) | 32.14% (25.55–39.54%) | USD 180.39 | USD 30,306.20 | USD -3,052.10 |
| HOLD_15_SESSIONS | 5 : 5 | 168/195 (27) | 33.33% (26.65–40.76%) | USD -60.32 | USD -10,134.00 | USD -2,888.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 173/195 (22) | 31.79% (25.31–39.06%) | USD -12.41 | USD -2,146.80 | USD -577.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 173/195 (22) | 63.01% (55.60–69.84%) | USD -242.00 | USD -41,866.30 | USD -10,567.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 173/195 (22) | 31.79% (25.31–39.06%) | USD 155.14 | USD 26,838.70 | USD -3,052.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 173/195 (22) | 31.79% (25.31–39.06%) | USD -62.05 | USD -10,734.00 | USD -2,888.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 189/195 (6) | 28.57% (22.61–35.39%) | USD -27.10 | USD -5,121.40 | USD -1,005.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 189/195 (6) | 53.97% (46.85–60.92%) | USD -285.42 | USD -53,944.90 | USD -6,257.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 189/195 (6) | 34.39% (27.99–41.41%) | USD 95.74 | USD 18,095.10 | USD -2,823.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 189/195 (6) | 28.57% (22.61–35.39%) | USD -135.49 | USD -25,607.00 | USD -5,028.00 |
| HOLD_20_SESSIONS | 1 : 1 | 45/195 (150) | 40.00% (27.02–54.55%) | USD -82.82 | USD -3,727.00 | USD -1,006.60 |
| HOLD_20_SESSIONS | 1 : 6 | 45/195 (150) | 60.00% (45.45–72.98%) | USD -937.88 | USD -42,204.50 | USD -7,819.10 |
| HOLD_20_SESSIONS | 6 : 1 | 45/195 (150) | 44.44% (30.94–58.82%) | USD 358.12 | USD 16,115.50 | USD -3,416.10 |
| HOLD_20_SESSIONS | 5 : 5 | 45/195 (150) | 40.00% (27.02–54.55%) | USD -414.11 | USD -18,635.00 | USD -5,033.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 165/195 (30) | 30.30% (23.80–37.70%) | USD -5.28 | USD -871.00 | USD -1,282.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 165/195 (30) | 62.42% (54.83–69.45%) | USD -300.96 | USD -49,658.50 | USD -10,567.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 165/195 (30) | 32.12% (25.47–39.58%) | USD 264.01 | USD 43,561.50 | USD -3,283.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 165/195 (30) | 30.30% (23.80–37.70%) | USD -26.39 | USD -4,355.00 | USD -6,413.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 189/195 (6) | 28.57% (22.61–35.39%) | USD -27.10 | USD -5,121.40 | USD -1,005.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 189/195 (6) | 53.97% (46.85–60.92%) | USD -285.42 | USD -53,944.90 | USD -6,257.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 189/195 (6) | 34.39% (27.99–41.41%) | USD 95.74 | USD 18,095.10 | USD -2,823.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 189/195 (6) | 28.57% (22.61–35.39%) | USD -135.49 | USD -25,607.00 | USD -5,028.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -75% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -50% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -40% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -30% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -25% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -20% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -15% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -10% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| -5% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| 0% | 195/195 | 100.00% | USD 800.64 | USD 82.45 |
| 5% | 43/195 | 22.05% | USD -3,077.76 | USD -9,654.05 |
| 10% | 1/195 | 0.51% | USD -13,467.42 | USD -26,462.55 |
| 20% | 1/195 | 0.51% | USD -35,021.49 | USD -60,080.75 |

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