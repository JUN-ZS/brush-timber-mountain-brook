#!/usr/bin/env python3
"""QQQ Tail Bank V4: cross-date 2-layer stack with decoupled tail expiry.

Structural isolation:
  - Harvest/call package uses the usual nearest 18-35 DTE expiry.
  - Put spread uses the NEXT listed expiry after the harvest expiry.
  - Thus +25Δ Long Put / -10Δ Short Put survives beyond the short-cycle
    call harvest instead of expiring with it.
  - Up to 2 simultaneous vintages; 50% capital per vintage.
  - No within-vintage strike migration in this V4.

The only change vs synchronized 2-layer stack is put-spread maturity.
"""

from __future__ import annotations
import argparse, json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_harvest_v1 import (
    ensure_data, load_underlying, q_at, executable, midpoint, sha256_file
)

CAPITAL=100000.0
N=2
DTE_MIN=18
DTE_MAX=35
HOLD_MAX=30
STACK=2
ATM_TARGET=0.50
SC_TARGET=0.20
WING_TARGET=0.08
LP_TARGET=-0.25
SP_TARGET=-0.10


def duck(con,sql,params=None):
    return con.execute(sql,params or []).df()


def chain(con,opt_path,dt,expiry=None):
    sql="""
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark, CAST(delta AS DOUBLE) AS delta,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume,
             UPPER(type) AS type
      FROM read_parquet(?)
      WHERE CAST(date AS DATE)=?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid
        AND delta IS NOT NULL
    """
    p=[str(opt_path),pd.Timestamp(dt).date()]
    if expiry is None:
        sql += """ AND CAST(expiration AS DATE) BETWEEN
                  CAST(date AS DATE)+INTERVAL 18 DAY
                  AND CAST(date AS DATE)+INTERVAL 35 DAY"""
    else:
        sql += " AND CAST(expiration AS DATE)=?"
        p.append(pd.Timestamp(expiry).date())
    x=duck(con,sql,p)
    if x.empty:return x
    x["date"]=pd.to_datetime(x["date"])
    x["expiration"]=pd.to_datetime(x["expiration"])
    x["dte"]=(x["expiration"]-pd.Timestamp(dt)).dt.days
    return x


def pick(df,delta,gt=None,lt=None):
    x=df.copy()
    if gt is not None:x=x[x.strike>float(gt)]
    if lt is not None:x=x[x.strike<float(lt)]
    if x.empty:return None
    x=x.assign(err=(x.delta-float(delta)).abs())
    return x.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]


def select_entry(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    expiries=sorted(r["expiration"].dropna().unique())
    if not expiries:return None
    harvest_exp=pd.Timestamp(expiries[0])
    # "Tail bank": next listed expiry after the harvest expiry.
    tail_candidates=[]
    r_all=duck(con,"""
      SELECT DISTINCT CAST(expiration AS DATE) AS expiration
      FROM read_parquet(?)
      WHERE CAST(date AS DATE)=?
        AND CAST(expiration AS DATE)>?
      ORDER BY expiration
    """,[str(opt_path),pd.Timestamp(dt).date(),harvest_exp.date()])
    if r_all.empty:return None
    tail_exp=pd.Timestamp(r_all.iloc[0]["expiration"])

    gh=r[r.expiration==harvest_exp]
    rt=chain(con,opt_path,dt,tail_exp)
    if rt.empty:return None

    c=gh[gh.type=="CALL"]; p=rt[rt.type=="PUT"]
    atm=pick(c,ATM_TARGET)
    lp=pick(p,LP_TARGET)
    if atm is None or lp is None:return None
    sc=pick(c,SC_TARGET,gt=atm.strike)
    if sc is None:return None
    wing=pick(c,WING_TARGET,gt=sc.strike)
    if wing is None:return None
    sp=pick(p,-SP_TARGET,lt=lp.strike)
    if sp is None:return None

    return {
      "harvest_expiry":harvest_exp,
      "tail_expiry":tail_exp,
      "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
      "sc":{"id":str(sc.contract_id),"k":float(sc.strike)},
      "wing":{"id":str(wing.contract_id),"k":float(wing.strike)},
      "lp":{"id":str(lp.contract_id),"k":float(lp.strike)},
      "sp":{"id":str(sp.contract_id),"k":float(sp.strike)},
    }


def quotes(con,opt_path,ids,start,end):
    ids=sorted({str(x) for x in ids})
    q=duck(con,"""
      SELECT CAST(date AS DATE) AS date,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid,CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
    """,[str(opt_path),ids,pd.Timestamp(start).date(),pd.Timestamp(end).date()])
    if q.empty:return q
    q["date"]=pd.to_datetime(q.date);q["contract_id"]=q.contract_id.astype(str)
    return q.drop_duplicates(["date","contract_id"]).set_index(["date","contract_id"]).sort_index()


def Q(q,dt,cid):
    row=q_at(q,pd.Timestamp(dt),str(cid))
    return row


def trade(con,opt_path,u,row,legs):
    entry=pd.Timestamp(row.date)
    harvest_limit=min(entry+pd.Timedelta(days=HOLD_MAX),legs["harvest_expiry"])
    # Tail continues to its own later expiry.
    tail_limit=legs["tail_expiry"]
    last=min(pd.Timestamp(u.date.max()),tail_limit)
    w=u[(u.date>=entry)&(u.date<=last)].reset_index(drop=True)
    if w.empty:return None,"NO_WINDOW"

    harvest_exit=pd.Timestamp(w[w.date<=harvest_limit].iloc[-1].date)
    tail_exit=pd.Timestamp(w[w.date<=tail_limit].iloc[-1].date)

    ids={k:legs[k]["id"] for k in ("atm","sc","wing","lp","sp")}
    all_ids=set(ids.values())
    q=quotes(con,opt_path,all_ids,entry,tail_exit)
    vals=[
      executable(Q(q,entry,ids["atm"]),"BUY"),
      executable(Q(q,entry,ids["sc"]),"SELL"),
      executable(Q(q,entry,ids["wing"]),"BUY"),
      executable(Q(q,entry,ids["lp"]),"BUY"),
      executable(Q(q,entry,ids["sp"]),"SELL"),
    ]
    if any(pd.isna(x) for x in vals):return None,"NO_ENTRY_QUOTES"
    entry_cf=(vals[0]-N*vals[1]+N*vals[2]+vals[3]-vals[4])*100.0
    cash=-float(entry_cf)
    eq=[]

    for _,r in w.iterrows():
        dt=pd.Timestamp(r.date)

        if dt==harvest_exit:
            cvals=[
              executable(Q(q,dt,ids["atm"]),"SELL"),
              executable(Q(q,dt,ids["sc"]),"BUY"),
              executable(Q(q,dt,ids["wing"]),"SELL"),
            ]
            if any(pd.isna(x) for x in cvals):
                return None,"NO_HARVEST_EXIT_QUOTES"
            cash += (cvals[0]-N*cvals[1]+N*cvals[2])*100.0

        if dt==tail_exit:
            pvals=[
              executable(Q(q,dt,ids["lp"]),"SELL"),
              executable(Q(q,dt,ids["sp"]),"BUY"),
            ]
            if any(pd.isna(x) for x in pvals):
                return None,"NO_TAIL_EXIT_QUOTES"
            cash += (pvals[0]-pvals[1])*100.0

        active_calls=dt<harvest_exit
        active_tail=dt<tail_exit

        mark=0.0
        if active_calls:
            cm=[]
            for cid in ("atm","sc","wing"):
                cm.append(midpoint(Q(q,dt,ids[cid])))
            if any(pd.isna(x) for x in cm):
                return None,"NO_MTM_QUOTES"
            mark += (cm[0]-N*cm[1]+N*cm[2])*100.0
        if active_tail:
            pm=[]
            for cid in ("lp","sp"):
                pm.append(midpoint(Q(q,dt,ids[cid])))
            if any(pd.isna(x) for x in pm):
                return None,"NO_MTM_QUOTES"
            mark += (pm[0]-pm[1])*100.0

        eq.append((dt,CAPITAL+cash+mark))

        # Once both sleeves are realized, trade is complete.
        if dt==tail_exit:
            break

    pnl=cash
    return {
      "entry":entry,
      "harvest_exit":harvest_exit,
      "tail_exit":tail_exit,
      "pnl_usd":float(pnl),
      "return_pct":float(100*pnl/CAPITAL),
      "entry_cashflow_usd":float(entry_cf),
      "harvest_expiry":str(legs["harvest_expiry"].date()),
      "tail_expiry":str(legs["tail_expiry"].date()),
      "eq":eq
    },"OK"


def candidates(con,opt_path,u):
    out=[];rej={}
    for _,row in u.iterrows():
        if not bool(row.signal):continue
        legs=select_entry(con,opt_path,row.date)
        if legs is None:
            rej["NO_ENTRY_LEGS"]=rej.get("NO_ENTRY_LEGS",0)+1;continue
        tr,s=trade(con,opt_path,u,row,legs)
        if tr is None:
            rej[s]=rej.get(s,0)+1;continue
        out.append(tr)
    return sorted(out,key=lambda x:pd.Timestamp(x["entry"])),rej


def admit(cs,max_layers=STACK):
    sel=[];act=[]
    for tr in cs:
        en=pd.Timestamp(tr["entry"])
        act=[x for x in act if pd.Timestamp(x["tail_exit"])>=en]
        if len(act)>=max_layers:continue
        sel.append(tr);act.append(tr)
    return sel


def curve(selected,max_layers,dates):
    if not selected:return pd.DataFrame()
    alloc=CAPITAL/max_layers
    starts={};tails={};paths={}
    for i,tr in enumerate(selected):
        k=f"v{i:04d}"
        en=pd.Timestamp(tr["entry"]);ex=pd.Timestamp(tr["tail_exit"])
        starts.setdefault(en,[]).append((k,tr))
        tails.setdefault(ex,[]).append((k,tr))
        paths[k]=pd.DataFrame(tr["eq"],columns=["date","raw_nav"]).assign(
            date=lambda x:pd.to_datetime(x.date)).drop_duplicates("date").set_index("date")
    cash=CAPITAL;active={};done=set();rows=[]
    for dt0 in dates:
        dt=pd.Timestamp(dt0)
        for k,tr in tails.get(dt,[]):
            if k not in active:continue
            p=paths[k]
            raw=float(p.loc[dt,"raw_nav"]) if dt in p.index else float(p.iloc[-1].raw_nav)
            cash += alloc*raw/CAPITAL
            done.add(k);del active[k]
        for k,tr in starts.get(dt,[]):
            if k in done or k in active:continue
            cash-=alloc;active[k]=tr
        nav=float(cash)
        for k,tr in active.items():
            p=paths[k];hist=p.loc[p.index<=dt]
            if hist.empty:continue
            nav+=alloc*float(hist.iloc[-1].raw_nav)/CAPITAL
        rows.append({"date":dt,"nav":nav,"active_layers":len(active)})
    e=pd.DataFrame(rows)
    e["peak"]=e.nav.cummax();e["dd"]=e.nav/e.peak-1
    return e


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    op,up=ensure_data(Path(a.data_dir));u=load_underlying(up).copy().reset_index(drop=True);con=duckdb.connect()
    cs,rej=candidates(con,op,u);sel=admit(cs,STACK);eq=curve(sel,STACK,u.date.tolist())
    final=float(eq.nav.iloc[-1]);first=pd.Timestamp(eq.date.iloc[0]);last=pd.Timestamp(eq.date.iloc[-1]);yrs=max((last-first).days/365.25,1/365.25)
    report={
      "research_id":"QQQ_TAIL_BANK_V4",
      "status":"REAL_QQQ_CHAIN_CROSS_DATE_TAIL_PERSISTENCE",
      "contract":{
        "stack_layers":STACK,"allocation":"50% per vintage",
        "harvest":"+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ Call Wings",
        "tail":"+1 ~25Δ Long Put -1 ~10Δ Short Put",
        "harvest_expiry":"nearest listed expiry in 18-35 DTE",
        "tail_expiry":"next listed expiry after harvest expiry",
        "tail_persists_beyond_harvest":True,
        "within_vintage_migration":False,
        "optimization":False,"black_scholes":False,"interpolation":False
      },
      "data":{
        "options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up),
        "underlying_range":[str(pd.Timestamp(u.date.min()).date()),str(pd.Timestamp(u.date.max()).date())]
      },
      "results":{
        "candidate_signals":len(cs),"trades":len(sel),
        "entries_skipped_full":len(cs)-len(sel),
        "total_return_pct":100*(final/CAPITAL-1),
        "cagr":(final/CAPITAL)**(1/yrs)-1,
        "maxdd_daily_mtm":float(eq.dd.min()),
        "avg_active_layers":float(eq.active_layers.mean()),
        "max_active_layers":int(eq.active_layers.max()),
        "final_nav_usd":final,
        "rejections":rej
      }
    }
    pd.DataFrame([report["results"]]).to_csv(out/"summary.csv",index=False)
    if not eq.empty:eq.to_csv(out/"equity.csv",index=False)
    pd.DataFrame([{
      "vintage_id":f"v{i:04d}","entry":str(pd.Timestamp(x["entry"]).date()),
      "harvest_exit":str(pd.Timestamp(x["harvest_exit"]).date()),
      "tail_exit":str(pd.Timestamp(x["tail_exit"]).date()),
      "pnl_usd_100k_unit":x["pnl_usd"],
      "return_pct_unit":x["return_pct"],
      "harvest_expiry":x["harvest_expiry"],"tail_expiry":x["tail_expiry"]
    } for i,x in enumerate(sel)]).to_csv(out/"trades.csv",index=False)
    (out/"qqq_tail_bank_v4_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":main()
