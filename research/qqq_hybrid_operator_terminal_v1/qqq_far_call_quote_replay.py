#!/usr/bin/env python3
"""Research-only QQQ far-call listed-contract EOD-side replay.

This is an event/quote replay, not exchange-confirmed fills. The public source is a
4 p.m. ET EOD preservation mirror, lacks several dates, and ends 2025-12-15.
No missing quote is forward-filled; portfolio CAGR/MaxDD are deliberately blocked.
"""
from __future__ import annotations
import csv, json, math, re, sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import full_history_qqq_quote_audit as audit

START_DATE = "2018-03-01"
REQUESTED_END_DATE = "2025-12-31"
SOURCE_END_DATE = "2025-12-15"
INITIAL_CAPITAL = 100_000.0
QQQ_CORE_FRACTION = 0.42
# Exact source-model setting; the alternate is the legacy credit-budget interpretation.
BUDGET_MODES = (
    {"name": "SOURCE_MAX_LOSS_0P8PCT_NAV", "kind": "max_loss", "pct": 0.008},
    {"name": "LEGACY_CREDIT_1P2PCT_NAV", "kind": "credit", "pct": 0.012},
)
SLIPPAGE_PER_LEG = (0.0, 0.025, 0.05, 0.10)
COMMISSION_PER_CONTRACT_PER_SIDE = (0.0, 0.65)  # HYPOTHETICAL sensitivity only.
DTE_MIN, DTE_MAX, DTE_TARGET = 20, 40, 30
SHORT_DELTA_TARGET, WING_DELTA_TARGET = 0.16, 0.08
STOP_DTE = 7
STOP_LOSS_OVER_MAXLOSS = -0.55
TAKE_PROFIT_OVER_MAXLOSS = 0.50
# Attribution-only diagnostic bins; never used to select, size, or exit a trade.
TREND_LOOKBACK_SESSIONS = 20
TREND_MOMENTUM_BAND = 0.02
SPREAD_TIGHT_MAX_PCT_MID = 10.0
SPREAD_MODERATE_MAX_PCT_MID = 25.0
OPTION_COLUMNS = ["contract_id", "symbol", "expiration", "strike", "type",
                  "bid", "ask", "bid_size", "ask_size", "volume", "open_interest",
                  "date", "implied_volatility", "delta"]
EVIDENCE = "OBSERVED_EOD_QUOTES / DERIVED_SIDE_PRICE_REPLAY; NOT_CONFIRMED_FILLS"
QUOTE_TIME_STATUS = "README_REPORTED_16:00_US_EASTERN_SNAPSHOT; EXACT_TICK_TIMESTAMP_UNVERIFIED"


def n(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def day(value):
    if value is None:
        return ""
    return value.isoformat()[:10] if hasattr(value, "isoformat") else str(value)[:10]


def normalized_contract_id(value):
    if value is None:
        return ""
    out = re.sub(r"\s+", "", str(value).strip().upper())
    return out[2:] if out.startswith("O:") else out


def contract_root(value):
    """Return OCC root only when the source ID parses as a full OCC-style symbol."""
    ident = normalized_contract_id(value)
    match = re.fullmatch(r"([A-Z0-9]{1,6})(\d{6})[CP](\d{8})", ident)
    return match.group(1) if match else None


def valid_quote(row, require_size=True):
    bid, ask = n(row.get("bid")), n(row.get("ask"))
    if bid is None or ask is None or bid <= 0 or ask <= 0 or bid > ask:
        return False
    if require_size:
        bs, ass = n(row.get("bid_size")), n(row.get("ask_size"))
        if bs is None or ass is None or bs <= 0 or ass <= 0:
            return False
    return True


def valid_standard_qqq_call(row, session_day, require_size=True):
    if str(row.get("symbol", "")).upper() != "QQQ":
        return False
    if str(row.get("type", "")).strip().lower() not in ("c", "call"):
        return False
    ident = normalized_contract_id(row.get("contract_id"))
    if not ident:
        return False
    # Never treat an unknown or adjusted option root as standard QQQ.
    if contract_root(ident) != "QQQ":
        return False
    strike, delta = n(row.get("strike")), n(row.get("delta"))
    if strike is None or delta is None or delta <= 0 or delta >= 1:
        return False
    if not audit.base.standard_strike_grid(strike):
        return False
    try:
        dte = (date.fromisoformat(day(row.get("expiration"))) -
               date.fromisoformat(session_day)).days
    except (TypeError, ValueError):
        return False
    return DTE_MIN <= dte <= DTE_MAX and valid_quote(row, require_size=require_size)


def choose_vertical(rows, session_day):
    """Choose an actual listed same-expiry call vertical nearest source Delta targets."""
    candidates = []
    root_blocked = 0
    quote_rejected = 0
    calls = []
    for row in rows:
        if str(row.get("symbol", "")).upper() != "QQQ":
            continue
        if str(row.get("type", "")).strip().lower() not in ("c", "call"):
            continue
        ident = normalized_contract_id(row.get("contract_id"))
        root = contract_root(ident)
        if root != "QQQ":
            root_blocked += 1
            continue
        try:
            dte = (date.fromisoformat(day(row.get("expiration"))) -
                   date.fromisoformat(session_day)).days
        except (TypeError, ValueError):
            continue
        if not DTE_MIN <= dte <= DTE_MAX:
            continue
        if not valid_quote(row, require_size=True):
            quote_rejected += 1
            continue
        strike, delta = n(row.get("strike")), n(row.get("delta"))
        if strike is None or delta is None or delta <= 0 or delta >= 1:
            continue
        if not audit.base.standard_strike_grid(strike):
            continue
        calls.append((dte, row, strike, delta, ident))
    if not calls:
        return {"status": "NO_VALID_STANDARD_QQQ_CALLS", "root_blocked_rows": root_blocked,
                "invalid_or_no_size_rows": quote_rejected}

    by_expiry = defaultdict(list)
    for item in calls:
        by_expiry[day(item[1].get("expiration"))].append(item)
    expiry_pairs = []
    for expiry, items in by_expiry.items():
        dte = items[0][0]
        shorts = sorted((x for x in items if 0.03 <= x[3] <= 0.30),
                        key=lambda x: abs(x[3] - SHORT_DELTA_TARGET))[:30]
        wings = sorted((x for x in items if 0.01 <= x[3] <= 0.20),
                       key=lambda x: abs(x[3] - WING_DELTA_TARGET))[:30]
        for short in shorts:
            for wing in wings:
                if short[2] >= wing[2] or short[3] <= wing[3]:
                    continue
                width = wing[2] - short[2]
                gross_credit = n(short[1].get("bid")) - n(wing[1].get("ask"))
                if gross_credit is None or gross_credit <= 0 or gross_credit >= width:
                    continue
                score = abs(short[3] - SHORT_DELTA_TARGET) + abs(wing[3] - WING_DELTA_TARGET)
                expiry_pairs.append((abs(dte - DTE_TARGET), -len(items), expiry, score,
                                     short, wing, width, gross_credit))
    if not expiry_pairs:
        return {"status": "NO_VALID_POSITIVE_CREDIT_VERTICAL", "root_blocked_rows": root_blocked,
                "invalid_or_no_size_rows": quote_rejected}
    # Choose closest-to-30-DTE expiry first; then best Delta match within it.
    best_expiry = min(x[0] for x in expiry_pairs)
    possible = [x for x in expiry_pairs if x[0] == best_expiry]
    chosen_expiry = min(possible, key=lambda x: (x[1], x[2]))[2]
    same_expiry = [x for x in possible if x[2] == chosen_expiry]
    chosen = min(same_expiry, key=lambda x: (x[3], -x[7], x[5][2]-x[4][2]))
    _, _, expiry, score, short, wing, width, gross_credit = chosen
    def serialize_leg(item, leg):
        row = item[1]
        return {
            "contract_id": item[4], "root": contract_root(item[4]),
            "expiry": expiry, "strike": item[2], "delta": item[3],
            "bid": n(row.get("bid")), "ask": n(row.get("ask")),
            "bid_size": n(row.get("bid_size")), "ask_size": n(row.get("ask_size")),
            "volume": n(row.get("volume")), "open_interest": n(row.get("open_interest")),
            "source_iv": n(row.get("implied_volatility")), "leg": leg,
        }
    return {
        "status": "PAIR_SELECTED", "expiry": expiry,
        "dte": (date.fromisoformat(expiry)-date.fromisoformat(session_day)).days,
        "short": serialize_leg(short, "SHORT"), "wing": serialize_leg(wing, "LONG_WING"),
        "width": width, "gross_observed_side_credit_per_share": gross_credit,
        "delta_score": score, "evidence": EVIDENCE,
        "root_blocked_rows": root_blocked, "invalid_or_no_size_rows": quote_rejected,
    }


def quote_map(rows):
    result = {}
    for row in rows:
        ident = normalized_contract_id(row.get("contract_id"))
        if ident:
            result[ident] = row
    return result


def refresh_pair_for_entry(signal_pair, rows_by_id, session_day):
    """Reprice the exact contracts selected at the prior session's close.

    This prevents using next-session Delta/contract identity to choose a trade
    and then pretending the same EOD quote was an ex-ante selection.
    """
    if not signal_pair or signal_pair.get("status") != "PAIR_SELECTED":
        return {"status": "NO_VALID_PAIR_AT_SIGNAL_CLOSE"}
    selected_short = signal_pair["short"]
    selected_wing = signal_pair["wing"]
    short = rows_by_id.get(selected_short["contract_id"])
    wing = rows_by_id.get(selected_wing["contract_id"])
    if short is None or wing is None:
        return {"status": "SIGNAL_CONTRACT_MISSING_NEXT_SESSION"}
    for row, selected in ((short, selected_short), (wing, selected_wing)):
        if day(row.get("date")) != session_day:
            return {"status": "STALE_OR_MIXED_ENTRY_QUOTE_DATE"}
        if str(row.get("symbol", "")).upper() != "QQQ":
            return {"status": "ENTRY_UNDERLYING_MISMATCH"}
        if str(row.get("type", "")).strip().lower() not in ("c", "call"):
            return {"status": "ENTRY_OPTION_RIGHT_MISMATCH"}
        if normalized_contract_id(row.get("contract_id")) != selected["contract_id"]:
            return {"status": "ENTRY_CONTRACT_ID_MISMATCH"}
        if contract_root(row.get("contract_id")) != "QQQ":
            return {"status": "ENTRY_CONTRACT_ROOT_UNVERIFIED"}
        if day(row.get("expiration")) != signal_pair["expiry"]:
            return {"status": "ENTRY_EXPIRY_MISMATCH"}
        if n(row.get("strike")) is None or abs(n(row.get("strike")) - selected["strike"]) > 1e-8:
            return {"status": "ENTRY_STRIKE_MISMATCH"}
        if not valid_quote(row, require_size=True):
            return {"status": "INVALID_OR_UNSIZED_ENTRY_QUOTE"}
    dte = (date.fromisoformat(signal_pair["expiry"]) - date.fromisoformat(session_day)).days
    if dte <= 0:
        return {"status": "SIGNAL_CONTRACT_EXPIRED_BEFORE_ENTRY"}
    width = n(wing.get("strike")) - n(short.get("strike"))
    gross_credit = n(short.get("bid")) - n(wing.get("ask"))
    if width is None or width <= 0 or gross_credit is None or gross_credit <= 0 or gross_credit >= width:
        return {"status": "NONPOSITIVE_OR_INVALID_NEXT_SESSION_CREDIT"}

    def leg(row, name):
        return {
            "contract_id": normalized_contract_id(row.get("contract_id")),
            "root": contract_root(row.get("contract_id")),
            "expiry": signal_pair["expiry"], "strike": n(row.get("strike")),
            "delta": n(row.get("delta")), "bid": n(row.get("bid")),
            "ask": n(row.get("ask")), "bid_size": n(row.get("bid_size")),
            "ask_size": n(row.get("ask_size")), "volume": n(row.get("volume")),
            "open_interest": n(row.get("open_interest")),
            "source_iv": n(row.get("implied_volatility")), "leg": name,
        }
    return {
        "status": "PAIR_SELECTED", "expiry": signal_pair["expiry"], "dte": dte,
        "short": leg(short, "SHORT"), "wing": leg(wing, "LONG_WING"),
        "width": width, "gross_observed_side_credit_per_share": gross_credit,
        "delta_score": signal_pair.get("delta_score"),
        "selected_on_signal_date": True, "signal_date": session_day,
        "evidence": EVIDENCE,
    }


def close_side_debit_per_share(position, rows_by_id, slippage, commission, require_size=False):
    short = rows_by_id.get(position["short_id"])
    wing = rows_by_id.get(position["wing_id"])
    if short is None or wing is None:
        return None, "CONTRACT_ROW_MISSING"
    if not valid_quote(short, require_size=require_size) or not valid_quote(wing, require_size=require_size):
        return None, "INVALID_EXIT_QUOTE" if not require_size else "INVALID_OR_UNSIZED_EXIT_QUOTE"
    if contract_root(short.get("contract_id")) != "QQQ" or contract_root(wing.get("contract_id")) != "QQQ":
        return None, "EXIT_CONTRACT_ROOT_UNVERIFIED"
    short_ask, wing_bid = n(short.get("ask")), n(wing.get("bid"))
    if short_ask is None or wing_bid is None or short_ask < wing_bid:
        return None, "INCONSISTENT_VERTICAL_EXIT_MARK"
    # Add slippage and fees on both legs for closing; assumptions are explicit scenarios.
    return short_ask - wing_bid + 2 * slippage + 2 * commission / 100, "OK"


def entry_net_credit_per_share(pair, slippage, commission):
    return pair["gross_observed_side_credit_per_share"] - 2 * slippage - 2 * commission / 100


def loss_budget_per_spread(pair, net_credit_ps, slippage, commission):
    # Worst-case vertical width less net entry cash credit, plus assumed close costs.
    close_cost_per_spread = 2 * slippage * 100 + 2 * commission
    return max(0.0, (pair["width"] - net_credit_ps) * 100 + close_cost_per_spread)


def pick_quantity(nav, pair, budget_mode, net_credit_ps, slippage, commission):
    if nav is None or nav <= 0 or pair is None or net_credit_ps <= 0:
        return 0, None
    budget = nav * budget_mode["pct"]
    if budget_mode["kind"] == "credit":
        denom = net_credit_ps * 100
        risk = loss_budget_per_spread(pair, net_credit_ps, slippage, commission)
        return (math.floor(budget / denom) if denom > 0 else 0), risk
    risk = loss_budget_per_spread(pair, net_credit_ps, slippage, commission)
    return (math.floor(budget / risk) if risk > 0 else 0), risk


def regime(vix):
    x = n(vix)
    if x is None: return "UNKNOWN"
    if x < 15: return "LOW_LT15"
    if x < 25: return "NORMAL_15_25"
    if x < 35: return "ELEVATED_25_35"
    return "HIGH_GTE35"


def quote_spread_pct_mid(row):
    """Observed leg spread as % of midpoint; diagnostic only, not a fill probability."""
    bid, ask = n(row.get("bid")), n(row.get("ask"))
    if bid is None or ask is None or bid <= 0 or ask < bid:
        return None
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return None
    return (ask - bid) / mid * 100.0


def quote_quality_bucket(short_spread_pct_mid, wing_spread_pct_mid):
    """Explicit descriptive bins; they do not gate trades or assert fillability."""
    values = [n(short_spread_pct_mid), n(wing_spread_pct_mid)]
    if any(value is None for value in values):
        return "UNKNOWN_QUOTE_SPREAD"
    widest = max(values)
    if widest <= SPREAD_TIGHT_MAX_PCT_MID:
        return "TIGHT_LE_10PCT_MID"
    if widest <= SPREAD_MODERATE_MAX_PCT_MID:
        return "MODERATE_10_25PCT_MID"
    return "WIDE_GT25PCT_MID"


def raw_spot_momentum20(raw_spot, prior_history):
    """20-session nominal-close momentum, used only to stratify attribution."""
    current = n(raw_spot)
    if current is None or current <= 0:
        return None, "UNKNOWN_CURRENT_RAW_SPOT"
    if len(prior_history) < TREND_LOOKBACK_SESSIONS:
        return None, "UNKNOWN_INSUFFICIENT_20_SESSION_HISTORY"
    reference = n(prior_history[-TREND_LOOKBACK_SESSIONS][1])
    if reference is None or reference <= 0:
        return None, "UNKNOWN_MISSING_20_SESSION_REFERENCE"
    change = current / reference - 1.0
    if change >= TREND_MOMENTUM_BAND:
        label = "UP_GE_2PCT_20S"
    elif change <= -TREND_MOMENTUM_BAND:
        label = "DOWN_LE_NEG2PCT_20S"
    else:
        label = "RANGE_ABS_LT2PCT_20S"
    return change, label


def attribute_closed_trade(trade):
    """Reconcile closed-trade cash flows without inventing marks or fills."""
    out = dict(trade)
    quantity = n(trade.get("quantity"))
    gross_entry_ps = n(trade.get("entry_gross_credit_per_share"))
    net_entry_ps = n(trade.get("entry_net_credit_ps"))
    net_exit_ps = n(trade.get("exit_net_debit_per_share"))
    realized = n(trade.get("realized_pnl_after_scenario_costs"))
    if any(value is None for value in (quantity, gross_entry_ps, net_entry_ps, net_exit_ps, realized)) or quantity < 1:
        out.update({
            "attribution_status": "BLOCKED_MISSING_CASH_FLOW_FIELDS",
            "entry_gross_credit_cash_usd": None, "entry_execution_costs_usd": None,
            "exit_gross_debit_cash_usd": None, "exit_execution_costs_usd": None,
            "recomputed_net_pnl_usd": None, "pnl_reconciliation_error_usd": None,
            "loss_as_pct_entry_max_loss": None,
        })
        return out

    # Entry cash received before costs is the short Bid minus long-wing Ask.
    entry_gross_cash = gross_entry_ps * 100.0 * quantity
    entry_costs = (gross_entry_ps - net_entry_ps) * 100.0 * quantity
    intrinsic_exit = n(trade.get("exit_intrinsic_debit_per_share"))
    if intrinsic_exit is not None:
        exit_gross_ps = intrinsic_exit
        exit_basis = "INTRINSIC_SETTLEMENT_PROXY"
    else:
        short_ask = n(trade.get("exit_short_ask"))
        wing_bid = n(trade.get("exit_wing_bid"))
        if short_ask is None or wing_bid is None:
            out.update({
                "attribution_status": "BLOCKED_MISSING_EXIT_SIDE_QUOTES",
                "entry_gross_credit_cash_usd": round(entry_gross_cash, 6),
                "entry_execution_costs_usd": round(entry_costs, 6),
                "exit_gross_debit_cash_usd": None, "exit_execution_costs_usd": None,
                "recomputed_net_pnl_usd": None, "pnl_reconciliation_error_usd": None,
                "loss_as_pct_entry_max_loss": None,
            })
            return out
        exit_gross_ps = short_ask - wing_bid
        exit_basis = "OBSERVED_EOD_SHORT_ASK_MINUS_WING_BID"
    exit_gross_cash = exit_gross_ps * 100.0 * quantity
    exit_costs = (net_exit_ps - exit_gross_ps) * 100.0 * quantity
    recomputed = entry_gross_cash - entry_costs - exit_gross_cash - exit_costs
    error = recomputed - realized
    risk = n(trade.get("entry_total_max_loss_scenario_usd"))
    loss_utilization = (max(0.0, -realized) / risk * 100.0) if risk is not None and risk > 0 else None

    short_delta_drift = n(trade.get("exit_short_delta_drift"))
    if short_delta_drift is None:
        entry_delta, exit_delta = n(trade.get("short_delta")), n(trade.get("exit_short_delta"))
        if entry_delta is not None and exit_delta is not None:
            short_delta_drift = exit_delta - entry_delta
    wing_delta_drift = n(trade.get("exit_wing_delta_drift"))
    if wing_delta_drift is None:
        entry_delta, exit_delta = n(trade.get("wing_delta")), n(trade.get("exit_wing_delta"))
        if entry_delta is not None and exit_delta is not None:
            wing_delta_drift = exit_delta - entry_delta

    out.update({
        "entry_gross_credit_cash_usd": round(entry_gross_cash, 6),
        "entry_execution_costs_usd": round(entry_costs, 6),
        "exit_gross_debit_per_share": round(exit_gross_ps, 8),
        "exit_gross_debit_cash_usd": round(exit_gross_cash, 6),
        "exit_execution_costs_usd": round(exit_costs, 6),
        "exit_debit_basis": exit_basis,
        "recomputed_net_pnl_usd": round(recomputed, 6),
        "pnl_reconciliation_error_usd": round(error, 8),
        "attribution_status": "PASS_CASH_FLOW_RECONCILIATION" if abs(error) <= 0.01 else "FAIL_CASH_FLOW_RECONCILIATION",
        "entry_year": str(trade.get("entry_date") or "")[:4] or "UNKNOWN",
        "exit_year": str(trade.get("exit_date") or "")[:4] or "UNKNOWN",
        "loss_as_pct_entry_max_loss": round(loss_utilization, 6) if loss_utilization is not None else None,
        "short_delta_drift": round(short_delta_drift, 8) if short_delta_drift is not None else None,
        "wing_delta_drift": round(wing_delta_drift, 8) if wing_delta_drift is not None else None,
        "entry_quote_quality_bucket": quote_quality_bucket(
            trade.get("entry_short_spread_pct_mid"), trade.get("entry_wing_spread_pct_mid")),
        "exit_quote_quality_bucket": quote_quality_bucket(
            trade.get("exit_short_spread_pct_mid"), trade.get("exit_wing_spread_pct_mid")),
    })
    return out


def _trade_group_metrics(trades):
    def values(key):
        return [x for row in trades if (x := n(row.get(key))) is not None]
    def total(key):
        xs = values(key)
        return round(sum(xs), 6) if xs else None
    pnl = values("realized_pnl_after_scenario_costs")
    loss_util = values("loss_as_pct_entry_max_loss")
    short_drift = values("short_delta_drift")
    wing_drift = values("wing_delta_drift")
    holding = values("holding_calendar_days")
    errors = values("pnl_reconciliation_error_usd")
    statuses = [row.get("attribution_status") for row in trades]
    return {
        "trade_count": len(trades),
        "net_pnl_usd": round(sum(pnl), 2) if pnl else 0.0,
        "mean_net_pnl_usd": round(sum(pnl) / len(pnl), 2) if pnl else None,
        "win_fraction": sum(value > 0 for value in pnl) / len(pnl) if pnl else None,
        "entry_gross_credit_cash_usd": total("entry_gross_credit_cash_usd"),
        "entry_execution_costs_usd": total("entry_execution_costs_usd"),
        "exit_gross_debit_cash_usd": total("exit_gross_debit_cash_usd"),
        "exit_execution_costs_usd": total("exit_execution_costs_usd"),
        "recomputed_net_pnl_usd": total("recomputed_net_pnl_usd"),
        "reconciliation_failures": sum(value == "FAIL_CASH_FLOW_RECONCILIATION" for value in statuses),
        "reconciliation_blocked": sum(str(value).startswith("BLOCKED") for value in statuses),
        "max_abs_reconciliation_error_usd": round(max(abs(value) for value in errors), 8) if errors else None,
        "mean_loss_as_pct_entry_max_loss": round(sum(loss_util) / len(loss_util), 6) if loss_util else None,
        "mean_short_delta_drift": round(sum(short_drift) / len(short_drift), 8) if short_drift else None,
        "mean_wing_delta_drift": round(sum(wing_drift) / len(wing_drift), 8) if wing_drift else None,
        "mean_holding_calendar_days": round(sum(holding) / len(holding), 4) if holding else None,
    }


def build_trade_attribution(trades):
    """Build by-scenario and stratified closed-trade diagnostics; no portfolio metrics."""
    dimensions = ("exit_reason", "entry_regime", "exit_regime", "entry_trend_regime",
                  "exit_trend_regime", "entry_quote_quality_bucket", "entry_year")
    by_scenario = {}
    csv_rows = []
    scenario_ids = sorted({str(row.get("scenario_id") or row.get("scenario") or "UNKNOWN") for row in trades})
    for scenario_id in scenario_ids:
        subset = [row for row in trades if str(row.get("scenario_id") or row.get("scenario") or "UNKNOWN") == scenario_id]
        scenario_summary = _trade_group_metrics(subset)
        scenario_summary["groups"] = {}
        for dimension in dimensions:
            groups = defaultdict(list)
            for row in subset:
                value = row.get(dimension)
                if value in (None, ""):
                    value = "UNKNOWN"
                groups[str(value)].append(row)
            scenario_summary["groups"][dimension] = {}
            for bucket in sorted(groups):
                metrics = _trade_group_metrics(groups[bucket])
                scenario_summary["groups"][dimension][bucket] = metrics
                csv_rows.append({
                    "scenario_id": scenario_id, "dimension": dimension, "bucket": bucket,
                    **metrics,
                })
        by_scenario[scenario_id] = scenario_summary
    total_metrics = _trade_group_metrics(trades)
    summary = {
        "status": "CLOSED_TRADE_ATTRIBUTION_ONLY; NOT_PORTFOLIO_PERFORMANCE",
        "closed_trade_rows": len(trades),
        "reconciliation_pass_rows": sum(row.get("attribution_status") == "PASS_CASH_FLOW_RECONCILIATION" for row in trades),
        "reconciliation_fail_rows": sum(row.get("attribution_status") == "FAIL_CASH_FLOW_RECONCILIATION" for row in trades),
        "reconciliation_blocked_rows": sum(str(row.get("attribution_status", "")).startswith("BLOCKED") for row in trades),
        "all_scenario_cash_flow_totals": total_metrics,
        "scenarios": by_scenario,
        "group_rows_count": len(csv_rows),
        "classification_note": (
            "entry/exit regime and 20-session raw-spot momentum are post-hoc diagnostic strata only; "
            "spread buckets use max leg spread/midpoint <=10%, <=25%, >25%; none is a trade rule."
        ),
    }
    return summary, csv_rows


class Replay:
    def __init__(self, budget_mode, slippage, commission):
        self.mode = budget_mode
        self.slippage = slippage
        self.commission = commission
        self.cash = INITIAL_CAPITAL * (1 - QQQ_CORE_FRACTION)
        self.initial_core_value = INITIAL_CAPITAL * QQQ_CORE_FRACTION
        self.first_adj_close = None
        self.position = None
        self.pending_open = False
        self.pending_selection = None
        self.pending_close = False
        self.events = []
        self.trades = []
        self.daily = []
        self.counters = Counter()
        self.mark_status_counts = Counter()
        self.mark_failure_samples = []
        self.exit_quote_size_missing_sessions = 0
        self.last_raw_spot_date = None
        self.last_raw_spot = None
        self.expiry_settlement_fallbacks = 0
        self.expiry_settlement_missing_spot = 0
        self.missing_position_mark_dates = []
        self.last_valid_nav = None
        self.unresolved_positions = []
        self.expired_unresolved_keys = set()
        self.raw_spot_history = []  # one slot per expected session; missing closes remain explicit
        self._signal_vix = None
        self._signal_momentum20_pct = None
        self._signal_trend_regime = "UNKNOWN"
        self.max_open_max_loss_usd = 0.0
        self.max_open_max_loss_pct_nav = 0.0

    def _core_value(self, spot_info):
        adj = n((spot_info or {}).get("adjusted_close"))
        if adj is None or adj <= 0:
            return None
        if self.first_adj_close is None:
            self.first_adj_close = adj
        return self.initial_core_value * adj / self.first_adj_close

    def _nav(self, core_value, position, quotes, day_key):
        if core_value is None:
            return None, "CORE_TOTAL_RETURN_PRICE_MISSING"
        if position is None:
            return core_value + self.cash, "OK"
        exp_day = date.fromisoformat(position["expiry"])
        if date.fromisoformat(day_key) >= exp_day:
            return None, "POSITION_AT_OR_AFTER_EXPIRY"
        debit, status = close_side_debit_per_share(position, quotes, self.slippage, self.commission)
        if debit is None:
            return None, status
        return core_value + self.cash - debit * 100 * position["quantity"], "OK"

    def process(self, day_key, rows, spot_info, vix_value, selected_pair=None, qmap_override=None):
        supplied_map = qmap_override if qmap_override is not None else quote_map(rows)
        row_dates = {day(row.get("date")) for row in rows}
        map_dates = {day(row.get("date")) for row in supplied_map.values()}
        stale_or_mixed = (bool(rows) and row_dates != {day_key}) or (bool(supplied_map) and map_dates != {day_key})
        if stale_or_mixed:
            # A quote with a prior/future/missing timestamp must never be reused.
            self.counters["stale_or_mixed_chain_dates"] += 1
            rows = []
            supplied_map = {}
            selected_pair = {"status": "STALE_OR_MIXED_CHAIN_DATE"}
        chain_present = bool(rows)
        self.counters["expected_sessions"] += 1
        if chain_present:
            self.counters["chain_sessions"] += 1
        else:
            self.counters["missing_chain_sessions"] += 1
        raw_spot = n((spot_info or {}).get("raw_close"))
        trend_momentum20_pct, trend_regime_key = raw_spot_momentum20(raw_spot, self.raw_spot_history)
        core_value = self._core_value(spot_info)
        qmap = supplied_map
        if selected_pair is None:
            selected_pair = choose_vertical(rows, day_key) if chain_present else {"status": "NO_CHAIN"}
        if selected_pair.get("status") == "PAIR_SELECTED":
            self.counters["candidate_pair_sessions"] += 1
        else:
            self.counters["no_valid_pair_sessions"] += 1

        executed_close_today = False
        # Resolve a defined-risk call vertical at expiration using intrinsic value.
        # If expiry is a non-session date or the exact expiry close is absent, a
        # prior-session spot may be used only as an explicitly tagged fallback.
        if self.position is not None and date.fromisoformat(day_key) >= date.fromisoformat(self.position["expiry"]):
            p = self.position
            expiry_day = date.fromisoformat(p["expiry"])
            current_day = date.fromisoformat(day_key)
            settlement_spot = None
            settlement_price_date = None
            settlement_basis = None
            if current_day == expiry_day and raw_spot is not None:
                settlement_spot = raw_spot
                settlement_price_date = day_key
                settlement_basis = "OBSERVED_RAW_CLOSE_ON_EXPIRY_DATE"
            elif (current_day > expiry_day and self.last_raw_spot is not None and
                  self.last_raw_spot_date is not None and
                  date.fromisoformat(self.last_raw_spot_date) < expiry_day):
                settlement_spot = self.last_raw_spot
                settlement_price_date = self.last_raw_spot_date
                settlement_basis = "FALLBACK_LAST_OBSERVED_SESSION_BEFORE_EXPIRY"
                self.expiry_settlement_fallbacks += 1
            if settlement_spot is not None:
                intrinsic_short = max(settlement_spot - p["short_strike"], 0.0)
                intrinsic_wing = max(settlement_spot - p["wing_strike"], 0.0)
                intrinsic_debit = max(0.0, min(p["width"], intrinsic_short - intrinsic_wing))
                friction = 2 * self.slippage + 2 * self.commission / 100
                debit = intrinsic_debit + friction
                realized = (p["entry_net_credit_ps"] - debit) * 100 * p["quantity"]
                self.cash -= debit * 100 * p["quantity"]
                trade = {
                    **p, "exit_date": day_key, "settlement_price_date": settlement_price_date,
                    "settlement_spot": settlement_spot, "settlement_basis": settlement_basis,
                    "exit_reason": "EXPIRY_INTRINSIC_SETTLEMENT",
                    "exit_raw_spot": settlement_spot,
                    "exit_vix": n(vix_value) if settlement_price_date == day_key else None,
                    "exit_regime": regime(vix_value) if settlement_price_date == day_key else "UNKNOWN_SETTLEMENT_DATE_ALIGNMENT",
                    "exit_momentum20_pct": trend_momentum20_pct if settlement_price_date == day_key else None,
                    "exit_trend_regime": trend_regime_key if settlement_price_date == day_key else "UNKNOWN_SETTLEMENT_DATE_ALIGNMENT",
                    "exit_short_delta": None, "exit_wing_delta": None,
                    "exit_short_spread_pct_mid": None, "exit_wing_spread_pct_mid": None,
                    "exit_intrinsic_debit_per_share": intrinsic_debit,
                    "exit_net_debit_per_share": debit,
                    "realized_pnl_after_scenario_costs": realized,
                    "holding_calendar_days": (date.fromisoformat(day_key) - date.fromisoformat(p["entry_date"])).days,
                    "status": "SETTLED_INTRINSIC_PROXY_NOT_CONFIRMED_EXERCISE",
                }
                self.trades.append(trade)
                self.events.append({
                    "date": day_key, "event": "EXPIRY_SETTLEMENT_PROXY",
                    "settlement_price_date": settlement_price_date, "settlement_spot": settlement_spot,
                    "settlement_basis": settlement_basis, "intrinsic_debit_per_share": intrinsic_debit,
                    "net_debit_per_share_with_scenario_costs": debit, "realized_pnl": round(realized, 2),
                    "quantity": p["quantity"], "budget_mode": self.mode["name"],
                    "slippage_per_leg": self.slippage,
                    "commission_per_contract_per_side": self.commission,
                })
                self.position = None
                self.pending_close = False
                self.pending_open = False
                self.pending_selection = None
                self.counters["closed_trades"] += 1
                self.counters["expiry_settlements"] += 1
                executed_close_today = True
            else:
                self.expiry_settlement_missing_spot += 1
                self.counters["expiry_settlement_missing_spot"] += 1

        if self.position is not None and self.pending_close and chain_present and date.fromisoformat(day_key) < date.fromisoformat(self.position["expiry"]):
            debit, status = close_side_debit_per_share(self.position, qmap, self.slippage, self.commission)
            exp = date.fromisoformat(self.position["expiry"])
            if debit is not None and date.fromisoformat(day_key) < exp:
                p = self.position
                realized = (p["entry_net_credit_ps"] - debit) * 100 * p["quantity"]
                self.cash -= debit * 100 * p["quantity"]
                trade = {
                    **p, "exit_date": day_key, "exit_reason": p.get("exit_reason", "RULE_EXIT"),
                    "exit_short_bid": n(qmap[p["short_id"]].get("bid")),
                    "exit_short_ask": n(qmap[p["short_id"]].get("ask")),
                    "exit_wing_bid": n(qmap[p["wing_id"]].get("bid")),
                    "exit_wing_ask": n(qmap[p["wing_id"]].get("ask")),
                    "exit_short_delta": n(qmap[p["short_id"]].get("delta")),
                    "exit_wing_delta": n(qmap[p["wing_id"]].get("delta")),
                    "exit_short_spread_pct_mid": quote_spread_pct_mid(qmap[p["short_id"]]),
                    "exit_wing_spread_pct_mid": quote_spread_pct_mid(qmap[p["wing_id"]]),
                    "exit_short_delta_drift": (n(qmap[p["short_id"]].get("delta")) - n(p.get("short_delta"))) if n(qmap[p["short_id"]].get("delta")) is not None and n(p.get("short_delta")) is not None else None,
                    "exit_wing_delta_drift": (n(qmap[p["wing_id"]].get("delta")) - n(p.get("wing_delta"))) if n(qmap[p["wing_id"]].get("delta")) is not None and n(p.get("wing_delta")) is not None else None,
                    "exit_raw_spot": raw_spot, "exit_vix": n(vix_value),
                    "exit_regime": regime(vix_value), "exit_momentum20_pct": trend_momentum20_pct,
                    "exit_trend_regime": trend_regime_key,
                    "exit_net_debit_per_share": debit, "realized_pnl_after_scenario_costs": realized,
                    "holding_calendar_days": (date.fromisoformat(day_key)-date.fromisoformat(p["entry_date"])).days,
                    "status": "CLOSED_EOD_SIDE_PROXY_NOT_CONFIRMED_FILL",
                }
                self.trades.append(trade)
                self.events.append({"date": day_key, "event": "CLOSE", "status": status,
                                    "quantity": p["quantity"], "realized_pnl": round(realized, 2),
                                    "reason": p.get("exit_reason"), "budget_mode": self.mode["name"],
                                    "slippage_per_leg": self.slippage, "commission_per_contract_per_side": self.commission})
                self.position = None
                self.pending_close = False
                executed_close_today = True
                self.counters["closed_trades"] += 1
            else:
                self.counters["exit_delayed_missing_quote"] += 1
                self.events.append({"date": day_key, "event": "CLOSE_DEFERRED", "status": status,
                                    "reason": self.position.get("exit_reason"), "budget_mode": self.mode["name"]})

        just_opened = False
        if self.position is None and self.pending_open and chain_present:
            self.pending_open = False
            signal_pair = self.pending_selection
            self.pending_selection = None
            if raw_spot is None or core_value is None:
                self.counters["entry_blocked_missing_spot"] += 1
                self.events.append({"date": day_key, "event": "ENTRY_BLOCKED", "reason": "RAW_OR_ADJUSTED_SPOT_MISSING"})
            else:
                pair = refresh_pair_for_entry(signal_pair, qmap, day_key)
                if pair.get("status") != "PAIR_SELECTED":
                    self.counters["entry_no_valid_pair"] += 1
                    self.events.append({"date": day_key, "event": "ENTRY_SKIPPED",
                                        "reason": pair.get("status"), "signal_date": self._signal_date})
                else:
                    net_credit = entry_net_credit_per_share(pair, self.slippage, self.commission)
                    nav_for_sizing = core_value + self.cash
                    quantity, max_loss = pick_quantity(nav_for_sizing, pair, self.mode, net_credit,
                                                       self.slippage, self.commission)
                    if net_credit <= 0:
                        self.counters["entry_nonpositive_credit"] += 1
                        self.events.append({"date": day_key, "event": "ENTRY_BLOCKED",
                                            "reason": "NONPOSITIVE_NET_CREDIT_AFTER_COSTS"})
                    elif quantity < 1:
                        self.counters["entry_quantity_zero"] += 1
                        self.events.append({"date": day_key, "event": "ENTRY_SKIPPED",
                                            "reason": "BUDGET_BELOW_ONE_SPREAD",
                                            "nav_for_sizing": round(nav_for_sizing, 2)})
                    else:
                        self.cash += net_credit * 100 * quantity
                        total_max_loss = max_loss * quantity
                        self.max_open_max_loss_usd = max(self.max_open_max_loss_usd, total_max_loss)
                        self.max_open_max_loss_pct_nav = max(self.max_open_max_loss_pct_nav,
                                                              total_max_loss / nav_for_sizing if nav_for_sizing > 0 else 0.0)
                        self.position = {
                            "budget_mode": self.mode["name"], "slippage_per_leg": self.slippage,
                            "commission_per_contract_per_side": self.commission,
                            "signal_date": self._signal_date, "entry_date": day_key,
                            "signal_vix": self._signal_vix, "signal_regime": regime(self._signal_vix),
                            "signal_momentum20_pct": self._signal_momentum20_pct,
                            "signal_trend_regime": self._signal_trend_regime,
                            "entry_raw_spot": raw_spot, "entry_vix": n(vix_value),
                            "entry_momentum20_pct": trend_momentum20_pct, "entry_trend_regime": trend_regime_key,
                            "entry_selection_expiry": signal_pair.get("expiry") if signal_pair else None,
                            "entry_short_bid": pair["short"]["bid"], "entry_short_ask": pair["short"]["ask"],
                            "entry_wing_bid": pair["wing"]["bid"], "entry_wing_ask": pair["wing"]["ask"],
                            "entry_short_spread_pct_mid": quote_spread_pct_mid(pair["short"]),
                            "entry_wing_spread_pct_mid": quote_spread_pct_mid(pair["wing"]),
                            "entry_quote_quality_bucket": quote_quality_bucket(quote_spread_pct_mid(pair["short"]), quote_spread_pct_mid(pair["wing"])),
                            "entry_gross_credit_per_share": pair["gross_observed_side_credit_per_share"],
                            "entry_net_credit_ps": net_credit, "entry_cash_credit": net_credit*100*quantity,
                            "short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"],
                            "expiry": pair["expiry"], "short_strike": pair["short"]["strike"],
                            "wing_strike": pair["wing"]["strike"], "short_delta": pair["short"]["delta"],
                            "wing_delta": pair["wing"]["delta"], "width": pair["width"],
                            "entry_dte": pair["dte"], "quantity": quantity,
                            "max_loss_per_spread_scenario": max_loss,
                            "entry_total_max_loss_scenario_usd": total_max_loss,
                            "entry_total_max_loss_pct_nav": total_max_loss / nav_for_sizing if nav_for_sizing > 0 else None,
                            "source_status": EVIDENCE, "exit_reason": None,
                            "entry_regime": regime(vix_value),
                        }
                        self.counters["opened_trades"] += 1
                        self.events.append({"date": day_key, "event": "OPEN",
                                            "expiry": pair["expiry"], "short_id": pair["short"]["contract_id"],
                                            "wing_id": pair["wing"]["contract_id"], "short_strike": pair["short"]["strike"],
                                            "wing_strike": pair["wing"]["strike"], "short_delta": pair["short"]["delta"],
                                            "wing_delta": pair["wing"]["delta"], "dte": pair["dte"],
                                            "gross_credit_per_share": pair["gross_observed_side_credit_per_share"],
                                            "net_credit_per_share": net_credit, "quantity": quantity,
                                            "max_loss_per_spread_scenario": round(max_loss, 4),
                                            "nav_for_sizing": round(nav_for_sizing, 2), "budget_mode": self.mode["name"],
                                            "slippage_per_leg": self.slippage,
                                            "commission_per_contract_per_side": self.commission,
                                            "selection_signal_date": self._signal_date,
                                            "source_status": EVIDENCE})
                        just_opened = True
        elif self.position is None and self.pending_open and not chain_present:
            self.pending_open = False
            self.pending_selection = None
            self.counters["entry_skipped_missing_next_session_chain"] += 1
            self.events.append({"date": day_key, "event": "ENTRY_SKIPPED",
                                "reason": "NO_NEXT_SESSION_CHAIN", "signal_date": self._signal_date})

        # Mark existing positions only from the current exact contract rows; never forward-fill.
        nav, mark_status = self._nav(core_value, self.position, qmap, day_key)
        self.mark_status_counts[mark_status] += 1
        if self.position is not None and qmap:
            short_row = qmap.get(self.position["short_id"])
            wing_row = qmap.get(self.position["wing_id"])
            if short_row is not None and wing_row is not None and (
                n(short_row.get("bid_size")) is None or n(short_row.get("ask_size")) is None or
                n(wing_row.get("bid_size")) is None or n(wing_row.get("ask_size")) is None or
                n(short_row.get("bid_size")) <= 0 or n(short_row.get("ask_size")) <= 0 or
                n(wing_row.get("bid_size")) <= 0 or n(wing_row.get("ask_size")) <= 0
            ):
                self.exit_quote_size_missing_sessions += 1
        if nav is None:
            if len(self.mark_failure_samples) < 8:
                self.mark_failure_samples.append({
                    "date": day_key, "mark_status": mark_status,
                    "position_expiry": self.position.get("expiry") if self.position else None,
                    "short_id": self.position.get("short_id") if self.position else None,
                    "wing_id": self.position.get("wing_id") if self.position else None,
                    "chain_present": chain_present, "quote_rows": len(qmap),
                    "core_value_missing": core_value is None,
                })
            self.counters["unmarked_nav_sessions"] += 1
            if self.position is not None:
                self.missing_position_mark_dates.append(day_key)
                self.counters["missing_position_mark_sessions"] += 1
        else:
            self.counters["marked_nav_sessions"] += 1
            self.last_valid_nav = nav
        if self.position is not None and chain_present and not just_opened and not self.pending_close:
            debit, status = close_side_debit_per_share(self.position, qmap, self.slippage, self.commission)
            if debit is not None and date.fromisoformat(day_key) < date.fromisoformat(self.position["expiry"]):
                pnl_per_spread = (self.position["entry_net_credit_ps"] - debit) * 100
                risk = self.position["max_loss_per_spread_scenario"]
                pnl_over_risk = pnl_per_spread / risk if risk and risk > 0 else None
                dte = (date.fromisoformat(self.position["expiry"])-date.fromisoformat(day_key)).days
                reason = None
                if dte <= STOP_DTE: reason = "DTE_LE_7"
                elif pnl_over_risk is not None and pnl_over_risk <= STOP_LOSS_OVER_MAXLOSS: reason = "PNL_OVER_MAXLOSS_LE_NEG_0P55"
                elif pnl_over_risk is not None and pnl_over_risk >= TAKE_PROFIT_OVER_MAXLOSS: reason = "PNL_OVER_MAXLOSS_GE_0P50"
                if reason:
                    self.pending_close = True
                    self.position["exit_reason"] = reason
                    self.counters["close_signals"] += 1
                    self.events.append({"date": day_key, "event": "CLOSE_SIGNAL_NEXT_SESSION",
                                        "reason": reason, "dte": dte,
                                        "mark_pnl_per_spread": round(pnl_per_spread, 4),
                                        "pnl_over_scenario_maxloss": round(pnl_over_risk, 6) if pnl_over_risk is not None else None,
                                        "source_status": EVIDENCE})
        # A close fills on today's quote only if its trigger was observed on a prior session.
        # Flat policy signals at today's close are eligible only for a future session.
        if self.position is None and not self.pending_close and chain_present and raw_spot is not None:
            self.pending_open = True
            self.pending_selection = selected_pair
            self._signal_date = day_key
            self._signal_vix = n(vix_value)
            self._signal_momentum20_pct = trend_momentum20_pct
            self._signal_trend_regime = trend_regime_key
        elif self.position is None and not chain_present:
            self.pending_open = False
            self.pending_selection = None

        marked = nav is not None
        self.daily.append({
            "date": day_key, "raw_spot": raw_spot, "adjusted_close_for_core_tr": n((spot_info or {}).get("adjusted_close")),
            "vix": n(vix_value), "regime": regime(vix_value),
            "raw_spot_momentum20_pct": trend_momentum20_pct, "raw_spot_trend_regime": trend_regime_key,
            "chain_present": chain_present,
            "quote_time_status": QUOTE_TIME_STATUS,
            "cash_balance": round(self.cash, 6), "core_value_adjusted_total_return_proxy": round(core_value, 6) if core_value is not None else None,
            "no_call_baseline_nav": round(core_value + INITIAL_CAPITAL * (1 - QQQ_CORE_FRACTION), 6) if core_value is not None else None,
            "nav_eod_marked": round(nav, 6) if nav is not None else None,
            "incremental_nav_vs_no_call": round(nav - (core_value + INITIAL_CAPITAL * (1 - QQQ_CORE_FRACTION)), 6) if nav is not None and core_value is not None else None,
            "nav_mark_status": mark_status, "position_open": self.position is not None,
            "position_short_id": self.position.get("short_id") if self.position else None,
            "position_wing_id": self.position.get("wing_id") if self.position else None,
            "position_expiry": self.position.get("expiry") if self.position else None,
            "position_quantity": self.position.get("quantity") if self.position else None,
            "pending_close": self.pending_close, "pending_open": self.pending_open,
            "pending_selection_expiry": self.pending_selection.get("expiry") if self.pending_selection and self.pending_selection.get("status") == "PAIR_SELECTED" else None,
            "source_status": EVIDENCE,
        })
        self.raw_spot_history.append((day_key, raw_spot))
        if raw_spot is not None:
            self.last_raw_spot_date = day_key
            self.last_raw_spot = raw_spot


def iter_qqq_chain_days(option_paths):
    """Yield one QQQ chain per source date; input files are SHA-verified by caller."""
    for path in option_paths:
        parquet = pq.ParquetFile(path)
        audit.assert_date_ordered_parquet(parquet, path)
        names = set(parquet.schema_arrow.names)
        missing = sorted(set(OPTION_COLUMNS) - names)
        if missing:
            raise ValueError(f"{path.name} missing required columns: {missing}")
        current_day, qqq_rows = None, []
        for batch in parquet.iter_batches(batch_size=65536, columns=OPTION_COLUMNS):
            for row in batch.to_pylist():
                row_day = day(row.get("date"))
                if not row_day:
                    continue
                if current_day is None:
                    current_day = row_day
                elif row_day != current_day:
                    if qqq_rows:
                        yield current_day, qqq_rows
                    current_day, qqq_rows = row_day, []
                if str(row.get("symbol", "")).upper() == "QQQ":
                    qqq_rows.append(row)
        if current_day is not None and qqq_rows:
            yield current_day, qqq_rows


def run_replay(out_dir):
    cache = Path(".cache/qqq-options-full-history")
    integrity, universe_by_day, spots, expected = audit.build_inputs(cache)
    expected = [d for d in expected if START_DATE <= d <= REQUESTED_END_DATE]
    option_paths, file_integrity = [], {}
    for spec in audit.ANNUAL_FILES:
        path, meta = audit.download_verified(spec, cache)
        option_paths.append(path)
        file_integrity[spec["name"]] = meta

    chain_iter = iter(iter_qqq_chain_days(option_paths))
    next_chain = next(chain_iter, None)
    replay_states = []
    for mode in BUDGET_MODES:
        for slip in SLIPPAGE_PER_LEG:
            for commission in COMMISSION_PER_CONTRACT_PER_SIDE:
                replay_states.append(Replay(mode, slip, commission))
    pair_statuses = Counter()
    chain_day_count = 0
    for session_day in expected:
        rows = []
        while next_chain is not None and next_chain[0] < session_day:
            # Data outside the configured universe is ignored; no data is forward-filled.
            next_chain = next(chain_iter, None)
        if next_chain is not None and next_chain[0] == session_day:
            rows = next_chain[1]
            next_chain = next(chain_iter, None)
            chain_day_count += 1
        pair = choose_vertical(rows, session_day) if rows else {"status": "NO_CHAIN"}
        pair_statuses[pair.get("status", "UNKNOWN")] += 1
        spot = spots.get(session_day)
        vix = (universe_by_day.get(session_day) or {}).get("vix")
        qmap = quote_map(rows)
        for state in replay_states:
            state.process(session_day, rows, spot, vix, pair, qmap)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scenarios, all_trades, all_events = [], [], []
    for state in replay_states:
        name = state.mode["name"]
        slip_tag = f"{state.slippage:.3f}"
        commission_tag = f"{state.commission:.2f}"
        closed = state.trades
        pnls = [n(t.get("realized_pnl_after_scenario_costs")) for t in closed]
        pnls = [x for x in pnls if x is not None]
        win_count = sum(x > 0 for x in pnls)
        loss_values = [t.get("max_loss_per_spread_scenario") for t in closed]
        scenario = {
            "scenario": name, "budget_kind": state.mode["kind"], "budget_pct_nav": state.mode["pct"],
            "slippage_per_leg_usd": state.slippage,
            "commission_per_contract_per_side_usd": state.commission,
            "commission_status": "HYPOTHETICAL_SCENARIO_NOT_BROKER_VERIFIED",
            "source_status": EVIDENCE,
            "initial_capital": INITIAL_CAPITAL, "qqq_core_total_return_fraction": QQQ_CORE_FRACTION,
            "source_last_observation": SOURCE_END_DATE, "requested_end": REQUESTED_END_DATE,
            "expected_sessions": len(expected), "sessions_with_chain": chain_day_count,
            "opened_spreads": state.counters["opened_trades"], "closed_spreads": len(closed),
            "unresolved_or_open_position_at_end": int(state.position is not None),
            "expired_unresolved": state.counters["expired_unresolved"],
            "close_signals": state.counters["close_signals"],
            "close_deferred_due_invalid_or_missing_quote": state.counters["exit_delayed_missing_quote"],
            "skipped_entry_missing_pair": state.counters["entry_no_valid_pair"],
            "entries_blocked_nonpositive_net_credit": state.counters["entry_nonpositive_credit"],
            "entry_quantity_zero": state.counters["entry_quantity_zero"],
            "stale_or_mixed_chain_dates_rejected": state.counters["stale_or_mixed_chain_dates"],
            "entry_skipped_missing_next_session_chain": state.counters["entry_skipped_missing_next_session_chain"],
            "missing_position_mark_sessions": state.counters["missing_position_mark_sessions"],
            "exit_quote_size_missing_sessions": state.exit_quote_size_missing_sessions,
            "expiry_settlements": state.counters["expiry_settlements"],
            "expiry_settlement_fallbacks": state.expiry_settlement_fallbacks,
            "expiry_settlement_missing_spot": state.expiry_settlement_missing_spot,
            "mark_status_counts": dict(state.mark_status_counts),
            "mark_failure_samples": state.mark_failure_samples,
            "unmarked_nav_sessions": state.counters["unmarked_nav_sessions"],
            "closed_trade_net_pnl_sum_usd": round(sum(pnls), 2) if pnls else 0.0,
            "mean_closed_trade_net_pnl_usd": round(sum(pnls)/len(pnls), 2) if pnls else None,
            "median_closed_trade_net_pnl_usd": median(pnls) if pnls else None,
            "max_open_max_loss_scenario_usd": round(state.max_open_max_loss_usd, 2),
            "max_open_max_loss_scenario_pct_nav": state.max_open_max_loss_pct_nav,
            "closed_trade_win_fraction": win_count/len(pnls) if pnls else None,
            "median_scenario_max_loss_per_spread_usd": sorted(n(x) for x in loss_values if n(x) is not None)[len([x for x in loss_values if n(x) is not None])//2] if any(n(x) is not None for x in loss_values) else None,
            "marked_nav_rows": state.counters["marked_nav_sessions"],
            "nav_path_complete": False,
            "performance_gate": "BLOCKED: EOD mirror is not confirmed fills; chain gaps and source cutoff make daily portfolio path incomplete",
            "cagr": None, "daily_mtm_maxdd": None, "sharpe": None, "es95": None,
            "open_position_at_end": state.position,
            "unresolved_positions": state.unresolved_positions,
        }
        scenarios.append(scenario)
        scenario_id = f"{name}|SLIP_PER_LEG_{state.slippage:.3f}|COMM_PER_CONTRACT_SIDE_{state.commission:.2f}"
        all_trades.extend([{**t, "scenario": name, "scenario_id": scenario_id,
                            "slippage_per_leg_usd": state.slippage,
                            "commission_per_contract_per_side_usd": state.commission}
                           for t in closed])
        all_events.extend([{**e, "scenario": name, "scenario_id": scenario_id,
                            "slippage_per_leg_usd": state.slippage,
                            "commission_per_contract_per_side_usd": state.commission}
                           for e in state.events])

    attributed_trades = [attribute_closed_trade(trade) for trade in all_trades]
    attribution_summary, attribution_group_rows = build_trade_attribution(attributed_trades)
    report = {
        "research_id": "QQQ_FAR_CALL_LISTED_CONTRACT_EOD_REPLAY_V1",
        "status": "RESEARCH_DIAGNOSTIC_NOT_PERFORMANCE_APPROVED",
        "strategy_policy_changed": False, "main_changed": False, "broker_orders_enabled": False,
        "not_opra_fills": True, "not_virgin_oos": True,
        "source": {"repository": "anahatsingh-ui/options-dataset-hist",
                   "source_type": "public preservation mirror; EOD option quote snapshots",
                   "reported_snapshot_time": "16:00 US/Eastern",
                   "exact_tick_timestamp_status": "UNVERIFIED",
                   "underlying_prices_and_option_quotes_are_not_exchange_confirmed_fills": True},
        "price_basis": {"qqq_options": "raw nominal QQQ close and actual listed strikes",
                        "qqq_core_accounting": "adjusted-close total-return proxy; kept separate"},
        "contract_selection": {"expiry": "closest eligible 20-40 DTE expiry to 30 DTE",
                               "short_call_delta_target": SHORT_DELTA_TARGET,
                               "long_wing_delta_target": WING_DELTA_TARGET,
                               "source_delta_used": True, "listed_strikes_only": True,
                               "require_occ_root_QQQ": True, "require_positive_bid_ask_and_size": True},
        "rules": {"source_max_loss_budget_pct_nav": 0.008, "alternate_legacy_credit_budget_pct_nav": 0.012,
                  "close_signal": f"DTE <= {STOP_DTE} or P&L/max-loss <= {STOP_LOSS_OVER_MAXLOSS} or >= {TAKE_PROFIT_OVER_MAXLOSS}",
                  "entry_exit_timing": "select actual contracts at close t; t+1 may reprice only those exact contract IDs from t+1 quotes; if either is missing/invalid, skip without substitution. Exit signal at t closes no earlier than next observed session. EOD-side prices are proxies, not fill proof.",
                  "slippage_scenarios_per_leg_usd": list(SLIPPAGE_PER_LEG),
                  "commission_per_contract_per_side_scenarios_usd": list(COMMISSION_PER_CONTRACT_PER_SIDE)},
        "coverage": {"expected_sessions": len(expected), "chain_sessions": chain_day_count,
                     "first_expected_date": expected[0] if expected else None,
                     "last_expected_date": expected[-1] if expected else None,
                     "last_source_observation": SOURCE_END_DATE,
                     "terminal_missing_sessions": [d for d in expected if d > SOURCE_END_DATE],
                     "days_by_pair_status": dict(pair_statuses),
                     "source_integrity": integrity, "option_file_integrity": file_integrity},
        "scenarios": scenarios,
        "trade_attribution": attribution_summary,
        "interpretation": "Only closed-spread event P&L is summarized. It is a quote-side proxy under explicit hypothetical costs, not confirmed fills. CAGR, daily MTM MaxDD, Sharpe, ES95 are intentionally NULL because the observation path is incomplete and EOD snapshots do not prove fills.",
    }
    (out_dir / "qqq_far_call_replay_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (out_dir / "qqq_far_call_replay_trades.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({k for x in attributed_trades for k in x})
        if not fields: fields = ["scenario", "status"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(attributed_trades)
    (out_dir / "qqq_far_call_replay_attribution.json").write_text(json.dumps(attribution_summary, indent=2), encoding="utf-8")
    with (out_dir / "qqq_far_call_replay_attribution.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({k for x in attribution_group_rows for k in x})
        if not fields: fields = ["scenario_id", "dimension", "bucket"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(attribution_group_rows)
    with (out_dir / "qqq_far_call_replay_events.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({k for x in all_events for k in x})
        if not fields: fields = ["scenario", "event"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(all_events)
    all_daily = []
    for state in replay_states:
        scenario_name = state.mode["name"]
        all_daily.extend([{**row, "scenario": scenario_name,
                           "slippage_per_leg_usd": state.slippage,
                           "commission_per_contract_per_side_usd": state.commission}
                          for row in state.daily])
    with (out_dir / "qqq_far_call_replay_daily.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({k for x in all_daily for k in x})
        if not fields: fields = ["scenario", "date", "nav_mark_status"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(all_daily)

    lines = [
        "# QQQ FAR CALL listed-contract EOD-side replay",
        "",
        "**Status:** research diagnostic only; not exchange-confirmed fills and not performance approval.",
        f"**Observed data window:** {START_DATE}–{SOURCE_END_DATE}. Requested through {REQUESTED_END_DATE}; terminal source gap remains.",
        f"**Coverage:** {len(expected)} expected sessions, {chain_day_count} with QQQ chain rows.",
        "",
        "## Paired scenarios (all trade P&L figures are quote-side proxies after listed cost scenarios)",
        "",
        "| Budget | Slip/leg | Commission/contract/side | Opens | Closes | Closed-trade P&L sum | Avg closed-trade P&L | Open/unresolved end | Missing position marks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in scenarios:
        avg_pnl = "—" if s["mean_closed_trade_net_pnl_usd"] is None else ("$%.2f" % s["mean_closed_trade_net_pnl_usd"])
        lines.append("| %s | $%.3f | $%.2f | %d | %d | $%.2f | %s | %d | %d |" % (
            s["scenario"], s["slippage_per_leg_usd"], s["commission_per_contract_per_side_usd"],
            s["opened_spreads"], s["closed_spreads"], s["closed_trade_net_pnl_sum_usd"], avg_pnl,
            s["unresolved_or_open_position_at_end"], s["missing_position_mark_sessions"]))
    lines += [
        "",
        "## Trade-level attribution (closed spreads only)",
        "",
        f"Cash-flow reconciliation: {attribution_summary['reconciliation_pass_rows']} PASS, {attribution_summary['reconciliation_fail_rows']} FAIL, {attribution_summary['reconciliation_blocked_rows']} BLOCKED rows. Every trade decomposes into gross entry credit − entry costs − gross exit debit − exit costs; a mismatch over $0.01 is a hard diagnostic failure.",
        "",
        "The attributed trades CSV includes entry/exit leg quotes, leg spread/midpoint, Delta drift, raw nominal spot, VIX regime, 20-session raw-spot momentum regime, holding days and loss as a percentage of the recorded scenario max-loss budget. These are descriptive strata, not changes to strategy rules or proof of fills.",
        "",
        "| Scenario | Net P&L | Entry gross credit | Entry costs | Exit gross debit | Exit costs | Reconciliation failures | Mean short Delta drift | Mean loss / max-loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        *["| %s | $%.2f | $%.2f | $%.2f | $%.2f | $%.2f | %d | %s | %s |" % (
            scenario_id,
            metrics.get("net_pnl_usd") or 0.0,
            metrics.get("entry_gross_credit_cash_usd") or 0.0,
            metrics.get("entry_execution_costs_usd") or 0.0,
            metrics.get("exit_gross_debit_cash_usd") or 0.0,
            metrics.get("exit_execution_costs_usd") or 0.0,
            metrics.get("reconciliation_failures") or 0,
            ("%.4f" % metrics["mean_short_delta_drift"]) if metrics.get("mean_short_delta_drift") is not None else "—",
            ("%.2f%%" % metrics["mean_loss_as_pct_entry_max_loss"]) if metrics.get("mean_loss_as_pct_entry_max_loss") is not None else "—")
          for scenario_id, metrics in attribution_summary["scenarios"].items()],
        "",
        "Group attribution CSV contains all scenarios. The Actions summary below renders the pre-selected base and adverse-cost scenario strata for visibility even if artifact storage is unavailable.",
        "",
    ]
    attribution_display_scenarios = (
        "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00",
        "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.65",
    )
    attribution_dimensions = ("exit_reason", "entry_regime", "exit_regime",
                              "entry_trend_regime", "exit_trend_regime",
                              "entry_quote_quality_bucket", "entry_year")
    for scenario_id in attribution_display_scenarios:
        scenario_attribution = attribution_summary["scenarios"].get(scenario_id)
        if scenario_attribution is None:
            continue
        lines += [
            "",
            f"### Attribution strata: `{scenario_id}`",
            "",
            "| Dimension | Bucket | Trades | Net P&L | Mean P&L | Win fraction | Mean loss / max-loss | Mean short Delta drift | Reconciliation fails |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for dimension in attribution_dimensions:
            for bucket, metrics in scenario_attribution["groups"].get(dimension, {}).items():
                mean_pnl = "—" if metrics.get("mean_net_pnl_usd") is None else ("$%.2f" % metrics["mean_net_pnl_usd"])
                win_fraction = "—" if metrics.get("win_fraction") is None else ("%.1f%%" % (metrics["win_fraction"] * 100))
                loss_usage = "—" if metrics.get("mean_loss_as_pct_entry_max_loss") is None else ("%.2f%%" % metrics["mean_loss_as_pct_entry_max_loss"])
                short_drift = "—" if metrics.get("mean_short_delta_drift") is None else ("%.4f" % metrics["mean_short_delta_drift"])
                lines.append("| %s | %s | %d | $%.2f | %s | %s | %s | %s | %d |" % (
                    dimension, bucket, metrics["trade_count"], metrics["net_pnl_usd"],
                    mean_pnl, win_fraction, loss_usage, short_drift,
                    metrics["reconciliation_failures"]))
    lines += [
        "",
        "Subgroup P&L is closed-trade-only. The base and adverse-cost scenario are independent reruns and must not be added together. Regime/quote-spread bins are descriptive diagnostics, not entry/exit filters; EOD snapshots remain unverified execution proxies.",
        "",
        "## Mark diagnostics",
        "",
        "The zero/near-zero markability pattern from the initial run is explicitly surfaced below; use the new run to verify it is resolved rather than infer from workflow success alone.",
        "",
        "`mark_status_counts`: " + json.dumps(replay_states[0].mark_status_counts, sort_keys=True),
        "",
        "`first_mark_failure_samples`: " + json.dumps(replay_states[0].mark_failure_samples, sort_keys=True),
        "",
        "`first_open_event`: " + json.dumps(next((e for e in replay_states[0].events if e.get("event") == "OPEN"), None), sort_keys=True),
        "",
        "## Hard limitations",
        "",
        "- Contract IDs and expiry are selected from the signal-day chain and pinned; next session may reprice only the same exact IDs. A changed candidate set does not substitute a new contract.",
        "- No same-close entry/exit: signals are carried forward to a later quote session.",
        "- Stale/mixed quote dates are rejected; no quote forward-fill. Exact contract identity, root, same expiry, bid/ask and displayed sizes must be present.",
        "- Non-standard/unparseable roots, crossed/invalid quotes and non-positive net credits block new positions.",
        "- The 0.8% max-loss sizing scenario reproduces the inspected source-model budget setting; 1.2% NAV credit budget is a separate legacy-interpretation scenario, not assumed equivalent.",
        "- Commissions ($0.00 / $0.65 per contract per side) and per-leg slippage are explicit scenarios, not verified broker fees or measured executions.",
        "- No CAGR, daily MTM MaxDD, Sharpe or ES95 is claimed: source rows stop 2025-12-15, internal dates are missing, and EOD snapshots do not prove fills.",
        "- VXX option history is not supplied here. This result covers only a QQQ-core plus QQQ far-call overlay research sleeve; it is not a full QQQ/VXX Hybrid strategy result.",
        "",
        "## Reproducibility",
        "",
        "All annual QQQ Parquet files and the underlying/universe/model/helper source pins must pass existing Git blob SHA/byte checks before this replay runs.",
        "",
    ]
    (out_dir / "qqq_far_call_replay_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"research_id": report["research_id"], "status": report["status"],
                      "coverage": report["coverage"] | {"source_integrity": "HASH_VERIFIED"},
                      "mark_diagnostics": {"baseline_mark_status_counts": dict(replay_states[0].mark_status_counts),
                                           "baseline_first_mark_failures": replay_states[0].mark_failure_samples,
                                           "baseline_first_open_event": next((e for e in replay_states[0].events if e.get("event") == "OPEN"), None)},
                      "trade_attribution": {"closed_trade_rows": attribution_summary["closed_trade_rows"],
                                           "reconciliation_pass_rows": attribution_summary["reconciliation_pass_rows"],
                                           "reconciliation_fail_rows": attribution_summary["reconciliation_fail_rows"],
                                           "reconciliation_blocked_rows": attribution_summary["reconciliation_blocked_rows"]},
                      "scenarios": [{k: s[k] for k in ("scenario","slippage_per_leg_usd",
                                    "commission_per_contract_per_side_usd","opened_spreads","closed_spreads",
                                    "closed_trade_net_pnl_sum_usd","mean_closed_trade_net_pnl_usd",
                                    "unresolved_or_open_position_at_end","missing_position_mark_sessions",
                                    "mark_status_counts","mark_failure_samples","exit_quote_size_missing_sessions",
                                    "performance_gate")} for s in scenarios],
                      "output_dir": str(out_dir)}, indent=2))
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/qqq_far_call_replay")
    args = parser.parse_args()
    run_replay(args.out)


if __name__ == "__main__":
    main()
