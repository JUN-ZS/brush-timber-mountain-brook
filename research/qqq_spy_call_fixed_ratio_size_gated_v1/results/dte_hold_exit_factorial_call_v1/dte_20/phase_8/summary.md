# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 174.03 / USD 953.63; mean absolute mismatch USD 779.60; mean match score 18.95%.
- Actual selected contract ratios: {'1:6': 194}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 194; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 191/194 | 116/75/0 | 60.73% (53.66–67.38%) | USD -128.37 | USD 129.90 | USD -24,519.10 | USD -5,200.10 | 3 |
| HOLD_5_OR_DTE_LE_7 | 191/194 | 116/75/0 | 60.73% (53.66–67.38%) | USD -128.37 | USD 129.90 | USD -24,519.10 | USD -5,200.10 | 3 |
| HOLD_5_OR_DTE_LE_14 | 194/194 | 107/87/0 | 55.15% (48.12–61.99%) | USD -107.59 | USD 54.40 | USD -20,872.40 | USD -3,479.10 | 0 |
| HOLD_10_SESSIONS | 139/194 | 82/57/0 | 58.99% (50.68–66.82%) | USD -368.37 | USD 165.90 | USD -51,202.90 | USD -9,391.10 | 55 |
| HOLD_10_OR_DTE_LE_7 | 172/194 | 108/64/0 | 62.79% (55.36–69.66%) | USD -117.96 | USD 173.40 | USD -20,289.20 | USD -7,777.10 | 22 |
| HOLD_10_OR_DTE_LE_14 | 194/194 | 108/86/0 | 55.67% (48.64–62.48%) | USD -112.01 | USD 50.40 | USD -21,729.40 | USD -3,479.10 | 0 |
| HOLD_15_SESSIONS | 5/194 | 4/1/0 | 80.00% (37.55–96.38%) | USD 483.90 | USD 902.90 | USD 2,419.50 | USD -1,663.10 | 189 |
| HOLD_15_OR_DTE_LE_7 | 172/194 | 107/65/0 | 62.21% (54.77–69.11%) | USD -124.11 | USD 173.40 | USD -21,347.20 | USD -7,777.10 | 22 |
| HOLD_15_OR_DTE_LE_14 | 194/194 | 108/86/0 | 55.67% (48.64–62.48%) | USD -112.01 | USD 50.40 | USD -21,729.40 | USD -3,479.10 | 0 |
| HOLD_20_SESSIONS | 0/194 | 0/0/0 | — | — | — | — | — | 194 |
| HOLD_20_OR_DTE_LE_7 | 172/194 | 107/65/0 | 62.21% (54.77–69.11%) | USD -124.11 | USD 173.40 | USD -21,347.20 | USD -7,777.10 | 22 |
| HOLD_20_OR_DTE_LE_14 | 194/194 | 108/86/0 | 55.67% (48.64–62.48%) | USD -112.01 | USD 50.40 | USD -21,729.40 | USD -3,479.10 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 9.31 | USD -58.59 |
| HOLD_5_OR_DTE_LE_7 | USD 9.31 | USD -58.59 |
| HOLD_5_OR_DTE_LE_14 | USD 1.45 | USD -29.94 |
| HOLD_10_SESSIONS | USD 79.41 | USD -368.68 |
| HOLD_10_OR_DTE_LE_7 | USD 44.51 | USD -83.37 |
| HOLD_10_OR_DTE_LE_14 | USD 1.08 | USD -33.99 |
| HOLD_15_SESSIONS | USD -55.00 | USD 618.00 |
| HOLD_15_OR_DTE_LE_7 | USD 46.24 | USD -91.26 |
| HOLD_15_OR_DTE_LE_14 | USD 1.08 | USD -33.99 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD 46.24 | USD -91.26 |
| HOLD_20_OR_DTE_LE_14 | USD 1.08 | USD -33.99 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 191 | 63.35% | USD -49.27 | USD -9,411.00 | USD -5,121.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 191 | 63.35% | USD -58.37 | USD -11,149.10 | USD -5,130.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 191 | 61.26% | USD -84.27 | USD -16,096.00 | USD -5,156.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 191 | 61.26% | USD -93.37 | USD -17,834.10 | USD -5,165.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 191 | 60.73% | USD -119.27 | USD -22,781.00 | USD -5,191.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 191 | 60.73% | USD -128.37 | USD -24,519.10 | USD -5,200.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 191 | 56.54% | USD -189.27 | USD -36,151.00 | USD -5,261.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 191 | 56.02% | USD -198.37 | USD -37,889.10 | USD -5,270.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 191 | 63.35% | USD -49.27 | USD -9,411.00 | USD -5,121.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 191 | 63.35% | USD -58.37 | USD -11,149.10 | USD -5,130.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 191 | 61.26% | USD -84.27 | USD -16,096.00 | USD -5,156.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 191 | 61.26% | USD -93.37 | USD -17,834.10 | USD -5,165.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 191 | 60.73% | USD -119.27 | USD -22,781.00 | USD -5,191.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 191 | 60.73% | USD -128.37 | USD -24,519.10 | USD -5,200.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 191 | 56.54% | USD -189.27 | USD -36,151.00 | USD -5,261.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 191 | 56.02% | USD -198.37 | USD -37,889.10 | USD -5,270.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 59.79% | USD -28.49 | USD -5,527.00 | USD -3,400.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 59.79% | USD -37.59 | USD -7,292.40 | USD -3,409.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 58.25% | USD -63.49 | USD -12,317.00 | USD -3,435.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 57.73% | USD -72.59 | USD -14,082.40 | USD -3,444.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 56.19% | USD -98.49 | USD -19,107.00 | USD -3,470.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 55.15% | USD -107.59 | USD -20,872.40 | USD -3,479.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 48.97% | USD -168.49 | USD -32,687.00 | USD -3,540.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 47.94% | USD -177.59 | USD -34,452.40 | USD -3,549.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 139 | 61.15% | USD -289.27 | USD -40,208.00 | USD -9,312.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 139 | 61.15% | USD -298.37 | USD -41,472.90 | USD -9,321.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 139 | 61.15% | USD -324.27 | USD -45,073.00 | USD -9,347.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 139 | 61.15% | USD -333.37 | USD -46,337.90 | USD -9,356.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 139 | 58.99% | USD -359.27 | USD -49,938.00 | USD -9,382.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 139 | 58.99% | USD -368.37 | USD -51,202.90 | USD -9,391.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 139 | 56.12% | USD -429.27 | USD -59,668.00 | USD -9,452.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 139 | 55.40% | USD -438.37 | USD -60,932.90 | USD -9,461.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 172 | 63.37% | USD -38.86 | USD -6,684.00 | USD -7,698.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 172 | 63.37% | USD -47.96 | USD -8,249.20 | USD -7,707.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 172 | 63.37% | USD -73.86 | USD -12,704.00 | USD -7,733.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 172 | 63.37% | USD -82.96 | USD -14,269.20 | USD -7,742.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 172 | 62.79% | USD -108.86 | USD -18,724.00 | USD -7,768.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 172 | 62.79% | USD -117.96 | USD -20,289.20 | USD -7,777.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 172 | 61.05% | USD -178.86 | USD -30,764.00 | USD -7,838.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 172 | 59.88% | USD -187.96 | USD -32,329.20 | USD -7,847.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 60.82% | USD -32.91 | USD -6,384.00 | USD -3,400.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 60.82% | USD -42.01 | USD -8,149.40 | USD -3,409.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 59.28% | USD -67.91 | USD -13,174.00 | USD -3,435.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 58.76% | USD -77.01 | USD -14,939.40 | USD -3,444.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 56.70% | USD -102.91 | USD -19,964.00 | USD -3,470.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 55.67% | USD -112.01 | USD -21,729.40 | USD -3,479.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 47.94% | USD -172.91 | USD -33,544.00 | USD -3,540.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.91% | USD -182.01 | USD -35,309.40 | USD -3,549.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 5 | 80.00% | USD 563.00 | USD 2,815.00 | USD -1,584.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 5 | 80.00% | USD 553.90 | USD 2,769.50 | USD -1,593.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 5 | 80.00% | USD 528.00 | USD 2,640.00 | USD -1,619.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 5 | 80.00% | USD 518.90 | USD 2,594.50 | USD -1,628.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 5 | 80.00% | USD 493.00 | USD 2,465.00 | USD -1,654.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 5 | 80.00% | USD 483.90 | USD 2,419.50 | USD -1,663.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 5 | 80.00% | USD 423.00 | USD 2,115.00 | USD -1,724.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 5 | 80.00% | USD 413.90 | USD 2,069.50 | USD -1,733.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 172 | 63.37% | USD -45.01 | USD -7,742.00 | USD -7,698.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 172 | 63.37% | USD -54.11 | USD -9,307.20 | USD -7,707.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 172 | 63.37% | USD -80.01 | USD -13,762.00 | USD -7,733.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 172 | 62.79% | USD -89.11 | USD -15,327.20 | USD -7,742.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 172 | 62.21% | USD -115.01 | USD -19,782.00 | USD -7,768.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 172 | 62.21% | USD -124.11 | USD -21,347.20 | USD -7,777.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 172 | 60.47% | USD -185.01 | USD -31,822.00 | USD -7,838.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 172 | 59.30% | USD -194.11 | USD -33,387.20 | USD -7,847.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 60.82% | USD -32.91 | USD -6,384.00 | USD -3,400.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 60.82% | USD -42.01 | USD -8,149.40 | USD -3,409.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 59.28% | USD -67.91 | USD -13,174.00 | USD -3,435.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 58.76% | USD -77.01 | USD -14,939.40 | USD -3,444.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 56.70% | USD -102.91 | USD -19,964.00 | USD -3,470.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 55.67% | USD -112.01 | USD -21,729.40 | USD -3,479.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 47.94% | USD -172.91 | USD -33,544.00 | USD -3,540.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.91% | USD -182.01 | USD -35,309.40 | USD -3,549.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 172 | 63.37% | USD -45.01 | USD -7,742.00 | USD -7,698.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 172 | 63.37% | USD -54.11 | USD -9,307.20 | USD -7,707.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 172 | 63.37% | USD -80.01 | USD -13,762.00 | USD -7,733.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 172 | 62.79% | USD -89.11 | USD -15,327.20 | USD -7,742.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 172 | 62.21% | USD -115.01 | USD -19,782.00 | USD -7,768.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 172 | 62.21% | USD -124.11 | USD -21,347.20 | USD -7,777.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 172 | 60.47% | USD -185.01 | USD -31,822.00 | USD -7,838.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 172 | 59.30% | USD -194.11 | USD -33,387.20 | USD -7,847.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 194 | 60.82% | USD -32.91 | USD -6,384.00 | USD -3,400.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 194 | 60.82% | USD -42.01 | USD -8,149.40 | USD -3,409.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 194 | 59.28% | USD -67.91 | USD -13,174.00 | USD -3,435.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 194 | 58.76% | USD -77.01 | USD -14,939.40 | USD -3,444.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 194 | 56.70% | USD -102.91 | USD -19,964.00 | USD -3,470.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 194 | 55.67% | USD -112.01 | USD -21,729.40 | USD -3,479.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 194 | 47.94% | USD -172.91 | USD -33,544.00 | USD -3,540.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 194 | 46.91% | USD -182.01 | USD -35,309.40 | USD -3,549.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 191/194 (3) | 29.32% (23.32–36.13%) | USD -23.05 | USD -4,402.60 | USD -449.60 |
| HOLD_5_SESSIONS | 1 : 6 | 191/194 (3) | 60.73% (53.66–67.38%) | USD -128.37 | USD -24,519.10 | USD -5,200.10 |
| HOLD_5_SESSIONS | 6 : 1 | 191/194 (3) | 31.94% (25.74–38.85%) | USD -32.98 | USD -6,299.10 | USD -2,459.10 |
| HOLD_5_SESSIONS | 5 : 5 | 191/194 (3) | 29.32% (23.32–36.13%) | USD -115.25 | USD -22,013.00 | USD -2,248.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 191/194 (3) | 29.32% (23.32–36.13%) | USD -23.05 | USD -4,402.60 | USD -449.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 191/194 (3) | 60.73% (53.66–67.38%) | USD -128.37 | USD -24,519.10 | USD -5,200.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 191/194 (3) | 31.94% (25.74–38.85%) | USD -32.98 | USD -6,299.10 | USD -2,459.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 191/194 (3) | 29.32% (23.32–36.13%) | USD -115.25 | USD -22,013.00 | USD -2,248.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 25.77% (20.13–32.36%) | USD -26.14 | USD -5,071.40 | USD -607.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 55.15% (48.12–61.99%) | USD -107.59 | USD -20,872.40 | USD -3,479.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 34.54% (28.20–41.47%) | USD -75.40 | USD -14,627.40 | USD -2,283.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 25.77% (20.13–32.36%) | USD -130.71 | USD -25,357.00 | USD -3,038.00 |
| HOLD_10_SESSIONS | 1 : 1 | 139/194 (55) | 31.65% (24.50–39.79%) | USD -4.64 | USD -644.40 | USD -1,296.60 |
| HOLD_10_SESSIONS | 1 : 6 | 139/194 (55) | 58.99% (50.68–66.82%) | USD -368.37 | USD -51,202.90 | USD -9,391.10 |
| HOLD_10_SESSIONS | 6 : 1 | 139/194 (55) | 37.41% (29.81–45.69%) | USD 335.91 | USD 46,692.10 | USD -2,881.10 |
| HOLD_10_SESSIONS | 5 : 5 | 139/194 (55) | 31.65% (24.50–39.79%) | USD -23.18 | USD -3,222.00 | USD -6,483.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 172/194 (22) | 30.81% (24.40–38.07%) | USD 8.02 | USD 1,378.80 | USD -406.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 172/194 (22) | 62.79% (55.36–69.66%) | USD -117.96 | USD -20,289.20 | USD -7,777.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 172/194 (22) | 33.14% (26.54–40.48%) | USD 174.07 | USD 29,940.80 | USD -2,862.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 172/194 (22) | 30.81% (24.40–38.07%) | USD 40.08 | USD 6,894.00 | USD -2,033.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 26.29% (20.60–32.90%) | USD -27.18 | USD -5,273.40 | USD -607.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 55.67% (48.64–62.48%) | USD -112.01 | USD -21,729.40 | USD -3,479.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 35.57% (29.17–42.52%) | USD -78.27 | USD -15,184.40 | USD -2,283.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 26.29% (20.60–32.90%) | USD -135.91 | USD -26,367.00 | USD -3,038.00 |
| HOLD_15_SESSIONS | 1 : 1 | 5/194 (189) | 40.00% (11.76–76.93%) | USD 25.40 | USD 127.00 | USD -200.60 |
| HOLD_15_SESSIONS | 1 : 6 | 5/194 (189) | 80.00% (37.55–96.38%) | USD 483.90 | USD 2,419.50 | USD -1,663.10 |
| HOLD_15_SESSIONS | 6 : 1 | 5/194 (189) | 40.00% (11.76–76.93%) | USD -306.10 | USD -1,530.50 | USD -2,322.10 |
| HOLD_15_SESSIONS | 5 : 5 | 5/194 (189) | 40.00% (11.76–76.93%) | USD 127.00 | USD 635.00 | USD -1,003.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 172/194 (22) | 31.40% (24.93–38.67%) | USD 8.43 | USD 1,450.80 | USD -406.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 172/194 (22) | 62.21% (54.77–69.11%) | USD -124.11 | USD -21,347.20 | USD -7,777.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 172/194 (22) | 32.56% (26.00–39.88%) | USD 183.16 | USD 31,502.80 | USD -2,862.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 172/194 (22) | 31.40% (24.93–38.67%) | USD 42.17 | USD 7,254.00 | USD -2,033.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 26.29% (20.60–32.90%) | USD -27.18 | USD -5,273.40 | USD -607.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 55.67% (48.64–62.48%) | USD -112.01 | USD -21,729.40 | USD -3,479.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 35.57% (29.17–42.52%) | USD -78.27 | USD -15,184.40 | USD -2,283.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 26.29% (20.60–32.90%) | USD -135.91 | USD -26,367.00 | USD -3,038.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/194 (194) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/194 (194) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 172/194 (22) | 31.40% (24.93–38.67%) | USD 8.43 | USD 1,450.80 | USD -406.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 172/194 (22) | 62.21% (54.77–69.11%) | USD -124.11 | USD -21,347.20 | USD -7,777.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 172/194 (22) | 32.56% (26.00–39.88%) | USD 183.16 | USD 31,502.80 | USD -2,862.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 172/194 (22) | 31.40% (24.93–38.67%) | USD 42.17 | USD 7,254.00 | USD -2,033.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 194/194 (0) | 26.29% (20.60–32.90%) | USD -27.18 | USD -5,273.40 | USD -607.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 194/194 (0) | 55.67% (48.64–62.48%) | USD -112.01 | USD -21,729.40 | USD -3,479.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 194/194 (0) | 35.57% (29.17–42.52%) | USD -78.27 | USD -15,184.40 | USD -2,283.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 194/194 (0) | 26.29% (20.60–32.90%) | USD -135.91 | USD -26,367.00 | USD -3,038.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -75% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -50% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -40% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -30% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -25% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -20% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -15% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -10% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| -5% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| 0% | 194/194 | 100.00% | USD 740.05 | USD 60.45 |
| 5% | 23/194 | 11.86% | USD -4,504.30 | USD -10,834.35 |
| 10% | 0/194 | 0.00% | USD -15,160.90 | USD -26,060.35 |
| 20% | 0/194 | 0.00% | USD -36,734.75 | USD -60,181.15 |

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