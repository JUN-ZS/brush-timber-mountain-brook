# Dynamic NAV x BAR Tug-of-War Contract V1

Status: research-only; deployment blocked. This adds sequential NAV compounding, BAR hit rates and daily drawdown tiers to the fixed-cohort research. It does not authorize any live Hybrid sizing change or order.

## Objective and source
- Initial NAV: USD 100,000.
- Net-profit target: USD 214,012; required ending NAV: USD 314,012.
- Window: 2018-03-01 to 2025-12-15, bounded by the pinned option quote mirror.
- The source has 62 non-overlapping option episodes with EOD quote-side estimates, not confirmed fills. Missing option marks remain null.

## Dynamic loop
Each resolved episode is added to NAV. The next entry uses the latest resolved NAV, re-calculates percent-NAV BAR levels and sizes whole ratio units from the then-current NAV. Positions do not overlap. Entry sizes are capped by displayed bid/ask size. Unresolved positions censor the rest of the NAV path rather than being assigned a fabricated cash exit.

Three sizing modes are compared:
1. PER_TRADE_TERMINAL_BUDGET: calculate whole units from current NAV times the selected risk budget divided by the current contract's expiry payoff maximum loss.
2. EXPANDING_WORST_TERMINAL_BUDGET: divide by the larger of the current expiry loss and the worst expiry-loss envelope seen among prior candidates.
3. FIXED_1_UNIT_BUDGET_BYPASS and FIXED_12_UNIT_BUDGET_BYPASS: force 1 or 12 units when displayed entry size allows it, regardless of whether they exceed the selected tail budget. These are unsafe diagnostic comparators; 12 units is a scale stress test, not an assumption of linear P&L.

## BAR and drawdown rates
For the 0.5%, 1%, 2% levels, report:
- NET_PROFIT_BAR: percent of executed episodes with at least one observed net-liquidation P&L mark at or above the NAV-relative positive line.
- NET_LOSS_BAR: percent with at least one mark at or below the NAV-relative negative line.
- FRICTION_COST_BAR: percent with midpoint-to-side-quote liquidation drag at or above the same dollar line.
All rates have episode and mark denominators, hit counts, nominal Wilson bounds for episode incidence, and sample gates. The regime file slices BAR rates by VIX and DTE for (a) all ratios under the 1% tail-budget, base-cost, per-trade-sizing branch and (b) a separate exact 1-long/5-short, fixed-1-unit, 1%-reference-level diagnostic that intentionally bypasses the terminal-loss budget. The latter measures BAR shape only and is not a sizing recommendation.
Daily portfolio NAV rates include -3%, -5%, -10%, -15%, -20%, -25%, and -30% drawdown cycle counts, cycles/year, event years, event-year share and share of valid days at or below each tier.

A zero-episode BAR row is BLOCKED/PENDING rather than 0%. Rates are historical occurrence, not forward probabilities.

## Integrity limits
- Quote-side EOD data are not confirmed fills and exact quote timestamps are unauthenticated.
- The 2018-2025 period has already been examined during development and is not blind OOS.
- Daily NAV marks are unknown while active quote prices are missing; observed drawdown may understate hidden losses.
- The terminal-payoff budget is not a broker margin, assignment or forced-liquidation model.
- The configuration grid is a search, so the number of configurations that hit the target is not a probability. Fixed-unit budget-bypass modes are not candidates for promotion when they breach the terminal-payoff budget.
- No live Hybrid policy constants, app target mutation or broker order permissions change.

## Acceptance
The dynamic test file covers optional mark-curve preservation, both DTE7 residual-long variants, whole-unit sizing/budget breaches, episode vs mark BAR hit rates, DD cycle/year rates, and a single-episode compounded NAV run. Formal acceptance requires this test, all existing research tests, the full matrix run and output-existence checks on the self-hosted runner.
