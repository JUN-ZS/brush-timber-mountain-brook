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
OPTION_COLUMNS = ["contract_id", "symbol", "expiration", "strike", "type",
                  "bid", "ask", "bid_size", "ask_size", "volume", "open_interest",
                  "date", "implied_volatility", "delta"]
EVIDENCE = "OBSERVED_EOD_QUOTES / DERIVED_SIDE_PRICE_REPLAY; NOT_CONFIRMED_FILLS"


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
    match = re.fullmatch(r"([A-Z]{1,6})(\d{6})[CP](\d{8})", ident)
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


def close_side_debit_per_share(position, rows_by_id, slippage, commission):
    short = rows_by_id.get(position["short_id"])
    wing = rows_by_id.get(position["wing_id"])
    if short is None or wing is None:
        return None, "CONTRACT_ROW_MISSING"
    if not valid_quote(short, require_size=True) or not valid_quote(wing, require_size=True):
        return None, "INVALID_OR_UNSIZED_EXIT_QUOTE"
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
        self.pending_close = False
        self.events = []
        self.trades = []
        self.daily = []
        self.counters = Counter()
        self.missing_position_mark_dates = []
        self.last_valid_nav = None
        self.unresolved_positions = []

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

    def process(self, day_key, rows, spot_info, vix_value, selected_pair=None):
        chain_present = bool(rows)
        self.counters["expected_sessions"] += 1
        if chain_present:
            self.counters["chain_sessions"] += 1
        else:
            self.counters["missing_chain_sessions"] += 1
        raw_spot = n((spot_info or {}).get("raw_close"))
        core_value = self._core_value(spot_info)
        qmap = quote_map(rows)
        selected_pair = selected_pair if selected_pair is not None else (choose_vertical(rows, day_key) if chain_present else {"status": "NO_CHAIN"})
        if selected_pair.get("status") == "PAIR_SELECTED":
            self.counters["candidate_pair_sessions"] += 1
        else:
            self.counters["no_valid_pair_sessions"] += 1

        executed_close_today = False
        if self.position is not None and self.pending_close and chain_present:
            debit, status = close_side_debit_per_share(self.position, qmap, self.slippage, self.commission)
            exp = date.fromisoformat(self.position["expiry"])
            if debit is not None and date.fromisoformat(day_key) < exp:
                p = self.position
                realized = (p["entry_net_credit_ps"] - debit) * 100 * p["quantity"]
                self.cash -= debit * 100 * p["quantity"]
                trade = {
                    **p, "exit_date": day_key, "exit_reason": p.get("exit_reason", "RULE_EXIT"),
                    "exit_short_ask": n(qmap[p["short_id"]].get("ask")),
                    "exit_wing_bid": n(qmap[p["wing_id"]].get("bid")),
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
            elif date.fromisoformat(day_key) >= exp:
                self.counters["expired_unresolved"] += 1
                self.unresolved_positions.append({"date": day_key, "reason": "NO_VALID_EXIT_QUOTE_BEFORE_EXPIRY",
                                                  "short_id": self.position["short_id"], "wing_id": self.position["wing_id"]})
            else:
                self.counters["exit_delayed_missing_quote"] += 1
                self.events.append({"date": day_key, "event": "CLOSE_DEFERRED", "status": status,
                                    "reason": self.position.get("exit_reason"), "budget_mode": self.mode["name"]})

        just_opened = False
        if self.position is None and self.pending_open and chain_present:
            self.pending_open = False
            if raw_spot is None or core_value is None:
                self.counters["entry_blocked_missing_spot"] += 1
                self.events.append({"date": day_key, "event": "ENTRY_BLOCKED", "reason": "RAW_OR_ADJUSTED_SPOT_MISSING"})
            elif selected_pair.get("status") != "PAIR_SELECTED":
                self.counters["entry_no_valid_pair"] += 1
                self.events.append({"date": day_key, "event": "ENTRY_SKIPPED", "reason": selected_pair.get("status")})
            else:
                pair = selected_pair
                net_credit = entry_net_credit_per_share(pair, self.slippage, self.commission)
                nav_for_sizing = core_value + self.cash
                quantity, max_loss = pick_quantity(nav_for_sizing, pair, self.mode, net_credit,
                                                   self.slippage, self.commission)
                if net_credit <= 0:
                    self.counters["entry_nonpositive_credit"] += 1
                    self.events.append({"date": day_key, "event": "ENTRY_BLOCKED", "reason": "NONPOSITIVE_NET_CREDIT_AFTER_COSTS"})
                elif quantity < 1:
                    self.counters["entry_quantity_zero"] += 1
                    self.events.append({"date": day_key, "event": "ENTRY_SKIPPED", "reason": "BUDGET_BELOW_ONE_SPREAD",
                                        "nav_for_sizing": round(nav_for_sizing, 2)})
                else:
                    self.cash += net_credit * 100 * quantity
                    self.position = {
                        "budget_mode": self.mode["name"], "slippage_per_leg": self.slippage,
                        "commission_per_contract_per_side": self.commission,
                        "signal_date": self._signal_date, "entry_date": day_key,
                        "entry_short_bid": pair["short"]["bid"], "entry_wing_ask": pair["wing"]["ask"],
                        "entry_gross_credit_per_share": pair["gross_observed_side_credit_per_share"],
                        "entry_net_credit_ps": net_credit, "entry_cash_credit": net_credit*100*quantity,
                        "short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"],
                        "expiry": pair["expiry"], "short_strike": pair["short"]["strike"],
                        "wing_strike": pair["wing"]["strike"], "short_delta": pair["short"]["delta"],
                        "wing_delta": pair["wing"]["delta"], "width": pair["width"],
                        "entry_dte": pair["dte"], "quantity": quantity,
                        "max_loss_per_spread_scenario": max_loss,
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
                                        "source_status": EVIDENCE})
                    just_opened = True

        # Mark existing positions only from the current exact contract rows; never forward-fill.
        nav, mark_status = self._nav(core_value, self.position, qmap, day_key)
        if nav is None:
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
            self._signal_date = day_key
        elif self.position is None and not chain_present:
            self.pending_open = False

        marked = nav is not None
        self.daily.append({
            "date": day_key, "raw_spot": raw_spot, "adjusted_close_for_core_tr": n((spot_info or {}).get("adjusted_close")),
            "vix": n(vix_value), "regime": regime(vix_value), "chain_present": chain_present,
            "nav_eod_marked": round(nav, 6) if nav is not None else None,
            "nav_mark_status": mark_status, "position_open": self.position is not None,
            "pending_close": self.pending_close, "pending_open": self.pending_open,
            "source_status": EVIDENCE,
        })


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
        for state in replay_states:
            state.process(session_day, rows, spot, vix, pair)

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
            "missing_position_mark_sessions": state.counters["missing_position_mark_sessions"],
            "unmarked_nav_sessions": state.counters["unmarked_nav_sessions"],
            "closed_trade_net_pnl_sum_usd": round(sum(pnls), 2) if pnls else 0.0,
            "mean_closed_trade_net_pnl_usd": round(sum(pnls)/len(pnls), 2) if pnls else None,
            "median_closed_trade_net_pnl_usd": sorted(pnls)[len(pnls)//2] if pnls else None,
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
        all_trades.extend([{**t, "scenario": name, "slippage_per_leg_usd": state.slippage,
                            "commission_per_contract_per_side_usd": state.commission}
                           for t in closed])
        all_events.extend([{**e, "scenario": name, "slippage_per_leg_usd": state.slippage,
                            "commission_per_contract_per_side_usd": state.commission}
                           for e in state.events])

    report = {
        "research_id": "QQQ_FAR_CALL_LISTED_CONTRACT_EOD_REPLAY_V1",
        "status": "RESEARCH_DIAGNOSTIC_NOT_PERFORMANCE_APPROVED",
        "strategy_policy_changed": False, "main_changed": False, "broker_orders_enabled": False,
        "not_opra_fills": True, "not_virgin_oos": True,
        "price_basis": {"qqq_options": "raw nominal QQQ close and actual listed strikes",
                        "qqq_core_accounting": "adjusted-close total-return proxy; kept separate"},
        "contract_selection": {"expiry": "closest eligible 20-40 DTE expiry to 30 DTE",
                               "short_call_delta_target": SHORT_DELTA_TARGET,
                               "long_wing_delta_target": WING_DELTA_TARGET,
                               "source_delta_used": True, "listed_strikes_only": True,
                               "require_occ_root_QQQ": True, "require_positive_bid_ask_and_size": True},
        "rules": {"source_max_loss_budget_pct_nav": 0.008, "alternate_legacy_credit_budget_pct_nav": 0.012,
                  "close_signal": f"DTE <= {STOP_DTE} or P&L/max-loss <= {STOP_LOSS_OVER_MAXLOSS} or >= {TAKE_PROFIT_OVER_MAXLOSS}",
                  "entry_exit_timing": "signal at close t; entry/exit proxy uses next observed eligible session quote; never same-close signal/fill",
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
        "interpretation": "Only closed-spread event P&L is summarized. It is a quote-side proxy under explicit hypothetical costs, not confirmed fills. CAGR, daily MTM MaxDD, Sharpe, ES95 are intentionally NULL because the observation path is incomplete and EOD snapshots do not prove fills.",
    }
    (out_dir / "qqq_far_call_replay_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (out_dir / "qqq_far_call_replay_trades.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({k for x in all_trades for k in x})
        if not fields: fields = ["scenario", "status"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(all_trades)
    with (out_dir / "qqq_far_call_replay_events.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({k for x in all_events for k in x})
        if not fields: fields = ["scenario", "event"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(all_events)

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
        "## Hard limitations",
        "",
        "- No same-close entry/exit: signals are carried forward to a later quote session.",
        "- No quote forward-fill. Exact contract identity, root, same expiry, bid/ask and displayed sizes must be present.",
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
                      "scenarios": [{k: s[k] for k in ("scenario","slippage_per_leg_usd",
                                    "commission_per_contract_per_side_usd","opened_spreads","closed_spreads",
                                    "closed_trade_net_pnl_sum_usd","mean_closed_trade_net_pnl_usd",
                                    "unresolved_or_open_position_at_end","missing_position_mark_sessions",
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
