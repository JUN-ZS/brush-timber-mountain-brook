#!/usr/bin/env python3
"""Paired historical EOD quote replay: QQQ long puts vs SPY short puts.

The output is an aggregate research report, not an execution simulator or a
claim of actual fills. Contract selection uses signal-day quotes; entries are
marked at the next common session close to avoid same-close look-ahead.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HORIZONS = (1, 3, 5, 10, 20)
MODES = ("DELTA_MATCHED", "OTM_MATCHED", "PREMIUM_MATCHED")
COSTS = (
    {"id": "TOUCH_NO_COMMISSION", "label": "Bid/ask touch; $0 commission", "commission": 0.0, "slippage": 0.0},
    {"id": "STANDARD", "label": "Standard: $0.65/contract/side", "commission": 0.65, "slippage": 0.0},
    {"id": "STRESS", "label": "Stress: $1.30/contract/side + $0.05/share/side", "commission": 1.30, "slippage": 0.05},
)
SOURCE_HASHES = {
    "SPY_options.parquet": "a7152991b45b81f090f970e945bf88def8093b8ecb9b250e9891cb6d88041f0a",
    "SPY_underlying.parquet": "847e60a441eb10969d87cd4a6da604257b782d9076168f68d5730b84096c79db",
    "QQQ_options.parquet": "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
    "QQQ_underlying.parquet": "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351",
}
SOURCE_RELEASE = "https://github.com/lambdaclass/options_portfolio_backtester/releases/tag/data-v1"
MULTIPLIER = 100
REGIMES = ("BOTH_DOWN_QQQ_WEAKER", "BOTH_DOWN_SPY_WEAKER", "BOTH_UP", "MIXED")


def _norm_name(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def _find_column(columns: list[str], choices: tuple[str, ...], required: bool = True) -> str | None:
    by_norm = {_norm_name(str(c)): str(c) for c in columns}
    for choice in choices:
        found = by_norm.get(_norm_name(choice))
        if found is not None:
            return found
    if required:
        raise ValueError("Missing required source column; expected one of: " + ", ".join(choices))
    return None


def _parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()


def load_underlying(path: Path, start: pd.Timestamp, end: pd.Timestamp) -> dict[pd.Timestamp, float]:
    names = pq.ParquetFile(path).schema.names
    date_col = _find_column(names, ("date", "datetime", "quotedate"))
    close_col = _find_column(names, ("close", "rawclose", "adjclose", "adjustedclose"))
    raw = pd.read_parquet(path, columns=[date_col, close_col])
    out = pd.DataFrame({
        "date": _parse_date(raw[date_col]),
        "close": pd.to_numeric(raw[close_col], errors="coerce"),
    }).dropna()
    out = out[(out["date"] >= start) & (out["date"] <= end)]
    out = out.sort_values("date").drop_duplicates("date", keep="last")
    if out.empty:
        raise ValueError("No underlying prices inside the requested date range: " + str(path))
    return {pd.Timestamp(r.date): float(r.close) for r in out.itertuples(index=False)}


def load_put_quotes(
    path: Path, start: pd.Timestamp, end: pd.Timestamp, max_dte: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    names = pq.ParquetFile(path).schema.names
    date_col = _find_column(names, ("quotedate", "quote_date", "date", "asof"))
    exp_col = _find_column(names, ("expiration", "expiry", "expirydate", "expirationdate"))
    type_col = _find_column(names, ("type", "right", "optiontype", "putcall", "cpflag"))
    strike_col = _find_column(names, ("strike", "strikeprice"))
    bid_col = _find_column(names, ("bid", "bidprice"))
    ask_col = _find_column(names, ("ask", "askprice"))
    delta_col = _find_column(names, ("delta", "optiondelta"))
    keep = list(dict.fromkeys([date_col, exp_col, type_col, strike_col, bid_col, ask_col, delta_col]))
    raw = pd.read_parquet(path, columns=keep)
    out = pd.DataFrame({
        "quote_date": _parse_date(raw[date_col]),
        "expiration": _parse_date(raw[exp_col]),
        "option_type": raw[type_col].astype(str).str.strip().str.upper(),
        "strike": pd.to_numeric(raw[strike_col], errors="coerce"),
        "bid": pd.to_numeric(raw[bid_col], errors="coerce"),
        "ask": pd.to_numeric(raw[ask_col], errors="coerce"),
        "delta": pd.to_numeric(raw[delta_col], errors="coerce"),
    })
    out["dte"] = (out["expiration"] - out["quote_date"]).dt.days
    out["strike_key"] = (out["strike"] * 1000).round().astype("Int64")
    is_put = out["option_type"].isin(("P", "PUT", "PUTS"))
    good_dates = out["quote_date"].notna() & out["expiration"].notna()
    good_prices = out["bid"].notna() & out["ask"].notna() & (out["bid"] >= 0) & (out["ask"] > 0) & (out["ask"] >= out["bid"])
    in_range = (out["quote_date"] >= start) & (out["quote_date"] <= end) & (out["dte"] >= 0) & (out["dte"] <= max_dte)
    out = out[is_put & good_dates & good_prices & in_range & out["strike_key"].notna()].copy()
    out["strike_key"] = out["strike_key"].astype("int64")
    out = out.drop_duplicates()
    duplicate_mask = out.duplicated(["quote_date", "expiration", "strike_key"], keep=False)
    ambiguous_keys = int(out.loc[duplicate_mask, ["quote_date", "expiration", "strike_key"]].drop_duplicates().shape[0])
    out = out.loc[~duplicate_mask].copy()
    if out.empty:
        raise ValueError("No valid put quotes inside the requested DTE/date range: " + str(path))
    out = out.set_index(["quote_date", "expiration", "strike_key"], drop=False).sort_index()
    meta = {
        "path_name": path.name,
        "rows_after_put_date_dte_quote_filters": int(len(out)),
        "ambiguous_contract_date_keys_excluded": ambiguous_keys,
        "source_columns": names,
    }
    return out, meta


def _day(frame: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame | None:
    try:
        value = frame.loc[date]
    except KeyError:
        return None
    if isinstance(value, pd.Series):
        return value.to_frame().T
    return value


def _quote_at(frame: pd.DataFrame, date: pd.Timestamp, expiration: pd.Timestamp, strike_key: int) -> pd.Series | None:
    try:
        row = frame.loc[(date, expiration, strike_key)]
    except KeyError:
        return None
    if isinstance(row, pd.DataFrame):
        return None
    bid, ask = float(row["bid"]), float(row["ask"])
    if not (math.isfinite(bid) and math.isfinite(ask) and bid >= 0 and ask > 0 and ask >= bid):
        return None
    return row


def _entry_candidates(day: pd.DataFrame | None, target_dte: int, tolerance: int) -> pd.DataFrame:
    if day is None or day.empty:
        return pd.DataFrame()
    low, high = max(1, target_dte - tolerance), target_dte + tolerance
    g = day[(day["dte"] >= low) & (day["dte"] <= high)].copy()
    g = g[(g["bid"] > 0) & (g["ask"] > 0) & (g["ask"] >= g["bid"])]
    return g


def _select(
    candidates: pd.DataFrame,
    spot: float,
    mode: str,
    target_dte: int,
    target_abs_delta: float,
    target_otm: float,
    premium_reference: float | None = None,
) -> pd.Series | None:
    if candidates.empty or not math.isfinite(spot) or spot <= 0:
        return None
    g = candidates[candidates["strike"] < spot].copy()
    if g.empty:
        return None
    g["otm_pct"] = (spot - g["strike"]) / spot
    g["dte_distance"] = (g["dte"] - target_dte).abs()
    if mode == "DELTA_MATCHED":
        g = g[g["delta"].notna()].copy()
        if g.empty:
            return None
        g["score"] = (g["delta"].abs() - target_abs_delta).abs() + 0.002 * g["dte_distance"]
    elif mode == "OTM_MATCHED":
        g["score"] = (g["otm_pct"] - target_otm).abs() + 0.0002 * g["dte_distance"]
    elif mode == "PREMIUM_MATCHED":
        if premium_reference is None:
            return None
        g["score"] = (g["bid"] - premium_reference).abs() + 0.0001 * g["dte_distance"]
    else:
        raise ValueError("Unsupported matching mode: " + mode)
    g = g.sort_values(["score", "dte_distance", "strike"], kind="stable")
    return g.iloc[0]


def _contract_ref(row: pd.Series) -> dict[str, Any]:
    return {
        "expiration": pd.Timestamp(row["expiration"]),
        "strike": float(row["strike"]),
        "strike_key": int(row["strike_key"]),
        "dte_signal": int(row["dte"]),
        "delta_signal": float(row["delta"]) if pd.notna(row["delta"]) else None,
        "otm_signal": float(row["otm_pct"]),
        "bid_signal": float(row["bid"]),
        "ask_signal": float(row["ask"]),
    }


def _mode_contracts(
    qqq_candidates: pd.DataFrame,
    spy_candidates: pd.DataFrame,
    qqq_spot: float,
    spy_spot: float,
    target_dte: int,
    target_abs_delta: float,
    target_otm: float,
) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    selected: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    qqq_delta = _select(qqq_candidates, qqq_spot, "DELTA_MATCHED", target_dte, target_abs_delta, target_otm)
    spy_delta = _select(spy_candidates, spy_spot, "DELTA_MATCHED", target_dte, target_abs_delta, target_otm)
    qqq_otm = _select(qqq_candidates, qqq_spot, "OTM_MATCHED", target_dte, target_abs_delta, target_otm)
    spy_otm = _select(spy_candidates, spy_spot, "OTM_MATCHED", target_dte, target_abs_delta, target_otm)
    if qqq_delta is not None and spy_delta is not None:
        selected["DELTA_MATCHED"] = (_contract_ref(qqq_delta), _contract_ref(spy_delta))
    if qqq_otm is not None and spy_otm is not None:
        selected["OTM_MATCHED"] = (_contract_ref(qqq_otm), _contract_ref(spy_otm))
    if qqq_delta is not None:
        spy_premium = _select(
            spy_candidates, spy_spot, "PREMIUM_MATCHED", target_dte, target_abs_delta, target_otm,
            premium_reference=float(qqq_delta["ask"]),
        )
        if spy_premium is not None:
            selected["PREMIUM_MATCHED"] = (_contract_ref(qqq_delta), _contract_ref(spy_premium))
    return selected


def leg_pnl_per_contract(long_entry_ask: float, long_exit_bid: float, short_entry_bid: float, short_exit_ask: float) -> tuple[float, float]:
    """Gross realized quote-touch P&L per one contract, before fees/slippage."""
    return (
        (float(long_exit_bid) - float(long_entry_ask)) * MULTIPLIER,
        (float(short_entry_bid) - float(short_exit_ask)) * MULTIPLIER,
    )


def package_pnl(
    long_gross: float, short_gross: float, long_qty: int, short_qty: int,
    commission_per_side: float = 0.65, slippage_per_share_per_side: float = 0.0,
) -> float:
    per_contract_cost = 2 * commission_per_side + 2 * slippage_per_share_per_side * MULTIPLIER
    return long_qty * long_gross + short_qty * short_gross - (long_qty + short_qty) * per_contract_cost


def _quantile(values: np.ndarray, q: float) -> float | None:
    return float(np.quantile(values, q)) if len(values) else None


def _basic_stats(pnl: np.ndarray) -> dict[str, Any]:
    if len(pnl) == 0:
        return {
            "n": 0, "wins": 0, "losses": 0, "breakeven": 0, "win_rate_pct": None,
            "mean_pnl": None, "median_pnl": None, "p05_pnl": None, "p01_pnl": None,
            "es05_pnl": None, "worst_pnl": None, "best_pnl": None, "total_pnl": None,
            "profit_factor": None, "avg_win": None, "avg_loss": None,
        }
    positive = pnl[pnl > 1e-9]
    negative = pnl[pnl < -1e-9]
    flat = len(pnl) - len(positive) - len(negative)
    gross_gain = float(positive.sum())
    gross_loss = float(-negative.sum())
    es_cut = _quantile(pnl, 0.05)
    tail = pnl[pnl <= es_cut] if es_cut is not None else np.array([], dtype=float)
    return {
        "n": int(len(pnl)),
        "wins": int(len(positive)),
        "losses": int(len(negative)),
        "breakeven": int(flat),
        "win_rate_pct": 100.0 * len(positive) / len(pnl),
        "mean_pnl": float(np.mean(pnl)),
        "median_pnl": float(np.median(pnl)),
        "p05_pnl": _quantile(pnl, 0.05),
        "p01_pnl": _quantile(pnl, 0.01),
        "es05_pnl": float(np.mean(tail)) if len(tail) else None,
        "worst_pnl": float(np.min(pnl)),
        "best_pnl": float(np.max(pnl)),
        "total_pnl": float(np.sum(pnl)),
        "profit_factor": (gross_gain / gross_loss) if gross_loss > 0 else (99.9 if gross_gain > 0 else 0.0),
        "avg_win": float(np.mean(positive)) if len(positive) else None,
        "avg_loss": float(np.mean(negative)) if len(negative) else None,
    }


def _regime_for(qret: float, sret: float) -> str:
    if qret < 0 and sret < 0:
        return "BOTH_DOWN_QQQ_WEAKER" if qret < sret else "BOTH_DOWN_SPY_WEAKER"
    if qret >= 0 and sret >= 0:
        return "BOTH_UP"
    return "MIXED"


def build_summaries(samples: list[dict[str, Any]], max_qty: int) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for mode in MODES:
        for horizon in HORIZONS:
            rows = [r for r in samples if r["mode"] == mode and r["horizon"] == horizon]
            if not rows:
                rows = []
            long_gross = np.asarray([r["long_gross_pnl"] for r in rows], dtype=float)
            short_gross = np.asarray([r["short_gross_pnl"] for r in rows], dtype=float)
            qret = np.asarray([r["qqq_spot_return"] for r in rows], dtype=float)
            sret = np.asarray([r["spy_spot_return"] for r in rows], dtype=float)
            regimes = np.asarray([r["regime"] for r in rows], dtype=object)
            qstrike = np.asarray([r["qqq_strike"] for r in rows], dtype=float)
            qentry = np.asarray([r["qqq_entry_ask"] for r in rows], dtype=float)
            sstrike = np.asarray([r["spy_strike"] for r in rows], dtype=float)
            sentry = np.asarray([r["spy_entry_bid"] for r in rows], dtype=float)
            cashflow_unit = np.asarray([r["spy_entry_bid"] * MULTIPLIER - r["qqq_entry_ask"] * MULTIPLIER for r in rows], dtype=float)
            premium_mismatch = np.asarray([r["actual_entry_premium_mismatch"] for r in rows], dtype=float)
            delta_diff = np.asarray([r["delta_abs_diff"] for r in rows if r["delta_abs_diff"] is not None], dtype=float)
            dte_diff = np.asarray([r["dte_abs_diff"] for r in rows], dtype=float)
            otm_diff = np.asarray([r["otm_abs_diff"] for r in rows], dtype=float)
            for cost in COSTS:
                per_contract_cost = 2 * cost["commission"] + 2 * cost["slippage"] * MULTIPLIER
                for long_qty in range(1, max_qty + 1):
                    for short_qty in range(1, max_qty + 1):
                        pnl = long_qty * long_gross + short_qty * short_gross - (long_qty + short_qty) * per_contract_cost
                        stats = _basic_stats(pnl)
                        offset_rates = []
                        step = max(1, horizon)
                        entry_index = np.asarray([int(r["entry_index"]) for r in rows], dtype=int)
                        for offset in range(step):
                            cohort = pnl[(entry_index % step) == offset]
                            if len(cohort):
                                offset_rates.append(float(np.mean(cohort > 1e-9) * 100))
                        regime_rows = {}
                        for regime in REGIMES:
                            mask = regimes == regime
                            reg = _basic_stats(pnl[mask])
                            regime_rows[regime] = {
                                "n": reg.get("n", 0),
                                "wins": reg.get("wins", 0),
                                "win_rate_pct": reg.get("win_rate_pct"),
                                "mean_pnl": reg.get("mean_pnl"),
                            }
                        zero_pnl = (
                            long_qty * (qstrike - qentry) * MULTIPLIER
                            + short_qty * (sentry - sstrike) * MULTIPLIER
                            - (long_qty + short_qty) * per_contract_cost
                        )
                        row = {
                            "mode": mode, "horizon": horizon, "cost_id": cost["id"],
                            "cost_label": cost["label"], "commission_per_side": cost["commission"],
                            "slippage_per_share_per_side": cost["slippage"],
                            "long_qty": long_qty, "short_qty": short_qty,
                            **stats,
                            "offset_win_rate_min_pct": min(offset_rates) if offset_rates else None,
                            "offset_win_rate_median_pct": float(np.median(offset_rates)) if offset_rates else None,
                            "offset_win_rate_max_pct": max(offset_rates) if offset_rates else None,
                            "median_entry_net_cashflow_4_to_5_usd": float(np.median(5 * sentry * MULTIPLIER - 4 * qentry * MULTIPLIER)) if len(rows) else None,
                            "median_entry_net_cashflow_selected_ratio_usd": float(np.median(short_qty * sentry * MULTIPLIER - long_qty * qentry * MULTIPLIER)) if len(rows) else None,
                            "median_per_contract_premium_mismatch_usd": float(np.median(premium_mismatch) * MULTIPLIER) if len(rows) else None,
                            "median_abs_delta_difference": float(np.median(delta_diff)) if len(delta_diff) else None,
                            "median_abs_dte_difference_days": float(np.median(dte_diff)) if len(dte_diff) else None,
                            "median_abs_otm_difference_pct_points": float(np.median(otm_diff) * 100) if len(otm_diff) else None,
                            "simultaneous_zero_underlying_stress_worst_usd": float(np.min(zero_pnl)) if len(zero_pnl) else None,
                            "simultaneous_zero_underlying_stress_median_usd": float(np.median(zero_pnl)) if len(zero_pnl) else None,
                            "regimes": regime_rows,
                        }
                        summaries.append(row)
    return summaries


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")


def make_html(report: dict[str, Any]) -> str:
    payload = _safe_json(report)
    return r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>QQQ LONG PUT × SPY SHORT PUT — Historical Win-Rate Report</title>
<style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,Arial,sans-serif;background:#0b1120;color:#e5e7eb}
body{margin:0;padding:24px;max-width:1180px;margin-inline:auto}h1{font-size:clamp(24px,4vw,36px);margin:0 0 8px}
.sub{color:#9ca3af;line-height:1.5;margin-bottom:22px}.panel{background:#121c2f;border:1px solid #26344b;border-radius:14px;padding:18px;margin:14px 0}
.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}.control{display:flex;flex-direction:column;gap:8px;color:#cbd5e1}
select,input[type=range]{width:100%}select{background:#0b1120;color:#f8fafc;border:1px solid #475569;border-radius:8px;padding:9px}
input[type=range]{accent-color:#67e8f9}.big{font-size:32px;font-weight:750;letter-spacing:-.02em}.muted{color:#94a3b8;font-size:13px;line-height:1.5}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}.metric{background:#0b1425;border:1px solid #25354d;border-radius:10px;padding:12px}.metric label{display:block;color:#94a3b8;font-size:12px;margin-bottom:8px}.metric strong{font-size:21px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:right;border-bottom:1px solid #29384f;padding:10px 8px;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{color:#9ca3af;font-weight:600}
.tablewrap{overflow-x:auto}.bar{height:8px;background:#25354d;border-radius:99px;margin-top:8px;overflow:hidden}.bar span{display:block;height:100%;background:#22d3ee}
.warning{border-left:3px solid #f59e0b;padding-left:12px}.good{color:#67e8f9}.negative{color:#fda4af}summary{cursor:pointer;font-weight:650}code{color:#bae6fd}
@media(max-width:560px){body{padding:14px}.panel{padding:13px}.big{font-size:27px}}
</style></head><body>
<h1>QQQ LONG PUT × SPY SHORT PUT</h1>
<div class="sub">Historical end-of-day quote replay · contract ratio adjustable from 1:1 to 10:10 · default package 4 QQQ long puts : 5 SPY short puts</div>
<div class="panel">
<div class="controls">
<label class="control">Contract matching rule<select id="mode"><option value="PREMIUM_MATCHED" selected>Same per-contract premium price</option><option value="DELTA_MATCHED">Same target absolute delta</option><option value="OTM_MATCHED">Same percent out-of-the-money</option></select></label>
<label class="control">Exit after<select id="horizon"><option value="1">1 trading session</option><option value="3">3 trading sessions</option><option value="5" selected>5 trading sessions</option><option value="10">10 trading sessions</option><option value="20">20 trading sessions</option></select></label>
<label class="control">Cost scenario<select id="cost"><option value="TOUCH_NO_COMMISSION">Bid/ask touch, no commission</option><option value="STANDARD" selected>Standard commission</option><option value="STRESS">Worse friction stress</option></select></label>
<label class="control">QQQ LONG PUT contracts: <b id="longQtyLabel">4</b><input id="longQty" type="range" min="1" max="10" step="1" value="4"></label>
<label class="control">SPY SHORT PUT contracts: <b id="shortQtyLabel">5</b><input id="shortQty" type="range" min="1" max="10" step="1" value="5"></label>
</div>
<div class="muted" id="contractNote" style="margin-top:14px"></div>
</div>
<div class="panel">
<div class="grid">
<div class="metric"><label>Combined package win rate</label><div class="big" id="winRate">—</div><div class="bar"><span id="winBar" style="width:0%"></span></div><div class="muted" id="sample">—</div></div>
<div class="metric"><label>Average net P&L / episode</label><strong id="meanPnl">—</strong><div class="muted">Dollar P&L for the selected full ratio, after selected costs</div></div>
<div class="metric"><label>Median net P&L</label><strong id="medianPnl">—</strong><div class="muted">50th percentile of paired episodes</div></div>
<div class="metric"><label>Lower-tail P&L (P05 / P01)</label><strong id="tails">—</strong><div class="muted" id="es05">—</div></div>
<div class="metric"><label>Profit factor</label><strong id="pf">—</strong><div class="muted" id="avgWinLoss">—</div></div>
<div class="metric"><label>Worst historical episode</label><strong id="worst">—</strong><div class="muted">Observed quoted exit path, not maximum possible loss</div></div>
<div class="metric"><label>Non-overlap offset win-rate range</label><strong id="offsetRange">—</strong><div class="muted">Entry calendar offset sensitivity; reduces overlap distortion but is not a future-probability guarantee</div></div>
<div class="metric"><label>Median opening net cash flow</label><strong id="cashflow">—</strong><div class="muted">Positive = net credit; negative = net debit</div></div>
<div class="metric"><label>Simultaneous zero-price stress</label><strong id="zeroStress">—</strong><div class="muted">Hypothetical both-underlyings-to-zero expiry payoff; not the observed-horizon worst loss</div></div>
</div>
</div>
<div class="panel"><h2>Holding-period comparison</h2><div class="muted">Uses the same matching rule, contract quantities and cost setting; coverage changes by horizon because missing exit quotes and expired contracts are not filled with synthetic marks.</div><div class="tablewrap"><table><thead><tr><th>Exit horizon</th><th>N paired</th><th>Wins</th><th>Win rate</th><th>Mean P&L</th><th>P05</th><th>Worst</th></tr></thead><tbody id="horizonRows"></tbody></table></div></div>
<div class="panel"><h2>Quote coverage and missing marks</h2><div class="muted">This is the denominator audit: absent quotes and expired contracts are not treated as losses or zero-value exits. Read coverage beside every win rate.</div><div class="tablewrap"><table><thead><tr><th>Pairing rule</th><th>Candidate pairs</th><th>Paired entries</th><th>Entry coverage</th><th>Exit horizon</th><th>Paired exits</th><th>Exit coverage / entries</th><th>Missing exit marks</th></tr></thead><tbody id="coverageRows"></tbody></table></div></div>
<div class="panel"><h2>Market-regime split</h2><div class="muted">Regimes use realized underlying close-to-close returns from entry to exit. They describe where package outcomes occurred; they are not entry-time predictive signals.</div><div class="tablewrap"><table><thead><tr><th>Regime</th><th>N</th><th>Wins</th><th>Win rate</th><th>Mean package P&L</th></tr></thead><tbody id="regimeRows"></tbody></table></div></div>
<div class="panel"><h2>Method, data and limits</h2><div id="method"></div><details style="margin-top:12px"><summary>Dataset hash pins</summary><pre id="hashes" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details></div>
<script>
const R = __REPORT_PAYLOAD__;
const MODE_LABELS = {DELTA_MATCHED:"Same target absolute delta",OTM_MATCHED:"Same percent OTM",PREMIUM_MATCHED:"Same per-contract premium"};
const REGIME_LABELS = {BOTH_DOWN_QQQ_WEAKER:"Both fell; QQQ fell more",BOTH_DOWN_SPY_WEAKER:"Both fell; SPY fell more",BOTH_UP:"Both rose / flat",MIXED:"Mixed direction"};
const $ = id => document.getElementById(id);
const money = n => n == null || !Number.isFinite(Number(n)) ? "N/A" : (Number(n)<0?"−$":"$")+Math.abs(Number(n)).toLocaleString("en-US",{maximumFractionDigits:0});
const pct = n => n == null || !Number.isFinite(Number(n)) ? "N/A" : Number(n).toFixed(1)+"%";
const num = n => n == null || !Number.isFinite(Number(n)) ? "N/A" : Number(n).toFixed(2);
function getRow(h) {
  return R.summaries.find(x=>x.mode===$("mode").value && x.horizon===Number(h) && x.cost_id===$("cost").value && x.long_qty===Number($("longQty").value) && x.short_qty===Number($("shortQty").value));
}
function render() {
  const lq=Number($("longQty").value), sq=Number($("shortQty").value), h=Number($("horizon").value), row=getRow(h);
  $("longQtyLabel").textContent=String(lq); $("shortQtyLabel").textContent=String(sq);
  if (!row || row.n===0) {
    ["winRate","sample","meanPnl","medianPnl","tails","es05","pf","avgWinLoss","worst","offsetRange","cashflow","zeroStress"].forEach(id=>$(id).textContent="BLOCKED / no paired observations");
    $("winBar").style.width="0%"; $("horizonRows").innerHTML=""; $("regimeRows").innerHTML="";
    return;
  }
  $("winRate").textContent=pct(row.win_rate_pct); $("winBar").style.width=Math.max(0,Math.min(100,row.win_rate_pct))+"%";
  $("sample").textContent=String(row.wins)+" wins / "+String(row.losses)+" losses / "+String(row.breakeven)+" flat · N="+String(row.n);
  $("meanPnl").textContent=money(row.mean_pnl); $("medianPnl").textContent=money(row.median_pnl);
  $("tails").textContent=money(row.p05_pnl)+" / "+money(row.p01_pnl); $("es05").textContent="Mean of worst ~5%: "+money(row.es05_pnl);
  $("pf").textContent=num(row.profit_factor); $("avgWinLoss").textContent="Average win "+money(row.avg_win)+" · average loss "+money(row.avg_loss);
  $("worst").textContent=money(row.worst_pnl);
  $("offsetRange").textContent=row.offset_win_rate_min_pct==null?"N/A":pct(row.offset_win_rate_min_pct)+" / "+pct(row.offset_win_rate_median_pct)+" / "+pct(row.offset_win_rate_max_pct);
  $("cashflow").textContent=money(row.median_entry_net_cashflow_selected_ratio_usd);
  $("zeroStress").textContent=money(row.simultaneous_zero_underlying_stress_worst_usd);
  const nDelta=row.median_abs_delta_difference==null?"N/A":num(row.median_abs_delta_difference);
  $("contractNote").textContent="Mode: "+MODE_LABELS[row.mode]+". Median |delta difference|="+nDelta+"; median |DTE difference|="+num(row.median_abs_dte_difference_days)+" days; median |OTM difference|="+num(row.median_abs_otm_difference_pct_points)+" percentage points; same-price mismatch (median per contract, filled prices)="+money(row.median_per_contract_premium_mismatch_usd)+". Initial package cash flow is shown separately; premium matching does not mean the 4:5 package is cash neutral.";
  const horizons=[1,3,5,10,20];
  $("horizonRows").innerHTML=horizons.map(x=>{const z=getRow(x);return "<tr><td>"+x+" sessions</td><td>"+(z?z.n:0)+"</td><td>"+(z?z.wins:0)+"</td><td>"+(z?pct(z.win_rate_pct):"N/A")+"</td><td>"+(z?money(z.mean_pnl):"N/A")+"</td><td>"+(z?money(z.p05_pnl):"N/A")+"</td><td>"+(z?money(z.worst_pnl):"N/A")+"</td></tr>";}).join("");
  $("regimeRows").innerHTML=Object.keys(REGIME_LABELS).map(k=>{const z=row.regimes[k];return "<tr><td>"+REGIME_LABELS[k]+"</td><td>"+z.n+"</td><td>"+z.wins+"</td><td>"+pct(z.win_rate_pct)+"</td><td>"+money(z.mean_pnl)+"</td></tr>";}).join("");
}
["mode","horizon","cost","longQty","shortQty"].forEach(id=>$(id).addEventListener("input",render));
$("method").innerHTML="<p><b>Source:</b> historical EOD option chains from the pinned data-v1 release, with overlapping SPY/QQQ coverage beginning in 2011. QQQ and SPY option chains are different contracts; matching is selectable rather than assuming equal dollar strikes mean comparable risk.</p>"
+"<p><b>No same-close look-ahead:</b> choose puts using the signal-day chain, mark entry on the next shared trading-session close at QQQ ask (long) and SPY bid (short), then close both legs on the same later session at QQQ bid and SPY ask. The fixed contracts are followed; missing quote/expired contract = missing observation, never zero or forward-filled.</p>"
+"<p><b>Selection defaults:</b> target "+R.meta.target_dte+" calendar DTE ±"+R.meta.dte_tolerance+" days; delta target "+R.meta.target_abs_delta+"; OTM target "+pct(R.meta.target_otm*100)+". Premium matching chooses SPY bid nearest to the QQQ ask observed on the signal day. Ratio quantities are independent integer contracts, each multiplier "+R.meta.multiplier+".</p>"
+"<p><b>Win definition:</b> combined net P&amp;L strictly greater than $0 after the selected commission/slippage scenario. The sample includes daily rolling entries, so adjacent episodes overlap. The offset sensitivity shows the min/median/max win rate across holding-horizon-spaced entry cohorts; it helps expose path dependence but is not an independent-trial confidence interval.</p>"
+"<p><b>Execution limitations:</b> EOD snapshots are not confirmed fills and the source does not guarantee quoted size. Bid/ask touch is an estimate; stress adds commission and per-side slippage. No intraday gap fills, assignment, early exercise, broker margin, portfolio concurrency or capital-sizing claims are made. The simultaneous zero-price number is a hypothetical expiry tail stress, not the empirical worst exit.</p>"
+"<p class='warning'><b>Interpretation boundary:</b> a high win rate can coexist with a large short-put tail loss and poor expected value. Check mean/median, P05/P01, worst P&amp;L, stress loss and SPY assignment notional before interpreting the ratio.</p>"
+"<p class='muted'>Generated status: "+R.meta.status+". Sample period: "+R.meta.sample_start+" to "+R.meta.sample_end+". This is descriptive historical research, not a forward probability or trade instruction.</p>";
$("hashes").textContent=JSON.stringify(R.meta.source_hashes,null,2);
const MODE_KEYS = ["PREMIUM_MATCHED","DELTA_MATCHED","OTM_MATCHED"];
const MODE_NAMES = {PREMIUM_MATCHED:"Premium matched",DELTA_MATCHED:"Delta matched",OTM_MATCHED:"Percent-OTM matched"};
const renderCoverage = () => {
  let html = "";
  for (const mode of MODE_KEYS) {
    const c = R.meta.coverage[mode];
    const entryRate = c.selected_contract_pairs ? (100*c.entry_pair_quotes/c.selected_contract_pairs) : null;
    for (const horizon of R.meta.horizons) {
      const h = c.horizons[String(horizon)];
      const exitRate = c.entry_pair_quotes ? (100*h.paired_exits/c.entry_pair_quotes) : null;
      html += "<tr><td>"+MODE_NAMES[mode]+"</td><td>"+c.selected_contract_pairs+"</td><td>"+c.entry_pair_quotes+"</td><td>"+pct(entryRate)+"</td><td>"+horizon+" sessions</td><td>"+h.paired_exits+"</td><td>"+pct(exitRate)+"</td><td>"+h.missing_exit_quotes+"</td></tr>";
    }
  }
  $("coverageRows").innerHTML=html;
};
renderCoverage();
render();
</script></body></html>""".replace("__REPORT_PAYLOAD__", payload)


def replay(args: argparse.Namespace) -> dict[str, Any]:
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    max_dte = args.target_dte + args.dte_tolerance
    qqq_spot = load_underlying(Path(args.qqq_underlying), start, end)
    spy_spot = load_underlying(Path(args.spy_underlying), start, end)
    common_dates = sorted(set(qqq_spot).intersection(spy_spot))
    if len(common_dates) <= max(HORIZONS) + 2:
        raise ValueError("Insufficient common SPY/QQQ underlying sessions.")
    qqq_opts, qqq_meta = load_put_quotes(Path(args.qqq_options), start, end, max_dte)
    spy_opts, spy_meta = load_put_quotes(Path(args.spy_options), start, end, max_dte)
    qqq_quote_dates = set(qqq_opts.index.get_level_values("quote_date").unique())
    spy_quote_dates = set(spy_opts.index.get_level_values("quote_date").unique())
    usable_dates = [d for d in common_dates if d in qqq_quote_dates and d in spy_quote_dates]
    if not usable_dates:
        raise ValueError("No shared SPY/QQQ sessions have valid option quotes.")
    coverage: dict[str, Any] = {
        mode: {
            "common_signal_sessions": len(usable_dates),
            "selected_contract_pairs": 0,
            "entry_pair_quotes": 0,
            "missing_entry_quotes": 0,
            "no_candidate_pair": 0,
            "horizons": {str(h): {"paired_exits": 0, "missing_exit_quotes": 0} for h in HORIZONS},
        } for mode in MODES
    }
    samples: list[dict[str, Any]] = []
    date_pos = {d: i for i, d in enumerate(common_dates)}
    for signal_date in usable_dates:
        i = date_pos[signal_date]
        if i + max(HORIZONS) + 1 >= len(common_dates):
            continue
        entry_date = common_dates[i + 1]
        qqq_day = _day(qqq_opts, signal_date)
        spy_day = _day(spy_opts, signal_date)
        qqq_cand = _entry_candidates(qqq_day, args.target_dte, args.dte_tolerance)
        spy_cand = _entry_candidates(spy_day, args.target_dte, args.dte_tolerance)
        choices = _mode_contracts(
            qqq_cand, spy_cand, qqq_spot[signal_date], spy_spot[signal_date],
            args.target_dte, args.target_abs_delta, args.target_otm,
        )
        for mode in MODES:
            if mode not in choices:
                coverage[mode]["no_candidate_pair"] += 1
                continue
            coverage[mode]["selected_contract_pairs"] += 1
            qref, sref = choices[mode]
            qentry = _quote_at(qqq_opts, entry_date, qref["expiration"], qref["strike_key"])
            sentry = _quote_at(spy_opts, entry_date, sref["expiration"], sref["strike_key"])
            if qentry is None or sentry is None:
                coverage[mode]["missing_entry_quotes"] += 1
                continue
            if float(qentry["ask"]) <= 0 or float(sentry["bid"]) <= 0:
                coverage[mode]["missing_entry_quotes"] += 1
                continue
            coverage[mode]["entry_pair_quotes"] += 1
            delta_diff = None
            if qref["delta_signal"] is not None and sref["delta_signal"] is not None:
                delta_diff = abs(abs(qref["delta_signal"]) - abs(sref["delta_signal"]))
            dte_diff = abs(qref["dte_signal"] - sref["dte_signal"])
            otm_diff = abs(qref["otm_signal"] - sref["otm_signal"])
            actual_mismatch = abs(float(qentry["ask"]) - float(sentry["bid"]))
            for horizon in HORIZONS:
                exit_date = common_dates[i + 1 + horizon]
                qexit = _quote_at(qqq_opts, exit_date, qref["expiration"], qref["strike_key"])
                sexit = _quote_at(spy_opts, exit_date, sref["expiration"], sref["strike_key"])
                if qexit is None or sexit is None or float(qexit["bid"]) <= 0 or float(sexit["ask"]) <= 0:
                    coverage[mode]["horizons"][str(horizon)]["missing_exit_quotes"] += 1
                    continue
                long_gross, short_gross = leg_pnl_per_contract(
                    float(qentry["ask"]), float(qexit["bid"]),
                    float(sentry["bid"]), float(sexit["ask"]),
                )
                qret = qqq_spot[exit_date] / qqq_spot[entry_date] - 1.0
                sret = spy_spot[exit_date] / spy_spot[entry_date] - 1.0
                coverage[mode]["horizons"][str(horizon)]["paired_exits"] += 1
                samples.append({
                    "mode": mode, "horizon": horizon,
                    "signal_date": signal_date.strftime("%Y-%m-%d"),
                    "entry_date": entry_date.strftime("%Y-%m-%d"),
                    "entry_index": i + 1,
                    "exit_date": exit_date.strftime("%Y-%m-%d"),
                    "qqq_strike": qref["strike"], "spy_strike": sref["strike"],
                    "qqq_expiration": qref["expiration"].strftime("%Y-%m-%d"),
                    "spy_expiration": sref["expiration"].strftime("%Y-%m-%d"),
                    "qqq_dte_signal": qref["dte_signal"], "spy_dte_signal": sref["dte_signal"],
                    "qqq_delta_signal": qref["delta_signal"], "spy_delta_signal": sref["delta_signal"],
                    "qqq_entry_ask": float(qentry["ask"]), "qqq_exit_bid": float(qexit["bid"]),
                    "spy_entry_bid": float(sentry["bid"]), "spy_exit_ask": float(sexit["ask"]),
                    "long_gross_pnl": long_gross, "short_gross_pnl": short_gross,
                    "qqq_spot_return": qret, "spy_spot_return": sret,
                    "regime": _regime_for(qret, sret),
                    "actual_entry_premium_mismatch": actual_mismatch,
                    "delta_abs_diff": delta_diff, "dte_abs_diff": float(dte_diff),
                    "otm_abs_diff": float(otm_diff),
                })
    if not samples:
        raise ValueError("All paired quote paths were incomplete; report remains BLOCKED.")
    summaries = build_summaries(samples, args.max_qty)
    used_dates = [pd.Timestamp(r["signal_date"]) for r in samples]
    meta = {
        "status": "COMPUTED_HISTORICAL_EOD_QUOTE_REPLAY",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sample_start": min(used_dates).strftime("%Y-%m-%d"),
        "sample_end": max(used_dates).strftime("%Y-%m-%d"),
        "underlying_common_sessions": len(common_dates),
        "option_quote_signal_sessions": len(usable_dates),
        "target_dte": args.target_dte,
        "dte_tolerance": args.dte_tolerance,
        "target_abs_delta": args.target_abs_delta,
        "target_otm": args.target_otm,
        "max_qty": args.max_qty,
        "multiplier": MULTIPLIER,
        "entry_execution_assumption": "Select on signal-day EOD chain; enter at next common-session EOD quote: buy QQQ put at ask, sell SPY put at bid.",
        "exit_execution_assumption": "Close both selected contracts on the same later common session: sell QQQ long put at bid, buy back SPY short put at ask.",
        "missing_mark_policy": "Missing, expired, invalid, or non-executable quote-side marks are excluded for that horizon; never forward-filled or replaced by zero.",
        "overlap_warning": "Daily starts overlap; horizon-spaced offset cohorts are reported as path sensitivity, not an independent-trial probability interval.",
        "source_release": SOURCE_RELEASE,
        "source_hashes": SOURCE_HASHES,
        "quote_source_limit": "EOD option snapshots; quote sizes are not part of this source contract; prices are modeled touch fills, not confirmed executions.",
        "qqq_data_audit": qqq_meta,
        "spy_data_audit": spy_meta,
        "coverage": coverage,
        "paired_exit_samples": len(samples),
        "matching_modes": list(MODES),
        "horizons": list(HORIZONS),
        "cost_scenarios": list(COSTS),
    }
    return {"meta": meta, "summaries": summaries}


def make_markdown_report(report: dict[str, Any]) -> str:
    meta = report["meta"]
    summaries = report["summaries"]

    def money(value: Any) -> str:
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return "N/A"
        return ("−" if float(value) < 0 else "") + "$" + format(abs(float(value)), ",.0f")

    def pct(value: Any) -> str:
        return "N/A" if value is None else f"{float(value):.1f}%"

    def row(mode: str, horizon: int, cost: str, long_qty: int = 4, short_qty: int = 5) -> dict[str, Any]:
        return next(x for x in summaries if x["mode"] == mode and x["horizon"] == horizon
                    and x["cost_id"] == cost and x["long_qty"] == long_qty and x["short_qty"] == short_qty)

    lines = [
        "# QQQ LONG PUT × SPY SHORT PUT — Paired Historical Replay",
        "",
        f"**Status:** {meta['status']}  ",
        f"**Signal sample window:** {meta['sample_start']} to {meta['sample_end']}  ",
        f"**Underlying common sessions:** {meta['underlying_common_sessions']:,}  ",
        f"**Paired exit observations across all modes/horizons:** {meta['paired_exit_samples']:,}",
        "",
        "## Baseline: 4 QQQ LONG PUT : 5 SPY SHORT PUT",
        "",
        "Default pairing is per-contract premium-matched; contracts are selected at the signal-day EOD quote, entered on the next common session, and closed together at the selected horizon. Standard friction is $0.65 per contract per side.",
        "",
        "| Holding period | N paired | Wins | Losses | Flat | Win rate | Mean net P&L | Median | P05 | P01 | Worst observed | Profit factor |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for horizon in HORIZONS:
        x = row("PREMIUM_MATCHED", horizon, "STANDARD")
        pf = "N/A" if x.get("profit_factor") is None else f"{x['profit_factor']:.2f}"
        lines.append(
            f"| {horizon} sessions | {x.get('n', 0):,} | {x.get('wins', 0):,} | {x.get('losses', 0):,} | {x.get('breakeven', 0):,} "
            f"| {pct(x.get('win_rate_pct'))} | {money(x.get('mean_pnl'))} | {money(x.get('median_pnl'))} "
            f"| {money(x.get('p05_pnl'))} | {money(x.get('p01_pnl'))} | {money(x.get('worst_pnl'))} | {pf} |"
        )
    lines += [
        "",
        "## Matching rule sensitivity — 5-session exit, 4:5, standard friction",
        "",
        "| Rule | N paired | Win rate | Mean net P&L | Median | P05 | Worst observed | Median delta gap | Median DTE gap | Median OTM gap (pp) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        x = row(mode, 5, "STANDARD")
        dgap = "N/A" if x["median_abs_delta_difference"] is None else f"{x['median_abs_delta_difference']:.3f}"
        lines.append(
            f"| {mode} | {x['n']:,} | {pct(x['win_rate_pct'])} | {money(x['mean_pnl'])} | {money(x['median_pnl'])} "
            f"| {money(x['p05_pnl'])} | {money(x['worst_pnl'])} | {dgap} "
            f"| {x['median_abs_dte_difference_days']:.1f} | {x['median_abs_otm_difference_pct_points']:.2f} |"
        )
    lines += [
        "",
        "## Data coverage audit",
        "",
        "The denominator matters. Missing / expired option marks are not converted to zero, so each displayed win rate must be read with paired-exit coverage.",
        "",
        "| Pairing rule | Valid candidate pairs | Paired entries | Entry coverage | Horizon | Paired exits | Exit coverage vs entries | Missing exit marks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        c = meta["coverage"][mode]
        entry_rate = 100.0*c["entry_pair_quotes"]/c["selected_contract_pairs"] if c["selected_contract_pairs"] else None
        for horizon in HORIZONS:
            h = c["horizons"][str(horizon)]
            exit_rate = 100.0*h["paired_exits"]/c["entry_pair_quotes"] if c["entry_pair_quotes"] else None
            lines.append(
                f"| {mode} | {c['selected_contract_pairs']:,} | {c['entry_pair_quotes']:,} | {pct(entry_rate)} "
                f"| {horizon} sessions | {h['paired_exits']:,} | {pct(exit_rate)} | {h['missing_exit_quotes']:,} |"
            )
    lines += [
        "",
        "## Assumptions and interpretation",
        "",
        f"- Target expiry: {meta['target_dte']} calendar DTE ±{meta['dte_tolerance']} days; target absolute delta {meta['target_abs_delta']:.2f}; OTM target {meta['target_otm']:.1%}.",
        "- Fill convention: buy QQQ put at ask / sell SPY put at bid; close QQQ put at bid / buy back SPY put at ask. Entry occurs on the next common session after contract selection.",
        "- Costs: touch with no commission, standard $0.65 per contract per side, and stress $1.30 per contract per side plus $0.05 per share per side.",
        "- Daily entry starts overlap. Horizon-spaced offset cohorts are sensitivity diagnostics, not independent trials or future-probability confidence intervals.",
        "- Historical EOD quote-side marks are modeled fills, not verified execution. Quote sizes are unavailable. Expiry settlement, early assignment/exercise, broker margin, intraday gaps, portfolio concurrency, and taxes are not modeled.",
        "- Short SPY puts retain substantial tail liability. The hypothetical both-underlyings-to-zero stress, P05/P01, worst observed P&L, average win/loss and profit factor are essential context; win rate alone is insufficient.",
        "",
        "## Interactive view",
        "",
        "Download index.html from this folder and open it in a browser to adjust contract counts (1–10 per leg), matching rule, holding horizon and cost scenario. The HTML is self-contained. summary.json contains aggregate results only; raw chains are not committed.",
        "",
        "## Pinned data source",
        "",
        f"Release: {meta['source_release']}",
        "",
        "| Input | SHA-256 |",
        "|---|---|",
    ]
    for name, digest in meta["source_hashes"].items():
        lines.append(f"| {name} | {digest} |")
    lines += ["", "This is descriptive historical research, not a broker execution report or a forward probability forecast.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qqq-options", required=True)
    parser.add_argument("--spy-options", required=True)
    parser.add_argument("--qqq-underlying", required=True)
    parser.add_argument("--spy-underlying", required=True)
    parser.add_argument("--start", default="2011-03-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--target-dte", type=int, default=30)
    parser.add_argument("--dte-tolerance", type=int, default=10)
    parser.add_argument("--target-abs-delta", type=float, default=0.25)
    parser.add_argument("--target-otm", type=float, default=0.05)
    parser.add_argument("--max-qty", type=int, default=10)
    parser.add_argument("--output-dir", default="reports/qqq-long-put-spy-short-put")
    args = parser.parse_args()
    if args.target_dte < 1 or args.dte_tolerance < 0 or not 0 < args.target_abs_delta < 0.5:
        parser.error("DTE must be positive, tolerance nonnegative, and target absolute delta between 0 and 0.5.")
    if not 0 < args.target_otm < 0.5 or not 1 <= args.max_qty <= 20:
        parser.error("Target OTM must be between 0 and 0.5; max quantity must be 1 through 20.")
    report = replay(args)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "index.html").write_text(make_html(report), encoding="utf-8")
    markdown = make_markdown_report(report)
    (out / "REPORT.md").write_text(markdown, encoding="utf-8")
    default = next(r for r in report["summaries"] if r["mode"] == "PREMIUM_MATCHED" and r["horizon"] == 5 and r["cost_id"] == "STANDARD" and r["long_qty"] == 4 and r["short_qty"] == 5)
    print(json.dumps({
        "status": report["meta"]["status"],
        "sample_period": [report["meta"]["sample_start"], report["meta"]["sample_end"]],
        "paired_exit_samples": report["meta"]["paired_exit_samples"],
        "default_4_to_5_premium_matched_5day_standard": {k: default.get(k) for k in ("n", "wins", "losses", "win_rate_pct", "mean_pnl", "median_pnl", "p05_pnl", "worst_pnl", "profit_factor")},
        "coverage": report["meta"]["coverage"],
        "output_dir": str(out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
