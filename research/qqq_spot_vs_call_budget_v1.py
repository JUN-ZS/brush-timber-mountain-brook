#!/usr/bin/env python3
"""Historical-data comparison: QQQ spot buy-and-hold vs budgeted long calls.

Research only. Uses observed historical option bid/ask quotes from the pinned
QQQ_options.parquet dataset. No model-imputed option prices are used.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import brentq

CAPITAL_USD = 7000.0
TARGET_DELTA = 0.05
WEEKLY_STEP_SESSIONS = 5
WEEKLY_DTE_TARGET = 7
WEEKLY_DTE_RANGE = (5, 10)
ANNUAL_DTE_TARGET = 365
ANNUAL_DTE_RANGE = (330, 400)
DELTA_ACCEPT_RANGE = (0.01, 0.10)
OPTION_MULTIPLIER = 100
EXIT_QUOTE_MAX_AGE_DAYS = 5
NEAR_TOTAL_LOSS_USD = CAPITAL_USD * 0.01
EXPECTED_OPTIONS_SHA256 = "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734"
EXPECTED_UNDERLYING_SHA256 = "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_underlying(path: Path):
    x = pd.read_parquet(path)
    x.columns = [str(c).strip().lower().replace(" ", "_") for c in x.columns]
    if "date" not in x or "close" not in x:
        raise ValueError(f"Underlying parquet needs date and close columns; found {list(x.columns)}")
    dates = pd.to_datetime(x["date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_localize(None)
    x["date"] = dates.dt.normalize()
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    adj_col = next((c for c in ("adjclose", "adj_close", "adjusted_close", "adjustedclose") if c in x.columns), None)
    if adj_col:
        x[adj_col] = pd.to_numeric(x[adj_col], errors="coerce")
        x["benchmark_price"] = x[adj_col].where(x[adj_col] > 0, x["close"])
        benchmark_mode = "adjusted_close"
    else:
        x["benchmark_price"] = x["close"]
        benchmark_mode = "close_price_only"
    x = x.dropna(subset=["date", "close", "benchmark_price"])
    x = x[(x["close"] > 0) & (x["benchmark_price"] > 0)]
    x = x.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    if len(x) < 3000:
        raise ValueError(f"Underlying history unexpectedly short: {len(x)} rows")
    return x, benchmark_mode


def option_date_bounds(path: Path):
    con = duckdb.connect()
    try:
        r = con.execute(
            "SELECT MIN(CAST(date AS DATE)), MAX(CAST(date AS DATE)), COUNT(*) FROM read_parquet(?)",
            [str(path)],
        ).fetchone()
    finally:
        con.close()
    if not r or r[0] is None or r[1] is None:
        raise ValueError("Could not read dates from QQQ options parquet")
    return pd.Timestamp(r[0]), pd.Timestamp(r[1]), int(r[2])


def read_entry_chains(path: Path, dates: list[pd.Timestamp]) -> pd.DataFrame:
    entry_dates = sorted({pd.Timestamp(d).date() for d in dates})
    if not entry_dates:
        return pd.DataFrame()
    sql = """
        SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id, CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
               CAST(delta AS DOUBLE) AS delta, COALESCE(CAST(volume AS DOUBLE), 0.0) AS volume
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER(CAST("type" AS VARCHAR)) = 'CALL'
          AND date IS NOT NULL AND expiration IS NOT NULL AND contract_id IS NOT NULL
          AND strike IS NOT NULL AND delta IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
          AND CAST(bid AS DOUBLE) >= 0 AND CAST(ask AS DOUBLE) > 0
          AND CAST(ask AS DOUBLE) >= CAST(bid AS DOUBLE)
          AND (
            CAST(expiration AS DATE) BETWEEN CAST(date AS DATE) + INTERVAL 5 DAY AND CAST(date AS DATE) + INTERVAL 10 DAY
            OR CAST(expiration AS DATE) BETWEEN CAST(date AS DATE) + INTERVAL 330 DAY AND CAST(date AS DATE) + INTERVAL 400 DAY
          )
    """
    con = duckdb.connect()
    try:
        out = con.execute(sql, [str(path), entry_dates]).df()
    finally:
        con.close()
    if out.empty:
        return out
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["expiration"] = pd.to_datetime(out["expiration"]).dt.normalize()
    out["contract_id"] = out["contract_id"].astype(str)
    for c in ("strike", "bid", "ask", "delta", "volume"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["dte"] = (out["expiration"] - out["date"]).dt.days
    return out.dropna(subset=["date", "expiration", "strike", "bid", "ask", "delta", "dte"])


def pick_candidate(chain: pd.DataFrame, entry_date, spot: float, kind: str):
    """Select an OTM Call nearest 5 absolute delta within the fixed DTE band."""
    if chain is None or chain.empty:
        return None
    if kind == "weekly":
        lo, hi, target_dte = (*WEEKLY_DTE_RANGE, WEEKLY_DTE_TARGET)
    elif kind == "annual":
        lo, hi, target_dte = (*ANNUAL_DTE_RANGE, ANNUAL_DTE_TARGET)
    else:
        raise ValueError(f"Unknown strategy kind: {kind}")
    d = pd.Timestamp(entry_date).normalize()
    g = chain[chain["date"].eq(d)].copy()
    if g.empty:
        return None
    g = g[
        (g["dte"] >= lo) & (g["dte"] <= hi) & (g["strike"] > float(spot))
        & (g["delta"].abs() >= DELTA_ACCEPT_RANGE[0]) & (g["delta"].abs() <= DELTA_ACCEPT_RANGE[1])
        & (g["ask"] > 0) & (g["ask"] >= g["bid"]) & (g["bid"] >= 0)
    ].copy()
    if g.empty:
        return None
    g["delta_error"] = (g["delta"].abs() - TARGET_DELTA).abs()
    g["dte_error"] = (g["dte"] - target_dte).abs()
    g = g.sort_values(["delta_error", "dte_error", "volume", "ask"],
                      ascending=[True, True, False, True], kind="mergesort")
    r = g.iloc[0]
    return {
        "entry_date": d, "expiration": pd.Timestamp(r["expiration"]).normalize(),
        "contract_id": str(r["contract_id"]), "strike": float(r["strike"]),
        "delta": float(r["delta"]), "dte": int(r["dte"]), "bid": float(r["bid"]),
        "ask": float(r["ask"]), "volume": float(r["volume"]), "spot": float(spot),
        "otm_pct": float(r["strike"]) / float(spot) - 1.0,
    }


def read_contract_quotes(path: Path, contract_ids: list[str]) -> dict[str, dict]:
    ids = sorted(set(str(x) for x in contract_ids if x is not None))
    if not ids:
        return {}
    sql = """
        SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask
        FROM read_parquet(?)
        WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
          AND date IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
          AND CAST(bid AS DOUBLE) >= 0 AND CAST(ask AS DOUBLE) >= CAST(bid AS DOUBLE)
        ORDER BY CAST(contract_id AS VARCHAR), CAST(date AS DATE)
    """
    con = duckdb.connect()
    try:
        q = con.execute(sql, [str(path), ids]).df()
    finally:
        con.close()
    if q.empty:
        return {}
    q["date"] = pd.to_datetime(q["date"]).dt.normalize()
    q["contract_id"] = q["contract_id"].astype(str)
    result = {}
    for cid, g in q.groupby("contract_id", sort=False):
        g = g.sort_values("date").drop_duplicates("date")
        result[str(cid)] = {
            "dates": g["date"].to_numpy(dtype="datetime64[ns]"),
            "bid": g["bid"].to_numpy(dtype=float),
        }
    return result


def _spot_on_or_before(underlying: pd.DataFrame, target: pd.Timestamp):
    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    j = int(np.searchsorted(dates, np.datetime64(pd.Timestamp(target).normalize()), side="right") - 1)
    if j < 0:
        raise ValueError(f"No underlying bar on or before {target}")
    return float(underlying.iloc[j]["close"]), pd.Timestamp(underlying.iloc[j]["date"])


def mark_position(pos: dict, target: pd.Timestamp, quotes: dict[str, dict], underlying: pd.DataFrame):
    """Use latest observed bid within 5 days; otherwise use intrinsic-value floor."""
    cut = min(pd.Timestamp(target).normalize(), pd.Timestamp(pos["expiration"]).normalize())
    q = quotes.get(str(pos["contract_id"]))
    if q is not None and len(q["dates"]):
        dates = q["dates"]
        j = int(np.searchsorted(dates, np.datetime64(cut), side="right") - 1)
        entry_np = np.datetime64(pd.Timestamp(pos["entry_date"]).normalize())
        while j >= 0 and dates[j] <= entry_np:
            j -= 1
        if j >= 0:
            qdate = pd.Timestamp(dates[j]).normalize()
            age = int((cut - qdate).days)
            if 0 <= age <= EXIT_QUOTE_MAX_AGE_DAYS:
                return max(float(q["bid"][j]), 0.0) * OPTION_MULTIPLIER * int(pos["qty"]), "OBSERVED_BID", qdate
    spot, spot_date = _spot_on_or_before(underlying, cut)
    value = max(spot - float(pos["strike"]), 0.0) * OPTION_MULTIPLIER * int(pos["qty"])
    return value, "INTRINSIC_FALLBACK", spot_date


def xirr(cashflows: list[tuple[pd.Timestamp, float]]) -> float | None:
    flows = [(pd.Timestamp(d).normalize(), float(v)) for d, v in cashflows if math.isfinite(float(v))]
    if not flows or not any(v > 0 for _, v in flows):
        return -1.0 if flows else None
    if not any(v < 0 for _, v in flows):
        return None
    flows.sort(key=lambda z: z[0])
    origin = flows[0][0]
    def npv(rate: float) -> float:
        return sum(v / ((1.0 + rate) ** ((d - origin).days / 365.25)) for d, v in flows)
    low, high = -0.999999, 1.0
    f_low, f_high = npv(low), npv(high)
    while f_low * f_high > 0 and high < 1_000_000.0:
        high = high * 2.0 + 1.0
        f_high = npv(high)
    if f_low * f_high > 0:
        return None
    try:
        return float(brentq(npv, low, high, maxiter=500))
    except (ValueError, RuntimeError, OverflowError):
        return None


def size_contracts(cash: float, ask_per_share: float) -> int:
    cost = float(ask_per_share) * OPTION_MULTIPLIER
    if not math.isfinite(cost) or cost <= 0 or cash < cost:
        return 0
    return max(0, int(math.floor((cash + 1e-9) / cost)))


def _date_index(dates: np.ndarray, target: pd.Timestamp, side: str = "left") -> int | None:
    i = int(np.searchsorted(dates, np.datetime64(pd.Timestamp(target).normalize()), side=side))
    return i if i < len(dates) else None


def _candidate_event_dates(underlying: pd.DataFrame, start_idx: int, last_eligible_idx: int):
    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    starts = list(range(start_idx, last_eligible_idx + 1, WEEKLY_STEP_SESSIONS))
    weekly_dates, annual_dates = set(), set()
    for si in starts:
        start_date = pd.Timestamp(underlying.iloc[si]["date"]).normalize()
        end_target = start_date + pd.DateOffset(years=10)
        ei = int(np.searchsorted(dates, np.datetime64(end_target.normalize()), side="right") - 1)
        for idx in range(si, ei, WEEKLY_STEP_SESSIONS):
            weekly_dates.add(pd.Timestamp(underlying.iloc[idx]["date"]).normalize())
        for yr in range(10):
            idx = _date_index(dates, start_date + pd.DateOffset(years=yr), side="left")
            if idx is not None and idx < ei:
                annual_dates.add(pd.Timestamp(underlying.iloc[idx]["date"]).normalize())
    return sorted(weekly_dates), sorted(annual_dates)


def _simulate_path(underlying, start_idx, end_idx, weekly_candidates, annual_candidates, quotes, strategy):
    start_date = pd.Timestamp(underlying.iloc[start_idx]["date"]).normalize()
    end_date = pd.Timestamp(underlying.iloc[end_idx]["date"]).normalize()
    stock_start = float(underlying.iloc[start_idx]["benchmark_price"])
    stock_end = float(underlying.iloc[end_idx]["benchmark_price"])
    stock_terminal = CAPITAL_USD * stock_end / stock_start
    if strategy == "spot_buy_hold":
        return {
            "strategy": strategy, "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(), "terminal_nav_usd": stock_terminal,
            "profit_usd": stock_terminal - CAPITAL_USD, "total_return_pct": stock_terminal / CAPITAL_USD - 1,
            "xirr": (stock_terminal / CAPITAL_USD) ** (365.25 / max((end_date - start_date).days, 1)) - 1,
            "premium_paid_usd": 0.0, "contracts_bought": 0, "entry_events": 1,
            "candidate_misses": 0, "positions_closed": 0, "all_contract_payouts_zero": False,
            "any_contracts_bought": False, "near_total_loss": stock_terminal <= NEAR_TOTAL_LOSS_USD,
            "observed_bid_exits": 0, "intrinsic_fallback_exits": 0, "exit_payout_usd": 0.0,
        }

    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    cash, positions, cashflows = 0.0, [], []
    premium_paid = 0.0
    contracts_bought = candidate_misses = observed_bid_exits = intrinsic_fallback_exits = 0
    position_payouts, exit_payout_total = [], 0.0
    if strategy == "weekly_5d_call":
        event_indices = list(range(start_idx, end_idx, WEEKLY_STEP_SESSIONS))
        contribution = CAPITAL_USD / max(len(event_indices), 1)
        event_kind = "weekly"
    elif strategy == "annual_365d_call":
        event_indices = []
        for yr in range(10):
            idx = _date_index(dates, start_date + pd.DateOffset(years=yr), side="left")
            if idx is not None and idx < end_idx:
                event_indices.append(idx)
        event_indices = sorted(set(event_indices))
        contribution = CAPITAL_USD / max(len(event_indices), 1)
        event_kind = "annual"
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    for idx in event_indices:
        event_date = pd.Timestamp(underlying.iloc[idx]["date"]).normalize()
        keep = []
        for pos in positions:
            if pd.Timestamp(pos["expiration"]).normalize() <= event_date:
                value, source, _ = mark_position(pos, pos["expiration"], quotes, underlying)
                cash += value
                exit_payout_total += value
                position_payouts.append(value)
                if source == "OBSERVED_BID": observed_bid_exits += 1
                else: intrinsic_fallback_exits += 1
            else:
                keep.append(pos)
        positions = keep
        cash += contribution
        cashflows.append((event_date, -contribution))
        candidate_map = weekly_candidates if event_kind == "weekly" else annual_candidates
        candidate = candidate_map.get(event_date)
        if candidate is None:
            candidate_misses += 1
            continue
        qty = size_contracts(cash, candidate["ask"])
        if qty <= 0:
            candidate_misses += 1
            continue
        spend = candidate["ask"] * OPTION_MULTIPLIER * qty
        cash -= spend
        premium_paid += spend
        contracts_bought += qty
        positions.append({**candidate, "qty": qty, "entry_date": event_date, "premium_paid": spend})

    for pos in positions:
        cutoff = min(pd.Timestamp(pos["expiration"]).normalize(), end_date)
        value, source, _ = mark_position(pos, cutoff, quotes, underlying)
        cash += value
        exit_payout_total += value
        position_payouts.append(value)
        if source == "OBSERVED_BID": observed_bid_exits += 1
        else: intrinsic_fallback_exits += 1
    terminal_nav = max(float(cash), 0.0)
    rate = xirr(cashflows + [(end_date, terminal_nav)])
    traded_positions = len(position_payouts)
    return {
        "strategy": strategy, "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(), "terminal_nav_usd": terminal_nav,
        "profit_usd": terminal_nav - CAPITAL_USD, "total_return_pct": terminal_nav / CAPITAL_USD - 1.0,
        "xirr": rate, "premium_paid_usd": premium_paid, "contracts_bought": contracts_bought,
        "entry_events": len(event_indices), "candidate_misses": candidate_misses,
        "positions_closed": traded_positions,
        "all_contract_payouts_zero": bool(traded_positions > 0 and sum(position_payouts) <= 1e-8),
        "any_contracts_bought": contracts_bought > 0,
        "near_total_loss": terminal_nav <= NEAR_TOTAL_LOSS_USD,
        "observed_bid_exits": observed_bid_exits, "intrinsic_fallback_exits": intrinsic_fallback_exits,
        "exit_payout_usd": exit_payout_total,
    }


def _clean(value):
    if isinstance(value, dict): return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_clean(v) for v in value]
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, (np.floating, float)): return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, np.bool_): return bool(value)
    if isinstance(value, pd.Timestamp): return value.isoformat()
    return value


def summarise(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, g in results.groupby("strategy", sort=False):
        traded = g[g["any_contracts_bought"].astype(bool)]
        rows.append({
            "strategy": strategy, "windows": int(len(g)),
            "mean_terminal_nav_usd": float(g.terminal_nav_usd.mean()),
            "median_terminal_nav_usd": float(g.terminal_nav_usd.median()),
            "p10_terminal_nav_usd": float(g.terminal_nav_usd.quantile(.10)),
            "p25_terminal_nav_usd": float(g.terminal_nav_usd.quantile(.25)),
            "p75_terminal_nav_usd": float(g.terminal_nav_usd.quantile(.75)),
            "p90_terminal_nav_usd": float(g.terminal_nav_usd.quantile(.90)),
            "mean_profit_usd": float(g.profit_usd.mean()),
            "median_profit_usd": float(g.profit_usd.median()),
            "positive_window_pct": float((g.profit_usd > 0).mean() * 100),
            "ending_below_7000_pct": float((g.terminal_nav_usd < CAPITAL_USD).mean() * 100),
            "median_xirr_pct": float(g.xirr.dropna().median() * 100) if g.xirr.notna().any() else None,
            "mean_xirr_pct": float(g.xirr.dropna().mean() * 100) if g.xirr.notna().any() else None,
            "p10_xirr_pct": float(g.xirr.dropna().quantile(.10) * 100) if g.xirr.notna().any() else None,
            "p90_xirr_pct": float(g.xirr.dropna().quantile(.90) * 100) if g.xirr.notna().any() else None,
            "any_contracts_bought_pct": float(g.any_contracts_bought.astype(bool).mean() * 100),
            "all_contract_payouts_zero_pct_when_traded": float(traded.all_contract_payouts_zero.astype(bool).mean() * 100) if len(traded) else None,
            "near_total_loss_pct": float(g.near_total_loss.astype(bool).mean() * 100),
            "median_contracts_bought": float(g.contracts_bought.median()),
            "median_positions_closed": float(g.positions_closed.median()),
            "median_premium_paid_usd": float(g.premium_paid_usd.median()),
            "median_exit_payout_usd": float(g.exit_payout_usd.median()),
            "median_candidate_misses": float(g.candidate_misses.median()),
            "observed_bid_exit_share_pct": 100.0 * float(g.observed_bid_exits.sum()) /
                max(1.0, float(g.observed_bid_exits.sum() + g.intrinsic_fallback_exits.sum())),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="research/qqq_spot_vs_call_budget_v1/results/latest")
    ap.add_argument("--verify-pinned-hashes", action="store_true")
    args = ap.parse_args()
    data_dir, out_dir = Path(args.data_dir), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    options_path, underlying_path = data_dir / "QQQ_options.parquet", data_dir / "QQQ_underlying.parquet"
    if not options_path.exists() or not underlying_path.exists():
        raise FileNotFoundError("Expected QQQ_options.parquet and QQQ_underlying.parquet in --data-dir")
    options_sha, underlying_sha = sha256_file(options_path), sha256_file(underlying_path)
    if args.verify_pinned_hashes:
        if options_sha != EXPECTED_OPTIONS_SHA256:
            raise RuntimeError(f"QQQ options hash changed: expected {EXPECTED_OPTIONS_SHA256}, got {options_sha}")
        if underlying_sha != EXPECTED_UNDERLYING_SHA256:
            raise RuntimeError(f"QQQ underlying hash changed: expected {EXPECTED_UNDERLYING_SHA256}, got {underlying_sha}")

    underlying, benchmark_mode = load_underlying(underlying_path)
    opt_min, opt_max, option_rows = option_date_bounds(options_path)
    underlying = underlying[(underlying.date >= opt_min) & (underlying.date <= opt_max)].reset_index(drop=True)
    if len(underlying) < 2520:
        raise RuntimeError(f"Common data window lacks ten years: {underlying.date.min()} to {underlying.date.max()}")
    dates = underlying.date.to_numpy(dtype="datetime64[ns]")
    max_end_date = pd.Timestamp(underlying.iloc[-1].date)
    eligible = []
    for idx in range(len(underlying)):
        if pd.Timestamp(underlying.iloc[idx].date).normalize() + pd.DateOffset(years=10) <= max_end_date:
            eligible.append(idx)
        else:
            break
    if not eligible:
        raise RuntimeError("No complete ten-year windows in common data")
    starts = eligible[::WEEKLY_STEP_SESSIONS]
    weekly_dates, annual_dates = _candidate_event_dates(underlying, starts[0], starts[-1])
    event_dates = sorted(set(weekly_dates) | set(annual_dates))
    chains = read_entry_chains(options_path, event_dates)
    if chains.empty:
        raise RuntimeError("No valid QQQ CALL bid/ask/Delta records at target entry dates")
    by_date = {pd.Timestamp(d): g for d, g in chains.groupby("date", sort=False)}
    close_by_date = underlying.set_index("date").close.to_dict()
    weekly_candidates = {d: pick_candidate(by_date.get(d), d, float(close_by_date[d]), "weekly") for d in weekly_dates}
    annual_candidates = {d: pick_candidate(by_date.get(d), d, float(close_by_date[d]), "annual") for d in annual_dates}
    candidate_ids = [c["contract_id"] for c in list(weekly_candidates.values()) + list(annual_candidates.values()) if c is not None]
    quotes = read_contract_quotes(options_path, candidate_ids)

    coverage_rows = []
    for kind, candidates in (("weekly_7dte", weekly_candidates), ("annual_365dte", annual_candidates)):
        chosen = [c for c in candidates.values() if c is not None]
        coverage_rows.append({
            "kind": kind, "entry_dates_tested": len(candidates), "entry_dates_with_candidate": len(chosen),
            "candidate_coverage_pct": 100 * len(chosen) / max(1, len(candidates)),
            "median_selected_delta": float(np.median([abs(c["delta"]) for c in chosen])) if chosen else None,
            "median_selected_dte": float(np.median([c["dte"] for c in chosen])) if chosen else None,
            "median_otm_pct": float(np.median([c["otm_pct"] for c in chosen])) if chosen else None,
            "median_entry_ask_per_share": float(np.median([c["ask"] for c in chosen])) if chosen else None,
            "median_entry_cost_per_contract_usd": float(np.median([c["ask"] * 100 for c in chosen])) if chosen else None,
            "median_spread_per_share": float(np.median([c["ask"] - c["bid"] for c in chosen])) if chosen else None,
            "median_volume": float(np.median([c["volume"] for c in chosen])) if chosen else None,
        })
    pd.DataFrame(coverage_rows).to_csv(out_dir / "candidate_coverage.csv", index=False)

    rows = []
    for si in starts:
        start_date = pd.Timestamp(underlying.iloc[si].date).normalize()
        end_idx = int(np.searchsorted(dates, np.datetime64((start_date + pd.DateOffset(years=10)).normalize()), side="right") - 1)
        if end_idx <= si:
            continue
        for strategy in ("spot_buy_hold", "weekly_5d_call", "annual_365d_call"):
            rows.append(_simulate_path(underlying, si, end_idx, weekly_candidates, annual_candidates, quotes, strategy))
    details = pd.DataFrame(rows)
    if details.empty:
        raise RuntimeError("No window results were produced")
    summary = summarise(details)
    details.to_csv(out_dir / "window_results.csv", index=False)
    summary.to_csv(out_dir / "aggregate_summary.csv", index=False)

    manifest = {
        "study_id": "QQQ_SPOT_VS_BUDGETED_LONG_CALLS_10Y_V1",
        "status": "OBSERVED_HISTORICAL_OPTION_BID_ASK_REPLAY",
        "source_commit": os.environ.get("GITHUB_SHA", "local"),
        "options_sha256": options_sha, "underlying_sha256": underlying_sha, "options_rows": option_rows,
        "options_date_min": opt_min.date().isoformat(), "options_date_max": opt_max.date().isoformat(),
        "underlying_common_date_min": pd.Timestamp(underlying.date.min()).date().isoformat(),
        "underlying_common_date_max": pd.Timestamp(underlying.date.max()).date().isoformat(),
        "complete_ten_year_windows": int(len(starts)), "start_stride_trading_sessions": WEEKLY_STEP_SESSIONS,
        "initial_capital_usd": CAPITAL_USD, "external_contributions_total_usd_per_strategy": CAPITAL_USD,
        "target_absolute_delta": TARGET_DELTA, "accepted_abs_delta_band": list(DELTA_ACCEPT_RANGE),
        "weekly_target_dte": WEEKLY_DTE_TARGET, "weekly_dte_band": list(WEEKLY_DTE_RANGE),
        "annual_target_dte": ANNUAL_DTE_TARGET, "annual_dte_band": list(ANNUAL_DTE_RANGE),
        "option_contract_multiplier": OPTION_MULTIPLIER,
        "cash_contribution_policy": "Weekly strategy contributes $7000 evenly over scheduled 5-session entries; annual strategy contributes $700 at each of ten yearly entry dates. Unspent cash and expired-option proceeds are carried forward; whole contracts only.",
        "entry_fill": "Observed ask on entry date",
        "exit_rule": "Hold to expiration, or to the 10-year window end if later; liquidate at last observed bid within five calendar days of cutoff. If no fresh bid, use underlying intrinsic value as a conservative fallback and count the fallback.",
        "option_fees": "Commissions and exchange fees excluded; entry ask and exit bid include quoted spread when observed.",
        "benchmark_price_mode": benchmark_mode,
        "quote_fallback_counts": {"observed_bid_exit_marks": int(details.observed_bid_exits.sum()),
                                  "intrinsic_fallback_exit_marks": int(details.intrinsic_fallback_exits.sum())},
        "limitations": [
            "Overlapping ten-year windows are highly correlated and are not independent observations.",
            "The $7000 spot benchmark is fully invested at the start; Call strategies deploy the same $7000 through contributions over ten years, so time with capital at risk differs by construction.",
            "Only listed whole contracts are purchased; unused cash is carried without interest. An entry occurs only when the accumulated cash can buy at least one contract at the observed ask.",
            "Call target is 5 absolute delta and OTM; realized Delta is the nearest available quote inside the fixed band, not exactly 0.05 each time.",
            "Commissions, taxes, borrowing costs and interest on uninvested cash are excluded."
        ],
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(_clean(manifest), indent=2, allow_nan=False), encoding="utf-8")
    md = [
        "# QQQ USD 7,000 Spot vs Budgeted Long Calls — Ten-Year Historical Study", "",
        f"- Status: {manifest['status']}",
        f"- Common sample: {manifest['underlying_common_date_min']} to {manifest['underlying_common_date_max']}",
        f"- Complete overlapping ten-year windows: {manifest['complete_ten_year_windows']}",
        f"- Options data SHA-256: {options_sha}", f"- Underlying data SHA-256: {underlying_sha}",
        "- Option pricing uses historical bid/ask quotes; no Black–Scholes option marks.",
        "", "## Fixed rules", "",
        "- QQQ spot: invest all $7,000 at the start and hold; adjusted close is used if available, otherwise price-only.",
        "- Weekly Call: contribute $7,000 evenly over 5-session entries; target 5-delta OTM Call, 7 DTE (5–10 allowed), hold to expiration.",
        "- Annual Call: contribute $700 at each of ten yearly entry dates; target 5-delta OTM Call, 365 DTE (330–400 allowed), hold to expiration.",
        "- Whole contracts only; cash and proceeds are carried forward without interest.",
        "- Fresh bid at exit; if unavailable within five days, use intrinsic value as a conservative fallback and count it.",
        "- Commissions and taxes excluded; observed bid/ask spread is included when quoted.",
        "", "## Entry quote coverage", "", pd.DataFrame(coverage_rows).to_string(index=False),
        "", "## Ten-year results", "", summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"),
        "", "## How to read this", "",
        "- Positive-window percentage means terminal account NAV exceeds the full $7,000 contribution budget.",
        "- XIRR uses actual contribution dates and terminal NAV; this is more appropriate than a simple ten-year CAGR for staggered contributions.",
        "- All-contract-payouts-zero is conditional on at least one contract having been bought.",
        "- Near-total-loss means terminal account NAV is at or below $70 (1% of total contributions).",
        "- The overlapping windows are not independent statistical trials.",
        "- The fully invested spot benchmark and the ten-year contribution-funded Call strategies have different capital-at-risk timing.",
        "", "## Provenance", "", f"- Workflow source commit: {manifest['source_commit']}",
        "- Hashes and exact coverage are in run_manifest.json.",
        "- window_results.csv has each window; aggregate_summary.csv has summary statistics; candidate_coverage.csv has option availability."
    ]
    (out_dir / "study_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"windows={len(starts)} option_rows={option_rows} selected_contracts={len(set(candidate_ids))}")
    print(f"output={out_dir.resolve()}")


if __name__ == "__main__":
    main()
