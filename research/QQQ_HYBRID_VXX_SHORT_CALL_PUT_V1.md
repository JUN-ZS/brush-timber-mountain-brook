# QQQ Hybrid — VXX Short Call + Short Put V1

**Status:** research draft; derived model only; not a live strategy.

## Why this branch exists

The recovered Hybrid must keep its VXX option layer visible. This variant explicitly tests both:

- VXX call-credit vertical: short call + higher-strike protective long call.
- VXX put-credit vertical: short put + lower-strike protective long put.

These are defined-risk spreads, not naked short options. QQQ Core, QQQ call-credit spread and VXX short stock remain in the simulated portfolio.

## Design of experiment

Use the same dates, underlying input series, non-VXX-option rules and starting capital across three runs:

| Variant | VXX call risk budget | VXX put risk budget | Purpose |
|---|---:|---:|---|
| LEGACY_CALL_ONLY | 2% NAV | 0% NAV | Must reconcile to preserved historical simulator |
| DUAL_CALL_PUT | 1% NAV | 1% NAV | New dual-sided VXX option hypothesis; total budget remains 2% |
| NO_VXX_OPTIONS | 0% NAV | 0% NAV | Counterfactual portfolio without VXX option legs |

These allocation percentages are historical research experiment settings only. They are **not current frozen sizing** and are not passed to the current-capacity program as defaults.

## Data and option model

- Input: src/data/universe.json, QQQ/VXX/VIX.
- Same historical window adapter as the existing profit-trend replay: 2018-03-01 through 2026-09-04, excluding missing rows.
- VXX option strikes are selected from modeled absolute short delta 0.35 and protective wing absolute delta 0.16.
- IV and prices use the preserved derived BS/VIX proxy, including modeled spread haircuts. These are not historical OPRA option chains or fills.
- The same historical term-slope proxy is retained for comparability. Real Cboe M1/M2 would be a separate model variant.

## Correct risk sizing

For each credit vertical:

max_loss_per_spread = (spread_width - net_credit) * 100

contracts = floor(NAV * risk_budget_pct / max_loss_per_spread)

The sizing check records the max loss at opening. It never divides the risk budget by received credit. A missing/invalid/non-positive-credit put candidate remains absent/PENDING; no synthetic minimum credit is invented for the new put leg.

## Full-portfolio attribution, not standalone attribution

Each daily equity row includes QQQ core, QQQ call-credit, VXX short stock, VXX call-credit and VXX put-credit mark-to-market PnL. It checks:

NAV - initial capital == sum(component PnL)

The report also compares:

- the new dual-call/put portfolio against NO_VXX_OPTIONS (portfolio-level counterfactual, which includes any NAV-based sizing feedback); and
- the old call-only variant against the untouched historical simulator for exact daily NAV parity.

Do not divide an isolated VXX-only simulator's realized PnL by total hybrid profit and label it the true incremental contribution. Realized PnL, open-position marked PnL, option-layer contribution, and whole-portfolio counterfactual delta are distinct measurements.

## Current capacity consumer V2

qqq_hybrid_current_capacity_v2.py fixes the prior credit-sizing error. It requires current NAV/prices, externally supplied current sizing budgets, current candidate expiry/DTE/delta/strikes/credit, actual holdings, and explicit per-leg allow_new booleans.

- Option capacities are sized by full vertical max loss.
- Missing candidate -> PENDING; no contract count is invented.
- Unknown/missing permission does not authorize new entries.
- When a leg is not allowed to add, max_buy=0; existing over-cap quantities can still produce max_sell for trim.
- Historical percentages and trend metrics are descriptive evidence only.
- VXX short-stock remains unbounded-loss exposure; this module does not claim a portfolio hard loss cap.

## Commands (Windows CMD)

py -3 research\qqq_hybrid_vxx_short_call_put_strategy_v1.py --spots-path src\data\universe.json --out artifacts\qqq_hybrid_vxx_short_call_put_v1

py -3 -m unittest research\test_qqq_hybrid_short_call_put_v1.py

A separate Windows self-hosted workflow performs replay parity, attribution reconciliation, capacity tests, and artifact upload. Nothing submits broker orders.
