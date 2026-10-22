# QQQ LONG PUT / SPY SHORT PUT — Equal-Premium Replay V1

**Status: research-only.** This version answers the equal-premium question, rather than assuming a fixed 4:5 ratio.

## Intent
For each historical cohort, buy standard-root QQQ PUT at the displayed Ask and sell standard-root SPY PUT at the displayed Bid, with the **total QQQ put premium debit matched as closely as possible to the SPY put premium credit**. Select whole-contract quantities independently for each cohort, constrained by the displayed entry-side sizes and a combined contract cap (default 9).

The ratio is deliberately variable. No ratio is promoted for live sizing. Equal debit/credit is a cash-flow convention, not equality of Delta, notional, margin, assignment obligation, max loss, or terminal payoff.

## Frozen selection and replay
- Source mirror: anahatsingh-ui/options-dataset-hist, tree commit 37f6c456fe1a4775c875673fb8ef907d5cd2fd66; verify every annual options file's byte count and Git blob SHA before processing. Hashes establish identity, not exchange / OPRA authenticity.
- Window: 2018-03-01 through 2025-12-15; available chain coverage ends 2025-12-15 for QQQ and 2025-12-12 for SPY.
- Select actual QQQ PUT and SPY PUT with a common expiry 30–60 calendar days out, nearest 45 DTE. Each leg's absolute Delta is nearest 0.25 within 0.10–0.50; no P&L-based strike selection.
- Enter no earlier than the next common observed session using the exact same selected contract IDs. Match premiums using QQQ put Ask and SPY put Bid at entry. Quantities are positive integers, do not exceed displayed Ask size for QQQ or Bid size for SPY, and total no more than max_total_contracts (default 9). Choose the quantity pair minimizing relative premium mismatch; tie-break toward the larger matched premium amount.
- Exit QQQ longs at Bid and buy SPY puts back at Ask. Require displayed size for both close legs. No quote forward-fill or contract substitution. Missing executable exits defer; no valid close by expiry/source end remains unresolved.
- Base assumed cost: USD 0.05 per option share per side + USD 0.65 per contract per side. Report zero/base/adverse cost sensitivity.
- Compare holding 5, 10, 20 sessions and exit trigger at DTE <= 7. Unresolved episodes are never assigned zero and are not included in resolved-only win-rate and P&L statistics.
- Expiry shock grid uses each cohort's actual dynamically selected quantities; intrinsic-value scenarios are hypothetical and not historical outcomes. Fixed-ratio sensitivity is labelled separately and does not reselect contracts or re-optimize a premium-matched policy.

## Required report
Each cohort's exact contract IDs, selected ratio, debit/credit, absolute mismatch / match score, strike, expiry, Delta, quote sizes, entry/exit dates; source manifest; entry skips; resolved/unresolved counts; resolved-only expectancy / wins / losses / median / worst; cost sensitivity; ratio and sizing sensitivity; hypothetical expiry shock grid.

## Boundaries
EOD displayed quotes are not verified fills. Size is only a screening gate. Equal premium does not make the legs risk-neutral: long QQQ put is negative Delta and short SPY put is positive Delta, but their magnitudes, volatility sensitivities, assignment and downside tail exposures differ. No margin, forced liquidation, early exercise, taxes, financing, portfolio compounding, intraday paths or live fills are modeled. No main branch, app sizing, broker or order behavior changes.
