# SPY Far-Tail Conditional Risk-Trigger Hedge — Research Contract V1

## Research question
Can a pre-declared entry-time risk rule reduce how often far-tail insurance premium is paid while retaining enough downside offset to justify the cost? No-hedge remains the primary control; unconditional 1x/3x tails are references.

## Frozen baseline and scope
- Baseline is read-only: QQQ LONG PUT 1 : SPY SHORT PUT 3, fixed five-common-session cadence, DTE14/DTE45, five overlapping phases and Hold-10/Hold-20 exits with the DTE<=7 guard.
- Original entry, leg selection, quantities and exit logic are not changed.
- Historical SPY chain is pinned to an existing completed overlay replay. Source hashes prove byte identity against the Git mirror, not OPRA provenance or actual fills.
- Before joining trigger flags to overlay outcomes, the runner requires every DTE14/DTE45 phase-ledger SHA-256 to match the original overlay manifest's `input_ledger_sha256` exactly. Missing, extra, or changed ledger hashes fail closed. The output manifest records this check and the analysis-script SHA-256.

## Entry-time trigger (frozen before measuring outcomes)
Buy a same-expiry far-OTM SPY PUT only when either condition is true at the base entry:
1. SPY entry spot is at least 5% below the high across the current entry observation plus the previous four entry observations in the same arm/phase. Five observations approximate 20 sessions only because the baseline signal cadence is five common sessions. All five prices must be valid; otherwise the drawdown component is unavailable and cannot trigger by itself.
2. The selected base short SPY PUT absolute Delta at signal time is at least 0.30.
Combine with OR. Delta is the stored signal-time Delta, not a new calculation at the later entry timestamp. Drawdown uses current and earlier observations only; no future prices are used.
Rule ID: SPY_DD5OBS_GE5PCT_OR_SIGNAL_SHORT_ABS_DELTA_GE0.30_V1.

These are pre-declared research thresholds, not tuned to maximize this replay's outcomes.

## Overlay arms
- Tail target: 2.5-delta (Put Delta about -0.025), 5-delta (about -0.05), and 10-delta (about -0.10) reference.
- Quantity 1 or 3. The 2.5 and 5-delta arms share the same absolute-Delta eligibility band 0.01-0.08.
- Same expiry as the base SPY short PUT; enter at ask, exit at bid. Costs are USD 0.05 per option-share per side plus USD 0.65 per contract per side.

## Fair comparison and missing data
- Show no-hedge mean across all resolved base trades and both no-hedge and conditional means on the exact same subset where the conditional realized outcome is known.
- If not triggered, conditional P&L equals base P&L. If triggered but entry quote/size eligibility fails, no purchase is assumed and base P&L remains the modeled strategy outcome; count the failed hedge opportunity.
- If a hedge entry passes its quote/size gate but the same-contract exit quote is missing/undersized, realized conditional P&L is unknown. Never replace it with zero, an MTM mark or base P&L.
- Show trigger rate, entry and exit coverage, outcome coverage, modeled opening debit, worst matched trade, losing trades improved/turned positive, annual outcomes and stress results.
- Five phase schedules overlap; phase min/median/max are robustness summaries, not independent samples or confidence intervals.

## Stress and decision limitations
Expiry stress is intrinsic payoff for the SPY short-put sleeve only. It omits the QQQ long PUT, time value, assignment/early exercise, margin, forced liquidation and account-level NAV.
Do not choose a rule solely because the deepest shock improves. Weigh recurring spend, annual behavior, quote coverage, worst matched trade and the losses incurred while the trigger is inactive. Freeze the rule and evaluate it on a later untouched chronological holdout before any deployment.
