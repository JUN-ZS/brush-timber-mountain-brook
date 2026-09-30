#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

START = pd.Timestamp("2011-01-01")
END = pd.Timestamp("2025-12-31")
REFERENCE_CAPITAL_USD = 500000.0 / 7.8

N_SHORT = 10
SIGNAL_PCT_52W = 0.98
SIGNAL_EXT200 = 0.08
COOLDOWN_DAYS = 10

FAR_DTES = (90, 120, 180)
FAR_DELTAS = (0.05, 0.08, 0.10)
NEAR_DTES = (7, 14, 21, 30)
NEAR_DELTA = 0.50
MAX_NEAR_QTY = 12

DISTANCE_BANDS = (0.08, 0.06, 0.04, 0.02)
DELTA_BANDS = (0.05, 0.08, 0.12)
GAMMA_RATIO_BANDS = (1.5, 2.5)
DELTA_JUMP_BANDS = (0.02, 0.04)

STRATEGIES = (
    "DAILY_TARGET_TP75",
    "SHOCK_ADD_TP75",
    "BAND_STEP_HARVEST",
    "TRAIL_RELOAD",
    "PARTIAL_HARVEST",
    "TIME_ROLL_TARGET",
    "PULLBACK_RELOAD",
    "ASYMMETRIC_TP100",
)

@dataclass
class NearPos:
    entry: pd.Timestamp
    expiry: pd.Timestamp
    cid: str
    strike: float
    entry_ask: float
    target_dte: int
    peak_bid: float = 0.0
    closed: bool = False
    exit: pd.Timestamp | None = None
    exit_bid: float | None = None
    pnl: float | None = None
    close_reason: str | None = None

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_underlying(path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path)
    x.columns = [c.lower() for c in x.columns]
    x["date"] = pd.to_datetime(x["date"]).dt.tz_localize(None).dt.normalize()
    x = x.sort_values("date").drop_duplicates("date")
    x = x[(x.date >= START) & (x.date <= END)].copy()
    x["dma200"] = x.close.rolling(200, min_periods=200).mean()
    x["high52w"] = x.close.rolling(252, min_periods=252).max()
    x["ext200"] = x.close / x.dma200 - 1.0
    x["ratio52"] = x.close / x.high52w
    x["signal"] = (x.ratio52 >= SIGNAL_PCT_52W) & (x.ext200 >= SIGNAL_EXT200)
    x["ret1d"] = x.close.pct_change()
    return x.reset_index(drop=True)

def option_columns(con, path: Path) -> set[str]:
    return {str(r[0]).lower() for r in con.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]
    ).fetchall()}

def read_options(con, path: Path, sql: str, params: list) -> pd.DataFrame:
    return con.execute(sql, [str(path), *params]).df()

def pick_far(chain: pd.DataFrame, spot: float, dte_target: int, delta_target: float):
    if chain is None or chain.empty:
        return None
    g = chain[
        (chain.strike > float(spot))
        & chain.bid.notna() & chain.ask.notna()
        & chain.delta.notna()
        & (chain.ask >= chain.bid) & (chain.bid >= 0)
    ].copy()
    if g.empty:
        return None
    g["dte"] = (g.expiration - g.date).dt.days
    g = g[(g.dte >= 60) & (g.dte <= 210)]
    if g.empty:
        return None
    exp_score = g.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"), volume=("volume", "sum")
    )
    exp_score["err"] = (exp_score.dte - dte_target).abs()
    ex = exp_score.sort_values(["err", "volume"], ascending=[True, False]).iloc[0].expiration
    z = g[g.expiration == ex].copy()
    z["derr"] = (z.delta.abs() - delta_target).abs()
    r = z.sort_values(["derr", "volume", "strike"], ascending=[True, False, True]).iloc[0]
    return {
        "cid": str(r.contract_id), "strike": float(r.strike), "delta": float(r.delta),
        "expiry": pd.Timestamp(r.expiration), "entry_bid": float(r.bid), "entry_ask": float(r.ask)
    }

def pick_near(chain: pd.DataFrame, spot: float, target_dte: int):
    if chain is None or chain.empty:
        return None
    g = chain[
        (chain.strike <= float(spot) * 1.02)
        & chain.bid.notna() & chain.ask.notna()
        & chain.delta.notna()
        & (chain.ask >= chain.bid) & (chain.bid >= 0)
    ].copy()
    if g.empty:
        return None
    g["dte"] = (g.expiration - g.date).dt.days
    g = g[(g.dte >= 7) & (g.dte <= 35)]
    if g.empty:
        return None
    exp_score = g.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"), volume=("volume", "sum")
    )
    exp_score["err"] = (exp_score.dte - target_dte).abs()
    ex = exp_score.sort_values(["err", "volume"], ascending=[True, False]).iloc[0].expiration
    z = g[(g.expiration == ex) & (g.strike <= float(spot) * 1.01)].copy()
    if z.empty:
        return None
    z["derr"] = (z.delta.abs() - NEAR_DELTA).abs()
    r = z.sort_values(["derr", "volume", "strike"], ascending=[True, False, True]).iloc[0]
    return {
        "cid": str(r.contract_id), "strike": float(r.strike),
        "delta": float(r.delta), "expiry": pd.Timestamp(r.expiration)
    }

def load_far_candidates(u, con, opt_path):
    sigdates = [pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(), "date"]]
    if not sigdates:
        return {}
    ch = read_options(con, opt_path, """
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
    """, [[d.date() for d in sigdates]])
    if ch.empty:
        return {}
    ch["date"] = pd.to_datetime(ch.date); ch["expiration"] = pd.to_datetime(ch.expiration)
    out = {}
    for d, g in ch.groupby("date", sort=False):
        out[d] = {}
        spot = float(u.loc[u.date == d, "close"].iloc[0])
        for fd in FAR_DTES:
            for fdel in FAR_DELTAS:
                out[d][(fd, fdel)] = pick_far(g, spot, fd, fdel)
    return out

def get_quotes(con, opt_path, ids, include_gamma=False):
    if not ids:
        return {}
    gamma_sql = ", CAST(gamma AS DOUBLE) AS gamma" if include_gamma else ""
    q = con.execute(f"""
        SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS cid,
               CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
               CAST(delta AS DOUBLE) AS delta {gamma_sql}
        FROM read_parquet(?)
        WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
          AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND bid>=0
    """, [str(opt_path), list(map(str, ids))]).df()
    q["date"] = pd.to_datetime(q.date); q["cid"] = q.cid.astype(str)
    return {str(cid): g.sort_values("date").drop_duplicates("date").set_index("date")
            for cid, g in q.groupby("cid", sort=False)}

def add_gamma_measure(far_quotes: dict, u: pd.DataFrame, has_gamma: bool):
    spot = u.set_index("date")["close"]
    for cid, q0 in far_quotes.items():
        q = q0.copy()
        q["spot"] = q.index.map(spot)
        ds = q["delta"].diff()
        dp = q["spot"].diff()
        proxy = (ds / dp.replace(0, np.nan)).abs()
        if has_gamma:
            actual = pd.to_numeric(q["gamma"], errors="coerce").abs()
            q["gamma_used"] = actual.fillna(proxy)
            source = "ACTUAL_GAMMA_WITH_PROXY_FALLBACK"
        else:
            q["gamma_used"] = proxy
            source = "DELTA_SPOT_GAMMA_PROXY"
        q["gamma_base"] = q["gamma_used"].shift(1).rolling(20, min_periods=5).median()
        q["gamma_ratio"] = q["gamma_used"] / q["gamma_base"].replace(0, np.nan)
        q["delta_jump"] = q["delta"].diff()
        q["gamma_source"] = source
        far_quotes[cid] = q

def state_from_far(qrow, spot, strike):
    fd = abs(float(qrow.delta)) if pd.notna(qrow.delta) else 0.0
    distance = (float(strike) - float(spot)) / float(spot)
    db = 0 if fd < 0.05 else (1 if fd < 0.08 else (2 if fd < 0.12 else 3))
    xb = 0 if distance >= 0.08 else (1 if distance >= 0.06 else (2 if distance >= 0.04 else (3 if distance >= 0.02 else 4)))
    gr = float(qrow.gamma_ratio) if pd.notna(qrow.gamma_ratio) else 1.0
    gb = 0 if gr < 1.5 else (1 if gr < 2.5 else 2)
    dj = float(qrow.delta_jump) if pd.notna(qrow.delta_jump) else 0.0
    jb = 0 if dj < 0.02 else (1 if dj < 0.04 else 2)
    coverage = 1.0 + 0.35*db + 0.30*xb + 0.30*gb + 0.35*jb
    desired_delta = N_SHORT * fd * coverage
    desired_qty = int(max(1, min(MAX_NEAR_QTY, math.ceil(desired_delta / NEAR_DELTA))))
    return {
        "far_delta": fd, "distance_pct": distance, "delta_band": db,
        "distance_band": xb, "gamma_ratio": gr, "gamma_band": gb,
        "delta_jump": dj, "jump_band": jb, "coverage_target": coverage,
        "desired_qty": desired_qty, "risk_score": db + xb + gb + jb
    }

def should_reload(strategy, state, prev_state, spot, camp_high, ret1d):
    if strategy in ("DAILY_TARGET_TP75","TRAIL_RELOAD","PARTIAL_HARVEST","TIME_ROLL_TARGET"):
        return True
    if strategy == "SHOCK_ADD_TP75":
        return prev_state is None or state["desired_qty"] > prev_state["desired_qty"] or state["delta_jump"] >= 0.02 or ret1d >= 0.015
    if strategy == "BAND_STEP_HARVEST":
        return prev_state is None or state["risk_score"] > prev_state["risk_score"]
    if strategy == "PULLBACK_RELOAD":
        return prev_state is None or spot <= camp_high*0.985 or state["risk_score"] > (prev_state["risk_score"] if prev_state else -1)
    if strategy == "ASYMMETRIC_TP100":
        return prev_state is None or state["desired_qty"] > prev_state["desired_qty"] or state["risk_score"] > (prev_state["risk_score"] if prev_state else -1)
    return True

def open_near(positions, leg, qmap, dt, target_dte, qty, cash):
    if qty <= 0 or leg is None:
        return 0, cash
    if leg is None:
        return 0, cash
    q = qmap.get(leg["cid"])
    if q is None or dt not in q.index:
        return 0, cash
    ask = float(q.loc[dt, "ask"])
    if not np.isfinite(ask) or ask < 0:
        return 0, cash
    for _ in range(int(qty)):
        positions.append(NearPos(dt, leg["expiry"], leg["cid"], leg["strike"], ask, target_dte, peak_bid=ask))
        cash -= ask*100.0
    return int(qty), cash

def close_pos(p, dt, bid, cash, reason):
    p.closed=True; p.exit=dt; p.exit_bid=float(bid); p.pnl=(float(bid)-p.entry_ask)*100.0; p.close_reason=reason
    return cash+float(bid)*100.0

def build_campaigns(u, candidates, far_quotes):
    out={}
    signals=u[u.signal & u.dma200.notna()]
    for fd in FAR_DTES:
        for fdel in FAR_DELTAS:
            rows=[]; next_allowed=None
            for _, sr in signals.iterrows():
                d0=pd.Timestamp(sr.date)
                if next_allowed is not None and d0<=next_allowed: continue
                far=candidates.get(d0,{}).get((fd,fdel))
                if not far: continue
                fq=far_quotes.get(far["cid"])
                if fq is None or d0 not in fq.index: continue
                end=min(far["expiry"], d0+pd.Timedelta(days=365))
                post=u[(u.date>d0)&(u.date<=end)]
                touch=post[post.high>=far["strike"]]
                reason="SHORT_TOUCH" if not touch.empty else "EXPIRY_OR_END"
                if not touch.empty: end=pd.Timestamp(touch.iloc[0].date)
                fq_after=fq.loc[fq.index>=end]
                if fq_after.empty: continue
                far_exit=pd.Timestamp(fq_after.index[0])
                if (far_exit-end).days>5: continue
                rows.append({"entry":d0,"end":end,"far_exit":far_exit,"far_reason":reason,"far":far})
                next_allowed=far_exit+pd.Timedelta(days=COOLDOWN_DAYS)
            out[(fd,fdel)]=rows
    return out

def simulate_campaign(u, far_quotes, near_chains, near_legs, near_q, camp, fd, fdel, nd, strategy):
    d0=camp["entry"]; far=camp["far"]; far_exit=camp["far_exit"]; fq=far_quotes.get(far["cid"])
    if fq is None or far_exit not in fq.index: return None
    spot_by=u.set_index("date")["close"]; ret_by=u.set_index("date")["ret1d"]
    positions=[]; trades=[]; cash=REFERENCE_CAPITAL_USD+far["entry_bid"]*N_SHORT*100.0
    peak=REFERENCE_CAPITAL_USD; min_eq=REFERENCE_CAPITAL_USD; prev=None; camp_high=float(spot_by.loc[d0])
    reloads=0; harvests=0
    for dt in pd.date_range(d0, far_exit, freq="D"):
        harvested_today = False
        if dt not in spot_by.index or dt not in fq.index: continue
        spot=float(spot_by.loc[dt]); r1d=float(ret_by.loc[dt]) if pd.notna(ret_by.loc[dt]) else 0.0
        camp_high=max(camp_high,spot)
        st=state_from_far(fq.loc[dt],spot,float(far["strike"]))
        active=[p for p in positions if not p.closed]
        # Profit/time/risk-relief harvest.
        for p in list(active):
            q=near_q.get(p.cid)
            if q is None or dt not in q.index: continue
            bid=float(q.loc[dt,"bid"]); p.peak_bid=max(p.peak_bid,bid)
            ret=bid/p.entry_ask-1.0 if p.entry_ask>0 else -1.0
            dleft=(p.expiry-dt).days
            close=False; reason=None
            if strategy != "ASYMMETRIC_TP100" and ret>=0.75: close,reason=True,"TP75"
            if strategy == "ASYMMETRIC_TP100" and ret>=1.00: close,reason=True,"TP100"
            if dleft<=2: close,reason=True,"DTE_LE2"
            if dt>=p.expiry: close,reason=True,"EXPIRY"
            if strategy=="TRAIL_RELOAD" and p.peak_bid>=p.entry_ask*1.50 and bid<=p.peak_bid*0.75:
                close,reason=True,"TRAIL25PCT"
            if strategy=="BAND_STEP_HARVEST" and prev is not None and st["risk_score"]+1<=prev["risk_score"] and ret>0:
                close,reason=True,"RISK_BAND_DOWN"
            if strategy=="TIME_ROLL_TARGET" and dleft<=2:
                close,reason=True,"TIME_ROLL"
            if strategy=="ASYMMETRIC_TP100":
                if prev is not None and st["risk_score"]+2<=prev["risk_score"] and ret>0: close,reason=True,"RISK_RELIEF"
            if strategy=="PARTIAL_HARVEST":
                if ret>=0.75: close=False; reason=None
            if close:
                cash=close_pos(p,dt,bid,cash,reason); trades.append(p); harvests+=1; harvested_today=True

        active=[p for p in positions if not p.closed]
        if strategy=="PARTIAL_HARVEST" and active:
            vals=[]; cost=0.0; bidv=0.0
            for p in active:
                q=near_q.get(p.cid)
                if q is None or dt not in q.index: continue
                b=float(q.loc[dt,"bid"]); vals.append((p,b,b/p.entry_ask-1.0 if p.entry_ask>0 else -1.0))
                cost += p.entry_ask*100.0; bidv += b*100.0
            if cost>0 and bidv/cost-1.0>=0.50:
                good=[x for x in vals if x[2]>0]
                for p,b,_ in good[:max(1,len(good)//2)]:
                    cash=close_pos(p,dt,b,cash,"PARTIAL_BOOK_50"); trades.append(p); harvests+=1; harvested_today=True
                active=[p for p in positions if not p.closed]

        # Coverage-driven reload: size to today's far-risk target.
        prev_qty=prev["desired_qty"] if prev is not None else 0
        allow=should_reload(strategy,st,prev,spot,camp_high,r1d)
        target=st["desired_qty"]
        if strategy=="ASYMMETRIC_TP100" and prev is not None and st["risk_score"] <= prev["risk_score"]:
            target=min(target,len(active))
        reload_ok=(not harvested_today) or strategy=="TIME_ROLL_TARGET"
        if (dt==d0 or allow) and reload_ok:
            need=max(0,target-len(active))
            if need>0:
                opened,cash=open_near(positions,near_legs.get((dt,nd)),near_q,dt,nd,need,cash)
                reloads+=opened

        # Shock reload is allowed to overshoot the normal target temporarily.
        if strategy in ("SHOCK_ADD_TP75","TRAIL_RELOAD","TIME_ROLL_TARGET","ASYMMETRIC_TP100") and st["delta_jump"]>=0.04 and ((not harvested_today) or strategy=="TIME_ROLL_TARGET"):
            active=[p for p in positions if not p.closed]
            extra=max(0,min(MAX_NEAR_QTY,target+2)-len(active))
            if extra>0 and near_chains.get(dt) is not None:
                opened,cash=open_near(positions,near_legs.get((dt,nd)),near_q,dt,nd,extra,cash); reloads+=opened

        # Mark-to-market: near at bid, far short at ask.
        liq=cash
        for p in positions:
            if p.closed: continue
            q=near_q.get(p.cid)
            if q is not None and dt in q.index: liq += float(q.loc[dt,"bid"])*100.0
        if dt<=far_exit and dt in fq.index: liq -= N_SHORT*float(fq.loc[dt,"ask"])*100.0
        peak=max(peak,liq); min_eq=min(min_eq,liq)
        prev=st

    # Force close remaining near longs at the far exit quote date or latest prior quote.
    for p in [x for x in positions if not x.closed]:
        q=near_q.get(p.cid)
        if q is None: continue
        av=q.loc[q.index>=far_exit]
        if not av.empty:
            dt2=pd.Timestamp(av.index[0]); bid=float(av.iloc[0].bid)
        else:
            pv=q.loc[q.index<=far_exit]
            if pv.empty: continue
            dt2=pd.Timestamp(pv.index[-1]); bid=float(pv.iloc[-1].bid)
        cash=close_pos(p,dt2,bid,cash,"FAR_EXIT"); trades.append(p)

    far_exit_ask=float(fq.loc[far_exit,"ask"])
    far_pnl=(far["entry_bid"]-far_exit_ask)*N_SHORT*100.0
    near_pnl=float(sum(p.pnl or 0.0 for p in trades))
    total=far_pnl+near_pnl
    wins=[p.pnl or 0.0 for p in trades if (p.pnl or 0.0)>0]
    losses=[p.pnl or 0.0 for p in trades if (p.pnl or 0.0)<0]
    gp=sum(wins); gl=-sum(losses)
    return {
        "campaign_entry":d0,"campaign_far_expiry":far["expiry"],"far_exit":far_exit,
        "far_reason":camp["far_reason"],"far_dte_target":fd,"far_delta_target":fdel,
        "far_strike":far["strike"],"far_entry_premium_usd":far["entry_bid"]*N_SHORT*100.0,
        "far_pnl_usd":far_pnl,"near_dte_target":nd,"strategy":strategy,
        "near_trades":len(trades),"near_wins":len(wins),"near_losses":len(losses),
        "near_win_rate":len(wins)/max(1,len(wins)+len(losses)),
        "near_gross_profit_usd":gp,"near_gross_loss_usd":gl,
        "near_profit_factor":gp/gl if gl>0 else (np.inf if gp>0 else np.nan),
        "near_realized_pnl_usd":near_pnl,"total_pnl_usd":total,
        "campaign_mdd":min_eq/REFERENCE_CAPITAL_USD-1.0,
        "max_active_near_qty":int(max([sum(1 for p in positions if not p.closed or (p.exit is not None and p.exit>=d) if p.entry<=d) for d in pd.date_range(d0,far_exit,freq="D")] or [0])),
        "reload_count":reloads,"harvest_count":harvests,
    }

def run_matrix(od:Path,ud:Path,out:Path):
    con=duckdb.connect(); u=load_underlying(ud); candidates=load_far_candidates(u,con,od)
    signal_dates=list(u.loc[u.signal & u.dma200.notna(),"date"])
    event_dates=set(pd.Timestamp(d) for d in signal_dates)
    for fd in FAR_DTES:
        for fdel in FAR_DELTAS:
            for d,legs in candidates.items():
                leg=legs.get((fd,fdel))
                if not leg: continue
                e=min(leg["expiry"],d+pd.Timedelta(days=365))
                event_dates.update(pd.Timestamp(x) for x in u.loc[(u.date>d)&(u.date<=e),"date"])
    near=read_options(con,od,"""
        SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id, CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
               COALESCE(CAST(volume AS DOUBLE),0) AS volume, CAST(delta AS DOUBLE) AS delta
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER("type")='CALL' AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask>=bid AND bid>=0
          AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 7 DAY
                                            AND CAST(date AS DATE)+INTERVAL 35 DAY
    """,[[d.date() for d in sorted(event_dates)]])
    near["date"]=pd.to_datetime(near.date); near["expiration"]=pd.to_datetime(near.expiration)
    near_chains={d:g for d,g in near.groupby("date",sort=False)}
    near_legs={}
    near_ids=set()
    for d,ch in near_chains.items():
        row=u.loc[u.date==d]
        if row.empty: continue
        spot=float(row.iloc[0].close)
        for nd in NEAR_DTES:
            leg=pick_near(ch,spot,nd)
            if leg:
                near_legs[(d,nd)]=leg
                near_ids.add(leg["cid"])
    cols=option_columns(con,od); has_gamma="gamma" in cols
    far_ids={leg["cid"] for legs in candidates.values() for leg in legs.values() if leg}
    far_q=get_quotes(con,od,far_ids,include_gamma=has_gamma)
    add_gamma_measure(far_q,u,has_gamma)
    near_q=get_quotes(con,od,near_ids,include_gamma=False)
    campaigns=build_campaigns(u,candidates,far_q)

    detail_rows=[]; summary_rows=[]
    for fd in FAR_DTES:
        for fdel in FAR_DELTAS:
            for nd in NEAR_DTES:
                for strategy in STRATEGIES:
                    rows=[]
                    for camp in campaigns[(fd,fdel)]:
                        r=simulate_campaign(u,far_q,near_chains,near_legs,near_q,camp,fd,fdel,nd,strategy)
                        if r is not None: rows.append(r)
                    if not rows: continue
                    df=pd.DataFrame(rows); detail_rows.append(df)
                    gp=float(df.near_gross_profit_usd.sum()); gl=float(df.near_gross_loss_usd.sum())
                    p=df.total_pnl_usd
                    summary_rows.append({
                        "strategy":strategy,"far_dte_target":fd,"far_delta_target":fdel,"near_dte_target":nd,
                        "campaigns":len(df),"positive_campaigns":int((p>0).sum()),
                        "campaign_win_rate":float((p>0).mean()),"total_pnl_usd":float(p.sum()),
                        "avg_campaign_pnl_usd":float(p.mean()),"median_campaign_pnl_usd":float(p.median()),
                        "worst_campaign_pnl_usd":float(p.min()),"far_pnl_usd":float(df.far_pnl_usd.sum()),
                        "near_realized_pnl_usd":float(df.near_realized_pnl_usd.sum()),
                        "near_trade_count":int(df.near_trades.sum()),
                        "near_win_rate":float(df.near_wins.sum()/max(1,df.near_wins.sum()+df.near_losses.sum())),
                        "near_profit_factor":float(gp/gl) if gl>0 else (np.inf if gp>0 else np.nan),
                        "mean_campaign_mdd":float(df.campaign_mdd.mean()),"worst_campaign_mdd":float(df.campaign_mdd.min()),
                        "mean_near_max_qty":float(df.max_active_near_qty.mean()),"max_near_qty_observed":int(df.max_active_near_qty.max()),
                        "total_reloads":int(df.reload_count.sum()),"total_harvests":int(df.harvest_count.sum())
                    })
    if not detail_rows: raise RuntimeError("No V22 results")
    detail=pd.concat(detail_rows,ignore_index=True)
    summary=pd.DataFrame(summary_rows).sort_values(
        ["total_pnl_usd","near_win_rate","campaign_win_rate"],ascending=[False,False,False]
    ).reset_index(drop=True)
    detail.to_csv(out/"v22_dynamic_risk_reload_detail.csv",index=False)
    summary.to_csv(out/"v22_dynamic_risk_reload_summary.csv",index=False)
    report={
        "status":"REAL_QQQ_CHAIN_DYNAMIC_RISK_RELOAD",
        "definitions":{
            "far_position":"10 x short call; far target 90/120/180 DTE and 5/8/10% delta, same V20/V21 extreme-high signal",
            "near_position":"near call closest to 50 delta; true 7/14/21/30 DTE matrix; buy at Ask, sell at Bid",
            "dynamic_state":"far absolute delta + live distance to short strike + gamma (or delta/spot gamma proxy) + daily delta acceleration",
            "dynamic_sizing":"ceil(10*abs(far_delta)*coverage_target/0.50), coverage_target responds to state bands; max 12 near contracts",
            "harvest_reload":"8 distinct reload/harvest profiles, all decisions use same-day or prior state only",
            "campaign_end":"first underlying High touch of far strike, otherwise far expiry/end; far close uses first executable Ask on/after end"
        },
        "data":{
            "options_sha256":sha256_file(od),"underlying_sha256":sha256_file(ud),
            "underlying_range":[str(u.date.min().date()),str(u.date.max().date())],
            "signal_count":int(u.signal.sum()),"near_event_date_count":len(event_dates),
            "gamma_source":"ACTUAL_GAMMA_WITH_PROXY_FALLBACK" if has_gamma else "DELTA_SPOT_GAMMA_PROXY"
        },
        "matrix":{
            "strategy_count":len(STRATEGIES),"strategies":list(STRATEGIES),
            "far_dtes":list(FAR_DTES),"far_deltas":list(FAR_DELTAS),
            "near_dtes":list(NEAR_DTES),"configs":len(STRATEGIES)*len(FAR_DTES)*len(FAR_DELTAS)*len(NEAR_DTES),
            "max_near_qty":MAX_NEAR_QTY
        },
        "top20":summary.head(20).to_dict("records")
    }
    (out/"v22_dynamic_risk_reload_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    print(json.dumps(report,indent=2,default=str),flush=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="data"); ap.add_argument("--out",default="artifacts")
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    run_matrix(Path(a.data_dir)/"QQQ_options.parquet",Path(a.data_dir)/"QQQ_underlying.parquet",out)

if __name__=="__main__":
    main()
