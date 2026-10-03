# QQQ_MUTUAL_CHASE_PROFIT_HOLD_V1 — Runtime Result

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

Source: actual GitHub PR #77 HEAD dataset, src/data/universe.json.
PR HEAD used for replay: 15a5bc8e3f8ce3034d59c8aa1f9ce4916b1bb3ef.
Data as-of: 2026-09-04.
Coverage: 273 monthly points, 153 complete overlapping rolling 10Y windows.

The common SELL state machine is fixed:
- POST_RUNUP = prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.
- Two consecutive qualifying month-ends confirm the episode.
- One SELL maximum per episode.
- SELL = 10% of prior-close NAV surplus.
- t-1 decision / t close execution.
- No future price read; no parameter search.

## Hypothesis

After a SELL, freeze the CLOCK target at the harvest-time target while the same extension episode persists, and prevent reserve redeployment during that cooldown. Resume the normal CLOCK after POST_RUNUP breaks.

This isolates post-harvest target behavior from the existing state-machine SELL trigger.

## Results

| Variant | Mean terminal delta vs CLOCK | Mean raw MaxDD delta | Mean economic MaxDD delta | Mean CAGR delta pp | Mean SELL events |
| --- | ---: | ---: | ---: | ---: | ---: |
| CURRENT_STATE_MACHINE | -0.530608 | +2.692 pp | +4.869 pp | -2.452 pp | 3.92 |
| PROFIT_HOLD | -0.530608 | +2.692 pp | +4.869 pp | -2.452 pp | 3.92 |

Incremental PROFIT_HOLD minus CURRENT_STATE_MACHINE:
- Mean terminal economic wealth: +0.000000611 B.
- Mean raw MaxDD: 0.000 pp.
- Mean economic-wealth MaxDD: +0.000003 pp.
- Mean CAGR: +0.0000047 pp.
- Higher terminal wealth: 4/153 windows.
- Lower economic-wealth MaxDD: 2/153 windows.
- Higher CAGR: 4/153 windows.

## Decision

The target-freeze hypothesis is effectively null in this dataset.

The reason is structural: the existing two-step confirmation + one-SELL-per-episode state machine already prevents most same-episode extraction churn, so freezing the rising CLOCK target adds almost no independent behavior.

No promotion.

This shifts the research focus away from target freezing and toward the semantics and timing of the reserve bucket itself.
