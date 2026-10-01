from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable


CODE_PATHS = (
    "research/live_hedge_v1/engine.py",
    "research/live_hedge_v1/campaign.py",
    "research/live_hedge_v1/futu_reader.py",
    "research/live_hedge_v1/futu_trade_reader.py",
    "research/live_hedge_v1/state.py",
    "research/live_hedge_v1/run_live_desk.py",
    "research/evidence_v1/ledger.py",
    "research/evidence_v1/identity.py",
    "research/evidence_v1/lock_guard.py",
    "research/strategy_instance_v1/run_instance.py",
    "research/strategy_instance_v1/ledger.py",
    "research/strategy_instance_v1/performance_tape.py",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(repo_root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        return out.strip() or None
    except Exception:
        return None


def strategy_lock(repo_root: Path) -> tuple[dict, str]:
    path = repo_root / "research" / "evidence_v1" / "STRATEGY_LOCK.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return obj, hashlib.sha256(raw).hexdigest()


def runtime_identity(repo_root: Path) -> dict:
    lock, lock_hash = strategy_lock(repo_root)
    code_hashes: dict[str, str] = {}
    for rel in CODE_PATHS:
        path = repo_root / rel
        if path.exists():
            code_hashes[rel] = sha256_file(path)
        else:
            code_hashes[rel] = "MISSING"

    return {
        "strategy_id": lock["strategy_id"],
        "strategy_version": lock["strategy_version"],
        "selection_cutoff": lock["selection_cutoff"],
        "research_engine_commit": lock["research_engine_commit"],
        "strategy_lock_hash": lock_hash,
        "git_head": git_head(repo_root),
        "code_hashes": code_hashes,
        "evidence_policy": lock["evidence_policy"],
    }
