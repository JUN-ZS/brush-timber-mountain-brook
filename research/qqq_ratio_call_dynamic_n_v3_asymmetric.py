#!/usr/bin/env python3
"""QQQ Ratio-Call Dynamic-N V3 — asymmetric two-way governor.

Frozen architecture:
  +1 ATM long call - N0 short OTM calls + N0 farther OTM long wings.

ENTRY:
  N0 = largest N in {1,2,3,4} whose terminal-payoff max-loss proxy <= 2% NAV.
  This avoids rejecting trades merely because N=4 is too large.

STATE MACHINE:
  1) UPSIDE governor (short-convexity risk):
     short delta starts near 0.20. Each +0.15 increment removes one
     SHORT+WING pair. This reduces N_pair monotonically.

  2) DOWNSIDE governor (package drawdown):
     monitor package MTM loss / initial defined risk.
     Starting at 25% risk consumption, target SHORT count scales as
       ceil(N0 * (1 - loss_fraction)).
     IMPORTANT: this governor closes SHORT calls ONLY, and only when the
     current buyback Ask is <= entry SHORT sale Bid (i.e. not locking a
     short loss). WINGS remain.

  3) PROFIT RECOVERY:
     High >= 98% of short strike on T, then T+1 Close < T Close,
     and short buyback Ask <= 50% entry premium:
     close ceil(N_short/2) SHORT calls only. Wings remain.

  4) BREAKOUT CONTINUATION:
     Same approach then T+1 Close >= T Close:
     buy back ALL remaining SHORT calls. ATM + wings remain.

  5) TIME/EXPIRY:
     close all remaining legs by 30 calendar days / expiry.

All prices use historical option-chain bid/ask/mark. No synthetic option pricing,
no interpolation, no parameter fitting.
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
    RELEASE_REPO, RELEASE_TAG, CAPITAL_HKD, HKD_PER_USD, CAPITAL_USD,
    PCT_52W, DMA_EXT, COOLDOWN_DAYS, SHORT_DELTA, WING_DELTA,
    DTE_MIN, DTE_MAX, HOLD_MAX, RISK_PCT, APPROACH_FRAC,
    START_DATE, END_DATE,
    sha256_file, ensure_data, duck, load_underlying,
    build_selection_cache, fetch_all_quotes, q_at, executable, midpoint,
    max_loss_proxy, run_mode,
)

N_CAP = 4
DELTA_STEP = 0.15
DD_START = 0.25
HARVEST_FRACTION = 0.50


def fetch_quotes_delta(con, opt_path, selection):
    ids = sorted({
        str(legs[key]["contract_id"])
        for legs in selection.values()
        for key in ("atm", "short", "wing")
    })
    if not ids:
        return pd.DataFrame()
    rows = duck(con, """
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS contract_id,
               bid, ask, mark, delta
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """, [str(opt_path), ids, START_DATE.date(), END_DATE.date()])
    if rows.empty:
        return pd.DataFrame(columns=["bid","ask","mark","delta"])
    rows["date"] = pd.to_datetime(rows["date"])
    rows["contract_id"] = rows["contract_id"].astype(str)
    return rows.drop_duplicates(["date","contract_id"], keep="last").set_index(
        ["date","contract_id"]
    ).sort_index()


def choose_n0(legs, spot):
    budget = CAPITAL_USD * (RISK_PCT / 100.0)
    for n in range(N_CAP, 0, -1):
        ml = max_loss_proxy(legs, n, spot)
        if ml <= budget:
            return n, ml
    return 0, max_loss_proxy(legs, 1, spot)


def delta_target_n(n0, current_n, d):
    if pd.isna(d) or d <= SHORT_DELTA:
        return current_n
    reductions = int(math.floor((d - SHORT_DELTA) / DELTA_STEP + 1e-12))
    return max(0, min(current_n, n0 - reductions))


def downside_target_short(n0, current_short, loss_fraction):
    if loss_fraction < DD_START:
        return current_short
    # 25% risk consumed -> retain ~75% of N0; 50% -> ~50%; etc.
    target = int(math.ceil(n0 * max(0.0, 1.0 - loss_fraction)))
    return max(0, min(current_short, target))


def pair_close(quotes, dt, short_id, wing_id, count):
    if count <= 0:
        return None
    qs, qw = q_at(quotes, dt, short_id), q_at(quotes, dt, wing_id)
    bs, sw = executable(qs, "BUY"), executable(qw, "SELL")
    if pd.isna(bs) or pd.isna(sw):
        return None
    return (-count * bs + count * sw) * 100.0, bs, sw


def short_close(quotes, dt, short_id, count):
    if count <= 0:
        return None
    qs = q_at(quotes, dt, short_id)
    bs = executable(qs, "BUY")
    if pd.isna(bs):
        return None
    return (-count * bs) * 100.0, bs


def process_trade(und, quotes, entry_row, legs):
    entry = pd.Timestamp(entry_row["date"])
    spot = float(entry_row["close"])
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

    n0, initial_risk = choose_n0(legs, spot)
    if n0 <= 0:
        return None, "RISK_GATE"

    atm_id = str(legs["atm"]["contract_id"])
    short_id = str(legs["short"]["contract_id"])
    wing_id = str(legs["wing"]["contract_id"])

    qa0, qs0, qw0 = q_at(quotes, entry, atm_id), q_at(quotes, entry, short_id), q_at(quotes, entry, wing_id)
    if any(x is None for x in (qa0, qs0, qw0)):
        return None, "NO_ENTRY_QUOTES"

    atm_entry = executable(qa0, "BUY")
    short_entry = executable(qs0, "SELL")
    wing_entry = executable(qw0, "BUY")
    if any(pd.isna(x) for x in (atm_entry, short_entry, wing_entry)):
        return None, "NO_ENTRY_QUOTES"

    entry_cf = (atm_entry - n0 * short_entry + n0 * wing_entry) * 100.0
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

    exit_date = end_date
    exit_reason = "EXPIRY_OR_TIME"

    for i, row in daily.iterrows():
        dt = pd.Timestamp(row["date"])
        is_final = False

        # Path-state action first: next-day continuation/reversal.
        if pending is not None and pd.Timestamp(pending["date"]) == dt and n_short > 0:
            p = pending
            pending = None
            close_now = float(row["close"])
            qs = q_at(quotes, dt, short_id)
            buy_short = executable(qs, "BUY")
            if pd.notna(buy_short):
                if close_now >= float(p["approach_close"]):
                    before = n_short
                    cash += (-before * buy_short) * 100.0
                    n_short = 0
                    events.append({
                        "date": str(dt.date()),
                        "event": "BREAKOUT_CONTINUATION_REMOVE_ALL_SHORT",
                        "n_short_before": before,
                        "n_short_closed": before,
                        "n_short_after": 0,
                        "approach_date": str(p["approach_date"].date()),
                        "approach_close": float(p["approach_close"]),
                        "next_close": close_now,
                        "short_buyback_usd": buy_short * 100.0,
                    })
                elif buy_short <= HARVEST_FRACTION * short_entry:
                    h = int(math.ceil(n_short / 2.0))
                    before = n_short
                    cash += (-h * buy_short) * 100.0
                    n_short -= h
                    events.append({
                        "date": str(dt.date()),
                        "event": "PROFIT_HARVEST50_SHORT_ONLY",
                        "n_short_before": before,
                        "n_short_closed": h,
                        "n_short_after": n_short,
                        "approach_date": str(p["approach_date"].date()),
                        "approach_close": float(p["approach_close"]),
                        "next_close": close_now,
                        "short_entry_premium_usd": short_entry * 100.0,
                        "short_buyback_usd": buy_short * 100.0,
                    })
                else:
                    events.append({
                        "date": str(dt.date()),
                        "event": "REVERSAL_NO_50PCT_SHORT_RECOVERY",
                        "approach_date": str(p["approach_date"].date()),
                        "approach_close": float(p["approach_close"]),
                        "next_close": close_now,
                        "short_entry_premium_usd": short_entry * 100.0,
                        "actual_buyback_usd": buy_short * 100.0,
                    })
            approach_armed = False

        # Arm next-day path check.
        if pending is None and n_short > 0 and dt > entry:
            approach_now = float(row["high"]) >= APPROACH_FRAC * float(legs["short"]["strike"])
            if approach_now and approach_armed and i + 1 < len(daily):
                approach_armed = False
                pending = {
                    "date": pd.Timestamp(daily.iloc[i + 1]["date"]),
                    "approach_date": dt,
                    "approach_close": float(row["close"]),
                }
            elif not approach_now:
                approach_armed = True

        # Current mid-mark before today's governors.
        qa = q_at(quotes, dt, atm_id)
        qs = q_at(quotes, dt, short_id)
        qw = q_at(quotes, dt, wing_id)
        ma, ms, mw = midpoint(qa), midpoint(qs), midpoint(qw)
        package_pnl_mid = np.nan
        if all(pd.notna(x) for x in (ma, ms, mw)):
            package_pnl_mid = cash + ma * 100.0 - n_short * ms * 100.0 + n_pair * mw * 100.0

        # DOWN-side governor: recover profitable shorts only; NEVER sell wings.
        if n_short > 0 and not pd.isna(package_pnl_mid) and initial_risk > 0:
            loss_fraction = max(0.0, -package_pnl_mid) / initial_risk
            dd_target = downside_target_short(n0, n_short, loss_fraction)
            reduce_short = n_short - dd_target
            if reduce_short > 0:
                qs_now = q_at(quotes, dt, short_id)
                buy_short_now = executable(qs_now, "BUY")
                if pd.notna(buy_short_now) and buy_short_now <= short_entry:
                    before = n_short
                    cash += (-reduce_short * buy_short_now) * 100.0
                    n_short -= reduce_short
                    events.append({
                        "date": str(dt.date()),
                        "event": "DD_PROFIT_RECOVER_SHORT_ONLY",
                        "package_pnl_mid_usd": package_pnl_mid,
                        "initial_risk_usd": initial_risk,
                        "loss_fraction_of_risk": loss_fraction,
                        "n_short_before": before,
                        "n_short_closed": reduce_short,
                        "n_short_after": n_short,
                        "short_buyback_usd": buy_short_now * 100.0,
                    })
                else:
                    events.append({
                        "date": str(dt.date()),
                        "event": "DD_SHORT_RECOVERY_BLOCKED_NOT_PROFITABLE",
                        "package_pnl_mid_usd": package_pnl_mid,
                        "initial_risk_usd": initial_risk,
                        "loss_fraction_of_risk": loss_fraction,
                        "requested_short_reduction": reduce_short,
                        "short_buyback_usd": None if pd.isna(buy_short_now) else buy_short_now * 100.0,
                    })

        # UP-side governor: reduce only structural pair units.
        if n_pair > 0 and n_short > 0:
            try:
                d = float(quotes.loc[(dt, short_id)]["delta"])
            except Exception:
                d = np.nan
            d_target = delta_target_n(n0, n_pair, d)
            target = min(n_pair, n_short, d_target)
            if target < n_pair:
                reduce_by = n_pair - target
                res = pair_close(quotes, dt, short_id, wing_id, reduce_by)
                if res is not None:
                    cf, buy_short_now, sell_wing_now = res
                    before = n_pair
                    cash += cf
                    n_pair = target
                    n_short = min(n_short, n_pair)
                    events.append({
                        "date": str(dt.date()),
                        "event": "DELTA_REDUCE_PAIR",
                        "short_delta": d,
                        "n_pair_before": before,
                        "n_pair_closed": reduce_by,
                        "n_pair_after": n_pair,
                        "n_short_after": n_short,
                        "short_buyback_usd": buy_short_now * 100.0,
                        "wing_sale_usd": sell_wing_now * 100.0,
                    })

        # Final daily mark after management.
        qa = q_at(quotes, dt, atm_id)
        qs = q_at(quotes, dt, short_id)
        qw = q_at(quotes, dt, wing_id)
        ma, ms, mw = midpoint(qa), midpoint(qs), midpoint(qw)
        if all(pd.notna(x) for x in (ma, ms, mw)):
            eq_rows.append((dt, CAPITAL_USD + cash + ma * 100.0 - n_short * ms * 100.0 + n_pair * mw * 100.0))

        if dt >= end_date:
            is_final = True
        if is_final:
            break

    qxa, qxs, qxw = q_at(quotes, exit_date, atm_id), q_at(quotes, exit_date, short_id), q_at(quotes, exit_date, wing_id)
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
        qxa, qxs, qxw = q_at(quotes, exit_date, atm_id), q_at(quotes, exit_date, short_id), q_at(quotes, exit_date, wing_id)

    sa, bs, sw = executable(qxa, "SELL"), executable(qxs, "BUY"), executable(qxw, "SELL")
    if any(pd.isna(x) for x in (sa, bs, sw)):
        return None, "NO_EXIT_QUOTES"

    exit_cf = (sa - n_short * bs + n_pair * sw) * 100.0
    pnl = cash + exit_cf
    eq_rows.append((pd.Timestamp(exit_date), CAPITAL_USD + pnl))

    return {
        "entry": entry,
        "exit": pd.Timestamp(exit_date),
        "reason": exit_reason,
        "n_initial": int(n0),
        "n_pair_final": int(n_pair),
        "n_short_final": int(n_short),
        "n_wing_final": int(n_pair),
        "atm_strike": float(legs["atm"]["strike"]),
        "short_strike": float(legs["short"]["strike"]),
        "wing_strike": float(legs["wing"]["strike"]),
        "entry_cashflow_usd": float(entry_cf),
        "pnl_usd": float(pnl),
        "max_loss_proxy_usd": float(initial_risk),
        "extension": float(entry_row["ext200"]),
        "ratio52": float(entry_row["ratio52"]),
        "harvest_events": int(sum(e["event"] == "PROFIT_HARVEST50_SHORT_ONLY" for e in events)),
        "continuation_events": int(sum(e["event"] == "BREAKOUT_CONTINUATION_REMOVE_ALL_SHORT" for e in events)),
        "dd_short_recover_events": int(sum(e["event"] == "DD_PROFIT_RECOVER_SHORT_ONLY" for e in events)),
        "delta_pair_reduce_events": int(sum(e["event"] == "DELTA_REDUCE_PAIR" for e in events)),
        "events": events,
        "eq_rows": eq_rows,
    }, "OK"


def run_dynamic(und, quotes, selection):
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
        tr, status = process_trade(und, quotes, row, legs)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue
        trades.append(tr)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [], {"mode":"DYNAMIC_N_V3_ASYMMETRIC","trades":0,"rejections":rejects}, pd.DataFrame()

    trdf = pd.DataFrame([{k:v for k,v in t.items() if k not in ("events","eq_rows")} for t in trades]).sort_values("entry").reset_index(drop=True)
    points = [p for t in trades for p in t["eq_rows"]]
    eqdf = pd.DataFrame(points, columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"] = eqdf["equity"].cummax()
    eqdf["dd"] = eqdf["equity"] / eqdf["peak"] - 1.0

    end_equity = CAPITAL_USD + trdf["pnl_usd"].sum()
    years = max((trdf["exit"].iloc[-1] - trdf["entry"].iloc[0]).days / 365.25, 1/365.25)
    total_return = end_equity / CAPITAL_USD - 1.0
    cagr = (1.0 + total_return)**(1.0/years) - 1.0 if total_return > -1.0 else -1.0

    stats = {
        "mode":"DYNAMIC_N_V3_ASYMMETRIC",
        "N_cap":N_CAP,
        "trades":int(len(trdf)),
        "win_rate":float((trdf["pnl_usd"] > 0).mean()),
        "avg_trade_usd":float(trdf["pnl_usd"].mean()),
        "worst_trade_usd":float(trdf["pnl_usd"].min()),
        "best_trade_usd":float(trdf["pnl_usd"].max()),
        "total_return":float(total_return),
        "cagr":float(cagr),
        "maxdd_daily_mtm":float(eqdf["dd"].min()),
        "maxdd_realized":float(
            (trdf["pnl_usd"].cumsum().add(CAPITAL_USD).div(
                trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax()
            ) - 1.0).min()
        ),
        "years":float(years),
        "harvest_events":int(trdf["harvest_events"].sum()),
        "continuation_events":int(trdf["continuation_events"].sum()),
        "dd_short_recover_events":int(trdf["dd_short_recover_events"].sum()),
        "delta_pair_reduce_events":int(trdf["delta_pair_reduce_events"].sum()),
        "avg_n_initial":float(trdf["n_initial"].mean()),
        "n_initial_counts":trdf["n_initial"].value_counts().sort_index().to_dict(),
        "rejections":rejects,
        "data_start":str(trdf["entry"].min().date()),
        "data_end":str(trdf["exit"].max().date()),
    }
    return trades, stats, eqdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    opt_path, und_path = ensure_data(Path(args.data_dir))
    und = load_underlying(und_path)

    signal_dates = [pd.Timestamp(x) for x in und.loc[und["signal"], "date"].tolist()]
    con = duckdb.connect()
    selection, selection_rejects = build_selection_cache(con, opt_path, signal_dates)
    quotes_dynamic = fetch_quotes_delta(con, opt_path, selection)
    quotes_baseline = fetch_all_quotes(con, opt_path, selection)

    _, b2, _ = run_mode(und, quotes_baseline, selection, 2, "BASELINE_TOUCH")
    _, b3, _ = run_mode(und, quotes_baseline, selection, 3, "BASELINE_TOUCH")
    _, b4, _ = run_mode(und, quotes_baseline, selection, 4, "BASELINE_TOUCH")
    trades, dyn, eqdf = run_dynamic(und, quotes_dynamic, selection)

    results = [b2, b3, b4, dyn]
    pd.DataFrame([{
        **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
        "events_json": json.dumps(t["events"], ensure_ascii=False)
    } for t in trades]).to_csv(out / "trades_DYNAMIC_N_V3_ASYMMETRIC.csv", index=False)
    if not eqdf.empty:
        eqdf.to_csv(out / "equity_DYNAMIC_N_V3_ASYMMETRIC.csv", index=False)

    report = {
        "research_contract":{
            "strategy":"1 ATM Long Call + N OTM Short Calls + N Far OTM Long Wings",
            "entry_N_rule":"largest N in {1,2,3,4} with initial max-loss proxy <= 2% NAV",
            "upside_governor":"short delta +0.15 steps above 0.20 remove one SHORT+WING pair",
            "downside_governor":"package MTM loss / initial risk; from 25% risk consumption, target SHORT count scales down; close SHORT only when buyback Ask <= entry SHORT Bid; NEVER sell wing in this governor",
            "profit_recovery":"approach High >= 98% short strike; next Close < approach Close; buyback Ask <= 50% entry premium; close ceil(N_short/2) SHORT only",
            "breakout_continuation":"approach then next Close >= approach Close; remove all remaining SHORT",
            "hold_max_days":HOLD_MAX,
            "DTE":[DTE_MIN,DTE_MAX],
            "entry_execution":"ATM buy Ask; short sell Bid; wing buy Ask",
            "management_execution":"short buyback Ask; wing sale Bid when pair reduction is required",
            "daily_mark":"Mid",
            "strict_quote_policy":"no interpolation; missing entry/exit rejects; missing management quote blocks action",
            "no_optimization":True,
        },
        "data":{
            "source_repo":RELEASE_REPO,
            "release_tag":RELEASE_TAG,
            "options_sha256":sha256_file(opt_path),
            "underlying_sha256":sha256_file(und_path),
            "underlying_range":[str(und["date"].min().date()),str(und["date"].max().date())],
            "selection_cache":len(selection),
            "selection_rejects":selection_rejects,
        },
        "results":results
    }
    (out/"ratio_call_dynamic_n_v3_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_dynamic_n_v3_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__ == "__main__":
    main()
