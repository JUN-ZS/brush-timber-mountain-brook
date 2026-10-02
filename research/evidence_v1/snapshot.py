from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


def _canon(value: Any) -> bytes:
    return json.dumps(
        _clean(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def snapshot_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canon(payload)).hexdigest()


def write_snapshot(repo_root: Path, cycle_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    clean = _clean(payload)
    body = json.dumps(
        clean,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"
    digest = snapshot_sha256(clean)
    rel = Path("research") / "evidence_v1" / "snapshots" / f"{cycle_id}.json"
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != body:
            raise RuntimeError(f"SNAPSHOT_ID_COLLISION:{cycle_id}")
    else:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    return {
        "snapshot_ref": rel.as_posix(),
        "snapshot_sha256": digest,
        "bytes": len(body.encode("utf-8")),
    }
