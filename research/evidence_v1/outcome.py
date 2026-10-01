from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .identity import runtime_identity
from .ledger import EvidenceLedger


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description="Append one immutable campaign outcome.")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--campaign-id", required=True)
    ap.add_argument("--family-id", default=None)
    ap.add_argument(
        "--anchor-evidence-id",
        required=True,
        help="Existing evidence row that this posthoc outcome resolves from.",
    )
    ap.add_argument(
        "--corrects-evidence-id",
        default=None,
        help="Existing OUTCOME_RESOLVED evidence id being corrected; correction is append-only.",
    )
    ap.add_argument("--realized-pnl", type=float, required=True)
    ap.add_argument("--benchmark-return", type=float, default=None)
    ap.add_argument("--start-nav", type=float, default=None)
    ap.add_argument("--end-nav", type=float, default=None)
    ap.add_argument("--max-drawdown", type=float, default=None)
    ap.add_argument("--mfe", type=float, default=None)
    ap.add_argument("--mae", type=float, default=None)
    ap.add_argument("--outcome-source", default="BROKER_RECONCILED")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    ledger = EvidenceLedger(
        repo / "research/evidence_v1/evidence.jsonl",
        identity=runtime_identity(repo),
    )
    prior = ledger.rows()
    matching = [r for r in prior if r.get("campaign_id") == args.campaign_id]
    if not matching:
        raise SystemExit(
            f"UNKNOWN_CAMPAIGN_ID:{args.campaign_id}; outcome cannot be backfilled without prior evidence"
        )

    anchor = next((r for r in prior if r.get("evidence_id") == args.anchor_evidence_id), None)
    if anchor is None or anchor.get("campaign_id") != args.campaign_id:
        raise SystemExit(
            f"INVALID_OUTCOME_ANCHOR:{args.anchor_evidence_id}; anchor must belong to campaign {args.campaign_id}"
        )

    outcome_rows = [r for r in matching if r.get("event_type") == "OUTCOME_RESOLVED"]
    if args.corrects_evidence_id:
        corrected = next(
            (r for r in outcome_rows if r.get("evidence_id") == args.corrects_evidence_id),
            None,
        )
        if corrected is None:
            raise SystemExit(
                f"INVALID_CORRECTION_TARGET:{args.corrects_evidence_id}; target must be an existing OUTCOME_RESOLVED for this campaign"
            )
    elif outcome_rows:
        raise SystemExit(
            f"OUTCOME_ALREADY_RESOLVED:{args.campaign_id}; use --corrects-evidence-id for an append-only correction"
        )

    anchor_time = datetime.fromisoformat(str(anchor.get("timestamp_utc")).replace("Z", "+00:00"))
    outcome_time = datetime.now(timezone.utc)
    if outcome_time < anchor_time:
        raise SystemExit("OUTCOME_BEFORE_ANCHOR")
    cycle_id = f"OUTCOME_{outcome_time.strftime('%Y%m%dT%H%M%SZ')}"
    row = ledger.append(
        "OUTCOME_RESOLVED",
        cycle_id=cycle_id,
        campaign_id=args.campaign_id,
        timestamp_utc=now_utc(),
        payload={
            "campaign_id": args.campaign_id,
            "family_id": args.family_id,
            "anchor_evidence_id": args.anchor_evidence_id,
            "corrects_evidence_id": args.corrects_evidence_id,
            "realized_pnl": args.realized_pnl,
            "benchmark_return": args.benchmark_return,
            "start_nav": args.start_nav,
            "end_nav": args.end_nav,
            "max_drawdown": args.max_drawdown,
            "mfe": args.mfe,
            "mae": args.mae,
            "outcome_source": args.outcome_source,
            "note": args.note,
            "label": "OBSERVED_FORWARD_OUTCOME_NOT_PROBABILITY",
            "non_retroactive": True
        },
        evidence_grade="BROKER_OBSERVED" if "BROKER" in args.outcome_source else "PROSPECTIVE_OUTCOME",
    )
    print(json.dumps({
        "status": "APPENDED",
        "evidence_id": row["evidence_id"],
        "record_hash": row["record_hash"],
        "campaign_id": args.campaign_id
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
