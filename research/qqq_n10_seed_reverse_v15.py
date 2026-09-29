#!/usr/bin/env python3
"""QQQ N10 seed -> reverse rights bank V15.

Contract:
- First valid signal: execute exactly one N=10 ratio-call trade, subject to the
  original mechanical 2% base risk gate. This is the purchased seed right.
- After the seed is realized, its realized P&L becomes a separate opportunity
  bank (not NAV/cash).
- Every later cycle may reproduce only a smaller N in {2..9}. N=10 is never
  re-issued.
- Choose the largest N<=9 whose real-chain defined-loss proxy is <=
  base 2% risk gate + current bank.
- After each realized offspring trade: bank=max(0, bank + realized P&L).
- No BS, no interpolation, no fitting, no result-based selection.
- Same real QQQ option chain, entry/exit Bid/Ask and Mid marking as V14.
"""

from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd

from qqq_profit_recycle_loop_v6 import (
    ensure_data,load_underlying,chain,pick,quotes,q_at,ex,mid,sha256_file
)

BASE_N=2
SEED_N=10
MAX_OFFSPRING_N=9
CAPITAL=100000.0
RISK_PCT=2.0
CAPITAL_USD=64102.5641025641


def max_loss_proxy(legs,n,spot,qa,qs,qw):
    atm_k=float(legs["atm"]["k"]); short_k=float(legs["short"]["k"]); wing_k=float(legs["wing"]["k"])
    grid=np.linspace(max(1.0,spot*0.2),max(spot*2.5,wing_k*1.25),1200)
    initial=(float(qa["ask"])-n*float(qs["bid"])+n*float(qw["ask"]))*100
    payoff=(np.maximum(grid-atm_k,0)-n*np.maximum(grid-short_k,0)+n*np.maximum(grid-wing_k,0))*100
    return max(0.0,-float(np.min(payoff-initial)))


def select_legs(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    exd=(r.groupby("expiration",as_index=False)
         .agg(dte=("dte","first"),mv=("volume","max"))
         .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(exd)]
    c=g[g.type=="CALL"]; atm=pick(c,0.50)
    if atm is None:return None
    sc=pick(c,0.20,gt=atm.strike)
    if sc is None:return None
    wing=pick(c,0.08,gt=sc.strike)
    if wing is None:return None
    return {"expiry":pd.Timestamp(exd),
            "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
            "short":{"id":str(sc.contract_id),"k":float(sc.strike)},
            "wing":{"id":str(wing.contract_id),"k":float(wing.strike)}}


def entry_quotes(con,opt_path,legs,dt):
    ids=[legs["atm"]["id"],legs["short"]["id"],legs["wing"]["id"]]
    q=quotes(con,opt_path,ids,dt,dt)
    return ids,q,q_at(q,dt,ids[0]),q_at(q,dt,ids[1]),q_at(q,dt,ids[2])


def run_trade(con,opt_path,u,row,legs,n):
    entry=pd.Timestamp(row.date)
    end=min(entry+pd.Timedelta(days=30),pd.Timestamp(legs["expiry"]))
    d=u[(u.date>=entry)&(u.date<=end)].copy().reset_index(drop=True)
    if d.empty:return None,"NO_WINDOW"
    ids,q,qa,qs,qw=entry_quotes(con,opt_path,legs,entry)
    if any(v is None for v in (qa,qs,qw)):return None,"NO_ENTRY_QUOTES"
    risk=max_loss_proxy(legs,n,float(row.close),qa,qs,qw)
    base_gate=CAPITAL_USD*(RISK_PCT/100)
    if risk>base_gate:return None,"RISK_GATE"
    entry_cf=(ex(qa,"BUY")-n*ex(qs,"SELL")+n*ex(qw,"BUY"))*100.0
    cash=-entry_cf;eq=[]
    for _,r in d.iterrows():
        dt=pd.Timestamp(r.date)
        ma,ms,mw=mid(q_at(q,dt,ids[0])),mid(q_at(q,dt,ids[1])),mid(q_at(q,dt,ids[2]))
        if not any(pd.isna(v) for v in (ma,ms,mw)):
            eq.append((dt,CAPITAL+cash+ma*100-n*ms*100+n*mw*100))
    exit_dt=pd.Timestamp(d.iloc[-1].date)
    vals=[ex(q_at(q,exit_dt,ids[0]),"SELL"),
          ex(q_at(q,exit_dt,ids[1]),"BUY"),
          ex(q_at(q,exit_dt,ids[2]),"SELL")]
    if any(pd.isna(v) for v in vals):return None,"NO_EXIT_QUOTES"
    exit_cf=(vals[0]-n*vals[1]+n*vals[2])*100.0
    pnl=cash+exit_cf
    eq.append((exit_dt,CAPITAL+pnl))
    return {"entry":entry,"exit":exit_dt,"n":n,"pnl_usd":float(pnl),
            "return_pct":float(100*pnl/CAPITAL),"risk_proxy_usd":float(risk),
            "entry_cashflow_usd":float(entry_cf),"eq":eq},"OK"


def seq(ts):
    if not ts:return pd.DataFrame()
    nav=CAPITAL;rows=[]
    for tr in sorted(ts,key=lambda x:pd.Timestamp(x["entry"])):
        for dt,raw in tr["eq"]:rows.append((pd.Timestamp(dt),nav*float(raw)/CAPITAL))
        nav*=1+tr["pnl_usd"]/CAPITAL
    e=(pd.DataFrame(rows,columns=["date","nav"]).groupby("date",as_index=False).nav.last()
       .sort_values("date"))
    e["peak"]=e.nav.cummax();e["dd"]=e.nav/e.peak-1
    return e


def summary(ts,e,label):
    if e.empty:return {"mode":label,"trades":0}
    yrs=max((pd.Timestamp(e.date.iloc[-1])-pd.Timestamp(e.date.iloc[0])).days/365.25,1/365.25)
    return {"mode":label,"trades":len(ts),
            "avg_trade_usd":float(np.mean([x["pnl_usd"] for x in ts])),
            "win_rate":float(np.mean([x["pnl_usd"]>0 for x in ts])),
            "total_return_pct":float(100*(e.nav.iloc[-1]/CAPITAL-1)),
            "cagr":float((e.nav.iloc[-1]/CAPITAL)**(1/yrs)-1),
            "maxdd_daily_mtm":float(e.dd.min()),
            "max_n":int(max([x["n"] for x in ts],default=0)),
            "funded_offspring_trades":int(sum(x.get("offspring",False) for x in ts))}


def simulate(con,op,u,signals,mode):
    bank=0.0; parent_n=None; next_allowed=None; trades=[]; rows=[]; rejects={}; seed_seen=False
    for _,row in signals.iterrows():
        dt=pd.Timestamp(row.date)
        if next_allowed is not None and dt<=next_allowed: continue

        legs=select_legs(con,op,dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"]=rejects.get("NO_ENTRY_LEGS",0)+1; continue

        ids,q,qa,qs,qw=entry_quotes(con,op,legs,dt)
        if any(v is None for v in (qa,qs,qw)):
            rejects["NO_ENTRY_QUOTES"]=rejects.get("NO_ENTRY_QUOTES",0)+1; continue

        r2=max_loss_proxy(legs,BASE_N,float(row.close),qa,qs,qw)
        risks={n:max_loss_proxy(legs,n,float(row.close),qa,qs,qw) for n in range(BASE_N,SEED_N+1)}
        base_gate=CAPITAL_USD*(RISK_PCT/100)

        if mode=="N10_SEED_REVERSE":
            if not seed_seen:
                target=SEED_N; reason="SEED_N10"
            else:
                affordable=[n for n in range(BASE_N,MAX_OFFSPRING_N+1)
                             if risks[n] <= base_gate + max(0.0,bank)]
                target=max(affordable) if affordable else None
                reason="BANK_BRED_SMALLER_N" if target is not None else "BANK_CANNOT_BREED"
        elif mode=="STATIC_N2":
            target=BASE_N; reason="STATIC_N2"
        else:
            raise ValueError(mode)

        if target is None:
            rejects[reason]=rejects.get(reason,0)+1
            continue

        tr,status=run_trade(con,op,u,row,legs,target)
        if tr is None:
            rejects[f"{reason}:{status}"]=rejects.get(f"{reason}:{status}",0)+1
            continue

        prev_bank=bank
        offspring=seed_seen
        target_risk=risks[target]
        incremental_vs_n2=max(0.0,target_risk-r2)
        tr.update({"reason":reason,"offspring":offspring,"bank_before_usd":float(prev_bank),
                   "bank_after_usd_precalc":float(max(0.0,prev_bank+tr["pnl_usd"])),
                   "parent_n":parent_n if parent_n is not None else "",
                   "base_gate_usd":float(base_gate),
                   "allowed_risk_usd":float(base_gate+max(0.0,prev_bank)),
                   "incremental_risk_vs_n2_usd":float(incremental_vs_n2)})
        trades.append(tr)
        rows.append({"entry":str(dt.date()),"exit":str(tr["exit"].date()),"n":target,
                     "reason":reason,"parent_n":parent_n if parent_n is not None else "",
                     "bank_before_usd":prev_bank,"pnl_usd":tr["pnl_usd"],
                     "bank_after_usd":max(0.0,prev_bank+tr["pnl_usd"]),
                     "risk_proxy_usd":target_risk,"incremental_risk_vs_n2_usd":incremental_vs_n2,
                     "allowed_risk_usd":base_gate+max(0.0,prev_bank),
                     "offspring":offspring})
        bank=max(0.0,prev_bank+float(tr["pnl_usd"]))
        parent_n=target
        seed_seen=True
        next_allowed=tr["exit"]+pd.Timedelta(days=10)

    e=seq(trades)
    return trades,e,rows,rejects,bank


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",default="data")
    ap.add_argument("--out",default="artifacts")
    a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)

    op,up=ensure_data(Path(a.data_dir))
    u=load_underlying(up).copy().reset_index(drop=True)
    signals=u[u.signal==True].copy().reset_index(drop=True)
    con=duckdb.connect()

    dyn,e_dyn,rows_dyn,reject_dyn,bank_dyn=simulate(con,op,u,signals,"N10_SEED_REVERSE")
    base,e_base,rows_base,reject_base,bank_base=simulate(con,op,u,signals,"STATIC_N2")

    sd=summary(dyn,e_dyn,"N10_SEED_REVERSE")
    sb=summary(base,e_base,"STATIC_N2")

    pd.DataFrame(rows_dyn).to_csv(out/"n10_seed_reverse_ledger.csv",index=False)
    pd.DataFrame(rows_base).to_csv(out/"static_n2_ledger.csv",index=False)
    if not e_dyn.empty:e_dyn.to_csv(out/"equity_n10_seed_reverse.csv",index=False)
    if not e_base.empty:e_base.to_csv(out/"equity_static_n2.csv",index=False)

    offspring=pd.DataFrame(rows_dyn)
    offspring_counts={}
    if not offspring.empty:
        for n,c in offspring[offspring.offspring==True].n.value_counts().sort_index().items():
            offspring_counts[str(int(n))]=int(c)

    report={"research_id":"QQQ_N10_SEED_REVERSE_RIGHTS_V15",
            "status":"REAL_QQQ_CHAIN_PATH_DEPENDENT",
            "contract":{
                "seed_n":SEED_N,"offspring_range":"2..9","n10_reissue":False,
                "seed_rule":"first valid signal executes N=10 only if mechanical base 2% risk gate passes",
                "bank_rule":"bank=max(0, bank + realized_pnl), bank is a separate opportunity-risk budget, not NAV",
                "offspring_rule":"largest N in 2..9 whose real-chain max-loss proxy <= base 2% gate + bank",
                "base_risk_gate_usd":CAPITAL_USD*(RISK_PCT/100),
                "lookahead":False,"black_scholes":False,"interpolation":False,"optimization":False},
            "data":{"options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up),
                    "signal_rows":int(len(signals))},
            "results":{"dynamic":sd,"static":sb,"dynamic_final_bank_usd":float(bank_dyn),
                       "offspring_n_counts":offspring_counts,
                       "dynamic_rejections":reject_dyn,
                       "static_rejections":reject_base}}
    (out/"qqq_n10_seed_reverse_v15_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":
    main()
