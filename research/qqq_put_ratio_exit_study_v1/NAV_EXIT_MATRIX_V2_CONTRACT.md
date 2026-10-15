# QQQ Put Ratio NAV Exit Matrix V2 — Contract

Status: historical DEVELOPMENT/REVISIT research only. No live-entry approval, broker orders, Frozen Original Hybrid change or main sizing-whitelist change.

## Scope
Unify QQQ close-to-close time/volatility context with QQQ put ratio N=1–6 in two directions, NAV=$100,000/$1,000,000, 0.5%/1%/2% risk budgets and P&L thresholds, first-3/first-5 session close-all versus reduce-SHORT, and current remaining DTE≤7 baseline.

## Separate clocks
- Entry cohort: standard same-expiry QQQ puts selected from actual public EOD rows at 30–60 calendar DTE (target 45); high-strike absolute Delta nearest .30 in [.20,.40], low-strike nearest .10 in [.04,.16].
- Holding age: entry-date EOD observation age 0. First-3 / first-5 mean ages 1–3 / 1–5. EOD signals act on a later observed quote.
- DTE≤7 baseline is current remaining calendar DTE, separate from entry DTE and holding age.

## Directions and risk
- SHORT-heavy N SHORT : 1 LONG: buy one higher-strike put, sell N lower-strike puts. For N>1 residual short downside tail remains; credit does not cap risk.
- LONG-heavy N LONG : 1 SHORT: buy N lower-strike puts, sell one higher-strike put. The expiry payoff valley and theta/vega profile differ; v1 historical results do not transfer to this direction.
- Terminal loss checks underlying=$0, both strikes and a point above both strikes. Package capacity is floor(NAV risk budget / terminal max loss per package); it is NOT brokerage margin or intraday risk approval.
- Every N/orientation needs sufficient displayed entry-side size. Failed depth/contract rows are counted, never “filled” by assuming extra depth.

## Results and limits
- Compare 0.5/1/2% NAV profit targets and matching loss thresholds, first-3/first-5 full close versus trim SHORT, and DTE≤7 baseline; retain base/adverse costs, trade counts, expectancy, win rate, profit factor, worst trade, mark coverage and deferred actions.
- Underlying return probabilities are overlapping historical QQQ closes, not independent-trial forecasts or probabilities of an option package being profitable. VIX is an S&P 500 proxy, not QQQ IV.
- Data ends 2025-12-15; 11 expected terminal sessions through 2025-12-31 are missing. 2018–2025 has been previously inspected: DEVELOPMENT/REVISIT, not virgin OOS.
- Public EOD marks are not confirmed fills; interim IV/margin paths, broker margin, early assignment, forced liquidation and liquidity gaps remain unmeasured. Do not select a policy by total P&L alone.
