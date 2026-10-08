"""
QQQ Hybrid Profit Trend Replay V1

Purpose
-------
Replay the preserved historical QQQ/VXX hybrid simulator and export the
profitability trend for downstream research.

Historical replay components:
  - QQQ long core
  - QQQ call-credit spread
  - VXX short stock
  - VXX call-credit spread

Sizing boundary
---------------
This program separates historical replay parameters from current sizing.

The preserved historical simulator contains historical/model allocation
parameters (including its old 42% QQQ allocation) solely to reproduce the old
backtest. Those values are NOT current frozen sizing.

The exported trend is evidence from the historical replay. A future/current
consumer must supply current sizing independently from the live cash-pool and
market-state calculation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from qqq_hybrid_dynamic_deployment_v1_1_replay import simulate


RESEARCH_ID = "QQQ_HYBRID_PROFIT_TREND_REPLAY_V1"
SOURCE_REPLAY = "QQQ_HYBRID_DYNAMIC_DEPLOYMENT_V1_1"
SOURCE_REPLAY_SHA = "ac74b3812c826ad491fb829108f26397322e45eb"
WINDOW_START = "2018-03-01"
WINDOW_END = "2026-09-04"


def _rolling_slope(values):
    if len(values) < 63:
        return float("nan")
    y = pd.Series(values, dtype="float64")
    t = pd.Series(range(len(y)), dtype="float64")
    t0 = t - t.mean()
    denom = float((t0**2).sum())
    if denom <= 0:
        return float("nan")
    return float((t0 * (y - y.mean())).sum() / denom)


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

    # Descriptive rolling performance only. No threshold here becomes a
    # current trade/sizing rule.
    for sessions, name in (
        (21, "1m"),
        (63, "3m"),
        (126, "6m"),
        (252, "12m"),
    ):
        x[f"profit_change_{name}"] = x["nav"].diff(sessions)
        x[f"return_{name}"] = x["nav"].pct_change(sessions)

    x["profit_slope_63d"] = x["profit"].rolling(
        63, min_periods=63
    ).apply(_rolling_slope, raw=True)

    return x


def latest_value(frame: pd.DataFrame, column: str):
    value = frame[column].iloc[-1]
    return None if pd.isna(value) else float(value)


def build_report(
    trend: pd.DataFrame,
    cagr: float,
    maxdd: float,
    final_nav: float,
    opens: int,
    closes: int,
    events: int,
    dynamic: bool,
) -> dict:
    initial_nav = float(trend["nav"].iloc[0])
    return {
        "research_id": RESEARCH_ID,
        "status": "DERIVED_REPLAY_TREND_EXPORT",
        "pricing_model": "DERIVED_BS_VIX",
        "not_opra": True,
        "source_replay": SOURCE_REPLAY,
        "source_replay_sha": SOURCE_REPLAY_SHA,
        "replay_variant": "DEPLOY_V1_1" if dynamic else "BASELINE",
        "window": {
            "start": WINDOW_START,
            "end": WINDOW_END,
            "rows": int(len(trend)),
        },
        "backtest_result": {
            "initial_nav": initial_nav,
            "final_nav": float(final_nav),
            "final_profit": float(trend["profit"].iloc[-1]),
            "cagr": float(cagr),
            "maxdd_daily_mtm": float(maxdd),
        },
        "latest_descriptive_trend": {
            "return_1m": latest_value(trend, "return_1m"),
            "return_3m": latest_value(trend, "return_3m"),
            "return_6m": latest_value(trend, "return_6m"),
            "return_12m": latest_value(trend, "return_12m"),
            "profit_slope_63d": latest_value(trend, "profit_slope_63d"),
            "drawdown": latest_value(trend, "drawdown"),
        },
        "source_trade_counts": {
            "opens": int(opens),
            "closes": int(closes),
            "events": int(events),
        },
        "current_sizing_contract": {
            "qqq_core_pct": "EXTERNAL_INPUT",
            "vxx_short_pct": "EXTERNAL_INPUT",
            "qqq_call_contracts": "EXTERNAL_INPUT",
            "vxx_call_contracts": "EXTERNAL_INPUT",
            "note": (
                "Historical replay sizing remains inside the preserved replay "
                "only. It is never promoted to current frozen capacity."
            ),
        },
        "consumer_contract": {
            "allowed": "Use profit/NAV trend as historical descriptive evidence.",
            "forbidden": (
                "Do not infer or hardcode current QQQ/VXX sizing from historical "
                "allocation percentages."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spots-path", required=True)
    parser.add_argument(
        "--out",
        default="artifacts/qqq_hybrid_profit_trend_replay_v1",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Replay V1.1 dynamic QQQ-financing deployment instead of baseline.",
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
    report = build_report(
        trend,
        cagr,
        maxdd,
        final_nav,
        len(opens),
        len(closes),
        len(events),
        args.dynamic,
    )
    json_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "research_id": RESEARCH_ID,
                "variant": report["replay_variant"],
                "csv": str(csv_path),
                "json": str(json_path),
                "rows": int(len(trend)),
                "final_nav": float(final_nav),
                "cagr": float(cagr),
                "maxdd_daily_mtm": float(maxdd),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
