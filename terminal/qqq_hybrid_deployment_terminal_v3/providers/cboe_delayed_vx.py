
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


NY = ZoneInfo("America/New_York")


def payload_asof(payload):
    """F2: observation date of the term structure = payload lastUpdate as a New York calendar date.

    The Cboe VX payload has one timestamp, top-level ``lastUpdate`` (e.g.
    ``2026-10-07T17:05:19.411998-05:00``); rows carry no trade/settlement date.
    Only an ISO datetime WITH an explicit offset (or ``Z``) is accepted. Missing or
    unparseable -> (None, status): never fall back to the fetch clock.
    """
    raw = payload.get("lastUpdate") if isinstance(payload, dict) else None
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, "MISSING_LAST_UPDATE", raw
    if not isinstance(raw, str):
        return None, "UNPARSEABLE_LAST_UPDATE", raw
    text = raw.strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = dt.datetime.fromisoformat(text)
    except ValueError:
        return None, "UNPARSEABLE_LAST_UPDATE", raw
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        return None, "UNPARSEABLE_LAST_UPDATE", raw
    return stamp.astimezone(NY).date().isoformat(), "PAYLOAD_LAST_UPDATE", raw


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


def fetch(allow_last: bool = False, now: dt.datetime | None = None) -> dict:
    req = urllib.request.Request(
        API,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        payload = json.loads(r.read().decode("utf-8"))

    now = now or dt.datetime.now(dt.timezone.utc)
    # fetch clock: only used to skip already-expired contracts and for display (fetched_at).
    ny_date = now.astimezone(NY).date()
    # F2: data_asof comes from the payload, never from the fetch clock.
    data_asof, asof_status, last_update_raw = payload_asof(payload)
    dating = {
        "data_asof": data_asof,
        "asof_status": asof_status,
        "last_update": last_update_raw,
        "fetched_at": now.isoformat(),
        "asof_utc": now.isoformat(),  # legacy alias of fetched_at (fetch time, NOT data time)
    }
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
            **dating,
        }

    m1, m2 = candidates[0], candidates[1]
    slope = (m2["price"] - m1["price"]) / m1["price"]

    return {
        "ok": True,
        # UNDATED: values are usable but their date is unproven -> engine F1 gate blocks (TERM DATE INVALID).
        "status": "LIVE_DELAYED" if data_asof else "UNDATED_PAYLOAD",
        "source": "CBOE_PUBLIC_DELAYED_VX",
        "official_page": OFFICIAL_PAGE,
        "api": API,
        **dating,
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
