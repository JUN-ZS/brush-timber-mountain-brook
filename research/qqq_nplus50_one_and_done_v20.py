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
    if chain is None or chain.empty:return None
    g=chain
    ex=g.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    g=g[g.expiration==ex]
    longs=g[(g.delta>=0.50)&(g.strike<float(spot))]
    if longs.empty:return None
    dist=(longs.delta-float(long_target)).abs()
    lp=longs.assign(err=dist).sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    shorts=g[g.strike>lp.strike]
    if shorts.empty:return None
    dist=(shorts.delta-float(short_target)).abs()
    sp=shorts.assign(err=dist).sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    return {"expiry":pd.Timestamp(ex),"long_id":str(lp.contract_id),"long_k":float(lp.strike),
            "long_delta":float(lp.delta),"short_id":str(sp.contract_id),"short_k":float(sp.strike),
            "short_delta":float(sp.delta)}

def build_sequence(u,signals,by_date,ld,sd):
    candidates=[]
    for _,row in signals.iterrows():
        dt=pd.Timestamp(row.date)
        legs=choose_legs(by_date.get(dt),float(row.close),ld,sd,dt)
        if legs is None:continue
        end=min(dt+pd.Timedelta(days=HOLD_MAX),legs["expiry"])
        daily=u[(u.date>dt)&(u.date<=end)]
        exit_date=None
        for _,d in daily.iterrows():
            if float(d.high)>=legs["short_k"]:
                exit_date=pd.Timestamp(d.date); break
        if exit_date is None:
            w=u[(u.date>=dt)&(u.date<=end)]
            if w.empty:continue
            exit_date=pd.Timestamp(w.iloc[-1].date)
        candidates.append({
          "entry":dt,"exit":exit_date,"long_id":legs["long_id"],"short_id":legs["short_id"],
          "long_k":legs["long_k"],"long_delta":legs["long_delta"],
          "short_k":legs["short_k"],"short_delta":legs["short_delta"],"expiry":legs["expiry"],
        })
    out=[]; next_allowed=None
    for tr in candidates:
        if next_allowed is not None and tr["entry"]<=next_allowed:continue
        out.append(tr); next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)
    return out

def load_needed_quotes(con,opt_path,seqs):
    rows=[]
    rid=0
    for (ld,sd),seq in seqs.items():
        for tr in seq:
            for cid in (tr["long_id"],tr["short_id"]):
                rows.append({"req_id":rid,"group_ld":ld,"group_sd":sd,"entry":tr["entry"],"exit":tr["exit"],
                              "cid":cid,"req_kind":"ENTRY","start":tr["entry"],"end":tr["entry"]})
                rid+=1
                rows.append({"req_id":rid,"group_ld":ld,"group_sd":sd,"entry":tr["entry"],"exit":tr["exit"],
                              "cid":cid,"req_kind":"EXIT_WINDOW","start":tr["exit"],"end":tr["exit"]+pd.Timedelta(days=5)})
                rid+=1
    req=pd.DataFrame(rows).drop_duplicates(["group_ld","group_sd","entry","exit","cid","req_kind"])
    con.register("req",req)
    q=con.execute("""
      SELECT r.group_ld,r.group_sd,r.entry,r.exit,r.cid,r.req_kind,
             CAST(o.date AS DATE) AS qdate,
             CAST(o.bid AS DOUBLE) AS bid,CAST(o.ask AS DOUBLE) AS ask
      FROM req r
      JOIN read_parquet(?) o
        ON CAST(o.contract_id AS VARCHAR)=r.cid
       AND CAST(o.date AS DATE) BETWEEN CAST(r.start AS DATE) AND CAST(r.end AS DATE)
      WHERE o.bid IS NOT NULL AND o.ask IS NOT NULL
        AND o.ask>=o.bid AND o.bid>=0
    """,[str(opt_path)]).df()
    q["qdate"]=pd.to_datetime(q.qdate)
    return q

def quote_for(q,gld,gsd,entry,exit_date,cid,kind):
    x=q[(q.group_ld==gld)&(q.group_sd==gsd)&(q.entry==entry)&(q.exit==exit_date)&(q.cid==cid)]
    if x.empty:return None
    if kind=="ENTRY":
        y=x[x.req_kind=="ENTRY"]
        if not y.empty:
            return float(y.iloc[0].bid),float(y.iloc[0].ask),pd.Timestamp(y.iloc[0].qdate)
        return None
    y=x[(x.req_kind=="EXIT_WINDOW") & (x.qdate>=pd.Timestamp(exit_date))].sort_values("qdate")
    if y.empty:return None
    return float(y.iloc[0].bid),float(y.iloc[0].ask),pd.Timestamp(y.iloc[0].qdate)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet";ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud);signals=u[u.signal & u.dma200.notna()].copy();con=duckdb.connect()
    chains=load_signal_chains(con,od,signals.date.tolist());chains["date"]=pd.to_datetime(chains.date)
    chains["expiration"]=pd.to_datetime(chains.expiration)
    chains["dte"]=(chains.expiration-chains.date).dt.days
    by_date={d:g for d,g in chains.groupby("date",sort=False)}

    seqs={}; rejects={"NO_LEGS":0}
    for ld in LONG_DELTAS:
      for sd in SHORT_DELTAS:
        seq=build_sequence(u,signals,by_date,ld,sd)
        seqs[(ld,sd)]=seq
        rejects["NO_LEGS"]+=len(signals)-len([x for x in seq])  # diagnostics only; not used for gating

    q=load_needed_quotes(con,od,seqs)
    rows=[]; quote_fail=0
    for (ld,sd),seq in seqs.items():
      for tr in seq:
        qe_l=quote_for(q,ld,sd,tr["entry"],tr["exit"],tr["long_id"],"ENTRY")
        qe_s=quote_for(q,ld,sd,tr["entry"],tr["exit"],tr["short_id"],"ENTRY")
        qx_l=quote_for(q,ld,sd,tr["entry"],tr["exit"],tr["long_id"],"EXIT")
        qx_s=quote_for(q,ld,sd,tr["entry"],tr["exit"],tr["short_id"],"EXIT")
        if any(x is None for x in (qe_l,qe_s,qx_l,qx_s)):
            quote_fail+=1; continue
        for n in NS:
          entry_cf=(qe_l[1]-n*qe_s[0])*100.0
          exit_cf=(qx_l[0]-n*qx_s[1])*100.0
          rows.append({
            "entry":tr["entry"],"exit":qx_l[2],"intended_exit":tr["exit"],"reason":"SHORT_TOUCH" if tr["exit"]<min(tr["entry"]+pd.Timedelta(days=HOLD_MAX),tr["expiry"]) else "EXPIRY_OR_TIME",
            "n":n,"long_delta_target":ld,"short_delta_target":sd,"long_k":tr["long_k"],"long_delta":tr["long_delta"],
            "short_k":tr["short_k"],"short_delta":tr["short_delta"],"expiry":tr["expiry"],
            "entry_cf_usd":entry_cf,"exit_cf_usd":exit_cf,"pnl_usd":-entry_cf+exit_cf
          })
    trades=pd.DataFrame(rows)
    if trades.empty:raise RuntimeError("No trades produced after quote join")
    trades.to_csv(out/"nplus50_trades.csv",index=False)

    summaries=[]
    for (ld,sd,n),g in trades.groupby(["long_delta_target","short_delta_target","n"],sort=True):
      g=g.sort_values("entry").reset_index(drop=True);vals=(g.pnl_usd>0).to_numpy()
      longest=cur=0
      for v in vals:
        cur=cur+1 if v else 0;longest=max(longest,cur)
      starts=max(len(vals)-9,0);ten=sum(bool(vals[i:i+10].all()) for i in range(starts))
      neg=g.loc[g.pnl_usd<0,"pnl_usd"];pos=g.loc[g.pnl_usd>0,"pnl_usd"]
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
    summary=pd.DataFrame(summaries);summary.to_csv(out/"nplus50_matrix_summary.csv",index=False)
    top=summary.sort_values(["ten_win_start_rate","win_rate","profit_factor","total_pnl_usd"],ascending=[False,False,False,False]).reset_index(drop=True)
    top.to_csv(out/"nplus50_ranked.csv",index=False)
    report={"status":"REAL_QQQ_CHAIN_MATRIX_REPLAY","data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud),
      "underlying_range":[str(u.date.min().date()),str(u.date.max().date())]},
      "parameters":{"long_delta_targets":LONG_DELTAS,"short_delta_targets":SHORT_DELTAS,"N":NS,
      "signal":"close/52w_high>=0.98 AND close/200dma-1>=0.08","expiry_dte":[DTE_MIN,DTE_MAX],"hold_max":HOLD_MAX,
      "cooldown":COOLDOWN_DAYS,"long_must_be_itm":True,"exit":"first post-entry short-strike High touch, else 30d/expiry"},
      "rows":int(len(trades)),"quote_fail":int(quote_fail),"top10":top.head(10).to_dict("records")}
    (out/"nplus50_matrix_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__":main()
