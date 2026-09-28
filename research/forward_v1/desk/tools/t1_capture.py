#!/usr/bin/env python3
"""Desk（信股慣性台）T1 LIVE FORWARD capture + provenance harden V1.

Hard locks:
- T0 must NEVER be re-emitted as T1
- Yahoo may resolve outcomes / bar-date only — never invent Desk geometry
- Genuine new completed daily bar: market_bar_asof > formal previous (2026-09-18)
- Original Desk engine emit required WITH machine-checkable provenance
- Filename alone (e.g. engine_emit_*.jsonl) is NEVER enough to accept an emit
- book_ADD ≠ MARK_BUY; observation only unless engine emits executable types
- Frozen H formulas never change; H ≠ BUY; no new H from T0
- Discovery cohort ≠ confirmation cohort; no price_at_signal backfill
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
MODEL = "DESK_CORE_V1"
VERSION = "T1_PROVENANCE_HARDEN_V1"
FORMAL_PREVIOUS_ASOF = "2026-09-18"
EVAL_CLOCK_T1 = "LIVE_FORWARD"
T0_DIRNAME = "T0_20260921T183800"
ENGINE_ID_DEFAULT = "xin_gu_inertia_desk"
ENGINE_ID_ALIASES = {
    "xin_gu_inertia_desk",
    "DESK_CORE_V1",
    "desk",
    "juniper-kite.desk",
    "desk.scanSymbol",
    "desk_run_warehouse_write",
}

ENGINE_DIR = Path("/workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get")
ENGINE_WRITE = ENGINE_DIR / "scripts" / "desk_run_warehouse_write.mts"
ENGINE_SNAP = ENGINE_DIR / "scripts" / "live-scan-snapshot.mts"

REQUIRED_PROVENANCE_KEYS = (
    "source",
    "engine_id",
    "engine_version",
    "engine_run_id",
    "market_bar_asof",
    "source_hash",
)

# Desk-specific geometry (as available from original Desk emit)
GEOMETRY_KEYS = (
    "alignScore",
    "opportunity",
    "desk_state",
    "regime",
    "shape",
    "trustUp",
    "hot",
    "bandPosPct",
    "relVol20",
    "book_addScore",
    "book_trimScore",
    "book_action",
    "book_board",
    "whyNotBuy",
)
GEOMETRY_CORE = {
    "alignScore",
    "opportunity",
    "desk_state",
    "regime",
    "shape",
    "trustUp",
    "hot",
    "relVol20",
}

FILENAME_ONLY_REJECT = re.compile(r"^engine_emit_.*\.jsonl$", re.IGNORECASE)

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




def already_captured_hashes(desk: Path) -> set[str]:
    """source_hash values already frozen into a formal T1_* tree or T1/ mirror."""
    found: set[str] = set()
    # Fixed mirror
    mir = desk / "T1" / "source_hash"
    if mir.exists():
        v = mir.read_text().strip()
        if v and v != "NULL":
            found.add(v)
    mir_prov = desk / "T1" / "source_provenance.json"
    if mir_prov.exists():
        try:
            p = load_json(mir_prov)
            if p.get("source_hash"):
                found.add(str(p["source_hash"]))
        except Exception:
            pass
    # Timestamped T1_* captures
    for d in desk.glob("T1_*"):
        if not d.is_dir():
            continue
        for cand in (d / "source_hash", d / "source_provenance.json"):
            if not cand.exists():
                continue
            try:
                if cand.name == "source_hash":
                    v = cand.read_text().strip()
                    if v and v != "NULL":
                        found.add(v)
                else:
                    p = load_json(cand)
                    if p.get("source_hash"):
                        found.add(str(p["source_hash"]))
            except Exception:
                continue
    # Index
    idx = desk / "research_memory" / "t1_capture_index.jsonl"
    for row in load_jsonl(idx):
        if row.get("source_hash"):
            found.add(str(row["source_hash"]))
    return found


def already_captured_event_ids(desk: Path) -> set[str]:
    ids: set[str] = set()
    for d in list(desk.glob("T1_*")) + ([desk / "T1"] if (desk / "T1").is_dir() else []):
        for evp in list(d.glob("events.jsonl")) + list((d / "events").glob("*.jsonl")):
            for row in load_jsonl(evp):
                if row.get("event_id"):
                    ids.add(str(row["event_id"]))
    return ids

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


def _normalize_source(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip().upper()
    aliases = {
        "ORIGINAL_ENGINE": "ORIGINAL_ENGINE",
        "ORIGINAL_ENGINE_EMIT": "ORIGINAL_ENGINE",
        "ENGINE_ORIGINAL": "ORIGINAL_ENGINE",
        "DESK_ORIGINAL_ENGINE": "ORIGINAL_ENGINE",
        "JUNIPER_KITE_DESK": "ORIGINAL_ENGINE",
    }
    return aliases.get(s, s)


def _geometry_from_row(sample: dict) -> dict[str, Any]:
    cr = sample.get("conditions_raw") or {}
    if not isinstance(cr, dict):
        cr = {}
    state = sample.get("state") or {}
    if not isinstance(state, dict):
        state = {}
    out: dict[str, Any] = {}
    for k in GEOMETRY_KEYS:
        if k in cr and cr[k] is not None:
            out[k] = cr[k]
        elif k in state and state[k] is not None:
            out[k] = state[k]
        elif k in sample and sample[k] is not None:
            out[k] = sample[k]
    # map state.desk_state etc. already covered; also whyNotBuy at top level
    if "whyNotBuy" not in out and sample.get("whyNotBuy") is not None:
        out["whyNotBuy"] = sample["whyNotBuy"]
    return out


def _looks_like_desk(sample: dict, geometry: dict) -> bool:
    if sample.get("yahoo_invented_signal") is True:
        return False
    if sample.get("yahoo_invented_geometry") is True:
        return False
    st = str(sample.get("signal_type") or "")
    app = str(sample.get("app_id") or "")
    model = str(sample.get("model_version") or "")
    has_marker = (
        st.startswith("desk.")
        or "book_ADD" in st
        or st.split(".")[-1].upper() in EXECUTABLE_TYPES
        or app == APP_ID
        or model == MODEL
        or bool(geometry)
        or bool(sample.get("conditions_raw"))
    )
    return bool(sample.get("event_id") and sample.get("market_bar_asof") and sample.get("ticker") and has_marker)


def _sidecar_provenance(path: Path) -> dict | None:
    for name in ("source_provenance.json", "provenance.json", "emit_provenance.json"):
        side = path.parent / name
        if side.exists():
            try:
                raw = load_json(side)
            except Exception:
                continue
            if isinstance(raw, dict):
                return raw
    return None


def extract_provenance_candidate(path: Path, sample: dict) -> dict[str, Any]:
    """Build provenance candidate from sidecar + row. Does not invent geometry."""
    side = _sidecar_provenance(path) or {}
    row_prov = sample.get("source_provenance") or sample.get("provenance_obj") or {}
    if isinstance(sample.get("provenance"), dict):
        row_prov = {**row_prov, **sample["provenance"]}

    def pick(*keys: str, default: Any = None) -> Any:
        for k in keys:
            if k in side and side[k] not in (None, ""):
                return side[k]
            if isinstance(row_prov, dict) and k in row_prov and row_prov[k] not in (None, ""):
                return row_prov[k]
            if k in sample and sample[k] not in (None, ""):
                return sample[k]
        return default

    source_raw = pick("source", "emit_source")
    # Do NOT treat data_source=yahoo+scanSymbol as ORIGINAL_ENGINE by itself —
    # that is the engine's bar feed label, not provenance. Require explicit stamp.
    if isinstance(source_raw, str) and source_raw.upper() in {
        "YAHOO", "YAHOO_FALLBACK", "REPLAY", "T0_RELABEL", "ENGINE_PACK_REPLAY",
    }:
        source_norm = source_raw.upper()
    else:
        source_norm = _normalize_source(source_raw)

    engine_id = pick("engine_id", "app_id", "engine")
    engine_version = pick("engine_version", "model_version", "version")
    engine_run_id = pick("engine_run_id", "run_id", "emit_run_id")
    market_bar_asof = str(pick("market_bar_asof", "asof", default="") or "")[:10]
    source_hash = pick("source_hash", "emit_hash", "content_hash")
    if not source_hash:
        source_hash = sha256_file(path)

    geometry = _geometry_from_row(sample)
    geo_side = side.get("geometry") or side.get("desk_geometry") or {}
    if isinstance(geo_side, dict):
        for k, v in geo_side.items():
            if k in GEOMETRY_KEYS and k not in geometry:
                geometry[k] = v

    return {
        "source": source_norm,
        "engine_id": engine_id,
        "engine_version": engine_version,
        "engine_run_id": engine_run_id,
        "market_bar_asof": market_bar_asof,
        "source_hash": source_hash,
        "geometry": geometry,
        "sidecar_path": str(path.parent / "source_provenance.json")
        if (path.parent / "source_provenance.json").exists()
        else None,
        "filename": path.name,
        "path": str(path),
    }


def validate_emit_provenance(cand: dict[str, Any], *, required_min_asof: str) -> dict[str, Any]:
    """Machine-checkable provenance gate.

    Rejects:
    - filename-only engine_emit_*.jsonl without ORIGINAL_ENGINE provenance
    - Yahoo / replay / T0-relabel sources
    - missing required keys
    - missing Desk geometry
    - asof <= formal previous
    """
    errors: list[str] = []
    fname = str(cand.get("filename") or "")
    filename_only_pattern = bool(FILENAME_ONLY_REJECT.match(fname))

    source = cand.get("source")
    if source != "ORIGINAL_ENGINE":
        errors.append(
            f"source must be ORIGINAL_ENGINE (got {source!r}); "
            "filename alone is insufficient"
        )

    for key in REQUIRED_PROVENANCE_KEYS:
        if key == "source":
            continue
        if cand.get(key) in (None, ""):
            errors.append(f"missing required provenance field: {key}")

    engine_id = str(cand.get("engine_id") or "")
    if engine_id and engine_id not in ENGINE_ID_ALIASES and not any(
        engine_id.lower().startswith(a.lower()) for a in ENGINE_ID_ALIASES
    ):
        errors.append(f"engine_id not recognized as Desk original engine: {engine_id!r}")

    asof = str(cand.get("market_bar_asof") or "")[:10]
    if not asof or asof <= required_min_asof:
        errors.append(
            f"market_bar_asof={asof!r} must be > formal_previous_asof={required_min_asof!r}"
        )

    geometry = cand.get("geometry") or {}
    if not isinstance(geometry, dict) or not geometry:
        errors.append(
            "missing Desk geometry "
            "(alignScore/opportunity/desk_state/regime/shape/trustUp/hot/…)"
        )
    else:
        if not (GEOMETRY_CORE & set(geometry.keys())):
            errors.append(
                f"geometry present but lacks core Desk keys; got {sorted(geometry)[:10]}"
            )

    if filename_only_pattern and (source != "ORIGINAL_ENGINE" or errors):
        errors.append(
            f"REJECT engine_emit_*.jsonl ({fname}): content provenance incomplete "
            "(filename match alone never accepted)"
        )

    ok = not errors
    return {
        "ok": ok,
        "errors": errors,
        "filename_only_pattern": filename_only_pattern,
        "required_keys": list(REQUIRED_PROVENANCE_KEYS),
        "geometry_keys_found": sorted(geometry.keys()) if isinstance(geometry, dict) else [],
        "provenance_gate": "REQUIRED",
    }


def collect_inbox_emits(desk: Path, required_min_asof: str) -> tuple[list[dict], list[dict]]:
    """Scan inbox for asof > formal WITH machine-checkable provenance.

    Returns (accepted, rejections). Filename-only engine_emit_*.jsonl rejected
    unless content + sidecar prove ORIGINAL_ENGINE.
    """
    roots = [
        desk / "signal_capture" / "T1_ENGINE_INBOX",
        desk / "signal_capture",
        desk / "engine_emit",
    ]
    wh = Path("/workspace/waffle-install/research/common_warehouse/events")
    if wh.is_dir():
        roots.append(wh)

    accepted: list[dict] = []
    rejections: list[dict] = []
    seen_paths: set[str] = set()

    for root in roots:
        if not root.exists():
            continue
        paths: list[Path] = []
        if root.is_file() and root.suffix == ".jsonl":
            paths = [root]
        else:
            for pat in ("*.jsonl", "desk_events_*.jsonl", "engine_emit_*.jsonl"):
                paths.extend(root.glob(pat))
                if root.is_dir():
                    paths.extend(root.rglob(pat))
        for path in sorted(set(paths)):
            key = str(path.resolve())
            if key in seen_paths:
                continue
            name_u = path.name.upper()
            if "STATUS" in name_u or "OUTCOME" in name_u or "INDEX" in name_u:
                continue
            if "T0_" in str(path):
                continue
            # Skip ACCEPTED archives / internal helpers
            if path.name.startswith("_"):
                continue
            seen_paths.add(key)
            try:
                rows = load_jsonl(path)
            except Exception:
                continue
            if not rows:
                continue
            sample = rows[0]
            if not isinstance(sample, dict):
                continue
            if sample.get("yahoo_invented_signal") is True or sample.get("yahoo_invented_geometry") is True:
                rejections.append({"path": str(path), "reason": "yahoo_invented"})
                continue
            geometry = _geometry_from_row(sample)
            if not _looks_like_desk(sample, geometry):
                rejections.append({"path": str(path), "reason": "not_desk_shaped"})
                continue

            cand = extract_provenance_candidate(path, sample)
            # Filter to rows with asof > formal
            kept = [
                r for r in rows
                if str(r.get("market_bar_asof") or "")[:10] > required_min_asof
                and _looks_like_desk(r, _geometry_from_row(r))
            ]
            if not kept:
                rejections.append({
                    "path": str(path),
                    "reason": "no_rows_newer_than_formal",
                    "asofs": sorted({str(r.get("market_bar_asof") or "")[:10] for r in rows}),
                })
                continue

            # Re-extract using first kept row (newer bar)
            cand = extract_provenance_candidate(path, kept[0])
            check = validate_emit_provenance(cand, required_min_asof=required_min_asof)
            if not check["ok"]:
                rejections.append({
                    "path": str(path),
                    "reason": "provenance_failed",
                    "errors": check["errors"],
                    "filename_only_pattern": check["filename_only_pattern"],
                    "source_seen": cand.get("source"),
                })
                continue

            accepted.append({
                "path": str(path),
                "n_events": len(kept),
                "market_bar_asof": max(str(r.get("market_bar_asof"))[:10] for r in kept),
                "sample_event_id": kept[0].get("event_id"),
                "source": "ORIGINAL_ENGINE",
                "provenance": {
                    "source": "ORIGINAL_ENGINE",
                    "engine_id": cand["engine_id"],
                    "engine_version": cand["engine_version"],
                    "engine_run_id": cand["engine_run_id"],
                    "market_bar_asof": cand["market_bar_asof"],
                    "source_hash": cand["source_hash"],
                    "geometry": cand["geometry"],
                },
                "provenance_check": check,
                "rows": kept,
            })

    accepted.sort(key=lambda x: x["market_bar_asof"], reverse=True)
    return accepted, rejections


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
        "yahoo_geometry_forbidden": True,
        "t0_relabel_forbidden": True,
        "filename_only_engine_emit_rejected": True,
        "provenance_gate": "REQUIRED",
        "required_provenance_keys": list(REQUIRED_PROVENANCE_KEYS),
        "required_geometry_keys": list(GEOMETRY_KEYS),
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

    if not latest or latest <= prev:
        gate.update({
            "T1_STATUS": "BLOCKED_WAITING_NEW_BAR",
            "gate_pass": False,
            "NEW_SIGNAL": 0,
            "new_events": 0,
            "confirmation_cohort": "CONFIRMATION_COHORT|EMPTY",
            "confirmation_cohort_open": False,
            "inbox_rejected_count": 0,
            "inbox_accepted_count": 0,
            "reason": (
                f"No new completed daily bar with market_bar_asof > formal_previous_asof={prev}. "
                f"latest_completed_bar={latest}. "
                "T0 re-emit ≠ T1. Do not invent T1 from Yahoo. "
                "provenance_gate=REQUIRED."
            ),
        })
        return gate

    accepted, rejections = collect_inbox_emits(desk, prev)
    if not accepted:
        gate.update({
            "T1_STATUS": "BLOCKED_WAITING_ENGINE_EMIT",
            "gate_pass": False,
            "NEW_SIGNAL": 0,
            "new_events": 0,
            "confirmation_cohort": "CONFIRMATION_COHORT|EMPTY",
            "confirmation_cohort_open": False,
            "detected_bar_asof": latest,
            "inbox_rejected_count": len(rejections),
            "inbox_accepted_count": 0,
            "emit_rejections": rejections[:20],
            "reason": (
                f"latest_completed_bar={latest} > formal={prev}, but no original Desk engine "
                "emit with machine-checkable provenance "
                f"(source=ORIGINAL_ENGINE + {', '.join(REQUIRED_PROVENANCE_KEYS)} + Desk geometry). "
                "Filename engine_emit_*.jsonl alone is REJECTED. "
                "Invoke juniper-kite desk_run_warehouse_write.mts after US RTH close; "
                "Yahoo must NOT invent Desk signals/geometry."
            ),
        })
        return gate

    best = accepted[0]
    prior_hashes = already_captured_hashes(desk)
    prior_events = already_captured_event_ids(desk)
    best_hash = str((best.get("provenance") or {}).get("source_hash") or "")
    best_event_ids = {str(r.get("event_id")) for r in best.get("rows") or [] if r.get("event_id")}
    already = (
        (best_hash and best_hash in prior_hashes)
        or (best_event_ids and best_event_ids.issubset(prior_events))
    )
    if already:
        gate.update({
            "T1_STATUS": "CAPTURED_ALREADY",
            "gate_pass": False,
            "NEW_SIGNAL": 0,
            "new_events": 0,
            "detected_bar_asof": best["market_bar_asof"],
            "detected_emit_path": best["path"],
            "engine_emit": {k: v for k, v in best.items() if k != "rows"},
            "confirmation_cohort_open": True,
            "inbox_rejected_count": len(rejections),
            "inbox_accepted_count": len(accepted),
            "already_captured_source_hash": best_hash or None,
            "reason": (
                f"Emit source_hash={best_hash[:12]}… / event_ids already frozen into T1 — "
                "anti-reprocess: NEW_SIGNAL=0; do not re-capture identical engine emit."
            ),
        })
        return gate

    gate.update({
        "T1_STATUS": "READY_TO_CAPTURE",
        "gate_pass": True,
        "NEW_SIGNAL": best["n_events"],
        "new_events": best["n_events"],
        "detected_bar_asof": best["market_bar_asof"],
        "detected_emit_path": best["path"],
        "engine_emit": {k: v for k, v in best.items() if k != "rows"},
        "confirmation_cohort_open": True,
        "inbox_rejected_count": len(rejections),
        "inbox_accepted_count": len(accepted),
        "reason": (
            "Genuine newer market_bar_asof + ORIGINAL_ENGINE emit with "
            "machine-checkable provenance present — capture path may proceed."
        ),
        "_emit_rows": best["rows"],
        "_emit_provenance": best["provenance"],
    })
    return gate


def open_confirmation_cohort(asof: str, run_id: str) -> str:
    return f"CONFIRMATION_COHORT|T1_PLUS|desk_market_bar_asof={asof}|opened_by={run_id}"


def write_t1_mirror(
    desk: Path,
    *,
    run_id: str,
    status: str,
    blocked_reason: str | None,
    asof: str | None,
    engine_run_id: str | None,
    source_hash: str | None,
    cohort_id: str | None,
    new_signals: int,
    new_events: int,
    profile: dict | None,
    provenance: dict | None,
    rejected_count: int,
) -> Path:
    """Always refresh research/forward_v1/desk/T1/ mirror (blocked or captured)."""
    t1 = desk / "T1"
    (t1 / "events").mkdir(parents=True, exist_ok=True)
    now = utc_stamp()
    capture_status = {
        "schema": "desk.t1_capture.data_wall.v1",
        "run_id": run_id,
        "node": NODE,
        "app_id": APP_ID,
        "model_version": MODEL,
        "version": VERSION,
        "t0_formal_asof": FORMAL_PREVIOUS_ASOF,
        "market_bar_asof": asof,
        "new_signals": new_signals,
        "new_events": new_events,
        "events_file": None if new_events == 0 else "events/",
        "status": status,
        "blocked_reason": blocked_reason,
        "provenance_gate": "REQUIRED",
        "rejected_inbox_rows": rejected_count,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "confirmation_cohort_id": cohort_id,
        "honesty": [
            "T0 ≠ T1",
            "Yahoo ≠ Desk geometry (alignScore/opportunity/desk_state/…)",
            "filename engine_emit_*.jsonl alone is NOT acceptance",
            "require ORIGINAL_ENGINE + engine_run_id + source_hash + Desk geometry",
            "book_ADD ≠ MARK_BUY; H ≠ BUY; no new H from T0",
            "price_at_signal never backfilled",
            "frozen H formula immutable",
        ],
        "checked_at": now,
        "checked_at_hkt": hkt_str(),
    }
    write_json(t1 / "capture_status.json", capture_status)

    snap = {
        "schema": "DESK_T1_RESEARCH_PROFILE_SNAPSHOT.v1",
        "profile_version": "research_profile_v1",
        "node": NODE,
        "snapshot_at": now,
        "t1_run_id": run_id,
        "market_bar_asof": asof,
        "confirmation_cohort_id": cohort_id,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "note": "no T1 yet — profile not re-invented" if status != "CAPTURED" else "frozen at genuine T1",
        "profile": profile if status == "CAPTURED" else {"note": "deferred until genuine T1"},
        "locks": {
            "T0_untouched": True,
            "formula_immutable": True,
            "book_ADD_observation_only": True,
            "yahoo_must_not_invent_signal": True,
            "score_ne_probability": True,
            "H_ne_BUY": True,
            "filename_only_engine_emit_rejected": True,
        },
    }
    write_json(t1 / "research_profile_snapshot.json", snap)

    if provenance and status == "CAPTURED":
        prov = provenance
    else:
        prov = {
            "schema": "DESK_T1_SOURCE_PROVENANCE.v1",
            "status": status,
            "source": None,
            "engine_id": None,
            "engine_version": None,
            "engine_run_id": engine_run_id,
            "market_bar_asof": asof,
            "source_hash": source_hash,
            "confirmation_cohort_id": cohort_id,
            "t0_formal_asof": FORMAL_PREVIOUS_ASOF,
            "yahoo_is_geometry": False,
            "provenance_gate": "REQUIRED",
            "note": "awaiting ORIGINAL_ENGINE emit" if status != "CAPTURED" else "captured",
        }
    write_json(t1 / "source_provenance.json", prov)

    # Flat marker files for machine-check (empty/null when blocked)
    for name, val in (
        ("engine_run_id", engine_run_id),
        ("source_hash", source_hash),
        ("market_bar_asof", asof),
        ("confirmation_cohort_id", cohort_id),
    ):
        p = t1 / name
        if val:
            p.write_text(str(val) + "\n")
        else:
            p.write_text("NULL\n")

    readme = t1 / "README.md"
    readme.write_text(
        f"""# Desk T1 artifact mirror

- status: `{status}`
- provenance_gate: REQUIRED
- formal T0 asof: `{FORMAL_PREVIOUS_ASOF}`
- market_bar_asof: `{asof}`
- confirmation_cohort_id: `{cohort_id}`
- engine_run_id: `{engine_run_id}`
- source_hash: `{source_hash}`

Hard locks: T0≠T1 · Yahoo≠geometry · filename-only emit rejected · book_ADD≠MARK_BUY · H≠BUY
"""
    )
    return t1


def capture_t1_if_ready(
    repo: Path,
    *,
    run_id: str,
    profile_snapshot: dict | None = None,
) -> dict:
    """Evaluate gate; if pass, freeze immutable T1_* tree + T1/ mirror.

    When blocked, still write T1/ + T1_CAPTURE_STATUS with honesty flags. Never touches T0.
    """
    desk = desk_root(repo)
    now = utc_now()
    gate = evaluate_t1_gate(repo)
    emit_rows = gate.pop("_emit_rows", None)
    emit_prov = gate.pop("_emit_provenance", None)

    status_dir = desk / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    profile_path = desk / "research_profile.json"
    profile = profile_snapshot or (load_json(profile_path) if profile_path.exists() else {})

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
        "confirmation_cohort_id": None,
        "engine_run_id": None,
        "source_hash": None,
        "market_bar_asof": None,
        "t1_path": None,
        "t1_mirror_path": "research/forward_v1/desk/T1/",
        "profile_snapshot_path": None,
        "source_provenance_path": None,
        "capture_status_path": None,
        "t0_untouched": True,
        "yahoo_invented_signal": False,
        "filename_only_engine_emit_rejected": True,
        "provenance_gate": "REQUIRED",
        "knowledge_note": (
            "When BLOCKED_WAITING_NEW_BAR / BLOCKED_WAITING_ENGINE_EMIT: plumbing ready; "
            "confirmation_cohort stays EMPTY; NEW_SIGNAL=0; do not invent T1; "
            "filename engine_emit_*.jsonl alone is never accepted; "
            "T0 discovery hypotheses stay UNTESTED until genuine T1+ confirmation cohort."
        ),
    }

    if not gate.get("gate_pass"):
        # Anti-reprocess: keep existing T1/ mirror intact when CAPTURED_ALREADY
        if gate["T1_STATUS"] == "CAPTURED_ALREADY":
            existing_prov = None
            existing_asof = gate.get("detected_bar_asof")
            existing_run = None
            existing_hash = gate.get("already_captured_source_hash")
            existing_cohort = None
            mir_prov = desk / "T1" / "source_provenance.json"
            if mir_prov.exists():
                existing_prov = load_json(mir_prov)
                existing_asof = existing_prov.get("market_bar_asof") or existing_asof
                existing_run = existing_prov.get("engine_run_id")
                existing_hash = existing_prov.get("source_hash") or existing_hash
                existing_cohort = existing_prov.get("confirmation_cohort_id")
            out.update({
                "T1_STATUS": "CAPTURED_ALREADY",
                "NEW_SIGNAL": 0,
                "new_events": 0,
                "confirmation_cohort_open": True,
                "confirmation_cohort": existing_cohort or out["confirmation_cohort"],
                "confirmation_cohort_id": existing_cohort,
                "engine_run_id": existing_run,
                "source_hash": existing_hash,
                "market_bar_asof": existing_asof,
                "t1_path": "research/forward_v1/desk/T1/",
                "knowledge_note": (
                    "Anti-reprocess: identical ORIGINAL_ENGINE emit already captured; "
                    "NEW_SIGNAL=0; knowledge_delta should be NONE on identical inputs."
                ),
            })
            write_json(status_dir / "T1_CAPTURE_STATUS.json", out)
            return out

        mirror = write_t1_mirror(
            desk,
            run_id=run_id,
            status=gate["T1_STATUS"],
            blocked_reason=gate.get("reason"),
            asof=gate.get("detected_bar_asof") or gate.get("latest_completed_bar"),
            engine_run_id=None,
            source_hash=None,
            cohort_id=None,
            new_signals=0,
            new_events=0,
            profile=profile,
            provenance=None,
            rejected_count=int(gate.get("inbox_rejected_count") or 0),
        )
        out["capture_status_path"] = str((mirror / "capture_status.json").relative_to(repo))
        out["source_provenance_path"] = str((mirror / "source_provenance.json").relative_to(repo))
        out["profile_snapshot_path"] = str((mirror / "research_profile_snapshot.json").relative_to(repo))
        write_json(status_dir / "T1_CAPTURE_STATUS.json", out)
        inbox = desk / "signal_capture" / "T1_ENGINE_INBOX"
        inbox.mkdir(parents=True, exist_ok=True)
        write_json(inbox / "LAST_GATE.json", {
            "T1_STATUS": out["T1_STATUS"],
            "reason": gate.get("reason"),
            "formal_previous_asof": out["formal_previous_asof"],
            "latest_completed_bar": gate.get("latest_completed_bar"),
            "provenance_gate": "REQUIRED",
            "inbox_rejected_count": gate.get("inbox_rejected_count"),
            "checked_at_utc": utc_stamp(now),
        })
        return out

    asof = gate["detected_bar_asof"]
    rows = emit_rows or []
    prov = emit_prov or {}
    t1_name = f"T1_{run_stamp(now)}"
    t1_dir = desk / t1_name
    events_dir = t1_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    cohort_id = open_confirmation_cohort(asof, run_id)
    engine_run_id = str(prov.get("engine_run_id") or run_id)
    source_hash = str(prov.get("source_hash") or "")
    if not source_hash and gate.get("detected_emit_path"):
        source_hash = sha256_file(Path(gate["detected_emit_path"])) or ""

    stamped: list[dict] = []
    for r in rows:
        row = dict(r)
        row["capture_wave"] = "T1"
        row["signal_cohort"] = "confirmation"
        row["confirmation_cohort"] = cohort_id
        row["confirmation_cohort_id"] = cohort_id
        row["evaluation_clock"] = EVAL_CLOCK_T1
        row["immutable"] = True
        row["immutable_signal"] = True
        row["t1_capture_run_id"] = run_id
        row["t1_formal_previous_asof"] = gate["formal_previous_asof"]
        row["engine_run_id"] = engine_run_id
        row["source_hash"] = source_hash
        row["source"] = "ORIGINAL_ENGINE"
        row["source_provenance"] = {
            "source": "ORIGINAL_ENGINE",
            "engine_id": prov.get("engine_id") or ENGINE_ID_DEFAULT,
            "engine_version": prov.get("engine_version") or MODEL,
            "engine_run_id": engine_run_id,
            "market_bar_asof": asof,
            "source_hash": source_hash,
        }
        row.setdefault("claimed_p", None)
        row.setdefault("score_label", "NOT_A_PROBABILITY")
        stamped.append(row)

    events_path = events_dir / f"desk_t1_events_{run_stamp(now)}.jsonl"
    with events_path.open("w") as f:
        for row in stamped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # also flat events.jsonl for compatibility
    with (t1_dir / "events.jsonl").open("w") as f:
        for row in stamped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

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
    with (t1_dir / "outcomes.jsonl").open("w") as f:
        for row in outcome_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    snap = {
        "schema": "DESK_T1_RESEARCH_PROFILE_SNAPSHOT.v1",
        "captured_at_utc": utc_stamp(now),
        "t1_run_id": run_id,
        "market_bar_asof": asof,
        "confirmation_cohort_id": cohort_id,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "profile": profile,
        "locks": {
            "T0_untouched": True,
            "formula_immutable": True,
            "book_ADD_observation_only": True,
            "yahoo_must_not_invent_signal": True,
            "score_ne_probability": True,
            "H_ne_BUY": True,
            "filename_only_engine_emit_rejected": True,
        },
    }
    write_json(t1_dir / "research_profile_snapshot.json", snap)

    full_prov = {
        "schema": "DESK_T1_SOURCE_PROVENANCE.v1",
        "source": "ORIGINAL_ENGINE",
        "engine_id": prov.get("engine_id") or ENGINE_ID_DEFAULT,
        "engine_version": prov.get("engine_version") or MODEL,
        "engine_run_id": engine_run_id,
        "market_bar_asof": asof,
        "source_hash": source_hash,
        "events_sha256": sha256_file(events_path),
        "confirmation_cohort_id": cohort_id,
        "geometry": prov.get("geometry") or {},
        "provenance_gate": "REQUIRED",
        "locks": {
            "T0_neq_T1": True,
            "Yahoo_neq_geometry": True,
            "frozen_H_immutable": True,
            "discovery_neq_confirmation": True,
            "no_price_backfill": True,
            "H_neq_BUY": True,
            "book_ADD_neq_MARK_BUY": True,
            "filename_only_engine_emit_rejected": True,
        },
    }
    write_json(t1_dir / "source_provenance.json", full_prov)

    capture_status = {
        "schema": "desk.t1_capture.data_wall.v1",
        "run_id": run_id,
        "node": NODE,
        "status": "CAPTURED",
        "new_signals": len(stamped),
        "new_events": len(stamped),
        "market_bar_asof": asof,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "confirmation_cohort_id": cohort_id,
        "provenance_gate": "REQUIRED",
        "t1_path": str(t1_dir.relative_to(repo)),
        "checked_at": utc_stamp(now),
    }
    write_json(t1_dir / "capture_status.json", capture_status)

    for name, val in (
        ("engine_run_id", engine_run_id),
        ("source_hash", source_hash),
        ("market_bar_asof", asof),
        ("confirmation_cohort_id", cohort_id),
    ):
        (t1_dir / name).write_text(str(val) + "\n")

    (t1_dir / "README.md").write_text(
        f"""# Desk T1 capture `{t1_name}`

- market_bar_asof: `{asof}` (formal previous: `{gate['formal_previous_asof']}`)
- confirmation_cohort_id: `{cohort_id}`
- engine_run_id: `{engine_run_id}`
- source_hash: `{source_hash}`
- events: `events/` + `events.jsonl` (n={len(stamped)})
- outcomes stubs: `outcomes.jsonl` (WAITING — Yahoo resolve later)
- research_profile snapshot: `research_profile_snapshot.json`
- source_provenance: `source_provenance.json`
- T0 untouched; Yahoo did not invent Desk signals
- book_ADD = OBSERVATION unless engine emitted executable types
- provenance_gate: REQUIRED
"""
    )

    # Mirror to fixed T1/ path (replace events — never accumulate re-process copies)
    write_t1_mirror(
        desk,
        run_id=run_id,
        status="CAPTURED",
        blocked_reason=None,
        asof=asof,
        engine_run_id=engine_run_id,
        source_hash=source_hash,
        cohort_id=cohort_id,
        new_signals=len(stamped),
        new_events=len(stamped),
        profile=profile,
        provenance=full_prov,
        rejected_count=int(gate.get("inbox_rejected_count") or 0),
    )
    mirror_events_dir = desk / "T1" / "events"
    if mirror_events_dir.exists():
        for oldp in mirror_events_dir.glob("*.jsonl"):
            oldp.unlink()
    mirror_events_dir.mkdir(parents=True, exist_ok=True)
    (mirror_events_dir / events_path.name).write_text(events_path.read_text())
    (mirror_events_dir / "events.jsonl").write_text(events_path.read_text())

    # Inbox archive
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
        "confirmation_cohort_id": cohort_id,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
        "run_id": run_id,
    })
    write_json(mirror / "source_provenance.json", full_prov)

    out.update({
        "T1_STATUS": "CAPTURED",
        "confirmation_cohort": cohort_id,
        "confirmation_cohort_id": cohort_id,
        "confirmation_cohort_open": True,
        "t1_path": str(t1_dir.relative_to(repo)),
        "profile_snapshot_path": str((t1_dir / "research_profile_snapshot.json").relative_to(repo)),
        "source_provenance_path": str((t1_dir / "source_provenance.json").relative_to(repo)),
        "capture_status_path": str((t1_dir / "capture_status.json").relative_to(repo)),
        "events_path": str(events_path.relative_to(repo)),
        "outcomes_path": str((t1_dir / "outcomes.jsonl").relative_to(repo)),
        "NEW_SIGNAL": len(stamped),
        "new_events": len(stamped),
        "market_bar_asof": asof,
        "engine_run_id": engine_run_id,
        "source_hash": source_hash,
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
            "confirmation_cohort_id": cohort_id,
            "engine_run_id": engine_run_id,
            "source_hash": source_hash,
            "written_at_utc": utc_stamp(now),
        }, ensure_ascii=False) + "\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Desk T1 capture gate (provenance harden)")
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()
    root = args.repo_root.resolve()
    rid = args.run_id or f"T1_GATE_{run_stamp()}"
    if args.gate_only:
        g = evaluate_t1_gate(root)
        g.pop("_emit_rows", None)
        g.pop("_emit_provenance", None)
        print(json.dumps(g, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(capture_t1_if_ready(root, run_id=rid), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
