# SPY Far-Tail In-Holding Risk-Trigger Hedge — Research Contract V1

## Objective
Test whether buying a same-expiry far-OTM SPY PUT after risk worsens during an existing QQQ LONG PUT 1 : SPY SHORT PUT 3 position can improve realized tail outcomes while avoiding unconditional insurance carry. No hedge remains the control; 1x and 3x hedge quantities are paired overlays.

## Frozen baseline
- Read only source-pinned trade_episodes.csv phase ledgers and the previously completed far-tail replay manifest.
- Primary exit policy: HOLD_20_OR_DTE_LE_7 across the existing DTE14/DTE45 arms and five overlapping fixed phases.
- Before replay, all ten DTE14/DTE45 phase-ledger SHA-256 values must equal the prior overlay manifest's input_ledger_sha256. Missing, extra, or changed hashes fail closed.
- The base trade entry, selected contracts, quantity, scheduled exit and realized P&L cannot be modified.

## Predeclared holding-period triggers
Each rule fires at most once per base position, on its first qualifying observation strictly after the base entry date and strictly before its original exit date.

1. **Exact short-put Delta:** absolute Delta of the selected, exact SPY short PUT is at least 0.35 on the current day's quote snapshot.
2. **Underlying drawdown:** SPY current daily close is at least 5.0% below that position's actual entry SPY spot.
3. **Package mark-to-close loss:** exact selected QQQ long PUT bid and SPY short PUT ask produce a full-package net mark-to-close P&L at or below -50% of the initial gross SPY short-put credit. Both current quotes and displayed sizes must pass the base close-side gates.
4. **Composite OR:** first observed date any of the above rules fires; record each component that fired on that date.

Thresholds are frozen before this replay. There is no parameter sweep, outcome-based rule selection, intraday interpolation or retroactive trigger. The same day's EOD quotes only define the modeled trigger and ask-side hedge entry; they are not verified fills.

## Hedge contract selection and accounting
- On the first trigger day, select the nearest eligible same-expiry, strictly OTM SPY PUT around the existing 2.5-delta, 5-delta and 10-delta targets using the prior overlay's selection and displayed-size rules.
- Test 1 and 3 contracts. Buy at the trigger-date ask, hold the exact same contract, and mark/close it only from the original base trade's exact exit-date bid. Cost: USD 0.05 per option-share per side plus USD 0.65 per contract per side.
- If not triggered, no hedge is purchased. If a trigger occurs but no eligible entry exists or the displayed ask size is insufficient for the quantity, no purchase is assumed and baseline realized P&L remains.
- If an eligible hedge was entered but the exact same-contract exit quote is missing or bid size is insufficient, its conditional realized outcome stays missing. Never replace it with zero, baseline P&L or an unrelated-date mark.
- Unresolved base positions remain mark-only; their P&L is never counted as realized.

## Time split and denominator
- Training/descriptive: entries in 2018-2022.
- Locked chronological holdout: entries in 2023-2025. Freeze thresholds before inspecting this replay and do not tune using holdout outcomes.
- The repository previously examined overlapping historical years for other strategy research. Therefore this is a rule-family holdout, not a globally virgin dataset. The pinned chain ends in 2025; genuinely untouched forward validation needs later source-pinned option-chain data.
- Report trigger rate, feature data coverage, entry/exit coverage, outcome coverage, modeled debit, paired mean P&L increment, worst matched-trade improvement, losses improved/turned positive and entry-year outcomes. Compare conditional outcomes with no-hedge P&L on exactly the same known-outcome rows.
- Five phases overlap; across-phase medians/ranges are not independent samples or confidence intervals.

## Data integrity and limits
- Download all yearly QQQ/SPY option chains and underlying-close files from the pinned source engine; verify each source file's byte count and Git blob SHA-1 against the engine's frozen pins.
- Do not forward-fill missing daily quotes, Delta or underlying prices. No lookahead, live broker connection, order placement, main-branch merge, NAV/margin model, forced liquidation, early exercise/assignment or financing model.
- EOD displayed sizes are a screening gate, not proof of a fill. Results are estimates, not confirmed executed performance.
