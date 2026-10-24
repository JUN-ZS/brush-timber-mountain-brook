#!/usr/bin/env python3
"""Cash-secured single-account NAV replay for the frozen QQQ long put : SPY short put strategy."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import run_spy_far_tail_holding_trigger_v1 as holding
import qqq_spy_put_fixed_phase_v1 as engine
import spy_far_tail_hedge_v1 as hedge_engine

ROOT = Path(__file__).resolve().parent
POLICY = "HOLD_20_OR_DTE_LE_7"
TRIGGER = "ANY_OF_THREE_PREDECLARED"
TAIL_LABEL = "TAIL_10_DELTA"
INITIAL_CAPITALS = (100_000.0, 250_000.0, 500_000.0, 1_000_000.0)
PHASES = (0, 1, 2, 3, 4)
HEDGE_MODES = (("NO_HEDGE", 0), ("TAIL_10D_1X", 1), ("TAIL_10D_3X", 3))
MULTIPLIER = 100
OUT_DIR = ROOT / "results" / "spy_far_tail_nav_account_v1"


def number(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def integer(value: Any, default: int = 0) -> int:
    value_f = number(value)
    return int(value_f) if value_f is not None else default


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unit_side_cost(row: dict[str, Any]) -> float:
    slip = number(row.get("base_slippage_per_share")) or 0.05
    commission = number(row.get("base_commission_per_contract_per_side")) or 0.65
    return slip * MULTIPLIER + commission


def exact_quote(row: dict[str, Any] | None, contract_id: str, symbol: str, day: str) -> bool:
    return bool(
        isinstance(row, dict)
        and engine.normalized_contract_id(row) == contract_id
        and engine.standard_put_identity(row, symbol)
        and engine.as_day(row.get("date")) == day
        and engine.valid_quote(row)
    )


def base_open_cashflow(trade: dict[str, Any]) -> float:
    qask = number(trade.get("qqq_entry_ask"))
    sbid = number(trade.get("spy_entry_bid"))
    lqty, sqty = integer(trade.get("long_qqq_qty")), integer(trade.get("short_spy_qty"))
    if qask is None or sbid is None or qask <= 0 or sbid <= 0 or min(lqty, sqty) < 1:
        raise ValueError(f"Bad base entry prices/quantities for {trade.get('trade_key')}")
    gross = MULTIPLIER * (sqty * sbid - lqty * qask)
    return gross - (lqty + sqty) * unit_side_cost(trade)


def base_close_cashflow(trade: dict[str, Any], qrow: dict[str, Any], srow: dict[str, Any]) -> float:
    lqty, sqty = integer(trade.get("long_qqq_qty")), integer(trade.get("short_spy_qty"))
    return MULTIPLIER * (
        lqty * float(qrow["bid"]) - sqty * float(srow["ask"])
    ) - (lqty + sqty) * unit_side_cost(trade)


def tail_close_cashflow(position: dict[str, Any], row: dict[str, Any]) -> float:
    qty = integer(position["tail_qty"])
    return MULTIPLIER * qty * float(row["bid"]) - qty * unit_side_cost(position["trade"])


def mark_value(position: dict[str, Any], q_by_id: dict[str, dict[str, Any]],
               s_by_id: dict[str, dict[str, Any]], day: str) -> tuple[float | None, int, int]:
    """Liquidation-side EOD valuation. Never forward-fill a missing or invalid quote."""
    trade = position["trade"]
    missing = 0
    size_shortfalls = 0
    value = 0.0
    if not position.get("base_closed"):
        qid, sid = str(trade.get("qqq_contract_id") or ""), str(trade.get("spy_contract_id") or "")
        qrow, srow = q_by_id.get(qid), s_by_id.get(sid)
        if not exact_quote(qrow, qid, "QQQ", day) or not exact_quote(srow, sid, "SPY", day):
            return None, 1, 0
        lqty, sqty = integer(trade.get("long_qqq_qty")), integer(trade.get("short_spy_qty"))
        if engine.displayed_size(qrow, "bid") < lqty or engine.displayed_size(srow, "ask") < sqty:
            size_shortfalls += 1
        value += MULTIPLIER * (
            lqty * float(qrow["bid"]) - sqty * float(srow["ask"])
        ) - (lqty + sqty) * unit_side_cost(trade)

    if position.get("tail_open"):
        tail_id = str(position.get("tail_contract_id") or "")
        tail_row = s_by_id.get(tail_id)
        if not exact_quote(tail_row, tail_id, "SPY", day):
            return None, 1, size_shortfalls
        qty = integer(position.get("tail_qty"))
        if engine.displayed_size(tail_row, "bid") < qty:
            size_shortfalls += 1
        value += MULTIPLIER * qty * float(tail_row["bid"]) - qty * unit_side_cost(trade)
    return value, missing, size_shortfalls


def make_account(capital: float, phase: int, hedge_mode: str, hedge_qty: int) -> dict[str, Any]:
    return {
        "capital": capital, "phase": phase, "hedge_mode": hedge_mode, "hedge_qty": hedge_qty,
        "cash": capital, "collateral": 0.0, "positions": {}, "taken_trade_keys": set(),
        "skipped_capital": 0, "resolved_base": 0, "delayed_base_exit_attempts": 0,
        "base_exit_delays": 0, "tail_attempts": 0, "tail_entries": 0,
        "tail_capital_blocked": 0, "tail_quote_gate_failed": 0, "tail_exit_delays": 0,
        "capital_blocked_trade_keys": [], "nav_rows": [], "peak_collateral": 0.0,
        "max_open_base_positions": 0, "realized_base_pnl_check_abs_max": 0.0,
        "realized_base_pnl_check_n": 0, "mark_gap_dates": 0, "mark_gap_position_days": 0,
        "mark_size_shortfall_days": 0,
    }


def prepare_accounts(trades_by_phase: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    accounts = []
    for phase in PHASES:
        if not trades_by_phase.get(phase):
            raise ValueError(f"No DTE45 / {POLICY} base trades for phase {phase}")
        for capital in INITIAL_CAPITALS:
            for mode, qty in HEDGE_MODES:
                account = make_account(capital, phase, mode, qty)
                account["scheduled_trades"] = {str(t["trade_key"]): t for t in trades_by_phase[phase]}
                accounts.append(account)
    return accounts


def close_due_positions(account: dict[str, Any], day: str,
                        q_by_id: dict[str, dict[str, Any]], s_by_id: dict[str, dict[str, Any]]) -> None:
    for key, pos in list(account["positions"].items()):
        trade = pos["trade"]
        target_exit = str(trade.get("exit_date") or "")
        if not target_exit or day < target_exit or pos.get("base_closed"):
            continue
        qid, sid = str(trade.get("qqq_contract_id") or ""), str(trade.get("spy_contract_id") or "")
        qrow, srow = q_by_id.get(qid), s_by_id.get(sid)
        valid = exact_quote(qrow, qid, "QQQ", day) and exact_quote(srow, sid, "SPY", day)
        executable = bool(
            valid
            and engine.displayed_size(qrow, "bid") >= integer(trade.get("long_qqq_qty"))
            and engine.displayed_size(srow, "ask") >= integer(trade.get("short_spy_qty"))
        )
        if not executable:
            if day == target_exit:
                account["base_exit_delays"] += 1
            account["delayed_base_exit_attempts"] += 1
            continue

        close_flow = base_close_cashflow(trade, qrow, srow)
        account["cash"] += close_flow
        collateral_release = MULTIPLIER * integer(trade.get("short_spy_qty")) * float(trade["spy_strike"])
        account["collateral"] = max(0.0, account["collateral"] - collateral_release)
        net_source = number(trade.get("net_pnl_usd"))
        if day == target_exit and net_source is not None and str(trade.get("status", "")).upper() == "RESOLVED":
            open_flow = base_open_cashflow(trade)
            reconciliation = abs(open_flow + close_flow - net_source)
            account["realized_base_pnl_check_abs_max"] = max(
                account["realized_base_pnl_check_abs_max"], reconciliation
            )
            account["realized_base_pnl_check_n"] += 1
        account["resolved_base"] += 1
        pos["base_closed"] = True
        if not pos.get("tail_open"):
            del account["positions"][key]


def close_due_tails(account: dict[str, Any], day: str,
                    s_by_id: dict[str, dict[str, Any]]) -> None:
    for key, pos in list(account["positions"].items()):
        if not pos.get("tail_open"):
            if pos.get("base_closed"):
                del account["positions"][key]
            continue
        trade = pos["trade"]
        target_exit = str(trade.get("exit_date") or "")
        if not target_exit or day < target_exit:
            continue
        tail_id = str(pos.get("tail_contract_id") or "")
        row = s_by_id.get(tail_id)
        valid = exact_quote(row, tail_id, "SPY", day)
        executable = bool(valid and engine.displayed_size(row, "bid") >= integer(pos.get("tail_qty")))
        if not executable:
            if day == target_exit:
                account["tail_exit_delays"] += 1
            continue
        account["cash"] += tail_close_cashflow(pos, row)
        pos["tail_open"] = False
        if pos.get("base_closed"):
            del account["positions"][key]


def open_due_base_positions(account: dict[str, Any], day: str,
                            q_by_id: dict[str, dict[str, Any]], s_by_id: dict[str, dict[str, Any]]) -> None:
    for key, trade in sorted(account["scheduled_trades"].items(), key=lambda item: (str(item[1]["entry_date"]), item[0])):
        if key in account["taken_trade_keys"] or str(trade.get("entry_date") or "") != day:
            continue
        account["taken_trade_keys"].add(key)
        qid, sid = str(trade.get("qqq_contract_id") or ""), str(trade.get("spy_contract_id") or "")
        qrow, srow = q_by_id.get(qid), s_by_id.get(sid)
        valid = exact_quote(qrow, qid, "QQQ", day) and exact_quote(srow, sid, "SPY", day)
        executable = bool(
            valid
            and engine.displayed_size(qrow, "ask") >= integer(trade.get("long_qqq_qty"))
            and engine.displayed_size(srow, "bid") >= integer(trade.get("short_spy_qty"))
        )
        if not executable:
            account["skipped_capital"] += 1
            account["capital_blocked_trade_keys"].append(key + ":ENTRY_QUOTE_UNAVAILABLE")
            continue
        entry_flow = base_open_cashflow(trade)
        reserved = MULTIPLIER * integer(trade.get("short_spy_qty")) * float(trade["spy_strike"])
        if account["cash"] + entry_flow - account["collateral"] - reserved < -0.01:
            account["skipped_capital"] += 1
            account["capital_blocked_trade_keys"].append(key + ":CASH_SECURED_CAPITAL_LIMIT")
            continue
        account["cash"] += entry_flow
        account["collateral"] += reserved
        account["peak_collateral"] = max(account["peak_collateral"], account["collateral"])
        pos = {
            "trade": trade, "opened_date": day, "tail_open": False, "tail_bought": False,
            "base_closed": False, "tail_contract_id": None, "tail_qty": 0,
            "tail_target_exit_date": str(trade.get("exit_date") or ""),
        }
        account["positions"][key] = pos
        account["max_open_base_positions"] = max(
            account["max_open_base_positions"],
            sum(1 for p in account["positions"].values() if not p.get("base_closed"))
        )


def open_due_tails(account: dict[str, Any], day: str,
                   s_by_id: dict[str, dict[str, Any]]) -> None:
    qty = account["hedge_qty"]
    if qty not in (1, 3):
        return
    for key, pos in list(account["positions"].items()):
        if pos.get("tail_bought") or pos.get("base_closed"):
            continue
        trade = pos["trade"]
        hedge = trade.get(f"_nav_hedge_row_{qty}x")
        if not hedge:
            continue
        planned_date = str(hedge.get("tail_entry_date") or "")
        if not planned_date or planned_date != day:
            continue
        if not truth(hedge.get("triggered")):
            pos["tail_bought"] = True
            continue
        account["tail_attempts"] += 1
        if not truth(hedge.get("tail_entry_executable")):
            account["tail_quote_gate_failed"] += 1
            pos["tail_bought"] = True
            continue
        tail_id = str(hedge.get("tail_contract_id") or "")
        row = s_by_id.get(tail_id)
        ask = number(hedge.get("tail_entry_ask"))
        if (
            ask is None or ask <= 0 or not exact_quote(row, tail_id, "SPY", day)
            or abs(float(row["ask"]) - ask) > 1e-5
            or engine.displayed_size(row, "ask") < qty
        ):
            account["tail_quote_gate_failed"] += 1
            pos["tail_bought"] = True
            continue
        entry_fee = qty * unit_side_cost(trade)
        debit = qty * MULTIPLIER * ask + entry_fee
        if account["cash"] - debit - account["collateral"] < -0.01:
            account["tail_capital_blocked"] += 1
            pos["tail_bought"] = True
            continue
        account["cash"] -= debit
        pos.update({
            "tail_open": True, "tail_bought": True, "tail_contract_id": tail_id,
            "tail_qty": qty, "tail_entry_date": day, "tail_entry_ask": ask,
            "tail_target_exit_date": str(trade.get("exit_date") or ""),
        })
        account["tail_entries"] += 1


def account_nav(account: dict[str, Any], day: str,
                q_by_id: dict[str, dict[str, Any]], s_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    total_market_value = 0.0
    missing = 0
    size_shortfalls = 0
    base_open_n = 0
    tail_open_n = 0
    for pos in account["positions"].values():
        if not pos.get("base_closed"):
            base_open_n += 1
        if pos.get("tail_open"):
            tail_open_n += 1
        value, miss, shortfall = mark_value(pos, q_by_id, s_by_id, day)
        if value is None:
            missing += max(1, miss)
        else:
            total_market_value += value
        size_shortfalls += shortfall
    nav = account["cash"] + total_market_value if missing == 0 else None
    free_cash = account["cash"] - account["collateral"]
    row = {
        "date": day, "initial_capital_usd": account["capital"], "phase": account["phase"],
        "hedge_mode": account["hedge_mode"], "hedge_qty": account["hedge_qty"],
        "cash_usd": round(account["cash"], 2), "reserved_cash_collateral_usd": round(account["collateral"], 2),
        "free_cash_after_collateral_usd": round(free_cash, 2),
        "open_base_positions_n": base_open_n, "open_tail_positions_n": tail_open_n,
        "position_market_value_net_liquidation_cost_usd": round(total_market_value, 2) if missing == 0 else None,
        "nav_usd": round(nav, 2) if nav is not None else None,
        "mark_complete": missing == 0, "unmarked_position_n": missing,
        "displayed_size_shortfall_position_n": size_shortfalls,
    }
    if nav is None:
        account["mark_gap_dates"] += 1
        account["mark_gap_position_days"] += missing
    if size_shortfalls:
        account["mark_size_shortfall_days"] += 1
    account["nav_rows"].append(row)
    return row


def calculate_summaries(accounts: list[dict[str, Any]], start_day: str, source_end_day: str):
    summary_rows, annual_rows, daily_rows = [], [], []
    for account in accounts:
        daily = account["nav_rows"]
        daily_rows.extend(daily)
        valid = [r for r in daily if r["nav_usd"] is not None]
        if not valid:
            raise ValueError(f"No fully marked NAV observations for {account['capital']}/{account['phase']}/{account['hedge_mode']}")
        last = valid[-1]
        peak = -math.inf
        max_dd = 0.0
        for r in valid:
            nav = float(r["nav_usd"])
            peak = max(peak, nav)
            dd = nav / peak - 1.0 if peak > 0 else -1.0
            max_dd = min(max_dd, dd)
        elapsed_days = max(1, (date.fromisoformat(str(last["date"])) - date.fromisoformat(start_day)).days)
        cagr = (float(last["nav_usd"]) / account["capital"]) ** (365.25 / elapsed_days) - 1 if last["nav_usd"] > 0 else None

        by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for r in valid:
            by_year[int(str(r["date"])[:4])].append(r)
        prior_year_nav = account["capital"]
        for year in sorted(by_year):
            year_rows = by_year[year]
            year_last = year_rows[-1]
            year_nav = float(year_last["nav_usd"])
            year_return = (year_nav / prior_year_nav - 1.0) * 100.0 if prior_year_nav > 0 else None
            annual_rows.append({
                "initial_capital_usd": account["capital"], "phase": account["phase"],
                "hedge_mode": account["hedge_mode"], "hedge_qty": account["hedge_qty"],
                "year": year, "year_start_nav_usd": round(prior_year_nav, 2),
                "last_valid_nav_date_in_year": year_last["date"], "year_end_nav_usd": round(year_nav, 2),
                "annual_return_pct": round(year_return, 4) if year_return is not None else None,
                "valid_nav_observations_n": len(year_rows),
                "marked_calendar_rows_n": sum(1 for r in daily if str(r["date"]).startswith(str(year))),
                "unmarked_calendar_rows_n": sum(1 for r in daily if str(r["date"]).startswith(str(year)) and r["nav_usd"] is None),
                "year_return_denominator": "initial capital for first observed year; previous available calendar-year NAV thereafter",
            })
            prior_year_nav = year_nav

        terminal_value = float(last["nav_usd"])
        summary_rows.append({
            "initial_capital_usd": account["capital"], "phase": account["phase"],
            "hedge_mode": account["hedge_mode"], "hedge_qty": account["hedge_qty"],
            "start_date_for_cagr": start_day, "source_window_end_date": source_end_day,
            "last_valid_nav_date": last["date"], "terminal_nav_usd": round(terminal_value, 2),
            "terminal_cash_usd": round(float(last["cash_usd"]), 2),
            "terminal_collateral_usd": round(float(last["reserved_cash_collateral_usd"]), 2),
            "total_return_pct": round((terminal_value / account["capital"] - 1.0) * 100.0, 4),
            "cagr_pct": round(cagr * 100.0, 4) if cagr is not None else None,
            "observed_nav_max_drawdown_pct": round(max_dd * 100.0, 4),
            "nav_observation_coverage_pct": round(100.0 * len(valid) / len(daily), 4),
            "unmarked_nav_days_n": account["mark_gap_dates"],
            "unmarked_position_days_n": account["mark_gap_position_days"],
            "mark_size_shortfall_days_n": account["mark_size_shortfall_days"],
            "planned_entries_n": len(account["scheduled_trades"]),
            "entry_signals_taken_n": len(account["taken_trade_keys"]) - account["skipped_capital"],
            "entry_signals_skipped_n": account["skipped_capital"],
            "base_trades_closed_n": account["resolved_base"],
            "base_exit_delayed_positions_n": account["base_exit_delays"],
            "delayed_base_exit_attempts_n": account["delayed_base_exit_attempts"],
            "tail_entry_attempts_n": account["tail_attempts"],
            "tail_entries_bought_n": account["tail_entries"],
            "tail_capital_blocked_n": account["tail_capital_blocked"],
            "tail_quote_gate_failed_n": account["tail_quote_gate_failed"],
            "tail_exit_delayed_positions_n": account["tail_exit_delays"],
            "peak_cash_collateral_required_usd": round(account["peak_collateral"], 2),
            "peak_collateral_as_pct_initial_capital": round(100.0 * account["peak_collateral"] / account["capital"], 4),
            "max_concurrent_base_positions_n": account["max_open_base_positions"],
            "cash_only_returns_assumed_pct": 0.0,
            "base_exit_pnl_reconciliation_abs_max_usd": round(account["realized_base_pnl_check_abs_max"], 4),
            "base_exit_pnl_reconciliation_rows_n": account["realized_base_pnl_check_n"],
            "nav_gap_note": "No stale quote is forward-filled. Max drawdown and CAGR use only fully marked NAV observations; gaps can understate drawdown.",
        })
    return daily_rows, annual_rows, summary_rows


def build_report(manifest: dict[str, Any], summary: list[dict[str, Any]], annual: list[dict[str, Any]]) -> str:
    lines = [
        "# SPY Far-Tail Trigger — Single-Account NAV Replay V1",
        "",
        "## Research design",
        "",
        "- Base strategy is fixed QQQ LONG PUT 1 : SPY SHORT PUT 3, policy HOLD_20_OR_DTE_LE_7, DTE45 arm only.",
        "- Each of the five phase schedules is a separate account path. Phase schedules are never summed into one portfolio.",
        "- Each path uses fixed contract quantities, no contract scaling; profits/losses affect later entry capacity through account cash.",
        "- Opening/closing cash flows use QQQ LONG PUT Ask/Bid and SPY SHORT PUT Bid/Ask, with USD 0.05 per option-share per side plus USD 0.65 per contract per side.",
        "- SPY short PUTs are cash-secured at 100% of strike × quantity × 100. QQQ long puts and SPY short puts are not cross-margined against each other.",
        "- Starting capital scenarios are USD 100,000, USD 250,000, USD 500,000 and USD 1,000,000. A signal that cannot meet cash collateral after entry costs is skipped, with no retry.",
        "- Hedge candidates use the predeclared OR trigger, same-contract SPY 10-absolute-Delta PUT and 1x or 3x quantity. Hedge debit is paid from available cash after collateral; insufficient cash blocks the hedge.",
        "- If a close quote/size is unavailable on the planned exit date, the position remains open and retries on later observed sessions. No base or tail mark is forward-filled.",
        "",
        "## Account-level outcomes",
        "",
        "| Starting NAV | Phase | Overlay | Trades taken / planned | Ending NAV | Total return | CAGR | Observed NAV MaxDD | NAV coverage |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(summary, key=lambda x: (float(x["initial_capital_usd"]), int(x["phase"]), str(x["hedge_mode"]))):
        lines.append(
            f"| USD {float(r['initial_capital_usd']):,.0f} | {r['phase']} | {r['hedge_mode']} "
            f"| {r['entry_signals_taken_n']} / {r['planned_entries_n']} "
            f"| USD {float(r['terminal_nav_usd']):,.2f} | {float(r['total_return_pct']):.2f}% "
            f"| {(str(r['cagr_pct']) + '%') if r['cagr_pct'] is not None else 'N/A'} "
            f"| {float(r['observed_nav_max_drawdown_pct']):.2f}% | {float(r['nav_observation_coverage_pct']):.2f}% |"
        )
    lines += [
        "",
        "## Annual NAV returns",
        "",
        "Annual returns are based on the last fully marked NAV observation in each calendar year; the first observed year uses initial capital as its denominator. The last valid NAV date is shown in nav_annual.csv.",
        "",
        "| Starting NAV | Phase | Overlay | Year | Last valid NAV date | Year-end NAV | Annual return |",
        "|---:|---:|---|---:|---|---:|---:|",
    ]
    for r in sorted(annual, key=lambda x: (float(x["initial_capital_usd"]), int(x["phase"]), str(x["hedge_mode"]), int(x["year"]))):
        lines.append(
            f"| USD {float(r['initial_capital_usd']):,.0f} | {r['phase']} | {r['hedge_mode']} | {r['year']} "
            f"| {r['last_valid_nav_date_in_year']} | USD {float(r['year_end_nav_usd']):,.2f} "
            f"| {float(r['annual_return_pct']):.2f}% |"
        )
    lines += [
        "",
        "## Accounting and interpretation limits",
        "",
        "- NAV is cash plus liquidation-side market value of open positions, net of modeled close-side friction. Realized close cash flows remove closed positions from the mark sum.",
        "- Mark dates with any invalid/missing exact-contract quote are output with blank NAV, not carried forward. CAGR and observed MaxDD use only fully marked dates; MaxDD can understate the true path drawdown across gaps. Coverage is shown per account.",
        "- A 0% risk-free/cash yield is assumed. No taxes, dividends, financing, borrow costs, early assignment, stock delivery, exercise fees, or broker-specific margin rules are modeled. The 100% cash-secured SPY put reserve is deliberately conservative, but is not a full assignment ledger.",
        "- The next-session daily Ask and EOD bid/ask are still research pricing proxies, not timestamped verified fills. Displayed size is not guaranteed liquidity.",
        "- These are fixed-lot, cash-constrained accounts, not percent-of-NAV position sizing. Compounding affects the ability to fund later fixed-size entries; it does not automatically scale contracts.",
        "- 2023–2025 data are not globally virgin; five phases are alternate overlapping start schedules and are independent account paths, not independent statistical samples.",
        "- This is a research backtest only. No broker connection, live orders, or main-branch merge.",
        "",
        "## Reproducibility",
        "",
        f"- Manifest status: {manifest['status']}",
        f"- Branch: {manifest['branch']}",
        f"- Baseline source rows loaded: {manifest['policy_rows_loaded']}",
        f"- Daily account NAV rows emitted: {manifest['daily_nav_rows']}",
        f"- Source-chain window: {manifest['source_start_date']} through {manifest['source_end_date']}",
        f"- Base input ledger hash match: {manifest['baseline_input_hashes_match_overlay_manifest']}",
        f"- Holding-trigger output SHA-256: {manifest['holding_trade_level_sha256']}",
        "",
    ]
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    results = ROOT / "results"
    holding_path = results / "spy_far_tail_holding_trigger_v2" / "holding_trade_level.csv"
    overlay_root = results / "spy_far_tail_hedge_v1"
    if not holding_path.is_file():
        raise FileNotFoundError(f"Missing completed V2 holding-trigger ledger: {holding_path}")
    _, all_trades, input_hashes, overlay_manifest, _ = holding.load_replay_inputs(results, overlay_root)
    config_rows = read_csv(holding_path)
    hedge_configs: dict[tuple[str, int], dict[str, str]] = {}
    for row in config_rows:
        if (
            row.get("trigger_rule") == TRIGGER
            and row.get("tail_label") == TAIL_LABEL
            and integer(row.get("tail_quantity")) in (1, 3)
            and row.get("arm") == "DTE45"
            and integer(row.get("phase")) in PHASES
            and row.get("policy") == POLICY
        ):
            hedge_configs[(str(row.get("trade_key")), integer(row.get("tail_quantity")))] = row

    trades_by_phase: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in all_trades:
        if raw.get("arm") != "DTE45" or raw.get("policy") != POLICY:
            continue
        phase = integer(raw.get("phase"), -1)
        if phase not in PHASES or not raw.get("entry_date"):
            continue
        trade = dict(raw)
        trade["_nav_hedge_row_1x"] = hedge_configs.get((str(trade["trade_key"]), 1))
        trade["_nav_hedge_row_3x"] = hedge_configs.get((str(trade["trade_key"]), 3))
        trades_by_phase[phase].append(trade)
    for phase in PHASES:
        trades_by_phase[phase].sort(key=lambda t: (str(t.get("entry_date")), str(t.get("trade_key"))))
        if not trades_by_phase[phase]:
            raise ValueError(f"No account-suitable DTE45 rows for phase {phase}")
        missing_configs = [
            str(t["trade_key"]) for t in trades_by_phase[phase]
            if (t["_nav_hedge_row_1x"] is None or t["_nav_hedge_row_3x"] is None)
        ]
        if missing_configs:
            raise ValueError(f"Missing frozen holding-trigger config rows: {missing_configs[:5]}")

    accounts = prepare_accounts(trades_by_phase)
    strategy_trades = [t for phase_rows in trades_by_phase.values() for t in phase_rows]
    start_day = (date.fromisoformat(min(str(t["entry_date"]) for t in strategy_trades)) - timedelta(days=1)).isoformat()
    end_day = max(str(t.get("_end_date") or t.get("last_observed_date") or t.get("entry_date"))
                  for t in strategy_trades)
    cache = args.cache
    years = range(int(start_day[:4]), int(end_day[:4]) + 1)
    qqq_paths, spy_paths, pins = [], [], []
    for year in years:
        p, pin = engine.download_verified("QQQ", year, cache / "qqq")
        qqq_paths.append(p); pins.append(pin)
        p, pin = engine.download_verified("SPY", year, cache / "spy")
        spy_paths.append(p); pins.append(pin)
    spot_maps: dict[str, dict[str, float]] = {}
    for symbol in ("QQQ", "SPY"):
        p, pin = engine.download_verified(symbol, None, cache / f"{symbol.lower()}-underlying")
        spot_maps[symbol] = engine.load_spots(p, symbol)
        pins.append(pin)
    trade_days = sorted(d for d in spot_maps["SPY"] if start_day < d <= end_day)

    for account in accounts:
        account["nav_rows"].append({
            "date": start_day, "initial_capital_usd": account["capital"], "phase": account["phase"],
            "hedge_mode": account["hedge_mode"], "hedge_qty": account["hedge_qty"],
            "cash_usd": account["capital"], "reserved_cash_collateral_usd": 0.0,
            "free_cash_after_collateral_usd": account["capital"], "open_base_positions_n": 0,
            "open_tail_positions_n": 0, "position_market_value_net_liquidation_cost_usd": 0.0,
            "nav_usd": account["capital"], "mark_complete": True, "unmarked_position_n": 0,
            "displayed_size_shortfall_position_n": 0,
        })

    stream_stats = {
        "qqq": {"chain_dates": 0, "put_rows": 0, "first_chain_date": None, "last_chain_date": None},
        "spy": {"chain_dates": 0, "put_rows": 0, "first_chain_date": None, "last_chain_date": None},
    }
    for day, q_rows, s_rows in holding.iter_merged_symbol_days(
        qqq_paths, spy_paths, start_day, end_day, stream_stats, trade_days
    ):
        q_by_id, s_by_id = engine.rows_by_id(q_rows), engine.rows_by_id(s_rows)
        for account in accounts:
            close_due_positions(account, day, q_by_id, s_by_id)
            close_due_tails(account, day, s_by_id)
            open_due_base_positions(account, day, q_by_id, s_by_id)
            open_due_tails(account, day, s_by_id)
            account_nav(account, day, q_by_id, s_by_id)

    daily_rows, annual_rows, summary_rows = calculate_summaries(accounts, start_day, end_day)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "nav_daily.csv", daily_rows)
    write_csv(out / "nav_annual.csv", annual_rows)
    write_csv(out / "nav_summary.csv", summary_rows)
    manifest = {
        "schema": "spy-far-tail-single-account-nav.v1",
        "status": "COMPLETED" if daily_rows and annual_rows and summary_rows else "FAILED_EMPTY_OUTPUT",
        "branch": "research/spy-far-tail-nav-account-v1",
        "policy": POLICY, "arm": "DTE45", "phases_are_separate_accounts": True,
        "phase_ids": list(PHASES), "starting_capital_scenarios_usd": list(INITIAL_CAPITALS),
        "hedge_scenarios": [{"name": name, "contracts": qty} for name, qty in HEDGE_MODES],
        "policy_rows_loaded": sum(len(v) for v in trades_by_phase.values()),
        "daily_nav_rows": len(daily_rows), "annual_nav_rows": len(annual_rows),
        "account_summary_rows": len(summary_rows),
        "source_start_date": start_day, "source_end_date": end_day,
        "baseline_input_hashes_match_overlay_manifest": input_hashes == overlay_manifest.get("input_ledger_sha256"),
        "baseline_input_ledger_sha256": input_hashes,
        "holding_trade_level_sha256": sha256_file(holding_path),
        "holding_trade_level_rows": len(config_rows),
        "option_chain_source": engine.SOURCE_REPO,
        "option_chain_source_commit": engine.SOURCE_COMMIT,
        "verified_source_pins": pins,
        "capital_rule": "Cash-secured SPY short puts at 100% strike notional; no cross-underlying margin credit; skip base entries when cash after entry costs cannot cover existing plus new collateral; no re-entry retry.",
        "mark_rule": "Liquidation-side bid/ask values less modeled close-side friction; no stale quote forward-fill; NAV blank if any open option position has a missing/invalid exact-contract mark.",
        "hedge_exit_rule": "Attempt exact base exit date; if displayed bid/size is unavailable, retain hedge and retry on subsequent observed sessions while the quote remains available.",
        "costs": {"slippage_per_share_per_side_usd": 0.05, "commission_per_contract_per_side_usd": 0.65},
        "known_limits": [
            "Not a broker fill replay; daily EOD quotes and displayed size are proxies.",
            "No early assignment, stock delivery, exercise fees, taxes, dividends, financing or cash yield.",
            "No automatic percentage-of-NAV resizing; contract counts remain 1 QQQ long PUT and 3 SPY short PUT per accepted entry.",
            "NAV coverage gaps are left blank, not forward-filled; observed MaxDD may understate drawdown over missing intervals.",
            "The phase schedules are alternate overlapping start dates and are not combined in a single account.",
        ],
    }
    if manifest["status"] != "COMPLETED" or not manifest["baseline_input_hashes_match_overlay_manifest"]:
        raise RuntimeError("Account NAV run failed completeness or frozen-baseline hash gate")
    if max((r["base_exit_pnl_reconciliation_abs_max_usd"] for r in summary_rows), default=0.0) > 1.00:
        raise RuntimeError("Base exit cashflow does not reconcile to the frozen realized P&L ledger within USD 1.00")
    (out / "nav_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    report = build_report(manifest, summary_rows, annual_rows)
    (out / "SPY_FAR_TAIL_NAV_ACCOUNT_REPORT.md").write_text(report, encoding="utf-8")
    required = ("## Research design", "## Account-level outcomes", "## Annual NAV returns", "## Accounting and interpretation limits", "## Reproducibility")
    missing = [heading for heading in required if heading not in report]
    if missing or len(report) < 2500:
        raise RuntimeError(f"NAV report completeness gate failed: {missing}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "spy-options-nav-account-v1")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    manifest = run(args)
    print(json.dumps({
        "status": manifest["status"], "policy_rows_loaded": manifest["policy_rows_loaded"],
        "daily_nav_rows": manifest["daily_nav_rows"], "annual_nav_rows": manifest["annual_nav_rows"],
        "account_summary_rows": manifest["account_summary_rows"], "output_dir": str(args.out),
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
