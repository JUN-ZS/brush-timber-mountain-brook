from __future__ import annotations

import json
import os
import re
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import futu  # type: ignore
except Exception:
    futu = None

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)
EVENTS = RUNTIME / "ledger_events.jsonl"
HOST = "127.0.0.1"
PORT = int(os.environ.get("QHP_LEDGER_PORT", "8790"))
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_resp(handler, payload, status=200):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(raw)


def num(value):
    try:
        x = float(str(value).replace(",", ""))
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def rows_from_futu(data):
    if isinstance(data, dict):
        return [data]
    if hasattr(data, "to_dict"):
        return data.to_dict("records")
    if isinstance(data, (list, tuple)):
        return list(data)
    return []


def row_get(row, *names):
    for name in names:
        if isinstance(row, dict) and name in row:
            return row[name]
        try:
            if hasattr(row, name):
                return getattr(row, name)
        except Exception:
            pass
    return None


def read_events():
    if not EVENTS.exists():
        return []
    out = []
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def existing_ids():
    return {str(x.get("id")) for x in read_events() if x.get("id")}


def append_events(events):
    ids = existing_ids()
    added = 0
    duplicates = 0
    with EVENTS.open("a", encoding="utf-8") as handle:
        for event in events:
            event_id = str(event.get("id") or "")
            if not event_id:
                raise ValueError("every imported event needs an id")
            if event_id in ids:
                duplicates += 1
                continue
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
            ids.add(event_id)
            added += 1
    return added, duplicates


def opend_marks(symbols):
    if futu is None:
        raise RuntimeError("futu-api unavailable")
    ctx = futu.OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    try:
        codes = ["US." + s if "." not in s else s for s in symbols]
        ret, data = ctx.get_market_snapshot(codes)
        if ret != getattr(futu, "RET_OK", 0):
            raise RuntimeError(str(data))
        result = {}
        for row in rows_from_futu(data):
            code = str(row_get(row, "code") or "").upper()
            px = num(row_get(row, "last_price"))
            if not code or px is None:
                continue
            result[code] = {"price": px, "source": "OPEND"}
            if code.startswith("US."):
                result[code[3:]] = {"price": px, "source": "OPEND"}
        return result
    finally:
        try:
            ctx.close()
        except Exception:
            pass


def yahoo_mark(symbol):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol, safe="") + "?range=1d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8, context=ssl.create_default_context()) as response:
        payload = json.load(response)
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        raise RuntimeError("Yahoo returned no chart result")
    meta = result[0].get("meta") or {}
    px = num(meta.get("regularMarketPrice"))
    if px is None:
        raise RuntimeError("Yahoo returned no regularMarketPrice")
    return {"price": px, "source": "YAHOO"}


def get_marks(symbols):
    wanted = [str(x).strip().upper() for x in symbols if str(x).strip()]
    out = {}
    errors = {}
    if wanted and futu is not None:
        try:
            out.update(opend_marks(wanted))
        except Exception as exc:
            errors["OPEND"] = type(exc).__name__ + ": " + str(exc)
    for symbol in wanted:
        if symbol in out:
            continue
        if symbol in {"QQQ", "VXX"}:
            try:
                out[symbol] = yahoo_mark(symbol)
            except Exception as exc:
                errors[symbol] = type(exc).__name__ + ": " + str(exc)
    return out, errors


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def translate_path(self, path):
        relative = urllib.parse.urlparse(path).path.lstrip("/")
        return str(ROOT / relative)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            return json_resp(self, {
                "ok": True,
                "app": "QQQ-HYBRID-PORTFOLIO-LEDGER-V1",
                "port": PORT,
                "futu_package": futu is not None,
                "events": str(EVENTS),
                "broker_orders": False,
            })
        if parsed.path == "/api/events":
            return json_resp(self, {"ok": True, "events": read_events()})
        if parsed.path == "/api/marks":
            symbols = urllib.parse.parse_qs(parsed.query).get("symbols", [""])[0].split(",")
            rows, errors = get_marks(symbols)
            source = "OPEND" if rows and all(v.get("source") == "OPEND" for v in rows.values()) else ("MIXED" if rows else "NONE")
            return json_resp(self, {
                "ok": bool(rows) or not [x for x in symbols if x],
                "rows": [{"symbol": k, **v} for k, v in rows.items()],
                "errors": errors,
                "source": source,
                "asOf": now_iso(),
            })
        if parsed.path == "/api/strategy-status":
            return json_resp(self, {
                "ok": True,
                "connected": False,
                "policy_owner": "V3",
                "message": "No automatic V3 bridge in Ledger V1. Do not derive BUY/HOLD/REDUCE from P&L.",
            })
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in {"/api/events", "/api/import"}:
            return json_resp(self, {"ok": False, "error": "not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if parsed.path == "/api/events":
                event = payload
                event_type = str(event.get("type", "")).upper()
                if event_type not in {"FILL", "CASHFLOW"}:
                    raise ValueError("event type must be FILL or CASHFLOW")
                added, duplicates = append_events([event])
            else:
                incoming = payload.get("events")
                if not isinstance(incoming, list):
                    raise ValueError("events array required")
                added, duplicates = append_events(incoming)
            return json_resp(self, {"ok": True, "added": added, "duplicates": duplicates})
        except Exception as exc:
            return json_resp(self, {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}, 400)


if __name__ == "__main__":
    print("QQQ Hybrid Portfolio Ledger V1: http://127.0.0.1:" + str(PORT))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
