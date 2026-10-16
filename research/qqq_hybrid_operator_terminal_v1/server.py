from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8790
V3_SNAPSHOT_URL = "http://127.0.0.1:8788/api/snapshot"
JOURNAL = ROOT / "runtime" / "operator_journal.jsonl"
JOURNAL.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_response(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def fetch_json(url: str, timeout: int = 8):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-store"})
    with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
        return json.load(response)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            return json_response(self, {
                "ok": True,
                "engine": "QQQ_HYBRID_OPERATOR_TERMINAL_V1",
                "host": HOST,
                "port": PORT,
                "broker_orders": False,
                "v3_snapshot_url": V3_SNAPSHOT_URL,
            })

        if parsed.path == "/api/snapshot":
            try:
                payload = fetch_json(V3_SNAPSHOT_URL, timeout=5)
                payload["bridge_source"] = "V3_READ_ONLY_LOCAL_SNAPSHOT"
                payload["bridge_retrieved_at"] = now_iso()
                payload["broker_orders"] = False
                return json_response(self, payload)
            except Exception as exc:
                return json_response(self, {
                    "ok": False,
                    "term_source": "BLOCKED",
                    "bridge_source": "V3_UNAVAILABLE",
                    "broker_orders": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "message": "Start the V3 terminal first, or enter a manually verified snapshot in the UI. No market values are fabricated.",
                }, 503)

        if parsed.path == "/api/options":
            params = urllib.parse.parse_qs(parsed.query)
            symbol = (params.get("symbol", ["QQQ"])[0] or "QQQ").upper()
            right = (params.get("right", ["both"])[0] or "both").lower()
            if symbol not in {"QQQ", "VXX"}:
                return json_response(self, {"ok": False, "error": "symbol must be QQQ or VXX"}, 400)
            if right not in {"call", "put", "both"}:
                return json_response(self, {"ok": False, "error": "right must be call, put or both"}, 400)
            try:
                target_dte = max(14, min(120, int(float(params.get("targetDte", ["45"])[0]))))
                base = "https://query2.finance.yahoo.com/v7/finance/options/" + urllib.parse.quote(symbol, safe="")
                root_payload = fetch_json(base, timeout=10)
                results = (root_payload.get("optionChain") or {}).get("result") or []
                if not results:
                    raise RuntimeError("option chain metadata unavailable")
                expirations = [int(x) for x in (results[0].get("expirationDates") or [])]
                now_ts = datetime.now(timezone.utc).timestamp()
                expiry = min(expirations, key=lambda x: abs((x - now_ts) / 86400 - target_dte)) if expirations else None
                url = base + (("?date=" + str(expiry)) if expiry else "")
                payload = fetch_json(url, timeout=10)
                rows = (payload.get("optionChain") or {}).get("result") or []
                if not rows:
                    raise RuntimeError("option chain expiry unavailable")
                opts = (rows[0].get("options") or [{}])[0]
                response = {
                    "ok": True,
                    "symbol": symbol,
                    "source": "YAHOO_OPTIONS_DELAYED_OR_ESTIMATED",
                    "target_dte": target_dte,
                    "expiry": datetime.fromtimestamp(expiry, timezone.utc).date().isoformat() if expiry else None,
                    "retrieved_at": now_iso(),
                    "calls": opts.get("calls") or [],
                    "puts": opts.get("puts") or [],
                    "warning": "Quotes may be delayed or incomplete and are not guaranteed executable. Check the live broker chain and bid/ask before acting.",
                    "broker_orders": False,
                }
                if right != "both":
                    response["calls" if right == "call" else "puts"] = opts.get("calls" if right == "call" else "puts") or []
                return json_response(self, response)
            except Exception as exc:
                return json_response(self, {
                    "ok": False,
                    "symbol": symbol,
                    "source": "UNAVAILABLE",
                    "error": f"{type(exc).__name__}: {exc}",
                    "broker_orders": False,
                }, 502)

        if parsed.path == "/api/journal":
            rows = []
            if JOURNAL.exists():
                for line in JOURNAL.read_text(encoding="utf-8").splitlines()[-100:]:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
            return json_response(self, {"ok": True, "rows": rows, "append_only": True, "broker_orders": False})

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/journal":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 1_000_000:
                return json_response(self, {"ok": False, "error": "invalid request size"}, 400)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                return json_response(self, {"ok": False, "error": "journal payload must be an object"}, 400)
            # Deliberately no order/trade mutation endpoint exists.
            row = {"journaled_at": now_iso(), "event_type": "MANUAL_PREVIEW_JOURNAL", **payload, "broker_orders": False}
            with JOURNAL.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            return json_response(self, {"ok": True, "journaled_at": row["journaled_at"], "broker_orders": False})
        except Exception as exc:
            return json_response(self, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 400)


if __name__ == "__main__":
    print("QQQ Hybrid Operator Terminal V1 -> http://127.0.0.1:8790")
    print("Read-only V3 market bridge at http://127.0.0.1:8788/api/snapshot")
    print("Manual sizing / journal only. No broker order endpoint.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
