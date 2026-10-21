# QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1

Research-only. Does not modify official V2.2.

Question: can a frozen QQQ put-spread keep the 42% core near >=10% CAGR on real chain, or does the hedge just bleed the equity premium?

## Already observed (do not reuse as this branch result)

`research/qqq-realchain-convexity-v1-20260929` Actions run 36498315406:

- 42% QQQ + always-on 2% NAV 25Δ/10Δ put spread
- 2018-03-01 → 2025-12-15 real Bid/Ask
- CAGR **3.67%**, MaxDD **-17.17%**, 210 cycles, realized hedge P&L **-$82,992**

That version had no core-only comparator on the same tape.

## This V1

Same tape, three frozen books:

1. CORE42 — 42% QQQ shares from day 0, leftover cash idle.
2. ALWAYS_ON — CORE42 + permanent 25Δ long / 10Δ short put spread, 2% NAV budget, 18–35 DTE, roll at 7 DTE.
3. SHOCK_GATED — same spread, but open only when
   - QQQ close / 252-session peak - 1 <= -8%, or
   - QQQ 5-session return <= -4%.
   After a cycle exits, re-enter only if the shock rule is still true. No parameter search.

Execution (all option books):

- long put @ Ask, short put @ Bid
- daily mark Mid
- exit long @ Bid, short @ Ask
- no interpolation, no Black-Scholes selection
- delta from the chain field

Data: lambdaclass/options_portfolio_backtester `data-v1` `QQQ_options.parquet` + `QQQ_underlying.parquet`.
Window 2018-03-01 → 2025-12-16. 2026 is out of this chain.

Not a live signal. No VXX in this cut.
