# Walk-Forward MAE Sizing and Strict Same-Contract Reversal — Audit

**Research run:** [GitHub Actions #30](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38911332183)  
**Tested code SHA:** `3f7e2d98ff229d5d9e0a22edef36f383fca77cc2`  
**Persisted outputs:** [run-3f7e2d98](https://github.com/JUN-ZS/brush-timber-mountain-brook/tree/research/qqq-put-ratio-exit-measurement-v1/research/qqq_put_ratio_exit_results_v1/run-3f7e2d98)  
**Source option-chain boundary:** 2025-12-15; 62 source episodes.  
**Status:** research-only; no policy promoted; no App/live sizing/order behavior changed.

## Executive results

- The complete matrix has **1,200 configurations**, and all 1,200 NAV paths were resolved by the model. **92 configurations** reached the searched historical target of 3.14012× starting NAV.
- All 92 target-reaching rows were the original **+1 higher-strike put / −5 lower-strike puts**, starting with **$100,000**. The strict same-contract inverse had **0** target-reaching configurations. Neither orientation reached the $3,140,120 target from $1,000,000 starting NAV.
- The 92 targets were not found at MAE risk budgets below 30% NAV. They comprised 4 rows at 30%, 12 at 40%, 17 at 50%, 29 at 75%, and 30 at 100%. These are parameter-grid counts on repeatedly reused historical data—not independent trials, trade win rates, or future probabilities.
- Across 600 matched NAV-sizing configurations (same starting NAV, exit policy, delay stress, MAE multiplier, and budget percentage), the strict inverse ended higher in **0**, equal in **11**, and lower in **589**. This compares the same sizing rule applied independently to each orientation; the resulting unit counts are not constrained to match.
- The exact inverse does **not** always lose on every individual episode. In the one-unit, `DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE`, zero-extra-delay example for trade 10 (entry 2019-04-30), the original modeled `net P&L = -$922.80` and its exact inverse modeled `net P&L = +$686.20`. However, across 620 episode × policy × delay reference cells (repeated variants, not independent observations), the inverse P&L was higher in only 3 and lower in 617.

## NAV-relative sizing results

The target means ending NAV ≥ 3.14012× starting NAV: $314,012 from $100,000; $3,140,120 from $1,000,000.

| Start NAV | Orientation | Configurations | Reached target | Best ending NAV among rows with ≥30 executed episodes | CAGR | MaxDD | Full-terminal loss / current NAV in that row |
|---:|---|---:|---:|---:|---:|---:|---:|
| $100,000 | Original +1/−5 | 300 | 92 | $763,211.30 | 29.80% | −59.02% | 4,196.19% |
| $100,000 | Strict same-contract inverse −1/+5 | 300 | 0 | $77,505.30 | −3.22% | −23.23% | 8.45% |
| $1,000,000 | Original +1/−5 | 300 | 0 | $1,822,690.50 | 8.01% | −18.66% | 2,590.38% |
| $1,000,000 | Strict same-contract inverse −1/+5 | 300 | 0 | $913,665.80 | −1.15% | −9.10% | 1.98% |

The “best ending NAV” column excludes configurations executing fewer than 30 episodes to avoid ranking near-idle paths as active results. It remains a grid-search diagnostic, not a selected strategy. Lower MaxDD in a row is an observed outcome, not a feasibility or acceptance gate.

### Target-reaching paths and tail exposure

Across the 92 $100,000 original-orientation target rows:

- Ending NAV: $316,115.45–$763,211.30; median $437,672.30.
- CAGR: 15.92%–29.80%; median 20.86%.
- MaxDD: −33.63% to −59.77%; median −43.25%.
- Worst modeled full-to-expiry terminal loss divided by current NAV across episodes: **1,254.61% minimum, 2,194.45% median, 4,425.69% maximum**.
- The target row with the lowest such terminal-loss ratio used a 40% NAV MAE budget, 1.5× MAE stress, and a 5-observation exit-delay stress. Its ending NAV was $321,465.30 (CAGR 16.17%), MaxDD −39.57%, while modeled full-terminal exposure still reached **1,254.61% of current NAV**.
- The lowest-MaxDD target row ended at $510,992 (CAGR 23.29%) with MaxDD −33.63%, but its modeled full-terminal exposure still reached 2,179.53% of current NAV.

This illustrates why neither MaxDD alone nor the managed policy-MAE budget is a substitute for a separate full-terminal, margin, assignment, and failed-exit risk treatment. A target-reaching historical path is not evidence that these exposures are safe or deployable.

## One-unit exact-inversion check

For the fixed-cohort one-unit reference using `DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE` with no added delay stress:

| Structure | Episodes | Positive model P&L | Negative model P&L | Total model P&L across isolated episodes | Positive-rate in this sample |
|---|---:|---:|---:|---:|---:|
| Original +1 higher-strike / −5 lower-strike | 62 | 59 | 3 | +$18,067.60 | 95.16% |
| Exact same-contract inverse −1 higher-strike / +5 lower-strike | 62 | 1 | 61 | −$28,918.70 | 1.61% |

These are isolated historical episodes summed for comparison, not a compounded portfolio result or a future-probability estimate. Six episode/policy samples fail the stricter clean-mark/entry-depth pairing in the corresponding clean reference set; the complete-mark paired sample has 56 cells per policy/delay combination.

## Method and integrity limits

- Walk-forward calibration uses only clean, resolved prior episodes with exits strictly before the next entry; at least 10 are required. Missing daily marks are not forward-filled and cannot train MAE.
- Whole-unit size is `floor(current NAV × budget / (prior worst clean one-unit policy MAE × stress multiplier))`, then capped by observed displayed entry-side depth. Budgets tested: 2/5/10/15/20/30/40/50/75/100%; MAE multipliers: 1.0×/1.5×/2.0×; forced exit delays: 0/1/2/3/5 observed sessions.
- The strict inverse swaps the original option IDs, strikes, entry quotes, and complete quote streams together; it does not substitute different strikes. Original is +1 higher strike / −5 lower strike; inverse is −1 of that exact higher-strike contract / +5 of that exact lower-strike contract.
- In the orientation-to-orientation NAV matrix, each side independently sizes from its own prior MAE history. Therefore the paired comparison matches the **risk-budget rule**, not fixed equal contracts. The separate one-unit reference table provides the equal-one-unit cross-check.
- Costs are modeled as $0.05 per option leg of slippage and $0.65 per contract per side. This is quote-side replay, not verified live fills.
- The option-chain mirror ends 2025-12-15, the period was previously examined, and end-of-day marks can miss intraday MAE. Whole-unit scaling may not be linear. Margin, assignment, market impact, broker liquidation, and unavailable exits are not fully modeled; the 1–5 observation-session delay stress is deterministic, not a delay probability.
- A 100% NAV budget is a sensitivity setting, not approved risk. No live app, frozen Hybrid constants, or broker-order permissions change.

## Source files

- `policy_mae_nav_matrix.csv` — 1,200 dynamic NAV/configuration rows.
- `policy_mae_unit_episode_reference.csv` — fixed one-unit episode/policy/delay references.
- `policy_mae_trade_rows.csv` — per-episode sizing, executed units, P&L, skips, and risk accounting.
- `policy_mae_study_summary.json` / `.md` — run summary and original top historical paths.
