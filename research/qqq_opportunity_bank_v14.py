#!/usr/bin/env python3
"""QQQ Profit-Risk-Budget Loop V12.

Profit-funded risk-budget interpretation:
  - The first cycle is ordinary N=2; no unearned N+50 bootstrap is assumed.
  - After each cycle is realized, cumulative opportunity bank is updated as
    bank=max(0, bank + realized_pnl). The bank is a separate risk budget, not NAV.
  - Extra pairs are added one integer pair at a time, up to +20:
        N_target = 2 + k, 0 <= k <= 20
  - k is the largest integer for which the incremental defined-loss proxy
    from N=2 to N=2+k is <= previous realized profit.
  - Losses therefore cannot create new leverage; a profitable cycle creates
    a bounded next-cycle opportunity.

This is not an optimized k. It is a deterministic affordability rule.
The base N=2 trade remains under the original 2% gate. Previous positive realized P&L becomes a separate incremental risk budget for the next cycle.

No look-ahead, Black-Scholes, interpolation or fitting.
"""

from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd

from qqq_profit_recycle_loop_v6 import (
    ensure_data,load_underlying,chain,pick,quotes,q_at,ex,mid,sha256_file
)

def max_loss_proxy(legs,n,spot,qa,qs,qw):
    atm_k=float(legs["atm"]["k"]); short_k=float(legs["short"]["k"]); wing_k=float(legs["wing"]["k"])
    grid=np.linspace(max(1.0,spot*0.2),max(spot*2.5,wing_k*1.25),1200)
    initial=(float(qa["ask"])-n*float(qs["bid"])+n*float(qw["ask"]))*100
    payoff=(np.maximum(grid-atm_k,0)-n*np.maximum(grid-short_k,0)+n*np.maximum(grid-wing_k,0))*100
    return max(0.0,-float(np.min(payoff-initial)))


BASE_N=2
MAX_EXTRA=20
CAPITAL=100000.0
RISK_PCT=2.0
CAPITAL_USD=64102.5641025641


def select_legs(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    exd=(r.groupby("expiration",as_index=False).agg(dte=("dte","first"),mv=("volume","max"))
         .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(exd)]
    c=g[g.type=="CALL"];atm=pick(c,0.50)
    if atm is None:return None
    sc=pick(c,0.20,gt=atm.strike)
    if sc is None:return None
    wing=pick(c,0.08,gt=sc.strike)
    if wing is None:return None
    return {"expiry":pd.Timestamp(exd),
            "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
            "short":{"id":str(sc.contract_id),"k":float(sc.strike)},
            "wing":{"id":str(wing.contract_id),"k":float(wing.strike)}}


def run_trade(con,opt_path,u,row,legs,n,risk_budget_usd=0.0):
    entry=pd.Timestamp(row.date)
    end=min(entry+pd.Timedelta(days=30),pd.Timestamp(legs["expiry"]))
    d=u[(u.date>=entry)&(u.date<=end)].copy().reset_index(drop=True)
    if d.empty:return None,"NO_WINDOW"

    ids=[legs["atm"]["id"],legs["short"]["id"],legs["wing"]["id"]]
    q=quotes(con,opt_path,ids,entry,end)
    qa=q_at(q,entry,ids[0]);qs=q_at(q,entry,ids[1]);qw=q_at(q,entry,ids[2])
    if any(v is None for v in (qa,qs,qw)):return None,"NO_ENTRY_QUOTES"

    risk=max_loss_proxy(legs,n,float(row.close),qa,qs,qw)
    allowed_risk=CAPITAL_USD*(RISK_PCT/100)+max(0.0,float(risk_budget_usd))
    if risk>allowed_risk:return None,"RISK_GATE"

    entry_cf=(ex(qa,"BUY")-n*ex(qs,"SELL")+n*ex(qw,"BUY"))*100.0
    cash=-entry_cf;eq=[]
    for _,r in d.iterrows():
        dt=pd.Timestamp(r.date)
        ma,ms,mw=mid(q_at(q,dt,ids[0])),mid(q_at(q,dt,ids[1])),mid(q_at(q,dt,ids[2]))
        if not any(pd.isna(v) for v in (ma,ms,mw)):
            eq.append((dt,CAPITAL+cash+ma*100-n*ms*100+n*mw*100))
    exit_dt=pd.Timestamp(d.iloc[-1].date)
    vals=[ex(q_at(q,exit_dt,ids[0]),"SELL"),ex(q_at(q,exit_dt,ids[1]),"BUY"),ex(q_at(q,exit_dt,ids[2]),"SELL")]
    if any(pd.isna(v) for v in vals):return None,"NO_EXIT_QUOTES"
    exit_cf=(vals[0]-n*vals[1]+n*vals[2])*100.0
    pnl=cash+exit_cf;eq.append((exit_dt,CAPITAL+pnl))
    return {"entry":entry,"exit":exit_dt,"n":n,"pnl_usd":float(pnl),
            "return_pct":float(100*pnl/CAPITAL),"risk_proxy_usd":float(risk),
            "entry_cashflow_usd":float(entry_cf),"eq":eq},"OK"


def seq(ts):
    if not ts:return pd.DataFrame()
    nav=CAPITAL;rows=[]
    for tr in sorted(ts,key=lambda x:pd.Timestamp(x["entry"])):
        for dt,raw in tr["eq"]:rows.append((pd.Timestamp(dt),nav*float(raw)/CAPITAL))
        nav*=1+tr["pnl_usd"]/CAPITAL
    e=pd.DataFrame(rows,columns=["date","nav"]).groupby("date",as_index=False).nav.last().sort_values("date")
    e["peak"]=e.nav.cummax();e["dd"]=e.nav/e.peak-1
    return e


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    op,up=ensure_data(Path(a.data_dir));u=load_underlying(up).copy().reset_index(drop=True);con=duckdb.connect()

    opportunity_bank=0.0;next_allowed=None;rows=[];rejects={};base=[];ladder=[]

    for _,row in u.iterrows():
        dt=pd.Timestamp(row.date)
        if next_allowed is not None and dt<=next_allowed:continue
        if not bool(row.signal):continue
        legs=select_legs(con,op,dt)
        if legs is None:rejects["NO_ENTRY_LEGS"]=rejects.get("NO_ENTRY_LEGS",0)+1;continue

        bt,bs=run_trade(con,op,u,row,legs,BASE_N,0.0)
        if bt is None:rejects["BASE_"+bs]=rejects.get("BASE_"+bs,0)+1;continue
        base.append(bt)

        # Deterministic affordability ladder, based only on previous realized profit.
        qd=quotes(con,op,[legs["atm"]["id"],legs["short"]["id"],legs["wing"]["id"]],dt,dt)
        qa=q_at(qd,dt,legs["atm"]["id"]);qs=q_at(qd,dt,legs["short"]["id"]);qw=q_at(qd,dt,legs["wing"]["id"])
        k=0
        affordability=[]
        if all(v is not None for v in (qa,qs,qw)):
            r2=max_loss_proxy(legs,2,float(row.close),qa,qs,qw)
            for extra in range(1,MAX_EXTRA+1):
                rn=max_loss_proxy(legs,2+extra,float(row.close),qa,qs,qw)
                inc=max(0.0,rn-r2)
                affordability.append({"n":2+extra,"incremental_risk_proxy_usd":inc,"funded":opportunity_bank>=inc and opportunity_bank>0})
                if opportunity_bank>=inc and opportunity_bank>0:k=extra
                else:break
        target=BASE_N+k
        if target==BASE_N:
            reason="BASE_N_PREV_PROFIT_INSUFFICIENT"
        else:
            reason=f"PROFIT_FUNDED_PLUS_{k}"
        tr,status=run_trade(con,op,u,row,legs,target,opportunity_bank)
        if tr is None:
            rejects[f"{reason}:{status}"]=rejects.get(f"{reason}:{status}",0)+1
            # Previous profit is preserved because the funded attempt did not execute.
            next_allowed=bt["exit"]+pd.Timedelta(days=10)
            continue
        tr["reason"]=reason;tr["extra_pairs"]=k;tr["bank_before_usd"]=float(opportunity_bank)
        tr["new_profit_usd"]=float(tr["pnl_usd"])
        ladder.append(tr)
        rows.append({"entry":str(dt.date()),"n":target,"extra_pairs":k,"reason":reason,
                     "bank_before_usd":opportunity_bank,"risk_budget_usd":prev_profit,"allowed_risk_usd":CAPITAL_USD*(RISK_PCT/100)+prev_profit,"pnl_usd":tr["pnl_usd"],
                     "risk_proxy_usd":tr["risk_proxy_usd"]})
        opportunity_bank=max(0.0,float(opportunity_bank)+float(tr["pnl_usd"]))
        next_allowed=bt["exit"]+pd.Timedelta(days=10)

    eb=seq(base);el=seq(ladder)
    def summ(ts,e,label):
        if e.empty:return {"mode":label,"trades":0}
        yrs=max((pd.Timestamp(e.date.iloc[-1])-pd.Timestamp(e.date.iloc[0])).days/365.25,1/365.25)
        return {"mode":label,"trades":len(ts),
                "avg_trade_usd":float(np.mean([x["pnl_usd"] for x in ts])),
                "win_rate":float(np.mean([x["pnl_usd"]>0 for x in ts])),
                "total_return_pct":float(100*(e.nav.iloc[-1]/CAPITAL-1)),
                "cagr":float((e.nav.iloc[-1]/CAPITAL)**(1/yrs)-1),
                "maxdd_daily_mtm":float(e.dd.min()),
                "max_extra_pairs":int(max([x.get("extra_pairs",0) for x in ts],default=0)),
                "funded_trades":int(sum(x.get("extra_pairs",0)>0 for x in ts))}
    sb=summ(base,eb,"STATIC_N2");sl=summ(ladder,el,"PROFIT_FUNDED_LADDER")

    pd.DataFrame(rows).to_csv(out/"profit_funded_ledger.csv",index=False)
    pd.DataFrame([sb,sl]).to_csv(out/"summary.csv",index=False)
    if not el.empty:el.to_csv(out/"equity_profit_funded.csv",index=False)
    report={"research_id":"QQQ_PROFIT_RISK_BUDGET_LOOP_V12",
            "status":"REAL_QQQ_CHAIN_PATH_DEPENDENT_PROFIT_FUNDED_RISK_BUDGET",
            "contract":{"base_n":2,"max_extra_pairs":20,
                        "funding":"previous realized positive P&L is a separate incremental risk budget",
                        "rule":"largest integer extra-pair count whose incremental max-loss proxy is <= previous positive P&L",
                        "base_risk_gate_usd":CAPITAL_USD*(RISK_PCT/100),
                        "effective_next_cycle_risk_budget":"base_risk_gate_usd + cumulative opportunity bank",
                        "no_optimization":True,"black_scholes":False,"interpolation":False},
            "data":{"options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up)},
            "results":{"static":sb,"ladder":sl,"final_opportunity_bank":opportunity_bank,
                       "funded_trade_count":sum(x["extra_pairs"]>0 for x in ladder)},
            "rejections":rejects}
    (out/"qqq_opportunity_bank_v14_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":main()
