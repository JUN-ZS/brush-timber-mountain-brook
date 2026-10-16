# Hybrid V3 — Put Ratio Evidence Module V1

**Status:** composable research overlay; deployment blocked. This describes an implementation and evidence contract, not approval to add Put Ratio to the Frozen Original Hybrid holdings.

## Design: split the evidence engine, compose the review

The module intentionally has a narrow boundary:

put_ratio_evidence_v1.json (source-pinned research output)
→ read-only GET /api/research/put-ratio-evidence
→ put_ratio_evidence.js (pure evaluation of inputs + snapshot)
→ optional Hybrid review panel and append-only decision journal.

The research statistics remain independently testable. The Hybrid UI can display them next to its live/frozen decision and optionally include the summary in the current human review. This is not a separate permanent application/main branch, nor does it rewrite Frozen Original Hybrid policy constants.

## Inputs

- Existing Hybrid NAV (manual ledger NAV field).
- Research direction and ratio N (1:N or N:1).
- One of the stored historical exit policies.
- Tail-loss budget as % of NAV.
- NAV-relative manual profit-warning line.
- Optional current net-liquidation P&L estimate, holding-session age, option DTE, manual RV20 and selected QQQ price-path horizon.
- Explicit COMBINED_REVIEW checkbox. Unchecked means informational/isolated; checked attaches the overlay to the current Hybrid review/journal.

Current P&L, age, DTE and RV20 are manually entered measurements, not silently read from unrelated current-market fields. Unfilled inputs remain unknown.

## Historical evidence contract

- The pinned option cohort is 62 non-overlapping LONG PUT 1 / SHORT PUT 5 episodes from 2018-03-01 through 2025-12-15.
- Each policy summary is one fixed ratio unit per episode; it is neither compounding nor a NAV-scaled account replay.
- The serial option-side equity curve has 1,960 QQQ sessions, 13 policy series, and 11 unknown daily marks on the direct replay curve. Unknown marks remain null.
- The saved data, curve and $800/$1,000 first-hit analysis are bound by source blob SHAs in the manifest. The app does not re-pick contracts, forward-fill quote marks, or synthesize missing option P&L at run time.
- Direct option history / strategy MaxDD is only shown for the exactly matching SHORT_HEAVY N=5 configuration. Other directions or N values can show their distinct terminal payoff arithmetic, but never inherit 1:5 win rate, drawdown, or policy-trigger statistics.
- NAV-relative target money is compared only with directly replayed fixed target levels ($500/$800/$1,000/$2,000). No interpolation or borrowing of another target's time statistics is permitted.
- RV20-conditioned downside statistics describe QQQ underlying price windows, not the probability of losing on the Put Ratio.

## Composition with the Hybrid decision

The primary V3 engine remains the source of Frozen market-regime decision and its Current → Target / action queue. The overlay produces a separate PUT_RATIO_RESEARCH_OVERLAY_OUTPUT_V1 containing evidence status, matched history, serial drawdown statistics, tail budget, profit/time/volatility alerts, provenance, and an optional human-review status.

- BLOCK_PUT_RATIO_ADDITION means the selected terminal-tail-loss budget allows zero complete Put Ratio units under the historical terminal-payoff estimate. It does not rewrite unrelated QQQ core or VXX sleeve targets.
- REVIEW_PUT_RATIO_SCENARIO asks for human review of the research scenario. It is not an execution command.
- Data/schema/source mismatch returns PENDING/BLOCKED and does not replace the primary Hybrid action.
- Journal rows retain the primary engine action/target separately from research_evidence, including the source manifest and module status.
- primaryHybridActionMutation=false, primaryHybridTargetMutation=false, and executionEnabled=false are explicit output contract invariants.

## Runtime / refresh

The V3 terminal loads the snapshot from the local API endpoint. The snapshot records Git blob IDs for the upstream research data, curve and profit-warning analysis; the API validates the schema, 62-episode count and source-window alignment on each read. The user can refresh the module alongside the existing market snapshot. A later controlled refresh can regenerate the snapshot only from a passing, SHA-pinned replay; it must not silently fetch or rewrite historical evidence in the live decision loop.

## Verification

- tests/put_ratio_evidence_test.js: pure evaluation, source gates, selected policy, matched ratio guard, tail-budget zero, DD tiers, direct-dollar target matching, time × volatility alerts, and no primary policy mutation.
- tests/put_ratio_evidence_api_test.py: read-only snapshot load, schema/source-window fail-closed checks, cohort/curve dimensions and source hashes.
- Existing golden_test.js and provider fixture tests remain required. The module is not considered integrated until the same PR head passes these checks.

## Evidence boundary

This is EOD quote-side replay from a public preservation mirror, not confirmed exchange fills. Source option history ends 2025-12-15. Exact quote timestamps, broker margin, interim liquidation, assignment, forced liquidation, and executable position capacity remain unverified. Historical win rate is not a deployment approval. Current default $80,000 NAV at a 1% tail budget permits zero 1:5 ratio units under the observed $214,696.90 worst terminal loss. Deployment remains **BLOCKED**; no broker order API is involved.
