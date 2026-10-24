# SPY Far-Tail PUT Protection Overlay — Research Contract V1

## Research question
Does buying a same-expiry, far-out-of-the-money SPY long PUT improve the downside of the frozen QQQ LONG PUT 1 : SPY SHORT PUT 3 cohort after premium costs, entry/exit quote-side prices and displayed-size checks?

## Frozen baseline
- Read-only inputs: actual DTE14 and DTE45 guarded-replay trade ledgers, five immutable anchor phases, both HOLD_10_OR_DTE_LE_7 and HOLD_20_OR_DTE_LE_7 exit policies.
- No change to original contract selection, trade ledger, entry cadence, quantities or exit logic.
- Historical chain source remains anahatsingh-ui/options-dataset-hist at commit 37f6c456fe1a4775c875673fb8ef907d5cd2fd66. Every SPY Parquet file is checked against its pinned Git blob size and SHA.

## Overlay selection matrix
- Tail A: target absolute Delta 0.025 (Put Delta about −0.025), eligible band 0.01–0.08.
- Tail B: target absolute Delta 0.05 (Put Delta about −0.05), eligible band 0.01–0.08. The 2.5-delta and 5-delta targets share the same eligibility band to isolate the effect of target-distance ranking.
- Tail C reference: target absolute Delta 0.10, eligible band 0.05–0.15.
- Each selected tail contract is tested with quantity 1 and quantity 3.
- Select on the base cohort's actual entry date, at the exact base SPY short-put expiry. Require a standard listed SPY put, strike strictly below SPY entry spot, valid bid/ask and positive bid.
- Selection ranking: closest absolute Delta, larger displayed ask size, larger open interest, tighter relative spread, then stable contract ID. The chosen contract does not change between 1x and 3x; displayed entry ask size gates each quantity.
- Entry uses ask; exit uses bid. Per-side costs per contract: USD 0.05/share slippage plus USD 0.65 commission.

## Accounting and unresolved handling
- Tail P&L = quantity × 100 × (exit bid − entry ask) less modeled entry and exit costs.
- Paired realized comparison requires the base trade to be resolved AND a valid quote for the exact tail contract on the same base exit date, with sufficient displayed bid size.
- The displayed-size gate is a screen, not proof of a fill. Missing or insufficient exits are not promoted to realized P&L; a valid quote may be shown as MTM with hypothetical exit costs.
- Base-unresolved trades stay unresolved even if a tail mark exists. No unresolved P&L is silently set to zero.
- Compare baseline and hedged P&L on the same paired trades, alongside entry/exit coverage. Quote-availability selection bias remains possible.
- No NAV, broker margin, forced liquidation, exercise/assignment fees or real order execution is inferred.

## Expiry stress grid
- Apply SPY expiry spot shocks of 0%, −10%, −20%, −30%, −40%, −50% and −100% from each actual SPY entry spot.
- Calculate intrinsic settlement economics for the SPY short-put sleeve alone, and then for that sleeve plus the tail long put; include opening-side modeled costs.
- This isolates the SPY sleeve; it excludes the QQQ long put, exit time value, assignment fees and margin.

## Required outputs
entry_selection.csv, trade_level.csv, summary.csv, stress_grid.csv, report.md and manifest.json.

## Interpretation limits
- The five anchor phases overlap and are robustness sensitivities, not independent statistical samples.
- Public end-of-day chains are not verified fills and pin hashes establish byte identity, not exchange/OPRA authenticity.
- Far-tail insurance may reduce extreme-loss severity but drag ordinary-period P&L through persistent premium spend. Evaluate premium cost, coverage, paired exits, win rate, worst trade and stress behavior together; no fixed pass threshold is imposed.
