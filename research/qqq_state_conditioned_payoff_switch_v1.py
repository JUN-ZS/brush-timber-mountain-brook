#!/usr/bin/env python3
"""QQQ State-Conditioned Payoff Switch V1.

Hypothesis only (new, not previously frozen):
  HEAT regime:
    +1 ATM Call -2 OTM Call +2 farther OTM Call wings.
    Signal = close/52w_high >= .98 AND close/200DMA - 1 >= .08.

  POST-CRASH regime:
    +1 ATM Call -1 OTM Put +1 farther OTM Put wing.
    Signal = close/200DMA - 1 <= -.05 AND close/52w_high <= .90.
    This is the earlier-library "break 200d by 5% and near 52w low" signal.

  Neutral regime:
    no trade.

Purpose: isolate whether changing payoff to match market state adds edge,
without dynamic-N complexity. Both use real QQQ historical chain bid/ask/delta.
No optimization.
"""

import argparse, hashlib, json, math
from pathlib import Path
import duckdb, numpy as np, pandas as pd

from qqq_ratio_call_harvest_v1 import (
    RELEASE_REPO, RELEASE_TAG, CAPITAL_USD, PCT_52W, DMA_EXT,
    COOLDOWN_DAYS, DTE_MIN, DTE_MAX, HOLD_MAX, RISK_PCT, APPROACH_FRAC,
    START_DATE, END_DATE, sha256_file, ensure_data, duck, load_underlying,
    q_at, executable, midpoint, max_loss_proxy, run_mode,
)

HEAT_N = 2
CRASH_N = 1
HEAT_RATIO = .98
HEAT_EXT = .08
CRASH_RATIO = .90
CRASH_EXT = -.05


def load_option_rows(con,opt_path,dates):
    if not dates:return pd.DataFrame()
    rows=duck(con,"""
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(expiration AS DATE) AS expiration,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               CAST(mark AS DOUBLE) AS mark,
               CAST(delta AS DOUBLE) AS delta,
               CAST(volume AS DOUBLE) AS volume,
               upper(type) AS type
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND CAST(expiration AS DATE) BETWEEN
              CAST(date AS DATE)+INTERVAL 18 DAY AND CAST(date AS DATE)+INTERVAL 35 DAY
          AND bid IS NOT NULL AND ask IS NOT NULL AND delta IS NOT NULL
    """,[str(opt_path),[pd.Timestamp(d).date() for d in dates]])
    return rows


def choose_expiry(g):
    x=g.sort_values(["dte","volume"],ascending=[True,False]).iloc[0]
    return x.expiration


def select_call(g, target_delta, atm_strike=None, above=None):
    x=g[g.type=="CALL"].copy()
    if atm_strike is not None:
        x=x[x.strike>atm_strike]
    elif above is not None:
        x=x[x.strike>above]
    if x.empty:return None
    x["e"]=(x.delta-target_delta).abs()
    return x.sort_values(["e","strike"]).iloc[0]


def select_put(g,target_delta,below=None,below_strike=None):
    x=g[g.type=="PUT"].copy()
    if below_strike is not None:x=x[x.strike<below_strike]
    elif below is not None:x=x[x.strike<below]
    if x.empty:return None
    x["e"]=(x.delta-target_delta).abs()
    return x.sort_values(["e","strike"],ascending=[True,False]).iloc[0]


def select_heat(rows,dt,spot):
    g=rows[rows.date==dt].copy()
    if g.empty:return None
    g["dte"]=(pd.to_datetime(g.expiration)-dt).dt.days
    exp=choose_expiry(g)
    g=g[g.expiration==exp]
    calls=g[g.type=="CALL"]
    if calls.empty:return None
    atm=calls.loc[(calls.delta-.50).abs().idxmin()]
    sh=select_call(calls,.20,atm_strike=float(atm.strike))
    if sh is None:return None
    wi=select_call(calls,.08,above=float(sh.strike))
    if wi is None:return None
    return {
        "regime":"HEAT","expiry":pd.Timestamp(exp),
        "atm":atm.to_dict(),"short":sh.to_dict(),"wing":wi.to_dict(),
        "n":HEAT_N,"shape":"CALL_RATIO"
    }


def select_crash(rows,dt,spot):
    g=rows[rows.date==dt].copy()
    if g.empty:return None
    g["dte"]=(pd.to_datetime(g.expiration)-dt).dt.days
    exp=choose_expiry(g)
    g=g[g.expiration==exp]
    calls=g[g.type=="CALL"]
    puts=g[g.type=="PUT"]
    if calls.empty or puts.empty:return None
    atm=calls.loc[(calls.delta-.50).abs().idxmin()]
    sp=select_put(puts,-.20,below_strike=spot)
    if sp is None:return None
    pw=select_put(puts,-.08,below_strike=float(sp.strike))
    if pw is None:return None
    return {
        "regime":"POST_CRASH","expiry":pd.Timestamp(exp),
        "atm":atm.to_dict(),"short":sp.to_dict(),"wing":pw.to_dict(),
        "n":CRASH_N,"shape":"CALL_SHORT_PUT"
    }


def contract_max_loss(legs):
    n=legs["n"]
    atm=float(legs["atm"]["strike"])
    st=float(legs["short"]["strike"])
    wi=float(legs["wing"]["strike"])
    et=float(legs["entry_cf"])
    grid=np.linspace(max(1.,legs["spot"]*.20),max(legs["spot"]*2.5,wi*1.25),800)
    if legs["shape"]=="CALL_RATIO":
        payoff=np.maximum(grid-atm,0)-n*np.maximum(grid-st,0)+n*np.maximum(grid-wi,0)
    else:
        payoff=np.maximum(grid-atm,0)-n*np.maximum(st-grid,0)+n*np.maximum(wi-grid,0)
    return max(0.,-float(np.min(et + payoff*100.0)))


def side_cashflow(legs):
    n=legs["n"]
    atm=legs["atm"];sh=legs["short"];wi=legs["wing"]
    if legs["shape"]=="CALL_RATIO":
        entry=(float(atm["ask"])-n*float(sh["bid"])+n*float(wi["ask"]))*100.
    else:
        # buy ATM call, SELL put at bid, BUY lower put at ask
        entry=(float(atm["ask"])-n*float(sh["bid"])+n*float(wi["ask"]))*100.
    return entry


def terminal_cf(legs,quotes,dt,final=True):
    n=legs["n"]; a=legs["atm"]; s=legs["short"]; w=legs["wing"]
    qa=q_at(quotes,dt,str(a["contract_id"])); qs=q_at(quotes,dt,str(s["contract_id"])); qw=q_at(quotes,dt,str(w["contract_id"]))
    sa=executable(qa,"SELL"); bs=executable(qs,"BUY"); sw=executable(qw,"SELL")
    if any(pd.isna(x) for x in (sa,bs,sw)):return None
    return (sa-n*bs+n*sw)*100.


def mark_cf(legs,quotes,dt):
    n=legs["n"];a,s,w=legs["atm"],legs["short"],legs["wing"]
    ma=midpoint(q_at(quotes,dt,str(a["contract_id"])))
    ms=midpoint(q_at(quotes,dt,str(s["contract_id"])))
    mw=midpoint(q_at(quotes,dt,str(w["contract_id"])))
    if any(pd.isna(x) for x in (ma,ms,mw)):return np.nan
    return (ma-n*ms+n*mw)*100.


def process_trade(und,quotes,legs,row):
    entry=pd.Timestamp(row.date); expiry=pd.Timestamp(legs["expiry"])
    end=min(entry+pd.Timedelta(days=HOLD_MAX),expiry)
    n=legs["n"]
    ids=[str(legs[x]["contract_id"]) for x in ("atm","short","wing")]
    q0=[q_at(quotes,entry,c) for c in ids]
    if any(x is None for x in q0):return None,"NO_ENTRY_QUOTES"
    ec=side_cashflow(legs)
    # risk gate uses actual executable entry cost + terminal payoff grid
    legs2=dict(legs);legs2["entry_cf"]=ec;legs2["spot"]=float(row.close)
    budget=CAPITAL_USD*(RISK_PCT/100.)
    ml=contract_max_loss(legs2)
    if ml>budget:return None,"RISK_GATE"
    cash=-ec
    daily=und[(und.date>=entry)&(und.date<=end)].copy().reset_index(drop=True)
    eq=[]
    for _,dr in daily.iterrows():
        dt=pd.Timestamp(dr.date)
        mc=mark_cf(legs,quotes,dt)
        if pd.notna(mc):eq.append((dt,CAPITAL_USD+cash+mc))
    exit_date=end
    cf=terminal_cf(legs,quotes,exit_date)
    if cf is None:
        av=sorted(d for (d,cid) in quotes.index if d>=exit_date and all(c in {cid for (d2,cid) in quotes.index if d2==d} for c in ids))
        found=None
        for d in av:
            if terminal_cf(legs,quotes,pd.Timestamp(d)) is not None:found=pd.Timestamp(d);break
        if found is None:return None,"NO_EXIT_QUOTES"
        exit_date=found;cf=terminal_cf(legs,quotes,exit_date)
    pnl=cash+cf
    eq.append((exit_date,CAPITAL_USD+pnl))
    return {
        "entry":entry,"exit":exit_date,"regime":legs["regime"],"shape":legs["shape"],
        "n":n,"atm_strike":float(legs["atm"]["strike"]),
        "short_strike":float(legs["short"]["strike"]),
        "wing_strike":float(legs["wing"]["strike"]),
        "entry_cashflow_usd":ec,"pnl_usd":pnl,"max_loss_usd":ml,
        "eq_rows":eq
    },"OK"


def run_switch(und,rows,selection,quotes):
    state_rows=und[(und.dma200.notna())].copy()
    trades=[];rejects={};next_allowed=None
    for _,r in state_rows.iterrows():
        dt=pd.Timestamp(r.date)
        if next_allowed is not None and dt<=next_allowed:continue
        regime=None
        if float(r.close/r.high52w)>=HEAT_RATIO and float(r.close/r.dma200-1)>=HEAT_EXT:
            regime="HEAT"
        elif float(r.close/r.dma200-1)<=CRASH_EXT and float(r.close/r.high52w)<=CRASH_RATIO:
            regime="POST_CRASH"
        else:
            continue
        legs=selection.get((dt,regime))
        if legs is None:rejects["NO_LEGS"]=rejects.get("NO_LEGS",0)+1;continue
        tr,status=process_trade(und,quotes,legs,r)
        if tr is None:rejects[status]=rejects.get(status,0)+1;continue
        trades.append(tr);next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)
    if not trades:return {"mode":"STATE_SWITCH_V1","trades":0,"rejections":rejects},trades,pd.DataFrame()
    trdf=pd.DataFrame([{k:v for k,v in t.items() if k!="eq_rows"} for t in trades]).sort_values("entry").reset_index(drop=True)
    pts=[p for t in trades for p in t["eq_rows"]]
    eqdf=pd.DataFrame(pts,columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"]=eqdf.equity.cummax();eqdf["dd"]=eqdf.equity/eqdf.peak-1
    end_eq=CAPITAL_USD+trdf.pnl_usd.sum()
    years=max((trdf.exit.iloc[-1]-trdf.entry.iloc[0]).days/365.25,1/365.25)
    total=end_eq/CAPITAL_USD-1
    cagr=(1+total)**(1/years)-1 if 1+total>0 else -1
    stats={
        "mode":"STATE_SWITCH_V1","trades":len(trdf),
        "heat_trades":int((trdf.regime=="HEAT").sum()),
        "post_crash_trades":int((trdf.regime=="POST_CRASH").sum()),
        "win_rate":float((trdf.pnl_usd>0).mean()),
        "avg_trade_usd":float(trdf.pnl_usd.mean()),
        "worst_trade_usd":float(trdf.pnl_usd.min()),
        "best_trade_usd":float(trdf.pnl_usd.max()),
        "total_return":float(total),"cagr":float(cagr),
        "maxdd_daily_mtm":float(eqdf.dd.min()),
        "maxdd_realized":float((trdf.pnl_usd.cumsum().add(CAPITAL_USD).div(trdf.pnl_usd.cumsum().add(CAPITAL_USD).cummax())-1).min()),
        "years":years,"rejections":rejects,
        "data_start":str(trdf.entry.min().date()),"data_end":str(trdf.exit.max().date())
    }
    return stats,trades,eqdf


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts");args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    opt_path,und_path=ensure_data(Path(args.data_dir));und=load_underlying(und_path)
    dates=[pd.Timestamp(x) for x in und.loc[und.dma200.notna(),"date"].tolist()]
    con=duckdb.connect()
    raw=load_option_rows(con,opt_path,dates)
    if raw.empty:raise SystemExit("NO OPTION ROWS")
    raw["date"]=pd.to_datetime(raw.date);raw["expiration"]=pd.to_datetime(raw.expiration)
    selection={}
    for _,r in und[und.dma200.notna()].iterrows():
        dt=pd.Timestamp(r.date);spot=float(r.close)
        if float(r.close/r.high52w)>=HEAT_RATIO and float(r.close/r.dma200-1)>=HEAT_EXT:
            x=select_heat(raw,dt,spot)
            if x:selection[(dt,"HEAT")]=x
        if float(r.close/r.dma200-1)<=CRASH_EXT and float(r.close/r.high52w)<=CRASH_RATIO:
            x=select_crash(raw,dt,spot)
            if x:selection[(dt,"POST_CRASH")]=x
    ids=set()
    for x in selection.values():
        for k in ("atm","short","wing"):ids.add(str(x[k]["contract_id"]))
    q=duck(con,"""
        SELECT CAST(date AS DATE) AS date,CAST(contract_id AS VARCHAR) AS contract_id,
               bid,ask,mark,delta
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """,[str(opt_path),sorted(ids),START_DATE.date(),END_DATE.date()])
    q["date"]=pd.to_datetime(q.date);q["contract_id"]=q.contract_id.astype(str)
    quotes=q.drop_duplicates(["date","contract_id"],keep="last").set_index(["date","contract_id"]).sort_index()

    stats,trades,eqdf=run_switch(und,raw,selection,quotes)
    pd.DataFrame([{**{k:v for k,v in t.items() if k!="eq_rows"},
                    "events_json":"[]"} for t in trades]).to_csv(out/"trades_STATE_SWITCH_V1.csv",index=False)
    if not eqdf.empty:eqdf.to_csv(out/"equity_STATE_SWITCH_V1.csv",index=False)
    report={
        "research_contract":{
            "strategy":"State-conditioned payoff switch",
            "heat":"1 ATM Call -2 20Δ OTM Calls +2 8Δ farther calls",
            "heat_signal":"close/52w_high >=0.98 AND close/200DMA -1 >=0.08",
            "post_crash":"1 ATM Call -1 20Δ OTM Put +1 8Δ farther OTM Put",
            "post_crash_signal":"close/200DMA -1 <=-0.05 AND close/52w_high <=0.90",
            "neutral":"no trade",
            "DTE":[DTE_MIN,DTE_MAX],"hold_max_days":HOLD_MAX,
            "risk_budget":f"{RISK_PCT}% NAV",
            "execution":"buy Ask / sell Bid; daily mark Mid; no interpolation",
            "no_optimization":True,
        },
        "data":{"source_repo":RELEASE_REPO,"release_tag":RELEASE_TAG,
                "options_sha256":sha256_file(opt_path),
                "underlying_sha256":sha256_file(und_path),
                "underlying_range":[str(und.date.min().date()),str(und.date.max().date())],
                "selection_count":len(selection)},
        "results":[stats]
    }
    (out/"state_switch_v1_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__":main()
