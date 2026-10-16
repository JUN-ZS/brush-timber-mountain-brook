
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

API = "https://www-api.cboe.com/us/futures/api/data/?symbol=VX"
OFFICIAL_PAGE = "https://www.cboe.com/delayed_quotes/vx/future_quotes/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 QQQ-Hybrid-V3"
STANDARD = re.compile(r"^VX/([FGHJKMNQUVXZ])(\d{1,2})$")


def _num(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def _date(v):
    s = str(v or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _rows(payload):
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload.get("data"), dict):
            for k in ("data", "futures", "contracts", "items"):
                if isinstance(payload["data"].get(k), list):
                    return payload["data"][k]
        for k in ("futures", "contracts", "items"):
            if isinstance(payload.get(k), list):
                return payload[k]
    raise ValueError("Unrecognized Cboe delayed VX payload shape")


def _price(row, allow_last):
    settle = _num(row.get("settlement"))
    if settle is not None and settle > 0:
        return settle, "settlement"
    if allow_last:
        last = _num(row.get("last_price"))
        if last is not None and last > 0:
            return last, "last"
    return None, None


def fetch(allow_last: bool = False) -> dict:
    req = urllib.request.Request(
        API,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        payload = json.loads(r.read().decode("utf-8"))

    now = dt.datetime.now(dt.timezone.utc)
    ny_date = now.astimezone(ZoneInfo("America/New_York")).date()
    candidates = []

    for row in _rows(payload):
        symbol = str(row.get("symbol") or row.get("symbol_id") or "").strip().upper()
        if not STANDARD.fullmatch(symbol):
            continue
        expiry = _date(row.get("expiration"))
        if expiry is None or expiry <= ny_date:
            continue
        px, basis = _price(row, allow_last)
        if px is None:
            continue
        candidates.append(
            {
                "symbol": symbol,
                "expiry": expiry.isoformat(),
                "price": px,
                "price_basis": basis,
                "last_price": _num(row.get("last_price")),
                "settlement": _num(row.get("settlement")),
                "prev_close": _num(row.get("prev_close")),
                "volume": _num(row.get("volume")),
                "open_interest": _num(row.get("prev_open_int") or row.get("open_interest")),
            }
        )

    candidates.sort(key=lambda x: x["expiry"])
    if len(candidates) < 2:
        return {
            "ok": False,
            "status": "BLOCKED",
            "source": "CBOE_PUBLIC_DELAYED_VX",
            "official_page": OFFICIAL_PAGE,
            "api": API,
            "reason": "fewer than two usable standard monthly VX contracts",
            "asof_utc": now.isoformat(),
            "data_asof": ny_date.isoformat(),
        }

    m1, m2 = candidates[0], candidates[1]
    slope = (m2["price"] - m1["price"]) / m1["price"]

    return {
        "ok": True,
        "status": "LIVE_DELAYED",
        "source": "CBOE_PUBLIC_DELAYED_VX",
        "official_page": OFFICIAL_PAGE,
        "api": API,
        "asof_utc": now.isoformat(),
        "data_asof": ny_date.isoformat(),
        "m1": m1,
        "m2": m2,
        "term_slope": slope,
        "term_state": "CONTANGO" if slope > 0 else ("BACKWARDATION" if slope < 0 else "FLAT"),
        "candidate_count": len(candidates),
    }


def main() -> int:
    try:
        result = fetch()
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
        result = {
            "ok": False,
            "status": "ERROR",
            "source": "CBOE_PUBLIC_DELAYED_VX",
            "api": API,
            "reason": f"{type(exc).__name__}: {exc}",
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
