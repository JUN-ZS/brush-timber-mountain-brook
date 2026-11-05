#!/usr/bin/env python3
"""QQQ/SPY 1:6 CALL pair: every 10 sessions alternate; one long-call Ask targets 6x short-call Bid."""
from __future__ import annotations
import argparse, csv, json, math, statistics, sys, re
from collections import Counter
from datetime import date
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE_DIR=HERE/"qqq_spy_put_fixed_ratio_size_gated_v1"
sys.path.insert(0,str(BASE_DIR))
import qqq_spy_put_premium_matched_phase_v1 as base


def standard_call_identity(row,symbol):
    """Validate standard OCC call identifier and row symbol/type/expiry/strike."""
    ident=base.normalized_contract_id(row)
    m=re.fullmatch(re.escape(symbol)+r"(\d{6})C(\d{8})",ident)
    if not m or str(row.get("symbol","")).upper()!=symbol:return False
    if str(row.get("type","")).strip().lower() not in ("c","call"):return False
    try:expiry=__import__("datetime").datetime.strptime(m.group(1),"%y%m%d").date().isoformat()
    except ValueError:return False
    strike=base.num(row.get("strike"))
    return (base.as_day(row.get("expiration"))==expiry and strike is not None and strike>0
            and abs(strike-int(m.group(2))/1000.0)<0.00051)

def call_moneyness(spot,strike):
    s,k=base.num(spot),base.num(strike)
    if s is None or k is None or s<=0 or k<=0:return {"otm_pct":None,"status":"INVALID"}
    pct=(k-s)/s*100.0
    status="OTM" if k>s else "ITM" if k<s else "ATM"
    return {"otm_pct":pct,"status":status}

def call_intrinsic_value(spot,strike):
    return max(float(spot)-float(strike),0.0)

def iter_call_symbol_days(paths,symbol,start_day,end_day,stats):
    """Stream CALL rows from the pinned full-history option-chain Parquet files."""
    import pyarrow.parquet as pq
    previous_day=""
    for path in paths:
        parquet=pq.ParquetFile(path)
        missing=sorted(set(base.OPTION_COLUMNS)-set(parquet.schema_arrow.names))
        if missing:raise ValueError(f"{path.name} missing required columns: {missing}")
        current_day,rows=None,[]
        def emit(day,day_rows):
            if day and start_day<=day<=end_day and day_rows:
                stats["chain_dates"]+=1;stats["call_rows"]+=len(day_rows);stats["last_chain_date"]=day
                return day,day_rows
            return None
        for batch in parquet.iter_batches(batch_size=65536,columns=base.OPTION_COLUMNS):
            for row in batch.to_pylist():
                day=base.as_day(row.get("date"))
                if not day:continue
                if previous_day and day<previous_day:
                    raise ValueError(f"{path.name} is not date ordered at {day} after {previous_day}")
                previous_day=day
                if current_day is None:current_day=day
                elif day!=current_day:
                    item=emit(current_day,rows)
                    if item is not None:yield item
                    current_day,rows=day,[]
                if (start_day<=day<=end_day and str(row.get("symbol","")).upper()==symbol
                    and str(row.get("type","")).strip().lower() in ("c","call")):
                    rows.append(row)
        item=emit(current_day,rows)
        if item is not None:yield item


START_DEFAULT,END_DEFAULT="2018-03-01","2025-12-15"
DTE_MIN,DTE_MAX,DTE_TARGET=14,28,20
SHORT_DELTA_TARGET=0.25
LONG_QTY,SHORT_QTY,MULTIPLIER=1,6,100
STRIDE=10
ENTRY_SIGNAL_OFFSET=0
SLIPPAGE_PER_SHARE,COMMISSION_PER_CONTRACT_SIDE=0.05,0.65
DEFAULT_NAV=100000.0
ARM_CONFIG={
 "alternate_dte20_every10":{"mode":"alternate","schedule_offset":ENTRY_SIGNAL_OFFSET,"max_hold_sessions":20,"exit_remaining_dte":7},
}

def premium_cashflow_usd(long_ask,short_bid):
    """Natural-side gross opening credit less debit; positive means net credit."""
    return round(MULTIPLIER*(SHORT_QTY*float(short_bid)-LONG_QTY*float(long_ask)),2)


def premium_match_pct(long_debit_usd,short_credit_usd):
    """Symmetric premium-size similarity score; diagnostic only, never an entry gate."""
    long_debit=abs(float(long_debit_usd));short_credit=abs(float(short_credit_usd))
    scale=max(long_debit,short_credit)
    return 100.0 if scale<=0 else 100.0*(1.0-abs(long_debit-short_credit)/scale)


def choose_contract_pair(short_rows,long_rows,short_symbol,long_symbol,day,short_spot,long_spot,
                         dte_min=DTE_MIN,dte_max=DTE_MAX,dte_target=DTE_TARGET):
    """Select short call Delta near +.25; match one opposite-index long-call Ask to 6x short Bid.

    Long-leg Delta is intentionally unconstrained. Long-leg displayed Bid size is not an
    entry gate because the buy is executed at Ask; it remains an exit/liquidity consideration.
    """
    if not short_rows or not long_rows or short_spot<=0 or long_spot<=0:return None
    date.fromisoformat(day)

    def expiry_map(rows,symbol,is_short):
        out={}
        for row in rows:
            if not standard_call_identity(row,symbol) or base.as_day(row.get("date"))!=day:continue
            if not base.valid_quote(row,require_positive_bid=is_short):continue
            expiry=base.as_day(row.get("expiration"))
            try:dte=(date.fromisoformat(expiry)-date.fromisoformat(day)).days
            except ValueError:continue
            if dte_min<=dte<=dte_max:out[expiry]=dte
        return out

    short_exp=expiry_map(short_rows,short_symbol,True)
    long_exp=expiry_map(long_rows,long_symbol,False)
    choices=[]
    for expiry in sorted(set(short_exp)&set(long_exp)):
        dte=short_exp[expiry]
        shorts=[]
        for row in short_rows:
            if not standard_call_identity(row,short_symbol) or base.as_day(row.get("date"))!=day:continue
            if base.as_day(row.get("expiration"))!=expiry or not base.valid_quote(row,require_positive_bid=True):continue
            delta,strike=base.num(row.get("delta")),base.num(row.get("strike"))
            if delta is None or delta<=0 or not base.DELTA_MIN<=abs(delta)<=base.DELTA_MAX or strike is None or strike<=0:continue
            bid_size,ask_size=base.displayed_size(row,"bid"),base.displayed_size(row,"ask")
            # Six displayed contracts at Bid are required to open the six short contracts.
            # Do not reject merely because the future closing Ask size is thin.
            if bid_size<SHORT_QTY:continue
            bid,ask=float(row["bid"]),float(row["ask"])
            shorts.append({"row":row,"id":base.normalized_contract_id(row),"strike":strike,
                "abs_delta":abs(delta),"delta":delta,"bid":bid,"ask":ask,"bid_size":bid_size,"ask_size":ask_size,
                "oi":base.num(row.get("open_interest")) or 0.0,
                "spread":(ask-bid)/max((ask+bid)/2,1e-9)})
        if not shorts:continue
        short_leg=min(shorts,key=lambda x:(abs(x["abs_delta"]-SHORT_DELTA_TARGET),
            -x["bid_size"],-x["oi"],x["spread"],x["id"]))
        target_ask=SHORT_QTY*short_leg["bid"]

        longs=[]
        for row in long_rows:
            if not standard_call_identity(row,long_symbol) or base.as_day(row.get("date"))!=day:continue
            if base.as_day(row.get("expiration"))!=expiry or not base.valid_quote(row):continue
            strike=base.num(row.get("strike"))
            if strike is None or strike<=0:continue
            ask_size=base.displayed_size(row,"ask")
            # One displayed Ask is sufficient to buy the long call. No long Delta/Bid-size gate.
            if ask_size<LONG_QTY:continue
            bid,ask=float(row["bid"]),float(row["ask"])
            delta=base.num(row.get("delta"))
            longs.append({"row":row,"id":base.normalized_contract_id(row),"strike":strike,
                "abs_delta":abs(delta) if delta is not None else None,"bid":bid,"ask":ask,
                "bid_size":base.displayed_size(row,"bid"),"ask_size":ask_size,
                "oi":base.num(row.get("open_interest")) or 0.0,
                "spread":(ask-bid)/max((ask+bid)/2,1e-9),
                "premium_error":abs(ask-target_ask)})
        if not longs:continue
        long_leg=min(longs,key=lambda x:(x["premium_error"],-x["ask_size"],
            -x["oi"],x["spread"],x["id"]))
        match=premium_match_pct(long_leg["ask"]*MULTIPLIER*LONG_QTY,target_ask*MULTIPLIER)
        choices.append(((abs(dte-dte_target),long_leg["premium_error"]/max(target_ask,0.01),
            abs(short_leg["abs_delta"]-SHORT_DELTA_TARGET),
            -(short_leg["bid_size"]+long_leg["ask_size"]),expiry),
            expiry,dte,short_leg,long_leg,target_ask,match))
    if not choices:return None
    _,expiry,dte,short_leg,long_leg,target_ask,match=min(choices,key=lambda x:x[0])
    sm=call_moneyness(short_spot,short_leg["strike"])
    lm=call_moneyness(long_spot,long_leg["strike"])
    return {"signal_date":day,"expiry":expiry,"signal_dte":dte,
        "short_symbol":short_symbol,"long_symbol":long_symbol,
        "short_contract_id":short_leg["id"],"short_strike":short_leg["strike"],
        "short_abs_delta":short_leg["abs_delta"],"short_delta":short_leg["delta"],"short_signal_bid":short_leg["bid"],
        "short_signal_ask":short_leg["ask"],"short_signal_bid_size":short_leg["bid_size"],
        "long_contract_id":long_leg["id"],"long_strike":long_leg["strike"],
        "long_abs_delta":long_leg["abs_delta"],"long_signal_bid":long_leg["bid"],
        "long_signal_ask":long_leg["ask"],"long_signal_ask_size":long_leg["ask_size"],
        "long_target_ask_signal":target_ask,"long_premium_match_pct_signal":match,
        "long_premium_error_signal":long_leg["premium_error"],
        "opening_premium_cashflow_signal_usd":premium_cashflow_usd(long_leg["ask"],short_leg["bid"]),
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
    if not base.valid_quote(long_row) or not base.valid_quote(short_row,require_positive_bid=is_entry):
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
        if dd<worst:worst=dd
        if ddp<worst_pct:worst_pct=ddp
    return worst,worst_pct*100

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text("",encoding="utf-8");return
    fields=list(dict.fromkeys(k for row in rows for k in row.keys()))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)

def exit_trigger(age, day, expiry, max_hold_sessions=20, remaining_dte_limit=7):
    """Return the first scheduled exit condition; execution may defer for invalid quotes."""
    remaining_dte=(date.fromisoformat(expiry)-date.fromisoformat(day)).days
    if remaining_dte<=remaining_dte_limit:
        return True,"REMAINING_DTE_LE_7"
    if age>=max_hold_sessions:
        return True,"MAX_HOLD_20_SESSIONS"
    return False,None


def simulate_arm(day_rows,spots,pair_map,common_dates,mode,hold_sessions,exit_remaining_dte,schedule_offset,initial_nav):
    dates=list(common_dates)
    scheduled=set(range(schedule_offset,len(dates),STRIDE))
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
            trigger,trigger_reason=exit_trigger(age,day,ep["expiry"],hold_sessions,exit_remaining_dte)
            if ep["expiry"]<=day:
                lspot=spots[ep["long_symbol"]].get(day);sspot=spots[ep["short_symbol"]].get(day)
                if lspot is not None and sspot is not None:
                    li=call_intrinsic_value(lspot,ep["long_strike"]);si=call_intrinsic_value(sspot,ep["short_strike"])
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
                        "exit_trigger":trigger_reason,"exit_long_bid":float(lrow["bid"]),
                        "exit_short_ask":float(srow["ask"]),"hold_sessions":age})
                    trades.append(ep);continue
                ep["exit_deferred_sessions"]+=1;ep["exit_last_reason"]=reason
            keep.append(ep)
        active=keep

        if pending is not None and idx>pending["signal_index"]:
            direction=pending["direction"]
            pair=pair_map.get(day,{}).get(direction)
            if pair is None:
                skips.append({"episode_id":pending["episode_id"],"signal_date":pending["schedule_signal_date"],
                    "direction":direction,"reason":"NO_VALID_COMMON_EXPIRY_DELTA_PAIR","entry_date":day})
                pending=None
            else:
                chosen={**pair,"direction":direction,"signal_index":pending["signal_index"],
                    "schedule_signal_date":pending["schedule_signal_date"],"episode_id":pending["episode_id"]}
                lmap=qmap if chosen["long_symbol"]=="QQQ" else smap
                ssmap=qmap if chosen["short_symbol"]=="QQQ" else smap
                lrow=lmap.get(chosen["long_contract_id"]);srow=ssmap.get(chosen["short_contract_id"])
                valid,reason=quote_sides_valid(lrow,srow,True)
                if valid:
                    opening_cashflow=premium_cashflow_usd(float(lrow["ask"]),float(srow["bid"]))
                    long_premium_paid=float(lrow["ask"])*MULTIPLIER*LONG_QTY
                    short_premium_received=float(srow["bid"])*MULTIPLIER*SHORT_QTY
                    actual_match=premium_match_pct(long_premium_paid,short_premium_received)
                    ep={**chosen,"episode_id":f"{mode}-{chosen['episode_id']}","arm":mode,
                        "entry_index":idx,"entry_date":day,"long_entry_ask":float(lrow["ask"]),
                        "short_entry_bid":float(srow["bid"]),"long_entry_bid":float(lrow["bid"]),
                        "short_entry_ask":float(srow["ask"]),"long_spot_entry":spots[chosen["long_symbol"]].get(day),
                        "short_spot_entry":spots[chosen["short_symbol"]].get(day),
                        "long_entry_abs_delta":abs(base.num(lrow.get("delta")) or 0.0),
                        "short_entry_abs_delta":abs(base.num(srow.get("delta")) or 0.0),
                        "long_premium_paid_usd":long_premium_paid,
                        "short_premium_received_usd":short_premium_received,
                        "actual_entry_premium_match_pct":actual_match,
                        "net_opening_cashflow_usd":opening_cashflow,
                        "short_assignment_notional_usd":SHORT_QTY*MULTIPLIER*float(chosen["short_strike"]),
                        "mark_missing_sessions":0,"last_mark_pnl_usd":None,"last_mark_index":idx,
                        "exit_deferred_sessions":0,"status":"OPEN"}
                    entered+=1;entries.append(ep.copy());active.append(ep)
                else:
                    skips.append({"episode_id":pending["episode_id"],"signal_date":pending["schedule_signal_date"],
                        "direction":direction,"reason":reason,"entry_date":day})
                pending=None

        if idx in scheduled:
            slot=(idx-schedule_offset)//STRIDE
            if pending is not None:
                schedule_skips.append({"signal_date":day,"slot":slot,"reason":"PRIOR_ENTRY_STILL_PENDING"})
            else:
                direction=direction_for(ARM_CONFIG[mode]["mode"],slot)
                selected+=1
                pending={"direction":direction,"signal_index":idx,
                    "schedule_signal_date":day,"episode_id":selected}

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
        skips.append({"episode_id":pending["episode_id"],"signal_date":pending["schedule_signal_date"],
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
    return {"arm":mode,"max_hold_sessions":hold_sessions,"exit_remaining_dte_calendar_days":exit_remaining_dte,
        "scheduled_opportunities":len(scheduled),
        "selected_signals":selected,"entered_cohorts":entered,"entry_skipped":len(skips),
        "schedule_skipped":len(schedule_skips),"resolved_trades":len(resolved),"unresolved_trades":len(open_unresolved),
        "wins":wins,"losses":sum(v<-.005 for v in pnls),"win_rate_pct":100*wins/len(pnls) if pnls else None,
        "win_rate_wilson95_pct":[low,high],"mean_trade_net_pnl_usd":statistics.mean(pnls) if pnls else None,
        "median_trade_net_pnl_usd":statistics.median(pnls) if pnls else None,"total_resolved_trade_net_pnl_usd":sum(pnls) if pnls else 0.0,
        "best_trade_net_pnl_usd":max(pnls) if pnls else None,"worst_trade_net_pnl_usd":min(pnls) if pnls else None,
        "median_signal_premium_match_pct":statistics.median([float(e["long_premium_match_pct_signal"]) for e in entries]) if entries else None,
        "median_actual_entry_premium_match_pct":statistics.median([float(e["actual_entry_premium_match_pct"]) for e in entries]) if entries else None,
        "zero_opening_premium_entries":sum(abs(float(e["net_opening_cashflow_usd"]))<0.005 for e in entries),
        "nonzero_opening_premium_entries":sum(abs(float(e["net_opening_cashflow_usd"]))>=0.005 for e in entries),
        "mean_opening_premium_cashflow_usd":statistics.mean([float(e["net_opening_cashflow_usd"]) for e in entries]) if entries else None,
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
    stats={"QQQ":{"chain_dates":0,"call_rows":0,"last_chain_date":None},
           "SPY":{"chain_dates":0,"call_rows":0,"last_chain_date":None}}
    qi=iter(iter_call_symbol_days(paths["QQQ"],"QQQ",start_day,end_day,stats["QQQ"]))
    si=iter(iter_call_symbol_days(paths["SPY"],"SPY",start_day,end_day,stats["SPY"]))
    qitem,sitem=next(qi,None),next(si,None)
    pair_map={}
    for idx,day in enumerate(common_dates):
        while qitem is not None and qitem[0]<day:qitem=next(qi,None)
        while sitem is not None and sitem[0]<day:sitem=next(si,None)
        qrows=qitem[1] if qitem is not None and qitem[0]==day else []
        srows=sitem[1] if sitem is not None and sitem[0]==day else []
        if qitem is not None and qitem[0]==day:qitem=next(qi,None)
        if sitem is not None and sitem[0]==day:sitem=next(si,None)
        # Select from the actual next-session entry snapshot, not the prior signal quote.
        if idx<=ENTRY_SIGNAL_OFFSET or (idx-1-ENTRY_SIGNAL_OFFSET)%STRIDE!=0:continue
        qspot,sspot=spots["QQQ"].get(day),spots["SPY"].get(day)
        pair_a=choose_contract_pair(srows,qrows,"SPY","QQQ",day,sspot,qspot) if qspot and sspot else None
        pair_b=choose_contract_pair(qrows,srows,"QQQ","SPY",day,qspot,sspot) if qspot and sspot else None
        pair_map[day]={"A":pair_a,"B":pair_b}
    return pair_map,stats


def collect_sparse_quotes(paths,needed_ids,start_day,end_day):
    sparse={"QQQ":{},"SPY":{}}
    stats={}
    for symbol in ("QQQ","SPY"):
        symbol_stats={"chain_dates":0,"call_rows":0,"last_chain_date":None}
        ids=needed_ids[symbol]
        if ids:
            for day,rows in iter_call_symbol_days(paths[symbol],symbol,start_day,end_day,symbol_stats):
                selected=[row for row in rows if base.normalized_contract_id(row) in ids]
                if selected:sparse[symbol][day]=selected
        stats[symbol]=symbol_stats
    return sparse,stats


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--start",default=START_DEFAULT);p.add_argument("--end",default=END_DEFAULT)
    p.add_argument("--qqq-cache",default=str(Path.home()/".cache"/"qqq-options-full-history"))
    p.add_argument("--spy-cache",default=str(Path.home()/".cache"/"spy-options-cross-put-v1"))
    p.add_argument("--out",default="research/alternating_qqq_spy_call_cycle_v1/results/latest")
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
        results[mode]=simulate_arm(day_rows,spots,pair_map,common_dates,mode,
            config["max_hold_sessions"],config["exit_remaining_dte"],config["schedule_offset"],args.initial_nav)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    summary=[]
    for mode,r in results.items():
        summary.append({
            "arm": mode,
            "scheduled_opportunities": r["scheduled_opportunities"],
            "selected_signals": r["selected_signals"],
            "entered_cohorts": r["entered_cohorts"],
            "entry_skipped": r["entry_skipped"],
            "starting_nav_usd": r["starting_nav_usd"],
            "ending_nav_usd": r["ending_nav_usd"],
            "total_portfolio_pnl_usd": r["total_portfolio_pnl_usd"],
            "max_drawdown_usd": r["max_drawdown_usd"],
            "max_drawdown_pct": r["max_drawdown_pct"],
        })
        write_csv(out/f"{mode}_daily_nav.csv",r["daily_nav_rows"])
        write_csv(out/f"{mode}_trades.csv",r["trades"])
        write_csv(out/f"{mode}_entries.csv",r["entries"])
        write_csv(out/f"{mode}_skips.csv",r["skips"]+r["schedule_skips"])
    write_csv(out/"portfolio_arm_summary.csv",summary)
    manifest={"study_id":"ALTERNATING_SPY_QQQ_CALL_DTE20_EVERY10_V1","status":"OBSERVED_HISTORICAL_EOD_QUOTE_REPLAY",
        "source_repository":base.SOURCE_REPO,"source_commit":base.SOURCE_COMMIT,"source_integrity":integrity,
        "source_window":{"start":args.start,"end":args.end,"first_common_session":common_dates[0],"last_common_session":common_dates[-1]},
        "option_chain_coverage":chain_stats,"common_sessions":len(common_dates),"initial_nav_usd":args.initial_nav,
        "contract_setup":{"option_right":"CALL","long_qty":1,"short_qty":6,"multiplier":100,"short_abs_delta_target":SHORT_DELTA_TARGET,
            "long_delta_rule":"UNCONSTRAINED: select one opposite-index LONG CALL by Ask nearest to 6x SHORT CALL Bid",
            "dte_band":[DTE_MIN,DTE_MAX],"dte_target":DTE_TARGET,
            "dte_selection_rule":"nearest common expiry to target 20 calendar DTE within the 14-28 day execution window",
            "common_expiry_required":True,
            "premium_balance_target":"Select one opposite-index long-call Ask nearest to six times the selected short-call Bid; enter even when a residual net debit/credit remains",
            "entry_pair_selection":"short CALL Delta nearest +0.25, then one long CALL Ask nearest 6x short Bid; both legs from actual next-common-session EOD quotes"},
        "exit_rule":{"trigger":"remaining calendar DTE <= 7 OR maximum holding age >= 20 common sessions",
            "max_hold_sessions":20,"exit_remaining_dte_calendar_days":7,
            "execution":"defer only when required long Bid / short Ask size is unavailable"},
        "cadence":{"new_signal_every_common_sessions":STRIDE,"signal_anchor_common_session_offset":ENTRY_SIGNAL_OFFSET,"first_scheduled_signal_date":common_dates[ENTRY_SIGNAL_OFFSET],"first_entry_date":common_dates[ENTRY_SIGNAL_OFFSET+1],"alternation":"A=SPY SHORT CALL 6 / QQQ LONG CALL 1; B=QQQ SHORT CALL 6 / SPY LONG CALL 1; one new group every 10 common sessions and direction reverses each scheduled group",
            "arms":{k:v for k,v in ARM_CONFIG.items()}},
        "costs":{"slippage_per_option_share_per_side_usd":SLIPPAGE_PER_SHARE,"commission_per_contract_per_side_usd":COMMISSION_PER_CONTRACT_SIDE},
        "portfolio_ledger":{"starting_nav":args.initial_nav,"daily_nav":"initial NAV + realized episode net P&L + open cohort net bid/ask mark P&L",
            "mark":"long call at bid; short call at ask; last mark carried when quotes absent",
            "margin":"not constrained; peak short assignment notional is warning metric only"},
        "results":summary,"limitations":[
            "Public historical EOD quote mirror; hashes prove file identity, not exchange/OPRA authenticity.",
            "EOD bid/ask and displayed size are not verified multi-leg fills.",
            "Opening premium balance is approximate; net debit/credit, bid/ask spreads, commission, slippage, financing, collateral and assignment remain.",
            "Premium equality does not equalize Delta, dollar Delta, gamma, vega, max loss, collateral, or assignment risk.",
            "QQQ/SPY basis and relative-performance risk remains; their downside beta is not identical.",
            "Fixed contract quantities are not constrained by margin, forced liquidation, financing, or assignment cash.",
            "Overlapping cohort P&L is represented in daily NAV; unresolved end-of-source cohorts are carried at last available marks.",
            "2018-03-01 to 2025-12-15 historical data cannot establish future performance."
        ]}
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding="utf-8")
    r=summary[0]
    r=summary[0]
    lines=[
        "# QQQ / SPY CALL 配對策略 — DTE 20 目標、每 10 個交易日必開交替",
        "",
        f"- 回測區間：{common_dates[0]} 至 {common_dates[-1]}；共 {len(common_dates)} 個共同交易日。",
        "- 起始 NAV：USD 100,000。",
        "- 每 10 個共同交易日開新一組；A=SPY SHORT CALL 6 張／QQQ LONG CALL 1 張；B=QQQ SHORT CALL 6 張／SPY LONG CALL 1 張，逐組反轉。",
        "- DTE：以 20 個日曆日為目標，在 14–28 日共同到期合約中選最接近者；兩腿必須同一到期日。",
        "- SHORT CALL：|Delta| 最接近 0.25；LONG CALL：不設 Delta 限制，選 Ask 最接近 6 × SHORT CALL Bid 的一張合約。",
        "- 例：SHORT CALL Bid $4 × 6 張 = $24；LONG CALL Ask 目標 $24 × 1 張。實際差額按實際報價記入淨收／淨付，不因差額而跳過排程。",
        "- 退出：剩餘日曆 DTE <= 7，或持有達 20 個共同交易日，先到者觸發；若平倉報價／顯示張數不足，才延遲執行。",
        "",
        f"- 排程機會：{r['scheduled_opportunities']}；成功開倉：{r['entered_cohorts']}；未能成交：{r['entry_skipped']}。",
        "",
        "| 最終 NAV | 淨損益 | MaxDD (USD) | MaxDD (%) |",
        "|---:|---:|---:|---:|",
        f"| USD {r['ending_nav_usd']:,.2f} | USD {r['total_portfolio_pnl_usd']:,.2f} | USD {r['max_drawdown_usd']:,.2f} | {r['max_drawdown_pct']:.2f}% |",
        "",
    ]
    (out/"study_report.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"COMPLETED","common_sessions":len(common_dates),"arms":summary},indent=2,allow_nan=False))

if __name__=="__main__":main()
