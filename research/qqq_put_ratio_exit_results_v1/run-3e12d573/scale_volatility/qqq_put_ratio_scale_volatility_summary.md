# QQQ Put Ratio: scale × exit × volatility/time

Status: RESEARCH DIAGNOSTIC ONLY; deployment remains BLOCKED.
Underlying sample: 2018-03-01 to 2025-12-15; valid closes 1960/1960.
Option cohort: 62 non-overlapping episodes; latest verified chain date 2025-12-15. Eleven expected option sessions through 2025-12-31 remain uncovered.
NAV-relative triggers: $100,000 = $500/$1,000/$2,000; $1,000,000 = $5,000/$10,000/$20,000 for 0.5/1/2%. A fixed $1,000 is not an invariant rule.

## QQQ price-move frequencies — not option-profit probabilities

| State | Sessions | N | P(up) | P(drop >=3%) | P(drop >=5%) | Nominal Wilson 95% for drop >=5% | P(drop >=10%) | P(up >=5%) | P05 | Median | P95 | sqrt-time ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 1 | 1959 | 56.1001% | 3.0628% | 0.4594% | 0.2419%–0.8709% | 0.051% | 0.5105% | -2.4747% | 0.1287% | 2.2351% | 1.3036 |
| RV20_15_25 | 1 | 802 | 57.1072% | 1.3716% | 0.2494% | 0.0684%–0.9047% | 0.0% | 0.0% | -2.0616% | 0.1711% | 2.1339% | 1.0484 |
| RV20_25_35 | 1 | 382 | 50.5236% | 5.7592% | 0.7853% | 0.2674%–2.2832% | 0.0% | 0.7853% | -3.0534% | 0.0303% | 3.0601% | 1.011 |
| RV20_GTE35 | 1 | 170 | 54.7059% | 11.7647% | 2.3529% | 0.9187%–5.8929% | 0.5882% | 4.1176% | -4.2489% | 0.1297% | 4.3491% | 1.151 |
| RV20_LT15 | 1 | 585 | 58.9744% | 1.0256% | 0.0% | 0.0%–0.6524% | 0.0% | 0.0% | -1.6451% | 0.121% | 1.3247% | 1.28 |
| ALL | 3 | 1957 | 58.2524% | 8.8401% | 2.5549% | 1.9433%–3.3524% | 0.3066% | 2.4527% | -3.7912% | 0.414% | 3.7732% | 1.2096 |
| RV20_15_25 | 3 | 800 | 60.25% | 7.25% | 1.5% | 0.8601%–2.6034% | 0.125% | 0.875% | -3.365% | 0.4628% | 3.592% | 1.0537 |
| RV20_25_35 | 3 | 382 | 50.2618% | 16.2304% | 5.2356% | 3.4145%–7.9481% | 0.5236% | 6.0209% | -5.021% | 0.0072% | 5.2759% | 0.975 |
| RV20_GTE35 | 3 | 170 | 59.4118% | 14.7059% | 8.2353% | 4.9688%–13.3476% | 1.7647% | 10.5882% | -6.2809% | 0.682% | 6.4744% | 0.927 |
| RV20_LT15 | 3 | 585 | 61.1966% | 4.6154% | 0.5128% | 0.1746%–1.4968% | 0.0% | 0.0% | -2.8083% | 0.4251% | 2.4265% | 1.2265 |
| ALL | 5 | 1955 | 60.2046% | 11.8159% | 4.2967% | 3.4838%–5.2888% | 0.665% | 5.0128% | -4.6824% | 0.6606% | 4.998% | 1.1722 |
| RV20_15_25 | 5 | 798 | 62.6566% | 10.401% | 3.5088% | 2.4386%–5.0244% | 0.3759% | 3.7594% | -4.5218% | 0.7508% | 4.7723% | 1.0619 |
| RV20_25_35 | 5 | 382 | 51.5707% | 22.2513% | 7.8534% | 5.5562%–10.9898% | 0.5236% | 9.6859% | -5.9118% | 0.1079% | 6.3529% | 0.9151 |
| RV20_GTE35 | 5 | 170 | 62.3529% | 15.2941% | 9.4118% | 5.8764%–14.7409% | 4.7059% | 18.2353% | -9.538% | 0.9514% | 7.9834% | 0.8847 |
| RV20_LT15 | 5 | 585 | 62.5641% | 5.2991% | 1.0256% | 0.4709%–2.2194% | 0.0% | 0.0% | -3.0544% | 0.6336% | 3.2889% | 1.1731 |
| ALL | 10 | 1950 | 64.2564% | 17.1282% | 9.8974% | 8.6498%–11.3028% | 1.3846% | 11.8974% | -6.9463% | 1.3761% | 6.5905% | 1.1512 |
| RV20_15_25 | 10 | 793 | 68.7264% | 14.7541% | 8.575% | 6.8204%–10.729% | 0.8827% | 10.5927% | -6.6937% | 1.6601% | 6.2888% | 1.024 |
| RV20_25_35 | 10 | 382 | 50.5236% | 31.1518% | 19.6335% | 15.9608%–23.9109% | 2.356% | 18.5864% | -8.5509% | 0.241% | 7.8546% | 0.9159 |
| RV20_GTE35 | 10 | 170 | 70.5882% | 16.4706% | 13.5294% | 9.1874%–19.4833% | 6.4706% | 32.3529% | -10.5002% | 2.9475% | 10.0219% | 0.8091 |
| RV20_LT15 | 10 | 585 | 66.8376% | 10.0855% | 3.4188% | 2.2239%–5.2215% | 0.0% | 3.7607% | -4.4036% | 1.2622% | 4.6825% | 1.1795 |
| ALL | 20 | 1940 | 66.9588% | 20.9794% | 13.8144% | 12.3504%–15.4215% | 3.8144% | 27.3196% | -9.1083% | 2.3931% | 9.8603% | 1.147 |
| RV20_15_25 | 20 | 783 | 69.4764% | 17.7522% | 10.3448% | 8.4017%–12.6751% | 3.4483% | 27.5862% | -7.6895% | 2.7086% | 9.3169% | 1.1155 |
| RV20_25_35 | 20 | 382 | 59.1623% | 32.7225% | 26.4398% | 22.2677%–31.081% | 9.1623% | 31.6754% | -11.7721% | 1.6128% | 10.4395% | 0.8561 |
| RV20_GTE35 | 20 | 170 | 65.8824% | 22.3529% | 14.1176% | 9.6741%–20.1471% | 2.3529% | 50.0% | -8.4052% | 4.8534% | 17.3693% | 0.7119 |
| RV20_LT15 | 20 | 585 | 70.9402% | 15.8974% | 9.0598% | 6.9932%–11.6606% | 1.3675% | 18.4615% | -6.2473% | 2.1123% | 6.482% | 1.2248 |
| ALL | 30 | 1930 | 67.5648% | 19.5337% | 14.0933% | 12.6121%–15.717% | 5.5959% | 39.3264% | -10.4519% | 3.1028% | 12.3089% | 1.1229 |
| RV20_15_25 | 30 | 773 | 67.7878% | 17.7232% | 13.066% | 10.8716%–15.6256% | 6.4683% | 39.4567% | -10.8122% | 2.9079% | 11.5668% | 1.1021 |
| RV20_25_35 | 30 | 382 | 63.3508% | 23.5602% | 20.6806% | 16.9208%–25.0243% | 11.5183% | 37.4346% | -15.2791% | 1.9462% | 11.5434% | 0.7902 |
| RV20_GTE35 | 30 | 170 | 70.0% | 23.5294% | 18.2353% | 13.1545%–24.72% | 2.3529% | 59.4118% | -8.8775% | 8.6122% | 22.4339% | 0.6987 |
| RV20_LT15 | 30 | 585 | 70.7692% | 17.265% | 9.4017% | 7.2944%–12.0387% | 1.7094% | 35.5556% | -7.2643% | 3.3196% | 8.6776% | 1.279 |
| ALL | 45 | 1915 | 71.4883% | 19.2689% | 15.1436% | 13.6079%–16.8188% | 8.1462% | 46.6841% | -12.7006% | 4.4438% | 15.5659% | 1.0809 |
| RV20_15_25 | 45 | 758 | 75.066% | 16.7546% | 13.3245% | 11.0892%–15.9297% | 6.5963% | 49.7361% | -11.1655% | 4.986% | 15.2912% | 0.9675 |
| RV20_25_35 | 45 | 382 | 64.9215% | 29.5812% | 24.8691% | 20.799%–29.4396% | 16.4921% | 44.5026% | -17.0407% | 4.2924% | 14.7391% | 0.7932 |
| RV20_GTE35 | 45 | 170 | 85.2941% | 10.5882% | 8.2353% | 4.9688%–13.3476% | 3.5294% | 69.4118% | -7.8925% | 10.5178% | 28.2652% | 0.6013 |
| RV20_LT15 | 45 | 585 | 67.6923% | 18.8034% | 13.6752% | 11.127%–16.6974% | 6.3248% | 38.6325% | -11.1208% | 3.3859% | 10.6653% | 1.3967 |

Wilson intervals are nominal: overlapping horizon events and serial dependence violate literal independent-trial assumptions. CSV non-overlap-offset ranges show sensitivity, not confidence bounds.
RV20 buckets use trailing information available at the starting close: <15%, 15–25%, 25–35%, >=35%. Any window crossing a missing expected-session close is censored.

## Terminal-loss budget sizing — payoff envelope, not broker margin

| Direction | N | Long/Short | NAV | Depth qualified/episodes | Median loss | P95 loss | Worst loss | Worst/NAV | Whole units at 0.5/1/2% budgets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | 1/1 | USD 100,000 | 62/62 | 373.8 | 616.3 | 768.3000000000002 | 0.7683% | 0/1/2 |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | 1/1 | USD 1,000,000 | 62/62 | 373.8 | 616.3 | 768.3000000000002 | 0.0768% | 6/13/26 |
| SHORT_HEAVY_1_LONG_N_SHORT | 2 | 1/2 | USD 100,000 | 62/62 | 24616.45 | 45003.95 | 50810.95 | 50.8109% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 2 | 1/2 | USD 1,000,000 | 62/62 | 24616.45 | 45003.95 | 50810.95 | 5.0811% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 3 | 1/3 | USD 100,000 | 62/62 | 51875.1 | 92864.6 | 105439.6 | 105.4396% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 3 | 1/3 | USD 1,000,000 | 62/62 | 51875.1 | 92864.6 | 105439.6 | 10.544% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 4 | 1/4 | USD 100,000 | 62/62 | 79133.75 | 140725.25 | 160068.25 | 160.0683% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 4 | 1/4 | USD 1,000,000 | 62/62 | 79133.75 | 140725.25 | 160068.25 | 16.0068% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | 1/5 | USD 100,000 | 62/62 | 106392.4 | 188585.9 | 214696.9 | 214.6969% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | 1/5 | USD 1,000,000 | 62/62 | 106392.4 | 188585.9 | 214696.9 | 21.4697% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 6 | 1/6 | USD 100,000 | 61/62 | 132919.55 | 236446.55 | 269325.55 | 269.3256% | 0/0/0 |
| SHORT_HEAVY_1_LONG_N_SHORT | 6 | 1/6 | USD 1,000,000 | 61/62 | 132919.55 | 236446.55 | 269325.55 | 26.9326% | 0/0/0 |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | 1/1 | USD 100,000 | 62/62 | 373.8 | 616.3 | 768.3000000000002 | 0.7683% | 0/1/2 |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | 1/1 | USD 1,000,000 | 62/62 | 373.8 | 616.3 | 768.3000000000002 | 0.0768% | 6/13/26 |
| LONG_HEAVY_N_LONG_1_SHORT | 2 | 2/1 | USD 100,000 | 61/62 | 858.95 | 1480.95 | 1844.9500000000003 | 1.845% | 0/0/1 |
| LONG_HEAVY_N_LONG_1_SHORT | 2 | 2/1 | USD 1,000,000 | 61/62 | 858.95 | 1480.95 | 1844.9500000000003 | 0.1845% | 2/5/10 |
| LONG_HEAVY_N_LONG_1_SHORT | 3 | 3/1 | USD 100,000 | 61/62 | 1374.6 | 2327.6 | 2921.6 | 2.9216% | 0/0/0 |
| LONG_HEAVY_N_LONG_1_SHORT | 3 | 3/1 | USD 1,000,000 | 61/62 | 1374.6 | 2327.6 | 2921.6 | 0.2922% | 1/3/6 |
| LONG_HEAVY_N_LONG_1_SHORT | 4 | 4/1 | USD 100,000 | 61/62 | 1890.25 | 3174.25 | 3998.2500000000005 | 3.9983% | 0/0/0 |
| LONG_HEAVY_N_LONG_1_SHORT | 4 | 4/1 | USD 1,000,000 | 61/62 | 1890.25 | 3174.25 | 3998.2500000000005 | 0.3998% | 1/2/5 |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | 5/1 | USD 100,000 | 61/62 | 2405.9 | 4020.9 | 5074.900000000001 | 5.0749% | 0/0/0 |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | 5/1 | USD 1,000,000 | 61/62 | 2405.9 | 4020.9 | 5074.900000000001 | 0.5075% | 0/1/3 |
| LONG_HEAVY_N_LONG_1_SHORT | 6 | 6/1 | USD 100,000 | 59/62 | 2865.55 | 4867.55 | 6151.55 | 6.1516% | 0/0/0 |
| LONG_HEAVY_N_LONG_1_SHORT | 6 | 6/1 | USD 1,000,000 | 59/62 | 2865.55 | 4867.55 | 6151.55 | 0.6152% | 0/1/3 |

Terminal loss is the lowest payoff across the expiry knots, not merely the QQQ=$0 outcome. Whole-unit counts use the worst observed qualifying episode and are terminal payoff arithmetic only. N=1 is mechanically the same 1-long/1-short spread in either label.

## Cost tug-of-war BAR (base costs, 1% NAV target and 1% terminal-risk budget)

The NAV target is the NET exit goal. The BAR estimates how far a midpoint-based gross mark would need to move to overcome observed spread crossing plus the selected slippage and commission assumptions. It is the P95 across per-episode median quote-mark drag, not a confirmed fill cost or an optimized trading rule.

| Direction | N | NAV | Sized units | Sizing status | Cost BAR P50 | Cost BAR P95 | Net target | Midpoint gross needed (P95) | Target / BAR P95 | Exit depth |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1 | SIZED_WITH_OBSERVED_DEPTH | 30.60 | 45.60 | 1000.00 | 1045.60 | 21.93x | 95.4% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 13 | SIZED_WITH_OBSERVED_DEPTH | 397.80 | 592.80 | 10000.00 | 10592.80 | 16.87x | 82.3% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 0 | BLOCKED_ZERO_WHOLE_UNITS | — | — | 1000.00 | — | — | — |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 0 | BLOCKED_ZERO_WHOLE_UNITS | — | — | 10000.00 | — | — | — |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1 | SIZED_WITH_OBSERVED_DEPTH | 30.60 | 45.60 | 1000.00 | 1045.60 | 21.93x | 95.4% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 13 | SIZED_WITH_OBSERVED_DEPTH | 397.80 | 592.80 | 10000.00 | 10592.80 | 16.87x | 82.3% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 0 | BLOCKED_ZERO_WHOLE_UNITS | — | — | 1000.00 | — | — | — |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1 | SIZED_WITH_OBSERVED_DEPTH | 95.30 | 148.30 | 10000.00 | 10148.30 | 67.43x | 92.8% |

The friction_bar_matrix.csv also breaks the cost drag out by VIX and DTE state and shows all 0.5/1/2% targets, both NAV inputs, all N values, and zero/base/adverse cost scenarios. A missing BAR caused by no depth-qualified historical episodes is BLOCK/PENDING, never treated as zero friction.

## Exit samples at base costs and 1% tail budget (full grid in CSV)

| Direction | N | NAV | Tail budget | Sized units | Sizing status | Policy | Resolved/eligible | Net P&L | Expectancy | Win% | Worst trade | Trigger% | DTE7 fallback | Deferred | Mark coverage |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DTE7_CLOSE_SHORT_RISK | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 100.0% | 0 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | TP_1.0PCT_FULL_CLOSE | 62/62 | -10553.15 | -170.21 | 14.5161% | -778.95 | 9.6774% | 56 | 5 | 99.3318% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_FULL_CLOSE | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_TRIM_SHORT_RISK | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_FULL_CLOSE | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_TRIM_SHORT_RISK | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_FULL_CLOSE | 62/62 | -11645.45 | -187.83 | 11.2903% | -728.6 | 77.4194% | 14 | 5 | 99.1603% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_TRIM_SHORT_RISK | 62/62 | -14865.25 | -239.76 | 11.2903% | -786.95 | 77.4194% | 14 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | SL_1.0PCT_FULL_CLOSE | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | DTE7_CLOSE_SHORT_RISK | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 100.0% | 0 | 5 | 99.3042% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | TP_1.0PCT_FULL_CLOSE | 52/52 | -62538.45 | -1202.66 | 21.1538% | -10126.35 | 15.3846% | 44 | 19 | 99.2409% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_FULL_CLOSE | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_TRIM_SHORT_RISK | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_FULL_CLOSE | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_TRIM_SHORT_RISK | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_FULL_CLOSE | 52/52 | -108083.3 | -2078.53 | 11.5385% | -9471.8 | 75.0% | 13 | 11 | 99.0932% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_TRIM_SHORT_RISK | 52/52 | -134520.75 | -2586.94 | 13.4615% | -10230.35 | 75.0% | 13 | 6 | 99.3042% |
| SHORT_HEAVY_1_LONG_N_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | SL_1.0PCT_FULL_CLOSE | 52/52 | -126703.2 | -2436.6 | 13.4615% | -10126.35 | 1.9231% | 51 | 5 | 99.2967% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DTE7_CLOSE_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | TP_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST3_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST3_1.0PCT_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST5_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST5_1.0PCT_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DAY20_NONPOS_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DAY20_NONPOS_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | SL_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DTE7_CLOSE_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | TP_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST3_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST3_1.0PCT_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST5_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST5_1.0PCT_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DAY20_NONPOS_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DAY20_NONPOS_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| SHORT_HEAVY_1_LONG_N_SHORT | 5 | USD 1,000,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | SL_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DTE7_CLOSE_SHORT_RISK | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 100.0% | 0 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | TP_1.0PCT_FULL_CLOSE | 62/62 | -10553.15 | -170.21 | 14.5161% | -778.95 | 9.6774% | 56 | 5 | 99.3318% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_FULL_CLOSE | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_TRIM_SHORT_RISK | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_FULL_CLOSE | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_TRIM_SHORT_RISK | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_FULL_CLOSE | 62/62 | -11645.45 | -187.83 | 11.2903% | -728.6 | 77.4194% | 14 | 5 | 99.1603% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_TRIM_SHORT_RISK | 62/62 | -14865.25 | -239.76 | 11.2903% | -786.95 | 77.4194% | 14 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 100,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | SL_1.0PCT_FULL_CLOSE | 62/62 | -14460.25 | -233.23 | 11.2903% | -778.95 | 0.0% | 62 | 5 | 99.3637% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | DTE7_CLOSE_SHORT_RISK | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 100.0% | 0 | 5 | 99.3042% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | TP_1.0PCT_FULL_CLOSE | 52/52 | -62538.45 | -1202.66 | 21.1538% | -10126.35 | 15.3846% | 44 | 19 | 99.2409% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_FULL_CLOSE | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_TRIM_SHORT_RISK | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_FULL_CLOSE | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_TRIM_SHORT_RISK | 52/52 | -130555.75 | -2510.69 | 13.4615% | -10126.35 | 0.0% | 52 | 5 | 99.3042% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_FULL_CLOSE | 52/52 | -108083.3 | -2078.53 | 11.5385% | -9471.8 | 75.0% | 13 | 11 | 99.0932% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_TRIM_SHORT_RISK | 52/52 | -134520.75 | -2586.94 | 13.4615% | -10230.35 | 75.0% | 13 | 6 | 99.3042% |
| LONG_HEAVY_N_LONG_1_SHORT | 1 | USD 1,000,000 | 1% | 13 | SIZED_WITH_OBSERVED_DEPTH | SL_1.0PCT_FULL_CLOSE | 52/52 | -126703.2 | -2436.6 | 13.4615% | -10126.35 | 1.9231% | 51 | 5 | 99.2967% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DTE7_CLOSE_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | TP_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST3_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST3_1.0PCT_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST5_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | FAST5_1.0PCT_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DAY20_NONPOS_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | DAY20_NONPOS_TRIM_SHORT_RISK | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 100,000 | 1% | 0 | BLOCKED_ZERO_WHOLE_UNITS | SL_1.0PCT_FULL_CLOSE | 0/0 | None | None | None% | None | None% | 0 | 0 | None% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DTE7_CLOSE_SHORT_RISK | 61/61 | -95107.9 | -1559.15 | 11.4754% | -5085.55 | 100.0% | 0 | 5 | 99.3538% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | TP_1.0PCT_FULL_CLOSE | 61/61 | -66377.65 | -1088.16 | 13.1148% | -5085.55 | 4.918% | 58 | 5 | 99.3396% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_FULL_CLOSE | 61/61 | -95107.9 | -1559.15 | 11.4754% | -5085.55 | 0.0% | 61 | 5 | 99.3538% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST3_1.0PCT_TRIM_SHORT_RISK | 61/61 | -95107.9 | -1559.15 | 11.4754% | -5085.55 | 0.0% | 61 | 5 | 99.3538% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_FULL_CLOSE | 61/61 | -95107.9 | -1559.15 | 11.4754% | -5085.55 | 0.0% | 61 | 5 | 99.3538% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | FAST5_1.0PCT_TRIM_SHORT_RISK | 61/61 | -95107.9 | -1559.15 | 11.4754% | -5085.55 | 0.0% | 61 | 5 | 99.3538% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_FULL_CLOSE | 61/61 | -75572.4 | -1238.89 | 13.1148% | -4801.8 | 81.9672% | 11 | 5 | 99.1323% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | DAY20_NONPOS_TRIM_SHORT_RISK | 61/61 | -95844.9 | -1571.23 | 11.4754% | -5093.55 | 81.9672% | 11 | 5 | 99.3538% |
| LONG_HEAVY_N_LONG_1_SHORT | 5 | USD 1,000,000 | 1% | 1 | SIZED_WITH_OBSERVED_DEPTH | SL_1.0PCT_FULL_CLOSE | 61/61 | -95107.9 | -1559.15 | 11.4754% | -5085.55 | 0.0% | 61 | 5 | 99.3538% |

## Self-audit / non-completion gates

- The option source reports a 16:00 ET preservation snapshot; exact quote timestamps and executable fills are not authenticated.
- 2018–2025 has already been seen in previous repository research: DEVELOPMENT/REVISIT, not blind final OOS.
- P(QQQ moves down 5%) is not P(a given option ratio loses 5% NAV): IV/skew, DTE, strikes, spreads, depth, costs and action lag intervene.
- No app sizing policy, Frozen Original Hybrid, main branch or broker-order permission changed.
- Deployment stays BLOCKED pending unseen OOS, decision-time/fill evidence and broker margin/assignment/forced-liquidation treatment.
