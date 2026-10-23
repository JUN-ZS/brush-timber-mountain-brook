#!/usr/bin/env python3
"""Compare entry frequency and net P&L with/without the 20-session relative-underperformance gate."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from datetime import date
from pathlib import Path
from typing import Any

RATIOS = {"1:6":"fixed_1_6","4:5":"fixed_4_5","2:4":"fixed_2_4","1:3":"fixed_1_3"}
POLICIES = ("HOLD_5_SESSIONS","HOLD_10_SESSIONS","HOLD_20_SESSIONS","EXIT_AT_DTE_LE_7")
WINDOWS = (
    ("1Y", date(2024,7,23), date(2025,7,23), 1.0),
    ("3Y", date(2022,7,23), date(2025,7,23), 3.0),
    ("5Y", date(2020,7,23), date(2025,7,23), 5.0),
)
CUTOFF = date(2025,7,23)
THRESHOLD = 0.005

def fnum(v: Any):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except (TypeError,ValueError):
        return None

def read_csv(path: Path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def read_dataset(root: Path, filter_name: str, ratio: str):
    folder=RATIOS[ratio]
    if filter_name=="none":
        base=root/"no_filter"/folder
        expected="none"
    else:
        base=root/folder
        expected="qqq_underperforms_spy_20d"
    sj=base/"summary.json"; trades=base/"trade_episodes.csv"; skips=base/"entry_skips.csv"
    for p in (sj,trades,skips):
        if not p.is_file(): raise FileNotFoundError(f"Required result missing: {p}")
    summary=json.loads(sj.read_text(encoding="utf-8"))
    actual=summary.get("entry_filter",{}).get("name")
    if actual!=expected: raise ValueError(f"{filter_name} {ratio} expected {expected}, got {actual}")
    return {"summary":summary,"trades":read_csv(trades),"skips":read_csv(skips),
            "sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (sj,trades,skips)}}

def day_of(row):
    try: return date.fromisoformat((row.get("signal_date") or "")[:10])
    except ValueError: return None

def episode_map(dataset):
    entered={}
    for r in dataset["trades"]:
        eid=r.get("episode_id",""); day=day_of(r)
        if eid and day:
            if eid in entered and entered[eid]!=day: raise ValueError(f"Inconsistent episode date for {eid}")
            entered[eid]=day
    skipped={}
    for r in dataset["skips"]:
        eid=r.get("episode_id",""); day=day_of(r)
        if eid and day: skipped[eid]=day
    overlap=set(entered)&set(skipped)
    if overlap: raise ValueError(f"Episodes both entered and skipped: {sorted(overlap)}")
    return {**entered,**skipped},entered,skipped

def summarize_period(ds, ratio, filter_name, window_name, start, end, years, policy):
    selected,entered,skipped=episode_map(ds)
    ids={k:d for k,d in selected.items() if start<=d<=end}
    entered_ids={k:d for k,d in entered.items() if start<=d<=end}
    skipped_ids={k:d for k,d in skipped.items() if start<=d<=end}
    trade_rows=[r for r in ds["trades"] if r.get("policy")==policy and day_of(r) is not None and start<=day_of(r)<=end]
    resolved=[r for r in trade_rows if r.get("status")=="RESOLVED" and fnum(r.get("net_pnl_usd")) is not None]
    pnl=[float(fnum(r["net_pnl_usd"])) for r in resolved]
    wins=sum(x>THRESHOLD for x in pnl); losses=sum(x< -THRESHOLD for x in pnl); flats=len(pnl)-wins-losses
    pos=sum(x for x in pnl if x>THRESHOLD); neg=sum(x for x in pnl if x< -THRESHOLD)
    stress=[]
    for r in resolved:
        value=fnum(r.get("net_pnl_usd")); longq=fnum(r.get("long_qqq_qty")); shortq=fnum(r.get("short_spy_qty"))
        if value is not None and longq is not None and shortq is not None:
            # Increase slippage from 0.05 to 0.10 per option share on both entry and exit.
            stress.append(value - 10.0*(longq+shortq))
    sw=sum(x>THRESHOLD for x in stress)
    unresolved=len(entered_ids)-len(resolved)
    return {
      "filter":filter_name,"ratio":ratio,"window":window_name,"start":start.isoformat(),"end":end.isoformat(),
      "window_years":years,"policy":policy,
      "selected_signal_cohorts":len(ids),"entered_cohorts":len(entered_ids),"entry_skips":len(skipped_ids),
      "selected_cohorts_per_year":round(len(ids)/years,3),"entered_cohorts_per_year":round(len(entered_ids)/years,3),
      "resolved":len(resolved),"unresolved":unresolved,"wins":wins,"losses":losses,"flat":flats,
      "win_rate_pct":round(100*wins/len(pnl),2) if pnl else None,
      "mean_net_pnl_resolved_usd":round(statistics.mean(pnl),2) if pnl else None,
      "median_net_pnl_resolved_usd":round(statistics.median(pnl),2) if pnl else None,
      "total_net_pnl_resolved_usd":round(sum(pnl),2),
      "annualized_resolved_net_pnl_usd":round(sum(pnl)/years,2),
      "worst_resolved_trade_usd":round(min(pnl),2) if pnl else None,
      "best_resolved_trade_usd":round(max(pnl),2) if pnl else None,
      "profit_factor":round(pos/abs(neg),3) if neg<0 else (None if pos==0 else "INF"),
      "stress_slippage_010_resolved":len(stress),
      "stress_win_rate_pct":round(100*sw/len(stress),2) if stress else None,
      "stress_mean_net_pnl_usd":round(statistics.mean(stress),2) if stress else None,
      "stress_total_net_pnl_usd":round(sum(stress),2),
      "stress_annualized_resolved_net_pnl_usd":round(sum(stress)/years,2),
      "stress_worst_trade_usd":round(min(stress),2) if stress else None
    }

def build(root:Path):
    cache={}; records=[]; annual=[]
    for filter_name in ("qqq_underperforms_spy_20d","none"):
        for ratio in RATIOS:
            ds=read_dataset(root,filter_name,ratio); cache[(filter_name,ratio)]=ds
            selected,entered,skipped=episode_map(ds)
            for year in range(2018,2026):
                start=date(year,1,1); end=min(date(year,12,31),CUTOFF)
                if start>CUTOFF: continue
                elapsed=max(1,(end-start).days+1)/365.2425
                sigs={k:d for k,d in selected.items() if start<=d<=end}
                ents={k:d for k,d in entered.items() if start<=d<=end}
                skps={k:d for k,d in skipped.items() if start<=d<=end}
                for policy in POLICIES:
                    r=summarize_period(ds,ratio,filter_name,str(year),start,end,elapsed,policy)
                    annual.append({"filter":filter_name,"ratio":ratio,"year":year,"policy":policy,
                       "selected_signal_cohorts":len(sigs),"entered_cohorts":len(ents),"entry_skips":len(skps),
                       "opened_per_year":round(len(ents)/elapsed,3),
                       "resolved":r["resolved"],"unresolved":r["unresolved"],
                       "win_rate_pct":r["win_rate_pct"],"mean_net_pnl_resolved_usd":r["mean_net_pnl_resolved_usd"],
                       "total_net_pnl_resolved_usd":r["total_net_pnl_resolved_usd"]})
            for wname,start,end,yrs in WINDOWS:
                for policy in POLICIES:
                    records.append(summarize_period(ds,ratio,filter_name,wname,start,end,yrs,policy))
    meta={"schema":"qqq-spy-entry-frequency-comparison.v1","source_cutoff":"2025-12-12",
      "last_signal_included":"2025-07-23",
      "window_convention":"Signal-date windows ending 2025-07-23 so long-hold and DTE<=7 exits have a chance to resolve in preserved history. Quote/depth failures remain unresolved.",
      "comparators":["qqq_underperforms_spy_20d","none"],"ratios":list(RATIOS),"policies":list(POLICIES),
      "source_hashes":{f"{f}/{r}":ds["sha256"] for (f,r),ds in cache.items()},
      "cohort_counts_full_period":{f"{f}/{r}":{"selected":len(episode_map(ds)[0]),"entered":len(episode_map(ds)[1]),"skipped":len(episode_map(ds)[2])} for (f,r),ds in cache.items()},
      "caveats":[
        "One cohort is attempted per roughly 45 common sessions; removing the relative-performance gate does not mean entering every day.",
        "Counts refer to strategy cohorts, not contracts: 1:3 opens four contracts, 2:4 six, 4:5 nine, and 1:6 seven.",
        "P&L is the sum of resolved fixed-size cohorts, not compounded NAV, and does not model portfolio overlap or capital recycling.",
        "Unresolved episodes are excluded from resolved P&L but reported separately, never assigned zero.",
        "The 0.10 slippage result adds USD 10 per contract round-trip versus base slippage; it does not simulate market impact.",
        "EOD displayed size is not a guaranteed multi-leg fill; broker margin, financing and forced liquidation are not modeled.",
        "Ratios were selected after reviewing the same historical period; this is in-sample comparison, not forward-alpha evidence."
      ]}
    return records,annual,meta

def money(x): return "—" if x is None else "USD "+format(float(x),",.2f")
def pct(x): return "—" if x is None else format(float(x),".2f")+"%"

def make_report(records,annual,meta):
    out=["# QQQ/SPY Entry-Frequency Comparison: Filtered vs Unfiltered","",
      "- Compare the 20-session relative-underperformance gate with no relative-performance gate.",
      "- Same fixed quantities, cohort cadence, DTE/Delta rules, quote-side directions, displayed-size gates and base costs.",
      "- Last signal included: 2025-07-23, allowing more complete observation of longer exits.",
      "- P&L is not compounded; unresolved cohorts are separately reported.","",
      "## Trade frequency per year (unique cohorts, not individual contracts)","",
      "| Window | Entry filter | Ratio | Selected cohorts | Entered | Skipped | Entered/year |",
      "|---|---|---:|---:|---:|---:|---:|"]
    for w in ("1Y","3Y","5Y"):
      for filt in ("qqq_underperforms_spy_20d","none"):
       for ratio in RATIOS:
        r=next(x for x in records if x["window"]==w and x["filter"]==filt and x["ratio"]==ratio and x["policy"]=="HOLD_20_SESSIONS")
        out.append(f"| {w} | {filt} | {ratio} | {r['selected_signal_cohorts']} | {r['entered_cohorts']} | {r['entry_skips']} | {r['entered_cohorts_per_year']:.2f} |")
    out += ["","## Mean and total net P&L per horizon (base costs)","",
      "| Window | Filter | Ratio | Exit | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Annualized resolved net | Worst trade | Unresolved |",
      "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for w in ("1Y","3Y","5Y"):
      for filt in ("qqq_underperforms_spy_20d","none"):
       for ratio in RATIOS:
        for policy in POLICIES:
         r=next(x for x in records if x["window"]==w and x["filter"]==filt and x["ratio"]==ratio and x["policy"]==policy)
         label={"HOLD_5_SESSIONS":"5d","HOLD_10_SESSIONS":"10d","HOLD_20_SESSIONS":"20d","EXIT_AT_DTE_LE_7":"DTE<=7"}[policy]
         out.append(f"| {w} | {filt} | {ratio} | {label} | {r['resolved']}/{r['entered_cohorts']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_resolved_usd'])} | {money(r['total_net_pnl_resolved_usd'])} | {money(r['annualized_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | {r['unresolved']} |")
    out += ["","## 20-session exit under slippage stress (USD 0.10 per option share per side)","",
      "Derived by adding USD 10 per contract round-trip to each resolved trade versus base slippage; not a new fill simulation.","",
      "| Window | Filter | Ratio | Resolved | Mean stressed net/trade | Total stressed net | Annualized stressed net | Worst stressed trade |",
      "|---|---|---:|---:|---:|---:|---:|---:|"]
    for w in ("1Y","3Y","5Y"):
      for filt in ("qqq_underperforms_spy_20d","none"):
       for ratio in RATIOS:
        r=next(x for x in records if x["window"]==w and x["filter"]==filt and x["ratio"]==ratio and x["policy"]=="HOLD_20_SESSIONS")
        out.append(f"| {w} | {filt} | {ratio} | {r['stress_slippage_010_resolved']} | {money(r['stress_mean_net_pnl_usd'])} | {money(r['stress_total_net_pnl_usd'])} | {money(r['stress_annualized_resolved_net_pnl_usd'])} | {money(r['stress_worst_trade_usd'])} |")
    out += ["","## Calendar-year count and 20-session P&L","",
      "| Year | Filter | Ratio | Selected cohorts | Entered | Skipped | Resolved/unresolved | Win rate | Mean net/trade | Total resolved net |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    seen=set()
    for r in annual:
      if r["policy"]!="HOLD_20_SESSIONS": continue
      key=(r["year"],r["filter"],r["ratio"])
      if key in seen: continue
      seen.add(key)
      out.append(f"| {r['year']} | {r['filter']} | {r['ratio']} | {r['selected_signal_cohorts']} | {r['entered_cohorts']} | {r['entry_skips']} | {r['resolved']}/{r['unresolved']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_resolved_usd'])} | {money(r['total_net_pnl_resolved_usd'])} |")
    out += ["","## Interpretation limits",""]+[f"- {x}" for x in meta["caveats"]]+[""]
    return "\n".join(out)

def save(root:Path,out_dir:Path):
    records,annual,meta=build(root); out_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in (("period_comparison.csv",records),("annual_calendar_comparison.csv",annual)):
      with (out_dir/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (out_dir/"comparison.json").write_text(json.dumps({"metadata":meta,"period_records":records,"annual_records":annual},indent=2),encoding="utf-8")
    (out_dir/"report.md").write_text(make_report(records,annual,meta),encoding="utf-8")
    return meta

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-root",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    p.add_argument("--out-dir",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/no_filter_frequency_audit"))
    a=p.parse_args(); meta=save(a.results_root,a.out_dir)
    print(json.dumps({"status":"COMPLETED","period_rows":len(meta["ratios"])*len(meta["comparators"])*3*len(meta["policies"]),
      "datasets_checked":len(meta["source_hashes"]),"last_signal_included":meta["last_signal_included"],"out_dir":str(a.out_dir)},indent=2))
if __name__=="__main__": main()
