"""Live state / risk engines. Same regime rules as V2.2, live or derived bars."""

from __future__ import annotations

import math
from typing import Any, Optional

from .universe import DAYS, closes, last_close, last_date, load_universe, momentum, realized_vol, stdev

Regime = str  # CALM | UNSTABLE | TAIL | RECOVERY


def _stdev_rets(prices: list[float], n: int) -> float:
    if len(prices) < n + 1:
        return 0.0
    sl = prices[-(n + 1) :]
    rets = []
    for i in range(1, len(sl)):
        if sl[i - 1] > 0:
            rets.append(sl[i] / sl[i - 1] - 1.0)
    return stdev(rets) * math.sqrt(DAYS) if len(rets) >= 2 else 0.0


def classify_state(
    qqq: list[float],
    vix: Optional[float],
    vix_prev5: Optional[float] = None,
) -> dict[str, Any]:
    vol = _stdev_rets(qqq, 20)
    vol5 = _stdev_rets(qqq, 5)
    p20 = momentum(qqq, 20) or 0.0
    p60 = momentum(qqq, 60) or 0.0
    mom5 = momentum(qqq, 5) or 0.0
    vix_accel = (vix - vix_prev5) if (vix is not None and vix_prev5 is not None) else None
    tail = (vix is not None and vix >= 30) or vol >= 0.38 or p20 <= -0.08
    unstable = (vix is not None and vix >= 20) or vol >= 0.25 or p20 < 0
    recovery = p20 > 0 and p60 < 0
    regime: Regime = "TAIL" if tail else "RECOVERY" if recovery else "UNSTABLE" if unstable else "CALM"
    building = (
        (not tail)
        and vix is not None
        and vix >= 18
        and mom5 < 0
        and ((vol5 > vol * 1.15 and vol5 >= 0.18) or (vix_accel is not None and vix_accel >= 2) or vol5 >= 0.28)
    )
    q_ret = None
    if len(qqq) >= 2 and qqq[-2] > 0:
        q_ret = qqq[-1] / qqq[-2] - 1.0
    return {
        "regime": regime,
        "building": bool(building),
        "vol": vol,
        "vol5": vol5,
        "vix": vix,
        "vix_accel": vix_accel,
        "dd20": p20,
        "mom60": p60,
        "mom5": mom5,
        "qqq_return": q_ret,
        "realized_vol": vol,
        "momentum_20d": p20,
        "momentum_60d": p60,
    }


def suggested_risk(state: dict[str, Any]) -> dict[str, Any]:
    """Suggested overlay. Not a frozen V2.2 spec and not a live fill."""
    regime = state.get("regime") or "CALM"
    building = bool(state.get("building"))
    qqq_exposure = 1.0  # V2.2 first-wave freeze: QQQ controller independent, held at 100%
    table = {
        "CALM": 0.25,
        "UNSTABLE": 0.50,
        "TAIL": 0.75,
        "RECOVERY": 0.25,
    }
    put = table.get(regime, 0.25)
    if building:
        put = max(put, 0.75)
    return {
        "qqq_exposure": qqq_exposure,
        "put_hedge": put,
        "target_hedge": put,
        "risk_budget": qqq_exposure,
        "dd_brake": None,
        "convexity_mode": "PUT_OVERLAY",
        "building": building,
        "regime": regime,
        "note": (
            "Suggested live overlay, not a V2.2 frozen spec and not an order. "
            "V2.2 first wave held QQQ at 100% and searched put size; that search FAIL "
            "does not prove live IV cannot change the result."
        ),
        "source": "DERIVED",
    }


def run_state_risk(
    *,
    live_qqq_closes: Optional[list[float]] = None,
    live_vix: Optional[float] = None,
    live_vix_closes: Optional[list[float]] = None,
    live_qqq_source: str = "UNAVAILABLE",
    live_vix_source: str = "UNAVAILABLE",
) -> dict[str, Any]:
    u = load_universe()
    source = "LIVE QUOTE"
    reason = None
    qqq = list(live_qqq_closes or [])
    if len(qqq) < 25:
        qqq = closes("QQQ", 80, u)
        source = "DERIVED"
        reason = "live daily closes unavailable; using V2.2 EOD universe (yahoo adjclose)"
    vix = live_vix
    vix_src = live_vix_source
    if vix is None:
        vix = last_close("VIX", u)
        vix_src = "DERIVED"
    vix_prev5 = None
    vhist = list(live_vix_closes or [])
    if len(vhist) >= 6:
        vix_prev5 = vhist[-6]
    else:
        vh = closes("VIX", 10, u)
        if len(vh) >= 6:
            vix_prev5 = vh[-6]
    st = classify_state(qqq, vix, vix_prev5)
    st["source"] = source
    st["vix_source"] = vix_src
    st["qqq_source"] = live_qqq_source if live_qqq_source == "LIVE QUOTE" and source == "LIVE QUOTE" else source
    st["asof"] = last_date(u) if source == "DERIVED" else "live"
    st["reason"] = reason
    risk = suggested_risk(st)
    risk["state_source"] = st["source"]
    return {"state": st, "risk": risk}
