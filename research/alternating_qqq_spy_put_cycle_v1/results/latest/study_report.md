# Alternating SPY / QQQ Short-Put and Opposite-Index Long-Put Cycle

- Sample: 2018-03-01 to 2025-12-12 (1959 common sessions).
- Each cohort: short 6 puts at |Delta| nearest 0.25, long 1 opposite-index put at |Delta| 0.60–0.70 (target 0.65).
- Common expiration required; DTE nearest 21 within 18–24 calendar days.
- PREMIUM BALANCE IS SOFT ONLY: 1 x opposite-index long-put Ask is targeted near 6 x short-put Bid (e.g. about $24 versus 6 x about $4), but exact equality is not required.
- ENTRY IS UNCONDITIONAL ON PREMIUM PARITY: every scheduled slot enters the selected common-expiry / DTE / Delta pair when valid entry quotes and displayed size are present; any debit or credit is recorded, not skipped.
- Pair is reselected on the next common-session EOD quote snapshot and entered from the same snapshot; new signal every 5 common sessions.
- P&L includes the entry debit/credit through the actual opening and closing leg prices, plus estimated round-trip slippage and commissions.

## Arms

| Arm | Entered | Resolved | Win % | Mean/trade | Median/trade | Worst/trade | Ending NAV | CAGR | Max DD | Peak short assignment notional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY_SHORT_QQQ_LONG_only | 389 | 388 | 72.42268041237114 | -34.306185567010324 | 319.8999999999998 | -16179.1 | 86962.10 | -1.7787360310499434 | -44.98% | 699900.00 |
| QQQ_SHORT_SPY_LONG_only | 389 | 388 | 70.10309278350516 | -25.97628865979381 | 262.8999999999999 | -16716.100000000002 | 87723.10 | -1.6687282858280694 | -31.42% | 721200.00 |
| SPY_SHORT_QQQ_LONG_only_hold10 | 389 | 387 | 83.72093023255815 | 86.52015503875968 | 583.9 | -20297.1 | 135042.10 | 3.935001152849682 | -76.50% | 943200.00 |
| QQQ_SHORT_SPY_LONG_only_hold10 | 389 | 387 | 83.20413436692506 | 95.23591731266153 | 617.9000000000002 | -27349.1 | 134451.10 | 3.8764516518950076 | -43.07% | 896400.00 |
| alternate_weekly_close | 389 | 388 | 71.3917525773196 | -4.527835051546399 | 279.4000000000001 | -7824.1 | 96045.10 | -0.5170785851691173 | -30.83% | 628800.00 |
| alternate_two_week_staggered | 389 | 387 | 82.68733850129199 | 63.19974160206719 | 602.9000000000002 | -27349.1 | 123546.10 | 2.7537293281523656 | -54.58% | 900000.00 |

## Interpretation

- alternate_two_week_staggered opens a new opposite-side cohort each week and holds each cohort up to 10 sessions, normally creating two concurrent layers.
- A 1:6 contract ratio is not a hedge ratio. Approximate premium-size matching does not equalize Dollar Delta, convexity, notional or assignment.
- CAGR/MaxDD use an unconstrained fixed-size P&L ledger on the stated NAV; they are not evidence of broker buying-power feasibility.
- Per-trade episode P&L overlaps; use daily NAV for the portfolio view.
