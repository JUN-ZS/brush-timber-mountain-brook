# QQQ_MUTUAL_CHASE_TWO_SIDED_V1 — Replay Result

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

## Provenance

This replay was computed against the GitHub branch's actual `src/data/universe.json` at commit `c0548f3dc45841eb3136a53a4ec29d7993eb28aa`.

Data as-of: 2026-09-04.

Coverage: 273 monthly points, 153 complete overlapping rolling 10Y windows.

The replay uses the fixed strict-causal rule in `scripts/run-qqq-mutual-chase-two-sided-v1.ts`. It is not an Actions artifact yet; the connector replay is recorded separately from CI verification.

## Fixed rule

At month t:

- Target account capital: C_t = B*t/120.
- The BUY/SELL dollar amount is determined only from NAV at t-1 month-end close.
- If prior NAV is below target, BUY the shortfall.
- If prior NAV is above target, SELL the excess.
- Harvested sale proceeds go into reserve and are reused before planned reserve.
- Planned reserve starts at B and external funding cannot exceed B.
- Execution occurs at t month-end close.
- No borrowing, no future price read, no parameter search.

Whole economic wealth = account NAV + planned reserve + harvested reserve.

## Results versus CLOCK

### Terminal economic wealth

| Metric | Two-sided vs CLOCK |
| --- | ---: |
| Mean delta / B | -0.655308 |
| Median delta / B | -0.644178 |
| Q05 delta / B | -1.113844 |
| Q25 delta / B | -0.798695 |
| Q75 delta / B | -0.427309 |
| Q95 delta / B | -0.305543 |
| Positive windows | 0 / 153 |

Mean terminal economic wealth:

- CLOCK: 2.559447 B
- Two-sided mutual chase: 1.904139 B

The mean terminal wealth CAGR from the whole-economic-wealth curve is about 9.854% for CLOCK versus 6.652% for two-sided mutual chase.

### Drawdown

Absolute mean MaxDD:

| Metric | CLOCK | Two-sided |
| --- | ---: | ---: |
| Raw account MaxDD | -23.041% | -14.944% |
| Economic-wealth MaxDD | -19.470% | -12.831% |

Deltas (two-sided minus CLOCK):

- Mean raw account MaxDD: +8.096 percentage points.
- Median raw account MaxDD: +10.918 percentage points.
- Mean economic-wealth MaxDD: +6.640 percentage points.
- Median economic-wealth MaxDD: +6.396 percentage points.

Here a positive MaxDD delta means the drawdown is less negative, i.e. improved.

### Capital recycling

| Measure | Result |
| --- | ---: |
| Mean external contribution / B | 41.281% |
| Median external contribution / B | 38.350% |
| Mean cumulative harvest-to-reserve / B | 115.409% |
| Principal-breach windows | 0 / 153 |

The 41.281% figure is NOT a statement that the formal 10Y Floor only needs 41.281% funding. It is the gross external contribution actually required by this research rule while sale proceeds recycle through reserve.

## Decision

The strict causal two-sided mutual chase does what the mechanism predicts:

1. It materially reduces drawdown.
2. It repeatedly harvests gains into reserve and later redeploys after losses.
3. It keeps every tested rolling window's terminal whole-economic wealth at or above B.
4. It pays a large terminal-wealth opportunity cost versus CLOCK in all 153 windows.

Therefore:

> **Mutual chase is a capital-preservation / drawdown-control mechanism, not a return-enhancement mechanism in this fixed V1 form.**

It is conceptually much closer to the user's BUY↔SELL balancing idea than the earlier DIP experiment, but V1 is too aggressive: it forces the account exposure back toward the linear target every month and consequently sells too much of the long-term QQQ trend.

No part of this result is promoted into the formal 10Y Floor.
