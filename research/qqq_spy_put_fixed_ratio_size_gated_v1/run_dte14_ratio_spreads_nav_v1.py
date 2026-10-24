#!/usr/bin/env python3
"""DTE14 single-account NAV replay for QQQ1:SPY3 and QQQ1:SPY6 with matched SPY far-tail put spreads."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import qqq_spy_put_fixed_phase_v1 as eng
import spy_far_tail_hedge_v1 as hedge
import run_spy_far_tail_account_nav_v1 as navlib
import run_spy_far_tail_conditional_v1 as conditional

ROOT=Path(__file__).resolve().parent
RES=ROOT/"results"
OUT=RES/"dte14_ratio_spreads_nav_v1"
POLICY="HOLD_20_OR_DTE_LE_7"
ARM="DTE14"
TAIL_LABEL="TAIL_10_DELTA"
PHASES=range(5)
START_NAV=100000.0
M=100
EPS=1e-6
CONFIGS=(
    {"ratio":"1:3","short_qty":3,"tail_qty":0,"name":"1:3 / no FAR TAIL"},
    {"ratio":"1:3","short_qty":3,"tail_qty":3,"name":"1:3 / 3 FAR TAIL (fully paired)"},
    {"ratio":"1:6","short_qty":6,"tail_qty":0,"name":"1:6 / no FAR TAIL"},
    {"ratio":"1:6","short_qty":6,"tail_qty":3,"name":"1:6 / 3 FAR TAIL (half paired)"},
    {"ratio":"1:6","short_qty":6,"tail_qty":6,"name":"1:6 / 6 FAR TAIL (fully paired)"},
)

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def readj(path: Path) -> dict[str,Any]:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise ValueError(f"Expected JSON object: {path}")
    return x

def num(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except (TypeError,ValueError):
        return None

def writecsv(path: Path, rows: list[dict[str,Any]]) -> None:
    if not rows: raise ValueError(f"Refusing empty output: {path}")
    fields=[]; seen=set()
    for row in rows:
        for k in row:
            if k not in seen: fields.append(k); seen.add(k)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def spread_collateral(short_strike: float, tail_strike: float|None, short_qty: int, tail_qty: int) -> float:
    """Conservative reserve: full strike notional for uncovered shorts; strike width for matched verticals."""
    if short_qty<0 or tail_qty<0 or tail_qty>short_qty:
        raise ValueError("Tail quantity must be between zero and SPY short-put quantity")
    if tail_qty==0:
        return float(short_strike)*M*short_qty
    if tail_strike is None or not float(tail_strike)<float(short_strike):
        raise ValueError("A collateralizing SPY tail PUT must be strictly below the short PUT strike")
    paired=min(short_qty,tail_qty)
    uncovered=short_qty-paired
    return (float(short_strike)-float(tail_strike))*M*paired + float(short_strike)*M*uncovered

def account_collateral(pos: dict[str,dict[str,Any]]) -> float:
    return sum(spread_collateral(p["strike"],p.get("tail_strike"),p["sqty"],p["tail_qty"])
               for p in pos.values() if p["base_open"])

def put_intrinsic(strike: float, spot: float, qty: int) -> float:
    return max(float(strike)-float(spot),0.0)*M*int(qty)

def run_load(cache: Path):
    overlay_path=RES/"spy_far_tail_hedge_v1"/"manifest.json"
    selection_path=RES/"spy_far_tail_hedge_v1"/"entry_selection.csv"
    for p in (overlay_path,selection_path):
        if not p.is_file() or p.stat().st_size==0: raise FileNotFoundError(f"Missing frozen tail-selection input: {p}")
    om=readj(overlay_path)
    if om.get("status")!="COMPLETED": raise ValueError("Frozen unconditional tail selection is not COMPLETED")
    _,raw,input_hashes=hedge.load_base_ledgers(RES)
    conditional.validate_baseline_hashes(input_hashes,om.get("input_ledger_sha256"))
    base={}
    for r in raw.values():
        if str(r.get("arm"))!=ARM or str(r.get("policy"))!=POLICY: continue
        k=navlib.key(r)
        if k in base: raise ValueError(f"Duplicate baseline trade key {k}")
        base[k]=r
    if len(base)<100: raise ValueError("DTE14 baseline ledger is unexpectedly small")

    tails={}
    tail_rows_for_market={}
    with selection_path.open("r",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if str(r.get("arm"))!=ARM or str(r.get("tail_label"))!=TAIL_LABEL or str(r.get("tail_quantity"))!="3":
                continue
            ck=(ARM,int(float(r["phase"])),navlib.epnorm(r.get("episode_id")))
            if ck in tails: raise ValueError(f"Duplicate far-tail contract selection {ck}")
            tails[ck]=r
            if r.get("tail_contract_id"):
                tail_rows_for_market[str(len(tail_rows_for_market))]={"tail_contract_id":r["tail_contract_id"]}
    cohort_keys={(str(r["arm"]),int(r["phase"]),navlib.epnorm(r.get("episode_id"))) for r in base.values()}
    if not cohort_keys.issubset(set(tails)):
        raise ValueError(f"Missing frozen same-entry FAR TAIL selections for {len(cohort_keys-set(tails))} DTE14 cohorts")
    end=str(om["stream_stats"]["last_chain_date"])
    hm={"chain_last_date":end}
    book,market_dates,qspots,spots,pins,stream_stats,ids,first,market_end=navlib.load_market(base,tail_rows_for_market,hm,cache)
    if market_end!=end: raise ValueError("Market replay endpoint differs from frozen tail-selection endpoint")
    if len(pins)!=18: raise ValueError(f"Expected 18 pinned source files, found {len(pins)}")
    return base,tails,input_hashes,om,selection_path,book,market_dates,qspots,spots,pins,stream_stats,ids,first,market_end

def mark_position(p: dict[str,Any], day: str, book):
    missing=[]; expected=available=0; size_ok=True; value=0.0
    u=navlib.unit(p["slip"],p["comm"])
    q=navlib.quote_at(book,day,"QQQ",p["qid"])
    s=navlib.quote_at(book,day,"SPY",p["sid"])
    expected+=2
    if q is None: missing.append("QQQ:"+p["qid"])
    else:
        available+=1
        if q["bid_size"]<p["lqty"]: size_ok=False
        value+=q["bid"]*M*p["lqty"]-u*p["lqty"]
    if s is None: missing.append("SPY:"+p["sid"])
    else:
        available+=1
        if s["ask_size"]<p["sqty"]: size_ok=False
        value-=s["ask"]*M*p["sqty"]+u*p["sqty"]
    if p["tail_qty"]:
        t=navlib.quote_at(book,day,"SPY",p["tid"]); expected+=1
        if t is None: missing.append("SPY_TAIL:"+p["tid"])
        else:
            available+=1
            if t["bid_size"]<p["tail_qty"]: size_ok=False
            value+=t["bid"]*M*p["tail_qty"]-u*p["tail_qty"]
    return (None if missing else value),expected,available,missing,size_ok

def simulate(phase: int, cfg: dict[str,Any], trades: list[dict[str,Any]], tails,
             book,market_dates,qspots,spots,end: str):
    first_trade=min(str(r["entry_date"]) for r in trades)
    idx=market_dates.index(first_trade)
    startday=market_dates[max(0,idx-1)]
    dates=[d for d in market_dates if startday<=d<=end]
    ratio=cfg["ratio"]; sqty=int(cfg["short_qty"]); tail_qty=int(cfg["tail_qty"])
    account_id=f"DTE14|phase_{phase}|NAV_100000|RATIO_{ratio}|TAIL_{tail_qty}"
    cash=float(START_NAV); pos={}; entries=defaultdict(list)
    for r0 in trades:
        r=dict(r0); r["trade_key"]="|".join(map(str,navlib.key(r0)))
        entries[str(r["entry_date"])].append(r)
    curve=[]; gates=[]; trade_results=[]; counts=defaultdict(int); mismatches=0
    for day in dates:
        # Close the QQQ long, SPY short(s), and matched far-tail PUT as one defined-risk package.
        for k,p in list(pos.items()):
            if p["base_open"] and p["exit_date"]==day and not p["exit_attempted"]:
                p["exit_attempted"]=True
                q=navlib.quote_at(book,day,"QQQ",p["qid"])
                s=navlib.quote_at(book,day,"SPY",p["sid"])
                t=navlib.quote_at(book,day,"SPY",p["tid"]) if p["tail_qty"] else None
                executable=bool(q and s and q["bid_size"]>=p["lqty"] and s["ask_size"]>=p["sqty"])
                if p["tail_qty"]:
                    executable=executable and bool(t and t["bid_size"]>=p["tail_qty"])
                if executable:
                    u=navlib.unit(p["slip"],p["comm"])
                    pnl_q=p["lqty"]*M*(q["bid"]-p["qask"])
                    pnl_s=p["sqty"]*M*(p["sbid"]-s["ask"])
                    pnl_t=p["tail_qty"]*M*(t["bid"]-p["hask"]) if p["tail_qty"] else 0.0
                    total_cost=2*u*(p["lqty"]+p["sqty"]+p["tail_qty"])
                    cash+=q["bid"]*M*p["lqty"]-u*p["lqty"]
                    cash-=s["ask"]*M*p["sqty"]+u*p["sqty"]
                    if p["tail_qty"]: cash+=t["bid"]*M*p["tail_qty"]-u*p["tail_qty"]
                    pnl=pnl_q+pnl_s+pnl_t-total_cost
                    counts["base_exit_closed_n"]+=1
                    counts["tail_exit_closed_n"]+=int(bool(p["tail_qty"]))
                    counts["realized_pnl_usd"]+=pnl
                    if p["tail_qty"]: counts["tail_realized_pnl_usd"]+=pnl_t-2*u*p["tail_qty"]
                    if ratio=="1:3" and tail_qty==0 and p["source_pnl"] is not None and abs(p["source_pnl"]-pnl)>.03:
                        mismatches+=1
                    trade_results.append({"account_id":account_id,"arm":ARM,"phase":phase,"ratio":ratio,
                        "short_spy_qty":sqty,"tail_qty":tail_qty,"trade_key":k,"entry_date":p["entry_date"],
                        "exit_date":day,"result_type":"QUOTE_SIDE_CLOSE","pnl_q_long_usd":round(pnl_q-2*u*p["lqty"],2),
                        "pnl_spy_short_usd":round(pnl_s-2*u*p["sqty"],2),
                        "pnl_far_tail_usd":round(pnl_t-2*u*p["tail_qty"],2) if p["tail_qty"] else 0.0,
                        "net_pnl_usd":round(pnl,2),"source_base_pnl_usd":p["source_pnl"]})
                    p["base_open"]=False
            if p["base_open"] and p["expiry"]==day:
                # Use contractual intrinsic payoff for all same-expiry legs together if no complete package close.
                qspot=num(qspots.get(day)); sspot=num(spots.get(day))
                if qspot is not None and sspot is not None:
                    qpay=put_intrinsic(p["qstrike"],qspot,p["lqty"])
                    spay=put_intrinsic(p["strike"],sspot,p["sqty"])
                    tpay=put_intrinsic(p["tail_strike"],sspot,p["tail_qty"]) if p["tail_qty"] else 0.0
                    cash+=qpay-spay+tpay
                    u=navlib.unit(p["slip"],p["comm"])
                    entry_cf=(-p["qask"]*M*p["lqty"]-u*p["lqty"]+
                              p["sbid"]*M*p["sqty"]-u*p["sqty"]-
                              (p["hask"] or 0.0)*M*p["tail_qty"]-u*p["tail_qty"])
                    pnl=qpay-spay+tpay+entry_cf
                    counts["expiry_settlements_n"]+=1
                    counts["realized_pnl_usd"]+=pnl
                    if p["tail_qty"]: counts["tail_realized_pnl_usd"]+=tpay-p["hask"]*M*p["tail_qty"]-u*p["tail_qty"]
                    trade_results.append({"account_id":account_id,"arm":ARM,"phase":phase,"ratio":ratio,
                        "short_spy_qty":sqty,"tail_qty":tail_qty,"trade_key":k,"entry_date":p["entry_date"],
                        "exit_date":day,"result_type":"INTRINSIC_EXPIRY_SETTLEMENT",
                        "pnl_q_long_usd":round(qpay-p["qask"]*M*p["lqty"]-u*p["lqty"],2),
                        "pnl_spy_short_usd":round(-spay+p["sbid"]*M*p["sqty"]-u*p["sqty"],2),
                        "pnl_far_tail_usd":round(tpay-p["hask"]*M*p["tail_qty"]-u*p["tail_qty"],2) if p["tail_qty"] else 0.0,
                        "net_pnl_usd":round(pnl,2),"source_base_pnl_usd":p["source_pnl"]})
                    p["base_open"]=False
            if not p["base_open"]:
                pos.pop(k,None)

        # Replay frozen entries. The only strategy dimension changed here is SPY short size and matched tail quantity.
        for r in entries.get(day,[]):
            counts["base_entry_attempts_n"]+=1
            q=navlib.quote_at(book,day,"QQQ",r.get("qqq_contract_id"))
            s=navlib.quote_at(book,day,"SPY",r.get("spy_contract_id"))
            if not q or not s:
                counts["quote_rejected_n"]+=1
                gates.append({"account_id":account_id,"date":day,"event":"BASE_ENTRY","trade_key":r["trade_key"],
                    "decision":"REJECT_QUOTE","reason":"EXACT_ENTRY_CONTRACT_MISSING"})
                continue
            lqty=int(float(r["long_qqq_qty"]))
            if q["ask_size"]<lqty or s["bid_size"]<sqty:
                counts["quote_rejected_n"]+=1
                gates.append({"account_id":account_id,"date":day,"event":"BASE_ENTRY","trade_key":r["trade_key"],
                    "decision":"REJECT_QUOTE","reason":"BASE_ENTRY_SIDE_SIZE_BELOW_REQUIRED_QUANTITY",
                    "qqq_ask_size":q["ask_size"],"required_qqq_qty":lqty,"spy_bid_size":s["bid_size"],"required_spy_qty":sqty})
                continue
            if abs(q["ask"]-float(r["qqq_entry_ask"]))>.0001 or abs(s["bid"]-float(r["spy_entry_bid"]))>.0001:
                raise ValueError("Frozen entry quote mismatch "+r["trade_key"])
            ckey=(ARM,int(phase),navlib.epnorm(r.get("episode_id")))
            sel=tails.get(ckey,{})
            tid=""; hstrike=None; hask=None
            if tail_qty:
                if not sel.get("tail_contract_id") or num(sel.get("tail_strike")) is None:
                    counts["tail_quote_rejected_n"]+=1
                    gates.append({"account_id":account_id,"date":day,"event":"FAR_TAIL_ENTRY","trade_key":r["trade_key"],
                        "decision":"REJECT_QUOTE","reason":"NO_PRESELECTED_TAIL_CONTRACT"})
                    continue
                if str(sel.get("entry_date"))!=day or str(sel.get("expiry"))!=str(r.get("expiry")):
                    raise ValueError("Far-tail selection date/expiry differs from frozen base entry "+r["trade_key"])
                if str(sel.get("base_spy_short_contract_id"))!=str(r.get("spy_contract_id")):
                    raise ValueError("Far-tail selection is not tied to exact frozen SPY short contract "+r["trade_key"])
                hstrike=float(sel["tail_strike"])
                if not hstrike<float(r["spy_strike"]):
                    counts["tail_quote_rejected_n"]+=1
                    gates.append({"account_id":account_id,"date":day,"event":"FAR_TAIL_ENTRY","trade_key":r["trade_key"],
                        "decision":"REJECT_QUOTE","reason":"TAIL_STRIKE_NOT_BELOW_SHORT_STRIKE","tail_strike":hstrike,"short_strike":r["spy_strike"]})
                    continue
                tid=eng.normalized_contract_id({"contract_id":sel["tail_contract_id"]})
                t=navlib.quote_at(book,day,"SPY",tid)
                ask_expected=num(sel.get("tail_entry_ask"))
                if not t or t["ask_size"]<tail_qty or ask_expected is None or abs(t["ask"]-ask_expected)>.0001:
                    counts["tail_quote_rejected_n"]+=1
                    gates.append({"account_id":account_id,"date":day,"event":"FAR_TAIL_ENTRY","trade_key":r["trade_key"],
                        "decision":"REJECT_QUOTE","reason":"EXACT_TAIL_ASK_OR_SIZE_GATE_FAILED",
                        "required_tail_qty":tail_qty,"tail_ask_size":t["ask_size"] if t else 0})
                    continue
                hask=float(t["ask"])
            slip=float(r["base_slippage_per_share"]); comm=float(r["base_commission_per_contract_per_side"]); u=navlib.unit(slip,comm)
            shortstrike=float(r["spy_strike"])
            cash_delta=(-q["ask"]*M*lqty-u*lqty+s["bid"]*M*sqty-u*sqty-
                        (hask*M*tail_qty+u*tail_qty if tail_qty else 0.0))
            held=account_collateral(pos)
            needed=spread_collateral(shortstrike,hstrike,sqty,tail_qty)
            if cash+cash_delta+EPS<held+needed:
                counts["capital_rejected_n"]+=1
                gates.append({"account_id":account_id,"date":day,"event":"BASE_ENTRY","trade_key":r["trade_key"],
                    "decision":"REJECT_CAPITAL","reason":"CASH_BELOW_REQUIRED_DEFINED_RISK_RESERVE",
                    "cash_before":round(cash,2),"cash_delta":round(cash_delta,2),"held_collateral":round(held,2),
                    "new_collateral":round(needed,2),"free_cash_after_entry_before_reserve":round(cash+cash_delta-held-needed,2),
                    "short_spy_qty":sqty,"tail_qty":tail_qty,"short_strike":shortstrike,"tail_strike":hstrike})
                continue
            cash+=cash_delta
            counts["base_trades_opened_n"]+=1
            expiry=str(r.get("expiry") or "")
            status=str(r.get("status","")).upper()
            resolved=status=="RESOLVED"
            exitday=str(r.get("exit_date") or "") if resolved else ""
            pos[r["trade_key"]]={"base_open":True,"ratio":ratio,"tail_qty":tail_qty,
                "qid":eng.normalized_contract_id({"contract_id":r["qqq_contract_id"]}),
                "sid":eng.normalized_contract_id({"contract_id":r["spy_contract_id"]}),
                "tid":tid,"lqty":lqty,"sqty":sqty,"strike":shortstrike,"qstrike":float(r["qqq_strike"]),
                "tail_strike":hstrike,"expiry":expiry,"qask":float(q["ask"]),"sbid":float(s["bid"]),"hask":hask,
                "slip":slip,"comm":comm,"source_pnl":num(r.get("net_pnl_usd")),"status":status,
                "exit_date":exitday,"exit_attempted":False,"entry_date":day}
            if tail_qty: counts["tail_contracts_opened_n"]+=tail_qty

        mv=0.0; missing=[]; exp=avail=0; sizeok=True; openbase=0
        for p in pos.values():
            v,en,av,miss,sz=mark_position(p,day,book)
            exp+=en; avail+=av; missing.extend(miss); sizeok=sizeok and sz
            if v is not None: mv+=v
            openbase+=int(p["base_open"])
        held=account_collateral(pos)
        navval=None if missing else cash+mv
        curve.append({"account_id":account_id,"arm":ARM,"phase":phase,"ratio":ratio,"short_spy_qty":sqty,
            "tail_qty":tail_qty,"date":day,"cash_usd":round(cash,2),"reserved_defined_risk_usd":round(held,2),
            "free_cash_after_reserve_usd":round(cash-held,2),"open_base_positions_n":openbase,
            "open_tail_contracts_n":sum(p["tail_qty"] for p in pos.values() if p["base_open"]),
            "quote_legs_expected_n":exp,"quote_legs_available_n":avail,
            "quote_coverage_pct":round(100*avail/exp,4) if exp else 100.,
            "full_size_liquidation_quote_available":bool(not missing and sizeok),
            "nav_usd":round(navval,2) if navval is not None else None,
            "nav_missing_contracts":";".join(missing[:10])})
        counts["peak_reserved_defined_risk_usd"]=max(counts["peak_reserved_defined_risk_usd"],held)
        counts["peak_open_positions_n"]=max(counts["peak_open_positions_n"],openbase)

    valid=[r for r in curve if r["nav_usd"] is not None]
    allnav=[float(r["nav_usd"]) for r in valid]
    last=next((r for r in reversed(curve) if r["date"]==end),None)
    endnav=num(last.get("nav_usd")) if last else None
    navcov=100*len(valid)/len(curve) if curve else 0.0
    dd=navlib.maxdd(allnav)
    grow=navlib.cagr(START_NAV,endnav,startday,end) if endnav is not None else None
    summary={"account_id":account_id,"arm":ARM,"phase":phase,"ratio":ratio,"short_spy_qty":sqty,"tail_qty":tail_qty,
        "config_name":cfg["name"],"policy":POLICY,"starting_nav_usd":START_NAV,"account_start_date":startday,"data_end_date":end,
        "ending_nav_usd":round(endnav,2) if endnav is not None else None,"ending_nav_available":endnav is not None,
        "total_profit_usd":round(endnav-START_NAV,2) if endnav is not None else None,
        "total_return_pct":round((endnav/START_NAV-1)*100,6) if endnav is not None else None,
        "cagr_pct":round(grow,6) if grow is not None else None,"max_drawdown_observed_pct":round(dd,6) if dd is not None else None,
        "nav_observations_n":len(valid),"market_sessions_n":len(curve),"nav_coverage_pct":round(navcov,4),
        "base_entry_attempts_n":counts["base_entry_attempts_n"],"base_trades_opened_n":counts["base_trades_opened_n"],
        "base_entries_skipped_capital_n":counts["capital_rejected_n"],"base_entries_rejected_quote_n":counts["quote_rejected_n"],
        "tail_entries_rejected_quote_n":counts["tail_quote_rejected_n"],"base_exits_closed_n":counts["base_exit_closed_n"],
        "expiry_settlements_n":counts["expiry_settlements_n"],"tail_contracts_opened_n":counts["tail_contracts_opened_n"],
        "realized_pnl_usd":round(counts["realized_pnl_usd"],2),"tail_realized_pnl_usd":round(counts["tail_realized_pnl_usd"],2),
        "pnl_reconciliation_mismatch_n":mismatches,"peak_reserved_defined_risk_usd":round(counts["peak_reserved_defined_risk_usd"],2),
        "peak_open_positions_n":counts["peak_open_positions_n"],
        "quote_leg_coverage_pct":round(100*sum(int(r["quote_legs_available_n"]) for r in curve)/
           max(1,sum(int(r["quote_legs_expected_n"]) for r in curve)),4),
        "nav_end_status":"QUOTED_MTM_AT_DATA_END" if endnav is not None else "ENDING_NAV_UNAVAILABLE"}
    annual=annual_rows(account_id,curve,START_NAV,startday,end,ratio,tail_qty)
    return summary,curve,annual,gates,trade_results

def annual_rows(account,curve,start_nav,start_date,end_date,ratio,tail_qty):
    grouped=defaultdict(list)
    years=sorted({int(r["date"][:4]) for r in curve})
    for r in curve:
        if r["nav_usd"] is not None: grouped[int(r["date"][:4])].append(r)
    prev_nav=prev_year=None; out=[]
    for year in years:
        allrows=[r for r in curve if int(r["date"][:4])==year]
        val=grouped.get(year,[])
        ld=max((r["date"] for r in allrows),default=None)
        last=max(val,key=lambda x:x["date"]) if val else None
        gap=(date.fromisoformat(ld)-date.fromisoformat(last["date"])).days if last and ld else None
        complete=bool(last and gap is not None and gap<=5)
        endnav=float(last["nav_usd"]) if complete else None
        if year==int(start_date[:4]): sv,sd,kind=start_nav,start_date,"PARTIAL_FROM_INCEPTION"
        elif prev_nav is not None and prev_year==year-1: sv,sd,kind=prev_nav,str(year-1)+"-12-31","CALENDAR_YEAR"
        else: sv,sd,kind=None,None,"PREVIOUS_ENDPOINT_UNAVAILABLE"
        if year==int(end_date[:4]) and end_date<str(year)+"-12-31": kind="PARTIAL_TO_DATA_END_"+end_date
        profit=endnav-sv if endnav is not None and sv is not None else None
        ret=(endnav/sv-1)*100 if endnav is not None and sv is not None and sv>0 else None
        out.append({"account_id":account,"arm":ARM,"ratio":ratio,"short_spy_qty":ratio.split(":")[-1],
            "tail_qty":tail_qty,"year":year,"period_kind":kind,"period_start_date":sd,
            "period_start_nav_usd":round(sv,2) if sv is not None else None,
            "period_end_date":last["date"] if complete else None,"period_end_nav_usd":round(endnav,2) if endnav is not None else None,
            "period_profit_usd":round(profit,2) if profit is not None else None,
            "period_return_pct":round(ret,6) if ret is not None else None,"last_calendar_observation_date":ld,
            "days_from_last_complete_mark_to_data_date":gap,"complete_nav_observations":len(val),
            "total_market_sessions":len(allrows),"endpoint_complete":complete})
        if endnav is not None: prev_nav,prev_year=endnav,year
        else: prev_nav,prev_year=None,None
    return out

def aggregate_summaries(rows):
    groups=defaultdict(list)
    for r in rows: groups[(r["ratio"],r["short_spy_qty"],r["tail_qty"])].append(r)
    out=[]
    for (ratio,sqty,tqty),g in sorted(groups.items()):
        def vals(k): return [float(x[k]) for x in g if x.get(k) is not None and math.isfinite(float(x[k]))]
        def med(k): return round(statistics.median(vals(k)),6) if vals(k) else None
        def bounds(k):
            v=vals(k)
            return (round(min(v),6),round(max(v),6),len(v)) if v else (None,None,0)
        rlo,rhi,rn=bounds("total_return_pct"); clo,chi,cn=bounds("cagr_pct"); dlo,dhi,dn=bounds("max_drawdown_observed_pct")
        out.append({"arm":ARM,"ratio":ratio,"short_spy_qty":sqty,"tail_qty":tqty,"phase_accounts_n":len(g),
            "ending_nav_available_n":sum(bool(x["ending_nav_available"]) for x in g),
            "median_ending_nav_usd":med("ending_nav_usd"),"median_total_profit_usd":med("total_profit_usd"),
            "median_total_return_pct":med("total_return_pct"),"return_min_pct":rlo,"return_max_pct":rhi,
            "return_available_phases_n":rn,"median_cagr_pct":med("cagr_pct"),"cagr_min_pct":clo,"cagr_max_pct":chi,
            "cagr_available_phases_n":cn,"median_max_drawdown_observed_pct":med("max_drawdown_observed_pct"),
            "maxdd_min_pct":dlo,"maxdd_max_pct":dhi,"maxdd_available_phases_n":dn,
            "median_nav_coverage_pct":med("nav_coverage_pct"),
            "median_base_trades_opened_n":med("base_trades_opened_n"),
            "median_entries_skipped_capital_n":med("base_entries_skipped_capital_n"),
            "median_entries_rejected_quote_n":med("base_entries_rejected_quote_n"),
            "median_peak_reserved_defined_risk_usd":med("peak_reserved_defined_risk_usd"),
            "median_peak_open_positions_n":med("peak_open_positions_n")})
    return out

def annual_medians(rows):
    groups=defaultdict(list)
    for r in rows: groups[(r["ratio"],r["short_spy_qty"],r["tail_qty"],r["year"])].append(r)
    out=[]
    for (ratio,sqty,tqty,year),g in sorted(groups.items()):
        p=[float(r["period_profit_usd"]) for r in g if r.get("period_profit_usd") is not None]
        v=[float(r["period_return_pct"]) for r in g if r.get("period_return_pct") is not None]
        kinds={str(r.get("period_kind","")) for r in g}
        kind=("PARTIAL_FROM_INCEPTION" if any(x.startswith("PARTIAL_FROM_INCEPTION") for x in kinds)
              else next((x for x in kinds if x.startswith("PARTIAL_TO_DATA_END")), "CALENDAR_YEAR"))
        out.append({"arm":ARM,"ratio":ratio,"short_spy_qty":sqty,"tail_qty":tqty,"year":year,"period_kind":kind,
            "phase_accounts_n":len(g),"valid_phase_profit_n":len(p),"median_period_profit_usd":round(statistics.median(p),2) if p else None,
            "min_period_profit_usd":round(min(p),2) if p else None,"max_period_profit_usd":round(max(p),2) if p else None,
            "median_period_return_pct":round(statistics.median(v),6) if v else None,
            "valid_phase_return_n":len(v),"min_period_return_pct":round(min(v),6) if v else None,
            "max_period_return_pct":round(max(v),6) if v else None})
    return out

def report_text(aggs,years):
    money=lambda x:"—" if x is None else f"{chr(36)}{float(x):,.0f}"
    pct=lambda x:"—" if x is None else f"{float(x):.2f}%"
    lines=["# DTE14 QQQ:SPY Put Ratios — $100,000 Single-Account NAV with FAR TAIL Collateral","",
      "Research-only historical replay. No broker orders. Five phase schedules overlap; report their medians/ranges, never add the phases together.","",
      "## Frozen strategy and collateral model","",
      "- DTE14 base selection and fixed exit policy: HOLD_20_OR_DTE_LE_7, inherited from the source-pinned QQQ long PUT / SPY short PUT replay.",
      "- Start NAV is exactly $100,000 for every phase. Each account replays a fixed QQQ long PUT 1 contract and SPY short PUT quantity of 3 or 6; lot size is not automatically scaled with NAV.",
      "- FAR TAIL is the source-pinned same-entry-date, same-expiry SPY TAIL_10_DELTA long PUT. It is purchased at the ask at the same entry event, not assumed to appear later as collateral.",
      "- Comparisons: 1:3 with 0 or 3 tails; 1:6 with 0, 3 or 6 tails. The full-coverage variants pair each SPY short PUT with one lower-strike same-expiry SPY long PUT. The 1:6 / 3-tail variant leaves three SPY shorts uncovered.",
      "- Reserve proxy = (short strike − tail strike) × 100 × paired spreads + short strike × 100 × uncovered short puts. Tail strikes must be strictly below the SPY short strike. Reserve is a conservative defined-risk collateral proxy, not a broker margin quote.",
      "- A QQQ long PUT does not collateralize SPY short PUTs. Only same-underlying, same-expiry, lower-strike SPY puts count as vertical-spread coverage. One tail contract only covers one short put; unmatched shorts retain full strike-notional reserve.",
      "- Entry and exit use exact contract Bid/Ask sides and displayed-size gates. Costs are $0.05 per option-share per side plus $0.65 per contract per side. Daily EOD quotes are not verified fills.",
      "- If any leg of the vertical package cannot pass the exit quote/size gate on the scheduled exit day, none of the package legs is separately closed. Remaining positions are marked to intrinsic at expiry when underlying closes are available; this is an assignment/liquidation proxy.",
      "",
      "## Account-level results (median across five phase accounts)","",
      "| Ratio | SPY short qty | FAR TAIL qty | Median end NAV | Median cumulative profit | Total return | CAGR | Observed MaxDD | Peak reserve | Median entries opened | Median capital rejections | NAV coverage |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in aggs:
        lines.append(f"| {r['ratio']} | {r['short_spy_qty']} | {r['tail_qty']} | {money(r['median_ending_nav_usd'])} | {money(r['median_total_profit_usd'])} | {pct(r['median_total_return_pct'])} | {pct(r['median_cagr_pct'])} | {pct(r['median_max_drawdown_observed_pct'])} | {money(r['median_peak_reserved_defined_risk_usd'])} | {r['median_base_trades_opened_n']} | {r['median_entries_skipped_capital_n']} | {pct(r['median_nav_coverage_pct'])} |")
    lines += ["","## Calendar-year account profit","",
      "A full calendar-year result is only reported when a complete year-end NAV mark exists. 2018 begins at account inception; 2025 ends at 2025-12-12. Previous incomplete year-end marks are not forward-filled.","",
      "| Ratio | Tail qty | Year | Period | Median account P&L | Min–max across phases | Median return | Valid phases |",
      "|---|---:|---:|---|---:|---:|---:|---:|"]
    for r in years:
        lo,hi=r.get("min_period_profit_usd"),r.get("max_period_profit_usd")
        range_text="—" if lo is None or hi is None else f"{money(lo)} to {money(hi)}"
        lines.append(f"| {r['ratio']} | {r['tail_qty']} | {r['year']} | {r['period_kind']} | {money(r['median_period_profit_usd'])} | {range_text} | {pct(r['median_period_return_pct'])} | {r['valid_phase_profit_n']}/{r['phase_accounts_n']} |")
    lines += ["","## Interpretation and limitations","",
      "- The principal decision metric is median annual account profit on the single $100k NAV path, not total P&L summed over overlapping trade episodes.",
      "- Tail PUT premiums reduce account NAV. Lower reserved collateral does not mean the hedge is free or the package is low-risk; compare premium drag with both worst trade and portfolio MaxDD.",
      "- MaxDD is computed from available daily NAV marks; gaps with missing quotes can understate risk. EOD prices and displayed sizes do not establish real fills.",
      "- A vertical-spread reserve calculated from strike width is not an exact broker initial/maintenance margin calculation. Actual brokers can add house requirements, fees, assignment/exercise cash needs, and liquidity buffers.",
      "- No margin borrowing, interest, taxes, dividends, early assignment fees, forced-liquidation engine, or verified fills is modeled. Source option chains end on 2025-12-12.",
      "- Five phase schedules overlap and are not independent samples or confidence intervals. No phases are pooled or summed.",
      "",
      "Supporting outputs: account_phase_summary.csv, account_summary_by_config.csv, account_annual_returns.csv, account_annual_median.csv, account_nav_daily.csv, capital_gates.csv, trade_results.csv and account_manifest.json."]
    return "\n".join(lines)

def run(args):
    global OUT
    OUT=args.out.expanduser().resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    cache=args.cache.expanduser().resolve(); cache.mkdir(parents=True,exist_ok=True)
    base,tails,input_hashes,om,selection_path,book,dates,qspots,spots,pins,stats,ids,first,end=run_load(cache)
    grouped=defaultdict(list)
    for r in base.values(): grouped[int(r["phase"])].append(r)
    if set(grouped)!=set(PHASES): raise ValueError("Expected all five DTE14 phase ledgers")
    summaries=[]; annual=[]; curves=[]; gates=[]; trade_rows=[]
    for phase in PHASES:
        trades=sorted(grouped[phase],key=lambda r:(str(r["entry_date"]),str(r.get("episode_id",""))))
        for cfg in CONFIGS:
            s,curve,years,blocked,done=simulate(phase,cfg,trades,tails,book,dates,qspots,spots,end)
            summaries.append(s); annual.extend(years); gates.extend(blocked); trade_rows.extend(done); curves.extend(curve)
    aggs=aggregate_summaries(summaries); yagg=annual_medians(annual)
    manifest={"schema":"dte14-ratio-spread-single-account-nav.v1","status":"COMPLETED","policy":POLICY,
        "starting_nav_usd":START_NAV,"base_arm":ARM,"base_trade_rows":len(base),
        "source_input_ledger_sha256":input_hashes,"source_input_hashes_match_overlay_manifest":input_hashes==om.get("input_ledger_sha256"),
        "overlay_manifest_sha256":digest(RES/"spy_far_tail_hedge_v1"/"manifest.json"),
        "tail_selection_sha256":digest(selection_path),"code_sha256":digest(Path(__file__)),
        "source_repository":om.get("source_repository"),"source_tree_commit":om.get("source_tree_commit"),
        "source_pin_count":len(pins),"source_pins":pins,"chain_first_date":first,"chain_end_date":end,
        "stream_stats":stats,"tracked_contract_count":{k:len(v) for k,v in ids.items()},
        "account_configurations":len(summaries),"annual_rows":len(annual),"daily_nav_rows":len(curves),
        "capital_gate_events":len(gates),"trade_result_rows":len(trade_rows),"phase_results_pooled_or_summed":False,
        "costs":{"slippage_per_option_share_per_side_usd":0.05,"commission_per_contract_per_side_usd":0.65},
        "ratio_and_tail_configs":[dict(x) for x in CONFIGS],
        "collateral_model":"same-expiry same-underlying SPY vertical spread; reserve full strike width x paired quantity; uncovered short puts reserve full strike notional",
        "warnings":["EOD quotes are proxies, not verified fills.","Displayed size is an eligibility screen, not guaranteed execution.",
          "A quote/size failure on exit keeps the entire spread package open until its intrinsic expiry settlement proxy; no later substitute exit.",
          "Cash reserve is not a broker margin simulation; no margin offsets across QQQ and SPY.",
          "Observed MaxDD may understate risk around missing-quote gaps.","Five anchor phases overlap and are not independent.",
          "Lot count is fixed and not scaled as NAV changes.","No 2026 option-chain performance; source ends 2025-12-12."]}
    writecsv(OUT/"account_phase_summary.csv",summaries)
    writecsv(OUT/"account_summary_by_config.csv",aggs)
    writecsv(OUT/"account_annual_returns.csv",annual)
    writecsv(OUT/"account_annual_median.csv",yagg)
    writecsv(OUT/"account_nav_daily.csv",sorted(curves,key=lambda r:(r["phase"],r["ratio"],r["tail_qty"],r["date"])))
    writecsv(OUT/"trade_results.csv",trade_rows)
    if not gates: gates=[{"account_id":"","date":"","event":"","trade_key":"","decision":"NO_REJECTIONS","reason":"No capital or quote rejections"}]
    writecsv(OUT/"capital_gates.csv",gates)
    (OUT/"DTE14_RATIO_SPREAD_NAV_REPORT.md").write_text(report_text(aggs,yagg),encoding="utf-8")
    required=("account_phase_summary.csv","account_summary_by_config.csv","account_annual_returns.csv","account_annual_median.csv",
              "account_nav_daily.csv","trade_results.csv","capital_gates.csv","DTE14_RATIO_SPREAD_NAV_REPORT.md")
    manifest["output_sha256"]={p.name:digest(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="account_manifest.json"}
    manifest["required_outputs_nonempty"]=all((OUT/f).is_file() and (OUT/f).stat().st_size>0 for f in required)
    manifest["pnl_reconciliation_mismatch_n"]=sum(int(x.get("pnl_reconciliation_mismatch_n",0)) for x in summaries)
    if len(summaries)!=25 or len(pins)!=18 or not manifest["required_outputs_nonempty"]:
        raise RuntimeError("Count/source/output gate failed")
    (OUT/"account_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":manifest["status"],"phase_accounts":len(summaries),"base_trade_rows":len(base),
       "source_pins":len(pins),"daily_nav_rows":len(curves),"capital_gate_events":len(gates),
       "output_dir":str(OUT)},sort_keys=True))
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache",type=Path,default=Path.home()/".cache"/"spy-options-dte14-ratio-nav-v1")
    p.add_argument("--out",type=Path,default=OUT)
    m=run(p.parse_args())
    if m.get("status")!="COMPLETED" or not m.get("required_outputs_nonempty"):
        raise RuntimeError("DTE14 ratio NAV replay output gate failed")
if __name__=="__main__": main()
