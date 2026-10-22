# QQQ LONG PUT / SPY SHORT PUT Fixed-Ratio Size-Gated Replay V1

## Objective

Verify whether in-sample candidates from the earlier ratio-sensitivity grid survive a fresh quote-side replay with fixed N and explicit displayed-size checks. Run two candidates over the same historical window and the QQQ-underperforms-SPY trailing-20-session entry signal:

- QQQ LONG PUT 1 : SPY SHORT PUT 6
- QQQ LONG PUT 4 : SPY SHORT PUT 5

The first is a high-short-put-exposure discovery candidate from the earlier post-hoc sizing grid; the second is a closer-cash-premium comparison/reference. Both were selected after viewing in-sample sensitivity, so this is still in-sample validation, not out-of-sample confirmation.

## Frozen mechanics

- Source hash/byte pinning, option contract selection, requested 2018-03-01 to 2025-12-15 window, signal condition, 30–60 DTE (target 45), same expiry, absolute Delta nearest 0.25 and eligible 0.10–0.50 stay the same.
- Entry is no earlier than the session after the signal. Selected exact contract IDs are held; no forward fill or contract substitution.
- Fixed contract quantities are selected before each entry: QQQ N=1 / SPY N=6, and QQQ N=4 / SPY N=5.
- Entry requires QQQ ask size >= QQQ long N and SPY bid size >= SPY short N. If size is inadequate, entry is deferred on the same selected contracts; if no valid entry before expiry, it is counted as skipped.
- Exits require QQQ bid size >= QQQ long N and SPY ask size >= SPY short N. Exit is deferred to later quotes if size is inadequate; expiry/source-end without a valid close remains unresolved.
- Compare 5/10/20-session holds and DTE<=7, using QQQ long exit Bid and SPY short exit Ask.
- Base costs stay at USD 0.05 per option share per side plus USD 0.65 per contract per side; preserve cost sensitivity.
- Results for both ratios are generated in separate output folders in one workflow, sharing the locally hash-verified source cache to avoid duplicate downloads.

## Required reporting

For each fixed ratio: entry filter checks and pass counts, entries accepted/deferred/skipped, resolved/unresolved exits, win rate, mean/median/total/worst P&L, base/zero/stress cost outcomes, premium debit/credit mismatch, and SPY strike-based assignment obligation. Show each exit policy and do not collapse unresolved episodes into zero P&L.

## Interpretation constraints

- Displayed EOD quote size is an execution screen, not a confirmed multi-leg fill.
- A fixed ratio intentionally does not equalize premium flow. Do not describe it as equal-premium or equal-risk.
- SPY short-put credit does not cap risk. Strike-based assignment obligation, margin, gap risk, volatility repricing, exercise/assignment costs and forced liquidation are not fully modeled.
- Hypothetical alternative ratios in the sensitivity output remain rescalings, not validated executions.
- Because candidate ratios were identified after viewing the in-sample sensitivity grid, no result here proves robust alpha; any positive result requires a predeclared prospective or genuinely untouched out-of-sample test.
- No merge to main, app-size change, broker connection, or live order.

## Outputs

- results/fixed_1_6: all reports for QQQ 1 / SPY 6.
- results/fixed_4_5: all reports for QQQ 4 / SPY 5.
- Each folder includes raw episode data, entry cohort, skipped entries, cost and sizing sensitivity, expiry-shock grid, SHA-pinned source manifest and summary.
