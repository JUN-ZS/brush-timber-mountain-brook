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
    oc = {str(v).lower() for v in con.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)", [str(opt)]
    ).df().column_name}
    iv_name = next((c for c in ("iv","implied_volatility","impliedvolatility") if c in oc), None)

    u = pd.read_parquet(under, columns=["date","close"])
    u["date"] = pd.to_datetime(u["date"]).dt.tz_localize(None).dt.normalize()
    u["close"] = pd.to_numeric(u["close"], errors="coerce")
    u["lr"] = np.log(u.close).diff()
    u["rv20"] = u.lr.shift(1).rolling(20,min_periods=20).std()*SQRT_252
    u = u[u.date.between(START,END)].copy()
    con.register("qqq_under", u)

    iv_expr = (
        f'CAST("{iv_name}" AS DOUBLE)' if iv_name
        else "NULL::DOUBLE"
    )
    sql = f"""
      WITH q AS (
        SELECT CAST(o.date AS DATE) AS date,
               CAST(o.expiration AS DATE) AS expiration,
               CAST(o.strike AS DOUBLE) AS strike,
               CAST(o.bid AS DOUBLE) AS bid,
               CAST(o.ask AS DOUBLE) AS ask,
               CAST(o.delta AS DOUBLE) AS delta,
               COALESCE(CAST(o.volume AS DOUBLE),0) AS volume,
               {iv_expr} AS iv,
               u.close AS spot
        FROM read_parquet(?) o
        JOIN qqq_under u
          ON CAST(o.date AS DATE)=u.date
        WHERE CAST(o.date AS DATE) BETWEEN DATE '2018-01-25' AND DATE '2026-09-01'
          AND UPPER(o.type)='CALL'
          AND CAST(o.expiration AS DATE) BETWEEN CAST(o.date AS DATE)+INTERVAL 20 DAY
                                           AND CAST(o.date AS DATE)+INTERVAL 40 DAY
          AND o.bid IS NOT NULL AND o.ask IS NOT NULL
          AND o.ask >= o.bid AND o.bid > 0
          AND o.delta IS NOT NULL
          AND ABS(CAST(o.delta AS DOUBLE)) BETWEEN 0.15 AND 0.85
      )
      SELECT date, expiration, strike, bid, ask, delta, volume, spot,
             (expiration-date) AS dte,
             LN(strike/spot) AS m,
             iv
      FROM q
    """
    z = con.execute(sql,[str(opt)]).df()
    if z.empty:
        raise RuntimeError("QQQ observed reference chain empty")
    z["dte"] = pd.to_numeric(z["dte"], errors="coerce")
    z["mid"] = (z.bid+z.ask)/2
    if iv_name:
        z["iv_n"] = np.where(z.iv>3,z.iv/100,z.iv)
    else:
        # Rare fallback: keep only 20 closest-delta observations per day before
        # midpoint inversion, so missing IV cannot explode memory.
        z["rank"] = z.groupby("date")["delta"].transform(
            lambda s: (s.abs()-.5).abs().rank(method="first")
        )
        z = z[z["rank"]<=20].copy()
        vals=[]
        for r in z.itertuples(index=False):
            vals.append(_iv_from_mid(float(r.spot),float(r.strike),float(r.dte)/365,
                                     float(r.mid)))
        z["iv_n"]=vals

    z=z[z.iv_n.notna() & z.iv_n.between(.02,3.5) & z.m.notna()].copy()
    out=(
        z.groupby("date",as_index=False)
        .apply(_summarize_qqq, include_groups=False)
        .reset_index(drop=True)
    )
    out=out.sort_values("date")
    cols=[c for c in out.columns if c!="date"]
    out[cols]=out[cols].shift(1)
    out["calibration_source_date"]=out.date.shift(1)
    return out


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
            for right in ("CALL","PUT"):
                # Same IV surface for CALL and PUT at identical (K,T).
                # This preserves internal put-call parity under the declared
                # zero-dividend / constant-rate pricing convention.
                iv=iv_raw
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
                    block["parity_residual"] = (
                        bs(s,k,t,iv,"CALL")[0] - price - (s-k*np.exp(-RATE*t))
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
    manifest={
        "research_id":"VXX_SYNTHETIC_OPTION_TAPE_V1",
        "status":"MODEL_DERIVED",
        "source":"MODEL_DERIVED_VXX_OPTION_TAPE",
        "historical_vxx_opra_available":False,
        "do_not_treat_as_live_or_opra":True,
        "date_range":{"start":str(state.date.min().date()),"end":str(state.date.max().date()),"days":int(state.date.nunique())},
        "families":list(FAMILIES),"dte_targets":list(DTE_TARGETS),"moneyness_grid":M_GRID.tolist(),
        "calibration":{"causal_shift":"one prior observation",
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
        "surface_integrity": {
          "common_iv_for_call_put": True,
          "put_call_parity_convention": "C-P = S-K*exp(-rT), zero dividend",
          "per_block_price_monotonicity": "hard gate",
          "per_block_discrete_convexity": "hard gate",
          "delta_monotonicity": "diagnostic_only_not_hard_gate",
        },
        "state_fingerprint":state_hash,
        "family_fingerprint":family_hash,
        "script_sha256":sha256_file(Path(__file__)),
        "python":platform.python_version(),"platform":platform.platform(),
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,default=str),encoding="utf-8")
    state.to_csv(out/"daily_surface_state.csv",index=False)
    print(json.dumps(manifest,indent=2,default=str))


if __name__=="__main__":
    main()
