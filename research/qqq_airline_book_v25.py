#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

CAPITAL=100000.0; GATE=0.02; N=2; HOLD_MAX=30; COOLDOWN=10; GROUND=20
LONG_D=0.55; SHORTS=(0.03,0.05)
START=pd.Timestamp("2011-01-01"); END=pd.Timestamp("2025-12-31")
PCT_52W=0.98; DMA_EXT=0.08

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

def load_chains(con,opt_path,dates):
    return con.execute("""
      SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id, CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume, CAST(delta AS DOUBLE) AS delta
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND UPPER("type")='CALL' AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 18 DAY AND CAST(date AS DATE)+INTERVAL 35 DAY
    """,[str(opt_path),[pd.Timestamp(d).date() for d in dates]]).df()

def pick(g,spot,sd):
    if g is None or g.empty: return None
    g=g.copy(); g["dte"]=(g.expiration-g.date).dt.days
    ex=g.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    g=g[g.expiration==ex]
    longs=g[(g.delta>=0.50)&(g.strike<float(spot))].copy()
    if longs.empty: return None
    longs["err"]=(longs.delta-LONG_D).abs()
    lp=longs.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    shorts=g[g.strike>lp.strike].copy()
    if shorts.empty: return None
    shorts["err"]=(shorts.delta-float(sd)).abs()
    sp=shorts.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    debit=(float(lp.ask)-N*float(sp.bid))*100.0
    return {"expiry":pd.Timestamp(ex),"long_id":str(lp.contract_id),"short_id":str(sp.contract_id),
            "short_k":float(sp.strike),"debit":float(debit),
            "long_ask":float(lp.ask),"short_bid":float(sp.bid)}

def first_quote(qrows,cid,target,side):
    arr=qrows.get(str(cid))
    if arr is None: return None
    dates,bids,asks=arr
    t=np.datetime64(pd.Timestamp(target).to_datetime64())
    j=int(np.searchsorted(dates,t,side="left"))
    if j>=len(dates) or dates[j]>t+np.timedelta64(5,"D"): return None
    return float(bids[j] if side=="bid" else asks[j])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); signals=u[u.signal & u.dma200.notna()].copy(); con=duckdb.connect()
    raw=load_chains(con,od,signals.date.tolist())
    raw["date"]=pd.to_datetime(raw.date); raw["expiration"]=pd.to_datetime(raw.expiration)
    by_date={d:g for d,g in raw.groupby("date",sort=False)}
    reserve=GATE*CAPITAL
    books={}
    for sd in SHORTS:
        nav=CAPITAL; grounded_until=None; flights=[]
        for _,row in signals.iterrows():
            dt=pd.Timestamp(row.date)
            if grounded_until is not None and dt<=grounded_until: continue
            legs=pick(by_date.get(dt),float(row.close),sd)
            if legs is None: continue
            if legs["debit"]>reserve: continue
            end=min(dt+pd.Timedelta(days=HOLD_MAX),legs["expiry"])
            daily=u[(u.date>dt)&(u.date<=end)]
            exit_date=None; reason="TIME"
            for _,d in daily.iterrows():
                if float(d.high)>=legs["short_k"]:
                    exit_date=pd.Timestamp(d.date); reason="CRASH"; break
            if exit_date is None:
                w=u[(u.date>=dt)&(u.date<=end)]
                if w.empty: continue
                exit_date=pd.Timestamp(w.iloc[-1].date)
            flights.append({"entry":dt,"exit":exit_date,"reason":reason,"legs":legs,"nav_before":nav})
            grounded_until=exit_date+pd.Timedelta(days=GROUND if reason=="CRASH" else COOLDOWN)
        books[sd]=flights
    ids=sorted({z for fl in books.values() for f in fl for z in (f["legs"]["long_id"],f["legs"]["short_id"])})
    starts=min(f["entry"] for fl in books.values() for f in fl)
    ends=max(f["exit"] for fl in books.values() for f in fl)+pd.Timedelta(days=5)
    q=con.execute("""
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS cid,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
    """,[str(od),ids,starts.date(),ends.date()]).df()
    q["date"]=pd.to_datetime(q.date); q["cid"]=q.cid.astype(str)
    q=q.sort_values(["date","cid"]).drop_duplicates(["cid","date"])
    qrows={}
    for cid,grp in q.groupby("cid",sort=False):
        g2=grp.sort_values("date")
        qrows[str(cid)]=(g2.date.to_numpy("datetime64[ns]"),g2.bid.to_numpy(float),g2.ask.to_numpy(float))
    rows=[]; summary=[]
    for sd,fl in books.items():
        nav=CAPITAL; eq=[]
        for f in fl:
            lg=f["legs"]
            lbid=first_quote(qrows,lg["long_id"],f["exit"],"bid")
            sask=first_quote(qrows,lg["short_id"],f["exit"],"ask")
            if lbid is None or sask is None: continue
            pnl=(-lg["debit"])+ (lbid-N*sask)*100.0
            nav+=pnl
            crash=f["reason"]=="CRASH"
            rows.append({"sd":sd,"entry":f["entry"],"exit":f["exit"],"reason":f["reason"],
                         "debit":lg["debit"],"pnl":pnl,"nav":nav,"crash":crash})
            eq.append(nav)
        g=pd.DataFrame([r for r in rows if r["sd"]==sd])
        if g.empty: continue
        peak=g.nav.cummax(); dd=g.nav/peak-1
        summary.append({
            "short_delta":sd,"flights":int(len(g)),"crashes":int(g.crash.sum()),
            "crash_rate":float(g.crash.mean()),"win_rate":float((g.pnl>0).mean()),
            "total_pnl":float(g.pnl.sum()),"nav_end":float(g.nav.iloc[-1]),
            "return_pct":float(g.nav.iloc[-1]/CAPITAL-1),"max_dd":float(dd.min()),
            "worst_pnl":float(g.pnl.min()),"reserve":reserve,
            "crashes_over_reserve":int((g.pnl.abs()>reserve).sum()),
        })
    pd.DataFrame(rows).to_csv(out/"v25_flights.csv",index=False)
    sm=pd.DataFrame(summary); sm.to_csv(out/"v25_summary.csv",index=False)
    report={"status":"REAL_QQQ_CHAIN_AIRLINE_BOOK_V25","capital":CAPITAL,"reserve":reserve,
            "structure":"1x55d long + 2x{3d,5d} short, same expiry, no harvest",
            "data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud)},
            "by_short":sm.to_dict("records"),
            "note":"Airline operations != must-win flights. Thin positive book if reserve holds."}
    (out/"v25_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__": main()
