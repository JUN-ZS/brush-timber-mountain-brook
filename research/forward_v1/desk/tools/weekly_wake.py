#!/usr/bin/env python3
"""Desk WEEKLY WAKE → SELF-DUE → RUN ONLY IF DUE.

Entry: python research/forward_v1/desk/tools/weekly_wake.py --now

ALWAYS evaluate self-due first.
IF WAIT: write SELF_DUE_STATUS, knowledge_delta=NONE, STOP (no reprocess).
IF DUE: only run the due lane(s) via existing forward_runner / resolver paths —
never mint fake T1.

CADENCE ≠ WAKE FREQUENCY. Weekly wake ≠ daily run.
Grok Bot weekly routine should call this CLI; no GitHub Actions cron required.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

HKT = timezone(timedelta(hours=8))

# Horizon buckets → resolver --horizons filter
LAYER_HORIZONS = {
    "SHORT": [5],
    "MEDIUM": [21, 63],
    "LONG": [126, 252],
}
LANE_HORIZON = {
    "maturity_5d": 5,
    "maturity_21d": 21,
    "maturity_63d": 63,
    "maturity_126d": 126,
    "maturity_252d": 252,
}


def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[4]


def _desk(repo: Path) -> Path:
    return repo / "research/forward_v1/desk"


def _now_pair() -> tuple[str, str]:
    utc = datetime.now(timezone.utc).replace(microsecond=0)
    hkt = utc.astimezone(HKT)
    return (
        utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        hkt.strftime("%Y-%m-%d %H:%M:%S HKT"),
    )


def _run_py(repo: Path, rel: str, extra: list[str] | None = None, timeout: int = 900) -> tuple[int, str]:
    cmd = [sys.executable, str(repo / rel), "--repo-root", str(repo)]
    if extra:
        cmd.extend(extra)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, f"TIMEOUT: {exc}"
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return proc.returncode, out


def _horizons_for_due_lanes(due_lanes: list[str]) -> list[int]:
    hz: list[int] = []
    for lane in due_lanes:
        if lane in LANE_HORIZON:
            n = LANE_HORIZON[lane]
            if n not in hz:
                hz.append(n)
    return sorted(hz)


def run_due_lanes(repo: Path, status: dict[str, Any]) -> dict[str, Any]:
    """Invoke existing tools for due lanes only. Never invent T1."""
    due = list(status.get("due_lanes") or [])
    results: dict[str, Any] = {"ran": [], "rcs": {}, "notes": []}

    if "signal_capture" in due:
        # Existing capture path — gate refuses invent / identical reprocess
        rc, out = _run_py(
            repo,
            "research/forward_v1/desk/tools/t1_capture.py",
            timeout=600,
        )
        results["rcs"]["t1_capture"] = rc
        results["ran"].append("t1_capture")
        results["notes"].append(
            "signal_capture lane → t1_capture.py (AS_EMITTED only; never invent T1)"
        )
        if rc != 0:
            results["notes"].append(f"t1_capture rc={rc}: {out[-500:]}")

    horizons = _horizons_for_due_lanes(due)
    if horizons:
        hz_arg = ",".join(str(h) for h in horizons)
        rc, out = _run_py(
            repo,
            "research/forward_v1/desk/tools/live_forward_resolver.py",
            extra=["--horizons", hz_arg],
            timeout=600,
        )
        results["rcs"]["live_forward_resolver"] = rc
        results["ran"].append(f"live_forward_resolver[{hz_arg}]")
        results["notes"].append(
            f"maturity lanes → live_forward_resolver --horizons {hz_arg}"
        )
        if rc != 0:
            results["notes"].append(f"resolver rc={rc}: {out[-500:]}")

    if not results["ran"]:
        results["notes"].append("due_lanes set but no runnable mapping — STOP")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Desk WEEKLY WAKE → SELF-DUE → RUN ONLY IF DUE"
    )
    ap.add_argument(
        "--now",
        action="store_true",
        help="evaluate self-due now; run due lanes only (default behavior too)",
    )
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="evaluate + write status; never invoke capture/resolver",
    )
    args = ap.parse_args()
    _ = args.now  # explicit --now accepted; absence still runs evaluate

    repo = (args.repo_root or _repo_root_from_here()).resolve()
    desk = _desk(repo)

    # Import sibling self_due without package install
    sys.path.insert(0, str(desk / "tools"))
    import self_due  # type: ignore  # noqa: E402

    utc_s, hkt_s = _now_pair()
    status = self_due.evaluate(repo)
    status_path = self_due.write_status(status, repo)

    wake_report: dict[str, Any] = {
        "schema": "WEEKLY_WAKE_REPORT.v1",
        "node": "desk",
        "pass": "WEEKLY_WAKE_SELF_DUE_V1",
        "wake_kind": "WEEKLY_WAKE",
        "written_at_utc": utc_s,
        "written_at_hkt": hkt_s,
        "self_due_path": str(status_path.relative_to(repo)),
        "due_now": status["due_now"],
        "action": status["action"],
        "due_lanes": status["due_lanes"],
        "wait_lanes": status["wait_lanes"],
        "knowledge_delta": status["knowledge_delta"],
        "reason": status["reason"],
        "anti_loop": status.get("anti_loop"),
        "CADENCE_NE_WAKE_FREQUENCY": True,
        "ran": False,
        "run_results": None,
        "stopped": False,
        "stop_reason": None,
    }

    if not status["due_now"] or status["action"] == "WAIT":
        # Anti-loop / WAIT: STOP — no reprocess
        status["knowledge_delta"] = "NONE"
        self_due.write_status(status, repo)
        wake_report["knowledge_delta"] = "NONE"
        wake_report["stopped"] = True
        wake_report["stop_reason"] = (
            "WAIT: due_now=false — same data / maturity not reached; "
            "no reprocess (anti-loop)"
        )
        out_path = desk / "status" / "WEEKLY_WAKE_REPORT.json"
        out_path.write_text(
            json.dumps(wake_report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "due_now": False,
            "action": "WAIT",
            "knowledge_delta": "NONE",
            "stopped": True,
            "self_due": str(status_path),
            "report": str(out_path),
            "reason": wake_report["stop_reason"],
        }, indent=2))
        return 0

    if args.dry_run:
        wake_report["stopped"] = True
        wake_report["stop_reason"] = "dry-run: due lanes not executed"
        wake_report["would_run"] = status["due_lanes"]
        out_path = desk / "status" / "WEEKLY_WAKE_REPORT.json"
        out_path.write_text(
            json.dumps(wake_report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "due_now": True,
            "action": status["action"],
            "dry_run": True,
            "due_lanes": status["due_lanes"],
            "self_due": str(status_path),
        }, indent=2))
        return 0

    # DUE: run only due lanes
    run_results = run_due_lanes(repo, status)
    wake_report["ran"] = True
    wake_report["run_results"] = run_results
    # Re-evaluate after run for honesty (anti-loop on next identical wake)
    status_after = self_due.evaluate(repo)
    # Preserve wake_kind on post-run status
    status_after["wake_kind"] = "WEEKLY_WAKE"
    status_after["post_run"] = True
    self_due.write_status(status_after, repo)
    wake_report["knowledge_delta"] = status_after.get("knowledge_delta")
    wake_report["post_run_due_now"] = status_after.get("due_now")
    wake_report["post_run_action"] = status_after.get("action")

    out_path = desk / "status" / "WEEKLY_WAKE_REPORT.json"
    out_path.write_text(
        json.dumps(wake_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "due_now": True,
        "action": status["action"],
        "due_lanes": status["due_lanes"],
        "ran": run_results["ran"],
        "rcs": run_results["rcs"],
        "post_run_due_now": status_after.get("due_now"),
        "self_due": str(status_path),
        "report": str(out_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
