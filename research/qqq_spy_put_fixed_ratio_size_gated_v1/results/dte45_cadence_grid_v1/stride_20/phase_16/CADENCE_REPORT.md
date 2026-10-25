# DTE45 overlapping cadence replay — stride 20, phase 16

- Window: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Fixed cadence: one entry opportunity every 20 common sessions, phase 16.
- Overlapping cohorts: enabled; the historical engine does not impose an account-level maximum-active-position or buying-power limit.
- Legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry required; each leg selected nearest abs Delta 0.25.
- Expiry selection: DTE 30–60, target 45; no market entry filter.
- Exit policy: HOLD_20_OR_DTE_LE_7.
- Costs: USD 0.05/option-share/side slippage + USD 0.65/contract/side commission.

## Historical quote-side results

| Metric | Result |
|---|---:|
| Entered cohorts | 98 |
| Resolved episodes | 96 |
| Unresolved episodes | 2 |
| Win rate (resolved only) | 83.33% |
| Mean net P&L per resolved trade | USD 658.74 |
| Median net P&L per resolved trade | USD 1,402.90 |
| Cumulative net P&L of resolved trades | USD 63,239.40 |
| Annual average of resolved-trade P&L sum | USD 8,116.02/year |
| Worst resolved trade | USD -44,015.10 |
| Profit factor | 1.785733 |
| Mean SPY short-put assignment obligation per cohort | USD 239,700.00 |

## Interpretation limits

This is an additive sum of resolved trade P&L divided by calendar years, not account profit, CAGR, or a $100,000 NAV feasibility result. Unresolved trades are excluded from the reported P&L and separately counted.

The run does not simulate account cash, margin, broker buying power, assignment funding, forced liquidation, financing, taxes, dividends, or compounding. Concurrent gross SPY assignment obligations can exceed NAV substantially; they are not the same as broker margin.

Far-OTM TAIL is excluded. Historical EOD displayed-side quotes are not verified fills, and displayed-size gates do not guarantee multi-leg execution. Results must be compared across the predeclared phase matrix, not selected by the best phase.
