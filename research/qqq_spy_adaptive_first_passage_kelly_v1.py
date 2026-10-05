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

ENTRY_H = 3.0
OPPOSITE_H = 8.0
MAX_RISK = 0.05
FRACTIONAL_KELLY = 0.25
MIN_TRAIN = 20
BUCKETS = [(3.0, 6.0), (6.0, 8.0), (8.0, 20.1)]


def sql(con, s):
    return con.execute(s).df()


def pathq(p):
    return str(p).replace("'", "''")


def build_state(con, qu, su, qpath, spath):
    q = load_px(con, qu, "Q")
    s = load_px(con, su, "S")
    x = q.merge(s, on=["date", "month"], how="inner").sort_values("date").reset_index(drop=True)
    days = weekly_observation_days(x)
    st = x.set_index("date")
    dates = sorted(pd.to_datetime(x.date).tolist())
    signal_dates = [prev_trading_date(dates, d) for d in days]
    signal_dates = [d for d in signal_dates if d is not None]
    qiv = atm_iv60_series(con, qpath, signal_dates)
    siv = atm_iv60_series(con, spath, signal_dates)

    rows = []
    for d in days:
        sigd = prev_trading_date(dates, d)
        if sigd is None:
            continue
        r = st.loc[sigd]
        qrv = float(r.Q_rv60) if pd.notna(r.Q_rv60) else np.nan
        srv = float(r.S_rv60) if pd.notna(r.S_rv60) else np.nan
        q_iv = qiv.get(pd.Timestamp(sigd), np.nan)
        s_iv = siv.get(pd.Timestamp(sigd), np.nan)
        q_vrp = q_iv / qrv if np.isfinite(q_iv) and np.isfinite(qrv) and qrv > 0 else np.nan
        s_vrp = s_iv / srv if np.isfinite(s_iv) and np.isfinite(srv) and srv > 0 else np.nan
        rel = (
            np.log(q_vrp / s_vrp)
            if np.isfinite(q_vrp) and np.isfinite(s_vrp) and q_vrp > 0 and s_vrp > 0
            else np.nan
        )
        rows.append(
            {
                "signal_date": pd.Timestamp(sigd),
                "entry_date": pd.Timestamp(d),
                "q_vrp": q_vrp,
                "s_vrp": s_vrp,
                "log_vrp_ratio": rel,
            }
        )

    z = pd.DataFrame(rows).sort_values("entry_date").reset_index(drop=True)
    z["d_score"] = bounded_percentile(z.log_vrp_ratio)
    z["d_delta"] = z.d_score.diff()
    z["abs_d"] = z.d_score.abs()
    return z


def build_first_passage_labels(state):
    """Historical state labels. Labels are allowed to look forward because only
    samples with label_end < current trading date are later used for training."""
    e = state[state.d_score.notna()].reset_index(drop=True)
    labels = []
    max_obs_gap = pd.Timedelta(days=MAX_HOLD_DAYS)
    for i, row in e.iterrows():
        d0 = pd.Timestamp(row.entry_date)
        s0 = float(row.d_score)
        if abs(s0) < ENTRY_H:
            continue
        direction = 1 if s0 > 0 else -1
        end_limit = d0 + max_obs_gap
        success = False
        end_date = None
        for j in range(i + 1, len(e)):
            dj = pd.Timestamp(e.iloc[j].entry_date)
            if dj > end_limit:
                break
            sj = float(e.iloc[j].d_score)
            if sj * direction <= -OPPOSITE_H:
                success = True
                end_date = dj
                break
        if end_date is None:
            # Failure is censored at the 45D horizon when there is an observation there.
            future = e[(e.entry_date > d0) & (e.entry_date <= end_limit)]
            if future.empty:
                continue
            end_date = pd.Timestamp(future.entry_date.iloc[-1])

        a = abs(s0)
        if a < 6:
            bucket = "3-6"
        elif a < 8:
            bucket = "6-8"
        else:
            bucket = "8-10"
        labels.append(
            {
                "sample_date": d0,
                "label_end": end_date,
                "direction": direction,
                "abs_score": a,
                "bucket": bucket,
                "success": int(success),
            }
        )
    return pd.DataFrame(labels)


def build_historical_option_cycles(con, state, qpath, spath):
    """Create realized one-layer pair outcomes used only after their exit date."""
    e = state[state.d_score.notna()].reset_index(drop=True)
    out = []
    active = None
    blocked = False
    no = 0

    for i, row in e.iterrows():
        d = pd.Timestamp(row.entry_date)
        score = float(row.d_score)
        if active is None:
            if blocked:
                if abs(score) <= 2.0:
                    blocked = False
                else:
                    continue
            if abs(score) < ENTRY_H:
                continue
            direction = 1 if score > 0 else -1
            pair = make_pair(con, qpath, spath, d, direction, f"hist_{no:04d}")
            if pair is None:
                continue
            active = {
                "cycle": no,
                "direction": direction,
                "entry_date": d,
                "entry_score": score,
                "pair": pair,
                "expiry_limit": d + pd.Timedelta(days=MAX_HOLD_DAYS),
            }
            no += 1
            continue

        target = score * active["direction"]
        if target <= -OPPOSITE_H:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "OPPOSITE_BOUNDARY"
            out.append(active)
            active = None
        elif d >= active["expiry_limit"]:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "TIME_EXIT"
            out.append(active)
            active = None
            blocked = True

    return out


def enrich_historical_payoff(con, cycles, qpath, spath):
    if not cycles:
        return pd.DataFrame()
    positions = []
    for c in cycles:
        for p in c["pair"]:
            p2 = p.copy()
            p2["cycle"] = c["cycle"]
            positions.append(p2)
    marks = unit_marks(con, qpath, spath, positions)
    mk = {
        (r.contract_id, r.date): (float(r.bid), float(r.ask), float(r.mark))
        for r in marks.itertuples(index=False)
    }
    rows = []
    for c in cycles:
        pnl = 0.0
        ok = True
        risk = 0.0
        for p in c["pair"]:
            v, valid = pair_value(p, mk, c["exit_date"], 1.0)
            if not valid:
                ok = False
                break
            pnl += v
            risk += max(float(p["risk"]), 0.0)
        if ok and risk > 0:
            rows.append(
                {
                    "cycle": c["cycle"],
                    "entry_date": c["entry_date"],
                    "exit_date": c["exit_date"],
                    "direction": c["direction"],
                    "entry_score": c["entry_score"],
                    "exit_score": c["exit_score"],
                    "reason": c["exit_reason"],
                    "pnl": pnl,
                    "risk": risk,
                    "pnl_risk": pnl / risk,
                }
            )
    return pd.DataFrame(rows)


def bucket_for(abs_score):
    for lo, hi in BUCKETS:
        if lo <= abs_score < hi:
            return f"{lo:g}-{hi:g}"
    return "8-10"


def posterior_probability(labels, current_date, direction, abs_score):
    if labels.empty:
        return 0.5, 0, "NO_DATA"

    usable = labels[labels.label_end < current_date]
    if usable.empty:
        return 0.5, 0, "NO_PURGED_DATA"

    direction_all = usable[usable.direction == direction]
    target_bucket = bucket_for(abs_score)
    bucket = direction_all[direction_all.bucket == target_bucket]

    # Hierarchical shrinkage: local bucket receives weight, direction prior supplies stability.
    base_n = len(direction_all)
    base_wins = float(direction_all.success.sum())
    base_p = (base_wins + 4.0) / (base_n + 8.0)

    local_n = len(bucket)
    if local_n >= 8:
        local_p = (float(bucket.success.sum()) + 4.0) / (local_n + 8.0)
        shrink = min(1.0, local_n / 24.0)
        p = shrink * local_p + (1.0 - shrink) * base_p
        return float(np.clip(p, 0.05, 0.95)), local_n, "LOCAL_SHRUNK"
    return float(np.clip(base_p, 0.05, 0.95)), base_n, "DIRECTION_PRIOR"


def payoff_ratio(history, current_date, direction):
    if history.empty:
        return 1.0, 0
    h = history[history.exit_date < current_date]
    same = h[h.direction == direction]
    use = same if len(same) >= 4 else h
    if use.empty:
        return 1.0, 0
    wins = use.loc[use.pnl_risk > 0, "pnl_risk"]
    losses = -use.loc[use.pnl_risk < 0, "pnl_risk"]
    if wins.empty or losses.empty:
        return 1.0, len(use)
    b = float(wins.mean() / losses.mean())
    return float(np.clip(b, 0.25, 4.0)), len(use)


def kelly_risk(p, b):
    # Full Kelly for a binary approximation, then hard fractional-Kelly cut.
    edge = b * p - (1.0 - p)
    if edge <= 0 or b <= 0:
        return 0.0
    f = edge / b
    return float(np.clip(FRACTIONAL_KELLY * f, 0.0, MAX_RISK))


def build_current_cycles(con, state, qpath, spath):
    e = state[state.d_score.notna()].reset_index(drop=True)
    cycles = []
    active = None
    blocked = False
    no = 0

    for row in e.itertuples(index=False):
        d = pd.Timestamp(row.entry_date)
        score = float(row.d_score)
        if active is None:
            if blocked:
                if abs(score) <= 2.0:
                    blocked = False
                else:
                    continue
            if abs(score) < ENTRY_H:
                continue
            direction = 1 if score > 0 else -1
            active = {
                "cycle": no,
                "direction": direction,
                "entry_date": d,
                "entry_score": score,
                "layers": [],
                "next_layer": 0,
                "risk_open": 0.0,
                "expiry_limit": d + pd.Timedelta(days=MAX_HOLD_DAYS),
            }
            no += 1

        target = score * active["direction"]
        # At most three trigger levels. Position risk, not contract count, is adaptive.
        for level in (3.0, 6.0, 8.0):
            if active["next_layer"] >= (1 if level == 3.0 else 2 if level == 6.0 else 3):
                continue
            if target < level:
                break
            pair = make_pair(
                con,
                qpath,
                spath,
                d,
                active["direction"],
                f"cycle_{active['cycle']:04d}_layer_{int(level)}",
            )
            if pair is None:
                break
            p, n, source = posterior_probability(
                LABELS, d, active["direction"], abs(score)
            )
            b, bn = payoff_ratio(HISTORY, d, active["direction"])
            desired = kelly_risk(p, b)
            if desired <= active["risk_open"] + 1e-12:
                add_risk_pct = 0.0
            else:
                add_risk_pct = desired - active["risk_open"]
            active["layers"].append(
                {
                    "layer": 1 if level == 3.0 else 2 if level == 6.0 else 3,
                    "entry_date": d,
                    "entry_score": score,
                    "pair": pair,
                    "threshold": level,
                    "probability": p,
                    "samples": n,
                    "prob_source": source,
                    "payoff_ratio": b,
                    "payoff_samples": bn,
                    "desired_cycle_risk_pct": desired,
                    "add_risk_pct": add_risk_pct,
                }
            )
            active["risk_open"] += add_risk_pct
            active["next_layer"] = 1 if level == 3.0 else 2 if level == 6.0 else 3

        if active["layers"] and target <= -OPPOSITE_H:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "OPPOSITE_BOUNDARY"
            cycles.append(active)

            # Reverse immediately; its risk budget is recomputed from then-current information.
            active = {
                "cycle": no,
                "direction": -active["direction"],
                "entry_date": d,
                "entry_score": score,
                "layers": [],
                "next_layer": 0,
                "risk_open": 0.0,
                "expiry_limit": d + pd.Timedelta(days=MAX_HOLD_DAYS),
            }
            no += 1

        elif active["layers"] and d >= active["expiry_limit"]:
            active["exit_date"] = d
            active["exit_score"] = score
            active["exit_reason"] = "TIME_EXIT"
            cycles.append(active)
            active = None
            blocked = True

    if active is not None and active["layers"]:
        active["exit_date"] = pd.Timestamp(e.entry_date.iloc[-1])
        active["exit_score"] = float(e.d_score.iloc[-1])
        active["exit_reason"] = "SAMPLE_END"
        cycles.append(active)
    return cycles


def flatten(cycles):
    out = []
    for c in cycles:
        for l in c["layers"]:
            for p in l["pair"]:
                z = p.copy()
                z["cycle"] = c["cycle"]
                z["layer"] = l["layer"]
                z["exit_date"] = c["exit_date"]
                z["exit_reason"] = c["exit_reason"]
                out.append(z)
    return out


def simulate(con, state, qpath, spath, valuation_dates, name):
    cycles = build_current_cycles(con, state, qpath, spath)
    flat = flatten(cycles)
    if not flat:
        return {
            "name": name, "cycles": 0, "entries": 0, "ending_nav": 100000.0,
            "cagr": 0.0, "maxdd": 0.0, "sharpe": 0.0, "mean_cycle_risk_pct": 0.0,
            "mean_p_hit": 0.5, "mean_layers": 0.0, "full_ladders": 0,
        }, pd.DataFrame(), pd.DataFrame()

    marks = unit_marks(con, qpath, spath, flat)
    mk = {
        (r.contract_id, r.date): (float(r.bid), float(r.ask), float(r.mark))
        for r in marks.itertuples(index=False)
    }

    events = {}
    for c in cycles:
        events.setdefault(pd.Timestamp(c["exit_date"]), []).append(("CLOSE", c))
        for l in c["layers"]:
            events.setdefault(pd.Timestamp(l["entry_date"]), []).append(("OPEN", (c, l)))

    nav = 100000.0
    realized = 0.0
    openpos = []
    rows = []
    reports = []
    for d in valuation_dates:
        for action, c in events.get(d, []):
            if action != "CLOSE":
                continue
            pnl = 0.0
            ok = True
            for p in openpos[:]:
                if p["cycle"] != c["cycle"]:
                    continue
                v, valid = pair_value(p, mk, d, p["qty"])
                if valid:
                    realized += v
                    pnl += v
                    openpos.remove(p)
                else:
                    ok = False
            reports.append(
                {
                    "cycle": c["cycle"],
                    "entry": c["entry_date"],
                    "exit": c["exit_date"],
                    "direction": c["direction"],
                    "entry_score": c["entry_score"],
                    "exit_score": c["exit_score"],
                    "reason": c["exit_reason"],
                    "layers": len(c["layers"]),
                    "risk_pct_sum": sum(l["add_risk_pct"] for l in c["layers"]),
                    "realized_pnl": pnl if ok else np.nan,
                    "mean_p_hit": float(np.mean([l["probability"] for l in c["layers"]])) if c["layers"] else np.nan,
                }
            )

        for action, item in events.get(d, []):
            if action != "OPEN":
                continue
            c, l = item
            add_total_risk = float(l["add_risk_pct"])
            if add_total_risk <= 0:
                continue
            # Split incremental theoretical risk equally between QQQ and SPY legs.
            per_leg_risk = max(nav, 1.0) * add_total_risk / 2.0
            pair_risk = max(sum(max(float(p["risk"]), 0.0) for p in l["pair"]), 1e-9)
            # Same fractional risk unit across both structures.
            qty = min(
                per_leg_risk / max(float(l["pair"][0]["risk"]), 1e-9),
                per_leg_risk / max(float(l["pair"][1]["risk"]), 1e-9),
            )
            if qty <= 0 or not np.isfinite(qty):
                continue
            for p in l["pair"]:
                p2 = p.copy()
                p2["qty"] = float(qty)
                p2["layer"] = l["layer"]
                p2["cycle"] = c["cycle"]
                openpos.append(p2)

        mtm = 0.0
        for p in openpos:
            v, valid = pair_mtm(p, mk, d, p["qty"])
            if valid:
                mtm += v
        nav = 100000.0 + realized + mtm
        rows.append((d, nav))

    e = pd.DataFrame(rows, columns=["date", "eq"])
    years = max((e.date.iloc[-1] - e.date.iloc[0]).days / 365.25, 1 / 365.25)
    ending = float(e["eq"].iloc[-1])
    cagr = (ending / 100000.0) ** (1.0 / years) - 1.0
    dd = float((e["eq"] / e["eq"].cummax() - 1.0).min())
    ret = e["eq"].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    sharpe = float(ret.mean() / ret.std(ddof=1) * math.sqrt(252)) if ret.std(ddof=1) > 0 else 0.0
    cr = pd.DataFrame(reports)

    all_layers = [l for c in cycles for l in c["layers"]]
    result = {
        "name": name,
        "entry_h": ENTRY_H,
        "opposite_h": OPPOSITE_H,
        "max_risk_pct": MAX_RISK,
        "fractional_kelly": FRACTIONAL_KELLY,
        "cycles": len(cycles),
        "entries": len(flat),
        "ending_nav": ending,
        "cagr": float(cagr),
        "maxdd": dd,
        "sharpe": sharpe,
        "mean_cycle_risk_pct": float(np.mean([sum(l["add_risk_pct"] for l in c["layers"]) for c in cycles])) if cycles else 0.0,
        "mean_p_hit": float(np.mean([l["probability"] for l in all_layers])) if all_layers else 0.5,
        "mean_layers": float(np.mean([len(c["layers"]) for c in cycles])) if cycles else 0.0,
        "full_ladders": int(sum(len(c["layers"]) == 3 for c in cycles)),
        "positive_cycles": int((cr.realized_pnl > 0).sum()) if not cr.empty else 0,
    }
    state_report = state.copy()
    return result, cr, state_report


def main():
    global LABELS, HISTORY

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
    state = build_state(con, qu, su, qpath, spath)
    labels = build_first_passage_labels(state)
    LABELS = labels
    hist_cycles = build_historical_option_cycles(con, state, qpath, spath)
    HISTORY = enrich_historical_payoff(con, hist_cycles, qpath, spath)

    state.to_csv(o / "relative_state.csv", index=False)
    labels.to_csv(o / "first_passage_labels.csv", index=False)
    HISTORY.to_csv(o / "historical_pair_payoffs.csv", index=False)

    daily_q = load_px(con, qu, "Q")
    valuation_dates = [pd.Timestamp(x) for x in daily_q.date if START <= x.strftime("%Y-%m-%d") <= END]

    rr, cycles, state_report = simulate(con, state, qpath, spath, valuation_dates, "A_ADAPTIVE_FIRST_PASSAGE_KELLY")
    pd.DataFrame([rr]).to_csv(o / "results.csv", index=False)
    cycles.to_csv(o / "cycles.csv", index=False)
    state_report.to_csv(o / "state_replay.csv", index=False)

    methodology = {
        "name": "Adaptive First-Passage Kelly V1",
        "signal": "log((QQQ ATM IV60/RV60)/(SPY ATM IV60/RV60)) transformed by causal rolling percentile into d_score [-10,+10]",
        "entry": "|d_score| >= 3",
        "layer_triggers": [3, 6, 8],
        "harvest": "opposite boundary -8 in active direction; then reverse",
        "timeout_days": MAX_HOLD_DAYS,
        "probability_model": "historical first-passage hit probability, direction-conditioned and score-bucket-conditioned with Beta(4,4) shrinkage; labels must end before current date",
        "payoff_model": "historical realized one-layer QQQ/SPY option pair pnl normalized by theoretical risk; only cycles exited before current date",
        "sizing": "0.25 Kelly from p and empirical payoff ratio; cumulative theoretical pair risk hard-capped at 5% NAV; later layers add only when desired Kelly risk exceeds risk already opened",
        "fills": "BUY at ask, SELL at bid; daily MTM at mark",
        "fractional_units": True,
        "no_live_orders": True,
        "no_parameter_search": True,
    }
    (o / "METHODOLOGY.json").write_text(json.dumps(methodology, indent=2), encoding="utf-8")

    lines = [
        "# QQQ-SPY Adaptive First-Passage Kelly V1",
        "",
        "The ladder is no longer fixed 1:2:3. Historical first-passage probability and realized option-pair payoff jointly determine the desired risk.",
        "A new layer can only increase risk when the causal Kelly budget rises; total theoretical pair risk is capped at 5% NAV.",
        "",
        "| strategy | cycles | ending NAV | CAGR | MaxDD | Sharpe | mean cycle risk | mean p(hit) | mean layers | full ladders | positive cycles |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {rr['name']} | {rr['cycles']} | {rr['ending_nav']:.2f} | {rr['cagr']:.2%} | {rr['maxdd']:.2%} | {rr['sharpe']:.2f} | {rr['mean_cycle_risk_pct']:.2%} | {rr['mean_p_hit']:.3f} | {rr['mean_layers']:.2f} | {rr['full_ladders']} | {rr['positive_cycles']} |",
        "",
        "Research diagnostic only. All training labels/payoff observations are purged so their information ends before the current sizing date.",
    ]
    (o / "RESULTS.md").write_text("\\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
