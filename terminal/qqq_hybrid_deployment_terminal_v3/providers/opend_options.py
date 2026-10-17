"""Futu OpenD option-chain fallback for QQQ / VXX (read-only).

Contract:
  success -> {ok:True, status:"LIVE", source:"OPEND_OPTIONS", ...}
  no OpenD / not entitled / connect fail ->
    {ok:False, status:"BLOCKED_NO_OPEND", source:"OPEND_OPTIONS", ...}
  OpenD up but empty / API error ->
    {ok:False, status:"OPTIONS_SOURCE_DOWN", source:"OPEND_OPTIONS", ...}

Never invents strikes. Optional dependency — no hard require if futu missing.
Mirrors server.py opend_snapshot (host/port, try/finally close context).
"""

from __future__ import annotations

import os
import socket
from datetime import date, datetime, timezone
from typing import Any

SOURCE = "OPEND_OPTIONS"
ALLOWED = frozenset({"QQQ", "VXX"})
CODE_MAP = {"QQQ": "US.QQQ", "VXX": "US.VXX"}

OPEND_HOST = os.environ.get("OPEND_HOST", "127.0.0.1")
OPEND_PORT = int(os.environ.get("OPEND_PORT", "11111"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(v: Any):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def _iter_rows(data):
    if isinstance(data, dict):
        return [data]
    if hasattr(data, "to_dict"):
        return data.to_dict("records")
    if isinstance(data, (list, tuple)):
        return list(data)
    return []


def _row_get(row, *names):
    for name in names:
        if isinstance(row, dict) and name in row:
            return row[name]
        try:
            if hasattr(row, name):
                return getattr(row, name)
        except Exception:
            pass
        try:
            return row[name]
        except Exception:
            pass
    return None


def _base(symbol: str, status: str, error: str | None = None) -> dict:
    return {
        "ok": False,
        "status": status,
        "source": SOURCE,
        "symbol": symbol,
        "error": error,
        "calls": [],
        "candidate": None,
        "expiry": None,
        "spot": None,
        "retrieved_at": _now_iso(),
    }


def _blocked(symbol: str, error: str) -> dict:
    return _base(symbol, "BLOCKED_NO_OPEND", error)


def _down(symbol: str, error: str) -> dict:
    return _base(symbol, "OPTIONS_SOURCE_DOWN", error)


def _is_permission(msg: str) -> bool:
    text = (msg or "").lower()
    keys = (
        "permission",
        "no right",
        "no privilege",
        "not authorized",
        "unauthor",
        "无权限",
        "沒有權限",
        "没有权限",
        "行情权限",
        "option right",
        "no access",
        "not entitled",
        "qot_logined=false",
        "qot_logined=False",
    )
    return any(k.lower() in text for k in keys)


def _tcp_open(host: str, port: int, timeout: float = 1.5) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"tcp connect {host}:{port} ok"
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _pick_expiry(expiries: list[str], target_dte: int) -> str | None:
    today = date.today()
    dated: list[tuple[int, str]] = []
    for e in expiries:
        raw = str(e)[:10]
        try:
            dte = (datetime.strptime(raw, "%Y-%m-%d").date() - today).days
        except Exception:
            continue
        if 14 <= dte <= 120:
            dated.append((dte, raw))
    if not dated:
        return None
    dated.sort(key=lambda t: abs(t[0] - target_dte))
    return dated[0][1]


def _normalize_call(row: dict, expiry: str, dte: int) -> dict | None:
    strike = _num(
        _row_get(row, "option_strike_price", "strike_price", "strike")
    )
    if strike is None or strike <= 0:
        return None
    bid = _num(_row_get(row, "bid_price", "bid", "bid_price_1"))
    ask = _num(_row_get(row, "ask_price", "ask", "ask_price_1"))
    last = _num(_row_get(row, "last_price", "last", "cur_price", "lastPrice"))
    iv = _num(
        _row_get(
            row,
            "option_implied_volatility",
            "implied_volatility",
            "impliedVolatility",
            "iv",
        )
    )
    # OpenD often reports IV as percent (e.g. 28); Yahoo uses fraction (0.28).
    if iv is not None and iv > 3:
        iv = iv / 100.0
    delta = _num(_row_get(row, "option_delta", "delta"))
    code = str(_row_get(row, "code") or "") or None
    return {
        "contractSymbol": code,
        "strike": strike,
        "bid": bid,
        "ask": ask,
        "lastPrice": last,
        "impliedVolatility": iv,
        "delta": delta,
        "expiration": expiry,
        "expiry": expiry,
        "days": dte,
    }


def fetch_option_chain(
    symbol: str = "QQQ",
    target_dte: int = 45,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Fetch US call chain near target_dte via Futu OpenD quote context."""
    sym = str(symbol or "").strip().upper()
    if sym not in ALLOWED:
        return _down(sym or "QQQ", "symbol must be QQQ or VXX")

    try:
        dte_target = max(14, min(120, int(float(target_dte))))
    except (TypeError, ValueError):
        dte_target = 45

    host = host or OPEND_HOST
    port = int(port if port is not None else OPEND_PORT)
    code = CODE_MAP[sym]

    try:
        import futu  # type: ignore
    except Exception as exc:
        return _blocked(sym, f"futu package unavailable: {type(exc).__name__}: {exc}")

    ok_tcp, tcp_msg = _tcp_open(host, port)
    if not ok_tcp:
        return _blocked(sym, f"OpenD tcp probe failed ({host}:{port}): {tcp_msg}")

    ctx = None
    try:
        ctx = futu.OpenQuoteContext(host=host, port=port)
        ret_ok = getattr(futu, "RET_OK", 0)

        # Entitlement / login probe
        try:
            ret_gs, gs = ctx.get_global_state()
            if ret_gs == ret_ok and isinstance(gs, dict):
                if gs.get("qot_logined") is False:
                    return _blocked(
                        sym,
                        "OpenD accepted socket but qot_logined=False (login / not entitled)",
                    )
        except Exception as exc:
            # Non-fatal if get_global_state unavailable; continue to chain call.
            gs_err = f"{type(exc).__name__}: {exc}"
            if _is_permission(gs_err):
                return _blocked(sym, gs_err)

        # Spot for underlying
        spot = None
        try:
            ret_s, snap = ctx.get_market_snapshot([code])
            if ret_s == ret_ok:
                for row in _iter_rows(snap):
                    spot = _num(_row_get(row, "last_price"))
                    if spot is not None:
                        break
        except Exception:
            pass

        ret, exp_data = ctx.get_option_expiration_date(code=code)
        if ret != ret_ok:
            err = str(exp_data)
            if _is_permission(err):
                return _blocked(sym, err)
            return _down(sym, f"get_option_expiration_date failed: {err}")

        expiries: list[str] = []
        if hasattr(exp_data, "columns") and "strike_time" in list(exp_data.columns):
            expiries = [
                str(x)[:10] for x in exp_data["strike_time"].tolist() if x is not None
            ]
        else:
            for row in _iter_rows(exp_data):
                st = _row_get(row, "strike_time", "expiry", "expiration")
                if st is not None:
                    expiries.append(str(st)[:10])

        expiry = _pick_expiry(expiries, dte_target)
        if not expiry:
            return _down(sym, "no option expiry near target DTE (14–120)")

        try:
            dte = (datetime.strptime(expiry, "%Y-%m-%d").date() - date.today()).days
        except Exception:
            dte = dte_target

        opt = getattr(getattr(futu, "OptionType", object), "CALL", "CALL")
        ret2, chain = ctx.get_option_chain(
            code=code, start=expiry, end=expiry, option_type=opt
        )
        if ret2 != ret_ok:
            err = str(chain)
            if _is_permission(err):
                return _blocked(sym, err)
            return _down(sym, f"get_option_chain failed: {err}")

        meta_rows = []
        for row in _iter_rows(chain):
            c = str(_row_get(row, "code") or "")
            strike = _num(_row_get(row, "strike_price", "option_strike_price", "strike"))
            if not c or strike is None:
                continue
            # Prefer OTM wing for credit-spread candidate selection (strike > spot).
            if spot is not None and strike <= spot:
                continue
            if spot is not None and strike > spot * 1.60:
                continue
            meta_rows.append({"code": c, "strike": strike, "row": row})

        if not meta_rows:
            # Fall back to all strikes if OTM filter emptied the set (spot unknown).
            for row in _iter_rows(chain):
                c = str(_row_get(row, "code") or "")
                strike = _num(
                    _row_get(row, "strike_price", "option_strike_price", "strike")
                )
                if c and strike is not None:
                    meta_rows.append({"code": c, "strike": strike, "row": row})

        if not meta_rows:
            return _down(sym, "OpenD option chain returned 0 contracts")

        # Enrich with snapshot quotes (bid/ask/IV/delta) — batch ≤40
        by_code: dict[str, Any] = {}
        codes = [m["code"] for m in meta_rows]
        batch = 40
        snap_errors: list[str] = []
        for i in range(0, len(codes), batch):
            chunk = codes[i : i + batch]
            try:
                ret3, snap = ctx.get_market_snapshot(chunk)
                if ret3 != ret_ok:
                    snap_errors.append(str(snap))
                    continue
                for row in _iter_rows(snap):
                    c = str(_row_get(row, "code") or "")
                    if c:
                        by_code[c] = row
            except Exception as exc:
                snap_errors.append(f"{type(exc).__name__}: {exc}")

        calls: list[dict] = []
        for m in meta_rows:
            snap_row = by_code.get(m["code"])
            if snap_row is not None:
                # Merge chain strike into snapshot if missing
                if _num(_row_get(snap_row, "option_strike_price", "strike_price", "strike")) is None:
                    if isinstance(snap_row, dict):
                        snap_row = {**snap_row, "strike_price": m["strike"]}
                merged = snap_row
            else:
                # Chain-only: strike+expiry known; quotes unavailable
                merged = {
                    "code": m["code"],
                    "strike_price": m["strike"],
                    "option_strike_price": m["strike"],
                }
            norm = _normalize_call(merged, expiry, dte)
            if norm is not None:
                calls.append(norm)

        usable = [
            c
            for c in calls
            if c.get("strike") is not None
            and (c.get("delta") is not None or c.get("impliedVolatility") is not None)
        ]
        if not usable:
            detail = (
                f"OpenD chain had {len(meta_rows)} contracts but no usable IV/delta quotes"
            )
            if snap_errors:
                detail += f"; snapshot errors: {'; '.join(snap_errors[:3])}"
            return _down(sym, detail)

        return {
            "ok": True,
            "status": "LIVE",
            "source": SOURCE,
            "symbol": sym,
            "target_dte": dte_target,
            "expiry": expiry,
            "spot": spot,
            "calls": usable,
            "candidate": None,
            "retrieved_at": _now_iso(),
            "opend_code": code,
            "calls_raw_count": len(meta_rows),
        }
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        if _is_permission(err) or any(
            k in err.lower()
            for k in (
                "connection refused",
                "timed out",
                "timeout",
                "failed to connect",
                "errno 111",
                "errno 61",
                "winerror 10061",
            )
        ):
            return _blocked(sym, err)
        return _down(sym, err)
    finally:
        if ctx is not None:
            try:
                ctx.close()
            except Exception:
                pass


if __name__ == "__main__":
    import pprint
    import sys

    out = fetch_option_chain(sys.argv[1] if len(sys.argv) > 1 else "QQQ")
    if out.get("ok"):
        pprint.pp({**out, "calls": f"<{len(out['calls'])} calls>"})
    else:
        pprint.pp(out)
