#!/usr/bin/env python3
"""Diagnose a scheduled QQQ/SPY CALL entry date using the pinned option-chain cache."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import alternating_qqq_spy_call_cycle_v1 as call
import qqq_spy_put_premium_matched_phase_v1 as base


def load_day(symbol: str, day: str, cache: Path):
    year = int(day[:4])
    path, integrity = base.download_verified(symbol, year, cache)
    stats = {"chain_dates": 0, "call_rows": 0, "last_chain_date": None}
    found = []
    for d, rows in call.iter_call_symbol_days([path], symbol, day, day, stats):
        if d == day:
            found = rows
            break
    return found, integrity, stats


def describe(symbol: str, rows: list[dict], day: str):
    counts = Counter()
    by_expiry = defaultdict(Counter)
    signed_samples = []
    for row in rows:
        counts["raw_call_rows"] += 1
        if not call.standard_call_identity(row, symbol):
            counts["invalid_occ_or_identity"] += 1
            continue
        counts["valid_call_identity"] += 1
        expiry = base.as_day(row.get("expiration"))
        try:
            dte = (date.fromisoformat(expiry) - date.fromisoformat(day)).days
        except ValueError:
            counts["invalid_expiry"] += 1
            continue
        if not call.DTE_MIN <= dte <= call.DTE_MAX:
            counts["outside_dte_window"] += 1
            continue
        counts["inside_dte_window"] += 1
        by_expiry[expiry]["inside_dte_window"] += 1
        if not base.valid_quote(row):
            counts["invalid_quote"] += 1
            by_expiry[expiry]["invalid_quote"] += 1
            continue
        counts["valid_quote"] += 1
        by_expiry[expiry]["valid_quote"] += 1
        strike = base.num(row.get("strike"))
        delta = base.num(row.get("delta"))
        if strike is None or strike <= 0:
            counts["invalid_strike"] += 1
            continue
        ask_size = base.displayed_size(row, "ask")
        if ask_size >= call.LONG_QTY:
            counts["long_ask_eligible"] += 1
            by_expiry[expiry]["long_ask_eligible"] += 1
        if not base.valid_quote(row, require_positive_bid=True):
            counts["short_bid_invalid"] += 1
            continue
        counts["positive_bid"] += 1
        if delta is None:
            counts["delta_missing"] += 1
            continue
        counts["negative_delta"] += int(delta < 0)
        counts["positive_delta"] += int(delta > 0)
        if not base.DELTA_MIN <= abs(delta) <= base.DELTA_MAX:
            counts["short_delta_magnitude_outside_10_50"] += 1
            continue
        counts["short_delta_magnitude_in_band"] += 1
        by_expiry[expiry]["short_delta_magnitude_in_band"] += 1
        if base.displayed_size(row, "bid") < call.SHORT_QTY:
            counts["short_bid_size_lt_6"] += 1
            continue
        counts["short_leg_eligible_by_abs_delta"] += 1
        by_expiry[expiry]["short_leg_eligible_by_abs_delta"] += 1
        if len(signed_samples) < 12:
            signed_samples.append({
                "contract_id": base.normalized_contract_id(row),
                "expiry": expiry, "strike": strike, "delta_raw": delta,
                "bid": float(row["bid"]), "bid_size": base.displayed_size(row, "bid"),
            })
    return {
        "symbol": symbol,
        "rows": dict(counts),
        "expiries": {k: dict(v) for k, v in sorted(by_expiry.items())},
        "sample_rows": signed_samples,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default="2019-02-14")
    p.add_argument("--qqq-cache", default=str(Path.home() / ".cache" / "qqq-options-full-history"))
    p.add_argument("--spy-cache", default=str(Path.home() / ".cache" / "spy-options-cross-put-v1"))
    args = p.parse_args()
    date.fromisoformat(args.date)
    rows, integrity, stats = {}, {}, {}
    for symbol, cache_name in (("QQQ", args.qqq_cache), ("SPY", args.spy_cache)):
        rows[symbol], integrity[symbol], stats[symbol] = load_day(symbol, args.date, Path(cache_name))
    q, s = rows["QQQ"], rows["SPY"]
    results = {}
    for direction, short_symbol, long_symbol in (("A", "SPY", "QQQ"), ("B", "QQQ", "SPY")):
        short_rows, long_rows = rows[short_symbol], rows[long_symbol]
        pair = call.choose_contract_pair(short_rows, long_rows, short_symbol, long_symbol,
                                         args.date, 1.0, 1.0)
        short_desc = describe(short_symbol, short_rows, args.date)
        long_desc = describe(long_symbol, long_rows, args.date)
        short_exp = set(short_desc["expiries"])
        long_exp = set(long_desc["expiries"])
        common_exp = sorted(short_exp & long_exp)
        eligible_common = [
            expiry for expiry in common_exp
            if short_desc["expiries"][expiry].get("short_leg_eligible_by_abs_delta", 0) > 0
            and long_desc["expiries"][expiry].get("long_ask_eligible", 0) > 0
        ]
        results[direction] = {
            "short_symbol": short_symbol, "long_symbol": long_symbol,
            "selected_pair": pair,
            "common_expiries": common_exp,
            "common_expiries_with_eligible_legs": eligible_common,
            "short_leg": short_desc,
            "long_leg": long_desc,
        }
    print(json.dumps({
        "date": args.date,
        "source_commit": base.SOURCE_COMMIT,
        "integrity": integrity,
        "day_scan_stats": stats,
        "directions": results,
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
