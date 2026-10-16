#!/usr/bin/env python3
"""Dynamic NAV, BAR-hit-rate and drawdown stress replay for the pinned QQQ put-ratio cohort.

Research-only. Each closed trade compounds into the next NAV. A one-unit budget-bypass
comparator is intentionally included to expose tail-budget violations; it is never a
deployment recommendation. EOD quote marks are not confirmed fills.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any

import qqq_put_ratio_scale_volatility_v1 as core

BAR_LEVELS = (0.005, 0.01, 0.02)
DD_LEVELS = (3, 5, 10, 15, 20, 25, 30)
SIZING_MODES = (
    "PER_TRADE_TERMINAL_BUDGET",
    "EXPANDING_WORST_TERMINAL_BUDGET",
    "FIXED_1_UNIT_BUDGET_BYPASS",
)
REGIME_STATES = (
    "ALL", "VIX_LT15", "VIX_15_25", "VIX_25_35", "VIX_GTE35",
    "DTE_LE7", "DTE_8_20", "DTE_21_40", "DTE_GT40",
)
BASE_COST = "BASE_005_065"
SOURCE_START = "2018-03-01"
SOURCE_END = "2025-12-15"
START_NAV_DEFAULT = 100_000.0
TARGET_PROFIT_DEFAULT = 214_012.0


def number(value: Any) -> float | None:
    return core.num(value)


def depth_capacity(trade: dict[str, Any], direction: str, n: int) -> int:
    """Maximum whole ratio units supported by displayed entry-side sizes."""
    q = trade.get("entry_quotes") or {}
    nl_unit, ns_unit = core.quantities(direction, n)
    long_q, short_q = q.get("long"), q.get("short")
    if not core.quote_ok(long_q, "ask") or not core.quote_ok(short_q, "bid"):
        return 0
    ask_size = number(long_q.get("ask_size"))
    bid_size = number(short_q.get("bid_size"))
    if ask_size is None or bid_size is None or ask_size < 0 or bid_size < 0:
        return 0
    return max(0, min(math.floor(ask_size / nl_unit), math.floor(bid_size / ns_unit)))


def choose_units(
    nav: float,
    budget_pct: float,
    one_unit_loss: float | None,
    prior_worst_loss: float,
    observed_depth_cap: int,
    sizing_mode: str,
) -> dict[str, Any]:
    if sizing_mode == "FIXED_1_UNIT_BUDGET_BYPASS":
        planned = 1
        denom = one_unit_loss
    else:
        denom = one_unit_loss
        if sizing_mode == "EXPANDING_WORST_TERMINAL_BUDGET":
            denom = max(float(one_unit_loss or 0), float(prior_worst_loss or 0))
        if denom is None or not math.isfinite(denom) or denom <= 0:
            planned = None
        else:
            planned = max(0, math.floor(nav * budget_pct / denom + 1e-9))
    actual = min(planned or 0, observed_depth_cap)
    status = (
        "PENDING_NO_TERMINAL_LOSS_ESTIMATE" if planned is None else
        "BLOCKED_ZERO_UNITS_BY_TAIL_BUDGET" if planned == 0 else
        "BLOCKED_NO_OBSERVED_ENTRY_DEPTH" if observed_depth_cap == 0 else
        "DEPTH_CAPPED" if actual < planned else
        "SIZED_WITHIN_TERMINAL_BUDGET"
    )
    return {
        "planned_units": planned,
        "actual_units": actual,
        "unit_terminal_loss_usd": one_unit_loss,
        "budget_usd": nav * budget_pct,
        "sizing_denominator_usd": denom,
        "sizing_status": status,
        "breaches_tail_budget": bool(
            actual > 0 and one_unit_loss is not None
            and actual * one_unit_loss > nav * budget_pct + 1e-7
        ),
    }


def vix_state(row: dict[str, Any]) -> str | None:
    v = number(row.get("vix"))
    if v is None:
        return None
    if v < 15:
        return "VIX_LT15"
    if v < 25:
        return "VIX_15_25"
    if v < 35:
        return "VIX_25_35"
    return "VIX_GTE35"


def dte_state(row: dict[str, Any]) -> str | None:
    d = number(row.get("dte"))
    if d is None:
        return None
    if d <= 7:
        return "DTE_LE7"
    if d <= 20:
        return "DTE_8_20"
    if d <= 40:
        return "DTE_21_40"
    return "DTE_GT40"


def state_matches(row: dict[str, Any], state: str) -> bool:
    if state == "ALL":
        return True
    return state in (vix_state(row), dte_state(row))


def scenario_key(config: dict[str, Any]) -> str:
    return "|".join(str(config[k]) for k in (
        "direction", "ratio_n", "tail_budget_pct", "policy", "cost_case", "sizing_mode"
    ))


def replay_scenario(
    trades: list[dict[str, Any]],
    prices: list[dict[str, Any]],
    start_nav: float,
    target_profit: float,
    direction: str,
    n: int,
    budget_pct: float,
    policy: dict[str, Any],
    cost: dict[str, Any],
    sizing_mode: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay episodes chronologically using the previously resolved NAV."""
    nav = float(start_nav)
    prior_worst_loss = 0.0
    last_exit_date: str | None = None
    executed: list[dict[str, Any]] = []
    skipped_budget = skipped_depth = skipped_overlap = 0
    depth_capped = tail_breaches = unresolved = 0
    planned_units_sum = 0
    max_planned_units = 0
    prices_dates = [str(x.get("date", ""))[:10] for x in prices]
    ordered_trades = sorted(
        trades,
        key=lambda t: str(t.get("entry_date") or ((t.get("path") or [{}])[0].get("date", "")))
    )

    for trade in ordered_trades:
        if nav <= 0:
            break
        entry_date = str(trade.get("entry_date") or ((trade.get("path") or [{}])[0].get("date", "")))[:10]
        if not entry_date:
            continue
        nl_unit, ns_unit = core.quantities(direction, n)
        env = core.terminal_envelope(
            trade, nl_unit, ns_unit, cost["slippage"], cost["commission"]
        )
        one_unit_loss = number(env.get("max_terminal_loss_usd"))
        prior_worst_loss = max(prior_worst_loss, float(one_unit_loss or 0))

        if last_exit_date is not None and entry_date <= last_exit_date:
            skipped_overlap += 1
            continue

        depth = depth_capacity(trade, direction, n)
        sizing = choose_units(
            nav, budget_pct, one_unit_loss, prior_worst_loss,
            depth, sizing_mode
        )
        # For a per-trade cap, the denominator remains current-trade liability; the prior worst
        # envelope only binds the explicitly expanding-history sizing mode.
        planned = sizing["planned_units"]
        planned_units_sum += int(planned or 0)
        max_planned_units = max(max_planned_units, int(planned or 0))
        depth_capped += int(sizing["sizing_status"] == "DEPTH_CAPPED")
        tail_breaches += int(sizing["breaches_tail_budget"])
        units = int(sizing["actual_units"])
        if units <= 0:
            if sizing["sizing_status"] == "BLOCKED_NO_OBSERVED_ENTRY_DEPTH":
                skipped_depth += 1
            else:
                skipped_budget += 1
            continue

        result = core.simulate(
            trade, direction, n, nav, policy,
            float(cost["slippage"]), float(cost["commission"]),
            units=units, include_mark_path=True
        )
        mark_curve = result.get("mark_curve") or []
        final_pnl = number(result.get("final_pnl_usd"))
        exit_date = (
            str(mark_curve[-1].get("date", ""))[:10] if mark_curve else
            str(trade.get("expiry") or entry_date)[:10]
        )
        if final_pnl is None:
            unresolved += 1
            # Do not make up a cash exit. Censor the account after unresolved active risk.
            exit_date = prices_dates[-1] if prices_dates else exit_date

        marks_by_date = {str(x.get("date", ""))[:10]: x for x in mark_curve}
        friction = core.friction_observations(
            trade, nl_unit * units, ns_unit * units,
            float(cost["slippage"]), float(cost["commission"])
        )
        friction = [
            {**x, "state_labels": tuple(x.get("state_labels") or ())}
            for x in friction if str(x.get("date", ""))[:10] in marks_by_date
        ]
        nav_after = nav + final_pnl if final_pnl is not None else None
        executed.append({
            "trade_id": trade.get("trade_id"),
            "entry_date": entry_date,
            "exit_date": exit_date,
            "nav_before": nav,
            "nav_after": nav_after,
            "final_pnl_usd": final_pnl,
            "final_status": result.get("final_status"),
            "ratio_units": units,
            "planned_units": planned,
            "one_unit_terminal_loss_usd": one_unit_loss,
            "budget_usd": sizing["budget_usd"],
            "sizing_denominator_usd": sizing["sizing_denominator_usd"],
            "sizing_status": sizing["sizing_status"],
            "breaches_tail_budget": sizing["breaches_tail_budget"],
            "mark_curve": mark_curve,
            "friction_observations": friction,
            "mark_coverage_pct": result.get("mark_coverage_pct"),
        })
        if final_pnl is None:
            break
        nav = float(nav_after)
        last_exit_date = exit_date
        if nav <= 0:
            break

    daily = build_daily_curve(prices, executed, float(start_nav))
    dd_meta, dd_rows = drawdown_tiers(daily, prices)
    valid_nav = [float(x["nav_usd"]) for x in daily if x.get("nav_usd") is not None and float(x["nav_usd"]) > 0]
    end_nav = None if unresolved else nav
    net_pnl = end_nav - start_nav if end_nav is not None else None
    years = (
        (core.date.fromisoformat(prices_dates[-1]) - core.date.fromisoformat(prices_dates[0])).days / 365.2425
        if len(prices_dates) > 1 else 0.0
    )
    cagr = 100 * ((end_nav / start_nav) ** (1 / years) - 1) if end_nav and end_nav > 0 and years > 0 else None
    max_observed_nav = max(valid_nav) if valid_nav else None
    summary = {
        "direction": direction,
        "ratio_n": n,
        "long_contracts_per_unit": nl_unit,
        "short_contracts_per_unit": ns_unit,
        "start_nav_usd": start_nav,
        "target_profit_usd": target_profit,
        "target_nav_usd": start_nav + target_profit,
        "tail_budget_pct_nav": budget_pct * 100,
        "policy": policy["name"],
        "cost_case": cost["name"],
        "sizing_mode": sizing_mode,
        "slippage_per_leg_usd": cost["slippage"],
        "commission_per_contract_per_side_usd": cost["commission"],
        "candidate_episodes": len(trades),
        "executed_episodes": len(executed),
        "skipped_by_tail_or_no_whole_unit": skipped_budget,
        "skipped_by_entry_depth": skipped_depth,
        "skipped_by_overlap": skipped_overlap,
        "depth_capped_episodes": depth_capped,
        "tail_budget_breach_episodes": tail_breaches,
        "unresolved_episodes": unresolved,
        "max_planned_units": max_planned_units,
        "mean_planned_units": round(planned_units_sum / len(trades), 4) if trades else None,
        "mean_actual_units": round(statistics.mean([x["ratio_units"] for x in executed]), 4) if executed else None,
        "max_actual_units": max((x["ratio_units"] for x in executed), default=0),
        "net_pnl_usd": round(net_pnl, 2) if net_pnl is not None else None,
        "final_nav_usd": round(end_nav, 2) if end_nav is not None else None,
        "return_pct": round(net_pnl / start_nav * 100, 4) if net_pnl is not None else None,
        "cagr_pct": round(cagr, 4) if cagr is not None else None,
        "target_touched_any_observed_nav_mark": bool(max_observed_nav is not None and max_observed_nav >= start_nav + target_profit),
        "target_reached_final_nav": bool(end_nav is not None and end_nav >= start_nav + target_profit),
        "max_observed_nav_usd": round(max_observed_nav, 2) if max_observed_nav is not None else None,
        "max_drawdown_pct_observed": dd_meta["max_drawdown_pct"],
        "daily_valid_nav_marks": dd_meta["valid_marks"],
        "daily_missing_nav_marks": dd_meta["missing_marks"],
        "daily_nav_coverage_pct": dd_meta["coverage_pct"],
        "evidence": "2018-03-01 to 2025-12-15 EOD quote-side replay, not confirmed fills",
        "deployment_status": "BLOCKED_RESEARCH_ONLY",
    }
    config = {
        "direction": direction, "ratio_n": n, "tail_budget_pct": budget_pct,
        "policy": policy["name"], "cost_case": cost["name"], "sizing_mode": sizing_mode,
    }
    summary["scenario_id"] = scenario_key(config)

    for row in dd_rows:
        row.update(config)
    return summary, executed, daily


def build_daily_curve(
    prices: list[dict[str, Any]],
    executed: list[dict[str, Any]],
    start_nav: float,
) -> list[dict[str, Any]]:
    """Merge open-position quote marks with cash/NAV when no option exposure is open."""
    dates = [str(x.get("date", ""))[:10] for x in prices]
    by_episode = sorted(executed, key=lambda x: x["entry_date"])
    rows: list[dict[str, Any]] = []
    index = 0
    completed_nav = float(start_nav)
    unresolved_before = False
    for day in dates:
        while index < len(by_episode) and by_episode[index]["exit_date"] < day:
            ep = by_episode[index]
            if ep.get("nav_after") is None:
                unresolved_before = True
            else:
                completed_nav = float(ep["nav_after"])
            index += 1
        if unresolved_before:
            rows.append({"date": day, "nav_usd": None,
                         "mark_status": "CENSORED_AFTER_UNRESOLVED_EXPOSURE", "active_trade_id": None})
            continue
        active = None
        if index < len(by_episode):
            ep = by_episode[index]
            if ep["entry_date"] <= day <= ep["exit_date"]:
                active = ep
        if active is None:
            rows.append({"date": day, "nav_usd": round(completed_nav, 4),
                         "mark_status": "CASH_OR_NO_OPEN_EXPOSURE", "active_trade_id": None})
            continue
        mark = next((x for x in active["mark_curve"] if str(x.get("date", ""))[:10] == day), None)
        mark_pnl = number(mark.get("pnl_usd")) if mark else None
        value = active["nav_before"] + mark_pnl if mark_pnl is not None else None
        rows.append({"date": day, "nav_usd": round(value, 4) if value is not None else None,
                     "mark_status": (mark.get("status", "OBSERVED_MARK") if mark else "MISSING_OPTION_MARK"),
                     "active_trade_id": active.get("trade_id")})
    return rows


def drawdown_tiers(
    daily: list[dict[str, Any]],
    prices: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    points = [{"date": x["date"], "nav": number(x.get("nav_usd"))} for x in daily]
    valid = [x for x in points if x["nav"] is not None and x["nav"] > 0]
    missing = len(points) - len(valid)
    if not valid:
        return {"max_drawdown_pct": None, "valid_marks": 0, "missing_marks": len(points), "coverage_pct": 0.0}, []
    peak = valid[0]
    worst = 0.0
    trough = peak
    cycles: list[dict[str, Any]] = []
    drawdowns: dict[str, float] = {}
    for point in valid:
        if point["nav"] >= peak["nav"]:
            if worst < 0:
                cycles.append({"worst_pct": worst, "trough_date": trough["date"]})
            peak = point
            worst = 0.0
            trough = point
            drawdowns[point["date"]] = 0.0
        else:
            dd = (point["nav"] / peak["nav"] - 1) * 100
            drawdowns[point["date"]] = dd
            if dd < worst:
                worst = dd
                trough = point
    if worst < 0:
        cycles.append({"worst_pct": worst, "trough_date": trough["date"]})
    start = core.date.fromisoformat(points[0]["date"])
    end = core.date.fromisoformat(points[-1]["date"])
    years = max(0.0, (end - start).days / 365.2425)
    calendar_years = sorted({p["date"][:4] for p in points})
    result = []
    max_dd = min([0.0] + [x["worst_pct"] for x in cycles])
    for level in DD_LEVELS:
        hits = [x for x in cycles if x["worst_pct"] <= -level + 1e-9]
        event_years: dict[str, int] = {}
        for hit in hits:
            year = hit["trough_date"][:4]
            event_years[year] = event_years.get(year, 0) + 1
        day_hits = sum(1 for x in drawdowns.values() if x <= -level + 1e-9)
        result.append({
            "drawdown_level_pct": level,
            "cycle_count": len(hits),
            "cycles_per_year": round(len(hits) / years, 4) if years > 0 else None,
            "event_year_count": len(event_years),
            "observed_year_count": len(calendar_years),
            "event_year_incidence_pct": round(100 * len(event_years) / len(calendar_years), 4) if calendar_years else None,
            "event_years": ",".join(sorted(event_years)),
            "event_year_counts": json.dumps(event_years, sort_keys=True),
            "valid_days_at_or_below_level": day_hits,
            "valid_day_incidence_pct": round(100 * day_hits / len(drawdowns), 4) if drawdowns else None,
            "valid_drawdown_days": len(drawdowns),
            "missing_nav_marks": missing,
            "sample_status": "OBSERVED_MARKS_NOT_FORWARD_PROBABILITY" if len(valid) >= 100 else "PENDING_SMALL_SAMPLE",
        })
    return {
        "max_drawdown_pct": round(max_dd, 4),
        "valid_marks": len(valid),
        "missing_marks": missing,
        "coverage_pct": round(100 * len(valid) / len(points), 4) if points else None,
        "span_years": round(years, 4),
    }, result


def build_bar_rows(
    executed: list[dict[str, Any]],
    config: dict[str, Any],
    states: tuple[str, ...] = ("ALL",),
) -> list[dict[str, Any]]:
    rows = []
    for state in states:
        for level in BAR_LEVELS:
            for bar_type in ("NET_PROFIT_BAR", "NET_LOSS_BAR", "FRICTION_COST_BAR"):
                episode_denominator = episode_hits = 0
                mark_denominator = mark_hits = 0
                for episode in executed:
                    threshold = float(episode["nav_before"]) * level
                    if bar_type == "FRICTION_COST_BAR":
                        selected = [x for x in episode["friction_observations"] if state_matches(x, state)]
                        values = [number(x.get("friction_drag_usd")) for x in selected]
                    else:
                        selected = [x for x in episode["mark_curve"] if state_matches(x, state)]
                        values = [number(x.get("pnl_usd")) for x in selected]
                    values = [v for v in values if v is not None and math.isfinite(v)]
                    if not values:
                        continue
                    episode_denominator += 1
                    mark_denominator += len(values)
                    if bar_type == "NET_PROFIT_BAR":
                        mark_hit = sum(v >= threshold for v in values)
                    elif bar_type == "NET_LOSS_BAR":
                        mark_hit = sum(v <= -threshold for v in values)
                    else:
                        mark_hit = sum(v >= threshold for v in values)
                    mark_hits += mark_hit
                    episode_hits += int(mark_hit > 0)
                lo, hi = core.wilson95(episode_hits, episode_denominator)
                sample_status = (
                    "BLOCKED_NO_EXECUTED_EPISODES" if episode_denominator == 0 else
                    "PENDING_SMALL_EPISODE_SAMPLE" if episode_denominator < 30 else
                    "BAR_SAMPLE_OK_DIAGNOSTIC_ONLY"
                )
                rows.append({
                    **config,
                    "state": state,
                    "bar_type": bar_type,
                    "bar_level_pct_nav": level * 100,
                    "episode_denominator": episode_denominator,
                    "episode_hit_count": episode_hits,
                    "episode_hit_pct": round(100 * episode_hits / episode_denominator, 4) if episode_denominator else None,
                    "episode_hit_wilson95_nominal_low_pct": round(lo, 4) if lo is not None else None,
                    "episode_hit_wilson95_nominal_high_pct": round(hi, 4) if hi is not None else None,
                    "mark_observation_denominator": mark_denominator,
                    "mark_hit_count": mark_hits,
                    "mark_hit_pct": round(100 * mark_hits / mark_denominator, 4) if mark_denominator else None,
                    "sample_status": sample_status,
                    "interpretation": (
                        "Historical episode/mark hit rate; not a forward probability or confirmed fill rate."
                        if bar_type != "FRICTION_COST_BAR" else
                        "Midpoint-to-side quote friction threshold rate; not confirmed fill costs."
                    ),
                })
    return rows


def build_annual_rows(
    daily: list[dict[str, Any]],
    prices: list[dict[str, Any]],
    config: dict[str, Any],
    start_nav: float,
) -> list[dict[str, Any]]:
    output = []
    years = sorted({str(x["date"])[:4] for x in prices})
    for year in years:
        year_rows = [x for x in daily if str(x["date"])[:4] == year]
        if not year_rows:
            continue
        previous = [x for x in daily if x["date"] < year_rows[0]["date"] and x.get("nav_usd") is not None]
        year_start = float(previous[-1]["nav_usd"]) if previous else float(start_nav)
        year_end = number(year_rows[-1].get("nav_usd"))
        valid = [x for x in year_rows if x.get("nav_usd") is not None]
        peak = year_start
        worst = 0.0
        for row in valid:
            value = float(row["nav_usd"])
            if value > peak:
                peak = value
            elif peak > 0:
                worst = min(worst, (value / peak - 1) * 100)
        output.append({
            **config,
            "year": year,
            "year_start_nav_usd": round(year_start, 2),
            "year_end_nav_usd": round(year_end, 2) if year_end is not None else None,
            "year_return_pct": round((year_end / year_start - 1) * 100, 4) if year_end is not None and year_start > 0 else None,
            "year_max_drawdown_pct_observed": round(worst, 4),
            "session_count": len(year_rows),
            "valid_nav_marks": len(valid),
            "nav_coverage_pct": round(100 * len(valid) / len(year_rows), 4) if year_rows else None,
            "status": "OBSERVED" if year_end is not None else "CENSORED_MISSING_FINAL_MARK",
        })
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    core.write_csv(path, rows)


def selected_daily(config: dict[str, Any]) -> bool:
    return (
        config["cost_case"] == BASE_COST
        and abs(float(config["tail_budget_pct"]) - 0.01) < 1e-10
        and config["ratio_n"] in (1, 3, 5)
        and config["policy"] in ("DTE7_CLOSE_SHORT_RISK", "TP_1.0PCT_FULL_CLOSE", "FAST5_1.0PCT_TRIM_SHORT_RISK")
        and config["sizing_mode"] in ("PER_TRADE_TERMINAL_BUDGET", "FIXED_1_UNIT_BUDGET_BYPASS")
    )


def run_study(
    trades: list[dict[str, Any]],
    prices: list[dict[str, Any]],
    out: Path,
    start_nav: float = START_NAV_DEFAULT,
    target_profit: float = TARGET_PROFIT_DEFAULT,
) -> dict[str, Any]:
    if not trades:
        raise ValueError("No option episodes; refusing a zero-sample result.")
    if not prices:
        raise ValueError("Underlying price series is empty.")
    if not math.isfinite(start_nav) or start_nav <= 0:
        raise ValueError("Start NAV must be finite and positive.")
    if not math.isfinite(target_profit) or target_profit <= 0:
        raise ValueError("Target profit must be finite and positive.")
    dates = [str(x.get("date", ""))[:10] for x in prices]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise ValueError("Price dates must be unique ascending.")
    if dates[0] < SOURCE_START or dates[-1] > SOURCE_END:
        raise ValueError("Underlying data must remain within the pinned option source window.")
    target_nav = start_nav + target_profit
    portfolio_rows = []
    all_bar_rows = []
    regime_bar_rows = []
    drawdown_rows = []
    annual_rows = []
    selected_daily_rows = []
    policies = core.policies()
    scenario_count = 0

    for direction in (core.SHORT_HEAVY, core.LONG_HEAVY):
        for n in core.RATIOS:
            for budget_pct in core.BUDGET_PCTS:
                for policy in policies:
                    for cost in core.COSTS:
                        for sizing_mode in SIZING_MODES:
                            config = {
                                "direction": direction,
                                "ratio_n": n,
                                "tail_budget_pct": budget_pct,
                                "policy": policy["name"],
                                "cost_case": cost["name"],
                                "sizing_mode": sizing_mode,
                            }
                            summary, executed, daily = replay_scenario(
                                trades, prices, start_nav, target_profit, direction, n,
                                budget_pct, policy, cost, sizing_mode,
                            )
                            portfolio_rows.append(summary)
                            all_bar_rows.extend(build_bar_rows(executed, config))
                            dd_meta, dds = drawdown_tiers(daily, prices)
                            for row in dds:
                                row.update(config)
                            drawdown_rows.extend(dds)
                            annual_rows.extend(build_annual_rows(daily, prices, config, start_nav))
                            if cost["name"] == BASE_COST and abs(budget_pct - 0.01) < 1e-10 and sizing_mode == "PER_TRADE_TERMINAL_BUDGET":
                                regime_bar_rows.extend(build_bar_rows(executed, config, REGIME_STATES))
                            if selected_daily(config):
                                for point in daily:
                                    selected_daily_rows.append({
                                        **config,
                                        "date": point["date"],
                                        "nav_usd": point["nav_usd"],
                                        "mark_status": point["mark_status"],
                                        "active_trade_id": point["active_trade_id"],
                                    })
                            scenario_count += 1

    viable = [row for row in portfolio_rows if row["net_pnl_usd"] is not None]
    budgeted = [
        row for row in viable
        if row["sizing_mode"] != "FIXED_1_UNIT_BUDGET_BYPASS"
        and row["tail_budget_breach_episodes"] == 0
        and row["executed_episodes"] >= 30
    ]
    by_net = lambda x: float(x["net_pnl_usd"] if x["net_pnl_usd"] is not None else -math.inf)
    best_any = sorted(viable, key=by_net, reverse=True)[:10]
    best_budgeted = sorted(budgeted, key=by_net, reverse=True)[:10]
    goal_touch_count = sum(bool(x["target_touched_any_observed_nav_mark"]) for x in viable)
    goal_final_count = sum(bool(x["target_reached_final_nav"]) for x in viable)

    for path, rows in (
        ("dynamic_nav_portfolio_matrix.csv", portfolio_rows),
        ("dynamic_bar_occurrence.csv", all_bar_rows),
        ("dynamic_bar_occurrence_by_regime.csv", regime_bar_rows),
        ("dynamic_drawdown_tiers.csv", drawdown_rows),
        ("dynamic_annual_path.csv", annual_rows),
        ("dynamic_nav_daily_selected.csv", selected_daily_rows),
    ):
        write_csv(out / path, rows)

    span_days = (core.date.fromisoformat(dates[-1]) - core.date.fromisoformat(dates[0])).days
    span_years = span_days / 365.2425 if span_days > 0 else 0
    meta = {
        "research_id": "QQQ_DYNAMIC_NAV_BAR_STRESS_V1",
        "status": "RESEARCH_DIAGNOSTIC_ONLY_DEPLOYMENT_BLOCKED",
        "date_start": dates[0],
        "date_end": dates[-1],
        "option_source_end": SOURCE_END,
        "option_episode_candidates": len(trades),
        "start_nav_usd": start_nav,
        "target_profit_usd": target_profit,
        "target_nav_usd": target_nav,
        "required_cagr_pct": round(100 * ((target_nav / start_nav) ** (1 / span_years) - 1), 4) if span_years > 0 else None,
        "budget_tiers_pct_nav": [round(x * 100, 4) for x in core.BUDGET_PCTS],
        "bar_tiers_pct_nav": [round(x * 100, 4) for x in BAR_LEVELS],
        "drawdown_tiers_pct": list(DD_LEVELS),
        "ratio_directions": [core.SHORT_HEAVY, core.LONG_HEAVY],
        "N_values": list(core.RATIOS),
        "policy_count": len(policies),
        "cost_cases": [x["name"] for x in core.COSTS],
        "sizing_modes": list(SIZING_MODES),
        "scenario_count": scenario_count,
        "bar_occurrence_rows": len(all_bar_rows),
        "regime_bar_occurrence_rows": len(regime_bar_rows),
        "drawdown_tier_rows": len(drawdown_rows),
        "annual_path_rows": len(annual_rows),
        "selected_daily_curve_rows": len(selected_daily_rows),
        "target_touched_config_count": goal_touch_count,
        "target_reached_final_config_count": goal_final_count,
        "target_counts_are_search_grid_not_probabilities": True,
        "best_in_sample_unconstrained": best_any,
        "best_in_sample_budget_compliant_min30": best_budgeted,
        "source_evidence": core.EVIDENCE,
        "limitations": [
            "EOD preservation-mirror quote marks are not confirmed fills.",
            "History has been previously reviewed; no scenario is blind final out-of-sample.",
            "Daily open-position NAV becomes null when option quote marks are missing; observed drawdown can understate hidden loss.",
            "Margin, assignment, forced liquidation and broker buying-power records are not modeled.",
            "Fixed-one-unit bypass sizing is shown only as a tail-budget-violating diagnostic.",
            "Search-grid goal counts are correlated historical configurations, not success probabilities.",
        ],
    }
    lines = [
        "# Dynamic NAV x BAR occurrence x drawdown stress",
        "",
        "Research only; deployment and broker orders remain BLOCKED.",
        "",
        "## Fixed objective",
        "",
        "Initial NAV: USD {:,.2f}".format(start_nav),
        "Net profit target: USD {:,.2f}; target final NAV: USD {:,.2f}".format(target_profit, target_nav),
        "Required CAGR over observed source span: {:.3f}%".format(meta["required_cagr_pct"]),
        "Option episodes: {}; option quote source ends {}".format(len(trades), SOURCE_END),
        "Scenario configurations: {}; these are a search grid, not independent trials.".format(scenario_count),
        "",
        "## Best in-sample configurations (not promoted)",
        "",
        "| Direction | N | Budget | Policy | Cost | Sizing | Done/62 | Net P&L | Final NAV | CAGR | MaxDD | Target final? |",
        "|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in best_any:
        lines.append("| {} | {} | {:.1f}% | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            row["direction"], row["ratio_n"], row["tail_budget_pct_nav"], row["policy"],
            row["cost_case"], row["sizing_mode"], row["executed_episodes"], row["net_pnl_usd"],
            row["final_nav_usd"], row["cagr_pct"], row["max_drawdown_pct_observed"],
            row["target_reached_final_nav"],
        ))
    lines += [
        "",
        "## Best in-sample configurations with risk budget respected and at least 30 episodes",
        "",
        "| Direction | N | Budget | Policy | Cost | Sizing | Done/62 | Net P&L | Final NAV | CAGR | MaxDD | Target final? |",
        "|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in best_budgeted:
        lines.append("| {} | {} | {:.1f}% | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            row["direction"], row["ratio_n"], row["tail_budget_pct_nav"], row["policy"],
            row["cost_case"], row["sizing_mode"], row["executed_episodes"], row["net_pnl_usd"],
            row["final_nav_usd"], row["cagr_pct"], row["max_drawdown_pct_observed"],
            row["target_reached_final_nav"],
        ))
    lines += [
        "",
        "## BAR levels and definition",
        "",
        "NET_PROFIT_BAR: at least one observed option-side net-liq mark reaches 0.5%, 1%, or 2% of that episode entry NAV.",
        "NET_LOSS_BAR: at least one observed option-side net-liq mark reaches the same negative NAV percentage.",
        "FRICTION_COST_BAR: midpoint-to-side-quote liquidation drag reaches the same NAV percentage; this is modeled quote drag, not fill cost.",
        "Tables contain episode incidence and mark-level incidence; regime table slices the 1% budget / base-cost / per-trade-sized cohort by VIX and DTE.",
        "BAR rows with zero executable episodes are BLOCKED/PENDING, not 0% occurrence.",
        "",
        "## Caveats",
        "",
        "No automatic trades. No live sizing or Frozen Original Hybrid policy changes.",
        "Year-2018 sample is partial; daily missing quote marks remain null.",
        "Historical BAR rates are descriptive; serial dependence and prior study selection mean these are not calibrated future probabilities.",
        "A high in-sample total P&L does not mean the setup is executable or that the target has a similar future success probability.",
    ]
    (out / "dynamic_nav_bar_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta["bar_definition"] = "Historical episode/mark crossing rate, not future probability or confirmed fill rate."
    (out / "dynamic_nav_bar_summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-nav", type=float, default=START_NAV_DEFAULT)
    parser.add_argument("--target-profit", type=float, default=TARGET_PROFIT_DEFAULT)
    args = parser.parse_args()
    trades = json.loads(args.cohort.read_text(encoding="utf-8"))
    prices = core.load_prices(args.prices)
    meta = run_study(trades, prices, args.out, args.start_nav, args.target_profit)
    print(json.dumps({k: v for k, v in meta.items()
                      if k not in ("best_in_sample_unconstrained", "best_in_sample_budget_compliant_min30")}, indent=2))
    print((args.out / "dynamic_nav_bar_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
