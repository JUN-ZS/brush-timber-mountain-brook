# QQQ_MUTUAL_CHASE_RESERVE_STATE_V1 — PREREGISTRATION

> RESEARCH_ONLY / DIAGNOSTIC_ONLY. This experiment does not alter the formal 10Y Floor, target authority, or broker execution.

## Question

After a profit harvest, does making the harvested **reserve** stateful—rather than immediately reusable—add incremental deployment value?

The research object is timing of reserve reuse only. The long-horizon capital target remains the fixed CLOCK:

\[
C_t = B\cdot t/120.
\]

No target reset, target freeze, or extra BUY is allowed.

## Fixed controls

All variants use the same SELL mechanism already fixed in the preceding V1 work:

- SELL fraction = 10% of prior-close surplus.
- POST_RUNUP eligibility = prior QQQ 6M return >= +15% and price >= 95% of the trailing 12M high.
- Two consecutive qualifying month-ends confirm the SELL state.
- One SELL maximum per continuous POST_RUNUP episode.
- SELL decision at t-1 month-end; execution at t month-end close.

The purpose is to isolate **reserve eligibility**, not to retune SELL.

## Reserve signal

The reserve-release weakness signal is deliberately inherited from the earlier fixed profit-release experiment:

\[
DD_{12,t} = QQQ_t/\max(QQQ_{t-11:t}) - 1
\]

Weakness means:

\[
DD_{12,t} \le -10\%.
\]

Recovery means:

\[
DD_{12,t} > -10\%.
\]

No alternative threshold is searched in this experiment.

## Three fixed variants

### 1. CURRENT_REUSE

Harvested reserve is immediately available for any future CLOCK shortfall.

This is the baseline to beat or reject. It is the existing reserve-reuse semantics.

### 2. ONE_SHOT_DD_RELEASE

Harvested reserve is locked.

The first month-end with prior QQQ 12M drawdown <= -10% releases all locked reserve. After release, it stays reusable permanently.

This is the direct control representing a non-stateful DD release.

### 3. RESERVE_STATE

Harvested reserve is locked and follows this fixed state machine:

\[
LOCKED \rightarrow WEAKNESS\_CANDIDATE \rightarrow RESERVE\_DEPLOYABLE \rightarrow RECOVERY \rightarrow LOCKED
\]

The transition rules are:

| State | Rule |
|---|---|
| LOCKED | First month with 12M DD <= -10% enters WEAKNESS_CANDIDATE. |
| WEAKNESS_CANDIDATE | A second consecutive month with 12M DD <= -10% confirms weakness and releases the locked reserve. |
| RESERVE_DEPLOYABLE | Released reserve may fund only future shortfalls to the unchanged CLOCK target. |
| RECOVERY | The first month with DD > -10% enters RECOVERY; reserve remains deployable while recovery is being confirmed. |
| LOCKED | After two consecutive recovery month-ends with DD > -10%, any unused available reserve is re-locked. |

A new weakness episode is therefore required to redeploy a re-locked reserve.

## Causal rules

The implementation must enforce:

1. Only t-1 month-end information may determine state transitions and BUY/SELL eligibility.
2. Execution occurs at the t month-end close.
3. No future price is read.
4. Total external contribution cannot exceed B.
5. Economic wealth includes NAV + planned reserve + harvested reserve, regardless of whether the harvested reserve is locked or deployable.
6. The reserve state never changes C_t=B*t/120.
7. The reserve state never forces a BUY beyond the normal shortfall chase.
8. No parameter search, optimizer, threshold sweep, or post-result winner selection.

## Primary incremental tests

The decisive comparisons are:

- RESERVE_STATE vs CURRENT_REUSE
- RESERVE_STATE vs ONE_SHOT_DD_RELEASE

The first asks whether reserve gating itself has useful timing value.

The second asks whether **state memory / hysteresis** adds value beyond a simple one-shot drawdown trigger.

## Reporting

Use all complete overlapping rolling 10Y windows available in \`src/data/universe.json\`.

Report:

- terminal economic wealth delta,
- raw-account MaxDD delta,
- economic-wealth MaxDD delta,
- CAGR delta,
- higher-terminal window count,
- lower-economic-MaxDD window count,
- SELL / release / re-lock event counts,
- terminal locked vs available reserve.

Do not declare a champion from the observed results. The experiment is a gate for whether reserve-state timing deserves another research stage.
