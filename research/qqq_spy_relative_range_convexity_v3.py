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


def simulate(con, state, qpath, spath, name, mode, include_spy, q_target=60, q_long_delta=0.50, q_wing=0.10, q_exit_dte=25):
    days = entry_days(state)
    state_dates = sorted(pd.to_datetime(state.date).tolist())
    st = state.set_index("date")
    candidates = []
    signals = []
    last_q = pd.Timestamp.min
    last_s = pd.Timestamp.min

    for d in days:
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        s = st.loc[sigd]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[0]
        if any(pd.isna(s[k]) for k in ["Q_rv60", "S_rv30"]):
            continue

        q_sig = qqq_rc(con, qpath, sigd, q_target, q_wing, q_long_delta, q_exit_dte)
        sp_sig = spy_ic(con, spath, sigd, 30, 0.10) if include_spy else None
        if q_sig is None:
            continue

        q_ratio = float(s.Q_rv60) / float(q_sig["atm_iv"])
        s_ratio = (
            float(sp_sig["atm_iv"]) / float(s.S_rv30)
            if sp_sig is not None
            else np.nan
        )
        q_gap = float(s.Q_rv60) - float(q_sig["atm_iv"])
        s_gap = (
            float(sp_sig["atm_iv"]) - float(s.S_rv30)
            if sp_sig is not None
            else np.nan
        )
        combined = q_ratio * s_ratio if np.isfinite(s_ratio) else np.nan
        relative = q_ratio / s_ratio if np.isfinite(s_ratio) and s_ratio > 0 else np.nan

        signals.append({
            "strategy": name,
            "signal_date": sigd,
            "entry_date": d,
            "q_rv60": float(s.Q_rv60),
            "q_iv60": float(q_sig["atm_iv"]),
            "q_ratio": q_ratio,
            "q_gap": q_gap,
            "s_rv30": float(s.S_rv30),
            "s_iv30": float(sp_sig["atm_iv"]) if sp_sig is not None else np.nan,
            "s_ratio": s_ratio,
            "s_gap": s_gap,
            "combined_ratio": combined,
            "relative_ratio": relative,
            "rr20": float(s.rr20) if pd.notna(s.rr20) else np.nan,
            "rv_velocity": float(s.rv_velocity) if pd.notna(s.rv_velocity) else np.nan,
        })

        if mode == "qqq_edge":
            eligible = q_ratio > 1.0
        elif mode == "pair_both":
            eligible = q_ratio > 1.0 and s_ratio > 1.0
        elif mode == "pair_combined":
            eligible = np.isfinite(combined) and combined > 1.0 and q_ratio > 0.90
        elif mode == "pair_relative":
            eligible = (
                np.isfinite(relative)
                and relative > 1.0
                and q_ratio > 1.0
            )
        else:
            eligible = False

        if not eligible:
            continue

        q = qqq_rc(con, qpath, d, q_target, q_wing, q_long_delta, q_exit_dte)
        sp = spy_ic(con, spath, d, 30, 0.10) if include_spy else None
        if q is not None and d >= last_q:
            q["name"] = f"{name}_Q_{len(candidates)}"
            q["signal_date"] = sigd
            q["q_ratio"] = q_ratio
            q["s_ratio"] = s_ratio
            candidates.append(q)
            target_exit = q["expiry"] - pd.Timedelta(days=q["exit_dte"])
            ix = min(len(state_dates) - 1, max(0, np.searchsorted(state_dates, target_exit, side="left")))
            last_q = pd.Timestamp(state_dates[ix])

        if sp is not None and d >= last_s:
            sp["name"] = f"{name}_S_{len(candidates)}"
            sp["signal_date"] = sigd
            sp["q_ratio"] = q_ratio
            sp["s_ratio"] = s_ratio
            candidates.append(sp)
            target_exit = sp["expiry"] - pd.Timedelta(days=sp["exit_dte"])
            ix = min(len(state_dates) - 1, max(0, np.searchsorted(state_dates, target_exit, side="left")))
            last_s = pd.Timestamp(state_dates[ix])

    if not candidates:
        return {
            "name": name,
            "entries": 0,
            "ending_nav": 100000.0,
            "cagr": 0.0,
            "maxdd": 0.0,
            "sharpe": 0.0,
            "q_entries": 0,
            "s_entries": 0,
            "signal_count": len(signals),
            "eligible_count": 0,
        }, pd.DataFrame(signals)

    marks = unit_marks(con, qpath, spath, candidates)
    mk = {
        (r.contract_id, r.date): (float(r.bid), float(r.ask), float(r.mark))
        for r in marks.itertuples(index=False)
    }

    nav = 100000.0
    openpos = []
    realized = 0.0
    rows = []
    used = set()
    qn = sum(p["symbol"] == "QQQ" for p in candidates)
    sn = sum(p["symbol"] == "SPY" for p in candidates)

    for d in state_dates:
        for p in candidates:
            if p["name"] in used or p["entry"] != d:
                continue
            share = 1.0 if not include_spy else (0.60 if p["symbol"] == "QQQ" else 0.40)
            qty = (
                max(1, int(math.floor((nav * 0.05 * share) / p["risk"])))
                if p["risk"] > 0
                else 0
            )
            if qty <= 0:
                used.add(p["name"])
                continue
            p2 = p.copy()
            p2["qty"] = qty
            openpos.append(p2)
            used.add(p["name"])

        still = []
        for p in openpos:
            exitd = max(d, p["expiry"] - pd.Timedelta(days=p["exit_dte"]))
            if d == exitd:
                v = 0.0
                ok = True
                for leg in p["legs"]:
                    b, a, m = mk.get((leg[6], d), (None, None, None))
                    if m is None:
                        ok = False
                        break
                    fill = b if leg[4] == 1 else a
                    v += leg[4] * fill * M * p["qty"]
                if ok:
                    entry_cf = (
                        -p["entry_value"] if p["symbol"] == "QQQ" else p["entry_value"]
                    ) * p["qty"]
                    realized += entry_cf + v
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
                b, a, m = mk.get((leg[6], d), (None, None, None))
                if m is None:
                    ok = False
                    break
                v += leg[4] * m * M * p["qty"]
            if ok:
                entry_cf = (
                    -p["entry_value"] if p["symbol"] == "QQQ" else p["entry_value"]
                ) * p["qty"]
                mtm += entry_cf + v

        eq = nav = 100000.0 + realized + mtm
        rows.append((d, eq))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e.date.iloc[-1] - e.date.iloc[0]).days / 365.25, 1 / 365.25)
    ending = float(e["eq"].iloc[-1])
    cagr = (ending / 100000.0) ** (1 / years) - 1
    dd = (e["eq"] / e["eq"].cummax() - 1).min()
    r = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sh = (r.mean() / r.std(ddof=1) * math.sqrt(TD)) if r.std(ddof=1) > 0 else 0.0

    sigdf = pd.DataFrame(signals)
    eligible_count = len(candidates)
    result = {
        "name": name,
        "entries": len(candidates),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": float(dd),
        "sharpe": float(sh),
        "q_entries": qn,
        "s_entries": sn,
        "signal_count": len(sigdf),
        "eligible_count": eligible_count,
        "mean_q_ratio": float(sigdf.q_ratio.mean()) if not sigdf.empty else np.nan,
        "mean_s_ratio": float(sigdf.s_ratio.mean()) if not sigdf.empty else np.nan,
    }
    return result, sigdf


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
    st = build_state(con, qu, su)
    st.to_csv(o / "state.csv", index=False)

    cfg = [
        ("A_50D60_QQQ_ONLY", "qqq_edge", False, 60, 0.50, 0.10, 25),
        ("B_35D60_QQQ_ONLY", "qqq_edge", False, 60, 0.35, 0.10, 25),
        ("C_25D60_QQQ_ONLY", "qqq_edge", False, 60, 0.25, 0.10, 25),
        ("D_25D90_QQQ_ONLY", "qqq_edge", False, 90, 0.25, 0.10, 35),
        ("E_50D60_PAIR_RELATIVE", "pair_relative", True, 60, 0.50, 0.10, 25),
        ("F_35D60_PAIR_RELATIVE", "pair_relative", True, 60, 0.35, 0.10, 25),
        ("G_25D60_PAIR_RELATIVE", "pair_relative", True, 60, 0.25, 0.10, 25),
        ("H_25D90_PAIR_RELATIVE", "pair_relative", True, 90, 0.25, 0.10, 35),
    ]

    res = []
    all_signals = []
    for name, mode, include_spy, q_target, q_long_delta, q_wing, q_exit_dte in cfg:
        rr, sig = simulate(
            con, st, qpath, spath, name, mode, include_spy,
            q_target=q_target, q_long_delta=q_long_delta,
            q_wing=q_wing, q_exit_dte=q_exit_dte
        )
        res.append(rr)
        all_signals.append(sig)

    signals_df = (
        pd.concat(all_signals, ignore_index=True)
        if all_signals and any(not x.empty for x in all_signals)
        else pd.DataFrame()
    )
    signals_df.to_csv(o / "signals.csv", index=False)
    (o / "results.json").write_text(json.dumps(res, indent=2, allow_nan=True), encoding="utf-8")

    lines = [
        "# QQQ-SPY Relative Range Convexity V3 — real-chain replay",
        "",
        "Period: 2018-03 through 2025-12; entry is first trading day of each month.",
        "Signal is evaluated on the PRIOR trading day; actual option structure is selected/fill-modelled on entry day.",
        "QQQ: 60D target reverse iron condor, long ~50Δ call/put, short ~10Δ wings, exit 25D.",
        "SPY: 30D target iron condor, short ~50Δ call/put, long ~10Δ wings, exit 7D.",
        "QQQ long-vol edge: prior-day QQQ RV60 / ATM IV60 > 1.",
        "SPY short-vol edge: prior-day ATM IV30 / RV30 > 1.",
        "Combined edge: (QQQ RV60/IV60) * (SPY IV30/RV30) > 1, with QQQ ratio > 0.90.",
        "Relative edge: (QQQ RV60/IV60) / (SPY IV30/RV30) > 1, with QQQ ratio > 1.",
        "Fill: BUY at ask, SELL at bid; daily MTM at mark=(bid+ask)/2; exit long at bid / short at ask.",
        "Liquidity: OI>=10 OR volume>=5, relative bid/ask spread<=35%.",
        "Risk sizing: 5% NAV total; QQQ-only uses 100% QQQ risk; pair uses 60% QQQ / 40% SPY.",
        "No pull_request trigger; this research workflow is push/manual only.",
        "",
        "| strategy | entries | ending NAV | CAGR | MaxDD | Sharpe | QQQ | SPY |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for r in res:
        lines.append(
            f"| {r['name']} | {r['entries']} | {r['ending_nav']:.2f} | "
            f"{r['cagr']:.2%} | {r['maxdd']:.2%} | {r['sharpe']:.2f} | "
            f"{r['q_entries']} | {r['s_entries']} |"
        )

    lines += [
        "",
        "This is an exploratory structure-family screen, not a production strategy and not an OOS claim; no live order transmission.",
    ]
    (o / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
