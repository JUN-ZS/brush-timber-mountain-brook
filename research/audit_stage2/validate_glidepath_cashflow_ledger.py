#!/usr/bin/env python3
"""Independent month-end cash-flow ledger replay for the Stage 2 glidepath artifact.

This validator deliberately does not import stock_bond_glidepath_backtest.py. It rebuilds
holdings from the frozen adjusted-close panel, applies published month-end cash flows, and
independently reconciles window ledger values and all annual NAV/cash-flow aggregates.
It does not claim to independently reproduce daily max drawdown, TWR CAGR, or XIRR.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

TICKERS = ("QQQ", "SPY", "AGG", "SHY", "IEF", "TLT")
BOND_TICKERS = ("AGG", "SHY", "IEF", "TLT")
TARGETS = (30, 40, 50, 60, 70, 80, 90, 100)
TIMINGS = ("front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late")
FLOWS = ("no_withdrawals", "delayed_stepup_example", "monthly_withdrawal_500_usd_stress", "monthly_withdrawal_1000_usd_stress")
INITIAL_CAPITAL = 100_000.0
HORIZON_MONTHS = 120
USD_TOLERANCE = 0.05


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def quantile(values: np.ndarray, probability: float) -> float:
    ordered = np.sort(np.asarray(values, dtype=float))
    require(ordered.size > 0, "Cannot compute quantile of an empty group")
    if ordered.size == 1:
        return float(ordered[0])
    position = (ordered.size - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    fraction = position - low
    return float(ordered[low] * (1.0 - fraction) + ordered[high] * fraction)


def target_bond_weight(target_pct: int, elapsed_months: int, timing: str) -> float:
    year = min(10, max(0, elapsed_months // 12))
    if timing == "front_rapid":
        progress = 0.5 * year if year <= 1 else 0.5 + 0.5 * (year - 1) / 9.0
    elif timing == "front_fast":
        progress = 0.5 * year / 2.0 if year <= 2 else 0.5 + 0.5 * (year - 2) / 8.0
    elif timing == "front_loaded":
        progress = 0.5 * year / 3.0 if year <= 3 else 0.5 + 0.5 * (year - 3) / 7.0
    elif timing == "linear":
        progress = year / 10.0
    elif timing == "mid_loaded":
        x = year / 10.0
        progress = 3.0 * x * x - 2.0 * x * x * x
    elif timing == "staggered":
        if year <= 2:
            progress = 0.25 * year / 2.0
        elif year <= 5:
            progress = 0.25 + 0.25 * (year - 2) / 3.0
        elif year <= 8:
            progress = 0.50 + 0.25 * (year - 5) / 3.0
        else:
            progress = 0.75 + 0.25 * (year - 8) / 2.0
    elif timing == "back_loaded":
        progress = max(0.0, (year - 5) / 5.0)
    elif timing == "back_late":
        progress = max(0.0, (year - 7) / 3.0)
    else:
        raise ValueError(f"Unsupported timing rule: {timing}")
    return target_pct / 100.0 * progress


def load_panel(path: Path, summary: dict[str, Any]):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = summary["data"]["raw_panel_canonical_sha256"]
    require(digest == expected, f"Frozen panel SHA-256 mismatch: expected {expected}, got {digest}")
    dates: list[date] = []
    prices: dict[str, list[float]] = {ticker: [] for ticker in TICKERS}
    last_month_index: dict[tuple[int, int], int] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None and set(("date", *TICKERS)).issubset(reader.fieldnames),
                "Adjusted-close panel does not have the expected columns")
        for row in reader:
            day = date.fromisoformat(row["date"])
            require(not dates or dates[-1] < day, f"Panel dates not strictly increasing at {day}")
            dates.append(day)
            for ticker in TICKERS:
                value = float(row[ticker])
                require(math.isfinite(value) and value > 0.0, f"Invalid {ticker} adjusted close on {day}")
                prices[ticker].append(value)
            last_month_index[(day.year, day.month)] = len(dates) - 1
    monthly_indices = sorted(last_month_index.values())
    monthly_dates = [dates[index] for index in monthly_indices]
    require(len(monthly_indices) == summary["method"]["rolling_windows_per_scenario"] + HORIZON_MONTHS,
            "Month-end point count does not conserve the published rolling-window count")
    require(len(dates) == summary["data"]["daily_common_observations"], "Daily panel row count mismatch")
    price_arrays = {ticker: np.asarray(values, dtype=float) for ticker, values in prices.items()}
    return dates, price_arrays, np.asarray(monthly_indices, dtype=int), monthly_dates, digest


def load_schedule(path: Path) -> dict[int, list[tuple[str, float]]]:
    schedule: dict[int, list[tuple[str, float]]] = defaultdict(list)
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None and {"month_index", "flow_type", "amount_usd"}.issubset(reader.fieldnames),
                "Flow schedule must expose month_index, flow_type, amount_usd")
        for row in reader:
            month = int(row["month_index"])
            flow_type = row["flow_type"].strip().lower()
            amount = float(row["amount_usd"])
            require(1 <= month <= HORIZON_MONTHS, f"Flow month outside 1..{HORIZON_MONTHS}: {month}")
            require(flow_type in ("deposit", "withdrawal"), f"Unsupported flow type: {flow_type}")
            require(math.isfinite(amount) and amount >= 0.0, f"Invalid flow amount: {amount}")
            schedule[month].append((flow_type, amount))
    return dict(schedule)


def schedule_for(mode: str, irregular: dict[int, list[tuple[str, float]]]):
    if mode == "no_withdrawals":
        return {}
    if mode == "delayed_stepup_example":
        return irregular
    if mode == "monthly_withdrawal_500_usd_stress":
        return {month: [("withdrawal", 500.0)] for month in range(1, HORIZON_MONTHS + 1)}
    if mode == "monthly_withdrawal_1000_usd_stress":
        return {month: [("withdrawal", 1000.0)] for month in range(1, HORIZON_MONTHS + 1)}
    raise ValueError(f"Unknown cashflow mode {mode}")


def replay_group(prices: dict[str, np.ndarray], month_indices: np.ndarray, start_months: np.ndarray,
                 bond: str, target: int, timing: str,
                 schedule: dict[int, list[tuple[str, float]]]) -> dict[str, Any]:
    """Vectorized independent 157-window ledger replay for one strategy/cashflow combination."""
    starts = month_indices[start_months]
    q0, s0 = prices["QQQ"][starts], prices["SPY"][starts]
    uq = INITIAL_CAPITAL * 0.5 / q0
    us = INITIAL_CAPITAL * 0.5 / s0
    ub = np.zeros(starts.size, dtype=float)
    deposits = np.zeros(starts.size, dtype=float)
    requested = np.zeros(starts.size, dtype=float)
    withdrawals = np.zeros(starts.size, dtype=float)
    shortfall = np.zeros(starts.size, dtype=float)
    market_pnl = np.zeros(starts.size, dtype=float)
    previous_after_flow = np.full(starts.size, INITIAL_CAPITAL, dtype=float)
    first_depletion = np.zeros(starts.size, dtype=int)
    yearly: list[dict[str, np.ndarray | int]] = [{
        "year": 0, "nav_usd": np.full(starts.size, round(INITIAL_CAPITAL, 2)),
        "actual_withdrawals_usd": np.zeros(starts.size), "withdrawal_shortfall_usd": np.zeros(starts.size),
        "additional_deposits_usd": np.zeros(starts.size), "target_bond_weight": 0.0, "target_stock_weight": 1.0,
    }]
    for month in range(1, HORIZON_MONTHS + 1):
        ix = month_indices[start_months + month]
        qp, sp, bp = prices["QQQ"][ix], prices["SPY"][ix], prices[bond][ix]
        nav_market = uq * qp + us * sp + ub * bp
        market_pnl += nav_market - previous_after_flow
        for flow_type, amount in schedule.get(month, []):
            nav_now = uq * qp + us * sp + ub * bp
            if flow_type == "deposit":
                live = nav_now > 1e-10
                scale = np.ones(starts.size, dtype=float)
                scale[live] = (nav_now[live] + amount) / nav_now[live]
                uq[live] *= scale[live]
                us[live] *= scale[live]
                ub[live] *= scale[live]
                dead = ~live
                if np.any(dead):
                    weight = target_bond_weight(target, month - 1, timing)
                    sw = 1.0 - weight
                    uq[dead] = amount * sw * 0.5 / qp[dead]
                    us[dead] = amount * sw * 0.5 / sp[dead]
                    ub[dead] = amount * weight / bp[dead]
                deposits += amount
            else:
                requested += amount
                paid = np.minimum(amount, np.maximum(nav_now, 0.0))
                shortfall += amount - paid
                live = (nav_now > 1e-10) & (paid > 0.0)
                scale = np.ones(starts.size, dtype=float)
                scale[live] = (nav_now[live] - paid[live]) / nav_now[live]
                uq[live] *= scale[live]
                us[live] *= scale[live]
                ub[live] *= scale[live]
                withdrawals += paid
        nav_after_flow = uq * qp + us * sp + ub * bp
        newly_depleted = (nav_after_flow <= 1e-8) & (first_depletion == 0)
        first_depletion[newly_depleted] = month
        if month % 12 == 0:
            weight = target_bond_weight(target, month, timing)
            stock_weight = max(0.0, 1.0 - weight)
            safe_nav = np.maximum(nav_after_flow, 0.0)
            uq = safe_nav * stock_weight * 0.5 / qp
            us = safe_nav * stock_weight * 0.5 / sp
            ub = safe_nav * weight / bp
            nav_after_flow = uq * qp + us * sp + ub * bp
            yearly.append({
                "year": month // 12, "nav_usd": np.round(np.maximum(nav_after_flow, 0.0), 2),
                "actual_withdrawals_usd": np.round(withdrawals, 2),
                "withdrawal_shortfall_usd": np.round(shortfall, 2),
                "additional_deposits_usd": np.round(deposits, 2),
                "target_bond_weight": weight, "target_stock_weight": 1.0 - weight,
            })
        previous_after_flow = nav_after_flow
    end_indices = month_indices[start_months + HORIZON_MONTHS]
    terminal = np.maximum(uq * prices["QQQ"][end_indices] + us * prices["SPY"][end_indices] + ub * prices[bond][end_indices], 0.0)
    conservation_error = terminal - (INITIAL_CAPITAL + market_pnl + deposits - withdrawals)
    return {
        "deposits": np.round(deposits, 2), "requested": np.round(requested, 2),
        "withdrawals": np.round(withdrawals, 2), "shortfall": np.round(shortfall, 2),
        "terminal": np.round(terminal, 2),
        "nominal_net_result": np.round(withdrawals + terminal - deposits - INITIAL_CAPITAL, 2),
        "first_depletion": first_depletion, "conservation_error": conservation_error, "yearly": yearly,
    }


def close_money(actual: Any, expected: float, label: str, report: dict) -> None:
    diff = abs(float(actual) - expected)
    report["numeric_field_comparisons"] += 1
    report["max_abs_diff_usd_by_field"][label] = max(report["max_abs_diff_usd_by_field"].get(label, 0.0), diff)
    if diff > USD_TOLERANCE:
        raise AssertionError(f"{label} mismatch: artifact={actual}, independent={expected}, abs_diff={diff:.6f}")


def validate(panel: Path, windows_csv: Path, summary_json: Path, flows_csv: Path, out: Path) -> dict[str, Any]:
    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    require(summary.get("schema") == "stock-bond-glidepath-backtest.v1", "Unexpected summary schema")
    dates, prices, month_indices, month_dates, panel_sha = load_panel(panel, summary)
    irregular = load_schedule(flows_csv)
    require(sum(a for events in irregular.values() for t, a in events if t == "withdrawal") == 12800.0,
            "Irregular schedule withdrawal total changed; review validator assumptions")
    require(sum(a for events in irregular.values() for t, a in events if t == "deposit") == 5000.0,
            "Irregular schedule deposit total changed; review validator assumptions")
    n_windows = int(summary["method"]["rolling_windows_per_scenario"])
    require(n_windows == len(month_indices) - HORIZON_MONTHS, "Summary and panel rolling-window count do not reconcile")
    annual_expected = {}
    annual_rows = summary.get("annual_scenarios")
    require(isinstance(annual_rows, list) and len(annual_rows) == 1024 * 11, "Annual summary must contain 11,264 scenario/year rows")
    for row in annual_rows:
        key = (row["bond_proxy"], int(row["target_bond_conversion_pct_at_year10"]), row["timing_rule"], row["cashflow_mode"], int(row["year"]))
        require(key not in annual_expected, f"Duplicate annual summary row {key}")
        annual_expected[key] = row
    report: dict[str, Any] = {
        "schema": "glidepath-cashflow-ledger-independent-replay.v1", "status": "RUNNING",
        "panel_sha256": panel_sha, "panel_rows": len(dates), "month_end_rows": len(month_indices),
        "rolling_windows_per_scenario": n_windows, "scenario_groups_replayed": 0,
        "scenario_window_rows_replayed": 0, "monthly_account_steps_replayed": 0,
        "accounting_conservation_checks": 0, "annual_summary_groups_checked": 0,
        "annual_nav_flow_metric_comparisons": 0, "numeric_field_comparisons": 0,
        "max_abs_conservation_error_usd": 0.0, "max_abs_diff_usd_by_field": {},
        "window_accounting_fields_checked": ["additional_deposits_usd", "total_capital_supplied_usd", "requested_withdrawals_usd", "actual_withdrawals_usd", "withdrawal_shortfall_usd", "terminal_nav_usd", "nominal_net_result_usd", "first_nav_depletion_month"],
        "annual_aggregate_fields_checked": ["median_nav_usd", "p05_nav_usd", "p95_nav_usd", "worst_nav_usd", "windows_below_initial_capital", "windows_with_withdrawal_shortfall", "median_actual_withdrawals_usd", "median_shortfall_usd", "p95_shortfall_usd", "median_target_bond_weight", "median_target_stock_weight"],
        "excluded_metrics": ["daily_max_drawdown", "time_weighted_cagr", "investor_xirr"],
    }
    expected_scenarios = {(b, t, timing, flow) for b in BOND_TICKERS for t in TARGETS for timing in TIMINGS for flow in FLOWS}
    seen_scenarios: set[tuple] = set()
    seen_rows: set[tuple] = set()
    mode_counts: dict[str, int] = defaultdict(int)
    start_months = np.arange(n_windows, dtype=int)
    start_date_to_index = {day.isoformat(): i for i, day in enumerate(month_dates)}

    # Scenario rows are emitted contiguously by the source workflow; validate this invariant as we stream.
    with windows_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"window_start", "window_end", "bond_proxy", "target_bond_conversion_pct_at_year10", "timing_rule", "cashflow_mode", "initial_capital_usd", "additional_deposits_usd", "total_capital_supplied_usd", "requested_withdrawals_usd", "actual_withdrawals_usd", "withdrawal_shortfall_usd", "terminal_nav_usd", "nominal_net_result_usd", "first_nav_depletion_month", "ending_stock_weight", "ending_bond_weight"}
        require(reader.fieldnames is not None and required_columns.issubset(reader.fieldnames), "Window CSV lacks required account ledger columns")
        iterator = iter(reader)
        pending = next(iterator, None)
        while pending is not None:
            first = pending
            bond, target, timing, mode = first["bond_proxy"], int(first["target_bond_conversion_pct_at_year10"]), first["timing_rule"], first["cashflow_mode"]
            key = (bond, target, timing, mode)
            require(key in expected_scenarios, f"Unexpected scenario key {key}")
            require(key not in seen_scenarios, f"Repeated/non-contiguous scenario group {key}")
            group_rows = [first]
            for _ in range(n_windows - 1):
                nxt = next(iterator, None)
                require(nxt is not None, f"Truncated CSV within scenario {key}")
                nkey = (nxt["bond_proxy"], int(nxt["target_bond_conversion_pct_at_year10"]), nxt["timing_rule"], nxt["cashflow_mode"])
                require(nkey == key, f"Scenario rows are not contiguous/conserved: expected {key}, got {nkey}")
                group_rows.append(nxt)
            starts_expected = [month_dates[i].isoformat() for i in range(n_windows)]
            require([r["window_start"] for r in group_rows] == starts_expected, f"Window starts do not match canonical rolling starts for {key}")
            require([r["window_end"] for r in group_rows] == [month_dates[i + HORIZON_MONTHS].isoformat() for i in range(n_windows)], f"Window ends mismatch for {key}")
            result = replay_group(prices, month_indices, start_months, bond, target, timing, schedule_for(mode, irregular))
            for i, row in enumerate(group_rows):
                ident = (*key, row["window_start"])
                require(ident not in seen_rows, f"Duplicate window row {ident}")
                seen_rows.add(ident)
                mode_counts[mode] += 1
                close_money(row["initial_capital_usd"], INITIAL_CAPITAL, "initial_capital_usd", report)
                close_money(row["additional_deposits_usd"], float(result["deposits"][i]), "additional_deposits_usd", report)
                close_money(row["total_capital_supplied_usd"], INITIAL_CAPITAL + float(result["deposits"][i]), "total_capital_supplied_usd", report)
                close_money(row["requested_withdrawals_usd"], float(result["requested"][i]), "requested_withdrawals_usd", report)
                close_money(row["actual_withdrawals_usd"], float(result["withdrawals"][i]), "actual_withdrawals_usd", report)
                close_money(row["withdrawal_shortfall_usd"], float(result["shortfall"][i]), "withdrawal_shortfall_usd", report)
                close_money(row["terminal_nav_usd"], float(result["terminal"][i]), "terminal_nav_usd", report)
                close_money(row["nominal_net_result_usd"], float(result["nominal_net_result"][i]), "nominal_net_result_usd", report)
                expected_depletion = "" if result["first_depletion"][i] == 0 else str(int(result["first_depletion"][i]))
                require(row["first_nav_depletion_month"].strip() == expected_depletion, f"First depletion mismatch for {ident}: CSV={row['first_nav_depletion_month']!r}, replay={expected_depletion!r}")
                require(abs(float(row["ending_stock_weight"]) - (1.0 - target / 100.0)) < 1e-10, f"Ending stock target mismatch for {ident}")
                require(abs(float(row["ending_bond_weight"]) - target / 100.0) < 1e-10, f"Ending bond target mismatch for {ident}")
            max_conservation = float(np.max(np.abs(result["conservation_error"])))
            report["max_abs_conservation_error_usd"] = max(report["max_abs_conservation_error_usd"], max_conservation)
            require(max_conservation < 1e-5, f"Account conservation failed for scenario {key}: max error {max_conservation}")
            report["accounting_conservation_checks"] += n_windows
            report["scenario_window_rows_replayed"] += n_windows
            report["monthly_account_steps_replayed"] += n_windows * HORIZON_MONTHS
            for mark in result["yearly"]:
                annual_key = (*key, int(mark["year"]))
                require(annual_key in annual_expected, f"Missing annual summary group {annual_key}")
                navs = np.asarray(mark["nav_usd"], dtype=float)
                withdrawals = np.asarray(mark["actual_withdrawals_usd"], dtype=float)
                shortfalls = np.asarray(mark["withdrawal_shortfall_usd"], dtype=float)
                metrics = {
                    "median_nav_usd": round(quantile(navs, 0.50), 2),
                    "p05_nav_usd": round(quantile(navs, 0.05), 2),
                    "p95_nav_usd": round(quantile(navs, 0.95), 2),
                    "worst_nav_usd": round(float(np.min(navs)), 2),
                    "windows_below_initial_capital": int(np.sum(navs < INITIAL_CAPITAL)),
                    "windows_with_withdrawal_shortfall": int(np.sum(shortfalls > 0.01)),
                    "median_actual_withdrawals_usd": round(quantile(withdrawals, 0.50), 2),
                    "median_shortfall_usd": round(quantile(shortfalls, 0.50), 2),
                    "p95_shortfall_usd": round(quantile(shortfalls, 0.95), 2),
                    "median_target_bond_weight": float(mark["target_bond_weight"]),
                    "median_target_stock_weight": float(mark["target_stock_weight"]),
                }
                annual_row = annual_expected[annual_key]
                for field, value in metrics.items():
                    if field in {"windows_below_initial_capital", "windows_with_withdrawal_shortfall"}:
                        require(int(annual_row[field]) == value, f"Annual {field} mismatch at {annual_key}: summary={annual_row[field]}, replay={value}")
                    elif field in {"median_target_bond_weight", "median_target_stock_weight"}:
                        require(abs(float(annual_row[field]) - value) < 1e-10, f"Annual {field} mismatch at {annual_key}: summary={annual_row[field]}, replay={value}")
                    else:
                        close_money(annual_row[field], value, "annual." + field, report)
                    report["annual_nav_flow_metric_comparisons"] += 1
                report["annual_summary_groups_checked"] += 1
            seen_scenarios.add(key)
            report["scenario_groups_replayed"] += 1
            pending = next(iterator, None)

    require(seen_scenarios == expected_scenarios, f"Scenario key coverage mismatch: missing={len(expected_scenarios-seen_scenarios)} extra={len(seen_scenarios-expected_scenarios)}")
    require(report["scenario_window_rows_replayed"] == len(expected_scenarios) * n_windows, "Window row count mismatch")
    require(set(mode_counts) == set(FLOWS) and all(count == 4 * 8 * 8 * n_windows for count in mode_counts.values()), f"Unexpected cashflow mode distribution: {dict(mode_counts)}")
    require(report["annual_summary_groups_checked"] == 11264, "Annual summary group count mismatch")
    report["cashflow_mode_window_rows"] = dict(sorted(mode_counts.items()))
    report["status"] = "PASSED"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--windows", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--flows-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.panel, args.windows, args.summary, args.flows_csv, args.out)
    keys = ("status", "panel_rows", "month_end_rows", "scenario_groups_replayed", "scenario_window_rows_replayed", "monthly_account_steps_replayed", "accounting_conservation_checks", "annual_summary_groups_checked", "annual_nav_flow_metric_comparisons", "numeric_field_comparisons", "max_abs_conservation_error_usd", "max_abs_diff_usd_by_field")
    print(json.dumps({k: result[k] for k in keys}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
