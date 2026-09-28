#!/usr/bin/env python3
"""QQQ Ratio-Call SHORT-ONLY Harvest V1.

Frozen management rule:
1) Entry: +1 ATM call - N OTM short calls + N farther OTM long wings.
2) When High >= 98% of the selected short strike, arm a next-trading-day check.
3) On the next trading day:
   - if Close >= approach-day Close: continuation -> buy back ALL remaining short calls.
   - if Close < approach-day Close AND the short call has recovered at least
     50% of its entry premium (entry Bid - next-day Ask >= 50%*entry Bid):
       buy back ceil(N_short/2) short calls ONLY. Keep ALL long wings + ATM long.
4) Re-arm only after price leaves the approach zone.
5) Exit remaining legs at 30 calendar days or expiry.
No optimization.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import duckdb

from qqq_ratio_call_harvest_v1 import (
    RELEASE_REPO, RELEASE_TAG, CAPITAL_HKD, HKD_PER_USD, CAPITAL_USD,
    PCT_52W, DMA_EXT, COOLDOWN_DAYS, APPROACH_FRAC,
    DTE_MIN, DTE_MAX, HOLD_MAX, RISK_PCT,
    START_DATE, END_DATE,
    sha256_file, ensure_data, duck,
    load_underlying, build_selection_cache, fetch_all_quotes,
    q_at, executable, midpoint, max_loss_proxy, run_mode,
)


def process_shortonly(und, quotes, entry_row, legs, n_initial):
    entry = pd.Timestamp(entry_row["date"])
    spot = float(entry_row["close"])
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

    atm_id = str(legs["atm"]["contract_id"])
    short_id = str(legs["short"]["contract_id"])
    wing_id = str(legs["wing"]["contract_id"])

    qa0 = q_at(quotes, entry, atm_id)
    qs0 = q_at(quotes, entry, short_id)
    qw0 = q_at(quotes, entry, wing_id)
    if any(x is None for x in (qa0, qs0, qw0)):
        return None, "NO_ENTRY_QUOTES"

    atm_entry = executable(qa0, "BUY")
    short_entry = executable(qs0, "SELL")
    wing_entry = executable(qw0, "BUY")
    if any(pd.isna(x) for x in (atm_entry, short_entry, wing_entry)):
        return None, "NO_ENTRY_QUOTES"

    ml = max_loss_proxy(legs, n_initial, spot)
    if ml > CAPITAL_USD * (RISK_PCT / 100.0):
        return None, "RISK_GATE"

    entry_cf = (atm_entry - n_initial * short_entry + n_initial * wing_entry) * 100.0
    cash = -entry_cf

    n_short = int(n_initial)
    n_wing = int(n_initial)
    pending_approach = None
    approach_armed = True
    events = []
    eq_rows = []
    daily = und[(und["date"] >= entry) & (und["date"] <= end_date)].copy().reset_index(drop=True)
    if daily.empty:
        return None, "NO_UNDERLYING_WINDOW"

    exit_date = end_date
    exit_reason = "EXPIRY_OR_TIME"

    for i, row in daily.iterrows():
        dt = pd.Timestamp(row["date"])
        is_final = False

        # Execute the pre-armed next-day decision only on that day.
        if pending_approach is not None and pd.Timestamp(pending_approach["date"]) == dt:
            approach = pending_approach
            pending_approach = None
            close_now = float(row["close"])

            qs = q_at(quotes, dt, short_id)
            qshort_ask = executable(qs, "BUY")
            if close_now >= float(approach["approach_close"]):
                if pd.notna(qshort_ask) and n_short > 0:
                    before = n_short
                    cash += (-n_short * qshort_ask) * 100.0
                    events.append({
                        "date": str(dt.date()),
                        "event": "CONTINUATION_REMOVE_ALL_SHORT",
                        "approach_date": str(approach["approach_date"].date()),
                        "approach_close": float(approach["approach_close"]),
                        "next_close": close_now,
                        "n_short_before": before,
                        "n_short_closed": before,
                        "n_short_after": 0,
                        "short_entry_premium_usd": short_entry * 100.0,
                        "short_buyback_usd": qshort_ask * 100.0,
                    })
                    n_short = 0
            elif pd.notna(qshort_ask) and n_short > 0:
                short_profit = short_entry - qshort_ask
                threshold = 0.50 * short_entry
                if short_entry > 0.0 and short_profit >= threshold:
                    h = int(math.ceil(n_short / 2.0))
                    before = n_short
                    cash += (-h * qshort_ask) * 100.0
                    n_short -= h
                    events.append({
                        "date": str(dt.date()),
                        "event": "HARVEST50_SHORT_ONLY",
                        "approach_date": str(approach["approach_date"].date()),
                        "approach_close": float(approach["approach_close"]),
                        "next_close": close_now,
                        "n_short_before": before,
                        "n_short_closed": h,
                        "n_short_after": n_short,
                        "harvest_fraction": h / before,
                        "short_entry_premium_usd": short_entry * 100.0,
                        "harvest_threshold_usd": threshold * 100.0,
                        "short_profit_usd": short_profit * 100.0,
                    })
            approach_armed = False

        # Observe a new approach and arm the next-day check.
        if pending_approach is None and n_short > 0 and dt > entry:
            approach_now = float(row["high"]) >= APPROACH_FRAC * float(legs["short"]["strike"])
            if approach_now and approach_armed:
                approach_armed = False
                if i + 1 < len(daily):
                    pending_approach = {
                        "date": pd.Timestamp(daily.iloc[i + 1]["date"]),
                        "approach_date": dt,
                        "approach_close": float(row["close"]),
                    }
            elif not approach_now:
                approach_armed = True

        if dt >= end_date:
            is_final = True

        qa = q_at(quotes, dt, atm_id)
        qs = q_at(quotes, dt, short_id)
        qw = q_at(quotes, dt, wing_id)
        ma, ms, mw = midpoint(qa), midpoint(qs), midpoint(qw)
        if not any(pd.isna(x) for x in (ma, ms, mw)):
            eq = CAPITAL_USD + cash + ma * 100.0 - n_short * ms * 100.0 + n_wing * mw * 100.0
            eq_rows.append((dt, eq))

        if is_final:
            break

    qxa = q_at(quotes, exit_date, atm_id)
    qxs = q_at(quotes, exit_date, short_id)
    qxw = q_at(quotes, exit_date, wing_id)
    if any(x is None for x in (qxa, qxs, qxw)):
        candidates = sorted(set(
            d for (d, cid) in quotes.index
            if d >= exit_date and cid in {atm_id, short_id, wing_id}
        ))
        found = None
        for d in candidates:
            if all(q_at(quotes, d, cid) is not None for cid in (atm_id, short_id, wing_id)):
                found = pd.Timestamp(d)
                break
        if found is None:
            return None, "NO_EXIT_QUOTES"
        exit_date = found
        qxa = q_at(quotes, exit_date, atm_id)
        qxs = q_at(quotes, exit_date, short_id)
        qxw = q_at(quotes, exit_date, wing_id)

    sa = executable(qxa, "SELL")
    bs = executable(qxs, "BUY")
    sw = executable(qxw, "SELL")
    if any(pd.isna(x) for x in (sa, bs, sw)):
        return None, "NO_EXIT_QUOTES"

    exit_cf = (sa - n_short * bs + n_wing * sw) * 100.0
    harvest_cash = sum(
        -int(e["n_short_closed"]) * float(e["short_buyback_usd"]) 
        for e in events if e["event"] == "HARVEST50_SHORT_ONLY"
    )
    continuation_cash = sum(
        -int(e["n_short_closed"]) * float(e["short_buyback_usd"])
        for e in events if e["event"] == "CONTINUATION_REMOVE_ALL_SHORT"
    )
    pnl = -entry_cf + harvest_cash + continuation_cash + (
        sa * 100.0 - n_short * bs * 100.0 + n_wing * sw * 100.0
    )
    eq_rows.append((pd.Timestamp(exit_date), CAPITAL_USD + pnl))

    return {
        "entry": entry,
        "exit": pd.Timestamp(exit_date),
        "reason": "SHORT_ONLY_GOVERNED",
        "n_initial": int(n_initial),
        "n_short_final": int(n_short),
        "n_wing_final": int(n_wing),
        "atm_strike": float(legs["atm"]["strike"]),
        "short_strike": float(legs["short"]["strike"]),
        "wing_strike": float(legs["wing"]["strike"]),
        "entry_cashflow_usd": float(entry_cf),
        "harvest_events": int(sum(e["event"] == "HARVEST50_SHORT_ONLY" for e in events)),
        "continuation_events": int(sum(e["event"] == "CONTINUATION_REMOVE_ALL_SHORT" for e in events)),
        "events": events,
        "harvest_cashflow_usd": float(harvest_cash),
        "continuation_cashflow_usd": float(continuation_cash),
        "exit_cashflow_usd": float(exit_cf),
        "pnl_usd": float(pnl),
        "max_loss_proxy_usd": float(ml),
        "extension": float(entry_row["ext200"]),
        "ratio52": float(entry_row["ratio52"]),
        "expiry": expiry,
        "eq_rows": eq_rows,
    }, "OK"


def run_shortonly(und, quotes, selection, n_fixed):
    rows = und[und["signal"] & und["dma200"].notna()].copy()
    trades, rejects = [], {}
    next_allowed = None
    for _, row in rows.iterrows():
        entry = pd.Timestamp(row["date"])
        if next_allowed is not None and entry <= next_allowed:
            continue
        legs = selection.get(entry)
        if legs is None:
            rejects["NO_LEGS"] = rejects.get("NO_LEGS", 0) + 1
            continue
        tr, status = process_shortonly(und, quotes, row, legs, n_fixed)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue
        trades.append(tr)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return trades, {"N": n_fixed, "trades": 0, "rejections": rejects}, pd.DataFrame()

    trdf = pd.DataFrame([{k:v for k,v in t.items() if k not in ("events","eq_rows")} for t in trades]).sort_values("entry")
    points = [p for t in trades for p in t["eq_rows"]]
    eqdf = pd.DataFrame(points, columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"] = eqdf["equity"].cummax()
    eqdf["dd"] = eqdf["equity"]/eqdf["peak"] - 1.0

    end_equity = CAPITAL_USD + trdf["pnl_usd"].sum()
    years = max((trdf["exit"].iloc[-1] - trdf["entry"].iloc[0]).days / 365.25, 1/365.25)
    total_return = end_equity / CAPITAL_USD - 1.0
    cagr = (1.0 + total_return)**(1.0/years) - 1.0 if 1+total_return > 0 else -1.0

    stats = {
        "mode": "SHORT_ONLY_GOVERNED",
        "N": int(n_fixed),
        "trades": int(len(trdf)),
        "win_rate": float((trdf["pnl_usd"] > 0).mean()),
        "avg_trade_usd": float(trdf["pnl_usd"].mean()),
        "worst_trade_usd": float(trdf["pnl_usd"].min()),
        "best_trade_usd": float(trdf["pnl_usd"].max()),
        "total_return": float(total_return),
        "cagr": float(cagr),
        "maxdd_daily_mtm": float(eqdf["dd"].min()),
        "maxdd_realized": float((trdf["pnl_usd"].cumsum().add(CAPITAL_USD).div(trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax()) - 1.0).min()),
        "years": float(years),
        "harvest_events": int(trdf["harvest_events"].sum()),
        "continuation_events": int(trdf["continuation_events"].sum()),
        "rejections": rejects,
        "data_start": str(trdf["entry"].min().date()),
        "data_end": str(trdf["exit"].max().date()),
    }
    return trades, stats, eqdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--n", nargs="+", type=int, default=[2,3,4])
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    opt_path, und_path = ensure_data(data_dir)
    und = load_underlying(und_path)

    dates = [pd.Timestamp(x) for x in und.loc[und["signal"], "date"].tolist()]
    con = duckdb.connect()
    selection, rejects = build_selection_cache(con, opt_path, dates)
    quotes = fetch_all_quotes(con, opt_path, selection)

    results = []
    for n in args.n:
        _, base_stats, _ = run_mode(und, quotes, selection, n, "BASELINE_TOUCH")
        _, short_trades, eqdf = run_shortonly(und, quotes, selection, n)
        results += [base_stats, short_trades]
        pd.DataFrame([{
            **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
            "events_json": json.dumps(t["events"], ensure_ascii=False)
        } for t in short_trades]).to_csv(out / f"trades_N{n}_SHORT_ONLY_GOVERNED.csv", index=False)
        if not eqdf.empty:
            eqdf.to_csv(out / f"equity_N{n}_SHORT_ONLY_GOVERNED.csv", index=False)

    report = {
        "research_contract": {
            "strategy": "1 ATM Long Call + N OTM Short Calls + N Far OTM Long Wings",
            "entry_signal": "QQQ close / 52-week high >= 0.98 AND close / 200DMA - 1 >= 0.08",
            "approach": f"daily High >= {APPROACH_FRAC:.2f} * selected short strike, edge-triggered",
            "next_day_test": "next trading-day Close compared with approach-day Close",
            "reversal_action": "if next Close < approach Close AND short premium recovered >= 50% of entry premium, close ceil(N_short/2) SHORT calls ONLY; keep all wings + ATM",
            "continuation_action": "if next Close >= approach Close, buy back ALL remaining SHORT calls; keep wings + ATM",
            "DTE": [DTE_MIN, DTE_MAX],
            "hold_max_days": HOLD_MAX,
            "short_delta": 0.20,
            "wing_delta": 0.08,
            "risk_gate": f"entry terminal-payoff max-loss proxy <= {RISK_PCT:.2f}% NAV",
            "entry_execution": "ATM buy Ask; short sell Bid; wing buy Ask",
            "mark": "daily Mid",
            "strict_quotes": True,
            "no_optimization": True,
        },
        "data": {
            "source_repo": RELEASE_REPO,
            "release_tag": RELEASE_TAG,
            "options_sha256": sha256_file(opt_path),
            "underlying_sha256": sha256_file(und_path),
            "underlying_range": [str(und["date"].min().date()), str(und["date"].max().date())],
        },
        "results": results
    }
    (out/"ratio_call_shortonly_v1_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_shortonly_v1_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__ == "__main__":
    main()
