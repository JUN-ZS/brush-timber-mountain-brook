# QQQ/SPY PUT 1:3 Fixed-Anchor Five-Phase Robustness

- Each phase uses immutable scheduled common-session indices: phase + k × 5. A missing chain, missing underlying close, rejected filter, absent eligible pair, or outstanding pending entry is recorded as a skipped scheduled slot; it never moves future slots.
- Each phase runs the full contract-selection and quote-side accounting pipeline. This report does not shift old P&L records.
- Fixed ratio QQQ LONG PUT 1 : SPY SHORT PUT 3; no relative filter; overlapping cohorts enabled.
- Same expiry; DTE 30–60 targeting 45; target absolute Delta 0.25; quote-side displayed-size checks; $0.05/share/side slippage and $0.65 per contract/side commission.
- Historical option source ends 2025-12-12. Period windows end 2025-07-23. EOD quote-side results are estimates, not confirmed fills.

## Fixed-slot accounting and anchor validation

| Phase | Scheduled slots | Selected pairs | Skipped slots | Skip reasons | Anchor integrity |
|---:|---:|---:|---:|---|---|
| 0 | 392 | 392 | 0 | none | PASS |
| 1 | 392 | 392 | 0 | none | PASS |
| 2 | 392 | 391 | 1 | MISSING_QQQ_AND_SPY_OPTION_CHAIN=1 | PASS |
| 3 | 392 | 391 | 1 | MISSING_QQQ_OPTION_CHAIN=1 | PASS |
| 4 | 391 | 389 | 2 | MISSING_QQQ_AND_SPY_OPTION_CHAIN=2 | PASS |

## Phase comparison — 5Y window

| Phase | Exit | Trades/year | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Stress annualized | Peak overlap | Peak SPY assignment obligation |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 10d or DTE<=7 | 50.20 | 74.40% | $151.40 | $37,851.00 | $7,570.20 | $-4,891.20 | $5,570.20 | 4 | $557,700.00 |
| 0 | 20d or DTE<=7 | 50.20 | 82.66% | $362.65 | $89,938.40 | $17,987.68 | $-6,016.20 | $16,003.68 | 7 | $963,450.00 |
| 1 | 10d or DTE<=7 | 50.20 | 75.20% | $116.10 | $29,025.00 | $5,805.00 | $-6,330.20 | $3,805.00 | 4 | $553,800.00 |
| 1 | 20d or DTE<=7 | 50.20 | 82.26% | $329.11 | $81,619.40 | $16,323.88 | $-6,439.20 | $14,339.88 | 7 | $958,200.00 |
| 2 | 10d or DTE<=7 | 50.20 | 74.90% | $90.43 | $22,698.80 | $4,539.76 | $-8,412.20 | $2,531.76 | 3 | $543,300.00 |
| 2 | 20d or DTE<=7 | 50.20 | 82.73% | $310.07 | $77,207.20 | $15,441.44 | $-9,376.20 | $13,449.44 | 7 | $958,200.00 |
| 3 | 10d or DTE<=7 | 50.20 | 75.70% | $125.80 | $31,576.80 | $6,315.36 | $-8,076.20 | $4,307.36 | 3 | $540,900.00 |
| 3 | 20d or DTE<=7 | 50.20 | 82.47% | $314.07 | $78,832.80 | $15,766.56 | $-7,886.20 | $13,758.56 | 5 | $891,000.00 |
| 4 | 10d or DTE<=7 | 50.20 | 75.30% | $140.25 | $35,202.80 | $7,040.56 | $-3,990.20 | $5,032.56 | 3 | $544,500.00 |
| 4 | 20d or DTE<=7 | 50.20 | 79.60% | $323.79 | $80,947.00 | $16,189.40 | $-6,244.20 | $14,189.40 | 6 | $891,000.00 |

## 1Y / 3Y / 5Y comparisons — 20-session exit

| Phase | Window | Opened/resolved/unresolved | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Stress annualized | Peak overlap | Peak assignment obligation |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

## Calendar-year results — 20-session exit

| Year | Phase | Opened/resolved | Win rate | Mean/trade | Total resolved | Worst trade |
|---:|---:|---:|---:|---:|---:|---:|

## Limits

- This is still an in-sample historical robustness test, not forward validation.
- P&L is additive fixed-size cohort P&L, not compounded NAV; no total account cash, collateral, margin, liquidation or simultaneous-loss constraint is modeled.
- Peak assignment obligation sums strike × 100 × short SPY contracts and is not broker margin.
- Higher entry frequency mechanically increases concurrent exposures. The test does not prove the account can fund every overlapping cohort.
- $0.10/share/side stress is a cost sensitivity, not a new fill simulation. Displayed EOD size does not guarantee multi-leg fills.
- The result is not complete unless all fixed-slot accounting checks report PASS; anchor checks do not correct for dependence, regime clustering, or prior strategy selection.
