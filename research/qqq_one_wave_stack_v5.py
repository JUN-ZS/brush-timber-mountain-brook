#!/usr/bin/env python3
"""QQQ One-Wave Stack V5.

Purpose: isolate whether the second within-vintage geometry migration
(30Δ -> 40Δ Short Call) is responsible for weakening the stacked strategy.

Cross-date stacking:
  1 layer, 2 layer half-stack, 4 layer stack.

Per vintage:
  +1 ~50Δ Call
  -2 ~20Δ Calls
  +2 ~8Δ Call Wings
  +1 ~25Δ Long Put
  -1 ~10Δ Short Put

Adaptive mode is deliberately ONE-WAVE only:
  upward wave trigger = previous close >= anchor close + 1 ATR20
  migrate on next trading day:
      Short Call 20Δ -> 30Δ
      Short Put 10Δ -> 5Δ
  no second migration.
Long Put, ATM Call, wings, N and expiry remain fixed.

Static vs one-wave adaptive are compared at each stack depth.
No optimization, BS, interpolation or look-ahead.
"""

from __future__ import annotations
import argparse, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

from qqq_ratio_call_harvest_v1 import ensure_data, load_underlying, sha256_file
from qqq_state_adaptive_geometry_v1 import (
    chain, pick, select_entry, quotes, Q, leg_mark, entry_cf, exit_cf,
    migration_cf
)

BASE=100000.0
N=2
STACKS={"1_LAYER":1,"2_LAYER_HALF_STACK":2,"4_LAYER_STACK":4}
CALL_TARGET=0.30
PUT_TARGET=0.05
ATR_MULT=1.0


def trade_one_wave(con,opt_path,u,row,legs,adaptive):
    entry=pd.Timestamp(row.date)
    last=min(entry+pd.Timedelta(days=30),pd.Timestamp(legs["expiry"]))
    w=u[(u.date>=entry)&(u.date<=last)].reset_index(drop=True)
    if w.empty:return None,"NO_WINDOW"

    base_ids={k:legs[k]["id"] for k in ("atm","sc20","wing","lp","sp10")}
    ids={"atm":base_ids["atm"],"sc":base_ids["sc20"],"wing":base_ids["wing"],
         "lp":base_ids["lp"],"sp":base_ids["sp10"]}

    migrations=[]
    if adaptive:
        anchor=float(row.close)
        wave_done=False
        for j in range(1,len(w)):
            if wave_done: break
            prev=w.iloc[j-1]
            atr=float(prev.atr20) if pd.notna(prev.atr20) else np.nan
            if pd.isna(atr): continue
            if float(prev.close) < anchor + ATR_MULT*atr: continue

            t1=pd.Timestamp(w.iloc[j].date)
            g=chain(con,opt_path,t1,legs["expiry"])
            if g.empty: continue
            c=g[g.type=="CALL"]; p=g[g.type=="PUT"]
            nc=pick(c,CALL_TARGET,gt=max(legs["atm"]["k"],float(w.iloc[j].close)),lt=legs["wing"]["k"])
            np_=pick(p,-PUT_TARGET,lt=min(legs["lp"]["k"],float(w.iloc[j].close)))
            if nc is None or np_ is None: continue
            newc,newp=str(nc.contract_id),str(np_.contract_id)
            if newc==ids["sc"] and newp==ids["sp"]: continue
            migrations.append({
                "date":t1,"wave":1,
                "call":{"id":newc,"k":float(nc.strike),"delta":float(nc.delta)},
                "put":{"id":newp,"k":float(np_.strike),"delta":float(np_.delta)}
            })
            wave_done=True

    all_ids=set(ids.values())|{m["call"]["id"] for m in migrations}|{m["put"]["id"] for m in migrations}
    q=quotes(con,opt_path,all_ids,entry,last)
    ec=entry_cf(q,entry,ids)
    if ec is None:return None,"NO_ENTRY_QUOTES"
    cash=-float(ec)
    active=dict(ids)
    events=[];eq=[]
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
                    "date":str(dt.date()),"migration_cashflow_usd":float(cf),
                    "old_call":oldc,"new_call":active["sc"],
                    "new_call_strike":m["call"]["k"],"new_call_delta":m["call"]["delta"],
                    "old_put":oldp,"new_put":active["sp"],
                    "new_put_strike":m["put"]["k"],"new_put_delta":m["put"]["delta"]
                })
        mk=leg_mark(q,dt,active)
        if pd.notna(mk):eq.append((dt,BASE+cash+mk))

    xc=exit_cf(q,pd.Timestamp(w.iloc[-1].date),active)
    if xc is None:return None,"NO_EXIT_QUOTES"
    pnl=cash+float(xc)
    eq.append((pd.Timestamp(w.iloc[-1].date),BASE+pnl))
    return {
        "entry":entry,"exit":pd.Timestamp(w.iloc[-1].date),
        "pnl_usd":float(pnl),"return_pct":float(100*pnl/BASE),
        "entry_cashflow_usd":float(ec),"migrations":events,"eq":eq
    },"OK"


def build(con,opt_path,u,adaptive):
    out=[];rej={}
    for _,row in u.iterrows():
        if not bool(row.signal):continue
        legs=select_entry(con,opt_path,row.date)
        if legs is None:
            rej["NO_ENTRY_LEGS"]=rej.get("NO_ENTRY_LEGS",0)+1;continue
        tr,s=trade_one_wave(con,opt_path,u,row,legs,adaptive)
        if tr is None:
            rej[s]=rej.get(s,0)+1;continue
        out.append(tr)
    return sorted(out,key=lambda x:pd.Timestamp(x["entry"])),rej


def admit(cands,k):
    selected=[];active=[]
    for tr in cands:
        en=pd.Timestamp(tr["entry"])
        active=[x for x in active if pd.Timestamp(x["exit"])>=en]
        if len(active)>=k:continue
        selected.append(tr);active.append(tr)
    return selected


def curve(selected,k,dates):
    if not selected:return pd.DataFrame()
    alloc=BASE/k
    starts={};exits={};paths={}
    for i,tr in enumerate(selected):
        key=f"v{i:04d}"
        en,ex=pd.Timestamp(tr["entry"]),pd.Timestamp(tr["exit"])
        starts.setdefault(en,[]).append((key,tr));exits.setdefault(ex,[]).append((key,tr))
        paths[key]=pd.DataFrame(tr["eq"],columns=["date","raw_nav"]).assign(
            date=lambda x:pd.to_datetime(x.date)).drop_duplicates("date").set_index("date")
    cash=BASE;active={};done=set();rows=[]
    for dt0 in dates:
        dt=pd.Timestamp(dt0)
        for key,tr in exits.get(dt,[]):
            if key not in active:continue
            p=paths[key];raw=float(p.loc[dt,"raw_nav"]) if dt in p.index else float(p.iloc[-1].raw_nav)
            cash+=alloc*raw/BASE;done.add(key);del active[key]
        for key,tr in starts.get(dt,[]):
            if key in done or key in active:continue
            cash-=alloc;active[key]=tr
        nav=cash
        for key,tr in active.items():
            p=paths[key];hist=p.loc[p.index<=dt]
            if not hist.empty:nav+=alloc*float(hist.iloc[-1].raw_nav)/BASE
        rows.append({"date":dt,"nav":nav,"active_layers":len(active)})
    e=pd.DataFrame(rows);e["peak"]=e.nav.cummax();e["dd"]=e.nav/e.peak-1
    return e


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    op,up=ensure_data(Path(a.data_dir));u=load_underlying(up).copy().reset_index(drop=True);con=duckdb.connect()
    sc,sr=build(con,op,u,False);ac,ar=build(con,op,u,True)
    results=[]
    for mode,cands,rej in [("STATIC",sc,sr),("ONE_WAVE_ADAPTIVE",ac,ar)]:
        for name,k in STACKS.items():
            sel=admit(cands,k);e=curve(sel,k,u.date.tolist())
            final=float(e.nav.iloc[-1]);start=pd.Timestamp(e.date.iloc[0]);end=pd.Timestamp(e.date.iloc[-1]);yrs=max((end-start).days/365.25,1/365.25)
            results.append({
              "mode":mode,"stack":name,"stack_layers":k,"trades":len(sel),
              "candidate_signals":len(cands),"entries_skipped_full":len(cands)-len(sel),
              "total_return_pct":100*(final/BASE-1),"cagr":(final/BASE)**(1/yrs)-1,
              "maxdd_daily_mtm":float(e.dd.min()),"avg_active_layers":float(e.active_layers.mean()),
              "max_active_layers":int(e.active_layers.max()),"final_nav_usd":final
            })
            if not e.empty:e.to_csv(out/f"equity_{mode}_{name}.csv",index=False)
            pd.DataFrame([{
              "vintage_id":f"v{i:04d}","entry":str(pd.Timestamp(x["entry"]).date()),
              "exit":str(pd.Timestamp(x["exit"]).date()),"pnl_usd":x["pnl_usd"],
              "migration_count":len(x["migrations"]), "migration_events_json":json.dumps(x["migrations"],ensure_ascii=False)
            } for i,x in enumerate(sel)]).to_csv(out/f"trades_{mode}_{name}.csv",index=False)
    pd.DataFrame(results).to_csv(out/"summary.csv",index=False)
    report={"research_id":"QQQ_ONE_WAVE_STACK_V5","status":"REAL_QQQ_CHAIN_ONE_WAVE_STACK","contract":{
      "stack_modes":STACKS,"one_wave":"20Δ Short Call -> 30Δ; 10Δ Short Put -> 5Δ",
      "trigger":"previous close >= anchor close + 1 ATR20; migrate T+1",
      "long_put":"retained","second_wave":False,"optimization":False,"black_scholes":False,"interpolation":False},
      "data":{"options_sha256":sha256_file(op),"underlying_sha256":sha256_file(up)},
      "results":results,"rejections":{"static":sr,"adaptive":ar}}
    (out/"qqq_one_wave_stack_v5_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":main()
