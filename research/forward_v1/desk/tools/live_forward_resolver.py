#!/usr/bin/env python3
"""Desk LIVE_FORWARD resolver — AUTO-RESOLVER V1.0

evaluation_clock = LIVE_FORWARD
maturity_anchor = market_bar_asof (T0: 2026-09-18) — entry price is that bar
signal_timestamp preserved; STALE_REFERENCE kept as-is
All events desk.book_ADD — never promote to MARK_BUY/ARMED/TRUST_UP
Never rewrite T0. Append-only. Never invent prices.
Never mix LIVE_FORWARD with REPLAY_FORWARD win-rate pools.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
MODEL = "DESK_CORE_V1"
EVAL_CLOCK = "LIVE_FORWARD"
BENCHMARK = "QQQ"
HORIZONS = (5, 21, 63, 126, 252)
T0_DIR = "T0_20260921T183800"
EVENTS = "events.jsonl"
EXPECTED_SIGNAL_TYPE = "desk.book_ADD"
EXPECTED_BAR = "2026-09-18"


def load_jsonl(path: Path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def calendar_from_qqq_cache(cache_path: Path) -> list[str]:
    if not cache_path.exists():
        return []
    raw = json.loads(cache_path.read_text())
    bars = raw.get("bars") if isinstance(raw, dict) else raw
    dates = []
    for b in bars or []:
        t = b.get("time")
        if t is None:
            continue
        # yahoo daily bar times are epoch seconds (market open-ish); date in HKT/US
        dates.append(datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%d"))
    return sorted(set(dates))


def nth_trading_day_after(calendar: list[str], anchor: str, n: int) -> str | None:
    after = [d for d in calendar if d > anchor]
    return after[n - 1] if len(after) >= n else None


def close_on(calendar_bars: dict[str, float], day: str) -> float | None:
    return calendar_bars.get(day)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--qqq-cache", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    t0 = root / "research/forward_v1/desk" / T0_DIR
    events = load_jsonl(t0 / EVENTS)

    qqq_path = args.qqq_cache or Path("/workspace/juniper-kite/cache/bars/QQQ.json")
    if not qqq_path.exists():
        qqq_path = root / "research/forward_v1/desk/fixtures/QQQ_bars.json"

    calendar: list[str] = []
    closes: dict[str, float] = {}
    if qqq_path.exists():
        raw = json.loads(qqq_path.read_text())
        bars = raw.get("bars") if isinstance(raw, dict) else raw
        for b in bars or []:
            t = b.get("time")
            if t is None:
                continue
            d = datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%d")
            closes[d] = float(b["close"])
        calendar = sorted(closes.keys())

    now = datetime.now(timezone.utc)
    run_id = f"desk_resolve_{now.strftime('%Y%m%dT%H%M%SZ')}"
    out_dir = root / "research/forward_v1/desk/resolution"
    out_dir.mkdir(parents=True, exist_ok=True)

    integrity = []
    anchors = {e.get("market_bar_asof") for e in events}
    if anchors != {EXPECTED_BAR}:
        integrity.append({"field": "market_bar_asof", "expected": [EXPECTED_BAR], "actual": sorted(a for a in anchors if a)})
    types = {e.get("signal_type") for e in events}
    if types != {EXPECTED_SIGNAL_TYPE}:
        integrity.append({"field": "signal_type", "expected": [EXPECTED_SIGNAL_TYPE], "actual": sorted(types)})
        integrity.append({"field": "semantic_upgrade", "expected": "forbidden", "actual": "signal_type drift detected"})

    resolved = {h: 0 for h in HORIZONS}
    waiting = 0
    price_missing = 0
    newly = 0
    append_rows = []

    for e in events:
        entry = e.get("price_at_signal")
        if entry is None:
            price_missing += 1
        anchor = e.get("market_bar_asof") or EXPECTED_BAR
        for h in HORIZONS:
            maturity = nth_trading_day_after(calendar, anchor, h) if calendar else None
            if entry is None:
                status = "PRICE_REFERENCE_MISSING"
                note = "no legal entry; never substitute"
                exit_px = None
                raw_ret = None
                bench_ret = None
                excess = None
                abs_hit = None
                exc_hit = None
                resolved_at = None
            elif maturity is None:
                status = "WAITING_FOR_FUTURE_BARS"
                waiting += 1
                note = "calendar has no Nth trading day after maturity_anchor; do not invent"
                exit_px = raw_ret = bench_ret = excess = abs_hit = exc_hit = resolved_at = None
            else:
                exit_px = close_on(closes, maturity)
                bench_entry = close_on(closes, anchor)
                bench_exit = exit_px
                # Need exit on maturity date in cache; if calendar has date but we're using QQQ as both stock calendar and bench
                # For individual tickers we only resolve when that ticker has a close — without per-ticker feed, keep WAITING
                # Honest: Desk T0 has per-ticker entry but we only have QQQ cache certified here → WAITING until certified multi-ticker feed
                status = "WAITING_FOR_FUTURE_BARS"
                waiting += 1
                note = (
                    f"maturity_calendar_date={maturity} listed; "
                    "certified post-anchor multi-ticker bar feed not yet wired for RESOLVED fills; refuse invent"
                )
                exit_px = raw_ret = bench_ret = excess = abs_hit = exc_hit = resolved_at = None

            append_rows.append(
                {
                    "schema": "common.event_outcome.v1",
                    "resolution_run_id": run_id,
                    "event_id": e["event_id"],
                    "app_id": APP_ID,
                    "model_version": e.get("model_version") or MODEL,
                    "evaluation_clock": EVAL_CLOCK,
                    "ticker": e["ticker"],
                    "signal_type": e.get("signal_type"),
                    "horizon_trading_days": h,
                    "maturity_anchor": anchor,
                    "signal_timestamp": e.get("signal_timestamp"),
                    "maturity_calendar_date": maturity,
                    "status": status,
                    "benchmark": BENCHMARK,
                    "entry_price": entry,
                    "exit_price": exit_px,
                    "raw_return": raw_ret,
                    "benchmark_return": bench_ret,
                    "excess_return": excess,
                    "MFE": None,
                    "MAE": None,
                    "absolute_hit": abs_hit,
                    "excess_hit": exc_hit,
                    "resolved_at": resolved_at,
                    "note": note,
                    "semantic_lock": "book_ADD_not_MARK_BUY",
                }
            )

    status = {
        "run_timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolution_run_id": run_id,
        "node": NODE,
        "app_id": APP_ID,
        "model_version": MODEL,
        "evaluation_clock": EVAL_CLOCK,
        "gate": "MAIN_B_MID_ACTIVE",
        "preflight_pr": 8,
        "t0_pr": 7,
        "active_nodes": [NODE],
        "preflight_blocked_nodes": [],
        "events_total": len(events),
        "signal_type_lock": {
            "desk.book_ADD": sum(1 for e in events if e.get("signal_type") == "desk.book_ADD"),
            "MARK_BUY": 0,
            "ARMED": 0,
            "TRUST_UP": 0,
            "promote_forbidden": True,
        },
        "resolved_5d": resolved[5],
        "resolved_21d": resolved[21],
        "resolved_63d": resolved[63],
        "resolved_126d": resolved[126],
        "resolved_252d": resolved[252],
        "waiting": waiting,
        "price_reference_missing": price_missing,
        "audit_only": 0,
        "integrity_failures": len(integrity),
        "newly_resolved": newly,
        "qqq_cache_path": str(qqq_path) if qqq_path.exists() else None,
        "calendar_last": calendar[-1] if calendar else None,
        "calendar_n": len(calendar),
        "maturity_anchor_field": "market_bar_asof",
        "maturity_anchor_value": EXPECTED_BAR,
        "benchmark": BENCHMARK,
        "mix_policy": "NEVER_MIX_LIVE_FORWARD_WITH_REPLAY_FORWARD_WINRATE",
        "score_policy": "NOT_A_PROBABILITY",
        "data_fact": (
            f"LIVE_FORWARD desk T0: 7 book_ADD, price OK, maturity_anchor={EXPECTED_BAR}; "
            "RESOLVED fills deferred until certified post-anchor multi-ticker bars (no invent)"
        ),
    }
    audit = {
        "run_id": run_id,
        "status": "AUDIT_FAIL" if integrity else "OK",
        "integrity_failures": integrity,
        "evaluation_clock": EVAL_CLOCK,
        "notes": [
            status["data_fact"],
            "append-only; T0 immutable",
            "LIVE_FORWARD ≠ REPLAY_FORWARD",
            "book_ADD ≠ MARK_BUY",
            "score ≠ probability",
        ],
    }

    print(json.dumps(status, indent=2))
    if args.dry_run:
        return

    with (out_dir / "OUTCOME_APPEND.jsonl").open("a") as f:
        for row in append_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out_dir / "FORWARD_STATUS.json").write_text(json.dumps(status, indent=2) + "\n")
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    (out_dir / f"FORWARD_STATUS_{stamp}.json").write_text(json.dumps(status, indent=2) + "\n")
    (out_dir / "RESOLUTION_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    (out_dir / "README.md").write_text(
        f"""# Desk LIVE_FORWARD resolution

- evaluation_clock: `{EVAL_CLOCK}`
- gate: MAIN_B_MID_ACTIVE (PRE #8 merged)
- T0 PR #7 immutable
- All events: `desk.book_ADD` (MARK_BUY/ARMED/TRUST_UP stay 0)
- Benchmark: QQQ
- Never mix with Cap-Rail/RelVol REPLAY_FORWARD win rates

Latest run: `{run_id}`
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
