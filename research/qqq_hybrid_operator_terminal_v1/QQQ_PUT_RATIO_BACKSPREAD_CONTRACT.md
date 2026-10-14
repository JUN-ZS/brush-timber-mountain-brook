# QQQ Put Ratio Backspread — Measurement Contract

Status: research-only payoff calculator inside Option Chain Lab. It does not enter the primary shared risk budget, does not alter the frozen strategy, and never authorizes orders.

## Locked interpretation

Here, N:1 means N long lower-strike QQQ puts for every one short higher-strike QQQ put. Both legs must share the same QQQ underlying and exact expiry, with K_short > K_long. This is a put ratio backspread. Do not silently reverse the counts; one long and N short puts have a different risk profile.

## Price convention and formula

- Long put entry price: Ask.
- Short put entry price: Bid.
- C = Bid_short − N × Ask_long, per share. Positive C is an opening net credit; negative C is an opening net debit.
- At expiry, P&L(S) = multiplier × [C + N × max(K_long − S, 0) − max(K_short − S, 0)].
- For N ≥ 1 and K_short > K_long, the expiry loss valley is at the long strike. Maximum loss per package = max(0, (K_short − K_long − C) × verified multiplier).
- At an underlying settlement of zero, payoff is multiplier × (C + N × K_long − K_short). Above the short strike, payoff is multiplier × C.

Breakevens are emitted only when their algebraic root falls inside its valid price interval. N=1 is a 1:1 vertical and has no added crash convexity. The calculator only uses the provided chain and never invents missing Put rows.

## Risk and evidence gates

The risk-budget package count is floor(candidate budget / maximum expiry loss per package) only. It excludes broker margin/buying power, early assignment/exercise, path risk and volatility changes before expiry, execution costs beyond the explicit sensitivity table, and interaction with the existing QQQ core. If expiry max loss is zero, capacity is not inferred as infinite.

Quote sensitivity shocks move the short Bid down and long Ask up by the listed per-side amount (0, $0.025, $0.05, $0.10). This is hypothetical stress, not observed slippage or a fill claim. Both selected puts require valid two-sided quotes even though the calculation uses the executable-side short Bid and long Ask.

The QQQ Put fixture remains empty because the supplied screenshot included CALL quotes only. Until the operator imports dated QQQ Put quotes with source metadata, the panel remains PENDING or SCENARIO ONLY. Adjusted contract terms are blocked; filling source fields never means the app independently authenticated them.

## Integration boundary

No main engine, current target, baseline strategy, option-risk pool, NAV or broker boundary is changed. Only the Option Chain Lab's isolated research panel and pure calculator are extended. The primary planner handoff remains restricted to its existing permitted QQQ/VXX call-credit candidates.