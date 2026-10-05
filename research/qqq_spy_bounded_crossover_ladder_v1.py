from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from qqq_spy_bounded_crossover_reanchor_v1 import (
    START,
    END,
    MAX_HOLD_DAYS,
    build_bounded_state,
    generate_cycles,
    load_px,
    make_pair,
    pair_mtm,
    pair_value,
    unit_marks,
)

# Pre-committed ladder family.
# We test bounded "averaging-in" (adds as the spread becomes more extreme),
# but never allow aggregate theoretical risk above 5% NAV per cycle.
LADDER_SCHEDULES = [
    ("A_EQUAL", [4.0, 8.0, 12.0], [1.0, 1.0, 1.0]),
    ("B_PROGRESSIVE", [4.0, 8.0, 12.0], [1.0, 2.0, 3.0]),
    ("C_FRONTLOADED", [4.0, 8.0, 12.0], [3.0, 2.0, 1.0]),
]


def entry_event_days(state):
    return sorted(pd.to_datetime(state.entry_date).tolist())


def build_ladder_cycles(con, state, qpath, spath, thresholds):
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
                if abs(score) <= 2.0:
                    blocked = False
                else:
                    continue

            direction = 1 if score >= thresholds[0] else (-1 if score <= -thresholds[0] else 0)
            if direction == 0:
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

        # Add all newly-reached same-direction layers on this observation.
        target_score = score * active["direction"]
        while active["next_layer"] < len(thresholds) and target_score >= thresholds[active["next_layer"]]:
            layer_idx = active["next_layer"]
            pair = make_pair(
                con,
                qpath,
                spath,
                d,
                active["direction"],
                f"cycle_{active['cycle_no']:04d}_layer_{layer_idx + 1}",
            )
            if pair is None:
                break
            layer = {
                "layer": layer_idx + 1,
                "entry_date": d,
                "entry_score": score,
                "pair": pair,
                "threshold": thresholds[layer_idx],
            }
            active["layers"].append(layer)
            active["next_layer"] += 1

        if not active["layers"]:
            active = None
            continue

        # Reached the opposite first-passage boundary: harvest all layers,
        # then immediately start the reverse direction at its first layer.
        if target_score <= -thresholds[-1]:
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
            pair = make_pair(
                con, qpath, spath, d,
                reverse["direction"],
                f"cycle_{cycle_no:04d}_layer_1",
            )
            if pair is None:
                active = None
                blocked = True
                continue

            reverse["layers"].append({
                "layer": 1,
                "entry_date": d,
                "entry_score": score,
                "pair": pair,
                "threshold": thresholds[0],
            })
            reverse["next_layer"] = 1
            cycle_no += 1
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


def simulate_ladder(con, state, qpath, spath, name, thresholds, weights, valuation_dates):
    cycles = build_ladder_cycles(con, state, qpath, spath, thresholds)
    flat = flatten_cycles(cycles)
    if not flat:
        return {
            "name": name,
            "cycles": 0,
            "entries": 0,
            "ending_nav": 100000.0,
            "cagr": 0.0,
            "maxdd": 0.0,
            "sharpe": 0.0,
            "opposite_boundary_exits": 0,
            "time_exits": 0,
            "sample_end_exits": 0,
            "mean_layers_opened": 0.0,
            "full_ladders": 0,
            "max_layers": 0,
        }, pd.DataFrame()

    marks = unit_marks(con, qpath, spath, flat)
    mk = {
        (r.contract_id, r.date): (float(r.bid), float(r.ask), float(r.mark))
        for r in marks.itertuples(index=False)
    }

    weight_sum = float(sum(weights))
    norm = [w / weight_sum for w in weights]

    events = {}
    for c in cycles:
        events.setdefault(pd.Timestamp(c["exit_date"]), []).append(("CLOSE", c))
    for c in cycles:
        for layer in c["layers"]:
            events.setdefault(pd.Timestamp(layer["entry_date"]), []).append(("OPEN_LAYER", (c, layer)))

    nav = 100000.0
    realized = 0.0
    openpos = []
    rows = []
    layer_pnl = []
    cycle_results = []

    for d in valuation_dates:
        # Harvest first.
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
            cycle_results.append({
                "cycle": c["cycle_no"],
                "entry": c["entry_date"],
                "exit": c["exit_date"],
                "entry_score": c["entry_score"],
                "exit_score": c["exit_score"],
                "direction": c["direction"],
                "reason": c["exit_reason"],
                "layers": len(c["layers"]),
                "realized_pnl": pnl if ok_all else np.nan,
            })

        # Open newly reached layers. The total cycle risk budget is capped at 5% NAV,
        # and each layer gets only its pre-committed fraction.
        for action, item in events.get(d, []):
            if action != "OPEN_LAYER":
                continue
            c, layer = item
            # Use current NAV immediately before the layer.
            layer_frac = norm[layer["layer"] - 1]
            risk_target_per_leg = max(nav, 1.0) * 0.025 * layer_frac
            max_qty = min(
                int(math.floor(risk_target_per_leg / max(float(p["risk"]), 1e-9)))
                for p in layer["pair"]
            )
            if max_qty < 1:
                # Skip the whole tranche rather than violating its pre-committed risk budget.
                continue
            for p in layer["pair"]:
                p2 = p.copy()
                p2["qty"] = max_qty
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
    r = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sh = float(r.mean() / r.std(ddof=1) * math.sqrt(252)) if r.std(ddof=1) > 0 else 0.0

    cr = pd.DataFrame(cycle_results)
    reason_counts = cr.reason.value_counts().to_dict() if not cr.empty else {}
    result = {
        "name": name,
        "thresholds": ",".join(str(x) for x in thresholds),
        "weights": ",".join(str(x) for x in weights),
        "cycles": len(cycles),
        "entries": len(flat),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": dd,
        "sharpe": sh,
        "opposite_boundary_exits": int(reason_counts.get("OPPOSITE_BOUNDARY", 0)),
        "time_exits": int(reason_counts.get("TIME_EXIT", 0)),
        "sample_end_exits": int(reason_counts.get("SAMPLE_END", 0)),
        "mean_layers_opened": float(cr.layers.mean()) if not cr.empty else 0.0,
        "full_ladders": int((cr.layers == len(thresholds)).sum()) if not cr.empty else 0,
        "max_layers": int(cr.layers.max()) if not cr.empty else 0,
        "positive_cycles": int((cr.realized_pnl > 0).sum()) if not cr.empty else 0,
        "mean_cycle_pnl": float(cr.realized_pnl.mean()) if not cr.empty else np.nan,
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

    con = __import__("duckdb").connect()
    state = build_bounded_state(con, qu, su, qpath, spath)
    state.to_csv(o / "bounded_state.csv", index=False)

    daily_q = load_px(con, qu, "Q")
    valuation_dates = [pd.Timestamp(x) for x in daily_q.date if START <= x.strftime("%Y-%m-%d") <= END]

    results = []
    reports = []
    for name, thresholds, weights in LADDER_SCHEDULES:
        rr, rep = simulate_ladder(
            con, state, qpath, spath, name, thresholds, weights, valuation_dates
        )
        results.append(rr)
        reports.append(rep)

    pd.DataFrame(results).to_csv(o / "results.csv", index=False)
    if any(not r.empty for r in reports):
        pd.concat(reports, ignore_index=True).to_csv(o / "cycles.csv", index=False)
    else:
        pd.DataFrame().to_csv(o / "cycles.csv", index=False)

    methodology = {
        "period": [START, END],
        "state": "causal weekly D = bounded_percentile(QQQ IV60/RV60) - bounded_percentile(SPY IV60/RV60)",
        "layers": LADDER_SCHEDULES,
        "entry": "layer k opens when |D| reaches threshold k in the active direction",
        "harvest": "all opened layers close at the opposite boundary; then reverse into layer 1",
        "timeout": f"{MAX_HOLD_DAYS} days",
        "risk_budget": "5% total theoretical pair risk per cycle; layer fractions normalized to 100%",
        "sizing": "each opened layer targets its fraction of 2.5% QQQ + 2.5% SPY theoretical risk using current NAV",
        "fills": "BUY at ask, SELL at bid; daily MTM at mark",
        "no_live_orders": True,
    }
    (o / "METHODOLOGY.json").write_text(json.dumps(methodology, indent=2), encoding="utf-8")

    lines = [
        "# QQQ-SPY Bounded Crossover / Layered Add V1",
        "",
        "Purpose: test bounded tranche adding as divergence becomes more extreme.",
        "This is not infinite martingale; total theoretical pair risk is capped at 5% NAV per cycle.",
        "",
        "| strategy | thresholds | weights | cycles | ending NAV | CAGR | MaxDD | Sharpe | mean layers | full ladders | positive cycles |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['thresholds']} | {r['weights']} | {r['cycles']} | "
            f"{r['ending_nav']:.2f} | {r['cagr']:.2%} | {r['maxdd']:.2%} | "
            f"{r['sharpe']:.2f} | {r['mean_layers_opened']:.2f} | "
            f"{r['full_ladders']} | {r['positive_cycles']} |"
        )
    lines += [
        "",
        "Exploratory only. Layer schedule is precommitted; no search-until-pass and no OOS selection.",
    ]
    (o / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
