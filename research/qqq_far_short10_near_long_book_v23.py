#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START=pd.Timestamp("2011-01-01"); END=pd.Timestamp("2025-12-31")
HOLD_MAX=30; COOLDOWN=10; ROLL_DTE=7; N_SHORT=10
PCT_52W=0.98; DMA_EXT=0.08
SHORT_DELTAS=(0.01,0.02,0.05,0.08,0.10)
BUCKETS={"A":(18,25),"B":(25,35)}
SHORT_DTE=(60,120)

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
          AND CAST(date AS DATE)+INTERVAL 120 DAY
    """,[str(opt_path),[pd.Timestamp(d).date() for d in dates]]).df()

def pick_short(g,spot,sd):
    far=g[(g.dte>=SHORT_DTE[0])&(g.dte<=SHORT_DTE[1])&(g.strike>float(spot))].copy()
    if far.empty: return None
    ex=far.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    far=far[far.expiration==ex]
    far["err"]=(far.delta-float(sd)).abs()
    r=far.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    return {"id":str(r.contract_id),"k":float(r.strike),"delta":float(r.delta),
            "bid":float(r.bid),"ask":float(r.ask),"expiry":pd.Timestamp(r.expiration),"dte":int(r.dte)}

def pick_long(g,lo,hi):
    near=g[(g.dte>=lo)&(g.dte<hi)].copy()
    if near.empty: return None
    ex=near.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    near=near[near.expiration==ex]
    atm=near[(near.delta>=0.45)&(near.delta<=0.60)]
    use=atm if not atm.empty else near
    use=use.copy(); use["err"]=(use.delta-0.50).abs()
    r=use.sort_values(["err","volume"],ascending=[True,False]).iloc[0]
    return {"id":str(r.contract_id),"k":float(r.strike),"delta":float(r.delta),
            "bid":float(r.bid),"ask":float(r.ask),"expiry":pd.Timestamp(r.expiration),
            "dte":int(r.dte),"lo":lo,"hi":hi}

def first_quote(qrows,cid,target):
    arr=qrows.get(str(cid))
    if arr is None: return None
    dates,bids,asks=arr
    t=np.datetime64(pd.Timestamp(target).to_datetime64())
    j=int(np.searchsorted(dates,t,side="left"))
    if j>=len(dates) or dates[j] > t+np.timedelta64(5,"D"): return None
    return float(bids[j]), float(asks[j])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); signals=u[u.signal & u.dma200.notna()].copy()
    con=duckdb.connect()
    raw=load_chains(con,od,signals.date.tolist())
    raw["date"]=pd.to_datetime(raw.date); raw["expiration"]=pd.to_datetime(raw.expiration)
    raw["dte"]=(raw.expiration-raw.date).dt.days
    by_date={d:g for d,g in raw.groupby("date",sort=False)}

    plans={}
    for sd in SHORT_DELTAS:
        book={}; cycles=[]; next_allowed=None
        for _,row in signals.iterrows():
            dt=pd.Timestamp(row.date)
            if next_allowed is not None and dt<=next_allowed: continue
            chain=by_date.get(dt)
            if chain is None or chain.empty: continue
            sh=pick_short(chain,float(row.close),sd)
            if sh is None: continue
            actions=[]
            for name,(lo,hi) in BUCKETS.items():
                cur=book.get(name)
                need_buy=False
                if cur is None:
                    need_buy=True
                else:
                    rem=int((cur["expiry"]-dt).days)
                    if rem<ROLL_DTE:
                        actions.append({"kind":"SELL_LONG","bucket":name,"leg":cur,"reason":"ROLL"})
                        need_buy=True
                        book.pop(name,None)
                if need_buy:
                    lg=pick_long(chain,lo,hi)
                    if lg is None: continue
                    lg["bucket"]=name; lg["entry"]=dt
                    book[name]=lg
                    actions.append({"kind":"BUY_LONG","bucket":name,"leg":lg,"reason":"STACK"})
            end=min(dt+pd.Timedelta(days=HOLD_MAX),sh["expiry"])
            daily=u[(u.date>dt)&(u.date<=end)]
            exit_date=None; reason="TIME"
            for _,d in daily.iterrows():
                if float(d.high)>=sh["k"]:
                    exit_date=pd.Timestamp(d.date); reason="SHORT_TOUCH"; break
            if exit_date is None:
                w=u[(u.date>=dt)&(u.date<=end)]
                if w.empty: continue
                exit_date=pd.Timestamp(w.iloc[-1].date)
            cycles.append({"entry":dt,"exit":exit_date,"reason":reason,"short":sh,
                           "actions":actions,"longs":{k:dict(v) for k,v in book.items()}})
            next_allowed=exit_date+pd.Timedelta(days=COOLDOWN)
        plans[sd]=cycles

    ids=sorted({z for cycles in plans.values() for c in cycles
                for z in [c["short"]["id"]]+[lg["id"] for lg in c["longs"].values()]
                +[a["leg"]["id"] for a in c["actions"]]})
    if not ids: raise RuntimeError("no legs")
    starts=min(c["entry"] for cycles in plans.values() for c in cycles)
    ends=max(c["exit"] for cycles in plans.values() for c in cycles)+pd.Timedelta(days=5)
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
        qrows[str(cid)]=(g2.date.to_numpy("datetime64[ns]"), g2.bid.to_numpy(float), g2.ask.to_numpy(float))

    rows=[]
    for sd,cycles in plans.items():
        for c in cycles:
            sh=c["short"]
            sq=first_quote(qrows,sh["id"],c["exit"])
            if sq is None: continue
            short_entry= -N_SHORT*sh["bid"]*100.0
            short_exit= N_SHORT*sq[1]*100.0
            short_pnl= -(short_entry) - short_exit
            long_cash=0.0; buys=0; sells=0
            for act in c["actions"]:
                lg=act["leg"]
                if act["kind"]=="BUY_LONG":
                    long_cash -= lg["ask"]*100.0; buys+=1
                else:
                    px=first_quote(qrows,lg["id"],c["entry"])
                    if px is None: continue
                    long_cash += px[0]*100.0; sells+=1
            pnl=short_pnl+long_cash
            rows.append({
                "sd":float(sd),"entry":c["entry"],"exit":c["exit"],"reason":c["reason"],
                "far_dte":sh["dte"],"far_delta":sh["delta"],"far_bid":sh["bid"],
                "n_longs":len(c["longs"]),"buys":buys,"sells":sells,
                "short_pnl_usd":float(short_pnl),"long_cash_usd":float(long_cash),
                "pnl_usd":float(pnl),"geo_win":c["reason"]!="SHORT_TOUCH",
                "dollar_win":float(pnl)>0,
            })
    trades=pd.DataFrame(rows)
    if trades.empty: raise RuntimeError("no priced cycles")
    trades.to_csv(out/"v23_cycles.csv",index=False)
    summaries=[]
    for sd,g in trades.groupby("sd",sort=True):
        g=g.sort_values("entry")
        summaries.append({
            "short_delta_target":float(sd),"cycles":int(len(g)),
            "geo_no_touch_rate":float(g.geo_win.mean()),
            "dollar_win_rate":float(g.dollar_win.mean()),
            "mean_far_bid":float(g.far_bid.mean()),
            "mean_far_dte":float(g.far_dte.mean()),
            "mean_n_longs":float(g.n_longs.mean()),
            "total_buys":int(g.buys.sum()),"total_sells":int(g.sells.sum()),
            "mean_short_pnl":float(g.short_pnl_usd.mean()),
            "mean_long_cash":float(g.long_cash_usd.mean()),
            "mean_pnl":float(g.pnl_usd.mean()),
            "total_pnl":float(g.pnl_usd.sum()),
            "worst_pnl":float(g.pnl_usd.min()),
            "touch_rate":float((g.reason=="SHORT_TOUCH").mean()),
        })
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/"v23_summary.csv",index=False)
    report={
        "status":"REAL_QQQ_CHAIN_FAR10_NEAR_BOOK_V23",
        "contract":{"n_short":N_SHORT,"far_dte":list(SHORT_DTE),"near_buckets":BUCKETS,
                    "long":"1 ATM per near bucket","gate":"52w>=0.98 AND ext200>=8%",
                    "stack":"buy empty near bucket","release":"sell+replace if DTE<7"},
        "data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud)},
        "diagnostics":{"signals":int(len(signals)),"cycles":int(len(trades))},
        "by_short_delta":summary.to_dict("records"),
    }
    (out/"v23_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__": main()
