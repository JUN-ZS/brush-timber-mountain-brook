# QQQ_MUTUAL_CHASE_SELL_STATE_MACHINE_V1

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

## Research question

Does a fixed SELL state machine create incremental value beyond simply reducing SELL frequency under the same market-extension condition?

The answer must be isolated from threshold tuning.

## Frozen rule

SELL fraction is fixed at 10%.

The eligibility condition is exactly the previously registered POST_RUNUP rule:

- prior QQQ 6M return >= +15%;
- prior QQQ price >= 95% of trailing 12M high.

No threshold is changed in this experiment.

## State machine

1. NORMAL
   - No SELL.
   - Transition to EXTENDED_CANDIDATE when POST_RUNUP becomes true.

2. EXTENDED_CANDIDATE
   - No SELL yet.
   - If POST_RUNUP remains true at the next prior month-end, transition to ARMED.
   - If POST_RUNUP breaks, return to NORMAL.

3. ARMED
   - If prior-close NAV is above the capital target, execute one fixed 10% SELL of the prior-close surplus.
   - After that SELL, transition to COOLDOWN.
   - If the extension breaks before a SELL, return to NORMAL.

4. COOLDOWN
   - No further SELL while the same POST_RUNUP episode continues.
   - Return to NORMAL only after POST_RUNUP breaks.
   - A future SELL therefore requires a fresh extension episode.

## Why this is a state machine rather than a threshold

The state has memory.

A static rule asks:

> Is the market extended right now?

The state machine asks:

> Has the extension persisted long enough to confirm the state, and has this episode already harvested?

This adds hysteresis in two places:

- confirmation: one observation is insufficient;
- cooldown: one extension episode can produce at most one harvest.

## Fair isolation

Two strategies are run with exactly the same:

- 10% SELL fraction;
- POST_RUNUP eligibility;
- BUY-side full shortfall chase;
- reserve accounting;
- t-1 decision / t close execution.

Only one differs by adding the state-machine confirmation + cooldown.

Therefore the comparison:

STATE_MACHINE vs STATIC_POST_RUNUP

isolates the value of state memory rather than SELL fraction or market-extension definition.

## Accounting

For normalized B = 1:

C_t = B*t/120.

BUY:

max(0, C_t - NAV_(t-1)) after reusing harvested reserve first.

SELL:

0.10 * max(0, NAV_(t-1) - C_t), but only on the ARMED -> COOLDOWN transition.

Economic wealth:

NAV + planned reserve + harvested reserve.

External contribution must remain <= B and no borrowing is allowed.

## Causality

Decision at month t uses only t-1 month-end observations.

Execution occurs at t month-end close.

No future price is read to decide or size the trade.

No ranking, optimization, or post-result threshold search is permitted.

## Primary evidence

1. Incremental terminal economic wealth vs STATIC_POST_RUNUP.
2. Incremental raw account MaxDD vs STATIC_POST_RUNUP.
3. Incremental economic-wealth MaxDD vs STATIC_POST_RUNUP.
4. Incremental CAGR vs STATIC_POST_RUNUP.
5. Number of SELL events and extension episodes.
6. Full 153-window distribution, with overlapping windows treated as diagnostic.

No result is automatically promoted into the formal 10Y Floor.
