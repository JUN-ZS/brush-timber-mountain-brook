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
| 4 | 391 | 388 | 388 | 0 | 3 | PASS |

## Exposure by phase and exit

| Phase | Exit | Resolved / unresolved | Net P&L (resolved) | Worst trade | Peak concurrent | Peak assignment obligation |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 5d | 382 / 10 | $24,348 | $-8,020 | 2 | $403,500 |
| 0 | 10d | 26 / 366 | $-37,451 | $-15,353 | 3 | $403,800 |
| 0 | 20d | 0 / 392 | $0 | — | 3 | $403,800 |
| 0 | DTE<=7 | 390 / 2 | $-11,194 | $-11,506 | 3 | $403,500 |
| 1 | 5d | 384 / 8 | $-5,077 | $-8,918 | 2 | $403,500 |
| 1 | 10d | 12 / 380 | $-495 | $-1,875 | 3 | $413,100 |
| 1 | 20d | 0 / 392 | $0 | — | 3 | $413,100 |
| 1 | DTE<=7 | 391 / 1 | $-3,866 | $-8,918 | 2 | $400,500 |
| 2 | 5d | 382 / 9 | $2,869 | $-9,303 | 3 | $404,400 |
| 2 | 10d | 12 / 379 | $-255 | $-1,797 | 3 | $404,400 |
| 2 | 20d | 0 / 391 | $0 | — | 3 | $404,400 |
| 2 | DTE<=7 | 388 / 3 | $-5,575 | $-5,449 | 3 | $404,400 |
| 3 | 5d | 383 / 7 | $13,196 | $-9,029 | 2 | $403,200 |
| 3 | 10d | 11 / 379 | $-4,604 | $-5,120 | 3 | $403,200 |
| 3 | 20d | 0 / 390 | $0 | — | 3 | $403,200 |
| 3 | DTE<=7 | 388 / 2 | $7,888 | $-9,164 | 3 | $403,200 |
| 4 | 5d | 372 / 16 | $-5,773 | $-9,327 | 2 | $400,500 |
| 4 | 10d | 23 / 365 | $-34,632 | $-11,782 | 3 | $419,100 |
| 4 | 20d | 0 / 388 | $0 | — | 3 | $419,100 |
| 4 | DTE<=7 | 386 / 2 | $-8,517 | $-9,622 | 2 | $400,500 |

## Worst phase — all NAV available (100%)

| Exit | NAV | Worst peak obligation | Obligation / NAV | Phases with peak breach | Max calendar days above capacity |
|---|---:|---:|---:|---:|---:|
| 5d | $80,000 | $404,400 | 505.5% | 5/5 | 2706 |
| 5d | $100,000 | $404,400 | 404.4% | 5/5 | 2232 |
| 5d | $1,000,000 | $404,400 | 40.4% | 0/5 | 0 |
| 10d | $80,000 | $419,100 | 523.9% | 5/5 | 2801 |
| 10d | $100,000 | $419,100 | 419.1% | 5/5 | 2683 |
| 10d | $1,000,000 | $419,100 | 41.9% | 0/5 | 0 |
| 20d | $80,000 | $419,100 | 523.9% | 5/5 | 2801 |
| 20d | $100,000 | $419,100 | 419.1% | 5/5 | 2683 |
| 20d | $1,000,000 | $419,100 | 41.9% | 0/5 | 0 |
| DTE<=7 | $80,000 | $404,400 | 505.5% | 5/5 | 2698 |
| DTE<=7 | $100,000 | $404,400 | 404.4% | 5/5 | 2292 |
| DTE<=7 | $1,000,000 | $404,400 | 40.4% | 0/5 | 0 |

## Worst phase — only 50% of NAV available

| Exit | NAV | Capital budget | Worst peak obligation | Obligation / budget | Phases with peak breach | Max calendar days above budget |
|---|---:|---:|---:|---:|---:|---:|
| 5d | $80,000 | $40,000 | $404,400 | 1011.0% | 5/5 | 2843 |
| 5d | $100,000 | $50,000 | $404,400 | 808.8% | 5/5 | 2843 |
| 5d | $1,000,000 | $500,000 | $404,400 | 80.9% | 0/5 | 0 |
| 10d | $80,000 | $40,000 | $419,100 | 1047.8% | 5/5 | 2843 |
| 10d | $100,000 | $50,000 | $419,100 | 838.2% | 5/5 | 2843 |
| 10d | $1,000,000 | $500,000 | $419,100 | 83.8% | 0/5 | 0 |
| 20d | $80,000 | $40,000 | $419,100 | 1047.8% | 5/5 | 2843 |
| 20d | $100,000 | $50,000 | $419,100 | 838.2% | 5/5 | 2843 |
| 20d | $1,000,000 | $500,000 | $419,100 | 83.8% | 0/5 | 0 |
| DTE<=7 | $80,000 | $40,000 | $404,400 | 1011.0% | 5/5 | 2822 |
| DTE<=7 | $100,000 | $50,000 | $404,400 | 808.8% | 5/5 | 2822 |
| DTE<=7 | $1,000,000 | $500,000 | $404,400 | 80.9% | 0/5 | 0 |

## Limits

- Positive additive P&L cannot override an infeasible cash-capacity path. The tested size is fixed, and no account-level capital gate is applied yet.
- This audit is not a margin model; it omits intraday fills, financing, changes in NAV, assignment timing and broker-specific offsets.
