"""Safer current-capacity adapter for the VXX short-call/put research line.

Current budgets and entry permissions are required EXTERNAL_INPUTS.
Historical percentages do not become current sizing defaults.
All option quantities use defined-risk spread max loss, not received credit.
This module emits a sizing worksheet only; it does not route orders.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def validate_trend(trend: dict) -> None:
    if trend.get("not_opra") is not True:
        raise ValueError("Historical trend must explicitly declare not_opra=true")
    contract = trend.get("current_sizing_contract") or {}
    for key in ("qqq_core_pct", "vxx_short_pct", "qqq_call_contracts", "vxx_call_contracts"):
        if contract.get(key) != "EXTERNAL_INPUT":
            raise ValueError(f"Historical trend sizing contract violated: {key}")


def _nonnegative_pct(sizing: dict, key: str) -> float:
    if key not in sizing:
        raise ValueError(f"Missing required EXTERNAL_INPUT sizing field: {key}")
    value = float(sizing[key])
    if not math.isfinite(value) or value < 0 or value > 100:
        raise ValueError(f"{key} must be a finite percentage in [0, 100]")
    return value


def _positive_number(obj: dict, key: str) -> float:
    value = float(obj[key])
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{key} must be finite and > 0")
    return value


def option_spread_capacity(nav: float, risk_pct: float, candidate: dict | None, side: str) -> dict:
    if candidate is None:
        return {"status": "PENDING", "target_contracts": None, "max_loss_per_spread": None,
                "risk_budget_usd": nav * risk_pct / 100.0, "reason": "No current executable chain candidate"}
    try:
        short_k = _positive_number(candidate, "short_strike")
        long_k = _positive_number(candidate, "long_strike")
        credit = _positive_number(candidate, "credit")
        dte = int(candidate["dte"])
        expiry = str(candidate["expiry"]).strip()
        short_delta = abs(float(candidate["short_delta"]))
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "PENDING", "target_contracts": None, "max_loss_per_spread": None,
                "risk_budget_usd": nav * risk_pct / 100.0, "reason": f"Invalid/missing candidate field: {exc}"}

    if not expiry or dte <= 0 or not math.isfinite(short_delta) or not 0 < short_delta < 1:
        return {"status": "PENDING", "target_contracts": None, "max_loss_per_spread": None,
                "risk_budget_usd": nav * risk_pct / 100.0, "reason": "Invalid expiry, DTE, or short delta"}

    if side == "call":
        width = long_k - short_k
    elif side == "put":
        width = short_k - long_k
    else:
        raise ValueError("side must be call or put")
    if width <= 0 or credit >= width:
        return {"status": "PENDING", "target_contracts": None, "max_loss_per_spread": None,
                "risk_budget_usd": nav * risk_pct / 100.0,
                "reason": "Invalid vertical ordering or credit >= spread width"}

    max_loss = (width - credit) * 100.0
    budget = nav * risk_pct / 100.0
    target = int(math.floor((budget + 1e-9) / max_loss)) if max_loss > 0 and risk_pct > 0 else 0
    return {
        "status": "READY", "side": side, "expiry": expiry, "dte": dte,
        "short_strike": short_k, "long_strike": long_k, "short_delta": short_delta,
        "credit": credit, "width": width, "max_loss_per_spread": max_loss,
        "risk_budget_usd": budget, "target_contracts": target,
        "max_loss_at_target": target * max_loss,
        "risk_budget_check": target * max_loss <= budget + 1e-7,
    }


def _compare(current, target, allow_new: bool) -> dict:
    current = max(float(current or 0), 0.0)
    if target is None:
        return {"status": "PENDING", "current": current, "target": None, "max_buy": 0, "max_sell": 0}
    target = float(target)
    max_sell = max(0.0, current - target)
    gap = max(0.0, target - current)
    return {
        "status": "OVER_CAP_TRIM" if max_sell > 0 else (
            "AT_TARGET" if gap == 0 else ("READY_TO_ADD" if allow_new else "HOLD_NO_ADD")
        ),
        "current": current, "target": target,
        "max_buy": gap if allow_new else 0.0, "max_sell": max_sell,
    }


def build_capacity_report(trend: dict, strategy_report: dict, inputs: dict) -> dict:
    validate_trend(trend)
    if strategy_report.get("not_opra") is not True:
        raise ValueError("VXX strategy report must declare not_opra=true")
    nav = _positive_number(inputs, "nav")
    qqq_price = _positive_number(inputs, "qqq_price")
    vxx_price = _positive_number(inputs, "vxx_price")
    sizing = inputs.get("current_sizing") or {}
    holdings = inputs.get("holdings") or {}
    candidates = inputs.get("candidates") or {}
    state = inputs.get("market_state") or {}
    allow_new = state.get("allow_new") or {}

    q_core_pct = _nonnegative_pct(sizing, "qqq_core_notional_pct")
    v_short_pct = _nonnegative_pct(sizing, "vxx_short_notional_pct")
    q_call_pct = _nonnegative_pct(sizing, "qqq_call_max_loss_pct")
    v_call_pct = _nonnegative_pct(sizing, "vxx_call_max_loss_pct")
    v_put_pct = _nonnegative_pct(sizing, "vxx_put_max_loss_pct")

    capacity = {
        "qqq_core_shares": int(math.floor(nav * q_core_pct / 100.0 / qqq_price)),
        "vxx_short_shares": int(math.floor(nav * v_short_pct / 100.0 / vxx_price)),
        "qqq_far_call": option_spread_capacity(nav, q_call_pct, candidates.get("qqq_call"), "call"),
        "vxx_call": option_spread_capacity(nav, v_call_pct, candidates.get("vxx_call"), "call"),
        "vxx_put": option_spread_capacity(nav, v_put_pct, candidates.get("vxx_put"), "put"),
    }
    targets = {
        "qqq_core": capacity["qqq_core_shares"],
        "vxx_short": capacity["vxx_short_shares"],
        "qqq_far_call": capacity["qqq_far_call"]["target_contracts"],
        "vxx_call": capacity["vxx_call"]["target_contracts"],
        "vxx_put": capacity["vxx_put"]["target_contracts"],
    }
    current_keys = {
        "qqq_core": "qqq_shares", "vxx_short": "vxx_shares",
        "qqq_far_call": "qqq_call_spreads", "vxx_call": "vxx_call_spreads",
        "vxx_put": "vxx_put_spreads",
    }
    current_vs_target = {}
    for leg, target in targets.items():
        permission = allow_new.get(leg)
        current_vs_target[leg] = _compare(
            holdings.get(current_keys[leg], 0), target, allow_new=(permission is True)
        )
        current_vs_target[leg]["new_entry_permission"] = (
            "EXPLICITLY_GRANTED" if permission is True else "NOT_GRANTED_OR_HOLD"
        )
    return {
        "program": "QQQ_HYBRID_CURRENT_CAPACITY_V2",
        "status": "EXTERNAL_BUDGETS_DEFINED_RISK_SIZING_ONLY",
        "history_evidence": {
            "legacy_variant": trend.get("backtest_result") or {},
            "strategy_research_id": strategy_report.get("research_id"),
            "dual_call_put_result": (strategy_report.get("variants") or {}).get("DUAL_CALL_PUT"),
            "usage": "Descriptive historical evidence only; not a source of current sizing percentages.",
        },
        "input_market_state_label": state.get("label", "UNSPECIFIED"),
        "cash_pool_nav_usd": nav, "current_sizing_source": "EXTERNAL_INPUT",
        "current_capacity": capacity, "current_vs_target": current_vs_target,
        "boundary": {
            "historical_percentages_promoted_to_current_sizing": False,
            "option_contracts_sized_by_credit_instead_of_max_loss": False,
            "missing_candidate_generates_contract_count": False,
            "unprovided_entry_permission_grants_add": False,
            "broker_order": False,
        },
        "risk_note": "VXX short stock has no defined maximum loss. VXX option legs are defined-risk verticals only.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend-json", required=True)
    parser.add_argument("--strategy-json", required=True)
    parser.add_argument("--current-json", required=True)
    parser.add_argument("--out", default="artifacts/qqq_hybrid_current_capacity_v2.json")
    args = parser.parse_args()
    report = build_capacity_report(
        json.loads(Path(args.trend_json).read_text(encoding="utf-8")),
        json.loads(Path(args.strategy_json).read_text(encoding="utf-8")),
        json.loads(Path(args.current_json).read_text(encoding="utf-8")),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
