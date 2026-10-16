#!/usr/bin/env python3
"""
Fetch Cboe public daily VX settlement tables and reconstruct end-of-day M1/M2.

DATA ACQUISITION ONLY. No strategy parameters or P&L logic are changed.

Selection:
  1. Keep standard monthly VX contracts (symbol starts with VX/).
  2. Exclude VXT/VXM and weekly VXNN instruments.
  3. Require expiration_date > trade_date.
  4. Sort by expiration date.
  5. M1 = earliest valid monthly VX; M2 = second earliest.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, io, json, re, time, urllib.error, urllib.request
from pathlib import Path

API = "https://www-api.cboe.com/us/futures/market_statistics/settlement/csv?dt={date}"
UA = "JUN-ZS/brush-timber-mountain-brook research/cboe-vx-daily-settlement"

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")

def pick_field(fields, *wanted):
    normalized = {norm(f): f for f in fields}
    for w in wanted:
        if norm(w) in normalized:
            return normalized[norm(w)]
    for f in fields:
        nf = norm(f)
        for w in wanted:
            if norm(w) in nf or nf in norm(w):
                return f
    return None

def parse_float(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    if s.endswith("*"):
        s = s[:-1]
    try:
        return float(s)
    except ValueError:
        return None

def parse_date(s):
    if s is None:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def fetch_csv(day: dt.date, retries=4):
    url = API.format(date=day.isoformat())
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8-sig", "replace")
                return body, None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (404, 410):
                return None, last
            if e.code == 429 or e.code >= 500:
                time.sleep(1.5 * (attempt + 1))
                continue
            return None, last
        except Exception as e:
            last = repr(e)
            time.sleep(1.5 * (attempt + 1))
    return None, last or "unknown_error"

def extract_m1_m2(day: dt.date, body: str):
    if not body or body[:200].lstrip().startswith("<"):
        raise ValueError("response is not CSV")
    rows = list(csv.DictReader(io.StringIO(body)))
    if not rows:
        return None
    fields = list(rows[0].keys())
    symbol_f = pick_field(fields, "symbol", "futures_symbol")
    expiry_f = pick_field(fields, "expiration_date", "contract_expiration_date", "expiration")
    settle_f = pick_field(fields, "settlement_price", "settlement", "settle", "daily_settlement_price")
    if not (symbol_f and expiry_f and settle_f):
        raise ValueError("unrecognized CSV columns: " + ",".join(fields))

    unique = {}
    for row in rows:
        sym = (row.get(symbol_f) or "").strip()
        if not sym.startswith("VX/"):
            continue
        exp = parse_date(row.get(expiry_f))
        px = parse_float(row.get(settle_f))
        if exp is None or px is None or exp <= day:
            continue
        unique[(exp, sym)] = px

    ordered = sorted((exp, sym, px) for (exp, sym), px in unique.items())
    if len(ordered) < 2:
        return None
    (e1, s1, p1), (e2, s2, p2) = ordered[:2]
    return {
        "trade_date": day.isoformat(),
        "m1_symbol": s1,
        "m1_expiry": e1.isoformat(),
        "m1_settlement": p1,
        "m2_symbol": s2,
        "m2_expiry": e2.isoformat(),
        "m2_settlement": p2,
        "term_slope": (p2 - p1) / p1 if p1 else None,
        "source": "CBOE_PUBLIC_DAILY_SETTLEMENT",
        "source_url": API.format(date=day.isoformat()),
    }

def split_window(start: dt.date, end: dt.date, parts: int, idx: int):
    total = (end - start).days + 1
    lo = start + dt.timedelta(days=(total * idx) // parts)
    hi = start + dt.timedelta(days=(total * (idx + 1)) // parts - 1)
    return lo, min(hi, end)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--parts", type=int, default=10)
    ap.add_argument("--part-index", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    if not (0 <= args.part_index < args.parts):
        raise SystemExit("part-index out of range")

    lo, hi = split_window(start, end, args.parts, args.part_index)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows, errors, schema_sample = [], [], None
    day = lo
    while day <= hi:
        if day.weekday() < 5:
            body, err = fetch_csv(day)
            if body:
                try:
                    rec = extract_m1_m2(day, body)
                    if rec:
                        rows.append(rec)
                    else:
                        errors.append({"date": day.isoformat(), "error": "fewer_than_two_valid_monthly_VX"})
                except Exception as e:
                    errors.append({"date": day.isoformat(), "error": str(e)})
                    if schema_sample is None:
                        schema_sample = body[:1000]
            else:
                errors.append({"date": day.isoformat(), "error": err or "empty_response"})
        day += dt.timedelta(days=1)

    rows.sort(key=lambda r: r["trade_date"])
    fields = [
        "trade_date","m1_symbol","m1_expiry","m1_settlement",
        "m2_symbol","m2_expiry","m2_settlement","term_slope","source","source_url"
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    weekday_requests = sum(
        1 for n in range((hi - lo).days + 1)
        if (lo + dt.timedelta(days=n)).weekday() < 5
    )
    meta = {
        "part_index": args.part_index,
        "parts": args.parts,
        "window": [lo.isoformat(), hi.isoformat()],
        "weekday_requests": weekday_requests,
        "rows": len(rows),
        "errors": len(errors),
        "error_sample": errors[:25],
        "schema_sample": schema_sample,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "Cboe public daily settlement CSV endpoint",
    }
    (out.parent / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))

    parser_errors = [
        e for e in errors
        if "unrecognized CSV columns" in e["error"] or "response is not CSV" in e["error"]
    ]
    if parser_errors:
        raise SystemExit("Cboe CSV parser contract failed; inspect metadata.json")

if __name__ == "__main__":
    main()
