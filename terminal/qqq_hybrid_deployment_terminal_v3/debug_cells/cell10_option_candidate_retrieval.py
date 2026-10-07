"""Cell 10 — REAL option-candidate retrieval (fail-soft).

PASS paths (either OK for CI — do not flake):
  A) LIVE: Yahoo returns non-empty calls -> select via engine candidateFromChain;
     assert candidate fields; currentLeg is null (Candidate ≠ Current Leg).
  B) OPTIONS_SOURCE_DOWN: ok=false, candidate=null, status exact, no fabricated strikes;
     still PASS with reason SOURCE_DOWN.

Does not change Decision/Build policy. Does not auto-fill Current Leg from Candidate.
No OpenD, no broker orders, no Ledger writes.
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
from providers.yahoo_options import fetch_option_chain

CELL = "10_OPTION_CANDIDATE_RETRIEVAL"
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
    fetched = fetch_option_chain("QQQ", target_dte=45)

    # Path B — honest source down (PASS)
    if not fetched.get("ok"):
        assert fetched.get("status") == "OPTIONS_SOURCE_DOWN", fetched
        assert fetched.get("source") == "YAHOO_OPTIONS", fetched
        assert fetched.get("candidate") is None, fetched
        assert fetched.get("calls") == [], fetched
        assert not any(
            k in fetched for k in ("shortStrike", "longStrike", "currentLeg", "qqqDte", "vxxDte")
        ), fetched
        print(
            json.dumps(
                {
                    "cell": CELL,
                    "ok": False,
                    "status": "OPTIONS_SOURCE_DOWN",
                    "source": fetched.get("source"),
                    "symbol": fetched.get("symbol"),
                    "error": fetched.get("error"),
                    "calls": [],
                    "candidate": None,
                    "currentLeg": None,
                    "reason": "SOURCE_DOWN",
                    "PASS": True,
                },
                ensure_ascii=False,
            )
        )
        return 0

    # Path A — LIVE retrieval + engine selection
    assert fetched.get("status") == "LIVE", fetched
    assert fetched.get("source") == "YAHOO_OPTIONS", fetched
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
    # Tag retrieval provenance on the output object (engine uses YAHOO_OPTIONS_ESTIMATE)
    retrieval_source = "YAHOO_OPTIONS"
    assert "currentLeg" not in candidate, candidate

    out = {
        "cell": CELL,
        "ok": True,
        "status": "LIVE",
        "source": retrieval_source,
        "symbol": fetched.get("symbol"),
        "expiry": fetched.get("expiry"),
        "spot": spot,
        "calls_count": len(calls),
        "candidate": {
            "shortStrike": candidate.get("shortStrike"),
            "longStrike": candidate.get("longStrike"),
            "dte": candidate.get("dte"),
            "delta": candidate.get("delta"),
            "credit": candidate.get("credit"),
            "sizingAvailable": candidate.get("sizingAvailable"),
            "expiration": candidate.get("expiration"),
            "source": candidate.get("source"),
            "retrievalSource": retrieval_source,
        },
        "currentLeg": None,
        "reason": "LIVE",
        "PASS": True,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
