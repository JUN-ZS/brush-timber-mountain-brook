#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd

CAPITAL = 100000.0
CORE = 0.42
BUDGET = 0.02
DTE_MIN = 18
DTE_MAX = 35
ROLL_DTE = 7
START = pd.Timestamp("2018-03-01")
END = pd.Timestamp("2025-12-16")
SHOCK_DD = -0.08
SHOCK_R5 = -0.04


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load_underlying(path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path)
    x.columns = [c.lower() for c in x.columns]
    if "date" not in x.columns:
        raise ValueError("underlying missing date")
    price_col = "adjclose" if "adjclose" in x.columns else (
        "adj_close" if "adj_close" in x.columns else "close"
    )
    x["date"] = pd.to_datetime(x["date"]).dt.tz_localize(None).dt.normalize()
    x = (
        x[(x.date >= START) & (x.date <= END)]
        .sort_values("date")
        .drop_duplicates("date")
        .reset_index(drop=True)
    )
    x["price"] = x[price_col].astype(float)
    x["peak252"] = x.price.rolling(252, min_periods=20).max()
    x["dd252"] = x.price / x.peak252 - 1
    x["r5"] = x.price.pct_change(5)
    x["shock"] = (x.dd252 <= SHOCK_DD) | (x.r5 <= SHOCK_R5)
    return x


def choose_contracts(con, opt_path, dates):
    q = con.execute(
        """
      SELECT CAST(date AS DATE) AS date,
             CAST(expiration AS DATE) AS expiration,
             CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(strike AS DOUBLE) AS strike,
             CAST(bid AS DOUBLE) AS bid,
             CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark,
             CAST(delta AS DOUBLE) AS delta,
             COALESCE(CAST(volume AS DOUBLE),0) AS volume,
             DATEDIFF('day',CAST(date AS DATE),CAST(expiration AS DATE)) AS dte
      FROM read_parquet(?)
      WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
        AND UPPER(type)='PUT'
        AND delta IS NOT NULL
        AND bid IS NOT NULL AND ask IS NOT NULL
        AND ask>=bid AND bid>=0
        AND CAST(expiration AS DATE) BETWEEN
            CAST(date AS DATE)+INTERVAL 18 DAY AND
            CAST(date AS DATE)+INTERVAL 35 DAY
    """,
        [str(opt_path), [pd.Timestamp(d).date() for d in dates]],
    ).df()
    if q.empty:
        return {}
    q["date"] = pd.to_datetime(q["date"])
    q["expiration"] = pd.to_datetime(q["expiration"])
    out = {}
    for dt, g in q.sort_values(["date", "dte", "volume"], ascending=[True, True, False]).groupby(
        "date", sort=True
    ):
        expiry = g.iloc[0].expiration
        g = g[g.expiration == expiry]
        l25 = g.loc[(g.delta + 0.25).abs().idxmin()]
        l10 = g.loc[(g.delta + 0.10).abs().idxmin()]
        if float(l10.strike) >= float(l25.strike):
            continue
        out[pd.Timestamp(dt)] = {
            "expiry": pd.Timestamp(expiry),
            "long_id": str(l25.contract_id),
            "long_k": float(l25.strike),
            "short_id": str(l10.contract_id),
            "short_k": float(l10.strike),
        }
    return out


def load_quotes(con, opt_path, ids):
    q = con.execute(
        """
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
             CAST(mark AS DOUBLE) AS mark
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND CAST(date AS DATE) BETWEEN ? AND ?
    """,
        [str(opt_path), list(ids), START.date(), END.date()],
    ).df()
    q["date"] = pd.to_datetime(q["date"])
    q["contract_id"] = q["contract_id"].astype(str)
    return q.set_index(["date", "contract_id"]).sort_index()


def qget(q, dt, cid):
    try:
        r = q.loc[(pd.Timestamp(dt), str(cid))]
    except KeyError:
        return None
    if pd.isna(r.bid) or pd.isna(r.ask):
        return None
    mid = (float(r.bid) + float(r.ask)) / 2
    return {
        "bid": float(r.bid),
        "ask": float(r.ask),
        "mark": float(r.mark) if pd.notna(r.mark) else mid,
        "mid": mid,
    }


def stats(navs, dates):
    e = pd.DataFrame({"date": dates, "nav": navs})
    e["peak"] = e.nav.cummax()
    e["dd"] = e.nav / e.peak - 1
    years = (e.date.iloc[-1] - e.date.iloc[0]).days / 365.25
    return {
        "cagr": float((e.nav.iloc[-1] / CAPITAL) ** (1 / years) - 1),
        "maxdd": float(e.dd.min()),
        "final_nav": float(e.nav.iloc[-1]),
        "start_nav": float(e.nav.iloc[0]),
    }, e


def run_book(U, sel, q, mode: str):
    shares = int((CAPITAL * CORE) // float(U.iloc[0].price))
    cash = CAPITAL - shares * float(U.iloc[0].price)
    hedge = None
    eq = []
    cycles = []
    for _, row in U.iterrows():
        dt = row.date
        px = float(row.price)
        if hedge is not None:
            ql = qget(q, dt, hedge["long_id"])
            qs = qget(q, dt, hedge["short_id"])
            dte = max((hedge["expiry"] - dt).days, 0)
            if ql and qs and dte <= ROLL_DTE:
                exitv = (ql["bid"] - qs["ask"]) * 100 * hedge["n"]
                realized = exitv - hedge["debit_usd"]
                cash += exitv
                cycles.append(
                    {
                        **{k: (str(v.date()) if hasattr(v, "date") else v) for k, v in hedge.items()},
                        "exit_date": str(dt.date()),
                        "exit_value_usd": float(exitv),
                        "realized_pnl_usd": float(realized),
                    }
                )
                hedge = None
        want = mode == "ALWAYS_ON" or (mode == "SHOCK_GATED" and bool(row.shock))
        if hedge is None and want:
            s = sel.get(dt)
            if s:
                ql = qget(q, dt, s["long_id"])
                qs = qget(q, dt, s["short_id"])
                if ql and qs:
                    debit = max(ql["ask"] - qs["bid"], 1e-4)
                    nav_now = cash + shares * px
                    n = int((nav_now * BUDGET) // (debit * 100))
                    if n > 0:
                        debit_usd = debit * 100 * n
                        cash -= debit_usd
                        hedge = {**s, "n": n, "debit_usd": float(debit_usd), "entry_date": str(dt.date())}
        hmark = 0.0
        if hedge is not None:
            ql = qget(q, dt, hedge["long_id"])
            qs = qget(q, dt, hedge["short_id"])
            if ql and qs:
                hmark = (ql["mid"] - qs["mid"]) * 100 * hedge["n"]
        eq.append(cash + shares * px + hmark)
    r, e = stats(eq, list(U.date))
    r["hedge_cycles"] = len(cycles)
    r["realized_hedge_pnl"] = float(sum(x["realized_pnl_usd"] for x in cycles))
    r["shock_days"] = int(U.shock.fillna(False).sum())
    return e, r, cycles


def run_core(U):
    shares = int((CAPITAL * CORE) // float(U.iloc[0].price))
    cash = CAPITAL - shares * float(U.iloc[0].price)
    navs = [cash + shares * float(p) for p in U.price]
    r, e = stats(navs, list(U.date))
    r["hedge_cycles"] = 0
    r["realized_hedge_pnl"] = 0.0
    r["shock_days"] = int(U.shock.fillna(False).sum())
    return e, r, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    od = Path(a.data_dir) / "QQQ_options.parquet"
    ud = Path(a.data_dir) / "QQQ_underlying.parquet"
    U = load_underlying(ud)
    con = duckdb.connect()
    sel = choose_contracts(con, od, list(U.date))
    ids = {z for s in sel.values() for z in (s["long_id"], s["short_id"])}
    q = load_quotes(con, od, ids)

    books = {}
    e_core, r_core, _ = run_core(U)
    books["CORE42"] = r_core
    e_core.to_csv(out / "qqq_hybrid_downside_convexity_v1_core_equity.csv", index=False)

    for mode in ("ALWAYS_ON", "SHOCK_GATED"):
        e, r, cycles = run_book(U, sel, q, mode)
        books[mode] = r
        tag = mode.lower()
        e.to_csv(out / f"qqq_hybrid_downside_convexity_v1_{tag}_equity.csv", index=False)
        pd.DataFrame(cycles).to_csv(
            out / f"qqq_hybrid_downside_convexity_v1_{tag}_cycles.csv", index=False
        )

    result = {
        "research_id": "QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1",
        "status": "REAL_QQQ_CHAIN_COMPONENT_TEST",
        "live_signal": False,
        "frozen": {
            "core": CORE,
            "budget": BUDGET,
            "dte_min": DTE_MIN,
            "dte_max": DTE_MAX,
            "roll_dte": ROLL_DTE,
            "long_delta": -0.25,
            "short_delta": -0.10,
            "shock_dd252": SHOCK_DD,
            "shock_r5": SHOCK_R5,
            "entry": "long Ask / short Bid",
            "mark": "Mid",
            "exit": "long Bid / short Ask",
            "interpolation": False,
            "vxx": False,
        },
        "data": {
            "options_sha256": sha256_file(od),
            "underlying_sha256": sha256_file(ud),
            "date_range": [str(U.date.min().date()), str(U.date.max().date())],
            "selected_entry_days": len(sel),
        },
        "prior_always_on_observed": {
            "source_run": 36498315406,
            "cagr": 0.036666823227275325,
            "maxdd": -0.1717206396665717,
            "hedge_cycles": 210,
            "realized_hedge_pnl": -82992.0,
            "grade": "OBSERVED",
        },
        "books": books,
        "pass_note": "10pct is a question for CORE42 vs SHOCK_GATED on this tape; ALWAYS_ON already observed below 10pct.",
    }
    (out / "qqq_hybrid_downside_convexity_v1_result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
