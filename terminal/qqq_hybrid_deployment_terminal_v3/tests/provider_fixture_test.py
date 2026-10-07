
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


# F2 — Cboe payload observation date must not use fetch clock.
import datetime as dt
import io
import json
from zoneinfo import ZoneInfo
import providers.cboe_delayed_vx as cboe
import server

assert cboe.payload_asof({"lastUpdate": "2026-10-07T23:30:00-05:00"})[:2] == ("2026-10-08", "PAYLOAD_LAST_UPDATE")
assert cboe.payload_asof({"lastUpdate": "2026-10-08T03:59:00Z"})[0] == "2026-10-07"
assert cboe.payload_asof({})[:2] == (None, "MISSING_LAST_UPDATE")
assert cboe.payload_asof({"lastUpdate": "2026-10-07T17:05:19"})[:2] == (None, "UNPARSEABLE_LAST_UPDATE")

assert server._opend_market_day("2026-10-08 00:15:00") == "2026-10-08"
assert server._opend_market_day("2026-10-07 23:59:59") == "2026-10-07"
assert server._opend_market_day("") is None
assert server._epoch_market_day(1791410719) is not None

NOW = dt.datetime(2026, 10, 7, 22, 12, tzinfo=dt.timezone.utc)
ROWS = [
    {"symbol": "VX41/V6", "expiration": "10/14/2026", "settlement": 17.3, "last_price": 17.3},
    {"symbol": "VX/V6", "expiration": "10/21/2026", "settlement": 17.0, "last_price": 17.0},
    {"symbol": "VX/X6", "expiration": "11/18/2026", "settlement": 18.0, "last_price": 18.0},
]
class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): return False
real_urlopen = cboe.urllib.request.urlopen
cboe.urllib.request.urlopen = lambda req, timeout=20: Resp(json.dumps({"lastUpdate":"2026-10-01T16:00:00-05:00","data":ROWS}).encode("utf-8"))
try:
    old = cboe.fetch(now=NOW)
finally:
    cboe.urllib.request.urlopen = real_urlopen
assert old["data_asof"] == "2026-10-01"
assert old["fetched_at"] == NOW.isoformat()
assert old["m1"]["symbol"] == "VX/V6" and old["m2"]["symbol"] == "VX/X6"
print("Cboe/OpenD/spot F2 provenance helpers PASS")
