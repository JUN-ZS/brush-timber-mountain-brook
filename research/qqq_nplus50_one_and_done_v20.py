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

def select_chain(con,opt_path,entry_date,spot,long_target,short_target):
    lo=entry_date+pd.Timedelta(days=DTE_MIN); hi=entry_date+pd.Timedelta(days=DTE_MAX)
    q=con.execute("""
      SELECT CAST(expiration AS DATE) expiration,
             CAST(contract_id AS VARCHAR) contract_id,
             CAST(strike AS DOUBLE) strike,
             UPPER("type") AS type_name, CAST(bid AS DOUBLE) bid,
             CAST(ask AS DOUBLE) ask, COALESCE(CAST(volume AS DOUBLE),0) volume,
             CAST(delta AS DOUBLE) delta
      FROM read_parquet(?)
      WHERE CAST(date AS DATE)=?
        AND CAST(expiration AS DATE) BETWEEN ? AND ?
        AND UPPER("type")='CALL'
        AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
    """,[str(opt_path),entry_date.date(),lo.date(),hi.date()]).df()
    if q.empty:return None
    q["expiration"]=pd.to_datetime(q.expiration); q["dte"]=(q.expiration-entry_date).dt.days
    ex=q.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    g=q[q.expiration==ex].copy()
    longs=g[(g.delta>=0.50)&(g.strike<float(spot))].copy()
    if longs.empty:return None
    longs["err"]=(longs.delta-float(long_target)).abs()
    lp=longs.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    shorts=g[g.strike>lp.strike].copy()
    if shorts.empty:return None
    shorts["err"]=(shorts.delta-float(short_target)).abs()
    sp=shorts.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    return {"expiry":pd.Timestamp(ex),"long_id":str(lp.contract_id),"long_k":float(lp.strike),
            "long_delta":float(lp.delta),"short_id":str(sp.contract_id),"short_k":float(sp.strike),
            "short_delta":float(sp.delta)}

def run_one(u,con,opt_path,row,legs,n):
    entry=pd.Timestamp(row.date); end=min(entry+pd.Timedelta(days=HOLD_MAX),legs["expiry"])
    daily=u[(u.date>=entry)&(u.date<=end)].reset_index(drop=True)
    if daily.empty:return None,"NO_WINDOW"
    q=con.execute("""
      SELECT CAST(date AS DATE) date, CAST(contract_id AS VARCHAR) contract_id,
             CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
    """,[str(opt_path),[legs["long_id"],legs["short_id"]],entry.date(),(end+pd.Timedelta(days=5)).date()]).df()
    if q.empty:return None,"NO_QUOTES"
    q["date"]=pd.to_datetime(q.date); q["contract_id"]=q.contract_id.astype(str)
    q=q.set_index(["date","contract_id"]).sort_index()
    def qa(dt,cid):
        try:r=q.loc[(pd.Timestamp(dt),str(cid))]
        except KeyError:return None
        return {"bid":float(r.bid),"ask":float(r.ask)}
    qe_l=qa(entry,legs["long_id"]); qe_s=qa(entry,legs["short_id"])
    if qe_l is None or qe_s is None:return None,"NO_ENTRY_QUOTES"
    entry_cf=(qe_l["ask"]-n*qe_s["bid"])*100.0
    exit_date=None; reason="EXPIRY_OR_TIME"
    for _,d in daily.iloc[1:].iterrows():
        if float(d.high)>=legs["short_k"]:
            exit_date=pd.Timestamp(d.date); reason="SHORT_TOUCH"; break
    if exit_date is None: exit_date=pd.Timestamp(daily.iloc[-1].date)
    ql=qa(exit_date,legs["long_id"]); qs=qa(exit_date,legs["short_id"])
    if ql is None or qs is None:
        future=sorted(set(d for (d,cid) in q.index if d>=exit_date and cid in {legs["long_id"],legs["short_id"]}))
        found=None
        for d in future:
            if qa(d,legs["long_id"]) is not None and qa(d,legs["short_id"]) is not None:
                found=pd.Timestamp(d); break
        if found is None:return None,"NO_EXIT_QUOTES"
        exit_date=found; ql=qa(exit_date,legs["long_id"]); qs=qa(exit_date,legs["short_id"])
    exit_cf=(ql["bid"]-n*qs["ask"])*100.0
    pnl=-entry_cf+exit_cf
    return {"entry":entry,"exit":exit_date,"reason":reason,"n":n,
            "long_k":legs["long_k"],"long_delta":legs["long_delta"],
            "short_k":legs["short_k"],"short_delta":legs["short_delta"],
            "expiry":legs["expiry"],"entry_cf_usd":entry_cf,"exit_cf_usd":exit_cf,
            "pnl_usd":pnl},"OK"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); con=duckdb.connect(); signals=u[u.signal & u.dma200.notna()].copy()
    rows=[]; reject={}
    for ld in LONG_DELTAS:
      for sd in SHORT_DELTAS:
        for n in NS:
          next_allowed=None
          for _,row in signals.iterrows():
            entry=pd.Timestamp(row.date)
            if next_allowed is not None and entry<=next_allowed:
              continue
            legs=select_chain(con,od,entry,float(row.close),ld,sd)
            if legs is None:
              reject["NO_LEGS"]=reject.get("NO_LEGS",0)+1
              continue
            tr,st=run_one(u,con,od,row,legs,n)
            if tr is None:
              reject[st]=reject.get(st,0)+1
              continue
            tr.update(long_delta_target=ld,short_delta_target=sd)
            rows.append(tr)
            next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)
    trades=pd.DataFrame(rows); trades.to_csv(out/"nplus50_trades.csv",index=False)
    summaries=[]
    for (ld,sd,n),g in trades.groupby(["long_delta_target","short_delta_target","n"],sort=True):
        g=g.sort_values("entry").reset_index(drop=True); vals=(g.pnl_usd>0).to_numpy()
        longest=cur=0
        for v in vals:
            cur=cur+1 if v else 0; longest=max(longest,cur)
        starts=max(len(vals)-9,0); ten=sum(vals[i:i+10].all() for i in range(starts))
        neg=g.loc[g.pnl_usd<0,"pnl_usd"]; pos=g.loc[g.pnl_usd>0,"pnl_usd"]
        summaries.append({
          "long_delta_target":ld,"short_delta_target":sd,"n":n,"trades":len(g),
          "wins":int(vals.sum()),"losses":int((~vals).sum()),"win_rate":float(vals.mean()),
          "avg_pnl_usd":float(g.pnl_usd.mean()),"median_pnl_usd":float(g.pnl_usd.median()),
          "best_pnl_usd":float(g.pnl_usd.max()),"worst_pnl_usd":float(g.pnl_usd.min()),
          "total_pnl_usd":float(g.pnl_usd.sum()),
          "profit_factor":float(pos.sum()/abs(neg.sum())) if len(neg) else float("inf"),
          "longest_win_streak":int(longest),
          "ten_win_start_rate":float(ten/starts) if starts else 0.0,
          "ten_win_completions":int(ten)
        })
    summary=pd.DataFrame(summaries); summary.to_csv(out/"nplus50_matrix_summary.csv",index=False)
    top=summary.sort_values(["win_rate","ten_win_start_rate","profit_factor","total_pnl_usd"],ascending=[False,False,False,False]).reset_index(drop=True)
    top.to_csv(out/"nplus50_ranked.csv",index=False)
    report={"status":"REAL_QQQ_CHAIN_MATRIX_REPLAY","data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud),
      "underlying_range":[str(u.date.min().date()),str(u.date.max().date())]},
      "parameters":{"long_delta_targets":LONG_DELTAS,"short_delta_targets":SHORT_DELTAS,"N":NS,
      "signal":"close/52w_high>=0.98 AND close/200dma-1>=0.08","expiry_dte":[DTE_MIN,DTE_MAX],"hold_max":HOLD_MAX,
      "cooldown":COOLDOWN_DAYS,"long_must_be_itm":true,"exit":"first post-entry short-strike High touch, else 30d/expiry"},
      "rows":len(trades),"rejects":reject,"top10":top.head(10).to_dict("records")}
    (out/"nplus50_matrix_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)
if __name__=="__main__": main()
