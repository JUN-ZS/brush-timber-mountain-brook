from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .ledger import EvidenceLedger


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
    superseded = {
        str(r.get("payload", {}).get("corrects_evidence_id"))
        for r in outcome_rows
        if r.get("payload", {}).get("corrects_evidence_id")
    }
    latest_outcomes = {}
    for r in outcome_rows:
        if r.get("evidence_id") in superseded:
            continue
        campaign = str(r.get("campaign_id") or r.get("payload", {}).get("campaign_id") or "")
        latest_outcomes[campaign or str(r.get("evidence_id"))] = r
    outcomes = list(latest_outcomes.values())
    pnls = [float(r["payload"]["realized_pnl"]) for r in outcomes]
    benchmarks = [
        float(r["payload"]["benchmark_return"])
        for r in outcomes
        if r["payload"].get("benchmark_return") is not None
    ]

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
    for r in rows:
        if r["event_type"] != "PRE_DECISION_OBSERVATION":
            continue
        ref = r.get("payload") or {}
        snap = ref.get("snapshot") or {}
        # Family vector lives in the immutable snapshot, not in a result-picked report.
        spath = repo / str(snap.get("snapshot_ref", ""))
        if not spath.exists():
            continue
        try:
            obj = json.loads(spath.read_text(encoding="utf-8"))
        except Exception:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
