# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 253.20 / USD 1,344.78; mean absolute mismatch USD 1,091.58; mean match score 19.02%.
- Actual selected contract ratios: {'1:6': 176}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 177; entered cohorts: 176; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 176/176 | 88/88/0 | 50.00% (42.69–57.31%) | USD -155.32 | USD 1.40 | USD -27,336.60 | USD -3,979.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 176/176 | 88/88/0 | 50.00% (42.69–57.31%) | USD -155.32 | USD 1.40 | USD -27,336.60 | USD -3,979.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 176/176 | 88/88/0 | 50.00% (42.69–57.31%) | USD -155.32 | USD 1.40 | USD -27,336.60 | USD -3,979.10 | 0 |
| HOLD_10_SESSIONS | 174/176 | 94/80/0 | 54.02% (46.61–61.26%) | USD -240.65 | USD 80.40 | USD -41,873.40 | USD -8,503.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 174/176 | 94/80/0 | 54.02% (46.61–61.26%) | USD -240.65 | USD 80.40 | USD -41,873.40 | USD -8,503.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 174/176 | 94/80/0 | 54.02% (46.61–61.26%) | USD -240.65 | USD 80.40 | USD -41,873.40 | USD -8,503.10 | 2 |
| HOLD_15_SESSIONS | 174/176 | 96/78/0 | 55.17% (47.75–62.37%) | USD -305.63 | USD 95.40 | USD -53,179.40 | USD -9,078.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 174/176 | 96/78/0 | 55.17% (47.75–62.37%) | USD -305.63 | USD 95.40 | USD -53,179.40 | USD -9,078.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 174/176 | 96/78/0 | 55.17% (47.75–62.37%) | USD -305.63 | USD 95.40 | USD -53,179.40 | USD -9,078.10 | 2 |
| HOLD_20_SESSIONS | 166/176 | 94/72/0 | 56.63% (49.02–63.93%) | USD -381.73 | USD 308.40 | USD -63,366.60 | USD -8,386.10 | 10 |
| HOLD_20_OR_DTE_LE_7 | 166/176 | 94/72/0 | 56.63% (49.02–63.93%) | USD -381.73 | USD 308.40 | USD -63,366.60 | USD -8,386.10 | 10 |
| HOLD_20_OR_DTE_LE_14 | 169/176 | 99/70/0 | 58.58% (51.04–65.74%) | USD -322.61 | USD 269.90 | USD -54,520.90 | USD -10,217.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 12.11 | USD -88.33 |
| HOLD_5_OR_DTE_LE_7 | USD 12.11 | USD -88.33 |
| HOLD_5_OR_DTE_LE_14 | USD 12.11 | USD -88.33 |
| HOLD_10_SESSIONS | USD 43.66 | USD -205.21 |
| HOLD_10_OR_DTE_LE_7 | USD 43.66 | USD -205.21 |
| HOLD_10_OR_DTE_LE_14 | USD 43.66 | USD -205.21 |
| HOLD_15_SESSIONS | USD 48.40 | USD -274.93 |
| HOLD_15_OR_DTE_LE_7 | USD 48.40 | USD -274.93 |
| HOLD_15_OR_DTE_LE_14 | USD 48.40 | USD -274.93 |
| HOLD_20_SESSIONS | USD 97.06 | USD -399.69 |
| HOLD_20_OR_DTE_LE_7 | USD 97.06 | USD -399.69 |
| HOLD_20_OR_DTE_LE_14 | USD 72.50 | USD -316.01 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 176 | 57.39% | USD -76.22 | USD -13,415.00 | USD -3,900.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 176 | 56.82% | USD -85.32 | USD -15,016.60 | USD -3,909.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 176 | 53.98% | USD -111.22 | USD -19,575.00 | USD -3,935.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 176 | 53.98% | USD -120.32 | USD -21,176.60 | USD -3,944.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 176 | 51.70% | USD -146.22 | USD -25,735.00 | USD -3,970.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 176 | 50.00% | USD -155.32 | USD -27,336.60 | USD -3,979.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 176 | 47.16% | USD -216.22 | USD -38,055.00 | USD -4,040.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 176 | 46.59% | USD -225.32 | USD -39,656.60 | USD -4,049.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 176 | 57.39% | USD -76.22 | USD -13,415.00 | USD -3,900.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 176 | 56.82% | USD -85.32 | USD -15,016.60 | USD -3,909.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 176 | 53.98% | USD -111.22 | USD -19,575.00 | USD -3,935.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 176 | 53.98% | USD -120.32 | USD -21,176.60 | USD -3,944.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 176 | 51.70% | USD -146.22 | USD -25,735.00 | USD -3,970.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 176 | 50.00% | USD -155.32 | USD -27,336.60 | USD -3,979.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 176 | 47.16% | USD -216.22 | USD -38,055.00 | USD -4,040.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 176 | 46.59% | USD -225.32 | USD -39,656.60 | USD -4,049.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 176 | 57.39% | USD -76.22 | USD -13,415.00 | USD -3,900.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 176 | 56.82% | USD -85.32 | USD -15,016.60 | USD -3,909.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 176 | 53.98% | USD -111.22 | USD -19,575.00 | USD -3,935.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 176 | 53.98% | USD -120.32 | USD -21,176.60 | USD -3,944.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 176 | 51.70% | USD -146.22 | USD -25,735.00 | USD -3,970.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 176 | 50.00% | USD -155.32 | USD -27,336.60 | USD -3,979.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 176 | 47.16% | USD -216.22 | USD -38,055.00 | USD -4,040.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 176 | 46.59% | USD -225.32 | USD -39,656.60 | USD -4,049.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 174 | 56.32% | USD -161.55 | USD -28,110.00 | USD -8,424.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 174 | 56.32% | USD -170.65 | USD -29,693.40 | USD -8,433.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 174 | 55.17% | USD -196.55 | USD -34,200.00 | USD -8,459.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 174 | 55.17% | USD -205.65 | USD -35,783.40 | USD -8,468.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 174 | 54.60% | USD -231.55 | USD -40,290.00 | USD -8,494.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 174 | 54.02% | USD -240.65 | USD -41,873.40 | USD -8,503.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 174 | 50.57% | USD -301.55 | USD -52,470.00 | USD -8,564.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 174 | 50.57% | USD -310.65 | USD -54,053.40 | USD -8,573.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 174 | 56.32% | USD -161.55 | USD -28,110.00 | USD -8,424.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 174 | 56.32% | USD -170.65 | USD -29,693.40 | USD -8,433.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 174 | 55.17% | USD -196.55 | USD -34,200.00 | USD -8,459.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 174 | 55.17% | USD -205.65 | USD -35,783.40 | USD -8,468.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 174 | 54.60% | USD -231.55 | USD -40,290.00 | USD -8,494.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 174 | 54.02% | USD -240.65 | USD -41,873.40 | USD -8,503.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 174 | 50.57% | USD -301.55 | USD -52,470.00 | USD -8,564.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 174 | 50.57% | USD -310.65 | USD -54,053.40 | USD -8,573.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 174 | 56.32% | USD -161.55 | USD -28,110.00 | USD -8,424.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 174 | 56.32% | USD -170.65 | USD -29,693.40 | USD -8,433.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 174 | 55.17% | USD -196.55 | USD -34,200.00 | USD -8,459.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 174 | 55.17% | USD -205.65 | USD -35,783.40 | USD -8,468.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 174 | 54.60% | USD -231.55 | USD -40,290.00 | USD -8,494.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 174 | 54.02% | USD -240.65 | USD -41,873.40 | USD -8,503.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 174 | 50.57% | USD -301.55 | USD -52,470.00 | USD -8,564.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 174 | 50.57% | USD -310.65 | USD -54,053.40 | USD -8,573.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 174 | 59.20% | USD -226.53 | USD -39,416.00 | USD -8,999.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 174 | 57.47% | USD -235.63 | USD -40,999.40 | USD -9,008.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 174 | 56.32% | USD -261.53 | USD -45,506.00 | USD -9,034.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 174 | 56.32% | USD -270.63 | USD -47,089.40 | USD -9,043.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 174 | 55.17% | USD -296.53 | USD -51,596.00 | USD -9,069.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 174 | 55.17% | USD -305.63 | USD -53,179.40 | USD -9,078.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 174 | 50.57% | USD -366.53 | USD -63,776.00 | USD -9,139.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 174 | 50.57% | USD -375.63 | USD -65,359.40 | USD -9,148.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 174 | 59.20% | USD -226.53 | USD -39,416.00 | USD -8,999.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 174 | 57.47% | USD -235.63 | USD -40,999.40 | USD -9,008.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 174 | 56.32% | USD -261.53 | USD -45,506.00 | USD -9,034.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 174 | 56.32% | USD -270.63 | USD -47,089.40 | USD -9,043.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 174 | 55.17% | USD -296.53 | USD -51,596.00 | USD -9,069.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 174 | 55.17% | USD -305.63 | USD -53,179.40 | USD -9,078.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 174 | 50.57% | USD -366.53 | USD -63,776.00 | USD -9,139.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 174 | 50.57% | USD -375.63 | USD -65,359.40 | USD -9,148.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 174 | 59.20% | USD -226.53 | USD -39,416.00 | USD -8,999.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 174 | 57.47% | USD -235.63 | USD -40,999.40 | USD -9,008.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 174 | 56.32% | USD -261.53 | USD -45,506.00 | USD -9,034.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 174 | 56.32% | USD -270.63 | USD -47,089.40 | USD -9,043.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 174 | 55.17% | USD -296.53 | USD -51,596.00 | USD -9,069.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 174 | 55.17% | USD -305.63 | USD -53,179.40 | USD -9,078.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 174 | 50.57% | USD -366.53 | USD -63,776.00 | USD -9,139.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 174 | 50.57% | USD -375.63 | USD -65,359.40 | USD -9,148.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 166 | 57.23% | USD -302.63 | USD -50,236.00 | USD -8,307.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 166 | 57.23% | USD -311.73 | USD -51,746.60 | USD -8,316.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 166 | 57.23% | USD -337.63 | USD -56,046.00 | USD -8,342.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 166 | 57.23% | USD -346.73 | USD -57,556.60 | USD -8,351.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 166 | 56.63% | USD -372.63 | USD -61,856.00 | USD -8,377.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 166 | 56.63% | USD -381.73 | USD -63,366.60 | USD -8,386.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 166 | 55.42% | USD -442.63 | USD -73,476.00 | USD -8,447.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 166 | 54.82% | USD -451.73 | USD -74,986.60 | USD -8,456.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 166 | 57.23% | USD -302.63 | USD -50,236.00 | USD -8,307.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 166 | 57.23% | USD -311.73 | USD -51,746.60 | USD -8,316.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 166 | 57.23% | USD -337.63 | USD -56,046.00 | USD -8,342.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 166 | 57.23% | USD -346.73 | USD -57,556.60 | USD -8,351.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 166 | 56.63% | USD -372.63 | USD -61,856.00 | USD -8,377.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 166 | 56.63% | USD -381.73 | USD -63,366.60 | USD -8,386.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 166 | 55.42% | USD -442.63 | USD -73,476.00 | USD -8,447.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 166 | 54.82% | USD -451.73 | USD -74,986.60 | USD -8,456.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 169 | 59.17% | USD -243.51 | USD -41,153.00 | USD -10,138.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 169 | 59.17% | USD -252.61 | USD -42,690.90 | USD -10,147.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 169 | 59.17% | USD -278.51 | USD -47,068.00 | USD -10,173.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 169 | 59.17% | USD -287.61 | USD -48,605.90 | USD -10,182.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 169 | 58.58% | USD -313.51 | USD -52,983.00 | USD -10,208.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 169 | 58.58% | USD -322.61 | USD -54,520.90 | USD -10,217.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 169 | 56.21% | USD -383.51 | USD -64,813.00 | USD -10,278.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 169 | 55.62% | USD -392.61 | USD -66,350.90 | USD -10,287.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 176/176 (0) | 31.82% (25.39–39.02%) | USD -25.21 | USD -4,437.60 | USD -393.60 |
| HOLD_5_SESSIONS | 1 : 6 | 176/176 (0) | 50.00% (42.69–57.31%) | USD -155.32 | USD -27,336.60 | USD -3,979.10 |
| HOLD_5_SESSIONS | 6 : 1 | 176/176 (0) | 38.64% (31.76–46.00%) | USD -21.17 | USD -3,726.60 | USD -2,410.10 |
| HOLD_5_SESSIONS | 5 : 5 | 176/176 (0) | 31.82% (25.39–39.02%) | USD -126.07 | USD -22,188.00 | USD -1,968.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 176/176 (0) | 31.82% (25.39–39.02%) | USD -25.21 | USD -4,437.60 | USD -393.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 176/176 (0) | 50.00% (42.69–57.31%) | USD -155.32 | USD -27,336.60 | USD -3,979.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 176/176 (0) | 38.64% (31.76–46.00%) | USD -21.17 | USD -3,726.60 | USD -2,410.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 176/176 (0) | 31.82% (25.39–39.02%) | USD -126.07 | USD -22,188.00 | USD -1,968.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 176/176 (0) | 31.82% (25.39–39.02%) | USD -25.21 | USD -4,437.60 | USD -393.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 176/176 (0) | 50.00% (42.69–57.31%) | USD -155.32 | USD -27,336.60 | USD -3,979.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 176/176 (0) | 38.64% (31.76–46.00%) | USD -21.17 | USD -3,726.60 | USD -2,410.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 176/176 (0) | 31.82% (25.39–39.02%) | USD -126.07 | USD -22,188.00 | USD -1,968.00 |
| HOLD_10_SESSIONS | 1 : 1 | 174/176 (2) | 31.61% (25.16–38.85%) | USD -13.15 | USD -2,287.40 | USD -1,021.60 |
| HOLD_10_SESSIONS | 1 : 6 | 174/176 (2) | 54.02% (46.61–61.26%) | USD -240.65 | USD -41,873.40 | USD -8,503.10 |
| HOLD_10_SESSIONS | 6 : 1 | 174/176 (2) | 41.95% (34.87–49.38%) | USD 148.63 | USD 25,861.60 | USD -4,110.10 |
| HOLD_10_SESSIONS | 5 : 5 | 174/176 (2) | 31.61% (25.16–38.85%) | USD -65.73 | USD -11,437.00 | USD -5,108.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 174/176 (2) | 31.61% (25.16–38.85%) | USD -13.15 | USD -2,287.40 | USD -1,021.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 174/176 (2) | 54.02% (46.61–61.26%) | USD -240.65 | USD -41,873.40 | USD -8,503.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 174/176 (2) | 41.95% (34.87–49.38%) | USD 148.63 | USD 25,861.60 | USD -4,110.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 174/176 (2) | 31.61% (25.16–38.85%) | USD -65.73 | USD -11,437.00 | USD -5,108.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 174/176 (2) | 31.61% (25.16–38.85%) | USD -13.15 | USD -2,287.40 | USD -1,021.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 174/176 (2) | 54.02% (46.61–61.26%) | USD -240.65 | USD -41,873.40 | USD -8,503.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 174/176 (2) | 41.95% (34.87–49.38%) | USD 148.63 | USD 25,861.60 | USD -4,110.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 174/176 (2) | 31.61% (25.16–38.85%) | USD -65.73 | USD -11,437.00 | USD -5,108.00 |
| HOLD_15_SESSIONS | 1 : 1 | 174/176 (2) | 32.18% (25.69–39.45%) | USD -20.02 | USD -3,483.40 | USD -664.60 |
| HOLD_15_SESSIONS | 1 : 6 | 174/176 (2) | 55.17% (47.75–62.37%) | USD -305.63 | USD -53,179.40 | USD -9,078.10 |
| HOLD_15_SESSIONS | 6 : 1 | 174/176 (2) | 35.63% (28.90–42.99%) | USD 165.49 | USD 28,795.60 | USD -4,690.10 |
| HOLD_15_SESSIONS | 5 : 5 | 174/176 (2) | 32.18% (25.69–39.45%) | USD -100.10 | USD -17,417.00 | USD -3,323.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 174/176 (2) | 32.18% (25.69–39.45%) | USD -20.02 | USD -3,483.40 | USD -664.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 174/176 (2) | 55.17% (47.75–62.37%) | USD -305.63 | USD -53,179.40 | USD -9,078.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 174/176 (2) | 35.63% (28.90–42.99%) | USD 165.49 | USD 28,795.60 | USD -4,690.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 174/176 (2) | 32.18% (25.69–39.45%) | USD -100.10 | USD -17,417.00 | USD -3,323.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 174/176 (2) | 32.18% (25.69–39.45%) | USD -20.02 | USD -3,483.40 | USD -664.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 174/176 (2) | 55.17% (47.75–62.37%) | USD -305.63 | USD -53,179.40 | USD -9,078.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 174/176 (2) | 35.63% (28.90–42.99%) | USD 165.49 | USD 28,795.60 | USD -4,690.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 174/176 (2) | 32.18% (25.69–39.45%) | USD -100.10 | USD -17,417.00 | USD -3,323.00 |
| HOLD_20_SESSIONS | 1 : 1 | 166/176 (10) | 32.53% (25.87–39.98%) | USD 7.85 | USD 1,302.40 | USD -836.60 |
| HOLD_20_SESSIONS | 1 : 6 | 166/176 (10) | 56.63% (49.02–63.93%) | USD -381.73 | USD -63,366.60 | USD -8,386.10 |
| HOLD_20_SESSIONS | 6 : 1 | 166/176 (10) | 39.16% (32.06–46.75%) | USD 436.65 | USD 72,483.40 | USD -4,713.10 |
| HOLD_20_SESSIONS | 5 : 5 | 166/176 (10) | 32.53% (25.87–39.98%) | USD 39.23 | USD 6,512.00 | USD -4,183.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 166/176 (10) | 32.53% (25.87–39.98%) | USD 7.85 | USD 1,302.40 | USD -836.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 166/176 (10) | 56.63% (49.02–63.93%) | USD -381.73 | USD -63,366.60 | USD -8,386.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 166/176 (10) | 39.16% (32.06–46.75%) | USD 436.65 | USD 72,483.40 | USD -4,713.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 166/176 (10) | 32.53% (25.87–39.98%) | USD 39.23 | USD 6,512.00 | USD -4,183.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 169/176 (7) | 30.77% (24.30–38.09%) | USD -2.77 | USD -467.40 | USD -836.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 169/176 (7) | 58.58% (51.04–65.74%) | USD -322.61 | USD -54,520.90 | USD -10,217.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 169/176 (7) | 35.50% (28.68–42.97%) | USD 303.25 | USD 51,249.10 | USD -4,764.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 169/176 (7) | 30.77% (24.30–38.09%) | USD -13.83 | USD -2,337.00 | USD -4,183.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -75% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -50% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -40% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -30% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -25% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -20% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -15% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -10% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| -5% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| 0% | 176/176 | 100.00% | USD 1,052.03 | USD 204.45 |
| 5% | 58/176 | 32.95% | USD -1,627.37 | USD -7,415.95 |
| 10% | 2/176 | 1.14% | USD -11,926.32 | USD -24,476.35 |
| 20% | 0/176 | 0.00% | USD -33,630.57 | USD -58,597.15 |

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