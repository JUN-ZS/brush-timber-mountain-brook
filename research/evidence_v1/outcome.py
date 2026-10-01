from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .identity import runtime_identity
from .ledger import EvidenceLedger


ANCHOR_EVENT_TYPES = {"PRE_DECISION_OBSERVATION", "DECISION_EMITTED", "CYCLE_FINALIZED"}
OUTCOME_SOURCES = {"BROKER_RECONCILED", "USER_REPORTED", "EXTERNAL_RESEARCH" }
BROKER_OUTCOME_ANCHOR_TYPES = {"EXECUTION_OBSERVED"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _anchor_family_ids(prior, anchor, repo: Path):
    """Return family ids demonstrably present in the anchored pre-decision snapshot."""
    candidates=[]
    anchor_type=str(anchor.get("event_type") or "").upper()
    if anchor_type=="PRE_DECISION_OBSERVATION":
        candidates=[anchor]
    else:
        candidates=[
            r for r in prior
            if str(r.get("event_type") or "").upper()=="PRE_DECISION_OBSERVATION"
            and r.get("cycle_id")==anchor.get("cycle_id")
            and r.get("campaign_id")==anchor.get("campaign_id")
        ]
    if not candidates:
        return set()
    ref=(candidates[-1].get("payload") or {}).get("snapshot") or {}
    snapshot_ref=str(ref.get("snapshot_ref") or "")
    expected=str(ref.get("snapshot_sha256") or "")
    if not snapshot_ref or not expected:
        return set()
    path=repo/snapshot_ref
    if not path.exists():
        return set()
    try:
        obj=json.loads(path.read_text(encoding="utf-8"))
        from .snapshot import snapshot_sha256
        if snapshot_sha256(obj)!=expected:
            return set()
        return {
            str(row.get("family_id"))
            for row in (obj.get("family_observation") or {}).get("rows",[])
            if row.get("family_id")
        }
    except Exception:
        return set()


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"INVALID_EVIDENCE_TIMESTAMP:{value}") from exc
    if parsed.tzinfo is None:
        raise SystemExit(f"INVALID_EVIDENCE_TIMESTAMP_MUST_BE_AWARE:{value}")
    return parsed.astimezone(timezone.utc)


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
    ap.add_argument("--outcome-source", choices=sorted(OUTCOME_SOURCES), default="USER_REPORTED")
    ap.add_argument(
        "--source-evidence-id",
        default=None,
        help="Evidence row supporting the declared outcome source; required for BROKER_RECONCILED.",
    )
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
    anchor_type = str(anchor.get("event_type") or "").upper()
    if anchor_type not in ANCHOR_EVENT_TYPES:
        raise SystemExit(
            f"INVALID_OUTCOME_ANCHOR_TYPE:{anchor_type}; anchor must be PRE_DECISION_OBSERVATION, DECISION_EMITTED, or CYCLE_FINALIZED"
        )

    if args.family_id:
        observed_family_ids = _anchor_family_ids(prior, anchor, repo)
        if not observed_family_ids:
            raise SystemExit(
                "FAMILY_ID_REQUIRES_VERIFIABLE_PRE_DECISION_SNAPSHOT"
            )
        if args.family_id not in observed_family_ids:
            raise SystemExit(
                f"FAMILY_ID_NOT_PRESENT_AT_ANCHOR:{args.family_id}"
            )

    source_evidence = None
    if args.source_evidence_id:
        source_evidence = next(
            (r for r in matching if r.get("evidence_id") == args.source_evidence_id),
            None,
        )
        if source_evidence is None:
            raise SystemExit(
                f"INVALID_SOURCE_EVIDENCE_ID:{args.source_evidence_id}; source evidence must belong to campaign {args.campaign_id}"
            )
        source_type = str(source_evidence.get("event_type") or "").upper()
        if args.outcome_source == "BROKER_RECONCILED" and source_type not in BROKER_OUTCOME_ANCHOR_TYPES:
            raise SystemExit(
                f"INVALID_BROKER_SOURCE_EVIDENCE_TYPE:{source_type}; expected EXECUTION_OBSERVED"
            )
    elif args.outcome_source == "BROKER_RECONCILED":
        raise SystemExit("BROKER_RECONCILED_REQUIRES_SOURCE_EVIDENCE_ID")

    outcome_rows = [r for r in matching if r.get("event_type") == "OUTCOME_RESOLVED"]
    current_outcomes = []
    superseded_ids = {
        str(r.get("payload", {}).get("corrects_evidence_id"))
        for r in outcome_rows
        if r.get("payload", {}).get("corrects_evidence_id")
    }
    current_outcomes = [r for r in outcome_rows if str(r.get("evidence_id")) not in superseded_ids]
    if len(current_outcomes) > 1:
        raise SystemExit(
            f"INVALID_OUTCOME_CORRECTION_CHAIN:{args.campaign_id}; multiple active outcomes exist"
        )
    if args.corrects_evidence_id:
        corrected = next(
            (r for r in outcome_rows if r.get("evidence_id") == args.corrects_evidence_id),
            None,
        )
        if corrected is None:
            raise SystemExit(
                f"INVALID_CORRECTION_TARGET:{args.corrects_evidence_id}; target must be an existing OUTCOME_RESOLVED for this campaign"
            )
        if not current_outcomes or corrected.get("evidence_id") != current_outcomes[0].get("evidence_id"):
            raise SystemExit(
                f"INVALID_CORRECTION_TARGET:{args.corrects_evidence_id}; corrections must target the current unsuperseded outcome"
            )
        corrected_payload=corrected.get("payload") or {}
        if args.family_id != corrected_payload.get("family_id"):
            raise SystemExit(
                "CORRECTION_CANNOT_RELABEL_FAMILY"
            )
        if args.anchor_evidence_id != corrected_payload.get("anchor_evidence_id"):
            raise SystemExit(
                "CORRECTION_CANNOT_RELABEL_ANCHOR"
            )
        if args.outcome_source != corrected_payload.get("outcome_source"):
            raise SystemExit(
                "CORRECTION_CANNOT_RELABEL_OUTCOME_SOURCE"
            )
        if args.source_evidence_id != corrected_payload.get("source_evidence_id"):
            raise SystemExit(
                "CORRECTION_CANNOT_RELABEL_SOURCE_EVIDENCE"
            )
    elif outcome_rows:
        raise SystemExit(
            f"OUTCOME_ALREADY_RESOLVED:{args.campaign_id}; use --corrects-evidence-id for an append-only correction"
        )

    anchor_time = _parse_utc(anchor.get("timestamp_utc"))
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
            "source_evidence_id": args.source_evidence_id,
            "source_evidence_event_type": source_evidence.get("event_type") if source_evidence else None,
            "note": args.note,
            "label": "OBSERVED_FORWARD_OUTCOME_NOT_PROBABILITY",
            "non_retroactive": True
        },
        evidence_grade=(
            "BROKER_OBSERVED"
            if args.outcome_source == "BROKER_RECONCILED"
            else "HUMAN_REPORTED"
            if args.outcome_source == "USER_REPORTED"
            else "EXTERNAL_RESEARCH"
        ),
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
