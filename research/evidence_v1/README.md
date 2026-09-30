# Prospective Strategy Evidence Record v1

## Purpose

This is deliberately different from a one-time OOS report.

A virgin OOS asks whether a locked family worked on a period that was not used for selection.

The prospective evidence record asks what the frozen strategy knew, what it emitted, what was actually executed, what changed in the environment, what went wrong, and what happened afterwards — over the life of the system.

## Evidence grades

PROSPECTIVE_OBSERVED = market/account state captured before the current decision.

BROKER_OBSERVED = broker order/deal/fill evidence observed from Futu OpenD.

PROSPECTIVE_OUTCOME = later outcome resolved from a prior frozen observation.

DATA_GAP = missing/stale/unavailable evidence. The gap itself is retained.

HUMAN_REPORTED = explicit manual correction or intervention, never silently merged into system evidence.

## What is recorded

Each live cycle can contain:

1. Runtime identity: strategy lock hash, research engine reference, current Git HEAD, and code hashes.
2. An exact market/option snapshot saved separately and addressed by SHA-256.
3. The complete locked 72-member family observation vector at that timestamp.
4. Strategy state before decision: signal, campaign state, candidates, risk inputs, and quote freshness.
5. The engine output: every candidate action and the emitted primary ticket.
6. Broker reconciliation: fills, partial fills, superseded tickets, and manual/broker intervention.
7. Later outcome: realized P&L, benchmark return, MAE/MFE and drawdown, appended as a new record.
8. A hash-chain linking every record to the previous record.

## Why it can become more informative than a virgin OOS report

A single virgin OOS is one fixed holdout. A longitudinal prospective record can accumulate non-overlapping forward regimes, real execution quality, liquidity failures, intervention frequency, state persistence, regime shifts, and same-timestamp counterfactual observations for every locked family member.

It can therefore become a much richer evidence base for robustness and operational reality.

It is still not a mathematical proof of future profitability.

## Non-negotiable rule

Infrastructure may improve.

The current alpha family may not silently mutate.

Any alpha mutation gets a new strategy_id and a new evidence lineage. Existing records stay attached to the old lineage.

## Runtime files

Raw live evidence is local-only because it may contain brokerage execution metadata:

- research/evidence_v1/evidence.jsonl
- research/evidence_v1/snapshots/*.json

Digest-only checkpoints are written under:

- research/evidence_v1/sealed/

Verify:

    python -m research.evidence_v1.seal

Create a checkpoint:

    python -m research.evidence_v1.seal --seal --note "weekly evidence checkpoint"

Resolve a mature campaign:

    python -m research.evidence_v1.outcome --campaign-id CAMPAIGN_ID --realized-pnl 1234.50 --benchmark-return 0.021

The outcome command appends; it never edits the original observation.
