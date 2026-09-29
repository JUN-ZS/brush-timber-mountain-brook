# QQQ Life-Win Rights V16

Research only. Not a live signal. Does not modify V2.2.

Frozen from the user sentence: 「一次 RISK WIN 吃一世」

## Contract

- Same package as V9–V15: +1 50Δ Call, −N 20Δ Short Call, +N 8Δ Wing.
- Real QQQ Bid/Ask. No Black-Scholes. No interpolation. No parameter search.
- Seed = V15 Mode B: first priced day posts `Bank_0 = ΔR_10`. Not a free N=10.
- `Bank_{t+1} = max(floor, Bank_t + α P⁺ − β |P⁻|)`. α=β=h=1.
- `N_t = max { N ∈ 2..20 : ΔR_N ≤ h·Bank and Risk(N) ≤ 2% gate + Bank }`.

## LIFE_WIN (two named modes, not a grid)

| Mode | LIFE_WIN iff | n_lock | floor |
| --- | --- | --- | --- |
| CONTROL_V15B | never | 2 | 0 |
| LIFE_DR10 | P ≥ ΔR_10 of that entry day | 10 | max(Bank_after, ΔR_10) |
| LIFE_OWN_RISK | P ≥ that vintage's Risk_proxy | N of that vintage | Bank_after |

Grant fires on the first LIFE_WIN and applies from the next signal only.
While granted, `N_t = max(N_t, n_lock)`. If the locked N fails the gate: record `LOCK_GATE`, do not silently scale down.

REVOKE iff a later vintage has `P < 0` and `|P| ≥ floor`. Then floor=0, n_lock=2.

## What this run is allowed to answer

1. Did a LIFE_WIN occur on this chain + this package?
2. After grant, did the right last to sample end (一世), or did one LOSS revoke it?
