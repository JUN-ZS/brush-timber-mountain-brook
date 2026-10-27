#!/usr/bin/env python3
"""Account cash, Reg-T-style margin proxy, entry gating, and EOD liquidation replay.

This is a hypothetical broker-capacity model, not an actual brokerage margin engine.
It replays the already-accepted DTE20 / exit-DTE<=4 QQQ/SPY PUT+CALL legs and does
not rerun or retune the underlying strategy.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

PUT_ENGINE_DIR = Path("research/qqq_spy_put_fixed_ratio_size_gated_v1").resolve()
if str(PUT_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PUT_ENGINE_DIR))
import qqq_spy_put_premium_matched_phase_v1 as put_engine  # noqa: E402

DATA_ROOT = Path(
    "research/qqq_spy_call_fixed_ratio_size_gated_v1/results/"
    "dte_hold_exit_factorial_call_v1/daily_nav_dte20_exit4_v1"
)
OUT = DATA_ROOT / "account_feasibility_v1"
REPLAY_ROOT = DATA_ROOT / "replay"
POLICY = "EXIT_AT_DTE_LE_4"
PHASES = (0, 2, 4, 6, 8)
MULTIPLIER = 100.0
SLIPPAGE_PER_SHARE = 0.05
COMMISSION_PER_CONTRACT_PER_SIDE = 0.65
UNIT_COST_PER_CONTRACT_PER_SIDE = SLIPPAGE_PER_SHARE * MULTIPLIER + COMMISSION_PER_CONTRACT_PER_SIDE
DEFAULT_CAPITALS = (100000.0, 250000.0, 500000.0, 750000.0, 1000000.0)
DEFAULT_MARGIN_MULTIPLIERS = (1.0, 1.5, 2.0)

# Hypothetical spot shocks. Extrinsic multipliers are explicit scenario assumptions,
# not observed implied-volatility forecasts.
STRESS_SCENARIOS = (
    {"name": "broad_down_10", "qqq_return": -0.10, "spy_return": -0.10, "extrinsic_multiplier": 1.5},
    {"name": "broad_down_20", "qqq_return": -0.20, "spy_return": -0.20, "extrinsic_multiplier": 2.0},
    {"name": "broad_down_30", "qqq_return": -0.30, "spy_return": -0.30, "extrinsic_multiplier": 2.5},
    {"name": "broad_down_50", "qqq_return": -0.50, "spy_return": -0.50, "extrinsic_multiplier": 3.0},
    {"name": "broad_up_10", "qqq_return": 0.10, "spy_return": 0.10, "extrinsic_multiplier": 0.9},
    {"name": "broad_up_20", "qqq_return": 0.20, "spy_return": 0.20, "extrinsic_multiplier": 0.8},
    {"name": "broad_up_30", "qqq_return": 0.30, "spy_return": 0.30, "extrinsic_multiplier": 0.7},
    {"name": "broad_up_50", "qqq_return": 0.50, "spy_return": 0.50, "extrinsic_multiplier": 0.6},
    {"name": "broad_up_100", "qqq_return": 1.00, "spy_return": 1.00, "extrinsic_multiplier": 0.5},
    {"name": "qqq_down_more_than_spy", "qqq_return": -0.40, "spy_return": -0.20, "extrinsic_multiplier": 2.5},
    {"name": "spy_up_more_than_qqq", "qqq_return": 0.10, "spy_return": 0.30, "extrinsic_multiplier": 0.7},
)


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def daystr(value):
    return str(value or "")[:10]


def normalize_contract_id(value):
    text = "".join(str(value or "").strip().upper().split())
    return text[2:] if text.startswith("O:") else text


def bool_value(value):
    return str(value or "").strip().lower() in ("true", "1", "yes")


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    if not fields:
        fields = ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def option_intrinsic(right, spot, strike):
    if str(right).upper() == "P":
        return max(float(strike) - float(spot), 0.0)
    return max(float(spot) - float(strike), 0.0)


def naked_stock_option_margin_per_contract(right, spot, strike, option_mark, qty=1):
    """IBKR-published stock-option formula, independently applied per short leg.

    Requirement = option mark + max(20% spot - OTM amount, 10% spot for calls
    or 10% strike for puts), multiplied by 100 and contract quantity.
    No cross-leg/portfolio offsets are credited.
    """
    spot, strike, option_mark = float(spot), float(strike), float(option_mark)
    right = str(right).upper()
    if spot <= 0 or strike <= 0 or option_mark < 0 or int(qty) < 0:
        raise ValueError("invalid margin inputs")
    if right == "C":
        otm = max(strike - spot, 0.0)
        floor = 0.10 * spot
    elif right == "P":
        otm = max(spot - strike, 0.0)
        floor = 0.10 * strike
    else:
        raise ValueError(f"unknown option right: {right}")
    core = max(0.20 * spot - otm, floor)
    return (option_mark + core) * MULTIPLIER * int(qty)


def entry_cash_delta(position):
    sign = 1.0 if position["position_side"] == "LONG" else -1.0
    return -sign * position["entry_price"] * MULTIPLIER * position["qty"] - UNIT_COST_PER_CONTRACT_PER_SIDE * position["qty"]


def exit_cash_delta(position):
    if position["exit_price"] is None:
        raise RuntimeError(f"resolved leg has no exit price: {position['position_id']}")
    sign = 1.0 if position["position_side"] == "LONG" else -1.0
    return sign * position["exit_price"] * MULTIPLIER * position["qty"] - UNIT_COST_PER_CONTRACT_PER_SIDE * position["qty"]


def settlement_cash_delta(position, spot):
    sign = 1.0 if position["position_side"] == "LONG" else -1.0
    intrinsic = option_intrinsic(position["right"], spot, position["strike"])
    return sign * intrinsic * MULTIPLIER * position["qty"]


def mark_row_is_open(row):
    return bool_value(row.get("is_open_eod"))


def position_key_from_mark(row):
    return (
        int(float(row["phase_sessions"])), str(row["strategy"]).upper(),
        daystr(row["signal_date"]), daystr(row["expiry"]), str(row["leg_name"]).upper(),
        normalize_contract_id(row["contract_id"]), daystr(row["entry_date"]),
    )


def trade_key(phase, strategy, row, contract_id):
    return (
        int(phase), str(strategy).upper(), daystr(row.get("signal_date")),
        daystr(row.get("expiry")), daystr(row.get("entry_date")), normalize_contract_id(contract_id),
    )


def load_trade_lookup():
    lookup = {}
    for phase in PHASES:
        for strategy in ("PUT", "CALL"):
            path = REPLAY_ROOT / strategy.lower() / f"phase_{phase}" / "trade_episodes.csv"
            if not path.is_file():
                raise FileNotFoundError(f"required source replay missing: {path}")
            for row in read_csv(path):
                if row.get("policy") != POLICY or not row.get("entry_date"):
                    continue
                for leg_name, contract_field in (
                    ("QQQ_LONG", "qqq_contract_id"), ("SPY_SHORT", "spy_contract_id")
                ):
                    key = trade_key(phase, strategy, row, row.get(contract_field))
                    if key in lookup:
                        raise RuntimeError(f"duplicate source trade identity: {key}")
                    lookup[key] = (row, leg_name)
    return lookup


def load_positions_and_marks():
    mark_path = DATA_ROOT / "daily_option_leg_marks.csv"
    daily_path = DATA_ROOT / "daily_nav_by_phase.csv"
    audit_path = DATA_ROOT / "daily_nav_max_drawdown_audit.json"
    for path in (mark_path, daily_path, audit_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"missing required completed NAV artifact: {path}")

    daily_rows = read_csv(daily_path)
    if not daily_rows:
        raise RuntimeError("daily NAV input is empty")
    daily_by_phase_day = {}
    for row in daily_rows:
        key = (int(float(row["phase_sessions"])), daystr(row["date"]))
        if key in daily_by_phase_day:
            raise RuntimeError(f"duplicate daily NAV row: {key}")
        daily_by_phase_day[key] = row

    raw_marks = read_csv(mark_path)
    if not raw_marks:
        raise RuntimeError("daily option-leg marks input is empty")
    mark_groups = defaultdict(list)
    marks_by_group_day = {}
    for row in raw_marks:
        key = position_key_from_mark(row)
        day = daystr(row["date"])
        if (key, day) in marks_by_group_day:
            raise RuntimeError(f"duplicate daily mark: {key} {day}")
        marks_by_group_day[(key, day)] = row
        mark_groups[key].append(row)

    trade_lookup = load_trade_lookup()
    positions = []
    marks_by_position_day = {}
    for index, (key, rows) in enumerate(sorted(mark_groups.items()), 1):
        phase, strategy, signal_date, expiry, leg_name, contract_id, entry_date = key
        first = rows[0]
        trade_id = (phase, strategy, signal_date, expiry, entry_date, contract_id)
        if trade_id not in trade_lookup:
            raise RuntimeError(f"daily mark has no source replay trade: {trade_id}")
        trade, source_leg_name = trade_lookup[trade_id]
        if source_leg_name != leg_name:
            raise RuntimeError(f"source leg mismatch for {trade_id}: {source_leg_name} != {leg_name}")

        if leg_name == "QQQ_LONG":
            entry_price = number(trade.get("qqq_entry_ask"))
            exit_price = number(trade.get("exit_qqq_bid"))
            qty_expected = int(float(trade.get("long_qqq_qty") or 0))
            symbol = "QQQ"
        else:
            entry_price = number(trade.get("spy_entry_bid"))
            exit_price = number(trade.get("exit_spy_ask"))
            qty_expected = int(float(trade.get("short_spy_qty") or 0))
            symbol = "SPY"
        qty = int(float(first.get("qty") or 0))
        if not contract_id or qty < 1 or qty != qty_expected or entry_price is None or entry_price <= 0:
            raise RuntimeError(f"invalid source quantity/entry price for {trade_id}")

        status = str(trade.get("status") or "")
        resolved = status.upper() == "RESOLVED"
        if resolved and (not trade.get("exit_date") or exit_price is None):
            raise RuntimeError(f"resolved trade lacks actual exit fill side: {trade_id}")
        settlement_days = sorted({
            daystr(row.get("date")) for row in rows
            if row.get("valuation_method") == "EXPIRY_INTRINSIC_SETTLEMENT_PROXY"
        })
        if len(settlement_days) > 1:
            raise RuntimeError(f"multiple expiry settlement marks for {trade_id}: {settlement_days}")
        settlement_date = settlement_days[0] if settlement_days else ""
        if resolved and settlement_date:
            raise RuntimeError(f"resolved trade also has expiry settlement proxy: {trade_id}")

        position_id = f"p{index:05d}"
        position = {
            "position_id": position_id, "phase_sessions": phase, "strategy": strategy,
            "signal_date": signal_date, "expiry": expiry, "leg_name": leg_name,
            "contract_id": contract_id, "entry_date": entry_date, "symbol": symbol,
            "right": str(first.get("right") or "").upper(),
            "position_side": str(first.get("position_side") or "").upper(),
            "qty": qty, "strike": float(number(first.get("strike"))),
            "entry_price": float(entry_price), "status": status, "resolved": resolved,
            "exit_date": daystr(trade.get("exit_date")) if resolved else "",
            "exit_price": float(exit_price) if resolved else None,
            "settlement_date": settlement_date,
            "basket_id": f"{phase}|{signal_date}|{entry_date}|{expiry}",
        }
        if position["position_side"] not in ("LONG", "SHORT") or position["right"] not in ("P", "C"):
            raise RuntimeError(f"invalid option side/right for {trade_id}")
        if position["strike"] <= 0:
            raise RuntimeError(f"invalid strike for {trade_id}")
        positions.append(position)
        for row in rows:
            marks_by_position_day[(position_id, daystr(row["date"]))] = row

    by_phase = defaultdict(list)
    for position in positions:
        by_phase[position["phase_sessions"]].append(position)

    baskets_by_phase_day = defaultdict(list)
    basket_members = defaultdict(list)
    for position in positions:
        basket_members[(position["phase_sessions"], position["basket_id"])].append(position)
    for (phase, basket_id), members in basket_members.items():
        expected = {
            ("PUT", "QQQ_LONG"), ("PUT", "SPY_SHORT"),
            ("CALL", "QQQ_LONG"), ("CALL", "SPY_SHORT"),
        }
        actual = {(p["strategy"], p["leg_name"]) for p in members}
        if len(members) != 4 or actual != expected:
            raise RuntimeError(f"matched basket must contain exactly four legs: {phase}/{basket_id} {actual}")
        entry_date = members[0]["entry_date"]
        if any(p["entry_date"] != entry_date for p in members):
            raise RuntimeError(f"basket members have different actual entry dates: {basket_id}")
        baskets_by_phase_day[(phase, entry_date)].append(sorted(members, key=lambda p: (p["strategy"], p["leg_name"])))

    phase_days = {}
    for phase in PHASES:
        rows = sorted((r for (p, _), r in daily_by_phase_day.items() if p == phase), key=lambda r: daystr(r["date"]))
        if not rows:
            raise RuntimeError(f"daily NAV missing phase {phase}")
        phase_days[phase] = rows
        if len(rows) != len({daystr(r["date"]) for r in rows}):
            raise RuntimeError(f"duplicate daily calendar session in phase {phase}")

    audit_source = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit_source.get("status") != "PASS":
        raise RuntimeError("source daily NAV audit is not PASS")
    expected_daily = int(audit_source.get("daily_nav_rows_expected") or 0)
    expected_leg_marks = int((audit_source.get("daily_leg_mark_coverage") or {}).get("expected_daily_leg_mark_rows") or 0)
    if expected_daily and len(daily_rows) != expected_daily:
        raise RuntimeError(f"daily NAV row count differs from source audit: {len(daily_rows)} != {expected_daily}")
    if expected_leg_marks and len(raw_marks) != expected_leg_marks:
        raise RuntimeError(f"daily leg-mark row count differs from source audit: {len(raw_marks)} != {expected_leg_marks}")
    return positions, marks_by_position_day, phase_days, daily_by_phase_day, baskets_by_phase_day, audit_source, by_phase


def load_underlying_spots():
    cache = Path.home() / ".cache" / "qqq-spy-pair-daily-nav-v1"
    path, integrity = put_engine.download_verified("SPY", None, cache / "spy")
    spots = put_engine.load_spots(path, "SPY")
    if not spots:
        raise RuntimeError("verified SPY underlying history is empty")
    return spots, integrity


def signed_position_value(position, mark_price):
    sign = 1.0 if position["position_side"] == "LONG" else -1.0
    return sign * float(mark_price) * MULTIPLIER * position["qty"]


def mark_for(position, day, marks_by_position_day):
    row = marks_by_position_day.get((position["position_id"], day))
    if row is None or not mark_row_is_open(row):
        raise RuntimeError(f"missing/open=false daily mark for active leg {position['position_id']} on {day}")
    mark = number(row.get("mark_price"))
    if mark is None or mark < 0:
        raise RuntimeError(f"invalid daily liquidation-side mark for {position['position_id']} on {day}")
    return row, float(mark)


def compute_state(active, cash, stock_value, day, spots, marks_by_position_day, margin_multiplier):
    option_market_value = 0.0
    close_costs = 0.0
    naked_option_margin = 0.0
    put_obligation = 0.0
    call_delivery_notional = 0.0
    call_intrinsic_liability = 0.0
    open_short_calls = 0
    stale_legs = 0
    max_stale_age = 0

    for position in active.values():
        row, mark = mark_for(position, day, marks_by_position_day)
        option_market_value += signed_position_value(position, mark)
        close_costs += UNIT_COST_PER_CONTRACT_PER_SIDE * position["qty"]
        if "STALE" in str(row.get("valuation_method") or ""):
            stale_legs += 1
            max_stale_age = max(max_stale_age, int(float(row.get("quote_age_sessions") or 0)))
        if position["symbol"] == "SPY" and position["position_side"] == "SHORT":
            spot = number(spots.get(day))
            if spot is None or spot <= 0:
                raise RuntimeError(f"SPY spot missing on active option day {day}")
            naked_option_margin += naked_stock_option_margin_per_contract(
                position["right"], spot, position["strike"], mark, position["qty"]
            )
            if position["right"] == "P":
                put_obligation += position["strike"] * MULTIPLIER * position["qty"]
            else:
                call_delivery_notional += position["strike"] * MULTIPLIER * position["qty"]
                call_intrinsic_liability += option_intrinsic("C", spot, position["strike"]) * MULTIPLIER * position["qty"]
                open_short_calls += position["qty"]

    equity = float(cash) + float(stock_value) + option_market_value - close_costs
    initial_req = 0.50 * float(stock_value) + float(margin_multiplier) * naked_option_margin
    maintenance_req = 0.25 * float(stock_value) + float(margin_multiplier) * naked_option_margin
    return {
        "cash_balance_usd": float(cash),
        "stock_market_value_usd": float(stock_value),
        "open_option_signed_market_value_usd": option_market_value,
        "estimated_open_option_liquidation_cost_usd": close_costs,
        "account_equity_usd": equity,
        "naked_spy_option_margin_proxy_usd": naked_option_margin,
        "initial_margin_requirement_proxy_usd": initial_req,
        "maintenance_margin_requirement_proxy_usd": maintenance_req,
        "initial_margin_cushion_usd": equity - initial_req,
        "maintenance_margin_cushion_usd": equity - maintenance_req,
        "gross_spy_put_assignment_obligation_usd": put_obligation,
        "gross_spy_short_call_delivery_notional_usd": call_delivery_notional,
        "current_spy_short_call_intrinsic_liability_usd": call_intrinsic_liability,
        "open_short_call_contracts": open_short_calls,
        "open_option_legs": len(active),
        "cash_shortfall_vs_put_assignment_usd": max(put_obligation - float(cash), 0.0),
        "stale_mark_legs": stale_legs,
        "max_stale_quote_age_sessions": max_stale_age,
    }


def forced_close(active, cash, day, marks_by_position_day):
    updated_cash = float(cash)
    total_closing_cost = 0.0
    closed_ids = []
    for position_id, position in list(active.items()):
        _, mark = mark_for(position, day, marks_by_position_day)
        closing_cost = UNIT_COST_PER_CONTRACT_PER_SIDE * position["qty"]
        updated_cash += signed_position_value(position, mark) - closing_cost
        total_closing_cost += closing_cost
        closed_ids.append(position_id)
        del active[position_id]
    return updated_cash, total_closing_cost, closed_ids


def stress_option_mark(position, mark, current_spot, scenario):
    ret = scenario["qqq_return"] if position["symbol"] == "QQQ" else scenario["spy_return"]
    stressed_spot = max(0.0, float(current_spot) * (1.0 + float(ret)))
    intrinsic_now = option_intrinsic(position["right"], current_spot, position["strike"])
    intrinsic_stressed = option_intrinsic(position["right"], stressed_spot, position["strike"])
    extrinsic = max(float(mark) - intrinsic_now, 0.0)
    stressed_mark = intrinsic_stressed + extrinsic * float(scenario["extrinsic_multiplier"])
    return stressed_spot, max(stressed_mark, intrinsic_stressed, 0.0)


def stress_state(active, cash, stock_value, day, spots, qqq_spots, marks_by_position_day, margin_multiplier, scenario):
    current = compute_state(active, cash, stock_value, day, spots, marks_by_position_day, margin_multiplier)
    stressed_option_value = 0.0
    stressed_naked_margin = 0.0
    stressed_put_obligation = 0.0
    stressed_call_notional = 0.0
    stressed_call_intrinsic = 0.0
    current_spy = number(spots.get(day))
    if current_spy is None:
        raise RuntimeError(f"missing SPY spot for scenario stress on {day}")
    for position in active.values():
        _, mark = mark_for(position, day, marks_by_position_day)
        spot_now = number((qqq_spots if position["symbol"] == "QQQ" else spots).get(day))
        if spot_now is None or spot_now <= 0:
            raise RuntimeError(f"missing {position['symbol']} spot for scenario stress on {day}")
        stressed_spot, stressed_mark = stress_option_mark(position, mark, spot_now, scenario)
        stressed_option_value += signed_position_value(position, stressed_mark)
        if position["symbol"] == "SPY" and position["position_side"] == "SHORT":
            stressed_naked_margin += naked_stock_option_margin_per_contract(
                position["right"], stressed_spot, position["strike"], stressed_mark, position["qty"]
            )
            if position["right"] == "P":
                stressed_put_obligation += position["strike"] * MULTIPLIER * position["qty"]
            else:
                stressed_call_notional += position["strike"] * MULTIPLIER * position["qty"]
                stressed_call_intrinsic += option_intrinsic("C", stressed_spot, position["strike"]) * MULTIPLIER * position["qty"]

    stressed_stock = float(stock_value) * (1.0 + float(scenario["qqq_return"]))
    close_costs = current["estimated_open_option_liquidation_cost_usd"]
    stressed_equity = float(cash) + stressed_stock + stressed_option_value - close_costs
    stressed_maintenance_req = 0.25 * stressed_stock + float(margin_multiplier) * stressed_naked_margin
    return {
        "current_equity_usd": current["account_equity_usd"],
        "stressed_equity_usd": stressed_equity,
        "stress_pnl_change_usd": stressed_equity - current["account_equity_usd"],
        "stressed_maintenance_requirement_proxy_usd": stressed_maintenance_req,
        "stressed_maintenance_cushion_usd": stressed_equity - stressed_maintenance_req,
        "stressed_spy_put_assignment_obligation_usd": stressed_put_obligation,
        "stressed_spy_call_delivery_notional_usd": stressed_call_notional,
        "stressed_spy_short_call_intrinsic_liability_usd": stressed_call_intrinsic,
    }


def append_event(events, **kwargs):
    events.append(kwargs)


def simulate_one(phase, capital, margin_multiplier, phase_days, baskets_by_phase_day,
                 positions_by_phase, marks_by_position_day, spots, qqq_spots,
                 stock_start_value, store_daily):
    first_day = daystr(phase_days[0]["date"])
    cash = float(capital) - float(stock_start_value)
    active = {}
    stopped = False
    accepted_baskets = 0
    margin_rejected_baskets = 0
    blocked_after_stop = 0
    forced_liquidations = 0
    unresolved_margin_breaches = 0
    decisions = []
    margin_events = []
    daily = []
    stress_track = {}
    candidate_basket_count = sum(
        1 for (p, _), groups in baskets_by_phase_day.items() if p == phase
        for _group in groups
    )

    for daily_source in phase_days:
        day = daystr(daily_source["date"])
        stock_value = float(daily_source["stock_market_value_total_return_proxy_usd"])
        forced_today = False
        blocked_today = 0
        admitted_today = 0
        baseline_equity = float(capital) - float(stock_start_value) + float(daily_source["portfolio_nav_usd"])

        # Close trades due for executable exit or expiry settlement before same-day entries.
        for position_id, position in list(active.items()):
            if position["exit_date"] and position["exit_date"] == day:
                cash += exit_cash_delta(position)
                del active[position_id]
            elif position["settlement_date"] and position["settlement_date"] == day:
                spot_map = spots if position["symbol"] == "SPY" else qqq_spots
                settle_spot = number(spot_map.get(day))
                if settle_spot is None:
                    raise RuntimeError(f"missing settlement spot for {position_id} on {day}")
                cash += settlement_cash_delta(position, settle_spot)
                del active[position_id]

        state = compute_state(active, cash, stock_value, day, spots, marks_by_position_day, margin_multiplier)
        if active and (state["account_equity_usd"] <= 0 or
                       state["account_equity_usd"] < state["maintenance_margin_requirement_proxy_usd"]):
            reason = "EOD_MAINTENANCE_MARGIN_BREACH" if state["account_equity_usd"] > 0 else "EOD_EQUITY_NONPOSITIVE"
            before = state["account_equity_usd"]
            req = state["maintenance_margin_requirement_proxy_usd"]
            leg_count = state["open_option_legs"]
            cash, closing_cost, closed_ids = forced_close(active, cash, day, marks_by_position_day)
            forced_liquidations += 1
            forced_today = True
            stopped = True
            append_event(margin_events, event_type="FORCED_LIQUIDATION", phase_sessions=phase,
                         account_capital_usd=capital, margin_multiplier=margin_multiplier, date=day,
                         reason=reason, equity_before_liquidation_usd=round(before, 2),
                         maintenance_requirement_usd=round(req, 2), open_legs_closed=leg_count,
                         liquidation_cost_usd=round(closing_cost, 2), positions_closed=";".join(closed_ids))
        elif state["account_equity_usd"] <= 0:
            unresolved_margin_breaches += 1
            stopped = True
            append_event(margin_events, event_type="ACCOUNT_INSOLVENT", phase_sessions=phase,
                         account_capital_usd=capital, margin_multiplier=margin_multiplier, date=day,
                         reason="NONPOSITIVE_EQUITY_WITHOUT_OPEN_OPTIONS",
                         equity_before_liquidation_usd=round(state["account_equity_usd"], 2),
                         maintenance_requirement_usd=round(state["maintenance_margin_requirement_proxy_usd"], 2),
                         open_legs_closed=0, liquidation_cost_usd=0.0, positions_closed="")

        day_baskets = sorted(baskets_by_phase_day.get((phase, day), []),
                             key=lambda items: (items[0]["signal_date"], items[0]["expiry"]))
        for members in day_baskets:
            basket_id = members[0]["basket_id"]
            if stopped:
                blocked_after_stop += 1
                blocked_today += 1
                append_event(decisions, account_capital_usd=capital, margin_multiplier=margin_multiplier,
                             phase_sessions=phase, basket_id=basket_id, signal_date=members[0]["signal_date"],
                             entry_date=day, decision="BLOCKED_AFTER_LIQUIDATION_STOP",
                             reason="prior margin-triggered liquidation or account insolvency",
                             projected_equity_usd="", projected_initial_margin_usd="", cash_after_entry_usd="")
                continue

            entry_cash_delta_total = sum(entry_cash_delta(p) for p in members)
            projected_cash = cash + entry_cash_delta_total
            projected_active = dict(active)
            projected_active.update({p["position_id"]: p for p in members})
            trial = compute_state(projected_active, projected_cash, stock_value, day, spots,
                                  marks_by_position_day, margin_multiplier)
            if trial["account_equity_usd"] <= 0 or trial["account_equity_usd"] < trial["initial_margin_requirement_proxy_usd"]:
                margin_rejected_baskets += 1
                blocked_today += 1
                append_event(decisions, account_capital_usd=capital, margin_multiplier=margin_multiplier,
                             phase_sessions=phase, basket_id=basket_id, signal_date=members[0]["signal_date"],
                             entry_date=day, decision="REJECTED_INSUFFICIENT_INITIAL_MARGIN",
                             reason="projected account equity below initial margin proxy",
                             projected_equity_usd=round(trial["account_equity_usd"], 2),
                             projected_initial_margin_usd=round(trial["initial_margin_requirement_proxy_usd"], 2),
                             cash_after_entry_usd=round(projected_cash, 2))
                continue

            cash = projected_cash
            active.update({p["position_id"]: p for p in members})
            accepted_baskets += 1
            admitted_today += 1
            append_event(decisions, account_capital_usd=capital, margin_multiplier=margin_multiplier,
                         phase_sessions=phase, basket_id=basket_id, signal_date=members[0]["signal_date"],
                         entry_date=day, decision="ACCEPTED", reason="projected equity covers initial margin proxy",
                         projected_equity_usd=round(trial["account_equity_usd"], 2),
                         projected_initial_margin_usd=round(trial["initial_margin_requirement_proxy_usd"], 2),
                         cash_after_entry_usd=round(projected_cash, 2))

        state = compute_state(active, cash, stock_value, day, spots, marks_by_position_day, margin_multiplier)
        if active and (state["account_equity_usd"] <= 0 or
                       state["account_equity_usd"] < state["maintenance_margin_requirement_proxy_usd"]):
            reason = "EOD_POST_ENTRY_MAINTENANCE_MARGIN_BREACH" if state["account_equity_usd"] > 0 else "EOD_POST_ENTRY_EQUITY_NONPOSITIVE"
            before = state["account_equity_usd"]
            req = state["maintenance_margin_requirement_proxy_usd"]
            leg_count = state["open_option_legs"]
            cash, closing_cost, closed_ids = forced_close(active, cash, day, marks_by_position_day)
            forced_liquidations += 1
            forced_today = True
            stopped = True
            append_event(margin_events, event_type="FORCED_LIQUIDATION", phase_sessions=phase,
                         account_capital_usd=capital, margin_multiplier=margin_multiplier, date=day,
                         reason=reason, equity_before_liquidation_usd=round(before, 2),
                         maintenance_requirement_usd=round(req, 2), open_legs_closed=leg_count,
                         liquidation_cost_usd=round(closing_cost, 2), positions_closed=";".join(closed_ids))

        state = compute_state(active, cash, stock_value, day, spots, marks_by_position_day, margin_multiplier)
        state.update({
            "account_capital_scenario_usd": float(capital), "margin_multiplier": float(margin_multiplier),
            "phase_sessions": phase, "date": day,
            "benchmark_unconstrained_equity_usd": baseline_equity,
            "difference_vs_unconstrained_benchmark_usd": state["account_equity_usd"] - baseline_equity,
            "accepted_baskets_today": admitted_today, "blocked_baskets_today": blocked_today,
            "forced_liquidation_today": forced_today, "model_stopped": stopped,
            "source_daily_nav_usd": float(daily_source["portfolio_nav_usd"]),
            "cash_after_put_assignment_reserve_usd": state["cash_balance_usd"] - state["gross_spy_put_assignment_obligation_usd"],
        })
        daily.append(state)

        for scenario in STRESS_SCENARIOS:
            evaluated = stress_state(active, cash, stock_value, day, spots, qqq_spots,
                                     marks_by_position_day, margin_multiplier, scenario)
            candidate = {
                "account_capital_scenario_usd": capital, "margin_multiplier": margin_multiplier,
                "phase_sessions": phase, "scenario": scenario["name"],
                "qqq_return_shock_pct": round(float(scenario["qqq_return"]) * 100, 2),
                "spy_return_shock_pct": round(float(scenario["spy_return"]) * 100, 2),
                "extrinsic_value_multiplier": scenario["extrinsic_multiplier"],
                "date": day, **{k: round(v, 2) for k, v in evaluated.items()},
                "gross_put_assignment_obligation_usd": round(state["gross_spy_put_assignment_obligation_usd"], 2),
                "gross_short_call_delivery_notional_usd": round(state["gross_spy_short_call_delivery_notional_usd"], 2),
                "cash_balance_usd": round(state["cash_balance_usd"], 2),
            }
            prior = stress_track.get(scenario["name"])
            if prior is None:
                stress_track[scenario["name"]] = {
                    "minimum_stressed_equity": candidate,
                    "worst_equity_change": candidate,
                    "minimum_stressed_margin_cushion": candidate,
                }
            else:
                if candidate["stressed_equity_usd"] < prior["minimum_stressed_equity"]["stressed_equity_usd"]:
                    prior["minimum_stressed_equity"] = candidate
                if candidate["stress_pnl_change_usd"] < prior["worst_equity_change"]["stress_pnl_change_usd"]:
                    prior["worst_equity_change"] = candidate
                if candidate["stressed_maintenance_cushion_usd"] < prior["minimum_stressed_margin_cushion"]["stressed_maintenance_cushion_usd"]:
                    prior["minimum_stressed_margin_cushion"] = candidate

    peak = -float("inf")
    peak_date = ""
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    max_dd_peak_date = first_day
    max_dd_trough_date = first_day
    for row in daily:
        equity = float(row["account_equity_usd"])
        if equity > peak:
            peak, peak_date = equity, row["date"]
        dd_usd = equity - peak
        dd_pct = (equity / peak - 1.0) * 100.0 if peak > 0 else None
        row["running_peak_equity_usd"] = round(peak, 2)
        row["drawdown_usd"] = round(dd_usd, 2)
        row["drawdown_pct"] = round(dd_pct, 4) if dd_pct is not None else ""
        if dd_pct is not None and dd_pct < max_dd_pct:
            max_dd_usd = dd_usd
            max_dd_pct = dd_pct
            max_dd_peak_date = peak_date
            max_dd_trough_date = row["date"]

    no_intervention = margin_rejected_baskets == 0 and blocked_after_stop == 0 and forced_liquidations == 0
    max_abs_baseline_diff = max(abs(float(r["difference_vs_unconstrained_benchmark_usd"])) for r in daily)
    if no_intervention and max_abs_baseline_diff > 0.05:
        raise RuntimeError(
            f"cash-ledger reconciliation failed for unrestricted scenario: capital={capital}, "
            f"multiplier={margin_multiplier}, max_abs_diff={max_abs_baseline_diff:.4f}"
        )

    summary = {
        "account_capital_scenario_usd": capital, "margin_multiplier": margin_multiplier,
        "phase_sessions": phase, "start_date": daily[0]["date"], "end_date": daily[-1]["date"],
        "start_equity_usd": round(daily[0]["account_equity_usd"], 2),
        "end_equity_usd": round(daily[-1]["account_equity_usd"], 2),
        "net_equity_change_usd": round(daily[-1]["account_equity_usd"] - capital, 2),
        "equity_return_pct": round((daily[-1]["account_equity_usd"] / capital - 1) * 100, 4) if capital > 0 else None,
        "max_drawdown_usd": round(max_dd_usd, 2), "max_drawdown_pct": round(max_dd_pct, 4),
        "max_drawdown_peak_date": max_dd_peak_date, "max_drawdown_trough_date": max_dd_trough_date,
        "min_equity_usd": round(min(float(r["account_equity_usd"]) for r in daily), 2),
        "min_cash_balance_usd": round(min(float(r["cash_balance_usd"]) for r in daily), 2),
        "days_cash_below_zero": sum(float(r["cash_balance_usd"]) < 0 for r in daily),
        "max_initial_margin_requirement_usd": round(max(float(r["initial_margin_requirement_proxy_usd"]) for r in daily), 2),
        "max_maintenance_margin_requirement_usd": round(max(float(r["maintenance_margin_requirement_proxy_usd"]) for r in daily), 2),
        "max_gross_put_assignment_obligation_usd": round(max(float(r["gross_spy_put_assignment_obligation_usd"]) for r in daily), 2),
        "max_gross_short_call_delivery_notional_usd": round(max(float(r["gross_spy_short_call_delivery_notional_usd"]) for r in daily), 2),
        "max_cash_gap_vs_put_assignment_reserve_usd": round(max(float(r["cash_shortfall_vs_put_assignment_usd"]) for r in daily), 2),
        "days_cash_insufficient_for_full_put_assignment": sum(float(r["cash_shortfall_vs_put_assignment_usd"]) > 0 for r in daily),
        "candidate_baskets_from_source_nav": candidate_basket_count,
        "accepted_baskets": accepted_baskets, "rejected_initial_margin_baskets": margin_rejected_baskets,
        "blocked_after_liquidation_stop_baskets": blocked_after_stop,
        "forced_liquidation_events": forced_liquidations,
        "unresolved_stock_only_margin_breach_days": unresolved_margin_breaches,
        "daily_source_reconciliation_status": "PASS" if no_intervention and max_abs_baseline_diff <= 0.05 else "INTERVENTION_PATH_DIFFERS_BY_DESIGN",
        "max_abs_difference_vs_unconstrained_benchmark_usd": round(max_abs_baseline_diff, 4),
    }
    stress_rows = []
    for trackers in stress_track.values():
        for criterion, key in (
            ("minimum_stressed_equity", "minimum_stressed_equity"),
            ("worst_equity_change", "worst_equity_change"),
            ("minimum_stressed_margin_cushion", "minimum_stressed_margin_cushion"),
        ):
            row = dict(trackers[key])
            row["criterion"] = criterion
            stress_rows.append(row)
    return summary, daily if store_daily else [], decisions, margin_events, stress_rows


def parse_float_list(raw, label):
    try:
        values = tuple(float(part.strip()) for part in raw.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid {label}: {raw}") from exc
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise argparse.ArgumentTypeError(f"{label} values must all be positive numbers")
    return values


def report_text(summary_rows, capital_summary, stress_rows, stock_start):
    lines = [
        "# QQQ/SPY PUT + CALL account feasibility and margin stress",
        "",
        "- Strategy input: existing audited DTE20 / remaining calendar DTE <= 4 daily NAV replay; not a new strategy optimization.",
        "- Legs: QQQ LONG PUT 1 : SPY SHORT PUT 6 (target abs-Delta 0.25) and QQQ LONG CALL 1 : SPY SHORT CALL 6 (target abs-Delta 0.20), same expiry for strict paired baskets.",
        "- Current QQQ holding input is USD 63,694 at USD 712.20 on 2026-10-26, equivalent to 89.4327 shares. The fixed share count is backcast over 2018-2025; its start value is USD {:,.2f}. This is a counterfactual position-history assumption, not proof the account actually held these shares in 2018.".format(stock_start),
        "- Account equity is cash + QQQ market value + signed option liquidation value less estimated closing costs. Initial cash = scenario capital minus the historical starting QQQ value. Option entry/exit cash flows include USD 0.05/share/side slippage and USD 0.65/contract/side commission.",
        "- New baskets are rejected if post-entry equity is below the modeled initial-margin requirement. Existing options are liquidated at EOD liquidation-side marks if equity is nonpositive or below modeled maintenance margin; once this occurs, the simulator stops opening new baskets.",
        "- Timing limit: checks occur at end-of-day only. Intraday margin calls, gap-through fills, borrow availability, interest, exercise/assignment fees, taxes and broker-specific house margin are not simulated.",
        "- Margin proxy applies an Interactive Brokers-published uncovered stock-option formula separately to each short SPY option, with no cross-leg offsets; it adds 50% of QQQ stock value for initial margin and 25% for maintenance. 1.5x and 2.0x variants are hypothetical house-margin stress multipliers, not official broker settings.",
        "- Full SPY short-PUT strike notional is reported as a cash-secured assignment reserve, separately from the margin proxy. Short-call delivery notional is not the same as cash required or maximum loss.",
        "- Stress scenarios apply hypothetical QQQ/SPY spot shocks and assumed multipliers on remaining option extrinsic value. They are sensitivities, not forecasts or full option-pricing outputs, and cannot bound naked short-call losses.",
        "- The prior daily NAV added stock market value to option P&L but omitted initial account cash. Therefore its >100% drawdown percentages were not account-return percentages. This report rebases each run to explicit starting account capital.",
        "",
        "## Capital scenarios (1.0x margin proxy; worst phase)",
        "",
        "| Starting capital | Worst max DD USD | Worst max DD % | Lowest end equity | Blocked baskets | Forced liquidations | Peak put assignment reserve | Peak call delivery notional | Peak cash gap vs put reserve |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in capital_summary:
        lines.append(
            "| USD {:,.0f} | USD {:,.2f} | {:.2f}% | USD {:,.2f} | {} | {} | USD {:,.2f} | USD {:,.2f} | USD {:,.2f} |".format(
                row["account_capital_scenario_usd"], row["worst_max_drawdown_usd"], row["worst_max_drawdown_pct"],
                row["lowest_end_equity_usd"], row["rejected_initial_margin_baskets"] + row["blocked_after_liquidation_stop_baskets"],
                row["forced_liquidation_events"], row["peak_put_assignment_reserve_usd"],
                row["peak_short_call_delivery_notional_usd"], row["peak_cash_gap_vs_put_reserve_usd"],
            )
        )
    lines += [
        "",
        "## Margin sensitivity across capital sizes",
        "",
        "| Starting capital | Margin multiplier | Phases with forced liquidation | Total blocked baskets | Worst max DD % | Lowest stressed margin cushion |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for capital in sorted({r["account_capital_scenario_usd"] for r in summary_rows}):
        for mult in sorted({r["margin_multiplier"] for r in summary_rows}):
            subset = [r for r in summary_rows if r["account_capital_scenario_usd"] == capital and r["margin_multiplier"] == mult]
            stress_subset = [r for r in stress_rows if r["account_capital_scenario_usd"] == capital and r["margin_multiplier"] == mult and r["criterion"] == "minimum_stressed_margin_cushion"]
            if not subset:
                continue
            lines.append(
                "| USD {:,.0f} | {:.1f}x | {} | {} | {:.2f}% | USD {:,.2f} |".format(
                    capital, mult, sum(r["forced_liquidation_events"] > 0 for r in subset),
                    sum(r["rejected_initial_margin_baskets"] + r["blocked_after_liquidation_stop_baskets"] for r in subset),
                    min(r["max_drawdown_pct"] for r in subset),
                    min((r["stressed_maintenance_cushion_usd"] for r in stress_subset), default=0.0),
                )
            )
    lines += [
        "",
        "## Interpretation boundaries",
        "",
        "- A cash-only put seller needs full exercise cash for the short puts; this portfolio also sells uncovered SPY calls. The QQQ shares and QQQ long options do not contractually cover SPY short calls.",
        "- The listed-option margin calculation is a broker-specific reference formula, not a guarantee of buying-power acceptance. Actual brokers can impose higher house requirements and liquidate intraday.",
        "- An uncovered short call has theoretically unlimited loss. A +100% stress case is only one finite scenario, not a maximum-loss estimate.",
        "- A backtest pass confirms code/data reconciliation, not that a broker would allow these trades or that historical EOD marks were executable fills.",
        "",
        "References: Interactive Brokers — https://www.interactivebrokers.com/en/trading/margin-options.php ; Options Industry Council naked-call risk — https://www.optionseducation.org/strategies/all-strategies/naked-call-uncovered-call-short-call .",
        "",
        "Files: phase_margin_summary.csv, capital_summary.csv, daily_account_nav.csv, entry_decisions.csv, margin_events.csv, stress_scenario_summary.csv, account_feasibility_audit.json.",
        "",
    ]
    return "\n".join(lines)


def generate(capitals, margin_multipliers):
    positions, marks_by_position_day, phase_days, daily_by_phase_day, baskets_by_phase_day, source_audit, positions_by_phase = load_positions_and_marks()
    spots, spot_integrity = load_underlying_spots()
    qqq_cache = Path.home() / ".cache" / "qqq-spy-pair-daily-nav-v1"
    qqq_path, qqq_integrity = put_engine.download_verified("QQQ", None, qqq_cache / "qqq")
    qqq_spots = put_engine.load_spots(qqq_path, "QQQ")

    stock_start_value = float(phase_days[PHASES[0]][0]["stock_market_value_total_return_proxy_usd"])
    if any(abs(float(rows[0]["stock_market_value_total_return_proxy_usd"]) - stock_start_value) > 0.01
           for phase, rows in phase_days.items() if phase != PHASES[0]):
        raise RuntimeError("QQQ stock starting value differs across phases")

    phase_summaries, daily_all, decisions_all, events_all, stress_all = [], [], [], [], []
    for capital in capitals:
        if capital <= stock_start_value:
            raise ValueError(f"capital {capital} must exceed backcast QQQ stock value {stock_start_value}")
        for margin_multiplier in margin_multipliers:
            for phase in PHASES:
                summary, daily, decisions, events, stress = simulate_one(
                    phase, capital, margin_multiplier, phase_days[phase], baskets_by_phase_day,
                    positions_by_phase, marks_by_position_day, spots, qqq_spots, stock_start_value,
                    store_daily=(abs(margin_multiplier - 1.0) < 1e-12),
                )
                phase_summaries.append(summary)
                decisions_all.extend(decisions)
                events_all.extend(events)
                stress_all.extend(stress)
                daily_all.extend(daily)

    highest_capital = max(capitals)
    unrestricted = [
        row for row in phase_summaries
        if row["account_capital_scenario_usd"] == highest_capital
        and abs(row["margin_multiplier"] - 1.0) < 1e-12
    ]
    if len(unrestricted) != len(PHASES):
        raise RuntimeError("missing unrestricted high-capital reconciliation scenarios")
    if any(row["daily_source_reconciliation_status"] != "PASS" for row in unrestricted):
        raise RuntimeError(f"highest-capital cash-flow replay did not reconcile to audited NAV: {unrestricted}")

    base_summaries = [r for r in phase_summaries if abs(r["margin_multiplier"] - 1.0) < 1e-12]
    capital_summary = []
    for capital in capitals:
        rows = [r for r in base_summaries if r["account_capital_scenario_usd"] == capital]
        capital_summary.append({
            "account_capital_scenario_usd": capital,
            "phases": len(rows),
            "worst_max_drawdown_usd": min(r["max_drawdown_usd"] for r in rows),
            "worst_max_drawdown_pct": min(r["max_drawdown_pct"] for r in rows),
            "lowest_end_equity_usd": min(r["end_equity_usd"] for r in rows),
            "lowest_min_equity_usd": min(r["min_equity_usd"] for r in rows),
            "rejected_initial_margin_baskets": sum(r["rejected_initial_margin_baskets"] for r in rows),
            "blocked_after_liquidation_stop_baskets": sum(r["blocked_after_liquidation_stop_baskets"] for r in rows),
            "forced_liquidation_events": sum(r["forced_liquidation_events"] for r in rows),
            "peak_put_assignment_reserve_usd": max(r["max_gross_put_assignment_obligation_usd"] for r in rows),
            "peak_short_call_delivery_notional_usd": max(r["max_gross_short_call_delivery_notional_usd"] for r in rows),
            "peak_cash_gap_vs_put_reserve_usd": max(r["max_cash_gap_vs_put_assignment_reserve_usd"] for r in rows),
            "min_cash_balance_usd": min(r["min_cash_balance_usd"] for r in rows),
        })

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "phase_margin_summary.csv", phase_summaries)
    write_csv(OUT / "capital_summary.csv", capital_summary)
    write_csv(OUT / "daily_account_nav.csv", daily_all)
    write_csv(OUT / "entry_decisions.csv", decisions_all)
    write_csv(OUT / "margin_events.csv", events_all)
    write_csv(OUT / "stress_scenario_summary.csv", stress_all)
    report = report_text(phase_summaries, capital_summary, stress_all, stock_start_value)
    (OUT / "ACCOUNT_FEASIBILITY_REPORT.md").write_text(report, encoding="utf-8")

    audit = {
        "status": "PASS",
        "method": "historical EOD account cash-flow replay with initial-margin entry gating, EOD maintenance-margin liquidation, and hypothetical underlying/extrinsic stress scenarios",
        "source_daily_nav_audit_status": source_audit.get("status"),
        "source_daily_nav_rows": len(daily_by_phase_day),
        "reconstructed_option_legs": len(positions),
        "reconstructed_position_daily_mark_rows": len(marks_by_position_day),
        "account_capital_scenarios_usd": list(capitals),
        "margin_multipliers": list(margin_multipliers),
        "phases": list(PHASES),
        "source_underlying_spy_integrity": spot_integrity,
        "source_underlying_qqq_integrity": qqq_integrity,
        "unrestricted_high_capital_reconciliation": {
            "capital_usd": highest_capital, "margin_multiplier": 1.0,
            "phases_passed": len(unrestricted), "phase_count": len(PHASES),
            "max_abs_difference_usd": max(r["max_abs_difference_vs_unconstrained_benchmark_usd"] for r in unrestricted),
            "status": "PASS",
        },
        "broker_buying_power_actual": False,
        "intraday_margin_and_gap_liquidation_modeled": False,
        "short_call_maximum_loss_finite": False,
        "stress_scenarios_are_hypothetical": True,
        "source_current_qqq_position_usd": 63694.0,
        "source_current_qqq_reference_price_usd": 712.20,
        "backcast_stock_start_value_usd": stock_start_value,
        "important_note": "The prior daily NAV excluded the capital cash balance; this model rebases it with explicit starting account capital. Short-option margin is a non-netted Reg-T-style proxy, not a broker approval or safety guarantee.",
    }
    (OUT / "account_feasibility_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "status": "PASS", "report": str(OUT / "ACCOUNT_FEASIBILITY_REPORT.md"),
        "phase_summary_rows": len(phase_summaries), "daily_account_nav_rows": len(daily_all),
        "entry_decision_rows": len(decisions_all), "margin_event_rows": len(events_all),
        "stress_scenario_rows": len(stress_all), "capital_summary": capital_summary,
        "audit": audit["unrestricted_high_capital_reconciliation"],
    }, indent=2, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capitals", default="100000,250000,500000,750000,1000000")
    parser.add_argument("--margin-multipliers", default="1,1.5,2")
    args = parser.parse_args()
    generate(parse_float_list(args.capitals, "capital"),
             parse_float_list(args.margin_multipliers, "margin multiplier"))


if __name__ == "__main__":
    main()
