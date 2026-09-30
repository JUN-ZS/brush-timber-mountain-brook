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
    cycle_id = f"OUTCOME_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    row = ledger.append(
        "OUTCOME_RESOLVED",
        cycle_id=cycle_id,
        campaign_id=args.campaign_id,
        timestamp_utc=now_utc(),
        payload={
            "campaign_id": args.campaign_id,
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
