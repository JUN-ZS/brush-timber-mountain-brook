from __future__ import annotations

import datetime
import json
import os
import re
import threading
import urllib.parse
import urllib.request
import ssl
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HOST = os.getenv("HYBRID_UI_HOST", "127.0.0.1")
PORT = int(os.getenv("HYBRID_UI_PORT", "8787"))
OPEND_HOST = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
OPEND_PORT = int(os.getenv("FUTU_OPEND_PORT", "11111"))
ROOT = Path(__file__).resolve().parent

try:
    import futu  # type: ignore
except Exception:
    futu = None

try:
    from providers.databento_vx import DatabentoVXLive
except Exception:
    DatabentoVXLive = None

_ctx = None
_ctx_lock = threading.Lock()
_contract_cache = {"ts": 0.0, "rows": []}
_db = DatabentoVXLive() if DatabentoVXLive else None


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _row_get(row, *names):
    for name in names:
        if isinstance(row, dict):
            value = row.get(name)
        else:
            try:
                value = row[name]
            except Exception:
                value = getattr(row, name, None)
        if value is None:
            continue
        if isinstance(value, float) and value != value:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _iter_rows(data):
    if data is None:
        return
    if hasattr(data, "iterrows"):
        for _, row in data.iterrows():
            yield row
    elif isinstance(data, list):
        yield from data


def opend_ctx():
    global _ctx
    if futu is None:
        return None
    with _ctx_lock:
        if _ctx is None:
            _ctx = futu.OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    return _ctx


def _opend_snapshot(codes):
    ctx = opend_ctx()
    if ctx is None:
        raise RuntimeError("futu package unavailable")
    ret, data = ctx.get_market_snapshot(codes)
    if ret != getattr(futu, "RET_OK", 0):
        raise RuntimeError(str(data))
    return data


def opend_spots():
    out = {}
    # QQQ/VXX use equity codes; VIX index must be requested separately as US..VIX.
    data = _opend_snapshot(["US.QQQ", "US.VXX"])
    for row in _iter_rows(data):
        code = str(_row_get(row, "code") or "").upper()
        last = _row_get(row, "last_price")
        if last is not None:
            out[code.split(".")[-1]] = {"price": float(last), "source": "OPEND"}
    try:
        vix_data = _opend_snapshot(["US..VIX"])
        for row in _iter_rows(vix_data):
            last = _row_get(row, "last_price")
            if last is not None:
                out["VIX"] = {"price": float(last), "source": "OPEND", "code": "US..VIX"}
                break
    except Exception as exc:
        out["VIX_ERROR"] = str(exc)
    return out


def candidate_vx_contracts():
    if _contract_cache["rows"] and datetime.datetime.now().timestamp() - _contract_cache["ts"] < 60:
        return _contract_cache["rows"]
    ctx = opend_ctx()
    if ctx is None:
        return []
    ret, data = ctx.get_stock_basicinfo(futu.Market.US, futu.SecurityType.FUTURE)
    if ret != getattr(futu, "RET_OK", 0):
        raise RuntimeError(str(data))
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    rows = []
    for row in _iter_rows(data):
        code = str(_row_get(row, "code") or "").upper()
        # Full-size VX monthlies only; VXM/main/next aliases are excluded.
        if not re.fullmatch(r"US\.VX\d{4}", code):
            continue
        ltd = str(_row_get(row, "last_trade_time") or "").strip()
        m = re.search(r"(20\d\d[-/]\d\d[-/]\d\d)", ltd)
        if not m:
            continue
        expiry = datetime.datetime.strptime(m.group(1).replace("/", "-"), "%Y-%m-%d")
        if expiry <= now:
            continue
        rows.append({"code": code, "expiry": expiry.strftime("%Y-%m-%d"), "last_trade_time": ltd})
    rows.sort(key=lambda x: x["expiry"])
    unique = []
    seen = set()
    for row in rows:
        if row["expiry"] in seen:
            continue
        seen.add(row["expiry"])
        unique.append(row)
    _contract_cache["rows"] = unique[:12]
    _contract_cache["ts"] = datetime.datetime.now().timestamp()
    return _contract_cache["rows"]


def opend_vx():
    ctx = opend_ctx()
    if ctx is None:
        raise RuntimeError("futu package unavailable")
    contracts = candidate_vx_contracts()
    if len(contracts) < 2:
        return {"ok": False, "reason": "less than two identifiable VX monthlies"}
    ret, data = ctx.get_market_snapshot([x["code"] for x in contracts[:8]])
    if ret != getattr(futu, "RET_OK", 0):
        return {"ok": False, "reason": str(data)}
    prices = {}
    for row in _iter_rows(data):
        code = str(_row_get(row, "code") or "")
        last = _row_get(row, "last_price")
        if last is not None:
            prices[code] = float(last)
    picked = []
    for contract in contracts:
        if contract["code"] in prices and prices[contract["code"]] > 0:
            picked.append({**contract, "last_price": prices[contract["code"]]})
        if len(picked) == 2:
            break
    return {
        "ok": len(picked) == 2,
        "m1": picked[0] if picked else None,
        "m2": picked[1] if len(picked) > 1 else None,
        "reason": None if len(picked) == 2 else "VX quote permission/price unavailable",
    }


def yahoo(sym):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(sym, safe='')}?range=1d&interval=1m&includePrePost=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(url=req, timeout=7, context=ssl.create_default_context()) as response:
        data = json.load(response)
    return data["chart"]["result"][0]["meta"].get("regularMarketPrice")


def secondary_vx():
    if _db is None:
        return {"ok": False, "status": "UNAVAILABLE", "reason": "Databento provider module unavailable"}
    if not _db.configured():
        return {"ok": False, "status": "UNCONFIGURED", "reason": "Set DATABENTO_API_KEY to enable secondary VX source"}
    try:
        return _db.latest()
    except Exception as exc:
        return {"ok": False, "status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}


def snapshot():
    out = {
        "source": "NONE",
        "timestamp": now_iso(),
        "qqq": None, "vxx": None, "vix": None,
        "m1": None, "m2": None,
        "m1_code": None, "m2_code": None,
        "term_source": "BLOCKED",
        "term_status": "BLOCKED",
        "source_chain": [],
        "errors": {},
    }

    # Spot: OpenD first, Yahoo per-field fallback.
    try:
        spots = opend_spots()
        for key in ("QQQ", "VXX", "VIX"):
            if key in spots:
                out["qqq" if key == "QQQ" else key.lower()] = spots[key]["price"]
        out["source_chain"].append("OPEND")
        out["spot_source"] = {k.lower(): spots.get(k, {}).get("source") for k in ("QQQ", "VXX", "VIX")}
    except Exception as exc:
        out["errors"]["opend_spot"] = str(exc)

    for key, sym in (("qqq", "QQQ"), ("vxx", "VXX"), ("vix", "^VIX")):
        if out[key] is not None:
            continue
        try:
            out[key] = float(yahoo(sym))
            out["source_chain"].append(f"YAHOO_{key.upper()}")
        except Exception as exc:
            out["errors"][f"yahoo_{key}"] = str(exc)

    # Term structure: OpenD, then licensed Databento CFE. Never synthesize M1/M2.
    try:
        vx = opend_vx()
        if vx.get("ok"):
            out["m1"] = vx["m1"]["last_price"]
            out["m2"] = vx["m2"]["last_price"]
            out["m1_code"] = vx["m1"]["code"]
            out["m2_code"] = vx["m2"]["code"]
            out["m1_expiry"] = vx["m1"]["expiry"]
            out["m2_expiry"] = vx["m2"]["expiry"]
            out["term_source"] = "OPEND"
            out["term_status"] = "LIVE"
            out["source_chain"].append("OPEND_VX")
        else:
            out["errors"]["opend_vx"] = vx.get("reason")
    except Exception as exc:
        out["errors"]["opend_vx"] = str(exc)

    if out["m1"] is None or out["m2"] is None:
        db = secondary_vx()
        out["secondary_vx"] = db
        if db.get("ok"):
            m1, m2 = db["m1"], db["m2"]
            out["m1"] = m1.get("mid") or m1.get("last")
            out["m2"] = m2.get("mid") or m2.get("last")
            out["m1_code"] = m1.get("raw_symbol")
            out["m2_code"] = m2.get("raw_symbol")
            out["m1_expiry"] = m1.get("expiry")
            out["m2_expiry"] = m2.get("expiry")
            out["term_source"] = "DATABENTO_CFE"
            out["term_status"] = "LIVE"
            out["source_chain"].append("DATABENTO_CFE_VX")
        else:
            out["errors"]["databento_vx"] = db.get("reason")

    if out["m1"] is not None and out["m2"] is not None:
        out["term_spread"] = (out["m2"] - out["m1"]) / out["m1"] if out["m1"] else None
    else:
        out["term_spread"] = None
        out["term_status"] = "BLOCKED"

    out["source"] = "+".join(dict.fromkeys(out["source_chain"])) or "NONE"
    return out


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path.startswith("/api/health"):
            payload = {
                "ok": True,
                "opend_package": futu is not None,
                "opend": f"{OPEND_HOST}:{OPEND_PORT}",
                "databento": _db.status() if _db else {"available": False},
            }
            raw = json.dumps(payload).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(raw); return

        if self.path.startswith("/api/snapshot"):
            try:
                raw = json.dumps(snapshot()).encode(); code = 200
            except Exception as exc:
                raw = json.dumps({"error": str(exc)}).encode(); code = 502
            self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(raw); return

        if self.path.startswith("/api/options"):
            query = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(query.query)
            symbol = params.get("symbol", ["QQQ"])[0].upper()
            if symbol not in {"QQQ", "VXX"}:
                self.send_error(400, "symbol must be QQQ or VXX"); return
            try:
                url = f"https://query2.finance.yahoo.com/v7/finance/options/{urllib.parse.quote(symbol, safe='')}"
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8, context=ssl.create_default_context()) as response:
                    payload = json.load(response)
                raw = json.dumps(payload).encode(); code = 200
            except Exception as exc:
                raw = json.dumps({"error": str(exc)}).encode(); code = 502
            self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(raw); return

        return super().do_GET()


if __name__ == "__main__":
    print(f"QQQ Hybrid Deployment Terminal V2 -> http://{HOST}:{PORT}")
    print(f"OpenD: {OPEND_HOST}:{OPEND_PORT} (read-only)")
    print("Secondary VX: Databento CFE when DATABENTO_API_KEY is configured")
    print("No broker order routing.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
