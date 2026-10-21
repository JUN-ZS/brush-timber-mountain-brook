"""Option-candidate cascade: Yahoo first, then OpenD fallback.

Priority for option chain:
  1. Yahoo (providers.yahoo_options)
  2. OpenD option chain when Yahoo down (providers.opend_options)
  3. Else OPTIONS_SOURCE_DOWN / BLOCKED_NO_OPEND (honest)

Never invents strikes. Candidate ≠ Current Leg.
"""

from __future__ import annotations

from typing import Any

from providers.yahoo_options import fetch_option_chain as fetch_yahoo
from providers.opend_options import fetch_option_chain as fetch_opend


def fetch_option_candidate(
    symbol: str = "QQQ",
    target_dte: int = 45,
) -> dict[str, Any]:
    """Cascade: Yahoo LIVE → return; else OpenD; else aggregate fail-soft."""
    yahoo = fetch_yahoo(symbol=symbol, target_dte=target_dte)
    if yahoo.get("ok") and yahoo.get("status") == "LIVE":
        out = dict(yahoo)
        out["path"] = "YAHOO_OPTIONS"
        out["fallback_from"] = None
        return out

    yahoo_err = {
        "ok": yahoo.get("ok"),
        "status": yahoo.get("status"),
        "source": yahoo.get("source"),
        "error": yahoo.get("error"),
    }

    opend = fetch_opend(symbol=symbol, target_dte=target_dte)
    if opend.get("ok") and opend.get("status") == "LIVE":
        out = dict(opend)
        out["path"] = "OPEND_OPTIONS"
        out["fallback_from"] = "YAHOO_OPTIONS"
        out["prior_error"] = yahoo_err
        return out

    # Aggregate fail-soft: prefer BLOCKED_NO_OPEND when OpenD unavailable/not entitled
    # after Yahoo is already down; else OPTIONS_SOURCE_DOWN with both errors.
    opend_status = opend.get("status") or "OPTIONS_SOURCE_DOWN"
    if opend_status == "BLOCKED_NO_OPEND":
        status = "BLOCKED_NO_OPEND"
        source = "OPEND_OPTIONS"
        error = opend.get("error") or "OpenD unavailable"
    else:
        status = "OPTIONS_SOURCE_DOWN"
        source = "OPTIONS_CASCADE"
        error = (
            f"yahoo={yahoo.get('error')!s}; opend={opend.get('error')!s}"
        )

    return {
        "ok": False,
        "status": status,
        "source": source,
        "symbol": str(symbol or "").strip().upper() or "QQQ",
        "error": error,
        "calls": [],
        "candidate": None,
        "currentLeg": None,
        "expiry": None,
        "spot": None,
        "path": status,
        "fallback_from": "YAHOO_OPTIONS",
        "prior_error": yahoo_err,
        "opend_error": {
            "ok": opend.get("ok"),
            "status": opend.get("status"),
            "source": opend.get("source"),
            "error": opend.get("error"),
        },
        "retrieved_at": opend.get("retrieved_at") or yahoo.get("retrieved_at"),
        "target_dte": target_dte,
    }


if __name__ == "__main__":
    import pprint
    import sys

    out = fetch_option_candidate(sys.argv[1] if len(sys.argv) > 1 else "QQQ")
    if out.get("ok"):
        pprint.pp({**out, "calls": f"<{len(out.get('calls') or [])} calls>"})
    else:
        pprint.pp(out)
