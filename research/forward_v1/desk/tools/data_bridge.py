#!/usr/bin/env python3
"""Desk DATA → SIGNAL bridge (MINIMUM RUN V1.2)

PRIMARY = juniper-kite yahoo live cache (if present)
YAHOO_FALLBACK = yfinance daily OHLCV for post-anchor gaps

Hard locks:
- never invent prices
- YAHOO_FALLBACK labeled with source/data_asof/retrieved_at/frequency/ticker
- never call YAHOO_FALLBACK ORIGINAL_LIVE
- T0 immutable; evaluation_clock=LIVE_FORWARD
- do not mix with Cap-Rail/RelVol REPLAY_FORWARD
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
EVAL_CLOCK = "LIVE_FORWARD"
T0_DIR = "T0_20260921T183800"
BENCHMARK = "QQQ"
DEFAULT_PRIMARY = Path("/workspace/juniper-kite/cache/bars")
FREQUENCY = "1d"
ET = ZoneInfo("America/New_York")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _last_completed_us_session_date(now: datetime | None = None) -> str:
    """Last completed US RTH calendar date (close ~16:05 ET)."""
    et = (now or _utc_now()).astimezone(ET)
    d = et.date()
    if et.hour < 16 or (et.hour == 16 and et.minute < 5):
        d = d - timedelta(days=1)
    while d.weekday() >= 5:
        d = d - timedelta(days=1)
    return d.isoformat()


def _mark_session_complete(bar: dict, completed_through: str) -> dict:
    """Bars after last completed US session are incomplete — not for resolve fills."""
    out = dict(bar)
    d = out.get("date")
    complete = bool(d and d <= completed_through)
    out["session_complete"] = complete
    if not complete:
        out["session_note"] = (
            f"INCOMPLETE_OR_UNCLOSED vs last_completed_us_session={completed_through}; "
            "excluded from post_anchor resolve calendar"
        )
    return out


def _bar_ymd_from_epoch(time_sec: int) -> str:
    return datetime.fromtimestamp(int(time_sec), tz=timezone.utc).strftime("%Y-%m-%d")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def read_t0_tickers(t0: Path) -> tuple[list[str], str]:
    events = load_jsonl(t0 / "events.jsonl")
    tickers = sorted({e["ticker"] for e in events if e.get("ticker")})
    anchors = {e.get("market_bar_asof") for e in events}
    anchor = sorted(a for a in anchors if a)[0] if anchors else "2026-09-18"
    return tickers, anchor


def load_primary_bars(cache_dir: Path, ticker: str) -> dict[str, dict]:
    """Return date -> {open,high,low,close,volume,source=PRIMARY,...}."""
    path = cache_dir / f"{ticker}.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except Exception:
        return {}
    bars = raw.get("bars") if isinstance(raw, dict) else raw
    out: dict[str, dict] = {}
    for b in bars or []:
        t = b.get("time")
        if t is None:
            continue
        d = _bar_ymd_from_epoch(int(t))
        out[d] = {
            "date": d,
            "open": float(b["open"]),
            "high": float(b["high"]),
            "low": float(b["low"]),
            "close": float(b["close"]),
            "volume": float(b.get("volume") or 0),
            "source": "PRIMARY",
            "primary_path": str(path),
            "frequency": FREQUENCY,
            "ticker": ticker,
        }
    return out


def fetch_yahoo_fallback(ticker: str, start: str, end: str, retrieved_at: str) -> dict[str, dict]:
    """Download daily OHLCV via yfinance; label every bar YAHOO_FALLBACK."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise SystemExit(
            "yfinance missing. pip install yfinance pandas --break-system-packages\n" + str(e)
        ) from e

    # yfinance end is exclusive; bump one day
    end_excl = (datetime.strptime(end, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
    df = yf.Ticker(ticker).history(start=start, end=end_excl, auto_adjust=False, actions=False)
    out: dict[str, dict] = {}
    if df is None or df.empty:
        return out
    for idx, row in df.iterrows():
        if getattr(idx, "tzinfo", None) is not None:
            date = idx.tz_convert("America/New_York").strftime("%Y-%m-%d")
        else:
            date = str(idx)[:10]
        try:
            o = float(row["Open"])
            h = float(row["High"])
            l = float(row["Low"])
            c = float(row["Close"])
            v = float(row["Volume"]) if "Volume" in row.index else 0.0
        except Exception:
            continue
        if any(x != x for x in (o, h, l, c)):  # NaN check
            continue
        out[date] = {
            "date": date,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
            "source": "YAHOO_FALLBACK",
            "data_asof": date,
            "retrieved_at": retrieved_at,
            "frequency": FREQUENCY,
            "ticker": ticker,
        }
    return out


def merge_bars(
    primary: dict[str, dict],
    yahoo: dict[str, dict],
    anchor: str,
    completed_through: str,
) -> tuple[list[dict], dict]:
    """PRIMARY wins on overlap; YAHOO_FALLBACK fills missing (esp. post-anchor).

    Incomplete current-session bars are kept for audit but excluded from
    post_anchor_* counts used by the resolver readiness gate.
    """
    dates = sorted(set(primary) | set(yahoo))
    merged: list[dict] = []
    counts = {
        "primary_bars": 0,
        "yahoo_fallback_bars": 0,
        "post_anchor_primary": 0,
        "post_anchor_yahoo_fallback": 0,
        "post_anchor_total": 0,
        "incomplete_bars": 0,
    }
    for d in dates:
        if d in primary:
            row = _mark_session_complete(primary[d], completed_through)
            counts["primary_bars"] += 1
            if d > anchor and row.get("session_complete"):
                counts["post_anchor_primary"] += 1
                counts["post_anchor_total"] += 1
        else:
            row = _mark_session_complete(yahoo[d], completed_through)
            counts["yahoo_fallback_bars"] += 1
            if d > anchor and row.get("session_complete"):
                counts["post_anchor_yahoo_fallback"] += 1
                counts["post_anchor_total"] += 1
        if not row.get("session_complete"):
            counts["incomplete_bars"] += 1
        merged.append(row)
    return merged, counts


def main() -> int:
    ap = argparse.ArgumentParser(description="Desk data bridge PRIMARY + YAHOO_FALLBACK")
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--primary-cache", type=Path, default=DEFAULT_PRIMARY)
    ap.add_argument("--anchor", type=str, default=None, help="override maturity_anchor")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    desk = root / "research/forward_v1/desk"
    t0 = desk / T0_DIR
    out_dir = desk / "data_bridge"
    bars_dir = out_dir / "bars"
    bars_dir.mkdir(parents=True, exist_ok=True)

    tickers, t0_anchor = read_t0_tickers(t0)
    anchor = args.anchor or t0_anchor
    want = sorted(set(tickers) | {BENCHMARK})

    now = _utc_now()
    retrieved_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    completed_through = _last_completed_us_session_date(now)
    # fetch window: a few days before anchor through tomorrow (UTC date)
    start = (datetime.strptime(anchor, "%Y-%m-%d").date() - timedelta(days=5)).isoformat()
    end = now.astimezone(ET).date().isoformat()

    per_symbol: dict[str, dict] = {}
    latest_by: dict[str, str | None] = {}
    failures: list[dict] = []

    for ticker in want:
        primary = load_primary_bars(args.primary_cache, ticker)
        yahoo: dict[str, dict] = {}
        yahoo_err = None
        # Always attempt YAHOO_FALLBACK for post-anchor gaps (honest label)
        try:
            yahoo = fetch_yahoo_fallback(ticker, start=start, end=end, retrieved_at=retrieved_at)
        except Exception as e:
            yahoo_err = str(e)
            failures.append({"ticker": ticker, "error": yahoo_err})

        merged, counts = merge_bars(primary, yahoo, anchor, completed_through)
        # Prefer writing bars at/after (anchor - 5d) for resolver use
        write_bars = [b for b in merged if b["date"] >= start]
        complete_bars = [b for b in write_bars if b.get("session_complete")]
        latest = complete_bars[-1]["date"] if complete_bars else None
        latest_raw = write_bars[-1]["date"] if write_bars else None
        latest_by[ticker] = latest
        post_anchor_dates = sorted(
            b["date"] for b in write_bars if b["date"] > anchor and b.get("session_complete")
        )

        payload = {
            "schema": "DESK_DATA_BRIDGE_BARS.v1",
            "ticker": ticker,
            "evaluation_clock": EVAL_CLOCK,
            "maturity_anchor": anchor,
            "frequency": FREQUENCY,
            "retrieved_at": retrieved_at,
            "primary_cache": str(args.primary_cache),
            "primary_available": bool(primary),
            "yahoo_fallback_attempted": True,
            "yahoo_fallback_error": yahoo_err,
            "latest_bar": latest,
            "latest_bar_raw_including_incomplete": latest_raw,
            "last_completed_us_session": completed_through,
            "post_anchor_trading_days": len(post_anchor_dates),
            "post_anchor_dates": post_anchor_dates,
            "bar_counts": counts,
            "bars": write_bars,
            "label_policy": {
                "PRIMARY": "juniper-kite live cache bar",
                "YAHOO_FALLBACK": "yfinance daily; NEVER ORIGINAL_LIVE",
                "forbidden": ["ORIGINAL_LIVE for yahoo rows", "invented prices"],
            },
        }
        path = bars_dir / f"{ticker}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        per_symbol[ticker] = {
            "path": str(path.relative_to(root)),
            "latest_bar": latest,
            "post_anchor_trading_days": len(post_anchor_dates),
            "post_anchor_dates": post_anchor_dates,
            "primary_bars": counts["primary_bars"],
            "yahoo_fallback_bars": counts["yahoo_fallback_bars"],
            "post_anchor_primary": counts["post_anchor_primary"],
            "post_anchor_yahoo_fallback": counts["post_anchor_yahoo_fallback"],
            "yahoo_fallback_error": yahoo_err,
        }
        print(
            f"{ticker}: latest_complete={latest} raw={latest_raw} post_anchor={len(post_anchor_dates)} "
            f"primary={counts['primary_bars']} yahoo_fb={counts['yahoo_fallback_bars']} "
            f"incomplete={counts['incomplete_bars']}"
        )

    latest_all = [d for d in latest_by.values() if d]
    calendar_latest = max(latest_all) if latest_all else None
    # QQQ post-anchor days as trading calendar proxy
    qqq_post = per_symbol.get(BENCHMARK, {}).get("post_anchor_trading_days", 0) or 0
    min_post = min(
        (per_symbol[t]["post_anchor_trading_days"] for t in tickers if t in per_symbol),
        default=0,
    )

    if calendar_latest and calendar_latest >= anchor:
        # FRESH through latest available; may still be WAITING for 5D
        data_status = "DATA_FRESH"
        if calendar_latest == anchor and qqq_post == 0:
            note = (
                f"bridge FRESH through {calendar_latest}=maturity_anchor; "
                "post_anchor_trading_days=0 — resolver must WAITING_FOR_FUTURE_BARS "
                "(resolved_5d=0 OK until ≥5 trading days after anchor)"
            )
        else:
            note = (
                f"bridge FRESH through {calendar_latest}; "
                f"qqq_post_anchor_days={qqq_post} min_ticker_post={min_post}"
            )
    else:
        data_status = "DATA_STALE"
        note = "no bars at/after maturity_anchor"

    status = {
        "schema": "DATA_BRIDGE_STATUS.v1",
        "node": NODE,
        "app_id": APP_ID,
        "hub_name": "信股慣性台",
        "evaluation_clock": EVAL_CLOCK,
        "minimum_run": "V1.2",
        "checked_at_utc": retrieved_at,
        "checked_at_hkt": now.astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "maturity_anchor": anchor,
        "last_completed_us_session": completed_through,
        "t0_path": f"research/forward_v1/desk/{T0_DIR}/",
        "t0_immutable": True,
        "tickers": tickers,
        "benchmark": BENCHMARK,
        "symbols": want,
        "primary_cache": str(args.primary_cache),
        "primary_exists": args.primary_cache.exists(),
        "yahoo_fallback": {
            "provider": "yfinance",
            "source_label": "YAHOO_FALLBACK",
            "never": "ORIGINAL_LIVE",
            "frequency": FREQUENCY,
            "retrieved_at": retrieved_at,
            "window_start": start,
            "window_end": end,
        },
        "latest_bar": calendar_latest,
        "latest_bar_by_symbol": latest_by,
        "post_anchor_trading_days_qqq": qqq_post,
        "post_anchor_trading_days_min_t0_tickers": min_post,
        "status": data_status,
        "resolver_implication": (
            "READY_TO_RESOLVE_5D" if min_post >= 5 and qqq_post >= 5 else "WAITING_FOR_FUTURE_BARS"
        ),
        "note": note,
        "failures": failures,
        "per_symbol": per_symbol,
        "hard_locks": [
            "never rewrite T0",
            "never invent prices",
            "YAHOO_FALLBACK ≠ ORIGINAL_LIVE",
            "book_ADD ≠ MARK_BUY",
            "LIVE_FORWARD ≠ REPLAY_FORWARD win-rate",
        ],
    }
    status_path = out_dir / "DATA_BRIDGE_STATUS.json"
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": data_status, "latest_bar": calendar_latest, "qqq_post": qqq_post, "min_post": min_post, "implication": status["resolver_implication"]}, indent=2))
    print("wrote", status_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
