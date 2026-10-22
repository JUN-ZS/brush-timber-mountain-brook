# QQQ LONG CALL / SPY SHORT PUT — Equal-Premium Replay V1

**Status:** isolated research only. Default matching limit is 9 total option contracts per cohort; exact LONG CALL : SHORT PUT quantities are selected from entry quotes. Not a trading recommendation.

## Intended comparison

Compare **LONG QQQ CALL versus SHORT SPY PUT**, with the USD premium paid for the long calls matched as closely as whole-contract constraints allow to the premium received from the short puts.

These cash flows have opposite signs. Equal premium debit/credit is only a sizing convention; it does not equalize Delta exposure, ETF notional, collateral/margin, assignment obligation, max loss, or downside convexity.

## Replay convention

- Public preservation source `anahatsingh-ui/options-dataset-hist`, pinned to the existing commit and each file's Git blob SHA plus byte count. Hash identity is not proof of OPRA/exchange authenticity.
- Default window 2018-03-01 through 2025-12-15; option data actually ends 2025-12-15 for QQQ and 2025-12-12 for SPY.
- Select standard-root QQQ CALL and SPY PUT with one common expiration, DTE 30–60 days closest to 45; each leg absolute Delta closest to 0.25 within 0.10–0.50. No P&L optimization.
- Select contract IDs on signal-date quotes/Delta; actual entry no earlier than the next common observed session, using those exact same IDs.
- At entry, choose positive whole-contract quantities minimizing relative mismatch between `QQQ CALL ask × 100 × quantity` and `SPY PUT bid × 100 × quantity`, constrained by displayed entry-side size and a total contract cap (default 9). Tie-break toward a larger matched premium amount. Ratios may vary per cohort.
- Buy QQQ CALL at Ask and close at Bid; sell SPY PUT at Bid and buy back at Ask. Require displayed size at each entry/exit. No quote forward-fill or contract substitution. Displayed size is not a verified fill.
- Base costs: USD 0.05 slippage per option share per side plus USD 0.65 commission per contract per side; also report zero/base/adverse cost scenarios.
- Compare exit triggers at holding 5, 10, 20 sessions and DTE <= 7. Missing executable exits defer until expiry/source end and remain UNRESOLVED; unresolved rows are never assigned zero P&L.
- Expiry shocks use `max(spot - strike, 0)` for QQQ calls and `max(strike - spot, 0)` for SPY puts; charge entry costs once, assume no closing trade, and label as hypothetical—not historical win rate.
- Fixed-ratio sensitivity is rescaled from the same leg-P&L paths, not a fresh contract-selection replay. All ratios in the sensitivity grid remain within the total-contract cap.

## Required results

Actual selected ratio per cohort; premium debit/credit mismatch; source coverage and SHA manifest; exact contract IDs, strikes, expiry, Delta, entry/exit dates and quote sides; resolved/unresolved counts and resolved-only win rate with nominal Wilson 95% interval; mean/median/total/worst net P&L, leg attribution, profit factor, MAE/MFE, exit delays, cost sensitivity, fixed-ratio sensitivity and hypothetical expiry shocks.

## Interpretation boundaries

EOD quotes are not authenticated fills; Wilson intervals do not fix serial dependence or regime clustering. No 2026 chain results, early exercise/assignment fees, broker margin, forced liquidation, portfolio compounding, taxes, financing, or intraday path are modeled. SPY short-put assignment/tail obligation may dominate loss; premium credits are not a max-loss budget. Do not modify the Frozen Original Hybrid, live sizing, app action targets, broker credentials, order paths, or deployment permissions.
