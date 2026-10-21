#!/usr/bin/env python3
"""Pack an independently verified eight-timing Stage 2 replay into canonical v2.html.

This command deliberately accepts generated research outputs as inputs. It does not
invent annual marks, histogram bins, cohort data, or capital-floor counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
EXPECTED_SCHEMA = "stock-bond-glidepath-backtest.v1"
BONDS = ("AGG", "SHY", "IEF", "TLT")
TARGETS = (30, 40, 50, 60, 70, 80, 90, 100)
TIMINGS = ("front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late")
FLOWS = ("no_withdrawals", "delayed_stepup_example", "monthly_withdrawal_500_usd_stress", "monthly_withdrawal_1000_usd_stress")
METRICS = ("terminal_nav_usd", "time_weighted_cagr", "daily_max_drawdown", "withdrawal_shortfall_usd")
PACK_RE = re.compile(r"const RAW_PACK=(\{.*?\});\s*const TG=", re.S)
TIMING_OPTIONS_RE = re.compile(r'<select id="timing">.*?</select>', re.S)
ARRAYS_RE = re.compile(r'const TG=\[[^\n]+;\nconst TN=\{[^\n]+', re.S)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def finite_or_none(value: Any, label: str) -> float | None:
    if value is None:
        return None
    number = float(value)
    require(math.isfinite(number), f"{label} must be finite or null")
    return number

def rounded(value: Any, digits: int = 6) -> float | None:
    number = finite_or_none(value, "packed numeric value")
    return None if number is None else round(number, digits)

def scenario_key(row: dict[str, Any]) -> tuple[str, int, str, str]:
    return (
        str(row["bond_proxy"]),
        int(row["target_bond_conversion_pct_at_year10"]),
        str(row["timing_rule"]),
        str(row["cashflow_mode"]),
    )

def expected_keys() -> list[tuple[str, int, str, str]]:
    return [(bond, target, timing, flow)
            for bond in BONDS for target in TARGETS
            for timing in TIMINGS for flow in FLOWS]

def index4(key: tuple[str, int, str, str]) -> list[int]:
    bond, target, timing, flow = key
    return [BONDS.index(bond), target, TIMINGS.index(timing), FLOWS.index(flow)]

def validate_and_pack(report: dict[str, Any], histogram_report: dict[str, Any],
                      cohort_report: dict[str, Any],
                      ledger_replay_report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("schema") == EXPECTED_SCHEMA, "Unexpected Stage 2 backtest schema")
    method = report.get("method", {})
    data = report.get("data", {})
    windows = int(method.get("rolling_windows_per_scenario", 0))
    initial = finite_or_none(method.get("initial_capital_usd"), "initial_capital_usd")
    require(windows == 157, f"Expected 157 overlapping windows, got {windows}")
    require(initial is not None and initial > 0, "Initial capital is missing or invalid")
    require(tuple(method.get("timing_rules", {}).keys()) == TIMINGS,
            "Stage 2 report does not declare all eight timing rules in the canonical order")
    require(data.get("last_common_date") == "2026-09-30",
            "The verified Stage 2 pack must end on the pinned common date 2026-09-30")
    source_sha = str(data.get("raw_panel_canonical_sha256", ""))
    require(re.fullmatch(r"[0-9a-f]{64}", source_sha) is not None,
            "Source panel SHA-256 is missing or malformed")
    require(int(data.get("common_month_end_observations", 0)) == 277,
            "Expected 277 common monthly observations")

    scenario_rows = report.get("scenarios", [])
    annual_rows = report.get("annual_scenarios", [])
    keys = expected_keys()
    require(len(scenario_rows) == len(keys) == 1024,
            f"Expected all 1,024 scenario rows, got {len(scenario_rows)}")
    by_scenario: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    for row in scenario_rows:
        key = scenario_key(row)
        require(key not in by_scenario, f"Duplicate scenario key: {key}")
        require(key in set(keys), f"Unexpected scenario key: {key}")
        require(int(row.get("rolling_windows", -1)) == windows,
                f"Wrong rolling-window count for {key}")
        by_scenario[key] = row
    require(set(by_scenario) == set(keys), "Scenario grid is incomplete")

    annual_keyed: dict[tuple[str, int, str, str, int], dict[str, Any]] = {}
    for row in annual_rows:
        key4 = scenario_key(row)
        year = int(row["year"])
        require(year in range(11), f"Invalid year index {year}")
        key = (*key4, year)
        require(key not in annual_keyed, f"Duplicate annual record: {key}")
        require(key4 in by_scenario, f"Annual record has no scenario summary: {key}")
        require(int(row.get("rolling_windows", -1)) == windows,
                f"Wrong annual rolling-window count: {key}")
        annual_keyed[key] = row
    require(len(annual_rows) == 11264 and len(annual_keyed) == 11264,
            f"Expected 11,264 unique annual records, got {len(annual_keyed)}")
    require(set(annual_keyed) == {(*key, year) for key in keys for year in range(11)},
            "Annual grid is missing one or more strategy/year combinations")

    require(ledger_replay_report.get("schema") == "glidepath-window-cashflow-ledger-replay.v1" and
            ledger_replay_report.get("status") == "PASS",
            "Independent cashflow-ledger replay must publish PASS before real-principal counts can be embedded")
    require(ledger_replay_report.get("source_panel_sha256") == source_sha and
            ledger_replay_report.get("source_as_of") == data.get("last_common_date") and
            int(ledger_replay_report.get("rolling_windows_per_scenario", 0)) == windows,
            "Independent real-principal counts differ from the pinned price source/window protocol")
    ledger_counts = ledger_replay_report.get("counters", {})
    require(ledger_counts.get("window_rows_replayed") == 160768 and
            ledger_counts.get("annual_rows_reconciled") == 11264 and
            ledger_counts.get("scenario_summaries_reconciled") == 1024 and
            ledger_counts.get("real_floor_annual_rows") == 11264,
            "Independent ledger replay does not cover the full window and annual real-principal grid")
    require(ledger_replay_report.get("real_floor_annual_count_rates") == [0.0235, 0.035],
            "Independent real-principal counts must contain exactly the 2.35% and 3.50% assumptions")
    real_floor_rows = ledger_replay_report.get("real_floor_annual_counts", [])
    real_floor_by_key: dict[tuple[str, int, str, str, int], tuple[int, int]] = {}
    for item in real_floor_rows:
        require(isinstance(item, list) and len(item) == 7 and all(isinstance(value, int) for value in item),
                "Malformed real-principal count row")
        year, bond_index, target, timing_index, flow_index, count235, count350 = item
        require(year in range(11) and bond_index in range(len(BONDS)) and target in TARGETS and
                timing_index in range(len(TIMINGS)) and flow_index in range(len(FLOWS)),
                f"Invalid real-principal count key: {item}")
        key = (BONDS[bond_index], target, TIMINGS[timing_index], FLOWS[flow_index], year)
        require(key not in real_floor_by_key, f"Duplicate real-principal count key: {key}")
        require(0 <= count235 <= windows and 0 <= count350 <= windows,
                f"Real-principal breach count outside 0–{windows}: {key}")
        if year == 0:
            require(count235 == 0 and count350 == 0,
                    f"Year-zero real-principal breach counts must be zero: {key}")
        real_floor_by_key[key] = (count235, count350)
    require(len(real_floor_rows) == 11264 and set(real_floor_by_key) == set(annual_keyed),
            "Independent real-principal count grid must contain one row for every strategy/year key")

    # Treat allocation targets, portfolio NAV, and external cash flows as separate
    # quantities. They must reconcile to one scenario/year key, never be inferred
    # from a label or borrowed from the no-withdrawal baseline.
    paths: dict[tuple[str, int, str], dict[str, tuple[float, ...]]] = {}
    paths_by_cashflow: dict[tuple[str, int, str], dict[str, tuple[float, ...]]] = {}
    for key in keys:
        summary = by_scenario[key]
        path_marks: list[tuple[int, float]] = []
        prior_cashflow_values = {
            "median_actual_withdrawals_usd": 0.0,
            "median_shortfall_usd": 0.0,
            "p95_shortfall_usd": 0.0,
            "windows_with_withdrawal_shortfall": 0,
        }
        for year in range(11):
            row = annual_keyed[(*key, year)]
            bond_w = finite_or_none(row.get("median_target_bond_weight"), f"{key}/{year} bond weight")
            stock_w = finite_or_none(row.get("median_target_stock_weight"), f"{key}/{year} stock weight")
            require(bond_w is not None and stock_w is not None, f"Missing annual weights: {key}/{year}")
            require(-1e-9 <= bond_w <= 1+1e-9 and -1e-9 <= stock_w <= 1+1e-9,
                    f"Annual weight outside 0–100%: {key}/{year}")
            require(abs(bond_w + stock_w - 1.0) <= 1e-8,
                    f"Stock/bond weights do not sum to 100%: {key}/{year}")
            path_marks.append((year, bond_w))

            nav_fields = ("median_nav_usd", "p05_nav_usd", "p95_nav_usd", "worst_nav_usd")
            nav_values = {
                field: finite_or_none(row.get(field), f"{key}/{year} {field}")
                for field in nav_fields
            }
            require(all(value is not None and value >= 0 for value in nav_values.values()),
                    f"Annual NAV values must be finite and non-negative: {key}/{year}")

            flow_fields = ("median_actual_withdrawals_usd", "median_shortfall_usd", "p95_shortfall_usd")
            flow_values = {
                field: finite_or_none(row.get(field), f"{key}/{year} {field}")
                for field in flow_fields
            }
            require(all(value is not None and value >= -0.01 for value in flow_values.values()),
                    f"Cashflow values must be finite and non-negative: {key}/{year}")
            require(float(flow_values["p95_shortfall_usd"]) + 0.01 >=
                    float(flow_values["median_shortfall_usd"]),
                    f"P95 shortfall is below the median shortfall: {key}/{year}")
            shortfall_windows = int(row.get("windows_with_withdrawal_shortfall", -1))
            require(0 <= shortfall_windows <= windows,
                    f"Shortfall-window count is outside 0–{windows}: {key}/{year}")

            if year == 0:
                require(row.get("median_cumulative_twr_cagr") is None,
                        f"Year zero must not report elapsed-period CAGR: {key}")
                for field, value in nav_values.items():
                    require(abs(float(value) - float(initial)) <= 0.02,
                            f"Year-zero {field} must equal starting NAV {initial}: {key}")
                require(all(abs(float(value)) <= 0.01 for value in flow_values.values()) and shortfall_windows == 0,
                        f"Year zero cannot already show withdrawals or a cashflow shortfall: {key}")
            else:
                for field, value in flow_values.items():
                    require(float(value) + 0.01 >= prior_cashflow_values[field],
                            f"Cumulative cashflow field regressed from year {year-1} to {year}: {key}/{field}")
                require(shortfall_windows >= prior_cashflow_values["windows_with_withdrawal_shortfall"],
                        f"Cumulative shortfall-window count regressed: {key}/{year}")
            prior_cashflow_values = {
                **{field: float(value) for field, value in flow_values.items()},
                "windows_with_withdrawal_shortfall": shortfall_windows,
            }

            if key[3] == "no_withdrawals":
                require(all(abs(float(value)) <= 0.01 for value in flow_values.values()) and shortfall_windows == 0,
                        f"No-withdrawal mode must not report actual withdrawals or shortfalls: {key}/{year}")

            if year == 10:
                field_pairs = (
                    ("median_nav_usd", "median_terminal_nav_usd"),
                    ("p05_nav_usd", "p05_terminal_nav_usd"),
                    ("p95_nav_usd", "p95_terminal_nav_usd"),
                    ("worst_nav_usd", "worst_terminal_nav_usd"),
                )
                for annual_field, summary_field in field_pairs:
                    require(abs(float(row[annual_field]) - float(summary[summary_field])) <= 0.02,
                            f"Year-10 {annual_field} does not reconcile to {summary_field}: {key}")
                cagr_a = row.get("median_cumulative_twr_cagr")
                cagr_s = summary.get("median_time_weighted_cagr")
                if cagr_a is not None and cagr_s is not None:
                    require(abs(float(cagr_a)-float(cagr_s)) <= 1e-8,
                            f"Year-10 CAGR does not reconcile: {key}")
                p05_cagr_a = row.get("p05_cumulative_twr_cagr")
                p05_cagr_s = summary.get("p05_time_weighted_cagr")
                if p05_cagr_a is not None and p05_cagr_s is not None:
                    require(abs(float(p05_cagr_a)-float(p05_cagr_s)) <= 1e-8,
                            f"Year-10 P05 CAGR does not reconcile: {key}")
                require(abs(float(row["median_drawdown_to_date"]) -
                            float(summary["median_daily_max_drawdown"])) <= 1e-8,
                        f"Year-10 drawdown does not reconcile: {key}")
                require(int(row["windows_with_withdrawal_shortfall"]) ==
                        int(summary["windows_with_withdrawal_shortfall"]),
                        f"Year-10 shortfall count does not reconcile: {key}")
                require(abs(float(row["median_actual_withdrawals_usd"]) -
                            float(summary["median_actual_withdrawals_usd"])) <= 0.02,
                        f"Year-10 actual withdrawals do not reconcile: {key}")
                require(abs(float(row["p95_shortfall_usd"]) -
                            float(summary["p95_withdrawal_shortfall_usd"])) <= 0.02,
                        f"Year-10 P95 shortfall does not reconcile: {key}")
                require(int(row["windows_below_initial_capital"]) ==
                        int(summary["windows_below_initial_capital_at_year10"]),
                        f"Year-10 below-initial-capital count does not reconcile: {key}")
                if key[3] == "no_withdrawals":
                    require(abs(float(summary["median_actual_withdrawals_usd"])) <= 0.01 and
                            abs(float(summary["p95_withdrawal_shortfall_usd"])) <= 0.01 and
                            int(summary["windows_with_withdrawal_shortfall"]) == 0,
                            f"No-withdrawal scenario summary contains cashflows or shortfalls: {key}")

        path = tuple(round(weight, 9) for _, weight in sorted(path_marks))
        group_key = (key[0], key[1], key[3])
        paths.setdefault(group_key, {})[key[2]] = path
        crossflow_key = (key[0], key[1], key[2])
        paths_by_cashflow.setdefault(crossflow_key, {})[key[3]] = path
    for (bond, target, flow), timing_paths in paths.items():
        require(set(timing_paths) == set(TIMINGS), f"Missing timing paths: {bond}/{target}/{flow}")
        require(len(set(timing_paths.values())) == 8,
                f"The eight timings must have eight distinct annual paths: {bond}/{target}/{flow}")
        for timing, path in timing_paths.items():
            require(len(path) == 11 and abs(path[0]) <= 1e-9,
                    f"Path must contain years 0–10 and start at 0% bonds: {bond}/{target}/{flow}/{timing}")
            require(abs(path[-1] - target/100.0) <= 1e-8,
                    f"Path must finish at the year-10 target: {bond}/{target}/{flow}/{timing}")
            require(all(a <= b + 1e-9 for a,b in zip(path,path[1:])),
                    f"Bond target path cannot decrease: {bond}/{target}/{flow}/{timing}")
    for (bond, target, timing), cashflow_paths in paths_by_cashflow.items():
        require(set(cashflow_paths) == set(FLOWS),
                f"Annual allocation path is missing a cashflow mode: {bond}/{target}/{timing}")
        require(len(set(cashflow_paths.values())) == 1,
                f"Changing cashflow mode must not silently change the target-allocation schedule: {bond}/{target}/{timing}")

    hist_rows = histogram_report.get("distributions", [])
    require(histogram_report.get("schema") == "stock-bond-glidepath-window-distributions.v1",
            "Unexpected histogram schema")
    require(int(histogram_report.get("rolling_windows_per_scenario", 0)) == windows,
            "Histogram report uses a different rolling-window count")
    hist_keyed: dict[tuple[str, int, str, str, str], dict[str, Any]] = {}
    for row in hist_rows:
        key4 = scenario_key(row)
        metric = str(row["metric"])
        key = (*key4, metric)
        require(key4 in by_scenario and metric in METRICS, f"Unexpected histogram group: {key}")
        require(key not in hist_keyed, f"Duplicate histogram group: {key}")
        n = int(row.get("n", 0))
        bins = row.get("bins", [])
        require(n == windows and bins, f"Histogram does not cover all windows: {key}")
        counts = [int(item["count"]) for item in bins]
        require(all(count >= 0 for count in counts) and sum(counts) == n,
                f"Histogram bins do not conserve all observations: {key}")
        low, high = finite_or_none(row.get("min"), "histogram min"), finite_or_none(row.get("max"), "histogram max")
        require(low is not None and high is not None and low <= high, f"Invalid histogram range: {key}")
        require(abs(float(bins[0]["low"])-low) <= 1e-6 and abs(float(bins[-1]["high"])-high) <= 1e-6,
                f"Histogram edge bounds do not match min/max: {key}")
        if len(bins) > 1 and high > low:
            step = (high-low)/len(bins)
            for i,item in enumerate(bins):
                expect_low = low + i*step
                expect_high = high if i == len(bins)-1 else low+(i+1)*step
                require(abs(float(item["low"])-expect_low) <= max(1e-6, abs(expect_low)*1e-8) and
                        abs(float(item["high"])-expect_high) <= max(1e-6, abs(expect_high)*1e-8),
                        f"Compact histogram requires equal-width bins: {key}")
        hist_keyed[key] = row
    expected_hist_keys = {(*key, metric) for key in keys for metric in METRICS}
    require(len(hist_rows) == 4096 and set(hist_keyed) == expected_hist_keys,
            f"Expected 4,096 complete histogram groups, got {len(hist_keyed)}")

    cohort_rows = cohort_report.get("cohorts", [])
    require(cohort_report.get("schema") == "stock-bond-glidepath-start-cohorts.v1",
            "Unexpected cohort schema")
    require(int(cohort_report.get("rolling_windows_per_scenario", 0)) == windows,
            "Cohort report uses a different rolling-window count")
    cohort_years = sorted({int(row["start_year"]) for row in cohort_rows})
    require(cohort_years, "No start-year cohorts in report")
    cohort_keyed: dict[tuple[str, int, str, str, int], dict[str, Any]] = {}
    cm: dict[str, list[Any]] = {}
    for row in cohort_rows:
        key4 = scenario_key(row)
        year = int(row["start_year"])
        key = (*key4, year)
        require(key4 in by_scenario and year in cohort_years, f"Unexpected cohort record: {key}")
        require(key not in cohort_keyed, f"Duplicate cohort record: {key}")
        count = int(row["window_count"])
        first, last = str(row["first_window_start"]), str(row["last_window_start"])
        require(count > 0 and first[:4] == str(year) and last[:4] == str(year) and first <= last,
                f"Invalid cohort start range: {key}")
        candidate = [count, first, last]
        if str(year) in cm:
            require(cm[str(year)] == candidate, f"Cohort metadata differs by strategy for {year}")
        else:
            cm[str(year)] = candidate
        cohort_keyed[key] = row
    expected_cohort_keys = {(*key, year) for key in keys for year in cohort_years}
    require(len(cohort_rows) == len(expected_cohort_keys) == 1024*len(cohort_years) and
            set(cohort_keyed) == expected_cohort_keys,
            "Cohort records do not form the same start-year grid for all 1,024 strategies")
    counts_by_scenario: dict[tuple[str,int,str,str], int] = {}
    for key, row in cohort_keyed.items():
        key4 = key[:4]
        counts_by_scenario[key4] = counts_by_scenario.get(key4, 0) + int(row["window_count"])
    require(set(counts_by_scenario) == set(keys) and all(v == windows for v in counts_by_scenario.values()),
            "Start-year cohort counts fail to conserve 157 windows for each strategy")

    # Preserve the compact field order consumed by v2.html's renderer.
    d = []
    for key in keys:
        row = by_scenario[key]
        d.append(index4(key) + [
            rounded(row["median_terminal_nav_usd"], 2),
            rounded(row["p05_terminal_nav_usd"], 2),
            rounded(row["p95_terminal_nav_usd"], 2),
            rounded(row["worst_terminal_nav_usd"], 2),
            rounded(row.get("median_time_weighted_cagr")),
            rounded(row.get("p05_time_weighted_cagr")),
            rounded(row.get("worst_time_weighted_cagr")),
            rounded(row["median_daily_max_drawdown"]),
            rounded(row["worst_daily_max_drawdown"]),
            int(row["windows_below_initial_capital_at_year10"]),
            int(row["windows_with_withdrawal_shortfall"]),
            rounded(row["median_actual_withdrawals_usd"], 2),
            rounded(row["p95_withdrawal_shortfall_usd"], 2),
            rounded(row.get("median_investor_xirr")),
        ])
    a = []
    for year in range(11):
        for key in keys:
            row = annual_keyed[(*key, year)]
            a.append([year, *index4(key)[0:1], index4(key)[1], index4(key)[2], index4(key)[3]] + [
                rounded(row["median_nav_usd"], 2), rounded(row["p05_nav_usd"], 2),
                rounded(row["p95_nav_usd"], 2), rounded(row["worst_nav_usd"], 2),
                rounded(row.get("median_cumulative_twr_cagr")), rounded(row.get("p05_cumulative_twr_cagr")),
                rounded(row.get("median_year_twr")), rounded(row.get("p05_year_twr")),
                rounded(row["median_drawdown_to_date"]), rounded(row["worst_drawdown_to_date"]),
                int(row["windows_below_initial_capital"]), int(row["windows_with_withdrawal_shortfall"]),
                rounded(row["median_actual_withdrawals_usd"], 2), rounded(row["median_shortfall_usd"], 2),
                rounded(row["p95_shortfall_usd"], 2), rounded(row["median_target_bond_weight"]),
                real_floor_by_key[(*key, year)][0], real_floor_by_key[(*key, year)][1],
            ])
    h = []
    for key in keys:
        for metric in METRICS:
            row = hist_keyed[(*key, metric)]
            h.append(index4(key) + [METRICS.index(metric),
                rounded(row["min"]), rounded(row["max"]), rounded(row["p05"]),
                rounded(row["median"]), rounded(row["p95"]),
                [int(item["count"]) for item in row["bins"]]])
    cohort = []
    for key in keys:
        for year in cohort_years:
            row = cohort_keyed[(*key, year)]
            cohort.append(index4(key) + [year,
                rounded(row["median_terminal_nav_usd"], 2), rounded(row["p05_terminal_nav_usd"], 2),
                rounded(row["p95_terminal_nav_usd"], 2), rounded(row["worst_terminal_nav_usd"], 2),
                rounded(row.get("median_time_weighted_cagr")), rounded(row.get("p05_time_weighted_cagr")),
                rounded(row.get("worst_time_weighted_cagr")), rounded(row.get("median_daily_max_drawdown")),
                rounded(row.get("worst_daily_max_drawdown")), int(row["windows_with_withdrawal_shortfall"]),
                int(row["windows_below_initial_capital"])])
    meta = {
        "source_as_of": str(data["last_common_date"]),
        "source_sha256": source_sha,
        "daily_common_observations": int(data["daily_common_observations"]),
        "common_month_end_observations": int(data["common_month_end_observations"]),
        "initial_capital_usd": round(initial, 2),
        "rolling_windows_per_scenario": windows,
        "cohort_years": cohort_years,
    }
    return {"cm": cm, "d": d, "a": a, "h": h, "c": cohort, "meta": meta}

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)

def embed_pack(html: str, pack: dict[str, Any]) -> str:
    matches = list(PACK_RE.finditer(html))
    require(len(matches) == 1, f"Expected exactly one RAW_PACK declaration, found {len(matches)}")
    payload = json.dumps(pack, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    html = PACK_RE.sub(lambda m: "const RAW_PACK=" + payload + ";\nconst TG=", html, count=1)

    old_selector = TIMING_OPTIONS_RE.findall(html)
    require(len(old_selector) == 1, "Expected exactly one timing selector")
    new_selector = """<select id="timing">
        <option value="front_rapid">急速前置：第1年半程</option>
        <option selected value="front_fast">加速前置：第2年半程</option>
        <option value="front_loaded">前置：第3年半程</option>
        <option value="linear">線性：每年等量</option>
        <option value="mid_loaded">中段加速：S曲線</option>
        <option value="staggered">分段：第2／5／8年達25／50／75%</option>
        <option value="back_loaded">後置：第5年開始</option>
        <option value="back_late">延後：第7年開始</option>
      </select>"""
    html = TIMING_OPTIONS_RE.sub(lambda _: new_selector, html, count=1)

    old_arrays_start = re.search(r'const TG=\[[^\n]+;\nconst TN=\{[^\n]+', html)
    require(old_arrays_start is not None, "Could not find the compact UI timing arrays")
    new_arrays = '''const TG=[30,40,50,60,70,80,90,100],TM=["front_rapid","front_fast","front_loaded","linear","mid_loaded","staggered","back_loaded","back_late"],FL=["no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress"],BM=["AGG","SHY","IEF","TLT"],MM=["terminal_nav_usd","time_weighted_cagr","daily_max_drawdown","withdrawal_shortfall_usd"];
const TN={front_rapid:"急速前置",front_fast:"加速前置",front_loaded:"前置",linear:"線性",mid_loaded:"中段S曲線",staggered:"分段轉換",back_loaded:"後置",back_late:"延後"},FN={no_withdrawals:"不提款",delayed_stepup_example:"延遲步進提款＋後續投入",monthly_withdrawal_500_usd_stress:"每月$500",monthly_withdrawal_1000_usd_stress:"每月$1,000"},C={blue:"#3977a8",teal:"#329b8a",orange:"#d97706",crimson:"#dc2626",AGG:"#3274a1",SHY:"#2a9d8f",IEF:"#e07a35",TLT:"#7966a8",front_rapid:"#9c2f55",front_fast:"#c94c4c",front_loaded:"#dd8547",linear:"#3274a1",mid_loaded:"#59a14f",staggered:"#6f9f76",back_loaded:"#8c78bd",back_late:"#b07aa1",grid:"#e8edf3",muted:"#718096",navy:"#203a59"};'''
    html = html[:old_arrays_start.start()] + new_arrays + html[old_arrays_start.end():]


    # Real-principal counts come from the independent replay, not from NAV quantiles.
    html = replace_once(html,
        "median_target_bond_weight:bw,median_target_stock_weight:sw};",
        "median_target_bond_weight:bw,median_target_stock_weight:sw,windows_below_real_principal_235:r[21],windows_below_real_principal_350:r[22]};",
        "annual real-principal properties")
    html = replace_once(html,
        '[s.cpi>0?"實質保本窗口（未精算）":"名目低於本金窗口",s.cpi>0?"不可精算":r.windows_below_initial_capital+"/"+r.rolling_windows,s.cpi>0?"缺少逐窗口 NAV，不把名目計數冒充實質計數；"+floorLabel:"名目 NAV 低於起始 $100,000 的歷史窗口數；不是未來機率"],',
        '[s.cpi>0?"低於實質本金窗口":"名目低於本金窗口",s.cpi>0?(s.cpi>=0.03?r.windows_below_real_principal_350:r.windows_below_real_principal_235)+"/"+r.rolling_windows:r.windows_below_initial_capital+"/"+r.rolling_windows,s.cpi>0?"逐窗口年末 NAV 比較通膨調整本金門檻；"+floorLabel+"；提款後只計剩餘 NAV":"名目 NAV 低於起始 $100,000 的歷史窗口數；不是未來機率"],',
        "real-principal metric card")
    html = replace_once(html,
        "(s.cpi>0?'實質保本窗口（未精算）':'名目低於本金')",
        "(s.cpi>0?'低於實質本金窗口':'名目低於本金')",
        "real-principal table header")
    html = replace_once(html,
        "(s.cpi>0?'未精算（名目 '+v.windows_below_initial_capital+'/'+v.rolling_windows+'）':v.windows_below_initial_capital+'/'+v.rolling_windows)",
        "(s.cpi>0?(s.cpi>=0.03?v.windows_below_real_principal_350:v.windows_below_real_principal_235)+'/'+v.rolling_windows:v.windows_below_initial_capital+'/'+v.rolling_windows)",
        "real-principal table count")
    html = replace_once(html,
        '      "年通脹 2.35% 時，768 組第10年策略中有 363 組可由最差窗口期末 NAV 證明「157 個歷史窗口均未跌破實質本金」；年通脹 3.50% 時是 329 組。這只代表第10年期末門檻，不代表途中不回撤或未來保本機率。" +\n      " 其餘未獲零跌破證明的策略，不代表已知它們全部跌破；精確實質跌破窗口數尚未全部逐窗口精算，頁面會標「未精算」，不把名目數字假裝成實質風險。";',
        '      "年通脹 2.35% 時，1,024 組第10年策略中有 " + RAW_PACK.a.filter(row => Number(row[0]) === 10 && Number(row[21]) === 0).length + " 組逐窗口核算確認零實質本金缺口；年通脹 3.50% 時是 " + RAW_PACK.a.filter(row => Number(row[0]) === 10 && Number(row[22]) === 0).length + " 組。這只代表第10年期末門檻，不代表途中不回撤或未來保本機率。" +\n      " 各策略在每個年份的實質本金缺口均已由獨立逐窗口重播計算；表格顯示該年期末 NAV 低於通膨調整本金門檻的窗口數。提款情境只計剩餘 NAV，不把已取走的現金加回；157 個重疊窗口不是未來機率。";',
        "real-principal dynamic zero-breach evidence")

    old_counts = "✓ 768 組策略 · 8,448 筆年度摘要"
    html = html.replace(old_counts, "✓ 1,024 組策略 · 11,264 筆年度摘要")
    html = html.replace("六條轉換曲線", "八條轉換曲線")
    html = html.replace("六種轉換時間規則", "八種轉換時間規則")
    html = html.replace("目標 × 6 規則", "目標 × 8 規則")
    html = html.replace("（共 48 格）", "（共 64 格）")
    html = html.replace("共 192 點＝4 種債券 × 8 目標 × 6 規則", "共 256 點＝4 種債券 × 8 目標 × 8 規則")
    html = html.replace("共 192 點", "共 256 點")
    html = html.replace(
        "○ 線性　□ 加速前置　△ 前置　◇ 中段S曲線　▽ 後置　＋ 延後",
        "◇ 急速前置　□ 加速前置　△ 前置　○ 線性　◆ 中段S曲線　⬟ 分段轉換　▽ 後置　＋ 延後"
    )
    html = html.replace(
        "本預覽保留 768 組策略、8,448 筆年度摘要、3,072 組分布與 10,752 筆起始年份分組。",
        "本預覽保留 1,024 組策略、11,264 筆年度摘要、4,096 組分布與 " + f"{len(pack['c']):,}" + " 筆起始年份分組。"
    )
    html = html.replace("8d34a8772fd5c74a7df20957cab971c3c2685963e54b160c3c958c8b9d4b7e70", str(pack["meta"]["source_sha256"]))
    # Keep the independent reverse replay source/date disclosure separate from the forward dataset.

    # Draw eight timing rules with distinct point symbols and line styles.
    old_shape = """let shape=r.timing_rule,mark;
    if(shape==="front_fast")mark='<rect x="'+(x-3.5).toFixed(1)+'" y="'+(y-3.5).toFixed(1)+'" width="7" height="7"';
    else if(shape==="front_loaded")mark='<polygon points="'+x.toFixed(1)+','+(y-4.5).toFixed(1)+' '+(x-4.5).toFixed(1)+','+(y+3.5).toFixed(1)+' '+(x+4.5).toFixed(1)+','+(y+3.5).toFixed(1)+'"';
    else if(shape==="linear")mark='<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+(sel?5.2:3.3)+'"';
    else if(shape==="mid_loaded")mark='<polygon points="'+x.toFixed(1)+','+(y-5).toFixed(1)+' '+(x-5).toFixed(1)+','+y.toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+' '+(x+5).toFixed(1)+','+y.toFixed(1)+'"';
    else if(shape==="back_loaded")mark='<polygon points="'+(x-4.5).toFixed(1)+','+(y-3.5).toFixed(1)+' '+(x+4.5).toFixed(1)+','+(y-3.5).toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+'"';
    else mark='<path d="M '+(x-4).toFixed(1)+' '+y.toFixed(1)+' H '+(x+4).toFixed(1)+' M '+x.toFixed(1)+' '+(y-4).toFixed(1)+' V '+(y+4).toFixed(1)+'" ';
    let close=shape==="front_fast"?"</rect>":shape==="front_loaded"||shape==="mid_loaded"||shape==="back_loaded"?"</polygon>":shape==="linear"?"</circle>":"</path>";"""
    new_shape = """let shape=r.timing_rule,mark;
    if(shape==="front_rapid")mark='<polygon points="'+x.toFixed(1)+','+(y-5).toFixed(1)+' '+(x+5).toFixed(1)+','+y.toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+' '+(x-5).toFixed(1)+','+y.toFixed(1)+'"';
    else if(shape==="front_fast")mark='<rect x="'+(x-3.5).toFixed(1)+'" y="'+(y-3.5).toFixed(1)+'" width="7" height="7"';
    else if(shape==="front_loaded")mark='<polygon points="'+x.toFixed(1)+','+(y-4.5).toFixed(1)+' '+(x-4.5).toFixed(1)+','+(y+3.5).toFixed(1)+' '+(x+4.5).toFixed(1)+','+(y+3.5).toFixed(1)+'"';
    else if(shape==="linear")mark='<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+(sel?5.2:3.3)+'"';
    else if(shape==="mid_loaded")mark='<polygon points="'+x.toFixed(1)+','+(y-5).toFixed(1)+' '+(x-5).toFixed(1)+','+y.toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+' '+(x+5).toFixed(1)+','+y.toFixed(1)+'"';
    else if(shape==="staggered")mark='<polygon points="'+x.toFixed(1)+','+(y-5).toFixed(1)+' '+(x+4.8).toFixed(1)+','+(y-1.5).toFixed(1)+' '+(x+3).toFixed(1)+','+(y+4.2).toFixed(1)+' '+(x-3).toFixed(1)+','+(y+4.2).toFixed(1)+' '+(x-4.8).toFixed(1)+','+(y-1.5).toFixed(1)+'"';
    else if(shape==="back_loaded")mark='<polygon points="'+(x-4.5).toFixed(1)+','+(y-3.5).toFixed(1)+' '+(x+4.5).toFixed(1)+','+(y-3.5).toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+'"';
    else mark='<path d="M '+(x-4).toFixed(1)+' '+y.toFixed(1)+' H '+(x+4).toFixed(1)+' M '+x.toFixed(1)+' '+(y-4).toFixed(1)+' V '+(y+4).toFixed(1)+'" ';
    let close=shape==="front_fast"?"</rect>":shape==="front_rapid"||shape==="front_loaded"||shape==="mid_loaded"||shape==="staggered"||shape==="back_loaded"?"</polygon>":shape==="linear"?"</circle>":"</path>";"""
    if html.count(old_shape) == 1:
        html = replace_once(html, old_shape, new_shape, "eight timing scatter markers")
    else:
        # The current main dashboard may already carry the eight-rule marker chain.
        # Accept that known-good form, but BLOCK unknown partial implementations.
        shape_blocks = list(re.finditer(r'let shape=r\.timing_rule,mark;(.*?)let close=shape=', html, re.S))
        require(len(shape_blocks) == 1, "Expected exactly one scatter shape block")
        shape_block = shape_blocks[0].group(1)
        missing_shapes = [timing for timing in TIMINGS if timing != "back_late" and f'shape==="{timing}"' not in shape_block]
        require(not missing_shapes and "else mark=" in shape_block,
                "Unsupported scatter marker block; missing timing shapes/fallback: " + ", ".join(missing_shapes))
    old_dash = '(m==="front_loaded"?"6 4":m==="back_loaded"?"2 4":"")'
    new_dash = '({front_rapid:"3 2",front_fast:"1 3",front_loaded:"8 4",linear:"",mid_loaded:"6 2 1 2",staggered:"5 2 1 2",back_loaded:"2 4",back_late:"10 3"}[m]||"")'
    if html.count(old_dash) == 1:
        html = replace_once(html, old_dash, new_dash, "glide path timing dash mapping")
    else:
        # A newer compact-page base may already contain the complete indexed dash map.
        indexed_dash_maps = re.findall(r'\(\s*\{([^{}]*)\}\s*\[\s*m\s*\]\s*\|\|\s*""\s*\)', html)
        known_complete_map = any(
            all(re.search(re.escape(timing) + r'\s*:', body) for timing in TIMINGS)
            for body in indexed_dash_maps
        )
        require(known_complete_map,
                "Unsupported glidepath dash mapping; no legacy map or complete eight-rule map found")

    # Older compact-page plots have independent, partial dash maps. Normalize every
    # timing-keyed map so newly added rules never serialize stroke-dasharray="undefined".
    dash_map_pattern = re.compile(r'(const\s+dash\s*=\s*)\{([^{}]*)\}(\s*;)')
    complete_dash_map = '{front_rapid:"3 2",front_fast:"1 3",front_loaded:"8 4",linear:"",mid_loaded:"6 2 1 2",staggered:"5 2 1 2",back_loaded:"2 4",back_late:"10 3"}'
    timing_keys = set(TIMINGS)
    replaced_dash_maps = 0

    def normalize_timing_dash_map(match: re.Match[str]) -> str:
        nonlocal replaced_dash_maps
        body = match.group(2)
        if any(re.search(re.escape(key) + r'\s*:', body) for key in timing_keys):
            replaced_dash_maps += 1
            return match.group(1) + complete_dash_map + match.group(3)
        return match.group(0)

    html = dash_map_pattern.sub(normalize_timing_dash_map, html)
    require(replaced_dash_maps >= 1,
            "Could not find a timing-keyed dash map to normalize for all eight rules")
    for timing in TIMINGS:
        require(re.search(r'const\s+dash\s*=\s*\{[^{}]*\b' + re.escape(timing) + r'\s*:', html) is not None,
                f"An eight-rule dash map is missing {timing}")

    # The four timing-independent source declarations below must remain intact.
    require('TM=["front_rapid","front_fast","front_loaded","linear","mid_loaded","staggered","back_loaded","back_late"]' in html,
            "Eight timing identifiers were not embedded")
    for count, marker in ((1024, '"d":'), (11264, '"a":'), (4096, '"h":'), (len(pack["c"]), '"c":')):
        require(count > 0 and marker in payload, f"Packed data missing {marker}")
    return html

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--histograms", type=Path, required=True)
    parser.add_argument("--cohorts", type=Path, required=True)
    parser.add_argument("--ledger-replay", type=Path, required=True)
    parser.add_argument("--html", type=Path, default=ROOT / "v2.html")
    args = parser.parse_args()

    report = json.loads(args.summary.read_text(encoding="utf-8"))
    hist = json.loads(args.histograms.read_text(encoding="utf-8"))
    cohort_report = json.loads(args.cohorts.read_text(encoding="utf-8"))
    ledger_replay_report = json.loads(args.ledger_replay.read_text(encoding="utf-8"))
    pack = validate_and_pack(report, hist, cohort_report, ledger_replay_report)
    original = args.html.read_text(encoding="utf-8")
    updated = embed_pack(original, pack)
    args.html.write_text(updated, encoding="utf-8")
    print(json.dumps({
        "status": "EIGHT_TIMING_PACK_EMBEDDED",
        "source_as_of": pack["meta"]["source_as_of"],
        "source_sha256": pack["meta"]["source_sha256"],
        "scenarios": len(pack["d"]),
        "annual_summaries": len(pack["a"]),
        "histogram_groups": len(pack["h"]),
        "cohort_rows": len(pack["c"]),
        "real_floor_annual_rows": len(real_floor_by_key),
        "cohort_years": pack["meta"]["cohort_years"],
        "html_characters": len(updated),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
