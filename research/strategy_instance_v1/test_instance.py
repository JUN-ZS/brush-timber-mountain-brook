from __future__ import annotations
import tempfile
from pathlib import Path
from .ledger import InstanceLedger, InstanceLedgerError, sha256_json
from .run_instance import apply_deal

def test_hash_chain():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"ledger.jsonl"; l=InstanceLedger(p,{"instance_id":"I"})
        l.append("INSTANCE_CREATED",instance_id="I",cycle_id="C1",timestamp_utc="2026-10-01T00:00:00+00:00",payload={"x":1})
        l.append("MARK_TO_MARKET",instance_id="I",cycle_id="C1",timestamp_utc="2026-10-01T00:00:01+00:00",payload={"pnl":12.5})
        assert l.validate()["records"]==2
        p.write_text(p.read_text().replace('"pnl":12.5','"pnl":13.5'),encoding="utf-8")
        try: l.validate()
        except InstanceLedgerError as e: assert "HASH_MISMATCH" in str(e)
        else: raise AssertionError("tamper not detected")

def test_fifo_long_close():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"LONG","qty":2,"avg_price":5.0,"lot_size":100,"status":"OPEN"}]
    r=apply_deal(lots,{"deal_id":"D1","code":"US.QQQ.TEST","side":"SELL","qty":3,"price":6.0,"lot_size":100})
    assert r==200.0
    assert sum(x["qty"] for x in lots if x.get("status","OPEN")=="OPEN" and x["side"]=="SHORT")==1

def test_fifo_short_cover():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"SHORT","qty":2,"avg_price":7.0,"lot_size":100,"status":"OPEN"}]
    r=apply_deal(lots,{"deal_id":"D2","code":"US.QQQ.TEST","side":"BUY_BACK","qty":1,"price":4.0,"lot_size":100})
    assert r==300.0
    assert sum(x["qty"] for x in lots if x.get("status","OPEN")=="OPEN" and x["side"]=="SHORT")==1

def test_canonical_hash_order():
    assert sha256_json({"a":1,"b":2})==sha256_json({"b":2,"a":1})
