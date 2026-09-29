# QQQ N-10 Seed + Opportunity Rights Bank V15

Research only. Not a live signal. Does not modify V2.2.

Frozen contract from the user's V14 follow-on:

- N is an opportunity right, not a free integer jump to N+20 / N+50.
- ΔR_N = Risk(N) − Risk(2) on that day's real-chain package.
- Coverage_N = (h · Bank) / ΔR_N. Usable iff Coverage_N ≥ 1.
- N_t = max { N ∈ 2..20 : ΔR_N ≤ h·Bank_t and Risk(N) ≤ 2% gate + Bank_t }.
- Bank_{t+1} = max(0, Bank_t + α P⁺ − β |P⁻|). Frozen α=1, β=1, h=1. No search.
- Mode B seed: first priced day posts Bank_0 = ΔR_10 of that day. Not a free N=10.
- Mode C seed: Bank_0 = 0.5 · ΔR_10.
- 互追反: after the seed, record whether Bank reproduces N > 10 and N < 10.

Same defined-risk package as V9–V14: +1 50Δ Call, −N 20Δ Short Call, +N 8Δ Wing.
Real QQQ Bid/Ask. No Black-Scholes. No interpolation.
