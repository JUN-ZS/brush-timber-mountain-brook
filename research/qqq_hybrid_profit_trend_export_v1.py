"""
QQQ Hybrid Profit Trend Export V1

Replay the historical source-aligned hybrid simulator and export its
profitability trend as a reusable research feed.

Historical replay components:
  - QQQ long core
  - QQQ call-credit spread
  - VXX short stock
  - VXX call-credit spread

IMPORTANT
---------
This program does NOT define current/live frozen sizing.

A historical replay constant such as 42% QQQ allocation is preserved only
inside the imported historical simulator so that its old backtest behavior is
replayed faithfully. It is NOT exported as a current target, capacity, or
frozen sizing rule.

Current sizing remains an external/operator calculation.
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

    # Raw rolling performance. These are descriptive outputs only; this
    # program does not turn them into trade or sizing thresholds.
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


def summarize(
    trend: pd.DataFrame,
    cagr: float,
    maxdd: float,
    final_nav: float,
    dynamic: bool,
    opens: int,
    closes: int,
    events: int,
) -> dict:
    initial_nav = float(trend["nav"].iloc[0])

    return {
        "research_id": RESEARCH_ID,
        "source_replay": SOURCE_REPLAY,
        "status": "DERIVED_REPLAY_TREND_EXPORT",
        "pricing_model": "DERIVED_BS_VIX",
        "not_opra": True,
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
                "Historical replay sizing is not exported as current frozen "
                "capacity. Current sizing is derived separately from the live "
                "cash-pool and market-state calculation."
            ),
        },
        "consumer_rule": (
            "Use profit_trend.csv/json as descriptive historical evidence. "
            "Do not convert historical replay percentages into hidden current "
            "sizing constants."
        ),
        "csv_columns": list(trend.columns),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spots-path", required=True)
    parser.add_argument(
        "--out",
        default="artifacts/qqq_hybrid_profit_trend_v1",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help=(
            "Replay V1.1 dynamic QQQ-financing deployment. "
            "Default is the original baseline replay."
        ),
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

    report = summarize(
        trend,
        cagr,
        maxdd,
        final_nav,
        args.dynamic,
        len(opens),
        len(closes),
        len(events),
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
