# QQQ_HYBRID_PROFIT_TREND_EXPORT_V1

Research-only exporter for the historical source-aligned hybrid replay.

## What it replays

The exporter calls the existing frozen historical replay implementation:

- QQQ long core
- QQQ call-credit spread
- VXX short stock
- VXX call-credit spread

The source replay is the historical **DERIVED_BS_VIX** reconstruction. It is not historical OPRA execution.

## What this program adds

It takes the replay equity curve and writes a reusable profitability-trend feed:

- `profit`: NAV minus initial NAV
- `daily_profit`: daily change in NAV
- `total_return`
- `drawdown`
- 1M / 3M / 6M / 12M rolling profit change
- 1M / 3M / 6M / 12M rolling return
- 63-session descriptive profit slope

The rolling fields are descriptive research outputs. No threshold is optimized here and no output field is converted into an automatic order or sizing instruction.

## Critical sizing separation

The historical replay contains its own historical/model allocation parameters because that is required to reproduce the old backtest.

**Do not treat those historical parameters as current frozen sizing.**

In particular, the frequently displayed **QQQ = 42% NAV** must not be copied into a current sizing contract. In the current operator workflow, the 42% figure is an example produced from the current cash-pool / market-state calculation (for example, an illustration anchored to 100 QQQ), not a permanent frozen capacity.

Therefore this exporter deliberately marks current sizing fields as:

`EXTERNAL_INPUT`

The future consumer should combine:

`historical profit trend` + `current market-state calculation` + `actual current holdings`

rather than importing a historical percentage as a hidden constant.

## Run

Baseline historical replay:

`python research/qqq_hybrid_profit_trend_export_v1.py --spots-path src/data/universe.json`

Dynamic V1.1 replay:

`python research/qqq_hybrid_profit_trend_export_v1.py --spots-path src/data/universe.json --dynamic`

Outputs:

`artifacts/qqq_hybrid_profit_trend_v1/profit_trend.csv`

`artifacts/qqq_hybrid_profit_trend_v1/profit_trend.json`

## Research boundary

This program exports historical profitability behavior. It does not claim that the derived option pricing equals actual historical market fills, and it does not change the current strategy policy.
