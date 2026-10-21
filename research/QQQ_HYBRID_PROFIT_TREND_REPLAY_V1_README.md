# QQQ_HYBRID_PROFIT_TREND_REPLAY_V1

This is a standalone research replay + exporter for the historical source-aligned QQQ/VXX hybrid.

## Historical replay actually preserved

The included `qqq_hybrid_dynamic_deployment_v1_1_replay.py` is copied from the verified historical source at commit:

`ac74b3812c826ad491fb829108f26397322e45eb`

It contains the four original layers:

1. QQQ long core
2. QQQ call-credit spread
3. VXX short stock
4. VXX call-credit spread

Its option pricing is `DERIVED_BS_VIX`, not historical OPRA execution.

## What is exported

`qqq_hybrid_profit_trend_replay_v1.py` runs that historical simulator and exports:

- `profit`: NAV minus initial NAV
- `daily_profit`
- `total_return`
- `drawdown`
- 1M / 3M / 6M / 12M rolling profit change
- 1M / 3M / 6M / 12M rolling return
- 63-session descriptive profit slope

The output is intended as a **historical profitability-trend feed**, not as a new backtest optimizer.

## Critical sizing separation

The old historical simulator contains allocation parameters required to reproduce its old result. Those historical parameters must not be treated as today's frozen sizing.

In particular:

**QQQ Core = 42% NAV is NOT frozen sizing in the current operator workflow.**

The current 42% figure can be a market/cash-pool-derived example, such as the earlier illustration based on a cash pool equivalent to 100 QQQ, after which the program derives the corresponding example position size.

Therefore this new exporter explicitly marks current sizing as `EXTERNAL_INPUT`.

The intended future data flow is:

`historical replay profit trend`
→ `current market state / cash-pool calculation`
→ `current target/capacity`
→ `Current vs Target`

The historical 42% must not bypass that chain.

## Run

Baseline replay:

`python research/qqq_hybrid_profit_trend_replay_v1.py --spots-path src/data/universe.json`

Dynamic V1.1 replay:

`python research/qqq_hybrid_profit_trend_replay_v1.py --spots-path src/data/universe.json --dynamic`

Outputs:

`artifacts/qqq_hybrid_profit_trend_replay_v1/profit_trend.csv`

`artifacts/qqq_hybrid_profit_trend_replay_v1/profit_trend.json`

## Boundary

No broker order is created. No live sizing is changed. No parameter search is performed.
