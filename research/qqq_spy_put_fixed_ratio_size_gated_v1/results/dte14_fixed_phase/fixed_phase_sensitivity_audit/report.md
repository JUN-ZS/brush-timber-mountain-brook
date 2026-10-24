# QQQ/SPY PUT 1:3 Fixed-Anchor Five-Phase Robustness

- Each phase uses immutable scheduled common-session indices: phase + k × 5. A missing chain, missing underlying close, rejected filter, absent eligible pair, or outstanding pending entry is recorded as a skipped scheduled slot; it never moves future slots.
- Each phase runs the full contract-selection and quote-side accounting pipeline. This report does not shift old P&L records.
- Fixed ratio QQQ LONG PUT 1 : SPY SHORT PUT 3; no relative filter; overlapping cohorts enabled.
- Same expiry; DTE 7–21 targeting 14; target absolute Delta 0.25; quote-side displayed-size checks; $0.05/share/side slippage and $0.65 per contract/side commission.
- Historical option source ends 2025-12-12. Period windows end 2025-07-23. EOD quote-side results are estimates, not confirmed fills.

## Fixed-slot accounting and anchor validation

| Phase | Scheduled slots | Selected pairs | Skipped slots | Skip reasons | Anchor integrity |
|---:|---:|---:|---:|---|---|
| 0 | 392 | 392 | 0 | none | PASS |
| 1 | 392 | 392 | 0 | none | PASS |
| 2 | 392 | 391 | 1 | MISSING_QQQ_AND_SPY_OPTION_CHAIN=1 | PASS |
| 3 | 392 | 391 | 1 | MISSING_QQQ_OPTION_CHAIN=1 | PASS |
| 4 | 391 | 388 | 3 | MISSING_QQQ_AND_SPY_OPTION_CHAIN=2; NO_ELIGIBLE_COMMON_EXPIRY_PAIR=1 | PASS |

## Phase comparison — 5Y window

| Phase | Exit | Trades/year | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Stress annualized | Peak overlap | Peak SPY assignment obligation |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 5d | 50.20 | 80.97% | $94.93 | $23,446.60 | $4,689.32 | $-7,612.20 | $2,713.32 | 2 | $368,700.00 |
| 0 | 10d | 50.20 | 88.89% | $362.02 | $3,258.20 | $651.64 | $-1,818.20 | $579.64 | 3 | $403,800.00 |
| 0 | 20d | 50.20 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $403,800.00 |
| 0 | DTE<=7 | 50.20 | 76.89% | $51.30 | $12,875.80 | $2,575.16 | $-9,955.20 | $567.16 | 2 | $368,700.00 |
| 1 | 5d | 50.20 | 77.51% | $28.05 | $6,985.20 | $1,397.04 | $-6,030.20 | $-594.96 | 2 | $370,500.00 |
| 1 | 10d | 50.20 | 80.00% | $25.40 | $127.00 | $25.40 | $-1,875.20 | $-14.60 | 3 | $413,100.00 |
| 1 | 20d | 50.20 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $413,100.00 |
| 1 | DTE<=7 | 50.20 | 74.90% | $44.06 | $11,059.80 | $2,211.96 | $-6,020.20 | $203.96 | 2 | $370,500.00 |
| 2 | 5d | 50.20 | 77.29% | $20.42 | $5,124.80 | $1,024.96 | $-9,303.20 | $-983.04 | 2 | $369,300.00 |
| 2 | 10d | 50.20 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $399,000.00 |
| 2 | 20d | 50.20 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $399,000.00 |
| 2 | DTE<=7 | 50.20 | 72.91% | $29.62 | $7,433.80 | $1,486.76 | $-4,188.20 | $-521.24 | 2 | $369,300.00 |
| 3 | 5d | 50.20 | 78.00% | $55.53 | $13,883.00 | $2,776.60 | $-9,029.20 | $776.60 | 2 | $369,000.00 |
| 3 | 10d | 50.20 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $398,400.00 |
| 3 | 20d | 50.20 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $398,400.00 |
| 3 | DTE<=7 | 50.20 | 76.10% | $53.07 | $13,319.80 | $2,663.96 | $-9,164.20 | $655.96 | 2 | $369,000.00 |
| 4 | 5d | 50.00 | 78.51% | $44.55 | $10,781.60 | $2,156.32 | $-9,327.20 | $220.32 | 2 | $369,600.00 |
| 4 | 10d | 50.00 | 100.00% | $278.30 | $1,113.20 | $222.64 | $187.80 | $190.64 | 3 | $419,100.00 |
| 4 | 20d | 50.00 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $419,100.00 |
| 4 | DTE<=7 | 50.00 | 76.71% | $65.46 | $16,300.20 | $3,260.04 | $-7,156.20 | $1,268.04 | 2 | $369,600.00 |

## 1Y / 3Y / 5Y comparisons — 20-session exit

| Phase | Window | Opened/resolved/unresolved | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Stress annualized | Peak overlap | Peak assignment obligation |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1Y | 50/0/50 | — | — | $0.00 | $0.00 | — | $0.00 | 2 | $368,700.00 |
| 0 | 3Y | 150/0/150 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $370,800.00 |
| 0 | 5Y | 251/0/251 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $403,800.00 |
| 1 | 1Y | 50/0/50 | — | — | $0.00 | $0.00 | — | $0.00 | 2 | $370,500.00 |
| 1 | 3Y | 150/0/150 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $370,500.00 |
| 1 | 5Y | 251/0/251 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $413,100.00 |
| 2 | 1Y | 50/0/50 | — | — | $0.00 | $0.00 | — | $0.00 | 2 | $369,300.00 |
| 2 | 3Y | 151/0/151 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $369,300.00 |
| 2 | 5Y | 251/0/251 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $399,000.00 |
| 3 | 1Y | 51/0/51 | — | — | $0.00 | $0.00 | — | $0.00 | 2 | $369,000.00 |
| 3 | 3Y | 151/0/151 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $369,000.00 |
| 3 | 5Y | 251/0/251 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $398,400.00 |
| 4 | 1Y | 50/0/50 | — | — | $0.00 | $0.00 | — | $0.00 | 2 | $369,600.00 |
| 4 | 3Y | 150/0/150 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $369,600.00 |
| 4 | 5Y | 250/0/250 | — | — | $0.00 | $0.00 | — | $0.00 | 3 | $419,100.00 |

## Calendar-year results — 20-session exit

| Year | Phase | Opened/resolved | Win rate | Mean/trade | Total resolved | Worst trade |
|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 0 | 43/0 | — | — | $0.00 | — |
| 2018 | 1 | 42/0 | — | — | $0.00 | — |
| 2018 | 2 | 42/0 | — | — | $0.00 | — |
| 2018 | 3 | 42/0 | — | — | $0.00 | — |
| 2018 | 4 | 41/0 | — | — | $0.00 | — |
| 2019 | 0 | 50/0 | — | — | $0.00 | — |
| 2019 | 1 | 51/0 | — | — | $0.00 | — |
| 2019 | 2 | 51/0 | — | — | $0.00 | — |
| 2019 | 3 | 50/0 | — | — | $0.00 | — |
| 2019 | 4 | 49/0 | — | — | $0.00 | — |
| 2020 | 0 | 51/0 | — | — | $0.00 | — |
| 2020 | 1 | 50/0 | — | — | $0.00 | — |
| 2020 | 2 | 49/0 | — | — | $0.00 | — |
| 2020 | 3 | 51/0 | — | — | $0.00 | — |
| 2020 | 4 | 51/0 | — | — | $0.00 | — |
| 2021 | 0 | 50/0 | — | — | $0.00 | — |
| 2021 | 1 | 51/0 | — | — | $0.00 | — |
| 2021 | 2 | 51/0 | — | — | $0.00 | — |
| 2021 | 3 | 49/0 | — | — | $0.00 | — |
| 2021 | 4 | 49/0 | — | — | $0.00 | — |
| 2022 | 0 | 50/0 | — | — | $0.00 | — |
| 2022 | 1 | 50/0 | — | — | $0.00 | — |
| 2022 | 2 | 50/0 | — | — | $0.00 | — |
| 2022 | 3 | 51/0 | — | — | $0.00 | — |
| 2022 | 4 | 50/0 | — | — | $0.00 | — |
| 2023 | 0 | 50/0 | — | — | $0.00 | — |
| 2023 | 1 | 50/0 | — | — | $0.00 | — |
| 2023 | 2 | 50/0 | — | — | $0.00 | — |
| 2023 | 3 | 50/0 | — | — | $0.00 | — |
| 2023 | 4 | 50/0 | — | — | $0.00 | — |
| 2024 | 0 | 51/0 | — | — | $0.00 | — |
| 2024 | 1 | 50/0 | — | — | $0.00 | — |
| 2024 | 2 | 50/0 | — | — | $0.00 | — |
| 2024 | 3 | 50/0 | — | — | $0.00 | — |
| 2024 | 4 | 51/0 | — | — | $0.00 | — |
| 2025 | 0 | 27/0 | — | — | $0.00 | — |
| 2025 | 1 | 28/0 | — | — | $0.00 | — |
| 2025 | 2 | 28/0 | — | — | $0.00 | — |
| 2025 | 3 | 28/0 | — | — | $0.00 | — |
| 2025 | 4 | 27/0 | — | — | $0.00 | — |

## Limits

- This is still an in-sample historical robustness test, not forward validation.
- P&L is additive fixed-size cohort P&L, not compounded NAV; no total account cash, collateral, margin, liquidation or simultaneous-loss constraint is modeled.
- Peak assignment obligation sums strike × 100 × short SPY contracts and is not broker margin.
- Higher entry frequency mechanically increases concurrent exposures. The test does not prove the account can fund every overlapping cohort.
- $0.10/share/side stress is a cost sensitivity, not a new fill simulation. Displayed EOD size does not guarantee multi-leg fills.
- The result is not complete unless all fixed-slot accounting checks report PASS; anchor checks do not correct for dependence, regime clustering, or prior strategy selection.
