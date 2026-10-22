# Equal-Premium QQQ PUT / SPY PUT — Delta and Downside Exposure Audit

Source: `entry_cohort.csv` and `expiry_shock_grid.csv` from the exact premium-matched replay in this branch. Forty-four entered cohorts; contract source runs through 2025-12-15 for QQQ and 2025-12-12 for SPY. The figures are quote-side/model estimates, not verified executions.

## 1. Equal premium did not create a directionally neutral pair

The debit/credit cash flows match well, but this structure still has a materially positive first-order delta-dollar exposure.

| Entry exposure metric | Mean per cohort | Median per cohort |
|---|---:|---:|
| LONG QQQ PUT absolute Delta-dollar exposure | $30,117.94 | $29,095.75 |
| SHORT SPY PUT positive Delta-dollar exposure | $39,118.31 | $36,395.46 |
| Net Delta-dollar exposure (short SPY leg minus long QQQ put magnitude) | **+$9,000.37** | **+$6,427.15** |

The short SPY put's positive Delta-dollar exposure exceeded the long QQQ put's negative Delta-dollar magnitude in **43 of 44 cohorts**. Delta-dollar uses entry spot × absolute Delta × contracts × 100. It is a first-order directional measure, not a maximum-loss, margin, or tail-risk calculation.

## 2. Exercise/assignment scale

| Metric | Mean | Median |
|---|---:|---:|
| LONG QQQ PUT maximum intrinsic value at strike (strike × contracts × 100) | $114,231.23 | $110,025 |
| SHORT SPY PUT strike-based assignment obligation | $149,912.50 | $136,000 |

The SPY obligation is a notional purchase obligation if assigned, **not** the broker's margin requirement or the position's maximum loss. The two ETFs and puts have different underlying prices and payoff paths, so these amounts are only a size comparison.

## 3. Hypothetical expiry stress by relative performance

These scenarios use each real entry cohort's strikes, quantities and spots; assume the quoted puts remain to expiry; value each leg at intrinsic value; and charge entry-side slippage/commission once. They are not historical trade results or probabilities.

| QQQ move to expiry | SPY move to expiry | Positive / 44 cohorts | Mean scenario P&L | Worst scenario P&L |
|---:|---:|---:|---:|---:|
| −10% | 0% | 42 / 44 (95.45%) | +$5,733.12 | −$52.85 |
| −10% | −5% | 42 / 44 (95.45%) | +$3,666.28 | −$52.85 |
| −15% | −5% | 44 / 44 (100%) | +$9,643.26 | +$3,659.05 |
| −20% | −10% | 44 / 44 (100%) | +$8,482.37 | +$3,228.00 |
| 0% | −10% | 0 / 44 (0%) | **−$9,291.70** | −$22,397.35 |
| −5% | −10% | 0 / 44 (0%) | **−$8,410.30** | −$19,892.15 |
| +10% | −5% | 2 / 44 (4.55%) | −$2,102.23 | −$8,365.85 |
| 0% | 0% | 12 / 44 (27.27%) | −$35.39 | −$349.20 |

The pair can work when QQQ underperforms SPY by enough, but it is vulnerable to the reverse case: SPY falls while QQQ is flat or falls less. Equal premiums did not equalize that relative downside. Flat or rising markets leave the puts expiring OTM in most cases, with entry/transaction costs and the premium mismatch producing a small negative carry.

## 4. Conclusion and next test

Do **not** choose a different fixed ratio merely because a rescaled sensitivity row has a better win rate. The premium-matched replay has negative mean net P&L for all four tested exits; all 30 capped fixed-ratio rows per exit also have negative expectancy. The next isolated test therefore tests entry timing, not another post-hoc contract ratio: open only when QQQ's trailing 20-common-session return is below SPY's, with that condition evaluated on the signal close and execution no earlier than the next common session. This rule is predeclared and will be compared to the unconditional baseline; it is not proof of edge and must retain the same costs and unresolved-exit accounting.
