#!/usr/bin/env python3
"""QQQ ORIGINAL SENTENCE LOOP V1 — research only, not a live signal.

Frozen from the user's own sentences:
  QQQ 升很多 → SHORT CALL 近一點, SHORT PUT 更 OTM, LONG PUT 同時在
  超過某波值才因應買賣; T 觸發, T+1 執行
  跨日期半堆疊 / 儲飛尾
  臨近 SHORT CALL 後一日下跌 → 先鎖至少一半盈利再變陣
  N+50 對 1 張先試; 用已實現正收益才准下一輪 N+20
  2% risk gate 不過就記錄 REJECT, 不准偷偷縮比例
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

CAPITAL = 100000.0
BASE_N = 2
SEED_N = BASE_N + 50
RECYCLE_N = BASE_N + 20
RISK_PCT = 0.02
STACK_K = 2
HOLD_MAX = 30
DTE_MIN, DTE_MAX = 18, 35
ATR_MULT = 1.0
APPROACH = 0.98
START = pd.Timestamp("2018-03-01")
END = pd.Timestamp("2025-12-16")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load_underlying(path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path)
    x.columns = [c.lower() for c in x.columns]
    px = "adjclose" if "adjclose" in x.columns else ("adj_close" if "adj_close" in x.columns else "close")
    x["date"] = pd.to_datetime(x["date"]).dt.tz_localize(None).dt.normalize()
    x = x[(x.date >= START) & (x.date <= END)].sort_values("date").drop_duplicates("date").reset_index(drop=True)
    x["close"] = x[px].astype(float)
    x["ret"] = x.close.pct_change()
    tr = x.close.diff().abs()
    x["atr20"] = tr.rolling(20, min_periods=20).mean()
    x["peak252"] = x.close.rolling(252, min_periods=60).max()
    x["sma200"] = x.close.rolling(200, min_periods=60).mean()
    x["signal"] = (x.close / x.peak252 >= 0.98) & (x.close / x.sma200 - 1 >= 0.08)
    return x


def duck(con, sql, p=None):
    return con.execute(sql, p or []).df()


def chain(con, opt_path, dt, expiry=None):
    sql = """
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark,
             CAST(delta AS DOUBLE) AS delta,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume,
             UPPER(type) AS type
      FROM read_parquet(?)
      WHERE CAST(date AS DATE)=?
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND delta IS NOT NULL
    """
    pars = [str(opt_path), pd.Timestamp(dt).date()]
    if expiry is None:
        sql += """ AND CAST(expiration AS DATE) BETWEEN
                   CAST(date AS DATE)+INTERVAL 18 DAY AND CAST(date AS DATE)+INTERVAL 35 DAY"""
    else:
        sql += " AND CAST(expiration AS DATE)=?"
        pars.append(pd.Timestamp(expiry).date())
    g = duck(con, sql, pars)
    if g.empty:
        return g
    g["date"] = pd.to_datetime(g.date)
    g["expiration"] = pd.to_datetime(g.expiration)
    g["dte"] = (g.expiration - pd.Timestamp(dt)).dt.days
    return g


def pick(df, delta, gt=None, lt=None):
    x = df.copy()
    if gt is not None:
        x = x[x.strike > float(gt)]
    if lt is not None:
        x = x[x.strike < float(lt)]
    if x.empty:
        return None
    x = x.assign(err=(x.delta - float(delta)).abs())
    return x.sort_values(["err", "volume"], ascending=[True, False]).iloc[0]


def select_entry(con, opt_path, dt, spot):
    r = chain(con, opt_path, dt)
    if r.empty:
        return None
    ex = (
        r.groupby("expiration", as_index=False)
        .agg(dte=("dte", "first"), mv=("volume", "max"))
        .sort_values(["dte", "mv"], ascending=[True, False])
        .iloc[0]["expiration"]
    )
    g = r[r.expiration == pd.Timestamp(ex)]
    c, p = g[g.type == "CALL"], g[g.type == "PUT"]
    atm = pick(c, 0.50)
    if atm is None:
        return None
    sc = pick(c, 0.20, gt=max(float(atm.strike), float(spot)))
    if sc is None:
        return None
    wing = pick(c, 0.08, gt=float(sc.strike))
    if wing is None:
        return None
    lp = pick(p, -0.25, lt=float(spot))
    if lp is None:
        return None
    sp = pick(p, -0.10, lt=float(lp.strike))
    if sp is None:
        return None
    return {
        "expiry": pd.Timestamp(ex),
        "atm": {"id": str(atm.contract_id), "k": float(atm.strike)},
        "sc": {"id": str(sc.contract_id), "k": float(sc.strike)},
        "wing": {"id": str(wing.contract_id), "k": float(wing.strike)},
        "lp": {"id": str(lp.contract_id), "k": float(lp.strike)},
        "sp": {"id": str(sp.contract_id), "k": float(sp.strike)},
    }


def quotes(con, opt_path, ids, start, end):
    ids = sorted({str(x) for x in ids})
    q = duck(
        con,
        """
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask, CAST(mark AS DOUBLE) AS mark
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
    """,
        [str(opt_path), ids, pd.Timestamp(start).date(), pd.Timestamp(end).date()],
    )
    if q.empty:
        return q
    q["date"] = pd.to_datetime(q.date)
    q["contract_id"] = q.contract_id.astype(str)
    return q.drop_duplicates(["date", "contract_id"]).set_index(["date", "contract_id"]).sort_index()


def q_at(q, dt, cid):
    try:
        r = q.loc[(pd.Timestamp(dt), str(cid))]
    except KeyError:
        return None
    if pd.isna(r.bid) or pd.isna(r.ask):
        return None
    return {"bid": float(r.bid), "ask": float(r.ask), "mark": float(r.mark) if pd.notna(r.mark) else (float(r.bid) + float(r.ask)) / 2}


def px(qq, side):
    if qq is None:
        return np.nan
    return qq["ask"] if side == "BUY" else qq["bid"]


def mid(qq):
    return np.nan if qq is None else (qq["bid"] + qq["ask"]) / 2


def package_cf(q, dt, ids, n, closing: bool):
    qa, qs, qw, ql, qp = [q_at(q, dt, ids[k]) for k in ("atm", "sc", "wing", "lp", "sp")]
    if closing:
        vals = [px(qa, "SELL"), px(qs, "BUY"), px(qw, "SELL"), px(ql, "SELL"), px(qp, "BUY")]
    else:
        vals = [px(qa, "BUY"), px(qs, "SELL"), px(qw, "BUY"), px(ql, "BUY"), px(qp, "SELL")]
    if any(pd.isna(v) for v in vals):
        return None
    return (vals[0] - n * vals[1] + n * vals[2] + vals[3] - vals[4]) * 100


def package_mid(q, dt, ids, n):
    parts = [q_at(q, dt, ids[k]) for k in ("atm", "sc", "wing", "lp", "sp")]
    if any(p is None for p in parts):
        return np.nan
    ma, ms, mw, ml, mp = [mid(p) for p in parts]
    return (ma - n * ms + n * mw + ml - mp) * 100


def risk_proxy(legs, n, spot, q, dt):
    ids = {k: legs[k]["id"] for k in ("atm", "sc", "wing", "lp", "sp")}
    qa, qs, qw, ql, qp = [q_at(q, dt, ids[k]) for k in ("atm", "sc", "wing", "lp", "sp")]
    if any(x is None for x in (qa, qs, qw, ql, qp)):
        return None
    init = (qa["ask"] - n * qs["bid"] + n * qw["ask"] + ql["ask"] - qp["bid"]) * 100
    grid = np.linspace(max(1.0, spot * 0.5), max(spot * 1.8, legs["wing"]["k"] * 1.2), 800)
    pay = (
        np.maximum(grid - legs["atm"]["k"], 0)
        - n * np.maximum(grid - legs["sc"]["k"], 0)
        + n * np.maximum(grid - legs["wing"]["k"], 0)
        + np.maximum(legs["lp"]["k"] - grid, 0)
        - np.maximum(legs["sp"]["k"] - grid, 0)
    ) * 100
    return max(0.0, -float(np.min(pay - init)))


def trade(con, opt_path, u, row, legs, n):
    entry = pd.Timestamp(row.date)
    last = min(entry + pd.Timedelta(days=HOLD_MAX), pd.Timestamp(legs["expiry"]))
    w = u[(u.date >= entry) & (u.date <= last)].reset_index(drop=True)
    if w.empty:
        return None, "NO_WINDOW"
    ids = {k: legs[k]["id"] for k in ("atm", "sc", "wing", "lp", "sp")}
    events = []
    extra_ids = set()
    anchor = float(row.close)
    wave_done = False
    harvest_done = False
    n_sc = n
    approach = False
    for j in range(1, len(w)):
        prev, cur = w.iloc[j - 1], w.iloc[j]
        t1 = pd.Timestamp(cur.date)
        if (not harvest_done) and approach and float(cur.close) < float(prev.close):
            events.append({"date": str(t1.date()), "kind": "HARVEST50_ARM"})
            harvest_done = True
        if float(prev.close) >= APPROACH * float(legs["sc"]["k"]):
            approach = True
        atr = float(prev.atr20) if pd.notna(prev.atr20) else np.nan
        if wave_done or pd.isna(atr):
            continue
        if float(prev.close) < anchor + ATR_MULT * atr:
            continue
        g = chain(con, opt_path, t1, legs["expiry"])
        if g.empty:
            continue
        c, p = g[g.type == "CALL"], g[g.type == "PUT"]
        nc = pick(c, 0.30, gt=max(legs["atm"]["k"], float(cur.close)), lt=legs["wing"]["k"])
        np_ = pick(p, -0.05, lt=min(legs["lp"]["k"], float(cur.close)))
        if nc is None or np_ is None:
            continue
        extra_ids.add(str(nc.contract_id))
        extra_ids.add(str(np_.contract_id))
        events.append(
            {
                "date": str(t1.date()),
                "kind": "WAVE1_MIGRATE",
                "new_sc": str(nc.contract_id),
                "new_sc_k": float(nc.strike),
                "new_sp": str(np_.contract_id),
                "new_sp_k": float(np_.strike),
            }
        )
        wave_done = True

    all_ids = set(ids.values()) | extra_ids
    q = quotes(con, opt_path, all_ids, entry, last)
    risk = risk_proxy(legs, n, float(row.close), q, entry)
    if risk is None:
        return None, "NO_ENTRY_QUOTES"
    if risk > CAPITAL * RISK_PCT:
        return None, "RISK_GATE"
    ec = package_cf(q, entry, ids, n_sc, False)
    if ec is None:
        return None, "NO_ENTRY_QUOTES"
    cash = -float(ec)
    trough = cash
    eq = []
    by = {pd.Timestamp(e["date"]): e for e in events}
    for _, r in w.iterrows():
        dt = pd.Timestamp(r.date)
        ev = by.get(dt)
        if ev and ev["kind"] == "WAVE1_MIGRATE":
            old_sc, old_sp = ids["sc"], ids["sp"]
            q_old_s, q_new_s = q_at(q, dt, old_sc), q_at(q, dt, ev["new_sc"])
            q_old_p, q_new_p = q_at(q, dt, old_sp), q_at(q, dt, ev["new_sp"])
            if q_old_s and q_new_s and q_old_p and q_new_p:
                # buy back old shorts/puts @ ask, sell new @ bid
                cf = n_sc * (q_new_s["bid"] - q_old_s["ask"]) * 100 + (q_new_p["bid"] - q_old_p["ask"]) * 100
                cash += cf
                ids["sc"], ids["sp"] = ev["new_sc"], ev["new_sp"]
                ev["migration_cf"] = float(cf)
        if ev and ev["kind"] == "HARVEST50_ARM" and n_sc >= 2:
            rec = cash - trough
            if rec > 0:
                half = n_sc // 2
                qs, qw = q_at(q, dt, ids["sc"]), q_at(q, dt, ids["wing"])
                if qs and qw:
                    # buy back half shorts @ ask, sell half wings @ bid
                    cf = half * (-qs["ask"] + qw["bid"]) * 100
                    cash += cf
                    n_sc -= half
                    ev["harvest_cf"] = float(cf)
                    ev["n_after"] = n_sc
        mk = package_mid(q, dt, ids, n_sc)
        if pd.notna(mk):
            nav = CAPITAL + cash + mk
            eq.append((dt, nav))
            trough = min(trough, cash + mk)
    xc = package_cf(q, pd.Timestamp(w.iloc[-1].date), ids, n_sc, True)
    if xc is None:
        return None, "NO_EXIT_QUOTES"
    pnl = cash + float(xc)
    eq.append((pd.Timestamp(w.iloc[-1].date), CAPITAL + pnl))
    return {
        "entry": entry,
        "exit": pd.Timestamp(w.iloc[-1].date),
        "n_open": int(n),
        "n_close": int(n_sc),
        "pnl_usd": float(pnl),
        "risk_proxy_usd": float(risk),
        "events": events,
        "eq": eq,
    }, "OK"


def admit(cands, k):
    selected, active = [], []
    for tr in cands:
        en = pd.Timestamp(tr["entry"])
        active = [x for x in active if pd.Timestamp(x["exit"]) >= en]
        if len(active) >= k:
            continue
        selected.append(tr)
        active.append(tr)
    return selected


def curve(selected, k, dates):
    if not selected:
        return pd.DataFrame()
    alloc = CAPITAL / k
    starts, exits, paths = {}, {}, {}
    for i, tr in enumerate(selected):
        key = f"v{i:04d}"
        en, ex = pd.Timestamp(tr["entry"]), pd.Timestamp(tr["exit"])
        starts.setdefault(en, []).append(key)
        exits.setdefault(ex, []).append(key)
        paths[key] = (
            pd.DataFrame(tr["eq"], columns=["date", "raw_nav"])
            .assign(date=lambda z: pd.to_datetime(z.date))
            .drop_duplicates("date")
            .set_index("date")
        )
        paths[key].attrs["tr"] = tr
    cash = CAPITAL
    active, done, rows = {}, set(), []
    for dt0 in dates:
        dt = pd.Timestamp(dt0)
        for key in exits.get(dt, []):
            if key not in active:
                continue
            p = paths[key]
            raw = float(p.loc[dt, "raw_nav"]) if dt in p.index else float(p.iloc[-1].raw_nav)
            cash += alloc * raw / CAPITAL
            done.add(key)
            del active[key]
        for key in starts.get(dt, []):
            if key in done or key in active:
                continue
            cash -= alloc
            active[key] = True
        nav = cash
        for key in active:
            p = paths[key]
            hist = p.loc[p.index <= dt]
            if not hist.empty:
                nav += alloc * float(hist.iloc[-1].raw_nav) / CAPITAL
        rows.append({"date": dt, "nav": nav, "active_layers": len(active)})
    e = pd.DataFrame(rows)
    e["peak"] = e.nav.cummax()
    e["dd"] = e.nav / e.peak - 1
    return e


def summarize(sel, e, label):
    if not sel or e.empty:
        return {"mode": label, "trades": 0}
    first, last = pd.Timestamp(e.date.iloc[0]), pd.Timestamp(e.date.iloc[-1])
    yrs = max((last - first).days / 365.25, 1 / 365.25)
    return {
        "mode": label,
        "trades": len(sel),
        "win_rate": float(np.mean([x["pnl_usd"] > 0 for x in sel])),
        "avg_trade_usd": float(np.mean([x["pnl_usd"] for x in sel])),
        "cagr": float((e.nav.iloc[-1] / CAPITAL) ** (1 / yrs) - 1),
        "maxdd": float(e.dd.min()),
        "final_nav": float(e.nav.iloc[-1]),
        "n_open_counts": pd.Series([x["n_open"] for x in sel]).value_counts().to_dict(),
        "wave_events": int(sum(1 for x in sel for e in x["events"] if e["kind"] == "WAVE1_MIGRATE")),
        "harvest_events": int(sum(1 for x in sel for e in x["events"] if e["kind"] == "HARVEST50_ARM")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    od = Path(a.data_dir) / "QQQ_options.parquet"
    ud = Path(a.data_dir) / "QQQ_underlying.parquet"
    u = load_underlying(ud)
    con = duckdb.connect()
    rejects = {}
    credit = 0.0
    seeded = False
    loop, static = [], []
    for _, row in u.iterrows():
        if not bool(row.signal):
            continue
        legs = select_entry(con, od, row.date, float(row.close))
        if legs is None:
            rejects["NO_ENTRY_LEGS"] = rejects.get("NO_ENTRY_LEGS", 0) + 1
            continue
        st, ss = trade(con, od, u, row, legs, BASE_N)
        if st is None:
            rejects[f"STATIC:{ss}"] = rejects.get(f"STATIC:{ss}", 0) + 1
            continue
        static.append(st)
        desired, reason = BASE_N, "BASE_N"
        if not seeded:
            desired, reason = SEED_N, "SEED_N_PLUS_50"
        elif credit > 0:
            desired, reason = RECYCLE_N, "CREDIT_TRY_N_PLUS_20"
        tr, status = trade(con, od, u, row, legs, desired)
        if tr is None:
            rejects[f"{reason}:{status}"] = rejects.get(f"{reason}:{status}", 0) + 1
            tr, status = st, "FALLBACK_N2"
            reason = f"{reason}_FALLBACK_N2"
            if reason.startswith("SEED") and status:
                pass
        else:
            if desired == SEED_N:
                seeded = True
        if tr is st and desired != BASE_N:
            tr = dict(st)
        tr["ratio_reason"] = reason
        tr["credit_before"] = float(credit)
        credit = max(0.0, credit + float(tr["pnl_usd"]))
        tr["credit_after"] = float(credit)
        loop.append(tr)

    sl = admit(static, STACK_K)
    ll = admit(loop, STACK_K)
    es = curve(sl, STACK_K, list(u.date))
    el = curve(ll, STACK_K, list(u.date))
    rs = summarize(sl, es, "STATIC_N2_HALF_STACK")
    rl = summarize(ll, el, "ORIGINAL_SENTENCE_LOOP")
    if not es.empty:
        es.to_csv(out / "equity_static.csv", index=False)
    if not el.empty:
        el.to_csv(out / "equity_loop.csv", index=False)
    pd.DataFrame(
        [
            {
                "entry": str(x["entry"].date()),
                "exit": str(x["exit"].date()),
                "n_open": x["n_open"],
                "n_close": x["n_close"],
                "pnl_usd": x["pnl_usd"],
                "ratio_reason": x.get("ratio_reason"),
                "credit_before": x.get("credit_before"),
                "credit_after": x.get("credit_after"),
                "events": json.dumps(x["events"]),
            }
            for x in ll
        ]
    ).to_csv(out / "loop_ledger.csv", index=False)
    report = {
        "research_id": "QQQ_ORIGINAL_SENTENCE_LOOP_V1",
        "live_signal": False,
        "status": "REAL_QQQ_CHAIN_USER_SENTENCE_REPLAY",
        "user_sentences": [
            "QQQ升很多 → SHORT CALL近一點, SHORT PUT更OTM, LONG PUT同時在",
            "超過某波值才因應買賣; T觸發 T+1執行",
            "跨日期半堆疊 / 儲飛尾",
            "臨近SHORT CALL後一日下跌 → 先鎖至少一半再變陣",
            "N+50對1張; 已實現正收益才准下一輪N+20; 2% gate不過則REJECT",
        ],
        "frozen": {
            "base_n": BASE_N,
            "seed_n": SEED_N,
            "recycle_n": RECYCLE_N,
            "stack_k": STACK_K,
            "wave": "ATR20 x 1, SC 20Δ→30Δ, SP 10Δ→5Δ, LP retained",
            "harvest": "approach 0.98*K_sc then next-day down → flatten half short+wing if recovered",
            "risk_gate": "2% NAV defined-loss proxy",
            "black_scholes": False,
            "interpolation": False,
        },
        "data": {
            "options_sha256": sha256_file(od),
            "underlying_sha256": sha256_file(ud),
            "range": [str(u.date.min().date()), str(u.date.max().date())],
            "signals": int(u.signal.fillna(False).sum()),
        },
        "results": {"static_half_stack": rs, "original_sentence_loop": rl, "final_credit": credit, "seed_activated": seeded},
        "rejections": rejects,
    }
    (out / "qqq_original_sentence_loop_v1_result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
