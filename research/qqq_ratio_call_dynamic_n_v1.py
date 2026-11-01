#!/usr/bin/env python3
"""QQQ Ratio-Call Dynamic-N V1 — frozen research replay.

Structure:
  +1 ATM long call - N short OTM calls + N farther OTM long call wings.

Management state machine:
  A. N-risk governor (monotone down):
       short delta >= 0.35 -> N_pair <= 3
       short delta >= 0.50 -> N_pair <= 2
       short delta >= 0.65 -> N_pair <= 1
       short delta >= 0.80 -> N_pair <= 0
     Each reduction closes one short+one wing pair at executable quotes.
     Thresholds are fixed increments of +0.15 from the entry target delta 0.20,
     not fitted to returns. N never increases inside a trade.

  B. Profit recovery:
       if High >= 0.98 * short_strike on T, arm T+1.
       if T+1 Close < T Close AND short buyback Ask <= 50% of entry
       short sale Bid, close ceil(N_short/2) SHORT calls only.
       All wings and the ATM long remain.

  C. Breakout continuation governor:
       if T+1 Close >= T Close after the same approach event,
       buy back ALL remaining SHORT calls. Keep all wings + ATM long.

  D. Exit remaining legs after 30 calendar days or expiry.

No parameter optimization. No synthetic option pricing. No interpolation.
Entry: ATM buy Ask; shorts sell Bid; wings buy Ask.
Management: short buyback Ask; wing sale Bid.
Daily mark: Mid.
Risk gate: initial package max-loss proxy <= 2% of starting NAV.
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
    build_selection_cache, fetch_all_quotes,
    q_at, executable, midpoint, max_loss_proxy, run_mode,
)

N_MAX = 4
DELTA_STEP = 0.15
DELTA_THRESHOLDS = {
    3: SHORT_DELTA + DELTA_STEP,       # 0.35
    2: SHORT_DELTA + 2 * DELTA_STEP,   # 0.50
    1: SHORT_DELTA + 3 * DELTA_STEP,   # 0.65
    0: SHORT_DELTA + 4 * DELTA_STEP,   # 0.80
}
HARVEST_FRACTION = 0.50


def fetch_quotes_with_delta(con, opt_path, selection):
    ids = sorted({
        str(legs[key]["contract_id"])
        for legs in selection.values()
        for key in ("atm", "short", "wing")
    })
    if not ids:
        return pd.DataFrame()
    rows = duck(con, """
        SELECT
            CAST(date AS DATE) AS date,
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
    rows = rows.drop_duplicates(["date","contract_id"], keep="last")
    return rows.set_index(["date","contract_id"]).sort_index()


def execute_pair_reduce(quotes, dt, short_id, wing_id, count):
    qs = q_at(quotes, dt, short_id)
    qw = q_at(quotes, dt, wing_id)
    bs = executable(qs, "BUY")
    sw = executable(qw, "SELL")
    if pd.isna(bs) or pd.isna(sw):
        return None
    return (-count * bs + count * sw) * 100.0, bs, sw


def delta_at(quotes, dt, cid):
    try:
        r = quotes.loc[(pd.Timestamp(dt), str(cid))]
    except KeyError:
        return np.nan
    try:
        return float(r["delta"])
    except Exception:
        return np.nan


def process_dynamic(und, quotes, entry_row, legs):
    entry = pd.Timestamp(entry_row["date"])
    spot = float(entry_row["close"])
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

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

    ml = max_loss_proxy(legs, N_MAX, spot)
    if ml > CAPITAL_USD * (RISK_PCT / 100.0):
        return None, "RISK_GATE"

    entry_cf = (atm_entry - N_MAX * short_entry + N_MAX * wing_entry) * 100.0
    cash = -entry_cf

    # The structural pair count controls the short+wing ratio.
    n_pair = N_MAX
    # Short-only harvest can reduce shorts below the wing count.
    n_short = N_MAX

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

        # 1) Execute the already-observed T -> T+1 path decision.
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
                        "approach_date": str(p["approach_date"].date()),
                        "approach_close": float(p["approach_close"]),
                        "next_close": close_now,
                        "n_short_before": before,
                        "n_short_closed": before,
                        "n_short_after": 0,
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
                        "approach_date": str(p["approach_date"].date()),
                        "approach_close": float(p["approach_close"]),
                        "next_close": close_now,
                        "n_short_before": before,
                        "n_short_closed": h,
                        "n_short_after": n_short,
                        "harvest_fraction": h / before,
                        "short_entry_premium_usd": short_entry * 100.0,
                        "harvest_threshold_usd": short_entry * HARVEST_FRACTION * 100.0,
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
                        "required_buyback_max_usd": short_entry * HARVEST_FRACTION * 100.0,
                        "actual_buyback_usd": buy_short * 100.0,
                    })

        # 2) Arm the next-day path check from the daily High.
        if pending is None and n_short > 0 and dt > entry:
            high = float(row["high"])
            approach_now = high >= APPROACH_FRAC * float(legs["short"]["strike"])
            if approach_now and approach_armed and i + 1 < len(daily):
                approach_armed = False
                pending = {
                    "date": pd.Timestamp(daily.iloc[i + 1]["date"]),
                    "approach_date": dt,
                    "approach_close": float(row["close"]),
                }
            elif not approach_now:
                approach_armed = True

        # 3) N-risk governor: reduce pair count monotonically with short delta.
        d = delta_at(quotes, dt, short_id)
        if n_pair > 0 and not pd.isna(d):
            target = n_pair
            for candidate_n in range(n_pair - 1, -1, -1):
                if d >= DELTA_THRESHOLDS[candidate_n]:
                    target = candidate_n
                else:
                    break
            if target < n_pair:
                reduce_by = n_pair - target
                res = execute_pair_reduce(quotes, dt, short_id, wing_id, reduce_by)
                if res is not None:
                    cf, buy_short_now, sell_wing_now = res
                    cash += cf
                    before_pair = n_pair
                    n_pair = target
                    n_short = min(n_short, n_pair)
                    events.append({
                        "date": str(dt.date()),
                        "event": "DELTA_N_REDUCE_PAIR",
                        "short_delta": d,
                        "n_pair_before": before_pair,
                        "n_pair_closed": reduce_by,
                        "n_pair_after": n_pair,
                        "n_short_after": n_short,
                        "short_buyback_usd": buy_short_now * 100.0,
                        "wing_sale_usd": sell_wing_now * 100.0,
                    })
                else:
                    events.append({
                        "date": str(dt.date()),
                        "event": "DELTA_N_REDUCE_BLOCKED_NO_QUOTES",
                        "short_delta": d,
                        "n_pair_before": n_pair,
                        "requested_n_pair_after": target,
                    })
        elif n_pair > 0 and pd.isna(d):
            events.append({
                "date": str(dt.date()),
                "event": "DELTA_MISSING_NO_N_CHANGE",
            })

        if dt >= end_date:
            is_final = True

        # Daily marked equity; no interpolation.
        qa = q_at(quotes, dt, atm_id)
        qs = q_at(quotes, dt, short_id)
        qw = q_at(quotes, dt, wing_id)
        ma, ms, mw = midpoint(qa), midpoint(qs), midpoint(qw)
        if not any(pd.isna(x) for x in (ma, ms, mw)):
            eq = CAPITAL_USD + cash + ma * 100.0 - n_short * ms * 100.0 + n_pair * mw * 100.0
            eq_rows.append((dt, eq))

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

    sa = executable(qxa, "SELL")
    bs = executable(qxs, "BUY")
    sw = executable(qxw, "SELL")
    if any(pd.isna(x) for x in (sa, bs, sw)):
        return None, "NO_EXIT_QUOTES"

    exit_cf = (sa - n_short * bs + n_pair * sw) * 100.0
    pnl = cash + exit_cf
    eq_rows.append((pd.Timestamp(exit_date), CAPITAL_USD + pnl))

    return {
        "entry": entry,
        "exit": pd.Timestamp(exit_date),
        "reason": exit_reason,
        "n_initial": N_MAX,
        "n_pair_final": int(n_pair),
        "n_short_final": int(n_short),
        "n_wing_final": int(n_pair),
        "atm_strike": float(legs["atm"]["strike"]),
        "short_strike": float(legs["short"]["strike"]),
        "wing_strike": float(legs["wing"]["strike"]),
        "entry_cashflow_usd": float(entry_cf),
        "pnl_usd": float(pnl),
        "max_loss_proxy_usd": float(ml),
        "extension": float(entry_row["ext200"]),
        "ratio52": float(entry_row["ratio52"]),
        "expiry": expiry,
        "harvest_events": int(sum(e["event"] == "PROFIT_HARVEST50_SHORT_ONLY" for e in events)),
        "continuation_events": int(sum(e["event"] == "BREAKOUT_CONTINUATION_REMOVE_ALL_SHORT" for e in events)),
        "delta_reduce_events": int(sum(e["event"] == "DELTA_N_REDUCE_PAIR" for e in events)),
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
        tr, status = process_dynamic(und, quotes, row, legs)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue
        trades.append(tr)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return trades, {"mode":"DYNAMIC_N_V1","trades":0,"rejections":rejects}, pd.DataFrame()

    trdf = pd.DataFrame([{k:v for k,v in t.items() if k not in ("events","eq_rows")} for t in trades]).sort_values("entry").reset_index(drop=True)
    points = [p for t in trades for p in t["eq_rows"]]
    eqdf = pd.DataFrame(points, columns=["date","equity"]).groupby("date",as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"] = eqdf["equity"].cummax()
    eqdf["dd"] = eqdf["equity"]/eqdf["peak"] - 1.0

    end_equity = CAPITAL_USD + trdf["pnl_usd"].sum()
    years = max((trdf["exit"].iloc[-1] - trdf["entry"].iloc[0]).days / 365.25, 1/365.25)
    total_return = end_equity / CAPITAL_USD - 1.0
    cagr = (1.0 + total_return)**(1.0/years) - 1.0 if total_return > -1.0 else -1.0

    stats = {
        "mode":"DYNAMIC_N_V1",
        "N_max":N_MAX,
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
        "delta_reduce_events":int(trdf["delta_reduce_events"].sum()),
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

    data_dir = Path(args.data_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    opt_path, und_path = ensure_data(data_dir)
    und = load_underlying(und_path)

    dates = [pd.Timestamp(x) for x in und.loc[und["signal"], "date"].tolist()]
    con = duckdb.connect()
    selection, selection_rejects = build_selection_cache(con, opt_path, dates)
    quotes_dynamic = fetch_quotes_with_delta(con, opt_path, selection)
    quotes_baseline = fetch_all_quotes(con, opt_path, selection)

    _, base2, _ = run_mode(und, quotes_baseline, selection, 2, "BASELINE_TOUCH")
    _, base3, _ = run_mode(und, quotes_baseline, selection, 3, "BASELINE_TOUCH")
    _, base4, _ = run_mode(und, quotes_baseline, selection, 4, "BASELINE_TOUCH")
    trades, dyn, eqdf = run_dynamic(und, quotes_dynamic, selection)

    results = [base2, base3, base4, dyn]
    for tname in ("N4_DYNAMIC",):
        pd.DataFrame([{
            **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
            "events_json": json.dumps(t["events"], ensure_ascii=False)
        } for t in trades]).to_csv(out / f"trades_{tname}.csv", index=False)
    if not eqdf.empty:
        eqdf.to_csv(out / "equity_N4_DYNAMIC.csv", index=False)

    report = {
        "research_contract": {
            "strategy":"1 ATM Long Call + N OTM Short Calls + N Far OTM Long Wings",
            "N_max":N_MAX,
            "entry_signal":"QQQ close / 52-week high >= 0.98 AND close / 200DMA - 1 >= 0.08",
            "N_delta_governor":"monotone down; thresholds 0.35, 0.50, 0.65, 0.80 map N_pair to 3,2,1,0; +0.15 increments from entry short delta 0.20",
            "profit_recovery":"approach High >= 98% short strike; next Close < approach Close; short buyback Ask <= 50% of entry short sale Bid; close ceil(N_short/2) shorts only",
            "breakout_continuation":"approach High >= 98% short strike; next Close >= approach Close; close all remaining shorts",
            "wings_after_short_harvest":"remain open",
            "DTE":[DTE_MIN,DTE_MAX],
            "hold_max_days":HOLD_MAX,
            "risk_gate":f"initial N={N_MAX} package terminal-payoff max-loss proxy <= {RISK_PCT:.2f}% NAV",
            "entry_execution":"ATM buy Ask; short sell Bid; wing buy Ask",
            "management_execution":"short buyback Ask; wing sale Bid",
            "daily_mark":"Mid",
            "strict_quote_policy":"no interpolation; missing entry/exit quotes reject trade; missing management quote blocks that action and logs it",
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
    (out/"ratio_call_dynamic_n_v1_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_dynamic_n_v1_summary.csv",index=False)
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__ == "__main__":
    main()
