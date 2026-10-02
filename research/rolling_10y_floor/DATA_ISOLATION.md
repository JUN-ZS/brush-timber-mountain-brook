# Rolling 10Y Floor — Data Isolation Contract

Core controller training/selection may use only information that would have been available at each as-of date.

## Existing HUB / prior backtests
Existing repository backtests, labeled outputs, benchmark cards, and prior research artifacts are **not inputs to controller selection**. They may be used later only as post-hoc validation/audit evidence when their own as-of date and lineage can be demonstrated to predate the test decision.

## Evidence classes
- OBSERVED: source series used directly in the replay target.
- PROXY_PRICE: historical price/index series used to find analogous market states only.
- DERIVED: values computed from observed/proxy inputs without future information.
- HYPOTHETICAL: synthetic baseline or stress comparison.

## Current separation
QQQ is the replay outcome target.
Nasdaq-100 and Nasdaq Composite are PROXY_PRICE state channels. Their own future returns are never used as the terminal payoff for a QQQ deployment decision; matched QQQ future paths are used instead.

## Look-ahead rule
A historical analog is eligible only when its full following 10-year QQQ outcome is already completed by the current as-of date. No partially matured analog is admitted.

## Scale rule
10Y is the fixed terminal horizon. 20Y/30Y/50Y are historical context windows. Scale disagreement is a first-class market state, not a parameter to be averaged away.

## Research status
RESEARCH_ONLY. No claim of live suitability or guaranteed non-loss is made from this module alone.
