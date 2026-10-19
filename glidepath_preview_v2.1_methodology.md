# Glidepath Preview v2.1 — quantitative definitions and limits

## What the interface is measuring

- The embedded replay contains 768 strategy settings, 8,448 annual summaries (years 0–10), 3,072 histogram summaries and 10,752 start-calendar-year cohort rows.
- Each displayed strategy uses 157 overlapping 10-year historical windows. Because the windows overlap, counts and percentiles are descriptive historical summaries, **not 157 independent trials and not a future probability estimate**.
- The underlying replay describes a 50/50 QQQ/SPY equity sleeve rebalanced along the chosen annual stock-to-bond glidepath, with AGG, SHY, IEF or TLT as bond ETF proxies. The common adjusted-close sample is 2003-09-29 to 2026-09-30. It does not include the 2000–2002 dot-com collapse.
- The adjusted-close history approximates reinvested distributions and splits. It is not a complete live-investing ledger. Taxes, bid/ask spreads and transaction costs are not independently modeled here.

## Inflation control

The control is an **annualized inflation scenario**, not actual CPI and not a forecast. The 2.35% preset references FRED's daily 10-year breakeven inflation rate (T10YIE) observation dated 2026-10-16. That metric is a market-derived inflation compensation proxy, not a promise that realized CPI will equal 2.35%:
https://fred.stlouisfed.org/series/T10YIE

For year t, displayed purchasing-power NAV is:

realNAV(t) = nominalNAV(t) / (1 + assumedInflation)^t

Displayed real annualized return is calculated as:

realCAGR = (1 + nominalCAGR) / (1 + assumedInflation) - 1

These are deterministic scenario conversions. They do not alter the historical market path. The 3.50% choice is a stress assumption, not market data.

## What is deliberately not claimed

1. The existing annual summary stores the count of windows below nominal $100,000, not the count below an inflation-adjusted threshold. The interface labels that count as nominal and does not relabel it as a real purchasing-power failure rate. A real breach count requires year-by-year NAV for each rolling window, not just aggregate percentiles.
2. Withdrawal and shortfall dollars remain nominal. Those flows occur on different dates, so converting the sum with a single end-of-horizon inflation divisor would be inaccurate. The current data package does not preserve enough event-level detail to calculate each flow's purchasing power exactly.
3. STRIPS/TIPS are **not a modeled strategy in this dashboard**. Previous fixed claims such as a guaranteed $100,000 floor and a $182,270 expected terminal value are removed. Such a comparison must separately specify maturity, purchase price/yield, face value, TIPS inflation mechanics, timing, equity allocation, taxes and costs before it can be compared fairly with ETF total-return history.
4. The “highest P05” and “shallowest median drawdown” controls rank the 48 settings for the selected bond proxy, cash-flow mode and year using the same historical sample displayed on screen. They are in-sample rankings, not a validated out-of-sample optimizer and not recommendations that one setting will be best in the future.
5. Summary quantiles are shown only where the underlying dataset has them. Asset, drawdown and return chart selectors are separate because this data package does not provide one universally available percentile for every metric.

## Current acceptance status

The independent test suite checks HTML ID uniqueness, JavaScript syntax, compact-data counts, histogram conservation, cohort coverage, scenario/year-10 reconciliation, metric-selector routing, nominal-vs-real wording and removal of unmodeled STRIPS guarantees. A passing static-data test does **not** constitute a real-browser visual regression or interaction test.

The repository's older glidepath_interactive_preview_optimized_bundle.zip is stale until regenerated from the current v2.html. Use the standalone v2.html from this branch only as a review candidate; do not treat the old archive as the same build.
