# Shared Position Management Meter — Measurement Contract

Status: measurement and manual-review layer only. It cannot place orders, mutate holdings, unlock a strategy, or change Frozen Original Hybrid. Apply the same scorecard to registered positions across supported templates while keeping strategy-specific economics and regime rules distinct.

## Why fixed dollars are not a decision rule

A gain of $1,000 is not comparable across NAV, quantity, initial risk, instrument and remaining opportunity. A three-calendar-day gain of $1,000 is $333.33/calendar day; a ten-calendar-day gain of $1,000 is $100/calendar day. If both positions have a $1,000 risk budget, both are +1R; if risk budgets are $5,000, both are only +0.2R. At NAV $100,000 this P&L is 1% NAV; at NAV $500,000 it is 0.2% NAV. These dimensions differ, but neither pace by itself implies a trim.

## Shared units

- **P&L / NAV (%)** = current gross unrealized P&L / entered NAV.
- **R-multiple** = current gross unrealized P&L / selected risk unit.
- **P&L pace** = gross unrealized P&L / elapsed calendar days; **R pace** = R-multiple / elapsed calendar days. Pace is unavailable if entry date is unknown or age is zero. Calendar days include weekends; this is not trading-session count or annualized alpha.
- **Risk budget rate (% NAV)** = risk-unit dollars / NAV.
- **Loss to stop from current mark** and **remaining target reward** are mark-to-threshold dollar estimates using current quantity and multiplier. Reward:loss-to-stop is shown only when both are measurable and the loss-to-stop is positive.
- **Time** = elapsed calendar days / optional operator-defined holding limit, plus option DTE and optional expiry-review threshold.
- **Evidence** = quote/mark provenance and freshness. A missing, stale, model-only, future-dated or unreferenced mark must not silently create a price trigger.

## Risk-unit hierarchy

1. Use a positive operator-entered risk budget when supplied.
2. Otherwise derive risk from entry to a structurally valid stop mark: QQQ long shares use a stop below entry; VXX short shares use a stop above entry; credit spreads use a net debit-to-close stop above entry net credit.
3. For a standard, fully identified credit vertical only, use the modeled expiry max loss if no stop-derived unit is available.
4. If none applies, risk is UNKNOWN. Do not compute R or infer a finite VXX short-stock tail from its margin requirement.

Target marks are side-aware: above entry for QQQ long shares; below entry for VXX short shares; below entry credit for a credit-spread closing debit. A positive user-defined target R can be used instead of or alongside a target price.

## Action precedence

1. A fresh, evidence-eligible mark has crossed the explicit stop, or gross loss has reached the risk budget → **HUMAN REVIEW**.
2. A verified market gate is in PRE-SHOCK / SHOCK for a risk-sensitive holding → **REGIME RISK REVIEW**.
3. Operator-defined maximum holding age or expiry-review threshold is reached → **TIME / EXPIRY REVIEW**.
4. An explicit target mark or target-R level is reached → **PROFIT REVIEW**, not an automatic full close.
5. A configured price rule cannot be evaluated from mark quality → **PENDING · REFRESH / VERIFY MARK**.
6. Missing risk, stop, entry date or time rule → **PLAN INCOMPLETE**.
7. Otherwise → **MONITOR**.

Every state is a review gate, not an order instruction. No universal stop percentage, three-day profit threshold, "$1,000 harvest line" or ten-day target is hard-coded.

## What the meter cannot prove

The scorecard does not estimate counterfactual future returns or prove that keeping a position is better than trimming it. Options marks exclude path-dependent changes in Greeks, volatility surface, early assignment, exercise, fees, fill slippage, liquidity and exact contract terms unless those are separately supplied and verified. High P&L/day is not evidence of an exhausted opportunity; low P&L/day is not evidence that the thesis failed. Assess remaining reward versus loss-to-stop, time, regime, option contract state, and a valid mark.

## Provenance labels

- **Observed**: operator-entered broker fill / current mark and references that pass the register's evidence checks; not independently authenticated by the APP.
- **Derived**: P&L/R, percent NAV, pace, stop distance, target reward, reward:risk, elapsed age and DTE from entered values.
- **Estimated**: risk unit inferred from entry/stop or a modeled standard-spread expiry maximum loss.
- **Hypothetical**: user-entered what-if price, stop, target, risk budget or time threshold. Input acceptance does not authenticate a quote.
