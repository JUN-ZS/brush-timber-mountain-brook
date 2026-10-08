from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_spy_self_financing_range_v1 import (
    START,
    END,
    TD,
    M,
    build_state,
    entry_days,
    prev_trading_date,
    qqq_rc,
    spy_ic,
    _load_marks,
    load_px,
)


Q_TARGET = 90
Q_LONG_DELTA = 0.25
Q_WING_DELTA = 0.05
Q_EXIT_DTE = 35
SPY_TARGET = 30
SPY_WING_DELTA = 0.10
PAIR_CAP = 3
RISK_BUDGET = 0.05

# New hypothesis, precommitted before this run:
# elevated QQQ/SPY correlation means diversification between the two sleeves
# is less useful, so do not sell SPY volatility to finance QQQ convexity when
# current 60-day realized correlation is above its causal 252-day median.
NEW_POLICY = "CORRELATION_MEDIAN_VETO"


def sql(con, s, params=None):
    return con.execute(s, params or {}).df()


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build_corr_state(con, qu, su, base_state):
    q = load_px(con, qu, "Q")[["date", "Q_px"]].copy()
    s = load_px(con, su, "S")[["date", "S_px"]].copy()
    x = q.merge(s, on="date", how="inner").sort_values("date").reset_index(drop=True)
    qr = np.log(x["Q_px"] / x["Q_px"].shift(1))
    sr = np.log(x["S_px"] / x["S_px"].shift(1))
    # State is evaluated on the prior trading date before entry. Therefore
    # corr60 may include information through that signal date, but the
    # reference median excludes the current corr60 observation.
    x["corr60"] = qr.rolling(60, min_periods=40).corr(sr)
    x["corr_med_252"] = x["corr60"].rolling(252, min_periods=126).median().shift(1)

    st = base_state.copy()
    st["date"] = pd.to_datetime(st["date"])
    corr = x[["date", "corr60", "corr_med_252"]].copy()
    corr["date"] = pd.to_datetime(corr["date"])
    st = st.merge(corr, on="date", how="left")
    st["corr_gate_ok"] = (
        st["corr60"].notna()
        & st["corr_med_252"].notna()
        & (st["corr60"] <= st["corr_med_252"])
    )
    return st


def signal_qualifies(signal_row, q_sig, s_sig, gated):
    q_ratio = float(signal_row.Q_rv60) / float(q_sig["atm_iv"])
    s_ratio = float(s_sig["atm_iv"]) / float(signal_row.S_rv30)
    qualify = q_ratio > 1.0 and s_ratio > 1.0
    if gated and not bool(signal_row.corr_gate_ok):
        qualify = False
    return qualify, q_ratio, s_ratio


def make_position(component, qty, entry_date, exit_date):
    return {
        **component,
        "qty": int(qty),
        "entry_date": pd.Timestamp(entry_date),
        "exit_date": pd.Timestamp(exit_date),
    }


def build_candidates(con, state, qpath, spath, gated, name):
    days = entry_days(state)
    state_dates = sorted(pd.to_datetime(state.date).tolist())
    st = state.set_index("date")

    q_candidates = []
    pair_candidates = []
    signal_rows = []

    for d in days:
        sigd = prev_trading_date(state_dates, d)
        if sigd is None:
            continue
        try:
            row = st.loc[pd.Timestamp(sigd)]
        except KeyError:
            continue
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        q_sig = qqq_rc(
            con, qpath, sigd, Q_TARGET, Q_WING_DELTA, Q_LONG_DELTA, Q_EXIT_DTE
        )
        s_sig = spy_ic(con, spath, sigd, SPY_TARGET, SPY_WING_DELTA)
        if q_sig is None or s_sig is None:
            continue

        qualifies, q_ratio, s_ratio = signal_qualifies(
            row, q_sig, s_sig, gated
        )

        signal_rows.append(
            {
                "strategy": name,
                "signal_date": pd.Timestamp(sigd),
                "entry_date": pd.Timestamp(d),
                "q_ratio": pair["q_ratio"],
                "s_ratio": pair["s_ratio"],
                "corr60": float(row.corr60) if pd.notna(row.corr60) else np.nan,
                "corr_med_252": float(row.corr_med_252) if pd.notna(row.corr_med_252) else np.nan,
                "corr_gate_ok": bool(row.corr_gate_ok) if pd.notna(row.corr_gate_ok) else False,
                "eligible_signal": bool(qualifies),
                "required_spy_units_entry": np.nan,
            }
        )

        q_entry = None
        s_entry = None
        entry_units = np.nan

        if qualifies:
            q_entry = qqq_rc(
                con, qpath, d, Q_TARGET, Q_WING_DELTA, Q_LONG_DELTA, Q_EXIT_DTE
            )
            s_entry = spy_ic(
                con, spath, d, SPY_TARGET, SPY_WING_DELTA
            )
            if q_entry is not None and s_entry is not None:
                q_debit_entry = float(q_entry["entry_value"])
                s_credit_entry = float(s_entry["entry_value"])
                if q_debit_entry > 0 and s_credit_entry > 0:
                    entry_units = int(math.ceil(q_debit_entry / s_credit_entry))
                qualifies = bool(entry_units == entry_units and entry_units <= PAIR_CAP)

        # Benchmark B: activity-matched QQQ-only. Same final pair eligibility,
        # but removes SPY. This isolates the incremental value of the SPY leg.
        if qualifies and q_entry is not None:
            q_exit = pd.Timestamp(q_entry["expiry"]) - pd.Timedelta(days=q_entry["exit_dte"])
            q_candidates.append(
                {
                    "name": f"{name}_Q_{len(q_candidates)}",
                    "symbol": "QQQ",
                    "legs": q_entry["legs"],
                    "risk": float(q_entry["risk"]),
                    "entry_value": float(q_entry["entry_value"]),
                    "entry_cf": -float(q_entry["entry_value"]),
                    "entry": pd.Timestamp(d),
                    "expiry": pd.Timestamp(q_entry["expiry"]),
                    "exit_dte": int(q_entry["exit_dte"]),
                    "target_exit": q_exit,
                }
            )

        if qualifies and q_entry is not None and s_entry is not None and np.isfinite(entry_units):
            pair_candidates.append(
                {
                    "name": f"{name}_PAIR_{len(pair_candidates)}",
                    "entry": pd.Timestamp(d),
                    "components": [
                        {
                            "symbol": "QQQ",
                            "legs": q_entry["legs"],
                            "risk": float(q_entry["risk"]),
                            "entry_cf": -float(q_entry["entry_value"]),
                            "expiry": pd.Timestamp(q_entry["expiry"]),
                            "exit_dte": int(q_entry["exit_dte"]),
                            "units": 1,
                        },
                        {
                            "symbol": "SPY",
                            "legs": s_entry["legs"],
                            "risk": float(s_entry["risk"]),
                            "entry_cf": float(s_entry["entry_value"]),
                            "expiry": pd.Timestamp(s_entry["expiry"]),
                            "exit_dte": 7,
                            "units": int(entry_units),
                        },
                    ],
                    "risk": float(q_entry["risk"]) + int(entry_units) * float(s_entry["risk"]),
                    "q_ratio": q_ratio,
                    "s_ratio": s_ratio,
                    "corr60": float(row.corr60) if pd.notna(row.corr60) else np.nan,
                    "corr_med_252": float(row.corr_med_252) if pd.notna(row.corr_med_252) else np.nan,
                    "corr_gate_ok": bool(row.corr_gate_ok) if pd.notna(row.corr_gate_ok) else False,
                    "spy_units": int(entry_units),
                }
            )

        signal_rows[-1]["eligible_final"] = bool(qualifies)
        signal_rows[-1]["required_spy_units_entry"] = int(entry_units) if np.isfinite(entry_units) else np.nan
        signal_rows[-1]["entry_funding_ok"] = bool(qualifies)
    return q_candidates, pair_candidates, pd.DataFrame(signal_rows)


def load_marks_for_candidates(con, qpath, spath, q_candidates, pair_candidates):
    ids = []
    for p in q_candidates:
        for leg in p["legs"]:
            ids.append((p["symbol"], str(leg[6])))
    for b in pair_candidates:
        for c in b["components"]:
            for leg in c["legs"]:
                ids.append((c["symbol"], str(leg[6])))
    return _load_marks(con, qpath, spath, ids)


def current_mtm(active, marks, d):
    total = 0.0
    for p in active:
        if "components" in p:
            for comp in p["components"]:
                for leg in comp["legs"]:
                    _, _, mark = marks.get((comp["symbol"], str(leg[6]), d), (None, None, None))
                    if mark is None:
                        return None
                    total += leg[4] * mark * M * p["qty"] * comp["units"]
                total += comp["entry_cf"] * p["qty"] * comp["units"]
        else:
            for leg in p["legs"]:
                _, _, mark = marks.get((p["symbol"], str(leg[6]), d), (None, None, None))
                if mark is None:
                    return None
                total += leg[4] * mark * M * p["qty"]
            total += p["entry_cf"] * p["qty"]
    return total


def run_q_only(con, state, marks, candidates, name, target_dates):
    by_entry = {}
    for p in candidates:
        by_entry.setdefault(pd.Timestamp(p["entry"]), []).append(p)

    active = []
    realized = 0.0
    rows = []
    for d in target_dates:
        d = pd.Timestamp(d)
        nav_before = 100000.0 + realized + (current_mtm(active, marks, d) or 0.0)
        for p in by_entry.get(d, []):
            qty = int(math.floor(max(nav_before, 1.0) * RISK_BUDGET / max(p["risk"], 1e-9)))
            if qty > 0:
                active.append(make_position(p, qty, d, p["target_exit"]))

        still = []
        for p in active:
            exitd = max(d, pd.Timestamp(p["exit_date"]))
            if d == exitd:
                v = 0.0
                ok = True
                for leg in p["legs"]:
                    bid, ask, mark = marks.get((p["symbol"], str(leg[6]), d), (None, None, None))
                    if mark is None:
                        ok = False
                        break
                    fill = bid if leg[4] == 1 else ask
                    v += leg[4] * fill * M * p["qty"]
                if ok:
                    realized += p["entry_cf"] * p["qty"] + v
                else:
                    still.append(p)
            else:
                still.append(p)
        active = still

        mtm = 0.0
        for p in active:
            v = 0.0
            ok = True
            for leg in p["legs"]:
                _, _, mark = marks.get((p["symbol"], str(leg[6]), d), (None, None, None))
                if mark is None:
                    ok = False
                    break
                v += leg[4] * mark * M * p["qty"]
            if ok:
                mtm += p["entry_cf"] * p["qty"] + v

        rows.append((d, 100000.0 + realized + mtm))

    return finalize_curve(pd.DataFrame(rows, columns=["date", "eq"]), name)


def run_pair(con, state, marks, candidates, name, target_dates):
    by_entry = {}
    for b in candidates:
        by_entry.setdefault(pd.Timestamp(b["entry"]), []).append(b)

    active = []
    realized = 0.0
    rows = []
    for d in target_dates:
        d = pd.Timestamp(d)
        nav_now = max(100000.0 + realized + (current_mtm(active, marks, d) or 0.0), 1.0)
        for b in by_entry.get(d, []):
            qty = int(math.floor(nav_now * RISK_BUDGET / max(b["risk"], 1e-9)))
            if qty > 0:
                active.append({**b, "qty": qty, "component_open": [True, True]})
                realized += sum(c["entry_cf"] * c["units"] for c in b["components"]) * qty

        still = []
        for b in active:
            for i, c in enumerate(b["components"]):
                if not b["component_open"][i]:
                    continue
                exitd = max(d, pd.Timestamp(c["expiry"]) - pd.Timedelta(days=c["exit_dte"]))
                if d == exitd:
                    v = 0.0
                    ok = True
                    for leg in c["legs"]:
                        bid, ask, mark = marks.get((c["symbol"], str(leg[6]), d), (None, None, None))
                        if mark is None:
                            ok = False
                            break
                        fill = bid if leg[4] == 1 else ask
                        v += leg[4] * fill * M * b["qty"] * c["units"]
                    if ok:
                        realized += v
                        b["component_open"][i] = False
            if any(b["component_open"]):
                still.append(b)
        active = still

        mtm = 0.0
        for b in active:
            for i, c in enumerate(b["components"]):
                if not b["component_open"][i]:
                    continue
                v = 0.0
                ok = True
                for leg in c["legs"]:
                    _, _, mark = marks.get((c["symbol"], str(leg[6]), d), (None, None, None))
                    if mark is None:
                        ok = False
                        break
                    v += leg[4] * mark * M * b["qty"] * c["units"]
                if ok:
                    mtm += v

        rows.append((d, 100000.0 + realized + mtm))

    return finalize_curve(pd.DataFrame(rows, columns=["date", "eq"]), name)


def finalize_curve(curve, name):
    if curve.empty:
        return {
            "name": name,
            "equity": curve,
            "ending_nav": 100000.0,
            "cagr": 0.0,
            "maxdd": 0.0,
            "sharpe": 0.0,
        }

    ending = float(curve.eq.iloc[-1])
    years = max((curve.date.iloc[-1] - curve.date.iloc[0]).days / 365.25, 1 / 365.25)
    cagr = (ending / 100000.0) ** (1 / years) - 1
    dd = float((curve.eq / curve.eq.cummax() - 1).min())
    r = curve.eq.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    sharpe = float(r.mean() / r.std(ddof=1) * math.sqrt(TD)) if r.std(ddof=1) > 0 else 0.0
    return {
        "name": name,
        "equity": curve,
        "ending_nav": ending,
        "cagr": cagr,
        "maxdd": dd,
        "sharpe": sharpe,
    }


def curve_metrics(base, qfilter, pair):
    b = base.set_index("date")
    q = qfilter.set_index("date")
    p = pair.set_index("date")
    ix = b.index.union(q.index).union(p.index)
    b = b.reindex(ix).ffill()
    q = q.reindex(ix).ffill()
    p = p.reindex(ix).ffill()

    qret = q.eq.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    pret = p.eq.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    brets = b.eq.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)

    worst = brets.nsmallest(max(1, int(len(brets) * 0.05))).index
    crash_capture = float((pret.loc[worst] - brets.loc[worst]).mean()) if len(worst) else 0.0
    qfilter_delta = float((pret.loc[worst] - qret.loc[worst]).mean()) if len(worst) else 0.0

    return {
        "pair_minus_qqq_cagr_pp": (p.eq.iloc[-1] / 100000.0) ** (1 / max((p.index[-1] - p.index[0]).days / 365.25, 1 / 365.25)) - 1
        - ((b.eq.iloc[-1] / 100000.0) ** (1 / max((b.index[-1] - b.index[0]).days / 365.25, 1 / 365.25)) - 1),
        "pair_minus_qqq_maxdd_pp": float(p.eq.div(p.eq.cummax()).sub(1).min() - b.eq.div(b.eq.cummax()).sub(1).min()),
        "pair_minus_activity_matched_qqq_cagr_pp": (p.eq.iloc[-1] / 100000.0) ** (1 / max((p.index[-1] - p.index[0]).days / 365.25, 1 / 365.25)) - 1
        - ((q.eq.iloc[-1] / 100000.0) ** (1 / max((q.index[-1] - q.index[0]).days / 365.25, 1 / 365.25)) - 1),
        "pair_minus_activity_matched_qqq_maxdd_pp": float(p.eq.div(p.eq.cummax()).sub(1).min() - q.eq.div(q.eq.cummax()).sub(1).min()),
        "crash_capture_vs_all_qqq_mean_daily_pp": crash_capture,
        "crash_capture_vs_activity_matched_qqq_mean_daily_pp": qfilter_delta,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--window", choices=["full", "oos", "late_oos"], default="full")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    qpath = str(Path(args.data_dir) / "QQQ_options.parquet")
    spath = str(Path(args.data_dir) / "SPY_options.parquet")
    qu = str(Path(args.data_dir) / "QQQ_underlying.parquet")
    su = str(Path(args.data_dir) / "SPY_underlying.parquet")
    for p in [qpath, spath, qu, su]:
        if not Path(p).exists():
            raise FileNotFoundError(p)

    con = duckdb.connect()
    base_state = build_state(con, qu, su)
    state = build_corr_state(con, qu, su, base_state)

    window_start = pd.Timestamp(START)
    window_end = pd.Timestamp(END)
    if args.window == "oos":
        window_start = pd.Timestamp("2022-01-03")
        state = state[state.date >= window_start].copy()
    elif args.window == "late_oos":
        window_start = pd.Timestamp("2024-01-02")
        state = state[state.entry_date >= window_start].copy()

    # QQQ-only broad benchmark.
    q_all_candidates, _, sig_all = build_candidates(
        con, state, qpath, spath, gated=False, name="QQQ_ONLY_ALL"
    )

    # The same qualification as the new gated pair, but QQQ-only, gives an
    # activity-matched counterfactual for isolating the SPY contribution.
    q_gate_candidates, _, sig_gate = build_candidates(
        con, state, qpath, spath, gated=True, name="QQQ_ONLY_ACTIVITY_MATCHED"
    )

    _, pair_base_candidates, sig_pair_base = build_candidates(
        con, state, qpath, spath, gated=False, name="PAIR_DYNAMIC3_BASE"
    )

    _, pair_gate_candidates, sig_pair_gate = build_candidates(
        con, state, qpath, spath, gated=True, name=NEW_POLICY
    )

    all_q = q_all_candidates
    all_q_filter = q_gate_candidates
    all_pairs = pair_base_candidates + pair_gate_candidates

    marks = load_marks_for_candidates(
        con, qpath, spath, all_q, all_pairs
    )

    valuation = load_px(con, qu, "Q")
    valuation = valuation[
        (valuation.date >= window_start)
        & (valuation.date <= window_end)
    ].date.tolist()

    q_all = run_q_only(
        con, state, marks, q_all_candidates, "QQQ_ONLY_ALL", valuation
    )
    q_filter = run_q_only(
        con, state, marks, q_gate_candidates, "QQQ_ONLY_ACTIVITY_MATCHED", valuation
    )
    pair_base = run_pair(
        con, state, marks, pair_base_candidates, "PAIR_DYNAMIC3_BASE", valuation
    )
    pair_gate = run_pair(
        con, state, marks, pair_gate_candidates, NEW_POLICY, valuation
    )

    metrics = {
        "window": args.window,
        "new_policy": NEW_POLICY,
        "policy_rule": "signal qualifies when QQQ RV60/QQQ ATM IV > 1 and SPY ATM IV30/SPY RV30 > 1; SPY funding is additionally allowed only when prior-day 60D QQQ/SPY realized correlation <= causal trailing 252-day median",
        "structure": {
            "QQQ": f"{Q_TARGET}D reverse iron condor, long {Q_LONG_DELTA:.2f} delta, short {Q_WING_DELTA:.2f} wings, exit {Q_EXIT_DTE}D",
            "SPY": f"{SPY_TARGET}D short iron condor, short 0.50 delta body, long {SPY_WING_DELTA:.2f} wings, exit 7D",
        },
        "pair_funding": f"1 QQQ convexity basket plus ceil(actual entry-day QQQ debit / actual entry-day SPY credit) SPY funding baskets, capped at {PAIR_CAP}x",
        "risk_budget": RISK_BUDGET,
        "data_provenance": {
            "QQQ_options_sha256": hash_file(Path(qpath)),
            "SPY_options_sha256": hash_file(Path(spath)),
            "QQQ_underlying_sha256": hash_file(Path(qu)),
            "SPY_underlying_sha256": hash_file(Path(su)),
        },
        "family_not_virgin": True,
        "why_not_virgin": "QQQ/SPY option structure family was previously explored in self-financing/relative-range research; this run tests a new causal correlation-veto policy rather than claiming a virgin structure discovery.",
        "counts": {
            "signals": int(len(sig_pair_base)),
            "base_pair_entries": int(len(pair_base_candidates)),
            "gated_pair_entries": int(len(pair_gate_candidates)),
            "base_gate_on_rate": float(sig_pair_gate.corr_gate_ok.mean()) if not sig_pair_gate.empty else np.nan,
            "gated_skipped_vs_base": int(max(0, len(pair_base_candidates) - len(pair_gate_candidates))),
        },
        "headline": {
            "QQQ_ONLY_ALL": {k: q_all[k] for k in ["ending_nav", "cagr", "maxdd", "sharpe"]},
            "QQQ_ONLY_ACTIVITY_MATCHED": {k: q_filter[k] for k in ["ending_nav", "cagr", "maxdd", "sharpe"]},
            "PAIR_DYNAMIC3_BASE": {k: pair_base[k] for k in ["ending_nav", "cagr", "maxdd", "sharpe"]},
            NEW_POLICY: {k: pair_gate[k] for k in ["ending_nav", "cagr", "maxdd", "sharpe"]},
        },
        "incremental_value": {
            "base": curve_metrics(q_all["equity"], q_filter["equity"], pair_base["equity"]),
            "gated": curve_metrics(q_all["equity"], q_filter["equity"], pair_gate["equity"]),
        },
        "guardrails": {
            "no_live_orders": True,
            "no_parameter_search": True,
            "research_only": True,
        },
    }

    pd.DataFrame(sig_all).to_csv(out / "signals_qqq_all.csv", index=False)
    pd.DataFrame(sig_gate).to_csv(out / "signals_activity_matched.csv", index=False)
    pd.DataFrame(sig_pair_base).to_csv(out / "signals_pair_base.csv", index=False)
    pd.DataFrame(sig_pair_gate).to_csv(out / "signals_pair_gate.csv", index=False)

    for x in [q_all, q_filter, pair_base, pair_gate]:
        x["equity"].to_csv(out / f"equity_{x['name'].lower()}.csv", index=False)

    (out / "RESULTS.json").write_text(
        json.dumps(metrics, indent=2, allow_nan=True), encoding="utf-8"
    )

    trial_ledger = {
        "protocol_version": "qqq-spy-incremental-funding-correlation-v1",
        "purpose": "test incremental QQQ convexity value contributed by a self-financing SPY sleeve, and whether a causal correlation veto improves that incremental value",
        "research_only": True,
        "selection_status": "LOCKED_FOR_COMPARISON",
        "virgin_oos": False,
        "why_not_virgin": metrics["family_not_virgin"],
        "windows_in_protocol": ["full", "oos", "late_oos"],
        "variants_in_protocol": [
            "QQQ_ONLY_ALL",
            "QQQ_ONLY_ACTIVITY_MATCHED",
            "PAIR_DYNAMIC3_BASE",
            NEW_POLICY,
        ],
        "total_variant_window_cells": 12,
        "primary_comparison": "PAIR_DYNAMIC3_BASE vs PAIR_DYNAMIC3_CORRELATION_MEDIAN_VETO",
        "incremental_control": "PAIR variant vs QQQ_ONLY_ACTIVITY_MATCHED on identical final eligibility dates",
        "new_policy_rule": metrics["policy_rule"],
        "trial_count_is_factual_not_selective": True,
        "no_parameter_search": True,
        "no_live_orders": True,
        "do_not_select_winner_from_oos": True,
    }
    (out / "TRIAL_LEDGER.json").write_text(
        json.dumps(trial_ledger, indent=2), encoding="utf-8"
    )

    lines = [
        f"# QQQ-SPY Incremental Funding / Correlation Veto — {args.window.upper()}",
        "",
        "Question: does SPY add value to QQQ convexity, and does a causal correlation veto improve that value?",
        "",
        "| variant | CAGR | MaxDD | Sharpe | ending NAV |",
        "|---|---:|---:|---:|---:|",
    ]
    for nm, r in metrics["headline"].items():
        lines.append(
            f"| {nm} | {r['cagr']:.2%} | {r['maxdd']:.2%} | {r['sharpe']:.2f} | {r['ending_nav']:.2f} |"
        )
    lines += [
        "",
        "Incremental comparisons (pair minus QQQ) are reported separately from absolute performance.",
        "The activity-matched QQQ control uses the same pair eligibility dates, isolating the incremental contribution of the SPY leg.",
        "Crash capture vs activity-matched QQQ is pair minus activity-matched QQQ on the worst 5% QQQ-only daily-return dates.",
        "",
        "The correlation veto is a state filter, not a return predictor; external research rationale is documented separately from the executable artifact.",
        "This run is research-only and the structure family is not virgin OOS.",
    ]
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
