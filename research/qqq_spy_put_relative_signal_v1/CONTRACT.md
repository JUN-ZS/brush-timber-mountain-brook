# QQQ LONG PUT / SPY SHORT PUT — Relative-Underperformance Entry Study V1

**Purpose:** test one predeclared entry condition on the equal-premium strategy, without optimizing entry thresholds to historical P&L.

## Hypothesis and rule
The baseline equal-premium replay had negative mean net P&L for every tested exit rule. This study tests whether entry timing improves when **QQQ's trailing 20-common-session close-to-close return is below SPY's trailing 20-session return**.

- Signal is computed at the signal-day close from the current close and the close 20 common sessions earlier.
- A position can enter only on the next observed common session, using the exact selected QQQ PUT and SPY PUT contract IDs and current entry quotes.
- If the condition is false, no position opens; scanning continues until the condition becomes true while the book is flat and the 45-session cohort spacing permits entry.
- No P&L-optimized thresholds, strike choice or exit changes. The prior equal-premium strategy remains the fixed baseline.

## Frozen mechanics
- Option data source, SHA/byte pinning, and history window match the equal-premium study: 2018-03-01 to 2025-12-15 requested, with QQQ chain through 2025-12-15 and SPY through 2025-12-12.
- Standard-root QQQ PUT and SPY PUT; common expiry 30–60 DTE nearest 45; absolute Delta target 0.25 per leg, eligible 0.10–0.50.
- At each entry, choose positive integer contracts that minimize mismatch between QQQ PUT Ask premium debit and SPY PUT Bid premium credit; use actual displayed entry depth and combined max-contract cap 9.
- Compare holding 5/10/20 sessions and DTE <= 7. QQQ long closes at Bid; SPY short put bought back at Ask.
- Costs remain $0.05 per option share per side plus $0.65 per contract per side, with zero/base/adverse sensitivity.
- Unresolved trades stay separate from resolved-only win-rate/P&L denominator.
- Use the same current quote sources and P&L accounting. Report actual entry count and filter evaluations; do not compare cumulative P&L without acknowledging differing cohort counts.

## Interpretation
This filter is an exploratory, directional hypothesis, not an optimized strategy or proof of edge. The sample is likely smaller than the unconditional 44-cohort baseline. Do not promote based on a higher win rate alone; compare per-resolved expectancy, cost sensitivity, unresolved rate, downside losses and same-date cohort details. Any subsequent signal must be predeclared and assessed out-of-sample. No live sizing, App changes, or broker orders.
