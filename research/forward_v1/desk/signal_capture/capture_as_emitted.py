#!/usr/bin/env python3
"""Desk SIGNAL_CAPTURE adapter — ORIGINAL juniper-kite engine ONLY.

Does NOT invent ranking / MARK_BUY / ARMED / TRUST_UP / book_ADD gates.
Calls or documents:
  /workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get/scripts/desk_run_warehouse_write.mts
  /workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get/scripts/live-scan-snapshot.mts

Rules:
- On DATA_STALE → SIGNAL_CAPTURE_BLOCKED_DATA_STALE (not NO_SIGNAL)
- On same bar as last formal T0 → NO_NEW_SIGNAL (do not write duplicate formal batch)
- On success with NEW bar → write NEW immutable T{n}_… batch; never mutate T0
- claimed_p = null; score_label = NOT_A_PROBABILITY
- book_ADD ≠ MARK_BUY (never promote)
- SIGNAL_CAPTURE and OUTCOME_RESOLVER are separate jobs
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
MODEL = "DESK_CORE_V1"
ENGINE_DIR = Path(
    "/workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get"
)
ENGINE_WRITE = ENGINE_DIR / "scripts" / "desk_run_warehouse_write.mts"
ENGINE_SNAP = ENGINE_DIR / "scripts" / "live-scan-snapshot.mts"
T0_DIRNAME = "T0_20260921T183800"


def load_df(root: Path) -> dict:
    p = root / "research/forward_v1/desk/data_factory/DATA_FACTORY_STATUS.json"
    if not p.exists():
        subprocess.run(
            [sys.executable, str(root / "research/forward_v1/desk/tools/data_factory_status.py"),
             "--repo-root", str(root)],
            check=False,
        )
    return json.loads(p.read_text())


def next_tn_dirname(desk: Path, stamp: str) -> str:
    """SIGNAL_CAPTURE batch dir under desk/; never reuse T0; never collide with formal T1_*.

    Formal T1 trees are written only by tools/t1_capture.py after provenance gate.
    """
    return f"SIGNAL_CAPTURE_BATCH_{stamp}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument(
        "--mode",
        choices=["status", "live_engine"],
        default="status",
        help="status=honest gate only; live_engine=invoke original desk_run_warehouse_write.mts when eligible",
    )
    ap.add_argument(
        "--force-same-bar",
        action="store_true",
        help="DANGEROUS research-only: allow capture on same bar as T0 (still new run_id; still never rewrite T0)",
    )
    args = ap.parse_args()
    root = args.repo_root.resolve()
    desk = root / "research/forward_v1/desk"
    out_dir = desk / "signal_capture"
    out_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    run_id = f"desk_capture_{now.strftime('%Y%m%dT%H%M%SZ')}"
    df = load_df(root)

    engine_paths = {
        "desk_run_warehouse_write": str(ENGINE_WRITE),
        "live_scan_snapshot": str(ENGINE_SNAP),
        "engine_dir_exists": ENGINE_DIR.exists(),
        "write_script_exists": ENGINE_WRITE.exists(),
        "snap_script_exists": ENGINE_SNAP.exists(),
        "how_to_call": (
            f"cd {ENGINE_DIR} && npx --yes tsx scripts/desk_run_warehouse_write.mts"
            if ENGINE_WRITE.exists()
            else "ORIGINAL engine scripts missing on this box"
        ),
    }

    base = {
        "schema": "SIGNAL_CAPTURE_STATUS.v1",
        "node": NODE,
        "app_id": APP_ID,
        "model_version": MODEL,
        "evaluation_clock": "LIVE_FORWARD",
        "run_id": run_id,
        "checked_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checked_at_hkt": now.astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "t0_untouched": True,
        "t0_path": f"research/forward_v1/desk/{T0_DIRNAME}/",
        "original_engine": engine_paths,
        "data_factory_status": df.get("status"),
        "data_factory_implication": df.get("signal_capture_implication"),
        "required_event_fields": [
            "event_id", "run_id", "model_version", "signal_timestamp",
            "market_bar_asof", "ticker", "signal_type", "price_at_signal",
            "universe_id", "universe_asof", "rank", "score", "claimed_p",
            "provenance", "conditions_raw",
        ],
        "provenance_gate": "REQUIRED",
        "honesty": [
            "claimed_p=null for DESK_CORE_V1",
            "score/opportunity = NOT_A_PROBABILITY",
            "book_ADD never promoted to MARK_BUY/ARMED/TRUST_UP",
            "never rewrite immutable T0",
            "never invent prices or future bars",
            "filename engine_emit_*.jsonl alone NEVER accepted without ORIGINAL_ENGINE provenance",
            "do not mix LIVE_FORWARD with REPLAY_FORWARD win-rate cohorts",
        ],
    }

    # --- Gate 1: DATA_STALE ---
    # Prefer data_bridge when PRIMARY juniper cache lags: bridge Yahoo is OK for
    # bar-date freshness; ORIGINAL engine still refreshes its own Yahoo on live_engine.
    bridge_path = desk / "data_bridge" / "DATA_BRIDGE_STATUS.json"
    bridge = json.loads(bridge_path.read_text()) if bridge_path.exists() else {}
    bridge_fresh = (
        bridge.get("status") == "DATA_FRESH"
        and str(bridge.get("latest_bar") or "")[:10] > str(df.get("t0_market_bar_asof") or "2026-09-18")[:10]
    )
    factory_fresh = df.get("status") == "DATA_FRESH"
    if not factory_fresh and not bridge_fresh:
        report = {
            **base,
            "status": "SIGNAL_CAPTURE_BLOCKED_DATA_STALE",
            "events_written": 0,
            "new_batch_path": None,
            "note": (
                "Refuse LIVE capture without fresh yahoo bars; "
                "this is DATA_STALE — not NO_SIGNAL / not engine empty."
            ),
            "failure_reason": df.get("failure_reason"),
            "bridge_status": bridge.get("status"),
            "bridge_latest_bar": bridge.get("latest_bar"),
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        blocked = out_dir / "T_CAPTURE_BLOCKED"
        blocked.mkdir(exist_ok=True)
        (blocked / "README.md").write_text(
            "# SIGNAL_CAPTURE_BLOCKED_DATA_STALE\n\n"
            "數據過期，唔好當「無訊號」。等 yahoo cache 追到最新 US session 先跑原引擎。\n"
            "T0 不可改寫。\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2
    if not factory_fresh and bridge_fresh:
        # Honest: primary cache stale, but bridge proves completed bar > T0;
        # live_engine will fetch Yahoo itself — do NOT invent geometry from bridge OHLC.
        base["data_factory_status"] = df.get("status")
        base["data_bridge_unlock"] = {
            "status": bridge.get("status"),
            "latest_bar": bridge.get("latest_bar"),
            "note": (
                "PRIMARY cache STALE; bridge FRESH with latest_bar > T0. "
                "Allow ORIGINAL engine live run (engine refreshes Yahoo). "
                "Yahoo OHLC ≠ Desk geometry."
            ),
        }

    # --- Gate 2: same bar as T0 → NO_NEW_SIGNAL ---
    latest_for_gate = str(
        (bridge.get("latest_bar") if bridge_fresh else None)
        or df.get("latest_bar")
        or ""
    )[:10]
    t0_bar = str(df.get("t0_market_bar_asof") or "2026-09-18")[:10]
    same_bar = (
        df.get("signal_capture_implication") == "NO_NEW_SIGNAL_SAME_BAR_AS_T0"
        or (latest_for_gate and latest_for_gate <= t0_bar)
    )
    if same_bar and not args.force_same_bar:
        report = {
            **base,
            "status": "NO_NEW_SIGNAL",
            "events_written": 0,
            "new_batch_path": None,
            "latest_bar": df.get("latest_bar"),
            "t0_market_bar_asof": df.get("t0_market_bar_asof"),
            "note": df.get("no_new_signal_note"),
            "distinction": (
                "NO_NEW_SIGNAL ≠ DATA_STALE. Data is fresh for last US session; "
                "formal T0 already covers this market_bar_asof. Wait for new daily bar."
            ),
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    # --- Gate 3: engine missing ---
    if not ENGINE_WRITE.exists():
        report = {
            **base,
            "status": "SIGNAL_CAPTURE_BLOCKED_ENGINE_MISSING",
            "events_written": 0,
            "note": f"original desk engine not found at {ENGINE_WRITE}",
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 3

    if args.mode == "status":
        report = {
            **base,
            "status": "LIVE_CAPTURE_ELIGIBLE",
            "events_written": 0,
            "note": (
                "Data gate passed. Re-run with --mode live_engine to invoke ORIGINAL "
                "desk_run_warehouse_write.mts (no second ranking logic)."
            ),
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    # --- live_engine: call ORIGINAL script ---
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    # Point warehouse write at a staging area under signal_capture (append-only new batch)
    stamp = now.astimezone(HKT).strftime("%Y%m%dT%H%M%S+0800")
    batch_name = next_tn_dirname(desk, stamp)
    batch_dir = desk / batch_name
    # Prefer letting original script write its warehouse, then we COPY events into new Tn —
    # but to avoid mutating T0 and to keep GitHub SoT clean, we run engine and then
    # materialize only if it produced a NEW market_bar_asof.
    r = subprocess.run(
        ["npx", "--yes", "tsx", str(ENGINE_WRITE)],
        cwd=str(ENGINE_DIR),
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    if r.returncode != 0:
        report = {
            **base,
            "status": "SIGNAL_CAPTURE_ENGINE_ERROR",
            "events_written": 0,
            "stderr_tail": (r.stderr or "")[-2000:],
            "stdout_tail": (r.stdout or "")[-1000:],
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 4

    # Locate newest journal / warehouse events from engine output paths (documented in T0)
    journal = Path("/workspace/juniper-kite/live/signals/latest.json")
    wh_events = Path("/workspace/waffle-install/research/common_warehouse/events")
    newest_events = None
    if wh_events.exists():
        cands = sorted(wh_events.glob("desk_events_*.jsonl"), key=lambda p: p.stat().st_mtime)
        if cands:
            newest_events = cands[-1]

    events: list[dict] = []
    if newest_events and newest_events.exists():
        for line in newest_events.read_text().splitlines():
            if line.strip():
                events.append(json.loads(line))

    if not events:
        report = {
            **base,
            "status": "SIGNAL_CAPTURE_ENGINE_NO_EVENTS",
            "events_written": 0,
            "note": "engine exited 0 but no desk_events_*.jsonl found; refuse invent",
            "stdout_tail": (r.stdout or "")[-1500:],
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 5

    bars = {e.get("market_bar_asof") for e in events}
    t0_bar = df.get("t0_market_bar_asof")
    if (not args.force_same_bar) and bars and bars <= {t0_bar}:
        report = {
            **base,
            "status": "NO_NEW_SIGNAL",
            "events_written": 0,
            "engine_events_seen": len(events),
            "engine_market_bar_asof": sorted(b for b in bars if b),
            "note": "engine re-emitted same bar as T0; not copied into formal Tn (avoid duplicate pool)",
        }
        (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    # Materialize NEW immutable batch (never touch T0)
    batch_dir.mkdir(parents=True, exist_ok=False)
    engine_run_id = str(events[0].get("run_id") or run_id)
    # content hash of raw engine emit before stamping (machine-checkable)
    raw_body = ("\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n").encode()
    source_hash = hashlib.sha256(raw_body).hexdigest()
    max_asof = max(str(b)[:10] for b in bars if b)

    # Stamp machine-checkable ORIGINAL_ENGINE provenance (do NOT invent geometry —
    # geometry already present from desk_run_warehouse_write conditions_raw/state)
    for e in events:
        e.setdefault("claimed_p", None)
        e.setdefault("score_label", "NOT_A_PROBABILITY")
        e["immutable"] = True
        e["evaluation_clock"] = "LIVE_FORWARD"
        e["source"] = "ORIGINAL_ENGINE"
        e["engine_id"] = e.get("app_id") or APP_ID
        e["engine_version"] = e.get("model_version") or MODEL
        e["engine_run_id"] = engine_run_id
        e["source_hash"] = source_hash
        e["source_provenance"] = {
            "source": "ORIGINAL_ENGINE",
            "engine_id": e["engine_id"],
            "engine_version": e["engine_version"],
            "engine_run_id": engine_run_id,
            "market_bar_asof": e.get("market_bar_asof"),
            "source_hash": source_hash,
        }
        # Keep data_source label (yahoo+scanSymbol = engine bar feed) separate from provenance.source
        e.setdefault("data_source", e.get("data_source") or "yahoo+scanSymbol")
        e.setdefault("provenance", "ORIGINAL_ENGINE")

    events_path = batch_dir / "events.jsonl"
    with events_path.open("w") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    meta = {
        "run_id": engine_run_id,
        "batch_dir": str(batch_dir.relative_to(root)),
        "n_events": len(events),
        "market_bar_asof": sorted(bars),
        "signal_types": {},
        "t0_untouched": True,
        "source": "ORIGINAL_ENGINE",
        "engine_id": APP_ID,
        "engine_version": MODEL,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "provenance_gate": "REQUIRED",
        "source_engine_events": str(newest_events),
        "journal": str(journal) if journal.exists() else None,
    }
    from collections import Counter
    meta["signal_types"] = dict(Counter(e.get("signal_type") for e in events))
    (batch_dir / "CAPTURE_META.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    )
    (batch_dir / "source_provenance.json").write_text(
        json.dumps({
            "source": "ORIGINAL_ENGINE",
            "engine_id": APP_ID,
            "engine_version": MODEL,
            "engine_run_id": engine_run_id,
            "market_bar_asof": max_asof,
            "source_hash": source_hash,
            "provenance_gate": "REQUIRED",
            "note": "stamped by capture_as_emitted after ORIGINAL desk_run_warehouse_write",
        }, indent=2, ensure_ascii=False) + "\n"
    )
    # also mirror under signal_capture/
    mirror = out_dir / f"T_CAPTURE_{stamp}"
    mirror.mkdir(parents=True, exist_ok=True)
    shutil.copy2(events_path, mirror / "events.jsonl")
    (mirror / "CAPTURE_META.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    )
    shutil.copy2(batch_dir / "source_provenance.json", mirror / "source_provenance.json")

    # T1_ENGINE_INBOX — machine-checkable emit for t1_capture provenance gate
    inbox = out_dir / "T1_ENGINE_INBOX"
    inbox.mkdir(parents=True, exist_ok=True)
    emit_name = f"engine_emit_{max_asof}_{engine_run_id}.jsonl"
    emit_path = inbox / emit_name
    with emit_path.open("w") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    (inbox / "source_provenance.json").write_text(
        json.dumps({
            "source": "ORIGINAL_ENGINE",
            "engine_id": APP_ID,
            "engine_version": MODEL,
            "engine_run_id": engine_run_id,
            "market_bar_asof": max_asof,
            "source_hash": source_hash,
            "emit_file": emit_name,
            "provenance_gate": "REQUIRED",
            "geometry_note": "Desk geometry in each row conditions_raw/state (alignScore/opportunity/desk_state/...)",
        }, indent=2, ensure_ascii=False) + "\n"
    )

    report = {
        **base,
        "status": "SIGNAL_CAPTURE_OK",
        "events_written": len(events),
        "new_batch_path": str(batch_dir.relative_to(root)),
        "mirror_path": str(mirror.relative_to(root)),
        "t1_inbox_emit": str(emit_path.relative_to(root)),
        "signal_types": meta["signal_types"],
        "market_bar_asof": sorted(b for b in bars if b),
        "source": "ORIGINAL_ENGINE",
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "provenance_gate": "REQUIRED",
        "note": "New immutable batch with ORIGINAL_ENGINE provenance; T0 not rewritten",
    }
    (out_dir / "SIGNAL_CAPTURE_STATUS.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
