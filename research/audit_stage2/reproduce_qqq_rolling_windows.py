#!/usr/bin/env python3
"""Reproduce historical 120-month QQQ rolling price-window diagnostics.

This is not a forward probability estimator or a total-return simulation. DCA assumes
1/120 of starting capital is invested at each monthly close, idle cash earns 0%, and
dividends, costs and taxes are excluded.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

HORIZON_MONTHS = 120

def load_month_ends(path: Path) -> list[tuple[dt.date, float]]:
    by_month: dict[tuple[int, int], tuple[dt.date, float]] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "Date" not in reader.fieldnames or "QQQ" not in reader.fieldnames:
            raise ValueError("Input CSV must contain Date and QQQ columns")
        for row in reader:
            try:
                date = dt.date.fromisoformat(row["Date"])
                price = float(row["QQQ"])
            except (TypeError, ValueError):
                continue
            if price > 0:
                by_month[(date.year, date.month)] = (date, price)
    points = sorted(by_month.values(), key=lambda p: p[0])
    if len(points) <= HORIZON_MONTHS:
        raise ValueError(f"Need more than {HORIZON_MONTHS} monthly observations; found {len(points)}")
    return points

def rolling_windows(points: list[tuple[dt.date, float]]) -> dict:
    rows = []
    for i in range(len(points) - HORIZON_MONTHS):
        start_date, start_px = points[i]
        end_date, end_px = points[i + HORIZON_MONTHS]
        lump_sum = end_px / start_px
        dca = sum((1.0 / HORIZON_MONTHS) * (end_px / points[i + j][1])
                  for j in range(HORIZON_MONTHS))
        rows.append({"start": start_date.isoformat(), "end": end_date.isoformat(),
                     "lump_sum_terminal_multiple": lump_sum,
                     "clock_dca_terminal_multiple": dca})
    def summarize(field: str) -> dict:
        vals = [row[field] for row in rows]
        worst = min(rows, key=lambda row: row[field])
        losers = [row for row in rows if row[field] < 1.0]
        return {"windows": len(vals), "nonloss_windows": len(vals) - len(losers),
                "loss_windows": len(losers),
                "historical_nonloss_fraction": (len(vals) - len(losers)) / len(vals),
                "worst_window": {k: worst[k] for k in ("start", "end", field)},
                "worst_terminal_value_from_100k_usd": 100000 * worst[field]}
    return {"horizon_months": HORIZON_MONTHS, "monthly_observations": len(points),
            "first_month_end": points[0][0].isoformat(),
            "last_observation": points[-1][0].isoformat(),
            "window_definition": "monthly start i through endpoint i+120; DCA purchases at i..i+119",
            "assumptions": {"price_series_only": True, "dividends_reinvested": False,
                            "cash_yield_during_dca": 0.0, "transaction_costs_and_taxes": 0.0,
                            "overlapping_windows_are_dependent": True},
            "lump_sum": summarize("lump_sum_terminal_multiple"),
            "clock_dca": summarize("clock_dca_terminal_multiple"), "rows": rows}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV with Date and QQQ columns")
    parser.add_argument("--out", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    points = load_month_ends(args.csv_path)
    result = rolling_windows(points)
    result["input_path"] = args.csv_path.as_posix()
    result["input_sha256"] = hashlib.sha256(args.csv_path.read_bytes()).hexdigest()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
