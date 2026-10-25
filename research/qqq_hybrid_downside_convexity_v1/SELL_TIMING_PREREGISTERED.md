# QQQ_MUTUAL_CHASE_SELL_TIMING_V1

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

Question: can selective SELL timing preserve more long-term compounding while retaining a meaningful part of the drawdown reduction?

Fixed SELL fraction: 0.50 for every rule. Only SELL eligibility changes.
Target: C_t = B*t/120.
SELL amount when eligible: 0.50 * max(0, NAV_(t-1) - C_t).
BUY is unchanged: full shortfall below C_t, using harvested reserve first.

Pre-registered SELL timing rules:
1. ALWAYS_SURPLUS: sell whenever prior NAV exceeds target. Control.
2. NEAR_12M_HIGH: sell only when prior QQQ is >= 95% of trailing 12M high.
3. AT_12M_HIGH: sell only at trailing 12M high.
4. STRONG_AND_HIGH: sell only when prior QQQ 12M return >= 0% and price >= 95% of trailing 12M high.
5. POST_RUNUP: sell only when prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.

Causality: decision at month t uses only t-1 close. Execution at t close. No future price read. No parameter search.
All complete rolling 10Y windows are reported; overlapping windows are diagnostic.

Primary outputs: terminal economic wealth vs CLOCK; raw account MaxDD vs CLOCK; economic-wealth MaxDD vs CLOCK; CAGR delta; SELL frequency; harvest.

No rule is promoted automatically.