from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .ledger import EvidenceLedger, sha256_json

BENCHMARKS = {"SPY", "QQQ"}
SOURCE_GRADES = {
    "USER_REPORTED": "HUMAN_REPORTED",
    "EXTERNAL_RESEARCH": "EXTERNAL_RESEARCH",
}


def _parse_utc(value: str) -> datetime:
    try:
        out = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"INVALID_EVIDENCE_TIMESTAMP:{value}") from exc
    if out.tzinfo is None:
        raise SystemExit(f"INVALID_EVIDENCE_TIMESTAMP_MUST_BE_AWARE:{value}")
    return out.astimezone(timezone.utc)


def _decision_candidate(prior, anchor_id, candidate_index, candidate_sha):
    anchor = next((r for r in prior if r.get("evidence_id") == anchor_id), None)
    if anchor is None:
        raise SystemExit(f"INVALID_CHECKPOINT_ANCHOR:{anchor_id}")
    if str(anchor.get("event_type") or "").upper() != "DECISION_EMITTED":
        raise SystemExit("CHECKPOINT_ANCHOR_MUST_BE_DECISION_EMITTED")

    payload = anchor.get("payload") or {}
    actions = payload.get("candidate_actions")
    journal = payload.get("candidate_journal")
    if not isinstance(actions, list) or not isinstance(journal, list):
        raise SystemExit("CHECKPOINT_ANCHOR_MISSING_CANDIDATE_JOURNAL")
    try:
        idx = int(candidate_index)
    except (TypeError, ValueError) as exc:
        raise SystemExit("INVALID_CANDIDATE_INDEX") from exc
    if idx < 0 or idx >= len(actions):
        raise SystemExit("INVALID_CANDIDATE_INDEX")
    action_hash = sha256_json(actions[idx])
    if action_hash != str(candidate_sha):
        raise SystemExit("CANDIDATE_SHA256_MISMATCH_AT_ANCHOR")
    row = next(
        (x for x in journal if int(x.get("candidate_index", -1)) == idx),
        None,
    )
    if row is None or str(row.get("candidate_sha256") or "") != action_hash:
        raise SystemExit("CANDIDATE_NOT_PRESENT_IN_ANCHOR_JOURNAL")
    if not isinstance(row.get("raw_candidate"), dict):
        raise SystemExit("CANDIDATE_RAW_MISSING_AT_ANCHOR")
    if sha256_json(row["raw_candidate"]) != action_hash:
        raise SystemExit("CANDIDATE_JOURNAL_DIGEST_MISMATCH")
    return anchor, row


def main() -> int:
    ap = argparse.ArgumentParser(description="Append one multi-horizon forward candidate checkpoint.")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--campaign-id", required=True)
    ap.add_argument("--anchor-evidence-id", required=True)
    ap.add_argument("--candidate-index", type=int, required=True)
    ap.add_argument("--candidate-sha256", required=True)
    ap.add_argument("--benchmark", choices=sorted(BENCHMARKS), required=True)
    ap.add_argument("--horizon-trading-days", type=int, required=True)
    ap.add_argument("--benchmark-return", type=float, required=True)
    ap.add_argument("--candidate-return", type=float, default=None)
    ap.add_argument("--observation-source", choices=sorted(SOURCE_GRADES), default="USER_REPORTED")
    ap.add_argument("--observation-note", default="")
    args = ap.parse_args()

    if args.horizon_trading_days <= 0:
        raise SystemExit("HORIZON_TRADING_DAYS_MUST_BE_POSITIVE")

    repo = args.repo_root.resolve()
    ledger = EvidenceLedger(repo / "research/evidence_v1/evidence.jsonl")
    prior = ledger.rows()
    matching = [r for r in prior if r.get("campaign_id") == args.campaign_id]
    if not matching:
        raise SystemExit(f"UNKNOWN_CAMPAIGN_ID:{args.campaign_id}")

    anchor, journal_row = _decision_candidate(
        matching,
        args.anchor_evidence_id,
        args.candidate_index,
        args.candidate_sha256,
    )

    anchor_time = _parse_utc(anchor.get("timestamp_utc"))
    now = datetime.now(timezone.utc)
    if now < anchor_time:
        raise SystemExit("CHECKPOINT_BEFORE_ANCHOR")

    same_scope = [
        r for r in matching
        if str(r.get("event_type") or "").upper() == "FORWARD_CHECKPOINT_OBSERVED"
        and (r.get("payload") or {}).get("anchor_evidence_id") == args.anchor_evidence_id
        and (r.get("payload") or {}).get("candidate_sha256") == args.candidate_sha256
        and (r.get("payload") or {}).get("benchmark") == args.benchmark
        and int((r.get("payload") or {}).get("horizon_trading_days", -1)) == args.horizon_trading_days
    ]
    if same_scope:
        raise SystemExit("FORWARD_CHECKPOINT_ALREADY_RECORDED")

    row = ledger.append(
        "FORWARD_CHECKPOINT_OBSERVED",
        cycle_id=f"CHECKPOINT_{now.strftime('%Y%m%dT%H%M%SZ')}",
        campaign_id=args.campaign_id,
        timestamp_utc=now.isoformat(),
        payload={
            "campaign_id": args.campaign_id,
            "anchor_evidence_id": args.anchor_evidence_id,
            "candidate_index": args.candidate_index,
            "candidate_sha256": args.candidate_sha256,
            "candidate_code": journal_row.get("candidate_code"),
            "candidate_action": (journal_row.get("raw_candidate") or {}).get("action"),
            "candidate_observed_at_utc": journal_row.get("observed_at_utc"),
            "benchmark": args.benchmark,
            "horizon_trading_days": args.horizon_trading_days,
            "benchmark_return": args.benchmark_return,
            "candidate_return": args.candidate_return,
            "observation_source": args.observation_source,
            "observation_note": args.observation_note,
            "label": "OBSERVED_FORWARD_CHECKPOINT_NOT_PROBABILITY",
            "non_retroactive": True,
        },
        evidence_grade=SOURCE_GRADES[args.observation_source],
    )
    print(json.dumps({
        "status": "APPENDED",
        "evidence_id": row["evidence_id"],
        "candidate_sha256": args.candidate_sha256,
        "benchmark": args.benchmark,
        "horizon_trading_days": args.horizon_trading_days,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
