#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path

def date_key(s):
    return str(s or "").strip()[:10]

def f(x):
    try:
        return float(x)
    except Exception:
        return None

def sign(x, eps=1e-12):
    if x is None or not math.isfinite(x):
        return None
    if x > eps: return 1
    if x < -eps: return -1
    return 0

def load_external(path):
    out={}
    with open(path,encoding="utf-8-sig",newline="") as h:
        for r in csv.DictReader(h):
            d=date_key(r.get("Date"))
            m1=f(r.get("M1")); m2=f(r.get("M2"))
            if d and m1 is not None and m2 is not None:
                out[d]={"m1":m1,"m2":m2,"s":(m2-m1)/m1 if m1 else None}
    return out

def load_cboe(path):
    out={}
    with open(path,encoding="utf-8-sig",newline="") as h:
        for r in csv.DictReader(h):
            d=date_key(r.get("trade_date"))
            m1=f(r.get("m1_settlement")); m2=f(r.get("m2_settlement"))
            if d and m1 is not None and m2 is not None:
                out[d]={
                    "m1":m1,"m2":m2,
                    "s":f(r.get("term_slope")),
                    "m1_expiry":date_key(r.get("m1_expiry")),
                    "m2_expiry":date_key(r.get("m2_expiry")),
                }
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cboe",required=True)
    ap.add_argument("--external",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    c=load_cboe(a.cboe)
    e=load_external(a.external)
    dates=sorted(set(c)&set(e))

    both_ok=0
    m1_ok=0
    m2_ok=0
    sign_ok=0
    order_ok=0
    rows=[]

    for d in dates:
        x,y=c[d],e[d]
        dm1=abs(x["m1"]-y["m1"])
        dm2=abs(x["m2"]-y["m2"])
        so=sign(x["s"]); se=sign(y["s"])
        m1pass=dm1 <= 0.10
        m2pass=dm2 <= 0.10
        signpass=(so is not None and se is not None and so == se)
        orderpass=(x["m1_expiry"] and x["m2_expiry"] and x["m1_expiry"] < x["m2_expiry"])
        m1_ok += int(m1pass); m2_ok += int(m2pass)
        both_ok += int(m1pass and m2pass)
        sign_ok += int(signpass)
        order_ok += int(orderpass)
        rows.append({
            "date":d,"m1_abs_diff":dm1,"m2_abs_diff":dm2,
            "external_slope":y["s"],"cboe_slope":x["s"],
            "term_sign_match":signpass,"expiry_order_ok":orderpass
        })

    n=len(dates)
    m1_rate=m1_ok/n if n else 0
    m2_rate=m2_ok/n if n else 0
    both_rate=both_ok/n if n else 0
    sign_rate=sign_ok/n if n else 0
    order_violations=n-order_ok

    checks={
        "overlap_rows_ge_900": n >= 900,
        "m1_abs_diff_le_0_10_rate_ge_99pct": m1_rate >= .99,
        "m2_abs_diff_le_0_10_rate_ge_99pct": m2_rate >= .99,
        "combined_m1_m2_abs_diff_le_0_10_rate_ge_99pct": both_rate >= .99,
        "term_sign_mismatch_le_1pct": (1-sign_rate) <= .01 if n else False,
        "expiry_order_violations_eq_0": order_violations == 0,
    }
    payload={
        "status":"PASS" if all(checks.values()) else "FAIL",
        "thresholds":{
            "min_overlap_rows":900,
            "max_abs_diff":0.10,
            "min_each_price_match_rate":0.99,
            "min_combined_price_match_rate":0.99,
            "max_term_sign_mismatch_rate":0.01,
            "max_expiry_order_violations":0
        },
        "metrics":{
            "overlap_rows":n,
            "m1_match_rate":m1_rate,
            "m2_match_rate":m2_rate,
            "combined_match_rate":both_rate,
            "term_sign_match_rate":sign_rate,
            "term_sign_mismatch_rate":1-sign_rate if n else None,
            "expiry_order_violations":order_violations
        },
        "checks":checks,
        "cboe_rows":len(c),
        "external_rows":len(e),
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    (out.parent/"overlap_rows.csv").write_text(
        "date,m1_abs_diff,m2_abs_diff,external_slope,cboe_slope,term_sign_match,expiry_order_ok\n"+
        "".join(
            f'{r["date"]},{r["m1_abs_diff"]:.6f},{r["m2_abs_diff"]:.6f},{r["external_slope"]},{r["cboe_slope"]},{r["term_sign_match"]},{r["expiry_order_ok"]}\n'
            for r in rows
        ),
        encoding="utf-8"
    )
    print(json.dumps(payload,indent=2))
    if payload["status"] != "PASS":
        raise SystemExit(2)

if __name__=="__main__":
    main()
