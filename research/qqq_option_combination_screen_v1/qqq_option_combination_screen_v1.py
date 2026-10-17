#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

OPTIONS_SHA256 = "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734"
UNDERLYING_SHA256 = "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351"
CORE_WEIGHT = 0.42
PUT_ANNUAL_PREMIUM_BUDGET = 0.020
CALL_MAX_LOSS_BUDGET = 0.008
DTE_MIN, DTE_MAX = 18, 35
ROLL_DTE = 7
VARIANTS = ("CORE_ONLY", "CORE_PLUS_PUT_DEBIT", "CORE_PLUS_CALL_CREDIT", "CORE_PLUS_CALL_AND_PUT")
COSTS = {"BASE": {"slippage_per_leg_per_share": 0.05, "commission_per_contract_per_side": 0.65},
         "STRESS": {"slippage_per_leg_per_share": 0.10, "commission_per_contract_per_side": 0.65}}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def good_quote(q: dict[str, float] | None) -> bool:
    return bool(q is not None and np.isfinite(q["bid"]) and np.isfinite(q["ask"])
                and q["bid"] >= 0 and q["ask"] > 0 and q["ask"] >= q["bid"])


def select_target(rows: pd.DataFrame, target_delta: float) -> dict[str, Any] | None:
    if rows.empty:
        return None
    x = rows.copy()
    x["delta_error"] = (x["delta"] - target_delta).abs()
    x["quoted_spread"] = x["ask"] - x["bid"]
    x["volume_rank"] = pd.to_numeric(x["volume"], errors="coerce").fillna(0)
    x = x.sort_values(["delta_error", "quoted_spread", "volume_rank"],
                      ascending=[True, True, False], kind="stable")
    return x.iloc[0].to_dict()


def select_vertical_for_expiry(chain: pd.DataFrame, spot: float, kind: str) -> dict[str, Any] | None:
    if kind == "CALL_CREDIT":
        shorts = chain[(chain["strike"] > spot) & (chain["delta"] > 0.02) & (chain["delta"] < 0.40)]
        short = select_target(shorts, 0.16)
        if short is None:
            return None
        wings = chain[(chain["strike"] > float(short["strike"])) &
                      (chain["delta"] > 0) & (chain["delta"] < float(short["delta"]))]
        wing = select_target(wings, 0.08)
        if wing is None or float(wing["strike"]) <= float(short["strike"]):
            return None
        return {
            "sleeve": kind, "expiry": pd.Timestamp(short["expiration"]),
            "short_id": str(short["contract_id"]), "short_strike": float(short["strike"]),
            "wing_id": str(wing["contract_id"]), "wing_strike": float(wing["strike"]),
            "selection_delta_short": float(short["delta"]), "selection_delta_wing": float(wing["delta"]),
            "width": float(wing["strike"]) - float(short["strike"]),
        }

    puts = chain[(chain["strike"] < spot) & (chain["delta"] < -0.01) & (chain["delta"] > -0.55)]
    long_put = select_target(puts, -0.25)
    if long_put is None:
        return None
    shorts = chain[(chain["strike"] < float(long_put["strike"])) &
                   (chain["delta"] < 0) & (chain["delta"] > float(long_put["delta"]))]
    short_put = select_target(shorts, -0.10)
    if short_put is None or float(short_put["strike"]) >= float(long_put["strike"]):
        return None
    return {
        "sleeve": kind, "expiry": pd.Timestamp(long_put["expiration"]),
        "long_id": str(long_put["contract_id"]), "long_strike": float(long_put["strike"]),
        "short_id": str(short_put["contract_id"]), "short_strike": float(short_put["strike"]),
        "selection_delta_long": float(long_put["delta"]), "selection_delta_short": float(short_put["delta"]),
        "width": float(long_put["strike"]) - float(short_put["strike"]),
    }


def build_candidates(options_path: Path, dates: pd.Series,
                     spot_by_date: dict[pd.Timestamp, float]) -> tuple[dict[tuple[pd.Timestamp, str], dict[str, Any]], set[str], dict[str, int]]:
    con = duckdb.connect()
    try:
        rows = con.execute("""
            SELECT CAST(date AS DATE) AS date,
                   CAST(expiration AS DATE) AS expiration,
                   CAST(contract_id AS VARCHAR) AS contract_id,
                   UPPER(CAST(type AS VARCHAR)) AS type,
                   CAST(strike AS DOUBLE) AS strike,
                   CAST(bid AS DOUBLE) AS bid,
                   CAST(ask AS DOUBLE) AS ask,
                   CAST(mark AS DOUBLE) AS mark,
                   CAST(delta AS DOUBLE) AS delta,
                   COALESCE(CAST(volume AS DOUBLE), 0) AS volume
            FROM read_parquet(?)
            WHERE CAST(date AS DATE) BETWEEN ? AND ?
              AND UPPER(CAST(type AS VARCHAR)) IN ('CALL', 'PUT')
              AND delta IS NOT NULL
              AND bid IS NOT NULL AND ask IS NOT NULL
              AND CAST(bid AS DOUBLE) >= 0
              AND CAST(ask AS DOUBLE) > 0
              AND CAST(ask AS DOUBLE) >= CAST(bid AS DOUBLE)
              AND CAST(expiration AS DATE) BETWEEN
                  CAST(date AS DATE) + INTERVAL 21 DAY AND
                  CAST(date AS DATE) + INTERVAL 36 DAY
        """, [str(options_path), dates.iloc[0].date(), dates.iloc[-1].date()]).df()
    finally:
        con.close()
    if rows.empty:
        raise RuntimeError("No valid candidate option quotes found in requested date range.")

    rows["date"] = pd.to_datetime(rows["date"]).dt.normalize()
    rows["expiration"] = pd.to_datetime(rows["expiration"]).dt.normalize()
    rows["contract_id"] = rows["contract_id"].astype(str)
    candidate_map: dict[tuple[pd.Timestamp, str], dict[str, Any]] = {}
    rejections = {"NO_CALL_VERTICAL_ON_SELECTION_DATE": 0, "NO_PUT_VERTICAL_ON_SELECTION_DATE": 0}

    for dt, day in rows.groupby("date", sort=True):
        dt = pd.Timestamp(dt)
        spot = spot_by_date.get(dt)
        if spot is None or not np.isfinite(spot) or spot <= 0:
            continue
        for kind, option_type in (("CALL_CREDIT", "CALL"), ("PUT_DEBIT", "PUT")):
            typed = day[day["type"] == option_type]
            selected = None
            if not typed.empty:
                expiries = sorted(pd.Timestamp(x) for x in typed["expiration"].unique())
                for expiry in expiries:
                    chain = typed[typed["expiration"] == expiry]
                    selected = select_vertical_for_expiry(chain, float(spot), kind)
                    if selected is not None:
                        selected["selection_date"] = dt
                        break
            if selected is None:
                rejections[f"NO_{option_type}_VERTICAL_ON_SELECTION_DATE"] += 1
            else:
                candidate_map[(dt, kind)] = selected

    ids: set[str] = set()
    for c in candidate_map.values():
        ids.update(v for k, v in c.items() if k.endswith("_id"))
    return candidate_map, ids, rejections


def load_underlying(path: Path, start_date: str, end_date: str) -> pd.DataFrame:
    raw = pd.read_parquet(path)
    raw.columns = [str(c).lower() for c in raw.columns]
    if "date" not in raw.columns or "close" not in raw.columns:
        raise ValueError("QQQ underlying file must contain date and close columns.")
    raw["date"] = pd.to_datetime(raw["date"]).dt.tz_localize(None).dt.normalize()
    raw["close"] = pd.to_numeric(raw["close"], errors="coerce")
    raw = raw[(raw["date"] >= pd.Timestamp(start_date)) & (raw["date"] <= pd.Timestamp(end_date))]
    raw = raw.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)
    if len(raw) < 2:
        raise RuntimeError("Fewer than two QQQ underlying sessions in the requested date range.")
    # Price-only returns are used; dividends are not fabricated or inferred from adjusted close.
    return raw[["date", "close"]]


def load_candidate_quote_history(options_path: Path, ids: set[str],
                                 start: pd.Timestamp, end: pd.Timestamp) -> dict[tuple[pd.Timestamp, str], dict[str, float]]:
    if not ids:
        return {}
    con = duckdb.connect()
    try:
        quotes = con.execute("""
            SELECT CAST(date AS DATE) AS date,
                   CAST(contract_id AS VARCHAR) AS contract_id,
                   CAST(bid AS DOUBLE) AS bid,
                   CAST(ask AS DOUBLE) AS ask,
                   CAST(mark AS DOUBLE) AS mark
            FROM read_parquet(?)
            WHERE CAST(contract_id AS VARCHAR) IN (SELECT UNNEST(?))
              AND CAST(date AS DATE) BETWEEN ? AND ?
        """, [str(options_path), sorted(ids), start.date(), end.date()]).df()
    finally:
        con.close()
    out: dict[tuple[pd.Timestamp, str], dict[str, float]] = {}
    if quotes.empty:
        return out
    quotes["date"] = pd.to_datetime(quotes["date"]).dt.normalize()
    quotes["contract_id"] = quotes["contract_id"].astype(str)
    for r in quotes.itertuples(index=False):
        bid = float(r.bid) if pd.notna(r.bid) else float("nan")
        ask = float(r.ask) if pd.notna(r.ask) else float("nan")
        mark = float(r.mark) if pd.notna(r.mark) else float("nan")
        mid = (bid + ask) / 2 if np.isfinite(bid) and np.isfinite(ask) else float("nan")
        out[(pd.Timestamp(r.date), str(r.contract_id))] = {"bid": bid, "ask": ask, "mid": mid, "mark": mark}
    return out


def quote_for(qmap, dt: pd.Timestamp, contract_id: str):
    q = qmap.get((pd.Timestamp(dt), str(contract_id)))
    return q if good_quote(q) else None


def vertical_quotes(qmap, dt, candidate, kind):
    if kind == "CALL_CREDIT":
        short = quote_for(qmap, dt, candidate["short_id"])
        wing = quote_for(qmap, dt, candidate["wing_id"])
        if short is None or wing is None or candidate["wing_strike"] <= candidate["short_strike"]:
            return None
        return {"short": short, "wing": wing}
    long = quote_for(qmap, dt, candidate["long_id"])
    short = quote_for(qmap, dt, candidate["short_id"])
    if long is None or short is None or candidate["long_strike"] <= candidate["short_strike"]:
        return None
    return {"long": long, "short": short}


def entry_cashflow(kind: str, q: dict[str, dict[str, float]], qty: int,
                   slip: float, commission: float) -> float:
    if kind == "PUT_DEBIT":
        long_fill, short_fill = q["long"]["ask"] + slip, q["short"]["bid"] - slip
        return -((long_fill - short_fill) * 100.0 * qty) - 2 * commission * qty
    short_fill, wing_fill = q["short"]["bid"] - slip, q["wing"]["ask"] + slip
    return ((short_fill - wing_fill) * 100.0 * qty) - 2 * commission * qty


def exit_cashflow(kind: str, q: dict[str, dict[str, float]], qty: int,
                  slip: float, commission: float) -> float:
    if kind == "PUT_DEBIT":
        long_fill, short_fill = q["long"]["bid"] - slip, q["short"]["ask"] + slip
        return ((long_fill - short_fill) * 100.0 * qty) - 2 * commission * qty
    wing_fill, short_fill = q["wing"]["bid"] - slip, q["short"]["ask"] + slip
    return ((wing_fill - short_fill) * 100.0 * qty) - 2 * commission * qty


def mark_value(kind: str, q: dict[str, dict[str, float]], qty: int) -> float:
    if kind == "PUT_DEBIT":
        return (q["long"]["mid"] - q["short"]["mid"]) * 100.0 * qty
    return (q["wing"]["mid"] - q["short"]["mid"]) * 100.0 * qty


def put_budget_for_holding_period(nav: float, entry_dte: int) -> float:
    # Annualized gross premium spend cap, prorated over expected exposure days.
    # The vertical is scheduled to close at DTE <= 7, so this avoids spending
    # 2% of NAV afresh on every roll and exhausting the cash reserve.
    planned_hold_days = max(1, int(entry_dte) - ROLL_DTE)
    return nav * PUT_ANNUAL_PREMIUM_BUDGET * planned_hold_days / 365.25


def size_put_debit(cash: float, q, slip: float, commission: float, budget: float) -> tuple[int, float]:
    debit_risk = ((q["long"]["ask"] + slip) - (q["short"]["bid"] - slip)) * 100.0 + 2 * commission
    if not np.isfinite(debit_risk) or debit_risk <= 0:
        return 0, debit_risk
    qty = min(math.floor(max(0.0, budget) / debit_risk),
              math.floor(max(0.0, cash) / debit_risk))
    return max(0, qty), debit_risk


def size_call_credit(nav: float, q, candidate: dict[str, Any],
                     slip: float, commission: float) -> tuple[int, float]:
    credit = q["short"]["bid"] - q["wing"]["ask"]
    width = float(candidate["width"])
    if credit <= 0 or width <= 0 or credit >= width:
        return 0, float("nan")
    # Strike-width loss plus a conservative four-leg round-trip friction allowance.
    unit_loss = (width - credit) * 100.0 + 4 * slip * 100.0 + 4 * commission
    if unit_loss <= 0:
        return 0, unit_loss
    return max(0, math.floor(nav * CALL_MAX_LOSS_BUDGET / unit_loss)), unit_loss


def run_one(underlying: pd.DataFrame, candidates, qmap, nav0: float,
            cost_name: str, variant: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cost = COSTS[cost_name]
    slip = float(cost["slippage_per_leg_per_share"])
    commission = float(cost["commission_per_contract_per_side"])
    first_spot = float(underlying.iloc[0]["close"])
    shares = math.floor(nav0 * CORE_WEIGHT / first_spot)
    cash = nav0 - shares * first_spot
    flows = {"PUT_DEBIT": 0.0, "CALL_CREDIT": 0.0}
    positions: dict[str, dict[str, Any] | None] = {"PUT_DEBIT": None, "CALL_CREDIT": None}
    active_sleeves = {
        "CORE_ONLY": set(),
        "CORE_PLUS_PUT_DEBIT": {"PUT_DEBIT"},
        "CORE_PLUS_CALL_CREDIT": {"CALL_CREDIT"},
        "CORE_PLUS_CALL_AND_PUT": {"PUT_DEBIT", "CALL_CREDIT"},
    }[variant]
    daily_rows: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    dates = [pd.Timestamp(x) for x in underlying["date"]]
    spot_by_date = {pd.Timestamp(r.date): float(r.close) for r in underlying.itertuples(index=False)}
    prior_nav: float | None = None
    blocked_exits = 0

    for i, dt in enumerate(dates):
        spot = spot_by_date[dt]
        for sleeve in ("CALL_CREDIT", "PUT_DEBIT"):
            pos = positions[sleeve]
            if pos is None or sleeve not in active_sleeves:
                continue
            if (pd.Timestamp(pos["expiry"]) - dt).days <= ROLL_DTE:
                q = vertical_quotes(qmap, dt, pos, sleeve)
                if q is None:
                    blocked_exits += 1
                    ledger.append({"date": str(dt.date()), "event": "EXIT_BLOCKED_MISSING_QUOTE",
                                   "variant": variant, "initial_nav_usd": nav0, "cost_case": cost_name,
                                   "sleeve": sleeve, "qty": pos["qty"], "expiry": str(pd.Timestamp(pos["expiry"]).date()),
                                   "reason": "Exact held-contract quote missing/invalid; position retained, no interpolation."})
                else:
                    cf = exit_cashflow(sleeve, q, int(pos["qty"]), slip, commission)
                    cash += cf
                    flows[sleeve] += cf
                    ledger.append({"date": str(dt.date()), "event": "EXIT", "variant": variant,
                                   "initial_nav_usd": nav0, "cost_case": cost_name, "sleeve": sleeve,
                                   "qty": pos["qty"], "expiry": str(pd.Timestamp(pos["expiry"]).date()),
                                   "reason": "DTE_LE_7", "cashflow_usd": cf, "entry_date": pos["entry_date"],
                                   "short_id": pos["short_id"], "other_leg_id": pos.get("wing_id", pos.get("long_id"))})
                    positions[sleeve] = None

        if i > 0 and prior_nav is not None and np.isfinite(prior_nav) and prior_nav > 0:
            signal_dt = dates[i - 1]
            for sleeve in ("CALL_CREDIT", "PUT_DEBIT"):
                if sleeve not in active_sleeves or positions[sleeve] is not None:
                    continue
                kind = sleeve
                cand = candidates.get((signal_dt, kind))
                if cand is None:
                    continue
                expiry = pd.Timestamp(cand["expiry"])
                exec_dte = (expiry - dt).days
                if exec_dte < DTE_MIN or exec_dte > DTE_MAX:
                    ledger.append({"date": str(dt.date()), "event": "ENTRY_BLOCKED_DTE",
                                   "variant": variant, "initial_nav_usd": nav0, "cost_case": cost_name,
                                   "sleeve": sleeve, "expiry": str(expiry.date()),
                                   "reason": f"Preselected exact contract execution DTE {exec_dte} is outside 18..35."})
                    continue
                q = vertical_quotes(qmap, dt, cand, kind)
                if q is None:
                    ledger.append({"date": str(dt.date()), "event": "ENTRY_BLOCKED_MISSING_QUOTE",
                                   "variant": variant, "initial_nav_usd": nav0, "cost_case": cost_name,
                                   "sleeve": sleeve, "expiry": str(expiry.date()),
                                   "reason": "Exact preselected contract quotes missing/invalid; no replacement."})
                    continue

                if sleeve == "PUT_DEBIT":
                    budget = put_budget_for_holding_period(prior_nav, exec_dte)
                    qty, unit_risk = size_put_debit(cash, q, slip, commission, budget)
                else:
                    qty, unit_risk = size_call_credit(prior_nav, q, cand, slip, commission)
                    budget = prior_nav * CALL_MAX_LOSS_BUDGET
                if qty <= 0:
                    ledger.append({"date": str(dt.date()), "event": "ENTRY_BLOCKED_SIZE_OR_CREDIT",
                                   "variant": variant, "initial_nav_usd": nav0, "cost_case": cost_name,
                                   "sleeve": sleeve, "expiry": str(expiry.date()), "unit_risk_usd": unit_risk,
                                   "budget_usd": budget, "reason": "No whole spread fits the defined risk budget."})
                    continue
                cf = entry_cashflow(sleeve, q, qty, slip, commission)
                if (sleeve == "PUT_DEBIT" and (cf >= 0 or cash + cf < -0.01)) or (sleeve == "CALL_CREDIT" and cf <= 0):
                    ledger.append({"date": str(dt.date()), "event": "ENTRY_BLOCKED_NET_CASHFLOW",
                                   "variant": variant, "initial_nav_usd": nav0, "cost_case": cost_name,
                                   "sleeve": sleeve, "expiry": str(expiry.date()),
                                   "reason": "Net entry cashflow is invalid after modeled friction."})
                    continue
                cash += cf
                flows[sleeve] += cf
                pos = dict(cand)
                pos.update({"qty": int(qty), "entry_date": str(dt.date()), "entry_cashflow_usd": float(cf),
                            "entry_nav_usd": float(prior_nav), "entry_dte": int(exec_dte),
                            "entry_unit_risk_usd": float(unit_risk), "cost_case": cost_name})
                positions[sleeve] = pos
                ledger.append({"date": str(dt.date()), "event": "ENTRY", "variant": variant,
                               "initial_nav_usd": nav0, "cost_case": cost_name, "sleeve": sleeve,
                               "qty": int(qty), "expiry": str(expiry.date()), "entry_dte": int(exec_dte),
                               "entry_cashflow_usd": cf, "unit_risk_usd": unit_risk, "budget_usd": budget,
                               "entry_nav_usd": float(prior_nav), "short_id": cand["short_id"],
                               "other_leg_id": cand.get("wing_id", cand.get("long_id")),
                               "short_strike": cand["short_strike"],
                               "other_leg_strike": cand.get("wing_strike", cand.get("long_strike")),
                               "selection_date": str(pd.Timestamp(cand["selection_date"]).date()),
                               "selection_delta_short": cand["selection_delta_short"],
                               "selection_delta_other": cand.get("selection_delta_wing", cand.get("selection_delta_long"))})

        marks: dict[str, float | None] = {"PUT_DEBIT": 0.0, "CALL_CREDIT": 0.0}
        mark_complete = True
        for sleeve in ("PUT_DEBIT", "CALL_CREDIT"):
            pos = positions[sleeve]
            if pos is None:
                marks[sleeve] = 0.0
            else:
                q = vertical_quotes(qmap, dt, pos, sleeve)
                if q is None:
                    marks[sleeve] = None
                    mark_complete = False
                else:
                    marks[sleeve] = mark_value(sleeve, q, int(pos["qty"]))

        core_mv = shares * spot
        core_pnl = shares * (spot - first_spot)
        put_pnl = flows["PUT_DEBIT"] + marks["PUT_DEBIT"] if marks["PUT_DEBIT"] is not None else None
        call_pnl = flows["CALL_CREDIT"] + marks["CALL_CREDIT"] if marks["CALL_CREDIT"] is not None else None
        nav = cash + core_mv + marks["PUT_DEBIT"] + marks["CALL_CREDIT"] if mark_complete else None
        reconciliation = nav - (nav0 + core_pnl + put_pnl + call_pnl) if mark_complete else None
        daily_rows.append({
            "date": str(dt.date()), "variant": variant, "initial_nav_usd": nav0, "cost_case": cost_name,
            "qqq_close": spot, "qqq_core_shares": shares, "cash_usd": cash, "core_market_value_usd": core_mv,
            "core_pnl_usd": core_pnl, "put_debit_mark_value_usd": marks["PUT_DEBIT"],
            "call_credit_mark_value_usd": marks["CALL_CREDIT"], "put_debit_pnl_usd": put_pnl,
            "call_credit_pnl_usd": call_pnl, "nav_usd": nav, "mark_complete": mark_complete,
            "reconciliation_error_usd": reconciliation,
            "put_position_qty": int(positions["PUT_DEBIT"]["qty"]) if positions["PUT_DEBIT"] else 0,
            "call_position_qty": int(positions["CALL_CREDIT"]["qty"]) if positions["CALL_CREDIT"] else 0,
        })
        prior_nav = float(nav) if mark_complete and nav is not None else None

    ddf = pd.DataFrame(daily_rows)
    nav_series = pd.to_numeric(ddf["nav_usd"], errors="coerce")
    complete = nav_series.notna()
    if complete.any():
        observed_nav = nav_series[complete]
        maxdd = float((observed_nav / observed_nav.cummax() - 1.0).min())
    else:
        maxdd = float("nan")

    daily_returns = [float("nan")] * len(ddf)
    for j in range(1, len(ddf)):
        if complete.iloc[j] and complete.iloc[j - 1]:
            prev, curr = float(nav_series.iloc[j - 1]), float(nav_series.iloc[j])
            if prev > 0:
                daily_returns[j] = curr / prev - 1
    ddf["observed_daily_return"] = daily_returns
    finite_daily = [x for x in daily_returns if np.isfinite(x)]
    worst_day = min(finite_daily) if finite_daily else float("nan")

    observed = ddf[complete].copy()
    annual = []
    if not observed.empty:
        observed["date_dt"] = pd.to_datetime(observed["date"])
        observed["year"] = observed["date_dt"].dt.year
        yearly_last = observed.groupby("year", sort=True).tail(1).set_index("year")["nav_usd"]
        for year, year_end_nav in yearly_last.items():
            prior_marks = observed[observed["date_dt"] < pd.Timestamp(int(year), 1, 1)]
            year_start_nav = float(prior_marks.iloc[-1]["nav_usd"]) if not prior_marks.empty else nav0
            if year_start_nav > 0:
                annual.append((int(year), float(year_end_nav) / year_start_nav - 1.0))
    worst_year = min((v for _, v in annual), default=float("nan"))
    first_date = pd.Timestamp(ddf.iloc[0]["date"])
    final_date = pd.Timestamp(ddf.iloc[-1]["date"])
    final_nav = float(nav_series.iloc[-1]) if complete.iloc[-1] else float("nan")
    years = max((final_date - first_date).days / 365.25, 1 / 365.25)
    cagr = (final_nav / nav0) ** (1 / years) - 1 if np.isfinite(final_nav) and final_nav > 0 else float("nan")
    recon = pd.to_numeric(ddf["reconciliation_error_usd"], errors="coerce").dropna()
    ledger_df = pd.DataFrame(ledger)
    summary = {
        "variant": variant, "cost_case": cost_name, "initial_nav_usd": nav0,
        "date_start": str(first_date.date()), "date_end": str(final_date.date()),
        "qqq_core_weight_normalization": CORE_WEIGHT,
        "put_annual_premium_budget_pct_nav": 100 * PUT_ANNUAL_PREMIUM_BUDGET if "PUT_DEBIT" in active_sleeves else 0,
        "call_max_loss_budget_pct_prior_nav": 100 * CALL_MAX_LOSS_BUDGET if "CALL_CREDIT" in active_sleeves else 0,
        "slippage_per_leg_per_share": slip, "commission_per_contract_per_side": commission,
        "final_nav_usd": final_nav, "total_return_pct": (final_nav / nav0 - 1) * 100 if np.isfinite(final_nav) else float("nan"),
        "cagr_pct": cagr * 100 if np.isfinite(cagr) else float("nan"),
        "maxdd_observed_marks_pct": maxdd * 100 if np.isfinite(maxdd) else float("nan"),
        "worst_observed_calendar_year_pct": worst_year * 100 if np.isfinite(worst_year) else float("nan"),
        "worst_observed_daily_return_pct": worst_day * 100 if np.isfinite(worst_day) else float("nan"),
        "qqq_core_pnl_at_end_usd": float(observed.iloc[-1]["core_pnl_usd"]) if not observed.empty else float("nan"),
        "put_debit_pnl_at_last_complete_mark_usd": float(observed.iloc[-1]["put_debit_pnl_usd"]) if not observed.empty and pd.notna(observed.iloc[-1]["put_debit_pnl_usd"]) else float("nan"),
        "call_credit_pnl_at_last_complete_mark_usd": float(observed.iloc[-1]["call_credit_pnl_usd"]) if not observed.empty and pd.notna(observed.iloc[-1]["call_credit_pnl_usd"]) else float("nan"),
        "complete_nav_marks": int(complete.sum()), "total_underlying_sessions": int(len(ddf)),
        "missing_or_incomplete_nav_marks": int((~complete).sum()),
        "max_abs_nav_reconciliation_error_usd": float(recon.abs().max()) if not recon.empty else float("nan"),
        "entries": int((ledger_df["event"] == "ENTRY").sum()) if not ledger_df.empty else 0,
        "exits": int((ledger_df["event"] == "EXIT").sum()) if not ledger_df.empty else 0,
        "blocked_entries": int(ledger_df["event"].astype(str).str.startswith("ENTRY_BLOCKED").sum()) if not ledger_df.empty else 0,
        "blocked_exits": int((ledger_df["event"] == "EXIT_BLOCKED_MISSING_QUOTE").sum()) if not ledger_df.empty else 0,
        "open_put_debit_qty_at_end": int(positions["PUT_DEBIT"]["qty"]) if positions["PUT_DEBIT"] else 0,
        "open_call_credit_qty_at_end": int(positions["CALL_CREDIT"]["qty"]) if positions["CALL_CREDIT"] else 0,
        "metric_quality": "OBSERVED_QUOTES_ONLY; missing held-leg marks can understate drawdown",
        "annual_returns_observed": json.dumps({str(y): round(v * 100, 6) for y, v in annual}, sort_keys=True),
    }
    if np.isfinite(summary["max_abs_nav_reconciliation_error_usd"]) and summary["max_abs_nav_reconciliation_error_usd"] >= 0.01:
        raise AssertionError(f"NAV attribution reconciliation failed: {summary['max_abs_nav_reconciliation_error_usd']}")
    return summary, daily_rows, ledger


def generate_report(summary_df: pd.DataFrame, manifest: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# QQQ + Options Combination Screen V1", "",
        "**Status: research-only; no live sizing changes and no broker orders.**", "",
        "## Prespecified candidates", "",
        "- CORE_ONLY: buy-and-hold QQQ shares sized to 42% of initial NAV; the remaining cash stays uninvested.",
        "- CORE_PLUS_PUT_DEBIT: the same core plus a 18–35 DTE QQQ put debit vertical (buy approximately 25-delta put, sell lower-strike approximately 10-delta put). Annualized gross premium budget: 2% of NAV, prorated by planned exposure days (entry DTE minus the 7-day roll threshold).",
        "- CORE_PLUS_CALL_CREDIT: the same core plus a 18–35 DTE QQQ call credit vertical (sell approximately 16-delta call, buy higher-strike approximately 8-delta protective call). Budget: 0.8% of prior observed NAV in conservative vertical max loss.",
        "- CORE_PLUS_CALL_AND_PUT: both option sleeves at their single-sleeve budgets. This has a larger combined nominal budget, so raw CAGR is not a matched-total-risk comparison.",
        "",
        "Candidates are selected from the prior observed session and entered next session using the exact same contract IDs. Invalid/missing quotes are not replaced or interpolated. Existing positions are closed using exact held-contract side quotes when DTE reaches 7 calendar days or less.",
        "",
        "## Source and execution",
        "",
        f"- Underlying/option date range: {manifest['date_start']} to {manifest['date_end']}.",
        f"- SHA-256 options: {manifest['options_sha256']}; underlying: {manifest['underlying_sha256']}.",
        "- BASE: $0.05/leg/share slippage per side + $0.65 per contract/leg/side commission. STRESS doubles slippage to $0.10; commission is unchanged.",
        "- Entry/exit use historical bid/ask plus modeled slippage; daily marks use exact-contract bid/ask midpoints. These are quote-side simulations, not authenticated broker fills or displayed-depth replay.",
        "- QQQ core returns are close-to-close price-only; dividends are not fabricated/inferred. Core shares are not rebalanced.",
        "- P&L is attributed to QQQ core, put debit spread, and call credit spread. NAV reconciliation must be within one cent on complete marks.",
        "",
        "## Results", "",
        summary_df[["variant", "cost_case", "initial_nav_usd", "final_nav_usd", "cagr_pct", "maxdd_observed_marks_pct", "worst_observed_calendar_year_pct", "worst_observed_daily_return_pct", "entries", "exits", "missing_or_incomplete_nav_marks"]].to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Interpretation limits", "",
        "- MaxDD and annual results are observed-mark metrics. Missing held-leg marks stay unknown, so the observed MaxDD may understate losses; no forward fill is used.",
        "- The combined portfolio adds the two sleeve budgets. It should not be declared superior based on raw CAGR alone.",
        "- No VXX stock short, no VXX option leg and no QQQ 1:5 ratio is included in these candidate portfolios.",
        "- The source option history ends on its last observed chain date; there is no QQQ option-chain evidence past that date.",
        "- The four candidates are a prespecified screen, not independent trials or a claim that any candidate is deployable.", ""
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out", default="research/qqq_option_combination_screen_v1/results")
    parser.add_argument("--start-date", default="2011-03-23")
    parser.add_argument("--end-date", default="2025-12-15")
    parser.add_argument("--navs", nargs="+", type=float, default=[80000.0, 1000000.0])
    args = parser.parse_args()
    data_dir, out_dir = Path(args.data_dir), Path(args.out)
    options_path = data_dir / "QQQ_options.parquet"
    underlying_path = data_dir / "QQQ_underlying.parquet"
    if not options_path.is_file() or not underlying_path.is_file():
        raise FileNotFoundError("Expected canonical QQQ_options.parquet and QQQ_underlying.parquet under --data-dir.")
    options_sha, underlying_sha = sha256_file(options_path), sha256_file(underlying_path)
    if options_sha != OPTIONS_SHA256 or underlying_sha != UNDERLYING_SHA256:
        raise ValueError("Canonical data SHA-256 mismatch; refusing to run on unpinned or changed source data.")

    underlying = load_underlying(underlying_path, args.start_date, args.end_date)
    spots = {pd.Timestamp(r.date): float(r.close) for r in underlying.itertuples(index=False)}
    candidates, ids, candidate_rejections = build_candidates(options_path, underlying["date"], spots)
    qmap = load_candidate_quote_history(options_path, ids, pd.Timestamp(underlying.iloc[0]["date"]), pd.Timestamp(underlying.iloc[-1]["date"]))
    if not qmap:
        raise RuntimeError("No exact-contract quote history loaded for selected candidate legs.")

    summaries: list[dict[str, Any]] = []
    all_daily: list[dict[str, Any]] = []
    all_ledger: list[dict[str, Any]] = []
    for nav0 in args.navs:
        if not np.isfinite(nav0) or nav0 <= 0:
            raise ValueError("Each --navs value must be positive and finite.")
        for cost_case in ("BASE", "STRESS"):
            for variant in VARIANTS:
                summary, daily, ledger = run_one(underlying, candidates, qmap, float(nav0), cost_case, variant)
                summaries.append(summary)
                all_daily.extend(daily)
                all_ledger.extend(ledger)

    summary_df = pd.DataFrame(summaries)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "summary.csv", index=False)
    pd.DataFrame(all_daily).to_csv(out_dir / "daily_nav.csv", index=False)
    pd.DataFrame(all_ledger).to_csv(out_dir / "trade_ledger.csv", index=False)
    manifest = {
        "study": "QQQ_OPTION_COMBINATION_SCREEN_V1",
        "date_start": str(pd.Timestamp(underlying.iloc[0]["date"]).date()),
        "date_end": str(pd.Timestamp(underlying.iloc[-1]["date"]).date()),
        "options_sha256": options_sha, "underlying_sha256": underlying_sha,
        "selected_contract_ids": len(ids), "candidate_structures_by_selection_date": len(candidates),
        "loaded_exact_contract_quote_rows": len(qmap), "candidate_selection_rejections": candidate_rejections,
        "underlying_sessions": int(len(underlying)), "variants": list(VARIANTS),
        "navs_usd": args.navs, "cost_cases": COSTS,
        "put_annual_premium_budget_pct_nav": 100 * PUT_ANNUAL_PREMIUM_BUDGET,
        "source_type": "historical quote-side simulation; executable fills/depth not authenticated",
        "same_close_lookahead": False, "quote_interpolation": False, "black_scholes": False,
        "dividends_included": False, "vxx_stock_short_included": False, "vxx_options_included": False,
        "parameter_optimization": False, "deployment_status": "BLOCKED_RESEARCH_ONLY",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    generate_report(summary_df, manifest, out_dir / "REPORT.md")
    print(json.dumps({"manifest": manifest, "summary": summary_df.to_dict(orient="records")}, indent=2, default=str))


if __name__ == "__main__":
    main()
