# Next Experiment Contract — QQQ Far-Call Replay (Research Only)

**Status:** specification only; not a completed replay, not strategy approval, and not a policy change.
**Parent evidence:** QQQ full-history EOD quote alignment Run #22.
**Objective:** determine whether the existing QQQ far-call credit layer has defensible, after-cost incremental value when its option selection and marks are aligned to contemporaneous nominal spot and observed listed contracts.

## Why this is the next experiment

Run #22 found a median -2.72% gap between the repository QQQ input and raw nominal close; raw-vs-adjusted target geometry selected different short/wing contracts on 96.61%/95.84% of matched dates. The proxy credit exceeded observed EOD short-Bid minus wing-Ask by a median $0.181/share. These are quote diagnostics, not portfolio returns. The next experiment must therefore replay the actual strategy rules against listed contracts rather than calibrate another universal coefficient to these aggregate gaps.

## Freeze before execution

1. Pin the exact baseline strategy source SHA, data source SHA(s), contract-selection rule, DTE band, delta targets, wing-width rule, rebalance/exit rules, and all risk-budget semantics. If any rule cannot be recovered from versioned source, mark the replay SPEC_INCOMPLETE and do not infer it.
2. Keep the Original Hybrid frozen. This experiment may compare a research-only QQQ far-call layer; it must not mutate main, live sizing, VXX policy, the shared option-risk pool, or broker-order permissions.
3. Preserve the original configured budget meaning. If 1.2%/2% NAV could mean credit budget or max-loss budget and the canonical source does not resolve it, run both as separately labelled scenarios; never silently choose one.
4. Do not tune parameters against the reported results. All already-reviewed 2018–2025 dates are development evidence, not a virgin lockbox.

## Two time-alignment tracks

- **Track A — same-day EOD diagnostic:** use same-day 4:00 p.m. Eastern chain only to measure candidate availability, contract identity, quote quality, and theoretical executable-side credit (short Bid minus wing Ask). It is not a fill simulation.
- **Track B — conservative delayed-entry replay:** choose the actual Short/Wing contract IDs, expiry, and strikes using information available at session t close. At t+1, reprice only those exact IDs using t+1 quotes; if either leg is absent, stale, unsized, invalid, non-standard, or produces non-positive net credit, skip the entry and do not substitute a new pair selected from t+1 data. Exit/marking must also use a current timestamped observation no earlier than the simulated event. If the source cannot support the event timing, mark it missing; never forward-fill an option quote or claim an intraday fill from EOD data.

Report both tracks separately. Track B pins contract selection at signal time and reprices only those exact contract IDs on the next session. It is still an EOD proxy, not proof of executable fills. The source README reports a 4:00 p.m. US Eastern snapshot, but the exact tick timestamp remains UNVERIFIED.

## Price, contract, and fill invariants

- Use raw nominal QQQ spot for option strike geometry and listed-contract payoff. Use adjusted prices only for stock total-return accounting, with explicit separation in code and column names.
- Select actual listed strike/expiry rows from the source. Do not synthesize a strike and then pretend a listed contract existed there.
- For credit vertical entry, reference short-leg Bid minus long-wing Ask. Require positive, non-crossed quotes, same underlying/right/expiry, correct strike ordering, and a verified contract multiplier. A non-positive credit or invalid leg means NO_TRADE/PENDING, not a fallback to midpoint.
- Expose commissions separately. Stress extra adverse slippage per leg at $0.00, $0.025, $0.05, and $0.10 as scenario assumptions; label them HYPOTHETICAL, not measured fees.
- Exclude or block any adjusted/non-standard option root unless the actual deliverable and payoff normalization are sourced and tested.
- Same-close signal and same-close fill are forbidden unless an independent timestamped execution record supports it.

## Required counterfactuals

1. Frozen baseline without the QQQ far-call layer.
2. Same baseline plus the historical/model-only QQQ far-call layer as currently implemented, explicitly labelled MODEL_ONLY where applicable.
3. Listed-contract, observed-side quote replay under Track B.
4. Track B with each adverse-cost scenario.
5. A no-trade control on dates with missing/invalid quotes, to show whether missingness itself changes exposure or performance.

The comparison must be paired by date and portfolio path, not compared as unrelated terminal numbers. Keep position limits, funding, and all other strategy components identical across arms.

## Required outputs and tests

- Per event: signal timestamp, quote timestamp, raw spot, source/row ID, contract root, expiry, strikes, DTE, Bid/Ask, credit, max loss, size, cost assumptions, trade/no-trade reason, and source status (OBSERVED, DERIVED, ESTIMATED, HYPOTHETICAL, UNVERIFIED).
- Coverage: expected sessions, missing underlying, missing chain, invalid pairs, no listed strike near target, adjusted roots blocked, and quote timestamps that cannot support the event.
- Performance: net CAGR, daily MTM MaxDD, Sharpe, ES95, turnover, trade count, percentage of no-trade days, and per-regime results. Reconcile daily portfolio NAV and all option cash flows to <= $0.01.
- Generalization: report calendar-year and pre-defined volatility-regime results; use at least five rolling windows when feasible. Since this history has been inspected, mark results DEVELOPMENT/REVISIT, not virgin OOS.
- Cost: show base plus all prescribed adverse-cost scenarios; do not choose one after seeing the results.
- Regression tests: raw vs adjusted spot cannot share the same variable/field; no same-close lookahead; invalid/adjusted contracts cannot size; non-positive credits cannot trade; missing quotes never forward-fill; NAV reconciliation within $0.01; run results reproduce from pinned inputs.

## Decision rule

The replay is diagnostic only until source timing, listed contract identity, contract terms, and fill/cost handling are all explicit. Any critical accuracy failure blocks performance interpretation. Passing code tests means the replay is reproducible, not that the strategy has an edge.

Only consider integration if a pre-registered goal passes the existing measurement contract without weakening thresholds after results are observed. Otherwise preserve the frozen baseline and record the negative result.

## Known limits carried forward

- Current QQQ preservation mirror stops on 2025-12-15; the requested range through 2025-12-31 is incomplete.
- Its EOD snapshots do not prove fills at the strategy decision time.
- This dataset does not contain VXX option history; VXX option marks remain model-derived and cannot be represented as OPRA replay.
- The 2018–2025 interval has been repeatedly inspected; it is not an untouched final holdout.