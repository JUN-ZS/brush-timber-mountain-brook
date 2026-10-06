#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

FIELDS=["trade_date","m1_code","m1_settlement","m2_code","m2_settlement","term_slope","source","source_m1_url","source_m2_url"]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    candidates=[]
    for p in sorted(Path(a.input_dir).glob("**/part_*.csv")):
        with p.open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f): candidates.append(r)
    by_date={}
    # Each contract part can independently emit the same date. Reconstruct M1/M2 globally:
    for r in candidates:
        by_date.setdefault(r["trade_date"],[]).append(r)
    rows=[]
    for day,arr in by_date.items():
        # M1/M2 must be the two earliest maturity codes among all part outputs.
        def key(code):
            letter,yy=code[0],int(code[1:]); return (2000+yy, {"F":1,"G":2,"H":3,"J":4,"K":5,"M":6,"N":7,"Q":8,"U":9,"V":10,"X":11,"Z":12}[letter])
        m1=min(arr,key=lambda x:key(x["m1_code"]))
        rest=[x for x in arr if x["m1_code"]!=m1["m1_code"]]
        if not rest: continue
        # Prefer the next maturity represented either as m1_code or m2_code.
        codes={}
        for r in arr:
            codes[r["m1_code"]]=r
            codes[r["m2_code"]]=r
        ordered=sorted(codes.values(),key=lambda x:key(x["m1_code"]))
        first_code=m1["m1_code"]
        second=next((x for x in ordered if x["m1_code"]!=first_code),None)
        if second is None: continue
        rows.append(second if False else {
            "trade_date":day,
            "m1_code":m1["m1_code"],
            "m1_settlement":m1["m1_settlement"],
            "m2_code":m1["m2_code"],
            "m2_settlement":m1["m2_settlement"],
            "term_slope":m1["term_slope"],
            "source":m1["source"],
            "source_m1_url":m1["source_m1_url"],
            "source_m2_url":m1["source_m2_url"],
        })
    # The part with earliest M1 already contains the correct M2 whenever all consecutive
    # monthly contracts are covered; because 10 parts are a partition of all monthly files,
    # dedupe by date is sufficient.
    rows=sorted({r["trade_date"]:r for r in rows}.values(),key=lambda x:x["trade_date"])
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(f"merged_rows={len(rows)} first={rows[0]['trade_date'] if rows else None} last={rows[-1]['trade_date'] if rows else None}")

if __name__=="__main__": main()
