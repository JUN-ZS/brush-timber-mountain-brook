#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from dataclasses import dataclass, asdict
from pathlib import Path
import duckdb, numpy as np, pandas as pd

START=pd.Timestamp("2011-01-01"); END=pd.Timestamp("2025-12-31")
N_SHORT=10
SIGNAL_PCT_52W=0.98
SIGNAL_EXT200=0.08
COOLDOWN_DAYS=10
FAR_DTES=(90,120,180)
FAR_DELTAS=(0.05,0.08,0.10)
NEAR_DTES=(7,14,21,30)
LONG_DELTA=0.50
NEAR_TP=0.75
NEAR_MAX_HOLD=30
MAX_STACK=5
REFERENCE_CAPITAL_USD=500000.0/7.8

STRATEGIES=(
    "SIGNAL_50",         # 1 near ATM long at campaign start, release at +50%, repeat only next signal
    "LADDER_2_4_6",      # add at +2/+4/+6% from campaign start; release each at +75%
    "DELTA_COVER",       # add until near-long delta >= 10*far short delta; release profitable excess
    "GAMMA_BURST",       # add on +1.5% day or +3pp far-delta jump; release on +50% book profit
    "PULLBACK_HARVEST",  # add on 1.5% pullbacks from campaign high; release each at +75%
    "TIME_LADDER",       # 3 near expiries; close/replace the shortest layer
)

@dataclass
class Pos:
    entry: pd.Timestamp
    expiry: pd.Timestamp
    cid: str
    strike: float
    delta: float
    cost: float
    target_profit: float
    target_dte: int
    closed: bool=False
    exit: pd.Timestamp|None=None
    exit_price: float|None=None
    pnl: float|None=None

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
    x["signal"]=(x.ratio52>=SIGNAL_PCT_52W)&(x.ext200>=SIGNAL_EXT200)
    x["ret1d"]=x.close.pct_change()
    return x.reset_index(drop=True)

def read_options(con, path, sql, params):
    return con.execute(sql,[str(path),*params]).df()

def pick_far(ch, spot, dte_target, delta_target):
    if ch is None or ch.empty: return None
    g=ch[(ch.strike>float(spot)) & (ch.bid.notna()) & (ch.ask.notna()) & (ch.delta.notna()) & (ch.ask>=ch.bid) & (ch.bid>=0)].copy()
    if g.empty: return None
    g["dte"]=(g.expiration-g.date).dt.days
    g=g[(g.dte>=60)&(g.dte<=210)]
    if g.empty: return None
    # Prefer expiration near requested far tenor, then higher volume.
    exp_score=g.groupby("expiration",as_index=False).agg(dte=("dte","first"), volume=("volume","sum"))
    exp_score["err"]=(exp_score.dte-dte_target).abs()
    ex=exp_score.sort_values(["err","volume"],ascending=[True,False]).iloc[0].expiration
    z=g[g.expiration==ex].copy()
    z["derr"]=(z.delta.abs()-delta_target).abs()
    z=z.sort_values(["derr","volume","strike"],ascending=[True,False,True])
    r=z.iloc[0]
    return {"cid":str(r.contract_id),"strike":float(r.strike),"delta":float(r.delta),
            "expiry":pd.Timestamp(r.expiration),"entry_bid":float(r.bid),"entry_ask":float(r.ask)}

def pick_near(ch, spot, target_dte):
    if ch is None or ch.empty: return None
    g=ch[(ch.strike<=float(spot)*1.02)&(ch.bid.notna())&(ch.ask.notna())&
          (ch.delta.notna())&(ch.ask>=ch.bid)&(ch.bid>=0)].copy()
    if g.empty:return None
    g["dte"]=(g.expiration-g.date).dt.days
    g=g[(g.dte>=7)&(g.dte<=35)]
    if g.empty:return None
    exp_score=g.groupby("expiration",as_index=False).agg(dte=("dte","first"),volume=("volume","sum"))
    exp_score["err"]=(exp_score.dte-target_dte).abs()
    ex=exp_score.sort_values(["err","volume"],ascending=[True,False]).iloc[0].expiration
    z=g[(g.expiration==ex)&(g.strike<=float(spot)*1.01)].copy()
    if z.empty:return None
    z["derr"]=(z.delta.abs()-LONG_DELTA).abs()
    r=z.sort_values(["derr","volume","strike"],ascending=[True,False,True]).iloc[0]
    return {"cid":str(r.contract_id),"strike":float(r.strike),"delta":float(r.delta),
            "expiry":pd.Timestamp(r.expiration),"entry_ask":float(r.ask)}

def build_far_candidates(u, con, opt_path):
    sigdates=[pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(),"date"]]
    if not sigdates:return {}
    ch=read_options(con,opt_path,"""
      SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id, CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume, CAST(delta AS DOUBLE) AS delta
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND UPPER("type")='CALL' AND delta IS NOT NULL
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 60 DAY
                                          AND CAST(date AS DATE)+INTERVAL 210 DAY
    """,[ [d.date() for d in sigdates] ])
    if ch.empty:return {}
    ch["date"]=pd.to_datetime(ch.date); ch["expiration"]=pd.to_datetime(ch.expiration)
    out={}
    for d,g in ch.groupby("date",sort=False):
        out[d]={}
        spot=float(u.loc[u.date==d,"close"].iloc[0])
        for fd in FAR_DTES:
            for delta in FAR_DELTAS:
                r=pick_far(g,spot,fd,delta)
                out[d][(fd,delta)]=r
    return out

def choose_campaigns(u, far_candidates, far_dte, far_delta):
    rows=[]
    active_until=None
    for _,ur in u.loc[u.signal & u.dma200.notna()].iterrows():
        d=pd.Timestamp(ur.date)
        if active_until is not None and d<=active_until: continue
        leg=far_candidates.get(d,{}).get((far_dte,far_delta))
        if not leg: continue
        rows.append({"entry":d,"far":leg,"start_spot":float(ur.close)})
        # provisional; exact end will be found from quotes/underlying in simulate
        active_until=d+pd.Timedelta(days=5)
    return rows

def get_quotes(con,opt_path,ids,with_delta=False):
    if not ids:return pd.DataFrame()
    cols="CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask"
    if with_delta: cols += ", CAST(delta AS DOUBLE) AS delta"
    q=read_options(con,opt_path,f"""
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS cid,
             {cols}
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
    """,[list(map(str,ids))])
    q["date"]=pd.to_datetime(q.date); q["cid"]=q.cid.astype(str)
    return q.sort_values(["cid","date"]).drop_duplicates(["cid","date"])

def far_quote_maps(q):
    out={}
    for cid,g in q.groupby("cid",sort=False):
        gg=g.set_index("date").sort_index()
        out[cid]=gg
    return out

def event_dates_for_strategy(strategy,camp,far_daily,u):
    d0=camp["entry"]; end=camp["end"]
    sub=u[(u.date>=d0)&(u.date<=end)].copy()
    if sub.empty:return []
    events=[]
    if strategy in ("SIGNAL_50","LADDER_2_4_6","DELTA_COVER","GAMMA_BURST","PULLBACK_HARVEST","TIME_LADDER"):
        events.append((d0,21))
    if strategy=="LADDER_2_4_6":
        start=float(sub.iloc[0].close)
        for pct in (0.02,0.04,0.06):
            hit=sub[sub.close>=start*(1+pct)]
            if not hit.empty: events.append((pd.Timestamp(hit.iloc[0].date),21))
    elif strategy=="DELTA_COVER":
        prev_req=1
        for _,r in sub.iterrows():
            fq=far_daily.loc[far_daily.index<=r.date]
            if fq.empty or pd.isna(fq.iloc[-1].delta): continue
            sd=abs(float(fq.iloc[-1].delta))
            req=max(1,min(MAX_STACK,int(math.ceil((N_SHORT*sd)/LONG_DELTA))))
            if req>prev_req:
                events.append((pd.Timestamp(r.date),21))
                prev_req=req
    elif strategy=="GAMMA_BURST":
        sub["ddelta"]=far_daily.reindex(sub.date).delta.diff()
        for _,r in sub.iterrows():
            if pd.isna(r.ret1d):continue
            dd=float(r.ddelta) if pd.notna(r.ddelta) else 0.0
            if float(r.ret1d)>=0.015 or dd>=0.03:
                events.append((pd.Timestamp(r.date),21))
    elif strategy=="PULLBACK_HARVEST":
        hi=-np.inf; last=None
        for _,r in sub.iterrows():
            hi=max(hi,float(r.close))
            if float(r.close)<=hi*0.985:
                if last is None or (r.date-last).days>=3:
                    events.append((pd.Timestamp(r.date),14))
                    last=pd.Timestamp(r.date)
    elif strategy=="TIME_LADDER":
        events=[(d0,7),(d0,14),(d0,21)]
    # stable, unique, sorted
    seen=set(); out=[]
    for e,t in sorted(events):
        k=(pd.Timestamp(e),int(t))
        if k not in seen:
            out.append(k); seen.add(k)
    return out

def simulate_strategy(u,far_candidates,near_chains,near_quotes_by_cid,far_dte,far_delta,strategy):
    # Build sequential campaigns based on signal, no overlap.
    sigs=u[u.signal & u.dma200.notna()]
    results=[]
    next_allowed=None
    for _,sr in sigs.iterrows():
        d0=pd.Timestamp(sr.date)
        if next_allowed is not None and d0<=next_allowed: continue
        far=far_candidates.get(d0,{}).get((far_dte,far_delta))
        if not far: continue
        far_cid=far["cid"]; far_strike=far["strike"]; far_exp=far["expiry"]
        fq=far_quotes.get(far_cid)
        if fq is None or fq.empty: continue
        # Campaign ends on first post-entry touch, 10 calendar days after close, or expiry.
        end=min(far_exp,d0+pd.Timedelta(days=365))
        subu=u[(u.date>d0)&(u.date<=end)].copy()
        touch=subu[subu.high>=far_strike]
        if not touch.empty:
            end=pd.Timestamp(touch.iloc[0].date); far_reason="SHORT_TOUCH"
        else:
            far_reason="EXPIRY"
        # Require an executable far close quote; use first quote at/after intended end up to 5 days.
        fq_after=fq.loc[fq.index>=end]
        if fq_after.empty: continue
        far_exit_date=pd.Timestamp(fq_after.index[0])
        if (far_exit_date-end).days>5: continue
        far_exit_ask=float(fq_after.iloc[0].ask)
        far_entry_bid=float(far.get("entry_bid",0.0))
        far_pnl=(far_entry_bid-N_SHORT*far_exit_ask)*100.0
        # strategy event schedule
        fqd=fq.copy()
        fqd.index=pd.to_datetime(fqd.index)
        fqd=fqd.reindex(subu.date).ffill()
        evs=event_dates_for_strategy(strategy,{"entry":d0,"end":end},fqd,u)
        # near contracts selected on event dates
        positions=[]; trades=[]; cash=far_entry_bid*N_SHORT*100.0
        used_ids=set()
        # daily loop through campaign
        days=pd.date_range(d0,end,freq="D")
        peak_equity=equity= cash
        eq_rows=[]
        for dt in days:
            if dt not in set(subu.date): continue
            spot=float(u.loc[u.date==dt,"close"].iloc[0])
            dayrow=u.loc[u.date==dt].iloc[0]
            # Opens
            for ed,target_dte in evs:
                if pd.Timestamp(ed)!=dt: continue
                if strategy=="SIGNAL_50":
                    if dt!=d0 or positions: continue
                add_count=1
                if strategy=="DELTA_COVER":
                    sd=abs(float(fqd.loc[dt,"delta"])) if dt in fqd.index and pd.notna(fqd.loc[dt,"delta"]) else 0.0
                    required=max(1,min(MAX_STACK,int(math.ceil((N_SHORT*sd)/LONG_DELTA))))
                    add_count=max(0,required-len([p for p in positions if not p.closed]))
                elif strategy=="TIME_LADDER":
                    add_count=1
                else:
                    if len([p for p in positions if not p.closed])>=MAX_STACK: continue
                for _ in range(add_count):
                    chain=near_chains.get(dt)
                    leg=pick_near(chain,spot,int(target_dte)) if chain is not None else None
                    if not leg: continue
                    if leg["cid"] in used_ids and strategy!="TIME_LADDER": continue
                    q=near_quotes_by_cid.get(leg["cid"])
                    if q is None or dt not in q.index: continue
                    ask=float(q.loc[dt,"ask"])
                    p=Pos(entry=dt,expiry=leg["expiry"],cid=leg["cid"],strike=leg["strike"],delta=leg["delta"],
                          cost=ask,target_profit=NEAR_TP,target_dte=int(target_dte))
                    positions.append(p); used_ids.add(p.cid); cash-=ask*100.0
            # Close rules / expiry
            active=[p for p in positions if not p.closed]
            for p in active:
                q=near_quotes_by_cid.get(p.cid)
                if q is None: continue
                # first same-day quote
                if dt not in q.index: continue
                bid=float(q.loc[dt,"bid"])
                dte=max(0,(p.expiry-dt).days)
                ret=bid/p.cost-1.0 if p.cost>0 else -1.0
                close=False
                if ret>=p.target_profit or dte<=2 or dt>=p.expiry or dt>=d0+pd.Timedelta(days=NEAR_MAX_HOLD):
                    close=True
                # DELTA_COVER: release a profitable excess layer when coverage >1.5
                if strategy=="DELTA_COVER" and ret>0:
                    sd=abs(float(fqd.loc[dt,"delta"])) if dt in fqd.index and pd.notna(fqd.loc[dt,"delta"]) else 0.0
                    active_count=len([x for x in positions if not x.closed])
                    coverage=(active_count*LONG_DELTA)/(max(1e-9,N_SHORT*sd))
                    if coverage>1.5: close=True
                if close:
                    p.closed=True; p.exit=dt; p.exit_price=bid; p.pnl=(bid-p.cost)*100.0
                    cash+=bid*100.0; trades.append(p)
            # GAMMA_BURST: book harvest after +50% of long cost, but only on a strong pullback day
            if strategy=="GAMMA_BURST":
                act=[p for p in positions if not p.closed]
                if act:
                    mkt=sum((float(near_quotes_by_cid[p.cid].loc[dt,"bid"])*100.0 if p.cid in near_quotes_by_cid and dt in near_quotes_by_cid[p.cid].index else p.cost*100.0) for p in act)
                    cost=sum(p.cost*100.0 for p in act)
                    ret=(mkt-cost)/cost if cost>0 else 0.0
                    if ret>=0.50 and float(dayrow.ret1d)<=-0.005:
                        for p in act:
                            q=near_quotes_by_cid.get(p.cid)
                            if q is not None and dt in q.index:
                                bid=float(q.loc[dt,"bid"]); p.closed=True; p.exit=dt; p.exit_price=bid; p.pnl=(bid-p.cost)*100.0
                                cash+=bid*100.0; trades.append(p)
            # Equity mark
            liq=cash
            for p in positions:
                if not p.closed:
                    q=near_quotes_by_cid.get(p.cid)
                    if q is not None and dt in q.index:
                        liq+=float(q.loc[dt,"bid"])*100.0
                    else:
                        liq+=0.0
            # far liability marked at ask
            if dt>=d0 and dt<=far_exit_date and dt in fq.index:
                liq-=N_SHORT*float(fq.loc[dt,"ask"])*100.0
            eq_rows.append((dt,liq))
            peak_equity=max(peak_equity,liq)
        # Force-close remaining near longs at far_exit_date (or last quote prior)
        for p in [x for x in positions if not x.closed]:
            q=near_quotes_by_cid.get(p.cid)
            if q is None: continue
            avail=q.loc[q.index>=far_exit_date]
            if avail.empty: avail=q.loc[q.index<=far_exit_date]
            if avail.empty: continue
            dt2=pd.Timestamp(avail.index[0] if avail.index[0]>=far_exit_date else avail.index[-1])
            bid=float(avail.iloc[0 if avail.index[0]>=far_exit_date else -1].bid)
            p.closed=True; p.exit=dt2; p.exit_price=bid; p.pnl=(bid-p.cost)*100.0
            cash+=bid*100.0; trades.append(p)
        total_pnl=far_pnl+sum(t.pnl or 0.0 for t in trades)
        # Approximate campaign equity including far + near; compute DD from recorded marks.
        eq=pd.DataFrame(eq_rows,columns=["date","equity"]).drop_duplicates("date")
        if not eq.empty:
            eq["nav"]=REFERENCE_CAPITAL_USD+eq.equity
            eq["drawdown"]=eq.nav/eq.nav.cummax()-1.0
            maxdd=float(eq.drawdown.min())
        else:maxdd=float("nan")
        results.append({
            "campaign_entry":d0,"campaign_far_expiry":far_exp,"far_exit":far_exit_date,"far_reason":far_reason,
            "far_dte_target":far_dte,"far_delta_target":far_delta,"far_strike":far_strike,
            "far_entry_premium_usd":far_entry_bid*N_SHORT*100.0,
            "far_pnl_usd":far_pnl,"near_trades":len(trades),
            "near_realized_pnl_usd":float(sum(t.pnl or 0.0 for t in trades)),
            "total_pnl_usd":float(total_pnl),"maxdd":maxdd,
            "long_wins":int(sum(1 for t in trades if (t.pnl or 0)>0)),
            "long_losses":int(sum(1 for t in trades if (t.pnl or 0)<=0)),
            "long_win_rate":float(sum(1 for t in trades if (t.pnl or 0)>0)/len(trades)) if trades else np.nan,
            "longest_stack":int(max([sum(1 for p in positions if not p.closed or (p.entry<=d and p.exit and p.exit>=d)) for d in pd.date_range(d0,far_exit_date,freq="D")] or [0])),
        })
        next_allowed=far_exit_date+pd.Timedelta(days=COOLDOWN_DAYS)
    return pd.DataFrame(results)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    od=Path(a.data_dir)/"QQQ_options.parquet"; ud=Path(a.data_dir)/"QQQ_underlying.parquet"
    u=load_underlying(ud); con=duckdb.connect()
    far_candidates=build_far_candidates(u,con,od)
    # Gather candidate near-entry dates conservatively from every signal date and each far config.
    event_dates=set(pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(),"date"])
    for fd in FAR_DTES:
        for fdel in FAR_DELTAS:
            for d,legs in far_candidates.items():
                if (fd,fdel) not in legs or not legs[(fd,fdel)]: continue
                end=min(legs[(fd,fdel)]["expiry"],d+pd.Timedelta(days=365))
                sub=u[(u.date>d)&(u.date<=end)]
                # Prefetch every active campaign date so state-dependent rules
                # can select a same-day near contract without look-ahead.
                event_dates.update(pd.Timestamp(x) for x in sub["date"])
                # Daily pullback / burst triggers are still derived from this history.
                hi=-np.inf
                for _,r in sub.iterrows():
                    hi=max(hi,float(r.close))
                    if float(r.close)<=hi*0.985:event_dates.add(pd.Timestamp(r.date))
    event_dates=sorted(event_dates)
    near=read_options(con,od,"""
      SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id, CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume, CAST(delta AS DOUBLE) AS delta
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND UPPER("type")='CALL' AND delta IS NOT NULL
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 7 DAY
                                          AND CAST(date AS DATE)+INTERVAL 35 DAY
    """,[ [d.date() for d in event_dates] ])
    near["date"]=pd.to_datetime(near.date); near["expiration"]=pd.to_datetime(near.expiration)
    near_chains={d:g for d,g in near.groupby("date",sort=False)}
    # All potential near IDs + far IDs, then fetch quotes across history.
    near_ids=set()
    for d,ch in near_chains.items():
        spot=float(u.loc[u.date==d,"close"].iloc[0])
        for td in NEAR_DTES:
            leg=pick_near(ch,spot,td)
            if leg: near_ids.add(leg["cid"])
    far_ids=set()
    for legs in far_candidates.values():
        for leg in legs.values():
            if leg: far_ids.add(leg["cid"])
    fq=get_quotes(con,od,far_ids,with_delta=True)
    global far_quotes
    far_quotes=far_quote_maps(fq)
    nq=get_quotes(con,od,near_ids,with_delta=False)
    near_quotes_by_cid=far_quote_maps(nq)
    all_rows=[]; by_strategy=[]
    for fd in FAR_DTES:
      for fdel in FAR_DELTAS:
        for strategy in STRATEGIES:
            # Global near candidates and quotes are fixed, no hindsight.
            df=simulate_strategy(u,far_candidates,near_chains,near_quotes_by_cid,fd,fdel,strategy)
            if df.empty: continue
            df["strategy"]=strategy
            all_rows.append(df)
            by_strategy.append({
              "strategy":strategy,"far_dte_target":fd,"far_delta_target":fdel,
              "campaigns":int(len(df)),"total_pnl_usd":float(df.total_pnl_usd.sum()),
              "avg_campaign_pnl_usd":float(df.total_pnl_usd.mean()),
              "median_campaign_pnl_usd":float(df.total_pnl_usd.median()),
              "far_pnl_usd":float(df.far_pnl_usd.sum()),
              "near_realized_pnl_usd":float(df.near_realized_pnl_usd.sum()),
              "near_trade_count":int(df.near_trades.sum()),
              "near_win_rate":float(df.long_wins.sum()/max(1,(df.long_wins+df.long_losses).sum())),
              "worst_campaign_pnl_usd":float(df.total_pnl_usd.min()),
              "mean_campaign_maxdd":float(df.maxdd.mean()),
              "worst_campaign_maxdd":float(df.maxdd.min()),
            })
    if not all_rows: raise RuntimeError("No strategy results")
    detail=pd.concat(all_rows,ignore_index=True)
    summary=pd.DataFrame(by_strategy)
    summary=summary.sort_values(["total_pnl_usd","near_win_rate"],ascending=[False,False]).reset_index(drop=True)
    detail.to_csv(out/"v21_dynamic_harvest_detail.csv",index=False)
    summary.to_csv(out/"v21_dynamic_harvest_summary.csv",index=False)
    report={
      "status":"REAL_QQQ_CHAIN_DYNAMIC_NEAR_LONG_HARVEST",
      "definitions":{
        "far_position":"10 x short call, far tenor target 90/120/180 DTE, delta target 5/8/10%, opened only at the same extreme-high signal used in V20",
        "near_position":"near call selected from the live chain closest to 50 delta and requested 7/14/21/30 DTE, bought at Ask and released at Bid",
        "campaign_end":"first underlying High touch of far short strike, otherwise far expiry; executable far close uses first available Ask within 5 calendar days",
        "no_lookahead":"all triggers use bars and quotes available on or before the management date"
      },
      "data":{"options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud),
              "underlying_range":[str(u.date.min().date()),str(u.date.max().date())],
              "signal_count":int(u.signal.sum()),"near_event_date_count":len(event_dates)},
      "matrix":{"strategies":list(STRATEGIES),"far_dtes":list(FAR_DTES),"far_deltas":list(FAR_DELTAS),
                "near_dtes":list(NEAR_DTES),"long_delta_target":LONG_DELTA,"near_take_profit":NEAR_TP},
      "top10":summary.head(10).to_dict("records")
    }
    (out/"v21_dynamic_harvest_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__":main()
