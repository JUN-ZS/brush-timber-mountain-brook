from __future__ import annotations

import argparse
import json
from pathlib import Path

from .identity import runtime_identity
from .ledger import EvidenceLedger


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify and optionally seal the evidence ledger.")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--seal", action="store_true")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    ledger = EvidenceLedger(
        repo / "research/evidence_v1/evidence.jsonl",
        identity=runtime_identity(repo),
    )
    result = ledger.validate()
    if args.seal:
        seal_path = (
            repo / "research/evidence_v1/sealed"
            / f"SEAL_{result['records']:08d}_{result['head_hash'][:16]}.json"
        )
        result["seal"] = ledger.seal(seal_path, note=args.note)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
