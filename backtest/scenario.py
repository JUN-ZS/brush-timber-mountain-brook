"""QQQ shock scenarios. LIVE quotes used for entry marks when present; shocked
option values are always DERIVED Black-Scholes because OpenD cannot reprice a
hypothetical spot.
"""

from __future__ import annotations

from typing import Any, Optional

from .bs import bs_price, iv_shock_for_move, norm_iv
from .types import OptionContract

SHOCKS = (-0.01, -0.03, -0.05, -0.10, -0.20)
STRUCTURES = ("QQQ_ONLY", "ATM_PUT", "OTM5_PUT", "PUT_SPREAD")


def _put_mark(spot: float, strike: float, dte: int, iv: float) -> float:
    return bs_price(spot, strike, max(dte, 1) / 365.0, iv, "PUT")


def run_scenarios(
    *,
    spot: Optional[float],
    iv: Optional[float],
    iv_source: str,
    spot_source: str,
    dte: int = 30,
    nav: float = 100_000.0,
    live_puts: Optional[list[OptionContract]] = None,
) -> dict[str, Any]:
    if spot is None or spot <= 0:
        return {
            "status": "UNAVAILABLE",
            "reason": "no spot to shock",
            "rows": [],
            "source": "UNAVAILABLE",
        }
    sig = norm_iv(iv, None)
    if sig is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "no IV (live or VIX). Refusing to silently use 0.25 as LIVE.",
            "rows": [],
            "source": "UNAVAILABLE",
        }
    live_puts = live_puts or []
    shares = nav / spot
    contracts = shares / 100.0
    rows = []
    for shock in SHOCKS:
        new_spot = spot * (1 + shock)
        qqq_pnl = shares * (new_spot - spot)
        iv2 = sig * iv_shock_for_move(shock)
        for kind in STRUCTURES:
            hedge_pnl = 0.0
            entry = None
            exitp = None
            entry_src = "DERIVED"
            if kind == "QQQ_ONLY":
                pass
            elif kind == "ATM_PUT":
                k = round(spot)
                live = _match(live_puts, k, dte)
                entry = live.mid if live and live.mid is not None else _put_mark(spot, k, dte, sig)
                entry_src = "LIVE QUOTE" if live and live.mid is not None else "DERIVED"
                exitp = _put_mark(new_spot, k, max(dte - 1, 1), iv2)
                hedge_pnl = contracts * 100.0 * (exitp - entry)
            elif kind == "OTM5_PUT":
                k = round(spot * 0.95)
                live = _match(live_puts, k, dte)
                entry = live.mid if live and live.mid is not None else _put_mark(spot, k, dte, sig)
                entry_src = "LIVE QUOTE" if live and live.mid is not None else "DERIVED"
                exitp = _put_mark(new_spot, k, max(dte - 1, 1), iv2)
                hedge_pnl = contracts * 100.0 * (exitp - entry)
            else:
                k_long = round(spot * 0.95)
                k_short = round(spot * 0.90)
                entry_l = _put_mark(spot, k_long, dte, sig)
                entry_s = _put_mark(spot, k_short, dte, sig)
                exit_l = _put_mark(new_spot, k_long, max(dte - 1, 1), iv2)
                exit_s = _put_mark(new_spot, k_short, max(dte - 1, 1), iv2)
                entry = entry_l - entry_s
                exitp = exit_l - exit_s
                entry_src = "DERIVED"
                hedge_pnl = contracts * 100.0 * (exitp - entry)
            total = qqq_pnl + hedge_pnl
            prot = None if qqq_pnl >= 0 else max(0.0, min(1.0, 1.0 - total / qqq_pnl)) if qqq_pnl != 0 else None
            rows.append(
                {
                    "shock": shock,
                    "structure": kind,
                    "underlying_pnl": qqq_pnl,
                    "hedge_pnl": hedge_pnl,
                    "total_pnl": total,
                    "protection_pct": prot,
                    "nav_impact": total / nav,
                    "entry": entry,
                    "exit": exitp,
                    "entry_source": entry_src if kind != "QQQ_ONLY" else spot_source,
                    "shocked_option_source": "DERIVED" if kind != "QQQ_ONLY" else "N/A",
                    "spot_source": spot_source,
                    "iv_source": iv_source,
                    "iv_used": sig,
                }
            )
    return {
        "status": "PASS",
        "spot": spot,
        "iv": sig,
        "spot_source": spot_source,
        "iv_source": iv_source,
        "note": "Shocked option values are DERIVED Black-Scholes. Only entry marks may be LIVE QUOTE.",
        "rows": rows,
        "source": "DERIVED" if spot_source != "LIVE QUOTE" else "MIXED",
    }


def _match(puts: list[OptionContract], strike: float, dte: int) -> Optional[OptionContract]:
    cand = [c for c in puts if c.source == "LIVE QUOTE" and c.strike is not None]
    if not cand:
        return None
    cand.sort(key=lambda c: (abs((c.dte or 0) - dte), abs((c.strike or 0) - strike)))
    best = cand[0]
    if abs((best.strike or 0) - strike) / max(strike, 1) > 0.015:
        return None
    return best
