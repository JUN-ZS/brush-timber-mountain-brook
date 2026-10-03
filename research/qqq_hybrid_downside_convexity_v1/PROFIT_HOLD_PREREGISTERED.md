# QQQ_MUTUAL_CHASE_PROFIT_HOLD_V1

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

## Question

After a profit harvest, does the system need to permanently lower its target, or should it temporarily hold the target during the same extension episode so harvested profit is not immediately bought back?

This is a target/reserve timing experiment.

## Fixed common rules

- POST_RUNUP = prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.
- Two consecutive qualifying prior month-ends confirm an extension episode.
- One SELL maximum per continuous extension episode.
- SELL fraction = 10% of prior-close NAV surplus above the active target.
- Decision t-1 month-end; execution t month-end close.
- No future price read.
- No parameter search.

## Variants

### CURRENT_STATE_MACHINE

Existing control:
- Target = C_t = B*t/120.
- Harvested reserve can be reused immediately on any later BUY shortfall.

### PROFIT_HOLD

When a SELL occurs:
- record the current clock target as holdTarget;
- enter COOLDOWN as before;
- while the same POST_RUNUP episode persists, active target is frozen at holdTarget;
- harvested reserve is not redeployed during this COOLDOWN episode;
- when POST_RUNUP breaks, release the hold and resume C_t;
- the harvested reserve then becomes reusable for the normal BUY shortfall.

The hold is temporary and state-linked. It does not permanently lower the 10Y capital clock.

## Fair isolation

Both variants use the same:
- SELL fraction;
- POST_RUNUP condition;
- two-observation confirmation;
- one-SELL-per-episode rule;
- BUY reserve accounting;
- causal timing.

Only post-harvest target behavior differs.

## Accounting

EconomicWealth = NAV + planned reserve + harvested reserve.

External contribution <= B.
Internal reserve transfers are not new capital.

Primary metrics:
- terminal economic wealth / CAGR;
- raw account MaxDD;
- economic-wealth MaxDD;
- external contribution;
- harvest;
- SELL count;
- target-hold episodes;
- terminal reserve.

All complete rolling 10Y windows are reported. No automatic promotion.
