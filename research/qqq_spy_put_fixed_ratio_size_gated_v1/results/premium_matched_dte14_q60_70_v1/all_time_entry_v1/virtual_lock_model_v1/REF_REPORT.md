# Per-trade virtual SPY -10% floor — model repricing

Study: all_time_entry_v1; period 2018-03-01 to 2025-12-15 (7.792 years).
Entry filter: none; exit policy: HOLD_20_OR_DTE_LE_7.

| Metric | Historical quote-side | Virtual-floor model |
|---|---:|---:|
| Resolved episodes | 1903 | 1903 |
| Cumulative episode P&L | USD -47,698.30 | USD 32,021.19 |
| Annual-average episode P&L sum | USD -6,121.38 | USD 4,109.45 |
| Mean per episode | USD -25.06 | USD 16.83 |
| Median per episode | USD 253.90 | USD 253.90 |
| Win rate | 73.46% | 73.52% |
| Worst resolved episode | USD -26,768.10 | USD -20,846.10 |
| Profit factor | 0.9444 | 1.0411 |

## Path and capital-pressure checks

- Cohort paths breaching -10%: 13; resolved exit closes below floor: 12; terminal P&L estimates adjusted: 12.
- Total terminal P&L adjustment: USD 79,719.49.
- Peak overlapping cohorts (date-level estimate): 10; average assignment obligation per cohort: USD 243,705.87.
- Worst single-cohort floating mark: original USD -23,763.10; virtual model USD -19,390.10.

Annual-average episode P&L is the sum of resolved episode P&L divided by elapsed study years, not account annual profit or CAGR. Overlapping daily entries require portfolio capital and margin constraints before account-level returns can be computed.

Limitations:
- Modelled virtual quote, not an actual tradable quote; Black-Scholes approximation for American-style SPY puts.
- Uses zero rates and zero dividend yield; same-day IV may be stale/noisy and quote residual is preserved.
- Only common-session closes are used; intraday floor breaches are missed.
- Overlapping episode P&L sums do not equal account returns or CAGR.
- Peak assignment notional is a contract-notional proxy, not broker margin; no portfolio cash, margin, assignment funding, forced liquidation, financing or compounding.
- The model changes SPY option marks but does not model counterfactual liquidity or altered discretionary decisions.
