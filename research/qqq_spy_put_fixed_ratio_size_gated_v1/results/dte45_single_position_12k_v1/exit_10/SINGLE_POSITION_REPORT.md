# DTE45 single-position replay — 10

- Period requested: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Entries: check every common underlying session; no market signal filter; a new cohort is blocked while the previous cohort is active.
- Legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry required.
- Selection: expiry DTE 30–60, target 45; both puts selected nearest absolute Delta 0.25 among eligible contracts.
- Exit rule: Exit after 10 trading sessions.
- Costs: slippage USD 0.05 per option-share per side; commission USD 0.65 per contract per side.

## Historical quote-side results

| Metric | Result |
|---|---:|
| Eligible daily opportunities | 1,959 |
| Entered cohorts | 162 |
| Resolved episodes | 160 |
| Unresolved episodes | 2 |
| Win rate (resolved only) | 73.75% |
| Mean net P&L per resolved trade | USD 141.25 |
| Median net P&L per resolved trade | USD 752.40 |
| Cumulative net P&L across resolved trades | USD 22,600.00 |
| Annual average of resolved trade P&L sum | USD 2,900.44/year |
| Worst resolved trade | USD -27,025.10 (-27.03% of USD 100k reference NAV) |
| Profit factor | 1.168643 |
| Average SPY short-put assignment obligation per cohort | USD 238,368.52 |

## Limits and interpretation

This is a sequential, one-open-cohort replay of the QQQ/SPY option legs. It deliberately does not import P&L from the overlapping cadence grid.

USD 100,000 is only a reference NAV for displaying the worst resolved trade as a percentage; this run does not constrain buying power, margin, assignment funding, forced liquidation, financing, tax, or compounding. The annual average above is an additive resolved-trade P&L sum divided by calendar years, not account annual profit or CAGR.

**Far-OTM TAIL insurance is not priced in these baseline runs.** No tail contract quantity, DTE/Delta rule, or roll policy is assumed. The results must not be read as net of TAIL premiums.

Historical EOD displayed bid/ask quotes are conservative quote-side estimates, not verified fills. If the exact selected contract cannot be closed with eligible displayed size, the engine defers the close and records unresolved cases rather than inventing a fill. Source integrity is recorded in source_manifest.json.
