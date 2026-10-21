"""
QQQ Hybrid New Program V1

This is the program that uses the exported hybrid profit trend.

Input feeds (historical evidence only)
--------------------------------------
1. Profit trend from the four-layer hybrid replay:
     - QQQ long core
     - QQQ call-credit spread
     - VXX short stock
     - VXX call-credit spread
2. VXX call-spread attribution (why the hybrid was recovered)

Current inputs (EXTERNAL_INPUT only)
------------------------------------
- Current cash pool / NAV
- Current QQQ / VXX prices
- External sizing percentages or budgets
- Actual current holdings
- Optional current option credits (if no credit, option qty stays PENDING)

Output
------
- Historical trend evidence (including VXX call-spread contribution)
- Current target / capacity
- Current vs target (max buy / max sell)

Hard boundary
-------------
Historical 42% is NOT current frozen sizing.
The profit trend is NOT turned into a BUY/SELL threshold.
No broker order is created.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_trend(trend: dict) -> None:
    if trend.get("not_opra") is not True:
        raise ValueError("Trend feed must declare not_opra=true")
    contract = trend.get("current_sizing_contract") or {}
    for key in (
        "qqq_core_pct",
        "vxx_short_pct",
        "qqq_call_contracts",
        "vxx_call_contracts",
    ):
        if contract.get(key) != "EXTERNAL_INPUT":
            raise ValueError(f"Sizing contract violated: {key} is not EXTERNAL_INPUT")


def current_capacity(inputs: dict) -> dict:
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
    return {
        "qqq_core_shares": qqq_shares,
        "vxx_short_shares": vxx_shares,
        "qqq_far_call_spreads": option_qty(
            qqq_call_budget_pct, float(q_credit) if q_credit is not None else None
        ),
        "vxx_call_spreads": option_qty(
            vxx_call_budget_pct, float(v_credit) if v_credit is not None else None
        ),
        "source": "EXTERNAL_INPUT",
        "note": "Capacity from current inputs only. Historical 42% was not used.",
    }


def compare(holdings: dict, capacity: dict) -> dict:
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
        "qqq_core": gap(holdings.get("qqq_shares"), capacity["qqq_core_shares"]),
        "vxx_short": gap(holdings.get("vxx_shares"), capacity["vxx_short_shares"]),
        "qqq_far_call": gap(holdings.get("qqq_calls"), capacity["qqq_far_call_spreads"]),
        "vxx_call": gap(holdings.get("vxx_calls"), capacity["vxx_call_spreads"]),
    }


def build_program_output(trend: dict, vxx_cc: dict | None, inputs: dict) -> dict:
    validate_trend(trend)
    capacity = current_capacity(inputs)
    comparison = compare(inputs.get("holdings") or {}, capacity)

    vxx_evidence = None
    if vxx_cc is not None:
        layer = vxx_cc.get("vxx_call_spread") or {}
        profit = (trend.get("backtest_result") or {}).get("final_profit")
        share = None
        if profit and layer.get("realized_pnl") is not None:
            share = round(float(layer["realized_pnl"]) / float(profit), 4)
        vxx_evidence = {
            "structure": layer.get("structure"),
            "risk_budget": layer.get("risk_budget"),
            "opens": layer.get("opens"),
            "closes": layer.get("closes"),
            "wins": layer.get("wins"),
            "losses": layer.get("losses"),
            "realized_pnl": layer.get("realized_pnl"),
            "share_of_baseline_profit": share,
            "usage": "historical evidence for the VXX call-spread layer only",
        }

    return {
        "program": "QQQ_HYBRID_NEW_PROGRAM_V1",
        "status": "TREND_FEED_PLUS_EXTERNAL_CAPACITY",
        "why_hybrid_was_recovered": "VXX call-credit spread (short VXX call + long wing)",
        "historical_evidence": {
            "window": trend.get("window"),
            "backtest_result": trend.get("backtest_result"),
            "latest_descriptive_trend": trend.get("latest_descriptive_trend"),
            "vxx_call_spread": vxx_evidence,
            "usage": "descriptive evidence only; not a current trade signal",
        },
        "current_sizing_contract": trend.get("current_sizing_contract"),
        "current_capacity": capacity,
        "current_vs_target": comparison,
        "boundary": {
            "historical_42_pct_used_as_current_capacity": False,
            "trend_turned_into_buy_sell_threshold": False,
            "broker_order": False,
            "opra_fills": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-json", required=True, help="profit_trend.json from hybrid replay")
    parser.add_argument(
        "--vxx-cc-json",
        help="Optional vxx_cc_report.json from VXX call-spread attribution",
    )
    parser.add_argument("--current-json", required=True, help="Current external inputs")
    parser.add_argument("--out", default="artifacts/qqq_hybrid_new_program_v1.json")
    args = parser.parse_args()

    trend = load_json(Path(args.trend_json))
    vxx_cc = load_json(Path(args.vxx_cc_json)) if args.vxx_cc_json else None
    inputs = load_json(Path(args.current_json))

    report = build_program_output(trend, vxx_cc, inputs)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
