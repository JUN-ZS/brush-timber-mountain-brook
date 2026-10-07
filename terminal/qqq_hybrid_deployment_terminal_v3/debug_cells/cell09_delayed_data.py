from __future__ import annotations

import datetime as dt
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from providers.cboe_delayed_vx import fetch

STANDARD = re.compile(r"^VX/[FGHJKMNQUVXZ]\d{1,2}$")


def main() -> int:
    x = fetch(allow_last=False)
    assert x.get("ok") is True, x
    assert x["status"] == "LIVE_DELAYED", x
    assert x["source"] == "CBOE_PUBLIC_DELAYED_VX", x

    m1, m2 = x["m1"], x["m2"]
    assert STANDARD.fullmatch(m1["symbol"]), m1
    assert STANDARD.fullmatch(m2["symbol"]), m2
    assert m1["expiry"] < m2["expiry"], (m1, m2)
    assert m1["expiry"] > x["data_asof"], (m1, x["data_asof"])
    assert m2["expiry"] > x["data_asof"], (m2, x["data_asof"])
    assert m1["price_basis"] == "settlement", m1
    assert m2["price_basis"] == "settlement", m2
    assert m1["price"] > 0 and m2["price"] > 0, (m1, m2)
    assert x["candidate_count"] >= 2, x

    expected = (m2["price"] - m1["price"]) / m1["price"]
    assert math.isclose(x["term_slope"], expected, rel_tol=1e-12, abs_tol=1e-12), x
    expected_state = "CONTANGO" if expected > 0 else ("BACKWARDATION" if expected < 0 else "FLAT")
    assert x["term_state"] == expected_state, x

    # Cboe adapter must never silently substitute a non-standard VX family.
    assert not any(token in m1["symbol"] + m2["symbol"] for token in ("VXM", "VXMT", "TAS", "VX40", "VX41")), (m1, m2)

    print({
        "cell": "09_DELAYED_DATA",
        "source": x["source"],
        "data_asof": x["data_asof"],
        "m1": {k: m1[k] for k in ("symbol", "expiry", "price", "price_basis")},
        "m2": {k: m2[k] for k in ("symbol", "expiry", "price", "price_basis")},
        "term_slope_pct": round(x["term_slope"] * 100, 6),
        "term_state": x["term_state"],
        "candidate_count": x["candidate_count"],
        "PASS": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
