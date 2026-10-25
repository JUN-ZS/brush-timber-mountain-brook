# QQQ Hybrid Combined Replay V1 — Record for Next AI

**Status:** DERIVED_REPLAY_COMBINED  
**Date:** 2026-10-09  
**Branch:** `research/qqq-hybrid-profit-trend-replay-v1-20261009`  
**Verified run:** [Run 37844546677](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37844546677)  
**Artifact:** `qqq-hybrid-profit-trend-replay-v1` (ID 11579940057)

## Why this exists

The hybrid was recovered because it contains a **VXX call-credit spread** (short VXX call + long wing), not only QQQ core or VXX short stock.

This record preserves the verified derived replay so the next AI does not re-derive or invent it.

## Source of truth

```
GitHub actual files
    ↓
GitHub actual commit / diff
    ↓
GitHub actual Actions run / logs / artifact
    ↓
tests / executable result
    ↓
repo documentation
    ↓
previous AI message
```

Do not treat AI chat as source of truth.

## What was replayed

Preserved simulator: `research/qqq_hybrid_dynamic_deployment_v1_1_replay.py`  
SHA: `ac74b3812c826ad491fb829108f26397322e45eb`

Four layers:

| Layer | Structure |
|-------|-----------|
| QQQ | Long core |
| QQQ option | Call-credit spread |
| VXX | Short stock |
| VXX option | Call-credit spread (short VXX call + long wing) |

Data: `src/data/universe.json` (QQQ / VXX / VIX, as-of 2026-09-04)  
Window: 2018-03-01 → 2026-09-04 (2141 sessions)  
Pricing: **DERIVED_BS_VIX** (not historical OPRA fills)

## Verified results (Run 37844546677)

### Full hybrid

| Variant | Final NAV | Final Profit | CAGR | MaxDD |
|---------|-----------|--------------|------|-------|
| BASELINE | 298,267 | +198,242 | 13.70% | -23.02% |
| DEPLOY_V1_1 | 303,257 | +203,232 | 13.92% | -22.85% |

Latest descriptive trend (BASELINE):

- 1M return: +2.08%
- 3M return: +2.50%
- 6M return: +18.17%
- 12M return: +21.27%
- 63d profit slope: +43.65
- Current drawdown: -1.85%

### VXX call-spread layer only

| Item | Value |
|------|-------|
| Structure | short VXX call + long wing |
| Risk budget | 2% (`BASE_RV`) |
| Delta targets | short ≈0.35 / long wing ≈0.16 |
| Opens | 50 |
| Closes | 49 |
| Wins | 41 |
| Losses | 8 |
| Realized PnL | +7,178 |
| Share of BASELINE profit | ≈ 3.62% |

VXX call-spread is a positive contributor in this derived replay, but it is a small share of total profit. Most NAV comes from the other layers.

## New program that uses the feed

`research/qqq_hybrid_new_program_v1.py`

It does exactly the intended chain:

```
Historical Profit Trend (four-layer hybrid)
    +
VXX call-spread attribution
    +
Current Market State
    +
Current Cash Pool
    +
Actual Current Holdings
    ↓
Current Target / Capacity
    ↓
Current vs Target
```

Run example:

```
python research/qqq_hybrid_new_program_v1.py \
  --trend-json artifacts/qqq_hybrid_profit_trend_replay_v1/baseline/profit_trend.json \
  --vxx-cc-json artifacts/qqq_hybrid_vxx_call_spread_contribution_v1/vxx_cc_report.json \
  --current-json current_inputs.json
```

## Hard boundaries (do not violate)

1. **Historical 42% ≠ Current Frozen Sizing**  
   The old simulator uses 42% QQQ only to reproduce its historical model. In the current operator workflow, current sizing is `EXTERNAL_INPUT`.

2. **Profit trend is descriptive evidence only**  
   Do not turn CAGR, slope, or rolling returns into a BUY/SELL threshold. That would create a new strategy.

3. **Derived ≠ OPRA**  
   Option prices are VIX/BS proxies. There are no historical OPRA fills in this replay.

4. **No live mutation**  
   This research line does not submit broker orders and does not change live sizing.

5. **Research ≠ Live strategy**  
   Do not promote research parameters into the live V3 path just because a number looks better.

## Current sizing contract

```
qqq_core_pct       = EXTERNAL_INPUT
vxx_short_pct      = EXTERNAL_INPUT
qqq_call_contracts = EXTERNAL_INPUT
vxx_call_contracts = EXTERNAL_INPUT
```

## Files for next AI

- `research/qqq_hybrid_dynamic_deployment_v1_1_replay.py` — preserved four-layer simulator
- `research/qqq_hybrid_profit_trend_replay_v1.py` — profit trend exporter
- `research/qqq_hybrid_vxx_call_spread_contribution_v1.py` — VXX call-spread attribution
- `research/qqq_hybrid_profit_trend_consumer_v1.py` — earlier consumer
- `research/qqq_hybrid_new_program_v1.py` — new program entry that uses the feed
- `.github/workflows/qqq-hybrid-profit-trend-replay-v1.yml` — self-hosted Windows runner

## What next AI must not do

- Do not claim PASS without a GitHub Actions artifact / log.
- Do not hardcode 42% as today's capacity.
- Do not replace the VIX-derived term-slope proxy with real Cboe M1/M2 inside this historical replay (that would make it a different model).
- Do not invent option quantities when no real candidate credit exists.
- Do not open the auto-trading boundary.

## One-line summary

The hybrid was recovered for its VXX call-credit spread. The derived replay is verified. VXX call-spread contributed about +7,178 (≈3.6% of baseline profit). The new program consumes that feed as evidence only. Historical 42% is not current frozen sizing. Current capacity remains EXTERNAL_INPUT.
