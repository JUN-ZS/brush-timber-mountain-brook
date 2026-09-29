#!/usr/bin/env python3
"""QQQ N-10 Seed + Opportunity Rights Bank V15 — research only, not a live signal.

Frozen:
  ΔR_N = Risk(N) - Risk(2)
  N_t = max {N in 2..20 : ΔR_N <= h*Bank and Risk(N) <= 2% gate + Bank}
  Bank_{t+1} = max(0, Bank_t + α P+ - β |P-|)
  α=1, β=1, h=1. No search. No look-ahead.
  Mode B: Bank_0 = ΔR_10 of first priced day (prepaid N=10 licence, not free).
  Mode C: Bank_0 = 0.5 * ΔR_10.
  互追反: after seed, does Bank reproduce N>10 and N<10.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qqq_profit_recycle_loop_v6 import (
    ensure_data,
    load_underlying,
    chain,
    pick,
    quotes,
    q_at,
    ex,
    mid,
    sha256_file,
)

CAPITAL = 100000.0
CAPITAL_USD = 64102.5641025641
RISK_PCT = 2.0
GATE_USD = CAPITAL_USD * (RISK_PCT / 100.0)
BASE_N = 2
SEED_N = 10
N_MAX = 20
ALPHA = 1.0
BETA = 1.0
HAIRCUT = 1.0
COOLDOWN_DAYS = 10
HOLD_MAX = 30


def max_loss_proxy(legs, n, spot, qa, qs, qw):
    atm_k = float(legs["atm"]["k"])
    short_k = float(legs["short"]["k"])
    wing_k = float(legs["wing"]["k"])
    grid = np.linspace(max(1.0, spot * 0.2), max(spot * 2.5, wing_k * 1.25), 1200)
    initial = (float(qa["ask"]) - n * float(qs["bid"]) + n * float(qw["ask"])) * 100
    payoff = (
        np.maximum(grid - atm_k, 0)
        - n * np.maximum(grid - short_k, 0)
        + n * np.maximum(grid - wing_k, 0)
    ) * 100
    return max(0.0, -float(np.min(payoff - initial)))


def select_legs(con, opt_path, dt):
    r = chain(con, opt_path, dt)
    if r.empty:
        return None
    exd = (
        r.groupby("expiration", as_index=False)
        .agg(dte=("dte", "first"), mv=("volume", "max"))
        .sort_values(["dte", "mv"], ascending=[True, False])
        .iloc[0]["expiration"]
    )
    g = r[r.expiration == pd.Timestamp(exd)]
    c = g[g.type == "CALL"]
    atm = pick(c, 0.50)
    if atm is None:
        return None
    sc = pick(c, 0.20, gt=atm.strike)
    if sc is None:
        return None
    wing = pick(c, 0.08, gt=sc.strike)
    if wing is None:
        return None
    return {
        "expiry": pd.Timestamp(exd),
        "atm": {"id": str(atm.contract_id), "k": float(atm.strike)},
        "short": {"id": str(sc.contract_id), "k": float(sc.strike)},
        "wing": {"id": str(wing.contract_id), "k": float(wing.strike)},
    }


def risk_curve(legs, spot, qa, qs, qw):
    out = {}
    for n in range(BASE_N, N_MAX + 1):
        out[n] = float(max_loss_proxy(legs, n, spot, qa, qs, qw))
    r2 = out[BASE_N]
    delta = {n: max(0.0, out[n] - r2) for n in out}
    return out, delta


def choose_n(risk, delta, bank):
    usable = HAIRCUT * max(0.0, float(bank))
    allowed = GATE_USD + max(0.0, float(bank))
    chosen = BASE_N
    for n in range(BASE_N, N_MAX + 1):
        if delta[n] <= usable + 1e-9 and risk[n] <= allowed + 1e-9:
            chosen = n
    return chosen


def run_trade(con, opt_path, u, row, legs, n, bank):
    entry = pd.Timestamp(row.date)
    end = min(entry + pd.Timedelta(days=HOLD_MAX), pd.Timestamp(legs["expiry"]))
    d = u[(u.date >= entry) & (u.date <= end)].copy().reset_index(drop=True)
    if d.empty:
        return None, "NO_WINDOW"
    ids = [legs["atm"]["id"], legs["short"]["id"], legs["wing"]["id"]]
    q = quotes(con, opt_path, ids, entry, end)
    qa = q_at(q, entry, ids[0])
    qs = q_at(q, entry, ids[1])
    qw = q_at(q, entry, ids[2])
    if any(v is None for v in (qa, qs, qw)):
        return None, "NO_ENTRY_QUOTES"
    risk = max_loss_proxy(legs, n, float(row.close), qa, qs, qw)
    allowed = GATE_USD + max(0.0, float(bank))
    if risk > allowed:
        return None, "RISK_GATE"
    entry_cf = (ex(qa, "BUY") - n * ex(qs, "SELL") + n * ex(qw, "BUY")) * 100.0
    if pd.isna(entry_cf):
        return None, "NO_ENTRY_QUOTES"
    cash = -float(entry_cf)
    eq = []
    for _, r in d.iterrows():
        dt = pd.Timestamp(r.date)
        ma, ms, mw = mid(q_at(q, dt, ids[0])), mid(q_at(q, dt, ids[1])), mid(q_at(q, dt, ids[2]))
        if not any(pd.isna(v) for v in (ma, ms, mw)):
            eq.append((dt, CAPITAL + cash + ma * 100 - n * ms * 100 + n * mw * 100))
    exit_dt = pd.Timestamp(d.iloc[-1].date)
    vals = [
        ex(q_at(q, exit_dt, ids[0]), "SELL"),
        ex(q_at(q, exit_dt, ids[1]), "BUY"),
        ex(q_at(q, exit_dt, ids[2]), "SELL"),
    ]
    if any(pd.isna(v) for v in vals):
        return None, "NO_EXIT_QUOTES"
    exit_cf = (vals[0] - n * vals[1] + n * vals[2]) * 100.0
    pnl = cash + float(exit_cf)
    eq.append((exit_dt, CAPITAL + pnl))
    return {
        "entry": entry,
        "exit": exit_dt,
        "n": int(n),
        "pnl_usd": float(pnl),
        "risk_proxy_usd": float(risk),
        "eq": eq,
    }, "OK"


def seq(ts):
    if not ts:
        return pd.DataFrame()
    nav = CAPITAL
    rows = []
    for tr in sorted(ts, key=lambda x: pd.Timestamp(x["entry"])):
        for dt, raw in tr["eq"]:
            rows.append((pd.Timestamp(dt), nav * float(raw) / CAPITAL))
        nav *= 1 + tr["pnl_usd"] / CAPITAL
    e = pd.DataFrame(rows, columns=["date", "nav"]).groupby("date", as_index=False).nav.last().sort_values("date")
    e["peak"] = e.nav.cummax()
    e["dd"] = e.nav / e.peak - 1
    return e


def summ(ts, e, label):
    if e.empty or not ts:
        return {"mode": label, "trades": 0}
    yrs = max((pd.Timestamp(e.date.iloc[-1]) - pd.Timestamp(e.date.iloc[0])).days / 365.25, 1 / 365.25)
    ns = [int(x["n"]) for x in ts]
    return {
        "mode": label,
        "trades": len(ts),
        "win_rate": float(np.mean([x["pnl_usd"] > 0 for x in ts])),
        "avg_trade_usd": float(np.mean([x["pnl_usd"] for x in ts])),
        "total_return_pct": float(100 * (e.nav.iloc[-1] / CAPITAL - 1)),
        "cagr": float((e.nav.iloc[-1] / CAPITAL) ** (1 / yrs) - 1),
        "maxdd": float(e.dd.min()),
        "n_min": int(min(ns)),
        "n_max": int(max(ns)),
        "n_mean": float(np.mean(ns)),
        "n_counts": pd.Series(ns).value_counts().sort_index().to_dict(),
        "n_gt_seed": int(sum(n > SEED_N for n in ns)),
        "n_eq_seed": int(sum(n == SEED_N for n in ns)),
        "n_lt_seed": int(sum(n < SEED_N for n in ns)),
        "up_steps": int(sum(ns[i] > ns[i - 1] for i in range(1, len(ns)))),
        "down_steps": int(sum(ns[i] < ns[i - 1] for i in range(1, len(ns)))),
    }


def update_bank(bank, pnl):
    if pnl >= 0:
        bank = bank + ALPHA * float(pnl)
    else:
        bank = bank - BETA * abs(float(pnl))
    return max(0.0, float(bank))


def replay(con, op, u, seed_frac, label):
    bank = 0.0
    seeded = False
    seed_cost = None
    seed_date = None
    next_allowed = None
    trades = []
    rows = []
    rejects = {}
    static = []
    for _, row in u.iterrows():
        dt = pd.Timestamp(row.date)
        if next_allowed is not None and dt <= next_allowed:
            continue
        if not bool(row.signal):
            continue
        legs = select_legs(con, op, dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"] = rejects.get("NO_ENTRY_LEGS", 0) + 1
            continue
        ids = [legs["atm"]["id"], legs["short"]["id"], legs["wing"]["id"]]
        qd = quotes(con, op, ids, dt, dt)
        qa = q_at(qd, dt, ids[0])
        qs = q_at(qd, dt, ids[1])
        qw = q_at(qd, dt, ids[2])
        if any(v is None for v in (qa, qs, qw)):
            rejects["NO_ENTRY_QUOTES"] = rejects.get("NO_ENTRY_QUOTES", 0) + 1
            continue
        risk, delta = risk_curve(legs, float(row.close), qa, qs, qw)
        st, ss = run_trade(con, op, u, row, legs, BASE_N, 0.0)
        if st is None:
            rejects["STATIC_" + ss] = rejects.get("STATIC_" + ss, 0) + 1
            continue
        static.append(st)
        if not seeded:
            seed_cost = float(delta[SEED_N])
            bank = seed_frac * seed_cost
            seeded = True
            seed_date = str(dt.date())
        target = choose_n(risk, delta, bank)
        tr, status = run_trade(con, op, u, row, legs, target, bank)
        if tr is None:
            rejects[f"N{target}:{status}"] = rejects.get(f"N{target}:{status}", 0) + 1
            next_allowed = st["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)
            continue
        side = "SEED"
        if len(trades) > 0:
            prev = trades[-1]["n"]
            if target > prev:
                side = "EXPAND"
            elif target < prev:
                side = "CONTRACT"
            else:
                side = "FLAT"
        rec = {
            "entry": str(dt.date()),
            "exit": str(tr["exit"].date()),
            "n": int(target),
            "side": side,
            "bank_before": float(bank),
            "usable_bank": HAIRCUT * float(bank),
            "delta_r_n": float(delta[target]),
            "delta_r_10": float(delta[SEED_N]),
            "risk_proxy_usd": float(tr["risk_proxy_usd"]),
            "allowed_risk_usd": GATE_USD + float(bank),
            "pnl_usd": float(tr["pnl_usd"]),
        }
        bank = update_bank(bank, tr["pnl_usd"])
        rec["bank_after"] = float(bank)
        tr["n"] = int(target)
        trades.append(tr)
        rows.append(rec)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)
    return {
        "label": label,
        "trades": trades,
        "static": static,
        "rows": rows,
        "rejects": rejects,
        "final_bank": float(bank),
        "seeded": seeded,
        "seed_date": seed_date,
        "seed_cost_usd": seed_cost,
        "seed_frac": seed_frac,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    op, up = ensure_data(Path(a.data_dir))
    u = load_underlying(up).copy().reset_index(drop=True)
    con = duckdb.connect()

    modes = [
        replay(con, op, u, 1.0, "B_SEED_FULL_DR10"),
        replay(con, op, u, 0.5, "C_SEED_HALF_DR10"),
    ]

    summaries = []
    all_rows = []
    for m in modes:
        e = seq(m["trades"])
        s = summ(m["trades"], e, m["label"])
        s["final_bank"] = m["final_bank"]
        s["seeded"] = m["seeded"]
        s["seed_date"] = m["seed_date"]
        s["seed_cost_usd"] = m["seed_cost_usd"]
        s["first_n"] = int(m["trades"][0]["n"]) if m["trades"] else None
        s["path_head"] = [int(x["n"]) for x in m["trades"][:12]]
        summaries.append(s)
        if not e.empty:
            e.to_csv(out / f"equity_{m['label'].lower()}.csv", index=False)
        for r in m["rows"]:
            r2 = dict(r)
            r2["mode"] = m["label"]
            all_rows.append(r2)
        es = seq(m["static"])
        ss = summ(m["static"], es, m["label"] + "_STATIC_N2")
        summaries.append(ss)

    pd.DataFrame(all_rows).to_csv(out / "n10_rights_ledger.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)

    chase = {}
    for m in modes:
        ns = [int(x["n"]) for x in m["trades"]]
        chase[m["label"]] = {
            "reproduced_larger_than_10": bool(any(n > SEED_N for n in ns)),
            "reproduced_smaller_than_10": bool(any(n < SEED_N for n in ns)),
            "first_n": ns[0] if ns else None,
            "max_n": max(ns) if ns else None,
            "min_n": min(ns) if ns else None,
            "n_path_head": ns[:20],
            "seed_date": m["seed_date"],
            "seed_cost_usd": m["seed_cost_usd"],
            "final_bank": m["final_bank"],
            "rejects": m["rejects"],
        }

    report = {
        "research_id": "QQQ_N10_RIGHTS_BANK_V15",
        "live_signal": False,
        "status": "REAL_QQQ_CHAIN_N10_SEED_RIGHTS_BANK_CHASE",
        "user_question": [
            "先買一張 N=10 的權之後，Bank 能否自己繁殖出更大的 N？",
            "同時能否自己繁殖出更小的 N？互追反",
        ],
        "frozen": {
            "alpha": ALPHA,
            "beta": BETA,
            "haircut": HAIRCUT,
            "seed_n": SEED_N,
            "base_n": BASE_N,
            "n_max": N_MAX,
            "gate_usd": GATE_USD,
            "bank_update": "max(0, Bank + αP+ - β|P-|)",
            "n_rule": "max N with ΔR_N <= h Bank and Risk(N) <= 2% + Bank",
            "mode_b": "Bank_0 = ΔR_10 of first priced day",
            "mode_c": "Bank_0 = 0.5 ΔR_10",
            "black_scholes": False,
            "interpolation": False,
            "parameter_search": False,
        },
        "data": {
            "options_sha256": sha256_file(op),
            "underlying_sha256": sha256_file(up),
            "range": [str(u.date.min().date()), str(u.date.max().date())],
            "signals": int(u.signal.fillna(False).sum()),
        },
        "results": summaries,
        "chase": chase,
    }
    (out / "qqq_n10_rights_bank_v15_result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
