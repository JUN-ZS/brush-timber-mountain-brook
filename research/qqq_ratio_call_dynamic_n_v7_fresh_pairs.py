#!/usr/bin/env python3
"""QQQ Ratio-Call Dynamic-N V7 — fresh-pair reconstruction.

Key change from V6:
  When the open short call becomes very low delta, the system does NOT add
  another copy of the old contract. It adds a NEW short+wing pair selected
  from the current market date, on the original entry expiry:
      short ~= 20 delta, wing ~= 8 delta.
  This is the literal interpretation of "short delta falls very low, then
  add short; add the same number of wings."

ENTRY:
  +1 ATM long call - 2 short calls + 2 farther OTM wings.
  Entry rejected when N=2 terminal max-loss proxy > 2% NAV.

N CONTROLLER:
  - N starts 2, max 4.
  - Fresh pair ADD: selected live short delta <= 0.10 for 2 consecutive
    sessions, and >=5 sessions since the last N change. Add ONE NEW pair.
    Resulting terminal max-loss <=2% NAV required.
  - Pair REDUCE: if any open short delta >=0.35, reduce one highest-delta
    short+wing pair. Repeat next session if still critical.
  - N never rises above 4.

PATH STATE:
  - Approach if the current High >= 98% of the closest open short strike.
  - Next session:
      reversal (Close lower than approach Close) + lead short buyback
      <=50% of that pair's entry premium -> buy back ONE lead SHORT only.
      continuation (Close >= approach Close) -> close ONE highest-delta
      SHORT+WING pair, not all shorts.

DOWNSIDE DD:
  - If package MTM loss >=25% of initial defined risk, reduce SHORT-only
    inventory to the risk target, but only where buyback Ask <= that pair's
    entry premium. Wings remain.
    
All execution uses historical option-chain Bid/Ask. Daily mark Mid.
No interpolation, no synthetic option prices, no optimization.
"""

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_harvest_v1 import (
    RELEASE_REPO, RELEASE_TAG, CAPITAL_USD, PCT_52W, DMA_EXT,
    COOLDOWN_DAYS, SHORT_DELTA, WING_DELTA, DTE_MIN, DTE_MAX,
    HOLD_MAX, RISK_PCT, APPROACH_FRAC, START_DATE, END_DATE,
    sha256_file, ensure_data, duck, load_underlying,
    build_selection_cache, fetch_all_quotes, q_at, executable, midpoint,
    max_loss_proxy, run_mode,
)

N_START = 2
N_CAP = 4
ADD_DELTA = 0.10
ADD_STREAK = 2
N_CHANGE_COOLDOWN = 5
REDUCE_DELTA = 0.35
DD_START = 0.25
HARVEST_FRACTION = 0.50


@dataclass
class OpenPair:
    short_id: str
    wing_id: str
    short_k: float
    wing_k: float
    entry_short_bid: float
    entry_wing_ask: float
    opened_date: pd.Timestamp
    origin: str
    active_short: bool = True
    active_wing: bool = True


def fetch_quotes_delta_all(con, opt_path, selection):
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
    if rows.empty:
        return pd.DataFrame()
    rows["date"] = pd.to_datetime(rows["date"])
    rows["contract_id"] = rows["contract_id"].astype(str)
    return rows.drop_duplicates(["date","contract_id"], keep="last").set_index(
        ["date","contract_id"]
    ).sort_index()


def fetch_fresh_pair_selection(con, opt_path, base_pairs):
    # base_pairs is a DataFrame of unique (date, expiry) keys for dates on which
    # a fresh pair may be required. One scan finds the current chain for each key.
    if base_pairs.empty:
        return {}

    keys = base_pairs.drop_duplicates().copy()
    keys["date"] = pd.to_datetime(keys["date"]).dt.date
    keys["expiration"] = pd.to_datetime(keys["expiration"]).dt.date

    # Use a temp relation rather than constructing a huge IN tuple.
    con.register("fresh_keys", keys)
    rows = duck(con, """
        SELECT CAST(o.date AS DATE) AS date,
               CAST(o.expiration AS DATE) AS expiration,
               CAST(o.contract_id AS VARCHAR) AS contract_id,
               o.strike, o.bid, o.ask, o.mark, o.delta, o.volume
        FROM read_parquet(?) o
        INNER JOIN fresh_keys k
          ON CAST(o.date AS DATE) = k.date
         AND CAST(o.expiration AS DATE) = k.expiration
        WHERE upper(o.type)='CALL'
          AND o.delta IS NOT NULL
          AND o.bid IS NOT NULL
          AND o.ask IS NOT NULL
    """, [str(opt_path)])
    try:
        con.unregister("fresh_keys")
    except Exception:
        pass

    if rows.empty:
        return {}

    rows["date"] = pd.to_datetime(rows["date"])
    rows["expiration"] = pd.to_datetime(rows["expiration"])
    out = {}
    for (dt, exp), g in rows.groupby(["date","expiration"], sort=True):
        # Current spot is joined later by caller. Select low-delta pair based on
        # the current chain only; strike must be above ATM/spot proxy supplied
        # through the candidate filter.
        # Pick the short closest 20Δ among OTM calls, then wing closest 8Δ above it.
        g = g.sort_values(["strike","volume"])
        out[(pd.Timestamp(dt), pd.Timestamp(exp))] = g
    return out


def terminal_max_loss_generic(cash, atm_k, pairs, spot):
    # All fresh pairs are on the same original expiry. The max terminal loss of
    # the current structure can therefore be computed on one common grid.
    max_wing = max([p.wing_k for p in pairs], default=spot * 1.2)
    max_short = max([p.short_k for p in pairs], default=spot * 1.1)
    grid = np.linspace(max(1.0, spot*0.20), max(spot*2.5, max_wing*1.25), 700)
    payoff = np.maximum(grid-atm_k,0.0)
    for p in pairs:
        if p.active_short:
            payoff -= np.maximum(grid-p.short_k,0.0)
        if p.active_wing:
            payoff += np.maximum(grid-p.wing_k,0.0)
    pnl = cash + payoff*100.0
    return max(0.0, -float(np.min(pnl)))


def select_fresh_pair(chain, spot, atm_k):
    g = chain[chain["strike"] > max(spot, atm_k)].copy()
    if g.empty:
        return None

    shorts = g.copy()
    shorts["err"] = (shorts["delta"] - SHORT_DELTA).abs()
    short = shorts.sort_values(["err","strike"]).iloc[0]

    wings = g[g["strike"] > float(short["strike"])].copy()
    if wings.empty:
        return None
    wings["err"] = (wings["delta"] - WING_DELTA).abs()
    wing = wings.sort_values(["err","strike"]).iloc[0]

    return short, wing


def row_delta(quotes, dt, cid):
    try:
        return float(quotes.loc[(pd.Timestamp(dt), str(cid))]["delta"])
    except Exception:
        return np.nan


def pair_buyback_price(quotes, dt, pair):
    q = q_at(quotes, dt, pair.short_id)
    return executable(q, "BUY")


def pair_wing_sell_price(quotes, dt, pair):
    q = q_at(quotes, dt, pair.wing_id)
    return executable(q, "SELL")


def make_pair(short, wing, dt, origin):
    return OpenPair(
        short_id=str(short["contract_id"]),
        wing_id=str(wing["contract_id"]),
        short_k=float(short["strike"]),
        wing_k=float(wing["strike"]),
        entry_short_bid=float(short["bid"]),
        entry_wing_ask=float(wing["ask"]),
        opened_date=pd.Timestamp(dt),
        origin=origin,
    )


def market_package_mark(quotes, dt, atm_id, atm_qty, pairs):
    qa = q_at(quotes, dt, atm_id)
    ma = midpoint(qa)
    if pd.isna(ma):
        return np.nan
    total = ma * 100.0
    for p in pairs:
        if p.active_short:
            total -= midpoint(q_at(quotes, dt, p.short_id)) * 100.0
        if p.active_wing:
            total += midpoint(q_at(quotes, dt, p.wing_id)) * 100.0
    return total


def process_trade(und, quotes, fresh_selection, entry_row, entry_legs):
    entry = pd.Timestamp(entry_row["date"])
    spot = float(entry_row["close"])
    expiry = pd.Timestamp(entry_legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

    # Initial N=2.
    base_ml = max_loss_proxy(entry_legs, N_START, spot)
    if base_ml > CAPITAL_USD*(RISK_PCT/100.0):
        return None, "RISK_GATE"

    atm_id = str(entry_legs["atm"]["contract_id"])
    atm_k = float(entry_legs["atm"]["strike"])

    qa0 = q_at(quotes, entry, atm_id)
    qs0 = q_at(quotes, entry, str(entry_legs["short"]["contract_id"]))
    qw0 = q_at(quotes, entry, str(entry_legs["wing"]["contract_id"]))
    if any(x is None for x in (qa0,qs0,qw0)):
        return None, "NO_ENTRY_QUOTES"

    atm_entry = executable(qa0,"BUY")
    short_entry = executable(qs0,"SELL")
    wing_entry = executable(qw0,"BUY")
    if any(pd.isna(x) for x in (atm_entry,short_entry,wing_entry)):
        return None, "NO_ENTRY_QUOTES"

    entry_cf = (atm_entry - N_START*short_entry + N_START*wing_entry)*100.0
    cash = -entry_cf

    pairs = []
    for _ in range(N_START):
        pairs.append(make_pair(
            entry_legs["short"], entry_legs["wing"], entry, "ENTRY"
        ))

    daily = und[(und["date"] >= entry) & (und["date"] <= end_date)].copy().reset_index(drop=True)
    if daily.empty:
        return None, "NO_UNDERLYING_WINDOW"

    n_change_i = -999
    low_streak = 0
    pending = None
    approach_armed = True
    events = []
    eq_rows = []

    for i,row in daily.iterrows():
        dt = pd.Timestamp(row["date"])

        # 1) Execute path action armed on the previous approach.
        if pending is not None and pd.Timestamp(pending["date"]) == dt:
            pstate = pending
            pending = None

            active_shorts = [p for p in pairs if p.active_short]
            if active_shorts:
                def risk_key(p):
                    d = row_delta(quotes, dt, p.short_id)
                    return -999 if pd.isna(d) else d
                lead = max(active_shorts, key=risk_key)
                lead_buy = pair_buyback_price(quotes, dt, lead)

                if float(row["close"]) >= float(pstate["approach_close"]):
                    # Continuation: reduce exactly one structural pair.
                    if len(active_shorts) > 1:
                        ws = pair_wing_sell_price(quotes, dt, lead)
                        if pd.notna(lead_buy) and pd.notna(ws):
                            cash += (-lead_buy + ws)*100.0
                            lead.active_short = False
                            lead.active_wing = False
                            n_change_i = i
                            events.append({
                                "date":str(dt.date()),
                                "event":"BREAKOUT_CONTINUATION_REDUCE_ONE_FRESH_PAIR",
                                "short_id":lead.short_id,
                                "short_delta":row_delta(quotes,dt,lead.short_id),
                            })
                    else:
                        if pd.notna(lead_buy):
                            cash += (-lead_buy)*100.0
                            lead.active_short = False
                            n_change_i = i
                            events.append({
                                "date":str(dt.date()),
                                "event":"BREAKOUT_CONTINUATION_REMOVE_LAST_SHORT",
                                "short_id":lead.short_id,
                            })
                elif pd.notna(lead_buy) and lead_buy <= HARVEST_FRACTION*lead.entry_short_bid:
                    cash += (-lead_buy)*100.0
                    lead.active_short = False
                    n_change_i = i
                    events.append({
                        "date":str(dt.date()),
                        "event":"PROFIT_HARVEST50_LEAD_SHORT_ONLY",
                        "short_id":lead.short_id,
                        "short_delta":row_delta(quotes,dt,lead.short_id),
                        "buyback_usd":lead_buy*100.0,
                    })
                else:
                    events.append({
                        "date":str(dt.date()),
                        "event":"REVERSAL_NO_50PCT_RECOVERY",
                        "short_id":lead.short_id,
                        "short_delta":row_delta(quotes,dt,lead.short_id),
                    })
            approach_armed = False

        # 2) Arm approach based on closest active short.
        active_shorts = [p for p in pairs if p.active_short]
        if active_shorts and pending is None and dt > entry:
            closest = min(active_shorts, key=lambda p: p.short_k)
            approach_now = float(row["high"]) >= APPROACH_FRAC*closest.short_k
            if approach_now and approach_armed and i+1 < len(daily):
                approach_armed = False
                pending = {
                    "date":pd.Timestamp(daily.iloc[i+1]["date"]),
                    "approach_date":dt,
                    "approach_close":float(row["close"]),
                    "short_id":closest.short_id,
                }
            elif not approach_now:
                approach_armed = True

        # 3) Current package mark before governors.
        mark = market_package_mark(quotes, dt, atm_id, 1, pairs)
        loss_fraction = np.nan
        if pd.notna(mark) and base_ml > 0:
            # package_pnl = current MTM relative to entry cashflow.
            package_pnl = cash + mark
            loss_fraction = max(0.0, -package_pnl)/base_ml

        # 4) DD governor: SHORT ONLY, only profitable shorts, never wings.
        active_shorts = [p for p in pairs if p.active_short]
        if active_shorts and pd.notna(loss_fraction) and loss_fraction >= DD_START:
            dd_target = max(0, int(math.ceil(N_START*(1.0-loss_fraction))))
            reduce_n = max(0, len(active_shorts)-dd_target)
            if reduce_n:
                candidates=[]
                for p in active_shorts:
                    bp=pair_buyback_price(quotes,dt,p)
                    if pd.notna(bp) and bp <= p.entry_short_bid:
                        candidates.append((bp,p))
                candidates.sort(key=lambda x:x[0])
                for bp,p in candidates[:reduce_n]:
                    cash += (-bp)*100.0
                    p.active_short=False
                    n_change_i=i
                    events.append({
                        "date":str(dt.date()),
                        "event":"DD_PROFIT_RECOVER_FRESH_SHORT_ONLY",
                        "short_id":p.short_id,
                        "loss_fraction":loss_fraction,
                        "buyback_usd":bp*100.0,
                    })

        # 5) Dynamic N: high-delta pair reductions first.
        active_shorts = [p for p in pairs if p.active_short]
        if active_shorts:
            deltas=[(row_delta(quotes,dt,p.short_id),p) for p in active_shorts]
            deltas=[(d,p) for d,p in deltas if pd.notna(d)]
            if deltas:
                deltas.sort(key=lambda x:x[0], reverse=True)
                if deltas[0][0] >= REDUCE_DELTA and (i-n_change_i)>=1:
                    d,p=deltas[0]
                    ws=pair_wing_sell_price(quotes,dt,p)
                    bp=pair_buyback_price(quotes,dt,p)
                    if pd.notna(ws) and pd.notna(bp):
                        cash += (-bp+ws)*100.0
                        p.active_short=False;p.active_wing=False
                        n_change_i=i;low_streak=0
                        events.append({
                            "date":str(dt.date()),
                            "event":"DELTA_REDUCE_ONE_FRESH_PAIR",
                            "short_id":p.short_id,
                            "short_delta":d,
                        })

                # Low-delta persistence and fresh pair add.
                lead_d=max(deltas,key=lambda x:x[0])[0]
                if lead_d <= ADD_DELTA:
                    low_streak += 1
                else:
                    low_streak = 0

                open_structural=[p for p in pairs if p.active_short and p.active_wing]
                if low_streak>=ADD_STREAK and (i-n_change_i)>=N_CHANGE_COOLDOWN and len(open_structural)<N_CAP:
                    # Use the original expiry but CURRENT chain.
                    chain=fresh_selection.get((dt,expiry))
                    if chain is not None:
                        fp=select_fresh_pair(chain, float(row["close"]), atm_k)
                        if fp is not None:
                            sh,wi=fp
                            sell_sh=executable({"bid":float(sh["bid"]),"ask":float(sh["ask"])},"SELL")
                            buy_wi=executable({"bid":float(wi["bid"]),"ask":float(wi["ask"])},"BUY")
                            if pd.notna(sell_sh) and pd.notna(buy_wi):
                                new_cash=cash+(sell_sh-buy_wi)*100.0
                                new_pairs=open_structural+[make_pair(sh,wi,dt,"FRESH_ADD")]
                                budget=CAPITAL_USD*(RISK_PCT/100.0)
                                risk=terminal_max_loss_generic(new_cash,atm_k,new_pairs,float(row["close"]))
                                if risk<=budget:
                                    cash=new_cash
                                    pairs.append(make_pair(sh,wi,dt,"FRESH_ADD"))
                                    n_change_i=i;low_streak=0
                                    events.append({
                                        "date":str(dt.date()),
                                        "event":"LOW_DELTA_ADD_FRESH_PAIR",
                                        "short_id":str(sh["contract_id"]),
                                        "wing_id":str(wi["contract_id"]),
                                        "short_delta":float(sh["delta"]),
                                        "wing_delta":float(wi["delta"]),
                                        "candidate_risk_usd":risk,
                                    })

        # 6) Final daily mark.
        mark=market_package_mark(quotes,dt,atm_id,1,pairs)
        if pd.notna(mark):
            eq_rows.append((dt,CAPITAL_USD+cash+mark))

        if dt>=end_date:
            break

    # Terminal close all active legs.
    q_atm=q_at(quotes,end_date,atm_id)
    sell_atm=executable(q_atm,"SELL")
    if pd.isna(sell_atm):
        return None,"NO_EXIT_QUOTES"

    exit_cf=sell_atm*100.0
    for p in pairs:
        if p.active_short:
            q=q_at(quotes,end_date,p.short_id)
            bp=executable(q,"BUY")
            if pd.isna(bp): return None,"NO_EXIT_QUOTES"
            exit_cf -= bp*100.0
        if p.active_wing:
            q=q_at(quotes,end_date,p.wing_id)
            sw=executable(q,"SELL")
            if pd.isna(sw): return None,"NO_EXIT_QUOTES"
            exit_cf += sw*100.0

    pnl=cash+exit_cf
    eq_rows.append((pd.Timestamp(end_date),CAPITAL_USD+pnl))

    return {
        "entry":entry,"exit":pd.Timestamp(end_date),
        "n_initial":N_START,
        "n_pair_final":sum(p.active_wing for p in pairs),
        "n_short_final":sum(p.active_short for p in pairs),
        "pnl_usd":float(pnl),
        "max_loss_proxy_usd":float(base_ml),
        "events":events,
        "eq_rows":eq_rows,
    },"OK"


def run_dynamic(und,quotes,selection,fresh_selection):
    signal_rows=und[und["signal"] & und["dma200"].notna()].copy()
    trades=[];rejects={};next_allowed=None

    for _,row in signal_rows.iterrows():
        entry=pd.Timestamp(row["date"])
        if next_allowed is not None and entry<=next_allowed:
            continue
        legs=selection.get(entry)
        if legs is None:
            rejects["NO_LEGS"]=rejects.get("NO_LEGS",0)+1;continue
        tr,status=process_trade(und,quotes,fresh_selection,row,legs)
        if tr is None:
            rejects[status]=rejects.get(status,0)+1;continue
        trades.append(tr)
        next_allowed=tr["exit"]+pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [],{"mode":"DYNAMIC_N_V7_FRESH_PAIRS","trades":0,"rejections":rejects},pd.DataFrame()

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
        "mode":"DYNAMIC_N_V7_FRESH_PAIRS",
        "N_start":N_START,"N_cap":N_CAP,
        "trades":int(len(trdf)),
        "win_rate":float((trdf["pnl_usd"]>0).mean()),
        "avg_trade_usd":float(trdf["pnl_usd"].mean()),
        "worst_trade_usd":float(trdf["pnl_usd"].min()),
        "best_trade_usd":float(trdf["pnl_usd"].max()),
        "total_return":float(total),"cagr":float(cagr),
        "maxdd_daily_mtm":float(eqdf["dd"].min()),
        "maxdd_realized":float((trdf["pnl_usd"].cumsum().add(CAPITAL_USD).div(trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax())-1).min()),
        "years":float(years),
        "profit_harvest_events":int(sum(e["event"]=="PROFIT_HARVEST50_LEAD_SHORT_ONLY" for e in ev)),
        "continuation_events":int(sum(e["event"] in ("BREAKOUT_CONTINUATION_REDUCE_ONE_FRESH_PAIR","BREAKOUT_CONTINUATION_REMOVE_LAST_SHORT") for e in ev)),
        "dd_short_recover_events":int(sum(e["event"]=="DD_PROFIT_RECOVER_FRESH_SHORT_ONLY" for e in ev)),
        "low_delta_add_fresh_pair_events":int(sum(e["event"]=="LOW_DELTA_ADD_FRESH_PAIR" for e in ev)),
        "delta_pair_reduce_events":int(sum(e["event"]=="DELTA_REDUCE_ONE_FRESH_PAIR" for e in ev)),
        "avg_n_pair_final":float(trdf["n_pair_final"].mean()),
        "avg_n_short_final":float(trdf["n_short_final"].mean()),
        "rejections":rejects,
        "data_start":str(trdf["entry"].min().date()),
        "data_end":str(trdf["exit"].max().date()),
    }
    return trades,stats,eqdf


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data-dir",default="data");ap.add_argument("--out",default="artifacts")
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    opt_path,und_path=ensure_data(Path(args.data_dir));und=load_underlying(und_path)

    dates=[pd.Timestamp(x) for x in und.loc[und["signal"],"date"].tolist()]
    con=duckdb.connect()
    selection,selection_rejects=build_selection_cache(con,opt_path,dates)

    # Build the (date, original-expiry) keyspace used for potential fresh adds.
    keys=[]
    for dt,legs in selection.items():
        exp=pd.Timestamp(legs["expiry"])
        for d in und.loc[(und["date"]>=dt)&(und["date"]<=min(dt+pd.Timedelta(days=HOLD_MAX),exp)),"date"]:
            keys.append({"date":pd.Timestamp(d),"expiration":exp})
    fresh_selection=fetch_fresh_pair_selection(con,opt_path,pd.DataFrame(keys))

    quotes=fetch_quotes_delta_all(con,opt_path,selection)

    # Merge fresh pair contracts into the quote store with one additional batch scan.
    fresh_ids=set()
    for chain in fresh_selection.values():
        if chain is None or chain.empty: continue
        # Keep a bounded candidate set per chain: top ~20 closest delta values
        # around the required short/wing targets plus a few strike neighbors.
        fresh_ids.update(chain.iloc[(chain["delta"]-SHORT_DELTA).abs().argsort()[:5]]["contract_id"].astype(str))
        fresh_ids.update(chain.iloc[(chain["delta"]-WING_DELTA).abs().argsort()[:5]]["contract_id"].astype(str))

    if fresh_ids:
        more=duck(con,"""
            SELECT CAST(date AS DATE) AS date,
                   CAST(contract_id AS VARCHAR) AS contract_id,
                   bid, ask, mark, delta
            FROM read_parquet(?)
            WHERE contract_id IN (SELECT * FROM UNNEST(?))
              AND CAST(date AS DATE) BETWEEN ? AND ?
        """,[str(opt_path),sorted(fresh_ids),START_DATE.date(),END_DATE.date()])
        if not more.empty:
            more["date"]=pd.to_datetime(more["date"]);more["contract_id"]=more["contract_id"].astype(str)
            more=more.drop_duplicates(["date","contract_id"],keep="last").set_index(["date","contract_id"]).sort_index()
            if quotes.empty:
                quotes=more
            else:
                quotes=pd.concat([quotes,more]).drop_duplicates(["date","contract_id"],keep="last").sort_index()

    trades, stats, eqdf = run_dynamic(und, quotes, selection, fresh_selection)
    results=[stats]
    pd.DataFrame([{
        **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
        "events_json":json.dumps(t["events"],ensure_ascii=False)
    } for t in trades]).to_csv(out/"trades_DYNAMIC_N_V7_FRESH_PAIRS.csv",index=False)
    if not eqdf.empty:
        eqdf.to_csv(out/"equity_DYNAMIC_N_V7_FRESH_PAIRS.csv",index=False)

    report={
        "research_contract":{
            "strategy":"1 ATM Long Call + dynamic fresh N Short OTM Calls + matching fresh OTM wings",
            "entry":"1x2x2; N0=2",
            "fresh_add":"when live lead short delta <=0.10 for 2 sessions and >=5 sessions since last N change, add ONE NEW current-date short ~=20delta + wing ~=8delta on the original expiry, only if terminal risk remains <=2% NAV",
            "pair_reduce":"when any active short delta >=0.35, close one highest-delta SHORT+WING pair",
            "path":"approach High >=98% of closest short strike; next-day reversal harvest one lead SHORT when buyback <=50% entry premium; continuation closes one highest-delta SHORT+WING pair",
            "downside_dd":"package loss >=25% of initial risk can close profitable SHORT only; wings stay",
            "DTE":[DTE_MIN,DTE_MAX],"hold_max_days":HOLD_MAX,
            "entry_execution":"ATM buy Ask; initial shorts sell Bid; initial wings buy Ask",
            "management_execution":"short buyback Ask; wing sale Bid for pair reduction",
            "daily_mark":"Mid","strict_quotes":True,"no_optimization":True,
        },
        "data":{
            "source_repo":RELEASE_REPO,"release_tag":RELEASE_TAG,
            "options_sha256":sha256_file(opt_path),"underlying_sha256":sha256_file(und_path),
            "underlying_range":[str(und["date"].min().date()),str(und["date"].max().date())],
            "selection_cache":len(selection),"fresh_key_count":len(fresh_selection),
            "fresh_candidate_contracts":len(fresh_ids)
        },
        "results":results
    }
    (out/"ratio_call_dynamic_n_v7_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_dynamic_n_v7_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__=="__main__":
    main()
