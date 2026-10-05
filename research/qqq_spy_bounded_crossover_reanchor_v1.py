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
    for w in (5, 20, 30, 60):
        d[f"rv{w}"] = r.rolling(w).std() * math.sqrt(TD)
    d["month"] = d.date.dt.to_period("M")
    return d.rename(
        columns={
            "close_px": prefix + "_px",
            "rv5": prefix + "_rv5",
            "rv20": prefix + "_rv20",
            "rv30": prefix + "_rv30",
            "rv60": prefix + "_rv60",
        }
    )[
        [
            "date",
            prefix + "_px",
            prefix + "_rv5",
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



# BOUNDED CROSSOVER / FIRST-PASSAGE HYSTERESIS V1
#
# Each object receives a causal bounded score S_i in [-10,+10] from its
# own volatility risk-premium state (ATM IV60 / RV60). D = S_QQQ - S_SPY.
# A pair trade is entered at a first-passage boundary +/-H and held until
# the opposite boundary is reached, then harvested and switched.
# This is a stateful hysteresis machine; it does NOT assume that a score
# reset guarantees a future market crossing. Defined-risk structures,
# time exits and risk-budget sizing are retained.

TD = 252
M = 100.0
START, END = "2018-03-01", "2025-12-01"
OBS_WEEKS = 52
OBS_MIN = 26
MAX_HOLD_DAYS = 45

def weekly_observation_days(state):
    z = state[(state.date >= pd.Timestamp(START)) & (state.date <= pd.Timestamp(END))].copy()
    # One observation per ISO calendar week: first available trading day.
    return [g.date.iloc[0] for _, g in z.groupby(z.date.dt.to_period("W-SUN"), sort=True)]

def atm_iv60(con, path, date):
    df = get_chain(con, path, date, 53, 67)
    if df.empty:
        return np.nan
    c = liquid(df[df.opt_type == "call"])
    p = liquid(df[df.opt_type == "put"])
    if c.empty or p.empty:
        return np.nan
    lc = c.iloc[(c.delta - 0.50).abs().argmin()]
    lp = p.iloc[(p.delta + 0.50).abs().argmin()]
    vals = [float(lc.implied_volatility), float(lp.implied_volatility)]
    if any(not np.isfinite(v) or v <= 0 for v in vals):
        return np.nan
    return float(np.mean(vals))

def bounded_percentile(values, window=OBS_WEEKS, min_periods=OBS_MIN):
    x = pd.Series(values, dtype="float64")
    out = np.full(len(x), np.nan, dtype=float)
    for i, cur in enumerate(x.to_numpy()):
        if not np.isfinite(cur):
            continue
        lo = max(0, i - window)
        hist = x.iloc[lo:i].dropna().to_numpy()
        if len(hist) < min_periods:
            continue
        less = float(np.sum(hist < cur))
        equal = float(np.sum(hist == cur))
        pct = (less + 0.5 * equal) / len(hist)
        out[i] = float(np.clip(20.0 * pct - 10.0, -10.0, 10.0))
    return out

def build_bounded_state(con, qu, su, qpath, spath):
    q = load_px(con, qu, "Q")
    s = load_px(con, su, "S")
    x = q.merge(s, on=["date", "month"], how="inner").sort_values("date").reset_index(drop=True)
    days = weekly_observation_days(x)
    st = x.set_index("date")
    rows = []
    state_dates = sorted(pd.to_datetime(x.date).tolist())

    for d in days:
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        r = st.loc[sigd]
        qrv = float(r.Q_rv60) if pd.notna(r.Q_rv60) else np.nan
        srv = float(r.S_rv60) if pd.notna(r.S_rv60) else np.nan
        qiv = atm_iv60(con, qpath, sigd)
        siv = atm_iv60(con, spath, sigd)
        q_vrp = qiv / qrv if np.isfinite(qiv) and np.isfinite(qrv) and qrv > 0 else np.nan
        s_vrp = siv / srv if np.isfinite(siv) and np.isfinite(srv) and srv > 0 else np.nan
        rows.append({
            "signal_date": pd.Timestamp(sigd),
            "entry_date": pd.Timestamp(d),
            "q_rv60": qrv,
            "s_rv60": srv,
            "q_iv60": qiv,
            "s_iv60": siv,
            "q_vrp": q_vrp,
            "s_vrp": s_vrp,
        })

    z = pd.DataFrame(rows).sort_values("entry_date").reset_index(drop=True)
    z["q_score"] = bounded_percentile(z.q_vrp)
    z["s_score"] = bounded_percentile(z.s_vrp)
    z["d_score"] = z.q_score - z.s_score
    return z

def normalize_position(p, direction):
    z = p.copy()
    z["direction"] = direction
    z["cashflow"] = (-p["entry_value"]) if p["symbol"] == "QQQ" else p["entry_value"]
    # Inverting the 4 legs flips long-vol <-> short-vol and swaps
    # max-loss / max-profit for the defined-risk structure.
    return z

def invert_position(p):
    z = p.copy()
    z["legs"] = [
        (leg[0], leg[1], leg[2], leg[3], -leg[4], leg[5], leg[6])
        for leg in p["legs"]
    ]
    z["entry_value"] = -p["entry_value"]
    z["risk"], z["profit"] = max(float(p["profit"]), 0.0), max(float(p["risk"]), 0.0)
    z["cashflow"] = -float(p["cashflow"])
    return z

def make_pair(con, qpath, spath, d, direction, name):
    # +1: QQQ vol rich versus SPY -> short QQQ vol / long SPY vol.
    # -1: QQQ vol cheap versus SPY -> long QQQ vol / short SPY vol.
    q = qqq_rc(con, qpath, d, 60, 0.10, 0.50, 35)
    s = spy_ic(con, spath, d, 60, 0.10)
    if q is None or s is None:
        return None
    q["cashflow"] = -float(q["entry_value"])
    s["cashflow"] = float(s["entry_value"])
    if direction > 0:
        q = invert_position(q)
        s = normalize_position(s, direction)
        # Long SPY vol = invert the short iron condor.
        s = invert_position(s)
        s["direction"] = direction
    else:
        q["direction"] = direction
        s = normalize_position(s, direction)
    # Recompute cashflows after inversion and attach cycle identity.
    for p in (q, s):
        p["cycle"] = name
        p["entry"] = pd.Timestamp(d)
    q["entry_cashflow"] = float(q["cashflow"])
    s["entry_cashflow"] = float(s["cashflow"])
    return [q, s]

def pair_value(p, marks_map, d, qty=1):
    v = float(p["cashflow"]) * qty
    ok = True
    for leg in p["legs"]:
        b, a, m = marks_map.get((leg[6], d), (None, None, None))
        if m is None:
            ok = False
            break
        # Exit convention: longs hit bid, shorts hit ask.
        fill = b if leg[4] == 1 else a
        v += leg[4] * fill * M * qty
    return v, ok

def pair_mtm(p, marks_map, d, qty=1):
    v = float(p["cashflow"]) * qty
    ok = True
    for leg in p["legs"]:
        b, a, m = marks_map.get((leg[6], d), (None, None, None))
        if m is None:
            ok = False
            break
        v += leg[4] * m * M * qty
    return v, ok

def generate_cycles(con, state, qpath, spath, threshold):
    events = state[state.d_score.notna()].reset_index(drop=True)
    cycles = []
    active = None
    blocked = False
    cycle_no = 0

    for row in events.itertuples(index=False):
        d = pd.Timestamp(row.entry_date)
        score = float(row.d_score)

        if active is None:
            if blocked:
                # Hysteresis re-arm: after a timeout / structure failure,
                # require the spread to come back inside a small central band.
                if abs(score) <= 2.0:
                    blocked = False
                else:
                    continue
            if score >= threshold:
                direction = 1
            elif score <= -threshold:
                direction = -1
            else:
                continue

            pair = make_pair(con, qpath, spath, d, direction, f"cycle_{cycle_no:04d}")
            if pair is None:
                continue
            active = {
                "pair": pair,
                "direction": direction,
                "entry_date": d,
                "entry_score": score,
                "expiry": min(p["expiry"] for p in pair),
                "risk_per_pair_pct": 0.05,
                "cycle_no": cycle_no,
            }
            cycle_no += 1
            continue

        target = -threshold if active["direction"] > 0 else threshold
        age = (d - active["entry_date"]).days
        expiry_limit = min(
            active["expiry"] - pd.Timedelta(days=5),
            active["entry_date"] + pd.Timedelta(days=MAX_HOLD_DAYS),
        )

        if score * active["direction"] <= -threshold:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "OPPOSITE_BOUNDARY"
            cycles.append(active)
            # Switch at the reached opposite peak.
            pair = make_pair(
                con, qpath, spath, d,
                -active["direction"],
                f"cycle_{cycle_no:04d}",
            )
            if pair is None:
                active = None
                blocked = True
                continue
            active = {
                "pair": pair,
                "direction": -active["direction"],
                "entry_date": d,
                "entry_score": score,
                "expiry": min(p["expiry"] for p in pair),
                "risk_per_pair_pct": 0.05,
                "cycle_no": cycle_no,
            }
            cycle_no += 1
        elif d >= expiry_limit:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "TIME_EXIT"
            cycles.append(active)
            active = None
            blocked = True

    if active is not None:
        # End-of-sample close on the last observed point available.
        last_d = pd.Timestamp(events.entry_date.iloc[-1])
        active["exit_date"] = last_d
        active["exit_score"] = float(events.d_score.iloc[-1])
        active["exit_reason"] = "SAMPLE_END"
        cycles.append(active)
    return cycles

def simulate_threshold(con, state, qpath, spath, name, threshold):
    cycles = generate_cycles(con, state, qpath, spath, threshold)
    flat_candidates = []
    for c in cycles:
        for p in c["pair"]:
            p2 = p.copy()
            p2["cycle"] = c["cycle_no"]
            p2["exit_date"] = c["exit_date"]
            p2["exit_reason"] = c["exit_reason"]
            p2["entry_score"] = c["entry_score"]
            p2["exit_score"] = c["exit_score"]
            flat_candidates.append(p2)

    if not flat_candidates:
        return {
            "name": name, "entries": 0, "cycles": 0, "ending_nav": 100000.0,
            "cagr": 0.0, "maxdd": 0.0, "sharpe": 0.0,
            "opposite_boundary_exits": 0, "time_exits": 0, "sample_end_exits": 0,
            "crossing_cycles": 0, "mean_abs_peak_to_peak": np.nan,
        }, pd.DataFrame()

    marks = unit_marks(con, qpath, spath, flat_candidates)
    mk = {(r.contract_id, r.date):(float(r.bid), float(r.ask), float(r.mark)) for r in marks.itertuples(index=False)}

    nav = 100000.0
    realized = 0.0
    rows = []
    used = set()
    openpos = []
    events_by_date = {}
    for c in cycles:
        events_by_date.setdefault(pd.Timestamp(c["entry_date"]), []).append(("OPEN", c))
    for c in cycles:
        events_by_date.setdefault(pd.Timestamp(c["exit_date"]), []).append(("CLOSE", c))

    cycle_sizes = {}
    for d in sorted(pd.to_datetime(state.entry_date.tolist())):
        # Close before open on the same day: harvest is credited before the switch.
        for action, c in events_by_date.get(d, []):
            if action != "CLOSE":
                continue
            for p in openpos[:]:
                if p.get("cycle") != c["cycle_no"]:
                    continue
                qty = p["qty"]
                v, ok = pair_value(p, mk, d, qty)
                if ok:
                    realized += v
                    openpos.remove(p)

        for action, c in events_by_date.get(d, []):
            if action != "OPEN":
                continue
            share_risk = 0.025
            # Use current NAV immediately before the new cycle.
            risk_target = max(nav, 1.0) * share_risk
            opened = True
            newpos = []
            for p in c["pair"]:
                qty = max(1, int(math.floor(risk_target / max(float(p["risk"]), 1e-9))))
                p2 = p.copy()
                p2["qty"] = qty
                newpos.append(p2)
            openpos.extend(newpos)
            cycle_sizes[c["cycle_no"]] = sum(max(float(p["risk"]), 0.0)*p["qty"] for p in newpos)

        mtm = 0.0
        for p in openpos:
            v, ok = pair_mtm(p, mk, d, p["qty"])
            if ok:
                mtm += v
        nav = 100000.0 + realized + mtm
        rows.append((d, nav))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e.date.iloc[-1]-e.date.iloc[0]).days/365.25, 1/365.25)
    ending = float(e.eq.iloc[-1])
    cagr = (ending/100000.0)**(1/years)-1
    dd = float((e.eq/e.eq.cummax()-1).min())
    rr = e.eq.pct_change().replace([np.inf,-np.inf],np.nan).fillna(0)
    sh = float(rr.mean()/rr.std(ddof=1)*math.sqrt(TD)) if rr.std(ddof=1)>0 else 0.0

    sd = state[state.d_score.notna()].copy()
    zero_cross = 0
    for c in cycles:
        lo, hi = sorted([float(c["entry_score"]), float(c["exit_score"])])
        if lo <= 0 <= hi:
            zero_cross += 1
    reason_counts = pd.Series([c["exit_reason"] for c in cycles]).value_counts().to_dict()
    cycle_report = pd.DataFrame([{
        "cycle": c["cycle_no"],
        "entry": c["entry_date"],
        "exit": c["exit_date"],
        "entry_score": c["entry_score"],
        "exit_score": c["exit_score"],
        "direction": c["direction"],
        "reason": c["exit_reason"],
        "days": (c["exit_date"]-c["entry_date"]).days,
    } for c in cycles])

    result = {
        "name": name,
        "threshold": float(threshold),
        "entries": len(flat_candidates),
        "cycles": len(cycles),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": dd,
        "sharpe": sh,
        "opposite_boundary_exits": int(reason_counts.get("OPPOSITE_BOUNDARY",0)),
        "time_exits": int(reason_counts.get("TIME_EXIT",0)),
        "sample_end_exits": int(reason_counts.get("SAMPLE_END",0)),
        "crossing_cycles": int(zero_cross),
        "mean_hold_days": float(cycle_report.days.mean()) if not cycle_report.empty else np.nan,
        "median_hold_days": float(cycle_report.days.median()) if not cycle_report.empty else np.nan,
        "mean_abs_peak_to_peak": float(np.abs(cycle_report.exit_score-cycle_report.entry_score).mean()) if not cycle_report.empty else np.nan,
        "mean_q_score_at_entry": float(state.loc[state.entry_date.isin(cycle_report.entry), "q_score"].mean()) if not cycle_report.empty else np.nan,
        "mean_s_score_at_entry": float(state.loc[state.entry_date.isin(cycle_report.entry), "s_score"].mean()) if not cycle_report.empty else np.nan,
    }
    cycle_report["strategy"] = name
    return result, cycle_report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
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
    state = build_bounded_state(con, qu, su, qpath, spath)
    state.to_csv(o / "bounded_state.csv", index=False)

    # Pre-committed exploratory boundary family. No "search until PASS":
    # all thresholds are reported side-by-side and are not selected on OOS.
    cfg = [
        ("A_BFPH_H6", 6.0),
        ("B_BFPH_H8", 8.0),
        ("C_BFPH_H10", 10.0),
        ("D_BFPH_H12", 12.0),
    ]

    results = []
    reports = []
    for name, h in cfg:
        rr, rep = simulate_threshold(con, state, qpath, spath, name, h)
        results.append(rr)
        reports.append(rep)

    results_df = pd.DataFrame(results)
    results_df.to_csv(o / "results.csv", index=False)
    if any(not x.empty for x in reports):
        pd.concat(reports, ignore_index=True).to_csv(o / "cycles.csv", index=False)
    else:
        pd.DataFrame().to_csv(o / "cycles.csv", index=False)

    state_info = {
        "start": START,
        "end": END,
        "score": "20*causal rolling percentile(IV60/RV60)-10, clipped to [-10,+10]",
        "relative": "D = QQQ_score - SPY_score in [-20,+20]",
        "observation": "first trading day of each calendar week; signal evaluated on prior trading day",
        "entry": "|D| >= H",
        "switch": "close at opposite boundary and switch direction at that observed entry day",
        "rearm_after_time_exit": "|D| <= 2",
        "max_hold_days": MAX_HOLD_DAYS,
        "position": "QQQ 60D reverse iron condor + SPY 60D iron condor; direction is inverted as needed",
        "risk_budget": "2.5% NAV theoretical max-loss per leg, 5% total pair budget",
        "fills": "BUY at ask, SELL at bid; daily MTM at mark=(bid+ask)/2",
        "data": "LambdaClass real option chain + underlying, 2018-03 through 2025-12",
    }
    (o / "METHODOLOGY.json").write_text(json.dumps(state_info, indent=2), encoding="utf-8")

    lines = [
        "# QQQ-SPY Bounded Crossover / First-Passage Hysteresis V1",
        "",
        "This experiment tests the user's two-object bounded-score idea using a real option chain.",
        "Each object is mapped to a causal score in [-10,+10], D=QQQ-SPY in [-20,+20].",
        "The position enters at +/-H and is held to the opposite boundary; then it is harvested and switched.",
        "A time exit forces a central re-arm (|D|<=2). The coordinate reset is NOT treated as a guarantee of market crossover.",
        "",
        "Period: 2018-03 through 2025-12; weekly observation; signal from prior trading day.",
        "Score basis: ATM IV60 / RV60, transformed by a rolling 52-week percentile with 26-point minimum history.",
        "QQQ structure: 60D reverse iron condor, long ~50Δ call/put, short ~10Δ wings.",
        "SPY structure: 60D iron condor, short ~50Δ call/put, long ~10Δ wings.",
        "Direction +: short QQQ vol / long SPY vol. Direction -: long QQQ vol / short SPY vol.",
        "Risk budget: 2.5% NAV theoretical max-loss per leg, 5% total pair.",
        "No live order transmission.",
        "",
        "| strategy | H | cycles | ending NAV | CAGR | MaxDD | Sharpe | opposite-boundary | time exits | zero-cross cycles |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['threshold']:.0f} | {r['cycles']} | {r['ending_nav']:.2f} | "
            f"{r['cagr']:.2%} | {r['maxdd']:.2%} | {r['sharpe']:.2f} | "
            f"{r['opposite_boundary_exits']} | {r['time_exits']} | {r['crossing_cycles']} |"
        )
    lines += [
        "",
        "Exploratory screen only. Threshold family is precommitted; no OOS claim and no parameter selected from the reported OOS sample.",
    ]
    (o / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
