#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START=pd.Timestamp("2011-01-01"); END=pd.Timestamp("2025-12-31")
N_SHORT=10; MAX_Q=15; COVER_LO=1.0; COVER_HI=2.0; COOLDOWN=10
SHORT_CLOSE_DTE=30; PCT_52W=0.98; DMA_EXT=0.08
SHORT_DELTAS=(0.02,0.05,0.08)
NEAR_DTE=(14,21)

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
    if not dates: return pd.DataFrame()
    return con.execute("""
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume,
             CAST(delta AS DOUBLE) AS delta
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND UPPER("type")='CALL'
        AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN
          CAST(date AS DATE)+INTERVAL 7 DAY
          AND CAST(date AS DATE)+INTERVAL 120 DAY
    """,[str(opt_path),[pd.Timestamp(d).date() for d in dates]]).df()

def pick_far_short(g,spot,sd):
    far=g[(g.dte>=60)&(g.dte<=120)&(g.strike>float(spot))].copy()
    if far.empty: return None
    ex=far.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    far=far[far.expiration==ex]
    far["err"]=(far.delta-float(sd)).abs()
    r=far.sort_values(["err","volume","strike"],ascending=[True,False,True]).iloc[0]
    return {"id":str(r.contract_id),"k":float(r.strike),"delta":float(r.delta),
            "bid":float(r.bid),"ask":float(r.ask),"expiry":pd.Timestamp(r.expiration),"dte":int(r.dte)}

def pick_near_atm(g):
    near=g[(g.dte>=NEAR_DTE[0])&(g.dte<=NEAR_DTE[1])].copy()
    if near.empty: return None
    ex=near.sort_values(["dte","volume"],ascending=[True,False]).iloc[0].expiration
    near=near[near.expiration==ex]
    atm=near[(near.delta>=0.45)&(near.delta<=0.60)]
    use=atm if not atm.empty else near
    use=use.copy(); use["err"]=(use.delta-0.50).abs()
    r=use.sort_values(["err","volume"],ascending=[True,False]).iloc[0]
    return {"id":str(r.contract_id),"k":float(r.strike),"delta":float(r.delta),
            "bid":float(r.bid),"ask":float(r.ask),"expiry":pd.Timestamp(r.expiration),"dte":int(r.dte)}

def first_px(qrows,cid,target,side):
    arr=qrows.get(str(cid))
    if arr is None: return None
    dates,bids,asks,deltas=arr
    t=np.datetime64(pd.Timestamp(target).to_datetime64())
    j=int(np.searchsorted(dates,t,side="left"))
    if j>=len(dates) or dates[j] > t+np.timedelta64(5,"D"): return None
    px=float(bids[j] if side=="bid" else asks[j])
    return px, float(deltas[j]), pd.Timestamp(dates[j])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); signals=u[u.signal & u.dma200.notna()].copy()
    sig_set=set(pd.to_datetime(signals.date).dt.normalize())
    con=duckdb.connect()
    raw=load_chains(con,od,signals.date.tolist())
    raw["date"]=pd.to_datetime(raw.date); raw["expiration"]=pd.to_datetime(raw.expiration)
    raw["dte"]=(raw.expiration-raw.date).dt.days
    by_date={d:g for d,g in raw.groupby("date",sort=False)}

    books=[]
    for sd in SHORT_DELTAS:
        next_allowed=None
        for _,row in signals.iterrows():
            dt=pd.Timestamp(row.date)
            if next_allowed is not None and dt<=next_allowed: continue
            chain=by_date.get(dt)
            if chain is None or chain.empty: continue
            sh=pick_far_short(chain,float(row.close),sd)
            if sh is None: continue
            close_by=min(sh["expiry"]-pd.Timedelta(days=SHORT_CLOSE_DTE), sh["expiry"])
            daily=u[(u.date>dt)&(u.date<=close_by)]
            exit_date=None; reason="DTE"
            for _,d in daily.iterrows():
                if float(d.high)>=sh["k"]:
                    exit_date=pd.Timestamp(d.date); reason="SHORT_TOUCH"; break
            if exit_date is None:
                w=u[(u.date>=dt)&(u.date<=close_by)]
                if w.empty: continue
                exit_date=pd.Timestamp(w.iloc[-1].date)
            rebals=[pd.Timestamp(x) for x in signals.date if dt<=pd.Timestamp(x)<=exit_date]
            books.append({"sd":sd,"entry":dt,"exit":exit_date,"reason":reason,"short":sh,"rebals":rebals})
            next_allowed=exit_date+pd.Timedelta(days=COOLDOWN)

    extra=sorted({d for b in books for d in b["rebals"]})
    extra_need=[d for d in extra if d not in by_date]
    if extra_need:
        more=load_chains(con,od,extra_need)
        if not more.empty:
            more["date"]=pd.to_datetime(more.date); more["expiration"]=pd.to_datetime(more.expiration)
            more["dte"]=(more.expiration-more.date).dt.days
            for d,g in more.groupby("date",sort=False):
                by_date[d]=g

    # first pass longs to collect ids
    planned=[]
    for b in books:
        longs=[]
        events=[]
        for rd in b["rebals"]:
            chain=by_date.get(rd)
            if chain is None or chain.empty: continue
            # drop expired longs
            keep=[]
            for lg in longs:
                if lg["expiry"]<=rd:
                    events.append({"date":rd,"kind":"EXPIRE_LONG","leg":lg})
                else:
                    keep.append(lg)
            longs=keep
            row=chain.iloc[0]
            # far delta that day if present else entry delta
            far_d=b["short"]["delta"]
            far_row=chain[chain.contract_id.astype(str)==b["short"]["id"]]
            if not far_row.empty:
                far_d=float(far_row.iloc[0].delta)
            long_exp=sum(abs(float(lg.get("delta",0.5))) for lg in longs)
            den=max(N_SHORT*abs(far_d),1e-6)
            cov=long_exp/den
            if cov<COVER_LO and len(longs)<MAX_Q:
                lg=pick_near_atm(chain)
                if lg is not None:
                    lg["bought"]=rd; longs.append(lg)
                    events.append({"date":rd,"kind":"STACK","leg":lg,"cov_before":cov})
            elif cov>COVER_HI and longs:
                lg=longs.pop(0)
                events.append({"date":rd,"kind":"HARVEST","leg":lg,"cov_before":cov})
        planned.append({**b,"events":events,"final_longs":longs})

    ids=sorted({z for p in planned for z in [p["short"]["id"]]
                +[e["leg"]["id"] for e in p["events"]]
                +[lg["id"] for lg in p["final_longs"]]})
    if not ids: raise RuntimeError("no ids")
    starts=min(p["entry"] for p in planned); ends=max(p["exit"] for p in planned)+pd.Timedelta(days=5)
    q=con.execute("""
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS cid,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             CAST(delta AS DOUBLE) AS delta
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
        qrows[str(cid)]=(g2.date.to_numpy("datetime64[ns]"), g2.bid.to_numpy(float),
                         g2.ask.to_numpy(float), g2.delta.fillna(0).to_numpy(float))

    rows=[]; evrows=[]
    for p in planned:
        sh=p["short"]
        sq=first_px(qrows,sh["id"],p["exit"],"ask")
        if sq is None: continue
        cash= N_SHORT*sh["bid"]*100.0
        cash-= N_SHORT*sq[0]*100.0
        stacks=harvs=exp=0; harvested_pnl=0.0; q_peak=0; q_now=0
        live=[]
        for e in p["events"]:
            lg=e["leg"]
            if e["kind"]=="STACK":
                cash-=lg["ask"]*100.0; stacks+=1; q_now+=1; q_peak=max(q_peak,q_now)
                live.append(lg)
            elif e["kind"]=="HARVEST":
                px=first_px(qrows,lg["id"],e["date"],"bid")
                if px is None: continue
                pnl=px[0]*100.0-lg["ask"]*100.0
                cash+=px[0]*100.0; harvs+=1; harvested_pnl+=pnl; q_now=max(0,q_now-1)
                evrows.append({"sd":p["sd"],"date":e["date"],"kind":"HARVEST","pnl":pnl})
            else:
                exp+=1; q_now=max(0,q_now-1)
        leftover=0.0
        for lg in p["final_longs"]:
            px=first_px(qrows,lg["id"],p["exit"],"bid")
            if px is None: continue
            leftover+=px[0]*100.0; cash+=px[0]*100.0
        rows.append({
            "sd":float(p["sd"]),"entry":p["entry"],"exit":p["exit"],"reason":p["reason"],
            "far_dte":sh["dte"],"far_delta0":sh["delta"],"far_bid":sh["bid"],
            "stacks":int(stacks),"harvests":int(harvs),"expires":int(exp),
            "q_peak":int(q_peak),"q_end":int(len(p["final_longs"])),
            "harvested_pnl":float(harvested_pnl),"leftover_mark":float(leftover),
            "pnl_usd":float(cash),"geo_win":p["reason"]!="SHORT_TOUCH",
            "dollar_win":float(cash)>0,
            "singularity":int(harvs>0 and len(p["final_longs"])==0 and p["reason"]=="SHORT_TOUCH"),
        })
    trades=pd.DataFrame(rows)
    if trades.empty: raise RuntimeError("no priced books")
    trades.to_csv(out/"v24_books.csv",index=False)
    summaries=[]
    for sd,g in trades.groupby("sd",sort=True):
        summaries.append({
            "short_delta_target":float(sd),"books":int(len(g)),
            "geo_no_touch_rate":float(g.geo_win.mean()),
            "dollar_win_rate":float(g.dollar_win.mean()),
            "mean_far_bid":float(g.far_bid.mean()),
            "mean_stacks":float(g.stacks.mean()),"mean_harvests":float(g.harvests.mean()),
            "mean_q_peak":float(g.q_peak.mean()),"mean_q_end":float(g.q_end.mean()),
            "mean_harvested_pnl":float(g.harvested_pnl.mean()),
            "total_pnl":float(g.pnl_usd.sum()),"worst_pnl":float(g.pnl_usd.min()),
            "touch_rate":float((g.reason=="SHORT_TOUCH").mean()),
            "singularity_books":int(g.singularity.sum()),
        })
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/"v24_summary.csv",index=False)
    report={
        "status":"REAL_QQQ_CHAIN_FAR10_COVERAGE_V24",
        "question":"Can harvested near gamma feed 10 persistent far shorts?",
        "coverage_band":[COVER_LO,COVER_HI],"n_short":N_SHORT,"max_q":MAX_Q,
        "near_dte":list(NEAR_DTE),"short_dte":[60,120],
        "data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud)},
        "diagnostics":{"signals":int(len(signals)),"books":int(len(trades))},
        "by_short_delta":summary.to_dict("records"),
        "not_v23":"V23 used fixed 1-per-bucket; V24 uses Coverage_t",
    }
    (out/"v24_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__": main()
