from __future__ import annotations
import argparse, json, math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

TD = 252
M = 100.0
START, END = "2018-03-01", "2025-12-01"


def sql(con, s):
    return con.execute(s).df()


def pathq(p):
    return str(p).replace("'", "''")


def load_px(con, path, prefix):
    d = sql(
        con,
        f"""
        SELECT CAST(date AS DATE) AS date,
               CAST("close" AS DOUBLE) AS close_px
        FROM read_parquet('{pathq(path)}')
        WHERE CAST(date AS DATE) BETWEEN DATE '2011-01-01' AND DATE '2025-12-31'
        ORDER BY date
        """,
    )
    d.date = pd.to_datetime(d.date)
    r = np.log(d.close_px / d.close_px.shift(1))
    for w in (5, 14, 20, 30, 60):
        d[f"rv{w}"] = r.rolling(w).std() * math.sqrt(TD)
    d["month"] = d.date.dt.to_period("M")
    return d.rename(
        columns={
            "close_px": prefix + "_px",
            "rv5": prefix + "_rv5",
            "rv14": prefix + "_rv14",
            "rv20": prefix + "_rv20",
            "rv30": prefix + "_rv30",
            "rv60": prefix + "_rv60",
        }
    )[
        [
            "date",
            prefix + "_px",
            prefix + "_rv5",
            prefix + "_rv14",
            prefix + "_rv20",
            prefix + "_rv30",
            prefix + "_rv60",
            "month",
        ]
    ]


def build_state(con, q_u, s_u):
    q = load_px(con, q_u, "Q")
    s = load_px(con, s_u, "S")
    x = (
        q.merge(s, on=["date", "month"], how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )

    x["rr20"] = x.Q_rv20 / x.S_rv20
    x["rr5"] = x.Q_rv5 / x.S_rv5
    x["rv_velocity"] = x.rr5 / x.rr20

    qr = np.log(x.Q_px / x.Q_px.shift(1))
    sr = np.log(x.S_px / x.S_px.shift(1))
    beta = qr.rolling(60).cov(sr) / sr.rolling(60).var()
    x["beta60"] = beta.shift(1)
    x["resid"] = qr - x.beta60 * sr
    x["resid_rv20"] = x.resid.rolling(20).std() * math.sqrt(TD)

    # Causal history-only context for the RV ratio; no future/current row included.
    x["rr_med_252"] = x.rr20.shift(1).rolling(252, min_periods=126).median()
    x["resid_med_252"] = (
        x.resid_rv20.shift(1).rolling(252, min_periods=126).median()
    )
    return x


def get_chain(con, path, date, lo, hi):
    d = date.strftime("%Y-%m-%d")
    return sql(
        con,
        f"""
        SELECT CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(expiration AS DATE) AS expiration,
               CAST(strike AS DOUBLE) AS strike,
               LOWER("type") AS opt_type,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               COALESCE(CAST(volume AS DOUBLE), 0) AS volume,
               COALESCE(CAST(open_interest AS DOUBLE), 0) AS open_interest,
               CAST(delta AS DOUBLE) AS delta,
               CAST(implied_volatility AS DOUBLE) AS implied_volatility
        FROM read_parquet('{pathq(path)}')
        WHERE CAST(date AS DATE)=DATE '{d}'
          AND CAST(expiration AS DATE)>DATE '{d}'
          AND CAST(expiration AS DATE)>=DATE '{d}' + INTERVAL '{lo} days'
          AND CAST(expiration AS DATE)<=DATE '{d}' + INTERVAL '{hi} days'
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask>=bid AND ask>0
          AND delta IS NOT NULL
          AND (open_interest>=10 OR volume>=5)
        """,
    )


def liquid(df):
    if df.empty:
        return df
    z = df.copy()
    z["mark"] = (z.ask + z.bid) / 2.0
    z["spr"] = (z.ask - z.bid) / z.mark.replace(0, np.nan)
    return z[np.isfinite(z.spr) & (z.spr <= 0.35)]


def pick4(df, target_dte, wing=0.10, long_delta=0.50):
    df = liquid(df)
    if df.empty:
        return None
    dtes = df.groupby("expiration").dte.first() if "dte" in df else None
    if dtes is None:
        return None
    e = (dtes - target_dte).abs().sort_values().index[0]
    x = df[df.expiration == e]
    c = x[x.opt_type == "call"]
    p = x[x.opt_type == "put"]
    if c.empty or p.empty:
        return None

    lc = c.iloc[(c["delta"] - long_delta).abs().argmin()]
    lp = p.iloc[(p["delta"] + long_delta).abs().argmin()]

    fc_pool = c[c["strike"] > float(lc.strike)]
    fp_pool = p[p["strike"] < float(lp.strike)]
    if fc_pool.empty or fp_pool.empty:
        return None

    fc = fc_pool.iloc[(fc_pool["delta"] - wing).abs().argmin()]
    fp = fp_pool.iloc[(fp_pool["delta"] + wing).abs().argmin()]

    ivs = [lc.implied_volatility, lp.implied_volatility, fc.implied_volatility, fp.implied_volatility]
    if any(pd.isna(v) or not np.isfinite(float(v)) or float(v) <= 0 for v in ivs):
        return None

    return e, lc, lp, fc, fp


def qqq_rc(con, path, date, target=60, wing=0.10, long_delta=0.50, exit_dte=25):
    df = get_chain(con, path, date, max(7, target - 7), target + 7)
    if df.empty:
        return None
    df["dte"] = (pd.to_datetime(df.expiration) - date).dt.days
    picked = pick4(df, target, wing, long_delta)
    if not picked:
        return None
    e, lc, lp, fc, fp = picked
    legs = [
        ("QQQ", str(e), lc.strike, "call", 1, float(lc.ask), str(lc.contract_id)),
        ("QQQ", str(e), fc.strike, "call", -1, float(fc.bid), str(fc.contract_id)),
        ("QQQ", str(e), lp.strike, "put", 1, float(lp.ask), str(lp.contract_id)),
        ("QQQ", str(e), fp.strike, "put", -1, float(fp.bid), str(fp.contract_id)),
    ]
    debit = sum(side * px * M for _, _, _, _, side, px, _ in legs)
    call_width = abs(float(fc.strike) - float(lc.strike)) * M
    put_width = abs(float(lp.strike) - float(fp.strike)) * M
    risk = max(debit, 0.0)
    profit = max(call_width, put_width) - debit
    atm_iv = (float(lc.implied_volatility) + float(lp.implied_volatility)) / 2.0
    struct_iv = sum(ivs_val for ivs_val in [
        float(lc.implied_volatility), float(lp.implied_volatility),
        float(fc.implied_volatility), float(fp.implied_volatility)
    ]) / 4.0
    return {
        "symbol": "QQQ",
        "entry": date,
        "expiry": pd.Timestamp(e),
        "exit_dte": exit_dte,
        "legs": legs,
        "risk": risk,
        "profit": profit,
        "entry_value": debit,
        "atm_iv": atm_iv,
        "struct_iv": struct_iv,
        "signal_iv": atm_iv,
    }


def spy_ic(con, path, date, target=30, wing=0.10):
    df = get_chain(con, path, date, max(7, target - 7), target + 7)
    if df.empty:
        return None
    df["dte"] = (pd.to_datetime(df.expiration) - date).dt.days
    picked = pick4(df, target, wing)
    if not picked:
        return None
    e, sc, sp, lc, lp = picked
    legs = [
        ("SPY", str(e), sc.strike, "call", -1, float(sc.bid), str(sc.contract_id)),
        ("SPY", str(e), lc.strike, "call", 1, float(lc.ask), str(lc.contract_id)),
        ("SPY", str(e), sp.strike, "put", -1, float(sp.bid), str(sp.contract_id)),
        ("SPY", str(e), lp.strike, "put", 1, float(lp.ask), str(lp.contract_id)),
    ]
    credit = -sum(side * px * M for _, _, _, _, side, px, _ in legs)
    wingw = max(
        abs(float(lc.strike) - float(sc.strike)),
        abs(float(sp.strike) - float(lp.strike)),
    ) * M
    risk = max(wingw - credit, 0.0)
    profit = max(credit, 0.0)
    atm_iv = (float(sc.implied_volatility) + float(sp.implied_volatility)) / 2.0
    struct_iv = sum(ivs_val for ivs_val in [
        float(sc.implied_volatility), float(sp.implied_volatility),
        float(lc.implied_volatility), float(lp.implied_volatility)
    ]) / 4.0
    return {
        "symbol": "SPY",
        "entry": date,
        "expiry": pd.Timestamp(e),
        "exit_dte": 7,
        "legs": legs,
        "risk": risk,
        "profit": profit,
        "entry_value": credit,
        "atm_iv": atm_iv,
        "struct_iv": struct_iv,
        "signal_iv": atm_iv,
    }


def entry_days(state):
    z = state[
        (state.date >= pd.Timestamp(START)) & (state.date <= pd.Timestamp(END))
    ].copy()
    return [
        g.date.iloc[0]
        for _, g in z.groupby(z.date.dt.to_period("M"), sort=True)
    ]


def prev_trading_date(state_dates, d):
    dates = pd.DatetimeIndex(state_dates)
    ix = dates.searchsorted(pd.Timestamp(d), side="left") - 1
    return dates[ix] if ix >= 0 else None


def unit_marks(con, qpath, spath, positions):
    ids = {"QQQ": [], "SPY": []}
    for p in positions:
        for leg in p["legs"]:
            if leg[0] in ids and leg[6] not in ids[leg[0]]:
                ids[leg[0]].append(leg[6])

    out = []
    for sym, idlist in ids.items():
        if not idlist:
            continue
        vals = ",".join("'" + x.replace("'", "''") + "'" for x in idlist)
        path = qpath if sym == "QQQ" else spath
        d = sql(
            con,
            f"""
            SELECT CAST(contract_id AS VARCHAR) AS contract_id,
                   CAST(date AS DATE) AS date,
                   CAST(bid AS DOUBLE) AS bid,
                   CAST(ask AS DOUBLE) AS ask
            FROM read_parquet('{pathq(path)}')
            WHERE contract_id IN ({vals})
            ORDER BY date
            """,
        )
        if not d.empty:
            d.date = pd.to_datetime(d.date)
            d["mark"] = (d.bid + d.ask) / 2.0
            d["symbol"] = sym
            out.append(d)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def simulate_qqq_only(con, state, qpath, name):
    days = entry_days(state)
    state_dates = sorted(pd.to_datetime(state.date).tolist())
    st = state.set_index("date")
    candidates = []
    signals = []
    last_q = pd.Timestamp.min

    for d in days:
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        s = st.loc[sigd]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[0]
        if any(pd.isna(s[k]) for k in ["Q_rv60"]):
            continue

        q_sig = qqq_rc(con, qpath, sigd, 90, 0.05, 0.25, 35)
        if q_sig is None:
            continue
        q_ratio = float(s.Q_rv60) / float(q_sig["atm_iv"])

        signals.append({
            "strategy": name,
            "signal_date": sigd,
            "entry_date": d,
            "q_rv60": float(s.Q_rv60),
            "q_iv60": float(q_sig["atm_iv"]),
            "q_ratio": q_ratio,
            "s_rv30": np.nan,
            "s_iv30": np.nan,
            "s_ratio": np.nan,
            "coverage_1x": np.nan,
            "dynamic_spy_units": np.nan,
        })
        if not (q_ratio > 1.0):
            continue

        q = qqq_rc(con, qpath, d, 90, 0.05, 0.25, 35)
        if q is not None and d >= last_q:
            q["name"] = f"{name}_Q_{len(candidates)}"
            q["signal_date"] = sigd
            q["q_ratio"] = q_ratio
            candidates.append(q)
            target_exit = q["expiry"] - pd.Timedelta(days=q["exit_dte"])
            ix = min(len(state_dates)-1, max(0, np.searchsorted(state_dates, target_exit, side="left")))
            last_q = pd.Timestamp(state_dates[ix])

    return _run_positions(con, state, qpath, spath=None, candidates=candidates, name=name, signal_count=len(signals),
                          risk_value=lambda p: p["risk"], cash_components=lambda p: [(-p["entry_value"], p["legs"], p["symbol"])])


def simulate_self_financing(con, state, qpath, spath, name, ratio_mode, ratio_cap):
    days = entry_days(state)
    state_dates = sorted(pd.to_datetime(state.date).tolist())
    st = state.set_index("date")
    baskets = []
    signals = []
    last_q = pd.Timestamp.min
    last_s = pd.Timestamp.min

    for d in days:
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        sig = st.loc[sigd]
        if isinstance(sig, pd.DataFrame):
            sig = sig.iloc[0]
        if any(pd.isna(sig[k]) for k in ["Q_rv60", "S_rv30"]):
            continue

        # State/eligibility is causal: prior-day realized/implied relationships only.
        q_sig = qqq_rc(con, qpath, sigd, 90, 0.05, 0.25, 35)
        sp_sig = spy_ic(con, spath, sigd, 30, 0.10)
        if q_sig is None or sp_sig is None:
            continue

        q_ratio = float(sig.Q_rv60) / float(q_sig["atm_iv"])
        s_ratio = float(sp_sig["atm_iv"]) / float(sig.S_rv30)
        state_edge = q_ratio > 1.0 and s_ratio > 1.0

        # Structure selection/funding ratio is based on the actual entry-day quotes,
        # never on the future exit path and never on the signal-day premium.
        q = qqq_rc(con, qpath, d, 90, 0.05, 0.25, 35) if state_edge else None
        sp = spy_ic(con, spath, d, 30, 0.10) if state_edge else None
        if q is None or sp is None:
            continue

        entry_coverage = float(sp["entry_value"]) / max(float(q["entry_value"]), 1e-12)
        if ratio_mode == "one_to_one":
            spy_units = 1
            eligible = state_edge and entry_coverage >= 1.0
        elif ratio_mode == "dynamic":
            spy_units = max(
                1,
                int(math.ceil(float(q["entry_value"]) / max(float(sp["entry_value"]), 1e-12))),
            )
            eligible = state_edge and spy_units <= int(ratio_cap)
        else:
            raise ValueError(ratio_mode)

        signals.append({
            "strategy": name,
            "signal_date": sigd,
            "entry_date": d,
            "q_rv60": float(sig.Q_rv60),
            "q_iv90": float(q_sig["atm_iv"]),
            "q_ratio": q_ratio,
            "s_rv30": float(sig.S_rv30),
            "s_iv30": float(sp_sig["atm_iv"]),
            "s_ratio": s_ratio,
            "coverage_signal_day": float(sp_sig["entry_value"]) / max(float(q_sig["entry_value"]), 1e-12),
            "coverage_entry_day": entry_coverage,
            "dynamic_spy_units": spy_units,
        })
        if not eligible:
            continue
        if d < last_q or d < last_s:
            continue

        combined_risk = float(q["risk"]) + spy_units * float(sp["risk"])
        if combined_risk <= 0:
            continue

        baskets.append({
            "name": f"{name}_{len(baskets)}",
            "entry": d,
            "signal_date": sigd,
            "components": [
                {
                    "symbol": "QQQ", "legs": q["legs"], "expiry": q["expiry"], "exit_dte": 35,
                    "entry_cf": -float(q["entry_value"]), "risk": float(q["risk"]), "units": 1,
                },
                {
                    "symbol": "SPY", "legs": sp["legs"], "expiry": sp["expiry"], "exit_dte": 7,
                    "entry_cf": float(sp["entry_value"]), "risk": float(sp["risk"]), "units": spy_units,
                },
            ],
            "risk": combined_risk,
            "q_ratio": q_ratio,
            "s_ratio": s_ratio,
            "coverage": entry_coverage,
            "spy_units": spy_units,
        })

        q_target_exit = q["expiry"] - pd.Timedelta(days=35)
        s_target_exit = sp["expiry"] - pd.Timedelta(days=7)
        q_ix = min(len(state_dates)-1, max(0, np.searchsorted(state_dates, q_target_exit, side="left")))
        s_ix = min(len(state_dates)-1, max(0, np.searchsorted(state_dates, s_target_exit, side="left")))
        last_q = pd.Timestamp(state_dates[q_ix])
        last_s = pd.Timestamp(state_dates[s_ix])

    return _run_baskets(con, state, qpath, spath, baskets, name, signals)

def _run_positions(con, state, qpath, spath, candidates, name, signal_count, risk_value, cash_components):
    if not candidates:
        return {
            "name": name, "entries": 0, "ending_nav": 100000.0, "cagr": 0.0,
            "maxdd": 0.0, "sharpe": 0.0, "q_entries": 0, "s_entries": 0,
            "signal_count": signal_count, "eligible_count": 0,
        }, pd.DataFrame()

    ids = []
    for p in candidates:
        for leg in p["legs"]:
            ids.append((p["symbol"], leg[6]))
    mk = _load_marks(con, qpath, spath, ids)

    nav = 100000.0
    realized = 0.0
    openpos = []
    used = set()
    rows = []
    for d in sorted(pd.to_datetime(state.date).tolist()):
        for p in candidates:
            if p["name"] in used or p["entry"] != d:
                continue
            qty = int(math.floor((nav * 0.05) / float(risk_value(p))))
            if qty > 0:
                pp = p.copy()
                pp["qty"] = qty
                openpos.append(pp)
            used.add(p["name"])

        still = []
        for p in openpos:
            exitd = max(d, p["expiry"] - pd.Timedelta(days=p["exit_dte"]))
            if d == exitd:
                v = 0.0
                ok = True
                for leg in p["legs"]:
                    b, a, m = mk.get((p["symbol"], leg[6], d), (None, None, None))
                    if m is None:
                        ok = False
                        break
                    fill = b if leg[4] == 1 else a
                    v += leg[4] * fill * M * p["qty"]
                if ok:
                    realized += ((-p["entry_value"] if p["symbol"] == "QQQ" else p["entry_value"]) * p["qty"]) + v
                else:
                    still.append(p)
            else:
                still.append(p)
        openpos = still

        mtm = 0.0
        for p in openpos:
            v = 0.0
            ok = True
            for leg in p["legs"]:
                b, a, m = mk.get((p["symbol"], leg[6], d), (None, None, None))
                if m is None:
                    ok = False
                    break
                v += leg[4] * m * M * p["qty"]
            if ok:
                entry_cf = (-p["entry_value"] if p["symbol"] == "QQQ" else p["entry_value"]) * p["qty"]
                mtm += entry_cf + v

        rows.append((d, 100000.0 + realized + mtm))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e.date.iloc[-1] - e.date.iloc[0]).days / 365.25, 1/365.25)
    ending = float(e["eq"].iloc[-1])
    r = e["eq"].pct_change().replace([np.inf,-np.inf], np.nan).fillna(0)
    return {
        "name": name, "entries": len(candidates), "ending_nav": ending,
        "cagr": float((ending/100000.0)**(1/years)-1),
        "maxdd": float((e["eq"]/e["eq"].cummax()-1).min()),
        "sharpe": float(r.mean()/r.std(ddof=1)*math.sqrt(TD)) if r.std(ddof=1)>0 else 0.0,
        "q_entries": len(candidates), "s_entries": 0, "signal_count": signal_count,
        "eligible_count": len(candidates),
    }, pd.DataFrame()


def _load_marks(con, qpath, spath, ids):
    by = {"QQQ": [], "SPY": []}
    for sym, cid in ids:
        if cid not in by[sym]:
            by[sym].append(cid)
    out = []
    for sym, idlist in by.items():
        if not idlist:
            continue
        vals = ",".join("'" + x.replace("'", "''") + "'" for x in idlist)
        path = qpath if sym == "QQQ" else spath
        d = sql(con, f"""
            SELECT CAST(contract_id AS VARCHAR) AS contract_id,
                   CAST(date AS DATE) AS date,
                   CAST(bid AS DOUBLE) AS bid,
                   CAST(ask AS DOUBLE) AS ask
            FROM read_parquet('{pathq(path)}')
            WHERE contract_id IN ({vals})
            ORDER BY date
        """)
        if not d.empty:
            d.date = pd.to_datetime(d.date)
            d["mark"] = (d.bid+d.ask)/2.0
            out.append((sym,d))
    mk = {}
    for sym,d in out:
        for r in d.itertuples(index=False):
            mk[(sym, r.contract_id, r.date)] = (float(r.bid), float(r.ask), float(r.mark))
    return mk


def _run_baskets(con, state, qpath, spath, baskets, name, signals):
    if not baskets:
        return {
            "name": name, "entries": 0, "ending_nav": 100000.0, "cagr": 0.0,
            "maxdd": 0.0, "sharpe": 0.0, "q_entries": 0, "s_entries": 0,
            "signal_count": len(signals), "eligible_count": 0,
            "mean_q_ratio": np.nan, "mean_s_ratio": np.nan, "mean_coverage": np.nan,
            "mean_spy_units": np.nan,
        }, pd.DataFrame(signals)

    ids = []
    for basket in baskets:
        for comp in basket["components"]:
            for leg in comp["legs"]:
                ids.append((comp["symbol"], leg[6]))
    mk = _load_marks(con, qpath, spath, ids)

    nav = 100000.0
    realized = 0.0
    openb = []
    rows = []
    used = set()

    dates = sorted(pd.to_datetime(state.date).tolist())
    for d in dates:
        for b in baskets:
            if b["name"] in used or b["entry"] != d:
                continue
            qty = int(math.floor((nav * 0.05) / float(b["risk"])))
            if qty > 0:
                bb = {**b, "qty": qty, "component_open": [True, True], "component_realized": [False, False]}
                # Entry cashflows are booked immediately. For self-financing baskets this is <= 0.
                realized += sum(c["entry_cf"] * c["units"] for c in b["components"]) * qty
                openb.append(bb)
            used.add(b["name"])

        still_b = []
        for b in openb:
            for i,c in enumerate(b["components"]):
                if not b["component_open"][i]:
                    continue
                exitd = max(d, c["expiry"] - pd.Timedelta(days=c["exit_dte"]))
                if d == exitd:
                    v = 0.0
                    ok = True
                    for leg in c["legs"]:
                        side = leg[4]
                        bid, ask, mark = mk.get((c["symbol"], leg[6], d), (None,None,None))
                        if mark is None:
                            ok = False
                            break
                        fill = bid if side == 1 else ask
                        v += side * fill * M * b["qty"] * c["units"]
                    if ok:
                        realized += v
                        b["component_open"][i] = False

            if any(b["component_open"]):
                still_b.append(b)
        openb = still_b

        mtm = 0.0
        for b in openb:
            for i,c in enumerate(b["components"]):
                if not b["component_open"][i]:
                    continue
                v = 0.0
                ok = True
                for leg in c["legs"]:
                    bid, ask, mark = mk.get((c["symbol"], leg[6], d), (None,None,None))
                    if mark is None:
                        ok = False
                        break
                    v += leg[4] * mark * M * b["qty"] * c["units"]
                if ok:
                    mtm += v

        rows.append((d, 100000.0 + realized + mtm))

    e = pd.DataFrame(rows, columns=["date","eq"])
    years = max((e.date.iloc[-1]-e.date.iloc[0]).days/365.25, 1/365.25)
    ending = float(e["eq"].iloc[-1])
    r = e["eq"].pct_change().replace([np.inf,-np.inf], np.nan).fillna(0)
    sigdf = pd.DataFrame(signals)
    return {
        "name": name, "entries": len(baskets), "ending_nav": ending,
        "cagr": float((ending/100000.0)**(1/years)-1),
        "maxdd": float((e["eq"]/e["eq"].cummax()-1).min()),
        "sharpe": float(r.mean()/r.std(ddof=1)*math.sqrt(TD)) if r.std(ddof=1)>0 else 0.0,
        "q_entries": len(baskets), "s_entries": len(baskets),
        "signal_count": len(signals), "eligible_count": len(baskets),
        "mean_q_ratio": float(sigdf.q_ratio.mean()) if not sigdf.empty else np.nan,
        "mean_s_ratio": float(sigdf.s_ratio.mean()) if not sigdf.empty else np.nan,
        "mean_coverage": float(sigdf.coverage_entry_day.mean()) if not sigdf.empty else np.nan,
        "mean_spy_units": float(sigdf.dynamic_spy_units.mean()) if not sigdf.empty else np.nan,
    }, sigdf



def _first_on_or_after(dates, target):
    dates = pd.DatetimeIndex(dates)
    ix = dates.searchsorted(pd.Timestamp(target), side="left")
    return dates[ix] if ix < len(dates) else None


def _simulate_position_book(con, state, qpath, spath, positions, name, signals):
    if not positions:
        return {
            "name": name, "entries": 0, "ending_nav": 100000.0, "cagr": 0.0,
            "maxdd": 0.0, "sharpe": 0.0, "q_entries": 0, "s_entries": 0,
            "signal_count": len(signals), "finance_trades": 0,
            "qqq_entry_debit": 0.0, "spy_net_pnl": 0.0, "finance_coverage": 0.0,
        }, pd.DataFrame(signals)

    ids = [(p["symbol"], leg[6]) for p in positions for leg in p["legs"]]
    mk = _load_marks(con, qpath, spath, ids)

    nav0 = 100000.0
    realized = 0.0
    openpos = []
    rows = []
    pos_pnl = []
    dates = sorted(pd.to_datetime(state.date).tolist())

    for d in dates:
        for p in positions:
            if p["entry"] == d:
                openpos.append(p)
                realized += p["entry_cf"] * p["qty"]

        still = []
        for p in openpos:
            if d == p["exitd"]:
                value = 0.0
                ok = True
                for leg in p["legs"]:
                    bid, ask, mark = mk.get((p["symbol"], leg[6], d), (None, None, None))
                    if mark is None:
                        ok = False
                        break
                    fill = bid if leg[4] == 1 else ask
                    value += leg[4] * fill * M * p["qty"]
                if ok:
                    pnl = p["entry_cf"] * p["qty"] + value
                    realized += value
                    pos_pnl.append({
                        "cycle": p["cycle"],
                        "symbol": p["symbol"],
                        "role": p["role"],
                        "entry": p["entry"],
                        "exit": d,
                        "pnl": pnl,
                        "entry_cf": p["entry_cf"] * p["qty"],
                    })
                else:
                    still.append(p)
            else:
                still.append(p)
        openpos = still

        mtm = 0.0
        for p in openpos:
            value = 0.0
            ok = True
            for leg in p["legs"]:
                bid, ask, mark = mk.get((p["symbol"], leg[6], d), (None, None, None))
                if mark is None:
                    ok = False
                    break
                value += leg[4] * mark * M * p["qty"]
            if ok:
                mtm += value

        rows.append((d, nav0 + realized + mtm))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e["date"].iloc[-1] - e["date"].iloc[0]).days / 365.25, 1 / 365.25)
    ending = float(e["eq"].iloc[-1])
    rets = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sharpe = float(rets.mean() / rets.std(ddof=1) * math.sqrt(TD)) if rets.std(ddof=1) > 0 else 0.0

    trades = pd.DataFrame(pos_pnl)
    spy_pnl = float(trades.loc[trades["symbol"] == "SPY", "pnl"].sum()) if not trades.empty else 0.0
    qqq_debit = float(sum(-p["entry_cf"] * p["qty"] for p in positions if p["symbol"] == "QQQ"))
    coverage = spy_pnl / qqq_debit if qqq_debit > 0 else 0.0

    result = {
        "name": name,
        "entries": len([p for p in positions if p["role"] == "QQQ"]),
        "ending_nav": ending,
        "cagr": float((ending / nav0) ** (1 / years) - 1),
        "maxdd": float((e["eq"] / e["eq"].cummax() - 1).min()),
        "sharpe": sharpe,
        "q_entries": len([p for p in positions if p["symbol"] == "QQQ"]),
        "s_entries": len([p for p in positions if p["symbol"] == "SPY"]),
        "signal_count": len(signals),
        "finance_trades": len([p for p in positions if p["symbol"] == "SPY"]),
        "qqq_entry_debit": qqq_debit,
        "spy_net_pnl": spy_pnl,
        "finance_coverage": coverage,
    }
    return result, pd.DataFrame(signals)


def _build_rolling_finance(con, state, qpath, spath, finance_mode):
    days = entry_days(state)
    state_dates = sorted(pd.to_datetime(state.date).tolist())
    st = state.set_index("date")
    positions = []
    signals = []
    next_q_entry = pd.Timestamp.min
    cycle = 0

    for d in days:
        if d < next_q_entry:
            continue

        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        sig = st.loc[sigd]
        if isinstance(sig, pd.DataFrame):
            sig = sig.iloc[0]
        if pd.isna(sig.get("Q_rv60", np.nan)):
            continue

        q_sig = qqq_rc(con, qpath, sigd, 90, 0.05, 0.25, 35)
        if q_sig is None:
            continue
        q_ratio = float(sig.Q_rv60) / float(q_sig["atm_iv"])
        if not (q_ratio > 1.0):
            continue

        q = qqq_rc(con, qpath, d, 90, 0.05, 0.25, 35)
        if q is None or q["risk"] <= 0:
            continue

        q_exit_target = q["expiry"] - pd.Timedelta(days=q["exit_dte"])
        q_exit = _first_on_or_after(state_dates, q_exit_target)
        if q_exit is None or q_exit <= d:
            continue

        q_qty = int(math.floor((100000.0 * 0.05) / float(q["risk"])))
        if q_qty <= 0:
            continue

        positions.append({
            "cycle": cycle,
            "role": "QQQ",
            "symbol": "QQQ",
            "entry": d,
            "exitd": q_exit,
            "legs": q["legs"],
            "entry_cf": -float(q["entry_value"]),
            "qty": q_qty,
        })
        signals.append({
            "cycle": cycle,
            "role": "QQQ",
            "finance_mode": finance_mode,
            "signal_date": sigd,
            "entry_date": d,
            "q_rv60": float(sig.Q_rv60),
            "q_iv90": float(q_sig["atm_iv"]),
            "q_ratio": q_ratio,
        })

        if finance_mode != "none":
            roll_target = d
            while roll_target < q_exit:
                roll = _first_on_or_after(state_dates, roll_target)
                if roll is None or roll >= q_exit:
                    break

                fsig_d = prev_trading_date(state_dates, roll)
                if fsig_d is None:
                    break
                fsig = st.loc[fsig_d]
                if isinstance(fsig, pd.DataFrame):
                    fsig = fsig.iloc[0]

                spy_sig = spy_ic(con, spath, fsig_d, 14, 0.10)
                s_ratio = (
                    float(spy_sig["atm_iv"]) / float(fsig.S_rv30)
                    if spy_sig is not None and pd.notna(fsig.S_rv30) and float(fsig.S_rv30) > 0
                    else np.nan
                )

                eligible = spy_sig is not None and np.isfinite(s_ratio)
                if finance_mode == "iv_edge":
                    eligible = eligible and s_ratio > 1.0
                elif finance_mode == "relative":
                    eligible = eligible and s_ratio > 1.0 and s_ratio > q_ratio

                if eligible:
                    sp = spy_ic(con, spath, roll, 14, 0.10)
                    if sp is not None and sp["risk"] > 0:
                        spy_qty = int(math.floor((100000.0 * 0.01) / float(sp["risk"])))
                        exit_target = min(
                            q_exit,
                            _first_on_or_after(state_dates, sp["expiry"] - pd.Timedelta(days=7))
                            or q_exit,
                        )
                        if spy_qty > 0 and exit_target > roll:
                            positions.append({
                                "cycle": cycle,
                                "role": "FINANCE_SPY",
                                "symbol": "SPY",
                                "entry": roll,
                                "exitd": exit_target,
                                "legs": sp["legs"],
                                "entry_cf": float(sp["entry_value"]),
                                "qty": spy_qty,
                            })
                            signals.append({
                                "cycle": cycle,
                                "role": "FINANCE_SPY",
                                "finance_mode": finance_mode,
                                "signal_date": fsig_d,
                                "entry_date": roll,
                                "q_ratio": q_ratio,
                                "s_rv30": float(fsig.S_rv30),
                                "s_iv14": float(spy_sig["atm_iv"]),
                                "s_ratio": s_ratio,
                                "spy_credit_per_unit": float(sp["entry_value"]),
                            })

                roll_target = roll + pd.Timedelta(days=7)

        next_q_entry = q_exit
        cycle += 1

    return positions, signals


def run_rolling_strategy(con, state, qpath, spath, name, finance_mode):
    positions, signals = _build_rolling_finance(con, state, qpath, spath, finance_mode)
    result, sigdf = _simulate_position_book(con, state, qpath, spath, positions, name, signals)
    return result, sigdf



def qqq_short_ic(con, path, date, target=14, wing=0.10):
    df = get_chain(con, path, date, max(5, target - 5), target + 5)
    if df.empty:
        return None
    df["dte"] = (pd.to_datetime(df.expiration) - date).dt.days
    picked = pick4(df, target, wing)
    if not picked:
        return None
    e, sc, sp, lc, lp = picked
    legs = [
        ("QQQ", str(e), sc.strike, "call", -1, float(sc.bid), str(sc.contract_id)),
        ("QQQ", str(e), lc.strike, "call", 1, float(lc.ask), str(lc.contract_id)),
        ("QQQ", str(e), sp.strike, "put", -1, float(sp.bid), str(sp.contract_id)),
        ("QQQ", str(e), lp.strike, "put", 1, float(lp.ask), str(lp.contract_id)),
    ]
    credit = -sum(side * px * M for _, _, _, _, side, px, _ in legs)
    wingw = max(
        abs(float(lc.strike) - float(sc.strike)),
        abs(float(sp.strike) - float(lp.strike)),
    ) * M
    risk = max(wingw - credit, 0.0)
    ivs = [
        float(sc.implied_volatility), float(sp.implied_volatility),
        float(lc.implied_volatility), float(lp.implied_volatility),
    ]
    if risk <= 0 or any(not np.isfinite(v) or v <= 0 for v in ivs):
        return None
    return {
        "symbol": "QQQ", "entry": date, "expiry": pd.Timestamp(e), "exit_dte": 7,
        "legs": legs, "risk": risk, "profit": max(credit, 0.0),
        "entry_value": credit, "atm_iv": (float(sc.implied_volatility) + float(sp.implied_volatility)) / 2.0,
    }


def _simulate_term_book(con, state, qpath, positions, name, signals):
    if not positions:
        return {
            "name": name, "entries": 0, "ending_nav": 100000.0, "cagr": 0.0,
            "maxdd": 0.0, "sharpe": 0.0, "qqq_cycles": 0, "finance_trades": 0,
            "long_debit": 0.0, "finance_entry_credit": 0.0,
            "finance_realized_pnl": 0.0, "finance_pnl_to_long_debit": 0.0,
            "signal_count": len(signals),
        }, pd.DataFrame(signals)

    ids = [("QQQ", leg[6]) for p in positions for leg in p["legs"]]
    mk = _load_marks(con, qpath, None, ids)

    nav0 = 100000.0
    realized = 0.0
    openpos = []
    rows = []
    trades = []
    dates = sorted(pd.to_datetime(state.date).tolist())

    for d in dates:
        for p in positions:
            if p["entry"] == d:
                realized += p["entry_cf"] * p["qty"]
                openpos.append(p)

        still = []
        for p in openpos:
            if d == p["exitd"]:
                value = 0.0
                ok = True
                for leg in p["legs"]:
                    bid, ask, mark = mk.get(("QQQ", leg[6], d), (None, None, None))
                    if mark is None:
                        ok = False
                        break
                    fill = bid if leg[4] == 1 else ask
                    value += leg[4] * fill * M * p["qty"]
                if ok:
                    realized += value
                    trades.append({
                        "cycle": p["cycle"], "role": p["role"], "entry": p["entry"], "exit": d,
                        "pnl": p["entry_cf"] * p["qty"] + value,
                        "entry_cf": p["entry_cf"] * p["qty"],
                    })
                else:
                    still.append(p)
            else:
                still.append(p)
        openpos = still

        mtm = 0.0
        for p in openpos:
            value = 0.0
            ok = True
            for leg in p["legs"]:
                bid, ask, mark = mk.get(("QQQ", leg[6], d), (None, None, None))
                if mark is None:
                    ok = False
                    break
                value += leg[4] * mark * M * p["qty"]
            if ok:
                mtm += value
        rows.append((d, nav0 + realized + mtm))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e["date"].iloc[-1] - e["date"].iloc[0]).days / 365.25, 1 / 365.25)
    ending = float(e["eq"].iloc[-1])
    rets = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sharpe = float(rets.mean() / rets.std(ddof=1) * math.sqrt(TD)) if rets.std(ddof=1) > 0 else 0.0

    tr = pd.DataFrame(trades)
    long_debit = float(sum(-p["entry_cf"] * p["qty"] for p in positions if p["role"] == "QQQ_LONG"))
    finance_credit = float(sum(p["entry_cf"] * p["qty"] for p in positions if p["role"] == "QQQ_FINANCE"))
    finance_pnl = float(tr.loc[tr["role"] == "QQQ_FINANCE", "pnl"].sum()) if not tr.empty else 0.0

    return {
        "name": name,
        "entries": len([p for p in positions if p["role"] == "QQQ_LONG"]),
        "ending_nav": ending,
        "cagr": float((ending / nav0) ** (1 / years) - 1),
        "maxdd": float((e["eq"] / e["eq"].cummax() - 1).min()),
        "sharpe": sharpe,
        "qqq_cycles": len([p for p in positions if p["role"] == "QQQ_LONG"]),
        "finance_trades": len([p for p in positions if p["role"] == "QQQ_FINANCE"]),
        "long_debit": long_debit,
        "finance_entry_credit": finance_credit,
        "finance_realized_pnl": finance_pnl,
        "finance_pnl_to_long_debit": finance_pnl / long_debit if long_debit > 0 else 0.0,
        "signal_count": len(signals),
    }, pd.DataFrame(signals)


def _build_term_structure(con, state, qpath, mode):
    days = entry_days(state)
    state_dates = sorted(pd.to_datetime(state.date).tolist())
    st = state.set_index("date")
    positions = []
    signals = []
    i = 0
    cycle = 0

    while i < len(days):
        d = days[i]
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            i += 1
            continue
        sig = st.loc[sigd]
        if isinstance(sig, pd.DataFrame):
            sig = sig.iloc[0]

        if any(pd.isna(sig.get(k, np.nan)) for k in ["Q_rv14", "Q_rv60"]):
            i += 1
            continue

        long_sig = qqq_rc(con, qpath, sigd, 90, 0.05, 0.25, 35)
        front_sig = qqq_short_ic(con, qpath, sigd, 14, 0.10)
        if long_sig is None or front_sig is None:
            i += 1
            continue

        front_ratio = float(front_sig["atm_iv"]) / float(sig.Q_rv14)
        back_ratio = float(sig.Q_rv60) / float(long_sig["atm_iv"])
        relative_ratio = front_ratio / back_ratio if back_ratio > 0 else np.nan

        if mode == "none":
            finance_ok = False
        elif mode == "always":
            finance_ok = True
        elif mode == "front_rich":
            finance_ok = front_ratio > 1.0
        elif mode == "relative":
            finance_ok = front_ratio > 1.0 and relative_ratio > 1.0
        else:
            raise ValueError(mode)

        signals.append({
            "cycle": cycle, "mode": mode, "signal_date": sigd, "entry_date": d,
            "rv14": float(sig.Q_rv14), "rv60": float(sig.Q_rv60),
            "front_iv14": float(front_sig["atm_iv"]), "back_iv90": float(long_sig["atm_iv"]),
            "front_ratio": front_ratio, "back_ratio": back_ratio,
            "relative_ratio": relative_ratio, "long_edge": back_ratio > 1.0,
            "finance_signal": finance_ok,
        })

        if back_ratio <= 1.0:
            i += 1
            continue

        long_pos = qqq_rc(con, qpath, d, 90, 0.05, 0.25, 35)
        if long_pos is None or long_pos["risk"] <= 0:
            i += 1
            continue

        long_exit = _first_on_or_after(state_dates, long_pos["expiry"] - pd.Timedelta(days=35))
        if long_exit is None or long_exit <= d:
            i += 1
            continue

        long_qty = int(math.floor((100000.0 * 0.05) / float(long_pos["risk"])))
        if long_qty <= 0:
            i += 1
            continue

        positions.append({
            "cycle": cycle, "role": "QQQ_LONG", "symbol": "QQQ",
            "entry": d, "exitd": long_exit, "legs": long_pos["legs"],
            "entry_cf": -float(long_pos["entry_value"]), "qty": long_qty,
        })

        if finance_ok:
            roll = d
            while roll < long_exit:
                fsig_d = prev_trading_date(state_dates, roll)
                if fsig_d is None:
                    break
                fsig = st.loc[fsig_d]
                if isinstance(fsig, pd.DataFrame):
                    fsig = fsig.iloc[0]
                if pd.isna(fsig.get("Q_rv14", np.nan)):
                    roll += pd.Timedelta(days=7)
                    continue

                front_sig_roll = qqq_short_ic(con, qpath, fsig_d, 14, 0.10)
                if front_sig_roll is not None:
                    roll_ratio = float(front_sig_roll["atm_iv"]) / float(fsig.Q_rv14)
                    if mode == "always":
                        ok = True
                    elif mode == "front_rich":
                        ok = roll_ratio > 1.0
                    else:
                        long_sig_roll = qqq_rc(con, qpath, fsig_d, 90, 0.05, 0.25, 35)
                        back_roll = (
                            float(fsig.Q_rv60) / float(long_sig_roll["atm_iv"])
                            if long_sig_roll is not None and pd.notna(fsig.Q_rv60)
                            else np.nan
                        )
                        rel_roll = roll_ratio / back_roll if np.isfinite(back_roll) and back_roll > 0 else np.nan
                        ok = roll_ratio > 1.0 and np.isfinite(rel_roll) and rel_roll > 1.0

                    if ok:
                        sp = qqq_short_ic(con, qpath, roll, 14, 0.10)
                        if sp is not None and sp["risk"] > 0:
                            short_qty = int(math.floor((100000.0 * 0.01) / float(sp["risk"])))
                            exitd = _first_on_or_after(state_dates, sp["expiry"] - pd.Timedelta(days=7))
                            if exitd is not None:
                                exitd = min(exitd, long_exit)
                                if short_qty > 0 and exitd > roll:
                                    positions.append({
                                        "cycle": cycle, "role": "QQQ_FINANCE", "symbol": "QQQ",
                                        "entry": roll, "exitd": exitd, "legs": sp["legs"],
                                        "entry_cf": float(sp["entry_value"]), "qty": short_qty,
                                    })

                roll += pd.Timedelta(days=7)

        cycle += 1
        i += 1
        while i < len(days) and days[i] <= long_exit:
            i += 1

    return positions, signals


def run_term_strategy(con, state, qpath, name, mode):
    positions, signals = _build_term_structure(con, state, qpath, mode)
    return _simulate_term_book(con, state, qpath, positions, name, signals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    d = Path(a.data_dir)
    o = Path(a.out)
    o.mkdir(parents=True, exist_ok=True)

    qpath = str(d / "QQQ_options.parquet")
    qu = str(d / "QQQ_underlying.parquet")
    for p in [qpath, qu]:
        assert Path(p).exists(), p

    con = duckdb.connect()
    st = build_state(con, qu, qu)
    st.to_csv(o / "state.csv", index=False)

    configs = [
        ("A_QQQ_25D90_ONLY", "none"),
        ("B_QQQ_25D90_PLUS_14D_ALWAYS", "always"),
        ("C_QQQ_25D90_PLUS_14D_FRONT_RICH", "front_rich"),
        ("D_QQQ_25D90_PLUS_14D_TERM_RELATIVE", "relative"),
    ]

    results = []
    signals_all = []
    for name, mode in configs:
        rr, sig = run_term_strategy(con, st, qpath, name, mode)
        if name == "A_QQQ_25D90_ONLY":
            rr["finance_trades"] = 0
            rr["finance_entry_credit"] = 0.0
            rr["finance_realized_pnl"] = 0.0
            rr["finance_pnl_to_long_debit"] = 0.0
        results.append(rr)
        if not sig.empty:
            signals_all.append(sig)

    signals_df = pd.concat(signals_all, ignore_index=True) if signals_all else pd.DataFrame()
    signals_df.to_csv(o / "signals.csv", index=False)
    (o / "results.json").write_text(json.dumps(results, indent=2, allow_nan=True), encoding="utf-8")

    lines = [
        "# QQQ Term-Structure Self-Finance V1 — real-chain replay",
        "",
        "Period: 2018-03 through 2025-12; one non-overlapping QQQ long cycle at a time.",
        "Signal state is evaluated on the PRIOR trading day; option structure is selected/fill-modelled on the actual entry date.",
        "Long convexity: QQQ 90D target reverse iron condor, long ~25Δ call/put, short ~5Δ wings, exit with 35D remaining.",
        "Finance: same-underlying QQQ 14D target iron condor, short ~50Δ call/put, long ~10Δ wings, rolled every 7 calendar days during the long cycle.",
        "Long gate: prior-day QQQ RV60 / QQQ 90D ATM IV > 1.",
        "Front-rich gate: prior-day QQQ 14D ATM IV / QQQ RV14 > 1.",
        "Term-relative gate: (14D IV/RV14) / (RV60/90D IV) > 1, with front ratio > 1.",
        "Sizing: long defined risk = 5% initial NAV per cycle; each short finance ticket = 1% initial NAV defined risk.",
        "Fill: BUY at ask, SELL at bid; daily MTM at mark=(bid+ask)/2; exit long at bid / short at ask.",
        "Liquidity: OI>=10 OR volume>=5, relative bid/ask spread<=35%.",
        "No pull_request trigger; push/manual research only; no live order transmission.",
        "",
        "| strategy | QQQ cycles | finance trades | ending NAV | CAGR | MaxDD | Sharpe | finance realized P&L / long debit |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['qqq_cycles']} | {r['finance_trades']} | "
            f"{r['ending_nav']:.2f} | {r['cagr']:.2%} | {r['maxdd']:.2%} | {r['sharpe']:.2f} | "
            f"{r['finance_pnl_to_long_debit']:.2%} |"
        )
    lines += [
        "",
        "This tests same-underlying term-structure financing of QQQ range convexity. It does not claim bonds are replaceable.",
        "Exploratory structure-family test; not a strict OOS claim.",
    ]
    (o / "RESULTS.md").write_text("\\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
