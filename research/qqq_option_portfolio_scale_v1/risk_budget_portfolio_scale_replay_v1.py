#!/usr/bin/env python3
"""Risk-budgeted event-driven QQQ Core + listed-option account replay.

Uses the same pinned EOD source, event trigger and exact-contract selection as the
one-unit shortlist screen. Every portfolio starts with $80,000, holds a fixed
price-only QQQ core equal to 42% of initial NAV, and sizes one conditional option
structure from prior complete liquidation NAV at 0.5%, 1%, or 2% terminal-tail
budget. Output is an observed quote-side simulation, not confirmed fills or broker
margin approval.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SHORTLIST_DIR = ROOT / "research" / "qqq_option_shortlist_v1"
sys.path.insert(0, str(SHORTLIST_DIR))
import qqq_option_shortlist_replay_v1 as core

START_DATE = "2018-03-01"
SOURCE_END_DATE = "2025-12-15"
INITIAL_NAV = float(os.environ.get("QQQ_INITIAL_NAV_USD", "80000"))
if not math.isfinite(INITIAL_NAV) or INITIAL_NAV <= 0:
    raise ValueError("QQQ_INITIAL_NAV_USD must be a finite positive amount")
CORE_WEIGHT = 0.42
RISK_BUDGETS = (0.005, 0.01, 0.02)
COST_CASES = {
    "BASE": (0.05, 0.65),
    "STRESS": (0.10, 0.65),
}
STRATEGIES = (
    "CALL_DEBIT_50D_10D",
    "CALL_DEBIT_PLUS_LONG_PUT_10D",
    "PUT_SHORT_HEAVY_1x1",
    "PUT_SHORT_HEAVY_1x4",
    "PUT_SHORT_HEAVY_1x5",
    "PUT_SHORT_HEAVY_1x6",
    "PUT_LONG_HEAVY_2x1",
)
HOLD_SESSIONS = 10
MAX_EXIT_DEFER_SESSIONS = 3
MIN_MULTIPLIER = 100.0


def num(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def as_day(value: Any) -> str:
    if value is None:
        return ""
    return value.isoformat()[:10] if hasattr(value, "isoformat") else str(value)[:10]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def identity_matches(row: dict[str, Any] | None, leg: dict[str, Any], session_day: str) -> bool:
    if not isinstance(row, dict):
        return False
    ident = core.cid(row.get("contract_id"))
    match = re.fullmatch(r"QQQ(\d{6})([CP])(\d{8})", ident)
    right = str(leg.get("right", "")).upper()
    if not match or match.group(2) != right or str(row.get("symbol", "")).upper() != "QQQ":
        return False
    try:
        encoded_expiry = datetime.strptime(match.group(1), "%y%m%d").date().isoformat()
    except ValueError:
        return False
    expiry = as_day(row.get("expiration"))
    strike = num(row.get("strike"))
    row_right = core.option_type(row)
    if (
        encoded_expiry != expiry
        or expiry != as_day(leg.get("expiry"))
        or row_right != right
        or strike is None
        or abs(strike - int(match.group(3)) / 1000.0) >= 0.00051
        or abs(strike - float(leg.get("strike"))) >= 0.00051
        or as_day(row.get("date")) != session_day
    ):
        return False
    try:
        return date.fromisoformat(expiry) > date.fromisoformat(session_day)
    except ValueError:
        return False


def legs_identity_valid(legs: list[dict[str, Any]], qmap: dict[str, dict[str, Any]], day: str) -> bool:
    return all(identity_matches(qmap.get(core.cid(leg.get("id"))), leg, day) for leg in legs)


def entry_depth_units(legs: list[dict[str, Any]], qmap: dict[str, dict[str, Any]]) -> int:
    capacities = []
    for leg in legs:
        row = qmap.get(core.cid(leg.get("id")))
        if not row:
            return 0
        side_field = "ask_size" if leg["side"] == "buy" else "bid_size"
        size = num(row.get(side_field))
        qty = int(leg.get("qty", 0))
        if size is None or size <= 0 or qty <= 0:
            return 0
        capacities.append(math.floor(size / qty))
    return min(capacities) if capacities else 0


def size_whole_units(
    nav: float,
    cash: float,
    risk_fraction: float,
    terminal_loss_per_unit: float,
    entry_cashflow_per_unit: float,
    depth_units: int,
) -> tuple[int, dict[str, Any]]:
    if nav <= 0 or cash <= 0 or terminal_loss_per_unit < 0 or depth_units <= 0:
        return 0, {"risk_budget_usd": max(0.0, nav * risk_fraction), "risk_units": 0,
                   "cash_units": 0, "depth_units": depth_units, "reason": "NAV_CASH_RISK_OR_DEPTH_BLOCK"}
    budget = nav * risk_fraction
    risk_units = depth_units if terminal_loss_per_unit <= 1e-9 else math.floor((budget + 1e-9) / terminal_loss_per_unit)
    if entry_cashflow_per_unit < -1e-9:
        cash_per_unit = -entry_cashflow_per_unit
        cash_units = math.floor((cash + 1e-9) / cash_per_unit)
    else:
        # Conservative reserve proxy for credit structures: reserve one-unit terminal loss in cash.
        cash_per_unit = terminal_loss_per_unit
        cash_units = depth_units if cash_per_unit <= 1e-9 else math.floor((cash + 1e-9) / cash_per_unit)
    units = max(0, min(depth_units, risk_units, cash_units))
    reason = "OK" if units > 0 else "NO_WHOLE_UNIT_FITS_RISK_CASH_DEPTH"
    return units, {
        "risk_budget_usd": round(budget, 2),
        "risk_units": int(risk_units),
        "cash_units": int(cash_units),
        "depth_units": int(depth_units),
        "cash_reserved_per_unit_usd": round(cash_per_unit, 2),
        "reason": reason,
    }


def scale_legs(legs: list[dict[str, Any]], units: int) -> list[dict[str, Any]]:
    return [{**leg, "qty": int(leg["qty"]) * units} for leg in legs]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("status\nNO_ROWS\n", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row.keys()))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def init_account(
    strategy: str, risk_fraction: float | None, cost_case: str, shares: int, first_spot: float
) -> dict[str, Any]:
    return {
        "account_id": f"{strategy}|risk={risk_fraction if risk_fraction is not None else 'NA'}|cost={cost_case}",
        "strategy_id": strategy,
        "risk_fraction": risk_fraction,
        "cost_case": cost_case,
        "slippage": COST_CASES.get(cost_case, (0.0, 0.0))[0],
        "commission": COST_CASES.get(cost_case, (0.0, 0.0))[1],
        "shares": shares,
        "cash": INITIAL_NAV - shares * first_spot,
        "option_cashflows": 0.0,
        "active": None,
        "previous_nav": INITIAL_NAV,
        "daily": [],
        "trades": [],
        "blocked_entries": 0,
        "entry_attempts": 0,
        "entries": 0,
        "exits": 0,
        "unresolved_exits": 0,
        "blocked_reasons": defaultdict(int),
        "max_abs_reconciliation_error_usd": 0.0,
        "missing_nav_marks": 0,
        "negative_cash_marks": 0,
    }


def close_due_positions(accounts: list[dict[str, Any]], qmap: dict[str, dict[str, Any]], session_day: str, idx: int) -> None:
    for account in accounts:
        pos = account["active"]
        if pos is None or pos.get("exit_censored") or idx < pos["exit_due_idx"]:
            continue
        identity_ok = legs_identity_valid(pos["legs"], qmap, session_day)
        if identity_ok:
            exit_cf, _contracts, reason = core.cashflow(
                pos["legs"], qmap, opening=False,
                slip=account["slippage"], commission=account["commission"]
            )
        else:
            exit_cf, reason = None, "EXIT_CONTRACT_IDENTITY_INVALID"
        if exit_cf is not None:
            account["cash"] += exit_cf
            account["option_cashflows"] += exit_cf
            net_pnl = pos["entry_cashflow_usd"] + exit_cf
            account["exits"] += 1
            account["trades"].append({
                "account_id": account["account_id"], "strategy_id": account["strategy_id"],
                "risk_fraction": account["risk_fraction"], "cost_case": account["cost_case"],
                "signal_date": pos["signal_date"], "entry_date": pos["entry_date"],
                "exit_date": session_day, "event": "EXIT", "status": "RESOLVED",
                "units": pos["units"], "contract_count": sum(x["qty"] for x in pos["legs"]),
                "entry_nav_usd": pos["entry_nav_usd"], "entry_cashflow_usd": pos["entry_cashflow_usd"],
                "exit_cashflow_usd": round(exit_cf, 2), "net_pnl_usd": round(net_pnl, 2),
                "one_unit_terminal_tail_loss_usd": pos["one_unit_tail_loss_usd"],
                "reserved_terminal_tail_loss_usd": pos["reserved_terminal_tail_loss_usd"],
                "exit_session_age": idx - pos["entry_idx"], "exit_delay_sessions": idx - pos["exit_due_idx"],
                "contract_legs": json.dumps(pos["legs"], separators=(",", ":")),
                "reason": "FIRST_VALID_SIDE_QUOTE_AT_OR_AFTER_10_SESSION_HORIZON",
            })
            account["active"] = None
        elif idx >= pos["exit_due_idx"] + MAX_EXIT_DEFER_SESSIONS:
            pos["exit_censored"] = True
            account["unresolved_exits"] += 1
            account["trades"].append({
                "account_id": account["account_id"], "strategy_id": account["strategy_id"],
                "risk_fraction": account["risk_fraction"], "cost_case": account["cost_case"],
                "signal_date": pos["signal_date"], "entry_date": pos["entry_date"],
                "last_checked_date": session_day, "event": "EXIT_UNRESOLVED", "status": "UNRESOLVED_EXIT_QUOTE",
                "units": pos["units"], "contract_count": sum(x["qty"] for x in pos["legs"]),
                "entry_nav_usd": pos["entry_nav_usd"], "entry_cashflow_usd": pos["entry_cashflow_usd"],
                "one_unit_terminal_tail_loss_usd": pos["one_unit_tail_loss_usd"],
                "reserved_terminal_tail_loss_usd": pos["reserved_terminal_tail_loss_usd"],
                "contract_legs": json.dumps(pos["legs"], separators=(",", ":")),
                "reason": reason,
            })


def attempt_entries(
    accounts: list[dict[str, Any]], candidates: dict[str, dict[str, Any]],
    candidate_status: dict[str, str], qmap: dict[str, dict[str, Any]], session_day: str, idx: int,
) -> None:
    for account in accounts:
        if account["strategy_id"] == "CORE_ONLY":
            continue
        account["entry_attempts"] += 1
        if account["active"] is not None:
            account["blocked_entries"] += 1
            account["blocked_reasons"]["PREVIOUS_POSITION_NOT_CLOSED"] += 1
            continue
        spec = candidates.get(account["strategy_id"])
        if spec is None:
            account["blocked_entries"] += 1
            why = candidate_status.get(account["strategy_id"], "CANDIDATE_NOT_AVAILABLE")
            account["blocked_reasons"][why] += 1
            continue
        nav = account.get("previous_nav")
        if nav is None or nav <= 0:
            account["blocked_entries"] += 1
            account["blocked_reasons"]["PRIOR_NAV_MARK_INCOMPLETE"] += 1
            continue
        unit_legs = spec["legs"]
        if not legs_identity_valid(unit_legs, qmap, session_day):
            account["blocked_entries"] += 1
            account["blocked_reasons"]["ENTRY_CONTRACT_IDENTITY_INVALID"] += 1
            continue
        entry_unit_cf, _contract_count, why = core.cashflow(
            unit_legs, qmap, opening=True,
            slip=account["slippage"], commission=account["commission"]
        )
        if entry_unit_cf is None:
            account["blocked_entries"] += 1
            account["blocked_reasons"][why] += 1
            continue
        risk = core.terminal_risk(unit_legs, entry_unit_cf)
        tail_loss = float(risk["terminal_worst_loss_usd"])
        depth = entry_depth_units(unit_legs, qmap)
        units, sizing = size_whole_units(
            float(nav), float(account["cash"]), float(account["risk_fraction"]),
            tail_loss, float(entry_unit_cf), depth,
        )
        if units <= 0:
            account["blocked_entries"] += 1
            account["blocked_reasons"][sizing["reason"]] += 1
            account["trades"].append({
                "account_id": account["account_id"], "strategy_id": account["strategy_id"],
                "risk_fraction": account["risk_fraction"], "cost_case": account["cost_case"],
                "signal_date": spec.get("signal_date", ""), "entry_date": session_day,
                "event": "ENTRY_BLOCKED", "status": "BLOCKED",
                "entry_nav_usd": round(float(nav), 2), "one_unit_terminal_tail_loss_usd": round(tail_loss, 2),
                "available_depth_units": depth, **sizing,
                "reason": sizing["reason"],
            })
            continue
        legs_scaled = scale_legs(unit_legs, units)
        entry_cf, contract_count, why = core.cashflow(
            legs_scaled, qmap, opening=True,
            slip=account["slippage"], commission=account["commission"]
        )
        if entry_cf is None:
            account["blocked_entries"] += 1
            account["blocked_reasons"][why] += 1
            continue
        if abs(float(entry_cf) - float(entry_unit_cf) * units) > 0.05:
            raise AssertionError(f"Cashflow scaling mismatch for {account['account_id']}: units={units}")
        if account["cash"] + entry_cf < -0.01:
            account["blocked_entries"] += 1
            account["blocked_reasons"]["CASH_WOULD_BE_NEGATIVE_AT_ENTRY"] += 1
            continue
        account["cash"] += entry_cf
        account["option_cashflows"] += entry_cf
        pos = {
            "signal_date": spec.get("signal_date", ""),
            "entry_date": session_day,
            "entry_idx": idx,
            "exit_due_idx": min(idx + HOLD_SESSIONS, account["_session_count"] - 1),
            "legs": legs_scaled,
            "units": units,
            "entry_cashflow_usd": float(entry_cf),
            "one_unit_tail_loss_usd": round(tail_loss, 2),
            "reserved_terminal_tail_loss_usd": round(tail_loss * units, 2),
            "entry_nav_usd": float(nav),
            "risk_budget_usd": sizing["risk_budget_usd"],
            "available_depth_units": depth,
            "exit_censored": False,
        }
        account["active"] = pos
        account["entries"] += 1
        account["trades"].append({
            "account_id": account["account_id"], "strategy_id": account["strategy_id"],
            "risk_fraction": account["risk_fraction"], "cost_case": account["cost_case"],
            "signal_date": spec.get("signal_date", ""), "entry_date": session_day,
            "event": "ENTRY", "status": "OPENED",
            "units": units, "contract_count": contract_count,
            "entry_nav_usd": round(float(nav), 2), "entry_cashflow_usd": round(float(entry_cf), 2),
            "one_unit_terminal_tail_loss_usd": round(tail_loss, 2),
            "reserved_terminal_tail_loss_usd": round(tail_loss * units, 2),
            "available_depth_units": depth, **sizing,
            "contract_legs": json.dumps(legs_scaled, separators=(",", ":")),
            "reason": "NEXT_OBSERVED_SESSION_EXACT_CONTRACT_ENTRY",
        })


def daily_mark(account: dict[str, Any], session_day: str, spot: float, first_spot: float,
               qmap: dict[str, dict[str, Any]]) -> dict[str, Any]:
    core_mv = account["shares"] * spot
    core_pnl = account["shares"] * (spot - first_spot)
    open_close_cf: float | None = 0.0
    active = account["active"]
    if active is not None:
        if legs_identity_valid(active["legs"], qmap, session_day):
            open_close_cf, _contract_count, _why = core.cashflow(
                active["legs"], qmap, opening=False,
                slip=account["slippage"], commission=account["commission"]
            )
        else:
            open_close_cf = None
    complete = open_close_cf is not None
    nav = account["cash"] + core_mv + float(open_close_cf) if complete else None
    option_pnl = account["option_cashflows"] + float(open_close_cf) if complete else None
    recon = nav - (INITIAL_NAV + core_pnl + option_pnl) if complete else None
    row = {
        "date": session_day,
        "account_id": account["account_id"],
        "strategy_id": account["strategy_id"],
        "risk_fraction": account["risk_fraction"],
        "cost_case": account["cost_case"],
        "qqq_close": round(spot, 4),
        "qqq_core_shares": account["shares"],
        "cash_usd": round(account["cash"], 2),
        "core_market_value_usd": round(core_mv, 2),
        "core_pnl_usd": round(core_pnl, 2),
        "realized_option_cashflows_usd": round(account["option_cashflows"], 2),
        "open_position_liquidation_cf_usd": round(float(open_close_cf), 2) if complete else None,
        "option_pnl_at_liquidation_mark_usd": round(option_pnl, 2) if complete else None,
        "nav_usd": round(float(nav), 2) if complete else None,
        "mark_complete": complete,
        "reconciliation_error_usd": round(float(recon), 8) if complete else None,
        "open_units": int(active["units"]) if active is not None else 0,
        "open_terminal_tail_reserve_usd": round(float(active["reserved_terminal_tail_loss_usd"]), 2) if active is not None else 0.0,
        "open_exit_censored": bool(active.get("exit_censored")) if active is not None else False,
        "cash_below_zero": account["cash"] < -0.01,
    }
    if complete:
        account["max_abs_reconciliation_error_usd"] = max(
            account["max_abs_reconciliation_error_usd"], abs(float(recon))
        )
    else:
        account["missing_nav_marks"] += 1
    if account["cash"] < -0.01:
        account["negative_cash_marks"] += 1
    account["daily"].append(row)
    account["previous_nav"] = float(nav) if complete and nav is not None and nav > 0 else None
    return row


def summarize_account(account: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    daily = account["daily"]
    valid = [r for r in daily if r["mark_complete"] and r["nav_usd"] is not None]
    navs = [float(r["nav_usd"]) for r in valid]
    maxdd = None
    if navs:
        peak = navs[0]
        dd = 0.0
        for value in navs:
            peak = max(peak, value)
            if peak > 0:
                dd = min(dd, value / peak - 1.0)
        maxdd = 100.0 * dd
    daily_returns = []
    for i in range(1, len(daily)):
        a, b = daily[i-1], daily[i]
        if a["mark_complete"] and b["mark_complete"] and a["nav_usd"] and a["nav_usd"] > 0:
            daily_returns.append((b["date"], float(b["nav_usd"]) / float(a["nav_usd"]) - 1.0))
    worst_day = min((r[1] for r in daily_returns), default=None)

    annual = []
    for year in sorted({r["date"][:4] for r in daily}):
        same_year = [r for r in valid if r["date"][:4] == year]
        if not same_year:
            continue
        year_end = same_year[-1]
        before = [r for r in valid if r["date"] < f"{year}-01-01"]
        start_nav = float(before[-1]["nav_usd"]) if before else INITIAL_NAV
        if start_nav > 0:
            annual.append({
                "account_id": account["account_id"], "strategy_id": account["strategy_id"],
                "risk_fraction": account["risk_fraction"], "cost_case": account["cost_case"],
                "year": int(year), "year_start_nav_usd": round(start_nav, 2),
                "year_end_nav_usd": year_end["nav_usd"],
                "observed_return_pct": round(100 * (float(year_end["nav_usd"]) / start_nav - 1.0), 4),
                "year_end_mark_complete": True,
            })
    final_row = daily[-1] if daily else {}
    final_nav = final_row.get("nav_usd") if final_row.get("mark_complete") else None
    first_day = date.fromisoformat(daily[0]["date"]) if daily else None
    last_day = date.fromisoformat(daily[-1]["date"]) if daily else None
    years = max((last_day-first_day).days/365.25, 1/365.25) if first_day and last_day else None
    cagr = ((float(final_nav)/INITIAL_NAV)**(1/years)-1)*100 if final_nav and final_nav > 0 and years else None
    summary = {
        "account_id": account["account_id"],
        "strategy_id": account["strategy_id"],
        "risk_fraction": account["risk_fraction"],
        "cost_case": account["cost_case"],
        "initial_nav_usd": INITIAL_NAV,
        "date_start": daily[0]["date"] if daily else None,
        "date_end": daily[-1]["date"] if daily else None,
        "final_nav_usd": round(float(final_nav), 2) if final_nav is not None else None,
        "total_return_pct": round(100*(float(final_nav)/INITIAL_NAV-1),4) if final_nav is not None else None,
        "cagr_pct": round(cagr, 4) if cagr is not None else None,
        "maxdd_observed_quote_side_marks_pct": round(maxdd, 4) if maxdd is not None else None,
        "worst_observed_daily_return_pct": round(worst_day*100, 4) if worst_day is not None else None,
        "worst_observed_calendar_year_pct": min((x["observed_return_pct"] for x in annual), default=None),
        "complete_nav_marks": len(valid),
        "missing_or_incomplete_nav_marks": account["missing_nav_marks"],
        "entries": account["entries"],
        "exits": account["exits"],
        "blocked_entries": account["blocked_entries"],
        "unresolved_exits": account["unresolved_exits"],
        "open_units_at_end": int(account["active"]["units"]) if account["active"] is not None else 0,
        "open_exit_censored_at_end": bool(account["active"].get("exit_censored")) if account["active"] is not None else False,
        "negative_cash_marks": account["negative_cash_marks"],
        "max_abs_nav_reconciliation_error_usd": round(account["max_abs_reconciliation_error_usd"], 8),
        "metric_quality": "DAILY_SIDE_QUOTE_LIQUIDATION_MARKS; missing held-leg marks left unknown; MaxDD may understate loss",
        "nav_accounting": "initial NAV + QQQ core PnL + option cashflows + open side-quote liquidation value",
    }
    return summary, annual


def write_gzip_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_bytes(b"")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row.keys()))
    with gzip.open(path, "wt", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_report(summary: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    base_only = next(r for r in summary if r["strategy_id"] == "CORE_ONLY")
    lines = [
        "# QQQ Event-Driven Risk-Budget Account Replay V1", "",
        "**Status: research only. No broker orders, no HUB execution, and no Frozen Original Hybrid policy change.**", "",
        f"- Run ID: {manifest.get('run_id') or 'CLI_NOT_GITHUB_ACTIONS'}; tested SHA: {manifest.get('tested_sha') or 'UNSET'}."
        f"- Source window: {manifest['source_window'][0]} to {manifest['source_window'][1]}; {manifest['source_sessions']} sessions and {manifest['signal_count']} event signals.",
        f"- Starting NAV: USD {INITIAL_NAV:,.0f}; fixed QQQ Core shares initially funded with {CORE_WEIGHT:.0%} of NAV; no dividends or rebalancing.",
        "- Every option account is independently sized from the prior complete NAV at a 0.5%, 1%, or 2% terminal-tail budget. Units are capped by displayed entry-side depth and conservative free-cash/reserve arithmetic.",
        "- Exit signal is after 10 observed sessions; exact-ID close can defer up to 3 observed sessions. Missing/invalid quotes and insufficient displayed size are not forward-filled.",
        "", "## Account results", "",
        "| Strategy | Tail budget | Costs | Final NAV USD | CAGR % | Observed MaxDD % | Worst year % | Entries | Exits | Blocked entries | Incomplete marks | NAV recon max USD |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary:
        budget = "—" if r["risk_fraction"] is None else f"{100*r['risk_fraction']:.1f}%"
        lines.append(
            f"| {r['strategy_id']} | {budget} | {r['cost_case']} | {r['final_nav_usd']} | {r['cagr_pct']} | "
            f"{r['maxdd_observed_quote_side_marks_pct']} | {r['worst_observed_calendar_year_pct']} | {r['entries']} | "
            f"{r['exits']} | {r['blocked_entries']} | {r['missing_or_incomplete_nav_marks']} | {r['max_abs_nav_reconciliation_error_usd']} |"
        )
    lines += [
        "", "## Decision limits", "",
        "- Risk sizing uses expiry-intrinsic payoff knots, not broker margin models. It cannot cap interim mark-to-market losses, assignment, forced liquidation, early exercise, or multi-leg fill risk.",
        "- Free cash reserved for short-heavy structures is a conservative research proxy, not a claim about actual broker margin.",
        "- MaxDD and CAGR are based on complete daily side-quote liquidation marks; missing marks stay missing and can understate drawdown.",
        "- QQQ Core is price-only, fixed shares funded to 42% of initial NAV; dividends are not included.",
        "- This is a historical screen using options quotes through 2025-12-15. It is not an untouched out-of-sample test and no result authorizes live deployment.",
        "",
    ]
    return "\n".join(lines)


def run(out_dir: Path) -> dict[str, Any]:
    cache = ROOT / ".cache" / "qqq-options-full-history"
    integrity, universe_by_day, spots, expected = core.audit.build_inputs(cache)
    expected = sorted(d for d in expected if START_DATE <= d <= SOURCE_END_DATE)
    if not expected:
        raise RuntimeError("No source-aligned QQQ/VIX sessions.")
    if expected[-1] != SOURCE_END_DATE:
        raise ValueError(f"Expected source-aligned QQQ/VIX end {SOURCE_END_DATE}, got {expected[-1]}")
    for d in expected:
        if num((spots.get(d) or {}).get("raw_close")) is None:
            raise ValueError(f"Missing raw QQQ close prevents NAV replay: {d}")
    signal_days = core.build_signals(expected, spots, universe_by_day)
    signal_set = set(signal_days)
    option_paths, file_integrity = [], {}
    for spec in core.audit.ANNUAL_FILES:
        path, meta = core.audit.download_verified(spec, cache)
        option_paths.append(path)
        file_integrity[spec["name"]] = meta
    first_spot = float(spots[expected[0]]["raw_close"])
    shares = math.floor(INITIAL_NAV * CORE_WEIGHT / first_spot)

    accounts: list[dict[str, Any]] = [init_account("CORE_ONLY", None, "NONE", shares, first_spot)]
    for strategy in STRATEGIES:
        for risk_fraction in RISK_BUDGETS:
            for cost_case in COST_CASES:
                accounts.append(init_account(strategy, risk_fraction, cost_case, shares, first_spot))
    for account in accounts:
        account["_session_count"] = len(expected)

    chain_iter = iter(core.source_replay.iter_qqq_chain_days(option_paths))
    next_chain = next(chain_iter, None)
    pending: dict[str, Any] | None = None
    last_chain_day = None
    all_daily: list[dict[str, Any]] = []
    all_trades: list[dict[str, Any]] = []
    for idx, session_day in enumerate(expected):
        while next_chain is not None and next_chain[0] < session_day:
            next_chain = next(chain_iter, None)
        if next_chain is not None and next_chain[0] == session_day:
            rows = next_chain[1]
            last_chain_day = session_day
            next_chain = next(chain_iter, None)
        else:
            rows = []
        qmap = core.chain_map(rows)
        spot = float((spots.get(session_day) or {})["raw_close"])

        # Close risk only using exact IDs, side-correct quotes and displayed depth.
        close_due_positions(accounts, qmap, session_day, idx)

        # Signal at EOD t; candidate contracts can only enter on the next observed session.
        if pending is not None and idx == pending["entry_idx"]:
            attempt_entries(accounts, pending["candidates"], pending["candidate_status"],
                            qmap, session_day, idx)
            pending = None

        for account in accounts:
            row = daily_mark(account, session_day, spot, first_spot, qmap)
            all_daily.append(row)

        if session_day in signal_set:
            spot_sig = num((spots.get(session_day) or {}).get("raw_close"))
            if spot_sig is None or not rows:
                pending = {
                    "signal_day": session_day, "entry_idx": idx + 1,
                    "candidates": {}, "candidate_status": {s: "SIGNAL_NO_SPOT_OR_CHAIN" for s in STRATEGIES},
                }
            else:
                candidates, statuses = core.build_candidates(rows, session_day, float(spot_sig))
                candidates = {
                    name: {**spec, "signal_date": session_day}
                    for name, spec in candidates.items() if name in STRATEGIES
                }
                pending = {
                    "signal_day": session_day, "entry_idx": idx + 1,
                    "candidates": candidates, "candidate_status": statuses,
                }

    for account in accounts:
        pos = account["active"]
        if pos is not None and not any(
            t.get("event") == "EXIT_UNRESOLVED" and t.get("signal_date") == pos["signal_date"]
            for t in account["trades"]
        ):
            account["unresolved_exits"] += 1
            account["trades"].append({
                "account_id": account["account_id"], "strategy_id": account["strategy_id"],
                "risk_fraction": account["risk_fraction"], "cost_case": account["cost_case"],
                "signal_date": pos["signal_date"], "entry_date": pos["entry_date"],
                "event": "END_OF_SOURCE_OPEN", "status": "UNRESOLVED_END_OF_SOURCE",
                "units": pos["units"], "reserved_terminal_tail_loss_usd": pos["reserved_terminal_tail_loss_usd"],
                "contract_legs": json.dumps(pos["legs"], separators=(",", ":")),
            })
        all_trades.extend(account["trades"])

    if last_chain_day != SOURCE_END_DATE:
        raise ValueError(f"Option source terminal date mismatch: {last_chain_day} != {SOURCE_END_DATE}")

    summary, annual = [], []
    for account in accounts:
        row, annual_rows = summarize_account(account)
        summary.append(row)
        annual.extend(annual_rows)
    max_recon = max((r["max_abs_nav_reconciliation_error_usd"] for r in summary if r["max_abs_nav_reconciliation_error_usd"] is not None), default=0.0)
    if max_recon >= 0.01:
        raise AssertionError(f"NAV attribution reconciliation failed: {max_recon}")

    daily_by_date = len(expected)
    manifest = {
        "research_id": "QQQ_EVENT_RISK_BUDGET_PORTFOLIO_REPLAY_V1",
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "tested_sha": os.environ.get("GITHUB_SHA"),
        "source_window": [expected[0], expected[-1]],
        "source_sessions": len(expected),
        "signal_count": len(signal_days),
        "initial_nav_usd": INITIAL_NAV,
        "qqq_core_initial_weight": CORE_WEIGHT,
        "risk_budgets": list(RISK_BUDGETS),
        "cost_cases": {k: {"slippage_per_share_per_leg_side_usd": v[0], "commission_per_contract_per_side_usd": v[1]} for k,v in COST_CASES.items()},
        "account_count": len(accounts),
        "daily_account_marks": len(all_daily),
        "trade_ledger_rows": len(all_trades),
        "options_source_files": file_integrity,
        "underlying_and_repo_source_integrity": integrity,
        "source_option_terminal_date": last_chain_day,
        "pricing_evidence": "OBSERVED_EOD_QUOTES_WITH_DERIVED_SIDE_PRICE_EXECUTION_MODEL_NOT_CONFIRMED_FILLS",
        "max_abs_nav_reconciliation_error_usd": max_recon,
        "metrics": "DAILY_SIDE_QUOTE_LIQUIDATION_MARKS; no forward fill; absent displayed depth means incomplete NAV mark",
        "limitations": [
            "No broker margin, assignment, early exercise, forced liquidation, or multi-leg fill sequencing model.",
            "Cash reserve for credit structures is a conservative proxy based on modeled terminal loss, not broker margin.",
            "Terminal payoff loss does not bound interim mark-to-market loss.",
            "Historical option chain ends 2025-12-15 and the signal/structure screen is exploratory, not virgin OOS.",
            "QQQ core is fixed shares, raw price-only, no dividends and no rebalancing.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "REPORT.md").write_text(render_report(summary, manifest), encoding="utf-8")
    write_csv(out_dir / "summary.csv", summary)
    write_csv(out_dir / "annual_returns.csv", annual)
    write_csv(out_dir / "trade_ledger.csv", all_trades)
    write_gzip_csv(out_dir / "daily_nav.csv.gz", all_daily)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({
        "research_id": result["research_id"],
        "source_window": result["source_window"],
        "source_sessions": result["source_sessions"],
        "signal_count": result["signal_count"],
        "account_count": result["account_count"],
        "daily_account_marks": result["daily_account_marks"],
        "trade_ledger_rows": result["trade_ledger_rows"],
        "max_abs_nav_reconciliation_error_usd": result["max_abs_nav_reconciliation_error_usd"],
        "output_dir": str(args.out),
    }, indent=2))


if __name__ == "__main__":
    main()
