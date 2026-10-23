# QQQ LONG PUT 1 : SPY SHORT PUT 3 — DTE 14 vs DTE 45 comparison

## Frozen comparison design

- DTE45 reference: DTE 30–60, target 45; target absolute Delta 0.25 on each leg.
- DTE14 test: DTE 7–21, target 14; target absolute Delta 0.25 on each leg.
- Both arms keep the same source pins, no entry filter, fixed 1:3, five-session fixed-anchor cadence, five phases, overlapping cohorts, same expiry, quote-side size checks and base costs (USD 0.05/share/side slippage plus USD 0.65/contract/side commission).
- Fixed-size cohort estimates, not compounded NAV or confirmed fills. Unresolved trades stay explicit, especially where a longer holding policy nears expiry.

## Fixed-anchor integrity

| Arm | Phase | Scheduled slots | Selected signals | Skipped slots | Status |
|---|---:|---:|---:|---:|---|
| DTE45 | 0 | 392 | 392 | 0 | PASS |
| DTE45 | 1 | 392 | 392 | 0 | PASS |
| DTE45 | 2 | 392 | 391 | 1 | PASS |
| DTE45 | 3 | 392 | 391 | 1 | PASS |
| DTE45 | 4 | 391 | 389 | 2 | PASS |
| DTE14 | 0 | 392 | 392 | 0 | PASS |
| DTE14 | 1 | 392 | 392 | 0 | PASS |
| DTE14 | 2 | 392 | 391 | 1 | PASS |
| DTE14 | 3 | 392 | 391 | 1 | PASS |
| DTE14 | 4 | 391 | 388 | 3 | PASS |

## Five-year performance by phase and exit policy

| Phase | Policy | DTE45 resolved/opened | DTE14 resolved/opened | Win DTE45 | Win DTE14 | Mean net DTE45 | Mean net DTE14 | Worst DTE45 | Worst DTE14 | Peak obligation DTE45 | Peak obligation DTE14 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | HOLD_5_SESSIONS | 251/251 | 247/251 | 69.72% | 80.97% | USD 74.08 | USD 94.93 | USD -5,302.20 | USD -7,612.20 | USD 363,600.00 | USD 368,700.00 |
| 0 | HOLD_10_SESSIONS | 250/251 | 9/251 | 74.40% | 88.89% | USD 151.40 | USD 362.02 | USD -4,891.20 | USD -1,818.20 | USD 557,700.00 | USD 403,800.00 |
| 0 | HOLD_20_SESSIONS | 248/251 | 0/251 | 82.66% | — | USD 362.11 | — | USD -6,016.20 | — | USD 963,450.00 | USD 403,800.00 |
| 0 | EXIT_AT_DTE_LE_7 | 242/251 | 251/251 | 85.54% | 76.89% | USD 414.68 | USD 51.30 | USD -8,692.20 | USD -9,955.20 | USD 1,227,600.00 | USD 368,700.00 |
| 1 | HOLD_5_SESSIONS | 251/251 | 249/251 | 67.33% | 77.51% | USD 19.64 | USD 28.05 | USD -4,750.20 | USD -6,030.20 | USD 363,600.00 | USD 370,500.00 |
| 1 | HOLD_10_SESSIONS | 250/251 | 5/251 | 75.20% | 80.00% | USD 116.10 | USD 25.40 | USD -6,330.20 | USD -1,875.20 | USD 553,800.00 | USD 413,100.00 |
| 1 | HOLD_20_SESSIONS | 248/251 | 0/251 | 82.26% | — | USD 327.48 | — | USD -6,439.20 | — | USD 958,200.00 | USD 413,100.00 |
| 1 | EXIT_AT_DTE_LE_7 | 243/251 | 251/251 | 84.36% | 74.90% | USD 430.44 | USD 44.06 | USD -6,998.20 | USD -6,020.20 | USD 1,173,600.00 | USD 370,500.00 |
| 2 | HOLD_5_SESSIONS | 251/251 | 251/251 | 66.53% | 77.29% | USD 25.48 | USD 20.42 | USD -8,482.20 | USD -9,303.20 | USD 363,300.00 | USD 369,300.00 |
| 2 | HOLD_10_SESSIONS | 251/251 | 0/251 | 74.90% | — | USD 90.43 | — | USD -8,412.20 | — | USD 543,300.00 | USD 399,000.00 |
| 2 | HOLD_20_SESSIONS | 248/251 | 0/251 | 82.66% | — | USD 306.68 | — | USD -9,376.20 | — | USD 958,200.00 | USD 399,000.00 |
| 2 | EXIT_AT_DTE_LE_7 | 243/251 | 251/251 | 85.19% | 72.91% | USD 408.66 | USD 29.62 | USD -8,438.20 | USD -4,188.20 | USD 1,204,200.00 | USD 369,300.00 |
| 3 | HOLD_5_SESSIONS | 251/251 | 250/251 | 65.34% | 78.00% | USD 30.41 | USD 55.53 | USD -7,423.20 | USD -9,029.20 | USD 362,400.00 | USD 369,000.00 |
| 3 | HOLD_10_SESSIONS | 251/251 | 0/251 | 75.70% | — | USD 125.80 | — | USD -8,076.20 | — | USD 540,900.00 | USD 398,400.00 |
| 3 | HOLD_20_SESSIONS | 251/251 | 0/251 | 82.47% | — | USD 314.07 | — | USD -7,886.20 | — | USD 891,000.00 | USD 398,400.00 |
| 3 | EXIT_AT_DTE_LE_7 | 241/251 | 251/251 | 86.31% | 76.10% | USD 423.57 | USD 53.07 | USD -9,106.20 | USD -9,164.20 | USD 1,215,600.00 | USD 369,000.00 |
| 4 | HOLD_5_SESSIONS | 251/251 | 242/250 | 66.14% | 78.51% | USD 54.55 | USD 44.55 | USD -3,165.20 | USD -9,327.20 | USD 364,500.00 | USD 369,600.00 |
| 4 | HOLD_10_SESSIONS | 251/251 | 4/250 | 75.30% | 100.00% | USD 140.25 | USD 278.30 | USD -3,990.20 | USD 187.80 | USD 544,500.00 | USD 419,100.00 |
| 4 | HOLD_20_SESSIONS | 250/251 | 0/250 | 79.60% | — | USD 323.81 | — | USD -6,244.20 | — | USD 891,000.00 | USD 419,100.00 |
| 4 | EXIT_AT_DTE_LE_7 | 242/251 | 249/250 | 85.95% | 76.71% | USD 389.36 | USD 65.46 | USD -8,526.20 | USD -7,156.20 | USD 1,225,500.00 | USD 369,600.00 |

## Actual entry-date moneyness

| Phase | Leg | DTE45 median signed % | DTE14 median signed % | Difference (pp) | DTE45 ATM/ITM | DTE14 ATM/ITM |
|---:|---|---:|---:|---:|---:|---:|
| 0 | QQQ | 4.70% | 2.73% | -1.963 pp | 1 | 6 |
| 0 | SPY | 3.75% | 2.06% | -1.686 pp | 0 | 8 |
| 1 | QQQ | 4.95% | 2.99% | -1.958 pp | 0 | 5 |
| 1 | SPY | 3.89% | 2.25% | -1.637 pp | 0 | 5 |
| 2 | QQQ | 4.70% | 2.59% | -2.107 pp | 2 | 12 |
| 2 | SPY | 3.75% | 2.03% | -1.724 pp | 1 | 11 |
| 3 | QQQ | 4.77% | 2.80% | -1.970 pp | 1 | 10 |
| 3 | SPY | 3.88% | 2.08% | -1.793 pp | 1 | 11 |
| 4 | QQQ | 4.68% | 2.69% | -1.990 pp | 1 | 9 |
| 4 | SPY | 3.76% | 2.09% | -1.671 pp | 1 | 5 |

## Interpretation safeguards

- Delta 0.25 is not a fixed OTM percent and not a guaranteed 75% win probability.
- Positive signed distance is OTM; negative is ITM. No selected ATM/ITM row is silently removed.
- The five phases overlap as samples; they are anchor-sensitivity checks, not five independent cohorts.
- Win rate uses resolved trades only. P&L is additive fixed-size cohort P&L. Gross SPY assignment obligation is not broker margin.

## Input audit hashes

- DTE45 phase audit SHA-256: 5be329811a96eef926fa18622ed0a0ff836d91e9bc6ec5e2f267513461389eb8
- DTE45 OTM manifest SHA-256: 39178a24e8c5db34286f7080f9c3c536010a775915255853e43c5adf4a3fb6a6
- DTE14 phase audit SHA-256: e2ab958de2f737d09125569e7df1d1fab3f69bd70fa5509cb28139fb2b58f87e
- DTE14 OTM manifest SHA-256: 6195a061975e69454ded22c287ae85f6a13a36f1d809415c38f562d0bd28fc83
- performance_comparison.csv: five phases × three windows × four exit policies (60 paired cases).
- otm_comparison.csv: per phase, leg, and signal/entry time (20 paired rows).
