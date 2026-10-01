from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_FAR_DTE = {90, 120, 180}
ALLOWED_FAR_DELTA = {0.05, 0.08, 0.10}
LOCKED_NEAR_DTE = 30
LOCKED_STRATEGY_ID = "QQQ_DYNAMIC_NEAR_LONG_V22_CANDIDATE_FAMILY"
LOCKED_STRATEGY_VERSION = "V22-family-30D-1.5x"
LOCKED_RESEARCH_ENGINE_COMMIT = "930c949ec5260865f2bf3ee1c6e030dab7b8e4c4"
LOCKED_POLICIES = {
    "TP50_IMMEDIATE","TP75_IMMEDIATE","TP100_IMMEDIATE","TRAIL20_IMMEDIATE",
    "TP50_ON_RISK","TP75_ON_RISK","TRAIL20_ON_RISK","TP75_COOLDOWN3",
}


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
        "SIGNAL_RATIO52_GTE": float(lock["signal"]["ratio52_gte"]),
        "SIGNAL_EXT200_GTE": float(lock["signal"]["ext200_gte"]),
    }
    manifest_expectations = {
        "strategy_version": "V22-family-30D-1.5x",
        "selection_cutoff": "2025-12-15",
        "selection_status": "LOCKED_FROM_PRIOR_FULL_SAMPLE_V22_AUDIT",
        "research_engine_commit": "930c949ec5260865f2bf3ee1c6e030dab7b8e4c4",
    }
    manifest_mismatches = {
        k: {"expected": v, "actual": lock.get(k)}
        for k, v in manifest_expectations.items()
        if lock.get(k) != v
    }
    if manifest_mismatches:
        raise StrategyLockViolation(
            "LOCK_VIOLATION:MANIFEST:" + json.dumps(manifest_mismatches, sort_keys=True)
        )
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

    if lock.get("strategy_id") != LOCKED_STRATEGY_ID:
        raise StrategyLockViolation("LOCK_VIOLATION:STRATEGY_ID")
    if lock.get("strategy_version") != LOCKED_STRATEGY_VERSION:
        raise StrategyLockViolation("LOCK_VIOLATION:STRATEGY_VERSION")
    if lock.get("research_engine_commit") != LOCKED_RESEARCH_ENGINE_COMMIT:
        raise StrategyLockViolation("LOCK_VIOLATION:RESEARCH_ENGINE_COMMIT")

    fam = lock["candidate_family"]
    if fam["near_dte"] != LOCKED_NEAR_DTE or float(fam["coverage"]) != 1.50:
        raise StrategyLockViolation("LOCK_VIOLATION:LOCK_MANIFEST_FAMILY")
    if set(int(x) for x in fam["far_dte"]) != set(ALLOWED_FAR_DTE):
        raise StrategyLockViolation("LOCK_VIOLATION:FAR_DTE_FAMILY")
    if set(float(x) for x in fam["far_abs_delta"]) != set(ALLOWED_FAR_DELTA):
        raise StrategyLockViolation("LOCK_VIOLATION:FAR_DELTA_FAMILY")
    if float(fam.get("long_delta")) != 0.50:
        raise StrategyLockViolation("LOCK_VIOLATION:LONG_DELTA_FAMILY")
    if set(fam.get("policies") or []) != LOCKED_POLICIES:
        raise StrategyLockViolation("LOCK_VIOLATION:POLICY_FAMILY")
    if int(fam["config_count"]) != 72:
        raise StrategyLockViolation("LOCK_VIOLATION:CONFIG_COUNT")
    expected_policies = {
        "TP50_IMMEDIATE","TP75_IMMEDIATE","TP100_IMMEDIATE","TRAIL20_IMMEDIATE",
        "TP50_ON_RISK","TP75_ON_RISK","TRAIL20_ON_RISK","TP75_COOLDOWN3",
    }
    if set(fam["policies"]) != expected_policies:
        raise StrategyLockViolation("LOCK_VIOLATION:POLICY_FAMILY")
    if float(lock["signal"]["ratio52_gte"]) != 0.98 or float(lock["signal"]["ext200_gte"]) != 0.08:
        raise StrategyLockViolation("LOCK_VIOLATION:SIGNAL_MANIFEST")
    expected["SIGNAL_RATIO52_GTE"] = float(lock["signal"]["ratio52_gte"])
    expected["SIGNAL_EXT200_GTE"] = float(lock["signal"]["ext200_gte"])
    return {"status": "PASS", "checked": expected, "strategy_id": lock["strategy_id"]}


def assert_runtime_lock(repo_root: Path, *, far_dte: int, far_delta: float, near_dte: int) -> dict[str, Any]:
    lock = load_lock(repo_root)
    assert_cli_member(far_dte=far_dte, far_delta=far_delta, near_dte=near_dte)
    engine_status = assert_engine_constants(repo_root)
    if lock.get("selection_cutoff") != "2025-12-15":
        raise StrategyLockViolation("LOCK_VIOLATION:SELECTION_CUTOFF")
    if lock.get("selection_status") != "LOCKED_FROM_PRIOR_FULL_SAMPLE_V22_AUDIT":
        raise StrategyLockViolation("LOCK_VIOLATION:SELECTION_STATUS")
    if lock.get("virgin_oos_status") != "NOT_VIRGIN_YET":
        raise StrategyLockViolation("LOCK_VIOLATION:VIRGIN_OOS_STATUS")
    return {
        "status": "PASS",
        "strategy_id": lock["strategy_id"],
        "strategy_version": lock["strategy_version"],
        "selection_cutoff": lock["selection_cutoff"],
        "virgin_oos_status": lock["virgin_oos_status"],
        "engine": engine_status,
    }
