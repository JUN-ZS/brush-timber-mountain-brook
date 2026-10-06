#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://cdn.cboe.com/resources/futures/archive/volume-and-price/CFE_{code}_VX.csv"
UA = "JUN-ZS/brush-timber-mountain-brook / Original Hybrid research"

MONTHS = {"F":1,"G":2,"H":3,"J":4,"K":5,"M":6,"N":7,"Q":8,"U":9,"V":10,"X":11,"Z":12}

def contract_codes():
    out=[]
    for yy in range(18,27):
        year=2000+yy
        for letter,month in MONTHS.items():
            if year == 2026 and month > 9:
                continue
            out.append(f"{letter}{yy:02d}")
    return out

def maturity(code):
    return (2000 + int(code[1:]), MONTHS[code[0]])

def norm(s):
    return re.sub(r"[^a-z0-9]+","_",str(s or "").strip().lower()).strip("_")

def field(fields,*names):
    targets={norm(x) for x in names}
    for f in fields:
        if norm(f) in targets:
            return f
    return None

def parse_date(s):
    s=str(s or "").strip()
    for fmt in ("%m/%d/%Y","%Y-%m-%d","%m/%d/%y"):
        try:
            return dt.datetime.strptime(s,fmt).date()
        except ValueError:
            pass
    return None

def parse_float(s):
    try:
        return float(str(s).strip().replace(",",""))
    except Exception:
        return None

def fetch(code):
    url=BASE.format(code=code)
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/csv,*/*"})
            with urllib.request.urlopen(req,timeout=45) as r:
                body=r.read().decode("utf-8-sig","replace")
            if not body or body.lstrip().startswith("<"):
                raise RuntimeError("non-CSV response")
            return body,url
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as e:
            last=repr(e)
            time.sleep(1.5*(attempt+1))
    raise RuntimeError(f"failed {code}: {last}")

def read_contract(code):
    body,url=fetch(code)
    rows=list(csv.DictReader(io.StringIO(body)))
    if not rows:
        return [],url,{"code":code,"rows":0}
    fields=list(rows[0].keys())
    date_f=field(fields,"Trade Date","Date")
    settle_f=field(fields,"Settle","Settlement Price","Settlement")
    if not date_f or not settle_f:
        raise RuntimeError(f"{code}: unrecognized columns {fields}")
    out=[]
    for row in rows:
        d=parse_date(row.get(date_f))
        px=parse_float(row.get(settle_f))
        if d and px is not None:
            out.append((d,px))
    return out,url,{"code":code,"rows":len(out)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",default="2018-03-01")
    ap.add_argument("--end",default="2026-09-04")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    start=dt.date.fromisoformat(args.start)
    end=dt.date.fromisoformat(args.end)

    contracts=contract_codes()
    by_date={}
    meta=[]

    for code in contracts:
        data,url,m=read_contract(code)
        m["url"]=url
        meta.append(m)
        y,mo=maturity(code)
        expiry=dt.date(y,mo,1)  # contract month identity only; daily selection uses maturity order
        for d,px in data:
            if start <= d <= end:
                by_date.setdefault(d,[]).append({
                    "code":code,
                    "price":px,
                    "maturity":(y,mo),
                    "source_url":url
                })

    rows=[]
    for d in sorted(by_date):
        eligible=[r for r in by_date[d] if dt.date(r["maturity"][0],r["maturity"][1],1) > dt.date(d.year,d.month,1)]
        # The archive stores monthly contract identity; current-month contract is excluded
        # once the trade date reaches its month, matching the research M1/M2 eligibility rule.
        eligible.sort(key=lambda r:r["maturity"])
        if len(eligible) < 2:
            continue
        m1,m2=eligible[0],eligible[1]
        p1,p2=m1["price"],m2["price"]
        rows.append({
            "trade_date":d.isoformat(),
            "m1_code":m1["code"],
            "m1_settlement":p1,
            "m2_code":m2["code"],
            "m2_settlement":p2,
            "term_slope":(p2-p1)/p1 if p1 else "",
            "source":"CBOE_CONTRACT_ARCHIVE_DAILY_SETTLEMENT",
            "source_m1_url":m1["source_url"],
            "source_m2_url":m2["source_url"]
        })

    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    fields=[
        "trade_date","m1_code","m1_settlement","m2_code","m2_settlement",
        "term_slope","source","source_m1_url","source_m2_url"
    ]
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    meta_out={
        "status":"PASS",
        "contract_files_attempted":len(contracts),
        "contract_files_nonempty":sum(1 for m in meta if m["rows"]>0),
        "output_rows":len(rows),
        "coverage":[rows[0]["trade_date"],rows[-1]["trade_date"]] if rows else [None,None],
        "start":args.start,
        "end":args.end,
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "source":"Cboe historical VX contract CSV archives"
    }
    (out.parent/"build_metadata.json").write_text(json.dumps(meta_out,indent=2),encoding="utf-8")
    print(json.dumps(meta_out,indent=2))

if __name__=="__main__":
    main()
