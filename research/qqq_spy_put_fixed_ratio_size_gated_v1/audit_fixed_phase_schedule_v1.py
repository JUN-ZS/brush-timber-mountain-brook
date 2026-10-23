#!/usr/bin/env python3
"""Audit fixed-anchor cadence slots and summarize five independently replayed phases."""
from __future__ import annotations
import csv, json, math, statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

PHASES = (0, 1, 2, 3, 4)
POLICIES = ("HOLD_5_SESSIONS", "HOLD_10_SESSIONS", "HOLD_20_SESSIONS", "EXIT_AT_DTE_LE_7")
LABELS = {"HOLD_5_SESSIONS":"5d", "HOLD_10_SESSIONS":"10d", "HOLD_20_SESSIONS":"20d", "EXIT_AT_DTE_LE_7":"DTE<=7"}
WINDOWS = (("1Y", date(2024,7,23), date(2025,7,23), 1.0),
           ("3Y", date(2022,7,23), date(2025,7,23), 3.0),
           ("5Y", date(2020,7,23), date(2025,7,23), 5.0))
CUTOFF = date(2025,7,23)

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def dval(value):
    try: return date.fromisoformat(str(value or "")[:10])
    except ValueError: return None

def fval(value):
    try:
        v=float(value)
        return v if math.isfinite(v) else None
    except (ValueError, TypeError): return None

def unique_count(rows, field="episode_id"):
    return len({str(r.get(field) or "") for r in rows if r.get(field) not in (None, "")})

def peak_exposure(rows, start, end):
    events=defaultdict(lambda:[0,0.0])
    for r in rows:
        entry=dval(r.get("entry_date"))
        finish=dval(r.get("exit_date")) or dval(r.get("last_observed_date"))
        obligation=fval(r.get("spy_put_strike_assignment_obligation_usd")) or 0.0
        if entry is None or finish is None or finish < start or entry > end or finish < entry:
            continue
        left=max(entry,start); right=min(finish,end)
        if left>right: continue
        events[left][0]+=1; events[left][1]+=obligation
        after=right+timedelta(days=1)
        events[after][0]-=1; events[after][1]-=obligation
    n=0; cash=0.0; peak_n=0; peak_cash=0.0
    for day in sorted(events):
        dn,dc=events[day]; n+=dn; cash+=dc
        peak_n=max(peak_n,n); peak_cash=max(peak_cash,cash)
    return peak_n,round(peak_cash,2)

def summarize(rows, phase, window, start, end, years, policy):
    all_policy=[r for r in rows if r.get("policy")==policy]
    opened_rows=[r for r in all_policy if (dval(r.get("signal_date")) is not None and start<=dval(r.get("signal_date"))<=end)]
    n_open=unique_count(opened_rows)
    resolved=[r for r in opened_rows if r.get("status")=="RESOLVED" and fval(r.get("net_pnl_usd")) is not None]
    pnl=[float(fval(r["net_pnl_usd"])) for r in resolved]
    wins=sum(p>0.005 for p in pnl); losses=sum(p< -0.005 for p in pnl)
    stress=[]
    for r in resolved:
        lq=fval(r.get("long_qqq_qty")); sq=fval(r.get("short_spy_qty")); value=fval(r.get("net_pnl_usd"))
        if lq is not None and sq is not None and value is not None:
            stress.append(value-10.0*(lq+sq))
    peak_n,peak_obligation=peak_exposure(all_policy,start,end)
    total=sum(pnl)
    return {
        "phase":phase, "window":window, "start":start.isoformat(), "end":end.isoformat(),
        "years":years,"entry_filter":"none","stride_sessions":5,"ratio":"1:3","policy":policy,
        "opened":n_open,"resolved":len(resolved),"unresolved":n_open-len(resolved),
        "wins":wins,"losses":losses,"win_rate_pct":round(100*wins/len(pnl),2) if pnl else None,
        "mean_net_pnl_usd":round(statistics.mean(pnl),2) if pnl else None,
        "median_net_pnl_usd":round(statistics.median(pnl),2) if pnl else None,
        "total_resolved_net_pnl_usd":round(total,2),
        "annualized_resolved_net_pnl_usd":round(total/years,2),
        "worst_resolved_trade_usd":round(min(pnl),2) if pnl else None,
        "profit_factor":round(sum(p for p in pnl if p>0)/abs(sum(p for p in pnl if p<0)),3) if any(p<0 for p in pnl) else None,
        "stress_total_net_pnl_usd":round(sum(stress),2),
        "stress_annualized_net_pnl_usd":round(sum(stress)/years,2),
        "stress_worst_trade_usd":round(min(stress),2) if stress else None,
        "peak_concurrent_cohorts":peak_n,
        "peak_short_assignment_obligation_usd":peak_obligation,
    }

def write_csv(path, rows):
    if not rows: raise ValueError(f"refusing empty output: {path}")
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def make_report(periods, calendar, schedule_checks, selection_meta):
    lines=[
      "# QQQ/SPY PUT 1:3 Fixed-Anchor Five-Phase Robustness",
      "",
      "- Each phase uses immutable scheduled common-session indices: phase + k × 5. A missing chain, missing underlying close, rejected filter, absent eligible pair, or outstanding pending entry is recorded as a skipped scheduled slot; it never moves future slots.",
      "- Each phase runs the full contract-selection and quote-side accounting pipeline. This report does not shift old P&L records.",
      "- Fixed ratio QQQ LONG PUT 1 : SPY SHORT PUT 3; no relative filter; overlapping cohorts enabled.",
      f"- Same expiry; DTE {selection_meta['dte_min']}–{selection_meta['dte_max']} targeting {selection_meta['dte_target']}; target absolute Delta {selection_meta['target_abs_delta']:.2f}; quote-side displayed-size checks; $0.05/share/side slippage and $0.65 per contract/side commission.",
      "- Historical option source ends 2025-12-12. Period windows end 2025-07-23. EOD quote-side results are estimates, not confirmed fills.",
      "",
      "## Fixed-slot accounting and anchor validation",
      "",
      "| Phase | Scheduled slots | Selected pairs | Skipped slots | Skip reasons | Anchor integrity |",
      "|---:|---:|---:|---:|---|---|",
    ]
    for r in schedule_checks:
        reasons="; ".join(f"{k}={v}" for k,v in sorted(r["skip_reason_counts"].items())) or "none"
        lines.append(f"| {r['phase']} | {r['scheduled_opportunities']} | {r['selected_signals']} | {r['skipped_opportunities']} | {reasons} | {r['status']} |")
    def money(x): return "—" if x is None else "$"+format(float(x),",.2f")
    def pct(x): return "—" if x is None else format(float(x),".2f")+"%"
    lines += ["","## Phase comparison — 5Y window","","| Phase | Exit | Trades/year | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Stress annualized | Peak overlap | Peak SPY assignment obligation |","|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted([x for x in periods if x["window"]=="5Y"],key=lambda x:(x["phase"],POLICIES.index(x["policy"]))):
        lines.append(f"| {r['phase']} | {LABELS[r['policy']]} | {r['opened']/5:.2f} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | {money(r['annualized_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | {money(r['stress_annualized_net_pnl_usd'])} | {r['peak_concurrent_cohorts']} | {money(r['peak_short_assignment_obligation_usd'])} |")
    lines += ["","## 1Y / 3Y / 5Y comparisons — 20-session exit","","| Phase | Window | Opened/resolved/unresolved | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Stress annualized | Peak overlap | Peak assignment obligation |","|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted([x for x in periods if x["policy"]=="HOLD_20_SESSIONS"],key=lambda x:(x["phase"],["1Y","3Y","5Y"].index(x["window"]))):
        lines.append(f"| {r['phase']} | {r['window']} | {r['opened']}/{r['resolved']}/{r['unresolved']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | {money(r['annualized_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | {money(r['stress_annualized_net_pnl_usd'])} | {r['peak_concurrent_cohorts']} | {money(r['peak_short_assignment_obligation_usd'])} |")
    lines += ["","## Calendar-year results — 20-session exit","","| Year | Phase | Opened/resolved | Win rate | Mean/trade | Total resolved | Worst trade |","|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted([x for x in calendar if x["policy"]=="HOLD_20_SESSIONS"],key=lambda x:(x["year"],x["phase"])):
        lines.append(f"| {r['year']} | {r['phase']} | {r['opened']}/{r['resolved']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} |")
    lines += ["","## Limits","","- This is still an in-sample historical robustness test, not forward validation.",
              "- P&L is additive fixed-size cohort P&L, not compounded NAV; no total account cash, collateral, margin, liquidation or simultaneous-loss constraint is modeled.",
              "- Peak assignment obligation sums strike × 100 × short SPY contracts and is not broker margin.",
              "- Higher entry frequency mechanically increases concurrent exposures. The test does not prove the account can fund every overlapping cohort.",
              "- $0.10/share/side stress is a cost sensitivity, not a new fill simulation. Displayed EOD size does not guarantee multi-leg fills.",
              "- The result is not complete unless all fixed-slot accounting checks report PASS; anchor checks do not correct for dependence, regime clustering, or prior strategy selection.",""]
    return "\n".join(lines)

def validate_schedule_phase(phase, summary, entry_rows, entry_skip_rows, schedule_skip_rows):
    stride=5
    count=int(summary.get("coverage",{}).get("common_underlying_sessions",0))
    expected=len(range(phase,count,stride))
    selection=summary.get("selection",{})
    sched=summary.get("fixed_entry_schedule",{})
    if selection.get("schedule_mode")!="FIXED_ANCHOR_NO_REANCHOR":
        raise ValueError(f"phase {phase}: not using fixed-anchor schedule")
    if selection.get("initial_phase_sessions")!=phase or selection.get("cohort_stride_sessions")!=stride:
        raise ValueError(f"phase {phase}: wrong phase/stride metadata")
    if sched.get("mode")!="FIXED_ANCHOR_NO_REANCHOR" or sched.get("phase_sessions")!=phase:
        raise ValueError(f"phase {phase}: missing fixed schedule metadata")
    if sched.get("scheduled_opportunities")!=expected:
        raise ValueError(f"phase {phase}: expected {expected} scheduled slots, saw {sched.get('scheduled_opportunities')}")
    selected=int(summary.get("cohort",{}).get("selected_signals",0))
    if sched.get("selected_signals")!=selected:
        raise ValueError(f"phase {phase}: selected-pair count mismatch")
    if sched.get("skipped_opportunities")!=len(schedule_skip_rows):
        raise ValueError(f"phase {phase}: scheduled skip count mismatch")
    if expected != selected + len(schedule_skip_rows):
        raise ValueError(f"phase {phase}: scheduled-slot accounting does not reconcile")
    selected_indices=[]
    for row in entry_rows+entry_skip_rows:
        value=fval(row.get("signal_index"))
        if value is None:
            raise ValueError(f"phase {phase}: selected signal missing signal_index")
        selected_indices.append(int(value))
    if len(selected_indices)!=selected:
        raise ValueError(f"phase {phase}: selected signal index count {len(selected_indices)} != {selected}")
    slots=set(range(phase,count,stride))
    bad=[i for i in selected_indices if i not in slots]
    if bad:
        raise ValueError(f"phase {phase}: selected signals off fixed cadence: {bad[:10]}")
    missed=[]
    for row in schedule_skip_rows:
        value=fval(row.get("scheduled_index"))
        if value is None or int(value) not in slots:
            missed.append(row.get("scheduled_index"))
    if missed:
        raise ValueError(f"phase {phase}: skip records off fixed cadence: {missed[:10]}")
    reason_counts={}
    for row in schedule_skip_rows:
        reason=str(row.get("reason") or "UNKNOWN")
        reason_counts[reason]=reason_counts.get(reason,0)+1
    return {"phase":phase,"status":"PASS","scheduled_opportunities":expected,
            "selected_signals":selected,"skipped_opportunities":len(schedule_skip_rows),
            "skip_reason_counts":reason_counts,"common_underlying_sessions":count}

def build(root:Path, out:Path):
    periods=[]; calendar=[]; hashes=[]; summaries={}; schedule_checks=[]; selection_meta=None
    for phase in PHASES:
        case=root/"fixed_phase_sensitivity"/f"phase_{phase}"
        sp=case/"summary.json"; tp=case/"trade_episodes.csv"
        ep=case/"entry_cohort.csv"; es=case/"entry_skips.csv"; ss=case/"scheduled_signal_skips.csv"
        for path in (sp,tp,ep,es,ss):
            if not path.is_file():
                raise FileNotFoundError(f"missing fixed-phase replay output: {path}")
        summary=read_json(sp)
        selection=summary.get("selection",{})
        current_selection={k:selection.get(k) for k in ("dte_min","dte_max","dte_target","target_abs_delta")}
        if selection_meta is None:
            selection_meta=current_selection
        elif current_selection != selection_meta:
            raise ValueError(f"phase {phase}: DTE/Delta selection differs: {current_selection} != {selection_meta}")
        if summary.get("entry_filter",{}).get("name")!="none":
            raise ValueError(f"wrong filter phase {phase}")
        if selection.get("allow_overlapping_cohorts") is not True:
            raise ValueError(f"overlap disabled phase {phase}")
        ratio=summary.get("ratio",{})
        if (ratio.get("fixed_long_qqq_contracts"),ratio.get("fixed_short_spy_contracts"))!=(1,3):
            raise ValueError(f"wrong ratio phase {phase}")
        entry_rows=read_csv(ep); entry_skip_rows=read_csv(es); schedule_skip_rows=read_csv(ss)
        check=validate_schedule_phase(phase,summary,entry_rows,entry_skip_rows,schedule_skip_rows)
        schedule_checks.append(check)
        rows=read_csv(tp)
        for window,start,end,years in WINDOWS:
            for policy in POLICIES:
                periods.append(summarize(rows,phase,window,start,end,years,policy))
        for year in range(2018,2026):
            start=date(year,1,1); end=min(date(year,12,31),CUTOFF)
            if start>end: continue
            for policy in POLICIES:
                r=summarize(rows,phase,str(year),start,end,max(1,(end-start).days+1)/365.2425,policy)
                calendar.append({k:r[k] for k in ("phase","window","start","end","entry_filter","stride_sessions","ratio","policy","opened","resolved","unresolved","win_rate_pct","mean_net_pnl_usd","total_resolved_net_pnl_usd","annualized_resolved_net_pnl_usd","worst_resolved_trade_usd","peak_concurrent_cohorts","peak_short_assignment_obligation_usd")}|{"year":year})
        hashes.append({"phase":phase,
          "summary_sha256":__import__("hashlib").sha256(sp.read_bytes()).hexdigest(),
          "trade_episodes_sha256":__import__("hashlib").sha256(tp.read_bytes()).hexdigest(),
          "entry_cohort_sha256":__import__("hashlib").sha256(ep.read_bytes()).hexdigest(),
          "entry_skips_sha256":__import__("hashlib").sha256(es.read_bytes()).hexdigest(),
          "scheduled_signal_skips_sha256":__import__("hashlib").sha256(ss.read_bytes()).hexdigest(),
          "summary_path":str(sp),"trade_path":str(tp),"entry_path":str(ep),
          "full_period_selected":summary.get("cohort",{}).get("selected_signals"),
          "full_period_entered":summary.get("cohort",{}).get("entered_cohorts"),
          "full_period_entry_skipped":summary.get("cohort",{}).get("entry_skipped"),
          "fixed_slot_skipped":summary.get("fixed_entry_schedule",{}).get("skipped_opportunities")})
        summaries[phase]=summary
    if len(schedule_checks)!=5 or any(x["status"]!="PASS" for x in schedule_checks):
        raise ValueError(f"fixed schedule integrity checks failed: {schedule_checks}")
    out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"period_comparison.csv",periods);write_csv(out/"calendar_year_comparison.csv",calendar)
    metadata={"schema":"qqq-spy-fixed-anchor-start-phase-robustness.v1","phase_count":5,"phases":list(PHASES),
      "schedule_mode":"FIXED_ANCHOR_NO_REANCHOR","entry_filter":"none","stride_sessions":5,"ratio":"1:3","policies":list(POLICIES),
      **(selection_meta or {}),
      "period_row_count":len(periods),"calendar_year_row_count":len(calendar),"source_last_chain_date":"2025-12-12",
      "period_windows":[{"name":w,"start":s.isoformat(),"end":e.isoformat(),"years":y} for w,s,e,y in WINDOWS],
      "source_hashes":hashes,"fixed_schedule_checks":schedule_checks}
    (out/"comparison.json").write_text(json.dumps({"metadata":metadata,"period_records":periods,"calendar_year_records":calendar},indent=2,allow_nan=False),encoding="utf-8")
    (out/"report.md").write_text(make_report(periods,calendar,schedule_checks,selection_meta or {}),encoding="utf-8")
    return metadata

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-root",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    p.add_argument("--out-dir",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/fixed_phase_sensitivity_audit"))
    a=p.parse_args(); m=build(a.results_root,a.out_dir)
    print(json.dumps({"status":"COMPLETED","phase_count":m["phase_count"],"period_rows":m["period_row_count"],"calendar_year_rows":m["calendar_year_row_count"],"fixed_schedule_checks":m["fixed_schedule_checks"]},indent=2))

if __name__=="__main__": main()
