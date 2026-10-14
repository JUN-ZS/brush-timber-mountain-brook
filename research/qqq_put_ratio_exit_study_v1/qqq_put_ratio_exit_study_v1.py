#!/usr/bin/env python3
"""Research-only 1-long/5-short QQQ put-ratio exit study.

Uses pinned public EOD option snapshots, not confirmed fills. No policy is approved
for live trading. All strategy exits are evaluated at quote snapshots only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "research" / "qqq_hybrid_operator_terminal_v1"
START_DATE = "2018-03-01"
SOURCE_END_DATE = "2025-12-15"
REQUESTED_END_DATE = "2025-12-31"
REFERENCE_NAV_USD = 100_000.0  # normalization only; not asserted to be the user's live NAV
CONTRACT_MULTIPLIER = 100
LONG_QTY = 1
SHORT_QTY = 5
DTE_MIN = 30
DTE_MAX = 60
DTE_TARGET = 45
LONG_ABS_DELTA_TARGET = 0.30
LONG_ABS_DELTA_RANGE = (0.20, 0.40)
SHORT_ABS_DELTA_TARGET = 0.10
SHORT_ABS_DELTA_RANGE = (0.04, 0.16)
EXIT_DTE = 7
EARLY_WIN_DAYS = 5
NO_PROFIT_DAYS = 20
PROFIT_TARGETS_USD = (500.0, 1000.0, 2000.0)
LOSS_STOPS_USD = (500.0, 1000.0, 2000.0)
MAX_PROFIT_FRACTIONS = (0.25, 0.50)
SLIPPAGE_PER_LEG_USD = (0.0, 0.025, 0.05, 0.10)
COMMISSION_PER_CONTRACT_PER_SIDE_USD = (0.0, 0.65)
BASE_EVENT_SLIPPAGE = 0.05
BASE_EVENT_COMMISSION = 0.65


def as_day(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return str(value)[:10]


def num(value: Any) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None


def contract_id(row: dict[str, Any]) -> str:
    value = re.sub(r"\s+", "", str(row.get("contract_id") or "").strip().upper())
    return value[2:] if value.startswith("O:") else value


def standard_put_identity(row: dict[str, Any]) -> bool:
    """Require standard QQQ OCC root, put right, and internally consistent expiry/strike."""
    ident = contract_id(row)
    match = re.fullmatch(r"QQQ(\d{6})P(\d{8})", ident)
    if not match or str(row.get("symbol", "")).upper() != "QQQ":
        return False
    if str(row.get("type", "")).strip().lower() not in ("p", "put"):
        return False
    try:
        encoded_expiry = datetime.strptime(match.group(1), "%y%m%d").date().isoformat()
    except ValueError:
        return False
    strike = num(row.get("strike"))
    encoded_strike = int(match.group(2)) / 1000.0
    return (
        as_day(row.get("expiration")) == encoded_expiry
        and strike is not None and strike > 0
        and abs(strike - encoded_strike) < 0.00051
    )


def quote_fields_valid(row: dict[str, Any] | None, allow_zero_bid: bool = False) -> bool:
    if not isinstance(row, dict):
        return False
    bid, ask = num(row.get("bid")), num(row.get("ask"))
    if bid is None or ask is None or ask <= 0:
        return False
    if bid < 0 or (bid == 0 and not allow_zero_bid) or bid > ask:
        return False
    return True


def entry_quote_valid(row: dict[str, Any] | None, side: str, quantity: int) -> bool:
    if not quote_fields_valid(row, allow_zero_bid=False):
        return False
    assert row is not None
    size_field = "bid_size" if side == "bid" else "ask_size"
    size = num(row.get(size_field))
    return size is not None and size >= quantity


def short_ask_quote_valid(row: dict[str, Any] | None) -> bool:
    """Validate a short-put close mark/action using the Ask side required to buy back.

    Bid may be missing when the Ask is still valid; if Bid is present it must not
    be negative or crossed. Displayed Ask size is separately checked for execution.
    """
    if not isinstance(row, dict):
        return False
    ask, bid = num(row.get("ask")), num(row.get("bid"))
    if ask is None or ask <= 0:
        return False
    if bid is not None and (bid < 0 or bid > ask):
        return False
    return True


def long_bid_quote_valid(row: dict[str, Any] | None, allow_zero_bid: bool = True) -> bool:
    """Validate a long-put mark/sale using the Bid side received when selling."""
    if not isinstance(row, dict):
        return False
    bid, ask = num(row.get("bid")), num(row.get("ask"))
    if bid is None or ask is None or ask <= 0:
        return False
    if bid < 0 or (bid == 0 and not allow_zero_bid) or bid > ask:
        return False
    return True


def quote_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {contract_id(row): row for row in rows if contract_id(row)}


def choose_ratio_put(
    rows: list[dict[str, Any]],
    signal_day: str,
    valid_expiries: set[str] | None = None,
    strike_validator: Callable[[float], bool] | None = None,
) -> dict[str, Any]:
    """Choose 1 higher-strike long put and 5 lower-strike short puts at same expiry.

    Selection is preregistered: DTE nearest 45 within 30–60; long abs(delta) nearest
    .30 within [.20,.40]; short abs(delta) nearest .10 within [.04,.16].
    Actual listed standard-root contracts only. No price/P&L optimization is used.
    """
    validator = strike_validator or (lambda _strike: True)
    try:
        signal_date = date.fromisoformat(signal_day)
    except ValueError:
        return {"status": "INVALID_SIGNAL_DATE"}
    candidates = []
    for row in rows:
        if not standard_put_identity(row):
            continue
        if as_day(row.get("date")) != signal_day:
            continue
        expiry = as_day(row.get("expiration"))
        if valid_expiries is not None and expiry not in valid_expiries:
            continue
        try:
            dte = (date.fromisoformat(expiry) - signal_date).days
        except ValueError:
            continue
        if not DTE_MIN <= dte <= DTE_MAX:
            continue
        strike, delta = num(row.get("strike")), num(row.get("delta"))
        if strike is None or delta is None or not 0 < abs(delta) < 1:
            continue
        if not validator(strike):
            continue
        if not quote_fields_valid(row) or not entry_quote_valid(row, "bid", 1) or not entry_quote_valid(row, "ask", 1):
            continue
        item = {
            "row": row, "id": contract_id(row), "expiry": expiry, "dte": dte,
            "strike": strike, "abs_delta": abs(delta),
            "min_size": min(num(row.get("bid_size")) or 0, num(row.get("ask_size")) or 0),
            "open_interest": num(row.get("open_interest")) or 0,
        }
        if LONG_ABS_DELTA_RANGE[0] <= item["abs_delta"] <= LONG_ABS_DELTA_RANGE[1]:
            candidates.append({**item, "role": "long"})
        if SHORT_ABS_DELTA_RANGE[0] <= item["abs_delta"] <= SHORT_ABS_DELTA_RANGE[1]:
            candidates.append({**item, "role": "short"})
    longs = [x for x in candidates if x["role"] == "long"]
    shorts = [x for x in candidates if x["role"] == "short"]
    pairs = []
    for long_leg in longs:
        for short_leg in shorts:
            if long_leg["expiry"] != short_leg["expiry"] or long_leg["strike"] <= short_leg["strike"]:
                continue
            dte = long_leg["dte"]
            delta_error = abs(long_leg["abs_delta"] - LONG_ABS_DELTA_TARGET) + abs(short_leg["abs_delta"] - SHORT_ABS_DELTA_TARGET)
            # Liquidity is a tie-breaker only, not a forecast; narrow vertical wins only after DTE/Delta.
            size_score = min(long_leg["min_size"], short_leg["min_size"])
            oi_score = min(long_leg["open_interest"], short_leg["open_interest"])
            key = (abs(dte - DTE_TARGET), delta_error, -size_score, -oi_score, long_leg["strike"] - short_leg["strike"], long_leg["id"], short_leg["id"])
            pairs.append((key, long_leg, short_leg))
    if not pairs:
        return {"status": "NO_VALID_STANDARD_1X5_PUT_RATIO"}
    _, long_leg, short_leg = min(pairs, key=lambda x: x[0])
    return {
        "status": "PAIR_SELECTED", "signal_date": signal_day,
        "expiry": long_leg["expiry"], "signal_dte": long_leg["dte"],
        "long_id": long_leg["id"], "long_strike": long_leg["strike"],
        "long_abs_delta": long_leg["abs_delta"], "short_id": short_leg["id"],
        "short_strike": short_leg["strike"], "short_abs_delta": short_leg["abs_delta"],
        "width": long_leg["strike"] - short_leg["strike"],
        "selection_rule": "nearest DTE45, long absDelta .30, short absDelta .10; same expiry; long strike > short strike",
    }


def entry_quotes(pair: dict[str, Any], rows: list[dict[str, Any]], entry_day: str) -> tuple[dict[str, Any] | None, str]:
    qmap = quote_map(rows)
    long_row, short_row = qmap.get(pair["long_id"]), qmap.get(pair["short_id"])
    if long_row is None or short_row is None:
        return None, "NEXT_SESSION_CONTRACT_ROW_MISSING"
    if as_day(long_row.get("date")) != entry_day or as_day(short_row.get("date")) != entry_day:
        return None, "ENTRY_QUOTE_DATE_MISMATCH"
    if not standard_put_identity(long_row) or not standard_put_identity(short_row):
        return None, "ENTRY_CONTRACT_IDENTITY_INVALID"
    if as_day(long_row.get("expiration")) != pair["expiry"] or as_day(short_row.get("expiration")) != pair["expiry"]:
        return None, "ENTRY_EXPIRY_MISMATCH"
    if not entry_quote_valid(short_row, "bid", SHORT_QTY):
        return None, "SHORT_BID_OR_SIZE_INSUFFICIENT"
    if not entry_quote_valid(long_row, "ask", LONG_QTY):
        return None, "LONG_ASK_OR_SIZE_INSUFFICIENT"
    return {"long": long_row, "short": short_row}, "OK"


def entry_cashflow(trade: dict[str, Any], slippage: float, commission: float) -> float:
    q = trade["entry_quotes"]
    short_bid = float(q["short"]["bid"])
    long_ask = float(q["long"]["ask"])
    # Five short puts are sold at Bid; one long put is bought at Ask. Costs apply to all 6 contracts.
    return CONTRACT_MULTIPLIER * (SHORT_QTY * (short_bid - slippage) - (long_ask + slippage)) - (SHORT_QTY + LONG_QTY) * commission


def expiry_intrinsic_pnl(cash: float, n_short: int, n_long: int, k_short: float, k_long: float, spot: float) -> float:
    long_payoff = n_long * max(k_long - spot, 0.0)
    short_payoff = n_short * max(k_short - spot, 0.0)
    return cash + CONTRACT_MULTIPLIER * (long_payoff - short_payoff)


def terminal_risk(trade: dict[str, Any], cash_at_entry: float, reference_nav: float = REFERENCE_NAV_USD) -> dict[str, Any]:
    ks, kl = trade["short_strike"], trade["long_strike"]
    max_gain = max(0.0, expiry_intrinsic_pnl(cash_at_entry, SHORT_QTY, LONG_QTY, ks, kl, ks))
    zero_pnl = expiry_intrinsic_pnl(cash_at_entry, SHORT_QTY, LONG_QTY, ks, kl, 0.0)
    tail_loss = max(0.0, -zero_pnl)
    stress = {}
    spot = num(trade.get("spot_entry"))
    for drop in (0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 0.75, 1.0):
        target_spot = None if spot is None else spot * (1 - drop)
        stress[f"underlying_drop_{int(drop*100)}pct"] = None if target_spot is None else round(expiry_intrinsic_pnl(cash_at_entry, SHORT_QTY, LONG_QTY, ks, kl, target_spot), 2)
    return {
        "entry_net_cash_usd": round(cash_at_entry, 2),
        "max_terminal_profit_at_short_strike_usd": round(max_gain, 2),
        "terminal_pnl_if_qqq_zero_usd": round(zero_pnl, 2),
        "terminal_tail_loss_if_qqq_zero_usd": round(tail_loss, 2),
        "terminal_tail_loss_pct_reference_nav": round(100 * tail_loss / reference_nav, 4),
        "max_profit_to_zero_price_tail_loss_ratio": round(max_gain / tail_loss, 6) if tail_loss > 0 else None,
        "1000_usd_target_as_pct_zero_price_tail_loss": round(100 * 1000 / tail_loss, 6) if tail_loss > 0 else None,
        "whole_ratio_units_under_0p5pct_nav_tail_budget": math.floor(reference_nav * 0.005 / tail_loss) if tail_loss > 0 else None,
        "whole_ratio_units_under_1pct_nav_tail_budget": math.floor(reference_nav * 0.01 / tail_loss) if tail_loss > 0 else None,
        "whole_ratio_units_under_2pct_nav_tail_budget": math.floor(reference_nav * 0.02 / tail_loss) if tail_loss > 0 else None,
        "required_reference_nav_for_1pct_tail_budget_usd": round(tail_loss / 0.01, 2) if tail_loss > 0 else 0.0,
        "terminal_intrinsic_stress_scenarios_usd": stress,
        "stress_status": "HYPOTHETICAL_EXPIRY_INTRINSIC_ONLY; EXCLUDES INTERIM_IV/MARGIN_CALL_AND_EXECUTION_GAPS",
    }


def mark_pnl(state: dict[str, Any], step: dict[str, Any], slippage: float, commission: float) -> tuple[float | None, str]:
    """Net liquidation estimate from observed close-side quote sides; not fill evidence."""
    result = float(state["cash"])
    if state["n_short"] > 0:
        row = step.get("short")
        if not short_ask_quote_valid(row):
            return None, "SHORT_MARK_MISSING_OR_INVALID"
        assert row is not None
        ask = num(row.get("ask"))
        if ask is None:
            return None, "SHORT_ASK_MISSING"
        result -= state["n_short"] * CONTRACT_MULTIPLIER * ask
        result -= state["n_short"] * (CONTRACT_MULTIPLIER * slippage + commission)
    if state["n_long"] > 0:
        row = step.get("long")
        if not long_bid_quote_valid(row, allow_zero_bid=True):
            return None, "LONG_MARK_MISSING_OR_INVALID"
        assert row is not None
        bid = num(row.get("bid"))
        if bid is None:
            return None, "LONG_BID_MISSING"
        result += state["n_long"] * CONTRACT_MULTIPLIER * bid
        # A zero bid is a zero-floor valuation, not a sale or proof of an executable exit.
        if bid > 0:
            result -= state["n_long"] * (CONTRACT_MULTIPLIER * slippage + commission)
    return result, "OK"


def close_short_qty(state: dict[str, Any], step: dict[str, Any], qty: int, slippage: float, commission: float) -> tuple[bool, str]:
    if qty <= 0 or qty > state["n_short"]:
        return False, "INVALID_CLOSE_QUANTITY"
    row = step.get("short")
    if not short_ask_quote_valid(row):
        return False, "SHORT_EXIT_QUOTE_INVALID"
    assert row is not None
    ask, size = num(row.get("ask")), num(row.get("ask_size"))
    if ask is None or ask <= 0:
        return False, "SHORT_EXIT_ASK_MISSING"
    if size is None or size < qty:
        return False, "SHORT_EXIT_ASK_SIZE_INSUFFICIENT"
    state["cash"] -= qty * CONTRACT_MULTIPLIER * (ask + slippage) + qty * commission
    state["n_short"] -= qty
    state["contracts_closed_short"] += qty
    return True, "OK"


def sell_long_if_executable(state: dict[str, Any], step: dict[str, Any], slippage: float, commission: float) -> tuple[bool, str]:
    if state["n_long"] <= 0:
        return True, "NO_LONG_REMAINS"
    row = step.get("long")
    if not quote_fields_valid(row, allow_zero_bid=True):
        return False, "LONG_EXIT_QUOTE_INVALID"
    assert row is not None
    bid, size = num(row.get("bid")), num(row.get("bid_size"))
    if bid is None or bid <= 0:
        return False, "LONG_ZERO_OR_MISSING_BID_REMAINS_OPEN"
    if size is None or size < state["n_long"]:
        return False, "LONG_EXIT_BID_SIZE_INSUFFICIENT_REMAINS_OPEN"
    qty = state["n_long"]
    state["cash"] += qty * CONTRACT_MULTIPLIER * (bid - slippage) - qty * commission
    state["n_long"] = 0
    return True, "OK"


def policy_list() -> list[dict[str, Any]]:
    policies = [{"name": "BASE_DTE7_CLOSE_SHORT_RISK", "kind": "dte7"}]
    policies += [{"name": f"TP_USD_{int(target)}_CLOSE_SHORT_RISK", "kind": "tp_usd", "target": target} for target in PROFIT_TARGETS_USD]
    policies += [{"name": f"TP_{int(frac*100)}PCT_MAX_TERMINAL_GAIN", "kind": "tp_fraction", "fraction": frac} for frac in MAX_PROFIT_FRACTIONS]
    policies += [{"name": "FAST_1000_WITHIN_5D_TRIM_4_SHORTS", "kind": "fast_trim", "target": 1000.0, "max_days": EARLY_WIN_DAYS, "trim_qty": 4}]
    policies += [{"name": "DAY20_NONPOSITIVE_CLOSE_SHORT_RISK", "kind": "day20_close"}, {"name": "DAY20_NONPOSITIVE_TRIM_4_SHORTS", "kind": "day20_trim", "trim_qty": 4}]
    policies += [{"name": f"SL_USD_{int(target)}_CLOSE_SHORT_RISK", "kind": "sl_usd", "target": target} for target in LOSS_STOPS_USD]
    return policies


def simulate_policy(trade: dict[str, Any], policy: dict[str, Any], slippage: float, commission: float) -> dict[str, Any]:
    state = {"cash": entry_cashflow(trade, slippage, commission), "n_short": SHORT_QTY, "n_long": LONG_QTY, "contracts_closed_short": 0}
    entry_cash = state["cash"]
    risk = terminal_risk(trade, entry_cash)
    target = None
    if policy["kind"] == "tp_usd" or policy["kind"] == "fast_trim":
        target = float(policy["target"])
    elif policy["kind"] == "tp_fraction":
        max_gain = risk["max_terminal_profit_at_short_strike_usd"]
        target = max_gain * float(policy["fraction"]) if max_gain > 0 else None
    pending_action: str | None = None
    pending_action_reason: str | None = None
    pending_action_date: str | None = None
    first_signal_date: str | None = None
    first_signal_action: str | None = None
    action_date: str | None = None
    action_dte: int | None = None
    action_hold_sessions: int | None = None
    resolved_holding_sessions: int | None = None
    first_signal_holding_sessions: int | None = None
    first_signal_reason: str | None = None
    policy_rule_signal_date: str | None = None
    policy_rule_signal_holding_sessions: int | None = None
    short_risk_exposure_session_equivalents = 0.0
    primary_action: str | None = None
    policy_rule_fired = False
    actions: list[dict[str, Any]] = []
    daily: list[dict[str, Any]] = []
    mark_missing = 0
    mark_required = 0
    action_deferred = 0
    max_observed = None
    min_observed = None
    final_pnl = None
    final_status = "UNRESOLVED"
    expiry = trade["expiry"]
    for i, step in enumerate(trade["path"]):
        hold_sessions = i
        dte = (date.fromisoformat(expiry) - date.fromisoformat(step["date"])).days
        # Count each observed replay session by remaining short quantity, relative to the original
        # five-short structure. This is a descriptive exposure-duration unit, not account capital or margin.
        short_risk_exposure_session_equivalents += state["n_short"] / SHORT_QTY
        # If all short risk is gone, keep trying to sell a still-open long put when a positive bid reappears.
        if state["n_short"] == 0 and state["n_long"] > 0:
            sold, sell_status = sell_long_if_executable(state, step, slippage, commission)
            if sold and state["n_long"] == 0:
                actions.append({"date": step["date"], "action": "SELL_RESIDUAL_LONG", "status": sell_status})
        pnl, mark_status = mark_pnl(state, step, slippage, commission)
        if state["n_short"] > 0 or state["n_long"] > 0:
            mark_required += 1
            if pnl is None:
                mark_missing += 1
        if pnl is not None:
            max_observed = pnl if max_observed is None else max(max_observed, pnl)
            min_observed = pnl if min_observed is None else min(min_observed, pnl)

        trigger = None
        # Signal only from an EOD mark; never execute against the same snapshot.
        # The order becomes eligible at the next observed session (dte > 0 only).
        if dte > 0 and state["n_short"] > 0 and pending_action is None and not policy_rule_fired and hold_sessions >= 1 and pnl is not None:
            kind = policy["kind"]
            if kind == "tp_usd" and pnl >= float(policy["target"]):
                trigger = "CLOSE_SHORT_RISK"
            elif kind == "tp_fraction" and target is not None and pnl >= target:
                trigger = "CLOSE_SHORT_RISK"
            elif kind == "sl_usd" and pnl <= -float(policy["target"]):
                trigger = "CLOSE_SHORT_RISK"
            elif kind == "fast_trim" and hold_sessions <= int(policy["max_days"]) and pnl >= float(policy["target"]):
                trigger = "TRIM_SHORTS"
            elif kind == "day20_close" and hold_sessions >= NO_PROFIT_DAYS and pnl <= 0:
                trigger = "CLOSE_SHORT_RISK"
            elif kind == "day20_trim" and hold_sessions >= NO_PROFIT_DAYS and pnl <= 0:
                trigger = "TRIM_SHORTS"
            if trigger:
                pending_action = trigger
                pending_action_reason = policy["name"]
                pending_action_date = step["date"]
                policy_rule_fired = True
                policy_rule_signal_date = step["date"]
                policy_rule_signal_holding_sessions = hold_sessions
                if first_signal_date is None:
                    first_signal_date = step["date"]
                    first_signal_action = trigger
                    first_signal_holding_sessions = hold_sessions
                    first_signal_reason = pending_action_reason

        # Baseline and all exit rules share a DTE<=7 risk-close boundary. This is
        # also an EOD signal; execution must occur on a later session, not this mark.
        if dte > 0 and state["n_short"] > 0 and pending_action is None and dte <= EXIT_DTE:
            pending_action = "CLOSE_SHORT_RISK"
            pending_action_reason = "DTE7_MANDATORY_CLOSE_SHORT_RISK"
            pending_action_date = step["date"]
            if first_signal_date is None:
                first_signal_date = step["date"]
                first_signal_action = "CLOSE_SHORT_RISK"
                first_signal_holding_sessions = hold_sessions
                first_signal_reason = pending_action_reason

        action_status = "NONE"
        can_execute_pending = (
            pending_action is not None and pending_action_date is not None
            and step["date"] > pending_action_date and dte > 0
        )
        if state["n_short"] > 0 and can_execute_pending:
            if pending_action == "TRIM_SHORTS":
                qty_to_close = min(int(policy.get("trim_qty", 4)), state["n_short"])
            else:
                qty_to_close = state["n_short"]
            closed, close_status = close_short_qty(state, step, qty_to_close, slippage, commission)
            if closed:
                if action_date is None:
                    action_date = step["date"]
                    action_dte = dte
                    action_hold_sessions = hold_sessions
                    primary_action = pending_action
                action_status = "EXECUTED_" + pending_action
                actions.append({"date": step["date"], "action": pending_action, "quantity": qty_to_close, "signal_date": pending_action_date, "reason": pending_action_reason, "status": close_status})
                if pending_action == "CLOSE_SHORT_RISK":
                    sold, sell_status = sell_long_if_executable(state, step, slippage, commission)
                    actions.append({"date": step["date"], "action": "SELL_LONG_IF_EXECUTABLE", "status": sell_status, "sold": sold})
                pending_action = None
            else:
                action_deferred += 1
                action_status = "DEFERRED_" + close_status
                actions.append({"date": step["date"], "action": pending_action, "quantity": qty_to_close, "signal_date": pending_action_date, "status": close_status})

        pnl_after, after_status = mark_pnl(state, step, slippage, commission)
        if pnl_after is not None:
            max_observed = pnl_after if max_observed is None else max(max_observed, pnl_after)
            min_observed = pnl_after if min_observed is None else min(min_observed, pnl_after)

        settled_today = False
        if dte <= 0:
            spot = num(step.get("spot"))
            if spot is not None:
                final_pnl = expiry_intrinsic_pnl(state["cash"], state["n_short"], state["n_long"], trade["short_strike"], trade["long_strike"], spot)
                state["cash"] = final_pnl
                state["n_short"] = 0
                state["n_long"] = 0
                final_status = "INTRINSIC_SETTLEMENT_PROXY_BEFORE_EXERCISE_ASSIGNMENT_FEES"
                resolved_holding_sessions = hold_sessions
                settled_today = True
            else:
                final_status = "UNRESOLVED_MISSING_EXPIRY_UNDERLYING"
        elif state["n_short"] == 0 and state["n_long"] == 0 and final_pnl is None:
            final_pnl = state["cash"]
            final_status = "CLOSED_AT_OBSERVED_SIDE_QUOTES"
            resolved_holding_sessions = hold_sessions

        if settled_today:
            pnl_after = final_pnl
            after_status = final_status
        daily.append({
            "date": step["date"], "holding_sessions": hold_sessions, "dte": dte,
            "pnl_before_action_usd": round(pnl, 2) if pnl is not None else None,
            "pnl_after_action_usd": round(pnl_after, 2) if pnl_after is not None else None,
            "mark_status": mark_status if pnl is None else after_status,
            "n_short_after_action": state["n_short"], "n_long_after_action": state["n_long"],
            "action_status": action_status,
        })
        if settled_today:
            break
        if state["n_short"] == 0 and state["n_long"] == 0:
            final_pnl = state["cash"]
            final_status = "CLOSED_AT_OBSERVED_SIDE_QUOTES"
            # Keep a flat cash path through the shared expiry window so exit rules use fixed entry cohorts.
            continue

    if final_pnl is None and trade["path"] and trade["path"][-1]["date"] == expiry:
        final_status = "UNRESOLVED_MISSING_EXPIRY_UNDERLYING"
    if final_pnl is None and state["n_short"] == 0 and state["n_long"] == 0:
        final_pnl = state["cash"]
        final_status = "CLOSED_AT_OBSERVED_SIDE_QUOTES"
        if trade["path"]:
            resolved_holding_sessions = len(trade["path"]) - 1
    target_value = target
    return {
        "trade_id": trade["trade_id"], "policy": policy["name"],
        "slippage_per_leg_usd": slippage, "commission_per_contract_per_side_usd": commission,
        "entry_date": trade["entry_date"], "signal_date": trade["signal_date"], "expiry": trade["expiry"],
        "long_id": trade["long_id"], "short_id": trade["short_id"],
        "long_strike": trade["long_strike"], "short_strike": trade["short_strike"],
        "spot_entry": trade["spot_entry"], "vix_entry": trade.get("vix_entry"),
        "entry_net_cash_usd": round(entry_cash, 2), "target_usd": round(target_value, 2) if target_value is not None else None,
        "terminal_tail_loss_if_qqq_zero_usd": risk["terminal_tail_loss_if_qqq_zero_usd"],
        "terminal_tail_loss_pct_reference_nav": risk["terminal_tail_loss_pct_reference_nav"],
        "final_pnl_usd": round(final_pnl, 2) if final_pnl is not None else None,
        "final_pnl_pct_reference_nav": round(final_pnl / REFERENCE_NAV_USD * 100, 6) if final_pnl is not None else None,
        "final_status": final_status, "exit_action": primary_action or "NONE",
        "exit_signal_date": first_signal_date, "exit_signal_action": first_signal_action,
        "first_signal_holding_sessions": first_signal_holding_sessions, "first_signal_reason": first_signal_reason,
        "policy_rule_signal_date": policy_rule_signal_date,
        "policy_rule_signal_holding_sessions": policy_rule_signal_holding_sessions,
        "exit_action_date": action_date, "exit_action_dte": action_dte,
        "exit_action_holding_sessions": action_hold_sessions,
        "signal_to_action_delay_sessions": (
            action_hold_sessions - first_signal_holding_sessions
            if action_hold_sessions is not None and first_signal_holding_sessions is not None else None
        ),
        "resolved_holding_sessions": resolved_holding_sessions,
        "short_risk_exposure_session_equivalents": round(short_risk_exposure_session_equivalents, 4),
        "action_deferred_sessions": action_deferred,
        "marked_sessions_required": mark_required, "missing_mark_sessions": mark_missing,
        "mark_coverage_pct": round(100*(mark_required-mark_missing)/mark_required, 4) if mark_required else 100.0,
        "max_observed_trade_pnl_usd": round(max_observed, 2) if max_observed is not None else None,
        "min_observed_trade_pnl_usd": round(min_observed, 2) if min_observed is not None else None,
        "actions": actions, "daily": daily,
    }


def mark_unmodified_trade(trade: dict[str, Any], slippage: float, commission: float) -> list[dict[str, Any]]:
    state = {"cash": entry_cashflow(trade, slippage, commission), "n_short": SHORT_QTY, "n_long": LONG_QTY}
    out = []
    for i, step in enumerate(trade["path"]):
        dte = (date.fromisoformat(trade["expiry"]) - date.fromisoformat(step["date"])).days
        pnl, status = mark_pnl(state, step, slippage, commission)
        if dte <= 0 and num(step.get("spot")) is not None:
            pnl = expiry_intrinsic_pnl(state["cash"], state["n_short"], state["n_long"], trade["short_strike"], trade["long_strike"], float(step["spot"]))
            status = "EXPIRY_INTRINSIC_PROXY"
        out.append({"date": step["date"], "holding_sessions": i, "dte": dte, "pnl_usd": round(pnl, 2) if pnl is not None else None, "mark_status": status, "vix": step.get("vix"), "spot": step.get("spot")})
    return out


def _distribution(values: list[float]) -> dict[str, Any]:
    xs = sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    if not xs:
        return {"n": 0, "mean": None, "median": None, "p05": None, "p95": None}
    def q(p):
        return xs[min(len(xs)-1, max(0, int(round((len(xs)-1)*p))))]
    return {"n": len(xs), "mean": round(sum(xs)/len(xs), 4), "median": round(statistics.median(xs), 4), "p05": round(q(.05), 4), "p95": round(q(.95), 4)}


def summarize_policy(results: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [x for x in results if x["final_pnl_usd"] is not None]
    pnls = [float(x["final_pnl_usd"]) for x in closed]
    winners = [x for x in pnls if x > 0]
    losers = [x for x in pnls if x < 0]
    profit_factor = sum(winners) / abs(sum(losers)) if losers and sum(losers) != 0 else (None if not winners else None)
    policy_triggered = [x for x in results if x.get("policy_rule_signal_date") is not None]
    fallback_triggered = [
        x for x in results
        if x.get("first_signal_reason") == "DTE7_MANDATORY_CLOSE_SHORT_RISK"
    ]
    resolved_exposure_rows = [
        x for x in closed
        if num(x.get("short_risk_exposure_session_equivalents")) is not None
        and float(x.get("short_risk_exposure_session_equivalents")) > 0
    ]
    resolved_exposure = sum(float(x["short_risk_exposure_session_equivalents"]) for x in resolved_exposure_rows)
    resolved_pnl_on_exposure_rows = sum(float(x["final_pnl_usd"]) for x in resolved_exposure_rows)
    return {
        "policy": results[0]["policy"] if results else "UNKNOWN",
        "slippage_per_leg_usd": results[0]["slippage_per_leg_usd"] if results else None,
        "commission_per_contract_per_side_usd": results[0]["commission_per_contract_per_side_usd"] if results else None,
        "trade_episodes": len(results), "resolved_trades": len(closed), "unresolved_trades": len(results)-len(closed),
        "closed_trade_net_pnl_sum_usd": round(sum(pnls), 2) if pnls else None,
        "closed_trade_net_pnl_pct_reference_nav": round(sum(pnls)/REFERENCE_NAV_USD*100, 6) if pnls else None,
        "expectancy_usd_per_resolved_trade": round(sum(pnls)/len(pnls), 2) if pnls else None,
        "median_trade_pnl_usd": round(statistics.median(pnls), 2) if pnls else None,
        "win_rate": round(len(winners)/len(pnls), 6) if pnls else None,
        "profit_factor": round(profit_factor, 6) if profit_factor is not None else None,
        "gross_wins_usd": round(sum(winners), 2), "gross_losses_usd": round(sum(losers), 2),
        "best_trade_usd": round(max(pnls), 2) if pnls else None,
        "worst_trade_usd": round(min(pnls), 2) if pnls else None,
        "policy_rule_triggered_trade_count": len(policy_triggered),
        "policy_rule_trigger_rate_pct": round(100 * len(policy_triggered) / len(results), 2) if results else None,
        "mandatory_dte7_fallback_trade_count": len(fallback_triggered),
        "policy_rule_trigger_age_sessions_distribution": _distribution([
            x["policy_rule_signal_holding_sessions"] for x in policy_triggered
            if x.get("policy_rule_signal_holding_sessions") is not None
        ]),
        "first_risk_action_age_sessions_distribution": _distribution([
            x["exit_action_holding_sessions"] for x in results if x.get("exit_action_holding_sessions") is not None
        ]),
        "resolved_holding_age_sessions_distribution": _distribution([
            x["resolved_holding_sessions"] for x in closed if x.get("resolved_holding_sessions") is not None
        ]),
        "signal_to_first_action_delay_sessions_distribution": _distribution([
            x["signal_to_action_delay_sessions"] for x in results if x.get("signal_to_action_delay_sessions") is not None
        ]),
        "resolved_short_risk_exposure_session_equivalents": round(resolved_exposure, 4),
        "net_pnl_per_short_risk_equivalent_session_usd": (
            round(resolved_pnl_on_exposure_rows / resolved_exposure, 4) if resolved_exposure > 0 else None
        ),
        "net_pnl_per_short_risk_equivalent_session_note": "Closed-trade net P&L divided by the sum of observed replay sessions weighted by remaining short contracts / original 5 shorts; descriptive only, not annualized, not risk-adjusted, and not a stand-alone policy selector.",
        "mean_action_deferred_sessions_per_trade": round(statistics.mean([x["action_deferred_sessions"] for x in results]), 4) if results else None,
        "total_missing_mark_sessions": sum(x["missing_mark_sessions"] for x in results),
        "trade_mark_coverage_pct": round(100 * (sum(x["marked_sessions_required"]-x["missing_mark_sessions"] for x in results) / sum(x["marked_sessions_required"] for x in results)), 4) if sum(x["marked_sessions_required"] for x in results) else 100.0,
        "terminal_tail_loss_zero_usd_distribution": _distribution([x["terminal_tail_loss_if_qqq_zero_usd"] for x in results]),
        "full_portfolio_return_metrics_status": "BLOCKED: fixed 1x5 unit path; source EOD marks/entry timing not confirmed fills; margin and complete broker execution records unavailable",
    }


def summarize_events(trades: list[dict[str, Any]]) -> dict[str, Any]:
    fast, late, day20_loss, day20_profit = [], [], [], []
    event_rows = []
    for trade in trades:
        marks = mark_unmodified_trade(trade, BASE_EVENT_SLIPPAGE, BASE_EVENT_COMMISSION)
        by_age = {x["holding_sessions"]: x for x in marks}
        hits = [x for x in marks if x["holding_sessions"] >= 1 and x["pnl_usd"] is not None and x["pnl_usd"] >= 1000]
        if hits:
            hit = hits[0]
            group = fast if hit["holding_sessions"] <= EARLY_WIN_DAYS else late
            for horizon in (5, 10):
                future = by_age.get(hit["holding_sessions"] + horizon)
                delta = None if future is None or future["pnl_usd"] is None else future["pnl_usd"] - hit["pnl_usd"]
                if delta is not None:
                    group.append({"delta": delta, "future_pnl": future["pnl_usd"], "hit_pnl": hit["pnl_usd"], "horizon": horizon})
            event_rows.append({"trade_id": trade["trade_id"], "event": "EOD_MARK_FIRST_REACHES_PLUS_1000", "event_date": hit["date"], "age_sessions": hit["holding_sessions"], "pnl_usd": hit["pnl_usd"]})
        d20 = by_age.get(NO_PROFIT_DAYS)
        if d20 and d20["pnl_usd"] is not None:
            group = day20_loss if d20["pnl_usd"] <= 0 else day20_profit
            for horizon in (5, 10):
                future = by_age.get(NO_PROFIT_DAYS + horizon)
                if future and future["pnl_usd"] is not None:
                    group.append({"delta": future["pnl_usd"] - d20["pnl_usd"], "future_pnl": future["pnl_usd"], "day20_pnl": d20["pnl_usd"], "horizon": horizon})
            event_rows.append({"trade_id": trade["trade_id"], "event": "DAY20_NONPOSITIVE" if d20["pnl_usd"] <= 0 else "DAY20_POSITIVE", "event_date": d20["date"], "age_sessions": NO_PROFIT_DAYS, "pnl_usd": d20["pnl_usd"]})

    def group_summary(items, base_key):
        out = {}
        for horizon in (5, 10):
            xs = [x for x in items if x["horizon"] == horizon]
            pnl = [x["delta"] for x in xs]
            future = [x["future_pnl"] for x in xs]
            base = [x.get(base_key, x.get("hit_pnl", 0)) for x in xs]
            out[str(horizon) + "_session_forward"] = {
                "n": len(xs), "median_pnl_change_usd": statistics.median(pnl) if pnl else None,
                "mean_pnl_change_usd": round(sum(pnl)/len(pnl), 2) if pnl else None,
                "fraction_future_pnl_nonpositive": round(sum(1 for x in future if x <= 0)/len(future), 4) if future else None,
                "fraction_pnl_giveback_ge_50pct_of_1000_target": round(sum(1 for x in xs if x["delta"] <= -500)/len(xs), 4) if xs else None,
                "future_pnl_distribution_usd": _distribution(future),
            }
        return out

    return {
        "cost_convention": {"slippage_per_leg_usd": BASE_EVENT_SLIPPAGE, "commission_per_contract_per_side_usd": BASE_EVENT_COMMISSION},
        "critical_timing_caveat": "Threshold events are EOD quote-mark events, not intraday threshold touches. Source reports 16:00 ET; exact tick timestamp and fill availability are unverified.",
        "plus_1000_events_total": len([x for x in event_rows if x["event"] == "EOD_MARK_FIRST_REACHES_PLUS_1000"]),
        "plus_1000_first_hit_within_5_sessions": len([x for x in event_rows if x["event"] == "EOD_MARK_FIRST_REACHES_PLUS_1000" and x["age_sessions"] <= EARLY_WIN_DAYS]),
        "plus_1000_first_hit_after_5_sessions": len([x for x in event_rows if x["event"] == "EOD_MARK_FIRST_REACHES_PLUS_1000" and x["age_sessions"] > EARLY_WIN_DAYS]),
        "early_1000_then_hold_original_1x5": group_summary(fast, "hit_pnl"),
        "late_1000_then_hold_original_1x5": group_summary(late, "hit_pnl"),
        "day20_nonpositive_then_hold_original_1x5": group_summary(day20_loss, "day20_pnl"),
        "day20_positive_then_hold_original_1x5": group_summary(day20_profit, "day20_pnl"),
        "events": event_rows,
        "interpretation_rule": "These are conditional historical diagnostics, not causal proof or a forecast; small event counts remain inconclusive.",
    }


def build_report(trades: list[dict[str, Any]], generation: dict[str, Any], source_integrity: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not trades:
        report = {
            "research_id": "QQQ_PUT_RATIO_EXIT_MEASUREMENT_V1", "status": "NO_ELIGIBLE_TRADES",
            "source_integrity": source_integrity, "generation": generation, "trades": 0,
            "limitations": ["No trade was opened; no exit rule or performance metric is promoted."],
        }
        return report, [], [], {"events": []}
    policies = policy_list()
    per_trade, summaries = [], []
    for slip in SLIPPAGE_PER_LEG_USD:
        for commission in COMMISSION_PER_CONTRACT_PER_SIDE_USD:
            for policy in policies:
                results = [simulate_policy(t, policy, slip, commission) for t in trades]
                for row in results:
                    row["source_evidence"] = "PUBLIC_EOD_PRESERVATION_MIRROR; DERIVED_SIDE_PRICE_REPLAY; NOT_CONFIRMED_FILLS"
                    per_trade.append(row)
                summaries.append(summarize_policy(results))
    base_rows = [x for x in summaries if x["slippage_per_leg_usd"] == BASE_EVENT_SLIPPAGE and x["commission_per_contract_per_side_usd"] == BASE_EVENT_COMMISSION]
    events = summarize_events(trades)
    risks = []
    for trade in trades:
        cash = entry_cashflow(trade, BASE_EVENT_SLIPPAGE, BASE_EVENT_COMMISSION)
        risks.append({"trade_id": trade["trade_id"], **terminal_risk(trade, cash)})
    tail_losses = [x["terminal_tail_loss_if_qqq_zero_usd"] for x in risks]
    max_tail = max(tail_losses) if tail_losses else 0
    median_tail = statistics.median(tail_losses) if tail_losses else 0
    mark_cov = generation.get("source_coverage", {})
    report = {
        "research_id": "QQQ_PUT_RATIO_EXIT_MEASUREMENT_V1",
        "status": "DEVELOPMENT_DIAGNOSTIC_NOT_LIVE_APPROVAL",
        "window": {"start": START_DATE, "source_end": SOURCE_END_DATE, "requested_end": REQUESTED_END_DATE},
        "structure": {
            "long_contracts": LONG_QTY, "short_contracts": SHORT_QTY,
            "long_leg": f"standard QQQ put, abs(delta) nearest {LONG_ABS_DELTA_TARGET:.2f} in {LONG_ABS_DELTA_RANGE}, strike above short put",
            "short_leg": f"5 standard QQQ puts, abs(delta) nearest {SHORT_ABS_DELTA_TARGET:.2f} in {SHORT_ABS_DELTA_RANGE}, same expiry, lower strike",
            "signal_dte": f"{DTE_MIN}–{DTE_MAX} calendar days, target {DTE_TARGET}",
            "entry_alignment": "Select contracts from session t snapshot; use only those same IDs at session t+1 snapshot; no replacement if quote/size is invalid.",
            "position_cadence": "Fixed, non-overlapping expiry-spaced cohort so exit policies share identical entry episodes; not a continuous re-entry portfolio strategy.",
            "reference_nav_usd": REFERENCE_NAV_USD, "reference_nav_note": "Normalization only; not verified current account NAV.",
            "multiplier": CONTRACT_MULTIPLIER,
        },
        "source_evidence": {
            "class": "PUBLIC_EOD_PRESERVATION_MIRROR / OBSERVED_QUOTE_SIDES / DERIVED_REPLAY",
            "source_url": "https://github.com/anahatsingh-ui/options-dataset-hist",
            "source_snapshot_time": "README reports 16:00 US/Eastern; exact tick timestamp unverified",
            "execution_claim": "No exchange-confirmed fill data; EOD option marks do not prove intraday executable trades.",
            "source_ends": SOURCE_END_DATE,
            "prior_exposure": "2018–2025 already inspected in prior repository research; DEVELOPMENT/REVISIT, not untouched holdout.",
            "source_integrity": source_integrity,
        },
        "generation": generation,
        "risk_summary_base_cost": {
            "base_slippage_per_leg_usd": BASE_EVENT_SLIPPAGE,
            "base_commission_per_contract_per_side_usd": BASE_EVENT_COMMISSION,
            "trade_count": len(risks), "median_tail_loss_if_qqq_zero_usd": round(median_tail, 2),
            "max_tail_loss_if_qqq_zero_usd": round(max_tail, 2),
            "median_tail_loss_pct_reference_nav": round(100*median_tail/REFERENCE_NAV_USD, 4),
            "max_tail_loss_pct_reference_nav": round(100*max_tail/REFERENCE_NAV_USD, 4),
            "tail_budget_capacity_0p5pct_nav_units": sum(x["whole_ratio_units_under_0p5pct_nav_tail_budget"] for x in risks)/len(risks),
            "tail_budget_capacity_1pct_nav_units": sum(x["whole_ratio_units_under_1pct_nav_tail_budget"] for x in risks)/len(risks),
            "tail_budget_capacity_2pct_nav_units": sum(x["whole_ratio_units_under_2pct_nav_tail_budget"] for x in risks)/len(risks),
            "required_nav_for_one_unit_at_1pct_tail_budget_median_usd": round(statistics.median([x["required_reference_nav_for_1pct_tail_budget_usd"] for x in risks]), 2),
            "one_unit_feasibility_for_100k_reference_nav": "BLOCKED if any one-unit terminal zero-price loss exceeds 100% of reference NAV; exact broker initial/maintenance margin remains UNKNOWN.",
            "risk_rows": risks,
        },
        "policy_summaries": summaries,
        "policy_summaries_base_cost": base_rows,
        "event_study": events,
        "performance_gate": "BLOCKED_FOR_DEPLOYMENT: EOD timing/fills unverified, broker margin/assignment costs unavailable, one-unit 1x5 tail risk may exceed reference NAV, and history is previously inspected development data.",
        "limitations": [
            "This is a short-ratio put structure: one higher-strike long put only offsets one of the five lower-strike short puts. The remaining four short puts create severe downside exposure.",
            "Zero-underlying tail loss is terminal intrinsic arithmetic; it does not model interim volatility expansion, margin calls, forced liquidation, execution gaps, or broker-specific margin.",
            "All exit triggers are EOD quote-mark rules; the dataset does not establish intraday touches or fills.",
            "Missing option marks are never forward-filled. A missing quote can defer a close action; unresolved trades do not enter closed-P&L totals.",
            "Intrinsic expiry settlement is a proxy before broker exercise/assignment fees, taxes, or operational frictions.",
            "No app capacity, Frozen Original Hybrid, main branch, or broker-order permission was modified.",
        ],
    }
    return report, summaries, per_trade, events


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = []
    for row in rows:
        for key in row:
            if key not in keys and key not in ("actions", "daily", "terminal_intrinsic_stress_scenarios_usd"):
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def render_markdown(report: dict[str, Any]) -> str:
    gen = report.get("generation", {})
    lines = [
        "# QQQ 1x5 Put Ratio Exit Measurement — V1",
        "",
        f"**Status:** `{report.get('status')}`  ",
        f"**Window:** {START_DATE} to {SOURCE_END_DATE} (requested end {REQUESTED_END_DATE}; source is incomplete after Dec 15, 2025)  ",
        "**Evidence:** public EOD preservation mirror / conservative quote-side replay; not confirmed fills.  ",
        f"**Entry episodes:** {gen.get('opened_trade_episodes', 0)}; selection skips: {gen.get('skip_counts', {})}",
        "",
        "## Frozen test definition",
        "",
        "- On session *t*, choose one standard QQQ put near abs(Delta) 0.30 and five standard lower-strike puts near abs(Delta) 0.10, same expiry, 30–60 DTE (target 45).",
        "- Use exact listed contract IDs at *t+1* for entry; long buy at Ask, five shorts sold at Bid; if quote/depth is invalid, skip rather than replace the legs.",
        "- Exit actions are based on EOD side marks only. Short-put closure buys back at Ask; risk-trim buys back four of five shorts and leaves a 1x1 defined-risk vertical. A residual long put can remain open if no positive Bid is available.",
        "- Same entry episodes for every rule, non-overlapping by expiry, fixed one-unit sizing. This isolates exit-rule effects; it is not a continuous re-entry portfolio simulation.",
        "- Session age is the observed replay index since entry (entry-date mark is age 0). The policy-trigger count/rate distinguishes a custom rule firing from the shared DTE<=7 safety fallback; signal-to-action delay counts observed trading sessions to the first successful risk-reducing action.",
        "- Net P&L per short-risk-equivalent session divides resolved after-cost P&L by the sum of each observed session weighted by remaining short contracts / original five shorts. This is a descriptive holding-time denominator only—not annualized return, risk-adjusted return, or a substitute for the tail-loss / mark-coverage / cost gates.",
        "",
        "## Base cost case: $0.05 per leg per side + $0.65 per contract per side",
        "",
        "| Exit rule | Resolved | Net P&L | Expectancy / trade | Policy trigger N / % | Median trigger age | Median first-action age | Median resolution age | Net P&L / short-risk eq-session | Win rate | Profit factor | Missing marks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in report.get("policy_summaries_base_cost", []):
        trigger_age = s["policy_rule_trigger_age_sessions_distribution"]["median"]
        action_age = s["first_risk_action_age_sessions_distribution"]["median"]
        resolution_age = s["resolved_holding_age_sessions_distribution"]["median"]
        trigger_text = f"{s['policy_rule_triggered_trade_count']}/{s['trade_episodes']} ({s['policy_rule_trigger_rate_pct']}%)"
        delay = s["signal_to_first_action_delay_sessions_distribution"]["median"]
        exposure_rate = s["net_pnl_per_short_risk_equivalent_session_usd"]
        # These elapsed-session metrics are descriptive; age 0 is the entry-date observation.
        lines.append(f"| {s['policy']} | {s['resolved_trades']}/{s['trade_episodes']} | {s['closed_trade_net_pnl_sum_usd']} | {s['expectancy_usd_per_resolved_trade']} | {trigger_text} | {trigger_age if trigger_age is not None else '—'} | {delay if delay is not None else '—'} | {resolution_age if resolution_age is not None else '—'} | {exposure_rate if exposure_rate is not None else '—'} | {s['win_rate']} | {s['profit_factor']} | {s['total_missing_mark_sessions']} |")
    rs = report.get("risk_summary_base_cost", {})
    lines += [
        "", "## Tail-risk and dollars-to-risk ratio", "",
        f"- Median terminal loss if QQQ reaches $0: **${rs.get('median_tail_loss_if_qqq_zero_usd')}** ({rs.get('median_tail_loss_pct_reference_nav')}% of the $100,000 reference NAV).",
        f"- Maximum observed selected-trade terminal loss if QQQ reaches $0: **${rs.get('max_tail_loss_if_qqq_zero_usd')}** ({rs.get('max_tail_loss_pct_reference_nav')}% of reference NAV).",
        f"- Median reference NAV needed for one 1x5 unit to fit a 1% terminal tail-risk budget: **${rs.get('required_nav_for_one_unit_at_1pct_tail_budget_median_usd')}**. This is terminal payoff arithmetic, not a broker margin figure.",
        "- $500 / $1,000 / $2,000 are also 0.5% / 1% / 2% of the $100,000 reference NAV, but those profit/loss thresholds are not inherently optimal. Compare each against the much larger terminal tail loss and the after-cost trade distribution.",
        "", "## Conditional event study (base costs; EOD marks)", "",
        f"- First EOD mark at +$1,000: {report.get('event_study', {}).get('plus_1000_events_total')} events; within 5 sessions: {report.get('event_study', {}).get('plus_1000_first_hit_within_5_sessions')}; later than 5 sessions: {report.get('event_study', {}).get('plus_1000_first_hit_after_5_sessions')}.",
        f"- Early +$1,000 then hold the original 1x5: {json.dumps(report.get('event_study', {}).get('early_1000_then_hold_original_1x5', {}), ensure_ascii=False)}",
        f"- Day-20 non-positive then hold the original 1x5: {json.dumps(report.get('event_study', {}).get('day20_nonpositive_then_hold_original_1x5', {}), ensure_ascii=False)}",
        f"- Day-20 positive comparison group: {json.dumps(report.get('event_study', {}).get('day20_positive_then_hold_original_1x5', {}), ensure_ascii=False)}",
        "", "## Decision gates", "",
        "- **No `WIN $1,000` rule is accepted just because it is round.** Compare after-cost expectancy, giveback after threshold, risk reduced by closing/trim, action execution coverage, and return per unit of tail loss.",
        "- **A +$1,000 EOD mark within 5 sessions is not automatically a warning.** It is a warning only if the event cohort shows systematically worse subsequent giveback / loss than later +$1,000 events, with enough observations and consistent quote coverage.",
        "- **No profit by day 20 is not automatically bearish or failure.** It is informative only if the 5-/10-session forward conditional outcomes differ from trades already profitable on day 20. Missing marks are censored, not assumed flat.",
        f"- Deployment gate: **{report.get('performance_gate')}**",
        "", "## Data integrity / caveats", "",
    ]
    for s in report.get("limitations", []):
        lines.append(f"- {s}")
    return "\n".join(lines) + "\n"


def run_source_replay(out_dir: Path) -> dict[str, Any]:
    sys.path.insert(0, str(SOURCE_DIR))
    import full_history_qqq_quote_audit as audit
    import qqq_far_call_quote_replay as source_replay

    cache = ROOT / ".cache" / "qqq-options-full-history"
    integrity, universe_by_day, spots, expected = audit.build_inputs(cache)
    expected = sorted(d for d in expected if START_DATE <= d <= SOURCE_END_DATE)
    expected_set = set(expected)
    option_paths, file_integrity = [], {}
    for spec in audit.ANNUAL_FILES:
        path, meta = audit.download_verified(spec, cache)
        option_paths.append(path)
        file_integrity[spec["name"]] = meta
    source_integrity = {"underlying_and_repo_source_pins": integrity, "annual_option_files": file_integrity}
    chain_iter = iter(source_replay.iter_qqq_chain_days(option_paths))
    next_chain = next(chain_iter, None)
    episodes: list[dict[str, Any]] = []
    active = None
    pending = None
    last_expiry = None
    stats: dict[str, Any] = {"expected_sessions_to_source_end": len(expected), "sessions_with_option_chain": 0, "option_rows": 0, "opened_trade_episodes": 0, "entry_skip_counts": Counter(), "selection_status_counts": Counter(), "observed_last_chain_date": None}

    for session_day in expected:
        while next_chain is not None and next_chain[0] < session_day:
            next_chain = next(chain_iter, None)
        if next_chain is not None and next_chain[0] == session_day:
            rows = next_chain[1]
            next_chain = next(chain_iter, None)
            stats["sessions_with_option_chain"] += 1
            stats["option_rows"] += len(rows)
            stats["observed_last_chain_date"] = session_day
        else:
            rows = []
        spot_data = spots.get(session_day) or {}
        raw_spot = num(spot_data.get("raw_close"))
        vix = (universe_by_day.get(session_day) or {}).get("vix")

        if pending is not None and active is None:
            quotes, status = entry_quotes(pending, rows, session_day) if rows else (None, "NEXT_SESSION_CHAIN_MISSING")
            if quotes is not None and raw_spot is not None:
                active = {
                    **pending, "trade_id": len(episodes) + 1, "entry_date": session_day,
                    "entry_quotes": quotes, "spot_entry": raw_spot, "vix_entry": vix,
                    "path": [],
                }
                stats["opened_trade_episodes"] += 1
                pending = None
            else:
                stats["entry_skip_counts"][status if quotes is None else "ENTRY_RAW_SPOT_MISSING"] += 1
                pending = None

        if active is not None:
            qmap = quote_map(rows)
            long_row = qmap.get(active["long_id"])
            short_row = qmap.get(active["short_id"])
            long_row = dict(long_row) if long_row is not None else None
            short_row = dict(short_row) if short_row is not None else None
            active["path"].append({
                "date": session_day, "dte": (date.fromisoformat(active["expiry"]) - date.fromisoformat(session_day)).days,
                "long": long_row, "short": short_row, "spot": raw_spot, "vix": vix,
            })
            if session_day == active["expiry"]:
                episodes.append(active)
                last_expiry = active["expiry"]
                active = None
            elif date.fromisoformat(session_day) > date.fromisoformat(active["expiry"]):
                raise ValueError(f"Trade {active['trade_id']} crossed expiry without settlement: {session_day} > {active['expiry']}")

        if active is None and pending is None and (last_expiry is None or session_day > last_expiry):
            if not rows or raw_spot is None or vix is None:
                continue
            pair = choose_ratio_put(rows, session_day, expected_set, audit.base.standard_strike_grid)
            stats["selection_status_counts"][pair["status"]] += 1
            if pair.get("status") == "PAIR_SELECTED":
                if pair["expiry"] > SOURCE_END_DATE or pair["expiry"] not in expected_set:
                    stats["entry_skip_counts"]["EXPIRY_OUTSIDE_VERIFIED_WINDOW"] += 1
                else:
                    pending = pair

    if active is not None:
        stats["entry_skip_counts"]["OPEN_POSITION_WITHOUT_SOURCE_EXPIRY"] += 1
    if stats["observed_last_chain_date"] != SOURCE_END_DATE:
        raise ValueError(f"Pinned source terminal-date mismatch: observed {stats['observed_last_chain_date']}, expected {SOURCE_END_DATE}")
    stats["entry_skip_counts"] = dict(stats["entry_skip_counts"])
    stats["selection_status_counts"] = dict(stats["selection_status_counts"])
    stats["source_coverage"] = {
        "expected_sessions_to_2025_12_15": len(expected),
        "sessions_with_chain": stats["sessions_with_option_chain"],
        "chain_session_coverage_pct": round(100*stats["sessions_with_option_chain"]/len(expected), 4) if expected else None,
        "last_chain_date": stats["observed_last_chain_date"],
        "universe_expected_sessions_after_source_end_to_requested_end": 11,
        "missing_chain_sessions_not_filled": len(expected) - stats["sessions_with_option_chain"],
    }
    report, summaries, per_trade, events = build_report(episodes, stats, source_integrity)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "qqq_put_ratio_exit_study_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "qqq_put_ratio_exit_study_summary.md").write_text(render_markdown(report), encoding="utf-8")
    _write_csv(out_dir / "qqq_put_ratio_exit_policy_summary.csv", summaries)
    _write_csv(out_dir / "qqq_put_ratio_exit_policy_trades.csv", per_trade)
    (out_dir / "qqq_put_ratio_exit_event_study.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "qqq_put_ratio_exit_study_v1")
    args = parser.parse_args()
    report = run_source_replay(args.out)
    print(json.dumps({
        "research_id": report.get("research_id"), "status": report.get("status"),
        "generation": report.get("generation"), "risk_summary_base_cost": {k:v for k,v in (report.get("risk_summary_base_cost") or {}).items() if k != "risk_rows"},
        "base_cost_policy_summaries": report.get("policy_summaries_base_cost"),
        "event_study": {k:v for k,v in (report.get("event_study") or {}).items() if k != "events"},
        "performance_gate": report.get("performance_gate"), "output_dir": str(args.out),
    }, indent=2))
    print((args.out / "qqq_put_ratio_exit_study_summary.md").read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
