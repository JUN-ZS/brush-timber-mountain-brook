"""Futu OpenD adapter.

UI / engines talk to this module, never to futu-api directly.
No credentials. No OpenSecTradeContext. No live orders.
"""

from __future__ import annotations

import socket
import traceback
from datetime import date, datetime
from typing import Any, Optional, Protocol

from .classify import classify_error
from .types import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    QQQ_CODE,
    VIX_CODE,
    Check,
    OptionContract,
    Quote,
    finite,
    unavailable_option,
    unavailable_quote,
)


class QuoteAdapter(Protocol):
    def connect(self) -> Check: ...
    def disconnect(self) -> None: ...
    def get_market_state(self) -> dict[str, Any]: ...
    def get_qqq_quote(self) -> Quote: ...
    def get_vix_quote(self) -> Quote: ...
    def get_qqq_option_chain(self, option_type: str = "PUT") -> dict[str, Any]: ...
    def get_option_quote(self, code: str) -> OptionContract: ...
    def get_option_quotes(self, codes: list[str]) -> list[OptionContract]: ...
    def get_order_book(self, code: str) -> dict[str, Any]: ...
    def subscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check: ...
    def unsubscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check: ...
    def get_daily_closes(self, code: str, n: int = 80) -> dict[str, Any]: ...


def probe_tcp(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True, f"tcp connect {host}:{port} ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        try:
            sock.close()
        except Exception:
            pass


def load_futu():
    try:
        import futu  # type: ignore

        return futu, None
    except Exception as e:
        return None, e


def _row_get(row: Any, *names: str) -> Any:
    for n in names:
        v = None
        if isinstance(row, dict):
            v = row.get(n)
        else:
            try:
                v = row[n]
            except Exception:
                v = getattr(row, n, None)
            if v is None and hasattr(row, "get"):
                try:
                    v = row.get(n)
                except Exception:
                    v = None
        if v is not None and not (isinstance(v, float) and v != v):
            if isinstance(v, str) and v.strip() == "":
                continue
            return v
    return None


def _dte(expiry: Optional[str]) -> Optional[int]:
    if not expiry:
        return None
    try:
        raw = str(expiry)[:10]
        exp = datetime.strptime(raw, "%Y-%m-%d").date()
        return (exp - date.today()).days
    except Exception:
        return None


def _right(v: Any) -> str:
    s = str(v or "").upper()
    if "CALL" in s or s in {"C", "2"}:
        return "CALL"
    return "PUT"


class FutuOpenDAdapter:
    """Official futu-api wrapper. Missing SDK / OpenD → UNAVAILABLE, never fake LIVE."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = int(port)
        self.ctx = None
        self.futu = None
        self.connected = False
        self.last_state: dict[str, Any] = {}
        self.last_error: Optional[str] = None

    def connect(self) -> Check:
        ok, why = probe_tcp(self.host, self.port)
        if not ok:
            self.last_error = why
            return Check(
                name="connection",
                status="FAIL",
                reason=f"OpenD tcp probe failed ({self.host}:{self.port}): {why}",
                issue_class="ENVIRONMENT",
            )
        futu, err = load_futu()
        if futu is None:
            self.last_error = str(err)
            return Check(
                name="connection",
                status="FAIL",
                reason=f"tcp port open but futu-api import failed: {err}",
                issue_class="ENVIRONMENT",
            )
        self.futu = futu
        try:
            self.ctx = futu.OpenQuoteContext(host=self.host, port=self.port)
            ret, data = self.ctx.get_global_state()
            ret_ok = getattr(futu, "RET_OK", 0)
            if ret != ret_ok:
                self.last_error = str(data)
                self.connected = False
                return Check(
                    name="connection",
                    status="FAIL",
                    reason=f"OpenQuoteContext opened but get_global_state failed: {data}",
                    issue_class=classify_error(str(data), connected=True),
                    extra={"ret": ret},
                )
            self.last_state = dict(data) if isinstance(data, dict) else {"raw": data}
            self.connected = True
            qot = bool(self.last_state.get("qot_logined"))
            if not qot:
                return Check(
                    name="connection",
                    status="PARTIAL",
                    reason="OpenD accepted the socket but qot_logined=False. Login inside OpenD.",
                    issue_class="ENVIRONMENT",
                    extra=self.last_state,
                )
            return Check(
                name="connection",
                status="PASS",
                reason=f"connected {self.host}:{self.port} qot_logined=True program={self.last_state.get('program_status_type')}",
                issue_class=None,
                extra={
                    "qot_logined": qot,
                    "trd_logined": bool(self.last_state.get("trd_logined")),
                    "market_us": str(self.last_state.get("market_us")),
                },
            )
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"
            self.connected = False
            return Check(
                name="connection",
                status="FAIL",
                reason=self.last_error,
                issue_class=classify_error(self.last_error, connected=False),
                extra={"trace": traceback.format_exc()[-1500:]},
            )

    def disconnect(self) -> None:
        ctx, self.ctx = self.ctx, None
        self.connected = False
        if ctx is None:
            return
        try:
            ctx.close()
        except Exception:
            pass

    def get_market_state(self) -> dict[str, Any]:
        if not self.connected or self.ctx is None:
            return {
                "source": "UNAVAILABLE",
                "reason": self.last_error or "not connected",
                "qot_logined": None,
                "trd_logined": None,
                "market_us": None,
            }
        try:
            ret_ok = getattr(self.futu, "RET_OK", 0)
            ret, data = self.ctx.get_global_state()
            if ret != ret_ok:
                return {"source": "UNAVAILABLE", "reason": str(data), "class": classify_error(str(data), connected=True)}
            d = dict(data) if isinstance(data, dict) else {"raw": data}
            d["source"] = "LIVE QUOTE"
            return d
        except Exception as e:
            return {"source": "UNAVAILABLE", "reason": f"{type(e).__name__}: {e}", "class": classify_error(str(e))}

    def _snapshot(self, codes: list[str]) -> tuple[Optional[Any], Optional[str]]:
        if not self.connected or self.ctx is None:
            return None, self.last_error or "not connected"
        try:
            ret_ok = getattr(self.futu, "RET_OK", 0)
            ret, data = self.ctx.get_market_snapshot(codes)
            if ret != ret_ok:
                return None, str(data)
            return data, None
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    def _quote_from_row(self, code: str, row: Any) -> Quote:
        last = finite(_row_get(row, "last_price", "last", "cur_price", "price"))
        bid = finite(_row_get(row, "bid_price", "bid", "bid_price_1"))
        ask = finite(_row_get(row, "ask_price", "ask", "ask_price_1"))
        ts = _row_get(row, "update_time", "data_time", "time")
        vol = finite(_row_get(row, "volume"))
        prev = finite(_row_get(row, "prev_close_price", "last_close_price", "prev_close"))
        if last is None and bid is None and ask is None:
            return unavailable_quote(code, "snapshot row had no last/bid/ask")
        return Quote(
            code=code,
            last=last,
            bid=bid,
            ask=ask,
            timestamp=str(ts) if ts is not None else None,
            source="LIVE QUOTE",
            volume=vol,
            prev_close=prev,
        )

    def _iter_rows(self, data: Any):
        if data is None:
            return
        if hasattr(data, "iterrows"):
            for _, row in data.iterrows():
                yield row
            return
        if isinstance(data, list):
            for row in data:
                yield row

    def get_qqq_quote(self) -> Quote:
        data, err = self._snapshot([QQQ_CODE])
        if err or data is None:
            q = unavailable_quote(QQQ_CODE, err or "snapshot empty")
            return q
        for row in self._iter_rows(data):
            code = str(_row_get(row, "code") or QQQ_CODE)
            return self._quote_from_row(code, row)
        return unavailable_quote(QQQ_CODE, "snapshot returned 0 rows")

    def get_vix_quote(self) -> Quote:
        data, err = self._snapshot([VIX_CODE])
        if err or data is None:
            return unavailable_quote(VIX_CODE, err or "snapshot empty")
        for row in self._iter_rows(data):
            return self._quote_from_row(str(_row_get(row, "code") or VIX_CODE), row)
        return unavailable_quote(VIX_CODE, "snapshot returned 0 rows")

    def get_qqq_option_chain(self, option_type: str = "PUT") -> dict[str, Any]:
        empty = {
            "underlying": QQQ_CODE,
            "expiry_count": 0,
            "contract_count": 0,
            "expiries": [],
            "contracts": [],
            "source": "UNAVAILABLE",
            "reason": None,
            "class": None,
        }
        if not self.connected or self.ctx is None:
            empty["reason"] = self.last_error or "not connected"
            empty["class"] = "ENVIRONMENT"
            return empty
        try:
            ret_ok = getattr(self.futu, "RET_OK", 0)
            ret, exp_data = self.ctx.get_option_expiration_date(code=QQQ_CODE)
            if ret != ret_ok:
                empty["reason"] = str(exp_data)
                empty["class"] = classify_error(str(exp_data), connected=True)
                return empty
            expiries: list[str] = []
            if hasattr(exp_data, "columns") and "strike_time" in list(exp_data.columns):
                expiries = [str(x)[:10] for x in exp_data["strike_time"].tolist() if x is not None]
            elif isinstance(exp_data, list):
                expiries = [str(x)[:10] for x in exp_data]
            today = date.today()
            dated: list[tuple[int, str]] = []
            for e in expiries:
                try:
                    dte = (datetime.strptime(e, "%Y-%m-%d").date() - today).days
                except Exception:
                    continue
                if 5 <= dte <= 90:
                    dated.append((dte, e))
            dated.sort()
            # Prefer 21/30/45 neighbourhood; keep at most 4 expiries.
            picked: list[str] = []
            for target in (21, 30, 45, 14, 60):
                if not dated:
                    break
                dated.sort(key=lambda t: abs(t[0] - target))
                e = dated[0][1]
                if e not in picked:
                    picked.append(e)
                    dated = [t for t in dated if t[1] != e]
            if not picked:
                picked = expiries[:3]
            opt = None
            try:
                ot = getattr(self.futu, "OptionType")
                opt = getattr(ot, option_type, None) or getattr(ot, "PUT", option_type)
            except Exception:
                opt = option_type
            contracts: list[OptionContract] = []
            reasons: list[str] = []
            for exp in picked:
                kwargs = {"code": QQQ_CODE, "start": exp, "end": exp}
                if opt is not None:
                    kwargs["option_type"] = opt
                ret2, chain = self.ctx.get_option_chain(**kwargs)
                if ret2 != ret_ok:
                    reasons.append(f"{exp}: {chain}")
                    continue
                for row in self._iter_rows(chain):
                    code = str(_row_get(row, "code") or "")
                    if not code:
                        continue
                    strike = finite(_row_get(row, "strike_price", "option_strike_price", "strike"))
                    strike_time = _row_get(row, "strike_time", "expiry", "expiration")
                    right = _right(_row_get(row, "option_type", "option_right", "type"))
                    lot = finite(_row_get(row, "lot_size", "option_contract_size"))
                    contracts.append(
                        OptionContract(
                            code=code,
                            underlying=QQQ_CODE,
                            right=right,
                            strike=strike,
                            expiry=str(strike_time)[:10] if strike_time else exp,
                            dte=_dte(str(strike_time)[:10] if strike_time else exp),
                            lot_size=int(lot) if lot else 100,
                            bid=None,
                            ask=None,
                            last=None,
                            iv=None,
                            delta=None,
                            gamma=None,
                            theta=None,
                            vega=None,
                            oi=None,
                            volume=None,
                            source="LIVE QUOTE",
                            field_sources={
                                "code": "LIVE QUOTE",
                                "strike": "LIVE QUOTE" if strike is not None else "UNAVAILABLE",
                                "expiry": "LIVE QUOTE",
                                "bid": "UNAVAILABLE",
                                "ask": "UNAVAILABLE",
                                "iv": "UNAVAILABLE",
                                "delta": "UNAVAILABLE",
                            },
                        )
                    )
            if not contracts:
                empty["expiries"] = picked
                empty["expiry_count"] = len(picked)
                empty["reason"] = "; ".join(reasons) if reasons else "option chain returned 0 contracts"
                empty["class"] = classify_error(empty["reason"], connected=True)
                empty["source"] = "UNAVAILABLE"
                return empty
            return {
                "underlying": QQQ_CODE,
                "expiry_count": len(picked),
                "contract_count": len(contracts),
                "expiries": picked,
                "contracts": contracts,
                "source": "LIVE QUOTE",
                "reason": "; ".join(reasons) if reasons else None,
                "class": None,
            }
        except Exception as e:
            empty["reason"] = f"{type(e).__name__}: {e}"
            empty["class"] = classify_error(empty["reason"], connected=True)
            empty["extra_trace"] = traceback.format_exc()[-1500:]
            return empty

    def _option_from_row(self, code: str, row: Any, meta: Optional[OptionContract] = None) -> OptionContract:
        bid = finite(_row_get(row, "bid_price", "bid", "bid_price_1"))
        ask = finite(_row_get(row, "ask_price", "ask", "ask_price_1"))
        last = finite(_row_get(row, "last_price", "last", "cur_price"))
        iv = finite(_row_get(row, "option_implied_volatility", "implied_volatility", "iv"))
        if iv is not None and iv > 3:
            iv = iv / 100.0
        delta = finite(_row_get(row, "option_delta", "delta"))
        gamma = finite(_row_get(row, "option_gamma", "gamma"))
        theta = finite(_row_get(row, "option_theta", "theta"))
        vega = finite(_row_get(row, "option_vega", "vega"))
        oi = finite(_row_get(row, "option_open_interest", "open_interest", "oi"))
        vol = finite(_row_get(row, "volume"))
        strike = finite(_row_get(row, "option_strike_price", "strike_price", "strike"))
        expiry = _row_get(row, "strike_time", "expiry")
        right = _right(_row_get(row, "option_type"))
        lot = finite(_row_get(row, "option_contract_size", "lot_size"))
        fs = {}
        for k, v in {
            "bid": bid,
            "ask": ask,
            "last": last,
            "iv": iv,
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "oi": oi,
            "volume": vol,
            "strike": strike,
        }.items():
            fs[k] = "LIVE QUOTE" if v is not None else "UNAVAILABLE"
        base = meta
        return OptionContract(
            code=code,
            underlying=QQQ_CODE,
            right=right if _row_get(row, "option_type") else (base.right if base else "PUT"),
            strike=strike if strike is not None else (base.strike if base else None),
            expiry=(str(expiry)[:10] if expiry else (base.expiry if base else None)),
            dte=_dte(str(expiry)[:10] if expiry else (base.expiry if base else None)),
            lot_size=int(lot) if lot else (base.lot_size if base else 100),
            bid=bid,
            ask=ask,
            last=last,
            iv=iv,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            oi=oi,
            volume=vol,
            source="LIVE QUOTE" if any(v is not None for v in (bid, ask, last, iv, delta)) else "UNAVAILABLE",
            field_sources=fs,
            reason=None if any(v is not None for v in (bid, ask, last)) else "snapshot had no bid/ask/last",
        )

    def get_option_quote(self, code: str) -> OptionContract:
        rows = self.get_option_quotes([code])
        return rows[0] if rows else unavailable_option(code, "empty")

    def get_option_quotes(self, codes: list[str]) -> list[OptionContract]:
        out: list[OptionContract] = []
        if not codes:
            return out
        batch = 40
        for i in range(0, len(codes), batch):
            chunk = codes[i : i + batch]
            data, err = self._snapshot(chunk)
            if err or data is None:
                for c in chunk:
                    o = unavailable_option(c, err or "snapshot empty")
                    out.append(o)
                continue
            seen = set()
            by_code: dict[str, Any] = {}
            for row in self._iter_rows(data):
                c = str(_row_get(row, "code") or "")
                if c:
                    by_code[c] = row
            for c in chunk:
                if c in by_code:
                    out.append(self._option_from_row(c, by_code[c]))
                    seen.add(c)
                else:
                    out.append(unavailable_option(c, "code missing from snapshot"))
        return out

    def get_order_book(self, code: str) -> dict[str, Any]:
        if not self.connected or self.ctx is None:
            return {"code": code, "source": "UNAVAILABLE", "reason": "not connected", "class": "ENVIRONMENT"}
        try:
            ret_ok = getattr(self.futu, "RET_OK", 0)
            ret, data = self.ctx.get_order_book(code)
            if ret != ret_ok:
                return {
                    "code": code,
                    "source": "UNAVAILABLE",
                    "reason": str(data),
                    "class": classify_error(str(data), connected=True),
                }
            payload: dict[str, Any] = {"code": code, "source": "LIVE QUOTE"}
            if isinstance(data, dict):
                payload.update({k: data.get(k) for k in ("Bid", "Ask", "bid", "ask") if k in data})
            else:
                payload["raw_type"] = type(data).__name__
            return payload
        except Exception as e:
            return {
                "code": code,
                "source": "UNAVAILABLE",
                "reason": f"{type(e).__name__}: {e}",
                "class": classify_error(str(e), connected=True),
            }

    def subscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check:
        if not self.connected or self.ctx is None or self.futu is None:
            return Check("subscribe", "FAIL", "not connected", "ENVIRONMENT")
        try:
            st = getattr(self.futu, "SubType")
            wanted = subtypes or ["QUOTE"]
            mapped = []
            for s in wanted:
                mapped.append(getattr(st, s, s))
            ret_ok = getattr(self.futu, "RET_OK", 0)
            ret, err = self.ctx.subscribe(codes, mapped)
            if ret != ret_ok:
                return Check("subscribe", "FAIL", str(err), classify_error(str(err), connected=True))
            return Check("subscribe", "PASS", f"subscribed {len(codes)} codes", None)
        except Exception as e:
            return Check("subscribe", "FAIL", f"{type(e).__name__}: {e}", classify_error(str(e), connected=True))

    def unsubscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check:
        if not self.connected or self.ctx is None or self.futu is None:
            return Check("unsubscribe", "SKIPPED", "not connected", "ENVIRONMENT")
        try:
            st = getattr(self.futu, "SubType")
            wanted = subtypes or ["QUOTE"]
            mapped = [getattr(st, s, s) for s in wanted]
            ret_ok = getattr(self.futu, "RET_OK", 0)
            ret, err = self.ctx.unsubscribe(codes, mapped)
            if ret != ret_ok:
                return Check("unsubscribe", "FAIL", str(err), classify_error(str(err), connected=True))
            return Check("unsubscribe", "PASS", f"unsubscribed {len(codes)} codes", None)
        except Exception as e:
            return Check("unsubscribe", "FAIL", f"{type(e).__name__}: {e}", classify_error(str(e)))

    def get_daily_closes(self, code: str, n: int = 80) -> dict[str, Any]:
        if not self.connected or self.ctx is None or self.futu is None:
            return {"code": code, "source": "UNAVAILABLE", "closes": [], "reason": "not connected"}
        try:
            kl = getattr(self.futu, "KLType").K_DAY
            ret_ok = getattr(self.futu, "RET_OK", 0)
            if hasattr(self.ctx, "request_history_kline"):
                ret, data, _page = self.ctx.request_history_kline(code, ktype=kl, max_count=n)
            else:
                ret, data = self.ctx.get_cur_kline(code, n, kl)
            if ret != ret_ok:
                return {
                    "code": code,
                    "source": "UNAVAILABLE",
                    "closes": [],
                    "reason": str(data),
                    "class": classify_error(str(data), connected=True),
                }
            closes: list[float] = []
            dates: list[str] = []
            if hasattr(data, "iterrows"):
                col_c = "close" if "close" in data.columns else ("Close" if "Close" in data.columns else None)
                col_t = "time_key" if "time_key" in data.columns else ("time" if "time" in data.columns else None)
                if col_c:
                    for _, row in data.iterrows():
                        v = finite(row[col_c])
                        if v is not None:
                            closes.append(v)
                            dates.append(str(row[col_t])[:10] if col_t else "")
            return {"code": code, "source": "LIVE QUOTE", "closes": closes, "dates": dates}
        except Exception as e:
            return {
                "code": code,
                "source": "UNAVAILABLE",
                "closes": [],
                "reason": f"{type(e).__name__}: {e}",
                "class": classify_error(str(e), connected=True),
            }


class UnavailableAdapter:
    """Used when SDK is missing. Every price source is UNAVAILABLE."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reason: str = "futu-api not installed"):
        self.host = host
        self.port = port
        self.reason = reason
        self.connected = False
        self.last_state: dict[str, Any] = {}

    def connect(self) -> Check:
        return Check("connection", "FAIL", self.reason, "ENVIRONMENT")

    def disconnect(self) -> None:
        return None

    def get_market_state(self) -> dict[str, Any]:
        return {"source": "UNAVAILABLE", "reason": self.reason, "class": "ENVIRONMENT"}

    def get_qqq_quote(self) -> Quote:
        return unavailable_quote(QQQ_CODE, self.reason)

    def get_vix_quote(self) -> Quote:
        return unavailable_quote(VIX_CODE, self.reason)

    def get_qqq_option_chain(self, option_type: str = "PUT") -> dict[str, Any]:
        return {
            "underlying": QQQ_CODE,
            "expiry_count": 0,
            "contract_count": 0,
            "expiries": [],
            "contracts": [],
            "source": "UNAVAILABLE",
            "reason": self.reason,
            "class": "ENVIRONMENT",
        }

    def get_option_quote(self, code: str) -> OptionContract:
        return unavailable_option(code, self.reason)

    def get_option_quotes(self, codes: list[str]) -> list[OptionContract]:
        return [unavailable_option(c, self.reason) for c in codes]

    def get_order_book(self, code: str) -> dict[str, Any]:
        return {"code": code, "source": "UNAVAILABLE", "reason": self.reason, "class": "ENVIRONMENT"}

    def subscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check:
        return Check("subscribe", "SKIPPED", self.reason, "ENVIRONMENT")

    def unsubscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check:
        return Check("unsubscribe", "SKIPPED", self.reason, "ENVIRONMENT")

    def get_daily_closes(self, code: str, n: int = 80) -> dict[str, Any]:
        return {"code": code, "source": "UNAVAILABLE", "closes": [], "reason": self.reason}


class MockAdapter:
    """Test-only. SOURCE is always SYNTHETIC. Must never be used as LIVE."""

    def __init__(self, qqq: float = 500.0, vix: float = 20.0):
        self.host = "mock"
        self.port = 0
        self.connected = False
        self.qqq = qqq
        self.vix = vix
        self.last_state = {"qot_logined": True, "market_us": "MOCK"}

    def connect(self) -> Check:
        self.connected = True
        return Check("connection", "PASS", "mock adapter SOURCE=SYNTHETIC", None, extra={"source": "SYNTHETIC"})

    def disconnect(self) -> None:
        self.connected = False

    def get_market_state(self) -> dict[str, Any]:
        return {"source": "SYNTHETIC", "qot_logined": True, "trd_logined": False, "market_us": "MOCK"}

    def get_qqq_quote(self) -> Quote:
        return Quote(QQQ_CODE, self.qqq, self.qqq - 0.01, self.qqq + 0.01, "SYNTHETIC", "SYNTHETIC")

    def get_vix_quote(self) -> Quote:
        return Quote(VIX_CODE, self.vix, None, None, "SYNTHETIC", "SYNTHETIC")

    def get_qqq_option_chain(self, option_type: str = "PUT") -> dict[str, Any]:
        c = OptionContract(
            code="US.QQQ_SYNTHETIC_P",
            underlying=QQQ_CODE,
            right="PUT",
            strike=round(self.qqq * 0.95, 2),
            expiry="2099-01-01",
            dte=30,
            lot_size=100,
            bid=8.0,
            ask=8.4,
            last=8.2,
            iv=0.22,
            delta=-0.25,
            gamma=0.01,
            theta=-0.05,
            vega=0.12,
            oi=1000,
            volume=10,
            source="SYNTHETIC",
            field_sources={k: "SYNTHETIC" for k in ("bid", "ask", "iv", "delta")},
        )
        return {
            "underlying": QQQ_CODE,
            "expiry_count": 1,
            "contract_count": 1,
            "expiries": ["2099-01-01"],
            "contracts": [c],
            "source": "SYNTHETIC",
            "reason": "mock",
            "class": None,
        }

    def get_option_quote(self, code: str) -> OptionContract:
        return self.get_qqq_option_chain()["contracts"][0]

    def get_option_quotes(self, codes: list[str]) -> list[OptionContract]:
        row = self.get_option_quote(codes[0] if codes else "X")
        return [row for _ in codes] or [row]

    def get_order_book(self, code: str) -> dict[str, Any]:
        return {"code": code, "source": "SYNTHETIC", "bid": [[8.0, 10]], "ask": [[8.4, 10]]}

    def subscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check:
        return Check("subscribe", "PASS", "mock", None, extra={"source": "SYNTHETIC"})

    def unsubscribe(self, codes: list[str], subtypes: Optional[list[str]] = None) -> Check:
        return Check("unsubscribe", "PASS", "mock", None)

    def get_daily_closes(self, code: str, n: int = 80) -> dict[str, Any]:
        px = self.qqq if "QQQ" in code else self.vix
        closes = [px * (1 + 0.0001 * i) for i in range(n)]
        return {"code": code, "source": "SYNTHETIC", "closes": closes}


def make_adapter(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    futu, err = load_futu()
    if futu is None:
        return UnavailableAdapter(host, port, f"futu-api not installed: {err}")
    return FutuOpenDAdapter(host, port)
