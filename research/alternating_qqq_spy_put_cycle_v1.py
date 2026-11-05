#!/usr/bin/env python3
"""Alternating SPY/QQQ put cycles with 21-DTE entries and one/two-week holds."""
from __future__ import annotations
import argparse, csv, json, math, statistics, sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE_DIR=HERE/"qqq_spy_put_fixed_ratio_size_gated_v1"
sys.path.insert(0,str(BASE_DIR))
import qqq_spy_put_premium_matched_phase_v1 as base

START_DEFAULT,END_DEFAULT="2018-03-01","2025-12-15"
DTE_MIN,DTE_MAX,DTE_TARGET=18,24,21
SHORT_DELTA_TARGET=0.25
LONG_DELTA_LOW,LONG_DELTA_HIGH,LONG_DELTA_TARGET=0.60,0.70,0.65
LONG_QTY,SHORT_QTY,MULTIPLIER=1,6,100
STRIDE=5
SLIPPAGE_PER_SHARE,COMMISSION_PER_CONTRACT_SIDE=0.05,0.65
DEFAULT_NAV=100000.0
ARM_CONFIG={
 "SPY_SHORT_QQQ_LONG_only":{"mode":"fixed_A","hold":5},
 "QQQ_SHORT_SPY_LONG_only":{"mode":"fixed_B","hold":5},
 "alternate_weekly_close":{"mode":"alternate","hold":5},
 "alternate_two_week_staggered":{"mode":"alternate","hold":10},
}

def choose_contract_pair(short_rows,long_rows,short_symbol,long_symbol,day,short_spot,long_spot,
                         dte_min=DTE_MIN,dte_max=DTE_MAX,dte_target=DTE_TARGET):
    if not short_rows or not long_rows or short_spot<=0 or long_spot<=0:return None
    date.fromisoformat(day)
    def expiry_map(rows,symbol):
        out={}
        for row in rows:
            if not base.standard_put_identity(row,symbol) or base.as_day(row.get("date"))!=day:continue
            if not base.valid_quote(row,require_positive_bid=True):continue
            expiry=base.as_day(row.get("expiration"))
            try:dte=(date.fromisoformat(expiry)-date.fromisoformat(day)).days
            except ValueError:continue
            if dte_min<=dte<=dte_max:out[expiry]=dte
        return out
    short_exp,long_exp=expiry_map(short_rows,short_symbol),expiry_map(long_rows,long_symbol)
    choices=[]
    for expiry in sorted(set(short_exp)&set(long_exp)):
        dte=short_exp[expiry]
        shorts=[]
        for row in short_rows:
            if not base.standard_put_identity(row,short_symbol) or base.as_day(row.get("date"))!=day:continue
            if base.as_day(row.get("expiration"))!=expiry or not base.valid_quote(row,require_positive_bid=True):continue
            delta,strike=base.num(row.get("delta")),base.num(row.get("strike"))
            if delta is None or not base.DELTA_MIN<=abs(delta)<=base.DELTA_MAX or strike is None or strike<=0:continue
            bid_size,ask_size=base.displayed_size(row,"bid"),base.displayed_size(row,"ask")
            if bid_size<SHORT_QTY or ask_size<SHORT_QTY:continue
            bid,ask=float(row["bid"]),float(row["ask"])
            shorts.append({"row":row,"id":base.normalized_contract_id(row),"strike":strike,
                "abs_delta":abs(delta),"bid":bid,"ask":ask,"bid_size":bid_size,"ask_size":ask_size,
                "oi":base.num(row.get("open_interest")) or 0.0,
                "spread":(ask-bid)/max((ask+bid)/2,1e-9)})
        if not shorts:continue
        short_leg=min(shorts,key=lambda x:(abs(x["abs_delta"]-SHORT_DELTA_TARGET),-x["bid_size"],-x["oi"],x["spread"],x["id"]))
        target_ask=SHORT_QTY*short_leg["bid"]
        longs=[]
        for row in long_rows:
            if not base.standard_put_identity(row,long_symbol) or base.as_day(row.get("date"))!=day:continue
            if base.as_day(row.get("expiration"))!=expiry or not base.valid_quote(row,require_positive_bid=True):continue
            delta,strike=base.num(row.get("delta")),base.num(row.get("strike"))
            if delta is None or not LONG_DELTA_LOW<=abs(delta)<=LONG_DELTA_HIGH or strike is None or strike<=0:continue
            bid_size,ask_size=base.displayed_size(row,"bid"),base.displayed_size(row,"ask")
            if bid_size<LONG_QTY or ask_size<LONG_QTY:continue
            bid,ask=float(row["bid"]),float(row["ask"])
            longs.append({"row":row,"id":base.normalized_contract_id(row),"strike":strike,
                "abs_delta":abs(delta),"bid":bid,"ask":ask,"bid_size":bid_size,"ask_size":ask_size,
                "oi":base.num(row.get("open_interest")) or 0.0,
                "spread":(ask-bid)/max((ask+bid)/2,1e-9),"premium_error":abs(ask-target_ask)})
        if not longs:continue
        long_leg=min(longs,key=lambda x:(x["premium_error"],abs(x["abs_delta"]-LONG_DELTA_TARGET),
            -x["ask_size"],-x["oi"],x["spread"],x["id"]))
        match=100.0*(1.0-long_leg["premium_error"]/max(target_ask,long_leg["ask"],0.01))
        choices.append(((abs(dte-dte_target),long_leg["premium_error"]/max(target_ask,0.01),
            abs(short_leg["abs_delta"]-SHORT_DELTA_TARGET),abs(long_leg["abs_delta"]-LONG_DELTA_TARGET),
            -(short_leg["bid_size"]+long_leg["ask_size"]),expiry),
            expiry,dte,short_leg,long_leg,target_ask,match))
    if not choices:return None
    _,expiry,dte,short_leg,long_leg,target_ask,match=min(choices,key=lambda x:x[0])
    sm=base.put_moneyness(short_spot,short_leg["strike"]);lm=base.put_moneyness(long_spot,long_leg["strike"])
    return {"signal_date":day,"expiry":expiry,"signal_dte":dte,"short_symbol":short_symbol,"long_symbol":long_symbol,
        "short_contract_id":short_leg["id"],"short_strike":short_leg["strike"],
        "short_abs_delta":short_leg["abs_delta"],"short_signal_bid":short_leg["bid"],"short_signal_ask":short_leg["ask"],
        "short_signal_bid_size":short_leg["bid_size"],"long_contract_id":long_leg["id"],"long_strike":long_leg["strike"],
        "long_abs_delta":long_leg["abs_delta"],"long_signal_bid":long_leg["bid"],"long_signal_ask":long_leg["ask"],
        "long_signal_ask_size":long_leg["ask_size"],"long_target_ask_signal":target_ask,
        "long_premium_match_pct_signal":match,"long_premium_error_signal":long_leg["ask"]-target_ask,
        "short_spot_signal":float(short_spot),"long_spot_signal":float(long_spot),
        "short_moneyness_signal":sm["status"],"short_otm_pct_signal":sm["otm_pct"],
        "long_moneyness_signal":lm["status"],"long_otm_pct_signal":lm["otm_pct"]}

def direction_for(mode,slot):
    if mode=="fixed_A":return "A"
    if mode=="fixed_B":return "B"
    if mode=="alternate":return "A" if slot%2==0 else "B"
    raise ValueError(mode)

def quote_sides_valid(long_row,short_row,is_entry):
    if long_row is None or short_row is None:return False,"SELECTED_CONTRACT_MISSING"
    if not base.valid_quote(long_row,require_positive_bid=True) or not base.valid_quote(short_row,require_positive_bid=True):
        return False,"INVALID_BID_ASK"
    if is_entry:
        if base.displayed_size(long_row,"ask")<LONG_QTY:return False,"LONG_ASK_SIZE_LT_1"
        if base.displayed_size(short_row,"bid")<SHORT_QTY:return False,"SHORT_BID_SIZE_LT_6"
    else:
        if base.displayed_size(long_row,"bid")<LONG_QTY:return False,"LONG_BID_SIZE_LT_1"
        if base.displayed_size(short_row,"ask")<SHORT_QTY:return False,"SHORT_ASK_SIZE_LT_6"
    return True,"OK"

def trade_pnl(ep,long_exit_bid,short_exit_ask):
    long_gross=LONG_QTY*MULTIPLIER*(long_exit_bid-ep["long_entry_ask"])
    short_gross=SHORT_QTY*MULTIPLIER*(ep["short_entry_bid"]-short_exit_ask)
    cost=2.0*(LONG_QTY+SHORT_QTY)*(SLIPPAGE_PER_SHARE*MULTIPLIER+COMMISSION_PER_CONTRACT_SIDE)
    return {"long_gross_pnl_usd":long_gross,"short_gross_pnl_usd":short_gross,
        "gross_pnl_usd":long_gross+short_gross,"estimated_round_trip_cost_usd":cost,
        "net_pnl_usd":long_gross+short_gross-cost}

def live_mark(ep,long_row,short_row):
    if not base.valid_quote(long_row) or not base.valid_quote(short_row):return None
    return trade_pnl(ep,float(long_row["bid"]),float(short_row["ask"]))["net_pnl_usd"]

def wilson(wins,n):
    if n<=0:return None,None
    z=1.959963984540054;p=wins/n;den=1+z*z/n
    c=(p+z*z/(2*n))/den;m=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return max(0,c-m)*100,min(1,c+m)*100

def drawdown(nav_values):
    peak=None;worst=0.0;worst_pct=0.0
    for v in nav_values:
        peak=v if peak is None else max(peak,v)
        dd=v-peak;ddp=dd/peak if peak and peak>0 else 0.0
        if dd<worst:worst,worst_pct=dd,ddp
    return worst,worst_pct*100

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text("",encoding="utf-8");return
    fields=list(dict.fromkeys(k for row in rows for k in row.keys()))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)

def simulate_arm(day_rows,spots,pair_map,mode,hold_sessions,initial_nav):
    dates=sorted(spots["QQQ"].keys() & spots["SPY"].keys())
    scheduled=set(range(0,len(dates),STRIDE))
    active=[];pending=None;trades=[];entries=[];skips=[];schedule_skips=[];daily=[]
    selected=entered=0
    for idx,day in enumerate(dates):
        qrows=day_rows["QQQ"].get(day,[]);srows=day_rows["SPY"].get(day,[])
        qmap,smap=base.rows_by_id(qrows),base.rows_by_id(srows)
        keep=[]
        for ep in active:
            age=idx-ep["entry_index"]
            lmap=qmap if ep["long_symbol"]=="QQQ" else smap
            ssmap=qmap if ep["short_symbol"]=="QQQ" else smap
            lrow=lmap.get(ep["long_contract_id"]);srow=ssmap.get(ep["short_contract_id"])
            mark=live_mark(ep,lrow,srow)
            if mark is not None:
                ep["last_mark_pnl_usd"]=mark;ep["last_mark_date"]=day;ep["last_mark_index"]=idx
            else:ep["mark_missing_sessions"]+=1
            trigger=age>=hold_sessions
            if ep["expiry"]<=day:
                lspot=spots[ep["long_symbol"]].get(day);sspot=spots[ep["short_symbol"]].get(day)
                if lspot is not None and sspot is not None:
                    li=max(ep["long_strike"]-lspot,0.0);si=max(ep["short_strike"]-sspot,0.0)
                    lg=LONG_QTY*MULTIPLIER*(li-ep["long_entry_ask"])
                    sg=SHORT_QTY*MULTIPLIER*(ep["short_entry_bid"]-si)
                    cost=2.0*(LONG_QTY+SHORT_QTY)*(SLIPPAGE_PER_SHARE*MULTIPLIER+COMMISSION_PER_CONTRACT_SIDE)
                    ep.update({"long_gross_pnl_usd":lg,"short_gross_pnl_usd":sg,"gross_pnl_usd":lg+sg,
                        "estimated_round_trip_cost_usd":cost,"net_pnl_usd":lg+sg-cost,
                        "status":"EXPIRY_INTRINSIC_SETTLEMENT","exit_date":day,"exit_source":"INTRINSIC"})
                    trades.append(ep);continue
                ep.update({"status":"UNRESOLVED_EXPIRED","exit_date":None});trades.append(ep);continue
            if trigger:
                valid,reason=quote_sides_valid(lrow,srow,False)
                if valid:
                    ep.update(trade_pnl(ep,float(lrow["bid"]),float(srow["ask"])))
                    ep.update({"status":"RESOLVED","exit_date":day,"exit_source":"OBSERVED_BID_ASK",
                        "exit_long_bid":float(lrow["bid"]),"exit_short_ask":float(srow["ask"]),"hold_sessions":age})
                    trades.append(ep);continue
                ep["exit_deferred_sessions"]+=1;ep["exit_last_reason"]=reason
            keep.append(ep)
        active=keep

        if pending is not None and idx>pending["signal_index"]:
            lmap=qmap if pending["long_symbol"]=="QQQ" else smap
            ssmap=qmap if pending["short_symbol"]=="QQQ" else smap
            lrow=lmap.get(pending["long_contract_id"]);srow=ssmap.get(pending["short_contract_id"])
            valid,reason=quote_sides_valid(lrow,srow,True)
            if valid:
                ep={**pending,"episode_id":f"{mode}-{pending['episode_id']}","arm":mode,
                    "entry_index":idx,"entry_date":day,"long_entry_ask":float(lrow["ask"]),
                    "short_entry_bid":float(srow["bid"]),"long_entry_bid":float(lrow["bid"]),
                    "short_entry_ask":float(srow["ask"]),"long_spot_entry":spots[pending["long_symbol"]].get(day),
                    "short_spot_entry":spots[pending["short_symbol"]].get(day),
                    "long_entry_abs_delta":abs(base.num(lrow.get("delta")) or 0.0),
                    "short_entry_abs_delta":abs(base.num(srow.get("delta")) or 0.0),
                    "long_premium_paid_usd":float(lrow["ask"])*MULTIPLIER*LONG_QTY,
                    "short_premium_received_usd":float(srow["bid"])*MULTIPLIER*SHORT_QTY,
                    "actual_entry_premium_match_pct":100.0*(1.0-abs(float(lrow["ask"])-SHORT_QTY*float(srow["bid"]))/
                        max(float(lrow["ask"]),SHORT_QTY*float(srow["bid"]),0.01)),
                    "net_opening_cashflow_usd":MULTIPLIER*(SHORT_QTY*float(srow["bid"])-LONG_QTY*float(lrow["ask"])),
                    "short_assignment_notional_usd":SHORT_QTY*MULTIPLIER*float(pending["short_strike"]),
                    "mark_missing_sessions":0,"last_mark_pnl_usd":None,"last_mark_index":idx,
                    "exit_deferred_sessions":0,"status":"OPEN"}
                entered+=1;entries.append(ep.copy());active.append(ep);pending=None
            else:
                pending["entry_defer_sessions"]+=1;pending["last_entry_reason"]=reason
                if day>=pending["expiry"]:
                    skips.append({"episode_id":pending["episode_id"],"signal_date":pending["signal_date"],
                        "direction":pending["direction"],"reason":"NO_EXECUTABLE_ENTRY_BEFORE_EXPIRY",
                        "last_attempt_date":day,"last_reason":reason});pending=None

        if idx in scheduled:
            slot=idx//STRIDE
            if pending is not None:
                schedule_skips.append({"signal_date":day,"slot":slot,"reason":"PRIOR_ENTRY_STILL_PENDING"})
            else:
                direction=direction_for(ARM_CONFIG[mode]["mode"],slot)
                pair=pair_map.get(day,{}).get(direction)
                if pair is None:
                    schedule_skips.append({"signal_date":day,"slot":slot,"direction":direction,
                        "reason":"NO_ELIGIBLE_DTE21_CROSS_PUT_PAIR"})
                else:
                    selected+=1;pending={**pair,"direction":direction,"signal_index":idx,
                        "episode_id":selected,"entry_defer_sessions":0}

        realized=sum(float(t["net_pnl_usd"]) for t in trades if t.get("net_pnl_usd") is not None)
        unrealized=0.0;short_notional=0.0;stale=0
        for ep in active:
            lmap=qmap if ep["long_symbol"]=="QQQ" else smap
            ssmap=qmap if ep["short_symbol"]=="QQQ" else smap
            mark=live_mark(ep,lmap.get(ep["long_contract_id"]),ssmap.get(ep["short_contract_id"]))
            if mark is None:mark=ep.get("last_mark_pnl_usd");stale+=1
            else:ep["last_mark_pnl_usd"]=mark;ep["last_mark_index"]=idx
            unrealized+=float(mark or 0.0)
            short_notional+=float(ep["short_assignment_notional_usd"])
        pnl=realized+unrealized
        daily.append({"date":day,"arm":mode,"realized_pnl_usd":realized,"unrealized_pnl_usd":unrealized,
            "total_pnl_usd":pnl,"nav_usd":initial_nav+pnl,"active_cohorts":len(active),
            "active_short_put_assignment_notional_usd":short_notional,"stale_mark_cohorts":stale})

    if pending is not None:
        skips.append({"episode_id":pending["episode_id"],"signal_date":pending["signal_date"],
            "direction":pending["direction"],"reason":"SOURCE_END_WITH_ENTRY_PENDING","last_attempt_date":dates[-1]})
    for ep in active:
        ep.update({"status":"UNRESOLVED_SOURCE_END","exit_date":None});trades.append(ep)
    navs=[float(r["nav_usd"]) for r in daily];worst_dd,worst_dd_pct=drawdown(navs)
    resolved=[t for t in trades if t.get("status") in ("RESOLVED","EXPIRY_INTRINSIC_SETTLEMENT") and t.get("net_pnl_usd") is not None]
    pnls=[float(t["net_pnl_usd"]) for t in resolved];wins=sum(v>0.005 for v in pnls)
    low,high=wilson(wins,len(pnls))
    years=(date.fromisoformat(dates[-1])-date.fromisoformat(dates[0])).days/365.25
    final_nav=navs[-1] if navs else initial_nav
    cagr=(final_nav/initial_nav)**(1/years)-1 if years>0 and final_nav>0 else None
    open_unresolved=[t for t in trades if str(t.get("status","")).startswith("UNRESOLVED")]
    return {"arm":mode,"hold_sessions":hold_sessions,"scheduled_opportunities":len(scheduled),
        "selected_signals":selected,"entered_cohorts":entered,"entry_skipped":len(skips),
        "schedule_skipped":len(schedule_skips),"resolved_trades":len(resolved),"unresolved_trades":len(open_unresolved),
        "wins":wins,"losses":sum(v<-.005 for v in pnls),"win_rate_pct":100*wins/len(pnls) if pnls else None,
        "win_rate_wilson95_pct":[low,high],"mean_trade_net_pnl_usd":statistics.mean(pnls) if pnls else None,
        "median_trade_net_pnl_usd":statistics.median(pnls) if pnls else None,"total_resolved_trade_net_pnl_usd":sum(pnls) if pnls else 0.0,
        "best_trade_net_pnl_usd":max(pnls) if pnls else None,"worst_trade_net_pnl_usd":min(pnls) if pnls else None,
        "median_signal_premium_match_pct":statistics.median([float(e["long_premium_match_pct_signal"]) for e in entries]) if entries else None,
        "median_actual_entry_premium_match_pct":statistics.median([float(e["actual_entry_premium_match_pct"]) for e in entries]) if entries else None,
        "median_actual_long_put_abs_delta":statistics.median([float(e["long_entry_abs_delta"]) for e in entries]) if entries else None,
        "median_actual_short_put_abs_delta":statistics.median([float(e["short_entry_abs_delta"]) for e in entries]) if entries else None,
        "median_short_assignment_notional_per_cohort_usd":statistics.median([float(e["short_assignment_notional_usd"]) for e in entries]) if entries else None,
        "max_concurrent_layers":max((int(r["active_cohorts"]) for r in daily),default=0),
        "peak_open_short_assignment_notional_usd":max((float(r["active_short_put_assignment_notional_usd"]) for r in daily),default=0.0),
        "starting_nav_usd":initial_nav,"ending_nav_usd":final_nav,"total_portfolio_pnl_usd":final_nav-initial_nav,
        "mean_annual_portfolio_pnl_usd":(final_nav-initial_nav)/years if years>0 else None,
        "portfolio_cagr_pct":cagr*100 if cagr is not None else None,
        "max_drawdown_usd":worst_dd,"max_drawdown_pct":worst_dd_pct,
        "days_below_starting_nav_pct":100*sum(v<initial_nav for v in navs)/len(navs) if navs else None,
        "source_window_years":years,"daily_nav_rows":daily,"trades":trades,"entries":entries,
        "skips":skips,"schedule_skips":schedule_skips}

def build_pair_map(paths,spots,common_dates,start_day,end_day):
    stats={"QQQ":{"chain_dates":0,"put_rows":0,"last_chain_date":None},
           "SPY":{"chain_dates":0,"put_rows":0,"last_chain_date":None}}
    qi=iter(base.iter_symbol_days(paths["QQQ"],"QQQ",start_day,end_day,stats["QQQ"]))
    si=iter(base.iter_symbol_days(paths["SPY"],"SPY",start_day,end_day,stats["SPY"]))
    qitem,sitem=next(qi,None),next(si,None)
    pair_map={}
    for idx,day in enumerate(common_dates):
        while qitem is not None and qitem[0]<day:qitem=next(qi,None)
        while sitem is not None and sitem[0]<day:sitem=next(si,None)
        qrows=qitem[1] if qitem is not None and qitem[0]==day else []
        srows=sitem[1] if sitem is not None and sitem[0]==day else []
        if qitem is not None and qitem[0]==day:qitem=next(qi,None)
        if sitem is not None and sitem[0]==day:sitem=next(si,None)
        if idx%STRIDE!=0:continue
        qspot,sspot=spots["QQQ"].get(day),spots["SPY"].get(day)
        pair_a=choose_contract_pair(srows,qrows,"SPY","QQQ",day,sspot,qspot) if qspot and sspot else None
        pair_b=choose_contract_pair(qrows,srows,"QQQ","SPY",day,qspot,sspot) if qspot and sspot else None
        pair_map[day]={"A":pair_a,"B":pair_b}
    return pair_map,stats


def collect_sparse_quotes(paths,needed_ids,start_day,end_day):
    sparse={"QQQ":{},"SPY":{}}
    stats={}
    for symbol in ("QQQ","SPY"):
        symbol_stats={"chain_dates":0,"put_rows":0,"last_chain_date":None}
        ids=needed_ids[symbol]
        if ids:
            for day,rows in base.iter_symbol_days(paths[symbol],symbol,start_day,end_day,symbol_stats):
                selected=[row for row in rows if base.normalized_contract_id(row) in ids]
                if selected:sparse[symbol][day]=selected
        stats[symbol]=symbol_stats
    return sparse,stats


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--start",default=START_DEFAULT);p.add_argument("--end",default=END_DEFAULT)
    p.add_argument("--qqq-cache",default=str(Path.home()/".cache"/"qqq-options-full-history"))
    p.add_argument("--spy-cache",default=str(Path.home()/".cache"/"spy-options-cross-put-v1"))
    p.add_argument("--out",default="research/alternating_qqq_spy_put_cycle_v1/results/latest")
    p.add_argument("--initial-nav",type=float,default=DEFAULT_NAV)
    args=p.parse_args()
    if args.initial_nav<=0:raise ValueError("--initial-nav must be positive")
    years=[y for y in base.YEARS if int(args.start[:4])<=y<=int(args.end[:4])]
    integrity=[];paths={"QQQ":[],"SPY":[]};spots={}
    for symbol,cache_name in (("QQQ",args.qqq_cache),("SPY",args.spy_cache)):
        cache=Path(cache_name)
        for year in years:
            path,meta=base.download_verified(symbol,year,cache);paths[symbol].append(path);integrity.append(meta)
        upath,meta=base.download_verified(symbol,None,cache);integrity.append(meta);spots[symbol]=base.load_spots(upath,symbol)
    common_dates=sorted(d for d in spots["QQQ"].keys() & spots["SPY"].keys() if args.start<=d<=args.end)
    if len(common_dates)<100:raise RuntimeError(f"Insufficient common QQQ/SPY dates: {len(common_dates)}")
    pair_map,signal_chain_stats=build_pair_map(paths,spots,common_dates,args.start,args.end)
    needed_ids={"QQQ":set(),"SPY":set()}
    for choices in pair_map.values():
        for pair in choices.values():
            if pair is not None:
                needed_ids[pair["short_symbol"]].add(pair["short_contract_id"])
                needed_ids[pair["long_symbol"]].add(pair["long_contract_id"])
    day_rows,selected_quote_stats=collect_sparse_quotes(paths,needed_ids,args.start,args.end)
    chain_stats={"signal_scan":signal_chain_stats,"selected_contract_quote_scan":selected_quote_stats,
        "selected_contract_ids":{k:len(v) for k,v in needed_ids.items()}}
    results={}
    for mode,config in ARM_CONFIG.items():
        results[mode]=simulate_arm(day_rows,spots,pair_map,mode,config["hold"],args.initial_nav)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    summary=[]
    for mode,r in results.items():
        summary.append({k:v for k,v in r.items() if k not in {"daily_nav_rows","trades","entries","skips","schedule_skips"}})
        write_csv(out/f"{mode}_daily_nav.csv",r["daily_nav_rows"])
        write_csv(out/f"{mode}_trades.csv",r["trades"])
        write_csv(out/f"{mode}_entries.csv",r["entries"])
        write_csv(out/f"{mode}_skips.csv",r["skips"]+r["schedule_skips"])
    write_csv(out/"portfolio_arm_summary.csv",summary)
    manifest={"study_id":"ALTERNATING_SPY_QQQ_PUT_CYCLE_21DTE_V1","status":"OBSERVED_HISTORICAL_EOD_QUOTE_REPLAY",
        "source_repository":base.SOURCE_REPO,"source_commit":base.SOURCE_COMMIT,"source_integrity":integrity,
        "source_window":{"start":args.start,"end":args.end,"first_common_session":common_dates[0],"last_common_session":common_dates[-1]},
        "option_chain_coverage":chain_stats,"common_sessions":len(common_dates),"initial_nav_usd":args.initial_nav,
        "contract_setup":{"long_qty":1,"short_qty":6,"multiplier":100,"short_abs_delta_target":SHORT_DELTA_TARGET,
            "long_abs_delta_band":[LONG_DELTA_LOW,LONG_DELTA_HIGH],"long_abs_delta_target":LONG_DELTA_TARGET,
            "dte_band":[DTE_MIN,DTE_MAX],"dte_target":DTE_TARGET,"common_expiry_required":True,
            "premium_match_target":"long put Ask nearest 6x short put Bid; match reported, not assumed"},
        "cadence":{"new_signal_every_common_sessions":STRIDE,"alternation":"A=SPY short/QQQ long; B=QQQ short/SPY long; flips by fixed slot even if skipped",
            "arms":{k:v for k,v in ARM_CONFIG.items()}},
        "costs":{"slippage_per_option_share_per_side_usd":SLIPPAGE_PER_SHARE,"commission_per_contract_per_side_usd":COMMISSION_PER_CONTRACT_SIDE},
        "portfolio_ledger":{"starting_nav":args.initial_nav,"daily_nav":"initial NAV + realized episode net P&L + open cohort net bid/ask mark P&L",
            "mark":"long put at bid; short put at ask; last mark carried when quotes absent",
            "margin":"not constrained; peak short assignment notional is warning metric only"},
        "results":summary,"limitations":[
            "Public historical EOD quote mirror; hashes prove file identity, not exchange/OPRA authenticity.",
            "EOD bid/ask and displayed size are not verified multi-leg fills.",
            "Premium equality does not equalize Delta, dollar Delta, gamma, vega, max loss, collateral, or assignment risk.",
            "QQQ/SPY basis and relative-performance risk remains; their downside beta is not identical.",
            "Fixed contract quantities are not constrained by margin, forced liquidation, financing, or assignment cash.",
            "Overlapping cohort P&L is represented in daily NAV; unresolved end-of-source cohorts are carried at last available marks.",
            "2018-03-01 to 2025-12-15 historical data cannot establish future performance."
        ]}
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding="utf-8")
    lines=["# Alternating SPY / QQQ Short-Put and Opposite-Index Long-Put Cycle","",
        f"- Sample: {common_dates[0]} to {common_dates[-1]} ({len(common_dates)} common sessions).",
        "- Each cohort: short 6 puts at |Delta| nearest 0.25, long 1 opposite-index put at |Delta| 0.60–0.70 (target 0.65).",
        "- Common expiration required; DTE nearest 21 within 18–24 calendar days.",
        "- Long-put Ask selected closest to 6 x short-put Bid within Delta band; actual entry match reported separately.",
        "- Signal at EOD; entry no earlier than the next common session. New signal every 5 common sessions.","",
        "## Arms","","| Arm | Entered | Resolved | Win % | Mean/trade | Median/trade | Worst/trade | Ending NAV | CAGR | Max DD | Peak short assignment notional |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in summary:
        lines.append(f"| {r['arm']} | {r['entered_cohorts']} | {r['resolved_trades']} | "
            f"{r['win_rate_pct'] if r['win_rate_pct'] is not None else '—'} | "
            f"{r['mean_trade_net_pnl_usd'] if r['mean_trade_net_pnl_usd'] is not None else '—'} | "
            f"{r['median_trade_net_pnl_usd'] if r['median_trade_net_pnl_usd'] is not None else '—'} | "
            f"{r['worst_trade_net_pnl_usd'] if r['worst_trade_net_pnl_usd'] is not None else '—'} | "
            f"{r['ending_nav_usd']:.2f} | {r['portfolio_cagr_pct'] if r['portfolio_cagr_pct'] is not None else '—'} | "
            f"{r['max_drawdown_pct']:.2f}% | {r['peak_open_short_assignment_notional_usd']:.2f} |")
    lines += ["","## Interpretation","","- alternate_two_week_staggered opens a new opposite-side cohort each week and holds each cohort up to 10 sessions, normally creating two concurrent layers.",
        "- A 1:6 contract ratio is not a hedge ratio. Premium matching does not equalize Dollar Delta, convexity, notional or assignment.",
        "- CAGR/MaxDD use an unconstrained fixed-size P&L ledger on the stated NAV; they are not evidence of broker buying-power feasibility.",
        "- Per-trade episode P&L overlaps; use daily NAV for the portfolio view.",""]
    (out/"study_report.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"COMPLETED","common_sessions":len(common_dates),"arms":summary},indent=2,allow_nan=False))

if __name__=="__main__":main()
