# QQQ LONG PUT / SPY SHORT PUT Pullback Filter — Fixed-Ratio Size-Gated Replay V1

## Research hypothesis

Test whether the prior QQQ-underperforms-SPY 20-session signal is more selective when SPY's own trailing 20-session return is also nonpositive:

1. QQQ 20-common-session close-to-close return < SPY return.
2. SPY 20-common-session close-to-close return <= 0%.

Both conditions are evaluated at the signal-day close; entry is attempted no earlier than the next common observed session. This second-stage hypothesis was discovered by examining an earlier in-sample 36-entry run. Its qualifying subgroup contained 15 signals. It is exploratory and not an independent holdout.

## Fixed comparison

Run both fixed ratios under the same condition and source mechanics:
- QQQ LONG PUT 1 : SPY SHORT PUT 6.
- QQQ LONG PUT 4 : SPY SHORT PUT 5.

The ratios were selected after inspecting in-sample results. No ratio or threshold is optimized within this run.

## Frozen mechanics

- Same SHA/byte-pinned option and underlying source, source tree commit, and requested window 2018-03-01 through 2025-12-15.
- Standard-root QQQ/SPY PUTs, common expiry, DTE 30–60 (target 45), absolute Delta target 0.25 within the existing eligible band.
- Keep exact selected contract IDs; no quote forward-fill or contract substitution.
- Fixed ratios are selected before entry and are not premium matched.
- Entry size gate: QQQ ask size >= fixed QQQ quantity and SPY bid size >= fixed SPY quantity.
- Exit size gate: QQQ bid size >= fixed QQQ quantity and SPY ask size >= fixed SPY quantity.
- Insufficient entry size defers on the same selected contracts; no valid entry before expiry is skipped. Insufficient close size defers; expiry/source-end without executable close is unresolved.
- Exit policies: 5, 10 and 20 common market sessions, plus DTE <= 7.
- Base costs: USD 0.05 per option share per side plus USD 0.65 per contract per side; retain zero/base/stress cost sensitivity.
- Report premium debit/credit mismatch, assignment obligation, worst trade, unresolved rates and expiry shocks.

## Interpretation constraints

- The filter was discovered after inspecting this same 2018–2025 sample. Positive results are in-sample evidence, not proof of a durable edge.
- The source ends in 2025; there is no 2026 option performance in this data.
- Displayed EOD sizes are historical screening evidence, not confirmed multi-leg fills.
- Equal cash premium does not equalize Delta, notional, collateral, assignment or tail risk.
- The 1:6 structure is intentionally far from premium matched. Do not present it as hedge-equivalent to 4:5.
- Assignment, margin, volatility repricing, overnight gap risk, financing, exercise fees and forced liquidation are not fully modeled.
- No merge to main, live sizing change, broker connection or live order.

## Outputs

- results/fixed_1_6: all reports for fixed QQQ 1 : SPY 6.
- results/fixed_4_5: all reports for fixed QQQ 4 : SPY 5.
- Each folder includes summary JSON/Markdown, full trade episodes, entries, entry skips, cost sensitivity, sizing sensitivity, expiry shock grid and source manifest.
