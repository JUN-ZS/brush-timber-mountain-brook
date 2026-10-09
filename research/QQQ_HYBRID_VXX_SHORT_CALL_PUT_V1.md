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


## Public web research (external evidence, not copied as proof)

The research design was expanded after reviewing public material:

1. **Option Alpha — VXX Short Call Spread Backtesting (2023-07-10)**  
   https://www.youtube.com/watch?v=v5Z0DYy18UU  
   The public description explicitly says the author compares DTE settings and separates VXX RSI below 50 versus above 50. The page does not expose numerical results in its description, so this is a test-design lead, not performance proof. This branch now adds RSI<50 and RSI>=50 call-only research variants. The filter applies only to the VXX option entry; it does not silently alter the separate short-stock leg.

2. **ORATS — opposite VXX call-spread backtests (2019-08-07)**  
   https://orats.com/blog/the-tale-of-two-backtests-why-arent-opposite-strategies-absolute-returns-equal  
   ORATS reports an example in which a VXX short call spread returned +3.51% annualized versus -9.23% for the corresponding long call spread after costs. It attributes a large gap to estimated slippage and commissions, and says its historical entries use actual bid/ask snapshots around 14 minutes before close. This is evidence that costs are material, not a universal expected return for our Hybrid.

3. **ORATS — cross-symbol VIX moving-average trigger (2021-03-23)**  
   https://orats.com/blog/options-trading-using-stock-price-vs-moving-average  
   The example is a long VXX put entered when VIX is below its 20-day moving average. This is directionally different from a VXX short put credit spread, so it must not be mislabelled as evidence supporting our short-put leg. It demonstrates that an external VIX regime trigger can be tested separately from VXX price-only signals.

4. **Volatility Trading Strategies — VXX options as short-volatility exposure (2023-05-23)**  
   https://www.volatilitytradingstrategies.com/blog/estimating-future-vxx-prices-for-short-volatility-trading  
   The article compares long VXX puts, long VXX put verticals, long VXX put butterflies, short VXX straddles, and long SVIX as different ways to express short volatility. It also highlights borrow/availability issues with direct VXX short stock. These are related methods, but long puts and short puts are opposite directional exposures.

5. **ORATS historical data/backtester availability**  
   https://orats.com/backtester  
   The vendor describes EOD option data/backtests back to 2007 and custom tests using historical chains. Its backtester is a paid product; this repo run did not use ORATS/OPRA option data.

### What the web check means for our next experiment

- Yes, public work on VXX short call spreads and RSI/DTE regime tests already exists.
- I did not find a publicly accessible, independently auditable long-history result specifically validating our exact rule of selling both a VXX call-credit spread and a VXX put-credit spread inside the QQQ/VXX four-layer Hybrid.
- The dual call/put version must therefore be treated as our own hypothesis, not as an internet-proven strategy.
- The code now separates controlled tests: 1% call-only vs 1% call + 1% put; 2% call-only vs 2% call + 1% put; put-only vs no VXX options; call-only RSI<50 vs RSI>=50; and 14/30/45-calendar-day call-spread DTE sensitivity.
- The preserved legacy control intentionally retains the old index-based option-time convention to prove exact source parity. New-model variants mark positions using explicit calendar expiry dates so the 14/30/45-day sensitivity does not inherit the old mismatch. Cross-variant comparisons must use new-model controls, not treat the legacy parity control as an apples-to-apples sizing winner.
- This run still uses DERIVED_BS_VIX option prices. Its backtest numbers are useful for model screening only. A genuine option-chain replication would need historical VXX option bid/ask/greeks and correct reverse-split/contract-adjustment treatment; public webpages alone are not enough.
