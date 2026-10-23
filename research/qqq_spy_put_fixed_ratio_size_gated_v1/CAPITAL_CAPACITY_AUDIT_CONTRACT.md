# Fixed-Anchor QQQ/SPY PUT Capital Capacity Audit Contract V1

## Frozen trade setup
- No entry filter.
- One QQQ LONG PUT and three SPY SHORT PUT contracts for each selected cohort.
- Fixed signal schedule: phase + k × 5 common QQQ/SPY underlying sessions.
- Five anchor phases (0–4); overlapping cohorts are enabled in the replay.
- Use only the immutable fixed-anchor phase results that pass the schedule integrity audit.

## Exposure definition
- Per-cohort gross SPY assignment obligation is the selected SPY put strike × 100 multiplier × short SPY contracts.
- Aggregate this obligation across every cohort whose entry-to-exit interval overlaps the date being measured.
- Count entry date and exit date inclusively. If the trade remains unresolved, count it through its last observed date.
- Keep each exit policy separate: 5 sessions, 10 sessions, 20 sessions and DTE ≤ 7.
- Count calendar days for which the aggregate gross assignment obligation exceeds a configured capital budget.

## Scenario matrix
- Comparison NAVs: $80,000, $100,000, and $1,000,000.
- Available-capital budgets: 25%, 50%, 75%, and 100% of each NAV.
- The strategy's contract count is held fixed across NAV scenarios; do not silently resize the position to make a scenario pass.
- Report peak concurrent cohorts, peak gross assignment obligation, peak shortfall, peak obligation as a percentage of budget, and calendar days over budget.
- Preserve resolved/unresolved trade counts, cumulative resolved P&L and worst resolved single trade as context, not as substitutes for capital capacity.

## Interpretation
- Gross assignment obligation is a conservative cash-capacity proxy, not the broker's margin requirement.
- Do not offset SPY assignment obligation against the QQQ long put because they are different underlyings.
- NAV fractions are explicit stress assumptions, not a claim about the user's real cash balance or broker's collateral rules.
- This report is not a confirmed fill simulation. It omits intraday margin changes, financing, forced liquidation, assignment timing, slippage beyond the base replay and changes to account NAV.
- A profitable replay can still be infeasible when multiple obligations overlap. The next action should be an explicit cash-capacity gate and a fresh replay that skips cohorts it cannot fund.
