#!/usr/bin/env python3
"""QQQ Profit-Recycle Loop Optionality V6.

Core idea:
  N=2 is the ordinary ratio-call base.
  Seed cycle: N+50 = 52 short-call/wing pairs against 1 ATM long call.
  After a cycle is realized, its realized P&L updates an independent
  opportunity-credit ledger:
      credit_next = max(0, credit_current + realized_pnl)
  When credit is positive enough to cover the incremental defined-loss proxy
  of N+20 (22 total pairs) versus N=2, the next eligible signal may deploy
  N+20. Otherwise it falls back to N=2.

The first seed cycle is forced to N+50, subject to the same 2% risk gate.
If it cannot pass the gate, the seed is rejected and no fake success is
recorded. The replay then continues with N=2.

This is deliberately a path-dependent experiment:
  realized outcome -> opportunity credit -> next-cycle ratio -> next outcome.

No optimization, Black-Scholes, interpolation, or look-ahead.
Real historical QQQ option-chain Bid/Ask only.
"""

from __future__ import annotations
import argparse, json, math
from pathlib import Path
import duckdb, numpy as np, pandas as pd

from qqq_ratio_call_harvest_v1 import (
    CAPITAL_USD, COOLDOWN_DAYS, DTE_MIN, DTE_MAX, HOLD_MAX,
    ensure_data, load_underlying, sha256_file
)

BASE_N=2
SEED_N=BASE_N+50
RECYCLE_N=BASE_N+20
RISK_PCT=2.0
CAPITAL=100000.0
SHORT_DELTA=0.20
WING_DELTA=0.08


def duck(con,sql,p=None):
    return con.execute(sql,p or []).df()


def chain(con,opt_path,dt,expiry=None):
    sql="""
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark,
             CAST(delta AS DOUBLE) AS delta,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume,
             UPPER(type) AS type
      FROM read_parquet(?)
      WHERE CAST(date AS DATE)=?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid
        AND delta IS NOT NULL
    """
    pars=[str(opt_path),pd.Timestamp(dt).date()]
    if expiry is None:
        sql += """ AND CAST(expiration AS DATE) BETWEEN
                   CAST(date AS DATE)+INTERVAL 18 DAY
                   AND CAST(date AS DATE)+INTERVAL 35 DAY"""
    else:
        sql += " AND CAST(expiration AS DATE)=?"
        pars.append(pd.Timestamp(expiry).date())
    x=duck(con,sql,pars)
    if x.empty:return x
    x["date"]=pd.to_datetime(x["date"]);x["expiration"]=pd.to_datetime(x["expiration"])
    x["dte"]=(x["expiration"]-pd.Timestamp(dt)).dt.days
    return x


def pick(df,delta,gt=None,lt=None):
    x=df.copy()
    if gt is not None:x=x[x.strike>float(gt)]
    if lt is not None:x=x[x.strike<float(lt)]
    if x.empty:return None
    x=x.assign(err=(x.delta-float(delta)).abs())
    return x.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]


def select_legs(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    ex=(r.groupby("expiration",as_index=False)
          .agg(dte=("dte","first"),mv=("volume","max"))
          .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(ex)]
    c=g[g.type=="CALL"]
    atm=pick(c,0.50)
    if atm is None:return None
    short=pick(c,SHORT_DELTA,gt=atm.strike)
    if short is None:return None
    wing=pick(c,WING_DELTA,gt=short.strike)
    if wing is None:return None
    return {
      "expiry":pd.Timestamp(ex),
      "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
      "short":{"id":str(short.contract_id),"k":float(short.strike)},
      "wing":{"id":str(wing.contract_id),"k":float(wing.strike)}
    }


def quotes(con,opt_path,ids,start,end):
    ids=sorted({str(x) for x in ids})
    q=duck(con,"""
      SELECT CAST(date AS DATE) AS date,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
    """,[str(opt_path),ids,pd.Timestamp(start).date(),pd.Timestamp(end).date()])
    if q.empty:return q
    q["date"]=pd.to_datetime(q.date);q["contract_id"]=q.contract_id.astype(str)
    return q.drop_duplicates(["date","contract_id"]).set_index(["date","contract_id"]).sort_index()


def q_at(q,dt,cid):
    try:r=q.loc[(pd.Timestamp(dt),str(cid))]
    except KeyError:return None
    return {"bid":float(r.bid),"ask":float(r.ask),"mark":float(r.mark)}


def ex(q,side):
    if q is None or pd.isna(q["bid"]) or pd.isna(q["ask"]):return np.nan
    return float(q["ask"] if side=="BUY" else q["bid"])


def mid(q):
    if q is None:return np.nan
    if pd.notna(q["bid"]) and pd.notna(q["ask"]):
        return (float(q["bid"])+float(q["ask"]))/2
    if pd.notna(q["mark"]):return float(q["mark"])
    return np.nan


def max_loss_proxy(legs,n,spot):
    atm_k=float(legs["atm"]["k"]); short_k=float(legs["short"]["k"]); wing_k=float(legs["wing"]["k"])
    grid=np.linspace(max(1.0,spot*0.2),max(spot*2.5,wing_k*1.25),1200)
    initial=(float(legs["atm"]["ask"])-n*float(legs["short"]["bid"])+n*float(legs["wing"]["ask"]))*100
    payoff=(np.maximum(grid-atm_k,0)-n*np.maximum(grid-short_k,0)+n*np.maximum(grid-wing_k,0))*100
    return max(0.0,-float(np.min(payoff-initial)))


def run_trade(con,opt_path,u,row,legs,n):
    entry=pd.Timestamp(row.date)
    end=min(entry+pd.Timedelta(days=HOLD_MAX),pd.Timestamp(legs["expiry"]))
    d=u[(u.date>=entry)&(u.date<=end)].copy().reset_index(drop=True)
    if d.empty:return None,"NO_WINDOW"

    ids=[legs["atm"]["id"],legs["short"]["id"],legs["wing"]["id"]]
    q=quotes(con,opt_path,ids,entry,end)
    qa=q_at(q,entry,ids[0]);qs=q_at(q,entry,ids[1]);qw=q_at(q,entry,ids[2])
    vals=[ex(qa,"BUY"),ex(qs,"SELL"),ex(qw,"BUY")]
    if any(pd.isna(v) for v in vals):return None,"NO_ENTRY_QUOTES"

    risk=max_loss_proxy(legs,n,float(row.close))
    if risk>CAPITAL_USD*(RISK_PCT/100):return None,"RISK_GATE"

    entry_cf=(vals[0]-n*vals[1]+n*vals[2])*100
    cash=-float(entry_cf)
    eq=[]
    for _,r in d.iterrows():
        dt=pd.Timestamp(r.date)
        ma,ms,mw=mid(q_at(q,dt,ids[0])),mid(q_at(q,dt,ids[1])),mid(q_at(q,dt,ids[2]))
        if not any(pd.isna(v) for v in (ma,ms,mw)):
            eq.append((dt,CAPITAL+cash+ma*100-n*ms*100+n*mw*100))

    exit_dt=pd.Timestamp(d.iloc[-1].date)
    qa=q_at(q,exit_dt,ids[0]);qs=q_at(q,exit_dt,ids[1]);qw=q_at(q,exit_dt,ids[2])
    vals=[ex(qa,"SELL"),ex(qs,"BUY"),ex(qw,"SELL")]
    if any(pd.isna(v) for v in vals):return None,"NO_EXIT_QUOTES"
    exit_cf=(vals[0]-n*vals[1]+n*vals[2])*100
    pnl=cash+float(exit_cf)
    eq.append((exit_dt,CAPITAL+pnl))
    return {
      "entry":entry,"exit":exit_dt,"n":int(n),"pnl_usd":float(pnl),
      "return_pct":float(100*pnl/CAPITAL),
      "entry_cashflow_usd":float(entry_cf),
      "risk_proxy_usd":float(risk),"eq":eq
    },"OK"


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)

    op,up=ensure_data(Path(a.data_dir))
    u=load_underlying(up).copy().reset_index(drop=True)
    con=duckdb.connect()

    static=[];loop=[];rejects={}
    credit=0.0
    seeded=False
    next_allowed=None
    candidate_count=0

    for _,row in u.iterrows():
        dt=pd.Timestamp(row.date)
        if next_allowed is not None and dt<=next_allowed:continue
        if not bool(row.signal):continue
        candidate_count+=1

        legs=select_legs(con,op,dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"]=rejects.get("NO_ENTRY_LEGS",0)+1
            continue

        # Always compute the ordinary N=2 comparator on the same candidate.
        st,sstatus=run_trade(con,op,u,row,legs,BASE_N)
        if st is None:
            rejects[sstatus]=rejects.get(sstatus,0)+1
            continue

        # First eligible cycle is the N+50 seed. Subsequent cycles can use
        # N+20 only when prior realized credit covers its incremental risk.
        desired=BASE_N
        reason="BASE_N"
        if not seeded:
            desired=SEED_N
            reason="SEED_N_PLUS_50"
        else:
            incremental=max(0.0,max_loss_proxy(legs,RECYCLE_N,float(row.close))
                               -max_loss_proxy(legs,BASE_N,float(row.close)))
            if credit>=incremental and credit>0:
                desired=RECYCLE_N
                reason="CREDIT_FUNDED_N_PLUS_20"
            else:
                desired=BASE_N
                reason="CREDIT_INSUFFICIENT"

        tr,status=run_trade(con,op,u,row,legs,desired)
        if tr is None:
            rejects[f"{reason}:{status}"]=rejects.get(f"{reason}:{status}",0)+1
            # A failed seed does not create a fake credit or a fake success.
            next_allowed=st["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)
            continue

        tr["ratio_reason"]=reason
        tr["credit_before"]=float(credit)

        # Opportunity bank is a realized-profit ledger, not a second cash NAV.
        # Losses burn the bank; gains rebuild it.
        credit=max(0.0,credit+float(tr["pnl_usd"]))
        tr["credit_after"]=float(credit)

        if not seeded and desired==SEED_N:
            seeded=True

        loop.append(tr)
        static.append(st)
        next_allowed=max(st["exit"],tr["exit"])+pd.Timedelta(days=COOLDOWN_DAYS)

    def seq(trades):
        if not trades:return pd.DataFrame()
        nav=CAPITAL;rows=[]
        for tr in sorted(trades,key=lambda x:pd.Timestamp(x["entry"])):
            scale=1.0
            for dt,raw in tr["eq"]:
                rows.append((pd.Timestamp(dt),nav*float(raw)/CAPITAL))
            nav*=1+float(tr["pnl_usd"])/CAPITAL
        e=pd.DataFrame(rows,columns=["date","nav"]).groupby("date",as_index=False).nav.last().sort_values("date")
        e["peak"]=e.nav.cummax();e["dd"]=e.nav/e.peak-1
        return e

    def summarize(ts,label):
        e=seq(ts)
        if e.empty:return {"mode":label,"trades":0}
        first,last=pd.Timestamp(e.date.iloc[0]),pd.Timestamp(e.date.iloc[-1])
        yrs=max((last-first).days/365.25,1/365.25)
        return {
          "mode":label,"trades":len(ts),
          "win_rate":float(np.mean([x["pnl_usd"]>0 for x in ts])),
          "avg_trade_usd":float(np.mean([x["pnl_usd"] for x in ts])),
          "worst_trade_usd":float(np.min([x["pnl_usd"] for x in ts])),
          "best_trade_usd":float(np.max([x["pnl_usd"] for x in ts])),
          "total_return_pct":float(100*(e.nav.iloc[-1]/CAPITAL-1)),
          "cagr":float((e.nav.iloc[-1]/CAPITAL)**(1/yrs)-1),
          "maxdd_daily_mtm":float(e.dd.min()),
          "data_start":str(first.date()),"data_end":str(last.date())
        }

    sl=summarize(static,"STATIC_N2_SAME_CANDIDATES")
    ll=summarize(loop,"PROFIT_RECYCLE_LOOP")

    ratios=pd.DataFrame([{
      "entry":str(x["entry"].date()),"exit":str(x["exit"].date()),
      "n":x["n"],"ratio_reason":x["ratio_reason"],
      "credit_before":x["credit_before"],"pnl_usd":x["pnl_usd"],
      "credit_after":x["credit_after"],"risk_proxy_usd":x["risk_proxy_usd"]
    } for x in loop])
    ratios.to_csv(out/"loop_ledger.csv",index=False)
    e=seq(loop)
    if not e.empty:e.to_csv(out/"equity.csv",index=False)

    report={
      "research_id":"QQQ_PROFIT_RECYCLE_LOOP_V6",
      "status":"REAL_QQQ_CHAIN_PATH_DEPENDENT_OPPORTUNITY_LEDGER",
      "contract":{
        "base_N":BASE_N,
        "seed_ratio":"N+50 = 52 short-call/wing pairs vs 1 ATM Long Call",
        "recycle_ratio":"N+20 = 22 pairs vs 1 ATM Long Call",
        "first_cycle":"forced seed, subject to existing 2% risk gate",
        "next_cycle":"22 only if prior realized opportunity credit covers incremental risk proxy; else N=2",
        "credit_update":"max(0, prior_credit + realized_pnl)",
        "credit_is":"decision/risk permission ledger, not extra cash NAV",
        "cooldown":COOLDOWN_DAYS,
        "black_scholes":False,"interpolation":False,"optimization":False
      },
      "data":{
        "options_sha256":sha256_file(op),
        "underlying_sha256":sha256_file(up),
        "underlying_range":[str(u.date.min().date()),str(u.date.max().date())]
      },
      "results":{
        "candidate_signals":candidate_count,
        "static_comparator":sl,
        "loop":ll,
        "final_opportunity_credit_usd":credit,
        "seed_was_activated":seeded,
        "loop_ratio_counts":ratios.n.value_counts().to_dict() if not ratios.empty else {}
      },
      "rejections":rejects
    }
    pd.DataFrame([sl,ll]).to_csv(out/"summary.csv",index=False)
    (out/"qqq_profit_recycle_loop_v6_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":main()
