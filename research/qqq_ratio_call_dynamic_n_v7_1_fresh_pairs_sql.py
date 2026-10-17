#!/usr/bin/env python3
"""QQQ Ratio-Call Dynamic-N V7.1 — fresh-pair, SQL-native reconstruction.

Same strategy rules as V7.  Only the data path is optimized:
fresh-pair selection is performed inside DuckDB with window functions so the
runner does not materialize millions of option rows into pandas.

ENTRY:
  +1 ATM call - 2 short OTM calls + 2 farther OTM long wings.
  Initial N=2 must satisfy 2% NAV terminal max-loss proxy.

DYNAMIC N:
  - A fresh pair may be added only after 2 consecutive sessions with the
    currently active lead short at delta <=0.10, >=5 sessions after the last
    N change, and only if current-position terminal max-loss remains <=2% NAV.
  - The added pair is a NEW current-date short ~=20Δ and wing ~=8Δ on the
    original entry expiry.
  - Reduce one highest-delta short+wing pair when any active short reaches
    delta >=0.35. One pair per trading session.
  - N cap = 4.

PATH:
  - Approach if High >=98% of closest active short strike.
  - T+1 reversal: if Close<T approach Close and lead short buyback <=50% of
    its entry premium, buy back that one lead SHORT only; keep wing.
  - T+1 continuation: if Close>=approach Close, close one highest-delta
    SHORT+WING pair; if one short remains, remove the last SHORT only.

DOWNSIDE DD:
  - If package loss >=25% of initial risk, buy back profitable SHORTs only;
    never sell wings.

Historical bid/ask/mark/delta only. No interpolation. No synthetic pricing.
No parameter optimization.
"""

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_harvest_v1 import (
    RELEASE_REPO, RELEASE_TAG, CAPITAL_USD,
    PCT_52W, DMA_EXT, COOLDOWN_DAYS, SHORT_DELTA, WING_DELTA,
    DTE_MIN, DTE_MAX, HOLD_MAX, RISK_PCT, APPROACH_FRAC,
    START_DATE, END_DATE,
    sha256_file, ensure_data, duck, load_underlying,
    build_selection_cache, fetch_all_quotes, q_at, executable, midpoint,
    max_loss_proxy, run_mode,
)

N_START = 2
N_CAP = 4
ADD_DELTA = 0.10
ADD_STREAK = 2
N_CHANGE_COOLDOWN = 5
REDUCE_DELTA = 0.35
DD_START = 0.25
HARVEST_FRACTION = 0.50


@dataclass
class OpenPair:
    short_id: str
    wing_id: str
    short_k: float
    wing_k: float
    entry_short_bid: float
    entry_wing_ask: float
    opened_date: pd.Timestamp
    origin: str
    active_short: bool = True
    active_wing: bool = True


def fetch_quotes_delta_all(con, opt_path, selection):
    ids = sorted({
        str(legs[key]["contract_id"])
        for legs in selection.values()
        for key in ("atm", "short", "wing")
    })
    if not ids:
        return pd.DataFrame()
    rows = duck(con, """
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS contract_id,
               bid, ask, mark, delta
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """, [str(opt_path), ids, START_DATE.date(), END_DATE.date()])
    rows["date"] = pd.to_datetime(rows["date"])
    rows["contract_id"] = rows["contract_id"].astype(str)
    return rows.drop_duplicates(["date","contract_id"], keep="last").set_index(
        ["date","contract_id"]
    ).sort_index()


def build_fresh_pair_selection_sql(con, opt_path, selection, und):
    # One compact key row for every potential trade day/window.
    keys=[]
    und_idx=und.set_index("date")
    for dt,legs in selection.items():
        exp=pd.Timestamp(legs["expiry"])
        end=min(dt+pd.Timedelta(days=HOLD_MAX),exp)
        window=und.loc[(und["date"]>=dt)&(und["date"]<=end),["date","close"]]
        for _,r in window.iterrows():
            keys.append({
                "date":pd.Timestamp(r["date"]),
                "expiration":exp,
                "spot":float(r["close"]),
                "atm_k":float(legs["atm"]["strike"]),
            })
    if not keys:
        return {}
    kdf=pd.DataFrame(keys).drop_duplicates(["date","expiration"])
    kdf["date"]=pd.to_datetime(kdf["date"]).dt.date
    kdf["expiration"]=pd.to_datetime(kdf["expiration"]).dt.date
    con.register("fresh_keys",kdf)

    # Return exactly one candidate short and one wing per (date,expiry,spot).
    # This avoids materializing the full chain in Python.
    sql="""
    WITH c AS (
      SELECT
        CAST(o.date AS DATE) AS date,
        CAST(o.expiration AS DATE) AS expiration,
        CAST(o.contract_id AS VARCHAR) AS contract_id,
        CAST(o.strike AS DOUBLE) AS strike,
        CAST(o.bid AS DOUBLE) AS bid,
        CAST(o.ask AS DOUBLE) AS ask,
        CAST(o.mark AS DOUBLE) AS mark,
        CAST(o.delta AS DOUBLE) AS delta,
        CAST(o.volume AS DOUBLE) AS volume,
        k.spot,
        k.atm_k
      FROM read_parquet(?) o
      INNER JOIN fresh_keys k
        ON CAST(o.date AS DATE)=k.date
       AND CAST(o.expiration AS DATE)=k.expiration
      WHERE upper(o.type)='CALL'
        AND o.delta IS NOT NULL
        AND o.bid IS NOT NULL
        AND o.ask IS NOT NULL
        AND o.strike > greatest(k.spot,k.atm_k)
    ),
    short_ranked AS (
      SELECT *,
             ROW_NUMBER() OVER(
               PARTITION BY date,expiration
               ORDER BY abs(delta-0.20), strike
             ) AS rn_short
      FROM c
    ),
    s AS (
      SELECT
        date,expiration,spot,atm_k,
        contract_id AS short_id,
        strike AS short_k,
        bid AS short_bid,
        ask AS short_ask,
        mark AS short_mark,
        delta AS short_delta
      FROM short_ranked
      WHERE rn_short=1
    ),
    wing_ranked AS (
      SELECT
        s.*,
        c.contract_id AS wing_id,
        c.strike AS wing_k,
        c.bid AS wing_bid,
        c.ask AS wing_ask,
        c.mark AS wing_mark,
        c.delta AS wing_delta,
        ROW_NUMBER() OVER(
          PARTITION BY s.date,s.expiration
          ORDER BY abs(c.delta-0.08), c.strike
        ) AS rn_wing
      FROM s
      INNER JOIN c
        ON c.date=s.date
       AND c.expiration=s.expiration
       AND c.strike>s.short_k
    )
    SELECT
      date,expiration,spot,atm_k,
      short_id,short_k,short_bid,short_ask,short_mark,short_delta,
      wing_id,wing_k,wing_bid,wing_ask,wing_mark,wing_delta
    FROM wing_ranked
    WHERE rn_wing=1
    """
    rows=duck(con,sql,[str(opt_path)])
    try: con.unregister("fresh_keys")
    except Exception: pass

    out={}
    if rows.empty: return out
    rows["date"]=pd.to_datetime(rows["date"])
    rows["expiration"]=pd.to_datetime(rows["expiration"])
    for _,r in rows.iterrows():
        out[(pd.Timestamp(r["date"]),pd.Timestamp(r["expiration"]))]={
            "short":{
                "contract_id":str(r["short_id"]),
                "strike":float(r["short_k"]),
                "bid":float(r["short_bid"]),
                "ask":float(r["short_ask"]),
                "mark":float(r["short_mark"]),
                "delta":float(r["short_delta"]),
            },
            "wing":{
                "contract_id":str(r["wing_id"]),
                "strike":float(r["wing_k"]),
                "bid":float(r["wing_bid"]),
                "ask":float(r["wing_ask"]),
                "mark":float(r["wing_mark"]),
                "delta":float(r["wing_delta"]),
            }
        }
    return out


def fetch_selected_fresh_quotes(con,opt_path,fresh_selection):
    ids=set()
    for v in fresh_selection.values():
        ids.add(v["short"]["contract_id"]); ids.add(v["wing"]["contract_id"])
    if not ids: return pd.DataFrame()
    rows=duck(con,"""
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS contract_id,
               bid,ask,mark,delta
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """,[str(opt_path),sorted(ids),START_DATE.date(),END_DATE.date()])
    if rows.empty:return pd.DataFrame()
    rows["date"]=pd.to_datetime(rows["date"]);rows["contract_id"]=rows["contract_id"].astype(str)
    return rows.drop_duplicates(["date","contract_id"],keep="last").set_index(["date","contract_id"]).sort_index()


def make_pair(spec,dt,origin):
    return OpenPair(
        short_id=str(spec["short"]["contract_id"]),
        wing_id=str(spec["wing"]["contract_id"]),
        short_k=float(spec["short"]["strike"]),
        wing_k=float(spec["wing"]["strike"]),
        entry_short_bid=float(spec["short"]["bid"]),
        entry_wing_ask=float(spec["wing"]["ask"]),
        opened_date=pd.Timestamp(dt),
        origin=origin,
    )


def terminal_max_loss_generic(cash,atm_k,pairs,spot):
    max_wing=max([p.wing_k for p in pairs],default=spot*1.2)
    grid=np.linspace(max(1.0,spot*.20),max(spot*2.5,max_wing*1.25),700)
    payoff=np.maximum(grid-atm_k,0.0)
    for p in pairs:
        if p.active_short:payoff-=np.maximum(grid-p.short_k,0.0)
        if p.active_wing:payoff+=np.maximum(grid-p.wing_k,0.0)
    return max(0.0,-float(np.min(cash+payoff*100.0)))


def row_delta(quotes,dt,cid):
    try:return float(quotes.loc[(pd.Timestamp(dt),str(cid))]["delta"])
    except:return np.nan


def mark_package(quotes,dt,atm_id,pairs):
    qa=q_at(quotes,dt,atm_id)
    ma=midpoint(qa)
    if pd.isna(ma):return np.nan
    total=ma*100.0
    for p in pairs:
        if p.active_short: total-=midpoint(q_at(quotes,dt,p.short_id))*100.0
        if p.active_wing: total+=midpoint(q_at(quotes,dt,p.wing_id))*100.0
    return total


def close_short(quotes,dt,p,count=1):
    q=q_at(quotes,dt,p.short_id); bp=executable(q,"BUY")
    if pd.isna(bp):return None
    return (-count*bp)*100.0,bp


def close_pair(quotes,dt,p):
    qs,qw=q_at(quotes,dt,p.short_id),q_at(quotes,dt,p.wing_id)
    bp,sw=executable(qs,"BUY"),executable(qw,"SELL")
    if pd.isna(bp) or pd.isna(sw):return None
    return (-bp+sw)*100.0,bp,sw


def process_trade(und,quotes,entry_row,entry_legs,fresh_selection):
    entry=pd.Timestamp(entry_row["date"])
    spot=float(entry_row["close"])
    expiry=pd.Timestamp(entry_legs["expiry"])
    end_date=min(entry+pd.Timedelta(days=HOLD_MAX),expiry)

    base_ml=max_loss_proxy(entry_legs,N_START,spot)
    if base_ml>CAPITAL_USD*(RISK_PCT/100.0):
        return None,"RISK_GATE"

    atm_id=str(entry_legs["atm"]["contract_id"]);atm_k=float(entry_legs["atm"]["strike"])
    qa0=q_at(quotes,entry,atm_id)
    qs0=q_at(quotes,entry,str(entry_legs["short"]["contract_id"]))
    qw0=q_at(quotes,entry,str(entry_legs["wing"]["contract_id"]))
    if any(x is None for x in (qa0,qs0,qw0)):return None,"NO_ENTRY_QUOTES"

    ae,se,we=executable(qa0,"BUY"),executable(qs0,"SELL"),executable(qw0,"BUY")
    if any(pd.isna(x) for x in (ae,se,we)):return None,"NO_ENTRY_QUOTES"

    entry_cf=(ae-N_START*se+N_START*we)*100.0
    cash=-entry_cf
    pairs=[make_pair(entry_legs,entry,"ENTRY") for _ in range(N_START)]

    low_streak=0; last_n_change=-999; pending=None; approach_armed=True
    events=[];eq_rows=[]

    daily=und[(und["date"]>=entry)&(und["date"]<=end_date)].copy().reset_index(drop=True)
    for i,row in daily.iterrows():
        dt=pd.Timestamp(row["date"])

        # Path action from prior approach.
        if pending is not None and pd.Timestamp(pending["date"])==dt:
            pstate=pending;pending=None
            active=[p for p in pairs if p.active_short]
            if active:
                lead=max(active,key=lambda p:(-1 if pd.isna(row_delta(quotes,dt,p.short_id)) else row_delta(quotes,dt,p.short_id)))
                bp=executable(q_at(quotes,dt,lead.short_id),"BUY")
                if pd.notna(bp):
                    if float(row["close"])>=float(pstate["approach_close"]):
                        # Reduce one pair when possible.
                        if len(active)>1 and lead.active_wing:
                            pr=close_pair(quotes,dt,lead)
                            if pr:
                                cf,_,_=pr;cash+=cf
                                lead.active_short=False;lead.active_wing=False
                                last_n_change=i;low_streak=0
                                events.append({"date":str(dt.date()),"event":"BREAKOUT_REDUCE_ONE_FRESH_PAIR"})
                        else:
                            cash+=(-bp)*100.0
                            lead.active_short=False
                            last_n_change=i;low_streak=0
                            events.append({"date":str(dt.date()),"event":"BREAKOUT_REMOVE_LAST_SHORT"})
                    elif bp<=HARVEST_FRACTION*lead.entry_short_bid:
                        cash+=(-bp)*100.0
                        lead.active_short=False
                        last_n_change=i
                        events.append({"date":str(dt.date()),"event":"PROFIT_HARVEST50_LEAD_SHORT_ONLY"})

        # Arm new path check.
        active=[p for p in pairs if p.active_short]
        if active and pending is None and dt>entry:
            closest=min(active,key=lambda p:p.short_k)
            if float(row["high"])>=APPROACH_FRAC*closest.short_k and approach_armed and i+1<len(daily):
                approach_armed=False
                pending={"date":pd.Timestamp(daily.iloc[i+1]["date"]),"approach_date":dt,"approach_close":float(row["close"])}
            elif float(row["high"])<APPROACH_FRAC*closest.short_k:
                approach_armed=True

        # Package MTM.
        mark=mark_package(quotes,dt,atm_id,pairs)
        package_pnl=mark+cash if pd.notna(mark) else np.nan
        active=[p for p in pairs if p.active_short]

        # Downside governor: SHORT only, profitable only.
        if active and pd.notna(package_pnl) and base_ml>0:
            loss_frac=max(0.0,-package_pnl)/base_ml
            if loss_frac>=DD_START:
                target=max(0,int(math.ceil(N_START*(1.0-loss_frac))))
                reduce_n=max(0,len(active)-target)
                candidates=[]
                for p in active:
                    bp=executable(q_at(quotes,dt,p.short_id),"BUY")
                    if pd.notna(bp) and bp<=p.entry_short_bid:candidates.append((bp,p))
                candidates.sort(key=lambda z:z[0])
                for bp,p in candidates[:reduce_n]:
                    cash+=(-bp)*100.0;p.active_short=False;last_n_change=i
                    events.append({"date":str(dt.date()),"event":"DD_PROFIT_RECOVER_FRESH_SHORT_ONLY","short_id":p.short_id,"loss_fraction":loss_frac})

        # Delta governor on highest-delta active short.
        active=[p for p in pairs if p.active_short]
        if active:
            dd=[(row_delta(quotes,dt,p.short_id),p) for p in active]
            dd=[x for x in dd if pd.notna(x[0])]
            if dd:
                d,p=max(dd,key=lambda x:x[0])
                if d>=REDUCE_DELTA and (i-last_n_change)>=1 and len(active)>0:
                    pr=close_pair(quotes,dt,p) if p.active_wing else None
                    if pr:
                        cf,_,_=pr;cash+=cf;p.active_short=False;p.active_wing=False;last_n_change=i;low_streak=0
                        events.append({"date":str(dt.date()),"event":"DELTA_REDUCE_ONE_FRESH_PAIR","short_id":p.short_id,"short_delta":d})

        # Fresh add: require lead short to be low delta on consecutive sessions.
        active=[p for p in pairs if p.active_short]
        if active:
            dd=[row_delta(quotes,dt,p.short_id) for p in active]
            dd=[x for x in dd if pd.notna(x)]
            lead_d=max(dd) if dd else np.nan
            if pd.notna(lead_d) and lead_d<=ADD_DELTA: low_streak+=1
            else: low_streak=0

            structural=sum(1 for p in pairs if p.active_short and p.active_wing)
            if low_streak>=ADD_STREAK and (i-last_n_change)>=N_CHANGE_COOLDOWN and structural<N_CAP:
                spec=fresh_selection.get((dt,expiry))
                if spec:
                    sh=spec["short"];wi=spec["wing"]
                    sell_sh=float(sh["bid"]);buy_wi=float(wi["ask"])
                    new_cash=cash+(sell_sh-buy_wi)*100.0
                    active_struct=[p for p in pairs if p.active_short and p.active_wing]+[make_pair(spec,dt,"FRESH_ADD")]
                    risk=terminal_max_loss_generic(new_cash,atm_k,active_struct,float(row["close"]))
                    budget=CAPITAL_USD*(RISK_PCT/100.0)
                    if risk<=budget:
                        cash=new_cash;pairs.append(make_pair(spec,dt,"FRESH_ADD"));last_n_change=i;low_streak=0
                        events.append({"date":str(dt.date()),"event":"LOW_DELTA_ADD_FRESH_PAIR","short_id":str(sh["contract_id"]),"wing_id":str(wi["contract_id"]),"short_delta":float(sh["delta"]),"wing_delta":float(wi["delta"]),"candidate_risk_usd":risk})

        mark=mark_package(quotes,dt,atm_id,pairs)
        if pd.notna(mark):eq_rows.append((dt,CAPITAL_USD+cash+mark))
        if dt>=end_date:break

    # Exit all active legs at end_date.
    qa=q_at(quotes,end_date,atm_id);sa=executable(qa,"SELL")
    if pd.isna(sa):return None,"NO_EXIT_QUOTES"
    exit_cf=sa*100.0
    for p in pairs:
        if p.active_short:
            bp=executable(q_at(quotes,end_date,p.short_id),"BUY")
            if pd.isna(bp):return None,"NO_EXIT_QUOTES"
            exit_cf-=bp*100.0
        if p.active_wing:
            sw=executable(q_at(quotes,end_date,p.wing_id),"SELL")
            if pd.isna(sw):return None,"NO_EXIT_QUOTES"
            exit_cf+=sw*100.0
    pnl=cash+exit_cf;eq_rows.append((pd.Timestamp(end_date),CAPITAL_USD+pnl))
    return {
        "entry":entry,"exit":pd.Timestamp(end_date),
        "n_initial":N_START,
        "n_pair_final":sum(p.active_wing for p in pairs),
        "n_short_final":sum(p.active_short for p in pairs),
        "pnl_usd":float(pnl),
        "max_loss_proxy_usd":float(base_ml),
        "events":events,"eq_rows":eq_rows,
    },"OK"


def run_dynamic(und,quotes,selection,fresh_selection):
    rows=und[und["signal"] & und["dma200"].notna()].copy()
    trades=[];rejects={};next_allowed=None
    for _,row in rows.iterrows():
        entry=pd.Timestamp(row["date"])
        if next_allowed is not None and entry<=next_allowed:continue
        legs=selection.get(entry)
        if legs is None:
            rejects["NO_LEGS"]=rejects.get("NO_LEGS",0)+1;continue
        tr,status=process_trade(und,quotes,row,legs,fresh_selection)
        if tr is None:
            rejects[status]=rejects.get(status,0)+1;continue
        trades.append(tr);next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)
    if not trades:return {"mode":"DYNAMIC_N_V7_1_FRESH_PAIRS_SQL","trades":0,"rejections":rejects},trades,pd.DataFrame()

    trdf=pd.DataFrame([{k:v for k,v in t.items() if k not in ("events","eq_rows")} for t in trades]).sort_values("entry").reset_index(drop=True)
    pts=[p for t in trades for p in t["eq_rows"]]
    eqdf=pd.DataFrame(pts,columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"]=eqdf["equity"].cummax();eqdf["dd"]=eqdf["equity"]/eqdf["peak"]-1.0
    end_eq=CAPITAL_USD+trdf["pnl_usd"].sum();years=max((trdf["exit"].iloc[-1]-trdf["entry"].iloc[0]).days/365.25,1/365.25)
    total=end_eq/CAPITAL_USD-1.0;cagr=(1+total)**(1/years)-1 if 1+total>0 else -1
    ev=[e for t in trades for e in t["events"]]
    stats={
        "mode":"DYNAMIC_N_V7_1_FRESH_PAIRS_SQL","trades":int(len(trdf)),
        "win_rate":float((trdf["pnl_usd"]>0).mean()),"avg_trade_usd":float(trdf["pnl_usd"].mean()),
        "worst_trade_usd":float(trdf["pnl_usd"].min()),"best_trade_usd":float(trdf["pnl_usd"].max()),
        "total_return":float(total),"cagr":float(cagr),"maxdd_daily_mtm":float(eqdf["dd"].min()),
        "maxdd_realized":float((trdf["pnl_usd"].cumsum().add(CAPITAL_USD).div(trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax())-1).min()),
        "years":float(years),
        "profit_harvest_events":int(sum(e["event"]=="PROFIT_HARVEST50_LEAD_SHORT_ONLY" for e in ev)),
        "continuation_events":int(sum(e["event"] in ("BREAKOUT_CONTINUATION_REDUCE_ONE_FRESH_PAIR","BREAKOUT_REMOVE_LAST_SHORT") for e in ev)),
        "dd_short_recover_events":int(sum(e["event"]=="DD_PROFIT_RECOVER_FRESH_SHORT_ONLY" for e in ev)),
        "fresh_add_events":int(sum(e["event"]=="LOW_DELTA_ADD_FRESH_PAIR" for e in ev)),
        "delta_pair_reduce_events":int(sum(e["event"]=="DELTA_REDUCE_ONE_FRESH_PAIR" for e in ev)),
        "avg_n_pair_final":float(trdf["n_pair_final"].mean()),
        "avg_n_short_final":float(trdf["n_short_final"].mean()),
        "rejections":rejects,"data_start":str(trdf["entry"].min().date()),"data_end":str(trdf["exit"].max().date())
    }
    return stats,trades,eqdf


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts");args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    opt_path,und_path=ensure_data(Path(args.data_dir));und=load_underlying(und_path)
    dates=[pd.Timestamp(x) for x in und.loc[und["signal"],"date"].tolist()]
    con=duckdb.connect()
    selection,selection_rejects=build_selection_cache(con,opt_path,dates)
    print("SELECTION_CACHE",len(selection),"SELECTION_REJECTS",selection_rejects,flush=True)

    fresh_selection=build_fresh_pair_selection_sql(con,opt_path,selection,und)
    print("FRESH_SELECTION_KEYS",len(fresh_selection),flush=True)

    quotes=fetch_quotes_delta_all(con,opt_path,selection)
    more=fetch_selected_fresh_quotes(con,opt_path,fresh_selection)
    if not more.empty:
        if quotes.empty:quotes=more
        else:
            quotes=pd.concat([quotes,more])
            quotes=quotes[~quotes.index.duplicated(keep="last")].sort_index()
    print("QUOTE_ROWS",len(quotes),flush=True)

    quotes_base=fetch_all_quotes(con,opt_path,selection)
    _,b2,_=run_mode(und,quotes_base,selection,2,"BASELINE_TOUCH")
    _,b3,_=run_mode(und,quotes_base,selection,3,"BASELINE_TOUCH")
    _,b4,_=run_mode(und,quotes_base,selection,4,"BASELINE_TOUCH")
    dyn,trades,eqdf=run_dynamic(und,quotes,selection,fresh_selection)

    results=[b2,b3,b4,dyn]
    pd.DataFrame([{
        **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
        "events_json":json.dumps(t["events"],ensure_ascii=False)
    } for t in trades]).to_csv(out/"trades_DYNAMIC_N_V7_1_FRESH_PAIRS_SQL.csv",index=False)
    if not eqdf.empty:eqdf.to_csv(out/"equity_DYNAMIC_N_V7_1_FRESH_PAIRS_SQL.csv",index=False)
    report={
        "research_contract":{
            "strategy":"1 ATM Long Call + dynamic fresh N Short OTM Calls + matching fresh OTM wings",
            "entry":"1x2x2; N0=2",
            "fresh_add":"two consecutive lead-short sessions <=0.10 delta and >=5 sessions since N change; add one NEW current-date ~20delta short + ~8delta wing on original expiry; current terminal max-loss <=2% NAV",
            "pair_reduce":"highest-delta active short >=0.35 -> close one paired short+wing",
            "profit_recovery":"approach High >=98% closest short strike; next Close lower; lead short buyback <=50% entry premium -> close one SHORT only",
            "breakout_continuation":"approach then next Close >= approach Close -> close one highest-delta paired short+wing; if one short remains remove the last short",
            "downside_governor":"package loss >=25% initial risk -> profitable SHORT only; wings stay",
            "DTE":[DTE_MIN,DTE_MAX],"hold_max_days":HOLD_MAX,"risk_budget":"2% NAV","no_optimization":True,
            "entry_execution":"ATM buy Ask; short sell Bid; wing buy Ask",
            "management_execution":"short buyback Ask; wing sale Bid","daily_mark":"Mid","strict_quotes":True,
        },
        "data":{
            "source_repo":RELEASE_REPO,"release_tag":RELEASE_TAG,
            "options_sha256":sha256_file(opt_path),"underlying_sha256":sha256_file(und_path),
            "underlying_range":[str(und["date"].min().date()),str(und["date"].max().date())],
            "selection_cache":len(selection),"fresh_selection_keys":len(fresh_selection),"selection_rejects":selection_rejects,
        },
        "results":results
    }
    (out/"ratio_call_dynamic_n_v7_1_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_dynamic_n_v7_1_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__=="__main__":
    main()
