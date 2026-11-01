#!/usr/bin/env python3
"""QQQ State-Conditioned Payoff Switch V1.1 — SQL-native selection.

Same frozen hypothesis as V1:
  HEAT:
    +1 ATM Call -2 20Δ OTM Calls +2 8Δ farther OTM Calls
    signal close/52w_high >= .98 and close/200DMA-1 >= .08
  POST_CRASH:
    +1 ATM Call -1 20Δ OTM Put +1 8Δ farther OTM Put
    signal close/200DMA-1 <= -.05 and close/52w_high <= .90
  Else no trade.

Only execution/data path changed from V1:
contract selection is performed directly inside DuckDB over the canonical
QQQ option parquet. The Python process receives only selected contracts.
No parameter optimization.
"""

import argparse
import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_harvest_v1 import (
    RELEASE_REPO, RELEASE_TAG, CAPITAL_USD, COOLDOWN_DAYS,
    DTE_MIN, DTE_MAX, HOLD_MAX, RISK_PCT,
    START_DATE, END_DATE,
    sha256_file, ensure_data, load_underlying,
    q_at, executable, midpoint, run_mode, fetch_all_quotes,
)

HEAT_N=2
CRASH_N=1
HEAT_RATIO=.98
HEAT_EXT=.08
CRASH_RATIO=.90
CRASH_EXT=-.05


def duck(con,sql,params=None):
    return con.execute(sql,params or {}).df()


def build_regime_selection(con,opt_path,und):
    u=und[und["dma200"].notna()].copy()
    u["date"]=pd.to_datetime(u["date"])
    u["regime"]=np.where(
        (u["close"]/u["high52w"]>=HEAT_RATIO)&(u["close"]/u["dma200"]-1>=HEAT_EXT),
        "HEAT",
        np.where(
            (u["close"]/u["high52w"]<=CRASH_RATIO)&(u["close"]/u["dma200"]-1<=CRASH_EXT),
            "POST_CRASH",None
        )
    )
    u=u[u["regime"].notna()].copy()
    if u.empty:
        return {}
    keys=u[["date","regime","close"]].copy()
    con.register("regime_keys",keys)

    # Choose the nearest expiry (DTE 18-35; volume descending tie-break)
    # separately per signal date, then choose the actual payoff legs.
    sql="""
    WITH chain AS (
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
        UPPER(o.type) AS type,
        k.regime,
        CAST(k.close AS DOUBLE) AS spot,
        DATEDIFF('day',CAST(o.date AS DATE),CAST(o.expiration AS DATE)) AS dte
      FROM read_parquet(?) o
      INNER JOIN regime_keys k
        ON CAST(o.date AS DATE)=k.date
      WHERE CAST(o.expiration AS DATE)
              BETWEEN CAST(o.date AS DATE)+INTERVAL 18 DAY
                  AND CAST(o.date AS DATE)+INTERVAL 35 DAY
        AND o.bid IS NOT NULL
        AND o.ask IS NOT NULL
        AND o.delta IS NOT NULL
    ),
    expiry_stats AS (
      SELECT date,regime,expiration,dte,
             MAX(volume) AS max_volume
      FROM chain
      GROUP BY date,regime,expiration,dte
    ),
    expiry_rank AS (
      SELECT *,
             ROW_NUMBER() OVER(
               PARTITION BY date,regime
               ORDER BY dte, max_volume DESC NULLS LAST
             ) AS rn_exp
      FROM expiry_stats
    ),
    chosen_expiry AS (
      SELECT date,regime,expiration
      FROM expiry_rank
      WHERE rn_exp=1
    ),
    c AS (
      SELECT ch.*
      FROM chain ch
      INNER JOIN chosen_expiry e
        ON ch.date=e.date AND ch.regime=e.regime AND ch.expiration=e.expiration
    ),
    atm AS (
      SELECT *,
        ROW_NUMBER() OVER(
          PARTITION BY date,regime ORDER BY abs(delta-0.50), strike
        ) AS rn_atm
      FROM c
      WHERE type='CALL'
    ),
    a AS (
      SELECT * FROM atm WHERE rn_atm=1
    ),
    heat_short AS (
      SELECT c.*,
        ROW_NUMBER() OVER(
          PARTITION BY c.date,c.regime ORDER BY abs(c.delta-0.20), c.strike
        ) AS rn_short
      FROM c
      INNER JOIN a ON c.date=a.date AND c.regime=a.regime
      WHERE c.type='CALL' AND c.strike>a.strike
        AND c.regime='HEAT'
    ),
    hs AS (
      SELECT * FROM heat_short WHERE rn_short=1
    ),
    heat_wing AS (
      SELECT c.*,
        ROW_NUMBER() OVER(
          PARTITION BY c.date,c.regime ORDER BY abs(c.delta-0.08), c.strike
        ) AS rn_wing
      FROM c
      INNER JOIN hs ON c.date=hs.date AND c.regime=hs.regime
      WHERE c.type='CALL' AND c.strike>hs.strike
        AND c.regime='HEAT'
    ),
    hw AS (
      SELECT * FROM heat_wing WHERE rn_wing=1
    ),
    crash_short AS (
      SELECT c.*,
        ROW_NUMBER() OVER(
          PARTITION BY c.date,c.regime ORDER BY abs(c.delta+0.20), c.strike DESC
        ) AS rn_short
      FROM c
      INNER JOIN a ON c.date=a.date AND c.regime=a.regime
      WHERE c.type='PUT' AND c.strike<c.spot
        AND c.regime='POST_CRASH'
    ),
    cs AS (
      SELECT * FROM crash_short WHERE rn_short=1
    ),
    crash_wing AS (
      SELECT c.*,
        ROW_NUMBER() OVER(
          PARTITION BY c.date,c.regime ORDER BY abs(c.delta+0.08), c.strike DESC
        ) AS rn_wing
      FROM c
      INNER JOIN cs ON c.date=cs.date AND c.regime=cs.regime
      WHERE c.type='PUT' AND c.strike<cs.strike
        AND c.regime='POST_CRASH'
    ),
    cw AS (
      SELECT * FROM crash_wing WHERE rn_wing=1
    )
    SELECT
      a.date,a.regime,a.expiration AS expiry,a.contract_id AS atm_id,a.strike AS atm_k,
      hs.contract_id AS short_id,hs.strike AS short_k,hs.delta AS short_delta,
      hw.contract_id AS wing_id,hw.strike AS wing_k,hw.delta AS wing_delta
    FROM a
    INNER JOIN hs ON a.date=hs.date AND a.regime=hs.regime
    INNER JOIN hw ON a.date=hw.date AND a.regime=hw.regime
    WHERE a.regime='HEAT'
    UNION ALL
    SELECT
      a.date,a.regime,a.expiration AS expiry,a.contract_id AS atm_id,a.strike AS atm_k,
      cs.contract_id AS short_id,cs.strike AS short_k,cs.delta AS short_delta,
      cw.contract_id AS wing_id,cw.strike AS wing_k,cw.delta AS wing_delta
    FROM a
    INNER JOIN cs ON a.date=cs.date AND a.regime=cs.regime
    INNER JOIN cw ON a.date=cw.date AND a.regime=cw.regime
    WHERE a.regime='POST_CRASH'
    """
    rows=duck(con,sql,[str(opt_path)])
    try: con.unregister("regime_keys")
    except: pass
    out={}
    if rows.empty:return out
    rows["date"]=pd.to_datetime(rows["date"]);rows["expiry"]=pd.to_datetime(rows["expiry"])
    for _,r in rows.iterrows():
        out[(pd.Timestamp(r["date"]),str(r["regime"]))]={
            "regime":str(r["regime"]),
            "expiry":pd.Timestamp(r["expiry"]),
            "atm_id":str(r["atm_id"]),
            "atm_k":float(r["atm_k"]),
            "short_id":str(r["short_id"]),
            "short_k":float(r["short_k"]),
            "wing_id":str(r["wing_id"]),
            "wing_k":float(r["wing_k"]),
            "n":HEAT_N if str(r["regime"])=="HEAT" else CRASH_N,
            "shape":"CALL_RATIO" if str(r["regime"])=="HEAT" else "CALL_SHORT_PUT",
        }
    return out


def fetch_leg_quotes(con,opt_path,selection):
    ids=sorted({x[k] for x in selection.values() for k in ("atm_id","short_id","wing_id")})
    if not ids:return pd.DataFrame()
    rows=duck(con,"""
      SELECT CAST(date AS DATE) AS date,
             CAST(contract_id AS VARCHAR) AS contract_id,
             bid,ask,mark,delta
      FROM read_parquet(?)
      WHERE contract_id IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
    """,[str(opt_path),ids,START_DATE.date(),END_DATE.date()])
    rows["date"]=pd.to_datetime(rows["date"]);rows["contract_id"]=rows["contract_id"].astype(str)
    return rows.drop_duplicates(["date","contract_id"],keep="last").set_index(["date","contract_id"]).sort_index()


def payoff_max_loss(leg, quotes, dt, spot):
    n=leg["n"]; shape=leg["shape"]
    qa=q_at(quotes,dt,leg["atm_id"]);qs=q_at(quotes,dt,leg["short_id"]);qw=q_at(quotes,dt,leg["wing_id"])
    if any(x is None for x in (qa,qs,qw)):return None
    ae=executable(qa,"BUY");se=executable(qs,"SELL");we=executable(qw,"BUY")
    if any(pd.isna(x) for x in (ae,se,we)):return None
    entry_cf=(ae-n*se+n*we)*100.0
    grid=np.linspace(max(1.,spot*.20),max(spot*2.5,leg["wing_k"]*1.25),700)
    if shape=="CALL_RATIO":
        payoff=(np.maximum(grid-leg["atm_k"],0)-n*np.maximum(grid-leg["short_k"],0)+n*np.maximum(grid-leg["wing_k"],0))*100
    else:
        payoff=(np.maximum(grid-leg["atm_k"],0)-n*np.maximum(leg["short_k"]-grid,0)+n*np.maximum(leg["wing_k"]-grid,0))*100
    return max(0.,-float(np.min(entry_cf+payoff)))


def final_cf(leg,quotes,dt):
    n=leg["n"]
    qa=q_at(quotes,dt,leg["atm_id"]);qs=q_at(quotes,dt,leg["short_id"]);qw=q_at(quotes,dt,leg["wing_id"])
    sa=executable(qa,"SELL");bs=executable(qs,"BUY");sw=executable(qw,"SELL")
    if any(pd.isna(x) for x in (sa,bs,sw)):return None
    return (sa-n*bs+n*sw)*100


def mark_cf(leg,quotes,dt):
    n=leg["n"]
    ma=midpoint(q_at(quotes,dt,leg["atm_id"]))
    ms=midpoint(q_at(quotes,dt,leg["short_id"]))
    mw=midpoint(q_at(quotes,dt,leg["wing_id"]))
    if any(pd.isna(x) for x in (ma,ms,mw)):return np.nan
    return (ma-n*ms+n*mw)*100


def run_switch(und,selection,quotes):
    rows=und[und["dma200"].notna()].copy()
    trades=[];rejects={};next_allowed=None
    for _,r in rows.iterrows():
        dt=pd.Timestamp(r["date"])
        if next_allowed is not None and dt<=next_allowed:continue
        regime=None
        if float(r["close"]/r["high52w"])>=HEAT_RATIO and float(r["close"]/r["dma200"]-1)>=HEAT_EXT:
            regime="HEAT"
        elif float(r["close"]/r["high52w"])<=CRASH_RATIO and float(r["close"]/r["dma200"]-1)<=CRASH_EXT:
            regime="POST_CRASH"
        else:continue
        leg=selection.get((dt,regime))
        if leg is None:rejects["NO_LEGS"]=rejects.get("NO_LEGS",0)+1;continue
        spot=float(r["close"]); n=leg["n"]
        ml=payoff_max_loss(leg,quotes,dt,spot)
        if ml is None:rejects["NO_ENTRY_QUOTES"]=rejects.get("NO_ENTRY_QUOTES",0)+1;continue
        if ml>CAPITAL_USD*(RISK_PCT/100):rejects["RISK_GATE"]=rejects.get("RISK_GATE",0)+1;continue

        qa=q_at(quotes,dt,leg["atm_id"]);qs=q_at(quotes,dt,leg["short_id"]);qw=q_at(quotes,dt,leg["wing_id"])
        ae=executable(qa,"BUY");se=executable(qs,"SELL");we=executable(qw,"BUY")
        entry_cf=(ae-n*se+n*we)*100
        end=min(dt+pd.Timedelta(days=HOLD_MAX),leg["expiry"])
        daily=und[(und["date"]>=dt)&(und["date"]<=end)].copy()
        eq=[] 
        for _,dr in daily.iterrows():
            d=pd.Timestamp(dr["date"]);m=mark_cf(leg,quotes,d)
            if pd.notna(m):eq.append((d,CAPITAL_USD-entry_cf+m))
        exit_date=end;cf=final_cf(leg,quotes,exit_date)
        if cf is None:
            rejects["NO_EXIT_QUOTES"]=rejects.get("NO_EXIT_QUOTES",0)+1;continue
        pnl=-entry_cf+cf
        eq.append((exit_date,CAPITAL_USD+pnl))
        trades.append({
            "entry":dt,"exit":exit_date,"regime":regime,"shape":leg["shape"],"n":n,
            "atm_k":leg["atm_k"],"short_k":leg["short_k"],"wing_k":leg["wing_k"],
            "entry_cashflow_usd":entry_cf,"pnl_usd":pnl,"max_loss_usd":ml,"eq_rows":eq
        })
        next_allowed=exit_date+pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:return {"mode":"STATE_SWITCH_V1_1_SQL","trades":0,"rejections":rejects},trades,pd.DataFrame()
    trdf=pd.DataFrame([{k:v for k,v in t.items() if k!="eq_rows"} for t in trades]).sort_values("entry").reset_index(drop=True)
    pts=[p for t in trades for p in t["eq_rows"]]
    eqdf=pd.DataFrame(pts,columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"]=eqdf["equity"].cummax();eqdf["dd"]=eqdf["equity"]/eqdf["peak"]-1
    end_eq=CAPITAL_USD+trdf["pnl_usd"].sum()
    years=max((trdf["exit"].iloc[-1]-trdf["entry"].iloc[0]).days/365.25,1/365.25)
    total=end_eq/CAPITAL_USD-1
    cagr=(1+total)**(1/years)-1 if 1+total>0 else -1
    stats={
        "mode":"STATE_SWITCH_V1_1_SQL","trades":len(trdf),
        "heat_trades":int((trdf.regime=="HEAT").sum()),
        "post_crash_trades":int((trdf.regime=="POST_CRASH").sum()),
        "win_rate":float((trdf.pnl_usd>0).mean()),
        "avg_trade_usd":float(trdf.pnl_usd.mean()),
        "worst_trade_usd":float(trdf.pnl_usd.min()),
        "best_trade_usd":float(trdf.pnl_usd.max()),
        "total_return":float(total),"cagr":float(cagr),
        "maxdd_daily_mtm":float(eqdf.dd.min()),
        "maxdd_realized":float((trdf.pnl_usd.cumsum().add(CAPITAL_USD).div(trdf.pnl_usd.cumsum().add(CAPITAL_USD).cummax())-1).min()),
        "years":float(years),"rejections":rejects,
        "data_start":str(trdf.entry.min().date()),"data_end":str(trdf.exit.max().date())
    }
    return stats,trades,eqdf


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts");args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    opt_path,und_path=ensure_data(Path(args.data_dir));und=load_underlying(und_path)
    con=duckdb.connect()
    selection=build_regime_selection(con,opt_path,und)
    print("SELECTION_COUNT",len(selection),flush=True)
    quotes=fetch_leg_quotes(con,opt_path,selection)
    print("QUOTE_ROWS",len(quotes),flush=True)
    stats,trades,eqdf=run_switch(und,selection,quotes)
    pd.DataFrame([{**{k:v for k,v in t.items() if k!="eq_rows"},"events_json":"[]"} for t in trades]).to_csv(out/"trades_STATE_SWITCH_V1_1.csv",index=False)
    if not eqdf.empty:eqdf.to_csv(out/"equity_STATE_SWITCH_V1_1.csv",index=False)
    report={
      "research_contract":{
        "strategy":"State-conditioned payoff switch",
        "heat":"1 ATM Call -2 20Δ OTM Calls +2 8Δ farther OTM Calls",
        "heat_signal":"close/52w_high >=0.98 AND close/200DMA-1 >=0.08",
        "post_crash":"1 ATM Call -1 20Δ OTM Put +1 8Δ farther OTM Put",
        "post_crash_signal":"close/200DMA-1 <=-0.05 AND close/52w_high <=0.90",
        "neutral":"no trade","DTE":[DTE_MIN,DTE_MAX],"hold_max_days":HOLD_MAX,
        "risk_budget":"2% NAV","execution":"Ask/Bid entry and exit, daily Mid mark",
        "no_optimization":True
      },
      "data":{
        "source_repo":RELEASE_REPO,"release_tag":RELEASE_TAG,
        "options_sha256":sha256_file(opt_path),"underlying_sha256":sha256_file(und_path),
        "underlying_range":[str(und.date.min().date()),str(und.date.max().date())],
        "selection_count":len(selection)
      },
      "results":[stats]
    }
    (out/"state_switch_v1_1_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame([stats]).to_csv(out/"state_switch_v1_1_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__":main()
