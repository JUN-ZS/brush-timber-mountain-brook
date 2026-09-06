"""VIX substitutes when US index quotes are unavailable on OpenAPI.

Rules:
- Never label a proxy as LIVE QUOTE VIX.
- Prefer QQQ ~30D ATM put IV * 100 (same units as the VIX index).
- Optional VIXY 5-session change only as acceleration aid (not a VIX level).
- Fall back to QQQ realized vol * 100, then universe EOD VIX.
"""

from __future__ import annotations

from typing import Any, Optional

from .surface import atm_iv
from .types import OptionContract, finite
from .universe import closes, last_close, load_universe

VIXY_CODE = "US.VIXY"
TARGET_DTE = 30


def iv_to_vix_units(iv: float) -> float:
    """Map implied vol to VIX-like points (e.g. 0.18 -> 18, or 18 -> 18)."""
    x = float(iv)
    if x <= 0:
        raise ValueError("iv must be positive")
    if x <= 3.0:
        return x * 100.0
    return x


def pick_atm_near_dte(
    rows: list[OptionContract],
    spot: Optional[float],
    *,
    target_dte: int = TARGET_DTE,
) -> Optional[OptionContract]:
    if spot is None or spot <= 0:
        return None
    live = [
        r
        for r in rows
        if r.source == "LIVE QUOTE"
        and r.iv is not None
        and r.strike is not None
        and r.right == "PUT"
    ]
    if not live:
        live = [r for r in rows if r.source == "LIVE QUOTE" and r.iv is not None and r.strike is not None]
    if not live:
        return None
    with_dte = [r for r in live if r.dte is not None]
    pool = with_dte if with_dte else live
    pool.sort(key=lambda r: (abs((r.dte or target_dte) - target_dte), abs((r.strike or 0) - spot)))
    return pool[0]


def qqq_atm_iv_proxy(
    rows: list[OptionContract],
    spot: Optional[float],
) -> Optional[dict[str, Any]]:
    row = pick_atm_near_dte(rows, spot)
    if row is None:
        iv = atm_iv(rows, spot)
        if iv is None:
            return None
        level = iv_to_vix_units(iv)
        return {
            "level": level,
            "source": "DERIVED",
            "method": "QQQ_ATM_IV",
            "input_source": "LIVE QUOTE",
            "code": None,
            "dte": None,
            "iv_raw": iv,
            "reason": f"QQQ ATM IV {iv} -> proxy {level:.2f} (not US..VIX)",
        }
    iv = finite(row.iv)
    if iv is None:
        return None
    level = iv_to_vix_units(iv)
    return {
        "level": level,
        "source": "DERIVED",
        "method": "QQQ_ATM_IV",
        "input_source": "LIVE QUOTE",
        "code": row.code,
        "dte": row.dte,
        "iv_raw": iv,
        "strike": row.strike,
        "reason": (
            f"QQQ ATM put IV from {row.code} (dte={row.dte}) iv={iv} "
            f"-> proxy {level:.2f} VIX-units. Not the Cboe VIX index."
        ),
    }


def realized_vol_proxy(qqq_closes: Optional[list[float]]) -> Optional[dict[str, Any]]:
    if not qqq_closes or len(qqq_closes) < 22:
        return None
    from .engines import _stdev_rets

    vol = _stdev_rets(list(qqq_closes), 20)
    if vol <= 0:
        return None
    level = vol * 100.0
    return {
        "level": level,
        "source": "DERIVED",
        "method": "QQQ_REALIZED_VOL_20D",
        "input_source": "LIVE QUOTE",
        "code": "US.QQQ",
        "reason": f"QQQ 20d realized vol {vol:.4f} -> proxy {level:.2f} VIX-units",
    }


def vixy_accel(adapter: Any) -> Optional[dict[str, Any]]:
    """5-session VIXY change as acceleration aid only (not a VIX level)."""
    try:
        data, err = adapter._snapshot([VIXY_CODE])
        if err or data is None:
            return None
        last = None
        for row in adapter._iter_rows(data):
            last = finite(_row_get(row, "last_price"))
            break
        kl = adapter.get_daily_closes(VIXY_CODE, 12)
        closes_l = list((kl or {}).get("closes") or [])
        # Prefer same-series daily closes for accel so after-hours last cannot invent a fake jump.
        series_last = closes_l[-1] if closes_l else last
        prev5 = closes_l[-6] if len(closes_l) >= 6 else None
        accel = (series_last - prev5) if (series_last is not None and prev5 is not None) else None
        if abs(accel or 0) > 15:
            # Pathological gap / bad mix — drop accel rather than poison BUILDING.
            accel = None
        if last is None:
            last = series_last
        if last is None:
            return None
        return {
            "code": VIXY_CODE,
            "last": last,
            "prev5": prev5,
            "accel": accel,
            "closes": closes_l,
            "source": (kl or {}).get("source") or "LIVE QUOTE",
            "method": "VIXY_5D_CHG",
            "reason": "VIXY used only for acceleration aid; level is NOT treated as VIX",
        }
    except Exception as e:
        return {"code": VIXY_CODE, "error": f"{type(e).__name__}: {e}", "method": "VIXY_5D_CHG"}


def _row_get(row: Any, key: str):
    if hasattr(row, "get"):
        return row.get(key)
    try:
        return row[key]
    except Exception:
        return None


def resolve_vix_input(
    *,
    live_vix: Optional[float],
    live_vix_source: str,
    live_vix_closes: Optional[list[float]],
    option_rows: Optional[list[OptionContract]],
    spot: Optional[float],
    live_qqq_closes: Optional[list[float]],
    adapter: Any = None,
) -> dict[str, Any]:
    """Pick the best VIX-units input for classify_state."""
    out: dict[str, Any] = {
        "value": None,
        "prev5": None,
        "source": "UNAVAILABLE",
        "method": None,
        "reason": None,
        "proxy": None,
        "vixy": None,
        "index_quote_ok": False,
    }

    vixy = vixy_accel(adapter) if adapter is not None else None
    out["vixy"] = vixy

    if live_vix is not None and live_vix_source == "LIVE QUOTE":
        prev5 = None
        hist = list(live_vix_closes or [])
        if len(hist) >= 6:
            prev5 = hist[-6]
        out.update(
            {
                "value": float(live_vix),
                "prev5": prev5,
                "source": "LIVE QUOTE",
                "method": "US_INDEX_VIX",
                "reason": "live US..VIX",
                "index_quote_ok": True,
                "closes": hist,
            }
        )
        return out

    proxy = qqq_atm_iv_proxy(list(option_rows or []), spot)
    if proxy is None:
        proxy = realized_vol_proxy(live_qqq_closes)
    if proxy is None:
        u = load_universe()
        v = last_close("VIX", u)
        if v is not None:
            vh = closes("VIX", 10, u)
            prev5 = vh[-6] if len(vh) >= 6 else None
            proxy = {
                "level": float(v),
                "source": "DERIVED",
                "method": "UNIVERSE_EOD_VIX",
                "input_source": "DERIVED",
                "reason": "fallback to V2.2 EOD universe VIX; OpenAPI US index unavailable",
                "prev5": prev5,
            }

    if proxy is None:
        out["reason"] = "no VIX index and no usable proxy"
        return out

    value = float(proxy["level"])
    prev5 = proxy.get("prev5")
    if prev5 is None and vixy and vixy.get("accel") is not None:
        prev5 = value - float(vixy["accel"])
        proxy = dict(proxy)
        proxy["accel_from"] = "VIXY_5D_CHG"
        proxy["vixy_accel"] = vixy.get("accel")

    out.update(
        {
            "value": value,
            "prev5": prev5,
            "source": proxy.get("source") or "DERIVED",
            "method": proxy.get("method"),
            "reason": proxy.get("reason"),
            "proxy": proxy,
            "index_quote_ok": False,
        }
    )
    return out
