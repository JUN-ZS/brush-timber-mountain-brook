"""Cell 11 — OpenD option-chain fallback after Yahoo SOURCE_DOWN.

Cascade (via providers.option_candidate_fetch):
  1. Yahoo LIVE -> PASS (select candidate)
  2. OpenD LIVE after Yahoo down -> PASS (select candidate)
  3. BLOCKED_NO_OPEND after Yahoo down -> PASS (honest; expected on CI)
  4. OPTIONS_SOURCE_DOWN from both -> PASS (honest)

Assert never invents candidate strikes when not LIVE; currentLeg always null.
Does not change Decision/Build. No broker orders, no Ledger writes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from providers.option_candidate_fetch import fetch_option_candidate

CELL = "11_OPEND_OPTION_FALLBACK"
SELECT_JS = HERE / "cell10_select_candidate.js"


def _select_candidate(calls: list, spot: float, target_dte: int = 45) -> dict | None:
    payload = {
        "calls": calls,
        "spot": spot,
        "targetDelta": 0.10,
        "targetDte": target_dte,
        "asOf": None,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(payload, fh)
        tmp = Path(fh.name)
    try:
        proc = subprocess.run(
            ["node", str(SELECT_JS), str(tmp)],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(HERE),
        )
        out = json.loads(proc.stdout)
        return out.get("candidate")
    finally:
        tmp.unlink(missing_ok=True)


def main() -> int:
    fetched = fetch_option_candidate("QQQ", target_dte=45)
    status = fetched.get("status")
    source = fetched.get("source")
    path = fetched.get("path") or status

    # Never invent strikes when not LIVE
    if not fetched.get("ok"):
        assert status in {"BLOCKED_NO_OPEND", "OPTIONS_SOURCE_DOWN"}, fetched
        assert fetched.get("candidate") is None, fetched
        assert fetched.get("calls") == [] or fetched.get("calls") is None, fetched
        # currentLeg must be null / absent-as-null in cell output
        assert fetched.get("currentLeg") in (None,), {
            k: fetched.get(k) for k in ("currentLeg", "status", "source")
        }
        assert not any(
            k in fetched
            for k in ("shortStrike", "longStrike", "qqqDte", "vxxDte")
        ), fetched

        reason = (
            "BLOCKED_NO_OPEND"
            if status == "BLOCKED_NO_OPEND"
            else "SOURCE_DOWN"
        )
        print(
            json.dumps(
                {
                    "cell": CELL,
                    "ok": False,
                    "status": status,
                    "source": source,
                    "path": path,
                    "symbol": fetched.get("symbol"),
                    "error": fetched.get("error"),
                    "fallback_from": fetched.get("fallback_from"),
                    "prior_error": fetched.get("prior_error"),
                    "opend_error": fetched.get("opend_error"),
                    "calls": [],
                    "candidate": None,
                    "currentLeg": None,
                    "reason": reason,
                    "PASS": True,
                },
                ensure_ascii=False,
            )
        )
        return 0

    # LIVE from YAHOO_OPTIONS or OPEND_OPTIONS
    assert status == "LIVE", fetched
    assert source in {"YAHOO_OPTIONS", "OPEND_OPTIONS"}, fetched
    calls = fetched.get("calls") or []
    assert isinstance(calls, list) and len(calls) > 0, "LIVE requires non-empty calls"
    spot = fetched.get("spot")
    assert spot is not None and float(spot) > 0, f"LIVE requires spot, got {spot!r}"

    candidate = _select_candidate(calls, float(spot), int(fetched.get("target_dte") or 45))
    assert candidate is not None, "candidateFromChain returned null on non-empty LIVE chain"
    assert candidate.get("shortStrike") is not None, candidate
    assert candidate.get("longStrike") is not None, candidate
    assert candidate.get("dte") is not None, candidate
    assert (
        candidate.get("delta") is not None
        or candidate.get("credit") is not None
        or candidate.get("sizingAvailable") is True
    ), candidate
    assert "currentLeg" not in candidate, candidate

    out = {
        "cell": CELL,
        "ok": True,
        "status": "LIVE",
        "source": source,
        "path": path,
        "symbol": fetched.get("symbol"),
        "expiry": fetched.get("expiry"),
        "spot": spot,
        "calls_count": len(calls),
        "fallback_from": fetched.get("fallback_from"),
        "prior_error": fetched.get("prior_error"),
        "candidate": {
            "shortStrike": candidate.get("shortStrike"),
            "longStrike": candidate.get("longStrike"),
            "dte": candidate.get("dte"),
            "delta": candidate.get("delta"),
            "credit": candidate.get("credit"),
            "sizingAvailable": candidate.get("sizingAvailable"),
            "expiration": candidate.get("expiration"),
            "source": candidate.get("source"),
            "retrievalSource": source,
        },
        "currentLeg": None,
        "reason": "LIVE",
        "PASS": True,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
