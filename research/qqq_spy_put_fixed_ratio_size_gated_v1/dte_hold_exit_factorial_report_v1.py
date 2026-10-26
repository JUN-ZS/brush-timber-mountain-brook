#!/usr/bin/env python3
"""Audit and summarize the predeclared DTE × holding duration × exit-guard replay."""
from __future__ import annotations
import csv,json,statistics
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path

ROOT=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte_hold_exit_factorial_v1")
START,END=date(2018,3,1),date(2025,12,15)
YEARS=(END-START).days/365.25
BANDS={20:(14,26),30:(24,36),45:(39,51),60:(54,66)}
PHASES=(0,2,4,6,8);HOLDS=(5,10,15,20);GUARDS=(None,7,14)
POLICIES={(h,g):(f"HOLD_{h}_SESSIONS" if g is None else f"HOLD_{h}_OR_DTE_LE_{g}") for h in HOLDS for g in GUARDS}

def num(v):
    try:return None if v is None or v=="" else float(v)
    except (TypeError,ValueError):return None
def med(v):
    x=[float(a) for a in v if a is not None and a!=""]
    return round(statistics.median(x),2) if x else None
def money(v,d=0):return "n/a" if v is None or v=="" else "$"+f"{float(v):,.{d}f}"
def pct(v,d=2):return "n/a" if v is None or v=="" else f"{float(v):.{d}f}%"
def writecsv(path,rows):
    if not rows:raise SystemExit(f"empty output: {path}")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def overlap(path,policy):
    ev=defaultdict(lambda:[0,0.0])
    with path.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("policy")!=policy or not r.get("entry_date"):continue
            start=date.fromisoformat(r["entry_date"][:10]);st=(r.get("status") or "").upper()
            ex=r.get("exit_date") or "";last=r.get("last_observed_date") or ""
            end=date.fromisoformat(ex[:10]) if st=="RESOLVED" and ex else (date.fromisoformat(last[:10]) if last else END)
            end=max(start,end);ob=num(r.get("spy_put_strike_assignment_obligation_usd")) or 0
            ev[start][0]+=1;ev[start][1]+=ob;ev[end+timedelta(days=1)][0]-=1;ev[end+timedelta(days=1)][1]-=ob
    n=peak=0;ob=peakob=0.0
    for day in sorted(ev):
        n+=ev[day][0];ob+=ev[day][1];peak=max(peak,n);peakob=max(peakob,ob)
    return peak,round(peakob,2)
def load():
    cells=[];yrrows=[]
    for dte,(dmin,dmax) in BANDS.items():
        for phase in PHASES:
            out=ROOT/f"dte_{dte}"/f"phase_{phase}"
            for fn in ("summary.json","summary.md","trade_episodes.csv","factorial_policy_summary.json"):
                p=out/fn
                if not p.is_file() or p.stat().st_size==0:raise SystemExit(f"missing output: {p}")
            data=json.loads((out/"summary.json").read_text(encoding="utf-8"))
            if not str(data.get("status","")).startswith("COMPLETED"):raise SystemExit(f"incomplete DTE{dte} phase{phase}")
            sel=data.get("selection",{})
            expect={"dte_target":dte,"dte_min":dmin,"dte_max":dmax,"cohort_stride_sessions":10,"initial_phase_sessions":phase,"allow_overlapping_cohorts":True}
            if sel and any(sel.get(k)!=v for k,v in expect.items()):raise SystemExit(f"configuration mismatch DTE{dte} phase{phase}: {sel}")
            ratio=data.get("ratio",{})
            if ratio and (ratio.get("fixed_long_qqq_contracts")!=1 or ratio.get("fixed_short_spy_contracts")!=6):raise SystemExit("ratio mismatch")
            if set(data.get("policies",{}))!=set(POLICIES.values()):raise SystemExit(f"policy mismatch DTE{dte} phase{phase}")
            entries=int(data.get("cohort",{}).get("entered_cohorts",0));tp=out/"trade_episodes.csv"
            with tp.open(newline="",encoding="utf-8") as f:trades=list(csv.DictReader(f))
            for (hold,guard),policy in POLICIES.items():
                s=data["policies"][policy];total=num(s.get("total_net_pnl_usd"));ann=total/YEARS if total is not None else None
                peak,peakob=overlap(tp,policy)
                cells.append({"dte_target":dte,"dte_min":dmin,"dte_max":dmax,"phase_sessions":phase,"hold_sessions":hold,
                    "expiry_guard_dte":"" if guard is None else guard,"policy":policy,"entries":entries,"resolved":int(s.get("resolved") or 0),
                    "unresolved":int(s.get("unresolved") or 0),"win_rate_pct":num(s.get("win_rate_pct")),
                    "expectancy_usd":num(s.get("expectancy_net_usd")),"median_trade_usd":num(s.get("median_net_usd")),
                    "total_resolved_pnl_usd":total,"annual_resolved_pnl_usd":round(ann,2) if ann is not None else "",
                    "worst_trade_usd":num(s.get("worst_net_usd")),"profit_factor":num(s.get("profit_factor")),
                    "peak_concurrent_cohorts":peak,"peak_gross_assignment_obligation_usd":peakob,"status":data.get("status")})
                byexit=defaultdict(float);unres=defaultdict(int)
                for t in trades:
                    if t.get("policy")!=policy:continue
                    st=(t.get("status") or "").upper();ex=t.get("exit_date") or "";en=t.get("entry_date") or ""
                    if st=="RESOLVED" and ex and num(t.get("net_pnl_usd")) is not None:byexit[int(ex[:4])]+=float(t["net_pnl_usd"])
                    elif en:unres[int(en[:4])]+=1
                for year in range(2018,2026):
                    yrrows.append({"dte_target":dte,"phase_sessions":phase,"hold_sessions":hold,"expiry_guard_dte":"" if guard is None else guard,
                        "policy":policy,"exit_year":year,"resolved_pnl_usd":round(byexit[year],2),"unresolved_entries_by_entry_year":unres[year]})
    return cells,yrrows
def aggregate(cells):
    groups=defaultdict(list)
    for r in cells:groups[(r["dte_target"],r["hold_sessions"],r["expiry_guard_dte"],r["policy"])].append(r)
    out=[]
    for (dte,h,g,p),rs in sorted(groups.items(),key=lambda item:(item[0][0],item[0][1],99 if item[0][2] in (None,"") else int(item[0][2]),item[0][3])):
        vals=[num(r["annual_resolved_pnl_usd"]) for r in rs];vals=[v for v in vals if v is not None]
        out.append({"dte_target":dte,"dte_min":rs[0]["dte_min"],"dte_max":rs[0]["dte_max"],"hold_sessions":h,"expiry_guard_dte":g,"policy":p,
            "phase_count":len(rs),"median_annual_pnl_usd":med(vals),"min_annual_pnl_usd":round(min(vals),2) if vals else None,
            "max_annual_pnl_usd":round(max(vals),2) if vals else None,"phases_ge_12000":sum(v>=12000 for v in vals),
            "median_resolved":med([r["resolved"] for r in rs]),"median_unresolved":med([r["unresolved"] for r in rs]),
            "median_win_rate_pct":med([r["win_rate_pct"] for r in rs]),"median_expectancy_usd":med([r["expectancy_usd"] for r in rs]),
            "median_worst_trade_usd":med([r["worst_trade_usd"] for r in rs]),"median_peak_overlap":med([r["peak_concurrent_cohorts"] for r in rs]),
            "median_peak_assignment_obligation_usd":med([r["peak_gross_assignment_obligation_usd"] for r in rs])})
    return out
def factor_effects(configs):
    out=[];factors=[("Opening DTE target","dte_target",[20,30,45,60]),("Max holding sessions","hold_sessions",[5,10,15,20]),
        ("Early-exit DTE guard","expiry_guard_dte",["",7,14])]
    for name,field,levels in factors:
        vals=[]
        for lv in levels:
            rs=[r for r in configs if str(r[field])==str(lv)]
            vals.append((str(lv),med([r["median_annual_pnl_usd"] for r in rs]),len(rs)))
        ns=[v for _,v,_ in vals if v is not None];spread=round(max(ns)-min(ns),2) if ns else None
        for lev,v,n in vals:out.append({"factor":name,"level":lev,"median_annual_pnl_across_other_settings_usd":v,"level_median_spread_usd":spread,"comparisons":n})
    return out
def make_report(configs,effects,yr):
    L=["# DTE × holding duration × exit guard factorial replay","",f"- Period: {START.isoformat()} to {END.isoformat()} ({YEARS:.3f} calendar years).",
    "- Cadence: every 10 common QQQ/SPY sessions; five predeclared phase anchors: 0, 2, 4, 6, 8.",
    "- Fixed legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry; nearest absolute Delta 0.25 on both legs.",
    "- Costs: USD 0.05/share/side slippage + USD 0.65/contract/side commission; no entry filter.",
    "- DTE target bands: "+"; ".join(f"DTE{d}: {lo}–{hi}" for d,(lo,hi) in BANDS.items())+".",
    "- Exit rules: max hold 5/10/15/20 sessions × no guard / remaining DTE ≤ 7 / remaining DTE ≤ 14. Guard exits use OR logic with maximum hold.",
    "- 20 source-pinned replay runs (4 DTE targets × 5 phases); all 12 exit policies run on each selected entry stream, yielding 240 phase cells and 48 phase-aggregated settings.","",
    "## Main effects","",
    "Each factor level is the median annual resolved-trade P&L across the other settings and five phase anchors. Spread is max minus min of level medians; descriptive screening only, not causal or account return.","",
    "| Factor | Level | Median annual P&L across other settings | Factor level spread |","|---|---:|---:|---:|"]
    for fn in ("Opening DTE target","Max holding sessions","Early-exit DTE guard"):
        for r in [x for x in effects if x["factor"]==fn]:
            lv=r["level"]
            label=f"DTE{lv}" if fn=="Opening DTE target" else (f"{lv} sessions" if fn=="Max holding sessions" else ("No DTE guard" if lv=="" else f"Remaining DTE ≤ {lv}"))
            L.append(f"| {fn} | {label} | {money(r['median_annual_pnl_across_other_settings_usd'])} | {money(r['level_median_spread_usd'])} |")
    L += ["","## Same exit: hold up to 20 sessions OR remaining DTE ≤ 7","","| Opening DTE target (band) | Median annual P&L | Min–max by phase | Phases ≥ USD12k | Median win rate | Median worst trade |","|---:|---:|---:|---:|---:|---:|"]
    for r in sorted([x for x in configs if x["hold_sessions"]==20 and str(x["expiry_guard_dte"])=="7"],key=lambda x:x["dte_target"]):
        L.append(f"| DTE{r['dte_target']} ({r['dte_min']}–{r['dte_max']}) | {money(r['median_annual_pnl_usd'])} | {money(r['min_annual_pnl_usd'])}–{money(r['max_annual_pnl_usd'])} | {r['phases_ge_12000']}/5 | {pct(r['median_win_rate_pct'])} | {money(r['median_worst_trade_usd'],2)} |")
    L += ["","## Same DTE target: DTE45 (band 39–51)","","| Max hold | Guard | Median annual P&L | Min–max by phase | Phases ≥ USD12k | Median expectancy/trade | Median worst trade |","|---:|---|---:|---:|---:|---:|---:|"]
    for r in sorted([x for x in configs if x["dte_target"]==45],key=lambda x:(x["hold_sessions"],99 if x["expiry_guard_dte"]=="" else int(x["expiry_guard_dte"]))):
        guard="None" if r["expiry_guard_dte"]=="" else f"DTE≤{r['expiry_guard_dte']}"
        L.append(f"| {r['hold_sessions']} sessions | {guard} | {money(r['median_annual_pnl_usd'])} | {money(r['min_annual_pnl_usd'])}–{money(r['max_annual_pnl_usd'])} | {r['phases_ge_12000']}/5 | {money(r['median_expectancy_usd'],2)} | {money(r['median_worst_trade_usd'],2)} |")
    L += ["","## All 48 settings across five phases","","| Target DTE (band) | Hold | Guard | Median annual P&L | Min–max | ≥USD12k phases | Resolved | Unresolved | Win rate | Worst trade | Peak overlaps |","|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(configs,key=lambda x:(x["dte_target"],x["hold_sessions"],99 if x["expiry_guard_dte"]=="" else int(x["expiry_guard_dte"]))):
        g="none" if r["expiry_guard_dte"]=="" else f"≤{r['expiry_guard_dte']}"
        L.append(f"| DTE{r['dte_target']} ({r['dte_min']}–{r['dte_max']}) | {r['hold_sessions']} | {g} | {money(r['median_annual_pnl_usd'])} | {money(r['min_annual_pnl_usd'])}–{money(r['max_annual_pnl_usd'])} | {r['phases_ge_12000']}/5 | {r['median_resolved']:.0f} | {r['median_unresolved']:.0f} | {r['median_win_rate_pct']:.2f}% | {money(r['median_worst_trade_usd'],2)} | {r['median_peak_overlap']:.0f} |")
    L += ["","## Calendar-year concentration: DTE45 / hold 20 / guard 7","","Resolved P&L grouped by exit year, shown per phase anchor.","","| Phase | "+" | ".join(map(str,range(2018,2026)))+" |","|---:|"+"---:|"*8]
    chosen=[r for r in yr if r["dte_target"]==45 and r["hold_sessions"]==20 and str(r["expiry_guard_dte"])=="7"]
    for phase in PHASES:
        y={r["exit_year"]:r["resolved_pnl_usd"] for r in chosen if r["phase_sessions"]==phase}
        L.append("| "+str(phase)+" | "+" | ".join(money(y.get(a,0)) for a in range(2018,2026))+" |")
    L += ["","## Limits","",
    "- Annual number is resolved trade P&L summed and divided by calendar years, not CAGR, account return, or proof USD 100,000 can fund the positions. Unresolved trades are excluded from P&L statistics and separately counted.",
    "- EOD quote-side estimates are not verified fills. File hashes pin the data files but do not independently authenticate original exchange/OPRA provenance.",
    "- Five phase anchors are a robustness sample, not all 10 possible anchors. Results that move across anchors are phase-sensitive.",
    "- Gross SPY assignment obligation is not broker margin. Account cash, buying power, assignment funding, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.",
    "- Assess phase range, worst trade, unresolved episodes and calendar-year concentration alongside annual P&L; do not select the highest average alone.","",
    "Machine-readable outputs: factorial_matrix.csv (240 phase cells), factorial_config_summary.csv (48 settings), factorial_main_effects.csv, factorial_calendar_year_pnl.csv.",""]
    (ROOT/"DTE_HOLD_EXIT_FACTORIAL_REPORT.md").write_text("\n".join(L),encoding="utf-8")
def main():
    ROOT.mkdir(parents=True,exist_ok=True);cells,yr=load()
    if len(cells)!=240:raise SystemExit(f"expected 240 phase-level cells; got {len(cells)}")
    configs=aggregate(cells)
    if len(configs)!=48:raise SystemExit(f"expected 48 config summaries; got {len(configs)}")
    ef=factor_effects(configs)
    writecsv(ROOT/"factorial_matrix.csv",cells);writecsv(ROOT/"factorial_config_summary.csv",configs)
    writecsv(ROOT/"factorial_main_effects.csv",ef);writecsv(ROOT/"factorial_calendar_year_pnl.csv",yr)
    make_report(configs,ef,yr)
    print(f"AUDIT PASS cells={len(cells)} configs={len(configs)} yearly_rows={len(yr)}")
    print((ROOT/"DTE_HOLD_EXIT_FACTORIAL_REPORT.md").read_text(encoding="utf-8")[:12000])
if __name__=="__main__":main()
