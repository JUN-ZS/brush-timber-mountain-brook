#!/usr/bin/env python3
"""Source-pinned cash-secured account NAV replay for a fixed QQQ long-put / SPY short-put strategy."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
import qqq_spy_put_fixed_phase_v1 as eng
import spy_far_tail_hedge_v1 as hedge
import run_spy_far_tail_holding_trigger_v1 as trigger
import run_spy_far_tail_conditional_v1 as conditional

ROOT=Path(__file__).resolve().parent
RES=ROOT/"results"
OUT=RES/"spy_far_tail_account_nav_v1"
POLICY="HOLD_20_OR_DTE_LE_7"
RULE="ANY_OF_THREE_PREDECLARED"
TAIL="TAIL_10_DELTA"
ARMS=("DTE45","DTE14")
PHASES=range(5)
STARTS=(100000.0,250000.0,500000.0,1000000.0)
HEDGES=(0,1,3)
M=100
EPS=1e-6

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def readj(p):
    x=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise ValueError("Expected JSON object: "+str(p))
    return x

def num(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except (TypeError,ValueError): return None

def yes(x): return str(x).strip().lower() in ("true","1","yes")

def epnorm(x):
    s="" if x is None else str(x).strip()
    try:
        y=float(s)
        if math.isfinite(y) and y.is_integer(): return str(int(y))
    except (TypeError,ValueError): pass
    return s

def key(r):
    return str(r.get("arm","")),int(r.get("phase",0)),epnorm(r.get("episode_id")),str(r.get("policy",""))

def unit(slip,comm): return slip*M+comm

def pnl_base(p,qbid,sask):
    l,s=int(p["lqty"]),int(p["sqty"])
    u=unit(p["slip"],p["comm"])
    return l*M*(qbid-p["qask"])+s*M*(p["sbid"]-sask)-2*u*(l+s)

def pnl_tail(qty,ask,bid,slip,comm):
    return qty*M*(bid-ask)-2*unit(slip,comm)*qty

def put_intrinsic(strike,spot,qty):
    return max(float(strike)-float(spot),0.0)*M*int(qty)

def allow_base(cash,delta,held,needed): return cash+delta+EPS>=held+needed
def allow_tail(cash,debit,held): return cash-debit+EPS>=held

def maxdd(xs):
    if not xs: return None
    peak=xs[0]; result=0.0
    for x in xs:
        peak=max(peak,x)
        if peak>0: result=max(result,(peak-x)/peak*100)
    return result

def cagr(start,end,d0,d1):
    if start<=0 or end<=0 or d0>=d1: return None
    days=(date.fromisoformat(d1)-date.fromisoformat(d0)).days
    return ((end/start)**(365.25/days)-1)*100 if days>0 else None

def writecsv(path,rows):
    if not rows: raise ValueError("Refusing empty output "+str(path))
    fields=[]; seen=set()
    for r in rows:
        for k in r:
            if k not in seen: fields.append(k);seen.add(k)
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)

def quote_row(raw,sym,day):
    return {"date":day,"bid":num(raw.get("bid")),"ask":num(raw.get("ask")),
      "bid_size":eng.displayed_size(raw,"bid"),"ask_size":eng.displayed_size(raw,"ask"),
      "valid":eng.valid_quote(raw),"identity":eng.standard_put_identity(raw,sym),
      "strike":num(raw.get("strike")),"expiration":str(raw.get("expiration") or raw.get("expiry") or "")}

def quote_at(book,day,sym,contract):
    ident=eng.normalized_contract_id({"contract_id":contract})
    q=book.get(day,{}).get(sym,{}).get(ident)
    if not q or q["date"]!=day or not q["valid"] or not q["identity"] or q["bid"] is None or q["ask"] is None: return None
    return q

def load_ledgers():
    omp=RES/"spy_far_tail_hedge_v1"/"manifest.json"
    hdir=RES/"spy_far_tail_holding_trigger_v2"
    hmp=hdir/"holding_manifest.json"; tp=hdir/"holding_trade_level.csv"
    for p in (omp,hmp,tp):
        if not p.is_file() or p.stat().st_size==0: raise FileNotFoundError("Missing frozen replay input: "+str(p))
    om,hm=readj(omp),readj(hmp)
    if om.get("status")!="COMPLETED" or hm.get("status")!="COMPLETED": raise ValueError("Frozen upstream replay not completed")
    if hm.get("baseline_input_hashes_match_overlay_manifest") is not True: raise ValueError("Upstream SHA reconciliation failed")
    _,raw,hashes=hedge.load_base_ledgers(RES)
    conditional.validate_baseline_hashes(hashes,om.get("input_ledger_sha256"))
    if hashes!=hm.get("baseline_input_sha256"): raise ValueError("Holding trigger input SHA map differs from frozen ledger")
    base={}
    for r in raw.values():
        if r.get("policy")!=POLICY: continue
        k=key(r)
        if k in base: raise ValueError("Duplicate base key "+str(k))
        base[k]=r
    ov={}
    with tp.open("r",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("policy")!=POLICY or r.get("trigger_rule")!=RULE or r.get("tail_label")!=TAIL: continue
            if str(r.get("tail_quantity")) not in ("1","3"): continue
            k=(*key(r),int(r["tail_quantity"]))
            if k in ov: raise ValueError("Duplicate trigger key "+str(k))
            ov[k]=r
    expected={(*k,q) for k in base for q in (1,3)}
    if expected-set(ov): raise ValueError("Missing locked trigger outputs: "+str(len(expected-set(ov))))
    return base,ov,hashes,om,hm,tp

def load_market(base,ov,hm,cache):
    ids={"QQQ":set(),"SPY":set()}
    for r in base.values():
        for sym,field in (("QQQ","qqq_contract_id"),("SPY","spy_contract_id")):
            x=eng.normalized_contract_id({"contract_id":r.get(field)})
            if x: ids[sym].add(x)
    for r in ov.values():
        x=eng.normalized_contract_id({"contract_id":r.get("tail_contract_id")})
        if x: ids["SPY"].add(x)
    first=min(str(r["entry_date"]) for r in base.values()); end=str(hm["chain_last_date"])
    qp,sp,pins=[],[],[]
    for y in range(int(first[:4]),int(end[:4])+1):
        p,z=eng.download_verified("QQQ",y,cache/"qqq-options");qp.append(p);pins.append(z)
        p,z=eng.download_verified("SPY",y,cache/"spy-options");sp.append(p);pins.append(z)
    q_under,z=eng.download_verified("QQQ",None,cache/"qqq-underlying");pins.append(z)
    s_under,z=eng.download_verified("SPY",None,cache/"spy-underlying");pins.append(z)
    qspots,spots=eng.load_spots(q_under,"QQQ"),eng.load_spots(s_under,"SPY")
    dates=sorted(d for d in spots if d<=end)
    u_days=[d for d in dates if first<=d<=end]
    stats={"qqq":{"chain_dates":0,"put_rows":0,"first_chain_date":None,"last_chain_date":None},
      "spy":{"chain_dates":0,"put_rows":0,"first_chain_date":None,"last_chain_date":None},
      "merged_dates":0,"entry_day_missing_from_option_stream_n":0,"underlying_only_observation_days":0}
    book={}
    for day,qr,sr in trigger.iter_merged_symbol_days(qp,sp,first,end,stats,u_days):
        d={"QQQ":{},"SPY":{}}
        for sym,rows in (("QQQ",qr),("SPY",sr)):
            for r in rows:
                x=eng.normalized_contract_id(r)
                if x and x in ids[sym]: d[sym][x]=quote_row(r,sym,day)
        book[day]=d
    if len(pins)!=18: raise ValueError("Expected 18 byte-pinned source files, got "+str(len(pins)))
    return book,dates,qspots,spots,pins,stats,ids,first,end

def collateral(pos):
    return sum(p["strike"]*M*p["sqty"] for p in pos.values() if p["base_open"])

def mark_pos(p,day,book):
    value=0.0; exp=avail=0; missing=[]; sizeok=True; u=unit(p["slip"],p["comm"])
    if p["base_open"]:
        q=quote_at(book,day,"QQQ",p["qid"]);s=quote_at(book,day,"SPY",p["sid"]);exp+=2
        for x,label,qty,side in ((q,"QQQ:"+p["qid"],p["lqty"],"bid"),(s,"SPY:"+p["sid"],p["sqty"],"ask")):
            if x is None: missing.append(label)
            else:
                avail+=1
                if x[side+"_size"]<qty:sizeok=False
        if q is not None and s is not None:value+=q["bid"]*M*p["lqty"]-s["ask"]*M*p["sqty"]-u*(p["lqty"]+p["sqty"])
    if p["tail_open"]:
        t=quote_at(book,day,"SPY",p["tid"]);exp+=1
        if t is None:missing.append("SPY_TAIL:"+p["tid"])
        else:
            avail+=1
            if t["bid_size"]<p["hqty"]:sizeok=False
            value+=t["bid"]*M*p["hqty"]-u*p["hqty"]
    return (None if missing else value),exp,avail,missing,sizeok

def annual_rows(account,curve,start_nav,start_date,end_date,arm,phase,hqty):
    grouped=defaultdict(list)
    years=sorted({int(r["date"][:4]) for r in curve})
    for r in curve:
        if r["nav_usd"] is not None:grouped[int(r["date"][:4])].append(r)
    prev_nav=prev_year=None; out=[]
    for year in years:
        allrows=[r for r in curve if int(r["date"][:4])==year]; val=grouped.get(year,[])
        ld=max((r["date"] for r in allrows),default=None); last=max(val,key=lambda x:x["date"]) if val else None
        gap=(date.fromisoformat(ld)-date.fromisoformat(last["date"])).days if last and ld else None
        complete=bool(last and gap is not None and gap<=5)
        end=float(last["nav_usd"]) if complete else None
        if year==int(start_date[:4]):sv,sd,kind=start_nav,start_date,"PARTIAL_FROM_INCEPTION"
        elif prev_nav is not None and prev_year==year-1:sv,sd,kind=prev_nav,str(year-1)+"-12-31","CALENDAR_YEAR"
        else:sv,sd,kind=None,None,"PREVIOUS_ENDPOINT_UNAVAILABLE"
        if year==int(end_date[:4]) and end_date<str(year)+"-12-31":kind="PARTIAL_TO_DATA_END_"+end_date
        profit=end-sv if end is not None and sv is not None else None
        ret=(end/sv-1)*100 if end is not None and sv is not None and sv>0 else None
        out.append({"account_id":account,"arm":arm,"phase":phase,"starting_nav_usd":start_nav,"hedge_qty":hqty,"year":year,
          "period_kind":kind,"period_start_date":sd,"period_start_nav_usd":round(sv,2) if sv is not None else None,
          "period_end_date":last["date"] if complete else None,"period_end_nav_usd":round(end,2) if end is not None else None,
          "period_profit_usd":round(profit,2) if profit is not None else None,"period_return_pct":round(ret,6) if ret is not None else None,
          "last_calendar_observation_date":ld,"days_from_last_complete_mark_to_data_date":gap,
          "complete_nav_observations":len(val),"total_market_sessions":len(allrows),"endpoint_complete":complete})
        if end is not None:prev_nav,prev_year=end,year
        else:prev_nav,prev_year=None,None
    return out

def simulate(arm,phase,start,hqty,trades,ov,book,qspots,spots,market_dates,end):
    first=min(str(r["entry_date"]) for r in trades);idx=market_dates.index(first)
    startday=market_dates[max(idx-1,0)];dates=[d for d in market_dates if startday<=d<=end]
    acct=f"{arm}|phase_{phase}|NAV_{int(start)}|HEDGE_{hqty}"
    cash=float(start);pos={}; entries=defaultdict(list)
    for r in trades:
        x=dict(r);x["trade_key"]="|".join(map(str,key(r)));entries[str(r["entry_date"])].append(x)
    gate=[];curve=[];c=defaultdict(int);mismatches=0
    for day in dates:
        # Fixed exit date only. Missing quotes do not trigger a later substitute exit.
        for k,p in list(pos.items()):
            if p["base_open"] and p["exit_date"]==day and not p["exit_attempted"]:
                p["exit_attempted"]=True;q=quote_at(book,day,"QQQ",p["qid"]);s=quote_at(book,day,"SPY",p["sid"])
                if q and s and q["bid_size"]>=p["lqty"] and s["ask_size"]>=p["sqty"]:
                    u=unit(p["slip"],p["comm"]);cash+=q["bid"]*M*p["lqty"]-u*p["lqty"];cash-=s["ask"]*M*p["sqty"]+u*p["sqty"]
                    pnl=p["lqty"]*M*(q["bid"]-p["qask"])+p["sqty"]*M*(p["sbid"]-s["ask"])-2*u*(p["lqty"]+p["sqty"])
                    c["base_exit_closed_n"]+=1;c["base_realized_pnl_usd"]+=pnl
                    if p["source_pnl"] is not None and abs(p["source_pnl"]-pnl)>.03:mismatches+=1
                    p["base_open"]=False
                else:p["base_exit_failed"]=True;c["base_exit_failed_n"]+=1
            if p["tail_open"] and p["exit_date"]==day and not p["tail_exit_attempted"]:
                p["tail_exit_attempted"]=True;t=quote_at(book,day,"SPY",p["tid"])
                if t and t["bid_size"]>=p["hqty"]:
                    u=unit(p["slip"],p["comm"]);cash+=t["bid"]*M*p["hqty"]-u*p["hqty"]
                    c["tail_exit_closed_n"]+=1;c["tail_realized_pnl_usd"]+=pnl_tail(p["hqty"],p["hask"],t["bid"],p["slip"],p["comm"])
                    p["tail_open"]=False
                else:p["tail_exit_failed"]=True;c["tail_exit_failed_n"]+=1
            # If an unresolved contract reaches expiry without an executable close, use contractual put intrinsic at the underlying close.
            # This is an exercise plus immediate same-close stock liquidation proxy, not a claimed option fill.
            if p["base_open"] and p["expiry"]==day:
                qspot,sspot=num(qspots.get(day)),num(spots.get(day))
                if qspot is not None and sspot is not None:
                    qpay=put_intrinsic(p["qstrike"],qspot,p["lqty"])
                    spay=put_intrinsic(p["strike"],sspot,p["sqty"])
                    cash+=qpay-spay
                    u=unit(p["slip"],p["comm"])
                    entry_cf=-p["qask"]*M*p["lqty"]-u*p["lqty"]+p["sbid"]*M*p["sqty"]-u*p["sqty"]
                    c["base_expiry_settlements_n"]+=1
                    c["base_realized_pnl_usd"]+=qpay-spay+entry_cf
                    p["base_open"]=False
            if p["tail_open"] and p["expiry"]==day:
                sspot=num(spots.get(day)); hstrike=num(p["hstrike"])
                if sspot is not None and hstrike is not None:
                    payoff=put_intrinsic(hstrike,sspot,p["hqty"])
                    cash+=payoff
                    c["tail_expiry_settlements_n"]+=1
                    c["tail_realized_pnl_usd"]+=payoff-p["hask"]*M*p["hqty"]-unit(p["slip"],p["comm"])*p["hqty"]
                    p["tail_open"]=False
            if not p["base_open"] and not p["tail_open"]:pos.pop(k,None)
        # Replay original entries in source order; skip if cash cannot secure all overlapping SPY shorts.
        for r in entries.get(day,[]):
            c["base_entry_attempts_n"]+=1
            q=quote_at(book,day,"QQQ",r["qqq_contract_id"]);s=quote_at(book,day,"SPY",r["spy_contract_id"])
            if not q or not s:
                c["base_entries_rejected_quote_gate_n"]+=1;gate.append({"account_id":acct,"date":day,"event":"BASE_ENTRY","trade_key":r["trade_key"],"decision":"REJECT_QUOTE","reason":"EXACT_ENTRY_CONTRACT_MISSING"});continue
            lqty,sqty=int(float(r["long_qqq_qty"])),int(float(r["short_spy_qty"]))
            if q["ask_size"]<lqty or s["bid_size"]<sqty:
                c["base_entries_rejected_quote_gate_n"]+=1;gate.append({"account_id":acct,"date":day,"event":"BASE_ENTRY","trade_key":r["trade_key"],"decision":"REJECT_QUOTE","reason":"INSUFFICIENT_ENTRY_SIZE"});continue
            if abs(q["ask"]-float(r["qqq_entry_ask"]))>.0001 or abs(s["bid"]-float(r["spy_entry_bid"]))>.0001:raise ValueError("Entry quote mismatch "+r["trade_key"])
            slip,comm=float(r["base_slippage_per_share"]),float(r["base_commission_per_contract_per_side"]);u=unit(slip,comm)
            delta=-q["ask"]*M*lqty-u*lqty+s["bid"]*M*sqty-u*sqty;held=collateral(pos);needed=float(r["spy_strike"])*M*sqty
            if not allow_base(cash,delta,held,needed):
                c["base_entries_skipped_capital_n"]+=1;gate.append({"account_id":acct,"date":day,"event":"BASE_ENTRY","trade_key":r["trade_key"],"decision":"REJECT_CAPITAL","reason":"CASH_BELOW_CASH_SECURED_COLLATERAL","cash":round(cash,2),"cash_delta":round(delta,2),"held_collateral":round(held,2),"new_collateral":round(needed,2)});continue
            cash+=delta; c["base_trades_opened_n"]+=1
            tr=ov.get((*key(r),hqty)) if hqty in (1,3) else None; eligible=bool(tr and yes(tr.get("tail_entry_executable")))
            qid=eng.normalized_contract_id({"contract_id":r["qqq_contract_id"]});sid=eng.normalized_contract_id({"contract_id":r["spy_contract_id"]})
            tid=eng.normalized_contract_id({"contract_id":tr.get("tail_contract_id")}) if tr else ""
            resolved=str(r.get("status","")).upper()=="RESOLVED"; exitday=str(r.get("exit_date") or "") if resolved else ""
            pos[r["trade_key"]]={"base_open":True,"tail_open":False,"qid":qid,"sid":sid,"tid":tid,"lqty":lqty,"sqty":sqty,
              "strike":float(r["spy_strike"]),"qstrike":float(r["qqq_strike"]),"expiry":str(r.get("expiry") or ""),
              "hstrike":num(tr.get("tail_strike")) if tr else None,"qask":q["ask"],"sbid":s["bid"],"slip":slip,"comm":comm,
              "source_pnl":num(r.get("net_pnl_usd")),"exit_date":exitday,"exit_attempted":False,"base_exit_failed":False,
              "hqty":hqty,"tail_date":str(tr.get("tail_entry_date") or "") if eligible else "",
              "tailask_expected":num(tr.get("tail_entry_ask")) if tr else None,"tail_attempted":False,"hask":None,
              "tail_exit_attempted":False,"tail_exit_failed":False}
            if eligible:c["hedge_entry_opportunities_n"]+=1
        # Buy the preselected tail only on its exact next-session entry date and only if collateral remains intact.
        if hqty in (1,3):
            for k,p in list(pos.items()):
                if not p["base_open"] or p["tail_open"] or p["tail_attempted"] or p["tail_date"]!=day:continue
                p["tail_attempted"]=True;t=quote_at(book,day,"SPY",p["tid"]);expected=num(p["tailask_expected"])
                if not t or t["ask_size"]<hqty or expected is None or abs(t["ask"]-expected)>.0001:
                    c["hedge_entries_rejected_quote_n"]+=1;gate.append({"account_id":acct,"date":day,"event":"TAIL_ENTRY","trade_key":k,"decision":"REJECT_QUOTE","reason":"EXACT_NEXT_SESSION_QUOTE_MISMATCH"});continue
                debit=t["ask"]*M*hqty+unit(p["slip"],p["comm"])*hqty;held=collateral(pos)
                if not allow_tail(cash,debit,held):
                    c["hedge_entries_skipped_capital_n"]+=1;gate.append({"account_id":acct,"date":day,"event":"TAIL_ENTRY","trade_key":k,"decision":"REJECT_CAPITAL","reason":"WOULD_USE_RESERVED_COLLATERAL","debit":round(debit,2),"cash":round(cash,2),"held_collateral":round(held,2)});continue
                cash-=debit;p["tail_open"]=True;p["hask"]=t["ask"];c["hedge_trades_opened_n"]+=1
        mv=0.;missing=[];expected=available=0;sizeok=True;openb=opent=0;held=collateral(pos)
        for p in pos.values():
            v,en,av,miss,sz=mark_pos(p,day,book);expected+=en;available+=av;missing.extend(miss);sizeok=sizeok and sz
            if v is not None:mv+=v
            openb+=int(p["base_open"]);opent+=int(p["tail_open"])
        c["quote_legs_expected_n"]+=expected;c["quote_legs_available_n"]+=available
        if not missing and sizeok:c["size_executable_nav_days_n"]+=1
        nav=None if missing else cash+mv
        curve.append({"account_id":acct,"arm":arm,"phase":phase,"starting_nav_usd":start,"hedge_qty":hqty,"date":day,
          "cash_usd":round(cash,2),"reserved_spy_collateral_usd":round(held,2),"free_cash_after_collateral_usd":round(cash-held,2),
          "open_base_positions_n":openb,"open_tail_positions_n":opent,"quote_legs_expected_n":expected,"quote_legs_available_n":available,
          "quote_coverage_pct":round(100*available/expected,4) if expected else 100.,
          "full_size_liquidation_quote_available":bool(not missing and sizeok),"nav_usd":round(nav,2) if nav is not None else None,
          "nav_missing_contracts":";".join(missing[:10])})
        c["peak_collateral_usd"]=max(c["peak_collateral_usd"],held)
    vals=[float(r["nav_usd"]) for r in curve if r["nav_usd"] is not None];valid=[r for r in curve if r["nav_usd"] is not None]
    last=next((r for r in reversed(curve) if r["date"]==end),None); endnav=num(last.get("nav_usd")) if last else None
    cov=100*len(valid)/len(curve) if curve else 0.; dd=maxdd(vals); grow=cagr(start,endnav,startday,end) if endnav is not None else None
    s={"account_id":acct,"arm":arm,"phase":phase,"starting_nav_usd":start,"hedge_qty":hqty,"hedge_rule":"NO_HEDGE" if not hqty else "SPY_TAIL_10_DELTA_OR_TRIGGER",
      "base_policy":POLICY,"account_start_date":startday,"data_end_date":end,"ending_nav_usd":round(endnav,2) if endnav is not None else None,
      "ending_nav_available":endnav is not None,"latest_complete_nav_date":valid[-1]["date"] if valid else None,
      "total_profit_usd":round(endnav-start,2) if endnav is not None else None,
      "total_return_pct":round((endnav/start-1)*100,6) if endnav is not None else None,"cagr_pct":round(grow,6) if grow is not None else None,
      "max_drawdown_observed_pct":round(dd,6) if dd is not None else None,"nav_observations_n":len(valid),"market_sessions_n":len(curve),
      "nav_coverage_pct":round(cov,4),"base_entry_attempts_n":c["base_entry_attempts_n"],"base_trades_opened_n":c["base_trades_opened_n"],
      "base_entries_skipped_capital_n":c["base_entries_skipped_capital_n"],"base_entries_rejected_quote_n":c["base_entries_rejected_quote_gate_n"],
      "base_exits_closed_n":c["base_exit_closed_n"],"base_exits_failed_n":c["base_exit_failed_n"],
      "base_expiry_settlements_n":c["base_expiry_settlements_n"],"tail_expiry_settlements_n":c["tail_expiry_settlements_n"],
      "hedge_entry_opportunities_n":c["hedge_entry_opportunities_n"],"hedge_trades_opened_n":c["hedge_trades_opened_n"],
      "hedge_entries_skipped_capital_n":c["hedge_entries_skipped_capital_n"],"hedge_entries_rejected_quote_n":c["hedge_entries_rejected_quote_n"],
      "tail_exits_closed_n":c["tail_exit_closed_n"],"tail_exits_failed_n":c["tail_exit_failed_n"],
      "base_realized_pnl_usd":round(c["base_realized_pnl_usd"],2),"tail_realized_pnl_usd":round(c["tail_realized_pnl_usd"],2),
      "pnl_reconciliation_mismatch_n":mismatches,"open_base_positions_at_end_n":sum(bool(p["base_open"]) for p in pos.values()),
      "open_tail_positions_at_end_n":sum(bool(p["tail_open"]) for p in pos.values()),"peak_reserved_collateral_usd":round(c["peak_collateral_usd"],2),
      "quote_legs_expected_n":c["quote_legs_expected_n"],"quote_legs_available_n":c["quote_legs_available_n"],
      "quote_leg_coverage_pct":round(100*c["quote_legs_available_n"]/c["quote_legs_expected_n"],4) if c["quote_legs_expected_n"] else 100.,
      "size_executable_nav_days_n":c["size_executable_nav_days_n"],
      "nav_end_status":"QUOTED_MTM_AT_DATA_END" if endnav is not None else "ENDING_NAV_UNAVAILABLE"}
    return s,curve,annual_rows(acct,curve,start,startday,end,arm,phase,hqty),gate

def median_summary(rows):
    groups=defaultdict(list)
    for r in rows:groups[(r["arm"],r["starting_nav_usd"],r["hedge_qty"])].append(r)
    out=[]
    for (arm,nav,h),g in sorted(groups.items()):
        def vals(k):return [float(x[k]) for x in g if x.get(k) is not None and math.isfinite(float(x[k]))]
        def med(k):return round(statistics.median(vals(k)),6) if vals(k) else None
        def bounds(k):
            v=vals(k);return (round(min(v),6),round(max(v),6),len(v)) if v else (None,None,0)
        rlo,rhi,rn=bounds("total_return_pct");clo,chi,cn=bounds("cagr_pct");dlo,dhi,dn=bounds("max_drawdown_observed_pct")
        out.append({"arm":arm,"starting_nav_usd":nav,"hedge_qty":h,"phase_accounts_n":len(g),
          "ending_nav_available_n":sum(bool(x["ending_nav_available"]) for x in g),"median_ending_nav_usd":med("ending_nav_usd"),
          "median_total_profit_usd":med("total_profit_usd"),"median_total_return_pct":med("total_return_pct"),
          "return_min_pct":rlo,"return_max_pct":rhi,"return_available_phases_n":rn,"median_cagr_pct":med("cagr_pct"),
          "cagr_min_pct":clo,"cagr_max_pct":chi,"cagr_available_phases_n":cn,
          "median_max_drawdown_observed_pct":med("max_drawdown_observed_pct"),"maxdd_min_pct":dlo,"maxdd_max_pct":dhi,
          "maxdd_available_phases_n":dn,"median_nav_coverage_pct":med("nav_coverage_pct"),
          "median_base_trades_opened_n":med("base_trades_opened_n"),"median_base_entries_skipped_capital_n":med("base_entries_skipped_capital_n"),
          "median_hedge_trades_opened_n":med("hedge_trades_opened_n"),"median_hedge_entries_skipped_capital_n":med("hedge_entries_skipped_capital_n")})
    return out

def annual_medians(rows):
    groups=defaultdict(list)
    for r in rows:groups[(r["arm"],r["starting_nav_usd"],r["hedge_qty"],r["year"])].append(r)
    out=[]
    for (arm,nav,h,y),g in sorted(groups.items()):
        v=[float(r["period_return_pct"]) for r in g if r.get("period_return_pct") is not None]
        p=[float(r["period_profit_usd"]) for r in g if r.get("period_profit_usd") is not None]
        e=[float(r["period_end_nav_usd"]) for r in g if r.get("period_end_nav_usd") is not None]
        kinds={str(z.get("period_kind","")) for z in g}
        if any(k.startswith("PARTIAL_FROM_INCEPTION") for k in kinds): period_kind="PARTIAL_FROM_INCEPTION"
        elif any(k.startswith("PARTIAL_TO_DATA_END") for k in kinds): period_kind=next(k for k in kinds if k.startswith("PARTIAL_TO_DATA_END"))
        else: period_kind="CALENDAR_YEAR"
        out.append({"arm":arm,"starting_nav_usd":nav,"hedge_qty":h,"year":y,"period_kind":period_kind,
          "phase_accounts_n":len(g),"return_available_phases_n":len(v),
          "median_period_profit_usd":round(statistics.median(p),2) if p else None,
          "median_period_return_pct":round(statistics.median(v),6) if v else None,
          "min_period_return_pct":round(min(v),6) if v else None,"max_period_return_pct":round(max(v),6) if v else None,
          "median_end_nav_usd":round(statistics.median(e),2) if e else None})
    return out

def money(x):return "—" if x is None else chr(36)+f"{float(x):,.0f}"
def percent(x):return "—" if x is None else f"{float(x):.2f}%"

def report_text(summary,aggs,years,manifest):
    lines=["# SPY far-tail hedge: single-account NAV replay V1","",
      "Research only; no broker, no live orders. Phases are independent account simulations and are not summed.","",
      "## Rules and account accounting","",
      "- Fixed base lot: QQQ long PUT 1 : SPY short PUT 3, original HOLD_20_OR_DTE_LE_7 entry/exit schedule.",
      "- Comparison: no tail hedge versus the frozen OR trigger buying the same-expiry SPY 10-delta tail PUT next session, 1 or 3 contracts; hold to original base exit.",
      "- Starting NAV cases: $100k, $250k, $500k and $1m. Fixed lot size; NAV returns compound, but contract quantity is not increased as NAV grows.",
      "- SPY short-put collateral reserves strike × 100 × contracts for every open position. No borrowing or QQQ/SPY margin netting. New base entries and hedge buys are skipped if post-debit cash cannot retain the collateral reserve.",
      "- Entry/exit cash uses historical Ask/Bid sides and includes $0.05 per option-share per side plus $0.65 per contract per side. NAV marks longs at Bid and shorts at Ask, with estimated close costs.",
      "- No forward fill. A missing quote for any live leg makes that day's NAV missing. Quotes are daily EOD proxies, not guaranteed fills.","",
      "## Source controls","",
      f"- Base source-ledger rows: {manifest['base_trade_rows']}; conditional trigger rows: {manifest['overlay_rows']}.",
      f"- SHA-pinned chain and underlying files: {manifest['source_pin_count']}; chain dates {manifest['chain_first_date']} to {manifest['chain_end_date']}.",
      f"- Source ledger hashes reconciled: {manifest['baseline_sha_valid']}; resolved-trade P&L mismatches: {manifest['pnl_reconciliation_mismatch_n']}.",
      f"- Simulated accounts: {manifest['account_configurations']}; selected daily NAV rows: {manifest['daily_curve_rows']}.","",
      "## Results: median across five phase accounts","",
      "These medians describe five separate schedules, not pooled account profit. Range values are shown in the CSV output.","",
      "| Arm | Start NAV | Tail qty | Median end NAV | Median total return | Median CAGR | Median observed MaxDD | End NAVs available | Median base trades skipped | Median hedge buys skipped | NAV coverage |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in aggs:
        lines.append(f"| {r['arm']} | {money(r['starting_nav_usd'])} | {r['hedge_qty']} | {money(r['median_ending_nav_usd'])} | {percent(r['median_total_return_pct'])} | {percent(r['median_cagr_pct'])} | {percent(r['median_max_drawdown_observed_pct'])} | {r['ending_nav_available_n']}/{r['phase_accounts_n']} | {money(r['median_base_entries_skipped_capital_n'])} | {money(r['median_hedge_entries_skipped_capital_n'])} | {percent(r['median_nav_coverage_pct'])} |")
    lines += ["","## Yearly account returns: DTE45 medians","","2018 is partial from account inception. 2025 ends at 2025-12-12. A missing year-end mark is not forward-filled, so the next annual return may also be unavailable.","",
      "| Start NAV | Tail qty | Year | Period | Median P&L | Median account return | Valid phase returns |","|---:|---:|---:|---|---:|---:|---:|"]
    for r in years:
        if r["arm"]=="DTE45" and r["starting_nav_usd"] in (250000.0,1000000.0):
            lines.append(f"| {money(r['starting_nav_usd'])} | {r['hedge_qty']} | {r['year']} | {r['period_kind']} | {money(r['median_period_profit_usd'])} | {percent(r['median_period_return_pct'])} | {r['return_available_phases_n']}/{r['phase_accounts_n']} |")
    lines += ["","## Limits","",
      "- CAGR uses starting account capital and the exact data-end quoted NAV, never mean trade P&L.",
      "- Observed MaxDD uses complete available daily marks and may understate troughs when quotes are missing.",
      "- The full cash-collateral rule is intentionally conservative and does not represent any named broker's margin engine.",
      "- An unresolved option with no executable exit by expiry is marked to intrinsic at the underlying close, approximating exercise plus immediate same-close stock liquidation. Physical assignment, assignment fees and post-assignment share exposure are not modeled.",
      "- No margin borrowing, interest, financing, early exercise before expiry, forced liquidation, taxes, dividends, or timestamp-verified execution.",
      "- Failed scheduled exits remain open and unresolved; they are not silently filled with a later price.","",
      "See account_phase_summary.csv, account_summary_by_capital.csv, account_annual_returns.csv, account_annual_median_by_phase.csv, account_nav_selected.csv, capital_gates.csv and account_manifest.json."]
    return "\n".join(lines)

def run(args):
    OUT.mkdir(parents=True,exist_ok=True);cache=Path(args.cache).expanduser().resolve();cache.mkdir(parents=True,exist_ok=True)
    base,ov,hashes,om,hm,holding_file=load_ledgers()
    book,dates,qspots,spots,pins,stats,ids,first,end=load_market(base,ov,hm,cache)
    if end!=str(hm["chain_last_date"]):raise ValueError("Frozen chain end date mismatch")
    grouped=defaultdict(list)
    for k,r in base.items():
        x=dict(r);x["trade_key"]="|".join(map(str,k));grouped[(k[0],k[1])].append(x)
    if len(grouped)!=10:raise ValueError("Expected 2 arms x 5 phases")
    summaries,years,curves,gates=[],[],[],[]
    for arm in ARMS:
        for phase in PHASES:
            trades=grouped.get((arm,phase),[])
            if not trades:raise ValueError(f"Missing source ledger {arm}/{phase}")
            for start in STARTS:
                for h in HEDGES:
                    s,curve,annual,blocked=simulate(arm,phase,start,h,trades,ov,book,qspots,spots,dates,end)
                    summaries.append(s);years.extend(annual);gates.extend(blocked)
                    if phase==0:curves.extend(curve)
    aggs,year_aggs=median_summary(summaries),annual_medians(years)
    manifest={"schema":"spy-far-tail-single-account-nav.v1","status":"COMPLETED","base_policy":POLICY,
      "hedge_rule":RULE,"tail_label":TAIL,"hedge_quantities":list(HEDGES),"starting_nav_scenarios_usd":list(STARTS),
      "separate_phase_accounts":True,"phase_results_pooled_or_summed":False,
      "cash_collateral_rule":"SPY short put strike x 100 x open contracts, no borrowing or cross-underlying margin offsets",
      "baseline_sha_valid":hashes==hm.get("baseline_input_sha256"),"baseline_input_sha256":hashes,
      "overlay_manifest_sha256":digest(RES/"spy_far_tail_hedge_v1"/"manifest.json"),
      "holding_manifest_sha256":digest(RES/"spy_far_tail_holding_trigger_v2"/"holding_manifest.json"),
      "holding_trade_level_sha256":digest(holding_file),"code_sha256":digest(Path(__file__)),
      "source_repository":hm.get("option_chain_source"),"source_tree_commit":hm.get("option_chain_source_commit"),
      "source_pin_count":len(pins),"source_pins":pins,"chain_first_date":hm.get("chain_first_date"),"chain_end_date":end,
      "stream_stats":stats,"tracked_contract_count":{k:len(v) for k,v in ids.items()},
      "base_trade_rows":len(base),"overlay_rows":len(ov),"account_configurations":len(summaries),
      "annual_rows":len(years),"daily_curve_rows":len(curves),"capital_gate_events":len(gates),
      "slippage_per_option_share_per_side_usd":0.05,"commission_per_contract_per_side_usd":0.65,
      "pnl_reconciliation_mismatch_n":sum(int(x["pnl_reconciliation_mismatch_n"]) for x in summaries),
      "warnings":["EOD quotes are proxies, not fills.","No forward-fill of exact-contract marks.",
        "Observed MaxDD may understate risk across missing-quote gaps.","Cash-secured collateral is not a specific broker margin model.",
        "Unresolved contracts at expiry are priced at intrinsic using underlying close as an exercise plus immediate stock-liquidation proxy; physical assignment, early exercise and post-assignment share exposure are not modeled.",
        "No margin borrowing, funding, interest, tax, dividend, forced liquidation or timestamp-verified fills.",
        "Option-chain data ends on 2025-12-12.","Five phases are independent schedule runs, never summed.",
        "Fixed contract quantity: account NAV compounds but lot count is not dynamically scaled."]}
    writecsv(OUT/"account_phase_summary.csv",summaries)
    writecsv(OUT/"account_summary_by_capital.csv",aggs)
    writecsv(OUT/"account_annual_returns.csv",years)
    writecsv(OUT/"account_annual_median_by_phase.csv",year_aggs)
    writecsv(OUT/"account_nav_selected.csv",sorted(curves,key=lambda r:(r["arm"],r["starting_nav_usd"],r["hedge_qty"],r["date"])))
    if not gates:gates=[{"account_id":"","date":"","event":"","trade_key":"","decision":"NO_REJECTIONS","reason":"No capital or quote rejections"}]
    writecsv(OUT/"capital_gates.csv",gates)
    (OUT/"SPY_FAR_TAIL_ACCOUNT_NAV_REPORT.md").write_text(report_text(summaries,aggs,year_aggs,manifest),encoding="utf-8")
    manifest["output_sha256"]={p.name:digest(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="account_manifest.json"}
    required=("account_phase_summary.csv","account_summary_by_capital.csv","account_annual_returns.csv","account_annual_median_by_phase.csv","account_nav_selected.csv","capital_gates.csv","SPY_FAR_TAIL_ACCOUNT_NAV_REPORT.md")
    manifest["required_outputs_nonempty"]=all((OUT/f).is_file() and (OUT/f).stat().st_size>0 for f in required)
    if len(summaries)!=120 or len(pins)!=18 or not manifest["required_outputs_nonempty"]:raise RuntimeError("Final count/source/output gate failed")
    (OUT/"account_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":manifest["status"],"accounts":len(summaries),"source_pins":len(pins),"daily_nav_rows":len(curves),
       "capital_gate_events":len(gates),"pnl_reconciliation_mismatch_n":manifest["pnl_reconciliation_mismatch_n"],"output_dir":str(OUT)},sort_keys=True))
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache",type=Path,default=Path.home()/".cache"/"spy-options-account-nav-v1")
    m=run(p.parse_args())
    if m.get("status")!="COMPLETED" or not m.get("required_outputs_nonempty"):raise RuntimeError("NAV replay output gate failed")
if __name__=="__main__":main()
