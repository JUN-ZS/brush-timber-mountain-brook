from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_spy_bounded_crossover_reanchor_v1 import (
    START,
    END,
    TD,
    load_px,
    get_chain,
    liquid,
    unit_marks,
    weekly_observation_days,
    prev_trading_date,
    atm_iv60_series,
)


LONG_DTE = 180
LONG_ROLL_DTE = 60
SHORT_DTES = [7, 14, 21, 30]
SHORT_DELTA = 0.10
OBS_WEEKS = 26
MIN_FACTORS = 12
MAX_N = 12
NAV0 = 100000.0
THETA_FLOOR = 0.0
NET_DELTA_TOL = 0.15


def sql(con, s):
    return con.execute(s).df()


def pathq(p):
    return str(p).replace("'", "''")


def bs_greeks(spot, strike, dte, iv, rate=0.0, div=0.012, call=True):
    if not all(np.isfinite(x) for x in [spot, strike, dte, iv]) or spot <= 0 or strike <= 0 or dte <= 0 or iv <= 0:
        return None
    t = dte / 365.25
    sqt = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * iv * iv) * t) / (iv * sqt)
    d2 = d1 - iv * sqt
    n = math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    N = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    Nd2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    delta = math.exp(-div * t) * N if call else math.exp(-div * t) * (N - 1.0)
    gamma = math.exp(-div * t) * n / (spot * iv * sqt)
    vega = spot * math.exp(-div * t) * n * sqt
    theta = (
        -spot * math.exp(-div * t) * n * iv / (2.0 * sqt)
        - rate * strike * math.exp(-rate * t) * Nd2
        + div * spot * math.exp(-div * t) * N
    ) if call else (
        -spot * math.exp(-div * t) * n * iv / (2.0 * sqt)
        + rate * strike * math.exp(-rate * t) * (1.0 - Nd2)
        - div * spot * math.exp(-div * t) * (1.0 - N)
    )
    return {
        "delta": delta,
        "gamma": gamma,
        "vega_per_vol1": vega,
        "theta_day": theta / 365.25,
    }


def select_call(con, path, date, target_dte, target_delta):
    df = get_chain(con, path, date, max(2, target_dte - 5), target_dte + 5)
    if df.empty:
        return None
    x = liquid(df[df.opt_type == "call"]).copy()
    if x.empty:
        return None
    x["dte"] = (pd.to_datetime(x.expiration) - date).dt.days
    x = x[(x.dte >= max(1, target_dte - 5)) & (x.dte <= target_dte + 5)]
    if x.empty:
        return None
    row = x.iloc[(x.delta - target_delta).abs().argmin()]
    if not np.isfinite(float(row.implied_volatility)) or float(row.implied_volatility) <= 0:
        return None
    return {
        "contract_id": str(row.contract_id),
        "expiry": pd.Timestamp(row.expiration),
        "strike": float(row.strike),
        "iv": float(row.implied_volatility),
        "delta": float(row.delta),
        "bid": float(row.bid),
        "ask": float(row.ask),
        "dte": int(row.dte),
    }


def build_factor_history(con, underlying_path, option_path, weekly_days):
    px = load_px(con, underlying_path, "S")
    px = px[["date", "S_px"]].copy()
    px["week"] = px.date.dt.to_period("W-SUN")
    weekly = px.groupby("week", as_index=False).last()
    weekly["ret"] = weekly.S_px.pct_change()

    signal_dates = [prev_trading_date(px.date.tolist(), d) for d in weekly_days]
    signal_dates = [d for d in signal_dates if d is not None]
    ivmap = atm_iv60_series(con, option_path, signal_dates)

    rows = []
    for d in signal_dates:
        iv = ivmap.get(pd.Timestamp(d), np.nan)
        spot = float(px.loc[px.date == pd.Timestamp(d), "S_px"].iloc[-1]) if (px.date == pd.Timestamp(d)).any() else np.nan
        rows.append({"date": pd.Timestamp(d), "spot": spot, "atm_iv": iv})

    z = pd.DataFrame(rows).sort_values("date")
    if z.empty:
        return z
    z["ret"] = z.spot.pct_change()
    z["d_iv"] = z.atm_iv.diff()
    z["ret2"] = z.ret ** 2
    return z.dropna(subset=["ret", "d_iv", "ret2"]).reset_index(drop=True)


def covariance_matrix(history, current_date):
    if history.empty:
        return np.eye(3)
    h = history[history.date < current_date].tail(OBS_WEEKS)
    if len(h) < MIN_FACTORS:
        return np.eye(3)
    f = h[["ret", "d_iv", "ret2"]].to_numpy(float)
    cov = np.cov(f, rowvar=False)
    cov = np.nan_to_num(cov, nan=0.0, posinf=0.0, neginf=0.0)
    cov += np.eye(3) * max(float(np.trace(cov)) * 1e-6, 1e-10)
    return cov


def exposure(option, spot):
    g = bs_greeks(spot, option["strike"], option["dte"], option["iv"])
    if g is None:
        return None
    # P&L approximation per factor unit:
    # [underlying return, 1.00 IV-point change, squared return shock].
    e1 = g["delta"] * spot * 100.0
    e2 = g["vega_per_vol1"] * 0.01 * 100.0
    e3 = 0.5 * g["gamma"] * (spot ** 2) * 100.0
    theta = g["theta_day"] * 100.0
    return {
        "delta_dollar": e1,
        "vega_1pct_dollar": e2,
        "gamma_return2_dollar": e3,
        "theta_day_dollar": theta,
        "vec": np.array([e1, e2, e3], dtype=float),
        "delta": g["delta"],
    }


def delta_ratio(long_e, short_e):
    if short_e is None or long_e is None:
        return np.nan
    den = abs(short_e["delta_dollar"])
    return abs(long_e["delta_dollar"]) / den if den > 0 else np.nan


def mv_ratio(long_e, short_e, cov):
    if long_e is None or short_e is None:
        return np.nan
    a = long_e["vec"]
    b = short_e["vec"]
    den = float(b @ cov @ b)
    if den <= 0:
        return np.nan
    return float((b @ cov @ a) / den)


def choose_n(long_e, short_e, cov):
    nd = delta_ratio(long_e, short_e)
    nmv = mv_ratio(long_e, short_e, cov)
    candidates = []
    if not np.isfinite(nmv):
        nmv = nd
    base = float(np.clip(nmv, 0.0, MAX_N))
    # "Balance point": among nearby integer quantities, require non-negative theta
    # and choose the smallest variance residual. If none satisfies theta, use the
    # integer with smallest variance without the theta constraint.
    nearby = sorted(set(
        int(np.clip(round(base) + k, 1, MAX_N))
        for k in (-2, -1, 0, 1, 2)
    ))
    for n in nearby:
        residual = long_e["vec"] - n * short_e["vec"]
        var = float(residual @ cov @ residual)
        theta = long_e["theta_day_dollar"] - n * short_e["theta_day_dollar"]
        net_delta = long_e["delta_dollar"] - n * short_e["delta_dollar"]
        candidates.append((n, var, theta, net_delta))
    feasible = [x for x in candidates if x[2] >= THETA_FLOOR]
    pool = feasible if feasible else candidates
    best = min(pool, key=lambda x: x[1])
    return {
        "n_delta": nd,
        "n_mv": nmv,
        "n_balanced": int(best[0]),
        "residual_var": float(best[1]),
        "net_theta": float(best[2]),
        "net_delta_dollar": float(best[3]),
        "theta_feasible": bool(best[2] >= THETA_FLOOR),
    }


def option_cashflow_position(symbol, option, qty, side):
    # side +1 = long, -1 = short
    px = option["ask"] if side > 0 else option["bid"]
    return {
        "symbol": symbol,
        "contract_id": option["contract_id"],
        "entry": option["entry_date"],
        "expiry": option["expiry"],
        "strike": option["strike"],
        "side": side,
        "qty": float(qty),
        "entry_px": float(px),
        "cashflow": -side * float(px) * 100.0 * float(qty),
        "risk_diagnostic": "unbounded_short_call" if side < 0 else "long_premium",
    }


def marks_for_positions(con, option_path, positions):
    if not positions:
        return pd.DataFrame()
    ids = [p["contract_id"] for p in positions]
    vals = ",".join("'" + x.replace("'", "''") + "'" for x in sorted(set(ids)))
    d = sql(con, f"""
        SELECT CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(date AS DATE) AS date,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               CAST((bid+ask)/2.0 AS DOUBLE) AS mark
        FROM read_parquet('{pathq(option_path)}')
        WHERE contract_id IN ({vals})
        ORDER BY date
    """)
    if not d.empty:
        d.date = pd.to_datetime(d.date)
    return d


def position_value(p, row, exit=False):
    if row is None:
        return np.nan
    px = float(row.ask if (exit and p["side"] < 0) or (not exit and p["side"] < 0) else row.bid if exit else row.mark)
    # Above resolves:
    # long MTM/exit -> bid, short MTM -> mark, short exit -> ask.
    if not exit:
        px = float(row.mark)
    elif p["side"] > 0:
        px = float(row.bid)
    else:
        px = float(row.ask)
    return p["cashflow"] + p["side"] * px * 100.0 * p["qty"]


def run_strategy(con, state_dates, factor_hist, option_path, name, short_dte):
    long_pos = None
    short_pos = []
    event_positions = []
    nav = NAV0
    realized = 0.0
    rows = []
    balance_rows = []

    date_list = [pd.Timestamp(d) for d in state_dates]
    weekly_set = set(date_list)
    px_dates = load_px(con, option_path.replace("_options.parquet", "_underlying.parquet"), "S")["date"] if False else None

    qpath = option_path
    # Use underlying from caller via state_dates only for spot lookup below.
    spot_df = None

    # Preselect weekly options at observation dates.
    books = {}
    for d in date_list:
        long_roll = long_pos is None or (pd.Timestamp(long_pos["expiry"]) - d).days <= LONG_ROLL_DTE
        if long_roll:
            books.setdefault(d, {})["long"] = True
        books.setdefault(d, {})["short"] = True

    current_long = None
    short_book = []
    all_positions = []
    events = {}

    for d in date_list:
        if d not in events:
            events[d] = []

        if current_long is None or (current_long["expiry"] - d).days <= LONG_ROLL_DTE:
            opt = select_call(con, qpath, d, LONG_DTE, 0.50)
            if opt is not None:
                opt["entry_date"] = d
                if current_long is not None:
                    events[d].append(("CLOSE", current_long))
                p = option_cashflow_position("SPY", opt, 1, +1)
                current_long = p
                current_long["entry_option"] = opt
                events[d].append(("OPEN", current_long))

        # Short side is rolled weekly to a fresh DTE. Close any existing short book.
        for p in short_book:
            events[d].append(("CLOSE", p))
        short_book = []

        if current_long is None:
            continue

        spot = get_spot(con, d)
        if not np.isfinite(spot):
            continue
        lopt = current_long["entry_option"].copy()
        lopt["dte"] = max((pd.Timestamp(current_long["expiry"]) - d).days, 1)
        le = exposure(lopt, spot)
        sopt = select_call(con, qpath, d, short_dte, SHORT_DELTA)
        if sopt is None or le is None:
            continue
        se = exposure({**sopt, "dte": short_dte}, spot)
        cov = covariance_matrix(factor_hist, d)
        bal = choose_n(le, se, cov)

        n = bal["n_balanced"]
        # Cap at MAX_N and always use whole contracts.
        sopt["entry_date"] = d
        for _ in range(n):
            p = option_cashflow_position("SPY", sopt, 1, -1)
            p["entry_option"] = sopt
            short_book.append(p)
            events[d].append(("OPEN", p))

        balance_rows.append({
            "date": d,
            "short_dte": short_dte,
            "n_delta": bal["n_delta"],
            "n_mv": bal["n_mv"],
            "n_balanced": n,
            "residual_var": bal["residual_var"],
            "net_theta": bal["net_theta"],
            "net_delta_dollar": bal["net_delta_dollar"],
            "theta_feasible": bal["theta_feasible"],
            "long_delta": le["delta"],
            "short_delta": se["delta"],
            "long_dollar_delta": le["delta_dollar"],
            "short_dollar_delta": se["delta_dollar"],
        })

    # Flatten positions and fetch marks.
    all_positions = []
    for d in events:
        for action, p in events[d]:
            if p not in all_positions:
                all_positions.append(p)
    marks = marks_for_positions(con, qpath, all_positions)
    mk = {(r.contract_id, r.date): r for r in marks.itertuples(index=False)}

    # Daily valuation grid from first to last weekly observation.
    days = pd.date_range(min(date_list), max(date_list), freq="B")
    active = []
    cash = NAV0
    closed_pnl = 0.0
    bal_by_day = {r["date"]: r for r in balance_rows}

    for d in days:
        d = pd.Timestamp(d)
        for action, p in events.get(d, []):
            if action != "CLOSE":
                continue
            row = mk.get((p["contract_id"], d))
            if row is None:
                continue
            v = position_value(p, row, exit=True)
            closed_pnl += v
            if p in active:
                active.remove(p)

        for action, p in events.get(d, []):
            if action != "OPEN":
                continue
            active.append(p)

        mtm = 0.0
        for p in active:
            row = mk.get((p["contract_id"], d))
            if row is not None:
                mtm += position_value(p, row, exit=False)
        eq = NAV0 + closed_pnl + mtm
        rows.append({"date": d, "eq": eq})

    e = pd.DataFrame(rows)
    if e.empty:
        return {}, pd.DataFrame(), pd.DataFrame()

    ending = float(e["eq"].iloc[-1])
    years = max((e.date.iloc[-1] - e.date.iloc[0]).days / 365.25, 1 / 365.25)
    cagr = (ending / NAV0) ** (1 / years) - 1
    dd = float((e["eq"] / e["eq"].cummax() - 1).min())
    rr = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sharpe = float(rr.mean() / rr.std(ddof=1) * math.sqrt(252)) if rr.std(ddof=1) > 0 else 0.0

    br = pd.DataFrame(balance_rows)
    result = {
        "strategy": name,
        "short_dte": short_dte,
        "cycles": len(balance_rows),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": dd,
        "sharpe": sharpe,
        "mean_n_delta": float(br.n_delta.mean()) if not br.empty else np.nan,
        "mean_n_mv": float(br.n_mv.mean()) if not br.empty else np.nan,
        "mean_n_balanced": float(br.n_balanced.mean()) if not br.empty else np.nan,
        "median_n_balanced": float(br.n_balanced.median()) if not br.empty else np.nan,
        "theta_feasible_pct": float(br.theta_feasible.mean()) if not br.empty else np.nan,
        "mean_net_theta": float(br.net_theta.mean()) if not br.empty else np.nan,
        "mean_abs_net_delta": float(br.net_delta_dollar.abs().mean()) if not br.empty else np.nan,
    }
    return result, e, br


def get_spot(con, d):
    return np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = Path(a.data_dir)
    o = Path(a.out)
    o.mkdir(parents=True, exist_ok=True)

    option_path = str(d / "SPY_options.parquet")
    underlying_path = str(d / "SPY_underlying.parquet")
    for p in [option_path, underlying_path]:
        assert Path(p).exists(), p

    con = duckdb.connect()
    px = load_px(con, underlying_path, "S")
    days = weekly_observation_days(px)
    days = [pd.Timestamp(x) for x in days if START <= x.strftime("%Y-%m-%d") <= END]
    spot_map = {pd.Timestamp(r.date): float(r.S_px) for r in px.itertuples(index=False)}
    global _SPOT_MAP
    _SPOT_MAP = spot_map

    factor_hist = build_factor_history(con, underlying_path, option_path, days)
    factor_hist.to_csv(o / "factor_history.csv", index=False)

    results = []
    curves = []
    balances = []
    for sd in SHORT_DTES:
        for mode in ["BALANCED"]:
            rr, eq, br = run_strategy(con, days, factor_hist, option_path, f"SPY_LONG1_SHORT_BALANCED_{sd}D", sd)
            if rr:
                results.append(rr)
                eq["strategy"] = rr["strategy"]
                curves.append(eq)
                br["strategy"] = rr["strategy"]
                balances.append(br)

    # Delta-ratio reference is computed but not separately traded here; the
    # artifact contains N_delta vs N_MV vs final integer balance N side-by-side.
    pd.DataFrame(results).to_csv(o / "results.csv", index=False)
    if curves:
        pd.concat(curves, ignore_index=True).to_csv(o / "equity.csv", index=False)
    if balances:
        pd.concat(balances, ignore_index=True).to_csv(o / "balance_points.csv", index=False)

    methodology = {
        "definition": "Balance point = integer N of short calls that minimizes one-step residual option-P&L variance using causal factor covariance, subject to non-negative net theta when feasible.",
        "online_baseline": "Delta-neutral ratio N_delta = dollar delta(long)/dollar delta(short). Ratio-call sources commonly use combined delta to select contract count.",
        "smart_ratio": "Minimum-variance Greek ratio N_MV = (b' Sigma a)/(b' Sigma b), with a=long [delta,vega,gamma] factor exposure and b=short exposure.",
        "factor_covariance": "Past 26 weekly observations of SPY return, ATM-IV60 change, and squared return; current observation excluded.",
        "structure": "1 SPY long ~50-delta call around 180 DTE; weekly rolled SPY short ~10-delta calls at 7/14/21/30 DTE.",
        "chasing": "Short book is closed and rebuilt weekly; long call rolls when <=60 DTE.",
        "fills": "Long opens at ask and exits at bid; shorts open at bid and exit at ask; daily MTM at mid.",
        "integer_contracts": True,
        "max_short_calls": MAX_N,
        "uncovered_short_tail": True,
        "no_live_orders": True,
        "no_parameter_search": True,
    }
    (o / "METHODOLOGY.json").write_text(json.dumps(methodology, indent=2), encoding="utf-8")

    lines = [
        "# SPY Long-1 / Multi-Short-Call Balance Point V1",
        "",
        "The experiment directly tests the public ratio-spread idea, then replaces fixed N with a causal minimum-variance Greek balance.",
        "",
        "| strategy | short DTE | cycles | ending NAV | CAGR | MaxDD | Sharpe | mean N_delta | mean N_MV | mean N_balanced | theta-feasible |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['strategy']} | {r['short_dte']} | {r['cycles']} | {r['ending_nav']:.2f} | "
            f"{r['cagr']:.2%} | {r['maxdd']:.2%} | {r['sharpe']:.2f} | "
            f"{r['mean_n_delta']:.2f} | {r['mean_n_mv']:.2f} | {r['mean_n_balanced']:.2f} | "
            f"{r['theta_feasible_pct']:.1%} |"
        )
    (o / "RESULTS.md").write_text("\\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
