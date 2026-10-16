# QQQ Hybrid V4.4 — Assumption Ledger V1

**Status:** branch implementation / needs executable regression verification. This ledger does not authorize HUB execution, alter Frozen Original Hybrid policy targets, or grant broker-order permissions.

## 1. Separate four kinds of input

- **OBSERVED:** quote, position, contract deliverable, timestamp, fill, or statement directly supported by a source artifact and as-of time.
- **USER_ASSERTED:** a manually entered value or source reference. It can support a provisional calculation, but it is not independently verified merely because the UI accepts it.
- **DERIVED:** a result determined by code from inputs (e.g., strike width, net credit, max loss, NAV exposure).
- **HYPOTHETICAL_SCENARIO_NOT_OBSERVED:** a stress or capacity assumption used for sensitivity. It is not a historical frequency, win rate, observed drawdown, or forecast probability.

The dropdown previously named `VERIFIED_EXCHANGE_QUOTE` was misleading because it did not verify an external source. V4.4 labels this mode `USER_ASSERTED_OBSERVED_QUOTE`. Model prices marked `MODEL_ESTIMATE_BS_VIX` remain blocked from being treated as observed quote/capacity evidence.

## 2. The contract engine now checks identities before risk arithmetic

For each vertical:

1. Parse each OCC-style ID into root, expiry, call/put, and strike.
2. Check each leg's option type against the spread type; require both leg expiries to match each other and the entered expiry.
3. Check each ID root against QQQ or the selected VXX deliverable class.
4. Check the short/long Strike fields against the strikes encoded in the two IDs.
5. Derive `width = abs(longStrike - shortStrike)`. A separately entered width is only a cross-check; mismatch returns `BLOCKED_STRIKE_WIDTH_MISMATCH`, and no max-loss capacity is returned.
6. Use only the shared, validated multiplier after confirming both leg multipliers match.

For a credit vertical, the expiry max-loss formula remains `(strike-derived width - net credit per underlying unit) * verified-entered multiplier`. This is still only as reliable as the user-asserted source inputs. It is not a confirmed fill or proof of an exchange quote.

Every leg has its own timezone-aware ISO-8601 quote timestamp and source reference. A manual source marker like `USER_SUPPLIED_UNVERIFIED` explicitly denotes user assertion, not independent verification.

## 3. Adjusted VXX deliverables

An adjusted VXX root is not certified by a selector alone. The `ADJUSTED_USER_ASSERTED_25` scenario requires:

- OCC-style IDs using an adjusted VXX root such as VXX1/VXX2;
- matching short and long multipliers and the selected deliverable class;
- a user-provided source URL and SHA-256 syntax.

The URL and digest fields are not fetched or cryptographically reconciled to an external source by this static HTML. Therefore, the evidence class remains `USER_ASSERTED_NOT_INDEPENDENTLY_VERIFIED`; it must never be presented as independently verified. The regression fixture uses the reserved `.invalid` domain and a synthetic digest on purpose, to test structure only.

## 4. Explicit capacity/stress profiles

All fractions below are inputs to a sensitivity scenario, not estimated probabilities. **BASELINE exactly preserves prior defaults** so the act of introducing the assumption ledger does not itself retune the existing baseline.

| Assumption | BASELINE | CONSERVATIVE | STRESS |
|---|---:|---:|---:|
| Maximum quote age | 4 days | 2 days | 1 day |
| Short quote spread width cap | 25% | 15% | 10% |
| QQQ Far Call max-loss budget / NAV | 1.2% | 0.8% | 0.4% |
| VXX Call spread max-loss budget / NAV | 2.0% | 1.2% | 0.6% |
| VXX Put spread max-loss budget / NAV | 1.0% | 0.5% | 0.25% |
| Portfolio interim stress cap / NAV | 5.0% | 3.5% | 2.5% |
| Deployable margin fraction / NAV | 65% | 50% | 35% |
| VXX stock stress budget / NAV | 6.5% | 4.5% | 2.5% |
| VXX short underlying shock | 35% | 45% | 60% |
| VXX stock margin budget / NAV | 45% | 35% | 25% |
| QQQ core shock | 8% | 10% | 15% |
| QQQ call liability stress | 50% | 65% | 80% |
| VXX put liability stress | 45% | 60% | 75% |
| Interim loss floor vs max loss | 65% | 80% | 90% |

### Interpretation guardrails

- The profile names communicate severity, not statistically calibrated confidence.
- Do not infer that a 15% quote-spread cap or 60% underlying shock has any particular empirical probability without an explicitly sourced calibration study.
- Compare profiles on the same position ledger, quotes, time point, and policy target. Record which constraint binds for each leg.
- The profile may reduce/increase **capacity** only; it must not overwrite the frozen regime target. Golden Test GT-52 checks the target remains invariant across profiles.
- Never tune the profile until it “passes.” Keep BASELINE/CONSERVATIVE/STRESS together, show sensitivity, and retain adverse results.
- Missing fields remain PENDING/BLOCKED; no replacement with zero or a fallback value.

## 5. Required executable regression evidence before HUB

V4.4 adds GT-49 (strike/width consistency), GT-50 (OCC ID/type/expiry/strike consistency), GT-51 (independent leg timestamp/source fields), and GT-52 (scenario-profile monotonic capacity / frozen-target invariance). The test labels shown by the HTML must match the actual number of defined test cases.

The browser's “preflight” label means input-format checks only. A well-formatted hash string or non-empty log path is not proof that a real workflow ran. Actual HUB execution evidence must come from an accepted run ID and self-hosted runner name, plus generated source hashes, output hash, output row count, and uploaded manifest/logs.

## 6. Execution scope

- HUB-Web produces a NASDAQCOM proxy-state shard; it is not VXX historical option-chain replay.
- The workflow must support a standalone `hub_only` scope, avoid running NDX/QQQ/Bridge in that scope, use the explicitly approved self-hosted runner, and default the FRAME acceptance input to HOLD.
- Until the user explicitly accepts the FRAME and the remaining regression review passes, do not execute HUB data, change Frozen Original Hybrid targets, or submit broker orders.
