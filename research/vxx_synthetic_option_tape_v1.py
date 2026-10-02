#!/usr/bin/env python3
"""
VXX Synthetic Option Tape V1 — MODEL_DERIVED_VXX_OPTION_TAPE.

Research-only historical reconstruction. VXX/VIX/QQQ daily observations are
real inputs; QQQ option quotes are a contemporaneous observed reference.
The VXX option tape itself is model-derived, never OPRA/LIVE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.special import ndtr

RATE = 0.04
SQRT_252 = math.sqrt(252.0)
START = pd.Timestamp("2018-01-25")
END = pd.Timestamp("2026-09-01")
IV_LO, IV_HI = 0.40, 3.50
DTE_TARGETS = (14, 21, 30, 45, 60, 90, 120, 150, 180)
M_GRID = np.array(
    [-0.25,-0.20,-0.175,-0.15,-0.125,-0.10,-0.075,-0.05,-0.025,0.0,
      0.025,0.05,0.075,0.10,0.125,0.15,0.175,0.20,0.25,0.30,0.35,0.40]
)

FAMILIES = {
    "CONSERVATIVE": dict(atm=1.02, call=0.72, put=0.85, tail=0.45, spr=0.85, vrp=0.10, jump=0.55),
    "CENTRAL":      dict(atm=1.10, call=1.00, put=1.00, tail=0.70, spr=1.00, vrp=0.20, jump=0.80),
    "HIGH_SKEW":    dict(atm=1.10, call=1.40, put=1.10, tail=0.95, spr=1.15, vrp=0.20, jump=0.95),
    "STRESS":       dict(atm=1.25, call=1.80, put=1.35, tail=1.35, spr=1.70, vrp=0.30, jump=1.25),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def bs(s, k, t, sig, right):
    st = np.sqrt(np.maximum(t, 1e-12))
    d1 = (np.log(s / k) + (RATE + 0.5 * sig * sig) * t) / (sig * st)
    d2 = d1 - sig * st
    disc = np.exp(-RATE * t)
    pdf = np.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    gamma = pdf / np.maximum(s * sig * st, 1e-12)
    vega = s * pdf * st
    theta0 = -(s * pdf * sig) / (2.0 * st)
    if right == "CALL":
        price = s * ndtr(d1) - k * disc * ndtr(d2)
        delta = ndtr(d1)
        theta = theta0 - RATE * k * disc * ndtr(d2)
    else:
        price = k * disc * ndtr(-d2) - s * ndtr(-d1)
        delta = ndtr(d1) - 1.0
        theta = theta0 + RATE * k * disc * ndtr(-d2)
    return price, delta, gamma, vega, theta



def load_spots(p: Path) -> pd.DataFrame:
    x = pd.read_csv(p)
    x.columns = [c.strip().lower() for c in x.columns]
    x["date"] = pd.to_datetime(x["date"]).dt.normalize()
    for c in ("qqq","vxx","vix"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.sort_values("date").drop_duplicates("date")
    x = x[x.date.between(START, END) & x.vxx.gt(0) & x.vix.gt(0)].copy()
    x["vxx_lr"] = np.log(x.vxx).diff()
    x["qqq_lr"] = np.log(x.qqq).diff()
    x["vxx_rv20"] = x.vxx_lr.shift(1).rolling(20, min_periods=20).std() * SQRT_252
    x["vxx_rv60"] = x.vxx_lr.shift(1).rolling(60, min_periods=60).std() * SQRT_252
    x["qqq_rv20"] = x.qqq_lr.shift(1).rolling(20, min_periods=20).std() * SQRT_252
    mu = x.vix.shift(1).rolling(252, min_periods=60).mean()
    sd = x.vix.shift(1).rolling(252, min_periods=60).std()
    x["vix_z"] = ((x.vix-mu)/sd.replace(0,np.nan)).clip(-5,8)
    x["vix_d1_lag"] = x.vix.pct_change().shift(1)
    ratio = (x.vxx_rv20/(x.vix/100)).replace([np.inf,-np.inf],np.nan)
    x["rv_vix_ratio"] = ratio.shift(1).rolling(252,min_periods=60).median()
    return x.reset_index(drop=True)


def qqq_reference(con, opt: Path, under: Path) -> pd.DataFrame:
    """
    Bounded-memory causal QQQ surface reference.

    The canonical QQQ option parquet is large (~369MB compressed). Do not
    materialize it into pandas or iterate batches into a growing dictionary.
    DuckDB scans the parquet with a strict memory cap and spills to a local temp
    directory, returning only the deterministic 6-row representative per
    date/delta band needed by the model.
    """
    con.execute("PRAGMA threads=1")
    con.execute("PRAGMA memory_limit='256MB'")
    con.execute("PRAGMA temp_directory='.duckdb_tmp'")
    con.execute("PRAGMA preserve_insertion_order=false")

    schema=con.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)", [str(opt)]
    ).fetchdf()
    names=schema["column_name"].astype(str).tolist()
    lower={n.lower():n for n in names}

    def pick(*cands, required=True):
        for x in cands:
            if x in lower:
                return lower[x]
        if required:
            raise RuntimeError(
                f"QQQ parquet missing one of {cands}; columns={names[:40]}"
            )
        return None

    c_date=pick("date")
    c_exp=pick("expiration","expiry","exp")
    c_strike=pick("strike")
    c_type=pick("type","option_type","right")
    c_bid=pick("bid")
    c_ask=pick("ask")
    c_delta=pick("delta")
    c_volume=pick("volume",required=False)
    c_iv=pick("iv","implied_volatility","impliedvolatility",required=False)

    def ident(name):
        return '"' + str(name).replace('"','""') + '"'

    vdate=ident(c_date)
    vexp=ident(c_exp)
    vstrike=ident(c_strike)
    vtype=ident(c_type)
    vbid=ident(c_bid)
    vask=ident(c_ask)
    vdelta=ident(c_delta)
    vvolume=ident(c_volume) if c_volume else "0.0"
    viv=ident(c_iv) if c_iv else "NULL"

    q=f"""
    WITH base AS (
      SELECT
        CAST({vdate} AS DATE) AS date,
        CAST({vexp} AS DATE) AS expiration,
        TRY_CAST({vstrike} AS DOUBLE) AS strike,
        UPPER(CAST({vtype} AS VARCHAR)) AS type_norm,
        TRY_CAST({vbid} AS DOUBLE) AS bid,
        TRY_CAST({vask} AS DOUBLE) AS ask,
        TRY_CAST({vdelta} AS DOUBLE) AS delta,
        COALESCE(TRY_CAST({vvolume} AS DOUBLE),0.0) AS volume,
        TRY_CAST({viv} AS DOUBLE) AS iv_obs,
        DATEDIFF('day',CAST({vdate} AS DATE),CAST({vexp} AS DATE)) AS dte
      FROM read_parquet(?)
      WHERE CAST({vdate} AS DATE) BETWEEN DATE '2018-01-25' AND DATE '2026-09-01'
        AND UPPER(CAST({vtype} AS VARCHAR))='CALL'
        AND TRY_CAST({vstrike} AS DOUBLE)>0
        AND TRY_CAST({vbid} AS DOUBLE)>0
        AND TRY_CAST({vask} AS DOUBLE)>=TRY_CAST({vbid} AS DOUBLE)
        AND TRY_CAST({vdelta} AS DOUBLE) IS NOT NULL
        AND ABS(TRY_CAST({vdelta} AS DOUBLE)) BETWEEN 0.15 AND 0.85
        AND CAST({vexp} AS DATE)>CAST({vdate} AS DATE)
        AND DATEDIFF('day',CAST({vdate} AS DATE),CAST({vexp} AS DATE)) BETWEEN 20 AND 40
        -- Deterministic pre-sample before aggregation keeps the complete
        -- 369MB parquet from becoming an in-memory relation on small runners.
        AND MOD(
          HASH(
            CAST({vdate} AS VARCHAR) || '|' ||
            CAST({vexp} AS VARCHAR) || '|' ||
            CAST(TRY_CAST({vstrike} AS DOUBLE) AS VARCHAR)
          ),
          32
        ) = 0
    ),
    bands AS (
      SELECT *,
        CASE
          WHEN ABS(delta)<=0.30 THEN 1
          WHEN ABS(delta)<=0.45 THEN 2
          WHEN ABS(delta)<=0.55 THEN 3
          WHEN ABS(delta)<=0.70 THEN 4
          ELSE 5
        END AS band
      FROM base
    ),
    grouped AS (
      SELECT
        date,
        band,
        arg_min(
          struct_pack(
            expiration:=expiration,
            strike:=strike,
            type_norm:=type_norm,
            bid:=bid,
            ask:=ask,
            delta:=delta,
            volume:=volume,
            iv_obs:=iv_obs,
            dte:=dte
          ),
          struct_pack(
            dte_dist:=ABS(dte-30),
            neg_volume:=-volume,
            delta_dist:=ABS(ABS(delta)-0.50),
            expiration:=expiration,
            strike:=strike
          ),
          6
        ) AS picks
      FROM bands
      GROUP BY date,band
    )
    SELECT
      date,
      pick.expiration AS expiration,
      pick.strike AS strike,
      pick.type_norm AS type_norm,
      pick.bid AS bid,
      pick.ask AS ask,
      pick.delta AS delta,
      pick.volume AS volume,
      pick.iv_obs AS iv_obs,
      pick.dte AS dte
    FROM grouped
    CROSS JOIN UNNEST(picks) AS u(pick)
    ORDER BY date,band
    """

    z=con.execute(q,[str(opt)]).fetchdf()
    if z.empty:
        raise RuntimeError(
            "QQQ DuckDB deterministic pre-sample found no qualifying rows"
        )

    u=pd.read_parquet(under,columns=["date","close"])
    u["date"]=pd.to_datetime(u["date"]).dt.tz_localize(None).dt.normalize()
    u["close"]=pd.to_numeric(u["close"],errors="coerce")
    u=u[u.date.between(START,END)].copy()
    spot_map=dict(zip(u.date,u.close))

    z["date"]=pd.to_datetime(z["date"]).dt.normalize()
    z["expiration"]=pd.to_datetime(z["expiration"]).dt.normalize()
    z["spot"]=z.date.map(spot_map)
    z["m"]=np.log(z.strike/z.spot)
    z["mid"]=(z.bid+z.ask)/2
    if c_iv:
        z["iv_n"]=np.where(z.iv_obs>3,z.iv_obs/100,z.iv_obs)
    else:
        z["iv_n"]=[
            _iv_from_mid(float(r.spot),float(r.strike),float(r.dte)/365.0,float(r.mid))
            for r in z.itertuples(index=False)
        ]
    z=z[z.iv_n.notna() & z.iv_n.between(.02,3.5) & z.m.notna()].copy()
    if z.empty:
        raise RuntimeError("QQQ DuckDB reference has no usable IV rows")

    out=[]
    for dt,g in z.groupby("date",sort=True):
        atm=g[g.m.abs()<=.03].iv_n
        if atm.empty:
            atm=g.iloc[(g.delta.abs()-.5).abs().argsort()[:6]].iv_n
        cs=g[(g.m>0)&(g.m<=.25)]
        ps=g[(g.m<0)&(g.m>=-.25)]
        def slope(x):
            if len(x)<3:
                return 0.0
            try:
                w=np.sqrt(x.volume.to_numpy(float)+1.0)
                return float(np.polyfit(x.m.to_numpy(float),x.iv_n.to_numpy(float),1,w=w)[0])
            except Exception:
                return 0.0
        out.append({
            "date":dt,
            "qqq_atm_iv":float(atm.median()),
            "qqq_call_slope":slope(cs),
            "qqq_put_slope":-slope(ps),
            "qqq_rel_spread":float(((g.ask-g.bid)/g.mid).clip(0,2).median()),
            "qqq_reference_rows":int(len(g)),
        })
    r=pd.DataFrame(out).sort_values("date")
    cols=[x for x in r.columns if x!="date"]
    r[cols]=r[cols].shift(1)
    r["calibration_source_date"]=r.date.shift(1)
    return r

def _iv_from_mid(s,k,t,p):
    if not np.isfinite([s,k,t,p]).all() or min(s,k,t)<=0 or p<=0:
        return None
    lo,hi=1e-4,IV_HI
    for _ in range(60):
        m=(lo+hi)/2
        q=float(bs(np.array([s]),np.array([k]),np.array([t]),np.array([m]),"CALL")[0][0])
        if q>p: hi=m
        else: lo=m
    v=(lo+hi)/2
    return v if v>=.20 else None


def _summarize_qqq(g):
    atm=g[g.m.abs()<=.03].iv_n
    if atm.empty:
        atm=g.iloc[(g.delta.abs()-.5).abs().argsort()[:8]].iv_n
    c=g[(g.m>0)&(g.m<=.22)]
    p=g[(g.m<0)&(g.m>=-.22)]
    def slope(a):
        if len(a)<4: return 0.0
        try:
            return float(np.polyfit(a.m.to_numpy(),a.iv_n.to_numpy(),1)[0])
        except Exception:
            return 0.0
    sp=((g.ask-g.bid)/g.mid).clip(0,2)
    return pd.Series({
        "qqq_atm_iv":float(atm.median()),
        "qqq_call_slope":slope(c),
        "qqq_put_slope":-slope(p),
        "qqq_rel_spread":float(sp.median()),
    })


def friday_expiry(d,target):
    x=d+pd.Timedelta(days=int(target))
    x += pd.Timedelta(days=(4-x.weekday())%7)
    if (x-d).days<7: x+=pd.Timedelta(days=7)
    return x


def make_state(r,f):
    rv20=float(np.clip(r.vxx_rv20,.25,3.5))
    rv60=float(np.clip(r.vxx_rv60 if np.isfinite(r.vxx_rv60) else rv20,.25,3.5))
    qrv=float(r.qqq_rv20) if np.isfinite(r.qqq_rv20) else .18
    qiv=float(r.qqq_atm_iv) if np.isfinite(r.qqq_atm_iv) else .24
    qvrp=float(np.clip(qiv/max(qrv,.06),.85,1.8))
    ratio=float(r.rv_vix_ratio) if np.isfinite(r.rv_vix_ratio) else rv20/max(r.vix/100,.08)
    vix_equiv=float(np.clip(r.vix/100*ratio,.30,3.0))
    base=(.55*rv20+.25*rv60+.20*vix_equiv)*qvrp
    vixz=max(float(r.vix_z) if np.isfinite(r.vix_z) else 0,0)
    accel=abs(float(r.vix_d1_lag)) if np.isfinite(r.vix_d1_lag) else 0
    rv_gap=max(rv20/max(rv60,1e-6)-1,0)
    tail=float(np.clip(.65*vixz+.20*accel/.10+.15*rv_gap,0,6))
    atm=((1-f["vrp"])*base+f["vrp"]*max(rv20*qvrp,r.vix/100*2.2))*f["atm"]
    atm+=float(np.clip(tail*.025*f["jump"],0,.30))
    atm=float(np.clip(atm,IV_LO,IV_HI))
    qshape=float(abs(r.qqq_call_slope)/max(qiv,.05)) if np.isfinite(r.qqq_call_slope) else .5
    qpshape=float(abs(r.qqq_put_slope)/max(qiv,.05)) if np.isfinite(r.qqq_put_slope) else .5
    call_w=min(.50,(.24+.08*np.clip(qshape,0,2.5)+.03*min(tail,3))*f["call"])
    put_w=min(.90,(.55+.12*np.clip(qpshape,0,2.5)+.06*min(tail,3))*f["put"])
    return dict(
        date=r.date,family=r.family if hasattr(r,"family") else None,vxx=float(r.vxx),vix=float(r.vix),
        vxx_rv20=rv20,vxx_rv60=rv60,vix_z=float(r.vix_z) if np.isfinite(r.vix_z) else np.nan,
        tail_score=tail,qqq_atm_iv_ref=qiv,qqq_call_slope_ref=float(r.qqq_call_slope) if np.isfinite(r.qqq_call_slope) else np.nan,
        qqq_put_slope_ref=float(r.qqq_put_slope) if np.isfinite(r.qqq_put_slope) else np.nan,
        qqq_rel_spread_ref=float(r.qqq_rel_spread) if np.isfinite(r.qqq_rel_spread) else .10,
        atm_iv=atm,call_wing_slope=call_w,put_wing_slope=put_w,
        calibration_source_date=r.calibration_source_date,
    )



def _pava_nondecreasing(y):
    """Pool-adjacent-violators isotonic projection, equal weights."""
    vals=[]
    weights=[]
    blocks=[]
    for i,v in enumerate(np.asarray(y,float)):
        vals.append(float(v))
        weights.append(1.0)
        blocks.append([i,i])
        while len(vals)>=2 and vals[-2] > vals[-1] + 1e-15:
            nw=weights[-2]+weights[-1]
            nv=(vals[-2]*weights[-2]+vals[-1]*weights[-1])/nw
            vals[-2]=nv
            weights[-2]=nw
            blocks[-2][1]=blocks[-1][1]
            vals.pop()
            weights.pop()
            blocks.pop()
    out=np.empty(len(y),dtype=float)
    for v,(a,b) in zip(vals,blocks):
        out[a:b+1]=v
    return out


def _pava_nonincreasing(y):
    return -_pava_nondecreasing(-np.asarray(y,float))


def _project_no_arb_call_curve(raw_call, strikes, spot, disc):
    """
    Project raw call prices to a static zero-dividend no-arbitrage curve.
    The magnitude q=-dC/dK is projected to be non-increasing in [0,1].
    """
    raw_call=np.asarray(raw_call,float)
    strikes=np.asarray(strikes,float)
    if len(strikes)<3 or np.any(~np.isfinite(raw_call)) or np.any(~np.isfinite(strikes)):
        raise RuntimeError("no-arb projection input is invalid")
    dk=np.diff(strikes)
    if np.any(dk<=0):
        raise RuntimeError("strike grid must be strictly increasing")
    q=-np.diff(raw_call)/dk
    q=np.clip(q,0.0,1.0)
    q=_pava_nonincreasing(q)
    q=np.clip(q,0.0,1.0)
    cumulative=np.concatenate(([0.0],np.cumsum(-q*dk)))

    lower=np.maximum(spot-strikes*disc,0.0)-cumulative
    upper=spot-cumulative
    lo=float(np.max(lower))
    hi=float(np.min(upper))
    if lo>hi+1e-8:
        raise RuntimeError(f"no-arb anchor infeasible: lo={lo:.9g} hi={hi:.9g}")

    raw_anchor=raw_call-cumulative
    anchor=float(np.clip(np.mean(raw_anchor),lo,hi))
    curve=anchor+cumulative
    return curve,q


def _iv_from_price(s,k,t,p,right="CALL"):
    if not np.isfinite([s,k,t,p]).all() or min(s,k,t)<=0:
        return None
    disc=math.exp(-RATE*t)
    intrinsic=max((s-k*disc) if right=="CALL" else (k*disc-s),0.0)
    upper=s if right=="CALL" else k*disc
    tol=1e-9*max(1.0,upper)
    if p<intrinsic-tol or p>upper+tol:
        return None
    p=float(np.clip(p,intrinsic,upper))
    lo,hi=max(1e-4,IV_LO),IV_HI
    q_hi=float(bs(np.array([s]),np.array([k]),np.array([t]),np.array([hi]),right)[0][0])
    if q_hi+tol<p:
        return None
    for _ in range(70):
        m=(lo+hi)/2
        q=float(bs(np.array([s]),np.array([k]),np.array([t]),np.array([m]),right)[0][0])
        if q>p:
            hi=m
        else:
            lo=m
    return float((lo+hi)/2)


def _surface_regression_test():
    # Exact aggressive-wing shape that previously produced C(K+1)>C(K).
    s=50.0
    t=120.0/365.0
    m=np.array([-.025,.0,.025,.05,.1,.15,.2,.25,.3,.35,.4])
    k=s*(1+m)
    lm=np.log(k/s)
    atm=1.2
    callw=.42*1.8
    quad=.25
    tail=3.0
    iv=atm+np.where(
        lm>=0,callw*lm+quad*lm*lm,.55*(-lm)+.7*quad*lm*lm
    )
    iv=np.where(
        lm>0,iv+1.35*.045*tail*np.minimum(lm/.2,2),iv
    )
    raw=bs(np.full_like(k,s),k,np.full_like(k,t),iv,"CALL")[0]
    projected,_=_project_no_arb_call_curve(raw,k,s,math.exp(-RATE*t))
    slope=np.diff(projected)/np.diff(k)
    assert float(np.max(np.diff(raw)))>1e-6
    assert float(np.max(np.diff(projected)))<=1e-8
    assert float(np.min(np.diff(slope)))>=-1e-8
    put=projected-s+k*math.exp(-RATE*t)
    put_slope=np.diff(put)/np.diff(k)
    assert float(np.min(np.diff(put)))>=-1e-8
    assert float(np.min(np.diff(put_slope)))>=-1e-8
    return {
        "raw_max_call_price_diff":float(np.max(np.diff(raw))),
        "projected_max_call_price_diff":float(np.max(np.diff(projected))),
        "projected_min_second_slope_diff":float(np.min(np.diff(slope))),
    }



def build_family(market,family,out_file,write_tape=True):
    f=FAMILIES[family]
    writer=None
    rows=0
    days=set()
    state_rows=[]
    h=hashlib.sha256()
    sample_rows=[]
    for r0 in market.itertuples(index=False):
        if not np.isfinite(r0.vxx_rv20) or pd.isna(r0.calibration_source_date):
            continue
        # attach family without mutating market.
        r=r0._asdict()
        r["family"]=family
        class Row: pass
        rr=Row()
        for k,v in r.items(): setattr(rr,k,v)
        st=make_state(rr,f)
        state_rows.append(st)
        days.add(pd.Timestamp(rr.date))
        for target in DTE_TARGETS:
            expiry=friday_expiry(pd.Timestamp(rr.date),target)
            dte=int((expiry-pd.Timestamp(rr.date)).days)
            s=np.full(len(M_GRID),float(rr.vxx))
            k=np.maximum(.01,np.round(s*(1+M_GRID),2))
            lm=np.log(k/s)
            t=np.full(len(k),dte/365.0)
            iv_raw=st["atm_iv"]+np.where(
                lm>=0,st["call_wing_slope"]*lm+.20*lm*lm,
                st["put_wing_slope"]*(-lm)+.14*lm*lm
            )
            iv_raw=np.where(
                lm>0,
                iv_raw+f["tail"]*.015*st["tail_score"]*np.minimum(lm/.20,2),
                iv_raw
            )
            iv_raw=np.clip(iv_raw,IV_LO,IV_HI)

            # Raw strike-dependent IV can violate C_K<=0 / C_KK>=0.
            # Project CALL prices first, then recover one common IV surface.
            raw_call=bs(s,k,t,iv_raw,"CALL")[0]
            projected_call,_=_project_no_arb_call_curve(
                raw_call,k,float(rr.vxx),float(np.exp(-RATE*t[0]))
            )
            iv_projected=np.array([
                _iv_from_price(float(rr.vxx),float(kk),float(tt),float(pp),"CALL")
                for kk,tt,pp in zip(k,t,projected_call)
            ],dtype=float)
            if np.any(~np.isfinite(iv_projected)):
                raise RuntimeError(
                    f"{family} projected curve outside IV bounds on {rr.date} {expiry}"
                )
            for right in ("CALL","PUT"):
                # Same projected IV for CALL and PUT at identical (K,T).
                iv=iv_projected
                price,delta,gamma,vega,theta=bs(s,k,t,iv,right)
                rel=np.clip(
                    st["qqq_rel_spread_ref"] *
                    np.clip((st["atm_iv"]/max(st["qqq_atm_iv_ref"],.08))**.35,.75,3.0) *
                    f["spr"]*(1+.45*min(st["tail_score"],4))*(1+.65*np.abs(lm)),
                    .01,.35
                )
                half=np.maximum(.01,.5*price*rel)
                bid=np.maximum(0,price-half)
                ask=price+half
                block=pd.DataFrame({
                    "date":pd.Timestamp(rr.date),"expiration":expiry,"dte":dte,
                    "underlying":"VXX","type":right,"strike":k,
                    "bid":bid,"ask":ask,"mid":price,"iv":iv,"iv_raw":iv_raw,
                    "iv_repair_abs":np.zeros_like(iv),
                    "delta":delta,"gamma":gamma,"vega":vega,"theta":theta,
                    "parity_residual":np.nan,
                    "volume":np.nan,"open_interest":np.nan,
                    "model_family":family,"model_derived":True,
                    "source":"MODEL_DERIVED_VXX_OPTION_TAPE",
                    "calibration_source_date":pd.Timestamp(rr.calibration_source_date),
                    "model_rate":RATE,
                })
                rows += len(block)
                if len(sample_rows)<50000:
                    sample_rows.append(block)
                good=(
                    (block.bid<=block.mid+1e-10).all() and
                    (block.mid<=block.ask+1e-10).all() and
                    (block.bid>=0).all() and
                    np.isfinite(block[["iv","delta","gamma","vega","theta"]]).all().all()
                )
                if not good:
                    raise RuntimeError(f"{family} quote/greek gate failed on {rr.date} {expiry} {right}")
                sortb=block.sort_values("strike")
                strikes=sortb.strike.to_numpy(float)
                prices=sortb.mid.to_numpy(float)
                d1=np.diff(prices)
                # Strike grid is intentionally non-uniform, so raw second
                # differences are not a valid convexity test. Use finite
                # difference slopes dPrice/dStrike instead.
                dk=np.diff(strikes)
                slope=np.diff(prices)/np.maximum(dk,1e-12)
                convex_ok=bool(np.diff(slope).min()>=-1e-6)
                if right=="CALL":
                    if d1.max()>1e-8 or not convex_ok:
                        raise RuntimeError(f"{family} CALL price/convexity gate failed on {rr.date} {expiry}")
                else:
                    if d1.min()<-1e-8 or not convex_ok:
                        raise RuntimeError(f"{family} PUT price/convexity gate failed on {rr.date} {expiry}")

                if right=="PUT":
                    projected_parity=projected_call-price-(s-k*np.exp(-RATE*t))
                    block["parity_residual"] = projected_parity
                    if np.max(np.abs(projected_parity))>1e-8:
                        raise RuntimeError(
                            f"{family} put-call parity gate failed on {rr.date} {expiry}"
                        )

                if write_tape:
                    tbl=pa.Table.from_pandas(block,preserve_index=False)
                    if writer is None:
                        writer=pq.ParquetWriter(out_file,tbl.schema,compression="zstd")
                    writer.write_table(tbl)
                # Canonical rounded CSV hash; independent of Parquet encoding.
                canon=block[
                    ["date","expiration","type","strike","bid","ask","mid","iv",
                     "iv_raw","delta","gamma","vega","theta"]
                ].copy()
                for col in canon.columns[3:]:
                    canon[col]=pd.to_numeric(canon[col],errors="coerce").round(9)
                h.update(canon.to_csv(index=False,lineterminator="\n").encode())
    if writer is not None:
        writer.close()
    sample=pd.concat(sample_rows,ignore_index=True) if sample_rows else pd.DataFrame()
    return pd.DataFrame(state_rows),dict(rows=rows,days=len(days),tape_fingerprint=h.hexdigest(),sample=sample)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--spot-csv",required=True)
    ap.add_argument("--qqq-options",required=True)
    ap.add_argument("--qqq-underlying",required=True)
    ap.add_argument("--out",default="artifacts/vxx_synth_v1")
    ap.add_argument("--summary-only",action="store_true")
    args=ap.parse_args()

    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    spots=load_spots(Path(args.spot_csv))
    con=duckdb.connect()
    ref=qqq_reference(con,Path(args.qqq_options),Path(args.qqq_underlying))
    market=spots.merge(ref,on="date",how="left")
    market=market[market.calibration_source_date.notna() & market.vxx_rv20.notna()].copy()
    if market.empty:
        raise RuntimeError("No causal VXX market rows after calibration lock")

    metas={}
    all_states=[]
    family_fps=[]
    for fam in FAMILIES:
        path=out/f"vxx_option_tape_{fam.lower()}.parquet"
        states,meta=build_family(market,fam,path,write_tape=not args.summary_only)
        st=states.copy()
        st["family"]=fam
        all_states.append(st)
        family_fps.append((fam,meta["tape_fingerprint"]))
        meta2={"rows":meta["rows"],"days":meta["days"],"tape_fingerprint":meta["tape_fingerprint"]}
        metas[fam]=meta2
        if not args.summary_only:
            meta["sample"].sort_values(["date","expiration","type","strike"]).to_csv(
                out/f"vxx_option_tape_{fam.lower()}.sample.csv",index=False
            )

    state=pd.concat(all_states,ignore_index=True)

    # Combine family-level evidence without materializing the full tape.
    # The block gates above enforce static price shape. Track parity/greek/quote
    # ranges at the manifest level from the causal surface states and family run.
    family_hash=hashlib.sha256("\n".join(f"{a}:{b}" for a,b in family_fps).encode()).hexdigest()
    state_hash=hashlib.sha256(
        state.sort_values(["date","family"]).round(9).to_csv(index=False,lineterminator="\n").encode()
    ).hexdigest()
    canonical_fingerprint=hashlib.sha256(
        f"{family_hash}:{state_hash}".encode()
    ).hexdigest()
    regression=_surface_regression_test()
    manifest={
        "research_id":"VXX_SYNTHETIC_OPTION_TAPE_V1",
        "status":"MODEL_DERIVED",
        "source":"MODEL_DERIVED_VXX_OPTION_TAPE",
        "historical_vxx_opra_available":False,
        "do_not_treat_as_live_or_opra":True,
        "date_range":{"start":str(state.date.min().date()),"end":str(state.date.max().date()),"days":int(state.date.nunique())},
        "families":list(FAMILIES),"dte_targets":list(DTE_TARGETS),"moneyness_grid":M_GRID.tolist(),
        "calibration":{"causal_shift":"one prior observation",
          "qqq_reference_sampling":"stratified 5 delta bands x 6 rows/day, 20-40 DTE nearest 30D",
          "references":["observed VXX/VIX/QQQ daily path","causal VXX RV20/RV60",
                        "causal VIX z-score/prior acceleration",
                        "observed historical QQQ option bid/ask/delta/IV surface",
                        "causal QQQ RV20"]},
        "input_sha256":{
          "spots":sha256_file(Path(args.spot_csv)),
          "qqq_options":sha256_file(Path(args.qqq_options)),
          "qqq_underlying":sha256_file(Path(args.qqq_underlying))},
        "families_definition":FAMILIES,
        "family_meta":metas,
        "quality_gate": {
          "status":"PASS",
          "regression_test":"PASS",
          "blocks_checked":int(sum(meta["rows"] for meta in metas.values())/(2*len(M_GRID))),
          "regression_details":regression,
          "static_shape_rule":"CALL decreasing + convex; PUT increasing + convex",
        },
        "surface_integrity": {
          "common_iv_for_call_put": True,
          "put_call_parity_convention": "C-P = S-K*exp(-rT), zero dividend",
          "raw_surface_projected_to_no_arb_price_curve": True,
          "projected_price_monotonicity": "hard gate",
          "projected_discrete_convexity": "hard gate",
          "delta_monotonicity": "diagnostic_only_not_hard_gate",
        },
        "state_fingerprint":state_hash,
        "family_fingerprint":family_hash,
        "canonical_fingerprint":canonical_fingerprint,
        "script_sha256":sha256_file(Path(__file__)),
        "python":platform.python_version(),"platform":platform.platform(),
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,default=str),encoding="utf-8")
    state.to_csv(out/"daily_surface_state.csv",index=False)
    print(json.dumps(manifest,indent=2,default=str))


if __name__=="__main__":
    main()
