# TAIL ETF paired overlay: QQQ LONG PUT / SPY SHORT PUT

Window 2018-03-01 to 2025-12-15; elapsed 7.792 years; policy HOLD_20_OR_DTE_LE_7.

For each resolved strategy cohort, invest USD 250, 500, 1,000, or 2,500 in TAIL at the cohort entry-date adjusted close and close it on that cohort exit date. TAIL uses dividend-adjusted daily prices. Friction sensitivity is 0, 10, 25, and 50 bps round-trip. These budgets are ETF capital deployed, not option premiums.

## No-TAIL baseline

| Ratio | Resolved | Total episode P&L | Average / cohort | Median / cohort | Win rate | Worst cohort | Annual average episode P&L |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | 391 | USD -33,466.20 | USD -85.59 | USD -10.20 | 49.10% | USD -10,629.20 | USD -4,294.90 |
| 1:6 | 391 | USD -16,768.10 | USD -42.89 | USD 286.90 | 75.45% | USD -26,768.10 | USD -2,151.94 |

## TAIL overlay sensitivity

| Ratio | TAIL capital / cohort | Friction bps | TAIL total episode P&L | Combined total episode P&L | Mean combined / cohort | Median combined / cohort | Combined win rate | Worst combined cohort | Improvement on original worst cohort | Core losses with positive TAIL | Core losses offset >=25% | Positive TAIL P&L on losers / core loss dollars | Price pairing coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | USD 250.00 | 0 | USD -117.46 | USD -33,583.66 | USD -85.89 | USD -9.02 | 48.85% | USD -10,592.35 | USD 36.85 | 83/199 (41.7%) | 2/199 (1.0%) | USD 468.24 / USD 99,131.80 (0.47%) | 100.00% |
| 1:3 | USD 250.00 | 10 | USD -215.21 | USD -33,681.41 | USD -86.14 | USD -9.27 | 48.85% | USD -10,592.60 | USD 36.60 | 75/199 (37.7%) | 2/199 (1.0%) | USD 448.29 / USD 99,131.80 (0.45%) | 100.00% |
| 1:3 | USD 250.00 | 25 | USD -361.83 | USD -33,828.03 | USD -86.52 | USD -9.64 | 48.85% | USD -10,592.97 | USD 36.23 | 65/199 (32.7%) | 2/199 (1.0%) | USD 421.96 / USD 99,131.80 (0.43%) | 100.00% |
| 1:3 | USD 250.00 | 50 | USD -606.21 | USD -34,072.41 | USD -87.14 | USD -10.27 | 48.59% | USD -10,593.60 | USD 35.60 | 56/199 (28.1%) | 1/199 (0.5%) | USD 384.36 / USD 99,131.80 (0.39%) | 100.00% |
| 1:3 | USD 500.00 | 0 | USD -234.92 | USD -33,701.12 | USD -86.19 | USD -6.82 | 48.34% | USD -10,555.49 | USD 73.71 | 83/199 (41.7%) | 5/199 (2.5%) | USD 936.48 / USD 99,131.80 (0.94%) | 100.00% |
| 1:3 | USD 500.00 | 10 | USD -430.42 | USD -33,896.62 | USD -86.69 | USD -7.32 | 48.34% | USD -10,555.99 | USD 73.21 | 75/199 (37.7%) | 4/199 (2.0%) | USD 896.59 / USD 99,131.80 (0.90%) | 100.00% |
| 1:3 | USD 500.00 | 25 | USD -723.67 | USD -34,189.87 | USD -87.44 | USD -8.07 | 48.08% | USD -10,556.74 | USD 72.46 | 65/199 (32.7%) | 4/199 (2.0%) | USD 843.93 / USD 99,131.80 (0.85%) | 100.00% |
| 1:3 | USD 500.00 | 50 | USD -1,212.42 | USD -34,678.62 | USD -88.69 | USD -9.32 | 48.08% | USD -10,557.99 | USD 71.21 | 56/199 (28.1%) | 2/199 (1.0%) | USD 768.72 / USD 99,131.80 (0.78%) | 100.00% |
| 1:3 | USD 1,000.00 | 0 | USD -469.84 | USD -33,936.04 | USD -86.79 | USD -7.48 | 48.59% | USD -10,481.78 | USD 147.42 | 83/199 (41.7%) | 6/199 (3.0%) | USD 1,872.96 / USD 99,131.80 (1.89%) | 100.00% |
| 1:3 | USD 1,000.00 | 10 | USD -860.84 | USD -34,327.04 | USD -87.79 | USD -8.48 | 48.59% | USD -10,482.78 | USD 146.42 | 75/199 (37.7%) | 6/199 (3.0%) | USD 1,793.17 / USD 99,131.80 (1.81%) | 100.00% |
| 1:3 | USD 1,000.00 | 25 | USD -1,447.34 | USD -34,913.54 | USD -89.29 | USD -9.98 | 48.59% | USD -10,484.28 | USD 144.92 | 65/199 (32.7%) | 6/199 (3.0%) | USD 1,687.85 / USD 99,131.80 (1.70%) | 100.00% |
| 1:3 | USD 1,000.00 | 50 | USD -2,424.84 | USD -35,891.04 | USD -91.79 | USD -12.48 | 48.34% | USD -10,486.78 | USD 142.42 | 56/199 (28.1%) | 6/199 (3.0%) | USD 1,537.43 / USD 99,131.80 (1.55%) | 100.00% |
| 1:3 | USD 2,500.00 | 0 | USD -1,174.59 | USD -34,640.79 | USD -88.60 | USD -15.61 | 48.85% | USD -10,260.65 | USD 368.55 | 83/199 (41.7%) | 17/199 (8.5%) | USD 4,682.39 / USD 99,131.80 (4.72%) | 100.00% |
| 1:3 | USD 2,500.00 | 10 | USD -2,152.09 | USD -35,618.29 | USD -91.10 | USD -18.11 | 48.85% | USD -10,263.15 | USD 366.05 | 75/199 (37.7%) | 14/199 (7.0%) | USD 4,482.93 / USD 99,131.80 (4.52%) | 100.00% |
| 1:3 | USD 2,500.00 | 25 | USD -3,618.34 | USD -37,084.54 | USD -94.85 | USD -21.86 | 47.83% | USD -10,266.90 | USD 362.30 | 65/199 (32.7%) | 10/199 (5.0%) | USD 4,219.63 / USD 99,131.80 (4.26%) | 100.00% |
| 1:3 | USD 2,500.00 | 50 | USD -6,062.09 | USD -39,528.29 | USD -101.10 | USD -28.11 | 47.06% | USD -10,273.15 | USD 356.05 | 56/199 (28.1%) | 9/199 (4.5%) | USD 3,843.58 / USD 99,131.80 (3.88%) | 100.00% |
| 1:6 | USD 250.00 | 0 | USD -125.98 | USD -16,894.08 | USD -43.21 | USD 285.52 | 75.45% | USD -26,735.06 | USD 33.04 | 72/96 (75.0%) | 1/96 (1.0%) | USD 517.99 / USD 198,829.60 (0.26%) | 100.00% |
| 1:6 | USD 250.00 | 10 | USD -223.73 | USD -16,991.83 | USD -43.46 | USD 285.27 | 75.45% | USD -26,735.31 | USD 32.79 | 69/96 (71.9%) | 1/96 (1.0%) | USD 500.30 / USD 198,829.60 (0.25%) | 100.00% |
| 1:6 | USD 250.00 | 25 | USD -370.36 | USD -17,138.46 | USD -43.83 | USD 284.89 | 75.19% | USD -26,735.69 | USD 32.41 | 67/96 (69.8%) | 0/96 (0.0%) | USD 474.68 / USD 198,829.60 (0.24%) | 100.00% |
| 1:6 | USD 250.00 | 50 | USD -614.73 | USD -17,382.83 | USD -44.46 | USD 284.27 | 75.19% | USD -26,736.31 | USD 31.79 | 59/96 (61.5%) | 0/96 (0.0%) | USD 435.48 / USD 198,829.60 (0.22%) | 100.00% |
| 1:6 | USD 500.00 | 0 | USD -251.97 | USD -17,020.07 | USD -43.53 | USD 283.37 | 75.19% | USD -26,702.03 | USD 66.07 | 72/96 (75.0%) | 3/96 (3.1%) | USD 1,035.98 / USD 198,829.60 (0.52%) | 100.00% |
| 1:6 | USD 500.00 | 10 | USD -447.47 | USD -17,215.57 | USD -44.03 | USD 282.87 | 75.19% | USD -26,702.53 | USD 65.57 | 69/96 (71.9%) | 2/96 (2.1%) | USD 1,000.59 / USD 198,829.60 (0.50%) | 100.00% |
| 1:6 | USD 500.00 | 25 | USD -740.72 | USD -17,508.82 | USD -44.78 | USD 282.12 | 75.19% | USD -26,703.28 | USD 64.82 | 67/96 (69.8%) | 1/96 (1.0%) | USD 949.35 / USD 198,829.60 (0.48%) | 100.00% |
| 1:6 | USD 500.00 | 50 | USD -1,229.47 | USD -17,997.57 | USD -46.03 | USD 280.87 | 75.19% | USD -26,704.53 | USD 63.57 | 59/96 (61.5%) | 0/96 (0.0%) | USD 870.96 / USD 198,829.60 (0.44%) | 100.00% |
| 1:6 | USD 1,000.00 | 0 | USD -503.94 | USD -17,272.04 | USD -44.17 | USD 276.84 | 75.45% | USD -26,635.95 | USD 132.15 | 72/96 (75.0%) | 5/96 (5.2%) | USD 2,071.95 / USD 198,829.60 (1.04%) | 100.00% |
| 1:6 | USD 1,000.00 | 10 | USD -894.94 | USD -17,663.04 | USD -45.17 | USD 275.84 | 75.45% | USD -26,636.95 | USD 131.15 | 69/96 (71.9%) | 5/96 (5.2%) | USD 2,001.19 / USD 198,829.60 (1.01%) | 100.00% |
| 1:6 | USD 1,000.00 | 25 | USD -1,481.44 | USD -18,249.54 | USD -46.67 | USD 274.34 | 75.19% | USD -26,638.45 | USD 129.65 | 67/96 (69.8%) | 4/96 (4.2%) | USD 1,898.71 / USD 198,829.60 (0.95%) | 100.00% |
| 1:6 | USD 1,000.00 | 50 | USD -2,458.94 | USD -19,227.04 | USD -49.17 | USD 271.84 | 75.19% | USD -26,640.95 | USD 127.15 | 59/96 (61.5%) | 1/96 (1.0%) | USD 1,741.92 / USD 198,829.60 (0.88%) | 100.00% |
| 1:6 | USD 2,500.00 | 0 | USD -1,259.85 | USD -18,027.95 | USD -46.11 | USD 265.13 | 75.70% | USD -26,437.74 | USD 330.36 | 72/96 (75.0%) | 10/96 (10.4%) | USD 5,179.88 / USD 198,829.60 (2.61%) | 100.00% |
| 1:6 | USD 2,500.00 | 10 | USD -2,237.35 | USD -19,005.45 | USD -48.61 | USD 262.63 | 75.70% | USD -26,440.24 | USD 327.86 | 69/96 (71.9%) | 10/96 (10.4%) | USD 5,002.97 / USD 198,829.60 (2.52%) | 100.00% |
| 1:6 | USD 2,500.00 | 25 | USD -3,703.60 | USD -20,471.70 | USD -52.36 | USD 258.88 | 75.19% | USD -26,443.99 | USD 324.11 | 67/96 (69.8%) | 9/96 (9.4%) | USD 4,746.77 / USD 198,829.60 (2.39%) | 100.00% |
| 1:6 | USD 2,500.00 | 50 | USD -6,147.35 | USD -22,915.45 | USD -58.61 | USD 252.63 | 74.42% | USD -26,450.24 | USD 317.86 | 59/96 (61.5%) | 7/96 (7.3%) | USD 4,354.79 / USD 198,829.60 (2.19%) | 100.00% |

## Caveats

- Episode totals include overlapping trades and overlapping TAIL stakes; they are not portfolio returns or account CAGR.
- The overlay holds TAIL for the exact matched option-cohort interval. It is not a VIX/volatility-triggered hedge.
- Daily adjusted closes are not guaranteed executable fills. The 0–50 bps friction grid is a scenario sensitivity, not a reconstruction of historical bid/ask spreads.
- TAIL can decline during a losing option cohort. All resolved episode pairs are reported; unresolved core episodes are excluded.
- The source hash, query URL, and retrieval time are in source_manifest.json; the daily prices used are stored in TAIL_adjusted_close.csv.
