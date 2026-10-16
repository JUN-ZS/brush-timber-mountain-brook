#!/usr/bin/env python3
"""Historical source-reported QQQ put IV versus realized volatility; research diagnostic only."""
from __future__ import annotations
import argparse,csv,json,math,statistics,sys,datetime
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import qqq_put_ratio_exit_study_v1 as base

HORIZONS=(3,5,10,20,30)
BUCKETS=("IV_LT20","IV_20_30","IV_GTE30","UNKNOWN")

def num(v):
    try:
        x=float(v);return x if math.isfinite(x) else None
    except (TypeError,ValueError):return None

def dist(values):
    xs=sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    def q(p):return round(xs[min(len(xs)-1,max(0,int(round((len(xs)-1)*p))))],4) if xs else None
    return {"observations":len(xs),"mean":round(statistics.mean(xs),4) if xs else None,
            "median":round(statistics.median(xs),4) if xs else None,"p05":q(.05),"p95":q(.95)}

def rate(values,pred):
    xs=[float(v) for v in values if v is not None and math.isfinite(float(v))]
    hit=sum(bool(pred(v)) for v in xs)
    return {"events":hit,"observations":len(xs),"probability_pct":round(100*hit/len(xs),3) if xs else None}

def iv_bucket(iv):
    if iv is None:return "UNKNOWN"
    if iv<20:return "IV_LT20"
    if iv<30:return "IV_20_30"
    return "IV_GTE30"

def select_atm_put_iv(rows:list[dict[str,Any]],day:str,spot:float|None,target_dte:int=30)->dict[str,Any]|None:
    """Select same-day standard QQQ put IV; never forward-fill or substitute model IV."""
    if spot is None or not math.isfinite(float(spot)) or float(spot)<=0:return None
    candidates=[]
    for row in rows:
        if not base.standard_put_identity(row) or base.as_day(row.get("date"))!=day:continue
        try:
            dte=(datetime.date.fromisoformat(base.as_day(row.get("expiration")))-datetime.date.fromisoformat(day)).days
        except (ValueError,TypeError):continue
        if not 20<=dte<=40:continue
        delta=num(row.get("delta"));strike=num(row.get("strike"))
        bid,ask=num(row.get("bid")),num(row.get("ask"))
        bs,asz=num(row.get("bid_size")),num(row.get("ask_size"))
        raw_iv=num(row.get("implied_volatility"))
        if delta is None or strike is None or not .35<=abs(delta)<=.65:continue
        if bid is None or ask is None or bid<0 or ask<=0 or bid>ask:continue
        if bs is None or asz is None or bs<1 or asz<1:continue
        if raw_iv is None or raw_iv<=0 or raw_iv>300:continue
        iv=raw_iv/100.0 if raw_iv>3 else raw_iv
        unit="PERCENT_POINTS_NORMALIZED" if raw_iv>3 else "DECIMAL"
        if not 0<iv<=3:continue
        mid=(bid+ask)/2
        candidates.append({"date":day,"contract_id":base.contract_id(row),"expiry":base.as_day(row.get("expiration")),
            "dte":dte,"strike":strike,"abs_delta":abs(delta),"iv_decimal":iv,"iv_pct":100*iv,
            "iv_source_format":unit,"bid":bid,"ask":ask,"bid_size":bs,"ask_size":asz,
            "spread_pct":100*(ask-bid)/mid if mid>0 else None,
            "open_interest":num(row.get("open_interest")) or 0,"spot":float(spot)})
    if not candidates:return None
    return min(candidates,key=lambda x:(abs(x["dte"]-target_dte),abs(x["abs_delta"]-.5),
        x["spread_pct"] if x["spread_pct"] is not None else math.inf,
        -min(x["bid_size"],x["ask_size"]),-x["open_interest"],x["contract_id"]))

def build_profile(expected:list[str],spots:dict[str,Any],iv_by_day:dict[str,dict[str,Any]]):
    bars=[{"date":day,"close":num((spots.get(day) or {}).get("raw_close")),"iv":iv_by_day.get(day)} for day in expected]
    daily=[None]
    for i in range(1,len(bars)):
        a,b=bars[i-1]["close"],bars[i]["close"]
        daily.append(math.log(b/a) if a and b and a>0 and b>0 else None)
    rv20=[None]*len(bars)
    for i in range(20,len(bars)):
        xs=daily[i-19:i+1]
        if len(xs)==20 and not any(v is None for v in xs):rv20[i]=statistics.stdev(xs)*math.sqrt(252)*100
    ivvals=[];gaps=[];above=matched=0
    for i,b in enumerate(bars):
        row=b["iv"]
        if not isinstance(row,dict):continue
        iv=num(row.get("iv_pct"))
        if iv is None or iv<=0:continue
        ivvals.append(iv)
        if rv20[i] is not None:gaps.append(iv-rv20[i]);matched+=1;above+=int(iv>rv20[i])
    matched_rv20=[rv20[i] for i,b in enumerate(bars) if rv20[i] is not None and isinstance(b["iv"],dict)]
    by_horizon=[]
    for h in HORIZONS:
        groups=defaultdict(list);hits=defaultdict(int);trials=defaultdict(int)
        for i in range(len(bars)-h):
            a,b=bars[i],bars[i+h];row=a["iv"]
            if a["close"] is None or b["close"] is None or a["close"]<=0 or b["close"]<=0 or not isinstance(row,dict):continue
            iv=num(row.get("iv_pct"))
            if iv is None or iv<=0:continue
            bucket=iv_bucket(iv);ret=100*(b["close"]/a["close"]-1);move=iv*math.sqrt(h/252)
            groups[bucket].append({"ret":ret,"move":move,"iv":iv});trials[bucket]+=1;hits[bucket]+=int(abs(ret)>=move)
        for bucket in BUCKETS:
            xs=groups.get(bucket,[]);rets=[x["ret"] for x in xs]
            ratios=[abs(x["ret"])/x["move"] for x in xs if x["move"]>0]
            by_horizon.append({"horizon_sessions":h,"entry_iv_bucket":bucket,**dist(rets),
                "p_gain_ge_3pct":rate(rets,lambda x:x>=3),"p_gain_ge_5pct":rate(rets,lambda x:x>=5),
                "p_loss_le_minus3pct":rate(rets,lambda x:x<=-3),"p_loss_le_minus5pct":rate(rets,lambda x:x<=-5),
                "p_loss_le_minus10pct":rate(rets,lambda x:x<=-10),
                "median_entry_iv_pct":round(statistics.median([x["iv"] for x in xs]),4) if xs else None,
                "one_sigma_expected_move_pct":round(statistics.median([x["iv"] for x in xs])*math.sqrt(h/252),4) if xs else None,
                "observed_abs_move_ge_one_sigma_pct":round(100*hits[bucket]/trials[bucket],3) if trials[bucket] else None,
                "median_abs_move_over_one_sigma":round(statistics.median(ratios),4) if ratios else None})
    daily_rows=[]
    for i,b in enumerate(bars):
        row=b["iv"]
        if not isinstance(row,dict):continue
        rec={k:row.get(k) for k in ("date","contract_id","expiry","dte","strike","abs_delta","iv_decimal","iv_pct","iv_source_format","bid","ask","bid_size","ask_size","spread_pct","spot")}
        rec["rv20_annualized_pct"]=round(rv20[i],4) if rv20[i] is not None else None
        rec["iv_minus_rv20_pct_points"]=round(row["iv_pct"]-rv20[i],4) if rv20[i] is not None else None
        rec["iv_above_rv20"]=(row["iv_pct"]>rv20[i]) if rv20[i] is not None else None
        daily_rows.append(rec)
    return {"research_id":"QQQ_PUT_IV_VS_REALIZED_VOLATILITY_V1","status":"SOURCE_REPORTED_IV_DIAGNOSTIC_NOT_OPTION_PNL_PROBABILITY",
        "expected_sessions":len(expected),"selected_iv_sessions":len(daily_rows),
        "quote_coverage_pct":round(100*len(daily_rows)/len(expected),3) if expected else None,
        "first_iv_date":min((x["date"] for x in daily_rows),default=None),"last_iv_date":max((x["date"] for x in daily_rows),default=None),
        "median_source_iv_pct":round(statistics.median(ivvals),4) if ivvals else None,
        "matched_iv_rv20_sessions":matched,"median_rv20_pct":round(statistics.median(matched_rv20),4) if matched_rv20 else None,
        "median_iv_minus_rv20_pct_points":round(statistics.median(gaps),4) if gaps else None,
        "iv_above_rv20_pct":round(100*above/matched,3) if matched else None,"iv_minus_rv20_distribution":dist(gaps),
        "conditional_forward_results":by_horizon,"daily_selected_quote_audit_rows":daily_rows,
        "limitations":["Forward windows overlap; these are historical descriptive frequencies, not independent-trial forecasts.",
            "The source-reported IV is not exchange-authenticated and may be derived from the same quote marks/midpoint.",
            "Annualized IV times sqrt(h/252) is a reference one-sigma move, not a probability the option strategy wins."]}

def run(out:Path):
    sys.path.insert(0,str(ROOT/"research"/"qqq_hybrid_operator_terminal_v1"))
    import full_history_qqq_quote_audit as audit
    import qqq_far_call_quote_replay as replay
    cache=ROOT/".cache"/"qqq-options-full-history"
    integrity,universe,spots,expected=audit.build_inputs(cache)
    expected=sorted(d for d in expected if base.START_DATE<=d<=base.REQUESTED_END_DATE)
    files=[];pins={}
    for spec in audit.ANNUAL_FILES:
        p,pin=audit.download_verified(spec,cache);files.append(p);pins[spec["name"]]=pin
    chains=iter(replay.iter_qqq_chain_days(files));current=next(chains,None);ivs={}
    for day in expected:
        while current is not None and current[0]<day:current=next(chains,None)
        rows=[]
        if current is not None and current[0]==day:rows=current[1];current=next(chains,None)
        iv=select_atm_put_iv(rows,day,num((spots.get(day) or {}).get("raw_close")))
        if iv is not None:ivs[day]=iv
    report=build_profile(expected,spots,ivs)
    report["integrity"]=integrity;report["option_file_integrity"]=pins;report["missing_terminal_sessions"]=11
    out.mkdir(parents=True,exist_ok=True)
    (out/"qqq_put_iv_realized_vol_study_v1.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    rows=report["daily_selected_quote_audit_rows"]
    fields=["date","contract_id","expiry","dte","strike","abs_delta","iv_decimal","iv_pct","iv_source_format",
            "bid","ask","bid_size","ask_size","spread_pct","open_interest","spot","rv20_annualized_pct",
            "iv_minus_rv20_pct_points","iv_above_rv20"]
    with (out/"qqq_put_iv_realized_vol_daily_v1.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    lines=["# QQQ Source IV versus Realized Volatility — V1","",
       f"**Status:** {report['status']}; historical EOD source-IV diagnostic, not option strategy P&L.",
       f"**Coverage:** {report['selected_iv_sessions']}/{report['expected_sessions']} sessions ({report['quote_coverage_pct']}%), {report['first_iv_date']} to {report['last_iv_date']}.",
       f"**Median IV:** {report['median_source_iv_pct']}%; **median IV−RV20:** {report['median_iv_minus_rv20_pct_points']} points; **IV>RV20:** {report['iv_above_rv20_pct']}% of {report['matched_iv_rv20_sessions']} matched sessions.",
       "Selection is same-day standard QQQ put, 20–40 calendar DTE (target 30), |delta| 0.35–0.65 (target 0.50), valid two-sided quote and positive displayed size. Missing IV is not filled.",
       "Public mirror IV may be midpoint-derived; it is not exchange-authenticated and does not prove a fill.","",
       "| Horizon | Entry IV band | N | Median return | P(+3%) | P(+5%) | P(≤−3%) | P(≤−5%) | P(≤−10%) | Absolute move ≥ IV 1σ | Median absolute move / IV 1σ |",
       "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in report["conditional_forward_results"]:
        lines.append(f"| {x['horizon_sessions']} | {x['entry_iv_bucket']} | {x['observations']} | {x['median']}% | {x['p_gain_ge_3pct']['probability_pct']}% | {x['p_gain_ge_5pct']['probability_pct']}% | {x['p_loss_le_minus3pct']['probability_pct']}% | {x['p_loss_le_minus5pct']['probability_pct']}% | {x['p_loss_le_minus10pct']['probability_pct']}% | {x['observed_abs_move_ge_one_sigma_pct']}% | {x['median_abs_move_over_one_sigma']} |")
    lines+=["","## Limits",""]+["- "+x for x in report["limitations"]]
    (out/"qqq_put_iv_realized_vol_study_v1.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,default=ROOT/"artifacts"/"qqq_put_ratio_exit_study_v1")
    args=parser.parse_args();r=run(args.out)
    print(json.dumps({k:r[k] for k in ("research_id","status","selected_iv_sessions","expected_sessions","quote_coverage_pct","first_iv_date","last_iv_date","median_source_iv_pct","median_iv_minus_rv20_pct_points","iv_above_rv20_pct")},indent=2))
    print((args.out/"qqq_put_iv_realized_vol_study_v1.md").read_text(encoding="utf-8"))
if __name__=="__main__":main()
