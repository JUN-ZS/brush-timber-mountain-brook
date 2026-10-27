#!/usr/bin/env python3
"""Pair the frozen QQQ/SPY PUT and CALL 1:6 ledgers, with a QQQ-share overlay.

Only cohorts with the same signal date, expiry, and actual entry date form a basket.
One basket may be active at a time; an unresolved leg reserves the slot through source end.
The stock overlay is a buy-and-hold total-return proxy, not a broker-account simulation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = Path("research/qqq_spy_call_fixed_ratio_size_gated_v1")
CALL_ROOT = BASE / "results/dte_hold_exit_factorial_call_v1"
PUT_ROOT = Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte_hold_exit_factorial_v1")
OUT = CALL_ROOT / "put_call_stock_overlay_v1"
UNIVERSE = Path("src/data/universe.json")
START = "2018-03-01"
END = "2025-12-15"
DTE_TARGETS = (20, 30, 45, 60)
PHASES = (0, 2, 4, 6, 8)
POLICY = "HOLD_20_OR_DTE_LE_7"
YEARS = (date.fromisoformat(END) - date.fromisoformat(START)).days / 365.25
DEFAULT_STOCK_VALUE_USD = 63694.0
# Public market close used only to translate the stated current position value into
# an approximate share count; historical return path comes from the HUB series.
DEFAULT_CURRENT_QQQ_PRICE_USD = 712.20
DEFAULT_CURRENT_QQQ_PRICE_DATE = "2026-10-26"
CURRENT_QQQ_PRICE_SOURCE = "StockAnalysis QQQ history, close on 2026-10-26"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def resolved(row: dict) -> bool:
    return str(row.get("status", "")).upper() == "RESOLVED" and number(row.get("net_pnl_usd")) is not None


def strict_pair_key(row: dict):
    """Exact basket identity: common signal, same expiry, and same actual entry date."""
    signal, expiry, entry = (str(row.get(k) or "") for k in ("signal_date", "expiry", "entry_date"))
    if not signal or not expiry or not entry:
        return None
    return (signal, expiry, entry)


def pair_trade_rows(put_rows: list[dict], call_rows: list[dict]):
    """Strictly pair two leg ledgers and report attrition at every matching stage."""
    put_rows = [r for r in put_rows if r.get("entry_date") and r.get("signal_date")]
    call_rows = [r for r in call_rows if r.get("entry_date") and r.get("signal_date")]
    p_by_signal = {str(r["signal_date"]): r for r in put_rows}
    c_by_signal = {str(r["signal_date"]): r for r in call_rows}
    common_signals = set(p_by_signal) & set(c_by_signal)
    same_expiry = {
        s for s in common_signals
        if str(p_by_signal[s].get("expiry") or "") == str(c_by_signal[s].get("expiry") or "")
    }
    same_entry = {
        s for s in same_expiry
        if str(p_by_signal[s].get("entry_date") or "") == str(c_by_signal[s].get("entry_date") or "")
    }

    p_by_key = {strict_pair_key(r): r for r in put_rows if strict_pair_key(r)}
    c_by_key = {strict_pair_key(r): r for r in call_rows if strict_pair_key(r)}
    keys = sorted(set(p_by_key) & set(c_by_key),
                  key=lambda k: (int(float(p_by_key[k].get("signal_index") or 0)),
                                 int(float(p_by_key[k].get("entry_index") or 0)), k))
    pairs = []
    for key in keys:
        p, c = p_by_key[key], c_by_key[key]
        p_ok, c_ok = resolved(p), resolved(c)
        full_pnl = float(p["net_pnl_usd"]) + float(c["net_pnl_usd"]) if p_ok and c_ok else None
        realized_legs = (float(p["net_pnl_usd"]) if p_ok else 0.0) + (float(c["net_pnl_usd"]) if c_ok else 0.0)
        pairs.append({
            "signal_date": key[0], "expiry": key[1], "entry_date": key[2],
            "signal_index": int(float(p.get("signal_index") or c.get("signal_index") or 0)),
            "entry_index": int(float(p.get("entry_index") or c.get("entry_index") or 0)),
            "put_status": p.get("status"), "call_status": c.get("status"),
            "put_exit_date": p.get("exit_date") or "", "call_exit_date": c.get("exit_date") or "",
            "put_exit_index": p.get("exit_index") or "", "call_exit_index": c.get("exit_index") or "",
            "put_exit_reason": p.get("exit_reason") or "", "call_exit_reason": c.get("exit_reason") or "",
            "put_net_pnl_usd": number(p.get("net_pnl_usd")),
            "call_net_pnl_usd": number(c.get("net_pnl_usd")),
            "both_resolved": bool(p_ok and c_ok),
            "completed_pair_net_pnl_usd": full_pnl,
            "realized_option_legs_pnl_usd": realized_legs,
            "_put": p, "_call": c,
        })
    diag = {
        "put_entered_cohorts": len(put_rows),
        "call_entered_cohorts": len(call_rows),
        "common_signal_dates": len(common_signals),
        "same_expiry_signal_dates": len(same_expiry),
        "same_entry_date_signal_dates": len(same_entry),
        "strict_matched_pairs": len(pairs),
        "put_only_signal_dates": len(set(p_by_signal) - set(c_by_signal)),
        "call_only_signal_dates": len(set(c_by_signal) - set(p_by_signal)),
    }
    return pairs, diag


def pair_release_index(pair: dict, source_sessions: int) -> int:
    """A paired slot releases only after both legs close; unresolved pairs hold to source end."""
    if not pair["both_resolved"]:
        return source_sessions + 1
    indices = [number(pair.get("put_exit_index")), number(pair.get("call_exit_index"))]
    if any(i is None for i in indices):
        return source_sessions + 1
    return int(max(indices))


def gate_pairs(pairs: list[dict], cap: int, source_sessions: int):
    """Chronological admission gate with same-session releases processed before new signals."""
    selected, blocked = [], []
    ordered = sorted(pairs, key=lambda p: (int(p["signal_index"]), int(p["entry_index"]), p["signal_date"]))
    for pair in ordered:
        active = [s for s in selected if pair_release_index(s, source_sessions) > int(pair["signal_index"])]
        if len(active) < cap:
            selected.append(pair)
        else:
            blocked.append(pair)
    return selected, blocked


def calculate_stock_scenarios(universe: dict, raw_start_close: float, notional: float,
                              current_price: float, current_price_date: str):
    dates, adjusted = universe["dates"], universe["c"]["QQQ"]
    if len(dates) != len(adjusted):
        raise RuntimeError("HUB QQQ date and adjusted-close arrays do not align")
    try:
        i0, i1 = dates.index(START), dates.index(END)
    except ValueError as exc:
        raise RuntimeError(f"HUB QQQ adjusted-close series missing {START} or {END}") from exc
    p0, p1 = float(adjusted[i0]), float(adjusted[i1])
    if min(p0, p1, raw_start_close, current_price) <= 0:
        raise RuntimeError("invalid QQQ price in stock overlay")
    total_return_factor = p1 / p0
    current_shares = notional / current_price
    historical_start_value = current_shares * raw_start_close
    current_position_end_total_return_value = historical_start_value * total_return_factor
    initial_shares = notional / raw_start_close
    initial_investment_end_value = notional * total_return_factor
    return {
        "hub_source": universe.get("source"),
        "hub_asof": universe.get("asof"),
        "stock_start_date": START,
        "stock_end_date": END,
        "qqq_raw_start_close_usd": raw_start_close,
        "qqq_hub_adjusted_close_start": p0,
        "qqq_hub_adjusted_close_end": p1,
        "qqq_total_return_factor": total_return_factor,
        "period_return_pct": (total_return_factor - 1) * 100,
        "current_position_value_usd": notional,
        "current_price_reference_usd": current_price,
        "current_price_reference_date": current_price_date,
        "current_price_reference_source": CURRENT_QQQ_PRICE_SOURCE,
        "implied_current_shares": current_shares,
        "current_position_historical_start_value_usd": historical_start_value,
        "current_position_historical_end_total_return_value_usd": current_position_end_total_return_value,
        "current_position_historical_total_return_pnl_usd": current_position_end_total_return_value - historical_start_value,
        "historical_initial_investment_usd": notional,
        "historical_initial_shares_at_start_close": initial_shares,
        "historical_initial_investment_end_total_return_value_usd": initial_investment_end_value,
        "historical_initial_investment_total_return_pnl_usd": initial_investment_end_value - notional,
        "position_value_note": "HUB c.QQQ is adjusted close; return factor approximates total return with distributions reinvested. Current shares are estimated from the stated current value divided by the 2026-10-26 closing price.",
    }


def stock_drawdown_pct(universe: dict) -> float:
    dates, values = universe["dates"], universe["c"]["QQQ"]
    start = dates.index(START)
    end = dates.index(END)
    series = [float(x) for x in values[start:end + 1]]
    peak, worst = series[0], 0.0
    for value in series:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1)
    return worst * 100


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row if not k.startswith("_")))
    if not fields:
        fields = ["status"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def generate(stock_value: float, current_price: float, current_price_date: str):
    universe = read_json(UNIVERSE)
    start_entries = read_csv(CALL_ROOT / "dte_45/phase_0/entry_cohort.csv")
    start_quotes = [r for r in start_entries if r.get("signal_date") == START and number(r.get("qqq_spot_signal"))]
    if not start_quotes:
        raise RuntimeError("could not establish raw QQQ start close from source-pinned entry cohort")
    raw_start_close = float(start_quotes[0]["qqq_spot_signal"])
    stock = calculate_stock_scenarios(universe, raw_start_close, stock_value, current_price, current_price_date)
    stock["stock_only_max_drawdown_pct"] = stock_drawdown_pct(universe)
    phase_rows, selected_pairs = [], []
    config_accum = defaultdict(list)

    for dte in DTE_TARGETS:
        for phase in PHASES:
            cdir = CALL_ROOT / f"dte_{dte}/phase_{phase}"
            pdir = PUT_ROOT / f"dte_{dte}/phase_{phase}"
            put_rows = [r for r in read_csv(pdir / "trade_episodes.csv") if r.get("policy") == POLICY]
            call_rows = [r for r in read_csv(cdir / "trade_episodes.csv") if r.get("policy") == POLICY]
            pairs, diag = pair_trade_rows(put_rows, call_rows)
            csummary = read_json(cdir / "summary.json")
            psummary = read_json(pdir / "summary.json")
            source_sessions = int(psummary.get("coverage", {}).get("common_underlying_sessions")
                                  or csummary.get("coverage", {}).get("common_underlying_sessions") or 0)
            if source_sessions <= 0:
                raise RuntimeError(f"missing source session count for DTE{dte} phase {phase}")
            admitted, blocked = gate_pairs(pairs, cap=1, source_sessions=source_sessions)
            complete = [r for r in admitted if r["both_resolved"]]
            completed_pair_pnl = sum(float(r["completed_pair_net_pnl_usd"]) for r in complete)
            resolved_leg_pnl = sum(float(r["realized_option_legs_pnl_usd"]) for r in admitted)
            unresolved_pair_n = len(admitted) - len(complete)
            leg_unresolved_n = sum(1 for r in admitted if not resolved(r["_put"])) + sum(1 for r in admitted if not resolved(r["_call"]))
            worst_pair = min((float(r["completed_pair_net_pnl_usd"]) for r in complete), default=None)
            phase_result = {
                "dte_target": dte, "phase_sessions": phase, "policy": POLICY,
                **diag,
                "max_active_paired_sets": 1,
                "admitted_paired_sets": len(admitted),
                "skipped_matched_pairs_capacity": len(blocked),
                "complete_resolved_pairs": len(complete),
                "incomplete_unresolved_pairs": unresolved_pair_n,
                "unresolved_option_legs": leg_unresolved_n,
                "completed_pair_net_pnl_usd": round(completed_pair_pnl, 2),
                "completed_pair_annual_additive_pnl_usd": round(completed_pair_pnl / YEARS, 2),
                "resolved_option_legs_pnl_usd": round(resolved_leg_pnl, 2),
                "resolved_option_legs_annual_additive_pnl_usd": round(resolved_leg_pnl / YEARS, 2),
                "worst_completed_paired_trade_usd": round(worst_pair, 2) if worst_pair is not None else None,
                "stock_pnl_current_position_value_basis_usd": round(stock["current_position_historical_total_return_pnl_usd"], 2),
                "stock_plus_completed_pair_pnl_current_position_basis_usd": round(
                    stock["current_position_historical_total_return_pnl_usd"] + completed_pair_pnl, 2),
                "stock_plus_resolved_legs_pnl_current_position_basis_usd": round(
                    stock["current_position_historical_total_return_pnl_usd"] + resolved_leg_pnl, 2),
                "stock_pnl_initial_63694_at_start_basis_usd": round(stock["historical_initial_investment_total_return_pnl_usd"], 2),
                "stock_plus_completed_pair_pnl_initial_63694_at_start_basis_usd": round(
                    stock["historical_initial_investment_total_return_pnl_usd"] + completed_pair_pnl, 2),
                "annualization_years": round(YEARS, 4),
                "stock_end_value_current_position_basis_usd": round(stock["current_position_historical_end_total_return_value_usd"], 2),
            }
            phase_rows.append(phase_result)
            config_accum[dte].append(phase_result)
            for r in admitted:
                selected_pairs.append({
                    "dte_target": dte, "phase_sessions": phase, "policy": POLICY,
                    "signal_date": r["signal_date"], "expiry": r["expiry"], "entry_date": r["entry_date"],
                    "signal_index": r["signal_index"], "entry_index": r["entry_index"],
                    "put_status": r["put_status"], "call_status": r["call_status"],
                    "put_exit_date": r["put_exit_date"], "call_exit_date": r["call_exit_date"],
                    "put_exit_index": r["put_exit_index"], "call_exit_index": r["call_exit_index"],
                    "put_exit_reason": r["put_exit_reason"], "call_exit_reason": r["call_exit_reason"],
                    "put_net_pnl_usd": r["put_net_pnl_usd"], "call_net_pnl_usd": r["call_net_pnl_usd"],
                    "both_resolved": r["both_resolved"],
                    "completed_pair_net_pnl_usd": r["completed_pair_net_pnl_usd"],
                    "realized_option_legs_pnl_usd": r["realized_option_legs_pnl_usd"],
                })

    config_rows = []
    for dte, rows in config_accum.items():
        def med(key):
            values = [float(r[key]) for r in rows if r.get(key) not in (None, "")]
            return statistics.median(values) if values else None
        completed_annual = [float(r["completed_pair_annual_additive_pnl_usd"]) for r in rows]
        resolved_leg_annual = [float(r["resolved_option_legs_annual_additive_pnl_usd"]) for r in rows]
        current_combined = [float(r["stock_plus_resolved_legs_pnl_current_position_basis_usd"]) for r in rows]
        initial_combined = [float(r["stock_plus_resolved_legs_pnl_current_position_basis_usd"])
                            for r in rows]
        config_rows.append({
            "dte_target": dte, "policy": POLICY, "max_active_paired_sets": 1, "phase_count": len(rows),
            "median_completed_pair_annual_additive_pnl_usd": round(statistics.median(completed_annual), 2),
            "min_phase_completed_pair_annual_additive_pnl_usd": round(min(completed_annual), 2),
            "max_phase_completed_pair_annual_additive_pnl_usd": round(max(completed_annual), 2),
            "median_resolved_option_legs_annual_additive_pnl_usd": round(statistics.median(resolved_leg_annual), 2),
            "median_admitted_paired_sets": med("admitted_paired_sets"),
            "median_skipped_matched_pairs_capacity": med("skipped_matched_pairs_capacity"),
            "median_strict_matched_pairs": med("strict_matched_pairs"),
            "median_unresolved_option_legs": med("unresolved_option_legs"),
            "worst_completed_pair_across_phases_usd": min(
                [float(r["worst_completed_paired_trade_usd"]) for r in rows
                 if r.get("worst_completed_paired_trade_usd") not in (None, "")], default=None),
            "median_stock_plus_completed_pair_pnl_current_position_basis_usd": round(statistics.median(
                float(r["stock_plus_completed_pair_pnl_current_position_basis_usd"]) for r in rows), 2),
            "min_phase_stock_plus_completed_pair_pnl_current_position_basis_usd": round(min(
                float(r["stock_plus_completed_pair_pnl_current_position_basis_usd"]) for r in rows), 2),
            "max_phase_stock_plus_completed_pair_pnl_current_position_basis_usd": round(max(
                float(r["stock_plus_completed_pair_pnl_current_position_basis_usd"]) for r in rows), 2),
            "median_stock_plus_resolved_legs_pnl_current_position_basis_usd": round(statistics.median(current_combined), 2),
            "median_stock_plus_resolved_legs_pnl_initial_63694_at_start_basis_usd": round(statistics.median(
                float(r["stock_plus_resolved_legs_pnl_current_position_basis_usd"]) +
                stock["historical_initial_investment_total_return_pnl_usd"] -
                stock["current_position_historical_total_return_pnl_usd"] for r in rows), 2),
            "stock_only_total_return_pnl_current_position_basis_usd": round(
                stock["current_position_historical_total_return_pnl_usd"], 2),
            "stock_only_total_return_pnl_if_63694_invested_at_start_usd": round(
                stock["historical_initial_investment_total_return_pnl_usd"], 2),
        })

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "put_call_stock_overlay_by_phase.csv", phase_rows)
    write_csv(OUT / "put_call_stock_overlay_config_summary.csv", config_rows)
    write_csv(OUT / "put_call_stock_overlay_selected_pairs.csv", selected_pairs)
    (OUT / "QQQ_STOCK_OVERLAY_REPORT.md").write_text(
        render_report(stock, config_rows, phase_rows), encoding="utf-8"
    )
    print(f"PAIR_STOCK OVERLAY AUDIT PASS: phase_rows={len(phase_rows)} config_rows={len(config_rows)} selected_pairs={len(selected_pairs)}")
    print((OUT / "QQQ_STOCK_OVERLAY_REPORT.md").read_text(encoding="utf-8")[:14000])


def render_report(stock: dict, configs: list[dict], phases: list[dict]) -> str:
    lines = [
        "# PUT + CALL paired replay with a QQQ-stock overlay", "",
        f"- Option replay window: {START} to {END} ({YEARS:.3f} calendar years).",
        f"- Options: QQQ LONG PUT 1 : SPY SHORT PUT 6 at target abs-Delta 0.25; QQQ LONG CALL 1 : SPY SHORT CALL 6 at target abs-Delta 0.20.",
        f"- Both option baskets use same-expiry legs internally; PUT and CALL baskets are paired only when signal date, expiry, and actual entry date all match.",
        f"- Exit policy: {POLICY}; a basket reserves one combined slot until both option trades resolve. At most one paired basket is active; unresolved baskets reserve the slot through source end.",
        "- Unmatched PUT-only or CALL-only entries are skipped as a pair. No independent annual medians are added.",
        "- Option trade P&L is the existing source-pinned quote-side estimate after the study's fixed slippage and commissions; unresolved option-leg P&L is not marked.",
        f"- HUB QQQ history: {stock['hub_source']}, as-of {stock['hub_asof']}; adjusted-close ratio is used as a total-return proxy.",
        f"- Current value input: USD {stock['current_position_value_usd']:,.2f}; current reference price USD {stock['current_price_reference_usd']:,.2f} ({stock['current_price_reference_date']}; {stock['current_price_reference_source']}); implied shares approx. {stock['implied_current_shares']:,.4f}.",
        f"- Historical stock position under that current-value basis: estimated start value USD {stock['current_position_historical_start_value_usd']:,.2f}; end total-return wealth USD {stock['current_position_historical_end_total_return_value_usd']:,.2f}; stock total-return P&L USD {stock['current_position_historical_total_return_pnl_usd']:,.2f} ({stock['period_return_pct']:.2f}% on starting value).",
        f"- Alternative interpretation: investing USD {stock['historical_initial_investment_usd']:,.2f} on {START} and holding through {END} gives estimated stock total-return P&L USD {stock['historical_initial_investment_total_return_pnl_usd']:,.2f}. This is not the same as a current holding worth USD 63,694.",
        f"- QQQ stock-only max drawdown in the study window, based on the HUB adjusted-close series: {stock['stock_only_max_drawdown_pct']:.2f}%. This is not the combined portfolio drawdown.",
        "",
        "## DTE summary (phase aggregation)", "",
        "| DTE target | Median annual P&L of completed paired option sets | Phase range | Median stock + completed-pair P&L (current-value share basis) | Median stock + resolved option-leg P&L (current-value share basis) | Median admitted sets | Median matched pairs skipped by capacity | Median unresolved option legs | Worst completed pair across phases |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in configs:
        worst = r["worst_completed_pair_across_phases_usd"]
        worst_text = "n/a" if worst is None else f"{float(worst):,.2f}"
        lines.append(
            f"| {r['dte_target']} | {r['median_completed_pair_annual_additive_pnl_usd']:,.2f} | "
            f"{r['min_phase_completed_pair_annual_additive_pnl_usd']:,.2f}–{r['max_phase_completed_pair_annual_additive_pnl_usd']:,.2f} | "
            f"{r['median_stock_plus_completed_pair_pnl_current_position_basis_usd']:,.2f} | "
            f"{r['median_stock_plus_resolved_legs_pnl_current_position_basis_usd']:,.2f} | "
            f"{r['median_admitted_paired_sets']:,.1f} | {r['median_skipped_matched_pairs_capacity']:,.1f} | "
            f"{r['median_unresolved_option_legs']:,.1f} | {worst_text} |"
        )
    lines += [
        "", "## All phase results", "",
        "| DTE | Phase | Matched pairs | Admitted pairs | Capacity skipped | Fully resolved pairs | Unresolved pairs | Pair net P&L (completed only) | Realized option-leg P&L (unresolved legs excluded) | Stock P&L (current-value share basis) | Stock + completed-pair P&L | Stock + resolved-leg P&L |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in phases:
        lines.append(
            f"| {r['dte_target']} | {r['phase_sessions']} | {r['strict_matched_pairs']} | {r['admitted_paired_sets']} | "
            f"{r['skipped_matched_pairs_capacity']} | {r['complete_resolved_pairs']} | {r['incomplete_unresolved_pairs']} | "
            f"{r['completed_pair_net_pnl_usd']:,.2f} | {r['resolved_option_legs_pnl_usd']:,.2f} | "
            f"{r['stock_pnl_current_position_value_basis_usd']:,.2f} | "
            f"{r['stock_plus_completed_pair_pnl_current_position_basis_usd']:,.2f} | "
            f"{r['stock_plus_resolved_legs_pnl_current_position_basis_usd']:,.2f} |"
        )
    lines += [
        "", "## Interpretation limits", "",
        "- These are additive USD outcomes, not CAGR, account return, or proof that $63,694 covers the options' buying-power requirements.",
        "- The share overlay uses a total-return adjusted-close ratio; it estimates dividends/distributions reinvested. The option legs use raw underlying close for contract selection and separate EOD bid/ask quotes.",
        "- The market price used to infer current share count is a dated reference, so the implied share count is approximate rather than a live account-position read.",
        "- A QQQ share holding is not contractual coverage for SPY short puts or SPY short calls. SPY assignment cash and short-call delivery obligations remain separate and unmodeled.",
        "- Unresolved option legs are excluded from resolved P&L and remain an uncertainty. A full combined max drawdown cannot be calculated from the trade ledger alone because it does not preserve the complete daily marked P&L for all open options.",
        "- Pair net P&L requires both PUT and CALL trades to resolve; the realized-option-leg column separately counts a leg that closed even if its paired leg remains unresolved. These two totals intentionally differ.",
        "- This is an isolated research artifact. No main merge and no broker orders.",
        "",
        "Files: put_call_stock_overlay_by_phase.csv, put_call_stock_overlay_config_summary.csv, put_call_stock_overlay_selected_pairs.csv.",
        "",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--qqq-stock-value-usd", type=float, default=DEFAULT_STOCK_VALUE_USD)
    p.add_argument("--current-qqq-price", type=float, default=DEFAULT_CURRENT_QQQ_PRICE_USD)
    p.add_argument("--current-price-date", default=DEFAULT_CURRENT_QQQ_PRICE_DATE)
    args = p.parse_args()
    if args.qqq_stock_value_usd <= 0 or args.current_qqq_price <= 0:
        raise SystemExit("stock value and QQQ reference price must be positive")
    generate(args.qqq_stock_value_usd, args.current_qqq_price, args.current_price_date)


if __name__ == "__main__":
    main()
