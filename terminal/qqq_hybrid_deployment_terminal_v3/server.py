
from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from providers.cboe_delayed_vx import fetch as fetch_cboe_vx
except Exception:
    fetch_cboe_vx = None

try:
    import futu  # type: ignore
except Exception:
    futu = None

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)
JOURNAL = RUNTIME / "decision_journal.jsonl"
HOST = "127.0.0.1"
PORT = 8788
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def json_resp(handler, payload, status=200):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(raw)


def num(v):
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
    return None


def opend_snapshot(codes):
    if futu is None:
        raise RuntimeError("futu package unavailable")
    ctx = futu.OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    try:
        ret, data = ctx.get_market_snapshot(codes)
        if ret != getattr(futu, "RET_OK", 0):
            raise RuntimeError(str(data))
        out = {}
        for row in _iter_rows(data):
            code = str(_row_get(row, "code") or "").upper()
            px = num(_row_get(row, "last_price"))
            if code and px is not None:
                out[code] = {"price": px, "source": "OPEND"}
        return out
    finally:
        try:
            ctx.close()
        except Exception:
            pass


def opend_spots():
    data = opend_snapshot(["US.QQQ", "US.VXX"])
    out = {
        "QQQ": data.get("US.QQQ"),
        "VXX": data.get("US.VXX"),
    }
    try:
        vx = opend_snapshot(["US..VIX"])
        out["VIX"] = next(iter(vx.values())) if vx else None
    except Exception:
        out["VIX"] = None
    return out


def yahoo(sym):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(sym, safe="")
        + "?range=1d&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=8, context=context) as response:
        payload = json.load(response)
    result = payload["chart"]["result"][0]
    meta = result.get("meta", {})
    px = meta.get("regularMarketPrice")
    ts = meta.get("regularMarketTime")
    return {"price": num(px), "timestamp": ts, "source": "YAHOO"}


def snapshot():
    out = {
        "captured_at": now_iso(),
        "today": datetime.now(timezone.utc).astimezone().date().isoformat(),
        "qqq": None,
        "vxx": None,
        "vix": None,
        "m1": None,
        "m2": None,
        "m1_code": None,
        "m2_code": None,
        "m1_expiry": None,
        "m2_expiry": None,
        "term_slope": None,
        "term_state": None,
        "term_source": "BLOCKED",
        "term_asof": None,
        "spot_asof": None,
        "source_chain": [],
        "provenance": {},
        "errors": {},
    }

    try:
        spots = opend_spots()
        for key in ("QQQ", "VXX", "VIX"):
            item = spots.get(key)
            if item and item.get("price") is not None:
                out[key.lower()] = item["price"]
                out["provenance"][key.lower()] = "OPEND"
        if any(x is not None for x in spots.values()):
            out["source_chain"].append("OPEND")
    except Exception as exc:
        out["errors"]["opend_spot"] = f"{type(exc).__name__}: {exc}"

    for key, sym in (("qqq", "QQQ"), ("vxx", "VXX"), ("vix", "^VIX")):
        if out[key] is not None:
            continue
        try:
            y = yahoo(sym)
            out[key] = y["price"]
            out["provenance"][key] = "YAHOO"
        except Exception as exc:
            out["errors"][f"yahoo_{key}"] = f"{type(exc).__name__}: {exc}"

    if out["qqq"] is not None or out["vxx"] is not None or out["vix"] is not None:
        out["source_chain"].append("YAHOO_FALLBACK")
    out["spot_asof"] = datetime.now(timezone.utc).astimezone().date().isoformat()

    if fetch_cboe_vx is not None:
        try:
            vx = fetch_cboe_vx()
            if vx.get("ok"):
                out["m1"] = vx["m1"]["price"]
                out["m2"] = vx["m2"]["price"]
                out["m1_code"] = vx["m1"]["symbol"]
                out["m2_code"] = vx["m2"]["symbol"]
                out["m1_expiry"] = vx["m1"]["expiry"]
                out["m2_expiry"] = vx["m2"]["expiry"]
                out["term_slope"] = vx["term_slope"] * 100
                out["term_state"] = vx["term_state"]
                out["term_source"] = vx["source"]
                out["term_asof"] = vx["data_asof"]
                out["provenance"]["m1"] = "CBOE_PUBLIC_DELAYED_VX"
                out["provenance"]["m2"] = "CBOE_PUBLIC_DELAYED_VX"
                out["provenance"]["term_slope"] = "DERIVED_FROM_CBOE_M1_M2"
                out["source_chain"].append("CBOE_PUBLIC_DELAYED_VX")
            else:
                out["errors"]["cboe_vx"] = vx.get("reason")
        except Exception as exc:
            out["errors"]["cboe_vx"] = f"{type(exc).__name__}: {exc}"

    # Cboe delayed VX is the production primary. OpenD VX is fallback only when Cboe is unavailable/incomplete.
    if (out["m1"] is None or out["m2"] is None) and futu is not None:
        try:
            ctx = futu.OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
            try:
                ret, basics = ctx.get_stock_basicinfo(futu.Market.US, futu.SecurityType.FUTURE)
                if ret == getattr(futu, "RET_OK", 0):
                    rows = []
                    for row in _iter_rows(basics):
                        code = str(_row_get(row, "code") or "").upper()
                        ltd = str(_row_get(row, "last_trade_time") or "")
                        if not re.fullmatch(r"US\.VX\d{4}", code):
                            continue
                        datepart = ltd[:10].replace("/", "-")
                        if len(datepart) != 10:
                            continue
                        rows.append((datepart, code))
                    rows.sort()
                    picks = []
                    for expiry, code in rows:
                        if expiry > out["today"]:
                            picks.append((expiry, code))
                    picks = picks[:2]
                    if len(picks) == 2:
                        codes = [p[1] for p in picks]
                        ret2, snap = ctx.get_market_snapshot(codes)
                        if ret2 == getattr(futu, "RET_OK", 0):
                            by = {}
                            for row in _iter_rows(snap):
                                code = str(_row_get(row, "code") or "").upper()
                                px = num(_row_get(row, "last_price"))
                                if px is not None:
                                    by[code] = px
                            if all(c in by for _, c in picks):
                                out["m1"], out["m2"] = by[picks[0][1]], by[picks[1][1]]
                                out["m1_code"], out["m2_code"] = picks[0][1], picks[1][1]
                                out["m1_expiry"], out["m2_expiry"] = picks[0][0], picks[1][0]
                                out["term_slope"] = ((out["m2"] - out["m1"]) / out["m1"]) * 100
                                out["term_state"] = "CONTANGO" if out["term_slope"] > 0 else ("BACKWARDATION" if out["term_slope"] < 0 else "FLAT")
                                out["term_source"] = "OPEND_VX_LIVE"
                                out["term_asof"] = out["today"]
                                out["provenance"]["m1"] = "OPEND_VX"
                                out["provenance"]["m2"] = "OPEND_VX"
                                out["provenance"]["term_slope"] = "DERIVED_FROM_OPEND_VX"
                                out["source_chain"].append("OPEND_VX_LIVE")
            finally:
                ctx.close()
        except Exception as exc:
            out["errors"]["opend_vx"] = f"{type(exc).__name__}: {exc}"



    out["source_chain"] = list(dict.fromkeys(out["source_chain"]))
    return out


def append_journal(payload):
    stamp = now_iso()
    row = {"journaled_at": stamp, **payload}
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"ok": True, "journaled_at": stamp}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path.startswith("/api/health"):
            return json_resp(
                self,
                {
                    "ok": True,
                    "engine": "V3-FREE-VX-PROVENANCE-2",
                    "port": PORT,
                    "opend_package": futu is not None,
                    "cboe_delayed_adapter": fetch_cboe_vx is not None,
                    "journal": str(JOURNAL),
                },
            )

        if self.path.startswith("/api/snapshot"):
            try:
                return json_resp(self, snapshot())
            except Exception as exc:
                return json_resp(self, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 502)

        if self.path.startswith("/api/journal"):
            rows = []
            if JOURNAL.exists():
                for line in JOURNAL.read_text(encoding="utf-8").splitlines()[-100:]:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
            return json_resp(self, {"ok": True, "rows": rows})

        if self.path.startswith("/api/options"):
            query = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(query.query)
            symbol = params.get("symbol", ["QQQ"])[0].upper()
            if symbol not in {"QQQ", "VXX"}:
                return json_resp(self, {"ok": False, "error": "symbol must be QQQ or VXX"}, 400)
            try:
                target_dte = max(14, min(120, int(float(params.get("targetDte", ["45"])[0]))))
                base_url = "https://query2.finance.yahoo.com/v7/finance/options/" + urllib.parse.quote(symbol, safe="")
                req = urllib.request.Request(base_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context()) as response:
                    root = json.load(response)
                result = (root.get("optionChain") or {}).get("result") or []
                if not result: raise RuntimeError("Yahoo option chain result unavailable")
                meta = result[0]
                expirations = [int(x) for x in (meta.get("expirationDates") or []) if num(x) is not None]
                now_ts = datetime.now(timezone.utc).timestamp()
                expiry = min(expirations, key=lambda x: abs((x-now_ts)/86400-target_dte)) if expirations else None
                url = base_url + (("?date="+str(expiry)) if expiry else "")
                req2 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=10, context=ssl.create_default_context()) as response:
                    payload = json.load(response)
                result2 = (payload.get("optionChain") or {}).get("result") or []
                if not result2: raise RuntimeError("Yahoo option expiry result unavailable")
                opts = result2[0].get("options") or []
                calls = opts[0].get("calls") if opts else []
                return json_resp(self, {"ok": True, "symbol": symbol, "source": "YAHOO_OPTIONS", "target_dte": target_dte, "expiry": datetime.fromtimestamp(expiry, timezone.utc).date().isoformat() if expiry else None, "retrieved_at": now_iso(), "calls": calls or []})
            except Exception as exc:
                return json_resp(self, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 502)
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/journal"):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
            return json_resp(self, append_journal(payload))
        except Exception as exc:
            return json_resp(self, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 400)


if __name__ == "__main__":
    print(f"QQQ Hybrid Deployment Terminal V3 -> http://{HOST}:{PORT}")
    print("Signal / decision-support only. No broker orders.")
    print("Term source: Cboe public delayed first; OpenD VX fallback.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
