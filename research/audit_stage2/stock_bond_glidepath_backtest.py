#!/usr/bin/env python3
"""Historical stock-to-bond glidepath replay using dividend-adjusted daily ETF prices.

Equity sleeve: 50/50 QQQ and SPY at each annual glidepath rebalance.
Bond proxies: AGG (aggregate bonds), SHY (short Treasuries), IEF (7-10y Treasuries),
and TLT (20+y Treasuries). Adjusted-close price relatives approximate reinvested
distributions. This is not an individual Treasury/STRIPS maturity-floor backtest.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cashflow_aware_qqq_spy import FlowEvent, load_flow_schedule, solve_xirr, _quantile

TICKERS = ("QQQ", "SPY", "AGG", "SHY", "IEF", "TLT")
STOCK_TICKERS = ("QQQ", "SPY")
BOND_TICKERS = ("AGG", "SHY", "IEF", "TLT")
TARGET_CONVERSIONS = (30, 40, 50, 60, 70, 80, 90, 100)
TIMING_RULES = ("linear", "front_loaded", "back_loaded")
TIMING_LABELS = {"linear": "線性", "front_loaded": "前置轉換", "back_loaded": "後置轉換"}
INITIAL_CAPITAL_USD = 100_000.0
HORIZON_MONTHS = 120
DATA_START = dt.date(2003, 7, 1)
DATA_END = dt.date(2026, 9, 30)  # last fully completed month; do not treat a partial current month as a month-end mark
SOURCE_NAME = "Yahoo Finance chart API: dividend/split-adjusted close"
SOURCE_TEMPLATE = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1={period1}&period2={period2}&interval=1d&events=div%2Csplits&includeAdjustedClose=true"
COLORS = {
    "AGG": "#3274A1", "SHY": "#2A9D8F", "IEF": "#E07A35", "TLT": "#7966A8",
    "QQQ": "#C94C4C", "SPY": "#657184",
    "grid": "#E8EDF3", "ink": "#1E293B", "muted": "#64748B", "navy": "#183153",
}

def _date_to_epoch(value: dt.date) -> int:
    return int(dt.datetime.combine(value, dt.time(), tzinfo=dt.timezone.utc).timestamp())

def _fetch_json(url: str, retries: int = 4) -> dict:
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; reproducible-research/1.0)",
                    "Accept": "application/json,text/plain,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=40) as response:
                payload = response.read()
            return json.loads(payload.decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Yahoo history download failed after {retries} attempts: {url}: {last_error}")

def download_adjusted_close(ticker: str, start: dt.date = DATA_START, end: dt.date = DATA_END) -> dict[str, float]:
    """Return date -> adjusted close, rejecting empty, invalid or suspiciously short series."""
    query = urllib.parse.urlencode({
        "period1": _date_to_epoch(start),
        "period2": _date_to_epoch(end + dt.timedelta(days=1)),
        "interval": "1d",
        "events": "div,splits",
        "includeAdjustedClose": "true",
    })
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{query}"
    body = _fetch_json(url)
    chart = body.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"{ticker}: Yahoo returned error {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"{ticker}: no chart result")
    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    adj_series = indicators.get("adjclose") or []
    if not timestamps or not adj_series or not adj_series[0].get("adjclose"):
        raise RuntimeError(f"{ticker}: adjusted-close history is missing")
    adjusted = adj_series[0]["adjclose"]
    dates: dict[str, float] = {}
    for stamp, value in zip(timestamps, adjusted):
        if value is None:
            continue
        day = dt.datetime.fromtimestamp(int(stamp), tz=dt.timezone.utc).date()
        number = float(value)
        if start <= day <= end and math.isfinite(number) and number > 0:
            dates[day.isoformat()] = number
    if len(dates) < 1_000:
        raise RuntimeError(f"{ticker}: suspiciously short history ({len(dates)} rows); refusing to fake a long backtest")
    return dates

def load_common_market_panel() -> tuple[list[dt.date], dict[str, list[float]], list[int], dict]:
    downloaded = {ticker: download_adjusted_close(ticker) for ticker in TICKERS}
    common = set(downloaded[TICKERS[0]])
    for ticker in TICKERS[1:]:
        common &= set(downloaded[ticker])
    dates = sorted(dt.date.fromisoformat(value) for value in common)
    if not dates:
        raise ValueError("No common daily observations among all stock and bond proxies")
    prices = {
        ticker: [downloaded[ticker][day.isoformat()] for day in dates]
        for ticker in TICKERS
    }
    month_last: dict[tuple[int, int], int] = {}
    for index, day in enumerate(dates):
        month_last[(day.year, day.month)] = index
    monthly_indices = list(month_last.values())
    monthly_indices.sort(key=lambda index: dates[index])
    if len(monthly_indices) <= HORIZON_MONTHS:
        raise ValueError(
            f"Only {len(monthly_indices)} common month-end points; need more than {HORIZON_MONTHS}"
        )
    # Canonical compact representation is the frozen data payload whose SHA is recorded in every run.
    rows = ["date," + ",".join(TICKERS)]
    for i, day in enumerate(dates):
        rows.append(day.isoformat() + "," + ",".join(f"{prices[t][i]:.10f}" for t in TICKERS))
    canonical = ("\n".join(rows) + "\n").encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    metadata = {
        "provider": SOURCE_NAME,
        "source_url_template": SOURCE_TEMPLATE,
        "data_start_requested": DATA_START.isoformat(),
        "data_end_requested": DATA_END.isoformat(),
        "downloaded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "tickers": list(TICKERS),
        "bond_proxy_descriptions": {
            "AGG": "iShares Core U.S. Aggregate Bond ETF; Treasury, agency MBS and investment-grade corporate exposure",
            "SHY": "iShares 1-3 Year Treasury Bond ETF; short duration U.S. Treasuries",
            "IEF": "iShares 7-10 Year Treasury Bond ETF; intermediate U.S. Treasuries",
            "TLT": "iShares 20+ Year Treasury Bond ETF; long-duration U.S. Treasuries",
        },
        "daily_common_observations": len(dates),
        "first_common_date": dates[0].isoformat(),
        "last_common_date": dates[-1].isoformat(),
        "common_month_end_observations": len(monthly_indices),
        "raw_panel_canonical_sha256": digest,
        "data_note": "Adjusted close includes Yahoo historical split/dividend adjustment; ETF total-return proxy, not direct Treasury CUSIP marks. Canonical panel embedded as CSV artifact on each run.",
    }
    return dates, prices, monthly_indices, {"metadata": metadata, "canonical_csv": canonical.decode("utf-8")}

def _month_index_by_day(dates: list[dt.date], monthly_indices: list[int]) -> dict[int, int]:
    return {daily_index: month_no for month_no, daily_index in enumerate(monthly_indices)}

def _target_bond_weight(target_pct: int, elapsed_months: int, timing_rule: str = "linear") -> float:
    """Stepwise ten-year glidepath; target is the year-10 bond share of initial capital."""
    if timing_rule not in TIMING_RULES:
        raise ValueError(f"Unsupported timing rule: {timing_rule}")
    year = min(10, max(0, elapsed_months // 12))
    if timing_rule == "linear":
        progress = year / 10.0
    elif timing_rule == "front_loaded":
        # Reach half of the requested year-10 conversion by year 3, then the other
        # half evenly over years 4-10.
        progress = 0.5 * year / 3.0 if year <= 3 else 0.5 + 0.5 * (year - 3) / 7.0
    else:
        # Hold the all-stock starting allocation through year 5, then convert evenly
        # during years 6-10.
        progress = max(0.0, (year - 5) / 5.0)
    return target_pct / 100.0 * progress

def _set_target_weights(units: dict[str, float], prices: dict[str, list[float]], daily_index: int,
                        nav: float, bond_ticker: str, bond_weight: float) -> None:
    if nav <= 1e-10:
        for ticker in TICKERS:
            units[ticker] = 0.0
        return
    stock_weight = max(0.0, 1.0 - bond_weight)
    units["QQQ"] = nav * stock_weight * 0.5 / prices["QQQ"][daily_index]
    units["SPY"] = nav * stock_weight * 0.5 / prices["SPY"][daily_index]
    for ticker in BOND_TICKERS:
        units[ticker] = 0.0
    units[bond_ticker] = nav * bond_weight / prices[bond_ticker][daily_index]

def replay_one_window(
    dates: list[dt.date],
    prices: dict[str, list[float]],
    monthly_indices: list[int],
    start_month_index: int,
    bond_ticker: str,
    target_conversion_pct: int,
    schedule: dict[int, list[FlowEvent]] | None = None,
    initial_capital_usd: float = INITIAL_CAPITAL_USD,
    compute_xirr: bool = True,
    timing_rule: str = "linear",
) -> dict:
    """Daily adjusted-mark replay with annual rebalances and month-end external cash flows."""
    if bond_ticker not in BOND_TICKERS:
        raise ValueError(f"Unsupported bond proxy: {bond_ticker}")
    if target_conversion_pct not in TARGET_CONVERSIONS:
        raise ValueError(f"Target conversion must be one of {TARGET_CONVERSIONS}")
    if timing_rule not in TIMING_RULES:
        raise ValueError(f"Timing rule must be one of {TIMING_RULES}")
    schedule = schedule or {}
    start_daily_index = monthly_indices[start_month_index]
    end_month_index = start_month_index + HORIZON_MONTHS
    end_daily_index = monthly_indices[end_month_index]
    start_date, end_date = dates[start_daily_index], dates[end_daily_index]
    units = {ticker: 0.0 for ticker in TICKERS}
    units["QQQ"] = initial_capital_usd * 0.5 / prices["QQQ"][start_daily_index]
    units["SPY"] = initial_capital_usd * 0.5 / prices["SPY"][start_daily_index]
    investor_flows: list[tuple[dt.date, float]] = [(start_date, -initial_capital_usd)]
    deposits = requested_withdrawals = actual_withdrawals = shortfall = 0.0
    performance_index = initial_capital_usd
    nav_previous_after_flow = initial_capital_usd
    running_peak = performance_index
    max_drawdown = 0.0
    first_growth_depletion_month = None
    current_month_index = start_month_index
    # Fast map month-end daily row -> relative month in the active 10-year window.
    month_end_rel = {
        monthly_indices[global_month]: global_month - start_month_index
        for global_month in range(start_month_index + 1, end_month_index + 1)
    }

    for daily_index in range(start_daily_index + 1, end_daily_index + 1):
        nav_market = sum(units[ticker] * prices[ticker][daily_index] for ticker in TICKERS)
        if nav_previous_after_flow > 1e-10:
            performance_index *= nav_market / nav_previous_after_flow
        running_peak = max(running_peak, performance_index)
        if running_peak > 0:
            max_drawdown = min(max_drawdown, performance_index / running_peak - 1.0)
        nav_after_flow = nav_market
        relative_month = month_end_rel.get(daily_index)
        if relative_month is not None:
            # Cash events occur at the month-end close, in CSV order.
            for event in schedule.get(relative_month, []):
                if event.flow_type == "deposit":
                    amount = event.amount_usd
                    # Add capital pro rata to existing holdings, avoiding an accidental
                    # off-calendar rebalance. The next scheduled annual glidepath date changes
                    # target weights; the external deposit itself should not change strategy weights.
                    value_now = sum(units[ticker] * prices[ticker][daily_index] for ticker in TICKERS)
                    if value_now > 1e-10:
                        for ticker in TICKERS:
                            position_value = units[ticker] * prices[ticker][daily_index]
                            units[ticker] += amount * (position_value / value_now) / prices[ticker][daily_index]
                    else:
                        # If the portfolio was fully depleted, restart at the active step's target weights.
                        weight = _target_bond_weight(target_conversion_pct, relative_month - 1, timing_rule)
                        stock_weight = 1.0 - weight
                        units["QQQ"] += amount * stock_weight * 0.5 / prices["QQQ"][daily_index]
                        units["SPY"] += amount * stock_weight * 0.5 / prices["SPY"][daily_index]
                        units[bond_ticker] += amount * weight / prices[bond_ticker][daily_index]
                    deposits += amount
                    investor_flows.append((dates[daily_index], -amount))
                else:
                    requested_withdrawals += event.amount_usd
                    value = sum(units[ticker] * prices[ticker][daily_index] for ticker in TICKERS)
                    paid = min(event.amount_usd, max(0.0, value))
                    shortfall += event.amount_usd - paid
                    if value > 1e-10 and paid > 0:
                        factor = (value - paid) / value
                        for ticker in TICKERS:
                            units[ticker] *= factor
                        actual_withdrawals += paid
                        investor_flows.append((dates[daily_index], paid))
            nav_after_flow = sum(units[ticker] * prices[ticker][daily_index] for ticker in TICKERS)
            if nav_after_flow <= 1e-8 and first_growth_depletion_month is None:
                first_growth_depletion_month = relative_month
            # At the 12-month close, change the weights for the following year.
            if relative_month % 12 == 0:
                next_bond_weight = _target_bond_weight(target_conversion_pct, relative_month, timing_rule)
                _set_target_weights(units, prices, daily_index, nav_after_flow, bond_ticker, next_bond_weight)
                nav_after_flow = sum(units[ticker] * prices[ticker][daily_index] for ticker in TICKERS)
        nav_previous_after_flow = nav_after_flow

    terminal_nav = max(0.0, sum(units[ticker] * prices[ticker][end_daily_index] for ticker in TICKERS))
    elapsed_years = (end_date - start_date).days / 365.25
    twr_cagr = (performance_index / initial_capital_usd) ** (1.0 / elapsed_years) - 1.0 if elapsed_years > 0 and performance_index > 0 else None
    if terminal_nav > 1e-10:
        investor_flows.append((end_date, terminal_nav))
    if compute_xirr:
        xirr, xirr_status = solve_xirr(investor_flows)
    else:
        xirr, xirr_status = None, "NOT_COMPUTED_FOR_FIXED_WITHDRAWAL_STRESS"
    return {
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "bond_proxy": bond_ticker,
        "target_bond_conversion_pct_at_year10": target_conversion_pct,
        "timing_rule": timing_rule,
        "cashflow_mode": "custom_schedule" if schedule else "no_withdrawals",
        "initial_capital_usd": round(initial_capital_usd, 2),
        "additional_deposits_usd": round(deposits, 2),
        "total_capital_supplied_usd": round(initial_capital_usd + deposits, 2),
        "requested_withdrawals_usd": round(requested_withdrawals, 2),
        "actual_withdrawals_usd": round(actual_withdrawals, 2),
        "withdrawal_shortfall_usd": round(shortfall, 2),
        "terminal_nav_usd": round(terminal_nav, 2),
        "nominal_net_result_usd": round(actual_withdrawals + terminal_nav - deposits - initial_capital_usd, 2),
        "time_weighted_cagr": twr_cagr,
        "daily_max_drawdown": max_drawdown,
        "investor_xirr": xirr,
        "investor_xirr_status": xirr_status,
        "first_nav_depletion_month": first_growth_depletion_month,
        "ending_stock_weight": 1.0 - target_conversion_pct / 100.0,
        "ending_bond_weight": target_conversion_pct / 100.0,
    }

def summarize_group(rows: list[dict]) -> dict:
    terminals = [float(row["terminal_nav_usd"]) for row in rows]
    cagrs = [float(row["time_weighted_cagr"]) for row in rows if row["time_weighted_cagr"] is not None]
    drawdowns = [float(row["daily_max_drawdown"]) for row in rows]
    xirrs = [float(row["investor_xirr"]) for row in rows if row["investor_xirr"] is not None]
    withdrawals = [float(row["actual_withdrawals_usd"]) for row in rows]
    shortfalls = [float(row["withdrawal_shortfall_usd"]) for row in rows]
    return {
        "bond_proxy": rows[0]["bond_proxy"],
        "target_bond_conversion_pct_at_year10": rows[0]["target_bond_conversion_pct_at_year10"],
        "timing_rule": rows[0]["timing_rule"],
        "cashflow_mode": rows[0]["cashflow_mode"],
        "rolling_windows": len(rows),
        "median_terminal_nav_usd": round(_quantile(terminals, 0.50) or 0.0, 2),
        "p05_terminal_nav_usd": round(_quantile(terminals, 0.05) or 0.0, 2),
        "p95_terminal_nav_usd": round(_quantile(terminals, 0.95) or 0.0, 2),
        "worst_terminal_nav_usd": round(min(terminals), 2),
        "median_time_weighted_cagr": _quantile(cagrs, 0.50),
        "p05_time_weighted_cagr": _quantile(cagrs, 0.05),
        "worst_time_weighted_cagr": min(cagrs) if cagrs else None,
        "median_daily_max_drawdown": _quantile(drawdowns, 0.50),
        "worst_daily_max_drawdown": min(drawdowns),
        "windows_below_initial_capital_at_year10": sum(value < INITIAL_CAPITAL_USD for value in terminals),
        "windows_with_withdrawal_shortfall": sum(value > 0.01 for value in shortfalls),
        "median_actual_withdrawals_usd": round(_quantile(withdrawals, 0.50) or 0.0, 2),
        "p95_withdrawal_shortfall_usd": round(_quantile(shortfalls, 0.95) or 0.0, 2),
        "median_investor_xirr": _quantile(xirrs, 0.50),
        "xirr_defined_windows": len(xirrs),
    }

def run_backtest(dates, prices, monthly_indices, schedule: dict[int, list[FlowEvent]] | None = None,
                 initial_capital_usd: float = INITIAL_CAPITAL_USD) -> tuple[dict, list[dict]]:
    def fixed_monthly_schedule(amount: float) -> dict[int, list[FlowEvent]]:
        return {month: [FlowEvent(month, "withdrawal", amount, f"fixed monthly stress at {amount:.0f} USD")]
                for month in range(1, HORIZON_MONTHS + 1)}
    schedules = [("no_withdrawals", {}, True)]
    if schedule:
        schedules.append(("delayed_stepup_example", schedule, True))
    # Explicit stress tests, not a default investor spending assumption.
    schedules.extend([
        ("monthly_withdrawal_500_usd_stress", fixed_monthly_schedule(500.0), False),
        ("monthly_withdrawal_1000_usd_stress", fixed_monthly_schedule(1000.0), False),
    ])
    all_rows, summaries = [], []
    window_count = len(monthly_indices) - HORIZON_MONTHS
    if window_count <= 0:
        raise ValueError("Not enough common monthly observations for rolling 10-year backtests")
    for mode_name, active_schedule, compute_xirr in schedules:
        for timing_rule in TIMING_RULES:
            for bond in BOND_TICKERS:
                for target in TARGET_CONVERSIONS:
                    group = [
                        replay_one_window(dates, prices, monthly_indices, start, bond, target,
                                          schedule=active_schedule, initial_capital_usd=initial_capital_usd,
                                          compute_xirr=compute_xirr, timing_rule=timing_rule)
                        for start in range(window_count)
                    ]
                    for row in group:
                        row["cashflow_mode"] = mode_name
                    summaries.append(summarize_group(group))
                    all_rows.extend(group)
    report = {
        "schema": "stock-bond-glidepath-backtest.v1",
        "method": {
            "horizon_months": HORIZON_MONTHS,
            "rolling_windows_per_scenario": window_count,
            "initial_capital_usd": initial_capital_usd,
            "stock_sleeve": "QQQ/SPY 50/50 on each annual glidepath rebalance; both use dividend/split-adjusted close",
            "glidepath_rule": "Start at 0% bond. At each 12-month anniversary, rebalance to a stepwise target bond weight; the selected year-10 target is reached at month 120. Targets: 30%-100% in 10-point steps.",
            "timing_rules": {"linear": "equal conversion steps across years 1-10", "front_loaded": "reach 50% of final target by year 3, then reach the rest evenly by year 10", "back_loaded": "no bond allocation through year 5; convert evenly in years 6-10"},
            "bond_exposures": "AGG is broad aggregate fixed income; SHY, IEF and TLT are short-, intermediate- and long-duration Treasury ETF proxies.",
            "total_return_proxy": "Yahoo Finance adjusted close series; the adjusted-price ratio is used to approximate reinvested distributions and splits.",
            "rebalancing": "Annual rebalancing when target glidepath changes; no other rebalancing within each year. Holdings drift between annual steps.",
            "cashflows": "Optional event schedules are applied at month-end; withdrawals are pro rata and limited to NAV, shortfalls are explicit, and new deposits are invested pro rata into currently held positions so they do not force an off-calendar rebalance. XIRR is computed for no-flow and irregular-flow scenarios; fixed monthly stress schedules report time-weighted return and withdrawal shortfall without an expensive XIRR solve.",
            "drawdown": "Daily time-weighted return index tracks market movement, excluding external deposits and withdrawals from max-drawdown calculation.",
            "overlapping_windows_are_independent_probability": False,
            "floor_guarantee": False,
            "caveats": [
                "An ETF is not a maturity-matched individual Treasury bond or principal guarantee.",
                "Adjusted closes may be revised by the data provider; exact source payload SHA is recorded and uploaded.",
                "Historical overlapping windows are descriptive and are not independent trials or future probabilities.",
                "Taxes, transaction costs, bid/ask spreads and fund expense ratios beyond those reflected in ETF returns are not modelled.",
                "A 50/50 QQQ/SPY stock sleeve is a specified research baseline, not a claim of optimality.",
            ],
        },
        "data": {},
        "scenarios": summaries,
    }
    return report, all_rows

def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)

def _money(value: float) -> str:
    return "$" + f"{value:,.0f}"

def _svg_open(title: str, subtitle: str, width: int = 1180, height: int = 620) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<title>{_esc(title)}</title><desc>{_esc(subtitle)}</desc><rect width="100%" height="100%" rx="16" fill="#FFFFFF"/>'
            f'<text x="36" y="42" font-family="Arial,sans-serif" font-size="25" font-weight="700" fill="{COLORS["navy"]}">{_esc(title)}</text>'
            f'<text x="36" y="70" font-family="Arial,sans-serif" font-size="13" fill="{COLORS["muted"]}">{_esc(subtitle)}</text>')

def _svg_end(footer: str) -> str:
    return f'<text x="36" y="600" font-family="Arial,sans-serif" font-size="11" fill="{COLORS["muted"]}">{_esc(footer)}</text></svg>'

def render_metric_chart(rows: list[dict], metric: str, title: str, subtitle: str,
                        as_percent: bool = False, downside: bool = False, value_format: str = "usd") -> str:
    width, height = 1180, 620
    x0, y0, plot_w, plot_h = 94, 112, 800, 410
    bonds = list(BOND_TICKERS)
    targets = list(TARGET_CONVERSIONS)
    data = {(row["bond_proxy"], row["target_bond_conversion_pct_at_year10"]): row for row in rows}
    values = [float(data[(bond, target)][metric]) for bond in bonds for target in targets
              if data[(bond, target)].get(metric) is not None]
    if not values:
        raise ValueError(f"No values to render for {metric}")
    ymin, ymax = min(values), max(values)
    if as_percent:
        ymin = min(ymin, 0.0)
        ymax = max(ymax, 0.0)
    pad = (ymax - ymin) * 0.12 or 0.01
    ymin, ymax = ymin - pad, ymax + pad
    if as_percent:
        ymin, ymax = max(-1.0, ymin), min(1.0, ymax)
    span = ymax - ymin or 1.0
    svg = [_svg_open(title, subtitle, width, height)]
    for tick in range(6):
        value = ymin + span * tick / 5
        y = y0 + plot_h - (value - ymin) / span * plot_h
        svg.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{x0+plot_w}" y2="{y:.2f}" stroke="{COLORS["grid"]}"/>')
        label = f"{value*100:.1f}%" if as_percent else (str(int(round(value))) if value_format == "count" else _money(value))
        svg.append(f'<text x="{x0-10}" y="{y+4:.2f}" text-anchor="end" font-size="11" fill="{COLORS["muted"]}">{_esc(label)}</text>')
    for idx, target in enumerate(targets):
        x = x0 + plot_w * idx / (len(targets)-1)
        svg.append(f'<line x1="{x:.2f}" y1="{y0}" x2="{x:.2f}" y2="{y0+plot_h}" stroke="{COLORS["grid"]}"/>')
        svg.append(f'<text x="{x:.2f}" y="{y0+plot_h+22}" text-anchor="middle" font-size="11" fill="{COLORS["muted"]}">{target}%</text>')
    for bond in bonds:
        vals = [data[(bond,target)].get(metric) for target in targets]
        points = []
        for idx, value in enumerate(vals):
            if value is None: continue
            x = x0 + plot_w * idx / (len(targets)-1)
            y = y0 + plot_h - (float(value)-ymin)/span*plot_h
            points.append((x,y))
        if points:
            path = " ".join(("M" if i==0 else "L")+f" {x:.2f} {y:.2f}" for i,(x,y) in enumerate(points))
            svg.append(f'<path d="{path}" fill="none" stroke="{COLORS[bond]}" stroke-width="3"/>')
            for x,y in points:
                svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{COLORS[bond]}"/>')
    lx, ly = 940, 142
    for bond in bonds:
        svg.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+24}" y2="{ly}" stroke="{COLORS[bond]}" stroke-width="4"/>')
        svg.append(f'<text x="{lx+32}" y="{ly+4}" font-size="13" fill="{COLORS["ink"]}">{bond}</text>')
        ly += 31
    svg.append(_svg_end("X 軸為第10年債券目標比重；滾動窗口相互重疊。ETF 代理不代表到期本金保證。"))
    return "".join(svg)

def render_html(outdir: Path, report: dict, charts: dict[str,str]) -> None:
    sections = [
        ("01_terminal_wealth.svg", "第10年終值", "中位終值依 30%–100% 目標比較；另有 P05 與最差窗口在 CSV/JSON。"),
        ("02_daily_drawdown.svg", "每日最大回撤", "使用日頻調整價形成時間加權績效指數，外部提款／投入不直接算成回撤。"),
        ("03_time_weighted_cagr.svg", "年化時間加權回報", "按逐年目標比例、年度再平衡與債券 ETF 代理的實際歷史回報計算。"),
        ("04_withdrawal_shortfall_sample.svg", "遞增提款示例", "同時展示每月取款以外的延遲、升降與中途再投入情境。"),
        ("05_withdrawal_shortfall_500.svg", "每月提款500美元壓力測試", "十年累計要求提款60,000美元；不是預設支出。"),
        ("06_withdrawal_shortfall_1000.svg", "每月提款1,000美元壓力測試", "十年累計要求提款120,000美元；不是預設支出。"),
    ]
    page = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<title>股票轉債回測</title><style>body{max-width:1240px;margin:20px auto;padding:0 16px;font-family:system-ui,sans-serif;color:#1e293b;background:#f6f8fb}section{padding:16px;margin:18px 0;background:white;border:1px solid #d7dee8;border-radius:14px}section svg{width:100%;height:auto}.note{padding:12px;background:#fff1e5;border-radius:8px}</style></head><body>",
            "<h1>股票逐年轉債券：30%–100% 歷史比較</h1>",
            f'<p>資料來源 SHA-256：<code>{_esc(report["data"]["raw_panel_canonical_sha256"])}</code>；每日共同觀測 {report["data"]["daily_common_observations"]}；十年窗口 {report["method"]["rolling_windows_per_scenario"]}。</p>',
            "<p class='note'><b>重要限制：</b>股票和債券皆使用交易所 ETF 調整收市價作總回報代理。AGG 是綜合債，SHY/IEF/TLT 是不同久期的美國國債 ETF；它們都不是持有至指定到期日的 STRIPS，也不保證本金。窗口重疊、未計稅費及外部成本。</p>"]
    for filename, title, description in sections:
        page.extend(["<section><h2>", _esc(title), "</h2><p>", _esc(description), "</p>", charts[filename], "</section>"])
    page.append("<section><h2>可核對的程式／口徑</h2><p>原始每日價格快照、各窗口逐行 CSV、彙總 JSON、四張 SVG 和本 HTML 一併上傳於本次 GitHub Actions artifact。</p></section></body></html>")
    (outdir / "index.html").write_text("".join(page) + "\n", encoding="utf-8")

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    fields = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def generate_results(outdir: Path, schedule_path: Path | None = None) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    dates, prices, monthly_indices, source = load_common_market_panel()
    schedule = load_flow_schedule(schedule_path) if schedule_path else None
    report, rows = run_backtest(dates, prices, monthly_indices, schedule=schedule)
    report["data"] = source["metadata"]
    (outdir / "historical_adjusted_close_panel.csv").write_text(source["canonical_csv"], encoding="utf-8")
    write_csv(outdir / "stock_bond_glidepath_windows.csv", rows)
    summaries = report["scenarios"]
    noflow = [row for row in summaries if row["cashflow_mode"] == "no_withdrawals"]
    sample_flow = [row for row in summaries if row["cashflow_mode"] == "delayed_stepup_example"]
    monthly_500 = [row for row in summaries if row["cashflow_mode"] == "monthly_withdrawal_500_usd_stress"]
    monthly_1000 = [row for row in summaries if row["cashflow_mode"] == "monthly_withdrawal_1000_usd_stress"]
    charts = {
        "01_terminal_wealth.svg": render_metric_chart(noflow, "median_terminal_nav_usd",
            "第10年終值：比較轉債30%–100%",
            "四種債券代理；曲線為 10 年滾動窗口終值中位數", False),
        "02_daily_drawdown.svg": render_metric_chart(noflow, "median_daily_max_drawdown",
            "最大回撤：比較轉債30%–100%",
            "每個窗口先算每日時間加權最大回撤，再比較中位數", True),
        "03_time_weighted_cagr.svg": render_metric_chart(noflow, "median_time_weighted_cagr",
            "年化時間加權回報：比較轉債30%–100%",
            "調整收市價代理總回報；不等於未來預期回報", True),
        "04_withdrawal_shortfall_sample.svg": render_metric_chart(sample_flow, "windows_with_withdrawal_shortfall",
            "遞增提款示例：無法全額支付的歷史窗口數",
            "示例合計提款12,800美元、後續投入5,000美元；不是預設支出", False, value_format="count"),
        "05_withdrawal_shortfall_500.svg": render_metric_chart(monthly_500, "windows_with_withdrawal_shortfall",
            "固定每月提款500美元：缺口窗口數",
            "十年累計要求提款60,000美元；純壓力情境，不是使用者預設", False, value_format="count"),
        "06_withdrawal_shortfall_1000.svg": render_metric_chart(monthly_1000, "windows_with_withdrawal_shortfall",
            "固定每月提款1,000美元：缺口窗口數",
            "十年累計要求提款120,000美元；純壓力情境，不是使用者預設", False, value_format="count"),
    }
    for filename, content in charts.items():
        (outdir / filename).write_text(content, encoding="utf-8")
    report["cashflow_schedule"] = {
        "rows": sum(len(v) for v in (schedule or {}).values()),
        "withdrawal_total_usd": round(sum(e.amount_usd for group in (schedule or {}).values() for e in group if e.flow_type == "withdrawal"), 2),
        "deposit_total_usd": round(sum(e.amount_usd for group in (schedule or {}).values() for e in group if e.flow_type == "deposit"), 2),
    }
    (outdir / "stock_bond_glidepath_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_html(outdir, report, charts)
    return report

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--flows-csv", type=Path)
    args = parser.parse_args()
    report = generate_results(args.outdir, args.flows_csv)
    compact = {
        "schema": report["schema"],
        "data": report["data"],
        "rolling_windows": report["method"]["rolling_windows_per_scenario"],
        "summary_count": len(report["scenarios"]),
        "summaries": [row for row in report["scenarios"] if row["cashflow_mode"] == "no_withdrawals"],
        "cashflow_schedule": report.get("cashflow_schedule"),
        "output_dir": args.outdir.as_posix(),
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
