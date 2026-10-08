"""
QQQ Hybrid Profit Trend Export V1

Purpose
-------
Replay the historical source-aligned hybrid simulator and export ONLY the
resulting profitability trend as a reusable research feed.

The historical replay contains:
  - QQQ long core
  - QQQ call-credit spread
  - VXX short stock
  - VXX call-credit spread

Important separation
--------------------
This file DOES NOT define current/live frozen sizing.

In particular, the historical replay may contain a historical/model value such
as 42% QQQ allocation. That value is preserved only because the imported
historical simulator must be replayed faithfully. It is NOT exported as a
current target, capacity, or frozen sizing rule.

Current sizing must remain an external/operator calculation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from qqq_hybrid_dynamic_deployment_v1_1 import simulate


RESEARCH_ID = "QQQ_HYBRID_PROFIT_TREND_EXPORT_V1"
SOURCE_REPLAY = "QQQ_HYBRID_DYNAMIC_DEPLOYMENT_V1_1"
WINDOW_START = "2018-03-01"
WINDOW_END = "2026-09-04"


def build_profit_trend(eq: pd.DataFrame) -> pd.DataFrame:
    if not {"date", "nav"}.issubset(eq.columns):
        raise ValueError("Simulator equity frame must contain date and nav")

    x = eq.copy()
    x["date"] = pd.to_datetime(x["date"])
    x = x.sort_values("date").reset_index(drop=True)

    initial_nav = float(x["nav"].iloc[0])
    x["profit"] = x["nav"] - initial_nav
    x["total_return"] = x["nav"] / initial_nav - 1.0
    x["daily_profit"] = x["nav"].diff().fillna(0.0)
    x["peak_nav"] = x["nav"].cummax()
    x["drawdown"] = x["nav"] / x["peak_nav"] - 1.0

    # Descriptive trend only: raw rolling performance at fixed horizons.
    # These are not optimized thresholds and are not current trade triggers.
    for sessions, name in (
        (21, "1m"),
        (63, "3m"),
        (126, "6m"),
        (252, "12m"),
    ):
        x[f"profit_change_{name}"] = x["nav"].diff(sessions)
        x[f"return_{name}"] = x["nav"].pct_change(sessions)

    # A simple descriptive slope in dollars/session over the last 63 sessions.
    # It is intentionally not converted into a sizing rule here.
    x["profit_slope_63d"] = (
        x["profit"].rolling(63, min_periods=63)
        .apply(
            lambda y: float(
                pd.Series(y.values)
                .pipe(lambda s: s.index.to_series().corr(s) * 0)
            )
        )
    )

    # Replace the placeholder above with an explicit least-squares slope.
    def slope(values):
        if len(values) < 63:
            return float("nan")
        y = pd.Series(values, dtype="float64")
        t = pd.Series(range(len(y)), dtype="float64")
        denom = float(((t - t.mean()) ** 2).sum())
        if denom <= 0:
            return float("nan")
        return float(((t - t.mean()) * (y - y.mean())).sum() / denom)

    x["profit_slope_63d"] = x["profit"].rolling(63, min_periods=63).apply(
        slope, raw=True
    )

    return x


def summarize(trend: pd.DataFrame, cagr: float, maxdd: float, final_nav: float) -> dict:
    initial_nav = float(trend["nav"].iloc[0])
    final_profit = float(trend["profit"].iloc[-1])

    def latest(column: str):
        value = trend[column].iloc[-1]
        return None if pd.isna(value) else float(value)

    return {
        "research_id": RESEARCH_ID,
        "source_replay": SOURCE_REPLAY,
        "status": "DERIVED_REPLAY_TREND_EXPORT",
        "pricing_model": "DERIVED_BS_VIX",
        "not_opra": True,
        "window": {
            "start": WINDOW_START,
            "end": WINDOW_END,
            "rows": int(len(trend)),
        },
        "backtest_result": {
            "initial_nav": initial_nav,
            "final_nav": float(final_nav),
            "final_profit": final_profit,
            "cagr": float(cagr),
            "maxdd_daily_mtm": float(maxdd),
        },
        "latest_descriptive_trend": {
            "return_1m": latest("return_1m"),
            "return_3m": latest("return_3m"),
            "return_6m": latest("return_6m"),
            "return_12m": latest("return_12m"),
            "profit_slope_63d": latest("profit_slope_63d"),
            "drawdown": latest("drawdown"),
        },
        "current_sizing_contract": {
            "qqq_core_pct": "EXTERNAL_INPUT",
            "vxx_short_pct": "EXTERNAL_INPUT",
            "qqq_call_contracts": "EXTERNAL_INPUT",
            "vxx_call_contracts": "EXTERNAL_INPUT",
            "note": (
                "Historical replay parameters are not exported as current "
                "frozen sizing. Current sizing is derived separately from "
                "the live cash-pool / market-state calculation."
            ),
        },
        "outputs": {
            "csv_columns": [
                "date",
                "nav",
                "profit",
                "total_return",
                "daily_profit",
                "peak_nav",
                "drawdown",
                "profit_change_1m",
                "return_1m",
                "profit_change_3m",
                "return_3m",
                "profit_change_6m",
                "return_6m",
                "profit_change_12m",
                "return_12m",
                "profit_slope_63d",
            ]
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spots-path", required=True)
    parser.add_argument("--out", default="artifacts/qqq_hybrid_profit_trend_v1")
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Use the V1.1 dynamic QQQ-financing deployment replay instead of baseline.",
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cagr, maxdd, final_nav, opens, closes, events, eq = simulate(
        args.spots_path,
        dynamic=args.dynamic,
    )

    trend = build_profit_trend(eq)

    csv_path = out / "profit_trend.csv"
    json_path = out / "profit_trend.json"
    trend.to_csv(csv_path, index=False)

    report = summarize(trend, cagr, maxdd, final_nav)
    report["replay_variant"] = "DEPLOY_V1_1" if args.dynamic else "BASELINE"
    report["source_trade_counts"] = {
        "opens": int(len(opens)),
        "closes": int(len(closes)),
        "events": int(len(events)),
    }
    report["consumer_rule"] = (
        "Consume the historical profitability trend as descriptive research "
        "evidence. Do not convert it into a hidden sizing constant."
    )

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({
        "research_id": RESEARCH_ID,
        "variant": report["replay_variant"],
        "csv": str(csv_path),
        "json": str(json_path),
        "rows": int(len(trend)),
        "final_nav": float(final_nav),
        "cagr": float(cagr),
        "maxdd_daily_mtm": float(maxdd),
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
