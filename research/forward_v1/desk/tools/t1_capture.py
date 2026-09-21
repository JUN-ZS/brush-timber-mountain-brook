#!/usr/bin/env python3
"""Desk（信股慣性台）T1 LIVE FORWARD capture gate + confirmation cohort plumbing V1.

Hard locks:
- T0 must NEVER be re-emitted as T1
- Yahoo may resolve outcomes only — never invent Desk signals / geometry
- Genuine new completed daily bar: market_bar_asof > previous formal asof (≈2026-09-18)
- Original Desk engine emit required (juniper-kite desk_run_warehouse_write / live-scan-snapshot)
- book_ADD ≠ MARK_BUY; observation only unless engine emits executable types
- research observes only
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
MODEL = "DESK_CORE_V1"
VERSION = "T1_LIVE_FORWARD_CONFIRMATION_V1"
FORMAL_PREVIOUS_ASOF = "2026-09-18"
EVAL_CLOCK_T1 = "LIVE_FORWARD"
T0_DIRNAME = "T0_20260921T183800"

ENGINE_DIR = Path("/workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get")
ENGINE_WRITE = ENGINE_DIR / "scripts" / "desk_run_warehouse_write.mts"
ENGINE_SNAP = ENGINE_DIR / "scripts" / "live-scan-snapshot.mts"

EXECUTABLE_TYPES = {
    "MARK_BUY", "ARMED", "TRUST_UP", "BUY", "SELL", "OPEN", "CLOSE", "TRIM", "REDUCE", "REVERSE",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def hkt_str(dt: datetime | None = None) -> str:
    return (dt or utc_now()).astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT")


def run_stamp(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def desk_root(repo: Path) -> Path:
    return repo / "research" / "forward_v1" / "desk"


def find_t0(desk: Path) -> Path:
    t0 = desk / T0_DIRNAME
    if t0.is_dir():
        return t0
    cands = sorted(desk.glob("T0_*"))
    if not cands:
        raise SystemExit("no T0_* under desk")
    return cands[-1]


def formal_previous_asof(desk: Path) -> str:
    status_path = desk / "status" / "T1_CAPTURE_STATUS.json"
    if status_path.exists():
        st = load_json(status_path)
        if st.get("formal_previous_asof"):
            return str(st["formal_previous_asof"])[:10]
    t0 = find_t0(desk)
    evs = load_jsonl(t0 / "events.jsonl")
    if evs:
        return str(evs[0].get("market_bar_asof") or FORMAL_PREVIOUS_ASOF)[:10]
    # data factory / bridge
    for rel in (
        "data_factory/DATA_FACTORY_STATUS.json",
        "data_bridge/DATA_BRIDGE_STATUS.json",
        "signal_capture/SIGNAL_CAPTURE_STATUS.json",
    ):
        p = desk / rel
        if p.exists():
            st = load_json(p)
            for k in ("t0_market_bar_asof", "formal_previous_asof"):
                if st.get(k):
                    return str(st[k])[:10]
    return FORMAL_PREVIOUS_ASOF


def latest_completed_bar(desk: Path) -> str | None:
    for rel in (
        "data_bridge/DATA_BRIDGE_STATUS.json",
        "data_factory/DATA_FACTORY_STATUS.json",
    ):
        p = desk / rel
        if p.exists():
            st = load_json(p)
            bar = st.get("latest_bar") or st.get("calendar_latest")
            if bar:
                return str(bar)[:10]
    return None


def looks_like_desk_event(row: dict) -> bool:
    """Reject Yahoo-only invented rows; accept original Desk engine AS_EMITTED shape."""
    if row.get("yahoo_invented_signal") is True:
        return False
    if row.get("source") == "yahoo" and not row.get("signal_type") and not row.get("conditions_raw"):
        return False
    st = str(row.get("signal_type") or "")
    app = str(row.get("app_id") or "")
    model = str(row.get("model_version") or "")
    has_desk_marker = (
        st.startswith("desk.")
        or "book_ADD" in st
        or st.split(".")[-1].upper() in EXECUTABLE_TYPES
        or app == APP_ID
        or model == MODEL
        or bool(row.get("conditions_raw"))
    )
    return bool(row.get("event_id") and row.get("market_bar_asof") and row.get("ticker") and has_desk_marker)


def collect_inbox_emits(desk: Path, required_min_asof: str) -> list[dict]:
    """Scan T1_ENGINE_INBOX + signal_capture + engine warehouse for asof > formal."""
    roots = [
        desk / "signal_capture" / "T1_ENGINE_INBOX",
        desk / "signal_capture",
        desk / "engine_emit",
    ]
    # Original engine warehouse (read-only; never invent)
    wh = Path("/workspace/waffle-install/research/common_warehouse/events")
    if wh.is_dir():
        roots.append(wh)

    found: list[dict] = []
    seen_paths: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        patterns = ["*.jsonl", "events.jsonl", "desk_events_*.jsonl"]
        paths: list[Path] = []
        if root.is_file() and root.suffix == ".jsonl":
            paths = [root]
        else:
            for pat in patterns:
                paths.extend(root.glob(pat))
                paths.extend(root.rglob(pat))
        for path in sorted(set(paths)):
            key = str(path.resolve())
            if key in seen_paths:
                continue
            # skip status / outcome / index files
            name_u = path.name.upper()
            if "STATUS" in name_u or "OUTCOME" in name_u or "INDEX" in name_u:
                continue
            if "T0_" in str(path):
                continue
            seen_paths.add(key)
            try:
                rows = load_jsonl(path)
            except Exception:
                continue
            if not rows:
                continue
            sample = rows[0]
            if not looks_like_desk_event(sample):
                continue
            asofs = sorted({str(r.get("market_bar_asof") or "")[:10] for r in rows if r.get("market_bar_asof")})
            newer = [a for a in asofs if a > required_min_asof]
            if not newer:
                continue
            # Keep only rows with asof > formal
            kept = [r for r in rows if str(r.get("market_bar_asof") or "")[:10] > required_min_asof and looks_like_desk_event(r)]
            if not kept:
                continue
            found.append({
                "path": str(path),
                "n_events": len(kept),
                "market_bar_asof": max(str(r.get("market_bar_asof"))[:10] for r in kept),
                "sample_event_id": kept[0].get("event_id"),
                "source": "ORIGINAL_ENGINE_EMIT",
                "rows": kept,
            })
    found.sort(key=lambda x: x["market_bar_asof"], reverse=True)
    return found


def evaluate_t1_gate(repo: Path) -> dict:
    desk = desk_root(repo)
    prev = formal_previous_asof(desk)
    t0 = find_t0(desk)
    t0_sha = sha256_file(t0 / "events.jsonl")
    latest = latest_completed_bar(desk)

    gate: dict[str, Any] = {
        "schema": "DESK_T1_CAPTURE_GATE.v1",
        "node": NODE,
        "version": VERSION,
        "formal_previous_asof": prev,
        "latest_completed_bar": latest,
        "t0_events_sha256": t0_sha,
        "yahoo_signal_forbidden": True,
        "t0_relabel_forbidden": True,
        "original_engine": {
            "desk_run_warehouse_write": str(ENGINE_WRITE),
            "live_scan_snapshot": str(ENGINE_SNAP),
            "engine_dir_exists": ENGINE_DIR.exists(),
            "write_script_exists": ENGINE_WRITE.exists(),
            "snap_script_exists": ENGINE_SNAP.exists(),
        },
        "checked_at_utc": utc_stamp(),
        "checked_at_hkt": hkt_str(),
    }

    # Gate A: need completed bar newer than formal
    if not latest or latest <= prev:
        gate.update({
            "T1_STATUS": "BLOCKED_WAITING_NEW_BAR",
            "gate_pass": False,
            "NEW_SIGNAL": 0,
            "new_events": 0,
            "confirmation_cohort": "CONFIRMATION_COHORT|EMPTY",
            "confirmation_cohort_open": False,
            "reason": (
                f"No new completed daily bar with market_bar_asof > formal_previous_asof={prev}. "
                f"latest_completed_bar={latest}. "
                "T0 re-emit ≠ T1. Do not invent T1 from Yahoo. "
                "(Honesty: RelVol #44 / BEAM #45 style blocker.)"
            ),
        })
        return gate

    emits = collect_inbox_emits(desk, prev)
    if not emits:
        gate.update({
            "T1_STATUS": "BLOCKED_WAITING_ENGINE_EMIT",
            "gate_pass": False,
            "NEW_SIGNAL": 0,
            "new_events": 0,
            "confirmation_cohort": "CONFIRMATION_COHORT|EMPTY",
            "confirmation_cohort_open": False,
            "detected_bar_asof": latest,
            "reason": (
                f"latest_completed_bar={latest} > formal={prev}, but no original Desk engine "
                "AS_EMITTED payload found in T1_ENGINE_INBOX / signal_capture / warehouse "
                f"with market_bar_asof > {prev}. "
                "Invoke juniper-kite desk_run_warehouse_write.mts after US RTH close; "
                "Yahoo must NOT invent Desk signals."
            ),
        })
        return gate

    best = emits[0]
    gate.update({
        "T1_STATUS": "READY_TO_CAPTURE",
        "gate_pass": True,
        "NEW_SIGNAL": best["n_events"],
        "new_events": best["n_events"],
        "detected_bar_asof": best["market_bar_asof"],
        "detected_emit_path": best["path"],
        "engine_emit": {k: v for k, v in best.items() if k != "rows"},
        "confirmation_cohort_open": True,
        "reason": (
            "Genuine newer market_bar_asof + original Desk engine emit present — "
            "capture path may proceed."
        ),
        "_emit_rows": best["rows"],
    })
    return gate


def open_confirmation_cohort(asof: str, run_id: str) -> str:
    return f"CONFIRMATION_COHORT|T1_PLUS|desk_market_bar_asof={asof}|opened_by={run_id}"


def capture_t1_if_ready(
    repo: Path,
    *,
    run_id: str,
    profile_snapshot: dict | None = None,
) -> dict:
    """Evaluate gate; if pass, freeze immutable T1_* tree + profile snapshot.

    When blocked, still write T1_CAPTURE_STATUS with honesty flags. Never touches T0.
    """
    desk = desk_root(repo)
    now = utc_now()
    gate = evaluate_t1_gate(repo)
    # Strip internal rows before persisting gate
    emit_rows = gate.pop("_emit_rows", None)

    status_dir = desk / "status"
    status_dir.mkdir(parents=True, exist_ok=True)

    out: dict[str, Any] = {
        "schema": "DESK_T1_CAPTURE_STATUS.v1",
        "node": NODE,
        "app_id": APP_ID,
        "model_version": MODEL,
        "version": VERSION,
        "run_id": run_id,
        "written_at_utc": utc_stamp(now),
        "written_at_hkt": hkt_str(now),
        "formal_previous_asof": gate["formal_previous_asof"],
        "gate": gate,
        "T1_STATUS": gate["T1_STATUS"],
        "NEW_SIGNAL": int(gate.get("NEW_SIGNAL") or 0),
        "new_events": int(gate.get("new_events") or 0),
        "new_trades": 0,
        "confirmation_cohort_open": bool(gate.get("confirmation_cohort_open")),
        "confirmation_cohort": gate.get("confirmation_cohort") or "CONFIRMATION_COHORT|EMPTY",
        "t1_path": None,
        "profile_snapshot_path": None,
        "t0_untouched": True,
        "yahoo_invented_signal": False,
        "knowledge_note": (
            "When BLOCKED_WAITING_NEW_BAR / BLOCKED_WAITING_ENGINE_EMIT: plumbing ready; "
            "confirmation_cohort stays EMPTY; NEW_SIGNAL=0; do not invent T1; "
            "T0 discovery hypotheses stay UNTESTED until genuine T1+ confirmation cohort."
        ),
    }

    if not gate.get("gate_pass"):
        write_json(status_dir / "T1_CAPTURE_STATUS.json", out)
        # Mirror blocker note under inbox
        inbox = desk / "signal_capture" / "T1_ENGINE_INBOX"
        inbox.mkdir(parents=True, exist_ok=True)
        write_json(inbox / "LAST_GATE.json", {
            "T1_STATUS": out["T1_STATUS"],
            "reason": gate.get("reason"),
            "formal_previous_asof": out["formal_previous_asof"],
            "latest_completed_bar": gate.get("latest_completed_bar"),
            "checked_at_utc": utc_stamp(now),
        })
        return out

    asof = gate["detected_bar_asof"]
    rows = emit_rows or []
    t1_name = f"T1_{run_stamp(now)}"
    t1_dir = desk / t1_name
    t1_dir.mkdir(parents=True, exist_ok=True)

    cohort_id = open_confirmation_cohort(asof, run_id)
    stamped: list[dict] = []
    for r in rows:
        row = dict(r)
        row["capture_wave"] = "T1"
        row["signal_cohort"] = "confirmation"
        row["confirmation_cohort"] = cohort_id
        row["evaluation_clock"] = EVAL_CLOCK_T1
        row["immutable"] = True
        row["immutable_signal"] = True
        row["t1_capture_run_id"] = run_id
        row["t1_formal_previous_asof"] = gate["formal_previous_asof"]
        row.setdefault("claimed_p", None)
        row.setdefault("score_label", "NOT_A_PROBABILITY")
        stamped.append(row)

    events_path = t1_dir / "events.jsonl"
    with events_path.open("w") as f:
        for row in stamped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Outcome stubs (WAITING) — Yahoo resolves later when bars exist; never invent returns
    horizons = [5, 21, 63, 126, 252]
    outcome_rows: list[dict] = []
    for row in stamped:
        for hz in horizons:
            outcome_rows.append({
                "schema": "common.event_outcome.v1",
                "event_id": row.get("event_id"),
                "ticker": row.get("ticker"),
                "horizon_trading_days": hz,
                "status": "WAITING_FOR_FUTURE_BARS",
                "evaluation_clock": EVAL_CLOCK_T1,
                "benchmark": "QQQ",
                "absolute_return": None,
                "benchmark_return": None,
                "excess_return": None,
                "price_at_signal": row.get("price_at_signal"),
                "market_bar_asof": row.get("market_bar_asof"),
                "confirmation_cohort": cohort_id,
                "capture_wave": "T1",
                "note": "stub — resolve via Yahoo/data_bridge when bars exist; do not invent",
            })
    outcomes_path = t1_dir / "outcomes.jsonl"
    with outcomes_path.open("w") as f:
        for row in outcome_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    profile_path = desk / "research_profile.json"
    profile = profile_snapshot or (load_json(profile_path) if profile_path.exists() else {})
    snap = {
        "schema": "DESK_T1_RESEARCH_PROFILE_SNAPSHOT.v1",
        "captured_at_utc": utc_stamp(now),
        "t1_run_id": run_id,
        "market_bar_asof": asof,
        "confirmation_cohort": cohort_id,
        "profile": profile,
        "locks": {
            "T0_untouched": True,
            "formula_immutable": True,
            "book_ADD_observation_only": True,
            "yahoo_must_not_invent_signal": True,
            "score_ne_probability": True,
            "H_ne_BUY": True,
        },
    }
    snap_path = t1_dir / "research_profile_snapshot.json"
    write_json(snap_path, snap)

    (t1_dir / "README.md").write_text(
        f"""# Desk T1 capture `{t1_name}`

- market_bar_asof: `{asof}` (formal previous: `{gate['formal_previous_asof']}`)
- confirmation_cohort: `{cohort_id}`
- events: `events.jsonl` (n={len(stamped)})
- outcomes stubs: `outcomes.jsonl` (WAITING — Yahoo resolve later)
- research_profile snapshot: `research_profile_snapshot.json`
- T0 untouched; Yahoo did not invent Desk signals
- book_ADD = OBSERVATION unless engine emitted executable types
"""
    )

    # Mirror accepted payload into inbox archive (append-only formal)
    inbox = desk / "signal_capture" / "T1_ENGINE_INBOX"
    inbox.mkdir(parents=True, exist_ok=True)
    mirror = inbox / f"ACCEPTED_{t1_name}"
    mirror.mkdir(parents=True, exist_ok=True)
    with (mirror / "events.jsonl").open("w") as f:
        for row in stamped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_json(mirror / "CAPTURE_META.json", {
        "t1_path": str(t1_dir.relative_to(repo)),
        "n_events": len(stamped),
        "market_bar_asof": asof,
        "confirmation_cohort": cohort_id,
        "run_id": run_id,
    })

    out.update({
        "T1_STATUS": "CAPTURED",
        "confirmation_cohort": cohort_id,
        "confirmation_cohort_open": True,
        "t1_path": str(t1_dir.relative_to(repo)),
        "profile_snapshot_path": str(snap_path.relative_to(repo)),
        "events_path": str(events_path.relative_to(repo)),
        "outcomes_path": str(outcomes_path.relative_to(repo)),
        "NEW_SIGNAL": len(stamped),
        "new_events": len(stamped),
        "market_bar_asof": asof,
    })
    write_json(status_dir / "T1_CAPTURE_STATUS.json", out)

    idx = desk / "research_memory" / "t1_capture_index.jsonl"
    idx.parent.mkdir(parents=True, exist_ok=True)
    with idx.open("a") as f:
        f.write(json.dumps({
            "t1_path": out["t1_path"],
            "run_id": run_id,
            "market_bar_asof": asof,
            "n_events": len(stamped),
            "confirmation_cohort": cohort_id,
            "written_at_utc": utc_stamp(now),
        }, ensure_ascii=False) + "\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Desk T1 capture gate")
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()
    root = args.repo_root.resolve()
    rid = args.run_id or f"T1_GATE_{run_stamp()}"
    if args.gate_only:
        g = evaluate_t1_gate(root)
        g.pop("_emit_rows", None)
        print(json.dumps(g, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(capture_t1_if_ready(root, run_id=rid), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
