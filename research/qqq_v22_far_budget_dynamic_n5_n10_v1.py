#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import qqq_dynamic_near_long_state_engine_v22_930c949 as v22

FROZEN_ENGINE_BLOB = "1fb0464b59c0d7d734007d44f675c610d3033d49"
FAR_DTE = 120
FAR_DELTA = 0.08
NEAR_DTE = 30
COVERAGE_MULT = 1.50
POLICY = "TP50_IMMEDIATE"
N_VALUES = (10, 5)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def valid_chain(g: pd.DataFrame, spot: float) -> pd.DataFrame:
    z = g[
        (g.strike > float(spot))
        & g.bid.notna()
        & g.ask.notna()
        & g.delta.notna()
        & (g.ask >= g.bid)
        & (g.bid >= 0)
    ].copy()
    if z.empty:
        return z
    z["dte"] = (z.expiration - z.date).dt.days
    return z[(z.dte >= 60) & (z.dte <= 210)].copy()


def choose_expiration(z: pd.DataFrame, dte_target: int) -> pd.Timestamp | None:
    if z.empty:
        return None
    exp_score = z.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"),
        volume=("volume", "sum"),
    )
    exp_score["err"] = (exp_score.dte - dte_target).abs()
    return pd.Timestamp(
        exp_score.sort_values(["err", "volume"], ascending=[True, False])
        .iloc[0]
        .expiration
    )


def far_candidate_from_row(r) -> dict:
    out = {
        "cid": str(r.contract_id),
        "strike": float(r.strike),
        "delta": float(r.delta),
        "expiry": pd.Timestamp(r.expiration),
        "entry_bid": float(r.bid),
        "entry_ask": float(r.ask),
    }
    if "gamma" in r.index and pd.notna(r["gamma"]):
        out["gamma"] = float(r["gamma"])
    return out


def build_budget_dynamic_far(
    u: pd.DataFrame,
    con,
    opt_path: Path,
    baseline: dict,
    n_short: int,
) -> tuple[dict, pd.DataFrame]:
    sigdates = [pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(), "date"]]
    if not sigdates:
        raise RuntimeError("No signal dates")

    has_gamma = "gamma" in v22.option_columns(con, opt_path)
    gamma_select = ', CAST("gamma" AS DOUBLE) AS gamma' if has_gamma else ""

    ch = v22.read_options(
        con,
        opt_path,
        f"""
        SELECT CAST(date AS DATE) AS date,
               CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               COALESCE(CAST(volume AS DOUBLE),0) AS volume,
               CAST(delta AS DOUBLE) AS delta
               {gamma_select}
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER("type")='CALL'
          AND delta IS NOT NULL
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask >= bid AND bid >= 0
          AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 60 DAY
                                            AND CAST(date AS DATE)+INTERVAL 210 DAY
        """,
        [[d.date() for d in sigdates]],
    )
    if ch.empty:
        raise RuntimeError("No far option rows on signal dates")

    ch["date"] = pd.to_datetime(ch.date)
    ch["expiration"] = pd.to_datetime(ch.expiration)

    out = {}
    audit = []

    for d0, g in ch.groupby("date", sort=False):
        spot = float(u.loc[u.date == d0, "close"].iloc[0])
        base = baseline.get(d0, {}).get((FAR_DTE, FAR_DELTA))
        if base is None:
            continue

        z = valid_chain(g, spot)
        ex = choose_expiration(z, FAR_DTE)
        if ex is None:
            continue
        z = z[z.expiration == ex].copy()
        if z.empty:
            continue

        target_total = float(base["entry_bid"]) * float(v22.N_SHORT) * 100.0
        target_each = target_total / float(n_short * 100.0)

        # Core rule:
        # choose the FARTEST OTM strike on the same DTE bucket whose entry
        # premium still funds the same total dollar target as 10 x baseline 8Δ.
        eligible = z[z.bid >= target_each].copy()
        fallback = False
        if not eligible.empty:
            eligible = eligible.sort_values(
                ["strike", "volume", "delta"],
                ascending=[False, False, True],
            )
            r = eligible.iloc[0]
        else:
            # No OTM contract reaches the budget target. Keep the same expiry
            # and choose the highest-premium OTM contract; record the shortfall.
            fallback = True
            r = z.sort_values(["bid", "volume", "strike"], ascending=[False, False, True]).iloc[0]

        leg = far_candidate_from_row(r)
        actual_total = float(leg["entry_bid"]) * float(n_short) * 100.0
        audit.append(
            {
                "date": str(pd.Timestamp(d0).date()),
                "n_short": n_short,
                "baseline_strike": float(base["strike"]),
                "baseline_delta_abs": abs(float(base["delta"])),
                "baseline_entry_bid": float(base["entry_bid"]),
                "target_total_premium_usd": target_total,
                "target_per_contract_premium": target_each,
                "selected_strike": float(leg["strike"]),
                "selected_delta_abs": abs(float(leg["delta"])),
                "selected_entry_bid": float(leg["entry_bid"]),
                "selected_total_premium_usd": actual_total,
                "premium_gap_usd": actual_total - target_total,
                "distance_pct": (float(leg["strike"]) - spot) / spot,
                "baseline_distance_pct": (float(base["strike"]) - spot) / spot,
                "fallback_shortfall": fallback,
                "expiry": str(pd.Timestamp(leg["expiry"]).date()),
            }
        )
        out.setdefault(pd.Timestamp(d0), {})[(FAR_DTE, FAR_DELTA)] = leg

    return out, pd.DataFrame(audit)


def build_near_chains(u, con, opt_path, far_maps):
    event_dates = set()
    for fmap in far_maps:
        for d0, legs in fmap.items():
            event_dates.add(pd.Timestamp(d0))
            for leg in legs.values():
                if leg:
                    end = min(pd.Timestamp(leg["expiry"]), d0 + pd.Timedelta(days=365))
                    event_dates.update(
                        pd.Timestamp(x)
                        for x in u[(u.date >= d0) & (u.date <= end)].date
                    )
    event_dates = sorted(event_dates)

    near = v22.read_options(
        con,
        opt_path,
        """
        SELECT CAST(date AS DATE) AS date,
               CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               COALESCE(CAST(volume AS DOUBLE),0) AS volume,
               CAST(delta AS DOUBLE) AS delta
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER("type")='CALL'
          AND delta IS NOT NULL
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask >= bid AND bid >= 0
          AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 7 DAY
                                            AND CAST(date AS DATE)+INTERVAL 35 DAY
        """,
        [[d.date() for d in event_dates]],
    )
    if near.empty:
        raise RuntimeError("No near option rows")

    near["date"] = pd.to_datetime(near.date)
    near["expiration"] = pd.to_datetime(near.expiration)
    near_chains = {d: g for d, g in near.groupby("date", sort=False)}

    near_ids = set()
    for d, ch in near_chains.items():
        spot_row = u.loc[u.date == d, "close"]
        if spot_row.empty:
            continue
        spot = float(spot_row.iloc[0])
        leg = v22.pick_near(ch, spot, NEAR_DTE)
        if leg:
            near_ids.add(leg["cid"])

    return near_chains, near_ids, event_dates


def summarize_case(name, df, audit):
    if df.empty:
        return {
            "case": name,
            "campaigns": 0,
            "total_pnl_usd": float("nan"),
        }

    far_entry = float(df.far_entry_premium_usd.sum())
    return {
        "case": name,
        "campaigns": int(len(df)),
        "total_pnl_usd": float(df.total_pnl_usd.sum()),
        "far_pnl_usd": float(df.far_pnl_usd.sum()),
        "near_realized_pnl_usd": float(df.near_realized_pnl_usd.sum()),
        "avg_campaign_pnl_usd": float(df.total_pnl_usd.mean()),
        "median_campaign_pnl_usd": float(df.total_pnl_usd.median()),
        "worst_campaign_pnl_usd": float(df.total_pnl_usd.min()),
        "mean_campaign_maxdd": float(df.maxdd.mean()),
        "worst_campaign_maxdd": float(df.maxdd.min()),
        "near_trade_count": int(df.near_trades.sum()),
        "near_win_rate": float(df.long_wins.sum() / max(1, df.long_wins.sum() + df.long_losses.sum())),
        "avg_near_opens": float(df.near_open_count.mean()),
        "avg_final_stack": float(df.final_stack.mean()),
        "state_increases": int(df.state_increases.sum()),
        "state_decreases": int(df.state_decreases.sum()),
        "far_entry_premium_sum_usd": far_entry,
        "audit_rows": int(len(audit)),
    }




def simulate_forced_entry(
    u,
    entry_date,
    far_candidates,
    near_chains,
    far_quotes_by_cid,
    near_quotes_by_cid,
    n_short,
    has_gamma,
):
    # Run the frozen simulator one campaign at a time so every case is forced
    # onto the exact same entry-date set. Future observations remain available
    # for path evolution; only the entry signal mask is restricted.
    u_one = u.copy()
    u_one["signal"] = False
    u_one.loc[u_one.date == pd.Timestamp(entry_date), "signal"] = True
    v22.N_SHORT = n_short
    return v22.simulate(
        u=u_one,
        far_candidates=far_candidates,
        near_chains=near_chains,
        far_quotes_by_cid=far_quotes_by_cid,
        near_quotes_by_cid=near_quotes_by_cid,
        far_dte=FAR_DTE,
        far_delta=FAR_DELTA,
        near_dte=NEAR_DTE,
        coverage_mult=COVERAGE_MULT,
        policy=POLICY,
        has_gamma=has_gamma,
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts/far_budget_dynamic")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    root = Path(__file__).resolve().parents[1]
    engine_path = root / "research" / "qqq_dynamic_near_long_state_engine_v22_930c949.py"
    actual_engine_blob = v22.sha256_file(engine_path)  # raw SHA256 for runtime evidence

    od = Path(args.data_dir) / "QQQ_options.parquet"
    ud = Path(args.data_dir) / "QQQ_underlying.parquet"
    u = v22.load_underlying(ud)
    con = duckdb.connect()

    # Build the source-aligned N=10 fixed 8Δ reference exactly once.
    fixed_all = v22.build_far_candidates(u, con, od)
    if not fixed_all:
        raise RuntimeError("No fixed far candidates")
    fixed_far_all, has_gamma = fixed_all
    fixed = {
        d: {k: val for k, val in legs.items() if k == (FAR_DTE, FAR_DELTA)}
        for d, legs in fixed_far_all.items()
    }
    fixed = {d: legs for d, legs in fixed.items() if legs.get((FAR_DTE, FAR_DELTA))}

    dynamic_maps = {}
    audits = {}
    for n in N_VALUES:
        dm, audit = build_budget_dynamic_far(u, con, od, fixed, n)
        dynamic_maps[n] = dm
        audits[n] = audit
        audit.to_csv(out / f"selection_audit_n{n}.csv", index=False)

    # Fixed-control maps use the exact same frozen 8Δ candidate for both N values.
    fixed_maps = {n: fixed for n in N_VALUES}

    all_far_maps = [fixed_maps[10], fixed_maps[5], dynamic_maps[10], dynamic_maps[5]]
    near_chains, near_ids, event_dates = build_near_chains(u, con, od, all_far_maps)

    far_ids = set()
    for fmap in all_far_maps:
        for legs in fmap.values():
            for leg in legs.values():
                if leg:
                    far_ids.add(leg["cid"])

    fq = v22.get_quotes(con, od, far_ids, with_delta=True, with_gamma=has_gamma)
    far_quotes = v22.quote_maps(fq)
    nq = v22.get_quotes(con, od, near_ids)
    near_quotes = v22.quote_maps(nq)

    # Establish one fixed entry schedule from the frozen N10 fixed-8Δ control.
    # Every comparison case is then run one campaign at a time on those exact dates.
    v22.N_SHORT = 10
    baseline_probe = v22.simulate(
        u=u,
        far_candidates=fixed_maps[10],
        near_chains=near_chains,
        far_quotes_by_cid=far_quotes,
        near_quotes_by_cid=near_quotes,
        far_dte=FAR_DTE,
        far_delta=FAR_DELTA,
        near_dte=NEAR_DTE,
        coverage_mult=COVERAGE_MULT,
        policy=POLICY,
        has_gamma=has_gamma,
    )
    if baseline_probe.empty:
        raise RuntimeError("No baseline campaigns to define a common entry path")
    entry_dates = [pd.Timestamp(x) for x in baseline_probe["campaign_entry"].tolist()]

    runs = [
        ("N10_FIXED_8D", 10, fixed_maps[10]),
        ("N5_FIXED_8D", 5, fixed_maps[5]),
        ("N10_BUDGET_DYNAMIC", 10, dynamic_maps[10]),
        ("N5_BUDGET_DYNAMIC", 5, dynamic_maps[5]),
    ]

    summaries = []
    details = {}
    entry_status = []

    for name, n, fmap in runs:
        parts = []
        for entry_date in entry_dates:
            leg_map = fmap.get(entry_date, {})
            available = bool(leg_map.get((FAR_DTE, FAR_DELTA)))
            entry_status.append(
                {
                    "case": name,
                    "campaign_entry": str(entry_date.date()),
                    "candidate_available": available,
                }
            )
            if not available:
                continue
            one = simulate_forced_entry(
                u=u,
                entry_date=entry_date,
                far_candidates=fmap,
                near_chains=near_chains,
                far_quotes_by_cid=far_quotes,
                near_quotes_by_cid=near_quotes,
                n_short=n,
                has_gamma=has_gamma,
            )
            if not one.empty:
                parts.append(one)

        df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        df.to_csv(out / f"{name.lower()}.csv", index=False)
        details[name] = df
        audit = audits.get(n, pd.DataFrame()) if "BUDGET" in name else pd.DataFrame()
        audit = (
            audit[audit["date"].isin({str(d.date()) for d in entry_dates})].copy()
            if not audit.empty
            else audit
        )
        summaries.append(summarize_case(name, df, audit))

    pd.DataFrame(entry_status).to_csv(out / "forced_entry_status.csv", index=False)

    # Paired campaign comparison on the exact same entry-date schedule.
    a = details["N10_BUDGET_DYNAMIC"].copy()
    b = details["N5_BUDGET_DYNAMIC"].copy()
    paired = a.merge(
        b,
        on="campaign_entry",
        how="outer",
        suffixes=("_n10", "_n5"),
    )
    if not paired.empty:
        for col in ("total_pnl_usd", "far_pnl_usd", "maxdd"):
            paired[f"delta_{col}_n5_minus_n10"] = (
                paired[f"{col}_n5"] - paired[f"{col}_n10"]
            )
    paired.to_csv(out / "paired_dynamic_n5_minus_n10.csv", index=False)

    combined_audit = pd.concat(
        [audits[10].assign(case="N10_BUDGET_DYNAMIC"), audits[5].assign(case="N5_BUDGET_DYNAMIC")],
        ignore_index=True,
    )
    combined_audit.to_csv(out / "selection_audit_all.csv", index=False)

    report = {
        "research_id": "QQQ_V22_FAR_BUDGET_DYNAMIC_N5_N10_V1",
        "status": "REAL_QQQ_CHAIN_REPLAY",
        "pricing": "actual QQQ options Bid/Ask; frozen V22 simulator",
        "not_opra": False,
        "common_path": {
            "entry_schedule_source": "N10 fixed 8Δ frozen V22 control",
            "entry_schedule_campaigns": int(len(entry_dates)),
            "all_cases_forced_to_same_entry_dates": True,
            "future_path_data_preserved": True,
        },
        "anti_leakage": {
            "far_selection_uses": "entry-date chain only",
            "budget_target": "N10 fixed 8-delta entry Bid total premium on the same entry date",
            "dynamic_rule": "same selected expiration bucket as baseline; choose farthest OTM strike whose N x Bid still reaches the frozen aggregate financing target",
            "fallback": "highest-premium OTM contract in the selected expiration when target cannot be reached",
        },
        "frozen_parameters": {
            "far_dte": FAR_DTE,
            "far_delta_reference": FAR_DELTA,
            "near_dte": NEAR_DTE,
            "coverage_mult": COVERAGE_MULT,
            "policy": POLICY,
            "n_values": list(N_VALUES),
            "source_engine_blob_sha": FROZEN_ENGINE_BLOB,
            "source_engine_sha256_runtime": actual_engine_blob,
            "options_sha256": sha256_file(od),
            "underlying_sha256": sha256_file(ud),
            "underlying_range": [str(u.date.min().date()), str(u.date.max().date())],
            "signal_count": int(u.signal.sum()),
            "event_date_count": len(event_dates),
            "gamma_mode": "OBSERVED_GAMMA" if has_gamma else "DERIVED_DDELTA_DSPOT",
        },
        "results": summaries,
        "paired_dynamic": {
            "campaigns": int(len(paired)),
            "total_pnl_n5_minus_n10_usd": float(paired["delta_total_pnl_n5_minus_n10"].sum()) if not paired.empty else None,
            "mean_pnl_delta_usd": float(paired["delta_total_pnl_n5_minus_n10"].mean()) if not paired.empty else None,
            "median_pnl_delta_usd": float(paired["delta_total_pnl_n5_minus_n10"].median()) if not paired.empty else None,
            "n5_minus_n10_maxdd_delta_mean": float(paired["delta_maxdd_n5_minus_n10"].mean()) if not paired.empty else None,
            "n5_minus_n10_maxdd_delta_median": float(paired["delta_maxdd_n5_minus_n10"].median()) if not paired.empty else None,
        },
        "selection_audit": {
            "n10_budget_dynamic_rows": int(len(audits[10])),
            "n5_budget_dynamic_rows": int(len(audits[5])),
            "n10_fallback_count": int(audits[10].fallback_shortfall.sum()) if not audits[10].empty else 0,
            "n5_fallback_count": int(audits[5].fallback_shortfall.sum()) if not audits[5].empty else 0,
            "n10_mean_delta_abs": float(audits[10].selected_delta_abs.mean()) if not audits[10].empty else None,
            "n5_mean_delta_abs": float(audits[5].selected_delta_abs.mean()) if not audits[5].empty else None,
            "n10_mean_distance_pct": float(audits[10].distance_pct.mean()) if not audits[10].empty else None,
            "n5_mean_distance_pct": float(audits[5].distance_pct.mean()) if not audits[5].empty else None,
            "n10_mean_strike_shift_pct_vs_baseline": float(
                ((audits[10].selected_strike - audits[10].baseline_strike) / audits[10].baseline_strike).mean()
            ) if not audits[10].empty else None,
            "n5_mean_strike_shift_pct_vs_baseline": float(
                ((audits[5].selected_strike - audits[5].baseline_strike) / audits[5].baseline_strike).mean()
            ) if not audits[5].empty else None,
        },
        "interpretation_rule": "This run is a structural sensitivity test, not a claim that N5 or N10 is universally superior.",
    }
    (out / "qqq_v22_far_budget_dynamic_n5_n10_result.json").write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
