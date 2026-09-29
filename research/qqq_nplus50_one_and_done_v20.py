#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

CAPITAL_USD=500000.0/7.8
START=pd.Timestamp("2011-01-01"); END=pd.Timestamp("2025-12-31")
DTE_MIN=18; DTE_MAX=35; HOLD_MAX=30; COOLDOWN_DAYS=10
PCT_52W=0.98; DMA_EXT=0.08
LONG_DELTAS=(0.55,0.60,0.70,0.80,0.90)
SHORT_DELTAS=(0.01,0.02,0.03,0.05,0.08,0.10)
NS=(2,3,4,5,8,10,15,20,30,40,50)

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def load_underlying(path):
    x=pd.read_parquet(path)
    x.columns=[c.lower() for c in x.columns]
    x["date"]=pd.to_datetime(x["date"]).dt.tz_localize(None).dt.normalize()
    x=x.sort_values("date").drop_duplicates("date")
    x=x[(x.date>=START)&(x.date<=END)].copy()
    x["dma200"]=x.close.rolling(200,min_periods=200).mean()
    x["high52w"]=x.close.rolling(252,min_periods=252).max()
    x["ext200"]=x.close/x.dma200-1
    x["ratio52"]=x.close/x.high52w
    x["signal"]=(x.ratio52>=PCT_52W)&(x.ext200>=DMA_EXT)
    return x.reset_index(drop=True)

def load_signal_chains(con,opt_path,dates):
    return con.execute("""
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume,
             CAST(delta AS DOUBLE) AS delta
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND UPPER("type")='CALL'
        AND delta IS NOT NULL
        AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN
          CAST(date AS DATE)+INTERVAL 18 DAY
          AND CAST(date AS DATE)+INTERVAL 35 DAY
    """,[str(opt_path),[pd.Timestamp(d).date() for d in dates]]).df()

def choose_legs(chain,spot,long_target,short_target,entry):
    if chain.empty:return None
    g=chain.copy()
    g["expiration"]=pd.to_datetime(g.expiration)
    g["dte"]=(g.expiration-pd.Timestamp(entry)).dt.days
    ex=g.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    g=g[g.expiration==ex]
    longs=g[(g.delta>=0.50)&(g.strike<float(spot))].copy()
    if longs.empty:return None
    longs["err"]=(longs.delta-float(long_target)).abs()
    lp=longs.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    shorts=g[g.strike>lp.strike].copy()
    if shorts.empty:return None
    shorts["err"]=(shorts.delta-float(short_target)).abs()
    sp=shorts.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    return {
      "expiry":pd.Timestamp(ex),
      "long_id":str(lp.contract_id),"long_k":float(lp.strike),"long_delta":float(lp.delta),
      "short_id":str(sp.contract_id),"short_k":float(sp.strike),"short_delta":float(sp.delta)
    }

def load_quotes(con,opt_path,ids,start,end):
    if not ids:return pd.DataFrame()
    q=con.execute("""
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
        AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
    """,[str(opt_path),sorted(ids),start.date(),end.date()]).df()
    q["date"]=pd.to_datetime(q.date); q["contract_id"]=q.contract_id.astype(str)
    return q.set_index(["date","contract_id"]).sort_index()

def find_quote(q,dt,cid,side=None):
    key=(pd.Timestamp(dt),str(cid))
    try:r=q.loc[key]
    except KeyError:return None
    return {"bid":float(r.bid),"ask":float(r.ask)}

def next_common_quote(q,dt,long_id,short_id):
    dates=sorted({d for (d,c) in q.index if d>=pd.Timestamp(dt) and c in {long_id,short_id}})
    for d in dates:
        a=find_quote(q,d,long_id); s=find_quote(q,d,short_id)
        if a is not None and s is not None:return pd.Timestamp(d),a,s
    return None,None,None

def build_trade(u,row,legs,q,n):
    entry=pd.Timestamp(row.date)
    end=min(entry+pd.Timedelta(days=HOLD_MAX),legs["expiry"])
    daily=u[(u.date>=entry)&(u.date<=end)].reset_index(drop=True)
    if daily.empty:return None
    qe_l=find_quote(q,entry,legs["long_id"])
    qe_s=find_quote(q,entry,legs["short_id"])
    if qe_l is None or qe_s is None:return None
    exit_date=None; reason="EXPIRY_OR_TIME"
    for _,d in daily.iloc[1:].iterrows():
        if float(d.high)>=legs["short_k"]:
            exit_date=pd.Timestamp(d.date); reason="SHORT_TOUCH"; break
    if exit_date is None:exit_date=pd.Timestamp(daily.iloc[-1].date)
    ql=find_quote(q,exit_date,legs["long_id"]); qs=find_quote(q,exit_date,legs["short_id"])
    if ql is None or qs is None:
        exit_date,ql,qs=next_common_quote(q,exit_date,legs["long_id"],legs["short_id"])
        if exit_date is None:return None
    entry_cf=(qe_l["ask"]-n*qe_s["bid"])*100.0
    exit_cf=(ql["bid"]-n*qs["ask"])*100.0
    return {
      "entry":entry,"exit":exit_date,"reason":reason,"n":int(n),
      "long_k":legs["long_k"],"long_delta":legs["long_delta"],
      "short_k":legs["short_k"],"short_delta":legs["short_delta"],
      "expiry":legs["expiry"],"entry_cf_usd":entry_cf,"exit_cf_usd":exit_cf,
      "pnl_usd":-entry_cf+exit_cf
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud)
    signals=u[u.signal & u.dma200.notna()].copy()
    dates=signals.date.tolist()
    con=duckdb.connect()
    chains=load_signal_chains(con,od,dates)
    chains["date"]=pd.to_datetime(chains.date)
    by_date={d:g for d,g in chains.groupby("date",sort=False)}
    target_legs={}
    all_ids=set(); rejects={}
    for ld in LONG_DELTAS:
      for sd in SHORT_DELTAS:
        legs_by_entry={}
        for _,row in signals.iterrows():
          dt=pd.Timestamp(row.date)
          legs=choose_legs(by_date.get(dt,pd.DataFrame()),float(row.close),ld,sd,dt)
          if legs is None:
            rejects["NO_LEGS"]=rejects.get("NO_LEGS",0)+1; continue
          legs_by_entry[dt]=legs
          all_ids.add(legs["long_id"]); all_ids.add(legs["short_id"])
        target_legs[(ld,sd)]=legs_by_entry

    quotes=load_quotes(con,od,all_ids,pd.Timestamp(signals.date.min()),pd.Timestamp(signals.date.max())+pd.Timedelta(days=HOLD_MAX+5))
    rows=[]; reject_trade=0
    for ld in LONG_DELTAS:
      for sd in SHORT_DELTAS:
        for n in NS:
          next_allowed=None
          for _,row in signals.iterrows():
            entry=pd.Timestamp(row.date)
            if next_allowed is not None and entry<=next_allowed:continue
            legs=target_legs[(ld,sd)].get(entry)
            if legs is None:continue
            tr=build_trade(u,row,legs,quotes,n)
            if tr is None:
              reject_trade+=1; continue
            tr.update(long_delta_target=ld,short_delta_target=sd)
            rows.append(tr)
            next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)

    trades=pd.DataFrame(rows)
    if trades.empty:raise RuntimeError("No trades produced")
    trades.to_csv(out/"nplus50_trades.csv",index=False)

    summaries=[]
    for (ld,sd,n),g in trades.groupby(["long_delta_target","short_delta_target","n"],sort=True):
        g=g.sort_values("entry").reset_index(drop=True)
        vals=(g.pnl_usd>0).to_numpy()
        longest=cur=0
        for v in vals:
            cur=cur+1 if v else 0
            longest=max(longest,cur)
        starts=max(len(vals)-9,0)
        ten=sum(bool(vals[i:i+10].all()) for i in range(starts))
        neg=g.loc[g.pnl_usd<0,"pnl_usd"]; pos=g.loc[g.pnl_usd>0,"pnl_usd"]
        summaries.append({
          "long_delta_target":ld,"short_delta_target":sd,"n":int(n),"trades":int(len(g)),
          "wins":int(vals.sum()),"losses":int((~vals).sum()),"win_rate":float(vals.mean()),
          "avg_pnl_usd":float(g.pnl_usd.mean()),"median_pnl_usd":float(g.pnl_usd.median()),
          "best_pnl_usd":float(g.pnl_usd.max()),"worst_pnl_usd":float(g.pnl_usd.min()),
          "total_pnl_usd":float(g.pnl_usd.sum()),
          "profit_factor":float(pos.sum()/abs(neg.sum())) if len(neg) else float("inf"),
          "longest_win_streak":int(longest),"ten_win_start_rate":float(ten/starts) if starts else 0.0,
          "ten_win_completions":int(ten)
        })
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/"nplus50_matrix_summary.csv",index=False)
    top=summary.sort_values(["ten_win_start_rate","win_rate","profit_factor","total_pnl_usd"],ascending=[False,False,False,False]).reset_index(drop=True)
    top.to_csv(out/"nplus50_ranked.csv",index=False)
    report={"status":"REAL_QQQ_CHAIN_MATRIX_REPLAY","data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud),
      "underlying_range":[str(u.date.min().date()),str(u.date.max().date())]},
      "parameters":{"long_delta_targets":LONG_DELTAS,"short_delta_targets":SHORT_DELTAS,"N":NS,
      "signal":"close/52w_high>=0.98 AND close/200dma-1>=0.08","expiry_dte":[DTE_MIN,DTE_MAX],"hold_max":HOLD_MAX,
      "cooldown":COOLDOWN_DAYS,"long_must_be_itm":True,"exit":"first post-entry short-strike High touch, else 30d/expiry"},
      "rows":int(len(trades)),"rejects":{**rejects,"TRADE_BUILD_FAIL":reject_trade},"top10":top.head(10).to_dict("records")}
    (out/"nplus50_matrix_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__": main()
