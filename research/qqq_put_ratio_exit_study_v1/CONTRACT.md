# QQQ 1x5 Put Ratio — Exit Rule Measurement Contract V1

**Status:** research-only, not a live trade recommendation, no app sizing-policy change.

## Question and payoff

Measure whether exit timing changes a fixed structure of 1 long higher-strike QQQ put and 5 short lower-strike QQQ puts, same expiry. Test, rather than assume, whether a $1,000 exit threshold is useful; whether reaching +$1,000 within five holding sessions predicts giveback; and whether a non-positive mark on holding-session 20 predicts later outcomes.

For long strike KL, short strike KS < KL, entry net cash C (credit positive), expiry QQQ price S and standard 100 multiplier:

P&L(S) = C + 100 × [max(KL − S, 0) − 5 × max(KS − S, 0)].

At S=0 this is C + 100 × (KL − 5KS). One long put only offsets one of five short puts. This payoff arithmetic does not cap interim volatility, margin-call or forced-liquidation risk.

## Frozen data and entry convention

- Source window 2018-03-01 through the last verified QQQ option-chain snapshot on 2025-12-15. The requested history ended 2025-12-31, but the last 11 expected sessions lacked the source coverage needed by the existing QQQ history.
- Data files, repo source and contract universe are SHA-verified by the reused loader from the existing QQQ EOD audit. Public mirror README reports a 16:00 US/Eastern snapshot; exact tick timestamp and confirmed fills are not available.
- On session t, choose only actual standard-root QQQ put contracts at the same expiry, 30–60 calendar DTE (target 45); long absolute Delta nearest .30 in [.20,.40], short absolute Delta nearest .10 in [.04,.16], and long strike greater than short. This is a fixed research convention, not an optimized signal.
- Entry is no earlier than session t+1 and uses only the same exact contract IDs; long enters at Ask and five short puts at Bid. Require adequate displayed size; if quotes or depth fail, skip rather than replace a leg.
- Episodes do not overlap. Every exit rule gets the same fixed one-unit entry cohort. This isolates exits; it is not a continuously reinvested portfolio replay.
- Friction sensitivity per leg per side: $0, $0.025, $0.05, $0.10; commission sensitivity per contract per side: $0 or $0.65. These are hypothetical cost scenarios, not broker-confirmed charges.

## Preregistered exit comparisons

1. Baseline: signal close of short risk when DTE <= 7.
2. Signal close of short risk at net liquidation mark >= $500 / $1,000 / $2,000.
3. Signal close at 25% / 50% of modelled maximum terminal profit.
4. If first EOD mark >= +$1,000 occurs within the first five holding sessions, signal a one-time trim of four short puts; leave one long put and one short put.
5. At holding-session 20, if net EOD liquidation mark <= $0, compare full short-risk closure with trimming four shorts.
6. Signal close at net mark <= -$500 / -$1,000 / -$2,000.
7. All rules inherit the DTE<=7 safety boundary if their own rule did not fire. EOD creates the signal; execution must be a later observed session with valid side quote and sufficient Ask size to buy back shorts. No same-close fill assumption and no forward-filled quotes. Missing execution quotes can defer an action.

## Required measurement

Per policy: number of episodes, resolved/unresolved, total P&L USD and percentage of a $100,000 reference NAV only, expectancy, median, win rate, profit factor, best/worst trade, mark coverage, deferred actions and full cost grid.

Risk: entry net cash; P&L at QQQ=$0; terminal tail loss in USD and % reference NAV; reward-to-tail-loss ratio; illustrative whole-unit counts at 0.5% / 1% / 2% terminal-tail budgets. These counts are not broker capacity or margin approval.

Event studies: first EOD mark >= +$1,000 within 5 sessions versus later, with subsequent 5/10-session P&L changes and giveback; at session 20 compare non-positive versus positive groups and subsequent recovery/further-loss. Missing marks are unknown/censored, never assumed flat.

$1,000 equals 1% of the reference $100,000 NAV, but no round-dollar target is assumed optimal. A quick +$1,000 is a warning only if the conditional forward data supports it. Day-20 non-positive is not a directional forecast without measured cohort evidence.

## Time-to-harvest measurement (descriptive, not an optimizer)

For each exit policy, publish the following on the identical fixed entry cohort:

**Age convention:** the entry-date EOD observation is session age 0. Each subsequent observed market session increments age by one. Therefore the day-20 threshold is checked after 20 observed-session transitions from entry (the 21st quote row when counting the entry observation), and a signal can only execute on a later valid observation.


- Custom policy trigger count and rate, separately from the shared mandatory DTE<=7 safety fallback.
- Median/mean observed-session age at the first custom trigger, age at first successful risk-reducing action, signal-to-action delay in observed market sessions, and age when the episode finally resolves.
- Count of short-risk-equivalent exposure sessions: on each observed replay session, add remaining short contracts / the original five short contracts. This captures whether a four-of-five trim reduces subsequent short exposure to 0.2 of the original unit, but is not capital, margin or complete portfolio risk.
- Resolved net P&L divided by total short-risk-equivalent exposure sessions, alongside (never instead of) net expectancy, win rate, profit factor, worst trade, missing marks, deferred actions, mark coverage, and terminal tail-loss measurements.
- Keep unresolved episode and exposure counts visible. A delay means observed market sessions from signal to the first successful action; it is not wall-clock time and does not assert an executable intraday fill.
- These time-normalized fields are descriptive only. Do not pick the highest P&L/session as the best policy: early closes can mechanically shrink the denominator, tail loss and drawdown can dominate the ratio, and the historical sample is previously inspected DEVELOPMENT/REVISIT data.

## Promotion gates

- Accuracy: standard contract identity/expiry/strike/right, actual listed contract IDs, conservative entry/exit sides, costs charged to all six contracts, no same-close fill, no forward fill, source hashes and terminal date verified.
- Generality: disclose counts and coverage; small event subgroups remain inconclusive. 2018–2025 was already inspected in prior research; this is DEVELOPMENT/REVISIT, not a virgin holdout.
- Value: do not select by gross total profit alone. Compare after-cost expectancy, profit factor, worst loss, tail loss, giveback, mark coverage, deferred actions and sensitivity across costs.
- Integration: no changes to app, Frozen Original Hybrid, main branch, live sizing or broker-order permissions.
- Deployment remains BLOCKED without intraday decision/fill data, broker margin/assignment requirements and a complete tail-risk treatment.
