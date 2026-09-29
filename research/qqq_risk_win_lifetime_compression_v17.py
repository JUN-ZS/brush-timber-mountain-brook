#!/usr/bin/env python3
"""QQQ Risk-Win Lifetime Compression V17.

Research question:
Can one realized Risk WIN purchase a long future sequence of opportunities?

Reference path is the V16 strict real-chain path:
- first valid signal N=10 seed
- afterward N>2 only if incremental defined-loss risk R(N)-R(2) <= Bank
- total risk <= base 2% gate + Bank
- Bank=max(0, Bank + realized P&L)

Additional post-hoc isolation:
- each positive realized V16 P&L is independently used as the only Bank seed
- all later positive P&Ls are ignored
- later negative P&Ls alone consume the isolated Bank
- future N is selected from the real QQQ chain using only current isolated Bank
- metrics measure calendar lifetime, future signals covered, offspring count,
  maximum N and cumulative incremental risk capacity reused

This isolation is explicitly counterfactual/post-hoc and never chooses the
historical winners for the reference strategy.
"""

from __future__ import annotations
import argparse,json
from pathlib import Path
import duckdb,numpy as np,pandas as pd

from qqq_profit_recycle_loop_v6 import (
    ensure_data,load_underlying,chain,pick,quotes,q_at,ex,sha256_file
)

BASE_N=2
SEED_N=10
MAX_OFFSPRING_N=9
CAPITAL=100000.0
RISK_PCT=2.0
CAPITAL_USD=64102.5641025641


def max_loss_proxy(legs,n,spot,qa,qs,qw):
    atm_k=float(legs["atm"]["k"])
    short_k=float(legs["short"]["k"])
    wing_k=float(legs["wing"]["k"])
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
    c=g[g.type=="CALL"]
    atm=pick(c,0.50)
    if atm is None:return None
    sc=pick(c,0.20,gt=atm.strike)
    if sc is None:return None
    wing=pick(c,0.08,gt=sc.strike)
    if wing is None:return None
    return {"expiry":pd.Timestamp(exd),
            "atm":{"id":str(atm.contract_id),"k":float(atm.strike)},
            "short":{"id":str(sc.contract_id),"k":float(sc.strike)},
            "wing":{"id":str(wing.contract_id),"k":float(wing.strike)}}


def build_entry_pack(con,op,u,row):
    dt=pd.Timestamp(row.date)
    legs=select_legs(con,op,dt)
    if legs is None:return {"bad":"NO_ENTRY_LEGS"}
    ids=[legs["atm"]["id"],legs["short"]["id"],legs["wing"]["id"]]
    end=min(dt+pd.Timedelta(days=30),pd.Timestamp(legs["expiry"]))
    d=u[(u.date>=dt)&(u.date<=end)].copy().reset_index(drop=True)
    if d.empty:return {"bad":"NO_WINDOW"}
    q=quotes(con,op,ids,dt,end)
    qa=q_at(q,dt,ids[0])
    qs=q_at(q,dt,ids[1])
    qw=q_at(q,dt,ids[2])
    if any(v is None for v in (qa,qs,qw)):return {"bad":"NO_ENTRY_QUOTES"}
    r2=max_loss_proxy(legs,BASE_N,float(row.close),qa,qs,qw)
    risks={n:max_loss_proxy(legs,n,float(row.close),qa,qs,qw)
           for n in range(BASE_N,SEED_N+1)}
    return {"legs":legs,"ids":ids,"d":d,"q":q,"qa":qa,"qs":qs,"qw":qw,
            "r2":r2,"risks":risks}


def trade_pnl(pack,n):
    ids=pack["ids"]
    d=pack["d"]
    qa,qs,qw=pack["qa"],pack["qs"],pack["qw"]
    entry_cf=(ex(qa,"BUY")-n*ex(qs,"SELL")+n*ex(qw,"BUY"))*100.0
    cash=-entry_cf
    exit_dt=pd.Timestamp(d.iloc[-1].date)
    vals=[ex(q_at(pack["q"],exit_dt,ids[0]),"SELL"),
          ex(q_at(pack["q"],exit_dt,ids[1]),"BUY"),
          ex(q_at(pack["q"],exit_dt,ids[2]),"SELL")]
    if any(pd.isna(v) for v in vals):
        return None
    exit_cf=(vals[0]-n*vals[1]+n*vals[2])*100.0
    return float(cash+exit_cf)


def simulate_v16_path(con,op,u,signals,cache):
    bank=0.0
    parent_n=None
    next_allowed=None
    trades=[]
    for _,row in signals.iterrows():
        dt=pd.Timestamp(row.date)
        if next_allowed is not None and dt<=next_allowed:
            continue
        key=str(dt.date())
        if key not in cache:
            cache[key]=build_entry_pack(con,op,u,row)
        pack=cache[key]
        if "bad" in pack:
            continue
        base_gate=CAPITAL_USD*(RISK_PCT/100)
        r2=pack["r2"]
        risks=pack["risks"]
        if not trades:
            target=SEED_N
            reason="SEED_N10"
            risk_budget=0.0
        else:
            affordable=[]
            if bank>0:
                affordable=[n for n in range(BASE_N+1,MAX_OFFSPRING_N+1)
                            if max(0.0,risks[n]-r2)<=bank
                            and risks[n]<=base_gate+bank]
            if affordable:
                target=max(affordable)
                reason="BANK_BRED_SMALLER_N"
                risk_budget=bank
            elif risks[BASE_N]<=base_gate:
                target=BASE_N
                reason="BASE_N_BANK_INSUFFICIENT"
                risk_budget=bank
            else:
                continue
        pnl=trade_pnl(pack,target)
        if pnl is None:
            continue
        tr={"entry":dt,"exit":pd.Timestamp(pack["d"]["date"].iloc[-1]),
            "n":target,"pnl_usd":pnl,"reason":reason,
            "bank_before_usd":float(bank),
            "bank_after_usd":float(max(0.0,bank+pnl)),
            "risk_proxy_usd":float(risks[target]),
            "incremental_risk_vs_n2_usd":float(max(0.0,risks[target]-r2)),
            "parent_n":parent_n,"risk_budget_usd":float(risk_budget)}
        trades.append(tr)
        bank=max(0.0,bank+pnl)
        parent_n=target
        next_allowed=tr["exit"]+pd.Timedelta(days=10)
    return trades,bank


def isolated_win_replay(seed_index,reference,cache):
    seed=reference[seed_index]
    bank=max(0.0,float(seed["pnl_usd"]))
    seed_entry=pd.Timestamp(seed["entry"])
    base_gate=CAPITAL_USD*(RISK_PCT/100)
    future_signals=0
    offspring_count=0
    max_n=BASE_N
    cumulative_incremental_risk=0.0
    first_offspring=None
    last_entry=None
    depletion=None

    for k in range(seed_index+1,len(reference)):
        row=reference[k]
        pack=cache[str(pd.Timestamp(row["entry"]).date())]
        if "bad" in pack:
            continue
        r2=pack["r2"]
        risks=pack["risks"]

        target=BASE_N
        if bank>0:
            affordable=[n for n in range(BASE_N+1,MAX_OFFSPRING_N+1)
                        if max(0.0,risks[n]-r2)<=bank
                        and risks[n]<=base_gate+bank]
            if affordable:
                target=max(affordable)

        pnl=trade_pnl(pack,target)
        if pnl is None:
            continue

        future_signals+=1
        last_entry=pd.Timestamp(row["entry"])
        max_n=max(max_n,target)

        if target>BASE_N:
            offspring_count+=1
            cumulative_incremental_risk += max(0.0,risks[target]-r2)
            if first_offspring is None:
                first_offspring=pd.Timestamp(row["entry"])

        # Critical isolation rule:
        # future wins do not replenish this seed. Only future losses consume it.
        if pnl<0:
            bank=max(0.0,bank+pnl)

        if bank<=0:
            depletion=pd.Timestamp(row["exit"])
            break

    end=depletion if depletion is not None else pd.Timestamp(reference[-1]["exit"])
    lifetime_days=int((end-seed_entry).days)

    return {
        "seed_entry":str(seed_entry.date()),
        "seed_n":int(seed["n"]),
        "seed_pnl_usd":float(seed["pnl_usd"]),
        "future_signals_covered":int(future_signals),
        "offspring_count":int(offspring_count),
        "max_n":int(max_n),
        "cumulative_incremental_risk_usd":float(cumulative_incremental_risk),
        "opportunity_reuse_ratio":float(cumulative_incremental_risk/seed["pnl_usd"]),
        "first_future_offspring_entry":str(first_offspring.date()) if first_offspring is not None else "",
        "last_covered_entry":str(last_entry.date()) if last_entry is not None else "",
        "lifetime_days":lifetime_days,
        "depletion_date":str(depletion.date()) if depletion is not None else "",
        "survives_history":bool(depletion is None)
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",default="data")
    ap.add_argument("--out",default="artifacts")
    a=ap.parse_args()
    out=Path(a.out)
    out.mkdir(parents=True,exist_ok=True)

    op,up=ensure_data(Path(a.data_dir))
    u=load_underlying(up).copy().reset_index(drop=True)
    signals=u[u.signal==True].copy().reset_index(drop=True)
    con=duckdb.connect()

    cache={}
    dyn,final_bank=simulate_v16_path(con,op,u,signals,cache)

    isolated=[]
    for i,tr in enumerate(dyn):
        if tr["pnl_usd"]>0:
            isolated.append(isolated_win_replay(i,dyn,cache))
    idf=pd.DataFrame(isolated)

    pd.DataFrame(dyn).to_csv(out/"v16_reference_ledger.csv",index=False)
    idf.to_csv(out/"isolated_risk_win_lifetime.csv",index=False)

    if not idf.empty:
        agg={
            "positive_seed_count":int(len(idf)),
            "mean_lifetime_days":float(idf.lifetime_days.mean()),
            "median_lifetime_days":float(idf.lifetime_days.median()),
            "max_lifetime_days":int(idf.lifetime_days.max()),
            "history_survivors":int(idf.survives_history.sum()),
            "mean_future_signals":float(idf.future_signals_covered.mean()),
            "median_future_signals":float(idf.future_signals_covered.median()),
            "max_future_signals":int(idf.future_signals_covered.max()),
            "mean_offspring_count":float(idf.offspring_count.mean()),
            "median_offspring_count":float(idf.offspring_count.median()),
            "max_offspring_count":int(idf.offspring_count.max()),
            "mean_reuse_ratio":float(idf.opportunity_reuse_ratio.mean()),
            "median_reuse_ratio":float(idf.opportunity_reuse_ratio.median()),
            "max_reuse_ratio":float(idf.opportunity_reuse_ratio.max()),
            "total_seed_pnl_usd":float(idf.seed_pnl_usd.sum())
        }
    else:
        agg={"positive_seed_count":0}

    report={
        "research_id":"QQQ_RISK_WIN_LIFETIME_COMPRESSION_V17",
        "status":"REAL_QQQ_CHAIN_PLUS_POSTHOC_SINGLE_WIN_ISOLATION",
        "contract":{
            "reference":"V16_strict_bank_only",
            "single_win_seed":"one observed positive V16 realized P&L",
            "future_positive_pnl":"ignored",
            "future_negative_pnl":"consumes isolated Bank",
            "offspring":"N>2 only if incremental R(N)-R(2) <= isolated Bank and total R(N) <= base gate + isolated Bank",
            "time_compression_metric":"cumulative incremental risk capacity / one seed WIN",
            "posthoc_counterfactual":True,
            "optimization":False,
            "black_scholes":False,
            "interpolation":False
        },
        "data":{
            "options_sha256":sha256_file(op),
            "underlying_sha256":sha256_file(up),
            "signal_rows":int(len(signals)),
            "reference_trades":int(len(dyn))
        },
        "results":{
            "reference_final_bank_usd":float(final_bank),
            "isolated_aggregate":agg,
            "top_by_lifetime":idf.sort_values(["lifetime_days","seed_pnl_usd"],ascending=[False,False]).head(10).to_dict(orient="records") if not idf.empty else [],
            "top_by_reuse_ratio":idf.sort_values(["opportunity_reuse_ratio","seed_pnl_usd"],ascending=[False,False]).head(10).to_dict(orient="records") if not idf.empty else []
        }
    }

    (out/"qqq_risk_win_lifetime_compression_v17_result.json").write_text(
        json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":
    main()
