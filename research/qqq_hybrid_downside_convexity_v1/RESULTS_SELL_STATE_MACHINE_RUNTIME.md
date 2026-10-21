# QQQ_MUTUAL_CHASE_SELL_STATE_MACHINE_V1 — Runtime Result

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

This result was reproduced in the analysis runtime from the actual GitHub PR HEAD and the current repository dataset. It is not treated as a GitHub Actions artifact because the Actions research workflows on this commit currently fail at job startup with zero recorded steps.

## Provenance

- Repository: JUN-ZS/brush-timber-mountain-brook
- Source file: src/data/universe.json
- Source ref: refs/pull/77/head
- PR HEAD used for replay: 6f39d1faa87ee3b74a180a0ff12af94c4b9e810e
- Data as-of: 2026-09-04
- Monthly points: 273
- Complete overlapping 10Y windows: 153

The replay uses the same fixed executable rules registered in SELL_STATE_MACHINE_PREREGISTERED.md:

- SELL fraction = 10%.
- POST_RUNUP = prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.
- Two consecutive qualifying month-ends confirm an episode.
- One SELL maximum per continuous episode.
- After SELL, COOLDOWN persists until POST_RUNUP breaks.
- Decision uses t-1 month-end only; execution uses t month-end close.
- No future price read and no parameter search.

## Fair isolation

The incremental control is STATIC_POST_RUNUP:

- same 10% SELL fraction;
- same POST_RUNUP condition;
- same BUY-side full shortfall chase;
- same reserve accounting;
- same causal timing.

Only confirmation/cooldown state memory is added in STATE_MACHINE.

Therefore STATE_MACHINE vs STATIC_POST_RUNUP is the direct test of state-memory value.

## Results versus CLOCK

| Variant | Mean terminal delta B | Mean raw MaxDD delta | Mean economic MaxDD delta | Mean CAGR delta pp | Mean SELL events | Positive terminal windows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| STATIC_POST_RUNUP | -0.572591 | +4.636 pp | +5.834 pp | -2.671 pp | 23.04 | 0/153 |
| STATE_MACHINE | -0.530608 | +2.692 pp | +4.869 pp | -2.452 pp | 3.92 | 1/153 |

Reference CLOCK mean economic CAGR = 9.748981%.

## Incremental STATE_MACHINE vs STATIC_POST_RUNUP

- Mean terminal economic wealth delta: +0.041983 B.
- Median terminal delta: +0.024102 B.
- Q05 terminal delta: -0.012805 B.
- Q95 terminal delta: +0.134482 B.
- Mean raw account MaxDD delta: -1.944 pp.
- Mean economic-wealth MaxDD delta: -0.965 pp.
- Mean CAGR delta: +0.219 pp.
- Positive terminal windows: 135 / 153.
- Lower raw MaxDD windows: 61 / 153.
- Lower economic MaxDD windows: 139 / 153.
- Higher CAGR windows: 135 / 153.
- Mean SELL reduction: 19.12 events per 10Y window.

## Absolute reading

Using the same CLOCK reference:

- STATE_MACHINE mean terminal economic CAGR = about 7.297%.
- STATE_MACHINE mean raw account MaxDD = about -20.349%.
- STATE_MACHINE mean economic-wealth MaxDD = about -14.602%.

Thus the state machine improves the static 10% POST_RUNUP rule materially, but it does not close the remaining gap to CLOCK.

## Decision

The experiment gives the SELL state machine a genuine research signal:

1. State memory is not merely cosmetic; the state-machine variant is better than the same-condition static rule in terminal wealth and CAGR in most windows, and it lowers economic-wealth MaxDD in 139/153 windows.
2. The dominant mechanism is hysteresis: confirmation + one-harvest-per-extension-episode prevents repeated extraction during persistent trends.
3. However, STATE_MACHINE remains below CLOCK in mean terminal wealth and CAGR, so it is not promoted to the formal 10Y Floor.
4. The next research gate should test whether the remaining compounding drag comes from the fixed 10% harvest size or from the target formulation itself. That test must preserve the state-memory structure rather than silently replacing it with threshold search.
