#!/usr/bin/env python3
"""Independent quote-side replay for QQQ long puts and SPY short puts."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics, sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"qqq_spy_put_equal_premium_v1"))
import qqq_spy_put_equal_premium_replay_v1 as base

ENTRY_PATH="research/qqq_spy_put_equal_premium_v1/results/latest/entry_cohort.csv"
TRADE_PATH="research/qqq_spy_put_equal_premium_v1/results/latest/trade_episodes.csv"
SUMMARY_PATH="research/qqq_spy_put_equal_premium_v1/results/latest/summary.json"
ENTRY_SHA="5646739377f7d8c4346e2e2b2f915ba21a497669"
TRADE_SHA="13b4cf574d24250655d8f9e3d5878e3a4d4f1bd5"
SUMMARY_SHA="968676c093d48579b516e1b07d4ec55619b90349"
COSTS=({"name":"ZERO_COST","slippage":0.0,"commission":0.0},
       {"name":"BASE_COST","slippage":0.05,"commission":0.65},
       {"name":"ADVERSE_COST","slippage":0.10,"commission":0.65})
POLICY_MAP={p["policy"]:p for p in base.POLICIES}
POLICIES=tuple(POLICY_MAP)
LEG_Q="QQQ_LONG_PUT_STANDALONE"
LEG_S="SPY_SHORT_PUT_STANDALONE"
PAIR="FIXED_PAIR_CROSS_GRID"
MULT=100
ENTRY_FIELDS=["plan_id","episode_id","signal_date","expiry","strategy","qqq_long_contracts","spy_short_contracts","entry_status","entry_skip_reason","entry_attempt_count","entry_defer_sessions","entry_date","entry_delay_sessions","qqq_contract_id","spy_contract_id","qqq_entry_ask","qqq_entry_bid","spy_entry_bid","spy_entry_ask","qqq_entry_ask_size","spy_entry_bid_size","qqq_entry_premium_debit_usd","spy_entry_premium_credit_usd","premium_abs_mismatch_usd","premium_match_pct","last_attempt_date","last_attempt_reason"]
TRADE_FIELDS=["plan_id","episode_id","policy","strategy","signal_date","expiry","entry_status","status","unresolved_reason","qqq_long_contracts","spy_short_contracts","qqq_contract_id","spy_contract_id","entry_date","entry_delay_sessions","entry_index","exit_signal_date","exit_date","exit_delay_sessions","exit_deferred_sessions","exit_reason","qqq_entry_ask","spy_entry_bid","qqq_entry_ask_size","spy_entry_bid_size","exit_qqq_bid","exit_spy_ask","exit_qqq_bid_size","exit_spy_ask_size","qqq_long_gross_pnl_usd","spy_short_gross_pnl_usd","gross_pnl_usd","valid_mark_sessions","missing_mark_sessions","last_observed_date"]
AGG_FIELDS=["strategy","policy","cost_scenario","slippage_per_option_share_usd","commission_per_contract_per_side_usd","qqq_long_contracts","spy_short_contracts","cohort_candidates","entered_n","entry_skipped_n","resolved_n","unresolved_n","wins","losses","flat","win_rate_pct","mean_net_pnl_usd","median_net_pnl_usd","total_net_pnl_usd","best_net_pnl_usd","worst_net_pnl_usd","profit_factor","mean_qqq_long_gross_pnl_usd","mean_spy_short_gross_pnl_usd","mean_entry_delay_sessions","mean_qqq_premium_debit_usd","mean_spy_premium_credit_usd","mean_abs_premium_mismatch_usd","mean_premium_match_pct","execution_depth_status"]

def blob_sha(data:bytes)->str:
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def pinned_csv(path:Path,sha:str)->list[dict[str,str]]:
    actual=blob_sha(path.read_bytes())
    if actual!=sha: raise ValueError(f"Git blob SHA mismatch for {path}: {actual} != {sha}")
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def pinned_json(path:Path,sha:str)->dict[str,Any]:
    actual=blob_sha(path.read_bytes())
    if actual!=sha:raise ValueError(f"Git blob SHA mismatch for {path}: {actual} != {sha}")
    return json.loads(path.read_text(encoding="utf-8"))
def i(v:Any)->int:return int(float(v))
def f(v:Any)->float|None:
    try:
        x=float(v);return x if math.isfinite(x) else None
    except (TypeError,ValueError):return None
def mean(xs:list[float])->float|None:return statistics.mean(xs) if xs else None
def match_pct(debit:float,credit:float)->float|None:
    hi=max(debit,credit);return min(debit,credit)/hi*100 if hi>0 else None
def rt_cost(slippage:float,commission:float)->float:return 2*(slippage*MULT+commission)

def validate_entry(strategy:str,qrow:dict|None,srow:dict|None,nq:int,ns:int)->tuple[bool,str]:
    if strategy==LEG_Q:
        if qrow is None:return False,"QQQ_SELECTED_CONTRACT_MISSING"
        if not base.standard_put_identity(qrow,"QQQ"):return False,"QQQ_CONTRACT_IDENTITY_INVALID"
        if not base.valid_quote(qrow,require_positive_bid=True):return False,"QQQ_ENTRY_BID_ASK_INVALID"
        if base.displayed_size(qrow,"ask")<nq:return False,"QQQ_LONG_ASK_SIZE_INSUFFICIENT"
        return True,"OK"
    if strategy==LEG_S:
        if srow is None:return False,"SPY_SELECTED_CONTRACT_MISSING"
        if not base.standard_put_identity(srow,"SPY"):return False,"SPY_CONTRACT_IDENTITY_INVALID"
        if not base.valid_quote(srow,require_positive_bid=True):return False,"SPY_ENTRY_BID_ASK_INVALID"
        if base.displayed_size(srow,"bid")<ns:return False,"SPY_SHORT_BID_SIZE_INSUFFICIENT"
        return True,"OK"
    if nq<1 or ns<1:return False,"PAIR_REQUIRES_BOTH_LEGS"
    return base.entry_quotes_valid(qrow,srow,nq,ns)

def validate_exit(strategy:str,qrow:dict|None,srow:dict|None,nq:int,ns:int)->tuple[bool,str]:
    if strategy==LEG_Q:
        if qrow is None:return False,"QQQ_SELECTED_CONTRACT_MISSING"
        if not base.standard_put_identity(qrow,"QQQ"):return False,"QQQ_CONTRACT_IDENTITY_INVALID"
        if not base.valid_quote(qrow):return False,"QQQ_EXIT_BID_ASK_INVALID"
        if base.displayed_size(qrow,"bid")<nq:return False,"QQQ_LONG_BID_SIZE_INSUFFICIENT"
        return True,"OK"
    if strategy==LEG_S:
        if srow is None:return False,"SPY_SELECTED_CONTRACT_MISSING"
        if not base.standard_put_identity(srow,"SPY"):return False,"SPY_CONTRACT_IDENTITY_INVALID"
        if not base.valid_quote(srow):return False,"SPY_EXIT_BID_ASK_INVALID"
        if base.displayed_size(srow,"ask")<ns:return False,"SPY_SHORT_ASK_SIZE_INSUFFICIENT"
        return True,"OK"
    if nq<1 or ns<1:return False,"PAIR_REQUIRES_BOTH_LEGS"
    return base.exit_quotes_valid(qrow,srow,nq,ns)

def raw_pnl(nq:int,ns:int,qentry:float|None,sentry:float|None,qexit:float|None,sexit:float|None)->tuple[float,float,float]:
    qg=nq*MULT*(qexit-qentry) if nq and qentry is not None and qexit is not None else 0.0
    sg=ns*MULT*(sentry-sexit) if ns and sentry is not None and sexit is not None else 0.0
    return qg,sg,qg+sg

def collect_quotes(symbol:str,target_ids:set[str],start:str,end:str,cache:Path):
    years=[y for y in base.YEARS if int(start[:4])<=y<=int(end[:4])]
    paths=[];integrity=[]
    for year in years:
        p,m=base.download_verified(symbol,year,cache);paths.append(p);integrity.append(m)
    stats={"chain_dates":0,"put_rows":0,"last_chain_date":None};by_day={}
    for day,rows in base.iter_symbol_days(paths,symbol,start,end,stats):
        chosen={}
        for r in rows:
            ident=base.normalized_contract_id(r)
            if ident in target_ids:chosen[ident]=r
        if chosen:by_day[day]=chosen
    return by_day,integrity,stats

def load_inputs(args):
    cohorts=pinned_csv(Path(args.cohorts),ENTRY_SHA)
    old_trades=pinned_csv(Path(args.trades),TRADE_SHA)
    old_summary=pinned_json(Path(args.summary_json),SUMMARY_SHA)
    if len(cohorts)!=44 or len({r["episode_id"] for r in cohorts})!=44:
        raise ValueError(f"expected 44 distinct frozen cohorts; got {len(cohorts)}")
    q_u,q_um=base.download_verified("QQQ",None,Path(args.qqq_cache))
    s_u,s_um=base.download_verified("SPY",None,Path(args.spy_cache))
    qspots=base.load_spots(q_u,"QQQ");sspots=base.load_spots(s_u,"SPY")
    dates=sorted(d for d in set(qspots)&set(sspots) if args.start<=d<=args.end)
    if not dates:raise ValueError("no common QQQ/SPY underlying dates")
    sig_idx={d:n for n,d in enumerate(dates)}
    qids={base.normalized_contract_id({"contract_id":r["qqq_contract_id"]}) for r in cohorts}
    sids={base.normalized_contract_id({"contract_id":r["spy_contract_id"]}) for r in cohorts}
    qdata,qint,qstats=collect_quotes("QQQ",qids,args.start,args.end,Path(args.qqq_cache))
    sdata,sint,sstats=collect_quotes("SPY",sids,args.start,args.end,Path(args.spy_cache))
    for r in cohorts:
        if r["signal_date"][:10] not in sig_idx:raise ValueError(f"signal date not found in common sessions: {r['signal_date']}")
    integrity=[q_um,s_um]+qint+sint
    return cohorts,old_trades,old_summary,dates,sig_idx,qspots,sspots,qdata,sdata,integrity,qstats,sstats

def build_plans(cohorts:list[dict[str,str]],sig_idx:dict[str,int],maxn:int,cap:int)->list[dict[str,Any]]:
    out=[]
    for c in cohorts:
        sid=c["signal_date"][:10];expiry=c["expiry"][:10];eid=str(c["episode_id"])
        specs=[(LEG_Q,n,0) for n in range(1,maxn+1)]+[(LEG_S,0,n) for n in range(1,maxn+1)]
        specs += [(PAIR,nq,ns) for nq in range(1,min(maxn,cap-1)+1) for ns in range(1,min(maxn,cap-nq)+1)]
        for strategy,nq,ns in specs:
            out.append({"plan_id":f"{eid}:{strategy}:{nq}x{ns}","episode_id":eid,"signal_date":sid,"signal_index":sig_idx[sid],
             "expiry":expiry,"strategy":strategy,"qqq_long_contracts":nq,"spy_short_contracts":ns,
             "qqq_contract_id":base.normalized_contract_id({"contract_id":c["qqq_contract_id"]}),
             "spy_contract_id":base.normalized_contract_id({"contract_id":c["spy_contract_id"]}),
             "entry_status":"PENDING","entry_skip_reason":"","entry_attempt_count":0,"entry_defer_sessions":0,
             "entry_date":"","entry_delay_sessions":"","qqq_entry_ask":"","qqq_entry_bid":"","spy_entry_bid":"","spy_entry_ask":"",
             "qqq_entry_ask_size":"","spy_entry_bid_size":"","qqq_entry_premium_debit_usd":"","spy_entry_premium_credit_usd":"",
             "premium_abs_mismatch_usd":"","premium_match_pct":"","last_attempt_date":"","last_attempt_reason":""})
    return out

def entry_attempt(plan:dict[str,Any],day:str,idx:int,qmap:dict,smap:dict,qspots:dict,sspots:dict)->bool:
    qrow=qmap.get(plan["qqq_contract_id"]);srow=smap.get(plan["spy_contract_id"])
    nq=plan["qqq_long_contracts"];ns=plan["spy_short_contracts"]
    valid,reason=validate_entry(plan["strategy"],qrow,srow,nq,ns)
    plan["entry_attempt_count"]+=1;plan["last_attempt_date"]=day;plan["last_attempt_reason"]=reason
    if not valid:
        plan["entry_defer_sessions"]+=1
        if day>=plan["expiry"]:
            plan["entry_status"]="ENTRY_SKIPPED";plan["entry_skip_reason"]="NO_VALID_ENTRY_BEFORE_EXPIRY:"+reason
        return False
    if nq and day not in qspots:
        reason="QQQ_UNDERLYING_CLOSE_MISSING"
    elif ns and day not in sspots:
        reason="SPY_UNDERLYING_CLOSE_MISSING"
    else:reason=""
    if reason:
        plan["entry_defer_sessions"]+=1;plan["last_attempt_reason"]=reason
        if day>=plan["expiry"]:
            plan["entry_status"]="ENTRY_SKIPPED";plan["entry_skip_reason"]=reason
        return False
    plan["entry_status"]="ENTERED";plan["entry_date"]=day;plan["entry_delay_sessions"]=idx-plan["signal_index"]
    plan["last_attempt_reason"]="OK"
    plan["qqq_entry_ask"]=float(qrow["ask"]) if nq else ""
    plan["qqq_entry_bid"]=float(qrow["bid"]) if nq else ""
    plan["spy_entry_bid"]=float(srow["bid"]) if ns else ""
    plan["spy_entry_ask"]=float(srow["ask"]) if ns else ""
    plan["qqq_entry_ask_size"]=base.displayed_size(qrow,"ask") if nq else ""
    plan["spy_entry_bid_size"]=base.displayed_size(srow,"bid") if ns else ""
    qdeb=float(qrow["ask"])*MULT*nq if nq else None
    scred=float(srow["bid"])*MULT*ns if ns else None
    plan["qqq_entry_premium_debit_usd"]=qdeb if qdeb is not None else ""
    plan["spy_entry_premium_credit_usd"]=scred if scred is not None else ""
    if qdeb is not None and scred is not None:
        plan["premium_abs_mismatch_usd"]=abs(qdeb-scred)
        plan["premium_match_pct"]=match_pct(qdeb,scred) or ""
    return True

def spawn(plan:dict[str,Any],idx:int)->list[dict[str,Any]]:
    return [{**plan,"policy":p,"status":"OPEN","unresolved_reason":"","entry_index":idx,
      "pending_exit":False,"exit_signal_date":"","exit_signal_index":None,"exit_date":"","exit_delay_sessions":"",
      "exit_deferred_sessions":0,"exit_reason":"","exit_qqq_bid":"","exit_spy_ask":"",
      "exit_qqq_bid_size":"","exit_spy_ask_size":"","qqq_long_gross_pnl_usd":"","spy_short_gross_pnl_usd":"",
      "gross_pnl_usd":"","valid_mark_sessions":0,"missing_mark_sessions":0,"last_observed_date":plan["entry_date"]}
      for p in POLICIES]

def finish(pos:dict[str,Any],status:str,reason:str,day:str,idx:int|None=None,qrow:dict|None=None,srow:dict|None=None)->dict[str,Any]:
    pos["status"]=status;pos["unresolved_reason"]=reason;pos["last_observed_date"]=day
    if status=="RESOLVED":
        pos["exit_date"]=day
        pos["exit_delay_sessions"]=idx-pos["exit_signal_index"] if pos["exit_signal_index"] is not None else 0
        nq=pos["qqq_long_contracts"];ns=pos["spy_short_contracts"]
        pos["exit_qqq_bid"]=float(qrow["bid"]) if nq and qrow else ""
        pos["exit_spy_ask"]=float(srow["ask"]) if ns and srow else ""
        pos["exit_qqq_bid_size"]=base.displayed_size(qrow,"bid") if nq and qrow else ""
        pos["exit_spy_ask_size"]=base.displayed_size(srow,"ask") if ns and srow else ""
        qg,sg,gross=raw_pnl(nq,ns,f(pos["qqq_entry_ask"]) if nq else None,
                             f(pos["spy_entry_bid"]) if ns else None,
                             f(pos["exit_qqq_bid"]) if nq else None,
                             f(pos["exit_spy_ask"]) if ns else None)
        pos["qqq_long_gross_pnl_usd"]=qg;pos["spy_short_gross_pnl_usd"]=sg;pos["gross_pnl_usd"]=gross
    return pos

def process_active(active:list[dict[str,Any]],day:str,idx:int,qmap:dict,smap:dict)->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    remaining=[];done=[]
    for p in active:
        qrow=qmap.get(p["qqq_contract_id"]);srow=smap.get(p["spy_contract_id"]);p["last_observed_date"]=day
        nq=p["qqq_long_contracts"];ns=p["spy_short_contracts"]
        if p["pending_exit"]:
            valid,reason=validate_exit(p["strategy"],qrow,srow,nq,ns)
            if valid:
                done.append(finish(p,"RESOLVED","",day,idx,qrow,srow));continue
            p["exit_deferred_sessions"]+=1
            if day>=p["expiry"]:
                done.append(finish(p,"UNRESOLVED_EXPIRED_NO_EXECUTABLE_CLOSE",reason,day));continue
            remaining.append(p);continue
        if p["strategy"]==LEG_Q:marked=qrow is not None and base.valid_quote(qrow)
        elif p["strategy"]==LEG_S:marked=srow is not None and base.valid_quote(srow)
        else:marked=qrow is not None and srow is not None and base.valid_quote(qrow) and base.valid_quote(srow)
        if marked:p["valid_mark_sessions"]+=1
        else:p["missing_mark_sessions"]+=1
        if day>=p["expiry"]:
            done.append(finish(p,"UNRESOLVED_EXPIRED_NO_EXIT","EXPIRY_REACHED_BEFORE_EXIT_TRIGGER",day));continue
        age=idx-p["entry_index"];pol=POLICY_MAP[p["policy"]]
        dte=(date.fromisoformat(p["expiry"])-date.fromisoformat(day)).days
        trigger=age>=pol["hold_sessions"] if pol["hold_sessions"] is not None else dte<=7
        if trigger:
            p["pending_exit"]=True;p["exit_signal_date"]=day;p["exit_signal_index"]=idx
            p["exit_reason"]=f"HOLD_{pol['hold_sessions']}_SESSIONS" if pol["hold_sessions"] is not None else "DTE_LE_7"
        remaining.append(p)
    return remaining,done

def simulate(plans:list[dict[str,Any]],dates:list[str],qspots:dict,sspots:dict,qdata:dict,sdata:dict,maxn:int,cap:int):
    by_signal=defaultdict(list)
    for p in plans:by_signal[p["signal_index"]].append(p)
    pending=[];active=[];completed=[]
    for idx,day in enumerate(dates):
        if idx>0:pending.extend(by_signal.get(idx-1,[]))
        qmap=qdata.get(day,{});smap=sdata.get(day,{})
        active,done=process_active(active,day,idx,qmap,smap);completed.extend(done)
        next_pending=[]
        for p in pending:
            if p["entry_status"]!="PENDING":continue
            if day>p["expiry"]:
                p["entry_status"]="ENTRY_SKIPPED";p["entry_skip_reason"]="SOURCE_SESSION_AFTER_EXPIRY";continue
            entered=entry_attempt(p,day,idx,qmap,smap,qspots,sspots)
            if entered:active.extend(spawn(p,idx))
            elif p["entry_status"]=="PENDING":next_pending.append(p)
        pending=next_pending
    for p in pending:
        if p["entry_status"]=="PENDING":
            p["entry_status"]="ENTRY_SKIPPED";p["entry_skip_reason"]="SOURCE_END_BEFORE_VALID_ENTRY"
            if not p["last_attempt_date"]:
                p["last_attempt_date"]=dates[-1];p["last_attempt_reason"]="NO_LATER_SOURCE_SESSION"
    for p in active:completed.append(finish(p,"UNRESOLVED_SOURCE_END","SOURCE_END_BEFORE_EXECUTABLE_EXIT",dates[-1]))
    expected=44*(2*maxn+sum(1 for q in range(1,min(maxn,cap-1)+1) for s in range(1,min(maxn,cap-q)+1)))
    if len(plans)!=expected:raise ValueError(f"plan count mismatch: {len(plans)} vs {expected}")
    return completed,plans

def summarize_one(trades:list[dict[str,Any]],plans:list[dict[str,Any]],strategy:str,policy:str,cost:dict,nq:int,ns:int)->dict[str,Any]:
    candidates=[p for p in plans if p["strategy"]==strategy and i(p["qqq_long_contracts"])==nq and i(p["spy_short_contracts"])==ns]
    ids={p["plan_id"] for p in candidates}
    episodes=[r for r in trades if r["strategy"]==strategy and r["policy"]==policy and r["plan_id"] in ids]
    resolved=[r for r in episodes if r["status"]=="RESOLVED"]
    gross=[float(r["gross_pnl_usd"]) for r in resolved]
    pnl=[g-rt_cost(cost["slippage"],cost["commission"])*(nq+ns) for g in gross]
    qgross=[float(r["qqq_long_gross_pnl_usd"] or 0) for r in resolved]
    sgross=[float(r["spy_short_gross_pnl_usd"] or 0) for r in resolved]
    wins=sum(x>0.005 for x in pnl);losses=sum(x< -0.005 for x in pnl);flats=len(pnl)-wins-losses
    positive=sum(x for x in pnl if x>0);negative=-sum(x for x in pnl if x<0)
    entered=[p for p in candidates if p["entry_status"]=="ENTERED"]
    qdeb=[float(p["qqq_entry_premium_debit_usd"]) for p in entered if p["qqq_entry_premium_debit_usd"]!=""]
    scred=[float(p["spy_entry_premium_credit_usd"]) for p in entered if p["spy_entry_premium_credit_usd"]!=""]
    mismatches=[float(p["premium_abs_mismatch_usd"]) for p in entered if p["premium_abs_mismatch_usd"]!=""]
    matches=[float(p["premium_match_pct"]) for p in entered if p["premium_match_pct"]!=""]
    delays=[float(p["entry_delay_sessions"]) for p in entered if p["entry_delay_sessions"]!=""]
    return {"strategy":strategy,"policy":policy,"cost_scenario":cost["name"],"slippage_per_option_share_usd":cost["slippage"],
      "commission_per_contract_per_side_usd":cost["commission"],"qqq_long_contracts":nq,"spy_short_contracts":ns,
      "cohort_candidates":len(candidates),"entered_n":len(entered),"entry_skipped_n":len(candidates)-len(entered),
      "resolved_n":len(resolved),"unresolved_n":len(episodes)-len(resolved),"wins":wins,"losses":losses,"flat":flats,
      "win_rate_pct":wins/len(resolved)*100 if resolved else None,"mean_net_pnl_usd":mean(pnl),
      "median_net_pnl_usd":statistics.median(pnl) if pnl else None,"total_net_pnl_usd":sum(pnl) if pnl else None,
      "best_net_pnl_usd":max(pnl) if pnl else None,"worst_net_pnl_usd":min(pnl) if pnl else None,
      "profit_factor":positive/negative if negative>0 else (math.inf if positive>0 else (0.0 if pnl else None)),
      "mean_qqq_long_gross_pnl_usd":mean(qgross),"mean_spy_short_gross_pnl_usd":mean(sgross),
      "mean_entry_delay_sessions":mean(delays),"mean_qqq_premium_debit_usd":mean(qdeb),
      "mean_spy_premium_credit_usd":mean(scred),"mean_abs_premium_mismatch_usd":mean(mismatches),
      "mean_premium_match_pct":mean(matches),"execution_depth_status":"INDEPENDENT_SIDE_DEPTH_GATED_EOD_QUOTE_REPLAY"}

def summarize_baseline(old_trades:list[dict[str,str]],cohorts:list[dict[str,str]])->list[dict[str,Any]]:
    by_policy={p:[r for r in old_trades if r["policy"]==p] for p in POLICIES}
    entry={str(r["episode_id"]):r for r in cohorts};results=[]
    for cost in COSTS:
        for policy in POLICIES:
            opened=by_policy[policy];resolved=[r for r in opened if r["status"]=="RESOLVED"]
            pnl=[];qg=[];sg=[]
            for r in resolved:
                a=float(r["qqq_long_gross_pnl_usd"]);b=float(r["spy_short_gross_pnl_usd"])
                pnl.append(a+b-rt_cost(cost["slippage"],cost["commission"])*(i(r["long_qqq_qty"])+i(r["short_spy_qty"])))
                qg.append(a);sg.append(b)
            wins=sum(x>0.005 for x in pnl);losses=sum(x< -0.005 for x in pnl);flats=len(pnl)-wins-losses
            positive=sum(x for x in pnl if x>0);negative=-sum(x for x in pnl if x<0)
            ent=[entry[str(r["episode_id"])] for r in cohorts]
            qdeb=[float(r["qqq_long_premium_debit_usd"]) for r in ent]
            scred=[float(r["spy_short_premium_credit_usd"]) for r in ent]
            mm=[abs(a-b) for a,b in zip(qdeb,scred)]
            matches=[match_pct(a,b) for a,b in zip(qdeb,scred) if max(a,b)>0]
            results.append({"strategy":"PREMIUM_MATCHED_BASELINE","policy":policy,"cost_scenario":cost["name"],
              "slippage_per_option_share_usd":cost["slippage"],"commission_per_contract_per_side_usd":cost["commission"],
              "qqq_long_contracts":"VARIABLE","spy_short_contracts":"VARIABLE","cohort_candidates":len(opened),
              "entered_n":len(opened),"entry_skipped_n":0,"resolved_n":len(resolved),"unresolved_n":len(opened)-len(resolved),
              "wins":wins,"losses":losses,"flat":flats,"win_rate_pct":wins/len(resolved)*100 if resolved else None,
              "mean_net_pnl_usd":mean(pnl),"median_net_pnl_usd":statistics.median(pnl) if pnl else None,
              "total_net_pnl_usd":sum(pnl) if pnl else None,"best_net_pnl_usd":max(pnl) if pnl else None,
              "worst_net_pnl_usd":min(pnl) if pnl else None,"profit_factor":positive/negative if negative>0 else (math.inf if positive>0 else (0.0 if pnl else None)),
              "mean_qqq_long_gross_pnl_usd":mean(qg),"mean_spy_short_gross_pnl_usd":mean(sg),
              "mean_entry_delay_sessions":mean([float(r["entry_delay_sessions"]) for r in ent]),
              "mean_qqq_premium_debit_usd":mean(qdeb),"mean_spy_premium_credit_usd":mean(scred),
              "mean_abs_premium_mismatch_usd":mean(mm),"mean_premium_match_pct":mean([x for x in matches if x is not None]),
              "execution_depth_status":"BASELINE_SOURCE_ENTRY_EXIT_DEPTH_SCREENED"})
    return results

def aggregates(trades,plans,maxn:int,cap:int):
    rows=[]
    for cost in COSTS:
        for policy in POLICIES:
            for n in range(1,maxn+1):
                rows.append(summarize_one(trades,plans,LEG_Q,policy,cost,n,0))
                rows.append(summarize_one(trades,plans,LEG_S,policy,cost,0,n))
            for nq in range(1,min(maxn,cap-1)+1):
                for ns in range(1,min(maxn,cap-nq)+1):
                    rows.append(summarize_one(trades,plans,PAIR,policy,cost,nq,ns))
    o={LEG_Q:0,LEG_S:1,PAIR:2};co={c["name"]:n for n,c in enumerate(COSTS)};po={p:n for n,p in enumerate(POLICIES)}
    rows.sort(key=lambda r:(co[r["cost_scenario"]],po[r["policy"]],o[r["strategy"]],
      i(r["qqq_long_contracts"]) if str(r["qqq_long_contracts"]).isdigit() else 99,
      i(r["spy_short_contracts"]) if str(r["spy_short_contracts"]).isdigit() else 99))
    return rows

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]):
    import io
    b=io.StringIO(newline="");w=csv.DictWriter(b,fieldnames=fields,extrasaction="ignore",lineterminator="\n");w.writeheader()
    for r in rows:
        cooked={}
        for k in fields:
            v=r.get(k,"")
            if v is None or (isinstance(v,float) and not math.isfinite(v)):v=""
            elif isinstance(v,float):v=round(v,6)
            cooked[k]=v
        w.writerow(cooked)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(b.getvalue(),encoding="utf-8")

def usd(v):return "n/a" if v is None else "USD "+format(float(v),",.2f")
def pct(v):return "n/a" if v is None else f"{float(v):.2f}%"

def write_report(out:Path,agg:list,baseline:list,plans:list,cohorts:list,maxn:int,cap:int,window:dict):
    b=[r for r in baseline if r["cost_scenario"]=="BASE_COST"]
    qen=sum(p["strategy"]==LEG_Q and p["entry_status"]=="ENTERED" for p in plans)
    sen=sum(p["strategy"]==LEG_S and p["entry_status"]=="ENTERED" for p in plans)
    pen=sum(p["strategy"]==PAIR and p["entry_status"]=="ENTERED" for p in plans)
    npair=sum(1 for q in range(1,min(maxn,cap-1)+1) for s in range(1,min(maxn,cap-q)+1))
    lines=["# QQQ LONG PUT / SPY SHORT PUT — Independent-Leg Sizing V2","",
      "**Status: independent EOD quote-side replay; research only. No live sizing or orders; no merge to main.**","",
      "## Method","",
      f"- Frozen originally selected cohorts: {len(cohorts)}. Requested window: {window['start']} to {window['end']}; common underlying sessions: {window['sessions']}.",
      f"- QQQ LONG PUT standalone: N=1–{maxn}; SPY SHORT PUT standalone: N=1–{maxn}; fixed paired N:M combinations: {npair} with combined count <= {cap}.",
      "- Exact original contract IDs are reused; each plan starts no earlier than the next common session after the signal. Failed entry-side depth defers; entry is skipped by expiry/source end.",
      "- QQQ standalone entry/exit depends only on QQQ quote and Ask/Bid depth. SPY standalone depends only on SPY quote and Bid/Ask depth. Fixed pairs require both legs at entry and exit.",
      "- Entries use QQQ Ask and SPY Bid; exits use QQQ Bid and SPY Ask. No forward-filling or contract substitutions.",
      "- Costs: zero, base USD 0.05 per option share per side plus USD 0.65 per contract per side, and adverse USD 0.10/share plus USD 0.65/side.",
      "- Displayed EOD depth is a screening gate, not a guaranteed fill. These are not exchange-confirmed executions.","",
      "## Entry coverage","",
      f"- QQQ-only plans: {len(cohorts)*maxn}; entered {qen}; skipped {len(cohorts)*maxn-qen}.",
      f"- SPY-only plans: {len(cohorts)*maxn}; entered {sen}; skipped {len(cohorts)*maxn-sen}.",
      f"- Pair plans: {len(cohorts)*npair}; entered {pen}; skipped {len(cohorts)*npair-pen}.",
      "- Candidate-level defer/skip reasons and entry side sizes are recorded in the attempt CSV; exit size values and unresolved states are in the raw trade files.","",
      "## Original premium-matched baseline reference (base costs)","",
      "Baseline numbers come from the frozen prior run. Entry/outcome coverage and fixed sizing differ across grid cells, so they are reference comparisons, not automatically a matched experiment.","",
      "| Exit policy | Resolved/opened | Win/loss | Win rate | Mean net P&L | Total net P&L | Mean QQQ debit | Mean SPY credit | Premium match |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in b:lines.append(f"| {r['policy']} | {r['resolved_n']}/{r['cohort_candidates']} | {r['wins']}/{r['losses']} | {pct(r['win_rate_pct'])} | {usd(r['mean_net_pnl_usd'])} | {usd(r['total_net_pnl_usd'])} | {usd(r['mean_qqq_premium_debit_usd'])} | {usd(r['mean_spy_premium_credit_usd'])} | {pct(r['mean_premium_match_pct'])} |")
    lines += ["","## Independent legs (base costs)","","| Policy | Standalone leg | N | Entered/candidate | Resolved/entered | Win rate | Mean net P&L | Total net P&L | Worst resolved |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        for strategy,n in ((LEG_Q,1),(LEG_Q,4),(LEG_Q,maxn),(LEG_S,1),(LEG_S,4),(LEG_S,maxn)):
            qn,sn=(n,0) if strategy==LEG_Q else (0,n)
            r=next(x for x in agg if x["strategy"]==strategy and x["policy"]==policy and x["cost_scenario"]=="BASE_COST" and x["qqq_long_contracts"]==qn and x["spy_short_contracts"]==sn)
            lines.append(f"| {policy} | {strategy.replace('_STANDALONE','').replace('_',' ')} | {n} | {r['entered_n']}/{r['cohort_candidates']} | {r['resolved_n']}/{r['entered_n']} | {pct(r['win_rate_pct'])} | {usd(r['mean_net_pnl_usd'])} | {usd(r['total_net_pnl_usd'])} | {usd(r['worst_net_pnl_usd'])} |")
    lines += ["","## Fixed paired examples (base costs; premium cash flows shown)","","| Policy | QQQ:SPY | Entered/candidate | Resolved/entered | Win rate | Mean net P&L | Mean QQQ debit | Mean SPY credit | Match score | Worst resolved |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        for nq,ns in ((1,1),(1,5),(4,4),(4,5),(5,1)):
            if nq+ns>cap or max(nq,ns)>maxn:continue
            r=next(x for x in agg if x["strategy"]==PAIR and x["policy"]==policy and x["cost_scenario"]=="BASE_COST" and x["qqq_long_contracts"]==nq and x["spy_short_contracts"]==ns)
            lines.append(f"| {policy} | {nq}:{ns} | {r['entered_n']}/{r['cohort_candidates']} | {r['resolved_n']}/{r['entered_n']} | {pct(r['win_rate_pct'])} | {usd(r['mean_net_pnl_usd'])} | {usd(r['mean_qqq_premium_debit_usd'])} | {usd(r['mean_spy_premium_credit_usd'])} | {pct(r['mean_premium_match_pct'])} | {usd(r['worst_net_pnl_usd'])} |")
    lines += ["","## Limits","","- This replay fixes the earlier flaw: each standalone leg has its own entry attempts, exit trigger, quote availability and depth gate. Paired positions still close as a pair.",
      "- Fixed N:M does not imply equal premium or equal risk. Inspect debit, credit, mismatch and match score before comparing paired results.",
      "- Unresolved and entry-skipped outcomes stay separate and are not assigned zero. Premium-matched baseline has dynamic quantities and a different denominator/entry policy from fixed grid cells.",
      "- EOD quote history is from a public preservation mirror; SHA pins establish file identity, not exchange authenticity. No early assignment, broker margin, financing, taxes, compounding, forced liquidation or intraday path is modeled.","",
      "## Files","","- entry_attempts.csv: one row per cohort and tested sizing plan, with deferrals and final entry result.",
      "- independent_leg_trades.csv: standalone positions with leg-specific exits and quote depth.",
      "- fixed_pair_trades.csv: pairs with both-leg entry/exit depth checks.",
      "- independent_leg_sizing.csv: standalone N performance, three cost assumptions.",
      "- fixed_pair_cross_grid.csv: all paired N:M cases under the total contract cap.",
      "- premium_matched_baseline.csv: frozen prior run, recalculated under the cost assumptions.",
      "- source_manifest.json: pinned output inputs and hashes.",""]
    (out/"summary.md").write_text("\n".join(lines),encoding="utf-8")

def run(args):
    if date.fromisoformat(args.start)>date.fromisoformat(args.end):raise ValueError("start must be <= end")
    if not 1<=args.max_leg_contracts<=9 or not 2<=args.max_total_contracts<=9:raise ValueError("leg max must be 1..9 and pair cap 2..9")
    cohorts,old_trades,old_summary,dates,sig_idx,qspots,sspots,qdata,sdata,integrity,qstats,sstats=load_inputs(args)
    plans=build_plans(cohorts,sig_idx,args.max_leg_contracts,args.max_total_contracts)
    trades,plans=simulate(plans,dates,qspots,sspots,qdata,sdata,args.max_leg_contracts,args.max_total_contracts)
    baseline=summarize_baseline(old_trades,cohorts)
    agg=aggregates(trades,plans,args.max_leg_contracts,args.max_total_contracts)
    # Reconcile matched-size pairs that also retain the original entry date and resolved exit cohort.
    old={(str(r["episode_id"]),r["policy"]):r for r in old_trades};reconciled=0
    for r in trades:
        prior=old.get((str(r["episode_id"]),r["policy"]))
        if r["strategy"]==PAIR and prior and prior["status"]=="RESOLVED" and r["status"]=="RESOLVED" and r["entry_date"]==prior["entry_date"] and i(r["qqq_long_contracts"])==i(prior["long_qqq_qty"]) and i(r["spy_short_contracts"])==i(prior["short_spy_qty"]):
            pnl=float(r["gross_pnl_usd"])-rt_cost(0.05,0.65)*(i(r["qqq_long_contracts"])+i(r["spy_short_contracts"]))
            if abs(pnl-float(prior["net_pnl_usd"]))<0.02:reconciled+=1
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"entry_attempts.csv",plans,ENTRY_FIELDS)
    write_csv(out/"independent_leg_trades.csv",[r for r in trades if r["strategy"] in (LEG_Q,LEG_S)],TRADE_FIELDS)
    write_csv(out/"fixed_pair_trades.csv",[r for r in trades if r["strategy"]==PAIR],TRADE_FIELDS)
    write_csv(out/"independent_leg_sizing.csv",[r for r in agg if r["strategy"] in (LEG_Q,LEG_S)],AGG_FIELDS)
    write_csv(out/"fixed_pair_cross_grid.csv",[r for r in agg if r["strategy"]==PAIR],AGG_FIELDS)
    write_csv(out/"premium_matched_baseline.csv",baseline,AGG_FIELDS)
    manifest={"schema":"qqq-spy-independent-leg-sizing.v2","status":"FULL_INDEPENDENT_QUOTE_SIDE_REPLAY",
      "pinned_inputs":{"entry_cohort_git_blob_sha":ENTRY_SHA,"trade_episodes_git_blob_sha":TRADE_SHA,"summary_json_git_blob_sha":SUMMARY_SHA},
      "source":{"repository":base.SOURCE_REPO,"tree_commit":base.SOURCE_COMMIT},
      "window":{"start":args.start,"end":args.end,"common_underlying_sessions":len(dates),"first_session":dates[0],"last_common_session":dates[-1]},
      "cohort_count":len(cohorts),"parameters":{"max_standalone_contracts":args.max_leg_contracts,"max_pair_contracts":args.max_total_contracts,
       "cost_scenarios":COSTS,"exit_policies":list(POLICIES),
       "pair_grid_cells_per_policy_cost":sum(1 for nq in range(1,min(args.max_leg_contracts,args.max_total_contracts-1)+1) for ns in range(1,min(args.max_leg_contracts,args.max_total_contracts-nq)+1))},
      "controls":{"standalone_entry_exit_depth_independent":True,"pair_requires_both_legs":True,"quote_forward_fill":False,"contract_substitution":False,"confirmed_exchange_fills":False},
      "source_file_integrity":{"verified_files":integrity,"qqq_option_chain_stats":qstats,"spy_option_chain_stats":sstats},
      "reconciliation":{"matched_qty_entry_date_resolved_pnl_matches_source":reconciled,"source_trade_rows":len(old_trades)}}
    (out/"source_manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    write_report(out,agg,baseline,plans,cohorts,args.max_leg_contracts,args.max_total_contracts,{"start":args.start,"end":args.end,"sessions":len(dates)})
    result={"status":"COMPLETED_WITH_UNRESOLVEDS" if any(r["unresolved_n"] for r in agg) else "COMPLETED",
      "frozen_cohorts":len(cohorts),"plans":len(plans),"entered_plans":sum(p["entry_status"]=="ENTERED" for p in plans),
      "skipped_plans":sum(p["entry_status"]!="ENTERED" for p in plans),"trade_episodes":len(trades),
      "standalone_trade_episodes":sum(r["strategy"] in (LEG_Q,LEG_S) for r in trades),"pair_trade_episodes":sum(r["strategy"]==PAIR for r in trades),
      "source_reconciliation_count":reconciled,"output_dir":str(out)}
    (out/"summary.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return result

def parse_args():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--start",default="2018-03-01");p.add_argument("--end",default="2025-12-15")
    p.add_argument("--max-leg-contracts",type=int,default=9);p.add_argument("--max-total-contracts",type=int,default=9)
    p.add_argument("--cohorts",default=ENTRY_PATH);p.add_argument("--trades",default=TRADE_PATH);p.add_argument("--summary-json",default=SUMMARY_PATH)
    p.add_argument("--qqq-cache",default=str(Path.home()/".cache"/"qqq-options-independent-leg-v2"));p.add_argument("--spy-cache",default=str(Path.home()/".cache"/"spy-options-independent-leg-v2"))
    p.add_argument("--out",default="research/qqq_spy_put_independent_leg_v1/results/latest");return p.parse_args()
if __name__=="__main__":print(json.dumps(run(parse_args()),indent=2,allow_nan=False))
