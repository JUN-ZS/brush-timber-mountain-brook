#!/usr/bin/env python3
"""Frozen QQQ ratio-call HARVEST50 V1 replay.

Comparison:
  BASELINE_TOUCH
    +1 ATM call - N*OTM short call + N*far OTM call wing.
    Exit whole package on the first post-entry day whose underlying High
    touches the selected short strike; otherwise exit at time/expiry.

  HARVEST50_REVERSAL
    Same entry and contract selection. Do not exit on short-strike touch.
    An approach event is an edge-triggered day with High >= 98% of short strike.
    If the NEXT trading day's Close is lower than the approach day's Close,
    and the short+wing pair is profitable on executable close quotes, close
    ceil(N_remaining/2) pairs (>= 50% of remaining pairs), keeping the ATM long.
    Re-arm only after price leaves the approach zone. Final exit is time/expiry.

No optimization, no OOS fitting, no synthetic option pricing.
Data is the canonical data-v1 GitHub release.
"""

import argparse
import hashlib
import json
import math
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
START_DATE = pd.Timestamp("2011-01-01")
END_DATE = pd.Timestamp("2025-12-31")


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
        raise FileNotFoundError("Canonical data files were not downloaded by the workflow.")
    return opt, und


def duck(con, sql, params=None):
    return con.execute(sql, params or {}).df()


def load_underlying(path: Path):
    df = pd.read_parquet(path)
    df.columns = [c.lower() for c in df.columns]
    if "date" not in df.columns:
        raise ValueError("Underlying data missing date")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df = df.sort_values("date").drop_duplicates("date")
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)].copy()
    need = {"open", "high", "low", "close"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"Underlying data missing {sorted(missing)}")
    df["dma200"] = df["close"].rolling(200, min_periods=200).mean()
    df["high52w"] = df["close"].rolling(252, min_periods=252).max()
    df["ext200"] = df["close"] / df["dma200"] - 1.0
    df["ratio52"] = df["close"] / df["high52w"]
    df["signal"] = (df["ratio52"] >= PCT_52W) & (df["ext200"] >= DMA_EXT)
    return df.reset_index(drop=True)


def pick_legs(con, opt_path: Path, entry_date: pd.Timestamp):
    lo = entry_date + pd.Timedelta(days=DTE_MIN)
    hi = entry_date + pd.Timedelta(days=DTE_MAX)
    rows = duck(con, """
        SELECT contract_id, expiration, strike, type, bid, ask, mark,
               volume, open_interest, implied_volatility, delta
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) = ?
          AND upper(type) = 'CALL'
          AND CAST(expiration AS DATE) BETWEEN ? AND ?
          AND delta IS NOT NULL
          AND bid IS NOT NULL
          AND ask IS NOT NULL
    """, [str(opt_path), entry_date.date(), lo.date(), hi.date()])
    if rows.empty:
        return None

    rows["expiration"] = pd.to_datetime(rows["expiration"])
    rows["dte"] = (rows["expiration"] - entry_date).dt.days

    # Same practical-expiry selection as the original lab:
    exp = rows.sort_values(["dte", "volume"], ascending=[True, False]).iloc[0]["expiration"]
    chain = rows[rows["expiration"] == exp].copy()
    if chain.empty:
        return None

    atm = chain.iloc[(chain["delta"] - 0.50).abs().argsort()[:1]].iloc[0]
    shorts = chain[chain["strike"] > atm["strike"]].copy()
    if shorts.empty:
        return None
    shorts["d_err"] = (shorts["delta"] - SHORT_DELTA).abs()
    short = shorts.sort_values(["d_err", "strike"]).iloc[0]

    wings = chain[chain["strike"] > short["strike"]].copy()
    if wings.empty:
        return None
    wings["d_err"] = (wings["delta"] - WING_DELTA).abs()
    wing = wings.sort_values(["d_err", "strike"]).iloc[0]

    return {
        "expiry": pd.Timestamp(atm["expiration"]),
        "atm": {k: atm[k] for k in ["contract_id", "strike", "bid", "ask", "mark", "delta", "expiration"]},
        "short": {k: short[k] for k in ["contract_id", "strike", "bid", "ask", "mark", "delta", "expiration"]},
        "wing": {k: wing[k] for k in ["contract_id", "strike", "bid", "ask", "mark", "delta", "expiration"]},
    }


def max_loss_proxy(legs, n, spot):
    atm_k = float(legs["atm"]["strike"])
    short_k = float(legs["short"]["strike"])
    wing_k = float(legs["wing"]["strike"])
    grid = np.linspace(max(1.0, spot * 0.20),
                       max(spot * 2.5, wing_k * 1.25), 600)
    initial = (
        float(legs["atm"]["ask"])
        - n * float(legs["short"]["bid"])
        + n * float(legs["wing"]["ask"])
    ) * 100.0
    payoff = (
        np.maximum(grid - atm_k, 0.0)
        - n * np.maximum(grid - short_k, 0.0)
        + n * np.maximum(grid - wing_k, 0.0)
    ) * 100.0
    return max(0.0, -float(np.min(payoff - initial)))


def build_selection_cache(con, opt_path, signal_dates):
    if not signal_dates:
        return {}, {}
    # One parquet scan for all signal dates. Contract selection is identical
    # to the lab logic, but implemented set-wise for speed.
    date_list = [pd.Timestamp(d).date() for d in signal_dates]
    rows = duck(con, """
        SELECT
            CAST(date AS DATE) AS date,
            expiration,
            strike,
            bid,
            ask,
            mark,
            volume,
            delta,
            DATEDIFF('day', CAST(date AS DATE), CAST(expiration AS DATE)) AS dte
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND upper(type) = 'CALL'
          AND delta IS NOT NULL
          AND bid IS NOT NULL
          AND ask IS NOT NULL
          AND CAST(expiration AS DATE) BETWEEN
              CAST(date AS DATE) + INTERVAL 18 DAY
              AND CAST(date AS DATE) + INTERVAL 35 DAY
    """, [str(opt_path), date_list])
    if rows.empty:
        return {}, {"NO_CHAIN_ROWS": len(date_list)}

    rows["date"] = pd.to_datetime(rows["date"])
    rows["expiration"] = pd.to_datetime(rows["expiration"])

    # Same practical-expiry rule as the original lab: nearest DTE,
    # volume descending as the tie-break.
    rows = rows.sort_values(
        ["date","dte","volume"],
        ascending=[True,True,False]
    )
    chosen_exp = (
        rows.drop_duplicates("date", keep="first")[["date","expiration"]]
        .rename(columns={"expiration":"chosen_exp"})
    )
    chain = rows.merge(chosen_exp, on="date", how="inner")
    chain = chain[chain["expiration"] == chain["chosen_exp"]].copy()

    cache = {}
    for dt, g in chain.groupby("date", sort=True):
        atm = g.loc[(g["delta"] - 0.50).abs().idxmin()]
        shorts = g[g["strike"] > float(atm["strike"])].copy()
        if shorts.empty:
            continue
        shorts["d_err"] = (shorts["delta"] - SHORT_DELTA).abs()
        short = shorts.sort_values(["d_err","strike"]).iloc[0]

        wings = g[g["strike"] > float(short["strike"])].copy()
        if wings.empty:
            continue
        wings["d_err"] = (wings["delta"] - WING_DELTA).abs()
        wing = wings.sort_values(["d_err","strike"]).iloc[0]

        cache[pd.Timestamp(dt)] = {
            "expiry": pd.Timestamp(atm["expiration"]),
            "atm": {
                "contract_id": None,
                "strike": float(atm["strike"]),
                "bid": float(atm["bid"]),
                "ask": float(atm["ask"]),
                "mark": float(atm["mark"]),
                "delta": float(atm["delta"]),
                "expiration": pd.Timestamp(atm["expiration"]),
            },
            "short": {
                "contract_id": None,
                "strike": float(short["strike"]),
                "bid": float(short["bid"]),
                "ask": float(short["ask"]),
                "mark": float(short["mark"]),
                "delta": float(short["delta"]),
                "expiration": pd.Timestamp(short["expiration"]),
            },
            "wing": {
                "contract_id": None,
                "strike": float(wing["strike"]),
                "bid": float(wing["bid"]),
                "ask": float(wing["ask"]),
                "mark": float(wing["mark"]),
                "delta": float(wing["delta"]),
                "expiration": pd.Timestamp(wing["expiration"]),
            },
        }

    # Fetch contract_id exactly once for the three selected strikes.  The
    # selection stage above intentionally did not group on contract_id.
    lookup = duck(con, """
        SELECT CAST(date AS DATE) AS date, expiration, strike, type, contract_id
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND upper(type) = 'CALL'
          AND expiration BETWEEN
              CAST(date AS DATE) + INTERVAL 18 DAY
              AND CAST(date AS DATE) + INTERVAL 35 DAY
    """, [str(opt_path), date_list])
    lookup["date"] = pd.to_datetime(lookup["date"])
    lookup["expiration"] = pd.to_datetime(lookup["expiration"])

    rejects = {}
    for dt, legs in list(cache.items()):
        for key in ("atm","short","wing"):
            m = lookup[
                (lookup["date"] == dt) &
                (lookup["expiration"] == legs[key]["expiration"]) &
                (lookup["strike"] == legs[key]["strike"]) &
                (lookup["type"].str.upper() == "CALL")
            ]
            if m.empty:
                cache.pop(dt, None)
                rejects["MISSING_CONTRACT_ID"] = rejects.get("MISSING_CONTRACT_ID",0)+1
                break
            legs[key]["contract_id"] = str(m.iloc[0]["contract_id"])
    return cache, rejects
def fetch_all_quotes(con, opt_path, selected):
    ids = sorted({
        legs["atm"]["contract_id"]
        for legs in selected.values()
    } | {
        legs["short"]["contract_id"]
        for legs in selected.values()
    } | {
        legs["wing"]["contract_id"]
        for legs in selected.values()
    })
    if not ids:
        return pd.DataFrame()

    # One parquet scan for every selected contract.  This replaces hundreds
    # of repeated file scans while preserving exact EOD bid/ask/mark.
    values = duck(con, """
        SELECT CAST(date AS DATE) AS date, contract_id, bid, ask, mark
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """, [str(opt_path), ids, START_DATE.date(), END_DATE.date()])
    values["date"] = pd.to_datetime(values["date"])
    values["contract_id"] = values["contract_id"].astype(str)
    return values.set_index(["date", "contract_id"]).sort_index()


def q_at(quotes, dt, cid):
    try:
        r = quotes.loc[(pd.Timestamp(dt), str(cid))]
    except KeyError:
        return None
    return {"bid": float(r["bid"]), "ask": float(r["ask"]), "mark": float(r["mark"])}


def executable(q, side):
    if q is None or pd.isna(q["bid"]) or pd.isna(q["ask"]):
        return np.nan
    return float(q["ask"] if side == "BUY" else q["bid"])


def midpoint(q):
    if q is None:
        return np.nan
    if pd.notna(q["bid"]) and pd.notna(q["ask"]):
        return (float(q["bid"]) + float(q["ask"])) / 2.0
    if pd.notna(q["mark"]):
        return float(q["mark"])
    return np.nan


def process_one(und, quotes, entry_row, legs, n_initial, mode):
    entry = pd.Timestamp(entry_row["date"])
    spot = float(entry_row["close"])
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

    atm_id = str(legs["atm"]["contract_id"])
    short_id = str(legs["short"]["contract_id"])
    wing_id = str(legs["wing"]["contract_id"])

    qe_atm = q_at(quotes, entry, atm_id)
    qe_short = q_at(quotes, entry, short_id)
    qe_wing = q_at(quotes, entry, wing_id)
    if any(x is None for x in (qe_atm, qe_short, qe_wing)):
        return None, "NO_ENTRY_QUOTES"

    buy_atm = executable(qe_atm, "BUY")
    sell_short = executable(qe_short, "SELL")
    buy_wing = executable(qe_wing, "BUY")
    if any(pd.isna(x) for x in (buy_atm, sell_short, buy_wing)):
        return None, "NO_ENTRY_QUOTES"

    entry_cf = (buy_atm - n_initial * sell_short + n_initial * buy_wing) * 100.0
    pair_entry_credit = sell_short - buy_wing
    n_remaining = int(n_initial)
    harvest_events = []
    approach_armed = True
    last_approach_idx = None
    pending_action = None

    daily = und[(und["date"] >= entry) & (und["date"] <= end_date)].copy().reset_index(drop=True)
    if daily.empty:
        return None, "NO_UNDERLYING_WINDOW"

    # Exact entry risk gate, same as the lab's defined-loss proxy.
    ml = max_loss_proxy(legs, n_initial, spot)
    if ml > CAPITAL_USD * (RISK_PCT / 100.0):
        return None, "RISK_GATE"

    cash = -entry_cf
    eq_rows = []

    exit_date = pd.Timestamp(end_date)
    exit_reason = "EXPIRY_OR_TIME"

    for i, row in daily.iterrows():
        dt = pd.Timestamp(row["date"])
        is_final = False

        # Path-managed rule:
        #   approach on T -> observe T+1:
        #     T+1 Close < T Close: harvest >=50% of initial pair credit by
        #       closing ceil(N_remaining/2) paired short+wing units.
        #     otherwise: continuation -> exit the whole package on T+1.
        if mode in ("HARVEST50_REVERSAL", "HARVEST50_GOVERNED") and dt > entry:
            if pending_action is not None and pd.Timestamp(pending_action["date"]) == dt:
                action = pending_action
                pending_action = None
                if float(row["close"]) >= float(action["approach_close"]):
                    exit_date = dt
                    exit_reason = "APPROACH_THEN_CONTINUATION_EXIT"
                    is_final = True
                elif n_remaining > 0:
                    qs_now = q_at(quotes, dt, short_id)
                    qw_now = q_at(quotes, dt, wing_id)
                    bs_now = executable(qs_now, "BUY")
                    sw_now = executable(qw_now, "SELL")
                    if pd.notna(bs_now) and pd.notna(sw_now):
                        pair_close_cost = bs_now - sw_now
                        pair_profit = pair_entry_credit - pair_close_cost
                        harvest_threshold = 0.50 * pair_entry_credit
                        if pair_entry_credit > 0.0 and pair_profit >= harvest_threshold:
                            h = int(math.ceil(n_remaining / 2.0))
                            harvest_cf = (-h * bs_now + h * sw_now) * 100.0
                            cash += harvest_cf
                            n_before = n_remaining
                            n_remaining -= h
                            harvest_events.append({
                                "date": str(dt.date()),
                                "event": "HARVEST50_REVERSAL",
                                "approach_date": str(action["approach_date"]),
                                "approach_close": float(action["approach_close"]),
                                "reversal_close": float(row["close"]),
                                "n_before": n_before,
                                "n_closed": h,
                                "n_after": n_remaining,
                                "harvest_fraction": h / n_before,
                                "pair_entry_credit_usd": pair_entry_credit * 100.0,
                                "harvest_threshold_usd": harvest_threshold * 100.0,
                                "pair_profit_usd": pair_profit * 100.0,
                                "realized_harvest_pnl_usd": h * pair_profit * 100.0,
                            })
                        else:
                            harvest_events.append({
                                "date": str(dt.date()),
                                "event": "REVERSAL_NO_HARVEST_THRESHOLD",
                                "approach_date": str(action["approach_date"]),
                                "approach_close": float(action["approach_close"]),
                                "reversal_close": float(row["close"]),
                                "pair_entry_credit_usd": pair_entry_credit * 100.0,
                                "harvest_threshold_usd": harvest_threshold * 100.0,
                                "pair_profit_usd": pair_profit * 100.0,
                            })
            else:
                approach_now = float(row["high"]) >= APPROACH_FRAC * float(legs["short"]["strike"])
                if approach_now and approach_armed and n_remaining > 0:
                    approach_armed = False
                    if i + 1 < len(daily):
                        next_dt = pd.Timestamp(daily.iloc[i + 1]["date"])
                        approach_close = float(row["close"])
                        pending_action = {
                            "date": next_dt,
                            "approach_date": dt,
                            "approach_close": approach_close,
                        }
                elif not approach_now:
                    approach_armed = True

        # Baseline: the original whole-package touch exit.
        if mode == "BASELINE_TOUCH" and dt > entry:
            if float(row["high"]) >= float(legs["short"]["strike"]):
                exit_date = dt
                exit_reason = "SHORT_STRIKE_TOUCH"
                is_final = True
            else:
                is_final = dt >= end_date
        elif mode == "HARVEST50_REVERSAL":
            is_final = locals().get("is_final", False) or dt >= end_date
        elif mode == "HARVEST50_GOVERNED":
            is_final = locals().get("is_final", False) or dt >= end_date
        else:
            is_final = dt >= end_date

        # Mark-to-mid equity for daily drawdown.
        qa = q_at(quotes, dt, atm_id)
        qs = q_at(quotes, dt, short_id)
        qw = q_at(quotes, dt, wing_id)
        ma, ms, mw = midpoint(qa), midpoint(qs), midpoint(qw)
        if not any(pd.isna(x) for x in (ma, ms, mw)):
            eq = CAPITAL_USD + cash + ma * 100.0 - n_remaining * ms * 100.0 + n_remaining * mw * 100.0
            eq_rows.append((dt, eq))

        if is_final:
            break

    qx_atm = q_at(quotes, exit_date, atm_id)
    qx_short = q_at(quotes, exit_date, short_id)
    qx_wing = q_at(quotes, exit_date, wing_id)
    if any(x is None for x in (qx_atm, qx_short, qx_wing)):
        # No interpolation: use first available quote date on/after the intended
        # exit, but only if all three contracts are quoted on that same date.
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
        qx_atm = q_at(quotes, exit_date, atm_id)
        qx_short = q_at(quotes, exit_date, short_id)
        qx_wing = q_at(quotes, exit_date, wing_id)

    sell_atm = executable(qx_atm, "SELL")
    buy_short = executable(qx_short, "BUY")
    sell_wing = executable(qx_wing, "SELL")
    if any(pd.isna(x) for x in (sell_atm, buy_short, sell_wing)):
        return None, "NO_EXIT_QUOTES"

    exit_cf = (sell_atm - n_remaining * buy_short + n_remaining * sell_wing) * 100.0

    harvest_cash = 0.0
    for ev in harvest_events:
        dt = pd.Timestamp(ev["date"])
        qs = q_at(quotes, dt, short_id)
        qw = q_at(quotes, dt, wing_id)
        h = int(ev["n_closed"])
        harvest_cash += (-h * executable(qs, "BUY") + h * executable(qw, "SELL")) * 100.0

    pnl = -entry_cf + harvest_cash + exit_cf

    # Replace the exit-date mark with executable terminal equity.
    portfolio_terminal_eq = CAPITAL_USD + pnl
    eq_rows.append((pd.Timestamp(exit_date), portfolio_terminal_eq))

    return {
        "entry": entry,
        "exit": pd.Timestamp(exit_date),
        "reason": exit_reason if mode == "BASELINE_TOUCH" else (
            "HARVESTED_THEN_EXIT" if harvest_events else "EXPIRY_OR_TIME"
        ),
        "n_initial": int(n_initial),
        "n_final": int(n_remaining),
        "atm_strike": float(legs["atm"]["strike"]),
        "short_strike": float(legs["short"]["strike"]),
        "wing_strike": float(legs["wing"]["strike"]),
        "entry_cashflow_usd": float(entry_cf),
        "harvest_events": int(len(harvest_events)),
        "harvest_cashflow_usd": float(harvest_cash),
        "exit_cashflow_usd": float(exit_cf),
        "pnl_usd": float(pnl),
        "max_loss_proxy_usd": float(ml),
        "extension": float(entry_row["ext200"]),
        "ratio52": float(entry_row["ratio52"]),
        "expiry": expiry,
        "events": harvest_events,
        "eq_rows": eq_rows,
    }, "OK"


def run_mode(und, quotes, selection, n_fixed, mode):
    signal_rows = und[und["signal"] & und["dma200"].notna()].copy()
    trades = []
    rejects = {}
    next_allowed = None

    for _, row in signal_rows.iterrows():
        entry = pd.Timestamp(row["date"])
        if next_allowed is not None and entry <= next_allowed:
            continue
        legs = selection.get(entry)
        if legs is None:
            rejects["NO_LEGS"] = rejects.get("NO_LEGS", 0) + 1
            continue

        tr, status = process_one(und, quotes, row, legs, n_fixed, mode)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue
        trades.append(tr)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [], {
            "mode": mode, "N": n_fixed, "trades": 0,
            "rejections": rejects, "harvest_events": 0
        }, pd.DataFrame()

    trades.sort(key=lambda x: x["entry"])
    rows = []
    equity_points = []
    for t in trades:
        rows.append({k: v for k, v in t.items() if k not in ("events", "eq_rows")})
        equity_points.extend(t["eq_rows"])

    trdf = pd.DataFrame(rows).sort_values("entry").reset_index(drop=True)
    eqdf = pd.DataFrame(equity_points, columns=["date", "equity"])
    eqdf["date"] = pd.to_datetime(eqdf["date"])
    # Multiple observations on the same exit day: keep terminal realized equity.
    eqdf = eqdf.groupby("date", as_index=False)["equity"].last().sort_values("date")
    eqdf["peak"] = eqdf["equity"].cummax()
    eqdf["dd"] = eqdf["equity"] / eqdf["peak"] - 1.0

    end_equity = float(CAPITAL_USD + trdf["pnl_usd"].sum())
    years = max((trdf["exit"].iloc[-1] - trdf["entry"].iloc[0]).days / 365.25, 1/365.25)
    total_ret = end_equity / CAPITAL_USD - 1.0
    cagr = (1.0 + total_ret) ** (1.0 / years) - 1.0 if 1.0 + total_ret > 0 else -1.0

    events = [ev for t in trades for ev in t["events"]]
    stats = {
        "mode": mode,
        "N": int(n_fixed),
        "trades": int(len(trdf)),
        "win_rate": float((trdf["pnl_usd"] > 0).mean()),
        "avg_trade_usd": float(trdf["pnl_usd"].mean()),
        "worst_trade_usd": float(trdf["pnl_usd"].min()),
        "best_trade_usd": float(trdf["pnl_usd"].max()),
        "total_return": float(total_ret),
        "cagr": float(cagr),
        "maxdd_daily_mtm": float(eqdf["dd"].min()),
        "maxdd_realized": float(
            (trdf["pnl_usd"].cumsum().add(CAPITAL_USD).div(
                trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax()
            ) - 1.0).min()
        ),
        "years": float(years),
        "harvest_events": int(len(events)),
        "profitable_harvest_events": int(sum(1 for e in events if e.get("pair_profit_usd", 0) > 0)),
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
    opt_hash = sha256_file(opt_path)
    und_hash = sha256_file(und_path)
    und = load_underlying(und_path)

    signal_dates = [pd.Timestamp(x) for x in und.loc[und["signal"], "date"].tolist()]
    con = duckdb.connect()
    selection, selection_rejects = build_selection_cache(con, opt_path, signal_dates)

    print("OPTIONS_SHA256", opt_hash, flush=True)
    print("UNDERLYING_SHA256", und_hash, flush=True)
    print("UNDERLYING_ROWS", len(und), "FROM", und["date"].min().date(), "TO", und["date"].max().date(), flush=True)
    print("SIGNAL_ROWS", len(signal_dates), flush=True)
    print("SELECTION_CACHE", len(selection), "SELECTION_REJECTS", selection_rejects, flush=True)
    print("BATCH_FETCH_QUOTES", flush=True)

    quotes = fetch_all_quotes(con, opt_path, selection)
    print("QUOTE_ROWS", len(quotes), flush=True)

    all_stats = []
    for n in args.n:
        for mode in ("BASELINE_TOUCH", "HARVEST50_REVERSAL", "HARVEST50_GOVERNED"):
            print(f"RUN N={n} MODE={mode}", flush=True)
            trades, stats, eqdf = run_mode(und, quotes, selection, n, mode)
            all_stats.append(stats)
            pd.DataFrame([
                {
                    **{k: v for k, v in t.items() if k not in ("events", "eq_rows")},
                    "events_json": json.dumps(t["events"], ensure_ascii=False),
                }
                for t in trades
            ]).to_csv(out / f"trades_N{n}_{mode}.csv", index=False)
            if not eqdf.empty:
                eqdf.to_csv(out / f"equity_N{n}_{mode}.csv", index=False)

    report = {
        "research_contract": {
            "strategy": "1 ATM Long Call + N OTM Short Calls + N Far OTM Long Wings",
            "signal": "QQQ close / 52-week high >= 0.98 AND close / 200DMA - 1 >= 0.08",
            "cooldown_days": COOLDOWN_DAYS,
            "DTE": [DTE_MIN, DTE_MAX],
            "hold_max_days": HOLD_MAX,
            "short_delta": SHORT_DELTA,
            "wing_delta": WING_DELTA,
            "approach": f"daily High >= {APPROACH_FRAC:.2f} * selected short strike, edge-triggered",
            "reversal": "next trading-day Close < approach-day Close",
            "harvest": "on next-day reversal after approach, close ceil(N_remaining/2) pairs only when executable pair profit >= 50% of initial pair credit; Short Ask / Wing Bid; keep ATM long",
            "baseline_exit": "first post-entry day High >= short strike",
            "new_exit": "HARVEST50_REVERSAL: time/expiry; HARVEST50_GOVERNED: approach then continuation exits whole package next trading day; reversal harvests only when pair profit >= 50% of initial pair credit",
            "entry_execution": "ATM buy Ask; short sell Bid; wing buy Ask",
            "mark": "daily Mid",
            "strict_quote_policy": "no interpolation; missing entry/exit quotes reject the trade",
            "risk_gate": f"entry terminal-payoff max-loss proxy <= {RISK_PCT:.2f}% NAV",
            "capital_hkd": CAPITAL_HKD,
            "hkd_per_usd": HKD_PER_USD,
            "no_optimization": True,
        },
        "data": {
            "source_repo": RELEASE_REPO,
            "release_tag": RELEASE_TAG,
            "options_sha256": opt_hash,
            "underlying_sha256": und_hash,
            "underlying_date_range": [str(und["date"].min().date()), str(und["date"].max().date())],
            "options_expected_coverage": "2011-03-23 through 2025-12-16",
        },
        "results": all_stats,
    }
    (out / "ratio_call_harvest_v1_result.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    pd.DataFrame(all_stats).to_csv(out / "ratio_call_harvest_v1_summary.csv", index=False)
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
