#!/usr/bin/env python3
"""QQQ Put Ratio NAV Exit Matrix V2: N=1..6, both directions, empirical time/vol context."""
from __future__ import annotations
import argparse, csv, importlib.util, json, math, statistics, sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE_PATH=HERE/"qqq_put_ratio_exit_study_v1.py"
SPEC=importlib.util.spec_from_file_location("qqq_ratio_exit_base_v1",BASE_PATH)
if SPEC is None or SPEC.loader is None: raise RuntimeError("Cannot load pinned v1 helpers")
BASE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(BASE)
START_DATE=BASE.START_DATE; SOURCE_END_DATE=BASE.SOURCE_END_DATE; REQUESTED_END_DATE=BASE.REQUESTED_END_DATE
MULTIPLIER=BASE.CONTRACT_MULTIPLIER
NAVS=(100000.0,1000000.0); BUDGET_PCTS=(0.5,1.0,2.0)
HORIZONS=(1,3,5,10,20,30,45); RV_WINDOWS=(10,20,30,60)
COST_CASES=({"name":"BASE_COST","slippage":0.05,"commission":0.65},{"name":"ADVERSE_COST","slippage":0.10,"commission":0.65})


def quantile(values:list[float],p:float)->float|None:
    xs=sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    return round(xs[min(len(xs)-1,max(0,int(round((len(xs)-1)*p))))],4) if xs else None

def distribution(values:list[float])->dict[str,Any]:
    xs=[float(x) for x in values if x is not None and math.isfinite(float(x))]
    return {"observations":len(xs),"mean":round(statistics.mean(xs),4) if xs else None,
            "median":round(statistics.median(xs),4) if xs else None,"p05":quantile(xs,.05),
            "p25":quantile(xs,.25),"p75":quantile(xs,.75),"p90":quantile(xs,.90),"p95":quantile(xs,.95)}

def event_rate(values:list[float],predicate)->dict[str,Any]:
    xs=[float(x) for x in values if x is not None and math.isfinite(float(x))]
    hits=sum(1 for x in xs if predicate(x))
    return {"events":hits,"observations":len(xs),"probability_pct":round(100*hits/len(xs),3) if xs else None}

def vix_bucket(vix:float|None)->str:
    if vix is None:return "UNKNOWN"
    if vix<15:return "VIX_LT15"
    if vix<25:return "VIX_15_25"
    if vix<35:return "VIX_25_35"
    return "VIX_GTE35"

def expiry_pnl(cash:float,n_long:int,n_short:int,long_strike:float,short_strike:float,spot:float)->float:
    return cash+MULTIPLIER*(n_long*max(long_strike-spot,0.0)-n_short*max(short_strike-spot,0.0))

def entry_cash_per_package(trade:dict[str,Any],slip:float,commission:float)->float:
    q=trade["entry_quotes"]; nl=int(trade["n_long"]); ns=int(trade["n_short"])
    return MULTIPLIER*(ns*(float(q["short"]["bid"])-slip)-nl*(float(q["long"]["ask"])+slip))-(nl+ns)*commission

def terminal_risk_per_package(trade:dict[str,Any],slip:float,commission:float)->dict[str,Any]:
    cash=entry_cash_per_package(trade,slip,commission)
    nl,ns=int(trade["n_long"]),int(trade["n_short"])
    kl,ks=float(trade["long_strike"]),float(trade["short_strike"])
    points=sorted(set((0.0,min(kl,ks),max(kl,ks),max(kl,ks)+1.0)))
    pnls=[expiry_pnl(cash,nl,ns,kl,ks,s) for s in points]
    return {"entry_cash_per_package_usd":round(cash,2),"terminal_max_loss_usd":round(max(0.0,-min(pnls)),2),
            "terminal_max_gain_usd":round(max(0.0,max(pnls)),2),
            "pnl_if_qqq_zero_usd":round(expiry_pnl(cash,nl,ns,kl,ks,0),2),
            "payoff_breakpoints_usd":{str(s):round(p,2) for s,p in zip(points,pnls)}}

def package_capacity(trade:dict[str,Any],nav:float,budget_pct:float,slip:float,commission:float)->dict[str,Any]:
    risk=terminal_risk_per_package(trade,slip,commission)
    loss=risk["terminal_max_loss_usd"]
    risk_cap=math.floor(nav*budget_pct/100/loss) if loss>0 else 0
    long_size=BASE.num(trade["entry_quotes"]["long"].get("ask_size"))
    short_size=BASE.num(trade["entry_quotes"]["short"].get("bid_size"))
    n_long,n_short=int(trade["n_long"]),int(trade["n_short"])
    depth_known=long_size is not None and short_size is not None and long_size>=0 and short_size>=0
    if depth_known:
        long_cap=math.floor(long_size/n_long) if n_long>0 else 0
        short_cap=math.floor(short_size/n_short) if n_short>0 else 0
        depth_cap=min(long_cap,short_cap)
    else:
        long_cap=short_cap=depth_cap=0
    return {"risk":risk,"risk_budget_capacity_packages":risk_cap,
            "entry_depth_capacity_packages":depth_cap,
            "entry_long_ask_size":long_size,"entry_short_bid_size":short_size,
            "entry_depth_known":depth_known,
            "packages":min(risk_cap,depth_cap),
            "depth_limited":depth_known and depth_cap<risk_cap}


def shape_quote_pair(pair:dict[str,Any],rows:list[dict[str,Any]],entry_day:str,n:int,orientation:str,qmap:dict[str,dict[str,Any]]|None=None)->tuple[dict[str,Any]|None,str]:
    qmap=qmap if qmap is not None else BASE.quote_map(rows)
    high=qmap.get(pair.get("long_id")); low=qmap.get(pair.get("short_id"))
    if high is None or low is None:return None,"NEXT_SESSION_CONTRACT_ROW_MISSING"
    if BASE.as_day(high.get("date"))!=entry_day or BASE.as_day(low.get("date"))!=entry_day:return None,"ENTRY_QUOTE_DATE_MISMATCH"
    if not BASE.standard_put_identity(high) or not BASE.standard_put_identity(low):return None,"ENTRY_CONTRACT_IDENTITY_INVALID"
    if BASE.as_day(high.get("expiration"))!=pair.get("expiry") or BASE.as_day(low.get("expiration"))!=pair.get("expiry"):return None,"ENTRY_EXPIRY_MISMATCH"
    if orientation=="short-heavy": long_row,short_row,nl,ns=high,low,1,n
    elif orientation=="long-heavy": long_row,short_row,nl,ns=low,high,n,1
    else:return None,"INVALID_ORIENTATION"
    if not BASE.entry_quote_valid(long_row,"ask",nl):return None,"LONG_ASK_OR_SIZE_INSUFFICIENT"
    if not BASE.entry_quote_valid(short_row,"bid",ns):return None,"SHORT_BID_OR_SIZE_INSUFFICIENT"
    return {"long":long_row,"short":short_row,"n_long":nl,"n_short":ns},"OK"

def create_trade(pair:dict[str,Any],quotes:dict[str,Any],n:int,orientation:str,entry_day:str,spot:float,vix:float|None,trade_id:int)->dict[str,Any]:
    if orientation=="short-heavy":
        long_id,short_id=pair["long_id"],pair["short_id"]; kl,ks,nl,ns=float(pair["long_strike"]),float(pair["short_strike"]),1,n
    else:
        long_id,short_id=pair["short_id"],pair["long_id"]; kl,ks,nl,ns=float(pair["short_strike"]),float(pair["long_strike"]),n,1
    if orientation=="short-heavy" and not kl>ks>0:raise ValueError("invalid short-heavy geometry")
    if orientation=="long-heavy" and not ks>kl>0:raise ValueError("invalid long-heavy geometry")
    return {"trade_id":trade_id,"signal_date":pair["signal_date"],"entry_date":entry_day,"expiry":pair["expiry"],
            "long_id":long_id,"short_id":short_id,"long_strike":kl,"short_strike":ks,
            "long_abs_delta":pair.get("long_abs_delta"),"short_abs_delta":pair.get("short_abs_delta"),
            "entry_dte":(date.fromisoformat(pair["expiry"])-date.fromisoformat(entry_day)).days,
            "spot_entry":spot,"vix_entry":vix,"entry_quotes":{"long":quotes["long"],"short":quotes["short"]},
            "n_long":nl,"n_short":ns,"orientation":orientation,"n":n,"path":[]}

def build_volatility_time_profile(expected:list[str],spots:dict[str,Any],universe:dict[str,Any])->dict[str,Any]:
    bars=[]
    for day in expected:
        close=BASE.num((spots.get(day) or {}).get("raw_close")); vix=BASE.num((universe.get(day) or {}).get("vix"))
        bars.append({"date":day,"close":close,"vix":vix,"bucket":vix_bucket(vix)})
    horizons=[]; conditional=[]; buckets=("VIX_LT15","VIX_15_25","VIX_25_35","VIX_GTE35","UNKNOWN")
    for h in HORIZONS:
        vals=[]; grouped=defaultdict(list)
        for i in range(len(bars)-h):
            a,b=bars[i],bars[i+h]
            if a["close"] is None or b["close"] is None or a["close"]<=0 or b["close"]<=0:continue
            r=100*(b["close"]/a["close"]-1); vals.append(r); grouped[a["bucket"]].append(r)
        horizons.append({"horizon_sessions":h,**distribution(vals),
            "gain_ge_1pct":event_rate(vals,lambda x:x>=1),"gain_ge_3pct":event_rate(vals,lambda x:x>=3),
            "gain_ge_5pct":event_rate(vals,lambda x:x>=5),"loss_le_minus1pct":event_rate(vals,lambda x:x<=-1),
            "loss_le_minus3pct":event_rate(vals,lambda x:x<=-3),"loss_le_minus5pct":event_rate(vals,lambda x:x<=-5),
            "loss_le_minus10pct":event_rate(vals,lambda x:x<=-10)})
        if h in (3,5,10,20,45):
            for bucket in buckets:
                xs=grouped.get(bucket,[])
                conditional.append({"horizon_sessions":h,"entry_vix_bucket":bucket,**distribution(xs),
                    "gain_ge_3pct":event_rate(xs,lambda x:x>=3),"gain_ge_5pct":event_rate(xs,lambda x:x>=5),
                    "loss_le_minus3pct":event_rate(xs,lambda x:x<=-3),"loss_le_minus5pct":event_rate(xs,lambda x:x<=-5)})
    daily=[None]
    for i in range(1,len(bars)):
        a,b=bars[i-1]["close"],bars[i]["close"]
        daily.append(math.log(b/a) if a and b and a>0 and b>0 else None)
    # Pre-registered absolute RV bands: <20%, 20-35%, >=35% annualized.
    # RV uses returns available at the entry-date close only.
    rv20_by_index=[None]*len(bars)
    for i in range(20,len(bars)):
        xs=daily[i-19:i+1]
        if len(xs)==20 and not any(x is None for x in xs):
            rv20_by_index[i]=statistics.stdev(xs)*math.sqrt(252)*100
    def rv20_bucket(value):
        if value is None:return "UNKNOWN"
        if value<20:return "RV20_LT20"
        if value<35:return "RV20_20_35"
        return "RV20_GTE35"
    conditional_rv=[]
    for h in (3,5,10,20,45):
        grouped=defaultdict(list)
        for i in range(len(bars)-h):
            a,b=bars[i],bars[i+h]
            if a["close"] is None or b["close"] is None or a["close"]<=0 or b["close"]<=0:continue
            grouped[rv20_bucket(rv20_by_index[i])].append(100*(b["close"]/a["close"]-1))
        for bucket in ("RV20_LT20","RV20_20_35","RV20_GTE35","UNKNOWN"):
            xs=grouped.get(bucket,[])
            conditional_rv.append({"horizon_sessions":h,"entry_rv20_bucket":bucket,**distribution(xs),
                "gain_ge_3pct":event_rate(xs,lambda x:x>=3),"gain_ge_5pct":event_rate(xs,lambda x:x>=5),
                "loss_le_minus3pct":event_rate(xs,lambda x:x<=-3),"loss_le_minus5pct":event_rate(xs,lambda x:x<=-5),
                "loss_le_minus10pct":event_rate(xs,lambda x:x<=-10)})
    # Event study after prior 3-session QQQ return has reached +3% / +5%.
    # Event dates and forward windows overlap; these are descriptive, not independent trials.
    surge_study=[]
    for surge_threshold in (3.0,5.0):
        event_indices=[]
        for i in range(3,len(bars)):
            a,b=bars[i-3],bars[i]
            if a["close"] is not None and b["close"] is not None and a["close"]>0 and b["close"]>0:
                if 100*(b["close"]/a["close"]-1)>=surge_threshold:event_indices.append(i)
        for h in (1,3,5,10):
            forward=[]
            for i in event_indices:
                if i+h>=len(bars):continue
                a,b=bars[i],bars[i+h]
                if a["close"] is not None and b["close"] is not None and a["close"]>0 and b["close"]>0:
                    forward.append(100*(b["close"]/a["close"]-1))
            surge_study.append({"prior_3_session_return_ge_pct":surge_threshold,"forward_horizon_sessions":h,
                **distribution(forward),"negative_forward_return":event_rate(forward,lambda x:x<0),
                "forward_loss_le_minus3pct":event_rate(forward,lambda x:x<=-3),
                "forward_gain_ge_3pct":event_rate(forward,lambda x:x>=3),
                "forward_gain_ge_5pct":event_rate(forward,lambda x:x>=5),"overlapping_event_dates":True})
    rv=[]
    for window in RV_WINDOWS:
        vals=[]; by_bucket=defaultdict(list)
        for i in range(window,len(bars)):
            xs=daily[i-window+1:i+1]
            if len(xs)!=window or any(x is None for x in xs):continue
            sig=statistics.stdev(xs)*math.sqrt(252)*100;vals.append(sig);by_bucket[bars[i]["bucket"]].append(sig)
        rv.append({"window_sessions":window,"annualization_factor":252,**distribution(vals),
                   "by_vix_bucket":{b:distribution(by_bucket.get(b,[])) for b in buckets}})
    observed_days=[b["date"] for b in bars if b["close"] is not None]
    return {"status":"EMPIRICAL_UNDERLYING_CONTEXT_NOT_OPTION_PNL_PROBABILITY",
            "source_start":observed_days[0] if observed_days else None,"source_end":observed_days[-1] if observed_days else None,
            "expected_sessions":len(bars),"observed_close_sessions":len(observed_days),
            "missing_expected_close_sessions":len(bars)-len(observed_days),
            "horizon_returns":horizons,"conditional_by_vix_proxy":conditional,
            "conditional_by_entry_rv20":conditional_rv,"prior_3_session_surge_forward_study":surge_study,
            "entry_rv20_bands_pct_annualized":{"RV20_LT20":"<20%","RV20_20_35":"20% to <35%","RV20_GTE35":">=35%"},
            "rolling_realized_volatility":rv,
            "interpretation":"Overlapping historical QQQ close-to-close frequencies are not independent-trial forecasts or probabilities of a specific option package profiting. VIX is S&P 500 implied-volatility context, not the QQQ option IV surface. Missing endpoint closes are excluded."}

def make_policies(nav:float,pct:float,orientation:str,n:int)->list[dict[str,Any]]:
    target=nav*pct/100
    out=[{"name":"DTE7_BASELINE","kind":"DTE7","target_usd":None,"target_pct":None,"age_limit":None,"action":"CLOSE_ALL"}]
    out += [{"name":f"ANYTIME_TP_{pct:g}PCT_NAV","kind":"TP_ANY","target_usd":target,"target_pct":pct,"age_limit":None,"action":"CLOSE_ALL"},
            {"name":f"ANYTIME_SL_{pct:g}PCT_NAV","kind":"SL_ANY","target_usd":target,"target_pct":pct,"age_limit":None,"action":"CLOSE_ALL"}]
    for days in (3,5):
        out.append({"name":f"FIRST{days}D_TP_{pct:g}PCT_CLOSE_ALL","kind":"TP_WINDOW_CLOSE","target_usd":target,"target_pct":pct,"age_limit":days,"action":"CLOSE_ALL"})
        if not (orientation=="short-heavy" and n==1):
            out.append({"name":f"FIRST{days}D_TP_{pct:g}PCT_TRIM_SHORT","kind":"TP_WINDOW_TRIM","target_usd":target,"target_pct":pct,"age_limit":days,"action":"TRIM_SHORT"})
    return out


def all_exit_policies(nav:float,orientation:str,n:int)->list[dict[str,Any]]:
    """Create the exit-target axis independently from the package risk-budget axis."""
    policies=[{"name":"DTE7_BASELINE","kind":"DTE7","target_usd":None,"target_pct":None,"age_limit":None,"action":"CLOSE_ALL"}]
    for target_pct in BUDGET_PCTS:
        policies.extend(p for p in make_policies(nav,target_pct,orientation,n) if p["kind"]!="DTE7")
    return policies

def simulate_policy(trade:dict[str,Any],policy:dict[str,Any],packages:int,slip:float,commission:float,nav:float)->dict[str,Any]:
    nl0,ns0=int(trade["n_long"]),int(trade["n_short"]); nl,ns=nl0*packages,ns0*packages
    state={"cash":entry_cash_per_package(trade,slip,commission)*packages,"n_long":nl,"n_short":ns,"contracts_closed_short":0}
    pending=None;pending_day=None;custom_fired=False;signal_age=None;action_age=None;pending_long_close=False
    custom_trigger=False;fallback=False;deferred=0;required=0;missing=0;exposure=0.0
    final=None;final_status="UNRESOLVED";resolved=False;max_mark=None;min_mark=None;actions=[]
    for age,step in enumerate(trade["path"]):
        day=step["date"];dte=(date.fromisoformat(trade["expiry"])-date.fromisoformat(day)).days
        exposure+=state["n_short"]/max(1,ns)
        # Retry a residual Long Put sale only when a CLOSE_ALL action failed on that leg.
        # TRIM_SHORT on a long-heavy ratio intentionally preserves its N Long Puts.
        if pending_long_close and state["n_short"]==0 and state["n_long"]>0:
            sold,status=BASE.sell_long_if_executable(state,step,slip,commission)
            if sold and state["n_long"]==0:
                actions.append("SELL_RESIDUAL_LONG");pending_long_close=False
            else:deferred+=1
        pnl,status=BASE.mark_pnl(state,step,slip,commission)
        if state["n_short"]>0 or state["n_long"]>0:
            required+=1
            if pnl is None:missing+=1
        if pnl is not None:
            max_mark=pnl if max_mark is None else max(max_mark,pnl);min_mark=pnl if min_mark is None else min(min_mark,pnl)
        trigger=None
        if dte>0 and state["n_short"]>0 and pending is None and not custom_fired and age>=1 and pnl is not None:
            k=policy["kind"];target=policy.get("target_usd")
            if k=="TP_ANY" and pnl>=target:trigger="CLOSE_ALL"
            elif k=="SL_ANY" and pnl<=-target:trigger="CLOSE_ALL"
            elif k=="TP_WINDOW_CLOSE" and age<=policy["age_limit"] and pnl>=target:trigger="CLOSE_ALL"
            elif k=="TP_WINDOW_TRIM" and age<=policy["age_limit"] and pnl>=target:trigger="TRIM_SHORT"
            if trigger:
                pending,pending_day=trigger,day;custom_fired=True;custom_trigger=True
                if signal_age is None:signal_age=age
        if dte>0 and state["n_short"]>0 and pending is None and dte<=7:
            pending,pending_day="CLOSE_ALL",day;fallback=True
            if signal_age is None:signal_age=age
        if pending is not None and pending_day is not None and day>pending_day and dte>0 and state["n_short"]>0:
            if pending=="TRIM_SHORT":
                qty=min(max(0,state["n_short"]-packages),state["n_short"]) if trade["orientation"]=="short-heavy" else state["n_short"]
            else:qty=state["n_short"]
            if qty<=0:ok,close_status=False,"NO_EXCESS_SHORT_TO_TRIM"
            else:ok,close_status=BASE.close_short_qty(state,step,qty,slip,commission)
            if ok:
                action_age=age;actions.append(pending)
                if pending=="CLOSE_ALL":
                    sold,sell_status=BASE.sell_long_if_executable(state,step,slip,commission);actions.append("SELL_LONG_"+sell_status)
                    pending_long_close=(not sold and state["n_long"]>0)
                pending,pending_day=None,None
            else:deferred+=1
        if dte<=0:
            spot=BASE.num(step.get("spot"))
            if state["n_short"]==0 and state["n_long"]==0:
                final=state["cash"];final_status="CLOSED_AT_OBSERVED_SIDE_QUOTES";resolved=True
            elif spot is not None:
                final=expiry_pnl(state["cash"],state["n_long"],state["n_short"],trade["long_strike"],trade["short_strike"],spot)
                final_status="INTRINSIC_SETTLEMENT_PROXY_BEFORE_ASSIGNMENT_FEES";resolved=True
            break
        if state["n_short"]==0 and state["n_long"]==0:
            final=state["cash"];final_status="CLOSED_AT_OBSERVED_SIDE_QUOTES";resolved=True;break
    return {"policy":policy["name"],"nav_usd":nav,"risk_budget_pct_nav":policy.get("risk_budget_pct_nav"),
        "target_pct_nav":policy.get("target_pct"),"target_usd":policy.get("target_usd"),"packages":packages,
        "episode_id":trade["trade_id"],"orientation":trade["orientation"],"n":trade["n"],
        "n_long_per_package":nl0,"n_short_per_package":ns0,"total_long_opened":nl,"total_short_opened":ns,
        "entry_date":trade["entry_date"],"expiry":trade["expiry"],"entry_dte":trade["entry_dte"],
        "final_pnl_usd":round(final,2) if final is not None else None,
        "final_pnl_pct_nav":round(100*final/nav,6) if final is not None else None,
        "final_status":final_status,"resolved":resolved,"custom_triggered":custom_trigger,"dte7_fallback_triggered":fallback,
        "signal_age":signal_age,"first_action_age":action_age,
        "signal_to_action_sessions":action_age-signal_age if action_age is not None and signal_age is not None else None,
        "mark_coverage_pct":round(100*(required-missing)/required,3) if required else 100.0,
        "missing_mark_sessions":missing,"required_mark_sessions":required,"deferred_action_sessions":deferred,
        "short_risk_exposure_session_equivalents":round(exposure,4),
        "remaining_long_contracts":state["n_long"],"remaining_short_contracts":state["n_short"],
        "residual_structure":"LONG_ONLY" if state["n_long"]>0 and state["n_short"]==0 else "LONG_AND_SHORT" if state["n_long"]>0 and state["n_short"]>0 else "SHORT_ONLY" if state["n_short"]>0 else "FLAT",
        "max_observed_mark_pnl_usd":round(max_mark,2) if max_mark is not None else None,
        "min_observed_mark_pnl_usd":round(min_mark,2) if min_mark is not None else None,"actions":";".join(actions)}

def summarize_policy(results:list[dict[str,Any]],candidate_n:int,blocked:int)->dict[str,Any]:
    closed=[x for x in results if x["resolved"] and x["final_pnl_usd"] is not None]
    pnls=[float(x["final_pnl_usd"]) for x in closed];wins=[x for x in pnls if x>0];losses=[x for x in pnls if x<0];gl=abs(sum(losses))
    return {"candidate_episodes":candidate_n,"episodes_fitting_budget":len(results),"episodes_blocked_zero_capacity":blocked,
        "resolved_episodes":len(closed),"unresolved_episodes":len(results)-len(closed),
        "packages_deployed_sum":sum(x["packages"] for x in results),
        "net_pnl_sum_usd":round(sum(pnls),2) if pnls else None,
        "expectancy_usd_per_resolved_episode":round(statistics.mean(pnls),2) if pnls else None,
        "median_pnl_usd":round(statistics.median(pnls),2) if pnls else None,
        "win_rate_pct":round(100*len(wins)/len(pnls),3) if pnls else None,
        "profit_factor":round(sum(wins)/gl,5) if gl>0 else None,
        "best_trade_usd":round(max(pnls),2) if pnls else None,"worst_trade_usd":round(min(pnls),2) if pnls else None,
        "custom_triggered_episodes":sum(x["custom_triggered"] for x in results),
        "dte7_fallback_episodes":sum(x["dte7_fallback_triggered"] for x in results),
        "mean_mark_coverage_pct":round(statistics.mean([x["mark_coverage_pct"] for x in results]),3) if results else None,
        "missing_mark_sessions":sum(x["missing_mark_sessions"] for x in results),
        "deferred_action_sessions":sum(x["deferred_action_sessions"] for x in results)}

def write_csv(path:Path,rows:list[dict[str,Any]])->None:
    if not rows:path.write_text("",encoding="utf-8");return
    fields=[]
    for row in rows:
        for k,v in row.items():
            if k not in fields and not isinstance(v,(dict,list)):fields.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for row in rows:w.writerow(row)

def run_matrix(out_dir:Path)->dict[str,Any]:
    sys.path.insert(0,str(BASE.SOURCE_DIR))
    import full_history_qqq_quote_audit as audit
    import qqq_far_call_quote_replay as source_replay
    cache=ROOT/".cache"/"qqq-options-full-history"
    integrity,universe,spots,expected=audit.build_inputs(cache)
    # Keep the originally requested calendar through 2025-12-31 for underlying probability context.
    # Option entries remain gated separately to the last available option-chain date below.
    expected=sorted(d for d in expected if START_DATE<=d<=REQUESTED_END_DATE);valid_days=set(expected)
    option_paths=[];file_pins={}
    for spec in audit.ANNUAL_FILES:
        path,pin=audit.download_verified(spec,cache);option_paths.append(path);file_pins[spec["name"]]=pin
    chains=iter(source_replay.iter_qqq_chain_days(option_paths));next_chain=next(chains,None)
    shapes=[(n,o) for n in range(1,7) for o in ("short-heavy","long-heavy")]
    states={};episodes={}
    for n,o in shapes:
        key=f"N{n}_{o.upper().replace('-','_')}"
        states[key]={"n":n,"o":o,"active":None,"pending":None,"last_expiry":None,"selected":0,"opened":0,"skips":Counter(),"selection_status":Counter()}
        episodes[key]=[]
    last_chain=None
    for day in expected:
        while next_chain is not None and next_chain[0]<day:next_chain=next(chains,None)
        if next_chain is not None and next_chain[0]==day:
            rows=next_chain[1];next_chain=next(chains,None);last_chain=day
        else:rows=[]
        spot=BASE.num((spots.get(day) or {}).get("raw_close"));vix=BASE.num((universe.get(day) or {}).get("vix"))
        # Reuse one option lookup and one pair selection across all shape states for this session.
        qmap_day=BASE.quote_map(rows) if rows else {}
        pair_today=BASE.choose_ratio_put(rows,day,valid_days,audit.base.standard_strike_grid) if rows and spot is not None and vix is not None else None
        for key,state in states.items():
            if state["pending"] is not None and state["active"] is None:
                pair=state["pending"]
                quote,status=shape_quote_pair(pair,rows,day,state["n"],state["o"],qmap_day) if rows else (None,"NEXT_SESSION_CHAIN_MISSING")
                if quote is not None and spot is not None:
                    state["active"]=create_trade(pair,quote,state["n"],state["o"],day,spot,vix,len(episodes[key])+1)
                    state["opened"]+=1;state["pending"]=None
                else:state["skips"][status if quote is None else "ENTRY_RAW_SPOT_MISSING"]+=1;state["pending"]=None
            active=state["active"]
            if active is not None:
                lr=qmap_day.get(active["long_id"]);sr=qmap_day.get(active["short_id"])
                active["path"].append({"date":day,"dte":(date.fromisoformat(active["expiry"])-date.fromisoformat(day)).days,
                    "long":dict(lr) if lr is not None else None,"short":dict(sr) if sr is not None else None,"spot":spot,"vix":vix})
                if day==active["expiry"]:
                    episodes[key].append(active);state["last_expiry"]=active["expiry"];state["active"]=None
                elif date.fromisoformat(day)>date.fromisoformat(active["expiry"]):raise ValueError("Episode crossed expiry: "+key)
        if not rows or spot is None or vix is None:continue
        for key,state in states.items():
            if state["active"] is not None or state["pending"] is not None:continue
            if state["last_expiry"] is not None and day<=state["last_expiry"]:continue
            pair=pair_today or {"status":"NO_PAIR_SELECTION"}
            state["selection_status"][pair.get("status","UNKNOWN")]+=1
            if pair.get("status")!="PAIR_SELECTED":continue
            state["selected"]+=1
            if pair["expiry"]>SOURCE_END_DATE or pair["expiry"] not in valid_days:state["skips"]["EXPIRY_OUTSIDE_VERIFIED_WINDOW"]+=1
            else:state["pending"]=pair
    for state in states.values():
        if state["active"] is not None:state["skips"]["OPEN_POSITION_WITHOUT_SOURCE_EXPIRY"]+=1
        if state["pending"] is not None:state["skips"]["PENDING_ENTRY_AT_SOURCE_END"]+=1
    if last_chain!=SOURCE_END_DATE:raise ValueError("Option source ended on "+str(last_chain)+", expected "+SOURCE_END_DATE)
    vol=build_volatility_time_profile(expected,spots,universe)
    policy_rows=[];capacity_rows=[];episode_rows=[]
    for n,o in shapes:
        key=f"N{n}_{o.upper().replace('-','_')}";trades=episodes[key];state=states[key]
        for nav in NAVS:
            for budget_pct in BUDGET_PCTS:
                for costs in COST_CASES:
                    caps=[]
                    for trade in trades:
                        sizing=package_capacity(trade,nav,budget_pct,costs["slippage"],costs["commission"])
                        caps.append({"trade":trade,**sizing,"units":sizing["packages"]})
                    units_list=[x["units"] for x in caps]
                    capacity_rows.append({"orientation":o,"n":n,"nav_usd":nav,"risk_budget_pct_nav":budget_pct,"cost_case":costs["name"],
                        "selected_pair_count":state["selected"],"opened_episode_count":state["opened"],"episodes":len(trades),
                        "entry_skip_counts":dict(state["skips"]),
                        "median_terminal_max_loss_per_package_usd":round(statistics.median([x["risk"]["terminal_max_loss_usd"] for x in caps]),2) if caps else None,
                        "p95_terminal_max_loss_per_package_usd":quantile([x["risk"]["terminal_max_loss_usd"] for x in caps],.95),
                        "median_max_loss_pct_nav":round(statistics.median([100*x["risk"]["terminal_max_loss_usd"]/nav for x in caps]),4) if caps else None,
                        "median_risk_budget_package_capacity":round(statistics.median([x["risk_budget_capacity_packages"] for x in caps]),3) if caps else None,
                        "median_entry_depth_capacity_packages":round(statistics.median([x["entry_depth_capacity_packages"] for x in caps]),3) if caps else None,
                        "episodes_limited_by_displayed_entry_depth":sum(x["depth_limited"] for x in caps),
                        "episodes_fitting_one_or_more_packages":sum(x>=1 for x in units_list),
                        "percent_episodes_fitting_one_or_more_packages":round(100*sum(x>=1 for x in units_list)/len(units_list),3) if units_list else None,
                        "median_package_capacity":round(statistics.median(units_list),3) if units_list else None,"max_package_capacity":max(units_list,default=None)})
                    # Risk budget sets package count; the policy set independently spans all target percentages.
                    for policy in all_exit_policies(nav,o,n):
                        results=[];blocked=0
                        for cap in caps:
                            if cap["units"]<1:blocked+=1;continue
                            result=simulate_policy(cap["trade"],policy,cap["units"],costs["slippage"],costs["commission"],nav)
                            result.update({"risk_budget_pct_nav":budget_pct,"cost_case":costs["name"],"capacity_packages":cap["units"],
                                           "risk_budget_capacity_packages":cap["risk_budget_capacity_packages"],
                                           "entry_depth_capacity_packages":cap["entry_depth_capacity_packages"],
                                           "entry_depth_limited":cap["depth_limited"],
                                           "terminal_max_loss_per_package_usd":cap["risk"]["terminal_max_loss_usd"]})
                            results.append(result);episode_rows.append(result)
                        summary=summarize_policy(results,len(trades),blocked)
                        policy_rows.append({"orientation":o,"n":n,"nav_usd":nav,"risk_budget_pct_nav":budget_pct,"cost_case":costs["name"],
                            "policy":policy["name"],"policy_kind":policy["kind"],"action":policy["action"],
                            "target_pct_nav":policy.get("target_pct"),"target_usd":policy.get("target_usd"),
                            "holding_window_sessions":policy.get("age_limit"),"selected_pairs":state["selected"],**summary})
    report={"research_id":"QQQ_PUT_RATIO_NAV_EXIT_MATRIX_V2","status":"DEVELOPMENT_DIAGNOSTIC_NOT_LIVE_APPROVAL",
        "entry_contract":"Separate non-overlapping cohort per N/orientation; same-expiry standard QQQ puts selected from EOD rows at 30-60 calendar DTE (target 45), higher-strike abs-delta nearest .30 in [.20,.40], lower-strike nearest .10 in [.04,.16]; enter next observed session only if exact contract IDs and requested side sizes are valid.",
        "shape_grid":[{"n":n,"orientation":o} for n,o in shapes],"nav_grid_usd":list(NAVS),"risk_budget_grid_pct_nav":list(BUDGET_PCTS),
        "clocks":{"entry_dte":"30-60 calendar days, target 45","holding_age":"entry-day EOD age 0; first 3/5 sessions are ages 1-3/1-5; EOD signals act no earlier than a later quote","baseline":"current remaining calendar DTE<=7"},
        "cost_cases":list(COST_CASES),"underlying_volatility_time_profile":vol,"capacity_summary":capacity_rows,"policy_summary":policy_rows,
        "source":{"integrity":integrity,"option_file_integrity":file_pins,"option_last_date":SOURCE_END_DATE,"requested_end":REQUESTED_END_DATE,"missing_terminal_sessions":11,"holdout_untouched":False,"fills_verified":False},
        "limitations":["2018-2025 source has been previously inspected; DEVELOPMENT/REVISIT, not virgin OOS.",
        "Public EOD option marks and displayed size do not prove fills. Broker margin, IV path, early assignment and forced liquidation remain unmeasured.",
        "Underlying return frequencies are overlapping historical outcomes, not independent-trial forecasts or option-package profit probabilities. VIX is an S&P 500 proxy, not QQQ option IV.",
        "P&L is a fixed non-overlapping cohort and is not continuously reinvested account CAGR/MaxDD.",
        "No policy is selected by total P&L alone; inspect expectancy, profit factor, worst trade, mark coverage, deferred actions and adverse costs."]}
    return report,policy_rows,capacity_rows,episode_rows

def write_csv(path:Path,rows:list[dict[str,Any]])->None:
    if not rows:path.write_text("",encoding="utf-8");return
    fields=[]
    for row in rows:
        for k,v in row.items():
            if k not in fields and not isinstance(v,(dict,list)):fields.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for row in rows:w.writerow(row)

def _fmt_money(value:Any)->str:
    return "—" if value is None else "$" + f"{float(value):,.2f}"


def _fmt_num(value:Any,digits:int=2)->str:
    return "—" if value is None else f"{float(value):.{digits}f}"


def render_exit_policy_sensitivity(policy_rows:list[dict[str,Any]])->str:
    """Render every first-3/first-5 NAV-target action at base cost, not just selected winners."""
    baseline_by_key={}
    for row in policy_rows:
        if row.get("cost_case")=="BASE_COST" and row.get("policy_kind")=="DTE7":
            key=(row.get("orientation"),row.get("n"),row.get("nav_usd"),row.get("risk_budget_pct_nav"),row.get("cost_case"))
            baseline_by_key[key]=row
    selected=[r for r in policy_rows
              if r.get("cost_case")=="BASE_COST"
              and r.get("policy_kind") in {"TP_WINDOW_CLOSE","TP_WINDOW_TRIM"}
              and r.get("target_pct_nav") in BUDGET_PCTS
              and r.get("holding_window_sessions") in (3,5)]
    selected.sort(key=lambda r:(float(r["nav_usd"]),float(r["risk_budget_pct_nav"]),str(r["orientation"]),int(r["n"]),
                                float(r["target_pct_nav"]),int(r["holding_window_sessions"]),str(r["action"])))
    lines=[
        "| Direction | N | NAV | Risk budget | Exit target | Window | Action | Eligible / blocked | Resolved / unresolved | Trigger / DTE7 fallback | DTE7 resolved / P&L | Policy resolved / P&L | Expectancy | Win% | PF | Worst trade | Mark coverage | Deferred actions |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for row in selected:
        key=(row.get("orientation"),row.get("n"),row.get("nav_usd"),row.get("risk_budget_pct_nav"),row.get("cost_case"))
        base=baseline_by_key.get(key,{})
        target=row.get("target_pct_nav")
        eligible=row.get("episodes_fitting_budget",0)
        blocked=row.get("episodes_blocked_zero_capacity",0)
        resolved=row.get("resolved_episodes",0)
        unresolved=row.get("unresolved_episodes",0)
        action="CLOSE ALL" if row.get("action")=="CLOSE_ALL" else "TRIM SHORT"
        window=int(row["holding_window_sessions"])
        target_txt=f"{float(target):g}% / ${float(row.get('target_usd') or 0):,.0f}"
        base_txt=f"{base.get('resolved_episodes',0)} / {_fmt_money(base.get('net_pnl_sum_usd'))}"
        policy_txt=f"{resolved} / {_fmt_money(row.get('net_pnl_sum_usd'))}"
        lines.append(
            f"| {row['orientation']} | {row['n']} | ${float(row['nav_usd']):,.0f} | {float(row['risk_budget_pct_nav']):g}% "
            f"| {target_txt} | {window} | {action} | {eligible} / {blocked} | {resolved} / {unresolved} "
            f"| {row.get('custom_triggered_episodes',0)} / {row.get('dte7_fallback_episodes',0)} "
            f"| {base_txt} | {policy_txt} | {_fmt_money(row.get('expectancy_usd_per_resolved_episode'))} "
            f"| {_fmt_num(row.get('win_rate_pct'))}% | {_fmt_num(row.get('profit_factor'),3)} "
            f"| {_fmt_money(row.get('worst_trade_usd'))} | {_fmt_num(row.get('mean_mark_coverage_pct'))}% "
            f"| {row.get('deferred_action_sessions',0)} |"
        )
    return "\n".join(lines)


def render_adverse_cost_sensitivity(policy_rows:list[dict[str,Any]])->str:
    """Show BASE vs ADVERSE costs on the $1m NAV / 1% risk-budget slice for all early-exit policies."""
    by_key={}
    for row in policy_rows:
        if row.get("nav_usd")!=1000000.0 or row.get("risk_budget_pct_nav")!=1.0:
            continue
        if row.get("policy_kind") not in {"TP_WINDOW_CLOSE","TP_WINDOW_TRIM"}:
            continue
        key=(row.get("orientation"),row.get("n"),row.get("target_pct_nav"),row.get("holding_window_sessions"),
             row.get("action"),row.get("cost_case"))
        by_key[key]=row
    keys=sorted({k[:5] for k in by_key},key=lambda k:(str(k[0]),int(k[1]),float(k[2]),int(k[3]),str(k[4])))
    lines=[
        "| Direction | N | Target | Window | Action | Base resolved / P&L | Adverse resolved / P&L | Base triggers | Adverse triggers | Base worst | Adverse worst |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|"
    ]
    for key in keys:
        o,n,pct,window,action=key
        base=by_key.get((*key,"BASE_COST"))
        adverse=by_key.get((*key,"ADVERSE_COST"))
        if base is None or adverse is None:
            continue
        label="CLOSE ALL" if action=="CLOSE_ALL" else "TRIM SHORT"
        lines.append(
            f"| {o} | {n} | {float(pct):g}% | {window} | {label} "
            f"| {base.get('resolved_episodes',0)} / {_fmt_money(base.get('net_pnl_sum_usd'))} "
            f"| {adverse.get('resolved_episodes',0)} / {_fmt_money(adverse.get('net_pnl_sum_usd'))} "
            f"| {base.get('custom_triggered_episodes',0)} | {adverse.get('custom_triggered_episodes',0)} "
            f"| {_fmt_money(base.get('worst_trade_usd'))} | {_fmt_money(adverse.get('worst_trade_usd'))} |"
        )
    return "\n".join(lines)


def render_markdown(report:dict[str,Any])->str:
    lines=["# QQQ Put Ratio NAV Exit Matrix V2","","**Status:** DEVELOPMENT_DIAGNOSTIC_NOT_LIVE_APPROVAL. Public EOD quote-side replay, not confirmed fills.",
    f"**Window:** {report['underlying_volatility_time_profile']['source_start']} to {report['underlying_volatility_time_profile']['source_end']}; requested history through 2025-12-31 has 11 missing expected sessions.",
    "","## QQQ underlying return distributions by horizon (not option P&L probabilities)","","| Horizon | N | Median return | P(+3% or more) | P(+5% or more) | P(-3% or worse) | P(-5% or worse) | P(-10% or worse) |","|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in report["underlying_volatility_time_profile"]["horizon_returns"]:
        lines.append(f"| {x['horizon_sessions']} | {x['observations']} | {x['median']}% | {x['gain_ge_3pct']['probability_pct']}% | {x['gain_ge_5pct']['probability_pct']}% | {x['loss_le_minus3pct']['probability_pct']}% | {x['loss_le_minus5pct']['probability_pct']}% | {x['loss_le_minus10pct']['probability_pct']}% |")
    lines+=["","## Forward returns conditioned on trailing 20-session realized volatility","","Bands are fixed before comparing exit policies: <20%, 20–35%, and ≥35% annualized. RV uses only data through the entry-date close. These are QQQ-underlying frequencies, not option-profit probabilities.","","| Horizon | Entry RV20 band | N | Median return | P(+3%) | P(+5%) | P(≤−3%) | P(≤−5%) | P(≤−10%) |","|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for x in report["underlying_volatility_time_profile"]["conditional_by_entry_rv20"]:
        lines.append(f"| {x['horizon_sessions']} | {x['entry_rv20_bucket']} | {x['observations']} | {x['median']}% | {x['gain_ge_3pct']['probability_pct']}% | {x['gain_ge_5pct']['probability_pct']}% | {x['loss_le_minus3pct']['probability_pct']}% | {x['loss_le_minus5pct']['probability_pct']}% | {x['loss_le_minus10pct']['probability_pct']}% |")
    lines+=["","## Outcomes after a 3-session QQQ surge","","The event is defined after the preceding three-session return has already reached +3% or +5%. Forward windows and event dates overlap; results are descriptive, not independent trials. A spot surge alone is not an option exit rule.","","| Prior 3-session return | Forward sessions | N | Median forward return | P(next return < 0) | P(≤−3%) | P(≥+3%) | P(≥+5%) |","|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in report["underlying_volatility_time_profile"]["prior_3_session_surge_forward_study"]:
        lines.append(f"| ≥{x['prior_3_session_return_ge_pct']:g}% | {x['forward_horizon_sessions']} | {x['observations']} | {x['median']}% | {x['negative_forward_return']['probability_pct']}% | {x['forward_loss_le_minus3pct']['probability_pct']}% | {x['forward_gain_ge_3pct']['probability_pct']}% | {x['forward_gain_ge_5pct']['probability_pct']}% |")
    lines+=["","## N=1-6, both directions, NAV and risk-budget sizing","","| Direction | N | NAV | Risk budget | Cost | Episodes | Median max loss/package | Median loss % NAV | Episodes fit ≥1 package | Median packages | DTE7 P&L | 3-day 0.5% close | 3-day 0.5% trim | 5-day 1% close | 5-day 1% trim |","|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    capacity=report["capacity_summary"];policies=report["policy_summary"]
    for x in capacity:
        if x["cost_case"]!="BASE_COST":continue
        o,n,nav,b=x["orientation"],x["n"],x["nav_usd"],x["risk_budget_pct_nav"]
        rows=[r for r in policies if r["orientation"]==o and r["n"]==n and r["nav_usd"]==nav and r["risk_budget_pct_nav"]==b and r["cost_case"]=="BASE_COST"]
        def pval(kind,pct,age,action):
            found=next((r for r in rows if r["policy_kind"]==kind and r["target_pct_nav"]==pct and r["holding_window_sessions"]==age and r["action"]==action),None)
            if found is None:return "N/A"
            return "—" if found["net_pnl_sum_usd"] is None else str(round(found["net_pnl_sum_usd"],2))
        baseline=next((r for r in rows if r["policy_kind"]=="DTE7"),None)
        lines.append(f"| {o} | {n} | {int(nav):,} | {b:g}% | BASE | {x['episodes']} | {x['median_terminal_max_loss_per_package_usd']} | {x['median_max_loss_pct_nav']}% | {x['percent_episodes_fitting_one_or_more_packages']}% | {x['median_package_capacity']} | {baseline['net_pnl_sum_usd'] if baseline else '—'} | {pval('TP_WINDOW_CLOSE',.5,3,'CLOSE_ALL')} | {pval('TP_WINDOW_TRIM',.5,3,'TRIM_SHORT')} | {pval('TP_WINDOW_CLOSE',1.0,5,'CLOSE_ALL')} | {pval('TP_WINDOW_TRIM',1.0,5,'TRIM_SHORT')} |")
    lines += ["","## Complete first-3 / first-5 NAV exit sensitivity (BASE costs)",
    "",
    "This table prints all 0.5% / 1% / 2% NAV targets for both $100k and $1m NAV, each tested independently against the 0.5% / 1% / 2% terminal-tail risk-budget axis. It includes close-all and reduce-short actions, with the DTE≤7 baseline side by side.",
    "",
    "P&L sums and expectancy are calculated over resolved episodes only; read resolved / unresolved and eligible / blocked counts before comparing. The episodes form a fixed non-overlapping development cohort, not one compounded account. TRIM SHORT means short-heavy retains one short per package, while long-heavy buys back its only short and retains N long puts. Short-heavy N=1 has no excess short to trim, so that action is not a valid candidate.",
    "",
    render_exit_policy_sensitivity(policies),
    "",
    "## Adverse-cost check: $1m NAV, 1% terminal-tail risk budget",
    "",
    "BASE uses $0.05 per-share slippage per leg per side + $0.65 commission/contract/side; ADVERSE doubles slippage to $0.10. This slice compares all target/window/action combinations. Resolved counts may differ, so do not subtract aggregate totals as though every row were a perfectly paired episode cohort.",
    "",
    render_adverse_cost_sensitivity(policies),
    "",
    "NAV targets are proportional: 0.5/1/2% = $500/$1,000/$2,000 at $100k and $5,000/$10,000/$20,000 at $1m. Package capacity is floored from each episode's terminal max-loss estimate; zero capacity means no package fits that terminal-loss budget, not a broker margin conclusion.",
    "",
    "Return probabilities are overlapping historical QQQ underlying moves, not independent-trial forecasts or option-package profit probabilities. VIX is an S&P 500 proxy, not QQQ IV.",
    "",
    "Entry DTE, first-3/first-5 holding age and remaining DTE≤7 are separate clocks. Signals are EOD and actions use later quote-side marks. Missing quotes are not forward-filled.",
    "",
    "This is a fixed non-overlapping episode cohort, not continuously reinvested account CAGR/MaxDD. Historical data has been inspected previously, so this is DEVELOPMENT/REVISIT rather than virgin OOS. Broker margin, intraday IV/margin paths, assignment and forced liquidation remain unmeasured."]
    return "\n".join(lines)+"\n"

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,default=ROOT/"artifacts"/"qqq_put_ratio_exit_matrix_v2");args=parser.parse_args()
    report,policies,capacities,episodes=run_matrix(args.out)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"qqq_put_ratio_nav_exit_matrix_v2.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (args.out/"qqq_put_ratio_nav_exit_matrix_v2.md").write_text(render_markdown(report),encoding="utf-8")
    write_csv(args.out/"qqq_put_ratio_nav_exit_policy_matrix_v2.csv",policies)
    write_csv(args.out/"qqq_put_ratio_nav_exit_config_matrix_v2.csv",capacities)
    write_csv(args.out/"qqq_put_ratio_nav_exit_episode_results_v2.csv",episodes)
    print(json.dumps({"research_id":report["research_id"],"status":report["status"],"configs":len(capacities),"policy_rows":len(policies),"episode_rows":len(episodes),"output_dir":str(args.out)},indent=2))
    print((args.out/"qqq_put_ratio_nav_exit_matrix_v2.md").read_text(encoding="utf-8"))

if __name__=="__main__":main()
