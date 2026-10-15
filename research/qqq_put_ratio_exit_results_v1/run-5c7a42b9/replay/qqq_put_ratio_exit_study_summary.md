# QQQ 1x5 Put Ratio Exit Measurement — V1

**Status:** `DEVELOPMENT_DIAGNOSTIC_NOT_LIVE_APPROVAL`  
**Window:** 2018-03-01 to 2025-12-15 (requested end 2025-12-31; source is incomplete after Dec 15, 2025)  
**Evidence:** public EOD preservation mirror / conservative quote-side replay; not confirmed fills.  
**Entry episodes:** 62; selection skips: {}

## Frozen test definition

- On session *t*, choose one standard QQQ put near abs(Delta) 0.30 and five standard lower-strike puts near abs(Delta) 0.10, same expiry, 30–60 DTE (target 45).
- Use exact listed contract IDs at *t+1* for entry; long buy at Ask, five shorts sold at Bid; if quote/depth is invalid, skip rather than replace the legs.
- Exit actions are based on EOD side marks only. Short-put closure buys back at Ask; risk-trim buys back four of five shorts and leaves a 1x1 defined-risk vertical. A residual long put can remain open if no positive Bid is available.
- Same entry episodes for every rule, non-overlapping by expiry, fixed one-unit sizing. This isolates exit-rule effects; it is not a continuous re-entry portfolio simulation.
- Session age is the observed replay index since entry (entry-date mark is age 0). The policy-trigger count/rate distinguishes a custom rule firing from the shared DTE<=7 safety fallback; signal-to-action delay counts observed trading sessions to the first successful risk-reducing action.
- Net P&L per short-risk-equivalent session divides resolved after-cost P&L by the sum of each observed session weighted by remaining short contracts / original five shorts. This is a descriptive holding-time denominator only—not annualized return, risk-adjusted return, or a substitute for the tail-loss / mark-coverage / cost gates.

## Base cost case: $0.05 per leg per side + $0.65 per contract per side

| Exit rule | Resolved | Net P&L | Expectancy / trade | Policy trigger N / % | DTE7 fallback N | Median trigger age | Median first-action age | Median resolution age | Net P&L / short-risk eq-session | Win rate | Profit factor | Missing marks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BASE_DTE7_CLOSE_SHORT_RISK | 62/62 | 18067.6 | 291.41 | 0/62 (0.0%) | 62 | — | 1.0 | 25.5 | 10.871 | 0.951613 | 19.428805 | 12 |
| TP_USD_500_CLOSE_SHORT_RISK | 62/62 | 14199.6 | 229.03 | 16/62 (25.81%) | 46 | 19.0 | 1.0 | 24.0 | 9.0042 | 0.935484 | 7.347041 | 12 |
| TP_USD_1000_CLOSE_SHORT_RISK | 62/62 | 18067.6 | 291.41 | 3/62 (4.84%) | 59 | 23.0 | 1.0 | 25.5 | 10.871 | 0.951613 | 19.428805 | 12 |
| TP_USD_2000_CLOSE_SHORT_RISK | 62/62 | 18067.6 | 291.41 | 0/62 (0.0%) | 62 | — | 1.0 | 25.5 | 10.871 | 0.951613 | 19.428805 | 12 |
| TP_25PCT_MAX_TERMINAL_GAIN | 62/62 | 17220.6 | 277.75 | 7/62 (11.29%) | 55 | 21.0 | 1.0 | 24.5 | 10.4557 | 0.951613 | 18.564871 | 12 |
| TP_50PCT_MAX_TERMINAL_GAIN | 62/62 | 18067.6 | 291.41 | 0/62 (0.0%) | 62 | — | 1.0 | 25.5 | 10.871 | 0.951613 | 19.428805 | 12 |
| FAST_1000_WITHIN_5D_TRIM_4_SHORTS | 62/62 | 18067.6 | 291.41 | 0/62 (0.0%) | 62 | — | 1.0 | 25.5 | 10.871 | 0.951613 | 19.428805 | 12 |
| DAY20_NONPOSITIVE_CLOSE_SHORT_RISK | 62/62 | 10789.6 | 174.03 | 10/62 (16.13%) | 52 | 20.5 | 1.0 | 24.0 | 6.6357 | 0.903226 | 2.636573 | 11 |
| DAY20_NONPOSITIVE_TRIM_4_SHORTS | 62/62 | 9568.6 | 154.33 | 10/62 (16.13%) | 52 | 20.5 | 1.0 | 25.5 | 5.8581 | 0.854839 | 2.205842 | 12 |
| SL_USD_500_CLOSE_SHORT_RISK | 62/62 | 751.6 | 12.12 | 20/62 (32.26%) | 42 | 5.0 | 1.0 | 24.0 | 0.5817 | 0.709677 | 1.075172 | 11 |
| SL_USD_1000_CLOSE_SHORT_RISK | 62/62 | 14.6 | 0.24 | 10/62 (16.13%) | 52 | 6.0 | 1.0 | 24.0 | 0.0098 | 0.83871 | 1.001094 | 11 |
| SL_USD_2000_CLOSE_SHORT_RISK | 62/62 | -5325.4 | -85.89 | 6/62 (9.68%) | 56 | 10.5 | 1.0 | 24.0 | -3.3578 | 0.870968 | 0.737295 | 12 |

## Tail-risk and dollars-to-risk ratio

- Median terminal loss if QQQ reaches $0: **$106392.4** (106.3924% of the $100,000 reference NAV).
- Maximum observed selected-trade terminal loss if QQQ reaches $0: **$214696.9** (214.6969% of reference NAV).
- Median reference NAV needed for one 1x5 unit to fit a 1% terminal tail-risk budget: **$10639240.0**. This is terminal payoff arithmetic, not a broker margin figure.
- $500 / $1,000 / $2,000 are also 0.5% / 1% / 2% of the $100,000 reference NAV, but those profit/loss thresholds are not inherently optimal. Compare each against the much larger terminal tail loss and the after-cost trade distribution.

## Conditional event study (base costs; EOD marks)

- First EOD mark at +$1,000: 9 events; within 5 sessions: 0; later than 5 sessions: 9.
- Early +$1,000 then hold the original 1x5: {"5_session_forward": {"n": 0, "median_pnl_change_usd": null, "mean_pnl_change_usd": null, "fraction_future_pnl_nonpositive": null, "fraction_pnl_giveback_ge_50pct_of_1000_target": null, "future_pnl_distribution_usd": {"n": 0, "mean": null, "median": null, "p05": null, "p95": null}}, "10_session_forward": {"n": 0, "median_pnl_change_usd": null, "mean_pnl_change_usd": null, "fraction_future_pnl_nonpositive": null, "fraction_pnl_giveback_ge_50pct_of_1000_target": null, "future_pnl_distribution_usd": {"n": 0, "mean": null, "median": null, "p05": null, "p95": null}}}
- Day-20 non-positive then hold the original 1x5: {"5_session_forward": {"n": 5, "median_pnl_change_usd": 332.0, "mean_pnl_change_usd": 278.2, "fraction_future_pnl_nonpositive": 0.2, "fraction_pnl_giveback_ge_50pct_of_1000_target": 0.0, "future_pnl_distribution_usd": {"n": 5, "mean": 235.8, "median": 207.2, "p05": -2.8, "p95": 644.2}}, "10_session_forward": {"n": 2, "median_pnl_change_usd": 21.825, "mean_pnl_change_usd": 21.82, "fraction_future_pnl_nonpositive": 0.0, "fraction_pnl_giveback_ge_50pct_of_1000_target": 0.0, "future_pnl_distribution_usd": {"n": 2, "mean": 17.025, "median": 17.025, "p05": 1.85, "p95": 32.2}}}
- Day-20 positive comparison group: {"5_session_forward": {"n": 56, "median_pnl_change_usd": 3.150000000000002, "mean_pnl_change_usd": -131.89, "fraction_future_pnl_nonpositive": 0.0714, "fraction_pnl_giveback_ge_50pct_of_1000_target": 0.0357, "future_pnl_distribution_usd": {"n": 56, "mean": 138.8812, "median": 175.7, "p05": -53.8, "p95": 876.2}}, "10_session_forward": {"n": 28, "median_pnl_change_usd": 20.650000000000013, "mean_pnl_change_usd": 125.84, "fraction_future_pnl_nonpositive": 0.0, "fraction_pnl_giveback_ge_50pct_of_1000_target": 0.0, "future_pnl_distribution_usd": {"n": 28, "mean": 394.2536, "median": 194.65, "p05": 60.1, "p95": 2186.2}}}

## Decision gates

- **No `WIN $1,000` rule is accepted just because it is round.** Compare after-cost expectancy, giveback after threshold, risk reduced by closing/trim, action execution coverage, and return per unit of tail loss.
- **A +$1,000 EOD mark within 5 sessions is not automatically a warning.** It is a warning only if the event cohort shows systematically worse subsequent giveback / loss than later +$1,000 events, with enough observations and consistent quote coverage.
- **No profit by day 20 is not automatically bearish or failure.** It is informative only if the 5-/10-session forward conditional outcomes differ from trades already profitable on day 20. Missing marks are censored, not assumed flat.
- Deployment gate: **BLOCKED_FOR_DEPLOYMENT: EOD timing/fills unverified, broker margin/assignment costs unavailable, one-unit 1x5 tail risk may exceed reference NAV, and history is previously inspected development data.**

## Data integrity / caveats

- This is a short-ratio put structure: one higher-strike long put only offsets one of the five lower-strike short puts. The remaining four short puts create severe downside exposure.
- Zero-underlying tail loss is terminal intrinsic arithmetic; it does not model interim volatility expansion, margin calls, forced liquidation, execution gaps, or broker-specific margin.
- All exit triggers are EOD quote-mark rules; the dataset does not establish intraday touches or fills.
- Missing option marks are never forward-filled. A missing quote can defer a close action; unresolved trades do not enter closed-P&L totals.
- Intrinsic expiry settlement is a proxy before broker exercise/assignment fees, taxes, or operational frictions.
- No app capacity, Frozen Original Hybrid, main branch, or broker-order permission was modified.
