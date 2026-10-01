from __future__ import annotations
import tempfile
from pathlib import Path
from .ledger import InstanceLedger, InstanceLedgerError, sha256_json
from .run_instance import apply_deal, manual_apply_trade, manual_position_snapshot, manual_book_pnl_preview

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

def test_manual_adjustable_book_tracks_realized_pnl_without_touching_broker_book():
    lots=[]
    pnl,_=manual_apply_trade(lots,action="ADD",code="US.QQQ.TEST",qty=2,price=5.0,lot_size=100,trade_id="M1",timestamp="2026-10-01T00:00:00+00:00")
    assert pnl==0.0
    pnl,_=manual_apply_trade(lots,action="REDUCE",code="US.QQQ.TEST",qty=1,price=7.0,lot_size=100,trade_id="M2",timestamp="2026-10-01T00:01:00+00:00")
    assert pnl==200.0
    pos=manual_position_snapshot(lots)
    assert pos[0]["qty"]==1
    assert pos[0]["avg_cost"]==5.0


def test_manual_far_short_book_tracks_cover_pnl():
    lots=[]
    manual_apply_trade(lots,action="SELL_FAR",code="US.QQQ.TEST",qty=10,price=2.0,lot_size=100,trade_id="M3",timestamp="2026-10-01T00:02:00+00:00")
    pnl,_=manual_apply_trade(lots,action="BUY_BACK_FAR",code="US.QQQ.TEST",qty=4,price=1.25,lot_size=100,trade_id="M4",timestamp="2026-10-01T00:03:00+00:00")
    assert pnl==300.0
    pos=manual_position_snapshot(lots)
    assert pos[0]["side"]=="SHORT"
    assert pos[0]["qty"]==6

def test_manual_pnl_preview_does_not_mutate_book():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"LONG","qty":2,"avg_price":5.0,"lot_size":100,"status":"OPEN"}]
    p=manual_book_pnl_preview(lots,action="REDUCE",code="US.QQQ.TEST",qty=1,price=7.0,lot_size=100)
    assert p["realized_pnl_preview"]==200.0
    assert p["matched_qty"]==1
    assert lots[0]["qty"]==2


def test_manual_pnl_preview_blocks_over_reduce():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"LONG","qty":1,"avg_price":5.0,"lot_size":100,"status":"OPEN"}]
    p=manual_book_pnl_preview(lots,action="REDUCE",code="US.QQQ.TEST",qty=2,price=7.0,lot_size=100)
    assert p["remaining_unmatched"]==1

