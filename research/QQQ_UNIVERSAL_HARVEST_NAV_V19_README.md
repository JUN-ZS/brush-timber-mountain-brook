# QQQ Universal Harvest NAV V19

Research only. Not a live signal. Do not merge into V2.2.

V18 measured opportunity counts. V19 adds the missing official NAV layer.

## Capital and marking

- Capital = $100,000 (same as V16 NAV convention).
- NAV ≠ Bank. Bank still follows V18 isolation. NAV marks every realized cashflow.
- Cashflows: seed P&L on seed exit, then each purchased right P&L on that right's exit.
- No daily MTM inside a right. Step NAV only.
- No look-ahead, no BS, no interpolation, no parameter search.

## Two report layers

1. Per-seed books. Each N>2 WIN is its own isolated book. These books overlap in calendar and must not be summed into one portfolio.
2. FIRST_SEED_ONLY. One official curve: the earliest V16 N>2 WIN, isolated, no re-seed after Bank hits 0.

ISOLATED is authoritative. REPLENISH is contamination comparator only.

Hybrid Dynamic remains excluded.
