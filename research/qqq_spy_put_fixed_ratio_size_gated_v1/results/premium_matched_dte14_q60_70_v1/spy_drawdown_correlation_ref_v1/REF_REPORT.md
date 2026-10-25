# SPY drawdown x QQQ correlation — historical REF condition replay

Window: 2018-03-01 to 2025-12-15 (7.792 years); premium-matched DTE14; HOLD_20_OR_DTE_LE_7; 391 resolved cohorts per ratio.

## Correlation

- Full-period Pearson correlation of daily close returns on common QQQ/SPY sessions: **0.9360**.
- Entry correlation filter: prior 60 common-session daily returns, ending before entry; strictly positive.

## Conditional results — base strategy P&L, no TAIL

Annual-average episode sum = qualifying P&L divided by the full 7.792-year sample; this is NOT CAGR or a capital-constrained annual return.

| Ratio | Condition | N | Sum P&L | Mean / episode | Median / episode | Win rate | Worst | Annual-average episode sum |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | all_resolved_baseline | 391 | USD -33,466.20 | USD -85.59 | USD -10.20 | 49.10% | USD -10,629.20 | USD -4,294.90 |
| 1:3 | positive_prior_60d_correlation_only | 391 | USD -33,466.20 | USD -85.59 | USD -10.20 | 49.10% | USD -10,629.20 | USD -4,294.90 |
| 1:3 | entry_SPY_ATH_drawdown_not_below_minus_10pct_AND_corr60_positive | 303 | USD -15,398.60 | USD -50.82 | USD -17.20 | 47.19% | USD -8,355.20 | USD -1,976.19 |
| 1:3 | whole_episode_SPY_ATH_drawdown_not_below_minus_10pct_AND_corr60_positive | 287 | USD -1,383.40 | USD -4.82 | USD -17.20 | 47.04% | USD -2,675.20 | USD -177.54 |
| 1:3 | whole_episode_SPY_return_from_entry_not_below_minus_10pct_AND_corr60_positive | 387 | USD -6,180.40 | USD -15.97 | USD -4.20 | 49.61% | USD -4,114.20 | USD -793.16 |
| 1:3 | entry_SPY_ATH_drawdown_not_below_minus_15pct_AND_corr60_positive | 346 | USD -33,700.20 | USD -97.40 | USD -13.20 | 48.27% | USD -10,629.20 | USD -4,324.93 |
| 1:3 | whole_episode_SPY_ATH_drawdown_not_below_minus_15pct_AND_corr60_positive | 331 | USD -5,662.20 | USD -17.11 | USD -13.20 | 48.04% | USD -4,683.20 | USD -726.66 |
| 1:3 | whole_episode_SPY_return_from_entry_not_below_minus_15pct_AND_corr60_positive | 390 | USD -22,837.00 | USD -58.56 | USD -7.20 | 49.23% | USD -8,355.20 | USD -2,930.80 |
| 1:6 | all_resolved_baseline | 391 | USD -16,768.10 | USD -42.89 | USD 286.90 | 75.45% | USD -26,768.10 | USD -2,151.94 |
| 1:6 | positive_prior_60d_correlation_only | 391 | USD -16,768.10 | USD -42.89 | USD 286.90 | 75.45% | USD -26,768.10 | USD -2,151.94 |
| 1:6 | entry_SPY_ATH_drawdown_not_below_minus_10pct_AND_corr60_positive | 303 | USD 6,794.70 | USD 22.42 | USD 250.90 | 75.58% | USD -21,700.10 | USD 872.00 |
| 1:6 | whole_episode_SPY_ATH_drawdown_not_below_minus_10pct_AND_corr60_positive | 287 | USD 47,588.30 | USD 165.81 | USD 260.90 | 77.70% | USD -6,324.10 | USD 6,107.26 |
| 1:6 | whole_episode_SPY_return_from_entry_not_below_minus_10pct_AND_corr60_positive | 387 | USD 50,341.30 | USD 130.08 | USD 291.90 | 76.23% | USD -10,439.10 | USD 6,460.57 |
| 1:6 | entry_SPY_ATH_drawdown_not_below_minus_15pct_AND_corr60_positive | 346 | USD -33,125.60 | USD -95.74 | USD 259.90 | 74.86% | USD -26,768.10 | USD -4,251.19 |
| 1:6 | whole_episode_SPY_ATH_drawdown_not_below_minus_15pct_AND_corr60_positive | 331 | USD 41,999.90 | USD 126.89 | USD 263.90 | 76.13% | USD -11,059.10 | USD 5,390.07 |
| 1:6 | whole_episode_SPY_return_from_entry_not_below_minus_15pct_AND_corr60_positive | 390 | USD 10,000.00 | USD 25.64 | USD 288.40 | 75.64% | USD -21,700.10 | USD 1,283.35 |

## Definitions

- Entry ATH gate: at entry, SPY is no more than 10%/15% below its running all-history close high. This is the implementable state filter.
- Whole-episode ATH gate: every close during a trade remains above the threshold relative to SPY's all-history high. Ex-post only.
- Whole-episode entry-return gate: SPY never closes 10%/15% below the cohort's entry close through exit. Ex-post only.
- ATH starts at the earliest source date in 1999 to avoid resetting the high-water mark at the 2018 start. Intraday breaches may be missed.
- Episodes overlap. Their P&L sum is not compounded account P&L; account CAGR requires daily NAV, capital sizing, margin and assignment handling.
- Rolling correlation is a lagged condition, not causation or a guarantee of future correlation.

## Outputs

- episode_classification.csv: each cohort's entry/exit path, SPY drawdown and lagged correlation flags.
- summary.json: aggregate results and data-source identities. Price files are checked against pinned Git blob hashes.
