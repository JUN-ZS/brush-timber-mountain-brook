#!/usr/bin/env python3
"""Cash-flow-aware rolling 10-year outcomes for QQQ and SPY.

Uses the repository's SHA-pinned daily price file, converted to monthly-last
observations. This is a price-only diagnostic, not a total-return or execution replay.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HORIZON_MONTHS = 120
INITIAL_CAPITAL_USD = 100_000.0
MONTHLY_WITHDRAWAL_GRID_USD = (0.0, 250.0, 500.0, 1_000.0, 1_500.0, 2_000.0)
TICKERS = ("QQQ", "SPY")
DEFAULT_FLOOR_FACE_USD = 100_000.0
INDICATIVE_TEN_YEAR_PAR_YIELD = 0.0509  # official par-yield reference, 2026-10-16
DEFAULT_FLOOR_COST_USD = DEFAULT_FLOOR_FACE_USD / (1 + INDICATIVE_TEN_YEAR_PAR_YIELD / 2) ** 20

PINNED_INPUT_SHA256 = "c9e369c8a3789c543c05fafa82ed67589c1292a7bd423f2ef9990313825f5127"
EXPECTED_MONTHLY_OBSERVATIONS = 331


@dataclass(frozen=True)
class MonthlyPrice:
    date: dt.date
    qqq: float
    spy: float
    daily_points: tuple[tuple[dt.date, float, float], ...] = ()

    def price(self, ticker: str):
        if ticker == "QQQ":
            return self.qqq
        if ticker == "SPY":
            return self.spy
        raise ValueError(f"Unsupported ticker: {ticker}")


@dataclass(frozen=True)
class FlowEvent:
    month_index: int
    flow_type: str
    amount_usd: float
    note: str = ""


def load_monthly_prices(path: Path) -> tuple[list[MonthlyPrice], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PINNED_INPUT_SHA256:
        raise ValueError(
            "Pinned market CSV SHA-256 mismatch: "
            f"expected {PINNED_INPUT_SHA256}, got {digest}. "
            "Do not silently accept changed market data; review and deliberately repin."
        )

    daily_by_month: dict[tuple[int, int], list[tuple[dt.date, float, float]]] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"Date", "QQQ", "SPY"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"Input must contain columns: {sorted(required)}")
        for row in reader:
            try:
                date = dt.date.fromisoformat(row["Date"])
                qqq = float(row["QQQ"])
                spy = float(row["SPY"])
            except (TypeError, ValueError, KeyError):
                continue
            if not (math.isfinite(qqq) and math.isfinite(spy) and qqq > 0 and spy > 0):
                continue
            daily_by_month.setdefault((date.year, date.month), []).append((date, qqq, spy))

    points: list[MonthlyPrice] = []
    for month_key in sorted(daily_by_month):
        bars = sorted(daily_by_month[month_key], key=lambda bar: bar[0])
        last_date, last_qqq, last_spy = bars[-1]
        points.append(MonthlyPrice(last_date, last_qqq, last_spy, tuple(bars)))
    if len(points) != EXPECTED_MONTHLY_OBSERVATIONS:
        raise ValueError(
            f"Expected {EXPECTED_MONTHLY_OBSERVATIONS} monthly observations from pinned "
            f"data; found {len(points)}"
        )
    if len(points) <= HORIZON_MONTHS:
        raise ValueError("Not enough monthly observations for a 120-month replay")
    return points, digest


def load_flow_schedule(path: Path) -> dict[int, list[FlowEvent]]:
    """Load relative-month cash flows. Positive amount_usd is always an amount.

    flow_type is deposit or withdrawal. If several events share a month, file order
    defines their sequence (for example, deposit before withdrawal).
    """
    schedule: dict[int, list[FlowEvent]] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"month_index", "flow_type", "amount_usd"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                "Flow CSV needs month_index,flow_type,amount_usd; optional column: note"
            )
        for line_number, row in enumerate(reader, start=2):
            try:
                month_index = int(row["month_index"])
                amount = float(row["amount_usd"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid month or amount on schedule line {line_number}") from error
            flow_type = str(row["flow_type"]).strip().lower()
            if not 1 <= month_index <= HORIZON_MONTHS:
                raise ValueError(f"month_index must be 1..{HORIZON_MONTHS}, line {line_number}")
            if flow_type not in {"deposit", "withdrawal"}:
                raise ValueError(f"flow_type must be deposit or withdrawal, line {line_number}")
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError(f"amount_usd must be finite and > 0, line {line_number}")
            schedule.setdefault(month_index, []).append(
                FlowEvent(month_index, flow_type, amount, str(row.get("note", "") or ""))
            )
    return schedule


def fixed_withdrawal_schedule(monthly_amount_usd: float) -> dict[int, list[FlowEvent]]:
    if not math.isfinite(monthly_amount_usd) or monthly_amount_usd < 0:
        raise ValueError("Monthly withdrawal must be finite and >= 0")
    if monthly_amount_usd == 0:
        return {}
    return {
        month: [FlowEvent(month, "withdrawal", monthly_amount_usd, "fixed monthly scenario")]
        for month in range(1, HORIZON_MONTHS + 1)
    }


def _npv_at_log_rate(
    log_one_plus_rate: float,
    dated_cashflows: list[tuple[dt.date, float]],
    origin: dt.date,
) -> float:
    total = 0.0
    for date, amount in dated_cashflows:
        years = (date - origin).days / 365.25
        total += amount * math.exp(-log_one_plus_rate * years)
    return total


def solve_xirr(dated_cashflows: Iterable[tuple[dt.date, float]]) -> tuple[float | None, str]:
    """Solve annualized money-weighted return; return null on ambiguous/no root.

    Search range is -99.9% to +1000% annualized. More than one root is considered
    ambiguous and is not silently reduced to whichever root a numerical solver finds.
    """
    by_date: dict[dt.date, float] = {}
    for date, amount in dated_cashflows:
        if not math.isfinite(amount):
            return None, "INVALID_CASHFLOW"
        by_date[date] = by_date.get(date, 0.0) + amount
    flows = sorted(
        ((date, amount) for date, amount in by_date.items() if abs(amount) > 1e-10),
        key=lambda item: item[0],
    )
    if len(flows) < 2 or not any(amount < 0 for _, amount in flows) or not any(
        amount > 0 for _, amount in flows
    ):
        return None, "NO_ROOT"
    origin = flows[0][0]
    total_abs = sum(abs(amount) for _, amount in flows)
    tolerance = max(1e-8, total_abs * 1e-12)
    low = math.log(0.001)  # rate = -99.9%
    high = math.log(11.0)  # rate = +1000%
    samples = 1_200
    xs = [low + (high - low) * index / samples for index in range(samples + 1)]
    values = [_npv_at_log_rate(x, flows, origin) for x in xs]
    roots: list[float] = []

    for index in range(len(xs) - 1):
        x0, x1 = xs[index], xs[index + 1]
        y0, y1 = values[index], values[index + 1]
        if abs(y0) <= tolerance:
            roots.append(x0)
        if y0 * y1 < 0:
            lo, hi, vlo = x0, x1, y0
            for _ in range(160):
                mid = (lo + hi) / 2
                vmid = _npv_at_log_rate(mid, flows, origin)
                if abs(vmid) <= tolerance or abs(hi - lo) < 1e-13:
                    lo = hi = mid
                    break
                if (vlo < 0) == (vmid < 0):
                    lo, vlo = mid, vmid
                else:
                    hi = mid
            roots.append((lo + hi) / 2)
    if abs(values[-1]) <= tolerance:
        roots.append(xs[-1])

    unique_roots: list[float] = []
    for root in sorted(roots):
        if not unique_roots or abs(root - unique_roots[-1]) > 1e-5:
            unique_roots.append(root)
    if not unique_roots:
        return None, "NO_ROOT_IN_SEARCH_RANGE"
    if len(unique_roots) > 1:
        return None, "MULTIPLE_ROOTS_AMBIGUOUS"
    return math.expm1(unique_roots[0]), "OK"


def _max_drawdown(values: list[float]) -> float:
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def replay_window(
    points: list[MonthlyPrice],
    start_index: int,
    ticker: str,
    schedule: dict[int, list[FlowEvent]],
    initial_capital_usd: float = INITIAL_CAPITAL_USD,
) -> dict:
    end_index = start_index + HORIZON_MONTHS
    if start_index < 0 or end_index >= len(points):
        raise ValueError("Requested window is outside available data")
    if not math.isfinite(initial_capital_usd) or initial_capital_usd <= 0:
        raise ValueError("Initial capital must be finite and > 0")

    start = points[start_index]
    end = points[end_index]
    nav = initial_capital_usd
    deposits = 0.0
    requested_withdrawals = 0.0
    actual_withdrawals = 0.0
    shortfall = 0.0
    min_nav = nav
    first_depletion_month: int | None = None
    investor_cashflows: list[tuple[dt.date, float]] = [(start.date, -initial_capital_usd)]

    for month_index in range(1, HORIZON_MONTHS + 1):
        previous_price = points[start_index + month_index - 1].price(ticker)
        current_point = points[start_index + month_index]
        current_price = current_point.price(ticker)
        nav *= current_price / previous_price

        for event in schedule.get(month_index, []):
            if event.flow_type == "deposit":
                nav += event.amount_usd
                deposits += event.amount_usd
                investor_cashflows.append((current_point.date, -event.amount_usd))
            else:
                requested_withdrawals += event.amount_usd
                paid = min(event.amount_usd, max(0.0, nav))
                nav = max(0.0, nav - paid)
                actual_withdrawals += paid
                shortfall += event.amount_usd - paid
                if paid > 1e-10:
                    investor_cashflows.append((current_point.date, paid))
            min_nav = min(min_nav, nav)
            if nav <= 1e-8 and first_depletion_month is None:
                first_depletion_month = month_index

    terminal_nav = max(0.0, nav)
    if terminal_nav > 1e-10:
        investor_cashflows.append((end.date, terminal_nav))
    xirr, xirr_status = solve_xirr(investor_cashflows)
    daily_path: list[tuple[dt.date, float]] = []
    for monthly_point in points[start_index : end_index + 1]:
        for daily_date, qqq_value, spy_value in monthly_point.daily_points:
            if start.date <= daily_date <= end.date:
                daily_path.append((daily_date, qqq_value if ticker == "QQQ" else spy_value))
    if daily_path:
        daily_path.sort(key=lambda item: item[0])
        drawdown_prices = [value for _, value in daily_path]
    else:
        # Synthetic tests may provide monthly points only.
        drawdown_prices = [point.price(ticker) for point in points[start_index : end_index + 1]]
    monthly_prices = [point.price(ticker) for point in points[start_index : end_index + 1]]
    elapsed_years = (end.date - start.date).days / 365.25
    market_price_cagr = (
        (monthly_prices[-1] / monthly_prices[0]) ** (1.0 / elapsed_years) - 1.0
        if elapsed_years > 0
        else None
    )

    return {
        "ticker": ticker,
        "window_start": start.date.isoformat(),
        "window_end": end.date.isoformat(),
        "initial_capital_usd": round(initial_capital_usd, 2),
        "additional_deposits_usd": round(deposits, 2),
        "total_capital_supplied_usd": round(initial_capital_usd + deposits, 2),
        "requested_withdrawals_usd": round(requested_withdrawals, 2),
        "actual_withdrawals_usd": round(actual_withdrawals, 2),
        "withdrawal_shortfall_usd": round(shortfall, 2),
        "terminal_nav_usd": round(terminal_nav, 2),
        "min_month_end_nav_usd": round(min_nav, 2),
        "nominal_net_result_vs_initial_capital_usd": round(
            actual_withdrawals + terminal_nav - deposits - initial_capital_usd, 2
        ),
        "investor_xirr": xirr,
        "investor_xirr_status": xirr_status,
        "underlying_price_cagr": market_price_cagr,
        "underlying_price_max_drawdown": _max_drawdown(drawdown_prices),
        "ever_depleted_at_month_end": first_depletion_month is not None,
        "first_depletion_month_index": first_depletion_month,
    }


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _round_rate(value: float | None) -> float | None:
    return None if value is None else round(value, 8)


def summarize_scenario(label: str, ticker: str, monthly_withdrawal_usd: float | None, rows: list[dict]) -> dict:
    terminal = [float(row["terminal_nav_usd"]) for row in rows]
    actual_withdrawals = [float(row["actual_withdrawals_usd"]) for row in rows]
    shortfalls = [float(row["withdrawal_shortfall_usd"]) for row in rows]
    xirr_values = [float(row["investor_xirr"]) for row in rows if row["investor_xirr"] is not None]
    price_cagrs = [float(row["underlying_price_cagr"]) for row in rows]
    drawdowns = [float(row["underlying_price_max_drawdown"]) for row in rows]
    return {
        "ticker": ticker,
        "scenario": label,
        "fixed_monthly_withdrawal_usd": monthly_withdrawal_usd,
        "rolling_windows": len(rows),
        "windows_with_any_unfunded_withdrawal": sum(value > 0.01 for value in shortfalls),
        "windows_ever_depleted_at_month_end": sum(
            bool(row["ever_depleted_at_month_end"]) for row in rows
        ),
        "median_actual_withdrawals_usd": round(_quantile(actual_withdrawals, 0.50) or 0.0, 2),
        "median_withdrawal_shortfall_usd": round(_quantile(shortfalls, 0.50) or 0.0, 2),
        "p95_withdrawal_shortfall_usd": round(_quantile(shortfalls, 0.95) or 0.0, 2),
        "median_terminal_nav_usd": round(_quantile(terminal, 0.50) or 0.0, 2),
        "p05_terminal_nav_usd": round(_quantile(terminal, 0.05) or 0.0, 2),
        "worst_terminal_nav_usd": round(min(terminal), 2),
        "median_nominal_net_result_usd": round(
            _quantile([float(row["nominal_net_result_vs_initial_capital_usd"]) for row in rows], 0.50) or 0.0,
            2,
        ),
        "xirr_defined_windows": len(xirr_values),
        "xirr_no_root_or_invalid_windows": sum(
            row["investor_xirr_status"] in {"NO_ROOT", "NO_ROOT_IN_SEARCH_RANGE", "INVALID_CASHFLOW"}
            for row in rows
        ),
        "xirr_ambiguous_windows": sum(
            row["investor_xirr_status"] == "MULTIPLE_ROOTS_AMBIGUOUS" for row in rows
        ),
        "median_investor_xirr": _round_rate(_quantile(xirr_values, 0.50)),
        "p05_investor_xirr": _round_rate(_quantile(xirr_values, 0.05)),
        "worst_defined_investor_xirr": _round_rate(min(xirr_values) if xirr_values else None),
        "median_underlying_price_cagr": _round_rate(_quantile(price_cagrs, 0.50)),
        "median_underlying_price_max_drawdown": _round_rate(_quantile(drawdowns, 0.50)),
        "worst_underlying_price_max_drawdown": _round_rate(min(drawdowns)),
    }


def summarize_capital_floor_scenarios(
    points: list[MonthlyPrice],
    floor_face_usd: float = DEFAULT_FLOOR_FACE_USD,
    floor_cost_usd: float = DEFAULT_FLOOR_COST_USD,
    custom_schedule: dict[int, list[FlowEvent]] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Replay a maturity-floor portfolio; all optional spending uses the growth sleeve first.

    The modeled zero-coupon floor is locked until maturity. Deposits and withdrawals
    are applied at monthly closes. A withdrawal is funded pro-rata from the QQQ, SPY
    and cash components of the growth sleeve only; any unfunded amount is recorded as
    shortfall rather than drawing down the protected floor.
    """
    if not math.isfinite(floor_face_usd) or floor_face_usd <= 0:
        raise ValueError("Floor face value must be finite and > 0")
    if not math.isfinite(floor_cost_usd) or floor_cost_usd <= 0:
        raise ValueError("Floor purchase cost must be finite and > 0")
    if floor_cost_usd >= INITIAL_CAPITAL_USD:
        raise ValueError(
            "Floor purchase cost must be below initial capital so a growth sleeve remains"
        )
    growth_initial = INITIAL_CAPITAL_USD - floor_cost_usd
    strategies = [
        ("FLOOR_PLUS_CASH_0PCT", 0.0, 0.0, 1.0),
        ("FLOOR_PLUS_QQQ", 1.0, 0.0, 0.0),
        ("FLOOR_PLUS_SPY", 0.0, 1.0, 0.0),
        ("FLOOR_PLUS_QQQ_SPY_50_50", 0.5, 0.5, 0.0),
    ]
    rows: list[dict] = []
    summaries: list[dict] = []
    window_count = len(points) - HORIZON_MONTHS
    if window_count <= 0:
        raise ValueError("Not enough monthly points to build a ten-year floor replay")
    schedule = custom_schedule or {}

    for strategy, qqq_weight, spy_weight, cash_weight in strategies:
        scenario_rows: list[dict] = []
        for start_index in range(window_count):
            start = points[start_index]
            end = points[start_index + HORIZON_MONTHS]
            qqq_value = growth_initial * qqq_weight
            spy_value = growth_initial * spy_weight
            cash_value = growth_initial * cash_weight
            deposits = 0.0
            requested_withdrawals = 0.0
            actual_withdrawals = 0.0
            withdrawal_shortfall = 0.0
            first_growth_depletion_month: int | None = None
            min_growth_nav = growth_initial
            investor_cashflows: list[tuple[dt.date, float]] = [(start.date, -INITIAL_CAPITAL_USD)]

            for month_index in range(1, HORIZON_MONTHS + 1):
                previous = points[start_index + month_index - 1]
                current = points[start_index + month_index]
                qqq_value *= current.qqq / previous.qqq
                spy_value *= current.spy / previous.spy

                for event in schedule.get(month_index, []):
                    if event.flow_type == "deposit":
                        amount = event.amount_usd
                        qqq_value += amount * qqq_weight
                        spy_value += amount * spy_weight
                        cash_value += amount * cash_weight
                        deposits += amount
                        investor_cashflows.append((current.date, -amount))
                    else:
                        requested_withdrawals += event.amount_usd
                        growth_nav_before = qqq_value + spy_value + cash_value
                        paid = min(event.amount_usd, max(0.0, growth_nav_before))
                        withdrawal_shortfall += event.amount_usd - paid
                        if growth_nav_before > 1e-10 and paid > 0:
                            remaining_fraction = (growth_nav_before - paid) / growth_nav_before
                            qqq_value *= remaining_fraction
                            spy_value *= remaining_fraction
                            cash_value *= remaining_fraction
                            actual_withdrawals += paid
                            investor_cashflows.append((current.date, paid))

                growth_nav = max(0.0, qqq_value + spy_value + cash_value)
                min_growth_nav = min(min_growth_nav, growth_nav)
                if growth_nav <= 1e-8 and first_growth_depletion_month is None:
                    first_growth_depletion_month = month_index

            growth_terminal = max(0.0, qqq_value + spy_value + cash_value)
            terminal = floor_face_usd + growth_terminal
            if terminal > 1e-10:
                investor_cashflows.append((end.date, terminal))
            xirr, xirr_status = solve_xirr(investor_cashflows)
            elapsed_years = (end.date - start.date).days / 365.25
            terminal_cagr = (
                (terminal / INITIAL_CAPITAL_USD) ** (1 / elapsed_years) - 1
                if elapsed_years > 0
                else None
            )
            nominal_net_result = actual_withdrawals + terminal - deposits - INITIAL_CAPITAL_USD
            row = {
                "scenario": strategy,
                "cashflow_mode": "custom_schedule" if custom_schedule is not None else "no_withdrawals",
                "window_start": start.date.isoformat(),
                "window_end": end.date.isoformat(),
                "initial_capital_usd": round(INITIAL_CAPITAL_USD, 2),
                "floor_face_usd_at_maturity": round(floor_face_usd, 2),
                "floor_purchase_cost_usd": round(floor_cost_usd, 2),
                "growth_sleeve_initial_capital_usd": round(growth_initial, 2),
                "qqq_growth_weight": qqq_weight,
                "spy_growth_weight": spy_weight,
                "cash_growth_weight": cash_weight,
                "additional_deposits_usd": round(deposits, 2),
                "total_capital_supplied_usd": round(INITIAL_CAPITAL_USD + deposits, 2),
                "requested_withdrawals_usd": round(requested_withdrawals, 2),
                "actual_withdrawals_usd": round(actual_withdrawals, 2),
                "withdrawal_shortfall_usd": round(withdrawal_shortfall, 2),
                "min_month_end_growth_sleeve_nav_usd": round(min_growth_nav, 2),
                "growth_sleeve_terminal_usd": round(growth_terminal, 2),
                "protected_maturity_payment_usd": round(floor_face_usd, 2),
                "terminal_nav_usd": round(terminal, 2),
                "nominal_net_result_vs_initial_capital_usd": round(nominal_net_result, 2),
                "investor_xirr": xirr,
                "investor_xirr_status": xirr_status,
                "terminal_cagr": terminal_cagr,
                "first_growth_sleeve_depletion_month": first_growth_depletion_month,
                "principal_floor_met_at_maturity_before_tax_costs": terminal >= floor_face_usd,
                "floor_payment_used_for_spending": False,
                "floor_method": (
                    "zero-coupon maturity payment modeled as fixed face value; "
                    "not marked to market during the ten-year holding period"
                ),
                "window_index": start_index,
            }
            scenario_rows.append(row)
            rows.append(row)

        terminal_values = [float(row["terminal_nav_usd"]) for row in scenario_rows]
        cagrs = [
            float(row["terminal_cagr"])
            for row in scenario_rows
            if row["terminal_cagr"] is not None
        ]
        xirr_values = [
            float(row["investor_xirr"])
            for row in scenario_rows
            if row["investor_xirr"] is not None
        ]
        actual_withdrawals_values = [float(row["actual_withdrawals_usd"]) for row in scenario_rows]
        shortfall_values = [float(row["withdrawal_shortfall_usd"]) for row in scenario_rows]
        worst = min(scenario_rows, key=lambda row: float(row["terminal_nav_usd"]))
        summaries.append({
            "scenario": strategy,
            "cashflow_mode": "custom_schedule" if custom_schedule is not None else "no_withdrawals",
            "floor_face_usd_at_maturity": round(floor_face_usd, 2),
            "floor_purchase_cost_usd": round(floor_cost_usd, 2),
            "growth_sleeve_initial_capital_usd": round(growth_initial, 2),
            "growth_sleeve_share_of_initial_capital": round(growth_initial / INITIAL_CAPITAL_USD, 8),
            "floor_cost_reference_yield_assumption": INDICATIVE_TEN_YEAR_PAR_YIELD,
            "floor_cost_reference_note": (
                "Illustrative calculation from the 2026-10-16 ten-year Treasury par yield, "
                "semiannual-compounding convention; not an executable, maturity-matched STRIPS quote"
                if abs(floor_cost_usd - DEFAULT_FLOOR_COST_USD) < 0.01
                else "User-supplied scenario cost; verify against an executable maturity-matched quote"
            ),
            "rolling_windows": len(scenario_rows),
            "windows_floor_not_met_by_model_before_tax_costs": sum(
                not bool(row["principal_floor_met_at_maturity_before_tax_costs"])
                for row in scenario_rows
            ),
            "windows_with_any_unfunded_withdrawal": sum(
                float(row["withdrawal_shortfall_usd"]) > 0.01 for row in scenario_rows
            ),
            "windows_with_growth_sleeve_depleted": sum(
                row["first_growth_sleeve_depletion_month"] is not None for row in scenario_rows
            ),
            "median_actual_withdrawals_usd": round(_quantile(actual_withdrawals_values, 0.50) or 0.0, 2),
            "median_withdrawal_shortfall_usd": round(_quantile(shortfall_values, 0.50) or 0.0, 2),
            "p95_withdrawal_shortfall_usd": round(_quantile(shortfall_values, 0.95) or 0.0, 2),
            "median_terminal_nav_usd": round(_quantile(terminal_values, 0.50) or 0.0, 2),
            "p05_terminal_nav_usd": round(_quantile(terminal_values, 0.05) or 0.0, 2),
            "worst_terminal_nav_usd": round(min(terminal_values), 2),
            "worst_terminal_window": {
                "start": worst["window_start"],
                "end": worst["window_end"],
            },
            "median_terminal_cagr": _round_rate(_quantile(cagrs, 0.50)),
            "p05_terminal_cagr": _round_rate(_quantile(cagrs, 0.05)),
            "worst_terminal_cagr": _round_rate(min(cagrs) if cagrs else None),
            "median_investor_xirr": _round_rate(_quantile(xirr_values, 0.50)),
            "p05_investor_xirr": _round_rate(_quantile(xirr_values, 0.05)),
            "nominal_floor_is_only_a_maturity_value": True,
            "real_purchasing_power_guaranteed": False,
            "taxes_fees_and_early_sale_risk_included": False,
            "floor_payment_used_for_spending": False,
        })
    return summaries, rows

def run_research(
    points: list[MonthlyPrice],
    custom_schedule: dict[int, list[FlowEvent]] | None = None,
    include_withdrawal_grid: bool = False,
    floor_face_usd: float = DEFAULT_FLOOR_FACE_USD,
    floor_cost_usd: float = DEFAULT_FLOOR_COST_USD,
) -> tuple[dict, list[dict]]:
    all_rows: list[dict] = []
    summaries: list[dict] = []
    if custom_schedule is not None:
        scenarios = [("custom_schedule", None, custom_schedule)]
    elif include_withdrawal_grid:
        scenarios = [
            (f"monthly_withdrawal_{int(amount)}_usd", amount, fixed_withdrawal_schedule(amount))
            for amount in MONTHLY_WITHDRAWAL_GRID_USD
        ]
    else:
        scenarios = [("no_withdrawals", 0.0, {})]

    for ticker in TICKERS:
        for label, withdrawal_amount, schedule in scenarios:
            scenario_rows = [
                replay_window(points, start_index, ticker, schedule)
                for start_index in range(len(points) - HORIZON_MONTHS)
            ]
            for row in scenario_rows:
                row["scenario"] = label
                row["fixed_monthly_withdrawal_usd"] = withdrawal_amount
            all_rows.extend(scenario_rows)
            summaries.append(summarize_scenario(label, ticker, withdrawal_amount, scenario_rows))

    floor_summaries, floor_rows = summarize_capital_floor_scenarios(
        points,
        floor_face_usd=floor_face_usd,
        floor_cost_usd=floor_cost_usd,
        custom_schedule=custom_schedule,
    )
    all_rows.extend(floor_rows)

    report = {
        "schema": "cashflow-aware-investor-outcomes.v2",
        "input": {
            "sha256": PINNED_INPUT_SHA256,
            "monthly_observations": len(points),
            "first_observation": points[0].date.isoformat(),
            "last_observation": points[-1].date.isoformat(),
        },
        "method": {
            "horizon_months": HORIZON_MONTHS,
            "rolling_windows_per_scenario": len(points) - HORIZON_MONTHS,
            "initial_capital_usd": INITIAL_CAPITAL_USD,
            "default_cashflow_behavior": "No deposit or withdrawal events unless --flows-csv is supplied; fixed-withdrawal sensitivity is opt-in via --withdrawal-grid",
            "window_definition": "initial price at month 0; months 1..120 apply market price return then scheduled external cash flows; final NAV is measured after month-120 flows",
            "external_flow_sign_convention": "deposit increases invested NAV and is a negative investor cash flow; a withdrawal is paid only up to available NAV and the paid amount is a positive investor cash flow; unpaid withdrawal demand is recorded as shortfall",
            "xirr": "annualized actual/365.25 money-weighted return; unique root searched from -99.9% to +1000%; no-root and multiple-root cases remain null/status-coded",
            "price_only": True,
            "drawdown_marking": "full daily source marks from the monthly-start close through the monthly-end close; synthetic fixtures fall back to monthly marks",
            "dividends_reinvested": False,
            "transaction_costs_and_taxes": 0.0,
            "cash_interest": 0.0,
            "leverage_or_options": False,
            "rolling_windows_overlap": True,
            "window_counts_are_forward_probabilities": False,
            "cashflow_scenario": (
                "relative-month custom schedule is applied to both unprotected controls and floor-backed growth sleeves; floor-backed withdrawals are paid only from growth sleeve and any shortfall is reported"
                if custom_schedule is not None
                else "no withdrawals and no further deposits by default"
            ),
            "floor_cashflow_waterfall": "deposits are invested into the growth sleeve at target weights; withdrawals are paid pro-rata from that sleeve at the monthly close; the protected maturity face payment is locked and never used for spending; shortfall remains explicit",
            "withdrawal_grid_enabled": include_withdrawal_grid,
            "capital_floor_model": {
                "floor_face_usd_at_maturity": floor_face_usd,
                "floor_purchase_cost_usd": floor_cost_usd,
                "growth_sleeve_initial_capital_usd": INITIAL_CAPITAL_USD - floor_cost_usd,
                "illustrative_par_yield_assumption": INDICATIVE_TEN_YEAR_PAR_YIELD,
                "illustrative_date": "2026-10-16",
                "critical_assumption": (
                    "A maturity-matched zero-coupon Treasury/STRIPS is bought at the supplied cost "
                    "and held to maturity. Any configured withdrawal/deposit events are applied to the "
                    "growth sleeve only; the floor's maturity payment is never used to fund spending. "
                    "Tax and transaction costs are not modeled. The remaining sleeve is unlevered price-only QQQ/SPY or zero-yield cash."
                ),
                "not_an_executable_quote": abs(floor_cost_usd - DEFAULT_FLOOR_COST_USD) < 0.01,
                "not_a_historical_bond_strategy_backtest": True,
            },
        },
        "scenario_summaries": summaries,
        "capital_floor_summaries": floor_summaries,
    }
    return report, all_rows

def write_rows_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No replay rows to write")
    fieldnames = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Pinned CSV with Date, QQQ and SPY")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON summary")
    parser.add_argument("--rows-out", type=Path, required=True, help="Output rolling-window CSV")
    parser.add_argument("--flows-csv", type=Path, help="Optional relative-month deposit/withdrawal schedule")
    parser.add_argument(
        "--withdrawal-grid",
        action="store_true",
        help="Opt in to fixed $0/$250/$500/$1000/$1500/$2000 monthly withdrawal sensitivity",
    )
    parser.add_argument(
        "--floor-face-usd",
        type=float,
        default=DEFAULT_FLOOR_FACE_USD,
        help="Nominal face payment to protect at the horizon maturity (default: 100000)",
    )
    parser.add_argument(
        "--floor-cost-usd",
        type=float,
        default=DEFAULT_FLOOR_COST_USD,
        help=(
            "All-in purchase cost for the maturity-floor instrument (default: an illustrative "
            "60,493.71 USD derived from the 2026-10-16 ten-year Treasury par-yield proxy, not a quote)"
        ),
    )
    args = parser.parse_args()

    points, digest = load_monthly_prices(args.input)
    schedule = load_flow_schedule(args.flows_csv) if args.flows_csv else None
    report, rows = run_research(
        points,
        custom_schedule=schedule,
        include_withdrawal_grid=args.withdrawal_grid,
        floor_face_usd=args.floor_face_usd,
        floor_cost_usd=args.floor_cost_usd,
    )
    report["input"]["actual_sha256"] = digest
    if args.flows_csv:
        report["method"]["custom_schedule_source"] = args.flows_csv.name
        report["method"]["custom_schedule_rows"] = sum(len(items) for items in schedule.values())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_rows_csv(args.rows_out, rows)
    print(json.dumps({
        "schema": report["schema"],
        "input": report["input"],
        "scenario_summaries": report["scenario_summaries"],
        "capital_floor_summaries": report["capital_floor_summaries"],
        "summary_output": args.out.as_posix(),
        "rows_output": args.rows_out.as_posix(),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
