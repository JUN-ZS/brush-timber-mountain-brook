# SPY weekly -1% trigger + per-trade virtual -10% entry-price floor

Window: 2018-03-01 to 2025-12-15 (7.792 years). Trigger is a downward crossing of SPY rolling 5-common-session close return through -1%; no correlation gate.

Each primary conditional trade must have SPY remain at or above 90% of its own entry-date close for the whole entry-to-exit path. This is ex-post path conditioning, not an executable stop or an entry filter.

## Trigger and path coverage

| Ratio | Signals | Entered | Skipped | Resolved | Unresolved | Breached SPY floor | Pass virtual lock |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | 138 | 138 | 0 | 138 | 0 | 1 | 137 |
| 1:6 | 138 | 138 | 0 | 138 | 0 | 1 | 137 |
| 2:6 half-premium | 138 | 138 | 0 | 138 | 0 | 1 | 137 |
| 2:6 same contract | 138 | 138 | 0 | 138 | 0 | 1 | 137 |

## P&L comparison

P&L includes the existing replay costs. 'Annual-average episode sum' is conditional episode P&L divided by the complete study period; it is not an account return or CAGR. Because cohorts overlap, sums cannot be compounded as account NAV.

| Ratio | Condition | N resolved | Sum episode P&L | Mean / episode | Median / episode | Win rate | Profit factor | Worst episode |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | all_resolved_trades | 138 | USD -13,455.60 | USD -97.50 | USD -47.70 | 41.30% | 0.6506 | USD -5,962.20 |
| 1:3 | virtual_lock_10pct_pass | 137 | USD -11,086.40 | USD -80.92 | USD -47.20 | 41.61% | 0.6932 | USD -5,962.20 |
| 1:6 | all_resolved_trades | 138 | USD 846.20 | USD 6.13 | USD 271.40 | 77.54% | 1.0113 | USD -15,422.10 |
| 1:6 | virtual_lock_10pct_pass | 137 | USD 8,013.30 | USD 58.49 | USD 273.90 | 78.10% | 1.1182 | USD -15,422.10 |
| 2:6 half-premium | all_resolved_trades | 138 | USD -3,139.20 | USD -22.75 | USD 221.60 | 75.36% | 0.9506 | USD -12,850.40 |
| 2:6 half-premium | virtual_lock_10pct_pass | 137 | USD 3,327.20 | USD 24.29 | USD 223.60 | 75.91% | 1.0584 | USD -12,850.40 |
| 2:6 same contract | all_resolved_trades | 138 | USD -25,635.20 | USD -185.76 | USD -95.40 | 41.30% | 0.6632 | USD -11,924.40 |
| 2:6 same contract | virtual_lock_10pct_pass | 137 | USD -20,896.80 | USD -152.53 | USD -94.40 | 41.61% | 0.7072 | USD -11,924.40 |

## Interpretation constraints

- The key question is conditional P&L for the trades whose SPY path did not breach -10% from the individual entry close; the 'all resolved' arm is shown only as a baseline.
- The virtual lock excludes paths that breached -10%; it does not simulate a stop-out, and it does not guarantee the option strategy itself loses no more than 10%.
- The option positions are QQQ puts versus SPY short puts; a 10% SPY floor is not a loss cap on the option portfolio.
- Quotes, contract availability and displayed size are historical snapshots, not proof of executable multi-leg fills.

Artifacts: summary.json and episode_classification.csv.
