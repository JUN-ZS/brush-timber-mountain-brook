# QQQ Source IV versus Realized Volatility — V1

**Status:** SOURCE_REPORTED_IV_DIAGNOSTIC_NOT_OPTION_PNL_PROBABILITY; historical EOD source-IV diagnostic, not option strategy P&L.
**Coverage:** 1956/1971 sessions (99.239%), 2018-03-01 to 2025-12-15.
**Median IV:** 20.024%; **median IV−RV20:** 1.461 points; **IV>RV20:** 61.054% of 1936 matched sessions.
Selection is same-day standard QQQ put, 20–40 calendar DTE (target 30), |delta| 0.35–0.65 (target 0.50), valid two-sided quote and positive displayed size. Missing IV is not filled.
Public mirror IV may be midpoint-derived; it is not exchange-authenticated and does not prove a fill.

| Horizon | Entry IV band | N | Median return | P(+3%) | P(+5%) | P(≤−3%) | P(≤−5%) | P(≤−10%) | Absolute move ≥ IV 1σ | Median absolute move / IV 1σ |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | IV_LT20 | 946 | 0.3977% | 2.22% | 0.0% | 4.968% | 0.951% | 0.106% | 25.37% | 0.5825 |
| 3 | IV_20_30 | 774 | 0.5369% | 11.886% | 1.809% | 10.982% | 3.101% | 0.258% | 29.457% | 0.6753 |
| 3 | IV_GTE30 | 233 | 0.3247% | 27.039% | 14.592% | 17.167% | 7.296% | 1.288% | 33.047% | 0.6651 |
| 3 | UNKNOWN | 0 | None% | None% | None% | None% | None% | None% | None% | None |
| 5 | IV_LT20 | 944 | 0.5785% | 8.686% | 0.106% | 7.521% | 2.013% | 0.212% | 26.695% | 0.6208 |
| 5 | IV_20_30 | 774 | 0.7857% | 20.93% | 6.072% | 14.083% | 5.556% | 0.517% | 28.682% | 0.656 |
| 5 | IV_GTE30 | 233 | 0.7249% | 33.906% | 21.459% | 21.888% | 9.442% | 3.004% | 33.476% | 0.692 |
| 5 | UNKNOWN | 0 | None% | None% | None% | None% | None% | None% | None% | None |
| 10 | IV_LT20 | 939 | 1.1441% | 21.299% | 3.727% | 13.738% | 6.603% | 0.426% | 30.671% | 0.6584 |
| 10 | IV_20_30 | 774 | 1.7444% | 33.721% | 16.15% | 18.863% | 12.145% | 1.421% | 29.457% | 0.6859 |
| 10 | IV_GTE30 | 233 | 2.6542% | 45.923% | 30.901% | 24.893% | 15.451% | 5.15% | 24.034% | 0.6669 |
| 10 | UNKNOWN | 0 | None% | None% | None% | None% | None% | None% | None% | None |
| 20 | IV_LT20 | 937 | 2.0467% | 40.128% | 18.463% | 17.609% | 11.206% | 3.308% | 35.112% | 0.7721 |
| 20 | IV_20_30 | 766 | 2.5873% | 47.781% | 32.245% | 25.196% | 16.71% | 4.439% | 28.851% | 0.7377 |
| 20 | IV_GTE30 | 233 | 4.2807% | 57.511% | 46.781% | 20.601% | 15.021% | 3.863% | 24.893% | 0.6947 |
| 20 | UNKNOWN | 0 | None% | None% | None% | None% | None% | None% | None% | None |
| 30 | IV_LT20 | 935 | 2.5632% | 47.273% | 31.765% | 18.824% | 11.658% | 3.85% | 35.08% | 0.7658 |
| 30 | IV_20_30 | 758 | 3.5789% | 52.639% | 44.723% | 21.108% | 17.942% | 8.179% | 30.871% | 0.7659 |
| 30 | IV_GTE30 | 233 | 5.8106% | 59.657% | 52.361% | 16.738% | 11.159% | 3.863% | 27.468% | 0.6654 |
| 30 | UNKNOWN | 0 | None% | None% | None% | None% | None% | None% | None% | None |

## Limits

- Forward windows overlap; these are historical descriptive frequencies, not independent-trial forecasts.
- The source-reported IV is not exchange-authenticated and may be derived from the same quote marks/midpoint.
- Annualized IV times sqrt(h/252) is a reference one-sigma move, not a probability the option strategy wins.
