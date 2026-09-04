# EVB Evolutionary Trading Brain — V0.1 Research Run

## Scope

This run used the workspace's daily `spots_qqq_vxx_vix.csv` as the executable dataset: 2,179 rows from 2018-01-02 through 2026-09-01, with 2,161 non-null VXX observations. The dataset was independently cross-checked against current public market-data sources for the latest period. Cboe publishes VIX history back to 1990 and VIX term-structure data; QQQ daily history extends to 1999 in public datasets.

The goal was **not** to optimize a single threshold. Instead, an evolutionary-style competition was run over 12,000 signal genomes and multiple option structures. IS was 2018–2022; OOS was 2023–2026. OOS was used only as an audit, not as the selection target.

## Signal genome

Each genome combined:

- QQQ distance below MA20: 1–6%
- persistence age: 2–12 trading days
- daily rebound threshold: 0.1–0.8%
- 5-day VIX decline requirement: 1–7%
- relative-return / realized-volatility confirmation
- five different reversal logics

The central state concept is:

`persistent displacement -> expected-event clock -> reversal evidence -> option structure auction`

The engine does not assume that a displacement must eventually converge. A timeout is a real outcome.

## Option structures competed

1. ATM long call
2. 50Δ/10Δ call vertical
3. 35Δ/15Δ call vertical
4. 25Δ/10Δ call vertical
5. ATM call calendar
6. 25Δ/10Δ put credit spread
7. 35Δ/15Δ call vertical + 10Δ put hedge
8. 50Δ/10Δ call vertical + 10Δ put hedge
9. 50Δ/15Δ call vertical + 10Δ put hedge

Option prices were Black–Scholes with QQQ IV proxied from VIX (`IV ≈ 1.08×VIX`). This is **Hypothetical**, not an OPRA historical-chain backtest. A 5% option-value friction stress was used for the main ranking and 10% for sensitivity.

## Important result: asymmetric protection has signal-level value

Across 339 paired signal genomes with at least 20 IS events and 10 OOS events, the 50Δ/10Δ call vertical with a small 10Δ put hedge showed:

| Metric | 50Δ/10Δ call vertical | + 10Δ put hedge |
|---|---:|---:|
| Median IS EV | 1.17% | 1.16% |
| Median IS 5% tail | -29.8% | **-26.0%** |
| Median IS ES | -31.4% | **-27.3%** |
| Median OOS EV | 22.62% | 22.14% |
| Median OOS 5% tail | -20.86% | **-20.78%** |
| OOS tail improvement frequency | — | **100% of paired cases** |
| EV loss >20% | — | **0% of paired cases** |

These numbers are **normalized structure returns**, not portfolio CAGR. The denominator is structure risk/capital, so they must not be interpreted as a deployable annual return.

The important structural finding is different:

> A small opposite-side convexity leg can reduce left-tail damage while preserving most of the reversal payoff in this model.

That is exactly the kind of relative-weight relationship the EVB architecture should search rather than assuming “QQQ up = buy calls”.

## Strongest stable signal family found

The highest repeated family was approximately:

- displacement: ~2.1% below MA20
- persistence: 2–3 days minimum
- reversal: positive QQQ day + falling VIX / relative confirmation
- holding horizon: 10 trading days

This family repeatedly produced enough events to cross the research sample gate, unlike the earlier `Z <= -1` definition.

However, the apparent OOS advantage is still not statistically mature enough for live capital allocation because the best individual configurations can have only ~10 OOS events. The engine therefore **does not promote the highest-CAGR row to production**.

## Event-clock / “未出現太久” engine

Current last-known state in the workspace data (2026-09-01):

- QQQ: 707.64
- MA20: ~717.97
- QQQ distance from MA20: ~-1.44%
- VIX: 16.34
- below-MA persistence: ~6 trading days

Public data subsequently showed QQQ rebounding on Sep 3 while VIX fell to 15.20 on Sep 2; current public quotes therefore indicate that a reversal leg has already started after the Sep 1 weakness. This is a live-market observation, not a backtest result.

Historical event-clock examples from the dataset:

| Event | Count | Median gap | P90 gap | Last observed | Absence at Sep 1 |
|---|---:|---:|---:|---|---:|
| QQQ +1% day | 473 | 3d | 10d | Aug 27 | 3d |
| QQQ +2% day | 148 | 6d | 38d | Aug 4 | 20d |
| QQQ +0.5% & VIX falling | 686 | 3d | 6d | Aug 27 | 3d |
| QQQ +1% rebound while below MA20 | 138 | 4d | 44.4d | Jul 30 | 23d |
| VIX -10% over 5d | 449 | 1d | 15d | Aug 6 | 18d |
| MA20 cross up | 114 | 14d | 42.8d | Aug 27 | 3d |

The absence clock is therefore not a simple “overdue = buy”. It should estimate a **conditional hazard** given the current state and elapsed duration.

## What the evolutionary brain should become

The next architecture is not a bigger parameter grid. It is a population of competing hypotheses:

`Genome = {event definition, state variables, persistence clock, reversal detector, option topology, leg ratios, risk budget, exit rule}`

Each genome receives fitness from:

`EV + tail protection + OOS stability + sample size + cost sensitivity + regime diversity - complexity penalty`

Then use:

1. mutation — alter one mechanism at a time
2. crossover — combine successful event clocks with successful option structures
3. extinction — kill rules that only work in one regime
4. memory — preserve historical event analogs
5. walk-forward — periodically retrain on expanding history and test on unseen history
6. ensemble — deploy only when several independent genomes agree

The key is **state × history × context**, not a fixed threshold.

## Candidate pool policy

A candidate should enter the live-candidate pool only if it passes all of:

- IS and OOS positive EV
- minimum event count
- multiple non-overlapping episodes
- no single crisis responsible for most profit
- cost stress remains viable
- tail loss is bounded relative to the unhedged structure
- performance survives parameter perturbation
- performance survives regime holdout
- no look-ahead information
- no selection based on final OOS ranking

The best genome is therefore not necessarily the highest EV. It is the one occupying the best **risk-adjusted evolutionary niche**.

## External data expansion

Cboe provides VIX daily history from 1990 onward and VIX term-structure information. This creates a route to extend the state history beyond the 2018 VXX sample. QQQ public daily history reaches back to 1999. The next major upgrade should reconstruct a long-history volatility state using VIX/VIX9D/VIX3M/VVIX/VIX futures where available, then use VXX only where the actual instrument exists.

## Hard conclusion

**Yes, there is evidence that the search space contains useful relative-weight structures.** The most interesting result from this run is not “buy ATM calls”; it is that a small asymmetric opposite-side hedge repeatedly improved the tail distribution of a bullish reversal structure without materially destroying its modeled EV.

But this is still a research engine, not a live trading proof. The next decisive experiment is a true historical option-chain replay with actual bid/ask, IV surface, expiries, early exits, and portfolio-level capital allocation.
