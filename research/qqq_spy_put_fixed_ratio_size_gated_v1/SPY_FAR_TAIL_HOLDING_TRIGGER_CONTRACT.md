# SPY Far-Tail In-Holding Risk-Trigger Hedge — Research Contract V2

## Purpose and versioning
This version corrects the execution-time flaw in V1: a trigger computed from a daily EOD snapshot cannot be assumed filled at that same day's EOD Ask. V1 artifacts remain in the separate `spy_far_tail_holding_trigger_v1` folder as exploratory diagnostics and must not be treated as executable performance. V2 uses a next-session exact-contract quote for the hedge entry.

## Frozen baseline
- QQQ LONG PUT 1 : SPY SHORT PUT 3; primary exit policy `HOLD_20_OR_DTE_LE_7`.
- Existing DTE14/DTE45 arms and five fixed phase schedules remain unchanged.
- Original base entries, selected contracts, quantities, exits, and P&L are read-only.
- Before replay, all base-ledger SHA-256 values must exactly match the prior unconditional overlay manifest. Changed, missing or extra hashes fail closed.

## Predeclared holding-period triggers
Each rule fires once at its first qualifying observation strictly after base entry and strictly before the original base exit:
1. **Exact short PUT Delta:** absolute Delta of the selected exact SPY short PUT is >= 0.35 on the current day.
2. **SPY underlying drawdown:** current SPY close is >= 5.0% below the actual SPY entry spot.
3. **Package mark-to-close loss:** executable package P&L using the current exact QQQ long-put bid and SPY short-put ask is <= -50% of the initial gross SPY short-put credit.
4. **OR composite:** first observed day any of the above fires; component reasons are retained.

No parameter sweep or outcome-based threshold selection is performed. Missing prices, Delta or quotes are not forward-filled. Package MTM is unavailable unless both current exact-contract quotes and close-side displayed-size gates pass.

## Causal hedge-entry timing (V2 correction)
- Day T uses only data observed on day T to evaluate the trigger and select a candidate same-expiry far-tail SPY PUT.
- The candidate is **not** assumed purchased on day T. The only entry attempt is on the next SPY underlying trading session, using that session's quote for the exact contract selected on day T.
- No same-day substitution, fallback to day-T quote, forward-fill, or retry on a later session. If the scheduled next-session quote is missing/invalid, the hedge is not entered. If the Ask depth is below 1 or 3 contracts, that quantity is unavailable.
- If a gap changes the candidate's Delta or moneyness before next-session entry, record the actual next-session Delta/spot; do not retroactively reselect the contract based on future outcomes.
- An entered hedge is held to the original base trade's exact exit date and marked/closed at that same contract's Bid and displayed size. An invalid or undersized exit leaves the conditional realized result missing.

This is deliberately conservative and reproducible with daily source data. The next-session daily Ask is still only an execution-timing proxy, not a timestamped verified fill.

## Hedge comparison and accounting
- Candidate targets: existing ~2.5-, 5- and 10-absolute-Delta SPY PUTs, 1x and 3x.
- Modeled cost: USD 0.05 per option-share per side plus USD 0.65 per contract per side.
- No trigger or failed next-session entry leaves the base realized outcome unchanged. Entered hedge with missing/undersized original-exit quote leaves the conditional outcome unknown, never zero or base P&L.
- Compare conditional versus no-hedge only on exactly the same rows whose conditional realized outcome is known. Report trigger rate, feature coverage, next-session entry coverage, exit coverage, unknown outcomes, total entry debit, average paired P&L change, loss-improved / turned-positive counts, and annual entry-year behavior.
- `worst_trade_improvement_usd` means the P&L change on the **exact original worst-loss trade** within the matched known-outcome sample.
- `difference_between_worst_observed_pnls_usd` is the difference between the minimum conditional P&L and minimum baseline P&L; those minima can belong to different trades, so this is not a paired improvement.
- Include identifiers for both minimum-outcome trades within each phase so results can be traced.
- Do not select a winner solely from the 2023–2025 holdout table. All rules/configurations form a predeclared comparison family; later forward validation is required for strategy selection.

## Chronological split and known limits
- Descriptive/development entries: 2018–2022.
- Locked rule-family holdout entries: 2023–2025.
- This is not globally virgin: the repository previously analyzed overlapping historical years for other strategy research. A globally untouched forward holdout needs newer source-pinned option-chain history beyond 2025.
- The five phase schedules overlap and are not independent samples or confidence intervals.
- Source files are byte-count/Git-blob-SHA verified against the frozen source-engine pins. EOD quote/depth is not proof of fills.
- No broker connection, orders, main-branch merge, NAV/margin, financing, early assignment, forced liquidation, or cross-position capital model is included.


## V2.1 decision-quality metrics
- In addition to conditional mean P&L, the report records mean paired P&L change on actually entered hedges, lower 5th-percentile and bottom-5%-mean position outcomes, change in trade loss frequency, and modeled opening debit per successful entry.
- The bottom-5%-mean change compares the bottom tail of the baseline and conditional samples; those observations need not be the same positions. It is a trade-level distribution statistic, not portfolio MaxDD/CVaR.
- The exact global worst resolved baseline trade is reported separately from the worst baseline trade among matched rows. If the global worst trade has an unknown conditional result, its paired change is missing and must not be imputed from the next-worst matched trade.
- Count fields are rendered as counts, never currency. The report title, manifest schema and output directory identify the V2 replay.
