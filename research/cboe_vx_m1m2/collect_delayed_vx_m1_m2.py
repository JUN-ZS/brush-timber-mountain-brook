#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

API = "https://www-api.cboe.com/us/futures/api/data/?symbol=VX"
PAGE = "https://www.cboe.com/delayed_quotes/vx/future_quotes/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Cboe-VX-delayed-research"
STANDARD_RE = re.compile(r"^VX/([FGHJKMNQUVXZ])(\\d{1,2})$")

def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def num(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None

def parse_expiry(v: str) -> dt.date | None:
    s = str(v or "").strip()
    for f in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None

def flatten(payload):
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload.get("data"), dict):
            for k in ("data","futures","contracts","items"):
                if isinstance(payload["data"].get(k), list):
                    return payload["data"][k]
        for k in ("futures","contracts","items"):
            if isinstance(payload.get(k), list):
                return payload[k]
    raise ValueError("Unrecognized Cboe VX futures JSON shape")

def standard_monthly(row):
    sym = str(row.get("symbol") or row.get("symbol_id") or "").strip()
    return bool(STANDARD_RE.fullmatch(sym))

def price(row, allow_last):
    settle = num(row.get("settlement"))
    if settle is not None and settle > 0:
        return settle, "settlement"
    if allow_last:
        last = num(row.get("last_price"))
        if last is not None and last > 0:
            return last, "last_price"
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-last", action="store_true", help="Fallback to delayed last price when settlement is unavailable.")
    ap.add_argument("--api", default=API)
    a = ap.parse_args()

    payload = get_json(a.api)
    rows = flatten(payload)
    now_utc = dt.datetime.now(dt.timezone.utc)
    ny_today = now_utc.astimezone(ZoneInfo("America/New_York")).date()
    candidates = []
    for r in rows:
        if not standard_monthly(r):
            continue
        expiry = parse_expiry(r.get("expiration"))
        if expiry is None or expiry <= ny_today:
            continue
        px, basis = price(r, a.allow_last)
        if px is None:
            continue
        candidates.append({
            "symbol": str(r.get("symbol") or "").strip(),
            "expiration": expiry.isoformat(),
            "price": px,
            "price_basis": basis,
            "last_price": num(r.get("last_price")),
            "settlement": num(r.get("settlement")),
            "prev_close": num(r.get("prev_close")),
            "volume": num(r.get("volume")),
            "open_interest": num(r.get("prev_open_int") or r.get("open_interest")),
        })
    candidates.sort(key=lambda x: x["expiration"])
    if len(candidates) < 2:
        raise SystemExit("FAIL: fewer than two standard monthly VX contracts with usable prices")
    m1, m2 = candidates[0], candidates[1]
    slope = (m2["price"] - m1["price"]) / m1["price"]
    out = {
        "status":"PASS",
        "source":"CBOE_PUBLIC_DELAYED_VX_FUTURES_API",
        "official_page":PAGE,
        "api":a.api,
        "asof_utc":now_utc.isoformat(),
        "signal_date_new_york":ny_today.isoformat(),
        "selection_rule":"standard monthly VX only; exclude weekly numbered VX contracts; expiry > New York data date; sort expiry",
        "price_rule":"settlement preferred" + ("; last_price fallback enabled" if a.allow_last else ""),
        "m1":m1,"m2":m2,"term_slope":slope,
        "term_state":"CONTANGO" if slope > 0 else ("BACKWARDATION" if slope < 0 else "FLAT"),
        "action_hint":"TERM_CARRY" if slope > 0 else ("TERM_REDUCE" if slope < 0 else "TERM_HOLD"),
        "contract_count_after_filter":len(candidates),
    }
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"FAIL: Cboe delayed VX endpoint unavailable: {exc}", file=sys.stderr)
        raise SystemExit(3)
