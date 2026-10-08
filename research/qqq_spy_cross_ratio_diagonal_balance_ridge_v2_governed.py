from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_spy_cross_ratio_diagonal_balance_ridge_v1 import (
    NAV0,
    LONG_DTES,
    SHORT_DTES,
    TARGET_LONG_DELTA,
    TARGET_SHORT_DELTA,
    MAX_N,
    HEDGE_LOOKBACK,
    MIN_HEDGE_SAMPLES,
    THETA_TOL,
    START,
    END,
    weekly_dates,
    get_spot_map,
    build_factor_history,
    covariance_for_date,
    choose_integer_n,
    preselect_calls,
    load_marks,
    simulate_config,
)

FAMILIES = [
    ("SPY", "SPY"),
    ("QQQ", "QQQ"),
    ("SPY", "QQQ"),
    ("QQQ", "SPY"),
]
CANONICAL_BASE_COMMIT = "8c4027fdea1d4077960726b7ba8c2cd544dd9d0e"


def build_configs(orientation: str) -> list[tuple[str, str, int, int]]:
    configs: list[tuple[str, str, int, int]] = []
    if orientation in ("normal", "both"):
        for la, sa in FAMILIES:
            for ld in LONG_DTES:
                for sd in SHORT_DTES:
                    configs.append((la, sa, ld, sd))
    if orientation in ("reverse", "both"):
        for la, sa in FAMILIES:
            for ld in SHORT_DTES:
                for sd in LONG_DTES:
                    configs.append((la, sa, ld, sd))
    return configs


def source_hash(fn) -> str:
    return hashlib.sha256(inspect.getsource(fn).encode("utf-8")).hexdigest()


def audit_protocol() -> dict:
    normal = build_configs("normal")
    reverse = build_configs("reverse")
    both = build_configs("both")
    if len(normal) != 32 or len(reverse) != 32 or len(both) != 64:
        raise AssertionError(
            f"unexpected config universe: normal={len(normal)} reverse={len(reverse)} both={len(both)}"
        )
    if len(set(both)) != len(both):
        raise AssertionError("duplicate configs in canonical universe")

    # Blind causality test: adding arbitrary future observations must not alter
    # a covariance computed for an earlier date because the canonical function
    # explicitly filters hist.date < d.
    base = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-05", "2024-01-12", "2024-01-19", "2024-01-26", "2024-02-02", "2024-02-09",
                 "2024-02-16", "2024-02-23", "2024-03-01", "2024-03-08", "2024-03-15", "2024-03-22"]
            ),
            "q_ret": np.linspace(-0.02, 0.02, 12),
            "s_ret": np.linspace(0.015, -0.015, 12),
            "dq_iv": np.linspace(0.01, -0.01, 12),
            "ds_iv": np.linspace(-0.01, 0.01, 12),
            "q_div": np.linspace(0.0001, 0.0008, 12),
            "s_div": np.linspace(0.0002, 0.0007, 12),
        }
    )
    target_date = pd.Timestamp("2024-03-15")
    c1 = covariance_for_date(base, target_date)
    future = base.copy()
    future_rows = future.iloc[-3:].copy()
    future_rows["date"] = pd.to_datetime(
        ["2027-01-01", "2027-01-08", "2027-01-15"]
    )
    future_rows[["q_ret", "s_ret", "dq_iv", "ds_iv"]] = 1000.0
    future = pd.concat([future, future_rows], ignore_index=True)
    c2 = covariance_for_date(future, target_date)
    np.testing.assert_allclose(c1, c2, rtol=0.0, atol=0.0)

    # N must stay within the frozen integer universe.
    long_e = {"vec": np.array([1.0, 0, 0, 0, 0, 0]), "theta": 0.1, "delta_dollar": 1.0}
    short_e = {"vec": np.array([0.1, 0, 0, 0, 0, 0]), "theta": -0.001, "delta_dollar": 0.1}
    r = choose_integer_n(long_e, short_e, np.eye(6), exposure_side=-1)
    if not (1 <= int(r["n_balanced"]) <= MAX_N):
        raise AssertionError(f"N escaped frozen range: {r['n_balanced']}")

    return {
        "audit": "PASS",
        "canonical_base_commit": CANONICAL_BASE_COMMIT,
        "strategy_rules_changed": False,
        "no_parameter_search": True,
        "no_live_orders": True,
        "config_counts": {
            "normal": len(normal),
            "reverse": len(reverse),
            "both": len(both),
        },
        "frozen_parameters": {
            "long_dtes": LONG_DTES,
            "short_dtes": SHORT_DTES,
            "long_delta": TARGET_LONG_DELTA,
            "short_delta": TARGET_SHORT_DELTA,
            "max_n": MAX_N,
            "hedge_lookback": HEDGE_LOOKBACK,
            "min_hedge_samples": MIN_HEDGE_SAMPLES,
            "theta_tol": THETA_TOL,
        },
        "canonical_function_hashes": {
            "preselect_calls": source_hash(preselect_calls),
            "simulate_config": source_hash(simulate_config),
            "choose_integer_n": source_hash(choose_integer_n),
            "covariance_for_date": source_hash(covariance_for_date),
        },
        "checks": [
            "normal/reverse configuration universe is exact and duplicate-free",
            "future-data injection does not change causal covariance",
            "integer N remains within frozen 1..MAX_N",
        ],
    }


def worker_run(args):
    prep_path, configs, worker_index = args
    with open(prep_path, "rb") as fh:
        prep = pickle.load(fh)

    results = []
    curves = []
    balances = []
    t0 = time.perf_counter()

    for la, sa, ld, sd in configs:
        rr, eq, br = simulate_config(
            None,
            None,
            None,
            prep["qspots"],
            prep["sspots"],
            prep["dates"],
            prep["hist"],
            prep["covariance_cache"],
            prep["selector"],
            prep["mark_maps"],
            la,
            sa,
            ld,
            sd,
        )
        if rr is None:
            continue
        strategy = f"{la}_LONG1__{sa}_SHORTN__L{ld}D__S{sd}D"
        rr["strategy"] = strategy
        rr["orientation"] = prep["orientation"]
        rr["worker_index"] = worker_index
        results.append(rr)

        eq["strategy"] = strategy
        eq["orientation"] = prep["orientation"]
        eq["worker_index"] = worker_index
        curves.append(eq)

        if not br.empty:
            br["strategy"] = strategy
            br["orientation"] = prep["orientation"]
            br["worker_index"] = worker_index
            balances.append(br)

    return {
        "worker_index": worker_index,
        "config_count": len(configs),
        "seconds": time.perf_counter() - t0,
        "results": results,
        "curves": curves,
        "balances": balances,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--orientation", choices=["normal", "reverse", "both"], default="both")
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--audit-only", action="store_true")
    a = ap.parse_args()

    audit = audit_protocol()
    if a.audit_only:
        print(json.dumps(audit, indent=2))
        return

    if not a.data_dir:
        raise ValueError("--data-dir is required unless --audit-only is used")
    workers = a.workers or min(5, max(1, os.cpu_count() or 1))
    if workers < 1:
        raise ValueError("--workers must be >= 1")

    data = Path(a.data_dir)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    qpath = str(data / "QQQ_options.parquet")
    spath = str(data / "SPY_options.parquet")
    qu = str(data / "QQQ_underlying.parquet")
    su = str(data / "SPY_underlying.parquet")
    for p in [qpath, spath, qu, su]:
        if not Path(p).exists():
            raise FileNotFoundError(p)

    con = duckdb.connect()
    t0 = time.perf_counter()

    configs = build_configs(a.orientation)
    dates = weekly_dates(con, su)
    qspots = get_spot_map(con, qu)
    sspots = get_spot_map(con, su)
    hist = build_factor_history(con, qu, su, qpath, spath, dates)

    covariance_cache = {
        pd.Timestamp(d): covariance_for_date(hist, pd.Timestamp(d))
        for d in dates
    }

    selector = preselect_calls(con, {"QQQ": qpath, "SPY": spath}, dates)
    ids_by_asset = {"QQQ": set(), "SPY": set()}
    for (asset, _, _, _), opt in selector.items():
        ids_by_asset[asset].add(opt["contract_id"])
    mark_maps = {
        asset: load_marks(
            con,
            {"QQQ": qpath, "SPY": spath}[asset],
            sorted(ids_by_asset[asset]),
        )
        for asset in ids_by_asset
    }
    t_prep = time.perf_counter()

    prep_path = out / "PREP_CACHE.pkl"
    with open(prep_path, "wb") as fh:
        pickle.dump(
            {
                "orientation": a.orientation,
                "dates": dates,
                "qspots": qspots,
                "sspots": sspots,
                "hist": hist,
                "covariance_cache": covariance_cache,
                "selector": selector,
                "mark_maps": mark_maps,
            },
            fh,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    chunks = [configs[i::workers] for i in range(workers)]
    chunks = [c for c in chunks if c]
    jobs = [(str(prep_path), chunk, i) for i, chunk in enumerate(chunks)]

    worker_results = []
    with ProcessPoolExecutor(max_workers=len(chunks)) as pool:
        for result in pool.map(worker_run, jobs):
            worker_results.append(result)

    t_sim = time.perf_counter()

    results = []
    curves = []
    balances = []
    worker_timings = []
    for wr in worker_results:
        results.extend(wr["results"])
        curves.extend(wr["curves"])
        balances.extend(wr["balances"])
        worker_timings.append(
            {"worker_index": wr["worker_index"], "config_count": wr["config_count"], "seconds": round(wr["seconds"], 3)}
        )

    res = pd.DataFrame(results)
    if not res.empty:
        res = res.sort_values(["orientation", "long_asset", "short_asset", "long_dte", "short_dte"])
    res.to_csv(out / "results.csv", index=False)
    if curves:
        pd.concat(curves, ignore_index=True).to_csv(out / "equity.csv", index=False)
    if balances:
        pd.concat(balances, ignore_index=True).to_csv(out / "balance_points.csv", index=False)

    # Research protocol summary: this is evidence about the execution layer,
    # not a claim that the strategy has alpha.
    methodology = {
        "name": "QQQ-SPY Cross-Underlying Ratio-Diagonal Balance Ridge V2 — Governed Parallel Replay",
        "research_live_boundary": "RESEARCH_ONLY",
        "strategy_rules_changed": False,
        "no_parameter_search": True,
        "no_live_orders": True,
        "canonical_base_commit": CANONICAL_BASE_COMMIT,
        "canonical_strategy_source": "research/qqq_spy_cross_ratio_diagonal_balance_ridge_v1.py",
        "orientation": a.orientation,
        "config_count": len(configs),
        "families": [list(x) for x in FAMILIES],
        "execution_model": "ONE_PREP_MANY_PROCESS_WORKERS",
        "workers": len(chunks),
        "worker_config_counts": [len(c) for c in chunks],
        "frozen_parameters": audit["frozen_parameters"],
        "canonical_function_hashes": audit["canonical_function_hashes"],
        "data_provenance": {
            "option_files": ["QQQ_options.parquet", "SPY_options.parquet"],
            "underlying_files": ["QQQ_underlying.parquet", "SPY_underlying.parquet"],
            "start": START,
            "end": END,
            "weekly_observation_count": len(dates),
        },
        "runtime_seconds": {
            "prepare": round(t_prep - t0, 3),
            "parallel_simulation_wall": round(t_sim - t_prep, 3),
            "total_before_reporting": round(t_sim - t0, 3),
        },
        "worker_timings": worker_timings,
        "audit": audit,
    }
    (out / "METHODOLOGY.json").write_text(
        json.dumps(methodology, indent=2), encoding="utf-8"
    )

    lines = [
        f"# QQQ-SPY Cross-Underlying Ratio-Diagonal Balance Ridge V2 — {a.orientation.upper()}",
        "",
        "Governed execution replay. Strategy rules remain delegated to the canonical V1 implementation.",
        "Execution model: one preparation phase, then multiple process workers over disjoint configuration chunks.",
        "",
        f"- Configs: {len(configs)}",
        f"- Workers: {len(chunks)}",
        f"- Prepare: {t_prep - t0:.2f}s",
        f"- Simulation wall: {t_sim - t_prep:.2f}s",
        f"- Total before reporting: {t_sim - t0:.2f}s",
        "",
        "| long | short | L-DTE | S-DTE | points | mean N-delta | mean N-MV | mean N-balanced | CAGR | MaxDD | Sharpe | theta feasible |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in res.iterrows():
        lines.append(
            f"| {r.long_asset} | {r.short_asset} | {int(r.long_dte)} | {int(r.short_dte)} | "
            f"{int(r.rebalance_points)} | {r.mean_n_delta:.2f} | {r.mean_n_mv:.2f} | "
            f"{r.mean_n_balanced:.2f} | {r.cagr:.2%} | {r.maxdd:.2%} | "
            f"{r.sharpe:.2f} | {r.theta_feasible_pct:.1%} |"
        )

    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Workers: {len(chunks)}")
    print(f"Prepare seconds: {t_prep - t0:.3f}")
    print(f"Simulation wall seconds: {t_sim - t_prep:.3f}")
    print(f"Total seconds: {t_sim - t0:.3f}")


if __name__ == "__main__":
    main()
