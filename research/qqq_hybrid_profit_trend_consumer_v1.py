"""
QQQ Hybrid Profit Trend Consumer V1

Purpose
-------
Apply the historical profit-trend feed as descriptive evidence, then
compute current target/capacity from external current inputs only.

Flow
----
Historical Profit Trend
    +
Current Market State
    +
Current Cash Pool
    +
Actual Current Holdings
    →
Current Target / Capacity
    →
Current vs Target

Hard boundary
-------------
Historical allocation percentages (including the old 42% QQQ) are NOT
current frozen sizing. They stay inside the preserved replay.

This consumer never reads a percentage out of the trend file and treats
it as today's capacity. Current sizing is always EXTERNAL_INPUT.

The trend is not turned into a BUY/SELL threshold.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_trend(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("not_opra") is not True:
        raise ValueError("Trend feed must declare not_opra=true")
    contract = data.get("current_sizing_contract") or {}
    for key in (
        "qqq_core_pct",
        "vxx_short_pct",
        "qqq_call_contracts",
        "vxx_call_contracts",
    ):
        if contract.get(key) != "EXTERNAL_INPUT":
            raise ValueError(f"Sizing contract violated: {key} is not EXTERNAL_INPUT")
    return data


def current_capacity(inputs: dict) -> dict:
    """Compute capacity from external current inputs only.

    Required external inputs:
      nav, qqq_price, vxx_price,
      qqq_core_pct, vxx_short_pct,
      qqq_call_budget_pct, vxx_call_budget_pct

    Optional:
      qqq_call_credit, vxx_call_credit
      (if missing or <=0, option quantity stays PENDING)
    """
    nav = float(inputs["nav"])
    qqq_price = float(inputs["qqq_price"])
    vxx_price = float(inputs["vxx_price"])
    qqq_core_pct = float(inputs["qqq_core_pct"])
    vxx_short_pct = float(inputs["vxx_short_pct"])
    qqq_call_budget_pct = float(inputs["qqq_call_budget_pct"])
    vxx_call_budget_pct = float(inputs["vxx_call_budget_pct"])

    qqq_shares = int(nav * (qqq_core_pct / 100.0) / qqq_price) if nav > 0 and qqq_price > 0 else 0
    vxx_shares = int(nav * (vxx_short_pct / 100.0) / vxx_price) if nav > 0 and vxx_price > 0 else 0

    def option_qty(budget_pct, credit):
        if credit is None or credit <= 0 or nav <= 0 or budget_pct <= 0:
            return None
        return max(0, int(nav * (budget_pct / 100.0) / (credit * 100.0)))

    q_credit = inputs.get("qqq_call_credit")
    v_credit = inputs.get("vxx_call_credit")
    q_qty = option_qty(qqq_call_budget_pct, float(q_credit) if q_credit is not None else None)
    v_qty = option_qty(vxx_call_budget_pct, float(v_credit) if v_credit is not None else None)

    return {
        "qqq_core_shares": qqq_shares,
        "vxx_short_shares": vxx_shares,
        "qqq_far_call_spreads": q_qty,
        "vxx_call_spreads": v_qty,
        "source": "EXTERNAL_INPUT",
        "note": "Capacity derived only from supplied current inputs. Historical 42% was not used.",
    }


def compare(current: dict, capacity: dict) -> dict:
    def gap(cur, tgt):
        if tgt is None:
            return {"status": "PENDING", "max_buy": 0, "max_sell": 0}
        cur = float(cur or 0)
        tgt = float(tgt)
        return {
            "current": cur,
            "target": tgt,
            "max_buy": max(0, tgt - cur),
            "max_sell": max(0, cur - tgt),
        }

    return {
        "qqq_core": gap(current.get("qqq_shares"), capacity["qqq_core_shares"]),
        "vxx_short": gap(current.get("vxx_shares"), capacity["vxx_short_shares"]),
        "qqq_far_call": gap(current.get("qqq_calls"), capacity["qqq_far_call_spreads"]),
        "vxx_call": gap(current.get("vxx_calls"), capacity["vxx_call_spreads"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-json", required=True, help="Path to profit_trend.json from the replay")
    parser.add_argument("--current-json", required=True, help="Path to current external inputs JSON")
    parser.add_argument("--out", default="artifacts/qqq_hybrid_profit_trend_consumer_v1.json")
    args = parser.parse_args()

    trend = load_trend(Path(args.trend_json))
    current_inputs = json.loads(Path(args.current_json).read_text(encoding="utf-8"))

    capacity = current_capacity(current_inputs)
    comparison = compare(current_inputs.get("holdings") or {}, capacity)

    report = {
        "research_id": "QQQ_HYBRID_PROFIT_TREND_CONSUMER_V1",
        "status": "DESCRIPTIVE_TREND_PLUS_EXTERNAL_CAPACITY",
        "historical_trend_evidence": {
            "source_replay": trend.get("source_replay"),
            "source_replay_sha": trend.get("source_replay_sha"),
            "replay_variant": trend.get("replay_variant"),
            "window": trend.get("window"),
            "backtest_result": trend.get("backtest_result"),
            "latest_descriptive_trend": trend.get("latest_descriptive_trend"),
            "usage": "historical descriptive evidence only; not a current trade signal",
        },
        "current_sizing_contract": trend.get("current_sizing_contract"),
        "current_capacity": capacity,
        "current_vs_target": comparison,
        "boundary": {
            "historical_42_pct_used_as_current_capacity": False,
            "trend_turned_into_buy_sell_threshold": False,
            "broker_order": False,
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
