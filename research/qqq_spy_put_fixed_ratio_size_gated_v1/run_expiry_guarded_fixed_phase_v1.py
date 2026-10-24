#!/usr/bin/env python3
"""Run source-pinned QQQ/SPY PUT replays with 10/20-session exits protected by DTE<=7."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ENGINE_PATH = ROOT / "qqq_spy_put_fixed_phase_v1.py"
POLICY_DEFINITIONS = (
    {"policy": "HOLD_10_OR_DTE_LE_7", "hold_sessions": 10, "dte_guard_days": 7},
    {"policy": "HOLD_20_OR_DTE_LE_7", "hold_sessions": 20, "dte_guard_days": 7},
)
TRIGGER_SOURCE = 'trigger=ep["age_sessions"]>=policy["hold_sessions"] if policy["hold_sessions"] is not None else dte<=7'
REASON_SOURCE = "ep[\"exit_reason\"]=f\"HOLD_{policy['hold_sessions']}_SESSIONS\" if policy[\"hold_sessions\"] is not None else \"DTE_LE_7\""
TRIGGER_PATCH = 'trigger = expiry_guard_exit_trigger(ep["age_sessions"], dte, policy["hold_sessions"], policy.get("dte_guard_days", 7)) if policy["hold_sessions"] is not None else dte <= 7'
REASON_PATCH = 'ep["exit_reason"] = expiry_guard_exit_reason(ep["age_sessions"], dte, policy["hold_sessions"], policy.get("dte_guard_days", 7))'


def expiry_guard_exit_trigger(age_sessions: int, dte: int, hold_sessions: int, guard_days: int = 7) -> bool:
    """Trigger when either the planned hold is reached or remaining calendar DTE is at/below guard."""
    if hold_sessions < 1 or guard_days < 0:
        raise ValueError("hold_sessions must be positive and guard_days non-negative")
    return age_sessions >= hold_sessions or dte <= guard_days


def expiry_guard_exit_reason(age_sessions: int, dte: int, hold_sessions: int, guard_days: int = 7) -> str:
    if age_sessions >= hold_sessions:
        return f"HOLD_{hold_sessions}_SESSIONS"
    return f"DTE_LE_{guard_days}"


def load_engine_namespace() -> tuple[dict[str, Any], dict[str, str]]:
    """Load the existing engine with an exact, fail-closed exit-trigger patch."""
    source = ENGINE_PATH.read_text(encoding="utf-8")
    if source.count(TRIGGER_SOURCE) != 1:
        raise RuntimeError("replay engine trigger anchor changed; refusing a fuzzy patch")
    if source.count(REASON_SOURCE) != 1:
        raise RuntimeError("replay engine exit-reason anchor changed; refusing a fuzzy patch")
    patched = source.replace(TRIGGER_SOURCE, TRIGGER_PATCH, 1).replace(REASON_SOURCE, REASON_PATCH, 1)
    namespace: dict[str, Any] = {
        "__name__": "_expiry_guarded_fixed_phase_engine",
        "__file__": str(ENGINE_PATH),
        "expiry_guard_exit_trigger": expiry_guard_exit_trigger,
        "expiry_guard_exit_reason": expiry_guard_exit_reason,
    }
    exec(compile(patched, str(ENGINE_PATH), "exec"), namespace)
    namespace["POLICIES"] = [dict(item) for item in POLICY_DEFINITIONS]
    hashes = {
        "base_engine_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "patched_engine_sha256": hashlib.sha256(patched.encode("utf-8")).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return namespace, hashes


def main() -> int:
    engine, hashes = load_engine_namespace()
    args = engine["parse_args"]()
    report = engine["run_replay"](args)
    variant = {
        "name": "EXPIRY_GUARDED_HOLD",
        "policy_definitions": [dict(item) for item in POLICY_DEFINITIONS],
        "trigger": "close when age_sessions >= hold_sessions OR remaining calendar DTE <= 7",
        "exit_execution": "trigger on observed EOD row; close only on a later row with exact contract IDs and sufficient quote-side size; otherwise defer and preserve unresolved status",
        "implementation": hashes,
        "git_sha": __import__("os").environ.get("GITHUB_SHA"),
    }
    report["execution_variant"] = variant
    out = Path(args.out)
    (out / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    manifest_path = out / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["execution_variant"] = variant
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    with (out / "summary.md").open("a", encoding="utf-8") as handle:
        handle.write("\n\n## Expiry-guarded exit contract\n\n")
        handle.write("- Exit signal: planned 10/20 common-session holding limit OR remaining calendar DTE <= 7, whichever occurs first.\n")
        handle.write("- A trigger is not a guaranteed fill. The replay still requires exact selected contracts, valid quotes and sufficient displayed exit-side size; failed closes defer and can remain unresolved at expiry/source end.\n")
        handle.write(f"- Base engine SHA-256: {hashes['base_engine_sha256']}; patched engine SHA-256: {hashes['patched_engine_sha256']}; runner SHA-256: {hashes['runner_sha256']}.\n")
    print(json.dumps({
        "status": report["status"],
        "window": report["window"],
        "selection": report["selection"],
        "entry_filter": report["entry_filter"]["name"],
        "ratio": report["ratio"],
        "cohort": {k: report["cohort"][k] for k in ("selected_signals", "entered_cohorts", "entry_skipped")},
        "fixed_entry_schedule": report["fixed_entry_schedule"],
        "policies": report["policies"],
        "execution_variant": variant,
        "output_dir": str(args.out),
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
