#!/usr/bin/env python3
"""Desk DATA_FACTORY_STATUS — yahoo live bar cache / journal freshness.

Desk LIVE_FORWARD uses juniper-kite yahoo cache (NOT Cap-Rail/RelVol WAREHOUSE_L1).
Never invent bars. Distinguish DATA_STALE vs NO_NEW_SIGNAL vs RESOLVER_WAITING.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
HKT = ZoneInfo("Asia/Hong_Kong")
ET = ZoneInfo("America/New_York")


def _bar_ymd(time_sec: int) -> str:
    # Match T0/resolver: UTC date from yahoo daily epoch
    return datetime.fromtimestamp(int(time_sec), tz=timezone.utc).strftime("%Y-%m-%d")


def _expected_last_completed_us_session(now_utc: datetime) -> str:
    """Last completed US regular-session calendar date (date of RTH close)."""
    et = now_utc.astimezone(ET)
    # RTH close ~16:00 ET; before that, previous weekday is last completed
    d = et.date()
    if et.hour < 16 or (et.hour == 16 and et.minute < 5):
        d = d - timedelta(days=1)
    while d.weekday() >= 5:  # Sat/Sun → Friday
        d = d - timedelta(days=1)
    return d.isoformat()


def scan_cache(cache_dir: Path) -> tuple[list[str], str | None, str | None, dict]:
    symbols: list[str] = []
    latest_by_sym: dict[str, str] = {}
    fetched_ats: list[str] = []
    for p in sorted(cache_dir.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            raw = json.loads(p.read_text())
        except Exception:
            continue
        bars = raw.get("bars") if isinstance(raw, dict) else raw
        if not bars:
            continue
        t = bars[-1].get("time")
        if t is None:
            continue
        ymd = _bar_ymd(int(t))
        symbols.append(p.stem)
        latest_by_sym[p.stem] = ymd
        if isinstance(raw, dict) and raw.get("fetchedAt"):
            fetched_ats.append(str(raw["fetchedAt"]))
    calendar_latest = max(latest_by_sym.values()) if latest_by_sym else None
    last_success = max(fetched_ats) if fetched_ats else None
    return symbols, calendar_latest, last_success, latest_by_sym


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/workspace/juniper-kite/cache/bars"),
    )
    ap.add_argument(
        "--latest-json",
        type=Path,
        default=Path("/workspace/juniper-kite/live/signals/latest.json"),
    )
    args = ap.parse_args()
    root = args.repo_root.resolve()
    now = datetime.now(timezone.utc)
    wall = now.date()
    expected = _expected_last_completed_us_session(now)

    symbols: list[str] = []
    calendar_latest: str | None = None
    last_success: str | None = None
    latest_by_sym: dict[str, str] = {}
    data_source = "yahoo_live_cache_missing"
    failure_reason: str | None = None

    if args.cache_dir.exists():
        symbols, calendar_latest, last_success, latest_by_sym = scan_cache(args.cache_dir)
        data_source = "yahoo_live_cache:/workspace/juniper-kite/cache/bars"
    else:
        failure_reason = f"cache_dir missing: {args.cache_dir}"

    journal_meta = None
    if args.latest_json.exists():
        try:
            journal_meta = json.loads(args.latest_json.read_text())
        except Exception as e:
            journal_meta = {"error": str(e)}

    lag = None
    if calendar_latest:
        lag = (wall - date.fromisoformat(calendar_latest)).days

    # Desk-specific freshness: latest completed US session vs cache
    if not calendar_latest:
        status = "DATA_STALE"
        failure_reason = failure_reason or "no bars in cache"
        signal_impl = "SIGNAL_CAPTURE_BLOCKED_DATA_STALE"
        resolver_impl = "RESOLVER_WAITING"
    elif calendar_latest < expected:
        status = "DATA_STALE"
        failure_reason = (
            f"cache calendar_latest={calendar_latest} behind expected_last_us_session={expected} "
            f"wall={wall.isoformat()}"
        )
        signal_impl = "SIGNAL_CAPTURE_BLOCKED_DATA_STALE"
        resolver_impl = "RESOLVER_WAITING"
    else:
        status = "DATA_FRESH"
        failure_reason = None
        signal_impl = "LIVE_CAPTURE_ELIGIBLE_IF_NEW_BAR_VS_LAST_FORMAL"
        resolver_impl = "RESOLVER_WAITING"  # maturity still needs post-anchor fills

    # Formal T0 bar for NO_NEW_SIGNAL distinction (not the same as DATA_STALE)
    t0_bar = "2026-09-18"
    t0_path = root / "research/forward_v1/desk/T0_20260921T183800/events.jsonl"
    if t0_path.exists():
        try:
            first = json.loads(t0_path.read_text().splitlines()[0])
            t0_bar = first.get("market_bar_asof") or t0_bar
        except Exception:
            pass

    no_new_signal_note = None
    if status == "DATA_FRESH" and calendar_latest and calendar_latest <= t0_bar:
        no_new_signal_note = (
            f"latest_bar={calendar_latest} already formalized as T0 market_bar_asof={t0_bar}; "
            "wait for NEW daily bar after US RTH close before T1+ LIVE_FORWARD events. "
            "This is NO_NEW_SIGNAL / SAME_BAR — NOT DATA_STALE."
        )
        signal_impl = "NO_NEW_SIGNAL_SAME_BAR_AS_T0"

    doc = {
        "schema": "DATA_FACTORY_STATUS.v1",
        "node": NODE,
        "app_id": APP_ID,
        "evaluation_clock": "LIVE_FORWARD",
        "checked_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checked_at_hkt": now.astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "data_source": data_source,
        "data_asof": calendar_latest,
        "calendar_latest": calendar_latest,
        "calendar_end": calendar_latest,
        "latest_bar": calendar_latest,
        "expected_last_us_session": expected,
        "symbols_available": len(symbols),
        "symbols": symbols,
        "latest_bar_by_symbol": latest_by_sym,
        "lookahead_safe": True,
        "freshness_lag_calendar_days_vs_wall": lag,
        "last_success": last_success,
        "failure_reason": failure_reason,
        "status": status,
        "journal_latest": {
            "path": str(args.latest_json) if args.latest_json.exists() else None,
            "captured_at_hkt": (journal_meta or {}).get("captured_at_hkt"),
            "warehouse_run_id": (journal_meta or {}).get("warehouse_run_id"),
            "counts": (journal_meta or {}).get("counts"),
        },
        "t0_market_bar_asof": t0_bar,
        "no_new_signal_note": no_new_signal_note,
        "resolver_implication": resolver_impl,
        "signal_capture_implication": signal_impl,
        "distinctions": {
            "DATA_STALE": status == "DATA_STALE",
            "NO_NEW_SIGNAL": bool(no_new_signal_note),
            "RESOLVER_WAITING": True,
            "SYSTEM_NOT_RUNNING": False,
            "note": (
                "DATA_STALE ≠ NO_NEW_SIGNAL ≠ RESOLVER_WAITING ≠ SYSTEM_NOT_RUNNING. "
                "Desk never mixes LIVE_FORWARD with Cap-Rail/RelVol REPLAY_FORWARD win-rate cohorts."
            ),
        },
        "hard_locks": [
            "never rewrite T0",
            "never invent prices or future bars",
            "book_ADD ≠ MARK_BUY/ARMED/TRUST_UP",
            "score/opportunity = NOT_A_PROBABILITY; claimed_p=null",
            "prefer original juniper-kite desk engine",
        ],
    }

    out = root / "research/forward_v1/desk/data_factory/DATA_FACTORY_STATUS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(doc, indent=2, ensure_ascii=False))
    return 0 if status == "DATA_FRESH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
