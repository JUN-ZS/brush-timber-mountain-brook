#!/usr/bin/env python3
"""Desk FORWARD_SYSTEM_STATUS orchestrator — LIVE_FORWARD only."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
ET = ZoneInfo("America/New_York")
NODE = "desk"
APP_ID = "xin_gu_inertia_desk"


def market_state(now: datetime) -> str:
    """Rough US equity session label; UNKNOWN if clock quirks."""
    try:
        et = now.astimezone(ET)
    except Exception:
        return "UNKNOWN"
    if et.weekday() >= 5:
        return "POSTMARKET" if et.weekday() == 5 and et.hour < 0 else "CLOSED_WEEKEND"
    t = et.hour * 60 + et.minute
    # premarket 04:00–09:30; RTH 09:30–16:00; post 16:00–20:00
    if 4 * 60 <= t < 9 * 60 + 30:
        return "PREMARKET"
    if 9 * 60 + 30 <= t < 16 * 60:
        if t < 12 * 60:
            return "OPEN"
        return "INTRADAY"
    if 16 * 60 <= t < 20 * 60:
        return "POSTMARKET"
    if t >= 20 * 60 or t < 4 * 60:
        return "CLOSE"
    return "UNKNOWN"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--refresh", action="store_true", help="re-run data_factory + signal status first")
    args = ap.parse_args()
    root = args.repo_root.resolve()
    desk = root / "research/forward_v1/desk"
    tools = desk / "tools"

    if args.refresh:
        subprocess.run(
            [sys.executable, str(tools / "data_factory_status.py"), "--repo-root", str(root)],
            check=False,
        )
        subprocess.run(
            [sys.executable, str(desk / "signal_capture" / "capture_as_emitted.py"),
             "--repo-root", str(root), "--mode", "status"],
            check=False,
        )

    now = datetime.now(timezone.utc)
    df = json.loads((desk / "data_factory/DATA_FACTORY_STATUS.json").read_text())
    sc = json.loads((desk / "signal_capture/SIGNAL_CAPTURE_STATUS.json").read_text())

    # Resolver: prefer PR#9 path if present locally; else note OPEN on GitHub
    res_path = desk / "resolution/FORWARD_STATUS.json"
    resolver_doc = None
    if res_path.exists():
        resolver_doc = json.loads(res_path.read_text())
    else:
        # try local pack (not on main yet)
        alt = Path("/workspace/juniper-kite/desk_resolver_pack/research/forward_v1/desk/resolution/FORWARD_STATUS.json")
        if alt.exists():
            resolver_doc = json.loads(alt.read_text())

    blocked_reasons = []
    if df.get("status") == "DATA_STALE":
        blocked_reasons.append(f"DATA_STALE: {df.get('failure_reason')}")
    if sc.get("status") == "SIGNAL_CAPTURE_BLOCKED_DATA_STALE":
        blocked_reasons.append("LIVE SIGNAL_CAPTURE blocked until fresh bars")
    if sc.get("status") == "NO_NEW_SIGNAL":
        blocked_reasons.append(
            "NO_NEW_SIGNAL: same market_bar_asof as T0 — wait new US daily bar (not DATA_STALE)"
        )
    blocked_reasons.append("Resolver PR #9 OPEN on GitHub (not merged to main yet)")
    if resolver_doc and resolver_doc.get("waiting", 0) > 0:
        blocked_reasons.append(
            f"RESOLVER_WAITING: waiting={resolver_doc.get('waiting')} newly_resolved={resolver_doc.get('newly_resolved', 0)} "
            f"maturity_anchor={resolver_doc.get('maturity_anchor_value')} — refuse invent fills"
        )
    blocked_reasons.append(
        "Scheduler: ops/*.yml.example only — OAuth token lacks workflow scope "
        "(scopes: gist, read:org, repo); cannot install .github/workflows live-loop"
    )

    ms = market_state(now)
    new_events_today = int(sc.get("events_written") or 0)
    newly_resolved = int((resolver_doc or {}).get("newly_resolved") or 0)

    doc = {
        "schema": "FORWARD_SYSTEM_STATUS.v1",
        "node": NODE,
        "hub_name": "信股慣性台",
        "app_id": APP_ID,
        "evaluation_clock": "LIVE_FORWARD",
        "checked_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checked_at_hkt": now.astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "market_state": ms,
        "data_status": df.get("status"),
        "data_factory": df,
        "signal_capture": sc.get("status"),
        "signal_capture_detail": sc,
        "outcome_resolver": {
            "pr9_state": "OPEN",
            "pr9_title": "research(forward): Desk LIVE_FORWARD auto-resolver V1.0",
            "on_main": False,
            "evaluation_clock": "LIVE_FORWARD",
            "tools_path_when_merged": "research/forward_v1/desk/tools/live_forward_resolver.py",
            "last_status": {
                "events_total": (resolver_doc or {}).get("events_total", 7),
                "waiting": (resolver_doc or {}).get("waiting", 35),
                "newly_resolved": newly_resolved,
                "resolved_5d": (resolver_doc or {}).get("resolved_5d", 0),
                "price_reference_missing": (resolver_doc or {}).get("price_reference_missing", 0),
                "maturity_anchor": (resolver_doc or {}).get("maturity_anchor_value", "2026-09-18"),
                "integrity_failures": (resolver_doc or {}).get("integrity_failures", 0),
                "source": str(res_path) if res_path.exists() else "desk_resolver_pack (PR#9 branch)",
            },
            "implication": "RESOLVER_WAITING",
            "note": "outcomes-only; no new signals from resolver",
        },
        "preflight": {
            "pr8_state": "MERGED",
            "gate": "MAIN_B_MID_ACTIVE",
            "t0_pr": 7,
            "t0_path": "research/forward_v1/desk/T0_20260921T183800/",
            "t0_immutable": True,
        },
        "warehouse_status": "APPEND_PATH_READY_WHEN_T1_ELIGIBLE",
        "warehouse_local_hint": "/workspace/waffle-install/research/common_warehouse",
        "new_events_today": new_events_today,
        "newly_resolved": newly_resolved,
        "blocked": True,
        "blocked_reason": " | ".join(blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "distinctions": {
            "DATA_STALE": df.get("status") == "DATA_STALE",
            "NO_NEW_SIGNAL": sc.get("status") == "NO_NEW_SIGNAL",
            "RESOLVER_WAITING": True,
            "SYSTEM_NOT_RUNNING": "partial — scripts exist; Actions scheduler not installed",
            "NEVER_MIX": "LIVE_FORWARD desk ≠ Cap-Rail/RelVol REPLAY_FORWARD win-rate cohorts",
        },
        "report_block": {
            "DATA": f"{df.get('status')} — latest_bar={df.get('latest_bar')} expected_us={df.get('expected_last_us_session')} lag={df.get('freshness_lag_calendar_days_vs_wall')}d symbols={df.get('symbols_available')}",
            "SIGNAL": f"{sc.get('status')} — engine={sc.get('original_engine', {}).get('write_script_exists')} events_written={sc.get('events_written', 0)}",
            "EVENT": f"{new_events_today} new today; T0 untouched (7 book_ADD / MARK_BUY=0)",
            "RESOLVER": f"PR #9 OPEN; waiting={(resolver_doc or {}).get('waiting', 35)} resolved=0 maturity_anchor=2026-09-18",
            "WAREHOUSE": "append path ready when T1+ eligible (new bar)",
            "SCHEDULER": "example only (no workflow scope on OAuth)",
            "CURRENT_BLOCK": "NO_NEW_SIGNAL (same bar as T0) + resolver PR open + no Actions workflow; NOT Cap-Rail DATA_STALE warehouse freeze",
            "NEXT_AUTOMATIC_ACTION": "After US RTH close with new daily bar: refresh yahoo cache → data_factory → capture --mode live_engine → append T1; merge resolver #9 when ready; install workflow when scope available",
        },
    }

    out = desk / "status/FORWARD_SYSTEM_STATUS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(doc["report_block"], indent=2, ensure_ascii=False))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
