#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from pathlib import Path

FIELDS = [
    "trade_date","m1_symbol","m1_expiry","m1_settlement",
    "m2_symbol","m2_expiry","m2_settlement","term_slope","source","source_url"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    seen = {}
    for p in sorted(Path(a.input_dir).glob("**/part_*.csv")):
        with p.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                day = r.get("trade_date")
                if day:
                    seen[day] = r

    rows = [seen[k] for k in sorted(seen)]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(
        f"merged_rows={len(rows)} "
        f"first={rows[0]['trade_date'] if rows else None} "
        f"last={rows[-1]['trade_date'] if rows else None}"
    )

if __name__ == "__main__":
    main()
