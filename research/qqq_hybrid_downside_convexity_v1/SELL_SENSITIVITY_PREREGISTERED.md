# QQQ_MUTUAL_CHASE_SELL_SENSITIVITY_V1

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

## Question

The fixed two-sided mutual-chase V1 sells 100% of NAV excess above the linear capital target. Its drawdown improves materially, but terminal economic wealth falls in every tested rolling window.

This experiment isolates one variable only:

> What happens when the SELL side harvests only a fixed fraction alpha of the prior-close excess?

The BUY side remains unchanged and fully chases shortfall.

## Pre-registered alpha set

The alpha values are fixed before reading the new results:

- 0.00
- 0.10
- 0.25
- 0.50
- 0.75
- 1.00

No other alpha is searched. No winner is selected from these results.

Interpretation:

SELL_t = alpha * max(0, NAV_{t-1} - C_t)

where C_t = B*t/120.

BUY remains:

BUY_t = max(0, C_t - NAV_{t-1})

after reusing harvested reserve first and planned reserve second.

## Causality

- Decision amount at month t uses only NAV at month t-1 close.
- Execution occurs at month t close.
- No future price is read.
- No parameter search or post-result tuning.
- Every complete rolling 10Y window is reported.
- Windows overlap and remain diagnostic rather than independent observations.

## Fair accounting

For every alpha:

Economic Wealth = Account NAV + Planned Reserve + Harvested Reserve.

External contribution may fall below B because harvested gains are recycled; that is internal capital recycling, not free return.

Primary comparison:

- terminal economic wealth versus CLOCK;
- raw pre-rebalance account MaxDD versus CLOCK;
- whole-economic-wealth MaxDD versus CLOCK.

## Interpretation rule

This is not a search for a passing controller parameter.

The purpose is to reveal the shape of the trade-off:

SELL strength ↑
→ drawdown control ↑
→ QQQ trend exposure ↓
→ potential compounding drag ↑

The research question is therefore whether the trade-off is gradual, cliff-like, or contains a broad efficiency region.

No alpha is promoted automatically into the formal 10Y Floor.
