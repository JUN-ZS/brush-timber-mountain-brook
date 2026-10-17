# QQQ Option Shortlist — Temporal and Friction Audit V1

**Status: research only. No live orders, HUB action changes, or Frozen Original Hybrid changes.**

- Source run: 39006048516; tested SHA: 7f78073d27d65018b4700c0be2ceeb45e4754d0c.
- Source window: ['2018-03-01', '2025-12-15']; sessions: 1960; signal events: 28.
- Trade ledger SHA-256: a9ee12ab3a86d5c5f4e8e7c06574a809711c1c7252ab6d7fa358e0caa5e0f5e9.
- Evidence: OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS.

## Same-event fixed-horizon outcomes

BASE is the original quote-side replay. ZERO and STRESS are friction adjustments to the same episodes, not separate fill simulations.

| Strategy | Resolved | BASE win % | BASE mean USD | STRESS win % | STRESS mean USD | STRESS PF | Worst STRESS USD | 1% budget-sizeable events | 2% budget-sizeable events |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CALL_DEBIT_50D_10D | 28 | 57.1429 | 92.72 | 57.1429 | 72.72 | 1.30354 | -992.6 | 7 | 22 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 24 | 58.3333 | 49.02 | 54.1667 | 19.02 | 1.07555 | -1014.9 | 3 | 18 |
| PUT_SHORT_HEAVY_1x1 | 28 | 25.0 | -154.28 | 25.0 | -174.28 | 0.23832 | -598.6 | 27 | 28 |
| PUT_SHORT_HEAVY_1x4 | 28 | 53.5714 | -15.04 | 46.4286 | -65.04 | 0.30852 | -813.5 | 0 | 0 |
| PUT_SHORT_HEAVY_1x5 | 28 | 78.5714 | 31.38 | 42.8571 | -28.62 | 0.72055 | -1286.8 | 0 | 0 |
| PUT_SHORT_HEAVY_1x6 | 28 | 78.5714 | 77.79 | 60.7143 | 7.79 | 1.06317 | -1760.1 | 0 | 0 |
| PUT_LONG_HEAVY_2x1 | 28 | 25.0 | -354.97 | 25.0 | -384.97 | 0.26255 | -1405.9 | 7 | 24 |

## Paired test: does the extra LONG PUT pay for itself?

Only dates where call-only and call-plus-put rows used identical two call contracts are included.

| Period | Cost case | Exact pairs | Mean P&L delta (combo − call) | Combo higher-P&L count | Mean MAE delta (positive is less adverse) | MAE improved count |
|---|---|---:|---:|---:|---:|---:|
| FULL | BASE | 24 | -71.59 | 3 | 29.07 | 12 |
| FULL | STRESS | 24 | -81.59 | 3 | 19.07 | 11 |
| 2018-2022 | BASE | 15 | -68.63 | 2 | 18.1 | 7 |
| 2018-2022 | STRESS | 15 | -78.63 | 2 | 8.1 | 6 |
| 2023-2025 | BASE | 9 | -76.52 | 1 | 47.37 | 5 |
| 2023-2025 | STRESS | 9 | -86.52 | 1 | 37.37 | 5 |

## Decision readout

- CALL debit stress mean: USD 72.72 per event across 28 events. At least one unit fit the 1% terminal-tail budget on 7/28 events and the 2% budget on 22/28.
- Time dependence: CALL debit stress mean was USD 1.66 per event in 2018–2022 and USD 222.73 in 2023–2025. The later segment has 9 events and is not a virgin holdout.
- SHORT-heavy PUT ratio: 1x5 stress mean USD -28.62 and 1x6 stress mean USD 7.79. Both have zero complete units inside the 0.5%, 1%, and 2% NAV terminal-tail budgets on every observed episode.
- Extra LONG PUT remains a protection hypothesis only. Do not auto-add it; weigh incremental P&L cost against paired improvement in adverse marks.

## Interpretation limits

- Episode statistics are not a continuously compounded account CAGR/MaxDD.
- Risk-unit counts use BASE entry terminal-payoff arithmetic plus entry-side displayed depth; broker margin, exit depth and interim liquidation limits are not proved.
- 2018-2022 versus 2023-2025 is a descriptive split after exploratory full-sample review, not an untouched holdout.
- The public historical option chain ends on 2025-12-15; no option outcomes are available in this audit after that date.
- No portfolio compounding, total account CAGR, or account MaxDD is inferred from these isolated fixed-horizon episodes.
- Entry displayed size does not prove sufficient exit size; terminal payoff does not bound interim liquidation or broker margin.
