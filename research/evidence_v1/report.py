from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def load_rows(path: Path):
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
    rows = load_rows(path)

    by_type = Counter(r["event_type"] for r in rows)
    outcomes = [
        r for r in rows
        if r["event_type"] == "OUTCOME_RESOLVED"
        and isinstance(r.get("payload"), dict)
        and r["payload"].get("realized_pnl") is not None
    ]
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

    report = {
        "schema": "STRATEGY_EVIDENCE_REPORT.v1",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "record_integrity_scope": "DESCRIPTIVE_ONLY_NO_RESELECTION",
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
            "families_observed_every_cycle": sum(
                1 for fid, n in family_counts.items() if n == len({r.get("cycle_id") for r in rows if r.get("cycle_id")})
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
