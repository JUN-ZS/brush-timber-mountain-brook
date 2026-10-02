#!/usr/bin/env python3
"""
VXX Synthetic Option Tape V1 — MODEL_DERIVED_VXX_OPTION_TAPE.

Research-only. This reconstructs a deterministic VXX option surface from:
  * observed VXX/VIX/QQQ daily history,
  * causal VXX/QQQ realized-volatility state,
  * a one-observation-lagged historical QQQ option surface reference.

It is NOT historical VXX OPRA and must never be labelled LIVE/OBSERVED.
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
from scipy.special import ndtr

RATE = 0.04
SQRT_252 = math.sqrt(252.0)
START = pd.Timestamp("2018-01-25")
END = pd.Timestamp("2026-09-01")
IV_LO, IV_HI = 0.40, 3.50
REL_SPREAD_HI = 0.35
DTE_TARGETS = (14, 21, 30, 45, 60, 90, 120, 150, 180)
M_GRID = np.array(
    [-0.25,-0.20,-0.175,-0.15,-0.125,-0.10,-0.075,-0.05,-0.025,0.0,
      0.025,0.05,0.075,0.10,0.125,0.15,0.175,0.20,0.25,0.30,0.35,0.40],
    dtype=float,
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


def bs(
    s: np.ndarray, k: np.ndarray, t: np.ndarray, sig: np.ndarray, right: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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


def implied_vol(s: float, k: float, t: float, p: float, right: str) -> float | None:
    if not np.isfinite([s,k,t,p]).all() or min(s,k,t) <= 0 or p <= 0:
        return None
    lo, hi = 1e-4, IV_HI
    for _ in range(65):
        m = (lo + hi) * 0.5
        px = float(bs(np.array([s]), np.array([k]), np.array([t]), np.array([m]), right)[0][0])
        intrinsic = max(s-k,0.0) if right=="CALL" else max(k-s,0.0)
        if px > p:
            hi = m
        else:
            lo = m
    v = (lo + hi) * 0.5
    return v if v >= IV_LO/2 else None


def load_spots(path: Path) -> pd.DataFrame:
    x = pd.read_csv(path)
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


def parquet_cols(con, p: Path) -> set[str]:
    d = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(p)]).df()
    return {str(v).lower() for v in d.column_name}


def qqq_reference(con, opt: Path, under: Path) -> pd.DataFrame:
    oc = parquet_cols(con, opt)
    iv_name = next((c for c in ("iv","implied_volatility","impliedvolatility") if c in oc), None)
    iv_sel = f', CAST("{iv_name}" AS DOUBLE) AS iv' if iv_name else ""

    u = pd.read_parquet(under)
    u.columns = [c.lower() for c in u.columns]
    u["date"] = pd.to_datetime(u["date"]).dt.tz_localize(None).dt.normalize()
    u["close"] = pd.to_numeric(u["close"], errors="coerce")
    u["lr"] = np.log(u.close).diff()
    u["rv20"] = u.lr.shift(1).rolling(20,min_periods=20).std()*SQRT_252
    u = u[u.date.between(START,END)].copy()
    spot_map = dict(zip(u.date, u.close))

    sql = f"""
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(delta AS DOUBLE) AS delta,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume
             {iv_sel}
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) BETWEEN DATE '2018-01-25' AND DATE '2026-09-01'
        AND UPPER(type)='CALL'
        AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 20 DAY
                                         AND CAST(date AS DATE)+INTERVAL 40 DAY
        AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask >= bid AND bid > 0
        AND delta IS NOT NULL
        AND ABS(CAST(delta AS DOUBLE)) BETWEEN 0.15 AND 0.85
    """
    z = con.execute(sql,[str(opt)]).df()
    if z.empty:
        raise RuntimeError("QQQ reference chain is empty")
    z["date"] = pd.to_datetime(z.date)
    z["expiration"] = pd.to_datetime(z.expiration)
    z["spot"] = z.date.map(spot_map)
    z["dte"] = (z.expiration-z.date).dt.days
    z["mid"] = (z.bid+z.ask)/2
    z["m"] = np.log(z.strike/z.spot)
    if iv_name:
        z["iv_n"] = np.where(z.iv>3,z.iv/100,z.iv)
    else:
        z["rank"] = z.groupby("date")["delta"].transform(
            lambda s: (s.abs()-0.5).abs().rank(method="first")
        )
        z = z[z["rank"]<=25].copy()
        vals=[]
        for r in z.itertuples(index=False):
            vals.append(implied_vol(float(r.spot),float(r.strike),float(r.dte)/365,
                                    float(r.mid),"CALL"))
        z["iv_n"]=vals
    z=z[z.iv_n.notna() & z.iv_n.between(.02,3.5) & z.m.notna()].copy()

    out=[]
    for d,g in z.groupby("date",sort=True):
        atm=g[g.m.abs()<=.03].iv_n
        if atm.empty:
            atm=g.iloc[(g.delta.abs()-.5).abs().argsort()[:8]].iv_n
        cs=g[(g.m>0)&(g.m<=.22)].copy()
        ps=g[(g.m<0)&(g.m>=-.22)].copy()
        def sl(a):
            if len(a)<4: return 0.0
            try:
                return float(np.polyfit(a.m.to_numpy(),a.iv_n.to_numpy(),1,
                                        w=np.sqrt(a.volume.to_numpy()+1)))
            except Exception:
                return 0.0
        call_s=sl(cs)
        put_s=-sl(ps)
        spread=float(((g.ask-g.bid)/g.mid).clip(0,2).median())
        out.append(dict(
            date=d, qqq_atm_iv=float(atm.median()),
            qqq_call_slope=call_s, qqq_put_slope=put_s,
            qqq_rel_spread=spread,
        ))
    r=pd.DataFrame(out).sort_values("date")
    # Strong causality rule: VXX date t can only see QQQ reference from <t.
    ref_cols=[c for c in r.columns if c!="date"]
    r[ref_cols]=r[ref_cols].shift(1)
    r["calibration_source_date"]=r.date.shift(1)
    return r


def friday_expiry(d: pd.Timestamp, target: int) -> pd.Timestamp:
    x=d+pd.Timedelta(days=target)
    x += pd.Timedelta(days=(4-x.weekday())%7)
    if (x-d).days<7: x+=pd.Timedelta(days=7)
    return x



def repair_iv_shape(
    s: np.ndarray, k: np.ndarray, t: np.ndarray, iv: np.ndarray, right: str
) -> np.ndarray:
    """Minimal deterministic no-arbitrage repair along the strike axis.

    The raw VXX tail surface is allowed to be intentionally aggressive. If
    that makes call prices rise with strike or put prices fall with strike,
    reduce/increase only the offending IV until monotonicity is restored.
    The repair is reported explicitly and is never treated as calibration data.
    """
    out = iv.copy()
    prev = None
    for i in range(len(out)):
        px = float(bs(s[i:i+1], k[i:i+1], t[i:i+1], out[i:i+1], right)[0][0])
        if prev is not None:
            bad = px > prev + 1e-10 if right == "CALL" else px < prev - 1e-10
            if bad:
                if right == "CALL":
                    lo, hi = IV_LO, float(out[i])
                    for _ in range(45):
                        mid = (lo + hi) * 0.5
                        q = float(bs(
                            s[i:i+1], k[i:i+1], t[i:i+1],
                            np.array([mid]), right
                        )[0][0])
                        if q > prev:
                            hi = mid
                        else:
                            lo = mid
                    out[i] = lo
                else:
                    lo, hi = float(out[i]), IV_HI
                    for _ in range(45):
                        mid = (lo + hi) * 0.5
                        q = float(bs(
                            s[i:i+1], k[i:i+1], t[i:i+1],
                            np.array([mid]), right
                        )[0][0])
                        if q < prev:
                            lo = mid
                        else:
                            hi = mid
                    out[i] = hi
                px = float(bs(
                    s[i:i+1], k[i:i+1], t[i:i+1],
                    np.array([out[i]]), right
                )[0][0])
        prev = px
    return np.clip(out, IV_LO, IV_HI)

def build_family(m: pd.DataFrame, family: str) -> tuple[pd.DataFrame,pd.DataFrame]:
    f=FAMILIES[family]
    states=[]
    blocks=[]
    for r in m.itertuples(index=False):
        if not np.isfinite(r.vxx_rv20):
            continue
        rv20=float(np.clip(r.vxx_rv20,.25,3.5))
        rv60=float(np.clip(r.vxx_rv60 if np.isfinite(r.vxx_rv60) else rv20,.25,3.5))
        qrv=float(r.qqq_rv20) if np.isfinite(r.qqq_rv20) else .18
        qiv=float(r.qqq_atm_iv) if np.isfinite(r.qqq_atm_iv) else .24
        qvrp=float(np.clip(qiv/max(qrv,.06),.85,1.8))
        ratio=float(r.rv_vix_ratio) if np.isfinite(r.rv_vix_ratio) else rv20/max(r.vix/100,.08)
        vix_equiv=float(np.clip(r.vix/100*ratio,.30,3.0))
        base=(.55*rv20+.25*rv60+.20*vix_equiv)
        base*=qvrp
        tail=float(max(r.vix_z if np.isfinite(r.vix_z) else 0,0))
        accel=float(abs(r.vix_d1_lag) if np.isfinite(r.vix_d1_lag) else 0)
        tail_score=float(np.clip(.65*tail+.20*accel/.10+.15*max(r.vxx_rv20/max(r.vxx_rv60,1e-6)-1,0),0,6))
        atm=((1-f["vrp"])*base+f["vrp"]*max(rv20*qvrp,r.vix/100*2.2))*f["atm"]
        atm += float(np.clip(tail_score*.025*f["jump"],0,.30))
        atm=float(np.clip(atm,IV_LO,IV_HI))

        qshape=float(abs(r.qqq_call_slope)/max(qiv,.05)) if np.isfinite(r.qqq_call_slope) else .5
        qpshape=float(abs(r.qqq_put_slope)/max(qiv,.05)) if np.isfinite(r.qqq_put_slope) else .5
        call_w=(.42+.18*np.clip(qshape,0,2.5)+.10*min(tail_score,3))*f["call"]
        put_w=(.55+.12*np.clip(qpshape,0,2.5)+.08*min(tail_score,3))*f["put"]
        quad=.20+.05*min(tail_score,4)
        ref_sp=float(r.qqq_rel_spread) if np.isfinite(r.qqq_rel_spread) else .10
        vol_scale=float(np.clip((atm/max(qiv,.08))**.35,.75,3.0))

        states.append(dict(
            date=r.date,family=family,vxx=float(r.vxx),vix=float(r.vix),
            vxx_rv20=rv20,vxx_rv60=rv60,vix_z=float(r.vix_z) if np.isfinite(r.vix_z) else np.nan,
            tail_score=tail_score,qqq_atm_iv_ref=qiv,qqq_call_slope_ref=float(r.qqq_call_slope) if np.isfinite(r.qqq_call_slope) else np.nan,
            qqq_put_slope_ref=float(r.qqq_put_slope) if np.isfinite(r.qqq_put_slope) else np.nan,
            qqq_rel_spread_ref=ref_sp,atm_iv=atm,call_wing_slope=call_w,put_wing_slope=put_w,
            calibration_source_date=r.calibration_source_date,
        ))

        s=np.full(len(M_GRID),float(r.vxx))
        k=np.maximum(.01,np.round(s*(1+M_GRID),2))
        lm=np.log(k/s)
        exps=[friday_expiry(pd.Timestamp(r.date),d) for d in DTE_TARGETS]
        for expiry in exps:
            dte=int((expiry-pd.Timestamp(r.date)).days)
            t=np.full(len(k),max(dte,1)/365.0)
            iv_raw=atm+np.where(lm>=0,call_w*lm+quad*lm*lm,
                                put_w*(-lm)+.70*quad*lm*lm)
            iv_raw=np.where(lm>0,
                            iv_raw+f["tail"]*.045*tail_score*np.minimum(lm/.20,2.0),
                            iv_raw)
            iv_raw=np.clip(iv_raw,IV_LO,IV_HI)
            for right in ("CALL","PUT"):
                iv=repair_iv_shape(s,k,t,iv_raw,right)
                iv_repair_abs=np.abs(iv-iv_raw)
                price,delta,gamma,vega,theta=bs(
                    s,t*0+k,t,iv,right
                )
                rel=np.clip(ref_sp*vol_scale*f["spr"]*(1+.45*min(tail_score,4))*
                            (1+.65*np.abs(lm)),.01,REL_SPREAD_HI)
                half=np.maximum(.01,.5*price*rel)
                bid=np.maximum(0,price-half)
                ask=price+half
                blocks.append(pd.DataFrame({
                    "date":pd.Timestamp(r.date),"expiration":expiry,"dte":dte,
                    "underlying":"VXX","type":right,"strike":k,
                    "bid":bid,"ask":ask,"mid":price,"iv":iv,
                    "delta":delta,"gamma":gamma,"vega":vega,"theta":theta,
                    "iv_raw":iv_raw,"iv_repair_abs":iv_repair_abs,
                    "volume":np.nan,"open_interest":np.nan,
                    "model_family":family,"model_derived":True,
                    "source":"MODEL_DERIVED_VXX_OPTION_TAPE",
                    "calibration_source_date":r.calibration_source_date,
                    "model_rate":RATE,
                }))
    return pd.concat(blocks,ignore_index=True),pd.DataFrame(states)


def quality(t: pd.DataFrame,s: pd.DataFrame)->dict:
    q={
      "rows":int(len(t)),"days":int(t.date.nunique()),
      "model_derived_only":bool(t.model_derived.all() and t.source.eq("MODEL_DERIVED_VXX_OPTION_TAPE").all()),
      "quote_order":bool((t.bid<=t.mid+1e-10).all() and (t.mid<=t.ask+1e-10).all()),
      "nonnegative_quotes":bool((t.bid>=0).all() and (t.ask>0).all()),
      "iv_bounds":bool(t.iv.between(IV_LO,IV_HI).all()),
      "expiry_after":bool((t.expiration>t.date).all()),
      "greeks_finite":bool(np.isfinite(t[["iv","delta","gamma","vega","theta"]]).all().all()),
      "surface_repair_finite":bool(np.isfinite(t[["iv_raw","iv_repair_abs"]]).all().all()),
      "causal":bool(t.calibration_source_date.notna().all() and (t.calibration_source_date<t.date).all()),
    }
    cmono=pmono=cdmono=pdmono=True
    for _,g in t.groupby(["model_family","date","expiration"],sort=False):
        c=g[g.type.eq("CALL")].sort_values("strike")
        p=g[g.type.eq("PUT")].sort_values("strike")
        if len(c)>2:
            cmono &= bool(np.diff(c.mid.to_numpy()).max()<=1e-8)
            cdmono &= bool(np.diff(c.delta.to_numpy()).max()<=1e-8)
        if len(p)>2:
            pmono &= bool(np.diff(p.mid.to_numpy()).min()>=-1e-8)
            pdmono &= bool(np.diff(p.delta.to_numpy()).min()>=-1e-8)
    q.update(call_price_monotone=cmono,put_price_monotone=pmono,
             call_delta_monotone=cdmono,put_delta_monotone=pdmono,
             state_rows=int(len(s)))
    q["status"]="PASS" if all(v for k,v in q.items() if isinstance(v,bool)) else "FAIL"
    return q


def fingerprint(t:pd.DataFrame,s:pd.DataFrame)->str:
    cols=["date","expiration","type","strike","bid","ask","mid","iv","delta","gamma","vega","theta","model_family"]
    z=t[cols].sort_values(["date","expiration","type","strike","model_family"],kind="mergesort").copy()
    for c in cols[3:12]: z[c]=pd.to_numeric(z[c],errors="coerce").round(9)
    u=s.sort_values(["date","family"]).copy()
    payload=(z.to_csv(index=False,lineterminator="\n")+u.to_csv(index=False,lineterminator="\n")).encode()
    return hashlib.sha256(payload).hexdigest()


def run(args):
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    spot=Path(args.spot_csv); opt=Path(args.qqq_options); und=Path(args.qqq_underlying)
    spots=load_spots(spot)
    con=duckdb.connect()
    ref=qqq_reference(con,opt,und)
    m=spots.merge(ref,on="date",how="left")
    # Do not invent an earlier calibration source; start only when all causal inputs exist.
    m=m[m.calibration_source_date.notna()].copy()
    m=m[m.vxx_rv20.notna()].copy()

    tapes=[]; states=[]
    family_meta={}
    for fam in FAMILIES:
        t,s=build_family(m,fam); q=quality(t,s)
        if q["status"]!="PASS": raise RuntimeError(f"{fam} quality gate failed: {q}")
        tapes.append(t); states.append(s)
        family_meta[fam]={"rows":len(t),"days":int(t.date.nunique())}
    tape=pd.concat(tapes,ignore_index=True)
    state=pd.concat(states,ignore_index=True)
    q=quality(tape,state)
    if q["status"]!="PASS": raise RuntimeError(f"combined quality gate failed: {q}")
    fp=fingerprint(tape,state)

    manifest={
      "research_id":"VXX_SYNTHETIC_OPTION_TAPE_V1",
      "status":"MODEL_DERIVED",
      "source":"MODEL_DERIVED_VXX_OPTION_TAPE",
      "historical_vxx_opra_available":False,
      "do_not_treat_as_live_or_opra":True,
      "date_range":{"start":str(tape.date.min().date()),"end":str(tape.date.max().date()),
                    "days":int(tape.date.nunique())},
      "families":list(FAMILIES),
      "dte_targets":list(DTE_TARGETS),
      "moneyness_grid":M_GRID.tolist(),
      "calibration":{"causal_shift":"one prior observation",
        "observed_references":["VXX/VIX/QQQ daily path","VXX causal RV20/RV60",
          "VIX causal z-score/prior acceleration","observed QQQ option bid/ask/delta/IV surface",
          "QQQ causal RV20"]},
      "input_sha256":{"spots":sha256_file(spot),"qqq_options":sha256_file(opt),"qqq_underlying":sha256_file(und)},
      "quality_gate":q,"family_meta":family_meta,"canonical_fingerprint":fp,
      "script_sha256":sha256_file(Path(__file__)),"python":platform.python_version(),
      "platform":platform.platform(),"numpy":np.__version__,
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,default=str),encoding="utf-8")
    state.to_csv(out/"daily_surface_state.csv",index=False)
    m.to_csv(out/"market_calibration_state.csv",index=False)
    if not args.summary_only:
        tape.to_parquet(out/"vxx_option_tape.parquet",index=False)
        tape.sort_values(["date","model_family","expiration","type","strike"]).head(50000).to_csv(
            out/"vxx_option_tape.sample.csv",index=False)
    print(json.dumps(manifest,indent=2,default=str))
    if args.verify_manifest:
        expected=json.loads(Path(args.verify_manifest).read_text(encoding="utf-8"))
        if expected.get("canonical_fingerprint")!=fp:
            raise RuntimeError(f"cross-run fingerprint mismatch: {expected.get('canonical_fingerprint')} != {fp}")
        print("CROSS_RUN_FINGERPRINT_MATCH",fp)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--spot-csv",required=True)
    ap.add_argument("--qqq-options",required=True)
    ap.add_argument("--qqq-underlying",required=True)
    ap.add_argument("--out",default="artifacts/vxx_synth_v1")
    ap.add_argument("--summary-only",action="store_true")
    ap.add_argument("--verify-manifest")
    run(ap.parse_args())
