# Fixed-Anchor QQQ/SPY PUT Capital Capacity Audit

- Same fixed size in every NAV case: QQQ LONG PUT 1 : SPY SHORT PUT 3 per cohort, no filter, stride five, overlapping cohorts enabled.
- Gross SPY assignment obligation = short SPY strike × 100 × contracts. It is a conservative cash-capacity proxy, not broker margin. The QQQ long put is not netted against a different underlying's assignment.
- Positions count from entry through exit inclusive, or through last observed day if unresolved. Threshold days are calendar days.
- NAVs of $80k, $100k and $1m are comparison cases; available capital is assumed to be 25%, 50%, 75% or 100% of NAV. No NAV case is assumed to be the user's account.
- Fixed contract quantities are not resized to fit the NAV. This stage tests capacity; it does not simulate broker liquidation or confirmed fills.

## Fixed-anchor checks

| Phase | Scheduled slots | Selected | Entered | Entry skips | Missed slots | Status |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 392 | 392 | 392 | 0 | 0 | PASS |
| 1 | 392 | 392 | 392 | 0 | 0 | PASS |
| 2 | 392 | 391 | 391 | 0 | 1 | PASS |
| 3 | 392 | 391 | 390 | 1 | 1 | PASS |
| 4 | 391 | 389 | 389 | 0 | 2 | PASS |

## Exposure by phase and exit

| Phase | Exit | Resolved / unresolved | Net P&L (resolved) | Worst trade | Peak concurrent | Peak assignment obligation |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 10d or DTE<=7 | 389 / 3 | $36,550 | $-13,211 | 4 | $594,000 |
| 0 | 20d or DTE<=7 | 384 / 8 | $76,532 | $-23,302 | 7 | $980,100 |
| 1 | 10d or DTE<=7 | 389 / 3 | $10,094 | $-12,630 | 4 | $593,700 |
| 1 | 20d or DTE<=7 | 384 / 8 | $56,991 | $-25,266 | 7 | $980,400 |
| 2 | 10d or DTE<=7 | 388 / 3 | $19,730 | $-8,412 | 3 | $598,200 |
| 2 | 20d or DTE<=7 | 384 / 7 | $68,851 | $-18,370 | 7 | $986,400 |
| 3 | 10d or DTE<=7 | 388 / 2 | $28,283 | $-10,501 | 3 | $590,400 |
| 3 | 20d or DTE<=7 | 386 / 4 | $68,835 | $-21,325 | 5 | $976,800 |
| 4 | 10d or DTE<=7 | 387 / 2 | $20,731 | $-11,219 | 3 | $587,700 |
| 4 | 20d or DTE<=7 | 383 / 6 | $68,802 | $-20,969 | 6 | $972,900 |

## Worst phase — all NAV available (100%)

| Exit | NAV | Worst peak obligation | Obligation / NAV | Phases with peak breach | Max calendar days above capacity |
|---|---:|---:|---:|---:|---:|
| 10d or DTE<=7 | $80,000 | $598,200 | 747.8% | 5/5 | 2836 |
| 10d or DTE<=7 | $100,000 | $598,200 | 598.2% | 5/5 | 2836 |
| 10d or DTE<=7 | $1,000,000 | $598,200 | 59.8% | 0/5 | 0 |
| 20d or DTE<=7 | $80,000 | $986,400 | 1233.0% | 5/5 | 2836 |
| 20d or DTE<=7 | $100,000 | $986,400 | 986.4% | 5/5 | 2836 |
| 20d or DTE<=7 | $1,000,000 | $986,400 | 98.6% | 0/5 | 0 |

## Worst phase — only 50% of NAV available

| Exit | NAV | Capital budget | Worst peak obligation | Obligation / budget | Phases with peak breach | Max calendar days above budget |
|---|---:|---:|---:|---:|---:|---:|
| 10d or DTE<=7 | $80,000 | $40,000 | $598,200 | 1495.5% | 5/5 | 2843 |
| 10d or DTE<=7 | $100,000 | $50,000 | $598,200 | 1196.4% | 5/5 | 2843 |
| 10d or DTE<=7 | $1,000,000 | $500,000 | $598,200 | 119.6% | 5/5 | 138 |
| 20d or DTE<=7 | $80,000 | $40,000 | $986,400 | 2466.0% | 5/5 | 2843 |
| 20d or DTE<=7 | $100,000 | $50,000 | $986,400 | 1972.8% | 5/5 | 2843 |
| 20d or DTE<=7 | $1,000,000 | $500,000 | $986,400 | 197.3% | 5/5 | 1380 |

## Limits

- Positive additive P&L cannot override an infeasible cash-capacity path. The tested size is fixed, and no account-level capital gate is applied yet.
- This audit is not a margin model; it omits intraday fills, financing, changes in NAV, assignment timing and broker-specific offsets.
