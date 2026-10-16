#!/usr/bin/env python3
"""Build a serial fixed-one-unit QQQ 1x5 quote-side portfolio equity path.

This is not an executable NAV-sized strategy. It keeps missing option marks null,
does not forward-fill, and marks the run research-only because EOD quotes are
not confirmed fills and broker margin/forced-liquidation is unavailable.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = ROOT / "research" / "qqq_put_ratio_lab_v1"
SOURCE_SCRIPT = ROOT / "research" / "qqq_put_ratio_exit_study_v1" / "qqq_put_ratio_exit_study_v1.py"
SLIPPAGE = 0.05
COMMISSION = 0.65
DD_LEVELS = (3, 5, 10, 15, 20, 25, 30)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("qqq_put_ratio_exit_study_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import replay source module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_session_dates(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    dates = [str(row.get("date", ""))[:10] for row in rows]
    dates = [d for d in dates if d]
    if dates != sorted(set(dates)):
        raise ValueError("Session dates must be unique and ascending")
    for value in dates:
        date.fromisoformat(value)
    return dates


def combine_episode_daily(session_dates: list[str], trade_results: list[dict[str, Any]]) -> list[float | None]:
    """Combine non-overlapping trade MTM paths into total account P&L.

    Values are cumulative portfolio P&L, not NAV. A no-position day is known flat
    at the last realized result. During a position, a missing leg/mark makes that
    day's portfolio value null; there is never forward filling. If an episode is
    unresolved, all later equity becomes unknown because available capital cannot
    be reconciled safely.
    """
    ordered = sorted(trade_results, key=lambda t: (str(t.get("entry_date", "")), int(t.get("trade_id", 0))))
    date_index = {d: i for i, d in enumerate(session_dates)}
    for trade in ordered:
        if trade.get("entry_date") not in date_index:
            raise ValueError(f"Entry date outside session calendar: {trade.get('entry_date')}")
        daily = trade.get("daily")
        if not isinstance(daily, list) or not daily:
            raise ValueError(f"Trade {trade.get('trade_id')} has no daily path")
        if daily[0].get("date") != trade.get("entry_date"):
            raise ValueError(f"Trade {trade.get('trade_id')} daily path does not start on entry")
        for row in daily:
            if row.get("date") not in date_index:
                raise ValueError(f"Trade path date outside session calendar: {row.get('date')}")
        if ordered.index(trade) > 0:
            previous = ordered[ordered.index(trade)-1]
            previous_last = previous.get("daily", [{}])[-1].get("date")
            if str(trade["entry_date"]) <= str(previous_last):
                raise ValueError("Episode paths overlap; serial equity replay would double-count exposure")

    daily_maps = [{str(row["date"]): row for row in trade["daily"]} for trade in ordered]
    curve: list[float | None] = []
    realized_pnl = 0.0
    unresolved_prior = False
    trade_idx = 0
    for session in session_dates:
        if unresolved_prior:
            curve.append(None)
            continue
        while trade_idx < len(ordered):
            trade = ordered[trade_idx]
            last_date = str(trade["daily"][-1]["date"])
            if session > last_date:
                final_pnl = trade.get("final_pnl_usd")
                if final_pnl is None:
                    unresolved_prior = True
                    break
                realized_pnl += float(final_pnl)
                trade_idx += 1
                continue
            break
        if unresolved_prior:
            curve.append(None)
            continue
        if trade_idx >= len(ordered):
            curve.append(round(realized_pnl, 2))
            continue
        trade = ordered[trade_idx]
        entry = str(trade["entry_date"])
        last_date = str(trade["daily"][-1]["date"])
        if session < entry or session > last_date:
            curve.append(round(realized_pnl, 2))
            continue
        mark = daily_maps[trade_idx].get(session)
        if mark is None:
            raise ValueError(f"Unexpected missing calendar row inside trade {trade.get('trade_id')} on {session}")
        pnl = mark.get("pnl_after_action_usd")
        curve.append(None if pnl is None else round(realized_pnl + float(pnl), 2))
        if session == last_date:
            final_pnl = trade.get("final_pnl_usd")
            if final_pnl is None:
                unresolved_prior = True
            else:
                realized_pnl += float(final_pnl)
                trade_idx += 1
    return curve


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    m = len(xs) // 2
    return round(xs[m], 3) if len(xs) % 2 else round((xs[m-1] + xs[m]) / 2, 3)


def curve_metrics(session_dates: list[str], pnl_curve: list[float | None], nav: float) -> dict[str, Any]:
    if len(session_dates) != len(pnl_curve):
        raise ValueError("Session and portfolio P&L curve lengths differ")
    known: list[tuple[int, str, float, float]] = []
    for i, (day, pnl) in enumerate(zip(session_dates, pnl_curve)):
        if pnl is None:
            continue
        equity = nav + float(pnl)
        if not math.isfinite(equity):
            continue
        known.append((i, day, float(pnl), equity))
    if not known:
        return {"starting_nav_usd": nav, "known_marks": 0, "status": "PENDING_NO_VALID_PORTFOLIO_MARKS"}
    peak_equity = known[0][3]
    peak_date = known[0][1]
    max_dd_pct = 0.0
    max_dd_usd = 0.0
    max_dd_peak_date = peak_date
    max_dd_trough_date = known[0][1]
    for _, day, _, equity in known:
        if equity >= peak_equity:
            peak_equity, peak_date = equity, day
        else:
            dd_usd = peak_equity - equity
            dd_pct = (equity / peak_equity - 1.0) * 100.0 if peak_equity > 0 else None
            if dd_usd > max_dd_usd:
                max_dd_usd = dd_usd
            if dd_pct is not None and dd_pct < max_dd_pct:
                max_dd_pct = dd_pct
                max_dd_peak_date = peak_date
                max_dd_trough_date = day

    # Drawdown cycles close only when a new observed equity high recovers the prior peak.
    cycles: list[dict[str, Any]] = []
    high_value, high_date, high_idx = known[0][3], known[0][1], known[0][0]
    worst_dd_pct, worst_trough_date, worst_trough_idx = 0.0, high_date, high_idx
    for idx, day, _, equity in known[1:]:
        dd_pct = (equity / high_value - 1.0) * 100.0 if high_value > 0 else 0.0
        if equity >= high_value:
            cycles.append({
                "peak_date": high_date, "trough_date": worst_trough_date,
                "trough_index": worst_trough_idx, "max_drawdown_pct": worst_dd_pct,
                "recovered_date": day, "peak_index": high_idx,
            })
            high_value, high_date, high_idx = equity, day, idx
            worst_dd_pct, worst_trough_date, worst_trough_idx = 0.0, day, idx
        elif dd_pct < worst_dd_pct:
            worst_dd_pct, worst_trough_date, worst_trough_idx = dd_pct, day, idx
    cycles.append({
        "peak_date": high_date, "trough_date": worst_trough_date,
        "trough_index": worst_trough_idx, "max_drawdown_pct": worst_dd_pct,
        "recovered_date": None, "peak_index": high_idx,
    })
    if max_dd_peak_date == peak_date and max_dd_pct == 0:
        max_dd_peak_date = peak_date
        max_dd_trough_date = peak_date

    span_years = (date.fromisoformat(session_dates[-1]) - date.fromisoformat(session_dates[0])).days / 365.2425
    levels = []
    for level in DD_LEVELS:
        hit = sorted(
            [c for c in cycles if c["max_drawdown_pct"] <= -level],
            key=lambda c: c["trough_index"],
        )
        gaps = [hit[i]["trough_index"] - hit[i-1]["trough_index"] for i in range(1, len(hit))]
        years_with_event = sorted({c["trough_date"][:4] for c in hit})
        levels.append({
            "level_pct": level,
            "episodes": len(hit),
            "events_per_year": round(len(hit) / span_years, 4) if span_years > 0 else None,
            "years_with_event": len(years_with_event),
            "calendar_years": len({d[:4] for d in session_dates}),
            "median_gap_sessions": _median([float(x) for x in gaps]),
            "trough_year_counts": {
                y: sum(1 for c in hit if c["trough_date"][:4] == y) for y in years_with_event
            },
        })
    missing = len(pnl_curve) - len(known)
    final_pnl = next((p for p in reversed(pnl_curve) if p is not None), None)
    return {
        "starting_nav_usd": nav,
        "ending_nav_last_observed_usd": round(nav + final_pnl, 2) if final_pnl is not None else None,
        "net_pnl_last_observed_usd": round(final_pnl, 2) if final_pnl is not None else None,
        "known_marks": len(known),
        "expected_sessions": len(session_dates),
        "mark_coverage_pct": round(100 * len(known) / len(session_dates), 4),
        "missing_marks_not_filled": missing,
        "max_drawdown_usd_peak_to_trough": round(max_dd_usd, 2),
        "max_drawdown_pct_of_prior_equity_peak": round(max_dd_pct, 4),
        "max_drawdown_peak_date": max_dd_peak_date,
        "max_drawdown_trough_date": max_dd_trough_date,
        "max_drawdown_cycle_count": len(cycles),
        "drawdown_levels": levels,
        "trades_in_serial_cohort": len(ordered_trade_ids := []),  # filled by caller
        "status": "OBSERVED_QUOTE_SIDE_SERIAL_FIXED_UNIT_REPLAY_NOT_LIVE_EQUITY",
        "limitations": [
            "One ratio unit per non-overlapping historical episode; no reinvestment, compounding, or NAV-scaled quantity.",
            "Missing option marks stay null; drawdowns are observed-mark estimates and may understate unobserved intraday/in-between-mark troughs.",
            "EOD preservation-mirror quotes are not confirmed fills; exact quote times, broker margin, assignment and forced liquidation are unavailable.",
            "A terminal-tail-loss budget that permits zero units blocks live use regardless of this historical mark-to-market curve.",
        ],
    }


def build_curves(cohort: list[dict[str, Any]], session_dates: list[str], replay_module) -> dict[str, Any]:
    curves: dict[str, list[float | None]] = {}
    summary: dict[str, Any] = {}
    nav = 80_000.0
    for policy in replay_module.policy_list():
        results = [
            replay_module.simulate_policy(trade, policy, SLIPPAGE, COMMISSION)
            for trade in cohort
        ]
        pnl_curve = combine_episode_daily(session_dates, results)
        curves[policy["name"]] = pnl_curve
        metrics = curve_metrics(session_dates, pnl_curve, nav)
        metrics["trades_in_serial_cohort"] = len(results)
        metrics["resolved_trades"] = sum(1 for x in results if x.get("final_pnl_usd") is not None)
        metrics["win_rate_pct"] = round(
            100 * sum(1 for x in results if x.get("final_pnl_usd") is not None and float(x["final_pnl_usd"]) > 0)
            / max(1, metrics["resolved_trades"]), 4
        )
        metrics["net_pnl_sum_closed_trades_usd"] = round(
            sum(float(x["final_pnl_usd"]) for x in results if x.get("final_pnl_usd") is not None), 2
        )
        metrics["mark_coverage_across_active_trade_sessions_pct"] = round(
            100 * sum(1 for x in results for d in x["daily"] if d.get("pnl_after_action_usd") is not None)
            / max(1, sum(len(x["daily"]) for x in results)), 4
        )
        summary[policy["name"]] = metrics
    return {
        "research_id": "QQQ_PUT_RATIO_SERIAL_PORTFOLIO_CURVE_V1",
        "status": "RESEARCH_DIAGNOSTIC_ONLY_DEPLOYMENT_BLOCKED",
        "source_window": {"start": session_dates[0], "end": session_dates[-1], "sessions": len(session_dates)},
        "episode_definition": "Fixed one 1-long/5-short unit per sequential, non-overlapping source episode. The next episode starts only after prior expiry; this is not NAV-scaled or reinvested.",
        "evidence": "OBSERVED_EOD_QUOTE_SIDES + DERIVED_NET_LIQUIDATION_ESTIMATE; NOT_CONFIRMED_FILLS",
        "cost_convention": {"slippage_per_leg_per_side_usd": SLIPPAGE, "commission_per_contract_per_side_usd": COMMISSION},
        "curve_semantics": "Each series is cumulative portfolio P&L in USD, before adding the chosen starting NAV. Flat/no-position sessions carry only realized P&L. Missing marks during an open ratio remain null; no forward fills.",
        "reference_nav_usd_for_summary": nav,
        "source_option_end": "2025-12-15",
        "trade_count": len(cohort),
        "session_dates": session_dates,
        "cumulative_pnl_usd_by_policy": curves,
        "metrics_by_policy_at_80k_nav": summary,
        "deployment_gate": "BLOCKED: terminal tail risk exceeds NAV for 1x5 in this sample; quote-side EOD marks are not fills; margin/assignment/forced-liquidation and blind OOS remain unresolved.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True, help="Path to generated qqq_put_ratio_exit_source_cohort.json")
    parser.add_argument("--sessions", type=Path, required=True, help="Path to full QQQ market-session calendar CSV")
    parser.add_argument("--out", type=Path, default=LAB_DIR / "portfolio_curve.json")
    args = parser.parse_args()
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    sessions = read_session_dates(args.sessions)
    replay_module = load_module(SOURCE_SCRIPT)
    result = build_curves(cohort, sessions, replay_module)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "research_id": result["research_id"], "status": result["status"],
        "trade_count": result["trade_count"], "session_count": len(sessions),
        "policy_count": len(result["cumulative_pnl_usd_by_policy"]),
        "outputs": str(args.out),
        "baseline": result["metrics_by_policy_at_80k_nav"]["BASE_DTE7_CLOSE_SHORT_RISK"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
