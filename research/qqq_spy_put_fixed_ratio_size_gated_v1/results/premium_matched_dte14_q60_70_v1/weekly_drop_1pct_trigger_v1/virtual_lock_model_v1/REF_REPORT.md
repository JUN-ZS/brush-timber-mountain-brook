# Per-trade virtual SPY -10% floor — model repricing

Study: weekly_drop_1pct_trigger_v1; period 2018-03-01 to 2025-12-15 (7.792 years).
Entry filter: spy_weekly_drop_1pct; exit policy: HOLD_20_OR_DTE_LE_7.

| Metric | Historical quote-side | Virtual-floor model |
|---|---:|---:|
| Resolved episodes | 138 | 138 |
| Cumulative episode P&L | USD 846.20 | USD 7,142.36 |
| Annual-average episode P&L sum | USD 108.60 | USD 916.62 |
| Mean per episode | USD 6.13 | USD 51.76 |
| Median per episode | USD 271.40 | USD 271.40 |
| Win rate | 77.54% | 77.54% |
| Worst resolved episode | USD -15,422.10 | USD -15,422.10 |
| Profit factor | 1.0113 | 1.104 |

## Path and capital-pressure checks

- Cohort paths breaching -10%: 1; resolved exit closes below floor: 1; terminal P&L estimates adjusted: 1.
- Total terminal P&L adjustment: USD 6,296.16.
- Peak overlapping cohorts (date-level estimate): 3; average assignment obligation per cohort: USD 236,628.26.
- Worst single-cohort floating mark: original USD -16,291.10; virtual model USD -16,291.10.

Annual-average episode P&L is the sum of resolved episode P&L divided by elapsed study years, not account annual profit or CAGR. Overlapping daily entries require portfolio capital and margin constraints before account-level returns can be computed.

Limitations:
- Modelled virtual quote, not an actual tradable quote; Black-Scholes approximation for American-style SPY puts.
- Uses zero rates and zero dividend yield; same-day IV may be stale/noisy and quote residual is preserved.
- Only common-session closes are used; intraday floor breaches are missed.
- Overlapping episode P&L sums do not equal account returns or CAGR.
- Peak assignment notional is a contract-notional proxy, not broker margin; no portfolio cash, margin, assignment funding, forced liquidation, financing or compounding.
- The model changes SPY option marks but does not model counterfactual liquidity or altered discretionary decisions.
