# QQQ Hybrid Research Measurement Contract

**Status:** pre-registered evaluation rules for future research; no live strategy policy change. Thresholds below are engineering/research acceptance criteria, not claims that any return target is achievable.

## 1. Three dimensions and scorecards

Each change receives independent **Accuracy**, **Generality**, and **Integration** decisions. These are not averaged: any critical fail blocks promotion.

### A. Accuracy (0–100; critical gates still binary)

| Metric | Measurement | PASS threshold | BLOCK condition |
|---|---|---|---|
| Provenance completeness | Required fields present / imported rows: symbol, right, expiry, strike, bid, ask, source, observation date/time & timezone or explicit UNKNOWN, contract ID/deliverable status | 100% of rows carry explicit values or explicit UNKNOWN; never silently impute | Any unlabelled model-generated or copied quote |
| Golden arithmetic | Recomputed credit, max profit, max loss, breakeven, payoff | Absolute error <= $0.01 per contract across golden cases | Any known-case error > $0.01 |
| Bid/ask validity | Positive bid/ask, bid <= ask, spread width > credit > 0 for credit vertical | 100% invalid pairs excluded from candidate sizing | Any invalid pair produces capacity |
| Invalid-input handling | Blank/zero/negative multiplier, blank/negative budget, invalid quantity | BLOCK/PENDING, no invisible defaults | Invalid input auto-converts to standard multiplier, budget, or 1 contract |
| NAV attribution | Sum of layer P&L vs portfolio NAV change | Absolute reconciliation error <= $0.01 at every audited mark | Any unexplained difference > $0.01 |
| Freshness | VX settlement age <= 4 calendar days; spot/VX as-of gap <= 2 calendar days; future/invalid source dates blocked | 100% of used source rows pass | Stale/mixed data can produce ADD/BUY sizing |
| Contract deliverable | Verified OCC/clearing contract ID, multiplier, share deliverable, cash component and applicable effective date | 100% of contracts used as trade-ready have verified terms | Unverified adjusted VXX contract treated as a standard 100-share contract |

Scoring guide: 100 = all hard gates pass. 90–99 = no critical fail, only disclosed non-trade-critical metadata warnings. Below 90 = research-only. Any BLOCK row overrides the numeric average.

### B. Generality (no result-driven tuning)

| Metric | Measurement | PASS threshold | Interpretation |
|---|---|---|---|
| Fixed baseline | Preserve current frozen policy & same data/cost window for paired counterfactual | Exactly the same dates, inputs, costs and portfolio accounting | Different windows/assumptions require a separate comparison |
| Chronological separation | Training / validation / final OOS lockbox | 60% / 20% / 20% chronological split where sample size permits; lockbox is evaluated once after design freeze | Never tune on final lockbox |
| Regime coverage | CARRY, WEAKENING, PRE-SHOCK, SHOCK/backwardation, plus major known event windows where data exists | Report metrics per state; >= 100 daily observations in a state to publish a state metric; otherwise INSUFFICIENT_SAMPLE | Averages must not hide the shock regime |
| Trade count | Completed trades per variant and reported regime | >= 30 completed trades for descriptive trade-level stats; below this, mark low sample and do not claim an edge | 30 is a minimum reporting floor, not proof of statistical significance |
| Rolling windows | At least 5 chronological rolling windows where data permits | Primary effect direction in >= 4/5 windows and no unreported catastrophic failure in the remaining window | If fewer than five valid windows, state the limitation |
| Cost stress | Base costs and an adverse case | Test base assumption and >= 1.5x spread slippage / borrow cost where relevant | A fragile edge that vanishes under plausible costs is not promoted |
| Lookahead/leakage | Signals use only data available at decision time; execution after signal timestamp | 0 same-close lookahead; no overlapping future data in feature construction | Any leakage is a critical fail |
| Trial ledger | Record every tested variant, failure and reason | 100% of attempted variants logged before the final OOS read | No search-until-PASS; report multiple-testing controls if many variants are explored |

For the existing VXX options study, model-generated Black–Scholes/VIX option marks are insufficient to pass the **trade-performance accuracy gate**. They remain useful for stress exploration, but the report must say MODEL_ONLY / NOT_OPRA.

### C. Integration (promotion gate)

A new idea must nominate exactly one primary purpose before test:

1. **Return enhancement:** net-of-cost final OOS CAGR improvement >= +0.50 percentage points; MaxDD must not worsen by more than 1.00 percentage point; Sharpe (rf=0) must not fall by more than 0.05.
2. **Downside protection:** final OOS MaxDD improves by >= 2.00 percentage points **and** daily-return ES95 improves by >= 10%, where ES95 is the arithmetic mean of the worst 5% of daily portfolio returns and improvement means the candidate's absolute downside magnitude is at most 90% of the baseline's; CAGR give-up <= 0.50 percentage points.
3. **Capital deployment / timing:** either the downside-protection gate passes, or net-of-cost terminal NAV is not worse by more than 0.50% of baseline and one pre-selected deployment metric improves by a stated threshold: average unallocated-cash / NAV falls by >= 5.00 percentage points, or time to reach the same target allocation falls by >= 20%, while all capital, margin and option-risk gates still pass. Select the metric and threshold before looking at the lockbox.

These thresholds are project acceptance rules, not universal financial laws. If another objective is selected, update this document in a separately reviewed commit **before** running that experiment, not after seeing the result.

All promotion tracks additionally require: Accuracy hard gates pass; required Generality evidence is present; the effect has an economic explanation not dependent on one isolated event; the user-facing limitation label is retained; and an explicit human-reviewed PR. Otherwise status is RESEARCH_ONLY or INSUFFICIENT_DATA, never silently promoted.

## 2. External source strength: 0–12 evidence triage

This score ranks whether an external claim is worth replicating. It does **not** score truth probability or strategy profitability.

Give 0, 1, or 2 points for each:
1. Authority / source identity.
2. Data and method traceability.
3. Cost and execution disclosure.
4. Instrument match to the proposed trade.
5. Strategy match to the proposed portfolio layer.
6. Out-of-sample / robustness evidence.

Interpretation: 9–12 = prioritize replication; 6–8 = research hypothesis only; 0–5 = background context only. Product mismatch or missing executable option history prevents policy promotion regardless of total.

| Source / claim | Auth. | Data/method | Costs | Instrument | Strategy | Robustness | Total | Use |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ORATS VXX opposite call-spread example (2019) | 2 | 2 | 2 | 2 | 1 | 0 | 9/12 | Highest priority to reproduce the cost methodology; not proof of our Hybrid |
| VTS long-run VXX decay estimate (2023) | 1 | 1 | 0 | 2 | 1 | 0 | 5/12 | Background/scenario input only |
| Cboe contango/backwardation explanation (2022) | 2 | 2 | 0 | 1 | 0 | 1 | 6/12 | Regime hypothesis and warning against directional inference |
| Simon VIX-option study (2017 issue) | 2 | 1 | 1 | 0 | 1 | 1 | 6/12 | Research-design reference; VIX options are not VXX options |
| Arian et al. OOS-method comparison (2024; synthetic controlled setting) | 2 | 1 | 1 | 0 | 0 | 2 | 6/12 | Validation-method reference only, not strategy evidence |
| OCC VXX1 adjustment memo (2024) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Contract authority source, not an alpha study; exact deliverable must be checked per series/date |

Scores are analyst triage judgements. Keep the component scores and source date visible; revise them only with a written reason. The ORATS total is deliberately not a strategy quality score: the source is highly useful for cost conventions but has not validated this specific portfolio or its OOS edge.

## 3. Baseline comparison format

Every experiment report must show, at minimum:

- Baseline and candidate identifiers / source commits.
- Data start/end, observation count, source provenance and unavailable periods.
- Same capital, signal timing, fill timing and cost conventions.
- Final NAV, CAGR, daily marked MaxDD, annualized volatility, Sharpe rf=0, worst day, 5% expected shortfall, state-by-state outcomes, rolling-window deltas.
- Option trade count, percent of rows with executable two-sided quotes, spread width / liquidity exclusions, commissions, slippage, and contract adjustment exclusions.
- Borrow-cost sensitivity for short stock; margin assumptions separated from loss limits.
- Primary objective and the pre-registered acceptance threshold.
- Variant trial ledger including failures; no selected-best-only report.

If the data cannot support a measure, write UNAVAILABLE or INSUFFICIENT_SAMPLE; do not replace it with zero.

## 4. Current known limits

- Historical options replay in PR #98 uses DERIVED_BS_VIX marks, not a full historical OPRA quote-and-fill replay.
- VXX stock borrow rate of 3% is an assumed planning input, not verified historical broker data.
- The uploaded chain fixture is an observed transcription of visible rows only. Its exact quote timestamp and contract deliverable are not verified.
- Underlying daily data through 2026-09-04 cannot substitute for a full VXX historical option chain.
- The 2018–2026 range already reviewed in prior research PRs #97/#98 is not a virgin, untouched final lockbox. A later 60/20/20 split within that same familiar range may be a chronological holdout for a new, pre-specified comparison, but it must be labelled previously exposed / development-revisit rather than blind OOS. Claim a true untouched lockbox only for data or dates that were not used to design, select, or tune the candidate.
- None of the thresholds above changes the frozen Original Hybrid policy or grants broker-order permission.
