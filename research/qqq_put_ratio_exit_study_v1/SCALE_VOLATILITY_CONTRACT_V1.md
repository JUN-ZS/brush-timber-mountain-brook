# QQQ Put Ratio: Scale × Exit × Volatility/Time — V1 contract

Status: independent research only. No APP sizing policy, Frozen Original Hybrid, main branch, live sizing or broker-order permission changes.

## Measurement scope
- SHORT_HEAVY_1_LONG_N_SHORT = buy one higher-strike put and sell N lower-strike puts.
- LONG_HEAVY_N_LONG_1_SHORT = buy N higher-strike puts and sell one lower-strike put.
- N=1 is mechanically the same 1-long/1-short position under either label, not two independent ideas.
- Unit counts use the worst observed one-unit expiry loss in this previously inspected cohort; this is a retrospective sizing sensitivity, not a live capacity guarantee.
- N=1–6; reference NAVs $100,000 and $1,000,000. Thresholds are 0.5%, 1%, 2% NAV: $500/$1,000/$2,000 at $100k and $5,000/$10,000/$20,000 at $1m.
- Use the same listed-contract cohort. If displayed size cannot support the ratio multiplied by selected whole units, exclude the episode and retain the skipped count. Do not substitute legs or forward-fill marks.
- Policy replay is scaled by whole ratio units derived from each NAV and tail-risk budget; entries are filtered again by displayed size for the entire position.
- Cost cases: zero-friction bound, $0.05 per leg/side + $0.65 per contract/side, and $0.10 + $0.65. Hypothetical sensitivities only.

## Payoff and exits
- Calculate terminal payoff at QQQ=0, short strike, long strike and above long strike. Worst loss is the lowest payoff knot; it is not always the QQQ=$0 payoff, particularly for N=1.
- Report median/P95/worst observed terminal loss and whole-unit risk budgets for 0.5/1/2% NAV. Counts are terminal payoff arithmetic, not broker margin or interim liquidation capacity.
- DTE ≤7 is the shared short-risk fallback.
- Profit targets at 0.5/1/2% NAV full-close the position.
- If first target hit within holding session 3 or 5, compare full close versus short-risk trim. Short-heavy N>1 trims to one residual short; N=1 removes the short; long-heavy closes the single short but keeps the N long puts.
- At session 20 with non-positive liquidation mark: compare full close vs the same short-risk trim.
- Loss stops at 0.5/1/2% NAV full-close. EOD signal executes no earlier than a later observed session. Missing quote/size defers action; it does not count as a success.

## Volatility × time probability
- Use source-pinned QQQ raw closes through 2025-12-15; horizons 1/3/5/10/20/30/45 observed sessions.
- Conditional groups use trailing 20-session annualized realized volatility (<15%, 15–25%, 25–35%, ≥35%) or VIX groups (<15, 15–25, 25–35, ≥35). Only use information known at the starting close.
- Report empirical P(up), P(drop ≥3/5/10%), P(up ≥5%), quantiles, sample size, nominal Wilson range and non-overlapping-offset sensitivity for the 5% drop. Overlapping horizons are dependent; nominal Wilson bounds are not a literal independent-sample confidence interval.
- These are QQQ price-path frequencies, not option strategy win probabilities. Option P&L additionally depends on IV/skew, DTE, strike, spread width, displayed depth, costs and next-session action.

## Evidence gate
The public EOD preservation mirror reports 16:00 US/Eastern snapshots, but exact timestamp and fills are not authenticated. Option data ends 2025-12-15; 11 expected sessions through 2025-12-31 are missing. Prior-reviewed 2018–2025 is development/revisit data, not a blind final OOS. Live deployment remains BLOCKED pending genuinely unseen OOS, decision-time/fill evidence and broker margin/assignment/forced-liquidation treatment.

## User NAV and cost BAR
- CLI accepts any positive NAV using repeatable `--nav X` arguments; the workflow pins $100,000 and $1,000,000 as reproducible comparison cases.
- The cost BAR reconciles a theoretical midpoint P&L mark with the conservative net liquidation mark using the long-leg Bid and short-leg Ask, and includes opening-side costs, closing-side costs, slippage and commissions.
- Report the median and P95 across each episode's median observed quote-mark drag; stratify by VIX and DTE so the BAR changes with state. Compare this drag with the requested 0.5/1/2% NAV net target; show the corresponding midpoint gross mark needed, without pretending it is a fill or choosing a policy solely from this ratio.
- If required displayed size is unavailable, report unavailable/PENDING instead of a zero-cost BAR.
