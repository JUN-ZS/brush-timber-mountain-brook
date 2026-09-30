#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts-dir", default="parts")
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    parts = Path(args.parts_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    detail_files = sorted(parts.rglob("v23_dynamic_state_detail_shard_*.csv"))
    summary_files = sorted(parts.rglob("v23_dynamic_state_summary_shard_*.csv"))
    result_files = sorted(parts.rglob("v23_dynamic_state_result_shard_*.json"))

    if len(detail_files) != 24 or len(summary_files) != 24:
        raise RuntimeError(
            f"expected 24 detail + 24 summary files, got {len(detail_files)} + {len(summary_files)}"
        )

    details = pd.concat((pd.read_csv(p) for p in detail_files), ignore_index=True)
    summary = pd.concat((pd.read_csv(p) for p in summary_files), ignore_index=True)

    if len(summary) != 864:
        raise RuntimeError(f"expected 864 configuration rows, got {len(summary)}")
    if summary.config_index.nunique() != 864:
        raise RuntimeError("config_index is not unique across all 864 configurations")
    if set(summary.config_index.astype(int)) != set(range(864)):
        raise RuntimeError("config_index coverage is not exactly 0..863")

    if details.config_index.nunique() != 864:
        raise RuntimeError("detail does not contain all 864 configurations")

    summary = summary.sort_values(
        ["total_pnl_usd", "near_win_rate"],
        ascending=[False, False],
    ).reset_index(drop=True)

    # Campaign-level period robustness, kept descriptive rather than optimizing.
    d = details.copy()
    d["campaign_entry"] = pd.to_datetime(d["campaign_entry"])
    d["period"] = pd.cut(
        d["campaign_entry"].dt.year,
        bins=[2010, 2017, 2021, 2025],
        labels=["2011-2017", "2018-2021", "2022-2025"],
        include_lowest=True,
    )

    period_rows = []
    for idx, g in d.groupby(["config_index", "period"], observed=False):
        ci, period = idx
        if pd.isna(period):
            continue
        period_rows.append(
            {
                "config_index": int(ci),
                "period": str(period),
                "campaigns": int(len(g)),
                "total_pnl_usd": float(g.total_pnl_usd.sum()),
                "near_realized_pnl_usd": float(g.near_realized_pnl_usd.sum()),
                "far_pnl_usd": float(g.far_pnl_usd.sum()),
            }
        )
    periods = pd.DataFrame(period_rows)

    pivot = periods.pivot_table(
        index="config_index",
        columns="period",
        values="total_pnl_usd",
        aggfunc="sum",
        fill_value=0.0,
    )
    three_period_positive = 0
    if all(x in pivot.columns for x in ["2011-2017", "2018-2021", "2022-2025"]):
        three_period_positive = int(
            ((pivot["2011-2017"] > 0) &
             (pivot["2018-2021"] > 0) &
             (pivot["2022-2025"] > 0)).sum()
        )

    detail.to_csv(out / "v23_dynamic_state_detail_merged.csv", index=False)
    summary.to_csv(out / "v23_dynamic_state_summary_merged.csv", index=False)
    periods.to_csv(out / "v23_dynamic_state_periods.csv", index=False)

    metadata = []
    for p in result_files:
        try:
            metadata.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass

    report = {
        "status": "REAL_QQQ_CHAIN_DYNAMIC_STATE_ENGINE_V23_PARALLEL_MERGED",
        "matrix_configs": 864,
        "shards_expected": 24,
        "shards_result_files": len(metadata),
        "config_integrity": {
            "unique_configs": int(summary.config_index.nunique()),
            "missing_config_count": int(864 - summary.config_index.nunique()),
            "duplicate_config_count": int(len(summary) - summary.config_index.nunique()),
            "positive_total_pnl_configs": int((summary.total_pnl_usd > 0).sum()),
            "negative_total_pnl_configs": int((summary.total_pnl_usd < 0).sum()),
            "zero_total_pnl_configs": int((summary.total_pnl_usd == 0).sum()),
            "three_period_positive_configs": three_period_positive,
        },
        "top20": summary.head(20).to_dict("records"),
        "periods_file": "v23_dynamic_state_periods.csv",
        "detail_file": "v23_dynamic_state_detail_merged.csv",
        "summary_file": "v23_dynamic_state_summary_merged.csv",
    }

    (out / "v23_dynamic_state_result.json").write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
