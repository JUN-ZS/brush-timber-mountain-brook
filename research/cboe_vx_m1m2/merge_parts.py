#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from pathlib import Path

FIELDS=["trade_date","m1_code","m1_settlement","m2_code","m2_settlement","term_slope","source","source_m1_url","source_m2_url"]

LETTERS={"F":1,"G":2,"H":3,"J":4,"K":5,"M":6,"N":7,"Q":8,"U":9,"V":10,"X":11,"Z":12}

def maturity(code):
    return (2000+int(code[1:]),LETTERS[code[0]])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    by_date={}
    for p in sorted(Path(a.input_dir).glob("**/part_*.csv")):
        with p.open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                by_date.setdefault(r["trade_date"],[]).append(r)
    rows=[]
    for day,arr in sorted(by_date.items()):
        unique={r["contract_code"]:r for r in arr}
        ordered=sorted(unique.values(),key=lambda r:maturity(r["contract_code"]))
        if len(ordered)<2:
            continue
        m1,m2=ordered[0],ordered[1]
        p1=float(m1["settlement"]); p2=float(m2["settlement"])
        rows.append({
            "trade_date":day,
            "m1_code":m1["contract_code"],
            "m1_settlement":p1,
            "m2_code":m2["contract_code"],
            "m2_settlement":p2,
            "term_slope":(p2-p1)/p1 if p1 else "",
            "source":"CBOE_CONTRACT_ARCHIVE_DAILY_SETTLEMENT",
            "source_m1_url":m1["source_url"],
            "source_m2_url":m2["source_url"],
        })
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(f"merged_rows={len(rows)} first={rows[0]['trade_date'] if rows else None} last={rows[-1]['trade_date'] if rows else None}")

if __name__=="__main__": main()
