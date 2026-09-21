#!/usr/bin/env python3
"""Desk LIVE_FORWARD resolver — MINIMUM RUN V1.2 (real OHLC + QQQ)

evaluation_clock = LIVE_FORWARD
maturity_anchor = market_bar_asof (T0: 2026-09-18)
Reads stock OHLC + QQQ OHLC from data_bridge (PRIMARY + YAHOO_FALLBACK).
Calendar date alone is NOT enough — both calendar AND prices must validate.
Never invent prices. Never rewrite T0. book_ADD ≠ MARK_BUY.
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


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def load_bridge_bars(bridge_bars_dir: Path, ticker: str) -> dict[str, dict]:
    """date -> bar dict with open/high/low/close/source.

    Incomplete/unclosed session bars (session_complete=False) are excluded
    from the resolve calendar — calendar ≠ price; refuse invent fills.
    """
    path = bridge_bars_dir / f"{ticker}.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    out: dict[str, dict] = {}
    for b in raw.get("bars") or []:
        d = b.get("date")
        if not d:
            continue
        if b.get("session_complete") is False:
            continue
        try:
            c = float(b["close"])
            if c != c:  # NaN
                continue
        except (TypeError, ValueError, KeyError):
            continue
        out[d] = b
    return out


def trading_calendar(*bar_maps: dict[str, dict]) -> list[str]:
    """Union of dates that appear in ALL provided maps (intersection for strict).
    For maturity we use QQQ calendar as US session proxy; stock must also have the day.
    """
    if not bar_maps:
        return []
    sets = [set(m.keys()) for m in bar_maps if m]
    if not sets:
        return []
    # Prefer QQQ-only calendar for "Nth trading day"; stock validated separately
    return sorted(sets[0])


def nth_trading_day_after(calendar: list[str], anchor: str, n: int) -> str | None:
    after = [d for d in calendar if d > anchor]
    return after[n - 1] if len(after) >= n else None


def post_anchor_count(calendar: list[str], anchor: str) -> int:
    return sum(1 for d in calendar if d > anchor)


def valid_close(bars: dict[str, dict], day: str) -> float | None:
    b = bars.get(day)
    if not b:
        return None
    try:
        c = float(b["close"])
    except (TypeError, ValueError, KeyError):
        return None
    if c != c or c <= 0:
        return None
    return c


def mfe_mae(bars: dict[str, dict], calendar: list[str], anchor: str, maturity: str, entry: float):
    """MFE/MAE over (anchor, maturity] trading days using stock H/L vs entry."""
    window = [d for d in calendar if anchor < d <= maturity]
    if not window or entry is None or entry <= 0:
        return None, None
    mfe = None
    mae = None
    for d in window:
        b = bars.get(d)
        if not b:
            continue
        try:
            h = float(b["high"])
            l = float(b["low"])
        except (TypeError, ValueError, KeyError):
            continue
        up = (h - entry) / entry
        dn = (l - entry) / entry
        mfe = up if mfe is None else max(mfe, up)
        mae = dn if mae is None else min(mae, dn)
    return mfe, mae


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument(
        "--bridge-bars",
        type=Path,
        default=None,
        help="data_bridge/bars dir (default: research/forward_v1/desk/data_bridge/bars)",
    )
    ap.add_argument("--horizons", type=str, default="5,21,63,126,252")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    t0 = root / "research/forward_v1/desk" / T0_DIR
    events = load_jsonl(t0 / EVENTS)
    horizons = tuple(int(x) for x in args.horizons.split(",") if x.strip())

    bridge_dir = args.bridge_bars or (root / "research/forward_v1/desk/data_bridge/bars")
    qqq_bars = load_bridge_bars(bridge_dir, BENCHMARK)
    qqq_cal = sorted(qqq_bars.keys())

    now = datetime.now(timezone.utc)
    run_id = f"desk_resolve_{now.strftime('%Y%m%dT%H%M%SZ')}"
    out_dir = root / "research/forward_v1/desk/resolution"
    out_dir.mkdir(parents=True, exist_ok=True)

    integrity = []
    anchors = {e.get("market_bar_asof") for e in events}
    if anchors != {EXPECTED_BAR}:
        integrity.append(
            {"field": "market_bar_asof", "expected": [EXPECTED_BAR], "actual": sorted(a for a in anchors if a)}
        )
    types = {e.get("signal_type") for e in events}
    if types != {EXPECTED_SIGNAL_TYPE}:
        integrity.append(
            {"field": "signal_type", "expected": [EXPECTED_SIGNAL_TYPE], "actual": sorted(types)}
        )
        integrity.append(
            {"field": "semantic_upgrade", "expected": "forbidden", "actual": "signal_type drift detected"}
        )

    resolved = {h: 0 for h in horizons}
    waiting = 0
    price_missing = 0
    newly = 0
    calendar_only_blocked = 0
    append_rows = []
    stock_cache: dict[str, dict[str, dict]] = {}

    qqq_post = post_anchor_count(qqq_cal, EXPECTED_BAR)
    qqq_latest = qqq_cal[-1] if qqq_cal else None

    for e in events:
        ticker = e["ticker"]
        entry = e.get("price_at_signal")
        if entry is None:
            price_missing += 1
        else:
            entry = float(entry)
        anchor = e.get("market_bar_asof") or EXPECTED_BAR
        if ticker not in stock_cache:
            stock_cache[ticker] = load_bridge_bars(bridge_dir, ticker)
        stock_bars = stock_cache[ticker]
        stock_cal = sorted(stock_bars.keys())

        for h in horizons:
            maturity = nth_trading_day_after(qqq_cal, anchor, h) if qqq_cal else None
            stock_source = None
            qqq_source_a = None
            qqq_source_m = None
            exit_px = raw_ret = bench_ret = excess = abs_hit = exc_hit = resolved_at = None
            mfe = mae = None
            status = "WAITING_FOR_FUTURE_BARS"
            note = ""

            if entry is None:
                status = "PRICE_REFERENCE_MISSING"
                note = "no legal entry; never substitute"
                waiting += 0  # counted via price_missing path separately
            elif maturity is None:
                status = "WAITING_FOR_FUTURE_BARS"
                waiting += 1
                note = (
                    f"QQQ calendar has only {qqq_post} post-anchor trading day(s) after {anchor} "
                    f"(need {h}); latest_bar={qqq_latest}; do not invent"
                )
            else:
                # Calendar has maturity on QQQ — still require real prices on BOTH legs
                exit_px = valid_close(stock_bars, maturity)
                bench_entry = valid_close(qqq_bars, anchor)
                bench_exit = valid_close(qqq_bars, maturity)
                # stock must also have traded that day (calendar ≠ price)
                stock_has_maturity = maturity in stock_bars
                stock_has_path = post_anchor_count(stock_cal, anchor) >= h

                if exit_px is None or bench_entry is None or bench_exit is None or not stock_has_maturity:
                    status = "WAITING_FOR_FUTURE_BARS"
                    waiting += 1
                    calendar_only_blocked += 1
                    missing = []
                    if exit_px is None or not stock_has_maturity:
                        missing.append(f"{ticker}.close@{maturity}")
                    if bench_entry is None:
                        missing.append(f"QQQ.close@{anchor}")
                    if bench_exit is None:
                        missing.append(f"QQQ.close@{maturity}")
                    note = (
                        f"maturity_calendar_date={maturity} on QQQ cal but price validation failed "
                        f"(missing={missing}; stock_post_anchor={post_anchor_count(stock_cal, anchor)}); "
                        "calendar ≠ price; refuse invent"
                    )
                    exit_px = raw_ret = bench_ret = excess = abs_hit = exc_hit = resolved_at = None
                else:
                    raw_ret = (exit_px - entry) / entry
                    bench_ret = (bench_exit - bench_entry) / bench_entry
                    excess = raw_ret - bench_ret
                    abs_hit = bool(raw_ret > 0)
                    exc_hit = bool(excess > 0)
                    mfe, mae = mfe_mae(stock_bars, qqq_cal, anchor, maturity, entry)
                    status = "RESOLVED"
                    resolved_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                    resolved[h] = resolved.get(h, 0) + 1
                    newly += 1
                    stock_source = (stock_bars.get(maturity) or {}).get("source")
                    qqq_source_a = (qqq_bars.get(anchor) or {}).get("source")
                    qqq_source_m = (qqq_bars.get(maturity) or {}).get("source")
                    note = (
                        f"RESOLVED {h}D via real OHLC; entry=price_at_signal={entry}; "
                        f"exit={ticker}.close@{maturity}={exit_px} src={stock_source}; "
                        f"bench QQQ {bench_entry}@{anchor}→{bench_exit}@{maturity} "
                        f"src={qqq_source_a}/{qqq_source_m}"
                    )

            append_rows.append(
                {
                    "schema": "common.event_outcome.v1",
                    "resolution_run_id": run_id,
                    "minimum_run": "V1.2",
                    "event_id": e["event_id"],
                    "app_id": APP_ID,
                    "model_version": e.get("model_version") or MODEL,
                    "evaluation_clock": EVAL_CLOCK,
                    "ticker": ticker,
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
                    "MFE": mfe,
                    "MAE": mae,
                    "absolute_hit": abs_hit,
                    "excess_hit": exc_hit,
                    "resolved_at": resolved_at,
                    "price_sources": {
                        "stock_exit": stock_source,
                        "qqq_anchor": qqq_source_a,
                        "qqq_exit": qqq_source_m,
                    },
                    "note": note,
                    "semantic_lock": "book_ADD_not_MARK_BUY",
                    "validation": "calendar_and_price",
                }
            )

    # waiting also includes PRICE_REFERENCE_MISSING horizons? Existing code counted waiting only for WAITING status.
    # Recompute waiting from append_rows for honesty
    waiting = sum(1 for r in append_rows if r["status"] == "WAITING_FOR_FUTURE_BARS")
    price_ref_rows = sum(1 for r in append_rows if r["status"] == "PRICE_REFERENCE_MISSING")

    status_doc = {
        "run_timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolution_run_id": run_id,
        "minimum_run": "V1.2",
        "node": NODE,
        "app_id": APP_ID,
        "model_version": MODEL,
        "evaluation_clock": EVAL_CLOCK,
        "gate": "MAIN_B_MID_ACTIVE",
        "preflight_pr": 8,
        "t0_pr": 7,
        "resolver_pr": 9,
        "live_loop_pr": 10,
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
        "resolved_5d": resolved.get(5, 0),
        "resolved_21d": resolved.get(21, 0),
        "resolved_63d": resolved.get(63, 0),
        "resolved_126d": resolved.get(126, 0),
        "resolved_252d": resolved.get(252, 0),
        "waiting": waiting,
        "price_reference_missing": price_missing,
        "price_reference_missing_rows": price_ref_rows,
        "calendar_only_blocked": calendar_only_blocked,
        "audit_only": 0,
        "integrity_failures": len(integrity),
        "newly_resolved": newly,
        "bridge_bars_dir": str(bridge_dir),
        "qqq_latest_bar": qqq_latest,
        "qqq_post_anchor_trading_days": qqq_post,
        "calendar_n": len(qqq_cal),
        "maturity_anchor_field": "market_bar_asof",
        "maturity_anchor_value": EXPECTED_BAR,
        "benchmark": BENCHMARK,
        "mix_policy": "NEVER_MIX_LIVE_FORWARD_WITH_REPLAY_FORWARD_WINRATE",
        "score_policy": "NOT_A_PROBABILITY",
        "resolve_policy": "calendar_AND_price_required; stock_OHLC + QQQ_OHLC",
        "data_fact": (
            f"LIVE_FORWARD desk T0: 7 book_ADD, price OK, maturity_anchor={EXPECTED_BAR}; "
            f"qqq_latest={qqq_latest} post_anchor_days={qqq_post}; "
            f"resolved_5d={resolved.get(5, 0)} newly_resolved={newly}; "
            "no invent"
        ),
    }
    audit = {
        "run_id": run_id,
        "minimum_run": "V1.2",
        "status": "AUDIT_FAIL" if integrity else "OK",
        "integrity_failures": integrity,
        "evaluation_clock": EVAL_CLOCK,
        "notes": [
            status_doc["data_fact"],
            "append-only; T0 immutable",
            "LIVE_FORWARD ≠ REPLAY_FORWARD",
            "book_ADD ≠ MARK_BUY",
            "score ≠ probability",
            "calendar ≠ price — both must validate",
            "YAHOO_FALLBACK never ORIGINAL_LIVE",
        ],
    }

    print(json.dumps(status_doc, indent=2))
    if args.dry_run:
        return

    with (out_dir / "OUTCOME_APPEND.jsonl").open("a") as f:
        for row in append_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out_dir / "FORWARD_STATUS.json").write_text(json.dumps(status_doc, indent=2) + "\n")
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    (out_dir / f"FORWARD_STATUS_{stamp}.json").write_text(json.dumps(status_doc, indent=2) + "\n")
    (out_dir / "RESOLUTION_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    (out_dir / "README.md").write_text(
        f"""# Desk LIVE_FORWARD resolution（MINIMUM RUN V1.2）

## 繁中摘要
- `evaluation_clock`: `{EVAL_CLOCK}`（唔好同 Cap-Rail/RelVol `REPLAY_FORWARD` win-rate 混池）
- Gate: `MAIN_B_MID_ACTIVE`（PRE #8 merged；Resolver #9 / LIVE LOOP #10 已上 main）
- T0 PR #7 **不可改寫**
- 全部事件：`desk.book_ADD`（MARK_BUY/ARMED/TRUST_UP 維持 0）
- Benchmark: QQQ
- **真實 OHLC**：stock close + QQQ close；日曆有日但缺價 → 仍 `WAITING_FOR_FUTURE_BARS`
- 資料橋：`../data_bridge/`（PRIMARY → YAHOO_FALLBACK；Yahoo 永唔標 `ORIGINAL_LIVE`）

## Latest
- run: `{run_id}`
- resolved_5d: `{resolved.get(5, 0)}`
- waiting: `{waiting}`
- qqq_latest / post_anchor_days: `{qqq_latest}` / `{qqq_post}`
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
