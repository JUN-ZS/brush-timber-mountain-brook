#!/usr/bin/env python3
"""Audit fixed-size overlapping QQQ LONG PUT / SPY SHORT PUT capital exposure."""
import csv, json, hashlib
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

PHASES=range(5)
POLICIES=("HOLD_5_SESSIONS","HOLD_10_SESSIONS","HOLD_20_SESSIONS","EXIT_AT_DTE_LE_7")
LABELS={"HOLD_5_SESSIONS":"5d","HOLD_10_SESSIONS":"10d","HOLD_20_SESSIONS":"20d","EXIT_AT_DTE_LE_7":"DTE<=7"}
NAVS=(80000.0,100000.0,1000000.0)
FRACTIONS=(0.25,0.5,0.75,1.0)

def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def readc(p):
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def day(x):
    try: return date.fromisoformat(str(x or "")[:10])
    except (ValueError,TypeError): return None
def num(x):
    try: return float(x) if x not in (None,"") else None
    except (ValueError,TypeError): return None
def cash(x): return "—" if x is None else "$"+format(x,",.0f")

def validate(phase,s,e,sk,ss):
    n=int(s["coverage"]["common_underlying_sessions"])
    z=s["selection"]; q=s["fixed_entry_schedule"]
    assert s["entry_filter"]["name"]=="none", f"phase {phase}: filter"
    assert z["schedule_mode"]=="FIXED_ANCHOR_NO_REANCHOR", f"phase {phase}: schedule mode"
    assert z["initial_phase_sessions"]==phase and z["cohort_stride_sessions"]==5, f"phase {phase}: cadence"
    assert z["allow_overlapping_cohorts"] is True, f"phase {phase}: overlap"
    assert (s["ratio"]["fixed_long_qqq_contracts"],s["ratio"]["fixed_short_spy_contracts"])==(1,3), f"phase {phase}: ratio"
    slots=set(range(phase,n,5))
    assert q["scheduled_opportunities"]==len(slots), f"phase {phase}: schedule count"
    assert q["selected_signals"]==s["cohort"]["selected_signals"]==len(e)+len(sk), f"phase {phase}: selected/entry ledger"
    assert q["skipped_opportunities"]==len(ss) and len(slots)==len(e)+len(sk)+len(ss), f"phase {phase}: slot accounting"
    for row in e+sk: assert int(row["signal_index"]) in slots, f"phase {phase}: off-anchor signal"
    for row in ss: assert int(row["scheduled_index"]) in slots, f"phase {phase}: off-anchor skip"
    return {"phase":phase,"status":"PASS","slots":len(slots),"selected":len(e)+len(sk),"entered":len(e),"entry_skips":len(sk),"missed_slots":len(ss)}

def sweep(rows):
    events=defaultdict(lambda:[0,0.0])
    used=[]
    for r in rows:
        a=day(r.get("entry_date")); b=day(r.get("exit_date")) or day(r.get("last_observed_date"))
        value=num(r.get("spy_put_strike_assignment_obligation_usd"))
        if a is None or b is None or b<a or value is None or value<0: continue
        events[a][0]+=1; events[a][1]+=value
        events[b+timedelta(days=1)][0]-=1; events[b+timedelta(days=1)][1]-=value
        used.append((a,b))
    active=0; exposure=0.0; peak_n=0; peak=0.0; periods=[]
    points=sorted(events)
    for i,d in enumerate(points[:-1]):
        dn,dx=events[d]; active+=dn; exposure=round(exposure+dx,7)
        days=(points[i+1]-d).days
        if days<=0: continue
        peak_n=max(peak_n,active); peak=max(peak,exposure)
        periods.append((d,points[i+1],days,active,max(0.0,exposure)))
    span=(min(a for a,b in used).isoformat(),max(b for a,b in used).isoformat()) if used else (None,None)
    return {"positions":len(used),"peak_n":peak_n,"peak":round(peak,2),"periods":periods,"span":span}

def fmtpct(n): return "—" if n is None else f"{n:.1f}%"

def build(root,out):
    checks=[]; summary=[]; scenarios=[]; hashes=[]
    for phase in PHASES:
        folder=root/"fixed_phase_sensitivity"/f"phase_{phase}"
        paths={name:folder/name for name in ("summary.json","entry_cohort.csv","entry_skips.csv","scheduled_signal_skips.csv","trade_episodes.csv")}
        for p in paths.values():
            if not p.is_file(): raise FileNotFoundError(f"phase {phase}: missing {p}")
        s=readj(paths["summary.json"]); e=readc(paths["entry_cohort.csv"]); sk=readc(paths["entry_skips.csv"]); ss=readc(paths["scheduled_signal_skips.csv"])
        checks.append(validate(phase,s,e,sk,ss))
        trades=readc(paths["trade_episodes.csv"])
        for policy in POLICIES:
            rows=[r for r in trades if r.get("policy")==policy]
            wins=[num(r.get("net_pnl_usd")) for r in rows if r.get("status")=="RESOLVED" and num(r.get("net_pnl_usd")) is not None]
            resolved=sum(r.get("status")=="RESOLVED" for r in rows)
            unresolved=len(rows)-resolved
            ex=sweep(rows)
            row={"phase":phase,"policy":policy,"exit":LABELS[policy],"opened":len(rows),"resolved":resolved,"unresolved":unresolved,
                 "total_resolved_pnl_usd":round(sum(wins),2),"worst_trade_usd":round(min(wins),2) if wins else None,
                 "peak_concurrent_cohorts":ex["peak_n"],"peak_spy_assignment_obligation_usd":ex["peak"],
                 "period_start":ex["span"][0],"period_end":ex["span"][1]}
            summary.append(row)
            for nav in NAVS:
                for fraction in FRACTIONS:
                    budget=nav*fraction
                    breached=sum(length for a,b,length,n,value in ex["periods"] if value>budget+0.005)
                    scenarios.append({**row,"nav_usd":nav,"available_capital_fraction":fraction,"capital_budget_usd":budget,
                      "peak_shortfall_usd":round(max(0,ex["peak"]-budget),2),
                      "peak_obligation_pct_of_budget":round(100*ex["peak"]/budget,2),
                      "calendar_days_over_budget":breached,"observed_calendar_days":sum(p[2] for p in ex["periods"])})
        hashes.append({"phase":phase,"source_commit":s.get("source",{}).get("tree_commit"),
          "summary_sha256":hashlib.sha256(paths["summary.json"].read_bytes()).hexdigest(),
          "trade_sha256":hashlib.sha256(paths["trade_episodes.csv"].read_bytes()).hexdigest()})
    out.mkdir(parents=True,exist_ok=True)
    def write(path,rows):
        with path.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write(out/"phase_policy_capacity_summary.csv",summary)
    write(out/"capital_capacity_scenarios.csv",scenarios)
    md=["# Fixed-Anchor QQQ/SPY PUT Capital Capacity Audit","","- Same fixed size in every NAV case: QQQ LONG PUT 1 : SPY SHORT PUT 3 per cohort, no filter, stride five, overlapping cohorts enabled.",
        "- Gross SPY assignment obligation = short SPY strike × 100 × contracts. It is a conservative cash-capacity proxy, not broker margin. The QQQ long put is not netted against a different underlying's assignment.",
        "- Positions count from entry through exit inclusive, or through last observed day if unresolved. Threshold days are calendar days.",
        "- NAVs of $80k, $100k and $1m are comparison cases; available capital is assumed to be 25%, 50%, 75% or 100% of NAV. No NAV case is assumed to be the user's account.",
        "- Fixed contract quantities are not resized to fit the NAV. This stage tests capacity; it does not simulate broker liquidation or confirmed fills.","",
        "## Fixed-anchor checks","","| Phase | Scheduled slots | Selected | Entered | Entry skips | Missed slots | Status |","|---:|---:|---:|---:|---:|---:|---|"]
    for c in checks: md.append(f"| {c['phase']} | {c['slots']} | {c['selected']} | {c['entered']} | {c['entry_skips']} | {c['missed_slots']} | {c['status']} |")
    md += ["","## Exposure by phase and exit","","| Phase | Exit | Resolved / unresolved | Net P&L (resolved) | Worst trade | Peak concurrent | Peak assignment obligation |","|---:|---|---:|---:|---:|---:|---:|"]
    for r in summary: md.append(f"| {r['phase']} | {r['exit']} | {r['resolved']} / {r['unresolved']} | {cash(r['total_resolved_pnl_usd'])} | {cash(r['worst_trade_usd'])} | {r['peak_concurrent_cohorts']} | {cash(r['peak_spy_assignment_obligation_usd'])} |")
    md += ["","## Worst phase — all NAV available (100%)","","| Exit | NAV | Worst peak obligation | Obligation / NAV | Phases with peak breach | Max calendar days above capacity |","|---|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        for nav in NAVS:
            chosen=[r for r in scenarios if r["policy"]==policy and r["nav_usd"]==nav and r["available_capital_fraction"]==1.0]
            peak=max(r["peak_spy_assignment_obligation_usd"] for r in chosen)
            breach=sum(r["peak_spy_assignment_obligation_usd"]>nav for r in chosen)
            days=max(r["calendar_days_over_budget"] for r in chosen)
            md.append(f"| {LABELS[policy]} | {cash(nav)} | {cash(peak)} | {fmtpct(100*peak/nav)} | {breach}/5 | {days} |")
    md += ["","## Worst phase — only 50% of NAV available","","| Exit | NAV | Capital budget | Worst peak obligation | Obligation / budget | Phases with peak breach | Max calendar days above budget |","|---|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        for nav in NAVS:
            chosen=[r for r in scenarios if r["policy"]==policy and r["nav_usd"]==nav and r["available_capital_fraction"]==0.5]
            cap=nav*0.5; peak=max(r["peak_spy_assignment_obligation_usd"] for r in chosen)
            breach=sum(r["peak_spy_assignment_obligation_usd"]>cap for r in chosen)
            days=max(r["calendar_days_over_budget"] for r in chosen)
            md.append(f"| {LABELS[policy]} | {cash(nav)} | {cash(cap)} | {cash(peak)} | {fmtpct(100*peak/cap)} | {breach}/5 | {days} |")
    md += ["","## Limits","","- Positive additive P&L cannot override an infeasible cash-capacity path. The tested size is fixed, and no account-level capital gate is applied yet.",
           "- This audit is not a margin model; it omits intraday fills, financing, changes in NAV, assignment timing and broker-specific offsets.",""]
    (out/"capacity_report.md").write_text("\n".join(md),encoding="utf-8")
    meta={"schema":"qqq-spy-fixed-anchor-capacity-audit.v1","phases":list(PHASES),"policies":list(POLICIES),
      "nav_cases_usd":list(NAVS),"capital_fractions":list(FRACTIONS),"scenario_rows":len(scenarios),
      "phase_policy_rows":len(summary),"fixed_anchor_checks":checks,"source_hashes":hashes,
      "assignment_measure":"gross SPY short-put strike x 100 x contract count; cash capacity proxy, not broker margin"}
    (out/"capacity_manifest.json").write_text(json.dumps(meta,indent=2,allow_nan=False),encoding="utf-8")
    return meta

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-root",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    p.add_argument("--out-dir",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/fixed_phase_capacity_audit"))
    a=p.parse_args()
    m=build(a.results_root,a.out_dir)
    print(json.dumps({"status":"COMPLETED","scenarios":m["scenario_rows"],"phase_policy_rows":m["phase_policy_rows"],"schedule_checks":m["fixed_anchor_checks"]},indent=2))
