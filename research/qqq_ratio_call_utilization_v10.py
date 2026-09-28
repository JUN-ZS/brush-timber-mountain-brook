#!/usr/bin/env python3
"""
QQQ Ratio-Call Utilization V10

V7 management unchanged:
+1 ATM call - N short OTM calls + N farther OTM long wings.
Dynamic initial N = largest N in 1..6 whose exact terminal payoff max-loss
(using executable entry quotes) <= 5% of initial capital.
State management:
- downside package stop at 50% of initial package max-loss proxy,
- touch of short strike arms next-day breakout confirmation,
- confirmed breakout closes all SHORT only and keeps all WING,
- failed breakout closes one SHORT only,
- approach/reversal harvest closes one paired SHORT+WING unit when
  next-day close reverses and pair profit >= 50% of entry pair credit,
- observed short delta >= 0.60 removes one paired unit.
No re-add.

NEW TEST:
Allow 1, 2, 3, or 4 concurrent position lanes. Each lane uses the same
5% per-lane risk budget and same V7 trade engine. One signal day opens at
most one package. A lane is reusable 10 calendar days after its package exits.
No lane count was optimized.

Portfolio curve:
Each trade contributes its local mark-to-mid delta relative to the starting
capital until exit; realized delta is carried forward after exit.
4% bond carry is shown only as a separate hypothetical comparison.
"""
import argparse
import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_state_v7 import (
    CAPITAL_USD, START_DATE, END_DATE, COOLDOWN_DAYS,
    ensure_data, sha256_file, load_underlying, select_contracts,
    fetch_quotes, choose_initial_n, manage_trade
)

LANES = (1, 2, 3, 4)
LANE_RISK = 0.05
BOND_CARRY = 0.04


def run_concurrent(und, quotes, selection, lanes):
    signals = und[und["signal"] & und["dma200"].notna()].copy()
    available = [pd.Timestamp(START_DATE)] * lanes
    trades, rejects = [], {}

    for _, row in signals.iterrows():
        entry = pd.Timestamp(row["date"])
        free = [i for i,d in enumerate(available) if entry > d]
        if not free:
            continue
        lane = min(free)
        legs = selection.get(entry)
        if legs is None:
            rejects["NO_SELECTION"] = rejects.get("NO_SELECTION",0)+1
            continue
        n = choose_initial_n(legs, LANE_RISK)
        if n <= 0:
            rejects["RISK_GATE"] = rejects.get("RISK_GATE",0)+1
            continue
        tr, status = manage_trade(und, quotes, row, legs, n, "STATE_MACHINE")
        if tr is None:
            rejects[status] = rejects.get(status,0)+1
            continue
        tr["lane"] = lane
        trades.append(tr)
        available[lane] = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [], {"lanes":lanes,"risk_per_lane":LANE_RISK,"trades":0,"rejections":rejects}, pd.DataFrame()

    trdf = pd.DataFrame([
        {k:v for k,v in t.items() if k not in ("events","eq_rows")}
        for t in trades
    ]).sort_values("entry").reset_index(drop=True)

    dates = pd.DatetimeIndex(und["date"]).sort_values().unique()
    port_delta = pd.Series(0.0, index=dates)

    for t in trades:
        pts = pd.DataFrame(t["eq_rows"], columns=["date","local_equity"])
        pts["date"] = pd.to_datetime(pts["date"])
        pts = pts.sort_values("date").groupby("date",as_index=False)["local_equity"].last().set_index("date")
        s = pd.Series(np.nan, index=dates, dtype=float)
        for d,v in pts["local_equity"].items():
            if d in s.index:
                s.loc[d] = float(v) - CAPITAL_USD
        s.loc[s.index < pd.Timestamp(t["entry"])] = 0.0
        s = s.ffill().fillna(0.0)
        port_delta = port_delta.add(s, fill_value=0.0)

    equity = CAPITAL_USD + port_delta

    first = dates.min()
    years = max((dates.max()-first).days/365.25, 1/365.25)
    bond = CAPITAL_USD * np.power(1.0+BOND_CARRY, (dates-first).days.astype(float)/365.25)
    equity_bond = pd.Series(bond,index=dates) + port_delta

    dd = equity/equity.cummax()-1.0
    dd_b = equity_bond/equity_bond.cummax()-1.0
    total = float(equity.iloc[-1]/CAPITAL_USD-1.0)
    total_b = float(equity_bond.iloc[-1]/CAPITAL_USD-1.0)
    cagr = ((1+total)**(1/years)-1) if 1+total>0 else -1
    cagr_b = ((1+total_b)**(1/years)-1) if 1+total_b>0 else -1

    stats = {
        "lanes": int(lanes),
        "risk_per_lane": LANE_RISK,
        "max_simultaneous_risk_budget": lanes*LANE_RISK,
        "trades": int(len(trdf)),
        "win_rate": float((trdf.pnl_usd>0).mean()),
        "avg_trade_usd": float(trdf.pnl_usd.mean()),
        "worst_trade_usd": float(trdf.pnl_usd.min()),
        "best_trade_usd": float(trdf.pnl_usd.max()),
        "total_return": total,
        "cagr": float(cagr),
        "maxdd_daily_mtm": float(dd.min()),
        "maxdd_realized_trade": float((
            trdf.pnl_usd.cumsum().add(CAPITAL_USD) /
            trdf.pnl_usd.cumsum().add(CAPITAL_USD).cummax() - 1
        ).min()),
        "hypothetical_bond4pct_cagr": float(cagr_b),
        "hypothetical_bond4pct_maxdd_daily_mtm": float(dd_b.min()),
        "years": float(years),
        "initial_N_distribution": trdf.n_initial.value_counts().sort_index().to_dict(),
        "breakout_events": int(trdf.breakout_events.sum()),
        "continuation_events": int(trdf.continuation_events.sum()),
        "harvest_events": int(trdf.harvest_events.sum()),
        "delta_reduce_events": int(trdf.delta_reduce_events.sum()),
        "downside_stop_events": int(trdf.downside_stop_events.sum()),
        "rejections": rejects,
        "data_start": str(trdf.entry.min().date()),
        "data_end": str(trdf.exit.max().date()),
    }
    curve = pd.DataFrame({
        "date": dates,
        "equity": equity.values,
        "equity_plus_bond4pct_hypothetical": equity_bond.values,
        "dd": dd.values,
        "dd_plus_bond4pct_hypothetical": dd_b.values,
    })
    return trades, stats, curve


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",default="data")
    ap.add_argument("--out",default="artifacts")
    args=ap.parse_args()

    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    opt_path, und_path = ensure_data(Path(args.data_dir))
    und=load_underlying(und_path)
    dates=[pd.Timestamp(x) for x in und.loc[und["signal"],"date"]]

    con=duckdb.connect()
    selection, selection_rejects = select_contracts(con,opt_path,dates)
    quotes=fetch_quotes(con,opt_path,selection)

    stats_all=[]; all_report=[]
    for lanes in LANES:
        trades,stats,curve=run_concurrent(und,quotes,selection,lanes)
        stats_all.append(stats)
        if trades:
            pd.DataFrame([
                {**{k:v for k,v in t.items() if k not in ("events","eq_rows")},
                 "events_json":json.dumps(t["events"],ensure_ascii=False)}
                for t in trades
            ]).to_csv(out/f"trades_lanes{lanes}_risk5pct.csv",index=False)
        curve.to_csv(out/f"equity_lanes{lanes}_risk5pct.csv",index=False)

    report={
        "research_contract":{
            "base_management":"V7 State Machine, unchanged",
            "lanes_tested":list(LANES),
            "risk_per_lane":LANE_RISK,
            "cooldown_per_lane_days":COOLDOWN_DAYS,
            "one_entry_per_signal_day":True,
            "lane_assignment":"lowest-numbered free lane",
            "overlap_allowed":True,
            "hypothetical_bond_carry":"4% annual on full capital, separate sensitivity only",
            "no_lane_optimization":True
        },
        "data":{
            "source_repo":"lambdaclass/options_portfolio_backtester",
            "release_tag":"data-v1",
            "options_sha256":sha256_file(opt_path),
            "underlying_sha256":sha256_file(und_path),
            "underlying_range":[str(und.date.min().date()),str(und.date.max().date())],
            "signals":len(dates),
            "selections":len(selection),
            "selection_rejects":selection_rejects
        },
        "results":stats_all
    }
    (out/"ratio_call_utilization_v10_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(stats_all).to_csv(out/"ratio_call_utilization_v10_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)

if __name__=="__main__":
    main()
