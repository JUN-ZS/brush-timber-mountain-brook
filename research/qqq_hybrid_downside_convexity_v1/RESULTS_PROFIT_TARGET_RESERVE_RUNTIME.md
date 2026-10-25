# QQQ_MUTUAL_CHASE_PROFIT_TARGET_RESERVE_V1 — Runtime Result

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

Source: actual GitHub PR #77 HEAD dataset, src/data/universe.json.
PR HEAD used for replay: 15a5bc8e3f8ce3034d59c8aa1f9ce4916b1bb3ef.
Data as-of: 2026-09-04.
Coverage: 273 monthly points, 153 complete overlapping rolling 10Y windows.

All variants use the fixed SELL state machine:
- POST_RUNUP: prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.
- Two consecutive qualifying month-ends to confirm an episode.
- One SELL maximum per continuous episode.
- SELL = 10% of prior-close NAV surplus above the variant's active risk target.
- t-1 month-end decision, t month-end close execution.
- No future price read and no parameter search.

## Results versus CLOCK

| Variant | Mean terminal ΔB | Mean raw MaxDD Δ | Mean economic MaxDD Δ | Mean CAGR Δ pp | Mean SELL | Mean releases | Positive terminal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CURRENT_REUSE | -0.530608 | +2.692 pp | +4.869 pp | -2.452 pp | 3.92 | 0.00 | 1/153 |
| PROFIT_FLOOR_CREDIT | -0.545872 | +2.388 pp | +4.958 pp | -2.531 pp | 3.92 | 0.00 | 1/153 |
| PROFIT_DRAWDOWN_RELEASE | -0.532943 | +2.695 pp | +4.894 pp | -2.464 pp | 3.92 | 1.73 | 1/153 |

CLOCK mean economic CAGR = 9.749%.

## Incremental versus CURRENT_REUSE

### PROFIT_FLOOR_CREDIT
- Mean terminal ΔB: -0.015263.
- Mean raw MaxDD Δ: -0.304 pp.
- Mean economic-wealth MaxDD Δ: +0.089 pp.
- Mean CAGR Δ: -0.080 pp.
- Higher terminal windows: 0/153.
- Lower economic MaxDD windows: 0/153.

Interpretation: permanent target reduction protects the raw QQQ account slightly, but does not improve whole-economic-wealth drawdown and costs compounding.

### PROFIT_DRAWDOWN_RELEASE
- Mean terminal ΔB: -0.002335.
- Mean raw MaxDD Δ: +0.004 pp.
- Mean economic-wealth MaxDD Δ: +0.026 pp.
- Mean CAGR Δ: -0.013 pp.
- Higher terminal windows: 27/153.
- Lower economic MaxDD windows: 0/153.

Compared with PROFIT_FLOOR_CREDIT, drawdown release recovers almost all of the terminal-wealth/CAGR loss:
- +0.012928B terminal;
- +0.067 pp CAGR;
but economic-wealth MaxDD is still 0.063 pp worse than the Floor Credit variant, and neither beats CURRENT_REUSE.

## Structural result

1. Harvested profit should NOT be interpreted as a permanent subtraction from the 10Y CLOCK target.
2. A target freeze during the same extension episode is also not material: a separate fixed replay showed effectively zero incremental effect versus the existing state machine.
3. The reserve therefore appears more useful as an independent capital bucket than as a permanent target-reset mechanism.
4. The next research object should be RESERVE_STATE, not another target threshold:
   - PROTECTED / HOLD;
   - REDEPLOYABLE only under a predefined weakness condition;
   - external funding clock remains formally C_t = B*t/120.
5. No target/reserve variant is promoted into the formal Floor controller.
