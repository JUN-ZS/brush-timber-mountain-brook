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
    MAX_HOLD_DAYS,
    load_px,
    make_pair,
    pair_mtm,
    pair_value,
    unit_marks,
    prev_trading_date,
    weekly_observation_days,
    atm_iv60_series,
    bounded_percentile,
)


THRESHOLDS = [3.0, 6.0, 8.0]
SCHEDULES = [
    ("A_REL_EQUAL", [1.0, 1.0, 1.0], False),
    ("B_REL_PROGRESSIVE", [1.0, 2.0, 3.0], False),
    ("C_REL_FRONTLOADED", [3.0, 2.0, 1.0], False),
    ("D_EXHAUSTION_PROGRESSIVE", [1.0, 2.0, 3.0], True),
]


def sql(con, s):
    return con.execute(s).df()


def pathq(p):
    return str(p).replace("'", "''")


def build_relative_state(con, qu, su, qpath, spath):
    q = load_px(con, qu, "Q")
    s = load_px(con, su, "S")
    x = (
        q.merge(s, on=["date", "month"], how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )
    days = weekly_observation_days(x)
    st = x.set_index("date")
    state_dates = sorted(pd.to_datetime(x.date).tolist())
    signal_dates = [prev_trading_date(state_dates, d) for d in days]
    signal_dates = [d for d in signal_dates if d is not None]

    qiv = atm_iv60_series(con, qpath, signal_dates)
    siv = atm_iv60_series(con, spath, signal_dates)

    rows = []
    for d in days:
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        r = st.loc[sigd]
        qrv = float(r.Q_rv60) if pd.notna(r.Q_rv60) else np.nan
        srv = float(r.S_rv60) if pd.notna(r.S_rv60) else np.nan
        q_iv = qiv.get(pd.Timestamp(sigd), np.nan)
        s_iv = siv.get(pd.Timestamp(sigd), np.nan)
        q_vrp = q_iv / qrv if np.isfinite(q_iv) and np.isfinite(qrv) and qrv > 0 else np.nan
        s_vrp = s_iv / srv if np.isfinite(s_iv) and np.isfinite(srv) and srv > 0 else np.nan
        # Relative state is built first, then ranked against its own causal history.
        rel = np.log(q_vrp / s_vrp) if np.isfinite(q_vrp) and np.isfinite(s_vrp) and q_vrp > 0 and s_vrp > 0 else np.nan
        rows.append(
            {
                "signal_date": pd.Timestamp(sigd),
                "entry_date": pd.Timestamp(d),
                "q_rv60": qrv,
                "s_rv60": srv,
                "q_iv60": q_iv,
                "s_iv60": s_iv,
                "q_vrp": q_vrp,
                "s_vrp": s_vrp,
                "log_vrp_ratio": rel,
            }
        )

    z = pd.DataFrame(rows).sort_values("entry_date").reset_index(drop=True)
    # Key refinement: rank the RELATIVE state directly.
    z["d_score"] = bounded_percentile(z.log_vrp_ratio)
    z["d_delta"] = z.d_score.diff()
    z["abs_d"] = z.d_score.abs()
    z["abs_d_delta"] = z.abs_d.diff()
    z["abs_d_accel"] = z.abs_d_delta.diff()
    return z


def should_add_layer(events, idx, layer_no, direction, score):
    if layer_no == 1:
        return True
    if idx <= 0:
        return False
    prev = float(events.iloc[idx - 1].d_score)
    if not np.isfinite(prev):
        return False
    # "Exhaustion" = still beyond the next threshold, but divergence is no
    # longer accelerating materially. This is a gate, not an unconditional
    # averaging-down rule.
    current_abs = abs(score)
    prev_abs = abs(prev)
    return current_abs <= prev_abs + 0.50


def build_cycles(con, state, qpath, spath, gated):
    events = state[state.d_score.notna()].reset_index(drop=True)
    cycles = []
    active = None
    blocked = False
    cycle_no = 0

    for idx, row in events.iterrows():
        d = pd.Timestamp(row.entry_date)
        score = float(row.d_score)

        if active is None:
            if blocked:
                if abs(score) <= 2.0:
                    blocked = False
                else:
                    continue
            if score >= THRESHOLDS[0]:
                direction = 1
            elif score <= -THRESHOLDS[0]:
                direction = -1
            else:
                continue
            active = {
                "cycle_no": cycle_no,
                "direction": direction,
                "entry_date": d,
                "entry_score": score,
                "layers": [],
                "next_layer": 0,
                "expiry_limit": d + pd.Timedelta(days=MAX_HOLD_DAYS),
            }
            cycle_no += 1

        target = score * active["direction"]
        while active["next_layer"] < len(THRESHOLDS) and target >= THRESHOLDS[active["next_layer"]]:
            layer_no = active["next_layer"] + 1
            allow = True
            if gated:
                allow = should_add_layer(events, idx, layer_no, active["direction"], score)
            if not allow:
                break
            pair = make_pair(
                con,
                qpath,
                spath,
                d,
                active["direction"],
                f"cycle_{active['cycle_no']:04d}_layer_{layer_no}",
            )
            if pair is None:
                break
            active["layers"].append(
                {
                    "layer": layer_no,
                    "entry_date": d,
                    "entry_score": score,
                    "pair": pair,
                    "threshold": THRESHOLDS[layer_no - 1],
                }
            )
            active["next_layer"] += 1

        if not active["layers"]:
            active = None
            continue

        if target <= -THRESHOLDS[-1]:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "OPPOSITE_BOUNDARY"
            cycles.append(active)

            reverse = {
                "cycle_no": cycle_no,
                "direction": -active["direction"],
                "entry_date": d,
                "entry_score": score,
                "layers": [],
                "next_layer": 0,
                "expiry_limit": d + pd.Timedelta(days=MAX_HOLD_DAYS),
            }
            cycle_no += 1
            pair = make_pair(
                con,
                qpath,
                spath,
                d,
                reverse["direction"],
                f"cycle_{reverse['cycle_no']:04d}_layer_1",
            )
            if pair is None:
                active = None
                blocked = True
                continue
            reverse["layers"].append(
                {
                    "layer": 1,
                    "entry_date": d,
                    "entry_score": score,
                    "pair": pair,
                    "threshold": THRESHOLDS[0],
                }
            )
            reverse["next_layer"] = 1
            active = reverse

        elif d >= active["expiry_limit"]:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "TIME_EXIT"
            cycles.append(active)
            active = None
            blocked = True

    if active is not None:
        active["exit_date"] = pd.Timestamp(events.entry_date.iloc[-1])
        active["exit_score"] = float(events.d_score.iloc[-1])
        active["exit_reason"] = "SAMPLE_END"
        cycles.append(active)
    return cycles


def flatten_cycles(cycles):
    out = []
    for c in cycles:
        for layer in c["layers"]:
            for p in layer["pair"]:
                z = p.copy()
                z["cycle"] = c["cycle_no"]
                z["layer"] = layer["layer"]
                z["exit_date"] = c["exit_date"]
                z["exit_reason"] = c["exit_reason"]
                z["entry_score"] = layer["entry_score"]
                z["layer_threshold"] = layer["threshold"]
                out.append(z)
    return out


def simulate(con, state, qpath, spath, name, weights, gated, valuation_dates):
    cycles = build_cycles(con, state, qpath, spath, gated)
    flat = flatten_cycles(cycles)
    if not flat:
        return {
            "name": name,
            "thresholds": ",".join(map(str, THRESHOLDS)),
            "weights": ",".join(map(str, weights)),
            "gated": gated,
            "cycles": 0,
            "entries": 0,
            "ending_nav": 100000.0,
            "cagr": 0.0,
            "maxdd": 0.0,
            "sharpe": 0.0,
            "integer_feasible_layers": 0,
            "layers_opened": 0,
            "full_ladders": 0,
        }, pd.DataFrame()

    marks = unit_marks(con, qpath, spath, flat)
    mk = {
        (r.contract_id, r.date): (float(r.bid), float(r.ask), float(r.mark))
        for r in marks.itertuples(index=False)
    }

    norm = np.asarray(weights, dtype=float)
    norm = norm / norm.sum()

    events = {}
    for c in cycles:
        events.setdefault(pd.Timestamp(c["exit_date"]), []).append(("CLOSE", c))
        for layer in c["layers"]:
            events.setdefault(pd.Timestamp(layer["entry_date"]), []).append(("OPEN_LAYER", (c, layer)))

    nav = 100000.0
    realized = 0.0
    openpos = []
    rows = []
    cycle_results = []
    integer_feasible = 0

    for d in valuation_dates:
        for action, item in events.get(d, []):
            if action != "CLOSE":
                continue
            c = item
            pnl = 0.0
            ok_all = True
            for p in openpos[:]:
                if p.get("cycle") != c["cycle_no"]:
                    continue
                v, ok = pair_value(p, mk, d, p["qty"])
                if ok:
                    realized += v
                    pnl += v
                    openpos.remove(p)
                else:
                    ok_all = False
            cycle_results.append(
                {
                    "cycle": c["cycle_no"],
                    "entry": c["entry_date"],
                    "exit": c["exit_date"],
                    "entry_score": c["entry_score"],
                    "exit_score": c["exit_score"],
                    "direction": c["direction"],
                    "reason": c["exit_reason"],
                    "layers": len(c["layers"]),
                    "realized_pnl": pnl if ok_all else np.nan,
                }
            )

        for action, item in events.get(d, []):
            if action != "OPEN_LAYER":
                continue
            c, layer = item
            layer_frac = float(norm[layer["layer"] - 1])
            risk_target_per_leg = max(nav, 1.0) * 0.025 * layer_frac
            layer_qty = min(
                risk_target_per_leg / max(float(p["risk"]), 1e-9)
                for p in layer["pair"]
            )
            if not np.isfinite(layer_qty) or layer_qty <= 0:
                continue

            # Diagnostic only: real contracts are indivisible, so report
            # whether the layer could fit with one whole contract inside budget.
            if all(float(p["risk"]) <= risk_target_per_leg for p in layer["pair"]):
                integer_feasible += 1

            for p in layer["pair"]:
                p2 = p.copy()
                p2["qty"] = float(layer_qty)
                p2["layer"] = layer["layer"]
                openpos.append(p2)

        mtm = 0.0
        for p in openpos:
            v, ok = pair_mtm(p, mk, d, p["qty"])
            if ok:
                mtm += v
        nav = 100000.0 + realized + mtm
        rows.append((d, nav))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e.date.iloc[-1] - e.date.iloc[0]).days / 365.25, 1 / 365.25)
    ending = float(e["eq"].iloc[-1])
    cagr = (ending / 100000.0) ** (1 / years) - 1
    dd = float((e["eq"] / e["eq"].cummax() - 1).min())
    ret = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sharpe = float(ret.mean() / ret.std(ddof=1) * math.sqrt(252)) if ret.std(ddof=1) > 0 else 0.0

    cr = pd.DataFrame(cycle_results)
    result = {
        "name": name,
        "thresholds": ",".join(map(str, THRESHOLDS)),
        "weights": ",".join(map(str, weights)),
        "gated": gated,
        "cycles": len(cycles),
        "entries": len(flat),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": dd,
        "sharpe": sharpe,
        "opposite_boundary_exits": int((cr.reason == "OPPOSITE_BOUNDARY").sum()) if not cr.empty else 0,
        "time_exits": int((cr.reason == "TIME_EXIT").sum()) if not cr.empty else 0,
        "sample_end_exits": int((cr.reason == "SAMPLE_END").sum()) if not cr.empty else 0,
        "mean_layers_opened": float(cr.layers.mean()) if not cr.empty else 0.0,
        "full_ladders": int((cr.layers == len(THRESHOLDS)).sum()) if not cr.empty else 0,
        "positive_cycles": int((cr.realized_pnl > 0).sum()) if not cr.empty else 0,
        "mean_cycle_pnl": float(cr.realized_pnl.mean()) if not cr.empty else np.nan,
        "integer_feasible_layers": integer_feasible,
        "fractional_risk_diagnostic": True,
    }
    cr["strategy"] = name
    return result, cr


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
    state = build_relative_state(con, qu, su, qpath, spath)
    state.to_csv(o / "relative_state.csv", index=False)
    daily_q = load_px(con, qu, "Q")
    valuation_dates = [pd.Timestamp(x) for x in daily_q.date if START <= x.strftime("%Y-%m-%d") <= END]

    results = []
    reports = []
    for name, weights, gated in SCHEDULES:
        rr, rep = simulate(con, state, qpath, spath, name, weights, gated, valuation_dates)
        results.append(rr)
        reports.append(rep)

    pd.DataFrame(results).to_csv(o / "results.csv", index=False)
    if any(not x.empty for x in reports):
        pd.concat(reports, ignore_index=True).to_csv(o / "cycles.csv", index=False)
    else:
        pd.DataFrame().to_csv(o / "cycles.csv", index=False)

    methodology = {
        "idea": "Relative first-passage ladder with state-dependent add gate",
        "relative_state": "log(QQQ ATM-IV60/RV60) - log(SPY ATM-IV60/RV60), ranked causally into [-10,+10]",
        "thresholds": THRESHOLDS,
        "schedules": SCHEDULES,
        "entry": "|relative_score| >= 3",
        "layering": "layers 2/3 open at 6/8 only when divergence is no longer accelerating by more than 0.50 score points/week",
        "harvest": "opposite 8 boundary; reverse into layer 1",
        "timeout_days": MAX_HOLD_DAYS,
        "risk_budget": "5% total pair theoretical risk per cycle, 2.5% per leg",
        "sizing": "fractional risk units for structural diagnosis; integer contract feasibility reported separately",
        "fills": "BUY at ask, SELL at bid; daily MTM at mark",
        "no_live_orders": True,
    }
    (o / "METHODOLOGY.json").write_text(json.dumps(methodology, indent=2), encoding="utf-8")

    lines = [
        "# QQQ-SPY Relative First-Passage Ladder V2",
        "",
        "This is the smarter variant suggested by the literature audit:",
        "rank the relative state directly, use threshold switching, and only add adverse-side tranches when divergence is no longer accelerating.",
        "The P&L run uses fractional risk units strictly as a structural diagnostic; whole-contract feasibility is reported separately.",
        "",
        "| strategy | thresholds | weights | gated | cycles | ending NAV | CAGR | MaxDD | Sharpe | mean layers | full ladders | positive cycles | integer-feasible layers |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['thresholds']} | {r['weights']} | {r['gated']} | "
            f"{r['cycles']} | {r['ending_nav']:.2f} | {r['cagr']:.2%} | {r['maxdd']:.2%} | "
            f"{r['sharpe']:.2f} | {r['mean_layers_opened']:.2f} | {r['full_ladders']} | "
            f"{r['positive_cycles']} | {r['integer_feasible_layers']} |"
        )
    (o / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
