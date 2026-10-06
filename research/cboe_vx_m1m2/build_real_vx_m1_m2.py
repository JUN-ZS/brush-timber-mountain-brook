#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{expiry}.csv"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Original-Hybrid-research"
MONTHS = "FGHJKMNQUVXZ"

def third_friday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 15)
    while d.weekday() != 4:
        d += dt.timedelta(days=1)
    return d

def standard_vx_expiry_candidates(year: int, month: int) -> list[dt.date]:
    # VX standard expiry is normally Wednesday, 30 days before the third Friday.
    # Cboe has holiday shifts; try the adjacent Tuesday as well. We validate
    # candidates by HTTP existence, never by assuming the calendar.
    target = third_friday(year, month) - dt.timedelta(days=30)
    candidates = []
    for delta in range(-2, 3):
        d = target + dt.timedelta(days=delta)
        if d.weekday() in (1, 2, 3):  # Tue/Wed/Thu
            candidates.append(d)
    return candidates

def candidate_expiries(start: dt.date, end: dt.date) -> list[dt.date]:
    # Include one month of warm-up before the requested start and two after end.
    y, m = start.year, start.month
    first = dt.date(y, m, 1)
    first -= dt.timedelta(days=62)
    last = dt.date(end.year, end.month, 1)
    last += dt.timedelta(days=93)
    seen = set()
    out = []
    cur = first
    while cur <= last:
        for d in standard_vx_expiry_candidates(cur.year, cur.month):
            if first <= d <= last and d not in seen:
                seen.add(d)
                out.append(d)
        cur += dt.timedelta(days=32)
        cur = dt.date(cur.year, cur.month, 1)
    return sorted(out)

def norm(s: str) -> str:
    return str(s or "").strip().lower().replace("﻿", "")

def parse_date(s):
    s = str(s or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def parse_float(s):
    try:
        return float(str(s).strip().replace(",", ""))
    except Exception:
        return None

def fetch_expiry(expiry: dt.date):
    url = BASE.format(expiry=expiry.isoformat())
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/csv,text/plain,*/*",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read().decode("utf-8-sig", "replace")
            # Cboe may return a legal/HTML page instead of CSV on bad/retired URLs.
            if not body or body.lstrip().startswith("<"):
                return None, url, "NON_CSV"
            return body, url, "OK"
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None, url, f"HTTP_{e.code}"
            if attempt == 3:
                return None, url, f"HTTP_{e.code}"
            time.sleep(1.0 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                return None, url, "NETWORK_ERROR"
            time.sleep(1.0 * (attempt + 1))
    return None, url, "ERROR"

def parse_contract(body: str, expiry: dt.date, url: str):
    # Cboe VX contract archive columns are:
    # Trade Date,Futures,Open,High,Low,Close,Settle,Change,...
    rows = list(csv.reader(io.StringIO(body)))
    out = []
    for row in rows:
        if not row:
            continue
        d = parse_date(row[0])
        if d is None or len(row) < 7:
            continue
        settle = parse_float(row[6])
        if settle is None:
            continue
        # The final expiry-day row is final settlement, not a tradable prior-close
        # state for our M1/M2 daily term signal. Keep only d < expiry.
        if d < expiry:
            out.append((d, settle))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2018-03-01")
    ap.add_argument("--end", default="2026-09-04")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    start = dt.date.fromisoformat(a.start)
    end = dt.date.fromisoformat(a.end)
    candidates = candidate_expiries(start, end)

    by_date = {}
    meta = []
    successful = set()

    for expiry in candidates:
        body, url, status = fetch_expiry(expiry)
        item = {"expiry": expiry.isoformat(), "url": url, "status": status, "rows": 0}
        if body is not None:
            data = parse_contract(body, expiry, url)
            item["rows"] = len(data)
            if data:
                successful.add(expiry)
                for d, px in data:
                    if start <= d <= end:
                        by_date.setdefault(d, []).append({
                            "expiry": expiry,
                            "price": px,
                            "code": f"VX_{expiry.isoformat()}",
                            "source_url": url,
                        })
        meta.append(item)

    rows = []
    for d in sorted(by_date):
        eligible = sorted(
            [x for x in by_date[d] if x["expiry"] > d],
            key=lambda x: x["expiry"]
        )
        # Deduplicate expiry in case multiple candidate paths ever resolve to one file.
        uniq = []
        seen = set()
        for x in eligible:
            if x["expiry"] not in seen:
                seen.add(x["expiry"])
                uniq.append(x)
        if len(uniq) < 2:
            continue
        m1, m2 = uniq[0], uniq[1]
        p1, p2 = m1["price"], m2["price"]
        rows.append({
            "trade_date": d.isoformat(),
            "m1_code": m1["code"],
            "m1_expiry": m1["expiry"].isoformat(),
            "m1_settlement": p1,
            "m2_code": m2["code"],
            "m2_expiry": m2["expiry"].isoformat(),
            "m2_settlement": p2,
            "term_slope": (p2 - p1) / p1 if p1 else "",
            "source": "CBOE_VX_CONTRACT_ARCHIVE_DAILY_SETTLEMENT",
            "source_m1_url": m1["source_url"],
            "source_m2_url": m2["source_url"],
        })

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "trade_date","m1_code","m1_expiry","m1_settlement",
        "m2_code","m2_expiry","m2_settlement","term_slope",
        "source","source_m1_url","source_m2_url"
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    nonempty = sum(1 for x in meta if x["rows"] > 0)
    payload = {
        "status": "PASS" if rows else "FAIL",
        "contract_files_attempted": len(meta),
        "contract_files_nonempty": nonempty,
        "output_rows": len(rows),
        "coverage": [rows[0]["trade_date"], rows[-1]["trade_date"]] if rows else [None, None],
        "start": a.start,
        "end": a.end,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "Cboe per-expiry VX historical CSV archive",
        "selection": "sort actual contract expiry; eligible iff expiry > trade_date; exclude expiry-day final settlement",
        "failed_candidates": [x for x in meta if x["status"] != "OK"][:50],
    }
    (out.parent / "build_metadata.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))
    if not rows:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
