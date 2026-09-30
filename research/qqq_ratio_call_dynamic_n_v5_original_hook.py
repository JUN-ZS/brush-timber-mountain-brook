#!/usr/bin/env python3
"""QQQ Ratio-Call Dynamic-N V5 — original-hook reconstruction.

This run follows the earlier research hook more literally:

ENTRY:
  +1 ATM call - 2 OTM short calls + 2 farther OTM long call wings.
  N starts at 2, not 4.
  Entry is admitted only if N=2 terminal max-loss <= 2% NAV.

N CONTROLLER:
  - Add one SHORT+WING pair per qualifying day when selected short delta <= 0.10,
    up to N=4, BUT only if the resulting current-position terminal max-loss
    remains <= 2% NAV.
  - Reduce one SHORT+WING pair when short delta reaches 0.35, another at 0.50,
    another at 0.65, another at 0.80.
  - Thus N is path-dependent and can move both up and down, but never exceeds 4.
  - No look-ahead: all decisions use that day's observed quotes/delta.

PATH STATES:
  - Approach: High >= 98% of short strike.
  - Next-day reversal: if Close falls AND short buyback Ask <= 50% of entry
    premium, close ceil(N_short/2) SHORT calls only. Wings remain.
  - Next-day continuation: if Close >= approach Close, close all remaining SHORT.
    ATM + wings remain.

DOWNSIDE DD:
  - If package MTM loss >=25% of initial risk, progressively recover
    SHORT-only, but only when the buyback Ask <= the entry short sale Bid.
    WINGS are not sold by this downside governor.

No optimization. No synthetic option prices. No interpolation.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_harvest_v1 import (
    RELEASE_REPO, RELEASE_TAG, CAPITAL_USD,
    PCT_52W, DMA_EXT, COOLDOWN_DAYS, SHORT_DELTA,
    DTE_MIN, DTE_MAX, HOLD_MAX, RISK_PCT, APPROACH_FRAC,
    START_DATE, END_DATE,
    sha256_file, ensure_data, duck, load_underlying,
    build_selection_cache, fetch_all_quotes, q_at, executable, midpoint,
    max_loss_proxy, run_mode,
)

N_START = 2
N_CAP = 4
ADD_DELTA = 0.10
REDUCE_LEVELS = [0.35, 0.50, 0.65, 0.80]
DD_START = 0.25
HARVEST_FRACTION = 0.50


def fetch_quotes_delta(con, opt_path, selection):
    ids = sorted({
        str(legs[key]["contract_id"])
        for legs in selection.values()
        for key in ("atm", "short", "wing")
    })
    rows = duck(con, """
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS contract_id,
               bid, ask, mark, delta
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """, [str(opt_path), ids, START_DATE.date(), END_DATE.date()])
    rows["date"] = pd.to_datetime(rows["date"])
    rows["contract_id"] = rows["contract_id"].astype(str)
    return rows.drop_duplicates(["date","contract_id"], keep="last").set_index(
        ["date","contract_id"]
    ).sort_index()


def terminal_max_loss(cash, atm_k, short_k, wing_k, n_short, n_pair, spot):
    grid = np.linspace(max(1.0, spot * 0.20), max(spot * 2.5, wing_k * 1.25), 600)
    payoff = (
        np.maximum(grid-atm_k, 0.0)
        - n_short*np.maximum(grid-short_k, 0.0)
        + n_pair*np.maximum(grid-wing_k, 0.0)
    ) * 100.0
    terminal_pnl = cash + payoff
    return max(0.0, -float(np.min(terminal_pnl)))


def current_structural_risk(
    cash, legs, spot, n_short, n_pair,
    atm_id, short_id, wing_id, quotes, dt
):
    qa, qs, qw = q_at(quotes, dt, atm_id), q_at(quotes, dt, short_id), q_at(quotes, dt, wing_id)
    if any(x is None for x in (qa, qs, qw)):
        return None
    buy_short = executable(qs, "BUY")
    buy_wing = executable(qw, "BUY")
    if pd.isna(buy_short) or pd.isna(buy_wing):
        return None
    return {
        "max_loss": terminal_max_loss(
            cash,
            float(legs["atm"]["strike"]),
            float(legs["short"]["strike"]),
            float(legs["wing"]["strike"]),
            n_short, n_pair, spot
        )
    }


def process_trade(und, quotes, entry_row, legs):
    entry = pd.Timestamp(entry_row["date"])
    spot = float(entry_row["close"])
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

    qa0, qs0, qw0 = q_at(quotes, entry, str(legs["atm"]["contract_id"])), \
                    q_at(quotes, entry, str(legs["short"]["contract_id"])), \
                    q_at(quotes, entry, str(legs["wing"]["contract_id"]))
    if any(x is None for x in (qa0, qs0, qw0)):
        return None, "NO_ENTRY_QUOTES"

    atm_id = str(legs["atm"]["contract_id"])
    short_id = str(legs["short"]["contract_id"])
    wing_id = str(legs["wing"]["contract_id"])

    atm_entry = executable(qa0, "BUY")
    short_entry = executable(qs0, "SELL")
    wing_entry = executable(qw0, "BUY")
    if any(pd.isna(x) for x in (atm_entry, short_entry, wing_entry)):
        return None, "NO_ENTRY_QUOTES"

    # Literal 1x2x2 starting structure.
    n0 = N_START
    initial_risk = max_loss_proxy(legs, n0, spot)
    if initial_risk > CAPITAL_USD*(RISK_PCT/100.0):
        return None, "RISK_GATE"

    entry_cf = (atm_entry - n0*short_entry + n0*wing_entry)*100.0
    cash = -entry_cf
    n_pair = n0
    n_short = n0

    approach_armed = True
    pending = None
    events = []
    eq_rows = []
    daily = und[(und["date"] >= entry) & (und["date"] <= end_date)].copy().reset_index(drop=True)
    if daily.empty:
        return None, "NO_UNDERLYING_WINDOW"

    for i,row in daily.iterrows():
        dt = pd.Timestamp(row["date"])
        is_final = dt >= end_date

        # --- Path state: T -> T+1 ---
        if pending is not None and pd.Timestamp(pending["date"]) == dt and n_short > 0:
            p = pending
            pending = None
            close_now = float(row["close"])
            qs = q_at(quotes, dt, short_id)
            buy_short = executable(qs, "BUY")
            if pd.notna(buy_short):
                if close_now >= float(p["approach_close"]):
                    before = n_short
                    cash += (-before*buy_short)*100.0
                    n_short = 0
                    events.append({
                        "date":str(dt.date()),
                        "event":"BREAKOUT_CONTINUATION_REMOVE_ALL_SHORT",
                        "n_short_before":before,"n_short_closed":before,"n_short_after":0,
                        "approach_date":str(p["approach_date"].date()),
                        "approach_close":float(p["approach_close"]),
                        "next_close":close_now,
                        "short_buyback_usd":buy_short*100.0
                    })
                elif buy_short <= HARVEST_FRACTION*short_entry:
                    h=int(math.ceil(n_short/2.0))
                    before=n_short
                    cash += (-h*buy_short)*100.0
                    n_short -= h
                    events.append({
                        "date":str(dt.date()),
                        "event":"PROFIT_HARVEST50_SHORT_ONLY",
                        "n_short_before":before,"n_short_closed":h,"n_short_after":n_short,
                        "approach_date":str(p["approach_date"].date()),
                        "approach_close":float(p["approach_close"]),
                        "next_close":close_now,
                        "short_entry_premium_usd":short_entry*100.0,
                        "short_buyback_usd":buy_short*100.0
                    })
                else:
                    events.append({
                        "date":str(dt.date()),
                        "event":"REVERSAL_NO_50PCT_SHORT_RECOVERY",
                        "approach_date":str(p["approach_date"].date()),
                        "approach_close":float(p["approach_close"]),
                        "next_close":close_now,
                        "short_entry_premium_usd":short_entry*100.0,
                        "actual_buyback_usd":buy_short*100.0
                    })
            approach_armed=False

        # --- Arm path state ---
        if pending is None and n_short > 0 and dt > entry:
            approach_now = float(row["high"]) >= APPROACH_FRAC*float(legs["short"]["strike"])
            if approach_now and approach_armed and i+1 < len(daily):
                approach_armed=False
                pending={
                    "date":pd.Timestamp(daily.iloc[i+1]["date"]),
                    "approach_date":dt,
                    "approach_close":float(row["close"])
                }
            elif not approach_now:
                approach_armed=True

        # --- Mid-mark current package ---
        qa,qs,qw=q_at(quotes,dt,atm_id),q_at(quotes,dt,short_id),q_at(quotes,dt,wing_id)
        ma,ms,mw=midpoint(qa),midpoint(qs),midpoint(qw)
        package_pnl=np.nan
        if all(pd.notna(x) for x in (ma,ms,mw)):
            package_pnl=cash+ma*100.0-n_short*ms*100.0+n_pair*mw*100.0

        # --- Downside governor: SHORT-only risk recovery ---
        if n_short>0 and pd.notna(package_pnl) and initial_risk>0:
            loss_frac=max(0.0,-package_pnl)/initial_risk
            if loss_frac >= DD_START:
                dd_target=max(0, int(math.ceil(n0*(1.0-loss_frac))))
                reduce_short=max(0,n_short-dd_target)
                if reduce_short>0:
                    qs_now=q_at(quotes,dt,short_id)
                    buy_short_now=executable(qs_now,"BUY")
                    if pd.notna(buy_short_now) and buy_short_now<=short_entry:
                        before=n_short
                        cash+=(-reduce_short*buy_short_now)*100.0
                        n_short-=reduce_short
                        events.append({
                            "date":str(dt.date()),"event":"DD_PROFIT_RECOVER_SHORT_ONLY",
                            "package_pnl_mid_usd":package_pnl,
                            "initial_risk_usd":initial_risk,
                            "loss_fraction_of_risk":loss_frac,
                            "n_short_before":before,
                            "n_short_closed":reduce_short,
                            "n_short_after":n_short,
                            "short_buyback_usd":buy_short_now*100.0
                        })

        # --- Dynamic N controller, driven by current delta ---
        if n_short > 0:
            try:
                d=float(quotes.loc[(dt,short_id)]["delta"])
            except Exception:
                d=np.nan

            # Downshift ladder: every +0.15 delta over entry target removes one pair.
            if not pd.isna(d):
                reduce_levels=sum(d>=x for x in REDUCE_LEVELS)
                delta_target=max(0,n0-reduce_levels)

                # Upshift only while delta is very low, at most one pair per session.
                if d <= ADD_DELTA and n_pair < N_CAP and n_short == n_pair:
                    candidate=n_pair+1
                    qs_now=q_at(quotes,dt,short_id)
                    qw_now=q_at(quotes,dt,wing_id)
                    add_short_price=executable(qs_now,"BUY")
                    add_wing_buy=executable(qw_now,"BUY")
                    if pd.notna(add_short_price) and pd.notna(add_wing_buy):
                        # Add pair cashflow: sell one short at today's Bid, buy one
                        # wing at today's Ask.
                        sell_short_add=executable(qs_now,"SELL")
                        buy_wing_add=executable(qw_now,"BUY")
                        cash_after=cash+(sell_short_add-buy_wing_add)*100.0
                        candidate_risk=terminal_max_loss(
                            cash_after,
                            float(legs["atm"]["strike"]),
                            float(legs["short"]["strike"]),
                            float(legs["wing"]["strike"]),
                            n_short+1,n_pair+1,spot
                        )
                        budget=CAPITAL_USD*(RISK_PCT/100.0)
                        if candidate_risk <= budget:
                            cash=cash_after
                            n_pair+=1
                            n_short+=1
                            events.append({
                                "date":str(dt.date()),
                                "event":"LOW_DELTA_ADD_PAIR",
                                "short_delta":d,
                                "n_pair_after":n_pair,
                                "n_short_after":n_short,
                                "candidate_risk_usd":candidate_risk,
                                "risk_budget_usd":budget,
                                "added_short_sell_usd":sell_short_add*100.0,
                                "added_wing_buy_usd":buy_wing_add*100.0
                            })
                        else:
                            events.append({
                                "date":str(dt.date()),
                                "event":"LOW_DELTA_ADD_BLOCKED_RISK",
                                "short_delta":d,
                                "candidate_risk_usd":candidate_risk,
                                "risk_budget_usd":budget,
                                "n_pair_current":n_pair
                            })

                # Downshift pair count from the same delta state.
                target=min(n_pair,n_short,delta_target)
                if target<n_pair:
                    reduce_by=n_pair-target
                    res=close_pair_now=pair_result=None
                    qs_now=q_at(quotes,dt,short_id)
                    qw_now=q_at(quotes,dt,wing_id)
                    buy_short_now=executable(qs_now,"BUY")
                    sell_wing_now=executable(qw_now,"SELL")
                    if pd.notna(buy_short_now) and pd.notna(sell_wing_now):
                        cash+=(-reduce_by*buy_short_now+reduce_by*sell_wing_now)*100.0
                        before=n_pair
                        n_pair=target
                        n_short=min(n_short,n_pair)
                        events.append({
                            "date":str(dt.date()),
                            "event":"DELTA_REDUCE_PAIR",
                            "short_delta":d,
                            "n_pair_before":before,
                            "n_pair_closed":reduce_by,
                            "n_pair_after":n_pair,
                            "n_short_after":n_short,
                            "short_buyback_usd":buy_short_now*100.0,
                            "wing_sale_usd":sell_wing_now*100.0
                        })

        # --- Final mark ---
        qa,qs,qw=q_at(quotes,dt,atm_id),q_at(quotes,dt,short_id),q_at(quotes,dt,wing_id)
        ma,ms,mw=midpoint(qa),midpoint(qs),midpoint(qw)
        if all(pd.notna(x) for x in (ma,ms,mw)):
            eq_rows.append((dt,CAPITAL_USD+cash+ma*100.0-n_short*ms*100.0+n_pair*mw*100.0))

        if is_final:
            break

    # Terminal close.
    qxa,qxs,qxw=q_at(quotes,end_date,atm_id),q_at(quotes,end_date,short_id),q_at(quotes,end_date,wing_id)
    if any(x is None for x in (qxa,qxs,qxw)):
        candidates=sorted(set(d for (d,cid) in quotes.index if d>=end_date and cid in {atm_id,short_id,wing_id}))
        found=None
        for d in candidates:
            if all(q_at(quotes,d,cid) is not None for cid in (atm_id,short_id,wing_id)):
                found=pd.Timestamp(d);break
        if found is None:
            return None,"NO_EXIT_QUOTES"
        end_date=found
        qxa,qxs,qxw=q_at(quotes,end_date,atm_id),q_at(quotes,end_date,short_id),q_at(quotes,end_date,wing_id)

    sa,bs,sw=executable(qxa,"SELL"),executable(qxs,"BUY"),executable(qxw,"SELL")
    if any(pd.isna(x) for x in (sa,bs,sw)):
        return None,"NO_EXIT_QUOTES"

    pnl=cash+(sa*100.0-n_short*bs*100.0+n_pair*sw*100.0)
    eq_rows.append((pd.Timestamp(end_date),CAPITAL_USD+pnl))

    return {
        "entry":entry,"exit":pd.Timestamp(end_date),
        "n_initial":n0,"n_pair_final":n_pair,"n_short_final":n_short,
        "pnl_usd":float(pnl),"max_loss_proxy_usd":float(initial_risk),
        "events":events,"eq_rows":eq_rows
    },"OK"


def run_dynamic(und,quotes,selection):
    rows=und[und["signal"] & und["dma200"].notna()].copy()
    trades=[]; rejects={}; next_allowed=None
    for _,row in rows.iterrows():
        entry=pd.Timestamp(row["date"])
        if next_allowed is not None and entry<=next_allowed:
            continue
        legs=selection.get(entry)
        if legs is None:
            rejects["NO_LEGS"]=rejects.get("NO_LEGS",0)+1;continue
        tr,status=process_trade(und,quotes,row,legs)
        if tr is None:
            rejects[status]=rejects.get(status,0)+1;continue
        trades.append(tr)
        next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [],{"mode":"DYNAMIC_N_V5_ORIGINAL_HOOK","trades":0,"rejections":rejects},pd.DataFrame()

    trdf=pd.DataFrame([{k:v for k,v in t.items() if k not in ("events","eq_rows")} for t in trades]).sort_values("entry").reset_index(drop=True)
    pts=[p for t in trades for p in t["eq_rows"]]
    eqdf=pd.DataFrame(pts,columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"]=eqdf["equity"].cummax();eqdf["dd"]=eqdf["equity"]/eqdf["peak"]-1.0
    end_eq=CAPITAL_USD+trdf["pnl_usd"].sum()
    years=max((trdf["exit"].iloc[-1]-trdf["entry"].iloc[0]).days/365.25,1/365.25)
    total=end_eq/CAPITAL_USD-1.0
    cagr=(1+total)**(1/years)-1 if 1+total>0 else -1
    ev=[e for t in trades for e in t["events"]]
    stats={
        "mode":"DYNAMIC_N_V5_ORIGINAL_HOOK",
        "N_start":N_START,"N_cap":N_CAP,
        "trades":int(len(trdf)),
        "win_rate":float((trdf["pnl_usd"]>0).mean()),
        "avg_trade_usd":float(trdf["pnl_usd"].mean()),
        "worst_trade_usd":float(trdf["pnl_usd"].min()),
        "best_trade_usd":float(trdf["pnl_usd"].max()),
        "total_return":float(total),"cagr":float(cagr),
        "maxdd_daily_mtm":float(eqdf["dd"].min()),
        "maxdd_realized":float((trdf["pnl_usd"].cumsum().add(CAPITAL_USD).div(trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax())-1).min()),
        "years":years,
        "profit_harvest_events":int(sum(e["event"]=="PROFIT_HARVEST50_SHORT_ONLY" for e in ev)),
        "continuation_events":int(sum(e["event"]=="BREAKOUT_CONTINUATION_REMOVE_ALL_SHORT" for e in ev)),
        "dd_short_recover_events":int(sum(e["event"]=="DD_PROFIT_RECOVER_SHORT_ONLY" for e in ev)),
        "low_delta_add_pair_events":int(sum(e["event"]=="LOW_DELTA_ADD_PAIR" for e in ev)),
        "delta_pair_reduce_events":int(sum(e["event"]=="DELTA_REDUCE_PAIR" for e in ev)),
        "avg_n_initial":float(trdf["n_initial"].mean()),
        "avg_n_pair_final":float(trdf["n_pair_final"].mean()),
        "avg_n_short_final":float(trdf["n_short_final"].mean()),
        "rejections":rejects,
        "data_start":str(trdf["entry"].min().date()),
        "data_end":str(trdf["exit"].max().date())
    }
    return trades,stats,eqdf


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    opt_path,und_path=ensure_data(Path(args.data_dir));und=load_underlying(und_path)
    dates=[pd.Timestamp(x) for x in und.loc[und["signal"],"date"].tolist()]
    con=duckdb.connect();selection,sel_rejects=build_selection_cache(con,opt_path,dates)
    quotes=fetch_quotes_delta(con,opt_path,selection)
    quotes_base=fetch_all_quotes(con,opt_path,selection)
    _,b2,_=run_mode(und,quotes_base,selection,2,"BASELINE_TOUCH")
    _,b3,_=run_mode(und,quotes_base,selection,3,"BASELINE_TOUCH")
    _,b4,_=run_mode(und,quotes_base,selection,4,"BASELINE_TOUCH")
    trades,dyn,eqdf=run_dynamic(und,quotes,selection)

    results=[b2,b3,b4,dyn]
    pd.DataFrame([{
        **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
        "events_json":json.dumps(t["events"],ensure_ascii=False)
    } for t in trades]).to_csv(out/"trades_DYNAMIC_N_V5_ORIGINAL_HOOK.csv",index=False)
    if not eqdf.empty:eqdf.to_csv(out/"equity_DYNAMIC_N_V5_ORIGINAL_HOOK.csv",index=False)

    report={
        "research_contract":{
            "strategy":"1 ATM Long Call + dynamic N Short OTM Calls + dynamic N Far OTM Long Wings",
            "entry_structure":"1x2x2; N0=2",
            "add_rule":"if selected short delta <=0.10, add at most one SHORT+WING pair per session up to N=4, only if current-position terminal max-loss after the add <=2% NAV",
            "reduce_rule":"short delta >=0.35/0.50/0.65/0.80 progressively reduces N by one pair per crossed level",
            "profit_recovery":"approach High >=98% short strike; next Close < approach Close; buyback Ask <=50% entry short Bid; close ceil(N_short/2) SHORT only",
            "breakout_continuation":"approach then next Close >= approach Close; remove all remaining SHORT; retain ATM and wings",
            "downside_governor":"package MTM loss >=25% of initial risk; close profitable SHORT only; never use this governor to sell wing",
            "risk_budget":"2% NAV",
            "DTE":[DTE_MIN,DTE_MAX],"hold_max_days":HOLD_MAX,
            "entry_execution":"ATM buy Ask; short sell Bid; wing buy Ask",
            "management_execution":"short buyback Ask; wing sale Bid for pair reductions",
            "daily_mark":"Mid","strict_quotes":True,"no_optimization":True,
        },
        "data":{
            "source_repo":RELEASE_REPO,"release_tag":RELEASE_TAG,
            "options_sha256":sha256_file(opt_path),"underlying_sha256":sha256_file(und_path),
            "underlying_range":[str(und["date"].min().date()),str(und["date"].max().date())],
            "selection_cache":len(selection),"selection_rejects":sel_rejects,
        },
        "results":results
    }
    (out/"ratio_call_dynamic_n_v5_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_dynamic_n_v5_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__=="__main__":main()
