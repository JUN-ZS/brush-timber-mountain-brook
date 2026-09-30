from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_FAR_DTE = {90, 120, 180}
ALLOWED_FAR_DELTA = {0.05, 0.08, 0.10}
LOCKED_NEAR_DTE = 30


class StrategyLockViolation(RuntimeError):
    pass


def load_lock(repo_root: Path) -> dict[str, Any]:
    return json.loads(
        (repo_root / "research/evidence_v1/STRATEGY_LOCK.json").read_text(encoding="utf-8")
    )


def assert_cli_member(*, far_dte: int, far_delta: float, near_dte: int) -> None:
    if far_dte not in ALLOWED_FAR_DTE:
        raise StrategyLockViolation(f"LOCK_VIOLATION:FAR_DTE={far_dte}")
    if min(abs(far_delta - x) for x in ALLOWED_FAR_DELTA) > 1e-9:
        raise StrategyLockViolation(f"LOCK_VIOLATION:FAR_DELTA={far_delta}")
    if near_dte != LOCKED_NEAR_DTE:
        raise StrategyLockViolation(f"LOCK_VIOLATION:NEAR_DTE={near_dte}")


def assert_engine_constants(repo_root: Path) -> dict[str, Any]:
    lock = load_lock(repo_root)
    from ..live_hedge_v1 import engine

    expected = {
        "N_SHORT": 10,
        "LONG_DELTA": 0.50,
        "MAX_STACK": 5,
        "COVERAGE_MULT": 1.50,
        "NEAR_TP": 0.50,
        "NEAR_ROLL_DTE": 2,
    }
    actual = {k: getattr(engine, k, None) for k in expected}
    mismatches = {
        k: {"expected": v, "actual": actual.get(k)}
        for k, v in expected.items()
        if actual.get(k) != v
    }
    if mismatches:
        raise StrategyLockViolation(
            "LOCK_VIOLATION:ENGINE_CONSTANTS:" + json.dumps(mismatches, sort_keys=True)
        )

    fam = lock["candidate_family"]
    if fam["near_dte"] != LOCKED_NEAR_DTE or float(fam["coverage"]) != 1.50:
        raise StrategyLockViolation("LOCK_VIOLATION:LOCK_MANIFEST_FAMILY")
    return {"status": "PASS", "checked": expected, "strategy_id": lock["strategy_id"]}


def assert_runtime_lock(repo_root: Path, *, far_dte: int, far_delta: float, near_dte: int) -> dict[str, Any]:
    lock = load_lock(repo_root)
    assert_cli_member(far_dte=far_dte, far_delta=far_delta, near_dte=near_dte)
    engine_status = assert_engine_constants(repo_root)
    if lock.get("selection_cutoff") != "2025-12-15":
        raise StrategyLockViolation("LOCK_VIOLATION:SELECTION_CUTOFF")
    if lock.get("virgin_oos_status") == "VIRGIN_PROVEN":
        raise StrategyLockViolation("LOCK_VIOLATION:INVALID_OOS_STATE")
    return {
        "status": "PASS",
        "strategy_id": lock["strategy_id"],
        "strategy_version": lock["strategy_version"],
        "selection_cutoff": lock["selection_cutoff"],
        "virgin_oos_status": lock["virgin_oos_status"],
        "engine": engine_status,
    }
