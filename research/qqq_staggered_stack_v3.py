#!/usr/bin/env python3
"""QQQ staggered stack + within-vintage adaptive geometry V3.

V3 combines two previously isolated dimensions:
  A) cross-date overlapping vintages (V2)
  B) within-vintage upward-wave geometry migration (V1)

Per-vintage entry:
  +1 ~50Δ Call
  -2 ~20Δ Calls
  +2 ~8Δ farther Call Wings
  +1 ~25Δ Long Put
  -1 ~10Δ Short Put

Within each vintage, adaptive mode applies:
  previous close >= anchor close + 1.0*ATR20
  -> next trading day:
       Short Call 20Δ -> 30Δ -> 40Δ
       Short Put  10Δ -> 5Δ
       Long Put retained
       ATM Call / Call Wings / N / expiry fixed

Cross-date modes:
  1 layer, 2 layer half-stack, 4 layer stack.

For each K-layer mode, compare:
  STATIC_STACK
  ADAPTIVE_STACK

Portfolio starts at USD 100,000, allocating 100,000/K per admitted vintage.
Overlapping vintages are marked and aggregated directly.
"""

from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb

from qqq_ratio_call_harvest_v1 import ensure_data, load_underlying, sha256_file
from qqq_state_adaptive_geometry_v1 import select_entry, trade

BASE_CAPITAL = 100_000.0
STACKS = {
    "1_LAYER": 1,
    "2_LAYER_HALF_STACK": 2,
    "4_LAYER_STACK": 4,
}


def build_candidates(con, opt_path, u, adaptive):
    candidates = []
    rejects = {}

    for _, row in u.iterrows():
        if not bool(row.signal):
            continue

        dt = pd.Timestamp(row.date)
        legs = select_entry(con, opt_path, dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"] = rejects.get("NO_ENTRY_LEGS", 0) + 1
            continue

        tr, status = trade(con, opt_path, u, row, legs, adaptive)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue

        candidates.append(tr)

    candidates.sort(key=lambda x: pd.Timestamp(x["entry"]))
    return candidates, rejects


def admit_stack(candidates, max_layers):
    selected = []
    active = []

    for tr in candidates:
        entry = pd.Timestamp(tr["entry"])
        active = [x for x in active if pd.Timestamp(x["exit"]) >= entry]
        if len(active) >= max_layers:
            continue
        selected.append(tr)
        active.append(tr)

    return selected


def portfolio_curve(selected, max_layers, dates):
    if not selected:
        return pd.DataFrame(
            columns=["date", "nav", "active_layers", "tail_long_puts"]
        )

    alloc = BASE_CAPITAL / max_layers
    starts, exits, paths = {}, {}, {}

    for i, tr in enumerate(selected):
        key = f"v{i:05d}"
        en, ex = pd.Timestamp(tr["entry"]), pd.Timestamp(tr["exit"])
        starts.setdefault(en, []).append((key, tr))
        exits.setdefault(ex, []).append((key, tr))
        paths[key] = (
            pd.DataFrame(tr["eq"], columns=["date", "raw_nav"])
            .assign(date=lambda x: pd.to_datetime(x["date"]))
            .drop_duplicates("date")
            .set_index("date")
            .sort_index()
        )

    cash = BASE_CAPITAL
    active = {}
    realized = {}
    rows = []

    for dt0 in dates:
        dt = pd.Timestamp(dt0)

        for key, tr in exits.get(dt, []):
            if key not in active:
                continue
            p = paths[key]
            if dt in p.index:
                final_nav = float(p.loc[dt, "raw_nav"])
            else:
                final_nav = float(p.iloc[-1].raw_nav)
            cash += alloc * final_nav / BASE_CAPITAL
            realized[key] = final_nav
            del active[key]

        for key, tr in starts.get(dt, []):
            if key in active or key in realized:
                continue
            cash -= alloc
            active[key] = tr

        nav = float(cash)
        tails = 0

        for key, tr in active.items():
            p = paths[key]
            hist = p.loc[p.index <= dt]
            if hist.empty:
                continue
            raw_nav = float(hist.iloc[-1].raw_nav)
            nav += alloc * raw_nav / BASE_CAPITAL
            tails += 1

        rows.append(
            {
                "date": dt,
                "nav": nav,
                "active_layers": len(active),
                "tail_long_puts": tails,
            }
        )

    out = pd.DataFrame(rows)
    out["peak"] = out.nav.cummax()
    out["dd"] = out.nav / out.peak - 1.0
    return out


def summarize(selected, curve, label, stack_layers, candidate_count):
    if curve.empty:
        return {"mode": label, "stack_layers": stack_layers, "trades": 0}

    final_nav = float(curve.nav.iloc[-1])
    start = pd.Timestamp(curve.date.iloc[0])
    end = pd.Timestamp(curve.date.iloc[-1])
    years = max((end-start).days/365.25, 1/365.25)

    return {
        "mode": label,
        "stack_layers": stack_layers,
        "trades": int(len(selected)),
        "candidate_signals": int(candidate_count),
        "entries_skipped_full": int(candidate_count-len(selected)),
        "total_return_pct": float(100*(final_nav/BASE_CAPITAL-1)),
        "cagr": float((final_nav/BASE_CAPITAL)**(1/years)-1),
        "maxdd_daily_mtm": float(curve.dd.min()),
        "avg_active_layers": float(curve.active_layers.mean()),
        "max_active_layers": int(curve.active_layers.max()),
        "days_with_2plus_layers": int((curve.active_layers>=2).sum()),
        "days_with_4_layers": int((curve.active_layers>=4).sum()),
        "tail_days_weighted": int(curve.tail_long_puts.sum()),
        "data_start": str(start.date()),
        "data_end": str(end.date()),
        "final_nav_usd": final_nav,
    }


def write_trades(path, selected):
    rows=[]
    for i,tr in enumerate(selected):
        rows.append({
            "vintage_id": f"v{i:05d}",
            "entry": str(pd.Timestamp(tr["entry"]).date()),
            "exit": str(pd.Timestamp(tr["exit"]).date()),
            "pnl_usd_100k_unit": float(tr["pnl_usd"]),
            "return_pct_unit": float(tr["return_pct"]),
            "entry_cashflow_usd_100k_unit": float(tr["entry_cashflow_usd"]),
            "migration_count": int(len(tr["migrations"])),
            "migration_events_json": json.dumps(tr["migrations"], ensure_ascii=False),
        })
    pd.DataFrame(rows).to_csv(path,index=False)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",default="data")
    ap.add_argument("--out",default="artifacts")
    args=ap.parse_args()

    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)

    opt_path, up_path = ensure_data(Path(args.data_dir))
    u=load_underlying(up_path).copy().reset_index(drop=True)
    con=duckdb.connect()

    static_candidates, static_rej = build_candidates(con,opt_path,u,False)
    adaptive_candidates, adaptive_rej = build_candidates(con,opt_path,u,True)

    results=[]
    trading_dates=u["date"].tolist()

    for mode_name,adaptive,candidates,rejections in [
        ("STATIC_STACK",False,static_candidates,static_rej),
        ("ADAPTIVE_STACK",True,adaptive_candidates,adaptive_rej),
    ]:
        for stack_name,k in STACKS.items():
            selected=admit_stack(candidates,k)
            curve=portfolio_curve(selected,k,trading_dates)
            label=f"{mode_name}_{stack_name}"

            results.append(
                summarize(
                    selected,curve,label,k,len(candidates)
                )
            )
            write_trades(out/f"trades_{label}.csv",selected)
            if not curve.empty:
                curve.to_csv(out/f"equity_{label}.csv",index=False)

    pd.DataFrame(results).to_csv(out/"summary.csv",index=False)

    report={
        "research_id":"QQQ_STAGGERED_STACK_V3",
        "status":"REAL_QQQ_CHAIN_STACK_PLUS_DYNAMIC_GEOMETRY",
        "contract":{
            "per_vintage":"+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ Call Wings +1 ~25Δ Long Put -1 ~10Δ Short Put",
            "static_mode":"no within-vintage migration",
            "adaptive_mode":"20Δ->30Δ->40Δ Short Call and 10Δ->5Δ Short Put; Long Put retained",
            "wave_trigger":"previous close >= anchor close + 1.0*ATR20; migrate on T+1",
            "stack_modes":STACKS,
            "allocation":"BASE_CAPITAL / K per admitted vintage",
            "expiry":"fixed per vintage",
            "holding":"30 days maximum or expiry",
            "overlap":True,
            "cooldown":False,
            "black_scholes":False,
            "interpolation":False,
            "optimization":False
        },
        "data":{
            "options_sha256":sha256_file(opt_path),
            "underlying_sha256":sha256_file(up_path),
            "underlying_range":[str(pd.Timestamp(u.date.min()).date()),str(pd.Timestamp(u.date.max()).date())]
        },
        "results":results,
        "rejections":{
            "static":static_rej,
            "adaptive":adaptive_rej
        }
    }

    (out/"qqq_staggered_stack_v3_result.json").write_text(
        json.dumps(report,indent=2),encoding="utf-8"
    )
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":
    main()
