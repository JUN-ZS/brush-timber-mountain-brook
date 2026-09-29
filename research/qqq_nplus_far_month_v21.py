#!/usr/bin/env python3
"""V21: extreme-high gate, 1 near-ATM long + N FOTM shorts, 60-120 DTE."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START=pd.Timestamp("2011-01-01"); END=pd.Timestamp("2025-12-31")
DTE_MIN=60; DTE_MAX=120; HOLD_MAX=30; COOLDOWN_DAYS=10
PCT_52W=0.98; DMA_EXT=0.08
LONG_DELTAS=(0.50,0.55,0.70,0.90)
SHORT_DELTAS=(0.01,0.02,0.05,0.08,0.10)
NS=(2,10,20,50)
TARGET_WINS=10

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
        AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN
          CAST(date AS DATE)+INTERVAL 60 DAY
          AND CAST(date AS DATE)+INTERVAL 120 DAY
    """,[str(opt_path),[pd.Timestamp(d).date() for d in dates]]).df()

def choose_legs(chain,spot,long_target,short_target):
    if chain is None or chain.empty:return None
    g=chain.copy()
    g["dte"]=(g.expiration-g.date).dt.days
    ex=g.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    g=g[g.expiration==ex]
    if float(long_target)<=0.55:
        longs=g[(g.delta>=0.45)&(g.delta<=0.60)].copy()
    else:
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

def one_and_done(vals, pnls, prefix=""):
    wins=0; stopped_at=0; pnl=0.0; reached=False; first_loss=False
    for i,(w,p) in enumerate(zip(vals, pnls), start=1):
        pnl += float(p); stopped_at=i
        if w:
            wins += 1
            if wins>=TARGET_WINS:
                reached=True; break
        else:
            first_loss=True; break
    pfx=prefix
    return {f"{pfx}from_start_reached_10":bool(reached),
            f"{pfx}from_start_wins_before_stop":int(wins),
            f"{pfx}from_start_pnl_usd":float(pnl),
            f"{pfx}from_start_hit_loss":bool(first_loss)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); signals=u[u.signal & u.dma200.notna()].copy(); con=duckdb.connect()
    chains=load_signal_chains(con,od,signals.date.tolist())
    chains["date"]=pd.to_datetime(chains.date); chains["expiration"]=pd.to_datetime(chains.expiration)
    by_date={d:g for d,g in chains.groupby("date",sort=False)}
    seqs={}; missing=0
    for ld in LONG_DELTAS:
      for sd in SHORT_DELTAS:
        cands=[]
        for _,row in signals.iterrows():
          dt=pd.Timestamp(row.date)
          legs=choose_legs(by_date.get(dt),float(row.close),ld,sd)
          if legs is None:
            missing+=1; continue
          end=min(dt+pd.Timedelta(days=HOLD_MAX),legs["expiry"])
          daily=u[(u.date>dt)&(u.date<=end)]
          exit_date=None; reason="EXPIRY_OR_TIME"
          for _,d in daily.iterrows():
            if float(d.high)>=legs["short_k"]:
              exit_date=pd.Timestamp(d.date); reason="SHORT_TOUCH"; break
          if exit_date is None:
            w=u[(u.date>=dt)&(u.date<=end)]
            if w.empty: continue
            exit_date=pd.Timestamp(w.iloc[-1].date)
          cands.append(dict(entry=dt,exit_intended=exit_date,reason=reason,ld=ld,sd=sd,**legs))
        outseq=[]; nxt=None
        for tr in cands:
          if nxt is not None and tr["entry"]<=nxt: continue
          outseq.append(tr); nxt=tr["exit_intended"]+pd.Timedelta(days=COOLDOWN_DAYS)
        seqs[(ld,sd)]=outseq
    specs=pd.DataFrame([tr for seq in seqs.values() for tr in seq])
    if specs.empty: raise RuntimeError("No far-month sequences")
    ids=sorted({z for seq in seqs.values() for tr in seq for z in (tr["long_id"],tr["short_id"])})
    q=con.execute("""
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS cid,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
    """,[str(od),ids,min(x["entry"] for seq in seqs.values() for x in seq).date(),
         max(x["exit_intended"] for seq in seqs.values() for x in seq).date()]).df()
    q["date"]=pd.to_datetime(q.date); q["cid"]=q.cid.astype(str)
    q=q.sort_values(["date","cid"]).drop_duplicates(["cid","date"])
    specs["key"]=np.arange(len(specs))
    ent_l=specs[["key","entry","long_id"]].rename(columns={"long_id":"cid","entry":"date"}).merge(q,on=["cid","date"],how="left")
    ent_s=specs[["key","entry","short_id"]].rename(columns={"short_id":"cid","entry":"date"}).merge(q,on=["cid","date"],how="left")
    entry=ent_l.rename(columns={"ask":"long_entry_ask","bid":"long_entry_bid"})[["key","long_entry_ask"]].merge(
          ent_s.rename(columns={"bid":"short_entry_bid","ask":"short_entry_ask"})[["key","short_entry_bid","short_entry_ask"]],on="key")
    qrows={}
    for cid,grp in q.groupby("cid",sort=False):
        g2=grp.sort_values("date")
        qrows[str(cid)]=(g2.date.to_numpy(dtype="datetime64[ns]"), g2.bid.to_numpy(float), g2.ask.to_numpy(float))
    def first_quote(cid,target):
        arr=qrows.get(str(cid))
        if arr is None: return None
        dates,bids,asks=arr
        t=np.datetime64(pd.Timestamp(target).to_datetime64())
        j=int(np.searchsorted(dates,t,side="left"))
        if j>=len(dates) or dates[j] > t+np.timedelta64(5,"D"): return None
        return float(bids[j]), float(asks[j])
    rows=[]
    for rr in specs[["key","exit_intended","long_id","short_id"]].itertuples(index=False):
        lq=first_quote(rr.long_id,rr.exit_intended); sq=first_quote(rr.short_id,rr.exit_intended)
        rows.append({"key":int(rr.key),
                     "long_exit_bid": None if lq is None else lq[0],
                     "short_exit_ask": None if sq is None else sq[1]})
    merged=specs.merge(entry,on="key").merge(pd.DataFrame(rows),on="key")
    before=len(merged)
    merged=merged.dropna(subset=["long_entry_ask","short_entry_bid","long_exit_bid","short_exit_ask"])
    expanded=merged.loc[merged.index.repeat(len(NS))].copy()
    expanded["n"]=np.tile(NS,len(merged))
    expanded["entry_cf_usd"]=(expanded.long_entry_ask-expanded.n*expanded.short_entry_bid)*100.0
    expanded["exit_cf_usd"]=(expanded.long_exit_bid-expanded.n*expanded.short_exit_ask)*100.0
    expanded["pnl_usd"]=-expanded.entry_cf_usd+expanded.exit_cf_usd
    expanded["geo_win"]=expanded.reason!="SHORT_TOUCH"
    expanded["dollar_win"]=expanded.pnl_usd>0
    summaries=[]
    for (ld,sd,n),g in expanded.groupby(["ld","sd","n"],sort=True):
        g=g.sort_values("entry")
        dollar=g.dollar_win.to_numpy(); geo=g.geo_win.to_numpy(); pnls=g.pnl_usd.to_numpy(float)
        row={"long_delta_target":float(ld),"short_delta_target":float(sd),"n":int(n),"trades":int(len(g)),
             "geo_no_touch_rate":float(geo.mean()),"dollar_win_rate":float(dollar.mean()),
             "mean_short_entry_bid":float(g.short_entry_bid.mean()),
             "mean_long_entry_ask":float(g.long_entry_ask.mean()),
             "mean_entry_debit_usd":float(g.entry_cf_usd.mean()),
             "mean_dte":float((g.expiry-g.entry).dt.days.mean()) if "expiry" in g else None,
             "worst_pnl_usd":float(g.pnl_usd.min()),"total_pnl_usd":float(g.pnl_usd.sum())}
        row.update(one_and_done(dollar,pnls,"dollar_"))
        row.update(one_and_done(geo,pnls,"geo_"))
        summaries.append(row)
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/"v21_far_month_summary.csv",index=False)
    by_sd=summary.groupby("short_delta_target").agg(
        mean_geo=("geo_no_touch_rate","mean"),mean_dollar=("dollar_win_rate","mean"),
        mean_short_bid=("mean_short_entry_bid","mean"),mean_debit=("mean_entry_debit_usd","mean"),
        n10_dollar=("dollar_win_rate","mean")
    ).reset_index()
    n10=summary[summary.n==10].sort_values(["short_delta_target","long_delta_target"])
    report={"status":"REAL_QQQ_CHAIN_FAR_MONTH_V21",
            "contract":{"gate":"close/52w>=0.98 AND ext200>=8%","dte":[DTE_MIN,DTE_MAX],"hold_max":HOLD_MAX,
                        "structure":"1 near-ATM long + N FOTM short, same expiry"},
            "data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud)},
            "diagnostics":{"signals":int(len(signals)),"missing_legs":int(missing),
                           "sequences":int(len(specs)),"quote_fail":int(before-len(merged)),
                           "trades":int(len(expanded))},
            "by_short_delta":by_sd.to_dict("records"),
            "n10":n10.to_dict("records")}
    (out/"v21_far_month_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__": main()
