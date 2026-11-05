# Alternating SPY / QQQ Short-Put and Opposite-Index Long-Put Cycle

- Sample: 2018-03-01 to 2025-12-12 (1959 common sessions).
- Each cohort: short 6 puts at |Delta| nearest 0.25, long 1 opposite-index put at |Delta| 0.60–0.70 (target 0.65).
- Common expiration required; DTE nearest 21 within 18–24 calendar days.
- HARD ENTRY RULE: 1 x opposite-index long-put Ask must equal 6 x short-put Bid to $0.00 gross opening premium; otherwise that scheduled cohort is skipped.
- Pair is reselected on the next common-session EOD quote snapshot and entered from the same snapshot; new schedule signal every 5 common sessions.
- Zero gross opening premium excludes commissions and slippage; bid/ask spreads and all exit costs remain in P&L.

## Arms

| Arm | Entered | Resolved | Win % | Mean/trade | Median/trade | Worst/trade | Ending NAV | CAGR | Max DD | Peak short assignment notional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY_SHORT_QQQ_LONG_only | 0 | 0 | — | — | — | — | 100000.00 | 0.0 | 0.00% | 0.00 |
| QQQ_SHORT_SPY_LONG_only | 1 | 1 | 100.0 | 150.90000000000015 | 150.90000000000015 | 150.90000000000015 | 100150.90 | 0.019373906606423574 | -0.20% | 120000.00 |
| SPY_SHORT_QQQ_LONG_only_hold10 | 0 | 0 | — | — | — | — | 100000.00 | 0.0 | 0.00% | 0.00 |
| QQQ_SHORT_SPY_LONG_only_hold10 | 1 | 1 | 0.0 | -5.099999999999895 | -5.099999999999895 | -5.099999999999895 | 99994.90 | -0.0006552291239914076 | -0.20% | 120000.00 |
| alternate_weekly_close | 1 | 1 | 100.0 | 150.90000000000015 | 150.90000000000015 | 150.90000000000015 | 100150.90 | 0.019373906606423574 | -0.20% | 120000.00 |
| alternate_two_week_staggered | 1 | 1 | 0.0 | -5.099999999999895 | -5.099999999999895 | -5.099999999999895 | 99994.90 | -0.0006552291239914076 | -0.20% | 120000.00 |

## Interpretation

- alternate_two_week_staggered opens a new opposite-side cohort each week and holds each cohort up to 10 sessions, normally creating two concurrent layers.
- A 1:6 contract ratio is not a hedge ratio. Exact premium parity does not equalize Dollar Delta, convexity, notional or assignment.
- CAGR/MaxDD use an unconstrained fixed-size P&L ledger on the stated NAV; they are not evidence of broker buying-power feasibility.
- Per-trade episode P&L overlaps; use daily NAV for the portfolio view.
