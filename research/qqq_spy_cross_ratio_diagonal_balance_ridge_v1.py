from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_spy_bounded_crossover_reanchor_v1 import (
    START,
    END,
    load_px,
    liquid,
    weekly_observation_days,
    prev_trading_date,
    atm_iv60_series,
)

NAV0 = 100000.0
LONG_DTES = [90, 180]
SHORT_DTES = [7, 14, 21, 30]
TARGET_LONG_DELTA = 0.50
TARGET_SHORT_DELTA = 0.10
MAX_N = 8
HEDGE_LOOKBACK = 26
MIN_HEDGE_SAMPLES = 12
THETA_TOL = 0.0


def sql(con, s):
    return con.execute(s).df()


def pathq(p):
    return str(p).replace("'", "''")


def bs_greeks(spot, strike, dte, iv, call=True, rate=0.0, div=0.012):
    if not all(np.isfinite(v) for v in [spot, strike, dte, iv]) or spot <= 0 or strike <= 0 or dte <= 0 or iv <= 0:
        return None
    t = dte / 365.25
    sqt = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * iv * iv) * t) / (iv * sqt)
    d2 = d1 - iv * sqt
    pdf = math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    cdf1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
    cdf2 = 0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0)))
    if call:
        delta = math.exp(-div * t) * cdf1
        theta_year = (
            -spot * math.exp(-div * t) * pdf * iv / (2.0 * sqt)
            - rate * strike * math.exp(-rate * t) * cdf2
            + div * spot * math.exp(-div * t) * cdf1
        )
    else:
        delta = math.exp(-div * t) * (cdf1 - 1.0)
        theta_year = (
            -spot * math.exp(-div * t) * pdf * iv / (2.0 * sqt)
            + rate * strike * math.exp(-rate * t) * (1.0 - cdf2)
            - div * spot * math.exp(-div * t) * (1.0 - cdf1)
        )
    gamma = math.exp(-div * t) * pdf / (spot * iv * sqt)
    vega = spot * math.exp(-div * t) * pdf * sqt
    return {
        "delta": delta,
        "gamma": gamma,
        "vega_per_vol1": vega,
        "theta_day": theta_year / 365.25,
    }


def preselect_calls(con, option_paths, dates):
    """
    Build the exact call-selection universe needed by this research in two
    parquet scans (one per underlying), rather than rescanning a parquet file
    for every configuration/date.
    """
    targets = []
    for d in sorted(pd.Timestamp(x) for x in dates):
        ds = d.strftime("%Y-%m-%d")
        for td in sorted(set(LONG_DTES + SHORT_DTES)):
            targets.append((ds, int(td), float(TARGET_LONG_DELTA)))
            targets.append((ds, int(td), float(TARGET_SHORT_DELTA)))
    values_sql = ",".join(
        f"(DATE '{ds}', {td}, {delta:.8f})" for ds, td, delta in targets
    )
    out = {}
    for asset, path in option_paths.items():
        q = sql(
            con,
            f"""
            WITH targets(date, target_dte, target_delta) AS (
                VALUES {values_sql}
            ),
            eligible AS (
                SELECT
                    CAST(o.contract_id AS VARCHAR) AS contract_id,
                    CAST(o.date AS DATE) AS date,
                    CAST(o.expiration AS DATE) AS expiration,
                    CAST(o.strike AS DOUBLE) AS strike,
                    CAST(o.bid AS DOUBLE) AS bid,
                    CAST(o.ask AS DOUBLE) AS ask,
                    CAST(o.delta AS DOUBLE) AS delta,
                    CAST(o.implied_volatility AS DOUBLE) AS iv,
                    t.target_dte,
                    t.target_delta,
                    date_diff(
                        'day',
                        CAST(o.date AS DATE),
                        CAST(o.expiration AS DATE)
                    ) AS dte_calc,
                    (CAST(o.ask AS DOUBLE) - CAST(o.bid AS DOUBLE))
                    / NULLIF(
                        (CAST(o.ask AS DOUBLE) + CAST(o.bid AS DOUBLE)) / 2.0,
                        0
                    ) AS spr
                FROM read_parquet('{pathq(path)}') o
                JOIN targets t
                  ON CAST(o.date AS DATE) = t.date
                WHERE LOWER(o."type") = 'call'
                  AND CAST(o.expiration AS DATE) > CAST(o.date AS DATE)
                  AND date_diff(
                        'day',
                        CAST(o.date AS DATE),
                        CAST(o.expiration AS DATE)
                      ) >= GREATEST(2, t.target_dte - 7)
                  AND date_diff(
                        'day',
                        CAST(o.date AS DATE),
                        CAST(o.expiration AS DATE)
                      ) <= t.target_dte + 7
                  AND o.bid IS NOT NULL
                  AND o.ask IS NOT NULL
                  AND o.ask >= o.bid
                  AND o.ask > 0
                  AND o.delta IS NOT NULL
                  AND (o.open_interest >= 10 OR o.volume >= 5)
            ),
            liquid AS (
                SELECT *
                FROM eligible
                WHERE isfinite(spr)
                  AND spr <= 0.35
            ),
            ranked AS (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY date, target_dte, target_delta
                           ORDER BY ABS(delta - target_delta),
                                    expiration,
                                    strike,
                                    contract_id
                       ) AS rn
                FROM liquid
                WHERE iv IS NOT NULL
            )
            SELECT contract_id, date, expiration, strike, bid, ask, delta, iv,
                   dte_calc, target_dte, target_delta
            FROM ranked
            WHERE rn = 1
            ORDER BY date, target_dte, target_delta
            """,
        )
        for r in q.itertuples(index=False):
            iv = float(r.iv)
            if not np.isfinite(iv) or iv <= 0:
                continue
            out[(asset, pd.Timestamp(r.date), int(r.target_dte), float(r.target_delta))] = {
                "contract_id": str(r.contract_id),
                "expiry": pd.Timestamp(r.expiration),
                "strike": float(r.strike),
                "iv": iv,
                "delta": float(r.delta),
                "bid": float(r.bid),
                "ask": float(r.ask),
                "dte": int(r.dte_calc),
            }
    return out

def weekly_dates(con, underlying_path):
    px = load_px(con, underlying_path, "S")
    return [pd.Timestamp(x) for x in weekly_observation_days(px)
            if START <= x.strftime("%Y-%m-%d") <= END]


def build_factor_history(con, q_underlying, s_underlying, q_options, s_options, dates):
    q = load_px(con, q_underlying, "Q")[["date", "Q_px"]].copy()
    s = load_px(con, s_underlying, "S")[["date", "S_px"]].copy()
    x = q.merge(s, on="date", how="inner").sort_values("date")
    x["q_ret"] = np.log(x.Q_px / x.Q_px.shift(1))
    x["s_ret"] = np.log(x.S_px / x.S_px.shift(1))

    state_dates = sorted(pd.to_datetime(x.date).tolist())
    signal_dates = [prev_trading_date(state_dates, d) for d in dates]
    signal_dates = [d for d in signal_dates if d is not None]
    qiv = atm_iv60_series(con, q_options, signal_dates)
    siv = atm_iv60_series(con, s_options, signal_dates)

    rows = []
    for d in signal_dates:
        r = x.loc[x.date == pd.Timestamp(d)].iloc[-1]
        rows.append({
            "date": pd.Timestamp(d),
            "q_ret": float(r.q_ret) if pd.notna(r.q_ret) else np.nan,
            "s_ret": float(r.s_ret) if pd.notna(r.s_ret) else np.nan,
            "q_iv": qiv.get(pd.Timestamp(d), np.nan),
            "s_iv": siv.get(pd.Timestamp(d), np.nan),
        })
    z = pd.DataFrame(rows).sort_values("date")
    if z.empty:
        return z
    z["q_div"] = z.q_ret ** 2
    z["s_div"] = z.s_ret ** 2
    z["dq_iv"] = z.q_iv.diff()
    z["ds_iv"] = z.s_iv.diff()
    return z.dropna(subset=["q_ret", "s_ret", "q_div", "s_div"]).reset_index(drop=True)


def covariance_for_date(hist, d):
    if hist.empty:
        return np.eye(6)
    h = hist[hist.date < d].tail(HEDGE_LOOKBACK)
    if len(h) < MIN_HEDGE_SAMPLES:
        return np.eye(6)
    f = h[["q_ret", "s_ret", "dq_iv", "ds_iv", "q_div", "s_div"]].copy()
    f = f.replace([np.inf, -np.inf], np.nan).dropna()
    if len(f) < MIN_HEDGE_SAMPLES:
        return np.eye(6)
    cov = np.cov(f.to_numpy(float), rowvar=False)
    cov = np.nan_to_num(cov, nan=0.0, posinf=0.0, neginf=0.0)
    trace = max(float(np.trace(cov)), 1e-10)
    cov += np.eye(6) * trace * 1e-6
    return cov


def option_exposure(option, spot, asset):
    g = bs_greeks(spot, option["strike"], option["dte"], option["iv"], call=True)
    if g is None:
        return None
    scale_delta = g["delta"] * spot * 100.0
    scale_vega = g["vega_per_vol1"] * 0.01 * 100.0
    scale_gamma = 0.5 * g["gamma"] * spot * spot * 100.0
    theta = g["theta_day"] * 100.0
    vec = np.zeros(6, dtype=float)
    if asset == "QQQ":
        vec[0] = scale_delta
        vec[2] = scale_vega
        vec[4] = scale_gamma
    else:
        vec[1] = scale_delta
        vec[3] = scale_vega
        vec[5] = scale_gamma
    return {
        "vec": vec,
        "theta": theta,
        "delta_dollar": scale_delta,
        "delta": g["delta"],
    }


def balance_ridge(long_e, short_e, cov):
    a = long_e["vec"]
    b = short_e["vec"]
    denom = float(b @ cov @ b)
    if denom <= 0:
        return np.nan, np.nan
    n_mv = float((b @ cov @ a) / denom)
    n_delta = abs(long_e["delta_dollar"]) / max(abs(short_e["delta_dollar"]), 1e-9)
    return n_delta, n_mv


def choose_integer_n(long_e, short_e, cov, exposure_side=-1):
    n_delta, n_mv = balance_ridge(long_e, short_e, cov)
    if not np.isfinite(n_mv):
        n_mv = n_delta
    n0 = int(np.clip(round(max(n_mv, 0.0)), 1, MAX_N))

    rows = []
    for n in range(1, MAX_N + 1):
        residual = long_e["vec"] + exposure_side * n * short_e["vec"]
        var = float(residual @ cov @ residual)
        net_theta = long_e["theta"] + exposure_side * n * short_e["theta"]
        net_delta = long_e["delta_dollar"] + exposure_side * n * short_e["delta_dollar"]
        rows.append({
            "n": n,
            "residual_var": var,
            "net_theta": net_theta,
            "net_delta_dollar": net_delta,
            "theta_ok": bool(net_theta >= THETA_TOL),
        })

    rr = pd.DataFrame(rows)
    feasible = rr[rr.theta_ok]
    pool = feasible if not feasible.empty else rr
    best = pool.sort_values(["residual_var", "n"]).iloc[0]
    return {
        "n_delta": n_delta,
        "n_mv": n_mv,
        "n_balanced": int(best.n),
        "ridge": rr,
    }


def make_position(asset, option, side, entry_date, qty=1.0):
    px = option["ask"] if side > 0 else option["bid"]
    return {
        "asset": asset,
        "contract_id": option["contract_id"],
        "expiry": option["expiry"],
        "strike": option["strike"],
        "side": side,
        "qty": float(qty),
        "entry_date": pd.Timestamp(entry_date),
        "entry_px": float(px),
        "cashflow": -side * float(px) * 100.0 * float(qty),
        "option": option,
    }


def load_marks(con, path, ids):
    if not ids:
        return {}
    vals = ",".join("'" + x.replace("'", "''") + "'" for x in sorted(set(ids)))
    d = sql(con, f"""
        SELECT CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(date AS DATE) AS date,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               CAST((bid+ask)/2.0 AS DOUBLE) AS mark
        FROM read_parquet('{pathq(path)}')
        WHERE contract_id IN ({vals})
        ORDER BY date
    """)
    if d.empty:
        return {}
    d.date = pd.to_datetime(d.date)
    return {(str(r.contract_id), pd.Timestamp(r.date)): r for r in d.itertuples(index=False)}


def position_value(p, row, exit=False):
    if row is None:
        return np.nan
    if not exit:
        px = float(row.mark)
    elif p["side"] > 0:
        px = float(row.bid)
    else:
        px = float(row.ask)
    return p["cashflow"] + p["side"] * px * 100.0 * p["qty"]


def get_spot_map(con, path):
    px = load_px(con, path, "S")
    return {pd.Timestamp(r.date): float(r.S_px) for r in px.itertuples(index=False)}


def simulate_config(
    con,
    qpath,
    spath,
    qspots,
    sspots,
    dates,
    factor_hist,
    selector,
    mark_maps,
    long_asset,
    short_asset,
    long_dte,
    short_dte,
):
    spot_map = {"QQQ": qspots, "SPY": sspots}
    long_current = None
    short_current = None
    records = []
    balance_rows = []

    for d in dates:
        d = pd.Timestamp(d)

        if long_current is None or (pd.Timestamp(long_current["expiry"]) - d).days <= 60:
            opt = selector.get(
                (long_asset, d, int(long_dte), float(TARGET_LONG_DELTA))
            )
            if opt is not None:
                if long_current is not None:
                    long_current["exit_date"] = d
                opt = opt.copy()
                opt["entry_date"] = d
                long_current = make_position(long_asset, opt, +1, d)
                long_current["option"] = opt
                records.append(long_current)

        if short_current is not None:
            short_current["exit_date"] = d
        short_current = None

        if long_current is None:
            continue

        spot_l = spot_map[long_asset].get(d, np.nan)
        spot_s = spot_map[short_asset].get(d, np.nan)
        if not np.isfinite(spot_l) or not np.isfinite(spot_s):
            continue

        lopt = long_current["option"].copy()
        lopt["dte"] = max((pd.Timestamp(long_current["expiry"]) - d).days, 1)
        le = option_exposure(lopt, spot_l, long_asset)

        sopt = selector.get(
            (short_asset, d, int(short_dte), float(TARGET_SHORT_DELTA))
        )
        if le is None or sopt is None:
            continue
        sopt = sopt.copy()
        sopt["entry_date"] = d
        se = option_exposure(
            {**sopt, "dte": int(short_dte)},
            spot_s,
            short_asset,
        )
        if se is None:
            continue

        cov = covariance_for_date(factor_hist, d)
        bal = choose_integer_n(le, se, cov, exposure_side=-1)

        n = bal["n_balanced"]
        sp = make_position(short_asset, sopt, -1, d, qty=n)
        sp["option"] = sopt
        short_current = sp
        records.append(sp)

        balance_rows.append({
            "date": d,
            "long_asset": long_asset,
            "short_asset": short_asset,
            "long_dte": long_dte,
            "short_dte": short_dte,
            "n_delta": bal["n_delta"],
            "n_mv": bal["n_mv"],
            "n_balanced": n,
            "net_theta": float(le["theta"] - n * se["theta"]),
            "net_delta_dollar": float(le["delta_dollar"] - n * se["delta_dollar"]),
            "residual_var": float(
                bal["ridge"].loc[
                    bal["ridge"].n == n, "residual_var"
                ].iloc[0]
            ),
            "theta_ok": bool(
                bal["ridge"].loc[
                    bal["ridge"].n == n, "theta_ok"
                ].iloc[0]
            ),
        })

    day_grid = pd.date_range(min(dates), max(dates), freq="B")

    # Event indexes preserve the original ordering semantics while avoiding
    # scanning every historical position on every business day.
    entry_events = {}
    exit_events = {}
    for p in records:
        entry_events.setdefault(pd.Timestamp(p["entry_date"]), []).append(p)
        if p.get("exit_date") is not None:
            exit_events.setdefault(pd.Timestamp(p["exit_date"]), []).append(p)

    active = []
    active_ids = set()
    rows = []
    close_pnl = 0.0
    last_mark = {}

    for d in day_grid:
        d = pd.Timestamp(d)

        # Original behavior: entries are activated before same-day closes.
        for p in entry_events.get(d, ()):
            pid = id(p)
            if pid not in active_ids:
                active.append(p)
                active_ids.add(pid)

        # Original behavior: a missing mark on the scheduled exit date means
        # the position is not removed on that date.
        for p in exit_events.get(d, ()):
            pid = id(p)
            if pid not in active_ids:
                continue
            row = mark_maps[p["asset"]].get((p["contract_id"], d))
            if row is None:
                continue
            close_pnl += position_value(p, row, exit=True)
            active = [q for q in active if id(q) != pid]
            active_ids.remove(pid)

        mtm = 0.0
        for p in active:
            row = mark_maps[p["asset"]].get((p["contract_id"], d))
            if row is not None:
                last_mark[(p["asset"], p["contract_id"])] = row
            else:
                row = last_mark.get((p["asset"], p["contract_id"]))
            if row is not None:
                mtm += position_value(p, row, exit=False)
        eq = NAV0 + close_pnl + mtm
        rows.append({"date": d, "eq": eq})

    eq = pd.DataFrame(rows)
    if eq.empty:
        return None, pd.DataFrame(), pd.DataFrame()

    ending = float(eq["eq"].iloc[-1])
    years = max((eq.date.iloc[-1] - eq.date.iloc[0]).days / 365.25, 1 / 365.25)
    cagr = (ending / NAV0) ** (1 / years) - 1
    maxdd = float((eq["eq"] / eq["eq"].cummax() - 1).min())
    ret = eq["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sharpe = float(
        ret.mean() / ret.std(ddof=1) * math.sqrt(252)
    ) if ret.std(ddof=1) > 0 else 0.0

    br = pd.DataFrame(balance_rows)
    result = {
        "long_asset": long_asset,
        "short_asset": short_asset,
        "long_dte": long_dte,
        "short_dte": short_dte,
        "rebalance_points": len(br),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": maxdd,
        "sharpe": sharpe,
        "mean_n_delta": float(br.n_delta.mean()) if not br.empty else np.nan,
        "mean_n_mv": float(br.n_mv.mean()) if not br.empty else np.nan,
        "mean_n_balanced": float(br.n_balanced.mean()) if not br.empty else np.nan,
        "median_n_balanced": float(br.n_balanced.median()) if not br.empty else np.nan,
        "n_std": float(br.n_balanced.std(ddof=1)) if len(br) > 1 else 0.0,
        "theta_feasible_pct": float(br.theta_ok.mean()) if not br.empty else np.nan,
        "mean_net_theta": float(br.net_theta.mean()) if not br.empty else np.nan,
        "mean_abs_net_delta": float(br.net_delta_dollar.abs().mean()) if not br.empty else np.nan,
        "mean_residual_var": float(br.residual_var.mean()) if not br.empty else np.nan,
    }
    return result, eq, br

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--orientation",
        choices=["normal", "reverse", "both"],
        default="both",
        help="normal = long far / short near; reverse = long near / short far; both = run both",
    )
    a = ap.parse_args()

    d = Path(a.data_dir)
    o = Path(a.out)
    o.mkdir(parents=True, exist_ok=True)

    qpath = str(d / "QQQ_options.parquet")
    spath = str(d / "SPY_options.parquet")
    qu = str(d / "QQQ_underlying.parquet")
    su = str(d / "SPY_underlying.parquet")
    for p in [qpath, spath, qu, su]:
        assert Path(p).exists(), p

    con = duckdb.connect()
    t0 = time.perf_counter()
    dates = weekly_dates(con, su)
    qspots = get_spot_map(con, qu)
    sspots = get_spot_map(con, su)
    hist = build_factor_history(con, qu, su, qpath, spath, dates)
    hist.to_csv(o / "factor_history.csv", index=False)
    t_factor = time.perf_counter()

    option_paths = {"QQQ": qpath, "SPY": spath}
    selector = preselect_calls(con, option_paths, dates)
    t_selector = time.perf_counter()

    ids_by_asset = {"QQQ": set(), "SPY": set()}
    for (asset, _, _, _), opt in selector.items():
        ids_by_asset[asset].add(opt["contract_id"])
    mark_maps = {
        asset: load_marks(con, option_paths[asset], sorted(ids))
        for asset, ids in ids_by_asset.items()
    }
    t_marks = time.perf_counter()

    families = [("SPY", "SPY"), ("QQQ", "QQQ"), ("SPY", "QQQ"), ("QQQ", "SPY")]
    configs = []
    if a.orientation in ("normal", "both"):
        for la, sa in families:
            # Standard calendar/diagonal direction:
            # long far (90/180D) and roll short near (7/14/21/30D).
            for ld in LONG_DTES:
                for sd in SHORT_DTES:
                    configs.append((la, sa, ld, sd))
    if a.orientation in ("reverse", "both"):
        for la, sa in families:
            # Reverse-calendar direction:
            # long near (7/14/21/30D) and repeatedly short far (90/180D).
            for ld in SHORT_DTES:
                for sd in LONG_DTES:
                    configs.append((la, sa, ld, sd))

    results = []
    curves = []
    balances = []
    for la, sa, ld, sd in configs:
        rr, eq, br = simulate_config(
            con,
            qpath,
            spath,
            qspots,
            sspots,
            dates,
            hist,
            selector,
            mark_maps,
            la,
            sa,
            ld,
            sd,
        )
        if rr is not None:
            results.append(rr)
            eq["strategy"] = f"{la}_LONG1__{sa}_SHORTN__L{ld}D__S{sd}D"
            curves.append(eq)
            br["strategy"] = eq["strategy"].iloc[0] if not br.empty else eq["strategy"].iloc[0]
            balances.append(br)

    t_sim = time.perf_counter()

    res = pd.DataFrame(results).sort_values(["long_asset", "short_asset", "long_dte", "short_dte"])
    res.to_csv(o / "results.csv", index=False)
    if curves:
        pd.concat(curves, ignore_index=True).to_csv(o / "equity.csv", index=False)
    if balances:
        pd.concat(balances, ignore_index=True).to_csv(o / "balance_points.csv", index=False)

    ridge_rows = []
    for la, sa, ld, sd in configs:
        name = f"{la}_LONG1__{sa}_SHORTN__L{ld}D__S{sd}D"
        subset = res[
            (res.long_asset == la) & (res.short_asset == sa) &
            (res.long_dte == ld) & (res.short_dte == sd)
        ]
        if not subset.empty:
            ridge_rows.append(subset.iloc[0].to_dict())
    pd.DataFrame(ridge_rows).to_csv(o / "balance_ridge_summary.csv", index=False)

    methodology = {
        "name": "QQQ-SPY Cross-Underlying Ratio-Diagonal Balance Ridge V1",
        "configs": f"1 long call versus N short calls across same/cross underlying pairs; selected orientation={a.orientation}",
        "normal_time_orientation": "long far 90/180D, short near 7/14/21/30D",
        "reverse_time_orientation": "long near 7/14/21/30D, short far 90/180D",
        "selected_orientation": a.orientation,
        "long_dtes": LONG_DTES + SHORT_DTES,
        "short_dtes": SHORT_DTES + LONG_DTES,
        "long_delta": TARGET_LONG_DELTA,
        "short_delta": TARGET_SHORT_DELTA,
        "N_range": [1, MAX_N],
        "balance_1": "N_delta = abs(long dollar delta) / abs(short dollar delta)",
        "balance_2": "N_MV = (b' Sigma a)/(b' Sigma b), minimum-variance hedge ratio across QQQ/SPY return, IV-change, and squared-return factors",
        "balance_point": "integer N minimizing residual variance among N=1..8; when feasible, non-negative net theta is required",
        "rebalancing": "short call rebuilt weekly; long call rolled when <=60 DTE",
        "fills": "long buy at ask / exit at bid; short sell at bid / buy-to-close at ask; daily MTM at midpoint",
        "marks": "last known historical mark carried forward only when current-day quote missing; never future-filled",
        "tail": "naked short-call tail is intentionally retained as a diagnostic; not a live-order strategy",
        "no_live_orders": True,
        "no_parameter_search": True,
        "execution_refactor": "preselect required option contracts once per asset; load historical marks once per asset; index entry/exit events instead of scanning all historical positions daily; strategy rules unchanged",
        "runtime_seconds": {
            "factor_history_and_calendar": round(t_factor - t0, 3),
            "option_selection_cache": round(t_selector - t_factor, 3),
            "historical_mark_cache": round(t_marks - t_selector, 3),
            "strategy_valuation": round(t_sim - t_marks, 3),
            "total_before_reporting": round(t_sim - t0, 3),
        },
    }
    (o / "METHODOLOGY.json").write_text(json.dumps(methodology, indent=2), encoding="utf-8")

    lines = [
        f"# QQQ-SPY Cross-Underlying Ratio-Diagonal Balance Ridge V1 — {a.orientation.upper()}",
        "",
        "Four families: SPY/ SPY, QQQ/ QQQ, SPY long vs QQQ short, QQQ long vs SPY short.",
        "N is not fixed. Delta ratio and minimum-variance ratio are recorded; the selected integer minimizes residual factor variance subject to non-negative theta when feasible.",
        "",
        "| long | short | L-DTE | S-DTE | points | mean N-delta | mean N-MV | mean N-balanced | CAGR | MaxDD | Sharpe | theta feasible |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in res.iterrows():
        lines.append(
            f"| {r.long_asset} | {r.short_asset} | {int(r.long_dte)} | {int(r.short_dte)} | "
            f"{int(r.rebalance_points)} | {r.mean_n_delta:.2f} | {r.mean_n_mv:.2f} | {r.mean_n_balanced:.2f} | "
            f"{r.cagr:.2%} | {r.maxdd:.2%} | {r.sharpe:.2f} | {r.theta_feasible_pct:.1%} |"
        )
    (o / "RESULTS.md").write_text("\\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
