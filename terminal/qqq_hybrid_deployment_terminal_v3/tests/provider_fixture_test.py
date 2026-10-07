
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from providers.cboe_delayed_vx import _date, STANDARD

assert STANDARD.fullmatch("VX/V6")
assert STANDARD.fullmatch("VX/X6")
assert not STANDARD.fullmatch("VX40/V6")
assert not STANDARD.fullmatch("VXT/V6")
assert _date("10/21/2026").isoformat()=="2026-10-21"
print("Cboe provider filter PASS")

# ---------------------------------------------------------------------------
# F2: data_asof must come from the payload lastUpdate (New York date), never from
# the fetch clock. Fixtures: fresh, 6-day-old (engine STALE), missing (engine BLOCKED).
import datetime as dt
import io
import json
import subprocess

import providers.cboe_delayed_vx as cboe
from providers.cboe_delayed_vx import payload_asof
import server

# payload_asof: explicit New York conversion (EDT -4 / EST -5), offset required.
assert payload_asof({"lastUpdate": "2026-10-07T17:05:19.411998-05:00"})[:2] == ("2026-10-07", "PAYLOAD_LAST_UPDATE")
assert payload_asof({"lastUpdate": "2026-10-07T23:30:00-05:00"})[0] == "2026-10-08"   # 00:30 ET next day
assert payload_asof({"lastUpdate": "2026-10-08T03:59:00Z"})[0] == "2026-10-07"        # 23:59 EDT
assert payload_asof({"lastUpdate": "2026-10-08T04:00:00Z"})[0] == "2026-10-08"        # 00:00 EDT
assert payload_asof({"lastUpdate": "2026-12-01T04:30:00+00:00"})[0] == "2026-11-30"   # 23:30 EST
assert payload_asof({})[:2] == (None, "MISSING_LAST_UPDATE")
assert payload_asof({"lastUpdate": ""})[:2] == (None, "MISSING_LAST_UPDATE")
assert payload_asof({"lastUpdate": "yesterday"})[:2] == (None, "UNPARSEABLE_LAST_UPDATE")
assert payload_asof({"lastUpdate": "2026-10-07T17:05:19"})[:2] == (None, "UNPARSEABLE_LAST_UPDATE")  # naive: no guessing
assert payload_asof({"lastUpdate": 1791410719})[:2] == (None, "UNPARSEABLE_LAST_UPDATE")

NOW = dt.datetime(2026, 10, 7, 22, 12, 0, tzinfo=dt.timezone.utc)  # 18:12 ET, 06:12 HKT next day
ROWS = [
    {"symbol": "VX41/V6", "expiration": "10/14/2026", "settlement": 17.3, "last_price": 0.0},   # weekly: ignored
    {"symbol": "VX/V6", "expiration": "10/21/2026", "settlement": 17.0, "last_price": 17.0},
    {"symbol": "VX/X6", "expiration": "11/18/2026", "settlement": 18.0, "last_price": 18.0},
]


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fetch_fixture(payload):
    real = cboe.urllib.request.urlopen
    cboe.urllib.request.urlopen = lambda req, timeout=20: _Resp(json.dumps(payload).encode("utf-8"))
    try:
        return cboe.fetch(now=NOW)
    finally:
        cboe.urllib.request.urlopen = real


def engine_on(vx, today="2026-10-07", spot_asof="2026-10-07"):
    out = {"qqq": 750.0, "vxx": 20.0, "vix": 16.0, "m1": None, "m2": None, "term_slope": None,
           "term_source": "BLOCKED", "term_asof": None, "spot_asof": spot_asof,
           "provenance": {"qqq": "YAHOO", "vxx": "YAHOO", "vix": "YAHOO"}, "source_chain": [], "errors": {}}
    server.apply_cboe_vx(out, vx)
    js = r"""
const fs=require('fs'),vm=require('vm');globalThis.window={};
vm.runInThisContext(fs.readFileSync(process.argv[1],'utf8'));
const E=globalThis.window.HybridEngineV3;const live=JSON.parse(fs.readFileSync(0,'utf8'));
const d={...live,s:Number(live.term_slope),termAsOf:live.term_asof,spotAsOf:live.spot_asof,today:live.today};
const e=E.derive(d);process.stdout.write(JSON.stringify({state:e.state,action:e.action,blocked:e.blocked,code:e.health.code||null,status:e.health.status,ageDays:e.health.ageDays??null}));
"""
    res = subprocess.run(["node", "-e", js, str(ROOT / "engine.js")], input=json.dumps({**out, "today": today}),
                         capture_output=True, text=True, check=True)
    return out, json.loads(res.stdout)


fresh = fetch_fixture({"lastUpdate": "2026-10-07T17:05:19.411998-05:00", "data": ROWS})
assert fresh["ok"] is True and fresh["status"] == "LIVE_DELAYED", fresh
assert fresh["data_asof"] == "2026-10-07" and fresh["asof_status"] == "PAYLOAD_LAST_UPDATE", fresh
assert fresh["fetched_at"] == NOW.isoformat() and fresh["last_update"] == "2026-10-07T17:05:19.411998-05:00", fresh
assert (fresh["m1"]["symbol"], fresh["m2"]["symbol"]) == ("VX/V6", "VX/X6"), fresh
snap, eng = engine_on(fresh)
assert snap["term_asof"] == "2026-10-07" and snap["term_fetched_at"] == NOW.isoformat(), snap
assert eng["status"] == "FRESH" and eng["state"] == "CARRY" and eng["ageDays"] == 0, eng

old = fetch_fixture({"lastUpdate": "2026-10-01T16:00:00-05:00", "data": ROWS})
assert old["data_asof"] == "2026-10-01", old           # payload date, NOT the fetch date 2026-10-07
assert old["fetched_at"] == NOW.isoformat(), old
_, eng = engine_on(old)
assert eng["state"] == "DATA STALE" and eng["blocked"] is True and eng["ageDays"] == 6, eng

missing = fetch_fixture({"data": ROWS})
assert missing["ok"] is True and missing["data_asof"] is None, missing   # never falls back to now
assert missing["status"] == "UNDATED_PAYLOAD" and missing["asof_status"] == "MISSING_LAST_UPDATE", missing
snap, eng = engine_on(missing)
assert snap["term_asof"] is None, snap
assert eng["state"] == "DATA BLOCKED" and eng["code"] == "TERM_DATE_INVALID" and eng["blocked"] is True, eng

junk = fetch_fixture({"lastUpdate": "not-a-time", "data": ROWS})
assert junk["data_asof"] is None and junk["asof_status"] == "UNPARSEABLE_LAST_UPDATE", junk
_, eng = engine_on(junk)
assert eng["state"] == "DATA BLOCKED" and eng["code"] == "TERM_DATE_INVALID", eng

print("Cboe provider F2 payload-date PASS (fresh FRESH · 6d STALE · missing/unparseable BLOCKED)")
