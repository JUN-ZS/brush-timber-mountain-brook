# QQQ + Options Combination Screen V1

Status: research-only, independent branch, no broker orders and no HUB/main policy changes.

## Question
Which small set of QQQ-and-option structures merits further investigation under the same dated QQQ option history, rather than assuming that the highest win rate or largest model CAGR is best?

## Prespecified candidates
1. CORE_ONLY: fixed QQQ shares equal to 42% of initial NAV; remaining cash stays uninvested.
2. CORE_PLUS_PUT_DEBIT: same QQQ core plus a defined-risk QQQ put debit vertical (long approximately 25-delta put, short lower-strike approximately 10-delta put), 18–35 DTE at next-session entry; annualized gross premium-spend budget of 2% of NAV, prorated by expected holding days for each cycle (entry DTE minus the 7-day roll threshold).
3. CORE_PLUS_CALL_CREDIT: same core plus a defined-risk QQQ call credit vertical (short approximately 16-delta call, protective higher-strike approximately 8-delta call), 18–35 DTE at entry; maximum-loss budget 0.8% of prior observed NAV.
4. CORE_PLUS_CALL_AND_PUT: both option sleeves, using the same budgets as in candidates 2 and 3. Its combined nominal risk budget is greater than either single-sleeve variant; do not describe raw CAGR as a matched-total-risk win.

The 42% share allocation and risk budgets are research normalization only and do not become current HUB targets. Put debit premiums are capped at a 2% annualized gross spend rate, prorated to planned hold days; this avoids allocating 2% of NAV repeatedly on every roll. The 1-long/5-short put ratio is deliberately not in the eligible candidate set due to its previously observed very large terminal-tail loss estimate; it may remain a separate stress/control study.

## Execution and accounting
- SHA-pinned canonical QQQ option and underlying Parquet files from lambdaclass/options_portfolio_backtester release data-v1.
- Candidate contract IDs and strikes are chosen from the prior observed session. The exact same IDs are used for next-session execution; no replacing missing legs, same-close signal/fill, interpolation, Black-Scholes pricing, or parameter optimization.
- Entry/exit use side-specific historical Bid/Ask plus an explicit friction case; marks use exact-contract bid/ask midpoints.
- BASE costs: $0.05 per option leg per share of slippage per side plus $0.65 per contract per leg per side. STRESS doubles per-leg per-share slippage to $0.10.
- Only one active vertical per sleeve; existing vertical is closed when DTE <= 7 calendar days if exact exit quotes exist. Missing quotes block the transaction and remain disclosed.
- P&L is attributed to QQQ price-only core, put-debit sleeve, and call-credit sleeve, and their sum must reconcile with NAV within $0.01 on complete marks.
- No dividends are added to QQQ core return. Mark gaps are not forward-filled. MaxDD is therefore labelled observed-mark-only and may understate risk when marks are absent.

## Comparison
Initial NAVs: $80,000 and $1,000,000. Costs: BASE and STRESS. Total design: 4 structures × 2 NAVs × 2 cost cases = 16 rows. Compare CAGR, observed-mark MaxDD, worst observed calendar-year return, worst observed daily return, sleeve P&L attribution, quote completeness, trade count, and NAV reconciliation. Do not create one weighted score or hard-code an acceptable CAGR/MaxDD threshold.

## Evidence labels
The canonical Parquet files are historical option quotes, not independently authenticated fills, and displayed depth is not verified in this experiment. These results are quote-side simulation only. Option history currently ends on 2025-12-15, so no QQQ option strategy claim extends past that date.
