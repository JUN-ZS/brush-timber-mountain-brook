#!/usr/bin/env python3
"""Frozen QQQ state-adaptive option geometry V1.
No optimization. Real historical QQQ option-chain Bid/Ask only.

ENTRY:
  +1 ~50Δ Call
  -2 ~20Δ Calls
  +2 ~8Δ farther Call Wings
  +1 ~25Δ Long Put
  -1 ~10Δ Short Put

UPWARD WAVE:
  previous close >= anchor close + 1.0 * ATR20
  -> execute on next trading day, same expiry:
     Short Call: 20Δ -> 30Δ -> 40Δ (closer)
     Short Put:  10Δ -> 5Δ (farther OTM)
     Long Put remains untouched.
  ATM call, call wings, N=2 and expiry remain fixed.

Execution uses historical Ask/Bid; marks use Mid; no interpolation, no BS pricing.
"""

from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

from qqq_ratio_call_harvest_v1 import (
    CAPITAL_USD, COOLDOWN_DAYS, DTE_MIN, DTE_MAX, HOLD_MAX,
    ensure_data, load_underlying, q_at, executable, midpoint, sha256_file
)

CAPITAL = 100000.0
N = 2
CALL_TARGETS = (0.20, 0.30, 0.40)
PUT_TARGETS = (0.10, 0.05)
ATM_TARGET = 0.50
WING_TARGET = 0.08
LONG_PUT_TARGET = -0.25
ATR_WINDOW = 20
WAVE_MULT = 1.0

def duck(con, sql, params=None):
    return con.execute(sql, params or []).df()

def under(path):
    u = load_underlying(path).copy()
    prev = u["close"].shift(1)
    u["tr"] = np.maximum(
        u["high"]-u["low"],
        np.maximum((u["high"]-prev).abs(), (u["low"]-prev).abs())
    )
    u["atr20"] = u["tr"].rolling(ATR_WINDOW, min_periods=ATR_WINDOW).mean()
    return u.reset_index(drop=True)

def chain(con, opt_path, dt, expiry=None):
    sql = """
      SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark, CAST(delta AS DOUBLE) AS delta,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume, UPPER(type) AS type
      FROM read_parquet(?)
      WHERE CAST(date AS DATE)=?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid
        AND delta IS NOT NULL
    """
    p=[str(opt_path), pd.Timestamp(dt).date()]
    if expiry is None:
        sql += """ AND CAST(expiration AS DATE) BETWEEN
                   CAST(date AS DATE)+INTERVAL 18 DAY
                   AND CAST(date AS DATE)+INTERVAL 35 DAY"""
    else:
        sql += " AND CAST(expiration AS DATE)=?"
        p.append(pd.Timestamp(expiry).date())
    x=duck(con,sql,p)
    if x.empty:return x
    x["date"]=pd.to_datetime(x["date"]); x["expiration"]=pd.to_datetime(x["expiration"])
    x["dte"]=(x["expiration"]-pd.Timestamp(dt)).dt.days
    return x

def pick(df, delta, gt=None, lt=None):
    x=df.copy()
    if gt is not None:x=x[x.strike>float(gt)]
    if lt is not None:x=x[x.strike<float(lt)]
    if x.empty:return None
    x=x.assign(err=(x.delta-float(delta)).abs())
    return x.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]

def select_entry(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    ex=(r.groupby("expiration",as_index=False)
          .agg(dte=("dte","first"),mv=("volume","max"))
          .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(ex)]
    c=g[g.type=="CALL"]; p=g[g.type=="PUT"]
    atm=pick(c,ATM_TARGET)
    lp=pick(p,LONG_PUT_TARGET)
    if atm is None or lp is None:return None
    sc20=pick(c,CALL_TARGETS[0],gt=atm.strike)
    sc40=pick(c,CALL_TARGETS[-1],gt=atm.strike)
    if sc20 is None or sc40 is None:return None
    wing=pick(c,WING_TARGET,gt=sc40.strike)
    sp10=pick(p,-PUT_TARGETS[0],lt=lp.strike)
    if wing is None or sp10 is None:return None
    sp5=pick(p,-PUT_TARGETS[-1],lt=sp10.strike)
    if sp5 is None:return None
    return {
      "expiry":pd.Timestamp(ex),
      "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
      "sc20":{"id":str(sc20.contract_id),"k":float(sc20.strike)},
      "sc40":{"id":str(sc40.contract_id),"k":float(sc40.strike)},
      "wing":{"id":str(wing.contract_id),"k":float(wing.strike)},
      "lp":{"id":str(lp.contract_id),"k":float(lp.strike)},
      "sp10":{"id":str(sp10.contract_id),"k":float(sp10.strike)},
      "sp5":{"id":str(sp5.contract_id),"k":float(sp5.strike)},
    }

def select_migration(con,opt_path,dt,legs,wave_no,current_call,current_put,spot):
    g=chain(con,opt_path,dt,legs["expiry"])
    if g.empty:return None
    c=g[g.type=="CALL"]; p=g[g.type=="PUT"]
    target_call=CALL_TARGETS[min(wave_no,len(CALL_TARGETS)-1)]
    target_put=PUT_TARGETS[min(wave_no,len(PUT_TARGETS)-1)]
    # The migrated Short Call must still be OTM relative to the actual T+1 spot.
    nc=pick(c,target_call,gt=max(legs["atm"]["k"],spot),lt=legs["wing"]["k"])
    # The Long Put remains the anchor; only the Short Put moves farther OTM.
    np_=pick(p,-target_put,lt=min(legs["lp"]["k"],spot))
    if nc is None or np_ is None:return None
    return {
      "wave":wave_no,
      "call":{"id":str(nc.contract_id),"k":float(nc.strike),"delta":float(nc.delta)},
      "put":{"id":str(np_.contract_id),"k":float(np_.strike),"delta":float(np_.delta)},
      "changed":str(nc.contract_id)!=current_call or str(np_.contract_id)!=current_put
    }

def quotes(con,opt_path,ids,start,end):
    ids=sorted({str(x) for x in ids})
    q=duck(con,"""SELECT CAST(date AS DATE) AS date,
                     CAST(contract_id AS VARCHAR) AS contract_id,
                     CAST(bid AS DOUBLE) AS bid,CAST(ask AS DOUBLE) AS ask,
                     CAST(mark AS DOUBLE) AS mark
                  FROM read_parquet(?)
                  WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
                    AND CAST(date AS DATE) BETWEEN ? AND ?""",
             [str(opt_path),ids,pd.Timestamp(start).date(),pd.Timestamp(end).date()])
    if q.empty:return q
    q["date"]=pd.to_datetime(q.date); q["contract_id"]=q.contract_id.astype(str)
    return q.drop_duplicates(["date","contract_id"]).set_index(["date","contract_id"]).sort_index()

def Q(q,dt,cid): return q_at(q,pd.Timestamp(dt),str(cid))

def leg_mark(q,dt,ids):
    vals=[midpoint(Q(q,dt,ids[k])) for k in ("atm","sc","wing","lp","sp")]
    return np.nan if any(pd.isna(x) for x in vals) else (
        vals[0]-N*vals[1]+N*vals[2]+vals[3]-vals[4]
    )*100.0

def entry_cf(q,dt,ids):
    vals=[executable(Q(q,dt,ids[k]),s) for k,s in (
        ("atm","BUY"),("sc","SELL"),("wing","BUY"),("lp","BUY"),("sp","SELL")
    )]
    return None if any(pd.isna(x) for x in vals) else (
        vals[0]-N*vals[1]+N*vals[2]+vals[3]-vals[4]
    )*100.0

def exit_cf(q,dt,ids):
    vals=[executable(Q(q,dt,ids[k]),s) for k,s in (
        ("atm","SELL"),("sc","BUY"),("wing","SELL"),("lp","SELL"),("sp","BUY")
    )]
    return None if any(pd.isna(x) for x in vals) else (
        vals[0]-N*vals[1]+N*vals[2]+vals[3]-vals[4]
    )*100.0

def migration_cf(q,dt,oldc,newc,oldp,newp):
    oc,nc,op,np_=Q(q,dt,oldc),Q(q,dt,newc),Q(q,dt,oldp),Q(q,dt,newp)
    if any(x is None for x in (oc,nc,op,np_)):return None
    v=[executable(oc,"BUY"),executable(nc,"SELL"),
       executable(op,"BUY"),executable(np_,"SELL")]
    if any(pd.isna(x) for x in v):return None
    return (N*(-v[0]+v[1]) + (-v[2]+v[3]))*100.0

def trade(con,opt_path,u,row,legs,adaptive):
    entry=pd.Timestamp(row.date)
    last=min(entry+pd.Timedelta(days=HOLD_MAX),pd.Timestamp(legs["expiry"]))
    w=u[(u.date>=entry)&(u.date<=last)].reset_index(drop=True)
    if w.empty:return None,"NO_WINDOW"
    exit_date=pd.Timestamp(w.iloc[-1].date)

    base_ids={k:legs[k]["id"] for k in ("atm","sc20","wing","lp","sp10")}
    ids={"atm":base_ids["atm"],"sc":base_ids["sc20"],"wing":base_ids["wing"],
         "lp":base_ids["lp"],"sp":base_ids["sp10"]}
    migrations=[]
    if adaptive:
        anchor=float(row.close); wave=0
        curc,curp=ids["sc"],ids["sp"]
        for j in range(1,len(w)):
            prev=w.iloc[j-1]
            atr=float(prev.atr20) if pd.notna(prev.atr20) else np.nan
            if pd.isna(atr) or wave>=2:continue
            if float(prev.close) < anchor + WAVE_MULT*atr:continue
            t1=pd.Timestamp(w.iloc[j].date)
            m=select_migration(con,opt_path,t1,legs,wave+1,curc,curp,float(w.iloc[j].close))
            anchor=float(w.iloc[j].close)
            if m is None or not m["changed"]:continue
            migrations.append({**m,"date":t1})
            curc,curp=m["call"]["id"],m["put"]["id"]
            wave+=1
        all_ids=set(ids.values())
        all_ids |= {m["call"]["id"] for m in migrations}
        all_ids |= {m["put"]["id"] for m in migrations}
    else:
        all_ids=set(ids.values())

    q=quotes(con,opt_path,all_ids,entry,exit_date)
    ec=entry_cf(q,entry,ids)
    if ec is None:return None,"NO_ENTRY_QUOTES"
    cash=-float(ec)
    active=dict(ids)
    events=[]; eq=[]

    bydate={pd.Timestamp(m["date"]):m for m in migrations}
    for _,r in w.iterrows():
        dt=pd.Timestamp(r.date)
        m=bydate.get(dt)
        if m is not None:
            cf=migration_cf(q,dt,active["sc"],m["call"]["id"],active["sp"],m["put"]["id"])
            if cf is not None:
                cash+=cf
                oldc,oldp=active["sc"],active["sp"]
                active["sc"],active["sp"]=m["call"]["id"],m["put"]["id"]
                events.append({
                    "date":str(dt.date()),"wave":int(m["wave"]),
                    "migration_cashflow_usd":float(cf),
                    "old_call":oldc,"new_call":active["sc"],
                    "new_call_strike":m["call"]["k"],"new_call_delta":m["call"]["delta"],
                    "old_put":oldp,"new_put":active["sp"],
                    "new_put_strike":m["put"]["k"],"new_put_delta":m["put"]["delta"]
                })
        mk=leg_mark(q,dt,active)
        if pd.notna(mk):eq.append((dt,CAPITAL+cash+mk))

    xc=exit_cf(q,exit_date,active)
    if xc is None:return None,"NO_EXIT_QUOTES"
    pnl=cash+float(xc)
    eq.append((exit_date,CAPITAL+pnl))
    return {
      "entry":entry,"exit":exit_date,"pnl_usd":float(pnl),
      "return_pct":float(100*pnl/CAPITAL),
      "entry_cashflow_usd":float(ec),"migrations":events,"eq":eq
    },"OK"

def summary(trades,label):
    if not trades:return {"mode":label,"trades":0},pd.DataFrame()
    t=pd.DataFrame([{k:v for k,v in x.items() if k not in ("eq","migrations")} for x in trades]).sort_values("entry").reset_index(drop=True)
    t["mult"]=1+t.pnl_usd/CAPITAL
    t["nav"]=CAPITAL*t.mult.cumprod()

    # Reconstruct a single sequential portfolio curve from the per-trade
    # 100k-normalized MTM paths. Trades do not overlap.
    nav0=CAPITAL
    seq=[]
    for _,tr in t.iterrows():
        hit=[x for x in trades if pd.Timestamp(x["entry"])==pd.Timestamp(tr["entry"])]
        if not hit:
            continue
        x=hit[0]
        for dt,raw_nav in x["eq"]:
            seq.append((pd.Timestamp(dt),nav0*(float(raw_nav)/CAPITAL)))
        nav0=nav0*(1+float(tr["pnl_usd"])/CAPITAL)
    e=pd.DataFrame(seq,columns=["date","nav"]).groupby("date",as_index=False).nav.last().sort_values("date")
    e["peak"]=e.nav.cummax(); e["dd"]=e.nav/e.peak-1
    yrs=max((t.exit.iloc[-1]-t.entry.iloc[0]).days/365.25,1/365.25)
    st={
      "mode":label,"trades":int(len(t)),
      "win_rate":float((t.pnl_usd>0).mean()),
      "avg_trade_usd":float(t.pnl_usd.mean()),
      "worst_trade_usd":float(t.pnl_usd.min()),
      "best_trade_usd":float(t.pnl_usd.max()),
      "total_return_pct":float(100*(t.nav.iloc[-1]/CAPITAL-1)),
      "cagr":float((t.nav.iloc[-1]/CAPITAL)**(1/yrs)-1),
      "maxdd_daily_mtm":float(e.dd.min()),
      "migration_events":int(sum(len(x["migrations"]) for x in trades)),
      "data_start":str(t.entry.min().date()),"data_end":str(t.exit.max().date())
    }
    return st,e

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    op,up=ensure_data(Path(a.data_dir))
    u=under(up); con=duckdb.connect()
    static=[]; adaptive=[]; rejects={}
    next_allowed=None
    for _,row in u.iterrows():
        dt=pd.Timestamp(row.date)
        if next_allowed is not None and dt<=next_allowed:continue
        if not bool(row.signal):continue
        legs=select_entry(con,op,dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"]=rejects.get("NO_ENTRY_LEGS",0)+1;continue
        s,ss=trade(con,op,u,row,legs,False)
        ad,as_=trade(con,op,u,row,legs,True)
        if s is None or ad is None:
            rejects[ss if s is None else as_]=rejects.get(ss if s is None else as_,0)+1;continue
        static.append(s);adaptive.append(ad)
        next_allowed=max(s["exit"],ad["exit"])+pd.Timedelta(days=COOLDOWN_DAYS)

    st,se=summary(static,"STATIC_GEOMETRY"); at,ae=summary(adaptive,"STATE_ADAPTIVE_GEOMETRY")
    for label,trades in (("STATIC_GEOMETRY",static),("STATE_ADAPTIVE_GEOMETRY",adaptive)):
        pd.DataFrame([{**{k:v for k,v in x.items() if k not in ("eq","migrations")},
                       "migration_events_json":json.dumps(x["migrations"],ensure_ascii=False)}
                      for x in trades]).to_csv(out/f"trades_{label}.csv",index=False)
    if not se.empty:se.to_csv(out/"equity_STATIC_GEOMETRY.csv",index=False)
    if not ae.empty:ae.to_csv(out/"equity_STATE_ADAPTIVE_GEOMETRY.csv",index=False)
    pd.DataFrame([st,at]).to_csv(out/"summary.csv",index=False)
    report={
      "research_id":"QQQ_STATE_ADAPTIVE_GEOMETRY_V1",
      "status":"REAL_QQQ_CHAIN_HYPOTHESIS_TEST",
      "contract":{
        "entry":"+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ Call Wings +1 ~25Δ Long Put -1 ~10Δ Short Put",
        "wave":"previous close >= anchor close + 1.0*ATR20",
        "lag":"T trigger -> T+1 migration",
        "call_ladder":[0.20,0.30,0.40],
        "short_put_abs_delta":[0.10,0.05],
        "long_put":"retained, never migrated",
        "atm_and_wings":"fixed",
        "N":2,"expiry":"fixed from entry",
        "migration":"buy old short at Ask / sell new short at Bid",
        "mark":"Mid","exit":"executable Bid/Ask",
        "interpolation":False,"black_scholes":False,"optimization":False
      },
      "data":{"options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up),
              "underlying_range":[str(u.date.min().date()),str(u.date.max().date())]},
      "results":{"static":st,"adaptive":at,"rejections":rejects}
    }
    (out/"qqq_state_adaptive_geometry_v1_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":main()