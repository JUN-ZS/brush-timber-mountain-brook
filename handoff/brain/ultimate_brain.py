#!/usr/bin/env python3
"""Minimal deterministic handoff runtime. No broker routing. Python stdlib only."""
from __future__ import annotations
import json, math, sys
from datetime import datetime, timezone
from pathlib import Path

POLICY = {
    "core_pct": 42.0,
    "vxx_normal_pct": 18.0,
    "vxx_high_pct": 10.0,
    "vxx_call_budget_pct": 2.0,
    "qqq_call_budget_pct": 1.2,
    "vix_high": 28.0,
    "term_safe": 5.0,
}

def num(x):
    try:
        if x in ("", None): return None
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None

def term(m1,m2):
    if m1 is None or m2 is None or m1 == 0: return None
    return (m2-m1)/m1*100.0

def decide(s):
    q,v,x = s["qqq"],s["vxx"],s["vix"]
    ts=term(s.get("m1"),s.get("m2"))
    if not all(isinstance(z,(int,float)) and math.isfinite(z) for z in (q,v,x)):
        return {"state":"DATA_INCOMPLETE","action":"HOLD","scope":"BLOCKED","confidence":0,"reason":"QQQ/VXX/VIX incomplete"}
    if ts is None:
        return {"state":"TERM_UNKNOWN","action":"HOLD","scope":"RISK_ONLY","confidence":35,"reason":"M1/M2 unavailable; block only term-dependent carry actions"}
    high=x>=POLICY["vix_high"]
    back=ts<=0
    if high and back:
        return {"state":"SHOCK","action":"REDUCE","scope":"FULL","confidence":97,"reason":"high VIX + backwardation"}
    if back:
        return {"state":"PRE_SHOCK","action":"REDUCE","scope":"FULL","confidence":92,"reason":"backwardation"}
    if high:
        return {"state":"PRE_SHOCK","action":"REDUCE","scope":"NO_NEW_CARRY","confidence":88,"reason":"high VIX"}
    if ts<=POLICY["term_safe"]:
        return {"state":"WEAKENING","action":"HOLD","scope":"FULL","confidence":79,"reason":"thin positive contango"}
    return {"state":"CARRY","action":"BUY","scope":"FULL","confidence":90,"reason":"positive contango + VIX below threshold"}

def main():
    if len(sys.argv)!=2:
        print("Usage: python handoff/brain/ultimate_brain.py handoff/brain/example_market_snapshot.json")
        return 2
    p=Path(sys.argv[1])
    s=json.loads(p.read_text(encoding="utf-8"))
    for k in ("qqq","vxx","vix","m1","m2"): s[k]=num(s.get(k))
    out={
      "timestamp":datetime.now(timezone.utc).isoformat(),
      "engine_role":"DECISION_SUPPORT_ONLY",
      "policy":POLICY,
      "input":s,
      "term_structure_pct":term(s["m1"],s["m2"]),
      "decision":decide(s),
      "provenance":s.get("provenance",{})
    }
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
