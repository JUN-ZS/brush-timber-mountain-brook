# QQQ Event-Driven Portfolio NAV Scale Replay V1

Repeats the same risk-budgeted event-driven account replay at initial NAVs of USD 80,000, USD 100,000, and USD 1,000,000. The only changed input is initial NAV. Each case uses the same hash-verified option files, QQQ/VIX series, event dates, contract selection, holding horizon, 0.5%/1%/2% terminal-tail budgets and BASE/STRESS costs.

The replay is run separately for each NAV to preserve the existing accounting path, then compared against CORE_ONLY at the same NAV. The report surfaces integer-contract, quote-depth and cash-reserve nonlinearity; it does not assume performance scales linearly.

Historical option observations end 2025-12-15. Results are research-only and do not prove broker margin, confirmed fills, virgin OOS performance or live deployability.
