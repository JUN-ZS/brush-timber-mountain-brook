# DTE20 single-position replay — exit after 10 sessions

- Period requested: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Entry schedule: every common-session opportunity; no entry filter; new entry blocked while this policy's position remains open.
- Option legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; shared expiry; selected expiry DTE 17–23, target 20.
- QQQ selection: absolute Delta target 0.65 ± 0.05; within-band QQQ ask matched nearest to 6 × selected SPY put bid.
- Exit rule: signal exit at holding age 10 trading sessions, then close only when exact selected contracts have executable displayed-side quotes; missing exits are reported unresolved.
- Costs: slippage USD 0.05 per option-share per side; commission USD 0.65 per contract per side.

## Historical quote-side results

| Metric | Result |
|---|---:|
| Entered cohorts | 163 |
| Resolved episodes | 149 |
| Unresolved episodes | 14 |
| Win rate (resolved only) | 85.23% |
| Mean net P&L per resolved trade | USD -87.35 |
| Median net P&L per resolved trade | USD 484.90 |
| Cumulative net P&L across resolved trades | USD -13,014.90 |
| Annual average of resolved trade P&L sum | USD -1,670.31/year |
| Worst resolved trade | USD -29,275.10 (-29.28% of USD 100k reference NAV) |
| Profit factor | 0.889196 |

## Interpretation and exclusions

This is a sequential single-position replay of the QQQ/SPY option legs, not a portfolio-account simulation. The USD 100,000 NAV is a reference denominator only; the engine does not impose buying-power, margin, assignment-funding, forced-liquidation, financing, tax, or compounding constraints, so the annual average above is not CAGR or a verified account return.

**Far-OTM TAIL insurance is not priced in this base run.** No tail option quantity, expiry/Delta rule, or roll/hold policy is encoded in this isolated timing comparison. Do not read these figures as the net result after paying for tail insurance.

Historical EOD displayed bid/ask quotes are conservative quote-side marks, not verified fills. The exact contract IDs, quote-size gate, unresolved trades, entry skips, and source-integrity manifest are retained in the sibling CSV/JSON outputs.

## DTE20 configuration

- Requested DTE window: 17–23, target 20; one common expiry required.
- Overlapping cohorts enabled: False.
- QQQ Delta band: [0.6, 0.7000000000000001].
