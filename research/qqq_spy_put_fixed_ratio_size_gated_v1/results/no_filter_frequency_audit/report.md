# QQQ/SPY Entry-Frequency Comparison: Filtered vs Unfiltered

- Compare the 20-session relative-underperformance gate with no relative-performance gate.
- Same fixed quantities, cohort cadence, DTE/Delta rules, quote-side directions, displayed-size gates and base costs.
- Last signal included: 2025-07-23, allowing more complete observation of longer exits.
- P&L is not compounded; unresolved cohorts are separately reported.

## Trade frequency per year (unique cohorts, not individual contracts)

| Window | Entry filter | Ratio | Selected cohorts | Entered | Skipped | Entered/year |
|---|---|---:|---:|---:|---:|---:|
| 1Y | qqq_underperforms_spy_20d | 1:6 | 5 | 5 | 0 | 5.00 |
| 1Y | qqq_underperforms_spy_20d | 4:5 | 5 | 5 | 0 | 5.00 |
| 1Y | qqq_underperforms_spy_20d | 2:4 | 5 | 5 | 0 | 5.00 |
| 1Y | qqq_underperforms_spy_20d | 1:3 | 5 | 5 | 0 | 5.00 |
| 1Y | none | 1:6 | 6 | 6 | 0 | 6.00 |
| 1Y | none | 4:5 | 6 | 6 | 0 | 6.00 |
| 1Y | none | 2:4 | 6 | 6 | 0 | 6.00 |
| 1Y | none | 1:3 | 6 | 6 | 0 | 6.00 |
| 3Y | qqq_underperforms_spy_20d | 1:6 | 15 | 15 | 0 | 5.00 |
| 3Y | qqq_underperforms_spy_20d | 4:5 | 15 | 15 | 0 | 5.00 |
| 3Y | qqq_underperforms_spy_20d | 2:4 | 15 | 15 | 0 | 5.00 |
| 3Y | qqq_underperforms_spy_20d | 1:3 | 15 | 15 | 0 | 5.00 |
| 3Y | none | 1:6 | 17 | 17 | 0 | 5.67 |
| 3Y | none | 4:5 | 17 | 17 | 0 | 5.67 |
| 3Y | none | 2:4 | 17 | 17 | 0 | 5.67 |
| 3Y | none | 1:3 | 17 | 17 | 0 | 5.67 |
| 5Y | qqq_underperforms_spy_20d | 1:6 | 26 | 26 | 0 | 5.20 |
| 5Y | qqq_underperforms_spy_20d | 4:5 | 26 | 26 | 0 | 5.20 |
| 5Y | qqq_underperforms_spy_20d | 2:4 | 26 | 26 | 0 | 5.20 |
| 5Y | qqq_underperforms_spy_20d | 1:3 | 26 | 26 | 0 | 5.20 |
| 5Y | none | 1:6 | 28 | 28 | 0 | 5.60 |
| 5Y | none | 4:5 | 28 | 28 | 0 | 5.60 |
| 5Y | none | 2:4 | 28 | 28 | 0 | 5.60 |
| 5Y | none | 1:3 | 28 | 28 | 0 | 5.60 |

## Mean and total net P&L per horizon (base costs)

| Window | Filter | Ratio | Exit | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Annualized resolved net | Worst trade | Unresolved |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1Y | qqq_underperforms_spy_20d | 1:6 | 5d | 5/5 | 80.00% | USD 1,213.30 | USD 6,066.50 | USD 6,066.50 | USD -2,198.10 | 0 |
| 1Y | qqq_underperforms_spy_20d | 1:6 | 10d | 5/5 | 100.00% | USD 2,388.30 | USD 11,941.50 | USD 11,941.50 | USD 258.90 | 0 |
| 1Y | qqq_underperforms_spy_20d | 1:6 | 20d | 5/5 | 80.00% | USD 2,230.50 | USD 11,152.50 | USD 11,152.50 | USD -1,370.10 | 0 |
| 1Y | qqq_underperforms_spy_20d | 1:6 | DTE<=7 | 4/5 | 75.00% | USD -1,126.10 | USD -4,504.40 | USD -4,504.40 | USD -8,997.10 | 1 |
| 1Y | qqq_underperforms_spy_20d | 4:5 | 5d | 5/5 | 40.00% | USD 6.90 | USD 34.50 | USD 34.50 | USD -787.70 | 0 |
| 1Y | qqq_underperforms_spy_20d | 4:5 | 10d | 5/5 | 40.00% | USD 161.50 | USD 807.50 | USD 807.50 | USD -364.70 | 0 |
| 1Y | qqq_underperforms_spy_20d | 4:5 | 20d | 5/5 | 40.00% | USD 183.90 | USD 919.50 | USD 919.50 | USD -686.70 | 0 |
| 1Y | qqq_underperforms_spy_20d | 4:5 | DTE<=7 | 4/5 | 25.00% | USD -503.95 | USD -2,015.80 | USD -2,015.80 | USD -1,630.70 | 1 |
| 1Y | qqq_underperforms_spy_20d | 2:4 | 5d | 5/5 | 60.00% | USD 400.20 | USD 2,001.00 | USD 2,001.00 | USD -1,025.80 | 0 |
| 1Y | qqq_underperforms_spy_20d | 2:4 | 10d | 5/5 | 80.00% | USD 822.20 | USD 4,111.00 | USD 4,111.00 | USD -71.80 | 0 |
| 1Y | qqq_underperforms_spy_20d | 2:4 | 20d | 5/5 | 80.00% | USD 781.80 | USD 3,909.00 | USD 3,909.00 | USD -721.80 | 0 |
| 1Y | qqq_underperforms_spy_20d | 2:4 | DTE<=7 | 4/5 | 75.00% | USD -567.80 | USD -2,271.20 | USD -2,271.20 | USD -3,527.80 | 1 |
| 1Y | qqq_underperforms_spy_20d | 1:3 | 5d | 5/5 | 60.00% | USD 445.60 | USD 2,228.00 | USD 2,228.00 | USD -934.20 | 0 |
| 1Y | qqq_underperforms_spy_20d | 1:3 | 10d | 5/5 | 100.00% | USD 905.40 | USD 4,527.00 | USD 4,527.00 | USD 37.80 | 0 |
| 1Y | qqq_underperforms_spy_20d | 1:3 | 20d | 5/5 | 80.00% | USD 850.80 | USD 4,254.00 | USD 4,254.00 | USD -613.20 | 0 |
| 1Y | qqq_underperforms_spy_20d | 1:3 | DTE<=7 | 4/5 | 75.00% | USD -494.45 | USD -1,977.80 | USD -1,977.80 | USD -3,572.20 | 1 |
| 1Y | none | 1:6 | 5d | 6/6 | 83.33% | USD 493.40 | USD 2,960.40 | USD 2,960.40 | USD -2,019.10 | 0 |
| 1Y | none | 1:6 | 10d | 6/6 | 50.00% | USD -729.43 | USD -4,376.60 | USD -4,376.60 | USD -10,453.10 | 0 |
| 1Y | none | 1:6 | 20d | 6/6 | 83.33% | USD 1,633.40 | USD 9,800.40 | USD 9,800.40 | USD -2,108.10 | 0 |
| 1Y | none | 1:6 | DTE<=7 | 6/6 | 83.33% | USD 1,185.40 | USD 7,112.40 | USD 7,112.40 | USD -5,709.10 | 0 |
| 1Y | none | 4:5 | 5d | 6/6 | 50.00% | USD 1.47 | USD 8.80 | USD 8.80 | USD -332.70 | 0 |
| 1Y | none | 4:5 | 10d | 6/6 | 66.67% | USD -312.53 | USD -1,875.20 | USD -1,875.20 | USD -2,193.70 | 0 |
| 1Y | none | 4:5 | 20d | 6/6 | 100.00% | USD 326.13 | USD 1,956.80 | USD 1,956.80 | USD 36.30 | 0 |
| 1Y | none | 4:5 | DTE<=7 | 6/6 | 100.00% | USD 680.97 | USD 4,085.80 | USD 4,085.80 | USD 20.30 | 0 |
| 1Y | none | 2:4 | 5d | 6/6 | 83.33% | USD 70.20 | USD 421.20 | USD 421.20 | USD -1,213.80 | 0 |
| 1Y | none | 2:4 | 10d | 6/6 | 50.00% | USD -364.47 | USD -2,186.80 | USD -2,186.80 | USD -4,239.80 | 0 |
| 1Y | none | 2:4 | 20d | 6/6 | 83.33% | USD 639.87 | USD 3,839.20 | USD 3,839.20 | USD -653.80 | 0 |
| 1Y | none | 2:4 | DTE<=7 | 6/6 | 83.33% | USD 658.53 | USD 3,951.20 | USD 3,951.20 | USD -1,399.80 | 0 |
| 1Y | none | 1:3 | 5d | 6/6 | 83.33% | USD 172.80 | USD 1,036.80 | USD 1,036.80 | USD -821.20 | 0 |
| 1Y | none | 1:3 | 10d | 6/6 | 50.00% | USD -319.03 | USD -1,914.20 | USD -1,914.20 | USD -4,203.20 | 0 |
| 1Y | none | 1:3 | 20d | 6/6 | 83.33% | USD 648.30 | USD 3,889.80 | USD 3,889.80 | USD -772.20 | 0 |
| 1Y | none | 1:3 | DTE<=7 | 6/6 | 83.33% | USD 543.30 | USD 3,259.80 | USD 3,259.80 | USD -1,952.20 | 0 |
| 3Y | qqq_underperforms_spy_20d | 1:6 | 5d | 15/15 | 60.00% | USD 310.57 | USD 4,658.50 | USD 1,552.83 | USD -4,827.10 | 0 |
| 3Y | qqq_underperforms_spy_20d | 1:6 | 10d | 15/15 | 80.00% | USD 1,006.43 | USD 15,096.50 | USD 5,032.17 | USD -3,817.10 | 0 |
| 3Y | qqq_underperforms_spy_20d | 1:6 | 20d | 14/15 | 85.71% | USD 1,474.40 | USD 20,641.60 | USD 6,880.53 | USD -1,370.10 | 1 |
| 3Y | qqq_underperforms_spy_20d | 1:6 | DTE<=7 | 13/15 | 76.92% | USD 212.98 | USD 2,768.70 | USD 922.90 | USD -8,997.10 | 2 |
| 3Y | qqq_underperforms_spy_20d | 4:5 | 5d | 15/15 | 46.67% | USD -65.37 | USD -980.50 | USD -326.83 | USD -787.70 | 0 |
| 3Y | qqq_underperforms_spy_20d | 4:5 | 10d | 15/15 | 40.00% | USD 64.23 | USD 963.50 | USD 321.17 | USD -491.70 | 0 |
| 3Y | qqq_underperforms_spy_20d | 4:5 | 20d | 14/15 | 50.00% | USD 36.66 | USD 513.20 | USD 171.07 | USD -774.70 | 1 |
| 3Y | qqq_underperforms_spy_20d | 4:5 | DTE<=7 | 13/15 | 46.15% | USD -164.01 | USD -2,132.10 | USD -710.70 | USD -1,630.70 | 2 |
| 3Y | qqq_underperforms_spy_20d | 2:4 | 5d | 15/15 | 53.33% | USD 75.27 | USD 1,129.00 | USD 376.33 | USD -1,363.80 | 0 |
| 3Y | qqq_underperforms_spy_20d | 2:4 | 10d | 15/15 | 73.33% | USD 344.87 | USD 5,173.00 | USD 1,724.33 | USD -775.80 | 0 |
| 3Y | qqq_underperforms_spy_20d | 2:4 | 20d | 14/15 | 85.71% | USD 505.91 | USD 7,082.80 | USD 2,360.93 | USD -721.80 | 1 |
| 3Y | qqq_underperforms_spy_20d | 2:4 | DTE<=7 | 13/15 | 76.92% | USD -1.80 | USD -23.40 | USD -7.80 | USD -3,527.80 | 2 |
| 3Y | qqq_underperforms_spy_20d | 1:3 | 5d | 15/15 | 53.33% | USD 103.27 | USD 1,549.00 | USD 516.33 | USD -1,718.20 | 0 |
| 3Y | qqq_underperforms_spy_20d | 1:3 | 10d | 15/15 | 80.00% | USD 380.93 | USD 5,714.00 | USD 1,904.67 | USD -1,245.20 | 0 |
| 3Y | qqq_underperforms_spy_20d | 1:3 | 20d | 14/15 | 85.71% | USD 553.87 | USD 7,754.20 | USD 2,584.73 | USD -613.20 | 1 |
| 3Y | qqq_underperforms_spy_20d | 1:3 | DTE<=7 | 13/15 | 76.92% | USD 52.57 | USD 683.40 | USD 227.80 | USD -3,572.20 | 2 |
| 3Y | none | 1:6 | 5d | 17/17 | 70.59% | USD -160.75 | USD -2,732.70 | USD -910.90 | USD -4,163.10 | 0 |
| 3Y | none | 1:6 | 10d | 17/17 | 58.82% | USD -880.39 | USD -14,966.70 | USD -4,988.90 | USD -10,453.10 | 0 |
| 3Y | none | 1:6 | 20d | 17/17 | 76.47% | USD 607.19 | USD 10,322.30 | USD 3,440.77 | USD -9,376.10 | 0 |
| 3Y | none | 1:6 | DTE<=7 | 16/17 | 81.25% | USD -340.16 | USD -5,442.60 | USD -1,814.20 | USD -20,318.10 | 1 |
| 3Y | none | 4:5 | 5d | 17/17 | 35.29% | USD -266.82 | USD -4,535.90 | USD -1,511.97 | USD -2,180.70 | 0 |
| 3Y | none | 4:5 | 10d | 17/17 | 47.06% | USD -554.35 | USD -9,423.90 | USD -3,141.30 | USD -2,929.70 | 0 |
| 3Y | none | 4:5 | 20d | 17/17 | 76.47% | USD -86.11 | USD -1,463.90 | USD -487.97 | USD -3,203.70 | 0 |
| 3Y | none | 4:5 | DTE<=7 | 16/17 | 81.25% | USD -389.01 | USD -6,224.20 | USD -2,074.73 | USD -7,641.70 | 1 |
| 3Y | none | 2:4 | 5d | 17/17 | 70.59% | USD -196.98 | USD -3,348.60 | USD -1,116.20 | USD -1,867.80 | 0 |
| 3Y | none | 2:4 | 10d | 17/17 | 52.94% | USD -512.51 | USD -8,712.60 | USD -2,904.20 | USD -4,239.80 | 0 |
| 3Y | none | 2:4 | 20d | 17/17 | 76.47% | USD 150.08 | USD 2,551.40 | USD 850.47 | USD -4,309.80 | 0 |
| 3Y | none | 2:4 | DTE<=7 | 16/17 | 81.25% | USD -273.05 | USD -4,368.80 | USD -1,456.27 | USD -9,633.80 | 1 |
| 3Y | none | 1:3 | 5d | 17/17 | 70.59% | USD -103.91 | USD -1,766.40 | USD -588.80 | USD -1,741.20 | 0 |
| 3Y | none | 1:3 | 10d | 17/17 | 52.94% | USD -412.91 | USD -7,019.40 | USD -2,339.80 | USD -4,203.20 | 0 |
| 3Y | none | 1:3 | 20d | 17/17 | 76.47% | USD 208.21 | USD 3,539.60 | USD 1,179.87 | USD -3,960.20 | 0 |
| 3Y | none | 1:3 | DTE<=7 | 16/17 | 81.25% | USD -187.20 | USD -2,995.20 | USD -998.40 | USD -8,692.20 | 1 |
| 5Y | qqq_underperforms_spy_20d | 1:6 | 5d | 26/26 | 65.38% | USD 379.67 | USD 9,871.40 | USD 1,974.28 | USD -4,827.10 | 0 |
| 5Y | qqq_underperforms_spy_20d | 1:6 | 10d | 26/26 | 76.92% | USD 714.05 | USD 18,565.40 | USD 3,713.08 | USD -3,830.10 | 0 |
| 5Y | qqq_underperforms_spy_20d | 1:6 | 20d | 25/26 | 88.00% | USD 1,658.22 | USD 41,455.50 | USD 8,291.10 | USD -2,138.10 | 1 |
| 5Y | qqq_underperforms_spy_20d | 1:6 | DTE<=7 | 23/26 | 82.61% | USD 989.29 | USD 22,753.70 | USD 4,550.74 | USD -8,997.10 | 3 |
| 5Y | qqq_underperforms_spy_20d | 4:5 | 5d | 26/26 | 50.00% | USD -44.47 | USD -1,156.20 | USD -231.24 | USD -787.70 | 0 |
| 5Y | qqq_underperforms_spy_20d | 4:5 | 10d | 26/26 | 53.85% | USD 88.65 | USD 2,304.80 | USD 460.96 | USD -1,007.70 | 0 |
| 5Y | qqq_underperforms_spy_20d | 4:5 | 20d | 25/26 | 68.00% | USD 273.66 | USD 6,841.50 | USD 1,368.30 | USD -774.70 | 1 |
| 5Y | qqq_underperforms_spy_20d | 4:5 | DTE<=7 | 23/26 | 69.57% | USD 168.13 | USD 3,866.90 | USD 773.38 | USD -1,630.70 | 3 |
| 5Y | qqq_underperforms_spy_20d | 2:4 | 5d | 26/26 | 61.54% | USD 103.89 | USD 2,701.20 | USD 540.24 | USD -1,363.80 | 0 |
| 5Y | qqq_underperforms_spy_20d | 2:4 | 10d | 26/26 | 73.08% | USD 262.82 | USD 6,833.20 | USD 1,366.64 | USD -1,633.80 | 0 |
| 5Y | qqq_underperforms_spy_20d | 2:4 | 20d | 25/26 | 88.00% | USD 649.64 | USD 16,241.00 | USD 3,248.20 | USD -721.80 | 1 |
| 5Y | qqq_underperforms_spy_20d | 2:4 | DTE<=7 | 23/26 | 86.96% | USD 386.29 | USD 8,884.60 | USD 1,776.92 | USD -3,527.80 | 3 |
| 5Y | qqq_underperforms_spy_20d | 1:3 | 5d | 26/26 | 61.54% | USD 132.38 | USD 3,441.80 | USD 688.36 | USD -1,718.20 | 0 |
| 5Y | qqq_underperforms_spy_20d | 1:3 | 10d | 26/26 | 76.92% | USD 277.07 | USD 7,203.80 | USD 1,440.76 | USD -1,570.20 | 0 |
| 5Y | qqq_underperforms_spy_20d | 1:3 | 20d | 25/26 | 88.00% | USD 655.68 | USD 16,392.00 | USD 3,278.40 | USD -613.20 | 1 |
| 5Y | qqq_underperforms_spy_20d | 1:3 | DTE<=7 | 23/26 | 86.96% | USD 390.45 | USD 8,980.40 | USD 1,796.08 | USD -3,572.20 | 3 |
| 5Y | none | 1:6 | 5d | 28/28 | 71.43% | USD 177.01 | USD 4,956.20 | USD 991.24 | USD -4,163.10 | 0 |
| 5Y | none | 1:6 | 10d | 28/28 | 60.71% | USD -360.60 | USD -10,096.80 | USD -2,019.36 | USD -10,453.10 | 0 |
| 5Y | none | 1:6 | 20d | 28/28 | 78.57% | USD 461.90 | USD 12,933.20 | USD 2,586.64 | USD -13,212.10 | 0 |
| 5Y | none | 1:6 | DTE<=7 | 27/28 | 81.48% | USD 211.64 | USD 5,714.30 | USD 1,142.86 | USD -20,318.10 | 1 |
| 5Y | none | 4:5 | 5d | 28/28 | 50.00% | USD -56.13 | USD -1,571.60 | USD -314.32 | USD -2,180.70 | 0 |
| 5Y | none | 4:5 | 10d | 28/28 | 53.57% | USD -285.31 | USD -7,988.60 | USD -1,597.72 | USD -2,929.70 | 0 |
| 5Y | none | 4:5 | 20d | 28/28 | 71.43% | USD -100.49 | USD -2,813.60 | USD -562.72 | USD -3,203.70 | 0 |
| 5Y | none | 4:5 | DTE<=7 | 27/28 | 81.48% | USD -133.33 | USD -3,599.90 | USD -719.98 | USD -7,641.70 | 1 |
| 5Y | none | 2:4 | 5d | 28/28 | 71.43% | USD 11.70 | USD 327.60 | USD 65.52 | USD -1,867.80 | 0 |
| 5Y | none | 2:4 | 10d | 28/28 | 60.71% | USD -234.66 | USD -6,570.40 | USD -1,314.08 | USD -4,239.80 | 0 |
| 5Y | none | 2:4 | 20d | 28/28 | 75.00% | USD 100.27 | USD 2,807.60 | USD 561.52 | USD -5,309.80 | 0 |
| 5Y | none | 2:4 | DTE<=7 | 27/28 | 81.48% | USD 9.61 | USD 259.40 | USD 51.88 | USD -9,633.80 | 1 |
| 5Y | none | 1:3 | 5d | 28/28 | 71.43% | USD 54.80 | USD 1,534.40 | USD 306.88 | USD -1,741.20 | 0 |
| 5Y | none | 1:3 | 10d | 28/28 | 60.71% | USD -178.52 | USD -4,998.60 | USD -999.72 | USD -4,203.20 | 0 |
| 5Y | none | 1:3 | 20d | 28/28 | 78.57% | USD 153.16 | USD 4,288.40 | USD 857.68 | USD -5,294.20 | 0 |
| 5Y | none | 1:3 | DTE<=7 | 27/28 | 81.48% | USD 56.65 | USD 1,529.60 | USD 305.92 | USD -8,692.20 | 1 |

## 20-session exit under slippage stress (USD 0.10 per option share per side)

Derived by adding USD 10 per contract round-trip to each resolved trade versus base slippage; not a new fill simulation.

| Window | Filter | Ratio | Resolved | Mean stressed net/trade | Total stressed net | Annualized stressed net | Worst stressed trade |
|---|---|---:|---:|---:|---:|---:|---:|
| 1Y | qqq_underperforms_spy_20d | 1:6 | 5 | USD 2,160.50 | USD 10,802.50 | USD 10,802.50 | USD -1,440.10 |
| 1Y | qqq_underperforms_spy_20d | 4:5 | 5 | USD 93.90 | USD 469.50 | USD 469.50 | USD -776.70 |
| 1Y | qqq_underperforms_spy_20d | 2:4 | 5 | USD 721.80 | USD 3,609.00 | USD 3,609.00 | USD -781.80 |
| 1Y | qqq_underperforms_spy_20d | 1:3 | 5 | USD 810.80 | USD 4,054.00 | USD 4,054.00 | USD -653.20 |
| 1Y | none | 1:6 | 6 | USD 1,563.40 | USD 9,380.40 | USD 9,380.40 | USD -2,178.10 |
| 1Y | none | 4:5 | 6 | USD 236.13 | USD 1,416.80 | USD 1,416.80 | USD -53.70 |
| 1Y | none | 2:4 | 6 | USD 579.87 | USD 3,479.20 | USD 3,479.20 | USD -713.80 |
| 1Y | none | 1:3 | 6 | USD 608.30 | USD 3,649.80 | USD 3,649.80 | USD -812.20 |
| 3Y | qqq_underperforms_spy_20d | 1:6 | 14 | USD 1,404.40 | USD 19,661.60 | USD 6,553.87 | USD -1,440.10 |
| 3Y | qqq_underperforms_spy_20d | 4:5 | 14 | USD -53.34 | USD -746.80 | USD -248.93 | USD -864.70 |
| 3Y | qqq_underperforms_spy_20d | 2:4 | 14 | USD 445.91 | USD 6,242.80 | USD 2,080.93 | USD -781.80 |
| 3Y | qqq_underperforms_spy_20d | 1:3 | 14 | USD 513.87 | USD 7,194.20 | USD 2,398.07 | USD -653.20 |
| 3Y | none | 1:6 | 17 | USD 537.19 | USD 9,132.30 | USD 3,044.10 | USD -9,446.10 |
| 3Y | none | 4:5 | 17 | USD -176.11 | USD -2,993.90 | USD -997.97 | USD -3,293.70 |
| 3Y | none | 2:4 | 17 | USD 90.08 | USD 1,531.40 | USD 510.47 | USD -4,369.80 |
| 3Y | none | 1:3 | 17 | USD 168.21 | USD 2,859.60 | USD 953.20 | USD -4,000.20 |
| 5Y | qqq_underperforms_spy_20d | 1:6 | 25 | USD 1,588.22 | USD 39,705.50 | USD 7,941.10 | USD -2,208.10 |
| 5Y | qqq_underperforms_spy_20d | 4:5 | 25 | USD 183.66 | USD 4,591.50 | USD 918.30 | USD -864.70 |
| 5Y | qqq_underperforms_spy_20d | 2:4 | 25 | USD 589.64 | USD 14,741.00 | USD 2,948.20 | USD -781.80 |
| 5Y | qqq_underperforms_spy_20d | 1:3 | 25 | USD 615.68 | USD 15,392.00 | USD 3,078.40 | USD -653.20 |
| 5Y | none | 1:6 | 28 | USD 391.90 | USD 10,973.20 | USD 2,194.64 | USD -13,282.10 |
| 5Y | none | 4:5 | 28 | USD -190.49 | USD -5,333.60 | USD -1,066.72 | USD -3,293.70 |
| 5Y | none | 2:4 | 28 | USD 40.27 | USD 1,127.60 | USD 225.52 | USD -5,369.80 |
| 5Y | none | 1:3 | 28 | USD 113.16 | USD 3,168.40 | USD 633.68 | USD -5,334.20 |

## Calendar-year count and 20-session P&L

| Year | Filter | Ratio | Selected cohorts | Entered | Skipped | Resolved/unresolved | Win rate | Mean net/trade | Total resolved net |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | qqq_underperforms_spy_20d | 1:6 | 4 | 4 | 0 | 4/0 | 75.00% | USD 378.65 | USD 1,514.60 |
| 2019 | qqq_underperforms_spy_20d | 1:6 | 4 | 4 | 0 | 4/0 | 100.00% | USD 1,175.15 | USD 4,700.60 |
| 2020 | qqq_underperforms_spy_20d | 1:6 | 4 | 4 | 0 | 4/0 | 100.00% | USD 1,891.40 | USD 7,565.60 |
| 2021 | qqq_underperforms_spy_20d | 1:6 | 5 | 5 | 0 | 5/0 | 100.00% | USD 2,072.30 | USD 10,361.50 |
| 2022 | qqq_underperforms_spy_20d | 1:6 | 5 | 5 | 0 | 5/0 | 80.00% | USD 1,559.30 | USD 7,796.50 |
| 2023 | qqq_underperforms_spy_20d | 1:6 | 5 | 5 | 0 | 4/1 | 75.00% | USD 848.65 | USD 3,394.60 |
| 2024 | qqq_underperforms_spy_20d | 1:6 | 5 | 5 | 0 | 5/0 | 100.00% | USD 1,308.90 | USD 6,544.50 |
| 2025 | qqq_underperforms_spy_20d | 1:6 | 3 | 3 | 0 | 3/0 | 66.67% | USD 2,816.23 | USD 8,448.70 |
| 2018 | qqq_underperforms_spy_20d | 4:5 | 4 | 4 | 0 | 4/0 | 75.00% | USD -251.45 | USD -1,005.80 |
| 2019 | qqq_underperforms_spy_20d | 4:5 | 4 | 4 | 0 | 4/0 | 100.00% | USD 355.30 | USD 1,421.20 |
| 2020 | qqq_underperforms_spy_20d | 4:5 | 4 | 4 | 0 | 4/0 | 75.00% | USD 289.55 | USD 1,158.20 |
| 2021 | qqq_underperforms_spy_20d | 4:5 | 5 | 5 | 0 | 5/0 | 100.00% | USD 588.10 | USD 2,940.50 |
| 2022 | qqq_underperforms_spy_20d | 4:5 | 5 | 5 | 0 | 5/0 | 80.00% | USD 687.30 | USD 3,436.50 |
| 2023 | qqq_underperforms_spy_20d | 4:5 | 5 | 5 | 0 | 4/1 | 25.00% | USD -238.20 | USD -952.80 |
| 2024 | qqq_underperforms_spy_20d | 4:5 | 5 | 5 | 0 | 5/0 | 60.00% | USD 20.90 | USD 104.50 |
| 2025 | qqq_underperforms_spy_20d | 4:5 | 3 | 3 | 0 | 3/0 | 66.67% | USD 370.97 | USD 1,112.90 |
| 2018 | qqq_underperforms_spy_20d | 2:4 | 4 | 4 | 0 | 4/0 | 75.00% | USD 13.70 | USD 54.80 |
| 2019 | qqq_underperforms_spy_20d | 2:4 | 4 | 4 | 0 | 4/0 | 100.00% | USD 520.70 | USD 2,082.80 |
| 2020 | qqq_underperforms_spy_20d | 2:4 | 4 | 4 | 0 | 4/0 | 100.00% | USD 719.20 | USD 2,876.80 |
| 2021 | qqq_underperforms_spy_20d | 2:4 | 5 | 5 | 0 | 5/0 | 100.00% | USD 886.20 | USD 4,431.00 |
| 2022 | qqq_underperforms_spy_20d | 2:4 | 5 | 5 | 0 | 5/0 | 80.00% | USD 781.80 | USD 3,909.00 |
| 2023 | qqq_underperforms_spy_20d | 2:4 | 5 | 5 | 0 | 4/1 | 75.00% | USD 167.70 | USD 670.80 |
| 2024 | qqq_underperforms_spy_20d | 2:4 | 5 | 5 | 0 | 5/0 | 100.00% | USD 491.80 | USD 2,459.00 |
| 2025 | qqq_underperforms_spy_20d | 2:4 | 3 | 3 | 0 | 3/0 | 66.67% | USD 1,045.53 | USD 3,136.60 |
| 2018 | qqq_underperforms_spy_20d | 1:3 | 4 | 4 | 0 | 4/0 | 75.00% | USD 99.80 | USD 399.20 |
| 2019 | qqq_underperforms_spy_20d | 1:3 | 4 | 4 | 0 | 4/0 | 100.00% | USD 489.05 | USD 1,956.20 |
| 2020 | qqq_underperforms_spy_20d | 1:3 | 4 | 4 | 0 | 4/0 | 100.00% | USD 742.55 | USD 2,970.20 |
| 2021 | qqq_underperforms_spy_20d | 1:3 | 5 | 5 | 0 | 5/0 | 100.00% | USD 850.40 | USD 4,252.00 |
| 2022 | qqq_underperforms_spy_20d | 1:3 | 5 | 5 | 0 | 5/0 | 80.00% | USD 683.00 | USD 3,415.00 |
| 2023 | qqq_underperforms_spy_20d | 1:3 | 5 | 5 | 0 | 4/1 | 75.00% | USD 275.05 | USD 1,100.20 |
| 2024 | qqq_underperforms_spy_20d | 1:3 | 5 | 5 | 0 | 5/0 | 100.00% | USD 499.20 | USD 2,496.00 |
| 2025 | qqq_underperforms_spy_20d | 1:3 | 3 | 3 | 0 | 3/0 | 66.67% | USD 1,096.13 | USD 3,288.40 |
| 2018 | none | 1:6 | 5 | 5 | 0 | 5/0 | 60.00% | USD -724.50 | USD -3,622.50 |
| 2019 | none | 1:6 | 6 | 6 | 0 | 6/0 | 100.00% | USD 1,146.23 | USD 6,877.40 |
| 2020 | none | 1:6 | 5 | 5 | 0 | 5/0 | 80.00% | USD -8,985.90 | USD -44,929.50 |
| 2021 | none | 1:6 | 6 | 6 | 0 | 6/0 | 100.00% | USD 2,538.57 | USD 15,231.40 |
| 2022 | none | 1:6 | 6 | 6 | 0 | 6/0 | 50.00% | USD -3,246.43 | USD -19,478.60 |
| 2023 | none | 1:6 | 5 | 5 | 0 | 5/0 | 80.00% | USD 1,160.90 | USD 5,804.50 |
| 2024 | none | 1:6 | 6 | 6 | 0 | 6/0 | 83.33% | USD 888.73 | USD 5,332.40 |
| 2025 | none | 1:6 | 3 | 3 | 0 | 3/0 | 66.67% | USD 1,209.23 | USD 3,627.70 |
| 2018 | none | 4:5 | 5 | 5 | 0 | 5/0 | 60.00% | USD -646.30 | USD -3,231.50 |
| 2019 | none | 4:5 | 6 | 6 | 0 | 6/0 | 100.00% | USD 340.97 | USD 2,045.80 |
| 2020 | none | 4:5 | 5 | 5 | 0 | 5/0 | 60.00% | USD -4,967.90 | USD -24,839.50 |
| 2021 | none | 4:5 | 6 | 6 | 0 | 6/0 | 83.33% | USD 283.13 | USD 1,698.80 |
| 2022 | none | 4:5 | 6 | 6 | 0 | 6/0 | 50.00% | USD -937.20 | USD -5,623.20 |
| 2023 | none | 4:5 | 5 | 5 | 0 | 5/0 | 80.00% | USD 58.90 | USD 294.50 |
| 2024 | none | 4:5 | 6 | 6 | 0 | 6/0 | 66.67% | USD -105.37 | USD -632.20 |
| 2025 | none | 4:5 | 3 | 3 | 0 | 3/0 | 100.00% | USD 373.97 | USD 1,121.90 |
| 2018 | none | 2:4 | 5 | 5 | 0 | 5/0 | 60.00% | USD -500.60 | USD -2,503.00 |
| 2019 | none | 2:4 | 6 | 6 | 0 | 6/0 | 100.00% | USD 505.53 | USD 3,033.20 |
| 2020 | none | 2:4 | 5 | 5 | 0 | 5/0 | 60.00% | USD -4,929.40 | USD -24,647.00 |
| 2021 | none | 2:4 | 6 | 6 | 0 | 6/0 | 100.00% | USD 920.87 | USD 5,525.20 |
| 2022 | none | 2:4 | 6 | 6 | 0 | 6/0 | 50.00% | USD -1,419.80 | USD -8,518.80 |
| 2023 | none | 2:4 | 5 | 5 | 0 | 5/0 | 80.00% | USD 391.40 | USD 1,957.00 |
| 2024 | none | 2:4 | 6 | 6 | 0 | 6/0 | 83.33% | USD 238.87 | USD 1,433.20 |
| 2025 | none | 2:4 | 3 | 3 | 0 | 3/0 | 66.67% | USD 503.53 | USD 1,510.60 |
| 2018 | none | 1:3 | 5 | 5 | 0 | 5/0 | 60.00% | USD -369.00 | USD -1,845.00 |
| 2019 | none | 1:3 | 6 | 6 | 0 | 6/0 | 100.00% | USD 476.13 | USD 2,856.80 |
| 2020 | none | 1:3 | 5 | 5 | 0 | 5/0 | 80.00% | USD -4,095.00 | USD -20,475.00 |
| 2021 | none | 1:3 | 6 | 6 | 0 | 6/0 | 100.00% | USD 979.97 | USD 5,879.80 |
| 2022 | none | 1:3 | 6 | 6 | 0 | 6/0 | 50.00% | USD -1,344.03 | USD -8,064.20 |
| 2023 | none | 1:3 | 5 | 5 | 0 | 5/0 | 80.00% | USD 437.00 | USD 2,185.00 |
| 2024 | none | 1:3 | 6 | 6 | 0 | 6/0 | 83.33% | USD 312.13 | USD 1,872.80 |
| 2025 | none | 1:3 | 3 | 3 | 0 | 3/0 | 66.67% | USD 491.13 | USD 1,473.40 |

## Interpretation limits

- One cohort is attempted per roughly 45 common sessions; removing the relative-performance gate does not mean entering every day.
- Counts refer to strategy cohorts, not contracts: 1:3 opens four contracts, 2:4 six, 4:5 nine, and 1:6 seven.
- P&L is the sum of resolved fixed-size cohorts, not compounded NAV, and does not model portfolio overlap or capital recycling.
- Unresolved episodes are excluded from resolved P&L but reported separately, never assigned zero.
- The 0.10 slippage result adds USD 10 per contract round-trip versus base slippage; it does not simulate market impact.
- EOD displayed size is not a guaranteed multi-leg fill; broker margin, financing and forced liquidation are not modeled.
- Ratios were selected after reviewing the same historical period; this is in-sample comparison, not forward-alpha evidence.
