#!/usr/bin/env python3
"""
Validate Cboe-derived M1/M2 against the previously observed 2016-2022 archive.
This is a data gate only. It does not change policy or P&L.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, json
from pathlib import Path

def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def f(x):
    try:
        return float(x)
    except Exception:
        return None

def d(x):
    return dt.date.fromisoformat(x)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cboe", required=True)
    ap.add_argument("--external", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cboe = {r["trade_date"]: r for r in read_rows(a.cboe) if r.get("trade_date")}
    ext = {}
    for r in read_rows(a.external):
        day = r.get("Date") or r.get("date") or r.get("trade_date")
        if day:
            ext[day] = r

    common = sorted(set(cboe) & set(ext))
    diffs, sign_mismatch, expiry_violations = [], 0, 0

    for day in common:
        cr, er = cboe[day], ext[day]
        vals = [f(cr["m1_settlement"]), f(cr["m2_settlement"]), f(er.get("M1")), f(er.get("M2"))]
        if any(v is None for v in vals):
            continue
        m1c, m2c, m1e, m2e = vals
        diffs.append((day, abs(m1c-m1e), abs(m2c-m2e), m1c, m1e, m2c, m2e))
        if (m2c - m1c) * (m2e - m1e) < 0:
            sign_mismatch += 1
        if (
            d(cr["m1_expiry"]) <= d(day)
            or d(cr["m2_expiry"]) <= d(day)
            or d(cr["m2_expiry"]) <= d(cr["m1_expiry"])
        ):
            expiry_violations += 1

    def pct(n, den):
        return 100 * n / den if den else None

    within_001 = sum(1 for x in diffs if x[1] <= 0.01 and x[2] <= 0.01)
    within_010 = sum(1 for x in diffs if x[1] <= 0.10 and x[2] <= 0.10)

    result = {
        "status": "PASS" if (
            len(common) >= 900
            and len(diffs) >= 900
            and pct(within_010, len(diffs)) >= 99.0
            and pct(sign_mismatch, len(diffs)) <= 1.0
            and expiry_violations == 0
        ) else "FAIL",
        "cboe_rows": len(cboe),
        "external_rows": len(ext),
        "common_dates": len(common),
        "compared": len(diffs),
        "within_0.01_dollars_pct": pct(within_001, len(diffs)),
        "within_0.10_dollars_pct": pct(within_010, len(diffs)),
        "slope_sign_mismatch_pct": pct(sign_mismatch, len(diffs)),
        "expiry_violations": expiry_violations,
        "worst_5": sorted(diffs, key=lambda x: max(x[1], x[2]), reverse=True)[:5],
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    Path(a.out).write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    if result["status"] != "PASS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
