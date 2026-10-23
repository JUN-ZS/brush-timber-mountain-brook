# QQQ/SPY Entry Frequency: Relative Filter vs No Filter V1

## Question
Does dropping the condition "QQQ trailing 20-session return below SPY" increase entry cohorts, and what happens to resolved net P&L at 1-, 3-, and 5-year horizons?

## Frozen design
- Compare existing qqq_underperforms_spy_20d outputs with a fresh entry-filter=none replay.
- Fixed ratios: QQQ LONG PUT : SPY SHORT PUT = 1:6, 4:5, 2:4, 1:3.
- Keep 45-common-session cohort stride; do not enter every day.
- Keep same-expiry DTE 30-60, target 45 DTE, absolute Delta target 0.25, exact contracts, displayed side-size gates and conservative quote directions.
- Keep base costs: USD 0.05 slippage per option share per side and USD 0.65 commission per contract per side.
- Compare exits at 5, 10, 20 common sessions and DTE <= 7.
- Include USD 0.10 slippage-per-option-share stress by charging incremental round-trip slippage against each resolved trade.
- Report selected signals, entered cohorts, entry skips, resolved/unresolved counts, resolved-only win rate, mean/median/total P&L, per-year frequency and annualized resolved P&L. Never assign zero P&L to unresolved trades.

## Time horizons
All 1Y/3Y/5Y windows end on 2025-07-23, the last common signal date in the preserved 45-session cohort sequence that leaves enough source history to inspect the long-hold and DTE<=7 exits. Start dates are 2024-07-23, 2022-07-23 and 2020-07-23. Later signals are excluded rather than counted as losses or wins when the source ends before the policy exit.

## Interpretation boundaries
- A cohort is one strategy entry, not one contract; 1:3 opens four contracts, 2:4 six, 4:5 nine, and 1:6 seven.
- Removing the 20-session relative filter still preserves the frozen cohort stride, so it does not create daily entries.
- Results are fixed-cohort sums, not compounding portfolio equity; they do not model portfolio overlap, capital recycling, margin calls, taxes or guaranteed fills.
- Ratios were selected after inspecting the same historical data, so this is in-sample comparison, not proof of forward alpha.
- No main merge, app sizing change, broker connection, or live orders.

## Outputs
- results/no_filter/fixed_1_6, fixed_4_5, fixed_2_4 and fixed_1_3: raw no-filter replay outputs.
- results/no_filter_frequency_audit/report.md: comparison report.
- results/no_filter_frequency_audit/period_comparison.csv: 1Y/3Y/5Y results by ratio, filter and exit.
- results/no_filter_frequency_audit/annual_calendar_comparison.csv: year-level entry frequency and results.
- results/no_filter_frequency_audit/comparison.json: full summaries and input hashes.
