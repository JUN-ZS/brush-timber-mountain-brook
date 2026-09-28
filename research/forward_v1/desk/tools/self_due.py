#!/usr/bin/env python3
"""Desk SELF-DUE evaluator — WEEKLY WAKE asks; DUE_RULE / WAIT_RULE decide.

CADENCE ≠ WAKE FREQUENCY.
SHORT/MEDIUM/LONG (1d/5/21/63/126/252) are information/maturity scales,
NOT commands to run daily / every-N-days.

Source of truth: research/forward_v1/desk/TEMPORAL_SELF_AUDIT.json
Implements DUE_RULE / WAIT_RULE / DUE_NOT_DUE_TEMPLATE as executable code.
Never invents T1, never rewrites T0, never changes formulas.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

HKT = timezone(timedelta(hours=8))

HORIZON_LAYER = {
    5: "SHORT",
    21: "MEDIUM",
    63: "MEDIUM",
    126: "LONG",
    252: "LONG",
}
MATURITY_LANES = ("maturity_5d", "maturity_21d", "maturity_63d", "maturity_126d", "maturity_252d")
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


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _now_pair() -> tuple[str, str]:
    utc = datetime.now(timezone.utc).replace(microsecond=0)
    hkt = utc.astimezone(HKT)
    return (
        utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        hkt.strftime("%Y-%m-%d %H:%M:%S HKT"),
    )


def _read_t1_asof(desk: Path, t1_status: dict, audit: dict) -> str:
    t1_file = desk / "T1" / "market_bar_asof"
    if t1_file.exists():
        val = t1_file.read_text(encoding="utf-8").strip()
        if val:
            return val
    asof = t1_status.get("market_bar_asof")
    if asof:
        return str(asof)
    anchor = (audit.get("t1_anchor") or {}).get("market_bar_asof")
    return str(anchor or "")


def _qqq_completed_dates(desk: Path) -> list[str]:
    path = desk / "data_bridge" / "bars" / "QQQ.json"
    if not path.exists():
        return []
    raw = _load(path)
    dates: list[str] = []
    for b in raw.get("bars") or []:
        d = b.get("date")
        if not d:
            continue
        if b.get("session_complete") is False:
            continue
        try:
            c = float(b["close"])
            if c != c or c <= 0:
                continue
        except (TypeError, ValueError, KeyError):
            continue
        dates.append(str(d))
    return sorted(set(dates))


def _post_asof_trading_days(qqq_dates: list[str], asof: str) -> int:
    if not asof:
        return 0
    return sum(1 for d in qqq_dates if d > asof)


def _inbox_newer_emit(
    desk: Path, t1_asof: str, captured_hash: str | None
) -> dict[str, Any] | None:
    """Return first ORIGINAL_ENGINE emit with market_bar_asof > t1_asof and new source_hash."""
    inbox = desk / "signal_capture" / "T1_ENGINE_INBOX"
    if not inbox.exists():
        return None
    candidates: list[dict[str, Any]] = []
    for path in sorted(inbox.rglob("*.jsonl")):
        # Skip already-accepted freeze trees for detection of *new* emits;
        # still allow reading root-level engine_emit_*.jsonl and fresh drops.
        try:
            lines = [
                json.loads(l)
                for l in path.read_text(encoding="utf-8").splitlines()
                if l.strip()
            ]
        except (OSError, json.JSONDecodeError):
            continue
        if not lines:
            continue
        sample = lines[0]
        source = sample.get("source")
        asof = str(sample.get("market_bar_asof") or "")
        sh = sample.get("source_hash")
        if source != "ORIGINAL_ENGINE":
            continue
        if not asof or asof <= t1_asof:
            continue
        if captured_hash and sh and sh == captured_hash:
            continue
        candidates.append(
            {
                "path": str(path),
                "market_bar_asof": asof,
                "source_hash": sh,
                "engine_run_id": sample.get("engine_run_id"),
                "n_events": len(lines),
            }
        )
    if not candidates:
        return None
    # Prefer newest asof
    candidates.sort(key=lambda c: c["market_bar_asof"], reverse=True)
    return candidates[0]


def evaluate(repo: Path | None = None) -> dict[str, Any]:
    repo = (repo or _repo_root_from_here()).resolve()
    desk = _desk(repo)
    utc_s, hkt_s = _now_pair()

    audit = _load(desk / "TEMPORAL_SELF_AUDIT.json")
    maturity = _load(desk / "status" / "OUTCOME_MATURITY_STATUS.json")
    t1_status = _load(desk / "status" / "T1_CAPTURE_STATUS.json")
    bridge = _load(desk / "data_bridge" / "DATA_BRIDGE_STATUS.json")

    t1_asof = _read_t1_asof(desk, t1_status, audit)
    bridge_latest = str(
        bridge.get("latest_bar")
        or bridge.get("last_completed_us_session")
        or ""
    )
    qqq_dates = _qqq_completed_dates(desk)
    if qqq_dates:
        # Prefer live bar calendar over stale status fields
        computed_latest = qqq_dates[-1]
        if not bridge_latest or computed_latest > bridge_latest:
            bridge_latest = computed_latest
    post_days = _post_asof_trading_days(qqq_dates, t1_asof)
    # Prefer computed; fall back to status if bars missing
    if not qqq_dates and maturity.get("post_t1_asof_trading_days") is not None:
        post_days = int(maturity.get("post_t1_asof_trading_days") or 0)

    captured_hash = t1_status.get("source_hash") or (
        (t1_status.get("gate") or {}).get("already_captured_source_hash")
    )
    t1_cap_status = t1_status.get("T1_STATUS") or (
        (t1_status.get("gate") or {}).get("T1_STATUS")
    )
    newer_emit = _inbox_newer_emit(desk, t1_asof, captured_hash)

    new_bar = bool(bridge_latest and t1_asof and bridge_latest > t1_asof)
    # Signal lane: DUE_RULE — new completed bar > asof AND engine emit for signal lane
    signal_due = bool(new_bar and newer_emit is not None)
    signal_reason: str
    if signal_due:
        signal_reason = (
            f"New completed bar {bridge_latest} > T1 asof {t1_asof} "
            f"AND ORIGINAL_ENGINE emit present "
            f"(asof={newer_emit['market_bar_asof']}, path={newer_emit['path']})"
        )
    elif not new_bar:
        signal_reason = (
            f"No new completed bar > T1 asof={t1_asof}; "
            f"bridge_latest={bridge_latest or 'NONE'}; "
            f"T1_STATUS={t1_cap_status or 'UNKNOWN'}"
        )
        if t1_cap_status == "CAPTURED_ALREADY":
            signal_reason += " (CAPTURED_ALREADY — anti-reprocess)"
    else:
        # new bar but no newer ORIGINAL_ENGINE emit
        signal_reason = (
            f"New bar {bridge_latest} > asof {t1_asof} but no new ORIGINAL_ENGINE "
            f"emit in T1_ENGINE_INBOX (do not invent T1 / Yahoo geometry)"
        )

    lanes: dict[str, dict[str, Any]] = {
        "signal_capture": {
            "due_now": signal_due,
            "reason": signal_reason,
            "required_new_data": (
                []
                if signal_due
                else [
                    f"completed US 1d bar date > {t1_asof} for cohort + QQQ (session_complete=true)",
                    "ORIGINAL_ENGINE emit on that new asof with provenance_gate keys + Desk geometry",
                ]
            ),
        }
    }

    due_lanes: list[str] = []
    wait_lanes: list[str] = []
    if signal_due:
        due_lanes.append("signal_capture")
    else:
        wait_lanes.append("signal_capture")

    horizons_waiting = maturity.get("horizons") or {}
    for lane, n in LANE_HORIZON.items():
        hz_key = str(n)
        hz_info = horizons_waiting.get(hz_key) or {}
        waiting = int(hz_info.get("t1_confirmation_waiting") or 0)
        # If status missing, assume stubs exist when T1 captured (audit: 7 per horizon)
        if not horizons_waiting and t1_asof:
            waiting = 7
        status = hz_info.get("status") or (
            "WAITING_FOR_FUTURE_BARS" if waiting else "UNKNOWN"
        )
        maturity_due = post_days >= n and waiting > 0 and status == "WAITING_FOR_FUTURE_BARS"
        if maturity_due:
            reason = (
                f"post_t1_asof_trading_days={post_days} >= {n}; "
                f"{waiting} T1 stubs still WAITING_FOR_FUTURE_BARS"
            )
            due_lanes.append(lane)
        else:
            if post_days < n:
                reason = f"need {n} post-asof trading days; have {post_days}"
            elif waiting <= 0:
                reason = f"no waiting T1 confirmation stubs for horizon={n}"
            else:
                reason = f"horizon={n} status={status}; not due"
            wait_lanes.append(lane)
        lanes[lane] = {
            "due_now": maturity_due,
            "reason": reason,
            "horizon": n,
            "layer": HORIZON_LAYER[n],
            "post_t1_asof_trading_days": post_days,
            "t1_confirmation_waiting": waiting,
            "status": status,
        }

    due_now = bool(due_lanes)

    # action mapping per deliverable
    if not due_now:
        action = "WAIT"
    else:
        layers: set[str] = set()
        if "signal_capture" in due_lanes:
            layers.add("SHORT")
        for lane in due_lanes:
            if lane.startswith("maturity_"):
                layers.add(HORIZON_LAYER[LANE_HORIZON[lane]])
        if "LONG" in layers:
            action = "RUN_LONG"
        elif "MEDIUM" in layers:
            action = "RUN_MEDIUM"
        else:
            action = "RUN_SHORT"

    required_new_data: list[str] = []
    if not signal_due:
        required_new_data.extend(lanes["signal_capture"]["required_new_data"])
    for lane in wait_lanes:
        if lane.startswith("maturity_"):
            n = LANE_HORIZON[lane]
            if post_days < n:
                required_new_data.append(
                    f"{n} completed post-asof US trading days with stock+QQQ closes "
                    f"(have {post_days}; asof={t1_asof})"
                )
    # de-dupe preserve order
    seen: set[str] = set()
    deduped: list[str] = []
    for x in required_new_data:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    required_new_data = deduped

    next_due_condition = (
        f"IF new completed bar date > {t1_asof} AND "
        f"(new ORIGINAL_ENGINE emit with new asof OR "
        f"post_t1_asof_trading_days reaches a horizon N in {{5,21,63,126,252}}) "
        f"THEN due_now for that lane; ELSE remain WAIT / CAPTURED_ALREADY / WAITING_FOR_FUTURE_BARS"
    )

    knowledge_delta = "NONE" if not due_now else "PENDING_RUN"
    # Anti-loop: same data → due_now=false
    anti_loop = {
        "same_data_stops": True,
        "rule": "identical bridge_latest + CAPTURED_ALREADY + post_days < all horizons → due_now=false → STOP",
        "bridge_latest": bridge_latest,
        "t1_asof": t1_asof,
        "T1_STATUS": t1_cap_status,
        "post_t1_asof_trading_days": post_days,
        "triggered_stop": not due_now,
    }

    due_rule = audit.get("DUE_RULE") or (
        "due only if (new completed bar > current asof AND engine emit for signal lane) "
        "OR (post_asof_trading_days >= horizon N for maturity lane)"
    )
    wait_rule = audit.get("WAIT_RULE") or (
        "WAIT if no new completed bar, or identical emit (CAPTURED_ALREADY), "
        "or post_asof_trading_days < N, or provenance/filename-only/Yahoo-geometry block"
    )

    status: dict[str, Any] = {
        "schema": "SELF_DUE_STATUS.v1",
        "node": "desk",
        "hub_name": audit.get("hub_name") or "信股慣性台",
        "app_id": audit.get("app_id") or "xin_gu_inertia_desk",
        "model_version": audit.get("model_version") or "DESK_CORE_V1",
        "pass": "WEEKLY_WAKE_SELF_DUE_V1",
        "wake_kind": "WEEKLY_WAKE",
        "written_at_utc": utc_s,
        "written_at_hkt": hkt_s,
        "evaluation_clock": "LIVE_FORWARD",
        "source_of_truth": "research/forward_v1/desk/TEMPORAL_SELF_AUDIT.json",
        "DUE_RULE": due_rule,
        "WAIT_RULE": wait_rule,
        "CADENCE_NE_WAKE_FREQUENCY": True,
        "note_cadence": (
            "CADENCE ≠ WAKE FREQUENCY. Weekly wake only ASKS self-due. "
            "SHORT/MEDIUM/LONG are information/maturity scales, not daily/every-N-day run commands."
        ),
        "t1_asof": t1_asof,
        "bridge_latest_completed_bar": bridge_latest,
        "post_t1_asof_trading_days": post_days,
        "T1_STATUS": t1_cap_status,
        "newer_engine_emit": newer_emit,
        "due_now": due_now,
        "due_lanes": due_lanes,
        "wait_lanes": wait_lanes,
        "lanes": lanes,
        "reason": (
            "; ".join(lanes[l]["reason"] for l in due_lanes)
            if due_now
            else (
                f"Wake≠due. No due lanes. post_t1={post_days}; "
                f"bridge_latest={bridge_latest}; T1 asof={t1_asof}; "
                f"T1_STATUS={t1_cap_status}."
            )
        ),
        "required_new_data": required_new_data,
        "next_due_condition": next_due_condition,
        "knowledge_delta": knowledge_delta,
        "action": action,
        "anti_loop": anti_loop,
        "hard_locks": [
            "no formula change",
            "no new H",
            "no T0 rewrite",
            "no T1 invent",
            "no Yahoo-as-geometry",
            "cadence ≠ wake frequency",
            "discovery ≠ confirmation",
        ],
    }
    return status


def write_status(status: dict[str, Any], repo: Path | None = None) -> Path:
    repo = (repo or _repo_root_from_here()).resolve()
    out = _desk(repo) / "status" / "SELF_DUE_STATUS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Desk SELF-DUE — evaluate DUE_RULE from TEMPORAL_SELF_AUDIT (no run)"
    )
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument(
        "--write",
        action="store_true",
        help="write status/SELF_DUE_STATUS.json (default: write)",
    )
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="evaluate only; do not write status file",
    )
    args = ap.parse_args()
    repo = (args.repo_root or _repo_root_from_here()).resolve()
    status = evaluate(repo)
    if not args.no_write:
        path = write_status(status, repo)
        print(f"SELF_DUE_STATUS written: {path}")
    print(json.dumps({
        "due_now": status["due_now"],
        "action": status["action"],
        "due_lanes": status["due_lanes"],
        "wait_lanes": status["wait_lanes"],
        "knowledge_delta": status["knowledge_delta"],
        "post_t1_asof_trading_days": status["post_t1_asof_trading_days"],
        "bridge_latest_completed_bar": status["bridge_latest_completed_bar"],
        "t1_asof": status["t1_asof"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
