from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Any

class DatabentoVXLive:
    """Optional secondary CFE VX source.

    Uses Databento XCBF.PITCH via the official client. No web scraping.
    Keeps instrument definitions/expiries and 1-second BBO quotes locally,
    then selects the two earliest valid full-size VX expiries.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("DATABENTO_API_KEY")
        self._lock = threading.Lock()
        self._definitions: dict[int, dict[str, Any]] = {}
        self._quotes: dict[int, dict[str, Any]] = {}
        self._client = None
        self._thread = None
        self._started = False
        self._error: str | None = None

    def configured(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _get(obj, *names):
        for name in names:
            if isinstance(obj, dict):
                value = obj.get(name)
            else:
                value = getattr(obj, name, None)
            if value is not None:
                return value
        return None

    @staticmethod
    def _price(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        if abs(value) > 1e7:
            value /= 1_000_000_000.0
        return value if value > 0 else None

    @staticmethod
    def _iso(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return str(value)

    def start(self):
        if self._started:
            return self.status()
        if not self.configured():
            self._error = "DATABENTO_API_KEY not configured"
            return self.status()
        try:
            import databento as db  # type: ignore
        except Exception as exc:
            self._error = f"databento package unavailable: {exc}"
            return self.status()
        try:
            self._client = db.Live(self.api_key)
            self._client.subscribe(
                dataset="XCBF.PITCH",
                schema="definition",
                symbols="VX.FUT",
                stype_in="parent",
            )
            self._client.subscribe(
                dataset="XCBF.PITCH",
                schema="bbo-1s",
                symbols="VX.FUT",
                stype_in="parent",
            )
            self._client.add_callback(self._on_record)
            self._client.start()
            self._started = True
            return self.status()
        except Exception as exc:
            self._client = None
            self._started = False
            self._error = f"{type(exc).__name__}: {exc}"
            return self.status()

    def _on_record(self, record):
        iid = self._get(record, "instrument_id")
        if iid is None:
            return
        try:
            iid = int(iid)
        except (TypeError, ValueError):
            return

        raw_symbol = self._get(record, "stype_out_symbol", "raw_symbol", "symbol")
        expiry = self._get(record, "expiration", "expiry")
        if raw_symbol or expiry:
            with self._lock:
                item = self._definitions.setdefault(iid, {"instrument_id": iid})
                if raw_symbol:
                    item["raw_symbol"] = str(raw_symbol)
                if expiry:
                    item["expiry"] = self._iso(expiry)

        price = self._price(self._get(record, "price", "last_price"))
        bid = self._price(self._get(record, "bid_px_00", "bid_px", "bid"))
        ask = self._price(self._get(record, "ask_px_00", "ask_px", "ask"))
        stamp = self._iso(self._get(record, "ts_recv", "ts_event", "pretty_ts_recv", "pretty_ts_event"))
        if any(v is not None for v in (price, bid, ask)):
            with self._lock:
                self._quotes[iid] = {
                    "instrument_id": iid,
                    "last": price,
                    "bid": bid,
                    "ask": ask,
                    "mid": (bid + ask) / 2 if bid is not None and ask is not None else price,
                    "timestamp": stamp,
                }

    @staticmethod
    def _is_full_size_vx(raw_symbol):
        return isinstance(raw_symbol, str) and raw_symbol.upper().startswith("VX/")

    def latest(self):
        if not self._started:
            self.start()
        now = datetime.now(timezone.utc)
        rows = []
        with self._lock:
            definitions = list(self._definitions.values())
            quotes = dict(self._quotes)

        for definition in definitions:
            raw = definition.get("raw_symbol")
            if not self._is_full_size_vx(raw):
                continue
            expiry_raw = definition.get("expiry")
            if not expiry_raw:
                continue
            try:
                expiry = datetime.fromisoformat(str(expiry_raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            if expiry <= now:
                continue
            quote = quotes.get(int(definition.get("instrument_id", -1)))
            if not quote:
                continue
            if not any(quote.get(k) is not None for k in ("mid", "last", "bid", "ask")):
                continue
            rows.append({**definition, **quote, "expiry": expiry.isoformat()})

        rows.sort(key=lambda x: datetime.fromisoformat(x["expiry"]))
        if len(rows) < 2:
            return {
                "ok": False,
                "source": "DATABENTO_CFE",
                "status": "BLOCKED",
                "reason": self._error or "waiting for two valid VX definitions and quotes",
            }

        return {
            "ok": True,
            "source": "DATABENTO_CFE",
            "status": "LIVE",
            "m1": rows[0],
            "m2": rows[1],
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

    def status(self):
        latest_ok = False
        if self._started:
            try:
                latest_ok = bool(self.latest().get("ok"))
            except Exception:
                latest_ok = False
        return {
            "configured": self.configured(),
            "started": self._started,
            "source": "DATABENTO_CFE",
            "latest_ok": latest_ok,
            "error": self._error,
        }

    def close(self):
        try:
            if self._client is not None:
                self._client.stop()
        except Exception:
            pass
        self._client = None
        self._started = False
