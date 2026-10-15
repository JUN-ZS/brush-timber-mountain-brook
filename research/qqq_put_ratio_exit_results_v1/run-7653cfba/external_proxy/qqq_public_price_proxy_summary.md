# QQQ public-price proxy supplement

**Status: price-path supplement only. No option strategy P&L is estimated for dates without an option chain.**

- Yahoo daily Close window: 2018-03-01 to 2026-10-15 (2169 observations).
- Option mirror boundary: 2025-12-15; use the post-boundary probability rows as an underlying-only sensitivity, not an option replay.
- Broad-market VIX proxy status: OK_YAHOO_FALLBACK; source: Yahoo Finance chart API ^VIX daily Close. This is not QQQ option IV/skew.
- Nasdaq-100 VXN proxy status: OK_YAHOO; source: Yahoo Finance chart API ^VXN daily Close. This is not a QQQ option IV/skew surface.
- Recent peak-to-last (up to 7 close-to-close sessions): -4.4711%.

## Downside frequencies by period

| Window | State | Sessions | N | P(down >=3%) | P(down >=5%) | P(down >=10%) | P05 return | Median | P95 return | Nominal 95% interval for down >=5% |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | ALL | 5 | 1955 | 11.8159% | 4.2967% | 0.665% | -4.6824% | 0.6606% | 4.998% | 3.4838%–5.2888% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_25_35 | 5 | 285 | 17.8947% | 8.0702% | 1.7544% | -6.1828% | 0.7287% | 6.9857% | 5.4376%–11.8181% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_GTE35 | 5 | 60 | 15.0% | 10.0% | 6.6667% | -10.7638% | 3.2261% | 10.0159% | 4.6643%–20.1495% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_20_30 | 5 | 895 | 13.5196% | 4.4693% | 0.3352% | -4.7874% | 0.6234% | 4.7937% | 3.2991%–6.0286% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_30_40 | 5 | 314 | 19.1083% | 8.2803% | 1.9108% | -6.3264% | 0.536% | 7.2243% | 5.7131%–11.8558% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_GTE40 | 5 | 48 | 16.6667% | 14.5833% | 8.3333% | -11.2509% | 2.312% | 10.0159% | 7.2482%–27.1672% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | ALL | 10 | 1950 | 17.1282% | 9.8974% | 1.3846% | -6.9463% | 1.3761% | 6.5905% | 8.6498%–11.3028% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_25_35 | 10 | 285 | 21.4035% | 12.6316% | 2.807% | -7.7036% | 1.9559% | 8.1675% | 9.2654%–16.9918% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_GTE35 | 10 | 60 | 15.0% | 13.3333% | 10.0% | -13.0514% | 5.1534% | 15.2646% | 6.9141%–24.1652% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_20_30 | 10 | 891 | 18.6308% | 10.8866% | 1.0101% | -6.992% | 1.4733% | 6.4509% | 9.0069%–13.1022% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_30_40 | 10 | 314 | 23.5669% | 14.6497% | 3.1847% | -7.8672% | 1.8992% | 8.1675% | 11.1661%–18.9877% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_GTE40 | 10 | 48 | 22.9167% | 18.75% | 10.4167% | -13.7716% | 4.6691% | 15.7411% | 10.1914%–31.9399% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | ALL | 20 | 1940 | 20.9794% | 13.8144% | 3.8144% | -9.1083% | 2.3931% | 9.8603% | 12.3504%–15.4215% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_25_35 | 20 | 284 | 20.0704% | 14.4366% | 4.5775% | -9.8321% | 3.9183% | 11.7464% | 10.8234%–18.9991% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_GTE35 | 20 | 60 | 10.0% | 8.3333% | 3.3333% | -9.1083% | 10.7228% | 20.7531% | 3.612%–18.0689% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_20_30 | 20 | 883 | 23.8958% | 15.1755% | 3.9638% | -9.3422% | 2.1101% | 8.9438% | 12.9602%–17.6925% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_30_40 | 20 | 312 | 23.0769% | 16.6667% | 4.4872% | -9.4942% | 3.9183% | 12.7022% | 12.9421%–21.2021% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_GTE40 | 20 | 48 | 12.5% | 8.3333% | 4.1667% | -9.9611% | 10.1333% | 21.1809% | 3.2884%–19.5533% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | ALL | 45 | 1915 | 19.2689% | 15.1436% | 8.1462% | -12.7006% | 4.4438% | 15.5659% | 13.6079%–16.8188% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_25_35 | 45 | 283 | 19.788% | 15.9011% | 5.3004% | -10.2255% | 5.4691% | 18.9001% | 12.1013%–20.6142% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VIX_GTE35 | 45 | 60 | 3.3333% | 3.3333% | 0.0% | 3.4526% | 18.2437% | 32.6826% | 0.9189%–11.3638% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_20_30 | 45 | 858 | 18.7646% | 15.8508% | 10.4895% | -14.4164% | 5.5796% | 14.6164% | 13.56%–18.4461% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_30_40 | 45 | 312 | 22.1154% | 17.3077% | 5.7692% | -10.9326% | 4.9225% | 19.6925% | 13.5142%–21.8964% |
| YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15 | VXN_GTE40 | 45 | 48 | 2.0833% | 0.0% | 0.0% | -0.8361% | 18.2437% | 33.9988% | 0.0%–7.41% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | ALL | 5 | 204 | 9.8039% | 2.451% | 0.0% | -4.0793% | 0.2255% | 5.1659% | 1.0514%–5.6083% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VIX_25_35 | 5 | 14 | 14.2857% | 7.1429% | 0.0% | -3.3467% | -1.0054% | 5.4292% | 1.2722%–31.4687% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_20_30 | 5 | 178 | 10.6742% | 2.809% | 0.0% | -4.1598% | 0.1087% | 5.0931% | 1.2057%–6.4062% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_30_40 | 5 | 11 | 0.0% | 0.0% | 0.0% | -1.0054% | 3.1878% | 8.3977% | 0.0%–25.8833% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | ALL | 10 | 199 | 11.5578% | 2.5126% | 0.0% | -3.9672% | 0.5267% | 8.0324% | 1.0779%–5.7459% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VIX_25_35 | 10 | 14 | 21.4286% | 7.1429% | 0.0% | -3.9296% | 1.1064% | 10.4335% | 1.2722%–31.4687% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_20_30 | 10 | 173 | 13.2948% | 2.8902% | 0.0% | -4.1616% | 0.3798% | 7.5868% | 1.2407%–6.5863% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_30_40 | 10 | 11 | 0.0% | 0.0% | 0.0% | -2.9496% | 1.7815% | 12.5958% | 0.0%–25.8833% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | ALL | 20 | 189 | 17.4603% | 3.7037% | 0.5291% | -4.3938% | 0.4556% | 14.3381% | 1.8055%–7.4464% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VIX_25_35 | 20 | 14 | 7.1429% | 0.0% | 0.0% | -1.8758% | 10.8196% | 17.7814% | 0.0%–21.5311% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_20_30 | 20 | 164 | 18.9024% | 4.2683% | 0.6098% | -4.3938% | 0.5217% | 14.2784% | 2.0827%–8.5472% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_30_40 | 20 | 11 | 18.1818% | 0.0% | 0.0% | -4.4878% | -0.7502% | 18.0685% | 0.0%–25.8833% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | ALL | 45 | 164 | 20.122% | 10.3659% | 0.6098% | -6.3989% | 3.1083% | 22.4093% | 6.5732%–15.9728% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VIX_25_35 | 45 | 14 | 0.0% | 0.0% | 0.0% | 17.8562% | 24.0561% | 32.6318% | 0.0%–21.5311% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_20_30 | 45 | 141 | 19.8582% | 11.3475% | 0.7092% | -6.5027% | 3.757% | 21.7536% | 7.1066%–17.6387% |
| YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15 | VXN_30_40 | 45 | 11 | 0.0% | 0.0% | 0.0% | -0.3195% | 1.8991% | 33.3041% | 0.0%–25.8833% |

## Data boundaries / use

- This supplement intentionally does not extend option-strategy P&L. A QQQ price down-move is not the probability of a particular put ratio losing money.
- A current-market observation can inform a stress scenario, but without QQQ option bid/ask and IV/skew on the same decision dates it cannot recreate fills, strategy gamma/vega, or margin actions.
- Any unavailable Yahoo data blocks this external supplement; it must not be silently substituted with zeros or forward-filled prices.
- All price-frequency estimates are empirical overlapping windows; non-overlap ranges are sensitivity checks, not independent-trial confidence intervals.
