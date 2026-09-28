#!/usr/bin/env python3
"""
QQQ Ratio-Call Harvest V1
-------------------------
Research-only, frozen-rule comparison:
  BASELINE_TOUCH:
    +1 ATM call - N x OTM short call + N x farther OTM long wings.
    Exit whole package on first post-entry day whose underlying High touches
    the short strike, otherwise exit at time/expiry.

  HARVEST50_REVERSAL:
    Same exact entry/contract-selection/risk gate.
    Do NOT exit on short-strike touch.
    If an approach event occurs (High >= 98% of short strike after being below)
    and the NEXT trading day's Close is lower than the approach day's Close,
    close at least half of the remaining short+wing pairs using executable
    quotes (buy short at Ask, sell wing at Bid). Keep the ATM long.
    Repeat on later fresh approach/reversal events.
    Final exit at time/expiry.

No parameter search or optimization is performed.
Data: canonical data-v1 release from lambdaclass/options_portfolio_backtester.
QQQ chain: 2011-03-23 through 2025-12-16 (dataset coverage).
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RELEASE_REPO = "lambdaclass/options_portfolio_backtester"
RELEASE_TAG = "data-v1"

CAPITAL_HKD = 500_000.0
HKD_PER_USD = 7.8
CAPITAL_USD = CAPITAL_HKD / HKD_PER_USD
RISK_PCT = 2.0

PCT_52W = 0.98
DMA_EXT = 0.08
COOLDOWN_DAYS = 10

SHORT_DELTA = 0.20
WING_DELTA = 0.08
DTE_MIN = 18
DTE_MAX = 35
HOLD_MAX = 30

APPROACH_FRAC = 0.98
STRICT_QUOTES = True

START_DATE = pd.Timestamp("2011-01-01")
END_DATE = pd.Timestamp("2025-12-31")

@dataclass
class Position:
    entry_date: pd.Timestamp
    end_date: pd.Timestamp
    expiry: pd.Timestamp
    atm_id: str
    short_id: str
    wing_id: str
    atm_k: float
    short_k: float
    wing_k: float
    n_initial: int
    n_remaining: int
    cash: float
    entry_cashflow: float
    harvest_count: int = 0
    realized_harvest_pnl: float = 0.0
    approach_armed: bool = True
    last_approach_close: float | None = None
    last_approach_date: pd.Timestamp | None = None

def run_cmd(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_data(data_dir: Path):
    data_dir.mkdir(parents=True, exist_ok=True)
    opt = data_dir / "QQQ_options.parquet"
    und = data_dir / "QQQ_underlying.parquet"
    if not opt.exists() or not und.exists():
        run_cmd([
            "gh","release","download",RELEASE_TAG,"--repo",RELEASE_REPO,
            "--pattern","QQQ_options.parquet","--pattern","QQQ_underlying.parquet",
            "--dir",str(data_dir),
        ])
    return opt, und

def load_underlying(path: Path):
    df = pd.read_parquet(path)
    df.columns = [c.lower() for c in df.columns]
    dcol = "date" if "date" in df.columns else "datetime"
    df["date"] = pd.to_datetime(df[dcol]).dt.tz_localize(None).dt.normalize()
    df = df.sort_values("date").drop_duplicates("date")
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)].copy()
    for c in ["open","high","low","close"]:
        if c not in df.columns:
            raise ValueError(f"Missing underlying field: {c}")
    df["dma200"] = df["close"].rolling(200, min_periods=200).mean()
    df["high52w"] = df["close"].rolling(252, min_periods=252).max()
    df["ext200"] = df["close"] / df["dma200"] - 1.0
    df["ratio52"] = df["close"] / df["high52w"]
    df["signal"] = (df["ratio52"] >= PCT_52W) & (df["ext200"] >= DMA_EXT)
    return df[["date","open","high","low","close","dma200","high52w","ext200","ratio52","signal"]].reset_index(drop=True)

def duck(con, sql, params=None):
    return con.execute(sql, params or {}).df()

def pick_legs(con, opt_path: Path, entry_date, spot):
    lo = entry_date + pd.Timedelta(days=DTE_MIN)
    hi = entry_date + pd.Timedelta(days=DTE_MAX)
    rows = duck(con, f"""
        SELECT contract_id, expiration, strike, type, bid, ask, mark, volume,
               open_interest, implied_volatility, delta
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) = ?
          AND upper(type) = 'CALL'
          AND CAST(expiration AS DATE) BETWEEN ? AND ?
          AND delta IS NOT NULL
          AND bid IS NOT NULL AND ask IS NOT NULL
    """, [str(opt_path), entry_date.date(), lo.date(), hi.date()])
    if rows.empty:
        return None
    rows["expiration"] = pd.to_datetime(rows["expiration"])
    rows["dte"] = (rows["expiration"] - entry_date).dt.days
    exp = rows.sort_values(["dte","volume"], ascending=[True, False]).iloc[0]["expiration"]
    chain = rows[rows["expiration"] == exp].copy()
    if chain.empty:
        return None

    atm = chain.iloc[(chain["delta"] - 0.50).abs().argsort()[:1]].iloc[0]
    short_pool = chain[chain["strike"] > atm["strike"]].copy()
    if short_pool.empty:
        return None
    short_pool["d_err"] = (short_pool["delta"] - SHORT_DELTA).abs()
    short_rows = short_pool.sort_values(["d_err","strike"]).head(1)
    if short_rows.empty:
        return None
    short = short_rows.iloc[0]

    wing_pool = chain[chain["strike"] > float(short["strike"])].copy()
    if wing_pool.empty:
        return None
    wing_pool["d_err"] = (wing_pool["delta"] - WING_DELTA).abs()
    wing = wing_pool.sort_values(["d_err","strike"]).head(1)
    if wing.empty:
        return None
    wing = wing.iloc[0]

    return {
        "expiry": pd.Timestamp(atm["expiration"]),
        "atm": atm.to_dict(),
        "short": short.to_dict(),
        "wing": wing.to_dict(),
    }

def quote_map(con, opt_path: Path, ids, start_date, end_date):
    ph = ",".join(["?"] * len(ids))
    return duck(con, f"""
        SELECT CAST(date AS DATE) AS date, contract_id, bid, ask, mark
        FROM read_parquet(?)
        WHERE contract_id IN ({ph})
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """, [str(opt_path), *ids, start_date.date(), end_date.date()])

def make_pivot(quotes):
    if quotes.empty:
        return None
    quotes["date"] = pd.to_datetime(quotes["date"])
    return quotes.pivot_table(index="date", columns="contract_id",
                              values=["bid","ask","mark"], aggfunc="last").sort_index()

def leg_quote(pivot, cid, dt):
    if pivot is None or dt not in pivot.index:
        return None
    r = pivot.loc[dt]
    out = {}
    for c in ["bid","ask","mark"]:
        try:
            out[c] = float(r[(c,cid)])
        except Exception:
            out[c] = np.nan
    return out

def exec_px(q, side):
    b, a = q["bid"], q["ask"]
    if pd.isna(b) or pd.isna(a):
        return np.nan
    return float(a if side == "BUY" else b)

def mid_px(q):
    if q is None:
        return np.nan
    if pd.notna(q["bid"]) and pd.notna(q["ask"]):
        return (float(q["bid"]) + float(q["ask"])) / 2.0
    if pd.notna(q["mark"]):
        return float(q["mark"])
    return np.nan

def max_loss_proxy(legs, n, spot):
    atm_k = float(legs["atm"]["strike"])
    short_k = float(legs["short"]["strike"])
    wing_k = float(legs["wing"]["strike"])
    grid = np.linspace(max(1.0, spot*0.20), max(spot*2.5, wing_k*1.25), 500)
    # Actual execution-style initial cashflow: ATM buy at ask,
    # short sell at bid, wing buy at ask.
    premium = (
        float(legs["atm"]["ask"])
        - n*float(legs["short"]["bid"])
        + n*float(legs["wing"]["ask"])
    ) * 100.0
    payoff = (
        np.maximum(grid-atm_k, 0)
        - n*np.maximum(grid-short_k, 0)
        + n*np.maximum(grid-wing_k, 0)
    ) * 100.0
    terminal = payoff - premium
    return max(0.0, -float(np.min(terminal)))

def select_n(n_fixed):
    return int(n_fixed)

def entry_trade(con, opt_path, srow, n_fixed):
    entry = pd.Timestamp(srow["date"])
    spot = float(srow["close"])
    legs = pick_legs(con, opt_path, entry, spot)
    if legs is None:
        return None, "NO_LEGS"
    ml = max_loss_proxy(legs, n_fixed, spot)
    if ml > CAPITAL_USD * (RISK_PCT/100.0):
        return None, "RISK_GATE"
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)
    ids = [legs["atm"]["contract_id"], legs["short"]["contract_id"], legs["wing"]["contract_id"]]
    q = quote_map(con, opt_path, ids, entry, end_date)
    pivot = make_pivot(q)
    if entry not in pivot.index:
        return None, "NO_ENTRY_QUOTES"
    qa = leg_quote(pivot, ids[0], entry)
    qs = leg_quote(pivot, ids[1], entry)
    qw = leg_quote(pivot, ids[2], entry)
    if any(x is None for x in (qa,qs,qw)):
        return None, "NO_ENTRY_QUOTES"
    buy_atm = exec_px(qa, "BUY")
    sell_short = exec_px(qs, "SELL")
    buy_wing = exec_px(qw, "BUY")
    if any(pd.isna(x) for x in (buy_atm,sell_short,buy_wing)):
        return None, "NO_ENTRY_QUOTES"
    entry_cf = (buy_atm - n_fixed*sell_short + n_fixed*buy_wing) * 100.0
    pos = Position(
        entry_date=entry, end_date=end_date, expiry=expiry,
        atm_id=ids[0], short_id=ids[1], wing_id=ids[2],
        atm_k=float(legs["atm"]["strike"]),
        short_k=float(legs["short"]["strike"]),
        wing_k=float(legs["wing"]["strike"]),
        n_initial=n_fixed, n_remaining=n_fixed,
        cash=-entry_cf, entry_cashflow=entry_cf
    )
    return (pos, pivot, ml, legs), "OK"

def terminal_close(pos, pivot, dt):
    qa = leg_quote(pivot, pos.atm_id, dt)
    qs = leg_quote(pivot, pos.short_id, dt)
    qw = leg_quote(pivot, pos.wing_id, dt)
    if any(x is None for x in (qa,qs,qw)):
        return None
    sa = exec_px(qa, "SELL")
    bs = exec_px(qs, "BUY")
    sw = exec_px(qw, "SELL")
    if any(pd.isna(x) for x in (sa,bs,sw)):
        return None
    cf = (sa - pos.n_remaining*bs + pos.n_remaining*sw) * 100.0
    return cf

def pair_close_cost(pivot, pos, dt):
    qs = leg_quote(pivot, pos.short_id, dt)
    qw = leg_quote(pivot, pos.wing_id, dt)
    if any(x is None for x in (qs,qw)):
        return np.nan
    bs = exec_px(qs, "BUY")
    sw = exec_px(qw, "SELL")
    if pd.isna(bs) or pd.isna(sw):
        return np.nan
    return bs - sw

def pair_open_profit(pivot, pos, dt):
    # Per pair profit using executable entry prices and executable close prices.
    entry_pair_credit = (
        pos.entry_cashflow/100.0 + float(legs_cache[pos.entry_date]["atm_entry_cost"])
    ) / (-pos.n_initial) if False else None
    # Actual pair basis from stored values:
    return float(pair_entry_credit_cache[pos.entry_date] - pair_close_cost(pivot, pos, dt))

def daily_equity_for_trade(pos, pivot, und_slice, mode, trade_logs):
    # Build daily mark-to-mid path and execute harvest/exit events.
    # The outer caller supplies a mutable event log.
    dates = list(und_slice["date"])
    cash = pos.cash
    n = pos.n_remaining
    # Entry-side per-pair credit is stored in trade_logs metadata.
    entry_pair_credit = trade_logs["_entry_pair_credit"]

    realized_harvest = 0.0
    exit_date = pos.end_date
    exit_reason = "EXPIRY_OR_TIME"

    eq_rows = []

    for i, dt in enumerate(dates):
        dt = pd.Timestamp(dt)
        qa = leg_quote(pivot, pos.atm_id, dt)
        qs = leg_quote(pivot, pos.short_id, dt)
        qw = leg_quote(pivot, pos.wing_id, dt)
        if dt == pos.entry_date:
            pass

        # New rule: approach edge today, check next day's Close.
        if mode == "HARVEST50_REVERSAL" and dt > pos.entry_date and i+1 < len(dates):
            high = float(und_slice.iloc[i]["high"])
            close = float(und_slice.iloc[i]["close"])
            approach_now = high >= APPROACH_FRAC * pos.short_k
            approach_edge = approach_now and (not pos.approach_armed)
            if approach_now and pos.approach_armed:
                pos.approach_armed = False
                pos.last_approach_close = close
                pos.last_approach_date = dt
            elif (not approach_now) and not pos.approach_armed:
                pos.approach_armed = True

            if pos.last_approach_date is not None and dt == pos.last_approach_date:
                # evaluate tomorrow
                tomorrow = pd.Timestamp(dates[i+1])
                if tomorrow > dt:
                    tomorrow_close = float(und_slice.iloc[i+1]["close"])
                    if tomorrow_close < close and n > 0:
                        cst = pair_close_cost(pivot, pos, tomorrow)
                        if pd.notna(cst):
                            pair_profit = entry_pair_credit - cst
                            if pair_profit > 0:
                                h = int(math.ceil(n / 2.0))
                                qs2 = leg_quote(pivot, pos.short_id, tomorrow)
                                qw2 = leg_quote(pivot, pos.wing_id, tomorrow)
                                bs2 = exec_px(qs2, "BUY") if qs2 else np.nan
                                sw2 = exec_px(qw2, "SELL") if qw2 else np.nan
                                if pd.notna(bs2) and pd.notna(sw2):
                                    cf = h*(bs2*-1.0 + sw2)*100.0
                                    # Positive/negative cash flow correctly reflects closing:
                                    # buy short costs -h*ask; sell wing yields +h*bid.
                                    cash += cf
                                    realized_harvest += h*pair_profit*100.0
                                    trade_logs["events"].append({
                                        "date": str(tomorrow.date()),
                                        "event": "HARVEST50_REVERSAL",
                                        "n_before": int(n),
                                        "n_closed": int(h),
                                        "n_after": int(n-h),
                                        "approach_date": str(dt.date()),
                                        "approach_close": close,
                                        "reversal_close": tomorrow_close,
                                        "pair_profit_executable": pair_profit,
                                        "realized_pair_pnl_est": h*pair_profit*100.0,
                                    })
                                    n -= h
                                    pos.n_remaining = n
                                    pos.harvest_count += 1
                                    pos.realized_harvest_pnl += h*pair_profit*100.0
                                    pos.last_approach_date = None
                                    pos.last_approach_close = None
                                    # Prevent immediate re-arm until a subsequent away day.
                                    pos.approach_armed = False

        # Baseline touch exit, checked after entry.
        if mode == "BASELINE_TOUCH" and dt > pos.entry_date:
            if float(und_slice.iloc[i]["high"]) >= pos.short_k:
                exit_date = dt
                exit_reason = "SHORT_STRIKE_TOUCH"
                break

        # Mark after any event on this date.
        ma = mid_px(qa)
        ms = mid_px(qs)
        mw = mid_px(qw)
        if any(pd.isna(x) for x in (ma,ms,mw)):
            continue
        equity = cash + ma*100.0 - n*ms*100.0 + n*mw*100.0
        eq_rows.append((dt, equity))

        if dt >= pos.end_date:
            exit_date = dt
            break

    return cash, n, exit_date, exit_reason, eq_rows

def process_trade(con, opt_path, und, srow, n_fixed, mode):
    info, status = entry_trade(con, opt_path, srow, n_fixed)
    if status != "OK":
        return None, status
    pos, pivot, ml, legs = info

    entry_pair_credit = (
        float(legs["short"]["bid"]) - float(legs["wing"]["ask"])
    )
    # Local event state. (Avoid mutable globals.)
    logs = {"events": [], "_entry_pair_credit": entry_pair_credit}

    und_slice = und[(und["date"] >= pos.entry_date) & (und["date"] <= pos.end_date)].copy().reset_index(drop=True)
    _, n_before_final, exit_date, exit_reason, eq_rows = daily_equity_for_trade(
        pos, pivot, und_slice, mode, logs
    )

    if pd.Timestamp(exit_date) not in pivot.index:
        avail = pivot.index[pivot.index >= pd.Timestamp(exit_date)]
        if len(avail):
            exit_date = avail.min()
        else:
            return None, "NO_EXIT_QUOTES"
    # Rebuild n after management.
    n_final = pos.n_remaining
    cf_exit = terminal_close(pos, pivot, pd.Timestamp(exit_date))
    if cf_exit is None:
        return None, "NO_EXIT_QUOTES"

    # terminal_close currently includes ATM and remaining pairs.
    total_pnl = pos.entry_cashflow * -1.0 + sum(
        [
            # Harvest cash flows already included in pos.cash via process loop;
            # terminal CF is added to initial cash balance for exact accounting.
        ]
    )
    # Exact realized cash accounting:
    # pos.cash started at -entry_cf, then harvest cash flows were added to local cash,
    # but daily_equity_for_trade does not return cash. Recompute realized harvest cash
    # from events, then add final terminal exit cash.
    harvest_cash = 0.0
    for e in logs["events"]:
        # Reconstruct exact executable close cashflow from quotes on event date.
        dt = pd.Timestamp(e["date"])
        qs = leg_quote(pivot, pos.short_id, dt)
        qw = leg_quote(pivot, pos.wing_id, dt)
        h = int(e["n_closed"])
        harvest_cash += (-h*exec_px(qs, "BUY") + h*exec_px(qw, "SELL")) * 100.0

    realized_pnl = -pos.entry_cashflow + harvest_cash + cf_exit
    tr = {
        "entry": pos.entry_date,
        "exit": pd.Timestamp(exit_date),
        "reason": exit_reason if mode == "BASELINE_TOUCH" else ("HARVESTED_THEN_EXIT" if logs["events"] else "EXPIRY_OR_TIME"),
        "n_initial": pos.n_initial,
        "n_final": n_final,
        "atm_strike": pos.atm_k,
        "short_strike": pos.short_k,
        "wing_strike": pos.wing_k,
        "entry_cashflow_usd": pos.entry_cashflow,
        "harvest_events": len(logs["events"]),
        "harvest_cashflow_usd": harvest_cash,
        "exit_cashflow_usd": cf_exit,
        "pnl_usd": realized_pnl,
        "max_loss_proxy_usd": ml,
        "extension": float(srow["ext200"]),
        "ratio52": float(srow["ratio52"]),
        "expiry": pos.expiry,
        "events": logs["events"],
        "eq_rows": eq_rows,
    }
    return tr, "OK"

def run_mode(opt_path, und, n_fixed, mode):
    sig = und[und["signal"] & und["dma200"].notna()].copy()
    con = duckdb.connect()
    trades = []
    rejects = {}
    next_allowed = None
    for _, srow in sig.iterrows():
        entry = pd.Timestamp(srow["date"])
        if next_allowed is not None and entry <= next_allowed:
            continue
        try:
            tr, status = process_trade(con, opt_path, und, srow, n_fixed, mode)
        except Exception as e:
            print(f"TRADE ERROR {entry.date()} {mode}: {e}", file=sys.stderr)
            tr, status = None, "ERROR"
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue
        trades.append(tr)
        next_allowed = pd.Timestamp(tr["exit"]) + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [], {}, pd.DataFrame()

    trdf = pd.DataFrame([{k:v for k,v in t.items() if k not in ("events","eq_rows")} for t in trades])
    trdf = trdf.sort_values("entry").reset_index(drop=True)

    # Daily portfolio equity using marked-to-mid trade rows + realized trade cash.
    # Because trades do not overlap, stitch eq_rows between trade intervals.
    eq = pd.Series(CAPITAL_USD, index=pd.DatetimeIndex(und["date"]), dtype=float)
    cash_base = CAPITAL_USD
    max_seen = CAPITAL_USD
    realized = CAPITAL_USD
    event_map = {}
    for t in trades:
        for dt, val in t["eq_rows"]:
            # t eq is measured from trade-local cash starting at -entry_cf,
            # so convert to portfolio capital baseline.
            pass
    # Robust realized curve for comparable CAGR plus conservative daily MTM DD:
    realized_curve = []
    running_cash = CAPITAL_USD
    for t in trades:
        running_cash += t["pnl_usd"]
        realized_curve.append((t["exit"], running_cash))

    rc = pd.DataFrame(realized_curve, columns=["date","equity"])
    rc["date"] = pd.to_datetime(rc["date"])
    rc = rc.sort_values("date")
    if not rc.empty:
        rc["peak"] = rc["equity"].cummax()
        rc["dd"] = rc["equity"]/rc["peak"] - 1.0
        maxdd_realized = float(rc["dd"].min())
        end_equity = float(rc["equity"].iloc[-1])
        years = max((rc["date"].iloc[-1] - trdf["entry"].iloc[0]).days/365.25, 1/365.25)
        total_ret = end_equity/CAPITAL_USD - 1.0
        cagr = (1.0 + total_ret)**(1.0/years) - 1.0 if (1.0+total_ret) > 0 else -1.0
    else:
        maxdd_realized = 0.0; end_equity = CAPITAL_USD; total_ret=0.0; cagr=0.0; years=0

    # Count approach/reversal events from trade event log.
    events = []
    for t in trades:
        events.extend(t["events"])
    wins = float((trdf["pnl_usd"] > 0).mean())
    stats = {
        "mode": mode,
        "N": int(n_fixed),
        "trades": int(len(trdf)),
        "win_rate": wins,
        "avg_trade_usd": float(trdf["pnl_usd"].mean()),
        "worst_trade_usd": float(trdf["pnl_usd"].min()),
        "best_trade_usd": float(trdf["pnl_usd"].max()),
        "total_return": float(total_ret),
        "cagr": float(cagr),
        "maxdd_realized": float(maxdd_realized),
        "years": float(years),
        "harvest_events": len(events),
        "rejections": rejects,
        "data_start": str(trdf["entry"].min().date()),
        "data_end": str(trdf["exit"].max().date()),
    }
    return trades, stats, trdf

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

    print("OPTIONS_SHA256", sha256_file(opt_path))
    print("UNDERLYING_SHA256", sha256_file(und_path))
    print("OPTIONS_SIZE_BYTES", opt_path.stat().st_size)
    print("UNDERLYING_SIZE_BYTES", und_path.stat().st_size)

    und = load_underlying(und_path)
    print("UNDERLYING_ROWS", len(und), "FROM", und["date"].min().date(), "TO", und["date"].max().date())
    print("SIGNAL_ROWS", int(und["signal"].sum()))
    results = []

    for n in args.n:
        for mode in ["BASELINE_TOUCH","HARVEST50_REVERSAL"]:
            print(f"RUN N={n} MODE={mode}", flush=True)
            trades, stats, trdf = run_mode(opt_path, und, n, mode)
            results.append(stats)
            pd.DataFrame([{
                **{k:v for k,v in t.items() if k not in ("events","eq_rows")},
                "events_json": json.dumps(t["events"], ensure_ascii=False),
            } for t in trades]).to_csv(out / f"trades_N{n}_{mode}.csv", index=False)

    report = {
        "research_contract": {
            "date_range_underlying": [str(und["date"].min().date()), str(und["date"].max().date())],
            "options_source": RELEASE_REPO,
            "release_tag": RELEASE_TAG,
            "no_optimization": True,
            "signal": "QQQ close/high52w >= 0.98 AND close/200DMA - 1 >= 0.08",
            "cooldown_days": COOLDOWN_DAYS,
            "DTE": [DTE_MIN,DTE_MAX],
            "hold_max_days": HOLD_MAX,
            "short_delta": SHORT_DELTA,
            "wing_delta": WING_DELTA,
            "approach": f"daily High >= {APPROACH_FRAC:.2f} * short strike, edge-triggered",
            "reversal": "next trading-day close < approach-day close",
            "harvest": "close ceil(N_remaining/2) short+wing pairs at executable quotes; only when pair profit > 0",
            "entry_execution": "ATM buy Ask; short sell Bid; wing buy Ask",
            "daily_mark": "Mid",
            "risk_gate": f"entry max-loss proxy <= {RISK_PCT:.2f}% NAV",
            "capital_hkd": CAPITAL_HKD,
            "hkd_per_usd": HKD_PER_USD,
        },
        "results": results,
    }
    (out/"ratio_call_harvest_v1_result.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    pd.DataFrame(results).to_csv(out/"ratio_call_harvest_v1_summary.csv",index=False)
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()
