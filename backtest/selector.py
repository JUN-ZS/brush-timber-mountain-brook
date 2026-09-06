"""Pick a protection structure from LIVE puts only.

Without LIVE bid>0 contracts the selector returns NOT_AVAILABLE.
It does not fall back to Black-Scholes and pretend the pick is live.
"""

from __future__ import annotations

from typing import Any, Optional

from .types import OptionContract


def _score(c: OptionContract, spot: float, regime: str) -> Optional[float]:
    if c.source != "LIVE QUOTE":
        return None
    if c.right != "PUT":
        return None
    if c.bid is None or c.bid <= 0:
        return None
    if c.strike is None or spot <= 0:
        return None
    dte = c.dte
    if dte is None or dte < 14 or dte > 60:
        return None
    otm = 1.0 - c.strike / spot
    if otm < 0.015 or otm > 0.10:
        return None
    spread = c.spread_pct
    if spread is None:
        spread = 0.25
    # Prefer 21-45 DTE, 2-8% OTM, tighter spread. Do not hard-wire a hedge %.
    dte_pen = abs((dte or 30) - 30) / 30.0
    otm_target = {"CALM": 0.05, "UNSTABLE": 0.03, "TAIL": 0.02, "RECOVERY": 0.05}.get(regime, 0.05)
    otm_pen = abs(otm - otm_target) / 0.05
    return -(spread * 4.0 + dte_pen + otm_pen)


def select_structure(
    contracts: list[OptionContract],
    *,
    spot: Optional[float],
    regime: str = "CALM",
    building: bool = False,
) -> dict[str, Any]:
    why_neg: list[str] = []
    if spot is None or spot <= 0:
        return {
            "status": "NOT_AVAILABLE",
            "structure": None,
            "reason": "no LIVE underlying spot; selector refuses to guess",
            "why": ["spot UNAVAILABLE"],
        }
    live = [c for c in contracts if c.source == "LIVE QUOTE"]
    if not live:
        return {
            "status": "NOT_AVAILABLE",
            "structure": None,
            "reason": "no LIVE option quotes — refusing SYNTHETIC/DERIVED as a selected hedge",
            "why": ["option quotes are not LIVE QUOTE"],
        }
    ranked: list[tuple[float, OptionContract]] = []
    for c in live:
        s = _score(c, spot, regime)
        if s is None:
            continue
        ranked.append((s, c))
    if not ranked:
        why_neg.append("no put with DTE 14-60, OTM 1.5-10%, bid>0")
        return {
            "status": "NOT_AVAILABLE",
            "structure": None,
            "reason": "LIVE chain present but no contract passed the first-stage liquidity/DTE/OTM filter",
            "why": why_neg,
        }
    ranked.sort(key=lambda t: t[0], reverse=True)
    best = ranked[0][1]
    otm = 1.0 - (best.strike or 0) / spot
    why = [
        f"STATE = {regime}" + (" + BUILDING" if building else ""),
        f"DTE = {best.dte} (prefer 21-45)",
        f"OTM = {otm:.2%} (prefer 2-8%)",
        f"bid = {best.bid} ask = {best.ask} spread = {best.spread_pct}",
        "liquidity filter: bid>0",
        "protection compared only among LIVE puts; DERIVED BS was not allowed to win",
    ]
    return {
        "status": "AVAILABLE",
        "structure": {
            "kind": "OTM_PUT",
            "code": best.code,
            "strike": best.strike,
            "dte": best.dte,
            "delta": best.delta,
            "iv": best.iv,
            "bid": best.bid,
            "ask": best.ask,
            "mid": best.mid,
            "spread_pct": best.spread_pct,
            "oi": best.oi,
            "source": "LIVE QUOTE",
        },
        "reason": "best LIVE put under the first-stage filter (not an order)",
        "why": why,
        "alternatives": [c.code for _, c in ranked[1:4]],
    }
