# QQQ_MUTUAL_CHASE_PROFIT_TARGET_RESERVE_V1

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

## Question

After a SELL harvests profit into reserve, should that reserve:
1. remain immediately reusable under the existing NAV target;
2. become protected Floor Credit that lowers the future risky-investment target; or
3. stay locked until a genuine market drawdown unlocks it for redeployment?

This experiment changes target/reserve semantics only. The common SELL state machine is fixed.

## Fixed common SELL state machine

- POST_RUNUP = prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.
- Two consecutive qualifying prior month-ends confirm an extension episode.
- One SELL maximum per continuous extension episode.
- COOLDOWN until POST_RUNUP breaks.
- SELL fraction = 10% of prior-close NAV surplus above the variant's current risk target.
- Decision uses t-1 month-end only; execution uses t month-end close.
- No future price read.
- No parameter search.

## Target/reserve variants

### CURRENT_REUSE
Control. Risk target is C_t = B*t/120. Harvested reserve is reused first for BUY.

### PROFIT_FLOOR_CREDIT
Harvested reserve becomes protected Floor Credit.
- H_t = locked harvested reserve.
- RISK_TARGET_t = max(0, C_t - H_t).
- Harvested reserve is not redeployed during normal target catch-up.
- Fresh external contribution buys the shortfall to the reduced risk target.
- Locked reserve remains outside QQQ and counts in economic wealth.

### PROFIT_DRAWDOWN_RELEASE
Same Floor Credit logic until a fixed QQQ drawdown trigger.
- Trigger = prior QQQ trailing 12M drawdown <= -10%.
- On the first qualifying drawdown while locked reserve exists, the entire locked reserve becomes available reserve.
- Available reserve may then be reused for BUY against the full CLOCK target.
- New harvests are locked again.
- No threshold search.

## Accounting

Economic Wealth = NAV + planned external-capital reserve + locked/available harvested reserve.

External cumulative contribution <= B.
Internal QQQ/reserve transfers are not new capital.

Primary metrics:
- terminal economic wealth / CAGR;
- raw account MaxDD;
- whole-economic-wealth MaxDD;
- external contribution;
- harvest;
- SELL count;
- reserve releases;
- terminal reserve.

All complete rolling 10Y windows are reported. No automatic promotion.
