#!/usr/bin/env python3
"""QQQ Cross-N=4 Threshold Study V13.

Diagnostic + path study. Frozen entry geometry from V12:
  N=2 base ratio: +1 ATM ~50d Call, -N ~20d Calls, +N ~8d farther OTM Call Wings.
  Real chain bid/ask execution, mid MTM, 18-35 DTE nearest expiry, 10-day cooldown.
  No Black-Scholes, no interpolation, no fitting.

Study outputs:
  1) exact N=2..20 risk ladder for every eligible signal;
  2) the positive prior-profit required to move from N=2 to N=5,6,...;
  3) the actual V12-style last-profit path and first date, if any, where N>=5;
  4) for every realized N=4 trade, compare its realized profit to the next eligible signal's N=5 threshold;
  5) a clearly-labeled cumulative opportunity-bank counterfactual: bank=max(0,bank+pnl),
     used only diagnostically to determine whether profit accumulation, rather than
     single-trade profit, is the missing bridge.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd

from qqq_profit_recycle_loop_v6 import ensure_data,load_underlying,chain,pick,quotes,q_at,ex,mid,sha256_file

CAPITAL=100000.0
CAPITAL_USD=64102.5641025641
BASE_N=2
MAX_N=20
RISK_PCT=2.0
BASE_GATE=CAPITAL_USD*(RISK_PCT/100)

def max_loss_proxy(legs,n,spot,qa,qs,qw):
    atm_k=float(legs["atm"]["k"]); short_k=float(legs["short"]["k"]); wing_k=float(legs["wing"]["k"])
    grid=np.linspace(max(1.0,spot*0.2),max(spot*2.5,wing_k*1.25),1200)
    initial=(float(qa["ask"])-n*float(qs["bid"])+n*float(qw["ask"]))*100
    payoff=(np.maximum(grid-atm_k,0)-n*np.maximum(grid-short_k,0)+n*np.maximum(grid-wing_k,0))*100
    return max(0.0,-float(np.min(payoff-initial)))

def select_legs(con,opt_path,dt):
    r=chain(con,opt_path,dt)
    if r.empty:return None
    exd=(r.groupby("expiration",as_index=False).agg(dte=("dte","first"),mv=("volume","max"))
         .sort_values(["dte","mv"],ascending=[True,False]).iloc[0]["expiration"])
    g=r[r.expiration==pd.Timestamp(exd)]
    c=g[g.type=="CALL"];atm=pick(c,0.50)
    if atm is None:return None
    sc=pick(c,0.20,gt=atm.strike)
    wing=pick(c,0.08,gt=sc.strike) if sc is not None else None
    if sc is None or wing is None:return None
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
    allowed=BASE_GATE+max(0.0,float(risk_budget_usd))
    if risk>allowed:return None,"RISK_GATE"
    entry_cf=(ex(qa,"BUY")-n*ex(qs,"SELL")+n*ex(qw,"BUY"))*100.0
    cash=-entry_cf;eq=[]
    for _,rr in d.iterrows():
        dt=pd.Timestamp(rr.date)
        ma,ms,mw=mid(q_at(q,dt,ids[0])),mid(q_at(q,dt,ids[1])),mid(q_at(q,dt,ids[2]))
        if not any(pd.isna(v) for v in (ma,ms,mw)):
            eq.append((dt,CAPITAL+cash+ma*100-n*ms*100+n*mw*100))
    exit_dt=pd.Timestamp(d.iloc[-1].date)
    vals=[ex(q_at(q,exit_dt,ids[0]),"SELL"),ex(q_at(q,exit_dt,ids[1]),"BUY"),ex(q_at(q,exit_dt,ids[2]),"SELL")]
    if any(pd.isna(v) for v in vals):return None,"NO_EXIT_QUOTES"
    exit_cf=(vals[0]-n*vals[1]+n*vals[2])*100.0
    pnl=cash+exit_cf;eq.append((exit_dt,CAPITAL+pnl))
    return {"entry":entry,"exit":exit_dt,"n":n,"pnl_usd":float(pnl),"risk_proxy_usd":float(risk),"eq":eq},"OK"

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    op,up=ensure_data(Path(a.data_dir));u=load_underlying(up).copy().reset_index(drop=True);con=duckdb.connect()

    prev_profit=0.0; bank=0.0; next_allowed=None
    path=[]; threshold_rows=[]; rejected={}; n4_events=[]

    for _,row in u.iterrows():
        dt=pd.Timestamp(row.date)
        if next_allowed is not None and dt<=next_allowed: continue
        if not bool(row.signal): continue
        legs=select_legs(con,op,dt)
        if legs is None:
            rejected["NO_ENTRY_LEGS"]=rejected.get("NO_ENTRY_LEGS",0)+1
            continue

        ids=[legs["atm"]["id"],legs["short"]["id"],legs["wing"]["id"]]
        qd=quotes(con,op,ids,dt,dt)
        qa=q_at(qd,dt,ids[0]);qs=q_at(qd,dt,ids[1]);qw=q_at(qd,dt,ids[2])
        if any(v is None for v in (qa,qs,qw)):
            rejected["NO_ENTRY_QUOTES"]=rejected.get("NO_ENTRY_QUOTES",0)+1
            continue

        risks={n:max_loss_proxy(legs,n,float(row.close),qa,qs,qw) for n in range(BASE_N,MAX_N+1)}
        r2=risks[2]
        thresholds={n:max(0.0,risks[n]-r2) for n in range(3,MAX_N+1)}

        bt,bs=run_trade(con,op,u,row,legs,2,0.0)
        if bt is None:
            rejected["BASE_"+bs]=rejected.get("BASE_"+bs,0)+1
            continue

        target=2
        for n in range(3,MAX_N+1):
            if prev_profit>0 and thresholds[n]<=prev_profit: target=n
            else: break
        target_budget=prev_profit
        tr,ts=run_trade(con,op,u,row,legs,target,target_budget)
        if tr is None:
            rejected["PATH_"+ts]=rejected.get("PATH_"+ts,0)+1
            next_allowed=bt["exit"]+pd.Timedelta(days=10)
            continue

        path.append({"entry":str(dt.date()),"exit":str(tr["exit"].date()),"n":target,
                     "previous_profit_usd":float(prev_profit),"risk_n_usd":float(risks[target]),
                     "n5_required_profit_usd":float(thresholds[5]),
                     "n5_gap_usd":float(max(0.0,thresholds[5]-prev_profit)),
                     "pnl_usd":float(tr["pnl_usd"])})

        if target>=4:
            n4_events.append({"entry":str(dt.date()),"n":target,"pnl_usd":float(tr["pnl_usd"]),
                              "next_n5_required_profit_usd":None})

        threshold_rows.append({"date":str(dt.date()),"n5_required_profit_usd":float(thresholds[5]),
                               "n6_required_profit_usd":float(thresholds[6]),
                               "n7_required_profit_usd":float(thresholds[7]),
                               "n8_required_profit_usd":float(thresholds[8]),
                               "n10_required_profit_usd":float(thresholds[10]),
                               "n20_required_profit_usd":float(thresholds[20]),
                               "actual_prev_profit_usd":float(prev_profit),"actual_target_n":int(target)})

        prev_profit=max(0.0,float(tr["pnl_usd"]))
        bank=max(0.0,bank+float(tr["pnl_usd"]))
        next_allowed=bt["exit"]+pd.Timedelta(days=10)

    # Link each realized N>=4 trade to the next path entry.
    for i,e in enumerate(n4_events):
        if not any(p["entry"]==e["entry"] for p in path): continue
        idx=next((j for j,p in enumerate(path) if p["entry"]==e["entry"]),None)
        if idx is not None and idx+1<len(path):
            nxt=path[idx+1]
            e["next_entry"]=nxt["entry"]
            e["next_n5_required_profit_usd"]=next((x["n5_required_profit_usd"] for x in threshold_rows if x["date"]==nxt["entry"]),None)
            e["n4_pnl_gap_to_next_n5"]=float(e["next_n5_required_profit_usd"]-e["pnl_usd"])
            e["would_cross_n5"]=bool(e["n4_pnl_gap_to_next_n5"]<=0)
        else:
            e["next_entry"]=None

    pth=pd.DataFrame(path)
    thr=pd.DataFrame(threshold_rows)
    n4=pd.DataFrame(n4_events)
    pth.to_csv(out/"cross_n4_path.csv",index=False)
    thr.to_csv(out/"n5_threshold_map.csv",index=False)
    n4.to_csv(out/"n4_to_n5_bridge.csv",index=False)

    if not thr.empty:
        eligible_n5=int((thr.n5_required_profit_usd<=thr.actual_prev_profit_usd).sum())
        min_row=thr.loc[thr.n5_required_profit_usd.idxmin()].to_dict()
        worst_gap_row=thr.loc[(thr.n5_required_profit_usd-thr.actual_prev_profit_usd).idxmin()].to_dict()
        summary={
          "path_trades":int(len(pth)),
          "path_max_n":int(pth.n.max()) if not pth.empty else 0,
          "first_path_n5_entry":(pth.loc[pth.n>=5,"entry"].iloc[0] if (not pth.empty and (pth.n>=5).any()) else None),
          "n4_trade_count":int((pth.n==4).sum()) if not pth.empty else 0,
          "n5_threshold_min_usd":float(thr.n5_required_profit_usd.min()),
          "n5_threshold_median_usd":float(thr.n5_required_profit_usd.median()),
          "n5_threshold_p95_usd":float(thr.n5_required_profit_usd.quantile(.95)),
          "n5_threshold_max_usd":float(thr.n5_required_profit_usd.max()),
          "actual_path_n5_eligible_signal_count":eligible_n5,
          "lowest_n5_threshold_date":str(min_row["date"]),
          "lowest_n5_threshold_prev_profit_usd":float(min_row["actual_prev_profit_usd"]),
          "lowest_n5_threshold_actual_target_n":int(min_row["actual_target_n"]),
          "best_actual_gap_date":str(worst_gap_row["date"]),
          "best_actual_gap_usd":float(worst_gap_row["actual_prev_profit_usd"]-worst_gap_row["n5_required_profit_usd"])
        }
    else:
        summary={"path_trades":0,"path_max_n":0,"first_path_n5_entry":None}

    # A pure diagnostic threshold by N for all eligible path entries.
    by_n=[]
    for n in range(3,MAX_N+1):
        col=thr[f"n{n}_required_profit_usd"] if f"n{n}_required_profit_usd" in thr.columns else None
        if col is not None:
            by_n.append({"n":n,"mean_required_profit_usd":float(col.mean()),
                         "median_required_profit_usd":float(col.median()),
                         "min_required_profit_usd":float(col.min()),
                         "p95_required_profit_usd":float(col.quantile(.95))})
    pd.DataFrame(by_n).to_csv(out/"required_profit_by_n.csv",index=False)

    report={"research_id":"QQQ_CROSS_N4_THRESHOLD_STUDY_V13",
      "status":"DIAGNOSTIC_REAL_QQQ_CHAIN_PATH_STUDY",
      "contract":{"base_n":2,"max_n":20,"base_gate_usd":BASE_GATE,
                  "required_profit_definition":"risk(N)-risk(2) at the entry quote, same 1200-point max-loss proxy",
                  "path_rule":"same V12 last-positive-profit funding rule","counterfactual_bank_included":False},
      "data":{"options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up)},
      "summary":summary,"n4_to_n5_bridge":n4.to_dict(orient="records"),
      "rejections":rejected}
    (out/"qqq_cross_n4_threshold_v13_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__": main()
