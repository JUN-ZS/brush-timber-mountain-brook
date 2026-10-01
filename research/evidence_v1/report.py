from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .ledger import EvidenceLedger
from .snapshot import snapshot_sha256


def load_rows(path: Path, ledger: EvidenceLedger | None = None):
    if ledger is not None:
        return ledger.rows()
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def pct(x, n):
    return None if not n else x / n


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize longitudinal strategy evidence without reselection.")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    repo = args.repo_root.resolve()
    path = repo / "research/evidence_v1/evidence.jsonl"
    ledger = EvidenceLedger(path)
    integrity = ledger.validate()
    rows = load_rows(path, ledger)

    by_type = Counter(r["event_type"] for r in rows)
    outcome_rows = [
        r for r in rows
        if r["event_type"] == "OUTCOME_RESOLVED"
        and isinstance(r.get("payload"), dict)
        and r["payload"].get("realized_pnl") is not None
    ]
    latest_outcomes = {}
    outcome_chain_errors = []
    for r in outcome_rows:
        campaign = str(r.get("campaign_id") or r.get("payload", {}).get("campaign_id") or "")
        key = campaign or str(r.get("evidence_id"))
        correction = str(r.get("payload", {}).get("corrects_evidence_id") or "")
        current = latest_outcomes.get(key)
        if correction:
            if current is None or correction != str(current.get("evidence_id")):
                outcome_chain_errors.append({
                    "campaign_id": key,
                    "evidence_id": r.get("evidence_id"),
                    "corrects_evidence_id": correction,
                    "expected_current_outcome": current.get("evidence_id") if current else None,
                })
                continue
        elif current is not None:
            outcome_chain_errors.append({
                "campaign_id": key,
                "evidence_id": r.get("evidence_id"),
                "reason": "OUTCOME_ALREADY_EXISTS_WITHOUT_CORRECTION",
                "expected_current_outcome": current.get("evidence_id"),
            })
            continue
        latest_outcomes[key] = r
    outcomes = list(latest_outcomes.values())
    pnls = [float(r["payload"]["realized_pnl"]) for r in outcomes]
    benchmarks = [
        float(r["payload"]["benchmark_return"])
        for r in outcomes
        if r["payload"].get("benchmark_return") is not None
    ]
    outcomes_by_source = defaultdict(lambda: {"count": 0, "realized_pnl_sum": 0.0, "benchmark_observations": 0})
    for r in outcomes:
        payload = r.get("payload") or {}
        source = str(payload.get("outcome_source") or "UNKNOWN")
        bucket = outcomes_by_source[source]
        bucket["count"] += 1
        bucket["realized_pnl_sum"] += float(payload.get("realized_pnl") or 0.0)
        if payload.get("benchmark_return") is not None:
            bucket["benchmark_observations"] += 1

    campaign_ids = {
        r.get("campaign_id")
        for r in rows
        if r.get("campaign_id")
    }
    cycles = len({r.get("cycle_id") for r in rows if r.get("cycle_id")})
    actions = []
    interventions = by_type["HUMAN_INTERVENTION"]
    for r in rows:
        if r["event_type"] != "DECISION_EMITTED":
            continue
        p = r.get("payload") or {}
        if p.get("primary"):
            actions.append(p["primary"])

    family_counts = Counter()
    family_active_counts = Counter()
    snapshot_failures = []
    for r in rows:
        if r["event_type"] != "PRE_DECISION_OBSERVATION":
            continue
        ref = r.get("payload") or {}
        snap = ref.get("snapshot") or {}
        snapshot_ref = str(snap.get("snapshot_ref") or "")
        expected_sha = str(snap.get("snapshot_sha256") or "")
        if not snapshot_ref or not expected_sha:
            snapshot_failures.append({
                "cycle_id": r.get("cycle_id"),
                "reason": "MISSING_SNAPSHOT_REFERENCE_OR_HASH",
            })
            continue
        spath = repo / snapshot_ref
        if not spath.exists():
            snapshot_failures.append({
                "cycle_id": r.get("cycle_id"),
                "snapshot_ref": snapshot_ref,
                "reason": "SNAPSHOT_MISSING",
            })
            continue
        try:
            obj = json.loads(spath.read_text(encoding="utf-8"))
            actual_sha = snapshot_sha256(obj)
        except Exception as exc:
            snapshot_failures.append({
                "cycle_id": r.get("cycle_id"),
                "snapshot_ref": snapshot_ref,
                "reason": f"SNAPSHOT_INVALID_JSON:{exc}",
            })
            continue
        if actual_sha != expected_sha:
            snapshot_failures.append({
                "cycle_id": r.get("cycle_id"),
                "snapshot_ref": snapshot_ref,
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "reason": "SNAPSHOT_HASH_MISMATCH",
            })
            continue
        for fr in (obj.get("family_observation") or {}).get("rows", []):
            fid = fr.get("family_id")
            if not fid:
                continue
            family_counts[fid] += 1
            if fr.get("status") == "AVAILABLE":
                family_active_counts[fid] += 1

    decision_cycles = {
        r.get("cycle_id")
        for r in rows
        if r.get("event_type") == "PRE_DECISION_OBSERVATION" and r.get("cycle_id")
    }
    report = {
        "schema": "STRATEGY_EVIDENCE_REPORT.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "record_integrity_scope": "DESCRIPTIVE_ONLY_NO_RESELECTION",
        "ledger_integrity": integrity,
        "ledger_head_hash": integrity["head_hash"],
        "snapshot_integrity": {
            "checked_pre_decision_snapshots": sum(1 for r in rows if r.get("event_type") == "PRE_DECISION_OBSERVATION"),
            "failures": snapshot_failures,
            "status": "PASS" if not snapshot_failures else "BLOCKED",
        },
        "outcome_chain_integrity": {
            "status": "PASS" if not outcome_chain_errors else "BLOCKED",
            "errors": outcome_chain_errors,
        },
        "records": len(rows),
        "cycles": cycles,
        "campaign_ids_seen": len(campaign_ids),
        "event_counts": dict(by_type),
        "decision_metrics": {
            "decision_events": by_type["DECISION_EMITTED"],
            "primary_actions": len(actions),
            "primary_action_rate": pct(len(actions), by_type["DECISION_EMITTED"]),
            "human_interventions": interventions,
            "data_gaps": by_type["DATA_GAP"],
        },
        "outcome_metrics": {
            "resolved_outcomes": len(pnls),
            "by_outcome_source": dict(outcomes_by_source),
            "realized_pnl_sum": sum(pnls) if pnls else None,
            "realized_pnl_mean": statistics.mean(pnls) if pnls else None,
            "realized_pnl_median": statistics.median(pnls) if pnls else None,
            "positive_outcome_rate": pct(sum(1 for x in pnls if x > 0), len(pnls)),
            "benchmark_observations": len(benchmarks),
            "mean_benchmark_return": statistics.mean(benchmarks) if benchmarks else None,
        },
        "family_observation": {
            "unique_family_members_observed": len(family_counts),
            "observation_rows": sum(family_counts.values()),
            "families_observed_every_pre_decision_cycle": sum(
                1 for fid, n in family_counts.items() if n == len(decision_cycles)
            ),
            "available_observation_count_by_family": dict(family_active_counts),
        },
        "rule": "This report describes accumulated evidence. It never promotes a family, changes thresholds, or converts observation into probability.",
    }
    out = repo / "research/evidence_v1/sealed/LONGITUDINAL_REPORT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if snapshot_failures or outcome_chain_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
