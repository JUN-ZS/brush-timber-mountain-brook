# QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1

Research-only. This branch is independent of the formal 10Y Floor product and MUST NOT write funding decisions back to the app.

## Question

Does changing the timing of the same 100% principal create enough incremental deployment value to matter, and does it create true downside convexity?

## Fixed comparisons

1. CLOCK: exactly 1/120 of B is deployed at each month-end for 120 months.
2. DIP_10_12M_ONE_SLICE: at each month, if QQQ is at least 10% below its trailing 12-month high, move exactly one future clock slice into the current month. The move is taken from the latest month that still contains an undistributed slice. No future price is read.
3. ORACLE_2X_CEILING: hindsight upper bound only. At most 2/120 of B may be deployed in any month; the 120 slices are allocated to the lowest-price months using the fully known 10Y window. This is NOT an executable strategy and is included only to measure the maximum timing capacity under a simple deployment cap.

No parameter search is allowed in V1. There is no ranking and no champion.

## Deployment accounting

For every complete rolling 10Y QQQ window:

- Total planned capital is exactly 1.0 B for every strategy.
- Each monthly contribution buys QQQ at that month's observed close.
- Terminal wealth is the sum of each deployed fraction multiplied by terminal-price / entry-price.
- Monthly portfolio equity is marked at each month-end.
- MaxDD is measured on that monthly equity curve.
- All windows overlap; they are diagnostics, not independent observations.

## Convexity test

For each window and selected shock month, rerun the same precomputed deployment schedule under a permanent one-month level shock of 0%, -10%, -20%, -30% applied from the shock month through the end.

Two readings are reported:

- FROZEN_SCHEDULE_CURVATURE: the deployment schedule is held fixed while the price path is shocked. A pure long/cash timing strategy should be affine in a permanent level shock; curvature should therefore be numerically near zero.
- PATH_AWARE_DIP_CURVATURE: the DIP rule is allowed to react to the shocked path. Any non-zero curvature here is policy/path dependence, not instrument convexity.

The research therefore distinguishes deployment value from true non-linear payoff convexity.

## Evidence gate

V1 does NOT search for a parameter set that passes a target.

The first questions are only:

- Is median / mean DIP incremental terminal wealth positive versus CLOCK?
- Is the effect economically material across the full distribution?
- How large is the ORACLE_2X timing ceiling?
- Does frozen-schedule downside curvature remain approximately zero?
- Does any path-aware curvature come only from the deployment rule changing exposure?

A positive answer to deployment value does not prove a funding rule. A positive answer to path-aware curvature does not prove option-like convexity.

## Data

Canonical repository QQQ observed daily series: src/data/universe.json

No future data beyond each rolling window is used by the executable strategies. The ORACLE is explicitly hindsight and is never presented as an OOS strategy.

## Output

The runner writes qqq_hybrid_downside_convexity_v1.json, qqq_hybrid_downside_convexity_v1.csv, and qqq_hybrid_downside_convexity_v1.md.

Status labels are RESEARCH_ONLY / DIAGNOSTIC_ONLY.