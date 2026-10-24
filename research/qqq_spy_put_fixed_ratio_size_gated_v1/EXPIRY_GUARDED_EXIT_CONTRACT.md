# QQQ/SPY PUT Expiry-Guarded Holding Experiment V1

## Research question

For the frozen QQQ LONG PUT 1 : SPY SHORT PUT 3 strategy, compare DTE 14 and DTE 45 under a 10- or 20-session intended holding period that is cut short when remaining calendar DTE reaches 7.

## Frozen controls

- Reference arm: DTE 30–60, target DTE 45.
- Test arm: DTE 7–21, target DTE 14.
- Both legs target absolute Delta 0.25 in the existing 0.10–0.50 eligible band.
- Fixed quantities: one QQQ long put and three SPY short puts.
- No entry filter, every five common underlying sessions, all five immutable fixed-anchor phases, overlapping cohorts enabled, common expiry, standard contract identity checks, conservative quote sides and displayed-size gates.
- Historical period: 2018-03-01 through 2025-12-15; source option chains are pinned and reverified against the original Git blob SHA and byte count.
- Base cost assumption: USD 0.05 per option-share per side plus USD 0.65 per contract per side.

## New exit policies

- HOLD_10_OR_DTE_LE_7: signal an exit when age reaches 10 common sessions OR remaining calendar DTE is <= 7, whichever occurs first.
- HOLD_20_OR_DTE_LE_7: signal an exit when age reaches 20 common sessions OR remaining calendar DTE is <= 7, whichever occurs first.

The trigger is calculated using observed end-of-day dates. A close is resolved only on a later observed row with the exact selected contracts, valid bid/ask, and sufficient displayed exit-side size. Failed exits are deferred; positions with no executable close by expiry or source end remain unresolved. This prevents an unfilled exit trigger from being misrepresented as a completed trade.

## Method and outputs

- Each DTE arm is a fresh full option selection and quote-side accounting replay, not a rewrite of old P&L records.
- The base replay source file remains unchanged. The guarded runner records SHA-256 for the base engine, deterministic patched engine and runner.
- Each arm has five phase ledgers, a fixed-anchor schedule/performance audit, an actual-entry OTM/ATM/ITM audit, and a gross SPY assignment-obligation capacity audit.
- The paired comparison contains 30 records: five phases × three signal-date windows (1Y/3Y/5Y) × two guarded policies.
- Result manifests hash the phase summaries, trade ledgers, entry cohorts and comparison inputs.

## Interpretation limits

- Win rate and resolved P&L use resolved trades only; opened/resolved/unresolved counts must be shown together.
- The five phase schedules overlap and are sensitivity checks, not independent samples.
- EOD displayed quotes are not verified fills. Triggering an exit does not ensure execution that day.
- Gross SPY short-put assignment obligation is strike × 100 × contracts; it is not broker margin or proof of account funding capacity.
- Fixed-size cohort P&L is additive, not compounded NAV. This is in-sample historical research and never places live orders.
