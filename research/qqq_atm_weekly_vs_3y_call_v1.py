#!/usr/bin/env python3
"""Observed-quote comparison of QQQ spot, weekly ATM calls, and actual ~3Y calls.

No Delta screen and no synthetic/Black-Scholes option marks. Research only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

CAPITAL = 7000.0
MULTIPLIER = 100
WEEK_STEP = 5
WEEKLY_DTE = (5, 10)
WEEKLY_TARGET = 7
THREE_YEAR_DTE = (900, 1200)
THREE_YEAR_TARGET = 1095
QUOTE_MAX_AGE_DAYS = 5
NEAR_TOTAL_LOSS = CAPITAL * 0.01
OPTIONS_SHA = "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734"
UNDERLYING_SHA = "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_underlying(path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path)
    x.columns = [str(c).strip().lower().replace(" ", "_") for c in x.columns]
    if "date" not in x or "close" not in x:
        raise ValueError(f"Underlying needs date and close columns, found {list(x.columns)}")
    dates = pd.to_datetime(x["date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_localize(None)
    x["date"] = dates.dt.normalize()
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    adj = next((c for c in ("adjclose", "adj_close", "adjusted_close", "adjustedclose") if c in x.columns), None)
    x["benchmark_price"] = pd.to_numeric(x[adj], errors="coerce") if adj else x["close"]
    x["benchmark_price"] = x["benchmark_price"].where(x["benchmark_price"] > 0, x["close"])
    x = x.dropna(subset=["date", "close", "benchmark_price"])
    x = x[(x["close"] > 0) & (x["benchmark_price"] > 0)]
    x = x.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return x


def option_bounds(path: Path):
    con = duckdb.connect()
    try:
        row = con.execute(
            "SELECT MIN(CAST(date AS DATE)), MAX(CAST(date AS DATE)), "
            "MIN(CAST(expiration AS DATE)), MAX(CAST(expiration AS DATE)), COUNT(*) "
            "FROM read_parquet(?)", [str(path)]
        ).fetchone()
    finally:
        con.close()
    return pd.Timestamp(row[0]), pd.Timestamp(row[1]), pd.Timestamp(row[2]), pd.Timestamp(row[3]), int(row[4])


def date_index(dates: np.ndarray, target: pd.Timestamp, side: str = "left"):
    i = int(np.searchsorted(dates, np.datetime64(pd.Timestamp(target).normalize()), side=side))
    return i if i < len(dates) else None


def window_starts(underlying: pd.DataFrame, years: int) -> list[int]:
    max_date = pd.Timestamp(underlying.iloc[-1]["date"]).normalize()
    out = []
    for i, raw in enumerate(underlying["date"]):
        if pd.Timestamp(raw).normalize() + pd.DateOffset(years=years) <= max_date:
            out.append(i)
        else:
            break
    return out[::WEEK_STEP]


def make_weekly_dates(underlying: pd.DataFrame, starts: list[int], years: int) -> tuple[list[pd.Timestamp], dict[int, int]]:
    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    events = set()
    end_indices = {}
    for si in starts:
        start = pd.Timestamp(underlying.iloc[si]["date"]).normalize()
        anniversary = start + pd.DateOffset(years=years)
        ei = int(np.searchsorted(dates, np.datetime64(anniversary.normalize()), side="right") - 1)
        if ei <= si:
            continue
        end_indices[si] = ei
        for ix in range(si, ei, WEEK_STEP):
            events.add(pd.Timestamp(underlying.iloc[ix]["date"]).normalize())
    return sorted(events), end_indices


def read_chains(path: Path, entry_dates: list[pd.Timestamp], dte_range: tuple[int, int]) -> pd.DataFrame:
    day_list = sorted({pd.Timestamp(d).date() for d in entry_dates})
    if not day_list:
        return pd.DataFrame()
    lo, hi = dte_range
    sql = f"""
        SELECT CAST(date AS DATE) AS date, CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id, CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
               CAST(delta AS DOUBLE) AS delta, COALESCE(CAST(volume AS DOUBLE), 0.0) AS volume
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER(CAST("type" AS VARCHAR)) = 'CALL'
          AND date IS NOT NULL AND expiration IS NOT NULL AND contract_id IS NOT NULL
          AND strike IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL
          AND CAST(bid AS DOUBLE) >= 0 AND CAST(ask AS DOUBLE) > 0
          AND CAST(ask AS DOUBLE) >= CAST(bid AS DOUBLE)
          AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE) + INTERVAL {lo} DAY
              AND CAST(date AS DATE) + INTERVAL {hi} DAY
    """
    con = duckdb.connect()
    try:
        out = con.execute(sql, [str(path), day_list]).df()
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
    return out.dropna(subset=["date", "expiration", "strike", "bid", "ask", "dte"])


def pick_atm_candidate(chain: pd.DataFrame | None, entry_date, spot: float, kind: str):
    """No Delta restriction: prefer target DTE, then nearest strike to spot (ATM)."""
    if chain is None or chain.empty:
        return None
    if kind == "weekly":
        lo, hi, target = *WEEKLY_DTE, WEEKLY_TARGET
    elif kind == "three_year":
        lo, hi, target = *THREE_YEAR_DTE, THREE_YEAR_TARGET
    else:
        raise ValueError(f"Unknown kind: {kind}")
    d = pd.Timestamp(entry_date).normalize()
    g = chain[chain["date"].eq(d)].copy()
    g = g[(g["dte"] >= lo) & (g["dte"] <= hi) & (g["ask"] > 0) &
          (g["bid"] >= 0) & (g["ask"] >= g["bid"])]
    if g.empty:
        return None
    g["dte_error"] = (g["dte"] - target).abs()
    g["moneyness_error"] = (g["strike"] / float(spot) - 1.0).abs()
    g["spread"] = g["ask"] - g["bid"]
    g = g.sort_values(
        ["dte_error", "moneyness_error", "spread", "volume", "ask"],
        ascending=[True, True, True, False, True], kind="mergesort"
    )
    r = g.iloc[0]
    return {
        "entry_date": d, "expiration": pd.Timestamp(r["expiration"]).normalize(),
        "contract_id": str(r["contract_id"]), "strike": float(r["strike"]),
        "delta": float(r["delta"]) if pd.notna(r["delta"]) else None,
        "dte": int(r["dte"]), "bid": float(r["bid"]), "ask": float(r["ask"]),
        "volume": float(r["volume"]) if pd.notna(r["volume"]) else 0.0,
        "spot": float(spot), "otm_pct": float(r["strike"]) / float(spot) - 1.0,
        "spread": float(r["spread"]),
    }


def read_contract_quotes(path: Path, ids: list[str]) -> dict[str, dict]:
    unique = sorted(set(str(v) for v in ids if v is not None))
    if not unique:
        return {}
    sql = """
      SELECT CAST(date AS DATE) AS date, CAST(contract_id AS VARCHAR) AS contract_id,
             CAST(bid AS DOUBLE) AS bid
      FROM read_parquet(?)
      WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
        AND date IS NOT NULL AND bid IS NOT NULL AND CAST(bid AS DOUBLE) >= 0
      ORDER BY CAST(contract_id AS VARCHAR), CAST(date AS DATE)
    """
    con = duckdb.connect()
    try:
        q = con.execute(sql, [str(path), unique]).df()
    finally:
        con.close()
    if q.empty:
        return {}
    q["date"] = pd.to_datetime(q["date"]).dt.normalize()
    q["contract_id"] = q["contract_id"].astype(str)
    return {
        str(cid): {
            "dates": group.sort_values("date").drop_duplicates("date")["date"].to_numpy(dtype="datetime64[ns]"),
            "bid": group.sort_values("date").drop_duplicates("date")["bid"].to_numpy(dtype=float),
        }
        for cid, group in q.groupby("contract_id", sort=False)
    }


def spot_on_or_before(underlying: pd.DataFrame, target: pd.Timestamp) -> tuple[float, pd.Timestamp]:
    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    i = int(np.searchsorted(dates, np.datetime64(pd.Timestamp(target).normalize()), side="right") - 1)
    if i < 0:
        raise ValueError(f"No QQQ bar on/before {target}")
    return float(underlying.iloc[i]["close"]), pd.Timestamp(underlying.iloc[i]["date"])


def size_contracts(cash: float, ask: float) -> int:
    cost = float(ask) * MULTIPLIER
    if not math.isfinite(cost) or cost <= 0 or cash + 1e-9 < cost:
        return 0
    return max(0, int(math.floor((cash + 1e-9) / cost)))


def mark_position(pos: dict, target: pd.Timestamp, quotes: dict[str, dict], underlying: pd.DataFrame):
    expiry, target = pd.Timestamp(pos["expiration"]).normalize(), pd.Timestamp(target).normalize()
    cut = min(expiry, target)
    if target >= expiry:
        spot, actual = spot_on_or_before(underlying, expiry)
        return max(spot - float(pos["strike"]), 0.0) * MULTIPLIER * int(pos["qty"]), "EXPIRY_INTRINSIC"
    q = quotes.get(str(pos["contract_id"]))
    if q is not None and len(q["dates"]):
        j = int(np.searchsorted(q["dates"], np.datetime64(cut), side="right") - 1)
        entry_np = np.datetime64(pd.Timestamp(pos["entry_date"]).normalize())
        while j >= 0 and q["dates"][j] <= entry_np:
            j -= 1
        if j >= 0:
            qdate = pd.Timestamp(q["dates"][j]).normalize()
            age = int((cut - qdate).days)
            if 0 <= age <= QUOTE_MAX_AGE_DAYS:
                return max(float(q["bid"][j]), 0.0) * MULTIPLIER * int(pos["qty"]), "OBSERVED_BID"
    spot, actual = spot_on_or_before(underlying, cut)
    return max(spot - float(pos["strike"]), 0.0) * MULTIPLIER * int(pos["qty"]), "INTRINSIC_FALLBACK"


def simulate_weekly(underlying, start_idx: int, end_idx: int, candidates: dict, quotes: dict, label: str) -> dict:
    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    start = pd.Timestamp(underlying.iloc[start_idx]["date"]).normalize()
    end = pd.Timestamp(underlying.iloc[end_idx]["date"]).normalize()
    event_indices = list(range(start_idx, end_idx, WEEK_STEP))
    per_entry = CAPITAL / max(len(event_indices), 1)
    cash, positions, premium_paid, bought, misses, payouts = 0.0, [], 0.0, 0, 0, 0.0
    expired_count = worthless_count = 0
    for ix in event_indices:
        day = pd.Timestamp(underlying.iloc[ix]["date"]).normalize()
        still_open = []
        for pos in positions:
            if pd.Timestamp(pos["expiration"]).normalize() <= day:
                value, source = mark_position(pos, pos["expiration"], quotes, underlying)
                cash += value
                payouts += value
                expired_count += int(pos["qty"])
                if value <= 1e-8:
                    worthless_count += int(pos["qty"])
            else:
                still_open.append(pos)
        positions = still_open
        cash += per_entry
        cand = candidates.get(day)
        if cand is None:
            misses += 1
            continue
        qty = size_contracts(cash, cand["ask"])
        if qty <= 0:
            misses += 1
            continue
        cost = float(cand["ask"]) * MULTIPLIER * qty
        cash -= cost
        premium_paid += cost
        bought += qty
        positions.append({**cand, "qty": qty, "entry_date": day})
    for pos in positions:
        value, source = mark_position(pos, end, quotes, underlying)
        cash += value
        payouts += value
        if pd.Timestamp(pos["expiration"]).normalize() <= end:
            expired_count += int(pos["qty"])
            if value <= 1e-8:
                worthless_count += int(pos["qty"])
    terminal = max(float(cash), 0.0)
    return {
        "strategy": label, "start_date": start.date().isoformat(), "end_date": end.date().isoformat(),
        "terminal_nav_usd": terminal, "profit_usd": terminal - CAPITAL,
        "total_return_pct": terminal / CAPITAL - 1.0, "premium_paid_usd": premium_paid,
        "contracts_bought": bought, "entry_events": len(event_indices), "candidate_or_cash_misses": misses,
        "expired_contracts": expired_count, "expired_worthless_contracts": worthless_count,
        "any_contracts_bought": bought > 0, "near_total_loss": terminal <= NEAR_TOTAL_LOSS,
        "exit_payout_usd": payouts,
    }


def simulate_three_year_call(underlying, start_idx: int, end_idx: int, candidate: dict, quotes: dict) -> dict:
    start = pd.Timestamp(underlying.iloc[start_idx]["date"]).normalize()
    end = pd.Timestamp(underlying.iloc[end_idx]["date"]).normalize()
    cash = CAPITAL
    qty = size_contracts(cash, candidate["ask"])
    cost = float(candidate["ask"]) * MULTIPLIER * qty
    cash -= cost
    if qty:
        pos = {**candidate, "qty": qty, "entry_date": start}
        value, source = mark_position(pos, end, quotes, underlying)
    else:
        value, source = 0.0, "NO_AFFORDABLE_CONTRACT"
    terminal = max(cash + value, 0.0)
    return {
        "strategy": "three_year_atm_call_if_quoted", "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(), "candidate_available": True, "contract_id": candidate["contract_id"],
        "strike": candidate["strike"], "entry_dte": candidate["dte"], "entry_delta_observed": candidate["delta"],
        "entry_ask_per_share": candidate["ask"], "contracts_bought": qty, "premium_paid_usd": cost,
        "exit_source": source, "terminal_nav_usd": terminal, "profit_usd": terminal - CAPITAL,
        "total_return_pct": terminal / CAPITAL - 1.0, "near_total_loss": terminal <= NEAR_TOTAL_LOSS,
    }


def spot_result(underlying, start_idx: int, end_idx: int, label: str) -> dict:
    start = pd.Timestamp(underlying.iloc[start_idx]["date"]).normalize()
    end = pd.Timestamp(underlying.iloc[end_idx]["date"]).normalize()
    p0, p1 = float(underlying.iloc[start_idx]["benchmark_price"]), float(underlying.iloc[end_idx]["benchmark_price"])
    nav = CAPITAL * p1 / p0
    return {
        "strategy": label, "start_date": start.date().isoformat(), "end_date": end.date().isoformat(),
        "terminal_nav_usd": nav, "profit_usd": nav - CAPITAL, "total_return_pct": nav / CAPITAL - 1.0,
        "premium_paid_usd": 0.0, "contracts_bought": 0, "candidate_or_cash_misses": 0,
        "any_contracts_bought": False, "near_total_loss": nav <= NEAR_TOTAL_LOSS,
    }


def summarise(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, g in frame.groupby("strategy", sort=False):
        rows.append({
            "strategy": strategy, "windows": len(g),
            "mean_terminal_nav_usd": g["terminal_nav_usd"].mean(),
            "median_terminal_nav_usd": g["terminal_nav_usd"].median(),
            "p10_terminal_nav_usd": g["terminal_nav_usd"].quantile(.10),
            "p90_terminal_nav_usd": g["terminal_nav_usd"].quantile(.90),
            "mean_profit_usd": g["profit_usd"].mean(),
            "median_profit_usd": g["profit_usd"].median(),
            "positive_window_pct": (g["profit_usd"] > 0).mean() * 100,
            "ending_below_7000_pct": (g["terminal_nav_usd"] < CAPITAL).mean() * 100,
            "near_total_loss_pct": g["near_total_loss"].astype(bool).mean() * 100,
            "median_contracts_bought": g["contracts_bought"].median() if "contracts_bought" in g else np.nan,
            "median_premium_paid_usd": g["premium_paid_usd"].median() if "premium_paid_usd" in g else np.nan,
            "median_candidate_or_cash_misses": g["candidate_or_cash_misses"].median() if "candidate_or_cash_misses" in g else np.nan,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="research/qqq_atm_weekly_vs_3y_call_v1/results/latest")
    ap.add_argument("--verify-pinned-hashes", action="store_true")
    args = ap.parse_args()
    data_dir, out = Path(args.data_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    opt_path, und_path = data_dir / "QQQ_options.parquet", data_dir / "QQQ_underlying.parquet"
    if not opt_path.exists() or not und_path.exists():
        raise FileNotFoundError("Expected QQQ_options.parquet and QQQ_underlying.parquet")
    opt_sha, und_sha = sha256_file(opt_path), sha256_file(und_path)
    if args.verify_pinned_hashes and (opt_sha != OPTIONS_SHA or und_sha != UNDERLYING_SHA):
        raise RuntimeError(f"Pinned data hash mismatch: options={opt_sha}, underlying={und_sha}")
    underlying = load_underlying(und_path)
    opt_min, opt_max, exp_min, exp_max, option_rows = option_bounds(opt_path)
    underlying = underlying[(underlying["date"] >= opt_min) & (underlying["date"] <= opt_max)].reset_index(drop=True)
    if len(underlying) < 2520:
        raise RuntimeError("Common underlying/options window is not long enough for 10-year windows")
    dates = underlying["date"].to_numpy(dtype="datetime64[ns]")
    starts10, starts3 = window_starts(underlying, 10), window_starts(underlying, 3)
    weekly_dates10, end10 = make_weekly_dates(underlying, starts10, 10)
    weekly_dates3, end3 = make_weekly_dates(underlying, starts3, 3)
    all_weekly_dates = sorted(set(weekly_dates10) | set(weekly_dates3))
    start3_dates = [pd.Timestamp(underlying.iloc[ix]["date"]).normalize() for ix in starts3]
    close_by_date = underlying.set_index("date")["close"].to_dict()
    week_chains = read_chains(opt_path, all_weekly_dates, WEEKLY_DTE)
    long_chains = read_chains(opt_path, start3_dates, THREE_YEAR_DTE)

    def candidate_map(chains, entry_dates, kind):
        by_date = {pd.Timestamp(d): g for d, g in chains.groupby("date", sort=False)} if not chains.empty else {}
        result = {}
        for d in entry_dates:
            spot = close_by_date.get(pd.Timestamp(d))
            result[pd.Timestamp(d)] = pick_atm_candidate(by_date.get(pd.Timestamp(d)), d, float(spot), kind) if spot else None
        return result

    weekly_candidates = candidate_map(week_chains, all_weekly_dates, "weekly")
    long_candidates = candidate_map(long_chains, start3_dates, "three_year")
    ids = [c["contract_id"] for c in list(weekly_candidates.values()) + list(long_candidates.values()) if c]
    quotes = read_contract_quotes(opt_path, ids)

    coverage = []
    for kind, candidates in (("weekly_atm_5_10dte", weekly_candidates), ("three_year_atm_900_1200dte", long_candidates)):
        chosen = [x for x in candidates.values() if x is not None]
        coverage.append({
            "kind": kind, "entry_dates_tested": len(candidates), "entry_dates_with_candidate": len(chosen),
            "coverage_pct": 100 * len(chosen) / max(1, len(candidates)),
            "median_observed_abs_delta_not_used_for_selection": float(np.median([abs(c["delta"]) for c in chosen if c["delta"] is not None])) if any(c["delta"] is not None for c in chosen) else None,
            "median_selected_dte": float(np.median([c["dte"] for c in chosen])) if chosen else None,
            "median_strike_vs_spot_pct": float(np.median([c["otm_pct"] for c in chosen]) * 100) if chosen else None,
            "median_entry_ask_per_share": float(np.median([c["ask"] for c in chosen])) if chosen else None,
            "median_entry_cost_per_contract_usd": float(np.median([c["ask"] * MULTIPLIER for c in chosen])) if chosen else None,
            "median_spread_per_share": float(np.median([c["spread"] for c in chosen])) if chosen else None,
            "median_volume": float(np.median([c["volume"] for c in chosen])) if chosen else None,
        })
    pd.DataFrame(coverage).to_csv(out / "entry_quote_coverage.csv", index=False)

    rows10 = []
    for si in starts10:
        ei = end10.get(si)
        if ei is None:
            continue
        rows10.append(spot_result(underlying, si, ei, "qqq_spot_buy_hold_10y"))
        rows10.append(simulate_weekly(underlying, si, ei, weekly_candidates, quotes, "weekly_atm_call_10y"))
    df10 = pd.DataFrame(rows10)
    df10.to_csv(out / "ten_year_window_results.csv", index=False)
    summarise(df10).to_csv(out / "ten_year_aggregate_summary.csv", index=False)

    rows3 = []
    for si in starts3:
        ei = end3.get(si)
        if ei is None:
            continue
        rows3.append(spot_result(underlying, si, ei, "qqq_spot_buy_hold_3y"))
        rows3.append(simulate_weekly(underlying, si, ei, weekly_candidates, quotes, "weekly_atm_call_3y"))
        d = pd.Timestamp(underlying.iloc[si]["date"]).normalize()
        candidate = long_candidates.get(d)
        if candidate is not None:
            rows3.append(simulate_three_year_call(underlying, si, ei, candidate, quotes))
    df3 = pd.DataFrame(rows3)
    df3.to_csv(out / "three_year_window_results.csv", index=False)
    summ3 = summarise(df3)
    summ3.to_csv(out / "three_year_aggregate_summary.csv", index=False)

    candidate_rows = [r for r in coverage if r["kind"] == "three_year_atm_900_1200dte"][0]
    report = [
        "# QQQ ATM Weekly Calls vs Actual Three-Year Long Calls",
        "",
        "- Pricing status: historical observed option bid/ask quotes only; no Black–Scholes imputation.",
        f"- Source sample: {underlying['date'].min().date()} to {underlying['date'].max().date()}.",
        f"- Ten-year overlapping windows: {len(starts10)}; three-year overlapping windows: {len(starts3)}.",
        f"- Pinned option rows: {option_rows:,}; options-date range {opt_min.date()} to {opt_max.date()}; latest expiration date in file {exp_max.date()}.",
        "",
        "## Exact rules",
        "",
        "- Weekly Call: $7,000 total contributions spread evenly over every fifth trading session of each window. Pick the listed Call with DTE closest to 7 within 5–10 calendar days, then strike closest to QQQ spot (ATM); Delta is not an entry filter.",
        "- Whole contracts only; buy at observed Ask. Unspent cash and proceeds are carried forward at 0% interest, so a weekly allocation too small to buy one contract accumulates rather than being spent at a fictional fractional-contract price.",
        "- All weekly Calls are held to expiration; expired contracts settle at intrinsic value from the QQQ close on or before expiration. At a window's final date, a still-live option uses a fresh observed bid within five calendar days, otherwise intrinsic fallback.",
        "- Three-year Call: spend up to $7,000 at the start of a three-year window on the ATM Call whose listed expiry is closest to 1,095 DTE within 900–1,200 DTE; buy at observed Ask and hold to the three-year window end/option expiration. It is only summarized for windows with an actual eligible listed contract. This is a single upfront premium budget, not a recurring contribution strategy.",
        "- QQQ spot benchmark invests the full $7,000 at the start. The stock and option strategies therefore have different capital-at-risk timing; read them as distinct budget deployment methods.",
        "- No commissions, taxes, or cash interest. Historical quotes and volume do not guarantee executable fills.",
        "",
        "## Quote coverage",
        "",
        pd.DataFrame(coverage).to_markdown(index=False),
        "",
        "## Ten-year results",
        "",
        df10.groupby("strategy", sort=False).apply(lambda g: pd.Series({
            "windows": len(g), "mean_terminal_nav_usd": g["terminal_nav_usd"].mean(),
            "median_terminal_nav_usd": g["terminal_nav_usd"].median(),
            "median_profit_usd": g["profit_usd"].median(),
            "positive_window_pct": (g["profit_usd"] > 0).mean() * 100,
            "ending_below_7000_pct": (g["terminal_nav_usd"] < CAPITAL).mean() * 100,
            "near_total_loss_pct": g["near_total_loss"].mean() * 100,
            "median_premium_paid_usd": g["premium_paid_usd"].median() if "premium_paid_usd" in g else 0,
            "median_contracts_bought": g["contracts_bought"].median() if "contracts_bought" in g else 0,
        })).reset_index().to_markdown(index=False),
        "",
        "## Three-year results",
        "",
        summ3.to_markdown(index=False),
        "",
    ]
    if int(candidate_rows["entry_dates_with_candidate"]) == 0:
        report += [
            "**Important:** No actual listed QQQ Calls were found in the configured 900–1,200 DTE band at the sampled entry dates. Therefore no three-year Call return is reported; this study does not invent a synthetic three-year option price.",
            "",
        ]
    elif float(candidate_rows["coverage_pct"]) < 50:
        report += [
            "**Coverage warning:** Actual three-year Call quotes are only available on a subset of sampled entry dates. The three-year-call summary is conditioned on windows with a real eligible quote and is not directly comparable to the full-window spot/weekly results.",
            "",
        ]
    report += [
        "## Interpretation limits",
        "",
        "- Overlapping windows are highly correlated, not independent trials.",
        "- ATM means closest listed strike to spot on the selected expiry; it does not mean an exact 0.50 Delta. Selected Delta is reported only as an observed diagnostic.",
        "- The three-year Call results, when available, are conditional on observed listed quotes and should not be generalized to dates with no eligible contract.",
        "",
    ]
    (out / "study_report.md").write_text("\n".join(report), encoding="utf-8")
    manifest = {
        "study_id": "QQQ_ATM_WEEKLY_VS_ACTUAL_3Y_CALL_V1",
        "status": "OBSERVED_HISTORICAL_OPTION_BID_ASK_REPLAY",
        "options_sha256": opt_sha, "underlying_sha256": und_sha,
        "options_rows": option_rows, "options_date_min": opt_min.date().isoformat(),
        "options_date_max": opt_max.date().isoformat(), "options_expiration_max": exp_max.date().isoformat(),
        "common_underlying_date_min": underlying["date"].min().date().isoformat(),
        "common_underlying_date_max": underlying["date"].max().date().isoformat(),
        "ten_year_windows": len(starts10), "three_year_windows": len(starts3),
        "capital_usd": CAPITAL, "weekly_contribution_policy": "7000 USD evenly contributed on every 5th trading session over each tested window; unused cash and proceeds roll forward at 0% interest",
        "weekly_contract_selection": "DTE nearest 7 inside 5-10 days, then strike closest to spot; no Delta filter; observed Ask fills",
        "three_year_contract_selection": "DTE nearest 1095 inside 900-1200 days, then strike closest to spot; observed Ask; upfront 7000 USD budget",
        "quote_coverage": coverage,
        "caveats": ["overlapping windows are not independent", "no commissions/taxes/cash interest", "historical quotes/volume are not guaranteed fills", "three-year results only on actual eligible listed quotes"]
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Done: {len(starts10)} ten-year and {len(starts3)} three-year windows")
    print(pd.DataFrame(coverage).to_string(index=False))
    print(summarise(df10).to_string(index=False))
    print(summ3.to_string(index=False))


if __name__ == "__main__":
    main()
