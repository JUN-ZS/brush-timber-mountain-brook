#!/usr/bin/env python3
"""SHA-pinned source/quote-quality probe of public QQQ EOD option chains; not a backtest."""
from __future__ import annotations
import hashlib, json, tempfile, urllib.request
from datetime import date, datetime
from pathlib import Path
from math import erf, exp, log, sqrt
from statistics import NormalDist

BASE = "https://raw.githubusercontent.com/anahatsingh-ui/options-dataset-hist/main/qqq"
FILES = {
    "options_2020.parquet": {"url": BASE+"/options_2020.parquet", "size": 59412637,
        "sha": "9d7abe1144c55e0091d28eca61deec4ac72393a5", "dates": ["2020-01-15", "2020-03-16", "2020-06-08", "2020-10-30"]},
    "options_2024.parquet": {"url": BASE+"/options_2024.parquet", "size": 82434832,
        "sha": "40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3", "dates": ["2024-02-01", "2024-04-15", "2024-08-05", "2024-11-06"]},
}
UNDERLYING = {"url": BASE+"/underlying_prices.parquet", "size": 332454,
    "sha": "f3a892bc4c88c692900b5c0071322c6db408996a"}
COLUMNS = ["contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size",
           "volume","open_interest","date","implied_volatility","delta"]
UNIVERSE_PATH = Path("src/data/universe.json")
UNIVERSE_GIT_BLOB_SHA = "43c1b3053d17b278cfc01bb0b87e41679f3e85c9"
MODEL_SOURCE_PATH = Path("research/qqq_hybrid_dynamic_deployment_v1_1_replay.py")
MODEL_SOURCE_GIT_BLOB_SHA = "ac74b3812c826ad491fb829108f26397322e45eb"

def git_blob_sha(path, expected_size):
    h=hashlib.sha1(); h.update(f"blob {expected_size}\0".encode("ascii"))
    with open(path,"rb") as handle:
        for block in iter(lambda: handle.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def download(spec, name, folder):
    path=Path(folder)/name
    if path.exists() and path.stat().st_size==spec["size"] and git_blob_sha(path,spec["size"])==spec["sha"]:
        return path,{"status":"CACHED_HASH_VERIFIED","bytes":spec["size"],"git_blob_sha":spec["sha"]}
    path.unlink(missing_ok=True)
    req=urllib.request.Request(spec["url"],headers={"User-Agent":"qqq-hybrid-eod-audit/1.0"})
    digest=hashlib.sha1(); digest.update(f"blob {spec['size']}\0".encode("ascii")); total=0
    with urllib.request.urlopen(req,timeout=90) as resp, open(path,"wb") as out:
        while True:
            block=resp.read(1024*1024)
            if not block: break
            total+=len(block); out.write(block); digest.update(block)
    actual=digest.hexdigest()
    if total!=spec["size"] or actual!=spec["sha"]:
        path.unlink(missing_ok=True)
        raise ValueError(f"{name} size/SHA mismatch: {total}/{spec['size']} bytes, {actual}/{spec['sha']}")
    return path,{"status":"DOWNLOADED_HASH_VERIFIED","bytes":total,"git_blob_sha":actual}

def as_day(v):
    if v is None: return ""
    return v.isoformat()[:10] if hasattr(v,"isoformat") else str(v)[:10]

def day_literals(pa, dtype, strings):
    if pa.types.is_date(dtype): return [date.fromisoformat(s) for s in strings]
    if pa.types.is_timestamp(dtype): return [datetime.fromisoformat(s+"T00:00:00") for s in strings]
    return strings

def numeric(v):
    try:
        n=float(v)
        return n if n==n and abs(n)!=float("inf") else None
    except (TypeError,ValueError): return None

def blob_sha_bytes(payload):
    h=hashlib.sha1()
    h.update(f"blob {len(payload)}\0".encode("ascii"))
    h.update(payload)
    return h.hexdigest()

def bsm_call(S,K,T,r,sigma,q=0.0):
    if T<=1/365 or sigma<1e-8:
        return max(S-K,0.0)
    vs=sigma*sqrt(max(T,1e-8))
    d1=(log(S/K)+(r-q+0.5*sigma*sigma)*T)/vs
    d2=d1-vs
    return S*exp(-q*T)*0.5*(1+erf(d1/sqrt(2)))-K*exp(-r*T)*0.5*(1+erf(d2/sqrt(2)))

def model_qqq_quote(S,vix,T=30/365):
    """Mirror quoteCC(..., kind='qqq') from the SHA-pinned research source."""
    iv=min(max(1.08*(vix/100),0.1),0.9)
    sigS,sigL=iv*0.95,iv*0.90
    q,r=0.004,0.03
    def strike_for_delta(target,sigma):
        p=min(max(target*exp(q*T),1e-6),1-1e-6)
        d1=NormalDist().inv_cdf(p)
        vs=sigma*sqrt(T)
        return max(S*exp(-(d1*vs-(r-q+0.5*sigma*sigma)*T)),1e-6)
    ks=strike_for_delta(0.16,sigS)
    kl=strike_for_delta(0.08,sigL)
    if kl<=ks: kl=ks*1.06
    half=min(max(0.025+0.08*max(vix/100-0.16,0),0.02),0.1)
    short_mid=bsm_call(S,ks,T,r,sigS,q)
    long_mid=bsm_call(S,kl,T,r,sigL,q)
    raw_credit=short_mid*(1-half)-long_mid*(1+half)
    return {"spot_input":S,"vix_input":vix,"T_years":T,"ivQqq":iv,"short_sigma":sigS,"long_sigma":sigL,
            "short_target_delta":0.16,"long_target_delta":0.08,"short_target_strike":ks,
            "long_target_strike":kl,"width":kl-ks,"half_spread_fraction":half,
            "short_mid_model":short_mid,"long_mid_model":long_mid,
            "credit_before_source_floor":raw_credit,"premium_used_by_quoteCC":max(raw_credit,1e-4)}

def model_credit_at_listed_strikes(S,vix,short_strike,long_strike,T):
    iv=min(max(1.08*(vix/100),0.1),0.9)
    sigS,sigL=iv*0.95,iv*0.90
    half=min(max(0.025+0.08*max(vix/100-0.16,0),0.02),0.1)
    short_mid=bsm_call(S,short_strike,T,0.03,sigS,0.004)
    long_mid=bsm_call(S,long_strike,T,0.03,sigL,0.004)
    return {"short_sigma":sigS,"long_sigma":sigL,"short_model_mid":short_mid,"long_model_mid":long_mid,
            "model_bid_for_short":short_mid*(1-half),"model_ask_for_wing":long_mid*(1+half),
            "model_mid_credit":short_mid-long_mid,
            "model_conservative_credit":short_mid*(1-half)-long_mid*(1+half)}

def model_credit_using_chain_ivs(S,vix,short_strike,long_strike,T,short_iv,wing_iv):
    """Diagnostic repricing using source-reported per-leg IV; this is not a fill model."""
    s_iv,l_iv=numeric(short_iv),numeric(wing_iv)
    if s_iv is None or l_iv is None or s_iv<=0 or l_iv<=0:
        return {"status":"CHAIN_IV_MISSING","short_iv":s_iv,"wing_iv":l_iv}
    half=min(max(0.025+0.08*max(vix/100-0.16,0),0.02),0.1)
    short_mid=bsm_call(S,short_strike,T,0.03,s_iv,0.004)
    wing_mid=bsm_call(S,long_strike,T,0.03,l_iv,0.004)
    return {
        "status":"CHAIN_IV_DIAGNOSTIC",
        "short_iv":s_iv,
        "wing_iv":l_iv,
        "model_short_mid":short_mid,
        "model_wing_mid":wing_mid,
        "model_mid_credit":short_mid-wing_mid,
        "model_short_bid_using_model_halfspread":short_mid*(1-half),
        "model_wing_ask_using_model_halfspread":wing_mid*(1+half),
        "model_conservative_credit_using_chain_ivs":short_mid*(1-half)-wing_mid*(1+half),
        "half_spread_still_model_derived":half,
        "caveat":"The input IV fields come from a public EOD mirror and are not independently verified as exchange-authoritative. The spread haircut remains model-derived."
    }

def standard_strike_grid(value):
    x=numeric(value)
    return x is not None and abs(x*2-round(x*2))<1e-5

def nearest_quote_model_pairs(rows,day,model_geom,raw_close,repo_adj_close,vix):
    """Pair real quotes at the nearest 30-calendar-day expiration and listed strikes."""
    dated=[]
    for row in rows:
        if str(row.get("type","")).lower() not in ("c","call"): continue
        try: dte=(date.fromisoformat(as_day(row.get("expiration")))-date.fromisoformat(day)).days
        except ValueError: continue
        bid,ask=numeric(row.get("bid")),numeric(row.get("ask"))
        strike=numeric(row.get("strike"))
        if 20<=dte<=40 and bid is not None and ask is not None and bid>0 and ask>0 and bid<=ask and standard_strike_grid(strike):
            dated.append((dte,row))
    if not dated:
        return {"status":"NO_VALID_STANDARD_GRID_CALLS_WITH_20_40_DTE"}
    expiries={}
    for dte,row in dated: expiries.setdefault(as_day(row.get("expiration")),{"dte":dte,"rows":[]})["rows"].append(row)
    expiry=min(expiries, key=lambda e:(abs(expiries[e]["dte"]-30),-len(expiries[e]["rows"]),e))
    dte=expiries[expiry]["dte"]
    eligible=expiries[expiry]["rows"]
    def valid_quote(row):
        bid,ask=numeric(row.get("bid")),numeric(row.get("ask"))
        return bid is not None and ask is not None and bid>0 and ask>0 and bid<=ask
    def select_pair(target):
        short_target=target["short_target_strike"]
        long_target=target["long_target_strike"]
        shorts=sorted((r for r in eligible if valid_quote(r)),key=lambda r:(
            abs(numeric(r.get("strike"))-short_target),
            abs(abs(numeric(r.get("delta")) or 0)-0.16),
            (numeric(r.get("ask")) or 0)-(numeric(r.get("bid")) or 0)))
        if not shorts: return None
        short=shorts[0]
        ks=numeric(short.get("strike"))
        wings=[r for r in eligible if numeric(r.get("strike"))>ks and valid_quote(r)]
        if not valid_quote(short) or not wings: return None
        wings.sort(key=lambda r:(
            abs(numeric(r.get("strike"))-long_target),
            abs(abs(numeric(r.get("delta")) or 0)-0.08),
            (numeric(r.get("ask")) or 0)-(numeric(r.get("bid")) or 0)))
        wing=wings[0]
        kl=numeric(wing.get("strike"))
        sb,sa=numeric(short.get("bid")),numeric(short.get("ask"))
        wb,wa=numeric(wing.get("bid")),numeric(wing.get("ask"))
        short_iv=numeric(short.get("implied_volatility"))
        wing_iv=numeric(wing.get("implied_volatility"))
        width=kl-ks
        exec_credit=sb-wa
        mid_credit=(sb+sa)/2-(wb+wa)/2
        t_actual=max(dte/365,1/365)
        model_repo=model_credit_at_listed_strikes(repo_adj_close,vix,ks,kl,t_actual)
        model_raw=model_credit_at_listed_strikes(raw_close,vix,ks,kl,t_actual)
        return {
            "expiry":expiry,"calendar_dte":dte,"short_contract_id":short.get("contract_id"),
            "short_strike":ks,"short_bid":sb,"short_ask":sa,"short_delta":numeric(short.get("delta")),
            "short_implied_volatility":short_iv,
            "short_volume":short.get("volume"),"short_open_interest":short.get("open_interest"),
            "wing_contract_id":wing.get("contract_id"),"wing_strike":kl,"wing_bid":wb,"wing_ask":wa,
            "wing_delta":numeric(wing.get("delta")),"wing_implied_volatility":wing_iv,
            "wing_volume":wing.get("volume"),"wing_open_interest":wing.get("open_interest"),"strike_width":width,
            "observed_credit_bid_minus_wing_ask":exec_credit,
            "observed_credit_mid_minus_mid":mid_credit,
            "observed_credit_is_valid_positive":0<exec_credit<width,
            "observed_max_loss_per_standard_100_multiplier":(width-exec_credit)*100 if 0<exec_credit<width else None,
            "spread_pct_of_short_mid":round((sa-sb)/((sa+sb)/2)*100,2) if sa+sb>0 else None,
            "model_using_repo_adjusted_spot_at_same_listed_strikes":model_repo,
            "model_using_raw_close_at_same_listed_strikes":model_raw,
            "model_iv_proxy_short_sigma":model_repo["short_sigma"],
            "model_iv_proxy_wing_sigma":model_repo["long_sigma"],
            "model_to_chain_iv_ratio_short":model_repo["short_sigma"]/short_iv if short_iv is not None and short_iv>0 else None,
            "model_to_chain_iv_ratio_wing":model_repo["long_sigma"]/wing_iv if wing_iv is not None and wing_iv>0 else None,
            "model_using_repo_spot_and_chain_leg_ivs":model_credit_using_chain_ivs(repo_adj_close,vix,ks,kl,t_actual,short_iv,wing_iv),
            "model_using_raw_close_and_chain_leg_ivs":model_credit_using_chain_ivs(raw_close,vix,ks,kl,t_actual,short_iv,wing_iv),
            "repo_spot_model_credit_minus_observed_executable":model_repo["model_conservative_credit"]-exec_credit,
            "raw_close_model_credit_minus_observed_executable":model_raw["model_conservative_credit"]-exec_credit,
            "notice":"No contract-root/deliverable verification is present in this EOD table; standard 100 multiplier remains an assumption."
        }
    pairs={}
    for label,geom in model_geom.items():
        pairs[label]=select_pair(geom)
    return {"status":"MATCHED_NEAREST_20_40_DTE_EXPIRY","selected_expiry":expiry,"calendar_dte":dte,
            "eligible_standard_grid_call_rows_in_expiry":len(eligible),"model_target_nearest_pairs":pairs,
            "strike_grid_rule":"half-dollar/integer strike only; this is a screen, not OCC contract-root proof"}


def read_dates(path, dates, pa, ds, columns=None):
    data=ds.dataset(str(path),format="parquet"); schema=data.schema
    if "date" not in schema.names: raise ValueError("Parquet missing date column")
    pred=ds.field("date").isin(day_literals(pa,schema.field("date").type,dates))
    if "symbol" in schema.names: pred=pred & (ds.field("symbol")=="QQQ")
    cols=[c for c in (columns or schema.names) if c in schema.names]
    return data.to_table(columns=cols,filter=pred).to_pylist()

def inspect_day(day, rows):
    calls=[r for r in rows if str(r.get("type","")).lower() in ("c","call")]
    valid=[]; candidates=[]
    for r in rows:
        bid,ask=numeric(r.get("bid")),numeric(r.get("ask"))
        if bid is not None and ask is not None and bid>0 and ask>0 and bid<=ask: valid.append(r)
    for r in calls:
        try: dte=(date.fromisoformat(as_day(r.get("expiration")))-date.fromisoformat(day)).days
        except ValueError: continue
        bid,ask,delta=numeric(r.get("bid")),numeric(r.get("ask")),numeric(r.get("delta"))
        if (30<=dte<=60 and delta is not None and .03<=abs(delta)<=.10 and
            bid is not None and ask is not None and bid>0 and ask>0 and bid<=ask):
            mid=(bid+ask)/2
            candidates.append({"contract_id":r.get("contract_id"),"expiration":as_day(r.get("expiration")),
                "dte_calendar":dte,"strike":r.get("strike"),"bid":bid,"ask":ask,"delta":delta,
                "spread":round(ask-bid,4),"spread_pct_of_mid":round((ask-bid)/mid*100,2) if mid else None,
                "iv":r.get("implied_volatility"),"volume":r.get("volume"),"open_interest":r.get("open_interest")})
    candidates.sort(key=lambda r:(abs(abs(r["delta"])-.06),abs(r["dte_calendar"]-45),r["spread"]))
    return {"date":day,"status":"ROWS_FOUND" if rows else "NO_ROWS_RETURNED","option_rows":len(rows),
        "call_rows":len(calls),"put_rows":len(rows)-len(calls),
        "positive_non_crossed_two_sided_rows":len(valid),
        "valid_two_sided_quote_pct":round(100*len(valid)/len(rows),2) if rows else None,
        "call_candidates_30_60_dte_abs_delta_0p03_0p10":len(candidates),"candidate_samples":candidates[:5]}

def main():
    report={"source":"anahatsingh-ui/options-dataset-hist","source_class":"PUBLIC_EOD_CHAIN_PRESERVATION_MIRROR",
        "sample_design":"Eight preselected development diagnostics across baseline, shock, rebound/volatility and recovery regimes; not blind OOS and not a strategy backtest",
        "quote_convention":"README says 4:00 PM US Eastern; not a 15:45 or intraday fill",
        "role":"QQQ layer quote-quality cross-check only; does not cover VXX",
        "trade_replay_approved":False,"file_integrity":{},"results":[],"overall":"INCONCLUSIVE"}
    try:
        import pyarrow as pa
        import pyarrow.dataset as ds
        with tempfile.TemporaryDirectory(prefix="qqq-eod-audit-") as temp:
            local={}
            for name,spec in FILES.items():
                local[name],report["file_integrity"][name]=download(spec,name,temp)
            underlying,report["file_integrity"]["underlying_prices.parquet"]=download(UNDERLYING,"underlying_prices.parquet",temp)
            dates=sorted({d for spec in FILES.values() for d in spec["dates"]})
            raw_rows={}
            for name,spec in FILES.items():
                rows=read_dates(local[name],spec["dates"],pa,ds,COLUMNS)
                by={d:[] for d in spec["dates"]}
                for row in rows:
                    d=as_day(row.get("date"))
                    if d in by: by[d].append(row)
                for d in spec["dates"]: raw_rows[d]=by[d]
                report["results"].extend(inspect_day(d,by[d]) for d in spec["dates"])
            spots=read_dates(underlying,dates,pa,ds)
            smap={as_day(r.get("date")):r for r in spots}
            report["underlying_spots"]={d:({"close":numeric(smap[d].get("close")),
                "adjusted_close":numeric(smap[d].get("adjusted_close")),"volume":smap[d].get("volume"),
                "split_coefficient":smap[d].get("split_coefficient")} if d in smap else None) for d in dates}
            universe_path=Path("src/data/universe.json")
            model_path=MODEL_SOURCE_PATH
            source_integrity={}
            universe_bytes=universe_path.read_bytes()
            model_bytes=model_path.read_bytes()
            source_integrity["src/data/universe.json"]={"bytes":len(universe_bytes),
                "git_blob_sha":blob_sha_bytes(universe_bytes),
                "status":"HASH_VERIFIED" if blob_sha_bytes(universe_bytes)==UNIVERSE_GIT_BLOB_SHA else "HASH_MISMATCH"}
            source_integrity[str(MODEL_SOURCE_PATH)]={"bytes":len(model_bytes),
                "git_blob_sha":blob_sha_bytes(model_bytes),
                "status":"HASH_VERIFIED" if blob_sha_bytes(model_bytes)==MODEL_SOURCE_GIT_BLOB_SHA else "HASH_MISMATCH"}
            report["model_source_integrity"]=source_integrity
            if all(item["status"]=="HASH_VERIFIED" for item in source_integrity.values()):
                universe=json.loads(universe_bytes.decode("utf-8"))
                position={d:i for i,d in enumerate(universe["dates"])}
                report["model_price_alignment"]=[]
                for day in dates:
                    i=position.get(day)
                    spotrow=smap.get(day)
                    if i is None or spotrow is None:
                        report["model_price_alignment"].append({"date":day,"status":"MISSING_UNIVERSE_OR_RAW_CLOSE"})
                        continue
                    repo_spot=numeric(universe["c"]["QQQ"][i])
                    vix=numeric(universe["c"]["VIX"][i])
                    raw_close=numeric(spotrow.get("close"))
                    adj_close=numeric(spotrow.get("adjusted_close"))
                    if None in (repo_spot,vix,raw_close):
                        report["model_price_alignment"].append({"date":day,"status":"MISSING_SPOT_OR_VIX"})
                        continue
                    repo_geom=model_qqq_quote(repo_spot,vix)
                    raw_geom=model_qqq_quote(raw_close,vix)
                    record={
                        "date":day,"universe_source":universe.get("source"),
                        "model_source_file_sha":MODEL_SOURCE_GIT_BLOB_SHA,
                        "repo_backtest_qqq_input":repo_spot,"public_source_raw_qqq_close":raw_close,
                        "public_source_adjusted_qqq_close":adj_close,
                        "repo_spot_vs_raw_close_pct":round((repo_spot/raw_close-1)*100,4),
                        "vix_from_same_repo_universe":vix,
                        "quoteCC_model_using_repo_spot_adjusted_series":repo_geom,
                        "quoteCC_model_using_public_raw_close":raw_geom,
                        "short_target_strike_shift_repo_minus_raw":repo_geom["short_target_strike"]-raw_geom["short_target_strike"],
                        "long_target_strike_shift_repo_minus_raw":repo_geom["long_target_strike"]-raw_geom["long_target_strike"],
                        "model_credit_shift_repo_minus_raw":repo_geom["premium_used_by_quoteCC"]-raw_geom["premium_used_by_quoteCC"],
                        "market_chain_match":nearest_quote_model_pairs(raw_rows[day],day,
                            {"repo_adjusted_spot":repo_geom,"raw_close_spot":raw_geom},
                            raw_close,repo_spot,vix),
                        "interpretation":"Diagnostic only: EOD chain mirror is QQQ-only; EOD quotes are not guaranteed fills. Historical share-price adjustment is suitable for total-return stock accounting but is not interchangeable with raw nominal spot used for option strikes/payoffs."
                    }
                    report["model_price_alignment"].append(record)
            else:
                report["model_price_alignment"]={"status":"MODEL_SOURCE_HASH_MISMATCH","detail":"No model-to-chain comparison performed because source series / replay code did not match pinned revisions."}
        integrity=all(x.get("status") in ("DOWNLOADED_HASH_VERIFIED","CACHED_HASH_VERIFIED") for x in report["file_integrity"].values()) and all(x.get("status")=="HASH_VERIFIED" for x in report.get("model_source_integrity",{}).values())
        hits=sum(x["status"]=="ROWS_FOUND" for x in report["results"])
        report["integrity_ok"]=integrity
        report["overall"]=("SAMPLE_DATES_HAVE_QQQ_CHAIN_ROWS" if integrity and hits==len(report["results"]) else
            "PARTIAL_QQQ_CHAIN_COVERAGE" if integrity and hits>0 else
            "NO_QQQ_ROWS_ON_TEST_DATES" if integrity else "INCONCLUSIVE_INTEGRITY_OR_READ")
    except Exception as exc:
        report["overall"]="INCONCLUSIVE_DOWNLOAD_OR_PARQUET_READ"
        report["error"]=type(exc).__name__+": "+str(exc)[:400]
    print("QQQ_PUBLIC_EOD_AUDIT_BEGIN")
    print(json.dumps(report,indent=2,sort_keys=True))
    print("QQQ_PUBLIC_EOD_AUDIT_END")
    return 0

if __name__=="__main__": raise SystemExit(main())
