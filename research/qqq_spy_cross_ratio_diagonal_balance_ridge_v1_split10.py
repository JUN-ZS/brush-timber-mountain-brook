from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
import sys

import duckdb
import numpy as np
import pandas as pd

# The canonical strategy implementation stays untouched. This wrapper only
# partitions the already-defined configuration universe into execution shards.
from qqq_spy_cross_ratio_diagonal_balance_ridge_v1 import (
    NAV0,
    LONG_DTES,
    SHORT_DTES,
    TARGET_LONG_DELTA,
    TARGET_SHORT_DELTA,
    MAX_N,
    START,
    END,
    weekly_dates,
    get_spot_map,
    build_factor_history,
    covariance_for_date,
    option_exposure,
    choose_integer_n,
    make_position,
    load_marks,
    simulate_config,
)

FAMILIES = [
    ("SPY", "SPY"),
    ("QQQ", "QQQ"),
    ("SPY", "QQQ"),
    ("QQQ", "SPY"),
]


def sql(con, s):
    return con.execute(s).df()


def pathq(p):
    return str(p).replace("'", "''")


def build_configs(orientation):
    configs = []
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


def preselect_calls_subset(con, option_paths, dates, configs):
    """Canonical call-selection rules, restricted to contracts actually needed
    by this shard. Ranking/filtering is identical to the source strategy.
    """
    needed = {asset: set() for asset in option_paths}
    for la, sa, ld, sd in configs:
        needed[la].add((int(ld), float(TARGET_LONG_DELTA)))
        needed[sa].add((int(sd), float(TARGET_SHORT_DELTA)))

    out = {}
    for asset, path in option_paths.items():
        targets = sorted(needed.get(asset, set()))
        if not targets:
            continue
        values_sql = ",".join(
            f"({int(td)}, {float(delta):.8f})" for td, delta in targets
        )
        q = sql(
            con,
            f"""
            WITH target_specs(target_dte, target_delta) AS (
                VALUES {values_sql}
            ),
            target_dates AS (
                SELECT CAST(v AS DATE) AS date
                FROM unnest([
                    {",".join("DATE '" + pd.Timestamp(d).strftime("%Y-%m-%d") + "'" for d in sorted(dates))}
                ]) AS t(v)
            ),
            targets AS (
                SELECT d.date, s.target_dte, s.target_delta
                FROM target_dates d
                CROSS JOIN target_specs s
            ),
            eligible AS (
                SELECT
                    CAST(o.contract_id AS VARCHAR) AS contract_id,
                    CAST(o.date AS DATE) AS date,
                    CAST(o.expiration AS DATE) AS expiration,
                    CAST(o.strike AS DOUBLE) AS strike,
                    CAST(o.bid AS DOUBLE) AS bid,
                    CAST(o.ask AS DOUBLE) AS ask,
                    CAST(o.delta AS DOUBLE) AS delta,
                    CAST(o.implied_volatility AS DOUBLE) AS iv,
                    t.target_dte,
                    t.target_delta,
                    date_diff(
                        'day',
                        CAST(o.date AS DATE),
                        CAST(o.expiration AS DATE)
                    ) AS dte_calc,
                    (CAST(o.ask AS DOUBLE) - CAST(o.bid AS DOUBLE))
                    / NULLIF(
                        (CAST(o.ask AS DOUBLE) + CAST(o.bid AS DOUBLE)) / 2.0,
                        0
                    ) AS spr
                FROM read_parquet('{pathq(path)}') o
                JOIN targets t
                  ON CAST(o.date AS DATE) = t.date
                WHERE LOWER(o."type") = 'call'
                  AND CAST(o.expiration AS DATE) > CAST(o.date AS DATE)
                  AND date_diff(
                        'day',
                        CAST(o.date AS DATE),
                        CAST(o.expiration AS DATE)
                      ) >= GREATEST(2, t.target_dte - 7)
                  AND date_diff(
                        'day',
                        CAST(o.date AS DATE),
                        CAST(o.expiration AS DATE)
                      ) <= t.target_dte + 7
                  AND o.bid IS NOT NULL
                  AND o.ask IS NOT NULL
                  AND o.ask >= o.bid
                  AND o.ask > 0
                  AND o.delta IS NOT NULL
                  AND (o.open_interest >= 10 OR o.volume >= 5)
            ),
            liquid AS (
                SELECT *
                FROM eligible
                WHERE isfinite(spr)
                  AND spr <= 0.35
            ),
            ranked AS (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY date, target_dte, target_delta
                           ORDER BY ABS(delta - target_delta),
                                    expiration,
                                    strike,
                                    contract_id
                       ) AS rn
                FROM liquid
                WHERE iv IS NOT NULL
            )
            SELECT contract_id, date, expiration, strike, bid, ask, delta, iv,
                   dte_calc, target_dte, target_delta
            FROM ranked
            WHERE rn = 1
            ORDER BY date, target_dte, target_delta
            """,
        )
        for row in q.itertuples(index=False):
            iv = float(row.iv)
            if not np.isfinite(iv) or iv <= 0:
                continue
            out[
                (
                    asset,
                    pd.Timestamp(row.date),
                    int(row.target_dte),
                    float(row.target_delta),
                )
            ] = {
                "contract_id": str(row.contract_id),
                "expiry": pd.Timestamp(row.expiration),
                "strike": float(row.strike),
                "iv": iv,
                "delta": float(row.delta),
                "bid": float(row.bid),
                "ask": float(row.ask),
                "dte": int(row.dte_calc),
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--orientation", choices=["normal", "reverse"], required=True)
    ap.add_argument("--shard-index", type=int, required=True)
    ap.add_argument("--shard-count", type=int, required=True)
    a = ap.parse_args()

    if not (0 <= a.shard_index < a.shard_count):
        raise ValueError("shard-index must be in [0, shard-count)")
    if a.shard_count <= 0:
        raise ValueError("shard-count must be positive")

    d = Path(a.data_dir)
    o = Path(a.out)
    o.mkdir(parents=True, exist_ok=True)

    qpath = str(d / "QQQ_options.parquet")
    spath = str(d / "SPY_options.parquet")
    qu = str(d / "QQQ_underlying.parquet")
    su = str(d / "SPY_underlying.parquet")
    for p in [qpath, spath, qu, su]:
        if not Path(p).exists():
            raise FileNotFoundError(p)

    con = duckdb.connect()
    t0 = time.perf_counter()

    full_configs = build_configs(a.orientation)
    n_full = len(full_configs)
    lo = (n_full * a.shard_index) // a.shard_count
    hi = (n_full * (a.shard_index + 1)) // a.shard_count
    configs = full_configs[lo:hi]
    if not configs:
        raise RuntimeError(f"empty shard {a.shard_index}/{a.shard_count}")

    dates = weekly_dates(con, su)
    qspots = get_spot_map(con, qu)
    sspots = get_spot_map(con, su)
    hist = build_factor_history(con, qu, su, qpath, spath, dates)
    hist.to_csv(o / "factor_history.csv", index=False)
    t_factor = time.perf_counter()

    covariance_cache = {
        pd.Timestamp(x): covariance_for_date(hist, pd.Timestamp(x))
        for x in dates
    }

    option_paths = {"QQQ": qpath, "SPY": spath}
    selector = preselect_calls_subset(con, option_paths, dates, configs)
    t_selector = time.perf_counter()

    ids_by_asset = {"QQQ": set(), "SPY": set()}
    for (asset, _, _, _), opt in selector.items():
        ids_by_asset[asset].add(opt["contract_id"])
    mark_maps = {
        asset: load_marks(con, option_paths[asset], sorted(ids))
        for asset, ids in ids_by_asset.items()
    }
    t_marks = time.perf_counter()

    results = []
    curves = []
    balances = []
    for la, sa, ld, sd in configs:
        rr, eq, br = simulate_config(
            con,
            qpath,
            spath,
            qspots,
            sspots,
            dates,
            hist,
            covariance_cache,
            selector,
            mark_maps,
            la,
            sa,
            ld,
            sd,
        )
        if rr is None:
            continue
        strategy = f"{la}_LONG1__{sa}_SHORTN__L{ld}D__S{sd}D"
        rr["strategy"] = strategy
        rr["orientation"] = a.orientation
        rr["shard_index"] = a.shard_index
        rr["shard_count"] = a.shard_count
        results.append(rr)
        eq["strategy"] = strategy
        eq["orientation"] = a.orientation
        eq["shard_index"] = a.shard_index
        curves.append(eq)
        if not br.empty:
            br["strategy"] = strategy
            br["orientation"] = a.orientation
            br["shard_index"] = a.shard_index
            balances.append(br)

    t_sim = time.perf_counter()

    res = pd.DataFrame(results)
    if not res.empty:
        res = res.sort_values(
            ["long_asset", "short_asset", "long_dte", "short_dte"]
        )
    res.to_csv(o / "results.csv", index=False)

    if curves:
        pd.concat(curves, ignore_index=True).to_csv(o / "equity.csv", index=False)
    else:
        pd.DataFrame(columns=["date", "eq", "strategy"]).to_csv(
            o / "equity.csv", index=False
        )

    if balances:
        pd.concat(balances, ignore_index=True).to_csv(
            o / "balance_points.csv", index=False
        )
    else:
        pd.DataFrame().to_csv(o / "balance_points.csv", index=False)

    methodology = {
        "name": "QQQ-SPY Cross-Underlying Ratio-Diagonal Balance Ridge V1",
        "execution_only_split": True,
        "strategy_source": "research/qqq_spy_cross_ratio_diagonal_balance_ridge_v1.py",
        "strategy_rules_changed": False,
        "orientation": a.orientation,
        "full_config_count": n_full,
        "shard_count": a.shard_count,
        "shard_index": a.shard_index,
        "shard_config_start": lo,
        "shard_config_end_exclusive": hi,
        "shard_config_count": len(configs),
        "configs": [list(x) for x in configs],
        "normal_time_orientation": "long far 90/180D, short near 7/14/21/30D",
        "reverse_time_orientation": "long near 7/14/21/30D, short far 90/180D",
        "long_delta": TARGET_LONG_DELTA,
        "short_delta": TARGET_SHORT_DELTA,
        "N_range": [1, MAX_N],
        "non_negative_theta_constraint": True,
        "weekly_rebalance": True,
        "bid_ask_fills": True,
        "daily_midpoint_mtm": True,
        "no_live_orders": True,
        "no_parameter_search": True,
        "runtime_seconds": {
            "factor_history_and_calendar": round(t_factor - t0, 3),
            "option_selection_subset": round(t_selector - t_factor, 3),
            "historical_mark_cache": round(t_marks - t_selector, 3),
            "strategy_valuation": round(t_sim - t_marks, 3),
            "total_before_reporting": round(t_sim - t0, 3),
        },
    }
    (o / "METHODOLOGY.json").write_text(
        json.dumps(methodology, indent=2), encoding="utf-8"
    )

    lines = [
        f"# Cross-Ratio-Diagonal Ridge — {a.orientation.upper()} — "
        f"Shard {a.shard_index + 1}/{a.shard_count}",
        "",
        f"Execution shard contains configs {lo}..{hi - 1} of {n_full}.",
        "This is an execution partition only; the canonical strategy rules are unchanged.",
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
    (o / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
