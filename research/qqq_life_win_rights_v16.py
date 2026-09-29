#!/usr/bin/env python3
"""QQQ Life-Win Rights V16 — research only, not a live signal.

User sentence frozen:
  「一次 RISK WIN 吃一世」

Checkable contract (no search, no look-ahead):
  Seed same as V15 Mode B: first priced day posts Bank_0 = ΔR_10. Not free.
  Bank_{t+1} = max(floor, Bank_t + α P+ − β |P−|), α=β=h=1.
  N_t = max {N in 2..20 : ΔR_N <= h·Bank and Risk(N) <= 2% gate + Bank}
  After grant, N_t = max(N_t, n_lock). Lock is not a silent scale-down:
  if locked N fails the gate, record LOCK_GATE and skip the signal.

  LIFE_WIN definitions (two frozen modes, not a grid search):
    LIFE_DR10:      P_t >= ΔR_10 of that entry day.
                    n_lock = 10. floor = max(Bank_after, ΔR_10).
    LIFE_OWN_RISK:  P_t >= Risk_proxy of that same vintage.
                    n_lock = N of that vintage. floor = Bank_after.

  Grant fires on the first LIFE_WIN, applies from the NEXT signal only.
  REVOKE iff a later vintage has P < 0 and |P| >= floor.
  After revoke: granted=False, floor=0, n_lock=2.

Question this run answers:
  Did a LIFE_WIN ever occur on this real chain + this package?
  After grant, did the right last to sample end (一世), or did one LOSS revoke it?
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
    }


def update_bank(bank, pnl, floor):
    if pnl >= 0:
        bank = bank + ALPHA * float(pnl)
    else:
        bank = bank - BETA * abs(float(pnl))
    return max(float(floor), float(bank))


def is_life_win(mode, pnl, delta_r10, risk_proxy):
    if pnl <= 0:
        return False
    if mode == "LIFE_DR10":
        return float(pnl) >= float(delta_r10) - 1e-9
    if mode == "LIFE_OWN_RISK":
        return float(pnl) >= float(risk_proxy) - 1e-9
    return False


def replay(con, op, u, life_mode, label):
    bank = 0.0
    floor = 0.0
    n_lock = BASE_N
    granted = False
    revoked = False
    seeded = False
    seed_cost = None
    seed_date = None
    grant_event = None
    revoke_event = None
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
            bank = 1.0 * seed_cost
            seeded = True
            seed_date = str(dt.date())
        raw_n = choose_n(risk, delta, bank)
        target = raw_n
        locked = False
        if granted and not revoked:
            if n_lock > target:
                target = int(n_lock)
                locked = True
        tr, status = run_trade(con, op, u, row, legs, target, bank)
        if tr is None:
            tag = f"N{target}:{status}"
            if locked:
                tag = f"LOCK_GATE_N{target}:{status}"
            rejects[tag] = rejects.get(tag, 0) + 1
            next_allowed = st["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)
            continue
        event = "SEED" if len(trades) == 0 else "HOLD"
        if len(trades) > 0:
            prev = trades[-1]["n"]
            if target > prev:
                event = "EXPAND"
            elif target < prev:
                event = "CONTRACT"
        rec = {
            "entry": str(dt.date()),
            "exit": str(tr["exit"].date()),
            "n": int(target),
            "raw_n": int(raw_n),
            "locked": bool(locked),
            "granted_before": bool(granted),
            "event": event,
            "bank_before": float(bank),
            "floor_before": float(floor),
            "delta_r_n": float(delta[target]),
            "delta_r_10": float(delta[SEED_N]),
            "risk_proxy_usd": float(tr["risk_proxy_usd"]),
            "allowed_risk_usd": GATE_USD + float(bank),
            "pnl_usd": float(tr["pnl_usd"]),
            "life_win_flag": False,
            "revoke_flag": False,
        }
        life = is_life_win(life_mode, tr["pnl_usd"], delta[SEED_N], tr["risk_proxy_usd"])
        rec["life_win_flag"] = bool(life)

        if (not granted) and life_mode != "CONTROL" and life:
            granted = True
            if life_mode == "LIFE_DR10":
                n_lock = SEED_N
                floor = max(float(bank) + float(tr["pnl_usd"]), float(delta[SEED_N]))
            else:
                n_lock = int(target)
                floor = max(0.0, float(bank) + float(tr["pnl_usd"]))
            rec["event"] = "LIFE_WIN"
            grant_event = {
                "entry": rec["entry"],
                "exit": rec["exit"],
                "n": int(target),
                "pnl_usd": float(tr["pnl_usd"]),
                "risk_proxy_usd": float(tr["risk_proxy_usd"]),
                "delta_r_10": float(delta[SEED_N]),
                "floor": float(floor),
                "n_lock": int(n_lock),
            }

        prev_granted = granted
        bank = update_bank(bank, tr["pnl_usd"], floor if granted else 0.0)

        if prev_granted and (not revoked) and tr["pnl_usd"] < 0 and abs(tr["pnl_usd"]) >= floor - 1e-9:
            revoked = True
            granted = False
            floor = 0.0
            n_lock = BASE_N
            rec["revoke_flag"] = True
            rec["event"] = "REVOKE"
            bank = max(0.0, bank)
            revoke_event = {
                "entry": rec["entry"],
                "exit": rec["exit"],
                "n": int(target),
                "pnl_usd": float(tr["pnl_usd"]),
                "risk_proxy_usd": float(tr["risk_proxy_usd"]),
            }

        rec["bank_after"] = float(bank)
        rec["floor_after"] = float(floor)
        rec["granted_after"] = bool(granted)
        rec["n_lock"] = int(n_lock)
        tr["n"] = int(target)
        trades.append(tr)
        rows.append(rec)
        next_allowed = tr["exit"] + pd.Timedelta(days=COOLDOWN_DAYS)

    post = []
    if grant_event is not None:
        gdt = pd.Timestamp(grant_event["exit"])
        post = [r for r in rows if pd.Timestamp(r["exit"]) > gdt]
    return {
        "label": label,
        "life_mode": life_mode,
        "trades": trades,
        "static": static,
        "rows": rows,
        "rejects": rejects,
        "final_bank": float(bank),
        "seeded": seeded,
        "seed_date": seed_date,
        "seed_cost_usd": seed_cost,
        "granted": grant_event is not None,
        "grant_held_to_end": bool(grant_event is not None and not revoked),
        "grant_event": grant_event,
        "revoked": revoked,
        "revoke_event": revoke_event,
        "trades_after_grant": len(post),
        "n_path_after_grant": [int(r["n"]) for r in post],
        "life_win_count": int(sum(1 for r in rows if r["life_win_flag"])),
    }


def slice_summ(rows, trades, after_exit, label):
    if after_exit is None:
        return {"mode": label, "trades": 0}
    keep_t = [t for t in trades if pd.Timestamp(t["exit"]) > pd.Timestamp(after_exit)]
    e = seq(keep_t)
    s = summ(keep_t, e, label)
    return s


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
        replay(con, op, u, "CONTROL", "CONTROL_V15B"),
        replay(con, op, u, "LIFE_DR10", "LIFE_DR10"),
        replay(con, op, u, "LIFE_OWN_RISK", "LIFE_OWN_RISK"),
    ]

    summaries = []
    all_rows = []
    life_report = {}
    for m in modes:
        e = seq(m["trades"])
        s = summ(m["trades"], e, m["label"])
        s["final_bank"] = m["final_bank"]
        s["seeded"] = m["seeded"]
        s["seed_date"] = m["seed_date"]
        s["seed_cost_usd"] = m["seed_cost_usd"]
        s["granted"] = m["granted"]
        s["grant_held_to_end"] = m["grant_held_to_end"]
        s["revoked"] = m["revoked"]
        s["life_win_count"] = m["life_win_count"]
        s["trades_after_grant"] = m["trades_after_grant"]
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
        gexit = m["grant_event"]["exit"] if m["grant_event"] else None
        post = slice_summ(m["rows"], m["trades"], gexit, m["label"] + "_POST_GRANT")
        summaries.append(post)
        life_report[m["label"]] = {
            "granted": m["granted"],
            "grant_held_to_end": m["grant_held_to_end"],
            "revoked": m["revoked"],
            "grant_event": m["grant_event"],
            "revoke_event": m["revoke_event"],
            "life_win_count": m["life_win_count"],
            "trades_after_grant": m["trades_after_grant"],
            "n_path_after_grant": m["n_path_after_grant"][:20],
            "n_path_head": [int(x["n"]) for x in m["trades"][:20]],
            "final_bank": m["final_bank"],
            "seed_date": m["seed_date"],
            "seed_cost_usd": m["seed_cost_usd"],
            "rejects": m["rejects"],
        }

    pd.DataFrame(all_rows).to_csv(out / "life_win_ledger.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)

    report = {
        "research_id": "QQQ_LIFE_WIN_RIGHTS_V16",
        "live_signal": False,
        "status": "REAL_QQQ_CHAIN_ONE_RISK_WIN_FEEDS_A_LIFETIME",
        "user_sentence": "一次 RISK WIN 吃一世",
        "user_question": [
            "一次 RISK WIN 會否在真實 QQQ chain 上出現？",
            "出現之後，權是否養到樣本末端（一世），抑或被一次 LOSS 撤權？",
        ],
        "frozen": {
            "alpha": ALPHA,
            "beta": BETA,
            "haircut": HAIRCUT,
            "seed_n": SEED_N,
            "base_n": BASE_N,
            "n_max": N_MAX,
            "gate_usd": GATE_USD,
            "seed": "Bank_0 = ΔR_10 of first priced day (same as V15 Mode B)",
            "life_dr10": "LIFE_WIN iff P >= ΔR_10; n_lock=10; floor=max(Bank_after, ΔR_10)",
            "life_own_risk": "LIFE_WIN iff P >= own Risk_proxy; n_lock=N; floor=Bank_after",
            "revoke": "P < 0 and |P| >= floor",
            "lock_gate": "locked N that fails 2%+Bank is REJECT, not scaled down",
            "grant_timing": "applies from next signal only",
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
        "life": life_report,
    }
    (out / "qqq_life_win_rights_v16_result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
