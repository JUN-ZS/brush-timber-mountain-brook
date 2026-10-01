#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd

from qqq_dynamic_near_long_state_engine_v22_930c949 import (
    FAR_DELTAS,
    FAR_DTES,
    POLICIES,
    build_far_candidates,
    get_quotes,
    load_underlying,
    pick_near,
    quote_maps,
    read_options,
    simulate,
)

CANDIDATE_NEAR_DTE = 30
CANDIDATE_COVERAGE = 1.50

OOS_WINDOWS = {
    "forward_holdout_2022-03-08_to_2025-12-15": ("2022-03-08", "2025-12-15"),
    "late_holdout_2024-01-02_to_2025-12-15": ("2024-01-02", "2025-12-15"),
}


def mask_campaigns(u_full: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    u = u_full.copy()
    u["signal"] = u["signal"] & u["date"].between(start, end)
    return u


def run_family(u: pd.DataFrame, con, opt_path: Path):
    far_build = build_far_candidates(u, con, opt_path)
    if not far_build:
        raise RuntimeError("No far candidates")
    far_candidates, has_gamma = far_build

    event_dates = set(
        pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(), "date"]
    )
    for legs in far_candidates.values():
        for leg in legs.values():
            if not leg:
                continue
            for d, vv in far_candidates.items():
                if leg in vv.values():
                    end = min(pd.Timestamp(leg["expiry"]), d + pd.Timedelta(days=365))
                    event_dates.update(
                        pd.Timestamp(x)
                        for x in u.loc[u.date.between(d, end), "date"]
                    )
                    break

    event_dates = sorted(event_dates)
    near = read_options(
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
        raise RuntimeError("No near option chains")
    near["date"] = pd.to_datetime(near.date)
    near["expiration"] = pd.to_datetime(near.expiration)
    near_chains = {d: g for d, g in near.groupby("date", sort=False)}

    near_ids = set()
    for d, ch in near_chains.items():
        spot_row = u.loc[u.date == d, "close"]
        if spot_row.empty:
            continue
        leg = pick_near(ch, float(spot_row.iloc[0]), CANDIDATE_NEAR_DTE)
        if leg:
            near_ids.add(leg["cid"])

    far_ids = {
        leg["cid"]
        for legs in far_candidates.values()
        for leg in legs.values()
        if leg
    }

    fq = get_quotes(con, opt_path, far_ids, with_delta=True, with_gamma=has_gamma)
    nq = get_quotes(con, opt_path, near_ids)
    far_quotes_by_cid = quote_maps(fq)
    near_quotes_by_cid = quote_maps(nq)

    rows = []
    for fd in FAR_DTES:
        for fdel in FAR_DELTAS:
            for policy in POLICIES:
                df = simulate(
                    u=u,
                    far_candidates=far_candidates,
                    near_chains=near_chains,
                    far_quotes_by_cid=far_quotes_by_cid,
                    near_quotes_by_cid=near_quotes_by_cid,
                    far_dte=fd,
                    far_delta=fdel,
                    near_dte=CANDIDATE_NEAR_DTE,
                    coverage_mult=CANDIDATE_COVERAGE,
                    policy=policy,
                    has_gamma=has_gamma,
                )
                if df.empty:
                    continue
                df["data_gamma_mode"] = (
                    "OBSERVED_GAMMA" if has_gamma else "DERIVED_DDELTA_DSPOT"
                )
                rows.append(df)

    if not rows:
        raise RuntimeError("No family results")
    return pd.concat(rows, ignore_index=True), has_gamma


def aggregate(detail: pd.DataFrame):
    key = ["far_dte_target", "far_delta_target", "policy"]
    cfg = (
        detail.groupby(key, as_index=False)
        .agg(
            campaigns=("total_pnl_usd", "size"),
            total_pnl_usd=("total_pnl_usd", "sum"),
            median_campaign_pnl_usd=("total_pnl_usd", "median"),
            mean_campaign_pnl_usd=("total_pnl_usd", "mean"),
            positive_campaign_ratio=("total_pnl_usd", lambda s: float((s > 0).mean())),
            worst_campaign_pnl_usd=("total_pnl_usd", "min"),
            mean_campaign_maxdd=("maxdd", "mean"),
            worst_campaign_maxdd=("maxdd", "min"),
            far_pnl_usd=("far_pnl_usd", "sum"),
            near_realized_pnl_usd=("near_realized_pnl_usd", "sum"),
            near_trades=("near_trades", "sum"),
            near_wins=("long_wins", "sum"),
            near_losses=("long_losses", "sum"),
        )
    )
    cfg["near_win_rate"] = cfg["near_wins"] / (cfg["near_wins"] + cfg["near_losses"]).clip(lower=1)

    family = {
        "n_configs": int(len(cfg)),
        "n_campaign_rows": int(len(detail)),
        "positive_config_ratio": float((cfg["total_pnl_usd"] > 0).mean()),
        "median_config_total_pnl_usd": float(cfg["total_pnl_usd"].median()),
        "q25_config_total_pnl_usd": float(cfg["total_pnl_usd"].quantile(0.25)),
        "q75_config_total_pnl_usd": float(cfg["total_pnl_usd"].quantile(0.75)),
        "positive_campaign_ratio": float((detail["total_pnl_usd"] > 0).mean()),
        "median_campaign_pnl_usd": float(detail["total_pnl_usd"].median()),
        "mean_campaign_maxdd": float(detail["maxdd"].mean()),
        "worst_campaign_pnl_usd": float(detail["total_pnl_usd"].min()),
        "worst_campaign_maxdd": float(detail["maxdd"].min()),
        "total_pnl_usd": float(detail["total_pnl_usd"].sum()),
        "far_pnl_usd": float(detail["far_pnl_usd"].sum()),
        "near_realized_pnl_usd": float(detail["near_realized_pnl_usd"].sum()),
        "near_trades": int(detail["near_trades"].sum()),
        "near_win_rate": float(
            detail["long_wins"].sum()
            / max(1, detail["long_wins"].sum() + detail["long_losses"].sum())
        ),
        "positive_policy_count_by_median": int(
            (cfg.groupby("policy")["median_campaign_pnl_usd"].median() > 0).sum()
        ),
        "positive_far_cell_count_by_median": int(
            (cfg.groupby(["far_dte_target", "far_delta_target"])["median_campaign_pnl_usd"].median() > 0).sum()
        ),
    }

    policy = (
        cfg.groupby("policy", as_index=False)
        .agg(
            n_configs=("total_pnl_usd", "size"),
            total_pnl_usd=("total_pnl_usd", "sum"),
            median_config_total_pnl_usd=("total_pnl_usd", "median"),
            median_campaign_pnl_usd=("median_campaign_pnl_usd", "median"),
            positive_config_ratio=("total_pnl_usd", lambda s: float((s > 0).mean())),
            positive_campaign_ratio=("positive_campaign_ratio", "mean"),
            mean_maxdd=("mean_campaign_maxdd", "mean"),
            worst_campaign_pnl_usd=("worst_campaign_pnl_usd", "min"),
            near_win_rate=("near_win_rate", "mean"),
        )
        .sort_values("total_pnl_usd", ascending=False)
    )

    far = (
        cfg.groupby(["far_dte_target", "far_delta_target"], as_index=False)
        .agg(
            n_configs=("total_pnl_usd", "size"),
            total_pnl_usd=("total_pnl_usd", "sum"),
            median_config_total_pnl_usd=("total_pnl_usd", "median"),
            median_campaign_pnl_usd=("median_campaign_pnl_usd", "median"),
            positive_config_ratio=("total_pnl_usd", lambda s: float((s > 0).mean())),
            positive_campaign_ratio=("positive_campaign_ratio", "mean"),
            mean_maxdd=("mean_campaign_maxdd", "mean"),
            worst_campaign_pnl_usd=("worst_campaign_pnl_usd", "min"),
            near_win_rate=("near_win_rate", "mean"),
        )
        .sort_values(["far_dte_target", "far_delta_target"])
    )

    yearly = (
        detail.assign(year=pd.to_datetime(detail["campaign_entry"]).dt.year)
        .groupby("year", as_index=False)
        .agg(
            campaign_rows=("total_pnl_usd", "size"),
            total_pnl_usd=("total_pnl_usd", "sum"),
            positive_campaign_ratio=("total_pnl_usd", lambda s: float((s > 0).mean())),
            median_campaign_pnl_usd=("total_pnl_usd", "median"),
            mean_maxdd=("maxdd", "mean"),
        )
    )

    return family, cfg, policy, far, yearly


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default="artifacts/oos_family")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    od = Path(args.data_dir) / "QQQ_options.parquet"
    ud = Path(args.data_dir) / "QQQ_underlying.parquet"

    u_full = load_underlying(ud)
    con = duckdb.connect()

    def sha256_file(path: Path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    lock_path = Path("research/evidence_v1/STRATEGY_LOCK.json")
    lock_obj = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_hash = hashlib.sha256(
        json.dumps(lock_obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    frozen_engine = Path("research/qqq_dynamic_near_long_state_engine_v22_930c949.py")

    manifest = {
        "engine_commit": "930c949ec5260865f2bf3ee1c6e030dab7b8e4c4",
        "frozen_engine_sha256": sha256_file(frozen_engine),
        "strategy_lock_hash": lock_hash,
        "canonical_data_sha256": {
            "QQQ_options.parquet": sha256_file(od),
            "QQQ_underlying.parquet": sha256_file(ud),
        },
        "candidate": "30D near + 1.50x coverage",
        "candidate_family_configs": 72,
        "family_definition": "9 far DTE×delta combinations × all 8 policies; no sub-selection inside OOS",
        "selection_status": "LOCKED_FROM_PRIOR_FULL_SAMPLE_V22_AUDIT",
        "virgin_oos_status": "NOT_VIRGIN_BECAUSE_PRIOR_SELECTION_USED_FULL_V22_SAMPLE",
        "windows": {},
    }

    for name, (start_s, end_s) in OOS_WINDOWS.items():
        start = pd.Timestamp(start_s)
        end = pd.Timestamp(end_s)
        u = mask_campaigns(u_full, start, end)
        detail, has_gamma = run_family(u, con, od)
        family, cfg, policy, far, yearly = aggregate(detail)

        prefix = out / name
        detail.to_csv(prefix.with_suffix(".detail.csv"), index=False)
        cfg.to_csv(prefix.with_suffix(".config.csv"), index=False)
        policy.to_csv(prefix.with_suffix(".policy.csv"), index=False)
        far.to_csv(prefix.with_suffix(".far.csv"), index=False)
        yearly.to_csv(prefix.with_suffix(".year.csv"), index=False)

        manifest["windows"][name] = {
            "start": start_s,
            "end": end_s,
            "gamma_mode": "OBSERVED_GAMMA" if has_gamma else "DERIVED_DDELTA_DSPOT",
            "family": family,
        }

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
