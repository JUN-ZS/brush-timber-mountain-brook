# QQQ policy-MAE, exit-delay and strict same-contract reversal study

**Research-only; no policy promoted. MaxDD is descriptive only.**

- Source episodes: 62; option source ends 2025-12-15.
- Configurations: 1200; resolved NAV paths: 1200; target reached in 92 searched configurations.
- Target: ending NAV >= 3.14012x start NAV (USD 100,000 -> USD 314,012; USD 1,000,000 -> USD 3,140,120).
- Walk-forward warm-up: at least 10 clean prior resolved episodes, strictly before each new entry.
- Budget ladder: 2%, 5%, 10%, 15%, 20%, 30%, 40%, 50%, 75%, 100%; MAE stress: 1.0x, 1.5x, 2.0x; forced delays: 0, 1, 2, 3, 5 sessions.

## Exact inversion

- Original: +1 original high-strike put and -5 original low-strike puts.
- Strict inverse: -1 of the same original high-strike contract and +5 of the same original low-strike contract. Same expiration, IDs, strikes and quote streams; only position signs/quantities reverse.
- This does not use the previous different-strike long-heavy family as a proxy.

## Risk accounting

- Size = floor(current NAV x budget / (worst clean prior one-unit policy MAE x stress multiple)); current entry depth caps whole units.
- Full-to-expiry loss including QQQ=0 is separately output; the MAE sizing rule does not cap that tail exposure.
- Forced-delay stress blocks displayed short-leg ask size after the DTE<=7 signal while leaving prices unchanged. This is a stress scenario, not a probability.
- Missing marks are never forward-filled and do not qualify for MAE training. MaxDD is not a PASS/FAIL filter.

## Highest historical ending-NAV rows (inspection only)

| Start NAV | Structure | Policy | Delay | Stress | Budget | Executed | Ending NAV | CAGR | MaxDD | Target | Terminal loss/current NAV |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_RETAIN_RESIDUAL_LONG | 5 | 1.0x | 100% | 49 | USD 1,822,690.50 | 8.01% | -18.66% | NO | 2590.38% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 5 | 1.0x | 100% | 49 | USD 1,822,690.50 | 8.01% | -18.66% | NO | 2590.38% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_RETAIN_RESIDUAL_LONG | 5 | 1.0x | 75% | 49 | USD 1,806,666.00 | 7.89% | -15.37% | NO | 2616.49% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 5 | 1.0x | 75% | 49 | USD 1,806,666.00 | 7.89% | -15.37% | NO | 2616.49% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_RETAIN_RESIDUAL_LONG | 5 | 1.5x | 100% | 49 | USD 1,796,298.20 | 7.81% | -13.68% | NO | 2422.62% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 5 | 1.5x | 100% | 49 | USD 1,796,298.20 | 7.81% | -13.68% | NO | 2422.62% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 2 | 1.0x | 100% | 49 | USD 1,790,095.70 | 7.76% | -18.72% | NO | 2622.43% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 3 | 1.0x | 100% | 49 | USD 1,788,816.15 | 7.75% | -18.72% | NO | 2645.16% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 2 | 1.0x | 75% | 49 | USD 1,773,715.10 | 7.63% | -15.35% | NO | 2649.80% |
| NAV 1,000,000 | ORIGINAL_1_LONG_5_SHORT | DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE | 3 | 1.0x | 75% | 49 | USD 1,772,435.55 | 7.62% | -15.34% | NO | 2673.01% |

Top rows are grid-search results on previously examined data, not recommendations. The option chain ends 2025-12-15; EOD side quotes are not confirmed fills; exact timestamp, intraday MAE, market impact, margin, assignment and forced liquidation are not authenticated or fully modeled. A 100% budget is a sensitivity point, not an approved risk level. No App, main branch, Frozen Hybrid sizing or order permission changes.
