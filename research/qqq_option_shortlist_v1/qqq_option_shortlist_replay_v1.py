#!/usr/bin/env python3
"""Research-only, event-matched QQQ option-structure shortlist replay.

Signals are fixed from QQQ/VIX histories before the entry session. Contract selection
uses a SHA-pinned historical EOD option-chain source; positions use exact listed IDs,
side-correct quotes, displayed-size constraints, and no forward-filled marks. Outputs
are quote-side estimates, not confirmed fills or broker-margin approval.
"""
from __future__ import annotations
import argparse, csv, json, math, re, sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "research" / "qqq_hybrid_operator_terminal_v1"
sys.path.insert(0, str(SOURCE_DIR))
import full_history_qqq_quote_audit as audit
import qqq_far_call_quote_replay as source_replay

START_DATE = "2018-03-01"
SOURCE_END_DATE = "2025-12-15"
NAV_USD = 80_000.0
RISK_BUDGETS = (0.005, 0.01, 0.02)
MULTIPLIER = 100
HOLD_SESSIONS = 10
MAX_EXIT_DEFER_SESSIONS = 3
BASE_SLIPPAGE_PER_SHARE = 0.05
BASE_COMMISSION_PER_CONTRACT_SIDE = 0.65
SIGNAL_DRAWDOWN_FROM_MA20 = -0.021
SIGNAL_COOLDOWN_SESSIONS = HOLD_SESSIONS + MAX_EXIT_DEFER_SESSIONS + 2
DTE_MIN, DTE_MAX, DTE_TARGET = 30, 60, 45


def num(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def day(value: Any) -> str:
    if value is None:
        return ""
    return value.isoformat()[:10] if hasattr(value, "isoformat") else str(value)[:10]


def cid(value: Any) -> str:
    ident = re.sub(r"\s+", "", str(value or "").strip().upper())
    return ident[2:] if ident.startswith("O:") else ident


def option_type(row: dict[str, Any]) -> str:
    value = str(row.get("type", "")).strip().upper()
    if value in {"C", "CALL"}:
        return "C"
    if value in {"P", "PUT"}:
        return "P"
    return ""


def standard_identity(row: dict[str, Any], right: str, session_day: str) -> bool:
    ident = cid(row.get("contract_id"))
    m = re.fullmatch(r"QQQ(\d{6})([CP])(\d{8})", ident)
    if not m or str(row.get("symbol", "")).upper() != "QQQ" or m.group(2) != right:
        return False
    try:
        expiry = datetime.strptime(m.group(1), "%y%m%d").date().isoformat()
    except ValueError:
        return False
    strike = num(row.get("strike"))
    if day(row.get("expiration")) != expiry or strike is None or strike <= 0:
        return False
    if abs(strike - int(m.group(3)) / 1000.0) >= 0.00051:
        return False
    try:
        dte = (date.fromisoformat(expiry) - date.fromisoformat(session_day)).days
    except ValueError:
        return False
    return DTE_MIN <= dte <= DTE_MAX and audit.base.standard_strike_grid(strike)


def valid_quote(row: dict[str, Any] | None) -> bool:
    if not isinstance(row, dict):
        return False
    bid, ask = num(row.get("bid")), num(row.get("ask"))
    bs, ass = num(row.get("bid_size")), num(row.get("ask_size"))
    return (bid is not None and ask is not None and bid > 0 and ask >= bid
            and bs is not None and ass is not None and bs > 0 and ass > 0)


def chain_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {cid(r.get("contract_id")): r for r in rows if cid(r.get("contract_id"))}


def build_signals(days: list[str], spots: dict[str, dict[str, Any]], universe: dict[str, dict[str, Any]]) -> list[str]:
    """Preregistered reversal hypothesis; next-session entry prevents same-close execution."""
    closes = [num((spots.get(d) or {}).get("raw_close")) for d in days]
    vix = [num((universe.get(d) or {}).get("vix")) for d in days]
    out: list[str] = []
    last_signal_idx = -10_000
    for i, d in enumerate(days):
        if i < 25 or i - last_signal_idx < SIGNAL_COOLDOWN_SESSIONS:
            continue
        if any(closes[j] is None for j in range(i-20, i+1)) or any(vix[j] is None for j in (i, i-5)):
            continue
        ma20 = sum(float(closes[j]) for j in range(i-19, i+1)) / 20.0
        dist_now = float(closes[i]) / ma20 - 1.0
        prev_ma20 = sum(float(closes[j]) for j in range(i-20, i)) / 20.0
        dist_prev = float(closes[i-1]) / prev_ma20 - 1.0
        positive_day = float(closes[i]) > float(closes[i-1])
        vix_falling = float(vix[i]) < float(vix[i-5])
        if dist_now <= SIGNAL_DRAWDOWN_FROM_MA20 and dist_prev <= SIGNAL_DRAWDOWN_FROM_MA20 and positive_day and vix_falling:
            out.append(d)
            last_signal_idx = i
    return out


def _contract_candidates(rows: list[dict[str, Any]], session_day: str, right: str, spot: float) -> list[dict[str, Any]]:
    items = []
    for r in rows:
        if option_type(r) != right or not standard_identity(r, right, session_day) or not valid_quote(r):
            continue
        strike, delta = num(r.get("strike")), num(r.get("delta"))
        if strike is None or delta is None or not 0 < abs(delta) < 1:
            continue
        expiry = day(r.get("expiration"))
        dte = (date.fromisoformat(expiry) - date.fromisoformat(session_day)).days
        items.append({"row": r, "id": cid(r.get("contract_id")), "expiry": expiry,
                      "dte": dte, "strike": strike, "abs_delta": abs(delta),
                      "delta": delta, "bid_size": int(num(r.get("bid_size")) or 0),
                      "ask_size": int(num(r.get("ask_size")) or 0), "spot": spot})
    return items


def leg(item: dict[str, Any], right: str, side: str, qty: int) -> dict[str, Any]:
    return {"id": item["id"], "expiry": item["expiry"], "strike": item["strike"],
            "right": right, "side": side, "qty": int(qty), "signal_delta": item["delta"]}


def choose_call_vertical(rows: list[dict[str, Any]], session_day: str, spot: float) -> dict[str, Any] | None:
    calls = _contract_candidates(rows, session_day, "C", spot)
    longs = [x for x in calls if 0.40 <= x["abs_delta"] <= 0.60 and x["strike"] < spot]
    shorts = [x for x in calls if 0.05 <= x["abs_delta"] <= 0.15 and x["strike"] > spot]
    pairs = []
    for long in longs:
        for short in shorts:
            if long["expiry"] != short["expiry"] or long["strike"] >= short["strike"]:
                continue
            debit = num(long["row"].get("ask")) - num(short["row"].get("bid"))
            width = short["strike"] - long["strike"]
            if debit is None or debit <= 0 or debit >= width:
                continue
            err = abs(long["abs_delta"] - 0.50) + abs(short["abs_delta"] - 0.10)
            liq = min(long["bid_size"], long["ask_size"], short["bid_size"], short["ask_size"])
            pairs.append((abs(long["dte"] - DTE_TARGET), err, -liq, long, short, debit, width))
    if not pairs:
        return None
    _, _, _, long, short, debit, width = min(pairs, key=lambda z: (z[0], z[1], z[2], z[3]["expiry"], z[3]["strike"]))
    return {"expiry": long["expiry"], "dte_signal": long["dte"], "width": width,
            "legs": [leg(long, "C", "buy", 1), leg(short, "C", "sell", 1)],
            "selection": "same-expiry QQQ standard call; long absDelta nearest .50; short absDelta nearest .10; target 45DTE"}


def choose_long_put(rows: list[dict[str, Any]], session_day: str, spot: float, expiry: str) -> dict[str, Any] | None:
    puts = [x for x in _contract_candidates(rows, session_day, "P", spot)
            if x["expiry"] == expiry and 0.05 <= x["abs_delta"] <= 0.15 and x["strike"] < spot]
    if not puts:
        return None
    p = min(puts, key=lambda x: (abs(x["abs_delta"] - 0.10), -min(x["bid_size"], x["ask_size"]), x["strike"]))
    return leg(p, "P", "buy", 1)


def choose_put_vertical(rows: list[dict[str, Any]], session_day: str, spot: float) -> dict[str, Any] | None:
    puts = _contract_candidates(rows, session_day, "P", spot)
    longs = [x for x in puts if 0.20 <= x["abs_delta"] <= 0.40 and x["strike"] < spot]
    shorts = [x for x in puts if 0.04 <= x["abs_delta"] <= 0.16 and x["strike"] < spot]
    pairs = []
    for long in longs:
        for short in shorts:
            if long["expiry"] != short["expiry"] or long["strike"] <= short["strike"]:
                continue
            err = abs(long["abs_delta"] - 0.30) + abs(short["abs_delta"] - 0.10)
            liq = min(long["bid_size"], long["ask_size"], short["bid_size"], short["ask_size"])
            pairs.append((abs(long["dte"] - DTE_TARGET), err, -liq, long, short))
    if not pairs:
        return None
    _, _, _, long, short = min(pairs, key=lambda z: (z[0], z[1], z[2], z[3]["expiry"], z[3]["strike"]))
    return {"expiry": long["expiry"], "dte_signal": long["dte"],
            "long": leg(long, "P", "buy", 1), "short": leg(short, "P", "sell", 1),
            "selection": "same-expiry standard QQQ puts; long absDelta nearest .30; short absDelta nearest .10; target 45DTE"}


def build_candidates(rows: list[dict[str, Any]], signal_day: str, spot: float) -> tuple[dict[str, Any], dict[str, str]]:
    result: dict[str, Any] = {}
    status: dict[str, str] = {}
    calls = choose_call_vertical(rows, signal_day, spot)
    if calls is None:
        status["CALL_DEBIT_50D_10D"] = "NO_VALID_STANDARD_POSITIVE_DEBIT_CALL_VERTICAL"
        status["CALL_DEBIT_PLUS_LONG_PUT_10D"] = "BLOCKED_DEPENDENCY_CALL_VERTICAL_MISSING"
    else:
        result["CALL_DEBIT_50D_10D"] = {"legs": calls["legs"], "expiry": calls["expiry"], "dte_signal": calls["dte_signal"]}
        status["CALL_DEBIT_50D_10D"] = "SELECTED"
        long_put = choose_long_put(rows, signal_day, spot, calls["expiry"])
        if long_put is None:
            status["CALL_DEBIT_PLUS_LONG_PUT_10D"] = "NO_VALID_SAME_EXPIRY_10D_LONG_PUT"
        else:
            result["CALL_DEBIT_PLUS_LONG_PUT_10D"] = {"legs": calls["legs"] + [long_put], "expiry": calls["expiry"], "dte_signal": calls["dte_signal"]}
            status["CALL_DEBIT_PLUS_LONG_PUT_10D"] = "SELECTED"
    puts = choose_put_vertical(rows, signal_day, spot)
    if puts is None:
        for n in range(1, 7):
            status[f"PUT_SHORT_HEAVY_1x{n}"] = "NO_VALID_STANDARD_PUT_VERTICAL"
            status[f"PUT_LONG_HEAVY_{n}x1"] = "NO_VALID_STANDARD_PUT_VERTICAL"
    else:
        for n in range(1, 7):
            result[f"PUT_SHORT_HEAVY_1x{n}"] = {"legs": [dict(puts["long"], qty=1), dict(puts["short"], qty=n)], "expiry": puts["expiry"], "dte_signal": puts["dte_signal"]}
            result[f"PUT_LONG_HEAVY_{n}x1"] = {"legs": [dict(puts["long"], qty=n), dict(puts["short"], qty=1)], "expiry": puts["expiry"], "dte_signal": puts["dte_signal"]}
            status[f"PUT_SHORT_HEAVY_1x{n}"] = "SELECTED"
            status[f"PUT_LONG_HEAVY_{n}x1"] = "SELECTED"
    return result, status


def cashflow(legs: list[dict[str, Any]], qmap: dict[str, dict[str, Any]], opening: bool,
             slip: float, commission: float) -> tuple[float | None, int, str]:
    """Opening/closing cash flows with buy-at-Ask, sell-at-Bid and visible-depth constraints."""
    total = 0.0
    contracts = 0
    for x in legs:
        row = qmap.get(x["id"])
        if row is None or not valid_quote(row):
            return None, contracts, "MISSING_OR_INVALID_TWO_SIDED_QUOTE"
        action = x["side"] if opening else ("sell" if x["side"] == "buy" else "buy")
        px = num(row.get("ask" if action == "buy" else "bid"))
        size = num(row.get("ask_size" if action == "buy" else "bid_size"))
        if px is None or px <= 0 or size is None or size < x["qty"]:
            return None, contracts, f"INSUFFICIENT_{action.upper()}_SIDE_SIZE_OR_PRICE"
        effective_px = px + slip if action == "buy" else px - slip
        sign = -1 if action == "buy" else 1
        total += sign * effective_px * MULTIPLIER * x["qty"]
        contracts += x["qty"]
    total -= contracts * commission
    return total, contracts, "OK"


def intrinsic(right: str, strike: float, spot: float) -> float:
    return max(spot - strike, 0.0) if right == "C" else max(strike - spot, 0.0)


def terminal_risk(legs: list[dict[str, Any]], entry_cf: float) -> dict[str, Any]:
    knots = sorted({0.0, *[float(x["strike"]) for x in legs], max(float(x["strike"]) for x in legs) * 2.0 + 1.0})
    values = []
    for s in knots:
        payoff = 0.0
        for x in legs:
            sign = 1.0 if x["side"] == "buy" else -1.0
            payoff += sign * intrinsic(x["right"], float(x["strike"]), s) * MULTIPLIER * int(x["qty"])
        values.append((s, entry_cf + payoff))
    worst_spot, worst_pnl = min(values, key=lambda z: z[1])
    return {"terminal_worst_loss_usd": round(max(0.0, -worst_pnl), 2),
            "terminal_worst_spot_knot": worst_spot,
            "terminal_pnl_at_zero_usd": round(dict(values).get(0.0, 0.0), 2),
            "terminal_pnl_knots": [{"spot": s, "pnl_usd": round(p, 2)} for s, p in values]}


def summarise(trades: list[dict[str, Any]], signal_counts: dict[str, Any]) -> dict[str, Any]:
    strategies = sorted({str(x["strategy_id"]) for x in trades})
    out = {}
    for strategy in strategies:
        all_rows = [x for x in trades if x["strategy_id"] == strategy]
        resolved = [x for x in all_rows if x.get("status") == "RESOLVED" and num(x.get("net_pnl_usd")) is not None]
        pnls = [float(x["net_pnl_usd"]) for x in resolved]
        wins = sum(p > 0 for p in pnls)
        gross_wins = sum(p for p in pnls if p > 0)
        gross_losses = -sum(p for p in pnls if p < 0)
        risk_returns = [float(x["net_pnl_usd"]) / float(x["terminal_worst_loss_usd"]) for x in resolved if num(x.get("terminal_worst_loss_usd")) and float(x["terminal_worst_loss_usd"]) > 0]
        out[strategy] = {
            "opened_episodes": len(all_rows), "resolved": len(resolved), "unresolved": sum(x.get("status") != "RESOLVED" for x in all_rows),
            "win_rate_pct": round(100*wins/len(pnls), 4) if pnls else None,
            "total_one_unit_net_pnl_usd": round(sum(pnls), 2) if pnls else None,
            "mean_one_unit_net_pnl_usd": round(sum(pnls)/len(pnls), 2) if pnls else None,
            "median_one_unit_net_pnl_usd": round(median(pnls), 2) if pnls else None,
            "worst_one_unit_net_pnl_usd": round(min(pnls), 2) if pnls else None,
            "best_one_unit_net_pnl_usd": round(max(pnls), 2) if pnls else None,
            "profit_factor": round(gross_wins/gross_losses, 5) if gross_losses else (None if not gross_wins else "INF_NO_LOSSES_IN_SAMPLE"),
            "median_net_pnl_over_entry_terminal_worst_loss": round(median(risk_returns), 5) if risk_returns else None,
            "tail_budget_1pct_nav_sizeable_episode_count": sum(int(x.get("units_at_1pct_nav_tail_budget") or 0) > 0 for x in all_rows),
        }
    return {"signal_summary": signal_counts, "strategy_summary": out}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("status\nNO_ROWS\n", encoding="utf-8")
        return
    keys = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def run(out_dir: Path) -> dict[str, Any]:
    cache = ROOT / ".cache" / "qqq-options-full-history"
    integrity, universe_by_day, spots, expected = audit.build_inputs(cache)
    expected = sorted(d for d in expected if START_DATE <= d <= SOURCE_END_DATE)
    if not expected:
        raise RuntimeError("No source-aligned QQQ/VIX sessions")
    signal_days = build_signals(expected, spots, universe_by_day)
    signal_set = set(signal_days)
    option_paths, file_integrity = [], {}
    for spec in audit.ANNUAL_FILES:
        path, meta = audit.download_verified(spec, cache)
        option_paths.append(path)
        file_integrity[spec["name"]] = meta

    chain_iter = iter(source_replay.iter_qqq_chain_days(option_paths))
    next_chain = next(chain_iter, None)
    pending = None
    active: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    core_rows: list[dict[str, Any]] = []
    selected_signals: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    selected_signal_count = 0
    for idx, session_day in enumerate(expected):
        while next_chain is not None and next_chain[0] < session_day:
            next_chain = next(chain_iter, None)
        if next_chain is not None and next_chain[0] == session_day:
            rows = next_chain[1]
            next_chain = next(chain_iter, None)
        else:
            rows = []
        qmap = chain_map(rows)
        spot_today = num((spots.get(session_day) or {}).get("raw_close"))

        # Entry is on the next observed QQQ/VIX session after the signal; preserve exact IDs.
        if pending is not None and idx == pending["entry_idx"]:
            for strategy_id, spec in pending["candidates"].items():
                entry_cf, contracts, reason = cashflow(spec["legs"], qmap, True, BASE_SLIPPAGE_PER_SHARE, BASE_COMMISSION_PER_CONTRACT_SIDE)
                if entry_cf is None:
                    status_counts[f"ENTRY_BLOCKED:{reason}"] += 1
                    continue
                risk = terminal_risk(spec["legs"], entry_cf)
                depth_units = min(int(num(qmap[x["id"]].get("ask_size" if x["side"] == "buy" else "bid_size")) or 0) // int(x["qty"]) for x in spec["legs"])
                risk_units = {str(int(b*1000)): (math.floor(NAV_USD*b / risk["terminal_worst_loss_usd"]) if risk["terminal_worst_loss_usd"] > 0 else depth_units) for b in RISK_BUDGETS}
                active.append({
                    "strategy_id": strategy_id, "signal_date": pending["signal_day"], "entry_date": session_day,
                    "entry_idx": idx, "exit_due_idx": min(idx + HOLD_SESSIONS, len(expected)-1),
                    "legs": spec["legs"], "entry_cashflow_usd": round(entry_cf, 2), "entry_contract_count": contracts,
                    **risk, "depth_units_at_entry": depth_units, "units_at_0p5pct_nav_tail_budget": min(depth_units, risk_units["5"]),
                    "units_at_1pct_nav_tail_budget": min(depth_units, risk_units["10"]),
                    "units_at_2pct_nav_tail_budget": min(depth_units, risk_units["20"]),
                    "entry_spot": spot_today, "exit_defer_count": 0, "mark_count": 0,
                    "mae_one_unit_usd": 0.0, "mfe_one_unit_usd": 0.0,
                })
                status_counts[f"OPENED:{strategy_id}"] += 1
            core_due_idx = min(idx + HOLD_SESSIONS, len(expected)-1)
            core_rows.append({"signal_date": pending["signal_day"], "entry_date": session_day,
                              "entry_spot": spot_today, "scheduled_exit_date": expected[core_due_idx],
                              "entry_idx": idx, "exit_due_idx": core_due_idx, "status": "PENDING"})
            pending = None

        # Exit exact IDs at/after the 10-session horizon. Missing marks are deferred, never filled forward.
        keep = []
        for pos in active:
            mark_cf, _, mark_reason = cashflow(pos["legs"], qmap, False, BASE_SLIPPAGE_PER_SHARE, BASE_COMMISSION_PER_CONTRACT_SIDE)
            if mark_cf is not None:
                pos["mark_count"] += 1
                current_unreal = float(pos["entry_cashflow_usd"]) + mark_cf
                pos["mae_one_unit_usd"] = min(float(pos["mae_one_unit_usd"]), current_unreal)
                pos["mfe_one_unit_usd"] = max(float(pos["mfe_one_unit_usd"]), current_unreal)
            if idx < pos["exit_due_idx"]:
                keep.append(pos)
                continue
            if mark_cf is not None:
                pnl = float(pos["entry_cashflow_usd"]) + mark_cf
                rows_out = {k: pos.get(k) for k in ("strategy_id", "signal_date", "entry_date", "entry_spot", "entry_cashflow_usd", "entry_contract_count", "terminal_worst_loss_usd", "terminal_worst_spot_knot", "terminal_pnl_at_zero_usd", "depth_units_at_entry", "units_at_0p5pct_nav_tail_budget", "units_at_1pct_nav_tail_budget", "units_at_2pct_nav_tail_budget", "mae_one_unit_usd", "mfe_one_unit_usd", "mark_count")}
                rows_out.update({"status":"RESOLVED", "exit_date":session_day, "exit_session_age":idx-pos["entry_idx"], "exit_delay_sessions":idx-pos["exit_due_idx"], "net_pnl_usd":round(pnl,2), "net_pnl_pct_entry_terminal_worst_loss":round(100*pnl/float(pos["terminal_worst_loss_usd"]),4) if float(pos["terminal_worst_loss_usd"])>0 else None, "contract_legs":pos["legs"]})
                trades.append(rows_out)
                status_counts[f"RESOLVED:{pos['strategy_id']}"] += 1
            elif idx >= pos["exit_due_idx"] + MAX_EXIT_DEFER_SESSIONS:
                rows_out = {k: pos.get(k) for k in ("strategy_id", "signal_date", "entry_date", "entry_spot", "entry_cashflow_usd", "entry_contract_count", "terminal_worst_loss_usd", "terminal_worst_spot_knot", "terminal_pnl_at_zero_usd", "depth_units_at_entry", "units_at_0p5pct_nav_tail_budget", "units_at_1pct_nav_tail_budget", "units_at_2pct_nav_tail_budget", "mae_one_unit_usd", "mfe_one_unit_usd", "mark_count")}
                rows_out.update({"status":"UNRESOLVED_EXIT_QUOTE", "scheduled_exit_date":expected[pos["exit_due_idx"]], "last_checked_date":session_day, "reason":mark_reason, "contract_legs":pos["legs"]})
                trades.append(rows_out)
                status_counts[f"UNRESOLVED:{pos['strategy_id']}:{mark_reason}"] += 1
            else:
                pos["exit_defer_count"] += 1
                keep.append(pos)
        active = keep

        # Resolve the QQQ price-only control on the same event entry and 10-session clock.
        for core in core_rows:
            if core["status"] != "PENDING" or idx < core["exit_due_idx"]:
                continue
            exit_spot = spot_today
            entry_spot = num(core.get("entry_spot"))
            if entry_spot is None or exit_spot is None or entry_spot <= 0:
                core.update({"status":"UNRESOLVED_PRICE", "exit_date":session_day})
            else:
                pnl_per_1000 = 1000.0 * (exit_spot / entry_spot - 1.0)
                core.update({"status":"RESOLVED", "exit_date":session_day, "exit_spot":exit_spot,
                             "ten_session_return_pct":round(100*(exit_spot/entry_spot-1),4),
                             "pnl_on_1000_usd_notional":round(pnl_per_1000,2)})

        # Signal close t -> select contracts; open exact IDs no earlier than t+1.
        if session_day in signal_set:
            selected_signal_count += 1
            spot_sig = num((spots.get(session_day) or {}).get("raw_close"))
            if spot_sig is None or not rows:
                status_counts["SIGNAL_NO_SPOT_OR_CHAIN"] += 1
                selected_signals.append({"signal_date":session_day,"status":"SIGNAL_NO_SPOT_OR_CHAIN"})
                continue
            specs, statuses = build_candidates(rows, session_day, spot_sig)
            for key, value in statuses.items():
                if value != "SELECTED":
                    status_counts[f"CANDIDATE:{key}:{value}"] += 1
            selected_signals.append({"signal_date":session_day,"spot":spot_sig,"status":"CANDIDATES_BUILT" if specs else "NO_VALID_CANDIDATE",
                                     "candidates":sorted(specs.keys()),"selection_status":statuses})
            if specs and idx + 1 < len(expected):
                pending = {"signal_day":session_day,"entry_idx":idx+1,"candidates":specs}

    for pos in active:
        trades.append({"strategy_id":pos["strategy_id"],"signal_date":pos["signal_date"],"entry_date":pos["entry_date"],
                       "status":"UNRESOLVED_END_OF_SOURCE","terminal_worst_loss_usd":pos["terminal_worst_loss_usd"],"contract_legs":pos["legs"]})
    for core in core_rows:
        if core["status"] == "PENDING":
            core.update({"status":"UNRESOLVED_END_OF_SOURCE"})

    signal_counts = {"signal_rule":"QQQ close <= 2.1% below rolling MA20 on current and prior session; QQQ up day; repository VIX below its level 5 sessions earlier",
                     "signal_count":len(signal_days),"signals_processed":selected_signal_count,
                     "source_window":[START_DATE,SOURCE_END_DATE],"source_sessions":len(expected),
                     "entry_clock":"signal at EOD t; exact selected contract IDs entered no earlier than next observed QQQ/VIX session t+1",
                     "exit_clock":f"first valid exact-ID quote-side close at/after {HOLD_SESSIONS} observed sessions; defer up to {MAX_EXIT_DEFER_SESSIONS} sessions then censor",
                     "base_cost_assumption":{"slippage_usd_per_share_per_leg_side":BASE_SLIPPAGE_PER_SHARE,"commission_usd_per_contract_per_side":BASE_COMMISSION_PER_CONTRACT_SIDE},
                     "nav_sizing_reference_usd":NAV_USD,"signal_cooldown_sessions":SIGNAL_COOLDOWN_SESSIONS,
                     "status_counts":dict(status_counts)}
    result = summarise(trades, signal_counts)
    resolved_core = [x for x in core_rows if x.get("status")=="RESOLVED"]
    core_pnls = [float(x["pnl_on_1000_usd_notional"]) for x in resolved_core]
    result["qqq_core_1000_notional_control"] = {"episodes":len(core_rows),"resolved":len(resolved_core),
      "mean_10_session_pnl_on_1000_usd_notional":round(sum(core_pnls)/len(core_pnls),2) if core_pnls else None,
      "median_10_session_pnl_on_1000_usd_notional":round(sorted(core_pnls)[len(core_pnls)//2],2) if core_pnls else None,
      "worst_10_session_pnl_on_1000_usd_notional":round(min(core_pnls),2) if core_pnls else None,
      "positive_10_session_ratio_pct":round(100*sum(x>0 for x in core_pnls)/len(core_pnls),4) if core_pnls else None,
      "note":"Underlying-only matched price-path control; not option P&L or a $80k portfolio return."}
    result["research_id"] = "QQQ_OPTION_SHORTLIST_REPLAY_V1"
    result["evidence_class"] = "OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS"
    result["source_integrity"] = {"underlying_and_repo_source_pins":integrity,"annual_option_files":file_integrity}
    result["limitations"] = ["Source option chains end 2025-12-15; no option P&L beyond that date.",
      "Quotes are public EOD preservation snapshots reported as 16:00 ET; exact tick timestamp and fills are unverified.",
      "Episode results are a matched fixed-horizon event study, not compounded portfolio CAGR/MaxDD.",
      "No broker margin, assignment, early exercise, forced liquidation, multi-leg fill sequencing, or market impact model.",
      "Terminal loss is intrinsic payoff at strike knots using observed entry-side prices; it does not bound interim liquidation losses.",
      "Candidate selection is fixed by DTE/delta and not optimized on P&L; the signal-family thresholds are a research hypothesis and require a later unseen holdout."]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/"summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    md=["# QQQ Option Shortlist Replay V1", "",f"Evidence: {result['evidence_class']}","",
        f"- Signals: {len(signal_days)}; processed: {selected_signal_count}; sessions: {len(expected)} ({START_DATE} to {SOURCE_END_DATE}).",
        f"- Matched QQQ-core control: {json.dumps(result['qqq_core_1000_notional_control'],ensure_ascii=False)}","",
        "## Strategy results (one unit per episode)","",
        "| Strategy | Opened | Resolved | Win rate | Mean P&L | Worst P&L | PF | Episodes sizeable at 1% NAV tail budget |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, s in result["strategy_summary"].items():
        md.append(f"| {name} | {s['opened_episodes']} | {s['resolved']} | {s['win_rate_pct']} | {s['mean_one_unit_net_pnl_usd']} | {s['worst_one_unit_net_pnl_usd']} | {s['profit_factor']} | {s['tail_budget_1pct_nav_sizeable_episode_count']} |")
    md += ["","## Interpretation guardrails",""]+[f"- {s}" for s in result["limitations"]]
    (out_dir/"summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    write_csv(out_dir/"trades.csv",trades)
    write_csv(out_dir/"core_control.csv",core_rows)
    write_csv(out_dir/"signals.csv",selected_signals)
    manifest={"research_id":result["research_id"],"source_end":SOURCE_END_DATE,"source_sessions":len(expected),"signals":len(signal_days),
      "trade_rows":len(trades),"source_file_count":len(file_integrity),"source_file_git_blob_sha":{k:v.get("git_blob_sha") for k,v in file_integrity.items()},
      "pricing_evidence":result["evidence_class"],"nav_reference_usd":NAV_USD,"source_integrity_status":"PINNED_SOURCE_VERIFICATION_COMPLETED_BY_REUSED_AUDIT"}
    (out_dir/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=ROOT/"artifacts"/"qqq_option_shortlist_v1")
    args=parser.parse_args()
    result=run(args.out)
    print(json.dumps({"research_id":result["research_id"],"evidence_class":result["evidence_class"],
      "signal_summary":result["signal_summary"],"qqq_core_1000_notional_control":result["qqq_core_1000_notional_control"],
      "strategy_summary":result["strategy_summary"],"limitations":result["limitations"]},indent=2,ensure_ascii=False))
    print((args.out/"summary.md").read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
