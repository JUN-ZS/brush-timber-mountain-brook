# QQQ Option Shortlist Validation V1

Evidence: observed historical EOD quotes with derived quote-side replay; not confirmed fills.

## Locked cohort

- Source run: 39003581461; locked trade input Git blob SHA-1: ba5fc1fa0fabf8cd914735503905cac6ee1f631e.
- Unique signal dates: 28; recorded event/strategy rows: 387; resolved rows: 387.
- Option chain ends 2025-12-15. The later 2023-2025 split has already been inspected and is not a virgin holdout.

## Full-period BASE results and 95% Wilson uncertainty

| Strategy | N | Win % (95% Wilson interval) | Mean P&L/unit | PF | Worst P&L | 1% NAV-tail-budget-sizeable episodes |
|---|---:|---:|---:|---:|---:|---:|
| CALL_DEBIT_50D_10D | 28 | 57.1429% (39.1–73.5%) | 92.72 | 1.40138 | -972.6 | 7 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 24 | 58.3333% (38.8–75.5%) | 49.02 | 1.20505 | -984.9 | 3 |
| PUT_SHORT_HEAVY_1x4 | 28 | 53.5714% (35.8–70.5%) | -15.04 | 0.77929 | -763.5 | 0 |
| PUT_SHORT_HEAVY_1x5 | 28 | 78.5714% (60.5–89.8%) | 31.38 | 1.41137 | -1226.8 | 0 |
| PUT_SHORT_HEAVY_1x6 | 28 | 78.5714% (60.5–89.8%) | 77.79 | 1.77115 | -1690.1 | 0 |
| PUT_LONG_HEAVY_1x1 | 28 | 25.0% (12.7–43.4%) | -154.28 | 0.27842 | -578.6 | 27 |
| PUT_LONG_HEAVY_2x1 | 28 | 25.0% (12.7–43.4%) | -354.97 | 0.28939 | -1375.9 | 7 |

## Paired call debit versus call debit plus long put

| Cost case | Matched events | Hedge higher P&L | Mean hedge-minus-call | Median difference | Events with less-adverse MAE | Mean MAE delta |
|---|---:|---:|---:|---:|---:|---:|
| ZERO_FRICTION | 24 | 4 (16.67%) | -60.29 | -77.0 | 12 | 29.07 |
| BASE | 24 | 3 (12.5%) | -71.59 | -88.3 | 12 | 29.07 |
| STRESS | 24 | 3 (12.5%) | -81.59 | -98.3 | 12 | 29.07 |

## Interpretation

- The CALL debit vertical is a candidate for further research only: positive event-average P&L is not a compounded return, and only a minority of entries fit the 1% NAV terminal-loss budget under the existing observed entry-side sizing.
- The added long put did not improve matched P&L consistently; do not include it by default. Its MAE improvement was mixed rather than universal.
- PUT short-heavy 1:5 and 1:6 have high single-unit win rates in this small cohort, but their QQQ=0 terminal losses leave zero whole units inside the 0.5%, 1%, and 2% NAV tail budgets for the recorded entries. The apparent expectancy is therefore not deployable under the stated tail budget.
- Long-heavy PUT ratios were net negative in this selected reversal cohort.
- The cost/time split is descriptive; 9 later-period events are too few to confirm persistence, and this period has already been inspected.
- Episode win rates and sums are one unit per event—not portfolio CAGR/MaxDD. Historical EOD marks are not authenticated fills; margin, assignment, intraday liquidation and multi-leg execution sequencing remain unmodelled.

## Next boundary

- Freeze the signal and candidate-selection rules. Do not tune the 2.1% threshold using these same results.
- A genuine confirmatory step needs timestamped quote captures after 2025-12-15, logged before the subsequent marks occur. If no freely accessible archival source exists, collect prospective paper data rather than substituting modeled option prices.
- No live HUB policy or broker-order path is modified by this validation.
