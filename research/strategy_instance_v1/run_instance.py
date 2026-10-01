from __future__ import annotations
import argparse, json, math, time
from datetime import datetime, timezone
from pathlib import Path
from .ledger import InstanceLedger, sha256_json
from ..evidence_v1.identity import runtime_identity
from ..live_hedge_v1.engine import Contract, Order, Position, plan, select_far, select_near
from ..live_hedge_v1.futu_reader import LiveFutuReader
from ..live_hedge_v1.futu_trade_reader import FutuTradeReader

ROOT=Path("research/strategy_instance_v1/instances")
MANIFEST_SCHEMA="STRATEGY_INSTANCE_MANIFEST.v1"
STATE_SCHEMA="STRATEGY_INSTANCE_STATE.v1"

def now():
    return datetime.now(timezone.utc).isoformat()

def dt(x):
    try:
        z=datetime.fromisoformat(str(x).replace("Z","+00:00"))
        return z.replace(tzinfo=timezone.utc) if z.tzinfo is None else z.astimezone(timezone.utc)
    except Exception: return None

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

def load_instance(repo,i):
    m=load(mpath(repo,i))
    if not m: raise SystemExit(f"UNKNOWN_INSTANCE_ID:{i}")
    if m.get("manifest_hash")!=mhash(m): raise SystemExit("INSTANCE_MANIFEST_TAMPERED_OR_MUTATED")
    s=load(spath(repo,i),{"schema":STATE_SCHEMA,"schema_version":1,"instance_id":i,
        "processed_deal_ids":[],"lots":[],"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,
        "last_snapshot_hash":None,"last_reconcile":None,"cycle_count":0,"data_gaps":0,"manual_lots":init_lots(m),"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None})
    l=InstanceLedger(lpath(repo,i),{"instance_id":i,"manifest_hash":m["manifest_hash"],
       "strategy_id":m.get("strategy_id"),"strategy_version":m.get("strategy_version"),
       "research_engine_commit":m.get("research_engine_commit")})
    s.setdefault("manual_lots", json.loads(json.dumps(m.get("initial_positions", []))))
    if not s.get("manual_lots") and m.get("initial_positions"):
        s["manual_lots"]=init_lots(m)
    # Normalize legacy/manual-less instances without touching broker lots.
    if s.get("manual_lots") and not isinstance(s.get("manual_lots")[0], dict):
        s["manual_lots"]=init_lots(m)
    s.setdefault("manual_realized_pnl",0.0)
    s.setdefault("manual_trade_count",0)
    s.setdefault("manual_last_mark",None)
    l.validate()
    return m,s,l

def pos_spec(x):
    p=[a.strip() for a in x.split(",")]
    if len(p) not in (4,5): raise SystemExit("POSITION_FORMAT=CODE,SIDE,QTY,AVG_COST[,LOT_SIZE]")
    side=p[1].upper()
    if side not in ("LONG","SHORT"): raise SystemExit("POSITION_SIDE=LONG|SHORT")
    return {"code":p[0],"side":side,"qty":max(0,si(p[2])),"avg_cost":max(0,sf(p[3])),
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
    rows=[]; unreal=0.0
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
        rows.append({"code":code,"side":side,"qty":qty,"avg_cost":px,"lot_size":size,"mid":float(mid),"unrealized_pnl":u,"status":"MARKED"})
    return {"rows":rows,"unrealized_pnl":unreal,"status":"OK" if rows and all(x["status"]=="MARKED" for x in rows) else ("PARTIAL" if rows else "EMPTY")}

def option_positions(ps):
    return [p for p in ps if str(p.get("code","")).upper().startswith("US.QQQ") and str(p.get("code","")).upper()!="US.QQQ"
            and str(p.get("side","")).upper() in ("LONG","SHORT") and si(p.get("qty"))>0]

def contracts_map(snap):
    out={}
    for x in snap.get("contracts",[]):
        if x.get("code"):
            out[str(x["code"])]=Contract(str(x["code"]),str(x.get("right","CALL")).upper(),sf(x.get("strike")),str(x.get("expiry","")),
                si(x.get("dte")),x.get("bid"),x.get("ask"),x.get("delta"),x.get("gamma"),x.get("iv"),max(1,si(x.get("lot_size")) or 100))
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

def reconcile(lots,ps):
    a={}
    for l in lots:
        if l.get("status","OPEN")!="OPEN": continue
        k=(str(l["code"]).upper(),str(l["side"]).upper()); a[k]=a.get(k,0)+si(l["qty"])
    b={}
    for p in option_positions(ps):
        k=(str(p["code"]).upper(),str(p["side"]).upper()); b[k]=b.get(k,0)+si(p["qty"])
    keys=set(a)|set(b)
    return [{"code":k[0],"side":k[1],"lot_qty":a.get(k,0),"broker_qty":b.get(k,0)} for k in sorted(keys) if a.get(k,0)!=b.get(k,0)]

def strategy_plan(snap,ps,orders,cmap,quotes,m):
    market=snap["market"]; pos=[]
    for p in ps:
        c=cmap.get(str(p["code"])); q=quotes.get(str(p["code"]),{})
        pos.append(Position(str(p["code"]),str(p["side"]).upper(),si(p["qty"]),sf(p["avg_cost"]),
            c.strike if c else q.get("strike"),c.expiry if c else q.get("expiry"),c.dte if c else q.get("dte"),
            q.get("delta"),q.get("gamma")))
    os=[Order(str(o.get("order_id","")),str(o.get("code","")),str(o.get("side","")).upper(),si(o.get("qty")),o.get("price"),
              str(o.get("status","")).upper(),str(o.get("updated_at","")),str(o.get("created_at","")),si(o.get("dealt_qty")),o.get("dealt_avg_price")) for o in orders]
    shorts=[p for p in pos if p.side=="SHORT" and str(p.code).upper().startswith("US.QQQ")]
    active=bool(shorts)
    far=None
    for p in shorts:
        c=cmap.get(p.code); q=quotes.get(p.code,{})
        if c: far=Contract(c.code,c.right,c.strike,c.expiry,c.dte,q.get("bid",c.bid),q.get("ask",c.ask),q.get("delta",c.delta),q.get("gamma",c.gamma),q.get("iv",c.iv),c.lot_size); break
    spot=sf(market.get("spot"))
    if far is None and not active:
        far=select_far(list(cmap.values()),spot,si(m.get("far_dte")) or 120,sf(m.get("far_delta")) or .08)
    near=select_near(list(cmap.values()),spot,si(m.get("near_dte")) or 30)
    if near:
        q=quotes.get(near.code,{})
        near=Contract(near.code,near.right,near.strike,near.expiry,near.dte,q.get("bid",near.bid),q.get("ask",near.ask),q.get("delta",near.delta),q.get("gamma",near.gamma),q.get("iv",near.iv),near.lot_size)
    if active and far is None: return {"status":"DATA_GAP","reason":"active short far quote unavailable"}
    return plan(market=market,far=far,near=near,positions=pos,orders=os,signal_active=bool(market.get("signal_active")),
                far_campaign_active=active,quotes_by_code=quotes,now=datetime.now(timezone.utc))

def cycle(args):
    repo=Path(args.repo_root).resolve(); m,s,l=load_instance(repo,args.instance_id); t=now()
    cid="CYCLE_"+t.replace(":","").replace("-","").replace(".",""); s["cycle_count"]=si(s.get("cycle_count"))+1
    try:
        history_start = None
        last_cycle = s.get("last_cycle_at")
        if last_cycle is None:
            history_start = m.get("created_at_utc")
        elif gap_minutes(t, last_cycle) is not None and gap_minutes(t, last_cycle) >= args.backfill_after_minutes:
            history_start = last_cycle
        tr=FutuTradeReader(args.host,args.port,real=not args.simulate).read(history_start=history_start)
        snap=LiveFutuReader(args.host,args.port).snapshot([p.get("code") for p in tr.get("positions",[]) if p.get("code")])
    except Exception as e:
        s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"BROKER_READ","error":repr(e)},source="BROKER_OBSERVED")
        s["last_cycle_at"]=t; save(spath(repo,args.instance_id),s); print(json.dumps({"status":"DATA_GAP","error":repr(e)},ensure_ascii=False,indent=2)); return 2
    ps=tr.get("positions",[]); orders=tr.get("orders",[]); cmap=contracts_map(snap); quotes=snap.get("quotes",{})
    history_used=bool(tr.get("history_backfill_used"))
    seen=set(map(str,s.get("processed_deal_ids",[]))); new=[]
    for d in tr.get("deals",[]):
        did=str(d.get("deal_id","") or "")
        if not did or did in seen or not after(d.get("created_at"),m["created_at_utc"]): continue
        if str(d.get("code","")).upper().startswith("US.QQQ"):
            d=dict(d); c=cmap.get(str(d["code"])); d["lot_size"]=c.lot_size if c else 100; new.append(d)
    realized_delta=0.0
    for d in sorted(new,key=lambda x:(dt(x.get("created_at")) or datetime.max.replace(tzinfo=timezone.utc),str(x.get("deal_id")))):
        realized_delta+=apply_deal(s["lots"],d); s["processed_deal_ids"].append(str(d["deal_id"]))
        l.append("EXECUTION_DETECTED",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"deal":d},source="BROKER_OBSERVED")
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
    mk=marks(ps,cmap,quotes); gross=s["realized_pnl"]+sf(mk["unrealized_pnl"])\n    mmk=mark_lots(s.get("manual_lots",[]),cmap,quotes)\n    s["manual_last_mark"]={"unrealized_pnl":mmk["unrealized_pnl"],"status":mmk["status"],"rows":mmk["rows"],"marked_at_utc":t}
    l.append("MARK_TO_MARKET",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={
        "snapshot_sha256":sh,"realized_pnl_gross":s["realized_pnl"],"unrealized_pnl_gross":mk["unrealized_pnl"],
        "gross_pnl":gross,"signed_market_value":mk["signed_market_value"],"marks":mk["rows"],"status":mk["status"],"manual_book":{"realized_pnl":s["manual_realized_pnl"],"unrealized_pnl":mmk["unrealized_pnl"],"total_pnl":s["manual_realized_pnl"]+sf(mmk["unrealized_pnl"]),"marks":mmk["rows"],"status":mmk["status"]}})
    if args.observe_strategy_plan and snap.get("status")=="OK":
        try:
            sp=strategy_plan(snap,ps,orders,cmap,quotes,m)
            l.append("STRATEGY_PLAN_OBSERVED",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,
                     payload={"plan":sp,"execution":"READ_ONLY_OBSERVATION"},source="SYSTEM")
        except Exception as e:
            s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"STRATEGY_PLAN","error":repr(e)})
    if tr.get("deal_warning"):
        s["data_gaps"]=si(s.get("data_gaps"))+1; l.append("DATA_GAP",instance_id=m["instance_id"],cycle_id=cid,timestamp_utc=t,payload={"stage":"DEAL_FEED","warning":tr["deal_warning"]},source="BROKER_OBSERVED")
    s["last_cycle_at"]=t; s["last_history_backfill_at"]=t if history_used else s.get("last_history_backfill_at"); save(spath(repo,args.instance_id),s)
    out={"status":"RECORDED","instance_id":args.instance_id,"cycle_id":cid,"timestamp_utc":t,
         "realized_pnl_gross":s["realized_pnl"],"unrealized_pnl_gross":mk["unrealized_pnl"],"gross_pnl":gross,"manual_book":{"realized_pnl":s["manual_realized_pnl"],"unrealized_pnl":mmk["unrealized_pnl"],"total_pnl":s["manual_realized_pnl"]+sf(mmk["unrealized_pnl"]),"trade_count":s["manual_trade_count"],"positions":manual_position_snapshot(s.get("manual_lots",[]))},
         "reconcile":s["last_reconcile"],"history_backfill_used":history_used,"history_start":tr.get("history_start"),"data_gaps_total":s["data_gaps"],"snapshot_sha256":sh,"ledger_head":l.validate()["head_hash"]}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0

def init_cmd(a):
    repo=Path(a.repo_root).resolve()
    try: r=runtime_identity(repo)
    except Exception: r={}
    start=a.start_at_utc or now(); created=now(); ps=[pos_spec(x) for x in a.position]
    m={"schema":MANIFEST_SCHEMA,"schema_version":1,"instance_id":a.instance_id,"created_at_utc":created,"start_at_utc":start,
       "strategy_id":a.strategy_id or r.get("strategy_id") or "UNSPECIFIED","strategy_version":a.strategy_version or r.get("strategy_version") or "UNSPECIFIED",
       "research_engine_commit":a.research_engine_commit or r.get("research_engine_commit"),"strategy_lock_hash":a.strategy_lock_hash or r.get("strategy_lock_hash"),
       "far_dte":120,"far_delta":.08,"near_dte":30,"coverage_mult":1.50,"initial_cash":a.initial_cash,
       "far_code_hint":a.far_code,"initial_positions":ps,"notes":a.note,
       "mutation_rule":"T0 and alpha lineage are immutable; material changes require a new instance."}
    d=idir(repo,a.instance_id)
    if d.exists() and any(d.iterdir()): raise SystemExit(f"INSTANCE_ALREADY_EXISTS:{a.instance_id}")
    m["manifest_hash"]=mhash(m); st={"schema":STATE_SCHEMA,"schema_version":1,"instance_id":a.instance_id,"processed_deal_ids":[],
       "lots":init_lots(m),"realized_pnl":0.0,"last_cycle_at":None,"last_snapshot_hash":None,"last_reconcile":None,"cycle_count":0,"data_gaps":0,
       "manual_lots":json.loads(json.dumps(init_lots(m))),"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None}
    save(mpath(repo,a.instance_id),m); save(spath(repo,a.instance_id),st)
    l=InstanceLedger(lpath(repo,a.instance_id),{"instance_id":a.instance_id,"manifest_hash":m["manifest_hash"],"strategy_id":m["strategy_id"],"strategy_version":m["strategy_version"],"research_engine_commit":m["research_engine_commit"]})
    c="INIT_"+created.replace(":","").replace("-","").replace(".","")
    l.append("INSTANCE_CREATED",instance_id=a.instance_id,cycle_id=c,timestamp_utc=created,payload={"economic_t0":start,"manifest_hash":m["manifest_hash"],"note":a.note},source="USER_INITIAL")
    l.append("INITIAL_STATE_RECORDED",instance_id=a.instance_id,cycle_id=c,timestamp_utc=created,payload={"initial_cash":a.initial_cash,"initial_positions":ps,"economic_t0":start,"observation_t0":created},source="USER_INITIAL")
    print(json.dumps({"status":"INSTANCE_CREATED","instance_id":a.instance_id,"start_at_utc":start,"created_at_utc":created,"manifest_hash":m["manifest_hash"],"path":str(d)},ensure_ascii=False,indent=2)); return 0

def manual_cmd(a):
    repo=Path(a.repo_root).resolve(); m,s,l=load_instance(repo,a.instance_id)
    t=a.timestamp_utc or now()
    action=str(a.action).upper()
    code=str(a.code).strip().upper()
    if not code.startswith("US.QQQ") or code == "US.QQQ":
        raise SystemExit("MANUAL_CODE_MUST_BE_QQQ_OPTION")
    a.code=code
    trade_id=a.trade_id or ("MANUAL_"+t.replace(":","").replace("-","").replace(".","").replace("+00:00","Z"))
    lots=json.loads(json.dumps(s.get("manual_lots",[])))
    pnl_delta,_=manual_apply_trade(
        lots,
        action=action,
        code=a.code,
        qty=a.qty,
        price=a.price,
        lot_size=a.lot_size,
        trade_id=trade_id,
        timestamp=t,
    )
    s["manual_lots"]=lots
    s["manual_realized_pnl"]=sf(s.get("manual_realized_pnl"))+sf(pnl_delta)
    s["manual_trade_count"]=si(s.get("manual_trade_count"))+1
    positions=manual_position_snapshot(lots)
    c="MANUAL_"+trade_id
    l.append("MANUAL_TRADE_RECORDED",instance_id=a.instance_id,cycle_id=c,timestamp_utc=t,
             payload={"trade_id":trade_id,"action":action,"code":a.code,"qty":si(a.qty),"price":sf(a.price),
                      "lot_size":max(1,si(a.lot_size) or 100),"realized_pnl_delta":sf(pnl_delta),
                      "manual_realized_pnl_after":s["manual_realized_pnl"],"positions_after":positions,
                      "note":a.note},
             source="USER_MANUAL")
    save(spath(repo,a.instance_id),s)
    print(json.dumps({"status":"MANUAL_TRADE_RECORDED","instance_id":a.instance_id,"trade_id":trade_id,
                      "action":action,"code":a.code,"qty":si(a.qty),"price":sf(a.price),
                      "realized_pnl_delta":sf(pnl_delta),"manual_realized_pnl":s["manual_realized_pnl"],
                      "manual_positions":positions},ensure_ascii=False,indent=2)); return 0

def note_cmd(a):
    repo=Path(a.repo_root).resolve(); m,s,l=load_instance(repo,a.instance_id); t=now(); c="NOTE_"+t.replace(":","").replace("-","").replace(".","")
    l.append("HUMAN_NOTE",instance_id=a.instance_id,cycle_id=c,timestamp_utc=t,payload={"note":a.text,"tag":a.tag},source="USER_MANUAL")
    print(json.dumps({"status":"NOTE_RECORDED","instance_id":a.instance_id,"timestamp_utc":t},ensure_ascii=False,indent=2)); return 0

def report(a):
    repo=Path(a.repo_root).resolve(); m,s,l=load_instance(repo,a.instance_id); rows=l._rows(); counts={}
    for r in rows: counts[r["event_type"]]=counts.get(r["event_type"],0)+1
    out={"schema":"STRATEGY_INSTANCE_REPORT.v1","instance_id":a.instance_id,"strategy_id":m.get("strategy_id"),"strategy_version":m.get("strategy_version"),
         "start_at_utc":m.get("start_at_utc"),"created_at_utc":m.get("created_at_utc"),"manifest_hash":m.get("manifest_hash"),
         "records":len(rows),"event_counts":counts,"cycle_count":s.get("cycle_count"),"realized_pnl_gross":s.get("realized_pnl"),"manual_book":{"realized_pnl":s.get("manual_realized_pnl",0.0),"unrealized_pnl":(s.get("manual_last_mark") or {}).get("unrealized_pnl"),"total_pnl":sf(s.get("manual_realized_pnl"))+sf((s.get("manual_last_mark") or {}).get("unrealized_pnl")),"trade_count":s.get("manual_trade_count",0),"positions":manual_position_snapshot(s.get("manual_lots",[]))},
         "last_reconcile":s.get("last_reconcile"),"data_gaps_total":s.get("data_gaps"),"open_lots":[x for x in s.get("lots",[]) if x.get("status","OPEN")=="OPEN" and si(x.get("qty"))>0],
         "ledger_head_hash":l.validate()["head_hash"],"rule":"Descriptive only; no strategy retuning or performance prediction."}
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
    x=s.add_parser("note"); x.add_argument("--instance-id",required=True); x.add_argument("--text",required=True); x.add_argument("--tag",default="USER_MANUAL"); x.set_defaults(fn=note_cmd)
    for name,fn in (("report",report),("verify",verify)):
        x=s.add_parser(name); x.add_argument("--instance-id",required=True); x.set_defaults(fn=fn)
    return p

if __name__=="__main__":
    a=parser().parse_args(); a.repo_root=Path(a.repo_root).resolve(); raise SystemExit(a.fn(a))
