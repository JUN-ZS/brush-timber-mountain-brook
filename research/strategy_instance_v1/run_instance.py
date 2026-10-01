import argparse, hashlib, json, math, os, tempfile, threading, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from contextlib import contextmanager
from pathlib import Path
from .ledger import InstanceLedger, sha256_json
from .performance_tape import build_performance_tape, classify_relationship
from ..live_hedge_v1.campaign import choose_primary_action
from ..evidence_v1.identity import runtime_identity
from ..live_hedge_v1.campaign import is_qqq_option_code
from ..live_hedge_v1.engine import (
    Contract,
    Order,
    Position,
    ensure_gamma_history_schema,
    gamma_baseline_from_history,
    plan,
    select_far,
    select_near,
)
from ..live_hedge_v1.futu_reader import LiveFutuReader
from ..live_hedge_v1.futu_trade_reader import FutuTradeReader

ROOT=Path("research/strategy_instance_v1/instances")
MANIFEST_SCHEMA="STRATEGY_INSTANCE_MANIFEST.v1"
STATE_SCHEMA="STRATEGY_INSTANCE_STATE.v1"
PLAN_MATCH_MAX_MINUTES = 15

def now():
    return datetime.now(timezone.utc).isoformat()

_US_EXCHANGE_TZ = ZoneInfo("America/New_York")


def dt(x):
    try:
        z=datetime.fromisoformat(str(x).replace("Z","+00:00"))
        if z.tzinfo is None:
            z=z.replace(tzinfo=_US_EXCHANGE_TZ)
        return z.astimezone(timezone.utc)
    except (TypeError, ValueError): return None

def after(a,b):
    da,db=dt(a),dt(b)
    return bool(da and db and da>db)

def gap_minutes(a,b):
    da,db=dt(a),dt(b)
    return None if not da or not db else max(0.0,(da-db).total_seconds()/60.0)

def sf(x):
    try:
        y=float(x); return y if math.isfinite(y) else 0.0
    except Exception: return 0.0

def si(x):
    try: return int(float(x or 0))
    except Exception: return 0


_INSTANCE_THREAD_LOCKS = {}
_INSTANCE_THREAD_LOCKS_GUARD = threading.Lock()

def _instance_lock_path(repo, instance_id):
    key = hashlib.sha256(
        f"{Path(repo).resolve()}::{str(instance_id)}".encode("utf-8")
    ).hexdigest()
    return Path(tempfile.gettempdir()) / f"qqq-strategy-instance-{key}.lock"


@contextmanager
def instance_mutation_lock(repo, instance_id):
    """Serialize one strategy-instance mutation across threads and processes."""
    lock_path = _instance_lock_path(repo, instance_id)
    key = str(lock_path)
    with _INSTANCE_THREAD_LOCKS_GUARD:
        thread_lock = _INSTANCE_THREAD_LOCKS.setdefault(key, threading.Lock())
    with thread_lock:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as fh:
            fh.seek(0, os.SEEK_END)
            if fh.tell() == 0:
                fh.write(b"0")
                fh.flush()
            fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fh.seek(0)
                if os.name == "nt":
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

def idir(repo,i): return repo/ROOT/i
def mpath(repo,i): return idir(repo,i)/"manifest.json"
def spath(repo,i): return idir(repo,i)/"state.json"
def lpath(repo,i): return idir(repo,i)/"ledger.jsonl"

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)

def load(path,default=None):
    if not path.exists(): return {} if default is None else default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e: raise SystemExit(f"INVALID_JSON:{path}") from e

def mhash(m):
    x=dict(m); x.pop("manifest_hash",None); return sha256_json(x)

def _recover_mutable_state_from_ledger(m, s, l):
    """Rebuild mutable caches from the immutable instance ledger after crashes.

    Event append and state-file replacement are separate filesystem operations.
    On restart the ledger therefore wins for execution/manual history; the JSON
    state remains a cache that can be reconstructed deterministically.
    """
    rows = l._rows()

    broker_lots = init_lots(m)
    processed = []
    strategy_ids = []
    unattributed_ids = []
    seen = set()
    realized = 0.0
    for row in rows:
        et=str(row.get("event_type") or "").upper()
        if et not in {"EXECUTION_DETECTED","BROKER_EXECUTION_UNATTRIBUTED","BROKER_EXECUTION_PRE_INSTANCE"}:
            continue
        deal = dict((row.get("payload") or {}).get("deal") or {})
        did = str(deal.get("deal_id") or "")
        if not did:
            continue

        if et=="EXECUTION_DETECTED":
            deal_status=str(deal.get("attribution_status") or "").upper()
            attribution=(row.get("payload") or {}).get("attribution") or {}
            match=attribution.get("match") if isinstance(attribution,dict) else None
            if deal_status=="MATCHED_PREDECISION_PLAN" and did not in strategy_ids and isinstance(match,dict):
                consumed,delta,_=apply_strategy_attributed_deal(broker_lots,deal,match)
                if consumed==si(deal.get("qty")):
                    strategy_ids.append(did)
                    realized += delta
                elif did not in unattributed_ids:
                    # Immutable history exists, but the replay state cannot reproduce
                    # the recorded application safely; do not invent a new position.
                    unattributed_ids.append(did)
            elif did not in unattributed_ids:
                # Legacy or incomplete execution rows are quarantined.
                # Never silently promote them into the new strategy P&L lineage.
                unattributed_ids.append(did)
        else:
            if did not in unattributed_ids:
                unattributed_ids.append(did)

        if did not in seen:
            seen.add(did)
            processed.append(did)

    if processed:
        s["lots"] = broker_lots
        s["processed_deal_ids"] = processed
        s["strategy_deal_ids"] = strategy_ids
        s["unattributed_deal_ids"] = unattributed_ids
        s["realized_pnl"] = sf(realized)

    manual_rows = [
        row for row in rows
        if row.get("event_type") == "MANUAL_TRADE_RECORDED"
    ]
    if manual_rows:
        # One trade_id is the idempotency key; use the latest unique event.
        unique_manual = {}
        order = []
        for row in manual_rows:
            payload = row.get("payload") or {}
            trade_id = str(payload.get("trade_id") or "")
            key = trade_id or f"__SEQ__{row.get('event_seq')}"
            if key not in unique_manual:
                order.append(key)
            unique_manual[key] = payload
        latest = unique_manual[order[-1]]
        if isinstance(latest.get("lots_after"), list):
            s["manual_lots"] = json.loads(json.dumps(latest["lots_after"]))
        if latest.get("manual_realized_pnl_after") is not None:
            s["manual_realized_pnl"] = sf(latest["manual_realized_pnl_after"])
        s["manual_trade_count"] = len(order)


def load_instance(repo,i):
    m=load(mpath(repo,i))
    if not m: raise SystemExit(f"UNKNOWN_INSTANCE_ID:{i}")
    if m.get("manifest_hash")!=mhash(m): raise SystemExit("INSTANCE_MANIFEST_TAMPERED_OR_MUTATED")
    s=load(spath(repo,i),{"schema":STATE_SCHEMA,"schema_version":1,"instance_id":i,
        "processed_deal_ids":[],"strategy_deal_ids":[],"unattributed_deal_ids":[],"lots":[],"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,
        "last_snapshot_hash":None,"gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot","far_delta_abs":None,"last_reconcile":None,"cycle_count":0,"data_gaps":0,"manual_lots":init_lots(m),"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None})
    l=InstanceLedger(lpath(repo,i),{"instance_id":i,"manifest_hash":m["manifest_hash"],
       "strategy_id":m.get("strategy_id"),"strategy_version":m.get("strategy_version"),
       "research_engine_commit":m.get("research_engine_commit")})
    if "manual_lots" not in s or not isinstance(s.get("manual_lots"), list):
        s["manual_lots"]=init_lots(m)
    elif s["manual_lots"] and "avg_price" not in s["manual_lots"][0] and "avg_cost" in s["manual_lots"][0]:
        # Legacy/partially initialized state: derive the separate manual book
        # from immutable T0, never from mutable broker lots.
        s["manual_lots"]=init_lots(m)
    s.setdefault("strategy_deal_ids",[])
    s.setdefault("unattributed_deal_ids",[])
    s.setdefault("manual_realized_pnl",0.0)
    s.setdefault("manual_trade_count",0)
    s.setdefault("manual_last_mark",None)
    l.validate()
    _recover_mutable_state_from_ledger(m, s, l)
    return m,s,l

def pos_spec(x):
    p=[a.strip() for a in x.split(",")]
    if len(p) not in (4,5): raise SystemExit("POSITION_FORMAT=CODE,SIDE,QTY,AVG_COST[,LOT_SIZE]")
    side=p[1].upper()
    if side not in ("LONG","SHORT"): raise SystemExit("POSITION_SIDE=LONG|SHORT")
    code=p[0].upper()
    if not is_qqq_option_code(code): raise SystemExit("POSITION_CODE_MUST_BE_QQQ_OPTION")
    return {"code":code,"side":side,"qty":max(0,si(p[2])),"avg_cost":max(0,sf(p[3])),
            "lot_size":max(1,si(p[4]) if len(p)==5 else 100),"source":"USER_INITIAL"}

def init_lots(m):
    return [{"lot_id":f"T0-{n:04d}","code":p["code"],"side":p["side"],"qty":si(p["qty"]),
             "avg_price":sf(p["avg_cost"]),"lot_size":max(1,si(p.get("lot_size")) or 100),
             "opened_at":m["start_at_utc"],"source":"USER_INITIAL","status":"OPEN"}
            for n,p in enumerate(m["initial_positions"],1) if si(p["qty"])>0]

def close_fifo(lots,code,side,qty,price,lot_size):
    rem=qty; pnl=0.0
    for l in lots:
        if rem<=0: break
        if l.get("status","OPEN")!="OPEN" or str(l.get("code","")).upper()!=code.upper() or str(l.get("side")).upper()!=side: continue
        take=min(rem,si(l["qty"])); entry=sf(l["avg_price"]); size=max(1,si(l.get("lot_size")) or lot_size or 100)
        pnl += ((price-entry) if side=="LONG" else (entry-price))*take*size
        l["qty"]=si(l["qty"])-take
        if l["qty"]<=0: l["qty"]=0; l["status"]="CLOSED"
        rem-=take
    return rem,pnl

def _open_lot_qty(lots,code,side):
    return sum(
        si(x.get("qty"))
        for x in lots
        if str(x.get("status","OPEN")).upper()=="OPEN"
        and str(x.get("code","")).upper()==str(code).upper()
        and str(x.get("side","")).upper()==str(side).upper()
    )


def apply_strategy_attributed_deal(lots,d,match):
    """Apply a plan-linked broker deal using the plan's expected position side.

    The broker transaction verb alone is not enough to know whether BUY closes a
    short or opens a long. The matched strategy leg supplies that semantic side.
    Close quantities are capped by currently managed lots so overfills cannot
    manufacture an opposite strategy position.
    """
    code=str(d.get("code","")).upper()
    broker_side=str(d.get("side","")).upper()
    q=si(d.get("qty"))
    px=sf(d.get("price"))
    size=max(1,si(d.get("lot_size")) or 100)
    candidate=(match or {}).get("candidate") or {}
    action=str((match or {}).get("action") or "").upper()
    if q<=0 or px<=0 or not code:
        return 0,0.0,"INVALID"
    if action=="CLOSE_CAMPAIGN_EMERGENCY":
        expected_side=str(candidate.get("expected_side") or "").upper()
        if not expected_side:
            expected_side="SHORT" if broker_side=="BUY" else "LONG" if broker_side=="SELL" else ""
    elif action=="SELL_FAR" or (
        action=="REPAIR_FAR" and str(candidate.get("direction","")).upper()=="ADD"
    ):
        expected_side="SHORT"
    elif action=="REPAIR_FAR" and str(candidate.get("direction","")).upper()=="REDUCE":
        expected_side="SHORT"
    else:
        expected_side="LONG"

    if expected_side=="LONG":
        if broker_side=="BUY":
            apply_deal(lots,dict(d))
            return q,0.0,"OPEN_LONG"
        if broker_side=="SELL":
            avail=_open_lot_qty(lots,code,"LONG")
            consume=min(q,avail)
            if consume<=0:
                return 0,0.0,"NO_MANAGED_LONG"
            pnl=close_fifo(lots,code,"LONG",consume,px,size)[1]
            return consume,pnl,"CLOSE_LONG"
    elif expected_side=="SHORT":
        if broker_side in {"SELL","SELL_SHORT"}:
            lot={"lot_id":f"D-{d.get('deal_id','X')}-S","code":code,"side":"SHORT",
                 "qty":q,"avg_price":px,"lot_size":size,"opened_at":d.get("created_at"),
                 "source":"BROKER_DEAL","status":"OPEN"}
            lots.append(lot)
            return q,0.0,"OPEN_SHORT"
        if broker_side in {"BUY","BUY_BACK"}:
            avail=_open_lot_qty(lots,code,"SHORT")
            consume=min(q,avail)
            if consume<=0:
                return 0,0.0,"NO_MANAGED_SHORT"
            pnl=close_fifo(lots,code,"SHORT",consume,px,size)[1]
            return consume,pnl,"CLOSE_SHORT"
    return 0,0.0,"SIDE_MISMATCH"


def apply_deal(lots,d):
    code=str(d.get("code","")); side=str(d.get("side","")).upper(); q=si(d.get("qty")); px=sf(d.get("price")); size=max(1,si(d.get("lot_size")) or 100)
    if not code or q<=0 or px<=0: return 0.0
    if side=="BUY":
        lots.append({"lot_id":f"D-{d.get('deal_id','X')}-L","code":code,"side":"LONG","qty":q,"avg_price":px,"lot_size":size,"opened_at":d.get("created_at"),"source":"BROKER_DEAL","status":"OPEN"}); return 0.0
    if side=="BUY_BACK":
        return close_fifo(lots,code,"SHORT",q,px,size)[1]
    if side=="SELL":
        rem,pnl=close_fifo(lots,code,"LONG",q,px,size)
        if rem:
            lots.append({"lot_id":f"D-{d.get('deal_id','X')}-S","code":code,"side":"SHORT","qty":rem,"avg_price":px,"lot_size":size,"opened_at":d.get("created_at"),"source":"BROKER_DEAL","status":"OPEN"})
        return pnl
    if side=="SELL_SHORT":
        lots.append({"lot_id":f"D-{d.get('deal_id','X')}-S","code":code,"side":"SHORT","qty":q,"avg_price":px,"lot_size":size,"opened_at":d.get("created_at"),"source":"BROKER_DEAL","status":"OPEN"}); return 0.0
    return 0.0

def manual_apply_trade(lots, *, action, code, qty, price, lot_size, trade_id, timestamp):
    """Apply a user-entered execution to the separate manual operator book.

    This book is intentionally independent from broker-observed lots/pnl. It
    is for the user's alternate adjustable strategy path; it never changes
    broker reconciliation or masquerades as broker evidence.
    """
    action = str(action).upper()
    code = str(code).strip()
    q = si(qty)
    px = sf(price)
    size = max(1, si(lot_size) or 100)
    if not code or q <= 0 or px <= 0:
        raise SystemExit("MANUAL_TRADE_INVALID")
    if action == "ADD":
        lots.append({
            "lot_id": f"M-{trade_id}-L",
            "code": code,
            "side": "LONG",
            "qty": q,
            "avg_price": px,
            "lot_size": size,
            "opened_at": timestamp,
            "source": "USER_MANUAL",
            "status": "OPEN",
        })
        return 0.0, 0
    if action == "REDUCE":
        rem, pnl = close_fifo(lots, code, "LONG", q, px, size)
        if rem:
            raise SystemExit(f"MANUAL_REDUCE_EXCEEDS_POSITION:{code}:{rem}")
        return pnl, 0
    if action == "SELL_FAR":
        lots.append({
            "lot_id": f"M-{trade_id}-S",
            "code": code,
            "side": "SHORT",
            "qty": q,
            "avg_price": px,
            "lot_size": size,
            "opened_at": timestamp,
            "source": "USER_MANUAL",
            "status": "OPEN",
        })
        return 0.0, 0
    if action == "BUY_BACK_FAR":
        rem, pnl = close_fifo(lots, code, "SHORT", q, px, size)
        if rem:
            raise SystemExit(f"MANUAL_COVER_EXCEEDS_POSITION:{code}:{rem}")
        return pnl, 0
    raise SystemExit("MANUAL_ACTION=ADD|REDUCE|SELL_FAR|BUY_BACK_FAR")

def manual_position_snapshot(lots):
    out = {}
    for l in lots:
        if l.get("status","OPEN") != "OPEN" or si(l.get("qty")) <= 0:
            continue
        k=(str(l["code"]).upper(),str(l["side"]).upper())
        row=out.setdefault(k, {"code":l["code"],"side":l["side"],"qty":0,"avg_cost":0.0,"notional":0.0})
        q=si(l["qty"]); px=sf(l["avg_price"]); row["qty"] += q
        row["notional"] += q*px
        row["avg_cost"] = row["notional"]/row["qty"] if row["qty"] else 0.0
    return sorted(out.values(), key=lambda x:(x["side"],x["code"]))

def mark_lots(lots, cmap, quotes):
    rows=[]; unreal=0.0; signed_mv=0.0
    for l in lots:
        if l.get("status","OPEN")!="OPEN" or si(l.get("qty"))<=0:
            continue
        code=str(l["code"]); q=quotes.get(code,{})
        mid=q.get("mid")
        bid=q.get("bid"); ask=q.get("ask")
        if mid is None and bid is not None and ask is not None and float(ask)>=float(bid):
            mid=(float(bid)+float(ask))/2
        if mid is None:
            rows.append({"code":code,"side":l.get("side"),"qty":si(l.get("qty")),"avg_cost":sf(l.get("avg_price")),"status":"NO_MARK"})
            continue
        size=max(1,si(l.get("lot_size")) or (cmap.get(code).lot_size if cmap.get(code) else 100))
        px=sf(l.get("avg_price")); qty=si(l.get("qty")); side=str(l.get("side")).upper()
        u=((float(mid)-px) if side=="LONG" else (px-float(mid)))*qty*size
        unreal += u
        signed_mv += (float(mid)*qty*size)*(1 if side=="LONG" else -1)
        rows.append({"code":code,"side":side,"qty":qty,"avg_cost":px,"lot_size":size,"mid":float(mid),"unrealized_pnl":u,"status":"MARKED"})
    return {"rows":rows,"unrealized_pnl":unreal,"signed_market_value":signed_mv,
            "status":"OK" if rows and all(x["status"]=="MARKED" for x in rows) else ("PARTIAL" if rows else "EMPTY")}

def option_positions(ps):
    return [
        p for p in ps
        if is_qqq_option_code(p.get("code",""))
        and str(p.get("side","")).upper() in ("LONG","SHORT")
        and si(p.get("qty"))>0
    ]

def contracts_map(snap):
    out={}
    quotes=snap.get("quotes",{}) or {}
    for x in snap.get("contracts",[]):
        if x.get("code"):
            code=str(x["code"])
            q=quotes.get(code,{}) or {}
            out[code]=Contract(
                code,
                str(x.get("right","CALL")).upper(),
                sf(x.get("strike")),
                str(x.get("expiry","")),
                si(x.get("dte")),
                q.get("bid",x.get("bid")),
                q.get("ask",x.get("ask")),
                q.get("delta",x.get("delta")),
                q.get("gamma",x.get("gamma")),
                q.get("iv",x.get("iv")),
                max(1,si(x.get("lot_size")) or 100),
                q.get("volume",x.get("volume")),
            )
    return out

def marks(ps,cmap,quotes):
    rows=[]; unreal=0.0; signed_mv=0.0
    for p in option_positions(ps):
        code=str(p["code"]); q=quotes.get(code,{})
        bid=q.get("bid"); ask=q.get("ask"); mid=q.get("mid")
        if mid is None and bid is not None and ask is not None and float(ask)>=float(bid): mid=(float(bid)+float(ask))/2
        if mid is None: rows.append({"code":code,"status":"NO_MARK"}); continue
        meta=cmap.get(code); size=meta.lot_size if meta else 100; qty=si(p["qty"]); avg=sf(p["avg_cost"]); side=str(p["side"]).upper()
        u=((float(mid)-avg) if side=="LONG" else (avg-float(mid)))*qty*size
        unreal+=u; signed_mv+=(float(mid)*qty*size)*(1 if side=="LONG" else -1)
        rows.append({"code":code,"side":side,"qty":qty,"avg_cost":avg,"lot_size":size,"mid":float(mid),"unrealized_pnl":u,"status":"MARKED"})
    return {"rows":rows,"unrealized_pnl":unreal,"signed_market_value":signed_mv,
            "status":"OK" if rows and all(x["status"]=="MARKED" for x in rows) else ("PARTIAL" if rows else "EMPTY")}

def _aggregate_lot_qty(lots):
    out={}
    for lot in lots or []:
        if str(lot.get("status","OPEN")).upper()!="OPEN" or si(lot.get("qty"))<=0:
            continue
        code=str(lot.get("code","")).upper()
        side=str(lot.get("side","")).upper()
        if code and side in {"LONG","SHORT"}:
            out[(code,side)]=out.get((code,side),0)+si(lot.get("qty"))
    return out


def managed_position_view(ps,lots):
    """Project account positions onto strategy-owned quantities only."""
    tracked=_aggregate_lot_qty(lots)
    observed={}
    for p in option_positions(ps):
        key=(str(p.get("code","")).upper(),str(p.get("side","")).upper())
        if key in tracked:
            observed[key]=observed.get(key,0)+si(p.get("qty"))
    out=[]
    for (code,side),tracked_qty in tracked.items():
        broker_qty=observed.get((code,side),0)
        qty=min(tracked_qty,broker_qty)
        if qty<=0:
            continue
        src=next((p for p in ps if str(p.get("code","")).upper()==code and str(p.get("side","")).upper()==side),{})
        out.append({
            "code":code,"side":side,"qty":qty,
            "avg_cost":sf(src.get("avg_cost")),
            "lot_size":max(1,si(src.get("lot_size")) or 100),
            "source":"BROKER_OBSERVED_STRATEGY_OWNED",
        })
    return out


def reconcile(lots,ps):
    tracked=_aggregate_lot_qty(lots)
    broker={}
    for p in option_positions(ps):
        key=(str(p.get("code","")).upper(),str(p.get("side","")).upper())
        if key in tracked:
            broker[key]=broker.get(key,0)+si(p.get("qty"))
    return [
        {"code":code,"side":side,"lot_qty":tracked[(code,side)],"broker_qty":broker.get((code,side),0)}
        for code,side in sorted(tracked)
        if tracked[(code,side)]!=broker.get((code,side),0)
    ]


def _candidate_match(candidate,side,code):
    action=str(candidate.get("action","")).upper()
    code=str(code).upper()
    side=str(side).upper()
    c=str(candidate.get("code","")).upper()
    if action=="ROLL_NEAR":
        if side=="SELL" and code==c:
            return dict(candidate)
        if side=="BUY" and code==str(candidate.get("new_code","")).upper():
            return dict(candidate)
        return None
    if action=="CLOSE_CAMPAIGN_EMERGENCY":
        for leg in candidate.get("legs",[]) or []:
            if str(leg.get("code","")).upper()==code and str(leg.get("side","")).upper()==side:
                hit=dict(leg); hit["action"]=action; return hit
        return None
    if c!=code:
        return None
    expected={
        "ADD_NEAR":"BUY",
        "HARVEST_NEAR":"SELL",
        "REDUCE_NEAR":"SELL",
        "SELL_FAR":"SELL",
    }.get(action)
    if expected=="BUY":
        return candidate if side=="BUY" else None
    if expected=="SELL":
        return candidate if side in {"SELL","SELL_SHORT"} else None
    if action=="REPAIR_FAR":
        direction=str(candidate.get("direction","")).upper()
        if direction=="ADD" and side in {"SELL","SELL_SHORT"}:
            return candidate
        if direction=="REDUCE" and side in {"BUY","BUY_BACK"}:
            return candidate
    return None


def _plan_match_for_deal(rows,deal):
    code=str(deal.get("code","")).upper()
    side=str(deal.get("side","")).upper()
    deal_time=dt(deal.get("created_at"))
    if not code or not deal_time:
        return None
    for event in reversed(rows or []):
        if str(event.get("event_type","")).upper()!="STRATEGY_PLAN_OBSERVED":
            continue
        event_time=dt(event.get("timestamp_utc"))
        if not event_time or event_time>deal_time:
            continue
        age=gap_minutes(deal.get("created_at"),event.get("timestamp_utc"))
        if age is None or age>PLAN_MATCH_MAX_MINUTES:
            break
        plan_obj=(event.get("payload") or {}).get("plan") or {}
        primary=plan_obj.get("primary_candidate")
        if not isinstance(primary,dict):
            return None
        hit=_candidate_match(primary,side,code)
        if hit is not None:
            return {
                "event_seq":event.get("event_seq"),
                "candidate_index":0,
                "observed_at_utc":event.get("timestamp_utc"),
                "action":str(primary.get("action","")).upper(),
                "candidate":hit,
                "age_minutes":age,
                "match_basis":"PRIMARY_CANDIDATE_ONLY",
            }
        break
    return None


def _consumed_plan_qty(rows, plan_key):
    consumed=0
    for row in rows or []:
        if str(row.get("event_type") or "").upper()!="EXECUTION_DETECTED":
            continue
        payload=row.get("payload") or {}
        attribution=payload.get("attribution") or {}
        if attribution.get("plan_key") == plan_key:
            consumed += si((payload.get("deal") or {}).get("qty"))
    return consumed


def apply_strategy_ownership_close(lots, deal, broker_positions):
    """Close owned lots only when the current account snapshot uniquely matches them.

    This preserves observable T0 economics while refusing to infer which lot an
    aggregated account close consumed when external same-code inventory exists.
    """
    code=str(deal.get("code","")).upper()
    side=str(deal.get("side","")).upper()
    q=si(deal.get("qty"))
    px=sf(deal.get("price"))
    size=max(1,si(deal.get("lot_size")) or 100)
    if q<=0 or px<=0 or not code:
        return 0,0.0,"INVALID"
    target_side="LONG" if side=="SELL" else "SHORT" if side in {"BUY","BUY_BACK"} else ""
    if not target_side:
        return 0,0.0,"SIDE_NOT_CLOSE"
    tracked=_open_lot_qty(lots,code,target_side)
    if tracked<=0:
        return 0,0.0,f"NO_MANAGED_{target_side}"
    broker_qty=sum(
        si(p.get("qty"))
        for p in option_positions(broker_positions or [])
        if str(p.get("code","")).upper()==code
        and str(p.get("side","")).upper()==target_side
    )
    if broker_qty != tracked:
        return 0,0.0,"OWNERSHIP_SNAPSHOT_AMBIGUOUS"
    consume=min(q,tracked)
    if consume<=0:
        return 0,0.0,"NO_CONSUMPTION"
    pnl=close_fifo(lots,code,target_side,consume,px,size)[1]
    return consume,pnl,f"CLOSE_{target_side}_OWNERSHIP_DERIVED"


def attribute_broker_deal(rows,deal,used_plan_qty=None):
    q=si(deal.get("qty"))
    match=_plan_match_for_deal(rows,deal)
    if q<=0:
        return {"status":"UNATTRIBUTED","qty":0,"reason":"non_positive_quantity"}
    if not match:
        return {"status":"UNATTRIBUTED","qty":0,"reason":"no_recent_matching_strategy_plan"}
    expected=si((match.get("candidate") or {}).get("qty"))
    if expected<=0:
        return {"status":"UNATTRIBUTED","qty":0,"reason":"matched_candidate_has_no_positive_qty","match":match}
    key=(
        str(match.get("event_seq")),
        int(match.get("candidate_index",0)),
        str(match.get("action") or ""),
        str((match.get("candidate") or {}).get("code") or (match.get("candidate") or {}).get("new_code") or ""),
        str(deal.get("side") or "").upper(),
    )
    persisted=_consumed_plan_qty(rows,key)
    already=persisted + si((used_plan_qty or {}).get(key))
    remaining=max(0,expected-already)
    if remaining<=0:
        return {"status":"UNATTRIBUTED","qty":0,
                "reason":"strategy_plan_quantity_already_consumed",
                "match":match,"plan_key":key}
    qty=min(q,remaining)
    return {"status":"MATCHED_PREDECISION_PLAN","qty":qty,
            "unattributed_qty":q-qty,"match":match,"basis":"recent_strategy_plan_observation",
            "plan_key":key,"plan_remaining_before":remaining}


def instance_far_position(m, positions):
    """Select the single strategy far position or return None on ambiguity."""
    shorts = [
        p for p in positions
        if str(p.get("side", "")).upper() == "SHORT"
        and is_qqq_option_code(p.get("code", ""))
    ]
    hint = str(m.get("far_code_hint") or "").upper()
    if hint:
        matches = [p for p in shorts if str(p.get("code", "")).upper() == hint]
    else:
        matches = shorts if len(shorts) == 1 else []
    return matches[0] if len(matches) == 1 else None


def gamma_state_for_instance(state, far=None, spot=None):
    """Return sanitized prior-window gamma state using the canonical engine migration."""
    history = ensure_gamma_history_schema(state, spot=spot)
    baseline = gamma_baseline_from_history(history)
    previous_delta = state.get("far_delta_abs")
    return history, baseline, previous_delta
def strategy_plan(snap,ps,orders,cmap,quotes,m,near_lots=None,gamma_baseline=None,previous_far_delta_abs=None):
    market=snap["market"]; pos=[]
    for p in ps:
        c=cmap.get(str(p["code"])); q=quotes.get(str(p["code"]),{})
        pos.append(Position(str(p["code"]),str(p["side"]).upper(),si(p["qty"]),sf(p["avg_cost"]),
            c.strike if c else q.get("strike"),c.expiry if c else q.get("expiry"),c.dte if c else q.get("dte"),
            q.get("delta"),q.get("gamma")))
    os=[Order(str(o.get("order_id","")),str(o.get("code","")),str(o.get("side","")).upper(),si(o.get("qty")),o.get("price"),
              str(o.get("status","")).upper(),str(o.get("updated_at","")),str(o.get("created_at","")),si(o.get("dealt_qty")),o.get("dealt_avg_price")) for o in orders]
    unknown_qqq=[
        p for p in pos
        if is_qqq_option_code(p.code)
        and p.side not in {"LONG","SHORT"}
        and si(p.qty)>0
    ]
    if unknown_qqq:
        return {
            "status":"BLOCKED_UNKNOWN_POSITION_SIDE",
            "reason":"QQQ option position has unknown/missing position_side; strategy planning is fail-closed",
            "unknown_positions":[p.__dict__ for p in unknown_qqq],
        }
    shorts=[p for p in pos if p.side=="SHORT" and is_qqq_option_code(p.code)]
    active=bool(shorts)
    far=None
    hinted_far = instance_far_position(
        m,
        [p.__dict__ for p in pos],
    )
    far_hint = str(m.get("far_code_hint") or "").upper()
    far_candidates = [hinted_far] if hinted_far is not None else []
    if active and (
        len(shorts) != 1
        or len(far_candidates) != 1
    ):
        return {
            "status": "DATA_GAP",
            "reason": (
                "far ownership ambiguous or extra unmanaged QQQ SHORT exists"
                if not far_hint
                else "far_code_hint does not uniquely isolate the single managed QQQ SHORT"
            ),
            "short_codes": [str(p.code) for p in shorts],
            "far_code_hint": far_hint or None,
        }
    if far_candidates:
        p = far_candidates[0]
        p_code = str(p.get("code") if isinstance(p, dict) else p.code)
        c=cmap.get(p_code); q=quotes.get(p_code,{})
        if c:
            far=Contract(
                c.code,c.right,c.strike,c.expiry,c.dte,
                q.get("bid",c.bid),q.get("ask",c.ask),
                q.get("delta",c.delta),q.get("gamma",c.gamma),
                q.get("iv",c.iv),c.lot_size,c.volume,
            )
    spot=sf(market.get("spot"))
    if far is None and not active:
        far=select_far(list(cmap.values()),spot,si(m.get("far_dte")) or 120,sf(m.get("far_delta")) or .08)
    near=select_near(list(cmap.values()),spot,si(m.get("near_dte")) or 30)
    if near:
        q=quotes.get(near.code,{})
        near=Contract(
            near.code,near.right,near.strike,near.expiry,near.dte,
            q.get("bid",near.bid),q.get("ask",near.ask),
            q.get("delta",near.delta),q.get("gamma",near.gamma),
            q.get("iv",near.iv),near.lot_size,near.volume,
        )
    if active and far is None: return {"status":"DATA_GAP","reason":"active short far quote unavailable"}
    return plan(market=market,far=far,near=near,positions=pos,orders=os,signal_active=bool(market.get("signal_active")),
                far_campaign_active=active,quotes_by_code=quotes,near_lots=near_lots or [],
                gamma_baseline=gamma_baseline,previous_far_delta_abs=previous_far_delta_abs,
                now=datetime.now(timezone.utc))

def cycle(args):
    repo = Path(args.repo_root).resolve()
    with instance_mutation_lock(repo, args.instance_id):
        return _cycle_unlocked(args)


def _cycle_unlocked(args):
    repo=Path(args.repo_root).resolve(); m,s,l=load_instance(repo,args.instance_id); t=now()
    cid="CYCLE_"+t.replace(":","").replace("-","").replace(".",""); s["cycle_count"]=si(s.get("cycle_count"))+1
    try:
        history_start = None
        last_cycle = s.get("last_cycle_at")
        if last_cycle is None:
            history_start = m.get("start_at_utc") or m.get("created_at_utc")
        elif gap_minutes(t, last_cycle) is not None and gap_minutes(t, last_cycle) >= args.backfill_after_minutes:
            history_start = last_cycle
        tr=FutuTradeReader(args.host,args.port,real=not args.simulate).read(history_start=history_start)
        broker_codes=[p.get("code") for p in tr.get("positions",[]) if p.get("code")]
        manual_codes=[x.get("code") for x in s.get("manual_lots",[]) if x.get("code")]
        snapshot_codes=sorted(set(str(x) for x in broker_codes+manual_codes if x))
        snap=LiveFutuReader(args.host,args.port).snapshot(snapshot_codes)
    except Exception as e:
        s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"BROKER_READ","error":repr(e)},source="BROKER_OBSERVED")
        s["last_cycle_at"]=t; save(spath(repo,args.instance_id),s); print(json.dumps({"status":"DATA_GAP","error":repr(e)},ensure_ascii=False,indent=2)); return 2
    ps=tr.get("positions",[]); orders=tr.get("orders",[]); cmap=contracts_map(snap); quotes=snap.get("quotes",{})
    history_used=bool(tr.get("history_backfill_used"))
    seen=set(map(str,s.get("processed_deal_ids",[]))); new=[]; pre_instance=[]
    for d in tr.get("deals",[]):
        did=str(d.get("deal_id","") or "")
        if not did or did in seen or not after(d.get("created_at"),m.get("start_at_utc") or m["created_at_utc"]):
            continue
        if is_qqq_option_code(d.get("code","")):
            d=dict(d); c=cmap.get(str(d["code"])); d["lot_size"]=c.lot_size if c else 100
            deal_time=dt(d.get("created_at"))
            created_time=dt(m["created_at_utc"])
            if deal_time and created_time and deal_time<=created_time:
                pre_instance.append(d)
            else:
                new.append(d)
    for d in sorted(pre_instance,key=lambda x:(dt(x.get("created_at")) or datetime.max.replace(tzinfo=timezone.utc),str(x.get("deal_id")))):
        did=str(d["deal_id"])
        s["unattributed_deal_ids"].append(did)
        s["processed_deal_ids"].append(did)
        s["data_gaps"]=si(s.get("data_gaps"))+1
        l.append(
            "BROKER_EXECUTION_PRE_INSTANCE",
            instance_id=m["instance_id"],
            cycle_id=cid,
            timestamp_utc=t,
            payload={
                "deal":d,
                "economic_t0":m.get("start_at_utc"),
                "instance_created_at":m["created_at_utc"],
                "reason":"execution occurred after economic T0 but before instance recording existed; baseline cannot be reconstructed without relabeling",
            },
            source="BROKER_OBSERVED",
        )
    realized_delta=0.0
    prior_rows=l._rows()
    plan_usage={}
    for d in sorted(
        new,
        key=lambda x: (
            dt(x.get("created_at")) or datetime.max.replace(tzinfo=timezone.utc),
            str(x.get("deal_id")),
        ),
    ):
        did=str(d["deal_id"])
        original_qty=si(d.get("qty"))
        attribution=attribute_broker_deal(prior_rows,d,plan_usage)

        if attribution.get("status")=="MATCHED_PREDECISION_PLAN":
            match=attribution.get("match") or {}
            requested_qty=si(attribution.get("qty"))
            attr_deal=dict(d)
            attr_deal["qty"]=requested_qty
            attr_deal["attribution_status"]="MATCHED_PREDECISION_PLAN"
            attr_deal["attribution_grade"]="DERIVED_NO_INTENT_PROOF"
            attr_deal["attribution_basis"]="RECENT_PRIMARY_DECISION_TIMING_MATCH"
            attr_deal["attribution"]=match

            consumed,delta,application=apply_strategy_attributed_deal(
                s["lots"],attr_deal,match
            )
            if consumed>0:
                key=attribution.get("plan_key")
                plan_usage[key]=si(plan_usage.get(key))+consumed
                realized_delta += delta
                s["strategy_deal_ids"].append(did)
                attr_deal["qty"]=consumed
                attr_deal["strategy_application"]=application
                l.append(
                    "EXECUTION_DETECTED",
                    instance_id=m["instance_id"],
                    cycle_id=cid,
                    timestamp_utc=t,
                    payload={
                        "deal":attr_deal,
                        "original_deal_qty":original_qty,
                        "attribution":attribution,
                        "realized_pnl_delta":delta,
                    },
                    source="BROKER_OBSERVED",
                )

            extra=original_qty-consumed
            if extra>0:
                s["unattributed_deal_ids"].append(did)
                s["data_gaps"]=si(s.get("data_gaps"))+1
                l.append(
                    "BROKER_EXECUTION_UNATTRIBUTED",
                    instance_id=m["instance_id"],
                    cycle_id=cid,
                    timestamp_utc=t,
                    payload={
                        "deal":d,
                        "attributed_qty":consumed,
                        "unattributed_qty":extra,
                        "reason":"quantity_exceeded_plan_or_managed_position",
                        "attribution":attribution,
                    },
                    source="BROKER_OBSERVED",
                )
        else:
            # A close against an already-owned strategy lot remains part of the
            # actual campaign economics even when no recent strategy decision
            # proves intent. Mark it as ownership-derived, never FOLLOW_STRATEGY.
            close_qty,close_pnl,close_application=apply_strategy_ownership_close(s["lots"],d,ps)
            if close_qty>0:
                attr_deal=dict(d)
                attr_deal["qty"]=close_qty
                attr_deal["attribution_status"]="MATCHED_STRATEGY_OWNERSHIP_DERIVED"
                attr_deal["attribution_grade"]="DERIVED_NO_INTENT_PROOF"
                attr_deal["attribution_basis"]="STRATEGY_OWNED_LOT_CLOSE_SCOPE"
                attr_deal["strategy_application"]=close_application
                realized_delta += close_pnl
                s["strategy_deal_ids"].append(did)
                l.append(
                    "EXECUTION_DETECTED",
                    instance_id=m["instance_id"],
                    cycle_id=cid,
                    timestamp_utc=t,
                    payload={
                        "deal":attr_deal,
                        "original_deal_qty":si(d.get("qty")),
                        "attribution":{
                            "status":"MATCHED_STRATEGY_OWNERSHIP_DERIVED",
                            "qty":close_qty,
                            "attribution_grade":"DERIVED_NO_INTENT_PROOF",
                            "attribution_basis":"STRATEGY_OWNED_LOT_CLOSE_SCOPE",
                        },
                        "realized_pnl_delta":close_pnl,
                    },
                    source="BROKER_OBSERVED",
                )
                extra=si(d.get("qty"))-close_qty
                if extra>0:
                    s["unattributed_deal_ids"].append(did)
                    s["data_gaps"]=si(s.get("data_gaps"))+1
                    l.append(
                        "BROKER_EXECUTION_UNATTRIBUTED",
                        instance_id=m["instance_id"],
                        cycle_id=cid,
                        timestamp_utc=t,
                        payload={"deal":d,"attributed_qty":close_qty,"unattributed_qty":extra,
                                 "reason":"close_exceeded_or_ambiguous_strategy_ownership",
                                 "attribution_grade":"DERIVED_NO_INTENT_PROOF"},
                        source="BROKER_OBSERVED",
                    )
            else:
                s["unattributed_deal_ids"].append(did)
                s["data_gaps"]=si(s.get("data_gaps"))+1
                l.append(
                    "BROKER_EXECUTION_UNATTRIBUTED",
                    instance_id=m["instance_id"],
                    cycle_id=cid,
                    timestamp_utc=t,
                    payload={
                        "deal":d,
                        "attribution":attribution,
                        "reason":attribution.get("reason","no_strategy_attribution"),
                        "attribution_grade":"NO_ATTRIBUTION",
                    },
                    source="BROKER_OBSERVED",
                )
        s["processed_deal_ids"].append(did)
    s["realized_pnl"]=sf(s.get("realized_pnl"))+realized_delta
    mism=reconcile(s["lots"],ps); s["last_reconcile"]={"status":"MATCH" if not mism else "DATA_GAP","mismatches":mism,"checked_at_utc":t}
    if mism:
        s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"POSITION_RECONCILIATION","mismatches":mism},source="BROKER_OBSERVED")
    raw={"market":snap.get("market"),"connection":snap.get("connection"),"positions":ps,"orders":orders,
         "deals":tr.get("deals",[]),"deal_warning":tr.get("deal_warning"),"contracts":snap.get("contracts",[]),"quotes":quotes,
         "sources":{"market":snap.get("source"),"trade":tr.get("source")}}
    sh=sha256_json(raw); sr=idir(repo,args.instance_id)/"snapshots"/f"{cid}.json"; save(sr,raw); s["last_snapshot_hash"]=sh
    l.append("BROKER_CYCLE_OBSERVED",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,
             payload={"snapshot_sha256":sh,"snapshot_ref":str(sr.relative_to(repo)),"positions":len(ps),
                      "orders":len(orders),"new_deals":len(new),"reconcile":s["last_reconcile"],"deal_warning":tr.get("deal_warning"),
                      "history_backfill_used":history_used,"history_start":tr.get("history_start"),"history_end":tr.get("history_end")},source="BROKER_OBSERVED")
    managed_ps=managed_position_view(ps,s["lots"])
    broker_managed_mark=marks(managed_ps,cmap,quotes)
    mk=mark_lots(s["lots"],cmap,quotes)
    mk["broker_managed_unrealized_pnl"]=broker_managed_mark["unrealized_pnl"]
    mk["broker_managed_signed_market_value"]=broker_managed_mark["signed_market_value"]
    gross=s["realized_pnl"]+sf(mk["unrealized_pnl"])
    pnl_observation_status="OBSERVED_MATCHED" if not mism and mk["status"]=="OK" else "DATA_GAP"
    mmk=mark_lots(s.get("manual_lots",[]),cmap,quotes)
    # These values are updated only after the read-only strategy observation
    # consumes the prior-state window. They must still exist when observation
    # is disabled, because state persistence below is unconditional.
    gamma_history = list(s.get("gamma_history") or [])
    current_far_gamma_spot = None
    current_far_delta_abs = None
    s["manual_last_mark"]={"unrealized_pnl":mmk["unrealized_pnl"],"status":mmk["status"],"rows":mmk["rows"],"marked_at_utc":t}
    l.append("MARK_TO_MARKET",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={
        "snapshot_sha256":sh,"realized_pnl_gross":s["realized_pnl"],"unrealized_pnl_gross":mk["unrealized_pnl"],
        "gross_pnl":gross,"pnl_observation_status":pnl_observation_status,"signed_market_value":mk["signed_market_value"],"marks":mk["rows"],"status":mk["status"],"manual_book":{"realized_pnl":s["manual_realized_pnl"],"unrealized_pnl":mmk["unrealized_pnl"],"total_pnl":s["manual_realized_pnl"]+sf(mmk["unrealized_pnl"]),"marks":mmk["rows"],"status":mmk["status"]}})
    strategy_observation_ok = False
    if args.observe_strategy_plan and snap.get("status")=="OK":
        try:
            gamma_history, gamma_baseline, previous_far_delta_abs = gamma_state_for_instance(
                s, None, sf(snap.get("market", {}).get("spot"))
            )
            current_far = None
            current_far_gamma_spot = None
            current_far_delta_abs = None
            current_far = instance_far_position(m, ps)
            if current_far:
                q = quotes.get(str(current_far.get("code")), {})
                spot_now = sf(snap.get("market", {}).get("spot"))
                if q.get("gamma") is not None and spot_now > 0:
                    current_far_gamma_spot = abs(float(q["gamma"])) * spot_now
                if q.get("delta") is not None:
                    current_far_delta_abs = abs(float(q["delta"]))
                    previous_far_delta_abs = s.get("far_delta_abs")
            sp=strategy_plan(
                snap, ps, orders, cmap, quotes, m,
                near_lots=s.get("lots", []),
                gamma_baseline=gamma_baseline,
                previous_far_delta_abs=previous_far_delta_abs,
            )
            primary_candidate=choose_primary_action(sp.get("candidate_actions",[]) or [])
            sp_observed=json.loads(json.dumps(sp))
            sp_observed["primary_candidate"]=primary_candidate
            l.append("STRATEGY_PLAN_OBSERVED",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,
                     payload={
                         "plan":sp_observed,
                         "execution":"READ_ONLY_OBSERVATION",
                         "pre_decision_snapshot_sha256":sh,
                         "attribution_window_minutes":PLAN_MATCH_MAX_MINUTES,
                         "primary_candidate":primary_candidate,
                         "attribution_basis":"PRIMARY_CANDIDATE_ONLY",
                     },source="SYSTEM")
            strategy_observation_ok = str(sp.get("status", "")).upper() in {"ACTIONABLE", "HOLD"}
        except Exception as e:
            s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"STRATEGY_PLAN","error":repr(e)})
    # Persist current observation only after the strategy plan consumed the prior window.
    if strategy_observation_ok and current_far_gamma_spot is not None:
        s["gamma_history"] = (gamma_history + [current_far_gamma_spot])[-20:]
        s["gamma_history_schema"] = 2
        s["gamma_history_unit"] = "gamma_spot"
    if strategy_observation_ok and current_far_delta_abs is not None:
        s["far_delta_abs"] = current_far_delta_abs
    if tr.get("deal_warning"):
        s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"DEAL_FEED","warning":tr["deal_warning"]},source="BROKER_OBSERVED")
    s["last_pnl_observation_status"]=pnl_observation_status
    s["last_cycle_at"]=t; s["last_history_backfill_at"]=t if history_used else s.get("last_history_backfill_at"); save(spath(repo,args.instance_id),s)
    out={"status":"RECORDED","instance_id":args.instance_id,"cycle_id":cid,"timestamp_utc":t,
         "realized_pnl_gross":s["realized_pnl"],"unrealized_pnl_gross":mk["unrealized_pnl"],"gross_pnl":gross,
         "pnl_observation_status":pnl_observation_status,
         "strategy_book_scope":"STRATEGY_ATTRIBUTED_EXECUTIONS_ONLY","manual_book":{"realized_pnl":s["manual_realized_pnl"],"unrealized_pnl":mmk["unrealized_pnl"] if mmk["status"]=="OK" else None,"total_pnl":(s["manual_realized_pnl"]+sf(mmk["unrealized_pnl"])) if mmk["status"]=="OK" else None,"trade_count":s["manual_trade_count"],"mark_status":mmk["status"],"positions":manual_position_snapshot(s.get("manual_lots",[]))},
         "reconcile":s["last_reconcile"],"history_backfill_used":history_used,"history_start":tr.get("history_start"),"data_gaps_total":s["data_gaps"],"snapshot_sha256":sh,"ledger_head":l.validate()["head_hash"]}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0

def init_cmd(a):
    repo=Path(a.repo_root).resolve()
    with instance_mutation_lock(repo,a.instance_id):
        return _init_cmd_unlocked(a)


def _init_cmd_unlocked(a):
    repo=Path(a.repo_root).resolve()
    try: r=runtime_identity(repo)
    except Exception: r={}
    locked_id=r.get("strategy_id")
    locked_version=r.get("strategy_version")
    locked_engine=r.get("research_engine_commit")
    locked_hash=r.get("strategy_lock_hash")
    supplied={"strategy_id":a.strategy_id,"strategy_version":a.strategy_version,
              "research_engine_commit":a.research_engine_commit,"strategy_lock_hash":a.strategy_lock_hash}
    if locked_id and a.strategy_id and a.strategy_id!=locked_id:
        raise SystemExit("INSTANCE_LINEAGE_MISMATCH:strategy_id")
    if locked_version and a.strategy_version and a.strategy_version!=locked_version:
        raise SystemExit("INSTANCE_LINEAGE_MISMATCH:strategy_version")
    if locked_engine and a.research_engine_commit and a.research_engine_commit!=locked_engine:
        raise SystemExit("INSTANCE_LINEAGE_MISMATCH:research_engine_commit")
    if locked_hash and a.strategy_lock_hash and a.strategy_lock_hash!=locked_hash:
        raise SystemExit("INSTANCE_LINEAGE_MISMATCH:strategy_lock_hash")
    if not locked_id:
        supplied["strategy_id"]=a.strategy_id
        supplied["strategy_version"]=a.strategy_version
        supplied["research_engine_commit"]=a.research_engine_commit
        supplied["strategy_lock_hash"]=a.strategy_lock_hash
    start=a.start_at_utc or now(); created=now(); ps=[pos_spec(x) for x in a.position]
    m={"schema":MANIFEST_SCHEMA,"schema_version":1,"instance_id":a.instance_id,"created_at_utc":created,"start_at_utc":start,
       "strategy_id":a.strategy_id or locked_id or "UNSPECIFIED","strategy_version":a.strategy_version or locked_version or "UNSPECIFIED",
       "research_engine_commit":a.research_engine_commit or locked_engine,"strategy_lock_hash":a.strategy_lock_hash or locked_hash,
       "far_dte":120,"far_delta":.08,"near_dte":30,"coverage_mult":1.50,"initial_cash":a.initial_cash,
       "far_code_hint":a.far_code,"initial_positions":ps,"notes":a.note,
       "mutation_rule":"T0 and alpha lineage are immutable; material changes require a new instance."}
    d=idir(repo,a.instance_id)
    if d.exists() and any(d.iterdir()): raise SystemExit(f"INSTANCE_ALREADY_EXISTS:{a.instance_id}")
    m["manifest_hash"]=mhash(m); st={"schema":STATE_SCHEMA,"schema_version":1,"instance_id":a.instance_id,"processed_deal_ids":[],
       "lots":init_lots(m),"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,"last_snapshot_hash":None,
       "last_reconcile":None,"last_pnl_observation_status":"DATA_GAP","cycle_count":0,"data_gaps":0,
       "gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot","far_delta_abs":None,
       "strategy_deal_ids":[],"unattributed_deal_ids":[],
       "manual_lots":json.loads(json.dumps(init_lots(m))),"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None}
    save(mpath(repo,a.instance_id),m); save(spath(repo,a.instance_id),st)
    l=InstanceLedger(lpath(repo,a.instance_id),{"instance_id":a.instance_id,"manifest_hash":m["manifest_hash"],"strategy_id":m["strategy_id"],"strategy_version":m["strategy_version"],"research_engine_commit":m["research_engine_commit"]})
    c="INIT_"+created.replace(":","").replace("-","").replace(".","")
    l.append("INSTANCE_CREATED",instance_id=a.instance_id,cycle_id=c,timestamp_utc=created,payload={"economic_t0":start,"manifest_hash":m["manifest_hash"],"note":a.note},source="USER_INITIAL")
    l.append("INITIAL_STATE_RECORDED",instance_id=a.instance_id,cycle_id=c,timestamp_utc=created,payload={"initial_cash":a.initial_cash,"initial_positions":ps,"economic_t0":start,"observation_t0":created,"strategy_lineage":{"strategy_id":m["strategy_id"],"strategy_version":m["strategy_version"],"research_engine_commit":m["research_engine_commit"],"strategy_lock_hash":m["strategy_lock_hash"]}},source="USER_INITIAL")
    print(json.dumps({"status":"INSTANCE_CREATED","instance_id":a.instance_id,"start_at_utc":start,"created_at_utc":created,"manifest_hash":m["manifest_hash"],"path":str(d)},ensure_ascii=False,indent=2)); return 0

def manual_book_pnl_preview(lots, *, action, code, qty, price, lot_size):
    action=str(action).upper(); code=str(code).strip().upper(); q=si(qty); px=sf(price)
    size=max(1,si(lot_size) or 100)
    if action=="REDUCE":
        remaining=q; pnl=0.0; matched=0; entries=[]
        for lot in lots:
            if remaining<=0: break
            if lot.get("status","OPEN")!="OPEN" or str(lot.get("code","")).upper()!=code or str(lot.get("side","")).upper()!="LONG":
                continue
            take=min(remaining,si(lot.get("qty"))); entry=sf(lot.get("avg_price")); s=max(1,si(lot.get("lot_size")) or size)
            pnl += (px-entry)*take*s; matched += take; entries.append({"lot_id":lot.get("lot_id"),"qty":take,"entry_price":entry,"pnl":(px-entry)*take*s})
            remaining-=take
        return {"action":action,"code":code,"qty":q,"price":px,"lot_size":size,"matched_qty":matched,
                "remaining_unmatched":remaining,"realized_pnl_preview":pnl,"lots":entries}
    if action=="BUY_BACK_FAR":
        remaining=q; pnl=0.0; matched=0; entries=[]
        for lot in lots:
            if remaining<=0: break
            if lot.get("status","OPEN")!="OPEN" or str(lot.get("code","")).upper()!=code or str(lot.get("side","")).upper()!="SHORT":
                continue
            take=min(remaining,si(lot.get("qty"))); entry=sf(lot.get("avg_price")); s=max(1,si(lot.get("lot_size")) or size)
            pnl += (entry-px)*take*s; matched += take; entries.append({"lot_id":lot.get("lot_id"),"qty":take,"entry_price":entry,"pnl":(entry-px)*take*s})
            remaining-=take
        return {"action":action,"code":code,"qty":q,"price":px,"lot_size":size,"matched_qty":matched,
                "remaining_unmatched":remaining,"realized_pnl_preview":pnl,"lots":entries}
    return {"action":action,"code":code,"qty":q,"price":px,"lot_size":size,
            "matched_qty":q,"remaining_unmatched":0,"realized_pnl_preview":0.0,"lots":[]}

def record_manual_trade(repo, *, instance_id, action, code, qty, price, lot_size=100, timestamp_utc=None, trade_id=None, note="", strategy_context=None):
    repo_path = Path(repo).resolve()
    with instance_mutation_lock(repo_path, instance_id):
        return _record_manual_trade_unlocked(
            repo_path,
            instance_id=instance_id,
            action=action,
            code=code,
            qty=qty,
            price=price,
            lot_size=lot_size,
            timestamp_utc=timestamp_utc,
            trade_id=trade_id,
            note=note,
            strategy_context=strategy_context,
        )


def _record_manual_trade_unlocked(repo, *, instance_id, action, code, qty, price, lot_size=100, timestamp_utc=None, trade_id=None, note="", strategy_context=None):
    m,s,l=load_instance(Path(repo).resolve(),instance_id)
    t=timestamp_utc or now(); action=str(action).upper(); code=str(code).strip().upper()
    if not is_qqq_option_code(code):
        raise SystemExit("MANUAL_CODE_MUST_BE_QQQ_OPTION")
    trade_id=trade_id or ("MANUAL_"+t.replace(":","").replace("-","").replace(".","").replace("+00:00","Z"))
    existing_manual_ids={str(r.get("payload",{}).get("trade_id")) for r in l._rows() if r.get("event_type")=="MANUAL_TRADE_RECORDED"}
    if trade_id in existing_manual_ids:
        raise SystemExit(f"MANUAL_TRADE_ID_EXISTS:{trade_id}")
    lots=json.loads(json.dumps(s.get("manual_lots",[])))
    preview=manual_book_pnl_preview(lots,action=action,code=code,qty=qty,price=price,lot_size=lot_size)
    if preview["remaining_unmatched"]>0:
        if action=="REDUCE":
            raise SystemExit(f"MANUAL_REDUCE_EXCEEDS_POSITION:{code}:{preview['remaining_unmatched']}")
        if action=="BUY_BACK_FAR":
            raise SystemExit(f"MANUAL_COVER_EXCEEDS_POSITION:{code}:{preview['remaining_unmatched']}")
    pnl_delta,_=manual_apply_trade(lots,action=action,code=code,qty=qty,price=price,lot_size=lot_size,trade_id=trade_id,timestamp=t)
    s["manual_lots"]=lots; s["manual_realized_pnl"]=sf(s.get("manual_realized_pnl"))+sf(pnl_delta)
    s["manual_trade_count"]=si(s.get("manual_trade_count"))+1
    s["manual_last_mark"]={"unrealized_pnl":None,"status":"STALE_AFTER_MANUAL_TRADE","rows":[],"marked_at_utc":t}
    positions=manual_position_snapshot(lots)
    sc=strategy_context or {}
    strategy_ticket_id=sc.get("ticket_id")
    strategy_action=sc.get("action")
    strategy_code=sc.get("code")
    strategy_qty=si(sc.get("qty"))
    relationship = classify_relationship(action, code, qty, sc)
    l.append("MANUAL_TRADE_RECORDED",instance_id=instance_id,cycle_id="MANUAL_"+trade_id,timestamp_utc=t,
             payload={"trade_id":trade_id,"action":action,"code":code,"qty":si(qty),"price":sf(price),
                      "lot_size":max(1,si(lot_size) or 100),"realized_pnl_delta":sf(pnl_delta),
                      "manual_realized_pnl_after":s["manual_realized_pnl"],"positions_after":positions,
                      "pnl_preview":preview,"note":note,"relationship_to_strategy":relationship,"strategy_reference":sc,"lots_after":lots},
             source="USER_MANUAL")
    save(spath(Path(repo).resolve(),instance_id),s)
    return {"status":"MANUAL_TRADE_RECORDED","instance_id":instance_id,"trade_id":trade_id,
            "timestamp_utc":t,"action":action,"code":code,"qty":si(qty),"price":sf(price),
            "lot_size":max(1,si(lot_size) or 100),"realized_pnl_delta":sf(pnl_delta),
            "manual_realized_pnl":s["manual_realized_pnl"],"manual_positions":positions,
            "pnl_preview":preview,"note":note,"relationship_to_strategy":relationship,"strategy_reference":sc}

def manual_cmd(a):
    out=record_manual_trade(
        a.repo_root,instance_id=a.instance_id,action=a.action,code=a.code,qty=a.qty,price=a.price,
        lot_size=a.lot_size,timestamp_utc=a.timestamp_utc,trade_id=a.trade_id,note=a.note
    )
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0

def note_cmd(a):
    repo=Path(a.repo_root).resolve(); m,s,l=load_instance(repo,a.instance_id); t=now(); c="NOTE_"+t.replace(":","").replace("-","").replace(".","")
    l.append("HUMAN_NOTE",instance_id=a.instance_id,cycle_id=c,timestamp_utc=t,payload={"note":a.text,"tag":a.tag},source="USER_MANUAL")
    print(json.dumps({"status":"NOTE_RECORDED","instance_id":a.instance_id,"timestamp_utc":t},ensure_ascii=False,indent=2)); return 0

def instance_summary(repo, instance_id):
    repo=Path(repo).resolve(); m,s,l=load_instance(repo,instance_id)
    mark=s.get("manual_last_mark") or {}
    rows=l._rows(); recent=[r for r in rows if r.get("event_type")=="MANUAL_TRADE_RECORDED"][-20:]
    return {
        "instance_id":instance_id,
        "strategy_id":m.get("strategy_id"),
        "strategy_version":m.get("strategy_version"),
        "start_at_utc":m.get("start_at_utc"),
        "created_at_utc":m.get("created_at_utc"),
        "manual_book":{
            "realized_pnl":sf(s.get("manual_realized_pnl")),
            "unrealized_pnl":sf(mark.get("unrealized_pnl")) if mark.get("status")=="OK" else None,
            "total_pnl":(sf(s.get("manual_realized_pnl"))+sf(mark.get("unrealized_pnl"))) if mark.get("status")=="OK" else None,
            "mark_status":mark.get("status"),
            "trade_count":si(s.get("manual_trade_count")),
            "positions":manual_position_snapshot(s.get("manual_lots",[])),
            "marks":mark.get("rows",[]),
        },
        "broker_book":{
            "scope":"STRATEGY_OWNED_ONLY",
            "realized_pnl":sf(s.get("realized_pnl")),
            "strategy_deal_count":len(s.get("strategy_deal_ids",[])),
            "unattributed_deal_count":len(s.get("unattributed_deal_ids",[])),
            "last_reconcile":s.get("last_reconcile"),
            "data_gaps":si(s.get("data_gaps")),
        },
        "recent_manual_trades":[r.get("payload",{}) | {"timestamp_utc":r.get("timestamp_utc"),"event_seq":r.get("event_seq")} for r in recent],
        "performance_tape":build_performance_tape(
            [r.get("payload",{}) | {"timestamp_utc":r.get("timestamp_utc"),"event_seq":r.get("event_seq")}
             for r in rows if r.get("event_type")=="MANUAL_TRADE_RECORDED"],
            baseline_lots=init_lots(m),
        ),
        "ledger_head_hash":l.validate()["head_hash"],
    }

def list_instances(repo):
    root=Path(repo).resolve()/ROOT
    if not root.exists(): return []
    out=[]
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d/"manifest.json").exists():
            try:
                m,s,l=load_instance(Path(repo).resolve(),d.name)
                out.append({"instance_id":d.name,"strategy_id":m.get("strategy_id"),"start_at_utc":m.get("start_at_utc"),
                            "manual_realized_pnl":sf(s.get("manual_realized_pnl")),
                            "manual_trade_count":si(s.get("manual_trade_count"))})
            except Exception:
                continue
    return out

def report(a):
    repo=Path(a.repo_root).resolve(); m,s,l=load_instance(repo,a.instance_id); rows=l._rows(); counts={}
    for r in rows: counts[r["event_type"]]=counts.get(r["event_type"],0)+1
    out={"schema":"STRATEGY_INSTANCE_REPORT.v1","instance_id":a.instance_id,"strategy_id":m.get("strategy_id"),"strategy_version":m.get("strategy_version"),
         "start_at_utc":m.get("start_at_utc"),"created_at_utc":m.get("created_at_utc"),"manifest_hash":m.get("manifest_hash"),
         "records":len(rows),"event_counts":counts,"cycle_count":s.get("cycle_count"),
         "execution_attribution":{
             "strategy_deals":len(s.get("strategy_deal_ids",[])),
             "unattributed_deals":len(s.get("unattributed_deal_ids",[])),
             "policy":"only recent pre-decision strategy-plan matches enter strategy P&L; all other broker QQQ executions remain observed but unattributed",
         },
         "realized_pnl_gross":s.get("realized_pnl"),"manual_book":{"realized_pnl":s.get("manual_realized_pnl",0.0),"unrealized_pnl":((s.get("manual_last_mark") or {}).get("unrealized_pnl") if (s.get("manual_last_mark") or {}).get("status")=="OK" else None),"total_pnl":(sf(s.get("manual_realized_pnl"))+sf((s.get("manual_last_mark") or {}).get("unrealized_pnl"))) if (s.get("manual_last_mark") or {}).get("status")=="OK" else None,"trade_count":s.get("manual_trade_count",0),"mark_status":(s.get("manual_last_mark") or {}).get("status"),"positions":manual_position_snapshot(s.get("manual_lots",[]))},
         "pnl_observation_status":s.get("last_pnl_observation_status"),
         "last_reconcile":s.get("last_reconcile"),"data_gaps_total":s.get("data_gaps"),"open_lots":[x for x in s.get("lots",[]) if x.get("status","OPEN")=="OPEN" and si(x.get("qty"))>0],
         "ledger_head_hash":l.validate()["head_hash"],
         "performance_tape":build_performance_tape(
             [r.get("payload",{}) | {"timestamp_utc":r.get("timestamp_utc"),"event_seq":r.get("event_seq")}
              for r in rows if r.get("event_type")=="MANUAL_TRADE_RECORDED"],
             baseline_lots=init_lots(m),
         ),
         "rule":"Descriptive only; no strategy retuning or performance prediction."}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0

def verify(a):
    repo=Path(a.repo_root).resolve(); m,s,l=load_instance(repo,a.instance_id)
    print(json.dumps({"status":"PASS","instance_id":a.instance_id,"manifest_hash":m["manifest_hash"],"ledger":l.validate()},ensure_ascii=False,indent=2)); return 0

def watch(a):
    if a.interval<10: raise SystemExit("WATCH_INTERVAL_TOO_SMALL")
    while True:
        rc=cycle(a)
        if a.once or (rc and a.stop_on_error): return rc
        time.sleep(a.interval)

def parser():
    p=argparse.ArgumentParser(description="Personal strategy instance recorder; broker read-only.")
    p.add_argument("--repo-root",default="."); s=p.add_subparsers(dest="command",required=True)
    x=s.add_parser("init"); x.add_argument("--instance-id",required=True); x.add_argument("--strategy-id",default=None); x.add_argument("--strategy-version",default=None)
    x.add_argument("--research-engine-commit",default=None); x.add_argument("--strategy-lock-hash",default=None); x.add_argument("--start-at-utc",default=None)
    x.add_argument("--initial-cash",type=float,default=None); x.add_argument("--far-code",default=None); x.add_argument("--position",action="append",default=[]); x.add_argument("--note",default=""); x.set_defaults(fn=init_cmd)
    for name in ("cycle","watch"):
        x=s.add_parser(name); x.add_argument("--instance-id",required=True); x.add_argument("--host",default="127.0.0.1"); x.add_argument("--port",type=int,default=11111); x.add_argument("--simulate",action="store_true"); x.add_argument("--observe-strategy-plan",action="store_true"); x.add_argument("--backfill-after-minutes",type=int,default=10)
        if name=="watch": x.add_argument("--interval",type=int,default=300); x.add_argument("--once",action="store_true"); x.add_argument("--stop-on-error",action="store_true")
        x.set_defaults(fn=cycle if name=="cycle" else watch)
    x=s.add_parser("manual"); x.add_argument("--instance-id",required=True); x.add_argument("--action",required=True,choices=["ADD","REDUCE","SELL_FAR","BUY_BACK_FAR"]); x.add_argument("--code",required=True); x.add_argument("--qty",type=int,required=True); x.add_argument("--price",type=float,required=True); x.add_argument("--lot-size",type=int,default=100); x.add_argument("--timestamp-utc",default=None); x.add_argument("--trade-id",default=None); x.add_argument("--note",default=""); x.set_defaults(fn=manual_cmd)
    x=s.add_parser("instances"); x.set_defaults(fn=lambda a: print(json.dumps({"instances":list_instances(a.repo_root)},ensure_ascii=False,indent=2)) or 0)
    x=s.add_parser("note"); x.add_argument("--instance-id",required=True); x.add_argument("--text",required=True); x.add_argument("--tag",default="USER_MANUAL"); x.set_defaults(fn=note_cmd)
    for name,fn in (("report",report),("verify",verify)):
        x=s.add_parser(name); x.add_argument("--instance-id",required=True); x.set_defaults(fn=fn)
    return p

if __name__=="__main__":
    a=parser().parse_args(); a.repo_root=Path(a.repo_root).resolve(); raise SystemExit(a.fn(a))
