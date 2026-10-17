# QQQ Event-Driven Portfolio NAV Scale Replay V1

**Research-only. No live HUB change and no broker orders.**

- Initial NAV cases: USD 80,000, USD 100,000, USD 1,000,000.
- Same source window: 2018-03-01 to 2025-12-15; 1960 sessions; 28 fixed events.
- 129 account rows; maximum NAV reconciliation error USD 0.00000000.
- The sole changed input is NAV. Strategy definitions, signals, option selection, holding horizon and costs stay fixed.
- Quote evidence is historical EOD with modeled side-price execution, not confirmed fills. Option history ends 2025-12-15.

## Core-only baseline by NAV

| Initial NAV USD | Final NAV USD | CAGR % | Observed MaxDD % | Worst observed year % |
|---:|---:|---:|---:|---:|
| 80,000 | 170,996.24 | 10.2398 | -22.7794 | -21.0335 |
| 100,000 | 213,745.30 | 10.2398 | -22.7794 | -21.0335 |
| 1,000,000 | 2,138,791.18 | 10.2486 | -22.796 | -21.049 |

## Candidate comparison — 1% tail budget, BASE costs

| NAV USD | Strategy | Final NAV | Delta final vs core | CAGR % | Delta CAGR pp | Observed MaxDD % | Delta MaxDD pp | Entries / blocked | Incomplete marks |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 80,000 | CALL_DEBIT_50D_10D | 170,381.24 | -615.00 | 10.1888 | -0.051 | -23.5001 | -0.7207 | 10 / 18 | 1 |
| 80,000 | CALL_DEBIT_PLUS_LONG_PUT_10D | 170,084.94 | -911.30 | 10.1642 | -0.0756 | -23.1741 | -0.3947 | 7 / 21 | 1 |
| 80,000 | PUT_SHORT_HEAVY_1x1 | 163,088.84 | -7,907.40 | 9.5719 | -0.6679 | -23.5163 | -0.7369 | 27 / 1 | 3 |
| 80,000 | PUT_SHORT_HEAVY_1x4 | 170,996.24 | 0.00 | 10.2398 | 0.0 | -22.7794 | 0.0 | 0 / 28 | 0 |
| 80,000 | PUT_SHORT_HEAVY_1x5 | 170,996.24 | 0.00 | 10.2398 | 0.0 | -22.7794 | 0.0 | 0 / 28 | 0 |
| 80,000 | PUT_SHORT_HEAVY_1x6 | 170,996.24 | 0.00 | 10.2398 | 0.0 | -22.7794 | 0.0 | 0 / 28 | 0 |
| 80,000 | PUT_LONG_HEAVY_2x1 | 164,856.44 | -6,139.80 | 9.7236 | -0.5162 | -24.0482 | -1.2688 | 19 / 9 | 2 |
| 100,000 | CALL_DEBIT_50D_10D | 216,063.70 | 2,318.40 | 10.3925 | 0.1527 | -23.0721 | -0.2927 | 20 / 8 | 1 |
| 100,000 | CALL_DEBIT_PLUS_LONG_PUT_10D | 214,777.60 | 1,032.30 | 10.3079 | 0.0681 | -23.0134 | -0.234 | 13 / 15 | 1 |
| 100,000 | PUT_SHORT_HEAVY_1x1 | 203,068.90 | -10,676.40 | 9.5172 | -0.7226 | -23.5053 | -0.7259 | 28 / 0 | 4 |
| 100,000 | PUT_SHORT_HEAVY_1x4 | 213,745.30 | 0.00 | 10.2398 | 0.0 | -22.7794 | 0.0 | 0 / 28 | 0 |
| 100,000 | PUT_SHORT_HEAVY_1x5 | 213,745.30 | 0.00 | 10.2398 | 0.0 | -22.7794 | 0.0 | 0 / 28 | 0 |
| 100,000 | PUT_SHORT_HEAVY_1x6 | 213,745.30 | 0.00 | 10.2398 | 0.0 | -22.7794 | 0.0 | 0 / 28 | 0 |
| 100,000 | PUT_LONG_HEAVY_2x1 | 205,228.00 | -8,517.30 | 9.666 | -0.5738 | -23.5534 | -0.774 | 24 / 4 | 2 |
| 1,000,000 | CALL_DEBIT_50D_10D | 2,163,898.58 | 25,107.40 | 10.4139 | 0.1653 | -23.4744 | -0.6784 | 28 / 0 | 43 |
| 1,000,000 | CALL_DEBIT_PLUS_LONG_PUT_10D | 2,148,011.78 | 9,220.60 | 10.3095 | 0.0609 | -23.2551 | -0.4591 | 24 / 4 | 29 |
| 1,000,000 | PUT_SHORT_HEAVY_1x1 | 2,014,272.18 | -124,519.00 | 9.4032 | -0.8454 | -24.135 | -1.339 | 28 / 0 | 69 |
| 1,000,000 | PUT_SHORT_HEAVY_1x4 | 2,138,791.18 | 0.00 | 10.2486 | 0.0 | -22.796 | 0.0 | 0 / 28 | 0 |
| 1,000,000 | PUT_SHORT_HEAVY_1x5 | 2,138,791.18 | 0.00 | 10.2486 | 0.0 | -22.796 | 0.0 | 0 / 28 | 0 |
| 1,000,000 | PUT_SHORT_HEAVY_1x6 | 2,138,791.18 | 0.00 | 10.2486 | 0.0 | -22.796 | 0.0 | 0 / 28 | 0 |
| 1,000,000 | PUT_LONG_HEAVY_2x1 | 2,007,978.08 | -130,813.10 | 9.3592 | -0.8894 | -24.1818 | -1.3858 | 28 / 0 | 55 |

## Capacity nonlinearity

The full CSV contains all 129 NAV accounts. The following companion view shows how entries and blocked entries changed as initial capital changed; this distinguishes percentage scaling from actual whole-contract feasibility.

| Strategy | Budget | Costs | Entries at USD 80k / 100k / 1m | Blocked at USD 80k / 100k / 1m | Delta final NAV vs core in USD 80k / 100k / 1m |
|---|---:|---|---|---|---|
| CALL_DEBIT_50D_10D | 1.0% | BASE | 10,20,28 | 18,8,0 | -615.0,2318.4,25107.4 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | BASE | 7,13,24 | 21,15,4 | -911.3,1032.3,9220.6 |
| PUT_LONG_HEAVY_2x1 | 1.0% | BASE | 19,24,28 | 9,4,0 | -6139.8,-8517.3,-130813.1 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | BASE | 27,28,28 | 1,0,0 | -7907.4,-10676.4,-124519.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | BASE | 0,0,0 | 28,28,28 | 0.0,0.0,0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | BASE | 0,0,0 | 28,28,28 | 0.0,0.0,0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | BASE | 0,0,0 | 28,28,28 | 0.0,0.0,0.0 |

## Interpretation limits

- Compare each option account only with CORE_ONLY at the same starting NAV; raw ending balances across different NAVs are not a strategy ranking.
- A larger NAV can unlock a whole contract, while displayed quote size can cap positions; therefore entries, costs and returns need not scale linearly.
- An option account whose entries are all blocked is effectively the core baseline, not evidence of added value.
- These three NAV levels are checkpoints, not a claim that every intermediate NAV was tested.
- Missing quote marks are never forward-filled. MaxDD may understate losses; broker margin, assignment, early exercise, forced liquidation and multi-leg sequencing are not modeled.
- All three NAV cases share the same exploratory 28-signal cohort; this is not out-of-sample confirmation.
