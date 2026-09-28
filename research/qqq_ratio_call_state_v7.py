#!/usr/bin/env python3
"""
QQQ Ratio-Call State Machine V7 — Breakout Short-Only
================================

Frozen, no-optimization research test.

Structure:
    +1 ATM CALL - N SHORT OTM CALL + N FAR OTM LONG CALL

At each entry:
    N_initial = largest integer N in {1..6} whose exact terminal payoff
                max-loss, using executable entry quotes, is <= risk budget.

Baseline:
    Same N_initial. Hold entire package until first daily High >= short strike;
    then close ATM + all remaining short + all wing contracts at executable EOD
    quotes.

State-machine candidate:
    ATM is core and is never removed by management.
    N_t counts paired (SHORT + WING) units.

    1. BREAKOUT governor:
       if daily High >= short strike, close ALL remaining paired short+wing
       units at that day's executable quotes; keep ATM.

    2. APPROACH -> next-day path test:
       Approach zone is armed when either
          High >= 0.90 * short strike
       OR short-call observed daily delta >= 0.45.
       The next trading day is classified:
          continuation: Close[next] >= Close[approach]
             -> close ALL remaining pairs, keep ATM.
          reversal: Close[next] < Close[approach]
             AND pair executable profit >= 50% of initial pair credit
             -> close ceil(N_remaining / 2) paired units, keep ATM.
       The approach trigger is edge-triggered and re-arms only after leaving
       the approach zone.

    3. LATE DELTA governor:
       if no higher-priority event fired and observed short delta >= 0.60,
       close exactly ONE paired unit.

No pair is ever re-added during a trade.
No optimization, no result fitting, no OOS selection.
N_max=6, risk budgets=2%, 5%, and 10% NAV are pre-declared sensitivity runs.
Downside governor: when daily package mark-to-mid P&L <= -50% of that
trade's own initial terminal max-loss proxy, terminate the whole package
at that day's executable quotes.

Data:
    canonical QQQ data-v1 GitHub release from
    lambdaclass/options_portfolio_backtester.

Execution:
    Entry: ATM buy Ask; short sell Bid; wing buy Ask.
    Management: short buy Ask; wing sell Bid.
    Final: remaining legs at executable EOD quotes.
    Daily drawdown mark: bid/ask Mid.
    No interpolation and no quote fabrication.
"""

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RELEASE_REPO = "lambdaclass/options_portfolio_backtester"
RELEASE_TAG = "data-v1"

CAPITAL_HKD = 500_000.0
HKD_PER_USD = 7.8
CAPITAL_USD = CAPITAL_HKD / HKD_PER_USD

N_MAX = 6
RISK_BUDGETS = (0.02, 0.05, 0.10)
DOWNSIDE_STOP_FRACTION = 0.50

PCT_52W = 0.98
DMA_EXT = 0.08
COOLDOWN_DAYS = 10

SHORT_DELTA_ENTRY = 0.20
WING_DELTA_ENTRY = 0.08
APPROACH_FRAC = 0.90
APPROACH_DELTA = 0.45
DANGER_DELTA = 0.60
HARVEST_RECOVERY = 0.50

DTE_MIN = 18
DTE_MAX = 35
HOLD_MAX = 30

START_DATE = pd.Timestamp("2011-01-01")
END_DATE = pd.Timestamp("2025-12-31")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_data(data_dir: Path):
    opt = data_dir / "QQQ_options.parquet"
    und = data_dir / "QQQ_underlying.parquet"
    if not opt.exists() or not und.exists():
        raise FileNotFoundError("Canonical data-v1 files are required.")
    return opt, und


def duck(con, sql, params=None):
    return con.execute(sql, params or {}).df()


def load_underlying(path: Path):
    df = pd.read_parquet(path)
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df = df.sort_values("date").drop_duplicates("date")
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)].copy()
    for c in ("open", "high", "low", "close"):
        if c not in df.columns:
            raise ValueError(f"Underlying missing {c}")
    df["dma200"] = df["close"].rolling(200, min_periods=200).mean()
    df["high52w"] = df["close"].rolling(252, min_periods=252).max()
    df["ext200"] = df["close"] / df["dma200"] - 1.0
    df["ratio52"] = df["close"] / df["high52w"]
    df["signal"] = (
        (df["ratio52"] >= PCT_52W)
        & (df["ext200"] >= DMA_EXT)
    )
    return df.reset_index(drop=True)


def select_contracts(con, opt_path: Path, signal_dates):
    if not signal_dates:
        return {}, {}
    dates = [pd.Timestamp(x).date() for x in signal_dates]
    rows = duck(con, """
        SELECT
            CAST(date AS DATE) AS date,
            CAST(expiration AS DATE) AS expiration,
            contract_id,
            strike,
            type,
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
    """, [str(opt_path), dates])

    if rows.empty:
        return {}, {"NO_CHAIN_ROWS": len(dates)}

    rows["date"] = pd.to_datetime(rows["date"])
    rows["expiration"] = pd.to_datetime(rows["expiration"])

    # Nearest expiry; volume is the deterministic tie-break.
    rows = rows.sort_values(
        ["date", "dte", "volume"],
        ascending=[True, True, False]
    )
    chosen = (
        rows.drop_duplicates("date", keep="first")[["date", "expiration"]]
        .rename(columns={"expiration": "chosen_exp"})
    )
    chain = rows.merge(chosen, on="date", how="inner")
    chain = chain[chain["expiration"] == chain["chosen_exp"]].copy()

    cache = {}
    rejects = {}
    for dt, g in chain.groupby("date", sort=True):
        if g.empty:
            continue
        atm = g.loc[(g["delta"] - 0.50).abs().idxmin()]

        shorts = g[g["strike"] > float(atm["strike"])].copy()
        if shorts.empty:
            rejects["NO_SHORT"] = rejects.get("NO_SHORT", 0) + 1
            continue
        shorts["d_err"] = (shorts["delta"] - SHORT_DELTA_ENTRY).abs()
        short = shorts.sort_values(["d_err", "strike"]).iloc[0]

        wings = g[g["strike"] > float(short["strike"])].copy()
        if wings.empty:
            rejects["NO_WING"] = rejects.get("NO_WING", 0) + 1
            continue
        wings["d_err"] = (wings["delta"] - WING_DELTA_ENTRY).abs()
        wing = wings.sort_values(["d_err", "strike"]).iloc[0]

        cache[pd.Timestamp(dt)] = {
            "expiry": pd.Timestamp(atm["expiration"]),
            "atm": {
                "contract_id": str(atm["contract_id"]),
                "strike": float(atm["strike"]),
                "bid": float(atm["bid"]),
                "ask": float(atm["ask"]),
                "mark": float(atm["mark"]),
                "delta": float(atm["delta"]),
            },
            "short": {
                "contract_id": str(short["contract_id"]),
                "strike": float(short["strike"]),
                "bid": float(short["bid"]),
                "ask": float(short["ask"]),
                "mark": float(short["mark"]),
                "delta": float(short["delta"]),
            },
            "wing": {
                "contract_id": str(wing["contract_id"]),
                "strike": float(wing["strike"]),
                "bid": float(wing["bid"]),
                "ask": float(wing["ask"]),
                "mark": float(wing["mark"]),
                "delta": float(wing["delta"]),
            },
        }

    return cache, rejects


def fetch_quotes(con, opt_path: Path, selection):
    ids = sorted({
        legs[k]["contract_id"]
        for legs in selection.values()
        for k in ("atm", "short", "wing")
    })
    if not ids:
        return pd.DataFrame()

    q = duck(con, """
        SELECT
            CAST(date AS DATE) AS date,
            contract_id,
            bid,
            ask,
            mark,
            delta
        FROM read_parquet(?)
        WHERE contract_id IN (SELECT * FROM UNNEST(?))
          AND CAST(date AS DATE) BETWEEN ? AND ?
    """, [str(opt_path), ids, START_DATE.date(), END_DATE.date()])

    q["date"] = pd.to_datetime(q["date"])
    q["contract_id"] = q["contract_id"].astype(str)
    q = (
        q.sort_values(["date", "contract_id"])
         .groupby(["date", "contract_id"], as_index=False)
         .last()
    )
    return q.set_index(["date", "contract_id"]).sort_index()


def q_at(quotes, dt, cid):
    try:
        r = quotes.loc[(pd.Timestamp(dt), str(cid))]
    except KeyError:
        return None
    return {
        "bid": float(r["bid"]),
        "ask": float(r["ask"]),
        "mark": float(r["mark"]),
        "delta": float(r["delta"]) if pd.notna(r["delta"]) else np.nan,
    }


def executable(q, side):
    if q is None or pd.isna(q["bid"]) or pd.isna(q["ask"]):
        return np.nan
    return float(q["ask"] if side == "BUY" else q["bid"])


def midpoint(q):
    if q is None:
        return np.nan
    if pd.notna(q["bid"]) and pd.notna(q["ask"]):
        return 0.5 * (float(q["bid"]) + float(q["ask"]))
    return np.nan


def package_max_loss(legs, n):
    ka = float(legs["atm"]["strike"])
    ks = float(legs["short"]["strike"])
    kw = float(legs["wing"]["strike"])

    entry_cost = (
        float(legs["atm"]["ask"])
        - n * float(legs["short"]["bid"])
        + n * float(legs["wing"]["ask"])
    ) * 100.0

    def terminal_pnl(s):
        payoff = (
            max(s - ka, 0.0)
            - n * max(s - ks, 0.0)
            + n * max(s - kw, 0.0)
        ) * 100.0
        return payoff - entry_cost

    # Piecewise-linear payoff; minima occur at kinks / zero.
    candidates = [0.0, ka, ks, kw]
    return max(0.0, -min(terminal_pnl(s) for s in candidates))


def choose_initial_n(legs, risk_budget):
    limit = CAPITAL_USD * risk_budget
    eligible = [n for n in range(1, N_MAX + 1)
                if package_max_loss(legs, n) <= limit + 1e-9]
    return max(eligible) if eligible else 0


def final_quote_date(quotes, intended, ids):
    # Strict: final liquidation must occur on the intended date, with all
    # three contracts quoted. No stale/interpolated fill.
    d = pd.Timestamp(intended)
    if all(q_at(quotes, d, cid) is not None for cid in ids):
        return d
    return None


def manage_trade(und, quotes, row, legs, n_initial, mode):
    entry = pd.Timestamp(row["date"])
    expiry = pd.Timestamp(legs["expiry"])
    end_date = min(entry + pd.Timedelta(days=HOLD_MAX), expiry)

    aid = legs["atm"]["contract_id"]
    sid = legs["short"]["contract_id"]
    wid = legs["wing"]["contract_id"]
    ids = (aid, sid, wid)

    qa0 = q_at(quotes, entry, aid)
    qs0 = q_at(quotes, entry, sid)
    qw0 = q_at(quotes, entry, wid)
    if any(x is None for x in (qa0, qs0, qw0)):
        return None, "NO_ENTRY_QUOTES"

    atm_entry = executable(qa0, "BUY")
    short_entry = executable(qs0, "SELL")
    wing_entry = executable(qw0, "BUY")
    if any(pd.isna(x) for x in (atm_entry, short_entry, wing_entry)):
        return None, "NO_ENTRY_QUOTES"

    entry_cf = (atm_entry - n_initial * short_entry + n_initial * wing_entry) * 100.0
    pair_credit = short_entry - wing_entry

    n_short = n_initial
    n_wing = n_initial
    cash = -entry_cf
    events = []
    pending_approach = None
    pending_breakout = None
    approach_armed = True

    daily = und[
        (und["date"] >= entry) & (und["date"] <= end_date)
    ].copy().reset_index(drop=True)
    if daily.empty:
        return None, "NO_UNDERLYING_WINDOW"

    exit_date = pd.Timestamp(daily.iloc[-1]["date"])
    exit_reason = "TIME_OR_EXPIRY"
    eq_rows = []

    for i, r in daily.iterrows():
        dt = pd.Timestamp(r["date"])
        acted_today = False

        qa = q_at(quotes, dt, aid)
        qs = q_at(quotes, dt, sid)
        qw = q_at(quotes, dt, wid)

        # State inputs available at today's close / daily high.
        short_delta = qs["delta"] if qs is not None else np.nan
        high = float(r["high"])
        close = float(r["close"])

        # ------------------------------------------------------------
        # Priority 0: downside package-loss governor.
        # ------------------------------------------------------------
        terminal_today = False
        if (
            mode == "STATE_MACHINE"
            and dt > entry
            and all(x is not None for x in (qa, qs, qw))
        ):
            ma0 = midpoint(qa)
            ms0 = midpoint(qs)
            mw0 = midpoint(qw)
            if all(pd.notna(x) for x in (ma0, ms0, mw0)):
                mtm_pnl = (
                    cash
                    + ma0 * 100.0
                    - n_short * ms0 * 100.0
                    + n_wing * mw0 * 100.0
                )
                stop_loss = DOWNSIDE_STOP_FRACTION * package_max_loss(
                    legs, n_initial
                )
                if stop_loss > 0.0 and mtm_pnl <= -stop_loss:
                    exit_date = dt
                    exit_reason = "DOWNSIDE_PACKAGE_STOP"
                    terminal_today = True
                    acted_today = True
                    events.append({
                        "date": str(dt.date()),
                        "event": "DOWNSIDE_PACKAGE_STOP",
                        "mtm_pnl_usd": float(mtm_pnl),
                        "stop_loss_usd": float(stop_loss),
                        "n_short": int(n_short),
                    })

        # ------------------------------------------------------------
        # Priority 0: downside package-loss governor.
        # If the package MTM drawdown reaches 50% of its own initial max-loss
        # proxy, terminate the package at this day's executable quotes.
        # ------------------------------------------------------------
        terminal_today = False
        if (
            mode == "STATE_MACHINE"
            and dt > entry
            and all(x is not None for x in (qa, qs, qw))
        ):
            ma0 = midpoint(qa)
            ms0 = midpoint(qs)
            mw0 = midpoint(qw)
            if all(pd.notna(x) for x in (ma0, ms0, mw0)):
                mtm_pnl = (
                    cash
                    + ma0 * 100.0
                    - n_short * ms0 * 100.0
                    + n_short * mw0 * 100.0
                )
                stop_loss = DOWNSIDE_STOP_FRACTION * package_max_loss(
                    legs, n_initial
                )
                if stop_loss > 0.0 and mtm_pnl <= -stop_loss:
                    exit_date = dt
                    exit_reason = "DOWNSIDE_PACKAGE_STOP"
                    terminal_today = True
                    acted_today = True
                    events.append({
                        "date": str(dt.date()),
                        "event": "DOWNSIDE_PACKAGE_STOP",
                        "mtm_pnl_usd": float(mtm_pnl),
                        "stop_loss_usd": float(stop_loss),
                        "n_short": int(n_short),
                    })

        # ------------------------------------------------------------
        # Priority 1: breakout confirmation governor.
        # A touch on T only arms a T+1 confirmation. This avoids using the
        # same day's intraday high as if the breakout were already confirmed.
        # ------------------------------------------------------------
        if (
            mode == "STATE_MACHINE"
            and (not terminal_today)
            and (not acted_today)
            and pending_breakout is not None
            and pd.Timestamp(pending_breakout["date"]) == dt
            and n_short > 0
        ):
            action = pending_breakout
            pending_breakout = None

            buy_short = executable(qs, "BUY")

            if pd.notna(buy_short):
                if close >= float(action["strike"]):
                    before = n_short
                    cash += (-before * buy_short) * 100.0
                    n_short = 0
                    events.append({
                        "date": str(dt.date()),
                        "event": "BREAKOUT_CONFIRMED_REMOVE_ALL_SHORT",
                        "touch_date": str(action["touch_date"].date()),
                        "touch_high": float(action["touch_high"]),
                        "next_close": close,
                        "n_short_before": before,
                        "n_short_closed": before,
                        "n_short_after": 0,
                        "n_wing_retained": n_wing,
                    })
                else:
                    before = n_short
                    cash += (-buy_short) * 100.0
                    n_short -= 1
                    events.append({
                        "date": str(dt.date()),
                        "event": "BREAKOUT_FAILED_REMOVE_ONE_SHORT",
                        "touch_date": str(action["touch_date"].date()),
                        "touch_high": float(action["touch_high"]),
                        "next_close": close,
                        "n_short_before": before,
                        "n_short_closed": 1,
                        "n_short_after": n_short,
                        "n_wing_retained": n_wing,
                    })
                acted_today = True
                approach_armed = False

        # Arm a next-day breakout confirmation on today's first touch.
        if (
            mode == "STATE_MACHINE"
            and (not terminal_today)
            and (not acted_today)
            and pending_breakout is None
            and n_short > 0
            and dt > entry
            and high >= float(legs["short"]["strike"])
        ):
            if i + 1 < len(daily):
                pending_approach = None
                pending_breakout = {
                    "date": pd.Timestamp(daily.iloc[i + 1]["date"]),
                    "touch_date": dt,
                    "touch_high": high,
                    "strike": float(legs["short"]["strike"]),
                }
                approach_armed = False

        # ------------------------------------------------------------
        # Priority 2: next-day decision from an earlier approach.
        # ------------------------------------------------------------
        if (
            mode == "STATE_MACHINE"
            and (not terminal_today)
            and (not acted_today)
            and pending_approach is not None
            and pd.Timestamp(pending_approach["date"]) == dt
            and n_short > 0
        ):
            action = pending_approach
            pending_approach = None

            if close >= float(action["approach_close"]):
                buy_short = executable(qs, "BUY")
                sell_wing = executable(qw, "SELL")
                if pd.notna(buy_short) and pd.notna(sell_wing):
                    before = n_short
                    cash += (-before * buy_short + before * sell_wing) * 100.0
                    n_short = 0
                    events.append({
                        "date": str(dt.date()),
                        "event": "CONTINUATION_REMOVE_ALL_PAIRS",
                        "approach_date": str(action["approach_date"].date()),
                        "approach_close": float(action["approach_close"]),
                        "next_close": close,
                        "n_before": before,
                        "n_closed": before,
                        "n_after": 0,
                    })
                    acted_today = True
            else:
                buy_short = executable(qs, "BUY")
                sell_wing = executable(qw, "SELL")
                if pd.notna(buy_short) and pd.notna(sell_wing):
                    pair_close_cost = buy_short - sell_wing
                    pair_profit = pair_credit - pair_close_cost
                    threshold = HARVEST_RECOVERY * pair_credit
                    if (
                        pair_credit > 0.0
                        and pair_profit >= threshold
                    ):
                        h = 1
                        before = n_short
                        cash += (-h * buy_short + h * sell_wing) * 100.0
                        n_short -= h
                        n_wing -= h
                        events.append({
                            "date": str(dt.date()),
                            "event": "REVERSAL_HARVEST_HALF_PAIRS",
                            "approach_date": str(action["approach_date"].date()),
                            "approach_close": float(action["approach_close"]),
                            "next_close": close,
                            "n_before": before,
                            "n_closed": h,
                            "n_after": n_short,
                            "n_wing_after": n_wing,
                            "pair_credit_usd": pair_credit * 100.0,
                            "pair_profit_usd": pair_profit * 100.0,
                            "threshold_usd": threshold * 100.0,
                        })
                        acted_today = True
                    else:
                        events.append({
                            "date": str(dt.date()),
                            "event": "REVERSAL_NO_HARVEST_THRESHOLD",
                            "approach_date": str(action["approach_date"].date()),
                            "approach_close": float(action["approach_close"]),
                            "next_close": close,
                            "pair_credit_usd": pair_credit * 100.0,
                            "pair_profit_usd": pair_profit * 100.0,
                            "threshold_usd": threshold * 100.0,
                        })
                        acted_today = True

            approach_armed = False

        # ------------------------------------------------------------
        # Priority 3: arm a new approach observation.
        # ------------------------------------------------------------
        if (
            mode == "STATE_MACHINE"
            and (not terminal_today)
            and (not acted_today)
            and pending_breakout is None
            and pending_approach is None
            and n_short > 0
            and dt > entry
        ):
            in_zone = (
                high >= APPROACH_FRAC * float(legs["short"]["strike"])
                or (pd.notna(short_delta) and short_delta >= APPROACH_DELTA)
            )
            if in_zone and approach_armed and i + 1 < len(daily):
                approach_armed = False
                pending_approach = {
                    "date": pd.Timestamp(daily.iloc[i + 1]["date"]),
                    "approach_date": dt,
                    "approach_close": close,
                }
            elif not in_zone:
                approach_armed = True

        # ------------------------------------------------------------
        # Priority 4: late delta governor, one pair at a time.
        # ------------------------------------------------------------
        if (
            mode == "STATE_MACHINE"
            and (not terminal_today)
            and (not acted_today)
            and n_short > 0
            and pd.notna(short_delta)
            and short_delta >= DANGER_DELTA
        ):
            buy_short = executable(qs, "BUY")
            sell_wing = executable(qw, "SELL")
            if pd.notna(buy_short) and pd.notna(sell_wing):
                before = n_short
                cash += (-buy_short + sell_wing) * 100.0
                n_short -= 1
                n_wing -= 1
                events.append({
                    "date": str(dt.date()),
                    "event": "LATE_DELTA_REMOVE_ONE_PAIR",
                    "n_before": before,
                    "n_closed": 1,
                    "n_after": n_short,
                    "n_wing_after": n_wing,
                    "short_delta": short_delta,
                })
                acted_today = True

        # ------------------------------------------------------------
        # Baseline whole-package touch exit.
        # ------------------------------------------------------------
        if mode == "BASELINE_TOUCH" and (not terminal_today) and dt > entry:
            if high >= float(legs["short"]["strike"]):
                exit_date = dt
                exit_reason = "SHORT_STRIKE_TOUCH"
                acted_today = True

        if dt >= end_date or i == len(daily) - 1:
            exit_date = dt
            if exit_reason == "TIME_OR_EXPIRY":
                exit_reason = "TIME_OR_EXPIRY"
            acted_today = True

        # Daily mark-to-mid drawdown observation.
        if all(x is not None for x in (qa, qs, qw)):
            ma = midpoint(qa)
            ms = midpoint(qs)
            mw = midpoint(qw)
            if all(pd.notna(x) for x in (ma, ms, mw)):
                eq = (
                    CAPITAL_USD
                    + cash
                    + ma * 100.0
                    - n_short * ms * 100.0
                    + n_wing * mw * 100.0
                )
                eq_rows.append((dt, eq))

        if (
            exit_reason in ("SHORT_STRIKE_TOUCH", "DOWNSIDE_PACKAGE_STOP")
            or dt >= end_date
        ):
            break

        if (
            mode == "STATE_MACHINE"
            and n_short == 0
            and dt < end_date
        ):
            # Continue tracking the ATM core until final exit.
            pass

    # Final exit must be an exact, executable quote date.
    exit_qdate = final_quote_date(quotes, exit_date, ids)
    if exit_qdate is None:
        return None, "NO_FINAL_QUOTES"

    qxa = q_at(quotes, exit_qdate, aid)
    qxs = q_at(quotes, exit_qdate, sid)
    qxw = q_at(quotes, exit_qdate, wid)

    sell_atm = executable(qxa, "SELL")
    buy_short = executable(qxs, "BUY")
    sell_wing = executable(qxw, "SELL")
    if any(pd.isna(x) for x in (sell_atm, buy_short, sell_wing)):
        return None, "NO_FINAL_QUOTES"

    exit_cf = (
        sell_atm
        - n_short * buy_short
        + n_wing * sell_wing
    ) * 100.0

    pnl = cash + exit_cf
    eq_rows.append((exit_qdate, CAPITAL_USD + pnl))

    return {
        "entry": entry,
        "exit": exit_qdate,
        "reason": (
            exit_reason if mode == "BASELINE_TOUCH"
            else "STATE_MACHINE_FINAL"
        ),
        "n_initial": int(n_initial),
        "n_short_final": int(n_short),
        "n_wing_final": int(n_wing),
        "atm_strike": float(legs["atm"]["strike"]),
        "short_strike": float(legs["short"]["strike"]),
        "wing_strike": float(legs["wing"]["strike"]),
        "entry_cashflow_usd": float(entry_cf),
        "pnl_usd": float(pnl),
        "max_loss_proxy_usd": float(package_max_loss(legs, n_initial)),
        "events": events,
        "breakout_events": sum(
            e["event"] in (
                "BREAKOUT_CONFIRMED_REMOVE_ALL_SHORT",
                "BREAKOUT_FAILED_REMOVE_ONE_SHORT",
            )
            for e in events
        ),
        "continuation_events": sum(
            e["event"] == "CONTINUATION_REMOVE_ALL_PAIRS"
            for e in events
        ),
        "harvest_events": sum(e["event"] == "REVERSAL_HARVEST_HALF_PAIRS" for e in events),
        "delta_reduce_events": sum(e["event"] == "LATE_DELTA_REMOVE_ONE_PAIR" for e in events),
        "downside_stop_events": sum(e["event"] == "DOWNSIDE_PACKAGE_STOP" for e in events),
        "eq_rows": eq_rows,
    }, "OK"


def run_one(und, quotes, selection, risk_budget, mode):
    signals = und[und["signal"] & und["dma200"].notna()].copy()
    trades = []
    rejects = {}
    next_allowed = None

    for _, row in signals.iterrows():
        entry = pd.Timestamp(row["date"])
        if next_allowed is not None and entry <= next_allowed:
            continue

        legs = selection.get(entry)
        if legs is None:
            rejects["NO_SELECTION"] = rejects.get("NO_SELECTION", 0) + 1
            continue

        n_initial = choose_initial_n(legs, risk_budget)
        if n_initial <= 0:
            rejects["RISK_GATE"] = rejects.get("RISK_GATE", 0) + 1
            continue

        tr, status = manage_trade(und, quotes, row, legs, n_initial, mode)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue

        trades.append(tr)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    if not trades:
        return [], {
            "mode": mode,
            "risk_budget": risk_budget,
            "trades": 0,
            "rejections": rejects,
        }, pd.DataFrame()

    trdf = pd.DataFrame([
        {k: v for k, v in t.items() if k not in ("events", "eq_rows")}
        for t in trades
    ]).sort_values("entry").reset_index(drop=True)

    points = [p for t in trades for p in t["eq_rows"]]
    eqdf = pd.DataFrame(points, columns=["date", "equity"])
    eqdf["date"] = pd.to_datetime(eqdf["date"])
    eqdf = (
        eqdf.sort_values("date")
            .groupby("date", as_index=False)["equity"]
            .last()
    )
    eqdf["peak"] = eqdf["equity"].cummax()
    eqdf["dd"] = eqdf["equity"] / eqdf["peak"] - 1.0

    final_equity = CAPITAL_USD + trdf["pnl_usd"].sum()
    years = max(
        (trdf["exit"].iloc[-1] - trdf["entry"].iloc[0]).days / 365.25,
        1 / 365.25,
    )
    total_return = final_equity / CAPITAL_USD - 1.0
    cagr = (
        (1.0 + total_return) ** (1.0 / years) - 1.0
        if 1.0 + total_return > 0
        else -1.0
    )

    n_hist = trdf["n_initial"].value_counts().sort_index().to_dict()

    stats = {
        "mode": mode,
        "risk_budget": float(risk_budget),
        "trades": int(len(trdf)),
        "win_rate": float((trdf["pnl_usd"] > 0).mean()),
        "avg_trade_usd": float(trdf["pnl_usd"].mean()),
        "worst_trade_usd": float(trdf["pnl_usd"].min()),
        "best_trade_usd": float(trdf["pnl_usd"].max()),
        "total_return": float(total_return),
        "cagr": float(cagr),
        "maxdd_daily_mtm": float(eqdf["dd"].min()),
        "maxdd_realized": float(
            (
                trdf["pnl_usd"].cumsum().add(CAPITAL_USD)
                / trdf["pnl_usd"].cumsum().add(CAPITAL_USD).cummax()
                - 1.0
            ).min()
        ),
        "years": float(years),
        "initial_N_distribution": n_hist,
        "breakout_events": int(trdf["breakout_events"].sum()),
        "continuation_events": int(trdf["continuation_events"].sum()),
        "harvest_events": int(trdf["harvest_events"].sum()),
        "delta_reduce_events": int(trdf["delta_reduce_events"].sum()),
        "downside_stop_events": int(trdf["downside_stop_events"].sum()),
        "rejections": rejects,
        "data_start": str(trdf["entry"].min().date()),
        "data_end": str(trdf["exit"].max().date()),
    }
    return trades, stats, eqdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)

    opt_path, und_path = ensure_data(data_dir)
    und = load_underlying(und_path)

    print("OPTIONS_SHA256", sha256_file(opt_path), flush=True)
    print("UNDERLYING_SHA256", sha256_file(und_path), flush=True)
    print(
        "UNDERLYING_RANGE",
        und["date"].min().date(),
        und["date"].max().date(),
        "ROWS",
        len(und),
        flush=True,
    )

    signal_dates = [pd.Timestamp(x) for x in und.loc[und["signal"], "date"]]
    con = duckdb.connect()
    selection, sel_rejects = select_contracts(con, opt_path, signal_dates)
    print(
        "SIGNALS",
        len(signal_dates),
        "SELECTIONS",
        len(selection),
        "SELECTION_REJECTS",
        sel_rejects,
        flush=True,
    )

    quotes = fetch_quotes(con, opt_path, selection)
    print("QUOTE_ROWS", len(quotes), flush=True)

    all_stats = []
    for risk_budget in RISK_BUDGETS:
        for mode in ("BASELINE_TOUCH", "STATE_MACHINE"):
            print(
                f"RUN risk={risk_budget:.2%} mode={mode}",
                flush=True,
            )
            trades, stats, eqdf = run_one(
                und, quotes, selection, risk_budget, mode
            )
            all_stats.append(stats)

            if trades:
                pd.DataFrame([
                    {
                        **{
                            k: v for k, v in t.items()
                            if k not in ("events", "eq_rows")
                        },
                        "events_json": json.dumps(
                            t["events"],
                            ensure_ascii=False,
                        ),
                    }
                    for t in trades
                ]).to_csv(
                    out / (
                        f"trades_risk{int(risk_budget*100)}pct_"
                        f"{mode}.csv"
                    ),
                    index=False,
                )
            if not eqdf.empty:
                eqdf.to_csv(
                    out / (
                        f"equity_risk{int(risk_budget*100)}pct_"
                        f"{mode}.csv"
                    ),
                    index=False,
                )

    report = {
        "research_contract": {
            "strategy": "1 ATM Long Call + N OTM Short Calls + N Far OTM Long Wings",
            "breakout_variation": "confirmed breakout removes all SHORT only; failed breakout removes one SHORT only; all WINGs are retained",
            "variation": "same V6 rules, but breakout actions close SHORT calls only and retain all wings",
            "N_selection": f"largest N in 1..{N_MAX} passing exact terminal max-loss risk gate",
            "risk_budgets": list(RISK_BUDGETS),
            "signal": "QQQ close/52-week high >= 0.98 AND close/200DMA - 1 >= 0.08",
            "cooldown_days": COOLDOWN_DAYS,
            "expiry_window_dte": [DTE_MIN, DTE_MAX],
            "max_hold_days": HOLD_MAX,
            "short_delta_entry": SHORT_DELTA_ENTRY,
            "wing_delta_entry": WING_DELTA_ENTRY,
            "approach": (
                f"High >= {APPROACH_FRAC:.2f}*short strike OR "
                f"observed short delta >= {APPROACH_DELTA:.2f}"
            ),
            "harvest": (
                "next-day reversal plus executable pair profit >= "
                f"{HARVEST_RECOVERY:.0%} of initial pair credit -> "
                "close exactly ONE paired short+wing unit"
            ),
            "continuation": (
                "next-day Close >= approach-day Close -> "
                "close all remaining paired short+wing units; keep ATM"
            ),
            "breakout_confirmation": (
                "High >= short strike on T arms T+1 confirmation; "
                "if Close[T+1] >= strike, close all remaining SHORT calls only; "
                "otherwise close exactly one SHORT call; retain all WINGs"
            ),
            "late_delta_governor": (
                f"observed short delta >= {DANGER_DELTA:.2f} -> "
                "close exactly one paired unit"
            ),
            "downside_governor": (
                f"daily package MTM P&L <= -{DOWNSIDE_STOP_FRACTION:.0%} "
                "of initial package max-loss proxy -> liquidate whole package"
            ),
            "no_readd": True,
            "baseline": "same dynamic entry N, whole package exits on first short-strike touch",
            "entry_execution": "ATM Ask / Short Bid / Wing Ask",