#!/usr/bin/env python3
"""Desk FORWARD_SYSTEM_STATUS orchestrator — LIVE_FORWARD MINIMUM RUN V1.2."""
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
    try:
        et = now.astimezone(ET)
    except Exception:
        return "UNKNOWN"
    if et.weekday() >= 5:
        return "CLOSED_WEEKEND"
    t = et.hour * 60 + et.minute
    if 4 * 60 <= t < 9 * 60 + 30:
        return "PREMARKET"
    if 9 * 60 + 30 <= t < 16 * 60:
        return "OPEN" if t < 12 * 60 else "INTRADAY"
    if 16 * 60 <= t < 20 * 60:
        return "POSTMARKET"
    return "CLOSE"


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
            [
                sys.executable,
                str(desk / "signal_capture" / "capture_as_emitted.py"),
                "--repo-root",
                str(root),
                "--mode",
                "status",
            ],
            check=False,
        )

    now = datetime.now(timezone.utc)
    df = json.loads((desk / "data_factory/DATA_FACTORY_STATUS.json").read_text())
    sc = json.loads((desk / "signal_capture/SIGNAL_CAPTURE_STATUS.json").read_text())

    bridge_path = desk / "data_bridge/DATA_BRIDGE_STATUS.json"
    bridge = json.loads(bridge_path.read_text()) if bridge_path.exists() else None

    res_path = desk / "resolution/FORWARD_STATUS.json"
    resolver_doc = json.loads(res_path.read_text()) if res_path.exists() else None

    blocked_reasons = []
    if df.get("status") == "DATA_STALE":
        blocked_reasons.append(f"DATA_STALE: {df.get('failure_reason')}")
    if sc.get("status") == "SIGNAL_CAPTURE_BLOCKED_DATA_STALE":
        blocked_reasons.append("LIVE SIGNAL_CAPTURE blocked until fresh bars")
    if sc.get("status") == "NO_NEW_SIGNAL":
        blocked_reasons.append(
            "NO_NEW_SIGNAL: same market_bar_asof as T0 — wait new US daily bar (not DATA_STALE)"
        )

    r5 = int((resolver_doc or {}).get("resolved_5d") or 0)
    waiting = int((resolver_doc or {}).get("waiting") or 0)
    post = (bridge or {}).get("post_anchor_trading_days_qqq")
    if post is None:
        post = (resolver_doc or {}).get("qqq_post_anchor_trading_days", 0)
    if r5 == 0 and waiting > 0:
        blocked_reasons.append(
            f"RESOLVER_WAITING: waiting={waiting} resolved_5d={r5} "
            f"post_anchor_days={post} maturity_anchor="
            f"{(resolver_doc or {}).get('maturity_anchor_value', '2026-09-18')} — refuse invent fills"
        )
    blocked_reasons.append(
        "Scheduler: ops/*.yml.example only — OAuth token lacks workflow scope "
        "(scopes: gist, read:org, repo); cannot install .github/workflows live-loop"
    )

    ms = market_state(now)
    new_events_today = int(sc.get("events_written") or 0)
    newly_resolved = int((resolver_doc or {}).get("newly_resolved") or 0)
    latest_bar = (bridge or {}).get("latest_bar") or df.get("latest_bar")

    resolver_implication = "RESOLVED_PARTIAL" if r5 > 0 else "RESOLVER_WAITING"
    if bridge and bridge.get("resolver_implication"):
        # bridge implication is readiness; prefer resolver actual
        pass

    data_line = (
        f"{(bridge or df).get('status') if bridge else df.get('status')} — "
        f"latest_bar={latest_bar} "
        f"post_anchor_days={post} "
        f"bridge={'YAHOO_FALLBACK+PRIMARY' if bridge else 'none'} "
        f"expected_us={df.get('expected_last_us_session')}"
    )
    resolver_line = (
        f"V1.2 OHLC resolver on main path; waiting={waiting} resolved_5d={r5} "
        f"newly_resolved={newly_resolved} maturity_anchor="
        f"{(resolver_doc or {}).get('maturity_anchor_value', '2026-09-18')} "
        f"qqq_post={post}"
    )

    next_action = (
        "When US session prints ≥5 trading days after 2026-09-18: "
        "data_bridge.py → resolve_5d.py → expect resolved_5d>0; "
        "T1 only on NEW bar after T0 asof (else NO_NEW_SIGNAL). "
        "Install Actions workflow when OAuth gains workflow scope."
    )
    if r5 > 0:
        next_action = (
            "Continue LIVE_FORWARD: refresh bridge after each US daily close; "
            "resolve remaining horizons; T1 on new bar only."
        )

    current_block = (
        f"NO_NEW_SIGNAL (same bar as T0) + RESOLVER_WAITING "
        f"(post_anchor_days={post}<5) + no Actions workflow; "
        "NOT Cap-Rail DATA_STALE warehouse freeze; tools ready"
    )
    if r5 > 0:
        current_block = "partial: some 5D resolved; scheduler still example-only"

    doc = {
        "schema": "FORWARD_SYSTEM_STATUS.v1",
        "node": NODE,
        "hub_name": "信股慣性台",
        "app_id": APP_ID,
        "evaluation_clock": "LIVE_FORWARD",
        "minimum_run": "V1.2",
        "checked_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checked_at_hkt": now.astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "market_state": ms,
        "data_status": (bridge or {}).get("status") or df.get("status"),
        "data_bridge": bridge,
        "data_factory": df,
        "signal_capture": sc.get("status"),
        "signal_capture_detail": sc,
        "outcome_resolver": {
            "pr9_state": "MERGED",
            "pr10_state": "MERGED",
            "minimum_run": "V1.2",
            "on_main": True,
            "evaluation_clock": "LIVE_FORWARD",
            "tools_path": "research/forward_v1/desk/tools/live_forward_resolver.py",
            "resolve_5d_path": "research/forward_v1/desk/tools/resolve_5d.py",
            "data_bridge_path": "research/forward_v1/desk/tools/data_bridge.py",
            "last_status": {
                "events_total": (resolver_doc or {}).get("events_total", 7),
                "waiting": waiting,
                "newly_resolved": newly_resolved,
                "resolved_5d": r5,
                "price_reference_missing": (resolver_doc or {}).get("price_reference_missing", 0),
                "maturity_anchor": (resolver_doc or {}).get("maturity_anchor_value", "2026-09-18"),
                "qqq_post_anchor_trading_days": post,
                "integrity_failures": (resolver_doc or {}).get("integrity_failures", 0),
                "source": str(res_path) if res_path.exists() else None,
            },
            "implication": resolver_implication,
            "note": "outcomes-only; calendar_AND_price; no new signals from resolver",
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
            "RESOLVER_WAITING": r5 == 0 and waiting > 0,
            "SYSTEM_NOT_RUNNING": "partial — V1.2 tools run locally; Actions scheduler not installed",
            "NEVER_MIX": "LIVE_FORWARD desk ≠ Cap-Rail/RelVol REPLAY_FORWARD win-rate cohorts",
        },
        "report_block": {
            "DATA": data_line,
            "SIGNAL": f"{sc.get('status')} — engine={sc.get('original_engine', {}).get('write_script_exists')} events_written={sc.get('events_written', 0)}",
            "EVENT": f"{new_events_today} new today; T0 untouched (7 book_ADD / MARK_BUY=0)",
            "RESOLVER": resolver_line,
            "WAREHOUSE": "append path ready when T1+ eligible (new bar); OUTCOME_APPEND append-only",
            "SCHEDULER": "example only (no workflow scope on OAuth)",
            "CURRENT_BLOCK": current_block,
            "NEXT_AUTOMATIC_ACTION": next_action,
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
