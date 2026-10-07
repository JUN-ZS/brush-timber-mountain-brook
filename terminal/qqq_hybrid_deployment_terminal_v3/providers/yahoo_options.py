"""Yahoo Finance option-chain retrieval for QQQ / VXX (read-only).

Contract:
  success -> {ok:True, status:"LIVE", source:"YAHOO_OPTIONS", ...}
  failure -> {ok:False, status:"OPTIONS_SOURCE_DOWN", ..., calls:[], candidate:null}

Never invents strikes. Used by /api/options and Cell 10.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

SOURCE = "YAHOO_OPTIONS"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 QQQ-Hybrid-V3"
ALLOWED = frozenset({"QQQ", "VXX"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(v: Any):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def _down(symbol: str, error: str) -> dict:
    return {
        "ok": False,
        "status": "OPTIONS_SOURCE_DOWN",
        "source": SOURCE,
        "symbol": symbol,
        "error": error,
        "calls": [],
        "candidate": None,
        "expiry": None,
        "spot": None,
        "retrieved_at": _now_iso(),
    }


def fetch_option_chain(
    symbol: str = "QQQ",
    target_dte: int = 45,
    timeout: float = 10.0,
) -> dict:
    """Fetch call chain near target_dte from Yahoo query2 options API."""
    sym = str(symbol or "").strip().upper()
    if sym not in ALLOWED:
        return _down(sym or "QQQ", "symbol must be QQQ or VXX")

    try:
        dte = max(14, min(120, int(float(target_dte))))
    except (TypeError, ValueError):
        dte = 45

    base_url = (
        "https://query2.finance.yahoo.com/v7/finance/options/"
        + urllib.parse.quote(sym, safe="")
    )
    ctx = ssl.create_default_context()

    try:
        req = urllib.request.Request(base_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            root = json.load(response)
        result = (root.get("optionChain") or {}).get("result") or []
        if not result:
            return _down(sym, "Yahoo option chain result unavailable")

        meta = result[0]
        quote = meta.get("quote") or {}
        spot = _num(quote.get("regularMarketPrice"))
        expirations = [
            int(x) for x in (meta.get("expirationDates") or []) if _num(x) is not None
        ]
        now_ts = datetime.now(timezone.utc).timestamp()
        expiry_ts = (
            min(expirations, key=lambda x: abs((x - now_ts) / 86400 - dte))
            if expirations
            else None
        )

        url = base_url + (("?date=" + str(expiry_ts)) if expiry_ts is not None else "")
        req2 = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req2, timeout=timeout, context=ctx) as response:
            payload = json.load(response)
        result2 = (payload.get("optionChain") or {}).get("result") or []
        if not result2:
            return _down(sym, "Yahoo option expiry result unavailable")

        meta2 = result2[0]
        if spot is None:
            spot = _num((meta2.get("quote") or {}).get("regularMarketPrice"))
        opts = meta2.get("options") or []
        calls = opts[0].get("calls") if opts else []
        if not isinstance(calls, list):
            calls = []

        expiry_iso = (
            datetime.fromtimestamp(expiry_ts, timezone.utc).date().isoformat()
            if expiry_ts is not None
            else None
        )
        return {
            "ok": True,
            "status": "LIVE",
            "source": SOURCE,
            "symbol": sym,
            "target_dte": dte,
            "expiry": expiry_iso,
            "spot": spot,
            "calls": calls,
            "candidate": None,
            "retrieved_at": _now_iso(),
        }
    except Exception as exc:
        return _down(sym, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    import pprint
    import sys

    out = fetch_option_chain(sys.argv[1] if len(sys.argv) > 1 else "QQQ")
    pprint.pp(out if not out.get("ok") else {**out, "calls": f"<{len(out['calls'])} calls>"})
