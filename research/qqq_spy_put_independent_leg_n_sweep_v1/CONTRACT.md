# Independent QQQ LONG PUT / SPY SHORT PUT Fixed-N Sweep V1

## Question
Separate the contribution of the selected QQQ LONG PUT leg from the selected SPY SHORT PUT leg, using independent constant contract counts N=1..6, then compare fixed-N pairs against the parent dynamic premium-matched pair.

## Frozen comparison
- Source: committed research/qqq_spy_put_equal_premium_v1/results/latest/trade_episodes.csv from the parent replay branch at the point this isolated branch was created.
- Reuse each source row's exact contract IDs, quote-side entry prices, quote-derived per-leg P&L, dates and exit policy. No new strike selection and no P&L-based contract selection.
- QQQ LONG PUT enters at Ask / exits at Bid. SPY SHORT PUT enters at Bid / exits at Ask.
- Standalone N is independently fixed at 1 through 6 contracts per cohort.
- Paired combinations are included only when QQQ N + SPY N is at most 9, matching the parent study's combined-count cap.
- Base round-trip costs: USD 0.05 slippage per option share per side plus USD 0.65 commission per contract per side. Sensitivity adds zero-cost and USD 0.10/share slippage cases.
- Preserve source unresolved status. P&L, totals, expectancy and win rates exclude unresolved episodes but show the excluded count.

## Calculation
For each leg, use the source episode's gross leg P&L divided by that leg's source variable contract count, multiplied by the hypothetical fixed N. Recompute that leg's round-trip costs for hypothetical N. Pair P&L is the sum of the two scaled gross leg P&Ls minus each leg's own costs. Original dynamic-pair net P&L is provided as a reference.

## Limitations
- This is post-analysis of committed outputs, not a fresh replay of raw option-chain files.
- Fixed N is not re-gated against historical displayed bid/ask size; fixed-N results are quote-price counterfactuals, not verified executable sizes.
- The source-file hash pins file identity, not exchange/OPRA authenticity or actual fills.
- A SHORT PUT premium credit does not cap risk. Report strike-based assignment obligation separately.
- Equal premium is not equal Delta, underlying notional, margin, assignment obligation, tail risk or market impact.
- No live order, broker connection or application sizing change is authorized.

## Outputs
- independent_leg_trade_episodes.csv: source episodes x exit policies x leg x fixed N.
- independent_leg_sizing_summary.csv: fixed-N leg metrics per exit policy.
- independent_leg_pair_matrix.csv: dynamic-pair reference and fixed-N pair metrics.
- cost_sensitivity.csv: each leg / pair across zero, base and stress costs.
- source_manifest.json: input hash, sample counts, formulas and limitations.
- summary.md: report and paired expectancy matrices.
