# QQQ Hybrid Research Measurement Contract

**Status:** pre-registered evaluation rules for future research; no live strategy policy change. Thresholds below are engineering/research acceptance criteria, not claims that any return target is achievable.

**Latest measured snapshot:** [QQQ Hybrid Measurement Scorecard — Replay #148 / Audit #177](QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN148.md). This immutable run snapshot is tied to code head `57fd41b2d47c8721b445a6f704610e0e524a890e`; it does not imply later documentation commits were replayed. Its disposition remains Accuracy **BLOCKED** for trade-performance use, Generality **NOT DEMONSTRATED**, and FAR CALL integration **FAILS CURRENT BASE SCREEN**.

## 0. Practical measurement when a condition may be wrong

**Do not wait for perfect inputs to learn something. Measure whether the plausible error changes the decision.** This section allows imperfect, clearly-labelled inputs for exploration; it does not relax the hard gates for primary sizing, contract safety, or strategy promotion.

### Repeatable workflow

For each uncertain condition, record: (1) what may be wrong; (2) its evidence class (OBSERVED, DERIVED, ESTIMATED, HYPOTHETICAL, or UNKNOWN); (3) a defensible low/base/high range and where that range came from; (4) the output under each case; and (5) whether the conclusion changes. Prefer official exchange/clearing documents and broker records; use reputable vendor methods as comparison conventions; when evidence is unavailable, use an explicit stress grid rather than silently choosing a precise point estimate.

Recalculate on the **same dates, same contracts, same capital path and same cost convention**. Change one uncertain variable at a time first; then run one combined adverse case to expose interactions. Report both the absolute change (USD, shares/contracts, percentage points) and a normalized change (percentage of NAV or the relevant risk budget). Record discrete changes too: selected contract, whole-contract capacity, action, and whether a risk limit or pre-registered acceptance bar is crossed.

### Materiality classes

| Class | Practical test | What may proceed |
|---|---|---|
| **CRITICAL** | Wrong contract/deliverable/multiplier; invalid or future timestamp; lookahead; an action changes; or a capital/margin/max-loss limit is crossed | Continue a labelled diagnostic or stress scenario, but block affected capacity / trade-ready status / promotion |
| **MATERIAL** | Selected option legs change; whole-contract capacity changes; the effect changes sign; risk usage changes by >= 5% of the shared max-loss pool; or an existing return / drawdown / ES95 acceptance bar is crossed | Continue research under explicit scenarios and use the adverse case; do not promote on the base case alone |
| **TOLERABLE FOR RESEARCH** | No action, contract, whole-contract count, or hard risk limit changes, and the output remains inside the pre-registered project tolerance under the plausible range | Use the approximation with its range and caveat; do not imply it is exact |
| **UNBOUNDED / UNKNOWN** | No defensible range exists from a source or observed data | Do not invent a point estimate. Keep the field UNKNOWN and compare explicit hypothetical scenarios |

The 5% risk-pool trigger is an **internal triage rule**, not a universal finance law. It is not used to excuse a discrete contract-count change or a hard-limit breach: either is material on its own. Existing promotion bars (+0.50 percentage points of CAGR, <=1.00 percentage point MaxDD worsening, or the separately defined downside/deployment bars) remain the strategy-level tolerances.

**Missing-data coverage is not just a percentage.** Compute coverage against all expected sessions, list missing dates, and inspect whether the gap is clustered in a shock regime or at the end of the sample. A small terminal gap may leave most diagnostics useful while still making terminal NAV / final-window performance incomplete. Do not replace missing observations with zero or forward-fill option quotes.

### What the current QQQ evidence says

These are measured examples from the repository's pinned EOD diagnostic, not new strategy-return claims:

- **Underlying-price basis is material.** The repository spot input is median -2.72% versus raw nominal close; the selected short / wing differs under raw versus adjusted geometry on 96.61% / 95.84% of matched dates. This is not a tiny price-noise problem. The option replay must use contemporaneous raw nominal spot for strike geometry, while the adjusted series can remain a separately-labelled core total-return proxy.
- **Fill realism is material and regime-dependent.** Median VIX-proxy estimated credit exceeds the observed EOD short-Bid minus wing-Ask reference by $0.181/share. Model half-spread haircuts are narrower than observed on 30.0% of short legs and 57.2% of wings overall, rising to 81.5% / 100.0% when VIX >= 35 (54 pairs). Do not solve this with one universal correction; retain the explicit $0.000 / $0.025 / $0.050 / $0.100 per-leg sensitivity grid and calibrate against instrument- and regime-matched quotes or actual execution records.
- **A high coverage percentage can still have a consequential gap.** The pinned source covers 1,946 raw-spot pairs out of 1,971 expected sessions (98.73%), but both underlying and option files stop on 2025-12-15, leaving 11 consecutive expected sessions at the sample end uncovered. Earlier-period quote-shape analysis can continue; full-window terminal performance cannot be called complete.
- **What is already enough to decide:** the existing FAR CALL screening report is negative across tested budget/cost arms and has incomplete portfolio marks. Do not tune its stop/strike rules to rescue the already-reviewed window. Keep the overlay research-only while improving measurement; do not alter the Frozen Original Hybrid on this evidence.

### External reference conventions (not automatic truths)

- [ORATS backtester methodology](https://docs.orats.io/backtest-api-guide/backtester-methodology.html) publishes a two-leg slippage convention of 66% of each leg's quoted spread. Use this as one vendor convention for comparison, not as a fill guarantee or an instrument-independent constant.
- [OCC information memos](https://infomemo.theocc.com/infomemo/search-memo) are the authoritative starting point for adjusted-option roots and deliverables; ticker/strike alone may be insufficient.
- [Cboe's term-structure discussion](https://www.cboe.com/insights/posts/inside-volatility-trading-is-vix-backwardation-necessarily-a-sign-of-a-future-down-market/) treats contango/backwardation as curve states, not a deterministic forecast of market direction.

This protocol distinguishes two questions: **"Is the approximation good enough to investigate the effect?"** and **"Is the evidence strong enough to size/promote a real trade?"** The first often can proceed with ranges; the second still must pass the relevant hard gates below.

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
| Option underlying price basis | Historical option strikes/marks/payoffs use contemporaneous raw nominal spot on the same contract basis, or an explicit corporate-action transformation is documented | 100% of option-pricing rows have raw/nominal spot provenance or a versioned transformation | Adjusted-close stock series is passed into option strike, delta, premium, or payoff formulas without a documented transformation |
| Per-leg spread realism | Compare modeled half-spread/mid against observed (Ask−Bid)/2 ÷ Mid for both short and wing; where an observed quote exists, report short Bid − wing Ask separately | 100% of trade-replay legs use observed quote-side prices or a documented adverse fill no tighter than observed leg spreads | A VIX-only haircut narrower than observed leg-level spreads is treated as an executable credit/fill |
| Contract deliverable | Verified OCC/clearing contract ID, multiplier, share deliverable, cash component and applicable effective date | 100% of contracts used as trade-ready have verified terms **and a supported payoff calculation** | Any adjusted deliverable is released into sizing based only on an operator note/checkbox, without an implemented payoff model |
| Prospective fill comparison | Match operator-entered short/long OCC symbols to the exact observed candidate; require source quote `observedAt` ≤ reported fill time ≤ `observedAt` + 15 minutes and source/freshness gates passing at capture. This is a comparability gate, not source authentication. | 100% of included comparisons match both legs and time window; excluded reported fills remain counted with explicit reasons | A wrong-leg, time-inverted, invalid-time or >15-minute quote/fill pair enters the reported-fill mean, or excluded rows disappear from the denominator |

Scoring guide: 100 = all hard gates pass. 90–99 = no critical fail, only disclosed non-trade-critical metadata warnings. Below 90 = research-only. Any BLOCK row overrides the numeric average.

**Position Register boundary:** the subtotal is *METADATA-COMPLETE*, not *evidence-qualified*. A source-type choice, reference string, timestamp, or terms checkbox confirms only operator-entered metadata; this app does not independently fetch/authenticate cited broker documents or reconcile actual account cash flows. UI and AI handoff must preserve that limitation.

**Separate mark-quality axes:** report mark status flags (missing, invalid, stale, or unsupported source classification) separately from source-metadata gaps (a known mark with UNKNOWN / MODEL_ESTIMATE source or no reference). These counters can overlap and must not be conflated as one cause or interpreted as independent evidence of source authenticity.

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

## Option Chain Lab execution hygiene (measurement only; no order authority)

The Option Chain Lab now reports relative quote width for each leg as `(Ask − Bid) / midpoint × 100`, using the pre-registered bins already used in trade attribution: `≤10%`, `>10–25%`, and `>25%`. Candidate rows expose each leg and the worse-leg band. A wide quote remains visible as a scenario, but it must not be mistaken for liquid execution evidence; the band is a review aid, not a probability or an order signal.

Quote observation timestamps must include an explicit ISO 8601 UTC offset (`Z` or `±HH:MM`). The Lab never parses an unzoned local timestamp using the browser machine timezone. An observation older than 15 minutes is labelled stale for manual execution review; missing, invalid, unzoned or future timestamps are separately blocked. Users may still inspect arithmetic on a stale/untimed scenario, but its status stays non-executable. Timestamp freshness does not authenticate the source, remove any vendor delay, or prove a fill.

Every selected vertical also reports additional adverse slippage per leg of `$0.000`, `$0.025`, `$0.050`, and `$0.100`, aligned with the existing listed-contract replay contract. Under each sensitivity, stressed net credit is `short Bid − wing Ask − 2 × additional slippage per leg`; if stressed credit is not positive, the scenario is `NO TRADE`. Max loss and whole-spread quantity are recomputed from the stressed credit and the explicitly entered scenario risk budget. These amounts are hypothetical sensitivities, not measured execution costs or guaranteed capacity. No Option Chain Lab state authorizes a broker order.

## Primary option-sizing evidence gate and Lab handoff (measurement only; no order authority)

Public Yahoo option-chain candidates are scenario inputs in the main terminal. A mathematically valid credit spread does not qualify for primary sizing while the multiplier/deliverable is unverified or the provider has not supplied an authenticated quote timestamp. Such candidates remain PENDING in the main shared-risk budget rather than yielding capacity from an assumed multiplier.

The Option Chain Lab provides a narrow handoff for QQQ CALL and VXX CALL only. It requires a named user screenshot transcription or broker export, recorded source/contract metadata, a standard 100-share deliverable, exact root/expiry/right/strike identity, two valid Bid/Ask legs, explicit operator attestation, and a UTC-offset observation time recorded by the operator within 15 minutes. Put chains and adjusted VXX roots remain outside the primary risk pool. The main engine revalidates packets on every plan recalculation, including leg-price arithmetic, OCC-style identities, contract root, multiplier, timestamp age and expiry horizon. A stale, unzoned, incomplete, mismatched or tampered packet returns to PENDING.

Important boundary: “recent” means recently recorded by the operator, not a provider-authenticated exchange quote timestamp. The program does not independently authenticate screenshot/CSV contents, evidence URLs, broker deliverables or fills. A passed handoff is a MANUAL RISK INPUT / HUMAN REVIEW state, never trade-ready and never permission to place a broker order. The bridge uses same-origin browser local storage and does not call a broker.

## 4. Current known limits

- Historical options replay in PR #98 uses DERIVED_BS_VIX marks, not a full historical OPRA quote-and-fill replay.
- VXX stock borrow rate of 3% is an assumed planning input, not verified historical broker data.
- The uploaded chain fixture is an observed transcription of visible rows only. Its exact quote timestamp and contract deliverable are not verified.
- Run #5 confirmed the historical QQQ option layer's input row.qqq comes from a series labelled adjusted close. It shifts target strikes by $5–$9 on two fixed EOD checkpoints and the same-listed-strike model credits by $0.33–$0.42/share. The model-to-quote gap is larger than this isolated spot-basis effect; selected per-leg source IVs must now be captured before attributing the rest.
- Run #5 also found 2020 actual per-leg half-spread/mid ratios of 42.6%–50.0% against a model haircut of 7.84%; in 2024 one wing was 19.44% against a 4.31% model haircut. The VIX-only spread function does not encode strike-specific liquidity. Do not treat that modeled quote as an executable fill.
- Run #11 extended the spot/IV comparison to eight dates. The universe QQQ spot remained 0.90%–3.73% below raw close; raw-target short/wing Deltas ranged 0.044/0.008 to 0.195/0.145, and the adjusted-target pair on 2020-01-15 reached 0.527/0.396. The proxy/source-IV ratio also changed sign around 1.0 across regimes (short 0.88×–1.62×, wing 0.84×–1.70×). Price-basis and IV errors can compensate each other; do not use that compensation as a model validation.
- Run #8 found the VIX-derived proxy short/wing volatilities were 1.37–1.62× / 1.40–1.77× the public chain's reported per-leg IV on four matched pairs. Repricing at raw spot with those source IVs reproduces the snapshot midpoint closely, but that may be circular because the source IV may be computed from the same quote. This is attribution evidence, not independent validation.
- Underlying daily data through 2026-09-04 cannot substitute for a full VXX historical option chain.
- The 2018–2026 range already reviewed in prior research PRs #97/#98 is not a virgin, untouched final lockbox. A later 60/20/20 split within that same familiar range may be a chronological holdout for a new, pre-specified comparison, but it must be labelled previously exposed / development-revisit rather than blind OOS. Claim a true untouched lockbox only for data or dates that were not used to design, select, or tune the candidate.
- Run #11's raw-spot + per-leg source-IV executable-credit gap varied from roughly -$0.326 to +$0.182/share across eight dates. The error direction changes after changing IV basis, so no one-direction correction is justified. Source IV may be derived from the same quote midpoint and the fill haircut is still modeled; this is attribution, not independent pricing validation or proof of fills.
- None of the thresholds above changes the frozen Original Hybrid policy or grants broker-order permission.


## Full-history QQQ EOD quote evidence — Run #16 (research-only)

Run #16 passed the pinned-file and source-integrity checks, but the usable source ends on 2025-12-15 although the requested comparison window ends 2025-12-31. Its first coverage denominator was based on dates present in both the underlying-price source and the repo universe; this excluded 11 expected late-December sessions. Treat the Run #16 coverage percentage as source-overlap coverage, not full-window coverage. The follow-up audit fixes the denominator to the full repo-universe session index and reports missing underlying prices and option rows separately.

On 1,946 raw-spot matched EOD pairs, the median model-minus-observed short-Bid/wing-Ask credit gap was +$0.181/share for the VIX-derived proxy, and the median absolute gap after replacing proxy IV with source-reported per-leg IV was $0.060/share. The latter may be circular because source IV may be calculated from the same quote mark. The modeled per-leg half-spread haircut was narrower than observed on 30.0% of short legs / 57.2% of wings overall, and 81.5% / 100% in the VIX >=35 subset.

This evidence keeps the **Option underlying price basis** and **Per-leg spread realism** accuracy gates **BLOCKED for trade replay**. EOD snapshots are not decision-time fills; the source has no VXX option history; these measurements make no CAGR, MaxDD, or incremental-edge claim. The frozen Original Hybrid and broker-order boundary are unchanged.


## Corrected full-history QQQ EOD quote evidence — Run #18

The corrected coverage run passed against the current PR head. Expected sessions: 1971; raw closes: 1960 (99.44%); option-chain dates: 1956 (99.24%); raw-target pairs: 1946 (98.73%). Both sources end 2025-12-15, leaving 11 expected sessions through 2025-12-31 uncovered.

Median repo QQQ input vs raw nominal close is -2.72%. The proxy median model-minus-observed short-Bid/wing-Ask credit gap is +$0.181/share; source-IV median absolute gap is $0.060/share but source IV is not independent validation. Haircuts remain narrower than observed on 30.0% short / 57.2% wing legs, and 81.5% / 100.0% in VIX ≥35 (54 pairs). **Option underlying price basis** and **Per-leg spread realism** remain **BLOCKED for trade replay**. No threshold, policy rule, performance claim, or broker-order permission changes.

See [Run #18 report](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN18.md) and [summary JSON](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN18.json).


## Run #22 — observed-side and adverse-fill gate review (2026-10-10)

Windows self-hosted [Run #22](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38015730909) completed the SHA-pinned 2018–2025 streaming diagnostic on the PR branch head. The requested window contains 1,971 expected sessions; source spot and QQQ option rows stop on 2025-12-15, so 11 expected sessions to 2025-12-31 remain uncovered. Coverage: raw underlying 99.44%, chain dates 99.24%, raw-spot target pairs 98.73% of expected dates.

The price-basis gate remains BLOCKED: median repo QQQ input vs raw close is −2.72%; target short/wing contract choices differ under raw vs adjusted geometry on 96.61% / 95.84% of matched dates, and repo-input selected-pair median Deltas are 0.28174 / 0.16985 vs intended 0.16 / 0.08. The spread-realism gate remains BLOCKED: proxy median model-minus-observed-side credit is +$0.181/share; observed EOD spread haircuts are wider than the model on 30.0% of short legs and 57.2% of wings.

| Extra slippage per leg (hypothetical) | Pairs with stressed credit ≤ $0 | Median proxy-model minus stressed observed credit |
|---:|---:|---:|
| $0.000 | 0.41% | $0.181/share |
| $0.010 | 0.57% | $0.201/share |
| $0.025 | 1.23% | $0.231/share |
| $0.050 | 2.93% | $0.281/share |
| $0.100 | 13.62% | $0.381/share |

These are scenario assumptions, not measured transaction costs or fill probabilities. Source-reported IV is not independent of source quotes. The diagnostic makes no strategy-return claim and does not change any acceptance threshold, frozen policy, or order permissions. See [Run #22 report](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN22.md) and [summary JSON](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN22.json).
