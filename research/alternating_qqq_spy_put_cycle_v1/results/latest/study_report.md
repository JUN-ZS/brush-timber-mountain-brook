# Alternating SPY / QQQ Short-Put and Opposite-Index Long-Put Cycle

- Sample: 2018-03-01 to 2025-12-12 (1959 common sessions).
- Each cohort: short 6 puts at |Delta| nearest 0.25, long 1 opposite-index put at |Delta| 0.60–0.70 (target 0.65).
- Common expiration required; DTE nearest 21 within 18–24 calendar days.
- Long-put Ask selected closest to 6 x short-put Bid within Delta band; actual entry match reported separately.
- Signal at EOD; entry no earlier than the next common session. New signal every 5 common sessions.

## Arms

| Arm | Entered | Resolved | Win % | Mean/trade | Median/trade | Worst/trade | Ending NAV | CAGR | Max DD | Peak short assignment notional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY_SHORT_QQQ_LONG_only | 391 | 390 | 72.56410256410257 | 18.63076923076922 | 281.4 | -17340.100000000002 | 107688.90 | 0.9562270176945553 | -52.14% | 556800.00 |
| QQQ_SHORT_SPY_LONG_only | 391 | 390 | 71.02564102564102 | 76.38717948717948 | 238.90000000000006 | -8961.1 | 127600.90 | 3.1809195939952017 | -18.00% | 731400.00 |
| SPY_SHORT_QQQ_LONG_only_hold10 | 391 | 389 | 82.0051413881748 | 83.48097686375333 | 526.8999999999995 | -26294.100000000002 | 134128.90 | 3.8444372340628696 | -84.73% | 1071300.00 |
| QQQ_SHORT_SPY_LONG_only_hold10 | 391 | 389 | 81.23393316195373 | 127.58380462724935 | 485.9000000000002 | -27042.1 | 147298.90 | 5.101561746619621 | -30.11% | 1080000.00 |
| alternate_weekly_close | 391 | 390 | 71.28205128205128 | 61.57692307692307 | 258.4000000000001 | -8961.1 | 121824.90 | 2.568689657181489 | -31.46% | 767400.00 |
| alternate_two_week_staggered | 391 | 389 | 81.74807197943444 | 85.58894601542418 | 532.9 | -27042.1 | 132335.90 | 3.665047244086228 | -56.37% | 1024800.00 |

## Interpretation

- alternate_two_week_staggered opens a new opposite-side cohort each week and holds each cohort up to 10 sessions, normally creating two concurrent layers.
- A 1:6 contract ratio is not a hedge ratio. Premium matching does not equalize Dollar Delta, convexity, notional or assignment.
- CAGR/MaxDD use an unconstrained fixed-size P&L ledger on the stated NAV; they are not evidence of broker buying-power feasibility.
- Per-trade episode P&L overlaps; use daily NAV for the portfolio view.
