#!/usr/bin/env python3
"""QQQ Cross N4 Threshold V13-Fast diagnostic.

Evaluate N=2..20 on every valid original signal using the same real-chain entry geometry and max-loss proxy. No trading or optimization.
"""

from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd
from qqq_profit_recycle_loop_v6 import ensure_data,load_underlying,chain,pick,sha256_file

CAPITAL_USD=64102.5641025641
GATE_USD=CAPITAL_USD*0.02
NODES=tuple(range(2,21))

def max_loss_proxy(legs,n,spot,qa,qs,qw):
    atm_k=float(legs["atm"]["k"]); short_k=float(legs["short"]["k"]); wing_k=float(legs["wing"]["k"])
    grid=np.linspace(max(1.0,spot*0.2),max(spot*2.5,wing_k*1.25),1200)
    initial=(float(qa["ask"])-n*float(qs["bid"])+n*float(qw["ask"]))*100
    payoff=(np.maximum(grid-atm_k,0)-n*np.maximum(grid-short_k,0)+n*np.maximum(grid-wing_k,0))*100
    return max(0.0,-float(np.min(payoff-initial)))


def q_at(q,dt,cid):
    try:r=q.loc[(pd.Timestamp(dt),str(cid))]
    except KeyError:return None
    return {"bid":float(r.bid),"ask":float(r.ask),"mark":float(r.mark)}

def fetch_entry_quotes(con,opt_path,ids,dt):
    df=con.execute("""SELECT CAST(date AS DATE) AS date,
                             CAST(contract_id AS VARCHAR) AS contract_id,
                             CAST(bid AS DOUBLE) bid,CAST(ask AS DOUBLE) ask,
                             CAST(mark AS DOUBLE) mark
                      FROM read_parquet(?)
                      WHERE CAST(date AS DATE)=?
                        AND CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))""",
                   [str(opt_path),pd.Timestamp(dt).date(),[str(x) for x in ids]]).df()
    if df.empty:return df
    return df.set_index(["date","contract_id"])

def pick_legs(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    ex=(r.groupby("expiration",as_index=False).agg(dte=("dte","first"),mv=("volume","max"))
        .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(ex)]
    c=g[g.type=="CALL"];atm=pick(c,0.50)
    if atm is None:return None
    sc=pick(c,0.20,gt=atm.strike); wing=pick(c,0.08,gt=sc.strike) if sc is not None else None
    if sc is None or wing is None:return None
    return {"expiry":pd.Timestamp(ex),"atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
            "short":{"id":str(sc.contract_id),"k":float(sc.strike)},"wing":{"id":str(wing.contract_id),"k":float(wing.strike)}}

def fetch_all_signal_chains(con,opt_path,dates):
    ds=[pd.Timestamp(x).date() for x in dates]
    q=con.execute("""
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
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 18 DAY
        AND CAST(date AS DATE)+INTERVAL 35 DAY
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid
        AND delta IS NOT NULL
    """,[str(opt_path),ds]).df()
    if q.empty:return {}
    q["date"]=pd.to_datetime(q["date"])
    q["expiration"]=pd.to_datetime(q["expiration"])
    q["dte"]=(q["expiration"]-q["date"]).dt.days
    return {d:g for d,g in q.groupby("date")}

def pick_legs_from_chain(r):
    if r is None or r.empty:return None
    ex=(r[(r.dte>=18)&(r.dte<=35)]
        .groupby("expiration",as_index=False).agg(dte=("dte","first"),mv=("volume","max"))
        .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(ex)]
    c=g[g.type=="CALL"]
    atm=pick(c,0.50)
    if atm is None:return None
    sc=pick(c,0.20,gt=atm.strike)
    wing=pick(c,0.08,gt=sc.strike) if sc is not None else None
    if sc is None or wing is None:return None
    return {"expiry":pd.Timestamp(ex),
            "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
            "short":{"id":str(sc.contract_id),"k":float(sc.strike)},
            "wing":{"id":str(wing.contract_id),"k":float(wing.strike)}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    op,up=ensure_data(Path(a.data_dir));u=load_underlying(up).copy().reset_index(drop=True);con=duckdb.connect()
    rows=[];rej={}
    sig=u[u.signal.astype(bool)].copy()
    chains=fetch_all_signal_chains(con,op,sig.date.tolist())
    for _,r in sig.iterrows():
        c=chains.get(pd.Timestamp(r.date))
        legs=pick_legs_from_chain(c)
        if legs is None: rej["NO_ENTRY_LEGS"]=rej.get("NO_ENTRY_LEGS",0)+1; continue
        entry=c[c["date"]==pd.Timestamp(r.date)].copy().set_index(["date","contract_id"])
        qa=q_at(entry,r.date,legs["atm"]["id"]);qs=q_at(entry,r.date,legs["short"]["id"]);qw=q_at(entry,r.date,legs["wing"]["id"])
        if any(x is None for x in (qa,qs,qw)): rej["NO_ENTRY_QUOTES"]=rej.get("NO_ENTRY_QUOTES",0)+1; continue
        r2=float(max_loss_proxy(legs,2,float(r.close),qa,qs,qw))
        for n in NODES:
            rp=float(max_loss_proxy(legs,n,float(r.close),qa,qs,qw))
            rows.append({"date":str(pd.Timestamp(r.date).date()),"n":n,"risk_proxy_usd":rp,
                         "incremental_vs_n2_usd":max(0.0,rp-r2),
                         "gate_usd":GATE_USD,"pass_2pct":rp<=GATE_USD})
    df=pd.DataFrame(rows);df.to_csv(out/"risk_ladder.csv",index=False)
    s=df.groupby("n").agg(signals=("date","count"),risk_mean=("risk_proxy_usd","mean"),
      risk_median=("risk_proxy_usd","median"),risk_p95=("risk_proxy_usd",lambda x:float(x.quantile(.95))),
      risk_max=("risk_proxy_usd","max"),pass_count=("pass_2pct","sum")).reset_index()
    s["pass_rate"]=s.pass_count/s.signals
    r2=float(s.loc[s.n==2,"risk_mean"].iloc[0]);s["incremental_vs_n2_mean"]=s.risk_mean-r2
    s.to_csv(out/"summary.csv",index=False)
    report={"research_id":"QQQ_CROSS_N4_THRESHOLD_V13_FAST","status":"DIAGNOSTIC_REAL_QQQ_CHAIN",
      "nodes":list(range(2,21)),"gate_usd":GATE_USD,"data":{"options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up)},
      "summary":s.to_dict(orient="records"),"rejections":rej}
    (out/"qqq_cross_n4_threshold_v13_fast_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":main()
