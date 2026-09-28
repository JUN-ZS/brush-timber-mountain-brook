# State × Return slice (V2.2 ASSOCIATIION)

> Frozen V2.2 Derived curve only. **ASSOCIATION_ONLY**. `credit_unlocked=false`. No param carve.

## By `assoc_v22` (regime on curve)

| State | Share | n | CAGR | MaxDD | Vol | Sharpe | mean/day | Stretch | Joint band |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CALM | 45.0% | 2538 | 6.2% | -16.4% | 12.6% | 1.129 | 0.000564 | False | False |
| UNSTABLE | 36.4% | 2055 | -0.7% | -32.8% | 16.6% | -0.032 | -2.1e-05 | False | False |
| TAIL | 10.7% | 604 | 0.6% | -38.6% | 24.5% | 0.3616 | 0.000352 | False | False |
| RECOVERY | 7.9% | 447 | 0.8% | -13.8% | 18.7% | 0.6484 | 0.00048 | False | False |

## Reading

- Best mean/day state: **CALM**
- Worst mean/day state: **UNSTABLE**
- Any state hits Stretch: **False**
- Any state hits joint 10–15%/DD≥-10%: **False**

State slices show where the frozen overlay spends time and how path stats differ; concatenated-regime CAGR is descriptive, not a deployable sleeve. Credit remains sealed.

## Era × State (compact)

| Era | State | n | CAGR | MaxDD | mean/day |
| --- | --- | --- | --- | --- | --- |
| 2003-2007 | CALM | 418 | 7.8% | -7.6% | 0.000697 |
| 2003-2007 | UNSTABLE | 406 | -1.5% | -16.9% | -0.000103 |
| 2003-2007 | RECOVERY | 109 | 0.8% | -7.8% | 0.000314 |
| 2008-2009 | CALM | 29 | -1.7% | -5.8% | -0.000912 |
| 2008-2009 | UNSTABLE | 216 | -2.7% | -20.9% | -0.000186 |
| 2008-2009 | TAIL | 223 | -13.3% | -38.6% | -0.001016 |
| 2008-2009 | RECOVERY | 37 | -7.4% | -5.4% | -0.001286 |
| 2010-2019 | CALM | 1403 | 7.3% | -16.4% | 0.000525 |
| 2010-2019 | UNSTABLE | 787 | -0.5% | -21.6% | -1.5e-05 |
| 2010-2019 | TAIL | 140 | 2.5% | -11.3% | 0.001762 |
| 2010-2019 | RECOVERY | 186 | 0.6% | -5.9% | 0.000358 |
| 2020 | CALM | 36 | 30.0% | -6.2% | 0.001115 |
| 2020 | UNSTABLE | 128 | 9.9% | -9.8% | 0.000701 |
| 2020 | TAIL | 81 | 12.6% | -10.8% | 0.001179 |
| 2021-2022 | CALM | 127 | 3.5% | -8.6% | 0.00027 |
| 2021-2022 | UNSTABLE | 215 | -11.5% | -25.9% | -0.001058 |
| 2021-2022 | TAIL | 101 | -3.6% | -14.9% | -0.000633 |
| 2021-2022 | RECOVERY | 60 | 3.8% | -13.8% | 0.000653 |
| 2023-2026 | CALM | 525 | 9.6% | -13.2% | 0.000679 |
| 2023-2026 | UNSTABLE | 303 | 4.8% | -13.0% | 0.000621 |
| 2023-2026 | TAIL | 46 | 3.3% | -5.9% | 0.002644 |
| 2023-2026 | RECOVERY | 47 | 4.0% | -3.5% | 0.002438 |

## BUILDING flag

- building=on: CAGR -1.4%, MaxDD -36.1%, n=553
- building=off: CAGR 8.5%, MaxDD -50.8%, n=5091

Next: optional RelVol weekPct stratum DESC-only join — still no Credit.
