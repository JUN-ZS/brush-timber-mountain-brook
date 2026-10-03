# QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1 — Frozen Result

Status: RESEARCH_ONLY. No funding authority. No product promotion.

Source: GitHub Actions research run #9, head `58166a5807435b2b10164bbfbbf63eaca8adeb2c`.

## 1. Deployment timing test

Data: QQQ observed daily snapshot through 2026-09-04, monthlyized to 273 points, 153 complete rolling 10Y windows. Windows overlap.

Fixed rules:

- CLOCK = 1/120 B every month.
- DIP_10_12M_ONE_SLICE = if trailing 12M QQQ drawdown <= -10%, move exactly one future clock slice into the current month.
- ORACLE_2X_CEILING = hindsight-only ceiling, max 2/120 in any month.

### DIP vs CLOCK

| Measure | Result |
| --- | ---: |
| Mean terminal delta / B | +0.158595× |
| Median terminal delta / B | +0.093802× |
| Q05 terminal delta / B | +0.010438× |
| Positive windows | 153 / 153 (100%) |
| Mean MaxDD delta | -0.009745 |
| Median MaxDD delta | -0.005869 |
| Q05 MaxDD delta | -0.030697 |
| Windows with MaxDD improvement | 4.6% |

Interpretation: the fixed dip rule produces a strong positive historical timing effect, but it worsens rather than improves drawdown. It is therefore NOT evidence of downside convexity.

### Oracle ceiling

Mean terminal delta / B is +0.976475× and median is +1.017755× versus CLOCK. This is hindsight only and is not an executable strategy. It measures the amount of theoretical timing capacity present in the historical paths.

## 2. Convexity test

Frozen-schedule permanent level shocks at months 24, 60, 96:

- Frozen-schedule curvature mean: 3.4e-17.
- Median: 0.
- This is numerical zero.

Path-aware DIP curvature:

- Mean: +0.017085.
- Median: +0.008292.
- Positive in 67.5% of tested rows.

Interpretation: frozen deployment has no mechanical payoff curvature. The path-aware curvature comes from the rule changing deployment after the shock. That is policy/path dependence, not option-like convexity.

## 3. Fixed protective-put test

Separate preregistered hypothesis:

- 100% QQQ exposure.
- Constant 0.5x protective put.
- 5% OTM.
- 45 calendar DTE.
- Roll 7 calendar days before expiry.
- 10% estimated spread haircut.
- No regime sizing and no parameter search.

This historical overlay uses the repository's Derived Black-Scholes/VIX engine and is NOT an OPRA fill backtest.

| Split | Naked CAGR | Put CAGR | ΔCAGR | Naked MaxDD | Put MaxDD | ΔMaxDD | Premium drag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Validation | 20.409% | 14.889% | -5.519pp | -28.559% | -21.988% | +6.571pp | 4.157% |
| OOS | 19.686% | 14.362% | -5.324pp | -29.562% | -28.790% | +0.772pp | 3.984% |

OOS ES improves by about 0.654 percentage points, but the CAGR drag is much larger. Fixed derived protection is therefore mechanically convex but not yet economically incremental.

## 4. V1 decision

- Deployment value: **YES, but it is path-timing value and carries drawdown risk.**
- True downside convexity from deployment timing: **NO.**
- Mechanical option convexity: **YES.**
- Economically sufficient historical protection from the fixed Derived put: **NO.**
- No V1 rule is promoted into the formal 10Y Floor.

## 5. Next research gate

The next independent test should be actual historical option-chain data (LambdaClass QQQ chain, 2011–2025) using one preregistered structure and conservative ask/bid fills. The purpose is to determine whether the Derived BS result is a model artifact and whether a convex hedge can be financed without giving away too much terminal wealth.

Do not search for a passing parameter after seeing these results.
