# QQQ/SPY Fixed-Ratio Temporal Stability Audit

- Common signal episodes: 36 across all ratios.
- Groups use signal date and include individual calendar years plus three frozen eras.
- Uses existing base-cost EOD quote-side estimates, not verified fills.
- Cohort integrity: all four ratio outputs have identical episode IDs and signal dates.

## Full-period reference

| Ratio | Exit | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Worst resolved trade | Unresolved |
|---|---|---:|---:|---:|---:|---:|---:|
| 1:6 | 5 sessions | 36/36 | 69.44% | USD 390.84 | USD 14,070.40 | USD -4,827.10 | 0 |
| 1:6 | 10 sessions | 36/36 | 80.56% | USD 770.29 | USD 27,730.40 | USD -3,830.10 | 0 |
| 1:6 | 20 sessions | 34/36 | 88.24% | USD 1,480.19 | USD 50,326.60 | USD -2,204.10 | 2 |
| 1:6 | DTE ≤ 7 | 30/36 | 80.00% | USD 675.90 | USD 20,277.00 | USD -8,997.10 | 6 |
| 4:5 | 5 sessions | 36/36 | 58.33% | USD 5.27 | USD 189.80 | USD -787.70 | 0 |
| 4:5 | 10 sessions | 36/36 | 63.89% | USD 113.63 | USD 4,090.80 | USD -1,007.70 | 0 |
| 4:5 | 20 sessions | 34/36 | 73.53% | USD 241.62 | USD 8,215.20 | USD -1,894.70 | 2 |
| 4:5 | DTE ≤ 7 | 30/36 | 70.00% | USD -6.20 | USD -186.00 | USD -4,303.70 | 6 |
| 2:4 | 5 sessions | 36/36 | 66.67% | USD 150.31 | USD 5,411.20 | USD -1,363.80 | 0 |
| 2:4 | 10 sessions | 36/36 | 77.78% | USD 302.37 | USD 10,885.20 | USD -1,633.80 | 0 |
| 2:4 | 20 sessions | 34/36 | 88.24% | USD 577.08 | USD 19,620.80 | USD -1,493.80 | 2 |
| 2:4 | DTE ≤ 7 | 30/36 | 83.33% | USD 213.20 | USD 6,396.00 | USD -4,031.80 | 6 |
| 1:3 | 5 sessions | 36/36 | 63.89% | USD 140.91 | USD 5,072.80 | USD -1,718.20 | 0 |
| 1:3 | 10 sessions | 36/36 | 80.56% | USD 299.44 | USD 10,779.80 | USD -1,570.20 | 0 |
| 1:3 | 20 sessions | 34/36 | 88.24% | USD 584.62 | USD 19,877.20 | USD -1,111.20 | 2 |
| 1:3 | DTE ≤ 7 | 30/36 | 83.33% | USD 247.60 | USD 7,428.00 | USD -3,572.20 | 6 |

## Ten-session hold by era

P&L and win rate use resolved trades only; opened/resolved/unresolved counts remain explicit.

| Ratio | Era | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Worst trade | QQQ LONG gross mean | SPY SHORT gross mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1:6 | 2018-2021 | 17/17 | 88.24% | USD 921.49 | USD 15,665.30 | USD -1,456.10 | USD -155.29 | USD 1,155.88 |
| 1:6 | 2022-2023 | 10/10 | 60.00% | USD -34.60 | USD -346.00 | USD -3,830.10 | USD -50.30 | USD 94.80 |
| 1:6 | 2024-2025 | 9/9 | 88.89% | USD 1,379.01 | USD 12,411.10 | USD -3,817.10 | USD -291.22 | USD 1,749.33 |
| 4:5 | 2018-2021 | 17/17 | 88.24% | USD 240.36 | USD 4,086.10 | USD -688.70 | USD -621.18 | USD 963.24 |
| 4:5 | 2022-2023 | 10/10 | 20.00% | USD -223.90 | USD -2,239.00 | USD -1,007.70 | USD -201.20 | USD 79.00 |
| 4:5 | 2024-2025 | 9/9 | 66.67% | USD 249.30 | USD 2,243.70 | USD -364.70 | USD -1,241.78 | USD 1,592.78 |
| 2:4 | 2018-2021 | 17/17 | 88.24% | USD 392.20 | USD 6,667.40 | USD -749.80 | USD -310.59 | USD 770.59 |
| 2:4 | 2022-2023 | 10/10 | 60.00% | USD -105.20 | USD -1,052.00 | USD -1,633.80 | USD -100.60 | USD 63.20 |
| 2:4 | 2024-2025 | 9/9 | 77.78% | USD 585.53 | USD 5,269.80 | USD -775.80 | USD -620.89 | USD 1,274.22 |
| 1:3 | 2018-2021 | 17/17 | 88.24% | USD 377.45 | USD 6,416.60 | USD -645.20 | USD -155.29 | USD 577.94 |
| 1:3 | 2022-2023 | 10/10 | 60.00% | USD -48.10 | USD -481.00 | USD -1,570.20 | USD -50.30 | USD 47.40 |
| 1:3 | 2024-2025 | 9/9 | 88.89% | USD 538.24 | USD 4,844.20 | USD -1,245.20 | USD -291.22 | USD 874.67 |

## Twenty-session hold by era

| Ratio | Era | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Worst trade | Unresolved |
|---|---|---:|---:|---:|---:|---:|---:|
| 1:6 | 2018-2021 | 17/17 | 94.12% | USD 1,420.14 | USD 24,142.30 | USD -2,204.10 | 0 |
| 1:6 | 2022-2023 | 9/10 | 77.78% | USD 1,243.46 | USD 11,191.10 | USD -2,138.10 | 1 |
| 1:6 | 2024-2025 | 8/9 | 87.50% | USD 1,874.15 | USD 14,993.20 | USD -1,370.10 | 1 |
| 4:5 | 2018-2021 | 17/17 | 88.24% | USD 265.54 | USD 4,514.10 | USD -1,894.70 | 0 |
| 4:5 | 2022-2023 | 9/10 | 55.56% | USD 275.97 | USD 2,483.70 | USD -774.70 | 1 |
| 4:5 | 2024-2025 | 8/9 | 62.50% | USD 152.17 | USD 1,217.40 | USD -686.70 | 1 |
| 2:4 | 2018-2021 | 17/17 | 94.12% | USD 555.61 | USD 9,445.40 | USD -1,493.80 | 0 |
| 2:4 | 2022-2023 | 9/10 | 77.78% | USD 508.87 | USD 4,579.80 | USD -327.80 | 1 |
| 2:4 | 2024-2025 | 8/9 | 87.50% | USD 699.45 | USD 5,595.60 | USD -721.80 | 1 |
| 1:3 | 2018-2021 | 17/17 | 94.12% | USD 563.39 | USD 9,577.60 | USD -1,111.20 | 0 |
| 1:3 | 2022-2023 | 9/10 | 77.78% | USD 501.69 | USD 4,515.20 | USD -541.20 | 1 |
| 1:3 | 2024-2025 | 8/9 | 87.50% | USD 723.05 | USD 5,784.40 | USD -613.20 | 1 |

## Interpretation

- The existing sample shows regime dependence: 10-session means turn negative in 2022-2023 across all four ratios.
- Gross-leg attribution is important. If SPY short-put gross gains outweigh negative QQQ long-put P&L, this is economically a short-downside-risk strategy, not a neutral paired hedge.
- Small period samples and retrospective ratio selection prevent this report from establishing robust alpha.
- Next evidential step: freeze a candidate and run prospective paper replay on genuinely new quotes without ratio or exit retuning.

## Input integrity

| Ratio | SHA-256 of trade_episodes.csv | Cohort matches reference |
|---|---|---|
| 1:6 | 17ea6325df2d3ef781b7721a597f0aa0ebfa1cec4b444158d0197181ff926e50 | True |
| 4:5 | effe6c9941905d2607bcd95553c2de0e025839fd1097102650249380b6e5ed38 | True |
| 2:4 | 7f3865c3de853980ec288d9c7655effc4a4e263dc06d0af31e2f1d4fc5c6c057 | True |
| 1:3 | 66310a729cc747073a8c79b72c70699445d2494af63612ba70e541a784d184cf | True |

## Caveats

- In-sample time-sliced audit, not an untouched out-of-sample test.
- Ratios were selected after reviewing the same 2018-2025 sample; positive results do not prove prospective alpha.
- Resolved-only P&L/win rates exclude unresolved rows, reported separately rather than assigned zero.
- Era groups are small and do not correct for serial dependence, overlapping regimes or model selection.
- EOD quotes and displayed-size gates are not confirmed multi-leg fills.
- SPY short-put exposure retains severe downside, assignment and collateral risk.
- Available EOD adverse marks do not capture intraday moves or missing quote periods.
