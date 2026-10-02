# SELF-AUDIT PROTOCOL v1

This protocol defines how the project should be improved without allowing CI, a runner, or a prior result to become the source of strategy ideas.

## 1. Source of truth

For repository code, strategy logic, tests, runtime artifacts, and claims about what has actually run:

`GitHub files + commits + workflow artifacts` are the source of truth.

Bot logs, chat summaries, runner messages, and remembered claims are leads only. A claim becomes verified only after the underlying GitHub object or artifact is inspected.

## 2. Preserve the experiment

The locked alpha is not a target to be made "green".

Every proposed change is classified before editing:

- **ALPHA** — signal, threshold, formula, family membership, policy membership, execution rule that changes the strategy path.
- **INFRASTRUCTURE** — observation, reconciliation, timestamp handling, provenance, safety fence, UI, test, storage, CI, recovery.
- **EVIDENCE** — recording or attribution semantics that must not be confused with a strategy improvement.

Infrastructure/evidence work may evolve without selecting alpha again. Any alpha change invalidates the current evidence chain.

## 3. The AI loop

The intended loop is:

`OBSERVE -> MODEL THE FAILURE -> PATCH IN BATCH -> VERIFY LOCALLY/STRUCTURALLY -> CI CONFIRMS -> REASSESS`

CI is a verifier, not the hypothesis generator.

A failing runner should answer "what invariant is broken?" It should not automatically produce the next patch. Repeated test-trigger/test-fix churn is treated as a process failure.

## 4. One-pass audit before touching CI

Before making a change:

1. Inspect the current GitHub implementation and the relevant history.
2. Identify the invariant that can actually fail.
3. Check adjacent code paths for the same assumption.
4. Patch related cases together.
5. Add the smallest regression test that demonstrates the invariant.
6. Only then use CI as confirmation.

Do not make a one-line patch merely because the runner exposes one one-line failure when the same assumption exists elsewhere.

## 5. Heavyweight replay boundary

The locked 72-config OOS replay is deliberately separated from the normal self-audit loop.

A successful replay is archived in `LOCKED_OOS_ATTESTATION.json` and is valid only while the immutable inputs still match:

- frozen research engine
- strategy lock
- canonical datasets
- locked family definition

Infrastructure-only changes validate the attestation and do not require re-running the full replay.

Any alpha/lock/frozen-engine/canonical-data drift must fail closed and require an explicit fresh replay.

## 6. Evidence discipline

The recorder must distinguish:

`OBSERVED` != `DERIVED` != `ESTIMATED` != `HYPOTHETICAL`

A broker fill is an observed transaction. A code/time match to a strategy candidate is only a potential linkage until explicitly confirmed by the operator. Missing quote history is a data gap, not a reconstructed observation.

Never manufacture a counterfactual path from skipped manual trades. Never turn a post-hoc result into a prospective prediction.

## 7. CI / runner discipline

The normal PR lanes should run on independent hosted infrastructure so one stuck self-hosted runner cannot serialize or distort the audit loop.

The project should prefer:

- narrow trigger surfaces,
- cheap deterministic checks on normal commits,
- heavyweight replay only when its immutable inputs require it,
- explicit/manual replay for archived OOS re-verification.

A runner cancellation, timeout, queue, or scheduling problem is infrastructure telemetry. It is not evidence about strategy quality.

## 8. Stop conditions

The self-audit must stop changing code when:

- the stated invariant is satisfied,
- the regression test exists,
- the current-head relevant CI lanes pass,
- the locked alpha/evidence boundary remains unchanged,
- no new independently observed failure or invariant is present.

"More commits" is not evidence of "more intelligence".

## 9. North star

The system is not being optimized to satisfy the runner.

It is being optimized so that a future observation can answer, without leakage:

**What did the locked strategy emit at that moment?  
What did the human actually do?  
What did the broker actually execute?  
What can still be verified now?  
What remains unknown?**

That chain is the experiment.
