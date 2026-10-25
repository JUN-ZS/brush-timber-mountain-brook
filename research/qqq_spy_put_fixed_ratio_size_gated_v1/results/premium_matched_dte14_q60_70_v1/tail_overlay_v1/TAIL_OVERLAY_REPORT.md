# TAIL ETF paired overlay: QQQ LONG PUT / SPY SHORT PUT

Window 2018-03-01 to 2025-12-15; elapsed 7.792 years; policy HOLD_20_OR_DTE_LE_7.

For each resolved strategy cohort, invest USD 250, 500, or 1,000 in TAIL at the cohort entry-date adjusted close and close it on that cohort exit date. TAIL uses dividend-adjusted daily prices. Friction sensitivity is 0 and 10 bps round-trip. These budgets are ETF capital deployed, not option premiums.

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
| 1:3 | USD 500.00 | 0 | USD -234.92 | USD -33,701.12 | USD -86.19 | USD -6.82 | 48.34% | USD -10,555.49 | USD 73.71 | 83/199 (41.7%) | 5/199 (2.5%) | USD 936.48 / USD 99,131.80 (0.94%) | 100.00% |
| 1:3 | USD 500.00 | 10 | USD -430.42 | USD -33,896.62 | USD -86.69 | USD -7.32 | 48.34% | USD -10,555.99 | USD 73.21 | 75/199 (37.7%) | 4/199 (2.0%) | USD 896.59 / USD 99,131.80 (0.90%) | 100.00% |
| 1:3 | USD 1,000.00 | 0 | USD -469.83 | USD -33,936.03 | USD -86.79 | USD -7.48 | 48.59% | USD -10,481.78 | USD 147.42 | 83/199 (41.7%) | 6/199 (3.0%) | USD 1,872.96 / USD 99,131.80 (1.89%) | 100.00% |
| 1:3 | USD 1,000.00 | 10 | USD -860.83 | USD -34,327.03 | USD -87.79 | USD -8.48 | 48.59% | USD -10,482.78 | USD 146.42 | 75/199 (37.7%) | 6/199 (3.0%) | USD 1,793.17 / USD 99,131.80 (1.81%) | 100.00% |
| 1:6 | USD 250.00 | 0 | USD -125.98 | USD -16,894.08 | USD -43.21 | USD 285.52 | 75.45% | USD -26,735.06 | USD 33.04 | 72/96 (75.0%) | 1/96 (1.0%) | USD 517.99 / USD 198,829.60 (0.26%) | 100.00% |
| 1:6 | USD 250.00 | 10 | USD -223.73 | USD -16,991.83 | USD -43.46 | USD 285.27 | 75.45% | USD -26,735.31 | USD 32.79 | 69/96 (71.9%) | 1/96 (1.0%) | USD 500.30 / USD 198,829.60 (0.25%) | 100.00% |
| 1:6 | USD 500.00 | 0 | USD -251.97 | USD -17,020.07 | USD -43.53 | USD 283.37 | 75.19% | USD -26,702.03 | USD 66.07 | 72/96 (75.0%) | 3/96 (3.1%) | USD 1,035.98 / USD 198,829.60 (0.52%) | 100.00% |
| 1:6 | USD 500.00 | 10 | USD -447.47 | USD -17,215.57 | USD -44.03 | USD 282.87 | 75.19% | USD -26,702.53 | USD 65.57 | 69/96 (71.9%) | 2/96 (2.1%) | USD 1,000.59 / USD 198,829.60 (0.50%) | 100.00% |
| 1:6 | USD 1,000.00 | 0 | USD -503.94 | USD -17,272.04 | USD -44.17 | USD 276.84 | 75.45% | USD -26,635.95 | USD 132.15 | 72/96 (75.0%) | 5/96 (5.2%) | USD 2,071.95 / USD 198,829.60 (1.04%) | 100.00% |
| 1:6 | USD 1,000.00 | 10 | USD -894.94 | USD -17,663.04 | USD -45.17 | USD 275.84 | 75.45% | USD -26,636.95 | USD 131.15 | 69/96 (71.9%) | 5/96 (5.2%) | USD 2,001.19 / USD 198,829.60 (1.01%) | 100.00% |

## Caveats

- Episode totals include overlapping trades and overlapping TAIL stakes; they are not portfolio returns or account CAGR.
- The overlay holds TAIL for the exact matched option-cohort interval. It is not a VIX/volatility-triggered hedge.
- Daily adjusted closes are not guaranteed executable fills. The 10 bps friction is a sensitivity case, not reconstructed historical spread.
- TAIL can decline during a losing option cohort. All resolved episode pairs are reported; unresolved core episodes are excluded.
- The source hash, query URL, and retrieval time are in source_manifest.json; the daily prices used are stored in TAIL_adjusted_close.csv.
