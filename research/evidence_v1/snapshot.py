from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canon(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def write_snapshot(repo_root: Path, cycle_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"
    digest = hashlib.sha256(_canon(payload)).hexdigest()
    rel = Path("research") / "evidence_v1" / "snapshots" / f"{cycle_id}.json"
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != body:
            raise RuntimeError(f"SNAPSHOT_ID_COLLISION:{cycle_id}")
    else:
        path.write_text(body, encoding="utf-8")
    return {
        "snapshot_ref": rel.as_posix(),
        "snapshot_sha256": digest,
        "bytes": len(body.encode("utf-8")),
    }
