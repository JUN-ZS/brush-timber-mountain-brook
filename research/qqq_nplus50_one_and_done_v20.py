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
        AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
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

def build_sequences(u,signals,by_date):
    seqs={}; missing_legs=0
    for ld in LONG_DELTAS:
      for sd in SHORT_DELTAS:
        candidates=[]
        for _,row in signals.iterrows():
          dt=pd.Timestamp(row.date)
          legs=choose_legs(by_date.get(dt),float(row.close),ld,sd,dt)
          if legs is None:
            missing_legs+=1; continue
          end=min(dt+pd.Timedelta(days=HOLD_MAX),legs["expiry"])
          daily=u[(u.date>dt)&(u.date<=end)]
          exit_date=None; reason="EXPIRY_OR_TIME"
          for _,d in daily.iterrows():
            if float(d.high)>=legs["short_k"]:
              exit_date=pd.Timestamp(d.date); reason="SHORT_TOUCH"; break
          if exit_date is None:
            w=u[(u.date>=dt)&(u.date<=end)]
            if w.empty:continue
            exit_date=pd.Timestamp(w.iloc[-1].date)
          candidates.append({
            "entry":dt,"exit_intended":exit_date,"reason":reason,
            "long_id":legs["long_id"],"short_id":legs["short_id"],
            "long_k":legs["long_k"],"long_delta":legs["long_delta"],
            "short_k":legs["short_k"],"short_delta":legs["short_delta"],"expiry":legs["expiry"],
            "ld":ld,"sd":sd
          })
        out=[]; next_allowed=None
        for tr in candidates:
          if next_allowed is not None and tr["entry"]<=next_allowed:continue
          out.append(tr); next_allowed=tr["exit_intended"]+pd.Timedelta(days=COOLDOWN_DAYS)
        seqs[(ld,sd)]=out
    return seqs,missing_legs

def load_quotes(con,opt_path,seqs):
    ids=sorted({z for seq in seqs.values() for tr in seq for z in (tr["long_id"],tr["short_id"])})
    starts=[tr["entry"] for seq in seqs.values() for tr in seq]
    ends=[tr["exit_intended"]+pd.Timedelta(days=5) for seq in seqs.values() for tr in seq]
    if not ids:return pd.DataFrame()
    q=con.execute("""
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS cid,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
    """,[str(opt_path),ids,min(starts).date(),max(ends).date()]).df()
    q["date"]=pd.to_datetime(q.date); q["cid"]=q.cid.astype(str)
    return q.sort_values(["date","cid"]).drop_duplicates(["cid","date"])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); signals=u[u.signal & u.dma200.notna()].copy(); con=duckdb.connect()
    chains=load_signal_chains(con,od,signals.date.tolist())
    chains["date"]=pd.to_datetime(chains.date); chains["expiration"]=pd.to_datetime(chains.expiration)
    chains["dte"]=(chains.expiration-chains.date).dt.days
    by_date={d:g for d,g in chains.groupby("date",sort=False)}
    seqs,missing_legs=build_sequences(u,signals,by_date)
    specs=pd.DataFrame([tr for seq in seqs.values() for tr in seq])
    if specs.empty:raise RuntimeError("No candidate sequences")
    q=load_quotes(con,od,seqs)
    if q.empty:raise RuntimeError("No option quotes loaded")

    specs["key"]=np.arange(len(specs))
    # Exact entry quote, one per contract/date.
    ent=specs[["key","entry","long_id","short_id"]].copy()
    ent_l=ent[["key","entry","long_id"]].rename(columns={"long_id":"cid","entry":"date"})
    ent_s=ent[["key","entry","short_id"]].rename(columns={"short_id":"cid","entry":"date"})
    ent_l=ent_l.merge(q,on=["cid","date"],how="left").rename(columns={"bid":"long_entry_bid","ask":"long_entry_ask"})
    ent_s=ent_s.merge(q,on=["cid","date"],how="left").rename(columns={"bid":"short_entry_bid","ask":"short_entry_ask"})
    entry=ent_l[["key","long_entry_bid","long_entry_ask"]].merge(ent_s[["key","short_entry_bid","short_entry_ask"]],on="key",how="outer")

    # Exit quote: exact intended date, else first common available quote within 5 days.
    # Avoid merge_asof's multi-key sorting requirements by doing an explicit
    # per-contract forward lookup against the already-loaded quote table.
    qrows={}
    for cid,grp in q.groupby("cid",sort=False):
        g2=grp.sort_values("date")
        qrows[str(cid)]=(
            g2["date"].to_numpy(dtype="datetime64[ns]"),
            g2["bid"].to_numpy(dtype=float),
            g2["ask"].to_numpy(dtype=float),
        )

    def first_quote(cid, target):
        arr=qrows.get(str(cid))
        if arr is None:
            return None
        dates,bids,asks=arr
        t=np.datetime64(pd.Timestamp(target).to_datetime64())
        j=int(np.searchsorted(dates,t,side="left"))
        if j>=len(dates):
            return None
        if dates[j] > t + np.timedelta64(5,"D"):
            return None
        return pd.Timestamp(dates[j]), float(bids[j]), float(asks[j])

    exit_rows=[]
    for rr in specs[["key","exit_intended","long_id","short_id"]].itertuples(index=False):
        lq=first_quote(rr.long_id,rr.exit_intended)
        sq=first_quote(rr.short_id,rr.exit_intended)
        if lq is None or sq is None:
            exit_rows.append({
                "key":int(rr.key),"exit_quote_date":pd.NaT,"exit_quote_date_s":pd.NaT,
                "long_exit_bid":np.nan,"long_exit_ask":np.nan,
                "short_exit_bid":np.nan,"short_exit_ask":np.nan,
            })
        else:
            exit_rows.append({
                "key":int(rr.key),"exit_quote_date":lq[0],"exit_quote_date_s":sq[0],
                "long_exit_bid":lq[1],"long_exit_ask":lq[2],
                "short_exit_bid":sq[1],"short_exit_ask":sq[2],
            })
    exitq=pd.DataFrame(exit_rows)
    merged=specs.merge(entry,on="key",how="left").merge(exitq,on="key",how="left")
    before=len(merged)
    merged=merged.dropna(subset=["long_entry_ask","short_entry_bid","long_exit_bid","short_exit_ask"]).copy()
    quote_fail=before-len(merged)
    if merged.empty:raise RuntimeError("All candidates missing executable quotes")

    expanded=merged.loc[merged.index.repeat(len(NS))].copy()
    expanded["n"]=np.tile(NS,len(merged))
    expanded["entry_cf_usd"]=(expanded.long_entry_ask-expanded.n*expanded.short_entry_bid)*100.0
    expanded["exit_cf_usd"]=(expanded.long_exit_bid-expanded.n*expanded.short_exit_ask)*100.0
    expanded["pnl_usd"]=-expanded.entry_cf_usd+expanded.exit_cf_usd
    trades=expanded
    trades.to_csv(out/"nplus50_trades.csv",index=False)

    summaries=[]
    for (ld,sd,n),g in trades.groupby(["ld","sd","n"],sort=True):
      g=g.sort_values("entry").reset_index(drop=True); vals=(g.pnl_usd>0).to_numpy()
      longest=cur=0
      for v in vals:
        cur=cur+1 if v else 0; longest=max(longest,cur)
      starts=max(len(vals)-9,0); ten=sum(bool(vals[i:i+10].all()) for i in range(starts))
      neg=g.loc[g.pnl_usd<0,"pnl_usd"];pos=g.loc[g.pnl_usd>0,"pnl_usd"]
      summaries.append({
        "long_delta_target":float(ld),"short_delta_target":float(sd),"n":int(n),"trades":int(len(g)),
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
      "diagnostics":{"signal_count":int(len(signals)),"missing_legs_count":int(missing_legs),"sequence_count":int(len(specs)),
      "quotes_rows":int(len(q)),"quote_fail_sequence_count":int(quote_fail),"trade_rows":int(len(trades))},
      "top10":top.head(10).to_dict("records")}
    (out/"nplus50_matrix_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__":main()
