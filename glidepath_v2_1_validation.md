# Glidepath preview v2.1 — independent validation

## Changed
- P05 drawdown and worst-window annualized return now show explicit missing-data messages instead of median values.
- Nominal capital-floor counts remain explicitly nominal; real-mode KPI/heatmap/cohort charts do not present them as real-loss counts.
- The 2.35% setting is an annualized inflation assumption. FRED T10YIE is cited as a dated market-implied anchor (2026-10-16: 2.35%), not realized CPI or a guaranteed forecast.
- Removed the static STRIPS/TIPS weights, fixed $182,270 terminal value, and guaranteed-hard-floor phrasing pending a comparable cashflow model.
- Regenerated the downloadable ZIP from the exact v2.1 HTML.

## Checks run in this update
- Parsed inline JavaScript without running browser-dependent code.
- Confirmed unique HTML IDs.
- Re-parsed embedded data: 768 unique scenario keys, 8,448 unique annual keys, 3,072 histogram summaries, and 10,752 cohort rows.
- Compared 768 year-10 summaries to annual-table values across the available NAV percentiles, CAGR percentiles, drawdowns, nominal below-capital counts and shortfall counts: zero mismatches.
- Confirmed every histogram's bins sum to 157 overlapping windows.
- Recompressed the HTML and inflated it in memory; decompressed bytes match HTML SHA-256 and CRC-32.

## Not claimed as passed
- No new headless-browser interaction run after this patch; slider interaction, CSV download events, responsive layout and rendered SVG geometry remain to be retested.
- Exact real-purchasing-power breach counts need per-window NAV paths or a fresh replay.
- STRIPS/TIPS floor and terminal-value calculations remain unmodeled and must not be presented as guarantees.

## Current artifacts
- v2.html is the canonical HTML source.
- glidepath_interactive_preview_optimized_bundle.zip contains the same v2.1 HTML as glidepath_interactive_preview_optimized.html.
- Machine audit status: STATIC_SEMANTIC_GUARDS_PASSED_BROWSER_RETEST_PENDING.


## Reverse direction v1 — independent historical replay

- Added a separate direction selector: **先股後債** remains the existing 768-strategy summary; **先債後股** constructs a distinct annual target path (year 0 starts at 100% bonds / 0% stocks, ending at the selected year-10 stock target).
- Reverse performance is recalculated from the repository's SPY/TLT daily adjusted-close series in `src/data/universe.json`; it is not calculated by inverting CAGR, drawdown, or principal-floor counts from the forward-direction summaries.
- The standalone HTML embeds the SPY/TLT data snapshot with its source SHA-256. A jointly missing SPY/TLT row is dropped as a non-trading/missing row; unmatched or invalid price rows fail the build rather than being filled with zero returns.
- The first replay scope is deliberately limited to **SPY + TLT**, **no withdrawals or contributions**, an initial $100,000 NAV, annual rebalancing, 252 trading days per year, and 157 full 10-year overlapping windows (start index 60, stride 20). It does not include trading costs, tax, slippage, or ETF-tracking effects.
- Selecting a bond proxy other than TLT or a cashflow mode other than no-withdrawal displays **BLOCK** rather than presenting unverified performance.
- This is a historical exploratory replay, not a guarantee or a claim that TLT is interchangeable with AGG, SHY, or IEF.


## Reverse direction v2 — same-window paired comparison

- The UI compares mirrored **stock-to-bond** and **bond-to-stock** schedules using the exact same 157 overlapping 10-year start/end windows, the same SPY/TLT adjusted-close observations, same $100,000 initial NAV, same annual rebalancing rule, same inflation assumption, and no deposits or withdrawals.
- The comparison shows nominal and real terminal NAV summaries, P05 real NAV, nominal/real CAGR, median and worst maximum drawdown, the median year in which the maximum drawdown first occurs, and real-principal threshold counts.
- Paired per-window wins (real terminal NAV and maximum drawdown) are kept separate from differences between aggregate medians/percentiles. The pairwise sample is overlapping historical windows, not independent future probabilities.
- Unsupported bond proxies or cashflow modes remain BLOCKED; the comparison is not silently copied from legacy summary metrics.

- The machine audit captures a distinct 2.35% annualized-inflation paired snapshot as well as the nominal (0% inflation) snapshot.
- The UI exposes the maximum-drawdown occurrence-year distribution for years 1–10 and the browser audit checks that each direction's year counts sum to the 157 matched windows.
