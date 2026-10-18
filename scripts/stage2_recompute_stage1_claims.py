#!/usr/bin/env python3
"""Recompute key numerical claims from Stage 1 using repository-pinned inputs.

Read-only, no third-party dependencies, no network access. Outputs JSON only.
The historical-window frequencies below are descriptive overlapping-window
frequencies on the QQQ field in data_market_data.csv, not future probabilities
and not verified dividend-reinvested total returns.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MARKET_CSV = ROOT / "artifacts" / "pulse_v2" / "data_market_data.csv"
FLOOR_JSON = ROOT / "research" / "rolling_10y_floor" / "rolling_floor_result.json"
BACKTEST_JSON = ROOT / "artifacts" / "backtest-result.json"
CPCV_JSON = ROOT / "research" / "refit_cpcv.json"
COST_JSON = ROOT / "research" / "cost_oos_cpcv_survival.json"
PROTECTED_TS = ROOT / "src" / "lib" / "pulse" / "protected.ts"

STAGE1_PINNED_SHA = "a4e04edf7d28978615d34652299b2964afc39a14"
EXPECTED_SOURCE_BLOB_SHA = "048f335b359848e1c1f261a488dd7366668806d1"
EXPECTED_INPUT_BLOBS = {
    "artifacts/pulse_v2/data_market_data.csv": "048f335b359848e1c1f261a488dd7366668806d1",
    "research/rolling_10y_floor/rolling_floor_result.json": "19e1b512c1677d000de44ee5cf5674f0e476a6eb",
    "artifacts/backtest-result.json": "4c737eb299b4226d8e3d1265e606b8699a95a0f4",
    "research/refit_cpcv.json": "3e623fcf32f3a18ce1ec4162f92d4c3443974e38",
    "research/cost_oos_cpcv_survival.json": "c12f0b79237341f99a3e39f347f6b8318e8904df",
    "src/lib/pulse/protected.ts": "88eca992eef600541dff1e54f51ce30feadd64b0",
    "src/lib/pulse/rolling-floor.ts": "131c7ea3022af31a3c3e46ae0e9de76bec7fa084",
    "src/data/universe.json": "43c1b3053d17b278cfc01bb0b87e41679f3e85c9",
    "artifacts/oos_family/manifest.json": "4f146ef9bcf65e19f5ca9e421f4028fb806e93f5",
    "research/evidence_v1/STRATEGY_LOCK.json": "1ba879f24e367570c3a4e3b04bca607450dc2b8d",
    "research/strategy_instance_v1/run_instance.py": "1757feda167a360fa63197d11d73835ce8f73526",
}


def verify_pinned_input_blobs() -> dict[str, str]:
    """Require all critical files to match Stage 1's exact Git blob IDs."""
    import subprocess

    verified: dict[str, str] = {}
    for relative, expected in EXPECTED_INPUT_BLOBS.items():
        path = ROOT / relative
        if not path.is_file():
            raise SystemExit(f"Missing pinned Stage-1 input: {relative}")
        actual = subprocess.run(
            ["git", "hash-object", str(path)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()
        if actual != expected:
            raise SystemExit(
                f"INPUT HASH MISMATCH for {relative}: expected {expected}, got {actual}; "
                "refuse to mix Stage-1 evidence with changed inputs."
            )
        verified[relative] = actual
    return verified


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_daily_prices(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "Date" not in reader.fieldnames or "QQQ" not in reader.fieldnames:
            raise ValueError("Expected Date and QQQ columns in market data CSV")
        fields = list(reader.fieldnames)
        rows: list[dict[str, Any]] = []
        for raw in reader:
            try:
                value = float(raw["QQQ"])
            except (TypeError, ValueError):
                continue
            if not raw.get("Date") or not math.isfinite(value) or value <= 0:
                continue
            rows.append({"date": raw["Date"], "qqq": value})
    rows.sort(key=lambda row: row["date"])
    if len(rows) < 121:
        raise ValueError("Insufficient QQQ rows for a ten-year monthly replay")
    return rows, fields


def month_end_prices(daily: list[dict[str, Any]]) -> list[dict[str, Any]]:
    last_by_month: dict[str, dict[str, Any]] = {}
    for row in daily:
        last_by_month[row["date"][:7]] = row
    return [last_by_month[key] for key in sorted(last_by_month)]


def maximum_drawdown(rows: list[dict[str, Any]], start: str, end: str) -> dict[str, Any]:
    values = [row for row in rows if start <= row["date"] <= end]
    if not values:
        return {"start": None, "end": None, "max_drawdown": None}
    peak = float(values[0]["qqq"])
    peak_date = values[0]["date"]
    worst = 0.0
    worst_peak_date = peak_date
    worst_trough_date = peak_date
    for row in values:
        value = float(row["qqq"])
        if value > peak:
            peak, peak_date = value, row["date"]
        dd = value / peak - 1.0
        if dd < worst:
            worst = dd
            worst_peak_date = peak_date
            worst_trough_date = row["date"]
    return {
        "start": values[0]["date"],
        "end": values[-1]["date"],
        "observations": len(values),
        "max_drawdown": worst,
        "peak_date": worst_peak_date,
        "trough_date": worst_trough_date,
    }


def recompute_10y_windows(daily: list[dict[str, Any]]) -> dict[str, Any]:
    monthly = month_end_prices(daily)
    horizon = 120
    windows: list[dict[str, Any]] = []
    for start in range(len(monthly) - horizon):
        terminal = float(monthly[start + horizon]["qqq"])
        start_price = float(monthly[start]["qqq"])
        lump = terminal / start_price
        # Same timing as the Stage-1 clock replay: 120 equal purchases at
        # months 0..119, valued at month 120. No extra contributions.
        dca = sum(
            terminal / float(monthly[start + k]["qqq"])
            for k in range(horizon)
        ) / horizon
        windows.append({
            "start_date": monthly[start]["date"],
            "end_date": monthly[start + horizon]["date"],
            "lump_terminal_multiple": lump,
            "clock_dca_terminal_multiple": dca,
        })
    if not windows:
        raise ValueError("No complete ten-year windows found")
    lump_losses = [row for row in windows if row["lump_terminal_multiple"] < 1.0]
    dca_losses = [row for row in windows if row["clock_dca_terminal_multiple"] < 1.0]
    worst_lump = min(windows, key=lambda row: row["lump_terminal_multiple"])
    worst_dca = min(windows, key=lambda row: row["clock_dca_terminal_multiple"])
    return {
        "basis": "monthly last-observation QQQ price field; no dedicated dividend or total-return field in CSV",
        "daily_rows": len(daily),
        "daily_first_date": daily[0]["date"],
        "daily_last_date": daily[-1]["date"],
        "monthly_observations": len(monthly),
        "monthly_first_date": monthly[0]["date"],
        "monthly_last_date": monthly[-1]["date"],
        "horizon_months": horizon,
        "overlapping_window_count": len(windows),
        "lump_sum_loss_windows": len(lump_losses),
        "lump_sum_nonloss_frequency": 1.0 - len(lump_losses) / len(windows),
        "lump_sum_worst_window": worst_lump,
        "clock_dca_loss_windows": len(dca_losses),
        "clock_dca_nonloss_frequency": 1.0 - len(dca_losses) / len(windows),
        "clock_dca_worst_window": worst_dca,
        "worst_lump_daily_drawdown": maximum_drawdown(
            daily, worst_lump["start_date"], worst_lump["end_date"]
        ),
        "interpretation_limit": (
            "These are overlapping historical windows, not 211 independent trials "
            "or an estimate of future ten-year success probability. The source CSV "
            "does not contain an identified dividend-reinvested total-return series."
        ),
    }


def recompute_floor_diagnostics(path: Path) -> dict[str, Any]:
    obj = read_json(path)
    states = Counter()
    state_steps = 0
    starts = obj.get("starts", {})
    replays = starts.values() if isinstance(starts, dict) else (starts if isinstance(starts, list) else [])
    for replay in replays:
        for point in replay.get("divergenceStateByDate", []):
            states[point.get("state", "UNKNOWN")] += 1
            state_steps += 1
    data = obj.get("data", {})
    replay = obj.get("replay", {})
    coupled = replay.get("coupled", {})
    return {
        "version": obj.get("version"),
        "evidence_class": obj.get("evidenceClass"),
        "qqq_data": data.get("QQQ"),
        "proxy_data": {name: data.get(name) for name in ("NASDAQ100", "NASDAQCOM")},
        "rolling_windows": replay.get("n"),
        "coupled_nonloss_frequency": coupled.get("nonLossRate"),
        "coupled_worst_terminal_multiple": coupled.get("worstTerminal"),
        "coupled_worst_max_drawdown": coupled.get("worstMaxDd"),
        "all_window_state_steps": state_steps,
        "states": dict(states),
        "thin_frequency": states.get("THIN", 0) / state_steps if state_steps else None,
        "clock_fallback_code_verified_by": "src/lib/pulse/rolling-floor.ts: replayOne fallback uses clockTarget when robustTarget is null and mandatoryAdd as the minimum monthly investment",
    }


def accounting_diagnostic(path: Path) -> dict[str, Any]:
    code = path.read_text(encoding="utf-8")
    required = {
        "daily_mark_differences": "putPnl += lot.contracts * (mid - lot.lastMark)",
        "purchase_outlay_at_ask": "const pay = mid * (1 + spec.spread)",
        "full_premium_deducted": "premium += contracts * pay",
        "premium_subtracted_from_daily_return": "(putPnl - premium) / equity",
        "lot_opened_at_mid_mark": "lots.push({ strike, expiryI, contracts, lastMark: mid, openedI: i })",
    }
    found = {key: value in code for key, value in required.items()}
    entry_mid, exit_mid, spread, contracts = 10.0, 12.0, 0.10, 1.0
    purchase_ask = entry_mid * (1.0 + spread)
    exit_bid = exit_mid * (1.0 - spread)
    current_roll_pnl = (
        (exit_mid - entry_mid)
        + (exit_bid - exit_mid)
        - contracts * purchase_ask
    ) * contracts
    true_cashflow_pnl = contracts * (exit_bid - purchase_ask)
    excess_loss = current_roll_pnl - true_cashflow_pnl
    return {
        "source_path": str(path.relative_to(ROOT)),
        "code_markers_present": found,
        "toy_entry_mid": entry_mid,
        "toy_exit_mid": exit_mid,
        "toy_spread_fraction": spread,
        "toy_contracts": contracts,
        "purchase_ask": purchase_ask,
        "exit_bid": exit_bid,
        "current_code_pnl_for_roll": current_roll_pnl,
        "cashflow_correct_pnl_for_roll": true_cashflow_pnl,
        "current_minus_correct": excess_loss,
        "excess_loss_equals_one_entry_mid_times_contracts": math.isclose(
            excess_loss, -entry_mid * contracts, rel_tol=0.0, abs_tol=1e-12
        ),
        "explanation": (
            "The code subtracts the full ask premium and separately sums mark changes "
            "starting from lastMark=entry mid. Without crediting the opening mark as "
            "an asset, the entry mid is charged twice. Toy example: pay 11, later sell "
            "at bid 10.8; correct P&L -0.2, current algebra -10.2."
        ),
    }


def treasury_scenario_diagnostics() -> dict[str, Any]:
    # These are Stage-1 assumptions, not executable broker quotes.
    strip_yield = 0.0515
    real_yield = 0.0286
    inflation = 0.0235
    horizon_years = 10
    semiannual_periods = horizon_years * 2
    pv_100k_face = 100_000 / ((1 + strip_yield / 2) ** semiannual_periods)
    fv_60_5k = 60_500 * ((1 + strip_yield / 2) ** semiannual_periods)
    inflation_factor = (1 + inflation) ** horizon_years
    tips_terminal = 14_500 * ((1 + real_yield) * (1 + inflation)) ** horizon_years
    tips_real_terminal = 14_500 * (1 + real_yield) ** horizon_years
    equity_expected_at_8_8 = 25_000 * (1.088 ** horizon_years)
    reported_a1 = 100_000
    a2_as_reported = 24_230
    equity_crash_83 = 25_000 * 0.17
    return {
        "assumptions_not_quotes": {
            "strip_nominal_yield": strip_yield,
            "tips_real_yield": real_yield,
            "inflation": inflation,
            "horizon_years": horizon_years,
        },
        "pv_for_100k_face_at_assumed_strip_yield": pv_100k_face,
        "terminal_value_if_all_60500_buys_at_assumed_strip_yield": fv_60_5k,
        "implied_inflation_factor": inflation_factor,
        "nominal_required_for_100k_real_break_even": 100_000 * inflation_factor,
        "tips_14500_terminal_nominal_from_compounded_real_and_cpi": tips_terminal,
        "tips_14500_terminal_in_start_year_real_dollars": tips_real_terminal,
        "equity_terminal_if_8_8pct_cagr": equity_expected_at_8_8,
        "reported_components_sum_if_a1_100000": reported_a1 + a2_as_reported + equity_expected_at_8_8,
        "reported_components_sum_if_a1_100590": 100_590 + a2_as_reported + 58_040,
        "reported_total_nav": 182_270,
        "reported_total_when_component_table_a1_is_100590": 100_590 + a2_as_reported + 58_040,
        "real_nav_when_only_nominal_floor_plus_reported_tips_remain": (reported_a1 + a2_as_reported) / inflation_factor,
        "nominal_nav_if_equity_sleeve_is_wiped_out": reported_a1 + a2_as_reported,
        "nominal_nav_under_reported_minus_83pct_equity_scenario": reported_a1 + a2_as_reported + equity_crash_83,
        "real_nav_under_reported_minus_83pct_equity_scenario": (
            reported_a1 + a2_as_reported + equity_crash_83
        ) / inflation_factor,
        "interpretation_limit": (
            "DGS10/DFII10/T10YIE are constant-maturity benchmark series, not an executable "
            "2036 STRIPS/TIPS bid/ask quote. Exact security cash flows, accrued amounts, "
            "fees, taxes and investor jurisdiction remain unpriced."
        ),
    }


def main() -> int:
    missing = [p for p in (MARKET_CSV, FLOOR_JSON, BACKTEST_JSON, CPCV_JSON, COST_JSON, PROTECTED_TS) if not p.is_file()]
    if missing:
        raise SystemExit("Missing required repository input(s): " + ", ".join(str(p) for p in missing))

    verified_input_blobs = verify_pinned_input_blobs()
    daily, fields = load_daily_prices(MARKET_CSV)
    backtest = read_json(BACKTEST_JSON)
    cpcv = read_json(CPCV_JSON)
    cost = read_json(COST_JSON)
    try:
        import subprocess
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        head = "UNAVAILABLE"

    no_identified_total_return_series = not any(
        any(token in field.lower() for token in ("dividend", "adjclose", "adjusted_close", "total_return"))
        for field in fields
    )
    result = {
        "schema": "stage2-recompute-stage1-claims-v1",
        "execution_head_sha": head,
        "stage1_pinned_source_sha": STAGE1_PINNED_SHA,
        "expected_market_csv_git_blob_sha": EXPECTED_SOURCE_BLOB_SHA,
        "verified_input_git_blobs": verified_input_blobs,
        "price_window_replay": recompute_10y_windows(daily),
        "data_field_limit": {
            "csv_columns": fields,
            "no_identified_dividend_or_total_return_column": no_identified_total_return_series,
        },
        "rolling_floor": recompute_floor_diagnostics(FLOOR_JSON),
        "protected_put_accounting": accounting_diagnostic(PROTECTED_TS),
        "protected_put_recorded_metrics": {
            "full_cagr": backtest.get("full", {}).get("cagr"),
            "full_max_drawdown": backtest.get("full", {}).get("maxDd"),
            "buy_hold_qqq_full_cagr": backtest.get("buyHoldQQQ", {}).get("full", {}).get("cagr"),
            "buy_hold_qqq_full_max_drawdown": backtest.get("buyHoldQQQ", {}).get("full", {}).get("maxDd"),
            "full_reported_premium_drag": backtest.get("extras", {}).get("full", {}).get("premiumDrag"),
            "full_reported_premium_sum": backtest.get("extras", {}).get("full", {}).get("premiumSum"),
            "data_layer_disclaimer": backtest.get("dataLayer"),
        },
        "refit_cpcv": cpcv.get("summary"),
        "cost_sensitivity_2x": next(
            (row for row in cost.get("cost_multiplier", []) if row.get("cost_mult") == 2), None
        ),
        "treasury_arithmetic": treasury_scenario_diagnostics(),
        "evidence_status": {
            "recomputable_from_checked_in_prices": True,
            "verified_executable_strips_or_tips_quote": False,
            "verified_tax_adjusted_floor": False,
            "verified_opra_historical_option_fills": False,
            "future_ten_year_success_probability_estimated": False,
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
